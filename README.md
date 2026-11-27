# Fırtına ve Yörünge · Storm & Orbit

Güneş fırtınalarının alçak Dünya yörüngesindeki (LEO) objeleri nasıl alçalttığını inceleyen bir veri bilimi projesi ve etkileşimli 3B sunumu.

**Canlı sunum:** https://storm-and-orbit.up.railway.app

> *An open data-science project on how solar storms lower objects in low Earth orbit, with an interactive 3D presentation (Turkish and English).*

## Bulgular

| Soru | Sonuç |
|---|---|
| Güneş döngüsü düşüşleri etkiliyor mu? | Güneş maksimumunda kontrolsüz objelerin yıllık düşme oranı minimumun **3,52 katı** (Spearman r = 0,78, 1966–2025). |
| Tek bir fırtına daha çok objeyi düşürüyor mu? | Sonraki 14 günde **+%11,7** fazla düşüş, ama kesin değil (p = 0,082, 54 fırtına). |
| Fırtına yörüngeleri alçaltıyor mu? | Evet. Her **+10 Ap** haftalık alçalmayı **%10,7** hızlandırıyor (%95: 7,7–15,0); 64 fırtınanın 49'unda etki plasebo haftasından büyük (Wilcoxon p = 1,1·10⁻⁵). |
| İrtifaya göre değişiyor mu? | Yükseldikçe artıyor: 250–450 km'de %6,6, 550–700 km'de %12,7. |
| Starlink fırlatmaları fırtınadan etkileniyor mu? | Alçak bırakılıp fırtınaya denk gelenlerde kayıp %3,83, sakinlerde %0,60; ama fark neredeyse tamamen Şubat 2022'den (49 uydudan 38'i) geliyor. |

## Yapı

| Dosya | Görev |
|---|---|
| `download_data.py` | GCAT kataloğunu ve GFZ indekslerini `data/` klasörüne indirir |
| `load.py` | Katalog ve indeksleri okur, tarihleri ve obje türlerini düzenler |
| `analysis.py` | Güneş döngüsü, fırtına sonrası düşüş, doz-yanıt ve Starlink analizleri → `results.json`, `dash_data/` |
| `st_plan.py` | Space-Track'ten indirilecek fırtına pencerelerini ve objeleri seçer → `data/st_plan.json` |
| `spacetrack_fetch.py` | Space-Track yörünge geçmişini indirir (hesap gerekir) → `data/spacetrack/` |
| `altitude.py` | Fırtına haftası / plasebo haftası alçalma oranları, irtifa bantları, bootstrap → `dash_data/alt_*.json` |
| `presentation/` | Sunumun şablonu (`template.html`), veri derleyici (`build_data.py`) ve harita dosyaları |
| `deploy/` | Railway yayını: Caddy ile statik site (`Dockerfile`, `Caddyfile`, `build_site.py`) |
| `page/` | Analiz panosunun sayfası |

## Yeniden üretme

```powershell
python -m pip install -r requirements.txt
python download_data.py
python analysis.py
```

Yörünge analizi için bir [Space-Track.org](https://www.space-track.org/) hesabı gerekir. Kullanıcı adı ve şifre terminalde sorulur ya da `SPACETRACK_USER` / `SPACETRACK_PASS` ortam değişkenlerinden okunur; hiçbir dosyaya yazılmaz.

```powershell
python st_plan.py
python spacetrack_fetch.py
python altitude.py
```

Sunumu derleyip yerelde açmak:

```powershell
python presentation\build_data.py
python -m http.server 8791 --directory presentation
```

Ardından `http://localhost:8791/preview.html` adresini açın.

Railway'e yayınlama adımları [deploy/README.md](deploy/README.md) dosyasında.

## Yöntem özeti

- **Fırtına seçimi:** 2000–2026 arasında Ap ≥ 50 olan günler; birbirine 30 günden yakın tepelerden en güçlüsü.
- **Obje seçimi:** her fırtınada en fazla 400 kontrolsüz obje (enkaz, roket gövdesi).
- **Beklenen kayıp:** her objenin −14…−3. günlerdeki alçalma hızı (Theil–Sen eğimi).
- **Fırtına haftası:** −2…+5. günlerdeki gerçek kayıp ÷ beklenen kayıp.
- **Plasebo:** aynı ölçüm fırtınadan 16 gün önce.
- **Model:** haftalık ortanca oranın logaritması ~ ΔAp + ΔF10.7; güven aralıkları fırtınalar yeniden örneklenerek (2.000 kez).

## Veri kaynakları ve lisanslar

- **GCAT:** Jonathan McDowell, [planet4589.org/space/gcat](https://planet4589.org/space/gcat/), CC BY 4.0
- **Kp, Ap, F10.7:** [GFZ Potsdam](https://kp.gfz-potsdam.de/en/), CC BY 4.0
- **Yörünge geçmişi:** [Space-Track.org](https://www.space-track.org/). Koşulları gereği ham kayıtlar bu depoda yer almaz; yalnızca hesaplanan özetler var.
- **Harita:** [Natural Earth](https://www.naturalearthdata.com/) (world-atlas TopoJSON), kamu malı
- **3B:** [three.js](https://threejs.org/) r170
