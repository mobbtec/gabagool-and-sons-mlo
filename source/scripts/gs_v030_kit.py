# LONG PIG — v0.3.0-a (owner 2026-11-12 14:28, in-game test of 0.2.9.1: "днём свет очень хороший, ночью прям испорчен";
# "коридор для персонала слишком пустой"). On top of the v0.2.9 kit:
#   NIGHT     the hall is still washed out after dark (the game raises exposure): every NIGHT copy (20:00-06:59) of the
#             hall / open-set / back-of-house lights is scaled again (keys x0.55, fills x0.65). Day copies untouched.
#   CORRIDOR  staff corridor dressed along the brick wall (free width stays >= 1.0 m): beer crates, cartons, broom, clock,
#             clipboard, coat hooks, notices. Vanilla props by archetype name only.
import math
import gs_v029_kit as K9
from gs_v029_kit import *                    # noqa: F401,F403
import gs_boh29_kit as B9

VERSION = "1.9.3"
# 0.3.1-c ANIMATED BLINDS (revision): the slats of the four 'open' blind panes are
# no longer part of the hall drawable - they are the prop lp_blind_slat (gs_44_build_props.py), spawned and turned by
# client/blinds.lua from client/blinds_data.lua (gs_49_blinds_data.py). Headrails, chains and the stacked pane stay static.
import gs_v026_kit as K6
if not hasattr(K6, "_slat_static"):
    K6._slat_static = K6._slat
    K6._blind_pane_static = K6.blind_pane
_PANE = {"animated": False}


def _slat_030(out, fr, u, d0, z0, z1, ang, ci, tilt=0.0):
    if _PANE["animated"]:
        return K6._slat_static([], fr, u, d0, z0, z1, ang, ci, tilt)      # same bead-chain anchor, no faces
    return K6._slat_static(out, fr, u, d0, z0, z1, ang, ci, tilt)


if not hasattr(K6, "_tube_static"):
    K6._tube_static = K6.tube


def _tube_030(fr, pts, *a, **k):
    if _PANE["animated"] and len(pts) == 3:          # 0.3.1-d: bead chain between slat bottoms - the slats move now
        return []
    return K6._tube_static(fr, pts, *a, **k)


K6.tube = _tube_030


def _blind_pane_030(fr, a, b, d0, pattern, seed):
    _PANE["animated"] = pattern[0] == "open"
    try:
        return K6._blind_pane_static(fr, a, b, d0, pattern, seed)
    finally:
        _PANE["animated"] = False


# 0.3.1-d (owner screenshot: stretched stripes on the reveal next to the entrance): 10 reveal faces of the shell had a
# constant U -> the texture was smeared sideways. U now runs across the reveal at the scale of V.
import gs_proto_geometry as _PG
if not hasattr(_PG, "_shell_faces_static"):
    _PG._shell_faces_static = _PG.shell_faces


def _shell_faces_030(*a, **k):
    out = _PG._shell_faces_static(*a, **k)
    fixed = 0
    for f in out:
        if not isinstance(f, dict) or len(f.get("uv", ())) != len(f.get("v", ())) or len(f["v"]) < 3:
            continue
        us = [u for u, _ in f["uv"]]
        vs_ = [v for _, v in f["uv"]]
        zs = [p[2] for p in f["v"]]
        if max(us) - min(us) > 1e-4 or max(vs_) - min(vs_) < 1e-4 or max(zs) - min(zs) < 0.3:
            continue
        sc = (max(vs_) - min(vs_)) / (max(zs) - min(zs))
        p0 = f["v"][0]
        hs = [math.hypot(p[0] - p0[0], p[1] - p0[1]) for p in f["v"]]
        if max(hs) < 0.05:
            continue
        f["uv"] = [(us[0] + h * sc, v) for h, v in zip(hs, vs_)]
        fixed += 1
    _shell_faces_030.fixed = fixed
    return out


_PG.shell_faces = _shell_faces_030


K6._slat = _slat_030
K6.blind_pane = _blind_pane_030
STREET = True                                # taco kiosk + signs removed, patio cap (gs_overrides STREET section)
NIGHT2 = {"troffer": 0.55, "banquette_key": 0.55, "soffit_can": 0.55, "entrance_can": 0.55, "ledge_can": 0.60,
          "boh_troffer": 0.60, "boh_wc_cage": 0.70}
NIGHT2_DEFAULT = 0.65
# 0.3.0-d (revision): one more step down for every night copy
NIGHT2 = {k: round(v * 0.8 * 0.72, 3) for k, v in NIGHT2.items()}   # 0.3.0-e: "уже лучше, но ещё темнее"
NIGHT2_DEFAULT = 0.38
YB = 7.07                                    # corridor face of the hall back wall (brick)
YR = 8.42 - B9.WT / 2                        # corridor face of P3 (rooms)


def _night2(L):
    out = []
    for l in L:
        if l.get("time") == NIGHT_HOURS:
            k = l["kind"]
            fam = "troffer" if k.startswith("troffer_lamp") else k
            l = dict(l, intensity=round(l["intensity"] * NIGHT2.get(fam, NIGHT2_DEFAULT), 3))
        out.append(l)
    return out


def lights():
    return _night2(K9.lights())


def open_lights():
    # 0.3.1-o (revision): the price board in the window (former OPEN neon) and
    # its glow light are gone
    L = [l for l in K9.open_lights() if l["kind"] != "open_neon_glow"]
    return _night2(L)


K9.neon_faces = lambda mat_neon: []


def boh_lights():
    return _night2(B9.boh_lights())


def corridor_props():
    F0 = B9.FLOOR
    up = (0.0, 1.0)                           # normal of the brick wall into the corridor
    out = []
    # beer crates stacked against the brick wall (0.27 deep -> 1.0 m stays free)
    for k, (ds, yaw) in enumerate(((0.0, 0.0), (0.02, 4.0), (-0.01, -3.0), (0.01, 2.0))):
        out.append(("prop_beer_box_01", 4.60 + ds, YB + 0.02 + 0.135, F0 + 0.13 * k, yaw))
    for k, (ds, yaw) in enumerate(((0.0, 3.0), (0.015, -5.0))):
        out.append(("prop_beer_box_01", 5.08 + ds, YB + 0.02 + 0.135, F0 + 0.13 * k, yaw))
    out += [("v_ind_cfbox", 5.62, YB + 0.02 + 0.12, F0, 6.0), ("v_ind_cfbox", 5.63, YB + 0.02 + 0.12, F0 + 0.31, -8.0),
            ("v_ind_cfbox", 5.95, YB + 0.02 + 0.12, F0, -4.0)]
    out.append(("prop_tool_broom", 2.25, YB + 0.10, F0, 0.0))
    out.append(B9._on_wall("v_ret_gc_clock", (3.60, YB), up, 2.05))
    out.append(B9._on_wall("prop_fib_clipboard", (6.95, YB), up, 1.35))
    out.append(B9._on_wall("prop_coathook_01", (1.55, YB), up, 1.70))
    out.append(B9._on_wall("prop_fib_clipboard", (5.30, YR), (0.0, -1.0), 1.40))
    return out


def boh_extra():
    """0.3.1-g (owner: "пропы в кухне и подсобке"): a few more vanilla props, checked with gs_43_layout_check.py."""
    F0 = B9.FLOOR
    out = []
    # (a sack truck and a carton stack for the storage were dropped: the audit showed both spots are already taken)
    out.append(B9._on_wall("v_ret_gc_clock", (14.50, B9.YS + 0.009), (0.0, 1.0), 2.05))             # kitchen, SW wall
    out.append(B9._on_wall("prop_fib_clipboard", (12.80 - B9.WT / 2, 8.25), (-1.0, 0.0), 1.45))     # storage, stock sheet
    F0 = B9.FLOOR
    up = (0.0, 1.0)
    # corridor: jacket on the existing hook, a six-pack on the beer crates
    out.append(B9._on_wall("v_club_roc_jacket2", (1.62, YB), up, 1.00))
    out.append(("v_ret_ml_6bottles", 5.08, YB + 0.02 + 0.135, F0 + 0.26, 4.0))
    # kitchen: cup rack on the SW wall (right of the clock)
    out.append(B9._on_wall("v_res_tre_cuprack", (15.20, B9.YS + 0.009), up, 1.45))
    # storage: top deck of the stock rack
    out.append(("v_serv_plastic_box", 10.33, 8.84, 1.835, 0.0))                 # (bottom z; rack collision top 1.83)
    out.append(("v_serv_plastic_box_lid", 10.33, 8.84, 1.835 + 0.47, 0.0))
    out.append(("prop_cs_cardbox_01", 10.30, 9.45, 1.835, 2.0))
    # staff room: water cooler + soda machine on the west wall, jacket on a hook by the door
    out.append(B9._against("prop_water_bottle", (0.60 + B9.WT / 2, 8.80), (1.0, 0.0)))
    out.append(B9._against("prop_vend_soda_02", (0.60 + B9.WT / 2, 9.75), (1.0, 0.0)))
    out.append(B9._on_wall("prop_coathook_01", (1.65, 8.42 + B9.WT / 2), up, 1.70))
    out.append(B9._on_wall("v_club_roc_jacket2", (1.60, 8.42 + B9.WT / 2), up, 1.00))
    # (office safe / plant dropped: the audit found no free floor there)
    out.append(B9._on_wall("prop_fib_clipboard", (14.12, B9.YS + 0.009), (0.0, 1.0), 1.45))
    return out


def vanilla_props():
    return K9.vanilla_props() + corridor_props() + boh_extra()


def vanilla_entities():
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        out.append(K9._ent(name, s, t, zb, yaw))
    for did, arch, pos, yaw in K9.all_doors():
        out.append((arch, pos, yaw))
    return out


# 0.3.1-j BACK-OF-HOUSE FINISHES (owner 2026-11-13: "лучше текстуры на кухне / в коридоре; только из интернета или
# Higgsfield"): the BOH drawable gets its own CC0 Poly Haven sets (gs_15s_cc0_v031.py) for the three wall / floor
# materials; the hall keeps its textures. UVs of those faces are rescaled so one texture repeat = the real size.
# 0.3.1-l (owner 21:43: the plaster "too dirty"): lp9_boh_plaster = Poly Haven painted_plaster_wall, 2.0 m (gs_15t_cc0_v031l.py);
# the dirt is now LOCAL (leak decals, see leak_faces) instead of one blotchy texture on every wall.
_BOH_CC0 = {"tile_white": ("lp9_boh_tile", 1.27), "plaster": ("lp9_boh_plaster", 2.0), "tile": ("lp9_boh_floor", 2.08)}
BOH_SPECS = list(K9.BOH_SPECS)
for _m, (_tx, _size) in _BOH_CC0.items():
    _i = B9.BOH_MATS.index(_m)
    _sh, _smp, _prm, _nm = BOH_SPECS[_i]
    BOH_SPECS[_i] = ("normal_spec.sps", {"DiffuseSampler": _tx, "BumpSampler": _tx + "_n", "SpecSampler": _tx + "_s"},
                     {"specularIntensityMult": 1.0, "specularFalloffMult": 40.0 if _m != "plaster" else 12.0,
                      "specularFresnel": 0.97, "bumpiness": 1.0}, _tx)
_BOH_CC0_IDX = {B9.BOH_MATS.index(m): size for m, (_t, size) in _BOH_CC0.items()}
# 0.3.1-l: two BOH-only materials, used by index (no remap): CC0 leak decals and the ceiling tile (for the fallen tile)
LEAK_IDX = len(BOH_SPECS)
BOH_SPECS.append(("decal.sps", {"DiffuseSampler": "lp9_boh_leaks"}, {}, "lp9_boh_leaks"))
CEILT_IDX = len(BOH_SPECS)
BOH_SPECS.append(("normal_spec.sps", {"DiffuseSampler": "lp9_ceil_tile1", "BumpSampler": "lp_flat_n", "SpecSampler": "lp_matte_s"},
                  {"specularIntensityMult": 0.3, "specularFalloffMult": 6.0, "specularFresnel": 0.97, "bumpiness": 1.0},
                  "lp9_ceil_tile1"))                                  # one 256 px cell of the ceiling sheet (memory)


# 0.3.1-l (owner screenshot of the office: shelf on three grey blocks): the shelf brackets were solid plates seen side-on
# as cubes. Now real L-brackets: thin wall strip + arm under the board + round diagonal brace (all back-of-house shelves).
import gs_boh_kit as _BK


def _wall_shelf_031l(p0, p1, n, z, depth=0.30, mat="steel"):
    out = []
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    fr = Frame((p0[0], p0[1], 0.0), (d[0], d[1], 0.0), (n[0], n[1], 0.0), (0.0, 0.0, 1.0))
    out += B9.cbox(fr, 0.0, L, 0.0, depth, z - 0.025, z, mat, grain="x")
    out += B9.cbox(fr, 0.0, L, depth - 0.02, depth, z, z + 0.03, mat, grain="x")
    nb = 2 if L < 1.3 else 3
    for k in range(nb):
        u = 0.1 + (L - 0.2) * k / (nb - 1)
        out += B9.cbox(fr, u - 0.012, u + 0.012, 0.0, 0.004, z - 0.20, z - 0.025, "steel")              # wall strip
        out += B9.cbox(fr, u - 0.012, u + 0.012, 0.0, depth - 0.04, z - 0.029, z - 0.025, "steel")      # arm
        out += K6.tube(B9.WORLD, [fr.p(u, 0.006, z - 0.185), fr.p(u, depth - 0.07, z - 0.031)], 0.005, 6, "steel")   # brace
    return out


_BK.wall_shelf = _wall_shelf_031l
B9.wall_shelf = _wall_shelf_031l


def _rescale_uv(f, size):
    """World-mapped UVs: scale about the first vertex so 1.0 UV = size metres (measured on the face itself)."""
    P = [tuple(map(float, v)) for v in f["v"]]
    U = [tuple(map(float, u)) for u in f["uv"]]
    best = 0.0
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            dg = math.dist(P[i], P[j])
            if dg > 0.05:
                best = max(best, math.dist(U[i], U[j]) / dg)
    if best <= 1e-6:
        return f
    k = (1.0 / size) / best
    u0 = U[0]
    return dict(f, uv=[(u0[0] + (u[0] - u0[0]) * k, u0[1] + (u[1] - u0[1]) * k) for u in U])


def _pipe_run(p0, p1, z, r, mat="iron", brackets=1.4):
    """Exposed pipe under the ceiling from p0 to p1 (s, t) at height z, with flat steel straps up to the ceiling."""
    out = []
    out += K6.tube(B9.WORLD, [(p0[0], p0[1], z), (p1[0], p1[1], z)], r, 8, mat)
    L = math.dist(p0, p1)
    n = max(1, int(L / brackets))
    for k in range(n + 1):
        f = 0.04 + 0.92 * k / n
        x, y = p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f
        out += B9.cbox(B9.WORLD, x - 0.015, x + 0.015, y - r - 0.006, y + r + 0.006, z - r - 0.008, B9.CEIL - 0.01, "steel")
    return out


def pipes_faces():
    """0.3.1-k (owner: "больше деталей в коридоре, на кухне, в помещениях"): exposed water / gas pipes and a conduit."""
    C = B9.CEIL
    out = []
    out += _pipe_run((0.60, 7.24), (9.95, 7.24), C - 0.20, 0.032)                 # corridor, along the brick wall
    out += _pipe_run((0.60, 7.36), (9.95, 7.36), C - 0.14, 0.020, mat="steel")
    out += _pipe_run((0.60, 8.30), (9.95, 8.30), C - 0.08, 0.012, mat="steel")    # electrical conduit
    out += _pipe_run((10.10, 4.86), (16.10, 4.86), C - 0.22, 0.028)              # kitchen, along the pass wall
    out += _pipe_run((10.10, 11.30), (16.10, 11.30), C - 0.20, 0.032)            # storage, along the back wall
    out += _pipe_run((10.10, 11.18), (16.10, 11.18), C - 0.12, 0.016, mat="steel")
    out += _pipe_run((0.70, 11.30), (5.50, 11.30), C - 0.18, 0.025)              # staff room
    return out


def boh_extra_faces():
    """0.3.1-j: more paper on the empty back-of-house walls (storage cooler wall, kitchen pass wall)."""
    out = []
    wc = 12.80 - B9.WT / 2 - 0.001                                       # storage side of the cooler partition
    out += B9.wall_notice((wc, 6.95), (-1.0, 0.0), 1.22, 0.62, 0.50, "cork")
    out += B9.wall_notice((wc, 7.78), (-1.0, 0.0), 1.38, 0.26, 0.34, "schedule")
    out += B9.wall_notice((wc, 5.75), (-1.0, 0.0), 1.42, 0.30, 0.38, "calendar")
    tk = 5.00 - B9.WT / 2 - 0.001                                        # kitchen side of P7
    out += B9.wall_notice((15.10, tk), (0.0, -1.0), 1.40, 0.26, 0.34, "special")     # 0.3.1-k: were in the cooler door
    out += B9.wall_notice((15.50, tk), (0.0, -1.0), 1.36, 0.26, 0.34, "schedule")
    out += pipes_faces()
    return out


def boh_faces():
    out = []
    for f in B9.boh_faces():
        size = _BOH_CC0_IDX.get(f["mat"])
        out.append(_rescale_uv(f, size) if size else f)
    up = (0.0, 1.0)
    extra = []
    extra += B9.wall_notice((2.90, YB), up, 1.35, 0.30, 0.40, "schedule")
    extra += B9.wall_notice((4.20, YB), up, 1.45, 0.26, 0.34, "no_loiter")
    extra += B9.wall_notice((7.40, YB), up, 1.40, 0.28, 0.36, "calendar")
    extra += B9.wall_notice((5.75, YR), (0.0, -1.0), 1.45, 0.24, 0.32, "clipping")
    extra += boh_extra_faces()
    ex2, direct = broken_ceiling_faces()
    extra += ex2
    extra += kitchen_junction_faces()
    for f in extra:                     # 0.3.1-j FIX: these used the raw hall index (20) -> rendered with the wrong material
        if f is not None:
            out.append(dict(f, mat=B9._REMAP[f["mat"]]))
    out += [f for f in direct + leak_faces() if f is not None]          # 0.3.1-l: BOH-only materials, already BOH indices
    return out


# ================================================================== 0.3.1-l LOCAL DIRT, BROKEN CEILING, LOOSE WIRES
# (owner 2026-11-13 21:43: "где-то течёт, где-то мухи, где-то вода капает в ведро ... 3D-провода на кухне вылазающиеся,
# пробитый чуть-чуть потолок на кухне ... зал не меняй"). Everything below is in the back-of-house drawable only.
LEAK_REG = {"A": (0, 0, 512, 512), "A2": (512, 0, 1024, 512), "B": (0, 512, 128, 1024), "C": (128, 512, 1024, 768),
            "D": (128, 768, 1024, 1024)}                                   # px in lp9_boh_leaks (1024 x 1024)


def _luv(key, pad=2.0):
    x0, y0, x1, y1 = LEAK_REG[key]
    return ((x0 + pad) / 1024.0, 1.0 - (y1 - pad) / 1024.0, (x1 - pad) / 1024.0, 1.0 - (y0 + pad) / 1024.0)


def leak_wall(p, n, w, z0, h, key, off=0.004, flip=False):
    """Leak decal on a wall face: p = (s, t) on the face, n = facing (ns, nt); width w centred on p, from z0 up h."""
    X = (-n[1], n[0])                                                     # left -> right seen from the room
    c = (p[0] + n[0] * off, p[1] + n[1] * off)
    a = (c[0] - X[0] * w / 2, c[1] - X[1] * w / 2)
    b = (c[0] + X[0] * w / 2, c[1] + X[1] * w / 2)
    u0, vb, u1, vt = _luv(key)
    if flip:
        u0, u1 = u1, u0
    vs = [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z0 + h), (a[0], a[1], z0 + h)]
    return F(vs, LEAK_IDX, [(u0, vb), (u1, vb), (u1, vt), (u0, vt)], hint=(n[0], n[1], 0.0))


def leak_faces():
    C = B9.CEIL
    up, dn = (0.0, 1.0), (0.0, -1.0)
    tk = 5.00 - B9.WT / 2                                                 # kitchen side of P7
    return [
        leak_wall((2.75, YB), up, 0.90, C - 1.25, 1.23, "A"),             # corridor: under the leaking pipe, over the bucket
        leak_wall((4.65, YR), dn, 1.20, 1.15, 0.42, "C"),                 # corridor: damp above the tiles
        leak_wall((14.10, B9.YN), dn, 1.00, C - 1.45, 1.43, "A2"),           # storage: under the pipes
        leak_wall((11.45, B9.YN), dn, 0.22, C - 1.62, 1.40, "B"),            # storage: rust streak from a pipe strap
        leak_wall((2.20, B9.YN), dn, 0.20, C - 1.45, 1.25, "B", flip=True),  # staff room: streak from the pipe
        leak_wall((3.90, B9.YN), dn, 1.30, 1.15, 0.40, "D"),                 # staff room: damp above the tiles
        leak_wall((14.25, tk), dn, 0.22, 1.70, 1.45, "B"),                # kitchen: streak under the pass-wall pipe
        leak_wall((11.95, tk), dn, 0.80, 2.02, 1.35, "A2", flip=True),    # kitchen: leak above the 3-bay sink
    ]


BROKEN_CELL = (19, 5)                     # kitchen ceiling tile (P grid) over the free floor between island and dish table
BROKEN_C = ((BROKEN_CELL[0] + 0.5) * P, (BROKEN_CELL[1] + 0.5) * P)      # (12.553, 3.541): bucket + drips (client)


def _sag(p0, p1, droop, n=10):
    pts = []
    for k in range(n + 1):
        u = k / n
        pts.append((p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u, p0[2] + (p1[2] - p0[2]) * u - droop * 4 * u * (1 - u)))
    return pts


def broken_ceiling_faces():
    """-> (hall-indexed faces, BOH-indexed faces): a missing ceiling tile in the kitchen - dark void, water stain, the
    tile hanging from its far edge with a corner broken off, a piece of it on the floor, cables hanging out."""
    C = B9.CEIL
    i, j = BROKEN_CELL
    s0, s1, t0, t1 = i * P, (i + 1) * P, j * P, (j + 1) * P
    e = 0.012
    ex, direct = [], []
    emit(ex, F([(s0 + e, t0 + e, C - 0.0035), (s1 - e, t0 + e, C - 0.0035), (s1 - e, t1 - e, C - 0.0035), (s0 + e, t1 - e, C - 0.0035)],
               "rubber", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(0, 0, -1)))
    emit(ex, K6.ceil_decal((s0 + s1) / 2, (t0 + t1) / 2, 0.60, K6.STAIN_SMALL, z=C - 0.0022))
    # hanging tile: hinge on the north edge, 38 deg down towards -t, the +s corner of the free edge broken off
    a = math.radians(38.0)
    W, L, th = (s1 - s0) - 2 * e, (t1 - t0) - 2 * e, 0.015
    hz, ht = C - 0.004, t1 - e
    D = (0.0, -math.cos(a), -math.sin(a))
    Nl = (0.0, math.sin(a), -math.cos(a))                                       # lower face normal (down)

    def pt(x, d, k=0.0):
        return (s0 + e + x, ht + D[1] * d - Nl[1] * k, hz + D[2] * d - Nl[2] * k)
    poly = [(0.0, 0.0), (W, 0.0), (W, L - 0.21), (W - 0.17, L), (0.0, L)]
    uv = [(0.02 + x / W * 0.96, 0.02 + (1 - d / L) * 0.96) for x, d in poly]
    emit(direct, F([pt(x, d) for x, d in poly], CEILT_IDX, uv, hint=Nl))
    emit(ex, F([pt(x, d, th) for x, d in poly], "plaster", [(x / 2.0, d / 2.0) for x, d in poly], hint=tuple(-c for c in Nl)))
    for k in range(len(poly)):
        (x0, d0), (x1, d1) = poly[k], poly[(k + 1) % len(poly)]
        q = [pt(x0, d0), pt(x1, d1), pt(x1, d1, th), pt(x0, d0, th)]
        mid = ((x0 + x1) / 2 - W / 2, (d0 + d1) / 2 - L / 2)
        hint = (mid[0], D[1] * mid[1], D[2] * mid[1])
        emit(ex, F(q, "plaster", [(0, 0), (0.3, 0), (0.3, 0.01), (0, 0.01)], hint=hint))
    # the broken corner on the floor
    yaw = math.radians(23.0)
    fr = Frame((12.86, 3.20, 0.0), (math.cos(yaw), math.sin(yaw), 0.0), (-math.sin(yaw), math.cos(yaw), 0.0))
    ex += B9.cbox(fr, -0.085, 0.085, -0.06, 0.06, B9.FLOOR + 0.004, B9.FLOOR + 0.019, "plaster")
    # cables out of the hole (south edge, clear of the hanging tile)
    ex += K6.tube(B9.WORLD, [(s0 + 0.16, t0 + 0.05, C + 0.02), (s0 + 0.17, t0 + 0.05, C - 0.12), (s0 + 0.19, t0 + 0.04, C - 0.32),
                             (s0 + 0.22, t0 + 0.02, C - 0.52), (s0 + 0.25, t0 + 0.00, C - 0.64)], 0.0065, 6, "rubber", caps=True)
    ex += K6.tube(B9.WORLD, _sag((s0 + 0.34, t0 + 0.06, C + 0.02), (s1 - 0.07, t0 + 0.09, C + 0.02), 0.42), 0.005, 6, "enamel", caps=True)
    end = (s0 + 0.45, t0 - 0.02, C - 0.44)
    ex += K6.tube(B9.WORLD, [(s0 + 0.42, t0 + 0.07, C + 0.02), (s0 + 0.43, t0 + 0.06, C - 0.14), (s0 + 0.44, t0 + 0.03, C - 0.30),
                             end], 0.010, 8, "steel", caps=True)
    ex += B9.cbox(B9.WORLD, end[0] - 0.05, end[0] + 0.05, end[1] - 0.035, end[1] + 0.035, end[2] - 0.06, end[2], "steel")
    return ex, direct


def kitchen_junction_faces():
    """Open junction box high on the kitchen SW wall, cover hanging off one screw, cables spilling out."""
    out = []
    y = B9.YS + 0.001
    sc, zc = 14.42, 2.82
    out += B9.cbox(B9.WORLD, sc - 0.11, sc + 0.11, y, y + 0.075, zc - 0.11, zc + 0.11, "steel")
    out += B9.cbox(B9.WORLD, sc - 0.095, sc + 0.095, y + 0.075, y + 0.078, zc - 0.095, zc + 0.095, "iron")   # dark inside
    a = math.radians(28.0)                                                  # cover hanging from its top-left screw
    fr = Frame((sc - 0.10, y + 0.082, zc + 0.10), (math.cos(a), 0.0, -math.sin(a)), (0.0, 1.0, 0.0), (math.sin(a), 0.0, math.cos(a)))
    out += B9.cbox(fr, 0.0, 0.21, 0.0, 0.004, -0.21, 0.0, "steel")
    for k, (mat, r, dx, drop, swing) in enumerate((("rubber", 0.006, -0.05, 0.42, 0.06), ("enamel", 0.005, -0.01, 0.30, -0.04),
                                                    ("rubber", 0.0055, 0.03, 0.55, 0.09), ("iron", 0.007, 0.06, 0.36, -0.07))):
        p0 = (sc + dx, y + 0.05, zc - 0.10)
        pts = [p0, (p0[0] + swing * 0.3, y + 0.07, p0[2] - drop * 0.35), (p0[0] + swing * 0.7, y + 0.09, p0[2] - drop * 0.75),
               (p0[0] + swing, y + 0.10, p0[2] - drop)]
        out += K6.tube(B9.WORLD, pts, r, 6, mat, caps=True)
    return out


# ================================================================== 0.3.2 MINI MARKET + FAST FOOD (owner brief 2026-11-15)
# "LONG PIG MINI MARKET - interior rework": the hall read as a diner; it must read as a 90s corner mini market + hot food
# stop. Owner's choices: the banquette on the back (P2) wall and the two centre tables go; lighting only slightly warmer.
#   ZONE C  back wall: ICE merchandiser, four glass-door beer / soda fridges, a double cooler, wine rack, BEER neon,
#           faded yellow header sign (Higgsfield picture, lp8 atlas region 'open_neon')
#   CENTRE  one gondola of two back-to-back 24/7 shelf pairs (stocked vanilla shelves), beer-case stack, newspaper box
#   ZONE B  counter: candy / gum / chips at the till, juice dispenser on the coffee end
#   ZONE D  the three booths and the window ledge stay (12 + 2 seats, 2 counter stools)
# Vanilla props by archetype name only. Everything is a filter / addition on top of the 0.3.1 kit.
import json as _json
from pathlib import Path as _Path
for _k, _v in _json.loads((_Path(__file__).resolve().parent / "gs_v032_vb.json").read_text()).items():
    VB.setdefault(_k, (tuple(_v["min"]), tuple(_v["max"])))

MKT_WALL_T = P2_T[0]                              # hall face of the back wall
MKT_BANQ = (-2.06, 5.66, 5.00, 6.96)              # banquette + its tables / chairs (s0, s1, t0, t1)
MKT_GONDOLA_T = 3.21
MKT_GONDOLA_S = (1.25, 3.35)
# 0.3.2-b FINAL POLISH (owner 2026-11-15 20:40): the big white ICE merchandiser, the white double cooler, the newspaper
# box and the loose beer cases are gone; one small steel chest under the ICE sign, a soda fridge with clear glass + two
# beer fridges (3 doors), beer / wine rack with cartons ON its shelves; four DIFFERENT shelf units in the gondola.
MKT_SODA_S = 0.80                                 # prop_vend_fridge01 (clear glass)
MKT_FRIDGES_S = (1.66, 2.52)                      # prop_bar_beerfridge_01
MKT_RACK_S = 3.72                                 # v_ret_ml_liqshelfe
MKT_WALL_S = (-1.7, 4.65)                         # stretch of the back wall taken by the new retail (old wall art hidden there)
MKT_SIGN = (-1.56, -0.06, 1.50, 2.10)             # header sign over the ice chest (s0, s1, z0, z1)
_MKT_SOFT = {MAT[m] for m in ("walnut", "leather", "steel", "terrazzo", "brass", "iron")}


_MKT_KEEP_WALL = {MAT[m] for m in ("tile", "plaster", "tile_white", "rubber")}


def _mkt_in_banq(s, t, z):
    s0, s1, t0, t1 = MKT_BANQ
    return s0 <= s <= s1 and t0 <= t <= t1 and z < 1.45


def _mkt_near_ctable(s, t, r=1.0):
    return any(abs(s - c[0]) < r and abs(t - c[1]) < r for c in CTABLES)


def _mkt_drop_prop(name, s, t, zb):
    if t > MKT_WALL_T and name != "v_serv_wetfloorsn":
        return False
    if _mkt_in_banq(s, t, zb) or (_mkt_near_ctable(s, t) and zb < 1.45):
        return True
    if t > MKT_WALL_T:                                           # back of house: never touched (0.3.2-a bug: was dropped)
        return False
    if 0.2 <= s <= MKT_WALL_S[1] and t > 6.25 and zb < 2.30:     # anything on the wall behind the fridges
        return True
    if t > 6.8 and MKT_WALL_S[0] <= s < 0.2 and 1.2 < zb < 2.5:  # wall props where the header sign hangs
        return True
    if name == "v_serv_wetfloorsn":                              # 0.3.2-b: no cleaning props in the aisles when open
        return True
    return False


def _shelf_yaw(n):
    """24/7 shelves: products face local -X."""
    return math.degrees(math.atan2(-n[1], -n[0]))


def market_props():
    F0 = FLOOR
    n = (0.0, -1.0)
    w = MKT_WALL_T
    out = [B9._against("prop_bar_cooler_01", (-0.81, w), n),                 # the one ice chest, under the ICE sign
           B9._against("prop_vend_fridge01", (MKT_SODA_S, w), n)]
    out += [B9._against("prop_bar_beerfridge_01", (s, w), n) for s in MKT_FRIDGES_S]
    out.append(B9._against("v_ret_ml_liqshelfe", (MKT_RACK_S, w), n))        # beer, wine and cartons on the shelves
    out.append(B9._on_wall("prop_beer_neon_03", (MKT_SODA_S, w), n, 1.62))   # BEER neon over the low soda fridge
    # gondola: four different stocked units. Cooler side (north): sodas + cans; entry side (south): chips / sauces /
    # household + a half-empty cereal unit
    g = MKT_GONDOLA_T
    a, b = MKT_GONDOLA_S
    out += [("v_ret_247shelves02", a, g + 0.006, F0, _shelf_yaw((0.0, 1.0))),
            ("v_ret_247shelves01", b, g + 0.006, F0, _shelf_yaw((0.0, 1.0))),
            ("v_ret_247shelves03", a, g - 0.006 - 0.176, F0, wall_yaw((0.0, -1.0))),          # front = local -Y, centred depth
            ("v_ret_247shelves05", b, g - 0.006 - 0.176, F0, math.degrees(math.atan2(-1.0, 0.0)))]   # front = local +X
    # impulse buys at the till (counter top 1.02) and on the coffee end (1.05)
    out += [("prop_choc_ego", 7.13, 4.90, 1.02, 80.0), ("prop_choc_meto", 7.13, 4.98, 1.02, 95.0), ("prop_choc_ego", 7.14, 5.06, 1.02, 88.0),
            ("prop_candy_pqs", 7.26, 4.94, 1.02, 20.0), ("prop_candy_pqs", 7.27, 5.04, 1.02, -15.0),
            ("prop_cs_crisps_01", 7.16, 5.52, 1.05, 85.0), ("prop_cs_crisps_01", 7.17, 5.63, 1.05, 100.0),
            ("prop_juice_dispenser", 7.55, 6.28, 1.05, wall_yaw((-1.0, 0.0)))]
    return out


def vanilla_props():
    base = K9.vanilla_props() + corridor_props() + boh_extra()
    return [e for e in base if e and not _mkt_drop_prop(e[0], e[1], e[2], e[3])] + market_props()


def set_entities():
    out = {}
    for nm, ents in K9.set_entities().items():
        keep = []
        for e in ents:
            p = e[1]
            if e[0] == "v_serv_bktmop_h":                        # 0.3.2-b: the mop lay across the aisle
                continue
            if e[0].startswith("gs_") or not (_mkt_in_banq(p[0], p[1], 0.0) or _mkt_near_ctable(p[0], p[1])):
                keep.append(e)
        out[nm] = keep
    return out


def collision_boxes():
    out = []
    for b in K9.collision_boxes():
        x0, x1, y0, y1, z0, z1 = b[0]
        cs, ct = (x0 + x1) / 2, (y0 + y1) / 2
        if z1 < 1.45 and (_mkt_in_banq(cs, ct, z1) or (_mkt_near_ctable(cs, ct, 0.6))):
            continue
        out.append(b)
    return out


def market_faces():
    """Faded yellow header sign on the back wall over the ICE box (Higgsfield picture) in a thin dark frame."""
    s0, s1, z0, z1 = MKT_SIGN
    y = MKT_WALL_T - 0.014
    out = [B9.card(B9.WORLD, s0, s1, z0, z1, y, "open_neon", (0.0, -1.0, 0.0))]
    out += B9.cbox(B9.WORLD, s0 - 0.02, s1 + 0.02, y + 0.002, MKT_WALL_T, z0 - 0.02, z1 + 0.02, "iron")
    return out


def hall_faces():
    ct = set(tuple(sorted(f["v"])) for f in K5.centre_faces() if f)
    out = []
    for f in K9.hall_faces():
        if f is None:
            continue
        if tuple(sorted(f["v"])) in ct:
            continue
        if f["mat"] in _MKT_SOFT and all(_mkt_in_banq(v[0], v[1], v[2]) and v[2] > 0.03 for v in f["v"]):
            continue
        if all(_mkt_near_ctable(v[0], v[1], 0.75) and 0.03 < v[2] < 1.3 for v in f["v"]):
            continue
        if f["mat"] not in _MKT_KEEP_WALL and all(6.85 <= v[1] <= MKT_WALL_T + 0.02 and MKT_WALL_S[0] <= v[0] <= MKT_WALL_S[1] and 1.2 <= v[2] <= 2.5 for v in f["v"]):
            continue                                              # old wall art behind the fridges / under the new sign
        out.append(f)
    return out + [f for f in market_faces() if f is not None]


def _mkt_lights(L):
    """0.3.2-b: the existing cans over the retail wall keep their place but no longer light glass (dont_light_alpha: the
    fridge doors looked milky), a little warmer 'old fluorescent' ceiling, food case +30 %, two weak cold fills at the
    fridges, an amber one at the neon and three weak warm-neutral fills over the booths (they were too dark)."""
    out = []
    for l in L:
        k = l["kind"]
        if k == "banquette_key":
            fl = tuple(l.get("flags", ()))
            l = dict(l, color=(1.0, 0.93, 0.80), intensity=round(l["intensity"] * 0.8, 3),
                     flags=fl if "dont_light_alpha" in fl else fl + ("dont_light_alpha",))
        elif k in ("troffer_lamp0", "troffer_lamp3"):
            l = dict(l, color=(0.99, 0.96, 0.88))
        elif k == "case":
            l = dict(l, intensity=round(l["intensity"] * 1.3, 3))
        out.append(l)
    soft = ("not_in_reflection", "no_specular", "dont_light_alpha")
    extra = [K9.LT("cooler_glow", "POINT", (s, MKT_WALL_T - 1.0, 1.60), (0.84, 0.92, 1.0), 0.55, 1.8, 2.0, flags=soft)
             for s in (1.25, 2.55)]
    extra.append(K9.LT("neon_amber", "POINT", (MKT_SODA_S, MKT_WALL_T - 0.35, 2.10), (1.0, 0.70, 0.24), 0.8, 1.6, 2.5, flags=soft))
    for a in V.booth_bays():
        extra.append(K9.LT("booth_fill", "POINT", (a + V.BOOTH_PITCH / 2, -0.55, 2.25), (1.0, 0.95, 0.87), 0.55, 2.6, 2.0, flags=soft))
    for l in extra:
        out.append(dict(l, time=DAY_HOURS))
        out.append(dict(l, intensity=round(l["intensity"] * 0.75, 3), time=NIGHT_HOURS))
    return out


def lights():
    return _night2(_mkt_lights(K9.lights()))


# ================================================================== 0.3.2-c DELI COUNTER REBUILD (gs_counter32.py)
import gs_counter32 as _C32
_C32.install()
_vp_032b = vanilla_props


def vanilla_props():
    """0.3.2-c second-pass polish: no loose litter on the hall floor; the scale stands on the new steel service shelf."""
    out = []
    for e in _vp_032b():
        n, s, t, zb, yaw = e
        if n.startswith("v_res_tt_litter") and t < MKT_WALL_T and zb < 0.1:
            continue
        if n == "v_ret_ml_scale" and 6.9 < s < 8.1 and 1.25 < zb < 1.34:
            e = (n, s, t, 1.34, yaw)
        out.append(e)
    return out


# ================================================================== 0.3.2-d SECOND PASS POLISH (owner brief, 2026-11-15)
_hf_032c, _vp_032c, _lt_032c = hall_faces, vanilla_props, lights
_DROP_DECALS = ((6.35, 3.7), (6.78, 3.3), (-0.6, 4.6), (0.3, 5.15), (2.6, 5.2))     # repeats + scuffs of removed chairs
_DROP_TOP = {("prop_choc_ego", 7.14, 5.06), ("prop_candy_pqs", 7.27, 5.04), ("prop_notepad_02", 7.58, 5.36),
             ("v_ret_gc_pen1", 7.36, 5.42), ("prop_cs_crisps_01", 7.16, 5.52), ("prop_cs_crisps_01", 7.17, 5.63),
             ("prop_food_sugarjar", 7.12, 6.5), ("prop_paper_bag_01", 7.75, 6.7), ("prop_paper_bag_small", 7.84, 5.25)}
_MOVE_TOP = {("prop_choc_ego", 7.13, 4.9): (7.12, 4.90, 90.0), ("prop_choc_meto", 7.13, 4.98): (7.12, 4.98, 90.0),
             ("prop_candy_pqs", 7.26, 4.94): (7.12, 5.07, 0.0),
             ("prop_food_sugarjar", 7.12, 5.8): (7.12, 5.92, 0.0), ("prop_food_ketchup", 7.1, 5.98): (7.12, 6.02, 0.0),
             ("prop_food_mustard", 7.1, 6.04): (7.12, 6.09, 0.0), ("prop_bar_napkindisp", 7.14, 6.15): (7.14, 6.22, 90.0),
             ("prop_cs_paper_cup", 7.4, 6.62): (7.16, 6.52, 0.0), ("prop_cs_paper_cup", 7.47, 6.66): (7.16, 6.60, 0.0)}


def hall_faces():
    out = []
    for f in _hf_032c():
        vs = f["v"]
        if max(v[2] for v in vs) < 0.05 and MAT.get("decal") == f["mat"]:
            cs, ct = sum(v[0] for v in vs) / len(vs), sum(v[1] for v in vs) / len(vs)
            if any(abs(cs - a) < 0.06 and abs(ct - b) < 0.06 for a, b in _DROP_DECALS):
                continue
        out.append(f)
    return out


def vanilla_props():
    """Counter tops: fewer, grouped items - impulse row left of the till, condiments + napkins + cups by the juice dispenser."""
    out = []
    for e in _vp_032c():
        k = (e[0], round(e[1], 2), round(e[2], 2))
        if k in _DROP_TOP and 1.0 < e[3] < 1.1:
            continue
        if k in _MOVE_TOP and 1.0 < e[3] < 1.1:
            s, t, yaw = _MOVE_TOP[k]
            e = (e[0], s, t, e[3], yaw)
        out.append(e)
    return out


def lights():
    """Three weak shadowless fills where the hall was darkest: the gondola aisle (neutral) and the window-ledge corner (warm)."""
    soft = ("not_in_reflection", "no_specular", "dont_light_alpha")
    extra = [K9.LT("market_fill", "POINT", (1.45, 3.9, 2.55), (1.0, 0.96, 0.90), 0.50, 3.0, 2.0, flags=soft),
             K9.LT("market_fill", "POINT", (3.05, 3.9, 2.55), (1.0, 0.96, 0.90), 0.50, 3.0, 2.0, flags=soft),
             K9.LT("corner_fill", "POINT", (-2.2, 0.1, 2.30), (1.0, 0.90, 0.76), 0.40, 2.6, 2.0, flags=soft)]
    out = _lt_032c()
    for l in extra:
        out.append(dict(l, time=DAY_HOURS))
        out.append(dict(l, intensity=round(l["intensity"] * 0.75, 3), time=NIGHT_HOURS))
    return out


# ================================================================== 0.3.2-e FINAL COMMERCIAL PASS (owner brief + 9 in-game screenshots, 2026-11-15)
# leftovers of the removed banquette (floor outline, table foot rings, end panel, floating stains), black plates on the
# cooler wall, hall puddle, stone cylinders by the till; back-counter tile turned to a horizontal bond; second gondola
# row; litter / plant / empty rack / rose wine removed; every prop yaw snapped; night boost on the window side.
_hf_032d, _vp_032d, _lt_032d = hall_faces, vanilla_props, lights
_DECALS_E = {MAT[m] for m in ("decal", "decal5", "decal6") if m in MAT}
MKT_ROWS = ((2.45, 1), (4.55, -1))            # (t of the row axis, +1 = original side order, -1 = mirrored)
MKT_ROW_S = (1.50, 3.60)


def hall_faces():
    out = []
    for f in _hf_032d():
        vs = f["v"]
        m = f["mat"]
        S = [v[0] for v in vs]; T = [v[1] for v in vs]; Z = [v[2] for v in vs]
        if min(S) >= -2.1 and max(S) <= 5.6 and min(T) >= 5.75 and max(T) <= 6.915 and max(Z) < 1.25 and m != MAT["tile"]:
            if not (m in _DECALS_E and max(Z) < 0.03):
                continue
        if m == MAT.get("puddle") and min(S) > 1.4 and max(S) < 3.1 and min(T) > 4.0 and max(T) < 5.6:
            continue
        if m == MAT["rubber"] and min(T) >= 6.9 and min(Z) > 1.25 and max(Z) < 2.02 and min(S) > -0.2 and max(S) < 4.8:
            continue
        if m == MAT["terrazzo"] and min(S) > 7.74 and max(S) < 7.86 and min(T) > 5.32 and max(T) < 5.54 and min(Z) >= 1.0:
            continue
        if m == MAT["tile_white"] and min(S) > 9.9 and max(T) < 6.95:
            f = dict(f, uv=[(uv[1], uv[0]) for uv in f["uv"]])
        out.append(f)
    return out


def _snap(yaw):
    y = ((yaw + 180.0) % 360.0) - 180.0
    q = round(y / 90.0) * 90.0
    return q if abs(y - q) <= 35.0 else round(y / 45.0) * 45.0


def vanilla_props():
    out = []
    for e in _vp_032d():
        n, s, t, zb, yaw = e
        hall = s < 6.95 and t < MKT_WALL_T
        if n.startswith("ng_proc_") and hall and zb < 0.1:
            continue
        if n == "prop_plant_int_04a" and s < -2.0 and t > 6.0:
            continue
        if n in ("prop_paper_bag_small", "prop_bread_rack_02") and 6.9 < s < 9.97 and t < MKT_WALL_T:
            continue
        if n.startswith("v_ret_247shelves") and hall and zb < 0.1:
            continue
        if n == "winerow":
            for k, dt in enumerate((-0.12, 0.0, 0.12)):
                out.append(("prop_wine_red" if (k + int(t * 10)) % 2 else "prop_wine_bot_01", s, t + dt, zb, 90.0))
            continue
        out.append((n, s, t, zb, _snap(yaw)))
    a, b = MKT_ROW_S
    for g, sg in MKT_ROWS:
        if sg > 0:      # drinks + cans to the north (coolers), groceries to the south (booths)
            out += [("v_ret_247shelves02", a, g + 0.01, 0.01, -90.0), ("v_ret_247shelves01", b, g + 0.01, 0.01, -90.0),
                    ("v_ret_247shelves03", a, g - 0.182, 0.01, 0.0), ("v_ret_247shelves05", b, g - 0.18, 0.01, -90.0)]
        else:           # mirrored and swapped end for end: every aisle shows a different pair
            out += [("v_ret_247shelves01", a, g - 0.01, 0.01, 90.0), ("v_ret_247shelves02", b, g - 0.01, 0.01, 90.0),
                    ("v_ret_247shelves05", a, g + 0.18, 0.01, 90.0), ("v_ret_247shelves03", b, g + 0.182, 0.01, 180.0)]
    return out


_NIGHT_E = {"ledge_can": 1.7, "entrance_can": 1.6, "banquette_key": 1.2, "corner_fill": 1.5}


def lights():
    soft = ("not_in_reflection", "no_specular", "dont_light_alpha")
    out = []
    for l in _lt_032d():
        if l.get("time") == NIGHT_HOURS and l["kind"] in _NIGHT_E:
            l = dict(l, intensity=round(l["intensity"] * _NIGHT_E[l["kind"]], 3))
        if l["kind"] == "market_fill":
            p = l["pos"]
            l = dict(l, pos=(MKT_ROW_S[0] if p[0] < 2.2 else MKT_ROW_S[1], 3.5, p[2]))
        out.append(l)
    for pos, inten in (((-1.9, 3.9, 2.35), 0.45), ((-1.5, 0.9, 2.40), 0.40), ((2.5, 5.6, 2.45), 0.35)):
        out.append(dict(K9.LT("night_fill", "POINT", pos, (1.0, 0.91, 0.80), inten, 3.2, 2.0, flags=soft), time=NIGHT_HOURS))
    return out


# ================================================================== 0.3.2-f (owner's 7 screenshots of 0.3.2-e, 2026-11-16)
# banquette end panels (they reached t = 6.96), cooler wall: chest + sign 30 cm right and an ATM on the left, gumball
# machines on the empty wall by the door, the two painted price boards on the back wall replaced by shelves with
# vanilla stock, night levels raised and evened out.
_hf_032e, _vp_032e, _lt_032e, _se_032e, _mf_032e = hall_faces, vanilla_props, lights, set_entities, market_faces
_MKT_SHIFT = 0.30
MKT_SIGN = (MKT_SIGN[0] + _MKT_SHIFT, MKT_SIGN[1] + _MKT_SHIFT, MKT_SIGN[2], MKT_SIGN[3])
_BOARDS_T = ((0.99, 1.61), (5.10, 5.71))
NIGHT2.update({"troffer": 0.60, "banquette_key": 0.55, "soffit_can": 0.55, "entrance_can": 0.65, "ledge_can": 0.65})
NIGHT2_DEFAULT = 0.6
_NIGHT_E.clear()


def _wall_shelves(t0, t1):
    out = []
    wf = V.Frame((V.P1_S[0], t0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    L = t1 - t0
    for z in (1.42, 1.86):
        out += V.cbox(wf, 0.0, L, 0.0, 0.26, z, z + 0.035, "walnut", ch=0.006, grain="x")
        for x in (0.08, L - 0.08):
            out += V.cbox(wf, x - 0.012, x + 0.012, 0.0, 0.012, z - 0.20, z, "iron", grain="z")
            out += V.cbox(wf, x - 0.012, x + 0.012, 0.0, 0.20, z - 0.02, z, "iron", grain="y")
            out += V.tube(wf, [(x, 0.01, z - 0.18), (x, 0.17, z - 0.02)], 0.006, 6, "iron")
    return [f for f in out if f]


def hall_faces():
    old_sign = set(tuple(sorted(f["v"])) for f in _mf_032e() if f)
    out = []
    for f in _hf_032e():
        vs = f["v"]
        m = f["mat"]
        S = [v[0] for v in vs]; T = [v[1] for v in vs]; Z = [v[2] for v in vs]
        if m == MAT["walnut"] and min(S) >= -2.1 and max(S) <= 5.7 and min(T) >= 6.3 and max(T) <= 6.97 and max(Z) < 1.3:
            continue
        if min(S) > 9.89 and max(S) < 9.926 and min(Z) > 1.36 and max(Z) < 2.42 and \
                any(min(T) >= a - 0.005 and max(T) <= b + 0.005 for a, b in _BOARDS_T) and m in (MAT["steel"], MAT["notice"]):
            continue
        if tuple(sorted(vs)) in old_sign:
            continue
        out.append(f)
    out += [f for f in market_faces() if f]
    for a, b in _BOARDS_T:
        out += _wall_shelves(a + 0.02, b - 0.02)
    return out


def vanilla_props():
    out = []
    for e in _vp_032e():
        if e[0] == "prop_bar_cooler_01" and e[2] > 6.0:
            e = (e[0], e[1] + _MKT_SHIFT, e[2], e[3], e[4])
        out.append(e)
    zf = 0.015
    out.append(("prop_atm_01", -1.72, MKT_WALL_T - 0.30, zf, 0.0))
    out += [("prop_gumball_03", -2.59, 1.72, zf, 90.0), ("prop_gumball_02", -2.69, 2.33, zf, 90.0)]
    s = V.P1_S[0] - 0.15
    z1, z2 = 1.455, 1.895
    out += [("v_res_tt_can03", s, 1.12, z1, 0.0), ("v_res_tt_can03", s, 1.22, z1, 0.0), ("v_res_tt_can03", s, 1.32, z1, 0.0),
            ("v_res_foodjarb", s, 1.47, z1, 0.0), ("prop_metalfoodjar_01", s, 1.16, z2, 0.0), ("v_res_foodjara", s, 1.42, z2, 0.0),
            ("prop_cs_paper_cup", s, 5.22, z1, 0.0), ("prop_cs_paper_cup", s, 5.31, z1, 0.0), ("prop_cs_paper_cup", s, 5.40, z1, 0.0),
            ("prop_food_sugarjar", s, 5.56, z1, 0.0), ("v_res_tt_platepile", s, 5.26, z2, 0.0), ("v_res_foodjarc", s, 5.54, z2, 0.0)]
    return out


def set_entities():
    out = {}
    for nm, ents in _se_032e().items():
        out[nm] = [((e[0], (5.45, 3.5, e[1][2]), 0.0) if e[0] == "v_serv_wetfloorsn" else e) for e in ents]
    return out


def lights():
    out = []
    for l in _lt_032e():
        if l["kind"] == "night_fill":
            l = dict(l, intensity=round(l["intensity"] * 1.4, 3), falloff=3.6)
        out.append(l)
    soft = ("not_in_reflection", "no_specular", "dont_light_alpha")
    out.append(dict(K9.LT("night_fill", "POINT", (2.5, 1.3, 2.45), (1.0, 0.91, 0.80), 0.5, 3.6, 2.0, flags=soft), time=NIGHT_HOURS))
    return out


# ================================================================== 0.3.2-g (owner's screenshots of 0.3.2-f, 2026-11-16)
# faded dark-blue tile behind the counter (ambientCG Tiles135B, CC0), maroon band all round the hall with the menu
# lettering, gumball machines on the DIAGONAL door wall (0.3.2-f put them on the W wall line, i.e. into the corner),
# more varied stock on the back shelves, night levels derived from the day levels.
_hf_032f, _vp_032f, _lt_032f = hall_faces, vanilla_props, lights
MAT["tile_blue"] = len(SHADER_SPECS)
SHADER_SPECS.append(("normal_spec.sps", {"DiffuseSampler": "lp10_tile_blue", "BumpSampler": "lp10_tile_blue_n", "SpecSampler": "lp10_tile_blue_s"},
                     {"specularIntensityMult": 0.7, "specularFalloffMult": 80.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp10_tile_blue"))
MAT["frieze_txt"] = len(SHADER_SPECS)
SHADER_SPECS.append(("normal_spec.sps", {"DiffuseSampler": "lp4_menu", "BumpSampler": "lp_flat_n", "SpecSampler": "lp_matte_s"},
                     {"specularIntensityMult": 0.12, "specularFalloffMult": 8.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp4_menu_matte"))
V.REP.update({"tile_blue": 1.2, "frieze_txt": 1.0})
_CH_A, _CH_B = (0.58, -1.23), (-2.9, 2.50)                       # diagonal entrance wall (hall face), SW end -> W end
_CH_N = (0.731, 0.682)
FRIEZE_Z = (2.93, 3.19)
_FRIEZE_WALLS = ((( 6.97, -1.23), _CH_A, (0.0, 1.0)), (_CH_A, _CH_B, _CH_N), (_CH_B, (-2.9, 6.94), (1.0, 0.0)),
                 ((-2.9, 6.94), (6.97, 6.94), (0.0, -1.0)))       # each wall left -> right as seen from the room
_FRIEZE_TEXT = (2, 0)                                             # walls that carry the lettering (W wall, booth wall)


def _frieze():
    out = []
    z0, z1 = FRIEZE_Z
    for k, (a, b, n) in enumerate(_FRIEZE_WALLS):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        def P(x, off, z):
            return (a[0] + d[0] * x + n[0] * off, a[1] + d[1] * x + n[1] * off, z)
        V.emit(out, V.F([P(0, 0.004, z0), P(L, 0.004, z0), P(L, 0.004, z1), P(0, 0.004, z1)], "walnut",
                        [(z0, 0.0), (z0, L), (z1, L), (z1, 0.0)], hint=(n[0], n[1], 0.0)))
        V.emit(out, V.F([P(0, 0.006, z0 - 0.012), P(L, 0.006, z0 - 0.012), P(L, 0.006, z0), P(0, 0.006, z0)], "steel",
                        [(0.0, 0.0), (L, 0.0), (L, 0.02), (0.0, 0.02)], hint=(n[0], n[1], 0.0)))
        if k in _FRIEZE_TEXT:
            h = 0.19
            w = h * 13.6
            x0 = (L - w) / 2
            zc = (z0 + z1) / 2
            V.emit(out, V.F([P(x0, 0.006, zc - h / 2), P(x0 + w, 0.006, zc - h / 2), P(x0 + w, 0.006, zc + h / 2), P(x0, 0.006, zc + h / 2)],
                            "frieze_txt", [(0.15, 0.885), (0.85, 0.885), (0.85, 0.988), (0.15, 0.988)], hint=(n[0], n[1], 0.0)))
    return [f for f in out if f]


def hall_faces():
    out = []
    for f in _hf_032f():
        if f["mat"] == MAT["tile_white"] and min(v[0] for v in f["v"]) > 9.9 and max(v[1] for v in f["v"]) < 6.95:
            f = dict(f, mat=MAT["tile_blue"], uv=[(v[2] / 1.2, v[1] / 1.2) for v in f["v"]])
        out.append(f)
    return out + _frieze()


_SHELF_MIX = {3.05: ("prop_metalfoodjar_01", "v_res_foodjarb", "v_res_tt_can03"), 3.85: ("v_res_fa_bread02", None, "prop_wine_red")}


def vanilla_props():
    out = []
    for e in _vp_032f():
        n, s, t, zb, yaw = e
        if n.startswith("prop_gumball"):
            continue
        if n.startswith("prop_wine") and s > 9.0 and 1.4 < zb < 1.5:
            hit = None
            for c, names in _SHELF_MIX.items():
                if abs(t - c) < 0.2:
                    hit = names[0 if t < c - 0.05 else (2 if t > c + 0.05 else 1)]
                    break
            else:
                hit = n
            if hit is None:
                continue
            e = (hit, s, t, zb, 0.0 if not hit.startswith("prop_wine") else yaw)
        out.append(e)
    yaw = B9.wall_yaw(_CH_N)
    for name, k, r in (("prop_gumball_03", 3.55 + 0.40, 0.31), ("prop_gumball_02", 3.55 + 1.12, 0.21)):
        L = math.hypot(_CH_B[0] - _CH_A[0], _CH_B[1] - _CH_A[1])
        d = ((_CH_B[0] - _CH_A[0]) / L, (_CH_B[1] - _CH_A[1]) / L)
        out.append((name, _CH_A[0] + d[0] * k + _CH_N[0] * r, _CH_A[1] + d[1] * k + _CH_N[1] * r, 0.015, yaw))
    return out


_NIGHT_G = {"troffer": 0.21, "soffit_can": 0.24, "banquette_key": 0.22, "entrance_wall_light": 0.25, "entrance_can": 0.28, "ledge_can": 0.28,
            "case": 0.45, "menu_glow": 0.45}     # 0.3.2-e was ~0.15-0.19 (too dark), 0.3.2-f ~0.29-0.33 (blown ceiling)
_NIGHT_FILLS = (((-0.35, 1.5, 2.50), 0.50), ((-1.9, 4.2, 2.35), 0.40), ((2.5, 1.3, 2.45), 0.35), ((2.5, 5.6, 2.45), 0.30))   # the door fill of e / f sat inside the diagonal wall


def lights():
    """Night = the day picture (which the owner likes) scaled per fixture type; three weak shadowless night fills."""
    src = [l for l in _lt_032f() if l["kind"] != "night_fill"]
    day = {(l["kind"], tuple(round(c, 2) for c in l["pos"])): l["intensity"] for l in src if l.get("time") == DAY_HOURS}
    out = []
    for l in src:
        if l.get("time") == NIGHT_HOURS:
            k = l["kind"]
            fam = "troffer" if k.startswith("troffer_lamp") else k
            base = day.get((k, tuple(round(c, 2) for c in l["pos"])))
            if base is not None:
                l = dict(l, intensity=round(base * _NIGHT_G.get(fam, 0.45), 3))
        out.append(l)
    soft = ("not_in_reflection", "no_specular", "dont_light_alpha")
    for pos, inten in _NIGHT_FILLS:
        out.append(dict(K9.LT("night_fill", "POINT", pos, (1.0, 0.92, 0.82), inten, 3.4, 2.0, flags=soft), time=NIGHT_HOURS))
    return out


# ================================================================== 1.1.0 FINAL (owner's screenshots of 0.3.2-g, 2026-11-16)
# one gumball machine (the triple one) centred on the diagonal wall; blue tile -> ambientCG Tiles135C (missing tiles,
# grime), larger repeat; back shelves restocked in an orderly pattern; more wall grime; night trim.
_hf_032g, _vp_032g, _lt_032g = hall_faces, vanilla_props, lights
_SHELF_S = V.P1_S[0] - 0.15
_GRIME = (  # (wall index in _FRIEZE_WALLS, x along the wall from its left end, z0, width, height, mat, uv rect)
    (1, 4.15, 1.42, 0.92, 1.04, "decal6", (0.0, 0.5, 0.5, 1.0)), (2, 1.95, 2.62, 1.30, 0.30, "decal5", (0.75, 0.25, 1.0, 0.5)),
    (2, 1.10, 0.04, 1.70, 0.20, "decal5", (0.5, 0.75, 0.75, 1.0)), (3, 0.25, 1.30, 0.40, 0.82, "decal6", (0.5, 0.5, 1.0, 1.0)),
    (3, 8.20, 2.62, 1.30, 0.30, "decal5", (0.75, 0.25, 1.0, 0.5)), (0, 0.25, 1.38, 0.40, 0.82, "decal6", (0.5, 0.5, 1.0, 1.0)),
    (0, 5.75, 0.04, 0.60, 0.20, "decal5", (0.5, 0.75, 0.75, 1.0)), (1, 0.30, 0.04, 1.20, 0.20, "decal5", (0.5, 0.75, 0.75, 1.0)),
    (3, 9.10, 0.95, 0.40, 0.82, "decal6", (0.5, 0.5, 1.0, 1.0)))


def _grime():
    out = []
    for k, x, z0, w, h, mat, (u0, v0, u1, v1) in _GRIME:
        a, b, n = _FRIEZE_WALLS[k]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        def P(xx, z):
            return (a[0] + d[0] * xx + n[0] * 0.005, a[1] + d[1] * xx + n[1] * 0.005, z)
        V.emit(out, V.F([P(x, z0), P(x + w, z0), P(x + w, z0 + h), P(x, z0 + h)], mat, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)],
                        hint=(n[0], n[1], 0.0)))
    return [f for f in out if f]


def hall_faces():
    out = []
    for f in _hf_032g():
        if f["mat"] == MAT["tile_blue"]:
            f = dict(f, uv=[(v[2] / 1.6, v[1] / 1.6) for v in f["v"]])
        out.append(f)
    return out + _grime()


def vanilla_props():
    out = []
    for e in _vp_032g():
        n, s, t, zb, yaw = e
        if n.startswith("prop_gumball"):
            continue
        if s > 9.7 and 2.2 < t < 4.5 and (abs(zb - 1.455) < 0.01 or 1.885 < zb < 1.91) and n != "v_ret_gc_clock":
            continue                                             # middle shelves of the back wall: restocked below
        out.append(e)
    s = _SHELF_S
    for i, t in enumerate((2.52, 2.64, 2.76, 3.94, 4.06, 4.18)):  # two groups of three bottles at the shelf ends
        out.append(("prop_wine_red" if i % 2 else "prop_wine_bot_01", s, t, 1.455, 90.0))
    out += [("v_res_fa_bread01", s, 3.18, 1.455, 0.0), ("v_res_fa_bread02", s, 3.50, 1.455, 0.0)]            # bread in the middle
    for name, t in (("v_res_foodjara", 2.55), ("v_res_foodjarb", 2.95), ("prop_metalfoodjar_01", 3.35), ("v_res_foodjarc", 3.75),
                    ("prop_metalfoodjar_01", 4.15)):               # top shelf: five containers at an even 40 cm pitch
        out.append((name, s, t, 1.895, 0.0))
    L = math.hypot(_CH_B[0] - _CH_A[0], _CH_B[1] - _CH_A[1])
    d = ((_CH_B[0] - _CH_A[0]) / L, (_CH_B[1] - _CH_A[1]) / L)
    k, r = 3.55 + 0.78, 0.30
    out.append(("prop_gumball_02", _CH_A[0] + d[0] * k + _CH_N[0] * r, _CH_A[1] + d[1] * k + _CH_N[1] * r, 0.015, B9.wall_yaw(_CH_N)))
    return out


_NIGHT_H = {"troffer": 0.86, "booth_fill": 1.25, "market_fill": 1.3, "case": 1.15}


def lights():
    out = []
    for l in _lt_032g():
        if l.get("time") == NIGHT_HOURS:
            k = l["kind"]
            fam = "troffer" if k.startswith("troffer_lamp") else k
            if fam in _NIGHT_H:
                l = dict(l, intensity=round(l["intensity"] * _NIGHT_H[fam], 3))
        out.append(l)
    return out


# ================================================================== 1.1.1 (owner 2026-11-16: worn tile with missing pieces everywhere,
# kitchen wrecked and dirty, more floor wear, a leak in the hall). Textures: gs_15w_worn_tiles.py (ambientCG Tiles135C, CC0).
_hf_110, _lk_110 = hall_faces, leak_faces
_TILE_WORN = 1.2                                                  # metres per repeat of the worn tile sheet (12 x 6 tiles)
SHELL_TEX = dict(SHELL_TEX)
SHELL_TEX["tile"] = ("lp10_tile_red", "lp10_tile_blue_n", "lp10_tile_blue_s", 70.0, 0.8)
SHADER_SPECS[MAT["tile"]] = ("normal_spec.sps", {"DiffuseSampler": "lp10_tile_red", "BumpSampler": "lp10_tile_blue_n", "SpecSampler": "lp10_tile_blue_s"},
                             {"specularIntensityMult": 0.8, "specularFalloffMult": 70.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp10_tile_red")
_i = B9.BOH_MATS.index("tile_white")
BOH_SPECS[_i] = ("normal_spec.sps", {"DiffuseSampler": "lp10_tile_dirty", "BumpSampler": "lp10_tile_dirty_n", "SpecSampler": "lp10_tile_dirty_s"},
                 {"specularIntensityMult": 0.8, "specularFalloffMult": 40.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp10_tile_dirty")
_BOH_CC0_IDX[_i] = _TILE_WORN

# shell wainscot / sills (material 2): u was length / 0.6, v was height / 1.0 -> one sheet per 1.2 m both ways
_shell_prev, _part_prev = _PG.shell_faces, K9.SG.partition_faces if hasattr(K9, "SG") else None


def _worn_uv(fs, mat):
    return [dict(f, uv=[(u * 0.6 / _TILE_WORN, v / _TILE_WORN) for u, v in f["uv"]])
            if isinstance(f, dict) and f.get("mat") == mat else f for f in fs]            # copies: never rescaled twice


def _shell_faces_111(*a, **k):
    return _worn_uv(_shell_prev(*a, **k), 2)


_PG.shell_faces = _shell_faces_111
import gs_slice_geometry as _SG
if not hasattr(_SG, "_partition_faces_static"):
    _SG._partition_faces_static = _SG.partition_faces
_SG.partition_faces = lambda mats, *a, **k: _worn_uv(_SG._partition_faces_static(mats, *a, **k), mats.get("wood", 2))

_FLOOR_WEAR = (("decal", (0.25, 0.5, 0.5, 1.0), 0.2, 3.5, 1.5), ("decal", (0.25, 0.5, 0.5, 1.0), 2.9, 3.5, 1.4), ("decal5", (0.5, 0.25, 0.75, 0.5), 4.9, 3.3, 1.1),
               ("decal5", (0.0, 0.0, 0.25, 0.25), -1.3, 5.3, 0.8), ("decal6", (0.5, 0.0, 1.0, 0.5), 5.6, 5.6, 0.75), ("decal", (0.75, 0.5, 1.0, 1.0), 3.0, 5.6, 0.6),
               ("decal", (0.25, 0.5, 0.5, 1.0), 5.6, 1.1, 1.3), ("decal6", (0.0, 0.0, 0.5, 0.5), 1.2, 5.6, 0.6), ("decal5", (0.5, 0.25, 0.75, 0.5), -1.6, 3.0, 1.0),
               ("decal", (0.75, 0.5, 1.0, 1.0), 0.4, 1.3, 0.6), ("decal6", (0.5, 0.0, 1.0, 0.5), 5.0, 6.35, 0.8))


def hall_faces():
    out = []
    for f in _hf_110():
        if f["mat"] == MAT["tile"] and max(v[2] for v in f["v"]) > 0.06:
            f = dict(f, uv=[(u * 0.6 / _TILE_WORN, v * 0.6 / _TILE_WORN) for u, v in f["uv"]])
        out.append(f)
    for mat, (u0, v0, u1, v1), s, t, w in _FLOOR_WEAR:
        h = w / 2
        V.emit(out, V.F([(s - h, t - h, 0.021), (s + h, t - h, 0.021), (s + h, t + h, 0.021), (s - h, t + h, 0.021)], mat,
                        [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=(0.0, 0.0, 1.0)))
    return [f for f in out if f]


def leak_faces():
    C = B9.CEIL
    up, dn = (0.0, 1.0), (0.0, -1.0)
    tk = 5.00 - B9.WT / 2
    return _lk_110() + [
        leak_wall((16.15, 2.00), (-1.0, 0.0), 1.00, C - 1.45, 1.43, "A"),        # kitchen: east wall, from the ceiling
        leak_wall((16.15, 0.10), (-1.0, 0.0), 1.30, 1.15, 0.40, "D"),            # kitchen: damp above the tiles
        leak_wall((13.00, -1.23), up, 0.22, C - 1.60, 1.40, "B"),                # kitchen: rust streak, street wall
        leak_wall((15.00, -1.23), up, 1.20, 1.15, 0.42, "C"),                    # kitchen: damp band, street wall
        leak_wall((13.20, tk), dn, 1.20, 1.15, 0.42, "C", flip=True),            # kitchen: damp band, pass wall
        leak_wall((15.30, tk), dn, 0.90, C - 1.25, 1.23, "A2"),                  # kitchen: second ceiling leak, pass wall
        leak_wall((6.20, YB), up, 0.22, C - 1.50, 1.30, "B"),                    # corridor: streak
        leak_wall((1.30, YR), dn, 1.00, C - 1.45, 1.43, "A", flip=True),         # corridor: ceiling leak, rooms side
    ]


# ================================================================== 1.2.0 FINAL (owner's 7 screenshots of 1.1.1, 2026-11-16)
# Textures / brick table: gs_15x_final.py (ambientCG Tiles135B / 135C / PaintedWood003, CC0).
import json as _json
_hf_111, _vp_111, _lt_111, _shell_111 = hall_faces, vanilla_props, lights, _PG.shell_faces
MAT["board"] = len(SHADER_SPECS)
SHADER_SPECS.append(("normal_spec.sps", {"DiffuseSampler": "lp11_board", "BumpSampler": "lp11_board_n", "SpecSampler": "lp_matte_s"},
                     {"specularIntensityMult": 0.25, "specularFalloffMult": 20.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp11_board"))
MAT["floor_dmg"] = len(SHADER_SPECS)
SHADER_SPECS.append(("decal.sps", {"DiffuseSampler": "lp11_floor_dmg"}, {}, "lp11_floor_dmg"))
V.REP.update({"board": 0.6, "floor_dmg": 1.0})
_C32.BOARD_MAT = "board"
SHELL_TEX["tile"] = ("lp10_tile_red", "lp10_tile_dirty_n", "lp10_tile_dirty_s", 70.0, 0.8)
_GRIME = ()                                                       # the 1.1.0 wall stains read as grey rectangles in game
_BRICKS = _json.loads((_Path(__file__).resolve().parent / "gs_v120_bricks.json").read_text()) if "_Path" in globals() else []
_DMG = {"B": (415, 250, 512, 385), "C": (140, 368, 345, 512), "D": (0, 270, 40, 375), "E": (165, 248, 220, 282), "F": (85, 355, 130, 405)}
_FLOOR_DMG = (("C", 0.9, 1.25, 0.85, 0), ("B", 4.9, 2.9, 0.55, 1), ("C", -1.0, 4.3, 0.70, 2), ("B", 2.4, 5.55, 0.50, 3), ("E", 5.9, 4.6, 0.32, 0),
              ("F", 3.3, 3.45, 0.30, 1), ("D", -1.9, 2.9, 0.45, 0), ("C", 6.0, 0.3, 0.75, 3), ("B", 0.2, 5.6, 0.45, 2), ("E", 1.9, 3.5, 0.30, 1),
              ("F", 5.2, 5.9, 0.34, 2), ("B", 4.4, -0.2, 0.40, 0))
HALL_HOLE = (7, 9)                                                # ceiling cell of the hall leak (P grid): s 4.51-5.15, t 5.79-6.44
HALL_HOLE_C = ((HALL_HOLE[0] + 0.5) * P, (HALL_HOLE[1] + 0.5) * P)


def _brick_box(b, depth, x0=None, x1=None):
    A, n = b["A"], b["n"]
    L = math.hypot(b["B"][0] - A[0], b["B"][1] - A[1])
    d = ((b["B"][0] - A[0]) / L, (b["B"][1] - A[1]) / L)
    xa, xb = (b["x"][0] if x0 is None else x0), (b["x"][1] if x1 is None else x1)
    ua = b["u"][0] + (b["u"][1] - b["u"][0]) * (xa - b["x"][0]) / (b["x"][1] - b["x"][0])
    ub = b["u"][0] + (b["u"][1] - b["u"][0]) * (xb - b["x"][0]) / (b["x"][1] - b["x"][0])
    z0, z1 = b["z"]; v0, v1 = b["v"]
    def P3(x, off, z):
        return (A[0] + d[0] * x + n[0] * off, A[1] + d[1] * x + n[1] * off, z)
    e = 0.01
    return [{"v": [P3(xa, depth, z0), P3(xb, depth, z0), P3(xb, depth, z1), P3(xa, depth, z1)], "uv": [(ua, v0), (ub, v0), (ub, v1), (ua, v1)], "mat": 1},
            {"v": [P3(xa, 0, z1), P3(xa, depth, z1), P3(xb, depth, z1), P3(xb, 0, z1)], "uv": [(ua, v1 - e), (ua, v1), (ub, v1), (ub, v1 - e)], "mat": 1},
            {"v": [P3(xa, 0, z0), P3(xb, 0, z0), P3(xb, depth, z0), P3(xa, depth, z0)], "uv": [(ua, v0 + e), (ub, v0 + e), (ub, v0), (ua, v0)], "mat": 1},
            {"v": [P3(xa, 0, z0), P3(xa, depth, z0), P3(xa, depth, z1), P3(xa, 0, z1)], "uv": [(ua + e, v0), (ua, v0), (ua, v1), (ua + e, v1)], "mat": 1},
            {"v": [P3(xb, depth, z0), P3(xb, 0, z0), P3(xb, 0, z1), P3(xb, depth, z1)], "uv": [(ub, v0), (ub - e, v0), (ub - e, v1), (ub, v1)], "mat": 1}]


def _shell_faces_120(*a, **k):
    out = list(_shell_111(*a, **k))
    for i, b in enumerate(_BRICKS):
        if b["kind"] == "out":
            out += _brick_box(b, 0.014 + 0.008 * (i % 3))               # bricks pushed out 14-30 mm
        else:
            out += _brick_box(b, 0.010, x1=b["x"][0] + 0.09)            # the broken stub left in a hole
    return out


_PG.shell_faces = _shell_faces_120


def _hall_hole():
    """Missing ceiling tile over the hall leak: dark void, the tile hanging by one edge, a stain ring on the next tile."""
    i, j = HALL_HOLE
    s0, s1, t0, t1 = i * P + 0.02, (i + 1) * P - 0.02, j * P + 0.02, (j + 1) * P - 0.02
    C = 3.40
    out = []
    V.emit(out, V.F([(s0, t0, C - 0.004), (s0, t1, C - 0.004), (s1, t1, C - 0.004), (s1, t0, C - 0.004)], "rubber",
                    [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(0.0, 0.0, -1.0)))
    for hint in ((1.0, 0.0, -0.6), (-1.0, 0.0, 0.6)):                    # the tile, hinged on the s0 edge, both sides
        V.emit(out, V.F([(s0, t0 + 0.03, C - 0.01), (s0, t1 - 0.03, C - 0.01), (s0 + 0.30, t1 - 0.05, C - 0.50), (s0 + 0.30, t0 + 0.06, C - 0.47)],
                        "plaster", [(0, 0), (0.6, 0), (0.6, 0.6), (0, 0.6)], hint=hint))
    return [f for f in out if f]


def hall_faces():
    out = []
    for f in _hf_111():
        vs = f["v"]
        if f["mat"] in (MAT["notice"], MAT["rubber"]) and min(v[0] for v in vs) > 9.9 and max(v[1] for v in vs) < 6.6 and \
                min(v[2] for v in vs) > 1.3 and max(v[2] for v in vs) < 2.45:
            continue                                               # papers / frames on the counter back wall
        out.append(f)
    for key, s, t, w, rot in _FLOOR_DMG:
        x0, y0, x1, y1 = _DMG[key]
        h = w * (y1 - y0) / (x1 - x0)
        uv = [(x0 / 512.0, 1 - y1 / 512.0), (x1 / 512.0, 1 - y1 / 512.0), (x1 / 512.0, 1 - y0 / 512.0), (x0 / 512.0, 1 - y0 / 512.0)]
        uv = uv[rot:] + uv[:rot]
        if rot % 2:
            w, h = h, w
        V.emit(out, V.F([(s - w / 2, t - h / 2, 0.022), (s + w / 2, t - h / 2, 0.022), (s + w / 2, t + h / 2, 0.022), (s - w / 2, t + h / 2, 0.022)],
                        "floor_dmg", uv, hint=(0.0, 0.0, 1.0)))
    for b in _BRICKS:                                              # dark bed where a brick is missing
        if b["kind"] == "hole":
            A, n = b["A"], b["n"]
            L = math.hypot(b["B"][0] - A[0], b["B"][1] - A[1])
            d = ((b["B"][0] - A[0]) / L, (b["B"][1] - A[1]) / L)
            q = [(A[0] + d[0] * x + n[0] * 0.003, A[1] + d[1] * x + n[1] * 0.003, z) for x, z in
                 ((b["x"][0], b["z"][0]), (b["x"][1], b["z"][0]), (b["x"][1], b["z"][1]), (b["x"][0], b["z"][1]))]
            V.emit(out, V.F(q, "iron", [(0, 0), (0.2, 0), (0.2, 0.08), (0, 0.08)], hint=(n[0], n[1], 0.0)))
    return [f for f in out if f] + _hall_hole()


def vanilla_props():
    out = []
    for e in _vp_111():
        if e[0] == "prop_gumball_02":
            e = (e[0], e[1], e[2], e[3] - 0.09, e[4])              # in game its foot hung about 9 cm above the floor
        out.append(e)
    return out


def lights():
    return [dict(l, intensity=round(l["intensity"] * 1.15, 3)) if l["kind"] in ("night_fill", "booth_fill") and l.get("time") == NIGHT_HOURS else l
            for l in _lt_111()]


# ================================================================== 1.2.1 (owner's screenshots of 1.2.0, 2026-11-16)
# Photo textures (gs_15z_photo_tex.py: ambientCG Tiles095, WoodSiding005, unmodified) live in the SHELL drawable (it has
# the memory): counter back wall + counter boards move there. Real geometry: recessed missing bricks, a ceiling cavity
# with brick sides, joists, a pipe and cables, the fallen tile in the ceiling material. Door casings back to brick.
_hf_120, _vp_120, _shell_120b, _part_120 = hall_faces, vanilla_props, _PG.shell_faces, _SG.partition_faces
SHELL_EXTRA_SPECS = [
    ("normal_spec.sps", {"DiffuseSampler": "lp12_wall_tile", "BumpSampler": "lp12_wall_tile_n", "SpecSampler": "lp12_wall_tile_s"},
     {"specularIntensityMult": 0.6, "specularFalloffMult": 60.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp12_wall_tile"),      # 6
    ("normal_spec.sps", {"DiffuseSampler": "lp12_board", "BumpSampler": "lp12_board_n", "SpecSampler": "lp12_board_s"},
     {"specularIntensityMult": 0.3, "specularFalloffMult": 20.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp12_board")]          # 7
_SM_TILE, _SM_BOARD = 6, 7
for _k in ("tile_blue", "board"):                                 # the hall keeps the slots but no longer the textures
    SHADER_SPECS[MAT[_k]] = SHADER_SPECS[MAT["tile"]]
_BRICK_HOLES = [b for b in _BRICKS if b["kind"] == "hole"]
_HOLE_D = 0.055
_WALL_T = 1.1                                                     # metres per repeat of the wall tile photo


def _nrm(vs):
    a, b, c = vs[0], vs[1], vs[2]
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2]); w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    return (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])


def _sq(vs, uvs, mat, want):
    """Shell face wound so that it faces `want`."""
    n = _nrm(vs)
    if n[0] * want[0] + n[1] * want[1] + n[2] * want[2] < 0:
        vs, uvs = vs[::-1], uvs[::-1]
    return {"v": [tuple(p) for p in vs], "uv": [tuple(q) for q in uvs], "mat": mat}


def _cut_wall(f, holes):
    """Vertical wall quad [A top, B top, B bottom, A bottom] with rectangular brick holes -> wall pieces + recesses."""
    A, B = f["v"][0], f["v"][1]
    zhi, zlo = A[2], f["v"][3][2]
    L = math.hypot(B[0] - A[0], B[1] - A[1])
    d = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
    n = _nrm(f["v"]); nl = math.hypot(n[0], n[1]); n = (n[0] / nl, n[1] / nl, 0.0)
    uA, uB = f["uv"][0][0], f["uv"][1][0]
    vh, vl = f["uv"][0][1], f["uv"][3][1]
    def P(x, z, off=0.0):
        return (A[0] + d[0] * x - n[0] * off, A[1] + d[1] * x - n[1] * off, z)
    def U(x, z):
        return (uA + (uB - uA) * x / L, vl + (vh - vl) * (z - zlo) / (zhi - zlo))
    def q(xa, xb, za, zb):
        return {"v": [P(xa, zb), P(xb, zb), P(xb, za), P(xa, za)], "uv": [U(xa, zb), U(xb, zb), U(xb, za), U(xa, za)], "mat": f["mat"]}
    out, cur = [], 0.0
    for h in sorted(holes, key=lambda b: b["x"][0]):
        x0, x1 = h["x"]; z0, z1 = h["z"]
        out += [q(cur, x0, zlo, zhi), q(x0, x1, zlo, z0), q(x0, x1, z1, zhi)]
        D = _HOLE_D
        sh = 0.021                                                # back of the recess: the brick half a course lower (reads as bedding)
        out.append(_sq([P(x0, z1, D), P(x1, z1, D), P(x1, z0, D), P(x0, z0, D)], [U(x0, z1 - sh), U(x1, z1 - sh), U(x1, z0 - sh), U(x0, z0 - sh)], f["mat"], n))
        out.append(_sq([P(x0, z1), P(x0, z1, D), P(x0, z0, D), P(x0, z0)], [U(x0, z1), U(x0 + D, z1), U(x0 + D, z0), U(x0, z0)], f["mat"], (d[0], d[1], 0)))
        out.append(_sq([P(x1, z1), P(x1, z1, D), P(x1, z0, D), P(x1, z0)], [U(x1, z1), U(x1 - D, z1), U(x1 - D, z0), U(x1, z0)], f["mat"], (-d[0], -d[1], 0)))
        out.append(_sq([P(x0, z0), P(x1, z0), P(x1, z0, D), P(x0, z0, D)], [U(x0, z0), U(x1, z0), U(x1, z0 - D), U(x0, z0 - D)], f["mat"], (0, 0, 1)))
        out.append(_sq([P(x0, z1), P(x1, z1), P(x1, z1, D), P(x0, z1, D)], [U(x0, z1), U(x1, z1), U(x1, z1 + D), U(x0, z1 + D)], f["mat"], (0, 0, -1)))
        cur = x1
    out.append(q(cur, L, zlo, zhi))
    return out


def _is_window_trim(f):
    cs = sum(p[0] for p in f["v"]) / len(f["v"]); ct = sum(p[1] for p in f["v"]) / len(f["v"])
    return (ct < -1.2 and 1.2 < cs < 5.7) or (cs < -2.88 and 3.4 < ct < 6.45)


def _casing_to_brick(fs, tile_mat, wall_mat):
    out = []
    for f in fs:
        if isinstance(f, dict) and f.get("mat") == tile_mat and max(p[2] for p in f["v"]) > 1.2 and not _is_window_trim(f):
            f = dict(f, mat=wall_mat, uv=[(u * 0.6, v * 0.6) for u, v in f["uv"]])   # tile uv (1.2 m) -> brick uv (2 m)
        out.append(f)
    return out


def _moved_to_shell():
    """Counter back-wall tile and counter boards, taken out of the hall drawable and re-mapped to the photo textures."""
    out = []
    for f in _hf_120():
        if f["mat"] == MAT["tile_blue"]:
            out.append({"v": f["v"], "uv": [(p[1] / _WALL_T, p[2] / _WALL_T) for p in f["v"]], "mat": _SM_TILE})
        elif f["mat"] == MAT["board"]:
            vs = f["v"]
            ts = [p[1] for p in vs]; ss = [p[0] for p in vs]
            k = int(math.floor(((min(ts) + max(ts)) / 2 - _C32.LINE_T0) / _C32.PITCH))
            j = (k * 5) % 12                                       # WoodSiding005: 12 boards per repeat, boards run along U
            if max(ss) - min(ss) < 1e-4 and max(ts) - min(ts) > 0.03:            # the face of the board: exactly one photo board
                uv = [(p[2] * 0.9 + 0.37 * k, (j + 0.08 + 0.84 * (p[1] - min(ts)) / (max(ts) - min(ts))) / 12.0) for p in vs]
            else:                                                  # edges / chamfers: a sliver of the same board
                uv = [(p[2] * 0.9 + 0.37 * k, (j + 0.5 + 2.0 * (p[0] - min(ss))) / 12.0) for p in vs]
            out.append({"v": vs, "uv": uv, "mat": _SM_BOARD})
    return out


def _ceiling_cavity():
    i, j = HALL_HOLE
    s0, s1, t0, t1 = i * P, (i + 1) * P, j * P, (j + 1) * P
    C, H = 3.40, 0.50
    out = []
    for (a, b, n) in (((s0, t0), (s1, t0), (0, 1, 0)), ((s1, t0), (s1, t1), (-1, 0, 0)), ((s1, t1), (s0, t1), (0, -1, 0)), ((s0, t1), (s0, t0), (1, 0, 0))):
        L = P
        out.append(_sq([(a[0], a[1], C + H), (b[0], b[1], C + H), (b[0], b[1], C), (a[0], a[1], C)],
                       [(0.2, 0.95), (0.2 + L / 2, 0.95), (0.2 + L / 2, 0.95 - H / 2), (0.2, 0.95 - H / 2)], 1, n))      # brick sides
    out.append(_sq([(s0, t0, C + H), (s1, t0, C + H), (s1, t1, C + H), (s0, t1, C + H)], [(0.3, 0.3), (0.6, 0.3), (0.6, 0.6), (0.3, 0.6)], 1, (0, 0, -1)))
    for tj in (t0 + 0.16, t1 - 0.20):                             # two old joists across the opening
        za, zb = C + 0.10, C + 0.26
        ta, tb = tj - 0.035, tj + 0.035
        bx = [((s0, ta, za), (s1, ta, za), (s1, tb, za), (s0, tb, za), (0, 0, -1)), ((s0, ta, za), (s1, ta, za), (s1, ta, zb), (s0, ta, zb), (0, -1, 0)),
              ((s0, tb, za), (s1, tb, za), (s1, tb, zb), (s0, tb, zb), (0, 1, 0))]
        for a, b, c, d_, n in bx:
            out.append(_sq([a, b, c, d_], [(0.1, 0.30), (0.75, 0.30), (0.75, 0.372), (0.1, 0.372)], _SM_BOARD, n))
    # the fallen tile: ceiling material, hinged on the s0 edge, both faces + the cut ceiling around the opening
    hs, hz = 0.33, 0.52
    tile = [(s0 + 0.01, t0 + 0.03, C - 0.005), (s0 + 0.01, t1 - 0.03, C - 0.005), (s0 + hs, t1 - 0.06, C - hz), (s0 + hs, t0 + 0.07, C - hz + 0.03)]
    uv = [(s0 / 5.15, t0 / 5.15), (s0 / 5.15, t1 / 5.15), (s1 / 5.15, t1 / 5.15), (s1 / 5.15, t0 / 5.15)]
    out.append(_sq(tile, uv, 3, (1, 0, -0.6)))
    out.append(_sq(tile, uv, 3, (-1, 0, 0.6)))
    return out


def _shell_faces_121(*a, **k):
    out = []
    i, j = HALL_HOLE
    s0, s1, t0, t1 = i * P, (i + 1) * P, j * P, (j + 1) * P
    U = lambda s, t: (s / 5.15, t / 5.15)
    for f in _shell_120b(*a, **k):
        if f["mat"] == 3 and len(f["v"]) == 5:                     # the ceiling, with one cell cut out
            for poly in ([(-2.9, 2.49919), (-2.9, 11.42), (s0, 11.42), (s0, -1.23), (0.584, -1.23)], [(s1, 11.42), (16.15, 11.42), (16.15, -1.23), (s1, -1.23)],
                         [(s0, t0), (s1, t0), (s1, -1.23), (s0, -1.23)], [(s0, 11.42), (s1, 11.42), (s1, t1), (s0, t1)]):
                out.append(_sq([(x, y, 3.4) for x, y in poly], [U(x, y) for x, y in poly], 3, (0, 0, -1)))
            continue
        if f["mat"] == 1 and len(f["v"]) == 4:
            hs = [b for b in _BRICK_HOLES if abs(f["v"][0][0] - b["A"][0]) < 0.02 and abs(f["v"][0][1] - b["A"][1]) < 0.02 and
                  abs(f["v"][1][0] - b["B"][0]) < 0.02 and abs(f["v"][1][1] - b["B"][1]) < 0.02 and f["v"][3][2] <= 1.01 and f["v"][0][2] > 3.0]
            if hs:
                out += _cut_wall(f, hs)
                continue
        out.append(f)
    out = _casing_to_brick(out, 2, 1)
    return out + _moved_to_shell() + _ceiling_cavity()


_PG.shell_faces = _shell_faces_121
_SG.partition_faces = lambda mats, *a, **k: _casing_to_brick(_part_120(mats, *a, **k), mats.get("wood", 2), mats.get("wall", 1))


def _hall_hole():
    """Pipe and cables in the ceiling cavity (the cavity itself, the joists and the fallen tile are shell geometry)."""
    i, j = HALL_HOLE
    s0, s1, t0, t1 = i * P, (i + 1) * P, j * P, (j + 1) * P
    C = 3.40
    out = []
    out += V.tube(V.WORLD, [(s0, t0 + 0.36, C + 0.33), (s1, t0 + 0.36, C + 0.33)], 0.03, 8, "steel")
    out += V.tube(V.WORLD, [(s1 - 0.18, t0 + 0.10, C + 0.30), (s1 - 0.17, t0 + 0.12, C + 0.02), (s1 - 0.15, t0 + 0.13, C - 0.22), (s1 - 0.11, t0 + 0.15, C - 0.40)],
                  0.006, 6, "rubber", caps=True)
    out += V.tube(V.WORLD, [(s1 - 0.30, t1 - 0.08, C + 0.28), (s1 - 0.29, t1 - 0.10, C + 0.00), (s1 - 0.31, t1 - 0.12, C - 0.16), (s1 - 0.36, t1 - 0.13, C - 0.27)],
                  0.005, 6, "rubber", caps=True)
    return [f for f in out if f]


def hall_faces():
    out = []
    for f in _hf_120():
        if f["mat"] in (MAT["tile_blue"], MAT["board"]):
            continue                                               # now in the shell drawable
        vs = f["v"]
        if f["mat"] == MAT["iron"] and len(vs) == 4 and max(p[2] for p in vs) - min(p[2] for p in vs) < 0.09 and \
                any(abs(sum(p[2] for p in vs) / 4 - (b["z"][0] + b["z"][1]) / 2) < 0.01 and
                    abs(vs[0][0] - (b["A"][0] + (b["B"][0] - b["A"][0]) * b["x"][0] / math.hypot(b["B"][0] - b["A"][0], b["B"][1] - b["A"][1]) + b["n"][0] * 0.003)) < 0.01
                    for b in _BRICK_HOLES):
            continue                                               # the flat black "hole" plates of 1.2.0
        if f["mat"] in (MAT["rubber"], MAT["plaster"]) and min(p[2] for p in vs) > 2.85 and \
                HALL_HOLE[0] * P - 0.01 < min(p[0] for p in vs) and max(p[0] for p in vs) < (HALL_HOLE[0] + 1) * P + 0.01 and \
                HALL_HOLE[1] * P - 0.01 < min(p[1] for p in vs) and max(p[1] for p in vs) < (HALL_HOLE[1] + 1) * P + 0.01:
            continue                                               # the flat black ceiling plate + panel of 1.2.0
        out.append(f)
    return out


_KEEP_HIGH = {"prop_beer_box_01", "v_ret_gc_box2", "v_ret_ml_6bottles", "prop_cs_paper_cup"}


def vanilla_props():
    out = []
    for e in _vp_120():
        n, s, t, zb, yaw = e
        if 9.6 < s < 9.97 and t < 6.9:
            if 2.4 < zb < 2.8 and (n not in _KEEP_HIGH or (n == "v_ret_gc_box2" and zb > 2.6)):
                continue                                           # top steel shelf: boxes, the beer case and the cup stacks stay
            if abs(zb - 1.895) < 0.02 and n != "v_ret_gc_clock" and not (n.startswith("v_res_foodjar") and (abs(t - 2.95) < 0.05 or abs(t - 3.75) < 0.05)):
                continue                                           # upper wall shelves: two jars in the middle only
            if abs(zb - 1.455) < 0.02 and n in ("v_res_foodjarb", "prop_food_sugarjar", "v_res_tt_can03"):
                continue                                           # lower wall shelves: bottles, bread and cups only
        out.append(e)
    return out


# ================================================================== 1.3.0 (owner's questionnaire, 2026-11-16)
# floor = quality checker (gs_15aa_v130.py); wall tile intact again (lp4_tile_red in the hall, Tiles133B in the kitchen)
# with point damage only; back rooms = painted brick + red tile like the hall; framed notices on empty hall walls;
# staff side of the counter stocked; light with more contrast.
_hf_121, _vp_121, _lt_121, _shell_121b, _part_121, _boh_121 = hall_faces, vanilla_props, lights, _PG.shell_faces, _SG.partition_faces, boh_faces
_RED = ("normal_spec.sps", {"DiffuseSampler": "lp4_tile_red", "BumpSampler": "lp3_tile_n", "SpecSampler": "lp3_tile_s"},
        {"specularIntensityMult": 0.75, "specularFalloffMult": 90.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp4_tile_red")
for _k in ("tile", "tile_blue", "board"):
    SHADER_SPECS[MAT[_k]] = _RED
SHELL_TEX["tile"] = ("lp4_tile_red", "lp3_tile_n", "lp3_tile_s", 90.0, 0.75)
SHELL_TEX["floor"] = ("lp13_floor", "lp13_floor_n", "lp13_floor_s", 40.0, 0.6)
_FLOOR_K = 1.0 / 1.28 / 0.25                                       # ambientCG Tiles012: 4 tiles of 32 cm per repeat; the old sheet was 4 m


def _uvmul(fs, mat, ku, kv):
    return [dict(f, uv=[(u * ku, v * kv) for u, v in f["uv"]]) if isinstance(f, dict) and f.get("mat") == mat else f for f in fs]


_PG.shell_faces = lambda *a, **k: _uvmul(_uvmul(_shell_121b(*a, **k), 0, _FLOOR_K, _FLOOR_K), 2, 2.0, 1.2)
_SG.partition_faces = lambda mats, *a, **k: _uvmul(_part_121(mats, *a, **k), mats.get("wood", 2), 2.0, 1.2)
# back rooms
_bi = B9.BOH_MATS.index
BOH_SPECS[_bi("plaster")] = ("normal_spec.sps", {"DiffuseSampler": "lp4_paintbrick", "BumpSampler": "lp3_paintbrick_n", "SpecSampler": "lp3_paintbrick_s"},
                             {"specularIntensityMult": 0.35, "specularFalloffMult": 10.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp4_paintbrick")
BOH_SPECS[_bi("tile_white")] = ("normal_spec.sps", {"DiffuseSampler": "lp13_tile_white", "BumpSampler": "lp13_tile_white_n", "SpecSampler": "lp13_tile_white_s"},
                                {"specularIntensityMult": 0.8, "specularFalloffMult": 60.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp13_tile_white")
BOH_RED_IDX = len(BOH_SPECS)
BOH_SPECS.append(_RED)


def boh_faces():
    out = []
    ti = _bi("tile")
    for f in _boh_121():
        if isinstance(f, dict) and f["mat"] == ti:
            vs = f["v"]
            if max(p[2] for p in vs) - min(p[2] for p in vs) > 0.05:           # brown wall tile -> the red wainscot tile of the hall
                ax = 0 if max(p[0] for p in vs) - min(p[0] for p in vs) > max(p[1] for p in vs) - min(p[1] for p in vs) else 1
                f = dict(f, mat=BOH_RED_IDX, uv=[(p[ax] / 0.6, p[2] / 1.0) for p in vs])
        out.append(f)
    return out


_WALL_DMG = ((1, 0.50, 0.22, 0.42, "B"), (1, 4.95, 0.30, 0.34, "E"), (3, 0.55, 0.25, 0.45, "C"), (3, 7.90, 0.20, 0.40, "B"), (3, 8.95, 0.45, 0.30, "F"),
             (0, 0.60, 0.25, 0.40, "C"), (2, 0.45, 0.30, 0.36, "B"))
_FRAMES = ((8.55, "shop_photo", 0.34, 0.26), (8.98, "clipping", 0.24, 0.32), (9.36, "permit", 0.24, 0.32))


def hall_faces():
    out = []
    for f in _hf_121():
        if f["mat"] == MAT["tile"] and max(p[2] for p in f["v"]) > 0.06:
            f = dict(f, uv=[(u * 2.0, v * 2.0) for u, v in f["uv"]])
        out.append(f)
    for k, x, z0, w, key in _WALL_DMG:                              # point damage on the wainscot
        a, b, n = _FRIEZE_WALLS[k]
        L = math.hypot(b[0] - a[0], b[1] - a[1]); d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        x0, y0, x1, y1 = _DMG[key]; h = w * (y1 - y0) / (x1 - x0)
        q = [(a[0] + d[0] * xx + n[0] * 0.004, a[1] + d[1] * xx + n[1] * 0.004, zz) for xx, zz in ((x, z0), (x + w, z0), (x + w, z0 + h), (x, z0 + h))]
        V.emit(out, V.F(q, "floor_dmg", [(x0 / 512.0, 1 - y1 / 512.0), (x1 / 512.0, 1 - y1 / 512.0), (x1 / 512.0, 1 - y0 / 512.0), (x0 / 512.0, 1 - y0 / 512.0)],
                        hint=(n[0], n[1], 0.0)))
    taken = [(min(p[0] for p in f["v"]), max(p[0] for p in f["v"])) for f in out
             if f and f["mat"] in (MAT["notice"], MAT.get("wall5", -1), MAT.get("wall6", -1)) and max(p[1] for p in f["v"]) < -1.2 and min(p[0] for p in f["v"]) > 7.0]
    for s, key, w, h in _FRAMES:                                    # framed pictures on the wall by the TV (existing artwork)
        if any(s - w / 2 - 0.06 < b and a < s + w / 2 + 0.06 for a, b in taken):
            continue
        t, z = V.PG.YS + 0.012, 1.62
        u0, v0, u1, v1 = K5.notice_uv(key)
        out += V.cbox(V.WORLD, s - w / 2 - 0.025, s + w / 2 + 0.025, V.PG.YS, t, z - 0.025, z + h + 0.025, "walnut", ch=0.004)
        V.emit(out, V.F([(s - w / 2, t + 0.002, z), (s + w / 2, t + 0.002, z), (s + w / 2, t + 0.002, z + h), (s - w / 2, t + 0.002, z + h)], "notice",
                        [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=(0.0, 1.0, 0.0)))
    return [f for f in out if f]


def vanilla_props():
    """Staff side of the counter: bags and boxes on the under-counter shelves and on the lower shelf of the prep bench."""
    out = list(_vp_121())
    out += [("prop_paper_bag_small", 7.55, 4.95, 0.505, 0.0), ("prop_paper_bag_small", 7.55, 5.10, 0.505, 0.0), ("prop_paper_bag_small", 7.55, 5.25, 0.505, 0.0),
            ("v_ret_gc_box2", 7.50, 5.80, 0.160, 90.0), ("v_ret_gc_box2", 7.50, 6.35, 0.160, 90.0), ("prop_paper_bag_01", 7.55, 6.10, 0.505, 90.0),
            ("v_ret_gc_box2", 9.60, 6.05, 0.265, 90.0), ("v_ret_gc_box2", 9.60, 5.45, 0.265, 90.0), ("v_ret_gc_box2", 9.60, 3.40, 0.265, 90.0),
            ("prop_paper_bag_01", 9.60, 4.50, 0.265, 90.0), ("prop_paper_bag_01", 9.60, 2.70, 0.265, 90.0)]
    return out


_CONTRAST = {"troffer": 0.82, "market_fill": 0.7, "corner_fill": 0.6, "window_day_fill": 0.85, "night_fill": 0.8, "soffit_can": 1.12, "banquette_key": 1.12,
             "booth_fill": 1.15, "case": 1.1}


def lights():
    out = []
    for l in _lt_121():
        k = l["kind"]; fam = "troffer" if k.startswith("troffer_lamp") else k
        if fam in _CONTRAST:
            l = dict(l, intensity=round(l["intensity"] * _CONTRAST[fam], 3))
        out.append(l)
    return out


# ================================================================== 1.4.0 (owner's 14 screenshots of 1.3.0, 2026-11-16)
# papers / plaques / frames off the walls, entrance door casing, WC door = office door model, hall lights moved into the
# lp_open entity set (closing the hall switches them off; only cooler and case lights stay), messy desk piles removed.
_hf_130, _vp_130, _lt_130, _boh_130 = hall_faces, vanilla_props, lights, boh_faces
for _i, _p in enumerate(B9.PARTS):
    if _p[0].startswith("P3"):
        _h = list(_p[5])
        _h[2] = B9.door_hole("office", 8.55, "gs_boh_wc")
        B9.PARTS[_i] = tuple(_p[:5]) + (_h,) + tuple(_p[6:])
_RM_SIGNS = ((4.62, 6.92, 1.96), (6.33, 6.93, 1.50), (6.48, 6.94, 1.97), (6.35, -1.22, 1.53), (5.86, -1.22, 1.58), (-2.90, 2.58, 1.38),
             (8.55, -1.22, 1.75), (8.98, -1.22, 1.78), (9.36, -1.22, 1.78))     # plaque, rota, catering, rota, grade, note, 3 frames


def _bbox(vs):
    return [min(p[i] for p in vs) for i in range(3)], [max(p[i] for p in vs) for i in range(3)]


def hall_faces():
    src = _hf_130()
    boxes = []
    for f in src:
        if f["mat"] in (MAT["notice"], MAT["wall5"]):
            c = [sum(p[i] for p in f["v"]) / len(f["v"]) for i in range(3)]
            if any(abs(c[0] - a) < 0.05 and abs(c[1] - b) < 0.05 and abs(c[2] - z) < 0.05 for a, b, z in _RM_SIGNS):
                lo, hi = _bbox(f["v"])
                boxes.append(([x - 0.07 for x in lo], [x + 0.07 for x in hi]))
    out = []
    for f in src:
        lo, hi = _bbox(f["v"])
        if any(all(lo[i] >= b0[i] and hi[i] <= b1[i] for i in range(3)) for b0, b1 in boxes):
            continue
        if f["mat"] == MAT["wall5"] and abs(sum(p[0] for p in f["v"]) / len(f["v"]) + 0.33) < 0.05 and abs(sum(p[1] for p in f["v"]) / len(f["v"]) + 0.25) < 0.05:
            us = [u for u, _ in f["uv"]]
            f = dict(f, uv=[(min(us) + max(us) - u, v) for u, v in f["uv"]])          # HOURS card read mirrored
        out.append(f)
    # painted casing round the entrance doors
    A, Bq = (-1.83782, 1.36221), (-0.52, -0.05)
    L = math.hypot(Bq[0] - A[0], Bq[1] - A[1])
    fr = V.Frame((A[0], A[1], 0.0), ((Bq[0] - A[0]) / L, (Bq[1] - A[1]) / L, 0.0), (_CH_N[0], _CH_N[1], 0.0), (0.0, 0.0, 1.0))
    out += V.cbox(fr, -0.11, 0.0, 0.0, 0.028, 0.02, 2.69, "enamel", ch=0.005, grain="z")
    out += V.cbox(fr, L, L + 0.11, 0.0, 0.028, 0.02, 2.69, "enamel", ch=0.005, grain="z")
    out += V.cbox(fr, 0.0, L, 0.0, 0.028, 2.58, 2.69, "enamel", ch=0.005, grain="x")
    return [f for f in out if f]


def boh_faces():
    ni = _bi("notice")
    return [f for f in _boh_130() if not (isinstance(f, dict) and f["mat"] == ni)]


def vanilla_props():
    out = []
    for e in _vp_130():
        if e[0] in ("prop_cd_folder_pile1", "prop_cs_documents_01"):
            continue
        if e[0] in ("v_ind_cfbox", "v_ind_cs_spray", "v_res_foodjarb"):
            e = (e[0], e[1], e[2], e[3], round(e[4] / 90.0) * 90.0)
        out.append(e)
    return out


HALL_LIGHTS_FN = _lt_130


def lights():
    return []                                                    # the hall drawable carries no lights any more


def open_lights():
    """lp_open = the look the owner liked as 'closed': every hall light + the three service lights, no bright troffer lamps."""
    return list(_lt_130()) + [dict(l) for l in K9.closed_lights()]


def closed_lights():
    """lp_closed = dark: only the cooler glow and the display-case strips."""
    return [dict(l, intensity=round(l["intensity"] * 0.8, 3)) for l in _lt_130() if l["kind"] in ("cooler_glow", "case", "neon_amber")]


# ================================================================== 1.4.1 (owner picked the wall finish from a sheet, 2026-11-16)
# painted brick -> ambientCG Tiles136B (gs_15ac_walltile.py), 12 tiles of 10 cm per repeat, in the hall and the back rooms;
# the 3D brick details are dropped with the brick; day lights -2 %.
_shell_140, _part_140, _ol_140 = _PG.shell_faces, _SG.partition_faces, open_lights
_BRICKS = []
_BRICK_HOLES = []
_WK = 2.0 / 1.2
SHELL_TEX["wall"] = ("lp14_wall", "lp14_wall_n", "lp14_wall_s", 60.0, 0.6)
_PG.shell_faces = lambda *a, **k: _uvmul(_shell_140(*a, **k), 1, _WK, _WK)
_SG.partition_faces = lambda mats, *a, **k: _uvmul(_part_140(mats, *a, **k), mats.get("wall", 1), _WK, _WK)
BOH_SPECS[_bi("plaster")] = ("normal_spec.sps", {"DiffuseSampler": "lp14_wall", "BumpSampler": "lp14_wall_n", "SpecSampler": "lp14_wall_s"},
                             {"specularIntensityMult": 0.6, "specularFalloffMult": 60.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp14_wall")
_BOH_CC0_IDX[_bi("plaster")] = 1.2


def open_lights():
    return [dict(l, intensity=round(l["intensity"] * 0.98, 3)) if l.get("time") == DAY_HOURS else l for l in _ol_140()]


# ================================================================== 1.5.0 (owner's 8 screenshots of 1.4.1 + answers, 2026-11-16)
# counter back wall = the red wainscot tile; blurry floor / wall decals out; 3D: lifted floor tiles, fallen wall tiles;
# night warmer and without spot glare; sports clock + box fan (vanilla) on the two empty walls; gumball 6 cm lower.
_hf_141, _vp_141, _ol_141, _shell_141, _part_141 = hall_faces, vanilla_props, open_lights, _PG.shell_faces, _SG.partition_faces
SHELL_EXTRA_SPECS[0] = ("normal_spec.sps", {"DiffuseSampler": "lp15_backwall", "BumpSampler": "lp12_wall_tile_n", "SpecSampler": "lp12_wall_tile_s"},
                        {"specularIntensityMult": 0.75, "specularFalloffMult": 90.0, "specularFresnel": 0.97, "bumpiness": 0.4}, "lp15_backwall")
VB["prop_sports_clock_01"] = ((-0.53, -0.06, -0.53), (0.53, 0.06, 0.53))
VB["v_res_fa_fan"] = ((-0.364, -0.124, -0.364), (0.364, 0.124, 0.407))
_LIFT = ((15, 9, (0.004, 0.022, 0.012, 0.0)), (3, 4, (0.018, 0.003, 0.0, 0.010)), (-4, 13, (0.0, 0.006, 0.020, 0.009)),
         (17, 1, (0.012, 0.0, 0.004, 0.019)), (8, 17, (0.002, 0.016, 0.021, 0.006)), (19, 14, (0.015, 0.008, 0.0, 0.003)))
_TILE_HOLES = (("ch_r", 0.50, 1.95), ("ch_r", 1.00, 2.45), ("ch_r", 0.60, 2.05), ("w_pier", 0.50, 2.05), ("sw_pier", 0.30, 2.25),
               ("ch_l", 0.70, 1.65), ("ch_l", 1.20, 2.55), ("ch_l", 0.80, 1.65))
_TH_FACES = {"ch_r": ((-2.9, 2.5), (-1.84, 1.36)), "w_pier": ((-2.9, 3.46), (-2.9, 2.5)), "sw_pier": ((0.58, -1.23), (1.26, -1.23)),
             "ch_l": ((-0.52, -0.05), (0.58, -1.23))}


def _cut_tiles(f, spots):
    A, B = f["v"][0], f["v"][1]
    zhi, zlo = A[2], f["v"][3][2]
    L = math.hypot(B[0] - A[0], B[1] - A[1])
    d = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
    n = _nrm(f["v"]); nl = math.hypot(n[0], n[1]); n = (n[0] / nl, n[1] / nl, 0.0)
    uA, uB = f["uv"][0][0], f["uv"][1][0]
    vh, vl = f["uv"][0][1], f["uv"][3][1]
    du, dv = (uB - uA) / L, (vh - vl) / (zhi - zlo)
    P3 = lambda x, z, off=0.0: (A[0] + d[0] * x - n[0] * off, A[1] + d[1] * x - n[1] * off, z)
    U = lambda x, z: (uA + du * x, vl + dv * (z - zlo))
    q = lambda xa, xb, za, zb: {"v": [P3(xa, zb), P3(xb, zb), P3(xb, za), P3(xa, za)], "uv": [U(xa, zb), U(xb, zb), U(xb, za), U(xa, za)], "mat": f["mat"]}
    holes = []
    for x, z in spots:
        u, v = U(x, z)
        v0 = math.floor(v * 12) / 12.0
        r = int(math.floor((1.0 - (v0 + 1e-6 - math.floor(v0 + 1e-6))) * 12 - 1e-6))          # row from the top of the sheet
        ph = 0.0 if r % 2 == 0 else 1.0 / 24.0
        u0 = math.floor((u - ph) * 12) / 12.0 + ph
        xs = sorted(((u0 - uA) / du, (u0 + 1.0 / 12.0 - uA) / du))
        zs = sorted(((v0 - vl) / dv + zlo, (v0 + 1.0 / 12.0 - vl) / dv + zlo))
        if xs[0] > 0.05 and xs[1] < L - 0.05 and not any(xs[0] < h[1] + 0.01 and h[0] < xs[1] + 0.01 for h in holes):
            holes.append((xs[0], xs[1], zs[0], zs[1]))
    out, cur, D = [], 0.0, 0.014
    for x0, x1, z0, z1 in sorted(holes):
        g = [U(x0, z0)] * 4                                                # grout colour for the bed and the reveals
        out += [q(cur, x0, zlo, zhi), q(x0, x1, zlo, z0), q(x0, x1, z1, zhi)]
        out.append(_sq([P3(x0, z1, D), P3(x1, z1, D), P3(x1, z0, D), P3(x0, z0, D)], g, f["mat"], n))
        out.append(_sq([P3(x0, z1), P3(x0, z1, D), P3(x0, z0, D), P3(x0, z0)], g, f["mat"], (d[0], d[1], 0)))
        out.append(_sq([P3(x1, z1), P3(x1, z1, D), P3(x1, z0, D), P3(x1, z0)], g, f["mat"], (-d[0], -d[1], 0)))
        out.append(_sq([P3(x0, z0), P3(x1, z0), P3(x1, z0, D), P3(x0, z0, D)], g, f["mat"], (0, 0, 1)))
        out.append(_sq([P3(x0, z1), P3(x1, z1), P3(x1, z1, D), P3(x0, z1, D)], g, f["mat"], (0, 0, -1)))
        cur = x1
    out.append(q(cur, L, zlo, zhi))
    return out, len(holes)


def _shell_faces_150(*a, **k):
    out = []
    _shell_faces_150.holes = 0
    for f in _shell_141(*a, **k):
        if f["mat"] == _SM_TILE:
            f = dict(f, uv=[(p[1] / 0.6, p[2] / 1.0) for p in f["v"]])           # red tile, same scale as the wainscot
        elif f["mat"] == 1 and len(f["v"]) == 4 and f["v"][3][2] <= 1.01 and f["v"][0][2] > 3.0:
            sp = [(x, z) for key, x, z in _TILE_HOLES if abs(f["v"][0][0] - _TH_FACES[key][0][0]) < 0.02 and abs(f["v"][0][1] - _TH_FACES[key][0][1]) < 0.02
                  and abs(f["v"][1][0] - _TH_FACES[key][1][0]) < 0.02 and abs(f["v"][1][1] - _TH_FACES[key][1][1]) < 0.02]
            if sp:
                pcs, nh = _cut_tiles(f, sp)
                _shell_faces_150.holes += nh
                out += pcs
                continue
        out.append(f)
    for i, j, lift in _LIFT:                                              # loose floor tiles, one corner up
        s0, t0, T = i * 0.32, j * 0.32, 0.32
        c = [(s0, t0), (s0 + T, t0), (s0 + T, t0 + T), (s0, t0 + T)]
        top = [(x, y, 0.021 + h) for (x, y), h in zip(c, lift)]
        out.append(_sq(top, [(x / 1.28, y / 1.28) for x, y in c], 0, (0, 0, 1)))
        mid = ((s0 + T / 2) / 1.28, (t0 + T / 2) / 1.28)
        for a_, b_ in ((0, 1), (1, 2), (2, 3), (3, 0)):
            if lift[a_] + lift[b_] > 0.004:
                nx, ny = c[b_][1] - c[a_][1], -(c[b_][0] - c[a_][0])
                out.append(_sq([top[a_], top[b_], (c[b_][0], c[b_][1], 0.02), (c[a_][0], c[a_][1], 0.02)], [mid] * 4, 0, (nx, ny, 0)))
    return out


_PG.shell_faces = _shell_faces_150
_FLOOR_DECALS = {MAT[m] for m in ("decal", "decal5", "decal6", "floor_dmg", "puddle") if m in MAT}


def hall_faces():
    out = []
    for f in _hf_141():
        zs = [p[2] for p in f["v"]]
        if f["mat"] in _FLOOR_DECALS and max(zs) < 0.06:
            continue                                                       # blurry floor stains / patches
        if f["mat"] == MAT["floor_dmg"]:
            continue                                                       # the same patches on the wainscot
        out.append(f)
    # small steel shelf for the box fan on the wall between the beer rack and the staff door
    out += V.cbox(V.WORLD, 4.95, 5.85, 6.62, 6.93, 1.75, 1.78, "steel", ch=0.004)
    for s in (5.05, 5.75):
        out += V.cbox(V.WORLD, s - 0.012, s + 0.012, 6.64, 6.93, 1.73, 1.75, "iron")
        out += V.tube(V.WORLD, [(s, 6.92, 1.52), (s, 6.66, 1.74)], 0.007, 6, "iron")
    return [f for f in out if f]


def vanilla_props():
    out = []
    for e in _vp_141():
        if e[0] == "prop_gumball_02":
            e = (e[0], e[1], e[2], e[3] - 0.06, e[4])
        out.append(e)
    out.append(B9._on_wall("prop_sports_clock_01", (8.55, V.PG.YS), (0.0, 1.0), 1.45))
    out.append(("v_res_fa_fan", 5.40, 6.93 - 0.16, 1.782, B9.wall_yaw((0.0, -1.0))))
    return out


_NIGHT_K = {"banquette_key": 0.6, "soffit_can": 0.6, "entrance_can": 0.45, "ledge_can": 0.7, "entrance_wall_light": 0.6, "troffer": 0.7,
            "night_fill": 1.25, "booth_fill": 1.2, "market_fill": 1.2}


def open_lights():
    out = []
    for l in _ol_141():
        k = l["kind"]; fam = "troffer" if k.startswith("troffer_lamp") else k
        if l.get("time") is None and k.startswith("ah_"):                 # service lights: were on at full power day AND night
            c = l["color"]
            out.append(dict(l, time=DAY_HOURS))
            out.append(dict(l, time=NIGHT_HOURS, intensity=round(l["intensity"] * 0.35, 3), color=(1.0, 0.86, 0.66)))
            continue
        if l.get("time") == NIGHT_HOURS:
            c = l["color"]
            l = dict(l, intensity=round(l["intensity"] * _NIGHT_K.get(fam, 1.0), 3), color=(c[0], round(c[1] * 0.93, 3), round(c[2] * 0.78, 3)))
        out.append(l)
    return out


# ================================================================== 1.6.0 (owner 2026-11-16 20:13)
# counter back wall = faded Italian flag in tile (gs_15ad_flag.py); bright 24/7 stock on the back shelves; BEER neon
# instead of the big clock; COLD CUTS thermometer out; leak decals of the kitchen (ambientCG, CC0) on the hall walls;
# band behind the counter; stronger lifted floor tiles; more / wider fallen wall tiles; night lower at the walls.
_hf_150, _vp_150, _ol_150, _shell_150 = hall_faces, vanilla_props, open_lights, _PG.shell_faces
_tile_spec = lambda nm: ("normal_spec.sps", {"DiffuseSampler": nm, "BumpSampler": "lp16_tile_n", "SpecSampler": "lp16_tile_s"},
                         {"specularIntensityMult": 0.6, "specularFalloffMult": 60.0, "specularFresnel": 0.97, "bumpiness": 1.0}, nm)
SHELL_EXTRA_SPECS[0] = _tile_spec("lp16_tile_red")
SHELL_EXTRA_SPECS.append(_tile_spec("lp16_tile_green"))                                   # 8
SHELL_EXTRA_SPECS.append(("decal.sps", {"DiffuseSampler": "lp9_boh_leaks"}, {}, "lp9_boh_leaks_hall"))   # 9
_SM_GREEN, _SM_LEAK = 8, 9
for _n, _b in (("prop_beer_neon_02", ((-0.476, -0.025, -0.562), (0.476, 0.025, 0.562))), ("v_ret_247_choptom", ((-0.134, -0.134, -0.088), (0.134, 0.134, 0.088))),
               ("v_ret_247_ketchup1", ((-0.134, -0.134, -0.132), (0.134, 0.134, 0.132))), ("v_ret_247_mustard", ((-0.097, -0.134, -0.078), (0.097, 0.134, 0.078))),
               ("v_ret_247_noodle2", ((-0.166, -0.166, -0.112), (0.166, 0.166, 0.112))), ("v_ret_247_popcan2", ((-0.134, -0.134, -0.09), (0.134, 0.134, 0.09))),
               ("v_ret_247_soappowder2", ((-0.116, -0.055, -0.142), (0.116, 0.055, 0.142))), ("v_ret_247_tomsoup1", ((-0.134, -0.134, -0.088), (0.134, 0.134, 0.088))),
               ("v_ret_247_tuna", ((-0.134, -0.134, -0.064), (0.134, 0.134, 0.064))), ("v_ret_247_vegsoup1", ((-0.134, -0.134, -0.088), (0.134, 0.134, 0.088)))):
    VB[_n] = _b
_LIFT = ((15, 9, (0.008, 0.045, 0.022, 0.0)), (3, 4, (0.038, 0.006, 0.0, 0.020)), (-4, 13, (0.0, 0.012, 0.042, 0.018)), (17, 1, (0.026, 0.0, 0.008, 0.040)),
         (8, 17, (0.004, 0.034, 0.044, 0.012)), (19, 14, (0.032, 0.016, 0.0, 0.006)), (5, 10, (0.0, 0.020, 0.040, 0.010)), (11, 5, (0.036, 0.010, 0.0, 0.022)),
         (-6, 9, (0.014, 0.040, 0.018, 0.0)), (13, 18, (0.0, 0.008, 0.030, 0.038)), (16, 9, (0.020, 0.0, 0.006, 0.030)), (4, 4, (0.0, 0.024, 0.010, 0.004)))
_TILE_HOLES = (("ch_r", 0.25, 1.95), ("ch_r", 0.85, 2.45), ("ch_r", 1.25, 1.55), ("w_pier", 0.30, 2.05), ("w_pier", 0.65, 2.65), ("sw_pier", 0.20, 2.25),
               ("ch_l", 0.25, 1.65), ("ch_l", 0.75, 2.55), ("ch_l", 1.25, 1.95))
_TILE_W = {(0.25, 1.95): 3, (0.85, 2.45): 2, (1.25, 1.55): 2, (0.30, 2.05): 2, (0.65, 2.65): 2, (0.20, 2.25): 3, (0.25, 1.65): 4, (0.75, 2.55): 3, (1.25, 1.95): 2}
_cut_tiles_1 = _cut_tiles


def _cut_tiles(f, spots):
    """Strips of 2-4 fallen tiles: the one-tile cutter run with a widened sheet period."""
    A, B = f["v"][0], f["v"][1]
    zhi, zlo = A[2], f["v"][3][2]
    L = math.hypot(B[0] - A[0], B[1] - A[1])
    d = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
    n = _nrm(f["v"]); nl = math.hypot(n[0], n[1]); n = (n[0] / nl, n[1] / nl, 0.0)
    uA, uB = f["uv"][0][0], f["uv"][1][0]
    vh, vl = f["uv"][0][1], f["uv"][3][1]
    du, dv = (uB - uA) / L, (vh - vl) / (zhi - zlo)
    P3 = lambda x, z, off=0.0: (A[0] + d[0] * x - n[0] * off, A[1] + d[1] * x - n[1] * off, z)
    U = lambda x, z: (uA + du * x, vl + dv * (z - zlo))
    q = lambda xa, xb, za, zb: {"v": [P3(xa, zb), P3(xb, zb), P3(xb, za), P3(xa, za)], "uv": [U(xa, zb), U(xb, zb), U(xb, za), U(xa, za)], "mat": f["mat"]}
    holes = []
    for x, z in spots:
        w = _TILE_W.get((x, z), 1)
        u, v = U(x, z)
        v0 = math.floor(v * 12) / 12.0
        r = int(math.floor((1.0 - (v0 + 1e-6 - math.floor(v0 + 1e-6))) * 12 - 1e-6))
        ph = 0.0 if r % 2 == 0 else 1.0 / 24.0
        u0 = math.floor((u - ph) * 12) / 12.0 + ph
        xs = sorted(((u0 - uA) / du, (u0 + (w if du > 0 else -w + 1) / 12.0 - (0 if du > 0 else 1.0 / 12.0) * 0 - uA) / du)) if du > 0 else \
            sorted(((u0 + 1.0 / 12.0 - uA) / du, (u0 + 1.0 / 12.0 - w / 12.0 - uA) / du))
        zs = sorted(((v0 - vl) / dv + zlo, (v0 + 1.0 / 12.0 - vl) / dv + zlo))
        if xs[0] > 0.04 and xs[1] < L - 0.04 and not any(xs[0] < h[1] + 0.01 and h[0] < xs[1] + 0.01 for h in holes):
            holes.append((xs[0], xs[1], zs[0], zs[1]))
    out, cur, D = [], 0.0, 0.035
    g2 = [(0.30, 0.30), (0.42, 0.30), (0.42, 0.38), (0.30, 0.38)]                  # 1.7.0: red substrate, 3.5 cm deep
    for x0, x1, z0, z1 in sorted(holes):
        g = [U(x0, z0)] * 4
        out += [q(cur, x0, zlo, zhi), q(x0, x1, zlo, z0), q(x0, x1, z1, zhi)]
        out.append(_sq([P3(x0, z1, D), P3(x1, z1, D), P3(x1, z0, D), P3(x0, z0, D)], g2, _SM_TILE, n))
        out.append(_sq([P3(x0, z1), P3(x0, z1, D), P3(x0, z0, D), P3(x0, z0)], g2, _SM_TILE, (d[0], d[1], 0)))
        out.append(_sq([P3(x1, z1), P3(x1, z1, D), P3(x1, z0, D), P3(x1, z0)], g2, _SM_TILE, (-d[0], -d[1], 0)))
        out.append(_sq([P3(x0, z0), P3(x1, z0), P3(x1, z0, D), P3(x0, z0, D)], g2, _SM_TILE, (0, 0, 1)))
        out.append(_sq([P3(x0, z1), P3(x1, z1), P3(x1, z1, D), P3(x0, z1, D)], g2, _SM_TILE, (0, 0, -1)))
        cur = x1
    out.append(q(cur, L, zlo, zhi))
    return out, len(holes)


def _clip_t(vs, a, b):
    """Polygon clipped to a <= t <= b (Sutherland-Hodgman on the t coordinate)."""
    for lim, keep in ((a, lambda p: p[1] >= a - 1e-9), (b, lambda p: p[1] <= b + 1e-9)):
        out = []
        for i in range(len(vs)):
            p, q_ = vs[i], vs[(i + 1) % len(vs)]
            if keep(p):
                out.append(p)
            if keep(p) != keep(q_) and abs(q_[1] - p[1]) > 1e-9:
                k = (lim - p[1]) / (q_[1] - p[1])
                out.append(tuple(p[j] + (q_[j] - p[j]) * k for j in range(3)))
        vs = out
        if len(vs) < 3:
            return []
    return vs


_FLAG = ((4.40, 7.0, _SM_GREEN), (2.30, 4.40, 1), (-2.0, 2.30, _SM_TILE))                 # left -> right seen from the hall
_HALL_LEAKS = (((-2.30, 6.94), (0.0, -1.0), 0.90, 1.68, 1.23, "A", False), ((8.70, -1.23), (0.0, 1.0), 1.00, 1.48, 1.43, "A2", False),
               ((-2.90, 5.20), (1.0, 0.0), 0.22, 1.55, 1.36, "B", False), ((6.30, 6.94), (0.0, -1.0), 1.20, 1.16, 0.42, "C", False),
               ((6.20, -1.23), (0.0, 1.0), 1.30, 1.16, 0.40, "D", True), ((5.60, 6.94), (0.0, -1.0), 0.22, 1.82, 1.08, "B", True))


def _shell_faces_160(*a, **k):
    out = []
    for f in _shell_150(*a, **k):
        if f["mat"] == _SM_TILE:
            for t0, t1, m in _FLAG:
                vs = _clip_t([tuple(p) for p in f["v"]], t0, t1)
                if len(vs) >= 3:
                    out.append({"v": vs, "uv": [(p[1] / 1.2, p[2] / 1.2) for p in vs], "mat": m})
            continue
        out.append(f)
    for p, n, w, z0, h, key, flip in _HALL_LEAKS:
        f = leak_wall(p, n, w, z0, h, key, flip=flip)
        if f:
            out.append({"v": [tuple(q_) for q_ in f["v"]], "uv": [tuple(q_) for q_ in f["uv"]], "mat": _SM_LEAK})
    return out


_PG.shell_faces = _shell_faces_160


def hall_faces():
    src = _hf_150()
    box = None
    for f in src:
        if f["mat"] == MAT["wall6"]:
            c = [sum(p[i] for p in f["v"]) / len(f["v"]) for i in range(3)]
            if abs(c[0] - 0.89) < 0.06 and abs(c[1] + 1.22) < 0.05 and abs(c[2] - 1.48) < 0.06:
                lo, hi = _bbox(f["v"]); box = ([x - 0.07 for x in lo], [x + 0.07 for x in hi])
    out = []
    for f in src:
        lo, hi = _bbox(f["v"])
        if box and all(lo[i] >= box[0][i] and hi[i] <= box[1][i] for i in range(3)):
            continue                                                       # COLD CUTS thermometer + its frame
        out.append(f)
    z0, z1 = FRIEZE_Z                                                      # the band continues behind the counter
    for (a, b, n) in (((9.94, -1.23), (8.02, -1.23), (0.0, 1.0)), ((9.94, 6.94), (9.94, -1.23), (-1.0, 0.0)), ((8.02, 6.94), (9.94, 6.94), (0.0, -1.0))):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        Pq = lambda x, z: (a[0] + d[0] * x + n[0] * 0.004, a[1] + d[1] * x + n[1] * 0.004, z)
        V.emit(out, V.F([Pq(0, z0), Pq(L, z0), Pq(L, z1), Pq(0, z1)], "walnut", [(z0, 0.0), (z0, L), (z1, L), (z1, 0.0)], hint=(n[0], n[1], 0.0)))
    return [f for f in out if f]


def vanilla_props():
    out = []
    for e in _vp_150():
        n, s, t, zb, yaw = e
        if n == "prop_sports_clock_01":
            continue
        if 9.6 < s < 9.97 and t < 6.9 and (abs(zb - 1.455) < 0.02 or abs(zb - 1.895) < 0.02) and n != "v_ret_gc_clock":
            continue                                                       # wine, bread, jars, cups on the back shelves
        out.append(e)
    s = V.P1_S[0] - 0.15
    def put(name, t, deck):
        out.append((name, s, t, deck, 90.0))                    # z = bottom of the prop
    for name, t in (("v_ret_247_popcan2", 2.50), ("v_ret_247_mustard", 2.82), ("v_ret_247_ketchup1", 3.12), ("v_ret_247_choptom", 3.44),
                    ("v_ret_247_tuna", 3.76), ("v_ret_247_popcan2", 4.08)):
        put(name, t, 1.455)
    for name, t in (("v_ret_247_noodle2", 2.55), ("v_ret_247_vegsoup1", 2.95), ("v_ret_247_soappowder2", 3.30), ("v_ret_247_soappowder2", 3.55),
                    ("v_ret_247_tomsoup1", 3.90)):
        put(name, t, 1.895)
    for name, t, deck in (("v_ret_247_ketchup1", 1.17, 1.455), ("v_ret_247_mustard", 1.45, 1.455), ("v_ret_247_noodle2", 1.30, 1.895),
                          ("v_ret_247_tomsoup1", 5.25, 1.455), ("v_ret_247_vegsoup1", 5.55, 1.455), ("v_ret_247_popcan2", 5.40, 1.895)):
        put(name, t, deck)
    out.append(B9._on_wall("prop_beer_neon_02", (8.55, V.PG.YS), (0.0, 1.0), 1.50))
    return out


_NIGHT_W = {"banquette_key": 0.55, "ledge_can": 0.6, "entrance_can": 0.6, "entrance_wall_light": 0.5, "soffit_can": 0.7, "troffer": 0.8,
            "night_fill": 0.7, "corner_fill": 0.7, "cooler_glow": 0.8, "ah_service_counter": 0.6, "ah_service_back": 0.6, "ah_night_hall": 0.7}


def open_lights():
    out = []
    for l in _ol_150():
        k = l["kind"]; fam = "troffer" if k.startswith("troffer_lamp") else k
        if l.get("time") == NIGHT_HOURS and fam in _NIGHT_W:
            l = dict(l, intensity=round(l["intensity"] * _NIGHT_W[fam], 3))
        out.append(l)
    return out


# ================================================================== 1.7.0 (owner 2026-11-16 20:42)
# black frame round the flag; floor dirt = the kitchen leak decals laid on the hall floor; half of the loose tiles broken
# in two; fallen wall tiles deeper with a red substrate; Logger neon instead of the BEER / pistols neon.
_hf_160, _vp_160, _shell_160 = hall_faces, vanilla_props, _PG.shell_faces
VB["prop_beer_neon_04"] = ((-0.507, -0.01, -0.45), (0.714, 0.01, 0.229))
_LIFT_170, _LIFT = _LIFT, ()
_FLOOR_DIRT = (("A", 1.0, 1.4, 1.5, 0), ("A2", 4.9, 3.3, 1.3, 1), ("A", -1.3, 4.6, 1.2, 2), ("A2", 2.5, 5.7, 1.4, 3), ("A", 5.9, 5.3, 1.1, 1),
               ("A2", 5.6, 0.9, 1.3, 0), ("A", 2.6, 3.5, 1.0, 3), ("A2", -1.6, 2.6, 1.0, 2), ("A", 0.3, 5.6, 0.9, 1), ("A2", 6.3, 2.6, 0.9, 2))


def _shell_faces_170(*a, **k):
    out = list(_shell_160(*a, **k))
    for key, s, t, w, rot in _FLOOR_DIRT:
        u0, vb, u1, vt = _luv(key)
        uv = [(u0, vb), (u1, vb), (u1, vt), (u0, vt)]
        uv = uv[rot:] + uv[:rot]
        h = w / 2
        out.append(_sq([(s - h, t - h, 0.0225), (s + h, t - h, 0.0225), (s + h, t + h, 0.0225), (s - h, t + h, 0.0225)], uv, _SM_LEAK, (0, 0, 1)))
    for idx, (i, j, lift) in enumerate(_LIFT_170):
        s0, t0, T = i * 0.32, j * 0.32, 0.32
        c = [(s0, t0), (s0 + T, t0), (s0 + T, t0 + T), (s0, t0 + T)]
        U = lambda p: (p[0] / 1.28, p[1] / 1.28)
        mid = [((s0 + T / 2) / 1.28, (t0 + T / 2) / 1.28)]
        if idx % 2 == 0:
            parts = [([0, 1, 2, 3], list(lift))]
        else:                                                    # snapped along the diagonal: the second half lies lower
            lo = (max(lift[0] - 0.014, 0.0), 0.0, max(lift[2] - 0.014, 0.0), lift[3])
            parts = [([0, 1, 2], [lift[0], lift[1], lift[2]]), ([0, 2, 3], [lo[0], lo[2], lo[3]])]
            out.append(_sq([(c[0][0], c[0][1], 0.021 + lift[0]), (c[2][0], c[2][1], 0.021 + lift[2]), (c[2][0], c[2][1], 0.021 + lo[2]),
                            (c[0][0], c[0][1], 0.021 + lo[0])], mid * 4, 0, (-1, 1, 0)))
        for ids, hs in parts:
            top = [(c[q_][0], c[q_][1], 0.021 + h_) for q_, h_ in zip(ids, hs)]
            out.append(_sq(top, [U(p) for p in top], 0, (0, 0, 1)))
            for e in range(len(ids)):
                a_, b_ = top[e], top[(e + 1) % len(ids)]
                if (a_[2] + b_[2]) / 2 > 0.024 and (abs(a_[0] - b_[0]) < 1e-6 or abs(a_[1] - b_[1]) < 1e-6):      # outer edges only
                    cx, cy = s0 + T / 2, t0 + T / 2
                    mx, my = (a_[0] + b_[0]) / 2 - cx, (a_[1] + b_[1]) / 2 - cy
                    out.append(_sq([a_, b_, (b_[0], b_[1], 0.02), (a_[0], a_[1], 0.02)], mid * 4, 0, (mx, my, 0)))
    return out


_PG.shell_faces = _shell_faces_170


def hall_faces():
    out = list(_hf_160())
    s1 = V.P1_S[0] - 0.006                                        # black frame round the flag, like a picture
    for (t0, t1, z0, z1) in ((0.16, 6.54, 2.37, 2.42), (0.16, 6.54, 0.97, 1.02), (0.16, 0.21, 1.02, 2.37), (6.49, 6.54, 1.02, 2.37)):
        out += V.cbox(V.WORLD, s1 - 0.022, s1, t0, t1, z0, z1, "iron", ch=0.004)
    return [f for f in out if f]


def vanilla_props():
    out = [e for e in _vp_160() if e[0] != "prop_beer_neon_02"]
    out.append(B9._on_wall("prop_beer_neon_04", (8.50, V.PG.YS), (0.0, 1.0), 1.75))
    return out


# ================================================================== 1.8.0 REMASTER PASS 1 (owner's directive 2026-11-17)
# Work zone behind the counter regrouped into stations (sandwich prep over the fridge block / slicing + wrapping / service),
# the two pairs of small side wall shelves removed (knife bar + hand-wash notice instead, the green panel stays empty),
# shelf stock in category blocks with a free end, deli cases sorted (hero case = salumi, second case = cheese + antipasti)
# with printed price tickets, steel joint profiles between the tile bands, PAY HERE / EMPLOYEES ONLY / table menu cards,
# reserve cartons at the counter-side gondola ends. Blinds, booths, shelving units, lights: NOT touched.
import json as _json18, random as _rnd18
_hf_170b, _vp_170b = hall_faces, vanilla_props
MAT["signs18"] = len(SHADER_SPECS)
SHADER_SPECS.append(("normal_spec.sps", {"DiffuseSampler": "lp18_signs", "BumpSampler": "lp_flat_n", "SpecSampler": "lp_matte_s"},
                     {"specularIntensityMult": 0.15, "specularFalloffMult": 10.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp18_signs"))
V.REP.update({"signs18": 1.0})
import pathlib as _pl18
_S18 = _json18.loads((_pl18.Path(__file__).resolve().parents[1] / "textures" / "v180" / "lp18_signs.json").read_text())["regions"]


def _s18(key, pad=2.0):
    x0, y0, x1, y1 = _S18[key]
    return ((x0 + pad) / 512.0, 1.0 - (y1 - pad) / 512.0, (x1 - pad) / 512.0, 1.0 - (y0 + pad) / 512.0)


def _card18(bl, br, tr, tl, key, hint, back=True):
    """Printed card: corners as the reader sees them (bottom-left, bottom-right, top-right, top-left)."""
    out = []
    u0, vb, u1, vt = _s18(key)
    V.emit(out, V.F([bl, br, tr, tl], "signs18", [(u0, vb), (u1, vb), (u1, vt), (u0, vt)], hint=hint))
    if back:
        m = ((u0 + u1) / 2, vb + 0.004)
        V.emit(out, V.F([br, bl, tl, tr], "signs18", [m] * 4, hint=(-hint[0], -hint[1], -hint[2])))
    return out


_CASE18 = {True: ((("salami_fan", 1.15), ("prosciutto_fold", 1.0), ("mortadella", 1.0), ("salami_fine", 0.9), ("prosciutto_fold", 1.0)),
                  (("salami_logs", 1.2), ("mortadella", 1.0), ("salami_fine", 0.9), ("salami_logs", 1.0))),
           False: ((("cheese_wedges", 1.1), ("mozzarella", 0.9), ("provolone_cut", 1.0), ("olives_green", 0.8), ("peppers", 0.9), ("olives_black", 0.8)),
                   (("provolone_cut", 1.1), ("cheese_wedges", 1.0), ("mozzarella", 0.9), (None, 0.45), ("peppers", 0.9)))}


def _case_food_180(t0, t1, hero):
    out = []
    fr = V.front_frame(t0)
    L = t1 - t0
    e, deck = 0.035, 0.88
    out += V.cbox(fr, e, L - e, 0.44, 0.80, deck, deck + 0.05, "iron", grain="x", skip=("-z",))    # riser
    rng = _rnd18.Random(18 if hero else 81)
    usable = L - 2 * e - 0.02
    front, back = _CASE18[bool(hero)]
    for items, (y0, y1), z in ((front, (0.10, 0.40), deck), (back, (0.47, 0.78), deck + 0.05)):
        tot = sum(w for _k, w in items)
        x = e + 0.01
        for kind, wt in items:
            w = usable * wt / tot
            x0, x1 = x + 0.008, x + w - 0.008
            x += w
            if kind is None:
                continue                                                  # sold-out gap: bare riser
            out += V.tray(fr, x0, x1, y0, y1, z)
            out += V.tray_food(fr, kind, x0 + 0.012, x1 - 0.012, y0 + 0.012, y1 - 0.012, z + 0.006, rng)
            px = (x0 + x1) / 2 + rng.uniform(-0.02, 0.02)
            out += V.tube(fr, [(px, y0 + 0.01, z + 0.01), (px, y0 + 0.012, z + 0.07)], 0.0016, 4, "steel")
            a, b = fr.p(px - 0.046, y0 + 0.004, z + 0.058), fr.p(px + 0.046, y0 + 0.004, z + 0.058)
            c, d = fr.p(px + 0.046, y0 + 0.016, z + 0.104), fr.p(px - 0.046, y0 + 0.016, z + 0.104)
            out += _card18(a, b, c, d, "tag_" + kind, fr.v(0, -1, 0.3))
    return [f for f in out if f]


def _counters_faces_180():
    out = []
    for k, (t0, t1) in enumerate(V.CASES_T):
        out += V.deli_case(t0, t1, hero=(k == 0))
        out += _case_food_180(t0, t1, hero=(k == 0))
    out += V.counter_body(V.REGISTER_T[0], V.REGISTER_T[1], 1.02)
    out += V.counter_body(V.COFFEE_T[0], V.COFFEE_T[1], 1.05)
    out += V.counter_body(V.GATE_T[0], V.GATE_T[1], 1.02)
    out += V.back_counter()
    out += V.slicer(V.BACK_S[0] + 0.33, 2.85, math.radians(-90))          # slicing + wrapping station (white band)
    out += V.paper_roll(V.BACK_S[0] + 0.35, 3.45, math.radians(-90))
    out += V.prosciutto_stand(V.BACK_S[0] + 0.33, 4.05, math.radians(90))
    out += V.hanging_rail()
    return out


V.counters_faces = _counters_faces_180
_BENCH18 = {"prop_food_tray_01", "prop_radio_01", "v_res_fa_chopbrd", "prop_cleaver", "v_res_fa_bread01", "v_res_fa_bread02", "prop_knife_stand"}
_GATE_FACE_S = 6.966                                                      # customer face of the gate counter (measured from the faces)


def hall_faces():
    out = []
    for f in _hf_170b():
        vs = f["v"]
        S = [v[0] for v in vs]; T = [v[1] for v in vs]; Z = [v[2] for v in vs]
        if f["mat"] in (MAT["walnut"], MAT["iron"]) and min(S) > 9.6 and 1.15 < min(Z) and max(Z) < 1.93 and \
                any(min(T) >= a - 0.01 and max(T) <= b + 0.01 for a, b in _BOARDS_T):
            continue                                                      # the four small side shelves
        out.append(f)
    s1 = V.P1_S[0] - 0.006
    for t in (2.30, 4.40):                                                # steel joint profile between the tile bands
        out += V.cbox(V.WORLD, s1 - 0.012, s1, t - 0.011, t + 0.011, 1.02, 2.37, "steel", ch=0.003, grain="z")
    # sandwich station: ingredient pans against the wall over the under-counter fridge
    bf = V.Frame((V.BACK_S[0], V.BACK_T[1], 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    rng = _rnd18.Random(5)
    for k, kind in enumerate(("peppers", "mozzarella", "olives_green", "salami_fan")):
        ta = 0.42 + k * 0.20
        x0, x1 = V.BACK_T[1] - ta - 0.185, V.BACK_T[1] - ta
        out += V.tray(bf, x0, x1, 0.40, 0.66, 0.92, h=0.05)
        out += V.tray_food(bf, kind, x0 + 0.012, x1 - 0.012, 0.412, 0.648, 0.926, rng)
    # magnetic knife bar on the red panel
    out += V.cbox(V.WORLD, s1 - 0.016, s1, 1.36, 1.92, 1.52, 1.555, "iron", ch=0.003, grain="x")
    for k, (t, bl, w) in enumerate(((1.44, 0.20, 0.034), (1.54, 0.17, 0.028), (1.63, 0.22, 0.045), (1.74, 0.13, 0.022), (1.83, 0.15, 0.024))):
        out += V.cbox(V.WORLD, s1 - 0.020, s1 - 0.016, t - w / 2, t + w / 2, 1.555 - bl, 1.56, "steel", grain="z")
        out += V.cbox(V.WORLD, s1 - 0.028, s1 - 0.010, t - 0.011, t + 0.011, 1.555 - bl - 0.105, 1.555 - bl, "rubber", ch=0.003, grain="z")
    # hand-wash notice (red panel), PAY HERE tent at the till, EMPLOYEES ONLY on the gate counter, menu tents on the booth tables
    out += _card18((s1 - 0.004, 1.02, 1.62), (s1 - 0.004, 0.80, 1.62), (s1 - 0.004, 0.80, 1.767), (s1 - 0.004, 1.02, 1.767), "wash", (-1, 0, 0), back=False)
    ps, pt = 7.10, 5.33
    out += V.cbox(V.WORLD, ps - 0.012, ps + 0.030, pt - 0.105, pt + 0.105, 1.02, 1.028, "steel", ch=0.002, grain="y")
    out += _card18((ps, pt + 0.10, 1.028), (ps, pt - 0.10, 1.028), (ps + 0.022, pt - 0.10, 1.103), (ps + 0.022, pt + 0.10, 1.103), "pay", (-1, 0, 0.3))
    gs_ = _GATE_FACE_S - 0.004
    out += _card18((gs_, 0.24, 0.66), (gs_, -0.16, 0.66), (gs_, -0.16, 0.81), (gs_, 0.24, 0.81), "staff", (-1, 0, 0), back=False)
    for sc in (1.60, 3.44, 5.29):
        tt, z = -0.86, 0.772
        out += _card18((sc + 0.045, tt, z), (sc - 0.045, tt, z), (sc - 0.045, tt - 0.022, z + 0.09), (sc + 0.045, tt - 0.022, z + 0.09), "menu", (0, 1, 0.3))
        out += _card18((sc - 0.045, tt - 0.044, z), (sc + 0.045, tt - 0.044, z), (sc + 0.045, tt - 0.022, z + 0.09), (sc - 0.045, tt - 0.022, z + 0.09), "menu",
                       (0, -1, 0.3))
    return [f for f in out if f]


def vanilla_props():
    out = []
    for e in _vp_170b():
        n, s, t, zb, yaw = e
        if 9.2 < s < 9.97 and t < 6.9:
            if n in _BENCH18 and 0.9 < zb < 1.0:
                continue
            if n.startswith("v_ret_247_") and 1.4 < zb < 1.95:
                continue
            if n == "prop_cs_paper_cup" and zb > 2.4:
                continue
        out.append(e)
    b0 = V.BACK_S[0]
    out += [("v_res_fa_chopbrd", b0 + 0.20, 0.80, 0.92, 90.0), ("prop_cleaver", b0 + 0.18, 0.84, 0.94, 70.0),
            ("v_res_fa_bread01", b0 + 0.50, 1.36, 0.92, 10.0), ("v_res_fa_bread02", b0 + 0.52, 1.56, 0.92, -8.0),
            ("prop_knife_stand", b0 + 0.60, 2.02, 0.92, 0.0), ("prop_radio_01", b0 + 0.58, 4.80, 0.92, -90.0)]
    out += [("prop_food_tray_01", b0 + 0.22, 1.82, 0.92 + 0.015 * k, 90.0) for k in range(4)]
    for (s, t, n_) in ((b0 + 0.56, 5.36, 6), (b0 + 0.56, 5.46, 5), (b0 + 0.47, 5.41, 3)):       # cup sleeves by the coffee machine
        out += [("prop_cs_paper_cup", s, t, 0.92 + 0.022 * k, 0.0) for k in range(n_)]
    s = V.P1_S[0] - 0.15
    for name, t in (("v_ret_247_ketchup1", 2.53), ("v_ret_247_ketchup1", 2.81), ("v_ret_247_mustard", 3.07), ("v_ret_247_mustard", 3.29),
                    ("v_ret_247_choptom", 3.66), ("v_ret_247_tuna", 3.94)):
        out.append((name, s, t, 1.455, 90.0))
    for name, t in (("v_ret_247_tomsoup1", 2.53), ("v_ret_247_tomsoup1", 2.81), ("v_ret_247_vegsoup1", 3.09), ("v_ret_247_noodle2", 3.43),
                    ("v_ret_247_noodle2", 3.79)):
        out.append((name, s, t, 1.895, 90.0))
    # reserve stock at the counter-side ends of the two gondolas (aisle to the counter stays 2 m wide)
    out += [("prop_cardbordbox_02a", 4.99, 2.36, 0.01, 90.0), ("v_ind_cfbox", 4.97, 2.30, 0.39, 15.0), ("prop_paper_box_01", 4.90, 4.63, 0.01, 0.0)]
    return out


# ================================================================== 1.8.1 (owner's 2 screenshots of 1.8.0, 2026-11-17 00:41)
# floor dirt decals did not show in game -> 4.5 mm higher; the wall shelf by the extinguisher was empty (v_res_fa_fan does not
# render) -> jar + wine like the upper shelf; office-paper carton at the gondola end -> plain carton; TAKE OUT card on the
# register counter front.
_hf_180, _vp_180, _shell_180 = hall_faces, vanilla_props, _PG.shell_faces


def _shell_faces_181(*a, **k):
    out = []
    for f in _shell_180(*a, **k):
        if f["mat"] == _SM_LEAK and max(v[2] for v in f["v"]) < 0.1:
            f = dict(f, v=[(v[0], v[1], 0.027) for v in f["v"]])
        out.append(f)
    return out


_PG.shell_faces = _shell_faces_181


def hall_faces():
    out = list(_hf_180())
    gs_ = _GATE_FACE_S - 0.004
    out += _card18((gs_, 5.24, 0.60), (gs_, 4.96, 0.60), (gs_, 4.96, 0.787), (gs_, 5.24, 0.787), "takeout", (-1, 0, 0), back=False)
    return [f for f in out if f]


def vanilla_props():
    out = []
    for e in _vp_180():
        if e[0] == "v_res_fa_fan" and e[2] < 6.95:
            continue
        if e[0] == "prop_paper_box_01" and abs(e[1] - 4.90) < 0.01 and abs(e[2] - 4.63) < 0.01:
            e = ("prop_cardbordbox_03a", 5.00, 4.63, 0.01, 0.0)
        out.append(e)
    out += [("v_res_foodjarc", 5.22, 6.81, 1.782, 0.0), ("prop_wine_red", 5.45, 6.81, 1.782, 0.0), ("prop_wine_bot_01", 5.57, 6.82, 1.782, 0.0)]
    return out


# ================================================================== 1.8.2 (owner 2026-11-17 00:46: "витрина должна быть лучше смоделирована, лучше стекло")
# Deli cases remodelled: curved one-piece front glass (vertical foot, 30 cm radius, flat top) in two bays with a silicone joint,
# glass ends cut to the same curve with a stainless edge tube, glass-to-shelf channel, light housing under the top, thermostat
# on the staff side. Same footprint, deck, service shelf height and collision as before.
import gs_counter32 as _C32
_vp_181 = vanilla_props
_CASE_R, _CASE_Z0 = 0.305, 1.00
_CASE_PROF = [(0.045, 0.90), (0.047, _CASE_Z0)] + [(0.047 + _CASE_R - _CASE_R * math.cos(math.radians(a)), _CASE_Z0 + _CASE_R * math.sin(math.radians(a)))
                                                    for a in (10, 20, 30, 40, 50, 60, 70, 80, 90)]


def _deli_case_182(t0, t1, hero=False):
    C = _C32
    cbox, tube, prism = V.cbox, V.tube, V.prism
    out = []
    fr = V.front_frame(t0)
    L = t1 - t0
    p = 0.032
    zs, zg = 0.86, 0.90
    zt = _CASE_Z0 + _CASE_R                              # 1.305: top of the glass
    ytop = _CASE_PROF[-1][0]                             # 0.352: where the curve turns flat
    yr, ym = 0.84, 0.50
    out += C._front(fr, t0, t1, louvre=True)
    # insulated body, staff-side doors with pulls, work ledge (as before)
    out += cbox(fr, 0.0, L, 0.036, 0.98, C.Z_KICK, zs, "enamel", grain="x", skip=("-y", "-z", "+z"))
    for k in range(2):
        xa, xb = 0.02 + k * (L - 0.02) / 2, (k + 1) * (L - 0.02) / 2
        out += cbox(fr, xa, xb, 0.98, 1.0, C.Z_KICK + 0.02, 0.84, "enamel", ch=0.004, grain="z")
        out += cbox(fr, xb - 0.10, xb - 0.04, 1.0, 1.02, 0.70, 0.72, "steel", ch=0.003, grain="x")
    out += cbox(fr, 0.0, L, 0.86, 1.03, 0.945, 0.97, "steel", ch=0.004, grain="x")
    out += cbox(fr, 0.06, 0.17, 1.0, 1.012, 0.74, 0.80, "iron", ch=0.003, grain="x")                       # thermostat
    out += cbox(fr, 0.075, 0.115, 1.012, 1.014, 0.757, 0.783, "glow", grain="x")
    # white display deck, stainless sill all round
    out += cbox(fr, p, L - p, 0.05, yr, zs, zs + 0.02, "enamel", grain="x", skip=("-z",))
    out += cbox(fr, 0.0, L, 0.018, 0.062, zs, zg, "steel", ch=0.004, grain="x")
    out += cbox(fr, 0.0, L, yr, yr + p, zs, zg, "steel", ch=0.004, grain="x")
    # ends: glass cut to the curve, stainless edge tube, rear post, base sill
    side = [(0.045, zg), (yr, zg), (yr, zt)] + [q for q in reversed(_CASE_PROF[1:])]
    for xa, xb in ((0.010, 0.016), (L - 0.016, L - 0.010)):
        out += prism(fr, side, xa, xb, "glass", caps=(True, True))
    for x in (0.013, L - 0.013):
        out += tube(fr, [(x, y, z) for y, z in _CASE_PROF] + [(x, ym, zt)], 0.011, 8, "steel", caps=True)
    for xa, xb in ((0.0, p), (L - p, L)):
        out += cbox(fr, xa, xb, 0.060, yr, zs, zg, "steel", ch=0.004, grain="y")
        out += cbox(fr, xa, xb, yr, yr + p, zg, zt + 0.035, "steel", ch=0.003, grain="z")
    # curved front glass in two bays + flat top strip, silicone joint in the middle
    prof = _CASE_PROF + [(ym - 0.008, zt)]
    for xa, xb in ((0.024, L / 2 - 0.003), (L / 2 + 0.003, L - 0.024)):
        for (y0, z0), (y1, z1) in zip(prof[:-1], prof[1:]):
            vs = [fr.p(xa, y0, z0), fr.p(xb, y0, z0), fr.p(xb, y1, z1), fr.p(xa, y1, z1)]
            n = fr.v(0.0, -(z1 - z0), (y1 - y0))
            V.emit(out, V.F(vs, "glass", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=n, smooth=True))
            V.emit(out, V.F(vs, "glass", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=tuple(-c for c in n), smooth=True))
    out += tube(fr, [(L / 2, y, z) for y, z in prof], 0.004, 6, "rubber")
    # glass-to-shelf channel, stainless service shelf with a rolled lip (hand-over point)
    out += cbox(fr, 0.0, L, ym - 0.012, ym + 0.004, zt - 0.012, zt + 0.008, "steel", ch=0.002, grain="x")
    out += cbox(fr, 0.0, L, ym, yr + p + 0.03, zt + 0.005, zt + 0.035, "steel", ch=0.005, grain="x")
    out += tube(fr, [(0.0, ym, zt + 0.023), (L, ym, zt + 0.023)], 0.013, 8, "steel", caps=True)
    # light housing under the flat top, shining down on the front row
    out += cbox(fr, p + 0.02, L - p - 0.02, ytop + 0.03, ytop + 0.10, zt - 0.034, zt - 0.008, "steel", ch=0.004, grain="x")
    out += cbox(fr, p + 0.04, L - p - 0.04, ytop + 0.04, ytop + 0.09, zt - 0.040, zt - 0.034, "glow", grain="x", skip=("+z",))
    # rear sliding glass doors in a steel track, pulls
    out += cbox(fr, p, L - p, yr - 0.040, yr, zg, zg + 0.012, "steel", grain="x")
    for k in range(2):
        xa, xb = p + k * (L - 2 * p) / 2, p + (k + 1) * (L - 2 * p) / 2
        yy = yr - 0.03 + 0.012 * k
        C._glass(out, [fr.p(xa - 0.02 * k, yy, zg + 0.012), fr.p(xb + 0.02 * (1 - k), yy, zg + 0.012), fr.p(xb + 0.02 * (1 - k), yy, zt), fr.p(xa - 0.02 * k, yy, zt)],
                 fr.v(0.0, 1.0, 0.0))
        out += cbox(fr, xb - 0.06, xb - 0.03, yy + 0.002, yy + 0.016, 1.0, 1.16, "steel", grain="z")
    # price-tag rail along the inside of the front sill
    out += cbox(fr, p, L - p, 0.064, 0.070, zg, zg + 0.028, "enamel", grain="x")
    return [f for f in out if f]


V.deli_case = _deli_case_182


def vanilla_props():
    out = []
    for e in _vp_181():
        if e[0] == "v_ret_ml_scale" and 6.9 < e[1] < 8.0:
            e = (e[0], e[1], e[2], e[3] + 0.005, e[4])                    # service shelf top is 5 mm higher now
        out.append(e)
    out += [("prop_paper_bag_small", 7.70, 3.52, 1.375, 0.0), ("prop_paper_bag_small", 7.70, 3.62, 1.375, 0.0), ("prop_paper_bag_small", 7.72, 3.72, 1.375, 0.0)]
    return out


# ================================================================== 1.9.0 (owner's 20 screenshots of 1.8.x, 2026-11-17 01:05)
# Service line rebuilt: gate counter removed (the line starts at the glass case; low board partition + staff saloon doors),
# ONE service counter at 1.02 with a dark marble top (ambientCG Marble009) instead of the two cream tops with a step,
# stainless carcass. Slicer and knives modelled from scratch, olives / peppers in 3D, price tickets no longer mirrored,
# tinted case glass. Removed: W-wall frieze lettering + the leak there, the two high wall shelves on the cooler wall,
# CAFFE ESPRESSO, LONG PIG DELI banner, Logger + BEER neons, TAKE OUT / EMPLOYEES ONLY cards, kitchen door clock + clipboard.
# Staff door in P2: v_ilev_cor_firedoor (wood, vision panel) instead of the flat grey steel leaf.
_hf_182, _vp_182, _shell_182 = hall_faces, vanilla_props, _PG.shell_faces
MAT["stone19"] = len(SHADER_SPECS)
SHADER_SPECS.append(("normal_spec.sps", {"DiffuseSampler": "lp19_stone", "BumpSampler": "lp19_stone_n", "SpecSampler": "lp19_stone_s"},
                     {"specularIntensityMult": 1.1, "specularFalloffMult": 110.0, "specularFresnel": 0.97, "bumpiness": 0.6}, "lp19_stone"))
V.REP.update({"stone19": 1.0})
SHADER_SPECS[MAT["glass"]] = ("glass_env.sps", {"DiffuseSampler": "lp19_case_glass", "BumpSampler": "gs_proto_flat_n", "SpecSampler": "gs_proto_glass_s"},
                              {"specularIntensityMult": 1.4, "specularFalloffMult": 120.0, "specularFresnel": 0.97, "bumpiness": 0.2}, "lp2_case_glass")
SVC_T = (V.REGISTER_T[0], V.COFFEE_T[1])                                   # 4.80 .. 6.85
_GATE_BOX = (6.85, 8.10, -0.47, 0.472)
_BELL_OLD = K9.BELL
_BELL_D = (-0.14, 5.60)
K9.BELL = (_BELL_OLD[0] + _BELL_D[0], _BELL_OLD[1] + _BELL_D[1], _BELL_OLD[2])
SG.P2_DOOR = (8.30, 8.30 + B9.door_w("kitchen") + 0.02)


def _hall_doors_190():
    out = []
    arch, pos, yaw = B9.door_entity("kitchen", "t", (SG.P1_S[0] + SG.P1_S[1]) / 2, SG.P1_DOOR[0], SG.P1_DOOR[1])
    out.append(("gs_kitchen", arch, pos, yaw))
    arch, pos, yaw = B9.door_entity("kitchen", "s", (SG.P2_T[0] + SG.P2_T[1]) / 2, SG.P2_DOOR[0], SG.P2_DOOR[1])
    out.append(("gs_staff_p2", arch, pos, yaw))
    return out


K9.hall_doors = hall_doors = _hall_doors_190


def _zframe(o, xd, yd):
    """Frame whose 'x' is world up: prism() then extrudes a plan outline vertically (prof = (local x, local y))."""
    return V.Frame(o, (0.0, 0.0, 1.0), xd, yd)


def _service_counter_190():
    C = _C32
    cbox, prism = V.cbox, V.prism
    t0, t1 = SVC_T
    out = []
    fr = V.front_frame(t0)
    L = t1 - t0
    g0, g1 = C._ext(t0, t1)
    zt, zc = 1.02, 0.982
    out += C._front(fr, t0, t1)
    out += cbox(fr, -g0, L + g1, 0.036, 0.060, C.Z_KICK, zc, "steel", grain="x", skip=("-z", "+z"))                 # closed back of the front
    out += cbox(fr, -g0, L + g1, 0.024, 0.060, C.Z_BUMP1, zc, "steel", ch=0.003, grain="x", skip=("+y", "+z"))      # stainless apron
    for xa, xb in ((0.0, 0.03), (L * 0.44 - 0.015, L * 0.44 + 0.015), (L - 0.03, L)):
        out += cbox(fr, xa, xb, 0.060, 0.985, C.Z_KICK, zc, "steel", ch=0.003, grain="z", skip=("-z", "+z"))
    for z in (C.Z_KICK, 0.48):
        out += cbox(fr, 0.03, L - 0.03, 0.060, 0.975, z, z + 0.025, "steel", ch=0.003, grain="x")
    out += cbox(fr, 0.0, L, 0.060, 0.985, zc - 0.03, zc, "steel", grain="x", skip=("+z",))                           # top rail under the slab
    for k in range(2):                                                                                              # drawers by the till (staff side)
        xa, xb = 0.04 + k * 0.42, 0.04 + (k + 1) * 0.42 - 0.012
        out += cbox(fr, xa, xb, 0.985, 1.003, 0.78, 0.945, "steel", ch=0.004, grain="x")
        out += cbox(fr, xa + 0.13, xb - 0.13, 1.003, 1.022, 0.855, 0.872, "iron", ch=0.003, grain="x")
    # marble slab with a bullnose customer edge
    out += cbox(fr, -g0, L + g1, -0.012, 1.01, zc, zt, "stone19", ch=0.004, grain="x", skip=("-z",))
    nose = V.round_rect(-0.048, -0.010, zc - 0.004, zt, 0.019, seg=4, corners=(1, 0, 1, 0))
    out += prism(fr, nose, -g0, L + g1, "stone19", smooth="all", caps=(True, True))
    return out


SALOON = dict(s=V.COUNTER_FRONT, ta=-0.735, tb=0.405, w=0.56)             # hinge line, hinge t of the two leaves, leaf width (client/saloon.lua)


def _saloon_190():
    """1.9.1: short board-clad stub wall + two posts. The two leaves are the prop lp_saloon_leaf (gs_44), swung by client/saloon.lua."""
    C = _C32
    cbox = V.cbox
    out = []
    s0 = V.COUNTER_FRONT
    ta, tb = V.PG.YS + 0.004, -0.80
    out += cbox(V.WORLD, s0 - 0.025, s0 + 0.025, ta, tb, 0.0, 0.985, "iron", grain="z", skip=("-z", "+z"))              # core (1.9.2: dark)
    k = 0
    while ta + k * C.PITCH < tb - 0.02:
        t0_, t1_ = ta + k * C.PITCH + 0.003, min(ta + (k + 1) * C.PITCH - 0.003, tb)
        for sa, sb in ((s0 - 0.040, s0 - 0.025), (s0 + 0.025, s0 + 0.040)):
            out += cbox(V.WORLD, sa, sb, t0_, t1_, 0.12, 0.985, C.BOARD_MAT, ch=0.002, grain="z")
        k += 1
    out += cbox(V.WORLD, s0 - 0.044, s0 + 0.044, ta, tb, 0.0, 0.12, "steel", ch=0.003, grain="x", skip=("-z",))       # kick plates
    out += cbox(V.WORLD, s0 - 0.055, s0 + 0.055, ta, tb + 0.055, 0.985, 1.02, "stone19", ch=0.006, grain="y", skip=("-z",))  # wood cap
    for t in (tb + 0.025, SALOON["tb"] + 0.035):                                                                      # posts
        out += cbox(V.WORLD, s0 - 0.028, s0 + 0.028, t - 0.025, t + 0.025, 0.0, 1.005 if t > 0 else 0.985, "steel", ch=0.006, grain="z", skip=("-z",))
    out += cbox(V.WORLD, s0 - 0.036, s0 + 0.036, SALOON["tb"] + 0.002, SALOON["tb"] + 0.068, 1.005, 1.02, "steel", ch=0.004)     # 1.9.2: level with the stub wall
    return out


def _slicer_190(sc, tc):
    """Gravity-feed deli slicer, operator on the -s side. Local x = +t (blade axis), y = +s, on the bench top."""
    cbox, lathe, tube, prism = V.cbox, V.lathe, V.tube, V.prism
    zb = 0.92
    f = V.Frame((sc, tc, zb), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    out = []
    for x in (-0.20, 0.20):
        for y in (-0.14, 0.14):
            out += cbox(f, x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.0, 0.014, "rubber", ch=0.004)
    zf = _zframe((sc, tc, zb + 0.014), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
    out += prism(zf, V.round_rect(-0.24, 0.24, -0.17, 0.17, 0.05, seg=4), 0.0, 0.062, "enamel", smooth="all", caps=(True, True))      # base casting
    out += prism(zf, V.round_rect(-0.235, 0.235, -0.165, 0.165, 0.048, seg=4), 0.062, 0.068, "steel", smooth="all", caps=(True, True))
    zm = _zframe((sc, tc, zb + 0.082), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
    out += prism(zm, V.round_rect(-0.225, -0.035, 0.0, 0.155, 0.045, seg=4), 0.0, 0.15, "enamel", smooth="all", caps=(True, True))    # motor housing
    out += prism(zm, V.round_rect(-0.205, -0.055, 0.02, 0.135, 0.04, seg=4), 0.15, 0.172, "enamel", smooth="all", caps=(True, True))
    # blade: dished disc on a hub, axis = local x, at x = -0.02
    bz = 0.082 + 0.155
    bf = V.Frame(f.p(-0.030, 0.005, bz), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))               # z' = +t
    R = 0.150
    out += lathe(bf, [(0.0, 0.030), (0.034, 0.030), (0.040, 0.018), (0.060, 0.012), (R - 0.012, 0.004), (R, 0.0)], 28, "steel")
    out += lathe(bf, [(R, 0.0), (R - 0.004, -0.004), (0.0, -0.004)], 28, "steel")
    out += lathe(bf, [(0.0, 0.040), (0.016, 0.040), (0.020, 0.030)], 12, "iron")                          # hub nut
    ring = [f.p(-0.036, 0.005 + (R + 0.012) * math.cos(a), bz + (R + 0.012) * math.sin(a)) for a in [math.radians(d) for d in range(-35, 216, 12)]]
    out += tube(V.WORLD, ring, 0.014, 8, "enamel", caps=True)                                             # blade guard (back + top)
    out += cbox(f, -0.075, -0.005, 0.02, 0.10, bz + R + 0.012, bz + R + 0.075, "enamel", ch=0.012)        # sharpener housing
    out += lathe(V.Frame(f.p(-0.040, 0.06, bz + R + 0.075), (1, 0, 0), (0, 1, 0), (0, 0, 1)), [(0.0, 0.0), (0.016, 0.0), (0.018, 0.012), (0.0, 0.016)], 10, "rubber")
    # gauge plate in front of the blade (operator side), product carriage with fence and pusher on the right
    out += cbox(f, -0.012, 0.000, -0.150, -0.005, 0.085, 0.30, "steel", ch=0.004, grain="z")
    out += cbox(f, 0.012, 0.235, -0.150, 0.150, 0.105, 0.117, "steel", ch=0.004, grain="x")               # carriage table
    out += cbox(f, 0.223, 0.235, -0.150, 0.150, 0.117, 0.255, "steel", ch=0.004, grain="z")               # end fence
    out += cbox(f, 0.012, 0.235, 0.138, 0.150, 0.117, 0.21, "steel", ch=0.004, grain="x")                 # back fence
    out += cbox(f, 0.04, 0.215, -0.02, 0.002, 0.117, 0.215, "steel", ch=0.004, grain="x")                 # pusher plate
    out += tube(V.WORLD, [f.p(0.13, -0.02, 0.19), f.p(0.13, -0.085, 0.215)], 0.008, 8, "steel")
    out += lathe(V.Frame(f.p(0.13, -0.085, 0.215), (1, 0, 0), (0, 0, 1), (0, -1, 0)), [(0.0, -0.004), (0.02, 0.0), (0.024, 0.02), (0.016, 0.042), (0.0, 0.046)], 12, "rubber")
    out += tube(V.WORLD, [f.p(0.02, 0.0, 0.092), f.p(0.23, 0.0, 0.092)], 0.007, 8, "steel")               # slide rod
    # thickness dial, switch with pilot light, cable gland
    out += lathe(V.Frame(f.p(-0.13, -0.17, 0.047), (1, 0, 0), (0, 0, 1), (0, -1, 0)), [(0.0, 0.0), (0.032, 0.0), (0.032, 0.022), (0.024, 0.03), (0.0, 0.03)], 16, "rubber")
    out += cbox(f, -0.215, -0.17, -0.172, -0.168, 0.03, 0.06, "iron", grain="x")
    out += cbox(f, -0.206, -0.194, -0.174, -0.172, 0.04, 0.052, "glow", grain="x")
    return [q for q in out if q]


_KNIVES_190 = (  # (t on the bar, blade length, heel width, kind)
    (1.43, 0.200, 0.046, "chef"), (1.53, 0.150, 0.020, "boning"), (1.63, 0.165, 0.078, "cleaver"), (1.75, 0.215, 0.030, "slicer"), (1.85, 0.095, 0.020, "paring"))


def _knife_bar_190(s1):
    cbox, prism = V.cbox, V.prism
    out = []
    zbar = 1.56
    out += cbox(V.WORLD, s1 - 0.020, s1, 1.34, 1.94, zbar - 0.022, zbar + 0.022, C32_BOARD(), ch=0.004, grain="x")      # hardwood strip
    out += cbox(V.WORLD, s1 - 0.024, s1 - 0.020, 1.36, 1.92, zbar - 0.010, zbar + 0.010, "steel", grain="x")           # magnet rail
    for t, bl, w, kind in _KNIVES_190:
        kf = V.Frame((s1 - 0.0245, t, zbar - bl * 0.45), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))           # blade tip up, handle down
        h = w / 2
        if kind == "cleaver":
            prof = [(-h, 0.0), (h, 0.0), (h, bl), (-h + 0.012, bl), (-h, bl - 0.012)]
        elif kind == "slicer":
            prof = [(-h, 0.0), (h, 0.0), (h, bl - 0.03), (h - 0.008, bl - 0.008), (0.0, bl), (-h, bl - 0.004)]
        else:                                                                                                          # spine straight, belly curved to the tip
            prof = [(-h, 0.0), (h, 0.0), (h * 0.98, bl * 0.45), (h * 0.62, bl * 0.72), (h * 0.05, bl * 0.92), (-h, bl)]
        out += prism(kf, prof, 0.0, 0.0024, "steel", caps=(True, True))
        hw = 0.027 if kind in ("chef", "cleaver", "slicer") else 0.021
        out += cbox(kf, -0.004, 0.0064, -hw / 2 - 0.002, hw / 2 + 0.002, -0.014, 0.0, "steel", ch=0.002, grain="y")    # bolster
        hl = 0.118 if kind != "paring" else 0.095
        hp = V.round_rect(-hw / 2, hw / 2, -0.014 - hl, -0.014, 0.008, seg=3)
        out += prism(kf, hp, -0.0075, 0.0100, "rubber", smooth="all", caps=(True, True))                               # riveted handle scales
        for k in range(3):
            z = -0.014 - hl * (0.2 + 0.3 * k)
            out += cbox(kf, 0.0100, 0.0108, -0.003, 0.003, z - 0.003, z + 0.003, "steel")
    return [q for q in out if q]


def C32_BOARD():
    return "walnut"


def _ball(o, r, cell, n=6):
    f = V.Frame(o, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    return V.lathe(f, [(0.0, -r), (r * 0.72, -r * 0.70), (r, 0.0), (r * 0.72, r * 0.70), (0.0, r)], n, "food", cell=cell)


def _tray_food_190(fr, kind, x0, x1, y0, y1, z, rng):
    if kind in ("olives_green", "olives_black"):
        out = []
        r = 0.0105
        nx, ny = int((x1 - x0 - 0.02) / 0.024), int((y1 - y0 - 0.02) / 0.024)
        for lay, (zz, keep) in enumerate(((z + r * 0.7, 1.0), (z + r * 2.1, 0.45))):
            for i in range(nx):
                for j in range(ny):
                    if rng.random() > keep:
                        continue
                    x = x0 + 0.02 + (i + 0.5 * (j % 2) + rng.uniform(-0.2, 0.2)) * 0.024
                    y = y0 + 0.02 + (j + rng.uniform(-0.2, 0.2)) * 0.024
                    if x > x1 - 0.014 or y > y1 - 0.014:
                        continue
                    out += _ball(fr.p(x, y, zz + rng.uniform(-0.002, 0.002)), r * rng.uniform(0.88, 1.08), kind, n=5)
        return out
    if kind == "peppers":
        out = []
        n = max(6, int((x1 - x0) / 0.03))
        for k in range(n):
            x = x0 + 0.025 + (x1 - x0 - 0.05) * (k + rng.uniform(-0.3, 0.3)) / max(n - 1, 1)
            ya, yb = y0 + 0.02 + rng.uniform(0, 0.03), y1 - 0.02 - rng.uniform(0, 0.03)
            pts = []
            for q in range(6):
                u = q / 5.0
                pts.append(fr.p(x + 0.012 * math.sin(u * 5.0 + k), ya + (yb - ya) * u, z + 0.010 + 0.006 * (k % 3) + 0.006 * math.sin(u * 3.1 + k * 1.7)))
            out += V.tube(V.WORLD, pts, 0.0105, 5, "food", cell="peppers", caps=True)
        return out
    return V.tray_food(fr, kind, x0, x1, y0, y1, z, rng)


def _case_food_190(t0, t1, hero):
    out = []
    fr = V.front_frame(t0)
    L = t1 - t0
    e, deck = 0.035, 0.88
    out += V.cbox(fr, e, L - e, 0.44, 0.80, deck, deck + 0.05, "steel", grain="x", skip=("-z",))    # stainless riser
    rng = _rnd18.Random(18 if hero else 81)
    usable = L - 2 * e - 0.02
    front, back = _CASE18[bool(hero)]
    for items, (y0, y1), z in ((front, (0.10, 0.40), deck), (back, (0.47, 0.78), deck + 0.05)):
        tot = sum(w for _k, w in items)
        x = e + 0.01
        for kind, wt in items:
            w = usable * wt / tot
            x0, x1 = x + 0.008, x + w - 0.008
            x += w
            if kind is None:
                continue
            out += V.tray(fr, x0, x1, y0, y1, z)
            out += _tray_food_190(fr, kind, x0 + 0.012, x1 - 0.012, y0 + 0.012, y1 - 0.012, z + 0.006, rng)
            px = (x0 + x1) / 2 + rng.uniform(-0.02, 0.02)
            out += V.tube(fr, [(px, y0 + 0.01, z + 0.01), (px, y0 + 0.012, z + 0.07)], 0.0016, 4, "steel")
            a, b = fr.p(px + 0.046, y0 + 0.004, z + 0.058), fr.p(px - 0.046, y0 + 0.004, z + 0.058)      # +x is the customer's LEFT
            c, d = fr.p(px - 0.046, y0 + 0.016, z + 0.104), fr.p(px + 0.046, y0 + 0.016, z + 0.104)
            out += _card18(a, b, c, d, "tag_" + kind, fr.v(0, -1, 0.3))
    return [q for q in out if q]


def _counters_faces_190():
    C = _C32
    out = []
    for k, (t0, t1) in enumerate(V.CASES_T):
        out += V.deli_case(t0, t1, hero=(k == 0))
        out += _case_food_190(t0, t1, hero=(k == 0))
    fr = V.front_frame(V.CASES_T[0][0])
    out += V.cbox(fr, -0.027, 0.0, -0.004, 1.03, FLOOR_190, 0.90, "steel", ch=0.004, grain="z", skip=("-z",))     # south end panel of the line
    out += _service_counter_190()
    out += _saloon_190()
    out += V.back_counter()
    out += _slicer_190(V.BACK_S[0] + 0.33, 2.85)
    out += V.paper_roll(V.BACK_S[0] + 0.35, 3.45, math.radians(-90))
    out += V.prosciutto_stand(V.BACK_S[0] + 0.33, 4.05, math.radians(90))
    out += V.hanging_rail()
    return out


FLOOR_190 = _C32.FLOOR
V.counters_faces = _counters_faces_190


def _counter_collision_190():
    out = []
    for t0, t1 in V.CASES_T:
        out.append(((V.COUNTER_FRONT - 0.01, t0, _C32.FLOOR), (V.COUNTER_BACK + 0.02, t1, 1.34), "GLASS_SHOOT_THROUGH"))
    out.append(((V.COUNTER_FRONT - 0.05, SVC_T[0] - 0.01, _C32.FLOOR), (V.COUNTER_BACK + 0.01, SVC_T[1] + 0.01, 1.02), "WOOD_SOLID_MEDIUM"))
    out.append(((V.COUNTER_FRONT - 0.05, V.PG.YS, _C32.FLOOR), (V.COUNTER_FRONT + 0.05, -0.745, 1.02), "WOOD_SOLID_MEDIUM"))     # stub wall + post
    out.append(((V.BACK_S[0] - 0.03, V.BACK_T[0], _C32.FLOOR), (V.BACK_S[1], V.BACK_T[1], 0.92), "METAL_SOLID_MEDIUM"))
    return out


V.counter_collision_boxes = _counter_collision_190


def _shell_faces_190(*a, **k):
    out = []
    for f in _shell_182(*a, **k):
        if f["mat"] == _SM_LEAK and all(v[0] < -2.80 for v in f["v"]):
            continue                                                       # leak streak on the W wall (over the W2 blinds)
        out.append(f)
    return out


_PG.shell_faces = _shell_faces_190


def hall_faces():
    out = []
    s1 = V.P1_S[0] - 0.006
    T_, I_, R_, S_ = MAT["terrazzo"], MAT["iron"], MAT["rubber"], MAT["steel"]
    for f in _hf_182():
        vs = f["v"]; m = f["mat"]
        S = [v[0] for v in vs]; T = [v[1] for v in vs]; Z = [v[2] for v in vs]
        if m == MAT["frieze_txt"]:                                     # 1.9.1: both letterings (W wall, booth wall)
            continue                                                       # lettering over the W2 window
        if (m == MAT["wall5"] and max(S) < -2.80) or (m == I_ and max(S) < -2.86 and 2.6 < min(T) and max(T) < 3.35 and 1.4 < min(Z) and max(Z) < 2.0):
            continue                                                       # CAFFE ESPRESSO tin sign
        if m == MAT["wall6"] and min(T) > -1.24 and max(T) < -1.19 and min(Z) > 2.6 and max(Z) < 2.95:
            continue                                                       # LONG PIG DELI banner over the booths
        if m == MAT["signs18"] and max(S) < 6.97 and max(Z) < 0.9:
            continue                                                       # TAKE OUT / EMPLOYEES ONLY cards
        if m in (I_, R_, S_) and min(S) > 9.90 and 1.30 < min(T) and max(T) < 1.96 and 1.19 < min(Z) and max(Z) < 1.60:
            continue                                                       # 1.8.0 knife bar
        inside_gate = min(S) > _GATE_BOX[0] and max(S) < _GATE_BOX[1] and min(T) > _GATE_BOX[2] and max(T) < _GATE_BOX[3] and min(Z) > 0.95 and max(Z) < 1.7
        if inside_gate:
            if all(abs(v[0] - _BELL_OLD[0]) < 0.09 and abs(v[1] - _BELL_OLD[1]) < 0.09 for v in vs) and max(Z) < 1.16:
                f = dict(f, v=[(v[0] + _BELL_D[0], v[1] + _BELL_D[1], v[2]) for v in vs])                # service bell -> service counter
            else:
                continue                                                   # everything that stood on the gate counter
        elif min(S) > 6.9 and max(S) < 8.05 and min(T) > SVC_T[0] - 0.02 and max(T) < SVC_T[1] + 0.02 and min(Z) > 1.0:
            dz = -0.03 if min(T) > V.COFFEE_T[0] - 0.01 and m != MAT["signs18"] else 0.0                  # coffee top was 3 cm higher
            if m == T_:
                f = dict(f, mat=MAT["enamel"])                             # printer housing: plastic, not counter laminate
            if dz:
                f = dict(f, v=[(v[0], v[1], v[2] + dz) for v in f["v"]])
        out.append(f)
    out += _knife_bar_190(s1)
    return [f for f in out if f]


def vanilla_props():
    out = []
    for e in _vp_182():
        n, s, t, zb, yaw = e
        if n in ("prop_beer_neon_04", "prop_beer_neon_03"):
            continue
        if n in ("v_ret_gc_clock", "prop_fib_clipboard") and t < -1.0 and s > 13.5:
            continue                                                       # clock + clipboard in front of the back door (kitchen)
        if _GATE_BOX[0] < s < _GATE_BOX[1] and _GATE_BOX[2] < t < _GATE_BOX[3] and zb > 0.9:
            continue
        if 6.9 < s < 8.05 and V.COFFEE_T[0] - 0.01 < t < SVC_T[1] + 0.02 and 1.03 < zb < 1.12:
            e = (n, s, t, zb - 0.03, yaw)
        out.append(e)
    return out


# ================================================================== 1.9.1 (owner's 11 screenshots of 1.9.0, 2026-11-17 01:42)
# counter top / caps: oak (ambientCG Wood049) instead of marble; high shelves back; saloon leaves = animated props, stub wall
# shorter and clad on both sides; remaining frieze lettering + sign frame removed; steel door in the kitchen <-> storage opening;
# clock on the green panel replaced by an own BROKEN clock (crooked, cracked face, minute hand hanging).
_hf_190, _vp_190 = hall_faces, vanilla_props
SHADER_SPECS[MAT["stone19"]] = ("normal_spec.sps", {"DiffuseSampler": "lp19_wood", "BumpSampler": "lp19_wood_n", "SpecSampler": "lp19_wood_s"},
                                {"specularIntensityMult": 0.4, "specularFalloffMult": 32.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp19_wood")
for _i, _p in enumerate(B9.PARTS):
    if _p[0].startswith("P7"):
        _h = list(_p[5])
        _h[0] = B9.door_hole("roc", 10.35, "gs_boh_pass")
        B9.PARTS[_i] = tuple(_p[:5]) + (_h,) + tuple(_p[6:])
_CLOCK_190 = (4.62, 2.05, 0.165, math.radians(13.0))                      # t, z, face radius, tilt


def _broken_clock_190(s1):
    t, z, R, a = _CLOCK_190
    ca, sa = math.cos(a), math.sin(a)
    f = V.Frame((s1 - 0.004, t, z), (0.0, ca, sa), (0.0, -sa, ca), (-1.0, 0.0, 0.0))                   # z' = out of the wall
    out = []
    out += V.lathe(f, [(0.0, 0.0), (R + 0.004, 0.0), (R + 0.004, 0.012)], 24, "iron")
    out += V.lathe(f, [(R, 0.012), (R + 0.006, 0.0), (R + 0.026, 0.0), (R + 0.030, 0.022), (R + 0.014, 0.040), (R, 0.030)], 24, "iron")
    u0, vb, u1, vt = _s18("clock")
    n = 20
    pts = [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]
    V.emit(out, V.F([f.p(-R * x, R * y, 0.014) for x, y in pts], "signs18",
                    [((u0 + u1) / 2 + (u1 - u0) / 2 * x, (vb + vt) / 2 + (vt - vb) / 2 * y) for x, y in pts], hint=(-1.0, 0.0, 0.0)))
    out += V.lathe(f, [(0.0, 0.014), (0.012, 0.014), (0.010, 0.024), (0.0, 0.026)], 10, "iron")
    out += V.cbox(V.WORLD, s1 - 0.026, s1 - 0.022, t - 0.005, t + 0.005, z - R * 0.86, z + 0.012, "iron", grain="z")        # minute hand, hanging
    hx, hz = -R * 0.5 * math.cos(math.radians(40)), R * 0.5 * math.sin(math.radians(40))
    out += V.tube(V.WORLD, [(s1 - 0.022, t, z), (s1 - 0.022, t + hx, z + hz)], 0.005, 5, "iron", caps=True)                # hour hand
    return [q for q in out if q]


def hall_faces():
    out = list(_hf_190())
    out += _broken_clock_190(V.P1_S[0] - 0.006)
    return [f for f in out if f]


def vanilla_props():
    return [e for e in _vp_190() if not (e[0] == "v_ret_gc_clock" and 9.6 < e[1] < 9.97 and e[2] < 6.9)]


# ================================================================== 1.9.2 (owner's 11 screenshots of 1.9.1, 2026-11-17 02:04) - last fixes
# gaps: staff side of the cases (slot above the doors, joints case|case and case|service counter), missing / broken boards of the
# counter front, end of the storage partition P8 (open slot to the cooler), prep bench end by the kitchen door; LONG PIG DELI
# sign over the booths removed; light: entrance corner +8 %, case lights -15 %, soffit cans over the cases -12 %.
# Saloon leaves (gs_44 lp_saloon_leaf): level with the stub wall, dark board cladding like the counter front, stainless plates.
_hf_191, _boh_191, _ol_191, _cl_191 = hall_faces, boh_faces, open_lights, closed_lights
_C32.BOARD_MISSING, _C32.BOARD_LOW, _C32.BOARD_TOP, _C32.BOARD_SPRUNG = set(), set(), set(), set()
V.BACK_T = (0.145, V.BACK_T[1])                                           # bench end up to the kitchen door casing (t 0.125)
_cf_191 = V.counters_faces


def _case_gaps_192():
    C = _C32
    cbox = V.cbox
    out = []
    yr, ym, p, zg, zt = 0.84, 0.50, 0.032, 0.90, _CASE_Z0 + _CASE_R
    for t0, t1 in V.CASES_T:                                              # slot between the staff doors and the work ledge
        fr = V.front_frame(t0)
        out += cbox(fr, 0.0, t1 - t0, 0.872, 0.99, 0.855, 0.945, "steel", grain="x")
    side = [(0.045, zg), (yr, zg), (yr, zt)] + [q for q in reversed(_CASE_PROF[1:])]
    (a0, a1), (b0, b1) = V.CASES_T
    for ja, jb, between_cases in ((a1, b0, True), (b1, V.REGISTER_T[0], False)):
        fj = V.front_frame(ja)
        Lj = jb - ja
        out += cbox(fj, -0.002, Lj + 0.002, 0.036, 1.0, C.Z_KICK, 0.945 if between_cases else 0.982, "steel", grain="z", skip=("-y",))
        if between_cases:
            out += cbox(fj, -0.002, Lj + 0.002, 0.86, 1.03, 0.945, 0.97, "steel", ch=0.004, grain="x")               # work ledge
            out += V.prism(fj, side, -0.003, Lj + 0.003, "steel", caps=(True, True))                                # stainless mullion
            out += cbox(fj, -0.003, Lj + 0.003, yr, yr + p, 0.86, zt + 0.035, "steel", grain="z")
            out += cbox(fj, -0.003, Lj + 0.003, ym, yr + p + 0.03, zt + 0.005, zt + 0.035, "steel", grain="x")      # service shelf
            out += V.tube(fj, [(-0.003, ym, zt + 0.023), (Lj + 0.003, ym, zt + 0.023)], 0.013, 8, "steel")
    return [f for f in out if f]


V.counters_faces = lambda: _cf_191() + _case_gaps_192()


def hall_faces():
    out = []
    W6, RB = MAT["wall6"], MAT["rubber"]
    for f in _hf_191():
        vs = f["v"]
        S = [v[0] for v in vs]; T = [v[1] for v in vs]; Z = [v[2] for v in vs]
        if f["mat"] in (W6, RB) and min(T) > -1.235 and max(T) < -1.20 and min(Z) > 2.85 and max(Z) < 3.2 and min(S) > 1.5 and max(S) < 5.4:
            continue                                                       # LONG PIG DELI sign over the booths + its clips
        out.append(f)
    return out


def boh_faces():
    """Wrap the storage-side finish of P8 round its free end (t = 8.66): the end was open (slot into the cooler wall)."""
    out = list(_boh_191())
    caps = []
    for f in out:
        vs = f["v"]
        S = [v[0] for v in vs]; T = [v[1] for v in vs]; Z = [v[2] for v in vs]
        if max(S) - min(S) < 0.002 and abs(min(S) - 12.74) < 0.003 and abs(max(T) - 8.66) < 0.003 and min(T) < 8.0:
            pts = list(zip(vs, f["uv"]))
            (pa, ua), (pb, ub) = next((x, y) for x in pts for y in pts if abs(x[0][2] - y[0][2]) < 1e-6 and abs(x[0][1] - y[0][1]) > 0.5)
            ku = (ub[0] - ua[0]) / (pb[1] - pa[1]); bu = ua[0] - ku * pa[1]
            (pc, uc), (pd, ud) = next((x, y) for x in pts for y in pts if abs(x[0][1] - y[0][1]) < 1e-6 and abs(x[0][2] - y[0][2]) > 0.05)
            kv = (ud[1] - uc[1]) / (pd[2] - pc[2]); bv = uc[1] - kv * pc[2]
            z0, z1 = min(Z), max(Z)
            cv = [(12.74, 8.66, z1), (12.86, 8.66, z1), (12.86, 8.66, z0), (12.74, 8.66, z0)]
            cuv = [(ku * (8.66 + (q[0] - 12.74)) + bu, kv * q[2] + bv) for q in cv]
            caps.append(dict(f, v=cv, uv=cuv))
    return out + caps


def _lt192(l):
    k, p = l["kind"], l["pos"]
    f = 0.85 if k == "case" else 0.88 if k == "soffit_can" else 1.08 if (p[0] < 1.0 and k != "window_day_fill") else 1.0
    return dict(l, intensity=round(l["intensity"] * f, 3)) if f != 1.0 else l


def open_lights():
    return [_lt192(l) for l in _ol_191()]


def closed_lights():
    return [_lt192(l) for l in _cl_191()]


# ================================================================== 1.9.3 (owner 2026-11-17 02:32)
# back wall behind the counter looked spot-lit: the lights aimed at / next to it -30 %. Saloon leaves: lp12_board + case steel (gs_44).
# Dust motes in the hall: client/ambience.lua (ent_amb_dust_motes).
_ol_192, _cl_192 = open_lights, closed_lights
_BACK_LT = ("ah_service_back", "staff_fill", "troffer_lamp0", "troffer_lamp1", "troffer_lamp3")


def _lt193(l):
    return dict(l, intensity=round(l["intensity"] * 0.70, 3)) if (l["kind"] in _BACK_LT and l["pos"][0] > 8.5) else l


def open_lights():
    return [_lt193(l) for l in _ol_192()]


def closed_lights():
    return [_lt193(l) for l in _cl_192()]
