import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Sparkles,
  Lock,
  Mail,
  Eye,
  EyeOff,
  Loader,
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  ArrowRight,
  User as UserIcon,
  KeyRound,
} from 'lucide-react';

type AuthMode = 'login' | 'register' | 'reset';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, resetPassword, isAuthenticated, loading: authLoading } = useAuth();

  const [mode, setMode] = useState<AuthMode>('login');
  
  // Form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isExistingAccount, setIsExistingAccount] = useState(false);

  const destination = (location.state as any)?.from?.pathname || '/';

  // If already logged in, redirect immediately
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      navigate(destination, { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate, destination]);

  const handleModeSwitch = (newMode: AuthMode) => {
    setMode(newMode);
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsExistingAccount(false);
    setConfirmPassword('');
  };

  // Real-time trimmed values
  const cleanPassword = password.replace(/[\u200B-\u200D\uFEFF\u00A0]/g, '').trim();
  const cleanConfirm = confirmPassword.replace(/[\u200B-\u200D\uFEFF\u00A0]/g, '').trim();
  const isMatch = cleanPassword.length > 0 && cleanPassword === cleanConfirm;
  const isMismatch = cleanConfirm.length > 0 && cleanPassword !== cleanConfirm;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsExistingAccount(false);

    const cleanEmail = email.trim().toLowerCase();

    if (!cleanEmail || !cleanPassword) {
      setErrorMessage('Please provide both email and password.');
      return;
    }

    if (mode === 'register') {
      const cleanName = name.trim();
      if (!cleanName) {
        setErrorMessage('Please enter your full name.');
        return;
      }
      if (cleanPassword.length < 6) {
        setErrorMessage('Password must be at least 6 characters long.');
        return;
      }
      if (cleanPassword !== cleanConfirm) {
        setErrorMessage(
          `Passwords do not match. ("Create Password" has ${cleanPassword.length} characters, "Confirm Password" has ${cleanConfirm.length} characters. Please check for spelling differences).`
        );
        return;
      }

      setSubmitting(true);
      try {
        await register(cleanName, cleanEmail, cleanPassword);
        setSuccessMessage('Account created successfully! Entering workspace...');
        setTimeout(() => {
          navigate(destination, { replace: true });
        }, 800);
      } catch (err: any) {
        const msg =
          err.response?.data?.detail ||
          err.message ||
          'Failed to create account. Please try again.';
        if (typeof msg === 'string' && msg.toLowerCase().includes('already exists')) {
          setIsExistingAccount(true);
        }
        setErrorMessage(msg);
      } finally {
        setSubmitting(false);
      }
    } else if (mode === 'reset') {
      // Password reset mode
      if (cleanPassword.length < 6) {
        setErrorMessage('New password must be at least 6 characters long.');
        return;
      }
      if (cleanPassword !== cleanConfirm) {
        setErrorMessage(
          `Passwords do not match (${cleanPassword.length} chars vs ${cleanConfirm.length} chars). Please re-enter.`
        );
        return;
      }

      setSubmitting(true);
      try {
        await resetPassword(cleanEmail, cleanPassword);
        setSuccessMessage('Password updated successfully! Entering workspace...');
        setTimeout(() => {
          navigate(destination, { replace: true });
        }, 800);
      } catch (err: any) {
        const msg =
          err.response?.data?.detail ||
          err.message ||
          'Failed to reset password. Please verify your email.';
        setErrorMessage(msg);
      } finally {
        setSubmitting(false);
      }
    } else {
      // Login mode
      setSubmitting(true);
      try {
        await login(cleanEmail, cleanPassword);
        navigate(destination, { replace: true });
      } catch (err: any) {
        let msg =
          err.response?.data?.detail ||
          err.message ||
          'Invalid email or password. Please try again.';
        if (err.code === 'ECONNABORTED' || err.message?.toLowerCase().includes('timeout')) {
          msg = 'Connection timed out. The backend service may be waking up from cold start; please try again.';
        }
        setErrorMessage(msg);
      } finally {
        setSubmitting(false);
      }
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-10 px-4 sm:px-6 relative">
      {/* Background Ambient Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full relative z-10">
        {/* Card */}
        <div className="glass-panel border border-white/[0.12] bg-slate-900/90 rounded-3xl p-8 sm:p-9 shadow-2xl backdrop-blur-2xl space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 p-[1px] shadow-lg shadow-indigo-500/30 mb-2">
              <div className="w-full h-full bg-slate-950 rounded-2xl flex items-center justify-center">
                <Sparkles size={24} className="text-cyan-400" />
              </div>
            </div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Welcome to <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">Sales AI</span>
            </h1>
            <p className="text-xs text-slate-400">
              {mode === 'login'
                ? 'Sign in to access your enterprise deal intelligence workspace'
                : mode === 'register'
                ? 'Create an account to start qualifying leads and closing deals'
                : 'Reset your account password to regain workspace access'}
            </p>
          </div>

          {/* Mode Tabs */}
          {mode !== 'reset' ? (
            <div className="p-1 bg-slate-950/80 border border-white/[0.08] rounded-2xl flex items-center gap-1">
              <button
                type="button"
                onClick={() => handleModeSwitch('login')}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer ${
                  mode === 'login'
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => handleModeSwitch('register')}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer ${
                  mode === 'register'
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                Create Account
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-semibold text-indigo-400 flex items-center gap-1.5">
                <KeyRound size={14} /> Password Reset
              </span>
              <button
                type="button"
                onClick={() => handleModeSwitch('login')}
                className="text-xs text-slate-400 hover:text-white transition cursor-pointer"
              >
                Back to Sign In
              </button>
            </div>
          )}

          {/* Feedback Notices */}
          {errorMessage && (
            <div className="p-3 bg-rose-950/70 border border-rose-500/40 text-rose-200 rounded-xl text-xs space-y-2 animate-in fade-in">
              <div className="flex items-start gap-2.5">
                <AlertCircle size={16} className="text-rose-400 shrink-0 mt-0.5" />
                <div className="leading-snug">{errorMessage}</div>
              </div>
              {isExistingAccount && (
                <div className="pt-1 border-t border-rose-500/20 flex items-center justify-end">
                  <button
                    type="button"
                    onClick={() => handleModeSwitch('login')}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow transition cursor-pointer"
                  >
                    Sign In with this email <ArrowRight size={13} />
                  </button>
                </div>
              )}
            </div>
          )}

          {successMessage && (
            <div className="p-3 bg-emerald-950/70 border border-emerald-500/40 text-emerald-200 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
              <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
              <div>{successMessage}</div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <UserIcon size={15} />
                  </div>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Alex Morgan"
                    autoComplete="name"
                    autoCapitalize="words"
                    autoCorrect="off"
                    spellCheck={false}
                    required={mode === 'register'}
                    className="w-full bg-slate-800/80 border border-white/[0.1] rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Work Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Mail size={15} />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  autoComplete="email"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                  required
                  className="w-full bg-slate-800/80 border border-white/[0.1] rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  {mode === 'register' ? 'Create Password' : mode === 'reset' ? 'New Password' : 'Password'}
                </label>
                {mode === 'login' && (
                  <button
                    type="button"
                    onClick={() => handleModeSwitch('reset')}
                    className="text-[11px] text-cyan-400 hover:text-cyan-300 transition cursor-pointer"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock size={15} />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  autoComplete={mode === 'register' || mode === 'reset' ? 'new-password' : 'current-password'}
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                  required
                  className={`w-full bg-slate-800/80 border border-white/[0.1] rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition ${
                    showPassword ? 'font-mono tracking-wider' : ''
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition cursor-pointer"
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {(mode === 'register' || mode === 'reset') && (
                <span className="text-[10px] text-slate-400 mt-1 block">
                  Must be at least 6 characters {password.length > 0 && `(${password.length} entered)`}
                </span>
              )}
            </div>

            {(mode === 'register' || mode === 'reset') && (
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <Lock size={15} />
                  </div>
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    autoComplete="new-password"
                    autoCapitalize="none"
                    autoCorrect="off"
                    spellCheck={false}
                    required={mode === 'register' || mode === 'reset'}
                    className={`w-full bg-slate-800/80 border rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none transition ${
                      showConfirmPassword ? 'font-mono tracking-wider' : ''
                    } ${
                      isMatch
                        ? 'border-emerald-500/50 focus:border-emerald-500'
                        : isMismatch
                        ? 'border-amber-500/50 focus:border-amber-500'
                        : 'border-white/[0.1] focus:border-indigo-500'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition cursor-pointer"
                    title={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  >
                    {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>

                {/* Real-time Match Indicator */}
                {confirmPassword.length > 0 && (
                  <div className="mt-1.5 flex items-center gap-1.5 text-[11px]">
                    {isMatch ? (
                      <span className="text-emerald-400 flex items-center gap-1 font-medium">
                        <CheckCircle2 size={13} /> Passwords match ({cleanPassword.length} characters)
                      </span>
                    ) : (
                      <span className="text-amber-400 flex items-center gap-1 font-medium">
                        <AlertCircle size={13} />
                        Passwords do not match ({cleanPassword.length} chars in Create vs {cleanConfirm.length} chars in Confirm)
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-2 py-3 bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition cursor-pointer active:scale-98 shadow-lg shadow-indigo-500/25 tracking-wide"
            >
              {submitting ? (
                <>
                  <Loader size={16} className="animate-spin text-white" />
                  {mode === 'register'
                    ? 'Creating Account...'
                    : mode === 'reset'
                    ? 'Updating Password...'
                    : 'Authenticating...'}
                </>
              ) : (
                <>
                  {mode === 'register'
                    ? 'Create Account & Sign In'
                    : mode === 'reset'
                    ? 'Update Password & Sign In'
                    : 'Sign In to Workspace'}
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          </form>

          {/* Mode Switch Footer */}
          <div className="text-center pt-2">
            {mode === 'login' ? (
              <p className="text-xs text-slate-400">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => handleModeSwitch('register')}
                  className="text-cyan-400 hover:text-cyan-300 font-semibold cursor-pointer underline-offset-4 hover:underline"
                >
                  Create one here
                </button>
              </p>
            ) : mode === 'register' ? (
              <p className="text-xs text-slate-400">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => handleModeSwitch('login')}
                  className="text-cyan-400 hover:text-cyan-300 font-semibold cursor-pointer underline-offset-4 hover:underline"
                >
                  Sign in here
                </button>
              </p>
            ) : (
              <p className="text-xs text-slate-400">
                Remember your password?{' '}
                <button
                  type="button"
                  onClick={() => handleModeSwitch('login')}
                  className="text-cyan-400 hover:text-cyan-300 font-semibold cursor-pointer underline-offset-4 hover:underline"
                >
                  Back to Sign In
                </button>
              </p>
            )}
          </div>

          {/* Security Features Callout */}
          <div className="pt-4 border-t border-white/[0.06] flex items-center justify-center gap-4 text-[11px] text-slate-400">
            <span className="flex items-center gap-1">
              <ShieldCheck size={13} className="text-emerald-400" /> Bcrypt Hashed
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <ShieldCheck size={13} className="text-indigo-400" /> JWT Encrypted
            </span>
            <span>•</span>
            <span>PostgreSQL CRM</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;


