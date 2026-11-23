# LONG PIG 2.6.0 - 1.9.3 restaurant layout with the 2.5.0 finishes (owner 2026-11-21 17:54: "keep the walls as here, move
# them into 1.9.3, remove the Italian flag, more details, no brick walls; ceiling, walls, floor, shelves, coolers from 2.5 -
# keep the sofas, the display case etc."; answers: east side exactly as 1.9.3 (no glass kiosk), brick only in the hall).
#   KEPT FROM 1.9.3  booths, deli line with the glass cases + counter end + stools, back counter with its shelves / knives /
#                    clock / phone / rail, saloon doors (client), TV on its bracket, window ledge + stools, condiment stand,
#                    every ceiling fixture and light, menu boards, scripts (bell, print, order-up, sit, work).
#   FROM 2.5.0       walls (calm plaster lp24_wall at real scale, red dado lp24_dado, red band with mustard pins), floor
#                    lp23_floor, filled tile recesses, no leak stains; cooler run with lit headers (4 x v_ret_ml_fridge +
#                    2 black glass-door uprights), 24/7 gondolas, candy rack end cap, product cartons, local grime decals,
#                    uniform blinds (client data).
#   REMOVED          Italian tile flag + its black frame (wall becomes plaster), Tiles136B "brick" wall finish in the hall,
#                    walnut beam under the ceiling, green water stains near the ceiling, static stacked blind slats, the old
#                    1.9.3 fridges / gondolas / ATM corner, archive boxes (-> product cartons).
#   MEMORY           the new 2.5 pieces live in an own drawable gs_v26_market (own material list) so the 1.9.3 hall drawable
#                    keeps its budget; see EXTRA_HALL_DRAWABLES (hook in gs_20_build_prototype.py, 2.6.0).
import json, math
from pathlib import Path
import gs_v030_kit as K30
# ---- 1.9.3 state, captured BEFORE the 2.x chain is imported (the chain re-assigns these on K30)
_hf193, _vp193, _cb193 = K30.hall_faces, K30.vanilla_props, K30.collision_boxes
_shell193 = K30._PG.shell_faces
_part193 = K30._SG.partition_faces
_SPECS193 = list(K30.SHADER_SPECS)
_REP193 = dict(K30.V.REP)
_SHELL_TEX193 = dict(K30.SHELL_TEX)
import gs_v250_kit as K25
from gs_v250_kit import *                    # noqa: F401,F403  (MAT, SHADER_SPECS, VB, V, B9, PG ... shared objects)

VERSION = "2.6.0"
K24, K23, K22, K21 = K25.K24, K25.K23, K25.K22, K25.K21
V, B9, PG = K25.V, K25.B9, K25.PG
F0 = PG.FLOOR
XW, YS, XE, YN = K25.XW, K25.YS, K25.XE, K25.YN
_quad, _bx, _sign, _sign2 = K22._quad, K22._bx, K22._sign, K23._sign2
_INV = {v: k for k, v in MAT.items()}
_SPECS25 = list(SHADER_SPECS)                 # 2.5.0 materials (band, white, alu, top, signs, grime ...)
_REP25 = dict(V.REP)
FF = K22.FRIDGE_FRONT
PANEL = "default.sps", {"DiffuseSampler": "lp20_panel_off"}, {}

# ---------------------------------------------------------------------------------------------------- layout numbers
FRIDGES = (-2.10, -0.57, 0.96, 2.49)          # 4 x v_ret_ml_fridge (1.52 m) as in 2.2-2.5
BLACK = (("prop_bar_beerfridge_01", 3.69), ("prop_bar_fridge_01", 4.53))     # 2 black uprights (0.84 m), front flush
COOL_END = 4.95                               # end of the cooler run (end panel 4.95 .. 4.98)
HEAD = ("ice_cold", "cold_beer", "drinks", "water", "deals_cold")
ATM_S = 5.35                                  # free-standing ATM between the cooler run and the 1.9.3 extinguisher
ISLAND, ROW2 = K22.ISLAND, K22.ROW2          # (t, (s, s)) 24/7 gondola rows of 2.2-2.5
_CELL = K25._CELL


def _cen(P):
    n = float(len(P))
    return (sum(p[0] for p in P) / n, sum(p[1] for p in P) / n, sum(p[2] for p in P) / n)


def _span(P, i):
    return max(p[i] for p in P) - min(p[i] for p in P)


def _flush(P, d=0.06):
    return (min(p[0] for p in P) > XE - d or max(p[0] for p in P) < XW + d or min(p[1] for p in P) > YN - d or max(p[1] for p in P) < YS + d)


# ---------------------------------------------------------------------------------------------------- shell
SHELL_TEX = dict(K25.SHELL_TEX)               # floor lp23_floor, wall lp24_wall, tile (dado) lp24_dado, ceiling 1.9.3
_W24 = K24.SHELL_EXTRA_SPECS[0]
SHELL_EXTRA_SPECS = list(K25.SHELL_EXTRA_SPECS)            # 0 wall_x (old flag red / substrate), 1 board, 2 wall_y (flag green), 3 leaks
_b = _SHELL_TEX193["wall"]
SHELL_EXTRA_SPECS.append(("normal_spec.sps", {"DiffuseSampler": _b[0], "BumpSampler": _b[1], "SpecSampler": _b[2]},
                          {"specularIntensityMult": _b[4], "specularFalloffMult": _b[3], "specularFresnel": 0.97, "bumpiness": 1.0}, "lp14_wall_boh"))   # 10
_b = _SHELL_TEX193["tile"]
SHELL_EXTRA_SPECS.append(("normal_spec.sps", {"DiffuseSampler": _b[0], "BumpSampler": _b[1], "SpecSampler": _b[2]},
                          {"specularIntensityMult": _b[4], "specularFalloffMult": _b[3], "specularFresnel": 0.97, "bumpiness": 1.0}, "lp4_tile_boh"))    # 11
SM_BOH_WALL, SM_BOH_TILE = 6 + 4, 6 + 5
SHELL_TEX_N = 11


def _shell_260(*a, **k):
    out, st = [], {"holes": 0, "sides": 0, "leaks": 0, "flag": 0}
    for f in K30._uvmul(_shell193(*a, **k), 0, 0.5, 0.5):              # lp23_floor scale as in 2.x
        if not isinstance(f, dict):
            out.append(f); continue
        m = f["mat"]
        if m == 9 and min(p[2] for p in f["v"]) > 0.2 and max(p[0] for p in f["v"]) < XE + 0.05 and max(p[1] for p in f["v"]) < YN + 0.05:
            st["leaks"] += 1; continue                                   # leak decals on the hall walls
        if m in (1, 6):
            r = K24._recess(f)
            if r == "side":
                st["sides"] += 1; continue
            if r:
                st["holes"] += 1; f = r; m = 1
        if m in (6, 8) and min(p[0] for p in f["v"]) > XE - 0.02:
            st["flag"] += 1                                              # flag tiles -> plain wall (specs 6 / 8 = lp24_wall)
        if m in (1, 6, 8):
            f = dict(f, uv=K24._wall_uv(f))
        elif m == 2:
            f = dict(f, uv=K24._dado_uv(f))
        out.append(f)
    _shell_260.stats = st
    return out


def _hall_side(f):
    P = f["v"]; c = _cen(P); n = K24._newell(P)
    q = (c[0] + 0.08 * n[0], c[1] + 0.08 * n[1])
    return XW < q[0] < XE and YS < q[1] < YN


def _part_260(mats, *a, **k):
    out = []
    for f in _part193(mats, *a, **k):
        if f["mat"] == mats.get("wall", 1):
            f = dict(f, uv=K24._wall_uv(f)) if _hall_side(f) else dict(f, mat=SM_BOH_WALL)
        elif f["mat"] == mats.get("wood", 2):
            f = dict(f, uv=K24._dado_uv(f)) if _hall_side(f) else dict(f, mat=SM_BOH_TILE)
        out.append(f)
    return out


PG.shell_faces = _shell_260
K30._SG.partition_faces = _part_260


# ---------------------------------------------------------------------------------------------------- hall drawable (1.9.3)
def _drop193(f):
    P = f["v"]; m = _INV.get(f["mat"]); c = _cen(P)
    zmin, zmax = min(p[2] for p in P), max(p[2] for p in P)
    if m == "blind":
        return "blind"                                                   # static stacked slats (bay 3 is animated now)
    if min(p[0] for p in P) > XW - 0.06 and max(p[0] for p in P) < COOL_END + 0.05 and min(p[1] for p in P) > FF - 0.03 and zmax < 2.93:
        return "cooler"                                                  # behind / inside the cooler run and its bulkhead
    if 4.98 < c[0] < 5.85 and c[1] > 6.55 and 1.40 < c[2] < 1.95:
        return "atm_shelf"                                               # little wall shelf where the ATM stands now
    if m == "iron" and min(p[0] for p in P) > XE - 0.09 and 0.1 < c[1] < 6.6 and 0.85 < c[2] < 2.5 and (_span(P, 1) > 0.8 or _span(P, 2) > 0.8):
        return "flag_frame"
    if m == "walnut" and zmin > 2.6:
        return "beam"                                                    # walnut beams under the ceiling / soffit + old high shelf
    if m == "steel" and min(p[0] for p in P) > 5.28 and max(p[0] for p in P) < 5.32 and c[1] > 6.6 and 2.6 < c[2] < 2.8:
        return "beam"                                                    # end bracket of that shelf
    if m == "decal5" and _flush(P, 0.03) and (zmin > 2.8 or _span(P, 2) > 0.6):
        return "stain"                                                   # water stains / runs on the walls
    return None


_DROP_STATS = {}


def _faces193():
    cur = dict(V.REP); V.REP.clear(); V.REP.update(_REP193)              # 1.9.3 faces with their own UV repeats
    try:
        fs = [f for f in _hf193() if f]
    finally:
        V.REP.clear(); V.REP.update(cur)
    return fs


LEDGE_END = 6.20


def _trim_ledge(f):
    """1.9.3 window ledge (terrazzo top + its steel) ran to t 6.33; the cooler run now starts at the west wall."""
    P = f["v"]
    if not (max(p[0] for p in P) < XW + 0.55 and min(p[1] for p in P) > 3.4 and max(p[1] for p in P) < 6.45 and 0.15 < min(p[2] for p in P) and max(p[2] for p in P) < 1.2):
        return f
    if max(p[1] for p in P) <= LEDGE_END + 1e-6:
        return f
    if min(p[1] for p in P) >= 6.30:                                     # end faces of the ledge -> new end
        return dict(f, v=[(p[0], LEDGE_END, p[2]) for p in P])
    vs, uvs = [], []                                                     # clip to t <= LEDGE_END, UVs interpolated
    Q = list(zip(P, f["uv"]))
    for i in range(len(Q)):
        (a, ua), (b, ub) = Q[i], Q[(i + 1) % len(Q)]
        ina, inb = a[1] <= LEDGE_END + 1e-9, b[1] <= LEDGE_END + 1e-9
        if ina:
            vs.append(tuple(a)); uvs.append(tuple(ua))
        if ina != inb and abs(b[1] - a[1]) > 1e-9:
            k = (LEDGE_END - a[1]) / (b[1] - a[1])
            vs.append(tuple(a[j] + (b[j] - a[j]) * k for j in range(3))); uvs.append(tuple(ua[j] + (ub[j] - ua[j]) * k for j in range(2)))
    return dict(f, v=vs, uv=uvs) if len(vs) >= 3 else None


def hall_faces():
    out = []
    st = {}
    tile = MAT["tile"]
    for f in _faces193():
        why = _drop193(f)
        if why:
            st[why] = st.get(why, 0) + 1; continue
        if f["mat"] == tile:
            f = dict(f, uv=K24._dado_uv(f))                              # 1.9.3 tile caps / pieces on the walls -> red dado paint
        f = _trim_ledge(f)
        if f:
            out.append(f)
    _DROP_STATS.clear(); _DROP_STATS.update(st)
    return out


# ---------------------------------------------------------------------------------------------------- market drawable (2.5 pieces)
def market_faces():
    out = []
    b0, b1 = XW, COOL_END
    _bx(out, b0, b1 + 0.03, FF + 0.02, YN, 2.285, 2.92, "white20")      # bulkhead over the coolers
    _bx(out, b0, b1 + 0.03, FF, YN, 2.265, 2.285, "alu20")
    for s, key in zip(FRIDGES, HEAD[:4]):
        _sign(out, key, (s, FF + 0.02), 1.50, 2.33, 2.83, (0.0, -1.0))
    _sign(out, HEAD[4], ((BLACK[0][1] + BLACK[1][1]) / 2, FF + 0.02), 1.50, 2.33, 2.83, (0.0, -1.0))
    _bx(out, 3.26, b1, FF + 0.03, YN, 2.165, 2.265, "top20")             # filler over the black uprights (2.17 m)
    _bx(out, b1, b1 + 0.03, FF, YN, F0, 2.285, "white20")                # end panel
    _sign2(out, "ice", (b1 + 0.03, 6.62), 0.50, 1.50, 1.75, (1.0, 0.0), 0.004)
    # red band with mustard pins all round the hall (above every opening; gaps at the two back doors)
    segs = (((XE, YS), (0.58, YS), (0.0, 1.0)), ((0.58, YS), (XW, 2.5), (0.731, 0.682)), ((XW, 2.5), (XW, FF), (1.0, 0.0)),
            ((b1 + 0.03, YN), (8.28, YN), (0.0, -1.0)), ((9.49, YN), (XE, YN), (0.0, -1.0)),
            ((XE, YN), (XE, 0.07), (-1.0, 0.0)), ((XE, -1.15), (XE, YS), (-1.0, 0.0)))
    for a, b, n in segs:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        _quad(out, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), L, K23.BAND_Z[0], K23.BAND_Z[1], n, "teal20", (0.0, 0.0, L / 0.9, 1.0), 0.006)
    # signs + local grime
    _sign(out, "atm", (ATM_S, YN), 0.75, 1.98, 2.23, (0.0, -1.0))
    _sign2(out, "noloit", (6.50, YS), 0.30, 1.40, 1.70, (0.0, 1.0), 0.006)
    for cell, c, w, z0, z1, n in (("smudge", (b1 + 0.03, 6.62), 0.55, 0.92, 1.42, (1.0, 0.0)),     # hands on the cooler end
                                  ("smudge", (XW, 2.96), 0.62, 1.20, 1.78, (1.0, 0.0)),           # above the condiment stand
                                  ("dust", (5.95, YN), 0.40, 0.95, 1.55, (0.0, -1.0))):            # corner by the extinguisher
        _quad(out, c, w, z0, z1, n, "decal6", _CELL[cell], 0.004)
    return [f for f in out if f]


def _market_specs():
    used = {f["mat"] for f in market_faces()}
    return [(_SPECS25[i][0], _SPECS25[i][1], _SPECS25[i][2], _SPECS25[i][3] + "_mk") if i in used else PANEL + ("lp20_unused_mk_%d" % i,)
            for i in range(len(_SPECS25))]


EXTRA_HALL_DRAWABLES = (("gs_v26_market", market_faces, _market_specs),)


# ---------------------------------------------------------------------------------------------------- props + collision
_KEEP_MKT = {"lr_prop_clubstool_01", "prop_bar_stool_01", "prop_bar_napkindisp", "prop_food_ketchup", "prop_food_mustard", "prop_cs_paper_cup",
             "v_res_mp_ashtraya", "prop_fire_exting_1a", "prop_game_clock_01", "v_res_fa_smokealarm", "v_ilev_fib_sprklr", "v_res_tre_plugsocket",
             "prop_tv_01", "prop_food_tray_01", "prop_food_tray_03", "prop_gumball_02", "v_serv_switch_2"}
CART = ("v_ret_ml_beerbla2", "v_ret_ml_beerpat2", "v_ret_ml_beerjak2", "v_ret_ml_beerben2", "v_ret_ml_beerpis1", "v_ret_ml_beerbla1", "v_ret_ml_beerjak1", "v_ret_ml_beerpat1")


def _zone(s, t):
    if not (s < XE - 0.02 and t < YN - 0.02):
        return "out"
    if s > 6.85:
        return "serv"
    if 0.4 < s < 6.4 and t < 0.05:
        return "booth"
    return "mkt"


def vanilla_props():
    out, k_c = [], 0
    for e in _vp193():
        n, s, t, z, yaw = e
        zn = _zone(s, t)
        if zn == "mkt" and n not in _KEEP_MKT:
            continue                                                     # 1.9.3 fridges, gondolas, ATM, jars on the old wall shelves
        if n.startswith("v_ret_gc_box") and zn != "out":
            if any(o[0] in CART and abs(o[1] - s) < 0.1 and abs(o[3] - z) < 0.05 and abs(o[2] - t) < 0.47 for o in out):
                continue                                                 # cartons are wider than the archive boxes
            if s > 9.3 and t > 5.9:
                continue                                                 # box in the swing of the staff door: not replaced
            e = (CART[k_c % len(CART)], s - 0.02 if s > 9.7 else s, t, z, 0.0 if 9.3 < s < 9.7 else 90.0); k_c += 1     # archive boxes -> cartons
        if n == "prop_bar_stool_01" and s < -2.0:
            e = (n, s, {3.95: 3.95, 4.95: 4.80, 5.95: 5.65}.get(round(t, 2), t), z, yaw)   # last stool clear of the first cooler door
        out.append(e)
    N = (0.0, -1.0)
    out += [B9._against("v_ret_ml_fridge", (s, YN), N) for s in FRIDGES]
    for nm, s in BLACK:
        out.append(B9._against(nm, (s, YN - 0.08), N, 0.0))
    for (g, cs), flip in ((ISLAND, 0), (ROW2, 1)):                       # 24/7 gondolas exactly as 2.2-2.5
        for i, s in enumerate(cs):
            if (i + flip) % 2 == 0:
                out += [("v_ret_247shelves02" if i else "v_ret_247shelves01", s, g + 0.01, F0, -90.0), ("v_ret_247shelves03", s, g - 0.182, F0, 0.0)]
            else:
                out += [("v_ret_247shelves01", s, g - 0.01, F0, 90.0), ("v_ret_247shelves05", s, g + 0.18, F0, 90.0)]
        zt = F0 + 1.56                                                   # cartons on top of the gondolas
        for j, (ds, dt, yw) in enumerate(((-0.55, 0.0, 92.0), (0.45, 0.06, 88.0), (cs[1] - cs[0] + 0.25, -0.03, 90.0))):
            out.append((CART[(j + 3 * flip) % len(CART)], cs[0] + ds, g + dt, zt, yw))
    out.append(B9._against("v_ret_gassweets", (ISLAND[1][-1] + 1.05, ISLAND[0] + 0.025), (1.0, 0.0)))   # candy rack end cap
    for j, (dt, h) in enumerate(((-0.17, 0), (0.17, 0), (-0.17, 1), (0.17, 1))):                         # carton stack at the row-2 end
        out.append((CART[(j + 5) % len(CART)], ROW2[1][-1] + 1.04 + 0.26, ROW2[0] + dt, F0 + 0.326 * h, (0.0, 3.0, -3.0, 0.0)[j]))
    out.append(B9._against("prop_atm_01", (ATM_S, YN), N))
    return out


def collision_boxes():
    M = "WOOD_SOLID_MEDIUM"
    out = [((b[0][0], b[0][1], b[0][2], LEDGE_END, b[0][4], b[0][5]), b[1]) if abs(b[0][3] - 6.33) < 0.01 and b[0][0] < -2.8 else b for b in _cb193()]
    out.append(((XW, COOL_END + 0.03, FF, YN, F0, 2.92), M))
    for g, cs in (ISLAND, ROW2):
        out.append(((cs[0] - 1.05, cs[-1] + 1.05, g - 0.37, g + 0.42, F0, 1.60), M))
    out += [((ISLAND[1][-1] + 1.05, ISLAND[1][-1] + 1.36, 3.38, 4.97, F0, 1.05), M),
            ((ROW2[1][-1] + 1.05, ROW2[1][-1] + 1.56, ROW2[0] - 0.42, ROW2[0] + 0.42, F0, 0.66), M),
            ((ATM_S - 0.28, ATM_S + 0.28, YN - 0.60, YN, F0, 1.65), M)]
    return out


# ---------------------------------------------------------------------------------------------------- hall material list
SHADER_SPECS[:] = _SPECS193 + [PANEL + ("lp20_unused_%d" % i,) for i in range(len(_SPECS193), len(_SPECS25))]
SHADER_SPECS[MAT["tile"]] = ("normal_spec.sps", {"DiffuseSampler": "lp24_dado", "BumpSampler": "lp24_dado_n", "SpecSampler": "lp24_dado_s"},
                             {"specularIntensityMult": 0.35, "specularFalloffMult": 24.0, "specularFresnel": 0.97, "bumpiness": 0.6}, "lp24_dado_hall")
_used = {f["mat"] for f in hall_faces()}
for _i in range(len(SHADER_SPECS)):
    if _i not in _used and not SHADER_SPECS[_i][3].startswith("lp20_unused"):
        SHADER_SPECS[_i] = PANEL + ("lp20_unused_%d" % _i,)
HALL_MIN_TRIS = 20000
for _n in ("hall_faces", "vanilla_props", "collision_boxes"):
    for _m in (K30, K21, K22, K23, K24, K25):
        setattr(_m, _n, globals()[_n])
for _m in (K30, K21, K22, K23, K24, K25):
    _m.SHELL_TEX, _m.SHELL_EXTRA_SPECS, _m.SHELL_TEX_N = SHELL_TEX, SHELL_EXTRA_SPECS, SHELL_TEX_N
