# Ağ Modeli: Cihazlar, Bağlantılar, Yedeklilik ve Kapasite

Bu belge `data/devices.csv` ve `data/links.csv` dosyalarındaki sentetik ağ modelini açıklar. Dosyalar `scripts/ag_modeli_uret.py` tarafından `data/topoloji.csv` girdisinden üretilir; elle düzenlenmez.

> **Önemli:** Fırat Üniversitesi'nin gerçek ağ altyapısı bu çalışmada kullanılmamıştır. Bu belgedeki bütün cihazlar, adresler, bağlantılar ve kapasiteler sentetik tasarım parametreleridir. Yalnızca bina konumları ve fakülte isimleri gerçek veriye dayanır (bkz. `docs/topoloji.md`, bölüm 0).

## 1. Cihaz envanteri (`data/devices.csv`)

| Tür (`device_type`) | Katman | Adet | Adlandırma | Açıklama |
|---|---|---|---|---|
| CORE | Çekirdek | 2 | `BIDB-CS01`, `BIDB-CS02` | Veri merkezinde yedekli çekirdek çifti |
| DISTRIBUTION | Dağıtım | 3 | `MUH-DS01` (Batı), `TEK-DS01` (Orta), `REK-DS01` (Doğu) | Her bölgede bir dağıtım switch'i |
| ACCESS | Erişim | 109 | `<BİNA>-AS01…` | 19 binadaki erişim switch'leri (K5) |
| SERVER_SWITCH | Veri merkezi | 2 | `BIDB-SS01`, `BIDB-SS02` | Veri merkezi sunucu switch'leri; iki çekirdeğe çift bağlı |
| AP | Kablosuz | 617 | `<BİNA>-AP001…` | K2'ye göre hesaplanan erişim noktaları |
| **Toplam** | | **733** | | |

Ek sütunlar: `role` (çekirdek, dağıtım, birincil/yedek yukarı bağlantı switch'i, sıradan erişim, sunucu, kablosuz) ve `floor` (erişim switch'leri ve AP'ler katlara sırayla dağıtılır).

### Yönetim IP planı (sentetik, RFC 1918)

| Blok | Kullanım |
|---|---|
| `10.0.0.0/24` | Çekirdek (`.1`, `.2`) ve dağıtım (`.11`–`.13`); bant dışı (out-of-band) yönetim ağı olarak düşünülmüştür |
| `10.1.<b>.0/24` | `b` numaralı binanın erişim/sunucu switch'leri |
| `10.2.<b>.0/24` | `b` numaralı binanın AP'leri |

`b`, binanın `data/topoloji.csv` içindeki sıra numarasıdır (BIDB = 1). Her blok en fazla 254 cihaz alır; en kalabalık bina 64 AP ve 10 switch içerir. Adreslerin benzersiz ve özel olduğu doğrulama betiğiyle sınanır. Kullanıcı VLAN'ları, noktadan noktaya hat adresleri ve OSPF tasarımı `docs/batfish_frr_hazirlik.md` belgesindedir.

## 2. Bağlantı envanteri (`data/links.csv`)

| Tür (`link_type`) | Uçlar | Adet | Kapasite | Fiber uzunluğu |
|---|---|---|---|---|
| CORE_INTERCONNECT | CS01 ↔ CS02 | 1 | 40 Gbps | Bina içi, tanımlanmadı |
| DIST_CORE | Dağıtım → CS01 (PRIMARY) ve CS02 (BACKUP) | 6 | 40 Gbps (K8) | K9, toplam 5.370 m |
| BUILDING_UPLINK | Bina AS01 → bölge dağıtımı (PRIMARY); AS02 → komşu bölge dağıtımı (BACKUP) | 19 + 8 = 27 | 10 Gbps (K8) | K9: birincil 5.888 m + yedek 7.629 m = 13.517 m (dağıtım switch'i aynı binadaysa bina içi) |
| SERVER_UPLINK | Sunucu switch'leri → CS01 ve CS02 | 4 | 10 Gbps | Bina içi, tanımlanmadı |
| ACCESS_RING | Bina içi, katlar arası erişim switch'i halkası | 108 | 10 Gbps | Bina içi, tanımlanmadı |
| AP_ACCESS | AP → aynı kattaki erişim switch'i | 617 | 1 Gbps | Bina içi bakır, tanımlanmadı |
| **Toplam** | | **763** | | Binalar arası fiber: 18.887 m |

Her bağlantının `srlg` sütunu, aynı fiziksel riski paylaşan bağlantıları gösterir (Shared Risk Link Group). Binalar arası hatta `SRLG-<bina1>-<bina2>`, bina içi bağlantıda `SITE-<bina>` yazılır. Aynı SRLG'yi paylaşan hatlar tek bir kazı ya da bina olayında birlikte kopar.

### 2.1 ACCESS_RING (eski adıyla STACK) neyi modelliyor?

İkinci denetimde 108 bağlantı tek tek incelendi. 18 binada n switch arasında n bağlantı vardır ve her biri tek bir kapalı döngüdür (halka). MUZ'da 2 switch ve 1 bağlantı vardır. 108 bağlantının 104'ü farklı katlardaki switch'leri birleştirir. Yani kod **fiziksel yığınlama (stacking)** modellemiyor: yığınlama, switch'leri arka paneldeki özel kablolarla tek bir mantıksal switch'e dönüştürür ve aynı dolapta yan yana duran cihazlar için kullanılır. Kodun yaptığı, katlar arasında **sıradan Ethernet bağlantılarıyla kurulmuş fiziksel bir halkadır**. Bu yüzden:

- Tür adı `STACK` → `ACCESS_RING` olarak değiştirildi; bağlantı sayısı (108) değişmedi.
- Kapasite 40 Gbps (yığınlama kablosu) yerine 10 Gbps (katlar arası fiber uplink) alındı.
- Halka bir Katman 2 döngüsüdür. Döngü, **RSTP (IEEE 802.1w)** ile engellenir: normalde halkadaki bir port bloklanır; bir bağlantı ya da switch koparsa bloklu port birkaç saniye içinde açılır. Katman 3 sınırı binanın yukarı bağlantı switch'lerindedir (AS01/AS02), bu yüzden Katman 2 bina dışına taşmaz.

Fiber uzunluğu yalnızca iki farklı binanın koordinatlarından K9 ile hesaplanabilen bağlantılar için yazılmıştır. Bina içi bağlantılarda uzunluk bilinmediği için boş bırakılmış, `length_basis` sütununda nedeni belirtilmiştir. Bu uzunluklar ölçüm değildir.

## 3. Yedeklilik mimarisi

### 3.1 Korunan ilişkiler

`data/topoloji.csv` içindeki birincil ve yedek bağlantı ilişkileri aynen korunmuştur: her bina bölgesinin dağıtım switch'ine bağlıdır, K7'yi sağlayan 8 bina (REK, MUH, EGT, IIBF, TEK, KUT, YEM, TIP) komşu bölgenin dağıtım switch'ine ikinci bir hatla bağlanır. Dağıtım switch'ini barındıran binalarda (MUH, TEK, REK) birincil hat bina içidir; bu binaların yedek hattı komşu bölgeye gider (MUH → TEK, TEK → REK, REK → TEK).

### 3.2 Graf üzerinde bulunan eksikler ve alınan tasarım kararları

Tablo düzeyinde "ikinci fiber var" demek gerçek yedeklilik anlamına gelmez. Model graf olarak kurulunca şu iki sorun ortaya çıktı:

**D1: Çekirdek tek hata noktasıydı (uygulandı).** Önceki tasarımda dağıtım switch'leri yalnızca çekirdeğe, pratikte tek bir çekirdek switch'ine bağlıydı. BIDB-CS01 arızalandığında veri merkezi dışındaki 19 binanın tamamı çevrimdışı kalıyordu (doğrulama raporu, S4 karşılaştırması). Çözüm olarak her dağıtım switch'i ikinci bir 40 Gbps hatla BIDB-CS02'ye de bağlandı (3 yeni bağlantı) ve iki çekirdek switch'i arasına 40 Gbps bağlantı eklendi. Bu bir **sentetik tasarım kararıdır**. Kaynak ve hedefler `data/links.csv` içinde `DIST_CORE / BACKUP` ve `CORE_INTERCONNECT` olarak yer alır. Sonuç: tek çekirdek arızasında hiçbir bina etkilenmez.

**D2: Yedek hat aynı switch'ten çıkmamalı (uygulandı).** Yedek hat, birincil hattın çıktığı switch'ten (AS01) çıksaydı, o switch arızalandığında yedek hat da işe yaramazdı. Bu yüzden yedek hat ikinci switch'ten (AS02) çıkar. Bina içindeki switch'ler katlar arası bir Ethernet halkasıyla (ACCESS_RING) birbirine bağlıdır, böylece AS01 arızalandığında diğer switch'ler AS02 üzerinden çekirdeğe ulaşır. Bu da bir sentetik tasarım kararıdır.

### 3.3 Arıza davranışı (özet)

Ayrıntılı ve otomatik üretilmiş sonuçlar `docs/dogrulama_raporu.md` dosyasındadır.

| # | Arıza | Sonuç |
|---|---|---|
| 1 | Bir binanın birincil yukarı bağlantı switch'i (AS01) | Yedekli 8 binada yalnızca o switch'e bağlı AP'ler etkilenir. Yedeksiz 11 binada bina tamamen çevrimdışı kalır. |
| 1b | Yukarı bağlantısı olmayan sıradan bir erişim switch'i | Yalnızca o switch'e bağlı AP'ler etkilenir (2–6 AP). |
| 2 | Bir binanın birincil fiberi | Yedekli 8 bina yedek hatla kesintisiz devam eder. Yedeksiz 11 bina çevrimdışı kalır. |
| 3 | Bir dağıtım switch'i | MUH-DS01: ILH, ECZ, MIM, AKM, MUZ çevrimdışı (97 AP). TEK-DS01: SPB, SAG, SUR çevrimdışı (71 AP). REK-DS01: FEN, VET, ITB çevrimdışı (105 AP). Dağıtım switch'ini barındıran binalar yedek hatla ayakta kalır. |
| 4 | Bir çekirdek switch'i | Hiçbir bina etkilenmez (D1 sayesinde). |
| 5 | Bir dağıtım–çekirdek hattı | Hiçbir bina etkilenmez (D1 sayesinde). |
| 6 | Aynı anda iki arıza | 741 kombinasyondan 27'si, tek arızaya dayanıklı 9 binadan en az birini çevrimdışı bırakır. En kötü durum iki çekirdek switch'inin birlikte arızalanmasıdır: bütün kampüs çevrimdışı olur. |

### 3.4 Kalan tek hata noktaları

25 tek hata noktası vardır ve hepsi **yedeksiz 11 binayla** ilgilidir:
- Bu binaların birincil yukarı bağlantı switch'leri (11)
- Bu binaların birincil fiberleri (11)
- Bu binaları barındıran bölgelerin dağıtım switch'leri (3)

Bunlar K7 kuralının bilinçli sonucudur: kullanıcı sayısı 1.500'ün altında olan ve kritik hizmet vermeyen binalara yedek hat çekilmemiştir. Ayrıca her AP tek bir porta bağlıdır; bir port ya da switch arızasında yalnızca o AP etkilenir. Bu, erişim katmanında kabul edilen bir durumdur.

### 3.5 Fiziksel ortak risk (ikinci denetimde modellendi)

İki çekirdek switch'i de aynı binada (BIDB) bulunur ve her dağıtım switch'inin iki çekirdek hattı aynı güzergâhı izler. Bu risk artık `srlg` sütunuyla modellenir ve doğrulama raporunun 6. bölümünde iki senaryo karşılaştırılır:

- **Senaryo A (mevcut, `data/`):** BIDB binasının tümüyle devre dışı kalması 20 binanın tamamını düşürür. Bir dağıtım switch'inin çekirdek güzergâhı kazıda kesilirse dağıtım switch'i çekirdekten kopar; bölgedeki binalar ancak yedek hatlı binaların içinden geçen transit yolla ayakta kalır. Batı bölgesinde bu yol yalnızca MUH'tan geçer ve beklenen yükün %120'sini taşıması gerekir.
- **Senaryo B (karşılaştırma, `data/senaryo_b/`):** CS02 Kütüphane (KUT) binasına taşınır. Konum ve uzunluklar sentetiktir. Cihaz kimliği karşılaştırma kolaylığı için `BIDB-CS02` olarak bırakılmıştır, fakat cihazın `building_id` değeri `KUT`'tur. BIDB kaybında kampüs ağı ayakta kalır, ancak sunucu switch'leri BIDB'de olduğu için veri merkezi servisleri yine kaybolur. Bedeli 1.922 m ek fiberdir (20.809 m).

Mevcut topoloji (A) değiştirilmemiştir; B yalnızca karar desteği için üretilir.

## 4. Kapasite ve aşırı abonelik modeli

Bütün kapasite değerleri **sentetik tasarım parametreleridir**, gerçek ölçüm değildir.

### 4.1 20:1 oranı nerede ve neye göre?

Cisco'nun yükseköğretim kablosuz ağ tasarım rehberi, erişim katmanı ağlarının ani ve dalgalı trafiğe karşı **20:1 aşırı abonelik** oranıyla tasarlandığını belirtir (Florwick & Whiteaker, 2013). Bu modelde oran **erişim katmanında, bina yukarı bağlantısı için** kullanılır:

> aşırı abonelik = binadaki uç portların toplam kapasitesi ÷ binanın yukarı bağlantı kapasitesi
> uç portlar = (AP + kablolu uç) × 1 Gbps; yukarı bağlantı = 10 Gbps

Oranın dayandığı varsayım: uçların hepsi aynı anda tam hızda veri göndermez. Bu yüzden teorik oran, beklenen trafikle birlikte değerlendirilir. Beklenen trafik = eşzamanlı kablosuz cihaz × 2 Mbps + kablolu uç × 5 Mbps (sentetik varsayım).

### 4.2 Sonuçlar

**Bina yukarı bağlantıları:** 9 binada teorik oran 20:1'i aşıyor: MUH (39,4:1), TIP (32,2:1), IIBF (30,4:1), TEK (28,7:1), EGT ve YEM (26,9:1), FEN (25,1:1), ITB (23,3:1), SAG (21,5:1). Beklenen trafik ise her binada 10 Gbps hattın %50'sinin altında kalıyor; en yüksek değer MUH'ta yaklaşık 4,8 Gbps (%48). Yani beklenen yük karşılanıyor, ama 20:1 tasarım hedefi bu 9 binada sağlanmıyor. Bu durum gizlenmemiş, "tasarım kararı bekleyen konular" arasına alınmıştır.

**Dağıtım katmanı:**

| Dağıtım | Bina | Giriş kapasitesi | Çekirdeğe (tek 40G) | Çekirdeğe (iki 40G) | Beklenen trafik |
|---|---|---|---|---|---|
| MUH-DS01 (Batı) | 6 | 60 Gbps | 1,5:1 | 0,75:1 | ~12,0 Gbps |
| TEK-DS01 (Orta) | 8 | 80 Gbps | 2,0:1 | 1,0:1 | ~21,0 Gbps |
| REK-DS01 (Doğu) | 5 | 50 Gbps | 1,25:1 | 0,62:1 | ~12,7 Gbps |

**Çekirdek ilişkisi:** Normal çalışmada her dağıtım switch'inin trafiği birincil hattan CS01'e gider; CS02 hattı bekleme (BACKUP) durumundadır. İki hattın aynı anda kullanılması (yük paylaşımı) bir tasarım seçeneğidir; kullanılırsa oranlar yukarıdaki "iki 40G" sütununa iner.

**Aktif-pasif ve aktif-aktif (ikinci denetim).** 20:1 bir *teorik port oranı göstergesidir*; beklenen kullanım ayrıca hesaplanır. Aktif-aktif çalışma kendiliğinden oluşmaz, yapılandırılması gerekir: binada VRRP ana yönlendiricisi VLAN bazında paylaştırılır (VLAN 100 öğrenci kablosuz → AS01; VLAN 110 personel kablosuz ve VLAN 200 kablolu → AS02) ve OSPF maliyetleri eşitlenir (ECMP). Aktif-aktif yalnızca yedek hatlı 8 binada teorik oranı yarıya indirir; 20:1'i aşan bina sayısı 9'dan 3'e (SAG, FEN, ITB) düşer. Bu üç bina yedeksiz olduğu için aktif-aktif onlara yardımcı olmaz. Ayrıntılı tablolar doğrulama raporunun 8. bölümündedir.

**Yedek hattın rolü:** Normal çalışmada bina yedek hatları trafik taşımaz. Birincil hat, birincil switch ya da bölgenin dağıtım switch'i arızalandığında trafik yedek hatta geçer ve komşu bölgenin dağıtım switch'ine yük biner. En kötü durum TEK-DS01 arızasıdır: Orta bölgenin yedekli binaları REK-DS01'e geçer ve REK-DS01'in çekirdek hattındaki beklenen trafik ~28,5 Gbps'ye çıkar (tek 40G hattın %71'i). Kapasite yetersizliği oluşmaz.

## 5. Batfish ve FRR için hazırlık

Adres ve yönlendirme verisi `scripts/adresleme_uret.py` ile `data/vlans.csv`, `data/p2p_links.csv` ve `data/routers.csv` dosyalarına üretilir. Tasarım `docs/batfish_frr_hazirlik.md` belgesindedir. Bu aşamada FRR yapılandırma dosyası **üretilmemiştir**.
