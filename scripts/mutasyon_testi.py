"""Hata enjeksiyonu (mutasyon) testi: doğrulayıcı gerçekten hata yakalıyor mu?

Her mutasyon, verinin geçici bir kopyasına tek bir bilinçli hata ekler ve
topoloji_dogrula.py'yi bu kopya üzerinde çalıştırır. Beklenen: doğrulayıcının
çıkış kodu 1 olması ve hatayı hedefleyen testin BAŞARISIZ olması.
Asıl veri (data/) hiçbir zaman değiştirilmez.

Çalıştırma: python3 scripts/mutasyon_testi.py
Çıktı    : docs/mutasyon_testi.md
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "topoloji_dogrula.py"


def rw(path, fn):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    fields = list(rows[0].keys())
    rows = fn(rows)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def setf(match, **kv):
    def fn(rows):
        for r in rows:
            if match(r):
                r.update(kv)
        return rows
    return fn


def drop(match):
    return lambda rows: [r for r in rows if not match(r)]


# (ad, beklenen başarısız test(ler), uygulanacak değişiklikler: [(dosya, fonksiyon)])
MUTATIONS = [
    ("Yinelenen cihaz kimliği", ["T1"],
     [("data/devices.csv", lambda rows: rows + [dict(rows[-1])])]),
    ("Var olmayan cihaza bağlantı", ["T3"],
     [("data/links.csv", setf(lambda r: r["link_id"] == "L0118", target_device="YOK-DS99"))]),
    ("Yinelenen yönetim IP adresi", ["T8"],
     [("data/devices.csv", setf(lambda r: r["device_id"] == "MUH-AS02", management_ip="10.1.3.1"))]),
    ("K9 dışı fiber uzunluğu (1663 → 1500)", ["T14"],
     [("data/links.csv", setf(lambda r: r["link_id"] == "L0002", fiber_length_m="1500"))]),
    ("Yedek hat birincil ile aynı dağıtıma bağlandı (MUH-AS02 → MUH-DS01)", ["T18"],
     [("data/links.csv", setf(lambda r: r["link_id"] == "L0048", target_device="MUH-DS01"))]),
    ("Sunucu switch'i ACCESS olarak etiketlendi", ["T16"],
     [("data/devices.csv", setf(lambda r: r["device_id"] == "BIDB-SS02", device_type="ACCESS", role="access"))]),
    ("Halka bağlantısı STACK olarak geri yazıldı", ["T17"],
     [("data/links.csv", setf(lambda r: r["link_id"] == next_ring_id(), link_type="STACK"))]),
    ("Halkada bir bağlantı silindi (döngü kırıldı)", ["T17"],
     [("data/links.csv", drop(lambda r: r["link_id"] == next_ring_id()))]),
    ("Yedek hatlı binanın yedek hattı kaldırıldı (KUT)", ["T18"],
     [("data/links.csv", drop(lambda r: r["link_id"] == "L0495"))]),
    ("Dağıtım–çekirdek hattından SRLG bilgisi silindi", ["T19"],
     [("data/links.csv", setf(lambda r: r["link_id"] == "L0004", srlg=""))]),
    ("Bina yedek hattının uzunluğu boşaltıldı", ["T20"],
     [("data/links.csv", setf(lambda r: r["link_id"] == "L0024", fiber_length_m=""))]),
    ("Aktif-aktif bölüşümü bozuldu (öğrenci payı yerine tüm yük hat 1'e)", ["T21"],
     [("scripts/topoloji_dogrula.py", None)]),
    ("İki VLAN'a aynı alt ağ verildi", ["T22"],
     [("data/vlans.csv", setf(lambda r: r["building_id"] == "ILH" and r["vlan_id"] == "110", subnet="172.16.48.0/21"))]),
    ("VRRP VIP bir switch'in yönetim adresine eşit", ["T22"],
     [("data/vlans.csv", setf(lambda r: r["building_id"] == "MUH" and r["vlan_id"] == "10", gateway_vip="10.1.3.1"))]),
    ("Senaryo B'de fazladan cihaz", ["T23"],
     [("data/senaryo_b/devices.csv", lambda rows: rows + [dict(rows[-1], device_id="FAZLA-AP")])]),
]


def next_ring_id():
    for r in csv.DictReader(open(ROOT / "data" / "links.csv", encoding="utf-8")):
        if r["link_type"] == "ACCESS_RING":
            return r["link_id"]


def run(tmp):
    env = dict(os.environ, DT_ROOT=str(tmp))
    p = subprocess.run([sys.executable, str(tmp / "scripts" / "topoloji_dogrula.py")], env=env, capture_output=True, text=True)
    failed = []
    js = tmp / "data" / "dogrulama_sonuclari.json"
    if js.exists() and p.returncode in (0, 1):
        try:
            failed = [t["test"].split()[0] for t in json.load(open(js, encoding="utf-8"))["testler"] if t["sonuc"] != "BAŞARILI"]
        except Exception:
            pass
    return p.returncode, failed, p.stderr.strip().splitlines()[-1:] if p.returncode not in (0, 1) else []


def main():
    rows = []
    for name, expected, changes in MUTATIONS:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            shutil.copytree(ROOT / "data", tmp / "data")
            shutil.copytree(ROOT / "scripts", tmp / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
            (tmp / "docs").mkdir()
            for path, fn in changes:
                if fn is None:   # kod mutasyonu
                    p = tmp / path
                    s = p.read_text(encoding="utf-8")
                    s = s.replace("s1 = math.ceil(cihaz * STUDENT_SHARE) * MBPS_PER_WIRELESS_DEVICE / 1000",
                                  "s1 = tot", 1)
                    p.write_text(s, encoding="utf-8")
                else:
                    rw(tmp / path, fn)
            code, failed, err = run(tmp)
            caught = code == 1 and all(e in failed for e in expected)
            rows.append(dict(mutasyon=name, beklenen=expected, cikis_kodu=code, basarisiz=failed, yakalandi=caught, hata=err))
    # Kontrol: değiştirilmemiş kopya temiz geçmeli
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        shutil.copytree(ROOT / "data", tmp / "data")
        shutil.copytree(ROOT / "scripts", tmp / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        (tmp / "docs").mkdir()
        code, failed, err = run(tmp)
        control = dict(cikis_kodu=code, basarisiz=failed)

    ok = sum(r["yakalandi"] for r in rows)
    o = ["# Mutasyon (hata enjeksiyonu) testi\n",
         "> `scripts/mutasyon_testi.py` tarafından otomatik üretilir. Her satırda verinin geçici bir kopyasına tek bir bilinçli hata eklenir; "
         "asıl veri değiştirilmez. Doğrulayıcı hatayı yakalarsa çıkış kodu 1 olur ve hedef test BAŞARISIZ görünür.\n",
         f"**Kontrol çalıştırması (hatasız kopya):** çıkış kodu {control['cikis_kodu']}, başarısız test: {', '.join(control['basarisiz']) or 'yok'}.\n",
         f"**Sonuç:** {ok}/{len(rows)} mutasyon yakalandı.\n",
         "| # | Eklenen hata | Hedef test | Çıkış kodu | Başarısız olan testler | Yakalandı mı |", "|---|---|---|---:|---|---|"]
    for i, r in enumerate(rows, 1):
        o.append(f"| M{i} | {r['mutasyon']} | {', '.join(r['beklenen'])} | {r['cikis_kodu']} | {', '.join(r['basarisiz']) or '—'} "
                 f"| {'✅ evet' if r['yakalandi'] else '❌ HAYIR'}{(' – ' + r['hata'][0]) if r['hata'] else ''} |")
    o.append("\nBir mutasyon birden fazla testi düşürebilir; bu beklenen bir durumdur (ör. bir halka bağlantısı silinince "
             "bağlantı sayısı da değişir). Önemli olan hedef testin hatayı yakalamasıdır.")
    (ROOT / "docs" / "mutasyon_testi.md").write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"Kontrol: çıkış {control['cikis_kodu']}; mutasyon: {ok}/{len(rows)} yakalandı; rapor: docs/mutasyon_testi.md")
    for r in rows:
        print(("  ok   " if r["yakalandi"] else "  KAÇTI ") + r["mutasyon"], r["cikis_kodu"], r["basarisiz"], r["hata"])
    sys.exit(0 if ok == len(rows) and control["cikis_kodu"] == 0 else 1)


if __name__ == "__main__":
    main()
