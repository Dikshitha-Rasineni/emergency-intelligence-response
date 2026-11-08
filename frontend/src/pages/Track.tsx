import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Check, Copy, ExternalLink, MapPin, RefreshCw, ShieldAlert, Sparkles } from "lucide-react";
import { api, ApiError } from "../lib/api";
import { saveReport, savedReports, tokenFor } from "../lib/store";
import { PriorityRing } from "../components/PriorityRing";
import { MapView, type MapMarker } from "../components/MapView";

const UNIT_EMOJI: Record<string, string> = { AMBULANCE: "🚑", FIRE_TENDER: "🚒", RESCUE_TENDER: "🚒", POLICE_PATROL: "🚓",
  HIGHWAY_PATROL: "🚓", DISASTER_TEAM: "🛟", RESCUE_BOAT: "🚤" };

function HelpOnTheWay({ v }: { v: any }) {
  const { t } = useTranslation();
  const ds: any[] = v.dispatches || [];
  if (!ds.length) return null;
  const markers: MapMarker[] = [];
  if (v.location.latitude != null) markers.push({ lat: v.location.latitude, lng: v.location.longitude, kind: "incident", label: t("report.location") });
  ds.forEach((d) => d.latitude != null && d.status !== "COMPLETED" &&
    markers.push({ lat: d.latitude, lng: d.longitude, kind: d.department, unit: d.unit_type, label: `${t(`help.units.${d.unit_type}`)} ${d.call_sign.split(" ").pop()}` }));
  const simulated = ds.some((d) => d.position_source === "SIMULATED");
  return (
    <section className="overflow-hidden rounded-panel bg-surface shadow-lift">
      <div className="dark-band relative overflow-hidden px-6 py-5 text-white">
        <div className="speed-lines absolute inset-0 opacity-60" />
        <h2 className="relative flex items-center gap-2 text-xl font-black"><span className="h-2.5 w-2.5 animate-blink rounded-full bg-sos-glow" />{t("help.title")}</h2>
        <p className="relative mt-1 text-sm text-white/75">{t("help.stay")}</p>
      </div>
      <div className="grid gap-5 p-5 lg:grid-cols-[1fr_1.1fr]">
        <ul className="space-y-3">
          {ds.map((d, i) => {
            const moving = d.status === "ASSIGNED" || d.status === "EN_ROUTE";
            return (
              <li key={i} className="rounded-2xl border border-line bg-paper p-4">
                <div className="flex items-center gap-3">
                  <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-white text-2xl shadow-card">{UNIT_EMOJI[d.unit_type] || "🚨"}</span>
                  <div className="min-w-0">
                    <p className="font-black">{t(`help.units.${d.unit_type}`)} <span className="tabular text-sm font-semibold text-muted">{d.call_sign.split(" ").pop()}</span></p>
                    <p className={`text-sm font-bold ${d.status === "ON_SCENE" ? "text-pri-low" : "text-teal-mid"}`}>{t(`help.status.${d.status}`)}</p>
                  </div>
                  {moving && d.eta_remaining_min != null && (
                    <span className="ml-auto shrink-0 rounded-xl bg-navy px-3 py-2 text-center text-white">
                      <span className="block text-2xl font-black leading-none">{d.eta_remaining_min <= 0 ? "…" : d.eta_remaining_min}</span>
                      <span className="text-[11px] font-semibold text-white/70">min</span>
                    </span>
                  )}
                </div>
                {moving && (
                  <div className="mt-3">
                    <div className="h-2 overflow-hidden rounded-full bg-line"><div className="h-full rounded-full bg-gradient-to-r from-teal-mid to-teal-glow transition-all duration-1000" style={{ width: `${Math.max(4, d.progress * 100)}%` }} /></div>
                    <p className="mt-1.5 text-xs font-semibold text-muted">{d.eta_remaining_min > 0 ? t("help.eta", { n: d.eta_remaining_min }) : t("help.arriving")}</p>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
        <div>
          <MapView height={300} markers={markers} fitKey={`${v.incident_id}:${ds.length}`} />
          {simulated && <p className="mt-2 text-xs text-muted">{t("help.simulated")}</p>}
        </div>
      </div>
    </section>
  );
}
import { ErrorBox, Loading } from "../components/States";
import { clock } from "../lib/format";

type View = any;

export function TrackLookup() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const [id, setId] = useState("");
  const [token, setToken] = useState("");
  const [err, setErr] = useState("");
  const saved = savedReports();
  async function open(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    const rid = id.trim().toUpperCase();
    try {
      await api(`/incidents/${rid}/track`, { token: token.trim() });
      saveReport({ id: rid, token: token.trim(), at: new Date().toISOString() });
      nav(`/track/${rid}`);
    } catch (e2) {
      setErr((e2 as ApiError).status === 404 ? t("track.notFound") : t("track.forbidden"));
    }
  }
  return (
    <div>
    <div className="dark-band text-white"><div className="mx-auto max-w-xl px-4 pb-24 pt-10 sm:px-6">
      <h1 className="text-4xl font-black">{t("track.title")}</h1>
      <p className="mt-2 text-white/70">{t("track.intro")}</p></div></div>
    <div className="relative mx-auto -mt-16 max-w-xl px-4 pb-12 sm:px-6">
      <form onSubmit={open} className="panel space-y-4 p-6">
        <div><label className="label" htmlFor="rid">{t("track.id")}</label>
          <input id="rid" className="field tabular" value={id} onChange={(e) => setId(e.target.value)} placeholder="INC-1A2B3C4D" required /></div>
        <div><label className="label" htmlFor="tok">{t("track.token")}</label>
          <input id="tok" className="field font-mono text-sm" value={token} onChange={(e) => setToken(e.target.value)} required autoComplete="off" /></div>
        {err && <ErrorBox>{err}</ErrorBox>}
        <button className="btn-primary">{t("track.open")}</button>
      </form>
      {saved.length > 0 && (
        <div className="mt-10">
          <h2 className="font-bold">{t("track.recent")}</h2>
          <ul className="panel mt-2 divide-y divide-line overflow-hidden">
            {saved.map((r) => (
              <li key={r.id}><Link to={`/track/${r.id}`} className="flex justify-between px-4 py-3 hover:bg-paper">
                <span className="tabular font-semibold">{r.id}</span><span className="text-sm text-muted">{new Date(r.at).toLocaleString()}</span></Link></li>
            ))}
          </ul>
        </div>
      )}
    </div>
    </div>
  );
}

function Explanation({ codes }: { codes: string[] }) {
  const { t } = useTranslation();
  return (
    <ul className="space-y-1.5 text-[15px]">
      {codes.map((c) => {
        const [k, v] = c.split(":");
        const value = k === "category" ? t(`categories.${v}`) : k === "hazard" ? t(`hazards.${v}`) : v;
        return <li key={c} className="flex items-start gap-2"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-mid" /><span>{t(`evidence.${k}`, { value })}</span></li>;
      })}
    </ul>
  );
}

export default function TrackDetail() {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const state = (useLocation().state || {}) as { justSent?: boolean; uploadErrors?: string[] };
  const token = tokenFor(id);
  const [v, setV] = useState<View | null>(null);
  const [err, setErr] = useState<string>("");
  const [nearby, setNearby] = useState<any[] | null>(null);
  const [copied, setCopied] = useState(false);
  const [ai, setAi] = useState<any>(null);

  const load = useCallback(() => {
    if (!token) return;
    api(`/incidents/${id}/track`, { token }).then((d) => { setV(d); setErr(""); })
      .catch((e: ApiError) => setErr(e.status === 403 ? t("track.forbidden") : e.message));
  }, [id, token, t]);

  const moving = (v?.dispatches || []).some((d: any) => d.status === "ASSIGNED" || d.status === "EN_ROUTE");
  useEffect(() => { load(); const iv = setInterval(load, moving ? 3000 : 8000); return () => clearInterval(iv); }, [load, moving]);
  useEffect(() => {
    if (v?.location?.latitude != null && nearby === null) {
      api(`/resources/nearby?latitude=${v.location.latitude}&longitude=${v.location.longitude}&radius=10`).then((r) => setNearby(r.slice(0, 6))).catch(() => setNearby([]));
    }
  }, [v, nearby]);

  useEffect(() => {  // GenAI (RAG) safety steps: ask again a few times while the model is still writing them
    if (!token || ai?.generated) return;
    let n = 0;
    const get = () => api(`/incidents/${id}/genai-guidance`, { token }).then((d) => d?.generated && setAi(d)).catch(() => undefined);
    get(); const iv = setInterval(() => { if (++n > 6) clearInterval(iv); else get(); }, 10000);
    return () => clearInterval(iv);
  }, [id, token, ai?.generated]);

  if (!token) return <TrackLookup />;
  if (err && !v) return <div className="mx-auto max-w-3xl p-6"><ErrorBox onRetry={load} retryLabel={t("common.retry")}>{err}</ErrorBox></div>;
  if (!v) return <Loading label={t("common.loading")} />;

  const a = v.assessment;
  const markers: MapMarker[] = [];
  if (v.location.latitude != null) markers.push({ lat: v.location.latitude, lng: v.location.longitude, kind: "incident", label: t("report.location") });
  (nearby || []).forEach((r) => markers.push({ lat: r.latitude, lng: r.longitude, kind: r.type, label: r.name }));
  const acked = (d: any) => d.status === "ACKNOWLEDGED";

  return (
    <div>
      <div className="dark-band relative overflow-hidden text-white">
        <div className="speed-lines absolute inset-0" />
        <div className="relative mx-auto flex max-w-5xl flex-wrap items-end justify-between gap-4 px-4 pb-24 pt-10 sm:px-6">
          <div className="animate-rise">
            {state.justSent && <p className="mb-3 inline-flex items-center gap-2 rounded-full bg-pri-low px-3 py-1 text-sm font-bold"><Check className="h-4 w-4" />{t("result.received")}</p>}
            <p className="text-sm text-white/60">{t("result.reportId")}</p>
            <h1 className="tabular text-4xl font-black sm:text-5xl">{v.incident_id}</h1>
            <p className="mt-2 flex flex-wrap items-center gap-2 text-lg font-semibold">
              <span className="rounded-full bg-white/15 px-3 py-0.5">{t(`categories.${v.category}`)}</span>
              <span className="inline-flex items-center gap-2 rounded-full bg-teal-mid/80 px-3 py-0.5"><span className="h-2 w-2 animate-blink rounded-full bg-white" />{t(`status.${v.status}`)}</span>
            </p>
          </div>
          <button className="btn-ghost-dark" onClick={load}><RefreshCw className="h-4 w-4" />{t("result.refresh")}</button>
        </div>
      </div>

      <div className="relative mx-auto -mt-16 max-w-5xl space-y-6 px-4 pb-12 sm:px-6">
        {state.uploadErrors?.map((e) => <ErrorBox key={e}>{e}</ErrorBox>)}
        {state.justSent && (
          <div className="panel border-2 !border-sun p-5">
            <p className="text-sm font-semibold">{t("result.keepToken")}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="text-sm text-muted">{t("result.trackingCode")}:</span>
              <code className="break-all rounded-lg bg-paper px-3 py-1.5 text-sm font-semibold">{token}</code>
              <button className="btn-text" onClick={() => { navigator.clipboard?.writeText(`${v.incident_id} ${token}`); setCopied(true); }}>
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}{copied ? t("result.copied") : t("result.copy")}</button>
            </div>
          </div>
        )}
        {v.merged && <p className="panel p-4 text-sm font-semibold text-teal">{t("result.merged")}</p>}
        <HelpOnTheWay v={v} />

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="panel p-6">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-lg font-black">{t("result.priority")}</h2>
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${a.status === "pending" ? "bg-sun/20 text-pri-moderate" : "bg-teal-soft text-teal"}`}>
                {a.status === "pending" && <span className="h-1.5 w-1.5 animate-blink rounded-full bg-pri-moderate" />}
                {a.status === "pending" ? t("result.assessmentPending") : t("result.assessmentComplete")}</span>
            </div>
            {a.insufficient_evidence ? (
              <p className="flex gap-2 rounded-xl bg-paper p-4 text-[15px]"><ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-pri-moderate" />{t("result.noConfirmed")}</p>
            ) : (
              <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center">
                <PriorityRing score={a.priority_score} severity={a.severity} label={a.severity ? t(`levels.${a.severity}`) : ""} />
                <div className="w-full min-w-0 sm:flex-1">
                  <h3 className="mb-2 text-sm font-black">{t("result.why")}</h3>
                  <Explanation codes={a.evidence_codes || []} />
                </div>
              </div>
            )}
            <p className={`mt-5 flex items-center gap-1.5 text-sm font-semibold ${v.location.verified ? "text-pri-low" : "text-pri-moderate"}`}>
              <MapPin className="h-4 w-4" />{v.location.verified ? t("result.locVerified") : t("result.locUnverified")}</p>
          </section>

          <section className="relative overflow-hidden rounded-panel p-6 text-white shadow-lift" style={{ backgroundImage: "linear-gradient(145deg,#0E8C8F,#0E5F63 55%,#0B3B47)" }}>
            <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full border-[18px] border-white/10" />
            <h2 className="relative text-lg font-black">{t("result.guidance")}</h2>
            {v.guidance.language_fallback && <p className="relative mt-1 text-xs text-white/75">{t("result.guidanceFallback")}</p>}
            {ai?.generated && <p className="relative mt-1 flex items-center gap-1.5 text-xs font-bold text-white/85"><Sparkles className="h-3.5 w-3.5" />{t("result.genaiGuidance")}</p>}
            <ol className="relative mt-4 space-y-3 text-[15px] leading-relaxed" lang={ai?.generated ? ai.language : v.guidance.language}>
              {(ai?.generated ? ai.steps : v.guidance.items).map((g: string, n: number) => (
                <li key={g} className="flex gap-3"><span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white text-xs font-black text-teal">{n + 1}</span><span>{g}</span></li>
              ))}
            </ol>
            {ai?.generated && ai.avoid?.length > 0 && (
              <ul className="relative mt-4 space-y-1.5 text-[15px]" lang={ai.language}>
                {ai.avoid.map((g: string) => <li key={g} className="flex gap-2"><span className="font-black text-[#FFB4BF]">✕</span>{g}</li>)}
              </ul>)}
            <p className="relative mt-5 text-xs text-white/70">{t("result.guidanceSource")}{ai?.generated && ai.citations?.length ? ` · ${ai.citations.map((c: any) => c.title).join("; ")}` : ""}</p>
          </section>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="panel p-6">
            <h2 className="text-lg font-black">{t("result.notified")}</h2>
            {v.departments.length === 0 ? <p className="mt-2 text-sm text-muted">{t("result.noneNotified")}</p> : (
              <ul className="mt-4 space-y-2">
                {v.departments.map((d: any) => (
                  <li key={d.department} className="flex items-center gap-3 rounded-xl bg-paper px-4 py-3">
                    <span className={`relative flex h-3 w-3 rounded-full ${acked(d) ? "bg-pri-low" : "bg-sun"}`}>
                      {!acked(d) && <span className="absolute inset-0 animate-ping rounded-full bg-sun" />}
                    </span>
                    <span className="font-semibold">{t(`departments.${d.department}`)}</span>
                    <span className={`ml-auto text-sm font-bold ${acked(d) ? "text-pri-low" : "text-muted"}`}>{t(`notification.${d.status}`)}</span>
                  </li>
                ))}
              </ul>
            )}
            <h2 className="mt-7 text-lg font-black">{t("result.updates")}</h2>
            {v.updates.length === 0 ? <p className="mt-2 text-sm text-muted">{t("result.noUpdates")}</p> : (
              <ol className="mt-3 space-y-3 border-l-2 border-teal-mid/40 pl-4">
                {v.updates.map((u: any, i: number) => (
                  <li key={i} className="relative text-[15px]"><span className="absolute -left-[23px] top-1.5 h-3 w-3 rounded-full border-2 border-white bg-teal-mid" />
                    <span className="tabular text-sm text-muted">{clock(u.at)}</span>{" "}
                    <strong>{u.department ? t(`departments.${u.department}`) : ""}</strong> {u.status ? t(`status.${u.status}`) : ""}
                    {u.note && <span className="block text-muted" lang={u.note_translated ? v.guidance.language : "en"}>{u.note}</span>}
                    {u.note_translated && <details className="text-xs text-muted"><summary className="cursor-pointer">{t("help.translated")} · {t("help.showOriginal")}</summary><span lang="en">{u.note_original}</span></details>}</li>
                ))}
              </ol>
            )}
            {v.media.length > 0 && (<>
              <h2 className="mt-7 text-lg font-black">{t("result.photos")}</h2>
              <ul className="mt-2 flex flex-wrap gap-2 text-sm">{v.media.map((m: any, i: number) => <li key={m.id} className="rounded-full bg-paper px-3 py-1 font-semibold">#{i + 1} {t(`media.${m.status}`)}</li>)}</ul>
            </>)}
          </section>

          <section className="panel p-6">
            <h2 className="text-lg font-black">{t("result.nearby")}</h2>
            {markers.length > 0 && <div className="mt-4"><MapView height={240} markers={markers} /></div>}
            {nearby === null && v.location.latitude != null && <Loading label={t("common.loading")} />}
            {nearby?.length === 0 && <p className="mt-2 text-sm text-muted">{t("result.nearbyNone")}</p>}
            <ul className="mt-4 space-y-2">
              {(nearby || []).map((r) => (
                <li key={r.id} className="flex items-start justify-between gap-3 rounded-xl bg-paper px-4 py-3">
                  <div>
                    <p className="font-bold">{r.name} {r.data_source === "DEMO_SEED" && <span className="ml-1 rounded bg-line px-1.5 py-0.5 text-[11px] font-semibold text-muted">{t("result.demoData")}</span>}
                      {r.data_source === "OSM" && <span className="ml-1 rounded bg-teal-soft px-1.5 py-0.5 text-[11px] font-semibold text-teal">OpenStreetMap</span>}</p>
                    <p className="text-sm text-muted">{t(`departments.${r.type === "AMBULANCE" ? "HOSPITAL" : r.type === "SHELTER" ? "DISASTER" : r.type}`)}, {t("result.straightLine", { km: r.distance_km })}</p>
                    {r.availability_status === "UNKNOWN" && <p className="text-xs text-muted">{t("result.availabilityUnknown")}</p>}
                    {r.phone && <a className="text-sm font-semibold text-teal" href={`tel:${r.phone}`}>{r.phone}</a>}
                  </div>
                  <a className="btn-text shrink-0" href={r.navigation_url} target="_blank" rel="noreferrer">{t("result.directions")}<ExternalLink className="h-3.5 w-3.5" /></a>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
