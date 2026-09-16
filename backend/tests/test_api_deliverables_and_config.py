import json
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import init_db
import app.database as db_module
from app.models import Lead, Proposal


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_scoring_config_endpoints(client):
    """Verify GET and POST /api/config/scoring dynamically updates and returns weights."""
    orig_q = settings.QUALIFIED_SCORE_THRESHOLD
    orig_n = settings.NEEDS_INFO_SCORE_THRESHOLD
    orig_f = settings.FIT_SCORE_WEIGHT
    orig_rd = settings.READINESS_SCORE_WEIGHT
    orig_o = settings.OPPORTUNITY_SCORE_WEIGHT
    orig_rk = settings.RISK_SCORE_WEIGHT

    try:
        get_res = client.get("/api/config/scoring")
        assert get_res.status_code == 200
        cfg = get_res.json()
        assert "qualified_threshold" in cfg
        assert "needs_info_threshold" in cfg
        assert "fit_weight" in cfg
        assert "readiness_weight" in cfg

        new_cfg = {
            "qualified_threshold": 75.0,
            "needs_info_threshold": 45.0,
            "fit_weight": 0.40,
            "readiness_weight": 0.30,
            "opportunity_weight": 0.20,
            "risk_weight": 0.10,
        }
        post_res = client.post("/api/config/scoring", json=new_cfg)
        assert post_res.status_code == 200
        updated = post_res.json()
        assert updated["qualified_threshold"] == 75.0
        assert updated["fit_weight"] == 0.40

        assert settings.QUALIFIED_SCORE_THRESHOLD == 75.0
        assert settings.FIT_SCORE_WEIGHT == 0.40
    finally:
        settings.QUALIFIED_SCORE_THRESHOLD = orig_q
        settings.NEEDS_INFO_SCORE_THRESHOLD = orig_n
        settings.FIT_SCORE_WEIGHT = orig_f
        settings.READINESS_SCORE_WEIGHT = orig_rd
        settings.OPPORTUNITY_SCORE_WEIGHT = orig_o
        settings.RISK_SCORE_WEIGHT = orig_rk


def test_knowledge_base_catalog_and_search_endpoints(client):
    """Verify catalog listing and RAG search endpoints."""
    prod_res = client.get("/api/knowledge-base/products")
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    assert "products" in prod_data
    assert len(prod_data["products"]) > 0
    prod_names = [p["name"] for p in prod_data["products"]]
    assert any("Document" in name for name in prod_names)

    serv_res = client.get("/api/knowledge-base/services")
    assert serv_res.status_code == 200
    serv_data = serv_res.json()
    assert "services" in serv_data
    assert len(serv_data["services"]) > 0

    search_res = client.get("/api/knowledge-base/search?query=document%20extraction%20pdf&entry_type=product&top_k=3")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert "results" in search_data
    assert len(search_data["results"]) > 0


def test_proposal_export_endpoint(client):
    """Verify GET /api/proposals/{lead_id}/export returns structured Markdown and HTML."""
    db = db_module.SessionLocal()
    try:
        test_lead = Lead(
            id="test-export-lead",
            company_name="Apex Global",
            inquiry_text="We need an AI-powered document processing solution capable of extracting information from approximately 10,000 PDF documents per month.",
            lead_status="Qualified",
            composite_score=84.5,
            completed_at=datetime.utcnow(),
            proposal_result={
                "title": "Enterprise AI Document Processing Solution Proposal for Apex Global",
                "executive_summary": "Apex Global requires automated extraction of 10,000 PDFs monthly.",
                "customer_requirements": ["Automated extraction of 10,000 PDFs monthly"],
                "proposed_solution": "DocumentAI Pro enterprise tier with OCR and layout-aware parser.",
                "implementation_roadmap": [
                    {"phase": "Phase 1: Ingestion & Model Configuration", "duration": "2 weeks", "activities": ["Connector setup", "Schema definition"]},
                    {"phase": "Phase 2: Validation & Deployment", "duration": "2 weeks", "activities": ["Accuracy tuning", "Production launch"]},
                ],
                "total_implementation_timeline": "4 weeks",
                "pricing_proposal": {"monthly_subscription": "$5,000/month", "onboarding": "$10,000"},
                "support_service_levels": {"uptime_sla": "99.9%", "support_tier": "24/7 Enterprise"},
                "success_metrics": ["99.5% field extraction accuracy", "Processing latency < 3 seconds per document"],
                "next_steps": ["Sign order form", "Kickoff sprint planning"],
                "sections": [
                    {"title": "1. Executive Summary", "content": "Apex Global requires automated extraction..."},
                    {"title": "2. Proposed Solution", "content": "DocumentAI Pro enterprise tier..."},
                ],
            },
        )
        db.merge(test_lead)
        db.commit()
    finally:
        db.close()

    export_res = client.get("/api/proposals/test-export-lead/export")
    assert export_res.status_code == 200
    export_data = export_res.json()

    assert export_data["lead_id"] == "test-export-lead"
    assert "Apex Global" in export_data["title"]
    assert "# Enterprise Solution Proposal" in export_data["markdown"]
    assert "Apex Global" in export_data["markdown"]
    assert "DocumentAI Pro" in export_data["markdown"]
    assert "<h1>Enterprise Solution Proposal for Apex Global</h1>" in export_data["html"]


def test_twelve_required_deliverables_structure(client):
    """Verify that all 12 required deliverables from the problem statement are represented and accessible in the system."""
    db = db_module.SessionLocal()
    try:
        lead_id = "test-12-deliverables"
        pipeline_data = {
            # Deliverable 2: Customer Information
            "research_result": {
                "company_name": "DocCorp",
                "industry_vertical": "Healthcare",
                "company_size": "250-500 employees",
                "business_context": "Healthcare billing and claims automation",
            },
            # Deliverable 3: Extracted Requirements & Deliverable 4: Missing Information
            "requirements_result": {
                "functional_requirements": ["Extract information from 10,000 PDF documents per month", "OCR accuracy"],
                "non_functional_requirements": {"scale": "10k/month", "compliance": "HIPAA"},
                "volume": "10,000 PDFs/month",
                "input_format": "PDF",
                "missing_information": ["Target field schema list", "Internal destination database details"],
            },
            # Deliverable 5: Lead Score Breakdown & Deliverable 6: Qualification Reasoning
            "qualification_result": {
                "lead_status": "Qualified",
                "fit_score": 90,
                "readiness_score": 85,
                "opportunity_score": 85,
                "risk_score": 15,
                "composite_score": 86.0,
                "formula": "0.35*fit + 0.25*readiness + 0.25*opportunity + 0.15*(100-risk)",
                "weights": {"fit": 0.35, "readiness": 0.25, "opportunity": 0.25, "risk": 0.15},
                "qualification_reasoning": "High-volume document extraction matches DocumentAI Pro capabilities exactly.",
            },
            # Deliverable 7: Matching Solutions
            "solution_matching_result": {
                "primary_solutions": [
                    {
                        "product_name": "DocumentAI Pro",
                        "coverage_percentage": 95,
                        "features_matched": ["PDF Extraction", "OCR Engine", "Tables parsing"],
                        "pricing": "$5,000 - $50,000/month",
                        "delivery_timeline": "2-4 weeks",
                        "certifications": ["SOC2", "HIPAA", "ISO 27001"],
                    }
                ],
            },
            # Deliverable 8: Proposed Solution & Deliverable 9: Draft Proposal
            "proposal_result": {
                "title": "AI Document Processing Proposal for DocCorp",
                "proposed_solution": "DocumentAI Pro with automated validation and HIPAA-compliant data pipeline.",
                "executive_summary": "DocCorp will automate the processing of 10,000 monthly PDF documents.",
                "customer_requirements": ["Process 10,000 PDF documents monthly"],
                "implementation_roadmap": [
                    {"phase": "Phase 1: Setup", "duration": "2 weeks", "activities": ["Document schema ingestion"]}
                ],
                "total_implementation_timeline": "4 weeks",
                "pricing_proposal": {"platform_tier": "DocumentAI Pro Enterprise", "monthly": "$5,000/month"},
                "support_service_levels": {"uptime_sla": "99.9%", "support": "24/7 Priority Support"},
                "sections": [{"title": "Overview", "content": "Full proposal text"}],
            },
            # Deliverables 10, 11, 12: Follow-up questions, Recommended next actions, Grounding verification
            "reviewer_result": {
                "follow_up_questions": ["What is the target SLA for batch OCR extraction?"],
                "recommended_next_steps": ["Schedule technical validation call", "Prepare sample PDF batch"],
                "claim_verification": [
                    {"claim": "DocumentAI Pro extracts 10,000 PDFs monthly", "source": "products.json", "verified": True}
                ],
                "readiness_assessment": {"ready_to_send": True},
            },
            "stages_completed": ["research", "requirements", "qualification", "solution_matching", "proposal", "reviewer"],
        }

        lead = Lead(
            id=lead_id,
            company_name="DocCorp",
            industry="Healthcare",
            inquiry_text="We need an AI-powered document processing solution capable of extracting information from approximately 10,000 PDF documents per month.",
            lead_status="Qualified",
            composite_score=86.0,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            pipeline_result=pipeline_data,
            proposal_result=pipeline_data["proposal_result"],
        )
        db.merge(lead)
        db.commit()
    finally:
        db.close()

    res = client.get(f"/api/leads/{lead_id}")
    assert res.status_code == 200
    data = res.json()

    # Deliverable 1: Lead Status (Properly reflects Needs More Information due to missing information items)
    assert data["status"] == "completed"
    assert data["lead_status"] == "Needs More Information"

    # Deliverable 2: Customer Information
    assert data["result"]["research_result"]["company_name"] == "DocCorp"
    assert data["result"]["research_result"]["business_context"] == "Healthcare billing and claims automation"

    # Deliverable 3: Extracted Requirements
    reqs = data["result"]["requirements"]["functional_requirements"]
    assert len(reqs) > 0
    assert any("10,000" in r for r in reqs)

    # Deliverable 4: Missing Information
    assert len(data["result"]["requirements"]["missing_information"]) == 2

    # Deliverable 5: Lead Score Breakdown
    assert data["result"]["qualification"]["composite_score"] == 86.0
    assert "formula" in data["result"]["qualification"]
    assert "weights" in data["result"]["qualification"]

    # Deliverable 6: Qualification Reasoning
    assert "DocumentAI Pro" in data["result"]["qualification"]["qualification_reasoning"]

    # Deliverable 7: Matching Solutions
    assert len(data["result"]["solution_matching"]["primary_solutions"]) > 0
    assert data["result"]["solution_matching"]["primary_solutions"][0]["coverage_percentage"] == 95

    # Deliverable 8 & 9: Proposed Solution & Proposal
    prop_res = client.get(f"/api/proposals/{lead_id}")
    assert prop_res.status_code == 200
    prop_data = prop_res.json()["proposal"]
    assert "DocumentAI Pro" in prop_data["proposed_solution"]
    assert prop_data["total_implementation_timeline"] == "4 weeks"

    # Deliverable 10: Follow-up Questions
    assert len(data["result"]["reviewer"]["follow_up_questions"]) == 1

    # Deliverable 11: Recommended Next Actions
    assert len(data["result"]["reviewer"]["recommended_next_steps"]) == 2

    # Deliverable 12: Grounding Verification
    assert data["result"]["reviewer"]["claim_verification"][0]["verified"] is True

    # Test list_leads returns fit_score and missing_information for the UI cards
    list_res = client.get("/api/leads")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert "leads" in list_data
    matched = next((l for l in list_data["leads"] if l["id"] == lead_id), None)
    assert matched is not None
    assert matched["composite_score"] == 86.0
    assert matched["fit_score"] == 90
    assert "missing_information" in matched
    assert len(matched["missing_information"]) == 2


def test_proposal_approval_and_send_workflows(client):
    """Verify proposal approve (via JSON body) and send endpoints update DB and lead status correctly."""
    db = db_module.SessionLocal()
    lead_id = "test-approve-lead"
    try:
        test_lead = Lead(
            id=lead_id,
            company_name="Approval Corp",
            inquiry_text="Need AI extraction for invoices and documents.",
            lead_status="Needs More Information",
            composite_score=78.0,
            completed_at=datetime.utcnow(),
            proposal_result={
                "title": "Enterprise Solution Proposal for Approval Corp",
                "executive_summary": "Summary text",
                "proposal_status": "draft",
            },
        )
        db.merge(test_lead)
        db.commit()
    finally:
        db.close()

    # 1. Approve via JSON Body (matching frontend Axios call)
    approve_res = client.post(
        f"/api/proposals/{lead_id}/approve",
        json={"approved_by": "Sales Director Jane"},
    )
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["status"] == "approved"
    assert approve_data["approved_by"] == "Sales Director Jane"
    assert "Proposal approved successfully" in approve_data["message"]

    # Verify DB Lead and Proposal records
    db = db_module.SessionLocal()
    try:
        updated_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        assert updated_lead.lead_status == "Qualified"  # Promoted from Needs More Information on approval
        assert updated_lead.proposal_result["proposal_status"] == "approved"
        assert updated_lead.proposal_result["approved_by"] == "Sales Director Jane"

        prop_record = db.query(Proposal).filter(Proposal.lead_id == lead_id).first()
        assert prop_record is not None
        assert prop_record.status == "approved"
        assert prop_record.approved_by == "Sales Director Jane"
    finally:
        db.close()

    # 2. Send via JSON Body with mock SMTP credentials
    original_host = settings.SMTP_HOST
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    try:
        settings.SMTP_HOST = "smtp.gmail.com"
        settings.SMTP_PORT = 587
        settings.SMTP_USER = "jane@approvalcorp.com"
        settings.SMTP_PASSWORD = "testapppassword123"
        settings.SMTP_USE_TLS = True

        from unittest.mock import MagicMock, patch
        mock_server = MagicMock()
        mock_server.send_message.return_value = {}

        with patch("smtplib.SMTP", return_value=mock_server):
            send_res = client.post(
                f"/api/proposals/{lead_id}/send",
                json={"recipient_email": "jane@approvalcorp.com"},
            )
            assert send_res.status_code == 200
            send_data = send_res.json()
            assert send_data["status"] == "sent"
            assert send_data["recipient"] == "jane@approvalcorp.com"

            db = db_module.SessionLocal()
            try:
                prop_record = db.query(Proposal).filter(Proposal.lead_id == lead_id).first()
                assert prop_record.status == "sent"
                assert prop_record.sent_to == "jane@approvalcorp.com"
                assert prop_record.sent_at is not None
            finally:
                db.close()
    finally:
        settings.SMTP_HOST = original_host
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass


def test_proposal_email_view_and_accept_portal(client):
    """Verify email-view renders interactive accept link and /accept route updates DB to Qualified & accepted."""
    db = db_module.SessionLocal()
    lead_id = "test-email-accept-portal"
    try:
        lead = Lead(
            id=lead_id,
            company_name="Acme Fintech",
            inquiry_text="Need high speed document extraction pipeline.",
            lead_status="Needs More Information",
            composite_score=80.0,
            completed_at=datetime.utcnow(),
            proposal_result={
                "title": "Enterprise Solution Proposal for Acme Fintech",
                "executive_summary": "High speed extraction pipeline with OCR.",
                "proposed_solution": "DocumentAI Pro Enterprise",
                "total_implementation_timeline": "3 weeks",
                "pricing_proposal": {"license": "$6,000/mo"},
                "proposal_status": "sent",
            },
        )
        db.merge(lead)
        db.commit()
    finally:
        db.close()

    # 1. Test /email-view renders interactive link (not dead mailto)
    view_res = client.get(f"/api/proposals/{lead_id}/email-view")
    assert view_res.status_code == 200
    html_body = view_res.text
    assert f"/api/proposals/{lead_id}/accept" in html_body
    assert "Accept &amp; Schedule Kickoff" in html_body or "Accept & Schedule Kickoff" in html_body
    assert f"mailto:{settings.SMTP_FROM_EMAIL}" not in html_body

    # 2. Test GET /{lead_id}/accept (client clicks button)
    accept_res = client.get(f"/api/proposals/{lead_id}/accept")
    assert accept_res.status_code == 200
    accept_html = accept_res.text
    assert "Proposal Accepted!" in accept_html
    assert "Acme Fintech" in accept_html
    assert "Qualified &amp; In Provisioning" in accept_html or "Qualified" in accept_html

    # 3. Verify lead and proposal status updated in database
    db = db_module.SessionLocal()
    try:
        updated = db.query(Lead).filter(Lead.id == lead_id).first()
        assert updated.lead_status == "Qualified"
        assert updated.proposal_result["status"] == "accepted"
        assert updated.proposal_result["accepted_at"] is not None

        prop_rec = db.query(Proposal).filter(Proposal.lead_id == lead_id).first()
        assert prop_rec is not None
        assert prop_rec.status == "accepted"
    finally:
        db.close()

    # 4. Test programmatic POST /{lead_id}/accept
    post_res = client.post(f"/api/proposals/{lead_id}/accept")
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "accepted"


def test_smtp_configuration_endpoints(client):
    """Verify dynamic SMTP config endpoints retrieve and update credentials."""
    # 1. GET /api/config/smtp
    get_res = client.get("/api/config/smtp")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert "configured" in get_data
    assert "smtp_host" in get_data
    assert "smtp_port" in get_data

    # 2. POST /api/config/smtp
    post_res = client.post(
        "/api/config/smtp",
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "demo_sender@gmail.com",
            "smtp_password": "testapppassword123",
            "smtp_from_email": "demo_sender@gmail.com",
            "smtp_use_tls": True,
        },
    )
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["configured"] is True
    assert post_data["smtp_user"] == "demo_sender@gmail.com"
    assert settings.SMTP_USER == "demo_sender@gmail.com"
    assert settings.SMTP_PASSWORD == "testapppassword123"



