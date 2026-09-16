"""Qualification Agent - Score leads with explainable criteria"""
from typing import Optional, Dict, Any
from app.services.llm_service import get_llm_service
from app.config import settings
from app.status_utils import normalize_lead_status
from app.utils.json_utils import parse_json_response
import logging
import json

logger = logging.getLogger(__name__)


def _compact_research(research_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Send only research fields that influence qualification evidence."""
    if not research_result:
        return {}
    return {
        "company_name": research_result.get("company_name"),
        "industry_vertical": research_result.get("industry_vertical"),
        "company_size": research_result.get("company_size"),
        "location": research_result.get("location"),
        "business_model": research_result.get("business_model"),
        "market_position": research_result.get("market_position"),
    }


def _compact_requirements(requirements_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Send only the requirement-derived fields that feed scoring evidence."""
    if not requirements_result:
        return {}
    return {
        "functional_requirements": requirements_result.get("functional_requirements", []),
        "missing_information": requirements_result.get("missing_information", []),
        "constraints": requirements_result.get("constraints", {}),
        "priority_mapping": requirements_result.get("priority_mapping", {}),
    }


def _bounded_score(value: Any) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


from app.services.scoring_engine import (
    evaluate_complete_lead,
    calculate_composite_lead_score,
    determine_qualification_status,
    QUALIFICATION_VERSION,
    SCORING_CONFIG_VERSION,
)


def calculate_deterministic_qualification(result: Dict[str, Any], missing_information: list[str] | None = None) -> Dict[str, Any]:
    """Derive the final score and status deterministically from configured weights and thresholds."""
    result["fit_score"] = _bounded_score(result.get("fit_score"))
    result["readiness_score"] = _bounded_score(result.get("readiness_score"))
    result["opportunity_score"] = _bounded_score(result.get("opportunity_score"))
    result["risk_score"] = _bounded_score(result.get("risk_score"))
    result["composite_score"] = calculate_composite_lead_score(
        result["fit_score"],
        result["readiness_score"],
        result["opportunity_score"],
        result["risk_score"],
    )
    result["lead_status"] = determine_qualification_status(
        result["composite_score"],
        missing_information,
    )
    result["qualification_version"] = QUALIFICATION_VERSION
    result["scoring_config_version"] = SCORING_CONFIG_VERSION
    return result


async def run_qualification_agent(
    research_result: Optional[Dict[str, Any]] = None,
    requirements_result: Optional[Dict[str, Any]] = None,
    lead_data: Optional[Dict[str, Any]] = None,
    solution_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute qualification agent. Qualitative facts extracted via LLM; all scores and status computed deterministically."""
    lead_dict = dict(lead_data) if lead_data else {}
    if research_result:
        lead_dict.setdefault("company_name", research_result.get("company_name"))
        lead_dict.setdefault("industry", research_result.get("industry_vertical"))
        lead_dict.setdefault("company_size", research_result.get("company_size"))

    try:
        llm_service = get_llm_service()

        research_str = json.dumps(_compact_research(research_result), ensure_ascii=False) if research_result else "No research data"
        requirements_str = json.dumps(_compact_requirements(requirements_result), ensure_ascii=False) if requirements_result else "No requirements data"
        
        commercial_str = ""
        if lead_dict:
            comm_items = []
            if lead_dict.get("budget"): comm_items.append(f"Budget: {lead_dict['budget']}")
            if lead_dict.get("timeline"): comm_items.append(f"Timeline: {lead_dict['timeline']}")
            if lead_dict.get("company_size"): comm_items.append(f"Company Size: {lead_dict['company_size']}")
            if lead_dict.get("additional_context"): comm_items.append(f"Additional Context: {lead_dict['additional_context']}")
            if comm_items:
                commercial_str = "\nCOMMERCIAL CONTEXT:\n" + "\n".join(comm_items) + "\n"

        prompt = f"""You are an enterprise B2B sales lead qualification expert.
Our Product Offerings:
1. Enterprise Document AI / OCR / Table Extraction (Processing PDFs, invoices, forms, charts at scale).
2. Conversational Customer Support AI (Omnichannel virtual agents, ticket deflection, CRM integration).
3. Compliance Shield AI (HIPAA, SOC2, PII/PHI redaction, audit logging).

Evaluate the following lead context and requirements carefully:

RESEARCH CONTEXT:
{research_str}
{commercial_str}
REQUIREMENTS:
{requirements_str}

Extract qualitative evidence and score drivers in JSON format:
{{
  "fit_evidence": "concise explanation of product capability alignment",
  "readiness_evidence": "concise explanation of budget and timeline readiness",
  "opportunity_evidence": "concise explanation of scale and opportunity size",
  "risk_evidence": "concise explanation of delivery or compliance risk",
  "score_drivers": [["Factor name", "Impact assessment"]],
  "follow_up_questions": ["question 1"]
}}

Only extract qualitative assessments. All numeric scores and final status are calculated deterministically by the scoring engine.
"""

        response = await llm_service.invoke(prompt, use_reasoning=False)
        
        try:
            qualitative_result = parse_json_response(response)
        except json.JSONDecodeError:
            qualitative_result = None

        final_result = evaluate_complete_lead(
            lead_dict=lead_dict,
            research_result=research_result,
            requirements_result=requirements_result,
            solution_result=solution_result,
            qualitative_llm_result=qualitative_result,
        )
        logger.info(f"Qualification completed - Score: {final_result.get('composite_score')} - Status: {final_result.get('lead_status')}")
        return final_result
        
    except Exception as e:
        logger.warning(f"Qualification agent LLM call failed ({e}); using deterministic fallback evaluation")
        return evaluate_complete_lead(
            lead_dict=lead_dict,
            research_result=research_result,
            requirements_result=requirements_result,
            solution_result=solution_result,
            qualitative_llm_result=None,
        )


def _fallback_qualification(research_result: Optional[Dict[str, Any]], requirements_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    reqs = (requirements_result or {}).get("functional_requirements", [])
    constraints = (requirements_result or {}).get("constraints", {})
    missing_info = (requirements_result or {}).get("missing_information", [])
    
    req_text = (" ".join(reqs) + " " + json.dumps(constraints)).lower()
    
    # Check for out-of-scope / spam / personal / homework
    spam_terms = ('homework', 'school', 'essay', 'crypto', 'bitcoin', 'shoes', 'weather', 'game', 'gaming', 'personal use', 'recipe')
    free_terms = ('free only', 'no budget', 'zero budget', 'cant pay', 'cannot pay', 'have no money', 'student')
    
    is_spam = any(w in req_text for w in spam_terms)
    is_free = any(w in req_text for w in free_terms)
    
    if is_spam or is_free:
        raw = {
            "fit_score": 15.0,
            "fit_evidence": "Inquiry is personal, consumer, or outside core enterprise B2B product capabilities.",
            "readiness_score": 10.0,
            "readiness_evidence": "Sub-commercial intent with no enterprise procurement budget or decision timeline.",
            "opportunity_score": 10.0,
            "opportunity_evidence": "Non-commercial individual use case with zero recurring revenue potential.",
            "risk_score": 85.0,
            "risk_evidence": "High delivery and commercial unviability risk; outside target enterprise market.",
            "qualification_reasoning": "Unqualified: Non-commercial or out-of-scope request. Recommended to decline or route to public community resources.",
            "score_drivers": [
                ["Capability Scope", "Out-of-Scope (-85)"],
                ["Commercial Budget", "Zero Budget (-90)"],
                ["Market Fit", "Consumer / Personal (-85)"],
            ],
            "follow_up_questions": [],
        }
        return calculate_deterministic_qualification(raw, missing_info)

    # Core enterprise offering checks
    doc_match = any(w in req_text for w in ('pdf', 'document', 'ocr', 'extract', 'invoice', 'form', 'scan', 'receipt', 'table'))
    chat_match = any(w in req_text for w in ('chat', 'support', 'conversational', 'ticket', 'bot', 'agent', 'helpdesk'))
    compliance_match = any(w in req_text for w in ('hipaa', 'soc2', 'soc 2', 'compliance', 'redact', 'pii', 'phi'))
    
    has_enterprise_vol = any(w in req_text for w in ('10,000', '10000', '50,000', '50000', '100k', 'high volume', 'enterprise scale', 'thousands'))
    has_budget = any(w in req_text for w in ('$', 'budget', 'per month', '/month', '/mo', 'approved budget', 'enterprise subscription'))
    has_timeline = any(w in req_text for w in ('month', 'week', 'timeline', 'q1', 'q2', 'q3', 'q4', 'asap', 'immediate', 'production rollout'))

    if doc_match or chat_match:
        fit = 92.0 if (compliance_match or (doc_match and has_enterprise_vol)) else 84.0
    else:
        fit = 55.0

    readiness = 88.0 if (has_budget and has_timeline) else 55.0 if (has_budget or has_timeline) else 35.0
    opportunity = 88.0 if has_enterprise_vol else 60.0 if (doc_match or chat_match) else 30.0
    risk = 18.0 if (has_budget and has_timeline and not missing_info) else 35.0 if not missing_info else 50.0

    reasoning = (
        "High-intent enterprise opportunity with strong capability fit, verified volume, and clear commercial alignment."
        if not missing_info and (fit >= 80 and readiness >= 75)
        else "Potentially viable opportunity, but critical commercial requirements (volume, budget, or timeline) require discovery follow-up."
    )

    raw = {
        "fit_score": fit,
        "fit_evidence": f"Requirement aligns with {'Enterprise Document AI & OCR' if doc_match else 'Conversational Support AI' if chat_match else 'Enterprise Automation'} capabilities.",
        "readiness_score": readiness,
        "readiness_evidence": "Production timeline and commercial budget parameters are documented." if (has_budget and has_timeline) else "Commercial budget or implementation timeline require confirmation.",
        "opportunity_score": opportunity,
        "opportunity_evidence": "High-volume recurring enterprise workload." if has_enterprise_vol else "Moderate commercial workload scale.",
        "risk_score": risk,
        "risk_evidence": "Low technical delivery risk." if risk < 25 else "Moderate risk pending confirmation of technical formats and integrations.",
        "qualification_reasoning": reasoning,
        "score_drivers": [
            ["Solution Alignment", f"Fit ({fit:.0f})"],
            ["Commercial Readiness", f"Readiness ({readiness:.0f})"],
            ["Workload Scale", f"Opportunity ({opportunity:.0f})"],
            ["Integration Risk", f"Risk ({risk:.0f})"],
        ],
        "follow_up_questions": missing_info or [],
    }
    return calculate_deterministic_qualification(raw, missing_info)
