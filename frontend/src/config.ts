/**
 * Centralized API and environment configuration.
 *
 * In local development (localhost / 127.0.0.1):
 * - Uses '/api' so Vite dev server proxies to localhost:8001.
 *
 * In production (e.g. Vercel deployment):
 * - Uses VITE_API_URL if explicitly configured;
 * - Otherwise defaults to the deployed Render backend URL:
 *   'https://sales-ai-etew.onrender.com/api'
 *
 * NEVER falls back to localhost in production.
 */

const getApiBaseUrl = (): string => {
  const envApiUrl = import.meta.env.VITE_API_URL;
  if (envApiUrl && envApiUrl.trim()) {
    const trimmed = envApiUrl.trim();
    return trimmed.endsWith('/api')
      ? trimmed
      : trimmed.startsWith('http')
      ? `${trimmed.replace(/\/$/, '')}/api`
      : trimmed;
  }

  // Check browser location
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const isLocal =
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === '0.0.0.0';

    if (isLocal) {
      return '/api';
    }
  }

  // Safe production fallback: the live Render backend
  return 'https://sales-ai-etew.onrender.com/api';
};

export const API_BASE_URL = getApiBaseUrl();
export const API_TOKEN = import.meta.env.VITE_API_TOKEN || '';
export const PRODUCTION_BACKEND_URL = 'https://sales-ai-etew.onrender.com';
export const PRODUCTION_FRONTEND_URL = 'https://sales-ai-ranjith-7416s-projects.vercel.app';
