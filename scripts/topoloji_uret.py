import math, csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent  # depo kök klasörü
# ad, kod, tur, kat, tepe kullanici, enlem, boylam, konum kaynagi, kritik
B=[
("Bilgi İşlem Daire Başkanlığı (veri merkezi)","BIDB","Veri merkezi",3,120,38.67785,39.20290,"Google Haritalar",True),
("Rektörlük","REK","İdari",5,400,38.67776,39.20196,"Google Haritalar",True),
("Mühendislik Fakültesi","MUH","Fakülte",5,2200,38.67430,39.18888,"Google Haritalar (dekanlık)",False),
("İlahiyat Fakültesi","ILH","Fakülte",4,900,38.67929,39.18885,"Google Haritalar",False),
("Eczacılık Fakültesi","ECZ","Fakülte",3,500,38.67793,39.18856,"Google Haritalar",False),
("Mimarlık Fakültesi","MIM","Fakülte",4,700,38.67698,39.19120,"OpenStreetMap",False),
("Atatürk Kültür Merkezi","AKM","Destek binası",2,1000,38.67389,39.18927,"Google Haritalar",False),
("Arkeoloji ve Etnografya Müzesi","MUZ","Destek binası",2,200,38.67306,39.19056,"Wikipedia",False),
("Spor Bilimleri Fakültesi","SPB","Fakülte",2,800,38.68237,39.19394,"Google Haritalar",False),
("Eğitim Fakültesi","EGT","Fakülte",4,1500,38.68062,39.19467,"Google Haritalar",False),
("İktisadi ve İdari Bilimler Fakültesi","IIBF","Fakülte",4,1700,38.68459,39.19425,"Google Haritalar",False),
("Sağlık Bilimleri Fakültesi","SAG","Fakülte",4,1200,38.68373,39.19415,"Google Haritalar",False),
("Su Ürünleri Fakültesi","SUR","Fakülte",3,400,38.68422,39.19399,"Google Haritalar",False),
("Teknoloji Fakültesi","TEK","Fakülte",4,1600,38.68128,39.19608,"Google Haritalar",False),
("Merkez Kütüphane","KUT","Destek binası",4,900,38.68012,39.19604,"Google Haritalar",True),
("Merkez Yemekhane","YEM","Destek binası",2,1500,38.67933,39.19656,"Tahmin (konum doğrulanamadı)",False),
("Fen Fakültesi","FEN","Fakülte",4,1400,38.68050,39.20143,"OpenStreetMap",False),
("Veteriner Fakültesi","VET","Fakülte",3,900,38.67905,39.20079,"Google Haritalar",False),
("İnsan ve Toplum Bilimleri Fakültesi","ITB","Fakülte",4,1300,38.68103,39.20332,"Google Haritalar (İnsani ve Sosyal Bilimler adıyla)",False),
("Tıp Fakültesi","TIP","Fakülte",6,1800,38.67904,39.20470,"Google Haritalar",True),
]
def bolge(lon): return "Batı" if lon<39.192 else ("Orta" if lon<39.199 else "Doğu")
YERLESKE={"Batı":"Mühendislik Yerleşkesi","Orta":"Rektörlük Yerleşkesi","Doğu":"Rektörlük Yerleşkesi"}
DIST={"Batı":"MUH","Orta":"TEK","Doğu":"REK"}
BACKUP_TO={"Batı":"Orta","Orta":"Doğu","Doğu":"Orta"}
P={k:(la,lo) for _,k,_,_,_,la,lo,_,_ in B}
def mesafe(a,b):
    (la1,lo1),(la2,lo2)=P[a],P[b];R=6371000
    p1,p2=math.radians(la1),math.radians(la2);dp=p2-p1;dl=math.radians(lo2-lo1)
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return round(2*R*math.asin(math.sqrt(h))*1.3)  # %30 guzergah payi
rows=[]
for ad,kod,tur,kat,kul,la,lo,kay,krit in B:
    if kod=="BIDB":
        # Veri merkezi: K1/K1b/K4 aynı yuvarlama kuralıyla hesaplanır; AP, kablolu uç ve switch sayısı elle belirlenir.
        esz=math.ceil(kul*0.6); cihaz=math.ceil(esz*1.2)
        ap=6; kablolu=60; port=math.ceil((ap+kablolu)*1.2); sw=2  # sw: 2 sunucu switch'i (BIDB-SS01/02); çekirdek switch'leri ayrıca sayılır
        rows.append(dict(kod=kod,ad=ad,tur=tur,kat=kat,kullanici=kul,eszamanli=esz,cihaz=cihaz,ap=ap,kablolu=kablolu,port=port,sw=sw,yerleske="Rektörlük Yerleşkesi",bolge="Çekirdek",birincil="—",birincil_m=0,yedek="—",yedek_m=0,kural_yedek="Çekirdek katmanı",enlem=la,boylam=lo,konum_kaynagi=kay,deger_turu="manuel: ap, kablolu, sw | hesaplanan: eszamanli, cihaz, port"));continue
    esz=math.ceil(kul*0.6); cihaz=math.ceil(esz*1.2); ap=max(math.ceil(cihaz/25),kat); kablolu=math.ceil(kul*0.15)
    port=math.ceil((ap+kablolu)*1.2); sw=max(kat,math.ceil(port/48))
    bz=bolge(lo); d=DIST[bz]
    if d==kod: birincil="Kendi binası (dağıtım burada)"; bm=0
    else: birincil=f"{d}-DS01 ({bz})"; bm=mesafe(kod,d)
    yedekli=kul>=1500 or krit
    if yedekli: yb=BACKUP_TO[bz]; yedek=f"{DIST[yb]}-DS01 ({yb})"; ym=mesafe(kod,DIST[yb])
    else: yedek="Yok"; ym=0
    neden=("kullanıcı ≥ 1.500" if kul>=1500 else "kritik hizmet") if yedekli else "kullanıcı < 1.500, kritik değil"
    rows.append(dict(kod=kod,ad=ad,tur=tur,kat=kat,kullanici=kul,eszamanli=esz,cihaz=cihaz,ap=ap,kablolu=kablolu,port=port,sw=sw,yerleske=YERLESKE[bz],bolge=bz,birincil=birincil,birincil_m=bm,yedek=yedek,yedek_m=ym,kural_yedek=neden,enlem=la,boylam=lo,konum_kaynagi=kay,deger_turu="hesaplanan"))
with open(ROOT/"data"/"topoloji.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
tr=lambda n:f"{n:,}".replace(",",".")
md=["# Ağ Topolojisi Tablosu\n",
"Bu tablo Fırat Üniversitesi kampüs ağının sentetik (uydurma ama kurallı) modelidir. Cihaz sayıları aşağıdaki kurallardan hesaplanmıştır, elle yazılmamıştır.\n",
"## 0. Veri türleri\n",
"Fırat Üniversitesi'nin gerçek ağ altyapısı bu çalışmada kullanılmamıştır. Model üç tür veriden oluşur:\n",
"| Tür | İçerik | Kaynak |\n|---|---|---|",
"| **A. Gerçek coğrafi veri** | Fakülte isimleri; bina konumları (Merkez Yemekhane hariç); iki yerleşkeli kampüs yapısı | Fırat Üniversitesi resmî sitesi (fakülte listesi: https://www.firat.edu.tr/tr/page/event/fakulteler-mezuniyet-toreni-ikinci-grup-7452; yerleşkeler: SKS Daire Başkanlığı sitesi); Google Haritalar, OpenStreetMap, Wikipedia (her binanın konum kaynağı tabloda) |",
"| **B. Sentetik tasarım parametresi** | Kat ve kullanıcı sayıları; AP, switch ve port sayıları; cihaz adları; IP adresleri; bağlantılar ve yedeklilik ilişkileri; hat kapasiteleri ve fiber uzunlukları | Bu belgedeki K1–K9 kuralları ve `docs/ag_modeli.md`; katsayıların bir kısmı kaynaklarla desteklenmiştir (bkz. `docs/kaynaklar.md`) |",
"| **C. Simülasyon verisi** | Gecikme, paket kaybı, trafik, CPU ve bellek kullanımı, arıza durumları | Henüz üretilmemiştir; şema ve senaryo mantığı `docs/telemetri_semasi.md` dosyasındadır |\n",
"## 1. Boyutlandırma kuralları\n",
"| Kural | Tanım | Gerekçe | Kaynak |\n|---|---|---|---|",
"| K1 · Eşzamanlı kullanıcı | Tepe kullanıcı × 0,6 | Bir üniversitede gün içinde aynı anda bağlı kullanıcılar günlük kullanıcıların %33–58'i olarak ölçülmüştür; yoğun saate göre boyutlandırma için üst sınır alınmıştır | Okumura & Fujimura (2023); Mohottige vd. (2022) |",
"| K1b · Eşzamanlı cihaz | Eşzamanlı kullanıcı × 1,2 | Kişi başına 1,2–1,3 kablosuz cihaz ölçülmüştür; kullanıcılar genellikle birden fazla cihaz taşır | Okumura & Fujimura (2023); Cisco (2013) |",
"| K2 · Erişim noktası (AP) | max(⌈eşzamanlı cihaz ÷ 25⌉, kat sayısı) | Tipik ofis ortamında AP hücresi başına 20–30 kullanıcı; aralığın ortası alınmıştır; her katta en az bir AP | Cisco (2013) |",
"| K3 · Kablolu uç | ⌈tepe kullanıcı × 0,15⌉ | Laboratuvar bilgisayarları, ofisler, yazıcılar, kameralar | Tasarım varsayımı (kaynak aranıyor) |",
"| K4 · Port ihtiyacı | ⌈(AP + kablolu uç) × 1,2⌉ | Her AP bir port kullanır; %20 büyüme payı | Tasarım varsayımı (kaynak aranıyor) |",
"| K5 · Erişim switch'i | max(kat sayısı, ⌈port ÷ 48⌉) | 48 portlu switch; her katta en az bir kat dolabı | Tasarım varsayımı (kaynak aranıyor) |",
"| K6 · Bölge | Binanın gerçek boylamına göre: Batı (< 39,192), Orta (39,192–39,199), Doğu (> 39,199) | Batı bölgesi Mühendislik Yerleşkesi'ne, Orta ve Doğu Rektörlük Yerleşkesi'ne karşılık gelir | Bina konumları (bkz. bölüm 0) |",
"| K7 · Yedek hat | Tepe kullanıcı ≥ 1.500 **veya** kritik hizmet | Bu binalar komşu bölgenin dağıtım switch'ine ikinci bir fiber hatla da bağlanır | Tasarım kararı |",
"| K8 · Hat kapasitesi | Bina → dağıtım: 10 Gbps; dağıtım → çekirdek: 40 Gbps | Erişim katmanı yoğun trafiğe karşı 20:1 aşırı abonelik oranıyla tasarlanır | Cisco (2013) |",
"| K9 · Fiber uzunluğu | İki bina arası kuş uçuşu mesafe × 1,3 | Kablo yol ve kanal güzergâhını izlediği için %30 pay (güzergâh katsayısı) | Tasarım varsayımı (kaynak aranıyor) |\n",
"Kaynakların tam künyeleri `docs/kaynaklar.md` dosyasındadır.\n",
"## 2. Katman yapısı\n",
"| Katman | Cihaz | Konum |\n|---|---|---|",
"| Çekirdek | BIDB-CS01, BIDB-CS02 (yedekli çift) | Bilgi İşlem Daire Başkanlığı |",
"| Dağıtım | MUH-DS01 (Batı), TEK-DS01 (Orta), REK-DS01 (Doğu) | Mühendislik Fakültesi, Teknoloji Fakültesi, Rektörlük |",
"| Erişim | Her binada K5'e göre hesaplanan switch'ler | Bina kat dolapları |",
"| Kablosuz | Her binada K2'ye göre hesaplanan AP'ler | Katlar |\n",
"## 3. Bina tablosu\n",
"| Kod | Bina | Yerleşke | Bölge (K6) | Kat | Tepe kullanıcı | AP (K2) | Erişim switch'i (K5) | Birincil bağlantı | Fiber (m, K9) | Yedek bağlantı (K7) | Fiber (m) | Konum kaynağı |",
"|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['kod']} | {r['ad']} | {r['yerleske']} | {r['bolge']} | {r['kat']} | {tr(r['kullanici'])} | {r['ap']} | {r['sw']} | {r['birincil']} | {r['birincil_m'] or '—'} | {r['yedek']} | {r['yedek_m'] or '—'} | {r['konum_kaynagi']} |")
md.append("\nEşzamanlı kullanıcı (K1), eşzamanlı cihaz (K1b), kablolu uç (K3) ve port (K4) ara değerleri `data/topoloji.csv` dosyasında yer alır. Her satırın `deger_turu` sütunu değerin kuralla mı hesaplandığını yoksa elle mi belirlendiğini gösterir.\n")
md.append("**Veri merkezi (BIDB) satırı:** Eşzamanlı kullanıcı, eşzamanlı cihaz ve port sayısı diğer binalarla aynı kurallarla hesaplanır. AP sayısı (6), kablolu uç sayısı (60; sunucu ve depolama bağlantıları) ve switch sayısı (2 sunucu switch'i: BIDB-SS01, BIDB-SS02) elle belirlenmiştir, çünkü veri merkezinin ihtiyacı kullanıcı sayısından değil barındırdığı sistemlerden doğar. Çekirdek switch'leri (BIDB-CS01, BIDB-CS02) bu sayıya dahil değildir.\n")
md.append("## 4. Özet\n")
nd=[r for r in rows if r['kod']!='BIDB']
S=lambda rs,k: sum(r[k] for r in rs)
md.append("Tüm değerler doğrudan `data/topoloji.csv` satırlarından toplanmıştır.\n")
md.append("| Kalem | Veri merkezi hariç | Veri merkezi dahil |\n|---|---|---|")
md.append(f"| Bina | {len(nd)} | {len(rows)} |")
md.append(f"| Tepe kullanıcı | {tr(S(nd,'kullanici'))} | {tr(S(rows,'kullanici'))} |")
md.append(f"| Eşzamanlı cihaz (K1b) | {tr(S(nd,'cihaz'))} | {tr(S(rows,'cihaz'))} |")
md.append(f"| Erişim noktası (AP) | {S(nd,'ap')} | {S(rows,'ap')} |")
md.append(f"| Kablolu uç | {tr(S(nd,'kablolu'))} | {tr(S(rows,'kablolu'))} |")
md.append(f"| Erişim katmanı switch'i (ACCESS) | {S(nd,'sw')} | {S(nd,'sw')} |")
md.append(f"| Veri merkezi sunucu switch'i (SERVER_SWITCH) | — | {S(rows,'sw') - S(nd,'sw')} |")
md.append("| Dağıtım switch'i | 3 | 3 |\n| Çekirdek switch | — | 2 |")
yed=[r['kod'] for r in rows if r['yedek'] not in ('Yok','—')];yok=[r['kod'] for r in rows if r['yedek']=='Yok']
md.append(f"| Yedek hattı olan bina | {len(yed)} ({', '.join(yed)}) |")
md.append(f"| Yedek hattı olmayan bina | {len(yok)} ({', '.join(yok)}) |")
md.append(f"| Toplam bina fiberi | {tr(sum(r['birincil_m']+r['yedek_m'] for r in rows))} m |\n")
md.append("## 5. Bilinen sınırlamalar\n")
for s in ["Kat sayıları ve kullanıcı sayıları temsilidir; gerçek kampüs verisi değildir.",
"Her fakülte tek bina olarak modellenmiştir; birden fazla binası olan fakülteler tek noktada gösterilmiştir. Mühendislik Fakültesi için dekanlık binasının konumu kullanılmıştır.",
"Merkez Yemekhane'nin konumu doğrulanamamış, kampüs ortasında tahmini bir nokta seçilmiştir.",
"İnsan ve Toplum Bilimleri Fakültesi haritada \"İnsani ve Sosyal Bilimler Fakültesi\" adıyla bulunmuştur.",
"Fırat Üniversitesi Hastanesi ayrı bina olarak modellenmemiş, Tıp Fakültesi kapsamında düşünülmüştür.",
"Öğrenci yurtları modele alınmamıştır; devlet yurtları üniversiteye değil Kredi ve Yurtlar Kurumu'na bağlıdır.",
"Model gerçek üniversite altyapısı üzerinde doğrulanmamıştır; tasarımın tutarlılığı yalnızca `scripts/topoloji_dogrula.py` ile otomatik olarak sınanmıştır.",
"Yedeklilik ve kapasite değerlendirmesi `docs/ag_modeli.md` ve `docs/dogrulama_raporu.md` dosyalarındadır.",
"K3, K4, K5 ve K9 katsayıları (0,15 · 1,2 · 48 · 1,3) henüz kaynakla desteklenmemiş tasarım varsayımlarıdır."]:
    md.append("- "+s)
open(ROOT/"docs"/"topoloji.md","w",encoding="utf-8").write("\n".join(md)+"\n")
print("topoloji.csv ve topoloji.md yazıldı:", len(rows), "satır")
