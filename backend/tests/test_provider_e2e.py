import os

import pytest

from app.services.llm_service import provider_status


@pytest.mark.asyncio
async def test_provider_backed_pipeline_end_to_end():
    """Run the complete agent graph against the configured real LLM provider."""
    if os.getenv("RUN_LLM_E2E") != "1":
        pytest.skip("Set RUN_LLM_E2E=1 to run the provider-backed integration test")

    readiness = provider_status()
    assert readiness["configured"], readiness["message"]

    from app.agents.orchestrator import get_orchestrator

    result = await get_orchestrator().execute({
        "lead_id": "integration-test",
        "company_name": "MediTech Solutions",
        "industry": "Healthcare",
        "company_size": "500-1000 employees",
        "budget": "$200K",
        "timeline": "3 months",
        "additional_context": "Decision-maker confirmed approval. Success criteria and integrations are documented.",
        "inquiry_text": "We need an AI-powered document processing solution capable of extracting information from approximately 10,000 PDF documents per month.",
        "conversation_history": [],
    })

    assert not result.get("errors"), result.get("errors")
    assert set(("research", "requirements", "qualification", "solution_matching", "proposal", "reviewer")).issubset(
        set(result.get("stages_completed", []))
    )
    assert result["research_result"].get("company_name")
    assert result["requirements_result"].get("functional_requirements")
    assert result["qualification_result"].get("composite_score") is not None
    assert result["solution_matching_result"].get("grounding_validation", {}).get("verified_solution_count", 0) > 0
    assert result["proposal_result"].get("proposal_status") == "approved"
    assert result["proposal_result"].get("grounding_validation", {}).get("approved") is True
    assert result["reviewer_result"].get("readiness_assessment")


def test_mock_provider_is_available_without_network_access():
    from app.services.llm_service import MockLLMProvider

    provider = MockLLMProvider(["mock response"])
    assert provider.invoke("test") == "mock response"
