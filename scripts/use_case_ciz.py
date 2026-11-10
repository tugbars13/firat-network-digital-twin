"""Kampüs Ağı Dijital İkizi — UML 2.x Use Case diyagramını çizer.
Çıktı: use-case.png ve use-case.svg (docs/diagrams/ altına kopyalanır)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, Circle

plt.rcParams["font.family"] = "Liberation Sans"
INK, GRAY, LIGHT = "#111111", "#555555", "#F2F2F2"
W, H = 1100, 1420
fig = plt.figure(figsize=(W / 100, H / 100), dpi=150)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")

UCX, UCW, UCH = 550, 290, 64
GROUPS = [
    ("Görüntüleme", [("UC-01", "Kampüs ağını 3D görüntüle"), ("UC-02", "Kampüs ağını filtrele"),
                     ("UC-03", "Bina detayını incele"), ("UC-04", "Cihaz detayını incele"),
                     ("UC-05", "Hat detayını incele")]),
    ("İzleme ve uyarı", [("UC-06", "Canlı telemetriyi izle"), ("UC-07", "Uyarıları görüntüle"),
                         ("UC-08", "Uyarıyı onayla")]),
    ("Analiz ve senaryo", [("UC-09", "Geçmiş ağ durumunu tekrar oynat"), ("UC-10", "Arıza senaryosu çalıştır"),
                           ("UC-11", "Yedeklilik analizini görüntüle"), ("UC-12", "Kapasite senaryosu çalıştır")]),
    ("Veri yönetimi", [("UC-13", "Topolojiyi içe aktar"), ("UC-14", "Telemetri gönder")]),
]
STEP, PAD_TOP, PAD_BOT, GAP = 80, 62, 22, 24
SYS_X0, SYS_X1, PK_X0, PK_X1 = 300, 800, 330, 770
ax.text(W / 2, 32, "Kampüs Ağı Dijital İkizi — Use Case Diyagramı (v2)", ha="center", va="center", fontsize=15, weight="bold", color=INK)

y = 110; pos = {}; boxes = []
for name, ucs in GROUPS:
    top = y; y += PAD_TOP
    for code, label in ucs:
        pos[code] = y; y += STEP
    bot = y - STEP + UCH / 2 + PAD_BOT
    boxes.append((name, top, bot)); y = bot + GAP
sys_top, sys_bot = 70, y + 6

ax.add_patch(Rectangle((SYS_X0, sys_top), SYS_X1 - SYS_X0, sys_bot - sys_top, fill=False, ec=INK, lw=2.2))
ax.text((SYS_X0 + SYS_X1) / 2, sys_top + 20, "Kampüs Ağı Dijital İkizi", ha="center", va="center", fontsize=13, weight="bold", color=INK)
for name, top, bot in boxes:
    ax.add_patch(Rectangle((PK_X0, top), PK_X1 - PK_X0, bot - top, fc=LIGHT, ec=GRAY, lw=1))
    ax.add_patch(Rectangle((PK_X0, top), 150, 26, fc="#E2E2E2", ec=GRAY, lw=1))
    ax.text(PK_X0 + 10, top + 13, name, ha="left", va="center", fontsize=11, weight="bold", color=INK)
for (code, label), yy in ((u, pos[u[0]]) for _, ucs in GROUPS for u in ucs):
    ax.add_patch(Ellipse((UCX, yy), UCW, UCH, fc="white", ec=INK, lw=1.2, zorder=3))
    ax.text(UCX, yy - 11, code, ha="center", va="center", fontsize=10.5, weight="bold", color=INK, zorder=4)
    ax.text(UCX, yy + 11, label, ha="center", va="center", fontsize=10.5, color=INK, zorder=4)

def actor(x, yc, name, stereo=None, label_above=False):
    ax.add_patch(Circle((x, yc - 38), 12, fc="white", ec=INK, lw=1.6, zorder=5))
    ax.plot([x, x], [yc - 26, yc + 12], color=INK, lw=1.6, zorder=5)
    ax.plot([x - 22, x + 22], [yc - 14, yc - 14], color=INK, lw=1.6, zorder=5)
    ax.plot([x, x - 18], [yc + 12, yc + 40], color=INK, lw=1.6, zorder=5)
    ax.plot([x, x + 18], [yc + 12, yc + 40], color=INK, lw=1.6, zorder=5)
    ly = yc - 70 if label_above else yc + 66
    if label_above == "right":
        ax.text(x + 30, yc - 38, name, ha="left", va="center", fontsize=12, color=INK)
    else:
        ax.text(x, ly, name, ha="center", va="center", fontsize=12, color=INK)
    if stereo: ax.text(x, (ly - 22) if label_above else yc - 66, stereo, ha="center", va="center", fontsize=11, style="italic", color=INK)

def connect(ax_x, codes, yc, side, span):
    # Her bağlantı aktörün yanında ayrı bir noktadan başlar (tek noktada birleşmez)
    n = len(codes)
    for i, c in enumerate(codes):
        ay = yc - span / 2 + (span * i / (n - 1) if n > 1 else span / 2)
        ex = UCX - UCW / 2 if side == "left" else UCX + UCW / 2
        ax.plot([ax_x, ex], [ay, pos[c]], color=INK, lw=1.0, zorder=2)

tek_codes = [f"UC-{i:02d}" for i in range(1, 9)]
yon_codes = [f"UC-{i:02d}" for i in range(1, 14)]
tek_y = (pos["UC-01"] + pos["UC-08"]) / 2 + 70
yon_y = (pos["UC-01"] + pos["UC-13"]) / 2
TEK_X, YON_X = 130, 960
actor(TEK_X, tek_y, "Teknik personel"); connect(TEK_X + 26, tek_codes, tek_y - 6, "left", 60)
actor(YON_X - 30, yon_y, "Ağ\nyöneticisi", label_above="right"); connect(YON_X - 56, yon_codes, yon_y - 2, "right", 96)
sim_y = pos["UC-14"]
actor(YON_X, sim_y + 14, "Telemetri simülatörü", "«sistem»")
ax.plot([UCX + UCW / 2, YON_X - 26], [sim_y, sim_y], color=INK, lw=1.0, zorder=2)

ax.set_ylim(sys_bot + 30, 0)
fig.set_size_inches(W / 100, (sys_bot + 30) / 100)
fig.savefig("use-case.png", dpi=150, facecolor="white")
fig.savefig("use-case.svg", facecolor="white")
