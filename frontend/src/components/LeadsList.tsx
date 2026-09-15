import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { Lead, LeadStatus } from '../types';
import {
  Loader,
  AlertCircle,
  ArrowRight,
  Trash2,
  Search,
  CheckCircle2,
  HelpCircle,
  AlertTriangle,
  Building2,
  Calendar,
  Layers,
  Sparkles,
  PlusCircle,
  BarChart3,
} from 'lucide-react';

const LeadsList: React.FC = () => {
  const navigate = useNavigate();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<LeadStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const api = useApi();

  const handleDelete = async (event: React.MouseEvent, lead: Lead) => {
    event.stopPropagation();
    const name = lead.company_name || 'this lead';
    if (!window.confirm(`Delete ${name}? This cannot be undone.`)) return;

    try {
      await api.deleteLead(lead.id);
      setLeads(currentLeads => currentLeads.filter(item => item.id !== lead.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete lead');
    }
  };

  useEffect(() => {
    const fetchLeads = async () => {
      try {
        setLoading(true);
        const result = await api.listLeads(0, 50, filter === 'all' ? undefined : filter);
        setLeads(Array.isArray(result?.leads) ? result.leads : []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load leads');
      } finally {
        setLoading(false);
      }
    };

    fetchLeads();
  }, [filter]);

  // Client-side quick search filtering
  const filteredLeads = useMemo(() => {
    if (!searchQuery.trim()) return leads;
    const q = searchQuery.toLowerCase();
    return leads.filter(
      lead =>
        (lead.company_name && lead.company_name.toLowerCase().includes(q)) ||
        (lead.inquiry_text && lead.inquiry_text.toLowerCase().includes(q)) ||
        (lead.contact_name && lead.contact_name.toLowerCase().includes(q)) ||
        (lead.industry && lead.industry.toLowerCase().includes(q))
    );
  }, [leads, searchQuery]);

  // Calculate metrics across loaded leads
  const stats = useMemo(() => {
    const total = leads.length;
    const qualified = leads.filter(l => l.lead_status === LeadStatus.Qualified).length;
    const needsInfo = leads.filter(l => l.lead_status === LeadStatus.NeedsInfo).length;
    const lowPriority = leads.filter(l => l.lead_status === LeadStatus.LowPriority).length;
    return { total, qualified, needsInfo, lowPriority };
  }, [leads]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case LeadStatus.Qualified:
      case 'Qualified':
        return {
          pill: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
          dot: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]',
          border: 'hover:border-emerald-500/40',
          icon: <CheckCircle2 size={13} className="text-emerald-400" />,
        };
      case LeadStatus.NeedsInfo:
      case 'Needs More Information':
        return {
          pill: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
          dot: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]',
          border: 'hover:border-amber-500/40',
          icon: <HelpCircle size={13} className="text-amber-400" />,
        };
      case LeadStatus.LowPriority:
      case 'Low Priority':
        return {
          pill: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
          dot: 'bg-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.8)]',
          border: 'hover:border-rose-500/40',
          icon: <AlertTriangle size={13} className="text-rose-400" />,
        };
      default:
        return {
          pill: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
          dot: 'bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.8)]',
          border: 'hover:border-blue-500/40',
          icon: <Loader size={13} className="animate-spin text-blue-400" />,
        };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <div className="relative inline-flex items-center justify-center">
            <div className="w-16 h-16 rounded-full border-2 border-indigo-500/30 border-t-indigo-400 animate-spin" />
            <Sparkles className="absolute text-cyan-400 animate-pulse" size={24} />
          </div>
          <p className="text-slate-200 font-medium tracking-wide">Syncing leads from PostgreSQL database...</p>
          <p className="text-slate-400 text-xs font-mono">Querying opportunities • Calculating scores</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 4-Metric Live Counter Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Leads */}
        <div className="glass-panel p-4 rounded-xl border border-white/[0.08] relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-blue-500/20 transition" />
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-medium">Total Pipeline</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Layers size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-white">{stats.total}</span>
            <span className="text-xs text-slate-400">Leads</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Recorded in system</p>
        </div>

        {/* Qualified */}
        <div className="glass-panel p-4 rounded-xl border border-emerald-500/20 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-emerald-500/20 transition" />
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider text-emerald-300 font-medium">Qualified</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-emerald-400">{stats.qualified}</span>
            <span className="text-xs text-emerald-500/80">Ready to close</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Score &ge; 75% threshold</p>
        </div>

        {/* Needs More Info */}
        <div className="glass-panel p-4 rounded-xl border border-amber-500/20 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-amber-500/20 transition" />
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider text-amber-300 font-medium">Needs Info</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <HelpCircle size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-amber-400">{stats.needsInfo}</span>
            <span className="text-xs text-amber-500/80">Follow-up req.</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Requires user context</p>
        </div>

        {/* Low Priority */}
        <div className="glass-panel p-4 rounded-xl border border-rose-500/20 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-rose-500/20 transition" />
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider text-rose-300 font-medium">Low Priority</span>
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <AlertTriangle size={16} />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-rose-400">{stats.lowPriority}</span>
            <span className="text-xs text-rose-500/80">Deprioritized</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Score &lt; 50% threshold</p>
        </div>
      </div>

      {/* Main Glass Workspace */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/[0.08]">
        {/* Title Bar and Search */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 text-indigo-400">
                <BarChart3 size={22} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">Sales Pipeline & Leads</h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Live AI-qualified customer opportunities stored in PostgreSQL
                </p>
              </div>
            </div>
          </div>

          {/* Quick Actions & Search */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div className="relative min-w-[240px]">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input
                type="text"
                placeholder="Search leads, companies..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900/60 border border-white/10 rounded-xl pl-10 pr-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/20 transition"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-white"
                >
                  ✕
                </button>
              )}
            </div>

            <button
              type="button"
              onClick={() => navigate('/')}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:via-indigo-500 hover:to-purple-500 text-white text-sm font-semibold shadow-lg shadow-indigo-500/25 transition cursor-pointer active:scale-95"
            >
              <PlusCircle size={16} />
              <span>New Lead</span>
            </button>
          </div>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex gap-2 my-6 flex-wrap">
          {(['all', LeadStatus.Qualified, LeadStatus.NeedsInfo, LeadStatus.LowPriority] as const).map(status => {
            const isActive = filter === status;
            return (
              <button
                key={status}
                type="button"
                onClick={() => setFilter(status)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition cursor-pointer active:scale-95 border ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-400/40 shadow-lg shadow-indigo-500/30'
                    : 'bg-slate-900/50 text-slate-300 border-white/[0.08] hover:bg-slate-800/80 hover:text-white'
                }`}
              >
                {status === 'all' ? 'All Opportunities' : status}
              </button>
            );
          })}
        </div>

        {error && (
          <div className="mb-6 bg-red-950/30 border border-red-500/40 rounded-xl p-4 flex items-center gap-3 text-red-200 text-sm">
            <AlertCircle className="text-red-400 flex-shrink-0" size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Lead Cards List */}
        {filteredLeads.length === 0 ? (
          <div className="text-center py-16 px-4 rounded-2xl border border-dashed border-white/10 bg-slate-900/30">
            <div className="w-14 h-14 mx-auto mb-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Sparkles size={24} />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">
              {searchQuery ? 'No matching leads found' : 'No sales leads in this category'}
            </h3>
            <p className="text-slate-400 text-sm max-w-md mx-auto mb-5">
              {searchQuery
                ? `No leads matched your query "${searchQuery}". Try clearing your search.`
                : 'Submit a new customer inquiry or upload an RFQ PDF to initiate qualification.'}
            </p>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition cursor-pointer shadow-lg shadow-indigo-500/20"
            >
              <PlusCircle size={16} /> Qualify New Opportunity
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3.5">
            {filteredLeads.map(lead => {
              const badge = getStatusBadge(lead.lead_status);
              const score = typeof lead.composite_score === 'number' ? Math.round(lead.composite_score) : null;

              return (
                <div
                  key={lead.id}
                  onClick={() => navigate(`/lead/${lead.id}`)}
                  className={`glass-card p-5 rounded-xl border border-white/[0.08] hover:border-indigo-500/40 hover:bg-slate-800/60 cursor-pointer transition-all duration-200 group flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${badge.border}`}
                >
                  {/* Left Column: Lead Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2.5 mb-1.5">
                      <div className="p-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-slate-300">
                        <Building2 size={16} />
                      </div>
                      <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition truncate">
                        {lead.company_name || 'Unnamed Opportunity'}
                      </h3>
                      {lead.industry && (
                        <span className="text-[11px] px-2 py-0.5 rounded-md bg-white/[0.04] text-slate-400 border border-white/[0.06]">
                          {lead.industry}
                        </span>
                      )}
                    </div>

                    <p className="text-slate-400 text-xs line-clamp-2 leading-relaxed max-w-2xl">
                      {lead.inquiry_text || 'No inquiry text provided'}
                    </p>

                    <div className="flex items-center gap-4 text-[11px] text-slate-500 mt-3">
                      <span className="flex items-center gap-1.5">
                        <Calendar size={12} className="text-slate-400" />
                        {new Date(lead.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>
                      {lead.contact_name && (
                        <span>• Contact: <strong className="text-slate-400 font-medium">{lead.contact_name}</strong></span>
                      )}
                      <span className="font-mono text-[10px] text-slate-400 hidden md:inline">
                        ID: {lead.id.slice(0, 8)}...
                      </span>
                    </div>
                  </div>

                  {/* Right Column: Score, Status & Actions */}
                  <div className="flex items-center gap-4 justify-between sm:justify-end shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-white/[0.05]">
                    {/* Status Pill & Indicators */}
                    <div className="flex flex-col items-start sm:items-end gap-1.5">
                      <div className="flex items-center gap-2">
                        {lead.lead_status === LeadStatus.NeedsInfo && score !== null && score >= 75 && (
                          <span
                            className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/30"
                            title="Opportunity has high score (>=75) but requires missing commercial information before marking as Qualified"
                          >
                            High Fit • Info Needed
                          </span>
                        )}
                        <span
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border backdrop-blur-md ${badge.pill}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                          {badge.icon}
                          <span>{lead.lead_status}</span>
                        </span>
                      </div>

                      {/* Score Indicator */}
                      {score !== null && (
                        <div className="text-xs text-slate-400 flex items-center gap-1.5">
                          <span>Lead Score:</span>
                          <span
                            className={`font-black ${
                              score >= 75
                                ? 'text-emerald-400'
                                : score >= 50
                                ? 'text-amber-400'
                                : 'text-rose-400'
                            }`}
                          >
                            {score}/100
                          </span>
                          {typeof lead.fit_score === 'number' && (
                            <span className="text-[10px] text-slate-500 font-mono" title="Product Fit component">
                              (Fit {Math.round(lead.fit_score)}%)
                            </span>
                          )}
                        </div>
                      )}

                      {/* Missing info count helper */}
                      {lead.lead_status === LeadStatus.NeedsInfo && lead.missing_information && lead.missing_information.length > 0 && (
                        <div
                          className="text-[10px] text-amber-400/90 flex items-center gap-1 cursor-help"
                          title={`Missing required customer data: ${lead.missing_information.join(', ')}`}
                        >
                          <AlertTriangle size={10} className="text-amber-400" />
                          <span>{lead.missing_information.length} details missing to qualify</span>
                        </div>
                      )}
                    </div>

                    {/* Action Controls */}
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={(event) => handleDelete(event, lead)}
                        className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition cursor-pointer active:scale-90"
                        aria-label={`Delete ${lead.company_name || 'lead'}`}
                        title="Delete lead"
                      >
                        <Trash2 size={16} />
                      </button>

                      <div className="p-2 text-slate-400 group-hover:text-cyan-400 group-hover:translate-x-1 transition duration-200">
                        <ArrowRight size={18} />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default LeadsList;

