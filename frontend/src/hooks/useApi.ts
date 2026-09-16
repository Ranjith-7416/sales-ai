import { useState, useCallback, useMemo } from 'react';
import axios, { AxiosError } from 'axios';
import { Lead, LeadInput, ScoringConfig, ProposalExportResult, KBProduct, KBService } from '../types';

import { API_BASE_URL, API_TOKEN } from '../config';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
  },
});

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleError = (err: AxiosError<any>) => {
    let message = err.response?.data?.detail || err.message || 'An error occurred';
    // If response is a blob containing JSON error details
    if (err.response?.data instanceof Blob) {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const parsed = JSON.parse(reader.result as string);
          if (parsed.detail) {
            setError(parsed.detail);
          }
        } catch {}
      };
      reader.readAsText(err.response.data);
    }
    setError(message);
    console.error('API Error:', message);
  };

  const submitLead = useCallback(async (leadInput: LeadInput) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post('/qualify-lead', leadInput);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const submitLeadDocument = useCallback(async (file: File, leadInput: LeadInput) => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      Object.entries(leadInput).forEach(([key, value]) => {
        if (value) formData.append(key, value);
      });
      const response = await apiClient.post('/leads/upload', formData);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getLead = useCallback(async (leadId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get(`/leads/${leadId}`);
      return response.data as Lead;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateLead = useCallback(async (leadId: string, leadInput: LeadInput) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.put(`/leads/${leadId}`, leadInput);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteLead = useCallback(async (leadId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.delete(`/leads/${leadId}`);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const listLeads = useCallback(async (skip = 0, limit = 20, status?: string, search?: string) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('skip', skip.toString());
      params.append('limit', limit.toString());
      if (status) params.append('status', status);
      if (search && search.trim()) params.append('search', search.trim());

      const response = await apiClient.get(`/leads?${params}`);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getProposal = useCallback(async (leadId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get(`/proposals/${leadId}`);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const generateProposal = useCallback(async (leadId: string, regenerate: boolean = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post(`/proposals/${leadId}/generate`, { regenerate });
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const approveProposal = useCallback(async (leadId: string, approverName?: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post(
        `/proposals/${leadId}/approve`,
        { approver_name: approverName || 'Sales Leadership' },
        { params: { approver_name: approverName || 'Sales Leadership' } }
      );
      return response.data;
    } catch (err) {
      await handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const exportProposal = useCallback(async (leadId: string, format: string = 'markdown'): Promise<ProposalExportResult> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get(`/proposals/${leadId}/export?format=${format}`);
      return response.data;
    } catch (err) {
      await handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const downloadProposalPdf = useCallback(async (leadId: string, clientEmail?: string, companyName?: string) => {
    setLoading(true);
    setError(null);

    try {
      let response;
      try {
        response = await apiClient.post(
          `/proposals/${leadId}/pdf`,
          { client_email: clientEmail },
          {
            params: clientEmail ? { client_email: clientEmail } : undefined,
            responseType: 'blob',
          }
        );
      } catch (postErr) {
        console.warn('POST /pdf attempt failed, trying GET /pdf fallback...', postErr);
        response = await apiClient.get(
          `/proposals/${leadId}/pdf`,
          {
            params: clientEmail ? { client_email: clientEmail } : undefined,
            responseType: 'blob',
          }
        );
      }

      let filename = `Proposal_${(companyName || 'Client').replace(/[^a-zA-Z0-9_\-]/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
      const disposition = response.headers?.['content-disposition'] || response.headers?.['Content-Disposition'];
      if (disposition && disposition.includes('filename=')) {
        const match = disposition.match(/filename="?([^";]+)"?/);
        if (match && match[1]) {
          filename = match[1].trim();
        }
      }

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      return { success: true, filename };
    } catch (err) {
      await handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getScoringConfig = useCallback(async (): Promise<ScoringConfig> => {
    try {
      const response = await apiClient.get('/config/scoring');
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    }
  }, []);

  const updateScoringConfig = useCallback(async (config: ScoringConfig): Promise<any> => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/config/scoring', config);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getProducts = useCallback(async (): Promise<KBProduct[]> => {
    try {
      const response = await apiClient.get('/knowledge-base/products');
      return response.data?.products || [];
    } catch (err) {
      handleError(err as AxiosError);
      return [];
    }
  }, []);

  const getServices = useCallback(async (): Promise<KBService[]> => {
    try {
      const response = await apiClient.get('/knowledge-base/services');
      return response.data?.services || [];
    } catch (err) {
      handleError(err as AxiosError);
      return [];
    }
  }, []);

  const searchKnowledgeBase = useCallback(async (query: string, entryType: 'product' | 'service' = 'product') => {
    try {
      const response = await apiClient.get(`/knowledge-base/search?query=${encodeURIComponent(query)}&entry_type=${entryType}`);
      return response.data?.results || [];
    } catch (err) {
      handleError(err as AxiosError);
      return [];
    }
  }, []);

  const getSmtpConfig = useCallback(async () => {
    try {
      const response = await apiClient.get('/config/smtp');
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      return { configured: false };
    }
  }, []);

  const updateSmtpConfig = useCallback(async (smtpConfig: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/config/smtp', smtpConfig);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const testSmtpConnection = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/config/smtp/test');
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);


  const acceptProposal = useCallback(async (leadId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post(`/proposals/${leadId}/accept`);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const requalifyLead = useCallback(async (leadId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post(`/leads/${leadId}/requalify`);
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return useMemo(() => ({
    loading,
    error,
    submitLead,
    submitLeadDocument,
    getLead,
    updateLead,
    deleteLead,
    listLeads,
    requalifyLead,
    getProposal,
    generateProposal,
    approveProposal,
    downloadProposalPdf,
    exportProposal,
    getScoringConfig,
    updateScoringConfig,
    getProducts,
    getServices,
    searchKnowledgeBase,
    getSmtpConfig,
    updateSmtpConfig,
    testSmtpConnection,
    acceptProposal,
  }), [
    loading,
    error,
    submitLead,
    submitLeadDocument,
    getLead,
    updateLead,
    deleteLead,
    listLeads,
    requalifyLead,
    getProposal,
    generateProposal,
    approveProposal,
    downloadProposalPdf,
    exportProposal,
    getScoringConfig,
    updateScoringConfig,
    getProducts,
    getServices,
    searchKnowledgeBase,
    getSmtpConfig,
    updateSmtpConfig,
    testSmtpConnection,
    acceptProposal,
  ]);
};

