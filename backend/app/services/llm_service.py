"""LLM Service - abstraction layer for multiple LLM providers"""
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.callbacks import StreamingStdOutCallbackHandler
from app.config import settings
import logging
import time
import re

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class ProviderQuotaError(RuntimeError):
    """A provider quota exhaustion that must not be retried downstream."""


def _is_quota_exhaustion(error: Exception) -> bool:
    message = str(error).lower()
    return "429" in message and any(
        marker in message
        for marker in ("quota", "free_tier", "daily quota", "generate_content_free_tier")
    )


def _is_transient_provider_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in ("503", "502", "504", "temporarily unavailable", "connection reset")) or (
        "429" in message and ("rate limit" in message or "try again in" in message or "tokens per minute" in message) and not _is_quota_exhaustion(error)
    )


class MockLLMProvider:
    """Deterministic provider for unit tests that must not call an external API."""

    def __init__(self, responses: Optional[list[str]] = None):
        self.responses = list(responses or [])

    def invoke(self, prompt: str) -> str:
        if self.responses:
            return self.responses.pop(0)
        return "{}"

    def batch(self, prompts: list[str]) -> list[str]:
        return [self.invoke(prompt) for prompt in prompts]


def _is_configured(value: Optional[str]) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    return bool(normalized and not normalized.startswith(("your-", "your_", "<")) and normalized not in {"changeme", "replace-me"})


def _provider_models(provider: str) -> tuple[Optional[str], Optional[str]]:
    if provider == "openrouter":
        return settings.OPENROUTER_MODEL_MAIN, settings.OPENROUTER_MODEL_REASONING
    if provider == "groq":
        return settings.GROQ_MODEL_MAIN, settings.GROQ_MODEL_REASONING
    return settings.LLM_MODEL_MAIN, settings.LLM_MODEL_REASONING


def _provider_is_configured(provider: str) -> bool:
    keys = {
        "anthropic": settings.ANTHROPIC_API_KEY,
        "openai": settings.OPENAI_API_KEY,
        "google": settings.GOOGLE_API_KEY,
        "gemini": settings.GOOGLE_API_KEY,
        "openrouter": settings.OPENROUTER_API_KEY,
        "groq": settings.GROQ_API_KEY,
    }
    main_model, reasoning_model = _provider_models(provider)
    return _is_configured(keys.get(provider)) and _is_configured(main_model) and _is_configured(reasoning_model)


def provider_status() -> dict:
    provider = settings.LLM_PROVIDER.lower()
    keys = {"anthropic": settings.ANTHROPIC_API_KEY, "openai": settings.OPENAI_API_KEY, "google": settings.GOOGLE_API_KEY, "gemini": settings.GOOGLE_API_KEY, "openrouter": settings.OPENROUTER_API_KEY, "groq": settings.GROQ_API_KEY}
    model, reasoning_model = _provider_models(provider)
    key_configured = _is_configured(keys.get(provider))
    model_configured = _is_configured(model) and _is_configured(reasoning_model)
    configured = (key_configured and model_configured) if provider != "mock" else True
    key_name = "GOOGLE_API_KEY" if provider in {"google", "gemini"} else f"{provider.upper()}_API_KEY"
    if provider == "mock":
        message = "Mock provider enabled for tests"
    elif not key_configured:
        message = f"Set {key_name} in backend/.env, or in the project root .env when using Docker Compose"
    elif provider in {"openrouter", "groq"} and not model_configured:
        model_prefix = "OPENROUTER" if provider == "openrouter" else "GROQ"
        message = f"Set {model_prefix}_MODEL_MAIN and {model_prefix}_MODEL_REASONING in backend/.env, or in the project root .env when using Docker Compose"
    else:
        message = "Provider key configured"
    return {
        "provider": provider,
        "configured": configured,
        "model": model,
        "message": message,
    }


class LLMService:
    """Unified LLM interface supporting multiple providers"""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        status = provider_status()
        if self.provider == "mock":
            self.llm_main = MockLLMProvider()
            self.llm_reasoning = self.llm_main
            return
        if self.provider not in {"anthropic", "openai", "google", "gemini", "openrouter", "groq"}:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        if not status["configured"]:
            raise ValueError(status["message"])
        self.main_model = settings.OPENROUTER_MODEL_MAIN if self.provider == "openrouter" else settings.GROQ_MODEL_MAIN if self.provider == "groq" else settings.LLM_MODEL_MAIN
        self.reasoning_model = settings.OPENROUTER_MODEL_REASONING if self.provider == "openrouter" else settings.GROQ_MODEL_REASONING if self.provider == "groq" else settings.LLM_MODEL_REASONING
        self.temperature = settings.LLM_TEMPERATURE
        self.fallback_providers = [
            provider.strip().lower()
            for provider in settings.LLM_FALLBACK_PROVIDERS.split(",")
            if provider.strip().lower() and provider.strip().lower() != self.provider
        ]
        self._fallback_clients = {}
        
        self.llm_main = self._initialize_main_llm()
        self.llm_reasoning = self._initialize_reasoning_llm()
        self._groq_fallback_client = None

    @property
    def groq_fallback_llm(self):
        if self.provider == "groq" and self.main_model != "openai/gpt-oss-20b":
            if self._groq_fallback_client is None:
                self._groq_fallback_client = ChatOpenAI(
                    api_key=settings.GROQ_API_KEY,
                    model_name="openai/gpt-oss-20b",
                    temperature=self.temperature,
                    max_tokens=2048,
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                    max_retries=0,
                    base_url=GROQ_BASE_URL,
                )
            return self._groq_fallback_client
        return None


    def _initialize_main_llm(self):
        """Initialize main LLM based on provider"""
        if self.provider == "anthropic":
            return ChatAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                model_name=self.main_model,
                temperature=self.temperature,
                max_tokens=1024,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        elif self.provider == "openai":
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model_name=self.main_model,
                temperature=self.temperature,
                max_tokens=1024,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        elif self.provider in {"openrouter", "groq"}:
            return ChatOpenAI(
                api_key=settings.OPENROUTER_API_KEY if self.provider == "openrouter" else settings.GROQ_API_KEY,
                model_name=self.main_model,
                temperature=self.temperature,
                max_tokens=2048,
                timeout=settings.LLM_TIMEOUT_SECONDS,
                max_retries=0,
                base_url=OPENROUTER_BASE_URL if self.provider == "openrouter" else GROQ_BASE_URL,
            )
        elif self.provider in {"google", "gemini"}:
            return ChatGoogleGenerativeAI(
                api_key=settings.GOOGLE_API_KEY,
                model=self.main_model,
                temperature=self.temperature,
                max_retries=0,
                timeout=settings.LLM_TIMEOUT_SECONDS,
                max_output_tokens=1024,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _initialize_reasoning_llm(self):
        """Initialize reasoning LLM for complex analysis"""
        if self.provider == "anthropic":
            return ChatAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                model_name=self.reasoning_model,
                temperature=0.5,
                max_tokens=1024,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        elif self.provider == "openai":
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model_name=self.reasoning_model,
                temperature=0.5,
                max_tokens=1024,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        elif self.provider in {"openrouter", "groq"}:
            return ChatOpenAI(
                api_key=settings.OPENROUTER_API_KEY if self.provider == "openrouter" else settings.GROQ_API_KEY,
                model_name=self.reasoning_model,
                temperature=0.5,
                max_tokens=2048,
                timeout=settings.LLM_TIMEOUT_SECONDS,
                max_retries=0,
                base_url=OPENROUTER_BASE_URL if self.provider == "openrouter" else GROQ_BASE_URL,
            )
        elif self.provider in {"google", "gemini"}:
            return ChatGoogleGenerativeAI(
                api_key=settings.GOOGLE_API_KEY,
                model=self.reasoning_model,
                temperature=0.5,
                max_retries=0,
                timeout=settings.LLM_TIMEOUT_SECONDS,
                max_output_tokens=1024,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _fallback_llm(self, provider: str, use_reasoning: bool):
        """Lazily construct a configured fallback without changing the selected provider."""
        key = (provider, use_reasoning)
        if key in self._fallback_clients:
            return self._fallback_clients[key], _provider_models(provider)[1 if use_reasoning else 0]
        if provider not in {"anthropic", "openai", "google", "gemini", "openrouter", "groq"} or not _provider_is_configured(provider):
            return None, None

        original_provider, original_main, original_reasoning = self.provider, self.main_model, self.reasoning_model
        try:
            self.provider = provider
            self.main_model, self.reasoning_model = _provider_models(provider)
            client = self._initialize_reasoning_llm() if use_reasoning else self._initialize_main_llm()
            self._fallback_clients[key] = client
            return client, self.reasoning_model if use_reasoning else self.main_model
        finally:
            self.provider, self.main_model, self.reasoning_model = original_provider, original_main, original_reasoning

    def _invoke_with_protections(self, llm, prompt: str, provider: str, model: str) -> str:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = llm.invoke(prompt)
                return response.content
            except Exception as error:
                if _is_quota_exhaustion(error):
                    raise ProviderQuotaError(f"{provider} provider quota exhausted for model {model}") from error
                if attempt < max_attempts - 1 and _is_transient_provider_error(error):
                    wait_seconds = 2.0 * (attempt + 1)
                    match = re.search(r"try again in ([\d\.]+)s", str(error), re.IGNORECASE)
                    if match:
                        try:
                            wait_seconds = float(match.group(1)) + 0.5
                        except ValueError:
                            pass
                    logger.warning(
                        "Transient LLM provider error / rate-limit; waiting %.1fs before retry (attempt %d/%d)",
                        wait_seconds, attempt + 1, max_attempts
                    )
                    time.sleep(wait_seconds)
                    continue
                logger.error("LLM invocation failed: %s", error)
                raise
        raise RuntimeError("LLM invocation did not produce a response")

    async def invoke(self, prompt: str, use_reasoning: bool = False) -> str:
        """Invoke LLM with prompt"""
        llm = self.llm_reasoning if use_reasoning else self.llm_main
        model = self.reasoning_model if use_reasoning else self.main_model
        try:
            return self._invoke_with_protections(llm, prompt, self.provider, model)
        except Exception as primary_error:
            # If Groq primary hits rate limit or quota, seamlessly try the lighter 20b model
            if getattr(self, "groq_fallback_llm", None) is not None:
                try:
                    logger.info("Attempting secondary Groq model (openai/gpt-oss-20b)...")
                    return self._invoke_with_protections(self.groq_fallback_llm, prompt, "groq", "openai/gpt-oss-20b")
                except Exception as secondary_error:
                    logger.warning("Secondary Groq model call failed: %s", secondary_error)

            if isinstance(primary_error, ProviderQuotaError):
                for fallback_provider in self.fallback_providers:
                    fallback_llm, fallback_model = self._fallback_llm(fallback_provider, use_reasoning)
                    if not fallback_llm:
                        continue
                    try:
                        result = self._invoke_with_protections(fallback_llm, prompt, fallback_provider, fallback_model)
                        logger.warning("Primary provider quota exhausted; completed request with configured fallback provider")
                        return result
                    except ProviderQuotaError:
                        continue
            raise primary_error

    async def batch_invoke(self, prompts: list) -> list:
        """Batch invoke LLM"""
        try:
            responses = self.llm_main.batch(prompts)
            return [r.content for r in responses]
        except Exception as e:
            logger.error(f"LLM batch invocation failed: {str(e)}")
            raise

    def get_llm(self, reasoning: bool = False):
        """Get LLM instance"""
        return self.llm_reasoning if reasoning else self.llm_main


# Singleton instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
