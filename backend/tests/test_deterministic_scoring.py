import pytest
from app.services.scoring_engine import (
    calculate_fit_score,
    calculate_readiness_score,
    calculate_opportunity_score,
    calculate_risk_score,
    calculate_composite_lead_score,
    determine_qualification_status,
    evaluate_complete_lead,
    sanitize_missing_information,
)
from app.services.email_service import build_proposal_email_content
from app.config import settings


def test_identical_apex_inputs_produce_identical_scores_and_status():
    """Bug #1 Core Test: Two identical records for Apex Financial Technologies produce 100% identical outputs."""
    lead_input_1 = {
        "lead_id": "657f3d54-03e1-430c-b0c0-e56e1777f2c0",
        "company_name": "Apex Financial Technologies",
        "contact_name": "Marcus Vance",
        "email": "m.vance@apexfinancial.io",
        "industry": "Financial Services",
        "company_size": "500-1000 employees",
        "budget": "$15,000 - $35,000/month",
        "timeline": "1-2 months",
        "additional_context": "Security and SOC2 Type II compliance are mandatory. Current manual processing turnaround is 3-5 business days.",
        "inquiry_text": "We need an AI-powered document processing solution capable of extracting information from approximately 10,000 PDF invoices and financial statements monthly. Key requirements include high-accuracy OCR, table parsing, and integration with our internal risk assessment database via REST API.",
    }

    lead_input_2 = {
        "lead_id": "0343a937-f9af-4580-9d9f-4a170a80ed22",
        "company_name": "Apex Financial Technologies",
        "contact_name": "Marcus Vance",
        "email": "m.vance@apexfinancial.io",
        "industry": "Financial Services",
        "company_size": "500-1000 employees",
        "budget": "$15,000 - $35,000/month",
        "timeline": "1-2 months",
        "additional_context": "Security and SOC2 Type II compliance are mandatory. Current manual processing turnaround is 3-5 business days.",
        "inquiry_text": "We need an AI-powered document processing solution capable of extracting information from approximately 10,000 PDF invoices and financial statements monthly. Key requirements include high-accuracy OCR, table parsing, and integration with our internal risk assessment database via REST API.",
    }

    result_1 = evaluate_complete_lead(lead_input_1)
    result_2 = evaluate_complete_lead(lead_input_2)

    assert result_1["composite_score"] == result_2["composite_score"]
    assert result_1["fit_score"] == result_2["fit_score"]
    assert result_1["readiness_score"] == result_2["readiness_score"]
    assert result_1["opportunity_score"] == result_2["opportunity_score"]
    assert result_1["risk_score"] == result_2["risk_score"]
    assert result_1["lead_status"] == result_2["lead_status"]
    assert result_1["lead_status"] == "Qualified"
    assert result_1["composite_score"] >= settings.QUALIFIED_SCORE_THRESHOLD


def test_sanitize_missing_information_clears_confirmed_fields():
    lead_dict = {
        "budget": "$20,000/month",
        "timeline": "2 months",
        "company_size": "500 employees",
        "contact_name": "Sarah Connor",
    }
    raw_missing = [
        "Approved commercial budget range or expected investment not confirmed",
        "Target implementation timeline not specified",
        "Decision-maker and approval process",
        "Technical detail on document format",
    ]
    cleaned = sanitize_missing_information(raw_missing, lead_dict)
    assert cleaned == []


def test_missing_budget_forces_needs_more_information():
    lead_dict = {
        "company_name": "Incomplete Enterprise Corp",
        "inquiry_text": "We want to extract 10,000 PDFs per month.",
        "budget": None,
        "timeline": None,
    }
    raw_missing = ["Budget range or expected investment", "Target implementation timeline"]
    result = evaluate_complete_lead(lead_dict, requirements_result={"missing_information": raw_missing})
    assert result["lead_status"] == "Needs More Information"


def test_out_of_scope_lead_is_low_priority():
    lead_dict = {
        "company_name": "Student Project",
        "inquiry_text": "I need help with my school homework essay on bitcoin and shoes with zero budget free only.",
        "budget": "$0",
        "timeline": "today",
    }
    result = evaluate_complete_lead(lead_dict)
    assert result["composite_score"] < settings.NEEDS_INFO_SCORE_THRESHOLD
    assert result["lead_status"] == "Low Priority"


def test_proposal_email_uses_render_url_in_production(monkeypatch):
    """Bug #2 Core Test: Ensure accept link never generates localhost in production."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "RENDER_EXTERNAL_URL", "https://sales-ai-etew.onrender.com")

    proposal_data = {
        "title": "Enterprise AI Proposal for Test Corp",
        "total_implementation_timeline": "2 weeks",
        "customer_requirements": ["Requirement 1"],
        "pricing_proposal": {"platform_fee": "$10,000/mo"},
        "next_steps": ["Sign agreement"],
    }
    text_content, html_content = build_proposal_email_content(
        recipient_email="test@corp.com",
        company_name="Test Corp",
        proposal_data=proposal_data,
        lead_id="test-lead-1234",
    )

    expected_url = "https://sales-ai-etew.onrender.com/api/proposals/test-lead-1234/accept"
    assert expected_url in text_content
    assert expected_url in html_content
    assert "localhost:8001" not in text_content
    assert "localhost:8001" not in html_content


def test_proposal_email_resolves_request_forwarded_host():
    class DummyRequest:
        headers = {
            "x-forwarded-proto": "https",
            "x-forwarded-host": "sales-ai-etew.onrender.com",
        }

    proposal_data = {
        "title": "Enterprise AI Proposal",
        "total_implementation_timeline": "3 weeks",
    }
    text_content, html_content = build_proposal_email_content(
        recipient_email="test@corp.com",
        company_name="Test Corp",
        proposal_data=proposal_data,
        lead_id="lead-abc",
        request=DummyRequest(),
    )
    expected_url = "https://sales-ai-etew.onrender.com/api/proposals/lead-abc/accept"
    assert expected_url in text_content
    assert expected_url in html_content
