"""Railway için yayın klasörünü hazırlar.

presentation/index.html (artifact gövdesi) tam bir HTML belgesine sarılır ve
harita dosyalarıyla birlikte deploy/site/ altına kopyalanır.
Önce: python presentation/build_data.py
"""
import shutil
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
SITE = HERE / "site"

body = (ROOT / "presentation" / "index.html").read_text(encoding="utf-8")
icon = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E"
        "%3Ccircle cx='20' cy='20' r='7.5' fill='%2317141f'/%3E"
        "%3Cellipse cx='20' cy='20' rx='17' ry='7' fill='none' stroke='%238a4dff' stroke-width='2.4' transform='rotate(-24 20 20)'/%3E"
        "%3Ccircle cx='34.2' cy='13.6' r='2.8' fill='%238a4dff'/%3E%3C/svg%3E")
desc = ("Güneş fırtınalarının alçak yörüngedeki uyduları nasıl alçalttığını 60 yıllık katalog, "
        "Güneş indeksleri ve 10.695 yörünge ölçümüyle anlatan etkileşimli 3B sunum.")
head = f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{desc}">
<meta name="theme-color" content="#f6f5fa">
<meta property="og:title" content="Fırtına ve Yörünge">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<link rel="icon" href="{icon}">
<style>:root{{color-scheme:light}}body{{margin:0;font:14px system-ui}}[hidden]{{display:none!important}}</style>
</head>
<body>
"""
if SITE.exists():
    shutil.rmtree(SITE)
(SITE / "geo").mkdir(parents=True)
(SITE / "index.html").write_text(head + body + "\n</body>\n</html>\n", encoding="utf-8")
for f in ["land-50m.json", "countries-110m.json"]:
    shutil.copy(ROOT / "presentation" / "geo" / f, SITE / "geo" / f)
print("site hazır:", sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob("*") if p.is_file()))
