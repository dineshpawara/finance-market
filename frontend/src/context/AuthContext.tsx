/**
 * Reactive Authentication & Session Context
 * ==========================================
 * Manages user authentication state, JWT Bearer token lifecycle,
 * and session persistence across page refreshes.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  type UserSummary,
  type LoginResponse,
  loginApi,
  verify2FaLoginApi,
} from '../api/auth';

interface AuthContextType {
  user: UserSummary | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginWithPassword: (password: string) => Promise<LoginResponse>;
  complete2Fa: (tempToken: string, code: string) => Promise<LoginResponse>;
  logout: () => void;
}

const STORAGE_KEY_TOKEN = 'finance_market_access_token';
const STORAGE_KEY_USER = 'finance_market_user';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserSummary | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Hydrate session from localStorage on application startup
  useEffect(() => {
    try {
      const storedToken = localStorage.getItem(STORAGE_KEY_TOKEN);
      const storedUser = localStorage.getItem(STORAGE_KEY_USER);

      if (storedToken && storedUser) {
        // Verify JWT token expiration before hydrating
        try {
          const payloadPart = storedToken.split('.')[1];
          if (payloadPart) {
            const payload = JSON.parse(atob(payloadPart));
            if (payload.exp && payload.exp * 1000 < Date.now()) {
              localStorage.removeItem(STORAGE_KEY_TOKEN);
              localStorage.removeItem(STORAGE_KEY_USER);
              setIsLoading(false);
              return;
            }
          }
        } catch {
          // Ignore parse errors and attempt hydration
        }

        setAccessToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY_TOKEN);
      localStorage.removeItem(STORAGE_KEY_USER);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Stage 1: Authenticate with password
   */
  const loginWithPassword = async (password: string): Promise<LoginResponse> => {
    const res = await loginApi(password);

    // If 2FA is not required and direct access token was issued
    if (!res.requires_2fa && res.access_token && res.user) {
      localStorage.setItem(STORAGE_KEY_TOKEN, res.access_token);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(res.user));
      setAccessToken(res.access_token);
      setUser(res.user);
    }

    return res;
  };

  /**
   * Stage 2: Validate 2FA passcode and establish authenticated session
   */
  const complete2Fa = async (tempToken: string, code: string): Promise<LoginResponse> => {
    const res = await verify2FaLoginApi(tempToken, code);

    if (res.access_token && res.user) {
      localStorage.setItem(STORAGE_KEY_TOKEN, res.access_token);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(res.user));
      setAccessToken(res.access_token);
      setUser(res.user);
    }

    return res;
  };

  /**
   * Terminate active session and clear persisted credentials
   */
  const logout = () => {
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    localStorage.removeItem(STORAGE_KEY_USER);
    setAccessToken(null);
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    accessToken,
    isAuthenticated: Boolean(accessToken && user),
    isLoading,
    loginWithPassword,
    complete2Fa,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
