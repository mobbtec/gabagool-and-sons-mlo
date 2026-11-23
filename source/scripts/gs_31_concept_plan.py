# Draws the dimensioned concept plan (stage A) from gs_30_concept_layout.
# usage: python3 gs_31_concept_plan.py <out_dir>
import math, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Arc, Circle, FancyArrow
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gs_30_concept_layout as L

INK = "#2b2420"
FILL = {
    "booth_bench": "#7A2328", "booth_table": "#d9cdb4", "cafe_table": "#d9cdb4", "chair": "#6b4a32",
    "column": "#2F5D3A", "gondola": "#a68a64", "shelf_wall": "#9c8a72", "coffee_stool": "#6b4a32",
    "deli_case": "#cfe3e6", "counter": "#5a3a26", "pastry_case": "#cfe3e6", "back_counter": "#5a3a26",
    "menu_board": "#1f1b18", "meat_rail": "#a3262a", "gate": "#7a5638", "window_display": "#b89a6a",
    "gingham_table": "#5f8a62", "kitchenette": "#c9c3b8", "tv": "#333333", "desk": "#7d868a",
    "filing": "#8b9497", "safe": "#4a4f52", "crates": "#a08050", "hand_truck": "#666",
    "range_hood": "#9aa1a4", "prep_table": "#b6bcbf", "sink": "#c3c9cc", "meat_saw": "#8d969a",
    "cooler_rack": "#b6bcbf",
}
LIGHT_C = {"troffer_cool": "#cfe2ff", "troffer_day": "#fff1c9", "neon_open": "#ff3b30"}


def wall_band(poly, thick=0.30):
    """outer outline of the vanilla walls (interior polygon offset outward)."""
    from shapely.geometry import Polygon
    p = Polygon(poly)
    return p.buffer(thick, join_style=2).exterior.coords, p.exterior.coords


def dim(ax, p0, p1, off, text, fs=8.5, col=INK):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    nx, ny = -dy / n * off, dx / n * off
    a0, a1 = (x0 + nx, y0 + ny), (x1 + nx, y1 + ny)
    ax.plot([x0, a0[0]], [y0, a0[1]], lw=0.5, color=col)
    ax.plot([x1, a1[0]], [y1, a1[1]], lw=0.5, color=col)
    ax.annotate("", a0, a1, arrowprops=dict(arrowstyle="<|-|>", lw=0.7, color=col, shrinkA=0, shrinkB=0, mutation_scale=7))
    ang = math.degrees(math.atan2(dy, dx))
    if ang > 90 or ang < -90:
        ang += 180
    mx, my = (a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2
    k = 0.16 if off >= 0 else -0.16
    ax.text(mx - dy / n * k, my + dx / n * k, text, ha="center", va="center", rotation=ang, fontsize=fs, color=col,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def door_arc(ax, hinge, closed_dir, open_dir, width, col=INK, lw=0.7):
    a0 = math.degrees(math.atan2(closed_dir[1], closed_dir[0]))
    a1 = math.degrees(math.atan2(open_dir[1], open_dir[0]))
    lo, hi = sorted([a0, a1])
    if hi - lo > 180:
        lo, hi = hi, lo + 360
    ax.add_patch(Arc(hinge, 2 * width, 2 * width, theta1=lo, theta2=hi, lw=lw, color=col, ls=(0, (3, 2)), zorder=8))
    ax.plot([hinge[0], hinge[0] + open_dir[0] * width], [hinge[1], hinge[1] + open_dir[1] * width], lw=1.4, color=col, zorder=8)


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(17, 12.4), dpi=110)
    ax.set_aspect("equal")
    ax.set_xlim(-6.0, 19.4)
    ax.set_ylim(-5.4, 14.6)
    ax.axis("off")

    outer, inner = wall_band(L.FLOOR_POLY)
    ax.add_patch(MPoly(list(outer), closed=True, fc="#4a403a", ec=INK, lw=1.0, zorder=1))
    ax.add_patch(MPoly(list(inner), closed=True, fc="#f6f1e7", ec=INK, lw=0.8, zorder=2))

    for name, code, poly, col in L.ZONES:
        ax.add_patch(MPoly(poly, closed=True, fc=col, alpha=0.22, ec="none", zorder=3))

    # openings in the vanilla wall: white gap + symbol
    for key, o in L.OPENINGS.items():
        (x0, y0), (x1, y1) = o["p0"], o["p1"]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        if key == "D1":
            inn = (0.73074, 0.68266)
        elif abs(dy) < 1e-6:
            inn = (0, 1)
        else:
            inn = (1, 0)
        out = (-inn[0], -inn[1])
        quad = [(x0 + out[0] * 0.32, y0 + out[1] * 0.32), (x1 + out[0] * 0.32, y1 + out[1] * 0.32), (x1 + inn[0] * 0.02, y1 + inn[1] * 0.02), (x0 + inn[0] * 0.02, y0 + inn[1] * 0.02)]
        ax.add_patch(MPoly(quad, closed=True, fc="white", ec="none", zorder=4))
        if o["kind"] == "window":
            for off in (0.10, 0.22):
                ax.plot([x0 + out[0] * off, x1 + out[0] * off], [y0 + out[1] * off, y1 + out[1] * off], lw=1.3, color="#3d8fb0", zorder=5)
            ax.plot([x0, x0 + out[0] * 0.32], [y0, y0 + out[1] * 0.32], lw=0.8, color=INK, zorder=5)
            ax.plot([x1, x1 + out[0] * 0.32], [y1, y1 + out[1] * 0.32], lw=0.8, color=INK, zorder=5)
        elif o["kind"] == "door2":
            half = n / 2
            door_arc(ax, (x0, y0), (ux, uy), inn, half)
            door_arc(ax, (x1, y1), (-ux, -uy), inn, half)
        else:
            hinge = (x1, y1)
            door_arc(ax, hinge, (-ux, -uy), inn, n)
        if key != "D1":
            continue
        far = 1.45
        lx, ly = (x0 + x1) / 2 + out[0] * far, (y0 + y1) / 2 + out[1] * far
        ax.text(lx, ly, o["label"], ha="center", va="center", fontsize=8.5, color="#1d5f7a" if o["kind"] == "window" else "#7a2328",
                rotation=-47, zorder=9, fontweight="bold")

    # partitions with door gaps
    for name, p0, p1, gaps in L.PARTITIONS:
        (x0, y0), (x1, y1) = p0, p1
        n = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / n, (y1 - y0) / n
        nx, ny = -uy, ux
        cuts = [0.0]
        for g0, g1, kind in sorted(gaps):
            cuts += [g0, g1]
        cuts.append(n)
        for a, b in zip(cuts[0::2], cuts[1::2]):
            if b - a < 1e-3:
                continue
            w = L.WALL_T / 2
            q = [(x0 + ux * a + nx * w, y0 + uy * a + ny * w), (x0 + ux * b + nx * w, y0 + uy * b + ny * w),
                 (x0 + ux * b - nx * w, y0 + uy * b - ny * w), (x0 + ux * a - nx * w, y0 + uy * a - ny * w)]
            ax.add_patch(MPoly(q, closed=True, fc="#5b514a", ec=INK, lw=0.5, zorder=6))
        for g0, g1, kind in gaps:
            h = (x0 + ux * g1, y0 + uy * g1)
            if kind == "door":
                door_arc(ax, h, (-ux, -uy), (nx, ny), g1 - g0, col="#5b514a", lw=0.6)
            else:
                ax.plot([x0 + ux * g0, h[0]], [y0 + uy * g0, h[1]], lw=2.2, color="#b58a55", zorder=6)
                ax.text((x0 + ux * (g0 + g1) / 2) - nx * 0.45, (y0 + uy * (g0 + g1) / 2) - ny * 0.45, "окно\nвыдачи", fontsize=6.5, ha="center", va="center", zorder=9, rotation=90 if abs(ux) < 0.5 else 0)

    # furniture
    for kind, box, note in L.FURNITURE:
        c = L.item_corners(box)
        elevated = len(box) >= 7
        ax.add_patch(MPoly(c, closed=True, fc=FILL.get(kind, "#999") if not elevated else "none",
                           ec=INK if not elevated else FILL.get(kind, "#999"), lw=0.5 if not elevated else 1.4,
                           ls="-" if not elevated else (0, (4, 2)), zorder=7, alpha=0.95))
        if kind == "booth_table":
            pass

    # lights
    for kind, (s, t, z), note in L.LIGHTS:
        col = LIGHT_C.get(kind, "#ffb347")
        ax.add_patch(Circle((s, t), 0.13, fc=col, ec="#7a4b00", lw=0.6, zorder=8))
        ax.plot([s - 0.17, s + 0.17], [t, t], lw=0.5, color="#7a4b00", zorder=8)
        ax.plot([s, s], [t - 0.17, t + 0.17], lw=0.5, color="#7a4b00", zorder=8)

    # zone labels
    LABEL_AT = {"gs_front": (3.6, 1.05), "gs_counter": (8.55, -0.75), "gs_corridor": (5.3, 7.72), "gs_staff_entry": (-1.25, 7.65),
                "gs_backroom": (3.2, 11.05), "gs_office": (7.05, 9.75), "gs_wc": (9.36, 9.9), "gs_kitchen": (12.9, 0.55),
                "gs_storage": (11.45, 9.6), "gs_cooler": (14.55, 6.55)}
    for name, code, poly, col in L.ZONES:
        x, y = LABEL_AT[code]
        lines = name.split(" (")
        title = lines[0] if code != "gs_front" else "Зал"
        ax.text(x, y, f"{title}\n{L.poly_area(poly):.1f} м²  ·  потолок {L.CEILING[code]:.2f}", ha="center", va="center",
                fontsize=8.8 if code not in ("gs_wc", "gs_corridor") else 7.0, color=INK, fontweight="bold", zorder=10,
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=1.2), rotation=90 if code == "gs_wc" else 0)

    # small callouts
    CALL = [((3.72, 0.32), "3 кабинки: бордовая кожа, шаг 1.85"), ((-2.25, 4.92), "витрина\nW2"),
            ((3.55, 4.55), "колонна"), ((2.1, 5.95), "стеллаж бакалеи"), ((7.5, 2.6), "витрины\nмясо · сыр"),
            ((7.5, 6.1), "кофе /\nвыпечка"), ((8.62, 1.6), "задний стол: слайсеры, эспрессо"), ((3.1, 9.9), "стол, клетчатая скатерть"),
            ((13.3, 2.4), "колода мясника"), ((14.5, 7.95), "окорока, ящики")]
    for (x, y), t in CALL:
        ax.text(x, y, t, ha="center", va="center", fontsize=6.6, color="#1a1a1a", zorder=11,
                rotation=90 if t.startswith("задний") else 0)

    # dimensions
    dim(ax, (-2.90, -1.23), (16.15, -1.23), -2.15, "19.05 м  (внутр. грань стен)")
    dim(ax, (16.15, -1.23), (16.15, 11.42), -1.15, "12.65 м")
    dim(ax, (0.584, -1.23), (7.0, -1.23), -1.25, "6.42")
    dim(ax, (7.0, -1.23), (10.0, -1.23), -1.25, "3.00")
    dim(ax, (10.0, -1.23), (16.15, -1.23), -1.25, "6.15")
    dim(ax, (1.263, -1.23), (5.654, -1.23), -0.55, "W1 витрина 4.39", col="#1d5f7a")
    dim(ax, (13.914, -1.23), (15.133, -1.23), -0.55, "D2 задняя дверь 1.22 (ступени)", col="#7a2328")
    dim(ax, (-2.90, 11.42), (-2.90, 7.0), -1.0, "4.42")
    dim(ax, (1.6, 7.06), (1.6, 8.36), 0.0, "1.30", fs=7)
    dim(ax, (-2.90, 7.0), (-2.90, 2.499), -1.0, "4.50")
    dim(ax, (-2.90, 6.394), (-2.90, 3.455), -0.45, "W2 окно 2.94", col="#1d5f7a")
    dim(ax, (-2.90, 10.402), (-2.90, 9.183), -0.45, "D3 дверь 1.22", col="#7a2328")
    dim(ax, (-2.90, 11.42), (0.60, 11.42), 0.55, "3.50")
    dim(ax, (0.60, 11.42), (5.60, 11.42), 0.55, "5.00")
    dim(ax, (5.60, 11.42), (8.60, 11.42), 0.55, "3.00")
    dim(ax, (8.60, 11.42), (10.0, 11.42), 0.55, "1.40")
    dim(ax, (10.0, 11.42), (16.15, 11.42), 0.55, "6.15")
    dim(ax, (16.15, 5.0), (16.15, -1.23), 0.55, "6.23")
    dim(ax, (6.2, 0.0), (6.2, 2.2), 0.0, "проход 2.2", fs=7)
    dim(ax, (8.0, 4.4), (9.24, 4.4), 0.0, "1.24", fs=7)

    # north arrow: world north in local (s,t) = (-0.719, 0.695)
    nx_, ny_ = -0.719, 0.695
    cx, cy = 18.1, 12.9
    ax.add_patch(FancyArrow(cx - nx_ * 0.6, cy - ny_ * 0.6, nx_ * 1.2, ny_ * 1.2, width=0.08, head_width=0.32, head_length=0.35, color=INK, zorder=12))
    ax.text(cx + nx_ * 1.3, cy + ny_ * 1.3, "С", fontsize=12, fontweight="bold", ha="center", va="center", color=INK)
    ax.text(-6.0, -4.9, "улица — фасад W1 / D2", fontsize=9, color="#555")
    ax.text(-6.0, 14.2, "LONG PIG · планировка v2 (согласовано направление; v2 — после аудита геометрии) · размеры в метрах, локальная система MLO (s, t)",
            fontsize=10.5, fontweight="bold", color=INK)
    ax.text(-6.0, 13.65, "Стены здания и проёмы W1/W2/D1/D2/D3 — существующие (vanilla). Перегородки 12 см — новые. Пунктир — над головой (меню-борды, рейка с колбасами).",
            fontsize=8.5, color="#444")

    # legend
    lx, ly = 3.0, -5.15
    leg = [("#7A2328", "кабинки, кожа"), ("#cfe3e6", "холод. витрины"), ("#5a3a26", "прилавок / задний стол"),
           ("#5f8a62", "задняя комната"), ("#b6bcbf", "нерж. оборудование"), ("#9c8a72", "стеллажи"), ("#ffb347", "светильник 2700K"), ("#cfe2ff", "светильник 4000K")]
    for i, (c, t) in enumerate(leg):
        x, y = lx + (i % 4) * 4.1, ly + (1 - i // 4) * 0.45
        ax.add_patch(MPoly([(x, y), (x + 0.35, y), (x + 0.35, y + 0.3), (x, y + 0.3)], closed=True, fc=c, ec=INK, lw=0.4))
        ax.text(x + 0.5, y + 0.15, t, fontsize=7.6, va="center")

    fig.savefig(os.path.join(out_dir, "plan_v2.png"), bbox_inches="tight", pad_inches=0.15)
    fig.savefig(os.path.join(out_dir, "plan_v2.svg"), bbox_inches="tight", pad_inches=0.15)
    print("written", out_dir)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../../docs/concept")
