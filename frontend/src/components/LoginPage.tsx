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
} from 'lucide-react';

type AuthMode = 'login' | 'register' | 'reset';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, resetPassword, isAuthenticated, loading: authLoading, user } = useAuth();

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

  // If already logged in, redirect to workspace
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
    setPassword('');
    setConfirmPassword('');
    setShowPassword(false);
    setShowConfirmPassword(false);
  };

  // Real-time sanitized values
  const cleanPassword = password.replace(/[\u200B-\u200D\uFEFF\u00A0]/g, '').trim();
  const cleanConfirm = confirmPassword.replace(/[\u200B-\u200D\uFEFF\u00A0]/g, '').trim();
  const isMatch = cleanPassword.length >= 8 && cleanPassword === cleanConfirm;
  const isMismatch = cleanConfirm.length > 0 && cleanPassword !== cleanConfirm;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsExistingAccount(false);

    const cleanEmail = (email || user?.email || '').trim().toLowerCase();

    // 1. FORGOT PASSWORD / RESET MODE
    if (mode === 'reset') {
      if (!cleanEmail) {
        setErrorMessage('Please enter your work email address.');
        return;
      }
      if (cleanPassword.length < 8) {
        setErrorMessage('New password must be at least 8 characters long.');
        return;
      }
      if (cleanPassword !== cleanConfirm) {
        setErrorMessage('New Password and Confirm New Password must match.');
        return;
      }

      setSubmitting(true);
      try {
        await resetPassword(cleanEmail, cleanPassword);
        setSuccessMessage('Password reset successfully! Please sign in with your new password.');
        setPassword('');
        setConfirmPassword('');
        setTimeout(() => {
          setMode('login');
        }, 1200);
      } catch (err: any) {
        const msg =
          err.response?.data?.detail ||
          err.message ||
          'Failed to reset password. Please check your account email and try again.';
        setErrorMessage(msg);
      } finally {
        setSubmitting(false);
      }
      return;
    }

    // 2. REGISTER MODE
    if (mode === 'register') {
      const cleanName = name.trim();
      if (!cleanName) {
        setErrorMessage('Please enter your full name.');
        return;
      }
      if (!cleanEmail) {
        setErrorMessage('Please provide your work email.');
        return;
      }
      if (cleanPassword.length < 8) {
        setErrorMessage('Password must be at least 8 characters long.');
        return;
      }
      if (cleanPassword !== cleanConfirm) {
        setErrorMessage('Passwords do not match. Please verify your password confirmation.');
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
      return;
    }

    // 3. LOGIN MODE
    if (mode === 'login') {
      if (!cleanEmail) {
        setErrorMessage('Please provide your work email.');
        return;
      }
      if (!cleanPassword) {
        setErrorMessage('Please enter your password.');
        return;
      }

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
          msg = 'Connection timed out. The backend service may be waking up; please try again.';
        }
        setErrorMessage(msg);
      } finally {
        setSubmitting(false);
      }
    }
  };

  return (
    <div className="relative min-h-[85vh] flex items-center justify-center py-10 px-4 sm:px-6">
      {/* Static Calm Water Background - GPU-accelerated static CSS radial gradients, zero heavy blur filters */}
      <div
        className="fixed inset-0 pointer-events-none overflow-hidden z-0"
        style={{
          background: `
            radial-gradient(circle at 12% 15%, rgba(8, 145, 178, 0.16) 0%, transparent 45%),
            radial-gradient(circle at 88% 85%, rgba(37, 99, 235, 0.18) 0%, transparent 45%),
            radial-gradient(circle at 50% 50%, rgba(20, 184, 166, 0.08) 0%, transparent 55%),
            linear-gradient(to bottom, #030d1a, #05182e, #020b16)
          `,
          transform: 'translateZ(0)',
          contain: 'strict',
        }}
      >
        {/* Static Water Waves (Pure static SVG shapes) */}
        <svg
          className="absolute bottom-0 left-0 w-full h-[320px] text-cyan-950/30"
          viewBox="0 0 1440 320"
          fill="none"
          preserveAspectRatio="none"
          style={{ transform: 'translateZ(0)' }}
        >
          <path
            fill="currentColor"
            fillOpacity="0.4"
            d="M0,192L48,197.3C96,203,192,213,288,202.7C384,192,480,160,576,165.3C672,171,768,213,864,224C960,235,1056,213,1152,192C1248,171,1344,149,1392,138.7L1440,128L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
          />
          <path
            fill="currentColor"
            fillOpacity="0.7"
            d="M0,256L48,245.3C96,235,192,213,288,218.7C384,224,480,256,576,256C672,256,768,224,864,208C960,192,1056,192,1152,202.7C1248,213,1344,235,1392,245.3L1440,256L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
          />
        </svg>
      </div>

      {/* Main Authentication Container */}
      <div className="max-w-md w-full relative z-10">
        {/* Modern Glassmorphism Card */}
        <div
          className="bg-[#091b30]/90 backdrop-blur-md border border-cyan-500/25 rounded-3xl p-7 sm:p-9 shadow-2xl shadow-cyan-950/60 space-y-6"
          style={{ transform: 'translateZ(0)' }}
        >

          {/* Header Section */}
          {mode === 'reset' ? (
            <div className="text-center space-y-2">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 via-sky-500 to-blue-600 p-[1px] shadow-lg shadow-cyan-500/25 mb-1">
                <div className="w-full h-full bg-[#05162a] rounded-2xl flex items-center justify-center">
                  <Lock size={22} className="text-cyan-400" />
                </div>
              </div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Forgot your password?
              </h1>
              <p className="text-xs text-slate-300">
                Enter your work email and choose a new password
              </p>
            </div>
          ) : (
            <div className="text-center space-y-2">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 via-sky-500 to-blue-600 p-[1px] shadow-lg shadow-cyan-500/25 mb-1">
                <div className="w-full h-full bg-[#05162a] rounded-2xl flex items-center justify-center">
                  <Sparkles size={24} className="text-cyan-300" />
                </div>
              </div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Welcome to <span className="bg-gradient-to-r from-cyan-400 to-sky-400 bg-clip-text text-transparent">Sales AI</span>
              </h1>
              <p className="text-xs text-slate-300">
                {mode === 'login'
                  ? 'Sign in to access your enterprise deal intelligence workspace'
                  : 'Create an account to start qualifying leads and closing deals'}
              </p>
            </div>
          )}

          {/* Mode Switch Tabs (Shown for Login / Register) */}
          {mode !== 'reset' && (
            <div className="p-1 bg-[#051426]/90 border border-cyan-500/20 rounded-2xl flex items-center gap-1">
              <button
                type="button"
                onClick={() => handleModeSwitch('login')}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer ${
                  mode === 'login'
                    ? 'bg-gradient-to-r from-cyan-600 via-sky-600 to-blue-600 text-white shadow-md shadow-cyan-900/30'
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
                    ? 'bg-gradient-to-r from-cyan-600 via-sky-600 to-blue-600 text-white shadow-md shadow-cyan-900/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                Create Account
              </button>
            </div>
          )}

          {/* Feedback Notices */}
          {errorMessage && (
            <div className="p-3 bg-rose-950/70 border border-rose-500/40 text-rose-200 rounded-xl text-xs space-y-2">
              <div className="flex items-start gap-2.5">
                <AlertCircle size={16} className="text-rose-400 shrink-0 mt-0.5" />
                <div className="leading-snug">{errorMessage}</div>
              </div>
              {isExistingAccount && (
                <div className="pt-1 border-t border-rose-500/20 flex items-center justify-end">
                  <button
                    type="button"
                    onClick={() => handleModeSwitch('login')}
                    className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow transition cursor-pointer"
                  >
                    Sign In with this email <ArrowRight size={13} />
                  </button>
                </div>
              )}
            </div>
          )}

          {successMessage && (
            <div className="p-3 bg-emerald-950/70 border border-emerald-500/40 text-emerald-200 rounded-xl text-xs flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
              <div>{successMessage}</div>
            </div>
          )}

          {/* FORGOT PASSWORD FORM */}
          {mode === 'reset' ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Work Email */}
              <div>
                <label className="text-xs font-semibold text-slate-200 block mb-1.5">
                  Work Email
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
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
                    className="w-full bg-[#061527]/90 border border-cyan-500/30 rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
              </div>

              {/* New Password */}
              <div>
                <label className="text-xs font-semibold text-slate-200 block mb-1.5">
                  New Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Lock size={15} />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    autoComplete="new-password"
                    autoCapitalize="none"
                    autoCorrect="off"
                    spellCheck={false}
                    required
                    className={`w-full bg-[#061527]/90 border rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none transition ${
                      showPassword ? 'font-mono tracking-wider' : ''
                    } ${
                      cleanPassword.length > 0 && cleanPassword.length < 8
                        ? 'border-amber-500/50 focus:border-amber-400 focus:ring-1 focus:ring-amber-400'
                        : 'border-cyan-500/30 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-cyan-300 transition cursor-pointer"
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                <span className="text-[10px] text-slate-400 mt-1 block">
                  Must be at least 8 characters {cleanPassword.length > 0 && `(${cleanPassword.length} entered)`}
                </span>
              </div>

              {/* Confirm New Password */}
              <div>
                <label className="text-xs font-semibold text-slate-200 block mb-1.5">
                  Confirm New Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
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
                    required
                    className={`w-full bg-[#061527]/90 border rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none transition ${
                      showConfirmPassword ? 'font-mono tracking-wider' : ''
                    } ${
                      isMatch
                        ? 'border-emerald-500/60 focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400'
                        : isMismatch
                        ? 'border-amber-500/60 focus:border-amber-400 focus:ring-1 focus:ring-amber-400'
                        : 'border-cyan-500/30 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-cyan-300 transition cursor-pointer"
                    title={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  >
                    {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>

                {/* Match Status Indicator */}
                {cleanConfirm.length > 0 && (
                  <div className="mt-1.5 flex items-center gap-1.5 text-[11px]">
                    {isMatch ? (
                      <span className="text-emerald-400 flex items-center gap-1 font-medium">
                        <CheckCircle2 size={13} /> Passwords match ({cleanPassword.length} characters)
                      </span>
                    ) : (
                      <span className="text-amber-400 flex items-center gap-1 font-medium">
                        <AlertCircle size={13} /> Passwords do not match
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Reset Password Button */}
              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-2 py-3 bg-gradient-to-r from-cyan-600 via-sky-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition cursor-pointer active:scale-98 shadow-lg shadow-cyan-900/40 tracking-wide"
              >
                {submitting ? (
                  <>
                    <Loader size={16} className="animate-spin text-white" />
                    Updating Password...
                  </>
                ) : (
                  'Reset Password'
                )}
              </button>

              {/* Back to Login Action */}
              <button
                type="button"
                onClick={() => handleModeSwitch('login')}
                className="w-full py-2.5 text-center text-xs font-semibold text-cyan-300 hover:text-cyan-200 transition cursor-pointer"
              >
                Back to Login
              </button>
            </form>
          ) : (
            /* LOGIN / REGISTER FORM */
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && (
                <div>
                  <label className="text-xs font-semibold text-slate-200 block mb-1.5">
                    Full Name
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
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
                      className="w-full bg-[#061527]/90 border border-cyan-500/30 rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                    />
                  </div>
                </div>
              )}

              {/* Work Email */}
              <div>
                <label className="text-xs font-semibold text-slate-200 block mb-1.5">
                  Work Email
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
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
                    className="w-full bg-[#061527]/90 border border-cyan-500/30 rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-200">
                    {mode === 'register' ? 'Create Password' : 'Password'}
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
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Lock size={15} />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                    autoCapitalize="none"
                    autoCorrect="off"
                    spellCheck={false}
                    required
                    className={`w-full bg-[#061527]/90 border border-cyan-500/30 rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition ${
                      showPassword ? 'font-mono tracking-wider' : ''
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-cyan-300 transition cursor-pointer"
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                {mode === 'register' && (
                  <span className="text-[10px] text-slate-400 mt-1 block">
                    Must be at least 8 characters {password.length > 0 && `(${password.length} entered)`}
                  </span>
                )}
              </div>

              {/* Confirm Password (Register mode) */}
              {mode === 'register' && (
                <div>
                  <label className="text-xs font-semibold text-slate-200 block mb-1.5">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
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
                      required
                      className={`w-full bg-[#061527]/90 border rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none transition ${
                        showConfirmPassword ? 'font-mono tracking-wider' : ''
                      } ${
                        isMatch
                          ? 'border-emerald-500/60 focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400'
                          : isMismatch
                          ? 'border-amber-500/60 focus:border-amber-400 focus:ring-1 focus:ring-amber-400'
                          : 'border-cyan-500/30 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-cyan-300 transition cursor-pointer"
                      title={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                    >
                      {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                  {cleanConfirm.length > 0 && (
                    <div className="mt-1.5 flex items-center gap-1.5 text-[11px]">
                      {isMatch ? (
                        <span className="text-emerald-400 flex items-center gap-1 font-medium">
                          <CheckCircle2 size={13} /> Passwords match
                        </span>
                      ) : (
                        <span className="text-amber-400 flex items-center gap-1 font-medium">
                          <AlertCircle size={13} /> Passwords do not match
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-2 py-3 bg-gradient-to-r from-cyan-600 via-sky-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition cursor-pointer active:scale-98 shadow-lg shadow-cyan-900/40 tracking-wide"
              >
                {submitting ? (
                  <>
                    <Loader size={16} className="animate-spin text-white" />
                    {mode === 'register' ? 'Creating Account...' : 'Authenticating...'}
                  </>
                ) : (
                  <>
                    {mode === 'register' ? 'Create Account & Sign In' : 'Sign In to Workspace'}
                    <ArrowRight size={15} />
                  </>
                )}
              </button>
            </form>
          )}

          {/* Mode Switch Footer (Login / Register) */}
          {mode !== 'reset' && (
            <div className="text-center pt-2">
              {mode === 'login' ? (
                <p className="text-xs text-slate-300">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => handleModeSwitch('register')}
                    className="text-cyan-400 hover:text-cyan-300 font-semibold cursor-pointer underline-offset-4 hover:underline"
                  >
                    Create one here
                  </button>
                </p>
              ) : (
                <p className="text-xs text-slate-300">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => handleModeSwitch('login')}
                    className="text-cyan-400 hover:text-cyan-300 font-semibold cursor-pointer underline-offset-4 hover:underline"
                  >
                    Sign in here
                  </button>
                </p>
              )}
            </div>
          )}

          {/* Security Features Callout */}
          <div className="pt-4 border-t border-cyan-500/15 flex items-center justify-center gap-4 text-[11px] text-slate-400">
            <span className="flex items-center gap-1">
              <ShieldCheck size={13} className="text-cyan-400" /> Bcrypt Hashed
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <ShieldCheck size={13} className="text-sky-400" /> JWT Encrypted
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
