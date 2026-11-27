"""Fırtınalar uyduları ne kadar alçaltıyor? Space-Track yörünge geçmişinden irtifa analizi.

Çalıştır:  python altitude.py [veri_klasörü]     (varsayılan: data/spacetrack)
Çıktı:     results_alt.json  ve  dash_data/alt_*.json

Her obje ve her fırtına için:
  1. Fırtınadan önceki [-14, -3]. günlerde irtifanın normal alçalma hızı (Theil-Sen eğimi).
  2. Fırtına haftasında [-2, +5] gerçekte kaybedilen irtifa.
  3. Oran = gerçek kayıp / normal hızla beklenen kayıp.  1 = fırtına etkisiz.
     "Kayıp gün" = fazladan kaybedilen irtifanın kaç günlük normal alçalmaya denk geldiği.
  4. Aynı ölçüm, fırtınasız bir sahte tarihte (-16. gün; ön pencere [-30, -19]) tekrarlanır:
     plasebo. Gerçek etki = fırtına oranı ile plasebo oranı arasındaki fark.
Birim obje değil penceredir (aynı haftadaki objeler birlikte dalgalanır): her olay için bir
fırtına ve bir plasebo penceresi, her birinde ortanca oran.
Model: log(ortanca oran) ~ ΔAp/10 + ΔF10.7/10 (pencerenin ön pencereye göre artışı), tüm
bantlar ve üç irtifa bandı için ayrı; güven aralıkları olaylar yeniden örneklenerek (2.000 kez).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from load import load_kp

HERE = Path(__file__).parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "data" / "spacetrack"
MU, RE = 398600.4418, 6378.137
RNG = np.random.default_rng(11)

plan = {p["event"]: p for p in json.loads((HERE / "data" / "st_plan.json").read_text(encoding="utf-8"))}
kp = load_kp()
f107_81 = kp["F107"].rolling(81, center=True, min_periods=40).mean()


def altitude_km(mean_motion_rev_day):
    n = mean_motion_rev_day * 2 * np.pi / 86400.0
    return (MU / n ** 2) ** (1 / 3) - RE


def clean(g):
    g = g.drop_duplicates("day").sort_values("day")
    if len(g) < 8:
        return g.iloc[0:0]
    med = g["alt"].rolling(5, center=True, min_periods=3).median()
    return g[(g["alt"] - med).abs() < 1.0]          # TLE sıçramalarını at (>1 km)


def at(g, d, tol=1.6):
    """d günündeki irtifa: en yakın iki kayıttan doğrusal ara değer; yakında kayıt yoksa NaN."""
    if not ((g["day"] - d).abs() <= tol).any():
        return np.nan
    return float(np.interp(d, g["day"], g["alt"]))


def measure(g, d0):
    """d0 gününü 'fırtına' sayarak ölçüm; gerçek (d0=0) ve plasebo (d0=-16) tamamen simetrik.
    Ön eğilim yakın ve kısa bir pencereden [d0-14, d0-3] ölçülür: uzun pencerenin düz eğilimi,
    alçaldıkça hızlanan objelerde fırtına olmadan da 'fazla alçalma' üretiyordu."""
    pre = g[(g["day"] >= d0 - 14) & (g["day"] <= d0 - 3)]
    if len(pre) < 5 or pre["day"].max() - pre["day"].min() < 7:
        return None
    slope = stats.theilslopes(pre["alt"], pre["day"])[0]          # km/gün (negatif = alçalıyor)
    a0, a1 = at(g, d0 - 2), at(g, d0 + 5)
    if np.isnan(a0) or np.isnan(a1):
        return None
    loss, expected = a0 - a1, -slope * 7
    return {"slope_m_day": slope * 1000, "loss_m": loss * 1000, "expected_m": expected * 1000,
            "alt0": a0}


rows, curves = [], []
files = sorted(SRC.glob("*.csv"))
if not files:
    sys.exit(f"{SRC} içinde CSV yok. Önce spacetrack_fetch.py'yi çalıştır.")
for f in files:
    ev = f.stem
    p = plan.get(ev)
    if p is None:
        continue
    t0 = pd.Timestamp(ev)
    df = pd.read_csv(f)
    if df.empty:
        continue
    df["epoch"] = pd.to_datetime(df["EPOCH"])
    df["day"] = (df["epoch"] - t0) / pd.Timedelta(days=1)
    df["alt"] = altitude_km(df["MEAN_MOTION"].astype(float))
    for nid, g in df.groupby("NORAD_CAT_ID"):
        if g["ECCENTRICITY"].median() > 0.01:
            continue
        g = clean(g)
        if g.empty or not (250 <= g["alt"].median() <= 700):
            continue
        m, pl = measure(g, 0), measure(g, -16)
        if m is None:
            continue
        rows.append({"event": ev, "norad": int(nid), **m,
                     "pl_loss_m": pl["loss_m"] if pl else np.nan,
                     "pl_expected_m": pl["expected_m"] if pl else np.nan})
        # Üst üste bindirme eğrisi: ön eğilimden sapma, günlük normal alçalma cinsinden
        s = m["slope_m_day"] / 1000
        if s < -0.005:
            dd = np.arange(-10, 21)
            res = [(at(g, d, 1.6) - (m["alt0"] + s * (d + 2))) / s for d in dd]   # >0 = fazladan alçalma
            curves.append({"event": ev, "alt0": m["alt0"], "res": res})

R = pd.DataFrame(rows)
for k in ["ap_peak", "ap_sum3", "kp_peak"]:
    R[k] = R["event"].map(lambda e: plan[e][k])
R["f107_81"] = R["event"].map(lambda e: float(f107_81.loc[pd.Timestamp(e)]))
# Pencerelerde başka fırtına var mı? (gerçek ön pencere [-14,-3]; plasebo tamamı [-30,-11])
_apmax = lambda e, a, b: int(kp["Ap"].loc[pd.Timestamp(e) + pd.Timedelta(days=a): pd.Timestamp(e) + pd.Timedelta(days=b)].max())
R["ap_pre_max"] = R["event"].map(lambda e: _apmax(e, -14, -3))
R["ap_placebo_max"] = R["event"].map(lambda e: _apmax(e, -30, -11))
R["band"] = pd.cut(R["alt0"], [250, 350, 450, 550, 700],
                   labels=["250–350 km", "350–450 km", "450–550 km", "550–700 km"])

# Oran ancak belirgin alçalan objelerde anlamlı (beklenen ≥ 35 m/hafta, ≥ 5 m/gün)
ok = R[(R["expected_m"] >= 35) & (R["loss_m"] > 0)].copy()
ok["ratio"] = ok["loss_m"] / ok["expected_m"]
ok["lost_days"] = (ok["loss_m"] - ok["expected_m"]) / (-ok["slope_m_day"])
okp = ok[(ok["pl_expected_m"] >= 35) & (ok["pl_loss_m"] > 0)].copy()
okp["pl_ratio"] = okp["pl_loss_m"] / okp["pl_expected_m"]

# ---- Pencere düzeyi veri seti
# Aynı haftadaki objeler birlikte dalgalanır (atmosfer yoğunluğu her hafta değişir), bu yüzden
# bağımsız birim obje değil PENCEREdir. Her olay için iki pencere: fırtına ve plasebo; her biri
# için ortanca oran ile o penceredeki Ap ve F10.7 artışı (ön pencereye göre).
WIN = {"storm": ((-2, 4), (-14, -3)), "placebo": ((-18, -12), (-30, -19))}
B3 = ["250–450 km", "450–550 km", "550–700 km"]
ok["band3"] = pd.cut(ok["alt0"], [250, 450, 550, 700], labels=B3)
okp["band3"] = pd.cut(okp["alt0"], [250, 450, 550, 700], labels=B3)


def kmean(e, a, b, col):
    t = pd.Timestamp(e)
    return float(kp[col].loc[t + pd.Timedelta(days=a): t + pd.Timedelta(days=b)].mean())


win = []
for ev in sorted(ok["event"].unique()):
    for kind, src, col in [("storm", ok, "ratio"), ("placebo", okp, "pl_ratio")]:
        (w0, w1), (p0, p1) = WIN[kind]
        d_ap = kmean(ev, w0, w1, "Ap") - kmean(ev, p0, p1, "Ap")
        d_f = kmean(ev, w0, w1, "F107") - kmean(ev, p0, p1, "F107")
        g = src[src["event"] == ev]
        for band, gb in [("Tümü", g)] + [(b, g[g["band3"] == b]) for b in B3]:
            if len(gb) >= 15:
                win.append({"event": ev, "kind": kind, "band": band, "n": int(len(gb)),
                            "ratio": float(gb[col].median()), "d_ap": d_ap, "d_f107": d_f,
                            "lost_days": float(gb["lost_days"].median()) if kind == "storm" else None})
W = pd.DataFrame(win)


def fit(d):
    X = np.column_stack([np.ones(len(d)), d["d_ap"] / 10, d["d_f107"] / 10])
    y = np.log(d["ratio"])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r2 = 1 - ((y - X @ b) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return b, r2


coef, grid = [], []
for band in ["Tümü"] + B3:
    d = W[W["band"] == band]
    if d["event"].nunique() < 10:          # bu bantta yeterli pencere yok
        continue
    b, r2 = fit(d)
    evs = d["event"].unique()
    grp = {e: d[d["event"] == e] for e in evs}
    boot = np.array([fit(pd.concat([grp[e] for e in RNG.choice(evs, len(evs))]))[0] for _ in range(2000)])
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    pct = lambda v: 100 * (np.exp(v) - 1)
    coef.append({"band": band, "n_windows": int(len(d)), "n_events": int(len(evs)), "r2": round(float(r2), 3),
                 "ap_pct": pct(b[1]), "ap_pct_lo": pct(lo[1]), "ap_pct_hi": pct(hi[1]),
                 "f107_pct": pct(b[2]), "f107_pct_lo": pct(lo[2]), "f107_pct_hi": pct(hi[2])})
    for dap in range(0, 65, 5):
        pb = np.exp(boot[:, 0] + boot[:, 1] * dap / 10)
        grid.append({"band": band, "d_ap": dap, "ratio": float(np.exp(b[0] + b[1] * dap / 10)),
                     "lo": float(np.percentile(pb, 2.5)), "hi": float(np.percentile(pb, 97.5))})

# ---- Fırtına vs plasebo, olay düzeyinde eşleştirilmiş test
T = W[W["band"] == "Tümü"].pivot(index="event", columns="kind", values="ratio").dropna()
w_stat, w_p = stats.wilcoxon(np.log(T["storm"]), np.log(T["placebo"]))
n_higher = int((T["storm"] > T["placebo"]).sum())
rho, rho_p = stats.spearmanr(W.loc[W["band"] == "Tümü", "d_ap"], W.loc[W["band"] == "Tümü", "ratio"])

# ---- Olay tablosu
st = W[(W["band"] == "Tümü") & (W["kind"] == "storm")].set_index("event")
pl = W[(W["band"] == "Tümü") & (W["kind"] == "placebo")].set_index("event")["ratio"]
EV = pd.DataFrame({"event": st.index, "ap_peak": [plan[e]["ap_peak"] for e in st.index],
                   "d_ap": st["d_ap"].round(1).values, "d_f107": st["d_f107"].round(1).values,
                   "n": st["n"].values, "ratio": st["ratio"].round(3).values,
                   "placebo_ratio": [round(float(pl[e]), 3) if e in pl.index else None for e in st.index],
                   "lost_days": st["lost_days"].round(2).values})

# ---- Üst üste bindirme eğrileri (fırtına gücüne göre ortanca)
C = pd.DataFrame(curves)
curve_rows = []
if len(C):
    C["strength"] = pd.cut(C["event"].map(lambda e: plan[e]["ap_peak"]), [0, 80, 130, 400],
                           labels=["Orta (Ap 50–80)", "Güçlü (Ap 80–130)", "Şiddetli (Ap > 130)"])
    for s_, g in C.groupby("strength", observed=True):
        med = np.nanmedian(np.array(g["res"].tolist(), dtype=float), axis=0)
        for d, v in zip(range(-10, 21), med):
            curve_rows.append({"strength": str(s_), "day": d, "lost_days": float(v), "n": int(len(g)),
                               "n_events": int(g["event"].nunique())})

res = {"n_objects": int(len(ok)), "n_events": int(ok["event"].nunique()), "coef": coef,
       "paired": {"n_events": int(len(T)), "storm_median": float(T["storm"].median()),
                  "placebo_median": float(T["placebo"].median()), "n_higher": n_higher, "wilcoxon_p": float(w_p)},
       "spearman": {"rho": float(rho), "p": float(rho_p)}, "events": EV.to_dict("records")}
(HERE / "results_alt.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

# ---- Rapor dosyaları (ham yörünge kaydı yok; yalnızca türetilmiş özetler)
DASH = HERE / "dash_data"
DASH.mkdir(exist_ok=True)
META = [{"label": "altitude.py", "value": (HERE / "altitude.py").read_text(encoding="utf-8"), "type": "code", "lang": "python"},
        {"label": "st_plan.py", "value": (HERE / "st_plan.py").read_text(encoding="utf-8"), "type": "code", "lang": "python"},
        {"label": "Girdi", "value": "Space-Track.org GP history (NORAD_CAT_ID, EPOCH, MEAN_MOTION, ECCENTRICITY), "
                                    "64 fırtına penceresi (2000–2026); GCAT; GFZ Kp/Ap/F10.7. Ham yörünge kayıtları paylaşılmaz."}]


def _c(v):
    if isinstance(v, (float, np.floating)):
        return None if np.isnan(v) else float(f"{float(v):.6g}")
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def dump(name, rows_):
    rows_ = [{k: _c(v) for k, v in r.items()} for r in rows_]
    (DASH / f"{name}.json").write_text(json.dumps({"rows": rows_, "meta": META}, ensure_ascii=False, allow_nan=False),
                                       encoding="utf-8")


ev_idx = EV.set_index("event")
c0 = coef[0]
dump("alt_summary", [{
    "n_objects": res["n_objects"], "n_events": res["n_events"],
    "storm_median": res["paired"]["storm_median"], "placebo_median": res["paired"]["placebo_median"],
    "n_higher": n_higher, "n_paired": int(len(T)), "wilcoxon_p": float(w_p),
    "ap_pct": c0["ap_pct"], "ap_pct_lo": c0["ap_pct_lo"], "ap_pct_hi": c0["ap_pct_hi"],
    "f107_pct": c0["f107_pct"], "f107_pct_lo": c0["f107_pct_lo"], "f107_pct_hi": c0["f107_pct_hi"], "r2": c0["r2"],
    "may24_lost_days": float(ev_idx.loc["2024-05-11", "lost_days"]), "may24_ratio": float(ev_idx.loc["2024-05-11", "ratio"]),
    "may24_n": int(ev_idx.loc["2024-05-11", "n"]),
    "hw03_lost_days": float(ev_idx.loc["2003-10-29", "lost_days"]), "hw03_ratio": float(ev_idx.loc["2003-10-29", "ratio"]),
}])
dump("alt_windows", W[W["band"] == "Tümü"].drop(columns=["band"]).to_dict("records"))
dump("alt_coef", coef)
dump("alt_grid", grid)
dump("alt_events", EV.sort_values("ap_peak", ascending=False).to_dict("records"))
dump("alt_curves", curve_rows)

print(f"Oran hesaplanan obje-fırtına: {len(ok):,} ({res['n_events']} fırtına), pencere satırı: {len(W)}")
pr = res["paired"]
print(f"Olay düzeyinde: fırtına ortancası {pr['storm_median']:.3f} vs plasebo {pr['placebo_median']:.3f}; "
      f"{n_higher}/{len(T)} olayda fırtına > plasebo; Wilcoxon p={w_p:.2e}; Spearman(ΔAp, oran)={rho:.2f} p={rho_p:.1e}")
for c in coef:
    print(f"  {c['band']:11s} n={c['n_windows']:3d} R²={c['r2']:.2f}  +10 Ap: %{c['ap_pct']:.1f} "
          f"[{c['ap_pct_lo']:.1f}, {c['ap_pct_hi']:.1f}]   +10 sfu: %{c['f107_pct']:.1f} [{c['f107_pct_lo']:.1f}, {c['f107_pct_hi']:.1f}]")
print(EV.sort_values("ap_peak", ascending=False).head(8).to_string(index=False))
for s_ in sorted({r["strength"] for r in curve_rows}):
    v = {r["day"]: r["lost_days"] for r in curve_rows if r["strength"] == s_}
    print(f"  eğri {s_}: -5:{v[-5]:.2f}  0:{v[0]:.2f}  +3:{v[3]:.2f}  +7:{v[7]:.2f}  +14:{v[14]:.2f}")
