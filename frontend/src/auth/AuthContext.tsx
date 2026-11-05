import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getApiError } from "../api/axios";
import { authService } from "../services/api";
import { setAccessToken } from "./tokenStore";
import type { RegisterPayload, RoleName, User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: string | null;
  roles: RoleName[];
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (payload: RegisterPayload) => Promise<void>;
  signOut: () => Promise<void>;
  updateCurrentUser: (updatedUser: User) => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
let restoreSessionPromise: ReturnType<typeof authService.refresh> | null = null;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  useEffect(() => {
    let active = true;
    restoreSessionPromise ??= authService.refresh();
    restoreSessionPromise
      .then((response) => {
        setAccessToken(response.access_token);
        if (active) setUser(response.usuario);
      })
      .catch(async (refreshError: unknown) => {
        const status = (refreshError as { response?: { status?: number } })
          ?.response?.status;
        if (status !== 401 && status !== 403 && active) {
          setError(getApiError(refreshError));
        }
        setAccessToken(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    const onExpired = () => {
      setAccessToken(null);
      setUser(null);
    };
    window.addEventListener("subastagro:session-expired", onExpired);
    return () => {
      active = false;
      window.removeEventListener("subastagro:session-expired", onExpired);
    };
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    setError(null);
    try {
      const response = await authService.login(email, password);
      setAccessToken(response.access_token);
      setUser(response.usuario);
    } catch (reason) {
      const message = getApiError(reason);
      setError(message);
      throw new Error(message);
    }
  }, []);

  const signUp = useCallback(async (payload: RegisterPayload) => {
    setError(null);
    try {
      await authService.register(payload);
    } catch (reason) {
      const message = getApiError(reason);
      setError(message);
      throw new Error(message);
    }
  }, []);

  const signOut = useCallback(async () => {
    try {
      await authService.logout();
    } catch (reason) {
      setError(getApiError(reason));
      throw reason;
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  }, []);
  const updateCurrentUser = useCallback((updatedUser: User) => {
    setUser(updatedUser);
  }, []);

  const roles = user?.roles.map((role) => role.nombre_rol) ?? [];
  const value = useMemo(
    () => ({ user, loading, error, roles, signIn, signUp, signOut, updateCurrentUser, clearError }),
    [user, loading, error, roles.join(","), signIn, signUp, signOut, updateCurrentUser, clearError],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return context;
}
