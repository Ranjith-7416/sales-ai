import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { Lead, LeadInput, LeadStatus, ResearchResult, RequirementResult, QualificationResult, SolutionMatchingResult, ProposalResult, ReviewerResult } from '../types';
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
  User,
  Mail,
  Briefcase,
  Users,
  DollarSign,
  Calendar,
  Activity,
  Layers,
  FileDown,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';

import { API_BASE_URL } from '../config';

// Radial SVG Gauge for Lead Qualification Score

const ScoreDial: React.FC<{ score: number; status: string }> = ({ score, status }) => {
  const clamped = Math.min(100, Math.max(0, score || 0));
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (clamped / 100) * circumference;

  const color =
    status === LeadStatus.Qualified || clamped >= 75
      ? '#10b981' // emerald
      : status === LeadStatus.NeedsInfo || clamped >= 50
      ? '#f59e0b' // amber
      : '#f43f5e'; // rose

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 96 96">
        {/* Background track */}
        <circle
          cx="48"
          cy="48"
          r={radius}
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth="7"
          fill="transparent"
        />
        {/* Dynamic progress ring */}
        <circle
          cx="48"
          cy="48"
          r={radius}
          stroke={color}
          strokeWidth="7"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className="text-xl font-black text-white tracking-tight" style={{ color }}>
          {status === LeadStatus.NeedsInfo && clamped === 0 ? '—' : clamped}
        </span>
        <span className="text-[9px] uppercase tracking-wider text-slate-400 font-medium">
          Fit Score
        </span>
      </div>
    </div>
  );
};

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
  const [generatingProposal, setGeneratingProposal] = useState(false);
  const [proposalNotification, setProposalNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);
  const [showSendModal, setShowSendModal] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [smtpStatus, setSmtpStatus] = useState<{
    configured: boolean;
    active_provider?: string;
    has_http_api?: boolean;
    smtp_user?: string;
    smtp_host?: string;
    is_render?: boolean;
    render_free_smtp_blocked?: boolean;
  } | null>(null);
  const [showSmtpDrawer, setShowSmtpDrawer] = useState(false);
  const [smtpTab, setSmtpTab] = useState<'http' | 'smtp'>('http');
  const [resendApiKey, setResendApiKey] = useState('');
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');
  const [savingSmtp, setSavingSmtp] = useState(false);
  const [sendModalNotification, setSendModalNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

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
        if (
          data.proposal_result?.proposal_status === 'approved' ||
          data.proposal_result?.status === 'approved'
        ) {
          setApprovedSuccess(true);
        }

        // Poll if still processing
        if (data.status !== 'completed') {
          const interval = setInterval(async () => {
            try {
              const updated = await api.getLead(leadId);
              if (!isMounted) return;
              setLead(updated);
              if (
                updated.proposal_result?.proposal_status === 'approved' ||
                updated.proposal_result?.status === 'approved'
              ) {
                setApprovedSuccess(true);
              }
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
      <div className="flex items-center justify-center min-h-[420px]">
        <div className="text-center space-y-4">
          <div className="relative inline-flex items-center justify-center">
            <div className="w-16 h-16 rounded-full border-2 border-indigo-500/30 border-t-indigo-400 animate-spin" />
            <Sparkles className="absolute text-cyan-400 animate-pulse" size={24} />
          </div>
          <p className="text-white text-lg font-medium tracking-wide">Analyzing sales lead through AI pipeline...</p>
          <p className="text-slate-400 text-xs font-mono">Extracting requirements • Searching product KB • Synthesizing proposal</p>
        </div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="glass-panel border border-red-500/30 rounded-2xl p-8 flex gap-4 text-red-200">
        <AlertCircle className="text-red-400 flex-shrink-0" size={28} />
        <div>
          <h3 className="text-red-100 font-bold text-lg">Error Loading Lead Record</h3>
          <p className="text-red-300/80 text-sm mt-1">{error || 'Lead record not found in PostgreSQL database.'}</p>
          <button
            type="button"
            onClick={() => navigate('/leads')}
            className="mt-4 px-4 py-2 bg-red-900/40 hover:bg-red-800/60 border border-red-700/60 text-white rounded-xl text-xs font-semibold transition cursor-pointer active:scale-95"
          >
            Return to All Leads
          </button>
        </div>
      </div>
    );
  }

  const qualification = (lead.result?.qualification || lead.result?.qualification_result || (lead as any).qualification_result || lead.result?.results?.qualification) as QualificationResult | undefined;
  const research = (lead.result?.research || lead.result?.research_result || (lead as any).research_result || lead.result?.results?.research) as ResearchResult | undefined;
  const requirements = (lead.result?.requirements || lead.result?.requirements_result || (lead as any).requirements_result || lead.result?.results?.requirements) as RequirementResult | undefined;
  const solution = (lead.result?.solution_matching || lead.result?.solution_matching_result || (lead as any).solution_matching_result || lead.result?.results?.solution_matching) as SolutionMatchingResult | undefined;
  const proposal = (lead.result?.proposal || lead.result?.proposal_result || (lead as any).proposal_result || lead.result?.results?.proposal) as ProposalResult | undefined;
  const review = (lead.result?.reviewer || lead.result?.reviewer_result || (lead as any).reviewer_result || lead.result?.results?.reviewer) as ReviewerResult | undefined;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Qualified':
      case LeadStatus.Qualified:
        return {
          pill: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
          dot: 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]',
          icon: <CheckCircle2 size={16} className="text-emerald-400" />,
          label: 'Qualified Lead',
        };
      case 'Needs More Information':
      case LeadStatus.NeedsInfo:
        return {
          pill: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
          dot: 'bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.8)]',
          icon: <HelpCircle size={16} className="text-amber-400" />,
          label: 'Needs More Information',
        };
      case 'Low Priority':
      case LeadStatus.LowPriority:
        return {
          pill: 'bg-rose-500/10 border-rose-500/30 text-rose-300',
          dot: 'bg-rose-400 shadow-[0_0_10px_rgba(244,63,94,0.8)]',
          icon: <AlertTriangle size={16} className="text-rose-400" />,
          label: 'Low Priority',
        };
      default:
        return {
          pill: 'bg-blue-500/10 border-blue-500/30 text-blue-300',
          dot: 'bg-blue-400 shadow-[0_0_10px_rgba(96,165,250,0.8)]',
          icon: <Loader size={16} className="animate-spin text-blue-400" />,
          label: status || 'Processing Pipeline',
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

  // 6 Pipeline Stages definition
  const pipelineStages = [
    { key: 'research', label: '1. Research' },
    { key: 'requirements', label: '2. Requirements' },
    { key: 'qualification', label: '3. Qualification' },
    { key: 'solution_matching', label: '4. Solutions' },
    { key: 'proposal', label: '5. Proposal' },
    { key: 'reviewer', label: '6. QA Review' },
  ];

  const isCompleted = lead.status === 'completed';
  const completedStages = new Set(lead.stages_completed || (isCompleted ? pipelineStages.map(s => s.key) : []));

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

  const isProposalApproved =
    approvedSuccess ||
    lead?.proposal_result?.proposal_status === 'approved' ||
    lead?.proposal_result?.status === 'approved';

  const getErrorMessage = (err: any, fallback: string): string => {
    if (!err) return fallback;
    const detail = err?.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item: any) => (typeof item === 'string' ? item : item?.msg || item?.message || JSON.stringify(item)))
        .join(', ');
    }
    if (detail && typeof detail === 'object') {
      return detail.message || detail.msg || JSON.stringify(detail);
    }
    return err?.message || fallback;
  };

  const handleGenerateProposal = async (regenerate: boolean = false) => {
    if (!leadId) return;
    setGeneratingProposal(true);
    setProposalNotification(null);
    try {
      const res = await api.generateProposal(leadId, regenerate);
      const generated = res?.proposal;
      if (generated) {
        setLead((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            proposal_result: generated,
            result: prev.result
              ? {
                  ...prev.result,
                  proposal_result: generated,
                  proposal: generated,
                }
              : {
                  proposal_result: generated,
                  proposal: generated,
                },
          };
        });
        setProposalNotification({
          type: 'success',
          message: regenerate
            ? '✨ Grounded proposal regenerated successfully from updated requirements.'
            : '✨ Grounded proposal generated successfully and ready for review/approval.',
        });
      }
    } catch (err: any) {
      console.error('Generation failed:', err);
      const errMsg = getErrorMessage(err, 'Failed to generate proposal');
      setProposalNotification({
        type: 'error',
        message: `Failed to generate proposal: ${errMsg}`,
      });
    } finally {
      setGeneratingProposal(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!leadId) return;
    setApproving(true);
    setProposalNotification(null);
    try {
      const res = await api.approveProposal(leadId, 'Sales AI Reviewer');
      setApprovedSuccess(true);

      const returnedProposal = res?.proposal;

      // Instantly update local state with returned approved proposal
      setLead((prev) => {
        if (!prev) return prev;
        const baseProposal = returnedProposal || prev.proposal_result || prev.result?.proposal_result || {};
        const updatedProposal = {
          ...baseProposal,
          proposal_status: 'approved',
          status: 'approved',
          approved_by: res?.approved_by || 'Sales AI Reviewer',
          approved_at: res?.approved_at || new Date().toISOString(),
        };

        return {
          ...prev,
          lead_status: 'Qualified',
          proposal_result: updatedProposal,
          result: prev.result
            ? {
                ...prev.result,
                proposal_result: updatedProposal,
                proposal: updatedProposal,
              }
            : {
                proposal_result: updatedProposal,
                proposal: updatedProposal,
              },
        };
      });

      setProposalNotification({
        type: 'success',
        message: '🎉 Proposal approved successfully! Recorded in database and ready for client delivery.',
      });
    } catch (err: any) {
      console.error('Approval failed:', err);
      const errMsg = getErrorMessage(err, 'Failed to approve proposal');
      setProposalNotification({
        type: 'error',
        message: `Failed to approve proposal: ${errMsg}`,
      });
    } finally {
      setApproving(false);
    }
  };

  const handleOpenSendModal = async () => {
    const defaultEmail = lead?.email || (lead?.company_name ? `contact@${lead.company_name.toLowerCase().replace(/[^a-z0-9]/g, '')}.com` : 'client@enterprise.com');
    setRecipientEmail(defaultEmail);
    setSendModalNotification(null);
    setShowSendModal(true);
    try {
      const smtpInfo = await api.getSmtpConfig();
      setSmtpStatus(smtpInfo);
      if (smtpInfo?.smtp_user) setSmtpUser(smtpInfo.smtp_user);
      if (!smtpInfo?.configured) {
        setShowSmtpDrawer(true);
      }
    } catch (e) {
      setShowSmtpDrawer(true);
    }
  };

  const handleSendProposal = async () => {
    const target = (recipientEmail || '').trim();
    if (!leadId || !target) return;

    setSendModalNotification(null);

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(target)) {
      const msg = 'Please enter a valid recipient email address (e.g. client@company.com).';
      setSendModalNotification({
        type: 'error',
        message: msg,
      });
      setProposalNotification({
        type: 'error',
        message: msg,
      });
      return;
    }

    // Check if SMTP is configured before attempting send
    if (smtpStatus && !smtpStatus.configured) {
      setShowSmtpDrawer(true);
      const msg = 'Live SMTP is not configured. Please enter your sender Gmail address and 16-character App Password below, click "Save & Enable SMTP Delivery", and then transmit.';
      setSendModalNotification({
        type: 'error',
        message: msg,
      });
      return;
    }

    setSendingEmail(true);
    try {
      const res = await api.sendProposal(leadId, target);
      if (res?.success) {
        const successMsg = `Email accepted for delivery to ${target}! (Message-ID: ${res.message_id || 'dispatched'})`;
        setSendModalNotification({
          type: 'success',
          message: successMsg,
        });
        setProposalNotification({
          type: 'success',
          message: successMsg,
        });
        setLead((prev) => {
          if (!prev) return prev;
          const updatedProposal = prev.proposal_result
            ? {
                ...prev.proposal_result,
                proposal_status: 'sent',
                status: 'sent',
                sent_to: target,
                sent_at: res.sent_at || new Date().toISOString(),
                delivery_mode: res.delivery_mode,
                message_id: res.message_id,
              }
            : prev.proposal_result;
          return {
            ...prev,
            proposal_result: updatedProposal,
          };
        });

        // Close modal after brief delay so user can see transmission confirmation
        setTimeout(() => {
          setShowSendModal(false);
          setSendModalNotification(null);
        }, 2200);
      } else {
        const errMsg = res?.message || 'Email could not be sent. Please check recipient address or email configuration.';
        setSendModalNotification({
          type: 'error',
          message: errMsg,
        });
        setProposalNotification({
          type: 'error',
          message: errMsg,
        });
        if (errMsg.includes('SMTP') || errMsg.includes('configured')) {
          setShowSmtpDrawer(true);
        }
      }
    } catch (err: any) {
      console.error('Send failed:', err);
      const serverMsg = err.response?.data?.message || err.response?.data?.error || err.message;
      const finalMsg = serverMsg || 'Email delivery failed. Please check SMTP settings or recipient email.';
      setSendModalNotification({
        type: 'error',
        message: finalMsg,
      });
      setProposalNotification({
        type: 'error',
        message: finalMsg,
      });
      if (finalMsg.includes('Render') || finalMsg.includes('101') || finalMsg.includes('unreachable')) {
        setSmtpTab('http');
        setShowSmtpDrawer(true);
      } else if (finalMsg.includes('SMTP') || finalMsg.includes('configured') || finalMsg.includes('Missing')) {
        setShowSmtpDrawer(true);
      }
    } finally {
      setSendingEmail(false);
    }
  };

  const handleSaveResendConfig = async () => {
    if (!resendApiKey.trim()) {
      setSendModalNotification({
        type: 'error',
        message: 'Please enter a valid Resend API Key (starts with re_...).',
      });
      return;
    }
    try {
      setSavingSmtp(true);
      setSendModalNotification(null);
      await api.updateSmtpConfig({
        resend_api_key: resendApiKey.trim(),
      });
      setSmtpStatus((prev) => ({
        configured: true,
        active_provider: 'resend_api',
        has_http_api: true,
        ...prev,
      }));
      setShowSmtpDrawer(false);
      setSendModalNotification({
        type: 'success',
        message: '✅ Resend API enabled over port 443! Ready for live delivery on Render. Click "Confirm & Send".',
      });
      setProposalNotification({
        type: 'success',
        message: 'Resend API enabled over port 443. Ready for live email delivery.',
      });
    } catch (err: any) {
      const errMsg = getErrorMessage(err, 'Failed to save Resend configuration');
      setSendModalNotification({
        type: 'error',
        message: `Failed to save Resend API key: ${errMsg}`,
      });
    } finally {
      setSavingSmtp(false);
    }
  };

  const handleSaveSmtp = async () => {
    if (!smtpUser.trim() || !smtpPassword.trim()) {
      setSendModalNotification({
        type: 'error',
        message: 'Please enter both your Gmail address and 16-character App Password.',
      });
      return;
    }
    try {
      setSavingSmtp(true);
      setSendModalNotification(null);
      await api.updateSmtpConfig({
        smtp_host: 'smtp.gmail.com',
        smtp_port: 587,
        smtp_user: smtpUser.trim(),
        smtp_password: smtpPassword.trim(),
        smtp_from_email: smtpUser.trim(),
        smtp_use_tls: true,
      });
      setSmtpStatus((prev) => ({
        configured: true,
        active_provider: 'smtp',
        smtp_user: smtpUser.trim(),
        smtp_host: 'smtp.gmail.com',
        ...prev,
      }));
      setShowSmtpDrawer(false);
      setSendModalNotification({
        type: 'success',
        message: '✅ SMTP credentials saved! Note: On Render Free Tier, port 587 may be blocked by the host. If delivery fails with Errno 101, use the free Resend API tab.',
      });
      setProposalNotification({
        type: 'success',
        message: 'SMTP credentials updated successfully.',
      });
    } catch (err: any) {
      const errMsg = getErrorMessage(err, 'Failed to save SMTP configuration');
      setSendModalNotification({
        type: 'error',
        message: `Failed to save SMTP configuration: ${errMsg}`,
      });
    } finally {
      setSavingSmtp(false);
    }
  };

  const numericScore = qualification?.composite_score ?? 0;

  return (
    <div className="space-y-6">
      {/* Top Banner & Opportunity Hero Card */}
      <div className="glass-panel border border-white/[0.08] rounded-2xl p-6 sm:p-8 relative overflow-hidden">
        {/* Glow ambient highlight */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-white/[0.08]">
          {/* Company Title & ID */}
          <div className="flex items-start sm:items-center gap-5">
            {/* Score Dial */}
            <ScoreDial score={numericScore} status={lead.lead_status} />

            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                  {lead.company_name || 'Customer Opportunity'}
                </h1>
                <div className={`inline-flex items-center gap-2 border rounded-full px-3.5 py-1 text-xs font-semibold backdrop-blur-md ${statusBadge.pill}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${statusBadge.dot}`} />
                  {statusBadge.icon}
                  <span>{statusBadge.label}</span>
                </div>
              </div>

              <p className="text-slate-400 text-xs mt-1.5 flex items-center gap-2 flex-wrap">
                <span className="font-mono text-slate-300">ID: {lead.id.slice(0, 8)}...</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Calendar size={12} className="text-slate-400" />
                  Received {new Date(lead.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                </span>
                <span>•</span>
                <span className="text-emerald-400 font-medium">PostgreSQL Sync: Live</span>
              </p>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={startEditing}
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 px-4 py-2 text-xs font-semibold text-white transition border border-white/[0.08] cursor-pointer active:scale-95"
            >
              <Edit3 size={14} className="text-indigo-400" /> Edit Lead Context
            </button>
            {proposal && (
              <button
                type="button"
                onClick={handleExportProposal}
                disabled={exporting}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 px-4 py-2 text-xs font-semibold text-white transition shadow-lg shadow-indigo-500/20 cursor-pointer active:scale-95"
              >
                <Download size={14} /> {exporting ? 'Exporting...' : 'Export Proposal (.md)'}
              </button>
            )}
          </div>
        </div>

        {/* 6 Context Blocks Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-6">
          <div className="glass-card p-3 rounded-xl border border-white/[0.06]">
            <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5 mb-1">
              <User size={12} className="text-cyan-400" /> Contact
            </span>
            <span className="text-white text-xs font-semibold truncate block">{lead.contact_name || 'Not provided'}</span>
          </div>

          <div className="glass-card p-3 rounded-xl border border-white/[0.06]">
            <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5 mb-1">
              <Mail size={12} className="text-blue-400" /> Email
            </span>
            <span className="text-white text-xs font-semibold truncate block">{lead.email || 'Not provided'}</span>
          </div>

          <div className="glass-card p-3 rounded-xl border border-white/[0.06]">
            <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5 mb-1">
              <Briefcase size={12} className="text-indigo-400" /> Industry
            </span>
            <span className="text-white text-xs font-semibold truncate block">{lead.industry || 'General'}</span>
          </div>

          <div className="glass-card p-3 rounded-xl border border-white/[0.06]">
            <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5 mb-1">
              <Users size={12} className="text-purple-400" /> Company Size
            </span>
            <span className="text-white text-xs font-semibold truncate block">{lead.company_size || 'To be confirmed'}</span>
          </div>

          <div className="glass-card p-3 rounded-xl border border-white/[0.06]">
            <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5 mb-1">
              <DollarSign size={12} className="text-emerald-400" /> Budget
            </span>
            <span className="text-white text-xs font-semibold truncate block">{lead.budget || 'To be confirmed'}</span>
          </div>

          <div className="glass-card p-3 rounded-xl border border-white/[0.06]">
            <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5 mb-1">
              <Clock size={12} className="text-amber-400" /> Timeline
            </span>
            <span className="text-white text-xs font-semibold truncate block">{lead.timeline || 'To be confirmed'}</span>
          </div>
        </div>

        {/* Lead Score Breakdown Cards */}
        {qualification && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-5">
            {/* Composite Score */}
            <div className="glass-card p-3.5 rounded-xl border border-indigo-500/30 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-indigo-300 uppercase tracking-wider font-semibold">Composite</span>
                <span className="text-[10px] text-slate-400 font-mono">100%</span>
              </div>
              <div className="text-2xl font-black text-indigo-400 mt-1">
                {formatScore(qualification.composite_score)}
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full transition-all duration-700"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.composite_score || 0))}%` }}
                />
              </div>
            </div>

            {/* Product Fit */}
            <div className="glass-card p-3.5 rounded-xl border border-emerald-500/20 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-emerald-300 uppercase tracking-wider font-semibold">Fit (25%)</span>
                <span className="text-[10px] text-emerald-500 font-mono">RAG Match</span>
              </div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                {formatScore(qualification.fit_score)}
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.fit_score || 0))}%` }}
                />
              </div>
            </div>

            {/* Readiness */}
            <div className="glass-card p-3.5 rounded-xl border border-amber-500/20 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-amber-300 uppercase tracking-wider font-semibold">Readiness (25%)</span>
                <span className="text-[10px] text-amber-500 font-mono">Intent</span>
              </div>
              <div className="text-2xl font-bold text-amber-400 mt-1">
                {formatScore(qualification.readiness_score)}
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-amber-500 to-yellow-400 h-full rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.readiness_score || 0))}%` }}
                />
              </div>
            </div>

            {/* Opportunity */}
            <div className="glass-card p-3.5 rounded-xl border border-purple-500/20 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-purple-300 uppercase tracking-wider font-semibold">Opportunity (30%)</span>
                <span className="text-[10px] text-purple-500 font-mono">Scale</span>
              </div>
              <div className="text-2xl font-bold text-purple-400 mt-1">
                {formatScore(qualification.opportunity_score)}
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.opportunity_score || 0))}%` }}
                />
              </div>
            </div>

            {/* Risk Level */}
            <div className="glass-card p-3.5 rounded-xl border border-rose-500/20 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-rose-300 uppercase tracking-wider font-semibold">Risk (20%)</span>
                <span className="text-[10px] text-rose-500 font-mono">Low is good</span>
              </div>
              <div className="text-2xl font-bold text-rose-400 mt-1">
                {Math.round(qualification.risk_score || 0)}
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-rose-500 to-red-400 h-full rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, qualification.risk_score || 0))}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Futuristic 6-Stage Pipeline Stepper */}
        <div className="mt-6 pt-5 border-t border-white/[0.08]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-1.5">
              <Activity size={13} className="text-indigo-400" />
              Autonomous Agent Pipeline Stages
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              {isCompleted ? 'Pipeline Complete (6/6)' : `Current: ${lead.current_stage || 'Processing'}`}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
            {pipelineStages.map((stage, idx) => {
              const done = isCompleted || completedStages.has(stage.key);
              const current = !isCompleted && lead.current_stage === stage.key;

              return (
                <div
                  key={stage.key}
                  className={`p-2.5 rounded-xl border text-xs flex items-center gap-2 transition ${
                    done
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                      : current
                      ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300 animate-pulse'
                      : 'bg-slate-900/40 border-white/[0.05] text-slate-500'
                  }`}
                >
                  {done ? (
                    <CheckCircle2 size={14} className="text-emerald-400 flex-shrink-0" />
                  ) : current ? (
                    <Loader size={14} className="animate-spin text-indigo-400 flex-shrink-0" />
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full border border-slate-600 text-[10px] flex items-center justify-center text-slate-400">
                      {idx + 1}
                    </span>
                  )}
                  <span className="truncate font-medium">{stage.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Inline Edit Form Modal */}
      {editing && (
        <form onSubmit={handleUpdate} className="glass-panel border border-indigo-500/40 rounded-2xl p-6 space-y-4 shadow-2xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Edit3 size={18} className="text-indigo-400" /> Update Opportunity Context & Re-evaluate
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
              className="bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
            />
            <input
              name="contact_name"
              value={editForm.contact_name || ''}
              onChange={(e) => setEditForm({ ...editForm, contact_name: e.target.value })}
              placeholder="Contact Person"
              className="bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
            />
            <input
              name="email"
              value={editForm.email || ''}
              onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
              placeholder="Email"
              className="bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
            />
            <input
              name="industry"
              value={editForm.industry || ''}
              onChange={(e) => setEditForm({ ...editForm, industry: e.target.value })}
              placeholder="Industry"
              className="bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
            />
            <input
              name="company_size"
              value={editForm.company_size || ''}
              onChange={(e) => setEditForm({ ...editForm, company_size: e.target.value })}
              placeholder="Company Size"
              className="bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
            />
            <input
              name="budget"
              value={editForm.budget || ''}
              onChange={(e) => setEditForm({ ...editForm, budget: e.target.value })}
              placeholder="Budget Range"
              className="bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
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
              className="w-full bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
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
              className="w-full bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="px-4 py-2 text-xs text-slate-300 hover:text-white bg-slate-800 rounded-xl transition cursor-pointer active:scale-95"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 px-4 py-2 text-xs font-semibold text-white transition cursor-pointer active:scale-95 shadow-lg shadow-emerald-500/20"
            >
              <Save size={14} /> Save and Re-run Pipeline
            </button>
          </div>
        </form>
      )}

      {/* Cyber Glass Navigation Tabs */}
      <div className="border-b border-white/[0.08]">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {[
            { id: 'overview', label: 'Overview & Score', icon: <Sparkles size={14} /> },
            { id: 'research', label: 'Web Research', icon: <Building2 size={14} /> },
            { id: 'requirements', label: 'Requirements', icon: <FileText size={14} /> },
            { id: 'solution', label: 'Solutions', icon: <Database size={14} /> },
            { id: 'proposal', label: 'Executive Proposal', icon: <FileDown size={14} /> },
            { id: 'review', label: 'QA & Review', icon: <ShieldCheck size={14} /> },
          ].map(tab => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2.5 rounded-xl font-semibold text-xs transition flex items-center gap-2 whitespace-nowrap cursor-pointer active:scale-95 border ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-400/40 shadow-lg shadow-indigo-500/25'
                    : 'bg-slate-900/50 text-slate-400 border-white/[0.06] hover:bg-slate-800/80 hover:text-white'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Panels with Glass Container */}
      <div className="glass-panel border border-white/[0.08] rounded-2xl p-6 sm:p-8 min-h-[450px]">

        {/* 1. OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Qualification Narrative */}
            {qualification && (
              <div className="glass-card p-6 rounded-2xl border border-indigo-500/30 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />
                <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Sparkles size={18} className="text-cyan-400" />
                  <span className="bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">
                    AI Qualification Reasoning & Strategy
                  </span>
                </h2>
                <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-line font-normal">
                  {qualification.qualification_reasoning}
                </p>
              </div>
            )}

            {/* Missing Information Callout */}
            {requirements?.missing_information && requirements.missing_information.length > 0 && (
              <div className="glass-card bg-amber-500/[0.04] border border-amber-500/30 rounded-2xl p-6 relative overflow-hidden">
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                    <HelpCircle size={16} />
                  </div>
                  <h3 className="text-sm font-bold text-amber-300">Information Needed to Accelerate Deal</h3>
                </div>
                <p className="text-xs text-amber-200/80 mb-4">
                  The following requirements were not fully specified in the customer inquiry. Click "Edit Lead Context" above to fill them in:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {requirements.missing_information.map((item, idx) => (
                    <div key={idx} className="bg-slate-900/60 border border-amber-500/20 rounded-xl p-3 text-xs text-amber-100 flex items-start gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0 shadow-[0_0_6px_rgba(251,191,36,0.8)]" />
                      <span className="leading-relaxed">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Score Drivers */}
            {qualification?.score_drivers && qualification.score_drivers.length > 0 && (
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                  <TrendingUp size={16} className="text-emerald-400" />
                  <span>Key Score Drivers & Evidence</span>
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {qualification.score_drivers.map((driver, idx) => {
                    const factor = Array.isArray(driver) ? driver[0] : (driver as any)?.factor || 'Driver';
                    const impact = Array.isArray(driver) ? driver[1] : (driver as any)?.impact || 'Positive';
                    return (
                      <div key={idx} className="glass-card p-4 rounded-xl border border-white/[0.08] hover:border-emerald-500/40 transition flex items-start gap-3">
                        <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mt-0.5">
                          <CheckCircle2 size={14} />
                        </div>
                        <div>
                          <p className="text-white font-semibold text-xs">{factor}</p>
                          <p className="text-slate-400 text-xs mt-0.5 leading-relaxed">{impact}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Original Customer Inquiry Preview */}
            <div className="glass-card p-5 rounded-2xl border border-white/[0.08]">
              <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">Original Customer Inquiry</h3>
              <blockquote className="text-slate-300 text-xs italic border-l-2 border-indigo-500/50 pl-3 leading-relaxed">
                "{lead.inquiry_text}"
              </blockquote>
            </div>
          </div>
        )}

        {/* 2. RESEARCH TAB */}
        {activeTab === 'research' && (
          <div className="space-y-6">
            {research ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="glass-card p-5 rounded-2xl border border-white/[0.08]">
                    <span className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block">Company & Industry</span>
                    <h3 className="text-lg font-bold text-white mt-1.5 flex items-center gap-2">
                      <Building2 size={18} className="text-cyan-400" />
                      {research.company_name}
                    </h3>
                    <p className="text-xs text-indigo-400 mt-1">{research.industry_vertical} • {research.company_size}</p>
                    <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-white/[0.06]">
                      <strong className="text-slate-300">Location:</strong> {research.location}
                    </p>
                  </div>

                  <div className="glass-card p-5 rounded-2xl border border-white/[0.08]">
                    <span className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block">Market Position & Model</span>
                    <p className="text-xs text-slate-200 mt-2 leading-relaxed">{research.business_model}</p>
                    <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-white/[0.06]">
                      <strong className="text-slate-300">Market Position:</strong> {research.market_position}
                    </p>
                  </div>
                </div>

                {research.recent_news && research.recent_news.length > 0 && (
                  <div className="glass-card p-5 rounded-2xl border border-white/[0.08]">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-white mb-3 flex items-center gap-2">
                      <Sparkles size={15} className="text-indigo-400" />
                      Public Intelligence & Recent Developments
                    </h3>
                    <ul className="space-y-2">
                      {research.recent_news.map((item, idx) => (
                        <li key={idx} className="text-xs text-slate-300 flex items-start gap-2.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 flex-shrink-0 shadow-[0_0_6px_rgba(6,182,212,0.8)]" />
                          <span className="leading-relaxed">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-16 text-slate-400">
                <Building2 size={36} className="mx-auto mb-2 text-slate-600" />
                <p className="text-sm">Public company research results will appear once the research agent completes.</p>
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
                  <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                    <FileText size={16} className="text-cyan-400" />
                    <span>Extracted Functional Requirements</span>
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {requirements.functional_requirements.map((req, idx) => (
                      <div key={idx} className="glass-card p-4 rounded-xl border border-white/[0.08] hover:border-cyan-500/40 transition flex items-start gap-3">
                        <div className="p-1 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mt-0.5">
                          <Check size={14} />
                        </div>
                        <span className="text-xs text-slate-200 leading-relaxed">{req}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {requirements.non_functional_requirements && Object.keys(requirements.non_functional_requirements).length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                      <Layers size={16} className="text-purple-400" />
                      <span>Non-Functional & Operational Requirements</span>
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      {Object.entries(requirements.non_functional_requirements).map(([k, v]) => (
                        <div key={k} className="glass-card p-4 rounded-xl border border-white/[0.08]">
                          <span className="text-[11px] font-semibold text-purple-400 uppercase tracking-wider block capitalize">{k}</span>
                          <span className="text-xs text-slate-200 mt-1.5 block font-medium">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {requirements.missing_information && requirements.missing_information.length > 0 && (
                  <div className="glass-card bg-amber-500/[0.04] border border-amber-500/30 rounded-2xl p-5">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-amber-300 mb-2 flex items-center gap-2">
                      <AlertTriangle size={14} className="text-amber-400" />
                      Unclear or Missing Requirements
                    </h3>
                    <div className="space-y-2 mt-3">
                      {requirements.missing_information.map((item, idx) => (
                        <div key={idx} className="text-xs text-amber-200/90 flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-16 text-slate-400">
                <FileText size={36} className="mx-auto mb-2 text-slate-600" />
                <p className="text-sm">Requirement analysis will populate when the pipeline runs.</p>
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
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <Database size={18} className="text-indigo-400" />
                    Recommended Solutions (Catalog-Grounded)
                  </h2>
                  <span className="inline-flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 px-3 py-1 rounded-full text-xs font-medium backdrop-blur-md">
                    <ShieldCheck size={14} className="text-emerald-400" /> Grounded in Knowledge Base
                  </span>
                </div>

                {solution.primary_solutions && solution.primary_solutions.map((sol, idx) => (
                  <div key={idx} className="glass-card p-6 rounded-2xl border border-white/[0.08] hover:border-indigo-500/40 transition space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.06] pb-4">
                      <div>
                        <h3 className="text-lg font-bold text-white">{sol.product_name}</h3>
                        <p className="text-[11px] text-slate-400 font-mono">Product ID: {sol.product_name.toLowerCase().replace(/[^a-z0-9]/g, '-')}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs px-3 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded-xl text-indigo-300 font-bold">
                          {sol.coverage_percentage}% Requirements Match
                        </span>
                        <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded-xl">
                          {formatCatalogPricing(sol.pricing)}
                        </span>
                      </div>
                    </div>

                    {/* Matched Features */}
                    {sol.features_matched && sol.features_matched.length > 0 && (
                      <div>
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">Verified Matched Capabilities</span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {sol.features_matched.map((feat, fidx) => (
                            <div key={fidx} className="bg-slate-900/50 p-2.5 rounded-xl text-xs text-slate-200 flex items-center gap-2 border border-white/[0.05]">
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
                  <div className="glass-card bg-indigo-500/[0.05] border border-indigo-500/30 rounded-2xl p-5 flex items-center justify-between">
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-indigo-300 block">Total Estimated Solution Value</span>
                      <span className="text-xl font-black text-white mt-1 block">
                        {formatCatalogPricing(solution.estimated_solution_value)}
                      </span>
                    </div>
                    <span className="text-xs text-slate-400">Strictly derived from catalog pricing tiers</span>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-16 text-slate-400">
                <Database size={36} className="mx-auto mb-2 text-slate-600" />
                <h3 className="text-base font-bold text-white mb-1">Solution Draft Pending</h3>
                <p className="text-xs">Grounded solutions will appear once the Solution Matching Agent completes.</p>
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
                <div className="glass-card p-4 rounded-2xl border border-white/[0.08] flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Status:</span>
                    <span
                      className={`text-xs px-3 py-1 rounded-full font-bold border transition ${
                        isProposalApproved
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-sm shadow-emerald-500/20'
                          : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                      }`}
                    >
                      {isProposalApproved ? 'Approved & Ready for Delivery ✓' : 'Grounded Draft Ready'}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={handleExportProposal}
                      disabled={exporting}
                      className="px-3 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95 shadow-lg shadow-indigo-500/20"
                    >
                      <Download size={14} /> Download (.md)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleGenerateProposal(true)}
                      disabled={generatingProposal || approving}
                      title="Re-generate proposal from latest requirements"
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/[0.08] rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95"
                    >
                      {generatingProposal ? (
                        <Loader size={14} className="animate-spin text-white" />
                      ) : (
                        <RefreshCw size={14} className="text-slate-400" />
                      )}
                      Regenerate
                    </button>
                    <button
                      type="button"
                      onClick={() => window.print()}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/[0.08] rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95"
                    >
                      <Printer size={14} /> Print / PDF
                    </button>
                    <button
                      type="button"
                      onClick={handleApproveProposal}
                      disabled={approving || isProposalApproved}
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                        isProposalApproved
                          ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-500/50 cursor-default'
                          : 'bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer active:scale-95 shadow-lg shadow-emerald-500/20'
                      }`}
                    >
                      {approving ? (
                        <>
                          <Loader size={14} className="animate-spin text-white" /> Approving...
                        </>
                      ) : isProposalApproved ? (
                        <>
                          <Check size={14} /> Approved ✓
                        </>
                      ) : (
                        <>
                          <Check size={14} /> Approve Proposal
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={handleOpenSendModal}
                      className="px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95 shadow-lg shadow-purple-500/20"
                    >
                      <Mail size={14} /> Send to Client
                    </button>
                    <a
                      href={`${API_BASE_URL}/proposals/${leadId}/email-view`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 text-indigo-300 hover:text-indigo-200 border border-indigo-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95"
                    >
                      <ExternalLink size={13} /> Preview Email
                    </a>
                  </div>
                </div>

                {/* Proposal Notification Toast / Banner */}
                {proposalNotification && (
                  <div
                    className={`p-3.5 rounded-xl border flex items-center justify-between text-xs transition-all duration-200 animate-in fade-in slide-in-from-top-2 ${
                      proposalNotification.type === 'success'
                        ? 'bg-emerald-950/70 border-emerald-500/40 text-emerald-200 shadow-lg shadow-emerald-900/20'
                        : proposalNotification.type === 'error'
                        ? 'bg-rose-950/70 border-rose-500/40 text-rose-200 shadow-lg shadow-rose-900/20'
                        : 'bg-blue-950/70 border-blue-500/40 text-blue-200'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 font-medium">
                      {proposalNotification.type === 'success' ? (
                        <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                      ) : proposalNotification.type === 'error' ? (
                        <AlertCircle size={16} className="text-rose-400 shrink-0" />
                      ) : (
                        <Sparkles size={16} className="text-blue-400 shrink-0" />
                      )}
                      <span>{proposalNotification.message}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setProposalNotification(null)}
                      className="text-slate-400 hover:text-white p-1 rounded-lg transition"
                    >
                      <X size={14} />
                    </button>
                  </div>
                )}

                {/* Proposal Content Body */}
                <div className="glass-card p-6 sm:p-8 rounded-2xl border border-white/[0.08] space-y-6">
                  {/* Executive Summary */}
                  <div>
                    <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                      <span className="text-indigo-400">1.</span> Executive Summary
                    </h2>
                    <p className="text-slate-200 text-xs leading-relaxed whitespace-pre-line bg-slate-900/60 p-4 rounded-xl border border-white/[0.05]">
                      {proposal.executive_summary}
                    </p>
                  </div>

                  {/* Proposed Solution */}
                  <div>
                    <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                      <span className="text-indigo-400">2.</span> Proposed Solution Architecture
                    </h2>
                    <p className="text-slate-200 text-xs leading-relaxed whitespace-pre-line bg-slate-900/60 p-4 rounded-xl border border-white/[0.05]">
                      {proposal.proposed_solution}
                    </p>
                  </div>

                  {/* Implementation Roadmap */}
                  {proposal.implementation_roadmap && proposal.implementation_roadmap.length > 0 && (
                    <div>
                      <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                        <span className="text-indigo-400">3.</span> Implementation Roadmap
                      </h2>
                      <div className="overflow-x-auto rounded-xl border border-white/[0.08]">
                        <table className="w-full text-left text-xs text-slate-300">
                          <thead className="bg-slate-900/80 text-slate-300 uppercase tracking-wider text-[10px]">
                            <tr>
                              <th className="p-3">Phase</th>
                              <th className="p-3">Estimated Duration</th>
                              <th className="p-3">Key Activities</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/[0.05] bg-slate-950/40">
                            {proposal.implementation_roadmap.map((item, idx) => (
                              <tr key={idx} className="hover:bg-white/[0.02] transition">
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
                      <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                        <span className="text-indigo-400">4.</span> Commercial & Investment Model
                      </h2>
                      <div className="bg-slate-900/60 border border-white/[0.05] rounded-xl p-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                          {Object.entries(proposal.pricing_proposal).map(([key, value]) => (
                            <div key={key} className="flex justify-between items-center py-2 border-b border-white/[0.04]">
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
                      <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                        <span className="text-indigo-400">5.</span> Service Levels & Compliance
                      </h2>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        {Object.entries(proposal.support_service_levels).map(([k, v]) => (
                          <div key={k} className="bg-slate-900/60 border border-white/[0.05] rounded-xl p-3.5 text-xs">
                            <span className="text-slate-400 uppercase tracking-wider block text-[10px]">{k.replace(/_/g, ' ')}</span>
                            <span className="text-slate-200 font-semibold mt-1 block">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-16 text-slate-400">
                <FileText size={36} className="mx-auto mb-2 text-slate-600" />
                <h3 className="text-base font-bold text-white mb-1">Proposal Draft Pending</h3>
                <p className="text-xs max-w-md mx-auto mb-5">
                  A proposal has not yet been generated for this lead. Click below to generate a catalog-grounded draft ready for review and delivery.
                </p>
                <button
                  type="button"
                  onClick={() => handleGenerateProposal(false)}
                  disabled={generatingProposal}
                  className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold inline-flex items-center gap-2 transition cursor-pointer active:scale-95 shadow-lg shadow-indigo-500/20"
                >
                  {generatingProposal ? (
                    <>
                      <Loader size={15} className="animate-spin text-white" /> Generating Grounded Proposal...
                    </>
                  ) : (
                    <>
                      <Sparkles size={15} className="text-amber-300" /> Generate Proposal Now
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* 6. REVIEW TAB */}
        {activeTab === 'review' && (
          <div className="space-y-6">
            {review ? (
              <>
                <div className="glass-card p-4 rounded-2xl border border-white/[0.08] flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                      <ShieldCheck size={18} className="text-cyan-400" />
                      Quality Assurance & Anti-Hallucination Review
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">Automated quality assurance against enterprise catalog grounding</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2.5">
                    <button
                      type="button"
                      onClick={handleApproveProposal}
                      disabled={approving || isProposalApproved}
                      className={`text-xs px-3.5 py-1.5 rounded-full font-bold border transition flex items-center gap-1.5 ${
                        isProposalApproved
                          ? 'bg-emerald-900/60 text-emerald-300 border-emerald-500/50 cursor-default'
                          : review.readiness_assessment?.ready_to_send
                          ? 'bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer active:scale-95 shadow-lg shadow-emerald-500/20'
                          : 'bg-amber-600 hover:bg-amber-500 text-white cursor-pointer active:scale-95 shadow-lg shadow-amber-500/20'
                      }`}
                    >
                      {approving ? (
                        <>
                          <Loader size={14} className="animate-spin text-white" /> Approving...
                        </>
                      ) : isProposalApproved ? (
                        <>
                          <Check size={14} /> Signed Off & Approved ✓
                        </>
                      ) : (
                        <>
                          <Check size={14} /> {review.readiness_assessment?.ready_to_send ? 'Ready for Customer Sign-off (Click to Approve)' : 'Approve & Sign Off'}
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={handleOpenSendModal}
                      className="px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95 shadow-lg shadow-purple-500/20"
                    >
                      <Mail size={14} /> Send to Client
                    </button>
                    <a
                      href={`${API_BASE_URL}/proposals/${leadId}/email-view`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 text-indigo-300 hover:text-indigo-200 border border-indigo-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95"
                    >
                      <ExternalLink size={13} /> Preview Email
                    </a>
                  </div>
                </div>

                {/* Review Notification Toast / Banner */}
                {proposalNotification && (
                  <div
                    className={`p-3.5 rounded-xl border flex items-center justify-between text-xs transition-all duration-200 animate-in fade-in slide-in-from-top-2 ${
                      proposalNotification.type === 'success'
                        ? 'bg-emerald-950/70 border-emerald-500/40 text-emerald-200 shadow-lg shadow-emerald-900/20'
                        : proposalNotification.type === 'error'
                        ? 'bg-rose-950/70 border-rose-500/40 text-rose-200 shadow-lg shadow-rose-900/20'
                        : 'bg-blue-950/70 border-blue-500/40 text-blue-200'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 font-medium">
                      {proposalNotification.type === 'success' ? (
                        <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                      ) : proposalNotification.type === 'error' ? (
                        <AlertCircle size={16} className="text-rose-400 shrink-0" />
                      ) : (
                        <Sparkles size={16} className="text-blue-400 shrink-0" />
                      )}
                      <span>{proposalNotification.message}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setProposalNotification(null)}
                      className="text-slate-400 hover:text-white p-1 rounded-lg transition"
                    >
                      <X size={14} />
                    </button>
                  </div>
                )}

                {/* Follow-up Questions */}
                {review.follow_up_questions && review.follow_up_questions.length > 0 && (
                  <div className="glass-card p-5 rounded-2xl border border-white/[0.08]">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-white mb-3 flex items-center gap-2">
                      <HelpCircle size={15} className="text-cyan-400" />
                      Follow-up Questions for Customer
                    </h3>
                    <div className="space-y-2.5">
                      {review.follow_up_questions.map((q, idx) => (
                        <div key={idx} className="bg-slate-900/60 border border-white/[0.05] rounded-xl p-3 text-xs text-slate-200 flex items-start gap-2.5">
                          <span className="text-cyan-400 font-bold">Q{idx + 1}:</span>
                          <span className="leading-relaxed">{q}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommended Next Steps */}
                {review.recommended_next_steps && review.recommended_next_steps.length > 0 && (
                  <div className="glass-card p-5 rounded-2xl border border-white/[0.08]">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-white mb-3 flex items-center gap-2">
                      <ArrowRight size={15} className="text-emerald-400" />
                      Recommended Next Actions
                    </h3>
                    <ol className="space-y-2">
                      {review.recommended_next_steps.map((step, idx) => (
                        <li key={idx} className="bg-slate-900/60 border border-white/[0.05] rounded-xl p-3 text-xs text-slate-200 flex items-start gap-2.5">
                          <span className="font-bold text-emerald-400">{idx + 1}.</span>
                          <span className="leading-relaxed">{step}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {/* Claim Verification Checklist */}
                {review.claim_verification && review.claim_verification.length > 0 && (
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">Claim Verification Grounding</h3>
                    <div className="space-y-2">
                      {review.claim_verification.map((claimItem, idx) => {
                        const claim = typeof claimItem === 'object' && claimItem !== null ? (claimItem as any).claim : String(claimItem);
                        const source = typeof claimItem === 'object' && claimItem !== null ? (claimItem as any).source : 'KB';
                        const verified = typeof claimItem === 'object' && claimItem !== null
                          ? (claimItem as any).verified !== false && (claimItem as any).verified !== 'false'
                          : true;
                        return (
                          <div key={idx} className="glass-card p-3 rounded-xl border border-white/[0.06] text-xs flex justify-between items-center gap-4">
                            <span className="text-slate-200 font-medium leading-relaxed">{claim}</span>
                            <span className={`px-2.5 py-0.5 rounded-full font-mono text-[10px] shrink-0 ${
                              verified
                                ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
                                : 'bg-rose-500/10 border border-rose-500/30 text-rose-300'
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
              <div className="text-center py-16 text-slate-400">
                <ShieldCheck size={36} className="mx-auto mb-2 text-slate-600" />
                <h3 className="text-base font-bold text-white mb-1">Review Pending</h3>
                <p className="text-xs">Final QA and verification checks will be presented after proposal generation.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Send Proposal Modal */}
      {showSendModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="glass-panel border border-white/[0.15] bg-slate-900/95 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <div className="flex items-center gap-2.5">
                <Mail size={16} className="text-indigo-400" />
                <h3 className="text-sm font-bold text-white">
                  Transmit Proposal to Client
                </h3>
                {smtpStatus && (
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                    smtpStatus.configured
                      ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40'
                      : 'bg-amber-950/80 text-amber-300 border-amber-500/40'
                  }`}>
                    {smtpStatus.configured ? '✓ SMTP Active' : '⚠️ SMTP Unconfigured'}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowSendModal(false);
                  setSendModalNotification(null);
                }}
                className="text-slate-400 hover:text-white transition p-1"
              >
                <X size={16} />
              </button>
            </div>

            {/* In-Modal Notification / Error Banner */}
            {sendModalNotification && (
              <div
                className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
                  sendModalNotification.type === 'error'
                    ? 'bg-red-950/70 border-red-500/40 text-red-300'
                    : sendModalNotification.type === 'success'
                    ? 'bg-emerald-950/70 border-emerald-500/40 text-emerald-300'
                    : 'bg-indigo-950/70 border-indigo-500/40 text-indigo-300'
                }`}
              >
                {sendModalNotification.type === 'error' ? (
                  <AlertTriangle size={15} className="text-red-400 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 size={15} className="text-emerald-400 shrink-0 mt-0.5" />
                )}
                <div className="leading-relaxed">{sendModalNotification.message}</div>
              </div>
            )}

            <div className="space-y-3.5">
              <div>
                <label className="text-xs text-slate-300 font-medium flex items-center justify-between">
                  <span>Client Recipient Email (Destination)</span>
                  <span className="text-[10px] text-slate-400">Target inbox to receive proposal</span>
                </label>
                <input
                  type="email"
                  value={recipientEmail}
                  onChange={(e) => setRecipientEmail(e.target.value)}
                  placeholder="client@company.com"
                  className="w-full bg-slate-800/80 border border-white/[0.1] rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 mt-1"
                />
              </div>

              {/* Email Delivery Configuration Alert & Setup Drawer */}
              {!smtpStatus?.configured ? (
                <div className="p-3.5 bg-amber-950/40 rounded-xl border border-amber-500/30 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-amber-300 flex items-center gap-1.5">
                      <AlertCircle size={14} className="text-amber-400 shrink-0" />
                      Email Delivery Provider Setup Required
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowSmtpDrawer(!showSmtpDrawer)}
                      className="text-[11px] text-amber-400 hover:text-amber-300 underline font-semibold cursor-pointer"
                    >
                      {showSmtpDrawer ? 'Collapse' : 'Configure Provider'}
                    </button>
                  </div>
                  <p className="text-[11px] text-amber-200/80 leading-relaxed">
                    To transmit real emails to <span className="font-semibold text-white">{recipientEmail || 'client'}</span>, configure an email provider. On Render Free Tier, use <strong className="text-white">Resend API (Port 443)</strong> because Render blocks port 587.
                  </p>

                  {showSmtpDrawer && (
                    <div className="pt-2.5 border-t border-amber-500/20 space-y-2.5 mt-2">
                      {/* Provider selection tabs */}
                      <div className="flex rounded-lg bg-slate-900/90 p-1 border border-white/[0.08]">
                        <button
                          type="button"
                          onClick={() => setSmtpTab('http')}
                          className={`flex-1 py-1 px-2 text-[10px] font-semibold rounded-md transition ${
                            smtpTab === 'http'
                              ? 'bg-indigo-600 text-white shadow-sm'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          🚀 Resend API (Port 443 • Free Tier)
                        </button>
                        <button
                          type="button"
                          onClick={() => setSmtpTab('smtp')}
                          className={`flex-1 py-1 px-2 text-[10px] font-semibold rounded-md transition ${
                            smtpTab === 'smtp'
                              ? 'bg-indigo-600 text-white shadow-sm'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          ✉️ Gmail SMTP (Port 587)
                        </button>
                      </div>

                      {smtpTab === 'http' ? (
                        <div className="space-y-2">
                          <div className="p-2 bg-indigo-950/40 rounded-lg border border-indigo-500/20 text-[10px] text-indigo-200/90 leading-relaxed">
                            <strong>Recommended for Render:</strong> Connects over standard HTTPS (port 443), completely bypassing Render's port 587 block.
                          </div>
                          <div>
                            <div className="flex items-center justify-between">
                              <label className="text-[10px] text-slate-300 font-medium">Resend API Key</label>
                              <a
                                href="https://resend.com/api-keys"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-[10px] text-indigo-400 hover:text-white underline inline-flex items-center gap-1 font-semibold"
                              >
                                Get Free Key (100 free/day) <ExternalLink size={10} />
                              </a>
                            </div>
                            <input
                              type="password"
                              value={resendApiKey}
                              onChange={(e) => setResendApiKey(e.target.value)}
                              placeholder="re_123456789abcdef..."
                              className="w-full bg-slate-900 border border-white/[0.1] rounded-lg px-2.5 py-1.5 text-xs text-white mt-1 font-mono focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={handleSaveResendConfig}
                            disabled={savingSmtp || !resendApiKey.trim()}
                            className="w-full mt-1 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer shadow-md shadow-indigo-600/30"
                          >
                            {savingSmtp ? <Loader size={12} className="animate-spin" /> : <Check size={12} />}
                            {savingSmtp ? 'Saving...' : 'Save & Enable Resend API (Port 443)'}
                          </button>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <div className="p-2 bg-amber-950/40 rounded-lg border border-amber-500/20 text-[10px] text-amber-200/90 leading-relaxed">
                            <strong>Direct SMTP Notice:</strong> Render Free Tier blocks outbound port 587 ([Errno 101]). Works when running locally or on a Render paid plan.
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-300 font-medium">Gmail Address (Sender Mailbox)</label>
                            <input
                              type="email"
                              value={smtpUser}
                              onChange={(e) => setSmtpUser(e.target.value)}
                              placeholder="your.account@gmail.com"
                              className="w-full bg-slate-900 border border-white/[0.1] rounded-lg px-2.5 py-1.5 text-xs text-white mt-1 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <div>
                            <div className="flex items-center justify-between">
                              <label className="text-[10px] text-slate-300 font-medium">16-Character Gmail App Password</label>
                              <a
                                href="https://myaccount.google.com/apppasswords"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-[10px] text-amber-300 hover:text-white underline inline-flex items-center gap-1 font-semibold"
                              >
                                Generate at Google <ExternalLink size={10} />
                              </a>
                            </div>
                            <input
                              type="password"
                              value={smtpPassword}
                              onChange={(e) => setSmtpPassword(e.target.value)}
                              placeholder="abcd efgh ijkl mnop"
                              className="w-full bg-slate-900 border border-white/[0.1] rounded-lg px-2.5 py-1.5 text-xs text-white mt-1 placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={handleSaveSmtp}
                            disabled={savingSmtp || !smtpUser.trim() || !smtpPassword.trim()}
                            className="w-full mt-1 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer"
                          >
                            {savingSmtp ? <Loader size={12} className="animate-spin" /> : <Check size={12} />}
                            {savingSmtp ? 'Saving...' : 'Save Gmail SMTP (Port 587)'}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-3 bg-emerald-950/40 rounded-xl border border-emerald-500/30 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5 text-emerald-300 text-[11px] font-medium">
                      <CheckCircle2 size={13} className="text-emerald-400" />
                      <span>
                        {smtpStatus?.has_http_api ? (
                          <>
                            Active Provider: <strong className="text-white">Resend API (HTTPS Port 443)</strong>
                          </>
                        ) : (
                          <>
                            Live Sender Mailbox: <strong className="text-white">{smtpStatus?.smtp_user}</strong> (Port 587)
                          </>
                        )}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowSmtpDrawer(!showSmtpDrawer)}
                      className="text-[10px] text-emerald-400 hover:text-emerald-300 underline font-medium cursor-pointer"
                    >
                      {showSmtpDrawer ? 'Close' : 'Change Provider'}
                    </button>
                  </div>

                  {showSmtpDrawer && (
                    <div className="pt-2 border-t border-emerald-500/20 space-y-2.5">
                      <div className="flex rounded-lg bg-slate-900/90 p-1 border border-white/[0.08]">
                        <button
                          type="button"
                          onClick={() => setSmtpTab('http')}
                          className={`flex-1 py-1 px-2 text-[10px] font-semibold rounded-md transition ${
                            smtpTab === 'http'
                              ? 'bg-indigo-600 text-white shadow-sm'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          🚀 Resend API (Port 443)
                        </button>
                        <button
                          type="button"
                          onClick={() => setSmtpTab('smtp')}
                          className={`flex-1 py-1 px-2 text-[10px] font-semibold rounded-md transition ${
                            smtpTab === 'smtp'
                              ? 'bg-indigo-600 text-white shadow-sm'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          ✉️ Gmail SMTP (Port 587)
                        </button>
                      </div>

                      {smtpTab === 'http' ? (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-[10px] text-slate-300 font-medium">New Resend API Key</label>
                            <a
                              href="https://resend.com/api-keys"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[10px] text-indigo-400 hover:text-white underline inline-flex items-center gap-1 font-semibold"
                            >
                              Get Free Key <ExternalLink size={10} />
                            </a>
                          </div>
                          <input
                            type="password"
                            value={resendApiKey}
                            onChange={(e) => setResendApiKey(e.target.value)}
                            placeholder="re_..."
                            className="w-full bg-slate-900 border border-white/[0.1] rounded-lg px-2.5 py-1.5 text-xs text-white font-mono"
                          />
                          <button
                            type="button"
                            onClick={handleSaveResendConfig}
                            disabled={savingSmtp || !resendApiKey.trim()}
                            className="w-full px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition cursor-pointer"
                          >
                            {savingSmtp ? <Loader size={12} className="animate-spin" /> : <Check size={12} />}
                            {savingSmtp ? 'Saving...' : 'Switch to Resend API (Port 443)'}
                          </button>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <div>
                            <label className="text-[10px] text-slate-300 font-medium">Sender Gmail Address</label>
                            <input
                              type="email"
                              value={smtpUser}
                              onChange={(e) => setSmtpUser(e.target.value)}
                              placeholder="your.account@gmail.com"
                              className="w-full bg-slate-900 border border-white/[0.1] rounded-lg px-2.5 py-1.5 text-xs text-white mt-1"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-300 font-medium">New App Password</label>
                            <input
                              type="password"
                              value={smtpPassword}
                              onChange={(e) => setSmtpPassword(e.target.value)}
                              placeholder="Enter new 16-character code"
                              className="w-full bg-slate-900 border border-white/[0.1] rounded-lg px-2.5 py-1.5 text-xs text-white mt-1 font-mono"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={handleSaveSmtp}
                            disabled={savingSmtp || !smtpUser.trim() || !smtpPassword.trim()}
                            className="w-full px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                          >
                            {savingSmtp ? <Loader size={12} className="animate-spin" /> : <Check size={12} />}
                            {savingSmtp ? 'Updating...' : 'Update SMTP Credentials'}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Client Email Preview & Sign-off Portal Banner */}
              <div className="p-3 bg-slate-800/60 rounded-xl border border-white/[0.08] space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                    <Sparkles size={12} className="text-indigo-400" />
                    Interactive Customer Portal
                  </span>
                  <a
                    href={`${API_BASE_URL}/proposals/${leadId}/email-view`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold underline"
                  >
                    <ExternalLink size={11} /> Preview HTML Email
                  </a>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Email includes an interactive <span className="text-emerald-400 font-semibold">✓ Accept Proposal &amp; Confirm Kickoff</span> button that marks deals Qualified and reserves onboarding slots.
                </p>
              </div>

              <p className="text-[11px] text-slate-400">
                {smtpStatus?.configured
                  ? `Real email delivery active via ${smtpStatus.smtp_host} (${smtpStatus.smtp_user}).`
                  : 'Without configured SMTP credentials, server delivery will be rejected per production policy.'}
              </p>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/[0.06]">
              <button
                type="button"
                onClick={() => {
                  setShowSendModal(false);
                  setSendModalNotification(null);
                }}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-white transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSendProposal}
                disabled={sendingEmail || !recipientEmail.trim()}
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-95 shadow-lg shadow-indigo-500/20"
              >
                {sendingEmail ? <Loader size={14} className="animate-spin text-white" /> : <Mail size={14} />}
                {sendingEmail ? 'Sending...' : 'Confirm & Send'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

