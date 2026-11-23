# LONG PIG — v0.2.3 "90s lobby" hall kit (owner 2026-11-01 14:08-14:11: rebuild, more seats, NO wood, match the exterior
# of the Long Pig Mini Market: corrugated metal + concrete block, yellow/red awning, black-and-white floor).
# Reuses the v0.2.1 primitives / booths / deli cases (gs_v021_kit) and replaces the architecture + dressing:
#   * walls: oxblood glazed tile wainscot (CC0 Tiles010 recolour) with aluminium cap + black rubber cove base,
#            cream painted brick above (CC0 PaintedBricks004, shell material) — no wood joinery any more
#   * ceiling: suspended mineral-fibre tile ceiling (own texture) with white T-bar grid, 2x4 troffers, recessed cans
#   * seating 26: 3 red-vinyl booths (W1), 2 red-vinyl banquettes on P2 with 4 laminate tables + 4 chairs,
#            window bar ledge at W2 with 3 stools, 3 counter stools
#   * own backlit menu boards over the counter, LONG PIG entry mat, grime decals; vanilla props by archetype name only
# Material slots keep the v0.2.1 indices; slot 0 ("walnut") now renders as maroon laminate, slot 1 ("leather") as red
# vinyl, slot 2 ("terrazzo") as cream speckle laminate (see SHADER_SPECS, used by gs_20).
import math
import gs_proto_geometry as PG
import gs_slice_geometry as SG
import gs_v021_kit as V
from gs_v021_kit import (Frame, WORLD, F, emit, cbox, prism, lathe, tube, mul, FLOOR, CEIL, LT, CORONA, flags_total,
                         KEY_FLAGS, FILL_FLAGS, C_TUNGSTEN, C_FILL, C_CASE, ROOM_TIMECYCLE, booth_bays, table_center,
                         COUNTER_FRONT, COUNTER_BACK, CASES_T, P1_S, P2_T, SOFFIT, BENCH_D, BENCH_T, TABLE_T, TABLE_W,
                         BOOTH_PITCH, N_BOOTHS, wall_runs, wall_yaw, recessed_can, chamfer_s_at, chamfer_t_at, cpv_hall,
                         bench, VB, BACK_S, REGISTER_T, COFFEE_T, GATE_T)

V.MAT.update({"tile": 13, "tile_white": 14, "rubber": 15, "menu": 16, "troffer": 17, "decal": 18, "mat": 19})
V.REP.update({"tile": 0.6, "tile_white": 0.6, "rubber": 0.5, "menu": 1.0, "troffer": 0.3, "decal": 1.0, "mat": 1.0})
MAT = V.MAT
# (shader, textures {sampler: name}, params, name) in MAT order — consumed by gs_20 (no wood textures left)
def _pbr(nm, d, n, s, falloff, inten=1.0, bump=1.0):
    return ("normal_spec.sps", {"DiffuseSampler": d, "BumpSampler": n, "SpecSampler": s},
            {"specularIntensityMult": inten, "specularFalloffMult": falloff, "specularFresnel": 0.97, "bumpiness": bump}, nm)
SHADER_SPECS = [
    _pbr("lp3_laminate_red", "lp3_laminate_red", "lp3_laminate_n", "lp3_laminate_s", 70.0, 0.8),          # 0 (was walnut)
    _pbr("lp3_vinyl_red", "lp3_vinyl_red", "lp2_leather_n", "lp3_vinyl_s", 55.0, 1.2, 1.0),               # 1 (was leather)
    _pbr("lp3_laminate_cream", "lp3_laminate_cream", "lp3_laminate_n", "lp3_laminate_s", 70.0, 0.8),      # 2 (was terrazzo)
    _pbr("lp_steel", "lp_steel", "lp_steel_n", "lp_steel_s", 160.0, 1.5),                                 # 3 stainless / chrome
    _pbr("lp2_enamel", "lp2_enamel", "lp2_enamel_n", "lp2_enamel_s", 80.0),                               # 4 enamel / T-bar
    _pbr("lp_brass", "lp_brass", "lp_flat_n", "lp_brass_s", 60.0),                                        # 5
    _pbr("lp2_iron", "lp2_iron", "lp2_iron_n", "lp2_iron_s", 30.0),                                       # 6
    ("glass_env.sps", {"DiffuseSampler": "gs_proto_glass", "BumpSampler": "gs_proto_flat_n", "SpecSampler": "gs_proto_glass_s"},
     {"specularIntensityMult": 1.0, "specularFalloffMult": 100.0, "specularFresnel": 0.97, "bumpiness": 0.2}, "lp2_case_glass"),  # 7
    _pbr("lp2_food", "lp3_food", "lp3_food_n", "lp2_food_s", 25.0, 0.8),                                  # 8 (1024 copies: 16 MiB budget)
    ("emissive.sps", {"DiffuseSampler": "lp_glow"}, {"emissiveMultiplier": 4.0}, "lp2_glow"),            # 9
    _pbr("lp2_flag", "lp2_flag", "lp2_flag_n", "lp_matte_s", 8.0, 0.3),                                   # 10
    ("emissive.sps", {"DiffuseSampler": "lp2_opal"}, {"emissiveMultiplier": 1.6}, "lp2_opal"),           # 11
    _pbr("lp2_plaster", "lp_wall_plaster", "lp_wall_plaster_n", "lp_wall_plaster_s", 8.0, 0.5),           # 12
    _pbr("lp3_tile_red", "lp3_tile_red", "lp3_tile_n", "lp3_tile_s", 140.0, 1.1),                         # 13
    _pbr("lp3_tile_white", "lp3_tile_white", "lp3_tile_n", "lp3_tile_s", 140.0, 1.1),                     # 14
    _pbr("lp3_rubber", "lp3_rubber", "lp_flat_n", "lp_matte_s", 20.0, 0.3),                               # 15
    ("emissive.sps", {"DiffuseSampler": "lp3_menu"}, {"emissiveMultiplier": 1.3}, "lp3_menu"),           # 16 backlit menu
    ("emissive.sps", {"DiffuseSampler": "lp3_troffer"}, {"emissiveMultiplier": 2.2}, "lp3_troffer"),     # 17 troffer lens
    ("decal.sps", {"DiffuseSampler": "lp3_decal_grime"}, {}, "lp3_decal_grime"),                        # 18 grime decals
    _pbr("lp3_mat", "lp3_mat", "lp_flat_n", "lp_matte_s", 10.0, 0.2),                                     # 19 entry mat
]
assert len(SHADER_SPECS) == len(MAT)
HALL_MAT_NOTE = "slot 0 laminate, 1 vinyl, 2 laminate (no wood)"
P = PG.CEIL_UV_M / 8.0               # 0.64375 m ceiling tile pitch (texture seams at k * P)
TILE_TOP = 1.15                      # wainscot height
LEDGE = dict(s=(PG.XW, PG.XW + 0.34), t=(3.55, 6.33), z=1.065)
BANQ = [(-2.00, 3.70), (1.85, 3.70)]  # (s start, length) along P2
BANQ_TABLES = [-1.10, 0.85, 2.75, 4.65]
BANQ_T = P2_T[0] - BENCH_D - 0.03 - 0.35          # 6.01  table centre t
TABLE2 = 0.70                                     # 2-top table size
ZT = 0.768                                         # table top height (same as the booths)
CAM_VIEWS = dict(V.CAM_VIEWS)
CAM_VIEWS.update({
    "VD": ((2.0, 3.2, 1.62), (1.6, 6.9, 1.2), "banquettes + photo wall (P2)"),
    "VE": ((0.4, 4.6, 1.62), (-2.9, 5.0, 1.3), "window bar ledge W2"),
    "VF": ((3.0, 2.4, 1.6), (7.0, 4.6, 2.5), "menu boards over the counter"),
})


# ================================================================== 1. WALLS: tile wainscot, cap, cove base, ceiling angle
def tile_wainscot(fr, u0, u1, top, mat="tile"):
    out = []
    out += cbox(fr, u0, u1, 0.0, 0.012, FLOOR, FLOOR + 0.10, "rubber", grain="x", skip=("-y",))           # cove base
    out += cbox(fr, u0, u1, 0.0, 0.015, FLOOR, FLOOR + 0.012, "rubber", grain="x", skip=("-y", "-z"))      # toe
    out += cbox(fr, u0, u1, 0.0, 0.009, FLOOR + 0.10, top - 0.018, mat, grain="x", rep=V.REP[mat], skip=("-y",))
    prof = [(0.0, top - 0.018), (0.014, top - 0.018), (0.016, top - 0.012), (0.016, top - 0.004), (0.010, top), (0.0, top)]
    out += prism(fr, prof, u0, u1, "steel", smooth={1, 2, 3}, skip_dirs=[(0.0, -1.0, 0.0)])            # aluminium cap
    return out


def ceiling_angle(fr, u0, u1):
    return cbox(fr, u0, u1, 0.0, 0.022, CEIL - 0.022, CEIL - 0.0005, "enamel", grain="x", skip=("-y", "+z"))


def wall_kit_faces():
    out = []
    for fr, runs, (c0, c1) in wall_runs():
        for u0, u1, kind in runs:
            if u1 - u0 < 0.05:
                continue
            out += tile_wainscot(fr, u0, u1, TILE_TOP if kind == "full" else 0.585)
        out += ceiling_angle(fr, c0, c1)
    # white tile behind the back counter (P1 face, splashback up to 2.40 m)
    sp = Frame((P1_S[0], SG.BACK_T[0], 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    out += cbox(sp, 0.0, SG.BACK_T[1] - SG.BACK_T[0], 0.0, 0.006, 0.92, 2.40, "tile_white", grain="x", rep=0.6, skip=("-y",))
    out += cbox(sp, 0.0, SG.BACK_T[1] - SG.BACK_T[0], 0.0, 0.016, 2.40, 2.418, "steel", grain="x", skip=("-y",))
    return out


# ================================================================== 2. SUSPENDED CEILING: T-bar grid, troffers, cans
TROFFERS = [  # (s cell, t cell, n_s, n_t) on the P grid
    (0, 1, 2, 1), (4, 1, 2, 1), (8, 1, 2, 1),
    (-2, 4, 2, 1), (2, 4, 2, 1), (6, 4, 2, 1),
    (0, 6, 2, 1), (4, 6, 2, 1),
    (13, 2, 2, 1), (13, 6, 2, 1),      # staff aisle behind the counter
]
CANS = [(s, BANQ_T - 0.05, "banquette") for s in BANQ_TABLES] + \
       [(-2.45, 4.25, "ledge"), (-2.45, 5.65, "ledge"), (-0.70, 1.05, "entrance")]


def _bar_s(s, out):
    """T-bar along t at constant s (hall part and staff part)."""
    if PG.XW < s < COUNTER_FRONT:
        t0 = PG.YS if s >= PG.P_SW[0] else max(PG.YS, chamfer_t_at(s))
        if s < PG.P_NW[0]:
            return
        out += cbox(WORLD, s - 0.012, s + 0.012, t0, P2_T[0], CEIL - 0.012, CEIL - 0.0005, "enamel", grain="y", skip=("+z",))
    elif COUNTER_BACK < s < P1_S[0]:
        out += cbox(WORLD, s - 0.012, s + 0.012, PG.YS, P2_T[0], CEIL - 0.012, CEIL - 0.0005, "enamel", grain="y", skip=("+z",))


def _bar_t(t, out):
    if not (PG.YS < t < P2_T[0]):
        return
    s0 = max(PG.XW, chamfer_s_at(t)) if t < PG.P_NW[1] else PG.XW
    out += cbox(WORLD, s0, COUNTER_FRONT, t - 0.012, t + 0.012, CEIL - 0.012, CEIL - 0.0005, "enamel", grain="x", skip=("+z",))
    out += cbox(WORLD, COUNTER_BACK, P1_S[0], t - 0.012, t + 0.012, CEIL - 0.012, CEIL - 0.0005, "enamel", grain="x", skip=("+z",))


def troffer(i, j, ns, nt):
    out = []
    s0, s1, t0, t1 = i * P, (i + ns) * P, j * P, (j + nt) * P
    b = 0.035
    z0, z1 = CEIL - 0.022, CEIL - 0.001
    out += cbox(WORLD, s0, s1, t0, t0 + b, z0, z1, "enamel", grain="x", skip=("+z",))
    out += cbox(WORLD, s0, s1, t1 - b, t1, z0, z1, "enamel", grain="x", skip=("+z",))
    out += cbox(WORLD, s0, s0 + b, t0 + b, t1 - b, z0, z1, "enamel", grain="y", skip=("+z",), caps=(False, False))
    out += cbox(WORLD, s1 - b, s1, t0 + b, t1 - b, z0, z1, "enamel", grain="y", skip=("+z",), caps=(False, False))
    zl = CEIL - 0.016
    vs = [(s0 + b, t0 + b, zl), (s1 - b, t0 + b, zl), (s1 - b, t1 - b, zl), (s0 + b, t1 - b, zl)]
    emit(out, F(vs, "troffer", [(0, 0), (ns * 2.0, 0), (ns * 2.0, nt * 2.0), (0, nt * 2.0)], hint=(0.0, 0.0, -1.0)))
    return out, ((s0 + s1) / 2, (t0 + t1) / 2)


def ceiling_faces():
    out = []
    for k in range(-6, 17):
        _bar_s(k * P, out)
    for k in range(-2, 12):
        _bar_t(k * P, out)
    # counter soffit (bulkhead): plaster underside + laminate fascia (was walnut)
    s0, s1 = SOFFIT["s"]
    t0, t1 = SOFFIT["t"]
    z = SOFFIT["z"]
    out += cbox(WORLD, s0, s1, t0, t1, z, CEIL, "plaster", ch=0.0, grain="y", skip=("+z",), caps=(False, False))
    out += cbox(WORLD, s0 - 0.03, s0 + 0.002, t0, t1, z - 0.02, z + 0.24, "walnut", ch=0.004, grain="y", caps=(False, False))
    out += cbox(WORLD, s0 - 0.034, s0 + 0.002, t0, t1, z - 0.035, z - 0.02, "steel", ch=0.003, grain="y", caps=(False, False))
    return out


def menu_boards():
    """Own backlit menu cabinets hung under the soffit edge, facing the customers (-s). Atlas: A = top half, B = bottom."""
    out = []
    for (t0, t1, v0, v1) in ((0.75, 3.25, 0.5, 1.0), (3.55, 6.55, 0.0, 0.5)):
        sF, sB = COUNTER_FRONT - 0.10, COUNTER_FRONT - 0.02
        z0, z1 = 2.30, 2.90
        vs = [(sF, t1, z0), (sF, t0, z0), (sF, t0, z1), (sF, t1, z1)]
        emit(out, F(vs, "menu", [(0.0, v0), (1.0, v0), (1.0, v1), (0.0, v1)], hint=(-1.0, 0.0, 0.0)))
        e = 0.025
        out += cbox(WORLD, sF - 0.004, sB, t0 - e, t0, z0 - e, z1 + e, "steel", grain="z")
        out += cbox(WORLD, sF - 0.004, sB, t1, t1 + e, z0 - e, z1 + e, "steel", grain="z")
        out += cbox(WORLD, sF - 0.004, sB, t0, t1, z0 - e, z0, "steel", grain="y", caps=(False, False))
        out += cbox(WORLD, sF - 0.004, sB, t0, t1, z1, z1 + e, "steel", grain="y", caps=(False, False))
        out += cbox(WORLD, sF + 0.002, sB, t0, t1, z0, z1, "enamel", grain="y", skip=("-x",), caps=(False, False))
        for tt in (t0 + 0.25, t1 - 0.25):
            out += tube(WORLD, [((sF + sB) / 2, tt, z1 + e), ((sF + sB) / 2, tt, SOFFIT["z"] - 0.035)], 0.005, 6, "steel")
    return out


def ceiling_fixtures():
    """-> faces, lights (dicts), vanilla (name, s, t, z_bottom, yaw)."""
    out, lights, van = [], [], []
    C_FLUO = (1.0, 0.93, 0.82)       # warm-white fluorescent (~3500 K)
    for (i, j, ns, nt) in TROFFERS:
        f, (sc, tc) = troffer(i, j, ns, nt)
        out += f
        lights.append(LT("troffer", "SPOT", (sc, tc, CEIL - 0.05), C_FLUO, 3.0, 4.2, 6.0, cone=(75.0, 38.0),
                         flags=("not_in_reflection",)))
    for (s, t, kind) in CANS:
        out += recessed_can(s, t, CEIL)
        if kind == "banquette":
            lights.append(LT("banquette_key", "SPOT", (s, t, CEIL - 0.04), C_TUNGSTEN, 6.0, 3.4, 14.0, cone=(42.0, 20.0),
                             flags=("static_shadows", "not_in_reflection"), corona=(0.10, 0.35)))
        else:
            lights.append(LT(kind + "_can", "SPOT", (s, t, CEIL - 0.04), C_TUNGSTEN, 4.5, 3.2, 12.0, cone=(45.0, 22.0),
                             flags=("not_in_reflection",), corona=(0.10, 0.35)))
    # Zone A key: enamel pendants (vanilla) over the booth tables
    for a in booth_bays():
        sc, tc = table_center(a)
        van.append(("bkr_prop_biker_pendant_light", sc, tc + 0.05, CEIL - 1.284, 0.0))
        lights.append(LT("booth_pendant_key", "SPOT", (sc, tc + 0.05, 2.20), C_TUNGSTEN, 8.0, 3.0, 16.0, cone=(55.0, 25.0),
                         flags=KEY_FLAGS))
        lights.append(CORONA("booth_bulb", (sc, tc + 0.05, 2.22), C_TUNGSTEN, 0.40, 0.7))
    # Zone B key: queue pendants (vanilla) in front of the cases
    for t in ((CASES_T[0][0] + CASES_T[0][1]) / 2, (CASES_T[1][0] + CASES_T[1][1]) / 2):
        sq = (V.BEAM_S[4] + COUNTER_FRONT) / 2 + 0.02
        van.append(("bkr_prop_biker_pendant_light", sq, t, CEIL - 1.284, 0.0))
        lights.append(LT("queue_pendant_key", "SPOT", (sq, t, 2.02), C_TUNGSTEN, 7.0, 3.2, 14.0, cone=(58.0, 26.0), flags=KEY_FLAGS))
        lights.append(CORONA("queue_bulb", (sq, t, 2.04), C_TUNGSTEN, 0.45, 0.8))
    # soffit cans over the cases / register
    for t in (1.05, 2.05, 3.20, 4.20, 5.10, 6.15):
        out += recessed_can(7.55, t, SOFFIT["z"])
        lights.append(LT("soffit_can", "SPOT", (7.55, t, SOFFIT["z"] - 0.03), (1.0, 0.88, 0.72), 5.0, 2.4, 16.0, cone=(36.0, 14.0),
                         flags=("not_in_reflection",), corona=(0.12, 0.35)))
    # backlit menu boards: soft glow onto the queue
    for t in (2.0, 5.05):
        lights.append(LT("menu_glow", "POINT", (COUNTER_FRONT - 0.45, t, 2.55), (1.0, 0.95, 0.86), 0.9, 2.4, 6.0, flags=FILL_FLAGS))
    lights.append(LT("staff_fill", "POINT", (8.85, 3.40, 2.85), C_FILL, 0.7, 3.5, 6.0, flags=FILL_FLAGS))
    return out, lights, van


# ================================================================== 3. SEATING
def table2(sc, tc, size=TABLE2, zt=ZT):
    """2-top: cream laminate top, chrome band, cast-iron pedestal."""
    out = []
    h = size / 2
    s0, s1, t0, t1 = sc - h, sc + h, tc - h, tc + h
    band = 0.035
    edge = [(-band, zt - 0.030), (-0.004, zt - 0.030), (0.0, zt - 0.022), (0.002, zt - 0.014), (0.0, zt - 0.006), (-0.004, zt), (-band, zt)]
    for sgn, s_edge in ((-1.0, s0), (1.0, s1)):
        fr = Frame((s_edge, 0.0, 0.0), (0.0, 1.0, 0.0), (sgn, 0.0, 0.0), (0.0, 0.0, 1.0))
        out += prism(fr, edge, t0, t1, "steel", smooth={1, 2, 3, 4})
    for sgn, t_edge in ((-1.0, t0), (1.0, t1)):
        fr = Frame((0.0, t_edge, 0.0), (1.0, 0.0, 0.0), (0.0, sgn, 0.0), (0.0, 0.0, 1.0))
        out += prism(fr, edge, s0 + band, s1 - band, "steel", smooth={1, 2, 3, 4}, caps=(False, False))
    out += cbox(WORLD, s0 + band, s1 - band, t0 + band, t1 - band, zt - 0.028, zt - 0.001, "terrazzo", grain="x", skip=("-z",))
    out += cbox(WORLD, s0 + 0.02, s1 - 0.02, t0 + 0.02, t1 - 0.02, zt - 0.05, zt - 0.03, "walnut", grain="x")
    ped = [(0.0, FLOOR), (0.22, FLOOR), (0.222, FLOOR + 0.012), (0.20, FLOOR + 0.024), (0.11, FLOOR + 0.04), (0.055, FLOOR + 0.07),
           (0.04, FLOOR + 0.11), (0.034, FLOOR + 0.16), (0.032, zt - 0.12), (0.04, zt - 0.10), (0.08, zt - 0.075),
           (0.10, zt - 0.062), (0.10, zt - 0.05), (0.0, zt - 0.05)]
    out += lathe(WORLD.child(sc, tc, 0.0), ped, 20, "steel", rep=0.5, tiles_u=2.0)
    return out


def booths_faces():
    out = []
    L = BENCH_T[1] - BENCH_T[0]
    for k, a in enumerate(booth_bays()):
        frA = Frame((a, BENCH_T[0], 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        frB = Frame((a + BOOTH_PITCH, BENCH_T[1], 0.0), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        out += bench(frA, L, back_detail=(k == 0))
        out += bench(frB, L, back_detail=(k == N_BOOTHS - 1))
        sc, _ = table_center(a)
        out += V.booth_table(sc, TABLE_T[0], TABLE_T[1])
    return out


def banquette_faces():
    out = []
    for s0, L in BANQ:
        fr = Frame((s0, P2_T[0], 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
        out += bench(fr, L, back_detail=False)
    for sc in BANQ_TABLES:
        out += table2(sc, BANQ_T)
    return out


def ledge_faces():
    out = []
    (s0, s1), (t0, t1), z = LEDGE["s"], LEDGE["t"], LEDGE["z"]
    out += cbox(WORLD, s0, s1 - 0.03, t0, t1, z - 0.032, z, "terrazzo", grain="y", skip=("-x",))
    out += cbox(WORLD, s1 - 0.03, s1, t0 - 0.01, t1 + 0.01, z - 0.04, z + 0.004, "steel", ch=0.006, grain="y")
    for tt in (t0 + 0.18, (t0 + t1) / 2, t1 - 0.18):
        out += cbox(WORLD, s0, s0 + 0.02, tt - 0.015, tt + 0.015, z - 0.32, z - 0.032, "steel", grain="z")
        out += tube(WORLD, [(s0 + 0.02, tt, z - 0.30), (s1 - 0.06, tt, z - 0.035)], 0.008, 6, "steel")
    # foot rail (chrome tube on two posts)
    out += tube(WORLD, [(s0 + 0.12, t0 + 0.05, 0.22), (s0 + 0.12, t1 - 0.05, 0.22)], 0.019, 10, "steel", caps=True)
    for tt in (t0 + 0.05, t1 - 0.05):
        out += cbox(WORLD, s0, s0 + 0.13, tt - 0.012, tt + 0.012, 0.21, 0.23, "steel", grain="x")
    return out


def seating_collision_boxes():
    out = []
    for s0, L in BANQ:
        out.append(((s0, P2_T[0] - BENCH_D, FLOOR), (s0 + L, P2_T[0], 0.47), "LEATHER"))
        out.append(((s0, P2_T[0] - 0.12, FLOOR), (s0 + L, P2_T[0], 1.10), "LEATHER"))
    for sc in BANQ_TABLES:
        h = TABLE2 / 2
        out.append(((sc - h, BANQ_T - h, ZT - 0.05), (sc + h, BANQ_T + h, ZT), "WOOD_SOLID_MEDIUM"))
        out.append(((sc - 0.04, BANQ_T - 0.04, FLOOR), (sc + 0.04, BANQ_T + 0.04, ZT - 0.05), "METAL_SOLID_SMALL"))
    (s0, s1), (t0, t1), z = LEDGE["s"], LEDGE["t"], LEDGE["z"]
    out.append(((s0, t0, z - 0.04), (s1, t1, z), "WOOD_SOLID_MEDIUM"))
    return out


# ================================================================== 4. FLOOR: entry mat + grime decals
def _chamfer_frame():
    d = (PG.P_SW[0] - PG.P_NW[0], PG.P_SW[1] - PG.P_NW[1])
    L = math.hypot(*d)
    d2 = (d[0] / L, d[1] / L)
    n2 = (-d2[1], d2[0]) if (-d2[1] + d2[0]) > 0 else (d2[1], -d2[0])
    return d2, n2, L


def entry_mat():
    d2, n2, L = _chamfer_frame()
    um = (PG.D1["a"][0] + PG.D1["a"][1]) / 2
    c = (PG.P_NW[0] + d2[0] * um + n2[0] * 0.06, PG.P_NW[1] + d2[1] * um + n2[1] * 0.06)
    fr = Frame((c[0], c[1], 0.0), (d2[0], d2[1], 0.0), (n2[0], n2[1], 0.0), (0.0, 0.0, 1.0))
    out = []
    w, dep, hz = 1.70, 0.95, 0.008
    vs = [fr.p(-w / 2, 0.0, hz), fr.p(w / 2, 0.0, hz), fr.p(w / 2, dep, hz), fr.p(-w / 2, dep, hz)]
    emit(out, F(vs, "mat", [(1, 0), (0, 0), (0, 1), (1, 1)], hint=(0.0, 0.0, 1.0)))
    for (a0, a1, b0, b1) in ((-w / 2, w / 2, -0.02, 0.0), (-w / 2, w / 2, dep, dep + 0.02), (-w / 2 - 0.02, -w / 2, 0.0, dep), (w / 2, w / 2 + 0.02, 0.0, dep)):
        out += cbox(fr, a0, a1, b0, b1, FLOOR, hz, "rubber", grain="x")
    return out


def decal_quad(p0, du, dv, cell, z_up=True):
    """Quad p0 + a du + b dv (a, b in 0..1) with the atlas cell (u0, v0, u1, v1); 2 mm off the surface."""
    u0, v0, u1, v1 = cell
    vs = [p0, tuple(p0[k] + du[k] for k in range(3)), tuple(p0[k] + du[k] + dv[k] for k in range(3)), tuple(p0[k] + dv[k] for k in range(3))]
    n = V.cross(du, dv)
    return F(vs, "decal", [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=n)


FLOOR_WEAR = [(-0.55, 1.20, 0.9), (0.6, 1.7, 0.8), (2.3, 2.2, 0.8), (6.35, 1.6, 0.7), (6.35, 3.7, 0.7), (6.45, 5.1, 0.65)]


def decal_faces():
    out = []
    STRIP = (0.0, 1.0, 1.0, 0.5)            # wall-base grime: v=1 (strong) at the bottom
    BLOT = (0.0, 0.0, 0.5, 0.5)             # floor wear
    # wall-base grime in front of the tile, along all full runs (2 m pieces, gaps between them)
    for fr, runs, _ in wall_runs():
        for u0, u1, kind in runs:
            if kind != "full" or u1 - u0 < 0.4:
                continue
            u = u0 + 0.1
            while u < u1 - 0.3:
                L = min(1.6, u1 - u - 0.1)
                p0 = fr.p(u, 0.0155, FLOOR + 0.10)
                emit(out, decal_quad(p0, mul(fr.X, L), (0.0, 0.0, 0.26), STRIP))
                u += L + 0.9
    # floor wear: entrance path + counter queue + in front of the register (soft blotches)
    for (s, t, r) in FLOOR_WEAR:
        emit(out, decal_quad((s - r, t - r, FLOOR + 0.002), (2 * r, 0.0, 0.0), (0.0, 2 * r, 0.0), BLOT))
    return out


# ================================================================== 5. VANILLA PROPS (archetype names only)
from gs_v023_vb import VB_V023
VB.update(VB_V023)


def _wall_n(d2):
    return d2


def vanilla_props():
    """(name, s, t, z_bottom, yaw_deg) — z_bottom = world z of the model's lowest point."""
    out = []
    bs = BACK_S[0]
    zt = ZT
    yaw_in_p2 = wall_yaw((0.0, -1.0))           # front -> -t (into the hall from P2)
    yaw_in_sw = wall_yaw((0.0, 1.0))
    # ---- counter / back counter (kept from v0.2.1)
    out += [("prop_till_01", 7.45, 5.10, 1.02, 90.0), ("v_ret_ml_scale", COUNTER_FRONT + 0.63, 2.15, 1.305, 90.0),
            ("prop_coffee_mac_02", P1_S[0] - 0.012 - 0.21, 5.95, 0.92, -90.0),
            ("v_res_fa_bread01", bs + 0.30, 4.35, 0.92, 0.0), ("v_res_fa_bread02", bs + 0.30, 4.60, 0.92, 15.0),
            ("v_res_fa_chopbrd", bs + 0.32, 3.95, 0.92, 90.0), ("prop_cleaver", bs + 0.30, 3.95, 0.941, 80.0),
            ("prop_knife_stand", bs + 0.55, 5.25, 0.92, 0.0)]
    out += [("prop_bread_rack_02", 9.59, 0.62, 0.92, 0.0), ("v_res_tt_platepile", 9.55, 5.62, 0.92, 0.0),
            ("prop_radio_01", 9.80, 2.15, 0.92, -90.0),
            ("prop_paper_bag_small", 7.80, 4.95, 1.02, 10.0), ("prop_paper_bag_small", 7.84, 5.25, 1.02, -15.0),
            ("prop_paper_bag_01", 7.75, 6.70, 1.05, 90.0)]
    # coffee counter (customer side): sugar, napkins, ketchup / mustard, paper cups + stools
    out += [("prop_food_sugarjar", COUNTER_FRONT + 0.12, 5.80, 1.05, 0.0), ("prop_food_sugarjar", COUNTER_FRONT + 0.12, 6.50, 1.05, 0.0),
            ("prop_bar_napkindisp", COUNTER_FRONT + 0.14, 6.15, 1.05, 90.0),
            ("prop_food_ketchup", COUNTER_FRONT + 0.10, 5.98, 1.05, 0.0), ("prop_food_mustard", COUNTER_FRONT + 0.10, 6.04, 1.05, 0.0),
            ("prop_cs_paper_cup", COUNTER_FRONT + 0.40, 6.62, 1.05, 0.0), ("prop_cs_paper_cup", COUNTER_FRONT + 0.47, 6.66, 1.05, 0.0)]
    for tt in (5.70, 6.20, 6.70):
        out.append(("lr_prop_clubstool_01", COUNTER_FRONT - 0.42, tt, FLOOR, 0.0))
    # menus + stock on the P1 shelf (kept)
    mb = VB["v_19_vanmenuplain"]
    out += [("v_19_vanmenuplain", SG.MENU_BACK_S - mb[1][1], 1.30, 1.35, 90.0), ("v_19_vanmenuplain", SG.MENU_BACK_S - mb[1][1], 5.40, 1.35, 90.0)]
    out += [("winerow", P1_S[0] - 0.17, 2.62, 1.455, 90.0), ("winerow", P1_S[0] - 0.17, 3.05, 1.455, 90.0),
            ("winerow", P1_S[0] - 0.17, 3.85, 1.455, 90.0),
            ("v_res_foodjara", P1_S[0] - 0.13, 2.55, 1.895, 0.0), ("v_res_foodjarb", P1_S[0] - 0.13, 2.80, 1.895, 25.0),
            ("prop_metalfoodjar_01", P1_S[0] - 0.13, 3.35, 1.895, 0.0), ("prop_metalfoodjar_01", P1_S[0] - 0.13, 3.58, 1.895, 0.0),
            ("v_res_foodjarc", P1_S[0] - 0.13, 4.05, 1.895, 60.0)]
    # ---- booth tables (diner set-ups, no wine)
    (s1, _), (s2, _), (s3, _) = [table_center(a) for a in booth_bays()]
    for sc, setup in ((s1, "condiments"), (s2, "coffee"), (s3, "plates")):
        out += [("prop_bar_napkindisp", sc, -1.03, zt, 90.0)]
        if setup == "condiments":
            out += [("prop_food_ketchup", sc + 0.14, -1.05, zt, 0.0), ("prop_food_mustard", sc + 0.21, -1.04, zt, 0.0),
                    ("prop_food_sugarjar", sc - 0.15, -1.04, zt, 0.0), ("v_ret_fh_plate1", sc - 0.18, -0.55, zt, 0.0)]
        elif setup == "coffee":
            out += [("v_res_mp_ashtraya", sc + 0.16, -1.00, zt, 0.0), ("v_res_mmug", sc - 0.18, -0.50, zt, 30.0),
                    ("v_res_mmug", sc + 0.17, -0.62, zt, 200.0), ("prop_food_sugarjar", sc - 0.14, -1.05, zt, 0.0)]
        else:
            out += [("prop_food_ketchup", sc - 0.15, -1.05, zt, 0.0), ("v_ret_fh_plate1", sc - 0.18, -0.58, zt, 0.0),
                    ("v_ret_fh_plate1", sc + 0.17, -0.40, zt, 75.0), ("v_res_mp_ashtraya", sc + 0.15, -1.00, zt, 0.0)]
    # ---- banquette tables + chairs (front of the chairs -> the table, +t)
    for k, sc in enumerate(BANQ_TABLES):
        tw = BANQ_T + 0.25
        out += [("prop_bar_napkindisp", sc - 0.13, tw, zt, 0.0)]
        if k % 2 == 0:
            out += [("prop_food_ketchup", sc + 0.06, tw + 0.02, zt, 0.0), ("prop_food_mustard", sc + 0.13, tw + 0.02, zt, 0.0),
                    ("v_res_mp_ashtraya", sc + 0.17, BANQ_T - 0.15, zt, 0.0)]
        else:
            out += [("prop_food_sugarjar", sc + 0.08, tw + 0.02, zt, 0.0), ("v_ret_gc_cup", sc - 0.15, BANQ_T - 0.18, zt, 0.0),
                    ("v_ret_gc_cup", sc + 0.16, BANQ_T - 0.12, zt, 0.0)]
        out.append(("v_ret_gc_chair02", sc, BANQ_T - 0.66, FLOOR, wall_yaw((0.0, 1.0))))
    # ---- window bar ledge (W2): stools + condiments
    for tt in (3.95, 4.95, 5.95):
        out.append(("prop_bar_stool_01", LEDGE["s"][1] + 0.34, tt, FLOOR, 0.0))
    zl = LEDGE["z"]
    out += [("prop_bar_napkindisp", PG.XW + 0.12, 4.45, zl, 90.0), ("prop_food_ketchup", PG.XW + 0.12, 5.40, zl, 0.0),
            ("prop_food_mustard", PG.XW + 0.12, 5.47, zl, 0.0), ("prop_cs_paper_cup", PG.XW + 0.22, 4.95, zl, 0.0),
            ("v_res_mp_ashtraya", PG.XW + 0.15, 3.80, zl, 0.0)]
    # ---- P2 photo wall over the banquettes + the regulars' pinned photos near the register
    zw = P2_T[0]
    def on_p2(name, s, zb):
        b = VB[name]
        return (name, s, zw - (b[1][1] + 0.003), zb, yaw_in_p2)
    out += [on_p2("v_med_wallpicture1", -1.10, 1.48), on_p2("ch_prop_vault_painting_01a", 0.85, 1.36),
            on_p2("v_ret_gc_clock", 1.80, 2.18), on_p2("v_med_wallpicture2", 2.75, 1.42),
            on_p2("ch_prop_vault_painting_01c", 4.65, 1.36)]
    for k, (nm, ds, dz) in enumerate((("prop_ped_pic_01", 0.0, 0.0), ("prop_ped_pic_02", 0.33, 0.06), ("prop_ped_pic_05", 0.08, 0.40),
                                      ("prop_ped_pic_07", 0.40, 0.44))):
        out.append(on_p2(nm, 5.95 + ds, 1.30 + dz))
    out.append(("prop_fire_exting_1a", 5.92, P2_T[0] - 0.14, FLOOR, yaw_in_p2))
    # ---- Hero Zone A pier (SW wall): sconces, founder portrait + picture light (kept); clock over the entrance (kept)
    sw = VB["v_ret_fh_walllighton"]
    out += [("v_ret_fh_walllighton", 5.93, PG.YS + sw[1][1], 1.66 + sw[0][2], yaw_in_sw),
            ("v_ret_fh_walllighton", (PG.P_SW[0] + PG.W1["s"][0] - PG.CASING_W) / 2, PG.YS + sw[1][1], 1.66 + sw[0][2], yaw_in_sw)]
    pic = VB["ch_prop_vault_painting_01e"]
    out += [("ch_prop_vault_painting_01e", 6.47, PG.YS + pic[1][1] + 0.002, 1.40, yaw_in_sw),
            ("ch_chint02_picture_light", 6.47, PG.YS + 0.06, 1.40 + (pic[1][2] - pic[0][2]), yaw_in_sw)]
    d2, n2, L = _chamfer_frame()
    ch_mid = (PG.P_NW[0] + d2[0] * L / 2, PG.P_NW[1] + d2[1] * L / 2)
    ck = VB["prop_game_clock_01"]
    out += [("prop_game_clock_01", ch_mid[0] + n2[0] * ck[1][1], ch_mid[1] + n2[1] * ck[1][1], 2.99 - 0.216, wall_yaw(n2))]
    # ---- entrance: ATM on the chamfer (the awning says ATM), drinks cooler on the NW wall, plant in the corner
    u = 0.85
    pa = (PG.P_NW[0] + d2[0] * u, PG.P_NW[1] + d2[1] * u)
    atm = VB["prop_atm_01"]
    out.append(("prop_atm_01", pa[0] + n2[0] * (atm[1][1] + 0.02), pa[1] + n2[1] * (atm[1][1] + 0.02), FLOOR, wall_yaw(n2)))
    fz = VB["v_ret_ml_fridge02"]
    out.append(("v_ret_ml_fridge02", PG.XW + fz[1][1] + 0.02, 2.95, FLOOR, wall_yaw((1.0, 0.0))))
    out.append(("v_res_rubberplant", -2.45, 6.60, FLOOR, 30.0))
    # ---- beer neons in the windows (face the street) — matches BEER & WINE on the awning
    out += [("prop_beer_neon_02", 1.985, -1.30, 1.39, wall_yaw((0.0, -1.0))), ("prop_beer_neon_03", 4.92, -1.30, 1.47, wall_yaw((0.0, -1.0))),
            ("prop_beer_neon_04", -2.97, 5.75, 1.75, wall_yaw((-1.0, 0.0)))]
    # ---- ceiling technology: smoke detectors + sprinklers in tile centres; wall sockets
    for (i, j) in ((-1, 7), (6, 2)):
        out.append(("v_res_fa_smokealarm", (i + 0.5) * P, (j + 0.5) * P, CEIL - 0.059, 0.0))
    for (i, j) in ((-3, 6), (-1, 3), (1, 0), (3, 3), (5, 0), (7, 3), (1, 8), (5, 8), (9, 6)):
        out.append(("v_ilev_fib_sprklr", (i + 0.5) * P, (j + 0.5) * P, CEIL - 0.074, 0.0))
    so = VB["v_res_tre_plugsocket"]
    out += [("v_res_tre_plugsocket", 6.45, P2_T[0] - (so[1][1] + 0.016), 0.24, yaw_in_p2),
            ("v_res_tre_plugsocket", 6.75, PG.YS + so[1][1] + 0.016, 0.24, yaw_in_sw)]
    # ---- ceiling vanilla (booth + queue pendants)
    _, _, van = ceiling_fixtures()
    out += van
    return out


def vanilla_entities():
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        mn = VB[name][0]
        out.append((name, (round(s, 4), round(t, 4), round(zb - mn[2], 4)), math.radians(yaw)))
    return out


# ================================================================== 6. LIGHTS, COLLISION, EVERYTHING
def lights():
    _, L, _ = ceiling_fixtures()
    sconce_flags = ("not_in_reflection",)
    C_AMB = (1.0, 0.64, 0.36)
    L += [LT("sconce", "POINT", (5.93, PG.YS + 0.20, 1.72), C_AMB, 1.4, 1.8, 8.0, flags=sconce_flags, corona=(0.35, 0.6)),
          LT("sconce", "POINT", ((PG.P_SW[0] + PG.W1["s"][0] - PG.CASING_W) / 2, PG.YS + 0.20, 1.72), C_AMB, 1.4, 1.8, 8.0,
             flags=sconce_flags, corona=(0.35, 0.6)),
          LT("picture_light", "SPOT", (6.47, PG.YS + 0.30, 2.25), (1.0, 0.82, 0.60), 3.0, 1.7, 8.0, aim=(0.0, -0.32, -0.95),
             cone=(42.0, 18.0), flags=("static_shadows", "not_in_reflection"))]
    for t0, t1 in CASES_T:
        for f in (0.28, 0.72):
            L.append(LT("case", "POINT", (COUNTER_FRONT + 0.45, t0 + (t1 - t0) * f, 1.20), C_CASE, 1.2, 1.2, 4.0,
                        flags=("dont_light_alpha", "not_in_reflection")))
    # beer neons: coloured accent spill on the room side (the tubes themselves are emissive)
    L += [LT("neon_spill", "POINT", (1.985, -1.10, 1.95), (1.0, 0.30, 0.22), 1.2, 2.0, 4.0, flags=FILL_FLAGS),
          LT("neon_spill", "POINT", (4.92, -1.10, 1.95), (0.35, 0.55, 1.0), 1.2, 2.0, 4.0, flags=FILL_FLAGS),
          LT("neon_spill", "POINT", (-2.75, 5.65, 1.85), (1.0, 0.62, 0.20), 1.0, 1.8, 4.0, flags=FILL_FLAGS)]
    return L


def ceiling_faces_all():
    f, _, _ = ceiling_fixtures()
    return ceiling_faces() + f + menu_boards()


def hall_faces():
    out = []
    out += wall_kit_faces()
    out += ceiling_faces_all()
    out += booths_faces()
    out += banquette_faces()
    out += ledge_faces()
    out += V.counters_faces()
    # (Italian tricolore of the old "Gabagool" concept removed in v0.2.3: LONG PIG follows its own exterior)
    out += entry_mat()
    out += decal_faces()
    return out


def collision_boxes():
    out = []
    for (mn, mx, m) in V.booth_collision_boxes() + V.counter_collision_boxes() + seating_collision_boxes():
        out.append(((mn[0], mx[0], mn[1], mx[1], mn[2], mx[2]), m))
    return out + SG.partition_collision_boxes()


box_tris = SG.box_tris
SEATS = {"booths": 4 * N_BOOTHS, "banquettes": len(BANQ_TABLES), "chairs": len(BANQ_TABLES), "ledge": 3, "counter": 3}
