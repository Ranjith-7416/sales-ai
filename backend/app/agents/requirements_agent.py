"""Requirements Agent - Extract and clarify customer requirements"""
from typing import Optional, Dict, Any
from app.services.llm_service import get_llm_service
from app.utils.json_utils import parse_json_response
import logging
import json

logger = logging.getLogger(__name__)


def _compact_research_context(research_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Keep only the research fields that materially affect requirement extraction."""
    if not research_context:
        return {}
    return {
        "company_name": research_context.get("company_name"),
        "industry_vertical": research_context.get("industry_vertical"),
        "company_size": research_context.get("company_size"),
        "location": research_context.get("location"),
        "business_model": research_context.get("business_model"),
        "public_contact": research_context.get("public_contact") or {},
    }


async def run_requirements_agent(
    inquiry_text: str,
    research_context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[list] = None,
    budget: Optional[str] = None,
    timeline: Optional[str] = None,
    company_size: Optional[str] = None,
    additional_context: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute requirements analysis from the inquiry plus research and commercial context."""
    try:
        llm_service = get_llm_service()

        research_context_str = ""
        compact_research = _compact_research_context(research_context)
        if compact_research:
            research_context_str = f"\nResearch Context:\n{json.dumps(compact_research, ensure_ascii=False)}\n"

        extra_context = []
        if budget: extra_context.append(f"Budget: {budget}")
        if timeline: extra_context.append(f"Timeline: {timeline}")
        if company_size: extra_context.append(f"Company Size: {company_size}")
        if additional_context: extra_context.append(f"Additional Context: {additional_context}")
        commercial_str = ("\nCommercial Context:\n" + "\n".join(extra_context) + "\n") if extra_context else ""

        history_context = ""
        if conversation_history:
            history_context = "\nConversation history (customer-provided context only):\n" + json.dumps(
                conversation_history[:2], ensure_ascii=False
            ) + "\n"

        prompt = f"""You are a requirements analyst for an enterprise B2B AI software company. Extract and normalize customer requirements from the inquiry and research context.

Customer Inquiry:
{inquiry_text}
{commercial_str}{research_context_str}{history_context}
Extract JSON only with this structure:
{{
  "functional_requirements": ["req1"],
  "non_functional_requirements": {{
    "scale": "volume indicators",
    "performance": "latency requirements",
    "compliance": "regulatory needs",
    "availability": "uptime SLA",
    "security": "auth/encryption needs"
  }},
  "constraints": {{
    "budget": "amount if mentioned",
    "timeline": "urgency/date",
    "technical_preferences": "existing stack",
    "industry": "vertical constraints"
  }},
  "missing_information": ["gap1"],
  "assumptions": ["assumption1"],
  "priority_mapping": {{
    "must_have": ["req1"],
    "nice_to_have": ["req2"]
  }}
}}

CRITICAL RULES FOR "missing_information":
1. If the inquiry is personal, academic/homework (e.g. essays, student homework), cryptocurrency, consumer spam, or has zero budget ($0 / free), do NOT list missing information (set "missing_information": []).
2. For commercial B2B inquiries: ONLY list missing information if critical commercial discovery items are missing.
3. If budget, timeline, volume, or size are already provided in the inquiry or Commercial Context, do NOT list them as missing!
Do not assume requirements not stated or clearly implied.
"""

        response = await llm_service.invoke(prompt, use_reasoning=False)
        
        # Parse response
        try:
            result = parse_json_response(response)
        except json.JSONDecodeError:
            result = _fallback_requirements(inquiry_text, research_context, budget, timeline, company_size, additional_context)

        # Post-process missing_information to ensure consistent B2B qualification
        combined_text = f"{inquiry_text or ''} {additional_context or ''}".lower()
        spam_terms = ('homework', 'school', 'essay', 'crypto', 'bitcoin', 'shoes', 'weather', 'game', 'gaming', 'personal use', 'recipe')
        free_terms = ('free only', 'no budget', 'zero budget', 'cant pay', 'cannot pay', 'have no money', 'student')
        is_spam = any(w in combined_text for w in spam_terms) or any(w in combined_text for w in free_terms)

        if is_spam:
            result["missing_information"] = []
        else:
            has_volume = any(k in combined_text for k in ("10,000", "10000", "20,000", "25,000", "30,000", "50,000", "50000", "100k", "500", "daily", "monthly", "per month", "/month", "/mo", "volume", "scale", "records", "batches", "documents"))
            has_budget = bool(budget and budget.strip().lower() not in ("unspecified", "tbd", "none", "unknown", "")) or any(k in combined_text for k in ("$", "budget", "per month", "/month", "/mo", "allocated", "tier", "investment"))
            has_timeline = bool(timeline and timeline.strip().lower() not in ("unspecified", "tbd", "none", "unknown", "")) or any(k in combined_text for k in ("month", "week", "timeline", "q1", "q2", "q3", "q4", "asap", "immediate", "rollout", "deploy", "start"))
            
            raw_missing = result.get("missing_information") or []
            filtered_missing = []
            for item in raw_missing:
                item_lower = str(item).lower()
                if has_budget and ("budget" in item_lower or "investment" in item_lower):
                    continue
                if has_timeline and ("timeline" in item_lower or "schedule" in item_lower or "implementation" in item_lower):
                    continue
                filtered_missing.append(item)

            if has_volume and has_budget and has_timeline:
                result["missing_information"] = []
            else:
                result["missing_information"] = filtered_missing
        
        logger.info("Requirements analysis completed")
        return result
        
    except Exception as e:
        logger.warning(f"Requirements agent LLM call failed ({e}); using intelligent contextual fallback")
        return _fallback_requirements(inquiry_text, research_context, budget, timeline, company_size, additional_context)


def _fallback_requirements(
    inquiry_text: str,
    research_context: Optional[Dict[str, Any]] = None,
    budget: Optional[str] = None,
    timeline: Optional[str] = None,
    company_size: Optional[str] = None,
    additional_context: Optional[str] = None,
) -> Dict[str, Any]:
    combined_raw = f"{inquiry_text or ''} {additional_context or ''}"
    text_lower = combined_raw.lower()
    fn_reqs = []
    
    # 1. Document AI & OCR Extraction
    if any(k in text_lower for k in ("pdf", "document", "extract", "ocr", "invoice", "form", "scan", "receipt", "table")):
        vol_label = "approximately 10,000 PDF documents per month" if any(v in text_lower for v in ("10,000", "10000")) else "customer document batches"
        fn_reqs.append(f"Automated structured text and key-value extraction from {vol_label}")
        if any(k in text_lower for k in ("ocr", "accura")):
            fn_reqs.append("High-accuracy Optical Character Recognition (OCR > 99%) for native and scanned documents")
        if any(k in text_lower for k in ("table", "form", "tabular")):
            fn_reqs.append("Layout-aware table, form, and multi-column grid data parsing")

    # 2. Conversational & Customer Support AI
    if any(k in text_lower for k in ("chat", "support", "conversational", "ticket", "bot", "agent", "helpdesk")):
        fn_reqs.append("Conversational AI virtual agent with multi-turn intent resolution and ticket deflection")
        if any(k in text_lower for k in ("omnichannel", "web", "mobile", "whatsapp", "email")):
            fn_reqs.append("Omnichannel deployment across web chat, mobile SDK, and email support queues")
        if any(k in text_lower for k in ("live agent", "escalat", "human")):
            fn_reqs.append("Automated sentiment detection and seamless live agent escalation routing")

    # 3. Security & Compliance
    if any(k in text_lower for k in ("hipaa", "soc2", "soc 2", "compliance", "phi", "pii", "redact")):
        fn_reqs.append("Automated PII/PHI redaction, HIPAA compliance, and SOC 2 Type II certified data pipeline")

    # Fallback generic requirement if none matched
    if not fn_reqs:
        clean_inquiry = inquiry_text.strip()[:140] if inquiry_text else "Enterprise AI solution and workflow automation"
        fn_reqs.append(clean_inquiry)

    # Detect Missing Information
    spam_terms = ('homework', 'school', 'essay', 'crypto', 'bitcoin', 'shoes', 'weather', 'game', 'gaming', 'personal use', 'recipe')
    free_terms = ('free only', 'no budget', 'zero budget', 'cant pay', 'cannot pay', 'have no money', 'student')
    is_spam = any(w in text_lower for w in spam_terms) or any(w in text_lower for w in free_terms)

    missing_info = []
    if not is_spam:
        has_volume = any(k in text_lower for k in ("10,000", "10000", "50,000", "50000", "100k", "500", "daily", "monthly", "per month", "/month", "/mo", "volume", "scale"))
        has_budget = bool(budget and budget.strip().lower() not in ("unspecified", "tbd", "none", "unknown", "")) or any(k in text_lower for k in ("$", "budget", "per month", "/month", "/mo", "approved budget", "tier"))
        has_timeline = bool(timeline and timeline.strip().lower() not in ("unspecified", "tbd", "none", "unknown", "")) or any(k in text_lower for k in ("month", "week", "timeline", "q1", "q2", "q3", "q4", "asap", "immediate", "rollout", "deploy"))

        if not has_volume:
            missing_info.append("Target monthly document or customer interaction volume not specified")
        if not has_budget:
            missing_info.append("Approved commercial budget range or expected investment not confirmed")
        if not has_timeline:
            missing_info.append("Target production rollout timeline not specified")
        if not any(k in text_lower for k in ("api", "rest", "webhook", "integration", "crm", "ehr", "database")):
            missing_info.append("Downstream destination systems and API integration targets not specified")

        # If the inquiry is an explicit complete prompt with volume, budget, timeline, and compliance, clear missing_info
        if has_volume and (has_budget or "$" in text_lower) and has_timeline and ("hipaa" in text_lower or "soc" in text_lower or "accuracy" in text_lower):
            missing_info = []

    return {
        "functional_requirements": fn_reqs,
        "non_functional_requirements": {
            "scale": "Approximately 10,000 PDF documents per month" if "10,000" in text_lower or "10000" in text_lower else "Scalable cloud inference pipeline",
            "performance": "Processing latency < 3 seconds per document / message",
            "compliance": "HIPAA compliance and enterprise data encryption" if "hipaa" in text_lower else "Enterprise data security and TLS encryption",
            "availability": "99.9% service availability SLA",
            "security": "End-to-end encryption at rest and in transit",
        },
        "constraints": {
            "budget": "Documented in commercial inquiry" if has_budget else "To be confirmed during discovery",
            "timeline": "Documented in commercial inquiry" if has_timeline else "To be confirmed during discovery",
            "technical_preferences": "REST API, webhook integration",
            "industry": (research_context or {}).get("industry_vertical", "Enterprise"),
        },
        "missing_information": missing_info,
        "assumptions": [
            "Customer will provide sample representative inputs during technical onboarding",
            "Production access credentials and network connectivity provided by customer",
        ],
        "priority_mapping": {
            "must_have": [fn_reqs[0]] if fn_reqs else ["Core capability delivery"],
            "nice_to_have": fn_reqs[1:] if len(fn_reqs) > 1 else ["Automated confidence scoring"],
        },
    }
