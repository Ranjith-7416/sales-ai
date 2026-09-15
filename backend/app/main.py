"""FastAPI Main Application"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
import logging
import uuid
from datetime import datetime

from app.config import settings, validate_production_settings
from app.database import init_db, get_db
from app.schemas import LeadInputSchema, LeadQualificationResult
from app.api import leads, proposals, knowledge_base, config_api, auth
from app.agents.orchestrator import get_orchestrator
from app.models import Lead
from app.models import Lead, LeadMemory
from app.status_utils import normalize_lead_status
from app.services.llm_service import provider_status
from app.security import rate_limit, require_auth
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    validate_production_settings()
    logger.info("Starting application...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as exc:
        logger.warning(f"Database initialization encountered an issue: {exc}")
    yield

    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sales AI - Lead Qualification & Proposal Generation System",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$|^http:\/\/localhost(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(proposals.router, prefix="/api/proposals", tags=["Proposals"])
app.include_router(knowledge_base.router, prefix="/api/knowledge-base", tags=["Knowledge Base"])
app.include_router(config_api.router, prefix="/api/config", tags=["Configuration"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/api/config/status")
async def configuration_status():
    """Report non-secret provider readiness for local setup and diagnostics."""
    return {"llm": provider_status()}


@app.get("/")
async def api_root(request: Request):
    """Return an interactive Developer Control Center when opened in browser, or JSON for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sales AI - Backend Control Center</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0b0f19; color: #f8fafc; min-height: 100vh; padding: 40px 20px; }}
    .container {{ max-width: 980px; margin: 0 auto; }}
    .header {{ display: flex; align-items: center; justify-content: space-between; padding-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 28px; flex-wrap: wrap; gap: 16px; }}
    .title-group {{ display: flex; align-items: center; gap: 14px; }}
    .logo-badge {{ background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; box-shadow: 0 8px 16px rgba(79, 70, 229, 0.3); }}
    .title {{ font-size: 22px; font-weight: 800; letter-spacing: -0.02em; }}
    .subtitle {{ font-size: 13px; color: #94a3b8; margin-top: 2px; }}
    .status-pill {{ display: inline-flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: #34d399; font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 9999px; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 10px #10b981; animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
    .grid-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 28px; }}
    .card {{ background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 20px; }}
    .card-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 6px; }}
    .card-val {{ font-size: 15px; font-weight: 700; color: #f1f5f9; display: flex; align-items: center; gap: 8px; }}
    .btn-group {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 32px; }}
    .btn {{ display: inline-flex; align-items: center; gap: 8px; padding: 12px 22px; border-radius: 10px; font-size: 13px; font-weight: 700; text-decoration: none; transition: all 0.2s; cursor: pointer; }}
    .btn-primary {{ background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: white; box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3); }}
    .btn-primary:hover {{ opacity: 0.95; transform: translateY(-1px); }}
    .btn-secondary {{ background: #1e293b; color: #e2e8f0; border: 1px solid rgba(255,255,255,0.1); }}
    .btn-secondary:hover {{ background: #334155; }}
    .btn-success {{ background: #059669; color: white; }}
    .btn-success:hover {{ background: #10b981; }}
    .section-title {{ font-size: 15px; font-weight: 700; color: #e2e8f0; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }}
    .endpoint-list {{ background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; overflow: hidden; margin-bottom: 24px; }}
    .endpoint-item {{ display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); text-decoration: none; color: inherit; transition: background 0.15s; }}
    .endpoint-item:last-child {{ border-bottom: none; }}
    .endpoint-item:hover {{ background: rgba(255,255,255,0.04); }}
    .left {{ display: flex; align-items: center; }}
    .method {{ font-size: 11px; font-weight: 800; padding: 4px 8px; border-radius: 6px; letter-spacing: 0.05em; min-width: 52px; text-align: center; }}
    .method-get {{ background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
    .method-post {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .endpoint-path {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 13px; font-weight: 600; color: #f1f5f9; margin-left: 12px; }}
    .endpoint-desc {{ font-size: 12px; color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="title-group">
        <div class="logo-badge">⚡</div>
        <div>
          <h1 class="title">{settings.APP_NAME}</h1>
          <p class="subtitle">Autonomous Multi-Agent Enterprise Sales Qualification &amp; Proposal Platform</p>
        </div>
      </div>
      <div class="status-pill">
        <span class="dot"></span>
        FastAPI Online &bull; Port {settings.PORT or 8001}
      </div>
    </div>

    <!-- System Stats -->
    <div class="grid-3">
      <div class="card">
        <div class="card-label">Primary Database</div>
        <div class="card-val" style="color: #60a5fa;">
          <span>🐘</span> PostgreSQL 18 (Active)
        </div>
      </div>
      <div class="card">
        <div class="card-label">AI Reasoning Engine</div>
        <div class="card-val" style="color: #c084fc;">
          <span>🧠</span> Groq (openai/gpt-oss-120b)
        </div>
      </div>
      <div class="card">
        <div class="card-label">Frontend Web App</div>
        <div class="card-val" style="color: #34d399;">
          <span>💻</span> React &bull; localhost:3000
        </div>
      </div>
    </div>

    <!-- Quick Action Buttons -->
    <div class="btn-group">
      <a href="/docs" class="btn btn-primary" target="_blank">
        📘 Interactive Swagger Docs (/docs) &rarr;
      </a>
      <a href="/redoc" class="btn btn-secondary" target="_blank">
        📖 ReDoc API Spec (/redoc)
      </a>
      <a href="http://localhost:3000" class="btn btn-success" target="_blank">
        🚀 Launch Frontend Workspace (localhost:3000)
      </a>
    </div>

    <!-- Core API Endpoints -->
    <div class="section-title">
      <span>📡</span> Core API Endpoints &amp; Routes
    </div>
    <div class="endpoint-list">
      <a href="/api/leads" target="_blank" class="endpoint-item">
        <div class="left">
          <span class="method method-get">GET</span>
          <span class="endpoint-path">/api/leads</span>
        </div>
        <span class="endpoint-desc">List all qualified leads with composite scores and requirements</span>
      </a>
      <a href="/api/config/scoring" target="_blank" class="endpoint-item">
        <div class="left">
          <span class="method method-get">GET</span>
          <span class="endpoint-path">/api/config/scoring</span>
        </div>
        <span class="endpoint-desc">View lead qualification scoring criteria, weights and formula</span>
      </a>
      <a href="/api/knowledge-base/products" target="_blank" class="endpoint-item">
        <div class="left">
          <span class="method method-get">GET</span>
          <span class="endpoint-path">/api/knowledge-base/products</span>
        </div>
        <span class="endpoint-desc">View verified enterprise products catalog for RAG grounding</span>
      </a>
      <a href="/api/knowledge-base/services" target="_blank" class="endpoint-item">
        <div class="left">
          <span class="method method-get">GET</span>
          <span class="endpoint-path">/api/knowledge-base/services</span>
        </div>
        <span class="endpoint-desc">View enterprise services catalog and pricing tiers</span>
      </a>
      <a href="/api/config/smtp" target="_blank" class="endpoint-item">
        <div class="left">
          <span class="method method-get">GET</span>
          <span class="endpoint-path">/api/config/smtp</span>
        </div>
        <span class="endpoint-desc">Inspect SMTP email delivery credentials and status</span>
      </a>
      <a href="/health" target="_blank" class="endpoint-item">
        <div class="left">
          <span class="method method-get">GET</span>
          <span class="endpoint-path">/health</span>
        </div>
        <span class="endpoint-desc">Backend health probe &amp; uptime status</span>
      </a>
    </div>
  </div>
</body>
</html>
"""
        return HTMLResponse(content=html)

    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": settings.APP_VERSION,
        "frontend": "http://localhost:3000",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "lead_api": "/api/leads",
        "proposals_api": "/api/proposals",
        "scoring_config": "/api/config/scoring",
        "knowledge_base": "/api/knowledge-base/products",
    }


@app.post("/api/qualify-lead", dependencies=[Depends(require_auth), Depends(rate_limit("RATE_LIMIT_LEAD_REQUESTS"))])
async def qualify_lead(
    lead_input: LeadInputSchema,
    background_tasks: BackgroundTasks,
    db = Depends(get_db),
):
    """
    Submit a customer inquiry for qualification.
    Returns immediately with lead ID, processes in background.
    """
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
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Lead created: {lead_id}")
        
        # Process in background
        background_tasks.add_task(
            _process_lead_qualification,
            lead_id=lead_id,
            lead_input=lead_input.model_dump(),
        )
        
        return {
            "lead_id": lead_id,
            "status": "submitted",
            "message": "Lead submitted for qualification. Check back for results.",
            "inquiry_received": lead_input.inquiry_text[:100],
        }
    
    except Exception as e:
        logger.error(f"Lead submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _normalize_lead_input_for_background(lead_input: dict | LeadInputSchema) -> dict:
    """Return a plain dictionary payload for the background worker.

    The worker may receive either a Pydantic model instance or a serialized
    dict from the API routes. Normalizing here prevents type-shape drift and
    avoids attribute-access failures such as a dict object being treated like
    a LeadInputSchema in the background pipeline.
    """
    if isinstance(lead_input, dict):
        return dict(lead_input)
    if hasattr(lead_input, "model_dump"):
        return lead_input.model_dump()
    if hasattr(lead_input, "dict"):
        return lead_input.dict()
    raise TypeError("lead_input must be a dict or a Pydantic model instance")


async def _process_lead_qualification(lead_id: str, lead_input: dict | LeadInputSchema):
    """Background task to process lead qualification"""
    try:
        logger.info(f"Processing lead qualification: {lead_id}")
        lead_input = _normalize_lead_input_for_background(lead_input)

        from app.database import SessionLocal
        memory_db = SessionLocal()
        try:
            lead_input["conversation_history"] = [
                {"role": item.role, "content": item.content}
                for item in memory_db.query(LeadMemory).filter(LeadMemory.lead_id == lead_id).order_by(LeadMemory.created_at.asc()).all()
            ]
        finally:
            memory_db.close()
        
        orchestrator = get_orchestrator()
        
        # Add lead_id to input
        lead_input["lead_id"] = lead_id

        async def persist_progress(state: dict, stage: str) -> None:
            progress_db = SessionLocal()
            try:
                progress_lead = progress_db.query(Lead).filter(Lead.id == lead_id).first()
                if progress_lead:
                    progress_lead.pipeline_result = jsonable_encoder({
                        "stages_completed": state.get("stages_completed", []),
                        "current_stage": stage,
                        "errors": state.get("errors", []),
                    })
                    progress_db.commit()
            finally:
                progress_db.close()

        lead_input["_progress_callback"] = persist_progress
        
        # Execute pipeline
        result = await orchestrator.execute(lead_input)
        result["current_stage"] = "complete"

        # Keep the lead useful when an external LLM is unavailable: show the
        # customer information still needed instead of leaving the result blank.
        missing_information = []
        inquiry_lower = (lead_input.get("inquiry_text") or "").lower()
        spam_terms = ('homework', 'school', 'essay', 'crypto', 'bitcoin', 'shoes', 'weather', 'game', 'gaming', 'personal use', 'recipe')
        free_terms = ('free only', 'no budget', 'zero budget', 'cant pay', 'cannot pay', 'have no money', 'student')
        is_spam_lead = any(w in inquiry_lower for w in spam_terms) or any(w in inquiry_lower for w in free_terms)

        if not is_spam_lead:
            for field, label in (
                ("company_size", "Company size and number of users"),
                ("budget", "Budget range or expected investment"),
                ("timeline", "Target implementation timeline"),
            ):
                if not lead_input.get(field):
                    missing_information.append(label)
            context = (lead_input.get("additional_context") or "").lower()
            combined_ctx = f"{context} {inquiry_lower}"
            if not lead_input.get("contact_name") and not any(term in combined_ctx for term in ("decision-maker", "decision maker", "approval", "vp", "director", "head of", "lead", "manager", "dr", "cto", "ceo")):
                missing_information.append("Decision-maker and approval process")
            if not any(term in combined_ctx for term in ("success", "integration", "ocr", "api", "accuracy", "documents", "turnaround", "ehr", "records", "invoices", "platform", "automate")):
                missing_information.append("Success criteria and required integrations")
        if not result.get("requirements_result"):
            result["requirements_result"] = {
                "functional_requirements": [lead_input.get("inquiry_text", "")],
                "non_functional_requirements": {},
                "constraints": {},
                "missing_information": missing_information,
                "assumptions": [],
                "priority_mapping": {"must_have": [], "nice_to_have": []},
            }
        if not result.get("qualification_result"):
            result["qualification_result"] = {
                "lead_status": "Needs More Information",
                "composite_score": 0,
                "fit_score": 0,
                "fit_evidence": "More customer context is required.",
                "readiness_score": 0,
                "readiness_evidence": "Budget and timeline are not yet confirmed.",
                "opportunity_score": 0,
                "opportunity_evidence": "The opportunity cannot be sized yet.",
                "risk_score": 0,
                "risk_evidence": "Decision process and success criteria are unknown.",
                "qualification_reasoning": "The inquiry was received. Add the requested customer information to continue qualification.",
                "score_drivers": [],
                "follow_up_questions": missing_information,
            }

        active_missing = result.get("requirements_result", {}).get("missing_information")
        if active_missing is None:
            active_missing = missing_information
        qualification_result = result.get("qualification_result") or {}
        qualification_result["lead_status"] = normalize_lead_status(
            qualification_result.get("lead_status"),
            qualification_result.get("composite_score"),
            active_missing,
        )
        result["qualification_result"] = qualification_result
        
        # Get database session
        from app.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Update lead record
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                qualification_result = result.get("qualification_result") or {}
                lead.pipeline_result = jsonable_encoder(result)
                lead.lead_status = normalize_lead_status(
                    qualification_result.get("lead_status"),
                    qualification_result.get("composite_score"),
                    active_missing,
                )
                lead.composite_score = qualification_result.get("composite_score", 0)
                lead.research_result = result.get("research_result")
                lead.requirements_result = result.get("requirements_result")
                lead.qualification_result = result.get("qualification_result")
                lead.solution_matching_result = result.get("solution_matching_result")
                lead.proposal_result = result.get("proposal_result")
                lead.reviewer_result = result.get("reviewer_result")
                lead.completed_at = datetime.utcnow()
                
                # Calculate pipeline duration
                if result.get("start_time") and result.get("end_time"):
                    start = datetime.fromisoformat(result["start_time"]) if isinstance(result["start_time"], str) else result["start_time"]
                    end = datetime.fromisoformat(result["end_time"]) if isinstance(result["end_time"], str) else result["end_time"]
                    lead.pipeline_duration_seconds = (end - start).total_seconds()
                
                db.add(LeadMemory(
                    lead_id=lead_id,
                    role="user",
                    content=lead_input.get("inquiry_text", ""),
                ))
                db.commit()
                logger.info(f"Lead {lead_id} qualification completed - Score: {lead.composite_score}")
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Lead qualification processing failed for {lead_id}: {str(e)}")
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.lead_status = "Needs More Information"
                lead.pipeline_result = {"errors": [{"stage": "pipeline", "error": str(e)}]}
                lead.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()


@app.get("/api/leads/{lead_id}")
async def get_lead_status(lead_id: str, db = Depends(get_db)):
    """Get lead qualification status and results"""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Determine status
        if lead.completed_at:
            status = "completed"
        elif lead.pipeline_result:
            status = "processing"
        else:
            status = "queued"
        
        response = {
            "lead_id": lead.id,
            "company_name": lead.company_name,
            "status": status,
            "lead_status": lead.lead_status,
            "composite_score": lead.composite_score,
            "created_at": lead.created_at,
            "completed_at": lead.completed_at,
        }
        
        # Include full results if completed
        if status == "completed" and lead.pipeline_result:
            response["results"] = {
                "research": lead.research_result,
                "requirements": lead.requirements_result,
                "qualification": lead.qualification_result,
                "solution_matching": lead.solution_matching_result,
                "proposal": lead.proposal_result,
                "reviewer": lead.reviewer_result,
            }
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leads")
async def list_leads(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    db = Depends(get_db),
):
    """List all leads with optional filtering"""
    try:
        query = db.query(Lead).order_by(Lead.created_at.desc())
        
        if status:
            query = query.filter(Lead.lead_status == status)
        
        total = query.count()
        leads_list = query.offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "leads": [
                {
                    "id": lead.id,
                    "company_name": lead.company_name,
                    "lead_status": lead.lead_status,
                    "composite_score": lead.composite_score,
                    "created_at": lead.created_at,
                    "completed_at": lead.completed_at,
                }
                for lead in leads_list
            ]
        }
    
    except Exception as e:
        logger.error(f"Error listing leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
