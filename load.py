"""Ham verileri okuyup temiz tablolara çeviren yardımcılar.

- GCAT satcat.tsv  (Jonathan McDowell, planet4589.org)  -> uydu/obje kataloğu
- GFZ Kp_ap_Ap_SN_F107_since_1932.txt                   -> günlük jeomanyetik ve güneş indeksleri
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"

_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
_DATE_RE = re.compile(r"^\s*(\d{4})\s+([A-Z][a-z]{2})?\s*(\d{1,2})?")


def parse_gcat_date(s: str):
    """'1957 Dec  1 1000?' -> Timestamp(1957-12-01). Ay/gün yoksa NaT (belirsiz)."""
    if not isinstance(s, str) or s.strip() in ("", "-", "*"):
        return pd.NaT
    m = _DATE_RE.match(s)
    if not m or not m.group(2) or not m.group(3):
        return pd.NaT
    try:
        return pd.Timestamp(int(m.group(1)), _MONTHS[m.group(2)], int(m.group(3)))
    except (KeyError, ValueError):
        return pd.NaT


def _read_gcat(name: str) -> pd.DataFrame:
    df = pd.read_csv(DATA / f"{name}.tsv", sep="\t", dtype=str, skiprows=[1], low_memory=False)
    df.columns = [c.lstrip("#") for c in df.columns]
    df = df.apply(lambda c: c.str.strip())
    df["source"] = name
    return df


def load_satcat() -> pd.DataFrame:
    """satcat (resmî katalog numaralı objeler) + auxcat (numara almadan düşen/izlenen
    objeler; ör. Şubat 2022'de kaybedilen Starlink'lerin çoğu burada)."""
    df = pd.concat([_read_gcat("satcat"), _read_gcat("auxcat")], ignore_index=True)
    for col in ["LDate", "SDate", "DDate"]:
        df[col + "_t"] = df[col].map(parse_gcat_date)
    for col in ["Perigee", "Apogee", "Inc", "Mass"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["kind"] = df["Type"].str[0]          # P=uydu, R=roket gövdesi, D=enkaz, C=parça
    df["is_starlink"] = df["Name"].str.contains("Starlink", case=False, na=False)
    return df


def load_kp() -> pd.DataFrame:
    cols = (["Y", "M", "D", "days", "days_m", "Bsr", "dB"]
            + [f"Kp{i}" for i in range(1, 9)] + [f"ap{i}" for i in range(1, 9)]
            + ["Ap", "SN", "F107obs", "F107adj", "flag"])
    df = pd.read_csv(DATA / "kp.txt", sep=r"\s+", comment="#", names=cols)
    df["date"] = pd.to_datetime(dict(year=df.Y, month=df.M, day=df.D))
    df = df.set_index("date")
    kp = df[[f"Kp{i}" for i in range(1, 9)]]
    out = pd.DataFrame({
        "Ap": df["Ap"].where(df["Ap"] >= 0),
        "Kp_max": kp.where(kp >= 0).max(axis=1),
        "F107": df["F107obs"].where(df["F107obs"] > 0),
        "SN": df["SN"].where(df["SN"] >= 0),
    })
    return out
