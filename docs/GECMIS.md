# Proje geçmişi

Projenin fikirden yayına nasıl ilerlediği: verilen kararlar, karşılaşılan sorunlar ve çözümleri.

## 1. Fikir aşaması

Hedef: herkese açık verilerle, alışılmış "ötegezegen sınıflandırma" ya da "galaksi morfolojisi" projelerinden farklı, özgün bir uzay bilimi projesi. Beş fikir değerlendirildi:

| # | Fikir | Veri | Yöntem |
|---|---|---|---|
| **1** | **Güneş fırtınaları uyduları nasıl düşürüyor?** | GCAT, Space-Track, GFZ Kp/Ap | Fırtına öncesi / sonrası irtifa kaybı, şiddet-etki modeli |
| 2 | Pulsar sıçramaları ile depremler aynı yasaya mı uyuyor? | Jodrell Bank glitch kataloğu, ATNF, USGS | Gutenberg–Richter ve Omori karşılaştırması |
| 3 | Keşfedilmemiş meteor yağmuru avı | Global Meteor Network, IAU listesi, JPL | Yörünge benzerliğiyle kümeleme (HDBSCAN) |
| 4 | Ağaç halkalarında süper Güneş fırtınası izi | IntCal karbon-14, buz çekirdeği berilyum-10 | Anomali ve değişim noktası tespiti |
| 5 | Apollo Ay depremi verisini yeniden taramak | Apollo pasif sismik deney, Nakamura kataloğu | Şablon eşleştirmeli dedektör |

**Seçilen: 1.** Veri bol, hikâyesi güçlü, sonucu görsel ve güncel (25. Güneş döngüsünün zirvesi ve Mayıs 2024 süper fırtınası).

## 2. İlk analiz: katalog ve indeksler

`load.py` ve `analysis.py` ile üç soru yanıtlandı: Güneş döngüsü, fırtına sonrası düşüş sayısı ve Starlink fırlatmaları. Sonuçlar etkileşimli bir rapor panosunda toplandı (`page/index.html`).

**Yolda düzeltilen veri sorunları:**

- **Kayıp Starlink uyduları:** ilk denemede Şubat 2022 için 49 uydudan yalnızca 6'sının kaybı görünüyordu. Hızlı düşen uydular katalog numarası almadan GCAT'in ikinci kataloğuna (`auxcat`) yazılmıştı. İki katalog birleştirilince doğru sayı (38/49) geldi.
- **Fırtınayla ilgisiz kayıplar:** Starlink listesine yörüngeye hiç ulaşmayan uçuşlar ve Temmuz 2024'teki Falcon 9 üst kademe arızası karışmıştı. `U` etiketleri, 150 km'nin altındaki perijeler ve `2024-129` çıkarıldı.
- **Sıfıra yuvarlanan p değeri:** Fisher testinin çok küçük p değeri rapora 0 olarak gidiyordu; anlamlı basamakla yuvarlama eklendi.

## 3. Yörünge alçalması analizi

İlk analiz, tek fırtınanın düşüş **sayısı** üzerindeki etkisinin belirsiz olduğunu gösterdi (p = 0,082). Daha hassas soru: fırtına **yörüngeyi** ne kadar alçaltıyor?

- `st_plan.py`: 64 fırtına ve her birinde en fazla 400 obje seçildi.
- `spacetrack_fetch.py`: Space-Track'in tarihsel yörünge kayıtları (~1,8 milyon kayıt) indirildi. Kullanıcı adı ve şifre yalnızca terminalde soruluyor, hiçbir dosyaya yazılmıyor.
- `altitude.py`: her obje için fırtına haftası ile plasebo haftası karşılaştırıldı.

**Yöntemdeki hata ve düzeltmesi:** İlk sonuç fiziğe aykırıydı: orta ve en şiddetli fırtınalar aynı etkiyi veriyordu ve plasebo haftalarında bile sabit bir "fazla alçalma" (~1,39×) çıkıyordu. Neden: fırtına öncesi eğilimi ölçen 27 günlük uzun pencere, alçaldıkça hızlanan objelerin hızlanmasını yakalayamıyordu. Düzeltme:

1. Kısa ve fırtınaya yakın bir ön pencere (`[−14, −3]`),
2. Fırtına ve plasebo ölçümünün tamamen simetrik olması,
3. İstatistiksel birimin objeden haftaya taşınması (aynı haftadaki objeler birlikte dalgalanır; bağımsız saymak kesinliği abartıyordu).

Etkisi önceden bilinen yapay veriyle test edildi: gerçek oran ≈ 1,9, kod 1,8 buldu; plasebo haftalarında 1,0. Düzeltilmiş yöntemle sonuç: plasebo 0,95×, fırtına 1,30×, 64 fırtınanın 49'unda etki plasebodan büyük.

## 4. Etkileşimli sunum

Sonuçları anlatmak için tarayıcıda çalışan bir 3B sunum yapıldı. Dört sürümde gelişti:

| Sürüm | Eklenenler |
|---|---|
| **v1** | three.js sahnesi, 9 bölüm, zaman çizelgesi, telemetri, 3B'ye bağlı etiketler, 39 parçalı uydu sökümü, sentezlenmiş müzik |
| **v2** | İngilizce dil desteği; Natural Earth haritasıyla gerçek kıtalar ve sınırlar; bulut katmanı; canlı yer izi haritası; daha ayrıntılı uydu ve obje modelleri |
| **v3** | Yükleniyor ekranı; beş süre seçeneği (elle mod dahil); fırtına laboratuvarı; tıklayarak obje ve parça inceleme; bilgi paneli; grafiklerde üzerine gelme; yeniden yazılmış müzik motoru |
| **v4** | Her bölüme "Neye bak" satırı ve genişletilmiş ayrıntılar; bilgi paneline 64 fırtınalık sıralanabilir arşiv, fizik, NOAA ölçeği, tarihçe ve sık sorulanlar |

**Sunumda çözülen sorunlar:**

- **Aşırı parlaklık:** ışıklar ve ortam haritası yoğunluğu yeniden ayarlandı; bloom eşiği yalnızca gerçekten parlak öğeleri etkileyecek şekilde 1,5'e çekildi.
- **GTAO ve şeffaf katmanlar:** ortam gölgelemesi şeffaf kabuklarda leke bırakıyordu; bu nesneler gölgeleme geçişinden çıkarıldı.
- **Etiket çakışmaları:** 3B'ye bağlı etiketler kenar panellerin altında kalınca karşı tarafa geçecek şekilde düzenlendi.
- **Sıfır boyutlu çizim tamponu:** pencere boyutu henüz bilinmeden oluşturulan tamponlar uyarı veriyordu; ilk boyut pencereden alınıp korundu.
- **Ses atlaması:** zaman çizelgesinde atlarken müzik olayları üst üste çalıyordu; atlamada yeniden planlama eklendi.

## 5. Yayın

- **Railway:** statik site Caddy ile sunuluyor (`deploy/`). Adres: https://storm-and-orbit.up.railway.app
- **GitHub:** https://github.com/CodeByPinar/storm-and-orbit

## 6. Veri paylaşımı kararları

- **Space-Track** ham kayıtları kullanım koşulları gereği depoda ve sunumda yok; yalnızca hesaplanan özetler paylaşılıyor.
- **GCAT** ve **GFZ** verileri CC BY 4.0 lisanslı; analiz tekrarlanabilsin diye indirilen anlık görüntü depoda, atıflarıyla birlikte.
- Şifreler ve hesap bilgileri hiçbir dosyada yok.
