# LONG PIG 3.0.0 - on top of 2.9.0 (owner 2026-11-22 14:25, in-game screenshots of 2.9.0):
#   * saloon doors by the deli case removed (client/saloon.lua no longer loaded - fxmanifest)
#   * tobacco unit rebuilt: hangs above the back counter (from 1.19 m), one depth everywhere; cigarettes are single packs
#     (v_ret_ml_cigs..6) standing on shelves in straight rows - the peg rack v_ret_247_cigs is gone; LONG PIG header -> METEORITE;
#     header boxes brighter (emissive 4.0)
#   * back counter tidy: candy boxes off, one short tray / cup stack, everything square to the wall
#   * small wall shelf with the oil tin on the north wall -> CCTV camera (prop_cctv_cam_04c)
#   * south wall behind the counter: painted "Deli" lettering (own texture lp30_deli); dark smudge decals removed; calmer plaster
#   * lighting NOT touched (owner: another program does it)
import json, math
from pathlib import Path
import gs_v290_kit as K29
from gs_v290_kit import *                    # noqa: F401,F403

VERSION = "3.0.0"
K28, K27, K26, K25, K24, K23, K22, K21, K30 = K29.K28, K29.K27, K29.K26, K29.K25, K29.K24, K29.K23, K29.K22, K29.K21, K29.K30
V, B9, PG = K29.V, K29.B9, K29.PG
F0 = PG.FLOOR
XW, YS, XE, YN = K29.XW, K29.YS, K29.XE, K29.YN
_quad, _bx = K22._quad, K22._bx
_INV = {v: k for k, v in MAT.items()}
_hf29, _mk29, _cb29 = K29.hall_faces, K29.market_faces, K29.collision_boxes
_vp28 = K29._vp28
_foot, _bay = K29._foot, K29._bay
UT0, UT1, BAYS, DIV, BAYW = K29.UT0, K29.UT1, K29.BAYS, K29.DIV, K29.BAYW
ZTOP, ZH1 = K29.ZTOP, K29.ZH1
HREG = json.loads((Path(__file__).resolve().parents[1] / "textures" / "v300" / "lp30_heads_regions.json").read_text())
_sc = Path(__file__).resolve().parents[2] / "docs" / "_raw" / "scan_cctv.json"
CAM = "prop_cctv_cam_04c"
VB.setdefault(CAM, ((-0.159, -0.443, -0.32), (0.155, 0.016, 0.107)))
if _sc.is_file():
    _it = json.loads(_sc.read_text())["items"].get(CAM)
    if _it:
        VB[CAM] = (tuple(_it["min"]), tuple(_it["max"]))

SHELL_TEX = dict(K28.SHELL_TEX)
SHELL_TEX["wall"] = ("lp30_wall", "lp30_wall_n", "lp30_wall_s", 10.0, 0.12)
SHELL_EXTRA_SPECS = list(K28.SHELL_EXTRA_SPECS)
SHELL_EXTRA_SPECS[0] = K28._ns("lp30_wall", 0.12, 10.0, 0.3, "lp30_wall_x")
SHELL_EXTRA_SPECS[2] = K28._ns("lp30_wall", 0.12, 10.0, 0.3, "lp30_wall_y")
SHELL_TEX_N = K28.SHELL_TEX_N

# ---------------------------------------------------------------------------------------------------- tobacco unit
ZBACK = 0.925                                 # white back panel starts on the counter top
ZP, Z0 = 1.19, 1.22                           # underside of the unit / bottom of the lowest shelf: clear of everything on the counter
D = 0.215                                     # one depth for panels, shelves and header boxes
_H3, _H4, _H5 = (ZTOP - Z0) / 3 - 0.02, (ZTOP - Z0) / 4 - 0.02, (ZTOP - Z0) / 5 - 0.02
# section k runs from the kitchen door (k = 0) to the staff door (k = 4)
SECTIONS = (("mixed",   "redwood",   (0.48, _H5, _H5, ZTOP - Z0 - 0.08 - 0.48 - 2 * _H5)),
            ("candy",   "meteorite", (_H4,) * 4),
            ("cigs",    "cardiaque", (_H5,) * 5),
            ("lottery", "lotto",     (_H3,) * 3),
            ("snacks",  "debonaire", (_H3,) * 3))


def _rows(k):
    """[(shelf top z, clear height)] for section k, bottom to top; shelves are 20 mm thick."""
    out, z = [], Z0
    for h in SECTIONS[k][2]:
        out.append((z + 0.020, h)); z += h + 0.020
    return out


def _unit(out):
    S = XE - 0.004
    _bx(out, S - 0.010, S, UT0, UT1, ZBACK, ZH1, "white20")                             # back panel down to the counter
    for k in range(BAYS + 1):                                                           # side panels
        t = UT0 + k * (BAYW + DIV)
        _bx(out, S - D, S - 0.010, t, t + DIV, ZP, ZH1, "white20", 0.003)
    _bx(out, S - D - 0.006, S - 0.010, UT0, UT1, ZP, Z0, "top20")                       # dark bottom rail
    for k in range(BAYS):
        t0, t1 = _bay(k)
        _quad(out, (S - 0.010, (t0 + t1) / 2), t1 - t0, Z0, ZTOP, (-1.0, 0.0), "mat", (0.0, 0.0, (t1 - t0) / 0.2, (ZTOP - Z0) / 0.2), 0.0015)   # pegboard
        for (zt, _h) in _rows(k):                                                       # shelf, lip, price strip
            z = zt - 0.020
            _bx(out, S - D, S - 0.010, t0, t1, z, zt, "white20")
            _bx(out, S - D - 0.004, S - D, t0, t1, z - 0.010, zt + 0.012, "alu20")
            _quad(out, (S - D - 0.004, (t0 + t1) / 2), t1 - t0 - 0.01, z - 0.007, zt + 0.009, (-1.0, 0.0), "teal20", (0.0, 0.42, 3.0, 0.52), 0.001)
        _bx(out, S - D, S - 0.010, t0, t1, ZTOP, ZTOP + 0.018, "white20")                # top panel under the light box
        _bx(out, S - D - 0.012, S - D, t0 - 0.004, t1 + 0.004, ZTOP + 0.018, ZTOP + 0.036, "alu20")
        _bx(out, S - D - 0.012, S - D, t0 - 0.004, t1 + 0.004, ZH1 - 0.018, ZH1, "alu20")
        for t in (t0 - 0.004, t1 - 0.010):
            _bx(out, S - D - 0.012, S - D, t, t + 0.014, ZTOP + 0.036, ZH1 - 0.018, "alu20")
        _bx(out, S - D, S - 0.010, t0, t1, ZTOP + 0.018, ZH1, "top20")
        x0, y0, x1, y1 = HREG[SECTIONS[k][1]]
        _quad(out, (S - D, (t0 + t1) / 2), t1 - t0 - 0.02, ZTOP + 0.036, ZH1 - 0.018, (-1.0, 0.0), "menu",
              (x0 / 1024.0, 1 - y1 / 512.0, x1 / 1024.0, 1 - y0 / 512.0), 0.004)
    _bx(out, S - D - 0.02, S, UT0 - 0.006, UT1 + 0.006, ZH1, ZH1 + 0.02, "white20", 0.004)   # cap


CHIPS = K29.CHIPS
CANDY = K29.SW_T                              # 0.14-0.16 m wide, 0.20 m deep: they fit the shelf (the 0.27 m boxes did not)
CIGS = ("v_ret_ml_cigs", "v_ret_ml_cigs2", "v_ret_ml_cigs3", "v_ret_ml_cigs4", "v_ret_ml_cigs5", "v_ret_ml_cigs6")
NPACK, PPITCH = 8, 0.140


def _unit_props():
    out = []
    SB = XE - 0.016                                                                      # face of the back panel
    SF = XE - 0.004 - D + 0.014                                                          # 14 mm behind the shelf front

    def at(name, t, z):
        e = B9._against(name, (SB, t), (-1.0, 0.0), 0.0)
        f = _foot(name, e[1], e[2], e[4])
        ds = (SF - f[0]) if (f[1] - f[0]) < 0.15 else 0.0                                # shallow goods stand at the shelf front
        return (e[0], e[1] + ds, e[2] + (t - (f[2] + f[3]) / 2), z, e[4])                # centred on t whatever the model's origin

    def row(names, k, z, pitch, n, one=None):
        t0, t1 = _bay(k); a = (t0 + t1) / 2 - pitch * (n - 1) / 2
        return [at(one or names[j % len(names)], a + pitch * j, z) for j in range(n)]
    for k in range(BAYS):
        t0, t1 = _bay(k); tc = (t0 + t1) / 2
        cat, R = SECTIONS[k][0], _rows(k)
        if cat == "snacks":
            for i, (z, _h) in enumerate(R):
                out += row(CHIPS, k, z, 0.240, 5, CHIPS[i % 4])
        elif cat == "lottery":
            for (z, _h) in R:
                out.append(at("v_ret_247_lottery", tc, z))
        elif cat == "cigs":
            for i, (z, _h) in enumerate(R):
                out += row(CIGS, k, z, PPITCH, NPACK, CIGS[i % 6])                       # one brand per shelf
        elif cat == "candy":
            for i, (z, _h) in enumerate(R):
                out += row(CANDY, k, z, 0.190, 6, CANDY[i % 4])
        else:                                                                            # mixed: LOTTO sign + candy / packs / packs / candy
            out.append(at("v_ret_247_lotterysign", tc, R[0][0]))
            for j, dt in enumerate((-0.47, -0.28, 0.28, 0.47)):
                out.append(at(CANDY[j], tc + dt, R[0][0]))
            out += row(CIGS, k, R[1][0], PPITCH, NPACK, CIGS[5])
            out += row(CIGS, k, R[2][0], PPITCH, NPACK, CIGS[3])
            out += row(CANDY, k, R[3][0], 0.190, 6, CANDY[2])
    return out


# ---------------------------------------------------------------------------------------------------- market drawable
GRIME = tuple(g for g in K27.GRIME7 if g[0] != "smudge")       # the dark blotches read as dirt stuck on the wall - drips / dust only
DELI = ((8.45, YS), 2.30, 1.52, 2.67)                          # painted lettering on the south wall behind the counter
_MSTAT = {}


def market_faces():
    out, st = [], {"unit29": 0, "decal": 0, "lit_sign": 0}
    for f in _mk29():
        P = f["v"]
        if K29._is28_unit(f):
            st["unit29"] += 1; continue
        if f["mat"] == MAT["decal6"]:
            st["decal"] += 1; continue
        if f["mat"] == MAT["signs20e"] and sum(p[0] for p in P) / len(P) > K26.COOL_END + 0.05:
            st["lit_sign"] += 1; continue                                # lit ATM sign (2.9.0 tested the wrong edge)
        out.append(f)
    _unit(out)
    for cell, c, w, z0, z1, n in GRIME:
        _quad(out, c, w, z0, z1, n, "decal6", K25._CELL[cell], 0.0035)
    _quad(out, DELI[0], DELI[1], DELI[2], DELI[3], (0.0, 1.0), "signs23b", (0.0, 0.0, 1.0, 1.0), 0.004)
    _MSTAT.clear(); _MSTAT.update(st)
    return [f for f in out if f]


def _market_specs():
    sp = list(K26._SPECS25)
    sp[MAT["teal20"]] = K28._ns("lp27_band", 0.25, 16.0)
    sp[MAT["decal6"]] = ("decal.sps", {"DiffuseSampler": "lp27_grime"}, {}, "lp27_grime")
    sp[MAT["signs23b"]] = ("decal.sps", {"DiffuseSampler": "lp30_deli"}, {}, "lp30_deli")
    sp[MAT["menu"]] = ("emissive.sps", {"DiffuseSampler": "lp30_heads"}, {"emissiveMultiplier": 4.0}, "lp30_heads_e")
    sp[MAT["mat"]] = K28._ns("lp28_peg", 0.2, 20.0, 1.0)
    used = {f["mat"] for f in market_faces()}
    return [(sp[i][0], sp[i][1], sp[i][2], sp[i][3] + "_mk") if i in used else K26.PANEL + ("lp20_unused_mk_%d" % i,) for i in range(len(sp))]


EXTRA_HALL_DRAWABLES = (("gs_v26_market", market_faces, _market_specs),)
_HSTAT = {}


def _is_tin_shelf(f):
    P = f["v"]
    return (min(p[0] for p in P) > 5.00 and max(p[0] for p in P) < 5.42 and min(p[1] for p in P) > 6.68
            and min(p[2] for p in P) > 2.45 and max(p[2] for p in P) < 3.02)


def hall_faces():
    out, n = [], 0
    for f in _hf29():
        if _is_tin_shelf(f):
            n += 1; continue                                             # small wall shelf with the oil tin -> CCTV camera
        out.append(f)
    _HSTAT.clear(); _HSTAT.update(K29._HSTAT); _HSTAT["tin_shelf"] = n
    return out


# ---------------------------------------------------------------------------------------------------- props
_UNIT28 = K29._UNIT28
CAM_E = B9._against(CAM, (5.20, YN), (0.0, -1.0), 0.0)
CAM_E = (CAM_E[0], CAM_E[1], CAM_E[2], 2.60, CAM_E[4])
_PSTAT = {}


def vanilla_props():
    out, st = [], {"sweets": 0, "trays": 0, "cups": 0}
    for e in _vp28():
        n, s, t, z, yaw = e
        if n in _UNIT28 and s > XE - 0.25 and z > 0.95:
            continue                                                     # goods of the old unit
        bc = 9.15 < s < XE - 0.02 and 0.90 < z < 1.30 and t < YN - 0.02  # on the back counter
        if bc and n in K27.SWEETS and abs(s - 9.36) < 1e-3:
            st["sweets"] += 1; continue                                  # candy boxes lay over the board, the plates and the cleaver
        if bc and n == "prop_food_tray_01":
            if z > 0.94:
                st["trays"] += 1; continue
            e = (n, 9.48, 2.78, z, 90.0)                                 # two trays, clear of the knife block
        if bc and n == "prop_cs_paper_cup":
            if abs(s - 9.58) > 0.02 or z > 0.97:
                st["cups"] += 1; continue                                # two short stacks instead of three tall ones
        if bc and n == "v_res_fa_chopbrd":
            e = (n, 9.48, t, z, 90.0)
        if bc and n == "prop_cleaver":
            e = (n, 9.48, t, z, 90.0)
        if bc and n in ("v_res_fa_bread01", "v_res_fa_bread02"):
            e = (n, s, t, z, 0.0)
        out.append(e)
    # back of house: every second loose duplicate of the bulk stock goes (never one that carries another prop)
    cnt = {}
    for e in out:
        cnt[e[0]] = cnt.get(e[0], 0) + 1
    seen, keep = {}, []
    for e in out:
        n, s, t, z, _y = e
        boh = s > XE + 0.10 or t > YN + 0.10
        if boh and cnt[n] >= 6 and not any(o is not e and abs(o[1] - s) < 0.30 and abs(o[2] - t) < 0.30 and o[3] > z + 0.01 for o in out):
            seen[n] = seen.get(n, 0) + 1
            if seen[n] % 2 == 0:
                st["boh"] = st.get("boh", 0) + 1; continue
        keep.append(e)
    _PSTAT.clear(); _PSTAT.update(st)
    return keep + _unit_props() + [CAM_E]


collision_boxes = _cb29

_used = {f["mat"] for f in hall_faces()}
for _i in range(len(SHADER_SPECS)):
    if _i not in _used and not SHADER_SPECS[_i][3].startswith("lp20_unused"):
        SHADER_SPECS[_i] = K26.PANEL + ("lp20_unused_%d" % _i,)
_OLD = (K30, K21, K22, K23, K24, K25, K26, K27, K28, K29)
for _nm in ("hall_faces", "vanilla_props", "collision_boxes"):
    for _m in _OLD:
        setattr(_m, _nm, globals()[_nm])
for _m in _OLD:
    _m.SHELL_TEX, _m.SHELL_EXTRA_SPECS, _m.SHELL_TEX_N = SHELL_TEX, SHELL_EXTRA_SPECS, SHELL_TEX_N
