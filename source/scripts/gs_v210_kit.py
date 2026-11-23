# LONG PIG 2.1.0-blockout - South LA mini market x Bronx bodega (owner brief 2026-11-21 + corrections).
# BLOCKOUT ONLY: the approved plan as plain volumes to check sizes, aisles, sight lines and collision in FiveM before any
# detailed modelling, final textures or mass prop dressing.
# PROTECTED (kept from 1.9.3 untouched): shell geometry incl. the drop ceiling, every light (open / closed / boh lights,
# timecycle, night script), troffer lenses, ceiling fans (client), the two overhead menu boards and everything else of the
# old hall above 2.25 m that is a fixture (pendants, cans, soffit). Everything of the old hall below 2.25 m is removed.
import math
import gs_v030_kit as K30
from gs_v030_kit import *                    # noqa: F401,F403

VERSION = "2.1.0-blockout"
V, B9, PG, SG = K30.V, K30.B9, K30._PG, K30._SG
W = V.WORLD
F0, CEIL = PG.FLOOR, PG.CEIL
XW, YS, XE, YN = -2.9, -1.23, 9.94, 6.94
KEEP_Z = 2.25

# temporary blockout surfaces (final worn finishes come after the composition is approved); the ceiling stays as it is
SHELL_TEX = dict(K30.SHELL_TEX)
SHELL_TEX["floor"] = ("lp20_floor", "lp20_floor_n", "lp20_floor_s", 60.0, 0.5)
SHELL_TEX["wall"] = ("lp20_wall", "lp20_wall_n", "lp20_wall_s", 10.0, 0.25)
SHELL_TEX["tile"] = ("lp20_wall", "lp20_wall_n", "lp20_wall_s", 10.0, 0.25)
SHELL_TEX_N = 11
HALL_MIN_TRIS = 500
_shell_193 = PG.shell_faces
PG.shell_faces = lambda *a, **k: K30._uvmul(_shell_193(*a, **k), 0, 0.5, 0.5)     # lp20_floor: 8 tiles per repeat -> 32 cm tiles


def _ns(tex, inten, fall):
    return ("normal_spec.sps", {"DiffuseSampler": tex, "BumpSampler": tex + "_n", "SpecSampler": tex + "_s"},
            {"specularIntensityMult": inten, "specularFalloffMult": fall, "specularFresnel": 0.97, "bumpiness": 1.0}, tex)


for _k, _sp, _rep in (("teal20", _ns("lp20_teal", 0.3, 14.0), 1.5), ("dark20", _ns("lp20_dark", 0.3, 14.0), 1.5), ("lam20", _ns("lp20_lam", 0.4, 30.0), 1.0),
                      ("top20", _ns("lp20_top", 0.6, 50.0), 0.8), ("white20", _ns("lp20_white", 0.45, 36.0), 1.0), ("alu20", _ns("lp20_alu", 0.9, 80.0), 0.6)):
    MAT[_k] = len(SHADER_SPECS)
    SHADER_SPECS.append(_sp)
    V.REP[_k] = _rep

WALLS = (((XE, YS), (0.58, YS), (0.0, 1.0)), ((0.58, YS), (XW, 2.5), (0.731, 0.682)), ((XW, 2.5), (XW, YN), (1.0, 0.0)), ((XW, YN), (6.3, YN), (0.0, -1.0)))
STRIPE_Z = (1.95, 2.20)                      # aged teal band of the reference (below the protected high fixtures)
# ---- approved plan (s0, s1, t0, t1, height, material, collision)
BLOCKS = {
    "cooler_3door": (-2.86, 0.20, 6.24, 6.92, 2.10, "white20"),
    "cooler_soda": (0.30, 1.10, 6.22, 6.92, 1.95, "teal20"),
    "cooler_black": (1.20, 2.20, 6.20, 6.92, 2.05, "top20"),
    "chest_ice": (2.30, 4.40, 6.00, 6.90, 0.90, "white20"),
    "shelf_tall": (4.60, 6.25, 6.50, 6.92, 2.00, "lam20"),
    "island_main": (0.50, 4.90, 3.75, 4.50, 1.55, "lam20"),
    "donut_case": (4.95, 5.50, 3.80, 4.45, 1.30, "alu20"),
    "rack_low": (1.00, 3.60, 1.75, 2.20, 1.20, "alu20"),
    "produce": (3.90, 5.20, 1.55, 2.35, 0.80, "lam20"),
    "crates": (1.50, 3.00, YS + 0.02, YS + 0.50, 0.70, "dark20"),
    "news": (3.30, 4.00, YS + 0.02, YS + 0.50, 1.20, "alu20"),
    "ledge": (XW + 0.02, XW + 0.38, 3.70, 5.50, 1.04, "top20"),
    "cash_front": (7.00, 7.65, -1.20, 1.55, 1.05, "dark20"),
    "cash_return": (7.65, 9.90, 1.25, 1.55, 1.05, "dark20"),
    "cash_wall": (9.55, 9.92, 0.20, 1.20, 2.20, "lam20"),
    "hot_case": (7.00, 7.70, 1.95, 4.20, 0.90, "alu20"),
    "deli_case": (7.00, 7.70, 4.30, 5.50, 0.90, "white20"),
    "coffee": (7.00, 7.90, 5.80, 6.90, 0.92, "lam20"),
    "staff_bench": (9.30, 9.92, 2.00, 6.00, 0.90, "steel"),
    "staff_gate": (7.00, 7.06, 1.55, 1.95, 1.00, "alu20"),
}
STOOLS = [(XW + 0.67, t) for t in (4.0, 4.6, 5.2)]
_KEEP_HIGH_MATS = ("enamel", "steel", "brass", "iron", "glow", "menu", "troffer", "troffer_off", "plaster")
_KEEP_PROPS = ("v_ilev_fib_sprklr", "v_res_fa_smokealarm", "v_res_tre_plugsocket", "v_serv_switch_2", "prop_fire_exting_1a")
_hf_193, _vp_193, _cb_193 = K30.hall_faces, K30.vanilla_props, K30.collision_boxes
_INV = {v: k for k, v in MAT.items()}


def _in_hall(s, t):
    return s < XE - 0.02 and t < YN - 0.02


def _bx(out, s0, s1, t0, t1, z0, z1, mat, ch=0.0):
    out += V.cbox(W, s0, s1, t0, t1, z0, z1, mat, ch=ch)


def _quad(out, c, w, z0, z1, n, mat, uv, off=0.004):
    r = (-n[1], n[0])
    a = (c[0] - r[0] * w / 2 + n[0] * off, c[1] - r[1] * w / 2 + n[1] * off)
    b = (c[0] + r[0] * w / 2 + n[0] * off, c[1] + r[1] * w / 2 + n[1] * off)
    u0, v0, u1, v1 = uv
    V.emit(out, V.F([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], mat, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=(n[0], n[1], 0.0)))


def kept_faces():
    """Protected fixtures of the 1.9.3 hall: everything that hangs at / under the ceiling."""
    out = []
    for f in _hf_193():
        if not f or min(p[2] for p in f["v"]) <= KEEP_Z or _INV.get(f["mat"]) not in _KEEP_HIGH_MATS:
            continue
        cs = sum(p[0] for p in f["v"]) / len(f["v"])
        if _INV[f["mat"]] == "brass" and 7.05 < cs < 7.65 and max(p[2] for p in f["v"]) < 3.36:
            continue                                     # the meat rail over the old deli counter (not a light fixture)
        out.append(f)
    return out


def hall_faces():
    out = list(kept_faces())
    for a, b, n in WALLS:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        _quad(out, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), L, STRIPE_Z[0], STRIPE_Z[1], n, "teal20", (0.0, 0.0, L / 1.5, 0.17), 0.006)
    for k, (s0, s1, t0, t1, h, mat) in BLOCKS.items():
        _bx(out, s0, s1, t0, t1, F0, h, mat, ch=0.004)
    # cashier: glazed security screen as one volume (frame + glass), service opening over the counter
    for (c, L, n) in (((7.04, 0.175), 2.75, (-1.0, 0.0)), ((8.47, 1.51), 2.86, (0.0, 1.0))):
        for nn in (n, (-n[0], -n[1])):
            _quad(out, c, L, 1.25, 2.20, nn, "glass", (0.0, 0.0, 1.0, 1.0), 0.0)
    for z0, z1 in ((1.21, 1.25), (2.20, 2.26)):
        _bx(out, 7.01, 7.07, -1.20, 1.55, z0, z1, "alu20"); _bx(out, 7.04, 9.90, 1.48, 1.54, z0, z1, "alu20")
    for t in (-1.20, -0.28, 0.63, 1.50):
        _bx(out, 7.01, 7.07, t, t + 0.05, 1.05, 2.20, "alu20")
    for s in (7.99, 8.94, 9.85):
        _bx(out, s, s + 0.05, 1.48, 1.54, 1.05, 2.20, "alu20")
    # hot / deli display cases as glazed volumes on their counters (two different proportions)
    for (t0, t1, h) in ((2.10, 4.05, 1.42), (4.40, 5.40, 1.30)):
        _bx(out, 7.03, 7.67, t0, t1, h, h + 0.04, "alu20")
        for c, L, n in (((7.04, (t0 + t1) / 2), t1 - t0, (-1.0, 0.0)), ((7.35, t0), 0.62, (0.0, -1.0)), ((7.35, t1), 0.62, (0.0, 1.0))):
            _quad(out, c, L, 0.90, h, n, "glass", (0.0, 0.0, 1.0, 1.0), 0.0)
            _quad(out, c, L, 0.90, h, (-n[0], -n[1]), "glass", (0.0, 0.0, 1.0, 1.0), 0.0)
    return [f for f in out if f]


def vanilla_props():
    out = [e for e in _vp_193() if not _in_hall(e[1], e[2]) or (e[0] in _KEEP_PROPS and e[3] > 1.0)]
    out.append(("prop_atm_01", XW + 0.30, 2.98, F0, 90.0))
    out += [("prop_bar_stool_01", s, t, F0, 0.0) for s, t in STOOLS]
    return out


def collision_boxes():
    out = [b for b in _cb_193() if not _in_hall((b[0][0] + b[0][1]) / 2, (b[0][2] + b[0][3]) / 2)]
    for k, (s0, s1, t0, t1, h, mat) in BLOCKS.items():
        out.append(((s0, s1, t0, t1, F0, h), "WOOD_SOLID_MEDIUM"))
    out += [((7.00, 7.08, -1.20, 1.55, 1.21, 2.26), "WOOD_SOLID_MEDIUM"), ((7.04, 9.90, 1.47, 1.55, 1.21, 2.26), "WOOD_SOLID_MEDIUM"),
            ((7.03, 7.67, 2.10, 4.05, 0.90, 1.46), "WOOD_SOLID_MEDIUM"), ((7.03, 7.67, 4.40, 5.40, 0.90, 1.34), "WOOD_SOLID_MEDIUM"),
            ((XW, XW + 0.60, 2.70, 3.26, F0, 1.65), "WOOD_SOLID_MEDIUM")]
    return out


_used = {f["mat"] for f in hall_faces()}     # memory: materials the blockout does not use carry one tiny texture
for _i in range(len(SHADER_SPECS)):
    if _i not in _used:
        SHADER_SPECS[_i] = ("default.sps", {"DiffuseSampler": "lp20_panel_off"}, {}, "lp20_unused_%d" % _i)
for _n in ("hall_faces", "vanilla_props", "collision_boxes"):
    setattr(K30, _n, globals()[_n])
K30.SHELL_TEX = SHELL_TEX
