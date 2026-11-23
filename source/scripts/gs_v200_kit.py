# LONG PIG 2.0.0 - FULL REWORK (owner brief LONG_PIG_GTA6_STYLE_FULL_REWORK, 2026-11-21): the 90s deli becomes a 2000s-2010s
# convenience store. Build 1 = the public hall: clean shell (light tile floor, warm grey paint, teal stripe, clean drop
# ceiling with LED panels), wall of coolers with lit headers, two long gondola rows, cashier booth behind security glass,
# hot-food + coffee counters, ATM, window eating ledge, own sign atlas. Back of house is kept from 1.9.3 (build 3).
# Vanilla props by archetype name only; textures = CC0 (ambientCG) + own (source/textures/v200).
import json, math
from pathlib import Path
import gs_v030_kit as K30
from gs_v030_kit import *                    # noqa: F401,F403

VERSION = "2.0.0"
V, B9, PG, SG = K30.V, K30.B9, K30._PG, K30._SG
W = V.WORLD
F0 = PG.FLOOR                                # 0.015
CEIL = PG.CEIL                               # 3.40
XW, YS, XE, YN = -2.9, -1.23, 9.94, 6.94     # hall: west / south / east (P1) / north (P2) wall faces
DAY = sum(1 << h for h in range(7, 20)); NIGHT = 0xFFFFFF & ~DAY; ALL = 0xFFFFFF
REG = json.loads((Path(__file__).resolve().parents[1] / "textures" / "v200" / "lp20_signs_regions.json").read_text())

# ------------------------------------------------------------------ shell: clean base, new surfaces
SHELL_TEX = dict(K30.SHELL_TEX)
SHELL_TEX["floor"] = ("lp20_floor", "lp20_floor_n", "lp20_floor_s", 60.0, 0.8)
SHELL_TEX["wall"] = ("lp20_wall", "lp20_wall_n", "lp20_wall_s", 10.0, 0.25)
SHELL_TEX["tile"] = ("lp20_wall", "lp20_wall_n", "lp20_wall_s", 10.0, 0.25)
SHELL_TEX["ceil"] = ("lp20_ceil", "lp3_ceiling_tile_n", "lp_ceiling_tile_s", 6.0, 0.3)
SHELL_EXTRA_SPECS = []
_FK = 4.0 / 2.56                             # shell floor UV = metres / 4 -> one repeat of lp20_floor = 2.56 m (8 tiles of 32 cm)
PG.shell_faces = lambda *a, **k: K30._uvmul(K30._shell_faces_030(*a, **k), 0, _FK, _FK)
SG.partition_faces = SG._partition_faces_static

# ------------------------------------------------------------------ materials of the hall drawable
def _ns(tex, inten, fall, bump=1.0):
    return ("normal_spec.sps", {"DiffuseSampler": tex, "BumpSampler": tex + "_n", "SpecSampler": tex + "_s"},
            {"specularIntensityMult": inten, "specularFalloffMult": fall, "specularFresnel": 0.97, "bumpiness": bump}, tex)


for _k, _sp, _rep in (("wall20", _ns("lp20_wall", 0.25, 10.0), 2.0), ("teal20", _ns("lp20_teal", 0.3, 14.0), 1.5), ("dark20", _ns("lp20_dark", 0.3, 14.0), 1.5),
                      ("lam20", _ns("lp20_lam", 0.4, 30.0), 1.0), ("top20", _ns("lp20_top", 0.6, 50.0), 0.8), ("white20", _ns("lp20_white", 0.45, 36.0), 1.0),
                      ("alu20", _ns("lp20_alu", 0.9, 80.0), 0.6),
                      ("signs20", ("default.sps", {"DiffuseSampler": "lp20_signs"}, {}, "lp20_signs"), 1.0),
                      ("signs20e", ("emissive.sps", {"DiffuseSampler": "lp20_signs"}, {"emissiveMultiplier": 1.25}, "lp20_signs_e"), 1.0)):
    MAT[_k] = len(SHADER_SPECS)
    SHADER_SPECS.append(_sp)
    V.REP[_k] = _rep

WALLS = (((XE, YS), (0.58, YS), (0.0, 1.0)), ((0.58, YS), (XW, 2.5), (0.731, 0.682)), ((XW, 2.5), (XW, YN), (1.0, 0.0)),
         ((XW, YN), (XE, YN), (0.0, -1.0)), ((XE, YN), (XE, YS), (-1.0, 0.0)))
STRIPE_Z = (2.64, 2.88)
# layout (s0, s1, t0, t1)
FRIDGE_S = (-2.10, -0.57, 0.96, 2.49, 4.02, 5.55)       # six v_ret_ml_fridge (1.52 m) on the north wall
FRIDGE_FRONT = YN - 0.70
HEAD = ("ice_cold", "cold_beer", "drinks", "water", "dairy", "deals_cold")
ROWS_T = (2.50, 4.60)                                    # gondola row axes
ROW_S = (1.50, 3.59, 5.68)                               # unit centres (2.08 m units)
BOOTH = (8.30, XE, YS, 2.60)                             # cashier booth (counter face s = 8.30, return at t = 2.60)
HOT = (9.24, XE, 3.05, 5.70)                             # hot-food counter on the east wall
COFFEE = (6.45, 8.15, 6.29, YN)                          # coffee counter on the north wall (the staff door s 8.3-9.47 stays free)
PANELS = [(s, t) for s in (-1.25, 1.33, 3.90, 6.48, 8.73) for t in (0.38, 2.95, 5.53)]   # LED panels 0.62 x 1.24 m


def _bx(out, s0, s1, t0, t1, z0, z1, mat, ch=0.0, skip=()):
    out += V.cbox(W, s0, s1, t0, t1, z0, z1, mat, ch=ch, skip=skip)


def _quad(out, c, w, z0, z1, n, mat, uv, off=0.004):
    r = (-n[1], n[0])                                    # viewer's right
    a = (c[0] - r[0] * w / 2 + n[0] * off, c[1] - r[1] * w / 2 + n[1] * off)
    b = (c[0] + r[0] * w / 2 + n[0] * off, c[1] + r[1] * w / 2 + n[1] * off)
    u0, v0, u1, v1 = uv
    V.emit(out, V.F([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], mat, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)],
                    hint=(n[0], n[1], 0.0)))


def _sign(out, key, c, w, z0, z1, n, mat="signs20e", off=0.004):
    x0, y0, x1, y1 = REG[key]
    _quad(out, c, w, z0, z1, n, mat, (x0 / 2048.0, 1 - y1 / 1024.0, x1 / 2048.0, 1 - y0 / 1024.0), off)


def _glass(out, c, w, z0, z1, n):
    _quad(out, c, w, z0, z1, n, "glass", (0.0, 0.0, 1.0, 1.0), 0.0)
    _quad(out, c, w, z0, z1, (-n[0], -n[1]), "glass", (0.0, 0.0, 1.0, 1.0), 0.0)


def _counter(out, s0, s1, t0, t1, top=0.92, kick="dark20", over=0.03):
    _bx(out, s0, s1, t0, t1, F0, F0 + 0.10, kick)
    _bx(out, s0, s1, t0, t1, F0 + 0.10, top, "lam20", ch=0.003)
    _bx(out, s0 - over, s1 + over, t0 - over, t1 + over, top, top + 0.04, "top20", ch=0.006)


def hall_faces():
    out = []
    # teal stripe + skirting on the walls
    for a, b, n in WALLS:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        _quad(out, c, L, STRIPE_Z[0], STRIPE_Z[1], n, "teal20", (0.0, 0.0, L / 1.5, 0.16), 0.006)
        _quad(out, c, L, STRIPE_Z[0] - 0.035, STRIPE_Z[0], n, "dark20", (0.0, 0.0, L / 1.5, 0.03), 0.006)
    for (s0, s1, t0, t1) in ((0.6, 6.4, YS, YS + 0.012), (XW, XW + 0.012, 3.3, FRIDGE_FRONT)):
        _bx(out, s0, s1, t0, t1, F0, F0 + 0.11, "dark20")
    # ---- coolers: bulkhead with lit headers over six fridges
    b0, b1 = XW, FRIDGE_S[-1] + 0.79
    _bx(out, b0, b1, FRIDGE_FRONT + 0.02, YN, 2.285, CEIL, "wall20", skip=("+y", "+z"))
    _bx(out, b0, b1, FRIDGE_FRONT, YN, 2.265, 2.285, "alu20")
    for s, key in zip(FRIDGE_S, HEAD):
        _sign(out, key, (s, FRIDGE_FRONT + 0.02), 1.50, 2.33, 2.83, (0.0, -1.0))
    _quad(out, ((b0 + b1) / 2, FRIDGE_FRONT + 0.02), b1 - b0, 2.93, 3.13, (0.0, -1.0), "teal20", (0.0, 0.0, (b1 - b0) / 1.5, 0.13))
    _bx(out, b1, b1 + 0.03, FRIDGE_FRONT, YN, F0, 2.285, "white20")                       # end panel of the cooler run
    # ---- cashier booth: counter, security glass in aluminium frames, bulkhead
    s0, s1, t0, t1 = BOOTH
    _counter(out, s0, s0 + 0.65, t0, t1, top=1.02, over=0.06)
    _counter(out, s0 + 0.65, s1, t1 - 0.30, t1, top=1.02, over=0.0)
    for (a, b, n, c) in (((s0 + 0.04, t0), (s0 + 0.04, t1), (-1.0, 0.0), None), ((s0 + 0.04, t1 - 0.04), (s1, t1 - 0.04), (0.0, 1.0), None)):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        _glass(out, c, L, 1.24, 2.30, n)
        d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        for z0, z1 in ((1.20, 1.24), (2.30, 2.36)):                                         # rails
            _bx(out, min(a[0], b[0]) - 0.025, max(a[0], b[0]) + 0.025, min(a[1], b[1]) - 0.025, max(a[1], b[1]) + 0.025, z0, z1, "alu20")
        k = max(2, int(round(L / 1.28)))
        for i in range(k + 1):                                                              # posts
            p = (a[0] + d[0] * L * i / k, a[1] + d[1] * L * i / k)
            _bx(out, p[0] - 0.025, p[0] + 0.025, p[1] - 0.025, p[1] + 0.025, 1.06, 2.30, "alu20")
    _bx(out, s0, s0 + 0.10, t0, t1, 2.36, CEIL, "wall20", skip=("+z",))                    # bulkhead over the glass
    _bx(out, s0 + 0.10, s1, t1 - 0.10, t1, 2.36, CEIL, "wall20", skip=("+z",))
    _sign(out, "cashier", (s0, 0.70), 1.60, 2.52, 2.92, (-1.0, 0.0))
    _quad(out, (s0, (t0 + t1) / 2), t1 - t0, 3.02, 3.20, (-1.0, 0.0), "teal20", (0.0, 0.0, (t1 - t0) / 1.5, 0.12))
    _sign(out, "p_noid", (s0 + 0.04, 0.05), 0.30, 1.52, 1.82, (-1.0, 0.0), "signs20", 0.006)
    _sign(out, "p_lotto", (s0 + 0.04, 2.05), 0.30, 1.52, 1.82, (-1.0, 0.0), "signs20", 0.006)
    _sign(out, "p_smile", (s0 + 0.65, t1), 0.34, 1.52, 1.86, (0.0, 1.0), "signs20", 0.03)
    _bx(out, XE - 0.30, XE - 0.02, 0.60, 2.20, 1.25, 1.29, "white20")                     # cigarette shelves on the back wall
    _bx(out, XE - 0.30, XE - 0.02, 0.60, 2.20, 1.62, 1.66, "white20")
    _bx(out, XE - 0.30, XE - 0.02, 0.60, 2.20, 1.99, 2.03, "white20")
    # ---- hot food counter + heated display case
    s0, s1, t0, t1 = HOT
    _counter(out, s0, s1, t0, t1)
    c0, c1 = 3.35, 4.95
    _bx(out, s0 + 0.05, s1 - 0.04, c0, c1, 0.96, 1.00, "steel")
    _bx(out, s0 + 0.05, s1 - 0.04, c0, c1, 1.26, 1.275, "steel")                           # upper tray
    _bx(out, s0 + 0.05, s1 - 0.04, c0, c1, 1.54, 1.58, "steel")                            # lid
    for t in (c0, c1 - 0.03):
        _bx(out, s0 + 0.05, s0 + 0.08, t, t + 0.03, 1.00, 1.54, "steel")
        _bx(out, s1 - 0.07, s1 - 0.04, t, t + 0.03, 1.00, 1.54, "steel")
    _glass(out, (s0 + 0.06, (c0 + c1) / 2), c1 - c0, 1.00, 1.54, (-1.0, 0.0))
    _glass(out, ((s0 + s1) / 2, c0 + 0.01), s1 - s0 - 0.12, 1.00, 1.54, (0.0, -1.0))
    _glass(out, ((s0 + s1) / 2, c1 - 0.01), s1 - s0 - 0.12, 1.00, 1.54, (0.0, 1.0))
    _sign(out, "hot_food", (XE, 4.15), 1.20, 1.92, 2.32, (-1.0, 0.0))
    # ---- coffee counter
    s0, s1, t0, t1 = COFFEE
    _counter(out, s0, s1, t0, t1)
    _bx(out, s0, s1, YN - 0.24, YN - 0.01, 1.42, 1.46, "white20")                          # cup shelf
    _sign(out, "coffee", (7.30, YN), 1.20, 1.90, 2.30, (0.0, -1.0))
    # ---- ATM sign, posters, welcome plate, hanging deals banner
    _sign(out, "atm", (XW, 2.98), 0.75, 1.86, 2.11, (1.0, 0.0))
    _sign(out, "welcome", (3.45, YS), 3.20, 2.94, 3.34, (0.0, 1.0), "signs20")
    _sign(out, "p_2for1", (7.45, YS), 0.42, 1.48, 1.90, (0.0, 1.0), "signs20")
    for n in ((-1.0, 0.0), (1.0, 0.0)):
        _sign(out, "deals", (2.40, 3.55), 1.28, 2.56, 3.20, n, "signs20", 0.003)
    for t in (3.0, 4.1):
        _bx(out, 2.397, 2.403, t - 0.003, t + 0.003, 3.20, CEIL, "alu20")
    _sign(out, "staff", (8.885, YN), 0.80, 2.42, 2.62, (0.0, -1.0), "signs20")           # over the staff door
    return [f for f in out if f]


# ------------------------------------------------------------------ vanilla props
_KEEP = ("v_ilev_fib_sprklr", "v_res_fa_smokealarm", "v_res_tre_plugsocket", "v_serv_switch_2", "prop_fire_exting_1a")
_vp_193 = K30.vanilla_props
_RS = json.loads((Path(__file__).resolve().parents[2] / "docs" / "_raw" / "retail_scan.json").read_text())["items"]


for _n, _v in _RS.items():                   # bounds of the retail props scanned read-only from the game (gs_53)
    if _n not in VB:
        VB[_n] = (tuple(_v["min"]), tuple(_v["max"]))


def _in_hall(s, t):
    return s < XE - 0.02 and t < YN - 0.02


def _row(out, names, c, t, z, yaw, step):
    for i, nm in enumerate(names):
        out.append((nm, c[0] + step[0] * (i - (len(names) - 1) / 2.0), c[1] + step[1] * (i - (len(names) - 1) / 2.0), z, yaw))


def vanilla_props():
    out = [e for e in _vp_193() if not _in_hall(e[1], e[2]) or (e[0] in _KEEP and e[3] > 1.0)]
    N, S_, E_, W_ = (0.0, -1.0), (0.0, 1.0), (-1.0, 0.0), (1.0, 0.0)
    out += [B9._against("v_ret_ml_fridge", (s, YN), N) for s in FRIDGE_S]
    for g, sg in zip(ROWS_T, (1, -1)):                                  # gondolas: stocked 24/7 units back to back
        for i, s in enumerate(ROW_S):
            if (i + (sg < 0)) % 2 == 0:
                out += [("v_ret_247shelves02" if i != 1 else "v_ret_247shelves01", s, g + 0.01, F0, -90.0), ("v_ret_247shelves03", s, g - 0.182, F0, 0.0)]
            else:
                out += [("v_ret_247shelves01", s, g - 0.01, F0, 90.0), ("v_ret_247shelves03", s, g + 0.182, F0, 180.0)]
    out.append(("prop_atm_01", XW + 0.30, 2.98, F0, 90.0))
    # cashier booth
    out += [("prop_till_01", 8.62, 1.20, 1.06, 90.0), ("v_ret_gc_cashreg", 8.62, -0.30, 1.06, 90.0),
            ("prop_choc_ego", 8.28, 0.70, 1.06, 90.0), ("prop_choc_meto", 8.28, 0.80, 1.06, 90.0), ("prop_candy_pqs", 8.28, 0.92, 1.06, 0.0),
            ("prop_choc_ego", 8.28, 1.60, 1.06, 90.0), ("prop_candy_pqs", 8.28, 1.72, 1.06, 0.0), ("prop_choc_meto", 8.28, 1.84, 1.06, 90.0)]
    for z in (1.29, 1.66, 2.03):                                        # stock on the back shelves of the booth
        for k, t in enumerate((0.75, 1.05, 1.35, 1.65, 1.95)):
            out.append((("v_ret_247_ketchup2", "prop_cigar_pack_01", "v_ret_ps_cologne", "prop_cigar_pack_02", "v_ret_247_swtcorn2")[(k + int(z * 3)) % 5], XE - 0.16, t, z, -90.0))
    # hot food: trays in the case, sauces, microwave
    for k, t in enumerate((3.50, 3.72, 3.94, 4.16, 4.38, 4.60, 4.80)):
        out.append((("prop_cs_hotdog_01", "prop_cs_burger_01", "prop_cs_hotdog_02", "prop_taco_01")[k % 4], 9.50, t, 1.00, 90.0))
        out.append((("prop_donut_01", "prop_donut_02", "prop_donut_02b")[k % 3], 9.52, t, 1.275, 0.0))
        out.append((("prop_donut_02", "prop_donut_01")[k % 2], 9.72, t + 0.05, 1.275, 30.0))
    out += [("prop_micro_01", 9.62, 5.25, 0.96, -90.0), ("prop_food_ketchup", 9.40, 5.05, 0.96, 0.0), ("prop_food_mustard", 9.40, 5.15, 0.96, 0.0),
            ("prop_bar_napkindisp", 9.42, 5.55, 0.96, 90.0), ("prop_food_tray_01", 9.55, 3.17, 0.96, 0.0)]
    # coffee
    out += [("prop_coffee_mac_02", 6.75, YN - 0.24, 0.96, 0.0), ("prop_coffee_mac_02", 7.12, YN - 0.24, 0.96, 0.0),
            ("prop_juice_dispenser", 7.80, YN - 0.33, 0.96, 0.0), ("prop_food_sugarjar", 7.42, YN - 0.44, 0.96, 0.0), ("prop_bar_napkindisp", 7.52, YN - 0.30, 0.96, 0.0)]
    for k, s in enumerate((6.60, 6.90, 7.25, 7.55, 7.90)):
        out.append((("prop_food_bs_cups01", "prop_cs_paper_cup")[k % 2], s, YN - 0.13, 1.46, 0.0))
    # no seating (owner): chest coolers and stock under the shop window, soda fridge, news rack, bin
    out += [B9._against("prop_bar_cooler_01", (2.05, YS), S_), B9._against("prop_bar_cooler_03", (4.30, YS), S_),
            B9._against("prop_vend_fridge01", (6.45, YS), S_), B9._against("prop_news_disp_02a_s", (7.35, YS), S_), ("prop_bin_07a", 7.95, YS + 0.30, F0, 0.0)]
    for z in (F0 + 0.14, F0 + 0.46):
        out += [("prop_cs_beer_box", 3.05, YS + 0.30, z, 0.0), ("prop_cs_beer_box", 3.05, YS + 0.66, z, 0.0)]
    # floor stock at the row ends
    for z in (F0 + 0.14, F0 + 0.46, F0 + 0.78):
        out += [("prop_cs_beer_box", 0.05, 4.45, z, 90.0), ("prop_cs_beer_box", 0.05, 4.82, z, 90.0)]
    for g in ROWS_T:                                                    # east row ends: beer cases, promo stacks
        for z in (F0 + 0.14, F0 + 0.46, F0 + 0.78):
            out += [("prop_cs_beer_box", 6.92, g - 0.19, z, 90.0), ("prop_cs_beer_box", 6.92, g + 0.19, z, 90.0)]
        out += [("v_ret_247_popcan2", 6.95, g - 0.15, F0 + 1.10, 0.0), ("v_ret_247_tomsoup1", 6.95, g + 0.16, F0 + 1.10, 15.0)]
    for k, s in enumerate((1.75, 2.05, 2.35, 3.75, 4.05, 4.35, 4.65, 4.95)):   # on the chest coolers under the window
        out.append((("v_ret_247_popcan2", "v_ret_247_noodle1", "v_ret_247_tuna", "v_ret_247_vegsoup1")[k % 4], s, YS + 0.36, 0.95, (k * 37) % 90))
    for k, s in enumerate((1.9, 2.2, 3.9, 4.3, 4.8)):
        out.append((("prop_ecola_can", "prop_orang_can_01", "prop_ld_can_01", "prop_energy_drink", "ng_proc_sodabot_01a")[k], s, YS + 0.62, 0.95, 0.0))
    for k, t in enumerate((-0.9, -0.6, 2.25)):                          # booth counter: lighters / snacks by the till
        out.append((("prop_ld_snack_01", "prop_cs_crisps_01", "ng_proc_candy01a")[k], 8.60, t, 1.06, 90.0))
    out += [("v_ret_gc_box2", 0.10, 2.35, F0, 10.0), ("v_ret_gc_box2", 0.10, 2.66, F0, -8.0), ("v_ret_gc_box2", 0.10, 2.50, F0 + 0.27, 20.0)]
    return out




# ------------------------------------------------------------------ light panels (entity sets) and lights
def open_specs():
    return [("emissive.sps", {"DiffuseSampler": "lp20_panel"}, {"emissiveMultiplier": 2.6}, "lp20_panel")]


def closed_specs():
    return [("default.sps", {"DiffuseSampler": "lp20_panel_off"}, {}, "lp20_panel_off")]


def _panel_faces():
    out = []
    for s, t in PANELS:
        V.emit(out, V.F([(s - 0.31, t - 0.62, CEIL - 0.006), (s - 0.31, t + 0.62, CEIL - 0.006), (s + 0.31, t + 0.62, CEIL - 0.006), (s + 0.31, t - 0.62, CEIL - 0.006)],
                        0, [(0.0, 0.0), (0.0, 2.0), (1.0, 2.0), (1.0, 0.0)], hint=(0.0, 0.0, -1.0)))
    return [f for f in out if f]


open_faces = _panel_faces
closed_faces = _panel_faces
WHITE = (1.0, 0.975, 0.93)
_SHADOW = {(1.33, 0.38), (3.90, 2.95), (6.48, 5.53), (-1.25, 2.95), (8.73, 0.38), (6.48, 0.38)}


def _dn(L, k):
    return [dict(L, time=DAY), dict(L, kind=L["kind"] + "_n", intensity=round(L["intensity"] * k, 3), time=NIGHT)]


def _cool_lights():
    out = []
    for s in FRIDGE_S:                                                  # cooler glow, always on
        out.append(dict(K30.LT("cooler", "POINT", (s, FRIDGE_FRONT - 0.35, 1.45), (0.86, 0.94, 1.0), 0.9, 2.0, 4.0,
                               flags=("no_specular", "not_in_reflection", "dont_light_alpha")), time=ALL))
    out.append(dict(K30.LT("hot_case", "POINT", (9.55, 4.15, 1.45), (1.0, 0.72, 0.42), 1.2, 1.3, 4.0, flags=("not_in_reflection", "dont_light_alpha")), time=ALL))
    out.append(dict(K30.LT("atm_glow", "POINT", (XW + 0.55, 2.98, 1.35), (0.7, 0.82, 1.0), 0.5, 1.4, 4.0, flags=("no_specular", "not_in_reflection")), time=ALL))
    return out


def open_lights():
    out = []
    for s, t in PANELS:
        sh = (s, t) in _SHADOW
        fl = (("static_shadows", "dynamic_shadows") if sh else ()) + ("not_in_reflection",) + (() if sh else ("no_specular",))
        out += _dn(K30.LT("panel", "SPOT", (s, t, CEIL - 0.05), WHITE, 2.6 if sh else 1.7, 6.2, 5.0, cone=(124.0, 60.0), flags=fl), 0.85)
        out.append(dict(K30.LT("panel_halo", "POINT", (s, t, CEIL - 0.12), WHITE, 0.25, 1.5, 4.0, flags=("no_specular", "not_in_reflection", "dont_light_alpha")), time=ALL))
    for s, t in ((1.3, 1.2), (5.2, 1.2), (1.3, 5.6), (5.2, 5.6), (8.9, 4.4)):                 # soft bounce
        out += _dn(K30.LT("bounce", "POINT", (s, t, 2.3), WHITE, 0.32, 5.0, 2.5, flags=("no_specular", "not_in_reflection")), 0.85)
    for s in (1.5, 4.5):                                                # daylight through the shop window
        out.append(dict(K30.LT("window_day_fill", "SPOT", (s, YS + 0.1, 2.42), (1.0, 0.98, 0.95), 0.9, 6.5, 2.0, aim=(0.0, 0.78, -0.62), cone=(80.0, 42.0),
                               flags=("no_specular", "not_in_reflection", "dont_light_alpha")), time=DAY))
    out.append(dict(K30.LT("booth", "SPOT", (9.2, 0.9, 2.3), WHITE, 1.6, 3.0, 4.0, cone=(110.0, 50.0), flags=("not_in_reflection",)), time=ALL))
    return out + _cool_lights()


def closed_lights():
    out = _cool_lights()
    for s, t in ((3.90, 2.95), (8.73, 0.38)):                           # two security panels
        out.append(dict(K30.LT("security", "SPOT", (s, t, CEIL - 0.05), WHITE, 0.9, 6.0, 5.0, cone=(120.0, 60.0), flags=("static_shadows", "dynamic_shadows", "not_in_reflection")), time=ALL))
    return out


def lights():
    return []


# ------------------------------------------------------------------ collision
_cb_193 = K30.collision_boxes


def collision_boxes():
    out = [b for b in _cb_193() if not _in_hall((b[0][0] + b[0][1]) / 2, (b[0][2] + b[0][3]) / 2)]
    M = "WOOD_SOLID_MEDIUM"
    out.append(((XW, FRIDGE_S[-1] + 0.82, FRIDGE_FRONT, YN, F0, CEIL), M))
    for g in ROWS_T:
        out.append(((ROW_S[0] - 1.05, ROW_S[-1] + 1.05, g - 0.37, g + 0.37, F0, 1.60), M))
    s0, s1, t0, t1 = BOOTH
    out += [((s0 - 0.06, s0 + 0.65, t0, t1, F0, 1.06), M), ((s0, s0 + 0.10, t0, t1, 1.20, CEIL), M), ((s0 + 0.65, s1, t1 - 0.30, t1, F0, 1.06), M),
            ((s0, s1, t1 - 0.10, t1, 1.20, CEIL), M)]
    out += [((HOT[0] - 0.03, HOT[1], HOT[2] - 0.03, HOT[3], F0, 1.58), M), ((COFFEE[0] - 0.03, COFFEE[1] + 0.03, COFFEE[2] - 0.03, COFFEE[3], F0, 0.96), M),
            ((XW, XW + 0.60, 2.70, 3.26, F0, 1.65), M), ((-0.15, 0.40, 4.25, 5.0, F0, 1.0), M), ((6.05, 7.8, YS, YS + 0.72, F0, 1.55), M),
            ((1.55, 5.10, YS, YS + 0.70, F0, 0.93), M)]
    return out


SHELL_TEX_N = 11                             # wall and wainscot band share one paint texture now
HALL_MIN_TRIS = 500
_used = {f["mat"] for f in hall_faces()}     # memory: materials the new hall does not use carry one tiny texture
for _i in range(len(SHADER_SPECS)):
    if _i not in _used:
        SHADER_SPECS[_i] = ("default.sps", {"DiffuseSampler": "lp20_panel_off"}, {}, "lp20_unused_%d" % _i)
for _n in ("hall_faces", "vanilla_props", "open_specs", "closed_specs", "open_faces", "closed_faces", "open_lights", "closed_lights", "lights", "collision_boxes"):
    setattr(K30, _n, globals()[_n])
K30.SHELL_TEX, K30.SHELL_EXTRA_SPECS = SHELL_TEX, SHELL_EXTRA_SPECS
