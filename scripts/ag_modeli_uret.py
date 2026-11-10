"""Sentetik kampüs ağı cihaz ve bağlantı modelini üretir.

Girdi : data/topoloji.csv  (scripts/topoloji_uret.py çıktısı)
Çıktı : data/devices.csv, data/links.csv

Bu dosyadaki bütün cihazlar, adresler ve bağlantılar SENTETİKTİR.
Fırat Üniversitesi'nin gerçek ağ altyapısını temsil etmez.
Tasarım parametreleri aşağıda tek yerde toplanmıştır; değiştirilirse model yeniden üretilir.
"""
import csv
import ipaddress
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Tasarım parametreleri (sentetik)
# ---------------------------------------------------------------------------
CORE_DEVICES = ["BIDB-CS01", "BIDB-CS02"]
DIST_BY_REGION = {"Batı": "MUH", "Orta": "TEK", "Doğu": "REK"}   # topoloji_uret.py ile aynı
GBPS_BUILDING_UPLINK = 10     # K8: bina -> dağıtım
GBPS_DIST_CORE = 40           # K8: dağıtım -> çekirdek
GBPS_CORE_INTERCONNECT = 40   # tasarım kararı: çekirdek çifti arası
GBPS_SERVER_UPLINK = 10       # tasarım kararı: veri merkezi sunucu switch'i -> çekirdek
GBPS_ACCESS_RING = 10         # tasarım kararı: bina içi katlar arası Ethernet halkası (denetim 2: önceki "STACK", 40 Gbps)
GBPS_AP_PORT = 1              # tasarım kararı: AP erişim portu
DUAL_HOME_DIST_TO_CORE = True # tasarım kararı (D1): her dağıtım switch'i iki çekirdeğe de bağlanır
# Çekirdek yerleşimi. "A": mevcut durum, iki çekirdek BIDB'de. "B": alternatif, CS02 başka binada (sentetik varsayım).
CORE2_SITE = {"A": "BIDB", "B": "KUT"}

# Yönetim (management) adres planı — RFC 1918 özel blok 10.0.0.0/8 içinde
MGMT_INFRA = ipaddress.ip_network("10.0.0.0/24")   # çekirdek ve dağıtım
MGMT_ACCESS = "10.1.{b}.0/24"                       # b = bina sıra numarası
MGMT_AP = "10.2.{b}.0/24"


def read_buildings():
    with open(ROOT / "data" / "topoloji.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("kat", "kullanici", "ap", "sw", "birincil_m", "yedek_m"):
            r[k] = int(r[k])
    return rows


def ds_of(code):
    return f"{code}-DS01"


def build(variant="A"):
    """variant: "A" mevcut tasarım, "B" CS02 farklı binada (fiziksel yedeklilik alternatifi)."""
    rows = read_buildings()
    cs2_site = CORE2_SITE[variant]
    bidx = {r["kod"]: i + 1 for i, r in enumerate(rows)}   # bina sıra numarası (IP planı için)
    byc = {r["kod"]: r for r in rows}
    devices, links = [], []

    def dev(device_id, name, dtype, b, layer, ip, role, floor=""):
        devices.append(dict(device_id=device_id, device_name=name, device_type=dtype,
                            building_id=b, region=byc[b]["bolge"] if b != "BIDB" else "Çekirdek", layer=layer,
                            management_ip=str(ip), status="up", synthetic_data=True,
                            role=role, floor=floor))

    def link(src, dst, ltype, gbps, length, pob, basis, srlg):
        # srlg: ortak fiziksel risk grubu (aynı güzergâh ya da aynı bina); fiziksel ortak arıza testleri için
        links.append(dict(link_id=f"L{len(links) + 1:04d}", source_device=src, target_device=dst,
                          link_type=ltype, bandwidth_gbps=gbps,
                          fiber_length_m=length if length else "", primary_or_backup=pob,
                          status="up", synthetic_data=True, length_basis=basis, srlg=srlg))

    # --- Çekirdek ---------------------------------------------------------
    core_site = {"BIDB-CS01": "BIDB", "BIDB-CS02": cs2_site}
    for i, c in enumerate(CORE_DEVICES, start=1):
        dev(c, f"Çekirdek switch'i {i}", "CORE", core_site[c], "Çekirdek", MGMT_INFRA[i], "core")
    if cs2_site == "BIDB":
        link("BIDB-CS01", "BIDB-CS02", "CORE_INTERCONNECT", GBPS_CORE_INTERCONNECT, None, "PRIMARY",
             "bina içi (veri merkezi) – uzunluk tanımlanmadı", "SITE-BIDB")
    else:
        link("BIDB-CS01", "BIDB-CS02", "CORE_INTERCONNECT", GBPS_CORE_INTERCONNECT, mesafe(byc["BIDB"], byc[cs2_site]), "PRIMARY",
             "K9 (bina koordinatlarından) – senaryo B sentetik varsayımı", f"SRLG-BIDB-{cs2_site}")

    # --- Dağıtım ----------------------------------------------------------
    for i, (region, b) in enumerate(DIST_BY_REGION.items(), start=11):
        dev(ds_of(b), f"{region} bölgesi dağıtım switch'i", "DISTRIBUTION", b, "Dağıtım", MGMT_INFRA[i], "distribution")
    for region, b in DIST_BY_REGION.items():
        d = byc[b]
        m = mesafe(d, byc["BIDB"])
        # Senaryo A'da iki çekirdek hattı aynı güzergâhı izler (aynı SRLG); senaryo B'de CS02 hattı farklı güzergâhtadır
        link(ds_of(b), "BIDB-CS01", "DIST_CORE", GBPS_DIST_CORE, m, "PRIMARY", "K9 (bina koordinatlarından)", f"SRLG-{b}-BIDB")
        if DUAL_HOME_DIST_TO_CORE:
            m2 = mesafe(d, byc[cs2_site])
            link(ds_of(b), "BIDB-CS02", "DIST_CORE", GBPS_DIST_CORE, m2 if m2 else None, "BACKUP",
                 ("K9 (bina koordinatlarından)" if cs2_site == "BIDB" else "K9 – senaryo B sentetik varsayımı") if m2 else "bina içi – uzunluk tanımlanmadı",
                 f"SRLG-{b}-{cs2_site}")

    # --- Erişim switch'leri ve AP'ler --------------------------------------
    for r in rows:
        b, kat, n_sw, n_ap = r["kod"], r["kat"], r["sw"], r["ap"]
        acc_net = ipaddress.ip_network(MGMT_ACCESS.format(b=bidx[b]))
        ap_net = ipaddress.ip_network(MGMT_AP.format(b=bidx[b]))
        is_dc = b == "BIDB"
        pref = "SS" if is_dc else "AS"
        dtype = "SERVER_SWITCH" if is_dc else "ACCESS"
        layer = "Veri merkezi" if is_dc else "Erişim"
        sw_ids = []
        for i in range(1, n_sw + 1):
            sid = f"{b}-{pref}{i:02d}"
            floor = 1 if is_dc else ((i - 1) % kat) + 1
            role = "server" if is_dc else ("uplink-primary" if i == 1 else ("uplink-backup" if i == 2 and r["yedek"] not in ("Yok", "—") else "access"))
            dev(sid, f"{r['ad']} {'sunucu' if is_dc else 'erişim'} switch'i {i}", dtype, b, layer, acc_net[i], role, floor)
            sw_ids.append((sid, floor))

        # Bina içi katlar arası Ethernet halkası: SW01-SW02-...-SWn-SW01 (n=2 ise tek bağlantı).
        # Fiziksel stacking DEĞİLDİR: switch'ler farklı katlardadır. Halka bir Katman-2 döngüsü oluşturur;
        # RSTP (IEEE 802.1w) ile bir bağlantı bloklanır (bkz. docs/ag_modeli.md).
        if not is_dc and n_sw >= 2:
            ids = [s for s, _ in sw_ids]
            pairs = list(zip(ids, ids[1:])) + ([(ids[-1], ids[0])] if n_sw >= 3 else [])
            for a, c in pairs:
                link(a, c, "ACCESS_RING", GBPS_ACCESS_RING, None, "PRIMARY", "bina içi katlar arası – uzunluk tanımlanmadı", f"SITE-{b}")

        # Yukarı bağlantılar
        if is_dc:
            for sid, _ in sw_ids:
                link(sid, "BIDB-CS01", "SERVER_UPLINK", GBPS_SERVER_UPLINK, None, "PRIMARY", "bina içi – uzunluk tanımlanmadı", "SITE-BIDB")
                if cs2_site == "BIDB":
                    link(sid, "BIDB-CS02", "SERVER_UPLINK", GBPS_SERVER_UPLINK, None, "BACKUP", "bina içi – uzunluk tanımlanmadı", "SITE-BIDB")
                else:
                    link(sid, "BIDB-CS02", "SERVER_UPLINK", GBPS_SERVER_UPLINK, mesafe(byc["BIDB"], byc[cs2_site]), "BACKUP",
                         "K9 – senaryo B sentetik varsayımı", f"SRLG-BIDB-{cs2_site}")
        else:
            pd = DIST_BY_REGION[r["bolge"]]
            own = pd == b
            link(sw_ids[0][0], ds_of(pd), "BUILDING_UPLINK", GBPS_BUILDING_UPLINK,
                 None if own else r["birincil_m"], "PRIMARY",
                 "bina içi (dağıtım switch'i aynı binada) – uzunluk tanımlanmadı" if own else "K9 (bina koordinatlarından)",
                 f"SITE-{b}" if own else f"SRLG-{b}-{pd}")
            if r["yedek"] not in ("Yok", "—"):
                bd = r["yedek"].split("-")[0]
                # Yedek hat ikinci switch'ten çıkar: birincil yukarı bağlantı switch'i arızalansa da bina erişimi korunur
                link(sw_ids[1][0], ds_of(bd), "BUILDING_UPLINK", GBPS_BUILDING_UPLINK, r["yedek_m"], "BACKUP",
                     "K9 (bina koordinatlarından)", f"SRLG-{b}-{bd}")

        # AP'ler: katlara sırayla dağıtılır, aynı kattaki switch'lere sırayla bağlanır
        by_floor = {}
        for sid, fl in sw_ids:
            by_floor.setdefault(fl, []).append(sid)
        per_floor_count = {}
        for j in range(1, n_ap + 1):
            fl = 1 if is_dc else ((j - 1) % kat) + 1
            aid = f"{b}-AP{j:03d}"
            dev(aid, f"{r['ad']} erişim noktası {j}", "AP", b, "Kablosuz", ap_net[j], "wireless", fl)
            cands = by_floor.get(fl) or [s for s, _ in sw_ids]
            k = per_floor_count.get(fl, 0)
            per_floor_count[fl] = k + 1
            link(aid, cands[k % len(cands)], "AP_ACCESS", GBPS_AP_PORT, None, "PRIMARY", "bina içi bakır kablo – uzunluk tanımlanmadı", f"SITE-{b}")
    return devices, links


def mesafe(a, b):
    """K9: kuş uçuşu mesafe × 1,3 (topoloji_uret.py ile aynı formül)."""
    la1, lo1, la2, lo2 = map(float, (a["enlem"], a["boylam"], b["enlem"], b["boylam"]))
    R = 6371000
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(h)) * 1.3)


def write(devices, links, folder=ROOT / "data"):
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in (("devices.csv", devices), ("links.csv", links)):
        with open(folder / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)


if __name__ == "__main__":
    d, l = build("A")
    write(d, l)
    print(f"Senaryo A (mevcut): devices.csv {len(d)} cihaz, links.csv {len(l)} bağlantı")
    d, l = build("B")
    write(d, l, ROOT / "data" / "senaryo_b")
    print(f"Senaryo B (CS02 {CORE2_SITE['B']} binasında, sentetik): {len(d)} cihaz, {len(l)} bağlantı -> data/senaryo_b/")
