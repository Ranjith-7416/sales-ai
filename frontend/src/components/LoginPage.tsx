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

type AuthMode = 'login' | 'register';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, isAuthenticated, loading: authLoading } = useAuth();

  const [mode, setMode] = useState<AuthMode>('login');
  
  // Form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const cleanEmail = email.trim().toLowerCase();
    const cleanPassword = password.trim();

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
      if (cleanPassword !== confirmPassword.trim()) {
        setErrorMessage('Passwords do not match. Please re-enter.');
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
        const msg =
          err.response?.data?.detail ||
          err.message ||
          'Invalid email or password. Please try again.';
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
                : 'Create an account to start qualifying leads and closing deals'}
            </p>
          </div>

          {/* Mode Tabs */}
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

          {/* Feedback Notices */}
          {errorMessage && (
            <div className="p-3 bg-rose-950/70 border border-rose-500/40 text-rose-200 rounded-xl text-xs flex items-start gap-2.5 animate-in fade-in">
              <AlertCircle size={16} className="text-rose-400 shrink-0 mt-0.5" />
              <div className="leading-snug">{errorMessage}</div>
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
                  required
                  className="w-full bg-slate-800/80 border border-white/[0.1] rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                {mode === 'register' ? 'Create Password' : 'Password'}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock size={15} />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                  required
                  className="w-full bg-slate-800/80 border border-white/[0.1] rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition cursor-pointer"
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {mode === 'register' && (
                <span className="text-[10px] text-slate-400 mt-1 block">
                  Must be at least 6 characters
                </span>
              )}
            </div>

            {mode === 'register' && (
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <Lock size={15} />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    autoComplete="new-password"
                    required={mode === 'register'}
                    className="w-full bg-slate-800/80 border border-white/[0.1] rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                  />
                </div>
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
            ) : (
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

