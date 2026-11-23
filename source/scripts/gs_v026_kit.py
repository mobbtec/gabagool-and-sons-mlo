# LONG PIG — v0.2.6 FINISH-AND-REFINE pass over v0.2.5 (owner brief LONG_PIG_V026_MASTER_STYLE_LIGHTING_PRODUCTION_BRIEF,
# 2026-11-01: "preserve first, improve second, replace only when justified"). Everything not listed here is the v0.2.5 kit.
#   REMOVE   hanging enamel dome pendants (booths + queue) and the two opal globes; the small tricolore on P2; every
#            black-and-white "mugshot" portrait (prop_ped_pic_*).
#   CEILING  same T-bar grid and acoustic tile (aged, no baked repeat): 15 recessed 2x4 / 1x2 prismatic troffers in a planned
#            rhythm (5 new ones replace the pendants), each with its OWN engine light (hue / strength per lamp age),
#            2 supply diffusers + 1 return grille with soot halos, 3 replaced tiles, stains, wall-top grime.
#            2 ordinary ceiling fans (vanilla prop_outdoor_fan_01) spawned + rotated client-side (client/fans.lua).
#   DAYLIGHT day-only soft fills behind the W1 / W2 glass (time flags 07-19), no fake sun streaks at night.
#   BLINDS   ORIGINAL vertical PVC blinds in the W1 / W2 reveals: individual slats, mixed angles, one pane stacked open.
#   WALLS    P2 big wall: supplier poster, family photos (renders of our own room), sponsor plaque, frame ghosts, anchors,
#            sticker residue, paint patches, chipped tiles, service notices; NW pier: soda tin sign + restroom note.
#   SEATING  same booths / banquettes, refined vinyl: sitting dips, flatter worn channels, welt seam, per-booth UV, wear.
#   SERVICE  receipt rolls, change dish, pen + pad at the till, staff mat, butcher-paper roll, deli sheets, tongs;
#            cleaning corner just inside the back room (mop bucket, wet-floor sign, broom).
#   FLOOR    A (default) = same checker, aged further, 4 m repeat; B (gray-beige quarry tile) only as an optional runtime
#            comparison (/gs_floor b), never baked.
import math
import gs_v021_kit as V0
import gs_v023_kit as K3
import gs_v024_kit as K4
import gs_v025_kit as K5
from gs_v025_kit import *                    # noqa: F401,F403
from gs_v025_kit import (V, PG, SG, WORLD, Frame, F, emit, cbox, prism, lathe, tube, FLOOR, CEIL, LT, CORONA, C_TUNGSTEN,
                         FILL_FLAGS, wall_yaw, VB, P, P1_S, P2_T, BACK_S, COUNTER_FRONT, BANQ, BANQ_TABLES, BANQ_T, ZT,
                         wall_frame, wall_u, notice, notice_uv, PIER_A, PIER_B, CTABLES, dcell, FLOOR_WEAR, SCUFFS,
                         GRIME, TRAFFIC, DRIPS, SCUFF, WATER, PATCH, GHOST, TAPE, _pbr)
from gs_v026_vb import VB_V026

VB.update(VB_V026)
V.MAT.update({"blind": 21, "decal5": 22, "wall5": 23})
V.REP.update({"blind": 1.0, "decal5": 1.0, "wall5": 1.0})
MAT = V.MAT
PG.FLOOR_UV_M = 4.0                          # floor A texture now covers 4 m (12 x 12 tiles): no visible 2 m repeat
VERSION = "0.2.6-refine"


def retex(spec, **swap):
    sh, samp, par, nm = spec
    return (sh, {k: swap.get(v, v) for k, v in samp.items()}, par, nm)


SHADER_SPECS = list(K5.SHADER_SPECS)
SHADER_SPECS[1] = retex(SHADER_SPECS[1], lp2_leather_n="lp5_leather_n")                       # memory: 1024 -> 512
SHADER_SPECS[8] = retex(SHADER_SPECS[8], lp2_food_s="lp5_food_s")                             # memory: 1024 -> 512
SHADER_SPECS[10] = _pbr("lp5_slot10_unused", "lp_brass", "lp_flat_n", "lp_matte_s", 8.0, 0.1)  # flag removed: tiny maps
SHADER_SPECS[12] = retex(SHADER_SPECS[12], lp_wall_plaster="lp5_plaster", lp_wall_plaster_n="lp5_plaster_n",
                         lp_wall_plaster_s="lp5_plaster_s")                                     # soffit underside only
SHADER_SPECS[17] = ("emissive.sps", {"DiffuseSampler": "lp5_troffer"}, {"emissiveMultiplier": 2.0}, "lp5_troffer")
SHADER_SPECS += [_pbr("lp5_blind", "lp5_blind", "lp_flat_n", "lp_matte_s", 12.0, 0.25),           # 21 PVC slats
                 ("decal.sps", {"DiffuseSampler": "lp5_decal"}, {}, "lp5_decal"),                # 22 history / wear decals
                 _pbr("lp5_wall", "lp5_wall", "lp_flat_n", "lp_matte_s", 8.0, 0.12)]             # 23 wall story atlas
assert len(SHADER_SPECS) == len(MAT)
SHELL_TEX = dict(K5.SHELL_TEX)
SHELL_TEX["floor"] = ("lp5_floor_bw", "lp5_floor_n", "lp5_floor_s", 40.0, 0.55)
SHELL_TEX["ceil"] = ("lp5_ceiling_tile", "lp3_ceiling_tile_n", "lp_ceiling_tile_s", 6.0, 0.3)
FLOOR_B = {"diffuse": ("lp5_floor_bw", "textures/lp5_floor_b.png"), "normal": ("lp5_floor_n", "textures/lp5_floor_b_n.png")}

# ================================================================== camera list for the owner's review (brief §18)
CAM_VIEWS = dict(K5.CAM_VIEWS)
CAM_VIEWS.update({
    "GS26_HALL": ((-1.2, 1.4, 1.65), (6.2, 2.2, 1.45), "Hero 01/02/15: hall from the entrance (12 / 23 h)"),
    "GS26_BLINDS": ((3.45, 2.3, 1.55), (3.45, -1.3, 1.45), "Hero 03: storefront W1 blinds from inside"),
    "GS26_BLINDS_OUT": ((3.46, -6.8, 1.65), (3.46, -1.3, 1.45), "Hero 04: storefront W1 from the street"),
    "GS26_CEILING": ((2.3, 1.6, 1.55), (2.3, 3.4, 3.35), "Hero 05: ceiling overview, troffers + fans"),
    "GS26_FIXTURE": ((1.9, 1.2, 2.25), (1.95, 2.9, 3.3), "Hero 06: troffer close-up + wall response"),
    "GS26_WALL": ((1.7, 3.0, 1.6), (1.7, 6.94, 1.62), "Hero 07: P2 big wall"),
    "GS26_FLOOR": ((5.4, 0.9, 0.42), (2.0, 2.3, 0.0), "Hero 08: floor at a low angle"),
    "GS26_BOOTH": ((2.55, 0.45, 1.05), (1.55, -0.75, 0.50), "Hero 09: booth vinyl macro"),
    "GS26_COUNTER": ((5.5, 3.7, 1.65), (7.6, 4.9, 1.10), "Hero 10: till from the customer side"),
    "GS26_STAFF": ((8.6, 0.0, 1.65), (8.7, 6.2, 1.0), "Hero 11: behind the counter"),
    "GS26_ENTRY": ((0.9, 2.6, 1.45), (-1.3, 0.5, 0.15), "Hero 12: entrance threshold and mat"),
    "GS26_GUM": ((-6.4, 6.0, 1.45), (-3.15, 7.15, 0.65), "Hero 13: gumball machines outside (NW facade)"),
    "GS26_REAR": ((8.05, 6.0, 1.62), (9.75, 7.6, 0.40), "Hero 14: staff path, P2 door, cleaning corner"),
})

# ================================================================== 1. CEILING SYSTEM
# (i, j, n_s, n_t, lamp) on the P grid; lamp: 0 cool, 1 aged warm, 2 weak (tube out), 3 dirty lens
TROFFERS = [(0, 1, 2, 1, 0), (4, 1, 2, 1, 1), (8, 1, 2, 1, 0),
            (-2, 4, 2, 1, 0), (2, 4, 2, 1, 0), (6, 4, 2, 1, 2),
            (0, 6, 2, 1, 1), (4, 6, 2, 1, 0),
            (13, 2, 2, 1, 3), (13, 6, 2, 1, 1),
            (2, -1, 2, 1, 0), (5, -1, 2, 1, 3), (8, -1, 2, 1, 0),         # NEW booth row (replaces 3 hanging domes)
            (9, 3, 1, 2, 0), (9, 6, 1, 2, 1)]                             # NEW queue pair (replaces 2 hanging domes)
SHADOW_TROFFERS = {(2, -1), (5, -1), (8, -1), (9, 3), (9, 6)}
LAMP = {0: ((0.93, 0.97, 1.00), 1.00), 1: ((1.00, 0.93, 0.82), 0.92), 2: ((0.92, 0.97, 0.93), 0.45), 3: ((0.93, 0.97, 1.00), 0.85)}
SUPPLY = [(1, 7), (6, 7)]                     # 4-way square diffusers
RETURN = [(6, 1)]                             # return-air bar grille
NEW_TILES = [(-1, 5), (7, 5), (4, 8)]         # whiter replacement tiles
WATER_TILES = [(3, 7), (-2, 2)]               # tide-ring stains (the v0.2.5 (9,3) stain sat where the queue troffer is now)
SMALL_STAINS = [(1, 7, 0.38, 0.30), (6, 7, -0.36, 0.33)]
FANS = [((1.5 * P), (4.5 * P)), ((5.5 * P), (4.5 * P))]                 # tile centres over the two centre tables
FAN_MODEL = "prop_outdoor_fan_01"
SPRINKLER_MOVE = {(9, 6): (9, 9)}             # vanilla sprinkler that would sit inside the new queue troffer


def troffer_cells():
    occ = {}
    for (i, j, ns, nt, lamp) in TROFFERS:
        for a in range(i, i + ns):
            for b in range(j, j + nt):
                occ[(a, b)] = "troffer"
    return occ


def _check_ceiling():
    occ = troffer_cells()
    for kind, cells in (("supply", SUPPLY), ("return", RETURN), ("new_tile", NEW_TILES), ("stain", WATER_TILES)):
        for c in cells:
            assert c not in occ, (kind, c, occ.get(c))
            occ[c] = kind
    spr = [(-3, 6), (-1, 3), (1, 0), (3, 3), (5, 0), (7, 3), (1, 8), (5, 8), (9, 6)]
    for c in spr:
        c = SPRINKLER_MOVE.get(c, c)
        assert occ.get(c) in (None, "new_tile"), ("sprinkler", c, occ.get(c))
    for c in ((-1, 7), (6, 2)):
        assert c not in occ, ("smoke", c)


_check_ceiling()


def lamp_uv(lamp):
    u0, v1 = (lamp % 2) * 0.5, 1.0 - (lamp // 2) * 0.5
    return u0 + 0.004, v1 - 0.5 + 0.008, u0 + 0.5 - 0.004, v1 - 0.008


def troffer26(i, j, ns, nt, lamp):
    """Recessed prismatic troffer: 4 cm enamel flange 2.8 cm below the tile, sloped white reflector returns, lens recessed."""
    out = []
    s0, s1, t0, t1 = i * P, (i + ns) * P, j * P, (j + nt) * P
    b, zf, zl, ins = 0.040, CEIL - 0.028, CEIL - 0.009, 0.014
    out += cbox(WORLD, s0, s1, t0, t0 + b, zf, CEIL - 0.0005, "enamel", grain="x", skip=("+z",))
    out += cbox(WORLD, s0, s1, t1 - b, t1, zf, CEIL - 0.0005, "enamel", grain="x", skip=("+z",))
    out += cbox(WORLD, s0, s0 + b, t0 + b, t1 - b, zf, CEIL - 0.0005, "enamel", grain="y", skip=("+z",), caps=(False, False))
    out += cbox(WORLD, s1 - b, s1, t0 + b, t1 - b, zf, CEIL - 0.0005, "enamel", grain="y", skip=("+z",), caps=(False, False))
    a0, a1, c0, c1 = s0 + b, s1 - b, t0 + b, t1 - b
    for (p, q, hint) in ((((a0, c0), (a0, c1)), ((a0 + ins, c0 + ins), (a0 + ins, c1 - ins)), (1.0, 0.0, -0.6)),
                         (((a1, c1), (a1, c0)), ((a1 - ins, c1 - ins), (a1 - ins, c0 + ins)), (-1.0, 0.0, -0.6)),
                         (((a1, c0), (a0, c0)), ((a1 - ins, c0 + ins), (a0 + ins, c0 + ins)), (0.0, 1.0, -0.6)),
                         (((a0, c1), (a1, c1)), ((a0 + ins, c1 - ins), (a1 - ins, c1 - ins)), (0.0, -1.0, -0.6))):
        vs = [(p[0][0], p[0][1], zf), (p[1][0], p[1][1], zf), (q[1][0], q[1][1], zl), (q[0][0], q[0][1], zl)]
        emit(out, F(vs, "enamel", [(0, 0), (1, 0), (1, 0.05), (0, 0.05)], hint=hint))
    u0, v0, u1, v1 = lamp_uv(lamp)
    l0, l1, m0, m1 = a0 + ins, a1 - ins, c0 + ins, c1 - ins
    vs = [(l0, m0, zl), (l1, m0, zl), (l1, m1, zl), (l0, m1, zl)]
    uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)] if ns >= nt else [(u0, v1), (u0, v0), (u1, v0), (u1, v1)]
    emit(out, F(vs, "troffer", uv, hint=(0.0, 0.0, -1.0)))
    for k in (0.3, 0.7):                                                    # lens latches on the long sides
        if ns >= nt:
            x = s0 + (s1 - s0) * k
            out += cbox(WORLD, x - 0.015, x + 0.015, c0 - 0.004, c0 + 0.006, zf - 0.004, zf, "steel", grain="x", skip=("+z",))
        else:
            y = t0 + (t1 - t0) * k
            out += cbox(WORLD, a0 - 0.004, a0 + 0.006, y - 0.015, y + 0.015, zf - 0.004, zf, "steel", grain="y", skip=("+z",))
    return out, ((s0 + s1) / 2, (t0 + t1) / 2)


def supply_diffuser(i, j):
    """4-way square ceiling diffuser in one tile: flange + 3 stepped cones + centre plate, dark plenum behind."""
    out = []
    s0, s1, t0, t1 = i * P + 0.022, (i + 1) * P - 0.022, j * P + 0.022, (j + 1) * P - 0.022
    cs, ct = (s0 + s1) / 2, (t0 + t1) / 2
    vs = [(s0, t0, CEIL - 0.003), (s1, t0, CEIL - 0.003), (s1, t1, CEIL - 0.003), (s0, t1, CEIL - 0.003)]
    emit(out, F(vs, "rubber", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(0.0, 0.0, -1.0)))
    h = (s1 - s0) / 2
    for k, (r0, r1, z) in enumerate(((h, h - 0.045, CEIL - 0.010), (h - 0.060, h - 0.095, CEIL - 0.024),
                                     (h - 0.110, h - 0.145, CEIL - 0.038), (h - 0.160, 0.0, CEIL - 0.052))):
        if r1 <= 0.0:
            out += cbox(WORLD, cs - r0, cs + r0, ct - r0, ct + r0, z, z + 0.008, "enamel", grain="x", skip=("+z",))
            continue
        for (x0, x1, y0, y1) in ((cs - r0, cs + r0, ct - r0, ct - r1), (cs - r0, cs + r0, ct + r1, ct + r0),
                                 (cs - r0, cs - r1, ct - r1, ct + r1), (cs + r1, cs + r0, ct - r1, ct + r1)):
            out += cbox(WORLD, x0, x1, y0, y1, z, CEIL - 0.004 if k == 0 else z + 0.010, "enamel", grain="x",
                        skip=("+z",), caps=None)
    return out


def return_grille(i, j):
    """Return-air bar grille in one tile: frame + 11 bars over a dark plenum."""
    out = []
    s0, s1, t0, t1 = i * P + 0.022, (i + 1) * P - 0.022, j * P + 0.022, (j + 1) * P - 0.022
    vs = [(s0, t0, CEIL - 0.003), (s1, t0, CEIL - 0.003), (s1, t1, CEIL - 0.003), (s0, t1, CEIL - 0.003)]
    emit(out, F(vs, "rubber", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(0.0, 0.0, -1.0)))
    f = 0.035
    for (x0, x1, y0, y1) in ((s0, s1, t0, t0 + f), (s0, s1, t1 - f, t1), (s0, s0 + f, t0 + f, t1 - f), (s1 - f, s1, t0 + f, t1 - f)):
        out += cbox(WORLD, x0, x1, y0, y1, CEIL - 0.016, CEIL - 0.004, "enamel", grain="x", skip=("+z",))
    n = 11
    for k in range(n):
        y = t0 + f + (t1 - t0 - 2 * f) * (k + 0.5) / n
        out += cbox(WORLD, s0 + f, s1 - f, y - 0.006, y + 0.006, CEIL - 0.030, CEIL - 0.004, "enamel", grain="x", skip=("+z",),
                    caps=(False, False))
    return out


def dcell5(i):
    cx, cy = i % 4, i // 4
    return (cx / 4.0 + 0.002, 1.0 - (cy + 1) / 4.0 + 0.002, (cx + 1) / 4.0 - 0.002, 1.0 - cy / 4.0 - 0.002)


VENT_HALO, NEW_TILE, TOP_GRIME, STICKER, FRAME_GHOST, ANCHORS, HAND_RUB, VINYL_WEAR, TILE_CHIP, PAINT_PATCH, MOP, \
    SCUFF_BAND, GREASE, STAIN_SMALL, GRIT, CUP_RINGS = range(16)


def d5(p0, du, dv, cell, hint):
    """Decal quad (lp5_decal) p0 + a du + b dv with an explicit facing direction."""
    u0, v0, u1, v1 = dcell5(cell)
    vs = [p0, tuple(p0[k] + du[k] for k in range(3)), tuple(p0[k] + du[k] + dv[k] for k in range(3)), tuple(p0[k] + dv[k] for k in range(3))]
    return F(vs, "decal5", [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=hint)


def ceil_decal(sc, tc, q, cell, z=CEIL - 0.0025):
    return d5((sc - q, tc + q, z), (2 * q, 0.0, 0.0), (0.0, -2 * q, 0.0), cell, (0.0, 0.0, -1.0))


def wall_decal(fr, u, y, z0, w, h, cell, n):
    return d5(fr.p(u - w / 2, y, z0), V.mul(fr.X, w), (0.0, 0.0, h), cell, n)


def ceiling_system():
    """-> faces, lights"""
    out, L = [], []
    for (i, j, ns, nt, lamp) in TROFFERS:
        f, (sc, tc) = troffer26(i, j, ns, nt, lamp)
        out += f
        c, g = LAMP[lamp]
        flags = ("static_shadows", "not_in_reflection") if (i, j) in SHADOW_TROFFERS else ("not_in_reflection",)
        L.append(LT(f"troffer_lamp{lamp}", "SPOT", (sc, tc, CEIL - 0.05), c, round(3.4 * g, 2), 5.2, 4.0, cone=(78.0, 46.0),
                    flags=flags))
    for (i, j) in SUPPLY:
        out += supply_diffuser(i, j)
        emit(out, ceil_decal((i + 0.5) * P, (j + 0.5) * P, 0.46, VENT_HALO))
    for (i, j) in RETURN:
        out += return_grille(i, j)
        emit(out, ceil_decal((i + 0.5) * P, (j + 0.5) * P, 0.44, VENT_HALO))
    for (i, j) in NEW_TILES:
        q = P / 2 - 0.013
        emit(out, ceil_decal((i + 0.5) * P, (j + 0.5) * P, q, NEW_TILE, z=CEIL - 0.0015))
    for (i, j, ds, dt) in SMALL_STAINS:
        emit(out, ceil_decal((i + 0.5) * P + ds, (j + 0.5) * P + dt, 0.13, STAIN_SMALL))
    for (i, j) in WATER_TILES:
        sc, tc = (i + 0.5) * P, (j + 0.5) * P
        emit(out, decal_quad_v4((sc - 0.27, tc + 0.27, CEIL - 0.003), (0.54, 0.0, 0.0), (0.0, -0.54, 0.0), dcell(WATER)))
    # dust / soot along every wall-ceiling joint (the ceiling is a designed environment, not one repeated material)
    for fr, runs, _ in V.wall_runs():
        u_lo, u_hi = min(a for a, b, k in runs), max(b for a, b, k in runs)
        u = u_lo + 0.05
        while u < u_hi - 0.2:
            Lr = min(1.7, u_hi - u - 0.05)
            emit(out, d5(fr.p(u, 0.004, CEIL - 0.34), V.mul(fr.X, Lr), (0.0, 0.0, 0.335), TOP_GRIME, fr.Y))
            u += Lr + 0.35
    return out, L


def decal_quad_v4(p0, du, dv, cell):
    return K3.decal_quad(p0, du, dv, cell)


# ================================================================== 2. LIGHTS (one system: fixtures <-> engine lights)
DAY_HOURS = sum(1 << h for h in range(7, 20))
W1_PANES = [(1.332, 2.637), (2.79, 4.131), (4.27, 5.575)]
W2_PANES = [(3.534, 4.84), (4.979, 6.319)]
DROP_KINDS = ("troffer", "booth_pendant_key", "booth_bulb", "queue_pendant_key", "queue_bulb", "centre_globe_key", "centre_globe")


def lights():
    L = []
    for l in K5.lights():
        if l["kind"] in DROP_KINDS:
            continue
        if l["kind"] == "banquette_key":                       # recessed cans stay, a touch softer under the new troffers
            l = dict(l, intensity=4.6)
        L.append(l)
    L += ceiling_system()[1]
    for a, b in W1_PANES:                                      # daylight behind the storefront glass, day only
        l = LT("window_day_fill", "SPOT", ((a + b) / 2, PG.YS - 0.13, 2.42), (1.0, 0.97, 0.92), 1.5, 6.5, 2.0,
               aim=(0.0, 0.78, -0.62), cone=(80.0, 42.0), flags=("no_specular", "not_in_reflection", "dont_light_alpha"))
        l["time"] = DAY_HOURS
        L.append(l)
    for a, b in W2_PANES:
        l = LT("window_day_fill", "SPOT", (PG.XW - 0.11, (a + b) / 2, 2.42), (1.0, 0.97, 0.92), 1.2, 6.0, 2.0,
               aim=(0.78, 0.0, -0.62), cone=(80.0, 42.0), flags=("no_specular", "not_in_reflection", "dont_light_alpha"))
        l["time"] = DAY_HOURS
        L.append(l)
    return L


# ================================================================== 3. VERTICAL BLINDS (original, W1 + W2 reveals)
SLAT_W, SLAT_PITCH = 0.089, 0.080
W1_D, W2_D = -0.085, -0.072            # hang line, metres from the interior wall face (negative = into the reveal)


def _slat(out, fr, u, d0, z0, z1, ang, ci, tilt=0.0):
    ca, sa = math.cos(ang), math.sin(ang)
    cs = [(-SLAT_W / 2 + SLAT_W * k / 3, 0.004 * (1 - (2 * k / 3 - 1) ** 2)) for k in range(4)]
    pts = [(u + a * ca - b * sa, d0 + a * sa + b * ca) for a, b in cs]
    nrm = fr.v(-sa, ca, 0.0)
    cu0 = ci * 0.25 + 0.01
    for k in range(3):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        ua, ub = cu0 + 0.23 * k / 3, cu0 + 0.23 * (k + 1) / 3
        vs = [fr.p(x0 + tilt, y0, z0), fr.p(x1 + tilt, y1, z0), fr.p(x1, y1, z1), fr.p(x0, y0, z1)]
        uv = [(ua, 0.0), (ub, 0.0), (ub, 1.0), (ua, 1.0)]
        emit(out, F(vs, "blind", uv, hint=nrm))
        emit(out, F(vs, "blind", uv, hint=V.mul(nrm, -1.0)))
    return ((pts[0][0] + pts[3][0]) / 2 + tilt, (pts[0][1] + pts[3][1]) / 2)


def blind_pane(fr, a, b, d0, pattern, seed):
    """One blind in the reveal between wall coordinates a < b. pattern: ('open', deg, jitter) | ('stacked', side)."""
    import random
    rnd = random.Random(seed)
    out = []
    zt, z0, z1 = 2.572, 0.655, 2.515
    out += cbox(fr, a + 0.006, b - 0.006, d0 - 0.022, d0 + 0.022, zt - 0.042, zt, "steel", ch=0.003, grain="x")   # headrail
    n = int((b - a - 0.03) / SLAT_PITCH)
    us = []
    if pattern[0] == "stacked":
        side = pattern[1]
        for k in range(n):
            us.append((b - 0.05 - k * 0.019) if side > 0 else (a + 0.05 + k * 0.019))
    else:
        u0 = a + (b - a - (n - 1) * SLAT_PITCH) / 2
        us = [u0 + k * SLAT_PITCH for k in range(n)]
    bottoms = []
    missing = rnd.randrange(2, n - 2) if pattern[0] == "open" and len(pattern) > 3 and pattern[3] else -1
    crooked = rnd.randrange(1, n - 1) if pattern[0] == "open" else -1
    stained = rnd.randrange(0, n)
    for k, u in enumerate(us):
        if k == missing:
            continue
        if pattern[0] == "stacked":
            ang = math.radians(rnd.uniform(84.0, 92.0))
        else:
            ang = math.radians(pattern[1] + rnd.uniform(-pattern[2], pattern[2]))
            if rnd.random() < 0.08:
                ang += math.radians(rnd.choice((-25.0, 22.0)))      # someone twisted one slat to look out
        r = rnd.random()
        ci = 2 if k == stained else (3 if r < 0.07 else (1 if r < (0.30 + pattern[-1] if isinstance(pattern[-1], float) else 0.30) else 0))
        zb = z0 + rnd.uniform(-0.006, 0.012) + (0.03 if ci == 3 else 0.0)        # replacement slat cut a bit short
        tilt = 0.035 if k == crooked else 0.0
        bottoms.append(_slat(out, fr, u, d0, zb, z1, ang, ci, tilt) + (zb + 0.012,))
    for k in range(len(bottoms) - 1):                                                # bead chain linking the slat bottoms
        (x0, y0, za), (x1, y1, zb_) = bottoms[k], bottoms[k + 1]
        out += tube(fr, [(x0, y0, za), ((x0 + x1) / 2, (y0 + y1) / 2, min(za, zb_) - 0.004), (x1, y1, zb_)], 0.0016, 4, "steel")
    ue = b - 0.025
    out += tube(fr, [(ue, d0 + 0.026, zt - 0.04), (ue, d0 + 0.026, 1.32)], 0.0018, 4, "steel")       # control chain loop
    out += tube(fr, [(ue - 0.012, d0 + 0.026, zt - 0.04), (ue - 0.012, d0 + 0.026, 1.36)], 0.0018, 4, "steel")
    out += tube(fr, [(ue + 0.010, d0 + 0.026, zt - 0.03), (ue + 0.010, d0 + 0.026, 1.55)], 0.0012, 4, "terrazzo")   # cord
    return out


BLINDS = [("SW", W1_PANES[0], ("open", 70.0, 6.0, True, 0.0)),
          ("SW", W1_PANES[1], ("open", 60.0, 5.0, False, 0.0)),
          ("SW", W1_PANES[2], ("stacked", -1)),
          ("NW", W2_PANES[0], ("open", 74.0, 6.0, False, 0.25)),
          ("NW", W2_PANES[1], ("open", 38.0, 4.0, True, 0.30))]


def blinds_faces():
    out = []
    for k, (wall, (a, b), pat) in enumerate(BLINDS):
        fr, n = wall_frame(wall)
        if wall == "SW":
            ua, ub = sorted((wall_u("SW", a, PG.YS), wall_u("SW", b, PG.YS)))
            out += blind_pane(fr, ua, ub, W1_D, pat, 2611 + k)
        else:
            out += blind_pane(fr, a, b, W2_D, pat, 2611 + k)
    return out


# ================================================================== 4. WALL STORY (P2 big wall, NW pier, entrance)
REG5 = {"supplier": (0, 0, 512, 768), "photo_counter": (512, 0, 768, 192), "photo_booths": (768, 0, 1024, 192),
        "photo_family": (512, 192, 704, 448), "plaque": (704, 192, 1024, 416), "hours": (512, 448, 704, 704),
        "catering": (704, 416, 1024, 704), "note": (0, 768, 256, 1024), "certificate": (256, 768, 576, 1024),
        "tin_sign": (576, 704, 1024, 1024)}


def w5_uv(key):
    x0, y0, x1, y1 = REG5[key]
    return (x0 / 1024 + 0.001, 1 - y1 / 1024 + 0.001, x1 / 1024 - 0.001, 1 - y0 / 1024 - 0.001)


def panel_fr(fr, n, u, z0, w, h, uvbox, mat, d=0.008, frame=None, fw=0.022, fd=0.016, board=0.0):
    """Paper / photo / sign on a wall frame: centred at u, bottom z0; optional frame or a solid board behind it."""
    out = []
    u0, v0, u1, v1 = uvbox
    dd = d + (fd * 0.5 if frame else 0.0) + board
    vs = [fr.p(u - w / 2, dd, z0), fr.p(u + w / 2, dd, z0), fr.p(u + w / 2, dd, z0 + h), fr.p(u - w / 2, dd, z0 + h)]
    emit(out, F(vs, mat, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=n))
    if board:
        out += cbox(fr, u - w / 2, u + w / 2, 0.0, board, z0, z0 + h, "iron", ch=0.003, grain="x", skip=("-y", "+y"))
    if frame:
        m = {"black": "rubber", "alu": "steel", "brown": "walnut"}[frame]
        for (a0, a1, b0, b1) in ((u - w / 2 - fw, u + w / 2 + fw, z0 - fw, z0), (u - w / 2 - fw, u + w / 2 + fw, z0 + h, z0 + h + fw),
                                 (u - w / 2 - fw, u - w / 2, z0, z0 + h), (u + w / 2, u + w / 2 + fw, z0, z0 + h)):
            out += cbox(fr, a0, a1, d - 0.004, d + fd, b0, b1, m, ch=0.003, grain="x" if (b1 - b0) < (a1 - a0) else "z", skip=("-y",))
        out += cbox(fr, u - w / 2, u + w / 2, d - 0.004, d + 0.002, z0, z0 + h, m, grain="x", skip=("-y",))
    return out


def story(wall, s, t, z0, w, key, **kw):
    fr, n = wall_frame(wall)
    x0, y0, x1, y1 = REG5[key]
    h = kw.pop("h", None) or w * (y1 - y0) / (x1 - x0)
    return panel_fr(fr, n, wall_u(wall, s, t), z0, w, h, w5_uv(key), "wall5", **kw)


def p2_story_faces():
    out = []
    fr, n = wall_frame("P2")
    zw = P2_T[0]
    # kept from v0.2.5: 1979 shop photo, espresso poster, clipping
    out += notice("P2", 0.25, zw, 1.70, 0.26, 0.26, "shop_photo", d=0.006, frame="black")
    out += notice("P2", 2.75, zw, 1.30, 0.46, 0.46, "espresso", d=0.006, frame="brown", fw=0.03)
    out += notice("P2", 4.50, zw, 1.38, 0.26, 0.26, "clipping", d=0.006, frame="black")
    # Zone A: everyday identity — big supplier poster over the first banquette table (sun-faded print, aluminium frame)
    out += story("P2", -1.10, zw, 1.28, 0.64, "supplier", d=0.006, frame="alu", fw=0.026)
    # Zone B: family / neighbourhood history — three colour snapshots of the shop + the youth-baseball sponsor plaque
    out += story("P2", 3.43, zw, 1.36, 0.34, "photo_counter", d=0.005, frame="black", fw=0.018)
    out += story("P2", 3.90, zw, 1.33, 0.24, "photo_family", d=0.005, frame="black", fw=0.018)
    out += story("P2", 3.58, zw, 1.66, 0.30, "photo_booths", d=0.005, frame="black", fw=0.018)
    out += story("P2", 4.62, zw, 1.82, 0.40, "plaque", d=0.0, board=0.016)
    # Zone D: service corner by the counter — cork board with flyers, catering notice taped up
    out += notice("P2", 6.33, zw, 1.30, 0.50, 0.40, "cork", d=0.006, frame="alu", fw=0.02)
    out += story("P2", 6.48, zw, 1.86, 0.25, "catering", d=0.003)
    # Zone C: surface age (decals): ghost of the picture that hung here for years, anchors where the portraits were,
    # sticker residue, paint patches, chipped wainscot tiles, chair / shoulder scuffs by the counter end
    emit(out, wall_decal(fr, 0.85, 0.004, 1.28, 0.62, 0.66, FRAME_GHOST, n))
    emit(out, wall_decal(fr, 5.25, 0.004, 1.30, 0.34, 0.30, STICKER, n))
    emit(out, wall_decal(fr, 5.20, 0.004, 1.70, 0.30, 0.30, ANCHORS, n))
    emit(out, wall_decal(fr, -2.35, 0.004, 1.78, 0.32, 0.26, PAINT_PATCH, n))
    emit(out, wall_decal(fr, 2.10, 0.004, 2.40, 0.42, 0.30, PAINT_PATCH, n))
    emit(out, wall_decal(fr, 6.80, 0.004, 2.20, 0.26, 0.24, PAINT_PATCH, n))
    for (s, z) in ((-1.65, 0.80), (1.78, 0.25), (5.70, 0.52), (6.70, 0.95)):
        emit(out, wall_decal(fr, s, 0.0175, z, 0.22, 0.22, TILE_CHIP, n))
    emit(out, wall_decal(fr, 6.25, 0.0175, 0.74, 1.30, 0.30, SCUFF_BAND, n))
    return out


def nw_pier_faces():
    """NW wall between the entrance chamfer and W2 (where the yellow fridge stood): old soda tin sign + restroom note."""
    out = []
    out += story("NW", PG.XW, 2.98, 1.52, 0.50, "tin_sign", d=0.0, board=0.008)
    out += story("NW", PG.XW, 3.28, 1.18, 0.15, "note", d=0.003)
    fr, n = wall_frame("NW")
    emit(out, wall_decal(fr, 2.92, 0.004, 1.24, 0.34, 0.20, STICKER, n))
    return out


def entrance_faces():
    """Store-hours card + old sticker residue on the chamfer pier next to D1, street grit around the mat."""
    out = []
    d2, n2, L = K3._chamfer_frame()
    fr = V.wall_frame(PG.P_NW, d2, n2)
    h1 = PG.A_NW - PG.D1["a"][0]
    u = h1 + PG.CASING_W + 0.20
    out += panel_fr(fr, (n2[0], n2[1], 0.0), u, 1.38, 0.15, 0.20, w5_uv("hours"), "wall5", d=0.003)
    emit(out, d5(fr.p(u - 0.17, 0.004, 1.30), V.mul(fr.X, 0.34), (0.0, 0.0, 0.40), STICKER, fr.Y))
    emit(out, d5(fr.p(u - 0.12, 0.004, 1.05), V.mul(fr.X, 0.24), (0.0, 0.0, 0.18), HAND_RUB, fr.Y))
    um = (PG.D1["a"][0] + PG.D1["a"][1]) / 2
    c = (PG.P_NW[0] + d2[0] * um + n2[0] * 0.75, PG.P_NW[1] + d2[1] * um + n2[1] * 0.75)
    q = 1.15
    emit(out, d5((c[0] - d2[0] * q - n2[0] * 0.75, c[1] - d2[1] * q - n2[1] * 0.75, FLOOR + 0.0025),
                 (d2[0] * 2 * q, d2[1] * 2 * q, 0.0), (n2[0] * 1.5, n2[1] * 1.5, 0.0), GRIT, (0.0, 0.0, 1.0)))
    return out


# ================================================================== 5. SEATING: same booths, refined vinyl
_BENCH_N = [0]


def bench26(fr, L, back_detail=False):
    """v0.2.1 bench (kept: plinth, seat box, panels, shell, cap, end caps) with refined vinyl: compressed sitting dips,
    softened front roll where people sit, per-channel wear on the back, welt seam at the seat/back joint, per-bench UV."""
    k_b = _BENCH_N[0]
    _BENCH_N[0] += 1
    import random
    rnd = random.Random(7300 + k_b)
    out = []
    D = V0.BENCH_D
    zf = FLOOR
    cbox_, mul = V0.cbox, V0.mul
    out += cbox_(fr, 0.02, L - 0.02, 0.07, D - 0.06, zf, zf + 0.09, "walnut", ch=0.003, grain="x", skip=("-z",))
    out += cbox_(fr, 0.0, L, 0.03, D - 0.035, zf + 0.09, 0.40, "walnut", ch=0.0, grain="x", skip=("-z", "+z", "-x", "+x"))
    fy = Frame(fr.p(0, D - 0.035, 0), fr.X, fr.Y, fr.Z)
    out += cbox_(fy, 0.0, L, 0.0, 0.02, zf + 0.09, zf + 0.165, "walnut", ch=0.004, grain="x", skip=("-y",))
    out += cbox_(fy, 0.0, L, 0.0, 0.02, 0.335, 0.40, "walnut", ch=0.004, grain="x", skip=("-y",))
    nst = 3 if L > 0.9 else 2
    sw = 0.07
    bay = (L - sw * nst) / (nst - 1)
    for k in range(nst):
        x = k * (bay + sw)
        out += cbox_(fy, x, x + sw, 0.0, 0.02, zf + 0.165, 0.335, "walnut", ch=0.004, grain="z", skip=("-y",), caps=(False, False))
    for k in range(nst - 1):
        a0 = sw + k * (bay + sw)
        out += V0.raised_panel(fy, a0, a0 + bay, zf + 0.165, 0.335, inset=0.03)
    out += cbox_(fr, 0.0, L, 0.0, 0.035, zf + 0.09, 1.045, "walnut", ch=0.0, grain="x", skip=("-x", "+x", "+z"))
    if back_detail:
        fb = Frame(fr.p(L, 0.0, 0.0), mul(fr.X, -1.0), mul(fr.Y, -1.0), fr.Z)
        out += cbox_(fb, 0.0, L, 0.0, 0.018, zf + 0.09, zf + 0.20, "walnut", ch=0.004, grain="x", skip=("-y",))
        out += cbox_(fb, 0.0, L, 0.0, 0.018, 0.93, 1.045, "walnut", ch=0.004, grain="x", skip=("-y",))
        for k in range(nst):
            x = k * (bay + sw)
            out += cbox_(fb, x, x + sw, 0.0, 0.018, zf + 0.20, 0.93, "walnut", ch=0.004, grain="z", skip=("-y",), caps=(False, False))
        for k in range(nst - 1):
            a0 = sw + k * (bay + sw)
            out += V0.raised_panel(fb, a0, a0 + bay, zf + 0.20, 0.93, inset=0.04)
    # seat cushions: crown + sitting dip (people sit 0.3 m from each cushion end... one dip per cushion) + softened front roll
    zc0, zc1 = 0.398, 0.472
    prof = V0.round_rect(0.075, D + 0.012, zc0, zc1, 0.03, seg=4, corners=(0.3, 0.4, 1.0, 0.5))
    half = L / 2
    su0, sv0 = V0._seed_uv(k_b, L, 26)
    for ci, (xa, xb) in enumerate(((0.035, half - 0.004), (half + 0.004, L - 0.035))):
        dip = rnd.uniform(0.007, 0.015)
        uc = rnd.uniform(0.42, 0.58)

        def crown(x, y, z, xa=xa, xb=xb, dip=dip, uc=uc):
            u = min(1.0, max(0.0, (x - xa) / (xb - xa)))
            k = max(0.0, math.sin(math.pi * u)) ** 0.6
            h = (z - zc0) / (zc1 - zc0)
            sit = math.exp(-((u - uc) / 0.28) ** 2) * max(0.0, min(1.0, (y - 0.10) / 0.18)) * max(0.0, min(1.0, (D + 0.01 - y) / 0.10))
            roll = math.exp(-((u - uc) / 0.30) ** 2) * max(0.0, min(1.0, (y - (D - 0.06)) / 0.07))
            return (y + 0.006 * k * max(0.0, (y - 0.3) / 0.27),
                    z + (0.011 * k * min(1.0, (D + 0.01 - y) / 0.06 + 0.2) - dip * sit - 0.006 * roll) * h)
        out += prism(fr, prof, xa, xb, "leather", rep=V0.REP["leather"], smooth="all", nseg=10, deform=crown, caps=(True, True),
                     uoff=su0 + 0.31 * ci, voff=sv0)
        pts = []
        for k in range(11):
            x = xa + (xb - xa) * k / 10
            y, z = crown(x, D + 0.003, zc1 - 0.006)
            pts.append((x, y, z))
        out += tube(fr, pts, 0.0055, 6, "leather")
    # back: backing plane + channel pillows (per-channel bulge: the two behind the sitting spots are flatter / sagged)
    b0, b1 = (0.105, 0.474), (0.050, 1.030)
    ax = (b1[0] - b0[0], b1[1] - b0[1])
    al = math.hypot(*ax)
    nrm = (ax[1] / al, -ax[0] / al)
    if nrm[0] < 0:
        nrm = (-nrm[0], -nrm[1])
    REP = V0.REP
    emit(out, F([fr.p(0.0, b0[0] - 0.01, b0[1]), fr.p(L, b0[0] - 0.01, b0[1]), fr.p(L, b1[0] - 0.01, b1[1]), fr.p(0.0, b1[0] - 0.01, b1[1])],
                "leather", [(0, 0), (L / REP["leather"], 0), (L / REP["leather"], al / REP["leather"]), (0, al / REP["leather"])],
                hint=fr.v(0, nrm[0], nrm[1])))
    nch = max(3, int(round(L / 0.27)))
    cw = L / nch
    worn = {int(nch * 0.25), int(nch * 0.75)}
    for k in range(nch):
        xa, xb = k * cw + 0.004, (k + 1) * cw - 0.004
        su, sv = V0._seed_uv(k, L, k_b)
        amp = 0.046 * (0.74 if k in worn else rnd.uniform(0.88, 1.04))
        sag = 0.35 if k in worn else 0.0

        def pillow(u, v, xa=xa, xb=xb, amp=amp, sag=sag):
            bulge = 0.004 + amp * (math.sin(math.pi * u) ** 0.55) * (math.sin(math.pi * v) ** (0.32 + sag))
            yb, zb = b0[0] + ax[0] * v, b0[1] + ax[1] * v
            return (xa + (xb - xa) * u, yb + nrm[0] * bulge, zb + nrm[1] * bulge)
        out += V0.grid(fr, pillow, 6, 12, "leather", lambda u, v, xa=xa, xb=xb, su=su, sv=sv:
                       ((xa + (xb - xa) * u) / REP["leather"] + su, v * al / REP["leather"] + sv),
                       hint_fn=lambda u, v: (0.0, nrm[0], nrm[1]))
    out += tube(fr, [(0.0, b0[0] + 0.012, b0[1] + 0.006), (L, b0[0] + 0.012, b0[1] + 0.006)], 0.0065, 6, "leather")   # welt seam
    cap = [(-0.012, 1.040), (0.080, 1.040), (0.080, 1.068), (0.071, 1.090), (0.050, 1.102), (0.010, 1.102), (-0.006, 1.094), (-0.012, 1.080)]
    out += prism(fr, cap, -0.035, L + 0.035, "walnut", smooth={2, 3, 4, 5, 6})
    side = [(-0.015, zf), (D + 0.015, zf), (D + 0.015, 0.50), (D - 0.005, 0.535), (D - 0.05, 0.553), (0.22, 0.582),
            (0.155, 0.612), (0.118, 0.68), (0.10, 1.04), (-0.015, 1.04)]
    for x0, x1, outward in ((-0.035, 0.0, -1.0), (L, L + 0.035, 1.0)):
        out += prism(fr, side, x0, x1, "walnut", caps=(True, True))
        xo = x0 if outward < 0 else x1
        fo = Frame(fr.p(xo, 0.0, 0.0), fr.Y, mul(fr.X, outward), fr.Z)
        out += V0.raised_panel(fo, 0.05, D - 0.04, zf + 0.11, 0.45, y_back=0.0, y_top=0.008, inset=0.03)
    # worn front edges where people slide in and out (2 of 3 benches)
    if k_b % 3 != 2:
        for xs in (L * 0.28, L * 0.72):
            emit(out, d5(fr.p(xs - 0.13, D + 0.019, 0.402), mul(fr.X, 0.26), (0.0, 0.0, 0.07), VINYL_WEAR, fr.Y))
    return out


def seating_faces():
    _BENCH_N[0] = 0
    old = K3.bench
    K3.bench = bench26
    try:
        return K3.booths_faces() + K3.banquette_faces()
    finally:
        K3.bench = old


# ================================================================== 6. SERVICE: till, staff mat, deli prep, cleaning corner
def service_faces():
    out = []
    zc = 1.02
    for (s, t) in ((7.80, 5.38), (7.80, 5.48)):                                   # spare receipt rolls by the till
        fr = WORLD.child(s, t, 0.0)
        out += lathe(fr, [(0.0, zc + 0.072), (0.038, zc + 0.072), (0.040, zc + 0.068), (0.040, zc + 0.004), (0.038, zc), (0.0, zc)][::-1],
                     14, "terrazzo")
    fr = WORLD.child(7.30, 4.80, 0.0)                                             # change dish
    out += lathe(fr, [(0.0, zc + 0.002), (0.055, zc + 0.002), (0.065, zc + 0.016), (0.069, zc + 0.017), (0.060, zc + 0.003),
                      (0.0, zc + 0.0005)][::-1], 18, "steel")
    # staff anti-fatigue mat behind the register (rubber, bevelled), worn mats are flat: no collision
    s0, s1, t0, t1, hz = 8.08, 8.86, 4.52, 5.70, 0.012
    out += cbox(WORLD, s0 + 0.02, s1 - 0.02, t0 + 0.02, t1 - 0.02, FLOOR, FLOOR + hz, "rubber", grain="x", skip=("-z",))
    for (a0, a1, b0, b1, hn) in ((s0, s0 + 0.02, t0, t1, (-1, 0, 1)), (s1 - 0.02, s1, t0, t1, (1, 0, 1)),
                                 (s0 + 0.02, s1 - 0.02, t0, t0 + 0.02, (0, -1, 1)), (s0 + 0.02, s1 - 0.02, t1 - 0.02, t1, (0, 1, 1))):
        hi = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
        vs = [(x, y, FLOOR + (hz if (abs(x - s0) > 0.019 and abs(x - s1) > 0.019 and abs(y - t0) > 0.019 and abs(y - t1) > 0.019) else 0.002))
              for (x, y) in hi]
        emit(out, F(vs, "rubber", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=hn))
    # butcher-paper roll on brackets + a stack of deli sheets + tongs on the back counter
    zb = 0.92
    s_r = 9.62
    for t in (2.50, 3.02):
        out += cbox(WORLD, s_r - 0.07, s_r + 0.07, t - 0.006, t + 0.006, zb, zb + 0.17, "steel", grain="z")
    fr = Frame((s_r, 2.51, zb + 0.105), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0))
    out += lathe(fr, [(0.0, 0.0), (0.058, 0.0), (0.06, 0.004), (0.06, 0.496), (0.058, 0.5), (0.0, 0.5)][::-1], 16, "terrazzo")
    out += cbox(WORLD, s_r - 0.085, s_r - 0.075, 2.50, 3.02, zb + 0.03, zb + 0.05, "steel", grain="y")             # cutter bar
    out += cbox(WORLD, 9.40, 9.70, 3.22, 3.48, zb, zb + 0.022, "terrazzo", grain="x", ch=0.002)                   # deli sheets
    for k, dt in enumerate((-0.012, 0.012)):
        out += cbox(WORLD, 9.36, 9.60, 3.66 + dt - 0.006, 3.66 + dt + 0.006, zb + 0.004 + 0.006 * k, zb + 0.008 + 0.006 * k, "steel", grain="x")
    # grease / mop / cup-ring decals where the work happens
    for (s, t, q, cell) in ((8.45, 5.95, 0.40, GREASE), (8.40, 1.25, 0.35, GREASE), (6.45, 2.60, 0.55, MOP), (6.40, 4.45, 0.55, MOP)):
        emit(out, d5((s - q, t - q, FLOOR + 0.0028), (2 * q, 0.0, 0.0), (0.0, 2 * q, 0.0), cell, (0.0, 0.0, 1.0)))
    for (s, t) in ((BANQ_TABLES[1], BANQ_T), (3.425, -0.62)):
        emit(out, d5((s - 0.14, t - 0.14, ZT + 0.0012), (0.28, 0.0, 0.0), (0.0, 0.28, 0.0), CUP_RINGS, (0.0, 0.0, 1.0)))
    return out


def service_vanilla():
    yaw_till = 90.0
    out = [("v_ret_gc_pen1", 7.36, 5.42, 1.02, 30.0), ("prop_notepad_02", 7.58, 5.36, 1.02, yaw_till + 8.0)]
    # cleaning corner just through the P2 door (staff aisle -> north back room), against the back face of P2, beside the
    # door, out of the walking line; staff only, off the dining floor (/gs_cam GS26_REAR looks at it from the aisle)
    out += [("v_serv_bktmop_h", 9.60, 7.45, FLOOR, 8.0), ("v_serv_wetfloorsn", 10.12, 7.32, FLOOR, 22.0),
            ("prop_tool_broom", 10.48, 7.17, FLOOR, 0.0), ("v_ind_cs_spray", 9.40, 7.90, FLOOR, 40.0)]
    # light switch by the counter end of P2 (old plastic plate) — model front is local +x
    out.append(("v_serv_switch_2", 6.86, P2_T[0], 1.16, -90.0))                  # local +x -> -t (into the hall)
    # one modest plant in the NW corner (revision), clear of the ledge, banquette and stools
    out.append(("prop_plant_int_04a", -2.50, 6.66, FLOOR, 25.0))
    return out


# ================================================================== 7. DECALS kept from v0.2.5 (patch moved off the cork board)
def decal_faces():
    out = []
    z = FLOOR + 0.002
    u0, vb, u1, vt = dcell(GRIME)
    for fr, runs, _ in V.wall_runs():
        for a, b, kind in runs:
            if kind != "full" or b - a < 0.4:
                continue
            u = a + 0.1
            while u < b - 0.3:
                Lr = min(1.6, b - u - 0.1)
                emit(out, K3.decal_quad(fr.p(u, 0.0155, FLOOR + 0.10), V.mul(fr.X, Lr), (0.0, 0.0, 0.26), (u0, vb, u1, vt)))
                u += Lr + 0.9
    for (s, t, r) in FLOOR_WEAR:
        emit(out, K3.decal_quad((s - r, t - r, z), (2 * r, 0.0, 0.0), (0.0, 2 * r, 0.0), dcell(TRAFFIC)))
    for (s, t) in SCUFFS:
        emit(out, K3.decal_quad((s - 0.30, t - 0.30, z + 0.0005), (0.6, 0.0, 0.0), (0.0, 0.6, 0.0), dcell(SCUFF)))
    fr, n = wall_frame("NW")
    emit(out, K3.decal_quad(fr.p(4.40, 0.0175, 0.12), (0.0, 0.32, 0.0), (0.0, 0.0, 0.42), dcell(DRIPS)))
    fr, n = wall_frame("SW")
    ua = wall_u("SW", PIER_A, PG.YS)
    emit(out, K3.decal_quad(fr.p(ua - 0.11, 0.004, 1.62), V.mul(fr.X, 0.22), (0.0, 0.0, 0.28), dcell(GHOST)))
    emit(out, K3.decal_quad(fr.p(ua - 0.13, 0.004, 2.10), V.mul(fr.X, 0.26), (0.0, 0.0, 0.20), dcell(PATCH)))
    emit(out, K3.decal_quad((-0.52, 6.55, 0.485), (0.14, 0.0, 0.0), (0.0, 0.14, 0.0), dcell(TAPE)))
    return out


def entry_mat26():
    """v0.2.3 entry mat, fixed: its top sat 7 mm BELOW the floor (z 0.008 < FLOOR 0.015), so only the rim showed."""
    d2, n2, L = K3._chamfer_frame()
    um = (PG.D1["a"][0] + PG.D1["a"][1]) / 2
    c = (PG.P_NW[0] + d2[0] * um + n2[0] * 0.06, PG.P_NW[1] + d2[1] * um + n2[1] * 0.06)
    fr = Frame((c[0], c[1], 0.0), (d2[0], d2[1], 0.0), (n2[0], n2[1], 0.0), (0.0, 0.0, 1.0))
    out = []
    w, dep, hz = 1.70, 0.95, FLOOR + 0.009
    vs = [fr.p(-w / 2, 0.0, hz), fr.p(w / 2, 0.0, hz), fr.p(w / 2, dep, hz), fr.p(-w / 2, dep, hz)]
    emit(out, F(vs, "mat", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(0.0, 0.0, 1.0)))       # 0.2.3 UVs were mirrored
    for (a0, a1, b0, b1) in ((-w / 2, w / 2, -0.02, 0.0), (-w / 2, w / 2, dep, dep + 0.02), (-w / 2 - 0.02, -w / 2, 0.0, dep), (w / 2, w / 2 + 0.02, 0.0, dep)):
        out += cbox(fr, a0, a1, b0, b1, FLOOR, hz - 0.002, "rubber", grain="x", skip=("-z",))
    return out


# ================================================================== assemble
def hall_faces():
    out = []
    out += K3.wall_kit_faces()
    out += K3.ceiling_faces()                     # T-bar grid + counter soffit (kept)
    out += ceiling_system()[0]                    # troffers, vents, ceiling decals, wall-top grime
    for (s, t, kind) in K3.CANS:                  # recessed cans (kept)
        out += V0.recessed_can(s, t, CEIL)
    for t in (1.05, 2.05, 3.20, 4.20, 5.10, 6.15):
        out += V0.recessed_can(7.55, t, K3.SOFFIT["z"])
    out += K3.menu_boards()
    out += seating_faces()
    out += K3.ledge_faces()
    out += V.counters_faces()
    out += entry_mat26()
    for sc, tc in CTABLES:
        out += K3.table2(sc, tc, size=K5.CT_SIZE)
    out += K5.p1_wall_faces()
    out += p2_story_faces()
    out += K5.sw_wall_faces()
    out += nw_pier_faces()
    out += entrance_faces()
    out += K5.counter_faces()
    out += blinds_faces()
    out += service_faces()
    out += decal_faces()
    return [f for f in out if f is not None]


REMOVED = dict(K5.REMOVED)
REMOVED.update({"bkr_prop_biker_pendant_light": "v0.2.6 §4.1 hanging dome pendants -> recessed troffers",
                "prop_ped_pic_*": "v0.2.6 §8 black-and-white mugshot-style portraits removed (not reinstalled under other names)"})


def vanilla_props():
    out = []
    for name, s, t, zb, yaw in K5.vanilla_props():
        if name == "bkr_prop_biker_pendant_light" or name.startswith("prop_ped_pic_"):
            continue
        if name == "v_ilev_fib_sprklr":
            c = (int(math.floor(s / P)), int(math.floor(t / P)))
            if c in SPRINKLER_MOVE:
                i, j = SPRINKLER_MOVE[c]
                s, t = (i + 0.5) * P, (j + 0.5) * P
        out.append((name, s, t, zb, yaw))
    out += service_vanilla()
    seen, uniq = set(), []                       # v0.2.5 placed the P2 clock twice (v0.2.3 list + v0.2.5 list): keep one
    for e in out:
        key = (e[0], round(e[1], 3), round(e[2], 3), round(e[3], 3))
        if key not in seen:
            seen.add(key)
            uniq.append(e)
    return uniq


def vanilla_entities():
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        mn = VB[name][0]
        out.append((name, (round(s, 4), round(t, 4), round(zb - mn[2], 4)), math.radians(yaw)))
    return out


def collision_boxes():
    return K5.collision_boxes()


SEATS = dict(K5.SEATS)

# exterior (client-side spawn, client/exterior.lua): grouped on the blank NW facade just past W2, snapped to the wall by a
# runtime ray-cast (fx, fy = front direction in MLO-local axes; the script finds the real facade behind the machine)
EXTERIOR = [("prop_gumball_02", -3.45, 6.95, (-1.0, 0.0)), ("prop_gumball_01", -3.45, 7.62, (-1.0, 0.0))]
