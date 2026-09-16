from app.config import settings


def normalize_lead_status(status: str | None, score: float | int | None, missing_information: list[str] | None = None) -> str:
    """Normalize status deterministically so score thresholds and missing info always dictate final status.
    
    The LLM string is never allowed to override thresholds.
    """
    missing = [m for m in (missing_information or []) if m and str(m).strip()]
    score_value = float(score) if score is not None else 0.0

    if missing:
        return "Needs More Information"
    if score_value >= settings.QUALIFIED_SCORE_THRESHOLD:
        return "Qualified"
    if score_value < settings.NEEDS_INFO_SCORE_THRESHOLD:
        return "Low Priority"
    return "Needs More Information"

