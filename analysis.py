"""Güneş fırtınaları ve uydu yeniden girişleri — ana analiz.

Çalıştır:  python analysis.py      ->  results.json (rapor sayfası bu dosyayı kullanır)

Üç soru:
  A) Güneş döngüsü: Güneş aktif olduğunda (yüksek F10.7) yörüngedeki objelerin
     yıllık düşme oranı artıyor mu?
  B) Fırtına etkisi: Büyük jeomanyetik fırtınadan sonraki günlerde yeniden
     girişler artıyor mu? (süperpoze dönem analizi + rastgele tarih testi)
  C) Starlink: Fırlatmadan hemen sonra gelen fırtına, uyduların erken kaybını
     açıklıyor mu?
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from load import load_satcat, load_kp

OUT = Path(__file__).parent / "results.json"
RNG = np.random.default_rng(42)
START, END = pd.Timestamp("1965-01-01"), pd.Timestamp("2026-11-25")

sat = load_satcat()
kp = load_kp()
sat["t0"] = sat["SDate_t"].fillna(sat["LDate_t"])

# Kontrolsüz objeler: enkaz (D), roket gövdesi (R), parça (C). Motor yok, manevra yok,
# yani düşüş zamanlarını yalnızca atmosfer belirliyor -> temiz fiziksel sinyal.
unc = sat[sat["kind"].isin(["D", "R", "C"])].copy()
unc_leo = unc[(unc["Apogee"] < 2000) | unc["DDate_t"].notna()]

days = pd.date_range(START, END)
reentry_daily = (unc_leo.dropna(subset=["DDate_t"])
                 .groupby("DDate_t").size().reindex(days, fill_value=0))
ap = kp["Ap"].reindex(days)
f107 = kp["F107"].reindex(days)
f107_81 = f107.rolling(81, center=True, min_periods=40).mean()

res = {"meta": {
    "start": str(START.date()), "end": str(END.date()),
    "n_objects": int(len(sat)),
    "n_uncontrolled_reentries": int(reentry_daily.sum()),
    "catalog_updated": "2026-11-26",
}}

# ---------------------------------------------------------------- A) Güneş döngüsü
years = range(1966, 2026)
rows = []
for y in years:
    t0, t1 = pd.Timestamp(y, 1, 1), pd.Timestamp(y + 1, 1, 1)
    alive = unc_leo[(unc_leo["t0"] < t0) &
                    (unc_leo["DDate_t"].isna() | (unc_leo["DDate_t"] >= t0))]
    pop = len(alive)
    dec = int(((alive["DDate_t"] >= t0) & (alive["DDate_t"] < t1)).sum())
    rows.append({"year": y, "pop": pop, "reentries": dec,
                 "rate_pct": 100 * dec / pop if pop else None,
                 "f107": round(float(f107.loc[str(y)].mean()), 1),
                 "ap": round(float(ap.loc[str(y)].mean()), 1)})
yr = pd.DataFrame(rows)
r_p, p_p = stats.pearsonr(yr["f107"], yr["rate_pct"])
r_s, p_s = stats.spearmanr(yr["f107"], yr["rate_pct"])
slope, intercept, *_ = stats.linregress(yr["f107"], yr["rate_pct"])
lo, hi = yr["f107"].quantile([0.1, 0.9])
res["cycle"] = {
    "yearly": yr.to_dict("records"),
    "pearson_r": round(r_p, 3), "pearson_p": float(p_p),
    "spearman_r": round(r_s, 3), "spearman_p": float(p_s),
    "slope": slope, "intercept": intercept,
    # Güneş minimumuna (F10.7 ~ %10'luk dilim) göre maksimumda kaç kat
    "max_vs_min_ratio": round((intercept + slope * hi) / (intercept + slope * lo), 2),
    "f107_lo": round(lo, 0), "f107_hi": round(hi, 0),
}

# ---------------------------------------------------------------- B) Fırtına etkisi
W = np.arange(-30, 61)
BASE = (W >= -30) & (W <= -1)
RESP = (W >= 0) & (W <= 14)


def decluster(series, thr, gap=30):
    ev, last = [], None
    for t in series[series >= thr].index:
        if last is None or (t - last).days > gap:
            ev.append(t)
        last = t
    return ev


def epoch_matrix(epochs):
    m = []
    for t in epochs:
        idx = t + pd.to_timedelta(W, "D")
        if idx[0] < days[0] or idx[-1] > days[-1]:
            continue
        c = reentry_daily.reindex(idx).to_numpy(float)
        base = c[BASE].mean()
        if base > 0:
            m.append(c / base)
    return np.array(m)


def stat(mat):
    return float(mat[:, RESP].mean())  # fırtına sonrası 0-14 gün / öncesi ortalama oranı


def null_distribution(epochs, n_iter=2000):
    """Her fırtınayı, aynı güneş aktivitesi düzeyinde (81 günlük F10.7 ±15 sfu)
    sakin bir rastgele günle değiştirir. Böylece 'güneş zaten aktifti' etkisi
    ayıklanır; geriye yalnızca fırtınanın kendisi kalır."""
    quiet = ap.rolling(21, center=True, min_periods=1).max() < 40
    cand = f107_81[quiet & f107_81.notna()]
    cand = cand[(cand.index >= days[0] + pd.Timedelta(days=31)) &
                (cand.index <= days[-1] - pd.Timedelta(days=61))]
    pools = [cand.index[(cand - f107_81.loc[t]).abs() <= 15] for t in epochs]
    out, curves = [], []
    for _ in range(n_iter):
        pick = [p[RNG.integers(len(p))] for p in pools if len(p)]
        m = epoch_matrix(pick)
        out.append(stat(m))
        curves.append(m.mean(0))
    return np.array(out), np.array(curves)


storms = [t for t in decluster(ap, 100) if t >= START + pd.Timedelta(days=31)]
mat = epoch_matrix(storms)
obs = stat(mat)
null, null_curves = null_distribution(storms)
p_val = float((null >= obs).mean())
boot = np.array([stat(mat[RNG.integers(len(mat), size=len(mat))]) for _ in range(2000)])

# 7 günlük yürüyen ortalama ile düzleştirilmiş eğri (günlük gürültü çok yüksek)
def smooth(v, k=7):
    return pd.Series(v).rolling(k, center=True, min_periods=1).mean().to_numpy()

res["epoch"] = {
    "threshold_ap": 100, "n_storms": int(len(mat)),
    "storm_dates": [str(t.date()) for t in storms],
    "lag": W.tolist(),
    "curve": np.round(smooth(mat.mean(0)), 4).tolist(),
    "null_lo": np.round(smooth(np.percentile(null_curves, 5, axis=0)), 4).tolist(),
    "null_hi": np.round(smooth(np.percentile(null_curves, 95, axis=0)), 4).tolist(),
    "null_mid": np.round(smooth(np.median(null_curves, axis=0)), 4).tolist(),
    "observed_ratio": round(obs, 4),
    "null_median": round(float(np.median(null)), 4),
    "excess_pct": round(100 * (obs - np.median(null)), 1),
    "ci95": [round(float(x), 4) for x in np.percentile(boot, [2.5, 97.5])],
    "p_value": p_val,
}

# Doz-yanıt: fırtına ne kadar güçlüyse etki o kadar büyük mü?
dose = []
for lo_, hi_ in [(30, 50), (50, 80), (80, 120), (120, 400)]:
    peak = ap.where((ap >= lo_) & (ap < hi_))
    ev = [t for t in decluster(peak.dropna(), lo_) if t >= START + pd.Timedelta(days=31)]
    # daha güçlü bir fırtınayla karışmasın: ±30 günde üst eşiği aşan gün olmasın
    ev = [t for t in ev if ap.loc[t - pd.Timedelta(days=30): t + pd.Timedelta(days=30)].max() < hi_]
    m = epoch_matrix(ev)
    if len(m) < 5:
        continue
    nl, _ = null_distribution(ev, n_iter=500)
    b = np.array([stat(m[RNG.integers(len(m), size=len(m))]) for _ in range(1000)])
    dose.append({"label": f"Ap {lo_}–{hi_ if hi_ < 400 else '+'}", "n": int(len(m)),
                 "excess_pct": round(100 * (stat(m) - np.median(nl)), 1),
                 "ci_lo": round(100 * (np.percentile(b, 2.5) - np.median(nl)), 1),
                 "ci_hi": round(100 * (np.percentile(b, 97.5) - np.median(nl)), 1),
                 "p_value": float((nl >= stat(m)).mean())})
res["dose"] = dose

# En güçlü fırtınalar ve sonrasındaki 14 günde düşen obje sayısı
top = []
for t in ap.sort_values(ascending=False).index:
    if any(abs((t - u["t"]).days) < 30 for u in top):
        continue
    after = int(reentry_daily.loc[t: t + pd.Timedelta(days=13)].sum())
    before = reentry_daily.loc[t - pd.Timedelta(days=30): t - pd.Timedelta(days=1)].mean() * 14
    top.append({"t": t, "date": str(t.date()), "ap": int(ap.loc[t]),
                "kp_max": round(float(kp.loc[t, "Kp_max"]), 1),
                "after14": after, "expected14": round(float(before), 1)})
    if len(top) == 10:
        break
for u in top:
    u.pop("t")
res["top_storms"] = top

# ---------------------------------------------------------------- C) Starlink
sl = sat[sat["is_starlink"] & (sat["kind"] == "P")].copy()
sl["life_days"] = (sl["DDate_t"] - sl["LDate_t"]).dt.days
launches = []
for tag, g in sl.groupby("Launch_Tag"):
    t = g["LDate_t"].min()
    if pd.isna(t) or t < pd.Timestamp("2019-05-01") or t > END - pd.Timedelta(days=30):
        continue
    w = kp.loc[t: t + pd.Timedelta(days=6)]
    launches.append({
        "tag": tag, "date": str(t.date()), "n": int(len(g)),
        "lost30": int((g["life_days"] <= 30).sum()),
        "ap_max7": int(w["Ap"].max()), "kp_max7": round(float(w["Kp_max"].max()), 1),
        "perigee_med": float(g["Perigee"].median()),
    })
L = pd.DataFrame(launches)
# Yörüngeye ulaşmayan/suborbital uçuşlar (GCAT 'U' etiketleri, perige < 150 km) ve
# Temmuz 2024 Falcon 9 üst kademe arızası (2024-129) fırtınayla ilgisiz: çıkar.
L = L[~L["tag"].str.contains("U") & (L["perigee_med"] > 150) & (L["tag"] != "2024-129")].copy()
L["lost_frac"] = L["lost30"] / L["n"]
L["low_deploy"] = L["perigee_med"] < 250
r_l, p_l = stats.spearmanr(L["ap_max7"], L["lost_frac"])
# Fırlatma sonrası ilk hafta en yüksek Kp'ye göre gruplar
L["kp_bin"] = pd.cut(L["kp_max7"], [-1, 3.99, 4.99, 9.1], labels=["Kp < 4", "Kp 4–5", "Kp ≥ 5"])
kb = (L.groupby(["low_deploy", "kp_bin"], observed=True)
      .agg(launches=("n", "size"), sats=("n", "sum"), lost=("lost30", "sum")).reset_index())
kb["lost_pct"] = (100 * kb["lost"] / kb["sats"]).round(2)
# Fisher testi: alçak bırakılan fırlatmalarda Kp≥5 vs Kp<5 kayıp oranı
low = L[L["low_deploy"]]
a = low[low["kp_max7"] >= 5][["lost30", "n"]].sum()
b = low[low["kp_max7"] < 5][["lost30", "n"]].sum()
odds, p_f = stats.fisher_exact([[a.lost30, a.n - a.lost30], [b.lost30, b.n - b.lost30]])
a_nf = low[(low["kp_max7"] >= 5) & (low["tag"] != "2022-010")][["lost30", "n"]].sum()
res["starlink"] = {
    "kp_bins": kb.astype({"kp_bin": str}).to_dict("records"),
    "fisher_low": {"storm_lost": int(a.lost30), "storm_sats": int(a.n),
                   "calm_lost": int(b.lost30), "calm_sats": int(b.n),
                   "odds_ratio": float(odds), "p": float(p_f),
                   "storm_lost_wo_feb22": int(a_nf.lost30), "storm_sats_wo_feb22": int(a_nf.n)},
    "n_launches": int(len(L)), "n_sats": int(L["n"].sum()),
    "launches": L.sort_values("date").to_dict("records"),
    "spearman_r": round(r_l, 3), "spearman_p": float(p_l),
    "lost_total": int(L["lost30"].sum()),
    "worst": L.sort_values("lost30", ascending=False).head(5).to_dict("records"),
}

# Starlink yıllık yeniden girişler (kontrollü + kontrolsüz) ve aktif filo büyüklüğü
sl_yr = (sl.dropna(subset=["DDate_t"]).groupby(sl["DDate_t"].dt.year).size())
res["starlink"]["reentries_by_year"] = {int(k): int(v) for k, v in sl_yr.items()}

# Günlük seri: rapordaki zaman çizelgesi için aylık özet
monthly = pd.DataFrame({"reentries": reentry_daily, "ap": ap, "f107": f107}).resample("MS").agg(
    {"reentries": "sum", "ap": "mean", "f107": "mean"})
res["monthly"] = [{"m": str(i.date())[:7], "reentries": int(r.reentries),
                   "ap": round(float(r.ap), 1),
                   "f107": None if pd.isna(r.f107) else round(float(r.f107), 1)}
                  for i, r in monthly.iterrows()]

OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

# ---------------------------------------------------------------- Rapor sayfası için veri dosyaları
# Her dosya {rows, meta}; meta, sayıları üreten kodun kendisini taşır (yeniden çalıştırılabilsin).
DASH = Path(__file__).parent / "dash_data"
DASH.mkdir(exist_ok=True)
_here = Path(__file__).parent
META = [
    {"label": "analysis.py", "value": (_here / "analysis.py").read_text(encoding="utf-8"),
     "type": "code", "lang": "python"},
    {"label": "load.py", "value": (_here / "load.py").read_text(encoding="utf-8"),
     "type": "code", "lang": "python"},
    {"label": "Girdi", "value": "GCAT satcat.tsv + auxcat.tsv (planet4589.org, 2026-11-26); "
                                "GFZ Kp_ap_Ap_SN_F107_since_1932.txt (kp.gfz-potsdam.de, 2026-11-25'e kadar)"},
]


def _clean(v):
    if isinstance(v, (np.floating, float)):
        return None if np.isnan(v) else float(f"{float(v):.6g}")
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def dump(name, rows):
    rows = [{k: _clean(v) for k, v in r.items()} for r in rows]
    (DASH / f"{name}.json").write_text(
        json.dumps({"rows": rows, "meta": META}, ensure_ascii=False, allow_nan=False), encoding="utf-8")


fl = res["starlink"]["fisher_low"]
dump("summary", [{
    "max_vs_min_ratio": c_["max_vs_min_ratio"], "spearman_r": c_["spearman_r"],
    "pearson_r": c_["pearson_r"], "f107_lo": c_["f107_lo"], "f107_hi": c_["f107_hi"],
    "n_storms": e_["n_storms"], "excess_pct": e_["excess_pct"],
    "ci_lo_pct": round(100 * (e_["ci95"][0] - e_["null_median"]), 1),
    "ci_hi_pct": round(100 * (e_["ci95"][1] - e_["null_median"]), 1),
    "p_value": round(e_["p_value"], 3),
    "n_uncontrolled_reentries": res["meta"]["n_uncontrolled_reentries"],
    "sl_launches": res["starlink"]["n_launches"], "sl_sats": res["starlink"]["n_sats"],
    "sl_storm_lost": fl["storm_lost"], "sl_storm_sats": fl["storm_sats"],
    "sl_calm_lost": fl["calm_lost"], "sl_calm_sats": fl["calm_sats"],
    "sl_storm_pct": round(100 * fl["storm_lost"] / fl["storm_sats"], 2),
    "sl_calm_pct": round(100 * fl["calm_lost"] / fl["calm_sats"], 2),
    "sl_fisher_p": fl["p"], "sl_odds": round(fl["odds_ratio"], 1),
    "sl_storm_wo_lost": fl["storm_lost_wo_feb22"], "sl_storm_wo_sats": fl["storm_sats_wo_feb22"],
    "sl_storm_wo_pct": round(100 * fl["storm_lost_wo_feb22"] / fl["storm_sats_wo_feb22"], 2),
}] if (c_ := res["cycle"]) and (e_ := res["epoch"]) else [])
dump("yearly", res["cycle"]["yearly"])
dump("epoch", [{"lag": l, "observed": o, "null_lo": a, "null_mid": m, "null_hi": b}
               for l, o, a, m, b in zip(e_["lag"], e_["curve"], e_["null_lo"], e_["null_mid"], e_["null_hi"])])
dump("dose", res["dose"])
dump("top_storms", res["top_storms"])
dump("starlink_launches", [
    {k: r[k] for k in ["tag", "date", "n", "lost30", "ap_max7", "kp_max7", "perigee_med", "low_deploy"]}
    for r in res["starlink"]["launches"]])
dump("starlink_kp", [{"group": "Alçak bırakma (<250 km)" if r["low_deploy"] else "Normal bırakma",
                      "kp_bin": r["kp_bin"], "launches": r["launches"], "sats": r["sats"],
                      "lost": r["lost"], "lost_pct": r["lost_pct"]}
                     for r in res["starlink"]["kp_bins"]])

# ---------------------------------------------------------------- Konsol özeti
c, e = res["cycle"], res["epoch"]
print(f"[A] Yıllık düşme oranı ~ F10.7: Pearson r={c['pearson_r']} (p={c['pearson_p']:.1e}), "
      f"Spearman r={c['spearman_r']};  maksimum/minimum ≈ {c['max_vs_min_ratio']}x")
print(f"[B] {e['n_storms']} fırtına (Ap≥100): 0-14 gün oranı {e['observed_ratio']} vs rastgele "
      f"{e['null_median']}  -> fazla %{e['excess_pct']}, %95 GA {e['ci95']}, p={e['p_value']:.4f}")
for d in dose:
    print(f"    {d['label']:12s} n={d['n']:3d}  fazla %{d['excess_pct']:5.1f}  "
          f"[{d['ci_lo']}, {d['ci_hi']}]  p={d['p_value']:.3f}")
print("    En güçlü fırtınalar:")
for u in top:
    print(f"      {u['date']}  Ap={u['ap']:3d}  sonraki 14 gün: {u['after14']:3d} (beklenen {u['expected14']})")
s = res["starlink"]
print(f"[C] {s['n_launches']} Starlink fırlatması, {s['n_sats']} uydu; 30 günde kayıp {s['lost_total']}; "
      f"Spearman(maks Ap ilk 7 gün, kayıp oranı) r={s['spearman_r']} p={s['spearman_p']:.3f}")
for w in s["worst"]:
    print(f"      {w['date']} {w['tag']}: {w['lost30']}/{w['n']} kayıp, ilk 7 gün maks Ap={w['ap_max7']}, "
          f"Kp={w['kp_max7']}, perige medyan {w['perigee_med']} km")
for k_ in s["kp_bins"]:
    print("    ", k_)
print("    Fisher (alçak bırakma, Kp≥5 vs <5):", s["fisher_low"])
print("    Starlink yeniden girişleri/yıl:", s["reentries_by_year"])
