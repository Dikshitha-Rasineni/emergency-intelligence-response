import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Crosshair, Loader2, MapPin, Send } from "lucide-react";
import { api, ApiError, uploadWithProgress } from "../lib/api";
import { saveReport } from "../lib/store";
import { PhotoPicker, type Picked } from "../components/PhotoPicker";
import { VoiceInput } from "../components/VoiceInput";
import { MapView } from "../components/MapView";
import { ErrorBox } from "../components/States";

const CATS = ["road_accident", "fire", "gas_leak", "flood", "medical", "rescue", "sos", "other"];
type Loc = { lat: number; lng: number; source: "DEVICE_GPS" | "MANUAL_PIN"; accuracy?: number } | null;

function Step({ n, title, children, hint }: { n: number; title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="panel p-5 sm:p-7">
      <div className="mb-4 flex items-start gap-3">
        <span className="step-num">{n}</span>
        <div><h2 className="text-lg font-black">{title}</h2>{hint && <p className="mt-0.5 text-sm text-muted">{hint}</p>}</div>
      </div>
      {children}
    </section>
  );
}

export default function Report() {
  const { t, i18n } = useTranslation();
  const nav = useNavigate();
  const initial = (useLocation().state as { text?: string } | null)?.text || "";
  const [text, setText] = useState(initial);
  const [photos, setPhotos] = useState<Picked[]>([]);
  const [loc, setLoc] = useState<Loc>(null);
  const [locMsg, setLocMsg] = useState<string>("");
  const [locating, setLocating] = useState(false);
  const [landmark, setLandmark] = useState("");
  const [landmarkTyped, setLandmarkTyped] = useState(false);
  const [addr, setAddr] = useState<"idle" | "looking" | "found" | "failed">("idle");
  const [category, setCategory] = useState("");
  const [injuries, setInjuries] = useState("");
  const [meta, setMeta] = useState({ max_image_mb: 8, max_images: 6, speech_server_available: false });
  const [phase, setPhase] = useState<"form" | "sending" | "uploading">("form");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [touched, setTouched] = useState(false);

  useEffect(() => { api("/meta").then(setMeta).catch(() => undefined); locate(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // When the location changes (GPS or a tap on the map), look up the nearest address and
  // fill the landmark field, unless the person has typed their own landmark.
  useEffect(() => {
    if (!loc || landmarkTyped) return;
    let live = true;
    setAddr("looking");
    const t = setTimeout(() => {
      api<{ label: string }>(`/maps/reverse?latitude=${loc.lat.toFixed(6)}&longitude=${loc.lng.toFixed(6)}`)
        .then((r) => { if (live && r.label) { setLandmark(r.label.slice(0, 255)); setAddr("found"); } })
        .catch(() => live && setAddr("failed"));
    }, 400);
    return () => { live = false; clearTimeout(t); };
  }, [loc?.lat, loc?.lng]); // eslint-disable-line react-hooks/exhaustive-deps

  function locate() {
    if (!navigator.geolocation) { setLocMsg(t("report.locationUnavailable")); return; }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (p) => { setLoc({ lat: p.coords.latitude, lng: p.coords.longitude, source: "DEVICE_GPS", accuracy: Math.round(p.coords.accuracy) });
               setLocMsg(t("report.locationFound", { m: Math.round(p.coords.accuracy) })); setLocating(false); },
      (e) => { setLocMsg(e.code === 1 ? t("report.locationDenied") : t("report.locationUnavailable")); setLocating(false); },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 30000 },
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (text.trim().length < 3) return;
    if (!navigator.onLine) { setError(t("report.offline")); return; }
    setError("");
    setPhase("sending");
    try {
      const r = await api<{ incident_id: string; tracking_token: string }>("/incidents", {
        method: "POST",
        json: {
          description: text.trim(), latitude: loc?.lat, longitude: loc?.lng, location_source: loc?.source,
          location_accuracy_m: loc?.accuracy, location: landmark || undefined, emergency_type: category || undefined,
          injuries: injuries ? Number(injuries) : 0, preferred_language: i18n.language,
        },
      });
      saveReport({ id: r.incident_id, token: r.tracking_token, at: new Date().toISOString() });
      let uploadErrors: string[] = [];
      if (photos.length) {
        setPhase("uploading");
        const fd = new FormData();
        photos.forEach((p) => fd.append("files", p.file, p.file.name));
        try {
          const res = await uploadWithProgress(`/incidents/${r.incident_id}/media`, fd, r.tracking_token, setProgress);
          uploadErrors = (res?.results || []).filter((x: any) => !x.accepted).map((x: any) => t("report.uploadFailed", { name: x.filename, reason: x.error }));
        } catch (err) {
          uploadErrors = [t("report.uploadFailed", { name: "", reason: (err as Error).message })];
        }
      }
      nav(`/track/${r.incident_id}`, { state: { justSent: true, uploadErrors } });
    } catch (err) {
      setPhase("form");
      setError(t("report.submitFailed", { reason: err instanceof ApiError ? err.message : String(err) }));
    }
  }

  const busy = phase !== "form";
  return (
    <div>
      <div className="dark-band relative overflow-hidden text-white">
        <div className="speed-lines absolute inset-0" />
        <div className="relative mx-auto flex max-w-3xl flex-wrap items-end justify-between gap-4 px-4 pb-24 pt-10 sm:px-6">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-bold"><span className="h-2 w-2 animate-blink rounded-full bg-sos-glow" />RESQ.AI</span>
            <h1 className="mt-3 text-4xl font-black">{t("report.title")}</h1>
          </div>
          <a href="tel:112" className="btn-ghost-dark">{t("hero.call")}</a>
        </div>
      </div>

      <form onSubmit={submit} className="relative mx-auto -mt-16 max-w-3xl space-y-5 px-4 pb-10 sm:px-6" noValidate>
        <Step n={1} title={t("report.describe")} hint={t("report.describeHint")}>
          <textarea id="desc" rows={5} value={text} onChange={(e) => setText(e.target.value)} aria-label={t("report.describe")}
            placeholder={t("report.placeholder")} className="field text-base" aria-invalid={touched && text.trim().length < 3} />
          {touched && text.trim().length < 3 && <p className="mt-1 text-sm font-semibold text-sos" role="alert">{t("report.needText")}</p>}
          <div className="mt-3"><VoiceInput onText={setText} serverAvailable={meta.speech_server_available} /></div>
        </Step>

        <Step n={2} title={t("report.location")}>
          <div className="flex flex-wrap items-center gap-3">
            <button type="button" className="btn-quiet" onClick={locate} disabled={locating}>
              {locating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Crosshair className="h-4 w-4 text-teal-mid" />}
              {locating ? t("report.locationDetecting") : t("report.locationDetect")}
            </button>
            <span className={`text-sm font-semibold ${loc ? "text-pri-low" : "text-muted"}`} aria-live="polite">{loc?.source === "MANUAL_PIN" ? t("report.locationPinned") : locMsg}</span>
          </div>
          <div className="mt-4">
            <MapView height={260} markers={loc ? [{ lat: loc.lat, lng: loc.lng, kind: "you", label: t("report.location") }] : []}
              onPick={(lat, lng) => setLoc({ lat, lng, source: "MANUAL_PIN" })} />
            <p className="mt-2 flex items-center gap-1.5 text-xs text-muted"><MapPin className="h-3.5 w-3.5" />{t("report.locationMapHint")}</p>
          </div>
          <label htmlFor="landmark" className="label mt-4">{t("report.locationText")}</label>
          <input id="landmark" className="field" value={landmark} onChange={(e) => { setLandmark(e.target.value); setLandmarkTyped(e.target.value.trim() !== ""); setAddr("idle"); }}
            placeholder={addr === "looking" ? t("report.addressLooking") : t("report.locationTextPlaceholder")} maxLength={255} />
          {addr === "found" && <p className="mt-1.5 text-xs font-semibold text-pri-low" aria-live="polite">{t("report.addressFound")}</p>}
          {addr === "looking" && <p className="mt-1.5 flex items-center gap-1.5 text-xs text-muted" aria-live="polite"><Loader2 className="h-3 w-3 animate-spin" />{t("report.addressLooking")}</p>}
        </Step>

        <Step n={3} title={t("report.photos")}>
          <PhotoPicker value={photos} onChange={setPhotos} maxMb={meta.max_image_mb} max={meta.max_images} />
        </Step>

        <Step n={4} title={t("report.categoryOptional")} hint={t("report.categoryHint")}>
          <div className="flex flex-wrap gap-2">
            {CATS.map((c) => (
              <button type="button" key={c} onClick={() => setCategory(category === c ? "" : c)} aria-pressed={category === c}
                className={`rounded-full border px-4 py-2 text-sm font-bold transition ${category === c ? "border-transparent bg-teal-mid text-white shadow-glowteal" : "border-line bg-white hover:-translate-y-0.5 hover:border-teal-mid"}`}>
                {t(`categories.${c}`)}
              </button>
            ))}
          </div>
          <label htmlFor="inj" className="label mt-5">{t("report.injuries")}</label>
          <input id="inj" type="number" min={0} max={500} inputMode="numeric" className="field w-32" value={injuries} onChange={(e) => setInjuries(e.target.value)} />
        </Step>

        {error && <ErrorBox>{error}</ErrorBox>}
        <div className="sticky bottom-0 z-[1000] -mx-4 border-t border-white/60 bg-paper/90 px-4 py-4 backdrop-blur sm:static sm:mx-0 sm:border-0 sm:bg-transparent sm:p-0">
          <button type="submit" className="btn-sos w-full py-4 text-lg" disabled={busy}>
            {busy ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            {phase === "sending" ? t("report.submitting") : phase === "uploading" ? `${t("report.uploading")} ${Math.round(progress * 100)}%` : t("report.submit")}
          </button>
          <p className="mt-3 text-center text-xs text-muted">{t("report.privacy")}</p>
        </div>
      </form>
    </div>
  );
}
