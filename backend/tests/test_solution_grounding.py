from app.agents.solution_agent import _ground_solutions, _compact_rag_context
from app.agents.orchestrator import _has_missing_information
from app.schemas import SolutionMatchingOutput


def test_real_kb_item_is_a_valid_grounded_match():
    result = _ground_solutions(
        {
            "primary_solutions": [
                {
                    "product_id": "prod-001",
                    "product_name": "DocumentAI Pro",
                    "features_matched": ["OCR with 99.8% accuracy"],
                    "pricing": "$5,000 - $50,000/month",
                    "delivery_timeline": "2-4 weeks",
                    "certifications": ["ISO 27001"],
                    "evidence": [{"source": "products.json: prod-001", "detail": "OCR with 99.8% accuracy", "matched_requirement": "Extract PDF"}],
                }
            ]
        },
        [{"product": {"id": "prod-001", "name": "DocumentAI Pro", "pricing": "$5,000 - $50,000/month", "implementation_timeline": "2-4 weeks", "certifications": ["ISO 27001"], "features": ["OCR with 99.8% accuracy"]}}],
        [],
    )

    assert result["grounding_validation"]["verified_solution_count"] == 1
    assert result["primary_solutions"][0]["product_id"] == "prod-001"
    assert result["primary_solutions"][0]["product_name"] == "DocumentAI Pro"


def test_missing_optional_metadata_does_not_reject_valid_grounded_match():
    result = _ground_solutions(
        {
            "primary_solutions": [
                {
                    "product_id": "prod-001",
                    "product_name": "DocumentAI Pro",
                    "features_matched": ["OCR with 99.8% accuracy"],
                    "evidence": [{"source": "products.json: prod-001", "detail": "OCR with 99.8% accuracy", "matched_requirement": "Extract PDF"}],
                }
            ]
        },
        [{"product": {"id": "prod-001", "name": "DocumentAI Pro", "features": ["OCR with 99.8% accuracy"]}}],
        [],
    )

    assert result["grounding_validation"]["verified_solution_count"] == 1
    assert result["primary_solutions"][0]["product_id"] == "prod-001"


def test_unknown_product_id_is_rejected():
    result = _ground_solutions(
        {
            "primary_solutions": [
                {"product_id": "prod-999", "product_name": "Unknown Product", "features_matched": ["OCR"]}
            ]
        },
        [{"product": {"id": "prod-001", "name": "DocumentAI Pro", "features": ["OCR with 99.8% accuracy"]}}],
        [],
    )

    assert result["grounding_validation"]["verified_solution_count"] == 0
    assert result["grounding_validation"]["rejected_solution_names"] == ["Unknown Product"]


def test_unsupported_capability_is_rejected():
    result = _ground_solutions(
        {
            "primary_solutions": [
                {"product_id": "prod-001", "product_name": "DocumentAI Pro", "features_matched": ["Invented laser surgery"]}
            ]
        },
        [{"product": {"id": "prod-001", "name": "DocumentAI Pro", "features": ["OCR with 99.8% accuracy"]}}],
        [],
    )

    assert result["grounding_validation"]["verified_solution_count"] == 0


def test_unsupported_price_is_rejected():
    result = _ground_solutions(
        {
            "primary_solutions": [
                {"product_id": "prod-001", "product_name": "DocumentAI Pro", "pricing": "Invented price"}
            ]
        },
        [{"product": {"id": "prod-001", "name": "DocumentAI Pro", "pricing": "$5,000 - $50,000/month", "features": ["OCR with 99.8% accuracy"]}}],
        [],
    )

    assert result["grounding_validation"]["verified_solution_count"] == 0


def test_unsupported_certification_is_rejected():
    result = _ground_solutions(
        {
            "primary_solutions": [
                {"product_id": "prod-001", "product_name": "DocumentAI Pro", "certifications": ["Invented certification"]}
            ]
        },
        [{"product": {"id": "prod-001", "name": "DocumentAI Pro", "certifications": ["ISO 27001"], "features": ["OCR with 99.8% accuracy"]}}],
        [],
    )

    assert result["grounding_validation"]["verified_solution_count"] == 0


def test_unsupported_sla_support_is_rejected():
    result = _ground_solutions(
        {
            "primary_solutions": [
                {"product_id": "prod-001", "product_name": "DocumentAI Pro", "support_hours": "Never", "sla": "99.999%"}
            ]
        },
        [{"product": {"id": "prod-001", "name": "DocumentAI Pro", "support_level": "24/7 Premium", "features": ["OCR with 99.8% accuracy"]}}],
        [],
    )

    assert result["grounding_validation"]["verified_solution_count"] == 0


def test_compact_evidence_preserves_grounding_when_caps_and_id_are_present():
    result = _ground_solutions(
        {
            "primary_solutions": [
                {
                    "product_id": "prod-001",
                    "product_name": "DocumentAI Pro",
                    "features_matched": ["OCR with 99.8% accuracy"],
                    "evidence": [{"source": "products.json: prod-001", "detail": "OCR with 99.8% accuracy", "matched_requirement": "Extract PDF"}],
                }
            ]
        },
        [{"product": {"id": "prod-001", "name": "DocumentAI Pro", "features": ["OCR with 99.8% accuracy"], "pricing": "$5,000 - $50,000/month"}}],
        [],
    )

    assert result["grounding_validation"]["verified_solution_count"] == 1
    assert result["primary_solutions"][0]["product_id"] == "prod-001"


def test_non_blocking_missing_information_does_not_stop_pipeline():
    assert not _has_missing_information({
        "requirements_result": {
            "functional_requirements": ["Extract data from PDF documents"],
            "missing_information": ["Target uptime SLA"],
        }
    })


def test_unusable_requirements_still_stop_pipeline():
    assert _has_missing_information({
        "requirements_result": {
            "functional_requirements": [],
            "missing_information": ["Unable to parse requirements"],
        }
    })


def test_grounding_rejects_unknown_solution_and_restores_catalog_facts():
    result = _ground_solutions(
        {
            "primary_solutions": [
                {
                    "product_name": "DocumentAI Pro",
                    "pricing": "Invented pricing",
                    "delivery_timeline": "Tomorrow",
                    "certifications": ["Invented certification"],
                },
                {"product_name": "Made Up Platform"},
            ]
        },
        [
            {
                "product": {
                    "name": "DocumentAI Pro",
                    "pricing": "$5,000 - $50,000/month",
                    "implementation_timeline": "2-4 weeks",
                    "certifications": ["ISO 27001"],
                }
            }
        ],
        [],
    )

    assert [item["product_name"] for item in result["primary_solutions"]] == ["DocumentAI Pro"]
    assert result["primary_solutions"][0]["pricing"] == "$5,000 - $50,000/month"
    assert result["primary_solutions"][0]["delivery_timeline"] == "2-4 weeks"
    assert result["primary_solutions"][0]["certifications"] == ["ISO 27001"]
    assert result["grounding_validation"]["rejected_solution_names"] == ["Made Up Platform"]


def test_solution_matching_schema_accepts_structured_catalog_pricing_and_evidence():
    result = SolutionMatchingOutput.model_validate({
        "primary_solutions": [{
            "product_name": "DocumentAI Pro",
            "coverage_percentage": 90,
            "features_matched": ["Layout-aware extraction"],
            "features_missing": ["Custom EHR connector"],
            "pricing": "$5,000 - $50,000/month",
            "delivery_timeline": "2-4 weeks",
            "certifications": ["ISO 27001"],
            "rationale": "Catalog feature coverage aligns with the PDF workflow.",
            "evidence": [{
                "source": "products.json: DocumentAI Pro",
                "detail": "Layout-aware extraction",
                "matched_requirement": "Extract PDF information",
            }],
            "limitations": "Custom EHR connector requires discovery.",
            "risks": [{"risk": "Variable source quality", "mitigation": "Validate samples"}],
        }],
        "complementary_services": [{
            "name": "Implementation & Integration",
            "reason": "Supports the custom EHR connector.",
            "evidence": "services.json: Implementation & Integration",
        }],
        "add_ons_recommended": [{
            "name": "DataVault Analytics",
            "reason": "Optional reporting add-on.",
        }],
        "requirement_coverage_matrix": {"Extract PDF information": "Full"},
        "gaps_and_workarounds": [{
            "gap": "Custom EHR connector",
            "workaround": "Scope an integration during discovery",
        }],
        "confidence_assessment": {"overall": "High", "reasoning": "Catalog-backed match"},
        "estimated_solution_value": {
            "breakdown": {
                "DocumentAI Pro": "$5,000 - $50,000/month",
                "DataVault Analytics (add-on)": "$96,000 - $900,000/year (optional)",
            },
            "notes": "Confirm final package after discovery.",
        },
        "grounding_validation": {"verified_solution_count": 1},
    })

    assert result.estimated_solution_value.breakdown["DataVault Analytics (add-on)"] == "$96,000 - $900,000/year (optional)"
    assert result.primary_solutions[0].evidence[0].source == "products.json: DocumentAI Pro"
    assert result.primary_solutions[0].limitations == ["Custom EHR connector requires discovery."]


def test_compact_rag_context_preserves_catalog_identity_and_metadata_for_grounding():
    result = _compact_rag_context(
        [
            {
                "product": {
                    "id": "prod-001",
                    "name": "DocumentAI Pro",
                    "description": "PDF extraction",
                    "pricing": "$5,000 - $50,000/month",
                    "implementation_timeline": "2-4 weeks",
                    "certifications": ["ISO 27001"],
                    "document": "products.json: DocumentAI Pro",
                }
            }
        ],
        [
            {
                "service": {
                    "id": "svc-001",
                    "name": "Implementation & Integration",
                    "description": "Integration services",
                    "pricing": "$50,000 - $500,000",
                    "support_hours": "24/7",
                    "document": "services.json: Implementation & Integration",
                }
            }
        ],
    )

    assert result["products"][0]["id"] == "prod-001"
    assert result["products"][0]["source"] == "products.json: DocumentAI Pro"
    assert result["services"][0]["id"] == "svc-001"
    assert result["services"][0]["source"] == "services.json: Implementation & Integration"


def test_grounding_replaces_calculated_breakdown_prices_with_catalog_prices():
    result = _ground_solutions(
        {
            "primary_solutions": [{"product_name": "DocumentAI Pro"}],
            "estimated_solution_value": {
                "breakdown": {
                    "DataVault Analytics (add-on)": "$96,000 - $900,000/year (optional)",
                }
            },
        },
        [{"product": {"name": "DocumentAI Pro", "pricing": "$5,000 - $50,000/month"}}],
        [{"service": {"name": "DataVault Analytics", "pricing": "$8,000 - $75,000/month"}}],
    )

    assert result["estimated_solution_value"]["breakdown"] == {
        "DataVault Analytics": "$8,000 - $75,000/month",
        "DocumentAI Pro": "$5,000 - $50,000/month",
    }
    assert result["grounding_validation"]["grounded_pricing_sources"] == [
        "DataVault Analytics",
        "DocumentAI Pro",
    ]
