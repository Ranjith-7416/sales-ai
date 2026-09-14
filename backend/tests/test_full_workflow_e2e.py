import json

import pytest


class DeterministicWebSearchService:
    """Deterministic fixture for the research web-search boundary only."""

    async def search_company(self, company_name: str):
        return {
            "company_name": company_name,
            "search_results": [
                {
                    "title": "MediTech Solutions profile",
                    "url": "https://example.test/meditech",
                    "description": "Healthcare technology provider with document workflows.",
                }
            ],
        }

    async def search_industry(self, industry: str):
        return {
            "industry": industry,
            "search_results": [
                {
                    "title": "Healthcare document automation trends",
                    "url": "https://example.test/healthcare-docs",
                    "description": "Healthcare organizations need secure, compliant document extraction and workflow automation.",
                }
            ],
        }


class DeterministicLLMService:
    """Deterministic fixture for the LLM boundary only; real downstream parser and validator remain active."""

    async def invoke(self, prompt: str, use_reasoning: bool = False) -> str:
        prompt_text = prompt.lower()

        if "business intelligence researcher" in prompt_text:
            return json.dumps({
                "company_name": "MediTech Solutions",
                "industry_vertical": "Healthcare",
                "company_size": "500-1000 employees",
                "location": "Not publicly available",
                "business_model": "Healthcare technology and clinical services company",
                "key_products_services": "Clinical services and technology products",
                "market_position": "Healthcare provider",
                "recent_news": ["MediTech Solutions expands digital health operations"],
                "concerns_flags": ["Document processing scale and compliance"],
                "public_contact": {
                    "website": "https://example.test/meditech",
                    "linkedin": "https://example.test/meditech-linkedin",
                },
            })

        if "requirements analyst" in prompt_text:
            return json.dumps({
                "functional_requirements": ["Extract PDF data", "Process 10,000 PDFs monthly"],
                "non_functional_requirements": {
                    "scale": "10,000 monthly PDFs",
                    "performance": "Near real-time extraction",
                    "compliance": "Healthcare data privacy controls",
                    "availability": "Business hours",
                    "security": "Encryption and access control",
                },
                "constraints": {
                    "budget": "$200K",
                    "timeline": "3 months",
                    "technical_preferences": "Document automation",
                    "industry": "Healthcare",
                },
                "missing_information": [],
                "assumptions": ["Document quality is sufficiently consistent"],
                "priority_mapping": {
                    "must_have": ["Extract PDF data", "Process 10,000 PDFs monthly"],
                    "nice_to_have": ["Risk reporting"],
                },
            })

        if "lead qualification expert" in prompt_text:
            return json.dumps({
                "fit_score": 85,
                "fit_evidence": "Healthcare document processing requirement is a strong fit for product capabilities.",
                "readiness_score": 82,
                "readiness_evidence": "Customer timeline, budget, and implementation range are documented.",
                "opportunity_score": 80,
                "opportunity_evidence": "Healthcare document automation has measurable workflow impact.",
                "risk_score": 18,
                "risk_evidence": "Low risk due to clear requirements and defined scale.",
                "score_drivers": [["document workflow fit", "strong"], ["timeline clarity", "high"]],
                "follow_up_questions": [],
            })

        if "solution architect" in prompt_text:
            return json.dumps({
                "primary_solutions": [
                    {
                        "product_name": "DocumentAI Pro",
                        "coverage_percentage": 90,
                        "features_matched": ["OCR with 99.8% accuracy", "Layout-aware extraction"],
                        "features_missing": [],
                        "pricing": "$5,000 - $50,000/month",
                        "delivery_timeline": "2-4 weeks",
                        "certifications": ["ISO 27001"],
                        "rationale": "DocumentAI Pro directly supports extracting structured data from PDF workflows and fits the healthcare compliance requirement.",
                        "evidence": [
                            {
                                "source": "products.json: prod-001",
                                "detail": "OCR with 99.8% accuracy and layout-aware extraction",
                                "matched_requirement": "Extract PDF data",
                            }
                        ],
                        "limitations": [],
                        "risks": [],
                    }
                ],
                "complementary_services": [
                    {
                        "name": "Implementation & Integration",
                        "reason": "Needed to integrate the document workflow",
                        "evidence": ["services.json: svc-001"],
                    }
                ],
                "add_ons_recommended": [],
                "requirement_coverage_matrix": {"Extract PDF data": "Full", "Process 10,000 PDFs monthly": "Partial"},
                "gaps_and_workarounds": [],
                "confidence_assessment": {
                    "overall": "High",
                    "reasoning": "Catalog evidence directly supports the requested workflow.",
                },
                "estimated_solution_value": {
                    "breakdown": {"DocumentAI Pro": "$5,000 - $50,000/month", "Implementation & Integration": "$3,000 - $8,000/month"},
                    "notes": "Pricing pulled from catalog evidence only.",
                },
            })

        if "proposal writer" in prompt_text:
            return json.dumps({
                "executive_summary": "DocumentAI Pro is a grounded fit for secure document processing workflows.",
                "customer_requirements": ["Extract PDF data", "Process 10,000 PDFs monthly"],
                "proposed_solution": "DocumentAI Pro provides layout-aware OCR workflows and secure extraction capabilities for healthcare document processing.",
                "implementation_roadmap": [
                    {"phase": "Discovery", "duration": "2-4 weeks", "activities": ["Validate PDF sources"]},
                    {"phase": "Implementation", "duration": "2-4 weeks", "activities": ["Deploy extraction workflow"]},
                ],
                "total_implementation_timeline": "2-4 weeks",
                "pricing_proposal": {
                    "base_product": "$5,000 - $50,000/month",
                    "add_ons": "[To be confirmed]",
                    "services": "$50,000 - $500,000",
                    "total_year_1": "[To be confirmed]",
                    "annual_renewal": "[To be confirmed]",
                },
                "support_service_levels": {
                    "tier": "24/7 Premium",
                    "response_time": "1 hour",
                },
                "success_metrics": ["Extract 10,000 PDFs monthly", "Maintain 99.8% OCR accuracy"],
                "next_steps": ["Review requirements", "Schedule technical discovery"],
                "sections": [
                    {"title": "Implementation", "content": "Use the DocumentAI Pro catalog-backed workflow with implementation services."}
                ],
            })

        if "quality assurance reviewer" in prompt_text:
            return json.dumps({
                "coverage_validation": [
                    {"requirement": "Extract PDF data", "addressed": True, "where": "DocumentAI Pro"},
                    {"requirement": "Process 10,000 PDFs monthly", "addressed": True, "where": "DocumentAI Pro"},
                ],
                "claim_verification": [
                    {"claim": "DocumentAI Pro supports OCR extraction", "verified": True, "source": "products.json: prod-001"},
                ],
                "unsupported_requirements": [],
                "missing_information": [],
                "risk_assessment": {
                    "technical_risks": ["Sample quality must be validated"],
                    "commercial_risks": [],
                    "organizational_risks": [],
                },
                "readiness_assessment": {
                    "ready_to_send": True,
                    "reason": "Catalog-grounded proposal passed validation",
                },
                "recommended_next_steps": ["Schedule discovery and pilot"],
                "follow_up_questions": [],
                "escalation_path": {
                    "approval_required": True,
                    "approver": "VP Sales",
                },
            })

        return "{}"


@pytest.mark.asyncio
async def test_deterministic_full_workflow_e2e(monkeypatch):
    """Deterministic full-workflow E2E using stubs only on LLM and web-search boundaries."""
    from app.agents import research_agent, requirements_agent, qualification_agent, solution_agent, proposal_agent, reviewer_agent
    from app.services import llm_service as llm_service_module
    from app.services import web_search as web_search_module

    fake_llm = DeterministicLLMService()
    fake_web = DeterministicWebSearchService()

    monkeypatch.setattr(research_agent, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(research_agent, "get_web_search_service", lambda: fake_web)
    monkeypatch.setattr(requirements_agent, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(qualification_agent, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(solution_agent, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(proposal_agent, "get_llm_service", lambda: fake_llm)
    monkeypatch.setattr(reviewer_agent, "get_llm_service", lambda: fake_llm)

    # Keep provider-backed E2E separate and untouched. This deterministic file exercises the
    # real orchestrator, real state schema parsing, real RAG retrieval, real proposal validator,
    # and real reviewer output validation via the same production code paths.
    monkeypatch.setattr(web_search_module, "get_web_search_service", lambda: fake_web)

    from app.agents.orchestrator import get_orchestrator

    result = await get_orchestrator().execute({
        "lead_id": "deterministic-e2e",
        "company_name": "MediTech Solutions",
        "industry": "Healthcare",
        "company_size": "500-1000 employees",
        "budget": "$200K",
        "timeline": "3 months",
        "additional_context": "Decision-maker confirmed approval. Success criteria and integrations are documented.",
        "inquiry_text": "We need an AI-powered document processing solution capable of extracting information from approximately 10,000 PDF documents per month.",
        "conversation_history": [],
    })

    assert not result.get("errors"), result.get("errors")
    assert set(("research", "requirements", "qualification", "solution_matching", "proposal", "reviewer")).issubset(
        set(result.get("stages_completed", []))
    )
    assert result["research_result"].get("company_name") == "MediTech Solutions"
    assert result["requirements_result"].get("functional_requirements")
    assert result["qualification_result"].get("composite_score") is not None
    assert result["solution_matching_result"].get("grounding_validation", {}).get("verified_solution_count", 0) > 0
    assert result["proposal_result"].get("proposal_status") == "approved"
    assert result["proposal_result"].get("grounding_validation", {}).get("approved") is True
    assert result["reviewer_result"].get("readiness_assessment", {}).get("ready_to_send") is True
