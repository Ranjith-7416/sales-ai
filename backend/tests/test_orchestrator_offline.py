import pytest

from app.agents import orchestrator
from app.main import _normalize_lead_input_for_background
from app.schemas import LeadInputSchema, ReviewerOutput


def test_normalize_lead_input_for_background_accepts_schema_or_dict():
    schema_input = LeadInputSchema(
        company_name="Acme",
        inquiry_text="Need PDF extraction",
        industry="Healthcare",
        company_size="50-100",
        budget="$5k",
        timeline="This quarter",
        additional_context="Need approvals",
    )

    normalized_schema = _normalize_lead_input_for_background(schema_input)
    assert normalized_schema["inquiry_text"] == "Need PDF extraction"

    normalized_dict = _normalize_lead_input_for_background({
        "company_name": "Acme",
        "inquiry_text": "Need PDF extraction",
    })
    assert normalized_dict["inquiry_text"] == "Need PDF extraction"


@pytest.mark.asyncio
async def test_orchestrator_runs_all_required_stages_without_llm(monkeypatch):
    monkeypatch.setattr(orchestrator, "_record_agent_execution", lambda *args, **kwargs: None)

    async def research(**kwargs):
        return {
            "company_name": kwargs["company_name"],
            "industry_vertical": "Healthcare",
            "company_size": "500-1000",
            "location": "Unknown",
            "business_model": "Healthcare technology",
            "key_products_services": "Clinical services",
            "market_position": "Unknown",
            "recent_news": [],
        }

    async def requirements(**kwargs):
        return {
            "functional_requirements": ["PDF extraction"],
            "non_functional_requirements": {},
            "constraints": {},
            "missing_information": [],
            "assumptions": [],
            "priority_mapping": {"must_have": ["PDF extraction"], "nice_to_have": []},
        }

    async def qualification(**kwargs):
        return {
            "lead_status": "Qualified",
            "composite_score": 80,
            "fit_score": 80,
            "fit_evidence": "Evidence",
            "readiness_score": 80,
            "readiness_evidence": "Evidence",
            "opportunity_score": 80,
            "opportunity_evidence": "Evidence",
            "risk_score": 20,
            "risk_evidence": "Evidence",
            "qualification_reasoning": "Evidence",
            "score_drivers": [],
        }

    async def solution(**kwargs):
        return {
            "primary_solutions": [{
                "product_name": "DocumentAI Pro",
                "coverage_percentage": 90,
                "features_matched": ["PDF extraction"],
                "features_missing": [],
                "pricing": "$5,000/month",
                "delivery_timeline": "2-4 weeks",
                "certifications": [],
            }],
            "complementary_services": [],
            "add_ons_recommended": [],
            "requirement_coverage_matrix": {"PDF extraction": "Full"},
            "gaps_and_workarounds": [],
            "confidence_assessment": {"overall": "High"},
            "estimated_solution_value": "$5,000/month",
            "grounding_validation": {"verified_solution_count": 1},
        }

    async def proposal(**kwargs):
        return {
            "executive_summary": "Grounded proposal",
            "customer_requirements": ["PDF extraction"],
            "proposed_solution": "DocumentAI Pro",
            "implementation_roadmap": [],
            "total_implementation_timeline": "2-4 weeks",
            "pricing_proposal": {"base_product": "$5,000/month"},
            "support_service_levels": {},
            "success_metrics": [],
            "next_steps": [],
            "sections": [],
            "proposal_status": "approved",
            "grounding_validation": {"approved": True},
        }

    async def reviewer(**kwargs):
        return {
            "coverage_validation": [],
            "claim_verification": [],
            "unsupported_requirements": [],
            "missing_information": [],
            "risk_assessment": {},
            "readiness_assessment": {"ready_to_send": True},
            "recommended_next_steps": [],
            "follow_up_questions": [],
            "escalation_path": {},
        }

    monkeypatch.setattr(orchestrator, "run_research_agent", research)
    monkeypatch.setattr(orchestrator, "run_requirements_agent", requirements)
    monkeypatch.setattr(orchestrator, "run_qualification_agent", qualification)
    monkeypatch.setattr(orchestrator, "run_solution_agent", solution)
    monkeypatch.setattr(orchestrator, "run_proposal_agent", proposal)
    monkeypatch.setattr(orchestrator, "run_reviewer_agent", reviewer)

    result = await orchestrator.SalesOrchestrator().execute({
        "lead_id": "offline-orchestrator",
        "company_name": "Example",
        "inquiry_text": "Need PDF extraction",
        "conversation_history": [],
    })

    assert set(("research", "requirements", "qualification", "solution_matching", "proposal", "reviewer")).issubset(
        set(result["stages_completed"])
    )
    assert result["reviewer_result"]["readiness_assessment"]["ready_to_send"] is True
    assert not result["errors"]


def test_invalid_stage_output_is_recorded_as_schema_error():
    result = orchestrator._validate_stage_outputs({
        "requirements_result": {"functional_requirements": "not-a-list"},
        "errors": [],
    })

    assert result["errors"][0]["stage"] == "requirements"
    assert result["errors"][0]["error"] == "Stage output schema validation failed"


def test_reviewer_schema_accepts_documented_boolean_and_structured_values():
    reviewer = ReviewerOutput.model_validate({
        "coverage_validation": [{
            "requirement": "Extract PDF data",
            "addressed": "yes",
            "where": ["DocumentAI Pro", "Implementation roadmap"],
        }],
        "claim_verification": [{
            "claim": "DocumentAI Pro is catalog-backed",
            "verified": True,
            "source": ["products.json", "DocumentAI Pro"],
        }],
        "missing_information": [{
            "info": "Document retention period",
            "impact": "medium",
            "to_ask": ["What retention period is required?"],
        }],
        "risk_assessment": {
            "technical_risks": [{
                "risk": "Source PDFs may vary in quality",
                "mitigation": "Validate representative samples during discovery",
            }],
            "commercial_risks": [],
            "organizational_risks": [],
        },
        "readiness_assessment": {"ready_to_send": True, "reason": "Grounded proposal"},
        "escalation_path": {"approval_required": False, "approver": None},
    })

    assert reviewer.coverage_validation[0].addressed is True
    assert reviewer.claim_verification[0].verified is True
    assert reviewer.readiness_assessment.ready_to_send is True


def test_reviewer_partial_coverage_is_not_treated_as_fully_addressed():
    reviewer = ReviewerOutput.model_validate({
        "coverage_validation": [{
            "requirement": "Unknown volume",
            "addressed": "partial",
            "where": "Requires discovery",
        }],
    })

    assert reviewer.coverage_validation[0].addressed is False
