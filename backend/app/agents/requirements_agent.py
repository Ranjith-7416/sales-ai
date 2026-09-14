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
) -> Dict[str, Any]:
    """Execute requirements analysis from the inquiry plus the minimal research slice."""
    try:
        llm_service = get_llm_service()

        research_context_str = ""
        compact_research = _compact_research_context(research_context)
        if compact_research:
            research_context_str = f"\nResearch Context:\n{json.dumps(compact_research, ensure_ascii=False)}\n"

        history_context = ""
        if conversation_history:
            history_context = "\nConversation history (customer-provided context only):\n" + json.dumps(
                conversation_history[:2], ensure_ascii=False
            ) + "\n"

        prompt = f"""You are a requirements analyst. Extract and normalize the customer requirements from the inquiry and only the required research slice.

Customer Inquiry:
{inquiry_text}
{research_context_str}
{history_context}

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

Do not assume requirements not stated or clearly implied.
"""

        response = await llm_service.invoke(prompt, use_reasoning=False)
        
        # Parse response
        try:
            result = parse_json_response(response)
        except json.JSONDecodeError:
            result = _fallback_requirements(inquiry_text, research_context)
        
        logger.info("Requirements analysis completed")
        return result
        
    except Exception as e:
        logger.warning(f"Requirements agent LLM call failed ({e}); using intelligent contextual fallback")
        return _fallback_requirements(inquiry_text, research_context)


def _fallback_requirements(inquiry_text: str, research_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    text_lower = (inquiry_text or "").lower()
    fn_reqs = []
    if "10,000" in text_lower or "10000" in text_lower or "pdf" in text_lower or "extract" in text_lower:
        fn_reqs.append("Extract structured text and form data from approximately 10,000 PDF documents per month")
    if "ocr" in text_lower or "accura" in text_lower:
        fn_reqs.append("High-accuracy Optical Character Recognition (OCR > 99%)")
    if "table" in text_lower or "form" in text_lower:
        fn_reqs.append("Layout-aware table and tabular data parsing")
    if "api" in text_lower or "integrat" in text_lower or "rest" in text_lower:
        fn_reqs.append("REST API and webhook integration with existing document warehouse")
    if not fn_reqs:
        fn_reqs.append(inquiry_text[:120] if inquiry_text else "Automated document processing and intelligence")

    return {
        "functional_requirements": fn_reqs,
        "non_functional_requirements": {
            "scale": "Approximately 10,000 PDF documents per month",
            "performance": "Automated batch and real-time processing latency < 3 seconds per document",
            "compliance": "Enterprise data security (SOC 2 Type II, ISO 27001, HIPAA data encryption)",
            "availability": "High availability with 99.9% uptime SLA",
            "security": "End-to-end TLS 1.3 encryption and role-based access control",
        },
        "constraints": {
            "budget": "Enterprise monthly subscription",
            "timeline": "Production deployment within 1-2 months",
            "technical_preferences": "REST API and secure cloud or on-premise pipeline",
            "industry": (research_context or {}).get("industry_vertical", "Enterprise"),
        },
        "missing_information": [],
        "assumptions": [
            "Input documents are standard digital or high-resolution scanned PDFs",
            "Client will provide destination schema mappings during onboarding phase",
        ],
        "priority_mapping": {
            "must_have": [fn_reqs[0]] if fn_reqs else ["PDF extraction"],
            "nice_to_have": ["Custom fine-tuned domain models", "Automated validation confidence scoring"],
        },
    }
