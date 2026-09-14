
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewerMissingInformation(BaseModel):
    info: str
    impact: str
    to_ask: Union[str, List[str]] = ""

class ResearchOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    company_name: str = "Unknown"
    industry_vertical: str = "Unknown"
    company_size: str = "Unknown"
    location: str = "Unknown"
    business_model: str = "Unknown"
    key_products_services: str = "Unknown"
    market_position: str = "Unknown"
    recent_news: List[str] = Field(default_factory=list)
    concerns_flags: Optional[Union[str, List[str]]] = None
    public_contact: Dict[str, str] = Field(default_factory=dict)


class RequirementOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    functional_requirements: List[str] = Field(default_factory=list)
    non_functional_requirements: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    missing_information: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    priority_mapping: Dict[str, List[str]] = Field(default_factory=dict)


class QualificationOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    lead_status: str = "Needs More Information"
    composite_score: Optional[float] = None
    fit_score: float = 0
    fit_evidence: str = ""
    readiness_score: float = 0
    readiness_evidence: str = ""
    opportunity_score: float = 0
    opportunity_evidence: str = ""
    risk_score: float = 0
    risk_evidence: str = ""
    qualification_reasoning: str = ""
    score_drivers: List[Any] = Field(default_factory=list)
    follow_up_questions: Optional[List[str]] = None


class PricingBreakdown(BaseModel):
    model_config = ConfigDict(extra="allow")

    breakdown: Dict[str, str] = Field(default_factory=dict)
    total: Optional[str] = None
    currency: Optional[str] = None
    billing_period: Optional[str] = None
    notes: Optional[Union[str, List[str]]] = None


CatalogPricing = Union[str, PricingBreakdown]


class SolutionEvidence(BaseModel):
    source: str
    detail: str
    matched_requirement: Optional[str] = None


class SolutionRisk(BaseModel):
    risk: str
    mitigation: Optional[Union[str, List[str]]] = None


class SolutionMatch(BaseModel):
    model_config = ConfigDict(extra="allow")

    product_name: str
    coverage_percentage: float = 0
    features_matched: List[str] = Field(default_factory=list)
    features_missing: List[str] = Field(default_factory=list)
    pricing: CatalogPricing = "Not listed in knowledge base"
    delivery_timeline: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)
    rationale: Optional[str] = None
    evidence: List[SolutionEvidence] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    risks: List[SolutionRisk] = Field(default_factory=list)

    @field_validator("limitations", mode="before")
    @classmethod
    def normalize_limitations(cls, value: Any) -> List[str]:
        if value is None:
            return []
        return [value] if isinstance(value, str) else value


class NamedRecommendation(BaseModel):
    name: str
    reason: str = ""
    evidence: Optional[Union[str, List[str]]] = None


class GapAndWorkaround(BaseModel):
    gap: str
    workaround: str


class ConfidenceAssessment(BaseModel):
    overall: str = "Low"
    reasoning: Optional[Union[str, List[str]]] = None


class SolutionMatchingOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    primary_solutions: List[SolutionMatch] = Field(default_factory=list)
    complementary_services: List[NamedRecommendation] = Field(default_factory=list)
    add_ons_recommended: List[NamedRecommendation] = Field(default_factory=list)
    requirement_coverage_matrix: Dict[str, str] = Field(default_factory=dict)
    gaps_and_workarounds: List[GapAndWorkaround] = Field(default_factory=list)
    confidence_assessment: ConfidenceAssessment = Field(default_factory=ConfidenceAssessment)
    estimated_solution_value: CatalogPricing = "Not listed in knowledge base"
    grounding_validation: Dict[str, Any] = Field(default_factory=dict)


class ProposalSection(BaseModel):
    title: str
    content: str


class ProposalOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    executive_summary: str = ""
    customer_requirements: List[str] = Field(default_factory=list)
    proposed_solution: str = ""
    implementation_roadmap: List[Dict[str, Any]] = Field(default_factory=list)
    total_implementation_timeline: Optional[str] = None
    pricing_proposal: Dict[str, Any] = Field(default_factory=dict)
    support_service_levels: Dict[str, Any] = Field(default_factory=dict)
    success_metrics: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    sections: List[ProposalSection] = Field(default_factory=list)
    proposal_status: Optional[str] = None
    grounding_validation: Dict[str, Any] = Field(default_factory=dict)


class ReviewerCoverageItem(BaseModel):
    requirement: str
    addressed: bool
    where: Union[str, List[str]]

    @field_validator("addressed", mode="before")
    @classmethod
    def normalize_addressed(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"yes", "true", "full", "addressed"}:
                return True
            if normalized in {"no", "false", "none", "unaddressed", "partial"}:
                return False
        raise ValueError("addressed must be a boolean or a recognized yes/no value")


class ReviewerClaimItem(BaseModel):
    claim: str
    verified: bool
    source: Union[str, List[str]]

    @field_validator("verified", mode="before")
    @classmethod
    def normalize_verified(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"yes", "true", "verified", "supported"}:
                return True
            if normalized in {"no", "false", "unverified", "unsupported"}:
                return False
        raise ValueError("verified must be a boolean or a recognized yes/no value")


class ReviewerMissingInformation(BaseModel):
    info: str
    impact: str
    to_ask: Union[str, List[str]] = ""


class ReviewerRiskDetail(BaseModel):
    risk: str
    mitigation: Optional[Union[str, List[str]]] = None


class ReviewerRiskAssessment(BaseModel):
    technical_risks: List[Union[str, ReviewerRiskDetail]] = Field(default_factory=list)
    commercial_risks: List[Union[str, ReviewerRiskDetail]] = Field(default_factory=list)
    organizational_risks: List[Union[str, ReviewerRiskDetail]] = Field(default_factory=list)


class ReviewerReadinessAssessment(BaseModel):
    ready_to_send: bool = False
    reason: Union[str, List[str]] = ""


class ReviewerEscalationPath(BaseModel):
    approval_required: bool = False
    approver: Optional[str] = None


class ReviewerOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    coverage_validation: List[ReviewerCoverageItem] = Field(default_factory=list)
    claim_verification: List[ReviewerClaimItem] = Field(default_factory=list)
    unsupported_requirements: List[str] = Field(default_factory=list)
    missing_information: List[ReviewerMissingInformation] = Field(default_factory=list)
    risk_assessment: ReviewerRiskAssessment = Field(default_factory=ReviewerRiskAssessment)
    readiness_assessment: ReviewerReadinessAssessment = Field(default_factory=ReviewerReadinessAssessment)
    recommended_next_steps: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    escalation_path: ReviewerEscalationPath = Field(default_factory=ReviewerEscalationPath)
    approval_required: bool = False
    approver: Optional[str] = None


class LeadInputSchema(BaseModel):
    company_name: Optional[str] = None
    inquiry_text: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    additional_context: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None


class LeadResponse(BaseModel):
    lead_id: str
    lead_status: Optional[str] = None
    composite_score: Optional[float] = None
    result: Optional[Dict[str, Any]] = None


class LeadQualificationResult(BaseModel):
    lead_id: str
    lead_status: str
    composite_score: Optional[float] = None
    research_result: Optional[ResearchOutput] = None
    requirements_result: Optional[RequirementOutput] = None
    qualification_result: Optional[QualificationOutput] = None
    solution_matching_result: Optional[SolutionMatchingOutput] = None
    proposal_result: Optional[ProposalOutput] = None
    reviewer_result: Optional[ReviewerOutput] = None
    stages_completed: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class ReviewerRiskDetail(BaseModel):
    risk: str
    mitigation: Optional[Union[str, List[str]]] = None


class ReviewerRiskAssessment(BaseModel):
    technical_risks: List[Union[str, ReviewerRiskDetail]] = Field(default_factory=list)
    commercial_risks: List[Union[str, ReviewerRiskDetail]] = Field(default_factory=list)
    organizational_risks: List[Union[str, ReviewerRiskDetail]] = Field(default_factory=list)


class ReviewerReadinessAssessment(BaseModel):
    ready_to_send: bool = False
    reason: Union[str, List[str]] = ""


class ReviewerEscalationPath(BaseModel):
    approval_required: bool = False
    approver: Optional[str] = None


class ReviewerOutput(BaseModel):
    """Structured final QA result from the reviewer agent."""

    coverage_validation: List[ReviewerCoverageItem] = Field(default_factory=list)
    claim_verification: List[ReviewerClaimItem] = Field(default_factory=list)
    unsupported_requirements: List[str] = Field(default_factory=list)
    missing_information: List[ReviewerMissingInformation] = Field(default_factory=list)
    risk_assessment: ReviewerRiskAssessment = Field(default_factory=ReviewerRiskAssessment)
    readiness_assessment: ReviewerReadinessAssessment = Field(default_factory=ReviewerReadinessAssessment)
    recommended_next_steps: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    escalation_path: ReviewerEscalationPath = Field(default_factory=ReviewerEscalationPath)
    approval_required: bool = False
    approver: Optional[str] = None


class LeadQualificationResult(BaseModel):
    lead_id: str
    lead_status: str
    composite_score: Optional[float] = None
    research_result: Optional[ResearchOutput] = None
    requirements_result: Optional[RequirementOutput] = None
    qualification_result: Optional[QualificationOutput] = None
    solution_matching_result: Optional[SolutionMatchingOutput] = None
    proposal_result: Optional[ProposalOutput] = None
    reviewer_result: Optional[ReviewerOutput] = None
    stages_completed: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)















