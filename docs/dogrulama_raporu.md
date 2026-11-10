# Topoloji doğrulama raporu

> Bu rapor `scripts/topoloji_dogrula.py` tarafından otomatik üretilir; elle düzenlenmez.
> Bütün veriler **sentetiktir**. Fırat Üniversitesi'nin gerçek ağ altyapısına ait hiçbir veri kullanılmamıştır;
> bina konumları dışında kalan her değer `docs/topoloji.md` ve `docs/ag_modeli.md` içindeki kurallardan üretilmiştir.

**Sonuç:** 23/23 yapısal test başarılı. Tek hata noktası: 25. Başarısız test yok.

Yeniden üretmek için: `python3 scripts/topoloji_uret.py && python3 scripts/ag_modeli_uret.py && python3 scripts/adresleme_uret.py && python3 scripts/topoloji_dogrula.py`

## 1. Envanter

| Cihaz türü | Adet |
|---|---:|
| CORE | 2 |
| DISTRIBUTION | 3 |
| ACCESS | 109 |
| SERVER_SWITCH | 2 |
| AP | 617 |
| **Toplam** | **733** |

| Bağlantı türü | Adet |
|---|---:|
| AP_ACCESS | 617 |
| ACCESS_RING | 108 |
| BUILDING_UPLINK | 27 |
| DIST_CORE | 6 |
| SERVER_UPLINK | 4 |
| CORE_INTERCONNECT | 1 |
| **Toplam** | **763** |

## 2. Yapısal testler

T1–T15 birinci denetimden korunmuştur; T16–T23 ikinci denetimde eklenmiştir.

| # | Test | Sonuç | Ayrıntı |
|---|---|---|---|
| T1 | Her cihazın benzersiz kimliği var | ✅ BAŞARILI | 733 cihaz; yinelenen: yok |
| T2 | Bağlantı kimlikleri benzersiz | ✅ BAŞARILI | 763 bağlantı; yinelenen: yok |
| T3 | Her bağlantının iki ucu devices.csv içinde | ✅ BAŞARILI | geçersiz uç: yok |
| T4 | Kendine bağlanan cihaz yok | ✅ BAŞARILI | yok |
| T5 | Aynı iki cihaz arasında aynı türde yinelenen bağlantı yok | ✅ BAŞARILI | yok |
| T6 | İzole cihaz yok | ✅ BAŞARILI | yok |
| T7 | Ağ grafiği tek parça (bağlı) | ✅ BAŞARILI | bileşen sayısı: 1 |
| T8 | Yönetim IP adresleri benzersiz ve özel (RFC 1918) | ✅ BAŞARILI | yinelenen: yok; tümü özel: True |
| T9 | Her dağıtım switch'i çekirdeğe bağlı | ✅ BAŞARILI | MUH-DS01 → BIDB-CS01, BIDB-CS02; TEK-DS01 → BIDB-CS01, BIDB-CS02; REK-DS01 → BIDB-CS01, BIDB-CS02 |
| T10 | Çekirdek switch'leri birbirine bağlı | ✅ BAŞARILI | BIDB-CS01 ↔ BIDB-CS02 |
| T11 | Cihaz envanteri topoloji.csv ile birebir uyumlu (AP ve erişim/sunucu switch'i) | ✅ BAŞARILI | uyumsuz bina: yok |
| T12 | K1–K5 hesapları her bina için yeniden doğrulandı | ✅ BAŞARILI | hatalı satır: yok |
| T13 | Toplamlar beklenen değerlerle uyumlu (20.900 / 611 hariç; 21.020 / 617 dahil) | ✅ BAŞARILI | hariç: 20900 kullanıcı, 611 AP; dahil: 21020 kullanıcı, 617 AP |
| T14 | Binalar arası fiber uzunlukları K9 ile tutarlı | ✅ BAŞARILI | uyumsuz: yok |
| T15 | Tanımlı her yedek hat, birincil hat koptuğunda binayı ayakta tutuyor | ✅ BAŞARILI | başarısız: yok |
| T16 | SERVER_SWITCH ve ACCESS ayrımı (2/3/109/2/617 = 733) | ✅ BAŞARILI | bulunan: {'CORE': 2, 'DISTRIBUTION': 3, 'ACCESS': 109, 'SERVER_SWITCH': 2, 'AP': 617}, toplam 733; BIDB'de ACCESS: yok; hatalı SS: yok; SS iki çekirdeğe bağlı: True |
| T17 | Bina içi halka tutarlılığı (STACK yok, aynı bina, n switch'te n bağlantı, tek döngü, toplam 108) | ✅ BAŞARILI | STACK: 0; ACCESS_RING: 108 (beklenen 108); uç hatası: yok; biçim hatası: yok |
| T18 | Yedeklilik sınıflandırması (8 yedek hatlı bina = hat+dağıtım yedekli; 9 dayanıklı = 8 + BIDB) | ✅ BAŞARILI | kural (K7): ['EGT', 'IIBF', 'KUT', 'MUH', 'REK', 'TEK', 'TIP', 'YEM']; YEDEK hattı olan: ['EGT', 'IIBF', 'KUT', 'MUH', 'REK', 'TEK', 'TIP', 'YEM']; testle yedekli: ['EGT', 'IIBF', 'KUT', 'MUH', 'REK', 'TEK', 'TIP', 'YEM']; tek arızaya dayanıklı: ['BIDB', 'EGT', 'IIBF', 'KUT', 'MUH', 'REK', 'TEK', 'TIP', 'YEM'] |
| T19 | Fiziksel ortak arıza (SRLG tanımlı; A'da BIDB kaybı 20 binanın tamamını düşürür; A'da DS–BIDB güzergâh kesintisi dağıtımı çekirdekten koparır ve yalnız bina transiti kalır; B'de tek bina/güzergâh kaybı başka binayı düşürmez ve transite gerek kalmaz) | ✅ BAŞARILI | SRLG'siz bağlantı: 0; A/BIDB kaybı: 20 bina çevrimdışı; A/DS–BIDB kesintisinde bina transiti: MUH-DS01 → MUH (%120.4); TEK-DS01 → EGT, IIBF, TEK, KUT, YEM (%42.1); REK-DS01 → REK, TIP (%63.5); B'de başka bina düşmüyor: True; B'de transit gerekmiyor: True |
| T20 | Fiber uzunluğu bileşenleri toplamla tutarlı (13.517 + dağıtım–çekirdek = toplam; uzunluk yalnız K9 hatlarında) | ✅ BAŞARILI | birincil 5888 + yedek 7629 = 13517; + dağıtım–çekirdek 5370 + veri merkezi 0 = 18887 m; K9 olup uzunluğu boş: yok; K9 dışı uzunluk: yok |
| T21 | Aktif-pasif ve aktif-aktif kapasite hesapları tutarlı (AA bölüşümü VLAN modeliyle eşleşiyor); N-1 durumunda hiçbir hat %100'ü aşmıyor | ✅ BAŞARILI | hata: yok; dağıtım arızasında aşım: yok; kampüs beklenen yükü 45.78 Gbps |
| T22 | Adresleme modeli tutarlı (34 /31 omurga hattı, çakışma yok, VIP çakışması yok, VLAN boyutları yeterli) | ✅ BAŞARILI | 109 VLAN, 34 /31, 32 OSPF yönlendiricisi; hata: yok |
| T23 | Senaryo B envanteri A ile aynı (yalnızca CS02'nin binası ve ilgili uzunluklar değişir) | ✅ BAŞARILI | cihaz: 733, bağlantı: 763; binası değişen: ['BIDB-CS02'] |

## 3. Tek arıza senaryoları (bilgi amaçlı)

### S1 – Birincil yukarı bağlantı switch'i (AS01) arızası

| Senaryo | Çevrimdışı bina | Kısmi etkilenen | Kaybedilen AP |
|---|---|---|---:|
| REK: birincil yukarı bağlantı switch'i (REK-AS01) arızalı | — | REK (3/12 AP) | 3 |
| MUH: birincil yukarı bağlantı switch'i (MUH-AS01) arızalı | — | MUH (7/64 AP) | 7 |
| ILH: birincil yukarı bağlantı switch'i (ILH-AS01) arızalı | ILH | — | 26 |
| ECZ: birincil yukarı bağlantı switch'i (ECZ-AS01) arızalı | ECZ | — | 15 |
| MIM: birincil yukarı bağlantı switch'i (MIM-AS01) arızalı | MIM | — | 21 |
| AKM: birincil yukarı bağlantı switch'i (AKM-AS01) arızalı | AKM | — | 29 |
| MUZ: birincil yukarı bağlantı switch'i (MUZ-AS01) arızalı | MUZ | — | 6 |
| SPB: birincil yukarı bağlantı switch'i (SPB-AS01) arızalı | SPB | — | 24 |
| EGT: birincil yukarı bağlantı switch'i (EGT-AS01) arızalı | — | EGT (6/44 AP) | 6 |
| IIBF: birincil yukarı bağlantı switch'i (IIBF-AS01) arızalı | — | IIBF (7/49 AP) | 7 |
| SAG: birincil yukarı bağlantı switch'i (SAG-AS01) arızalı | SAG | — | 35 |
| SUR: birincil yukarı bağlantı switch'i (SUR-AS01) arızalı | SUR | — | 12 |
| TEK: birincil yukarı bağlantı switch'i (TEK-AS01) arızalı | — | TEK (6/47 AP) | 6 |
| KUT: birincil yukarı bağlantı switch'i (KUT-AS01) arızalı | — | KUT (4/26 AP) | 4 |
| YEM: birincil yukarı bağlantı switch'i (YEM-AS01) arızalı | — | YEM (6/44 AP) | 6 |
| FEN: birincil yukarı bağlantı switch'i (FEN-AS01) arızalı | FEN | — | 41 |
| VET: birincil yukarı bağlantı switch'i (VET-AS01) arızalı | VET | — | 26 |
| ITB: birincil yukarı bağlantı switch'i (ITB-AS01) arızalı | ITB | — | 38 |
| TIP: birincil yukarı bağlantı switch'i (TIP-AS01) arızalı | — | TIP (5/52 AP) | 5 |

### S1b – Sıradan bir erişim switch'i arızası

| Senaryo | Çevrimdışı bina | Kısmi etkilenen | Kaybedilen AP |
|---|---|---|---:|
| REK: REK-AS05 arızalı | — | REK (2/12 AP) | 2 |
| MUH: MUH-AS10 arızalı | — | MUH (6/64 AP) | 6 |
| ILH: ILH-AS05 arızalı | — | ILH (3/26 AP) | 3 |
| ECZ: ECZ-AS03 arızalı | — | ECZ (5/15 AP) | 5 |
| MIM: MIM-AS04 arızalı | — | MIM (5/21 AP) | 5 |
| AKM: AKM-AS05 arızalı | — | AKM (5/29 AP) | 5 |
| MUZ: MUZ-AS02 arızalı | — | MUZ (3/6 AP) | 3 |
| SPB: SPB-AS04 arızalı | — | SPB (6/24 AP) | 6 |
| EGT: EGT-AS07 arızalı | — | EGT (5/44 AP) | 5 |
| IIBF: IIBF-AS08 arızalı | — | IIBF (6/49 AP) | 6 |
| SAG: SAG-AS06 arızalı | — | SAG (4/35 AP) | 4 |
| SUR: SUR-AS03 arızalı | — | SUR (4/12 AP) | 4 |
| TEK: TEK-AS08 arızalı | — | TEK (5/47 AP) | 5 |
| KUT: KUT-AS05 arızalı | — | KUT (3/26 AP) | 3 |
| YEM: YEM-AS07 arızalı | — | YEM (5/44 AP) | 5 |
| FEN: FEN-AS07 arızalı | — | FEN (5/41 AP) | 5 |
| VET: VET-AS05 arızalı | — | VET (4/26 AP) | 4 |
| ITB: ITB-AS06 arızalı | — | ITB (5/38 AP) | 5 |
| TIP: TIP-AS09 arızalı | — | TIP (4/52 AP) | 4 |

### S2 – Birincil fiber kopması

| Senaryo | Çevrimdışı bina | Kısmi etkilenen | Kaybedilen AP |
|---|---|---|---:|
| REK: birincil hat (L0023) koptu | — | — | 0 |
| MUH: birincil hat (L0047) koptu | — | — | 0 |
| ILH: birincil hat (L0118) koptu | ILH | — | 26 |
| ECZ: birincil hat (L0148) koptu | ECZ | — | 15 |
| MIM: birincil hat (L0168) koptu | MIM | — | 21 |
| AKM: birincil hat (L0195) koptu | AKM | — | 29 |
| MUZ: birincil hat (L0226) koptu | MUZ | — | 6 |
| SPB: birincil hat (L0237) koptu | SPB | — | 24 |
| EGT: birincil hat (L0269) koptu | — | — | 0 |
| IIBF: birincil hat (L0323) koptu | — | — | 0 |
| SAG: birincil hat (L0380) koptu | SAG | — | 35 |
| SUR: birincil hat (L0419) koptu | SUR | — | 12 |
| TEK: birincil hat (L0440) koptu | — | — | 0 |
| KUT: birincil hat (L0494) koptu | — | — | 0 |
| YEM: birincil hat (L0529) koptu | — | — | 0 |
| FEN: birincil hat (L0582) koptu | FEN | — | 41 |
| VET: birincil hat (L0629) koptu | VET | — | 26 |
| ITB: birincil hat (L0662) koptu | ITB | — | 38 |
| TIP: birincil hat (L0710) koptu | — | — | 0 |

### S3 – Dağıtım switch'i arızası

| Senaryo | Çevrimdışı bina | Kısmi etkilenen | Kaybedilen AP |
|---|---|---|---:|
| MUH-DS01 arızalı | ILH, ECZ, MIM, AKM, MUZ | — | 97 |
| TEK-DS01 arızalı | SPB, SAG, SUR | — | 71 |
| REK-DS01 arızalı | FEN, VET, ITB | — | 105 |

### S4 – Çekirdek switch'i arızası

| Senaryo | Çevrimdışı bina | Kısmi etkilenen | Kaybedilen AP |
|---|---|---|---:|
| BIDB-CS01 arızalı | — | — | 0 |
| BIDB-CS02 arızalı | — | — | 0 |

### S5 – Dağıtım–çekirdek hattı kopması

| Senaryo | Çevrimdışı bina | Kısmi etkilenen | Kaybedilen AP |
|---|---|---|---:|
| MUH-DS01 → BIDB-CS01 (PRIMARY) koptu | — | — | 0 |
| MUH-DS01 → BIDB-CS02 (BACKUP) koptu | — | — | 0 |
| TEK-DS01 → BIDB-CS01 (PRIMARY) koptu | — | — | 0 |
| TEK-DS01 → BIDB-CS02 (BACKUP) koptu | — | — | 0 |
| REK-DS01 → BIDB-CS01 (PRIMARY) koptu | — | — | 0 |
| REK-DS01 → BIDB-CS02 (BACKUP) koptu | — | — | 0 |

### S4' – Karşılaştırma: D1 öncesi tasarımda çekirdek arızası

| Senaryo | Çevrimdışı bina | Kısmi etkilenen | Kaybedilen AP |
|---|---|---|---:|
| [D1 öncesi tasarım] BIDB-CS01 arızalı | REK, MUH, ILH, ECZ, MIM, AKM, MUZ, SPB, EGT, IIBF, SAG, SUR, TEK, KUT, YEM, FEN, VET, ITB, TIP | — | 611 |
| [D1 öncesi tasarım] BIDB-CS02 arızalı | — | — | 0 |

### S6 – İkili altyapı arızaları

Çekirdek, dağıtım switch'leri ve bütün omurga hatlarından oluşan elemanlardan 741 çift denendi. 450 çift en az bir binayı çevrimdışı bırakıyor. Herhangi bir tek altyapı arızasına dayanıklı binalar: BIDB, EGT, IIBF, KUT, MUH, REK, TEK, TIP, YEM. Bu binaların en az birini düşüren çift sayısı: 27.

| Arıza çifti | Çevrimdışı bina | Kaybedilen AP |
|---|---|---:|
| BIDB-CS01 + BIDB-CS02 | BIDB, REK, MUH, ILH, ECZ, MIM, AKM, MUZ, SPB, EGT, IIBF, SAG, SUR, TEK, KUT, YEM, FEN, VET, ITB, TIP | 617 |
| TEK-DS01 + REK-DS01 | REK, SPB, EGT, IIBF, SAG, SUR, TEK, KUT, YEM, FEN, VET, ITB, TIP | 450 |
| MUH-DS01 + TEK-DS01 | MUH, ILH, ECZ, MIM, AKM, MUZ, SPB, SAG, SUR | 232 |
| MUH-DS01 + REK-DS01 | ILH, ECZ, MIM, AKM, MUZ, FEN, VET, ITB | 202 |
| MUH-DS01 + hat MUH-AS02–TEK-DS01 | MUH, ILH, ECZ, MIM, AKM, MUZ | 161 |
| MUH-DS01 + hat FEN-AS01–REK-DS01 | ILH, ECZ, MIM, AKM, MUZ, FEN | 138 |
| MUH-DS01 + hat ITB-AS01–REK-DS01 | ILH, ECZ, MIM, AKM, MUZ, ITB | 135 |
| MUH-DS01 + hat SAG-AS01–TEK-DS01 | ILH, ECZ, MIM, AKM, MUZ, SAG | 132 |
| MUH-DS01 + hat VET-AS01–REK-DS01 | ILH, ECZ, MIM, AKM, MUZ, VET | 123 |
| MUH-DS01 + hat SPB-AS01–TEK-DS01 | ILH, ECZ, MIM, AKM, MUZ, SPB | 121 |

## 4. Tek hata noktaları (SPOF)

Tek başına arızası en az bir binayı **tamamen** çevrimdışı bırakan cihaz ya da bağlantı. AP–erişim switch'i bağlantıları (her AP tek kabloyla bağlıdır) listeye alınmamıştır.

| Eleman | Tür | Çevrimdışı bina | Kaybedilen AP |
|---|---|---|---:|
| MUH-DS01 | cihaz | ILH, ECZ, MIM, AKM, MUZ | 97 |
| TEK-DS01 | cihaz | SPB, SAG, SUR | 71 |
| REK-DS01 | cihaz | FEN, VET, ITB | 105 |
| ILH-AS01 | cihaz | ILH | 26 |
| ECZ-AS01 | cihaz | ECZ | 15 |
| MIM-AS01 | cihaz | MIM | 21 |
| AKM-AS01 | cihaz | AKM | 29 |
| MUZ-AS01 | cihaz | MUZ | 6 |
| SPB-AS01 | cihaz | SPB | 24 |
| SAG-AS01 | cihaz | SAG | 35 |
| SUR-AS01 | cihaz | SUR | 12 |
| FEN-AS01 | cihaz | FEN | 41 |
| VET-AS01 | cihaz | VET | 26 |
| ITB-AS01 | cihaz | ITB | 38 |
| L0118 ILH-AS01–MUH-DS01 (BUILDING_UPLINK) | bağlantı | ILH | 26 |
| L0148 ECZ-AS01–MUH-DS01 (BUILDING_UPLINK) | bağlantı | ECZ | 15 |
| L0168 MIM-AS01–MUH-DS01 (BUILDING_UPLINK) | bağlantı | MIM | 21 |
| L0195 AKM-AS01–MUH-DS01 (BUILDING_UPLINK) | bağlantı | AKM | 29 |
| L0226 MUZ-AS01–MUH-DS01 (BUILDING_UPLINK) | bağlantı | MUZ | 6 |
| L0237 SPB-AS01–TEK-DS01 (BUILDING_UPLINK) | bağlantı | SPB | 24 |
| L0380 SAG-AS01–TEK-DS01 (BUILDING_UPLINK) | bağlantı | SAG | 35 |
| L0419 SUR-AS01–TEK-DS01 (BUILDING_UPLINK) | bağlantı | SUR | 12 |
| L0582 FEN-AS01–REK-DS01 (BUILDING_UPLINK) | bağlantı | FEN | 41 |
| L0629 VET-AS01–REK-DS01 (BUILDING_UPLINK) | bağlantı | VET | 26 |
| L0662 ITB-AS01–REK-DS01 (BUILDING_UPLINK) | bağlantı | ITB | 38 |

## 5. Bina bazında yedeklilik

Her bina için dört arıza **ayrı ayrı** uygulanmıştır. Durum: *ayakta* (bütün AP ve uç cihazlar çekirdeğe ulaşıyor), *kısmi* (binada bir kısım AP/cihaz kayıp), *çevrimdışı* (binanın hiçbir AP'si çekirdeğe ulaşamıyor). Kayıp sayılarına arızalı cihazın kendisi de dahildir. Çekirdek sütunu iki çekirdekten kötü olanını gösterir.

| Bina | Alternatif yol | Birincil fiber | Birincil erişim switch'i | Dağıtım switch'i | Çekirdek (en kötü) | Sınıf |
|---|---|---|---|---|---|---|
| BIDB | SS01/SS02 → CS02 | ayakta (0 AP, 0 cihaz) | kısmi (3 AP, 4 cihaz) | — | ayakta (0 AP, 0 cihaz) | Veri merkezi: sunucu switch'leri iki çekirdeğe çift bağlı |
| REK | REK-AS02 → TEK-DS01 | ayakta (0 AP, 0 cihaz) | kısmi (3 AP, 4 cihaz) | ayakta (0 AP, 0 cihaz) | ayakta (0 AP, 0 cihaz) | Hat + dağıtım + çekirdek yedekli |
| MUH | MUH-AS02 → TEK-DS01 | ayakta (0 AP, 0 cihaz) | kısmi (7 AP, 8 cihaz) | ayakta (0 AP, 0 cihaz) | ayakta (0 AP, 0 cihaz) | Hat + dağıtım + çekirdek yedekli |
| ILH | yok | çevrimdışı (26 AP, 31 cihaz) | çevrimdışı (26 AP, 31 cihaz) | çevrimdışı (26 AP, 31 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| ECZ | yok | çevrimdışı (15 AP, 18 cihaz) | çevrimdışı (15 AP, 18 cihaz) | çevrimdışı (15 AP, 18 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| MIM | yok | çevrimdışı (21 AP, 25 cihaz) | çevrimdışı (21 AP, 25 cihaz) | çevrimdışı (21 AP, 25 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| AKM | yok | çevrimdışı (29 AP, 34 cihaz) | çevrimdışı (29 AP, 34 cihaz) | çevrimdışı (29 AP, 34 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| MUZ | yok | çevrimdışı (6 AP, 8 cihaz) | çevrimdışı (6 AP, 8 cihaz) | çevrimdışı (6 AP, 8 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| SPB | yok | çevrimdışı (24 AP, 28 cihaz) | çevrimdışı (24 AP, 28 cihaz) | çevrimdışı (24 AP, 28 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| EGT | EGT-AS02 → REK-DS01 | ayakta (0 AP, 0 cihaz) | kısmi (6 AP, 7 cihaz) | ayakta (0 AP, 0 cihaz) | ayakta (0 AP, 0 cihaz) | Hat + dağıtım + çekirdek yedekli |
| IIBF | IIBF-AS02 → REK-DS01 | ayakta (0 AP, 0 cihaz) | kısmi (7 AP, 8 cihaz) | ayakta (0 AP, 0 cihaz) | ayakta (0 AP, 0 cihaz) | Hat + dağıtım + çekirdek yedekli |
| SAG | yok | çevrimdışı (35 AP, 41 cihaz) | çevrimdışı (35 AP, 41 cihaz) | çevrimdışı (35 AP, 41 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| SUR | yok | çevrimdışı (12 AP, 15 cihaz) | çevrimdışı (12 AP, 15 cihaz) | çevrimdışı (12 AP, 15 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| TEK | TEK-AS02 → REK-DS01 | ayakta (0 AP, 0 cihaz) | kısmi (6 AP, 7 cihaz) | ayakta (0 AP, 0 cihaz) | ayakta (0 AP, 0 cihaz) | Hat + dağıtım + çekirdek yedekli |
| KUT | KUT-AS02 → REK-DS01 | ayakta (0 AP, 0 cihaz) | kısmi (4 AP, 5 cihaz) | ayakta (0 AP, 0 cihaz) | ayakta (0 AP, 0 cihaz) | Hat + dağıtım + çekirdek yedekli |
| YEM | YEM-AS02 → REK-DS01 | ayakta (0 AP, 0 cihaz) | kısmi (6 AP, 7 cihaz) | ayakta (0 AP, 0 cihaz) | ayakta (0 AP, 0 cihaz) | Hat + dağıtım + çekirdek yedekli |
| FEN | yok | çevrimdışı (41 AP, 48 cihaz) | çevrimdışı (41 AP, 48 cihaz) | çevrimdışı (41 AP, 48 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| VET | yok | çevrimdışı (26 AP, 31 cihaz) | çevrimdışı (26 AP, 31 cihaz) | çevrimdışı (26 AP, 31 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| ITB | yok | çevrimdışı (38 AP, 44 cihaz) | çevrimdışı (38 AP, 44 cihaz) | çevrimdışı (38 AP, 44 cihaz) | ayakta (0 AP, 0 cihaz) | Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta) |
| TIP | TIP-AS02 → TEK-DS01 | ayakta (0 AP, 0 cihaz) | kısmi (5 AP, 6 cihaz) | ayakta (0 AP, 0 cihaz) | ayakta (0 AP, 0 cihaz) | Hat + dağıtım + çekirdek yedekli |

**Sınıf dağılımı:** Veri merkezi: sunucu switch'leri iki çekirdeğe çift bağlı: 1; Hat + dağıtım + çekirdek yedekli: 8; Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta): 11

**8 ve 9 farkı.** K7 kuralıyla yedek hattı olan bina sayısı 8'dir (REK, MUH, EGT, IIBF, TEK, KUT, YEM, TIP). S6'daki "tek altyapı arızasına dayanıklı" küme 9 binadır, çünkü dokuzuncu eleman BIDB'dir. BIDB bir yedek hat almaz; veri merkezi sunucu switch'leri (SS01, SS02) iki çekirdeğe ayrı ayrı bağlıdır, bu nedenle tek bir çekirdek ya da hat arızası BIDB'yi düşürmez. Yani 8 = *yedek hatlı bina*, 9 = *8 + çift bağlı veri merkezi*.

**Dürüst not.** Yedek hatlı binalarda birincil erişim switch'i (AS01) arızası binayı düşürmez ama **kısmi** kayba yol açar: AS01'e doğrudan bağlı AP'ler kaybolur, çünkü her AP tek kabloyla tek switch'e bağlıdır. Bu modelde AP düzeyinde yedeklilik yoktur.

## 6. Fiziksel ortak arıza: Senaryo A ve Senaryo B

- **Senaryo A (mevcut topoloji):** CS01 ve CS02 aynı binada (BIDB). Her dağıtım switch'inin iki çekirdek hattı aynı güzergâhtan geçer (aynı SRLG).
- **Senaryo B (karşılaştırma, uygulanmadı):** CS02 Kütüphane binasında (KUT). Konum ve uzunluklar **sentetik varsayımdır**; KUT yalnızca kampüsün orta bölgesinde olduğu ve kritik bina sayıldığı için seçilmiştir. Cihaz kimliği karşılaştırma kolaylığı için `BIDB-CS02` olarak bırakılmıştır.

| Olay | A: çevrimdışı bina | A: kayıp AP / uç cihaz | B: çevrimdışı bina | B: kayıp AP / uç cihaz |
|---|---|---|---|---|
| BIDB binası tümüyle devre dışı (enerji, yangın, su baskını) | 20 (tüm kampüs) | 617 / 728 | 1 (BIDB) | 6 / 8 |
| KUT binası tümüyle devre dışı | 1 (KUT) | 26 / 31 | 1 (KUT) | 26 / 31 |
| CS01 ve CS02 aynı anda arızalı (cihaz arızası) | 20 (tüm kampüs) | 617 / 728 | 20 (tüm kampüs) | 617 / 728 |
| MUH–BIDB fiber güzergâhı kazıda kesildi | 0 | 0 / 0 | 0 | 0 / 0 |
| TEK–BIDB fiber güzergâhı kazıda kesildi | 0 | 0 / 0 | 0 | 0 / 0 |
| REK–BIDB fiber güzergâhı kazıda kesildi | 0 | 0 / 0 | 0 | 0 / 0 |
| BIDB–KUT güzergâhı kesildi | 0 *(bu senaryoda yok)* | 0 / 0 | 0 | 0 / 0 |

**Bina üzerinden transit (Senaryo A).** Bir dağıtım switch'inin iki çekirdek hattı aynı güzergâhta olduğu için kazı ikisini birlikte keser. Bağlılık testi binaları "ayakta" gösterir, çünkü tek OSPF alanında trafik DS → yedek hatlı bir binanın AS01'i → bina içi → AS02 → diğer DS → çekirdek yolunu izleyebilir. Bu yol gerçektir ama 10 Gbps bina hatlarıyla sınırlıdır ve erişim katmanını transit yapar:

| Olay | Kopan dağıtım | Transit binalar | Transit kapasitesi | Taşınması gereken yük | Kullanım |
|---|---|---|---:|---:|---:|
| MUH–BIDB fiber güzergâhı kazıda kesildi | MUH-DS01 | MUH | 10 Gbps | 12.04 Gbps | **%120.4 (aşırı yük)** |
| TEK–BIDB fiber güzergâhı kazıda kesildi | TEK-DS01 | EGT, IIBF, TEK, KUT, YEM | 50 Gbps | 21.03 Gbps | %42.1 |
| REK–BIDB fiber güzergâhı kazıda kesildi | REK-DS01 | REK, TIP | 20 Gbps | 12.71 Gbps | %63.5 |

Senaryo B'de aynı kazı yalnızca bir hattı keser; dağıtım switch'i diğer çekirdeğe doğrudan bağlı kalır, transite gerek olmaz. Erişim katmanının transit olup olmayacağı Batfish–FRR aşamasında açıkça seçilecektir (bkz. `docs/batfish_frr_hazirlik.md`).

Birden fazla omurga hattının paylaştığı fiziksel risk grupları (SRLG):

- A: `SITE-BIDB` (5 hat); `SRLG-MUH-BIDB` (2 hat); `SRLG-REK-BIDB` (2 hat); `SRLG-TEK-BIDB` (2 hat)
- B: `SITE-BIDB` (2 hat); `SRLG-BIDB-KUT` (3 hat)

**Yorum.** Senaryo B, BIDB binasının kaybında kampüs ağının bağlantısını korur. Ancak sunucu switch'leri BIDB'de kaldığı için veri merkezindeki servisler yine kaybolur; gerçek bir felaket kurtarma için ikinci bir veri merkezi gerekir ve bu proje kapsamı dışındadır. B'nin maliyeti, yeni güzergâhlar ve ek fiberdir (bkz. bölüm 7).

## 7. Fiber uzunluğu ayrıştırması

Uzunluklar **ölçüm değildir**. Yalnızca binalar arası hatlara K9 (iki bina koordinatı arasındaki düz çizgi mesafesi × 1,3 güzergâh katsayısı) uygulanmıştır. Bina içi bağlantıların uzunluğu tanımlanmamıştır, çünkü kat planı verisi yoktur.

| Bileşen | Bağlantı | Uzunluğu tanımlı | Toplam (A) | Toplam (B) | Dayanak |
|---|---:|---:|---:|---:|---|
| Bina birincil hattı (bina → dağıtım) | 19 | 16 | 5.888 m | 5.888 m | K9 |
| Bina yedek hattı (AS02 → diğer dağıtım) | 8 | 8 | 7.629 m | 7.629 m | K9 |
| Dağıtım → CS01 (birincil) | 3 | 3 | 2.685 m | 2.685 m | K9 |
| Dağıtım → CS02 (yedek) | 3 | 3 | 2.685 m | 2.084 m | K9 |
| Veri merkezi (çekirdek arası + sunucu switch'i yukarı bağlantıları) | 5 | 0 | 0 m | 2.523 m | uzunluk tanımlanmadı |
| Bina içi (katlar arası halka + AP bağlantıları) | 725 | 0 | 0 m | 0 m | uzunluk tanımlanmadı |
| **Toplam fiber** | | | **18.887 m** | **20.809 m** | |
| Farklı güzergâh (aynı SRLG bir kez) | | | 16.202 m (27 güzergâh) | 19.127 m (31 güzergâh) | kazı/kanal açısından |

**Eski (13.517 m) ve yeni (18.887 m) değerin karşılaştırması:**

| Bileşen | Eski rapor | Yeni rapor | Fark | Açıklama |
|---|---:|---:|---:|---|
| Bina birincil hattı | 5.888 | 5.888 | 0 | değişmedi |
| Bina yedek hattı | 7.629 | 7.629 | 0 | değişmedi |
| Dağıtım–çekirdek | 0 | 5.370 | +5.370 | eski toplamda sayılmamıştı; D1 ile her dağıtım için ikinci hat eklendi (2 × 2.685) |
| Veri merkezi | 0 | 0 | 0 | A'da bina içi, uzunluk tanımsız |
| **Toplam** | **13.517** | **18.887** | **+5.370** | Fark yalnızca kapsamdan gelir; hiçbir hattın uzunluğu değişmemiştir |

## 8. Kapasite

Bütün trafik değerleri **sentetik tasarım parametreleridir** (eşzamanlı kablosuz cihaz başına 2 Mbps, kablolu uç başına 5 Mbps, uç port 1 Gbps, öğrenci payı %85). Ölçüm değildir.

- **Teorik oran** = kullanılan uç portların toplam hızı / etkin yukarı bağlantı kapasitesi. Bu bir *port oranı göstergesidir*; trafik değildir. Cisco (2013) erişim katmanı için 20:1'i bir başparmak kuralı olarak verir.
- **Beklenen kullanım** = beklenen trafik / hat kapasitesi.
- **Aktif-pasif:** yedek hat yalnız birincil koparsa taşır (OSPF maliyeti yedekte 100).
- **Aktif-aktif:** iki hat da taşır. Bunun için yapılandırma gerekir: binada VRRP ana yönlendiricisi VLAN bazında paylaştırılır (VLAN 100 → AS01, VLAN 110/200 → AS02), bina–dağıtım ve dağıtım–çekirdek OSPF maliyetleri eşitlenir (ECMP). Yapılandırılmadıkça aktif-aktif kapasite **yoktur**.

| Bina | Yedek hat | Uç port (Gbps) | Teorik oran AP | Teorik oran AA | Beklenen (Gbps) | Kullanım AP | AA hat 1 | AA hat 2 | N-1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| REK | var | 72 | 7.2:1 | 3.6:1 | 0.88 | %8.8 | %4.9 | %3.9 | %8.8 |
| MUH | var | 394 | **39.4:1** | 19.7:1 | 4.82 | %48.2 | %26.9 | %21.2 | %48.2 |
| ILH | yok | 161 | 16.1:1 | 16.1:1 | 1.97 | %19.7 | — | — | — |
| ECZ | yok | 90 | 9.0:1 | 9.0:1 | 1.09 | %10.9 | — | — | — |
| MIM | yok | 126 | 12.6:1 | 12.6:1 | 1.53 | %15.3 | — | — | — |
| AKM | yok | 179 | 17.9:1 | 17.9:1 | 2.19 | %21.9 | — | — | — |
| MUZ | yok | 36 | 3.6:1 | 3.6:1 | 0.44 | %4.4 | — | — | — |
| SPB | yok | 144 | 14.4:1 | 14.4:1 | 1.75 | %17.5 | — | — | — |
| EGT | var | 269 | **26.9:1** | 13.4:1 | 3.29 | %32.9 | %18.4 | %14.5 | %32.9 |
| IIBF | var | 304 | **30.4:1** | 15.2:1 | 3.72 | %37.2 | %20.8 | %16.4 | %37.2 |
| SAG | yok | 215 | **21.5:1** | **21.5:1** | 2.63 | %26.3 | — | — | — |
| SUR | yok | 72 | 7.2:1 | 7.2:1 | 0.88 | %8.8 | — | — | — |
| TEK | var | 287 | **28.7:1** | 14.3:1 | 3.5 | %35.0 | %19.6 | %15.4 | %35.0 |
| KUT | var | 161 | 16.1:1 | 8.1:1 | 1.97 | %19.7 | %11.0 | %8.7 | %19.7 |
| YEM | var | 269 | **26.9:1** | 13.4:1 | 3.29 | %32.9 | %18.4 | %14.5 | %32.9 |
| FEN | yok | 251 | **25.1:1** | **25.1:1** | 3.07 | %30.7 | — | — | — |
| VET | yok | 161 | 16.1:1 | 16.1:1 | 1.97 | %19.7 | — | — | — |
| ITB | yok | 233 | **23.3:1** | **23.3:1** | 2.85 | %28.5 | — | — | — |
| TIP | var | 322 | **32.2:1** | 16.1:1 | 3.94 | %39.4 | %22.0 | %17.4 | %39.4 |

20:1'i aşan bina — aktif-pasif: 9 (MUH, EGT, IIBF, SAG, TEK, YEM, FEN, ITB, TIP); aktif-aktif: 3 (SAG, FEN, ITB). Aktif-aktif yalnız yedek hatlı binalarda oranı yarıya indirir; yedeksiz binalar için tek çözüm yukarı bağlantı hızını artırmaktır.

**Dağıtım → çekirdek** (aktif-pasif: yalnız CS01 hattı, 40 Gbps; aktif-aktif: iki hat ECMP, 80 Gbps):

| Dağıtım | Yük AP (Gbps) | Kullanım AP | Yük AA (Gbps) | Kullanım AA |
|---|---:|---:|---:|---:|
| MUH-DS01 | 12.04 | %30.1 | 9.92 | %12.4 |
| REK-DS01 | 12.7 | %31.8 | 17.53 | %21.9 |
| TEK-DS01 | 21.02 | %52.6 | 18.32 | %22.9 |

Kampüs toplam beklenen yükü: 45.78 Gbps.

**Dağıtım switch'i arızası (N-1):** yedek hatlı binaların bütün yükü yedek dağıtıma geçer; yedeksiz binalar servis dışı kalır.

| Arızalı | Kalan dağıtım | Yük (Gbps) | Kullanım (tek 40G) | Kullanım (ECMP 80G) | Servis dışı bina |
|---|---|---:|---:|---:|---|
| MUH-DS01 | REK-DS01 | 12.71 | %31.8 | %15.9 | ILH, ECZ, MIM, AKM, MUZ |
| MUH-DS01 | TEK-DS01 | 25.85 | %64.6 | %32.3 | ILH, ECZ, MIM, AKM, MUZ |
| REK-DS01 | MUH-DS01 | 12.04 | %30.1 | %15.0 | FEN, VET, ITB |
| REK-DS01 | TEK-DS01 | 25.85 | %64.6 | %32.3 | FEN, VET, ITB |
| TEK-DS01 | MUH-DS01 | 12.04 | %30.1 | %15.0 | SPB, SAG, SUR |
| TEK-DS01 | REK-DS01 | 28.48 | %71.2 | %35.6 | SPB, SAG, SUR |

## 9. Sınırlılıklar

- Erişilebilirlik, grafik bağlılığıyla ölçülür (AP → herhangi bir çekirdek). Yönlendirme protokolünün yakınsama süresi, VRRP geçişi ve RSTP davranışı bu testte modellenmez; Batfish/FRR aşamasında ele alınacaktır.
- Bina içi halka (ACCESS_RING) bir Katman 2 döngüsüdür; döngü RSTP (IEEE 802.1w) ile engellenir. Grafik testi döngüyü bir yedek yol olarak görür; bu, RSTP'nin bir portu blokladığı ve arızada açtığı varsayımına dayanır.
- Kapasite hesapları ortalama yük üzerindendir; ani tepe (burst) ve uygulama karışımı modellenmez.
- Senaryo B yalnızca karşılaştırma içindir; mevcut topoloji (A) değiştirilmemiştir.
