import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import * as client from "./client";

interface AuthContextValue {
  isAuthenticated: boolean;
  userEmail: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(client.isAuthenticated());
  const [userEmail, setUserEmail] = useState(client.getUserEmail());

  // Server-side source of truth for identity — covers sessions that started
  // before email persistence existed, page reloads, and anything else that
  // could leave localStorage out of sync with who the token actually is.
  useEffect(() => {
    if (!isAuthenticated) return;
    client
      .fetchCurrentUser()
      .then((user) => setUserEmail(user.email))
      .catch(() => {
        /* if this fails, the regular 401 handling in apiFetch already
           redirects to /login — nothing extra to do here */
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const login = async (email: string, password: string) => {
    await client.login(email, password);
    setIsAuthenticated(true);
    setUserEmail(email);
  };

  const register = async (email: string, password: string) => {
    await client.register(email, password);
    setIsAuthenticated(true);
    setUserEmail(email);
  };

  const logout = () => {
    client.logout();
    setIsAuthenticated(false);
    setUserEmail(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, userEmail, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
