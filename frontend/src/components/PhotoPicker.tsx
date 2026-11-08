import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Camera, ImagePlus, X } from "lucide-react";

export type Picked = { id: string; file: File; url: string };
const TYPES = ["image/jpeg", "image/png", "image/webp"];

export function PhotoPicker({ value, onChange, maxMb, max }: { value: Picked[]; onChange: (p: Picked[]) => void; maxMb: number; max: number }) {
  const { t } = useTranslation();
  const [errors, setErrors] = useState<string[]>([]);
  const [drag, setDrag] = useState(false);
  const pickRef = useRef<HTMLInputElement>(null);
  const camRef = useRef<HTMLInputElement>(null);

  useEffect(() => () => value.forEach((p) => URL.revokeObjectURL(p.url)), []); // eslint-disable-line react-hooks/exhaustive-deps

  function add(files: FileList | File[]) {
    const errs: string[] = [];
    const next = [...value];
    for (const f of Array.from(files)) {
      if (!TYPES.includes(f.type)) { errs.push(t("report.photoType", { name: f.name })); continue; }
      if (f.size > maxMb * 1024 * 1024) { errs.push(t("report.photoTooLarge", { name: f.name, mb: maxMb })); continue; }
      if (next.length >= max) { errs.push(t("report.photoLimit", { max })); break; }
      next.push({ id: crypto.randomUUID(), file: f, url: URL.createObjectURL(f) });
    }
    setErrors(errs);
    onChange(next);
  }
  function remove(id: string) {
    const p = value.find((x) => x.id === id);
    if (p) URL.revokeObjectURL(p.url);
    onChange(value.filter((x) => x.id !== id));
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); add(e.dataTransfer.files); }}
        className={`rounded-panel border border-dashed p-4 ${drag ? "border-teal bg-teal-soft" : "border-line bg-surface"}`}
      >
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" className="btn-quiet" onClick={() => pickRef.current?.click()}><ImagePlus className="h-4 w-4" aria-hidden />{t("report.addPhotos")}</button>
          <button type="button" className="btn-quiet sm:hidden" onClick={() => camRef.current?.click()}><Camera className="h-4 w-4" aria-hidden />{t("report.takePhoto")}</button>
          <span className="hidden text-sm text-muted sm:inline">{t("report.dropHere")}</span>
        </div>
        <input ref={pickRef} type="file" accept={TYPES.join(",")} multiple hidden onChange={(e) => { e.target.files && add(e.target.files); e.target.value = ""; }} />
        <input ref={camRef} type="file" accept="image/*" capture="environment" hidden onChange={(e) => { e.target.files && add(e.target.files); e.target.value = ""; }} />
        {value.length > 0 && (
          <ul className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-6">
            {value.map((p) => (
              <li key={p.id} className="relative aspect-square overflow-hidden rounded border border-line">
                <img src={p.url} alt="" className="h-full w-full object-cover" />
                <button type="button" onClick={() => remove(p.id)} aria-label={t("report.removePhoto")}
                  className="absolute right-1 top-1 rounded-full bg-ink/80 p-1 text-white hover:bg-ink"><X className="h-3.5 w-3.5" /></button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p className="mt-1.5 text-xs text-muted">{t("report.photosHint", { mb: maxMb, max })}</p>
      {errors.map((e) => <p key={e} className="mt-1 text-sm text-sos" role="alert">{e}</p>)}
    </div>
  );
}
