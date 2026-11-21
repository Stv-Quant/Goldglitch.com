"use client";

import { useEffect, useRef, useState } from "react";

type Cell = { gx: number; gy: number; n: number };
type Data = { cells: Cell[]; scroll: { depth: number; n: number }[]; targets: { target: string; n: number }[] };
const WIDTH = { mobile: 390, tablet: 820, desktop: 1280 } as const;

/** The real page in an iframe with the click heatmap painted on top, plus scroll reach and the most clicked elements. */
export function Heatmap({ paths }: { paths: string[] }) {
  const [path, setPath] = useState(paths[0] ?? "/");
  const [device, setDevice] = useState<keyof typeof WIDTH>("mobile");
  const [days, setDays] = useState(30);
  const [data, setData] = useState<Data | null>(null);
  const [height, setHeight] = useState(2400);
  const canvas = useRef<HTMLCanvasElement>(null);
  const frame = useRef<HTMLIFrameElement>(null);
  const w = WIDTH[device];

  useEffect(() => {
    setData(null);
    fetch(`/api/admin/heatmap?path=${encodeURIComponent(path)}&device=${device}&days=${days}`)
      .then((r) => r.json()).then(setData).catch(() => setData({ cells: [], scroll: [], targets: [] }));
  }, [path, device, days]);

  useEffect(() => {
    const c = canvas.current;
    if (!c || !data) return;
    c.width = w; c.height = height;
    const g = c.getContext("2d")!;
    g.clearRect(0, 0, w, height);
    const max = Math.max(1, ...data.cells.map((x) => Number(x.n)));
    // intensity layer
    for (const cell of data.cells) {
      const x = (Number(cell.gx) + 0.5) * (w / 50), y = Number(cell.gy) * 40 + 20, a = Math.min(1, Number(cell.n) / max);
      const rad = g.createRadialGradient(x, y, 0, x, y, 34);
      rad.addColorStop(0, `rgba(0,0,0,${0.25 + a * 0.75})`); rad.addColorStop(1, "rgba(0,0,0,0)");
      g.fillStyle = rad; g.beginPath(); g.arc(x, y, 34, 0, 7); g.fill();
    }
    // colorize alpha → blue/green/yellow/red
    const img = g.getImageData(0, 0, w, height), d = img.data;
    for (let i = 0; i < d.length; i += 4) {
      const v = d[i + 3] / 255;
      if (!v) continue;
      const [r, gg, b] = v < 0.33 ? [0, 120 + v * 400, 255] : v < 0.66 ? [(v - 0.33) * 770, 255, 255 - (v - 0.33) * 770] : [255, 255 - (v - 0.66) * 750, 0];
      d[i] = r; d[i + 1] = gg; d[i + 2] = b; d[i + 3] = Math.min(200, v * 260);
    }
    g.putImageData(img, 0, 0);
  }, [data, w, height]);

  const onLoad = () => {
    try {
      const doc = frame.current?.contentDocument;
      if (doc) setHeight(Math.min(Math.max(doc.documentElement.scrollHeight, 800), 20000));
    } catch {
      /* same origin; ignore */
    }
  };
  const totalScroll = (data?.scroll ?? []).reduce((a, s) => a + Number(s.n), 0);
  const reach = (band: number) => totalScroll
    ? Math.round(((data?.scroll ?? []).filter((s) => Number(s.depth) >= band).reduce((a, s) => a + Number(s.n), 0) / totalScroll) * 100) : 0;
  const clicks = (data?.cells ?? []).reduce((a, c) => a + Number(c.n), 0);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 items-center text-sm">
        <select value={path} onChange={(e) => setPath(e.target.value)} className="rounded-lg border border-line bg-[var(--bg-2)] px-3 py-2">
          {[...new Set([...(paths.length ? paths : []), "/", "/planes", "/historial"])].map((p) => <option key={p}>{p}</option>)}
        </select>
        {(Object.keys(WIDTH) as (keyof typeof WIDTH)[]).map((d) => (
          <button key={d} onClick={() => setDevice(d)} className={`rounded-lg px-3 py-2 border ${device === d ? "border-[var(--gold)] text-hi" : "border-line text-lo"}`}>
            {d === "mobile" ? "Celular" : d === "tablet" ? "Tablet" : "Computador"}
          </button>
        ))}
        <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="rounded-lg border border-line bg-[var(--bg-2)] px-3 py-2">
          {[1, 7, 30, 90].map((d) => <option key={d} value={d}>{d === 1 ? "Hoy" : `${d} días`}</option>)}
        </select>
        <span className="text-lo num text-xs">{clicks.toLocaleString("es-CO")} clics · {totalScroll.toLocaleString("es-CO")} vistas medidas</span>
      </div>
      <div className="grid gap-4 lg:grid-cols-[auto_minmax(0,1fr)]">
        <div className="overflow-auto rounded-xl border border-line bg-black max-h-[80vh]" style={{ maxWidth: "100%" }}>
          <div className="relative" style={{ width: w, height }}>
            <iframe ref={frame} src={`${path}?gg_nt=1`} onLoad={onLoad} title="Página" scrolling="no"
              className="absolute inset-0 border-0 pointer-events-none" style={{ width: w, height }} />
            <canvas ref={canvas} className="absolute inset-0 pointer-events-none" style={{ width: w, height }} />
            {[25, 50, 75].map((p) => (
              <div key={p} className="absolute left-0 right-0 border-t border-dashed border-[var(--gold)] pointer-events-none"
                style={{ top: (height * p) / 100 }}>
                <span className="num text-[10px] bg-black/80 text-gold px-1">{reach(p / 10)}% llega al {p}%</span>
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-4 min-w-0">
          <div className="card p-4">
            <h3 className="text-sm font-semibold">Hasta dónde bajan</h3>
            {[10, 25, 50, 75, 90].map((p) => (
              <div key={p} className="mt-2 flex items-center gap-2 text-xs">
                <span className="w-10 num text-lo">{p}%</span>
                <div className="h-2 flex-1 rounded bg-[var(--bg-2)]"><div className="h-2 rounded bg-[var(--gold)]" style={{ width: `${reach(Math.floor(p / 10))}%` }} /></div>
                <span className="w-10 num text-right">{reach(Math.floor(p / 10))}%</span>
              </div>
            ))}
          </div>
          <div className="card p-4">
            <h3 className="text-sm font-semibold">Lo más clicado en esta página</h3>
            <ol className="mt-2 space-y-1 text-xs">
              {(data?.targets ?? []).map((t) => (
                <li key={t.target} className="flex justify-between gap-3"><span className="truncate text-mid">{t.target}</span><span className="num">{t.n}</span></li>
              ))}
              {data && !data.targets.length && <li className="text-lo">Todavía no hay clics medidos.</li>}
            </ol>
          </div>
          <p className="text-[11px] text-lo leading-relaxed">Azul = pocos clics, rojo = muchos. La página se muestra en el ancho del dispositivo
            elegido; las posiciones son aproximadas (columnas de 2% y filas de 40 px). Solo páginas públicas; la app y el acceso no se graban.</p>
        </div>
      </div>
    </div>
  );
}
