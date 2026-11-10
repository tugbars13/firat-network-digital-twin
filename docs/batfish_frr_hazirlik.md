# Batfish–FRR hazırlığı: adresleme ve yönlendirme tasarımı

> **Durum:** Bu belge yapılandırmanın dayanacağı **veri modelini** tanımlar. FRR yapılandırma dosyaları bu aşamada **üretilmemiştir**.
> Bütün adresler, VLAN'lar ve OSPF değerleri **sentetiktir**. Fırat Üniversitesi'nin gerçek adres planı ya da yönlendirme yapılandırması kullanılmamıştır.

Üretici betik: `scripts/adresleme_uret.py` (girdi: `data/topoloji.csv`, `data/devices.csv`, `data/links.csv`).
Doğrulama: `scripts/topoloji_dogrula.py`, test **T22** (çakışma, boyut, VIP, /31 ve yönlendirici sayısı kontrolleri).

## 1. Üretilen dosyalar

| Dosya | Satır | İçerik |
|---|---:|---|
| `data/vlans.csv` | 109 | Bina başına VLAN'lar: alt ağ, VRRP sanal adresi (VIP), fiziksel ağ geçidi adresleri, aktif-pasif ve aktif-aktif VRRP ana yönlendiricisi, ihtiyaç ve kapasite |
| `data/p2p_links.csv` | 34 | Omurga hatlarının /31 adresleri, OSPF alanı, ağ tipi, aktif-pasif ve aktif-aktif OSPF maliyetleri |
| `data/routers.csv` | 32 | OSPF yönlendiricileri: loopback, router-id, alan, komşu sayısı, VRRP rolü |

## 2. Temel tasarım kararı: Katman 3 sınırı bina içinde (routed access)

Binanın yukarı bağlantı switch'leri (AS01; yedek hatlı binalarda AS01 ve AS02) bina VLAN'larının ağ geçididir. Böylece:

- Katman 2 (VLAN'lar, RSTP) bina dışına taşmaz. Bir binadaki yayın fırtınası ya da döngü başka binayı etkilemez.
- Binalar arası bütün hatlar **yönlendirilmiş /31 hatlardır**; yedeklilik OSPF ile sağlanır, binalar arası STP gerekmez.
- Bina içindeki katlar arası halka (`ACCESS_RING`) bir Katman 2 döngüsüdür ve **RSTP (IEEE 802.1w)** ile korunur.

Bu nedenle OSPF yönlendiricisi sayısı 32'dir: 2 çekirdek + 3 dağıtım + 19 bina AS01 + 8 yedek hatlı binada AS02. Diğer 77 erişim switch'i Katman 2 switch'idir.

## 3. Adres blokları (RFC 1918)

| Blok | Kullanım | Not |
|---|---|---|
| `10.0.0.0/24` | Çekirdek ve dağıtım yönetimi (`devices.csv`) | Bant dışı (OOB) yönetim ağı varsayılır |
| `10.1.<b>.0/24` | VLAN 10 – switch yönetimi | `b` = binanın `topoloji.csv` sıra numarası |
| `10.2.<b>.0/24` | VLAN 11 – AP yönetimi | |
| `172.16.0.0/12` → bina başına bir `/20` | VLAN 100, 110, 200 – istemciler | `/20` içinden büyükten küçüğe ayrılır |
| `10.10.0.0/24` | VLAN 300 – veri merkezi sunucuları | Yalnızca BIDB |
| `10.253.<b>.0/29` | VLAN 900 – AS01–AS02 transit | Yalnızca yedek hatlı 8 bina |
| `10.254.0.0/24` | Loopback (`/32`) ve OSPF router-id | 32 adres |
| `10.255.0.0/24` | Omurga noktadan noktaya hatlar (`/31`, RFC 3021) | 34 hat, 68 adres |

## 4. VLAN tasarımı

Her binada aynı VLAN numaraları kullanılır; alt ağlar binaya özeldir.

| VLAN | Ad | Kimler | Boyutlandırma |
|---|---|---|---|
| 10 | YONETIM-SW | Erişim switch'leri | `/24`; cihazlar `.1`'den başlar |
| 11 | YONETIM-AP | AP'ler | `/24`; cihazlar `.1`'den başlar |
| 100 | OGRENCI-KABLOSUZ | Eşzamanlı kablosuz cihazların %85'i | (ihtiyaç × 1,25 + 3) adresi karşılayan en küçük önek |
| 110 | PERSONEL-KABLOSUZ | Eşzamanlı kablosuz cihazların %15'i | aynı kural |
| 200 | KABLOLU | Laboratuvar, ofis, yazıcı, kamera (K3) | aynı kural |
| 300 | SUNUCU | Veri merkezi sunucuları (yalnız BIDB) | `/24` |
| 900 | L3-TRANSIT | AS01–AS02 OSPF komşuluğu (yalnız yedek hatlı binalar) | `/29` |

%85/%15 öğrenci–personel ayrımı ve %25 adres payı **tasarım varsayımıdır** (bkz. `docs/kaynaklar.md`, bölüm 5).

**Ağ geçidi adresleri.** İkinci denetimde bir çakışma bulunup düzeltildi: yönetim VLAN'larında VIP önce `.1` seçilmişti, oysa `.1` bir switch'in ya da AP'nin yönetim adresiydi. Kural şimdi şöyledir:

| VLAN türü | VRRP sanal adresi (VIP) | Fiziksel ağ geçitleri | İstemci/cihaz adresleri |
|---|---|---|---|
| Yönetim (10, 11) | `.254` | Ağ geçidi switch'inin yönetim adresi bu ağdaysa o adres; değilse `.252` / `.253` | `.1`'den başlar |
| İstemci (100, 110, 200) ve sunucu (300) | `.1` | `.2` (AS01) ve `.3` (AS02) | DHCP havuzu `.4`'ten başlar |

T22, hiçbir VIP'in bir cihazın yönetim adresiyle aynı olmadığını sınar.

**Örnek – MUH (yedek hatlı, VRRP çifti):**

| VLAN | Alt ağ | VIP | AS01 / AS02 | İhtiyaç / kapasite | VRRP ana (aktif-pasif → aktif-aktif) |
|---|---|---|---|---|---|
| 10 | 10.1.3.0/24 | 10.1.3.254 | 10.1.3.1 / 10.1.3.2 | 10 / 251 | AS01 → AS01 |
| 11 | 10.2.3.0/24 | 10.2.3.254 | 10.2.3.252 / .253 | 64 / 251 | AS01 → AS01 |
| 100 | 172.16.32.0/21 | 172.16.32.1 | .2 / .3 | 1.347 / 2.043 | AS01 → AS01 |
| 110 | 172.16.42.0/23 | 172.16.42.1 | .2 / .3 | 237 / 507 | AS01 → **AS02** |
| 200 | 172.16.40.0/23 | 172.16.40.1 | .2 / .3 | 330 / 507 | AS01 → **AS02** |
| 900 | 10.253.3.0/29 | — | 10.253.3.1 / .2 | 2 / 6 | — |

**Örnek – ILH (yedeksiz, tek ağ geçidi):** VLAN 100 `172.16.48.0/22`, VLAN 110 `172.16.53.0/25`, VLAN 200 `172.16.52.0/24`; ağ geçidi yalnızca ILH-AS01, VRRP yoktur.

**Veri merkezi (BIDB):** VLAN'ların ağ geçidi CS01 ve CS02'dir (VRRP). SS01 ve SS02 iki çekirdeğe de bağlı olduğu için veri merkezinde de bir Katman 2 döngüsü oluşur (CS01–SS01–CS02–SS02); bu döngü de RSTP ile korunmalıdır.

## 5. Noktadan noktaya hatlar ve dağıtım/çekirdek IP planı

Omurga bağlantılarının her biri bir `/31` alır (`10.255.0.0/24` içinden, `links.csv` sırasıyla). Çift adres kaynak cihaza, tek adres hedef cihaza verilir.

| Hat türü | Adet | Örnek |
|---|---:|---|
| CORE_INTERCONNECT | 1 | L0001: BIDB-CS01 `10.255.0.0/31` ↔ BIDB-CS02 `10.255.0.1/31` |
| DIST_CORE | 6 | L0002: MUH-DS01 `10.255.0.2/31` ↔ BIDB-CS01 `10.255.0.3/31` |
| BUILDING_UPLINK | 27 | L0047: MUH-AS01 `10.255.0.18/31` ↔ MUH-DS01 `10.255.0.19/31`; L0048: MUH-AS02 `10.255.0.20/31` ↔ TEK-DS01 `10.255.0.21/31` |

**Loopback ve router-id:** CS01 `10.254.0.1`, CS02 `10.254.0.2`, MUH-DS01 `10.254.0.3`, REK-DS01 `10.254.0.4`, TEK-DS01 `10.254.0.5`; bina yönlendiricileri `10.254.0.6`'dan başlayarak alfabetik sırayla. Router-id loopback adresine eşittir; böylece arayüz kopsa da değişmez.

## 6. OSPF tasarımı

| Konu | Karar | Gerekçe |
|---|---|---|
| Protokol | OSPFv2 | FRR ve Batfish tarafından desteklenir; kampüs içi IGP olarak yaygındır |
| Alan | Tek alan, alan 0 | 32 yönlendirici ve 175 önek (109 VLAN + 34 hat + 32 loopback) küçük bir ağdır; çok alanlı tasarım karmaşıklık ekler. Büyürse bölge başına alan seçeneği açık bırakılmıştır |
| Ağ tipi | Omurga hatlarında `point-to-point` | DR/BDR seçimi gereksizdir, komşuluk daha hızlı kurulur |
| Pasif arayüzler | İstemci, yönetim ve sunucu VLAN'ları | Kullanıcı VLAN'larında OSPF komşuluğu kurulmaz; alt ağlar yalnızca duyurulur |
| Maliyet | Açıkça atanır (referans bant genişliğine bırakılmaz) | 10/40 Gbps hatlar varsayılan referansla aynı maliyeti alırdı |

**OSPF maliyetleri (`p2p_links.csv`):**

| Hat | Aktif-pasif | Aktif-aktif |
|---|---:|---:|
| Bina birincil hattı | 10 | 10 |
| Bina yedek hattı | 100 | 10 |
| Dağıtım → CS01 | 5 | 5 |
| Dağıtım → CS02 | 50 | 5 |
| Çekirdek arası | 5 | 5 |
| Bina içi transit (VLAN 900) | 10 | 10 |

**Komşuluklar (`routers.csv`, `ospf_neighbors`):** CS01 4 (3 dağıtım + CS02), CS02 4, MUH-DS01 8, REK-DS01 12, TEK-DS01 13. Yedeksiz bina AS01: 1. Yedek hatlı bina AS01 ve AS02: 2 (kendi dağıtımı + bina içi transit).

## 7. Yedek yönlendirme davranışı (beklenen)

Bu tablo Batfish ve FRR deneylerinde **sınanacak hipotezlerdir**; henüz çalıştırılmamıştır. Bağlılık sonuçları `docs/dogrulama_raporu.md` ile tutarlıdır.

| Arıza | Aktif-pasif davranış | Aktif-aktif davranış |
|---|---|---|
| Yedek hatlı binada birincil fiber | AS01'in yolu kaybolur; trafik VLAN 900 üzerinden AS02'ye, oradan yedek hatla diğer dağıtıma gider (maliyet 10 + 100). VRRP ana AS01'de kalır | VLAN 100 trafiği aynı şekilde AS02'ye kayar; 110/200 zaten AS02'dedir |
| Yedek hatlı binada AS01 arızası | VRRP AS02'ye geçer; AS01'e bağlı AP'ler kaybolur (her AP tek kabloyla bağlı) | Aynı; 110/200 için geçiş gerekmez |
| Yedeksiz binada birincil fiber ya da AS01 | Bina çevrimdışı; alternatif yol yoktur | Aynı |
| Dağıtım switch'i arızası | Yedek hatlı binalar yedek hatta geçer; yedeksiz binalar çevrimdışı | Aynı; yük yedek dağıtımda toplanır (en kötü TEK-DS01 arızasında REK-DS01 %71) |
| Bir dağıtım–çekirdek hattı | CS02 hattına geçiş (maliyet 50) | ECMP'nin bir yolu düşer, diğeri devam eder |
| Bir çekirdek switch'i | Diğer çekirdek devralır; BIDB VLAN'larında VRRP geçişi | Aynı |
| **Senaryo A: bir dağıtımın iki çekirdek hattı birlikte (aynı güzergâh)** | Dağıtım çekirdekten kopar. Tek OSPF alanında bina yönlendiricileri **transit** olur: DS → yedek hatlı binanın AS01'i → VLAN 900 → AS02 → diğer dağıtım → çekirdek. Batı bölgesinde bu yol yalnız MUH'tan geçer ve beklenen yükün %120'sini taşıması gerekir | Aynı yol, aynı darboğaz |

**Açık karar – erişim katmanı transit olsun mu?** Üç seçenek vardır:

1. **İzin ver (varsayılan alan 0 davranışı).** Yedek hat maliyeti 100 olduğu için transit yol yalnızca başka yol kalmadığında seçilir. Bağlılık korunur ama MUH darboğazı oluşur.
2. **Son çare yap (RFC 6987, OSPF stub router / `max-metric router-lsa`).** Bina yönlendiricileri en yüksek maliyetle duyurulur; transit yalnızca başka yol yoksa kullanılır. Bu topolojide sonuç 1. seçenekle aynıdır, ama niyeti açıkça yapılandırmaya yazar.
3. **Engelle.** Bina yönlendiricileri transit taşımaz; dağıtım güzergâhı kesilince yedeksiz binalar çevrimdışı kalır.

Senaryo B bu sorunu ortadan kaldırır, çünkü iki çekirdek hattı farklı güzergâhlardan gider. Seçim Batfish deneylerinden sonra yapılacaktır.

## 8. Sonraki adımlar (henüz yapılmadı)

1. `vlans.csv`, `p2p_links.csv` ve `routers.csv` dosyalarından her yönlendirici için FRR yapılandırması (`frr.conf`: arayüzler, `router ospf`, VRRP) üreten bir betik.
2. Batfish ile statik analiz: her VLAN alt ağının bütün yönlendiricilerden erişilebilir olması, OSPF komşuluklarının beklenen sayıda kurulması, çakışan adres olmaması, yukarıdaki arıza tablosunun Batfish'in `differentialReachability` sorgusuyla sınanması.
3. Containerlab ya da benzeri bir ortamda FRR ile dinamik deney: yakınsama süresi ve VRRP geçişinin ölçülmesi (sentetik ortamda).

## 9. Sınırlılıklar

- Katman 2 davranışı (RSTP, VRRP zamanlayıcıları) Batfish'in odak alanı değildir; bu kısım FRR/emülasyon aşamasında ele alınacaktır.
- İnternet çıkışı, güvenlik duvarı ve NAT modellenmemiştir.
- Bütün değerler sentetiktir ve gerçek kampüs yapılandırmasını temsil etmez.
