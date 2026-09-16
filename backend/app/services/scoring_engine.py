"""Authoritative Deterministic Lead Scoring and Qualification Engine.

Guarantees 100% deterministic, explainable, and consistent qualification results.
The LLM extracts structured facts and semantic evidence; this engine computes
all numeric metrics and final qualification statuses.
"""
from typing import Dict, Any, Optional, List, Tuple
import re
import logging
from app.config import settings

logger = logging.getLogger(__name__)

QUALIFICATION_VERSION = "2.0.0"
SCORING_CONFIG_VERSION = "1.0.0"

SPAM_TERMS = ('homework', 'school', 'essay', 'crypto', 'bitcoin', 'shoes', 'weather', 'game', 'gaming', 'personal use', 'recipe')
FREE_TERMS = ('free only', 'no budget', 'zero budget', 'cant pay', 'cannot pay', 'have no money', 'student', '$0')


def _extract_number(text: Optional[str]) -> Optional[float]:
    """Extract first numeric quantity from string."""
    if not text:
        return None
    match = re.search(r"(\d+[\d,]*)", str(text))
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def calculate_fit_score(
    requirements_result: Optional[Dict[str, Any]] = None,
    solution_result: Optional[Dict[str, Any]] = None,
    inquiry_text: str = "",
) -> Tuple[float, str]:
    """
    Calculate deterministic Fit Score (0 to 100).
    Measures how well customer requirements match catalog solutions.
    """
    base_score = 50.0
    evidence_parts = []

    text_lower = (inquiry_text or "").lower()

    # 0. Out of scope / spam / personal / homework check
    if any(t in text_lower for t in SPAM_TERMS) or any(t in text_lower for t in FREE_TERMS):
        return 15.0, "Inquiry is personal, consumer, academic, or outside core enterprise B2B software capabilities."

    # 1. Product capability match keywords
    has_doc_ai = any(kw in text_lower for kw in ["pdf", "document", "extract", "ocr", "invoice", "form"])
    has_chat = any(kw in text_lower for kw in ["chat", "support", "ticket", "virtual agent", "conversational"])
    has_compliance = any(kw in text_lower for kw in ["compliance", "hipaa", "soc2", "pii", "audit", "security", "gdpr"])

    # 2. Check Solution Agent coverage matrix
    coverage_matrix = {}
    if solution_result and isinstance(solution_result, dict):
        coverage_matrix = solution_result.get("requirement_coverage_matrix", {})
        confidence = (solution_result.get("confidence_assessment", {}) or {}).get("overall", "")
        verified_count = (solution_result.get("grounding_validation", {}) or {}).get("verified_solution_count", 0)
    else:
        confidence = ""
        verified_count = 0

    if coverage_matrix:
        full_matches = sum(1 for v in coverage_matrix.values() if str(v).lower() == "full")
        total_reqs = len(coverage_matrix)
        if total_reqs > 0:
            ratio = full_matches / total_reqs
            base_score = 70.0 + (ratio * 25.0)
            evidence_parts.append(f"Solution covers {full_matches}/{total_reqs} requirements ({round(ratio*100)}% coverage)")
    elif has_doc_ai or has_chat or has_compliance:
        base_score = 85.0
        matches = []
        if has_doc_ai: matches.append("Document AI & OCR extraction")
        if has_chat: matches.append("Customer Support AI")
        if has_compliance: matches.append("Compliance Shield")
        evidence_parts.append(f"Inquiry matches core product capabilities: {', '.join(matches)}")
    else:
        base_score = 40.0
        evidence_parts.append("Inquiry has partial or general automation capability match")

    # Grounded solution validation bonus
    if verified_count > 0:
        base_score = min(100.0, base_score + 5.0)

    fit_score = round(max(0.0, min(100.0, base_score)), 2)
    evidence = "; ".join(evidence_parts) if evidence_parts else "Product capability evaluation completed."
    return fit_score, evidence


def calculate_readiness_score(
    budget: Optional[str] = None,
    timeline: Optional[str] = None,
    additional_context: Optional[str] = None,
    missing_information: Optional[List[str]] = None,
) -> Tuple[float, str]:
    """
    Calculate deterministic Readiness Score (0 to 100).
    Measures budget availability, timeline urgency, and decision-maker involvement.
    """
    score = 20.0
    evidence_parts = []

    budget_clean = (budget or "").strip().lower()
    timeline_clean = (timeline or "").strip().lower()
    context_clean = (additional_context or "").strip().lower()

    # 0. Check for zero / free budget
    if any(f in budget_clean for f in FREE_TERMS) or budget_clean in ("$0", "0", "zero", "free") or any(f in context_clean for f in FREE_TERMS):
        return 10.0, "Sub-commercial intent with zero enterprise procurement budget"

    # 1. Budget evaluation (up to 40 pts)
    if budget_clean and budget_clean not in ("unspecified", "tbd", "to be confirmed", "none", "unknown", ""):
        num = _extract_number(budget_clean)
        if num and num >= 10000:
            score += 40.0
            evidence_parts.append(f"Confirmed enterprise budget ({budget.strip()})")
        elif num and num >= 2000:
            score += 30.0
            evidence_parts.append(f"Commercial budget specified ({budget.strip()})")
        elif num and num > 0:
            score += 25.0
            evidence_parts.append(f"Budget specified ({budget.strip()})")
        else:
            score += 5.0
            evidence_parts.append(f"Budget specified ({budget.strip()})")
    else:
        evidence_parts.append("Budget not yet confirmed")

    # 2. Timeline evaluation (up to 30 pts)
    if timeline_clean and timeline_clean not in ("unspecified", "tbd", "to be confirmed", "none", "unknown", ""):
        if any(w in timeline_clean for w in ["immediate", "asap", "1 month", "2 month", "1-2", "2-4 week", "weeks"]):
            score += 30.0
            evidence_parts.append(f"Urgent deployment timeline ({timeline.strip()})")
        elif any(w in timeline_clean for w in ["3 month", "quarter", "1-3 month", "q1", "q2", "q3", "q4"]):
            score += 20.0
            evidence_parts.append(f"Target timeline established ({timeline.strip()})")
        else:
            score += 15.0
            evidence_parts.append(f"Timeline provided ({timeline.strip()})")
    else:
        evidence_parts.append("Timeline not yet scheduled")

    # 3. Decision maker / executive authority (up to 10 pts)
    if any(title in context_clean for title in ["cio", "cto", "vp", "director", "head of", "c-level", "chief", "executive"]):
        score += 10.0
        evidence_parts.append("Executive decision-maker involvement confirmed")

    readiness_score = round(max(0.0, min(100.0, score)), 2)
    evidence = "; ".join(evidence_parts)
    return readiness_score, evidence


def calculate_opportunity_score(
    company_size: Optional[str] = None,
    industry: Optional[str] = None,
    inquiry_text: str = "",
    additional_context: Optional[str] = None,
) -> Tuple[float, str]:
    """
    Calculate deterministic Opportunity Score (0 to 100).
    Measures deal size potential, volume, and company scale.
    """
    score = 30.0
    evidence_parts = []

    combined_text = f"{inquiry_text} {additional_context or ''}".lower()
    size_clean = (company_size or "").strip().lower()
    industry_clean = (industry or "").strip().lower()

    # 0. Check spam / non-commercial
    if any(t in combined_text for t in SPAM_TERMS) or any(t in combined_text for t in FREE_TERMS):
        return 10.0, "Non-commercial individual or personal use case"

    # 1. Processing Volume (up to 40 pts)
    volume_num = _extract_number(combined_text)
    if any(k in combined_text for k in ["10,000", "10000", "50,000", "50000", "100,000", "100000", "enterprise volume", "scale"]):
        score += 40.0
        evidence_parts.append("High enterprise volume (~10,000+ units/month)")
    elif volume_num and volume_num >= 1000:
        score += 25.0
        evidence_parts.append(f"Significant monthly operational volume (~{int(volume_num)} units)")
    else:
        score += 10.0

    # 2. Company Size / Scale (up to 20 pts)
    if any(w in size_clean for w in ["500", "1000", "5000", "10,000", "enterprise", "large"]):
        score += 20.0
        evidence_parts.append(f"Enterprise organization size ({company_size})")
    elif any(w in size_clean for w in ["50", "100", "200", "250", "mid"]):
        score += 15.0
        evidence_parts.append(f"Mid-market organization size ({company_size})")
    elif size_clean and size_clean not in ("unknown", "unspecified", ""):
        score += 10.0

    # 3. High-Value Industry (up to 10 pts)
    if any(ind in industry_clean for ind in ["finance", "financial", "banking", "insurance", "healthcare", "legal", "fintech"]):
        score += 10.0
        evidence_parts.append(f"High-value vertical ({industry})")

    opportunity_score = round(max(0.0, min(100.0, score)), 2)
    evidence = "; ".join(evidence_parts)
    return opportunity_score, evidence


def calculate_risk_score(
    missing_information: Optional[List[str]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    inquiry_text: str = "",
    additional_context: Optional[str] = None,
) -> Tuple[float, str]:
    """
    Calculate deterministic Risk Score (0 to 100, where lower is better).
    Measures ambiguity, unaddressed compliance needs, and missing critical fields.
    """
    base_risk = 20.0
    evidence_parts = []

    missing = missing_information or []
    combined = f"{inquiry_text} {additional_context or ''}".lower()

    # 0. Check spam / non-commercial
    if any(t in combined for t in SPAM_TERMS) or any(t in combined for t in FREE_TERMS):
        return 85.0, "High commercial unviability risk; personal or non-commercial request"

    # 1. Missing information risk
    if len(missing) > 0:
        added_risk = min(40.0, len(missing) * 12.0)
        base_risk += added_risk
        evidence_parts.append(f"{len(missing)} missing requirement items identified")
    else:
        evidence_parts.append("No critical requirements missing")

    # 2. Compliance certainty
    has_compliance_req = any(c in combined for c in ["iso 27001", "soc 2", "soc2", "gdpr", "hipaa"])
    if has_compliance_req:
        evidence_parts.append("Standard compliance standards identified (supported by Compliance Shield)")
    else:
        base_risk += 5.0

    risk_score = round(max(10.0, min(95.0, base_risk)), 2)
    evidence = "; ".join(evidence_parts)
    return risk_score, evidence


def calculate_composite_lead_score(
    fit_score: float,
    readiness_score: float,
    opportunity_score: float,
    risk_score: float,
) -> float:
    """
    Authoritative composite Lead Score formula:
    Score = (Fit * fit_weight) + (Readiness * readiness_weight)
          + (Opportunity * opportunity_weight) + ((100 - Risk) * risk_weight)
    """
    fit_w = getattr(settings, "FIT_SCORE_WEIGHT", 0.25)
    readiness_w = getattr(settings, "READINESS_SCORE_WEIGHT", 0.25)
    opportunity_w = getattr(settings, "OPPORTUNITY_SCORE_WEIGHT", 0.30)
    risk_w = getattr(settings, "RISK_SCORE_WEIGHT", 0.20)

    composite = (
        (float(fit_score) * fit_w)
        + (float(readiness_score) * readiness_w)
        + (float(opportunity_score) * opportunity_w)
        + ((100.0 - float(risk_score)) * risk_w)
    )
    return round(max(0.0, min(100.0, composite)), 2)


def determine_qualification_status(
    composite_score: float,
    missing_information: Optional[List[str]] = None,
) -> str:
    """
    Authoritative qualification status determination strictly derived from score and thresholds.
    The LLM is NEVER allowed to override this determination.
    """
    missing = [m for m in (missing_information or []) if m and str(m).strip()]
    score = float(composite_score)

    # Incomplete customer information requires follow-up
    if missing:
        return "Needs More Information"

    qualified_thresh = getattr(settings, "QUALIFIED_SCORE_THRESHOLD", 75.0)
    needs_info_thresh = getattr(settings, "NEEDS_INFO_SCORE_THRESHOLD", 50.0)

    if score >= qualified_thresh:
        return "Qualified"
    elif score < needs_info_thresh:
        return "Low Priority"
    else:
        return "Needs More Information"


def sanitize_missing_information(
    missing_info: Optional[List[str]],
    lead_dict: Dict[str, Any],
) -> List[str]:
    """Clean and filter missing_information against confirmed lead fields.
    
    Prevents false requirements flags if customer already provided the field.
    """
    if not missing_info:
        return []

    budget = (lead_dict.get("budget") or "").strip().lower()
    timeline = (lead_dict.get("timeline") or "").strip().lower()
    company_size = (lead_dict.get("company_size") or "").strip().lower()
    contact_name = (lead_dict.get("contact_name") or "").strip().lower()

    has_budget = bool(budget and budget not in ("unspecified", "tbd", "to be confirmed", "none", "unknown", ""))
    has_timeline = bool(timeline and timeline not in ("unspecified", "tbd", "to be confirmed", "none", "unknown", ""))
    has_size = bool(company_size and company_size not in ("unspecified", "tbd", "none", "unknown", ""))
    has_contact = bool(contact_name and contact_name not in ("unspecified", "tbd", "none", "unknown", ""))

    sanitized = []
    for item in missing_info:
        if not item or not str(item).strip():
            continue
        text = str(item).lower()
        if has_budget and ("budget" in text or "investment" in text):
            continue
        if has_timeline and ("timeline" in text or "schedule" in text or "implementation" in text):
            continue
        if has_size and ("company size" in text or "number of users" in text or "headcount" in text):
            continue
        if has_contact and ("decision-maker" in text or "decision maker" in text or "approval" in text or "contact" in text):
            continue
        if any(w in text for w in ("document format", "technical constraint", "minor", "nice to have")):
            continue
        sanitized.append(str(item).strip())

    return sanitized


def evaluate_complete_lead(
    lead_dict: Dict[str, Any],
    research_result: Optional[Dict[str, Any]] = None,
    requirements_result: Optional[Dict[str, Any]] = None,
    solution_result: Optional[Dict[str, Any]] = None,
    qualitative_llm_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Single authoritative entry point to score and qualify a lead.
    Combines LLM-extracted qualitative drivers with deterministic mathematical scoring.
    """
    inquiry_text = lead_dict.get("inquiry_text") or ""
    company_size = lead_dict.get("company_size") or (research_result or {}).get("company_size")
    industry = lead_dict.get("industry") or (research_result or {}).get("industry_vertical")
    budget = lead_dict.get("budget")
    timeline = lead_dict.get("timeline")
    additional_context = lead_dict.get("additional_context")
    raw_missing = (requirements_result or {}).get("missing_information", [])
    missing_info = sanitize_missing_information(raw_missing, lead_dict)

    # 1. Deterministic component scoring
    fit_score, fit_evidence = calculate_fit_score(requirements_result, solution_result, inquiry_text)
    readiness_score, readiness_evidence = calculate_readiness_score(budget, timeline, additional_context, missing_info)
    opportunity_score, opportunity_evidence = calculate_opportunity_score(company_size, industry, inquiry_text, additional_context)
    risk_score, risk_evidence = calculate_risk_score(missing_info, (requirements_result or {}).get("constraints"), inquiry_text, additional_context)


    # 2. Authoritative composite score
    composite_score = calculate_composite_lead_score(fit_score, readiness_score, opportunity_score, risk_score)

    # 3. Deterministic status
    lead_status = determine_qualification_status(composite_score, missing_info)

    # 4. Qualitative evidence (reuse LLM drivers if available, otherwise deterministic drivers)
    llm_drivers = (qualitative_llm_result or {}).get("score_drivers") or []
    llm_questions = (qualitative_llm_result or {}).get("follow_up_questions") or []

    if not llm_drivers:
        llm_drivers = [
            ["Solution Fit Alignment", f"{fit_score}/100"],
            ["Budget & Timeline Readiness", f"{readiness_score}/100"],
            ["Enterprise Volume & Opportunity", f"{opportunity_score}/100"],
            ["Execution & Compliance Risk", f"{risk_score}/100"],
        ]

    return {
        "lead_status": lead_status,
        "composite_score": composite_score,
        "fit_score": fit_score,
        "fit_evidence": fit_evidence,
        "readiness_score": readiness_score,
        "readiness_evidence": readiness_evidence,
        "opportunity_score": opportunity_score,
        "opportunity_evidence": opportunity_evidence,
        "risk_score": risk_score,
        "risk_evidence": risk_evidence,
        "qualification_reasoning": f"Lead evaluated as {lead_status} with deterministic score {composite_score}/100 based on Fit ({fit_score}), Readiness ({readiness_score}), Opportunity ({opportunity_score}), and Risk ({risk_score}).",
        "score_drivers": llm_drivers,
        "follow_up_questions": llm_questions or missing_info,
        "qualification_version": QUALIFICATION_VERSION,
        "scoring_config_version": SCORING_CONFIG_VERSION,
    }
