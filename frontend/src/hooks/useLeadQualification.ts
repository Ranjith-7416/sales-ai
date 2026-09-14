import { useState, useCallback } from 'react';
import { Lead, LeadInput } from '../types';
import { useApi } from './useApi';

export const useLeadQualification = () => {
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completionPercentage, setCompletionPercentage] = useState(0);

  const api = useApi();

  const submitLead = useCallback(async (leadInput: LeadInput) => {
    setLoading(true);
    setError(null);
    setCompletionPercentage(0);

    try {
      const result = await api.submitLead(leadInput);
      setCompletionPercentage(10);
      setLoading(false);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to qualify lead';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  }, [api]);

  const submitLeadDocument = useCallback(async (file: File, leadInput: LeadInput) => {
    setLoading(true);
    setError(null);
    setCompletionPercentage(0);
    try {
      const result = await api.submitLeadDocument(file, leadInput);
      setCompletionPercentage(10);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process document';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [api]);

  const fetchLead = useCallback(async (leadId: string) => {
    setLoading(true);
    setError(null);

    try {
      const leadData = await api.getLead(leadId);
      setLead(leadData);
      return leadData;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch lead';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [api]);

  return {
    lead,
    loading,
    error,
    completionPercentage,
    submitLead,
    submitLeadDocument,
    fetchLead,
  };
};
