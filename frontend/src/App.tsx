import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import './App.css';
import InputForm from './components/InputForm';
import Dashboard from './components/Dashboard';
import LeadsList from './components/LeadsList';
import KnowledgeBaseViewer from './components/KnowledgeBaseViewer';
import ScoringConfigModal from './components/ScoringConfigModal';
import { Sliders, Database, PlusCircle, ListFilter } from 'lucide-react';

function Navigation({ onOpenScoring }: { onOpenScoring: () => void }) {
  const location = useLocation();

  return (
    <nav className="app-nav flex items-center gap-1.5 sm:gap-3">
      <NavLink
        to="/"
        end
        className={`nav-link flex items-center gap-1.5 ${location.pathname === '/' ? 'nav-link-active' : ''}`}
      >
        <PlusCircle size={14} /> <span>New Lead</span>
      </NavLink>
      <NavLink
        to="/leads"
        className={`nav-link flex items-center gap-1.5 ${location.pathname === '/leads' ? 'nav-link-active' : ''}`}
      >
        <ListFilter size={14} /> <span>All Leads</span>
      </NavLink>
      <NavLink
        to="/knowledge-base"
        className={`nav-link flex items-center gap-1.5 ${location.pathname === '/knowledge-base' ? 'nav-link-active' : ''}`}
      >
        <Database size={14} /> <span>Knowledge Base</span>
      </NavLink>
      <button
        type="button"
        onClick={onOpenScoring}
        className="nav-link flex items-center gap-1.5 text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer"
      >
        <Sliders size={14} className="text-blue-400" /> <span>Scoring Config</span>
      </button>
    </nav>
  );
}

function App() {
  const [scoringModalOpen, setScoringModalOpen] = useState(false);

  return (
    <Router>
      <div className="app-shell min-h-screen flex flex-col justify-between">
        {/* Header */}
        <header className="app-header sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <a href="/" className="brand-mark flex items-center gap-3">
                <span className="brand-dot w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" aria-hidden="true" />
                <span>
                  <span className="brand-name text-lg font-black text-white tracking-tight block">Sales AI</span>
                  <span className="brand-caption text-[11px] text-slate-400 block -mt-1">Agentic Lead Qualification & Proposals</span>
                </span>
              </a>
              <div className="header-right flex items-center gap-3">
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

        {/* Footer */}
        <footer className="app-footer border-t border-slate-800 py-6 mt-12 bg-slate-900/50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
            <p>© 2026 Sales AI • Agentic Lead Qualification & Grounded Proposal System</p>
            <div className="flex gap-4">
              <span>6-Agent LangGraph Pipeline</span>
              <span>RAG Catalog Grounding</span>
              <span>Explainable Scoring</span>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
