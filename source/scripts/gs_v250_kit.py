# LONG PIG 2.5.0 - second quality pass (revision: windows / blinds, cooler variety, coffee corner,
# local grime, Forge candidates). On top of 2.4.0; protected as before (exterior, ceiling, all lights, fans, menu boards).
#   FORGE   * candidates scanned read-only in the owner's game (gs_54_forge_scan.py -> docs/_raw/forge_scan.json) and their
#             Forge previews reviewed; used here: prop_bar_beerfridge_01, prop_bar_fridge_01, v_ret_gassweets,
#             v_ret_ml_beer* cartons, v_ret_ml_sweet* boxes, v_res_r_coffpot, prop_slush_dispenser, prop_food_cups2,
#             prop_food_coffee. Rejected / not placed: see docs/v250/PROP_RESEARCH.md.
#   COOLERS * last bay: two black glass-door uprights instead of the sixth identical unit; bulkhead extended 13 cm.
#   COFFEE  * coffee machine + glass pot + slush machine, cup towers, take-away cups; restock cartons beside the coolers.
#   STOCK   * candy rack as the island end cap (was a beer stack), candy boxes on the kiosk ledge (were loose bars).
#   GRIME   * 8 local alpha decals (lp25_grime) where dirt is motivated; nothing baked wall-wide.
#   BLINDS  * data only (gs_49b_blinds_v250.py): all five window bays, 80 slats, one pitch, one open angle.
import json, math
from pathlib import Path
import gs_v240_kit as K24
from gs_v240_kit import *                    # noqa: F401,F403

VERSION = "2.5.0"
K23, K22, K21, K30, V, B9, PG = K24.K23, K24.K22, K24.K21, K24.K30, K24.V, K24.B9, K24.PG
F0 = K24.F0
XW, YS, XE, YN = K24.XW, K24.YS, K24.XE, K24.YN
_quad, _bx, _sign2 = K22._quad, K22._bx, K23._sign2
_hf24, _vp24, _cb24 = K24.hall_faces, K24.vanilla_props, K24.collision_boxes
_INV = {v: k for k, v in MAT.items()}
FF = K22.FRIDGE_FRONT
_FS = json.loads((Path(__file__).resolve().parents[2] / "docs" / "_raw" / "forge_scan.json").read_text())["items"]
for _n, _v in _FS.items():
    if _n not in VB:
        VB[_n] = (tuple(_v["min"]), tuple(_v["max"]))

SHADER_SPECS[MAT["decal6"]] = ("decal.sps", {"DiffuseSampler": "lp25_grime"}, {}, "lp25_grime")
V.REP["decal6"] = 1.0
COOL_END = 6.47                              # new end of the cooler run (was 6.34)
BLACK = (("prop_bar_beerfridge_01", 5.21), ("prop_bar_fridge_01", 6.05))
_CELL = {"smudge": (0.0, 0.5, 0.5, 1.0), "scuff": (0.5, 0.5, 1.0, 1.0), "drips": (0.0, 0.0, 0.5, 0.5), "dust": (0.5, 0.0, 1.0, 0.5)}
GRIME = (  # cell, centre (s, t), width, z0, z1, wall normal, reason
    ("smudge", (0.92, YS), 0.50, 1.02, 1.70, (0.0, 1.0)),       # hands on the wall beside the entrance
    ("smudge", (XW, 3.36), 0.42, 1.02, 1.62, (1.0, 0.0)),       # beside the ATM
    ("smudge", (6.25, YS), 1.00, 1.00, 1.50, (0.0, 1.0)),       # above the chest cooler (lids, elbows)
    ("drips", (6.38, YS), 0.34, 1.04, 1.60, (0.0, 1.0)),        # under the NO LOITERING notice
    ("dust", (6.74, YN), 0.50, 1.00, 1.70, (0.0, -1.0)),        # corner behind the restock cartons
    ("scuff", (7.00, 3.70), 3.00, 0.12, 0.46, (-1.0, 0.0)),     # shoe scuffs on the service counter front
    ("scuff", (7.00, 6.30), 1.00, 0.12, 0.46, (-1.0, 0.0)),     # ... and on the coffee counter
    ("dust", (XW, 2.75), 0.50, 1.00, 1.60, (1.0, 0.0)),         # corner between the entrance wall and the ATM
)


def hall_faces():
    out = []
    for f in _hf24():
        P = f["v"]; m = _INV.get(f["mat"])
        if m == "white20" and all(6.335 < p[0] < 6.375 for p in P) and max(p[2] for p in P) < 2.29 and min(p[1] for p in P) > FF - 0.01:
            continue                                                       # old end panel of the cooler run
        if m == "signs23b" and all(abs(p[0] - 6.374) < 0.01 for p in P) and min(p[1] for p in P) > 6.2:
            continue                                                       # ICE notice on it
        out.append(f)
    _bx(out, 6.34, COOL_END + 0.03, FF + 0.02, YN, 2.285, 2.92, "white20")  # bulkhead extension
    _bx(out, 6.34, COOL_END + 0.03, FF, YN, 2.265, 2.285, "alu20")
    _bx(out, COOL_END, COOL_END + 0.03, FF, YN, F0, 2.285, "white20")       # new end panel
    _bx(out, 4.79, COOL_END, FF + 0.03, YN, 2.165, 2.265, "top20")          # filler above the two black uprights (2.17 m)
    _sign2(out, "ice", (COOL_END + 0.03, 6.60), 0.50, 1.50, 1.75, (1.0, 0.0), 0.004)
    for cell, c, w, z0, z1, n in GRIME:
        _quad(out, c, w, z0, z1, n, "decal6", _CELL[cell], 0.004)
    return out


def vanilla_props():
    out = []
    cart = ("v_ret_ml_beerbla2", "v_ret_ml_beerpat2", "v_ret_ml_beerjak2", "v_ret_ml_beerben2", "v_ret_ml_beerpis1", "v_ret_ml_beerbla1")
    k_c = 0
    for e in _vp24():
        n, s, t, z, yaw = e
        hall = s < XE - 0.02 and t < YN - 0.02
        if n == "v_ret_ml_fridge" and abs(s - K22.FRIDGE_S[-1]) < 0.05:
            continue                                                       # sixth identical cooler
        if n == "v_ind_cf_crate2" and hall and s > 6.4 and t > 6.2:
            continue                                                       # green crates -> restock cartons
        if n == "prop_cs_beer_box" and hall:
            if abs(s - 4.42) < 0.05:
                continue                                                   # end-cap beer stack -> candy rack
            e = (cart[k_c % len(cart)], s, t, z, yaw); k_c += 1            # overstock on the gondolas: retail cartons
        if 7.0 < s < 7.9 and 5.75 < t < 6.90 and 0.90 < z < 1.0:
            continue                                                       # old coffee counter set
        if n in ("prop_choc_ego", "prop_choc_meto", "prop_candy_pqs", "ng_proc_candy01a") and abs(s - 6.88) < 0.02 and abs(z - 1.02) < 0.01:
            continue                                                       # loose bars on the kiosk ledge
        out.append(e)
    for nm, s in BLACK:
        out.append(B9._against(nm, (s, YN - 0.08), (0.0, -1.0), 0.0))
    for k, (t, cnt) in enumerate(((6.72, 3), (6.36, 2))):                  # restock cartons between coolers and coffee
        for j in range(cnt):
            out.append((cart[(k * 3 + j) % len(cart)], 6.75, t, F0 + 0.33 * j, (4.0, -6.0, 3.0)[j]))
    out.append(B9._against("v_ret_gassweets", (K22.ISLAND[1][-1] + 1.05, K22.ISLAND[0] + 0.025), (1.0, 0.0)))   # island end cap
    for nm, t in (("v_ret_ml_sweet9", -1.02), ("v_ret_ml_sweetego", -0.66), ("v_ret_ml_sweet1", 0.70)):
        out.append((nm, 6.868, t, 1.02, 90.0))
    out += [("prop_coffee_mac_02", 7.62, 5.98, 0.94, -90.0), ("v_res_r_coffpot", 7.60, 6.27, 0.94, -90.0), ("prop_slush_dispenser", 7.58, 6.62, 0.94, -90.0),
            ("prop_food_sugarjar", 7.20, 5.90, 0.94, 0.0), ("prop_food_cups2", 7.22, 6.08, 0.94, 0.0), ("prop_food_bs_cups01", 7.22, 6.24, 0.94, 0.0),
            ("prop_food_coffee", 7.20, 6.42, 0.94, 0.0), ("prop_food_coffee", 7.31, 6.50, 0.94, 30.0), ("prop_bar_napkindisp", 7.24, 6.78, 0.94, 90.0)]
    return out


def collision_boxes():
    M = "WOOD_SOLID_MEDIUM"
    out = []
    for b in _cb24():
        (s0, s1, t0, t1, z0, z1) = b[0]
        if (abs(s0 - 4.15) < 0.01 and abs(s1 - 4.80) < 0.01) or (abs(s0 - 6.42) < 0.01 and abs(s1 - 6.94) < 0.01):
            continue                                                       # beer stack at the end cap, green crates
        out.append(b)
    out += [((6.37, COOL_END + 0.03, FF, YN, F0, 2.92), M), ((6.50, 7.00, 6.18, 6.92, F0, 1.0), M),
            ((K22.ISLAND[1][-1] + 1.05, K22.ISLAND[1][-1] + 1.36, 3.38, 4.97, F0, 1.05), M)]
    return out


_used = {f["mat"] for f in hall_faces()}
for _i in range(len(SHADER_SPECS)):
    if _i not in _used and not SHADER_SPECS[_i][3].startswith("lp20_unused"):
        SHADER_SPECS[_i] = ("default.sps", {"DiffuseSampler": "lp20_panel_off"}, {}, "lp20_unused_%d" % _i)
for _n in ("hall_faces", "vanilla_props", "collision_boxes"):
    for _m in (K30, K21, K22, K23, K24):
        setattr(_m, _n, globals()[_n])
