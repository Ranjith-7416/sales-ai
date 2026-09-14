import { useState, useCallback, useMemo } from 'react';
import axios, { AxiosError } from 'axios';
import { Lead, LeadInput, ScoringConfig, ProposalExportResult, KBProduct, KBService } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const API_TOKEN = import.meta.env.VITE_API_TOKEN;

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
    const message = err.response?.data?.detail || err.message || 'An error occurred';
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

  const listLeads = useCallback(async (skip = 0, limit = 20, status?: string) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('skip', skip.toString());
      params.append('limit', limit.toString());
      if (status) params.append('status', status);

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

  const approveProposal = useCallback(async (leadId: string, approvedBy: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post(`/proposals/${leadId}/approve`, {
        approved_by: approvedBy,
      });
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const sendProposal = useCallback(async (leadId: string, email: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post(`/proposals/${leadId}/send`, {
        recipient_email: email,
      });
      return response.data;
    } catch (err) {
      handleError(err as AxiosError);
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
      handleError(err as AxiosError);
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

  return useMemo(() => ({
    loading,
    error,
    submitLead,
    submitLeadDocument,
    getLead,
    updateLead,
    deleteLead,
    listLeads,
    getProposal,
    approveProposal,
    sendProposal,
    exportProposal,
    getScoringConfig,
    updateScoringConfig,
    getProducts,
    getServices,
    searchKnowledgeBase,
  }), [
    loading,
    error,
    submitLead,
    submitLeadDocument,
    getLead,
    updateLead,
    deleteLead,
    listLeads,
    getProposal,
    approveProposal,
    sendProposal,
    exportProposal,
    getScoringConfig,
    updateScoringConfig,
    getProducts,
    getServices,
    searchKnowledgeBase,
  ]);
};

