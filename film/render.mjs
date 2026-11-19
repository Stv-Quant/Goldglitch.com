// node render.mjs <w> <h> <fps> <seconds> <outdir> [fromFrame] [toFrame] [step]
import puppeteer from "puppeteer-core";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
const [w, h, fps, secs, out, from = 0, to, step = 1] = process.argv.slice(2);
const total = Math.round(fps * secs);
fs.mkdirSync(out, { recursive: true });
const root = path.resolve(".");
const srv = http.createServer((q, s) => { const f = path.join(root, q.url.split("?")[0] === "/" ? "index.html" : q.url.split("?")[0]); fs.readFile(f, (e, d) => { if (e) { s.statusCode = 404; s.end(); } else { s.setHeader("content-type", f.endsWith(".js") ? "text/javascript" : "text/html"); s.end(d); } }); }).listen(0);
const port = srv.address().port;
const b = await puppeteer.launch({ executablePath: "/usr/bin/google-chrome", args: ["--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const p = await b.newPage();
await p.setViewport({ width: +w, height: +h });
p.on("console", (m) => m.type() === "error" && console.log("console:", m.text()));
p.on("pageerror", (e) => console.log("pageerror:", e.message));
await p.goto(`http://localhost:${port}/?w=${w}&h=${h}`);
await p.waitForFunction("window.ready === true", { timeout: 120000 });
const end = to ? +to : total - 1;
const t0 = Date.now();
for (let i = +from; i <= end; i += +step) {
  const file = path.join(out, `f${String(i).padStart(5, "0")}.jpg`);
  if (fs.existsSync(file)) continue;
  const url = await p.evaluate((t) => window.grab(t), i / (total - 1));
  fs.writeFileSync(file, Buffer.from(url.split(",")[1], "base64"));
  if (i % 24 === 0) console.log(`frame ${i}/${end} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}
console.log("done", ((Date.now() - t0) / 1000).toFixed(1), "s");
await b.close(); srv.close();
