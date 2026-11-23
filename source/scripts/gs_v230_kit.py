# LONG PIG 2.3.0 - bodega rebuild, second pass (owner 2026-11-21: "render it yourself, look, carry on; everything must
# match the sign in colour"). On top of 2.2.0 (protected as before: ceiling, all lights, fans, overhead menu boards):
#   * palette of the shop's own sign / menu boards: brick-red dado and wall band with mustard pin lines, dirty cream
#     walls, mustard laminate, dark brown tops, cream enamel; the teal stripe (it crossed the windows) is gone;
#   * all finishes worn (source/textures/v230, gs_15aj_v230.py); sign atlas recoloured, second atlas for the kiosk;
#   * kiosk: fascia lettering, lottery ticket rack, notices, cigarette racks on the back wall, fan; stickers moved onto
#     the glass; the post that ran through the service opening is removed;
#   * fixes found in the check renders / audit: floating beer cases and fruit basket, stock on top of the gondolas.
import json, math
from pathlib import Path
import gs_v220_kit as K22
from gs_v220_kit import *                    # noqa: F401,F403

VERSION = "2.3.0"
K30, K21, V, B9, PG = K22.K30, K22.K21, K22.V, K22.B9, K22.PG
F0 = K22.F0
XW, YS, XE, YN = K22.XW, K22.YS, K22.XE, K22.YN
_quad, _bx, _sign = K22._quad, K22._bx, K22._sign
_hf22, _vp22, _cb22 = K22.hall_faces, K22.vanilla_props, K22.collision_boxes
REG2 = json.loads((Path(__file__).resolve().parents[1] / "textures" / "v230" / "lp23_signs2_regions.json").read_text())


def _ns(tex, inten, fall):
    return ("normal_spec.sps", {"DiffuseSampler": tex, "BumpSampler": tex + "_n", "SpecSampler": tex + "_s"},
            {"specularIntensityMult": inten, "specularFalloffMult": fall, "specularFresnel": 0.97, "bumpiness": 1.0}, tex)


for _k, _sp in (("teal20", _ns("lp23_band", 0.35, 18.0)), ("dark20", _ns("lp23_dark", 0.3, 14.0)), ("lam20", _ns("lp23_lam", 0.4, 30.0)),
                ("top20", _ns("lp23_top", 0.6, 50.0)), ("white20", _ns("lp23_white", 0.4, 30.0)), ("alu20", _ns("lp23_alu", 0.8, 70.0)),
                ("signs20", ("default.sps", {"DiffuseSampler": "lp23_signs"}, {}, "lp23_signs")),
                ("signs20e", ("emissive.sps", {"DiffuseSampler": "lp23_signs"}, {"emissiveMultiplier": 1.1}, "lp23_signs_e"))):
    SHADER_SPECS[MAT[_k]] = _sp
MAT["signs23b"] = len(SHADER_SPECS)
SHADER_SPECS.append(("default.sps", {"DiffuseSampler": "lp23_signs2"}, {}, "lp23_signs2"))
V.REP["signs23b"] = 1.0

SHELL_TEX = dict(K22.SHELL_TEX)
SHELL_TEX["floor"] = ("lp23_floor", "lp23_floor_n", "lp23_floor_s", 50.0, 0.45)
SHELL_TEX["wall"] = ("lp23_wall", "lp23_wall_n", "lp23_wall_s", 10.0, 0.2)
SHELL_TEX["tile"] = ("lp23_dado", "lp23_dado_n", "lp23_dado_s", 22.0, 0.35)
_WALLSPEC = _ns("lp23_wall", 0.2, 10.0)
SHELL_EXTRA_SPECS = list(K22.SHELL_EXTRA_SPECS)
SHELL_EXTRA_SPECS[0] = _WALLSPEC[:3] + ("lp23_wall_x",)
SHELL_EXTRA_SPECS[2] = _WALLSPEC[:3] + ("lp23_wall_y",)
SHELL_TEX_N = 11                             # floor, wall, dado, ceiling sets + 2; the two extra wall specs reuse lp23_wall
BAND_Z = (2.72, 2.90)                        # above every opening head (2.65)
CIG_S = (7.85, 9.10)


def _sign2(out, key, c, w, z0, z1, n, off=0.004):
    x0, y0, x1, y1 = REG2[key]
    _quad(out, c, w, z0, z1, n, "signs23b", (x0 / 1024.0, 1 - y1 / 1024.0, x1 / 1024.0, 1 - y0 / 1024.0), off)


def _drop(f):
    m = K22._INV.get(f["mat"]) if hasattr(K22, "_INV") else None
    m = m or {v: k for k, v in MAT.items()}.get(f["mat"])
    P = f["v"]; n = float(len(P))
    cs, ct, cz = sum(p[0] for p in P) / n, sum(p[1] for p in P) / n, sum(p[2] for p in P) / n
    if m == "teal20":
        return True                                                        # old stripe
    if m == "signs20" and ((cs < 6.985 and ct < 1.0 and cz > 1.2) or (abs(ct - 1.58) < 0.012 and cz > 1.2)):
        return True                                                        # stickers that floated in front of the frames
    if m == "white20" and cs > 7.2 and all(p[1] < YS + 0.215 for p in P) and all(1.37 < p[2] < 1.93 for p in P):
        return True                                                        # upper back shelves -> cigarette racks
    if m == "alu20" and all(6.94 < p[0] < 7.06 and -0.16 < p[1] < -0.07 and p[2] < 2.11 for p in P) and cz > 1.06:
        return True                                                        # post through the service opening
    return False


def hall_faces():
    out = [f for f in _hf22() if not _drop(f)]
    # wall band: south wall, entrance chamfer, west wall up to the cooler bulkhead
    for a, b, n in (((8.10, YS), (0.58, YS), (0.0, 1.0)), ((0.58, YS), (XW, 2.5), (0.731, 0.682)), ((XW, 2.5), (XW, K22.FRIDGE_FRONT), (1.0, 0.0))):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        _quad(out, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), L, BAND_Z[0], BAND_Z[1], n, "teal20", (0.0, 0.0, L / 0.9, 1.0), 0.006)
    # kiosk: fascia lettering on the roof edge, stickers on the glass, lottery rack, notices
    for t in (-0.67, 0.44):
        _sign2(out, "fascia", (6.97, t), 1.08, 2.158, 2.272, (-1.0, 0.0), 0.003)
    for s in (8.15, 9.34):
        _sign2(out, "fascia", (s, 1.58), 1.16, 2.158, 2.272, (0.0, 1.0), 0.003)
    G = 7.024
    _sign2(out, "lotto_rack", (G, -0.78), 0.50, 1.50, 2.00, (-1.0, 0.0), 0.0)
    _sign(out, "p_lotto", (G, -0.78), 0.26, 1.18, 1.44, (-1.0, 0.0), "signs20", 0.0)
    _sign(out, "p_noid", (G, 0.50), 0.26, 1.60, 1.86, (-1.0, 0.0), "signs20", 0.0)
    _sign2(out, "cashonly", (G, 0.80), 0.26, 1.22, 1.48, (-1.0, 0.0), 0.0)
    _sign(out, "p_smile", (8.90, 1.526), 0.30, 1.55, 1.85, (0.0, 1.0), "signs20", 0.0)
    _sign2(out, "open24", (8.20, 1.526), 0.56, 1.55, 1.83, (0.0, 1.0), 0.0)
    _sign2(out, "phone", (9.45, 1.526), 0.50, 1.20, 1.45, (0.0, 1.0), 0.0)
    _bx(out, 7.20, 9.74, YS + 0.004, YS + 0.018, 1.28, 1.94, "top20")                   # backing board of the cigarette racks
    # hall notices
    _sign2(out, "noloit", (6.38, YS), 0.30, 1.62, 1.92, (0.0, 1.0), 0.006)
    _sign2(out, "ice", (K22.FRIDGE_S[-1] + 0.82, 6.60), 0.50, 1.50, 1.75, (1.0, 0.0), 0.004)
    _sign2(out, "specials", (K22.SERVICE[0], 3.00), 1.92, 0.50, 0.80, (-1.0, 0.0), 0.005)
    _sign(out, "hot_food", (K22.SERVICE[0], 4.62), 0.84, 0.50, 0.78, (-1.0, 0.0), "signs20", 0.005)
    _sign(out, "p_2for1", (K22.COFFEE[0], 6.35), 0.30, 0.45, 0.75, (-1.0, 0.0), "signs20", 0.005)
    return [f for f in out if f]


def vanilla_props():
    out = []
    for e in _vp22():
        n, s, t, z, yaw = e
        if n == "prop_cs_beer_box":
            e = (n, s, t, z - 0.14, yaw)                                    # 2.2.0 gave the origin height, the tuple wants the bottom
        elif n == "prop_fruit_basket":
            e = (n, s, t, F0, yaw)
        elif s > 7.2 and t < YS + 0.2 and z > 1.39:
            continue                                                       # stock of the removed upper back shelves
        out.append(e)
    for s in CIG_S:
        e = B9._against("v_ret_247_cigs", (s, YS + 0.018), (0.0, 1.0))
        out.append((e[0], e[1], e[2], 1.30, e[4]))
    out += [("v_ret_gc_fan", 9.35, 0.62, F0, 200.0), ("v_serv_wetfloorsn", 5.95, 3.10, F0, 20.0), ("v_ret_gc_bin", 6.72, 5.60, F0, 0.0)]
    out += [("v_ind_cf_crate2", 6.68, 6.56, F0 + 0.40 * k, (4.0, -7.0, 3.0)[k]) for k in range(3)]
    for (g, cs) in (K22.ISLAND, K22.ROW2):                                 # overstock on top of the gondolas
        zt = F0 + 1.56
        out += [("v_ret_gc_box1", cs[0] - 0.55, g, zt, 8.0), ("v_ret_gc_box2", cs[0] - 0.10, g, zt, -12.0), ("prop_cs_beer_box", cs[0] + 0.45, g + 0.10, zt, 90.0),
                ("v_ret_gc_box1", cs[1] + 0.20, g, zt, 95.0), ("v_ret_gc_box2", cs[1] + 0.62, g, zt, 20.0), ("v_ret_gc_box2", cs[1] + 0.62, g, zt + 0.27, 5.0)]
    return out


def collision_boxes():
    out = list(_cb22())
    M = "WOOD_SOLID_MEDIUM"
    out += [((6.42, 6.94, 6.20, 6.92, F0, 1.20), M), ((9.05, 9.65, 0.35, 0.95, F0, 1.62), M)]
    return out


_used = {f["mat"] for f in hall_faces()}
for _i in range(len(SHADER_SPECS)):
    if _i not in _used and not SHADER_SPECS[_i][3].startswith("lp20_unused"):
        SHADER_SPECS[_i] = ("default.sps", {"DiffuseSampler": "lp20_panel_off"}, {}, "lp20_unused_%d" % _i)
for _n in ("hall_faces", "vanilla_props", "collision_boxes"):
    for _m in (K30, K21, K22):
        setattr(_m, _n, globals()[_n])
for _m in (K30, K21, K22):
    _m.SHELL_TEX, _m.SHELL_EXTRA_SPECS, _m.SHELL_TEX_N = SHELL_TEX, SHELL_EXTRA_SPECS, SHELL_TEX_N
