from app.services.proposal_validator import validate_proposal
from app.agents.proposal_agent import _is_usable_proposal


def test_validator_allows_catalog_backed_facts():
    result = validate_proposal(
        {
            "executive_summary": "DocumentAI Pro supports PDF processing at $5,000 - $50,000/month.",
            "customer_requirements": ["Extract information from PDF documents."],
            "proposed_solution": "DocumentAI Pro provides document processing.",
            "success_metrics": [],
            "next_steps": [],
            "implementation_roadmap": [],
            "sections": [],
        },
        {"functional_requirements": ["Extract information from PDF documents."]},
        {"primary_solutions": [{"product_name": "DocumentAI Pro", "pricing": "$5,000 - $50,000/month"}]},
    )
    assert result["approved"] is True


def test_validator_blocks_unsupported_commercial_claims():
    result = validate_proposal(
        {
            "executive_summary": "Our platform guarantees 100% accuracy for $1/month.",
            "customer_requirements": [],
            "proposed_solution": "",
            "success_metrics": [],
            "next_steps": [],
            "implementation_roadmap": [],
            "sections": [],
        }
    )
    assert result["approved"] is False
    assert result["unsupported_sentences"]


def test_validator_allows_grounded_solution_coverage_percentage():
    result = validate_proposal(
        {
            "proposed_solution": "DocumentAI Pro provides 90% native requirement coverage and 99.8% OCR accuracy.",
            "customer_requirements": [],
            "success_metrics": [],
            "next_steps": [],
            "implementation_roadmap": [],
            "sections": [],
        },
        {},
        {
            "primary_solutions": [
                {
                    "product_name": "DocumentAI Pro",
                    "coverage_percentage": 90,
                    "features_matched": ["OCR with 99.8% accuracy"],
                }
            ]
        },
    )

    assert result["approved"] is True


def test_validator_checks_supported_pricing_and_service_levels():
    result = validate_proposal(
        {
            "pricing_proposal": {"base_product": "$5,000 - $50,000/month"},
            "support_service_levels": {"tier": "24/7 Premium"},
        },
        {},
        {"primary_solutions": [{"product_name": "DocumentAI Pro"}]},
    )

    assert result["approved"] is True


def test_validator_blocks_unsupported_pricing_service_certification_and_timeline():
    result = validate_proposal(
        {
            "pricing_proposal": {"base_product": "$1/month"},
            "support_service_levels": {"response_time": "5 minutes"},
            "certifications": ["SOC 3"],
            "total_implementation_timeline": "3 days",
        }
    )

    assert result["approved"] is False
    assert len(result["unsupported_sentences"]) >= 4


def test_empty_grounding_repair_is_not_usable_proposal():
    assert _is_usable_proposal({"executive_summary": "", "proposed_solution": ""}) is False
    assert _is_usable_proposal({
        "executive_summary": "Grounded summary",
        "proposed_solution": "Grounded solution",
    }) is True
