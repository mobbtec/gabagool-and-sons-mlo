# LONG PIG — v0.2.4 "red armchair lounge": a new section in the middle of the 90s lobby (on top of gs_v023_kit).
# * pony wall (red tile both faces, cream laminate cap, chrome rail) that separates the lounge from the door->counter path
# * 6 ORIGINAL red-vinyl tub armchairs (channel-tufted inner back, rolled top, piped cushion, chrome swivel base) in two
#   conversation groups around round coffee tables, a side table with a drum lamp, opal globe pendants over the tables,
#   an ORIGINAL 90s confetti rug (lp3_rug, slot 10 = the removed flag material)
# * vanilla dressing by archetype name only: jukebox, gumball machines, tall plant, table set-ups, cups on the rail cap
# Pure Python (face dicts); consumed by gs_20 (build) and gs_21 (preview) exactly like gs_v023_kit.
import math
import gs_v023_kit as K3
from gs_v023_kit import *          # noqa: F401,F403  (re-export the v0.2.3 kit API: MAT, VB, LT, CORONA, cpv_hall, ...)
from gs_v023_kit import (V, PG, WORLD, Frame, F, emit, cbox, prism, lathe, tube, FLOOR, CEIL, LT, CORONA,
                         C_TUNGSTEN, FILL_FLAGS, wall_yaw, VB, P)
grid, disc_cap = V.grid, V.disc_cap

C_AMBER = V.C_AMBER
# ------------------------------------------------------------------ materials: slot 10 (old flag) -> rug
RUG = MAT["flag"]                                      # same slot index, new texture (flag removed in v0.2.3)
SHADER_SPECS = list(K3.SHADER_SPECS)
SHADER_SPECS[RUG] = ("normal_spec.sps", {"DiffuseSampler": "lp3_rug", "BumpSampler": "lp_flat_n", "SpecSampler": "lp_matte_s"},
                     {"specularIntensityMult": 0.15, "specularFalloffMult": 6.0, "specularFresnel": 0.97, "bumpiness": 0.3}, "lp3_rug")

# ------------------------------------------------------------------ layout (MLO-local s, t)
PONY = dict(s=(-0.45, 4.80), t=(1.96, 2.10), top=0.93)      # half wall between the path (south) and the lounge (north)
CAP_Z = 0.962
RAIL_Z = 1.235
TC = 3.10                                                   # lounge row centre line
GROUPS = [0.70, 3.60]                                       # coffee-table centres (s)
CH_DS, CH_DN = 0.76, 0.76                                   # armchair offsets from the table (side, north)
SIDE_TABLE = (2.15, TC)
RUG_RECT = (-0.50, 4.80, 2.40, 3.725)                       # 5.30 x 1.325 m (texture 4 : 1)
CT_R, CT_Z = 0.28, 0.452                                    # coffee table radius / top
ST_R, ST_Z = 0.20, 0.562                                    # side table
PENDANT_Z = 2.24                                            # opal globe centre

# floor wear: move the blotch that was under the new pony wall onto the path
K3.FLOOR_WEAR[:] = [w for w in K3.FLOOR_WEAR if not (abs(w[0] - 2.3) < 0.01 and w[1] in (2.2, 1.30))] + [(2.3, 1.30, 0.75)]

CAM_VIEWS = dict(K3.CAM_VIEWS)
CAM_VIEWS.update({
    "VG": ((-1.5, 1.0, 1.62), (3.0, 3.4, 0.7), "red armchair lounge from the entrance"),
    "VH": ((4.95, 4.55, 1.60), (0.8, 2.7, 0.6), "lounge from the jukebox"),
    "VI": ((1.90, 1.55, 1.40), (0.55, 3.30, 0.55), "armchair group close-up over the rail"),
})


def chairs():
    """(s, t, front2) of the 6 armchairs."""
    out = []
    for sc in GROUPS:
        out += [(sc - CH_DS, TC, (1.0, 0.0)), (sc + CH_DS, TC, (-1.0, 0.0)), (sc, TC + CH_DN, (0.0, -1.0))]
    return out


# ================================================================== 1. pony wall + rail
def pony_wall_faces():
    out = []
    (s0, s1), (t0, t1), top = PONY["s"], PONY["t"], PONY["top"]
    L = s1 - s0
    out += cbox(WORLD, s0, s1, t0, t1, FLOOR, top, "walnut", grain="x", skip=("-y", "+y", "-z", "+z"))      # core ends
    fr_s = Frame((s0, t0, 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
    fr_n = Frame((s1, t1, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    out += K3.tile_wainscot(fr_s, 0.0, L, top)
    out += K3.tile_wainscot(fr_n, 0.0, L, top)
    # stainless corner trims over the ends
    for a0, a1 in ((s0 - 0.018, s0), (s1, s1 + 0.018)):
        out += cbox(WORLD, a0, a1, t0 - 0.018, t1 + 0.018, FLOOR, top, "steel", ch=0.003, grain="z")
    # cream laminate cap with stainless nosings (drink ledge)
    out += cbox(WORLD, s0 - 0.03, s1 + 0.03, t0 - 0.035, t1 + 0.035, top, CAP_Z, "terrazzo", ch=0.004, grain="x")
    for tt0, tt1 in ((t0 - 0.041, t0 - 0.035), (t1 + 0.035, t1 + 0.041)):
        out += cbox(WORLD, s0 - 0.03, s1 + 0.03, tt0, tt1, top - 0.006, CAP_Z + 0.002, "steel", grain="x")
    # chrome rail: posts with flanges + top rail
    tm = (t0 + t1) / 2
    xs = rail_posts()
    for x in xs:
        fr = WORLD.child(x, tm, 0.0)
        out += lathe(fr, [(0.036, CAP_Z), (0.036, CAP_Z + 0.006), (0.022, CAP_Z + 0.014), (0.0, CAP_Z + 0.014)], 12, "steel")
        out += tube(WORLD, [(x, tm, CAP_Z + 0.012), (x, tm, RAIL_Z)], 0.016, 8, "steel")
    out += tube(WORLD, [(xs[0], tm, RAIL_Z), (xs[-1], tm, RAIL_Z)], 0.021, 10, "steel", caps=True)
    for x in (xs[0], xs[-1]):                                       # ball ends
        fr = WORLD.child(x, tm, 0.0)
        out += lathe(fr, [(0.0, RAIL_Z - 0.03)] + [(0.03 * math.sin(math.radians(a)), RAIL_Z - 0.03 * math.cos(math.radians(a)))
                                                    for a in (30, 60, 90, 120, 150)] + [(0.0, RAIL_Z + 0.03)], 12, "steel")
    return out


def rail_posts():
    (s0, s1) = PONY["s"]
    a, b = s0 + 0.15, s1 - 0.15
    return [a + (b - a) * k / 4 for k in range(5)]


# ================================================================== 2. tub armchair (original)
RO, RI, RM = 0.36, 0.285, 0.322            # outer / inner / roll radius of the back shell
ZB, ZSK, ZS = FLOOR + 0.200, 0.400, 0.472  # shell bottom, skirt top, cushion top
SPAN = math.radians(125.0)                 # back shell from -125 deg to +125 deg (0 = rear)


def _h(a):
    """Top of the back at angle a (0 = rear): 0.80 at the rear, 0.62 at the arm ends."""
    return 0.60 + 0.20 * ((1.0 + math.cos(a)) / 2.0) ** 1.4


def _ring(r, a, z):
    return (r * math.sin(a), -r * math.cos(a), z)


def tub_chair(sc, tc, front):
    out = []
    yaw = math.atan2(-front[0], front[1])
    fr = WORLD.child(sc, tc, 0.0, yaw)              # local +Y = front, -Y = rear
    rep = V.REP["leather"]
    # chrome swivel base
    out += lathe(fr, [(0.215, FLOOR), (0.22, FLOOR + 0.008), (0.212, FLOOR + 0.02), (0.06, FLOOR + 0.04), (0.032, FLOOR + 0.07),
                      (0.028, ZB - 0.03), (0.04, ZB - 0.016), (0.15, ZB - 0.008), (0.15, ZB), (0.0, ZB)], 16, "steel", rep=0.5)
    # shell underside + chrome trim band
    out += disc_cap(fr, RO, ZB, 24, "leather", up=False)
    out += lathe(fr, [(RO + 0.004, ZB - 0.002), (RO + 0.006, ZB + 0.008), (RO + 0.004, ZB + 0.018)], 24, "steel")
    # skirt (seat body) all round
    out += lathe(fr, [(0.335, ZB), (0.342, (ZB + ZSK) / 2), (0.336, ZSK)], 24, "leather", rep=rep)
    # seat cushion (crowned) + piping
    out += lathe(fr, [(0.298, ZSK + 0.006), (0.303, ZSK + 0.034), (0.297, ZS - 0.016), (0.272, ZS - 0.004), (0.20, ZS + 0.002),
                      (0.0, ZS + 0.004)], 24, "leather", rep=rep)
    out += tube(fr, [(0.300 * math.cos(2 * math.pi * k / 24), 0.300 * math.sin(2 * math.pi * k / 24), ZS - 0.012) for k in range(25)],
                0.0055, 5, "leather")
    # back shell: outer wall
    def outer(u, v):
        a = -SPAN + 2 * SPAN * u
        r = RO + 0.006 * math.sin(math.pi * v)
        return _ring(r, a, ZB + (_h(a) - ZB) * v)
    out += grid(fr, outer, 24, 3, "leather", lambda u, v: (u * 2 * SPAN * RO / rep, v * 0.6 / rep),
                hint_fn=lambda u, v: (math.sin(-SPAN + 2 * SPAN * u), -math.cos(-SPAN + 2 * SPAN * u), 0.0))
    # inner face: 9 channel-tufted pillows
    n = 9
    for k in range(n):
        a0, a1 = -SPAN + 2 * SPAN * k / n, -SPAN + 2 * SPAN * (k + 1) / n

        def pillow(u, v, a0=a0, a1=a1):
            a = a0 + (a1 - a0) * u
            top = _h(a) - 0.032
            bulge = 0.004 + 0.034 * (math.sin(math.pi * u) ** 0.55) * (math.sin(math.pi * v) ** 0.35)
            return _ring(RI - bulge, a, ZS - 0.01 + (top - ZS + 0.01) * v)
        out += grid(fr, pillow, 3, 6, "leather",
                    lambda u, v, a0=a0, a1=a1, k=k: ((a0 + (a1 - a0) * u) * RI / rep + 0.37 * k, v * 0.3 / rep),
                    hint_fn=lambda u, v, a0=a0, a1=a1: (-math.sin(a0 + (a1 - a0) * u), math.cos(a0 + (a1 - a0) * u), 0.0))
    # rolled top
    out += tube(fr, [_ring(RM, -SPAN + 2 * SPAN * k / 24, _h(-SPAN + 2 * SPAN * k / 24)) for k in range(25)], 0.044, 8, "leather",
                caps=True)
    # arm-end faces (closing the shell between inner and outer radius)
    for a, sg in ((-SPAN, -1.0), (SPAN, 1.0)):
        hint = fr.v(sg * math.cos(a), sg * math.sin(a), 0.0)
        hz = _h(a)
        for (r0, r1, z0, z1) in ((RI, RO, ZSK, hz), (0.335, RO, ZB, ZSK)):
            vs = [fr.p(*_ring(r0, a, z0)), fr.p(*_ring(r1, a, z0)), fr.p(*_ring(r1, a, z1)), fr.p(*_ring(r0, a, z1))]
            emit(out, F(vs, "leather", [(0, 0), ((r1 - r0) / rep, 0), ((r1 - r0) / rep, (z1 - z0) / rep), (0, (z1 - z0) / rep)], hint=hint))
    return out


# ================================================================== 3. tables, lamp, pendants, rug
def round_table(sc, tc, R, zt):
    out = []
    fr = WORLD.child(sc, tc, 0.0)
    out += disc_cap(fr, R - 0.018, zt - 0.002, 28, "terrazzo", up=True)
    out += lathe(fr, [(R - 0.018, zt - 0.027), (R, zt - 0.024), (R + 0.003, zt - 0.014), (R, zt - 0.003), (R - 0.018, zt)], 28, "steel")
    out += disc_cap(fr, R - 0.006, zt - 0.026, 28, "walnut", up=False)
    out += lathe(fr, [(0.20 * R / 0.28, FLOOR), (0.205 * R / 0.28, FLOOR + 0.008), (0.19 * R / 0.28, FLOOR + 0.02), (0.05, FLOOR + 0.035),
                      (0.03, FLOOR + 0.06), (0.026, zt - 0.06), (0.07, zt - 0.045), (0.07, zt - 0.026), (0.0, zt - 0.026)], 16, "steel", rep=0.5)
    return out


def drum_lamp(sc, tc, zt):
    out = []
    fr = WORLD.child(sc, tc, 0.0)
    out += lathe(fr, [(0.072, zt), (0.074, zt + 0.01), (0.05, zt + 0.03), (0.012, zt + 0.042), (0.0, zt + 0.042)], 16, "steel")
    out += tube(WORLD, [(sc, tc, zt + 0.04), (sc, tc, zt + 0.40)], 0.009, 8, "steel")
    shade = [(0.135, zt + 0.22), (0.105, zt + 0.40)]
    out += lathe(fr, shade, 20, "opal")
    out += lathe(fr, shade[::-1], 20, "opal")                                       # inner face
    for z, r in ((zt + 0.22, 0.137), (zt + 0.40, 0.107)):                           # chrome rims
        out += tube(fr, [(r * math.cos(2 * math.pi * k / 20), r * math.sin(2 * math.pi * k / 20), z) for k in range(21)], 0.004, 4, "steel")
    out += lathe(fr, [(0.0, zt + 0.27), (0.028, zt + 0.29), (0.03, zt + 0.32), (0.0, zt + 0.35)], 10, "glow")
    return out


def globe_pendant(sc, tc):
    out = []
    fr = WORLD.child(sc, tc, 0.0)
    out += lathe(fr, [(0.0, CEIL - 0.03), (0.06, CEIL - 0.03), (0.065, CEIL - 0.018), (0.06, CEIL - 0.002), (0.0, CEIL - 0.002)][::-1], 16, "steel")
    gr = 0.16
    top = PENDANT_Z + gr * 0.92
    out += tube(WORLD, [(sc, tc, CEIL - 0.03), (sc, tc, top + 0.05)], 0.006, 6, "steel")
    out += lathe(fr, [(0.0, top + 0.05), (0.03, top + 0.05), (0.052, top + 0.01), (0.062, top - 0.005), (0.0, top - 0.005)][::-1], 16, "steel")
    prof = [(gr * math.sin(math.radians(a)), PENDANT_Z - gr * math.cos(math.radians(a))) for a in range(0, 157, 12)]
    out += lathe(fr, prof, 20, "opal")
    out += lathe(fr, [(0.0, PENDANT_Z - 0.035), (0.03, PENDANT_Z), (0.0, PENDANT_Z + 0.035)], 8, "glow")
    return out


def rug_faces():
    out = []
    s0, s1, t0, t1 = RUG_RECT
    z = FLOOR + 0.009
    emit(out, F([(s0, t0, z), (s1, t0, z), (s1, t1, z), (s0, t1, z)], RUG, [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(0.0, 0.0, 1.0)))
    edge = (0.004, 0.5)                                       # uv on the cream outer edge
    for a, b in (((s0, t0), (s1, t0)), ((s1, t0), (s1, t1)), ((s1, t1), (s0, t1)), ((s0, t1), (s0, t0))):
        n2 = (b[1] - a[1], -(b[0] - a[0]))
        vs = [(a[0], a[1], FLOOR), (b[0], b[1], FLOOR), (b[0], b[1], z), (a[0], a[1], z)]
        emit(out, F(vs, RUG, [edge] * 4, hint=(n2[0], n2[1], 0.0)))
    return out


def lounge_faces():
    out = []
    out += pony_wall_faces()
    out += rug_faces()
    for s, t, f in chairs():
        out += tub_chair(s, t, f)
    for sc in GROUPS:
        out += round_table(sc, TC, CT_R, CT_Z)
        out += globe_pendant(sc + (0.02 if sc < 1.0 else 0.0), TC)
    out += round_table(SIDE_TABLE[0], SIDE_TABLE[1], ST_R, ST_Z)
    out += drum_lamp(SIDE_TABLE[0], SIDE_TABLE[1] + 0.03, ST_Z)
    return out


# ================================================================== 4. vanilla dressing (archetype names only)
def lounge_vanilla():
    out = []
    (t0, t1) = PONY["t"]
    tm = (t0 + t1) / 2
    out += [("prop_jukebox_02", 5.40, 3.88, FLOOR, wall_yaw((-1.0, 0.0))),          # cream jukebox, faces the lounge / door
            ("prop_gumball_01", -0.15, 2.32, FLOOR, wall_yaw((-1.0, 0.0))),         # red twin gumball stand at the lounge entry
            ("prop_gumball_02", -0.85, 2.55, FLOOR, wall_yaw((-1.0, 0.0))),         # triple gumball on a pedestal
            ("prop_plant_int_01b", 5.15, 2.45, FLOOR, 20.0)]                         # tall plant closing the east end
    for k, sc in enumerate(GROUPS):
        z = CT_Z
        if k == 0:
            out += [("v_res_mp_ashtraya", sc - 0.08, TC - 0.08, z, 0.0), ("v_res_mmug", sc + 0.10, TC + 0.08, z, 40.0),
                    ("v_res_mmug", sc - 0.10, TC + 0.12, z, 200.0), ("prop_food_sugarjar", sc + 0.09, TC - 0.12, z, 0.0)]
        else:
            out += [("v_ret_gc_cup", sc - 0.10, TC - 0.08, z, 0.0), ("v_ret_gc_cup", sc + 0.10, TC + 0.10, z, 0.0),
                    ("v_res_mp_ashtraya", sc + 0.08, TC - 0.12, z, 0.0), ("prop_cs_paper_cup", sc - 0.12, TC + 0.10, z, 0.0)]
    out += [("v_res_mp_ashtraya", SIDE_TABLE[0] - 0.10, SIDE_TABLE[1] - 0.12, ST_Z, 0.0)]
    # drink ledge on the pony wall cap (between the rail posts)
    out += [("prop_cs_paper_cup", 1.40, tm - 0.05, CAP_Z, 0.0), ("prop_cs_paper_cup", 1.47, tm + 0.05, CAP_Z, 0.0),
            ("prop_bar_napkindisp", 3.00, tm, CAP_Z, 0.0)]
    out += [("v_ilev_fib_sprklr", 5.5 * P, 4.5 * P, CEIL - 0.074, 0.0)]
    return out


def vanilla_props():
    return K3.vanilla_props() + lounge_vanilla()


def vanilla_entities():
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        mn = VB[name][0]
        out.append((name, (round(s, 4), round(t, 4), round(zb - mn[2], 4)), math.radians(yaw)))
    return out


# ================================================================== 5. lights, collision, everything
def lounge_lights():
    L = []
    for sc in GROUPS:
        sp = sc + (0.02 if sc < 1.0 else 0.0)
        L.append(LT("lounge_pendant_key", "SPOT", (sp, TC, PENDANT_Z - 0.20), C_TUNGSTEN, 7.0, 3.2, 14.0, cone=(62.0, 28.0),
                    flags=("static_shadows", "not_in_reflection")))
        L.append(CORONA("lounge_globe", (sp, TC, PENDANT_Z), C_TUNGSTEN, 0.55, 0.6))
    L.append(LT("lounge_lamp", "POINT", (SIDE_TABLE[0], SIDE_TABLE[1] + 0.03, ST_Z + 0.31), C_AMBER, 1.6, 2.0, 8.0, flags=FILL_FLAGS))
    L.append(LT("jukebox_glow", "POINT", (4.55, 3.88, 1.05), (1.0, 0.55, 0.35), 1.0, 1.6, 6.0, flags=FILL_FLAGS))
    return L


def lights():
    return K3.lights() + lounge_lights()


def hall_faces():
    return K3.hall_faces() + lounge_faces()


def lounge_collision_boxes():
    out = []
    (s0, s1), (t0, t1), top = PONY["s"], PONY["t"], PONY["top"]
    out.append(((s0 - 0.03, s1 + 0.03, t0 - 0.04, t1 + 0.04, FLOOR, CAP_Z), "CONCRETE"))
    xs = rail_posts()
    out.append(((xs[0] - 0.03, xs[-1] + 0.03, (t0 + t1) / 2 - 0.025, (t0 + t1) / 2 + 0.025, CAP_Z, RAIL_Z + 0.025), "METAL_SOLID_SMALL"))
    for s, t, f in chairs():
        out.append(((s - 0.33, s + 0.33, t - 0.33, t + 0.33, FLOOR, ZS), "LEATHER"))
        bs = (s - f[0] * 0.29, t - f[1] * 0.29)                       # rear strip of the back
        hx = 0.07 if f[0] else 0.30
        hy = 0.30 if f[0] else 0.07
        out.append(((bs[0] - hx, bs[0] + hx, bs[1] - hy, bs[1] + hy, ZS, 0.82), "LEATHER"))
    for sc, tc, R, zt in [(g, TC, CT_R, CT_Z) for g in GROUPS] + [(SIDE_TABLE[0], SIDE_TABLE[1], ST_R, ST_Z)]:
        out.append(((sc - R, sc + R, tc - R, tc + R, zt - 0.03, zt), "WOOD_SOLID_MEDIUM"))
        out.append(((sc - 0.04, sc + 0.04, tc - 0.04, tc + 0.04, FLOOR, zt - 0.03), "METAL_SOLID_SMALL"))
    return out


def collision_boxes():
    return K3.collision_boxes() + lounge_collision_boxes()


SEATS = dict(K3.SEATS)
SEATS["lounge_armchairs"] = len(chairs())
