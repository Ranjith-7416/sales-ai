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


class SmtpConfigSchema(BaseModel):
    smtp_host: Optional[str] = Field(default="smtp.gmail.com", description="SMTP hostname")
    smtp_port: Optional[int] = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP sender username or Gmail address")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password or 16-character Gmail App Password")
    smtp_from_email: Optional[str] = Field(default=None, description="Sender from header email")
    smtp_use_tls: Optional[bool] = Field(default=True, description="Enable STARTTLS encryption")
    resend_api_key: Optional[str] = Field(default=None, description="Resend HTTP API key (port 443)")
    brevo_api_key: Optional[str] = Field(default=None, description="Brevo HTTP API key (port 443)")
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid HTTP API key (port 443)")


@router.get("/smtp")
async def get_smtp_config():
    """Retrieve current email delivery configuration status (with credentials masked)"""
    has_smtp = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)
    has_resend = bool(settings.RESEND_API_KEY)
    has_brevo = bool(settings.BREVO_API_KEY)
    has_sendgrid = bool(settings.SENDGRID_API_KEY)
    is_configured = has_smtp or has_resend or has_brevo or has_sendgrid

    active_provider = "unconfigured"
    if has_resend:
        active_provider = "resend_api"
    elif has_brevo:
        active_provider = "brevo_api"
    elif has_sendgrid:
        active_provider = "sendgrid_api"
    elif has_smtp:
        active_provider = "smtp"

    return {
        "configured": is_configured,
        "active_provider": active_provider,
        "has_http_api": bool(has_resend or has_brevo or has_sendgrid),
        "smtp_host": settings.SMTP_HOST or "smtp.gmail.com",
        "smtp_port": settings.SMTP_PORT,
        "smtp_user": settings.SMTP_USER or "",
        "smtp_from_email": settings.SMTP_FROM_EMAIL or "sales@salesai-platform.com",
        "smtp_use_tls": settings.SMTP_USE_TLS,
        "has_password": bool(settings.SMTP_PASSWORD),
        "has_resend_api_key": has_resend,
        "has_brevo_api_key": has_brevo,
        "has_sendgrid_api_key": has_sendgrid,
        "is_render": bool(settings.RENDER),
        "render_free_smtp_blocked": bool(settings.RENDER and not (has_resend or has_brevo or has_sendgrid)),
        "note": "Render Free Tier blocks outbound ports 25, 465, and 587. For Render, use an HTTP Email API (Resend / Brevo) over HTTPS port 443.",
    }


@router.post("/smtp")
async def update_smtp_config(config: SmtpConfigSchema):
    """Update email delivery settings dynamically for live client email delivery"""
    if config.resend_api_key and config.resend_api_key.strip():
        settings.RESEND_API_KEY = config.resend_api_key.strip()
    if config.brevo_api_key and config.brevo_api_key.strip():
        settings.BREVO_API_KEY = config.brevo_api_key.strip()
    if config.sendgrid_api_key and config.sendgrid_api_key.strip():
        settings.SENDGRID_API_KEY = config.sendgrid_api_key.strip()

    if config.smtp_host:
        settings.SMTP_HOST = config.smtp_host.strip()
    if config.smtp_port is not None:
        settings.SMTP_PORT = config.smtp_port
    if config.smtp_user:
        settings.SMTP_USER = config.smtp_user.strip()
    if config.smtp_password:
        settings.SMTP_PASSWORD = config.smtp_password.strip()
    if config.smtp_from_email and config.smtp_from_email.strip():
        settings.SMTP_FROM_EMAIL = config.smtp_from_email.strip()
    elif config.smtp_user and "@" in config.smtp_user:
        settings.SMTP_FROM_EMAIL = config.smtp_user.strip()
    if config.smtp_use_tls is not None:
        settings.SMTP_USE_TLS = config.smtp_use_tls

    active_provider = (
        "resend_api" if settings.RESEND_API_KEY
        else "brevo_api" if settings.BREVO_API_KEY
        else "sendgrid_api" if settings.SENDGRID_API_KEY
        else "smtp" if (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)
        else "unconfigured"
    )

    logger.info("Email delivery configuration updated dynamically: provider=%s", active_provider)
    return {
        "message": "Email delivery configuration updated successfully",
        "configured": True,
        "active_provider": active_provider,
        "has_http_api": bool(settings.RESEND_API_KEY or settings.BREVO_API_KEY or settings.SENDGRID_API_KEY),
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_user": settings.SMTP_USER,
        "smtp_from_email": settings.SMTP_FROM_EMAIL,
    }

