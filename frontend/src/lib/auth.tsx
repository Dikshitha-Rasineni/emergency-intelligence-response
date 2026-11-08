import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";
import { store } from "./store";

export type User = { id: string; name: string; email: string; role: "ADMIN" | "HOSPITAL" | "POLICE" | "FIRE" | "DISASTER";
  organization_id?: string | null; organization_name?: string | null };

type Ctx = { user: User | null; token: string | null; ready: boolean;
  login: (email: string, password: string) => Promise<User>; logout: () => void };
const AuthCtx = createContext<Ctx>(null as unknown as Ctx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(store.get("resq.session.token"));
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!token) { setUser(null); setReady(true); return; }
    api<User>("/auth/me").then(setUser).catch(() => { setToken(null); setUser(null); }).finally(() => setReady(true));
  }, [token]);

  useEffect(() => {
    const onLogout = () => { setToken(null); setUser(null); };
    window.addEventListener("resq:logout", onLogout);
    return () => window.removeEventListener("resq:logout", onLogout);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const r = await api<{ access_token: string; user: User }>("/auth/login", { method: "POST", json: { email, password } });
    store.set("resq.session.token", r.access_token);
    setToken(r.access_token);
    setUser(r.user);
    return r.user;
  }, []);
  const logout = useCallback(() => { store.remove("resq.session.token"); setToken(null); setUser(null); }, []);
  return <AuthCtx.Provider value={{ user, token, ready, login, logout }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
