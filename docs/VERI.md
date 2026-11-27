# Veri

Projenin girdileri, ürettiği dosyalar ve her dosyanın alanları.

## Girdi verileri

| Dosya | Kaynak | İçerik | Boyut | Lisans | Depoda |
|---|---|---|---|---|---|
| `data/satcat.tsv` | [GCAT](https://planet4589.org/space/gcat/), Jonathan McDowell | Katalog numaralı bütün objeler: fırlatma, düşüş tarihi, tür, perije, apoje | ~18 MB | CC BY 4.0 | Evet (anlık görüntü) |
| `data/auxcat.tsv` | GCAT | Katalog numarası almadan düşen ya da kısa süre izlenen objeler | ~3 MB | CC BY 4.0 | Evet |
| `data/ftocat.tsv` | GCAT | Yörüngeye ulaşmayan fırlatmalar | ~0,5 MB | CC BY 4.0 | Evet |
| `data/kp.txt` | [GFZ Potsdam](https://kp.gfz-potsdam.de/en/) | 1932'den bu yana üç saatlik Kp, günlük Ap, Güneş lekesi sayısı, F10.7 | ~5 MB | CC BY 4.0 | Evet |
| `data/st_plan.json` | `st_plan.py` | 64 fırtına penceresi ve her birinde seçilen obje numaraları | 0,2 MB | — | Evet |
| `data/spacetrack/*.csv` | [Space-Track.org](https://www.space-track.org/) `gp_history` | 64 pencere için ~1,8 milyon yörünge kaydı | ~136 MB | Space-Track kullanım koşulları | **Hayır** |

- **Anlık görüntü tarihi:** GCAT ve GFZ dosyaları 25–26 Kasım 2026'da indirildi. Güncel sürüm için `python download_data.py`.
- **Space-Track:** kullanım koşulları ham kayıtların yeniden dağıtılmasına izin vermez. Bu yüzden depoda yalnızca bu kayıtlardan hesaplanan özetler (`dash_data/alt_*.json`, `results_alt.json`) var. Kendi hesabınızla `st_plan.py` → `spacetrack_fetch.py` sırasıyla yeniden indirebilirsiniz.

## Üretilen dosyalar

Her `dash_data/*.json` dosyası `{ "rows": [...], "meta": [...] }` biçimindedir. `meta`, sayıları üreten kodun kendisini ve girdinin tanımını taşır; dosya tek başına yeniden üretilebilir.

### Güneş döngüsü ve yeniden girişler (`analysis.py`)

| Dosya | Satır | Alanlar |
|---|---|---|
| `yearly.json` | 60 | `year` yıl · `pop` 1 Ocak'ta yörüngedeki kontrolsüz obje · `reentries` o yıl düşen · `rate_pct` düşme oranı (%) · `f107` yıllık ortalama F10.7 · `ap` yıllık ortalama Ap |
| `epoch.json` | 91 | `lag` fırtınaya göre gün (−30…+60) · `observed` normalleştirilmiş günlük yeniden giriş (7 günlük kayan ortalama) · `null_lo`, `null_mid`, `null_hi` rastgele tarihlerle %5 / %50 / %95 |
| `dose.json` | 4 | `label` Ap sınıfı · `n` fırtına sayısı · `excess_pct` fazla düşüş (%) · `ci_lo`, `ci_hi` %95 aralık · `p_value` |
| `top_storms.json` | 10 | `date` · `ap` · `kp_max` · `after14` sonraki 14 günde düşen · `expected14` önceki 30 güne göre beklenen |
| `starlink_launches.json` | 407 | `tag` GCAT fırlatma etiketi · `date` · `n` uydu · `lost30` 30 günde kayıp · `ap_max7`, `kp_max7` ilk hafta en yüksek · `perigee_med` ortanca perije (km) · `low_deploy` < 250 km |
| `starlink_kp.json` | 6 | `group` bırakma irtifası · `kp_bin` ilk hafta Kp sınıfı · `launches` · `sats` · `lost` · `lost_pct` |
| `summary.json` | 1 | Başlık sayıları: `max_vs_min_ratio`, `spearman_r`, `pearson_r`, `excess_pct`, `p_value`, Starlink Fisher testi (`sl_*`) |
| `results.json` | — | Yukarıdakilerin hepsi, ek olarak aylık seri ve Starlink'in yıllık yeniden girişleri |

### Yörünge alçalması (`altitude.py`)

| Dosya | Satır | Alanlar |
|---|---|---|
| `alt_summary.json` | 1 | `n_objects`, `n_events`, `storm_median`, `placebo_median`, `n_higher`, `wilcoxon_p`, model katsayıları, Mayıs 2024 ve Cadılar Bayramı 2003 özetleri |
| `alt_events.json` | 64 | `event` fırtına tarihi · `ap_peak` · `d_ap`, `d_f107` haftalık artış · `n` obje · `ratio` ortanca oran · `placebo_ratio` · `lost_days` ortanca kayıp gün |
| `alt_windows.json` | 128 | `event` · `kind` `storm` / `placebo` · `n` · `ratio` · `d_ap` · `d_f107` · `lost_days` |
| `alt_coef.json` | 4 | `band` (`Tümü` ve üç bant) · `n_windows` · `n_events` · `r2` · `ap_pct` (+10 Ap başına %) ve aralığı · `f107_pct` (+10 sfu başına %) ve aralığı |
| `alt_grid.json` | 52 | `band` · `d_ap` (0…60) · `ratio` model tahmini · `lo`, `hi` %95 aralık |
| `alt_curves.json` | 93 | `strength` fırtına sınıfı · `day` (−10…+20) · `lost_days` ortanca fazladan alçalma · `n` obje · `n_events` fırtına |
| `results_alt.json` | — | Yukarıdakilerin hepsi ve olay düzeyi Spearman korelasyonu |

### Sunum verisi

`presentation/build_data.py`, yukarıdaki dosyalardan sunumun ihtiyaç duyduğu ~34 KB'lık bir özet derler ve `template.html` içine gömer. Ek olarak GFZ dosyasından Mayıs 2024 ve Şubat 2022 çevresindeki günlük Ap/Kp/F10.7 değerlerini, NOAA G sınıflarının yıllık gün sayılarını ve tarihî fırtına günlerinin indekslerini hesaplar. Şubat 2022 sabitlerinin (38/49, 209 km, Kp 5,3) veriyle uyumunu `assert` ile doğrular.

### Harita

`presentation/geo/`: [world-atlas](https://github.com/topojson/world-atlas) 2.0.2 TopoJSON dosyaları (Natural Earth 1:50m kara, 1:110m ülkeler). Natural Earth kamu malıdır.

## Atıf

Bu verileri kullanırken lütfen kaynaklara atıf yapın:

- McDowell, J. C. *General Catalog of Artificial Space Objects*, https://planet4589.org/space/gcat/
- Matzka, J., Stolle, C., Yamazaki, Y., Bronkalla, O. ve Morschhauser, A. (2021). *The geomagnetic Kp index and derived indices of geomagnetic activity.* Space Weather, 19, e2020SW002641. Veri: GFZ Data Services.
- Space-Track.org, https://www.space-track.org/
