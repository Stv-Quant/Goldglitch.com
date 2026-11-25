"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Prob } from "@/components/stats/Prob";
import { probColor } from "@/lib/probScale";
import { scoreSlip, type Leg, type LegStatus, type SlipScore } from "@/lib/slip";
import { useSlipDraft } from "./slipDraft";

type Saved = { id: string; name: string | null; createdAt: number; legs: (Leg & { status: LegStatus })[]; status: LegStatus; score: SlipScore };

const fmt = new Intl.DateTimeFormat("es-CO", { timeZone: "America/Bogota", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false });
const STATUS: Record<LegStatus, { label: string; color: string }> = {
  pending: { label: "Pendiente", color: "var(--text-lo)" },
  won: { label: "Acertada", color: "var(--neon-up)" },
  lost: { label: "Fallada", color: "var(--neon-down)" },
  void: { label: "Nula", color: "var(--text-mid)" },
};
const GRADE_COLOR: Record<string, string> = { A: "var(--p6)", B: "var(--p5)", C: "var(--p4)", D: "var(--p3)", E: "var(--p2)" };

export function SlipsPage() {
  const draft = useSlipDraft();
  const [saved, setSaved] = useState<Saved[] | null>(null);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(() => {
    fetch("/api/app/slips", { cache: "no-store" }).then((r) => (r.ok ? r.json() : { slips: [] })).then((d) => setSaved(d.slips ?? []));
  }, []);
  useEffect(load, [load]);

  async function save() {
    setBusy(true); setMsg(null);
    const r = await fetch("/api/app/slips", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ name, legs: draft.legs.map((l) => ({ matchId: l.matchId, label: l.label })) }),
    }).catch(() => null);
    const j = await r?.json().catch(() => null);
    setBusy(false);
    if (!j?.ok) return setMsg({ ok: false, text: j?.error ?? "No se pudo guardar." });
    draft.clear(); setName(""); setMsg({ ok: true, text: "Combinada guardada." }); load();
  }

  async function remove(id: string) {
    await fetch(`/api/app/slips/${id}`, { method: "DELETE" }).catch(() => null);
    load();
  }

  const s = draft.legs.length ? scoreSlip(draft.legs) : null;
  const active = saved?.filter((x) => x.status === "pending") ?? [];
  const done = saved?.filter((x) => x.status !== "pending") ?? [];
  const won = done.filter((x) => x.status === "won").length;
  const settled = done.filter((x) => x.status !== "void").length;

  return (
    <div className="space-y-8">
      <div>
        <p className="eyebrow">Pro</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight">Combinadas</h1>
        <p className="mt-2 max-w-2xl text-sm text-mid">
          Junta picks de 80% o más con <span className="text-hi">+ Combinada</span> en cada partido. Calculamos la probabilidad de que salgan todas,
          el riesgo y una nota, y cuando terminan los partidos te mostramos cómo quedó cada selección.
        </p>
      </div>

      <section className="glass p-5 sm:p-6" aria-labelledby="h-draft">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="h-draft" className="text-lg font-semibold">Combinada en preparación</h2>
          {draft.legs.length > 0 && <button type="button" onClick={draft.clear} className="text-xs text-lo hover:text-hi">Vaciar</button>}
        </div>
        {!draft.legs.length ? (
          <p className="mt-3 text-sm text-lo">Todavía no agregaste selecciones. Abre un partido en <Link href="/app" className="text-gold">Partidos</Link> y toca “+ Combinada” en los picks.</p>
        ) : (
          <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_320px]">
            <ul className="divide-y divide-[var(--border-soft)]">
              {draft.legs.map((l, i) => (
                <li key={`${l.matchId}-${l.label}`} className="flex items-start gap-3 py-3">
                  <Prob p={l.p} className="w-12 shrink-0 text-right text-base font-semibold" />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-hi">{l.label}{s && s.weakest === i && draft.legs.length > 1 && <span className="ml-2 rounded px-1.5 py-px text-[9px] uppercase tracking-[0.12em]" style={{ background: "var(--gold-faint)", color: "var(--gold)" }}>La más débil</span>}</div>
                    <div className="text-[11px] text-lo">{l.home} vs {l.away} · {l.competition} · {fmt.format(l.kickoffAt)}</div>
                  </div>
                  <button type="button" onClick={() => draft.remove(l)} aria-label={`Quitar ${l.label}`} className="text-lo hover:text-hi">✕</button>
                </li>
              ))}
            </ul>
            {s && <ScoreCard s={s} n={draft.legs.length} />}
          </div>
        )}
        {draft.legs.length > 0 && (
          <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-line pt-4">
            <input value={name} onChange={(e) => setName(e.target.value)} maxLength={60} placeholder="Nombre (opcional)"
              className="min-w-0 flex-1 rounded-[10px] border border-line bg-[var(--bg-raise)] px-3 py-2 text-sm text-hi outline-none focus:border-[var(--border-glass)]" />
            <button type="button" disabled={busy || draft.legs.length < 2} onClick={save} className="btn-gold px-4 py-2 text-sm disabled:opacity-50">
              {busy ? "Guardando…" : draft.legs.length < 2 ? "Agrega al menos 2" : "Guardar combinada"}
            </button>
          </div>
        )}
        {msg && <p role="status" className="mt-3 text-sm" style={{ color: msg.ok ? "var(--neon-up)" : "var(--neon-down)" }}>{msg.text}</p>}
      </section>

      {settled > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:max-w-md">
          <div className="card p-4"><div className="text-[11px] text-lo">Combinadas acertadas</div><div className="num text-2xl font-semibold text-gold">{won}/{settled}</div></div>
          <div className="card p-4"><div className="text-[11px] text-lo">Tasa de acierto</div><div className="num text-2xl font-semibold">{Math.round((won / settled) * 100)}%</div></div>
        </div>
      )}

      <SlipList title="En juego" slips={active} empty={saved === null ? "Cargando…" : "No tienes combinadas pendientes."} onDelete={remove} />
      {done.length > 0 && <SlipList title="Terminadas" slips={done} onDelete={remove} />}
    </div>
  );
}

function ScoreCard({ s, n }: { s: SlipScore; n: number }) {
  if (n < 2) return <div className="card p-4 text-sm text-lo">Agrega otra selección para calcular la combinada.</div>;
  return (
    <div className="card space-y-4 p-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-[11px] text-lo">Probabilidad de que salgan todas</div>
          <Prob p={s.p} digits={1} className="text-4xl font-semibold" />
          <div className="num text-[11px] text-lo">rango {(s.range[0] * 100).toFixed(1)}–{(s.range[1] * 100).toFixed(1)}%</div>
        </div>
        <div className="text-center">
          <div className="text-[11px] text-lo">Nota</div>
          <div className="num text-4xl font-semibold" style={{ color: GRADE_COLOR[s.grade] }}>{s.grade}</div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div><div className="text-[11px] text-lo">Riesgo</div><div className="text-hi">{s.riskLabel} <span className="num text-lo">· {Math.round(s.risk)}</span></div></div>
        <div><div className="text-[11px] text-lo">Aciertos esperados</div><div className="num text-hi">{s.expectedHits.toFixed(1)} de {n}</div></div>
      </div>
      <div>
        <div className="mb-1.5 text-[11px] text-lo">Cuántas selecciones salen</div>
        <div className="flex h-16 items-end gap-1">
          {s.hits.map((v, k) => (
            <div key={k} className="flex flex-1 flex-col items-center gap-1">
              <div className="w-full rounded-t" style={{ height: `${Math.max(2, v * 56 / Math.max(...s.hits))}px`, background: k === n ? probColor(s.p) : "var(--seg-2)" }} />
              <span className="num text-[10px] text-lo">{k}</span>
            </div>
          ))}
        </div>
      </div>
      {s.sameMatch && (
        <p className="text-[11px] text-lo">Hay selecciones del mismo partido: se calculan como independientes, pero en realidad están relacionadas, así que la probabilidad real puede ser algo mayor o menor.</p>
      )}
    </div>
  );
}

function SlipList({ title, slips, empty, onDelete }: { title: string; slips: Saved[]; empty?: string; onDelete: (id: string) => void }) {
  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold">{title} <span className="num text-sm font-normal text-lo">{slips.length || ""}</span></h2>
      {!slips.length ? <div className="card p-5 text-sm text-lo">{empty}</div> : (
        <ul className="grid gap-3 lg:grid-cols-2">
          {slips.map((x) => (
            <li key={x.id} className="card p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-hi">{x.name ?? `${x.legs.length} selecciones`}</div>
                  <div className="text-[11px] text-lo">Guardada {fmt.format(x.createdAt)}</div>
                </div>
                <div className="text-right">
                  <Prob p={x.score.p} digits={1} className="text-xl font-semibold" />
                  <div className="text-[11px]" style={{ color: STATUS[x.status].color }}>{STATUS[x.status].label} · nota {x.score.grade}</div>
                </div>
              </div>
              <ul className="mt-3 space-y-1.5 border-t border-line pt-3">
                {x.legs.map((l) => (
                  <li key={`${l.matchId}-${l.label}`} className="flex items-start gap-2 text-sm">
                    <span aria-hidden className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ background: STATUS[l.status].color }} />
                    <span className="min-w-0 flex-1">
                      <span className="text-mid">{l.label}</span>
                      <span className="block text-[11px] text-lo">{l.home} vs {l.away} · {STATUS[l.status].label}</span>
                    </span>
                    <span className="num text-[12px] text-lo">{Math.round(l.p * 100)}%</span>
                  </li>
                ))}
              </ul>
              <div className="mt-3 text-right">
                <button type="button" onClick={() => onDelete(x.id)} className="text-[11px] text-lo hover:text-[var(--neon-down)]">Borrar</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
