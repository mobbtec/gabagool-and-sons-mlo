# LONG PIG 2.8.0 - fixes from the owner's in-game screenshots of 2.7.0 (2026-11-21 20:31):
#   * cartons on top of the gondolas floated -> removed; a tidy delivery stack stands in the corner by the entrance instead
#   * own basket stack removed (owner wants a GTA prop); fruit stand removed (only the fruit rendered, the crates did not)
#   * snack rack: the lower part stuck in the counter front -> the counter front is closed again below 0.64 m, the rack stands
#     5 cm deeper so only its top tier (candy bars) shows in a lined opening; black lining no longer proud of the front
#   * counter top tidy: items in one straight row; lottery display + LOTTO sign moved to the tobacco unit
#   * tobacco wall rebuilt as a modelled 5-bay unit like the 24/7 reference: side panels, pegboard back, three shelf rows
#     (snacks / cigarette racks / lottery + candy), price strips, lit header boxes with brand names, 3 wash lights
#   * walls: far fewer cracks, none embossed (lp28_wall)
import json, math
from pathlib import Path
import gs_v270_kit as K27
from gs_v270_kit import *                    # noqa: F401,F403

VERSION = "2.8.0"
K26, K25, K24, K23, K22, K21, K30 = K27.K26, K27.K25, K27.K24, K27.K23, K27.K22, K27.K21, K27.K30
V, B9, PG = K27.V, K27.B9, K27.PG
F0 = PG.FLOOR
XW, YS, XE, YN = K27.XW, K27.YS, K27.XE, K27.YN
_quad, _bx, _sign, _sign2 = K22._quad, K22._bx, K22._sign, K23._sign2
_INV = {v: k for k, v in MAT.items()}
_hf26, _vp26, _cb26, _mk26 = K27._hf26, K27._vp26, K27._cb26, K27._mk26
_ol27, _shell27 = K27.open_lights, PG.shell_faces
_clip, _foot, _ns = K27._clip, K27._foot, K27._ns
ISLAND, ROW2, CART, RACK = K27.ISLAND, K27.ROW2, K26.CART, K27.RACK
HREG = json.loads((Path(__file__).resolve().parents[1] / "textures" / "v280" / "lp28_heads_regions.json").read_text())
_sb = Path(__file__).resolve().parents[2] / "docs" / "_raw" / "scan_basket.json"
if _sb.is_file():
    for _n, _v in json.loads(_sb.read_text())["items"].items():
        VB.setdefault(_n, (tuple(_v["min"]), tuple(_v["max"])))
BASKET_PROP = None                            # set to an archetype name once a GTA basket-stack prop is confirmed

SHELL_TEX = dict(K27.SHELL_TEX)
SHELL_TEX["wall"] = ("lp28_wall", "lp28_wall_n", "lp28_wall_s", 10.0, 0.15)
SHELL_EXTRA_SPECS = list(K27.SHELL_EXTRA_SPECS)
SHELL_EXTRA_SPECS[0] = _ns("lp28_wall", 0.15, 10.0, 0.6, "lp28_wall_x")
SHELL_EXTRA_SPECS[2] = _ns("lp28_wall", 0.15, 10.0, 0.6, "lp28_wall_y")
SHELL_TEX_N = K27.SHELL_TEX_N

# ---------------------------------------------------------------------------------------------------- snack rack opening
NS1 = 7.345                                   # back of the opening; the rack front then sits at 7.05, behind the counter boards (7.01-7.03)
ZC = 0.64                                     # the counter front stays closed below this height
_re = B9._against(RACK, (NS1 - 0.014, 5.66), (-1.0, 0.0), 0.0)
_rf = _foot(RACK, _re[1], _re[2], _re[4])
NT0, NT1 = round(_rf[2] - 0.030, 3), round(_rf[3] + 0.030, 3)


def _open(f):
    P = f["v"]
    if max(p[2] for p in P) > 1.36 or max(p[2] for p in P) < ZC + 1e-4 or min(p[0] for p in P) > NS1 - 1e-4 or max(p[0] for p in P) < 6.90 \
            or max(p[1] for p in P) < NT0 + 1e-4 or min(p[1] for p in P) > NT1 - 1e-4:
        return [f]
    poly = list(zip([tuple(p) for p in P], [tuple(u) for u in f["uv"]]))
    a = _clip(poly, 1, NT0, True); rest = _clip(poly, 1, NT0, False)
    b = _clip(rest, 1, NT1, False); rest = _clip(rest, 1, NT1, True)
    c = _clip(rest, 0, NS1, False); rest = _clip(rest, 0, NS1, True)
    d = _clip(rest, 2, ZC, True)
    keep = []
    for q in (a, b, c, d):
        if q:
            area = 0.0
            for i in range(1, len(q) - 1):
                u = [q[i][0][j] - q[0][0][j] for j in range(3)]; w = [q[i + 1][0][j] - q[0][0][j] for j in range(3)]
                area += math.sqrt((u[1] * w[2] - u[2] * w[1]) ** 2 + (u[2] * w[0] - u[0] * w[2]) ** 2 + (u[0] * w[1] - u[1] * w[0]) ** 2)
            if area > 2e-6:
                keep.append(dict(f, v=[p for p, _u in q], uv=[u for _p, u in q]))
    return keep


def _shell_280(*a, **k):
    out = []
    for f in _shell27(*a, **k):
        if isinstance(f, dict) and f["mat"] == 7:
            out += _open(f)                                              # board cladding of the counter front
        else:
            out.append(f)
    return out


PG.shell_faces = _shell_280
_HSTAT = {}


def hall_faces():
    out, st = [], {"east": 0, "open_cut": 0}
    for f in _hf26():
        if K27._east_wall_old(f):
            st["east"] += 1; continue
        fs = _open(f)
        if len(fs) != 1 or fs[0] is not f:
            st["open_cut"] += 1
        out += fs
    L = 0.012                                                            # lining inside the opening, nothing proud of the counter
    _bx(out, NS1 - L, NS1, NT0, NT1, ZC - 0.30, 1.016, "iron")
    _bx(out, 6.958, NS1, NT0, NT0 + L, ZC, 1.016, "iron")
    _bx(out, 6.958, NS1, NT1 - L, NT1, ZC, 1.016, "iron")
    _bx(out, 6.958, _rf[0] - 0.004, NT0 + L, NT1 - L, ZC - 0.012, ZC, "iron")      # sill between the counter front and the rack
    _HSTAT.clear(); _HSTAT.update(st)
    return [f for f in out if f]


# ---------------------------------------------------------------------------------------------------- tobacco unit
BAYS, DIV, BAYW = 5, 0.030, 1.225
UT0 = 0.19                                    # unit start along the wall (t)
UT1 = UT0 + BAYS * BAYW + (BAYS + 1) * DIV
ZB, ZS3, ZS2, ZS1, ZTOP, ZH1 = 0.925, 0.975, 1.440, 2.080, 2.465, 2.800     # base, shelf levels (bottom faces), top panel, header top
DEP3, DEP = 0.205, 0.145                      # depth of the lower shelf / of the upper shelves and side panels above it
HEADS = ("cardiaque", "redwood", "longpig", "debonaire", "lotto")
_fy = B9.wall_yaw((-1.0, 0.0))


def _bay(k):
    t0 = UT0 + DIV + k * (BAYW + DIV)
    return t0, t0 + BAYW


def _unit(out):
    S = XE - 0.004
    _bx(out, S - 0.010, S, UT0, UT1, ZB, ZH1, "white20")                               # carcass back
    for k in range(BAYS + 1):                                                           # side panels: deep below, stepped back above
        t = UT0 + k * (BAYW + DIV)
        _bx(out, S - DEP3, S - 0.010, t, t + DIV, ZB, ZS2 + 0.02, "white20", 0.003)
        _bx(out, S - DEP, S - 0.010, t, t + DIV, ZS2 + 0.02, ZH1, "white20", 0.003)
    _bx(out, S - DEP3 - 0.006, S - 0.010, UT0, UT1, ZB, ZS3, "top20")                   # plinth on the back counter
    for k in range(BAYS):
        t0, t1 = _bay(k)
        _quad(out, (S - 0.010, (t0 + t1) / 2), t1 - t0, ZS3, ZTOP, (-1.0, 0.0), "mat", (0.0, 0.0, (t1 - t0) / 0.2, (ZTOP - ZS3) / 0.2), 0.0015)   # pegboard
        for z, dep in ((ZS2, DEP), (ZS1, DEP)):                                         # shelves with a lip and a price strip
            _bx(out, S - dep, S - 0.010, t0, t1, z, z + 0.020, "white20")
            _bx(out, S - dep - 0.004, S - dep, t0, t1, z - 0.012, z + 0.030, "alu20")
            _quad(out, (S - dep - 0.004, (t0 + t1) / 2), t1 - t0 - 0.01, z - 0.008, z + 0.026, (-1.0, 0.0), "teal20", (0.0, 0.42, 3.0, 0.52), 0.001)
        _bx(out, S - DEP3 - 0.004, S - DEP3, t0, t1, ZS3 - 0.01, ZS3 + 0.035, "alu20")   # lip of the lower shelf
        _quad(out, (S - DEP3 - 0.004, (t0 + t1) / 2), t1 - t0 - 0.01, ZS3 - 0.006, ZS3 + 0.031, (-1.0, 0.0), "teal20", (0.0, 0.42, 3.0, 0.52), 0.001)
        _bx(out, S - DEP, S - 0.010, t0, t1, ZTOP, ZTOP + 0.018, "white20")              # top panel under the light box
        # header light box: dark frame, lit face set back 8 mm
        _bx(out, S - DEP - 0.012, S - DEP, t0 - 0.004, t1 + 0.004, ZTOP + 0.018, ZTOP + 0.036, "alu20")
        _bx(out, S - DEP - 0.012, S - DEP, t0 - 0.004, t1 + 0.004, ZH1 - 0.018, ZH1, "alu20")
        for t in (t0 - 0.004, t1 - 0.010):
            _bx(out, S - DEP - 0.012, S - DEP, t, t + 0.014, ZTOP + 0.036, ZH1 - 0.018, "alu20")
        _bx(out, S - DEP, S - 0.010, t0, t1, ZTOP + 0.018, ZH1, "top20")
        x0, y0, x1, y1 = HREG[HEADS[k]]
        _quad(out, (S - DEP, (t0 + t1) / 2), t1 - t0 - 0.02, ZTOP + 0.036, ZH1 - 0.018, (-1.0, 0.0), "menu",
              (x0 / 1024.0, 1 - y1 / 512.0, x1 / 1024.0, 1 - y0 / 512.0), 0.004)
    _bx(out, S - DEP - 0.02, S, UT0 - 0.006, UT1 + 0.006, ZH1, ZH1 + 0.02, "white20", 0.004)   # cap


def _unit_props():
    out = []
    S = XE - 0.016
    chips = ("v_ret_ml_chips1", "v_ret_ml_chips2", "v_ret_ml_chips3", "v_ret_ml_chips4")
    sw = ("v_ret_ml_sweet5", "v_ret_ml_sweet6", "v_ret_ml_sweet7", "v_ret_ml_sweet4")

    def at(name, t, z):
        e = B9._against(name, (S, t), (-1.0, 0.0), 0.0)
        return (e[0], e[1], e[2], z, e[4])
    for k in range(BAYS):
        t0, t1 = _bay(k); tc = (t0 + t1) / 2
        f = _foot("v_ret_247_cigs", 0.0, 0.0, _fy)
        out.append(at("v_ret_247_cigs", tc - (f[2] + f[3]) / 2, ZS2 + 0.020))            # cigarette rack row
        for j in range(5):                                                               # snack row
            out.append(at(chips[(j + k) % 4], t0 + 0.1225 + 0.245 * j, ZS1 + 0.020))
        z3 = ZS3
        if k % 2 == 0:
            out.append(at("v_ret_247_lottery", tc, z3))                                  # lottery ticket display
            for j, dt in enumerate((-0.54, 0.54)):
                out.append(at(sw[(j + k) % 4], tc + dt, z3))
        elif k == 3:
            out.append(at("v_ret_247_lotterysign", tc, z3))                              # LOTTO sign
            for j, dt in enumerate((-0.50, -0.33, 0.33, 0.50)):
                out.append(at(sw[j], tc + dt, z3))
        else:
            for j in range(7):
                out.append(at(sw[j % 4], t0 + 0.11 + 0.167 * j, z3))
    return out


def market_faces():
    out = [f for f in K27.market_faces() if not (min(p[0] for p in f["v"]) > XE - 0.13 and 0.10 < min(p[1] for p in f["v"]) and max(p[1] for p in f["v"]) < 6.60
                                                 and 1.0 < min(p[2] for p in f["v"]) and max(p[2] for p in f["v"]) < 2.715)]     # 2.7.0 headers / backing board
    _unit(out)
    return [f for f in out if f]


def _market_specs():
    sp = list(K26._SPECS25)
    sp[MAT["teal20"]] = _ns("lp27_band", 0.25, 16.0)
    sp[MAT["decal6"]] = ("decal.sps", {"DiffuseSampler": "lp27_grime"}, {}, "lp27_grime")
    sp[MAT["menu"]] = ("emissive.sps", {"DiffuseSampler": "lp28_heads"}, {"emissiveMultiplier": 2.2}, "lp28_heads_e")
    sp[MAT["mat"]] = _ns("lp28_peg", 0.2, 20.0, 1.0)
    used = {f["mat"] for f in market_faces()}
    return [(sp[i][0], sp[i][1], sp[i][2], sp[i][3] + "_mk") if i in used else K26.PANEL + ("lp20_unused_mk_%d" % i,) for i in range(len(sp))]


EXTRA_HALL_DRAWABLES = (("gs_v26_market", market_faces, _market_specs),)

# ---------------------------------------------------------------------------------------------------- props + collision
_u = (PG.ch(PG.D1["a"][0], PG.CH_IN)[0] - PG.P_SW[0], PG.ch(PG.D1["a"][0], PG.CH_IN)[1] - PG.P_SW[1])
_ul = math.hypot(*_u); _u = (_u[0] / _ul, _u[1] / _ul)
_n = (0.731, 0.682)
STACK = []                                    # delivery stack in the corner between the first booth end (s 0.63) and the entrance door:
for _col, (_t, _cnt) in enumerate(((-0.66, 3), (-0.15, 2))):     # long side along the booth end, 2 cm off it; clear of the door leaf up to ~120 deg
    for _h in range(_cnt):
        STACK.append((CART[(_col * 3 + _h) % len(CART)], 0.445, _t, F0 + 0.326 * _h, 90.0 + (0.0, 3.0, -2.5)[_h]))
TOP = {"prop_till_01": (7.62, 5.12), "prop_choc_ego": (7.50, 4.90), "prop_choc_meto": (7.58, 4.90), "prop_candy_pqs": (7.66, 4.90),
       "prop_bar_napkindisp": (7.62, 5.62), "prop_food_ketchup": (7.62, 5.84), "prop_food_mustard": (7.62, 5.94), "prop_food_sugarjar": (7.62, 6.06),
       "prop_juice_dispenser": (7.62, 6.56)}


def vanilla_props():
    out, stools = [], 0
    for e in _vp26():
        n, s, t, z, yaw = e
        hall = s < XE - 0.02 and t < YN - 0.02
        if n == RACK:
            continue
        if n == "lr_prop_clubstool_01" and hall:
            stools += 1
            if stools < 3:
                continue
            e = (n, s, 6.70, z, yaw)
        if hall and s > 9.60 and z > 1.30:
            continue                                                     # old back-wall shelf stock
        if hall and n in CART and z > 1.4 and s < 6.9:
            continue                                                     # cartons on top of the gondolas (floated in game)
        if hall and n in CART and abs(s - (ROW2[1][-1] + 1.30)) < 0.05:
            continue                                                     # carton stack at the row-2 end -> entrance corner
        if hall and 6.95 < s < 8.05 and 4.80 < t < 6.90 and z > 0.95:    # counter-end top: one straight row
            if n not in TOP:
                continue
            e = (n, TOP[n][0], TOP[n][1], z, 90.0 if n in ("prop_till_01", "prop_bar_napkindisp") else (-90.0 if n == "prop_juice_dispenser" else 0.0))
        if hall and s > 9.30 and 0.9 < z < 1.3 and n in ("prop_coffee_mac_02", "prop_knife_stand", "prop_radio_01", "v_res_tt_platepile", "prop_cs_paper_cup"):
            e = (n, min(s, 9.50) if n != "prop_cs_paper_cup" else s - 0.22, {"prop_coffee_mac_02": 5.72, "v_res_tt_platepile": 5.12}.get(n, t), z, yaw)   # clear of the unit / staff door
        if n == "v_res_fa_bread01" or n == "v_res_fa_bread02":
            e = (n, 9.52, t, z, yaw)
        out.append(e)
    out.append(_re)
    out += _unit_props()
    out.append(K27.DONUT)
    out += STACK
    for k, t in enumerate((0.55, 1.05, 4.55, 5.15)):                     # candy boxes on the back counter, in line
        out.append((K27.SWEETS[k], 9.36, t, 0.92, 90.0))
    if BASKET_PROP:
        out.append(B9._against(BASKET_PROP, (ISLAND[1][0] - 1.05, ISLAND[0]), (-1.0, 0.0)))
    return out


def collision_boxes():
    M = "WOOD_SOLID_MEDIUM"
    out = [b for b in _cb26() if not (abs(b[0][5] - 1.05) < 1e-6 and abs(b[0][2] - 3.38) < 1e-6) and not (abs(b[0][5] - 0.66) < 1e-6 and b[0][0] > 5.0)]
    d = _foot("v_ret_247_donuts", K27.DONUT[1], K27.DONUT[2], K27.DONUT[4])
    xs = [e[1] for e in STACK]; ys = [e[2] for e in STACK]
    out += [((d[0], d[1], d[2], d[3], F0, 1.91), M), ((min(xs) - 0.25, max(xs) + 0.25, min(ys) - 0.25, max(ys) + 0.25, F0, 0.66), M),
            ((XE - 0.21, XE, UT0, UT1, 0.92, ZH1), M)]
    return out


# ---------------------------------------------------------------------------------------------------- lights: wash on the tobacco unit
def open_lights():
    L = list(_ol27())
    tpl = [l for l in L if isinstance(l, dict) and l.get("kind") == "cooler_glow"][0]
    for t in (1.45, 3.34, 5.23):
        L.append(dict(tpl, kind="tobacco_wash", type="POINT", pos=(XE - 0.62, t, 2.30), color=(1.0, 0.90, 0.74), intensity=0.85, falloff=2.3, exponent=2.0))
    return L


SHADER_SPECS[MAT["tile"]] = K27.SHADER_SPECS[MAT["tile"]]
_used = {f["mat"] for f in hall_faces()}
for _i in range(len(SHADER_SPECS)):
    if _i not in _used and not SHADER_SPECS[_i][3].startswith("lp20_unused"):
        SHADER_SPECS[_i] = K26.PANEL + ("lp20_unused_%d" % _i,)
for _nm in ("hall_faces", "vanilla_props", "collision_boxes", "open_lights"):
    for _m in (K30, K21, K22, K23, K24, K25, K26, K27):
        setattr(_m, _nm, globals()[_nm])
for _m in (K30, K21, K22, K23, K24, K25, K26, K27):
    _m.SHELL_TEX, _m.SHELL_EXTRA_SPECS, _m.SHELL_TEX_N = SHELL_TEX, SHELL_EXTRA_SPECS, SHELL_TEX_N
