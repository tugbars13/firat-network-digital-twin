import math, csv
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
        rows.append(dict(kod=kod,ad=ad,tur=tur,kat=kat,kullanici=kul,eszamanli=round(kul*0.6),ap=kat*2,kablolu=60,port=0,sw=4,yerleske="Rektörlük Yerleşkesi",bolge="Çekirdek",birincil="—",birincil_m=0,yedek="—",yedek_m=0,kural_yedek="Çekirdek katmanı",enlem=la,boylam=lo,konum_kaynagi=kay));continue
    esz=math.ceil(kul*0.6); ap=max(math.ceil(esz/30),kat); kablolu=math.ceil(kul*0.15)
    port=math.ceil((ap+kablolu)*1.2); sw=max(kat,math.ceil(port/48))
    bz=bolge(lo); d=DIST[bz]
    if d==kod: birincil="Kendi binası (dağıtım burada)"; bm=0
    else: birincil=f"{d}-DS01 ({bz})"; bm=mesafe(kod,d)
    yedekli=kul>=1500 or krit
    if yedekli: yb=BACKUP_TO[bz]; yedek=f"{DIST[yb]}-DS01 ({yb})"; ym=mesafe(kod,DIST[yb])
    else: yedek="Yok"; ym=0
    neden=("kullanıcı ≥ 1.500" if kul>=1500 else "kritik hizmet") if yedekli else "kullanıcı < 1.500, kritik değil"
    rows.append(dict(kod=kod,ad=ad,tur=tur,kat=kat,kullanici=kul,eszamanli=esz,ap=ap,kablolu=kablolu,port=port,sw=sw,yerleske=YERLESKE[bz],bolge=bz,birincil=birincil,birincil_m=bm,yedek=yedek,yedek_m=ym,kural_yedek=neden,enlem=la,boylam=lo,konum_kaynagi=kay))
with open("topoloji.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
tr=lambda n:f"{n:,}".replace(",",".")
md=["# Ağ Topolojisi Tablosu\n",
"Bu tablo Fırat Üniversitesi kampüs ağının sentetik (uydurma ama kurallı) modelidir. Cihaz sayıları aşağıdaki kurallardan hesaplanmıştır, elle yazılmamıştır.\n",
"## 0. Veri kaynakları ve varsayımlar\n",
"| Bilgi | Kaynak | Durum |\n|---|---|---|",
"| Fakülte listesi | Fırat Üniversitesi resmî sitesi (https://www.firat.edu.tr/tr/page/event/fakulteler-mezuniyet-toreni-ikinci-grup-7452) | Gerçek |",
"| Bina konumları | Google Haritalar ve OpenStreetMap (her binanın kaynağı tabloda) | Gerçek, yalnız Merkez Yemekhane tahmini |",
"| İki ana yerleşke (Mühendislik ve Rektörlük) | Fırat Üniversitesi SKS Daire Başkanlığı sitesi | Gerçek |",
"| Kat sayıları ve kullanıcı sayıları | — | Temsili varsayım |",
"| Ağ cihazları, bağlantılar, katsayılar | Bu belgedeki kurallar | Sentetik (projenin tasarımı) |\n",
"## 1. Boyutlandırma kuralları\n",
"| Kural | Tanım | Gerekçe |\n|---|---|---|",
"| K1 · Eşzamanlı kullanıcı | Tepe kullanıcı × 0,6 | Tepe saatte binadakilerin yaklaşık %60'ı aynı anda ağa bağlı kabul edilmiştir |",
"| K2 · Erişim noktası (AP) | max(⌈eşzamanlı ÷ 30⌉, kat sayısı) | Bir AP ~30 kullanıcıya rahat hizmet verir; her katta en az bir AP |",
"| K3 · Kablolu uç | ⌈tepe kullanıcı × 0,15⌉ | Laboratuvar bilgisayarları, ofisler, yazıcılar, kameralar |",
"| K4 · Port ihtiyacı | ⌈(AP + kablolu uç) × 1,2⌉ | Her AP bir port kullanır; %20 büyüme payı |",
"| K5 · Erişim switch'i | max(kat sayısı, ⌈port ÷ 48⌉) | 48 portlu switch; her katta en az bir kat dolabı |",
"| K6 · Bölge | Binanın gerçek boylamına göre: Batı (< 39,192), Orta (39,192–39,199), Doğu (> 39,199) | Batı bölgesi Mühendislik Yerleşkesi'ne, Orta ve Doğu Rektörlük Yerleşkesi'ne karşılık gelir |",
"| K7 · Yedek hat | Tepe kullanıcı ≥ 1.500 **veya** kritik hizmet | Bu binalar komşu bölgenin dağıtım switch'ine ikinci bir fiber hatla da bağlanır |",
"| K8 · Hat kapasitesi | Bina → dağıtım: 10 Gbps; dağıtım → çekirdek: 40 Gbps | Kurumsal kampüs ağlarında yaygın değerler |",
"| K9 · Fiber uzunluğu | İki bina arası kuş uçuşu mesafe × 1,3 | Kablo yol ve kanal güzergâhını izlediği için %30 pay |\n",
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
md.append("\nEşzamanlı kullanıcı (K1), kablolu uç (K3) ve port (K4) ara değerleri `data/topoloji.csv` dosyasında yer alır. Veri merkezi satırı kurallarla değil, elle belirlenmiştir: 2 çekirdek ve 2 sunucu switch'i.\n")
md.append("## 4. Özet\n")
md.append("| Kalem | Toplam |\n|---|---|")
md.append(f"| Bina (veri merkezi hariç) | {len(rows)-1} |")
md.append(f"| Tepe kullanıcı | {tr(sum(r['kullanici'] for r in rows))} |")
md.append(f"| Erişim noktası | {sum(r['ap'] for r in rows)} |")
md.append(f"| Erişim switch'i | {sum(r['sw'] for r in rows if r['kod']!='BIDB')} |")
md.append("| Dağıtım switch'i | 3 |\n| Çekirdek switch | 2 |")
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
"Dağıtım switch'ini barındıran binalar (MUH, TEK, REK) kendi switch'leri arızalanırsa yedek hatla komşu bölgeye geçer.",
"Katsayılar (0,6 · 30 · 0,15 · 1,2 · 1,3) varsayımdır ve raporda kaynakla desteklenmelidir."]:
    md.append("- "+s)
open("topoloji.md","w",encoding="utf-8").write("\n".join(md)+"\n")
for r in rows: print(r['kod'],r['bolge'],r['birincil'],r['birincil_m'],r['yedek'],r['yedek_m'])
print(sum(r['ap'] for r in rows), sum(r['sw'] for r in rows if r['kod']!='BIDB'))
