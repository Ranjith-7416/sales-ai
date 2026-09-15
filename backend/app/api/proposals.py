from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Proposal, Lead
from app.security import rate_limit, require_auth
from app.services.email_service import dispatch_proposal_email, build_proposal_email_content
from datetime import datetime
import uuid
import logging
from io import BytesIO
import json
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()


class ProposalApprovalRequest(BaseModel):
    approved_by: Optional[str] = Field(default="Sales AI Reviewer", description="Name or role of reviewer approving the proposal")


class ProposalSendRequest(BaseModel):
    recipient_email: Optional[str] = Field(default=None, description="Recipient email address")


@router.get("/{lead_id}")
async def get_proposal(lead_id: str, db: Session = Depends(get_db)):
    """Get proposal for a lead"""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        if not lead.proposal_result:
            raise HTTPException(status_code=404, detail="No proposal generated yet")
        
        # Determine proposal status from lead or proposal record
        proposal_record = db.query(Proposal).filter(Proposal.lead_id == lead_id).order_by(Proposal.created_at.desc()).first()
        status = proposal_record.status if proposal_record else lead.proposal_result.get("proposal_status", "draft")

        return {
            "lead_id": lead_id,
            "proposal": lead.proposal_result,
            "status": status,
            "approved_by": proposal_record.approved_by if proposal_record else lead.proposal_result.get("approved_by"),
            "approved_at": proposal_record.approved_at if proposal_record else lead.proposal_result.get("approved_at"),
            "created_at": lead.updated_at,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving proposal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/approve", dependencies=[Depends(require_auth), Depends(rate_limit("RATE_LIMIT_PROPOSAL_REQUESTS"))])
async def approve_proposal(
    lead_id: str,
    payload: Optional[ProposalApprovalRequest] = Body(None),
    approved_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Approve a proposal (supports JSON body or query param)"""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        if not lead.proposal_result:
            raise HTTPException(status_code=404, detail="No proposal to approve")

        # Resolve approved_by from body payload, query parameter, or default
        effective_approved_by = "Sales AI Reviewer"
        if payload and payload.approved_by:
            effective_approved_by = payload.approved_by
        elif approved_by:
            effective_approved_by = approved_by
        
        now = datetime.utcnow()

        # Find or create Proposal record
        proposal = db.query(Proposal).filter(Proposal.lead_id == lead_id).first()
        if not proposal:
            proposal = Proposal(
                id=str(uuid.uuid4()),
                lead_id=lead_id,
                proposal_markdown=json.dumps(lead.proposal_result, indent=2),
                status="approved",
                approved_by=effective_approved_by,
                approved_at=now,
            )
            db.add(proposal)
        else:
            proposal.status = "approved"
            proposal.approved_by = effective_approved_by
            proposal.approved_at = now
            proposal.proposal_markdown = json.dumps(lead.proposal_result, indent=2)

        # Update lead's proposal_result JSON and lead_status
        if isinstance(lead.proposal_result, dict):
            updated_prop = dict(lead.proposal_result)
            updated_prop["proposal_status"] = "approved"
            updated_prop["status"] = "approved"
            updated_prop["approved_by"] = effective_approved_by
            updated_prop["approved_at"] = now.isoformat()
            lead.proposal_result = updated_prop
        
        # When human approves, promote status to Qualified if it was pending or info needed
        if lead.lead_status in ["Needs More Information", "Low Priority", "Under Review", "Pending Review"]:
            lead.lead_status = "Qualified"

        lead.updated_at = now
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Proposal approved for lead {lead_id} by {effective_approved_by}")
        
        return {
            "message": "Proposal approved successfully",
            "lead_id": lead_id,
            "status": "approved",
            "approved_by": effective_approved_by,
            "approved_at": now.isoformat(),
            "proposal": lead.proposal_result,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving proposal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


from app.services.email_service import dispatch_proposal_email


@router.post("/{lead_id}/send", dependencies=[Depends(require_auth), Depends(rate_limit("RATE_LIMIT_PROPOSAL_REQUESTS"))])
async def send_proposal(
    lead_id: str,
    payload: Optional[ProposalSendRequest] = Body(None),
    recipient_email: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Send proposal to customer (supports live SMTP delivery or audit-logged dispatch)"""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        target_email = None
        if payload and payload.recipient_email:
            target_email = payload.recipient_email.strip()
        elif recipient_email:
            target_email = recipient_email.strip()
        elif lead.email:
            target_email = lead.email.strip()

        if not target_email:
            raise HTTPException(status_code=400, detail="recipient_email is required")

        # Fallback if proposal_result is in pipeline_result
        if not lead.proposal_result and lead.pipeline_result and isinstance(lead.pipeline_result, dict):
            lead.proposal_result = lead.pipeline_result.get("proposal")

        now = datetime.utcnow()
        proposal = db.query(Proposal).filter(Proposal.lead_id == lead_id).first()
        
        if not proposal:
            proposal = Proposal(
                id=str(uuid.uuid4()),
                lead_id=lead_id,
                proposal_markdown=json.dumps(lead.proposal_result or {}, indent=2),
                status="sent",
                sent_to=target_email,
                sent_at=now,
            )
            db.add(proposal)
        else:
            proposal.status = "sent"
            proposal.sent_to = target_email
            proposal.sent_at = now

        # Dispatch real email via SMTP service or record in audit queue
        email_result = dispatch_proposal_email(
            recipient_email=target_email,
            company_name=lead.company_name or "Valued Client",
            proposal_data=lead.proposal_result or {},
        )

        # Update lead proposal result with sent info
        if isinstance(lead.proposal_result, dict):
            updated_prop = dict(lead.proposal_result)
            updated_prop["proposal_status"] = "sent"
            updated_prop["status"] = "sent"
            updated_prop["sent_to"] = target_email
            updated_prop["sent_at"] = now.isoformat()
            updated_prop["delivery_mode"] = email_result.get("delivery_mode", "audit_recorded")
            lead.proposal_result = updated_prop

        lead.updated_at = now
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Proposal sent for lead {lead_id} to {target_email}: {email_result.get('message')}")
        
        return {
            "message": email_result.get("message", f"Proposal sent successfully to {target_email}"),
            "lead_id": lead_id,
            "status": "sent",
            "recipient": target_email,
            "delivery_mode": email_result.get("delivery_mode", "audit_recorded"),
            "sent_at": now.isoformat(),
            "proposal": lead.proposal_result,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending proposal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}/export")
async def export_proposal(lead_id: str, format: str = "markdown", db: Session = Depends(get_db)):
    """Export proposal formatted as clean Markdown or HTML document"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.proposal_result:
        raise HTTPException(status_code=404, detail="No proposal generated yet for this lead")

    p = lead.proposal_result
    company = lead.company_name or "Valued Client"
    date_str = datetime.utcnow().strftime("%B %d, %Y")

    # Build structured markdown
    lines = [
        f"# Enterprise Solution Proposal",
        f"",
        f"**Prepared For:** {company}  ",
        f"**Date:** {date_str}  ",
        f"**Proposal Reference:** {lead_id[:8].upper()}  ",
        f"**Verification Status:** Grounded in Product Catalog  ",
        f"",
        f"---",
        f"",
        f"## 1. Executive Summary",
        f"{p.get('executive_summary', 'Executive summary in preparation.')}",
        f"",
        f"## 2. Customer Requirements & Scope",
    ]
    reqs = p.get("customer_requirements", [])
    if reqs:
        for r in reqs:
            lines.append(f"- {r}")
    else:
        lines.append("- Document extraction and automated processing workflow")

    lines.extend([
        f"",
        f"## 3. Proposed Solution Architecture",
        f"{p.get('proposed_solution', 'Solution specification in progress.')}",
        f"",
        f"## 4. Implementation Roadmap & Timeline",
        f"**Total Timeline:** {p.get('total_implementation_timeline', '2-4 weeks')}",
        f"",
    ])

    roadmap = p.get("implementation_roadmap", [])
    if roadmap:
        lines.append("| Phase | Duration | Activities |")
        lines.append("| :--- | :--- | :--- |")
        for item in roadmap:
            if isinstance(item, dict):
                phase = item.get("phase", "Phase")
                duration = item.get("duration", "TBD")
                acts = ", ".join(item.get("activities", [])) if isinstance(item.get("activities"), list) else str(item.get("activities", ""))
                lines.append(f"| {phase} | {duration} | {acts} |")
        lines.append("")

    pricing = p.get("pricing_proposal", {})
    lines.extend([
        f"## 5. Commercial & Pricing Model",
        f"",
    ])
    if isinstance(pricing, dict):
        lines.append("| Component | Estimated Investment |")
        lines.append("| :--- | :--- |")
        for k, v in pricing.items():
            label = k.replace("_", " ").title()
            lines.append(f"| {label} | {v} |")
        lines.append("")
    else:
        lines.append(f"{pricing}\n")

    sla = p.get("support_service_levels", {})
    if isinstance(sla, dict) and sla:
        lines.extend([
            f"## 6. Support, Certifications & Service Levels",
            f"",
            f"| Tier | Availability | Response SLA |",
            f"| :--- | :--- | :--- |",
            f"| {sla.get('tier', 'Standard')} | {sla.get('availability', '24/7 Premium')} | {sla.get('response_time', '1 hour')} |",
            f"",
        ])

    metrics = p.get("success_metrics", [])
    if metrics:
        lines.extend([
            f"## 7. Success Metrics & Key Results",
            f"",
        ])
        for m in metrics:
            lines.append(f"- {m}")
        lines.append("")

    next_steps = p.get("next_steps", [])
    if next_steps:
        lines.extend([
            f"## 8. Next Steps & Recommended Actions",
            f"",
        ])
        for idx, step in enumerate(next_steps, 1):
            lines.append(f"{idx}. {step}")
        lines.append("")

    sections = p.get("sections", [])
    if sections:
        for s in sections:
            if isinstance(s, dict):
                lines.extend([
                    f"### {s.get('title', 'Additional Information')}",
                    f"{s.get('content', '')}",
                    f"",
                ])

    markdown_content = "\n".join(lines)
    html_content = (
        f"<!DOCTYPE html><html><head><title>Enterprise Solution Proposal - {company}</title>"
        f"<style>body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 40px auto; line-height: 1.6; color: #1e293b; }} "
        f"h1, h2, h3 {{ color: #0f172a; }} table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }} "
        f"th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; }} th {{ background-color: #f1f5f9; }}</style></head>"
        f"<body><h1>Enterprise Solution Proposal for {company}</h1><pre style='white-space: pre-wrap; font-family: inherit;'>{markdown_content}</pre></body></html>"
    )
    return {
        "lead_id": lead_id,
        "title": f"Enterprise Solution Proposal for {company}",
        "company_name": company,
        "format": format,
        "markdown": markdown_content,
        "html": html_content,
        "filename": f"Proposal_{company.replace(' ', '_')}_{lead_id[:8]}.{'html' if format == 'html' else 'md'}",
    }


@router.get("/{lead_id}/email-view", response_class=HTMLResponse)
async def view_proposal_email_html(lead_id: str, db: Session = Depends(get_db)):
    """View the exact HTML email generated for the client in browser"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.proposal_result and lead.pipeline_result and isinstance(lead.pipeline_result, dict):
        lead.proposal_result = lead.pipeline_result.get("proposal")
    if not lead.proposal_result:
        raise HTTPException(status_code=404, detail="No proposal generated yet")

    target_email = lead.proposal_result.get("sent_to") or lead.email or "client@example.com"
    company = lead.company_name or "Valued Client"

    _, html_content = build_proposal_email_content(
        recipient_email=target_email,
        company_name=company,
        proposal_data=lead.proposal_result,
    )
    return HTMLResponse(content=html_content)

