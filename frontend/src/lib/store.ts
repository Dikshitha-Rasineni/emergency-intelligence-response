/** localStorage wrapper: per-device conveniences only (language, own report tokens, session). */
export const store = {
  get(key: string): string | null {
    try { return window.localStorage.getItem(key); } catch { return null; }
  },
  set(key: string, value: string) {
    try { window.localStorage.setItem(key, value); } catch { /* storage unavailable */ }
  },
  remove(key: string) {
    try { window.localStorage.removeItem(key); } catch { /* ignore */ }
  },
  getJSON<T>(key: string, fallback: T): T {
    const raw = store.get(key);
    if (!raw) return fallback;
    try { return JSON.parse(raw) as T; } catch { return fallback; }
  },
};

export type SavedReport = { id: string; token: string; at: string };
export function saveReport(r: SavedReport) {
  const list = store.getJSON<SavedReport[]>("resq.reports", []).filter((x) => x.id !== r.id);
  store.set("resq.reports", JSON.stringify([r, ...list].slice(0, 10)));
}
export function savedReports(): SavedReport[] {
  return store.getJSON<SavedReport[]>("resq.reports", []);
}
export function tokenFor(id: string): string | null {
  return savedReports().find((r) => r.id === id)?.token ?? null;
}
