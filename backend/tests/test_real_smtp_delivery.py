"""Tests for Real SMTP Email Delivery, Email Validation, and Proposal Dispatch Audit Logging."""
import pytest
from unittest.mock import MagicMock, patch
import smtplib
import uuid
import httpx

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, init_db
from app.services.email_service import (
    validate_email_address,
    dispatch_proposal_email,
    build_proposal_email_content,
)
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
    try:
        yield db
    finally:
        db.close()


def get_auth_headers():
    if settings.API_AUTH_TOKEN:
        return {"Authorization": f"Bearer {settings.API_AUTH_TOKEN}"}
    return {}


def test_validate_email_address_valid():
    """Verify standard valid email formats pass validation."""
    valid_cases = [
        "client@example.com",
        "john.doe@company.org",
        "sales+lead@enterprise.ai",
        "first_last@sub.domain.co.uk",
    ]
    for email in valid_cases:
        is_valid, cleaned = validate_email_address(email)
        assert is_valid is True, f"Failed for {email}: {cleaned}"
        assert cleaned == email.strip()


def test_validate_email_address_invalid():
    """Verify invalid email formats are rejected with clear reasons."""
    invalid_cases = [
        "",
        None,
        "   ",
        "invalid-email",
        "user@",
        "@domain.com",
        "user@domain",
        "user name@domain.com",
        "user@ domain.com",
        "user@domain..com",
    ]
    for email in invalid_cases:
        is_valid, error = validate_email_address(email)
        assert is_valid is False, f"Expected invalid for '{email}', but got valid"
        assert len(error) > 0


def test_unconfigured_smtp_returns_failure():
    """Requirement: If SMTP is not configured, NEVER report sent or success."""
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    try:
        settings.SMTP_USER = None
        settings.SMTP_PASSWORD = None

        result = dispatch_proposal_email(
            recipient_email="client@example.com",
            company_name="Apex Corp",
            proposal_data={"title": "Test Proposal"},
            lead_id="test-lead-123",
        )

        assert result["success"] is False
        assert result["status"] == "failed"
        assert result["delivery_mode"] == "unconfigured"
        assert "SMTP server is not configured" in result["message"]
    finally:
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass


def test_smtp_live_delivery_success_mocked():
    """Verify successful SMTP delivery sets Message-ID and RFC headers."""
    original_host = settings.SMTP_HOST
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    try:
        settings.SMTP_HOST = "smtp.gmail.com"
        settings.SMTP_PORT = 587
        settings.SMTP_USER = "sender@gmail.com"
        settings.SMTP_PASSWORD = "testapppassword123"
        settings.SMTP_FROM_EMAIL = "sender@gmail.com"
        settings.SMTP_USE_TLS = True

        mock_server = MagicMock()
        mock_server.send_message.return_value = {}  # No refused recipients

        with patch("smtplib.SMTP", return_value=mock_server):
            result = dispatch_proposal_email(
                recipient_email="client@acme.com",
                company_name="Acme Corp",
                proposal_data={"title": "Acme Solution Proposal", "proposed_solution": "AI Engine"},
                lead_id="lead-456",
            )

            assert result["success"] is True
            assert result["status"] == "sent"
            assert result["delivery_mode"] == "smtp_live"
            assert result["recipient"] == "client@acme.com"
            assert "message_id" in result
            assert result["message_id"].startswith("<") and result["message_id"].endswith(">")

            # Check SMTP methods called
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("sender@gmail.com", "testapppassword123")
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
    finally:
        settings.SMTP_HOST = original_host
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass


def test_smtp_authentication_failure_handling():
    """Verify SMTPAuthenticationError returns safe error without leaking credentials."""
    original_host = settings.SMTP_HOST
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    try:
        settings.SMTP_HOST = "smtp.gmail.com"
        settings.SMTP_PORT = 587
        settings.SMTP_USER = "sender@gmail.com"
        settings.SMTP_PASSWORD = "wrongpassword"
        settings.SMTP_USE_TLS = True

        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted")

        with patch("smtplib.SMTP", return_value=mock_server):
            result = dispatch_proposal_email(
                recipient_email="client@acme.com",
                company_name="Acme Corp",
                proposal_data={"title": "Acme Solution Proposal"},
                lead_id="lead-456",
            )

            assert result["success"] is False
            assert result["status"] == "failed"
            assert result["delivery_mode"] == "smtp_error"
            assert "authentication error" in result["message"].lower()
            # Must NOT expose password
            assert "wrongpassword" not in str(result)
    finally:
        settings.SMTP_HOST = original_host
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass


def test_smtp_connection_failure_handling():
    """Verify connection timeout/refusal returns status=failed."""
    original_host = settings.SMTP_HOST
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    try:
        settings.SMTP_HOST = "unreachable.mail.server"
        settings.SMTP_PORT = 587
        settings.SMTP_USER = "sender@gmail.com"
        settings.SMTP_PASSWORD = "secretpassword"

        with patch("smtplib.SMTP", side_effect=smtplib.SMTPConnectError(421, b"Service not available")):
            result = dispatch_proposal_email(
                recipient_email="client@acme.com",
                company_name="Acme Corp",
                proposal_data={"title": "Acme Solution Proposal"},
                lead_id="lead-456",
            )

            assert result["success"] is False
            assert result["status"] == "failed"
            assert "connect" in result["message"].lower()
    finally:
        settings.SMTP_HOST = original_host
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass


def test_send_proposal_api_invalid_email(client, db_session):
    """Verify POST /api/proposals/{lead_id}/send returns HTTP 400 on invalid email."""
    lead_id = str(uuid.uuid4())
    lead = Lead(
        id=lead_id,
        company_name="Invalid Email Co",
        inquiry_text="Need AI automation",
        lead_status="Qualified",
        proposal_result={"title": "AI Proposal", "proposed_solution": "Architecture"},
    )
    db_session.add(lead)
    db_session.commit()

    res = client.post(
        f"/api/proposals/{lead_id}/send",
        json={"recipient_email": "not-an-email"},
        headers=get_auth_headers(),
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["status"] == "failed"
    assert "Invalid email format" in data["message"]


def test_send_proposal_api_unconfigured_smtp(client, db_session):
    """Verify POST /api/proposals/{lead_id}/send fails when SMTP is unconfigured and does not mark sent."""
    lead_id = str(uuid.uuid4())
    lead = Lead(
        id=lead_id,
        company_name="Unconfigured SMTP Co",
        inquiry_text="Need AI automation",
        lead_status="Qualified",
        proposal_result={"title": "AI Proposal", "proposed_solution": "Architecture"},
    )
    db_session.add(lead)
    db_session.commit()

    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    try:
        settings.SMTP_USER = None
        settings.SMTP_PASSWORD = None

        res = client.post(
            f"/api/proposals/{lead_id}/send",
            json={"recipient_email": "client@enterprise.com"},
            headers=get_auth_headers(),
        )
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["status"] == "failed"
        assert "SMTP server is not configured" in data["message"]

        # Verify proposal status in DB was NOT marked sent
        prop = db_session.query(Proposal).filter(Proposal.lead_id == lead_id).first()
        if prop:
            assert prop.status != "sent"

        # Verify audit activity recorded failure
        activity = db_session.query(UserActivity).filter(
            UserActivity.lead_id == lead_id,
            UserActivity.action == "proposal_email_failed",
        ).first()
        assert activity is not None
        assert activity.details["recipient"] == "client@enterprise.com"
    finally:
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass


def test_send_proposal_api_success_mocked_smtp(client, db_session):
    """Verify POST /api/proposals/{lead_id}/send records real send and Message-ID when SMTP succeeds."""
    lead_id = str(uuid.uuid4())
    lead = Lead(
        id=lead_id,
        company_name="Successful Send Co",
        inquiry_text="Need AI automation",
        lead_status="Qualified",
        proposal_result={"title": "AI Proposal", "proposed_solution": "Architecture"},
    )
    db_session.add(lead)
    db_session.commit()

    original_host = settings.SMTP_HOST
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    try:
        settings.SMTP_HOST = "smtp.gmail.com"
        settings.SMTP_PORT = 587
        settings.SMTP_USER = "sender@gmail.com"
        settings.SMTP_PASSWORD = "testapppassword123"
        settings.SMTP_USE_TLS = True

        mock_server = MagicMock()
        mock_server.send_message.return_value = {}

        with patch("smtplib.SMTP", return_value=mock_server):
            res = client.post(
                f"/api/proposals/{lead_id}/send",
                json={"recipient_email": "client@validcorp.com"},
                headers=get_auth_headers(),
            )
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["status"] == "sent"
            assert data["delivery_mode"] == "smtp_live"
            assert data["recipient"] == "client@validcorp.com"
            assert "message_id" in data
            assert data["message_id"].startswith("<")

            # Check DB Proposal
            prop = db_session.query(Proposal).filter(Proposal.lead_id == lead_id).first()
            assert prop is not None
            assert prop.status == "sent"
            assert prop.sent_to == "client@validcorp.com"

            # Check DB UserActivity audit log
            activity = db_session.query(UserActivity).filter(
                UserActivity.lead_id == lead_id,
                UserActivity.action == "proposal_email_sent",
            ).first()
            assert activity is not None
            assert activity.details["recipient"] == "client@validcorp.com"
            assert activity.details["message_id"] == data["message_id"]
    finally:
        settings.SMTP_HOST = original_host
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass


def test_http_api_resend_delivery(monkeypatch):
    """Verify proposal dispatch via Resend REST API (port 443)."""
    original_resend = settings.RESEND_API_KEY
    try:
        settings.RESEND_API_KEY = "re_test_dummy_key_123"

        class DummyResponse:
            status_code = 200
            headers = {"content-type": "application/json"}
            def json(self):
                return {"id": "resend_msg_mock_999"}

        def dummy_post(*args, **kwargs):
            return DummyResponse()

        monkeypatch.setattr(httpx.Client, "post", dummy_post)

        res = dispatch_proposal_email(
            recipient_email="client@example.com",
            company_name="Acme Inc",
            proposal_data={"title": "Cloud Migration Proposal"},
            lead_id="lead-resend-test",
        )

        assert res["success"] is True
        assert res["status"] == "sent"
        assert res["delivery_mode"] == "resend_api"
        assert res["message_id"] == "resend_msg_mock_999"
        assert "Resend API" in res["message"]
    finally:
        settings.RESEND_API_KEY = original_resend


def test_oserror_errno_101_render_blocked_message(monkeypatch):
    """Verify OSError [Errno 101] returns actionable Render Free Tier port block explanation."""
    original_host = settings.SMTP_HOST
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    try:
        settings.SMTP_HOST = "smtp.gmail.com"
        settings.SMTP_PORT = 587
        settings.SMTP_USER = "sender@gmail.com"
        settings.SMTP_PASSWORD = "testpassword123"

        def raise_errno_101(*args, **kwargs):
            err = OSError(101, "Network is unreachable")
            raise err

        monkeypatch.setattr(smtplib, "SMTP", raise_errno_101)

        res = dispatch_proposal_email(
            recipient_email="client@example.com",
            company_name="Acme Inc",
            proposal_data={"title": "Cloud Migration Proposal"},
            lead_id="lead-oserror-test",
        )

        assert res["success"] is False
        assert res["status"] == "failed"
        assert res["delivery_mode"] == "smtp_network_error"
        assert "Render Free Tier" in res["message"]
        assert "Resend" in res["message"]
        assert "101" in res["error"] or "Network is unreachable" in res["error"]
    finally:
        settings.SMTP_HOST = original_host
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass

