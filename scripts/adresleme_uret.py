"""Batfish–FRR deneyleri için sentetik adresleme ve yönlendirme modeli.

Girdi : data/topoloji.csv, data/devices.csv, data/links.csv
Çıktı : data/vlans.csv, data/p2p_links.csv, data/routers.csv

Bu aşamada cihaz yapılandırması (FRR config) ÜRETİLMEZ; yalnızca yapılandırmanın
dayanacağı tutarlı adres ve yönlendirme verisi hazırlanır. Bütün değerler sentetiktir.

Tasarım özeti (ayrıntılar: docs/batfish_frr_hazirlik.md):
- Katman 3 sınırı bina içindedir (routed access): binanın yukarı bağlantı switch'leri
  (AS01 ve yedekli binalarda AS02) bina VLAN'larının ağ geçididir. Katman 2 bina dışına çıkmaz.
- Omurga bağlantıları (bina–dağıtım, dağıtım–çekirdek, çekirdek arası) /31 noktadan noktaya yönlendirilmiş hatlardır.
- Tek OSPF alanı (alan 0). Yedek hatlar OSPF maliyetiyle aktif-pasif ya da aktif-aktif çalışır.
"""
import csv
import ipaddress
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Adres blokları (RFC 1918, sentetik)
LOOPBACK_NET = ipaddress.ip_network("10.254.0.0/24")
P2P_NET = ipaddress.ip_network("10.255.0.0/24")
TRANSIT_FMT = "10.253.{b}.0/29"           # yedekli binada AS01–AS02 Katman 3 transit VLAN'ı
CLIENT_SPACE = ipaddress.ip_network("172.16.0.0/12")  # bina başına bir /20
SERVER_NET = ipaddress.ip_network("10.10.0.0/24")     # veri merkezi sunucu VLAN'ı

# VLAN tasarımı (bütün binalarda aynı numaralar)
VLANS = [
    # (id, ad, amaç)
    (10, "YONETIM-SW", "Switch yönetimi"),
    (11, "YONETIM-AP", "AP yönetimi"),
    (100, "OGRENCI-KABLOSUZ", "Öğrenci kablosuz istemcileri"),
    (110, "PERSONEL-KABLOSUZ", "Personel kablosuz istemcileri"),
    (200, "KABLOLU", "Kablolu uçlar (laboratuvar, ofis, yazıcı, kamera)"),
]
OGRENCI_ORANI = 0.85       # sentetik: eşzamanlı kablosuz cihazların öğrenci payı
ADRES_PAYI = 1.25          # sentetik: alt ağ boyutlandırmada %25 pay

# OSPF maliyetleri (açıkça atanır; referans bant genişliğine bırakılmaz)
COST = {
    ("BUILDING_UPLINK", "PRIMARY"): (10, 10),    # (aktif-pasif, aktif-aktif)
    ("BUILDING_UPLINK", "BACKUP"): (100, 10),
    ("DIST_CORE", "PRIMARY"): (5, 5),
    ("DIST_CORE", "BACKUP"): (50, 5),
    ("CORE_INTERCONNECT", "PRIMARY"): (5, 5),
    ("TRANSIT", ""): (10, 10),
}


def rd(n):
    return list(csv.DictReader(open(ROOT / "data" / n, encoding="utf-8")))


def subnet_for(need):
    """İhtiyaç duyulan ana bilgisayar sayısını (pay dahil) karşılayan en küçük önek uzunluğu."""
    hosts = math.ceil(need * ADRES_PAYI) + 3          # ağ geçidi VIP + iki fiziksel ağ geçidi
    return 32 - math.ceil(math.log2(hosts + 2))


def build():
    bld = rd("topoloji.csv")
    devices = {d["device_id"]: d for d in rd("devices.csv")}
    links = rd("links.csv")
    bidx = {r["kod"]: i + 1 for i, r in enumerate(bld)}
    client_blocks = list(CLIENT_SPACE.subnets(new_prefix=20))

    # --- Katman 3 cihazları (OSPF yönlendiricileri) -------------------------------
    l3 = [d for d in devices.values() if d["device_type"] in ("CORE", "DISTRIBUTION")]
    l3 += [d for d in devices.values() if d["role"] in ("uplink-primary", "uplink-backup")]
    lo = iter(LOOPBACK_NET.hosts())
    routers = {}
    for d in sorted(l3, key=lambda x: ({"CORE": 0, "DISTRIBUTION": 1}.get(x["device_type"], 2), x["device_id"])):
        ip = next(lo)
        routers[d["device_id"]] = dict(device_id=d["device_id"], device_type=d["device_type"], building_id=d["building_id"],
                                       role=d["role"], loopback_ip=f"{ip}/32", router_id=str(ip), ospf_area="0.0.0.0",
                                       ospf_neighbors=0, vrrp_role="", synthetic_data=True)

    # --- Noktadan noktaya /31 hatlar ----------------------------------------------
    p2p = []
    pool = iter(P2P_NET.subnets(new_prefix=31))
    for l in links:
        if l["link_type"] not in ("BUILDING_UPLINK", "DIST_CORE", "CORE_INTERCONNECT"):
            continue
        net = next(pool)
        a, b = l["source_device"], l["target_device"]
        c_ap, c_aa = COST[(l["link_type"], l["primary_or_backup"])]
        p2p.append(dict(link_id=l["link_id"], link_type=l["link_type"], primary_or_backup=l["primary_or_backup"],
                        a_device=a, a_ip=f"{net[0]}/31", b_device=b, b_ip=f"{net[1]}/31", subnet=str(net),
                        ospf_area="0.0.0.0", ospf_network_type="point-to-point",
                        ospf_cost_aktif_pasif=c_ap, ospf_cost_aktif_aktif=c_aa, synthetic_data=True))
        routers[a]["ospf_neighbors"] += 1
        routers[b]["ospf_neighbors"] += 1

    # --- VLAN'lar ------------------------------------------------------------------
    vlans = []
    for r in bld:
        b = r["kod"]
        gw1 = f"{b}-AS01" if b != "BIDB" else "BIDB-CS01"
        yedekli = r["yedek"] not in ("Yok", "—")
        gw2 = f"{b}-AS02" if yedekli else ("BIDB-CS02" if b == "BIDB" else "")
        gws = ";".join(x for x in (gw1, gw2) if x)
        cihaz, kablolu = int(r["cihaz"]), int(r["kablolu"])
        ogr = math.ceil(cihaz * OGRENCI_ORANI)
        per = cihaz - ogr
        need = {10: int(r["sw"]), 11: int(r["ap"]), 100: ogr, 110: per, 200: kablolu}
        block = client_blocks[bidx[b] - 1]
        # İstemci VLAN'ları binanın /20 bloğundan sırayla, en büyükten küçüğe ayrılır
        free = [block]
        alloc = {}
        for vid in sorted((100, 110, 200), key=lambda v: -need[v]):
            plen = subnet_for(need[vid])
            free.sort(key=lambda n: n.prefixlen, reverse=True)  # en küçük uygun bloktan başla
            for i, f in enumerate(free):
                if f.prefixlen <= plen:
                    sub = list(f.subnets(new_prefix=plen))
                    alloc[vid] = sub[0]
                    rest = [x for x in f.address_exclude(sub[0])]
                    free = free[:i] + free[i + 1:] + rest
                    break
            else:
                raise ValueError(f"{b} VLAN {vid}: /20 bloğa sığmadı")
        alloc[10] = ipaddress.ip_network(f"10.1.{bidx[b]}.0/24")
        alloc[11] = ipaddress.ip_network(f"10.2.{bidx[b]}.0/24")
        # VRRP ana yönlendiricisi: aktif-aktif için VLAN bazında paylaştırılır (öğrenci AS01, diğerleri AS02)
        for vid, name, purpose in VLANS:
            net = alloc[vid]
            master = gw1 if (vid in (10, 11, 100) or not gw2) else gw2
            if vid in (10, 11):
                # Yönetim VLAN'larında cihaz yönetim adresleri .1'den başlar (devices.csv).
                # Bu yüzden VIP en son adrese (.254) konur; ağ geçidi switch'inin kendi
                # yönetim adresi bu ağdaysa SVI adresi olarak o kullanılır, değilse .252/.253.
                vip = net[-2]
                phys = []
                for i, g in enumerate(x for x in (gw1, gw2) if x):
                    mip = ipaddress.ip_address(devices[g]["management_ip"])
                    phys.append(mip if mip in net else net[-4 + i])
            else:
                # İstemci VLAN'larında VIP .1, fiziksel ağ geçitleri .2 ve .3 (DHCP havuzu .4'ten başlar)
                vip = net[1]
                phys = [net[2 + i] for i, g in enumerate(x for x in (gw1, gw2) if x)]
            vlans.append(dict(building_id=b, vlan_id=vid, vlan_name=name, purpose=purpose, subnet=str(net),
                              gateway_vip=str(vip), gateway_devices=gws, gateway_ips=";".join(map(str, phys)),
                              vrrp_master_aktif_aktif=master,
                              vrrp_master_aktif_pasif=gw1, need_hosts=need[vid], capacity_hosts=net.num_addresses - 2 - 3,
                              synthetic_data=True))
        if b == "BIDB":
            vlans.append(dict(building_id=b, vlan_id=300, vlan_name="SUNUCU", purpose="Veri merkezi sunucuları",
                              subnet=str(SERVER_NET), gateway_vip=str(SERVER_NET[1]), gateway_devices="BIDB-CS01;BIDB-CS02",
                              gateway_ips=f"{SERVER_NET[2]};{SERVER_NET[3]}",
                              vrrp_master_aktif_aktif="BIDB-CS01", vrrp_master_aktif_pasif="BIDB-CS01",
                              need_hosts=kablolu, capacity_hosts=SERVER_NET.num_addresses - 2 - 3, synthetic_data=True))
        if yedekli:
            t = ipaddress.ip_network(TRANSIT_FMT.format(b=bidx[b]))
            vlans.append(dict(building_id=b, vlan_id=900, vlan_name="L3-TRANSIT", purpose="AS01–AS02 OSPF komşuluğu",
                              subnet=str(t), gateway_vip="", gateway_devices=gws, gateway_ips=f"{t[1]};{t[2]}",
                              vrrp_master_aktif_aktif="", vrrp_master_aktif_pasif="",
                              need_hosts=2, capacity_hosts=t.num_addresses - 2, synthetic_data=True))
            routers[gw1]["ospf_neighbors"] += 1
            routers[gw2]["ospf_neighbors"] += 1
            routers[gw1]["vrrp_role"] = "VRRP: tüm VLAN'larda öncelikli (aktif-pasif); 10/11/100 ana (aktif-aktif)"
            routers[gw2]["vrrp_role"] = "VRRP: yedek (aktif-pasif); 110/200 ana (aktif-aktif)"
        elif b != "BIDB":
            routers[gw1]["vrrp_role"] = "Tek ağ geçidi (VRRP yok)"
    for c in ("BIDB-CS01", "BIDB-CS02"):
        routers[c]["vrrp_role"] = "BIDB VLAN'ları ve sunucu VLAN'ı ağ geçidi (VRRP)"
    return vlans, p2p, list(routers.values())


def write(vlans, p2p, routers):
    for name, data in (("vlans.csv", vlans), ("p2p_links.csv", p2p), ("routers.csv", routers)):
        with open(ROOT / "data" / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)


if __name__ == "__main__":
    v, p, r = build()
    write(v, p, r)
    print(f"vlans.csv: {len(v)} VLAN, p2p_links.csv: {len(p)} /31 hat, routers.csv: {len(r)} OSPF yönlendiricisi")
