import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Link, Navigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Brand } from "../components/Brand";
import { ErrorBox, Loading, Empty } from "../components/States";
import { DEPT_LABEL, timeAgo } from "../lib/format";

const TABS = ["System", "Users", "Organisations", "Resources", "Devices", "Knowledge", "Audit log", "Routing policy"] as const;
type Tab = (typeof TABS)[number];

function useData<T = any>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [err, setErr] = useState("");
  const reload = useCallback(() => { api<T>(path).then((d) => { setData(d); setErr(""); }).catch((e) => setErr(e.message)); }, [path]);
  useEffect(reload, [reload]);
  return { data, err, reload };
}

function Table({ head, rows, empty }: { head: string[]; rows: ReactNode[][]; empty: string }) {
  if (!rows.length) return <Empty title={empty} />;
  return (
    <div className="overflow-x-auto rounded-panel border border-line bg-surface">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-line bg-paper text-xs text-muted"><tr>{head.map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}</tr></thead>
        <tbody className="divide-y divide-line">{rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j} className="px-3 py-2 align-top">{c}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

function Form({ children, onSubmit, submit }: { children: ReactNode; onSubmit: (fd: FormData) => Promise<unknown>; submit: string }) {
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  return (
    <form className="panel mb-5 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4" onSubmit={async (e) => {
      e.preventDefault(); setErr(""); setOk("");
      const form = e.currentTarget;
      try { await onSubmit(new FormData(form)); form.reset(); setOk("Saved."); } catch (x) { setErr((x as Error).message); }
    }}>
      {children}
      <div className="flex items-end gap-3"><button className="btn-primary">{submit}</button>{ok && <span className="text-sm text-pri-low">{ok}</span>}</div>
      {err && <div className="sm:col-span-2 lg:col-span-4"><ErrorBox>{err}</ErrorBox></div>}
    </form>
  );
}
const F = ({ label, children }: { label: string; children: ReactNode }) => <label className="text-sm"><span className="label">{label}</span>{children}</label>;

function System() {
  const { data, err } = useData("/health");
  if (err) return <ErrorBox>{err}</ErrorBox>;
  if (!data) return <Loading />;
  const d: any = data;
  const row = (k: string, v: ReactNode, good: boolean) => [k, <span className={good ? "text-pri-low" : "text-pri-high"}>{v}</span>];
  return <Table head={["Component", "State"]} empty="" rows={[
    row("Database", d.database, d.database === "connected"), row("PostGIS", d.postgis, d.postgis !== "missing"),
    row("Text model", `${d.ai.text.provider} ${d.ai.text.model || ""}: ${d.ai.text.status}`, ["ready", "configured"].includes(d.ai.text.status)),
    row("Vision model", `${d.ai.vision.provider} ${d.ai.vision.model || ""}: ${d.ai.vision.status}`, ["ready", "configured"].includes(d.ai.vision.status)),
    row("Server speech-to-text", `${d.ai.speech.provider}: ${d.ai.speech.status}`, d.ai.speech.status === "configured"),
    row("Routing providers", d.routing.provider_order.join(", "), true),
    row("IoT device authentication", d.iot_device_auth, d.iot_device_auth === "enabled"),
    row("Live control-room connections", JSON.stringify(d.websocket_connections), true),
  ]} />;
}

function Users() {
  const { data, err, reload } = useData<any[]>("/admin/users");
  const orgs = useData<any[]>("/admin/organizations").data || [];
  return (<>
    <Form submit="Create user" onSubmit={async (fd) => { await api("/admin/users", { method: "POST", json: Object.fromEntries(fd) }); reload(); }}>
      <F label="Name"><input name="name" className="field" required /></F>
      <F label="Email"><input name="email" type="email" className="field" required /></F>
      <F label="Temporary password (10+ chars)"><input name="password" type="password" minLength={10} className="field" required /></F>
      <F label="Role"><select name="role" className="field">{["HOSPITAL", "POLICE", "FIRE", "DISASTER", "ADMIN"].map((r) => <option key={r}>{r}</option>)}</select></F>
      <F label="Organisation"><select name="organization_id" className="field"><option value="">None</option>{orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</select></F>
    </Form>
    {err && <ErrorBox>{err}</ErrorBox>}
    <Table head={["Name", "Email", "Role", "Organisation", "Status", ""]} empty="No users" rows={(data || []).map((u) => [u.name, u.email, DEPT_LABEL[u.role], u.organization_name || "None",
      u.is_active ? "Active" : "Disabled",
      <button className="btn-text" onClick={() => api(`/admin/users/${u.id}/active?active=${!u.is_active}`, { method: "POST" }).then(reload)}>{u.is_active ? "Disable" : "Enable"}</button>])} />
  </>);
}

function Orgs() {
  const { data, reload } = useData<any[]>("/admin/organizations");
  return (<>
    <Form submit="Add organisation" onSubmit={async (fd) => { await api("/admin/organizations", { method: "POST", json: { ...Object.fromEntries(fd), resource_id: fd.get("resource_id") || null } }); reload(); }}>
      <F label="Name"><input name="name" className="field" required /></F>
      <F label="Department"><select name="department" className="field">{["HOSPITAL", "POLICE", "FIRE", "DISASTER"].map((r) => <option key={r}>{r}</option>)}</select></F>
      <F label="Operates resource ID (optional)"><input name="resource_id" className="field" /></F>
    </Form>
    <Table head={["Organisation", "Department", "Resource", "Users"]} empty="No organisations" rows={(data || []).map((o) => [o.name, DEPT_LABEL[o.department], o.resource_id || "None", o.users])} />
  </>);
}

function Resources() {
  const { data, reload } = useData<any[]>("/admin/resources");
  return (<>
    <Form submit="Save resource" onSubmit={async (fd) => {
      const o: any = Object.fromEntries(fd);
      await api("/admin/resources", { method: "POST", json: { ...o, id: o.id || null, latitude: Number(o.latitude), longitude: Number(o.longitude), verified: o.verified === "on",
        capabilities: o.capabilities ? String(o.capabilities).split(",").map((s) => s.trim()) : [] } });
      reload();
    }}>
      <F label="ID (blank = new)"><input name="id" className="field" /></F>
      <F label="Name"><input name="name" className="field" required /></F>
      <F label="Type"><select name="resource_type" className="field">{["HOSPITAL", "AMBULANCE", "POLICE", "FIRE", "SHELTER", "DISASTER"].map((r) => <option key={r}>{r}</option>)}</select></F>
      <F label="Phone (only if verified)"><input name="phone" className="field" /></F>
      <F label="Latitude"><input name="latitude" type="number" step="any" className="field" required /></F>
      <F label="Longitude"><input name="longitude" type="number" step="any" className="field" required /></F>
      <F label="Capabilities (comma separated)"><input name="capabilities" className="field" /></F>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="verified" />Details verified with the facility</label>
    </Form>
    <Table head={["Name", "Type", "Location", "Source", "Verified", "Availability", ""]} empty="No resources" rows={(data || []).map((r) => [
      <span className="font-semibold">{r.name}<span className="block text-xs font-normal text-muted">{r.id}</span></span>, r.resource_type,
      <span className="tabular">{r.latitude.toFixed(4)}, {r.longitude.toFixed(4)}</span>, r.data_source, r.verified ? "Yes" : "No",
      r.availability ? `${r.availability.status.toLowerCase()}${r.availability.verified ? ` (reported ${timeAgo(r.availability.updated_at)})` : " (unverified)"}` : "unknown",
      <button className="btn-text text-sos" onClick={() => confirm(`Delete ${r.name}?`) && api(`/admin/resources/${r.id}`, { method: "DELETE" }).then(reload)}>Delete</button>])} />
  </>);
}

function Devices() {
  const { data, reload } = useData<any[]>("/admin/devices");
  return (<>
    <Form submit="Register device" onSubmit={async (fd) => {
      const o: any = Object.fromEntries(fd);
      await api("/admin/devices", { method: "POST", json: { ...o, latitude: o.latitude ? Number(o.latitude) : null, longitude: o.longitude ? Number(o.longitude) : null, active: true } });
      reload();
    }}>
      <F label="Device ID"><input name="device_id" className="field" required pattern="[A-Za-z0-9_.:\-]+" /></F>
      <F label="Name"><input name="name" className="field" /></F>
      <F label="Installed latitude"><input name="latitude" type="number" step="any" className="field" /></F>
      <F label="Installed longitude"><input name="longitude" type="number" step="any" className="field" /></F>
      <F label="Location label"><input name="location_label" className="field" /></F>
    </Form>
    <Table head={["Device", "Location", "Firmware", "Last seen", "Last reading"]} empty="No devices have reported yet" rows={(data || []).map((d) => [
      <span className="font-semibold">{d.device_id}<span className="block text-xs font-normal text-muted">{d.name}</span></span>,
      d.latitude != null ? <span>{d.location_label}<span className="tabular block text-xs text-muted">{d.latitude}, {d.longitude}</span></span> : <span className="text-pri-high">Not set: alerts cannot become incidents</span>,
      d.firmware_version || "?", d.last_seen_at ? `${timeAgo(d.last_seen_at)} via ${d.last_transport || "?"}` : "Never",
      d.last_reading ? `${d.last_reading.event_type}, ${d.last_reading.hazard_severity || "n/a"}` : "None"])} />
  </>);
}

function Knowledge() {
  const { data, reload } = useData<any[]>("/admin/knowledge");
  return (<>
    <Form submit="Add document" onSubmit={async (fd) => { await api("/admin/knowledge", { method: "POST", body: fd }); reload(); }}>
      <F label="Title"><input name="title" className="field" required /></F>
      <F label="Publisher (authority)"><input name="publisher" className="field" required placeholder="e.g. NDMA" /></F>
      <F label="Version / date"><input name="version" className="field" /></F>
      <F label="Source URL"><input name="source_url" type="url" className="field" /></F>
      <F label="Categories (comma separated codes)"><input name="categories" className="field" placeholder="fire, flood" /></F>
      <F label="Language"><select name="language" className="field">{["en", "te", "ta", "hi"].map((l) => <option key={l}>{l}</option>)}</select></F>
      <F label="Text file (.txt / .md)"><input name="file" type="file" accept=".txt,.md,text/plain" className="field" /></F>
      <F label="…or paste text"><textarea name="body" rows={2} className="field" /></F>
    </Form>
    <p className="mb-3 text-sm text-muted">Documents are used only after approval. Retrieval returns verbatim excerpts with their source. Nothing is generated.</p>
    <Table head={["Title", "Publisher", "Categories", "Chunks", "Status", ""]} empty="No knowledge documents. Add official guidance (for example NDMA, state fire services) to enable reference excerpts." rows={(data || []).map((d) => [
      d.title, d.publisher, d.categories.join(", ") || "all", d.chunks, d.approved ? <span className="text-pri-low">Approved</span> : <span className="text-pri-high">Awaiting approval</span>,
      <span className="flex gap-3"><button className="btn-text" onClick={() => api(`/admin/knowledge/${d.id}/approve?approved=${!d.approved}`, { method: "POST" }).then(reload)}>{d.approved ? "Withdraw" : "Approve"}</button>
        <button className="btn-text text-sos" onClick={() => confirm("Delete document?") && api(`/admin/knowledge/${d.id}`, { method: "DELETE" }).then(reload)}>Delete</button></span>])} />
  </>);
}

function Audit() {
  const { data } = useData<any>("/admin/audit?limit=200");
  return <Table head={["Time", "Actor", "Action", "Target", "Details"]} empty="No audit events" rows={(data?.items || []).map((a: any) => [
    <span className="tabular whitespace-nowrap">{new Date(a.at).toLocaleString()}</span>, a.actor, a.action, a.target_id || "", <code className="text-xs">{JSON.stringify(a.details)}</code>])} />;
}

function Policy() {
  const { data } = useData<any>("/admin/config");
  if (!data) return <Loading />;
  return (<div className="space-y-4">
    <p className="text-sm">Routing policy <strong>{data.routing_policy_version}</strong> is deterministic code: {data.routing_rules_source}. Each decision is stored with its reasons on the incident.</p>
    <Table head={["Department", "Fields it receives"]} empty="" rows={Object.entries(data.department_fields).map(([k, v]) => [DEPT_LABEL[k], (v as string[]).join(", ")])} />
    <Table head={["Category code", "Label"]} empty="" rows={data.categories.map((c: any) => [c.code, c.label])} />
    <p className="text-sm text-muted">Citizen interface languages: {data.ui_languages.join(", ")}</p>
  </div>);
}

export default function Admin() {
  const { user, ready, logout } = useAuth();
  const [tab, setTab] = useState<Tab>("System");
  if (!ready) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "ADMIN") return <Navigate to="/ops" replace />;
  const Body = { System, Users, Organisations: Orgs, Resources, Devices, Knowledge, "Audit log": Audit, "Routing policy": Policy }[tab];
  return (
    <div lang="en" className="min-h-screen">
      <header className="border-b border-line bg-surface">
        <div className="flex flex-wrap items-center gap-4 px-4 py-2.5">
          <Brand to="/admin" sub="Administration" />
          <Link to="/ops" className="text-sm font-semibold text-teal">All incidents</Link>
          <button onClick={logout} className="btn-quiet ml-auto px-3 py-1.5"><LogOut className="h-4 w-4" />Sign out</button>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-4" aria-label="Admin sections">
          {TABS.map((t) => <button key={t} onClick={() => setTab(t)} aria-current={tab === t}
            className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm font-semibold ${tab === t ? "border-teal text-ink" : "border-transparent text-muted hover:text-ink"}`}>{t}</button>)}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl p-4 sm:p-6"><h1 className="mb-4 text-xl font-bold">{tab}</h1><Body /></main>
    </div>
  );
}
