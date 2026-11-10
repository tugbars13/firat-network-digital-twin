"""Sentetik kampüs ağı topolojisini otomatik olarak doğrular.

Girdi : data/topoloji.csv, data/devices.csv, data/links.csv
        data/senaryo_b/devices.csv, data/senaryo_b/links.csv (fiziksel yedeklilik alternatifi)
        data/vlans.csv, data/p2p_links.csv, data/routers.csv (Batfish–FRR adresleme modeli)
Çıktı : docs/dogrulama_raporu.md, data/dogrulama_sonuclari.json
Çıkış kodu: herhangi bir yapısal test BAŞARISIZ ise 1, aksi hâlde 0.

Arıza senaryoları ve kapasite değerlendirmesi bilgi amaçlıdır; sonuçları rapora
olduğu gibi yazılır (olumsuz sonuçlar gizlenmez).
"""
import csv
import ipaddress
import itertools
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

import os

# DT_ROOT: hata enjeksiyonu (mutasyon) testinde verinin geçici bir kopyası üzerinde çalışmak için
ROOT = Path(os.environ.get("DT_ROOT", Path(__file__).resolve().parent.parent))

# Kapasite değerlendirmesi için sentetik trafik varsayımları (ölçüm değildir)
OVERSUB_TARGET = 20          # Cisco (2013): erişim katmanı 20:1 aşırı abonelik
EDGE_PORT_GBPS = 1           # tasarım parametresi: uç port hızı
MBPS_PER_WIRELESS_DEVICE = 2 # tasarım parametresi: eşzamanlı kablosuz cihaz başına ortalama trafik
MBPS_PER_WIRED_ENDPOINT = 5  # tasarım parametresi: kablolu uç başına ortalama trafik
UPLINK_GBPS = 10             # K8: bina -> dağıtım
DIST_CORE_GBPS = 40          # K8: dağıtım -> çekirdek
STUDENT_SHARE = 0.85         # adresleme_uret.py ile aynı: eşzamanlı kablosuz cihazların öğrenci payı
EXPECTED_RING = 108          # birinci denetimde sayılan bina içi halka bağlantısı (değiştirilmedi)
OLD_FIBER_M = 13517          # birinci denetim öncesi raporlanan toplam (yalnız bina hatları)


def load(folder="data"):
    rd = lambda n, f=folder: list(csv.DictReader(open(ROOT / f / n, encoding="utf-8")))
    return rd("topoloji.csv", "data"), rd("devices.csv"), rd("links.csv")


EDGE_TYPES = ("ACCESS", "SERVER_SWITCH", "AP")   # bina içi uç cihazlar (etki sayımında kullanılır)


def graph(devices, links, drop_nodes=(), drop_links=()):
    g = nx.MultiGraph()
    for d in devices:
        if d["device_id"] not in drop_nodes:
            g.add_node(d["device_id"])
    for l in links:
        if l["link_id"] in drop_links:
            continue
        a, b = l["source_device"], l["target_device"]
        if a in g and b in g:
            g.add_edge(a, b, key=l["link_id"])
    return g


class Ctx:
    def __init__(self, bld, devices, links):
        self.bld, self.devices, self.links = bld, devices, links
        self.dev = {d["device_id"]: d for d in devices}
        self.aps = defaultdict(list)
        for d in devices:
            if d["device_type"] == "AP":
                self.aps[d["building_id"]].append(d["device_id"])
        self.cores = [d["device_id"] for d in devices if d["device_type"] == "CORE"]
        self.edge = defaultdict(list)
        for d in devices:
            if d["device_type"] in EDGE_TYPES:
                self.edge[d["building_id"]].append(d["device_id"])

    def impact(self, drop_nodes=(), drop_links=()):
        """Arızanın etkisi: çevrimdışı/kısmi binalar, kaybedilen AP ve uç cihaz (erişim, sunucu switch'i, AP) sayısı."""
        g = graph(self.devices, self.links, drop_nodes, drop_links)
        reach = set()
        for c in self.cores:
            if c in g:
                reach |= nx.node_connected_component(g, c)
        per = {}
        for b in self.edge:
            aps = self.aps.get(b, [])
            ok = sum(1 for a in aps if a in reach)
            lost_dev = sum(1 for x in self.edge[b] if x not in reach)
            per[b] = dict(ap_ok=ok, ap_n=len(aps), cihaz_kayip=lost_dev)
        off = sorted(b for b, v in per.items() if v["ap_n"] and v["ap_ok"] == 0)
        part = sorted(b for b, v in per.items() if 0 < v["ap_ok"] < v["ap_n"])
        return dict(cevrimdisi=off, kismi=part, ap_kayip=sum(v["ap_n"] - v["ap_ok"] for v in per.values()),
                    cihaz_kayip=sum(v["cihaz_kayip"] for v in per.values()), bina=per)

    def service(self, drop_nodes=(), drop_links=()):
        """Her bina için çekirdeğe ulaşabilen AP oranı."""
        g = graph(self.devices, self.links, drop_nodes, drop_links)
        reach = set()
        for c in self.cores:
            if c in g:
                reach |= nx.node_connected_component(g, c)
        out = {}
        for b, aps in self.aps.items():
            ok = sum(1 for a in aps if a in reach)
            out[b] = (ok, len(aps))
        return out


def summarize(svc):
    off = [b for b, (ok, n) in svc.items() if ok == 0]
    part = [f"{b} ({n - ok}/{n} AP)" for b, (ok, n) in svc.items() if 0 < ok < n]
    lost_ap = sum(n - ok for ok, n in svc.values())
    return off, part, lost_ap


# ---------------------------------------------------------------------------
def structural_tests(ctx):
    bld, devices, links = ctx.bld, ctx.devices, ctx.links
    T = []
    add = lambda name, ok, detail="": T.append(dict(test=name, sonuc="BAŞARILI" if ok else "BAŞARISIZ", ayrinti=detail))

    ids = [d["device_id"] for d in devices]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    add("Her cihazın benzersiz kimliği var", not dup, f"{len(ids)} cihaz; yinelenen: {dup or 'yok'}")

    lids = [l["link_id"] for l in links]
    dupl = [k for k, v in Counter(lids).items() if v > 1]
    add("Bağlantı kimlikleri benzersiz", not dupl, f"{len(lids)} bağlantı; yinelenen: {dupl or 'yok'}")

    bad_end = [l["link_id"] for l in links if l["source_device"] not in ctx.dev or l["target_device"] not in ctx.dev]
    add("Her bağlantının iki ucu devices.csv içinde", not bad_end, f"geçersiz uç: {bad_end or 'yok'}")

    loops = [l["link_id"] for l in links if l["source_device"] == l["target_device"]]
    add("Kendine bağlanan cihaz yok", not loops, f"{loops or 'yok'}")

    pairs = Counter((tuple(sorted((l["source_device"], l["target_device"]))), l["link_type"]) for l in links)
    par = [p for p, c in pairs.items() if c > 1]
    add("Aynı iki cihaz arasında aynı türde yinelenen bağlantı yok", not par, f"{par or 'yok'}")

    g = graph(devices, links)
    iso = [n for n in g.nodes if g.degree(n) == 0]
    add("İzole cihaz yok", not iso, f"{iso or 'yok'}")
    add("Ağ grafiği tek parça (bağlı)", nx.is_connected(nx.Graph(g)), f"bileşen sayısı: {nx.number_connected_components(nx.Graph(g))}")

    ips = [d["management_ip"] for d in devices]
    dupip = [k for k, v in Counter(ips).items() if v > 1]
    priv = all(ipaddress.ip_address(i).is_private for i in ips)
    add("Yönetim IP adresleri benzersiz ve özel (RFC 1918)", not dupip and priv, f"yinelenen: {dupip or 'yok'}; tümü özel: {priv}")

    ds = [d for d in devices if d["device_type"] == "DISTRIBUTION"]
    ds_core = {x["device_id"]: sorted({l["target_device"] for l in links if l["source_device"] == x["device_id"] and l["link_type"] == "DIST_CORE"}) for x in ds}
    add("Her dağıtım switch'i çekirdeğe bağlı", all(ds_core.values()), "; ".join(f"{k} → {', '.join(v)}" for k, v in ds_core.items()))
    add("Çekirdek switch'leri birbirine bağlı",
        any(l["link_type"] == "CORE_INTERCONNECT" for l in links), "BIDB-CS01 ↔ BIDB-CS02")

    cnt_ap = Counter(d["building_id"] for d in devices if d["device_type"] == "AP")
    cnt_sw = Counter(d["building_id"] for d in devices if d["device_type"] in ("ACCESS", "SERVER_SWITCH"))
    mism = [b["kod"] for b in bld if cnt_ap[b["kod"]] != int(b["ap"]) or cnt_sw[b["kod"]] != int(b["sw"])]
    add("Cihaz envanteri topoloji.csv ile birebir uyumlu (AP ve erişim/sunucu switch'i)", not mism, f"uyumsuz bina: {mism or 'yok'}")

    # Hesap kuralları yeniden uygulanır
    calc_err = []
    for b in bld:
        if b["deger_turu"] != "hesaplanan":
            continue
        kul, kat = int(b["kullanici"]), int(b["kat"])
        esz = math.ceil(kul * 0.6); cih = math.ceil(esz * 1.2); ap = max(math.ceil(cih / 25), kat)
        kab = math.ceil(kul * 0.15); port = math.ceil((ap + kab) * 1.2); sw = max(kat, math.ceil(port / 48))
        if (int(b["eszamanli"]), int(b["cihaz"]), int(b["ap"]), int(b["kablolu"]), int(b["port"]), int(b["sw"])) != (esz, cih, ap, kab, port, sw):
            calc_err.append(b["kod"])
    add("K1–K5 hesapları her bina için yeniden doğrulandı", not calc_err, f"hatalı satır: {calc_err or 'yok'}")

    nd = [b for b in bld if b["kod"] != "BIDB"]
    S = lambda rs, k: sum(int(r[k]) for r in rs)
    tot = (S(nd, "kullanici"), S(nd, "ap"), S(bld, "kullanici"), S(bld, "ap"))
    add("Toplamlar beklenen değerlerle uyumlu (20.900 / 611 hariç; 21.020 / 617 dahil)",
        tot == (20900, 611, 21020, 617), f"hariç: {tot[0]} kullanıcı, {tot[1]} AP; dahil: {tot[2]} kullanıcı, {tot[3]} AP")

    # Fiber uzunlukları K9 ile yeniden hesaplanır
    from ag_modeli_uret import mesafe
    byc = {b["kod"]: b for b in bld}
    k9 = []
    for l in links:
        if l["fiber_length_m"] and l["source_device"] in ctx.dev and l["target_device"] in ctx.dev:
            a = ctx.dev[l["source_device"]]["building_id"]; c = ctx.dev[l["target_device"]]["building_id"]
            if mesafe(byc[a], byc[c]) != int(l["fiber_length_m"]):
                k9.append(l["link_id"])
    add("Binalar arası fiber uzunlukları K9 ile tutarlı", not k9, f"uyumsuz: {k9 or 'yok'}")

    # Yedek hatlar gerçekten alternatif yol oluşturuyor mu?
    alt_fail = []
    for l in links:
        if l["link_type"] == "BUILDING_UPLINK" and l["primary_or_backup"] == "PRIMARY" and l["source_device"] in ctx.dev:
            b = ctx.dev[l["source_device"]]["building_id"]
            has_backup = any(x["link_type"] == "BUILDING_UPLINK" and x["primary_or_backup"] == "BACKUP"
                             and ctx.dev[x["source_device"]]["building_id"] == b for x in links)
            if has_backup:
                ok, n = ctx.service(drop_links={l["link_id"]})[b]
                if ok != n:
                    alt_fail.append(b)
    add("Tanımlı her yedek hat, birincil hat koptuğunda binayı ayakta tutuyor", not alt_fail, f"başarısız: {alt_fail or 'yok'}")
    return T


# ---------------------------------------------------------------------------
def scenarios(ctx):
    L = ctx.links
    res = {}
    up_primary = {ctx.dev[l["source_device"]]["building_id"]: l["link_id"] for l in L if l["link_type"] == "BUILDING_UPLINK" and l["primary_or_backup"] == "PRIMARY"}
    uplink_sw = {ctx.dev[l["source_device"]]["building_id"]: l["source_device"] for l in L if l["link_type"] == "BUILDING_UPLINK" and l["primary_or_backup"] == "PRIMARY"}

    def run(label, **kw):
        off, part, lost = summarize(ctx.service(**kw))
        return dict(senaryo=label, cevrimdisi_bina=off, kismi_etkilenen=part, kaybedilen_ap=lost)

    res["S1_erisim_switchi"] = [run(f"{b}: birincil yukarı bağlantı switch'i ({s}) arızalı", drop_nodes={s}) for b, s in uplink_sw.items()]
    # Yukarı bağlantısı olmayan sıradan bir erişim switch'i (her binada son switch)
    last_sw = {}
    for d in ctx.devices:
        if d["device_type"] == "ACCESS" and d["role"] == "access":
            last_sw[d["building_id"]] = d["device_id"]
    res["S1b_siradan_erisim_switchi"] = [run(f"{b}: {s} arızalı", drop_nodes={s}) for b, s in last_sw.items()]
    res["S2_birincil_fiber"] = [run(f"{b}: birincil hat ({lid}) koptu", drop_links={lid}) for b, lid in up_primary.items()]
    res["S3_dagitim_switchi"] = [run(f"{d['device_id']} arızalı", drop_nodes={d["device_id"]}) for d in ctx.devices if d["device_type"] == "DISTRIBUTION"]
    res["S4_cekirdek_switchi"] = [run(f"{c} arızalı", drop_nodes={c}) for c in ctx.cores]
    dc_links = [l for l in L if l["link_type"] == "DIST_CORE"]
    res["S5_dagitim_cekirdek_hatti"] = [run(f"{l['source_device']} → {l['target_device']} ({l['primary_or_backup']}) koptu", drop_links={l["link_id"]}) for l in dc_links]
    # Önceki tasarım (D1 öncesi): dağıtım switch'leri yalnızca BIDB-CS01'e bağlı
    old = {l["link_id"] for l in dc_links if l["primary_or_backup"] == "BACKUP"}
    res["S4_onceki_tasarim"] = [run(f"[D1 öncesi tasarım] {c} arızalı", drop_nodes={c}, drop_links=old) for c in ctx.cores]

    # S6: altyapı elemanlarından ikili arızalar
    infra_nodes = ctx.cores + [d["device_id"] for d in ctx.devices if d["device_type"] == "DISTRIBUTION"]
    infra_links = [l["link_id"] for l in L if l["link_type"] in ("BUILDING_UPLINK", "DIST_CORE", "CORE_INTERCONNECT")]
    elems = [("n", x) for x in infra_nodes] + [("l", x) for x in infra_links]
    single_ok = {}  # tek arızada ayakta kalan binalar
    worst, pair_hits = [], Counter()
    base_off = set(summarize(ctx.service())[0])
    robust = set(ctx.aps)  # her tek arızada ayakta kalan binalar
    for e in elems:
        dn = {e[1]} if e[0] == "n" else set(); dl = {e[1]} if e[0] == "l" else set()
        robust -= set(summarize(ctx.service(drop_nodes=dn, drop_links=dl))[0])
    robust_hit = 0
    lid_desc = {l["link_id"]: f"{l['source_device']}–{l['target_device']}" for l in L}
    name = lambda e: e[1] if e[0] == "n" else f"hat {lid_desc[e[1]]}"
    for e1, e2 in itertools.combinations(elems, 2):
        dn = {e[1] for e in (e1, e2) if e[0] == "n"}
        dl = {e[1] for e in (e1, e2) if e[0] == "l"}
        off, part, lost = summarize(ctx.service(drop_nodes=dn, drop_links=dl))
        if off:
            worst.append((len(off), lost, name(e1), name(e2), off))
            if robust & set(off):
                robust_hit += 1
            for b in off:
                pair_hits[b] += 1
    worst.sort(reverse=True)
    res["S6_ikili_ariza"] = dict(
        incelenen_cift=math.comb(len(elems), 2),
        bina_kaybettiren_cift=len(worst),
        tek_arizaya_dayanikli_binalar=sorted(robust),
        dayanikli_bina_kaybettiren_cift=robust_hit,
        en_kotu_10=[dict(ariza=f"{a} + {b}", cevrimdisi_bina=off, kaybedilen_ap=lost) for _, lost, a, b, off in worst[:10]],
    )
    return res


def spof(ctx):
    """Tek başına arızası en az bir binayı tamamen çevrimdışı bırakan elemanlar."""
    out = []
    cand_nodes = [d["device_id"] for d in ctx.devices if d["device_type"] in ("CORE", "DISTRIBUTION", "ACCESS", "SERVER_SWITCH")]
    for n in cand_nodes:
        off, part, lost = summarize(ctx.service(drop_nodes={n}))
        own = ctx.dev[n]["building_id"]
        if off:
            out.append(dict(eleman=n, tur="cihaz", cevrimdisi_bina=off, kaybedilen_ap=lost))
    for l in ctx.links:
        if l["link_type"] == "AP_ACCESS":
            continue
        off, part, lost = summarize(ctx.service(drop_links={l["link_id"]}))
        if off:
            out.append(dict(eleman=f"{l['link_id']} {l['source_device']}–{l['target_device']} ({l['link_type']})", tur="bağlantı", cevrimdisi_bina=off, kaybedilen_ap=lost))
    return out


# ---------------------------------------------------------------------------
# İkinci denetim: yardımcılar
# ---------------------------------------------------------------------------
def uplinks(ctx):
    """Bina -> (birincil hat, yedek hat ya da None)."""
    p, b = {}, {}
    for l in ctx.links:
        if l["link_type"] != "BUILDING_UPLINK" or l["source_device"] not in ctx.dev:
            continue
        k = ctx.dev[l["source_device"]]["building_id"]
        (p if l["primary_or_backup"] == "PRIMARY" else b)[k] = l
    return p, b


def status(imp, b):
    v = imp["bina"].get(b)
    if v is None:
        return "—"
    if v["ap_n"] and v["ap_ok"] == 0:
        return "çevrimdışı"
    if v["ap_ok"] < v["ap_n"] or v["cihaz_kayip"]:
        return "kısmi"
    return "ayakta"


# ---------------------------------------------------------------------------
# 1) Fiber uzunluğu ayrıştırması
# ---------------------------------------------------------------------------
FIBER_CATS = [
    ("bina_birincil", "Bina birincil hattı (bina → dağıtım)", lambda l: l["link_type"] == "BUILDING_UPLINK" and l["primary_or_backup"] == "PRIMARY"),
    ("bina_yedek", "Bina yedek hattı (AS02 → diğer dağıtım)", lambda l: l["link_type"] == "BUILDING_UPLINK" and l["primary_or_backup"] == "BACKUP"),
    ("dagitim_cekirdek_birincil", "Dağıtım → CS01 (birincil)", lambda l: l["link_type"] == "DIST_CORE" and l["primary_or_backup"] == "PRIMARY"),
    ("dagitim_cekirdek_yedek", "Dağıtım → CS02 (yedek)", lambda l: l["link_type"] == "DIST_CORE" and l["primary_or_backup"] == "BACKUP"),
    ("veri_merkezi", "Veri merkezi (çekirdek arası + sunucu switch'i yukarı bağlantıları)", lambda l: l["link_type"] in ("CORE_INTERCONNECT", "SERVER_UPLINK")),
    ("bina_ici", "Bina içi (katlar arası halka + AP bağlantıları)", lambda l: l["link_type"] in ("ACCESS_RING", "AP_ACCESS")),
]


def fiber_breakdown(ctx):
    rows = []
    for key, label, f in FIBER_CATS:
        ls = [l for l in ctx.links if f(l)]
        withlen = [l for l in ls if l["fiber_length_m"]]
        rows.append(dict(kategori=key, ad=label, baglanti=len(ls), uzunlugu_tanimli=len(withlen),
                         uzunlugu_tanimsiz=len(ls) - len(withlen),
                         toplam_m=sum(int(l["fiber_length_m"]) for l in withlen),
                         dayanak=sorted({l["length_basis"].split(" (")[0].split(" –")[0] for l in withlen}) or ["uzunluk tanımlanmadı"]))
    toplam = sum(r["toplam_m"] for r in rows)
    # Ortak güzergâh: aynı SRLG'deki hatlar aynı kanaldan geçer; kazı açısından bir kez sayılır
    by_srlg = defaultdict(int)
    for l in ctx.links:
        if l["fiber_length_m"]:
            by_srlg[l["srlg"]] = max(by_srlg[l["srlg"]], int(l["fiber_length_m"]))
    eski = dict(bina_birincil=sum(int(b["birincil_m"] or 0) for b in ctx.bld),
                bina_yedek=sum(int(b["yedek_m"] or 0) for b in ctx.bld))
    return dict(kategoriler=rows, toplam_m=toplam, guzergah_m=sum(by_srlg.values()), guzergah_sayisi=len(by_srlg),
                eski_toplam_m=OLD_FIBER_M, eski_bilesen=eski)


# ---------------------------------------------------------------------------
# 2) Bina bazında yedeklilik (dört ayrı tek arıza)
# ---------------------------------------------------------------------------
def redundancy_per_building(ctx):
    prim, back = uplinks(ctx)
    srv_primary = {l["source_device"]: l for l in ctx.links if l["link_type"] == "SERVER_UPLINK" and l["primary_or_backup"] == "PRIMARY"}
    out = []
    for r in ctx.bld:
        b = r["kod"]
        if b == "BIDB":
            f1 = ("BIDB-SS01 → CS01 hattı", dict(drop_links={srv_primary["BIDB-SS01"]["link_id"]}))
            f2 = ("BIDB-SS01", dict(drop_nodes={"BIDB-SS01"}))
            f3 = None
        else:
            f1 = (f"{prim[b]['link_id']} ({prim[b]['source_device']} → {prim[b]['target_device']})", dict(drop_links={prim[b]["link_id"]}))
            f2 = (prim[b]["source_device"], dict(drop_nodes={prim[b]["source_device"]}))
            f3 = (prim[b]["target_device"], dict(drop_nodes={prim[b]["target_device"]}))
        tests = dict(birincil_fiber=f1, birincil_erisim_switchi=f2, dagitim_switchi=f3,
                     cekirdek_CS01=("BIDB-CS01", dict(drop_nodes={"BIDB-CS01"})),
                     cekirdek_CS02=("BIDB-CS02", dict(drop_nodes={"BIDB-CS02"})))
        res = {}
        for k, t in tests.items():
            if t is None:
                res[k] = dict(ariza="uygulanamaz (veri merkezi dağıtım katmanına bağlı değil)", durum="—", ap_kayip=0, cihaz_kayip=0, kampus_cevrimdisi=0)
                continue
            imp = ctx.impact(**t[1])
            v = imp["bina"][b]
            res[k] = dict(ariza=t[0], durum=status(imp, b), ap_kayip=v["ap_n"] - v["ap_ok"], cihaz_kayip=v["cihaz_kayip"],
                          kampus_cevrimdisi=len(imp["cevrimdisi"]))
        ok = lambda k: res[k]["durum"] in ("ayakta", "—")
        hat = ok("birincil_fiber"); dag = ok("dagitim_switchi"); cek = ok("cekirdek_CS01") and ok("cekirdek_CS02")
        if b == "BIDB":
            sinif = "Veri merkezi: sunucu switch'leri iki çekirdeğe çift bağlı"
        elif hat and dag and cek:
            sinif = "Hat + dağıtım + çekirdek yedekli"
        elif cek:
            sinif = "Yalnızca çekirdek yedekli (hat ve dağıtım tek nokta)"
        else:
            sinif = "Yedeksiz"
        out.append(dict(bina=b, yedek_hat=b in back, sinif=sinif, testler=res,
                        alternatif_yol=(f"{back[b]['source_device']} → {back[b]['target_device']}" if b in back
                                        else ("SS01/SS02 → CS02" if b == "BIDB" else "yok"))))
    return out


# ---------------------------------------------------------------------------
# 3) Fiziksel ortak arıza: senaryo A (iki çekirdek BIDB'de) ve B (CS02 KUT'ta)
# ---------------------------------------------------------------------------
def physical_events(ctx):
    E = []
    site = lambda s: {d["device_id"] for d in ctx.devices if d["building_id"] == s}
    E.append(("BIDB binası tümüyle devre dışı (enerji, yangın, su baskını)", dict(drop_nodes=site("BIDB"))))
    E.append(("KUT binası tümüyle devre dışı", dict(drop_nodes=site("KUT"))))
    E.append(("CS01 ve CS02 aynı anda arızalı (cihaz arızası)", dict(drop_nodes={"BIDB-CS01", "BIDB-CS02"})))
    for ds in ("MUH", "TEK", "REK"):
        ids = {l["link_id"] for l in ctx.links if l["srlg"] == f"SRLG-{ds}-BIDB"}
        E.append((f"{ds}–BIDB fiber güzergâhı kazıda kesildi (SRLG-{ds}-BIDB, {len(ids)} hat)", dict(drop_links=ids)))
    ids = {l["link_id"] for l in ctx.links if l["srlg"] == "SRLG-BIDB-KUT"}
    E.append((f"BIDB–KUT güzergâhı kesildi (SRLG-BIDB-KUT, {len(ids)} hat)", dict(drop_links=ids)))
    return E


def building_transit(ctx, drop_nodes=(), drop_links=()):
    """Dağıtım switch'i çekirdeğe yalnızca bir binanın erişim switch'leri üzerinden ulaşabiliyor mu?

    Tek OSPF alanında (alan 0) bina yönlendiricileri (AS01/AS02) de transit olabilir: dağıtım–çekirdek
    hatları kesilirse trafik DS → AS01 → (bina içi) → AS02 → diğer DS → çekirdek yolunu izler.
    Bu yol vardır ama 10 Gbps bina hatlarıyla sınırlıdır; burada açıkça raporlanır.
    """
    full = graph(ctx.devices, ctx.links, drop_nodes, drop_links)
    core_layer = [d for d in ctx.devices if d["device_type"] in ("CORE", "DISTRIBUTION")]
    bb = graph(core_layer, [l for l in ctx.links if l["link_type"] in ("DIST_CORE", "CORE_INTERCONNECT")], drop_nodes, drop_links)
    reach_full, reach_bb = set(), set()
    for cr in ctx.cores:
        if cr in full:
            reach_full |= nx.node_connected_component(full, cr)
            reach_bb |= nx.node_connected_component(bb, cr)
    prim, back = uplinks(ctx)
    load = {x["bina"]: x["beklenen_gbps"] for x in capacity_ext(ctx)["binalar"]}
    out = []
    for d in core_layer:
        ds = d["device_id"]
        if d["device_type"] != "DISTRIBUTION" or ds not in full or ds in reach_bb or ds not in reach_full:
            continue
        via = [b for b in back if prim[b]["target_device"] == ds and prim[b]["link_id"] not in drop_links
               and back[b]["target_device"] not in drop_nodes]
        yuk = sum(load[b] for b in prim if prim[b]["target_device"] == ds)
        kap = len(via) * UPLINK_GBPS
        out.append(dict(dagitim=ds, transit_binalar=via, kapasite_gbps=kap, yuk_gbps=round(yuk, 2),
                        kullanim=round(yuk / kap * 100, 1) if kap else None))
    return out


def physical_scenarios(ctxA, ctxB):
    out = []
    for (la, ka), (lb, kb) in zip(physical_events(ctxA), physical_events(ctxB)):
        row = dict(olay=la.split(" (SRLG")[0])
        for tag, c, k, lab in (("A", ctxA, ka, la), ("B", ctxB, kb, lb)):
            if not any(k.values()):
                row[tag] = dict(ayrinti="bu senaryoda böyle bir güzergâh yok", cevrimdisi=[], ap_kayip=0, cihaz_kayip=0, sunucu_switch_kayip=0, transit=[])
                continue
            imp = c.impact(**k)
            row[tag] = dict(ayrinti=lab, cevrimdisi=imp["cevrimdisi"], ap_kayip=imp["ap_kayip"], cihaz_kayip=imp["cihaz_kayip"],
                            sunucu_switch_kayip=imp["bina"]["BIDB"]["cihaz_kayip"] - (imp["bina"]["BIDB"]["ap_n"] - imp["bina"]["BIDB"]["ap_ok"]),
                            transit=building_transit(c, **k))
        out.append(row)
    srlg_groups = {}
    for tag, c in (("A", ctxA), ("B", ctxB)):
        g = defaultdict(list)
        for l in c.links:
            if l["link_type"] in ("DIST_CORE", "CORE_INTERCONNECT", "SERVER_UPLINK", "BUILDING_UPLINK"):
                g[l["srlg"]].append(l["link_id"])
        srlg_groups[tag] = {k: v for k, v in g.items() if len(v) > 1}
    return dict(olaylar=out, paylasilan_srlg=srlg_groups)


# ---------------------------------------------------------------------------
# 4) Kapasite: teorik oran, beklenen kullanım, aktif-pasif / aktif-aktif
# ---------------------------------------------------------------------------
def capacity_ext(ctx):
    prim, back = uplinks(ctx)
    rows = []
    ds_ap, ds_aa = Counter(), Counter()
    for r in ctx.bld:
        b = r["kod"]
        if b == "BIDB":
            continue
        ap, kab, cihaz = int(r["ap"]), int(r["kablolu"]), int(r["cihaz"])
        edge = (ap + kab) * EDGE_PORT_GBPS
        n_up = 2 if b in back else 1
        wl = cihaz * MBPS_PER_WIRELESS_DEVICE / 1000
        wd = kab * MBPS_PER_WIRED_ENDPOINT / 1000
        tot = wl + wd
        s1 = math.ceil(cihaz * STUDENT_SHARE) * MBPS_PER_WIRELESS_DEVICE / 1000      # VLAN 100 -> AS01
        s2 = tot - s1                                                                # VLAN 110 + 200 -> AS02
        row = dict(bina=b, yedek_hat=b in back, uc_port_gbps=edge,
                   oran_aktif_pasif=round(edge / UPLINK_GBPS, 1),
                   oran_aktif_aktif=round(edge / (UPLINK_GBPS * n_up), 1),
                   beklenen_gbps=round(tot, 2), kullanim_aktif_pasif=round(tot / UPLINK_GBPS * 100, 1))
        if b in back:
            row.update(aa_hat1_gbps=round(s1, 2), aa_hat2_gbps=round(s2, 2),
                       aa_hat1_kullanim=round(s1 / UPLINK_GBPS * 100, 1), aa_hat2_kullanim=round(s2 / UPLINK_GBPS * 100, 1),
                       n1_kullanim=round(tot / UPLINK_GBPS * 100, 1))
            ds_aa[prim[b]["target_device"]] += s1
            ds_aa[back[b]["target_device"]] += s2
        else:
            row.update(aa_hat1_gbps=None, aa_hat2_gbps=None, aa_hat1_kullanim=None, aa_hat2_kullanim=None, n1_kullanim=None)
            ds_aa[prim[b]["target_device"]] += tot
        ds_ap[prim[b]["target_device"]] += tot
        rows.append(row)
    dsl = []
    for d in sorted(ds_ap):
        dsl.append(dict(dagitim=d, ap_gbps=round(ds_ap[d], 2), ap_kullanim=round(ds_ap[d] / DIST_CORE_GBPS * 100, 1),
                        aa_gbps=round(ds_aa[d], 2), aa_kullanim=round(ds_aa[d] / (2 * DIST_CORE_GBPS) * 100, 1)))
    # Dağıtım switch'i arızası: yedekli binaların tüm yükü yedek dağıtıma geçer, yedeksiz binalar düşer
    shift = []
    tot_by_b = {x["bina"]: x["beklenen_gbps"] for x in rows}
    for d in sorted(ds_ap):
        load = Counter()
        lost = []
        for b, t in tot_by_b.items():
            pd_ = prim[b]["target_device"]
            bd = back[b]["target_device"] if b in back else None
            if pd_ != d:
                load[pd_] += t       # birincil dağıtım ayakta: bina yükünün tamamı orada
            elif bd:
                load[bd] += t
            else:
                lost.append(b)
        for o in sorted(load):
            shift.append(dict(arizali=d, kalan=o, yuk_gbps=round(load[o], 2),
                              kullanim_tek_hat=round(load[o] / DIST_CORE_GBPS * 100, 1),
                              kullanim_ecmp=round(load[o] / (2 * DIST_CORE_GBPS) * 100, 1),
                              servis_disi_bina=lost))
    toplam = sum(tot_by_b.values())
    return dict(binalar=rows, dagitim=dsl, dagitim_arizasi=shift, kampus_toplam_gbps=round(toplam, 2),
                ihlal_20_1_aktif_pasif=[x["bina"] for x in rows if x["oran_aktif_pasif"] > OVERSUB_TARGET],
                ihlal_20_1_aktif_aktif=[x["bina"] for x in rows if x["oran_aktif_aktif"] > OVERSUB_TARGET])


# ---------------------------------------------------------------------------
# 5) Yeni testler (T16–T23)
# ---------------------------------------------------------------------------
def audit2_tests(ctx, ctxB, FB, RB, PH, CAP, SC):
    T = []
    add = lambda name, ok, detail="": T.append(dict(test=name, sonuc="BAŞARILI" if ok else "BAŞARISIZ", ayrinti=detail))
    devs, links = ctx.devices, ctx.links
    types = Counter(d["device_type"] for d in devs)

    # T16 SERVER_SWITCH / ACCESS ayrımı
    ss = [d for d in devs if d["device_type"] == "SERVER_SWITCH"]
    acc_bidb = [d["device_id"] for d in devs if d["device_type"] == "ACCESS" and d["building_id"] == "BIDB"]
    ss_bad = [d["device_id"] for d in ss if d["building_id"] != "BIDB" or d["role"] != "server"]
    exp = dict(CORE=2, DISTRIBUTION=3, ACCESS=109, SERVER_SWITCH=2, AP=617)
    got = {k: types.get(k, 0) for k in exp}
    srv_up = Counter(l["source_device"] for l in links if l["link_type"] == "SERVER_UPLINK")
    ss_dual = all({l["target_device"] for l in links if l["link_type"] == "SERVER_UPLINK" and l["source_device"] == d["device_id"]} == {"BIDB-CS01", "BIDB-CS02"} for d in ss)
    add("T16 SERVER_SWITCH ve ACCESS ayrımı (2/3/109/2/617 = 733)",
        got == exp and sum(types.values()) == 733 and not acc_bidb and not ss_bad and ss_dual,
        f"bulunan: {got}, toplam {sum(types.values())}; BIDB'de ACCESS: {acc_bidb or 'yok'}; hatalı SS: {ss_bad or 'yok'}; SS iki çekirdeğe bağlı: {ss_dual}")

    # T17 Halka (eski STACK) bağlantı türü tutarlılığı
    stack = [l["link_id"] for l in links if l["link_type"] == "STACK"]
    ring = [l for l in links if l["link_type"] == "ACCESS_RING"]
    bad_end, per = [], defaultdict(list)
    for l in ring:
        a, c = ctx.dev.get(l["source_device"]), ctx.dev.get(l["target_device"])
        if not a or not c or a["device_type"] != "ACCESS" or c["device_type"] != "ACCESS" or a["building_id"] != c["building_id"]:
            bad_end.append(l["link_id"]); continue
        per[a["building_id"]].append(l)
    nsw = Counter(d["building_id"] for d in devs if d["device_type"] == "ACCESS")
    shape_err = []
    for b, n in nsw.items():
        ls = per.get(b, [])
        want = n if n >= 3 else (1 if n == 2 else 0)
        if len(ls) != want:
            shape_err.append(f"{b}: {len(ls)}≠{want}"); continue
        if n >= 3:
            g = nx.Graph(); g.add_edges_from((l["source_device"], l["target_device"]) for l in ls)
            if not (g.number_of_nodes() == n and all(dg == 2 for _, dg in g.degree()) and nx.is_connected(g)):
                shape_err.append(f"{b}: tek halka değil")
    add("T17 Bina içi halka tutarlılığı (STACK yok, aynı bina, n switch'te n bağlantı, tek döngü, toplam 108)",
        not stack and not bad_end and not shape_err and len(ring) == EXPECTED_RING,
        f"STACK: {len(stack)}; ACCESS_RING: {len(ring)} (beklenen {EXPECTED_RING}); uç hatası: {bad_end or 'yok'}; biçim hatası: {shape_err or 'yok'}")

    # T18 Yedeklilik sınıflandırması
    yedek_rule = {r["kod"] for r in ctx.bld if r["yedek"] not in ("Yok", "—")}
    _, back = uplinks(ctx)
    hatdag = {x["bina"] for x in RB if x["sinif"] == "Hat + dağıtım + çekirdek yedekli"}
    robust = set(SC["S6_ikili_ariza"]["tek_arizaya_dayanikli_binalar"])
    add("T18 Yedeklilik sınıflandırması (8 yedek hatlı bina = hat+dağıtım yedekli; 9 dayanıklı = 8 + BIDB)",
        yedek_rule == set(back) == hatdag and len(hatdag) == 8 and robust == hatdag | {"BIDB"},
        f"kural (K7): {sorted(yedek_rule)}; YEDEK hattı olan: {sorted(back)}; testle yedekli: {sorted(hatdag)}; tek arızaya dayanıklı: {sorted(robust)}")

    # T19 Fiziksel ortak arıza senaryosu
    inter = [l["link_id"] for l in links if l["fiber_length_m"] and not l["srlg"]]
    no_srlg = [l["link_id"] for l in links + ctxB.links if not l["srlg"]]
    a_bidb = next(r for r in PH["olaylar"] if r["olay"].startswith("BIDB binası"))["A"]["cevrimdisi"]
    def allowed(olay):
        if olay.startswith("BIDB binası"):
            return {"BIDB"}
        if olay.startswith("KUT binası"):
            return {"KUT"}
        return set()
    b_ok = all(set(r["B"]["cevrimdisi"]) <= allowed(r["olay"]) for r in PH["olaylar"] if "aynı anda" not in r["olay"])
    a_ds = {r["olay"]: r["A"] for r in PH["olaylar"] if "güzergâhı kazıda" in r["olay"]}
    b_ds = {r["olay"]: r["B"] for r in PH["olaylar"] if "güzergâhı kazıda" in r["olay"]}
    a_transit = all(len(v["transit"]) == 1 for v in a_ds.values())
    b_transit = not any(v["transit"] for v in b_ds.values())
    add("T19 Fiziksel ortak arıza (SRLG tanımlı; A'da BIDB kaybı 20 binanın tamamını düşürür; A'da DS–BIDB güzergâh kesintisi "
        "dağıtımı çekirdekten koparır ve yalnız bina transiti kalır; B'de tek bina/güzergâh kaybı başka binayı düşürmez ve transite gerek kalmaz)",
        not no_srlg and len(a_bidb) == len(ctx.bld) and a_transit and b_ok and b_transit,
        f"SRLG'siz bağlantı: {len(no_srlg)}; A/BIDB kaybı: {len(a_bidb)} bina çevrimdışı; A/DS–BIDB kesintisinde bina transiti: "
        + "; ".join(f"{t['dagitim']} → {', '.join(t['transit_binalar']) or 'yok'} (%{t['kullanim']})" for v in a_ds.values() for t in v["transit"])
        + f"; B'de başka bina düşmüyor: {b_ok}; B'de transit gerekmiyor: {b_transit}")

    # T20 Fiber bileşenlerinin toplamı
    cat = {r["kategori"]: r["toplam_m"] for r in FB["kategoriler"]}
    k9_missing = [l["link_id"] for l in links if l["length_basis"].startswith("K9") and not l["fiber_length_m"]]
    len_wo_k9 = [l["link_id"] for l in links if l["fiber_length_m"] and not l["length_basis"].startswith("K9")]
    ok20 = (cat["bina_birincil"] == FB["eski_bilesen"]["bina_birincil"] and cat["bina_yedek"] == FB["eski_bilesen"]["bina_yedek"]
            and cat["bina_birincil"] + cat["bina_yedek"] == OLD_FIBER_M
            and sum(cat.values()) == FB["toplam_m"] == OLD_FIBER_M + cat["dagitim_cekirdek_birincil"] + cat["dagitim_cekirdek_yedek"] + cat["veri_merkezi"]
            and not k9_missing and not len_wo_k9)
    add("T20 Fiber uzunluğu bileşenleri toplamla tutarlı (13.517 + dağıtım–çekirdek = toplam; uzunluk yalnız K9 hatlarında)",
        ok20, f"birincil {cat['bina_birincil']} + yedek {cat['bina_yedek']} = {cat['bina_birincil'] + cat['bina_yedek']}; "
              f"+ dağıtım–çekirdek {cat['dagitim_cekirdek_birincil'] + cat['dagitim_cekirdek_yedek']} + veri merkezi {cat['veri_merkezi']} = {FB['toplam_m']} m; "
              f"K9 olup uzunluğu boş: {k9_missing or 'yok'}; K9 dışı uzunluk: {len_wo_k9 or 'yok'}")

    # T21 Aktif-pasif / aktif-aktif kapasite hesapları
    err = []
    for x in CAP["binalar"]:
        if abs(x["oran_aktif_pasif"] - x["uc_port_gbps"] / UPLINK_GBPS) > 0.051:
            err.append(f"{x['bina']} AP oranı")
        if x["yedek_hat"]:
            if abs(x["oran_aktif_aktif"] * 2 - x["oran_aktif_pasif"]) > 0.11:
                err.append(f"{x['bina']} AA oranı")
            if abs(x["aa_hat1_gbps"] + x["aa_hat2_gbps"] - x["beklenen_gbps"]) > 0.011:
                err.append(f"{x['bina']} AA yük toplamı")
            if max(x["aa_hat1_kullanim"], x["aa_hat2_kullanim"], x["n1_kullanim"]) > 100:
                err.append(f"{x['bina']} AA/N-1 > %100")
        elif x["oran_aktif_aktif"] != x["oran_aktif_pasif"]:
            err.append(f"{x['bina']}: yedeksiz binada AA oranı farklı")
        if x["kullanim_aktif_pasif"] > 100:
            err.append(f"{x['bina']} AP > %100")
    # Aktif-aktif bölüşüm, adresleme modelindeki VLAN ihtiyaçlarından bağımsız olarak yeniden hesaplanır:
    # hat 1 = VLAN 100 (öğrenci kablosuz), hat 2 = VLAN 110 (personel kablosuz) + VLAN 200 (kablolu)
    need = defaultdict(dict)
    for v in csv.DictReader(open(ROOT / "data" / "vlans.csv", encoding="utf-8")):
        need[v["building_id"]][int(v["vlan_id"])] = int(v["need_hosts"])
    for x in CAP["binalar"]:
        if not x["yedek_hat"]:
            continue
        n = need.get(x["bina"], {})
        h1 = n.get(100, 0) * MBPS_PER_WIRELESS_DEVICE / 1000
        h2 = (n.get(110, 0) * MBPS_PER_WIRELESS_DEVICE + n.get(200, 0) * MBPS_PER_WIRED_ENDPOINT) / 1000
        if abs(h1 - x["aa_hat1_gbps"]) > 0.011 or abs(h2 - x["aa_hat2_gbps"]) > 0.011:
            err.append(f"{x['bina']} AA bölüşümü VLAN modeliyle uyuşmuyor")
    tot_ap = round(sum(d["ap_gbps"] for d in CAP["dagitim"]), 1)
    tot_aa = round(sum(d["aa_gbps"] for d in CAP["dagitim"]), 1)
    if tot_ap != tot_aa or abs(tot_ap - CAP["kampus_toplam_gbps"]) > 0.1:
        err.append("dağıtım yük toplamı tutarsız")
    over = [f"{s['arizali']}→{s['kalan']}" for s in CAP["dagitim_arizasi"] if s["kullanim_tek_hat"] > 100]
    add("T21 Aktif-pasif ve aktif-aktif kapasite hesapları tutarlı (AA bölüşümü VLAN modeliyle eşleşiyor); N-1 durumunda hiçbir hat %100'ü aşmıyor",
        not err and not over, f"hata: {err or 'yok'}; dağıtım arızasında aşım: {over or 'yok'}; kampüs beklenen yükü {CAP['kampus_toplam_gbps']} Gbps")

    # T22 Adresleme (Batfish–FRR hazırlığı)
    vl = list(csv.DictReader(open(ROOT / "data" / "vlans.csv", encoding="utf-8")))
    p2p = list(csv.DictReader(open(ROOT / "data" / "p2p_links.csv", encoding="utf-8")))
    rt = list(csv.DictReader(open(ROOT / "data" / "routers.csv", encoding="utf-8")))
    e = []
    backbone = {l["link_id"] for l in links if l["link_type"] in ("BUILDING_UPLINK", "DIST_CORE", "CORE_INTERCONNECT")}
    if {p["link_id"] for p in p2p} != backbone:
        e.append("p2p ≠ omurga bağlantıları")
    rids = {r["device_id"] for r in rt}
    for p in p2p:
        if not p["subnet"].endswith("/31") or p["a_device"] not in rids or p["b_device"] not in rids:
            e.append(f"{p['link_id']} /31 ya da uç hatası")
    nets = [ipaddress.ip_network(v["subnet"]) for v in vl] + [ipaddress.ip_network(p["subnet"]) for p in p2p] \
         + [ipaddress.ip_network(r["loopback_ip"]) for r in rt]
    ov = [(str(a), str(b)) for a, b in itertools.combinations(nets, 2) if a.overlaps(b)]
    if ov:
        e.append(f"çakışan alt ağ: {ov[:3]}")
    if len({r["loopback_ip"] for r in rt}) != len(rt):
        e.append("loopback tekrarı")
    small = [f"{v['building_id']}/{v['vlan_id']}" for v in vl if int(v["need_hosts"]) > int(v["capacity_hosts"])]
    if small:
        e.append(f"yetersiz VLAN: {small}")
    mgmt = {d["management_ip"] for d in devs}
    clash = [f"{v['building_id']}/{v['vlan_id']}" for v in vl if v["gateway_vip"] and v["gateway_vip"] in mgmt]
    if clash:
        e.append(f"VIP bir cihazın yönetim adresiyle çakışıyor: {clash}")
    vset = defaultdict(set)
    for v in vl:
        vset[v["building_id"]].add(int(v["vlan_id"]))
    miss = [b for b in vset if not {10, 11, 100, 110, 200} <= vset[b] or ((900 in vset[b]) != (b in back))]
    if miss:
        e.append(f"VLAN kümesi eksik/fazla: {miss}")
    exp_r = 2 + 3 + len([r for r in ctx.bld if r["kod"] != "BIDB"]) + len(back)
    if len(rt) != exp_r:
        e.append(f"yönlendirici sayısı {len(rt)} ≠ {exp_r}")
    add("T22 Adresleme modeli tutarlı (34 /31 omurga hattı, çakışma yok, VIP çakışması yok, VLAN boyutları yeterli)",
        not e, f"{len(vl)} VLAN, {len(p2p)} /31, {len(rt)} OSPF yönlendiricisi; hata: {e or 'yok'}")

    # T23 Senaryo B yalnızca CS02 konumu ve uzunluklarda farklı
    ida = {d["device_id"]: d["device_type"] for d in devs}
    idb = {d["device_id"]: d["device_type"] for d in ctxB.devices}
    la = {l["link_id"]: (l["source_device"], l["target_device"], l["link_type"]) for l in links}
    lb = {l["link_id"]: (l["source_device"], l["target_device"], l["link_type"]) for l in ctxB.links}
    moved = [d["device_id"] for d in ctxB.devices if d["building_id"] != ctx.dev[d["device_id"]]["building_id"]] if ida == idb else ["?"]
    add("T23 Senaryo B envanteri A ile aynı (yalnızca CS02'nin binası ve ilgili uzunluklar değişir)",
        ida == idb and la == lb and moved == ["BIDB-CS02"], f"cihaz: {len(idb)}, bağlantı: {len(lb)}; binası değişen: {moved}")
    return T


# ---------------------------------------------------------------------------
# Rapor
# ---------------------------------------------------------------------------
def fmt(n):
    return f"{n:,}".replace(",", ".")


def report(T, S, SP, ctx, FB, RB, PH, CAP, FBb):
    fails = sum(1 for t in T if t["sonuc"] != "BAŞARILI")
    types = Counter(d["device_type"] for d in ctx.devices)
    ltypes = Counter(l["link_type"] for l in ctx.links)
    o = []
    w = o.append
    w("# Topoloji doğrulama raporu\n")
    w("> Bu rapor `scripts/topoloji_dogrula.py` tarafından otomatik üretilir; elle düzenlenmez.")
    w("> Bütün veriler **sentetiktir**. Fırat Üniversitesi'nin gerçek ağ altyapısına ait hiçbir veri kullanılmamıştır;")
    w("> bina konumları dışında kalan her değer `docs/topoloji.md` ve `docs/ag_modeli.md` içindeki kurallardan üretilmiştir.\n")
    w(f"**Sonuç:** {len(T) - fails}/{len(T)} yapısal test başarılı. Tek hata noktası: {len(SP)}. "
      f"Başarısız test {'yok' if not fails else 'VAR – aşağıdaki tabloya bakınız'}.\n")
    w("Yeniden üretmek için: `python3 scripts/topoloji_uret.py && python3 scripts/ag_modeli_uret.py && "
      "python3 scripts/adresleme_uret.py && python3 scripts/topoloji_dogrula.py`\n")

    w("## 1. Envanter\n")
    w("| Cihaz türü | Adet |\n|---|---:|")
    for k in ("CORE", "DISTRIBUTION", "ACCESS", "SERVER_SWITCH", "AP"):
        w(f"| {k} | {types.get(k, 0)} |")
    w(f"| **Toplam** | **{sum(types.values())}** |\n")
    w("| Bağlantı türü | Adet |\n|---|---:|")
    for k, v in sorted(ltypes.items(), key=lambda x: -x[1]):
        w(f"| {k} | {v} |")
    w(f"| **Toplam** | **{sum(ltypes.values())}** |\n")

    w("## 2. Yapısal testler\n")
    w("T1–T15 birinci denetimden korunmuştur; T16–T23 ikinci denetimde eklenmiştir.\n")
    w("| # | Test | Sonuç | Ayrıntı |\n|---|---|---|---|")
    for i, t in enumerate(T, 1):
        name = t["test"] if t["test"].startswith("T") and t["test"][1].isdigit() else f"T{i} {t['test']}"
        num, _, rest = name.partition(" ")
        w(f"| {num} | {rest} | {'✅' if t['sonuc'] == 'BAŞARILI' else '❌'} {t['sonuc']} | {t['ayrinti']} |")
    w("")

    w("## 3. Tek arıza senaryoları (bilgi amaçlı)\n")
    labels = dict(S1_erisim_switchi="S1 – Birincil yukarı bağlantı switch'i (AS01) arızası",
                  S1b_siradan_erisim_switchi="S1b – Sıradan bir erişim switch'i arızası",
                  S2_birincil_fiber="S2 – Birincil fiber kopması", S3_dagitim_switchi="S3 – Dağıtım switch'i arızası",
                  S4_cekirdek_switchi="S4 – Çekirdek switch'i arızası", S5_dagitim_cekirdek_hatti="S5 – Dağıtım–çekirdek hattı kopması",
                  S4_onceki_tasarim="S4' – Karşılaştırma: D1 öncesi tasarımda çekirdek arızası")
    for k, lab in labels.items():
        w(f"### {lab}\n")
        w("| Senaryo | Çevrimdışı bina | Kısmi etkilenen | Kaybedilen AP |\n|---|---|---|---:|")
        for r in S[k]:
            w(f"| {r['senaryo']} | {', '.join(r['cevrimdisi_bina']) or '—'} | {', '.join(r['kismi_etkilenen']) or '—'} | {r['kaybedilen_ap']} |")
        w("")
    s6 = S["S6_ikili_ariza"]
    w("### S6 – İkili altyapı arızaları\n")
    w(f"Çekirdek, dağıtım switch'leri ve bütün omurga hatlarından oluşan elemanlardan {fmt(s6['incelenen_cift'])} çift denendi. "
      f"{fmt(s6['bina_kaybettiren_cift'])} çift en az bir binayı çevrimdışı bırakıyor. "
      f"Herhangi bir tek altyapı arızasına dayanıklı binalar: {', '.join(s6['tek_arizaya_dayanikli_binalar'])}. "
      f"Bu binaların en az birini düşüren çift sayısı: {s6['dayanikli_bina_kaybettiren_cift']}.\n")
    w("| Arıza çifti | Çevrimdışı bina | Kaybedilen AP |\n|---|---|---:|")
    for r in s6["en_kotu_10"]:
        w(f"| {r['ariza']} | {', '.join(r['cevrimdisi_bina'])} | {r['kaybedilen_ap']} |")
    w("")

    w("## 4. Tek hata noktaları (SPOF)\n")
    w("Tek başına arızası en az bir binayı **tamamen** çevrimdışı bırakan cihaz ya da bağlantı. "
      "AP–erişim switch'i bağlantıları (her AP tek kabloyla bağlıdır) listeye alınmamıştır.\n")
    w("| Eleman | Tür | Çevrimdışı bina | Kaybedilen AP |\n|---|---|---|---:|")
    for r in SP:
        w(f"| {r['eleman']} | {r['tur']} | {', '.join(r['cevrimdisi_bina'])} | {r['kaybedilen_ap']} |")
    w("")

    w("## 5. Bina bazında yedeklilik\n")
    w("Her bina için dört arıza **ayrı ayrı** uygulanmıştır. Durum: *ayakta* (bütün AP ve uç cihazlar çekirdeğe ulaşıyor), "
      "*kısmi* (binada bir kısım AP/cihaz kayıp), *çevrimdışı* (binanın hiçbir AP'si çekirdeğe ulaşamıyor). "
      "Kayıp sayılarına arızalı cihazın kendisi de dahildir. Çekirdek sütunu iki çekirdekten kötü olanını gösterir.\n")
    w("| Bina | Alternatif yol | Birincil fiber | Birincil erişim switch'i | Dağıtım switch'i | Çekirdek (en kötü) | Sınıf |\n|---|---|---|---|---|---|---|")
    cell = lambda r: r["durum"] if r["durum"] in ("—",) else f"{r['durum']} ({r['ap_kayip']} AP, {r['cihaz_kayip']} cihaz)"
    for x in RB:
        t = x["testler"]
        worst = max((t["cekirdek_CS01"], t["cekirdek_CS02"]), key=lambda r: (r["ap_kayip"], r["cihaz_kayip"]))
        w(f"| {x['bina']} | {x['alternatif_yol']} | {cell(t['birincil_fiber'])} | {cell(t['birincil_erisim_switchi'])} | "
          f"{cell(t['dagitim_switchi'])} | {cell(worst)} | {x['sinif']} |")
    w("")
    cls = Counter(x["sinif"] for x in RB)
    w("**Sınıf dağılımı:** " + "; ".join(f"{k}: {v}" for k, v in cls.items()) + "\n")
    w("**8 ve 9 farkı.** K7 kuralıyla yedek hattı olan bina sayısı 8'dir (REK, MUH, EGT, IIBF, TEK, KUT, YEM, TIP). "
      "S6'daki \"tek altyapı arızasına dayanıklı\" küme 9 binadır, çünkü dokuzuncu eleman BIDB'dir. "
      "BIDB bir yedek hat almaz; veri merkezi sunucu switch'leri (SS01, SS02) iki çekirdeğe ayrı ayrı bağlıdır, "
      "bu nedenle tek bir çekirdek ya da hat arızası BIDB'yi düşürmez. Yani 8 = *yedek hatlı bina*, 9 = *8 + çift bağlı veri merkezi*.\n")
    w("**Dürüst not.** Yedek hatlı binalarda birincil erişim switch'i (AS01) arızası binayı düşürmez ama **kısmi** kayba yol açar: "
      "AS01'e doğrudan bağlı AP'ler kaybolur, çünkü her AP tek kabloyla tek switch'e bağlıdır. Bu modelde AP düzeyinde yedeklilik yoktur.\n")

    w("## 6. Fiziksel ortak arıza: Senaryo A ve Senaryo B\n")
    w("- **Senaryo A (mevcut topoloji):** CS01 ve CS02 aynı binada (BIDB). Her dağıtım switch'inin iki çekirdek hattı aynı güzergâhtan geçer (aynı SRLG).")
    w("- **Senaryo B (karşılaştırma, uygulanmadı):** CS02 Kütüphane binasında (KUT). Konum ve uzunluklar **sentetik varsayımdır**; "
      "KUT yalnızca kampüsün orta bölgesinde olduğu ve kritik bina sayıldığı için seçilmiştir. Cihaz kimliği karşılaştırma kolaylığı için `BIDB-CS02` olarak bırakılmıştır.\n")
    w("| Olay | A: çevrimdışı bina | A: kayıp AP / uç cihaz | B: çevrimdışı bina | B: kayıp AP / uç cihaz |\n|---|---|---|---|---|")
    for r in PH["olaylar"]:
        a, b = r["A"], r["B"]
        ca = f"{len(a['cevrimdisi'])} ({', '.join(a['cevrimdisi'])})" if a["cevrimdisi"] else "0"
        cb = f"{len(b['cevrimdisi'])} ({', '.join(b['cevrimdisi'])})" if b["cevrimdisi"] else "0"
        if len(a["cevrimdisi"]) > 6:
            ca = f"{len(a['cevrimdisi'])} (tüm kampüs)" if len(a["cevrimdisi"]) >= 19 else f"{len(a['cevrimdisi'])}"
        if len(b["cevrimdisi"]) > 6:
            cb = f"{len(b['cevrimdisi'])} (tüm kampüs)" if len(b["cevrimdisi"]) >= 19 else f"{len(b['cevrimdisi'])}"
        na = " *(bu senaryoda yok)*" if a["ayrinti"].startswith("bu senaryoda") else ""
        nb = " *(bu senaryoda yok)*" if b["ayrinti"].startswith("bu senaryoda") else ""
        w(f"| {r['olay']} | {ca}{na} | {a['ap_kayip']} / {a['cihaz_kayip']} | {cb}{nb} | {b['ap_kayip']} / {b['cihaz_kayip']} |")
    w("")
    tr = [(r["olay"], t) for r in PH["olaylar"] for t in r["A"]["transit"]]
    if tr:
        w("**Bina üzerinden transit (Senaryo A).** Bir dağıtım switch'inin iki çekirdek hattı aynı güzergâhta olduğu için kazı ikisini birlikte keser. "
          "Bağlılık testi binaları \"ayakta\" gösterir, çünkü tek OSPF alanında trafik DS → yedek hatlı bir binanın AS01'i → bina içi → AS02 → diğer DS → çekirdek "
          "yolunu izleyebilir. Bu yol gerçektir ama 10 Gbps bina hatlarıyla sınırlıdır ve erişim katmanını transit yapar:\n")
        w("| Olay | Kopan dağıtım | Transit binalar | Transit kapasitesi | Taşınması gereken yük | Kullanım |\n|---|---|---|---:|---:|---:|")
        for olay, t in tr:
            k = f"%{t['kullanim']}" if t["kullanim"] is not None else "transit yok"
            if t["kullanim"] and t["kullanim"] > 100:
                k = f"**{k} (aşırı yük)**"
            w(f"| {olay} | {t['dagitim']} | {', '.join(t['transit_binalar']) or '—'} | {t['kapasite_gbps']} Gbps | {t['yuk_gbps']} Gbps | {k} |")
        w("\nSenaryo B'de aynı kazı yalnızca bir hattı keser; dağıtım switch'i diğer çekirdeğe doğrudan bağlı kalır, transite gerek olmaz. "
          "Erişim katmanının transit olup olmayacağı Batfish–FRR aşamasında açıkça seçilecektir (bkz. `docs/batfish_frr_hazirlik.md`).\n")
    w("Birden fazla omurga hattının paylaştığı fiziksel risk grupları (SRLG):\n")
    for tag in ("A", "B"):
        g = PH["paylasilan_srlg"][tag]
        w(f"- {tag}: " + ("; ".join(f"`{k}` ({len(v)} hat)" for k, v in sorted(g.items())) or "yok"))
    w("")
    w("**Yorum.** Senaryo B, BIDB binasının kaybında kampüs ağının bağlantısını korur. Ancak sunucu switch'leri BIDB'de kaldığı için "
      "veri merkezindeki servisler yine kaybolur; gerçek bir felaket kurtarma için ikinci bir veri merkezi gerekir ve bu proje kapsamı dışındadır. "
      "B'nin maliyeti, yeni güzergâhlar ve ek fiberdir (bkz. bölüm 7).\n")

    w("## 7. Fiber uzunluğu ayrıştırması\n")
    w("Uzunluklar **ölçüm değildir**. Yalnızca binalar arası hatlara K9 (iki bina koordinatı arasındaki düz çizgi mesafesi × 1,3 güzergâh katsayısı) "
      "uygulanmıştır. Bina içi bağlantıların uzunluğu tanımlanmamıştır, çünkü kat planı verisi yoktur.\n")
    w("| Bileşen | Bağlantı | Uzunluğu tanımlı | Toplam (A) | Toplam (B) | Dayanak |\n|---|---:|---:|---:|---:|---|")
    fbb = {r["kategori"]: r for r in FBb["kategoriler"]}
    for r in FB["kategoriler"]:
        w(f"| {r['ad']} | {r['baglanti']} | {r['uzunlugu_tanimli']} | {fmt(r['toplam_m'])} m | {fmt(fbb[r['kategori']]['toplam_m'])} m | {', '.join(r['dayanak'])} |")
    w(f"| **Toplam fiber** | | | **{fmt(FB['toplam_m'])} m** | **{fmt(FBb['toplam_m'])} m** | |")
    w(f"| Farklı güzergâh (aynı SRLG bir kez) | | | {fmt(FB['guzergah_m'])} m ({FB['guzergah_sayisi']} güzergâh) | {fmt(FBb['guzergah_m'])} m ({FBb['guzergah_sayisi']} güzergâh) | kazı/kanal açısından |\n")
    eb = FB["eski_bilesen"]
    cat = {r["kategori"]: r["toplam_m"] for r in FB["kategoriler"]}
    dc = cat["dagitim_cekirdek_birincil"] + cat["dagitim_cekirdek_yedek"]
    w("**Eski (13.517 m) ve yeni (18.887 m) değerin karşılaştırması:**\n")
    w("| Bileşen | Eski rapor | Yeni rapor | Fark | Açıklama |\n|---|---:|---:|---:|---|")
    w(f"| Bina birincil hattı | {fmt(eb['bina_birincil'])} | {fmt(cat['bina_birincil'])} | {cat['bina_birincil'] - eb['bina_birincil']} | değişmedi |")
    w(f"| Bina yedek hattı | {fmt(eb['bina_yedek'])} | {fmt(cat['bina_yedek'])} | {cat['bina_yedek'] - eb['bina_yedek']} | değişmedi |")
    w(f"| Dağıtım–çekirdek | 0 | {fmt(dc)} | +{fmt(dc)} | eski toplamda sayılmamıştı; D1 ile her dağıtım için ikinci hat eklendi (2 × {fmt(cat['dagitim_cekirdek_birincil'])}) |")
    w(f"| Veri merkezi | 0 | {fmt(cat['veri_merkezi'])} | 0 | A'da bina içi, uzunluk tanımsız |")
    w(f"| **Toplam** | **{fmt(FB['eski_toplam_m'])}** | **{fmt(FB['toplam_m'])}** | **+{fmt(FB['toplam_m'] - FB['eski_toplam_m'])}** | Fark yalnızca kapsamdan gelir; hiçbir hattın uzunluğu değişmemiştir |\n")

    w("## 8. Kapasite\n")
    w("Bütün trafik değerleri **sentetik tasarım parametreleridir** (eşzamanlı kablosuz cihaz başına "
      f"{MBPS_PER_WIRELESS_DEVICE} Mbps, kablolu uç başına {MBPS_PER_WIRED_ENDPOINT} Mbps, uç port {EDGE_PORT_GBPS} Gbps, öğrenci payı %{int(STUDENT_SHARE * 100)}). Ölçüm değildir.\n")
    w("- **Teorik oran** = kullanılan uç portların toplam hızı / etkin yukarı bağlantı kapasitesi. Bu bir *port oranı göstergesidir*; trafik değildir. "
      f"Cisco (2013) erişim katmanı için {OVERSUB_TARGET}:1'i bir başparmak kuralı olarak verir.")
    w("- **Beklenen kullanım** = beklenen trafik / hat kapasitesi.")
    w("- **Aktif-pasif:** yedek hat yalnız birincil koparsa taşır (OSPF maliyeti yedekte 100).")
    w("- **Aktif-aktif:** iki hat da taşır. Bunun için yapılandırma gerekir: binada VRRP ana yönlendiricisi VLAN bazında paylaştırılır "
      "(VLAN 100 → AS01, VLAN 110/200 → AS02), bina–dağıtım ve dağıtım–çekirdek OSPF maliyetleri eşitlenir (ECMP). "
      "Yapılandırılmadıkça aktif-aktif kapasite **yoktur**.\n")
    w("| Bina | Yedek hat | Uç port (Gbps) | Teorik oran AP | Teorik oran AA | Beklenen (Gbps) | Kullanım AP | AA hat 1 | AA hat 2 | N-1 |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    pc = lambda v: "—" if v is None else f"%{v}"
    for x in CAP["binalar"]:
        f20 = lambda v: f"**{v}:1**" if v > OVERSUB_TARGET else f"{v}:1"
        w(f"| {x['bina']} | {'var' if x['yedek_hat'] else 'yok'} | {x['uc_port_gbps']} | {f20(x['oran_aktif_pasif'])} | {f20(x['oran_aktif_aktif'])} | "
          f"{x['beklenen_gbps']} | %{x['kullanim_aktif_pasif']} | {pc(x['aa_hat1_kullanim'])} | {pc(x['aa_hat2_kullanim'])} | {pc(x['n1_kullanim'])} |")
    w("")
    w(f"20:1'i aşan bina — aktif-pasif: {len(CAP['ihlal_20_1_aktif_pasif'])} ({', '.join(CAP['ihlal_20_1_aktif_pasif']) or 'yok'}); "
      f"aktif-aktif: {len(CAP['ihlal_20_1_aktif_aktif'])} ({', '.join(CAP['ihlal_20_1_aktif_aktif']) or 'yok'}). "
      "Aktif-aktif yalnız yedek hatlı binalarda oranı yarıya indirir; yedeksiz binalar için tek çözüm yukarı bağlantı hızını artırmaktır.\n")
    w("**Dağıtım → çekirdek** (aktif-pasif: yalnız CS01 hattı, 40 Gbps; aktif-aktif: iki hat ECMP, 80 Gbps):\n")
    w("| Dağıtım | Yük AP (Gbps) | Kullanım AP | Yük AA (Gbps) | Kullanım AA |\n|---|---:|---:|---:|---:|")
    for d in CAP["dagitim"]:
        w(f"| {d['dagitim']} | {d['ap_gbps']} | %{d['ap_kullanim']} | {d['aa_gbps']} | %{d['aa_kullanim']} |")
    w(f"\nKampüs toplam beklenen yükü: {CAP['kampus_toplam_gbps']} Gbps.\n")
    w("**Dağıtım switch'i arızası (N-1):** yedek hatlı binaların bütün yükü yedek dağıtıma geçer; yedeksiz binalar servis dışı kalır.\n")
    w("| Arızalı | Kalan dağıtım | Yük (Gbps) | Kullanım (tek 40G) | Kullanım (ECMP 80G) | Servis dışı bina |\n|---|---|---:|---:|---:|---|")
    for s_ in CAP["dagitim_arizasi"]:
        w(f"| {s_['arizali']} | {s_['kalan']} | {s_['yuk_gbps']} | %{s_['kullanim_tek_hat']} | %{s_['kullanim_ecmp']} | {', '.join(s_['servis_disi_bina']) or '—'} |")
    w("")

    w("## 9. Sınırlılıklar\n")
    w("- Erişilebilirlik, grafik bağlılığıyla ölçülür (AP → herhangi bir çekirdek). Yönlendirme protokolünün yakınsama süresi, VRRP geçişi ve RSTP davranışı bu testte modellenmez; Batfish/FRR aşamasında ele alınacaktır.")
    w("- Bina içi halka (ACCESS_RING) bir Katman 2 döngüsüdür; döngü RSTP (IEEE 802.1w) ile engellenir. Grafik testi döngüyü bir yedek yol olarak görür; bu, RSTP'nin bir portu blokladığı ve arızada açtığı varsayımına dayanır.")
    w("- Kapasite hesapları ortalama yük üzerindendir; ani tepe (burst) ve uygulama karışımı modellenmez.")
    w("- Senaryo B yalnızca karşılaştırma içindir; mevcut topoloji (A) değiştirilmemiştir.")
    (ROOT / "docs" / "dogrulama_raporu.md").write_text("\n".join(o) + "\n", encoding="utf-8")
    return fails


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    bld, devices, links = load()
    ctx = Ctx(bld, devices, links)
    _, devB, linkB = load("data/senaryo_b")
    ctxB = Ctx(bld, devB, linkB)
    T = structural_tests(ctx)
    T = [dict(t, test=f"T{i} {t['test']}") for i, t in enumerate(T, 1)]
    S = scenarios(ctx)
    SP = spof(ctx)
    FB, FBb = fiber_breakdown(ctx), fiber_breakdown(ctxB)
    RB = redundancy_per_building(ctx)
    PH = physical_scenarios(ctx, ctxB)
    CAP = capacity_ext(ctx)
    T += audit2_tests(ctx, ctxB, FB, RB, PH, CAP, S)
    fails = report(T, S, SP, ctx, FB, RB, PH, CAP, FBb)
    json.dump(dict(testler=T, senaryolar=S, tek_hata_noktalari=SP, fiber=dict(A=FB, B=FBb), bina_yedeklilik=RB,
                   fiziksel=PH, kapasite=CAP), open(ROOT / "data" / "dogrulama_sonuclari.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"Yapısal test: {len(T) - fails}/{len(T)} başarılı; tek hata noktası: {len(SP)}; rapor: docs/dogrulama_raporu.md")
    for t in T:
        if t["sonuc"] != "BAŞARILI":
            print("  BAŞARISIZ:", t["test"], "|", t["ayrinti"])
    sys.exit(1 if fails else 0)
