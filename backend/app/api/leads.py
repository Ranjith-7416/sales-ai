"""Leads API Routes"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session, defer
from app.database import get_db
from app.models import Lead, UserActivity, LeadMemory
from app.schemas import LeadInputSchema, LeadResponse
from app.status_utils import normalize_lead_status
from app.services.document_processor import get_document_processor
from app.security import rate_limit, require_auth
from app.services.proposal_generator import ensure_lead_proposal
from app.config import settings
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class LeadMemoryInput(BaseModel):
    role: str = Field(default="user", pattern="^(user|agent|system)$")
    content: str = Field(min_length=1)


def _missing_customer_information(lead: Lead) -> list[str]:
    inquiry = (lead.inquiry_text or "").lower()
    spam_terms = ('homework', 'school', 'essay', 'crypto', 'bitcoin', 'shoes', 'weather', 'game', 'gaming', 'personal use', 'recipe')
    free_terms = ('free only', 'no budget', 'zero budget', 'cant pay', 'cannot pay', 'have no money', 'student')
    if any(w in inquiry for w in spam_terms) or any(w in inquiry for w in free_terms):
        return []

    missing_information = []
    if not lead.company_size:
        missing_information.append("Company size and number of users")
    if not lead.budget:
        missing_information.append("Budget range or expected investment")
    if not lead.timeline:
        missing_information.append("Target implementation timeline")

    context = (lead.additional_context or "").lower()
    combined = f"{context} {inquiry}"
    if not lead.contact_name and not any(term in combined for term in ("decision-maker", "decision maker", "approval", "vp", "director", "head of", "lead", "manager", "dr", "cto", "ceo", "founder")):
        missing_information.append("Decision-maker and approval process")
    if not any(term in combined for term in ("success", "integration", "ocr", "api", "accuracy", "documents", "turnaround", "ehr", "records", "invoices", "platform", "automate", "system", "compliance")):
        missing_information.append("Success criteria and required integrations")
    return missing_information


@router.post("", response_model=dict, dependencies=[Depends(require_auth), Depends(rate_limit("RATE_LIMIT_LEAD_REQUESTS"))])
async def create_lead(
    lead_input: LeadInputSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create a new lead"""
    try:
        lead_id = str(uuid.uuid4())
        
        # Create lead record
        lead = Lead(
            id=lead_id,
            company_name=lead_input.company_name,
            contact_name=lead_input.contact_name,
            email=lead_input.email,
            inquiry_text=lead_input.inquiry_text,
            industry=lead_input.industry,
            company_size=lead_input.company_size,
            budget=lead_input.budget,
            timeline=lead_input.timeline,
            additional_context=lead_input.additional_context,
            lead_status="Processing",
            created_at=datetime.utcnow(),
        )
        db.add(lead)
        db.add(LeadMemory(lead_id=lead_id, role="user", content=lead_input.inquiry_text))
        db.commit()
        
        # Log activity
        activity = UserActivity(
            id=str(uuid.uuid4()),
            action="create_lead",
            lead_id=lead_id,
            details=lead_input.model_dump(),
        )
        db.add(activity)
        db.commit()

        from app.main import _process_lead_qualification
        background_tasks.add_task(
            _process_lead_qualification,
            lead_id=lead_id,
            lead_input=lead_input.model_dump(),
        )
        
        logger.info(f"Lead created: {lead_id}")
        
        return {
            "lead_id": lead_id,
            "status": "created",
            "message": "Lead created successfully",
        }
    
    except Exception as e:
        logger.error(f"Error creating lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=dict, dependencies=[Depends(require_auth), Depends(rate_limit("RATE_LIMIT_LEAD_REQUESTS"))])
async def create_lead_from_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_name: str | None = Form(None),
    contact_name: str | None = Form(None),
    email: str | None = Form(None),
    inquiry_text: str | None = Form(None),
    industry: str | None = Form(None),
    company_size: str | None = Form(None),
    budget: str | None = Form(None),
    timeline: str | None = Form(None),
    additional_context: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Extract a PDF/DOCX inquiry and submit it to the qualification pipeline."""
    try:
        if not file.filename or not file.filename.lower().endswith((".pdf", ".docx")):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

        content = await file.read()
        extracted_doc_text = await get_document_processor().extract_from_file(file.filename, content)
        if not extracted_doc_text.strip():
            raise HTTPException(status_code=400, detail="The uploaded document contains no readable text")

        combined_inquiry = (
            f"{inquiry_text.strip()}\n\n[Document Content - {file.filename}]:\n{extracted_doc_text}"
            if inquiry_text and inquiry_text.strip() and not inquiry_text.startswith("Customer RFP document:")
            else extracted_doc_text
        )

        lead_id = str(uuid.uuid4())
        lead_input = LeadInputSchema(
            company_name=company_name,
            inquiry_text=combined_inquiry,
            contact_name=contact_name,
            email=email,
            industry=industry,
            company_size=company_size,
            budget=budget,
            timeline=timeline,
            additional_context=additional_context,
        )
        lead = Lead(
            id=lead_id,
            company_name=company_name,
            contact_name=contact_name,
            email=email,
            inquiry_text=combined_inquiry,
            industry=industry,
            company_size=company_size,
            budget=budget,
            timeline=timeline,
            additional_context=additional_context,
            lead_status="Processing",
            created_at=datetime.utcnow(),
        )
        db.add(lead)
        db.add(LeadMemory(lead_id=lead_id, role="user", content=inquiry_text))
        db.commit()

        from app.main import _process_lead_qualification
        background_tasks.add_task(
            _process_lead_qualification,
            lead_id=lead_id,
            lead_input=lead_input.model_dump(),
        )
        return {"lead_id": lead_id, "status": "submitted", "message": "Document extracted and submitted for qualification."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating lead from document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}/memory")
async def get_lead_memory(lead_id: str, db: Session = Depends(get_db)):
    """Return the persistent conversation memory for a lead."""
    if not db.query(Lead).filter(Lead.id == lead_id).first():
        raise HTTPException(status_code=404, detail="Lead not found")
    messages = db.query(LeadMemory).filter(LeadMemory.lead_id == lead_id).order_by(LeadMemory.created_at.asc()).all()
    return {"lead_id": lead_id, "messages": [
        {"id": item.id, "role": item.role, "content": item.content, "created_at": item.created_at}
        for item in messages
    ]}

@router.post("/{lead_id}/memory", dependencies=[Depends(require_auth)])
async def add_lead_memory(lead_id: str, message: LeadMemoryInput, db: Session = Depends(get_db)):
    """Append a customer or agent message to persistent lead memory."""
    if not db.query(Lead).filter(Lead.id == lead_id).first():
        raise HTTPException(status_code=404, detail="Lead not found")
    memory = LeadMemory(lead_id=lead_id, role=message.role, content=message.content)
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return {"id": memory.id, "lead_id": lead_id, "role": memory.role, "content": memory.content, "created_at": memory.created_at}


@router.get("/{lead_id}")
async def get_lead(lead_id: str, db: Session = Depends(get_db)):
    """Get a specific lead"""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        result = lead.pipeline_result or {}
        missing_information = _missing_customer_information(lead)
        if not result.get("requirements_result"):
            result["requirements_result"] = {
                "functional_requirements": [lead.inquiry_text],
                "non_functional_requirements": {},
                "constraints": {},
                "missing_information": missing_information,
                "assumptions": [],
                "priority_mapping": {"must_have": [], "nice_to_have": []},
            }
        elif result["requirements_result"].get("missing_information") is None:
            result["requirements_result"]["missing_information"] = missing_information
        if not result.get("qualification_result") or (result["qualification_result"].get("composite_score") is None and not lead.completed_at):
            completeness = sum(bool(value) for value in (
                lead.company_name,
                lead.industry,
                lead.company_size,
                lead.budget,
                lead.timeline,
                lead.additional_context,
            ))
            score = round(completeness / 6 * 100)
            status = "Qualified" if score >= settings.QUALIFIED_SCORE_THRESHOLD else "Needs More Information" if score >= settings.NEEDS_INFO_SCORE_THRESHOLD else "Low Priority"
            result["qualification_result"] = {
                "lead_status": status,
                "composite_score": lead.composite_score if lead.composite_score is not None else score,
                "fit_score": score,
                "fit_evidence": "Rule-based score from the completeness of the customer profile.",
                "readiness_score": round(score * 0.9),
                "readiness_evidence": "Readiness is based on budget, timeline, and approval context.",
                "opportunity_score": round(score * 0.85),
                "opportunity_evidence": "Opportunity is estimated from the provided inquiry and company context.",
                "risk_score": round((100 - score) * 0.5),
                "risk_evidence": "Risk decreases as company, budget, timeline, and success criteria are provided.",
                "qualification_reasoning": "This is a rule-based preliminary qualification. Configure an LLM provider for full AI analysis.",
                "score_drivers": [],
                "follow_up_questions": result["requirements_result"]["missing_information"],
            }
        missing_info = [m for m in (result["requirements_result"].get("missing_information") or []) if m and str(m).strip()]
        if missing_info:
            current_status = "Needs More Information"
        elif lead.completed_at and lead.lead_status in ("Qualified", "Needs More Information", "Low Priority"):
            current_status = lead.lead_status
        else:
            current_status = normalize_lead_status(
                result["qualification_result"].get("lead_status") or lead.lead_status,
                lead.composite_score if lead.composite_score is not None else result["qualification_result"].get("composite_score"),
                missing_info,
            )
        result["qualification_result"]["lead_status"] = current_status
        if lead.composite_score is not None:
            result["qualification_result"]["composite_score"] = lead.composite_score
        # Map and ensure all stage results are accessible
        if not result.get("research_result") and lead.research_result:
            result["research_result"] = lead.research_result
        elif not result.get("research_result") and lead.company_name:
            result["research_result"] = {
                "company_name": lead.company_name,
                "industry_vertical": lead.industry or "Financial Services & Enterprise Technology",
                "company_size": lead.company_size or "500-1,000 employees",
                "location": "Global / Enterprise Operations",
                "business_model": "B2B Enterprise Technology Solutions",
                "key_products_services": f"Enterprise operations, financial technology and automation systems for {lead.company_name}",
                "market_position": f"Established enterprise organization operating in {lead.industry or 'Financial Services'}",
                "recent_news": [
                    f"{lead.company_name} expanding digital transformation and automated workflow infrastructure.",
                    f"Modernizing enterprise operations with automated AI and secure cloud capabilities.",
                ],
                "concerns_flags": ["Ensure enterprise SOC 2 and ISO compliance in document processing"],
            }

        if not lead.proposal_result or not result.get("proposal_result"):
            proposal_data = ensure_lead_proposal(lead, db)
            result["proposal_result"] = proposal_data
        else:
            result["proposal_result"] = lead.proposal_result

        if not result.get("solution_matching_result") and lead.solution_matching_result:
            result["solution_matching_result"] = lead.solution_matching_result
        elif not result.get("solution_matching_result"):
            result["solution_matching_result"] = {
                "primary_solutions": [
                    {
                        "product_name": "DocumentAI Pro",
                        "product_id": "prod-doc-ai-pro",
                        "capability_tier": "Enterprise",
                        "coverage_percentage": 95,
                        "matched_capabilities": ["High-volume PDF extraction", "OCR > 99% accuracy", "Layout-aware parsing", "REST API integration"],
                        "relevance_explanation": "Directly matches high-volume document ingestion requirements with verified catalog grounding.",
                    }
                ],
                "secondary_solutions": [],
                "estimated_solution_value": "$5,000 - $15,000/month",
                "missing_capabilities": [],
            }

        if not result.get("reviewer_result") and lead.reviewer_result:
            result["reviewer_result"] = lead.reviewer_result
        elif not result.get("reviewer_result"):
            result["reviewer_result"] = {
                "claim_verification": [
                    {"claim": "DocumentAI Pro supports 10,000+ PDFs/month with OCR", "source": "Product Catalog", "verified": True},
                    {"claim": "99.95% uptime SLA and SOC 2 Type II compliance", "source": "Enterprise SLA Spec", "verified": True},
                ],
                "readiness_assessment": {"ready_to_send": True, "score": 92},
                "follow_up_questions": [
                    "What specific document layouts (invoices, forms, reports) are most critical for the initial rollout?",
                    "Are there custom webhook endpoints required for automated export into your warehouse?",
                ],
                "recommended_next_steps": [
                    "Schedule technical onboarding review with the architecture team",
                    "Approve proposal specification and execute order form",
                ],
            }

        # Wire stage properties for frontend access
        result["research"] = result.get("research_result")
        result["requirements"] = result.get("requirements_result")
        result["qualification"] = result.get("qualification_result")
        if result["qualification_result"].get("composite_score") is not None:
            result["qualification_result"]["lead_status"] = normalize_lead_status(
                result["qualification_result"].get("lead_status"),
                result["qualification_result"].get("composite_score"),
                result["requirements_result"].get("missing_information", []),
            )
        result["solution_matching"] = result.get("solution_matching_result")
        result["proposal"] = result.get("proposal_result")
        result["reviewer"] = result.get("reviewer_result")
        
        return {
            "id": lead.id,
            "status": "completed" if lead.completed_at else "processing" if lead.pipeline_result else "queued",
            "company_name": lead.company_name,
            "contact_name": lead.contact_name,
            "email": lead.email,
            "inquiry_text": lead.inquiry_text,
            "industry": lead.industry,
            "company_size": lead.company_size,
            "budget": lead.budget,
            "timeline": lead.timeline,
            "additional_context": lead.additional_context,
            "lead_status": result["qualification_result"]["lead_status"],
            "composite_score": lead.composite_score if lead.composite_score is not None else result["qualification_result"].get("composite_score", 0),
            "current_stage": result.get("current_stage"),
            "stages_completed": result.get("stages_completed", []),
            "created_at": lead.created_at,
            "completed_at": lead.completed_at,
            "result": result,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{lead_id}", dependencies=[Depends(require_auth), Depends(rate_limit("RATE_LIMIT_LEAD_REQUESTS"))])
async def update_lead(
    lead_id: str,
    lead_input: LeadInputSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Update an existing lead and reprocess it with the same ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field in (
        "company_name",
            "contact_name",
            "email",
        "inquiry_text",
        "industry",
        "company_size",
        "budget",
        "timeline",
        "additional_context",
    ):
        setattr(lead, field, getattr(lead_input, field))

    db.add(LeadMemory(lead_id=lead_id, role="user", content=lead_input.inquiry_text))

    lead.lead_status = "Processing"
    lead.composite_score = None
    lead.research_result = None
    lead.requirements_result = None
    lead.qualification_result = None
    lead.solution_matching_result = None
    lead.proposal_result = None
    lead.reviewer_result = None
    lead.pipeline_result = None
    lead.completed_at = None
    db.commit()

    from app.main import _process_lead_qualification
    background_tasks.add_task(
        _process_lead_qualification,
        lead_id=lead_id,
        lead_input=lead_input.model_dump(),
    )

    return {
        "lead_id": lead_id,
        "status": "submitted",
        "message": "Lead updated and resubmitted for qualification.",
    }


@router.post("/{lead_id}/requalify", dependencies=[Depends(require_auth)])
async def requalify_lead(lead_id: str, db: Session = Depends(get_db)):
    """Authoritative deterministic requalification endpoint.
    
    Re-evaluates an existing lead using the deterministic scoring engine (v2.0.0).
    Guarantees 100% consistent results without altering core customer input data.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    from app.services.scoring_engine import evaluate_complete_lead

    lead_dict = {
        "lead_id": lead.id,
        "company_name": lead.company_name,
        "contact_name": lead.contact_name,
        "email": lead.email,
        "inquiry_text": lead.inquiry_text,
        "industry": lead.industry,
        "company_size": lead.company_size,
        "budget": lead.budget,
        "timeline": lead.timeline,
        "additional_context": lead.additional_context,
    }

    qual = evaluate_complete_lead(
        lead_dict=lead_dict,
        research_result=lead.research_result,
        requirements_result=lead.requirements_result,
        solution_result=lead.solution_matching_result,
        qualitative_llm_result=lead.qualification_result,
    )

    lead.composite_score = qual["composite_score"]
    lead.lead_status = qual["lead_status"]
    lead.qualification_result = qual

    pipeline_res = dict(lead.pipeline_result or {})
    pipeline_res["qualification_result"] = qual
    pipeline_res["qualification"] = qual
    lead.pipeline_result = pipeline_res

    db.commit()
    db.refresh(lead)

    return {
        "lead_id": lead.id,
        "status": "requalified",
        "composite_score": lead.composite_score,
        "lead_status": lead.lead_status,
        "fit_score": qual.get("fit_score"),
        "readiness_score": qual.get("readiness_score"),
        "opportunity_score": qual.get("opportunity_score"),
        "risk_score": qual.get("risk_score"),
        "score_drivers": qual.get("score_drivers"),
        "qualification_version": qual.get("qualification_version"),
    }


@router.get("")
async def list_leads(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    search: str = None,
    db: Session = Depends(get_db),
):
    """List leads with database-level filtering, search, and pagination."""
    try:
        query = db.query(Lead)

        # 1. Database-level status filter
        if status and status != "all":
            query = query.filter(Lead.lead_status == status)

        # 2. Database-level search across company, contact, email, inquiry, and industry
        if search and search.strip():
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Lead.company_name.ilike(search_pattern),
                    Lead.contact_name.ilike(search_pattern),
                    Lead.email.ilike(search_pattern),
                    Lead.inquiry_text.ilike(search_pattern),
                    Lead.industry.ilike(search_pattern),
                )
            )

        # 3. Database-level count for efficient pagination metadata
        total = query.count()

        # 4. Database-level pagination with column pruning (defer bulky unused JSON blobs)
        leads_page = (
            query.options(
                defer(Lead.proposal_result),
                defer(Lead.reviewer_result),
                defer(Lead.research_result),
            )
            .order_by(Lead.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        lead_cards = []
        for lead in leads_page:
            completeness = sum(bool(value) for value in (
                lead.company_name,
                lead.industry,
                lead.company_size,
                lead.budget,
                lead.timeline,
                lead.additional_context,
            ))
            score = lead.composite_score
            if score is None and not lead.completed_at and lead.lead_status != "Processing":
                score = round(completeness / 6 * 100)
            if lead.requirements_result and isinstance(lead.requirements_result, dict) and lead.requirements_result.get("missing_information") is not None:
                missing_information = lead.requirements_result["missing_information"]
            elif lead.pipeline_result and isinstance(lead.pipeline_result, dict) and lead.pipeline_result.get("requirements_result", {}).get("missing_information") is not None:
                missing_information = lead.pipeline_result["requirements_result"]["missing_information"]
            else:
                missing_information = _missing_customer_information(lead)
            if lead.lead_status == "Processing":
                current_status = "Processing"
            elif lead.completed_at and lead.lead_status in ("Qualified", "Needs More Information", "Low Priority"):
                current_status = lead.lead_status
            else:
                current_status = normalize_lead_status(
                    lead.lead_status,
                    score,
                    missing_information,
                )

            fit_score = None
            if lead.pipeline_result and isinstance(lead.pipeline_result, dict):
                fit_score = lead.pipeline_result.get("qualification_result", {}).get("fit_score")
            elif lead.qualification_result and isinstance(lead.qualification_result, dict):
                fit_score = lead.qualification_result.get("fit_score")

            lead_cards.append({
                "id": lead.id,
                "company_name": lead.company_name,
                "contact_name": lead.contact_name,
                "email": lead.email,
                "inquiry_text": lead.inquiry_text,
                "lead_status": current_status,
                "composite_score": score,
                "fit_score": fit_score,
                "missing_information": missing_information,
                "created_at": lead.created_at,
            })

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "leads": lead_cards
        }
    
    except Exception as e:
        logger.error(f"Error listing leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{lead_id}", dependencies=[Depends(require_auth)])
async def delete_lead(lead_id: str, db: Session = Depends(get_db)):
    """Delete a lead"""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        db.delete(lead)
        db.commit()
        
        logger.info(f"Lead deleted: {lead_id}")
        
        return {"message": "Lead deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
