import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { ApiError, api } from "../api/client";
import type { User } from "../types";

const TOKEN_STORAGE_KEY = "ai_chat_platform_token";

function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStoredToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // Storage unavailable (private mode, blocked cookies, ...) -- the
    // session still works for the current page load, just won't persist.
  }
}

interface AuthContextValue {
  token: string | null;
  user: User | null;
  /** True while we still have to resolve a stored token into a user. */
  isBootstrapping: boolean;
  isSubmitting: boolean;
  authError: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(readStoredToken);
  const [user, setUser] = useState<User | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState<boolean>(() => readStoredToken() !== null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setIsBootstrapping(false);
      return;
    }
    let cancelled = false;
    setIsBootstrapping(true);
    api
      .me(token)
      .then((fetchedUser) => {
        if (!cancelled) setUser(fetchedUser);
      })
      .catch(() => {
        if (!cancelled) {
          setToken(null);
          writeStoredToken(null);
        }
      })
      .finally(() => {
        if (!cancelled) setIsBootstrapping(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = useCallback(async (email: string, password: string) => {
    setIsSubmitting(true);
    setAuthError(null);
    try {
      const result = await api.login(email, password);
      setToken(result.access_token);
      writeStoredToken(result.access_token);
    } catch (err) {
      setAuthError(err instanceof ApiError ? err.message : "Login failed. Please try again.");
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const register = useCallback(
    async (email: string, password: string) => {
      setIsSubmitting(true);
      setAuthError(null);
      try {
        await api.register(email, password);
        await login(email, password);
      } catch (err) {
        if (err instanceof ApiError) setAuthError(err.message);
        else if (!(err instanceof Error)) setAuthError("Registration failed. Please try again.");
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    [login],
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    writeStoredToken(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ token, user, isBootstrapping, isSubmitting, authError, login, register, logout }),
    [token, user, isBootstrapping, isSubmitting, authError, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
