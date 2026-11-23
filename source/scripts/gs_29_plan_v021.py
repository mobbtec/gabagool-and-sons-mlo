# LONG PIG — v0.2.1 measured front-hall plan (top view) from the SAME geometry modules the build uses
# (gs_proto_geometry = measured v0.1.6 shell, gs_v021_kit = v0.2.1 furniture / ceiling / fixtures).
#   python gs_29_plan_v021.py [out.png]
# Shows: walls / openings / door leaves, booths, tables, counters, cases, beams (dashed), fixtures, vanilla props,
# circulation + clearance dimensions, Hero Zones A / B.
import sys, math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyArrowPatch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gs_proto_geometry as PG
import gs_slice_geometry as SG
import gs_v021_kit as K

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent / "docs" / "art_direction" / "LONG_PIG_V021_PLAN.png"
fig, ax = plt.subplots(figsize=(16, 11), dpi=110)
ax.set_aspect("equal")
C = dict(wall="#2b2420", walnut="#6b4226", leather="#7a1f26", terr="#d8cfbe", steel="#9aa3a8", enamel="#efe6d2",
         glass="#7fb6d6", beam="#6b4226", light="#f2b233", text="#1d1a17", hero="#1f7a46", flow="#2f6db5")

# floor + walls of the front hall
ax.add_patch(Polygon(PG.FLOOR_POLY, closed=True, fc="#f4efe6", ec=C["wall"], lw=2.5))
ax.add_patch(Rectangle((SG.P1_S[0], PG.YS), SG.P1_S[1] - SG.P1_S[0], SG.P2_T[1] - PG.YS, fc=C["wall"], ec=C["wall"]))
ax.add_patch(Rectangle((PG.XW, SG.P2_T[0]), SG.P1_S[1] - PG.XW, SG.P2_T[1] - SG.P2_T[0], fc=C["wall"], ec=C["wall"]))
for a, b in (SG.P1_DOOR,):
    ax.add_patch(Rectangle((SG.P1_S[0] - 0.01, a), 0.14, b - a, fc="#f4efe6", ec="none"))
ax.add_patch(Rectangle((SG.P2_DOOR[0], SG.P2_T[0] - 0.01), SG.P2_DOOR[1] - SG.P2_DOOR[0], 0.14, fc="#f4efe6", ec="none"))
# windows + doors
ax.plot([PG.W1["s"][0], PG.W1["s"][1]], [PG.YS, PG.YS], color=C["glass"], lw=6, solid_capstyle="butt")
ax.plot([PG.XW, PG.XW], [PG.W2["t"][0], PG.W2["t"][1]], color=C["glass"], lw=6, solid_capstyle="butt")
d0, d1 = PG.DOOR_STRIP[0], PG.DOOR_STRIP[3]
ax.plot([PG.DOOR_STRIP[1][0], PG.DOOR_STRIP[2][0]], [PG.DOOR_STRIP[1][1], PG.DOOR_STRIP[2][1]], color="#c0392b", lw=5)
for did, arch, pos, yaw, pk in PG.vanilla_door_entities():
    if pk == "D1":
        ax.add_patch(Circle((pos[0], pos[1]), 0.70, fc="none", ec="#c0392b", ls=":", lw=1))
ax.text(-1.95, -0.35, "D1 entrance\n(double door,\nswing arcs)", fontsize=8, color="#c0392b", ha="center")
ax.text(3.46, PG.YS - 0.45, "W1 storefront window", fontsize=9, ha="center", color="#2f6d8f")
ax.text(PG.XW - 0.35, 4.9, "W2", fontsize=9, ha="center", color="#2f6d8f", rotation=90)

# beams + fixtures
pw = K.PRIMARY["w"]
for s in K.BEAM_S:
    t0 = PG.YS if s >= PG.P_SW[0] else K.chamfer_t_at(s)
    ax.add_patch(Rectangle((s - pw / 2, t0), pw, SG.P2_T[0] - t0, fc="none", ec=C["beam"], ls="--", lw=1.0))
for t in K.BEAM_T:
    s0 = max(PG.XW, K.chamfer_s_at(t)) if t < PG.P_NW[1] else PG.XW
    ax.add_patch(Rectangle((s0, t - 0.065), K.SOFFIT["s"][0] - s0, 0.13, fc="none", ec=C["beam"], ls="--", lw=0.8))
ax.add_patch(Rectangle((K.SOFFIT["s"][0], K.SOFFIT["t"][0]), 1.0, K.SOFFIT["t"][1] - K.SOFFIT["t"][0], fc="#e8dfcf", ec=C["beam"], ls="--", lw=1.0, alpha=0.6))
ax.text(7.5, 6.55, "counter soffit\nz 2.95 + cans", fontsize=7, ha="center")
for L in K.lights():
    x, y, z = L["pos"]
    mk = {"booth_pendant": ("o", 9), "dome": ("o", 8), "fan_kit": ("*", 14), "queue_pendant": ("o", 9), "soffit_can": ("s", 5),
          "sconce": ("^", 8), "picture_light": ("^", 6), "case": ("D", 4), "staff_fill": ("x", 7)}.get(L.get("kind"), ("o", 5))
    ax.plot(x, y, marker=mk[0], ms=mk[1], color=C["light"], mec="#7a5a10", mew=0.8)

# booths, tables
for a in K.booth_bays():
    for s0, s1 in ((a, a + K.BENCH_D), (a + K.BOOTH_PITCH - K.BENCH_D, a + K.BOOTH_PITCH)):
        ax.add_patch(Rectangle((s0, K.BENCH_T[0]), s1 - s0, K.BENCH_T[1] - K.BENCH_T[0], fc=C["leather"], ec=C["walnut"], lw=1.5))
    sc, tc = K.table_center(a)
    ax.add_patch(Rectangle((sc - K.TABLE_W / 2, K.TABLE_T[0]), K.TABLE_W, K.TABLE_T[1] - K.TABLE_T[0], fc=C["terr"], ec=C["walnut"], lw=1.5))
# counters + cases + back counter
for t0, t1 in K.CASES_T:
    ax.add_patch(Rectangle((K.COUNTER_FRONT, t0), 1.0, t1 - t0, fc=C["enamel"], ec="#777", lw=1.2))
    ax.add_patch(Rectangle((K.COUNTER_FRONT + 0.05, t0 + 0.04), 0.42, t1 - t0 - 0.08, fc=C["glass"], ec="none", alpha=0.35))
for (t0, t1), lab in ((K.REGISTER_T, "register"), (K.COFFEE_T, "coffee bar"), (K.GATE_T, "gate")):
    ax.add_patch(Rectangle((K.COUNTER_FRONT, t0), 1.0, t1 - t0, fc=C["walnut"], ec="#3a2414", lw=1.0, alpha=0.85))
    ax.text(K.COUNTER_FRONT + 0.5, (t0 + t1) / 2, lab, fontsize=7, color="white", ha="center", va="center", rotation=90)
ax.add_patch(Rectangle((K.BACK_S[0], K.BACK_T[0]), K.BACK_S[1] - K.BACK_S[0], K.BACK_T[1] - K.BACK_T[0], fc=C["enamel"], ec="#777", lw=1.0))
ax.text(9.6, 3.45, "back counter + slicer,\npaper roll, prosciutto stand;\nwall shelf + 2 vanilla menus", fontsize=7, ha="center", va="center", rotation=90)
ax.plot([K.COUNTER_FRONT + 0.32] * 2, [K.CASES_T[0][0] + 0.1, K.CASES_T[1][1] - 0.1], color="#b8862b", lw=2)
ax.text(7.32, 4.95, "salumi rail", fontsize=6.5, rotation=90, ha="center", color="#7a5a10")

# vanilla props (dots)
for name, s, t, zb, yaw in K.vanilla_props():
    if name.startswith(("bkr_prop_biker", "v_19")):
        continue
    ax.plot(s, t, ".", color="#555", ms=3)
for name, s, t, zb, yaw in K.vanilla_props():
    if name == "lr_prop_clubstool_01":
        ax.add_patch(Circle((s, t), 0.2, fc="#333", ec="none", alpha=0.6))
    if name == "prop_plant_int_01a":
        ax.add_patch(Circle((s, t), 0.4, fc="#3b6b2f", ec="none", alpha=0.5))
# flag
ax.plot([6.93, 6.93], [PG.YS + 0.08, PG.YS + 0.45], color="#0f7a41", lw=3)
ax.plot([6.93, 6.93], [PG.YS + 0.12, PG.YS + 0.28], color="#c8202f", lw=3)
ax.text(6.95, PG.YS + 0.62, "tricolore", fontsize=7, color="#0f7a41", ha="center")

# hero zones
ax.add_patch(Rectangle((4.30, PG.YS - 0.05), 2.75, 1.45, fc="none", ec=C["hero"], lw=2.5))
ax.text(5.65, 0.42, "HERO ZONE A", fontsize=10, color=C["hero"], ha="center", weight="bold")
ax.add_patch(Rectangle((6.95, 0.40), 3.05, 2.35, fc="none", ec=C["hero"], lw=2.5))
ax.text(8.45, 2.88, "HERO ZONE B", fontsize=10, color=C["hero"], ha="center", weight="bold")

# circulation + clearances
def arrow(p, q, txt=None, col=C["flow"]):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16, color=col, lw=2, alpha=0.8))
    if txt:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.15, txt, fontsize=8, color=col, ha="center")
arrow((-1.5, 0.6), (2.0, 2.0), "entry")
arrow((2.0, 2.0), (6.2, 2.4), "to the counter / queue")
arrow((2.4, 1.8), (2.4, 0.15), None)
arrow((4.25, 1.8), (4.25, 0.15), None)
arrow((6.6, 0.9), (6.6, -0.75), "staff pass", col="#8e44ad")
arrow((8.6, 6.2), (8.6, 0.6), "staff aisle", col="#8e44ad")


def dim(p, q, txt, off=(0, 0)):
    ax.annotate("", xy=p, xytext=q, arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1))
    ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], txt, fontsize=8, color="#c0392b", ha="center")
last = K.booth_bays()[-1] + K.BOOTH_PITCH
dim((last, -1.0), (K.COUNTER_FRONT, -1.0), f"{K.COUNTER_FRONT - last:.2f} m", (0, 0.12))
dim((5.0, K.BENCH_T[1]), (5.0, SG.P2_T[0]), f"aisle {SG.P2_T[0] - K.BENCH_T[1]:.2f} m (to P2)", (0.9, 0))
dim((K.COUNTER_FRONT - 0.62, 4.9), (K.COUNTER_FRONT, 4.9), "queue", (0, 0.12))
dim((K.COUNTER_FRONT, 6.0), (K.BACK_S[0], 6.0), f"{K.BACK_S[0] - K.COUNTER_BACK:.2f} m staff", (0.6, 0.15))
ax.text(1.8, 5.6, "P2 wall: heritage-wall + banquette (Phase 3)", fontsize=9, color="#555", style="italic")

ax.set_xlim(-3.4, 10.4)
ax.set_ylim(-2.0, 7.4)
ax.set_xlabel("s (m) — along the storefront (SW facade)")
ax.set_ylabel("t (m) — inwards")
ax.grid(True, ls=":", lw=0.5, alpha=0.5)
ax.set_title("LONG PIG v0.2.1 — front hall, measured plan (shell v0.1.6, layout from gs_v021_kit.py)", fontsize=12)
seats = 4 * K.N_BOOTHS + 3
ax.text(-3.3, 7.15, f"Seats now: {seats} (3 booths x 4 + 3 counter stools; v0.2.0: 15). Legend: yellow o pendant/dome, * fan + light kit, "
        f"square soffit can, ^ sconce/picture light, diamond case light; dashed = ceiling beams", fontsize=8)
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.tight_layout()
fig.savefig(OUT)
print("PLAN", OUT)
