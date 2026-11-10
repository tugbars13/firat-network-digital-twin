# Topoloji Olgunlaştırma ve Doğrulama Raporu

**Tarih:** 10 Kasım 2026
**Kapsam:** Fırat Üniversitesi sentetik kampüs ağı topolojisinin incelenmesi, düzeltilmesi, cihaz/bağlantı modeline dönüştürülmesi ve otomatik doğrulanması.

> Bu çalışmada Fırat Üniversitesi'nin gerçek ağ altyapısı kullanılmamış ve gerçek ağ üzerinde test yapılmamıştır. Fakülte isimleri ve bina konumları kamuya açık kaynaklardan alınmıştır. Cihazlar, adresler, bağlantılar, kapasiteler ve telemetri sentetiktir.

Ayrıntılı ve otomatik üretilen sonuçlar `docs/dogrulama_raporu.md` dosyasındadır. Bu rapordaki sayılar o dosyadan alınmıştır.

> **İkinci denetim notu:** Bu rapor birinci denetimin kaydıdır ve olduğu gibi korunmuştur. İkinci denetimde `ACCESS` türü `ACCESS` (109) ve `SERVER_SWITCH` (2) olarak ayrıldı, `STACK` bağlantıları `ACCESS_RING` (10 Gbps) olarak yeniden adlandırıldı. Güncel durum için `docs/ikinci_denetim_raporu.md` dosyasına bakınız.

## 1. Düzeltilen hesaplama hataları

Veri merkezi dışındaki 19 binanın bütün değerleri (K1, K1b, K2, K3, K4, K5, K6, K7) bağımsız olarak yeniden hesaplandı ve hepsi kurallarla birebir uyumlu çıktı. Beklenen toplamlar da doğrulandı: veri merkezi hariç 20.900 kullanıcı ve 611 AP, dahil 21.020 kullanıcı ve 617 AP. Uyuşmazlıklar yalnızca veri merkezi satırında ve özet tablosundaydı.

| # | Sorun | Düzeltme |
|---|---|---|
| H1 | Veri merkezinin eşzamanlı cihaz sayısı normal yuvarlamayla hesaplanmıştı (86). Diğer satırlar yukarı yuvarlıyor. | Aynı kural uygulandı: ⌈72 × 1,2⌉ = **87** |
| H2 | Veri merkezinin port sayısı 0 yazılmıştı; 6 AP ve 60 kablolu uçla çelişiyordu. | K4 uygulandı: ⌈(6 + 60) × 1,2⌉ = **80** |
| H3 | Veri merkezinin switch sütununda (4) çekirdek ve sunucu switch'leri karışıktı. | Sütun artık yalnızca 2 sunucu switch'ini içeriyor; 2 çekirdek switch'i ayrıca sayılıyor. |
| H4 | Özet tablosunda bina sayısı veri merkezi hariç, kullanıcı ve AP sayısı veri merkezi dahil veriliyordu. | Özet, "hariç" ve "dahil" sütunlarıyla ayrı ayrı gösteriliyor. |
| H5 | Elle belirlenen ve hesaplanan değerler ayırt edilemiyordu. | `data/topoloji.csv` içine `deger_turu` sütunu eklendi. |
| H6 | Tablo ve harita betikleri dosyaları, çalıştırıldıkları klasöre göre okuyup yazıyordu; depo kökünden çalıştırıldıklarında yanlış yere yazıyorlardı. | Betikler artık her zaman `data/` ve `docs/` klasörlerini kullanıyor. |

Hiçbir binanın kodu, koordinatı, fakülte adı ya da bölgesi değiştirilmedi.

## 2. Güncellenen ve eklenen dosyalar

| Dosya | Durum | İçerik |
|---|---|---|
| `scripts/topoloji_uret.py` | Güncellendi | H1–H6 düzeltmeleri, A/B/C veri türleri bölümü |
| `data/topoloji.csv` | Yeniden üretildi | Bina tablosu + `deger_turu` sütunu |
| `docs/topoloji.md` | Yeniden üretildi | Kurallar, bina tablosu, ayrılmış özet |
| `scripts/topoloji_harita.py` | Güncellendi | Dosya yolları, lejant |
| `docs/diagrams/topoloji-harita.png` | Yeniden üretildi | Harita |
| `scripts/ag_modeli_uret.py` | **Yeni** | Cihaz ve bağlantı modeli üreticisi |
| `data/devices.csv` | **Yeni** | 733 cihaz |
| `data/links.csv` | **Yeni** | 763 bağlantı |
| `docs/ag_modeli.md` | **Yeni** | Cihaz, bağlantı, IP planı, yedeklilik ve kapasite açıklaması |
| `scripts/topoloji_dogrula.py` | **Yeni** | Otomatik doğrulama ve arıza analizi |
| `docs/dogrulama_raporu.md`, `data/dogrulama_sonuclari.json` | **Yeni** (otomatik) | Doğrulama sonuçları |
| `scripts/telemetri_uret.py` | **Yeni** | Sentetik telemetri üreticisi |
| `data/telemetri_semasi.json`, `docs/telemetri_semasi.md` | **Yeni** | Telemetri şeması ve senaryo mantığı |
| `data/ornek_telemetri.csv` | **Yeni** | 777 kayıtlık örnek |
| `docs/kaynaklar.md` | Güncellendi | A/B/C ayrımı, içerik doğrulama sütunu, kaynaksız varsayımlar |

Yeniden üretim sırası: `topoloji_uret.py` → `ag_modeli_uret.py` → `topoloji_dogrula.py` → `telemetri_uret.py` (isteğe bağlı: `topoloji_harita.py`).

## 3. Nihai bina, kullanıcı, AP ve switch toplamları

| Kalem | Veri merkezi hariç | Veri merkezi dahil |
|---|---|---|
| Bina | 19 | 20 |
| Tepe kullanıcı | 20.900 | 21.020 |
| Eşzamanlı cihaz (K1b) | 15.048 | 15.135 |
| Erişim noktası (AP) | 611 | 617 |
| Kablolu uç | 3.135 | 3.195 |
| Erişim katmanı switch'i | 109 | 111 (2'si sunucu switch'i) |
| Dağıtım switch'i | 3 | 3 |
| Çekirdek switch'i | — | 2 |

## 4. Cihaz envanteri toplamları

| Tür | Adet |
|---|---|
| CORE | 2 |
| DISTRIBUTION | 3 |
| ACCESS | 111 |
| AP | 617 |
| **Toplam** | **733** |

## 5. Bağlantı envanteri toplamları

| Tür | Adet | Not |
|---|---|---|
| AP_ACCESS | 617 | AP → erişim switch'i, 1 Gbps |
| STACK | 108 | Bina içi switch halkası, 40 Gbps |
| BUILDING_UPLINK | 27 | 19 birincil + 8 yedek, 10 Gbps |
| DIST_CORE | 6 | 3 birincil (CS01) + 3 yedek (CS02), 40 Gbps |
| SERVER_UPLINK | 4 | Sunucu switch'leri → iki çekirdek, 10 Gbps |
| CORE_INTERCONNECT | 1 | CS01 ↔ CS02, 40 Gbps |
| **Toplam** | **763** | Binalar arası fiber toplamı 18.887 m (K9) |

## 6. Yedekli bağlantıların doğrulama sonuçları

- **Bina yedek hatları:** Tanımlı 8 yedek hattın 8'i de, birincil hat koptuğunda binanın bütün AP'lerini çekirdeğe ulaştırıyor (otomatik test başarılı).
- **Dağıtım–çekirdek yedekleri:** 6 dağıtım–çekirdek hattından herhangi biri koptuğunda hiçbir bina etkilenmiyor.
- **Önceki tasarımda bulunan eksik:** Dağıtım switch'leri yalnızca BIDB-CS01'e bağlıyken, bu switch'in arızası veri merkezi dışındaki 19 binanın tamamını (611 AP) çevrimdışı bırakıyordu. "Yedekli çekirdek çifti" tabloda tanımlıydı ama grafikte gerçek bir alternatif yol yoktu. Her dağıtım switch'i CS02'ye de bağlanarak (tasarım kararı D1) bu sorun giderildi. Artık tek çekirdek arızasında hiçbir bina etkilenmiyor.
- **Yedek hattın çıktığı switch:** Yedek hat, birincil hattın çıktığı switch'ten değil ikinci switch'ten çıkıyor (tasarım kararı D2). Bu sayede yedekli binalarda birincil switch arızalandığında yalnızca o switch'e bağlı AP'ler (3–7 AP) etkileniyor, bina ayakta kalıyor.
- **İkili arızalar:** 741 kombinasyondan 27'si, tek arızaya dayanıklı 9 binadan en az birini çevrimdışı bırakıyor. En kötü durum, iki çekirdek switch'inin birlikte arızalanmasıdır.

## 7. Tek hata noktaları

Grafik analizinde **25** tek hata noktası bulundu. Hepsi yedek hattı olmayan 11 binayla ilgili (ILH, ECZ, MIM, AKM, MUZ, SPB, SAG, SUR, FEN, VET, ITB):

- Bu binaların birincil yukarı bağlantı switch'leri (AS01): 11
- Bu binaların birincil fiberleri: 11
- Dağıtım switch'leri: 3 (MUH-DS01 arızası 5 binayı, TEK-DS01 3 binayı, REK-DS01 3 binayı çevrimdışı bırakır)

Bu, K7 kuralının bilinçli bir sonucudur. Ayrıca:
- Her AP'nin tek bir erişim portu vardır; arızası yalnızca o AP'yi etkiler.
- İki çekirdek switch'i aynı binada (BIDB) bulunur ve çekirdek hatları aynı güzergâhı izler. Bina düzeyindeki bir olay iki çekirdeği birden etkileyebilir. Bu fiziksel risk grafikte görünmez, ayrıca not edilmiştir.

## 8. Kapasite modelinin değerlendirmesi

- **20:1 oranı** erişim katmanında, bina uç port kapasitesinin 10 Gbps yukarı bağlantıya oranı olarak kullanılır (Florwick & Whiteaker, 2013).
- **9 bina bu hedefi teorik olarak aşıyor:** MUH 39,4:1, TIP 32,2:1, IIBF 30,4:1, TEK 28,7:1, EGT 26,9:1, YEM 26,9:1, FEN 25,1:1, ITB 23,3:1, SAG 21,5:1. Bu durum gizlenmemiş, açık konu olarak kaydedilmiştir.
- **Beklenen trafik karşılanıyor:** Sentetik trafik varsayımıyla (cihaz başına 2 Mbps, kablolu uç başına 5 Mbps) hiçbir bina yukarı bağlantısı %50'nin üzerine çıkmıyor; en yüksek doluluk MUH'ta %48.
- **Dağıtım–çekirdek kapasitesi yeterli:** Tek 40G hatla oranlar 1,25:1–2,0:1, iki hat birlikte kullanılırsa 0,62:1–1,0:1. Beklenen trafik dağıtım başına 12–21 Gbps.
- **Arıza durumunda yük kayması:** En kötü durum TEK-DS01 arızasıdır. Bu durumda REK-DS01'in çekirdek hattı ~28,5 Gbps taşır (%71). Kapasite yetersizliği oluşmaz.

Bütün kapasite ve trafik değerleri sentetik tasarım parametreleridir.

## 9. Otomatik doğrulama testlerinin sonuçları

`scripts/topoloji_dogrula.py` 15 yapısal test çalıştırır. **15 testin 15'i başarılı.**

Testler: benzersiz cihaz ve bağlantı kimlikleri; bağlantı uçlarının geçerliliği; kendine bağlantı ve yinelenen bağlantı olmaması; izole cihaz olmaması; grafiğin tek parça olması; IP adreslerinin benzersiz ve özel olması; dağıtım–çekirdek ve çekirdek–çekirdek bağlantıları; envanterin `topoloji.csv` ile uyumu; K1–K5 hesaplarının yeniden doğrulanması; toplamların beklenen değerlerle uyumu; fiber uzunluklarının K9 ile tutarlılığı; yedek hatların gerçek alternatif yol oluşturması.

**Testlerin hata yakalayabildiğinin kontrolü:** Verinin bir kopyasına bilerek üç hata eklendi: bir bağlantının ucu var olmayan bir cihaza yönlendirildi, bir bağlantı kimliği yinelendi ve bir binanın AP sayısı bir artırıldı. Betik bu kopyada 5 testi başarısız raporladı ve 1 çıkış koduyla sonlandı. Yani testler hatayı gerçekten yakalıyor.

## 10. Hâlâ tasarım kararı bekleyen konular

| # | Konu | Seçenekler |
|---|---|---|
| P1 | Yedeksiz 11 binanın tek hata noktaları | (a) K7 eşiğini düşürerek daha fazla binaya yedek hat; (b) Cisco'nun önerdiği gibi her bölgeye ikinci bir dağıtım switch'i; (c) mevcut hâliyle kabul etmek ve gerekçelendirmek |
| P2 | 20:1 hedefini aşan 9 bina | Yedekli binalarda yedek hattı aktif kullanmak (yük paylaşımı) MUH, TIP, IIBF, TEK, EGT ve YEM'i hedefin altına indirir. Yedeksiz SAG, FEN ve ITB için ikinci bir 10 Gbps hat gerekir. Ya da hedef, beklenen trafiğe göre yeniden değerlendirilir. |
| P3 | Çekirdeğin fiziksel ortak riski | CS02'yi başka bir binaya taşımak ve çekirdek hatlarını farklı güzergâhtan geçirmek |
| P4 | Dağıtım–çekirdek hatlarının çalışma modu | Aktif–pasif (şu anki model) ya da aktif–aktif |
| P5 | Batfish–FRR aktarımı | Hatlar arası noktadan noktaya IP adreslemesi ve yönlendirme protokolünün (örn. OSPF) tanımlanması; ardından yapılandırma üretimi |
| P6 | Kaynaksız katsayılar | K3, K4, K5 ve K9 için kaynak taraması; Teare & Paquet (2006) tam metninin okunması |
| P7 | Merkez Yemekhane'nin konumu | Doğrulanmış konumla değiştirmek |
| P8 | Kullanıcı VLAN ve IP planı | Proje planındaki 3. kartta yapılacak |
