import { fireEvent, render, screen, waitFor, act } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ScoringConfigModal from './ScoringConfigModal';

const { getScoringConfig, updateScoringConfig } = vi.hoisted(() => ({
  getScoringConfig: vi.fn(),
  updateScoringConfig: vi.fn(),
}));

vi.mock('../hooks/useApi', () => ({
  useApi: () => ({
    getScoringConfig,
    updateScoringConfig,
  }),
}));

describe('ScoringConfigModal', () => {
  const defaultMockConfig = {
    qualified_threshold: 75,
    needs_info_threshold: 50,
    fit_weight: 0.25,
    readiness_weight: 0.25,
    opportunity_weight: 0.30,
    risk_weight: 0.20,
    formula: '',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    getScoringConfig.mockResolvedValue(defaultMockConfig);
    updateScoringConfig.mockResolvedValue({ status: 'success' });
  });

  it('renders with Apply Configuration button enabled and not stuck on Applying', async () => {
    const handleClose = vi.fn();
    await act(async () => {
      render(<ScoringConfigModal isOpen={true} onClose={handleClose} />);
    });

    expect(screen.getByRole('heading', { name: /Qualification Engine Tuning/i })).toBeInTheDocument();

    const applyButton = screen.getByRole('button', { name: /Apply Configuration/i });
    expect(applyButton).toBeInTheDocument();
    expect(applyButton).not.toBeDisabled();
    expect(screen.queryByText(/Applying\.\.\./i)).not.toBeInTheDocument();
  });

  it('saves configuration on click, shows Applied! feedback, and closes cleanly', async () => {
    const handleClose = vi.fn();
    await act(async () => {
      render(<ScoringConfigModal isOpen={true} onClose={handleClose} />);
    });

    const applyButton = screen.getByRole('button', { name: /Apply Configuration/i });
    await act(async () => {
      fireEvent.click(applyButton);
    });

    expect(updateScoringConfig).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      expect(screen.getByText(/Applied!/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(handleClose).toHaveBeenCalled();
    }, { timeout: 1500 });
  });

  it('resets state when reopened so it is never stuck on Applying', async () => {
    const handleClose = vi.fn();
    let renderResult: any;
    await act(async () => {
      renderResult = render(<ScoringConfigModal isOpen={true} onClose={handleClose} />);
    });

    const applyButton = screen.getByRole('button', { name: /Apply Configuration/i });
    await act(async () => {
      fireEvent.click(applyButton);
    });

    await waitFor(() => {
      expect(updateScoringConfig).toHaveBeenCalledTimes(1);
    });

    // Close modal
    await act(async () => {
      renderResult.rerender(<ScoringConfigModal isOpen={false} onClose={handleClose} />);
    });
    expect(screen.queryByRole('heading', { name: /Qualification Engine Tuning/i })).not.toBeInTheDocument();

    // Reopen modal
    await act(async () => {
      renderResult.rerender(<ScoringConfigModal isOpen={true} onClose={handleClose} />);
    });
    const reopenedButton = screen.getByRole('button', { name: /Apply Configuration/i });
    expect(reopenedButton).toBeInTheDocument();
    expect(reopenedButton).not.toBeDisabled();
    expect(screen.queryByText(/Applying\.\.\./i)).not.toBeInTheDocument();
  });
});
