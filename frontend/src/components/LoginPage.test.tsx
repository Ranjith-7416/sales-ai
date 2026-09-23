import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from './LoginPage';

const { mockLogin, mockRegister, mockResetPassword } = vi.hoisted(() => ({
  mockLogin: vi.fn(),
  mockRegister: vi.fn(),
  mockResetPassword: vi.fn(),
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
    register: mockRegister,
    resetPassword: mockResetPassword,
    isAuthenticated: false,
    loading: false,
    user: null,
  }),
}));

describe('LoginPage and Simplified Forgot Password Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
  };

  it('renders login page by default with Sales AI branding and tabs', () => {
    renderComponent();
    expect(screen.getByRole('heading', { name: /Welcome to/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Sign In$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to Workspace/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Forgot password\?/i })).toBeInTheDocument();
  });

  it('switches to Forgot your password? view matching exact layout and removes OTP / Dev Code', () => {
    renderComponent();

    // Click "Forgot password?"
    const forgotLink = screen.getByRole('button', { name: /Forgot password\?/i });
    fireEvent.click(forgotLink);

    // Verify title
    expect(screen.getByRole('heading', { name: /Forgot your password\?/i })).toBeInTheDocument();

    // Verify fields
    expect(screen.getByText(/^New Password$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Confirm New Password$/i)).toBeInTheDocument();

    // Verify buttons
    expect(screen.getByRole('button', { name: /^Reset Password$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Back to Login$/i })).toBeInTheDocument();

    // Verify ZERO OTP, Dev Code, or Auto-fill exists
    expect(screen.queryByText(/Dev Code/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Auto-fill/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/6-Digit Verification Code/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Send Verification Code/i)).not.toBeInTheDocument();
  });

  it('toggles password visibility with eye icons', () => {
    renderComponent();
    fireEvent.click(screen.getByRole('button', { name: /Forgot password\?/i }));

    const inputs = screen.getAllByPlaceholderText('••••••••••••');
    const newPassInput = inputs[0] as HTMLInputElement;
    const confirmInput = inputs[1] as HTMLInputElement;

    expect(newPassInput.type).toBe('password');
    expect(confirmInput.type).toBe('password');

    // Click show password icons
    const showButtons = screen.getAllByTitle(/Show/i);
    fireEvent.click(showButtons[0]);
    expect(newPassInput.type).toBe('text');

    fireEvent.click(showButtons[1]);
    expect(confirmInput.type).toBe('text');
  });

  it('validates password mismatch and minimum 8 characters', async () => {
    renderComponent();

    // Switch to forgot password
    fireEvent.click(screen.getByRole('button', { name: /Forgot password\?/i }));

    const inputs = screen.getAllByPlaceholderText('••••••••••••');
    const newPassInput = inputs[0];
    const confirmInput = inputs[1];

    // Type 6 characters (too short)
    fireEvent.change(newPassInput, { target: { value: 'pass12' } });
    fireEvent.change(confirmInput, { target: { value: 'pass99' } });

    // Should indicate mismatch
    expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();

    // Attempt submit
    fireEvent.click(screen.getByRole('button', { name: /^Reset Password$/i }));

    // Should reject because < 8 chars or email missing
    await waitFor(() => {
      expect(mockResetPassword).not.toHaveBeenCalled();
    });
  });

  it('completes Login -> Forgot Password -> Reset Password -> Login flow seamlessly', async () => {
    mockResetPassword.mockResolvedValueOnce(undefined);
    renderComponent();

    // 1. Enter email on login screen
    const emailInput = screen.getByPlaceholderText('name@company.com');
    fireEvent.change(emailInput, { target: { value: 'sarah.connor@example.com' } });

    // 2. Click Forgot password?
    fireEvent.click(screen.getByRole('button', { name: /Forgot password\?/i }));
    expect(screen.getByRole('heading', { name: /Forgot your password\?/i })).toBeInTheDocument();

    // 3. Fill in matching 8+ character password
    const inputs = screen.getAllByPlaceholderText('••••••••••••');
    fireEvent.change(inputs[0], { target: { value: 'CalmOceanWater2026!' } });
    fireEvent.change(inputs[1], { target: { value: 'CalmOceanWater2026!' } });

    // Verify match indicator
    expect(screen.getByText(/Passwords match/i)).toBeInTheDocument();

    // 4. Click Reset Password
    fireEvent.click(screen.getByRole('button', { name: /^Reset Password$/i }));

    await waitFor(() => {
      expect(mockResetPassword).toHaveBeenCalledWith('sarah.connor@example.com', 'CalmOceanWater2026!');
    });

    expect(screen.getByText(/Password reset successfully/i)).toBeInTheDocument();

    // 5. Back to Login button works
    const backBtn = screen.getByRole('button', { name: /^Back to Login$/i });
    fireEvent.click(backBtn);
    expect(screen.getByRole('heading', { name: /Welcome to/i })).toBeInTheDocument();
  });
});
