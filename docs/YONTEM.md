# Yöntem

Bu belge, projedeki üç analizin her adımını kodla birebir eşleşecek ayrıntıda anlatır. Sayılar ve grafikler için [SONUCLAR.md](SONUCLAR.md), veri dosyaları için [VERI.md](VERI.md).

## İçindekiler

1. [Ortak hazırlık](#1-ortak-hazırlık)
2. [A · Güneş döngüsü ve yıllık düşme oranı](#2-a--güneş-döngüsü-ve-yıllık-düşme-oranı)
3. [B · Fırtına sonrası düşen obje sayısı](#3-b--fırtına-sonrası-düşen-obje-sayısı)
4. [C · Starlink fırlatmaları](#4-c--starlink-fırlatmaları)
5. [D · Fırtına haftasında yörünge alçalması](#5-d--fırtına-haftasında-yörünge-alçalması)
6. [Doğrulama ve yapay veri testi](#6-doğrulama-ve-yapay-veri-testi)
7. [Bilinen sınırlar](#7-bilinen-sınırlar)

---

## 1. Ortak hazırlık

Kod: [`load.py`](../load.py)

### Uydu kataloğu

- **Kaynak:** Jonathan McDowell'ın GCAT kataloğu. `satcat.tsv` resmî katalog numarası almış objeleri, `auxcat.tsv` numara almadan düşen ya da yalnızca kısa süre izlenen objeleri içerir.
- **İki katalog birleştirilir.** Bu kritik: Şubat 2022 Starlink uydularının çoğu, katalog numarası almadan düştüğü için yalnızca `auxcat`'te yer alır. Yalnızca `satcat` kullanıldığında 49 uydudan 6'sı görünüyordu; birleştirince doğru sayı (38/49) geldi.
- **Tarihler:** GCAT tarihleri `1957 Dec  1 1000?` biçimindedir. Ay ya da gün eksikse tarih belirsiz sayılır (`NaT`) ve o obje zamana bağlı hesaplara girmez.
- **Obje türü:** `Type` sütununun ilk harfi. `P` yük (uydu), `R` roket gövdesi, `D` enkaz, `C` parça.
- **Kontrolsüz objeler:** `D`, `R` ve `C`. Motorları yoktur, manevra yapmazlar; düşüş zamanlarını yalnızca atmosfer belirler. Bu yüzden Güneş ve fırtına etkisini görmek için en temiz örneklemdir.
- **Starlink:** adında `Starlink` geçen `P` türü objeler.

### Uzay havası indeksleri

- **Kaynak:** GFZ Potsdam, `Kp_ap_Ap_SN_F107_since_1932.txt`.
- **Kullanılan sütunlar:** günlük **Ap**, günün en yüksek üç saatlik **Kp** değeri, gözlenen **F10.7** ve Güneş lekesi sayısı.
- **81 günlük F10.7 ortalaması:** üç Güneş dönüşü boyunca ortalama; kısa süreli dalgalanmayı ayıklayıp Güneş döngüsünün düzeyini verir.

---

## 2. A · Güneş döngüsü ve yıllık düşme oranı

Kod: [`analysis.py`](../analysis.py), bölüm A

1. **Nüfus:** her yıl için, 1 Ocak'ta yörüngede olan kontrolsüz alçak yörünge objeleri. Alçak yörünge, apojesi 2.000 km'nin altında ya da düşüş tarihi bilinen objeler olarak tanımlanır.
2. **Düşen:** bu nüfustan o yıl içinde atmosfere girenler.
3. **Düşme oranı** = düşen ÷ nüfus (%).
4. **İlişki:** 1966–2025 arasındaki 60 yıl için yıllık ortalama F10.7 ile düşme oranı arasında Pearson ve Spearman korelasyonu.
5. **Maksimum/minimum oranı:** düşme oranının F10.7'ye doğrusal regresyonundan, F10.7'nin %90'lık dilimindeki tahmin (≈190 sfu) ÷ %10'luk dilimindeki tahmin (≈73 sfu).

> **Neden yıllık?** Bir objenin yörüngede kalma süresi aylardan yıllara uzanır. Yıllık oran, Güneş döngüsünün (≈11 yıl) etkisini görmek için yeterli çözünürlükte ve gürültüsü düşük.

---

## 3. B · Fırtına sonrası düşen obje sayısı

Kod: [`analysis.py`](../analysis.py), bölüm B

### Üst üste bindirilmiş olay analizi

1. **Fırtına seçimi:** günlük Ap ≥ 100 olan günler. Birbirine 30 günden yakın olanlardan yalnızca ilki tutulur (kümeleme ayıklama). Sonuç: 54 fırtına.
2. **Pencere:** her fırtına için −30…+60. günlerin günlük yeniden giriş sayısı.
3. **Normalleştirme:** her pencere, fırtınadan önceki 30 günün (−30…−1) ortalamasına bölünür. 1 = normal.
4. **İstatistik:** 0…+14. günlerin ortalama normalleştirilmiş değeri, tüm fırtınalar üzerinden ortalanır.

### Rastgele tarih testi (sıfır dağılımı)

Fırtınalar çoğunlukla Güneş maksimumunda olur; o dönemde düşüşler zaten yüksektir. Bu karışıklığı ayıklamak için:

1. Her fırtına, **aynı Güneş aktivitesi düzeyindeki** (81 günlük F10.7 farkı ≤ 15 sfu) **sakin** bir rastgele günle değiştirilir. Sakin gün: ±10 gün içinde Ap'si 40'ı aşmayan gün.
2. Aynı istatistik bu sahte tarihlerle 2.000 kez hesaplanır.
3. **Fazla** = gözlenen istatistik − sıfır dağılımının ortancası.
4. **p değeri** = sıfır dağılımında gözlenen değere eşit ya da büyük olanların oranı (tek yönlü).
5. **Güven aralığı:** fırtınalar yeniden örneklenerek (2.000 kez).

### Doz-yanıt

Aynı analiz dört Ap sınıfı için ayrı yapılır: 30–50, 50–80, 80–120, 120+. Her sınıfta, ±30 gün içinde sınıfın üst sınırını aşan bir fırtına olan tarihler çıkarılır; böylece bir sınıfın sonucu daha güçlü bir fırtınadan etkilenmez.

### En güçlü 10 gün

Tüm kayıt boyunca en yüksek Ap'li 10 gün (birbirine 30 günden yakın olmayan) için sonraki 14 günde düşen obje sayısı, önceki 30 günün günlük ortalamasından beklenen sayıyla karşılaştırılır.

---

## 4. C · Starlink fırlatmaları

Kod: [`analysis.py`](../analysis.py), bölüm C

1. **Fırlatmalar:** Mayıs 2019'dan son 30 güne kadar, GCAT fırlatma etiketine göre gruplanmış Starlink uyduları.
2. **Kayıp:** fırlatmadan sonraki 30 gün içinde atmosfere giren uydular.
3. **İlk hafta fırtınası:** fırlatma günü ve sonraki 6 günün en yüksek Kp ve Ap değeri.
4. **Bırakma irtifası:** fırlatmadaki uyduların ortanca perije yüksekliği. 250 km'nin altı "alçak bırakma".
5. **Çıkarılanlar** (fırtınayla ilgisi olmayan kayıplar):
   - GCAT'te `U` etiketli, yörüngeye ulaşmamış ya da yörünge altı uçuşlar,
   - ortanca perijesi 150 km'nin altında kalan fırlatmalar,
   - Temmuz 2024 Falcon 9 üst kademe arızası (`2024-129`).
6. **Gruplar:** bırakma irtifası (normal / alçak) × ilk hafta Kp'si (< 4, 4–5, ≥ 5).
7. **Test:** alçak bırakılan fırlatmalarda Kp ≥ 5 ile Kp < 5 arasındaki kayıp oranı farkı için Fisher kesin testi.
8. **Duyarlılık:** aynı karşılaştırma Şubat 2022 (`2022-010`) çıkarılarak tekrarlanır.

---

## 5. D · Fırtına haftasında yörünge alçalması

Kodlar: [`st_plan.py`](../st_plan.py), [`spacetrack_fetch.py`](../spacetrack_fetch.py), [`altitude.py`](../altitude.py)

### 5.1 Fırtına ve obje seçimi (`st_plan.py`)

- **Fırtınalar:** 2000–2026 arasında Ap ≥ 50 olan tepe günleri. En güçlüden başlanır; seçilmiş bir tepeye 30 günden yakın olanlar atlanır. Ap'si 50'nin altında kalsa da Starlink kaybı nedeniyle **3 Şubat 2022** ayrıca eklenir. Sonuç: 64 fırtına.
- **Objeler:** her fırtınada, pencerenin tamamı boyunca yörüngede kalan, katalog numaralı (`satcat`), perijesi 200 km'nin üstünde ve apojesi 700 km'nin altında kontrolsüz objelerden rastgele en fazla 400 tane. İrtifa bandı (250–700 km) ölçüm aşamasında yeniden uygulanır.
- **Pencere:** her fırtına için −35…+25. günler.

### 5.2 Yörünge geçmişini indirme (`spacetrack_fetch.py`)

- Space-Track `gp_history` sınıfından `NORAD_CAT_ID, EPOCH, MEAN_MOTION, ECCENTRICITY, BSTAR` alanları.
- İstekler arasında 3,5 saniye beklenir (Space-Track hız sınırı); `HTTP 429` gelirse beklenip tekrar denenir.
- Her fırtına `data/spacetrack/<tarih>.csv` olarak saklanır; yarıda kalan indirme kaldığı yerden sürer.
- Kullanıcı adı ve şifre ortam değişkeninden ya da terminalde sorularak alınır; hiçbir dosyaya yazılmaz.
- Toplam yaklaşık 1,8 milyon yörünge kaydı.

### 5.3 İrtifa ve temizlik

- **İrtifa:** ortalama hareketten (n, tur/gün) Kepler yasasıyla: a = (μ / n²)^(1/3), irtifa = a − 6.378,137 km (μ = 398.600,4418 km³/s²).
- **Dairesel yörünge:** ortanca dışmerkezliği 0,01'den büyük objeler çıkarılır.
- **Sıçramalar:** aynı güne düşen kopyalar atılır; 5 kayıtlık kayan ortancadan 1 km'den fazla sapan TLE kayıtları atılır. En az 8 kayıt gerekir.
- **Bant:** ortanca irtifası 250–700 km olan objeler.

### 5.4 Obje başına ölçüm

Fırtına günü `d0 = 0`:

| Adım | Tanım |
|---|---|
| Normal hız | `[d0−14, d0−3]` günlerindeki irtifaların Theil–Sen eğimi (en az 5 kayıt, en az 7 günlük yayılım) |
| Beklenen kayıp | normal hız × 7 gün |
| Gerçek kayıp | `d0−2` ile `d0+5` günleri arasındaki irtifa farkı (en yakın iki kayıttan doğrusal ara değer, ±1,6 gün içinde kayıt şart) |
| Oran | gerçek kayıp ÷ beklenen kayıp |
| Kayıp gün | (gerçek − beklenen) ÷ günlük normal alçalma |

- **Plasebo:** aynı ölçüm `d0 = −16` ile tekrarlanır (ön pencere `[−30, −19]`, ölçüm `[−18, −11]`). Ölçüm tamamen simetriktir.
- **Anlamlı alçalma şartı:** beklenen kayıp en az 35 m/hafta (≈5 m/gün) ve gerçek kayıp pozitif olmalı. Çok yavaş alçalan objelerde oran gürültüye boğulur.

### 5.5 Neden pencere düzeyinde?

Aynı haftadaki objeler aynı atmosferden geçer; birlikte dalgalanırlar. Onları bağımsız saymak, güven aralıklarını yapay biçimde daraltır. Bu yüzden **birim, objeler değil haftalardır**:

- Her fırtına için iki pencere: **fırtına** ve **plasebo**.
- Her pencerede, en az 15 objenin **ortanca oranı**.
- Her pencere için Ap ve F10.7'nin, kendi ön penceresine göre **artışı**:
  - fırtına penceresi `[−2, +4]` ↔ ön pencere `[−14, −3]`
  - plasebo penceresi `[−18, −12]` ↔ ön pencere `[−30, −19]`
- Sonuç: 128 pencere (64 fırtına + 64 plasebo).

### 5.6 Model

```
log(ortanca oran) = b0 + b1 · (ΔAp / 10) + b2 · (ΔF10.7 / 10)
```

- En küçük kareler; tüm objeler için ve üç irtifa bandı (250–450, 450–550, 550–700 km) için ayrı.
- **Etki yüzdesi:** 100 · (e^b − 1). Örneğin b1 = 0,101 → +10 Ap başına %10,7.
- **Güven aralıkları:** fırtınalar (pencere çiftleri birlikte) yeniden örneklenerek 2.000 kez; %2,5 ve %97,5 dilimleri.
- 10'dan az fırtınası olan bant modellenmez.

### 5.7 Eşleştirilmiş test

Her fırtına için fırtına penceresinin oranı ile plasebo penceresinin oranı karşılaştırılır: kaç fırtınada fırtına > plasebo, ve log oranlar üzerinde Wilcoxon işaretli sıra testi.

### 5.8 Kayıp gün eğrileri

Normal hızı günde en az 5 m olan objeler için −10…+20. günlerde, ön eğilimden sapma günlük normal alçalma cinsinden hesaplanır ve fırtına gücüne göre (Ap 50–80, 80–130, > 130) ortancası alınır.

---

## 6. Doğrulama ve yapay veri testi

- **Yapay veri:** etkisi bilinen sahte yörünge kayıtları üretildi (en güçlü fırtınada gerçek oran ≈ 1,9). Kod 1,8 buldu; plasebo tarihlerinde 1,0 çıktı, yani fırtına yokken sahte etki üretmiyor.
- **İlk sürümdeki yanlılık:** ilk denemede 27 günlük uzun bir ön pencere kullanılıyordu. Alçaldıkça hızlanan objelerde düz eğilim, fırtına olmadan da "fazla alçalma" üretti; orta ve şiddetli fırtınalar aynı etkiyi verdi (fiziğe aykırı). Kısa ve yakın ön pencere, tamamen simetrik plasebo ve pencere düzeyinde model ile düzeltildi; yapay veri testi düzeltilmiş yöntemle tekrar geçti.
- **Plasebo ortancası 0,95×:** fırtınasız haftalarda yöntem 1'e yakın sonuç veriyor.

---

## 7. Bilinen sınırlar

- **Tahmin aralığı:** ölçülen haftalık Ap artışı en fazla ~60. Laboratuvardaki daha büyük değerler modelin dışına taşmadır.
- **Karışık etkiler:** büyük fırtınalar çoğunlukla güçlü Güneş ışınımıyla birlikte gelir. Model Ap ve F10.7'yi ayrı tahmin eder, ama ikisi ilişkili olduğundan tam ayıramaz.
- **TLE hatası:** yörünge kayıtları günde birkaç kez güncellenir ve her birinin hata payı vardır; ortanca kullanmak tek tek hataları bastırır ama tamamen yok etmez.
- **Örneklem:** yalnızca kontrolsüz objeler. Manevra yapan uydular (çoğu aktif uydu) farklı davranır.
- **Starlink sonucu:** fark neredeyse tamamen tek bir olaydan (Şubat 2022) geliyor; genelleme için yeterli değil.
- **Bırakma irtifası:** GCAT'teki yörünge kaydından alınır; fırlatma anındaki gerçek değere yakın ama yaklaşık.
