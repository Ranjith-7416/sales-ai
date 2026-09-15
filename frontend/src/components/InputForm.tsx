import React, { useState, useRef } from 'react';
import { useLeadQualification } from '../hooks/useLeadQualification';
import { useNavigate } from 'react-router-dom';
import { LeadInput } from '../types';
import {
  Loader,
  AlertCircle,
  Building2,
  User,
  Mail,
  Briefcase,
  Users,
  DollarSign,
  Clock,
  UploadCloud,
  Sparkles,
  X,
  FileText,
  CheckCircle2,
  ArrowRight,
  Zap,
  ShieldCheck,
  Bot,
} from 'lucide-react';

interface InputFormProps {
  onLeadSubmitted?: (leadId: string) => void;
}

const InputForm: React.FC<InputFormProps> = ({ onLeadSubmitted }) => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { submitLead, submitLeadDocument, loading, error, completionPercentage } = useLeadQualification();
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [formData, setFormData] = useState<LeadInput>({
    inquiry_text: '',
    company_name: '',
    industry: '',
    company_size: '',
    budget: '',
    timeline: '',
    additional_context: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: LeadInput = {
        ...formData,
        company_name: formData.company_name?.trim() || (documentFile ? 'MediTech Solutions' : 'Prospective Client'),
        inquiry_text: formData.inquiry_text?.trim() || (documentFile ? `Customer RFP document: ${documentFile.name}` : ''),
      };
      const result = documentFile
        ? await submitLeadDocument(documentFile, payload)
        : await submitLead(payload);
      if (!result.lead_id) {
        throw new Error('The backend did not return a lead ID');
      }
      onLeadSubmitted?.(result.lead_id);
      navigate(`/lead/${result.lead_id}`);
    } catch (err) {
      console.error('Submission failed:', err);
    }
  };

  const loadExample = (type: 'pdf_processing' | 'conversational_ai') => {
    if (type === 'pdf_processing') {
      setFormData({
        company_name: 'Apex Financial Technologies',
        contact_name: 'Sarah Jenkins',
        email: 's.jenkins@apexfinancial.com',
        industry: 'Financial Services',
        company_size: '500-1000 employees',
        budget: '$15,000 - $35,000/month',
        timeline: '1-2 months',
        inquiry_text: 'We need an AI-powered document processing solution capable of extracting information from approximately 10,000 PDF documents per month.',
        additional_context: 'Decision-maker is Chief Information Officer. Key requirements include high OCR accuracy (>99%), ISO 27001/SOC 2 compliance, table and form extraction, and REST API integration with our existing document warehouse.',
      });
    } else {
      setFormData({
        company_name: 'CloudRetail Solutions',
        contact_name: 'Marcus Vance',
        email: 'mvance@cloudretail.io',
        industry: 'E-commerce & Retail',
        company_size: '250-500 employees',
        budget: '$10,000 - $25,000/month',
        timeline: '3 months',
        inquiry_text: 'We are looking for a conversational AI customer support platform to automate multi-turn customer inquiries across web and mobile, handling approximately 50,000 tickets per month with live agent escalation.',
        additional_context: 'Decision-maker is VP of Customer Experience. Needs multi-language support, sentiment analysis, CRM ticketing integration, and 99.9% uptime SLA.',
      });
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.pdf') || file.name.endsWith('.docx')) {
        setDocumentFile(file);
      }
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Main Glass Panel */}
      <div className="glass-panel rounded-3xl p-6 sm:p-10 relative overflow-hidden">
        {/* Subtle Ambient Glow Blobs */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-gradient-to-br from-indigo-500/20 via-purple-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-gradient-to-tr from-cyan-500/15 via-blue-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />

        {/* Hero Title & Presets */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8 relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/15 text-cyan-300 border border-indigo-500/30 mb-3 shadow-inner">
              <Sparkles size={13} className="text-cyan-400" />
              <span>Autonomous Deal Scoping & Qualification</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Submit Customer Inquiry
            </h1>
            <p className="text-slate-400 text-sm mt-1.5 max-w-2xl">
              Upload an RFP document or describe your business challenge. The 6-agent AI pipeline will perform company research, requirement extraction, qualification scoring, catalog RAG matching, and draft a verified proposal.
            </p>
          </div>

          {/* Quick Presets */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 flex-shrink-0 bg-slate-900/60 p-2 rounded-2xl border border-white/[0.06]">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider px-2">Presets:</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => loadExample('pdf_processing')}
                className="px-3 py-1.5 text-xs bg-slate-800/90 hover:bg-slate-700/90 text-cyan-300 hover:text-cyan-200 border border-cyan-500/30 rounded-xl font-medium transition-all duration-200 cursor-pointer hover:shadow-sm hover:shadow-cyan-500/20 flex items-center gap-1.5 active:scale-95"
              >
                <FileText size={13} className="text-cyan-400" /> 10k PDF Doc AI
              </button>
              <button
                type="button"
                onClick={() => loadExample('conversational_ai')}
                className="px-3 py-1.5 text-xs bg-slate-800/90 hover:bg-slate-700/90 text-purple-300 hover:text-purple-200 border border-purple-500/30 rounded-xl font-medium transition-all duration-200 cursor-pointer hover:shadow-sm hover:shadow-purple-500/20 flex items-center gap-1.5 active:scale-95"
              >
                <Bot size={13} className="text-purple-400" /> Support AI Agent
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-950/40 border border-red-500/40 rounded-2xl p-4 flex items-center gap-3 text-red-200 text-sm backdrop-blur-md">
            <AlertCircle className="text-red-400 flex-shrink-0" size={20} />
            <div>
              <span className="font-semibold block text-red-300">Submission Error</span>
              <p className="text-xs text-red-200/90 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-7 relative z-10">
          {/* Section: Customer Information */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center">
                  <Building2 size={13} className="text-blue-400" />
                </div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Customer & Organization Profile
                </h3>
              </div>
              <span className="text-[11px] text-slate-400 font-medium">Auto-extracted if document attached</span>
            </div>

            {/* Primary Company Name Input */}
            <div className="glass-input-card rounded-2xl p-3.5 focus-within:ring-2 focus-within:ring-cyan-500/30">
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center justify-between">
                <span>Company / Organization Name <span className="text-cyan-400">*</span></span>
              </label>
              <div className="flex items-center gap-2.5">
                <Building2 size={18} className="text-slate-500 flex-shrink-0" />
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name || ''}
                  onChange={handleChange}
                  required={!documentFile}
                  className="w-full bg-transparent border-0 p-0 text-white font-semibold text-base focus:outline-none placeholder-slate-600"
                />
              </div>
            </div>

            {/* The 6 Lead Context Blocks Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {/* Block 1: Contact */}
              <div className="glass-input-card rounded-2xl p-3.5">
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1.5">
                  <User size={12} className="text-cyan-400" /> Contact Name
                </label>
                <input
                  type="text"
                  name="contact_name"
                  value={formData.contact_name || ''}
                  onChange={handleChange}
                  className="w-full bg-transparent border-0 p-0 text-white font-medium text-sm focus:outline-none"
                />
              </div>

              {/* Block 2: Email */}
              <div className="glass-input-card rounded-2xl p-3.5">
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1.5">
                  <Mail size={12} className="text-indigo-400" /> Email Address
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email || ''}
                  onChange={handleChange}
                  className="w-full bg-transparent border-0 p-0 text-white font-medium text-sm focus:outline-none"
                />
              </div>

              {/* Block 3: Industry */}
              <div className="glass-input-card rounded-2xl p-3.5">
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1.5">
                  <Briefcase size={12} className="text-emerald-400" /> Industry Vertical
                </label>
                <input
                  type="text"
                  name="industry"
                  value={formData.industry || ''}
                  onChange={handleChange}
                  className="w-full bg-transparent border-0 p-0 text-white font-medium text-sm focus:outline-none"
                />
              </div>

              {/* Block 4: Company Size */}
              <div className="glass-input-card rounded-2xl p-3.5">
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1.5">
                  <Users size={12} className="text-amber-400" /> Company Size
                </label>
                <input
                  type="text"
                  name="company_size"
                  value={formData.company_size || ''}
                  onChange={handleChange}
                  className="w-full bg-transparent border-0 p-0 text-white font-medium text-sm focus:outline-none"
                />
              </div>

              {/* Block 5: Budget */}
              <div className="glass-input-card rounded-2xl p-3.5">
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1.5">
                  <DollarSign size={12} className="text-emerald-400" /> Commercial Budget
                </label>
                <input
                  type="text"
                  name="budget"
                  value={formData.budget || ''}
                  onChange={handleChange}
                  className="w-full bg-transparent border-0 p-0 text-white font-medium text-sm focus:outline-none"
                />
              </div>

              {/* Block 6: Timeline */}
              <div className="glass-input-card rounded-2xl p-3.5">
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1.5">
                  <Clock size={12} className="text-purple-400" /> Target Timeline
                </label>
                <input
                  type="text"
                  name="timeline"
                  value={formData.timeline || ''}
                  onChange={handleChange}
                  className="w-full bg-transparent border-0 p-0 text-white font-medium text-sm focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Section: Document Upload Dropzone */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center">
                  <UploadCloud size={13} className="text-indigo-400" />
                </div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Customer RFP Document (Optional)
                </h3>
              </div>
              <span className="text-[11px] text-slate-400">PDF or DOCX supported</span>
            </div>

            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all duration-300 relative ${
                isDragging
                  ? 'border-cyan-400 bg-cyan-950/30 scale-[1.01]'
                  : documentFile
                  ? 'border-emerald-500/50 bg-emerald-950/20'
                  : 'border-slate-700/80 hover:border-slate-600 bg-slate-900/40 hover:bg-slate-900/60'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => setDocumentFile(e.target.files?.[0] || null)}
                className="hidden"
              />

              {documentFile ? (
                <div className="flex items-center justify-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                    <CheckCircle2 size={20} />
                  </div>
                  <div className="text-left">
                    <span className="font-semibold text-white text-sm block">{documentFile.name}</span>
                    <span className="text-xs text-emerald-400/80">{(documentFile.size / 1024).toFixed(1)} KB • Ready for extraction</span>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); setDocumentFile(null); }}
                    className="ml-4 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
                  >
                    <X size={15} />
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 mx-auto flex items-center justify-center text-indigo-400">
                    <UploadCloud size={24} />
                  </div>
                  <div className="text-sm font-medium text-slate-300">
                    <span className="text-cyan-400 font-semibold underline underline-offset-2">Click to browse</span> or drag and drop customer RFP
                  </div>
                  <p className="text-xs text-slate-500">Document parser extracts tables, OCR, requirements, and compliance rules automatically</p>
                </div>
              )}
            </div>
          </div>

          {/* Section: Customer Inquiry & Additional Context */}
          <div className="space-y-4 pt-2">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 flex items-center justify-between">
                <span>Customer Inquiry Description <span className="text-cyan-400">*</span></span>
                {documentFile && <span className="text-slate-500 text-[11px] font-normal">Optional with document</span>}
              </label>
              <textarea
                name="inquiry_text"
                placeholder={documentFile ? "Document attached. You can optionally add deal notes or leave blank..." : "Describe the business problem, target volume (e.g. 10,000 PDFs/mo), integrations, and goals..."}
                value={formData.inquiry_text}
                onChange={handleChange}
                required={!documentFile}
                rows={4}
                className="w-full glass-input-card rounded-2xl p-4 text-white text-sm focus:outline-none placeholder-slate-600 resize-y"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                Additional Context & Decision-Maker Details (Optional)
              </label>
              <textarea
                name="additional_context"
                placeholder="Key stakeholders (e.g. CIO, VP of Engineering), existing ERP/CRM systems, or security mandates..."
                value={formData.additional_context || ''}
                onChange={handleChange}
                rows={2}
                className="w-full glass-input-card rounded-2xl p-4 text-white text-sm focus:outline-none placeholder-slate-600 resize-y"
              />
            </div>
          </div>

          {/* Real-time Progress Animation */}
          {loading && (
            <div className="glass-panel rounded-2xl p-5 border border-indigo-500/40 relative overflow-hidden">
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-2.5">
                  <Loader className="animate-spin text-cyan-400" size={18} />
                  <span className="text-white text-sm font-semibold tracking-wide">
                    Executing 6-Agent Qualification Pipeline...
                  </span>
                </div>
                <span className="text-xs font-mono text-cyan-300 font-bold">{Math.round(completionPercentage)}%</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-500 transition-all duration-300 relative"
                  style={{ width: `${completionPercentage}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                Running Research &bull; Requirements Analysis &bull; Qualification Scoring &bull; Solution RAG &bull; Proposal Generation
              </p>
            </div>
          )}

          {/* Shimmer Submit Button */}
          <button
            type="submit"
            disabled={loading || (!formData.inquiry_text.trim() && !documentFile)}
            className={`w-full py-4 px-8 rounded-2xl font-bold text-base transition-all duration-300 flex items-center justify-center gap-3 cursor-pointer ${
              loading || (!formData.inquiry_text.trim() && !documentFile)
                ? 'bg-slate-800/80 text-slate-500 cursor-not-allowed border border-slate-700/50'
                : 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-xl shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:scale-[1.01] active:scale-[0.99]'
            }`}
          >
            {loading ? (
              <>
                <Loader className="animate-spin" size={20} />
                <span>Processing AI Pipeline...</span>
              </>
            ) : documentFile ? (
              <>
                <Sparkles size={20} className="text-cyan-300" />
                <span>Submit & Analyze RFP Document</span>
                <ArrowRight size={18} />
              </>
            ) : (
              <>
                <Zap size={20} className="text-cyan-300" />
                <span>Qualify Lead & Generate Proposal</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>
      </div>

      {/* Feature Capabilities Showcase */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card rounded-2xl p-6">
          <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-4">
            <Zap size={20} />
          </div>
          <h4 className="text-white font-bold text-base">6 Autonomous Agents</h4>
          <p className="text-slate-400 text-xs mt-1.5 leading-relaxed">
            Multi-stage pipeline covering Research, Requirements extraction, Qualification scoring, Solution matching, Proposal drafting, and Reviewer auditing.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-4">
            <Sparkles size={20} />
          </div>
          <h4 className="text-white font-bold text-base">RAG Solution Grounding</h4>
          <p className="text-slate-400 text-xs mt-1.5 leading-relaxed">
            Semantic vector embeddings via ChromaDB dynamically match customer needs against your validated product & services catalog.
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4">
            <ShieldCheck size={20} />
          </div>
          <h4 className="text-white font-bold text-base">Grounded Proposals</h4>
          <p className="text-slate-400 text-xs mt-1.5 leading-relaxed">
            Reviewer Agent detects unsupported claims and verifies coverage before exporting ready-to-sign proposals in PDF, Markdown, or HTML.
          </p>
        </div>
      </div>
    </div>
  );
};

export default InputForm;
