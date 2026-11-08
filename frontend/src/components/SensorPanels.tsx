import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Car, Cpu, Droplets, Flame, Loader2, Radio, Wind, Zap } from "lucide-react";
import { api } from "../lib/api";
import { DEPT_LABEL, clock, timeAgo } from "../lib/format";

const TYPE_META: Record<string, { label: string; icon: typeof Car; tone: string }> = {
  ACCIDENT: { label: "Crash", icon: Car, tone: "from-[#FF4A64] to-[#C8102E]" },
  FIRE: { label: "Fire / smoke", icon: Flame, tone: "from-[#FF8A3D] to-[#C2571A]" },
  GAS: { label: "Gas leak", icon: Wind, tone: "from-[#F5B700] to-[#B07F00]" },
  FLOOD: { label: "Flood", icon: Droplets, tone: "from-[#5B8DEF] to-[#1F3A93]" },
};
const UNIT: Record<string, string> = { g: "g", N: "N", degC: "°C", cm: "cm", adc_delta: "sensor units" };
const SIG = (csq?: number | null) => (csq == null || csq === 99 ? null : csq >= 20 ? "excellent" : csq >= 15 ? "good" : csq >= 10 ? "fair" : "weak");
const SENSOR_NAME: Record<string, string> = { fsr: "force sensor", mpu6050: "accelerometer" };
const fmt = (v: number | null, u?: string) => (v == null ? "" : `${Math.round(v * 10) / 10} ${UNIT[u || ""] ?? u ?? ""}`.trim());

/** Banner on an incident that a hardware unit detected: what it read, and who was alerted automatically. */
export function SensorBanner({ v }: { v: any }) {
  const s = v.sensor_evidence?.[0];
  if (!s) return null;
  const meta = TYPE_META[s.event_type] || TYPE_META.ACCIDENT;
  const Icon = meta.icon;
  const sent: any[] = v.dispatched_to || [];
  return (
    <section className="dark-band relative mt-4 overflow-hidden rounded-panel p-5 text-white shadow-lift">
      <div className="speed-lines absolute inset-0 opacity-60" />
      <div className="relative flex flex-wrap items-start gap-4">
        <span className={`relative grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br ${meta.tone} shadow-glowred`}>
          <span className="absolute inset-0 animate-ring rounded-2xl border-2 border-sos-glow/70" />
          <Icon className="h-7 w-7" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-2 text-xs font-bold text-teal-glow"><Cpu className="h-3.5 w-3.5" />Detected by hardware sensor</p>
          <h2 className="mt-0.5 text-xl font-black">{s.reason?.replace(" (console demo trigger)", "") || meta.label}</h2>
          <p className="text-sm text-white/75">{s.device_location || s.device_name} <span className="tabular text-white/50">· {s.device_id}</span></p>
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            {s.observed_value != null && <span className="rounded-full bg-white/15 px-3 py-1 font-bold">Reading {fmt(s.observed_value, s.unit)}{s.threshold_value != null && <span className="font-normal text-white/70"> (limit {fmt(s.threshold_value, s.unit)})</span>}</span>}
            {s.transport === "GPRS" && <span className="rounded-full bg-white/15 px-3 py-1">Sent over SIM{SIG(s.signal_quality) ? ` · signal ${SIG(s.signal_quality)} (${s.signal_quality}/31)` : ""}</span>}
            {s.sensor && SENSOR_NAME[s.sensor] && <span className="rounded-full bg-white/15 px-3 py-1">ESP32 {SENSOR_NAME[s.sensor]}{s.raw_adc != null ? ` · ADC ${s.raw_adc}` : ""}</span>}
            {s.severity && <span className={`rounded-full px-3 py-1 font-bold ${s.severe ? "bg-sos-glow/30 text-[#FFD0D7]" : "bg-white/15"}`}>Device grade: {s.severity.toLowerCase()}</span>}
            <span className="rounded-full bg-white/15 px-3 py-1">Detected {clock(s.timestamp)}</span>
          </div>
        </div>
      </div>
      {sent.length > 0 && (
        <div className="relative mt-4 border-t border-white/15 pt-4">
          <p className="text-sm font-bold">Alerted automatically, no phone call needed</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {sent.map((d) => (
              <span key={d.department} className="flex items-center gap-2 rounded-xl bg-white/10 px-3 py-2 text-sm">
                <span className={`h-2.5 w-2.5 rounded-full ${d.status === "ACKNOWLEDGED" ? "bg-[#9CF5D0]" : "animate-blink bg-sun"}`} />
                <strong>{DEPT_LABEL[d.department]}</strong>
                <span className="text-white/70">{d.role?.toLowerCase()} · {d.status === "ACKNOWLEDGED" ? "acknowledged" : "alerted"}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

/** Sensor network: every registered unit, its last reading, and (admin, demo) a button per alert type. */
export function SensorConsole({ isAdmin }: { isAdmin: boolean }) {
  const [devices, setDevices] = useState<any[]>([]);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState<{ text: string; id?: string } | null>(null);
  const navigate = useNavigate();
  const load = useCallback(() => { api("/iot/devices").then(setDevices).catch(() => undefined); }, []);
  useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t); }, [load]);

  async function trigger(device: string, type: string) {
    setBusy(device + type); setMsg(null);
    try {
      const r = await api<any>(`/iot/devices/${device}/demo-alert`, { method: "POST", json: { event_type: type } });
      setMsg({ text: `${r.status === "MERGED_INTO_INCIDENT" ? "Attached to" : "Created"} ${r.incident_id}, priority ${r.priority_score ?? "–"}. Services alerted automatically.`, id: r.incident_id });
      load();
    } catch (e) { setMsg({ text: (e as Error).message }); } finally { setBusy(""); }
  }

  return (
    <div className="h-full overflow-y-auto p-5">
      <div className="dark-band relative overflow-hidden rounded-panel p-6 text-white shadow-lift">
        <div className="speed-lines absolute inset-0 opacity-60" />
        <div className="relative">
          <p className="flex items-center gap-2 text-sm font-bold text-teal-glow"><Radio className="h-4 w-4" />Sensor network</p>
          <h1 className="mt-1 text-2xl font-black">When the car crashes, the car calls for help.</h1>
          <p className="mt-2 max-w-measure text-white/75">An ESP32 inside the car reads a force sensor behind the dashboard. When the crash force crosses the limit it sends the reading over its own SIM card. RESQ.AI creates the incident, GenAI writes each service its brief, and hospital, police and fire are alerted with the nearest units dispatched.</p>
          {msg && (
            <p className="mt-4 inline-flex flex-wrap items-center gap-3 rounded-xl bg-white/15 px-4 py-2 text-sm font-semibold">
              <Zap className="h-4 w-4 text-sun" />{msg.text}
              {msg.id && <button className="underline" onClick={() => navigate(`/ops/${msg.id}`)}>Open incident</button>}
            </p>
          )}
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        {devices.map((d) => {
          const last = d.last_event;
          const online = d.last_seen_at && Date.now() - new Date(d.last_seen_at).getTime() < 10 * 60 * 1000;
          return (
            <article key={d.device_id} className="panel p-5">
              <div className="flex items-start gap-3">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-teal-soft text-teal"><Cpu className="h-5 w-5" /></span>
                <div className="min-w-0">
                  <h2 className="font-black">{d.name || d.device_id}</h2>
                  <p className="text-sm text-muted">{d.location_label}</p>
                  <p className="tabular mt-0.5 text-xs text-muted">{d.device_id}</p>
                </div>
                <span className={`ml-auto flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${online ? "bg-pri-low/15 text-pri-low" : "bg-paper text-muted"}`}>
                  <span className={`h-2 w-2 rounded-full ${online ? "animate-blink bg-pri-low" : "bg-muted/50"}`} />{online ? "Online" : d.last_seen_at ? `Seen ${timeAgo(d.last_seen_at)}` : "Waiting for first signal"}
                </span>
              </div>
              <div className="mt-3 rounded-xl bg-paper px-3 py-2 text-sm">
                {last ? (<>
                  <span className="font-semibold">{TYPE_META[last.event_type]?.label || "Telemetry"}</span>{" "}
                  <span className="text-muted">{last.reason?.replace(" (console demo trigger)", "")} {fmt(last.observed_value, last.measurement_unit)} · {clock(last.timestamp)}</span>
                  {last.incident_id && <button className="ml-2 font-bold text-teal-mid underline" onClick={() => navigate(`/ops/${last.incident_id}`)}>{last.incident_id}</button>}
                </>) : <span className="text-muted">No readings yet.</span>}
                <p className="text-xs text-muted">{d.alerts_total} qualified alert(s) so far
                  {d.transport === "GPRS" && ` · via SIM${SIG(d.signal_quality) ? `, signal ${SIG(d.signal_quality)} (${d.signal_quality}/31)` : ""}`}
                  {last?.fsr_raw_adc != null && ` · last ADC ${last.fsr_raw_adc}`}</p>
              </div>
              {isAdmin && (
                <div className="mt-4">
                  <p className="text-xs font-bold text-muted">Demo: send an alert from this unit</p>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    {Object.entries(TYPE_META).map(([t, m]) => {
                      const Icon = m.icon;
                      return (
                        <button key={t} disabled={!!busy} onClick={() => trigger(d.device_id, t)}
                          className={`flex items-center justify-center gap-2 rounded-xl bg-gradient-to-br ${m.tone} px-3 py-2.5 text-sm font-bold text-white shadow transition hover:-translate-y-0.5 disabled:opacity-60`}>
                          {busy === d.device_id + t ? <Loader2 className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}{m.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </article>
          );
        })}
        {devices.length === 0 && <p className="text-muted">No sensor units registered yet. Run the seed command to add the demo units.</p>}
      </div>
    </div>
  );
}
