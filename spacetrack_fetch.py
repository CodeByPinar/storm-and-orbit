"""Space-Track.org'dan fırtına pencerelerinin tarihsel yörünge kayıtlarını (GP history) indirir.

Kullanım (bu klasörde):
    python spacetrack_fetch.py
Kullanıcı adı ve şifre sorulur (şifre ekranda görünmez). İstenirse önceden
SPACETRACK_USER / SPACETRACK_PASS ortam değişkenleriyle de verilebilir.

- Bilgiler hiçbir dosyaya yazılmaz.
- Her pencere data/spacetrack/<tarih>.csv olarak saklanır; yarıda kalırsa yeniden
  çalıştırınca kaldığı yerden devam eder.
- Space-Track sınırlarına uyar: dakikada en fazla ~20 istek, 429 gelirse bekler.
- Yalnızca gereken sütunlar istenir (NORAD_CAT_ID, EPOCH, MEAN_MOTION, ECCENTRICITY, BSTAR).
"""
import getpass
import json
import os
import sys
import time
from pathlib import Path

import requests

BASE = "https://www.space-track.org"
HERE = Path(__file__).parent
PLAN = HERE / "data" / "st_plan.json"
OUT = HERE / "data" / "spacetrack"
FIELDS = "NORAD_CAT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,BSTAR"
PAUSE = 3.5  # saniye


def main():
    user, pw = os.environ.get("SPACETRACK_USER"), os.environ.get("SPACETRACK_PASS")
    if user == "space-track-kullanici-adin" or pw == "sifren":   # örnekteki yer tutucular
        user = pw = None
    if not user:
        user = input("Space-Track kullanıcı adı (kayıt olduğun e-posta): ").strip()
    if not pw:
        pw = getpass.getpass("Space-Track şifresi (yazarken ekranda görünmez, sonra Enter): ")
    if not user or not pw:
        sys.exit("Kullanıcı adı ve şifre gerekli.")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [p for p in plan if not (OUT / f"{p['event']}.csv").exists()]
    print(f"{len(plan)} pencereden {len(plan) - len(todo)} hazır, {len(todo)} indirilecek.")
    if not todo:
        return

    s = requests.Session()
    s.headers["User-Agent"] = "storm-orbit-study/1.0"
    r = s.post(f"{BASE}/ajaxauth/login", data={"identity": user, "password": pw}, timeout=60)
    if r.status_code != 200 or "Failed" in r.text:
        sys.exit(f"Giriş başarısız (HTTP {r.status_code}). Kullanıcı adı/şifreyi kontrol et.")
    print("Giriş tamam.")

    try:
        for i, p in enumerate(todo, 1):
            ids = ",".join(map(str, p["ids"]))
            url = (f"{BASE}/basicspacedata/query/class/gp_history/NORAD_CAT_ID/{ids}"
                   f"/EPOCH/{p['start']}--{p['end']}/orderby/NORAD_CAT_ID,EPOCH"
                   f"/predicates/{FIELDS}/format/csv")
            for attempt in range(5):
                r = s.get(url, timeout=600)
                if r.status_code == 429:
                    print("  hız sınırı, 70 sn bekleniyor...")
                    time.sleep(70)
                    continue
                break
            if r.status_code != 200:
                print(f"  {p['event']}: HTTP {r.status_code}, atlandı. {r.text[:200]}")
                time.sleep(PAUSE)
                continue
            tmp = OUT / f"{p['event']}.csv.part"
            tmp.write_text(r.text, encoding="utf-8")
            tmp.replace(OUT / f"{p['event']}.csv")
            n = r.text.count("\n") - 1
            print(f"[{i}/{len(todo)}] {p['event']} (Ap tepe {p['ap_peak']}): {n:,} kayıt")
            time.sleep(PAUSE)
    finally:
        s.get(f"{BASE}/ajaxauth/logout", timeout=60)


if __name__ == "__main__":
    main()
