"""README ve belgeler için sonuç grafiklerini üretir -> docs/figures/*.png

Girdi: dash_data/*.json (analysis.py ve altitude.py çıktıları)
Çalıştır: python tools/make_figures.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

VIOLET, INK, MUTED, SOFT, GREY = "#8a4dff", "#17141f", "#8b869a", "#efe7ff", "#c9c2dc"
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.size": 10.5, "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.edgecolor": "#d9d4e6", "axes.labelcolor": "#4f4a5e", "xtick.color": "#4f4a5e", "ytick.color": "#4f4a5e",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#efedf5", "grid.linewidth": 0.8,
    "legend.frameon": False, "axes.axisbelow": True,
})


def rows(name):
    return json.loads((ROOT / "dash_data" / f"{name}.json").read_text(encoding="utf-8"))["rows"]


def save(fig, name, note):
    fig.text(0.01, 0.01, note, fontsize=8, color=MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / name, dpi=150)
    plt.close(fig)
    print("  ", name)


# 1. Güneş döngüsü ve düşme oranı
y = rows("yearly")
yr = np.array([r["year"] for r in y]); f = np.array([r["f107"] for r in y]); rate = np.array([r["rate_pct"] for r in y])
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.fill_between(yr, f, color=SOFT, lw=0); ax.plot(yr, f, color=VIOLET, lw=2, label="F10.7 (sfu, sol eksen)")
ax.set_ylabel("Yıllık ortalama F10.7 (sfu)"); ax.set_ylim(0, 260)
ax2 = ax.twinx(); ax2.plot(yr, rate, color=INK, lw=1.8, label="Yıllık düşme oranı (%, sağ eksen)")
ax2.set_ylabel("Kontrolsüz objelerin yıllık düşme oranı (%)"); ax2.set_ylim(0, 15); ax2.grid(False); ax2.spines["right"].set_visible(True)
ax.set_title("Güneş aktifken yörünge daha çabuk boşalıyor (1966–2025)")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, loc="upper left")
save(fig, "solar_cycle.png", "Kaynak: GCAT (satcat + auxcat), GFZ Potsdam F10.7 · Spearman r = 0,78; maksimum/minimum oranı 3,52×")

# 2. Fırtına sonrası günlük yeniden girişler (üst üste bindirilmiş olay analizi)
e = rows("epoch")
lag = np.array([r["lag"] for r in e]); obs = np.array([r["observed"] for r in e])
fig, ax = plt.subplots(figsize=(10, 4))
ax.fill_between(lag, [r["null_lo"] for r in e], [r["null_hi"] for r in e], color=GREY, alpha=0.45, lw=0, label="Rastgele tarihlerle %95 aralık")
ax.plot(lag, [r["null_mid"] for r in e], color=MUTED, lw=1, ls="--")
ax.plot(lag, obs, color=VIOLET, lw=2, label="54 fırtınanın ortalaması")
ax.axvline(0, color=INK, lw=0.8); ax.axhline(1, color="#cfc8e2", lw=0.8)
ax.set_xlabel("Fırtınaya göre gün"); ax.set_ylabel("Günlük yeniden giriş (normale göre ×)")
ax.set_title("Fırtına sonrası düşen obje sayısı: artış var ama aralığın içinde")
ax.legend(loc="upper left")
save(fig, "reentry_epoch.png", "Üst üste bindirilmiş olay analizi · Ap ≥ 100 olan 54 fırtına · sonraki 14 gün: +%11,7 (p = 0,082)")

# 3. Doz-yanıt: haftalık Ap artışı ve alçalma oranı
w = rows("alt_windows"); g = [r for r in rows("alt_grid") if r["band"] == "Tümü" and r["d_ap"] <= 65]
fig, ax = plt.subplots(figsize=(10, 4.8))
for kind, col, lab, z in [("placebo", GREY, "Plasebo haftası", 2), ("storm", VIOLET, "Fırtına haftası", 3)]:
    pts = [r for r in w if r["kind"] == kind]
    ax.scatter([r["d_ap"] for r in pts], [r["ratio"] for r in pts], s=26, color=col, edgecolor="white", lw=0.6, label=lab, zorder=z)
gx = [r["d_ap"] for r in g]
ax.fill_between(gx, [r["lo"] for r in g], [r["hi"] for r in g], color=INK, alpha=0.08, lw=0)
ax.plot(gx, [r["ratio"] for r in g], color=INK, lw=2, label="Model ve %95 aralık", zorder=4)
ax.set_yscale("log"); ax.set_yticks([0.5, 1, 2, 3]); ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}×")); ax.get_yaxis().set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.axhline(1, color="#cfc8e2", lw=0.8)
ax.set_xlabel("Haftalık ortalama Ap artışı (önceki 11 güne göre)"); ax.set_ylabel("Alçalma oranı (gerçek ÷ beklenen)")
ax.set_title("Her +10 Ap haftalık alçalmayı %10,7 hızlandırıyor")
ax.legend(loc="upper left")
save(fig, "dose_response.png", "128 hafta (64 fırtına + 64 plasebo) · %95 aralık +%7,7 – +%15,0 · 49/64 fırtınada etki plasebodan büyük, Wilcoxon p = 1,1·10⁻⁵")

# 4. İrtifa bantları
c = [r for r in rows("alt_coef") if r["band"] != "Tümü"]
fig, ax = plt.subplots(figsize=(10, 3.4))
for i, r in enumerate(c):
    ax.plot([r["ap_pct_lo"], r["ap_pct_hi"]], [i, i], color=VIOLET, lw=3, solid_capstyle="round")
    ax.scatter([r["ap_pct"]], [i], s=90, color=VIOLET, edgecolor="white", lw=2, zorder=3)
    ax.text(r["ap_pct_hi"] + 0.4, i, f"+%{r['ap_pct']:.1f}".replace(".", ","), va="center", color=INK, fontsize=10.5)
ax.set_yticks(range(len(c))); ax.set_yticklabels([f"{r['band']}\n({r['n_windows']} hafta)" for r in c]); ax.set_ylim(len(c) - 0.5, -0.5)
ax.set_xlim(0, max(r["ap_pct_hi"] for r in c) + 4); ax.set_xlabel("+10 Ap başına alçalmanın hızlanması (%)")
ax.set_title("Etki yükseldikçe büyüyor")
save(fig, "altitude_bands.png", "Bant başına ayrı model · güven aralıkları fırtınalar yeniden örneklenerek (2.000 kez)")

# 5. Kayıp gün eğrileri
cv = rows("alt_curves")
fig, ax = plt.subplots(figsize=(10, 4))
for name, col in [("Orta (Ap 50–80)", "#d4c2ff"), ("Güçlü (Ap 80–130)", "#a57bff"), ("Şiddetli (Ap > 130)", "#6a2cf0")]:
    pts = sorted([r for r in cv if r["strength"] == name], key=lambda r: r["day"])
    ax.plot([r["day"] for r in pts], [r["lost_days"] for r in pts], color=col, lw=2.2, label=f"{name} · {pts[0]['n_events']} fırtına")
ax.axvline(0, color=INK, lw=0.8); ax.axhline(0, color="#cfc8e2", lw=0.8)
ax.set_xlabel("Fırtınaya göre gün"); ax.set_ylabel("Fazladan alçalma (gün)")
ax.set_title("Güçlü fırtınada yörünge birkaç günde haftalarca alçalabiliyor")
ax.legend(loc="upper left")
save(fig, "lost_days.png", "Ortanca obje · fazladan alçalma, objenin normal günlük alçalması cinsinden · Mayıs 2024: 6,9 gün, Cadılar Bayramı 2003: 15,0 gün")

# 6. Starlink
s = rows("starlink_kp")
groups = ["Normal bırakma", "Alçak bırakma (<250 km)"]; bins = ["Kp < 4", "Kp 4–5", "Kp ≥ 5"]
fig, ax = plt.subplots(figsize=(10, 3.8))
x = np.arange(len(groups)); wbar = 0.26
for k, (b, col) in enumerate(zip(bins, ["#d9d3ec", "#b9a6ee", VIOLET])):
    vals = [next(r for r in s if r["group"] == gname and r["kp_bin"] == b) for gname in groups]
    bars = ax.bar(x + (k - 1) * wbar, [v["lost_pct"] for v in vals], wbar * 0.92, color=col, label=f"İlk hafta {b}")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.06, f"%{v['lost_pct']:.2f}\n{v['lost']}/{v['sats']:,}".replace(",", ".").replace("%0.", "%0,").replace("%3.", "%3,"),
                ha="center", va="bottom", fontsize=8.5, color=INK)
ax.set_xticks(x); ax.set_xticklabels(groups); ax.set_ylabel("İlk 30 günde kayıp (%)"); ax.set_ylim(0, 5)
ax.set_title("Starlink: alçak bırakılıp fırtınaya denk gelenler")
ax.legend(loc="upper left")
save(fig, "starlink.png", "407 fırlatma, 12.474 uydu · fırtınalı alçak fırlatmalardaki kaybın 38'i tek olaydan: Şubat 2022 (49 uydudan 38'i)")
print("tamam:", OUT)
