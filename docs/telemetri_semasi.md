# Sentetik Telemetri Şeması ve Senaryo Mantığı

Henüz gerçek telemetri verisi yoktur ve bu projede gerçek ağdan veri alınmayacaktır. Bu belge, simülatörün üreteceği verinin **şemasını** ve **senaryo mantığını** tanımlar. Örnek amaçlı küçük bir veri seti (`data/ornek_telemetri.csv`, 777 kayıt) `scripts/telemetri_uret.py` ile üretilmiştir; büyük bir veri seti bilinçli olarak üretilmemiştir.

Makine tarafından okunabilir şema: `data/telemetri_semasi.json`.

## 1. Alanlar

| Alan | Tür | Birim | Açıklama |
|---|---|---|---|
| `timestamp` | ISO 8601 metin | — | Ölçüm zamanı |
| `scenario` | metin | — | `normal`, `yogun`, `hat_kopmasi`, `cihaz_arizasi` |
| `device_id` | metin | — | `data/devices.csv` içindeki cihaz kimliği |
| `interface_id` | metin | — | `<device_id>:<link_id>`; arayüz, `data/links.csv` içindeki bağlantının o cihazdaki ucudur |
| `latency_ms` | sayı / boş | ms | Hat çalışmıyorsa boş |
| `bandwidth_usage_mbps` | sayı | Mbps | Hattan geçen trafik |
| `packet_loss_percent` | sayı | % | Doluluk %80'i aşınca artar; hat çalışmıyorsa 100 |
| `cpu_usage_percent` | sayı | % | Doluluğa bağlı |
| `memory_usage_percent` | sayı | % | Doluluğa bağlı |
| `link_status` | metin | — | `up` / `down` |
| `synthetic_data` | mantıksal | — | Her zaman `true` |

## 2. Üretim mantığı

1. **Trafik:** Her binanın trafiği = eşzamanlı kablosuz cihaz × 2 Mbps + kablolu uç × 5 Mbps (sentetik varsayım; `topoloji_dogrula.py` kapasite bölümüyle aynı) × senaryo yük çarpanı × ±%10 rastgele değişim.
2. **Yönlendirme:** Bina trafiği birincil hattan dağıtım switch'ine, oradan birincil çekirdek hattından BIDB-CS01'e gider. Hat ya da cihaz çalışmıyorsa yedek hat/yedek çekirdek kullanılır. İkisi de yoksa bina çevrimdışıdır ve trafiği omurgaya ulaşmaz.
3. **Gecikme:** hop sayısı × 0,4 ms × (1 + 2u²); u = hat doluluğu. Yedek bina hattında güzergâh daha uzun olduğu için +0,6 ms.
4. **Paket kaybı:** u < 0,8 ise %0; üzerinde (u − 0,8) × 5.
5. **CPU / bellek:** CPU = %15 + %40·u; bellek = %35 + %10·u (küçük rastgele değişimle).
6. **Arızalı cihaz** telemetri göndermez; komşu cihazlarda o hattın ucu `down` görünür.
7. Rastgelelik sabit tohumla (seed) üretilir; aynı girdiyle aynı veri tekrar üretilir.

## 3. Senaryolar

| Senaryo | Yük çarpanı | Olay | Beklenen davranış |
|---|---|---|---|
| `normal` | 0,5 | — | Tüm hatlar `up`, düşük doluluk |
| `yogun` | 1,0 | — | K1 tepe eşzamanlılığı; doluluk ve gecikme artar |
| `hat_kopmasi` | 1,0 | MUH binasının birincil hattı kopar | MUH-AS01 ucu `down`; trafik MUH-AS02 → TEK-DS01 yedek hattına geçer, gecikme artar |
| `cihaz_arizasi` | 1,0 | TEK-DS01 arızalanır | Orta bölgedeki yedekli binalar (TEK, EGT, IIBF, KUT, YEM) REK-DS01'e geçer; yedeksiz binalar (SPB, SAG, SUR) çevrimdışı kalır |

## 4. Sınırlamalar

- Trafik ve gecikme formülleri basitleştirilmiş modellerdir; gerçek ağ davranışını birebir temsil etmez.
- Bu aşamada yalnızca omurga bağlantıları (bina–dağıtım, dağıtım–çekirdek, çekirdek arası) için telemetri üretilir. AP ve bina içi bağlantılar sonraki aşamada eklenecektir.
- Wi-Fi istemci sayısı alanı henüz şemada yoktur; simülatör aşamasında bina doluluk modeliyle (Mohottige vd., 2022) birlikte eklenecektir.
