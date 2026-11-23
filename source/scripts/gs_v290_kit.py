# LONG PIG 2.9.0 - on top of 2.8.0 (owner 2026-11-21 21:02):
#   * tobacco unit: one category per section - snacks / lottery / cigarettes / candy / mixed - each with its own shelf spacing
#   * every small poster / notice removed (2.x: ATM, NO LOITERING, ICE, OPEN 24, 2 FOR 1, SMILE, PHONE CARDS, CASH ONLY, NO I.D.,
#     COFFEE, LOTTO; 1.9.3: wall notices). The lit cooler headers stay.
#   * the solid collision box of the tobacco unit is gone (the racks sat inside it); a thin slab at the back instead
#   * roller blinds: client / server scripts + own prop lp_roller (gs_44); nothing of them is in this kit
import json, math
from pathlib import Path
import gs_v280_kit as K28
from gs_v280_kit import *                    # noqa: F401,F403

VERSION = "2.9.0"
K27, K26, K25, K24, K23, K22, K21, K30 = K28.K27, K28.K26, K28.K25, K28.K24, K28.K23, K28.K22, K28.K21, K28.K30
V, B9, PG = K28.V, K28.B9, K28.PG
F0 = PG.FLOOR
XW, YS, XE, YN = K28.XW, K28.YS, K28.XE, K28.YN
_quad, _bx = K22._quad, K22._bx
_INV = {v: k for k, v in MAT.items()}
_hf28, _vp28, _cb28, _mk28 = K28.hall_faces, K28.vanilla_props, K28.collision_boxes, K28.market_faces
_foot = K28._foot
HREG = K28.HREG
UT0, UT1, BAYS, DIV, BAYW = K28.UT0, K28.UT1, K28.BAYS, K28.DIV, K28.BAYW
ZB, Z0, ZTOP, ZH1, DEP = K28.ZB, K28.ZS3, K28.ZTOP, K28.ZH1, K28.DEP
DEPL = 0.205                                  # depth of a shelf that carries a lottery display (0.17 m deep)
_fy = K28._fy
_bay = K28._bay
# section k runs along the wall from the kitchen door (k = 0) to the staff door (k = 4); a customer reads them 4 -> 0
#            category     header        shelf rows: (clear height, depth)
SECTIONS = (("mixed",     "redwood",    ((0.48, DEPL), (0.64, DEP), (0.31, DEP))),
            ("candy",     "longpig",    ((0.278,  DEP),) * 5),
            ("cigs",      "cardiaque",  ((0.725, DEP), (0.725, DEP))),
            ("lottery",   "lotto",      ((0.4767, DEPL),) * 3),
            ("snacks",    "debonaire",  ((0.3525, DEP),) * 4))


def _rows(k):
    """[(shelf top z, clear height, depth)] for section k; shelves are 20 mm thick."""
    out, z = [], Z0
    for h, dep in SECTIONS[k][2]:
        out.append((z + 0.020, h, dep)); z += h + 0.020
    return out


def _unit(out):
    S = XE - 0.004
    _bx(out, S - 0.010, S, UT0, UT1, ZB, ZH1, "white20")                               # carcass back
    for k in range(BAYS + 1):                                                           # side panels
        t = UT0 + k * (BAYW + DIV)
        _bx(out, S - DEPL, S - 0.010, t, t + DIV, ZB, Z0 + 0.52, "white20", 0.003)
        _bx(out, S - DEP, S - 0.010, t, t + DIV, Z0 + 0.52, ZH1, "white20", 0.003)
    _bx(out, S - DEPL - 0.006, S - 0.010, UT0, UT1, ZB, Z0, "top20")                    # plinth on the back counter
    for k in range(BAYS):
        t0, t1 = _bay(k)
        _quad(out, (S - 0.010, (t0 + t1) / 2), t1 - t0, Z0, ZTOP, (-1.0, 0.0), "mat", (0.0, 0.0, (t1 - t0) / 0.2, (ZTOP - Z0) / 0.2), 0.0015)   # pegboard
        for (zt, _h, dep) in _rows(k):                                                  # shelf, lip, price strip
            z = zt - 0.020
            _bx(out, S - dep, S - 0.010, t0, t1, z, zt, "white20")
            _bx(out, S - dep - 0.004, S - dep, t0, t1, z - 0.010, zt + 0.012, "alu20")
            _quad(out, (S - dep - 0.004, (t0 + t1) / 2), t1 - t0 - 0.01, z - 0.007, zt + 0.009, (-1.0, 0.0), "teal20", (0.0, 0.42, 3.0, 0.52), 0.001)
        _bx(out, S - DEP, S - 0.010, t0, t1, ZTOP, ZTOP + 0.018, "white20")              # top panel under the light box
        _bx(out, S - DEP - 0.012, S - DEP, t0 - 0.004, t1 + 0.004, ZTOP + 0.018, ZTOP + 0.036, "alu20")
        _bx(out, S - DEP - 0.012, S - DEP, t0 - 0.004, t1 + 0.004, ZH1 - 0.018, ZH1, "alu20")
        for t in (t0 - 0.004, t1 - 0.010):
            _bx(out, S - DEP - 0.012, S - DEP, t, t + 0.014, ZTOP + 0.036, ZH1 - 0.018, "alu20")
        _bx(out, S - DEP, S - 0.010, t0, t1, ZTOP + 0.018, ZH1, "top20")
        x0, y0, x1, y1 = HREG[SECTIONS[k][1]]
        _quad(out, (S - DEP, (t0 + t1) / 2), t1 - t0 - 0.02, ZTOP + 0.036, ZH1 - 0.018, (-1.0, 0.0), "menu",
              (x0 / 1024.0, 1 - y1 / 512.0, x1 / 1024.0, 1 - y0 / 512.0), 0.004)
    _bx(out, S - DEP - 0.02, S, UT0 - 0.006, UT1 + 0.006, ZH1, ZH1 + 0.02, "white20", 0.004)   # cap


CHIPS = ("v_ret_ml_chips1", "v_ret_ml_chips2", "v_ret_ml_chips3", "v_ret_ml_chips4")
SW_T = ("v_ret_ml_sweet5", "v_ret_ml_sweet6", "v_ret_ml_sweet7", "v_ret_ml_sweet4")                     # tall boxes, 0.14-0.16 m wide
SW_L = ("v_ret_ml_sweet1", "v_ret_ml_sweet9", "v_ret_ml_sweetego", "v_ret_ml_sweet8", "v_ret_ml_sweet2")  # low boxes, 0.26 m wide


def _unit_props():
    out = []
    S = XE - 0.016

    def at(name, t, z):
        e = B9._against(name, (S, t), (-1.0, 0.0), 0.0)
        f = _foot(name, e[1], e[2], e[4])
        return (e[0], e[1], e[2] + (t - (f[2] + f[3]) / 2), z, e[4])                     # centred on t whatever the model's origin

    def row(names, k, z, pitch, n):
        t0, t1 = _bay(k); a = (t0 + t1) / 2 - pitch * (n - 1) / 2
        return [at(names[(j + int(z * 7)) % len(names)], a + pitch * j, z) for j in range(n)]
    for k in range(BAYS):
        t0, t1 = _bay(k); tc = (t0 + t1) / 2
        cat, R = SECTIONS[k][0], _rows(k)
        if cat == "snacks":
            for (z, _h, _d) in R:
                out += row(CHIPS, k, z, 0.240, 5)
        elif cat == "lottery":
            for (z, _h, _d) in R:
                out.append(at("v_ret_247_lottery", tc, z))
        elif cat == "cigs":
            for (z, _h, _d) in R:
                out.append(at("v_ret_247_cigs", tc, z))
        elif cat == "candy":
            for i, (z, _h, _d) in enumerate(R):
                out += row(SW_L, k, z, 0.290, 4) if i % 2 == 0 else row(SW_T, k, z, 0.170, 7)
        else:                                                                            # mixed: LOTTO sign + candy / cigarettes / candy
            out.append(at("v_ret_247_lotterysign", tc, R[0][0]))
            for j, dt in enumerate((-0.47, -0.31, 0.31, 0.47)):
                out.append(at(SW_T[j], tc + dt, R[0][0]))
            out.append(at("v_ret_247_cigs", tc, R[1][0]))
            out += row(SW_L, k, R[2][0], 0.290, 4)
    return out


def _is28_unit(f):
    P = f["v"]
    return min(p[0] for p in P) > XE - 0.24 and UT0 - 0.02 < min(p[1] for p in P) and max(p[1] for p in P) < UT1 + 0.02 and min(p[2] for p in P) > 0.90


_POSTER_MATS = (MAT["signs20"], MAT["signs23b"])


def market_faces():
    out = []
    for f in _mk28():
        if _is28_unit(f) or f["mat"] in _POSTER_MATS:
            continue                                                     # 2.8.0 unit (rebuilt below); small posters / notices
        if f["mat"] == MAT["signs20e"] and min(p[0] for p in f["v"]) > K26.COOL_END + 0.05:
            continue                                                     # lit ATM sign (the cooler headers stay)
        out.append(f)
    _unit(out)
    return [f for f in out if f]


_market_specs28 = K28._market_specs


def _market_specs():
    sp = list(K26._SPECS25)
    sp[MAT["teal20"]] = K28._ns("lp27_band", 0.25, 16.0)
    sp[MAT["decal6"]] = ("decal.sps", {"DiffuseSampler": "lp27_grime"}, {}, "lp27_grime")
    sp[MAT["menu"]] = ("emissive.sps", {"DiffuseSampler": "lp28_heads"}, {"emissiveMultiplier": 2.2}, "lp28_heads_e")
    sp[MAT["mat"]] = K28._ns("lp28_peg", 0.2, 20.0, 1.0)
    used = {f["mat"] for f in market_faces()}
    return [(sp[i][0], sp[i][1], sp[i][2], sp[i][3] + "_mk") if i in used else K26.PANEL + ("lp20_unused_mk_%d" % i,) for i in range(len(sp))]


EXTRA_HALL_DRAWABLES = (("gs_v26_market", market_faces, _market_specs),)
_NOTICE_MATS = tuple(MAT[m] for m in ("notice", "lp8") if m in MAT)
_HSTAT = {}


def hall_faces():
    out, n = [], 0
    for f in _hf28():
        if f["mat"] in _NOTICE_MATS and K26._flush(f["v"], 0.06):
            n += 1; continue                                             # 1.9.3 notices / small signs on the hall walls
        out.append(f)
    _HSTAT.clear(); _HSTAT["notices"] = n
    return out


_UNIT28 = {e[0] for e in K28._unit_props()}


def vanilla_props():
    out = [e for e in _vp28() if not (e[0] in _UNIT28 and e[1] > XE - 0.25 and e[3] > 0.95)]     # props of the 2.8.0 unit
    return out + _unit_props()


def collision_boxes():
    M = "WOOD_SOLID_MEDIUM"
    out = [b for b in _cb28() if not (abs(b[0][0] - (XE - 0.21)) < 1e-6 and abs(b[0][5] - ZH1) < 1e-6)]
    out.append(((XE - 0.03, XE, UT0, UT1, 0.92, ZH1), M))               # thin slab only: the racks no longer sit inside a collision box
    return out


_used = {f["mat"] for f in hall_faces()}
for _i in range(len(SHADER_SPECS)):
    if _i not in _used and not SHADER_SPECS[_i][3].startswith("lp20_unused"):
        SHADER_SPECS[_i] = K26.PANEL + ("lp20_unused_%d" % _i,)
for _nm in ("hall_faces", "vanilla_props", "collision_boxes"):
    for _m in (K30, K21, K22, K23, K24, K25, K26, K27, K28):
        setattr(_m, _nm, globals()[_nm])
