"use client";

import { useState } from "react";

type Props = {
  source: "env" | "panel" | "none";
  keyUpdatedAt: string | null;
  lastBatch: string | null;
  lastBatchFresh: boolean;
  endpoint: string;
};

export function IngestKeyPanel({ source, keyUpdatedAt, lastBatch, lastBatchFresh, endpoint }: Props) {
  const [secret, setSecret] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const status =
    source === "none" ? { tone: "var(--neon-down)", text: "Sin clave: SQPC no puede publicar todavía." }
    : !lastBatch ? { tone: "var(--gold)", text: "Clave lista. Esperando el primer envío de SQPC." }
    : lastBatchFresh ? { tone: "var(--neon-up)", text: `Conectado. Último envío ${lastBatch}.` }
    : { tone: "var(--neon-down)", text: `Conectado, pero sin envíos recientes (último ${lastBatch}).` };

  async function generate() {
    if (source === "panel" && !confirm("La clave actual dejará de funcionar y tendrás que actualizar el .env de SQPC. ¿Continuar?")) return;
    setBusy(true); setErr(null);
    try {
      const r = await fetch("/api/admin/ingest-key", { method: "POST" });
      const d = await r.json();
      if (!r.ok || !d.ok) throw new Error(d.error === "managed_in_cloudflare" ? "La clave está definida como secreto en Cloudflare; cámbiala allí." : "No se pudo generar la clave.");
      setSecret(d.secret);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const envText = secret ? `GG_INGEST_URL=${endpoint}\nGG_INGEST_SECRET=${secret}\n` : "";

  return (
    <section className="card p-5 sm:p-6 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Conexión con SQPC</h2>
          <p className="mt-1 text-sm" style={{ color: status.tone }}>● {status.text}</p>
          <p className="mt-1 text-xs text-lo break-all">Endpoint: <span className="num">{endpoint}</span></p>
          {source === "panel" && keyUpdatedAt && <p className="text-xs text-lo">Clave generada {keyUpdatedAt}</p>}
          {source === "env" && <p className="text-xs text-lo">La clave está configurada como secreto en Cloudflare (INGEST_HMAC_SECRET).</p>}
        </div>
        {source !== "env" && (
          <button onClick={generate} disabled={busy}
            className="rounded-lg bg-[var(--gold)] px-4 py-2 text-sm font-semibold text-black disabled:opacity-60">
            {busy ? "Generando…" : source === "none" ? "Generar clave" : "Cambiar clave"}
          </button>
        )}
      </div>
      {err && <p className="text-sm" style={{ color: "var(--neon-down)" }}>{err}</p>}
      {secret && (
        <div className="space-y-3">
          <p className="text-sm text-mid">
            Guarda esto en un archivo <span className="num">.env</span> junto a <span className="num">goldglitch_publish.py</span> en la carpeta de SQPC.
            Se muestra <b>una sola vez</b>.
          </p>
          <pre className="num text-xs whitespace-pre-wrap break-all rounded-lg border border-line bg-black/40 p-3">{envText}</pre>
          <button className="text-sm text-gold hover:underline underline-offset-4"
            onClick={() => navigator.clipboard.writeText(envText).then(() => setCopied(true))}>
            {copied ? "Copiado ✓" : "Copiar .env"}
          </button>
          <p className="text-xs text-lo">Prueba la conexión: <span className="num">python goldglitch_publish.py --ping</span></p>
        </div>
      )}
    </section>
  );
}
