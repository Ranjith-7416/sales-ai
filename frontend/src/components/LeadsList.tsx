import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { Lead, LeadStatus } from '../types';
import { Loader, AlertCircle, ArrowRight, Trash2 } from 'lucide-react';

const LeadsList: React.FC = () => {
  const navigate = useNavigate();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<LeadStatus | 'all'>('all');

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

  const getStatusColor = (status: LeadStatus) => {
    switch (status) {
      case LeadStatus.Qualified:
        return 'bg-green-100 text-green-800';
      case LeadStatus.NeedsInfo:
        return 'bg-yellow-100 text-yellow-800';
      case LeadStatus.LowPriority:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <Loader className="animate-spin mx-auto mb-4 text-blue-500" size={40} />
          <p className="text-white">Loading leads...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h1 className="text-3xl font-bold text-white mb-6">All Leads</h1>

        {/* Filters */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {(['all', LeadStatus.Qualified, LeadStatus.NeedsInfo, LeadStatus.LowPriority] as const).map(status => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {status === 'all' ? 'All Leads' : status}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-700 rounded-lg p-4 flex gap-3">
            <AlertCircle className="text-red-500 flex-shrink-0" size={20} />
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {leads.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-slate-400 text-lg">No leads found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {leads.map(lead => (
              <div
                key={lead.id}
                onClick={() => navigate(`/lead/${lead.id}`)}
                className="bg-slate-700 hover:bg-slate-600 rounded-lg p-4 cursor-pointer transition flex items-center justify-between"
              >
                <div>
                  <h3 className="text-white font-semibold">
                    {lead.company_name || 'Unnamed Lead'}
                  </h3>
                  <p className="text-slate-400 text-sm mt-1">
                    {(lead.inquiry_text || 'No inquiry provided').substring(0, 100)}...
                  </p>
                  <p className="text-slate-500 text-xs mt-2">
                    Created: {new Date(lead.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(lead.lead_status as LeadStatus)}`}>
                      {lead.lead_status}
                    </span>
                    {typeof lead.composite_score === 'number' && (
                      <p className="text-slate-300 font-bold mt-2">{lead.composite_score.toFixed(0)}</p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={(event) => handleDelete(event, lead)}
                    className="rounded-lg p-2 text-slate-400 hover:bg-red-900/40 hover:text-red-300"
                    aria-label={`Delete ${lead.company_name || 'lead'}`}
                    title="Delete lead"
                  >
                    <Trash2 size={18} />
                  </button>
                  <ArrowRight className="text-slate-400" size={20} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LeadsList;
