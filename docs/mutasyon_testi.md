# Mutasyon (hata enjeksiyonu) testi

> `scripts/mutasyon_testi.py` tarafından otomatik üretilir. Her satırda verinin geçici bir kopyasına tek bir bilinçli hata eklenir; asıl veri değiştirilmez. Doğrulayıcı hatayı yakalarsa çıkış kodu 1 olur ve hedef test BAŞARISIZ görünür.

**Kontrol çalıştırması (hatasız kopya):** çıkış kodu 0, başarısız test: yok.

**Sonuç:** 15/15 mutasyon yakalandı.

| # | Eklenen hata | Hedef test | Çıkış kodu | Başarısız olan testler | Yakalandı mı |
|---|---|---|---:|---|---|
| M1 | Yinelenen cihaz kimliği | T1 | 1 | T1, T8, T11, T16 | ✅ evet |
| M2 | Var olmayan cihaza bağlantı | T3 | 1 | T3, T7, T23 | ✅ evet |
| M3 | Yinelenen yönetim IP adresi | T8 | 1 | T8 | ✅ evet |
| M4 | K9 dışı fiber uzunluğu (1663 → 1500) | T14 | 1 | T14 | ✅ evet |
| M5 | Yedek hat birincil ile aynı dağıtıma bağlandı (MUH-AS02 → MUH-DS01) | T18 | 1 | T14, T18, T19, T23 | ✅ evet |
| M6 | Sunucu switch'i ACCESS olarak etiketlendi | T16 | 1 | T16, T23 | ✅ evet |
| M7 | Halka bağlantısı STACK olarak geri yazıldı | T17 | 1 | T17, T23 | ✅ evet |
| M8 | Halkada bir bağlantı silindi (döngü kırıldı) | T17 | 1 | T17, T23 | ✅ evet |
| M9 | Yedek hatlı binanın yedek hattı kaldırıldı (KUT) | T18 | 1 | T18, T20, T22, T23 | ✅ evet |
| M10 | Dağıtım–çekirdek hattından SRLG bilgisi silindi | T19 | 1 | T19 | ✅ evet |
| M11 | Bina yedek hattının uzunluğu boşaltıldı | T20 | 1 | T20 | ✅ evet |
| M12 | Aktif-aktif bölüşümü bozuldu (öğrenci payı yerine tüm yük hat 1'e) | T21 | 1 | T21 | ✅ evet |
| M13 | İki VLAN'a aynı alt ağ verildi | T22 | 1 | T22 | ✅ evet |
| M14 | VRRP VIP bir switch'in yönetim adresine eşit | T22 | 1 | T22 | ✅ evet |
| M15 | Senaryo B'de fazladan cihaz | T23 | 1 | T23 | ✅ evet |

Bir mutasyon birden fazla testi düşürebilir; bu beklenen bir durumdur (ör. bir halka bağlantısı silinince bağlantı sayısı da değişir). Önemli olan hedef testin hatayı yakalamasıdır.
