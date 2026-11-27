"""Sunumun gömülü verisini analiz çıktılarından derler ve sunumu tek bir HTML dosyası olarak üretir.

Girdi : ../dash_data/*.json (analysis.py ve altitude.py çıktıları), ../data/kp.txt
Çıktı : index.html  (template.html içindeki /*__DATA__*/ yerine veri yazılır)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from load import load_kp  # noqa: E402


def rows(name):
    return json.loads((ROOT / "dash_data" / f"{name}.json").read_text(encoding="utf-8"))["rows"]


kp = load_kp()


def daily(a, b):
    d = kp.loc[a:b]
    return [{"d": str(i.date()), "ap": int(r.Ap), "kp": round(float(r.Kp_max), 2), "f": round(float(r.F107), 1)}
            for i, r in d.iterrows()]


s0, sa = rows("summary")[0], rows("alt_summary")[0]
data = {
    "yearly": [{"y": r["year"], "rate": round(r["rate_pct"], 3), "f": r["f107"], "n": r["reentries"]} for r in rows("yearly")],
    "may24": daily("2024-04-27", "2024-05-25"),
    "feb22": daily("2022-01-27", "2022-02-16"),
    "curves": rows("alt_curves"),
    "windows": [{"e": r["event"], "k": r["kind"], "x": round(r["d_ap"], 2), "y": round(r["ratio"], 4),
                 "f": round(r["d_f107"], 1), "n": r["n"]} for r in rows("alt_windows")],
    "coef": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in rows("alt_coef")],
    "grid": [{"x": r["d_ap"], "y": round(r["ratio"], 4), "lo": round(r["lo"], 4), "hi": round(r["hi"], 4)}
             for r in rows("alt_grid") if r["band"] == "Tümü"],
    "grid_bands": {b: [{"x": r["d_ap"], "y": round(r["ratio"], 4), "lo": round(r["lo"], 4), "hi": round(r["hi"], 4)}
                       for r in rows("alt_grid") if r["band"] == b]
                   for b in ["250–450 km", "450–550 km", "550–700 km"]},
    "events": rows("alt_events")[:8],
    # Ayrıntı paneli için ek özetler
    "arch": [{"e": r["event"], "ap": r["ap_peak"], "dap": r["d_ap"], "df": r["d_f107"], "n": r["n"],
              "r": r["ratio"], "pr": r["placebo_ratio"], "ld": r["lost_days"]} for r in rows("alt_events")],
    "top": rows("top_storms"),
    "dose_re": rows("dose"),
    "sl_kp": rows("starlink_kp"),
    "epoch_peak": max(rows("epoch"), key=lambda r: r["observed"]),
    "gscale": {g: round(float((kp.loc["1957":"2025"].Kp_max >= g - 0.34).sum()
                              / ((kp.loc["1957":"2025"].index.max() - kp.loc["1957":"2025"].index.min()).days / 365.25)), 1)
               for g in [5, 6, 7, 8, 9]},
    "hist": {d: {"ap": int(kp.loc[d].Ap), "kp": round(float(kp.loc[d].Kp_max), 2), "f": round(float(kp.loc[d].F107), 1)}
             for d in ["1960-11-13", "1989-03-13", "2003-10-29", "2015-03-17", "2022-02-03", "2024-05-11", "2024-10-10"]},
    "kp_range": [str(kp.index.min().date()), str(kp.index.max().date())],
    "sum": {
        "cycle_ratio": s0["max_vs_min_ratio"], "spearman": s0["spearman_r"], "f_lo": s0["f107_lo"], "f_hi": s0["f107_hi"],
        "reentries": s0["n_uncontrolled_reentries"], "storm_excess": s0["excess_pct"], "storm_p": s0["p_value"],
        "n_storms_reentry": s0["n_storms"],
        "sl_storm_pct": s0["sl_storm_pct"], "sl_calm_pct": s0["sl_calm_pct"], "sl_wo_pct": s0["sl_storm_wo_pct"],
        "sl_launches": s0["sl_launches"], "sl_sats": s0["sl_sats"],
        "pearson": s0["pearson_r"], "storm_ci_lo": s0["ci_lo_pct"], "storm_ci_hi": s0["ci_hi_pct"],
        "sl_fisher_p": s0["sl_fisher_p"], "sl_odds": s0["sl_odds"], "sl_storm_lost": s0["sl_storm_lost"],
        "sl_storm_sats": s0["sl_storm_sats"], "sl_calm_lost": s0["sl_calm_lost"], "sl_calm_sats": s0["sl_calm_sats"],
        "f107_pct_lo": sa["f107_pct_lo"], "f107_pct_hi": sa["f107_pct_hi"], "storm_median": sa["storm_median"],
        "feb22_lost": 38, "feb22_n": 49, "feb22_perigee": 209, "feb22_kp": 5.3,
        **{k: sa[k] for k in ["n_objects", "n_events", "storm_median", "placebo_median", "n_higher", "n_paired",
                              "wilcoxon_p", "ap_pct", "ap_pct_lo", "ap_pct_hi", "f107_pct", "r2",
                              "may24_lost_days", "may24_ratio", "may24_n", "hw03_lost_days", "hw03_ratio"]},
    },
}
# Şubat 2022 sabitlerini veriden doğrula
sl = rows("starlink_launches")
f = next(r for r in sl if r["tag"] == "2022-010")
assert (f["lost30"], f["n"], round(f["perigee_med"]), round(f["kp_max7"], 1)) == (38, 49, 209, 5.3), f

js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
tpl = (HERE / "template.html").read_text(encoding="utf-8")
out = tpl.replace("/*__DATA__*/null", js)
(HERE / "index.html").write_text(out, encoding="utf-8")
# Yerel test: yayın iskeletinin (doctype, head, body) eşdeğeriyle sarılmış kopya
wrap = ('<!doctype html><html lang="tr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        '<style>:root{color-scheme:light}body{margin:0;font:14px system-ui}[hidden]{display:none!important}</style>'
        '</head><body>' + out + '</body></html>')
(HERE / "preview.html").write_text(wrap, encoding="utf-8")
print(f"veri {len(js)/1024:.1f} KB, index.html {len(out)/1024:.1f} KB")
