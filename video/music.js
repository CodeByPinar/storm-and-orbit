// Videonun müziği: OfflineAudioContext ile tarayıcıda, gerçek zamandan bağımsız sentezlenir ve WAV olarak döner.
// Re minör, 96 BPM; sahne kesmeleri vuruşa oturur ve ses tasarımı (yükselen ses, darbe) kesmelerle eşleşir.
window.__renderMusic = async (CUTS, DURATION) => {
  const SR = 48000, LEN = Math.ceil((DURATION + 0.2) * SR);
  const ctx = new OfflineAudioContext(2, LEN, SR);
  const mf = (m) => 440 * Math.pow(2, (m - 69) / 12);
  let seed = 1234; const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  // Ana zincir
  const lo = ctx.createBiquadFilter(); lo.type = "lowshelf"; lo.frequency.value = 110; lo.gain.value = 2.5;
  const hi = ctx.createBiquadFilter(); hi.type = "highshelf"; hi.frequency.value = 7000; hi.gain.value = 2;
  const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -18; comp.knee.value = 10; comp.ratio.value = 3; comp.attack.value = 0.012; comp.release.value = 0.2;
  const lim = ctx.createDynamicsCompressor(); lim.threshold.value = -2.5; lim.knee.value = 0; lim.ratio.value = 20; lim.attack.value = 0.002; lim.release.value = 0.1;
  const master = ctx.createGain(); master.gain.value = 0.9;
  const bus = ctx.createGain(); bus.connect(lo).connect(hi).connect(comp).connect(lim).connect(master).connect(ctx.destination);
  master.gain.setValueAtTime(0.9, DURATION - 2.6); master.gain.linearRampToValueAtTime(0.0001, DURATION);
  const padBus = ctx.createGain(); padBus.connect(bus);
  // Yankı
  const ir = ctx.createBuffer(2, SR * 3.4, SR);
  for (let c = 0; c < 2; c++) { const d = ir.getChannelData(c); let lp = 0; for (let i = 0; i < d.length; i++) { const t = i / SR; if (t < 0.02) continue; const x = (rnd() * 2 - 1) * Math.exp(-t * 2.0); lp += (x - lp) * (0.1 + 0.6 * Math.exp(-t * 2.5)); d[i] = lp * 1.6; } }
  const verb = ctx.createConvolver(); verb.buffer = ir; const verbIn = ctx.createGain(); const vr = ctx.createGain(); vr.gain.value = 0.32; verbIn.connect(verb).connect(vr).connect(bus);
  // Ping-pong eko
  const BEAT = 60 / 96, BAR = BEAT * 4;
  const dlyIn = ctx.createGain(), dl = ctx.createDelay(2), dr = ctx.createDelay(2), fb = ctx.createGain(), lpd = ctx.createBiquadFilter(), pl = ctx.createStereoPanner(), pr = ctx.createStereoPanner(), dg = ctx.createGain();
  dl.delayTime.value = dr.delayTime.value = BEAT * 0.75; fb.gain.value = 0.34; lpd.type = "lowpass"; lpd.frequency.value = 3200; pl.pan.value = -0.7; pr.pan.value = 0.7; dg.gain.value = 0.45;
  dlyIn.connect(dl); dl.connect(lpd).connect(dr); dr.connect(fb).connect(dl); dl.connect(pl).connect(dg); dr.connect(pr).connect(dg); dg.connect(bus); dg.connect(verbIn);
  const noise = ctx.createBuffer(1, SR * 2, SR); { const d = noise.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = rnd() * 2 - 1; }
  const wave = (fn, N) => { const re = new Float32Array(N + 1), im = new Float32Array(N + 1); for (let n = 1; n <= N; n++) im[n] = fn(n); return ctx.createPeriodicWave(re, im); };
  const WARM = wave((n) => 1 / Math.pow(n, 1.45), 32), REED = wave((n) => (n % 2 ? 1 / n : 0.3 / n), 24);
  function route(node, { pad = false, v = 0.2, d = 0, pan = 0 } = {}) {
    let n = node; if (pan) { const p = ctx.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, pan)); node.connect(p); n = p; }
    n.connect(pad ? padBus : bus);
    if (v) { const g = ctx.createGain(); g.gain.value = v; n.connect(g).connect(verbIn); }
    if (d) { const g = ctx.createGain(); g.gain.value = d; n.connect(g).connect(dlyIn); }
  }
  const I = {
    pad(t, notes, len, lvl) {
      const out = ctx.createGain(), f = ctx.createBiquadFilter(); f.type = "lowpass"; f.Q.value = 0.6;
      f.frequency.setValueAtTime(380, t); f.frequency.linearRampToValueAtTime(1500, t + Math.min(3, len * 0.6)); f.connect(out); route(out, { pad: true, v: 0.6 });
      notes.forEach((m, k) => { const pn = ctx.createStereoPanner(); pn.pan.value = ((k / Math.max(1, notes.length - 1)) - 0.5) * 0.9; pn.connect(f);
        for (const det of [-8, 8]) { const o = ctx.createOscillator(); o.setPeriodicWave(WARM); o.frequency.value = mf(m); o.detune.value = det; const g = ctx.createGain(); g.gain.value = 0.5; o.connect(g).connect(pn); o.start(t); o.stop(t + len + 3); }
        if (!k) { const s = ctx.createOscillator(); s.frequency.value = mf(m - 12); const g = ctx.createGain(); g.gain.value = 0.35; s.connect(g).connect(pn); s.start(t); s.stop(t + len + 3); } });
      out.gain.setValueAtTime(0.0001, t); out.gain.linearRampToValueAtTime(lvl, t + Math.min(1.6, len * 0.35)); out.gain.setTargetAtTime(lvl * 0.85, t + 1.6, 0.5); out.gain.setTargetAtTime(0.0001, t + len, 0.7);
    },
    bell(t, m, lvl, pan = 0, dec = 2.4) {
      const car = ctx.createOscillator(), mod = ctx.createOscillator(), mg = ctx.createGain(), out = ctx.createGain();
      car.frequency.value = mf(m); mod.frequency.value = mf(m) * 3.5; mg.gain.setValueAtTime(mf(m) * 2, t); mg.gain.exponentialRampToValueAtTime(mf(m) * 0.1, t + dec * 0.6);
      mod.connect(mg).connect(car.frequency); car.connect(out); route(out, { v: 0.45, d: 0.25, pan });
      out.gain.setValueAtTime(0.0001, t); out.gain.linearRampToValueAtTime(lvl, t + 0.004); out.gain.setTargetAtTime(0.0001, t + 0.01, dec / 4);
      car.start(t); mod.start(t); car.stop(t + dec + 0.5); mod.stop(t + dec + 0.5);
    },
    arp(t, m, lvl, pan) { const o = ctx.createOscillator(), f = ctx.createBiquadFilter(), g = ctx.createGain(); o.setPeriodicWave(REED); o.frequency.value = mf(m);
      f.type = "lowpass"; f.Q.value = 3; f.frequency.setValueAtTime(3400, t); f.frequency.exponentialRampToValueAtTime(450, t + 0.22); o.connect(f).connect(g); route(g, { v: 0.2, d: 0.3, pan });
      g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(lvl, t + 0.004); g.gain.setTargetAtTime(0.0001, t + 0.02, 0.07); o.start(t); o.stop(t + 0.5); },
    bass(t, m, len, lvl) { const o = ctx.createOscillator(), o2 = ctx.createOscillator(), sh = ctx.createWaveShaper(), f = ctx.createBiquadFilter(), g = ctx.createGain(), g2 = ctx.createGain();
      o.frequency.value = mf(m); o2.type = "triangle"; o2.frequency.value = mf(m) * 2; g2.gain.value = 0.35; const c = new Float32Array(256); for (let i = 0; i < 256; i++) c[i] = Math.tanh(1.8 * (i / 128 - 1)); sh.curve = c;
      f.type = "lowpass"; f.frequency.value = 460; o.connect(sh); o2.connect(g2).connect(sh); sh.connect(f).connect(g); route(g, { v: 0.03 });
      g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(lvl, t + 0.012); g.gain.setTargetAtTime(lvl * 0.7, t + 0.02, 0.08); g.gain.setTargetAtTime(0.0001, t + len, 0.05);
      o.start(t); o2.start(t); o.stop(t + len + 0.4); o2.stop(t + len + 0.4); },
    kick(t, lvl) { const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.setValueAtTime(160, t); o.frequency.exponentialRampToValueAtTime(45, t + 0.17); o.connect(g); route(g, { v: 0.02 });
      g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(lvl, t + 0.004); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.45); o.start(t); o.stop(t + 0.5);
      I.noise(t, 0.012, "highpass", 2600, 2600, 0.7, lvl * 0.22, 0.001, 0);
      padBus.gain.setValueAtTime(1, t); padBus.gain.linearRampToValueAtTime(0.5, t + 0.012); padBus.gain.setTargetAtTime(1, t + 0.05, 0.09); },
    snare(t, lvl) { I.noise(t, 0.22, "bandpass", 1900, 1500, 0.8, lvl, 0.002, 0.28); const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.value = 190; o.connect(g); route(g, { v: 0.2 });
      g.gain.setValueAtTime(lvl * 0.6, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.1); o.start(t); o.stop(t + 0.12); },
    hat(t, lvl, pan) { I.noise(t, 0.045, "highpass", 7800, 9000, 0.7, lvl, 0.001, 0.05, pan); },
    noise(t, len, type, f0, f1, q, lvl, a = 0.02, v = 0.3, pan = 0) { const s = ctx.createBufferSource(); s.buffer = noise; s.loop = true; const f = ctx.createBiquadFilter(); f.type = type; f.Q.value = q;
      f.frequency.setValueAtTime(f0, t); f.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + len); const g = ctx.createGain(); s.connect(f).connect(g); route(g, { v, pan });
      g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(lvl, t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + len); s.start(t, (t * 7.3) % 1.5); s.stop(t + len + 0.05); },
    riser(t, len, lvl) { const s = ctx.createBufferSource(); s.buffer = noise; s.loop = true; const f = ctx.createBiquadFilter(); f.type = "bandpass"; f.Q.value = 1.4;
      f.frequency.setValueAtTime(240, t); f.frequency.exponentialRampToValueAtTime(5600, t + len); const g = ctx.createGain(); s.connect(f).connect(g); route(g, { v: 0.5, d: 0.1 });
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(lvl, t + len); g.gain.linearRampToValueAtTime(0.0001, t + len + 0.05); s.start(t); s.stop(t + len + 0.1); },
    impact(t, lvl) { I.kick(t, lvl); const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.setValueAtTime(62, t); o.frequency.exponentialRampToValueAtTime(36, t + 1.6); o.connect(g); route(g, { v: 0.35 });
      g.gain.setValueAtTime(lvl * 0.85, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 2); o.start(t); o.stop(t + 2.1); I.noise(t, 1.6, "lowpass", 1000, 70, 0.7, lvl * 0.5, 0.003, 0.6); },
    whoosh(t, lvl) { I.noise(t - 0.35, 0.5, "bandpass", 600, 3800, 1.1, lvl, 0.3, 0.4); },
    ping(t, f, lvl, dec, pan) { const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.value = f; o.connect(g); route(g, { v: 0.4, pan });
      g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(lvl, t + 0.003); g.gain.exponentialRampToValueAtTime(0.0001, t + dec); o.start(t); o.stop(t + dec + 0.05); },
  };
  // Armoni ve düzen
  const C = { Dm9: [38, [57, 60, 64, 65]], Bb: [34, [57, 58, 62, 65]], F: [41, [57, 60, 64, 65]], Csus2: [36, [55, 60, 62, 67]], Gm9: [43, [57, 58, 62, 65]], Eb: [39, [55, 58, 62, 63]],
    A7sus: [45, [55, 57, 62, 64]], A7: [45, [55, 57, 61, 64]], Am7: [45, [55, 57, 60, 64]], D: [38, [57, 62, 66, 69]] };
  // Sahne başına: akorlar, pad seviyesi, davul yoğunluğu (0 yok, 1 yarım, 2 tam), arpej, çan
  const SEC = [
    { ch: ["Dm9", "Bb"], pad: 0.055, drums: 0, arp: 0, bell: 1, bass: "whole" },
    { ch: ["Dm9", "Bb", "F", "Csus2"], pad: 0.045, drums: 1, arp: 8, bass: "half" },
    { ch: ["Gm9", "Eb", "Bb", "A7"], pad: 0.042, drums: 2, arp: 16, bass: "8" },
    { ch: ["Dm9", "Am7", "Bb", "A7sus"], pad: 0.045, drums: 2, arp: 8, bass: "8" },
    { ch: ["F", "Csus2", "Dm9", "Bb"], pad: 0.045, drums: 2, arp: 16, bass: "8" },
    { ch: ["Dm9", "Bb", "Gm9", "A7"], pad: 0.045, drums: 1, arp: 8, bass: "half", pings: 1 },
    { ch: ["Dm9", "Eb", "F", "A7"], pad: 0.05, drums: 0, arp: 16, bass: "whole", servo: 1 },
    { ch: ["Bb", "D"], pad: 0.06, drums: 0, arp: 0, bell: 1, bass: "whole", end: 1 },
  ];
  SEC.forEach((S, k) => {
    const t0 = CUTS[k], t1 = CUTS[k + 1], len = t1 - t0, n = S.ch.length, seg = len / n;
    S.ch.forEach((name, i) => { const [root, v] = C[name]; const ts = t0 + i * seg;
      I.pad(ts, v, seg + (S.end && i === n - 1 ? 1.5 : 0.15), S.pad);
      const bl = S.bass === "whole" ? [[0, 1]] : S.bass === "half" ? [[0, 0.5], [0.5, 0.5]] : [...Array(Math.max(2, Math.round(seg / (BEAT / 2))))].map((_, j, a) => [j / a.length, 0.9 / a.length]);
      bl.forEach(([b, l], j) => I.bass(ts + b * seg, root + (S.bass === "8" && j % 4 === 3 ? 12 : 0), l * seg * 0.95, S.bass === "8" ? 0.09 : 0.12));
      if (S.arp) { const step = BEAT * 4 / S.arp, pat = [0, 1, 2, 3, 2, 1, 3, 2]; for (let j = 0; ts + j * step < ts + seg - 0.02; j++) I.arp(ts + j * step, v[pat[j % 8]] + 12, 0.028, j % 2 ? 0.45 : -0.45); }
    });
    if (S.drums) for (let b = 0; t0 + b * BEAT < t1 - 0.05; b++) { const t = t0 + b * BEAT;
      if (S.drums === 2 || b % 2 === 0) I.kick(t, b % 4 === 0 ? 0.36 : 0.28);
      if (S.drums === 2 && b % 2 === 1) I.snare(t, 0.1);
      for (let h = 0; h < (S.drums === 2 ? 4 : 2); h++) I.hat(t + h * BEAT / (S.drums === 2 ? 4 : 2), h % 2 ? 0.018 : 0.03, h % 2 ? 0.3 : -0.2); }
    if (S.bell) { const mel = S.end ? [74, 78, 81, 86] : [72, 69, 77, 74, 76]; mel.forEach((m, i) => I.bell(t0 + 0.4 + i * (S.end ? 0.45 : 0.9), m, S.end ? 0.05 : 0.04, i % 2 ? 0.35 : -0.35, S.end ? 3.2 : 2.4)); }
    if (S.pings) for (let i = 0; i < 49; i++) I.ping(t0 + 0.3 + i * 0.05, 3136 + (i % 5) * 220, 0.006, 0.04, (i % 7) / 7 - 0.5);
    if (S.servo) for (let i = 0; i < 40; i++) I.ping(t0 + 0.2 + rnd() * (len - 0.6), 2200 + rnd() * 3400, 0.004 + 0.004 * rnd(), 0.06 + 0.1 * rnd(), rnd() * 1.4 - 0.7);
    if (k > 0 && !S.end) I.whoosh(t0, 0.05);
  });
  // Ses tasarımı: fırtınadan önce yükselen ses ve darbe, sona doğru ikinci darbe
  I.riser(CUTS[2] - 1.6, 1.6, 0.09); I.impact(CUTS[2], 0.34);
  I.noise(CUTS[2], 4.5, "bandpass", 300, 2600, 1.2, 0.05, 1.2, 0.4);
  I.riser(CUTS[7] - 1.6, 1.6, 0.08); I.impact(CUTS[7], 0.3);
  I.bell(0.25, 62, 0.035, 0, 3.5);
  const buf = await ctx.startRendering();
  // 16 bit PCM WAV
  const L = buf.getChannelData(0), Rr = buf.getChannelData(1), N = buf.length, out = new DataView(new ArrayBuffer(44 + N * 4));
  const ws = (o, s) => { for (let i = 0; i < s.length; i++) out.setUint8(o + i, s.charCodeAt(i)); };
  ws(0, "RIFF"); out.setUint32(4, 36 + N * 4, true); ws(8, "WAVE"); ws(12, "fmt "); out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, 2, true);
  out.setUint32(24, SR, true); out.setUint32(28, SR * 4, true); out.setUint16(32, 4, true); out.setUint16(34, 16, true); ws(36, "data"); out.setUint32(40, N * 4, true);
  let peak = 0; for (let i = 0; i < N; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(Rr[i]));
  const g = peak > 0.98 ? 0.98 / peak : 1;
  for (let i = 0; i < N; i++) { out.setInt16(44 + i * 4, Math.max(-1, Math.min(1, L[i] * g)) * 32767, true); out.setInt16(46 + i * 4, Math.max(-1, Math.min(1, Rr[i] * g)) * 32767, true); }
  const bytes = new Uint8Array(out.buffer); let s = ""; for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return { b64: btoa(s), peak };
};
