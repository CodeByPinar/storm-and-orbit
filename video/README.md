# Tanıtım videosu

[`storm-and-orbit.mp4`](storm-and-orbit.mp4) · 38,6 saniye · 1920×1080 · 30 fps · H.264 + AAC

Projenin 3B sunumundaki three.js sahnelerinden, kare kare üretilmiş bir tanıtım videosu. Müzik de kodla, tarayıcıda sentezlenir; hiçbir hazır görüntü ya da ses dosyası kullanılmaz.

## Sahneler

| Süre | Sahne | Metin |
|---|---|---|
| 0:00–0:05 | Dünya ve yörüngedeki objeler | Fırtına ve Yörünge |
| 0:05–0:10 | Güneş döngüsü | 60 yıl · 35.231 yeniden giriş · **3,5×** |
| 0:10–0:16 | Mayıs 2024 fırtınası, sıkışan manyetosfer | 1960'tan beri en güçlü ikinci gün · **Ap 271** |
| 0:16–0:21 | Bir objenin fırtına haftası | 64 fırtına · 10.695 ölçüm · **1,30×** |
| 0:21–0:25 | İrtifa kabukları | Her +10 Ap → **+%10,7** |
| 0:25–0:30 | Starlink grubu | Şubat 2022 · **38/49** |
| 0:30–0:34 | Uydunun sökümü | Sürtünme anatomisi · **ρ · v² · A** |
| 0:34–0:39 | Kapanış | Canlı sunum ve GitHub adresleri |

## Nasıl üretiliyor

1. `render.mjs`, `deploy/site` klasörünü yerel bir sunucuyla açar ve sunumu başsız Edge/Chrome'da yükler (`#capture` modu: oynatma durur, zaman elle verilir).
2. Sunumun arayüz panelleri gizlenir; yerine `overlay.js` ile sinematik bir metin katmanı eklenir. Metnin her hâli yalnızca zamana bağlı hesaplanır, kareler birbirinden bağımsızdır.
3. Her kare için video zamanı sahnenin simülasyon aralığına eşlenir (`scenes.mjs`), `SIM.seek()` ile çizilir ve görüntüsü alınır. Görüntü yanda kalan metne yer açmak için `SIM.view()` ile sağa kaydırılır.
4. Kareler doğrudan ffmpeg'e akar; diske ara dosya yazılmaz.
5. `music.js`, OfflineAudioContext ile 96 BPM, re minörde bir müzik sentezler: pad, bas, arpej, FM çan, davullar, fırtına ve kapanış kesmelerinde yükselen ses ve darbe. Kesmeler vuruşlarla eşleşir.
6. ffmpeg görüntüyü H.264 (CRF 17), sesi AAC 192 kbps olarak birleştirir; `poster.jpg` kapak görselini de üretir.

## Yeniden üretmek

Gerekenler: Node 18+, ffmpeg (PATH'te), Edge ya da Chrome.

```powershell
python presentation\build_data.py
```

```powershell
python deploy\build_site.py
```

```powershell
cd video
```

```powershell
npm install
```

```powershell
node render.mjs
```

Yalnızca birkaç test karesi almak için (ör. 2,5 ve 13. saniye; `video/.tmp/` klasörüne yazılır):

```powershell
node render.mjs --frames 2.5,13
```

Metinleri ve sahne sürelerini değiştirmek için `scenes.mjs`, görünümü değiştirmek için `overlay.js`, müzik için `music.js` dosyasını düzenleyin.
