import pytest

from app.agents import orchestrator
from app.services.llm_service import ProviderQuotaError, _is_quota_exhaustion


def test_daily_quota_error_is_classified_without_exposing_credentials():
    error = Exception("429 quota exceeded for generate_content_free_tier_requests")

    assert _is_quota_exhaustion(error) is True


def test_non_quota_rate_limit_is_not_classified_as_daily_exhaustion():
    error = Exception("429 temporary rate limit")

    assert _is_quota_exhaustion(error) is False


@pytest.mark.asyncio
async def test_quota_failure_stops_dependent_nodes(monkeypatch):
    orchestrator._record_agent_execution = lambda *args, **kwargs: None

    async def fail_research(**kwargs):
        raise ProviderQuotaError("gemini provider quota exhausted")

    async def unexpected_requirements(**kwargs):
        raise AssertionError("requirements must not run after quota exhaustion")

    monkeypatch.setattr(orchestrator, "run_research_agent", fail_research)
    monkeypatch.setattr(orchestrator, "run_requirements_agent", unexpected_requirements)
    pipeline = orchestrator.SalesOrchestrator()
    state = {
        "lead_id": "quota-test",
        "company_name": "Example",
        "inquiry_text": "Need document processing",
        "stages_completed": [],
        "errors": [],
    }

    await pipeline._node_research(state)
    await pipeline._node_requirements(state)

    assert state["pipeline_status"] == "failed"
    assert state["errors"] == [{
        "stage": "research",
        "error": "gemini provider quota exhausted",
        "error_type": "provider_quota",
    }]