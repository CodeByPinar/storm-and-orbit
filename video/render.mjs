// Tanıtım videosunu üretir: sunumu (three.js) başsız tarayıcıda açar, her kareyi simülasyon zamanına
// göre çizip görüntüsünü alır, müziği OfflineAudioContext ile sentezler ve ffmpeg ile MP4'e dönüştürür.
//
// Kurulum:  cd video && npm install        (ffmpeg PATH'te olmalı; Edge ya da Chrome gerekir)
// Çalıştır: node render.mjs                -> video/storm-and-orbit.mp4
//           node render.mjs --frames 0,6,12  (yalnızca belirli saniyelerden test kareleri)
import puppeteer from "puppeteer-core";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { existsSync, mkdirSync, readFileSync, writeFileSync, statSync } from "node:fs";
import { dirname, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { SCENES, DURATION, CUTS, FPS, W, H } from "./scenes.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SITE = resolve(HERE, "../deploy/site");
const OUT = resolve(HERE, "storm-and-orbit.mp4");
const TMP = resolve(HERE, ".tmp"); mkdirSync(TMP, { recursive: true });
const args = process.argv.slice(2);
const testAt = args.includes("--frames") ? args[args.indexOf("--frames") + 1].split(",").map(Number) : null;

// Yerel statik sunucu (deploy/site)
const TYPES = { ".html": "text/html; charset=utf-8", ".json": "application/json", ".js": "text/javascript" };
const server = createServer((req, res) => {
  const p = join(SITE, decodeURIComponent(new URL(req.url, "http://x").pathname).replace(/\/$/, "/index.html"));
  if (!p.startsWith(SITE) || !existsSync(p) || statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "Content-Type": TYPES[extname(p)] || "application/octet-stream" }); res.end(readFileSync(p));
}).listen(0, "127.0.0.1");
await new Promise((r) => server.once("listening", r));
const BASE = `http://127.0.0.1:${server.address().port}/`;

const BROWSERS = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Google/Chrome/Application/chrome.exe", "/usr/bin/google-chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"];
const browser = await puppeteer.launch({ executablePath: BROWSERS.find((p) => existsSync(p)), headless: "new",
  args: ["--use-angle=default", "--enable-gpu", "--ignore-gpu-blocklist", "--hide-scrollbars", "--mute-audio", `--window-size=${W},${H}`] });
const page = await browser.newPage();
await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
await page.evaluateOnNewDocument(() => { try { localStorage.setItem("fy-lang", "tr"); localStorage.setItem("fy-dur", "std"); } catch (e) {} });
await page.goto(`${BASE}?r=${Date.now()}#capture`, { waitUntil: "networkidle0", timeout: 120000 });
await page.waitForFunction(() => window.SIM && SIM.mapReady(), { timeout: 60000 });
await page.evaluate(() => document.fonts.ready);
await page.addScriptTag({ content: readFileSync(join(HERE, "overlay.js"), "utf8") });
await page.addScriptTag({ content: readFileSync(join(HERE, "music.js"), "utf8") });
await page.evaluate((S, D) => window.__installOverlay(S, D), SCENES, DURATION);

const sceneAt = (t) => SCENES.find((s) => t >= s.t0 && t < s.t1) || SCENES[SCENES.length - 1];
const smooth = (x) => x * x * (3 - 2 * x);
async function drawFrame(t) {
  const s = sceneAt(t), u = Math.min(1, (t - s.t0) / (s.t1 - s.t0));
  // Simülasyon zamanı sahne içinde hafifçe yumuşatılmış doğrusal ilerler
  const sim = s.sim[0] + (s.sim[1] - s.sim[0]) * (0.85 * u + 0.15 * smooth(u));
  await page.evaluate(async (sim, view, t) => {
    SIM.view(view); SIM.seek(sim); window.__overlay(t);
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  }, sim, s.view, t);
  return page.screenshot({ type: "jpeg", quality: 94, optimizeForSpeed: true });
}

if (testAt) {
  for (const t of testAt) { writeFileSync(join(TMP, `test-${String(t).replace(".", "_")}.jpg`), await drawFrame(t)); console.log("test karesi", t); }
} else {
  // Müzik
  console.log("müzik sentezleniyor…");
  const { b64, peak } = await page.evaluate((C, D) => window.__renderMusic(C, D), CUTS, DURATION);
  const wav = join(TMP, "music.wav"); writeFileSync(wav, Buffer.from(b64, "base64"));
  console.log(`  müzik hazır (tepe ${peak.toFixed(2)})`);
  // Kareler doğrudan ffmpeg'e akar (diske ara dosya yazılmaz)
  const N = Math.round(DURATION * FPS);
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-", "-i", wav,
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart", "-shortest", OUT], { stdio: ["pipe", "inherit", "inherit"] });
  const t0 = Date.now();
  for (let f = 0; f < N; f++) {
    const buf = await drawFrame(f / FPS);
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    if (f % 60 === 0) { const el = (Date.now() - t0) / 1000; console.log(`  kare ${f}/${N} · ${el.toFixed(0)} sn · kalan ~${(el / Math.max(1, f) * (N - f)).toFixed(0)} sn`); }
  }
  ff.stdin.end();
  await new Promise((r, j) => ff.on("close", (c) => (c === 0 ? r() : j(new Error("ffmpeg " + c)))));
  // Kapak görseli
  writeFileSync(join(HERE, "poster.jpg"), await drawFrame(SCENES[2].t0 + 2.6));
  console.log("bitti:", OUT);
}
await browser.close();
server.close();
