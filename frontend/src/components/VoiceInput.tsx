import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Mic, Square } from "lucide-react";
import { LANGUAGES } from "../lib/i18n";
import { API } from "../lib/api";

/**
 * Voice reporting. Uses the browser's speech recognition when it exists for the chosen
 * language; otherwise records audio and sends it to the server transcriber (if configured).
 * The transcript is placed in the text box so the citizen can check and edit it.
 */
export function VoiceInput({ onText, serverAvailable }: { onText: (text: string) => void; serverAvailable: boolean }) {
  const { t, i18n } = useTranslation();
  const [lang, setLang] = useState<string>(i18n.language);
  useEffect(() => setLang(i18n.language), [i18n.language]);
  const [state, setState] = useState<"idle" | "listening" | "transcribing" | "done" | "error" | "unsupported">("idle");
  const recRef = useRef<any>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

  async function startServer() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      mr.ondataavailable = (e) => chunks.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach((tr) => tr.stop());
        setState("transcribing");
        const fd = new FormData();
        fd.append("audio", new Blob(chunks, { type: mr.mimeType || "audio/webm" }), "report.webm");
        fd.append("language", lang);
        try {
          const r = await fetch(`${API}/speech/transcribe`, { method: "POST", body: fd });
          if (!r.ok) throw new Error();
          const d = await r.json();
          onText(d.text);
          setState("done");
        } catch { setState("error"); }
      };
      mediaRef.current = mr;
      mr.start();
      setState("listening");
    } catch { setState("error"); }
  }

  function start() {
    if (SR) {
      const rec = new SR();
      rec.lang = LANGUAGES.find((l) => l.code === lang)?.speech || "en-IN";
      rec.interimResults = true;
      rec.continuous = true;
      let finalText = "";
      rec.onresult = (e: any) => {
        let interim = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) finalText += e.results[i][0].transcript + " ";
          else interim += e.results[i][0].transcript;
        }
        onText((finalText + interim).trim());
      };
      rec.onerror = (e: any) => {
        if ((e.error === "language-not-supported" || e.error === "network") && serverAvailable) { startServer(); return; }
        setState(e.error === "no-speech" ? "idle" : "error");
      };
      rec.onend = () => setState((s) => (s === "listening" ? "done" : s));
      recRef.current = rec;
      rec.start();
      setState("listening");
    } else if (serverAvailable && (window as any).MediaRecorder) {
      startServer();
    } else {
      setState("unsupported");
    }
  }
  function stop() {
    recRef.current?.stop();
    if (mediaRef.current?.state === "recording") mediaRef.current.stop();
  }

  const listening = state === "listening";
  return (
    <div className="flex flex-wrap items-center gap-2">
      {listening ? (
        <button type="button" onClick={stop} className="btn-sos"><Square className="h-4 w-4" aria-hidden />{t("report.voiceStop")}</button>
      ) : (
        <button type="button" onClick={start} className="btn-quiet" disabled={state === "transcribing"}><Mic className="h-4 w-4" aria-hidden />{t("report.voiceStart")}</button>
      )}
      <label className="text-sm text-muted">
        <span className="sr-only">{t("report.voiceLang")}</span>
        <select value={lang} onChange={(e) => setLang(e.target.value)} disabled={listening}
          className="rounded border border-line bg-surface px-2 py-2 text-sm text-ink">
          {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
        </select>
      </label>
      <p className="w-full text-sm" aria-live="polite">
        {listening && <span className="text-teal">{t("report.voiceListening")}</span>}
        {state === "transcribing" && <span className="text-muted">…</span>}
        {state === "done" && <span className="text-muted">{t("report.voiceReview")}</span>}
        {state === "error" && <span className="text-sos">{t("report.voiceFailed")}</span>}
        {state === "unsupported" && <span className="text-sos">{t("report.voiceUnsupported")}</span>}
      </p>
    </div>
  );
}
