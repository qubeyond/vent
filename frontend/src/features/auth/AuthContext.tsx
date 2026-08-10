import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchMe, login as loginRequest } from "./api";
import { clearToken, getToken } from "../../shared/api/client";

interface AuthContextValue {
  isAuthenticated: boolean;
  isChecking: boolean;
  username: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [username, setUsername] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      setIsChecking(false);
      return;
    }
    fetchMe()
      .then((me) => {
        setUsername(me.username);
        setIsAuthenticated(true);
      })
      .catch(() => clearToken())
      .finally(() => setIsChecking(false));
  }, []);

  async function login(user: string, password: string) {
    await loginRequest(user, password);
    const me = await fetchMe();
    setUsername(me.username);
    setIsAuthenticated(true);
  }

  function logout() {
    clearToken();
    setIsAuthenticated(false);
    setUsername(null);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, isChecking, username, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
