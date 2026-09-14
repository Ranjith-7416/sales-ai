from app.config import settings
from app.services import llm_service
import pytest


def test_gemini_requires_google_api_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", None)

    readiness = llm_service.provider_status()

    assert readiness["provider"] == "gemini"
    assert readiness["configured"] is False
    assert "GOOGLE_API_KEY" in readiness["message"]


def test_placeholder_google_api_key_is_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "YOUR_NEW_KEY")

    assert llm_service.provider_status()["configured"] is False


def test_gemini_is_initialized_through_google_sdk(monkeypatch):
    calls = []

    class FakeGemini:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr(settings, "LLM_MODEL_MAIN", "gemini-test-main")
    monkeypatch.setattr(settings, "LLM_MODEL_REASONING", "gemini-test-reasoning")
    monkeypatch.setattr(llm_service, "ChatGoogleGenerativeAI", FakeGemini)

    service = llm_service.LLMService()

    assert service.provider == "gemini"
    assert len(calls) == 2
    assert calls[0]["api_key"] == "test-key"
    assert calls[0]["model"] == "gemini-test-main"
    assert calls[0]["max_retries"] == 0
    assert calls[1]["model"] == "gemini-test-reasoning"


def test_openrouter_requires_its_own_key_and_model_configuration(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", None)
    monkeypatch.setattr(settings, "OPENROUTER_MODEL_MAIN", "openai/gpt-4o-mini")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL_REASONING", "openai/gpt-4o-mini")

    readiness = llm_service.provider_status()

    assert readiness["provider"] == "openrouter"
    assert readiness["configured"] is False
    assert "OPENROUTER_API_KEY" in readiness["message"]


def test_openrouter_is_initialized_through_openai_compatible_client(monkeypatch):
    calls = []

    class FakeOpenAICompatibleClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(settings, "LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL_MAIN", "openai/gpt-4o-mini")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL_REASONING", "anthropic/claude-3.5-haiku")
    monkeypatch.setattr(llm_service, "ChatOpenAI", FakeOpenAICompatibleClient)

    service = llm_service.LLMService()

    assert service.provider == "openrouter"
    assert service.main_model == "openai/gpt-4o-mini"
    assert service.reasoning_model == "anthropic/claude-3.5-haiku"
    assert len(calls) == 2
    assert calls[0]["api_key"] == "test-openrouter-key"
    assert calls[0]["base_url"] == llm_service.OPENROUTER_BASE_URL
    assert calls[0]["timeout"] == settings.LLM_TIMEOUT_SECONDS
    assert calls[0]["max_retries"] == 0
    assert calls[1]["model_name"] == "anthropic/claude-3.5-haiku"


def test_groq_requires_its_own_key_and_models(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", None)
    monkeypatch.setattr(settings, "GROQ_MODEL_MAIN", "llama-3.3-70b-versatile")
    monkeypatch.setattr(settings, "GROQ_MODEL_REASONING", "llama-3.3-70b-versatile")

    readiness = llm_service.provider_status()

    assert readiness["provider"] == "groq"
    assert readiness["configured"] is False
    assert "GROQ_API_KEY" in readiness["message"]


def test_groq_uses_openai_compatible_endpoint(monkeypatch):
    calls = []

    class FakeOpenAICompatibleClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-groq-key")
    monkeypatch.setattr(settings, "GROQ_MODEL_MAIN", "llama-3.3-70b-versatile")
    monkeypatch.setattr(settings, "GROQ_MODEL_REASONING", "llama-3.3-70b-versatile")
    monkeypatch.setattr(llm_service, "ChatOpenAI", FakeOpenAICompatibleClient)

    service = llm_service.LLMService()

    assert service.provider == "groq"
    assert service.main_model == "llama-3.3-70b-versatile"
    assert service.reasoning_model == "llama-3.3-70b-versatile"
    assert len(calls) == 2
    assert calls[0]["api_key"] == "test-groq-key"
    assert calls[0]["base_url"] == llm_service.GROQ_BASE_URL
    assert calls[0]["max_retries"] == 0
    assert calls[1]["model_name"] == "llama-3.3-70b-versatile"


@pytest.mark.asyncio
async def test_openrouter_quota_uses_configured_groq_fallback(monkeypatch):
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            calls.append(kwargs)

        def invoke(self, prompt):
            if self.kwargs["base_url"] == llm_service.OPENROUTER_BASE_URL:
                raise Exception("429 quota exceeded")
            return type("Response", (), {"content": "fallback response"})()

    monkeypatch.setattr(settings, "LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDERS", "groq")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL_MAIN", "openrouter/free")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL_REASONING", "openrouter/free")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-groq-key")
    monkeypatch.setattr(settings, "GROQ_MODEL_MAIN", "llama-3.3-70b-versatile")
    monkeypatch.setattr(settings, "GROQ_MODEL_REASONING", "llama-3.3-70b-versatile")
    monkeypatch.setattr(llm_service, "ChatOpenAI", FakeClient)

    service = llm_service.LLMService()

    assert await service.invoke("test prompt") == "fallback response"
    assert [call["base_url"] for call in calls] == [
        llm_service.OPENROUTER_BASE_URL,
        llm_service.OPENROUTER_BASE_URL,
        llm_service.GROQ_BASE_URL,
    ]
