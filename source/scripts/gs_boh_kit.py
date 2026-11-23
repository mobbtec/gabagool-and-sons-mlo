# LONG PIG — BACK OF HOUSE (owner brief 2026-11-02 "FINAL MLO COMPLETION", parts 4-6), built on the approved concept plan
# v2 (gs_30_concept_layout.py, docs 04/05): the existing L-shaped back area of the building (s 10.06-16.15 x t -1.23-11.42
# and s -2.90-10.06 x t 7.06-11.42, until now one empty shell) is divided by new 12 cm partitions into
#   kitchen (D2) | storage (L) | walk-in cooler | corridor | staff entry (D3) | staff back room | office | staff WC.
# No room is invented outside the vanilla envelope; the WC is 1.58 m wide (plan v2: 1.28 m) so a real GTA door fits.
# Geometry goes into its OWN drawable "gs_boh" (own material subset, own lights) so the hall drawable keeps its budget.
# Vanilla props are referenced by archetype name only (bounds: gs_v028_vb.py). Doors: vanilla prop_map_door_01 (steel).
import math
import gs_v021_kit as V0
import gs_v023_kit as K3
import gs_v026_kit as K6
import gs_v027_kit as K7
from gs_v027_kit import (V, PG, WORLD, Frame, F, emit, cbox, lathe, tube, FLOOR, CEIL, LT, VB, P, DAY_HOURS, FILL_FLAGS,
                         wall_yaw)
from gs_v028_vb import VB_V028

VB.update(VB_V028)
MAT = V.MAT
NIGHT_HOURS = K7.NIGHT_HOURS

# ================================================================== materials of the gs_boh drawable (subset of the hall)
BOH_MATS = ["walnut", "terrazzo", "steel", "enamel", "iron", "glass", "plaster", "tile", "tile_white", "rubber", "troffer",
            "notice", "decal5"]
BOH_SPECS = [K7.SHADER_SPECS[MAT[m]] for m in BOH_MATS]
_REMAP = {MAT[m]: i for i, m in enumerate(BOH_MATS)}

WT = 0.12                    # partition thickness
DOOR_H = 2.10                # open doorways (same as P1 / P2)
STEEL_DOOR = "prop_map_door_01"
SD = PG.VDOORS[STEEL_DOOR]
SD_W = SD["max"][0] - SD["min"][0]                     # 1.219
SD_HOLE = round(FLOOR + PG.DOOR_GAP + (SD["max"][2] - SD["min"][2]) + 0.02, 3)   # 2.489

# ================================================================== partitions (centre line, thickness WT)
# (name, axis, fixed, a0, a1, holes [(h0, h1, top, kind)], finish (-side, +side))
#   axis "s": wall runs along s at t = fixed (faces -t / +t);  axis "t": runs along t at s = fixed (faces -s / +s)
#   finish: "std" red tile wainscot 1.15 + cream plaster | "white" white tile to 2.0 + plaster | "cool" white tile full height
WC_S = (8.36, 9.94)
PARTS = [
    ("P1n corridor|storage", "t", 10.00, 7.06, PG.YN, [(7.18, 8.18, DOOR_H, "open")], ("std", "std")),
    ("P3 corridor|rooms", "s", 8.42, 0.54, 9.94, [(2.95, 3.95, DOOR_H, "open"), (6.70, 6.70 + SD_W + 0.02, SD_HOLE, "door"),
                                                  (8.60, 8.60 + SD_W + 0.02, SD_HOLE, "door")], ("std", "std")),
    ("P4 entry|backroom", "t", 0.60, 8.48, PG.YN, [], ("std", "std")),
    ("P5 backroom|office", "t", 5.60, 8.48, PG.YN, [], ("std", "std")),
    ("P6 office|WC", "t", 8.30, 8.48, PG.YN, [], ("std", "white")),
    ("P7 kitchen|storage", "s", 5.00, 10.06, PG.XE, [(10.31, 11.31, DOOR_H, "open"), (13.40, 13.40 + SD_W + 0.02, SD_HOLE, "door")],
     ("white", "std")),
    ("P8 storage|cooler", "t", 12.80, 5.06, 8.66, [], ("std", "cool")),
    ("P9 cooler|storage", "s", 8.60, 12.86, PG.XE, [], ("cool", "std")),
]
# P7: the cooler part of its +t side is white (cooler) — handled by COOL_RANGE
COOL_S = (12.86, PG.XE)
COOL_T = (5.06, 8.54)


def _plane(axis, fixed, side):
    """-> function (u, z) -> point on the face of the partition, outward normal."""
    off = fixed + side * WT / 2
    if axis == "s":
        return (lambda u, z: (u, off, z)), (0.0, float(side), 0.0)
    return (lambda u, z: (off, u, z)), (float(side), 0.0, 0.0)


def _rect(pt, n, u0, u1, z0, z1, mat, rep_u=None, rep_v=None, uoff=0.0):
    rep = V.REP.get(mat, 1.0)
    ru, rv = rep_u or rep, rep_v or rep
    vs = [pt(u0, z0), pt(u1, z0), pt(u1, z1), pt(u0, z1)]
    uv = [(u0 / ru + uoff, z0 / rv), (u1 / ru + uoff, z0 / rv), (u1 / ru + uoff, z1 / rv), (u0 / ru + uoff, z1 / rv)]
    return F(vs, mat, uv, hint=n)


def _bands(finish):
    """[(z0, z1, mat)] of a wall face, bottom to top."""
    if finish == "white":
        return [(FLOOR, FLOOR + 0.10, "rubber"), (FLOOR + 0.10, 2.00, "tile_white"), (2.00, CEIL, "plaster")]
    if finish == "cool":
        return [(FLOOR, FLOOR + 0.10, "rubber"), (FLOOR + 0.10, CEIL, "tile_white")]
    return [(FLOOR, FLOOR + 0.10, "rubber"), (FLOOR + 0.10, 1.15, "tile"), (1.15, CEIL, "plaster")]


def partition_faces():
    out, col = [], []
    for name, axis, fixed, a0, a1, holes, finish in PARTS:
        cuts = sorted({a0, a1} | {h for hh in holes for h in hh[:2]})
        for side, fin in ((-1, finish[0]), (1, finish[1])):
            pt, n = _plane(axis, fixed, side)
            for u0, u1 in zip(cuts[:-1], cuts[1:]):
                hole = next((h for h in holes if h[0] <= u0 + 1e-6 and u1 <= h[1] + 1e-6), None)
                zb = hole[2] if hole else FLOOR
                fin_here = fin
                if name.startswith("P7") and side > 0 and u0 >= COOL_S[0] - 1e-6:
                    fin_here = "cool"
                for (z0, z1, mat) in _bands(fin_here):
                    z0c = max(z0, zb)
                    if z1 - z0c > 1e-4:
                        emit(out, _rect(pt, n, u0, u1, z0c, z1, mat))
                if not hole:                                           # aluminium cap on the tile band
                    ztop = {"std": 1.15, "white": 2.00}.get(fin_here)
                    if ztop:
                        q = lambda u, z, side=side: pt(u, z)
                        p0, p1 = pt(u0, ztop), pt(u1, ztop)
                        d = (n[0] * 0.012, n[1] * 0.012, 0.0)
                        emit(out, F([p0, p1, (p1[0] + d[0], p1[1] + d[1], ztop), (p0[0] + d[0], p0[1] + d[1], ztop)], "steel",
                                    [(0, 0), (1, 0), (1, 0.05), (0, 0.05)], hint=(0.0, 0.0, 1.0)))
                        emit(out, F([p0, p1, (p1[0] + d[0], p1[1] + d[1], ztop - 0.012), (p0[0] + d[0], p0[1] + d[1], ztop - 0.012)],
                                    "steel", [(0, 0), (1, 0), (1, 0.05), (0, 0.05)], hint=n))
        # door / doorway jambs, heads and steel casings
        for (h0, h1, top, kind) in holes:
            for u, sg in ((h0, 1.0), (h1, -1.0)):
                if axis == "s":
                    vs = [(u, fixed - WT / 2, FLOOR), (u, fixed + WT / 2, FLOOR), (u, fixed + WT / 2, top), (u, fixed - WT / 2, top)]
                    hn = (sg, 0.0, 0.0)
                else:
                    vs = [(fixed - WT / 2, u, FLOOR), (fixed + WT / 2, u, FLOOR), (fixed + WT / 2, u, top), (fixed - WT / 2, u, top)]
                    hn = (0.0, sg, 0.0)
                emit(out, F(vs, "plaster", [(0, 0), (0.06, 0), (0.06, top), (0, top)], hint=hn))
            if axis == "s":
                vs = [(h0, fixed - WT / 2, top), (h1, fixed - WT / 2, top), (h1, fixed + WT / 2, top), (h0, fixed + WT / 2, top)]
            else:
                vs = [(fixed - WT / 2, h0, top), (fixed - WT / 2, h1, top), (fixed + WT / 2, h1, top), (fixed + WT / 2, h0, top)]
            emit(out, F(vs, "plaster", [(0, 0), (1, 0), (1, 0.06), (0, 0.06)], hint=(0.0, 0.0, -1.0)))
            cw, cp = 0.05, 0.015
            for side in (-1, 1):
                f0 = fixed + side * WT / 2
                f1 = f0 + side * cp
                lo, hi = min(f0, f1), max(f0, f1)
                for (b0, b1, z0, z1) in ((h0 - cw, h0, FLOOR, top + cw), (h1, h1 + cw, FLOOR, top + cw), (h0, h1, top, top + cw)):
                    if axis == "s":
                        out += cbox(WORLD, b0, b1, lo, hi, z0, z1, "enamel", grain="z" if z1 - z0 > 1 else "x")
                    else:
                        out += cbox(WORLD, lo, hi, b0, b1, z0, z1, "enamel", grain="z" if z1 - z0 > 1 else "x")
        # collision (solid parts + over the holes)
        for u0, u1 in zip(cuts[:-1], cuts[1:]):
            hole = next((h for h in holes if h[0] <= u0 + 1e-6 and u1 <= h[1] + 1e-6), None)
            z0 = hole[2] if hole else 0.0
            if axis == "s":
                col.append(((u0, u1, fixed - WT / 2, fixed + WT / 2, z0, CEIL), "PLASTER_SOLID"))
            else:
                col.append(((fixed - WT / 2, fixed + WT / 2, u0, u1, z0, CEIL), "PLASTER_SOLID"))
    # exposed end of P3 at the staff entry (s 0.54)
    emit(out, F([(0.54, 8.36, FLOOR), (0.54, 8.48, FLOOR), (0.54, 8.48, CEIL), (0.54, 8.36, CEIL)], "plaster",
                [(0, 0), (0.06, 0), (0.06, 1.7), (0, 1.7)], hint=(-1.0, 0.0, 0.0)))
    return out, col


# ================================================================== room finishes on the existing shell walls (overlays)
def _wall_overlay(p0, p1, n, finish, holes=()):
    """Tile / paint overlay 9 mm in front of a shell wall from p0 to p1 (2D), holes [(u0, u1, z_top)] along it."""
    out = []
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    off = 0.009
    pt = lambda u, z: (p0[0] + d[0] * u + n[0] * off, p0[1] + d[1] * u + n[1] * off, z)
    cuts = sorted({0.0, L} | {h for hh in holes for h in hh[:2]})
    for u0, u1 in zip(cuts[:-1], cuts[1:]):
        hole = next((h for h in holes if h[0] <= u0 + 1e-6 and u1 <= h[1] + 1e-6), None)
        zb = hole[2] if hole else FLOOR
        for (z0, z1, mat) in _bands(finish):
            if finish != "cool" and mat == "plaster":
                continue                                                 # keep the shell paint above the tile
            z0c = max(z0, zb)
            if z1 - z0c > 1e-4:
                emit(out, _rect(pt, (n[0], n[1], 0.0), u0, u1, z0c, z1, mat))
    return out


def finishes():
    out = []
    XE, YS, YN = PG.XE, PG.YS, PG.YN
    D2 = PG.D2
    # kitchen: white tile to 2.0 m on the shell walls (SW with D2, NE end wall, P1 back face)
    out += _wall_overlay((10.06, YS), (XE, YS), (0.0, 1.0), "white",
                         holes=[(D2["s"][0] - 10.06 - 0.075, D2["s"][1] - 10.06 + 0.075, D2["hole_top"] + 0.075)])
    out += _wall_overlay((XE, YS), (XE, 4.94), (-1.0, 0.0), "white")
    out += _wall_overlay((10.06 + 0.0, 4.94), (10.06, YS), (1.0, 0.0), "white", holes=[(4.94 - 0.07 - 0.075, 4.94 + 0.93 + 0.075, 2.175)])
    # cooler: white tile everywhere on its shell wall
    out += _wall_overlay((XE, 5.06), (XE, 8.54), (-1.0, 0.0), "cool")
    # WC: white tile on the NE end wall + P1n back
    out += _wall_overlay((WC_S[0], YN), (WC_S[1], YN), (0.0, -1.0), "white")
    out += _wall_overlay((9.94, 8.48), (9.94, YN), (-1.0, 0.0), "white")
    # floors: red quarry tile in the kitchen, white tile in the WC, grey rubber in the cooler (overlays 4 mm above the floor)
    for (s0, s1, t0, t1, mat) in ((10.06, XE, YS, 4.94, "tile"), (WC_S[0], WC_S[1], 8.48, YN, "tile_white"),
                                  (COOL_S[0], COOL_S[1], COOL_T[0], COOL_T[1], "rubber")):
        z = FLOOR + 0.004
        rep = 0.45 if mat != "rubber" else 1.0
        vs = [(s0, t0, z), (s1, t0, z), (s1, t1, z), (s0, t1, z)]
        emit(out, F(vs, mat, [(s0 / rep, t0 / rep), (s1 / rep, t0 / rep), (s1 / rep, t1 / rep), (s0 / rep, t1 / rep)], hint=(0, 0, 1)))
    return out


# ================================================================== own furniture
def steel_table(s0, s1, t0, t1, zt=0.91, shelf=0.25, splash=None):
    """Stainless prep / dish table: top with a rolled front edge, undershelf, 4 tube legs with bullet feet, optional splash."""
    out = []
    out += cbox(WORLD, s0, s1, t0, t1, zt - 0.035, zt, "steel", ch=0.006, grain="x")
    out += cbox(WORLD, s0 + 0.04, s1 - 0.04, t0 + 0.04, t1 - 0.04, shelf - 0.02, shelf, "steel", grain="x")
    for (s, t) in ((s0 + 0.04, t0 + 0.04), (s1 - 0.04, t0 + 0.04), (s1 - 0.04, t1 - 0.04), (s0 + 0.04, t1 - 0.04)):
        out += tube(WORLD, [(s, t, FLOOR + 0.03), (s, t, zt - 0.035)], 0.019, 8, "steel", caps=True)
        out += lathe(WORLD.child(s, t, 0.0), [(0.0, FLOOR), (0.016, FLOOR), (0.022, FLOOR + 0.03), (0.0, FLOOR + 0.03)], 8, "steel")
    if splash:                                                    # back splash on one edge ("-t" / "+t" / "-s" / "+s")
        if splash == "+t":
            out += cbox(WORLD, s0, s1, t1 - 0.012, t1, zt, zt + 0.15, "steel", grain="x")
        elif splash == "-t":
            out += cbox(WORLD, s0, s1, t0, t0 + 0.012, zt, zt + 0.15, "steel", grain="x")
        elif splash == "+s":
            out += cbox(WORLD, s1 - 0.012, s1, t0, t1, zt, zt + 0.15, "steel", grain="y")
        else:
            out += cbox(WORLD, s0, s0 + 0.012, t0, t1, zt, zt + 0.15, "steel", grain="y")
    return out


def exhaust_hood(s0, s1, t0, t1):
    """Wall canopy hood over the range: sloped front, filter bank, grease gutter, duct to the ceiling, worn steel."""
    out = []
    z0, z1, zt = 2.05, 2.30, 2.62
    out += cbox(WORLD, s0, s1, t0 + 0.30, t1, z1, zt, "steel", grain="x")                       # upper box (to the wall)
    # sloped front panel from (t0, z1) up to (t0 + 0.30, zt)
    vs = [(s0, t0, z1), (s1, t0, z1), (s1, t0 + 0.30, zt), (s0, t0 + 0.30, zt)]
    emit(out, F(vs, "steel", [(0, 0), (1, 0), (1, 0.4), (0, 0.4)], hint=(0.0, -0.73, 0.68)))
    out += cbox(WORLD, s0, s1, t0, t0 + 0.02, z0, z1, "steel", grain="x")                       # front skirt
    for x0 in (s0, s1 - 0.02):
        out += cbox(WORLD, x0, x0 + 0.02, t0, t1, z0, z1, "steel", grain="y")                    # side skirts
        vs = [(x0 + (0.02 if x0 > s0 else 0.0), t0, z1), (x0 + (0.02 if x0 > s0 else 0.0), t1, z1),
              (x0 + (0.02 if x0 > s0 else 0.0), t1, zt), (x0 + (0.02 if x0 > s0 else 0.0), t0 + 0.30, zt)]
        emit(out, F(vs, "steel", [(0, 0), (1, 0), (1, 0.3), (0, 0.3)], hint=(-1.0 if x0 == s0 else 1.0, 0.0, 0.0)))
    nf = int((s1 - s0 - 0.1) / 0.42)
    for k in range(nf):                                                                          # baffle filters (dark)
        a = s0 + 0.05 + k * (s1 - s0 - 0.1) / nf
        b = a + (s1 - s0 - 0.1) / nf - 0.01
        vs = [(a, t1 - 0.12, z1 + 0.02), (b, t1 - 0.12, z1 + 0.02), (b, t0 + 0.08, z1 + 0.02), (a, t0 + 0.08, z1 + 0.02)]
        emit(out, F(vs, "iron", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(0.0, 0.0, -1.0)))
    out += cbox(WORLD, s0 + 0.02, s1 - 0.02, t0 + 0.02, t0 + 0.08, z0 - 0.02, z0 + 0.02, "steel", grain="x")      # gutter
    sc, tc = (s0 + s1) / 2, t1 - 0.30
    out += cbox(WORLD, sc - 0.22, sc + 0.22, tc - 0.22, tc + 0.22, zt, CEIL, "steel", grain="z")               # duct
    return out


def wall_shelf(p0, p1, n, z, depth=0.30, mat="steel"):
    """Steel wall shelf with 2-3 brackets, p0 -> p1 along the wall, n = into the room."""
    out = []
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    fr = Frame((p0[0], p0[1], 0.0), (d[0], d[1], 0.0), (n[0], n[1], 0.0), (0.0, 0.0, 1.0))
    out += cbox(fr, 0.0, L, 0.0, depth, z - 0.025, z, mat, grain="x")
    out += cbox(fr, 0.0, L, depth - 0.02, depth, z, z + 0.03, mat, grain="x")
    nb = 2 if L < 1.3 else 3
    for k in range(nb):
        u = 0.1 + (L - 0.2) * k / (nb - 1)
        out += cbox(fr, u - 0.012, u + 0.012, 0.0, depth - 0.03, z - 0.20, z - 0.025, "steel", grain="z")
    return out


def counter_unit(s0, s1, t0, t1, zt=0.90):
    """Simple laminate base cabinet with a cream top (staff kitchenette)."""
    out = []
    out += cbox(WORLD, s0, s1, t0, t1, FLOOR, FLOOR + 0.10, "rubber", grain="x")
    out += cbox(WORLD, s0, s1, t0, t1, FLOOR + 0.10, zt - 0.03, "walnut", grain="x")
    out += cbox(WORLD, s0 - 0.02, s1 + 0.02, t0 - 0.02, t1 + 0.02, zt - 0.03, zt, "terrazzo", ch=0.004, grain="x")
    return out


def table_rect(sc, tc, L, W, zt=0.76):
    """Old formica dinette table (cream top, chrome edge band, two chrome T-legs)."""
    out = []
    out += cbox(WORLD, sc - L / 2, sc + L / 2, tc - W / 2, tc + W / 2, zt - 0.03, zt, "terrazzo", ch=0.006, grain="x")
    out += cbox(WORLD, sc - L / 2 - 0.004, sc + L / 2 + 0.004, tc - W / 2 - 0.004, tc + W / 2 + 0.004, zt - 0.03, zt - 0.006, "steel", grain="x")
    for x in (sc - L / 2 + 0.25, sc + L / 2 - 0.25):
        out += tube(WORLD, [(x, tc, FLOOR + 0.02), (x, tc, zt - 0.03)], 0.025, 10, "steel")
        out += cbox(WORLD, x - 0.03, x + 0.03, tc - W / 2 + 0.08, tc + W / 2 - 0.08, FLOOR, FLOOR + 0.03, "steel", grain="y")
    return out


def wc_mirror(s, t, z0, w=0.45, h=0.60, n=(1.0, 0.0)):
    """Small steel-framed mirror (glass_env, reflective look) on a wall facing n."""
    out = []
    d = (-n[1], n[0])
    fr = Frame((s, t, 0.0), (d[0], d[1], 0.0), (n[0], n[1], 0.0), (0.0, 0.0, 1.0))
    out += cbox(fr, -w / 2 - 0.02, w / 2 + 0.02, 0.0, 0.012, z0 - 0.02, z0 + h + 0.02, "steel", grain="z")
    vs = [fr.p(-w / 2, 0.014, z0), fr.p(w / 2, 0.014, z0), fr.p(w / 2, 0.014, z0 + h), fr.p(-w / 2, 0.014, z0 + h)]
    emit(out, F(vs, "glass", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(n[0], n[1], 0.0)))
    out += cbox(fr, -w / 2, w / 2, 0.0, 0.10, z0 - 0.06, z0 - 0.045, "steel", grain="x")      # little shelf
    return out


def wall_notice(p, n, z0, w, h, key, d=0.004):
    """Paper from the notices atlas (K5.NOTICE) on any wall facing n."""
    out = []
    dd = (-n[1], n[0])
    u0, v0, u1, v1 = K7.K5.notice_uv(key)
    fr = Frame((p[0], p[1], 0.0), (dd[0], dd[1], 0.0), (n[0], n[1], 0.0), (0.0, 0.0, 1.0))
    vs = [fr.p(-w / 2, d, z0), fr.p(w / 2, d, z0), fr.p(w / 2, d, z0 + h), fr.p(-w / 2, d, z0 + h)]
    emit(out, F(vs, "notice", [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=(n[0], n[1], 0.0)))
    return out


def vent_grille(p, n, z0, w=0.30, h=0.20):
    out = []
    dd = (-n[1], n[0])
    fr = Frame((p[0], p[1], 0.0), (dd[0], dd[1], 0.0), (n[0], n[1], 0.0), (0.0, 0.0, 1.0))
    out += cbox(fr, -w / 2, w / 2, 0.0, 0.012, z0, z0 + h, "enamel", grain="x")
    for k in range(6):
        z = z0 + 0.025 + k * (h - 0.05) / 5
        out += cbox(fr, -w / 2 + 0.02, w / 2 - 0.02, 0.012, 0.022, z - 0.006, z + 0.006, "enamel", grain="x")
    return out


def floor_drain(s, t):
    out = []
    out += cbox(WORLD, s - 0.10, s + 0.10, t - 0.10, t + 0.10, FLOOR + 0.0042, FLOOR + 0.006, "iron", grain="x")
    return out


def rubber_mat(s0, s1, t0, t1):
    return cbox(WORLD, s0, s1, t0, t1, FLOOR + 0.004, FLOOR + 0.016, "rubber", ch=0.004, grain="x", skip=("-z",))


# ================================================================== lights + fixtures per room
# (i, j, n_s, n_t, lamp) on the hall P grid (tile pitch); lamp: 0 cool, 1 warm, 2 weak, 3 dirty
BOH_TROFFERS = [
    (17, 0, 2, 1, 0), (21, 0, 2, 1, 3), (17, 4, 2, 1, 1), (21, 3, 2, 1, 0),            # kitchen
    (17, 9, 2, 1, 0), (21, 15, 2, 1, 2),                                               # storage
    (21, 10, 2, 1, 0),                                                                 # cooler (cold)
    (2, 11, 2, 1, 2), (9, 11, 2, 1, 1),                                                # corridor (weak / warm)
    (-3, 14, 2, 1, 3),                                                                 # staff entry
    (4, 15, 2, 1, 1),                                                                  # back room
    (10, 15, 2, 1, 0),                                                                 # office
]
COOL_LAMPS = {(21, 10)}
WC_LIGHT = (9.15, PG.YN - 0.009, 2.30)                            # cage light on the WC end wall, above the toilet


def boh_fixtures():
    out, L = [], []
    for (i, j, ns, nt, lamp) in BOH_TROFFERS:
        f, (sc, tc) = K6.troffer26(i, j, ns, nt, lamp)
        out += f
        c, g = K6.LAMP[lamp]
        if (i, j) in COOL_LAMPS:
            c = (0.86, 0.94, 1.0)
        L.append(LT("boh_troffer", "SPOT", (sc, tc, CEIL - 0.05), c, round(2.9 * g, 2), 4.6, 4.0, cone=(86.0, 34.0),
                    flags=("not_in_reflection",)))
    L.append(LT("boh_wc_cage", "POINT", (WC_LIGHT[0], WC_LIGHT[1] - 0.16, WC_LIGHT[2] + 0.02), (1.0, 0.86, 0.66), 1.4, 2.8, 6.0,
                flags=("not_in_reflection",)))
    return out, L


def boh_lights():
    out = []
    for l in boh_fixtures()[1]:
        out.append(dict(l, time=DAY_HOURS))
        out.append(dict(l, intensity=round(l["intensity"] * 0.55, 3), time=NIGHT_HOURS))
    return out


def _check_boh_ceiling():
    occ = {}
    for (i, j, ns, nt, lamp) in BOH_TROFFERS:
        s0, s1, t0, t1 = i * P, (i + ns) * P, j * P, (j + nt) * P
        for name, axis, fixed, a0, a1, holes, fin in PARTS:      # no troffer crosses a partition
            if axis == "s":
                assert not (t0 < fixed + WT / 2 and t1 > fixed - WT / 2 and s1 > a0 and s0 < a1), ("troffer over wall", i, j, name)
            else:
                assert not (s0 < fixed + WT / 2 and s1 > fixed - WT / 2 and t1 > a0 and t0 < a1), ("troffer over wall", i, j, name)
        assert PG.XW < s0 and s1 < PG.XE and PG.YS < t0 and t1 < PG.YN, ("troffer outside", i, j)
        assert not (s0 < 10.06 and t0 < 7.06), ("troffer in the hall", i, j)


_check_boh_ceiling()

# ================================================================== room dressing (own geometry)
YS, YN, XE = PG.YS, PG.YN, PG.XE


def kitchen_faces():
    out = []
    out += exhaust_hood(11.25, 13.05, 4.04, 4.94)
    out += steel_table(15.38, 16.13, 0.85, 2.45, splash="+s")                       # dish / drain table at the sink
    out += steel_table(12.05, 13.85, 1.55, 2.30)                                    # centre prep island
    out += wall_shelf((XE - 0.009, 0.85), (XE - 0.009, 2.45), (-1.0, 0.0), 1.62)    # over the dish table
    out += wall_shelf((11.30, YS + 0.009), (13.60, YS + 0.009), (0.0, 1.0), 1.75)   # dry goods / pans over the line
    out += floor_drain(13.95, 3.15)
    out += rubber_mat(14.93, 15.31, 2.65, 3.95)                                     # at the sink
    out += rubber_mat(11.45, 12.85, 3.55, 3.95)                                     # at the range
    out += cbox(WORLD, 13.08, 13.32, 4.40, 4.94, FLOOR, 0.91, "steel", grain="z")   # filler / spice cabinet next to the range
    # grease on the floor in front of the range, splash marks on the tile
    for (s, t, q, cell) in ((12.15, 3.70, 0.55, K6.GREASE), (13.0, 2.0, 0.6, K6.MOP), (15.0, 3.2, 0.45, K6.MOP)):
        emit(out, K6.d5((s - q, t - q, FLOOR + 0.0045), (2 * q, 0.0, 0.0), (0.0, 2 * q, 0.0), cell, (0.0, 0.0, 1.0)))
    return out


def storage_faces():
    out = []
    out += wall_notice((10.07, 9.4), (1.0, 0.0), 1.35, 0.26, 0.26, "schedule")      # stock list on P1n
    return out


def corridor_faces():
    out = []
    out += wall_notice((4.60, 8.359), (0.0, -1.0), 1.25, 0.50, 0.40, "cork")       # staff notice board
    out += wall_notice((4.48, 8.355), (0.0, -1.0), 1.36, 0.20, 0.20, "schedule", d=0.008)
    out += wall_notice((4.76, 8.355), (0.0, -1.0), 1.32, 0.18, 0.18, "special", d=0.008)
    emit(out, K6.d5((-2.6, 7.065, FLOOR + 0.12), (2.4, 0.0, 0.0), (0.0, 0.0, 0.25), K6.SCUFF_BAND, (0.0, 1.0, 0.0)))   # trolley scuffs
    emit(out, K6.d5((5.0, 8.355, FLOOR + 0.12), (3.0, 0.0, 0.0), (0.0, 0.0, 0.25), K6.SCUFF_BAND, (0.0, -1.0, 0.0)))
    return out


def staff_entry_faces():
    out = []
    out += wall_notice((0.539, 9.2), (-1.0, 0.0), 1.30, 0.26, 0.26, "permit")     # health permit copy / rules
    return out


def backroom_faces():
    out = []
    out += table_rect(2.95, 10.25, 1.60, 0.85)
    out += counter_unit(4.94, 5.54, 9.10, 10.30)
    out += wall_shelf((5.531, 9.10), (5.531, 10.30), (-1.0, 0.0), 1.55)
    out += wall_notice((5.53, 10.75), (-1.0, 0.0), 1.30, 0.30, 0.30, "calendar")
    out += wall_notice((1.6, 11.411), (0.0, -1.0), 1.45, 0.24, 0.24, "shop_photo", d=0.006)
    out += wall_notice((2.0, 11.411), (0.0, -1.0), 1.40, 0.30, 0.30, "clipping", d=0.006)
    out += cbox(WORLD, 0.70, 1.30, 10.80, 11.38, FLOOR, 0.62, "walnut", ch=0.004, grain="x")   # low TV cabinet
    return out


def office_faces():
    out = []
    out += wall_notice((7.0, 11.411), (0.0, -1.0), 1.35, 0.30, 0.30, "calendar")
    out += wall_notice((7.5, 11.411), (0.0, -1.0), 1.45, 0.26, 0.26, "permit")
    out += wall_notice((5.669, 10.6), (1.0, 0.0), 1.50, 0.26, 0.26, "shop_photo", d=0.006)
    out += wall_notice((5.669, 10.95), (1.0, 0.0), 1.38, 0.22, 0.22, "we_card")
    out += wall_shelf((5.669, 9.90), (5.669, 11.30), (1.0, 0.0), 1.80, depth=0.28, mat="walnut")
    return out


def wc_faces():
    out = []
    out += wc_mirror(8.369, 10.05, 1.25, n=(1.0, 0.0))
    out += vent_grille((8.70, YN - 0.009), (0.0, -1.0), 2.55)
    return out


def cooler_faces():
    out = []
    emit(out, K6.d5((13.4, 5.07, FLOOR + 0.10), (1.2, 0.0, 0.0), (0.0, 0.0, 0.30), K6.SCUFF_BAND, (0.0, 1.0, 0.0)))
    return out


def boh_faces():
    """All gs_boh geometry with materials REMAPPED to the BOH_MATS order."""
    f, _ = partition_faces()
    f += finishes()
    f += boh_fixtures()[0]
    for fn in (kitchen_faces, storage_faces, corridor_faces, staff_entry_faces, backroom_faces, office_faces, wc_faces, cooler_faces):
        f += fn()
    out = []
    for x in f:
        if x is None:
            continue
        if x["mat"] not in _REMAP:
            raise KeyError(("material not in BOH_MATS", x["mat"]))
        out.append(dict(x, mat=_REMAP[x["mat"]]))
    return out


def boh_collision():
    _, col = partition_faces()
    col += [((15.38, 16.13, 0.85, 2.45, FLOOR, 0.91), "METAL_SOLID_MEDIUM"),
            ((12.05, 13.85, 1.55, 2.30, FLOOR, 0.91), "METAL_SOLID_MEDIUM"),
            ((13.08, 13.32, 4.40, 4.94, FLOOR, 0.91), "METAL_SOLID_MEDIUM"),
            ((4.92, 5.56, 9.08, 10.32, FLOOR, 0.90), "WOOD_SOLID_MEDIUM"),
            ((2.15, 3.75, 9.83, 10.68, 0.70, 0.76), "WOOD_SOLID_MEDIUM"),
            ((0.70, 1.30, 10.80, 11.38, FLOOR, 0.62), "WOOD_SOLID_MEDIUM")]
    return col


# ================================================================== vanilla props (archetype names only)
def _on_wall(name, p, n, z):
    """Wall-mounted prop whose back is at local y = max y (front = -y): stand it on the wall facing n."""
    b = VB[name]
    return (name, p[0] + n[0] * (b[1][1] + 0.003), p[1] + n[1] * (b[1][1] + 0.003), z, wall_yaw(n))


def _against(name, p, n, gap=0.02):
    """Floor prop with its back (local +y) against a wall, front (-y) towards n."""
    b = VB[name]
    return (name, p[0] + n[0] * (b[1][1] + gap), p[1] + n[1] * (b[1][1] + gap), FLOOR, wall_yaw(n))


def boh_vanilla():
    out = []
    # ---- kitchen
    out.append(_against("prop_cooker_03", (12.15, 4.94 - 0.0), (0.0, -1.0)))
    out += [("prop_kitch_pot_huge", 11.80, 4.35, 0.97, 10.0), ("prop_kitch_pot_lrg", 12.45, 4.25, 0.97, 200.0)]
    out.append(_against("prop_ff_sink_02", (XE - 0.009, 3.30), (-1.0, 0.0)))
    out.append(_on_wall("prop_ff_sink_01", (11.75, YS + 0.009), (0.0, 1.0), 0.80))                  # hand sink by the door
    out.append(_on_wall("prop_soap_disp_01", (11.40, YS + 0.009), (0.0, 1.0), 1.10))
    out.append(_against("prop_fridge_01", (10.06 + 0.009, 3.05), (1.0, 0.0)))
    out.append(_against("prop_fridge_01", (10.06 + 0.009, 3.95), (1.0, 0.0)))
    out.append(_against("prop_ff_shelves_01", (10.06 + 0.009, 1.35), (1.0, 0.0)))
    out += [("v_res_fa_chopbrd", 12.55, 1.90, 0.91, 90.0), ("v_res_fa_chopbrd", 13.30, 1.95, 0.91, 85.0),
            ("prop_cleaver", 12.55, 1.85, 0.931, 70.0), ("prop_knife_stand", 13.70, 2.12, 0.91, 0.0),
            ("prop_kitch_pot_med", 12.30, 1.80, 0.25, 0.0), ("prop_ladel", 13.05, 1.75, 0.91, 30.0),
            ("prop_micro_01", 15.75, 1.05, 0.91, wall_yaw((-1.0, 0.0))), ("prop_kitch_pot_lrg", 15.70, 1.90, 0.91, 120.0)]
    out.append(("prop_cs_bin_02", 15.75, 0.40, FLOOR, 0.0))
    out.append(("prop_fire_exting_1a", 13.62, YS + 0.14, FLOOR, wall_yaw((0.0, 1.0))))
    # ---- storage
    out.append(_against("prop_shelves_01", (11.75, YN - 0.0), (0.0, -1.0)))
    out.append(_against("prop_shelves_02", (14.65, YN - 0.0), (0.0, -1.0)))
    out.append(_against("prop_shelves_01", (14.40, 8.66), (0.0, 1.0)))
    out += [("prop_boxpile_01a", 12.15, 6.00, FLOOR, 90.0), ("prop_cardbordbox_04a", 12.25, 7.55, FLOOR, 12.0),
            ("prop_cardbordbox_03a", 12.30, 8.25, FLOOR, -8.0), ("prop_cardbordbox_02a", 12.28, 8.22, FLOOR + 0.514, 20.0),
            ("prop_sacktruck_02a", 10.45, 10.30, FLOOR, 75.0), ("prop_cs_trolley_01", 15.35, 10.05, FLOOR, 0.0),
            ("prop_paper_box_01", 10.55, 9.20, FLOOR, 30.0), ("prop_paper_box_01", 10.58, 9.24, FLOOR + 0.364, 5.0),
            ("v_ind_cfbox2", 13.10, 10.05, FLOOR, 0.0), ("v_ind_cfbox", 13.45, 10.12, FLOOR, 40.0)]
    # ---- walk-in cooler
    out.append(_against("v_ind_cf_shelf", (XE - 0.009, 6.80), (-1.0, 0.0)))
    out.append(_against("prop_ff_shelves_01", (14.10, 8.54), (0.0, -1.0)))
    out += [("prop_fruit_plas_crate_01", 13.40, 6.20, FLOOR, 5.0), ("prop_fruit_plas_crate_01", 13.42, 6.22, FLOOR + 0.36, -7.0),
            ("v_ind_cf_crate2", 13.35, 7.20, FLOOR, 0.0), ("v_ind_cf_crate2", 13.36, 7.21, FLOOR + 0.40, 10.0)]
    # ---- cleaning corner (moved from v0.2.6: P1n now stands where two of its props were): staff entry, against P2
    out += [("v_serv_bktmop_h", -2.30, 7.42, FLOOR, 8.0), ("prop_tool_broom", -1.85, 7.17, FLOOR, 0.0),
            ("v_serv_wetfloorsn", -1.45, 7.38, FLOOR, 22.0), ("v_ind_cs_spray", -2.66, 7.25, FLOOR, 40.0)]
    out.append(("prop_fire_exting_1a", 6.10, 8.36 - 0.13, FLOOR, wall_yaw((0.0, -1.0))))
    # ---- staff entry (D3)
    out.append(_on_wall("prop_coathook_01", (0.54, 9.85), (-1.0, 0.0), 1.70))
    out.append(("v_club_roc_jacket1", 0.54 - 0.08, 9.75, 1.72 - 0.866, wall_yaw((-1.0, 0.0))))
    out.append(_against("prop_shelves_02", (-0.92, YN), (0.0, -1.0)))
    out += [("prop_bin_07a", -0.10, 7.55, FLOOR, 15.0), ("prop_sacktruck_02a", -0.20, 9.00, FLOOR, 200.0)]
    # ---- back room (staff)
    yaw_c = wall_yaw((0.0, 1.0))
    out += [("v_res_fa_chair01", 2.45, 9.55, FLOOR, wall_yaw((0.0, 1.0)) + 8.0), ("v_res_fa_chair01", 3.45, 9.60, FLOOR, wall_yaw((0.0, 1.0)) - 6.0),
            ("v_res_fa_chair01", 2.40, 10.95, FLOOR, wall_yaw((0.0, -1.0)) + 5.0), ("v_ret_gc_chair02", 3.50, 10.92, FLOOR, wall_yaw((0.0, -1.0)) - 9.0)]
    out += [("v_res_mmug", 2.70, 10.10, 0.76, 30.0), ("v_res_mp_ashtraya", 3.30, 10.40, 0.76, 0.0),
            ("prop_cs_paper_cup", 3.05, 10.05, 0.76, 0.0)]
    out.append(_against("prop_fridge_03", (5.54, 10.95), (-1.0, 0.0)))
    out += [("prop_micro_01", 5.20, 9.45, 0.90, wall_yaw((-1.0, 0.0))), ("prop_coffee_mac_02", 5.25, 10.05, 0.90, wall_yaw((-1.0, 0.0))),
            ("v_res_mmug", 5.05, 9.85, 0.90, 0.0), ("v_res_mmug", 5.08, 9.95, 0.90, 70.0)]
    out.append(("prop_tv_01", 1.00, 11.10, 0.62, wall_yaw((0.55, -0.83))))
    # ---- office
    out.append(_against("prop_office_desk_01", (6.95, YN), (0.0, -1.0), gap=0.06))
    out += [("v_res_tre_officechair", 6.95, 10.30, FLOOR, wall_yaw((0.0, 1.0)) + 12.0),
            ("prop_monitor_03b", 6.65, 11.05, 0.733, wall_yaw((0.0, -1.0)) + 8.0), ("prop_keyboard_01a", 6.75, 10.80, 0.733, wall_yaw((0.0, -1.0))),
            ("prop_office_phone_tnt", 7.45, 10.85, 0.733, wall_yaw((0.0, -1.0)) - 20.0), ("v_res_desklamp", 7.55, 11.15, 0.733, 0.0),
            ("prop_cd_folder_pile1", 6.15, 11.00, 0.733, 0.0), ("prop_cs_documents_01", 7.15, 10.78, 0.733, 15.0)]
    out.append(_against("v_med_cor_filingcab", (8.24, 11.05), (-1.0, 0.0)))
    out.append(_against("prop_ld_int_safe_01", (5.66, 9.10), (1.0, 0.0)))
    out.append(_on_wall("prop_coathook_01", (8.24, 10.05), (-1.0, 0.0), 1.70))
    out.append(("v_club_roc_jacket2", 8.24 - 0.08, 9.95, 1.72 - 0.774, wall_yaw((-1.0, 0.0))))
    out.append(("v_ret_csr_bin", 5.95, 10.55, FLOOR, 0.0))
    out.append(_on_wall("prop_fib_clipboard", (5.66, 9.95), (1.0, 0.0), 1.30))
    # ---- staff WC
    out.append(_against("prop_toilet_01", (9.30, YN - 0.009), (0.0, -1.0)))
    out.append(_against("prop_sink_06", (8.36 + 0.009, 10.05), (1.0, 0.0)))
    out.append(_on_wall("prop_toilet_roll_02", (9.94 - 0.009, 10.90), (-1.0, 0.0), 0.75))
    out.append(("prop_toilet_brush_01", 9.75, 11.20, FLOOR + 0.004, 0.0))
    out.append(_on_wall("prop_handdry_01", (9.94 - 0.009, 10.00), (-1.0, 0.0), 1.30))
    out.append(_on_wall("prop_soap_disp_01", (8.36 + 0.009, 9.72), (1.0, 0.0), 1.15))
    out.append(("v_ret_csr_bin", 8.62, 10.70, FLOOR + 0.004, 0.0))
    out.append(_on_wall("v_serv_metro_walllightcage", (WC_LIGHT[0], WC_LIGHT[1]), (0.0, -1.0), WC_LIGHT[2] - 0.19))
    return out


def boh_doors():
    """Steel doors (prop_map_door_01: hinge on the model x = 0, leaf along -x, slab local y -0.05..0) in the P3 / P7 holes.
    -> [(id, archetype, (s, t, z_origin), yaw_rad)]"""
    z = FLOOR + PG.DOOR_GAP - SD["min"][2]
    out = []
    for name, axis, fixed, a0, a1, holes, fin in PARTS:
        k = 0
        for (h0, h1, top, kind) in holes:
            if kind != "door":
                continue
            did = f"gs_boh_{name.split()[0].lower()}_{k}"
            k += 1
            out.append((did, STEEL_DOOR, (round(h1 - 0.01, 4), round(fixed + 0.025, 4), round(z, 4)), 0.0))
    return out


# references for the v0.2.6 cleaning corner props that must not be re-added by the hall kit (moved into the corridor)
CLEANING_OLD = {("v_serv_bktmop_h", 9.6, 7.45), ("v_serv_wetfloorsn", 10.12, 7.32), ("prop_tool_broom", 10.48, 7.17), ("v_ind_cs_spray", 9.4, 7.9)}
