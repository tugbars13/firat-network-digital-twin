# Ağ Topolojisi Tablosu

Bu tablo Fırat Üniversitesi kampüs ağının sentetik (uydurma ama kurallı) modelidir. Cihaz sayıları aşağıdaki kurallardan hesaplanmıştır, elle yazılmamıştır.

## 0. Veri kaynakları ve varsayımlar

| Bilgi | Kaynak | Durum |
|---|---|---|
| Fakülte listesi | Fırat Üniversitesi resmî sitesi (https://www.firat.edu.tr/tr/page/event/fakulteler-mezuniyet-toreni-ikinci-grup-7452) | Gerçek |
| Bina konumları | Google Haritalar ve OpenStreetMap (her binanın kaynağı tabloda) | Gerçek, yalnız Merkez Yemekhane tahmini |
| İki ana yerleşke (Mühendislik ve Rektörlük) | Fırat Üniversitesi SKS Daire Başkanlığı sitesi | Gerçek |
| Kat sayıları ve kullanıcı sayıları | — | Temsili varsayım |
| Ağ cihazları, bağlantılar, katsayılar | Bu belgedeki kurallar | Sentetik (projenin tasarımı) |

## 1. Boyutlandırma kuralları

| Kural | Tanım | Gerekçe |
|---|---|---|
| K1 · Eşzamanlı kullanıcı | Tepe kullanıcı × 0,6 | Tepe saatte binadakilerin yaklaşık %60'ı aynı anda ağa bağlı kabul edilmiştir |
| K2 · Erişim noktası (AP) | max(⌈eşzamanlı ÷ 30⌉, kat sayısı) | Bir AP ~30 kullanıcıya rahat hizmet verir; her katta en az bir AP |
| K3 · Kablolu uç | ⌈tepe kullanıcı × 0,15⌉ | Laboratuvar bilgisayarları, ofisler, yazıcılar, kameralar |
| K4 · Port ihtiyacı | ⌈(AP + kablolu uç) × 1,2⌉ | Her AP bir port kullanır; %20 büyüme payı |
| K5 · Erişim switch'i | max(kat sayısı, ⌈port ÷ 48⌉) | 48 portlu switch; her katta en az bir kat dolabı |
| K6 · Bölge | Binanın gerçek boylamına göre: Batı (< 39,192), Orta (39,192–39,199), Doğu (> 39,199) | Batı bölgesi Mühendislik Yerleşkesi'ne, Orta ve Doğu Rektörlük Yerleşkesi'ne karşılık gelir |
| K7 · Yedek hat | Tepe kullanıcı ≥ 1.500 **veya** kritik hizmet | Bu binalar komşu bölgenin dağıtım switch'ine ikinci bir fiber hatla da bağlanır |
| K8 · Hat kapasitesi | Bina → dağıtım: 10 Gbps; dağıtım → çekirdek: 40 Gbps | Kurumsal kampüs ağlarında yaygın değerler |
| K9 · Fiber uzunluğu | İki bina arası kuş uçuşu mesafe × 1,3 | Kablo yol ve kanal güzergâhını izlediği için %30 pay |

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
| BIDB | Bilgi İşlem Daire Başkanlığı (veri merkezi) | Rektörlük Yerleşkesi | Çekirdek | 3 | 120 | 6 | 4 | — | — | — | — | Google Haritalar |
| REK | Rektörlük | Rektörlük Yerleşkesi | Doğu | 5 | 400 | 8 | 5 | Kendi binası (dağıtım burada) | — | TEK-DS01 (Orta) | 836 | Google Haritalar |
| MUH | Mühendislik Fakültesi | Mühendislik Yerleşkesi | Batı | 5 | 2.200 | 44 | 10 | Kendi binası (dağıtım burada) | — | TEK-DS01 (Orta) | 1295 | Google Haritalar (dekanlık) |
| ILH | İlahiyat Fakültesi | Mühendislik Yerleşkesi | Batı | 4 | 900 | 18 | 4 | MUH-DS01 (Batı) | 721 | Yok | — | Google Haritalar |
| ECZ | Eczacılık Fakültesi | Mühendislik Yerleşkesi | Batı | 3 | 500 | 10 | 3 | MUH-DS01 (Batı) | 526 | Yok | — | Google Haritalar |
| MIM | Mimarlık Fakültesi | Mühendislik Yerleşkesi | Batı | 4 | 700 | 14 | 4 | MUH-DS01 (Batı) | 468 | Yok | — | OpenStreetMap |
| AKM | Atatürk Kültür Merkezi | Mühendislik Yerleşkesi | Batı | 2 | 1.000 | 20 | 5 | MUH-DS01 (Batı) | 74 | Yok | — | Google Haritalar |
| MUZ | Arkeoloji ve Etnografya Müzesi | Mühendislik Yerleşkesi | Batı | 2 | 200 | 4 | 2 | MUH-DS01 (Batı) | 261 | Yok | — | Wikipedia |
| SPB | Spor Bilimleri Fakültesi | Rektörlük Yerleşkesi | Orta | 2 | 800 | 16 | 4 | TEK-DS01 (Orta) | 288 | Yok | — | Google Haritalar |
| EGT | Eğitim Fakültesi | Rektörlük Yerleşkesi | Orta | 4 | 1.500 | 30 | 7 | TEK-DS01 (Orta) | 186 | REK-DS01 (Doğu) | 921 | Google Haritalar |
| IIBF | İktisadi ve İdari Bilimler Fakültesi | Rektörlük Yerleşkesi | Orta | 4 | 1.700 | 34 | 8 | TEK-DS01 (Orta) | 521 | REK-DS01 (Doğu) | 1316 | Google Haritalar |
| SAG | Sağlık Bilimleri Fakültesi | Rektörlük Yerleşkesi | Orta | 4 | 1.200 | 24 | 6 | TEK-DS01 (Orta) | 416 | Yok | — | Google Haritalar |
| SUR | Su Ürünleri Fakültesi | Rektörlük Yerleşkesi | Orta | 3 | 400 | 8 | 3 | TEK-DS01 (Orta) | 486 | Yok | — | Google Haritalar |
| TEK | Teknoloji Fakültesi | Rektörlük Yerleşkesi | Orta | 4 | 1.600 | 32 | 7 | Kendi binası (dağıtım burada) | — | REK-DS01 (Doğu) | 836 | Google Haritalar |
| KUT | Merkez Kütüphane | Rektörlük Yerleşkesi | Orta | 4 | 900 | 18 | 4 | TEK-DS01 (Orta) | 168 | REK-DS01 (Doğu) | 750 | Google Haritalar |
| YEM | Merkez Yemekhane | Rektörlük Yerleşkesi | Orta | 2 | 1.500 | 30 | 7 | TEK-DS01 (Orta) | 287 | REK-DS01 (Doğu) | 650 | Tahmin (konum doğrulanamadı) |
| FEN | Fen Fakültesi | Rektörlük Yerleşkesi | Doğu | 4 | 1.400 | 28 | 6 | REK-DS01 (Doğu) | 401 | Yok | — | OpenStreetMap |
| VET | Veteriner Fakültesi | Rektörlük Yerleşkesi | Doğu | 3 | 900 | 18 | 4 | REK-DS01 (Doğu) | 228 | Yok | — | Google Haritalar |
| ITB | İnsan ve Toplum Bilimleri Fakültesi | Rektörlük Yerleşkesi | Doğu | 4 | 1.300 | 26 | 6 | REK-DS01 (Doğu) | 497 | Yok | — | Google Haritalar (İnsani ve Sosyal Bilimler adıyla) |
| TIP | Tıp Fakültesi | Rektörlük Yerleşkesi | Doğu | 6 | 1.800 | 36 | 8 | REK-DS01 (Doğu) | 360 | TEK-DS01 (Orta) | 1025 | Google Haritalar |

Eşzamanlı kullanıcı (K1), kablolu uç (K3) ve port (K4) ara değerleri `data/topoloji.csv` dosyasında yer alır. Veri merkezi satırı kurallarla değil, elle belirlenmiştir: 2 çekirdek ve 2 sunucu switch'i.

## 4. Özet

| Kalem | Toplam |
|---|---|
| Bina (veri merkezi hariç) | 19 |
| Tepe kullanıcı | 21.020 |
| Erişim noktası | 424 |
| Erişim switch'i | 103 |
| Dağıtım switch'i | 3 |
| Çekirdek switch | 2 |
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
- Dağıtım switch'ini barındıran binalar (MUH, TEK, REK) kendi switch'leri arızalanırsa yedek hatla komşu bölgeye geçer.
- Katsayılar (0,6 · 30 · 0,15 · 1,2 · 1,3) varsayımdır ve raporda kaynakla desteklenmelidir.
