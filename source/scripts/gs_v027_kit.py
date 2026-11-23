# LONG PIG — v0.2.7 pass over v0.2.6 from the owner's in-game test (2026-11-02, 9 FiveM screenshots, b3095).
# Everything not listed here is the v0.2.6 kit (preserve first).
#   NIGHT    the hall was blown out at night (GTA raises exposure after dark): every interior light now exists twice with
#            hour masks (vanilla method, e.g. apartment / clubhouse lamps): DAY 07-19 at the v0.2.6 strength the owner
#            approved, NIGHT 20-06 at ~half. Troffer cones wider + softer (no dark wavy band at the wall top), ledge cans
#            soft-edged and weaker (no scallops above W2), small bounce points under 4 troffers (ceiling halo), lighter
#            ceiling vertex colours, timecycle artificial "up" ambient raised (ceiling no longer black).
#   SW PIER  NO LOITERING card -> old tin "COLD CUTS" thermometer sign (own art).
#   MAT      6 x 4 ft charcoal nylon logo mat with ribbed rubber border (the type US restaurants bought 1990s-2000s).
#   GATE     the empty short counter by case 1: take-out menus, tip jar, service bell, receipt spike, folded local paper,
#            interfolded deli sheets, food-stamps card, a pepper jar.
#   FLOOR    litter (crushed cans, crumpled paper, flyer, straw papers, butts by the door), puddles (glossy decal),
#            soda spill, wet shoe prints; the leak in the ceiling now drips into a puddle with a wet-floor sign.
#   P2 TOP   roof leak streaks from the ceiling + stained tiles; two high import shelves (tomato cans, olive-oil tins,
#            jars, wine) — the classic Italian-deli top shelf.
#   W1 WALL  vinyl LONG PIG DELI banner over the storefront windows, old CRT TV on a ceiling bracket in the counter corner.
#   NW PIER  fast-food trash receptacle with "THANK YOU" flap and tray top (dirty trays, cups).
#   FIXES    duplicate butcher-paper roll removed (v0.2.1 roll stays), deli sheets moved off the prosciutto stand,
#            tongs moved clear of it.
import math
import gs_v021_kit as V0
import gs_v023_kit as K3
import gs_v025_kit as K5
import gs_v026_kit as K6
from gs_v026_kit import *                    # noqa: F401,F403
from gs_v026_kit import (V, PG, SG, WORLD, Frame, F, emit, cbox, prism, lathe, tube, FLOOR, CEIL, LT, CORONA, VB, P, P1_S, P2_T,
                         BACK_S, COUNTER_FRONT, BANQ_T, BANQ_TABLES, ZT, wall_frame, wall_u, notice, PIER_A, PIER_B, CTABLES,
                         _pbr, retex, d5, dcell5, panel_fr, DAY_HOURS, FILL_FLAGS, C_TUNGSTEN, TOP_GRIME, GRIT, MOP, GREASE,
                         CUP_RINGS, wall_yaw)
from gs_v027_vb import VB_V027

VB.update(VB_V027)
V.MAT.update({"wall6": 24, "decal6": 25, "puddle": 26})
V.REP.update({"wall6": 1.0, "decal6": 1.0, "puddle": 1.0})
MAT = V.MAT
VERSION = "0.2.7-feedback"

SHADER_SPECS = list(K6.SHADER_SPECS)
SHADER_SPECS[0] = retex(SHADER_SPECS[0], lp4_laminate_red="lp6_laminate_red")           # memory: 1024 -> 512
SHADER_SPECS[2] = retex(SHADER_SPECS[2], lp4_laminate_cream="lp6_laminate_cream")       # memory: 1024 -> 512
SHADER_SPECS[8] = retex(SHADER_SPECS[8], lp3_food_n="lp6_food_n")                       # memory: 1024 -> 512
SHADER_SPECS[19] = _pbr("lp6_mat", "lp6_mat", "lp6_mat_n", "lp_matte_s", 8.0, 0.15)      # 6 x 4 ft logo mat
SHADER_SPECS += [_pbr("lp6_atlas", "lp6_atlas", "lp_flat_n", "lp_matte_s", 10.0, 0.15),  # 24 signs, labels, station
                 ("decal.sps", {"DiffuseSampler": "lp6_decal"}, {}, "lp6_decal"),       # 25 leaks, spill, shoe prints
                 ("normal_spec_decal.sps", {"DiffuseSampler": "lp6_puddle", "BumpSampler": "lp_flat_n", "SpecSampler": "lp6_puddle_s"},
                  {"specularIntensityMult": 1.0, "specularFalloffMult": 120.0, "specularFresnel": 0.98, "bumpiness": 0.1},
                  "lp6_puddle")]                                                          # 26 glossy puddles
assert len(SHADER_SPECS) == len(MAT)

CAM_VIEWS = dict(K6.CAM_VIEWS)
CAM_VIEWS.update({
    "GS27_NIGHT": ((-1.2, 1.4, 1.65), (6.2, 2.2, 1.45), "night check: hall from the entrance (/gs_time 23)"),
    "GS27_W2": ((0.9, 4.9, 1.6), (-2.9, 4.9, 2.2), "night check: W2 wall above the ledge (cans)"),
    "GS27_P2TOP": ((1.6, 3.2, 1.7), (1.6, 6.94, 2.75), "P2 top: leak streaks + import shelves"),
    "GS27_W1": ((3.4, 3.6, 1.7), (4.4, -1.23, 2.3), "W1 wall: banner, TV, thermometer sign"),
    "GS27_GATE": ((5.6, 0.9, 1.65), (7.45, 0.05, 1.02), "gate counter dressing"),
    "GS27_STATION": ((-0.6, 3.6, 1.55), (-2.8, 2.95, 0.85), "tray / trash station on the NW pier"),
    "GS27_FLOOR": ((4.2, 3.9, 1.25), (2.2, 4.8, 0.0), "leak puddle, wet-floor sign, litter"),
    "GS27_MAT": ((1.0, 2.4, 1.55), (-1.15, 0.45, 0.0), "entrance: 6 x 4 ft logo mat, puddle, butts"),
})

# ================================================================== 1. NIGHT LIGHTING
NIGHT_HOURS = 0xFFFFFF & ~DAY_HOURS                            # 20:00-06:59
NIGHT_SCALE = {"troffer": 0.48, "banquette_key": 0.55, "ledge_can": 0.50, "entrance_can": 0.60, "soffit_can": 0.60,
               "menu_glow": 0.75, "staff_fill": 0.70, "case": 0.80, "entrance_wall_light": 0.70, "ceiling_bounce": 0.70}
BOUNCE_TROFFERS = [(0, 1), (-2, 4), (2, 4), (4, 6)]           # hall troffers that get a ceiling halo


def _tune(l):
    k = l["kind"]
    if k.startswith("troffer_lamp"):                           # wider + softer: walls lit to the ceiling angle, no hard edge
        return dict(l, cone_out=86.0, cone_in=34.0, intensity=round(l["intensity"] * 0.94, 3))
    if k == "ledge_can":                                       # 0.45 m off the NW wall: soft-edged, weaker -> no scallops
        return dict(l, cone_out=40.0, cone_in=10.0, intensity=2.6)
    return l


def _family(kind):
    return "troffer" if kind.startswith("troffer_lamp") else kind


def lights():
    L = []
    base = []
    for l in K6.lights():
        if l["kind"] == "window_day_fill":                     # already day-only
            L.append(l)
            continue
        base.append(_tune(l))
    for (i, j) in BOUNCE_TROFFERS:                             # Rockstar method: small point under the fixture = ceiling halo
        sc, tc = (i + 1) * P, (j + 0.5) * P
        base.append(LT("ceiling_bounce", "POINT", (sc, tc, CEIL - 0.42), (0.98, 0.95, 0.90), 0.45, 1.6, 4.0, flags=FILL_FLAGS))
    for l in base:
        L.append(dict(l, time=DAY_HOURS))
        f = NIGHT_SCALE.get(_family(l["kind"]), 0.6)
        L.append(dict(l, intensity=round(l["intensity"] * f, 3), time=NIGHT_HOURS))
    return L


def cpv_hall(v):
    """v0.2.7: as v0.2.2 but the ceiling falls off much less (0.34 -> 0.29 instead of 0.19): with the night exposure the
    v0.2.6 ceiling read as a black lid over blown walls."""
    r, g, b, a = V0.cpv_hall(v)
    s, t, z = v
    if z >= 2.20:
        g = round(0.34 - 0.05 * min(1.0, (z - 2.20) / 1.20), 3)
    return (r, g, b, a)


# ================================================================== helpers
REG6 = {"banner": (0, 0, 1024, 136), "thermo": (0, 136, 128, 520), "flap": (128, 136, 384, 392), "menus": (384, 136, 640, 392),
        "news": (640, 136, 1024, 392), "tips": (128, 392, 384, 520), "stamps": (384, 392, 640, 520), "can_label": (640, 392, 1024, 456),
        "tin_label": (640, 456, 832, 744), "tin_label2": (832, 456, 1024, 744), "station_top": (0, 520, 640, 1024)}


def w6_uv(key, pad=0.001):
    x0, y0, x1, y1 = REG6[key]
    return (x0 / 1024 + pad, 1 - y1 / 1024 + pad, x1 / 1024 - pad, 1 - y0 / 1024 - pad)


def aspect6(key):
    x0, y0, x1, y1 = REG6[key]
    return (y1 - y0) / (x1 - x0)


def dcell6(i):
    cx, cy = i % 2, i // 2
    return (cx / 2.0 + 0.003, 1.0 - (cy + 1) / 2.0 + 0.003, (cx + 1) / 2.0 - 0.003, 1.0 - cy / 2.0 - 0.003)


LEAK_WIDE, LEAK_NARROW, SPILL, PRINTS = range(4)


def d6(p0, du, dv, cell, hint, mat="decal6"):
    u0, v0, u1, v1 = dcell6(cell) if mat == "decal6" else (0.0, 0.0, 1.0, 1.0)
    vs = [p0, tuple(p0[k] + du[k] for k in range(3)), tuple(p0[k] + du[k] + dv[k] for k in range(3)), tuple(p0[k] + dv[k] for k in range(3))]
    return F(vs, mat, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=hint)


def floor_quad(s, t, w, d, yaw_deg, cell, mat="decal6", z=FLOOR + 0.0031):
    a = math.radians(yaw_deg)
    ex, ey = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    p0 = (s - ex[0] * w / 2 - ey[0] * d / 2, t - ex[1] * w / 2 - ey[1] * d / 2, z)
    return d6(p0, (ex[0] * w, ex[1] * w, 0.0), (ey[0] * d, ey[1] * d, 0.0), cell, (0.0, 0.0, 1.0), mat)


def top_quad(fr, x0, x1, y0, y1, z, uvbox, mat="wall6", rot=False):
    u0, v0, u1, v1 = uvbox
    vs = [fr.p(x0, y0, z), fr.p(x1, y0, z), fr.p(x1, y1, z), fr.p(x0, y1, z)]
    uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)] if not rot else [(u1, v0), (u1, v1), (u0, v1), (u0, v0)]
    return F(vs, mat, uv, hint=fr.v(0.0, 0.0, 1.0))


def label_cyl(fr, r, z0, z1, n, uvbox, mat="wall6", a0=0.0, arc=2 * math.pi):
    """Paper label around a cylinder (local Z axis, right-handed frame): u runs with the angle (reads left -> right from
    outside), v up; arc < 2 pi for a front label."""
    out = []
    u0, v0, u1, v1 = uvbox
    for i in range(n):
        aa, ab = a0 + arc * i / n, a0 + arc * (i + 1) / n
        vs = [fr.p(r * math.cos(aa), r * math.sin(aa), z0), fr.p(r * math.cos(ab), r * math.sin(ab), z0),
              fr.p(r * math.cos(ab), r * math.sin(ab), z1), fr.p(r * math.cos(aa), r * math.sin(aa), z1)]
        ua, ub = u0 + (u1 - u0) * i / n, u0 + (u1 - u0) * (i + 1) / n
        am = (aa + ab) / 2
        emit(out, F(vs, mat, [(ua, v0), (ub, v0), (ub, v1), (ua, v1)], hint=fr.v(math.cos(am), math.sin(am), 0.0), smooth=True))
    return out


# ================================================================== 2. SW PIER: thermometer sign instead of NO LOITERING
def sw_wall_faces():
    out = []
    out += notice("SW", PIER_B, PG.YS, 1.22, 0.62, 0.62, "cork", d=0.006, frame="alu", fw=0.022)
    out += notice("SW", 5.86, PG.YS, 1.48, 0.20, 0.20, "grade", d=0.010)
    fr, n = wall_frame("SW")
    w = 0.21
    h = w * aspect6("thermo")
    out += panel_fr(fr, n, wall_u("SW", PIER_A, PG.YS), 1.16, w, h, w6_uv("thermo"), "wall6", d=0.0, board=0.007)
    return out


def decal_faces():
    """v0.2.6 decals minus the sconce ghost at PIER_A (the thermometer sign hangs there now)."""
    fr, n = wall_frame("SW")
    ua = wall_u("SW", PIER_A, PG.YS)
    ghost = K3.decal_quad(fr.p(ua - 0.11, 0.004, 1.62), V.mul(fr.X, 0.22), (0.0, 0.0, 0.28), K5.dcell(K5.GHOST))
    return [f for f in K6.decal_faces() if f is not None and f["v"] != ghost["v"]]


# ================================================================== 3. ENTRY MAT: 6 x 4 ft logo mat
MAT_W, MAT_D = 1.83, 1.22


def mat_frame():
    d2, n2, L = K3._chamfer_frame()
    um = (PG.D1["a"][0] + PG.D1["a"][1]) / 2
    c = (PG.P_NW[0] + d2[0] * um + n2[0] * 0.05, PG.P_NW[1] + d2[1] * um + n2[1] * 0.05)
    return Frame((c[0], c[1], 0.0), (d2[0], d2[1], 0.0), (n2[0], n2[1], 0.0), (0.0, 0.0, 1.0)), d2, n2


def entry_mat27():
    """Nylon-pile logo mat on a ribbed rubber backing (top 9 mm), bevelled rubber edge down to the floor. UV 0..1 = the
    whole 1536 x 1024 design (squeezed into 1024 x 512), so 'LONG PIG' reads for people coming in."""
    fr, d2, n2 = mat_frame()
    out = []
    w, dep, hz, b = MAT_W, MAT_D, FLOOR + 0.009, 0.014
    vs = [fr.p(-w / 2, 0.0, hz), fr.p(w / 2, 0.0, hz), fr.p(w / 2, dep, hz), fr.p(-w / 2, dep, hz)]
    emit(out, F(vs, "mat", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(0.0, 0.0, 1.0)))     # text upright for people walking in
    lo = FLOOR + 0.0012
    rim = [((-w / 2, 0.0), (w / 2, 0.0), (0.0, -1.0)), ((w / 2, 0.0), (w / 2, dep), (1.0, 0.0)),
           ((w / 2, dep), (-w / 2, dep), (0.0, 1.0)), ((-w / 2, dep), (-w / 2, 0.0), (-1.0, 0.0))]
    for (a, bb, (nx, ny)) in rim:
        p0, p1 = fr.p(a[0], a[1], hz), fr.p(bb[0], bb[1], hz)
        q0, q1 = fr.p(a[0] + nx * b, a[1] + ny * b, lo), fr.p(bb[0] + nx * b, bb[1] + ny * b, lo)
        out_n = fr.v(nx, ny, 0.6)
        emit(out, F([p0, p1, q1, q0], "rubber", [(0, 0), (1, 0), (1, 0.05), (0, 0.05)], hint=out_n))
    return out


# ================================================================== 4. GATE COUNTER (s 6.97-8.00, t -0.38..0.46, top 1.02)
ZG = 1.02


def gate_faces():
    out = []
    # take-out menus: a short stack, top copy slightly turned
    fr = WORLD.child(7.20, 0.20, 0.0, math.radians(84.0))
    for k in range(5):
        out += cbox(fr, -0.095, 0.095, -0.095, 0.095, ZG + 0.004 * k, ZG + 0.004 * (k + 1), "terrazzo", grain="x")
    fr2 = WORLD.child(7.205, 0.205, 0.0, math.radians(-90.0 + 6.0))             # text upright for a customer at -s
    emit(out, top_quad(fr2, -0.095, 0.095, -0.095, 0.095, ZG + 0.0205, w6_uv("menus")))
    # tip jar: glass, label on the customer side, a few folded bills (cream paper) inside
    frj = WORLD.child(7.13, -0.20, 0.0)
    out += lathe(frj, [(0.0, ZG), (0.060, ZG), (0.064, ZG + 0.006), (0.064, ZG + 0.150), (0.054, ZG + 0.162), (0.054, ZG + 0.172),
                       (0.051, ZG + 0.172)], 18, "glass")
    lab = Frame(frj.O, (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))         # angle pi/2 = towards the customers
    out += label_cyl(lab, 0.0655, ZG + 0.045, ZG + 0.110, 8, w6_uv("tips"), a0=math.pi / 2 - 1.1, arc=2.2)
    gb = (0.825, 0.326, 0.869, 0.375)                                             # plain green print = folded bills
    for k, (dx, dy, a, h) in enumerate(((0.012, 0.008, 20, 0.07), (-0.015, -0.01, -35, 0.06), (0.0, 0.016, 70, 0.08))):
        fb = WORLD.child(7.13 + dx, -0.20 + dy, 0.0, math.radians(a))
        vs = [fb.p(-0.032, 0.0, ZG + 0.004), fb.p(0.032, 0.0, ZG + 0.004), fb.p(0.028, 0.012, ZG + 0.004 + h), fb.p(-0.03, 0.012, ZG + 0.004 + h)]
        uv = [(gb[0], gb[1]), (gb[2], gb[1]), (gb[2], gb[3]), (gb[0], gb[3])]
        emit(out, F(vs, "wall6", uv, hint=fb.v(0.0, -1.0, 0.2)))
        emit(out, F(vs, "wall6", uv, hint=fb.v(0.0, 1.0, -0.2)))
    # service bell (chrome dome on a black base)
    frb = WORLD.child(7.34, 0.02, 0.0)
    out += lathe(frb, [(0.0, ZG), (0.040, ZG), (0.040, ZG + 0.012), (0.0, ZG + 0.012)], 16, "rubber")
    out += lathe(frb, [(0.0, ZG + 0.012), (0.036, ZG + 0.014), (0.034, ZG + 0.034), (0.024, ZG + 0.052), (0.010, ZG + 0.060),
                       (0.0, ZG + 0.061)], 16, "steel")
    out += lathe(frb, [(0.0, ZG + 0.061), (0.006, ZG + 0.061), (0.006, ZG + 0.072), (0.0, ZG + 0.073)], 8, "steel")
    # receipt spike with skewered slips (staff side)
    frs = WORLD.child(7.88, 0.06, 0.0)
    out += lathe(frs, [(0.0, ZG), (0.032, ZG), (0.030, ZG + 0.010), (0.0, ZG + 0.012)], 12, "iron")
    out += lathe(frs, [(0.0, ZG + 0.012), (0.0022, ZG + 0.012), (0.0018, ZG + 0.150), (0.0, ZG + 0.158)], 6, "steel")
    for k in range(6):
        fsl = WORLD.child(7.88, 0.06, 0.0, math.radians(37.0 * k + 11.0))
        z = ZG + 0.022 + 0.011 * k
        out += cbox(fsl, -0.040, 0.040, -0.028, 0.028, z, z + 0.0012, "terrazzo", grain="x")
    # folded local weekly (staff reading it between customers)
    frn = WORLD.child(7.58, -0.08, 0.0, math.radians(-70.0))
    out += cbox(frn, -0.150, 0.150, -0.105, 0.105, ZG, ZG + 0.007, "terrazzo", grain="x")
    emit(out, top_quad(frn, -0.150, 0.150, -0.105, 0.105, ZG + 0.0075, w6_uv("news")))
    # interfolded deli sheets in their open carton (moved off the prosciutto stand)
    frd = WORLD.child(7.66, 0.29, 0.0, math.radians(90.0))
    out += cbox(frd, -0.135, 0.135, -0.11, 0.11, ZG, ZG + 0.006, "terrazzo", grain="x")              # carton floor
    for (x0, x1, y0, y1) in ((-0.135, 0.135, -0.11, -0.104), (-0.135, 0.135, 0.104, 0.11), (-0.135, -0.129, -0.104, 0.104),
                             (0.129, 0.135, -0.104, 0.104)):
        out += cbox(frd, x0, x1, y0, y1, ZG, ZG + 0.06, "terrazzo", grain="x")
    out += cbox(frd, -0.125, 0.125, -0.10, 0.10, ZG + 0.006, ZG + 0.048, "terrazzo", grain="x", ch=0.002)
    # food-stamps card in a clear acrylic stand, facing the customers
    frc = Frame((7.05, 0.38, ZG), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))          # x -> -t: reads for -s
    ang = math.radians(76.0)
    w, h = 0.150, 0.075
    p0 = frc.p(-w / 2, 0.0, 0.004)
    up = frc.v(0.0, math.cos(ang), math.sin(ang))
    vs = [p0, frc.p(w / 2, 0.0, 0.004), tuple(frc.p(w / 2, 0.0, 0.004)[k] + up[k] * h for k in range(3)),
          tuple(p0[k] + up[k] * h for k in range(3))]
    u0, v0, u1, v1 = w6_uv("stamps")
    emit(out, F(vs, "wall6", [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=frc.v(0.0, -math.sin(ang), math.cos(ang))))
    out += cbox(frc, -w / 2 - 0.005, w / 2 + 0.005, -0.012, 0.02, 0.0, 0.004, "glass", grain="x")
    return out


def gate_vanilla():
    return [("v_res_foodjarc", 7.87, -0.26, ZG, 25.0)]


# ================================================================== 5. FLOOR: litter, puddles, spill, prints
LITTER = [("ng_proc_paper_01a", 2.38, 0.16, 35.0), ("ng_proc_sodacan_02a", 4.12, 0.20, 110.0), ("v_res_tt_litter1", 0.95, 0.55, 15.0),
          ("ng_proc_paper_03a", -1.62, 2.30, 62.0), ("ng_proc_sodacan_03a", -2.28, 3.48, 200.0), ("ng_proc_paper_01a", -2.18, 2.48, 140.0),
          ("v_res_tt_litter2", 0.55, 3.38, 80.0), ("ng_proc_sodacan_01a", 3.62, 2.72, 0.0), ("ng_proc_paper_01a", -0.20, 6.27, 260.0),
          ("ng_proc_sodacan_02b", 3.78, 6.24, 35.0), ("v_res_tt_litter3", 6.86, 2.02, 95.0), ("ng_proc_paper_03a", -2.64, 4.46, 10.0),
          ("v_res_tt_litter1", 6.88, 5.30, 200.0)]
LEAK_TILE = (3, 7)                                             # existing stained tile (v0.2.3) -> it leaks now


def floor_faces():
    out = []
    fr = mat_frame()[0]
    # rain walked in: puddle just past the mat, wet shoe prints towards the queue
    p = fr.p(0.25, MAT_D + 0.38, 0.0)
    emit(out, floor_quad(p[0], p[1], 0.86, 0.62, 18.0, 0, mat="puddle"))
    for k, (x, y, yaw) in enumerate(((0.55, MAT_D + 0.95, -28.0), (0.86, MAT_D + 1.53, -30.0))):
        q = fr.p(x, y, 0.0)
        emit(out, floor_quad(q[0], q[1], 0.55, 0.55, yaw, PRINTS))
    # the leak: drips from the stained tile into a puddle in the aisle (wet-floor sign beside it)
    sc, tc = (LEAK_TILE[0] + 0.5) * P, (LEAK_TILE[1] + 0.5) * P
    emit(out, floor_quad(sc + 0.05, tc - 0.05, 0.95, 0.72, 24.0, 0, mat="puddle"))
    # sticky soda by the tray station, a small one at the ledge, the mop corner behind P2
    emit(out, floor_quad(-2.12, 2.98, 0.48, 0.40, 30.0, SPILL))
    emit(out, floor_quad(-2.30, 5.40, 0.30, 0.26, -12.0, SPILL))
    emit(out, floor_quad(9.86, 7.78, 0.62, 0.48, 70.0, 0, mat="puddle"))
    return out


def floor_vanilla():
    out = [(n, s, t, FLOOR, yaw) for (n, s, t, yaw) in LITTER]
    fr = mat_frame()[0]
    for (x, y, yaw, nm) in ((-0.62, -0.10, 30.0, "ng_proc_cigbuts01a"), (0.98, 0.25, 115.0, "ng_proc_cigbuts02a"),
                            (-0.95, MAT_D + 0.12, 75.0, "ng_proc_cigbuts01a")):
        q = fr.p(x, y, 0.0)
        out.append((nm, q[0], q[1], FLOOR, yaw))
    sc, tc = (LEAK_TILE[0] + 0.5) * P, (LEAK_TILE[1] + 0.5) * P
    out.append(("v_serv_wetfloorsn", sc + 0.72, tc - 0.42, FLOOR, 205.0))
    return out


# ================================================================== 6. P2 TOP: roof leak + import shelves
SHELVES = [(-2.55, 1.42, 2.62), (2.22, 5.30, 2.70)]          # (s0, s1, board top z); gap at the clock (s 1.60-2.00)
SHELF_D = 0.24


def _tomato_can(out, s, t, z, k):
    fr = WORLD.child(s, t, 0.0, math.radians(37.0 * k))
    r, h = 0.051, 0.118
    out += lathe(fr, [(0.0, z), (r - 0.004, z), (r, z + 0.004), (r, z + 0.008)], 12, "steel")
    out += label_cyl(fr, r + 0.0005, z + 0.008, z + h - 0.008, 12, w6_uv("can_label"))
    out += lathe(fr, [(r, z + h - 0.008), (r, z + h - 0.004), (r - 0.004, z + h), (0.0, z + h)], 12, "steel")
    return h


def _oil_tin(out, s, t, z, key, yaw):
    """5 L square tin: printed front + back panels, plain sides in the label colour, pressed lid + spout."""
    fr = WORLD.child(s, t, 0.0, math.radians(yaw))
    w, d, h = 0.155, 0.105, 0.255
    out += cbox(fr, -w / 2, w / 2, -d / 2, d / 2, z, z + h, "brass" if key == "tin_label" else "iron", ch=0.004, grain="z")
    u0, v0, u1, v1 = w6_uv(key, pad=0.004)
    for sg in (-1.0, 1.0):
        y = sg * (d / 2 + 0.0008)
        vs = [fr.p(-w / 2 + 0.004, y, z + 0.006), fr.p(w / 2 - 0.004, y, z + 0.006), fr.p(w / 2 - 0.004, y, z + h - 0.006),
              fr.p(-w / 2 + 0.004, y, z + h - 0.006)]
        uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)] if sg < 0 else [(u1, v0), (u0, v0), (u0, v1), (u1, v1)]
        emit(out, F(vs, "wall6", uv, hint=fr.v(0.0, sg, 0.0)))
    out += lathe(fr.child(w / 2 - 0.035, 0.0, 0.0), [(0.0, z + h), (0.016, z + h), (0.016, z + h + 0.012), (0.0, z + h + 0.012)],
                 10, "steel")
    return h


def p2_top_faces():
    out = []
    fr, n = wall_frame("P2")
    zw = P2_T[0]
    for (s0, s1, zt) in SHELVES:
        out += cbox(fr, s0, s1, 0.0, SHELF_D, zt - 0.028, zt, "walnut", ch=0.004, grain="x")
        out += cbox(fr, s0, s1, SHELF_D - 0.006, SHELF_D + 0.002, zt - 0.010, zt + 0.032, "steel", grain="x")   # front lip
        nb = max(2, int(round((s1 - s0) / 1.30)) + 1)
        for k in range(nb):
            u = s0 + 0.10 + (s1 - s0 - 0.20) * k / (nb - 1)
            out += cbox(fr, u - 0.012, u + 0.012, 0.0, 0.010, zt - 0.20, zt - 0.028, "steel", grain="z")
            out += cbox(fr, u - 0.012, u + 0.012, 0.0, SHELF_D - 0.02, zt - 0.048, zt - 0.028, "steel", grain="y")
            out += tube(fr, [(u, 0.008, zt - 0.18), (u, SHELF_D - 0.04, zt - 0.048)], 0.006, 6, "steel")
    # shelf A (low, s -2.55..1.42): tomato pyramids and olive-oil tins, a gap where the leak runs
    zt = SHELVES[0][2]
    y = zw - SHELF_D / 2 - 0.005
    for (s, key, yaw) in ((-2.40, "tin_label", 3.0), (-2.22, "tin_label2", -4.0), (-0.20, "tin_label", 0.0),
                          (1.17, "tin_label2", 6.0), (1.33, "tin_label", -2.0)):
        _oil_tin(out, s, y, zt, key, yaw)
    for k, s in enumerate((-1.92, -1.81, -1.70, -1.865, -1.755, -1.81)):
        lvl = 0 if k < 3 else (1 if k < 5 else 2)
        _tomato_can(out, s, y - 0.01 * (k % 2), zt + 0.118 * lvl, k)
    for k, s in enumerate((-1.22, -1.11, -1.00, -0.89)):
        _tomato_can(out, s, y, zt, k + 3)
    for k, s in enumerate((0.93, 1.04)):
        _tomato_can(out, s, y + 0.02, zt, k + 9)
    # shelf B (s 2.22..5.30): older stock — tins + cans (wine + jars are vanilla)
    zt = SHELVES[1][2]
    for (s, key, yaw) in ((3.18, "tin_label2", 2.0), (3.36, "tin_label2", -3.0), (5.20, "tin_label", 4.0)):
        _oil_tin(out, s, y, zt, key, yaw)
    for k, s in enumerate((4.05, 4.16, 4.27, 4.105, 4.215)):
        _tomato_can(out, s, y, zt + (0.118 if k >= 3 else 0.0), k + 20)
    # roof leak: two streaks from the ceiling joint down the paint (behind the shelves), stained tiles above them
    emit(out, d6(fr.p(0.45 - 0.46, 0.0035, 2.36), V.mul(fr.X, 0.92), (0.0, 0.0, CEIL - 2.36 - 0.002), LEAK_WIDE, n))
    emit(out, d6(fr.p(4.92 - 0.20, 0.0035, 2.58), V.mul(fr.X, 0.40), (0.0, 0.0, CEIL - 2.58 - 0.002), LEAK_NARROW, n))
    for (sc, q) in ((0.45, 0.27), (4.90, 0.22)):
        tc = zw - 0.29
        emit(out, K6.decal_quad_v4((sc - q, tc + q, CEIL - 0.003), (2 * q, 0.0, 0.0), (0.0, -2 * q, 0.0), K5.dcell(K5.WATER)))
    return out


def p2_top_vanilla():
    zw = P2_T[0]
    y = zw - SHELF_D / 2 - 0.01
    za, zb = SHELVES[0][2], SHELVES[1][2]
    return [("v_res_foodjara", -1.45, y, za, 0.0), ("v_res_foodjarb", -0.55, y, za, 40.0),
            ("prop_wine_red", 2.40, y, zb, 0.0), ("prop_wine_bot_01", 2.52, y + 0.02, zb, 15.0), ("prop_wine_red", 2.64, y, zb, 70.0),
            ("prop_wine_bot_01", 2.76, y - 0.01, zb, 0.0), ("v_res_foodjarc", 3.70, y, zb, 0.0),
            ("prop_wine_red", 4.55, y, zb, 30.0), ("prop_wine_bot_01", 4.67, y, zb, 0.0)]


# ================================================================== 7. W1 WALL: banner over the windows, CRT TV in the corner
TV_POS = (6.78, -0.70, 2.30)                                  # bottom of the TV, counter-end corner of the SW wall


def w1_wall_faces():
    out = []
    fr, n = wall_frame("SW")
    h = 0.46
    w = h / aspect6("banner")
    uc = wall_u("SW", (PG.W1["s"][0] + PG.W1["s"][1]) / 2, PG.YS)
    z0 = 2.69
    u0, v0, u1, v1 = w6_uv("banner")

    def ban(a, b):
        x = uc - w / 2 + w * a
        sag = 0.012 * math.sin(math.pi * a) * (1.0 - b)          # vinyl hangs between the zip ties
        wave = 0.006 * math.sin(a * math.pi * 6.0) * (0.4 + 0.6 * (1.0 - b))
        return (x, 0.012 + wave, z0 + h * b - sag)
    out += V0.grid(fr, ban, 18, 2, "wall6", lambda a, b: (u0 + (u1 - u0) * a, v0 + (v1 - v0) * b), smooth=True,
                   hint_fn=lambda a, b: (0.0, 1.0, 0.0))
    for a in (0.004, 0.335, 0.665, 0.996):                     # zip ties to screws in the wall
        x, y, z = ban(a, 1.0)
        out += cbox(fr, x - 0.006, x + 0.006, 0.0, y + 0.004, z - 0.022, z - 0.010, "rubber", grain="y")
    # TV: ceiling plate + square tube + cradle (black steel)
    s, t, zb = TV_POS
    frt = WORLD.child(s, t, 0.0)
    out += cbox(frt, -0.07, 0.07, -0.07, 0.07, CEIL - 0.012, CEIL - 0.001, "iron", grain="x", skip=("+z",))
    out += cbox(frt, -0.02, 0.02, -0.02, 0.02, zb + 0.06, CEIL - 0.012, "iron", grain="z")
    frc = WORLD.child(s, t, 0.0, math.radians(TV_YAW))
    out += cbox(frc, -0.31, 0.31, -0.26, 0.21, zb - 0.025, zb - 0.002, "iron", grain="x", ch=0.003)          # platform
    out += cbox(frc, -0.31, 0.31, -0.26, -0.24, zb - 0.002, zb + 0.035, "iron", grain="x")                  # front lip
    for x in (-0.24, 0.24):
        out += tube(frc, [(x, 0.17, zb - 0.02), (0.0, 0.0, zb + 0.07)], 0.009, 6, "iron")
    out += cbox(frc, -0.04, 0.04, -0.04, 0.04, zb - 0.002, zb + 0.08, "iron", grain="z")
    return out


TV_YAW = wall_yaw((-0.79, 0.61))                               # screen towards the booths / hall


def w1_vanilla():
    s, t, zb = TV_POS
    return [("prop_tv_01", s, t, zb, TV_YAW)]


# ================================================================== 8. NW PIER: tray return / trash receptacle
ST = dict(s=(PG.XW, PG.XW + 0.46), t=(2.66, 3.26), z=1.06)


def station_faces():
    out = []
    (s0, s1), (t0, t1), zt = ST["s"], ST["t"], ST["z"]
    fr = Frame((s1, t0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))   # x along t, y = out into the hall (+s)
    W, D = t1 - t0, s1 - s0
    # body (red laminate) with its front face at y = -0.012, black rubber kick plate
    out += cbox(WORLD, s0, s1 - 0.012, t0, t1, FLOOR, zt, "walnut", grain="z", skip=("-x",))
    out += cbox(fr, 0.0, W, -0.012, -0.008, FLOOR, FLOOR + 0.10, "rubber", grain="x")
    # door below the flap (staff empties the bin here): panel + pull
    out += cbox(fr, 0.03, W - 0.03, -0.012, -0.002, FLOOR + 0.12, 0.52, "walnut", ch=0.003, grain="x")
    out += cbox(fr, W / 2 - 0.06, W / 2 + 0.06, -0.002, 0.014, 0.47, 0.485, "steel", grain="x")
    # push flap: brushed panel with "THANK YOU" + the swing-door slot, recessed in a steel frame
    fw, z0, z1 = 0.44, 0.56, 1.00
    xa, xb = (W - fw) / 2, (W + fw) / 2
    for (a0, a1, b0, b1) in ((xa - 0.025, xb + 0.025, z0 - 0.025, z0), (xa - 0.025, xb + 0.025, z1, z1 + 0.025),
                             (xa - 0.025, xa, z0, z1), (xb, xb + 0.025, z0, z1)):
        out += cbox(fr, a0, a1, -0.012, 0.0, b0, b1, "steel", ch=0.002, grain="x")
    u0, v0, u1, v1 = w6_uv("flap")
    vs = [fr.p(xa, -0.006, z0), fr.p(xb, -0.006, z0), fr.p(xb, -0.006, z1), fr.p(xa, -0.006, z1)]
    emit(out, F(vs, "wall6", [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=fr.v(0.0, 1.0, 0.0)))
    # tray top: laminate with dirt + rings, steel edge band, 3 cm overhang to the hall
    frt = Frame((s0, t0 - 0.02, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    out += cbox(frt, 0.0, D + 0.03, 0.0, W + 0.04, zt, zt + 0.028, "walnut", grain="x", skip=("+z",))
    emit(out, top_quad(frt, 0.0, D + 0.03, 0.0, W + 0.04, zt + 0.0285, w6_uv("station_top"), rot=True))
    out += cbox(frt, D + 0.03, D + 0.036, 0.0, W + 0.04, zt - 0.002, zt + 0.031, "steel", grain="y")
    # worn edge + hand grime decals on the flap frame
    emit(out, d5(fr.p(xa + 0.05, -0.0052, z0 + 0.12), fr.v(fw - 0.10, 0.0, 0.0), (0.0, 0.0, 0.22), K6.HAND_RUB, fr.v(0.0, 1.0, 0.0)))
    return out


def station_vanilla():
    (s0, s1), (t0, t1), zt = ST["s"], ST["t"], ST["z"]
    zt += 0.0285
    sc, tc = (s0 + s1) / 2 + 0.01, (t0 + t1) / 2
    out = []
    for k in range(3):                                         # clean tray stack, long side along the wall
        out.append(("prop_food_tray_01", sc, tc + 0.02, zt + 0.0215 * k, 90.0 + (k % 2) * 3.0))
    out.append(("prop_food_tray_03", sc + 0.02, tc - 0.03, zt + 0.0215 * 3, 84.0))    # dirty one dumped on top
    return out


def station_collision():
    (s0, s1), (t0, t1), zt = ST["s"], ST["t"], ST["z"]
    return [((s0, s1 + 0.03, t0 - 0.02, t1 + 0.02, FLOOR, zt + 0.03), "WOOD_SOLID_MEDIUM")]


def nw_pier_faces():
    """v0.2.6 tin sign kept; the restroom note moves to the corner (the station covers its old spot)."""
    out = []
    out += K6.story("NW", PG.XW, 2.98, 1.52, 0.50, "tin_sign", d=0.0, board=0.008)
    out += K6.story("NW", PG.XW, 2.585, 1.30, 0.15, "note", d=0.003)
    fr, n = wall_frame("NW")
    emit(out, K6.wall_decal(fr, 2.92, 0.004, 1.24, 0.34, 0.20, K6.STICKER, n))
    return out


# ================================================================== 9. SERVICE (v0.2.6 minus the duplicates)
def service_faces():
    out = []
    zc = 1.02
    for (s, t) in ((7.80, 5.38), (7.80, 5.48)):
        fr = WORLD.child(s, t, 0.0)
        out += lathe(fr, [(0.0, zc + 0.072), (0.038, zc + 0.072), (0.040, zc + 0.068), (0.040, zc + 0.004), (0.038, zc), (0.0, zc)][::-1],
                     14, "terrazzo")
    fr = WORLD.child(7.30, 4.80, 0.0)
    out += lathe(fr, [(0.0, zc + 0.002), (0.055, zc + 0.002), (0.065, zc + 0.016), (0.069, zc + 0.017), (0.060, zc + 0.003),
                      (0.0, zc + 0.0005)][::-1], 18, "steel")
    s0, s1, t0, t1, hz = 8.08, 8.86, 4.52, 5.70, 0.012
    out += cbox(WORLD, s0 + 0.02, s1 - 0.02, t0 + 0.02, t1 - 0.02, FLOOR, FLOOR + hz, "rubber", grain="x", skip=("-z",))
    for (a0, a1, b0, b1, hn) in ((s0, s0 + 0.02, t0, t1, (-1, 0, 1)), (s1 - 0.02, s1, t0, t1, (1, 0, 1)),
                                 (s0 + 0.02, s1 - 0.02, t0, t0 + 0.02, (0, -1, 1)), (s0 + 0.02, s1 - 0.02, t1 - 0.02, t1, (0, 1, 1))):
        hi = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
        vs = [(x, y, FLOOR + (hz if (abs(x - s0) > 0.019 and abs(x - s1) > 0.019 and abs(y - t0) > 0.019 and abs(y - t1) > 0.019) else 0.002))
              for (x, y) in hi]
        emit(out, F(vs, "rubber", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=hn))
    zb = 0.92                                                  # tongs: clear of the prosciutto stand (t 3.45)
    for k, dt in enumerate((-0.012, 0.012)):
        out += cbox(WORLD, 9.36, 9.60, 4.90 + dt - 0.006, 4.90 + dt + 0.006, zb + 0.004 + 0.006 * k, zb + 0.008 + 0.006 * k, "steel", grain="x")
    for (s, t, q, cell) in ((8.45, 5.95, 0.40, GREASE), (8.40, 1.25, 0.35, GREASE), (6.45, 2.60, 0.55, MOP), (6.40, 4.45, 0.55, MOP)):
        emit(out, d5((s - q, t - q, FLOOR + 0.0028), (2 * q, 0.0, 0.0), (0.0, 2 * q, 0.0), cell, (0.0, 0.0, 1.0)))
    for (s, t) in ((BANQ_TABLES[1], BANQ_T), (3.425, -0.62)):
        emit(out, d5((s - 0.14, t - 0.14, ZT + 0.0012), (0.28, 0.0, 0.0), (0.0, 0.28, 0.0), CUP_RINGS, (0.0, 0.0, 1.0)))
    return out


# ================================================================== 10. CEILING: v0.2.6 system, shorter wall-top grime band
def ceiling_faces27():
    faces, _ = K6.ceiling_system()
    out = []
    for f in faces:
        if f is None:
            continue
        if f["mat"] == MAT["decal5"]:
            zs = [p[2] for p in f["v"]]
            if min(zs) > CEIL - 0.36 and max(zs) - min(zs) > 0.3:        # the wall-top grime band: 0.335 -> 0.20 m
                lo = min(zs)
                f = dict(f, v=[(x, y, (CEIL - 0.205) if abs(z - lo) < 1e-4 else z) for (x, y, z) in f["v"]])
        out.append(f)
    return out


# ================================================================== assemble
def hall_faces():
    out = []
    out += K3.wall_kit_faces()
    out += K3.ceiling_faces()
    out += ceiling_faces27()
    for (s, t, kind) in K3.CANS:
        out += V0.recessed_can(s, t, CEIL)
    for t in (1.05, 2.05, 3.20, 4.20, 5.10, 6.15):
        out += V0.recessed_can(7.55, t, K3.SOFFIT["z"])
    out += K3.menu_boards()
    out += K6.seating_faces()
    out += K3.ledge_faces()
    out += V.counters_faces()
    out += entry_mat27()
    for sc, tc in CTABLES:
        out += K3.table2(sc, tc, size=K5.CT_SIZE)
    out += K5.p1_wall_faces()
    out += K6.p2_story_faces()
    out += sw_wall_faces()
    out += nw_pier_faces()
    out += K6.entrance_faces()
    out += K5.counter_faces()
    out += K6.blinds_faces()
    out += service_faces()
    out += decal_faces()
    out += gate_faces()
    out += floor_faces()
    out += p2_top_faces()
    out += w1_wall_faces()
    out += station_faces()
    return [f for f in out if f is not None]


REMOVED = dict(K6.REMOVED)
REMOVED.update({"no_loiter (notice)": "v0.2.7 owner: replaced by the COLD CUTS thermometer sign",
                "butcher roll v0.2.6": "duplicate of the v0.2.1 paper roll at the same back-counter spot"})


def vanilla_props():
    out = K6.vanilla_props()
    out += gate_vanilla() + floor_vanilla() + p2_top_vanilla() + w1_vanilla() + station_vanilla()
    return out


def vanilla_entities():
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        mn = VB[name][0]
        out.append((name, (round(s, 4), round(t, 4), round(zb - mn[2], 4)), math.radians(yaw)))
    return out


def collision_boxes():
    return K6.collision_boxes() + station_collision()


SEATS = dict(K6.SEATS)
EXTERIOR = list(K6.EXTERIOR)
