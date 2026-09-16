from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import json
import os
from pathlib import Path


BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def _parse_cors_origins(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return [origin.strip() for origin in value.split(",") if origin.strip()]


def _resolve_knowledge_base_path(raw_path: str) -> str:
    path = Path(raw_path)
    if path.is_absolute() and path.exists():
        return str(path)
    if path.exists():
        return str(path.resolve())
    backend_kb = Path(__file__).resolve().parents[1] / raw_path
    if backend_kb.exists():
        return str(backend_kb.resolve())
    return str(path)


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Sales AI Pipeline"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://salesai:salesai_password@localhost:5432/salesai_db"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_TIMEOUT_SECONDS: float = float(os.getenv("REDIS_TIMEOUT_SECONDS", "5"))

    # API protection and operational limits
    API_AUTH_TOKEN: Optional[str] = os.getenv("API_AUTH_TOKEN")
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    RATE_LIMIT_LEAD_REQUESTS: int = int(os.getenv("RATE_LIMIT_LEAD_REQUESTS", "10"))
    RATE_LIMIT_PROPOSAL_REQUESTS: int = int(os.getenv("RATE_LIMIT_PROPOSAL_REQUESTS", "30"))
    RATE_LIMIT_KB_UPLOADS: int = int(os.getenv("RATE_LIMIT_KB_UPLOADS", "10"))
    WEB_SEARCH_TIMEOUT_SECONDS: float = float(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "15"))
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
    DATABASE_CONNECT_TIMEOUT_SECONDS: int = int(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "10"))
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "1800"))

    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # gemini, groq, openrouter, anthropic, openai, google
    LLM_FALLBACK_PROVIDERS: str = os.getenv("LLM_FALLBACK_PROVIDERS", "groq")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

    # Models
    LLM_MODEL_MAIN: str = os.getenv("LLM_MODEL_MAIN", "gemini-1.5-flash")
    LLM_MODEL_REASONING: str = os.getenv("LLM_MODEL_REASONING", "gemini-1.5-flash")
    OPENROUTER_MODEL_MAIN: Optional[str] = os.getenv("OPENROUTER_MODEL_MAIN")
    OPENROUTER_MODEL_REASONING: Optional[str] = os.getenv("OPENROUTER_MODEL_REASONING")
    GROQ_MODEL_MAIN: Optional[str] = os.getenv("GROQ_MODEL_MAIN", "openai/gpt-oss-120b")
    GROQ_MODEL_REASONING: Optional[str] = os.getenv("GROQ_MODEL_REASONING", "openai/gpt-oss-120b")
    LLM_TEMPERATURE: float = 0.7

    # Qualification scoring
    QUALIFIED_SCORE_THRESHOLD: float = float(os.getenv("QUALIFIED_SCORE_THRESHOLD", "75"))
    NEEDS_INFO_SCORE_THRESHOLD: float = float(os.getenv("NEEDS_INFO_SCORE_THRESHOLD", "50"))
    FIT_SCORE_WEIGHT: float = float(os.getenv("FIT_SCORE_WEIGHT", "0.25"))
    READINESS_SCORE_WEIGHT: float = float(os.getenv("READINESS_SCORE_WEIGHT", "0.25"))
    OPPORTUNITY_SCORE_WEIGHT: float = float(os.getenv("OPPORTUNITY_SCORE_WEIGHT", "0.30"))
    RISK_SCORE_WEIGHT: float = float(os.getenv("RISK_SCORE_WEIGHT", "0.20"))

    # Web Search
    BRAVE_SEARCH_API_KEY: Optional[str] = os.getenv("BRAVE_SEARCH_API_KEY") or os.getenv("BRAVE_API_KEY")
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY")

    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = _resolve_knowledge_base_path(os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base"))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Cors
    CORS_ORIGINS: list = _parse_cors_origins(os.getenv(
        "CORS_ORIGINS",
        '["http://localhost:3000", "http://localhost:5173"]',
    ))

    # JWT & Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@salesai.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "salesai123")
    ADMIN_NAME: str = os.getenv("ADMIN_NAME", "Sales AI Director")
    ADMIN_ROLE: str = os.getenv("ADMIN_ROLE", "admin")

    # SMTP Email Delivery Configuration
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "sales@salesai-platform.com")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # Production Deployment & URL Resolution
    RENDER_EXTERNAL_URL: Optional[str] = os.getenv("RENDER_EXTERNAL_URL")
    RENDER: bool = bool(os.getenv("RENDER"))
    BACKEND_URL: Optional[str] = os.getenv("BACKEND_URL")

    # Frontend URL (Vercel production URL or localhost)
    FRONTEND_URL: str = os.getenv(
        "FRONTEND_URL",
        "https://sales-ai-ranjith-7416s-projects.vercel.app"
        if os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") or os.getenv("RENDER_EXTERNAL_URL")
        else "http://localhost:3000"
    )

    def is_production(self) -> bool:
        return (
            self.ENVIRONMENT.lower() == "production"
            or bool(self.RENDER_EXTERNAL_URL)
            or bool(os.getenv("RENDER"))
        )

    def get_backend_url(self, request: Optional[object] = None) -> str:
        """Resolve authoritative backend URL without silent localhost fallbacks in production."""
        # 1. Header inspection when request context is available
        if request and hasattr(request, "headers"):
            headers = getattr(request, "headers", {})
            forwarded_proto = headers.get("x-forwarded-proto", "https")
            forwarded_host = headers.get("x-forwarded-host") or headers.get("host")
            if forwarded_host:
                host_lower = forwarded_host.lower()
                if "localhost" not in host_lower and "127.0.0.1" not in host_lower:
                    return f"{forwarded_proto}://{forwarded_host}".rstrip("/")
                elif "localhost" in host_lower or "127.0.0.1" in host_lower:
                    return f"http://{forwarded_host}".rstrip("/")

        # 2. Render injected external URL
        if self.RENDER_EXTERNAL_URL and self.RENDER_EXTERNAL_URL.strip():
            return self.RENDER_EXTERNAL_URL.strip().rstrip("/")

        # 3. Explicit configured BACKEND_URL
        if self.BACKEND_URL and self.BACKEND_URL.strip():
            return self.BACKEND_URL.strip().rstrip("/")

        # 4. Production environment check
        if self.is_production():
            return "https://sales-ai-etew.onrender.com"

        # 5. Localhost development fallback
        return f"http://localhost:{self.PORT or 8001}"

    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_ENV_FILE), ".env"),
        case_sensitive=True,
    )


settings = Settings()



def validate_production_settings() -> None:
    if settings.ENVIRONMENT.lower() != "production":
        return

    missing = []
    if not settings.DATABASE_URL or "user:password" in settings.DATABASE_URL:
        missing.append("DATABASE_URL")
    if not settings.SECRET_KEY or settings.SECRET_KEY.startswith("your-"):
        missing.append("SECRET_KEY")
    if not settings.API_AUTH_TOKEN:
        missing.append("API_AUTH_TOKEN")
    if not settings.CORS_ORIGINS or any("localhost" in origin for origin in settings.CORS_ORIGINS):
        missing.append("CORS_ORIGINS")
    if missing:
        raise RuntimeError("Production configuration is incomplete: " + ", ".join(missing))
