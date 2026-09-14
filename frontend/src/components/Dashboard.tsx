import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { Lead, LeadInput, LeadStatus } from '../types';
import {
  Loader,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  Edit3,
  Save,
  X,
  Download,
  Printer,
  Check,
  ShieldCheck,
  Clock,
  AlertTriangle,
  Building2,
  HelpCircle,
  ArrowRight,
  Sparkles,
  FileText,
  Database,
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const { leadId } = useParams<{ leadId: string }>();
  const navigate = useNavigate();
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'research' | 'requirements' | 'solution' | 'proposal' | 'review'>('overview');
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<LeadInput>({ inquiry_text: '' });
  const [approving, setApproving] = useState(false);
  const [approvedSuccess, setApprovedSuccess] = useState(false);
  const [exporting, setExporting] = useState(false);

  const api = useApi();

  useEffect(() => {
    if (!leadId) return;

    let isMounted = true;
    const fetchLead = async () => {
      try {
        setLoading(true);
        const data = await api.getLead(leadId);
        if (!isMounted) return;
        setLead(data);

        // Poll if still processing
        if (data.status !== 'completed') {
          const interval = setInterval(async () => {
            try {
              const updated = await api.getLead(leadId);
              if (!isMounted) return;
              setLead(updated);
              if (updated.status === 'completed') {
                clearInterval(interval);
              }
            } catch (err) {
              console.error('Poll error:', err);
            }
          }, 2000);

          return () => clearInterval(interval);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load lead');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchLead();
    return () => { isMounted = false; };
  }, [leadId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <Loader className="animate-spin mx-auto mb-4 text-blue-500" size={40} />
          <p className="text-white text-lg font-medium">Analyzing sales lead through AI pipeline...</p>
          <p className="text-slate-400 text-sm mt-1">Extracting requirements, searching knowledge base, qualifying...</p>
        </div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded-xl p-8 flex gap-4">
        <AlertCircle className="text-red-500 flex-shrink-0" size={28} />
        <div>
          <h3 className="text-red-100 font-bold text-lg">Error Loading Lead</h3>
          <p className="text-red-200 mt-1">{error || 'Lead record not found in system.'}</p>
          <button
            type="button"
            onClick={() => navigate('/leads')}
            className="mt-4 px-4 py-2 bg-red-800/60 hover:bg-red-700 text-white rounded-lg text-sm transition cursor-pointer active:scale-95"
          >
            Return to All Leads
          </button>
        </div>
      </div>
    );
  }

  const qualification = lead.result?.qualification || lead.result?.qualification_result || lead.result?.results?.qualification;
  const research = lead.result?.research || lead.result?.results?.research;
  const requirements = lead.result?.requirements || lead.result?.requirements_result || lead.result?.results?.requirements;
  const solution = lead.result?.solution_matching || lead.result?.results?.solution_matching;
  const proposal = lead.result?.proposal || lead.result?.results?.proposal;
  const review = lead.result?.reviewer || lead.result?.results?.reviewer;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Qualified':
      case LeadStatus.Qualified:
        return {
          color: 'bg-emerald-900/40 border-emerald-500/60 text-emerald-300',
          icon: <CheckCircle2 size={18} className="text-emerald-400" />,
          label: 'Qualified',
        };
      case 'Needs More Information':
      case LeadStatus.NeedsInfo:
        return {
          color: 'bg-amber-900/40 border-amber-500/60 text-amber-300',
          icon: <HelpCircle size={18} className="text-amber-400" />,
          label: 'Needs More Information',
        };
      case 'Low Priority':
      case LeadStatus.LowPriority:
        return {
          color: 'bg-rose-900/40 border-rose-500/60 text-rose-300',
          icon: <AlertTriangle size={18} className="text-rose-400" />,
          label: 'Low Priority',
        };
      default:
        return {
          color: 'bg-blue-900/40 border-blue-500/60 text-blue-300',
          icon: <Loader size={18} className="animate-spin text-blue-400" />,
          label: status || 'Processing',
        };
    }
  };

  const statusBadge = getStatusBadge(lead.lead_status);

  const formatScore = (score: number | undefined) => {
    if (score === undefined || score === null) return '0';
    return (lead.lead_status === LeadStatus.NeedsInfo && score === 0) ? 'Not scored' : Math.round(score).toString();
  };

  const formatCatalogPricing = (pricing: any) => {
    if (!pricing) return 'To be confirmed';
    if (typeof pricing === 'string') return pricing;
    if (pricing.total) return pricing.total;
    if (pricing.breakdown) {
      return Object.entries(pricing.breakdown)
        .map(([name, value]) => `${name}: ${value}`)
        .join('; ');
    }
    return 'Grounded catalog pricing';
  };

  const stageLabels: Record<string, string> = {
    research: 'Researching company public context',
    requirements: 'Extracting functional & non-functional requirements',
    qualification: 'Computing explainable opportunity score',
    solution_matching: 'Matching product catalog with RAG',
    proposal: 'Drafting strictly grounded proposal',
    reviewer: 'Validating coverage & verifying claims against KB',
  };

  const startEditing = () => {
    setEditForm({
      company_name: lead.company_name,
      contact_name: lead.contact_name,
      email: lead.email,
      inquiry_text: lead.inquiry_text,
      industry: lead.industry,
      company_size: lead.company_size,
      budget: lead.budget,
      timeline: lead.timeline,
      additional_context: lead.additional_context,
    });
    setEditing(true);
  };

  const handleUpdate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!leadId || !editForm.inquiry_text.trim()) return;
    await api.updateLead(leadId, editForm);
    setEditing(false);
    setActiveTab('overview');
    setLead(await api.getLead(leadId));
  };

  const handleExportProposal = async () => {
    if (!leadId) return;
    setExporting(true);
    try {
      const result = await api.exportProposal(leadId, 'markdown');
      const blob = new Blob([result.markdown], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = result.filename || `Proposal_${lead.company_name || 'Lead'}.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setExporting(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!leadId) return;
    setApproving(true);
    try {
      await api.approveProposal(leadId, 'Sales AI Reviewer');
      setApprovedSuccess(true);
    } catch (err) {
      console.error('Approval failed:', err);
    } finally {
      setApproving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Customer Information */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-700">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-white tracking-tight">
                {lead.company_name || 'Customer Opportunity'}
              </h1>
              <div className={`inline-flex items-center gap-2 border rounded-full px-3.5 py-1 text-sm font-semibold shadow-sm ${statusBadge.color}`}>
                {statusBadge.icon}
                <span>{statusBadge.label}</span>
              </div>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Lead ID: <span className="font-mono text-slate-300">{lead.id}</span> • Received {new Date(lead.created_at).toLocaleDateString()}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={startEditing}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-700 hover:bg-slate-600 px-3.5 py-2 text-sm font-medium text-white transition border border-slate-600 cursor-pointer active:scale-95"
            >
              <Edit3 size={15} /> Edit Lead Context
            </button>
            {proposal && (
              <button
                type="button"
                onClick={handleExportProposal}
                disabled={exporting}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-700 px-3.5 py-2 text-sm font-medium text-white transition shadow-sm cursor-pointer active:scale-95"
              >
                <Download size={15} /> {exporting ? 'Exporting...' : 'Export Proposal (.md)'}
              </button>
            )}
          </div>
        </div>

        {/* Customer Info Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-4 text-xs">
          <div className="bg-slate-700/40 p-2.5 rounded-lg border border-slate-600/30">
            <span className="text-slate-400 block mb-0.5">Contact</span>
            <span className="text-white font-medium truncate block">{lead.contact_name || 'Not provided'}</span>
          </div>
          <div className="bg-slate-700/40 p-2.5 rounded-lg border border-slate-600/30">
            <span className="text-slate-400 block mb-0.5">Email</span>
            <span className="text-white font-medium truncate block">{lead.email || 'Not provided'}</span>
          </div>
          <div className="bg-slate-700/40 p-2.5 rounded-lg border border-slate-600/30">
            <span className="text-slate-400 block mb-0.5">Industry</span>
            <span className="text-white font-medium truncate block">{lead.industry || 'General'}</span>
          </div>
          <div className="bg-slate-700/40 p-2.5 rounded-lg border border-slate-600/30">
            <span className="text-slate-400 block mb-0.5">Company Size</span>
            <span className="text-white font-medium truncate block">{lead.company_size || 'To be confirmed'}</span>
          </div>
          <div className="bg-slate-700/40 p-2.5 rounded-lg border border-slate-600/30">
            <span className="text-slate-400 block mb-0.5">Budget</span>
            <span className="text-white font-medium truncate block">{lead.budget || 'To be confirmed'}</span>
          </div>
          <div className="bg-slate-700/40 p-2.5 rounded-lg border border-slate-600/30">
            <span className="text-slate-400 block mb-0.5">Timeline</span>
            <span className="text-white font-medium truncate block">{lead.timeline || 'To be confirmed'}</span>
          </div>
        </div>

        {/* Lead Score Cards */}
        {qualification && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-5">
            <div className="bg-gradient-to-br from-blue-950/60 to-slate-900 border border-blue-800/80 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Composite Score</span>
                <div className="text-3xl font-black text-blue-400 mt-1">
                  {formatScore(qualification.composite_score)}
                  <span className="text-xs font-normal text-slate-500"> / 100</span>
                </div>
              </div>
              <div className="w-full bg-slate-700 h-1.5 rounded-full mt-3 overflow-hidden">
                <div
                  className="bg-blue-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.composite_score || 0))}%` }}
                />
              </div>
            </div>

            <div className="bg-slate-750/70 bg-slate-800/90 border border-slate-700 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Product Fit (25%)</span>
                <div className="text-2xl font-bold text-emerald-400 mt-1">
                  {formatScore(qualification.fit_score)}
                </div>
              </div>
              <div className="w-full bg-slate-700 h-1.5 rounded-full mt-3 overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.fit_score || 0))}%` }}
                />
              </div>
            </div>

            <div className="bg-slate-750/70 bg-slate-800/90 border border-slate-700 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Readiness (25%)</span>
                <div className="text-2xl font-bold text-yellow-400 mt-1">
                  {formatScore(qualification.readiness_score)}
                </div>
              </div>
              <div className="w-full bg-slate-700 h-1.5 rounded-full mt-3 overflow-hidden">
                <div
                  className="bg-yellow-500 h-full rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.readiness_score || 0))}%` }}
                />
              </div>
            </div>

            <div className="bg-slate-750/70 bg-slate-800/90 border border-slate-700 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Opportunity (30%)</span>
                <div className="text-2xl font-bold text-purple-400 mt-1">
                  {formatScore(qualification.opportunity_score)}
                </div>
              </div>
              <div className="w-full bg-slate-700 h-1.5 rounded-full mt-3 overflow-hidden">
                <div
                  className="bg-purple-500 h-full rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.opportunity_score || 0))}%` }}
                />
              </div>
            </div>

            <div className="bg-slate-750/70 bg-slate-800/90 border border-slate-700 rounded-xl p-4 flex flex-col justify-between">
              <div>
                <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Risk Level (20%)</span>
                <div className="text-2xl font-bold text-rose-400 mt-1">
                  {Math.round(qualification.risk_score || 0)}
                  <span className="text-xs text-slate-400 font-normal"> (low is good)</span>
                </div>
              </div>
              <div className="w-full bg-slate-700 h-1.5 rounded-full mt-3 overflow-hidden">
                <div
                  className="bg-rose-500 h-full rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.risk_score || 0))}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Processing status banner */}
        {lead.status !== 'completed' && (
          <div className="mt-5 rounded-lg border border-blue-700 bg-blue-950/40 p-4 text-blue-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Loader className="animate-spin text-blue-400" size={18} />
              <span className="font-medium">
                {stageLabels[lead.current_stage || ''] || 'Processing sequential multi-agent pipeline...'}
              </span>
            </div>
            {lead.stages_completed && lead.stages_completed.length > 0 && (
              <span className="text-xs text-blue-300 font-mono">
                Completed: {lead.stages_completed.filter(s => s !== 'complete').join(' → ')}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Inline Edit Form Modal / Accordion */}
      {editing && (
        <form onSubmit={handleUpdate} className="bg-slate-800 border border-blue-600 rounded-xl p-6 space-y-4 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-slate-700">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Edit3 size={18} className="text-blue-400" /> Update Lead Context & Re-evaluate
            </h2>
            <button type="button" onClick={() => setEditing(false)} className="text-slate-400 hover:text-white" aria-label="Cancel update">
              <X size={20} />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              name="company_name"
              value={editForm.company_name || ''}
              onChange={(e) => setEditForm({ ...editForm, company_name: e.target.value })}
              placeholder="Company Name"
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400"
            />
            <input
              name="contact_name"
              value={editForm.contact_name || ''}
              onChange={(e) => setEditForm({ ...editForm, contact_name: e.target.value })}
              placeholder="Contact Person"
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400"
            />
            <input
              name="email"
              value={editForm.email || ''}
              onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
              placeholder="Email"
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400"
            />
            <input
              name="industry"
              value={editForm.industry || ''}
              onChange={(e) => setEditForm({ ...editForm, industry: e.target.value })}
              placeholder="Industry"
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400"
            />
            <input
              name="company_size"
              value={editForm.company_size || ''}
              onChange={(e) => setEditForm({ ...editForm, company_size: e.target.value })}
              placeholder="Company Size (e.g. 500-1000)"
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400"
            />
            <input
              name="budget"
              value={editForm.budget || ''}
              onChange={(e) => setEditForm({ ...editForm, budget: e.target.value })}
              placeholder="Budget Range"
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400"
            />
          </div>
          <div>
            <label className="text-xs text-slate-300 block mb-1">Customer Inquiry Requirements:</label>
            <textarea
              name="inquiry_text"
              value={editForm.inquiry_text}
              onChange={(e) => setEditForm({ ...editForm, inquiry_text: e.target.value })}
              required
              rows={3}
              placeholder="Inquiry text..."
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400"
            />
          </div>
          <div>
            <label className="text-xs text-slate-300 block mb-1">Additional Context (Decision-maker, Integrations, Success Criteria):</label>
            <textarea
              name="additional_context"
              value={editForm.additional_context || ''}
              onChange={(e) => setEditForm({ ...editForm, additional_context: e.target.value })}
              rows={2}
              placeholder="Approvals, existing stack, integrations..."
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="px-4 py-2 text-sm text-slate-300 hover:text-white bg-slate-700 rounded-lg transition cursor-pointer active:scale-95"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-sm font-semibold text-white transition cursor-pointer active:scale-95"
            >
              <Save size={15} /> Save and Re-run Pipeline
            </button>
          </div>
        </form>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-slate-700">
        <div className="flex gap-1 overflow-x-auto pb-0.5">
          {[
            { id: 'overview', label: 'Overview & Qualification' },
            { id: 'research', label: 'Company Research' },
            { id: 'requirements', label: 'Extracted Requirements' },
            { id: 'solution', label: 'Solution' },
            { id: 'proposal', label: 'Proposal' },
            { id: 'review', label: 'Review' },
          ].map(tab => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-3 font-semibold text-sm border-b-2 transition whitespace-nowrap cursor-pointer active:scale-[0.98] ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-400 bg-slate-800/40'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Panels */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 min-h-[450px]">
        {/* 1. OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Qualification Narrative */}
            {qualification && (
              <div className="bg-slate-750/50 bg-slate-900/40 p-5 rounded-xl border border-slate-700">
                <h2 className="text-base font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
                  <Sparkles size={18} className="text-blue-400" /> Qualification Reasoning & Narrative
                </h2>
                <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-line">
                  {qualification.qualification_reasoning}
                </p>
              </div>
            )}

            {/* Missing Information Callout */}
            {requirements?.missing_information && requirements.missing_information.length > 0 && (
              <div className="bg-amber-950/30 border border-amber-600/50 rounded-xl p-5">
                <h3 className="text-base font-bold text-amber-300 mb-2 flex items-center gap-2">
                  <HelpCircle size={18} className="text-amber-400" /> Information Needed to Accelerate Deal
                </h3>
                <p className="text-xs text-amber-200/80 mb-3">
                  The following requirements were not fully specified in the customer inquiry. Click "Edit Lead Context" to fill them in:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {requirements.missing_information.map((item, idx) => (
                    <div key={idx} className="bg-amber-900/20 border border-amber-800/50 rounded-lg p-2.5 text-xs text-amber-100 flex items-start gap-2">
                      <span className="text-amber-400 font-bold">•</span>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Score Drivers */}
            {qualification?.score_drivers && qualification.score_drivers.length > 0 && (
              <div>
                <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                  <TrendingUp size={18} className="text-emerald-400" /> Key Score Drivers & Evidence
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {qualification.score_drivers.map((driver, idx) => {
                    const factor = Array.isArray(driver) ? driver[0] : (driver as any)?.factor || 'Driver';
                    const impact = Array.isArray(driver) ? driver[1] : (driver as any)?.impact || 'Positive';
                    return (
                      <div key={idx} className="bg-slate-700/50 border border-slate-600/60 rounded-lg p-3.5 flex items-start gap-3">
                        <CheckCircle2 size={16} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-white font-semibold text-sm">{factor}</p>
                          <p className="text-slate-300 text-xs mt-0.5">{impact}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Original Customer Inquiry Preview */}
            <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-700/60">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Customer Inquiry Text</h3>
              <p className="text-slate-300 text-sm italic">"{lead.inquiry_text}"</p>
            </div>
          </div>
        )}

        {/* 2. RESEARCH TAB */}
        {activeTab === 'research' && (
          <div className="space-y-6">
            {research ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-700/50 p-4 rounded-xl border border-slate-600/50">
                    <span className="text-xs text-slate-400 uppercase tracking-wider block">Company & Industry</span>
                    <h3 className="text-lg font-bold text-white mt-1">{research.company_name}</h3>
                    <p className="text-sm text-blue-400 mt-0.5">{research.industry_vertical} • {research.company_size}</p>
                    <p className="text-xs text-slate-400 mt-2"><strong>Location:</strong> {research.location}</p>
                  </div>
                  <div className="bg-slate-700/50 p-4 rounded-xl border border-slate-600/50">
                    <span className="text-xs text-slate-400 uppercase tracking-wider block">Market Position & Model</span>
                    <p className="text-sm text-slate-200 mt-1">{research.business_model}</p>
                    <p className="text-xs text-slate-300 mt-2"><strong>Position:</strong> {research.market_position}</p>
                  </div>
                </div>

                {research.recent_news && research.recent_news.length > 0 && (
                  <div className="bg-slate-750/50 bg-slate-900/30 p-4 rounded-xl border border-slate-700">
                    <h3 className="text-sm font-bold text-white mb-2">Public Intelligence & Recent Developments</h3>
                    <ul className="space-y-2">
                      {research.recent_news.map((item, idx) => (
                        <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                          <span className="text-blue-400">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <Building2 size={36} className="mx-auto mb-2 text-slate-500" />
                <p>Public company research results will appear once the research agent completes.</p>
              </div>
            )}
          </div>
        )}

        {/* 3. REQUIREMENTS TAB */}
        {activeTab === 'requirements' && (
          <div className="space-y-6">
            {requirements ? (
              <>
                <div>
                  <h2 className="text-lg font-bold text-white mb-3">Extracted Functional Requirements</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {requirements.functional_requirements.map((req, idx) => (
                      <div key={idx} className="bg-slate-700/60 border border-slate-600/60 rounded-lg p-3 flex items-start gap-2">
                        <Check size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-slate-200">{req}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {requirements.non_functional_requirements && Object.keys(requirements.non_functional_requirements).length > 0 && (
                  <div>
                    <h3 className="text-base font-bold text-white mb-3">Non-Functional & Operational Requirements</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      {Object.entries(requirements.non_functional_requirements).map(([k, v]) => (
                        <div key={k} className="bg-slate-700/40 border border-slate-600/40 rounded-lg p-3">
                          <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider block capitalize">{k}</span>
                          <span className="text-xs text-slate-200 mt-1 block">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {requirements.missing_information && requirements.missing_information.length > 0 && (
                  <div className="bg-amber-950/20 border border-amber-700/60 rounded-xl p-4">
                    <h3 className="text-sm font-bold text-amber-300 mb-2">Unclear or Missing Requirements</h3>
                    <div className="space-y-1.5">
                      {requirements.missing_information.map((item, idx) => (
                        <p key={idx} className="text-xs text-amber-200 flex items-center gap-1.5">
                          <AlertTriangle size={13} className="text-amber-400 flex-shrink-0" /> {item}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <FileText size={36} className="mx-auto mb-2 text-slate-500" />
                <p>Requirement analysis will populate when the pipeline runs.</p>
              </div>
            )}
          </div>
        )}

        {/* 4. SOLUTION TAB */}
        {activeTab === 'solution' && (
          <div className="space-y-6">
            {solution ? (
              <>
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-white">Recommended Solutions (Catalog-Grounded)</h2>
                  <span className="inline-flex items-center gap-1.5 bg-emerald-950/60 border border-emerald-700 text-emerald-300 px-3 py-1 rounded-full text-xs font-medium">
                    <ShieldCheck size={14} className="text-emerald-400" /> Grounded in Knowledge Base
                  </span>
                </div>

                {solution.primary_solutions && solution.primary_solutions.map((sol, idx) => (
                  <div key={idx} className="bg-slate-750/70 bg-slate-700/50 border border-slate-600 rounded-xl p-5 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-600/60 pb-3">
                      <div>
                        <h3 className="text-xl font-bold text-white">{sol.product_name}</h3>
                        <p className="text-xs text-slate-400">Product ID: {sol.product_name.toLowerCase().replace(/[^a-z0-9]/g, '-')}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs px-3 py-1 bg-blue-900/60 border border-blue-700 rounded-lg text-blue-300 font-bold">
                          {sol.coverage_percentage}% Requirements Match
                        </span>
                        <span className="text-sm font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-3 py-1 rounded-lg">
                          {formatCatalogPricing(sol.pricing)}
                        </span>
                      </div>
                    </div>

                    {/* Matched Features */}
                    {sol.features_matched && sol.features_matched.length > 0 && (
                      <div>
                        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">Verified Matched Capabilities</span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {sol.features_matched.map((feat, fidx) => (
                            <div key={fidx} className="bg-slate-800/80 p-2 rounded text-xs text-slate-200 flex items-center gap-2 border border-slate-700/60">
                              <Check size={14} className="text-emerald-400 flex-shrink-0" />
                              <span>{feat}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                      {sol.delivery_timeline && (
                        <div className="flex items-center gap-2 text-slate-300">
                          <Clock size={14} className="text-amber-400" />
                          <span><strong>Implementation Timeline:</strong> {sol.delivery_timeline}</span>
                        </div>
                      )}
                      {sol.certifications && sol.certifications.length > 0 && (
                        <div className="flex items-center gap-2 text-slate-300">
                          <ShieldCheck size={14} className="text-purple-400" />
                          <span><strong>Certifications:</strong> {sol.certifications.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {solution.estimated_solution_value && (
                  <div className="bg-blue-950/40 border border-blue-800/80 rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold uppercase tracking-wider text-blue-300 block">Total Estimated Solution Value</span>
                      <span className="text-lg font-bold text-white mt-1 block">
                        {formatCatalogPricing(solution.estimated_solution_value)}
                      </span>
                    </div>
                    <span className="text-xs text-slate-400">Strictly derived from catalog pricing tiers</span>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <Database size={36} className="mx-auto mb-2 text-slate-500" />
                <h3 className="text-lg font-bold text-white mb-1">Solution Draft Pending</h3>
                <p className="text-sm">Grounded solutions will appear once the Solution Matching Agent completes.</p>
              </div>
            )}
          </div>
        )}

        {/* 5. PROPOSAL TAB */}
        {activeTab === 'proposal' && (
          <div className="space-y-6">
            {proposal ? (
              <>
                {/* Actions Toolbar */}
                <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 p-4 rounded-xl border border-slate-700">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Status:</span>
                    <span className="text-xs bg-emerald-900/60 text-emerald-300 border border-emerald-700 px-2.5 py-1 rounded font-bold">
                      Grounded Draft Ready
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={handleExportProposal}
                      disabled={exporting}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95"
                    >
                      <Download size={14} /> Download (.md)
                    </button>
                    <button
                      type="button"
                      onClick={() => window.print()}
                      className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95"
                    >
                      <Printer size={14} /> Print / PDF
                    </button>
                    <button
                      type="button"
                      onClick={handleApproveProposal}
                      disabled={approving || approvedSuccess}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                        approvedSuccess
                          ? 'bg-emerald-800 text-emerald-200 cursor-default'
                          : 'bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer active:scale-95'
                      }`}
                    >
                      <Check size={14} /> {approvedSuccess ? 'Approved ✓' : approving ? 'Approving...' : 'Approve Proposal'}
                    </button>
                  </div>
                </div>

                {/* Proposal Content Body */}
                <div className="bg-slate-900/40 p-6 rounded-xl border border-slate-700 space-y-6">
                  {/* Executive Summary */}
                  <div>
                    <h2 className="text-lg font-bold text-white mb-2">1. Executive Summary</h2>
                    <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-line bg-slate-800/60 p-4 rounded-lg border border-slate-700/60">
                      {proposal.executive_summary}
                    </p>
                  </div>

                  {/* Proposed Solution */}
                  <div>
                    <h2 className="text-lg font-bold text-white mb-2">2. Proposed Solution Architecture</h2>
                    <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-line bg-slate-800/60 p-4 rounded-lg border border-slate-700/60">
                      {proposal.proposed_solution}
                    </p>
                  </div>

                  {/* Implementation Roadmap */}
                  {proposal.implementation_roadmap && proposal.implementation_roadmap.length > 0 && (
                    <div>
                      <h2 className="text-lg font-bold text-white mb-2">3. Implementation Roadmap</h2>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs text-slate-300 border border-slate-700 rounded-lg overflow-hidden">
                          <thead className="bg-slate-800 text-slate-200 uppercase tracking-wider">
                            <tr>
                              <th className="p-3">Phase</th>
                              <th className="p-3">Estimated Duration</th>
                              <th className="p-3">Key Activities</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-700 bg-slate-800/40">
                            {proposal.implementation_roadmap.map((item, idx) => (
                              <tr key={idx}>
                                <td className="p-3 font-semibold text-white">{String(item.phase || `Phase ${idx + 1}`)}</td>
                                <td className="p-3 text-amber-300">{String(item.duration || '2-4 weeks')}</td>
                                <td className="p-3 text-slate-300">
                                  {Array.isArray(item.activities) ? item.activities.join(', ') : String(item.activities || '')}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Pricing Model */}
                  {proposal.pricing_proposal && (
                    <div>
                      <h2 className="text-lg font-bold text-white mb-2">4. Commercial & Investment Model</h2>
                      <div className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                          {Object.entries(proposal.pricing_proposal).map(([key, value]) => (
                            <div key={key} className="flex justify-between items-center py-1.5 border-b border-slate-700/50">
                              <span className="capitalize text-slate-400">{key.replace(/_/g, ' ')}:</span>
                              <span className="font-bold text-emerald-400">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* SLA & Support */}
                  {proposal.support_service_levels && Object.keys(proposal.support_service_levels).length > 0 && (
                    <div>
                      <h2 className="text-lg font-bold text-white mb-2">5. Service Levels & Compliance</h2>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        {Object.entries(proposal.support_service_levels).map(([k, v]) => (
                          <div key={k} className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-3 text-xs">
                            <span className="text-slate-400 uppercase tracking-wider block capitalize">{k.replace(/_/g, ' ')}</span>
                            <span className="text-slate-200 font-semibold mt-1 block">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <FileText size={36} className="mx-auto mb-2 text-slate-500" />
                <h3 className="text-lg font-bold text-white mb-1">Proposal Draft Pending</h3>
                <p className="text-sm">The proposal agent will draft grounded terms once solution matching is complete.</p>
              </div>
            )}
          </div>
        )}

        {/* 6. REVIEW TAB */}
        {activeTab === 'review' && (
          <div className="space-y-6">
            {review ? (
              <>
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-white">Quality Assurance & Anti-Hallucination Review</h2>
                  <span className={`text-xs px-3 py-1 rounded-full font-bold border ${
                    review.readiness_assessment?.ready_to_send
                      ? 'bg-emerald-950/60 border-emerald-700 text-emerald-300'
                      : 'bg-amber-950/60 border-amber-700 text-amber-300'
                  }`}>
                    {review.readiness_assessment?.ready_to_send ? 'Ready for Customer Sign-off' : 'Requires Human Review'}
                  </span>
                </div>

                {/* Follow-up Questions */}
                {review.follow_up_questions && review.follow_up_questions.length > 0 && (
                  <div className="bg-slate-750/70 bg-slate-900/40 p-4 rounded-xl border border-slate-700">
                    <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
                      <HelpCircle size={16} className="text-blue-400" /> Follow-up Questions for Customer
                    </h3>
                    <div className="space-y-2">
                      {review.follow_up_questions.map((q, idx) => (
                        <div key={idx} className="bg-slate-800/80 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 flex items-start gap-2">
                          <span className="text-blue-400 font-bold">Q{idx + 1}:</span>
                          <span>{q}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommended Next Steps */}
                {review.recommended_next_steps && review.recommended_next_steps.length > 0 && (
                  <div className="bg-slate-750/70 bg-slate-900/40 p-4 rounded-xl border border-slate-700">
                    <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
                      <ArrowRight size={16} className="text-emerald-400" /> Recommended Next Actions
                    </h3>
                    <ol className="space-y-2">
                      {review.recommended_next_steps.map((step, idx) => (
                        <li key={idx} className="bg-slate-800/80 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 flex items-start gap-2.5">
                          <span className="font-bold text-emerald-400">{idx + 1}.</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {/* Claim Verification Checklist */}
                {review.claim_verification && review.claim_verification.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-white mb-2">Claim Verification Grounding</h3>
                    <div className="space-y-2">
                      {review.claim_verification.map((claimItem, idx) => {
                        const claim = typeof claimItem === 'object' && claimItem !== null ? (claimItem as any).claim : String(claimItem);
                        const source = typeof claimItem === 'object' && claimItem !== null ? (claimItem as any).source : 'KB';
                        const verified = typeof claimItem === 'object' && claimItem !== null
                          ? (claimItem as any).verified !== false && (claimItem as any).verified !== 'false'
                          : true;
                        return (
                          <div key={idx} className="bg-slate-800 border border-slate-700/80 rounded-lg p-3 text-xs flex justify-between items-center">
                            <span className="text-slate-200 font-medium">{claim}</span>
                            <span className={`px-2 py-0.5 rounded font-mono text-[11px] ${
                              verified
                                ? 'bg-emerald-950/80 border border-emerald-800 text-emerald-300'
                                : 'bg-rose-950/80 border border-rose-800 text-rose-300'
                            }`}>
                              {verified ? `Verified (${source})` : 'Unverified'}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <ShieldCheck size={36} className="mx-auto mb-2 text-slate-500" />
                <h3 className="text-lg font-bold text-white mb-1">Review Pending</h3>
                <p className="text-sm">Final QA and verification checks will be presented after proposal generation.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
