# İkinci Teknik Denetim ve Topoloji İyileştirmesi

**Tarih:** 10 Kasım 2026
**Kapsam:** Mevcut topolojinin korunarak denetlenmesi. Bina kodları, cihazlar, bağlantılar ve doğrulama yapısı yeniden kurulmadı; yalnızca aşağıda gerekçesi yazılan değişiklikler yapıldı.

> Bu çalışmada Fırat Üniversitesi'nin gerçek ağ altyapısına ait **hiçbir veri yoktur**. Fakülte isimleri ve bina konumları kamuya açık kaynaklardan alınmıştır; cihazlar, adresler, bağlantılar, uzunluklar, kapasiteler, Senaryo B ve OSPF değerleri sentetiktir. Hiçbir uzunluk ölçüm olarak sunulmamıştır.

Otomatik üretilen ayrıntılar: `docs/dogrulama_raporu.md` (23 test, senaryolar, tablolar) ve `docs/mutasyon_testi.md` (hata enjeksiyonu). Bu rapordaki sayılar o dosyalardan alınmıştır.

## Özet

| # | Konu | Bulgu | Yapılan |
|---|---|---|---|
| 1 | SERVER_SWITCH | Veri merkezi switch'leri ACCESS olarak sayılıyordu (111) | Ayrı tür: ACCESS 109 + SERVER_SWITCH 2. Toplam 733 değişmedi |
| 2 | STACK | 108 bağlantı yığınlama değil, katlar arası Ethernet halkası | `ACCESS_RING`, 10 Gbps, RSTP ile döngü önleme. Sayı değişmedi |
| 3 | Fiber | 13.517 m ile 18.887 m farkı kapsamdan geliyor | Bileşenlere ayrıldı, karşılaştırma tablosu eklendi |
| 4 | 8 ve 9 bina | 8 = yedek hatlı bina; 9 = 8 + veri merkezi | Bina bazında dört ayrı arıza testi ve sınıflandırma |
| 5 | Fiziksel risk | A'da BIDB kaybı 20 binayı düşürüyor; güzergâh kesintisinde bina transiti ve MUH darboğazı (%120) | SRLG sütunu, Senaryo B (karşılaştırma) |
| 6 | Kapasite | 20:1 teorik oran ile beklenen kullanım karıştırılmamalı | Aktif-pasif / aktif-aktif ayrı hesap; 9 → 3 bina |
| 7 | Batfish–FRR | Adres planı yoktu | VLAN, /31, loopback, OSPF verisi; yapılandırma üretilmedi |
| 8 | Testler | 15 test | 23 test + 15 mutasyon; hepsi geçti, kontrol temiz |
| — | Ek bulgu | Yönetim VLAN'larında VIP (`.1`) bir cihaz adresiyle çakışıyordu | VIP `.254` yapıldı; T22 bunu sınıyor |

## 1. SERVER_SWITCH ve ACCESS ayrımı

**Sorun.** `BIDB-SS01` ve `BIDB-SS02` erişim katmanında değil, veri merkezinde sunucuları bağlıyor ve iki çekirdeğe de bağlılar. ACCESS olarak sayılmaları "109 erişim switch'i (K5)" ile "111 ACCESS" arasında açıklanamayan bir fark doğuruyordu.

**Yapılan.** `device_type = SERVER_SWITCH`, `layer = Veri merkezi`. Doğrulayıcıdaki etki hesabı, envanter testi ve tek hata noktası taraması bu türü kapsayacak biçimde güncellendi.

| Tür | Adet |
|---|---:|
| CORE | 2 |
| DISTRIBUTION | 3 |
| ACCESS | 109 |
| SERVER_SWITCH | 2 |
| AP | 617 |
| **Toplam** | **733** |

**Test:** T16 (sayılar, BIDB'de ACCESS bulunmaması, SS'lerin iki çekirdeğe bağlı olması). Mutasyon M6: SS02 tekrar ACCESS yapılınca T16 başarısız oluyor.

## 2. STACK bağlantılarının denetimi

**Kod gerçekte neyi modelliyor?** 108 bağlantı tek tek incelendi:

- 18 binada n switch arasında n bağlantı var ve hepsi **tek bir kapalı döngü**.
- MUZ'da 2 switch arasında 1 bağlantı var.
- 108 bağlantının 104'ü **farklı katlardaki** switch'leri birleştiriyor.

Üç kavramın farkı:

| Kavram | Ne demek | Bu modelde |
|---|---|---|
| Fiziksel yığınlama (stacking) | Aynı dolaptaki switch'ler özel arka panel kablolarıyla tek mantıksal switch olur | **Hayır.** Switch'ler farklı katlarda |
| Sıradan Ethernet bağlantısı | İki switch arasında standart port ve kablo | **Evet**, her bağlantı böyle |
| Fiziksel halka | Ethernet bağlantıları kapalı bir döngü oluşturur | **Evet**, 18 binada |

**Döngü nasıl önleniyor?** Halka bir Katman 2 döngüsüdür. RSTP (IEEE 802.1w) normalde halkadaki bir portu bloklar; bir bağlantı ya da switch koparsa bloklu port açılır. Katman 3 sınırı bina içinde olduğu için (bkz. bölüm 7) döngü bina dışına taşmaz.

**Yapılan.** Tür adı `ACCESS_RING`; kapasite 40 Gbps yerine 10 Gbps. **Sayı varsayımla değiştirilmedi** (108).

**Test:** T17 (STACK kalmadı, uçlar aynı binada ve ACCESS türünde, n switch'te n bağlantı, tek döngü, toplam 108). Mutasyon M7 (bir bağlantı STACK'e geri yazıldı) ve M8 (bir bağlantı silindi, döngü kırıldı) yakalanıyor.

## 3. Fiber uzunluğu ayrıştırması

K9 (koordinatlar arası mesafe × 1,3) **yalnızca iki farklı binayı birleştiren** hatlara uygulanır. Bina içi bağlantılarda uzunluk tanımlanmamıştır; kat planı verisi yoktur.

| Bileşen | Hat | Uzunluk (A) |
|---|---:|---:|
| Bina birincil hattı | 19 (16'sı binalar arası) | 5.888 m |
| Bina yedek hattı | 8 | 7.629 m |
| Dağıtım → CS01 | 3 | 2.685 m |
| Dağıtım → CS02 | 3 | 2.685 m |
| Veri merkezi | 5 | tanımsız (bina içi) |
| Bina içi (halka + AP) | 725 | tanımsız |
| **Toplam** | | **18.887 m** |

**Eski ve yeni:**

| | Eski | Yeni | Fark |
|---|---:|---:|---:|
| Bina hatları (birincil + yedek) | 13.517 | 13.517 | 0 |
| Dağıtım–çekirdek | sayılmamıştı | 5.370 | +5.370 |
| **Toplam** | **13.517** | **18.887** | **+5.370** |

Fark yalnızca kapsamdan gelir; hiçbir hattın uzunluğu değişmemiştir. Ek bilgi: Senaryo A'da her dağıtımın iki çekirdek hattı aynı güzergâhtadır. Kazı açısından farklı güzergâh toplamı 16.202 m'dir (27 güzergâh).

**Test:** T20 (birincil + yedek = 13.517; + dağıtım–çekirdek + veri merkezi = toplam; uzunluk yalnız K9 hatlarında). Mutasyon M11 yakalanıyor.

## 4. 8 yedek hatlı bina ve 9 dayanıklı bina

Her bina için dört arıza **ayrı ayrı** uygulandı: birincil fiber, birincil erişim switch'i (AS01), bölge dağıtım switch'i, çekirdek (CS01 ve CS02 ayrı). Tam tablo doğrulama raporunun 5. bölümündedir.

| Sınıf | Bina | Birincil fiber | AS01 | Dağıtım | Çekirdek |
|---|---|---|---|---|---|
| Hat + dağıtım + çekirdek yedekli (8) | REK, MUH, EGT, IIBF, TEK, KUT, YEM, TIP | ayakta | **kısmi** | ayakta | ayakta |
| Veri merkezi, çift bağlı (1) | BIDB | ayakta | kısmi | uygulanamaz | ayakta |
| Yalnızca çekirdek yedekli (11) | ILH, ECZ, MIM, AKM, MUZ, SPB, SAG, SUR, FEN, VET, ITB | çevrimdışı | çevrimdışı | çevrimdışı | ayakta |

**Açıklama.** "8" yedek hattı olan binaların sayısıdır (K7). "9", hiçbir tek altyapı arızasında çevrimdışı kalmayan binaların sayısıdır; dokuzuncu bina BIDB'dir, çünkü sunucu switch'leri iki çekirdeğe ayrı ayrı bağlıdır. Yedeklilik yalnızca gerçekten alternatif yol olan yerde iddia edilmiştir. Yedek hatlı binalarda bile AS01 arızası **kısmi** kayba yol açar (o switch'e bağlı AP'ler), çünkü AP'ler tek kabloyla bağlıdır.

**Test:** T18 (K7 kümesi = BACKUP hattı olan binalar = testle hat ve dağıtım yedekli binalar = 8; dayanıklı küme = 8 + BIDB). Mutasyonlar M5 (yedek hat birincil ile aynı dağıtıma bağlandı) ve M9 (KUT yedek hattı silindi) T18 tarafından yakalanıyor.

> **Dürüst not (M5):** Yedek hat birincil ile *aynı* dağıtıma bağlanınca T15 ("yedek hat birincil fiber kopunca binayı ayakta tutuyor") başarılı kalıyor; bu doğru bir sonuçtur, çünkü fiber arızası gerçekten karşılanıyor. Hatayı dağıtım arızasını da sınayan T18 yakalıyor. Bu, iki testin farklı şeyleri ölçtüğünü gösteriyor.

## 5. Fiziksel çekirdek riski: Senaryo A ve B

**A (mevcut):** CS01 ve CS02 aynı binada (BIDB). **B (karşılaştırma):** CS02 Kütüphane'de (KUT). B'nin konumu ve uzunlukları **sentetik varsayımdır**; mevcut topoloji değiştirilmedi. B, `data/senaryo_b/` klasöründe ayrı üretilir ve cihaz kimliği karşılaştırma kolaylığı için `BIDB-CS02` olarak kalır.

| Olay | A | B |
|---|---|---|
| BIDB binası tümüyle devre dışı | **20 bina çevrimdışı** (tüm kampüs) | Yalnız BIDB (6 AP, 2 sunucu switch'i) |
| KUT binası tümüyle devre dışı | Yalnız KUT | Yalnız KUT |
| CS01 ve CS02 cihaz arızası | Tüm kampüs | Tüm kampüs |
| Bir dağıtımın çekirdek güzergâhı kazıda kesilir | Dağıtım çekirdekten kopar; bina transiti gerekir (aşağıda) | Tek hat kopar, transit gerekmez |
| Ek fiber | — | +1.922 m (20.809 m) |

**Yeni bulgu: bina üzerinden transit.** Senaryo A'da bir dağıtımın iki çekirdek hattı birlikte kesildiğinde bağlılık testi binaları "ayakta" gösteriyor. Neden: tek OSPF alanında trafik DS → yedek hatlı bir binanın AS01'i → bina içi → AS02 → diğer dağıtım → çekirdek yolunu izleyebilir. Bu yol gerçektir ama 10 Gbps bina hatlarıyla sınırlıdır:

| Kopan dağıtım | Transit binalar | Kapasite | Yük | Kullanım |
|---|---|---:|---:|---:|
| MUH-DS01 | MUH | 10 Gbps | 12,04 Gbps | **%120 (aşırı yük)** |
| TEK-DS01 | EGT, IIBF, TEK, KUT, YEM | 50 Gbps | 21,03 Gbps | %42 |
| REK-DS01 | REK, TIP | 20 Gbps | 12,71 Gbps | %64 |

Bu nedenle "ayakta" sonucu Batı bölgesi için yanıltıcı olurdu; rapor bunu ayrıca gösterir. Erişim katmanının transit olup olmayacağı Batfish–FRR aşamasında seçilecektir (`docs/batfish_frr_hazirlik.md`, bölüm 7).

**B'nin sınırı.** Sunucu switch'leri BIDB'de kaldığı için B, BIDB kaybında veri merkezi servislerini korumaz; yalnızca kampüs ağının bağlantısını korur. Servisleri korumak ikinci bir veri merkezi gerektirir ve kapsam dışıdır.

**Test:** T19 (SRLG her bağlantıda tanımlı; A'da BIDB kaybı 20 binayı düşürür; A'da güzergâh kesintisi transit gerektirir; B'de tek bina ya da güzergâh kaybı başka binayı düşürmez ve transit gerektirmez) ve T23 (B'nin envanteri A ile aynı, yalnız CS02'nin binası değişik). Mutasyonlar M10 ve M15 yakalanıyor.

## 6. Kapasite

Bütün trafik değerleri **sentetik parametredir**: eşzamanlı kablosuz cihaz başına 2 Mbps, kablolu uç başına 5 Mbps, uç port 1 Gbps.

- **Teorik oran (port göstergesi)** = uç port kapasitesi / etkin yukarı bağlantı. Trafik değildir.
- **Beklenen kullanım** = beklenen trafik / hat kapasitesi.

| | Aktif-pasif | Aktif-aktif |
|---|---|---|
| Nasıl çalışır | Yedek hat yalnız arızada taşır (OSPF maliyeti 100) | İki hat birlikte taşır |
| Ne gerekir | Varsayılan | **Yapılandırılmalı:** VRRP ana yönlendiricisi VLAN bazında bölünür (100 → AS01; 110, 200 → AS02), OSPF maliyetleri eşitlenir |
| 20:1'i aşan bina | 9 (MUH 39,4; TIP 32,2; IIBF 30,4; TEK 28,7; EGT, YEM 26,9; FEN 25,1; ITB 23,3; SAG 21,5) | 3 (SAG, FEN, ITB; üçü de yedeksiz) |
| En yüksek beklenen kullanım | MUH %48 | MUH hat 1 %27, hat 2 %21 |
| N-1 (bir hat kopunca) | — | En kötü MUH %48 |

Dağıtım → çekirdek: aktif-pasifte en yüklü TEK-DS01 %53 (40 Gbps), aktif-aktifte (ECMP, 80 Gbps) %23. En kötü dağıtım arızasında (TEK-DS01) REK-DS01'e 28,48 Gbps biner (%71). Kampüs toplam beklenen yükü 45,78 Gbps'dir.

**Sonuç.** Beklenen yük her durumda karşılanıyor. 20:1 tasarım göstergesi aktif-pasifte 9 binada sağlanmıyor. Aktif-aktif bunu 3'e indiriyor, ama yalnızca yapılandırılırsa. Kalan üç bina için çözüm yukarı bağlantı hızını artırmak ya da yedek hat eklemektir. Bu bir tasarım kararıdır ve henüz verilmemiştir.

**Test:** T21 (AP ve AA oranları, AA yükünün VLAN modelinden bağımsız yeniden hesaplanması, N-1 ≤ %100). Mutasyon M12 (bölüşüm bozuldu) yakalanıyor.

## 7. Batfish–FRR hazırlığı

`scripts/adresleme_uret.py` ile üç dosya üretildi: `data/vlans.csv` (109 VLAN), `data/p2p_links.csv` (34 /31 hat), `data/routers.csv` (32 OSPF yönlendiricisi). Tasarım `docs/batfish_frr_hazirlik.md` belgesindedir: bina VLAN'ları, yönetim VLAN'ları, sunucu VLAN'ı, kablosuz istemci VLAN'ları, /31 hatlar, loopback planı, tek alanlı OSPF, açık maliyetler ve yedek yönlendirme davranışı. **FRR yapılandırması üretilmedi.**

**Ek bulgu ve düzeltme.** Denetim sırasında yönetim VLAN'larında VRRP sanal adresinin `.1` seçildiği, oysa `.1`'in bir switch'in ya da AP'nin yönetim adresi olduğu görüldü. VIP `.254` yapıldı; fiziksel ağ geçidi adresleri ayrı bir sütuna (`gateway_ips`) yazıldı.

**Test:** T22 (her omurga hattı için bir /31, uçlar OSPF yönlendiricisi, alt ağ çakışması yok, loopback tekrarı yok, VLAN boyutları yeterli, VIP–yönetim adresi çakışması yok, VLAN kümesi doğru, yönlendirici sayısı 32). Mutasyonlar M13 ve M14 yakalanıyor.

## 8. Testler ve hata enjeksiyonu

- Mevcut 15 test (T1–T15) aynen korundu.
- Yeni testler: T16 SERVER_SWITCH/ACCESS, T17 halka tutarlılığı, T18 yedeklilik sınıflandırması, T19 fiziksel ortak arıza, T20 fiber bileşenleri, T21 aktif-pasif/aktif-aktif kapasite, T22 adresleme, T23 Senaryo B envanteri.
- **Sonuç: 23/23 başarılı.** Başarısız test yoktur; olsaydı rapora olduğu gibi yazılır ve betik çıkış kodu 1 verirdi.
- Hata enjeksiyonu artık tekrarlanabilir bir betiktir: `scripts/mutasyon_testi.py`. Verinin geçici bir kopyasına 15 ayrı bilinçli hata eklenir; asıl veri değişmez. **15/15 mutasyon yakalandı**, hatasız kontrol kopyası çıkış kodu 0 verdi.
- İlk çalıştırmada iki mutasyon **kaçtı** ve düzeltildi:
  1. M12 (aktif-aktif bölüşümün bozulması): T21 yalnız toplamı sınıyordu. VLAN modelinden bağımsız yeniden hesap eklendi.
  2. M5: beklenen test T15 olarak yanlış yazılmıştı; hatayı T18 yakalıyor (bkz. bölüm 4 notu).

## 9. Değiştirilen ve eklenen dosyalar

| Dosya | Durum | Gerekçe |
|---|---|---|
| `scripts/ag_modeli_uret.py` | Değişti | SERVER_SWITCH türü, ACCESS_RING, SRLG sütunu, Senaryo B üretimi |
| `scripts/adresleme_uret.py` | **Yeni** | VLAN, /31, loopback, OSPF verisi |
| `scripts/topoloji_dogrula.py` | Değişti | T16–T23, bina bazında yedeklilik, fiziksel senaryolar, fiber ayrıştırması, genişletilmiş kapasite; `DT_ROOT` desteği |
| `scripts/mutasyon_testi.py` | **Yeni** | Tekrarlanabilir hata enjeksiyonu |
| `data/devices.csv`, `data/links.csv` | Yeniden üretildi | Tür ve SRLG değişiklikleri; sayılar aynı |
| `data/senaryo_b/` | **Yeni** | Karşılaştırma senaryosu |
| `data/vlans.csv`, `data/p2p_links.csv`, `data/routers.csv` | **Yeni** | Batfish–FRR veri modeli |
| `docs/dogrulama_raporu.md`, `data/dogrulama_sonuclari.json` | Yeniden üretildi | 23 test ve yeni bölümler |
| `docs/mutasyon_testi.md` | **Yeni** (otomatik) | Mutasyon sonuçları |
| `docs/batfish_frr_hazirlik.md` | **Yeni** | Adresleme ve yönlendirme tasarımı |
| `docs/ag_modeli.md`, `docs/kaynaklar.md` | Güncellendi | Yeni türler, halka açıklaması, Senaryo B, yeni varsayımlar |

## 10. Açık kararlar (hoca ile konuşulacak)

1. Senaryo B uygulansın mı, yoksa A'daki risk belgelenerek kabul mü edilsin?
2. Erişim katmanı transit olsun mu (bölüm 5 ve Batfish–FRR belgesi, bölüm 7)?
3. Aktif-aktif yapılandırılsın mı? Yedeksiz ve 20:1'i aşan SAG, FEN, ITB için ne yapılacak?
4. AP düzeyinde yedeklilik kapsam dışı mı kalsın?
