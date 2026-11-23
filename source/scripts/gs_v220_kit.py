# LONG PIG 2.2.0 - bodega rebuild, first real pass (owner on the 2.1.0 blockout, 2026-11-21: "not it - coolers like the
# 2.0 wall, remove the flag, shorten the display case, security glass everywhere exactly like the kiosk reference").
# On top of 2.1.0 (protected: ceiling, all lights, fans, overhead menu boards):
#   * cooler wall of 2.0 (six stocked two-door units under lit headers);
#   * cashier = one closed glazed KIOSK: base with candy shelves and steel ledge, glass in aluminium frames on every open
#     side incl. a chamfered corner, service opening, roof cap, stocked back walls;
#   * short heated case + small cold deli case on one service counter, coffee corner;
#   * stocked gondolas (24/7 units), chest coolers under the window, ATM, 3 stools;
#   * the tile flag behind the old counter and the 1.9 stub wall are gone.
import json, math
from pathlib import Path
import gs_v210_kit as K21
from gs_v210_kit import *                    # noqa: F401,F403

VERSION = "2.2.0"
K30, V, B9, PG, SG = K21.K30, K21.V, K21.B9, K21.PG, K21.SG
W = V.WORLD
F0, CEIL = PG.FLOOR, PG.CEIL
XW, YS, XE, YN = K21.XW, K21.YS, K21.XE, K21.YN
REG = json.loads((Path(__file__).resolve().parents[1] / "textures" / "v200" / "lp20_signs_regions.json").read_text())
_RS = json.loads((Path(__file__).resolve().parents[2] / "docs" / "_raw" / "retail_scan.json").read_text())["items"]
for _n, _v in _RS.items():
    if _n not in VB:
        VB[_n] = (tuple(_v["min"]), tuple(_v["max"]))

# shell: 1.9.3 without the board front of the old counter; the flag tiles become wall paint
def _shell_220(*a, **k):
    out = []
    for f in K30._uvmul(K21._shell_193(*a, **k), 0, 0.5, 0.5):
        if isinstance(f, dict) and f.get("mat") == 7 and max(p[2] for p in f["v"]) < 2.2:
            continue                             # board cladding of the old counter front (s = 7.0), incl. the 1.9 stub
        out.append(f)
    return out


PG.shell_faces = _shell_220
_WALLSPEC = ("normal_spec.sps", {"DiffuseSampler": "lp20_wall", "BumpSampler": "lp20_wall_n", "SpecSampler": "lp20_wall_s"},
             {"specularIntensityMult": 0.25, "specularFalloffMult": 10.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp20_wall_x")
SHELL_EXTRA_SPECS = list(K30.SHELL_EXTRA_SPECS)
SHELL_EXTRA_SPECS[0] = _WALLSPEC
SHELL_EXTRA_SPECS[2] = _WALLSPEC[:3] + ("lp20_wall_y",)
SHELL_TEX_N = 8

for _k, _sp in (("signs20", ("default.sps", {"DiffuseSampler": "lp20_signs"}, {}, "lp20_signs")),
                ("signs20e", ("emissive.sps", {"DiffuseSampler": "lp20_signs"}, {"emissiveMultiplier": 1.2}, "lp20_signs_e"))):
    MAT[_k] = len(SHADER_SPECS)
    SHADER_SPECS.append(_sp)
    V.REP[_k] = 1.0

_bx, _quad = K21._bx, K21._quad
FRIDGE_S = (-2.10, -0.57, 0.96, 2.49, 4.02, 5.55)
FRIDGE_FRONT = YN - 0.70
HEAD = ("ice_cold", "cold_beer", "drinks", "water", "dairy", "deals_cold")
ISLAND = (4.15, (1.00, 3.09))                # row axis t, unit centres s
ROW2 = (1.95, (2.00, 4.09))
KIOSK = ((7.00, YS), (7.00, 1.00), (7.55, 1.55), (XE, 1.55))        # open sides: west face, chamfer, north face
SERVICE = (7.00, 7.70, 1.95, 5.45)           # hot + deli counter under the menu boards
HOTCASE = (2.30, 3.70)
DELICASE = (4.15, 5.10)
COFFEE = (7.00, 7.90, 5.75, 6.90)


def _sign(out, key, c, w, z0, z1, n, mat="signs20e", off=0.004):
    x0, y0, x1, y1 = REG[key]
    _quad(out, c, w, z0, z1, n, mat, (x0 / 2048.0, 1 - y1 / 1024.0, x1 / 2048.0, 1 - y0 / 1024.0), off)


def _segs():
    out = []
    for a, b in zip(KIOSK[:-1], KIOSK[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        out.append((a, b, L, d, (-d[1], d[0])))              # outward normal = left of the walking direction
    return out


def _kiosk(out):
    for i, (a, b, L, d, n) in enumerate(_segs()):
        fr = V.Frame(O=(a[0], a[1], 0.0), X=(d[0], d[1], 0.0), Y=(n[0], n[1], 0.0))
        cb = lambda x0, x1, y0, y1, z0, z1, mat, ch=0.0: out.extend(V.cbox(fr, x0, x1, y0, y1, z0, z1, mat, ch=ch))
        cb(0.0, L, -0.58, -0.03, F0, 0.10, "dark20")                       # kick
        cb(0.0, L, -0.60, 0.0, 0.10, 0.98, "lam20", 0.003)                 # base cabinet
        cb(-0.02, L + 0.02, -0.62, 0.26, 0.98, 1.02, "steel", 0.006)       # steel top with the customer ledge
        if i == 0:                                                         # candy shelving on the customer face
            for z in (0.30, 0.56):
                cb(0.20, L - 0.20, 0.0, 0.22, z, z + 0.02, "white20")
                cb(0.20, L - 0.20, 0.21, 0.225, z + 0.02, z + 0.06, "white20")
            for u in (0.18, L - 0.20):
                cb(u, u + 0.02, 0.0, 0.225, 0.12, 0.94, "lam20")
        else:
            cb(0.12, L - 0.12, 0.0, 0.012, 0.16, 0.92, "top20")            # dark front panel
        # glazing: sill, posts, head, glass; service opening on the west face
        cb(0.0, L, -0.055, 0.0, 1.02, 1.07, "alu20")
        cb(0.0, L, -0.055, 0.0, 2.10, 2.15, "alu20")
        k = max(1, int(round(L / 1.1)))
        for j in range(k + 1):
            u = min(max(L * j / k - 0.025, 0.0), L - 0.05)
            cb(u, u + 0.05, -0.055, -0.005, 1.07, 2.10, "alu20")
        c = (a[0] + d[0] * L / 2 - n[0] * 0.03, a[1] + d[1] * L / 2 - n[1] * 0.03)
        zg = 1.07
        if i == 0:
            zg = 1.07
            u0, u1 = 0.95, 1.55                                             # service opening 0.6 x 0.30 m
            cb(u0 - 0.03, u0, -0.055, -0.005, 1.07, 1.40, "alu20"); cb(u1, u1 + 0.03, -0.055, -0.005, 1.07, 1.40, "alu20")
            cb(u0 - 0.03, u1 + 0.03, -0.055, -0.005, 1.37, 1.40, "alu20")
            for (g0, g1, z0) in ((0.0, u0, 1.07), (u0, u1, 1.40), (u1, L, 1.07)):
                cc = (a[0] + d[0] * (g0 + g1) / 2 - n[0] * 0.03, a[1] + d[1] * (g0 + g1) / 2 - n[1] * 0.03)
                for nn in (n, (-n[0], -n[1])):
                    _quad(out, cc, g1 - g0, z0, 2.10, nn, "glass", (0.0, 0.0, 1.0, 1.0), 0.0)
        else:
            for nn in (n, (-n[0], -n[1])):
                _quad(out, c, L, zg, 2.10, nn, "glass", (0.0, 0.0, 1.0, 1.0), 0.0)
        cb(-0.03, L + 0.03, -0.45, 0.03, 2.15, 2.28, "alu20")              # roof edge
    _bx(out, 7.00, XE, YS, 1.00, 2.17, 2.28, "alu20")                       # roof
    _bx(out, 7.55, XE, 1.00, 1.55, 2.17, 2.28, "alu20")
    # stickers on the glass (customer side)
    _sign(out, "p_noid", (6.97, 0.45), 0.26, 1.60, 1.86, (-1.0, 0.0), "signs20", 0.0)
    _sign(out, "p_lotto", (6.97, -0.75), 0.30, 1.55, 1.85, (-1.0, 0.0), "signs20", 0.0)
    _sign(out, "p_smile", (8.90, 1.58), 0.30, 1.55, 1.85, (0.0, 1.0), "signs20", 0.0)
    _sign(out, "welcome", (8.75, 1.565), 1.90, 0.42, 0.66, (0.0, 1.0), "signs20", 0.0)
    # back walls inside: shelving with a lit header
    for (c, w, n) in (((8.45, YS), 2.30, (0.0, 1.0)), ((XE, 0.82), 1.30, (-1.0, 0.0))):
        r = (-n[1], n[0])
        for z in (1.12, 1.38, 1.64, 1.90):
            s0, s1 = sorted((c[0] - r[0] * w / 2, c[0] + r[0] * w / 2)); t0, t1 = sorted((c[1] - r[1] * w / 2, c[1] + r[1] * w / 2))
            if n[0] == 0.0:
                _bx(out, s0, s1, YS + 0.01, YS + 0.20, z, z + 0.02, "white20")
            else:
                _bx(out, XE - 0.20, XE - 0.01, t0, t1, z, z + 0.02, "white20")
        _sign(out, "cashier", c, min(w, 1.30), 1.94, 2.15, n, "signs20e", 0.21)


def _service(out):
    s0, s1, t0, t1 = SERVICE
    _bx(out, s0 + 0.03, s1 - 0.02, t0, t1, F0, 0.10, "dark20")
    _bx(out, s0, s1, t0, t1, 0.10, 0.90, "lam20", 0.003)
    _bx(out, s0 - 0.04, s1 + 0.03, t0 - 0.02, t1 + 0.02, 0.90, 0.94, "steel", 0.006)
    for (c0, c1, h, warm) in ((HOTCASE[0], HOTCASE[1], 1.44, True), (DELICASE[0], DELICASE[1], 1.32, False)):
        _bx(out, s0 + 0.04, s1 - 0.04, c0, c1, 0.94, 0.985, "steel")                       # tray base
        _bx(out, s0 + 0.04, s1 - 0.04, c0, c1, h, h + 0.04, "alu20" if warm else "white20")  # lid
        if warm:
            _bx(out, s0 + 0.10, s1 - 0.06, c0 + 0.03, c1 - 0.03, 1.20, 1.212, "steel")      # upper tray
        for t in (c0, c1 - 0.03):
            for s in (s0 + 0.04, s1 - 0.07):
                _bx(out, s, s + 0.03, t, t + 0.03, 0.985, h, "alu20")
        for c, L, n in (((s0 + 0.05, (c0 + c1) / 2), c1 - c0, (-1.0, 0.0)), (((s0 + s1) / 2, c0 + 0.012), s1 - s0 - 0.10, (0.0, -1.0)),
                        (((s0 + s1) / 2, c1 - 0.012), s1 - s0 - 0.10, (0.0, 1.0))):
            for nn in (n, (-n[0], -n[1])):
                _quad(out, c, L, 0.985, h, nn, "glass", (0.0, 0.0, 1.0, 1.0), 0.0)
    _bx(out, 7.00, 7.05, 1.57, 1.93, 0.15, 1.00, "alu20")                                    # staff gate
    s0, s1, t0, t1 = COFFEE
    _bx(out, s0 + 0.03, s1, t0 + 0.03, t1, F0, 0.10, "dark20")
    _bx(out, s0, s1, t0, t1, 0.10, 0.90, "lam20", 0.003)
    _bx(out, s0 - 0.04, s1, t0 - 0.03, t1, 0.90, 0.94, "top20", 0.006)
    _bx(out, 9.30, 9.92, 2.00, 6.00, F0, 0.86, "steel"); _bx(out, 9.28, 9.92, 1.98, 6.02, 0.86, 0.90, "steel")   # staff bench


def hall_faces():
    out = list(K21.kept_faces())
    for a, b, n in K21.WALLS[:3]:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        _quad(out, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), L, 1.95, 2.20, n, "teal20", (0.0, 0.0, L / 1.5, 0.17), 0.006)
    # cooler wall
    b0, b1 = XW, FRIDGE_S[-1] + 0.79
    _bx(out, b0, b1, FRIDGE_FRONT + 0.02, YN, 2.285, 2.92, "white20")
    _bx(out, b0, b1, FRIDGE_FRONT, YN, 2.265, 2.285, "alu20")
    for s, key in zip(FRIDGE_S, HEAD):
        _sign(out, key, (s, FRIDGE_FRONT + 0.02), 1.50, 2.33, 2.83, (0.0, -1.0))
    _bx(out, b1, b1 + 0.03, FRIDGE_FRONT, YN, F0, 2.285, "white20")
    _kiosk(out)
    _service(out)
    _sign(out, "coffee", (7.45, YN), 0.90, 1.55, 1.85, (0.0, -1.0), "signs20")
    _sign(out, "atm", (XW, 2.98), 0.75, 1.62, 1.87, (1.0, 0.0))
    s0, s1, t0, t1, h, m = K21.BLOCKS["ledge"]
    _bx(out, s0, s1, t0, t1, 1.00, 1.04, "top20", 0.006)
    for t in (t0 + 0.2, (t0 + t1) / 2, t1 - 0.2):
        _bx(out, s0, s0 + 0.30, t - 0.02, t + 0.02, 0.96, 1.00, "alu20"); _bx(out, s0, s0 + 0.04, t - 0.02, t + 0.02, 0.62, 1.00, "alu20")
    return [f for f in out if f]


def vanilla_props():
    out = [e for e in K21._vp_193() if not K21._in_hall(e[1], e[2]) or (e[0] in K21._KEEP_PROPS and e[3] > 1.0)]
    N, S_ = (0.0, -1.0), (0.0, 1.0)
    out += [B9._against("v_ret_ml_fridge", (s, YN), N) for s in FRIDGE_S]
    for (g, cs), flip in ((ISLAND, 0), (ROW2, 1)):
        for i, s in enumerate(cs):
            if (i + flip) % 2 == 0:
                out += [("v_ret_247shelves02" if i else "v_ret_247shelves01", s, g + 0.01, F0, -90.0), ("v_ret_247shelves03", s, g - 0.182, F0, 0.0)]
            else:
                out += [("v_ret_247shelves01", s, g - 0.01, F0, 90.0), ("v_ret_247shelves05", s, g + 0.18, F0, 90.0)]
    for z in (F0 + 0.14, F0 + 0.46, F0 + 0.78):                         # island end: beer cases; row 2 end: boxes + produce
        out += [("prop_cs_beer_box", 4.42, ISLAND[0] - 0.19, z, 90.0), ("prop_cs_beer_box", 4.42, ISLAND[0] + 0.19, z, 90.0)]
    out += [("prop_fruit_basket", 5.45, 1.95, F0 + 0.28, 0.0), ("v_ret_gc_box2", 5.40, 2.45, F0, 15.0), ("v_ret_gc_box2", 0.72, 1.80, F0, -10.0), ("v_ret_gc_box2", 0.72, 2.10, F0, 8.0)]
    out.append(("prop_atm_01", XW + 0.30, 2.98, F0, 90.0))
    out += [("prop_bar_stool_01", s, t, F0, 0.0) for s, t in K21.STOOLS]
    out += [B9._against("prop_bar_cooler_01", (2.05, YS), S_), B9._against("prop_bar_cooler_03", (4.30, YS), S_), B9._against("prop_news_disp_02a_s", (5.90, YS), S_)]
    for z in (F0 + 0.14, F0 + 0.46):
        out += [("prop_cs_beer_box", 3.05, YS + 0.30, z, 0.0), ("prop_cs_beer_box", 3.05, YS + 0.66, z, 0.0)]
    # kiosk: till, register, candy on the ledge and on the front shelves, stock on the back shelves
    out += [("prop_till_01", 7.30, 0.25, 1.02, 90.0), ("v_ret_gc_cashreg", 7.32, -0.60, 1.02, 90.0)]
    for k, t in enumerate((-1.0, -0.85, -0.45, -0.2, 0.55, 0.8)):
        out.append((("prop_choc_ego", "prop_choc_meto", "prop_candy_pqs", "ng_proc_candy01a")[k % 4], 6.88, t, 1.02, 90.0))
    for z in (0.32, 0.58):
        for k, t in enumerate((-0.95, -0.70, -0.45, -0.20, 0.05, 0.30, 0.55, 0.78)):
            out.append((("prop_choc_ego", "prop_candy_pqs", "prop_choc_meto", "prop_ld_snack_01", "prop_choc_pq")[(k + int(z * 10)) % 5], 6.89, t, z, 90.0))
    for z in (1.14, 1.40, 1.66, 1.92):
        for k, s in enumerate((7.45, 7.75, 8.05, 8.35, 8.65, 8.95, 9.25, 9.50)):
            out.append((("v_ret_247_ketchup2", "prop_cigar_pack_01", "v_ret_ps_cologne", "prop_cigar_pack_02", "v_ret_247_swtcorn2", "v_ret_ps_toiletry_02")[(k + int(z * 4)) % 6], s, YS + 0.11, z, 0.0))
        for k, t in enumerate((0.30, 0.55, 0.80, 1.05, 1.30)):
            out.append((("prop_cigar_pack_02", "v_ret_ps_cologne_01", "prop_cigar_pack_01", "v_ret_247_ketchup2")[(k + int(z * 4)) % 4], XE - 0.11, t, z, -90.0))
    # hot case, deli case, counter
    for k, t in enumerate((2.45, 2.70, 2.95, 3.20, 3.45)):
        out.append((("prop_cs_hotdog_01", "prop_cs_burger_01", "prop_cs_hotdog_02", "prop_taco_01")[k % 4], 7.32, t, 0.985, 90.0))
        out.append((("prop_donut_01", "prop_donut_02", "prop_donut_02b")[k % 3], 7.38, t, 1.212, 0.0))
    for k, t in enumerate((4.30, 4.55, 4.80, 4.98)):
        out.append((("ng_proc_food_burg02a", "prop_cs_burger_01", "ng_proc_food_burg02c", "prop_taco_02")[k], 7.34, t, 0.985, 0.0))
    out += [("prop_bar_napkindisp", 7.30, 2.08, 0.94, 90.0), ("prop_food_ketchup", 7.25, 3.88, 0.94, 0.0), ("prop_food_mustard", 7.36, 3.92, 0.94, 0.0),
            ("prop_food_tray_01", 7.35, 5.28, 0.94, 0.0)]
    out += [("prop_coffee_mac_02", 7.62, 6.10, 0.94, -90.0), ("prop_coffee_mac_02", 7.62, 6.50, 0.94, -90.0), ("prop_food_sugarjar", 7.20, 5.92, 0.94, 0.0),
            ("prop_food_bs_cups01", 7.22, 6.30, 0.94, 0.0), ("prop_cs_paper_cup", 7.20, 6.62, 0.94, 0.0), ("prop_bar_napkindisp", 7.24, 6.78, 0.94, 90.0),
            ("prop_micro_01", 9.62, 2.50, 0.90, -90.0)]
    return out


def collision_boxes():
    out = [b for b in K21._cb_193() if not K21._in_hall((b[0][0] + b[0][1]) / 2, (b[0][2] + b[0][3]) / 2)]
    M = "WOOD_SOLID_MEDIUM"
    out.append(((XW, FRIDGE_S[-1] + 0.82, FRIDGE_FRONT, YN, F0, 2.92), M))
    for g, cs in (ISLAND, ROW2):
        out.append(((cs[0] - 1.05, cs[-1] + 1.05, g - 0.37, g + 0.42, F0, 1.60), M))
    out += [((4.15, 4.80, 3.85, 4.45, F0, 1.0), M), ((6.72, 7.62, YS, 1.00, F0, 1.02), M), ((7.00, 7.06, YS, 1.00, 1.40, 2.28), M),
            ((7.00, 7.06, YS, -0.28, 1.02, 1.40), M), ((7.00, 7.06, 0.32, 1.00, 1.02, 1.40), M),
            ((7.00, XE, 0.95, 1.81, F0, 1.02), M), ((7.55, XE, 1.49, 1.55, 1.02, 2.28), M), ((7.05, 7.60, 1.00, 1.50, 1.02, 2.28), M),
            ((6.96, 7.73, 1.93, 5.47, F0, 0.94), M), ((7.04, 7.66, HOTCASE[0], HOTCASE[1], 0.94, 1.48), M), ((7.04, 7.66, DELICASE[0], DELICASE[1], 0.94, 1.36), M),
            ((6.96, 7.90, 5.72, 6.90, F0, 0.94), M), ((9.28, 9.92, 1.98, 6.02, F0, 0.90), M), ((7.00, 7.05, 1.57, 1.93, F0, 1.00), M),
            ((XW, XW + 0.60, 2.70, 3.26, F0, 1.65), M), ((XW, XW + 0.38, 3.70, 5.50, 0.96, 1.04), M), ((1.55, 5.10, YS, YS + 0.70, F0, 0.93), M),
            ((5.55, 6.35, YS, YS + 0.55, F0, 1.25), M)]
    return out


_used = {f["mat"] for f in hall_faces()}
for _i in range(len(SHADER_SPECS)):
    if _i not in _used and not SHADER_SPECS[_i][3].startswith("lp20_unused"):
        SHADER_SPECS[_i] = ("default.sps", {"DiffuseSampler": "lp20_panel_off"}, {}, "lp20_unused_%d" % _i)
for _n in ("hall_faces", "vanilla_props", "collision_boxes"):
    setattr(K30, _n, globals()[_n]); setattr(K21, _n, globals()[_n])
K30.SHELL_TEX, K30.SHELL_EXTRA_SPECS = SHELL_TEX, SHELL_EXTRA_SPECS
