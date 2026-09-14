import React, { useState } from 'react';
import { useLeadQualification } from '../hooks/useLeadQualification';
import { useNavigate } from 'react-router-dom';
import { LeadInput } from '../types';
import { Loader, AlertCircle } from 'lucide-react';

interface InputFormProps {
  onLeadSubmitted?: (leadId: string) => void;
}

const InputForm: React.FC<InputFormProps> = ({ onLeadSubmitted }) => {
  const navigate = useNavigate();
  const { submitLead, submitLeadDocument, loading, error, completionPercentage } = useLeadQualification();
  const [documentFile, setDocumentFile] = useState<File | null>(null);
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
      const result = documentFile
        ? await submitLeadDocument(documentFile, formData)
        : await submitLead(formData);
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

  return (
    <div className="space-y-8">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Tell us what you need</h2>
            <p className="text-slate-300">
              Describe your business need in your own words. Our AI pipeline will research the company, extract requirements,
              qualify the opportunity, match grounded solutions, and prepare a verified draft proposal.
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Quick Presets:</span>
            <button
              type="button"
              onClick={() => loadExample('pdf_processing')}
              className="px-3 py-1.5 text-xs bg-blue-900/60 hover:bg-blue-800 text-blue-200 border border-blue-700 rounded-md font-medium transition cursor-pointer active:scale-95"
            >
              📄 10k PDF Document AI
            </button>
            <button
              type="button"
              onClick={() => loadExample('conversational_ai')}
              className="px-3 py-1.5 text-xs bg-purple-900/60 hover:bg-purple-800 text-purple-200 border border-purple-700 rounded-md font-medium transition cursor-pointer active:scale-95"
            >
              💬 Conversational Support AI
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-700 rounded-lg p-4 flex gap-3">
            <AlertCircle className="text-red-500 flex-shrink-0" size={20} />
            <div>
              <h3 className="text-red-100 font-semibold">Error</h3>
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Customer information */}
          <div className="border-t border-slate-700 pt-6">
            <h3 className="text-lg font-semibold text-white mb-4">Customer information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                name="company_name"
                placeholder="Company / organization"
                value={formData.company_name || ''}
                onChange={handleChange}
                required
                className="bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
              <input
                type="text"
                name="contact_name"
                placeholder="Contact name (optional)"
                value={formData.contact_name || ''}
                onChange={handleChange}
                className="bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
              <input
                type="email"
                name="email"
                placeholder="Email (optional)"
                value={formData.email || ''}
                onChange={handleChange}
                className="bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
              <input
                type="text"
                name="industry"
                placeholder="Industry (optional)"
                value={formData.industry || ''}
                onChange={handleChange}
                className="bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="border-t border-slate-700 pt-6">
            <h3 className="text-lg font-semibold text-white mb-2">Inquiry Document (Optional)</h3>
            <p className="text-slate-400 text-sm mb-3">Upload a PDF or DOCX when the customer requirements are in a document.</p>
            <input
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(event) => setDocumentFile(event.target.files?.[0] || null)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-slate-300 file:mr-4 file:rounded-md file:border-0 file:bg-orange-500 file:px-3 file:py-2 file:font-semibold file:text-slate-950"
            />
          </div>

          {/* Customer Inquiry */}
          <div className="border-t border-slate-700 pt-6">
              <h3 className="text-lg font-semibold text-white mb-4">Your inquiry</h3>
            <textarea
              name="inquiry_text"
              placeholder="Describe your business problem, desired outcome, scale, integrations, timeline, or constraints in plain language..."
              value={formData.inquiry_text}
              onChange={handleChange}
              required
              rows={6}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Additional Context */}
          <div className="border-t border-slate-700 pt-6">
            <h3 className="text-lg font-semibold text-white mb-4">Additional Context (Optional)</h3>
            <textarea
              name="additional_context"
              placeholder="Any additional information about the deal, decision-makers, or special requirements..."
              value={formData.additional_context || ''}
              onChange={handleChange}
              rows={4}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Progress */}
          {loading && (
            <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <Loader className="animate-spin text-blue-400" size={20} />
                <span className="text-blue-100 font-semibold">Processing lead qualification...</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${completionPercentage}%` }}
                />
              </div>
              <p className="text-blue-200 text-sm mt-2">{Math.round(completionPercentage)}% complete</p>
            </div>
          )}

          {/* Submit Button */}
          <div className="border-t border-slate-700 pt-6">
            <button
              type="submit"
              disabled={loading || !formData.inquiry_text.trim()}
              className={`w-full py-3 px-6 rounded-lg font-semibold transition cursor-pointer active:scale-[0.99] ${
                loading
                  ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {loading ? 'Receiving inquiry...' : 'Submit Inquiry'}
            </button>
          </div>
        </form>
      </div>

      {/* Information */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <div className="text-blue-400 text-3xl font-bold mb-2">7</div>
          <p className="text-slate-300">Analysis Stages</p>
          <p className="text-slate-400 text-sm mt-2">Research, Requirements, Qualification, Solution Matching, Proposal, Review</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <div className="text-green-400 text-3xl font-bold mb-2">AI</div>
          <p className="text-slate-300">Powered Pipeline</p>
          <p className="text-slate-400 text-sm mt-2">LangGraph orchestrated agents with full transparency</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <div className="text-purple-400 text-3xl font-bold mb-2">0-100</div>
          <p className="text-slate-300">Lead Score</p>
          <p className="text-slate-400 text-sm mt-2">Explainable scoring with evidence-based reasoning</p>
        </div>
      </div>
    </div>
  );
};

export default InputForm;
