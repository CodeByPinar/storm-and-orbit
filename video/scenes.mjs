// Tanıtım videosunun senaryosu: her sahne, videonun bir aralığını sunumun simülasyon zamanına eşler
// ve üstüne bindirilecek metni tanımlar. Sayılar analiz çıktılarıyla aynıdır (docs/SONUCLAR.md).
export const FPS = 30;
export const W = 1920, H = 1080;

export const SCENES = [
  { id: "title", t0: 0, t1: 5.2, sim: [0.6, 6.4], view: 0, layout: "center",
    kicker: "Bir uzay havası veri bilimi projesi", title: "Fırtına ve Yörünge",
    sub: "Güneş fırtınaları alçak yörüngedeki uyduları nasıl alçaltıyor?" },
  { id: "cycle", t0: 5.2, t1: 10.2, sim: [13.2, 22.5], view: 0.17,
    kicker: "60 yıl · 35.231 yeniden giriş", title: "Güneş aktifken yörünge çabuk boşalıyor",
    big: { v: 3.52, d: 1, suffix: "×" }, sub: "Güneş maksimumunda düşme oranı, minimumun 3,5 katı" },
  { id: "storm", t0: 10.2, t1: 15.6, sim: [27.0, 35.2], view: 0.1,
    kicker: "11 Mayıs 2024 · süper fırtına", title: "1960'tan beri en güçlü ikinci fırtına günü",
    big: { v: 271, d: 0, prefix: "Ap " }, sub: "Manyetosfer sıkıştı, kutup ışıkları alçak enlemlere indi" },
  { id: "week", t0: 15.6, t1: 20.6, sim: [38.6, 47.0], view: 0.14,
    kicker: "64 fırtına · 10.695 yörünge ölçümü", title: "Fırtına haftasında yörüngeler daha hızlı alçalıyor",
    big: { v: 1.3, d: 2, suffix: "×" }, sub: "Fırtınasız plasebo haftasında 0,95× · 64 fırtınanın 49'unda" },
  { id: "dose", t0: 20.6, t1: 25.1, sim: [61.2, 71.0], view: 0.17,
    kicker: "Doz-yanıt", title: "Her +10 Ap alçalmayı hızlandırıyor",
    big: { v: 10.7, d: 1, prefix: "+%" }, sub: "Yükseldikçe artıyor: 550–700 km'de +%12,7" },
  { id: "starlink", t0: 25.1, t1: 29.6, sim: [73.8, 82.6], view: 0.1,
    kicker: "Şubat 2022 · Starlink", title: "Küçük bir fırtına, 38 uydu",
    big: { v: 38, d: 0, suffix: "/49" }, sub: "209 km'de bırakılan uydular yükselemeden atmosfere girdi" },
  { id: "drag", t0: 29.6, t1: 33.6, sim: [86.0, 93.4], view: 0.12,
    kicker: "Sürtünme anatomisi", title: "Hava yoğunlaşınca uydu frenlenir",
    big: { text: "ρ · v² · A" }, sub: "39 parça · 1.143 bileşen · tarayıcıda, gerçek zamanlı" },
  { id: "end", t0: 33.6, t1: 38.6, sim: [102.6, 107.4], view: 0, layout: "end",
    kicker: "Etkileşimli 3B sunum · Türkçe ve English", title: "Fırtına ve Yörünge",
    lines: ["storm-and-orbit.up.railway.app", "github.com/CodeByPinar/storm-and-orbit"] },
];
export const DURATION = SCENES[SCENES.length - 1].t1;

// Müzik için bölüm sınırları (saniye)
export const CUTS = SCENES.map((s) => s.t0).concat(DURATION);
