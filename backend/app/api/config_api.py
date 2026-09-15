"""Scoring Configuration API - Configurable Lead Scoring"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.config import settings
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
    """Retrieve current lead qualification scoring criteria and weights"""
    return {
        "qualified_threshold": settings.QUALIFIED_SCORE_THRESHOLD,
        "needs_info_threshold": settings.NEEDS_INFO_SCORE_THRESHOLD,
        "fit_weight": settings.FIT_SCORE_WEIGHT,
        "readiness_weight": settings.READINESS_SCORE_WEIGHT,
        "opportunity_weight": settings.OPPORTUNITY_SCORE_WEIGHT,
        "risk_weight": settings.RISK_SCORE_WEIGHT,
        "formula": "Score = (Fit * fit_weight) + (Readiness * readiness_weight) + (Opportunity * opportunity_weight) + ((100 - Risk) * risk_weight)",
    }


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
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP hostname")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: str = Field(..., description="SMTP sender username or Gmail address")
    smtp_password: str = Field(..., description="SMTP password or 16-character Gmail App Password")
    smtp_from_email: Optional[str] = Field(default=None, description="Sender from header email")
    smtp_use_tls: bool = Field(default=True, description="Enable STARTTLS encryption")


@router.get("/smtp")
async def get_smtp_config():
    """Retrieve current SMTP configuration status (with credentials masked)"""
    is_configured = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)
    return {
        "configured": is_configured,
        "smtp_host": settings.SMTP_HOST or "smtp.gmail.com",
        "smtp_port": settings.SMTP_PORT,
        "smtp_user": settings.SMTP_USER or "",
        "smtp_from_email": settings.SMTP_FROM_EMAIL or "sales@salesai-platform.com",
        "smtp_use_tls": settings.SMTP_USE_TLS,
        "has_password": bool(settings.SMTP_PASSWORD),
        "note": "Configure a 16-character Gmail App Password for instant inbox delivery.",
    }


@router.post("/smtp")
async def update_smtp_config(config: SmtpConfigSchema):
    """Update SMTP settings dynamically for live client email delivery"""
    settings.SMTP_HOST = config.smtp_host.strip()
    settings.SMTP_PORT = config.smtp_port
    settings.SMTP_USER = config.smtp_user.strip()
    settings.SMTP_PASSWORD = config.smtp_password.strip()
    if config.smtp_from_email and config.smtp_from_email.strip():
        settings.SMTP_FROM_EMAIL = config.smtp_from_email.strip()
    else:
        settings.SMTP_FROM_EMAIL = config.smtp_user.strip()
    settings.SMTP_USE_TLS = config.smtp_use_tls

    logger.info("SMTP configuration updated dynamically for user: %s", settings.SMTP_USER)
    return {
        "message": "SMTP configuration updated successfully",
        "configured": True,
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_user": settings.SMTP_USER,
        "smtp_from_email": settings.SMTP_FROM_EMAIL,
    }

