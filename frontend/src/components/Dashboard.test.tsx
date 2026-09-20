import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Dashboard from './Dashboard';
import { LeadStatus } from '../types';

const { getLead } = vi.hoisted(() => ({
  getLead: vi.fn(),
}));

vi.mock('../hooks/useApi', () => ({
  useApi: () => ({
    getLead,
    updateLead: vi.fn(),
  }),
}));

function renderDashboard() {
  return render(
    <MemoryRouter
      initialEntries={['/lead/lead-1']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/lead/:leadId" element={<Dashboard />} />
      </Routes>
    </MemoryRouter>,
  );
}

const completedLead = {
  id: 'lead-1',
  company_name: 'MediTech Solutions',
  inquiry_text: 'Process healthcare PDFs.',
  lead_status: LeadStatus.Qualified,
  status: 'completed' as const,
  created_at: '2026-09-13T00:00:00Z',
  result: {
    qualification: {
      lead_status: LeadStatus.Qualified,
      composite_score: 84,
      fit_score: 82,
      readiness_score: 86,
      opportunity_score: 85,
      risk_score: 20,
      fit_evidence: 'Healthcare fit',
      readiness_evidence: 'Approved project',
      opportunity_evidence: 'Document volume',
      risk_evidence: 'Managed rollout',
      qualification_reasoning: 'Strong fit with clear requirements.',
      score_drivers: [['PDF volume', 'High value']],
    },
    requirements: {
      functional_requirements: ['Extract PDF information'],
      non_functional_requirements: {},
      constraints: {},
      missing_information: [],
      assumptions: [],
      priority_mapping: { must_have: [], nice_to_have: [] },
    },
    solution_matching: {
      primary_solutions: [{
        product_name: 'DocumentAI Pro',
        coverage_percentage: 90,
        features_matched: ['OCR'],
        features_missing: [],
        pricing: '$5,000 - $50,000/month',
        delivery_timeline: '2-4 weeks',
        certifications: ['ISO 27001'],
      }],
      complementary_services: [],
      add_ons_recommended: [],
      requirement_coverage_matrix: { 'Extract PDF information': 'Full' },
      gaps_and_workarounds: [],
      confidence_assessment: { overall: 'High' },
      estimated_solution_value: '$5,000/month',
    },
    proposal: {
      executive_summary: 'DocumentAI Pro will process the customer PDFs.',
      customer_requirements: ['Extract PDF information'],
      proposed_solution: 'DocumentAI Pro',
      implementation_roadmap: [],
      total_implementation_timeline: '2-4 weeks',
      pricing_proposal: { base_product: '$5,000/month' },
      support_service_levels: {},
      success_metrics: [],
      next_steps: [],
      sections: [],
    },
    reviewer: {
      coverage_validation: [],
      claim_verification: [],
      unsupported_requirements: [],
      missing_information: [],
      risk_assessment: {},
      readiness_assessment: { ready_to_send: false },
      recommended_next_steps: ['Confirm implementation scope'],
      follow_up_questions: ['Which EHR integration is required?'],
      escalation_path: {},
      approval_required: true,
    },
  },
};

describe('Dashboard workflow rendering', () => {
  beforeEach(() => {
    getLead.mockReset();
  });

  it('renders score, status, solution, proposal, and reviewer warning', async () => {
    getLead.mockResolvedValue(completedLead);
    renderDashboard();

    expect(await screen.findByText(/Qualified/i)).toBeInTheDocument();
    expect(screen.getAllByText('84').length).toBeGreaterThanOrEqual(1);

    fireEvent.click(screen.getByRole('button', { name: /Solutions/i }));
    expect(screen.getByText('DocumentAI Pro')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Executive Proposal' }));
    expect(screen.getByText('DocumentAI Pro will process the customer PDFs.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'QA & Review' }));
    expect(await screen.findByText(/Which EHR integration is required\?/)).toBeInTheDocument();
  });

  it('renders the needs-more-information state without a numeric score', async () => {
    getLead.mockResolvedValue({
      ...completedLead,
      lead_status: LeadStatus.NeedsInfo,
      result: {
        qualification: {
          ...completedLead.result.qualification,
          lead_status: LeadStatus.NeedsInfo,
          composite_score: 0,
        },
        requirements: {
          ...completedLead.result.requirements,
          missing_information: ['Budget range'],
        },
      },
    });
    renderDashboard();

    expect(await screen.findByText('Needs More Information')).toBeInTheDocument();
    expect(screen.getByText('Not scored')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Budget range')).toBeInTheDocument());
  });
});
