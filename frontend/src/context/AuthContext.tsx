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
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

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
      localStorage.setItem('salesai_token', token);
    } else {
      delete axios.defaults.headers.common['Authorization'];
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
        const res = await axios.get(`${API_BASE_URL}/auth/me`, {
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
    const res = await axios.post<LoginResponse>(`${API_BASE_URL}/auth/login`, {
      email,
      password,
    });

    const { access_token, user: userData } = res.data;
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('salesai_token', access_token);
    localStorage.setItem('salesai_user', JSON.stringify(userData));
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    const res = await axios.post<LoginResponse>(`${API_BASE_URL}/auth/register`, {
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
  }, []);

  const logout = useCallback(() => {
    try {
      axios.post(`${API_BASE_URL}/auth/logout`).catch(() => {});
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem('salesai_token');
      localStorage.removeItem('salesai_user');
      delete axios.defaults.headers.common['Authorization'];
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
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );

};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
