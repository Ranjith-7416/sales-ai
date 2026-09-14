"""Leads API Routes"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Lead, UserActivity, LeadMemory
from app.schemas import LeadInputSchema, LeadResponse
from app.status_utils import normalize_lead_status
from app.services.document_processor import get_document_processor
from app.security import rate_limit, require_auth
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
    missing_information = []
    if not lead.company_size:
        missing_information.append("Company size and number of users")
    if not lead.budget:
        missing_information.append("Budget range or expected investment")
    if not lead.timeline:
        missing_information.append("Target implementation timeline")

    context = (lead.additional_context or "").lower()
    inquiry = (lead.inquiry_text or "").lower()
    combined = f"{context} {inquiry}"
    if not any(term in combined for term in ("decision-maker", "decision maker", "approval", "vp", "director", "head of", "lead", "manager")):
        missing_information.append("Decision-maker and approval process")
    if not any(term in combined for term in ("success", "integration", "ocr", "api", "accuracy", "documents", "turnaround")):
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
        inquiry_text = await get_document_processor().extract_from_file(file.filename, content)
        if not inquiry_text.strip():
            raise HTTPException(status_code=400, detail="The uploaded document contains no readable text")

        lead_id = str(uuid.uuid4())
        lead_input = LeadInputSchema(
            company_name=company_name,
            inquiry_text=inquiry_text,
            industry=industry,
            company_size=company_size,
            budget=budget,
            timeline=timeline,
            additional_context=additional_context,
        )
        lead = Lead(
            id=lead_id,
            company_name=company_name,
            inquiry_text=inquiry_text,
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
        if not result.get("qualification_result") or result["qualification_result"].get("composite_score") in (None, 0):
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
                "composite_score": lead.composite_score or score,
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
        result["qualification_result"]["lead_status"] = normalize_lead_status(
            result["qualification_result"].get("lead_status"),
            result["qualification_result"].get("composite_score"),
            result["requirements_result"].get("missing_information", []),
        )
        # Do not manufacture recommendations or proposals from incomplete input.
        # The UI renders its pending state when these provider-backed results are absent.
        if not result.get("reviewer_result"):
            result["reviewer_result"] = None
        result["requirements"] = result["requirements_result"]
        result["qualification"] = result["qualification_result"]
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
            "lead_status": result["qualification_result"].get("lead_status", lead.lead_status),
            "composite_score": lead.composite_score or result["qualification_result"]["composite_score"],
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


@router.get("")
async def list_leads(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    db: Session = Depends(get_db),
):
    """List all leads"""
    try:
        query = db.query(Lead).order_by(Lead.created_at.desc())
        
        leads_list = query.all()
        lead_cards = []
        for lead in leads_list:
            completeness = sum(bool(value) for value in (
                lead.company_name,
                lead.industry,
                lead.company_size,
                lead.budget,
                lead.timeline,
                lead.additional_context,
            ))
            score = lead.composite_score
            if score is None or score == 0:
                score = round(completeness / 6 * 100)
            if lead.requirements_result and isinstance(lead.requirements_result, dict) and lead.requirements_result.get("missing_information") is not None:
                missing_information = lead.requirements_result["missing_information"]
            elif lead.pipeline_result and isinstance(lead.pipeline_result, dict) and lead.pipeline_result.get("requirements_result", {}).get("missing_information") is not None:
                missing_information = lead.pipeline_result["requirements_result"]["missing_information"]
            else:
                missing_information = _missing_customer_information(lead)
            current_status = normalize_lead_status(
                lead.lead_status,
                score,
                missing_information,
            )
            lead_cards.append({
                "id": lead.id,
                "company_name": lead.company_name,
                "contact_name": lead.contact_name,
                "email": lead.email,
                "inquiry_text": lead.inquiry_text,
                "lead_status": current_status,
                "composite_score": score,
                "created_at": lead.created_at,
            })

        if status:
            lead_cards = [lead for lead in lead_cards if lead["lead_status"] == status]
        total = len(lead_cards)
        lead_cards = lead_cards[skip:skip + limit]
        
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
