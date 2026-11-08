import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useAuth } from "../lib/auth";
import { ErrorBox } from "../components/States";
import { Brand } from "../components/Brand";
import { Radar } from "../components/Radar";

export default function Login() {
  const { login, user } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to={user.role === "ADMIN" ? "/admin" : "/ops"} replace />;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      const u = await login(email.trim().toLowerCase(), password);
      nav(u.role === "ADMIN" ? "/admin" : "/ops");
    } catch (e2) { setErr((e2 as Error).message); } finally { setBusy(false); }
  }
  return (
    <div lang="en" className="grid min-h-[calc(100vh-140px)] lg:grid-cols-2">
      <div className="dark-band relative hidden items-center justify-center overflow-hidden lg:flex">
        <div className="speed-lines absolute inset-0" />
        <Radar size={460} />
        <p className="absolute bottom-10 left-10 max-w-sm text-white/80"><span className="block text-2xl font-black text-white">Control-room console</span>Live incidents routed to your service, with an English brief and acknowledgement deadlines.</p>
      </div>
      <div className="flex items-center justify-center px-4 py-14">
        <div className="w-full max-w-sm animate-rise">
          <Brand sub="Control-room sign in" />
          <form onSubmit={submit} className="panel mt-8 space-y-4 p-7">
            <div><label className="label" htmlFor="em">Work email</label>
              <input id="em" type="email" autoComplete="username" className="field" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
            <div><label className="label" htmlFor="pw">Password</label>
              <input id="pw" type="password" autoComplete="current-password" className="field" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
            {err && <ErrorBox>{err}</ErrorBox>}
            <button className="btn-primary w-full py-3.5" disabled={busy}>{busy && <Loader2 className="h-4 w-4 animate-spin" />}Sign in</button>
          </form>
          <p className="mt-4 text-sm text-muted">Accounts are created by your RESQ.AI administrator. Citizens do not need an account to report.</p>
        </div>
      </div>
    </div>
  );
}
