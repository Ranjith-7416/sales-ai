import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import './App.css';
import InputForm from './components/InputForm';
import Dashboard from './components/Dashboard';
import LeadsList from './components/LeadsList';
import KnowledgeBaseViewer from './components/KnowledgeBaseViewer';
import ScoringConfigModal from './components/ScoringConfigModal';
import { Sliders, Database, PlusCircle, ListFilter, Sparkles, Server } from 'lucide-react';

function Navigation({ onOpenScoring }: { onOpenScoring: () => void }) {
  const location = useLocation();

  return (
    <nav className="flex items-center gap-2 sm:gap-2.5">
      <NavLink
        to="/"
        end
        className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
          location.pathname === '/'
            ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/25'
            : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent hover:border-slate-700/60'
        }`}
      >
        <PlusCircle size={14} /> <span>New Lead</span>
      </NavLink>
      <NavLink
        to="/leads"
        className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
          location.pathname === '/leads'
            ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/25'
            : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent hover:border-slate-700/60'
        }`}
      >
        <ListFilter size={14} /> <span>All Leads</span>
      </NavLink>
      <NavLink
        to="/knowledge-base"
        className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
          location.pathname === '/knowledge-base'
            ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/25'
            : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent hover:border-slate-700/60'
        }`}
      >
        <Database size={14} /> <span>Knowledge Base</span>
      </NavLink>
      <button
        type="button"
        onClick={onOpenScoring}
        className="flex items-center gap-2 text-slate-300 hover:text-white bg-slate-850/80 hover:bg-slate-800 border border-slate-700/70 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 hover:border-indigo-500/40 hover:shadow-sm hover:shadow-indigo-500/20 cursor-pointer active:scale-95"
      >
        <Sliders size={14} className="text-cyan-400" /> <span>Scoring Config</span>
      </button>
    </nav>
  );
}

function App() {
  const [scoringModalOpen, setScoringModalOpen] = useState(false);

  return (
    <Router>
      <div className="app-shell min-h-screen flex flex-col justify-between">
        {/* Floating Glass Header */}
        <header className="sticky top-0 z-40 bg-slate-950/75 backdrop-blur-xl border-b border-white/[0.08] shadow-2xl">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              {/* Brand Logo & Subtitle */}
              <a href="/" className="flex items-center gap-3 group">
                <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 p-[1px] shadow-lg shadow-indigo-500/30 group-hover:shadow-indigo-500/50 transition-all duration-300">
                  <div className="w-full h-full bg-slate-950 rounded-xl flex items-center justify-center">
                    <Sparkles size={18} className="text-cyan-400 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-black tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                      Sales <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">AI</span>
                    </span>
                    <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full">
                      v2.0
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 block -mt-0.5 font-medium tracking-wide">
                    Agentic Lead Qualification & Proposal Suite
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
          <Routes>
            <Route path="/" element={<InputForm />} />
            <Route path="/leads" element={<LeadsList />} />
            <Route path="/lead/:leadId" element={<Dashboard />} />
            <Route path="/knowledge-base" element={<KnowledgeBaseViewer />} />
          </Routes>
        </main>

        {/* Scoring Config Modal */}
        <ScoringConfigModal
          isOpen={scoringModalOpen}
          onClose={() => setScoringModalOpen(false)}
        />

        {/* Modern Cyber Footer */}
        <footer className="border-t border-white/[0.07] py-6 mt-12 bg-slate-950/60 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              <span>© 2026 Sales AI • Autonomous B2B Pipeline & Grounded Proposal Platform</span>
            </div>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="px-2 py-0.5 bg-slate-900 border border-slate-800 rounded-md text-slate-300 font-mono">6 Specialized Agents</span>
              <span className="px-2 py-0.5 bg-slate-900 border border-slate-800 rounded-md text-slate-300 font-mono">ChromaDB RAG</span>
              <span className="px-2 py-0.5 bg-slate-900 border border-slate-800 rounded-md text-slate-300 font-mono">PostgreSQL CRM</span>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
