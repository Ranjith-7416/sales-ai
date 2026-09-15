// Types for the application

export enum LeadStatus {
  Qualified = "Qualified",
  NeedsInfo = "Needs More Information",
  LowPriority = "Low Priority",
  Processing = "Processing",
}

export interface LeadInput {
  company_name?: string;
  contact_name?: string;
  email?: string;
  inquiry_text: string;
  industry?: string;
  company_size?: string;
  budget?: string;
  timeline?: string;
  additional_context?: string;
}

export interface Lead {
  id: string;
  lead_id?: string;
  company_name?: string;
  contact_name?: string;
  email?: string;
  inquiry_text: string;
  industry?: string;
  company_size?: string;
  budget?: string;
  timeline?: string;
  additional_context?: string;
  lead_status: LeadStatus | string;
  status: 'queued' | 'processing' | 'completed';
  current_stage?: string;
  stages_completed?: string[];
  composite_score?: number;
  fit_score?: number;
  missing_information?: string[];
  created_at: string;
  completed_at?: string;
  proposal_result?: any;
  research_result?: any;
  requirements_result?: any;
  qualification_result?: any;
  solution_matching_result?: any;
  reviewer_result?: any;
  result?: QualificationResultFull;
}

export interface ResearchResult {
  company_name: string;
  industry_vertical: string;
  company_size: string;
  location: string;
  business_model: string;
  key_products_services: string;
  market_position: string;
  recent_news: string[];
  concerns_flags?: string[];
  public_contact?: Record<string, string>;
}

export interface RequirementResult {
  functional_requirements: string[];
  non_functional_requirements: Record<string, unknown>;
  constraints: Record<string, unknown>;
  missing_information: string[];
  assumptions: string[];
  priority_mapping: {
    must_have: string[];
    nice_to_have: string[];
  };
}

export interface QualificationResult {
  lead_status: LeadStatus;
  composite_score: number;
  fit_score: number;
  fit_evidence: string;
  readiness_score: number;
  readiness_evidence: string;
  opportunity_score: number;
  opportunity_evidence: string;
  risk_score: number;
  risk_evidence: string;
  qualification_reasoning: string;
  score_drivers: [string, string][];
  follow_up_questions?: string[];
}

export interface SolutionMatch {
  product_name: string;
  coverage_percentage: number;
  features_matched: string[];
  features_missing: string[];
  pricing: CatalogPricing;
  delivery_timeline: string;
  certifications: string[];
  rationale?: string;
  evidence?: SolutionEvidence[];
  limitations?: string[];
  risks?: Array<string | { risk: string; mitigation?: string | string[] }>;
}

export interface PricingBreakdown {
  breakdown: Record<string, string>;
  total?: string;
  currency?: string;
  billing_period?: string;
  notes?: string | string[];
}

export type CatalogPricing = string | PricingBreakdown;

export interface SolutionEvidence {
  source?: string;
  detail?: string;
  [key: string]: unknown;
}

export interface SolutionMatchingResult {
  primary_solutions: SolutionMatch[];
  complementary_services: Record<string, string>[];
  add_ons_recommended: Record<string, string>[];
  requirement_coverage_matrix: Record<string, string>;
  gaps_and_workarounds: Record<string, string>[];
  confidence_assessment: Record<string, string>;
  estimated_solution_value: CatalogPricing;
}

export interface ProposalSection {
  title: string;
  content: string;
}

export interface ProposalResult {
  executive_summary: string;
  customer_requirements: string[];
  proposed_solution: string;
  implementation_roadmap: Record<string, unknown>[];
  total_implementation_timeline: string;
  pricing_proposal: Record<string, unknown>;
  support_service_levels: Record<string, string>;
  success_metrics: string[];
  next_steps: string[];
  sections: ProposalSection[];
}

export interface ReviewerResult {
  coverage_validation: Record<string, string>[];
  claim_verification: Record<string, string>[];
  unsupported_requirements: string[];
  missing_information: Record<string, string>[];
  risk_assessment: Record<string, string[]>;
  readiness_assessment: Record<string, unknown>;
  recommended_next_steps: string[];
  follow_up_questions: string[];
  escalation_path: Record<string, unknown>;
  approval_required: boolean;
  approver?: string;
}

export interface QualificationResultFull {
  research?: ResearchResult;
  requirements?: RequirementResult;
  requirements_result?: RequirementResult;
  qualification?: QualificationResult;
  qualification_result?: QualificationResult;
  solution_matching?: SolutionMatchingResult;
  proposal?: ProposalResult;
  reviewer?: ReviewerResult;
  results?: {
    research?: ResearchResult;
    requirements?: RequirementResult;
    qualification?: QualificationResult;
    solution_matching?: SolutionMatchingResult;
    proposal?: ProposalResult;
    reviewer?: ReviewerResult;
  };
}

export interface ScoringConfig {
  qualified_threshold: number;
  needs_info_threshold: number;
  fit_weight: number;
  readiness_weight: number;
  opportunity_weight: number;
  risk_weight: number;
  formula?: string;
}

export interface ProposalExportResult {
  lead_id: string;
  company_name: string;
  format: string;
  markdown: string;
  filename: string;
}

export interface KBProduct {
  id: string;
  name: string;
  category: string;
  description: string;
  features: string[];
  pricing: string;
  implementation_timeline?: string;
  certifications?: string[];
  uptime_sla?: string;
  support_level?: string;
  supported_formats?: string[];
}

export interface KBService {
  id: string;
  name: string;
  category: string;
  description: string;
  deliverables?: string[];
  pricing: string;
  delivery_timeline?: string;
  certifications?: string[];
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

