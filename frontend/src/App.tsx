import { useState, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import './App.css';
import InputForm from './components/InputForm';
import LoginPage from './components/LoginPage';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Sliders, Database, PlusCircle, ListFilter, Flame, Server, LogOut } from 'lucide-react';

// Lazy-loaded routes for code-splitting and rapid initial bundle delivery
const Dashboard = lazy(() => import('./components/Dashboard'));
const LeadsList = lazy(() => import('./components/LeadsList'));
const KnowledgeBaseViewer = lazy(() => import('./components/KnowledgeBaseViewer'));
const ScoringConfigModal = lazy(() => import('./components/ScoringConfigModal'));

function RouteLoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="text-center space-y-3">
        <div className="w-9 h-9 border-2 border-orange-500/30 border-t-orange-400 rounded-full animate-spin mx-auto" />
        <p className="text-xs font-semibold text-amber-200/70 tracking-wide">Loading workspace...</p>
      </div>
    </div>
  );
}

function Navigation({ onOpenScoring }: { onOpenScoring: () => void }) {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated && location.pathname === '/login') {
    return (
      <div className="flex items-center gap-2">
        <span className="px-3 py-1 bg-orange-500/15 border border-orange-500/30 text-amber-300 rounded-xl text-xs font-semibold">
          Sign In
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <nav className="flex items-center gap-2 sm:gap-2.5">
        <NavLink
          to="/"
          end
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
            location.pathname === '/'
              ? 'bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 text-white shadow-md shadow-orange-500/30'
              : 'text-stone-300 hover:text-white hover:bg-stone-900/80 border border-transparent hover:border-orange-500/30'
          }`}
        >
          <PlusCircle size={14} /> <span>New Lead</span>
        </NavLink>
        <NavLink
          to="/leads"
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
            location.pathname === '/leads'
              ? 'bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 text-white shadow-md shadow-orange-500/30'
              : 'text-stone-300 hover:text-white hover:bg-stone-900/80 border border-transparent hover:border-orange-500/30'
          }`}
        >
          <ListFilter size={14} /> <span>All Leads</span>
        </NavLink>
        <NavLink
          to="/knowledge-base"
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
            location.pathname === '/knowledge-base'
              ? 'bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 text-white shadow-md shadow-orange-500/30'
              : 'text-stone-300 hover:text-white hover:bg-stone-900/80 border border-transparent hover:border-orange-500/30'
          }`}
        >
          <Database size={14} /> <span>Knowledge Base</span>
        </NavLink>
        <button
          type="button"
          onClick={onOpenScoring}
          className="flex items-center gap-2 text-stone-300 hover:text-white bg-stone-900/80 hover:bg-stone-850 border border-stone-750/70 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 hover:border-orange-500/40 hover:shadow-sm hover:shadow-orange-500/20 cursor-pointer active:scale-95"
        >
          <Sliders size={14} className="text-amber-400" /> <span>Scoring Config</span>
        </button>
      </nav>

      {isAuthenticated && (
        <div className="flex items-center gap-2 pl-3 border-l border-white/[0.1]">
          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-amber-500 to-red-600 flex items-center justify-center text-[10px] font-extrabold text-white shadow-md">
            {user?.name ? user.name.slice(0, 2).toUpperCase() : 'SA'}
          </div>
          <div className="hidden lg:block text-left">
            <div className="text-[11px] font-bold text-slate-200 leading-none">{user?.name || 'Sales Director'}</div>
            <div className="text-[9px] text-amber-400/80 capitalize">{user?.role || 'admin'}</div>
          </div>
          <button
            type="button"
            onClick={logout}
            title="Sign Out"
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/15 rounded-lg transition cursor-pointer active:scale-90"
          >
            <LogOut size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

function App() {
  const [scoringModalOpen, setScoringModalOpen] = useState(false);

  return (
    <Router>
      <AuthProvider>
        <div className="app-shell min-h-screen flex flex-col justify-between">
          <div className="fire-embers" aria-hidden="true" />
          {/* Floating Glass Header */}
          <header className="sticky top-0 z-40 bg-stone-950/80 backdrop-blur-xl border-b border-orange-500/20 shadow-2xl">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                {/* Brand Logo & Subtitle */}
                <a href="/" className="flex items-center gap-3 group">
                  <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 via-orange-500 to-red-600 p-[1px] shadow-lg shadow-orange-500/30 group-hover:shadow-orange-500/60 transition-all duration-300">
                    <div className="w-full h-full bg-stone-950 rounded-xl flex items-center justify-center">
                      <Flame size={19} className="text-amber-400 group-hover:scale-110 transition-transform duration-300" />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-black tracking-tight bg-gradient-to-r from-white via-amber-100 to-amber-200 bg-clip-text text-transparent">
                        Sales <span className="bg-gradient-to-r from-amber-400 via-orange-400 to-red-500 bg-clip-text text-transparent">AI</span>
                      </span>
                      <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider bg-orange-500/20 text-orange-300 border border-orange-500/30 rounded-full">
                        v2.0
                      </span>
                    </div>
                    <span className="text-[10px] text-amber-200/60 block -mt-0.5 font-medium tracking-wide">
                      Agentic Lead Qualification &amp; Proposal Suite
                    </span>
                  </div>
                </a>

                {/* Status Indicator & Navigation */}
                <div className="flex items-center gap-4">
                  {/* Live Engine Status Pill */}
                  <div className="hidden lg:flex items-center gap-2 px-3 py-1 bg-slate-900/80 border border-slate-700/60 rounded-full text-[11px] text-slate-300 shadow-inner">
                    <span className="radar-dot" />
                    <span className="font-semibold text-emerald-400">Groq 120B AI</span>
                    <span className="text-slate-600">•</span>
                    <span className="flex items-center gap-1 text-slate-400">
                      <Server size={11} className="text-cyan-400" /> PostgreSQL 18
                    </span>
                  </div>

                  <Navigation onOpenScoring={() => setScoringModalOpen(true)} />
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
            <Suspense fallback={<RouteLoadingFallback />}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <InputForm />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/leads"
                  element={
                    <ProtectedRoute>
                      <LeadsList />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/lead/:leadId"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/knowledge-base"
                  element={
                    <ProtectedRoute>
                      <KnowledgeBaseViewer />
                    </ProtectedRoute>
                  }
                />
              </Routes>

              {/* Scoring Config Modal */}
              <ScoringConfigModal
                isOpen={scoringModalOpen}
                onClose={() => setScoringModalOpen(false)}
              />
            </Suspense>
          </main>

          {/* Modern Fire Footer */}
          <footer className="border-t border-orange-500/15 py-6 mt-12 bg-stone-950/70 backdrop-blur-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-amber-200/60">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-orange-400 shadow-[0_0_8px_rgba(249,115,22,0.8)]" />
                <span>© 2026 Sales AI • Autonomous B2B Pipeline &amp; Grounded Proposal Platform</span>
              </div>
              <div className="flex items-center gap-3 text-[11px]">
                <span className="px-2 py-0.5 bg-stone-900 border border-orange-500/20 rounded-md text-amber-200 font-mono">6 Specialized Agents</span>
                <span className="px-2 py-0.5 bg-stone-900 border border-orange-500/20 rounded-md text-amber-200 font-mono">ChromaDB RAG</span>
                <span className="px-2 py-0.5 bg-stone-900 border border-orange-500/20 rounded-md text-amber-200 font-mono">PostgreSQL CRM</span>
              </div>
            </div>
          </footer>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;
