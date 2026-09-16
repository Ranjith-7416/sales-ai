from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Proposal, Lead, UserActivity
from app.security import rate_limit, require_auth
from app.services.email_service import dispatch_proposal_email, build_proposal_email_content, validate_email_address
from app.config import settings
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
    request: Request,
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

        # Fallback if proposal_result is in pipeline_result
        if not lead.proposal_result and lead.pipeline_result and isinstance(lead.pipeline_result, dict):
            lead.proposal_result = lead.pipeline_result.get("proposal")

        if not lead.proposal_result:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "status": "failed",
                    "recipient": target_email or "",
                    "message": "Cannot send proposal: No proposal has been generated for this lead yet.",
                    "error": "No proposal generated",
                },
            )

        # 1. Validate recipient email
        is_valid, validation_msg = validate_email_address(target_email)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "status": "failed",
                    "recipient": target_email or "",
                    "message": validation_msg,
                    "error": validation_msg,
                },
            )
        target_email = validation_msg

        # 2. Perform real SMTP dispatch
        email_result = dispatch_proposal_email(
            recipient_email=target_email,
            company_name=lead.company_name or "Valued Client",
            proposal_data=lead.proposal_result or {},
            lead_id=lead_id,
            request=request,
        )

        proposal = db.query(Proposal).filter(Proposal.lead_id == lead_id).first()

        # 3. Conditional database audit & status update based on actual delivery result
        if email_result.get("success") is True:
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

            if isinstance(lead.proposal_result, dict):
                updated_prop = dict(lead.proposal_result)
                updated_prop["proposal_status"] = "sent"
                updated_prop["status"] = "sent"
                updated_prop["sent_to"] = target_email
                updated_prop["sent_at"] = now.isoformat()
                updated_prop["delivery_mode"] = email_result.get("delivery_mode", "smtp_live")
                updated_prop["message_id"] = email_result.get("message_id")
                lead.proposal_result = updated_prop

            audit_log = UserActivity(
                id=str(uuid.uuid4()),
                action="proposal_email_sent",
                lead_id=lead_id,
                details={
                    "recipient": target_email,
                    "sender": email_result.get("sender"),
                    "message_id": email_result.get("message_id"),
                    "delivery_mode": email_result.get("delivery_mode", "smtp_live"),
                    "smtp_host": email_result.get("smtp_host"),
                    "timestamp": now.isoformat(),
                },
                created_at=now,
            )
            db.add(audit_log)

            lead.updated_at = now
            db.commit()
            db.refresh(lead)

            logger.info(f"Proposal successfully sent for lead {lead_id} to {target_email} [Message-ID: {email_result.get('message_id')}]")

            return {
                "success": True,
                "status": "sent",
                "lead_id": lead_id,
                "recipient": target_email,
                "message": email_result.get("message", f"Email accepted for delivery to {target_email}"),
                "message_id": email_result.get("message_id"),
                "delivery_mode": email_result.get("delivery_mode", "smtp_live"),
                "sent_at": now.isoformat(),
                "proposal": lead.proposal_result,
            }
        else:
            # Delivery failed - DO NOT set status = "sent"
            if proposal:
                proposal.status = "failed"

            if isinstance(lead.proposal_result, dict):
                updated_prop = dict(lead.proposal_result)
                updated_prop["proposal_status"] = "failed"
                updated_prop["last_send_error"] = email_result.get("error")
                updated_prop["last_send_attempt"] = now.isoformat()
                lead.proposal_result = updated_prop

            audit_log = UserActivity(
                id=str(uuid.uuid4()),
                action="proposal_email_failed",
                lead_id=lead_id,
                details={
                    "recipient": target_email,
                    "error": email_result.get("error"),
                    "delivery_mode": email_result.get("delivery_mode"),
                    "timestamp": now.isoformat(),
                },
                created_at=now,
            )
            db.add(audit_log)

            lead.updated_at = now
            db.commit()

            logger.warning(f"Proposal delivery failed for lead {lead_id} to {target_email}: {email_result.get('error')}")

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "status": "failed",
                    "lead_id": lead_id,
                    "recipient": target_email,
                    "message": email_result.get("message", "Email could not be sent."),
                    "error": email_result.get("error", "SMTP delivery failure"),
                    "delivery_mode": email_result.get("delivery_mode"),
                },
            )
    
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
async def view_proposal_email_html(lead_id: str, request: Request, db: Session = Depends(get_db)):
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
        lead_id=lead_id,
        request=request,
    )
    return HTMLResponse(content=html_content)


@router.get("/{lead_id}/accept", response_class=HTMLResponse)
async def accept_proposal_page(lead_id: str, db: Session = Depends(get_db)):
    """
    Customer portal link: Accepts the proposal and confirms kickoff.
    Marks the lead as Qualified and proposal as accepted in PostgreSQL.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return HTMLResponse(
            status_code=404,
            content="""<!DOCTYPE html><html><body style='font-family: sans-serif; text-align: center; padding: 60px;'>
            <h2 style='color: #ef4444;'>Agreement Not Found</h2>
            <p style='color: #64748b;'>The requested proposal agreement link is invalid or expired.</p>
            </body></html>"""
        )

    # Recover proposal if nested
    if not lead.proposal_result and lead.pipeline_result and isinstance(lead.pipeline_result, dict):
        lead.proposal_result = lead.pipeline_result.get("proposal")

    now = datetime.utcnow()
    lead.lead_status = "Qualified"
    lead.updated_at = now

    # Update proposal record in db
    proposal = db.query(Proposal).filter(Proposal.lead_id == lead_id).first()
    if not proposal:
        proposal = Proposal(
            id=str(uuid.uuid4()),
            lead_id=lead_id,
            proposal_markdown=json.dumps(lead.proposal_result or {}, indent=2),
            status="accepted",
            sent_at=now,
        )
        db.add(proposal)
    else:
        proposal.status = "accepted"

    # Update json proposal_result
    if isinstance(lead.proposal_result, dict):
        updated_prop = dict(lead.proposal_result)
        updated_prop["proposal_status"] = "accepted"
        updated_prop["status"] = "accepted"
        updated_prop["accepted_at"] = now.isoformat()
        lead.proposal_result = updated_prop

    db.commit()
    db.refresh(lead)

    p = lead.proposal_result or {}
    company = lead.company_name or "Valued Client"
    title = p.get("title", f"Enterprise Solution Proposal for {company}")
    summary = p.get("executive_summary", "Solution architecture configured to your enterprise specifications.")
    timeline = p.get("total_implementation_timeline", "2-4 weeks")
    
    pricing = p.get("pricing_proposal", {})
    pricing_list = []
    if isinstance(pricing, dict):
        for k, v in pricing.items():
            pricing_list.append(f"<li style='margin-bottom: 4px;'><strong>{k.replace('_', ' ').title()}:</strong> {v}</li>")
    pricing_html = "".join(pricing_list) if pricing_list else "<li>Custom enterprise scope</li>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agreement Accepted - {company}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0b0f19; color: #f8fafc; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }}
    .card {{ max-width: 680px; width: 100%; background: #111827; border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }}
    .header {{ background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 36px 32px; text-align: center; color: white; }}
    .badge {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 9999px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }}
    .content {{ padding: 32px; }}
    .info-box {{ background: #1f2937; border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 20px; margin-bottom: 24px; }}
    .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; font-size: 13px; }}
    .label {{ color: #9ca3af; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }}
    .value {{ color: #f3f4f6; font-weight: 600; }}
    .slot-btn {{ background: #374151; color: white; border: 1px solid rgba(255,255,255,0.1); padding: 10px 16px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: all 0.2s; margin-right: 8px; margin-bottom: 8px; }}
    .slot-btn:hover {{ background: #4b5563; border-color: #10b981; }}
    .slot-btn.selected {{ background: #059669; border-color: #10b981; font-weight: 700; }}
    .action-btn {{ display: block; width: 100%; text-align: center; background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: white; text-decoration: none; padding: 14px 24px; border-radius: 10px; font-weight: 700; font-size: 14px; margin-top: 20px; transition: opacity 0.2s; }}
    .action-btn:hover {{ opacity: 0.9; }}
    .success-alert {{ display: none; background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 10px; padding: 12px 16px; margin-top: 16px; font-size: 13px; color: #34d399; text-align: center; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="badge">Official Confirmation</div>
      <h1 style="font-size: 26px; font-weight: 800; margin-bottom: 8px;">Proposal Accepted!</h1>
      <p style="font-size: 14px; opacity: 0.9;">Technical Kickoff &amp; Agreement Signed for <strong>{company}</strong></p>
    </div>
    
    <div class="content">
      <div class="info-box">
        <div class="info-grid">
          <div>
            <div class="label">Deal Reference</div>
            <div class="value">{lead_id[:8].upper()}</div>
          </div>
          <div>
            <div class="label">Deal Pipeline Status</div>
            <div class="value" style="color: #34d399;">✓ Qualified &amp; In Provisioning</div>
          </div>
          <div>
            <div class="label">Target Timeline</div>
            <div class="value">{timeline}</div>
          </div>
          <div>
            <div class="label">Accepted Timestamp</div>
            <div class="value">{now.strftime('%b %d, %Y - %H:%M UTC')}</div>
          </div>
        </div>

        <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 16px; font-size: 13px;">
          <div class="label">Agreed Commercial Investment</div>
          <ul style="margin: 8px 0 0 20px; color: #d1d5db; line-height: 1.6;">
            {pricing_html}
          </ul>
        </div>
      </div>

      <!-- Interactive Kickoff Scheduler -->
      <div style="margin-bottom: 24px;">
        <h3 style="font-size: 14px; font-weight: 700; margin-bottom: 12px; color: #e5e7eb;">
          Select Preferred Technical Kickoff Slot:
        </h3>
        <div id="slots">
          <button type="button" class="slot-btn selected" onclick="selectSlot(this, 'Tomorrow at 10:00 AM EST')">Tomorrow 10:00 AM EST</button>
          <button type="button" class="slot-btn" onclick="selectSlot(this, 'Wednesday at 2:00 PM EST')">Wednesday 2:00 PM EST</button>
          <button type="button" class="slot-btn" onclick="selectSlot(this, 'Thursday at 11:30 AM EST')">Thursday 11:30 AM EST</button>
        </div>
        <button type="button" onclick="confirmSlot()" style="margin-top: 10px; background: #10b981; color: white; border: none; padding: 9px 20px; border-radius: 8px; font-weight: 700; font-size: 12px; cursor: pointer;">
          Confirm Kickoff Time
        </button>
        <div id="confirmedAlert" class="success-alert">
          ✓ Kickoff meeting invitation sent for <span id="chosenSlot">Tomorrow at 10:00 AM EST</span>! Check your calendar.
        </div>
      </div>

      <a href="{settings.FRONTEND_URL}/lead/{lead_id}" class="action-btn">
        View Live Deal Room &amp; Pipeline Status &rarr;
      </a>

    </div>
  </div>

  <script>
    let selectedTime = 'Tomorrow at 10:00 AM EST';
    function selectSlot(el, time) {{
      document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
      el.classList.add('selected');
      selectedTime = time;
    }}
    function confirmSlot() {{
      document.getElementById('chosenSlot').innerText = selectedTime;
      document.getElementById('confirmedAlert').style.display = 'block';
    }}
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.post("/{lead_id}/accept")
async def api_accept_proposal(lead_id: str, db: Session = Depends(get_db)):
    """Programmatic API to accept a proposal for a lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    now = datetime.utcnow()
    lead.lead_status = "Qualified"
    lead.updated_at = now

    proposal = db.query(Proposal).filter(Proposal.lead_id == lead_id).first()
    if proposal:
        proposal.status = "accepted"

    if isinstance(lead.proposal_result, dict):
        updated_prop = dict(lead.proposal_result)
        updated_prop["proposal_status"] = "accepted"
        updated_prop["status"] = "accepted"
        updated_prop["accepted_at"] = now.isoformat()
        lead.proposal_result = updated_prop

    db.commit()
    return {
        "message": "Proposal marked as accepted",
        "lead_id": lead_id,
        "status": "accepted",
        "lead_status": "Qualified",
        "accepted_at": now.isoformat(),
    }


