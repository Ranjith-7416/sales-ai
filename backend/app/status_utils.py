from app.config import settings


def normalize_lead_status(status: str | None, score: float | int | None, missing_information: list[str] | None = None) -> str:
    """Normalize AI-derived status so incomplete leads are never misclassified as qualified."""
    missing = missing_information or []
    score_value = float(score) if score is not None else 0.0
    normalized_status = (status or "").strip()

    if missing:
        return "Needs More Information"
    if score_value >= settings.QUALIFIED_SCORE_THRESHOLD:
        return "Qualified"
    if normalized_status == "Low Priority" or score_value < settings.NEEDS_INFO_SCORE_THRESHOLD:
        return "Low Priority"
    if normalized_status in {"Qualified", "Needs More Information", "Low Priority"}:
        return normalized_status
    return "Needs More Information"
