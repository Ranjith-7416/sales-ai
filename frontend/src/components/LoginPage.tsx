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
  Zap,
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, loading: authLoading } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [demoNotice, setDemoNotice] = useState<string | null>(null);

  const destination = (location.state as any)?.from?.pathname || '/';

  // If already logged in, redirect immediately
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      navigate(destination, { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate, destination]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      await login(email.trim(), password.trim());
      navigate(destination, { replace: true });
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Authentication failed. Please check your credentials.';
      setErrorMessage(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemoAccount = () => {
    setEmail('admin@salesai.com');
    setPassword('salesai123');
    setErrorMessage(null);
    setDemoNotice('Demo credentials applied! Click "Sign In" to continue.');
    setTimeout(() => setDemoNotice(null), 4000);
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
              Sign in to manage your autonomous enterprise deal pipeline
            </p>
          </div>

          {/* Quick Fill Demo Banner */}
          <div className="p-3 bg-gradient-to-r from-indigo-950/70 to-purple-950/70 border border-indigo-500/30 rounded-2xl flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-yellow-400 shrink-0" />
              <div className="text-[11px] leading-tight text-slate-300">
                <span className="font-semibold text-white block">Evaluator / Demo Access</span>
                admin@salesai.com • salesai123
              </div>
            </div>
            <button
              type="button"
              onClick={fillDemoAccount}
              className="px-2.5 py-1 bg-indigo-600/40 hover:bg-indigo-600/70 text-indigo-200 hover:text-white border border-indigo-400/40 rounded-xl text-[10px] font-bold uppercase tracking-wider transition cursor-pointer active:scale-95 whitespace-nowrap"
            >
              Quick Fill
            </button>
          </div>

          {/* Feedback Notices */}
          {errorMessage && (
            <div className="p-3 bg-rose-950/70 border border-rose-500/40 text-rose-200 rounded-xl text-xs flex items-start gap-2.5 animate-in fade-in">
              <AlertCircle size={16} className="text-rose-400 shrink-0 mt-0.5" />
              <div className="leading-snug">{errorMessage}</div>
            </div>
          )}

          {demoNotice && (
            <div className="p-3 bg-emerald-950/70 border border-emerald-500/40 text-emerald-200 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
              <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
              <div>{demoNotice}</div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
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
                  placeholder="admin@salesai.com"
                  autoComplete="email"
                  required
                  className="w-full bg-slate-800/80 border border-white/[0.1] rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Password
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
                  autoComplete="current-password"
                  required
                  className="w-full bg-slate-800/80 border border-white/[0.1] rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition"
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-2 py-3 bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition cursor-pointer active:scale-98 shadow-lg shadow-indigo-500/25 tracking-wide"
            >
              {submitting ? (
                <>
                  <Loader size={16} className="animate-spin text-white" />
                  Authenticating...
                </>
              ) : (
                <>
                  Sign In to Workspace <ArrowRight size={15} />
                </>
              )}
            </button>
          </form>

          {/* Security Features Callout */}
          <div className="pt-4 border-t border-white/[0.06] flex items-center justify-center gap-4 text-[11px] text-slate-400">
            <span className="flex items-center gap-1">
              <ShieldCheck size={13} className="text-emerald-400" /> JWT Encrypted
            </span>
            <span>•</span>
            <span>PostgreSQL CRM</span>
            <span>•</span>
            <span>Agentic Orchestration</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
