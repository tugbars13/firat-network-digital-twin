# Ağ Topolojisi Tablosu

Bu tablo Fırat Üniversitesi kampüs ağının sentetik (uydurma ama kurallı) modelidir. Cihaz sayıları aşağıdaki kurallardan hesaplanmıştır, elle yazılmamıştır.

## 0. Veri türleri

Fırat Üniversitesi'nin gerçek ağ altyapısı bu çalışmada kullanılmamıştır. Model üç tür veriden oluşur:

| Tür | İçerik | Kaynak |
|---|---|---|
| **A. Gerçek coğrafi veri** | Fakülte isimleri; bina konumları (Merkez Yemekhane hariç); iki yerleşkeli kampüs yapısı | Fırat Üniversitesi resmî sitesi (fakülte listesi: https://www.firat.edu.tr/tr/page/event/fakulteler-mezuniyet-toreni-ikinci-grup-7452; yerleşkeler: SKS Daire Başkanlığı sitesi); Google Haritalar, OpenStreetMap, Wikipedia (her binanın konum kaynağı tabloda) |
| **B. Sentetik tasarım parametresi** | Kat ve kullanıcı sayıları; AP, switch ve port sayıları; cihaz adları; IP adresleri; bağlantılar ve yedeklilik ilişkileri; hat kapasiteleri ve fiber uzunlukları | Bu belgedeki K1–K9 kuralları ve `docs/ag_modeli.md`; katsayıların bir kısmı kaynaklarla desteklenmiştir (bkz. `docs/kaynaklar.md`) |
| **C. Simülasyon verisi** | Gecikme, paket kaybı, trafik, CPU ve bellek kullanımı, arıza durumları | Henüz üretilmemiştir; şema ve senaryo mantığı `docs/telemetri_semasi.md` dosyasındadır |

## 1. Boyutlandırma kuralları

| Kural | Tanım | Gerekçe | Kaynak |
|---|---|---|---|
| K1 · Eşzamanlı kullanıcı | Tepe kullanıcı × 0,6 | Bir üniversitede gün içinde aynı anda bağlı kullanıcılar günlük kullanıcıların %33–58'i olarak ölçülmüştür; yoğun saate göre boyutlandırma için üst sınır alınmıştır | Okumura & Fujimura (2023); Mohottige vd. (2022) |
| K1b · Eşzamanlı cihaz | Eşzamanlı kullanıcı × 1,2 | Kişi başına 1,2–1,3 kablosuz cihaz ölçülmüştür; kullanıcılar genellikle birden fazla cihaz taşır | Okumura & Fujimura (2023); Cisco (2013) |
| K2 · Erişim noktası (AP) | max(⌈eşzamanlı cihaz ÷ 25⌉, kat sayısı) | Tipik ofis ortamında AP hücresi başına 20–30 kullanıcı; aralığın ortası alınmıştır; her katta en az bir AP | Cisco (2013) |
| K3 · Kablolu uç | ⌈tepe kullanıcı × 0,15⌉ | Laboratuvar bilgisayarları, ofisler, yazıcılar, kameralar | Tasarım varsayımı (kaynak aranıyor) |
| K4 · Port ihtiyacı | ⌈(AP + kablolu uç) × 1,2⌉ | Her AP bir port kullanır; %20 büyüme payı | Tasarım varsayımı (kaynak aranıyor) |
| K5 · Erişim switch'i | max(kat sayısı, ⌈port ÷ 48⌉) | 48 portlu switch; her katta en az bir kat dolabı | Tasarım varsayımı (kaynak aranıyor) |
| K6 · Bölge | Binanın gerçek boylamına göre: Batı (< 39,192), Orta (39,192–39,199), Doğu (> 39,199) | Batı bölgesi Mühendislik Yerleşkesi'ne, Orta ve Doğu Rektörlük Yerleşkesi'ne karşılık gelir | Bina konumları (bkz. bölüm 0) |
| K7 · Yedek hat | Tepe kullanıcı ≥ 1.500 **veya** kritik hizmet | Bu binalar komşu bölgenin dağıtım switch'ine ikinci bir fiber hatla da bağlanır | Tasarım kararı |
| K8 · Hat kapasitesi | Bina → dağıtım: 10 Gbps; dağıtım → çekirdek: 40 Gbps | Erişim katmanı yoğun trafiğe karşı 20:1 aşırı abonelik oranıyla tasarlanır | Cisco (2013) |
| K9 · Fiber uzunluğu | İki bina arası kuş uçuşu mesafe × 1,3 | Kablo yol ve kanal güzergâhını izlediği için %30 pay (güzergâh katsayısı) | Tasarım varsayımı (kaynak aranıyor) |

Kaynakların tam künyeleri `docs/kaynaklar.md` dosyasındadır.

## 2. Katman yapısı

| Katman | Cihaz | Konum |
|---|---|---|
| Çekirdek | BIDB-CS01, BIDB-CS02 (yedekli çift) | Bilgi İşlem Daire Başkanlığı |
| Dağıtım | MUH-DS01 (Batı), TEK-DS01 (Orta), REK-DS01 (Doğu) | Mühendislik Fakültesi, Teknoloji Fakültesi, Rektörlük |
| Erişim | Her binada K5'e göre hesaplanan switch'ler | Bina kat dolapları |
| Kablosuz | Her binada K2'ye göre hesaplanan AP'ler | Katlar |

## 3. Bina tablosu

| Kod | Bina | Yerleşke | Bölge (K6) | Kat | Tepe kullanıcı | AP (K2) | Erişim switch'i (K5) | Birincil bağlantı | Fiber (m, K9) | Yedek bağlantı (K7) | Fiber (m) | Konum kaynağı |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BIDB | Bilgi İşlem Daire Başkanlığı (veri merkezi) | Rektörlük Yerleşkesi | Çekirdek | 3 | 120 | 6 | 2 | — | — | — | — | Google Haritalar |
| REK | Rektörlük | Rektörlük Yerleşkesi | Doğu | 5 | 400 | 12 | 5 | Kendi binası (dağıtım burada) | — | TEK-DS01 (Orta) | 836 | Google Haritalar |
| MUH | Mühendislik Fakültesi | Mühendislik Yerleşkesi | Batı | 5 | 2.200 | 64 | 10 | Kendi binası (dağıtım burada) | — | TEK-DS01 (Orta) | 1295 | Google Haritalar (dekanlık) |
| ILH | İlahiyat Fakültesi | Mühendislik Yerleşkesi | Batı | 4 | 900 | 26 | 5 | MUH-DS01 (Batı) | 721 | Yok | — | Google Haritalar |
| ECZ | Eczacılık Fakültesi | Mühendislik Yerleşkesi | Batı | 3 | 500 | 15 | 3 | MUH-DS01 (Batı) | 526 | Yok | — | Google Haritalar |
| MIM | Mimarlık Fakültesi | Mühendislik Yerleşkesi | Batı | 4 | 700 | 21 | 4 | MUH-DS01 (Batı) | 468 | Yok | — | OpenStreetMap |
| AKM | Atatürk Kültür Merkezi | Mühendislik Yerleşkesi | Batı | 2 | 1.000 | 29 | 5 | MUH-DS01 (Batı) | 74 | Yok | — | Google Haritalar |
| MUZ | Arkeoloji ve Etnografya Müzesi | Mühendislik Yerleşkesi | Batı | 2 | 200 | 6 | 2 | MUH-DS01 (Batı) | 261 | Yok | — | Wikipedia |
| SPB | Spor Bilimleri Fakültesi | Rektörlük Yerleşkesi | Orta | 2 | 800 | 24 | 4 | TEK-DS01 (Orta) | 288 | Yok | — | Google Haritalar |
| EGT | Eğitim Fakültesi | Rektörlük Yerleşkesi | Orta | 4 | 1.500 | 44 | 7 | TEK-DS01 (Orta) | 186 | REK-DS01 (Doğu) | 921 | Google Haritalar |
| IIBF | İktisadi ve İdari Bilimler Fakültesi | Rektörlük Yerleşkesi | Orta | 4 | 1.700 | 49 | 8 | TEK-DS01 (Orta) | 521 | REK-DS01 (Doğu) | 1316 | Google Haritalar |
| SAG | Sağlık Bilimleri Fakültesi | Rektörlük Yerleşkesi | Orta | 4 | 1.200 | 35 | 6 | TEK-DS01 (Orta) | 416 | Yok | — | Google Haritalar |
| SUR | Su Ürünleri Fakültesi | Rektörlük Yerleşkesi | Orta | 3 | 400 | 12 | 3 | TEK-DS01 (Orta) | 486 | Yok | — | Google Haritalar |
| TEK | Teknoloji Fakültesi | Rektörlük Yerleşkesi | Orta | 4 | 1.600 | 47 | 8 | Kendi binası (dağıtım burada) | — | REK-DS01 (Doğu) | 836 | Google Haritalar |
| KUT | Merkez Kütüphane | Rektörlük Yerleşkesi | Orta | 4 | 900 | 26 | 5 | TEK-DS01 (Orta) | 168 | REK-DS01 (Doğu) | 750 | Google Haritalar |
| YEM | Merkez Yemekhane | Rektörlük Yerleşkesi | Orta | 2 | 1.500 | 44 | 7 | TEK-DS01 (Orta) | 287 | REK-DS01 (Doğu) | 650 | Tahmin (konum doğrulanamadı) |
| FEN | Fen Fakültesi | Rektörlük Yerleşkesi | Doğu | 4 | 1.400 | 41 | 7 | REK-DS01 (Doğu) | 401 | Yok | — | OpenStreetMap |
| VET | Veteriner Fakültesi | Rektörlük Yerleşkesi | Doğu | 3 | 900 | 26 | 5 | REK-DS01 (Doğu) | 228 | Yok | — | Google Haritalar |
| ITB | İnsan ve Toplum Bilimleri Fakültesi | Rektörlük Yerleşkesi | Doğu | 4 | 1.300 | 38 | 6 | REK-DS01 (Doğu) | 497 | Yok | — | Google Haritalar (İnsani ve Sosyal Bilimler adıyla) |
| TIP | Tıp Fakültesi | Rektörlük Yerleşkesi | Doğu | 6 | 1.800 | 52 | 9 | REK-DS01 (Doğu) | 360 | TEK-DS01 (Orta) | 1025 | Google Haritalar |

Eşzamanlı kullanıcı (K1), eşzamanlı cihaz (K1b), kablolu uç (K3) ve port (K4) ara değerleri `data/topoloji.csv` dosyasında yer alır. Her satırın `deger_turu` sütunu değerin kuralla mı hesaplandığını yoksa elle mi belirlendiğini gösterir.

**Veri merkezi (BIDB) satırı:** Eşzamanlı kullanıcı, eşzamanlı cihaz ve port sayısı diğer binalarla aynı kurallarla hesaplanır. AP sayısı (6), kablolu uç sayısı (60; sunucu ve depolama bağlantıları) ve switch sayısı (2 sunucu switch'i: BIDB-SS01, BIDB-SS02) elle belirlenmiştir, çünkü veri merkezinin ihtiyacı kullanıcı sayısından değil barındırdığı sistemlerden doğar. Çekirdek switch'leri (BIDB-CS01, BIDB-CS02) bu sayıya dahil değildir.

## 4. Özet

Tüm değerler doğrudan `data/topoloji.csv` satırlarından toplanmıştır.

| Kalem | Veri merkezi hariç | Veri merkezi dahil |
|---|---|---|
| Bina | 19 | 20 |
| Tepe kullanıcı | 20.900 | 21.020 |
| Eşzamanlı cihaz (K1b) | 15.048 | 15.135 |
| Erişim noktası (AP) | 611 | 617 |
| Kablolu uç | 3.135 | 3.195 |
| Erişim katmanı switch'i (ACCESS) | 109 | 109 |
| Veri merkezi sunucu switch'i (SERVER_SWITCH) | — | 2 |
| Dağıtım switch'i | 3 | 3 |
| Çekirdek switch | — | 2 |
| Yedek hattı olan bina | 8 (REK, MUH, EGT, IIBF, TEK, KUT, YEM, TIP) |
| Yedek hattı olmayan bina | 11 (ILH, ECZ, MIM, AKM, MUZ, SPB, SAG, SUR, FEN, VET, ITB) |
| Toplam bina fiberi | 13.517 m |

## 5. Bilinen sınırlamalar

- Kat sayıları ve kullanıcı sayıları temsilidir; gerçek kampüs verisi değildir.
- Her fakülte tek bina olarak modellenmiştir; birden fazla binası olan fakülteler tek noktada gösterilmiştir. Mühendislik Fakültesi için dekanlık binasının konumu kullanılmıştır.
- Merkez Yemekhane'nin konumu doğrulanamamış, kampüs ortasında tahmini bir nokta seçilmiştir.
- İnsan ve Toplum Bilimleri Fakültesi haritada "İnsani ve Sosyal Bilimler Fakültesi" adıyla bulunmuştur.
- Fırat Üniversitesi Hastanesi ayrı bina olarak modellenmemiş, Tıp Fakültesi kapsamında düşünülmüştür.
- Öğrenci yurtları modele alınmamıştır; devlet yurtları üniversiteye değil Kredi ve Yurtlar Kurumu'na bağlıdır.
- Model gerçek üniversite altyapısı üzerinde doğrulanmamıştır; tasarımın tutarlılığı yalnızca `scripts/topoloji_dogrula.py` ile otomatik olarak sınanmıştır.
- Yedeklilik ve kapasite değerlendirmesi `docs/ag_modeli.md` ve `docs/dogrulama_raporu.md` dosyalarındadır.
- K3, K4, K5 ve K9 katsayıları (0,15 · 1,2 · 48 · 1,3) henüz kaynakla desteklenmemiş tasarım varsayımlarıdır.
