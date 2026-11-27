"""Herkese açık ham verileri data/ klasörüne indirir.

- GCAT satcat.tsv, auxcat.tsv, ftocat.tsv  (Jonathan McDowell, planet4589.org, CC BY 4.0)
- GFZ Potsdam Kp, Ap, SN, F10.7 (1932'den bu yana, CC BY 4.0)

Space-Track yörünge geçmişi bu betikle indirilmez; hesap gerektirir ve
koşulları yeniden dağıtıma izin vermez. Onun için: python st_plan.py, sonra
python spacetrack_fetch.py (kullanıcı adı ve şifre terminalde sorulur).
"""
from pathlib import Path

import requests

DATA = Path(__file__).parent / "data"
FILES = {
    "satcat.tsv": "https://planet4589.org/space/gcat/tsv/cat/satcat.tsv",
    "auxcat.tsv": "https://planet4589.org/space/gcat/tsv/cat/auxcat.tsv",
    "ftocat.tsv": "https://planet4589.org/space/gcat/tsv/cat/ftocat.tsv",
    "kp.txt": "https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F107_since_1932.txt",
}

DATA.mkdir(exist_ok=True)
for name, url in FILES.items():
    print(f"{name:12s} <- {url}")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    (DATA / name).write_bytes(r.content)
    print(f"{'':12s}    {len(r.content) / 1e6:.1f} MB")
