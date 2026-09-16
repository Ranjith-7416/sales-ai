"""Tests for Proposal Auto-Generation, Approval, and Full Lifecycle Recovery.

Verifies that clicking 'Approve Proposal' or accessing proposal endpoints for any lead
never fails with 'No proposal to approve' or 404, but seamlessly recovers or generates
a catalog-grounded proposal, updates the database, promotes lead status, and audits actions.
"""
import pytest
from unittest.mock import MagicMock, patch
import uuid
from datetime import datetime

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, init_db
from app.config import settings
from app.models import Lead, Proposal, UserActivity


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
    created_ids = []

    def tracker(lead):
        db.add(lead)
        created_ids.append(lead.id)
        return lead

    db.track_add = tracker
    try:
        yield db
    finally:
        for lid in created_ids:
            try:
                db.query(UserActivity).filter(UserActivity.lead_id == lid).delete()
                db.query(Proposal).filter(Proposal.lead_id == lid).delete()
                db.query(Lead).filter(Lead.id == lid).delete()
                db.commit()
            except Exception:
                db.rollback()
        db.close()


def get_auth_headers():
    if settings.API_AUTH_TOKEN:
        return {"Authorization": f"Bearer {settings.API_AUTH_TOKEN}"}
    return {}


def test_approve_proposal_auto_generates_when_proposal_is_none(client, db_session):
    """
    CRITICAL REGRESSION TEST:
    Verifies that calling POST /api/proposals/{lead_id}/approve on a lead with
    lead.proposal_result = None does NOT fail with 'No proposal to approve',
    but automatically generates the grounded proposal, marks it approved,
    promotes lead status to Qualified, and records Proposal & UserActivity in DB.
    """
    lead_id = f"test-lead-no-prop-{uuid.uuid4().hex[:8]}"
    lead = Lead(
        id=lead_id,
        company_name="InnovateAI Corp",
        contact_name="Sarah Jenkins",
        email="sarah@innovateai.com",
        inquiry_text="We need high-throughput OCR extraction for 50,000 PDF invoices monthly with SOC 2 compliance.",
        industry="Financial Services",
        budget="$10,000/month",
        timeline="3 weeks",
        lead_status="Needs More Information",
        proposal_result=None,  # Crucial: NO PRE-EXISTING PROPOSAL!
        pipeline_result=None,
        created_at=datetime.utcnow(),
    )
    db_session.track_add(lead)
    db_session.commit()

    # User clicks 'Approve Proposal'
    res = client.post(
        f"/api/proposals/{lead_id}/approve",
        json={"approved_by": "VP of Sales Alex"},
        headers=get_auth_headers(),
    )

    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["status"] == "approved"
    assert data["approved_by"] == "VP of Sales Alex"
    assert "Proposal approved successfully" in data["message"]
    assert "proposal" in data
    assert data["proposal"] is not None
    assert "DocumentAI Pro" in data["proposal"]["proposed_solution"]
    assert data["proposal"]["proposal_status"] == "approved"

    # Verify database state
    db = SessionLocal()
    try:
        updated_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        assert updated_lead is not None
        assert updated_lead.lead_status == "Qualified"  # Promoted from Needs More Information
        assert updated_lead.proposal_result is not None
        assert updated_lead.proposal_result["proposal_status"] == "approved"
        assert updated_lead.proposal_result["approved_by"] == "VP of Sales Alex"

        proposal_row = db.query(Proposal).filter(Proposal.lead_id == lead_id).first()
        assert proposal_row is not None
        assert proposal_row.status == "approved"
        assert proposal_row.approved_by == "VP of Sales Alex"

        activity = db.query(UserActivity).filter(
            UserActivity.lead_id == lead_id,
            UserActivity.action == "proposal_approved",
        ).first()
        assert activity is not None
        assert activity.details.get("approved_by") == "VP of Sales Alex"
    finally:
        db.close()


def test_generate_proposal_endpoint(client, db_session):
    """Verify POST /api/proposals/{lead_id}/generate explicitly creates a proposal on demand."""
    lead_id = f"test-lead-gen-{uuid.uuid4().hex[:8]}"
    lead = Lead(
        id=lead_id,
        company_name="Apex Logistics",
        inquiry_text="Automate bill of lading extraction and container manifests.",
        lead_status="Processing",
        proposal_result=None,
        created_at=datetime.utcnow(),
    )
    db_session.track_add(lead)
    db_session.commit()

    res = client.post(
        f"/api/proposals/{lead_id}/generate",
        json={"regenerate": False},
        headers=get_auth_headers(),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Proposal generated successfully"
    assert data["status"] == "draft"
    assert data["proposal"]["title"] == "Enterprise AI Solution Proposal for Apex Logistics"

    # Verify persisted in database
    db = SessionLocal()
    try:
        updated_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        assert updated_lead.proposal_result is not None
        assert updated_lead.proposal_result["title"] == "Enterprise AI Solution Proposal for Apex Logistics"
    finally:
        db.close()


def test_get_proposal_auto_generates_when_missing(client, db_session):
    """Verify GET /api/proposals/{lead_id} returns 200 with proposal even if not pre-generated."""
    lead_id = f"test-lead-get-{uuid.uuid4().hex[:8]}"
    lead = Lead(
        id=lead_id,
        company_name="BioHealth Analytics",
        inquiry_text="Clinical trial document extraction and patient form processing.",
        lead_status="Qualified",
        proposal_result=None,
        created_at=datetime.utcnow(),
    )
    db_session.track_add(lead)
    db_session.commit()

    res = client.get(
        f"/api/proposals/{lead_id}",
        headers=get_auth_headers(),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["lead_id"] == lead_id
    assert data["proposal"] is not None
    assert "Enterprise AI Solution Proposal for BioHealth Analytics" in data["proposal"]["title"]


def test_export_proposal_with_auto_generation(client, db_session):
    """Verify GET /api/proposals/{lead_id}/export generates and exports markdown seamlessly."""
    lead_id = f"test-lead-exp-{uuid.uuid4().hex[:8]}"
    lead = Lead(
        id=lead_id,
        company_name="Nexus Retail Group",
        inquiry_text="Receipt and purchase order OCR automation with warehouse webhooks.",
        lead_status="Qualified",
        proposal_result=None,
        created_at=datetime.utcnow(),
    )
    db_session.track_add(lead)
    db_session.commit()

    res = client.get(
        f"/api/proposals/{lead_id}/export",
        headers=get_auth_headers(),
    )
    assert res.status_code == 200
    data = res.json()
    assert "markdown" in data
    assert "# Enterprise Solution Proposal" in data["markdown"]
    assert "Nexus Retail Group" in data["markdown"]


def test_view_email_html_with_auto_generation(client, db_session):
    """Verify GET /api/proposals/{lead_id}/email-view returns valid HTML preview without failing."""
    lead_id = f"test-lead-email-{uuid.uuid4().hex[:8]}"
    lead = Lead(
        id=lead_id,
        company_name="Starlight Media",
        email="contact@starlightmedia.com",
        inquiry_text="Contract analysis and script metadata extraction.",
        lead_status="Qualified",
        proposal_result=None,
        created_at=datetime.utcnow(),
    )
    db_session.track_add(lead)
    db_session.commit()

    res = client.get(
        f"/api/proposals/{lead_id}/email-view",
        headers=get_auth_headers(),
    )
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Starlight Media" in res.text


def test_send_proposal_with_auto_generation(client, db_session):
    """Verify sending proposal to a lead that had no proposal automatically creates it and sends via SMTP."""
    lead_id = f"test-lead-send-{uuid.uuid4().hex[:8]}"
    lead = Lead(
        id=lead_id,
        company_name="OmniGlobal Tech",
        email="client@omniglobal.com",
        inquiry_text="Global enterprise invoice automation.",
        lead_status="Qualified",
        proposal_result=None,
        created_at=datetime.utcnow(),
    )
    db_session.track_add(lead)
    db_session.commit()

    original_host = settings.SMTP_HOST
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    try:
        settings.SMTP_HOST = "smtp.gmail.com"
        settings.SMTP_PORT = 587
        settings.SMTP_USER = "sender@company.com"
        settings.SMTP_PASSWORD = "apppassword123"
        settings.SMTP_USE_TLS = True

        mock_server = MagicMock()
        mock_server.send_message.return_value = {}

        with patch("smtplib.SMTP", return_value=mock_server):
            res = client.post(
                f"/api/proposals/{lead_id}/send",
                json={"recipient_email": "client@omniglobal.com"},
                headers=get_auth_headers(),
            )
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["status"] == "sent"
            assert data["recipient"] == "client@omniglobal.com"
            assert "message_id" in data
    finally:
        settings.SMTP_HOST = original_host
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass
