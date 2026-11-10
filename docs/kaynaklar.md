# Kaynaklar

Bu dosya, modeldeki hangi bilginin hangi kaynağa dayandığını ve kaynağın içeriğinin nasıl doğrulandığını gösterir. Kural numaraları `docs/topoloji.md` dosyasındaki boyutlandırma kurallarına karşılık gelir.

## 1. Verinin türüne göre kaynak durumu

| Tür | Kapsam | Kaynak durumu |
|---|---|---|
| **A. Gerçek coğrafi veri** | Fakülte isimleri, bina konumları, iki yerleşkeli kampüs yapısı | Kamuya açık kaynaklar (bölüm 2) |
| **B. Sentetik tasarım parametresi** | Cihaz, kullanıcı, AP ve switch sayıları; IP adresleri; bağlantılar; kapasiteler; yedeklilik ilişkileri | Projenin tasarımıdır. Bazı katsayılar kaynaklarla desteklenmiştir (bölüm 3); desteklenmeyenler açıkça varsayım olarak işaretlenmiştir (bölüm 5). |
| **C. Simülasyon verisi** | Gecikme, paket kaybı, trafik, CPU ve bellek, arıza durumları | Kaynağı yoktur; `scripts/telemetri_uret.py` tarafından kurallarla üretilir |

## 2. Coğrafi veriler (A)

- **Fakülte listesi:** Fırat Üniversitesi, fakülteler mezuniyet töreni duyurusu. https://www.firat.edu.tr/tr/page/event/fakulteler-mezuniyet-toreni-ikinci-grup-7452
- **İki ana yerleşke (Mühendislik ve Rektörlük):** Fırat Üniversitesi SKS Daire Başkanlığı, ulaşım sayfası. https://sksdab.firat.edu.tr/en/page/26447
- **Bina konumları:** Google Haritalar ve OpenStreetMap aramaları (Kasım 2026); Arkeoloji ve Etnografya Müzesi için Wikipedia. Her binanın konum kaynağı `data/topoloji.csv` içindeki `konum_kaynagi` sütunundadır. Merkez Yemekhane'nin konumu doğrulanamamıştır.

## 3. Tasarım parametrelerini destekleyen kaynaklar (B)

"İçerik doğrulaması" sütunu, kaynakta atıf yapılan bilginin gerçekten bulunduğunun nasıl kontrol edildiğini gösterir.

| Kaynak | Desteklediği kural | Kaynakta bulunan bilgi | İçerik doğrulaması |
|---|---|---|---|
| Okumura & Fujimura (2023) | K1, K1b, AP sayısı karşılaştırması | Ders günlerinde ~12.000 günlük öğrenci kullanıcı; 9:00–18:00 arasında aynı anda 4.000–7.000 kullanıcı (%33–58); kullanıcı başına 1,2–1,3 cihaz; merkezi Wi-Fi'de 630 AP | Tam metin okundu |
| Mohottige vd. (2022) | K1; simülatörde doluluk–Wi-Fi ilişkisi | Derse gelen öğrencilerin ortalama %18'i Wi-Fi'ye bağlanmıyor; kayıtlı öğrenci sayısı derse gelenden belirgin şekilde fazla | Tam metin okundu |
| Florwick & Whiteaker (2013), Cisco | K2, K1b, K8 | Tipik ofiste AP hücresi başına en fazla 20–30 kullanıcı; kullanıcılar birincil cihazın yanında ikinci bir cihaz taşır; erişim katmanı 20:1 aşırı abonelikle tasarlanır | Rehberin web sürümü okundu |
| Teare & Paquet (2006) | Üç katmanlı hiyerarşik yapı | Erişim, dağıtım ve çekirdek katmanlarından oluşan hiyerarşik model | **Yalnızca Google Akademik özeti görüldü; tam metin okunmadı.** Rapordan önce ilgili bölüm okunmalıdır. |
| Paguigan vd. (2022) | Üç katman yerine iki katman tartışması | Tek binalı, ~45 personel ve ~600 öğrencili yerleşkede maliyet gerekçesiyle iki katmanlı (collapsed-core) yapı önerilmiş | Tam metin okundu. Not: "iki katman daha ucuz" iddiası makalede bir firma web sayfasına dayanır; yalnızca örnek olarak kullanılmalıdır. |
| Swapna vd. (2025) | Benzer çalışma | Üç binalı ana kampüs ve şube kampüste hiyerarşik tasarım, bölüm başına VLAN, dağıtım katmanında yedeklilik | Tam metin okundu. Not: yazım kalitesi düşüktür; yalnızca destekleyici örnek olarak kullanılmalıdır. |

## 4. Kaynakça (APA)

- Florwick, J., & Whiteaker, J. (2013). *Wireless LAN design guide for high density client environments in higher education*. Cisco Systems. https://www3-realm.cisco.com/en/US/prod/collateral/wireless/ps5678/ps10981/design_guide_c07-693245.html
- Mohottige, I. P., Gharakheili, H. H., Moors, T., & Sivaraman, V. (2022). Modeling classroom occupancy using data of WiFi infrastructure in a university campus. *IEEE Sensors Journal, 22*(10), 9981–9996.
- Okumura, M., & Fujimura, S. (2023). Wireless LAN operation and behavioral inferences from usage analysis. In *Proceedings of the 2023 ACM SIGUCCS Annual Conference (SIGUCCS '23)*. ACM. https://doi.org/10.1145/3539811.3579565
- Paguigan, J. S., Albino, M. G., & Costales, J. A. (2022). An assessment and design of campus network using collapsed-core architecture. In *2022 IEEE 10th International Conference on Information, Communication and Networks (ICICN)* (pp. 10–14). IEEE. https://doi.org/10.1109/ICICN56848.2022.10006457
- Swapna, K., Nandeeshwar, B., Aravind, A., Gagan, B., & Ravi, B. (2025). Campus network design using Cisco Packet Tracer. In *2025 10th International Conference on Signal Processing and Communication (ICSC)* (pp. 45–50). IEEE. https://doi.org/10.1109/ICSC64553.2025.10968176
- Teare, D., & Paquet, C. (2006). *Campus network design fundamentals*. Cisco Press.

## 5. Kaynağı olmayan tasarım varsayımları

Aşağıdaki değerler hiçbir kaynağa atfedilmemiştir. Raporda "tasarım varsayımı" olarak sunulmalıdır.

| Değer | Nerede | Not |
|---|---|---|
| Kablolu uç oranı %15 (K3) | `topoloji_uret.py` | Kaynak taraması sürüyor |
| %20 büyüme payı (K4) | `topoloji_uret.py` | Kaynak taraması sürüyor |
| 48 portlu switch, kat başına en az bir switch (K5) | `topoloji_uret.py` | Kaynak taraması sürüyor |
| Fiber güzergâh katsayısı 1,3 (K9) | `topoloji_uret.py`, `ag_modeli_uret.py` | Güzergâh katsayısı (route factor / detour index) kavramı literatürde tanımlıdır, ancak 1,3 değeri için kaynak bulunmamıştır |
| Yedek hat eşiği 1.500 kullanıcı ve kritik hizmet listesi (K7) | `topoloji_uret.py` | Tasarım kararı |
| Çekirdek çift bağlantısı, bina içi katlar arası Ethernet halkası (10 Gbps, RSTP ile döngü önleme), 40 Gbps çekirdek arası kapasite, 1 Gbps AP portu | `ag_modeli_uret.py` | Tasarım kararı (ikinci denetimde "40 Gbps yığın" düzeltildi) |
| Senaryo B: CS02'nin Kütüphane (KUT) binasına taşınması | `ag_modeli_uret.py` → `data/senaryo_b/` | Yalnızca karşılaştırma; konum ve uzunluklar sentetik |
| Eşzamanlı kablosuz cihazların %85'i öğrenci, %15'i personel | `adresleme_uret.py`, `topoloji_dogrula.py` | Tasarım varsayımı (VLAN boyutu ve aktif-aktif bölüşüm için) |
| Alt ağ boyutlandırmada %25 adres payı | `adresleme_uret.py` | Tasarım varsayımı |
| OSPF maliyetleri (bina hattı 10/100, dağıtım–çekirdek 5/50, çekirdek arası 5, bina transit 10), tek alan (alan 0) | `adresleme_uret.py` | Tasarım kararı; Batfish–FRR aşamasında sınanacak |
| Cihaz başına 2 Mbps, kablolu uç başına 5 Mbps beklenen trafik | `topoloji_dogrula.py`, `telemetri_uret.py` | Tasarım varsayımı |
| Telemetri formülleri (gecikme, kayıp, CPU, bellek) | `telemetri_uret.py` | Basitleştirilmiş simülasyon modeli |
