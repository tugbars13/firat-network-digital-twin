"""Sentetik telemetri üreticisi (şema ve senaryo mantığı).

Bu aşamada büyük bir veri seti üretilmez. Betik, omurga bağlantılarının
(bina–dağıtım, dağıtım–çekirdek, çekirdek arası) her iki ucundaki arayüzler için
dört senaryoda küçük bir örnek üretir: data/ornek_telemetri.csv

Üretilen bütün değerler SİMÜLASYON verisidir; ölçüm değildir.

Kullanım:
    python3 scripts/telemetri_uret.py                       # örnek veri seti
    python3 -c "from telemetri_uret import uret; ..."        # simülatörden çağrı
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Senaryo parametreleri (sentetik)
SENARYOLAR = {
    "normal":        dict(yuk_carpani=0.5, aciklama="Normal çalışma, ders saati dışı ortalama yük"),
    "yogun":         dict(yuk_carpani=1.0, aciklama="Yoğun saat: K1 tepe eşzamanlılığı"),
    "hat_kopmasi":   dict(yuk_carpani=1.0, kopan_hat_binasi="MUH", aciklama="MUH binasının birincil hattı koptu, yedek hat devrede"),
    "cihaz_arizasi": dict(yuk_carpani=1.0, arizali_cihaz="TEK-DS01", aciklama="TEK-DS01 arızalı; yedekli binalar REK-DS01'e geçer, yedeksizler çevrimdışı"),
}
MBPS_KABLOSUZ, MBPS_KABLOLU = 2, 5          # topoloji_dogrula.py ile aynı trafik varsayımı
HOP_GECIKME_MS = 0.4                         # hop başına temel gecikme
YEDEK_YOL_EK_MS = {"BUILDING_UPLINK": 0.6}   # yedek hat daha uzun güzergâh
OMURGA_TURLERI = ("BUILDING_UPLINK", "DIST_CORE", "CORE_INTERCONNECT")


def _oku(ad):
    return list(csv.DictReader(open(ROOT / "data" / ad, encoding="utf-8")))


def _bina_trafigi_mbps(b, carpan):
    return (int(b["cihaz"]) * MBPS_KABLOSUZ + int(b["kablolu"]) * MBPS_KABLOLU) * carpan


def _durum(u):
    """Doluluk oranından gecikme çarpanı ve paket kaybı (basit kuyruk yaklaşımı)."""
    gecikme_carpani = 1 + 2 * u * u
    kayip = 0.0 if u < 0.8 else round((u - 0.8) * 5, 3)
    return gecikme_carpani, kayip


def uret(senaryo, zaman, seed=42):
    """Bir senaryo ve zaman damgası için omurga arayüzlerinin telemetri kayıtlarını döndürür."""
    p = SENARYOLAR[senaryo]
    rnd = random.Random(f"{seed}-{senaryo}-{zaman.isoformat()}")
    bld = {b["kod"]: b for b in _oku("topoloji.csv")}
    dev = {d["device_id"]: d for d in _oku("devices.csv")}
    links = [l for l in _oku("links.csv") if l["link_type"] in OMURGA_TURLERI]

    arizali_cihaz = {p.get("arizali_cihaz")} - {None}
    kopuk = set()
    if "kopan_hat_binasi" in p:
        kopuk |= {l["link_id"] for l in links if l["link_type"] == "BUILDING_UPLINK" and l["primary_or_backup"] == "PRIMARY"
                  and dev[l["source_device"]]["building_id"] == p["kopan_hat_binasi"]}
    calisiyor = lambda l: l["link_id"] not in kopuk and l["source_device"] not in arizali_cihaz and l["target_device"] not in arizali_cihaz

    yuk = {l["link_id"]: 0.0 for l in links}
    # Dağıtım -> çekirdek: birincil hat (CS01) aktif; çalışmıyorsa yedek (CS02)
    dc_aktif = {}
    for ds in {l["source_device"] for l in links if l["link_type"] == "DIST_CORE"}:
        if ds in arizali_cihaz:
            continue
        aday = sorted([l for l in links if l["link_type"] == "DIST_CORE" and l["source_device"] == ds],
                      key=lambda l: l["primary_or_backup"] != "PRIMARY")
        dc_aktif[ds] = next((l for l in aday if calisiyor(l)), None)
    # Bina -> dağıtım: birincil hat aktif; çalışmıyorsa yedek hat
    yedekte = set()
    for kod, b in bld.items():
        if kod == "BIDB":
            continue
        aday = sorted([l for l in links if l["link_type"] == "BUILDING_UPLINK" and dev[l["source_device"]]["building_id"] == kod],
                      key=lambda l: l["primary_or_backup"] != "PRIMARY")
        aktif = next((l for l in aday if calisiyor(l) and dc_aktif.get(l["target_device"])), None)
        if not aktif:
            continue  # bina çevrimdışı: trafiği omurgaya ulaşmaz
        t = _bina_trafigi_mbps(b, p["yuk_carpani"]) * rnd.uniform(0.9, 1.1)
        yuk[aktif["link_id"]] += t
        yuk[dc_aktif[aktif["target_device"]]["link_id"]] += t
        if aktif["primary_or_backup"] == "BACKUP":
            yedekte.add(aktif["link_id"])

    kayitlar = []
    for l in links:
        kap_mbps = float(l["bandwidth_gbps"]) * 1000
        up = calisiyor(l)
        u = min(yuk[l["link_id"]] / kap_mbps, 1.0) if up else 0.0
        gc, kayip = _durum(u)
        hop = {"BUILDING_UPLINK": 2, "DIST_CORE": 1, "CORE_INTERCONNECT": 1}[l["link_type"]]
        gecikme = HOP_GECIKME_MS * hop * gc + (YEDEK_YOL_EK_MS.get(l["link_type"], 0) if l["link_id"] in yedekte else 0)
        for uc in (l["source_device"], l["target_device"]):
            if uc in arizali_cihaz:
                continue  # arızalı cihazdan telemetri gelmez
            kayitlar.append(dict(
                timestamp=zaman.isoformat(), scenario=senaryo, device_id=uc,
                interface_id=f"{uc}:{l['link_id']}",
                latency_ms=round(gecikme * rnd.uniform(0.95, 1.05), 3) if up else "",
                bandwidth_usage_mbps=round(yuk[l["link_id"]], 1) if up else 0.0,
                packet_loss_percent=kayip if up else 100.0,
                cpu_usage_percent=round(min(95, 15 + 40 * u + rnd.uniform(-3, 3)), 1),
                memory_usage_percent=round(min(90, 35 + 10 * u + rnd.uniform(-2, 2)), 1),
                link_status="up" if up else "down",
                synthetic_data=True))
    return kayitlar


if __name__ == "__main__":
    t0 = datetime(2026, 11, 10, 14, 0, 0)
    satirlar = []
    for s in SENARYOLAR:
        for i in range(3):  # her senaryo için 1'er dakika arayla 3 zaman damgası
            satirlar += uret(s, t0 + timedelta(minutes=i))
    with open(ROOT / "data" / "ornek_telemetri.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print(f"ornek_telemetri.csv: {len(satirlar)} kayıt ({len(SENARYOLAR)} senaryo × 3 zaman damgası)")
