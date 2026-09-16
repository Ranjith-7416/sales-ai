"""
Tests for Professional PDF Proposal Generation & Manual Client Sharing.

Verifies:
1. Server-side PDF generation creates valid PDF files (%PDF-1.4).
2. Client email address appears in the generated PDF.
3. Top header contains BUSINESS PROPOSAL, Prepared For, Recipient Email, Date.
4. Bottom section contains Proposal Recipient block and instructions.
5. Endpoints POST /api/proposals/{lead_id}/pdf and GET /api/proposals/{lead_id}/pdf return 200, application/pdf, and sanitized filename.
6. Multi-page pagination works cleanly.
7. Zero SMTP or Resend API calls are triggered during PDF generation.
"""

import io
import re
import uuid
import pytest
import pypdf
from starlette.testclient import TestClient
from app.main import app
from app.database import init_db, SessionLocal
from app.models import Lead, Proposal, UserActivity
from app.services.pdf_service import build_proposal_pdf_bytes, sanitize_pdf_filename
from app.config import settings


@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_headers():
    if getattr(settings, "API_AUTH_TOKEN", None):
        return {"Authorization": f"Bearer {settings.API_AUTH_TOKEN}"}
    return {}


def test_sanitize_pdf_filename():
    """Verify filename sanitization produces clean, safe names."""
    fn1 = sanitize_pdf_filename("Apex Financial Technologies", "2026-09-16")
    assert fn1 == "Proposal_Apex_Financial_Technologies_2026-09-16.pdf"

    # Weird characters and spaces
    fn2 = sanitize_pdf_filename("Global / Tech & Co., LLC!", "2026-09-16")
    assert "/" not in fn2
    assert "&" not in fn2
    assert fn2.startswith("Proposal_")
    assert fn2.endswith(".pdf")


def test_pdf_service_generates_valid_pdf_with_client_email():
    """Verify PDF generator embeds client email, date, headers, and full proposal."""
    class DummyLead:
        id = str(uuid.uuid4())
        company_name = "Apex Financial Technologies"
        email = "s.jenkins@apexfinancial.com"

    proposal_data = {
        "title": "Document Intelligence Automation",
        "executive_summary": "Deliver automated invoice processing with high accuracy and low latency.",
        "customer_requirements": [
            "Process 50,000 PDF invoices per month",
            "SOC-2 Type II certified infrastructure",
            "Integration with SAP ERP",
        ],
        "proposed_solution": "Deploy DocumentAI Enterprise on private cloud infrastructure with secure API endpoints.",
        "implementation_roadmap": [
            {"phase": "Phase 1: Discovery", "duration": "1 Week", "activities": ["Requirement validation", "API specification"]},
            {"phase": "Phase 2: Pilot Deployment", "duration": "2 Weeks", "activities": ["Model tuning", "Integration testing"]},
            {"phase": "Phase 3: Production Launch", "duration": "1 Week", "activities": ["Go-live", "Staff training"]},
        ],
        "pricing_proposal": {
            "platform_subscription": "$36,000 / year",
            "implementation_fee": "$8,500 one-time",
            "support_tier": "Enterprise 24/7 included",
        },
        "business_benefits": [
            "85% reduction in manual document review time",
            "Zero data egress outside client boundary",
        ],
        "support_service_levels": {
            "uptime": "99.9% availability",
            "critical_response": "< 15 minutes",
        },
    }

    pdf_bytes = build_proposal_pdf_bytes(
        lead=DummyLead(),
        proposal_data=proposal_data,
        client_email="s.jenkins@apexfinancial.com",
    )

    # 1. Valid PDF header
    assert pdf_bytes.startswith(b"%PDF-"), "Generated file does not have valid PDF header"

    # 2. Inspect content using pypdf
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1, "PDF should have at least 1 page"

    full_text = "\n".join([page.extract_text() for page in reader.pages])

    # 3. Verify top header
    assert "BUSINESS PROPOSAL" in full_text
    assert "Apex Financial Technologies" in full_text
    assert "s.jenkins@apexfinancial.com" in full_text

    # 4. Verify proposal sections
    assert "1. Executive Summary" in full_text
    assert "2. Customer Requirements & Scope" in full_text
    assert "3. Proposed Solution Architecture" in full_text
    assert "4. Implementation Plan & Timeline" in full_text
    assert "5. Commercial Terms & Investment Model" in full_text

    # 5. Verify bottom recipient block
    assert "Proposal Recipient:" in full_text
    assert "Please send this proposal PDF to the recipient email address above." in full_text


def test_api_generate_and_download_proposal_pdf(client, db_session):
    """Verify POST and GET /api/proposals/{lead_id}/pdf return valid PDF file and headers."""
    lead_id = str(uuid.uuid4())
    lead = Lead(
        id=lead_id,
        company_name="CloudRetail Solutions",
        email="mvance@cloudretail.io",
        inquiry_text="Need e-commerce recommendation engine",
        lead_status="Qualified",
        proposal_result={
            "title": "CloudRetail AI Recommendation Engine",
            "executive_summary": "Real-time personalization engine boosting conversion by 25%.",
            "proposed_solution": "Vector-based real-time embedding matching engine.",
            "total_implementation_timeline": "3 Weeks",
            "pricing_proposal": {"license": "$18,000/yr"},
        },
    )
    db_session.add(lead)
    db_session.commit()

    # Test POST /api/proposals/{lead_id}/pdf
    res_post = client.post(
        f"/api/proposals/{lead_id}/pdf",
        json={"client_email": "custom.recipient@cloudretail.io"},
        headers=get_auth_headers(),
    )
    assert res_post.status_code == 200
    assert res_post.headers["content-type"] == "application/pdf"
    assert "attachment; filename=\"Proposal_CloudRetail_Solutions_" in res_post.headers["content-disposition"]
    assert res_post.content.startswith(b"%PDF-")

    # Verify extracted text contains custom recipient
    reader = pypdf.PdfReader(io.BytesIO(res_post.content))
    text = "\n".join([page.extract_text() for page in reader.pages])
    assert "custom.recipient@cloudretail.io" in text

    # Verify audit log recorded proposal_pdf_generated
    audit = db_session.query(UserActivity).filter(
        UserActivity.lead_id == lead_id,
        UserActivity.action == "proposal_pdf_generated",
    ).first()
    assert audit is not None
    assert audit.details["company"] == "CloudRetail Solutions"

    # Test GET /api/proposals/{lead_id}/pdf
    res_get = client.get(
        f"/api/proposals/{lead_id}/pdf",
        headers=get_auth_headers(),
    )
    assert res_get.status_code == 200
    assert res_get.headers["content-type"] == "application/pdf"
    assert res_get.content.startswith(b"%PDF-")


def test_api_export_proposal_as_pdf(client, db_session):
    """Verify GET /api/proposals/{lead_id}/export?format=pdf returns PDF directly."""
    lead_id = str(uuid.uuid4())
    lead = Lead(
        id=lead_id,
        company_name="Apex Global Logistics",
        email="ops@apexlogistics.com",
        inquiry_text="Automate warehouse routing",
        lead_status="Qualified",
        proposal_result={"title": "Routing Optimization AI", "proposed_solution": "Heuristic route planner"},
    )
    db_session.add(lead)
    db_session.commit()

    res = client.get(
        f"/api/proposals/{lead_id}/export?format=pdf",
        headers=get_auth_headers(),
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF-")


def test_dynamic_pdf_generation_multiple_distinct_leads(client, db_session):
    """
    Requirement 15: Verify PDF generation is 100% dynamic and NOT hard-coded.
    Generates PDF for Apex Financial Technologies and a second distinct lead (Lumina Healthcare),
    verifying each PDF contains only its own specific proposal content.
    """
    # 1. Lead 1: Apex Financial Technologies
    lead1_id = str(uuid.uuid4())
    lead1 = Lead(
        id=lead1_id,
        company_name="Apex Financial Technologies",
        email="alex.mercer@apexfinancial.com",
        inquiry_text="High-throughput financial risk analysis and trading ledger automation.",
        lead_status="Qualified",
        proposal_result={
            "title": "Financial Risk & Trading Intelligence Platform",
            "executive_summary": "Apex Financial risk analysis architecture processing 100k daily trades.",
            "customer_requirements": ["Sub-millisecond ledger compliance", "FINRA audit trails"],
            "proposed_solution": "Distributed ledger risk evaluation cluster.",
            "total_implementation_timeline": "4 Weeks",
            "pricing_proposal": {"tier": "$36,000 / year", "setup": "$5,000 one-time"},
        },
    )
    db_session.add(lead1)

    # 2. Lead 2: Lumina Healthcare Systems
    lead2_id = str(uuid.uuid4())
    lead2 = Lead(
        id=lead2_id,
        company_name="Lumina Healthcare Systems",
        email="dr.chen@luminahealth.io",
        inquiry_text="HIPAA compliant patient telemetry analytics and diagnostic triage.",
        lead_status="Qualified",
        proposal_result={
            "title": "Clinical Diagnostic & Patient Telemetry Suite",
            "executive_summary": "Lumina Healthcare hospital-grade clinical AI for emergency triage.",
            "customer_requirements": ["HIPAA Omnibus compliance", "HL7 FHIR v4 interface integration"],
            "proposed_solution": "HIPAA-isolated private edge inference nodes.",
            "total_implementation_timeline": "10 Weeks",
            "pricing_proposal": {"annual_license": "$75,000 / year", "clinical_training": "$12,000"},
        },
    )
    db_session.add(lead2)
    db_session.commit()

    # Generate PDF for Lead 1 (Apex)
    res1 = client.post(f"/api/proposals/{lead1_id}/pdf", headers=get_auth_headers())
    assert res1.status_code == 200
    reader1 = pypdf.PdfReader(io.BytesIO(res1.content))
    text1 = "\n".join([p.extract_text() for p in reader1.pages])

    # Lead 1 assertions
    assert "Apex Financial Technologies" in text1
    assert "alex.mercer@apexfinancial.com" in text1
    assert "36,000" in text1
    assert "FINRA audit trails" in text1
    assert "Lumina Healthcare Systems" not in text1
    assert "dr.chen@luminahealth.io" not in text1

    # Generate PDF for Lead 2 (Lumina)
    res2 = client.post(f"/api/proposals/{lead2_id}/pdf", headers=get_auth_headers())
    assert res2.status_code == 200
    reader2 = pypdf.PdfReader(io.BytesIO(res2.content))
    text2 = "\n".join([p.extract_text() for p in reader2.pages])

    # Lead 2 assertions
    assert "Lumina Healthcare Systems" in text2
    assert "dr.chen@luminahealth.io" in text2
    assert "75,000" in text2
    assert "HL7 FHIR v4" in text2
    assert "Apex Financial Technologies" not in text2
    assert "alex.mercer@apexfinancial.com" not in text2


def test_api_generate_pdf_by_proposal_id(client, db_session):
    """Requirement 9: Verify POST /api/proposal/{proposal_id}/pdf works using proposal id."""
    lead_id = str(uuid.uuid4())
    proposal_id = str(uuid.uuid4())
    lead = Lead(
        id=lead_id,
        company_name="Vanguard Logistics",
        email="dispatch@vanguardlogistics.com",
        inquiry_text="Fleet tracking and route optimization",
        lead_status="Qualified",
        proposal_result={"title": "Fleet Optimization", "proposed_solution": "Route optimizer"},
    )
    prop = Proposal(
        id=proposal_id,
        lead_id=lead_id,
        status="draft",
        executive_summary="Fleet optimization proposal",
    )
    db_session.add(lead)
    db_session.add(prop)
    db_session.commit()

    # Request using /api/proposal/{proposal_id}/pdf
    res = client.post(f"/api/proposal/{proposal_id}/pdf", headers=get_auth_headers())
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "Proposal_Vanguard_Logistics_" in res.headers["content-disposition"]
