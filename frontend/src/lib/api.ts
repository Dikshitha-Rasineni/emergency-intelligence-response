import { store } from "./store";

export const API = "/api/v1";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

function authHeader(): Record<string, string> {
  const t = store.get("resq.session.token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function api<T = any>(path: string, opts: RequestInit & { json?: unknown; token?: string | null } = {}): Promise<T> {
  const headers: Record<string, string> = { ...authHeader(), ...(opts.headers as Record<string, string>) };
  if (opts.token) headers["X-Tracking-Token"] = opts.token;
  let body = opts.body;
  if (opts.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.json);
  }
  let res: Response;
  try {
    res = await fetch(API + path, { ...opts, headers, body });
  } catch {
    throw new ApiError(0, "NETWORK", navigator.onLine ? "the server could not be reached" : "no internet connection");
  }
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const d = data?.detail;
    const msg = typeof d === "string" ? d : d?.message || d?.error || `HTTP ${res.status}`;
    if (res.status === 401 && store.get("resq.session.token") && !path.startsWith("/auth/login")) {
      store.remove("resq.session.token");
      window.dispatchEvent(new Event("resq:logout"));
    }
    throw new ApiError(res.status, d?.error || String(res.status), msg);
  }
  return data as T;
}

/** Upload with progress (fetch has no upload progress). */
export function uploadWithProgress(path: string, form: FormData, token: string | null, onProgress: (p: number) => void): Promise<any> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", API + path);
    if (token) xhr.setRequestHeader("X-Tracking-Token", token);
    const a = authHeader().Authorization;
    if (a) xhr.setRequestHeader("Authorization", a);
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(e.loaded / e.total);
    xhr.onload = () => {
      let data: any = null;
      try { data = JSON.parse(xhr.responseText); } catch { /* ignore */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(data);
      else reject(new ApiError(xhr.status, data?.detail?.error || "UPLOAD", data?.detail?.message || `HTTP ${xhr.status}`));
    };
    xhr.onerror = () => reject(new ApiError(0, "NETWORK", "the server could not be reached"));
    xhr.send(form);
  });
}

/** WebSockets can't go through Vercel's /api rewrite, so in production they connect straight to the backend
 *  (VITE_BACKEND_URL, e.g. https://resq-ai-api.onrender.com). Locally this falls back to the current host. */
const BACKEND = (import.meta.env.VITE_BACKEND_URL as string | undefined)?.replace(/\/$/, "");

export function wsUrl(path: string, token: string) {
  const base = BACKEND
    ? BACKEND.replace(/^http/, "ws")
    : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
  return `${base}${API}${path}?token=${encodeURIComponent(token)}`;
}
