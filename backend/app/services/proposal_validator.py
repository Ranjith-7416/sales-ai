"""Deterministic proposal grounding checks."""
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings

_STOP_WORDS = {
    "about", "after", "also", "based", "between", "customer", "from", "into",
    "that", "their", "this", "will", "with", "your", "have", "for", "and",
    "the", "are", "can", "not", "all", "our", "you", "they", "its",
}
_CLAIM_MARKERS = {
    "$", "%", "week", "month", "day", "year", "supports", "provides", "includes",
    "offers", "certified", "certification", "guarantee", "sla", "availability",
    "iso", "soc", "gdpr", "hipaa", "fedramp", "product", "service",
}


def _tokens(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9][a-z0-9.+%-]*", value.lower())
        if len(token) > 2 and token not in _STOP_WORDS
    }


def _knowledge_text() -> str:
    parts: List[str] = []
    for filename in ("products.json", "services.json"):
        path = Path(settings.KNOWLEDGE_BASE_PATH) / filename
        try:
            parts.append(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            continue
    return " ".join(parts)


def _catalog_field_text(field_names: set[str], solution: Dict[str, Any] | None) -> str:
    values: List[str] = []
    for filename in ("products.json", "services.json"):
        path = Path(settings.KNOWLEDGE_BASE_PATH) / filename
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            records = []
        for record in records:
            for key, value in record.items():
                if key in field_names:
                    values.extend(_flatten_claim_values(value))
    if solution:
        for key, value in solution.items():
            if key in field_names:
                values.extend(_flatten_claim_values(value))
    return " ".join(values).lower()


def _proposal_field_values(proposal: Dict[str, Any], field_name: str) -> List[str]:
    return _flatten_claim_values(proposal.get(field_name))


def _proposal_sentences(proposal: Dict[str, Any]) -> List[str]:
    values: List[str] = []
    for key in ("executive_summary", "proposed_solution", "total_implementation_timeline"):
        if isinstance(proposal.get(key), str):
            values.append(proposal[key])
    for key in ("customer_requirements", "success_metrics", "next_steps"):
        values.extend(item for item in proposal.get(key, []) if isinstance(item, str))
    for key in (
        "pricing_proposal",
        "support_service_levels",
        "certifications",
        "service_levels",
        "delivery_commitments",
    ):
        values.extend(_flatten_claim_values(proposal.get(key)))
    for item in proposal.get("implementation_roadmap", []) or []:
        if isinstance(item, dict):
            values.extend(str(value) for value in item.values() if isinstance(value, str))
    for item in proposal.get("sections", []) or []:
        if isinstance(item, dict) and isinstance(item.get("content"), str):
            values.append(item["content"])
    return [sentence.strip() for value in values for sentence in re.split(r"(?<=[.!?])\s+", value) if sentence.strip()]


def _flatten_claim_values(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for child in value.values() for item in _flatten_claim_values(child)]
    if isinstance(value, list):
        return [item for child in value for item in _flatten_claim_values(child)]
    return []


def _numeric_facts(value: str) -> set[str]:
    return {
        number.replace(",", "")
        for number in re.findall(r"(?<![\d.])\d+(?:,\d{3})*(?:\.\d+)?(?!\d)", value)
    }


def validate_proposal(
    proposal: Dict[str, Any],
    requirements: Dict[str, Any] | None = None,
    solution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate proposal sentences against catalog and customer evidence."""
    evidence = _knowledge_text()
    evidence += " " + json.dumps(requirements or {})
    evidence += " " + json.dumps(solution or {})
    evidence_tokens = _tokens(evidence)
    evidence_lower = evidence.lower()
    evidence_numbers = _numeric_facts(evidence)
    unsupported: List[str] = []

    structured_fields = {
        "pricing_proposal": {"pricing"},
        "support_service_levels": {"support_level", "support_tiers", "response_time_sla", "sla", "support_hours"},
        "certifications": {"certifications", "certifications_provided", "compliance_standards"},
        "total_implementation_timeline": {"implementation_timeline", "delivery_timeline", "duration"},
    }
    for proposal_field, evidence_fields in structured_fields.items():
        field_evidence = _catalog_field_text(evidence_fields, solution)
        for claim in _proposal_field_values(proposal, proposal_field):
            lowered_claim = claim.lower()
            if "[to be confirmed]" in lowered_claim or "to be determined" in lowered_claim or "tbd" in lowered_claim:
                continue
            if lowered_claim not in field_evidence:
                unsupported.append(claim)

    for sentence in _proposal_sentences(proposal):
        lowered = sentence.lower()
        sentence_tokens = _tokens(sentence)
        is_estimate = "[estimate]" in lowered or "to be determined" in lowered or "tbd" in lowered
        has_claim_marker = any(marker in lowered for marker in _CLAIM_MARKERS) or bool(re.search(r"\d", sentence))
        overlap = sentence_tokens & evidence_tokens
        numeric_literals = re.findall(r"\$?\d+(?:[,.]\d+)*(?:\.\d+)?%?", sentence)
        numeric_facts_grounded = all(
            literal.lower() in evidence_lower
            or literal.replace("$", "").replace(",", "").replace("%", "") in evidence_numbers
            for literal in numeric_literals
        )
        exact_evidence = lowered in evidence_lower
        if has_claim_marker and not is_estimate and not exact_evidence and (len(overlap) < 2 or not numeric_facts_grounded):
            unsupported.append(sentence)

    unsupported = list(dict.fromkeys(unsupported))

    return {
        "approved": not unsupported,
        "checked_sentence_count": len(_proposal_sentences(proposal)),
        "unsupported_sentences": unsupported,
        "status": "Approved" if not unsupported else "Blocked - manual verification required",
    }
