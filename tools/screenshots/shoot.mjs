// Sunumdan ekran görüntüleri alır -> docs/screenshots/*.png
// Kurulum: cd tools/screenshots && npm install
// Çalıştır: node shoot.mjs [adres]   (varsayılan: canlı site)
import puppeteer from "puppeteer-core";
import { existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../docs/screenshots");
mkdirSync(OUT, { recursive: true });
const URL = process.argv[2] || "https://storm-and-orbit.up.railway.app/";
const BROWSERS = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Google/Chrome/Application/chrome.exe", "/usr/bin/google-chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"];
const executablePath = BROWSERS.find((p) => existsSync(p));
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await puppeteer.launch({ executablePath, headless: "new", args: ["--use-angle=default", "--enable-gpu", "--ignore-gpu-blocklist", "--hide-scrollbars", "--mute-audio"] });
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: 1 });

async function load(hash, lang) {
  await page.evaluateOnNewDocument((l) => { try { localStorage.setItem("fy-lang", l); } catch (e) {} }, lang);
  // Sorgu parametresi tam yeniden yüklemeyi zorlar (yalnızca # değişirse sayfa yenilenmez)
  await page.goto(`${URL}?r=${Date.now()}${hash}`, { waitUntil: "networkidle0", timeout: 90000 });
  await page.waitForFunction(() => window.SIM && window.SIM.mapReady && window.SIM.mapReady(), { timeout: 60000 });
}
async function seekShot(t, name, extra) {
  await page.evaluate((tt) => { SIM.seek(tt); }, t);
  await wait(400);
  if (extra) await page.evaluate(extra);
  await page.evaluate((tt) => { SIM.seek(tt); }, t);
  await wait(600);
  await page.screenshot({ path: `${OUT}/${name}.png` });
  console.log("  ", name);
}

// Açılış ekranı
await load("", "tr");
await page.waitForFunction(() => !document.querySelector("#bootSound").disabled, { timeout: 90000 });
await wait(500);
await page.screenshot({ path: `${OUT}/00-acilis.png` });
console.log("   00-acilis");

// Bölümler (yakalama modu: açılış atlanır, zaman elle verilir)
await load("#capture", "tr");
const shots = [[5, "01-giris"], [12 + 6, "02-gunes-dongusu"], [24 + 7.5, "03-firtina"], [36 + 7, "04-bir-hafta"], [48 + 10, "05-doz-yanit"], [60 + 7, "06-irtifa"], [72 + 7, "07-starlink"], [84 + 9, "08-sokum"], [96 + 10, "09-sonuc"]];
for (const [t, n] of shots) await seekShot(t, n);
// Ayrıntılar açık bir anlatı kartı
await seekShot(48 + 10, "10-ayrintilar", () => { const d = document.querySelector("#story details"); if (d) d.open = true; });
// Laboratuvar: Mayıs 2024 hazır ayarı
await page.evaluate(() => { SIM.seek(30); SIM.lab(true); document.querySelectorAll("#lab .presets button")[2].click(); });
await wait(800);
await page.screenshot({ path: `${OUT}/11-laboratuvar.png` });
console.log("   11-laboratuvar");
await page.evaluate(() => SIM.lab(false));
// Bilgi paneli: fırtına arşivi
await page.evaluate(() => { SIM.seek(30); document.querySelector("#btnInfo").click(); });
await wait(300);
await page.evaluate(() => document.getElementById("sec-arsiv").scrollIntoView());
await wait(400);
await page.screenshot({ path: `${OUT}/12-bilgi-arsiv.png` });
console.log("   12-bilgi-arsiv");
await page.evaluate(() => { document.getElementById("sec-fizik").querySelectorAll("details").forEach((d) => (d.open = true)); document.getElementById("sec-fizik").scrollIntoView(); });
await wait(400);
await page.screenshot({ path: `${OUT}/13-bilgi-fizik.png` });
console.log("   13-bilgi-fizik");
await page.evaluate(() => document.querySelector("#drawer .dh .pill").click());
// Obje seçimi
await page.evaluate(() => { SIM.seek(18); let ok = false; for (let y = 300; y < 650 && !ok; y += 20) for (let x = 650; x < 950 && !ok; x += 20) ok = SIM.pick(x, y); });
await wait(500);
await page.screenshot({ path: `${OUT}/14-obje-secimi.png` });
console.log("   14-obje-secimi");
// İngilizce
await load("#capture", "en");
await seekShot(24 + 7.5, "15-english-storm");
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
await load("#capture", "tr");
await seekShot(24 + 7.5, "16-mobil");
await browser.close();
