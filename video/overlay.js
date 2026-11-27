// Sayfaya enjekte edilen video katmanı. Her kare yalnızca zamana bağlı hesaplanır (geçiş animasyonu yok),
// böylece kareler tek tek, sırasız ve tekrarlanabilir biçimde üretilebilir.
window.__installOverlay = (SCENES, DURATION) => {
  const css = `
    .ui, #callouts, #leaders, #hint, #pick, #drawer, #boot { display: none !important; }
    #vo { position: fixed; inset: 0; z-index: 50; pointer-events: none; font-family: "Inter Tight", system-ui, sans-serif; color: #17141f; }
    #vo .scrim { position: absolute; inset: 0; }
    #vo .block { position: absolute; left: 128px; top: 50%; width: 820px; transform: translateY(-50%); display: flex; flex-direction: column; gap: 22px; }
    #vo .kicker { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 22px; letter-spacing: .14em; text-transform: none; color: #6a2cf0; }
    #vo .title { font-size: 68px; line-height: 1.04; font-weight: 600; letter-spacing: -.03em; text-wrap: balance; }
    #vo .big { font-size: 170px; line-height: .92; font-weight: 600; letter-spacing: -.045em; color: #8a4dff; font-variant-numeric: tabular-nums; }
    #vo .sub { font-size: 30px; line-height: 1.35; color: #4f4a5e; max-width: 760px; text-wrap: balance; }
    #vo .center { left: 50%; width: 1300px; transform: translate(-50%, -50%); align-items: center; text-align: center; }
    #vo .center .title { font-size: 132px; letter-spacing: -.045em; }
    #vo .center .sub { font-size: 36px; max-width: 1100px; }
    #vo .lines { display: flex; flex-direction: column; gap: 14px; align-items: center; margin-top: 10px; }
    #vo .lines div { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 30px; color: #17141f; background: rgba(255,255,255,.82); border: 1px solid #e3dfee; border-radius: 999px; padding: 12px 28px; }
    #vo .lines div:first-child { background: #17141f; color: #fff; border-color: #17141f; }
    #vo .brand { position: absolute; left: 64px; top: 52px; display: flex; align-items: center; gap: 16px; font-size: 26px; font-weight: 600; letter-spacing: -.01em; }
    #vo .brand svg { width: 50px; height: 50px; }
    #vo .brand span { display: inline; font-family: "Inter Tight", system-ui, sans-serif; font-size: 26px; font-weight: 600; letter-spacing: -.01em; text-transform: none; color: #17141f; }
    #vo .src { position: absolute; left: 64px; bottom: 50px; font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 17px; letter-spacing: .08em; color: #8b869a; text-transform: none; }
    #vo .prog { position: absolute; left: 64px; right: 64px; bottom: 30px; height: 3px; border-radius: 3px; background: #e3dfee; overflow: hidden; }
    #vo .prog i { display: block; height: 100%; background: #8a4dff; }
    #vo .dip { position: absolute; inset: 0; background: #f6f5fa; }
    #vo .mark { width: 120px; height: 120px; }
  `;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  const root = document.createElement("div"); root.id = "vo";
  root.innerHTML = `
    <div class="scrim"></div>
    <div class="brand"><svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="7.5" fill="#17141f"/><ellipse cx="20" cy="20" rx="17" ry="7" fill="none" stroke="#8a4dff" stroke-width="2" transform="rotate(-24 20 20)"/><circle cx="34.2" cy="13.6" r="2.6" fill="#8a4dff"/></svg><span>Fırtına ve Yörünge</span></div>
    <div class="block"><svg class="mark" viewBox="0 0 40 40"><circle cx="20" cy="20" r="7.5" fill="#17141f"/><ellipse cx="20" cy="20" rx="17" ry="7" fill="none" stroke="#8a4dff" stroke-width="2" transform="rotate(-24 20 20)"/><circle cx="34.2" cy="13.6" r="2.6" fill="#8a4dff"/></svg><div class="kicker"></div><div class="title"></div><div class="big"></div><div class="sub"></div><div class="lines"></div></div>
    <div class="src">VERİ: GCAT · GFZ POTSDAM · SPACE-TRACK.ORG</div>
    <div class="prog"><i></i></div>
    <div class="dip"></div>`;
  document.body.appendChild(root);
  const $ = (s) => root.querySelector(s);
  const E = { scrim: $(".scrim"), brand: $(".brand"), block: $(".block"), mark: $(".mark"), kicker: $(".kicker"), title: $(".title"), big: $(".big"), sub: $(".sub"), lines: $(".lines"), src: $(".src"), prog: $(".prog i"), dip: $(".dip") };
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const ease = (x) => { x = clamp(x, 0, 1); return 1 - Math.pow(1 - x, 3); };
  const fmt = (v, d) => v.toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d });
  // Türkçe büyük harf (i → İ), ama marka ve İngilizce kelimeler (Starlink, English) Latin kuralıyla
  const KEEP = /^(starlink|english)$/i;
  const up = (s) => s.split(/(\s+)/).map((w) => (KEEP.test(w) ? w.toUpperCase() : w.toLocaleUpperCase("tr-TR"))).join("");
  let cur = null;
  function show(el, lt, at, dy = 26, out = 1) {
    const k = ease((lt - at) / 0.55) * out;
    el.style.opacity = k.toFixed(3); el.style.transform = `translateY(${((1 - ease((lt - at) / 0.55)) * dy).toFixed(1)}px)`;
  }
  window.__overlay = (t) => {
    const s = SCENES.find((q) => t >= q.t0 && t < q.t1) || SCENES[SCENES.length - 1];
    const lt = t - s.t0, len = s.t1 - s.t0;
    if (cur !== s.id) {
      cur = s.id;
      E.block.className = "block" + (s.layout === "center" || s.layout === "end" ? " center" : "");
      E.kicker.textContent = up(s.kicker || ""); E.title.textContent = s.title || ""; E.sub.textContent = s.sub || "";
      E.big.style.display = s.big ? "" : "none"; E.mark.style.display = s.layout ? "" : "none";
      E.lines.replaceChildren(...(s.lines || []).map((x) => { const d = document.createElement("div"); d.textContent = x; return d; }));
      E.lines.style.display = s.lines ? "" : "none"; E.sub.style.display = s.sub ? "" : "none";
      E.scrim.style.background = s.layout
        ? "radial-gradient(1100px 620px at 50% 50%, rgba(246,245,250,.86) 0%, rgba(246,245,250,.55) 55%, rgba(246,245,250,0) 100%)"
        : "linear-gradient(90deg, rgba(246,245,250,.94) 0%, rgba(246,245,250,.82) 30%, rgba(246,245,250,.35) 50%, rgba(246,245,250,0) 62%)";
    }
    // Çıkış: sahnenin son 0,45 saniyesinde metin söner (son sahne hariç)
    const out = s.id === "end" ? 1 : 1 - clamp((lt - (len - 0.45)) / 0.4, 0, 1);
    show(E.mark, lt, 0.05, 20, out); show(E.kicker, lt, 0.15, 26, out); show(E.title, lt, 0.32, 34, out);
    show(E.big, lt, 0.62, 40, out); show(E.sub, lt, s.big ? 1.05 : 0.7, 26, out); show(E.lines, lt, 1.0, 26, out);
    if (s.big) {
      if (s.big.text) E.big.textContent = s.big.text;
      else { const k = ease((lt - 0.62) / 1.25); E.big.textContent = (s.big.prefix || "") + fmt(s.big.v * k, s.big.d) + (s.big.suffix || ""); }
    }
    const chrome = s.layout ? 0 : 1;
    E.brand.style.opacity = E.src.style.opacity = (chrome * clamp(lt / 0.5, 0, 1) * (s.id === "drag" ? clamp((len - lt) / 0.4, 0, 1) : 1)).toFixed(3);
    E.prog.style.width = (100 * t / DURATION).toFixed(2) + "%";
    E.prog.parentElement.style.opacity = s.id === "title" ? clamp((lt - 3.5) / 0.8, 0, 1) : s.id === "end" ? clamp(1 - lt / 0.6, 0, 1) : 1;
    // Sahne geçişleri: kısa bir aydınlık kararma (açılışta ve kapanışta daha uzun)
    let dip = 0;
    for (const q of SCENES) { const d = Math.abs(t - q.t0); if (q.t0 > 0) dip = Math.max(dip, 1 - d / 0.22); }
    dip = Math.max(dip, 1 - t / 0.9, 1 - (DURATION - t) / 0.9);
    E.dip.style.opacity = clamp(dip, 0, 1).toFixed(3);
    E.scrim.style.opacity = s.id === "end" ? clamp(lt / 0.8, 0, 1).toFixed(3) : "1";
  };
};
