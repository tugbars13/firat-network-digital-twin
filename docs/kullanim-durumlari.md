# Kullanım Durumları (v2.1)

Bu liste, `docs/topoloji.md` dosyasındaki ağ topolojisine göre güncellenmiştir: gerçek bina konumları, üç bölge (Batı, Orta, Doğu), iki yerleşke, üç katmanlı yapı ve yedek hatlar.

## Aktörler

| Aktör | Tür | Açıklama |
|---|---|---|
| Teknik personel | İnsan | Ağı izler, cihaz ve hat detaylarına bakar, uyarıları takip eder. Senaryo çalıştıramaz, topolojiyi değiştiremez. |
| Ağ yöneticisi | İnsan | Görüntüleme ile izleme ve uyarı işlevlerini kullanır; ayrıca analiz ve senaryo çalıştırır, topolojiyi yönetir. |
| Telemetri simülatörü | Sistem | Ağ cihazlarının ölçümlerini (hat doluluğu, gecikme, cihaz durumu, Wi-Fi istemci sayısı) üretip sisteme gönderir. |

## Kullanım durumları

Öncelik: **Z** = zorunlu, **Ö** = önemli, **İ** = isteğe bağlı (zaman kalırsa).

### Görüntüleme

| No | Kullanım durumu | Aktör | Kısa açıklama | Topolojideki karşılığı | Öncelik |
|---|---|---|---|---|---|
| UC-01 | Kampüs ağını 3D görüntüle | Teknik personel, Ağ yöneticisi | Binaları gerçek konumlarında, ağ cihazlarını ve fiber hatları kampüs haritası üzerinde gösterir | 19 bina + veri merkezi, çekirdek–dağıtım–erişim katmanları | Z |
| UC-02 | Kampüs ağını filtrele | Teknik personel, Ağ yöneticisi | Görünümü Batı, Orta veya Doğu bölgesine; Mühendislik veya Rektörlük Yerleşkesi'ne daraltır | K6 bölge kuralı, iki yerleşke | İ |
| UC-03 | Bina detayını incele | Teknik personel, Ağ yöneticisi | Seçilen binanın kullanıcı sayısını, AP ve switch sayısını, bağlı olduğu dağıtım switch'ini ve yedek hattını gösterir | Topoloji tablosundaki bina satırı | Z |
| UC-04 | Cihaz detayını incele | Teknik personel, Ağ yöneticisi | Seçilen switch ya da AP'nin port durumu, CPU, sıcaklık ve VLAN bilgilerini gösterir | BIDB-CS01/02, MUH/TEK/REK-DS01, erişim switch'leri, AP'ler | Z |
| UC-05 | Hat detayını incele | Teknik personel, Ağ yöneticisi | Seçilen fiber hattın türünü (birincil/yedek), kapasitesini, uzunluğunu, anlık yükünü ve uçlarındaki cihazları gösterir | K7 yedek hat, K8 kapasite, K9 fiber uzunluğu | Z |

### İzleme ve uyarı

| No | Kullanım durumu | Aktör | Kısa açıklama | Topolojideki karşılığı | Öncelik |
|---|---|---|---|---|---|
| UC-06 | Canlı telemetriyi izle | Teknik personel, Ağ yöneticisi | Hat doluluğunu, gecikmeyi ve Wi-Fi istemci sayısını anlık olarak gösterir; hatlar doluluğa göre renklenir | Tüm cihaz ve hatlar | Z |
| UC-07 | Uyarıları görüntüle | Teknik personel, Ağ yöneticisi | Eşik aşımı, cihaz kapanması ve hat kopması gibi olayları listeler | Tüm cihaz ve hatlar | Ö |
| UC-08 | Uyarıyı onayla | Teknik personel, Ağ yöneticisi | Uyarının görüldüğünü ve ilgilenildiğini kaydeder | — | İ |

### Analiz ve senaryo

| No | Kullanım durumu | Aktör | Kısa açıklama | Topolojideki karşılığı | Öncelik |
|---|---|---|---|---|---|
| UC-09 | Geçmiş ağ durumunu tekrar oynat | Ağ yöneticisi | Seçilen tarih ve saatteki ağ durumunu yeniden gösterir | Telemetri geçmişi | Ö |
| UC-10 | Arıza senaryosu çalıştır | Ağ yöneticisi | Bir cihazı (örn. TEK-DS01) ya da fiber hattı sanal olarak devre dışı bırakır; hangi binaların yedek hatta geçtiğini, hangilerinin çevrimdışı kaldığını hesaplar ve gösterir | Dağıtım switch'leri, birincil ve yedek hatlar (K7) | Z |
| UC-11 | Yedeklilik analizini görüntüle | Ağ yöneticisi | Yedek hattı olmayan binaları ve tek arıza noktalarını listeler; ek hat önerisi sunar | Yedekli 8 bina / yedeksiz 11 bina (K7) | Ö |
| UC-12 | Kapasite senaryosu çalıştır | Ağ yöneticisi | Kullanıcı sayısı arttığında hangi hatların ve AP'lerin kapasitesinin aşılacağını hesaplar | K1–K2 kuralları, K8 kapasite | İ |

### Veri yönetimi

| No | Kullanım durumu | Aktör | Kısa açıklama | Topolojideki karşılığı | Öncelik |
|---|---|---|---|---|---|
| UC-13 | Topolojiyi içe aktar | Ağ yöneticisi | Cihaz, hat ve bina bilgilerini `data/topoloji.csv` dosyasından sisteme yükler | `scripts/topoloji_uret.py` çıktısı | Z |
| UC-14 | Telemetri gönder | Telemetri simülatörü | Her cihaz ve hat için ölçümleri düzenli aralıklarla sisteme iletir | Tüm cihaz ve hatlar | Z |

## Özet

| Öncelik | Kullanım durumları | Sayı |
|---|---|---|
| Zorunlu | UC-01, 03, 04, 05, 06, 10, 13, 14 | 8 |
| Önemli | UC-07, 09, 11 | 3 |
| İsteğe bağlı | UC-02, 08, 12 | 3 |

## Kapsam dışı bırakılanlar

- **Kimlik doğrulama (sisteme giriş yapma):** Proje bir prototip ve demo olarak geliştirildiği için kullanıcı girişi bu sürümde yer almaz. Teknik personel ve ağ yöneticisi rolleri arasındaki ayrım, arayüzde rol seçimiyle gösterilir. Gerçek bir kurulumda üniversitenin mevcut kimlik doğrulama sistemiyle (örn. LDAP/SSO) entegrasyon gerekecektir; bu, gelecek çalışmalar kapsamında değerlendirilmiştir.

## Önceki sürüme göre değişiklikler

- **Eklenenler:** UC-02 (bölge/yerleşke filtresi), UC-03 (bina detayı), UC-11 (yedeklilik analizi). Üçü de topoloji tablosunda yer alan bilgileri (bölgeler, bina satırları, yedek hatlar) kullanıcıya açar.
- **Kullanım durumları dört gruba ayrıldı:** Görüntüleme, İzleme ve uyarı, Analiz ve senaryo, Veri yönetimi.
- **Her kullanım durumuna öncelik verildi** ve topolojideki karşılığı yazıldı.
- **Numaralar yeniden düzenlendi.** Eski UC-05 ve sonrası kaydı.
- **UML 2.x düzeltmeleri:** Aktörler arasındaki genelleme ilişkisi kaldırıldı; iki insan aktör bağımsızdır. Ağ yöneticisi, kullandığı tüm kullanım durumlarına (UC-01–UC-13) doğrudan association ile bağlanmıştır.
- **İsim değişiklikleri:** UC-02 "Kampüs ağını filtrele", UC-09 "Geçmiş ağ durumunu tekrar oynat" olarak yeniden adlandırıldı.
