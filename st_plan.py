"""Space-Track'ten indirilecek pencereleri seçer -> data/st_plan.json

Her fırtına için: fırtınadan 35 gün önce ile 25 gün sonrası arasında yörüngede olan,
GCAT'e göre alçak ve yaklaşık dairesel yörüngedeki kontrolsüz objelerden (enkaz,
roket gövdesi, parça) rastgele en fazla 400 tanesi.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from load import load_satcat, load_kp

PRE, POST, MAX_OBJ = 35, 25, 400
EXTRA = ["2022-02-03"]                    # Starlink kaybının yaşandığı orta şiddetli fırtına
rng = np.random.default_rng(7)

kp = load_kp()
sat = load_satcat()
sat["t0"] = sat["SDate_t"].fillna(sat["LDate_t"])
ap = kp["Ap"].loc["2000-01-01":"2026-10-25"]   # +25 gün penceresi bugüne kadar dolmalı

# Tepe günleri: en güçlüden başlayarak, seçilmiş bir tepeye 30 günden yakın olanları atla.
# 0. gün = tepe günü. Ön pencerede başka fırtına olup olmadığı 'ap_pre_max' ile kaydedilir.
events = []
for t, v in ap[ap >= 50].sort_values(ascending=False).items():
    if all(abs((t - u).days) > 30 for u in events):
        events.append(t)
events = sorted(set(events) | {pd.Timestamp(d) for d in EXTRA})

unc = sat[sat["kind"].isin(["D", "R", "C"]) & (sat["source"] == "satcat")].copy()
unc["norad"] = pd.to_numeric(unc["Satcat"], errors="coerce")
unc = unc.dropna(subset=["norad"])

plan = []
for t in events:
    a, b = t - pd.Timedelta(days=PRE), t + pd.Timedelta(days=POST)
    c = unc[(unc["t0"] < a - pd.Timedelta(days=5)) &
            (unc["DDate_t"].isna() | (unc["DDate_t"] > b)) &
            (unc["Apogee"] < 700) & (unc["Perigee"] > 200)]
    ids = sorted(int(x) for x in rng.choice(c["norad"].to_numpy(), min(MAX_OBJ, len(c)), replace=False))
    w = kp.loc[t - pd.Timedelta(days=1): t + pd.Timedelta(days=1)]
    pre = kp.loc[a: t - pd.Timedelta(days=3)]
    plan.append({"event": str(t.date()), "start": str(a.date()), "end": str(b.date()),
                 "ap_peak": int(kp.loc[t, "Ap"]), "ap_sum3": int(w["Ap"].sum()),
                 "kp_peak": float(w["Kp_max"].max()), "ap_pre_max": int(pre["Ap"].max()),
                 "ids": ids})

out = Path(__file__).parent / "data" / "st_plan.json"
out.write_text(json.dumps(plan, indent=0), encoding="utf-8")
print(f"{len(plan)} pencere, toplam {sum(len(p['ids']) for p in plan)} obje-pencere -> {out.name}")
print("En güçlü 5:", sorted(((p["ap_peak"], p["event"]) for p in plan), reverse=True)[:5])
