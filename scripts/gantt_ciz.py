"""Proje zaman planının Gantt şemasını çizer.

Çıktı: docs/diagrams/gantt.png (300 dpi), gantt.svg, gantt.pdf
Plan verisi aşağıdaki TASKS listesindedir; tasarım değişse de içerik buradan gelir.
Yazı tipi: Inter (yoksa Aptos, Helvetica, Arial, DejaVu Sans).
"""
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "diagrams"

# --- İçerik (değiştirmeden önceki Gantt ile birebir aynı) -------------------------
TITLE = "Kampüs Ağı Dijital İkizi — Zaman Planı (21 Eylül - 31 Aralık 2026)"
START, END = date(2026, 9, 21), date(2026, 12, 31)
TODAY = date(2026, 11, 10)
D = date
TASKS = [  # (bölüm, ad, başlangıç, bitiş, durum)  durum: done / active / plan / other / milestone
    ("Hazırlık", "TEKNOFEST katılımı (proje dışı)", D(2026, 9, 28), D(2026, 10, 4), "other"),
    ("Hazırlık", "Proje araştırması", D(2026, 10, 5), D(2026, 10, 18), "done"),
    ("Hazırlık", "Kaynak taraması", D(2026, 10, 5), D(2026, 12, 13), "active"),
    ("Analiz ve modelleme", "Kapsam ve kullanım durumları", D(2026, 10, 19), D(2026, 10, 31), "done"),
    ("Analiz ve modelleme", "Ağ modeli ve doğrulama", D(2026, 11, 1), D(2026, 11, 10), "done"),
    ("Analiz ve modelleme", "Mimari ve diyagramlar", D(2026, 11, 9), D(2026, 11, 13), "active"),
    ("Analiz ve modelleme", "Danışmana sunum", D(2026, 11, 13), D(2026, 11, 13), "milestone"),
    ("Yazılım geliştirme", "Backend ve telemetri simülatörü", D(2026, 11, 16), D(2026, 11, 29), "plan"),
    ("Yazılım geliştirme", "Web arayüzü ve 3B görünüm", D(2026, 11, 16), D(2026, 12, 13), "plan"),
    ("Yazılım geliştirme", "İlk görünen sürüm", D(2026, 11, 22), D(2026, 11, 22), "milestone"),
    ("Yazılım geliştirme", "Senaryolar ve uyarılar", D(2026, 11, 30), D(2026, 12, 13), "plan"),
    ("Yazılım geliştirme", "Batfish–FRR deneyleri", D(2026, 12, 7), D(2026, 12, 20), "plan"),
    ("Bitiş", "Test ve entegrasyon", D(2026, 12, 14), D(2026, 12, 24), "plan"),
    ("Bitiş", "Bitirme raporu ve sunum", D(2026, 12, 14), D(2026, 12, 31), "plan"),
    ("Bitiş", "Teslim", D(2026, 12, 31), D(2026, 12, 31), "milestone"),
]
MONTHS = [("Eyl", D(2026, 9, 1)), ("Eki 2026", D(2026, 10, 1)), ("Kas 2026", D(2026, 11, 1)), ("Ara 2026", D(2026, 12, 1))]
TR_MON = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

# --- Tasarım ------------------------------------------------------------------
BG, INK, MUTED = "#FAFAFA", "#252525", "#7A7A7A"
GRID, GRID_SOFT, RULE = "#E6E6E6", "#F0F0F0", "#D9D9D9"
STYLE = {  # dolgu, kenar, yazı
    "done": ("#CDEBD3", "#7CC48A"),
    "active": ("#CFE3F7", "#6FA8DC"),
    "plan": ("#FFFFFF", "#C9C9C9"),
    "other": ("#F1F1F1", "#C9C9C9"),
}
TODAY_C, MILESTONE_C = "#F2C94C", "#3A3A3A"


def setup_font():
    for d in (Path("/usr/share/fonts/opentype/inter"), Path("/tmp/font/extras/ttf")):
        if d.exists():
            for f in d.glob("Inter-*.[ot]tf"):
                font_manager.fontManager.addfont(str(f))
    plt.rcParams["font.family"] = ["Inter", "Aptos", "Helvetica", "Arial", "DejaVu Sans"]


def main():
    setup_font()
    days = (END - START).days + 1
    weeks = [(START + timedelta(days=7 * i)) for i in range((days + 6) // 7)]

    # Yerleşim (birimler: x = gün, y = satır)
    label_w = 64.0          # sol ad sütunu (gün birimi cinsinden)
    row_h, sec_gap = 1.0, 0.9
    rows, y, last_sec = [], 0.0, None
    for sec, name, s, e, st in TASKS:
        if sec != last_sec:
            y += sec_gap if last_sec else 0.2
            rows.append(("section", sec, y))
            y += 0.95
            last_sec = sec
        rows.append(("task", (name, s, e, st), y))
        y += row_h
    total_h = y + 0.3

    fig_w = 13.0
    fig_h = 1.3 + total_h * 0.36 + 0.75
    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=BG)
    ax = fig.add_axes([0.03, 0.085, 0.94, 1 - 0.085 - 0.62 / fig_h])
    ax.set_facecolor(BG)
    x_lo, x_hi = -label_w, days + 1.5
    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(total_h, -2.6)
    ax.axis("off")
    X = lambda d: (d - START).days

    # Başlık
    fig.text(0.03, 1 - 0.32 / fig_h, TITLE, fontsize=17, fontweight="semibold", color=INK, va="top")

    # Aylar ve haftalar
    for i, (lab, m0) in enumerate(MONTHS):
        a = max(X(m0), 0)
        b = X(MONTHS[i + 1][1]) if i + 1 < len(MONTHS) else days
        ax.text(a + 1.2, -2.05, lab, fontsize=11.5, fontweight="semibold", color=INK, va="center")
        if a > 0:
            ax.plot([a, a], [-2.45, -1.65], color=RULE, lw=1)
    for w in weeks:
        xw = X(w)
        ax.text(xw + 3.5, -1.15, str(w.isocalendar().week), fontsize=9.5, color=MUTED, ha="center", va="center")
        ax.plot([xw, xw], [-0.75, total_h], color=GRID_SOFT, lw=0.8, zorder=0)
    ax.plot([0, days], [-0.75, -0.75], color=RULE, lw=1)

    # Bugün
    xt = X(TODAY) + 0.5
    ax.plot([xt, xt], [-0.75, total_h], color=TODAY_C, lw=2.2, zorder=1, solid_capstyle="butt")
    ax.text(xt, -0.45, "Bugün · 10 Kasım", fontsize=8.5, color="#8A6D00", ha="center", va="center", fontweight="medium",
            bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.6", fc="#FDF3D1", ec="none"), zorder=6)

    # Satırlar
    for kind, val, yy in rows:
        if kind == "section":
            ax.text(x_lo + 1.5, yy + 0.35, val, fontsize=10.5, fontweight="semibold", color="#5A5A5A", va="center")
            ax.plot([x_lo + 1.5, days], [yy + 0.8, yy + 0.8], color=GRID, lw=0.8, zorder=0)
            continue
        name, s, e, st = val
        cy = yy + 0.5
        ax.text(x_lo + 3.5, cy, name, fontsize=10.5, color=MUTED if st == "other" else INK, va="center",
                fontweight="semibold" if st == "milestone" and name == "Teslim" else "normal")
        # ad ile çubuğu bağlayan ince kılavuz
        ax.plot([x_lo + 3.5 + len(name) * 1.25, X(s) - 0.6], [cy, cy], color=GRID_SOFT, lw=0.8, ls=(0, (1, 2)), zorder=0)
        if st == "milestone":
            mx = X(s) + 0.5
            ax.add_patch(Polygon([[mx, cy - 0.3], [mx + 1.45, cy], [mx, cy + 0.3], [mx - 1.45, cy]], closed=True,
                                 fc=MILESTONE_C, ec="none", zorder=4))
            dl = f"{s.day} {TR_MON[s.month - 1]}"
            ha, off = ("right", -2.4) if mx > days - 6 else ("left", 2.4)
            ax.text(mx + off, cy, dl, fontsize=9, color=MUTED, va="center", ha=ha)
        else:
            fc, ec = STYLE[st]
            x0, w = X(s), X(e) - X(s) + 1
            ax.add_patch(FancyBboxPatch((x0 + 0.15, cy - 0.29), w - 0.3, 0.58,
                                        boxstyle="round,pad=0,rounding_size=0.9", mutation_aspect=0.35,
                                        fc=fc, ec=ec, lw=1.1, ls=(0, (3, 2)) if st == "other" else "solid", zorder=3))

    # Lejant (kompakt)
    lx, ly = 0.03, 0.045
    items = [("done", "Tamamlandı"), ("active", "Sürüyor"), ("plan", "Planlanan")]
    for i, (k, lab) in enumerate(items):
        fc, ec = STYLE[k]
        fig.patches.append(FancyBboxPatch((lx + i * 0.11, ly - 0.006), 0.022, 0.012 * 13 / fig_h * 0.9,
                                          boxstyle="round,pad=0,rounding_size=0.003", transform=fig.transFigure,
                                          fc=fc, ec=ec, lw=1))
        fig.text(lx + i * 0.11 + 0.028, ly, lab, fontsize=9.5, color=INK, va="center")
    fig.lines.append(plt.Line2D([lx + 0.33, lx + 0.33], [ly - 0.012, ly + 0.012], color=TODAY_C, lw=2.4, transform=fig.transFigure))
    fig.text(lx + 0.338, ly, "Bugün (10 Kasım)", fontsize=9.5, color=INK, va="center")
    fig.patches.append(Polygon([[lx + 0.465, ly - 0.008], [lx + 0.471, ly], [lx + 0.465, ly + 0.008], [lx + 0.459, ly]],
                               closed=True, transform=fig.transFigure, fc=MILESTONE_C, ec="none"))
    fig.text(lx + 0.478, ly, "Kilometre taşı", fontsize=9.5, color=INK, va="center")
    fig.text(0.97, ly, "Üstteki sayılar yılın hafta numaralarıdır (dönemin 1. haftası = 39. hafta).",
             fontsize=8.5, color=MUTED, va="center", ha="right")

    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"gantt.{ext}", dpi=300, facecolor=BG)
    print("gantt.png / gantt.svg / gantt.pdf yazıldı")


if __name__ == "__main__":
    main()
