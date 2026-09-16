"""Scoring Configuration API - Configurable Lead Scoring"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.config import settings
from app.services.cache_service import get_cache_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ScoringConfigSchema(BaseModel):
    qualified_threshold: float = Field(default=75.0, ge=0.0, le=100.0, description="Minimum score to be Qualified")
    needs_info_threshold: float = Field(default=50.0, ge=0.0, le=100.0, description="Minimum score for Needs More Information")
    fit_weight: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight of Fit score")
    readiness_weight: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight of Readiness score")
    opportunity_weight: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight of Opportunity score")
    risk_weight: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight of Risk score (inverted)")


@router.get("/scoring")
async def get_scoring_config():
    """Retrieve current lead qualification scoring criteria and weights (cached in Redis)"""
    cache = get_cache_service()
    cached = await cache.get(cache.cache_key_scoring())
    if cached:
        return cached

    config_data = {
        "qualified_threshold": settings.QUALIFIED_SCORE_THRESHOLD,
        "needs_info_threshold": settings.NEEDS_INFO_SCORE_THRESHOLD,
        "fit_weight": settings.FIT_SCORE_WEIGHT,
        "readiness_weight": settings.READINESS_SCORE_WEIGHT,
        "opportunity_weight": settings.OPPORTUNITY_SCORE_WEIGHT,
        "risk_weight": settings.RISK_SCORE_WEIGHT,
        "formula": "Score = (Fit * fit_weight) + (Readiness * readiness_weight) + (Opportunity * opportunity_weight) + ((100 - Risk) * risk_weight)",
    }
    await cache.set(cache.cache_key_scoring(), config_data, ttl=300)
    return config_data


@router.post("/scoring")
async def update_scoring_config(config: ScoringConfigSchema):
    """Update lead qualification scoring criteria and weights dynamically"""
    total_weights = round(config.fit_weight + config.readiness_weight + config.opportunity_weight + config.risk_weight, 2)
    if total_weights != 1.0:
        raise HTTPException(
            status_code=400,
            detail=f"Sum of weights must equal 1.0 (current sum: {total_weights})"
        )

    if config.needs_info_threshold > config.qualified_threshold:
        raise HTTPException(
            status_code=400,
            detail="needs_info_threshold cannot be higher than qualified_threshold"
        )

    settings.QUALIFIED_SCORE_THRESHOLD = config.qualified_threshold
    settings.NEEDS_INFO_SCORE_THRESHOLD = config.needs_info_threshold
    settings.FIT_SCORE_WEIGHT = config.fit_weight
    settings.READINESS_SCORE_WEIGHT = config.readiness_weight
    settings.OPPORTUNITY_SCORE_WEIGHT = config.opportunity_weight
    settings.RISK_SCORE_WEIGHT = config.risk_weight

    logger.info("Scoring configuration updated: fit=%.2f, ready=%.2f, opp=%.2f, risk=%.2f",
                config.fit_weight, config.readiness_weight, config.opportunity_weight, config.risk_weight)

    cache = get_cache_service()
    await cache.delete(cache.cache_key_scoring())

    return {
        "message": "Scoring configuration updated successfully",
        "qualified_threshold": settings.QUALIFIED_SCORE_THRESHOLD,
        "needs_info_threshold": settings.NEEDS_INFO_SCORE_THRESHOLD,
        "fit_weight": settings.FIT_SCORE_WEIGHT,
        "readiness_weight": settings.READINESS_SCORE_WEIGHT,
        "opportunity_weight": settings.OPPORTUNITY_SCORE_WEIGHT,
        "risk_weight": settings.RISK_SCORE_WEIGHT,
        "config": {
            "qualified_threshold": settings.QUALIFIED_SCORE_THRESHOLD,
            "needs_info_threshold": settings.NEEDS_INFO_SCORE_THRESHOLD,
            "fit_weight": settings.FIT_SCORE_WEIGHT,
            "readiness_weight": settings.READINESS_SCORE_WEIGHT,
            "opportunity_weight": settings.OPPORTUNITY_SCORE_WEIGHT,
            "risk_weight": settings.RISK_SCORE_WEIGHT,
        }
    }


from fastapi.responses import JSONResponse
import smtplib


class SmtpConfigSchema(BaseModel):
    email_provider: Optional[str] = Field(default="smtp", description="Active email provider (smtp)")
    smtp_host: Optional[str] = Field(default="smtp.gmail.com", description="SMTP hostname")
    smtp_port: Optional[int] = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP sender username or Gmail address")
    smtp_username: Optional[str] = Field(default=None, description="Alias for smtp_user")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password or 16-character Gmail App Password")
    smtp_from_email: Optional[str] = Field(default=None, description="Sender from header email")
    smtp_use_tls: Optional[bool] = Field(default=True, description="Enable STARTTLS encryption")


@router.get("/smtp")
async def get_smtp_config():
    """Retrieve current email delivery configuration status (with credentials masked)."""
    is_configured = settings.is_smtp_configured()
    active_provider = "smtp" if is_configured else "unconfigured"
    provider_display = f"Gmail SMTP ({settings.SMTP_HOST}:{settings.SMTP_PORT})" if is_configured else None

    return {
        "configured": is_configured,
        "active_provider": active_provider,
        "provider_display": provider_display,
        "email_provider": settings.EMAIL_PROVIDER,
        "smtp_host": settings.SMTP_HOST or "smtp.gmail.com",
        "smtp_port": settings.SMTP_PORT,
        "smtp_user": settings.SMTP_USER if (settings.SMTP_USER and not settings.is_placeholder(settings.SMTP_USER)) else "",
        "smtp_from_email": settings.SMTP_FROM_EMAIL or settings.SMTP_USER or "",
        "smtp_use_tls": settings.SMTP_USE_TLS,
        "has_password": bool(settings.SMTP_PASSWORD and not settings.is_placeholder(settings.SMTP_PASSWORD)),
        "is_render": bool(settings.RENDER),
    }


@router.post("/smtp")
async def update_smtp_config(config: SmtpConfigSchema):
    """Update Gmail SMTP delivery settings dynamically for live client email delivery."""
    settings.EMAIL_PROVIDER = "smtp"
    if config.smtp_host and config.smtp_host.strip():
        settings.SMTP_HOST = config.smtp_host.strip()
    if config.smtp_port is not None:
        settings.SMTP_PORT = config.smtp_port

    username = config.smtp_username or config.smtp_user
    if username and username.strip():
        settings.SMTP_USER = username.strip()
    if config.smtp_password and config.smtp_password.strip():
        settings.SMTP_PASSWORD = config.smtp_password.strip()
    if config.smtp_from_email and config.smtp_from_email.strip():
        settings.SMTP_FROM_EMAIL = config.smtp_from_email.strip()
    elif settings.SMTP_USER and "@" in settings.SMTP_USER:
        settings.SMTP_FROM_EMAIL = settings.SMTP_USER.strip()
    if config.smtp_use_tls is not None:
        settings.SMTP_USE_TLS = config.smtp_use_tls

    is_configured = settings.is_smtp_configured()
    active_provider = "smtp" if is_configured else "unconfigured"
    provider_display = f"Gmail SMTP ({settings.SMTP_HOST}:{settings.SMTP_PORT})" if is_configured else None

    logger.info("Gmail SMTP configuration updated dynamically: configured=%s, provider=%s", is_configured, active_provider)
    return {
        "message": "Gmail SMTP configuration updated successfully",
        "configured": is_configured,
        "active_provider": active_provider,
        "provider_display": provider_display,
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_user": settings.SMTP_USER or "",
        "smtp_from_email": settings.SMTP_FROM_EMAIL or settings.SMTP_USER or "",
        "has_password": bool(settings.SMTP_PASSWORD and not settings.is_placeholder(settings.SMTP_PASSWORD)),
    }


@router.post("/smtp/test")
async def test_smtp_connection():
    """Verify live Gmail SMTP connection, STARTTLS, and authentication without sending an email."""
    if not settings.is_smtp_configured():
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Gmail SMTP is not configured. Please provide your Gmail address and 16-character App Password.",
            },
        )
    try:
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=8)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=8)
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.quit()
        return {
            "success": True,
            "message": f"Successfully connected and authenticated to Gmail SMTP ({settings.SMTP_HOST}:{settings.SMTP_PORT}) as {settings.SMTP_USER}!",
        }
    except smtplib.SMTPAuthenticationError:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Gmail SMTP authentication failed. Please verify your Gmail address and 16-character Google App Password (2-Step Verification must be turned ON in Google Account settings).",
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"SMTP connection failed: {str(e)}",
            },
        )


