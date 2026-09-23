import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { User, LoginResponse } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  requestPasswordResetOtp: (email: string) => Promise<{ success: boolean; message: string; email: string; dev_otp?: string }>;
  resetPassword: (email: string, password: string, otpCode?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

import { API_BASE_URL } from '../config';

// Configured auth client with explicit 15s timeout to prevent hanging 'Authenticating...' state
const authClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('salesai_token'));
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('salesai_user');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState<boolean>(true);

  // Set default auth header whenever token changes
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      authClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('salesai_token', token);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      delete authClient.defaults.headers.common['Authorization'];
      localStorage.removeItem('salesai_token');
      localStorage.removeItem('salesai_user');
    }
  }, [token]);

  // Verify session on mount
  useEffect(() => {
    const verifySession = async () => {
      const storedToken = localStorage.getItem('salesai_token');
      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        const res = await authClient.get('/auth/me', {
          headers: { Authorization: `Bearer ${storedToken}` },
        });
        setUser(res.data);
        localStorage.setItem('salesai_user', JSON.stringify(res.data));
      } catch {
        setToken(null);
        setUser(null);
        localStorage.removeItem('salesai_token');
        localStorage.removeItem('salesai_user');
      } finally {
        setLoading(false);
      }
    };

    verifySession();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authClient.post<LoginResponse>('/auth/login', {
      email,
      password,
    });

    const { access_token, user: userData } = res.data;
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('salesai_token', access_token);
    localStorage.setItem('salesai_user', JSON.stringify(userData));
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    authClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    const res = await authClient.post<LoginResponse>('/auth/register', {
      name,
      email,
      password,
    });

    const { access_token, user: userData } = res.data;
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('salesai_token', access_token);
    localStorage.setItem('salesai_user', JSON.stringify(userData));
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    authClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
  }, []);

  const requestPasswordResetOtp = useCallback(async (email: string) => {
    const res = await authClient.post('/auth/forgot-password', { email });
    return res.data;
  }, []);

  const resetPassword = useCallback(async (email: string, password: string, otpCode?: string) => {
    const payload: { email?: string; new_password: string; otp_code?: string } = {
      new_password: password,
    };
    if (email) payload.email = email;
    if (otpCode) payload.otp_code = otpCode;

    const res = await authClient.post<LoginResponse>('/auth/reset-password', payload);

    const { access_token, user: userData } = res.data;
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('salesai_token', access_token);
    localStorage.setItem('salesai_user', JSON.stringify(userData));
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    authClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
  }, []);

  const logout = useCallback(() => {
    try {
      authClient.post('/auth/logout').catch(() => {});
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem('salesai_token');
      localStorage.removeItem('salesai_user');
      delete axios.defaults.headers.common['Authorization'];
      delete authClient.defaults.headers.common['Authorization'];
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!token,
        login,
        register,
        requestPasswordResetOtp,
        resetPassword,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );

};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
