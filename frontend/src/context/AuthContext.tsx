// Auth context providing login/register/logout and user state

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { User } from "../types/auth";
import * as authApi from "../api/auth";
import {
  clearAuth,
  getAuthToken,
  getAuthUser,
  getAllGameSessions,
  saveAuthToken,
  saveAuthUser,
} from "../utils/storage";

interface AuthContextValue {
  user: User | null;
  authToken: string | null;
  isLoading: boolean;
  showAuthModal: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function linkExistingSessions(authToken: string): Promise<void> {
  const sessions = getAllGameSessions();
  const tokens = sessions.map((s) => s.token);
  if (tokens.length === 0) return;
  try {
    await authApi.linkSessions(authToken, tokens);
  } catch {
    // Linking is best-effort -- don't block login/register on failure
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    // Initialize from localStorage for instant UI (validated on mount)
    const stored = getAuthUser();
    if (stored && getAuthToken()) {
      return { ...stored, created_at: "" } as User;
    }
    return null;
  });
  const [authToken, setAuthToken] = useState<string | null>(() =>
    getAuthToken(),
  );
  const [isLoading, setIsLoading] = useState(() => !!getAuthToken());
  const [showAuthModal, setShowAuthModal] = useState(false);

  const openAuthModal = useCallback(() => setShowAuthModal(true), []);
  const closeAuthModal = useCallback(() => setShowAuthModal(false), []);

  // Validate stored token on mount
  useEffect(() => {
    const storedToken = getAuthToken();
    if (!storedToken) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;

    async function validate() {
      try {
        const profile = await authApi.getProfile(storedToken!);
        if (!cancelled) {
          setUser(profile);
          setAuthToken(storedToken);
          saveAuthUser({ id: profile.id, username: profile.username });
        }
      } catch {
        if (!cancelled) {
          clearAuth();
          setUser(null);
          setAuthToken(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    validate();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const response = await authApi.login(username, password);
    saveAuthToken(response.token);
    saveAuthUser({ id: response.user.id, username: response.user.username });
    setAuthToken(response.token);
    setUser(response.user);
    await linkExistingSessions(response.token);
  }, []);

  const register = useCallback(async (username: string, password: string) => {
    const response = await authApi.register(username, password);
    saveAuthToken(response.token);
    saveAuthUser({ id: response.user.id, username: response.user.username });
    setAuthToken(response.token);
    setUser(response.user);
    await linkExistingSessions(response.token);
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
    setAuthToken(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, authToken, isLoading, showAuthModal, openAuthModal, closeAuthModal, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
