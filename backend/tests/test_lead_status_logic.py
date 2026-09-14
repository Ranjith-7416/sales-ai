from app.status_utils import normalize_lead_status
from app.agents.qualification_agent import calculate_deterministic_qualification


def test_status_requires_more_information_when_required_fields_are_missing():
    assert normalize_lead_status(
        "Qualified",
        90,
        ["Budget range or expected investment", "Decision-maker and approval process"],
    ) == "Needs More Information"


def test_status_is_qualified_only_when_complete_and_high_score():
    assert normalize_lead_status("Qualified", 85, []) == "Qualified"


def test_status_is_low_priority_for_low_score():
    assert normalize_lead_status("Low Priority", 35, []) == "Low Priority"


def test_missing_information_takes_priority_over_low_score():
    assert normalize_lead_status("Low Priority", 17, ["Budget range or expected investment"]) == "Needs More Information"


def test_qualification_score_is_deterministic_and_weighted():
    result = calculate_deterministic_qualification({
        "fit_score": 80,
        "readiness_score": 70,
        "opportunity_score": 90,
        "risk_score": 20,
        "lead_status": "Low Priority",
        "composite_score": 1,
    }, [])

    assert result["composite_score"] == 80.5
    assert result["lead_status"] == "Qualified"
