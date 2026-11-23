# LONG PIG 2.7.0 - on top of 2.6.0 (owner 2026-11-21 19:48, voice note + 24/7 reference shots):
#   COLOUR   band, dado and window surrounds in the colour of the owner's swatch (sign red-brown 116/70/57); the yellow pin
#            lines are gone (same colour, a shade deeper). Cooler headers keep their colours (revision).
#   WALLS    old plaster lp27_wall (stains, runs, cracks, flaked paint, repaint patches) + 16 stronger local grime decals +
#            posters / notices on the free wall pieces.
#   TOBACCO  back wall behind the counter: old shelves, brackets, knife rack, clock, phone and the hanging rail removed;
#            10 x v_ret_247_cigs in two rows up to the band, 5 own lit header signs above (LONG PIG brands).
#   SNACKS   the candy / snack rack (v_ret_gassweets) moved from the gondola end into a notch cut into the counter end next
#            to the deli case; two of the three stools there removed, one kept.
#   FRONT    24/7 fruit stand (v_ret_247_fruit) at the first gondola end by the entrance, own basket stack beside the
#            gondolas, donut cabinet (v_ret_247_donuts) at the freed gondola end, lottery display + LOTTO sign on the counter.
#   LIGHT    warmer: hall lights shifted warm (+6 %), timecycle ambient warmer / slightly stronger. Owner asked for it.
import json, math
from pathlib import Path
import gs_v260_kit as K26
from gs_v260_kit import *                    # noqa: F401,F403

VERSION = "2.7.0"
K25, K24, K23, K22, K21, K30 = K26.K25, K26.K24, K26.K23, K26.K22, K26.K21, K26.K30
V, B9, PG = K26.V, K26.B9, K26.PG
F0 = PG.FLOOR
XW, YS, XE, YN = K26.XW, K26.YS, K26.XE, K26.YN
_quad, _bx, _sign, _sign2 = K22._quad, K22._bx, K22._sign, K23._sign2
_INV = {v: k for k, v in MAT.items()}
_hf26, _vp26, _cb26, _mk26 = K26.hall_faces, K26.vanilla_props, K26.collision_boxes, K26.market_faces
_ol26, _cl26 = K26.open_lights, K26.closed_lights
ISLAND, ROW2 = K26.ISLAND, K26.ROW2
_S7 = json.loads((Path(__file__).resolve().parents[2] / "docs" / "_raw" / "scan_247b.json").read_text())["items"]
for _n, _v in _S7.items():
    if _n not in VB:
        VB[_n] = (tuple(_v["min"]), tuple(_v["max"]))
HREG = json.loads((Path(__file__).resolve().parents[1] / "textures" / "v270" / "lp27_heads_regions.json").read_text())


def _ns(tex, inten, fall, bump=0.6, nm=None):
    return ("normal_spec.sps", {"DiffuseSampler": tex, "BumpSampler": tex + "_n", "SpecSampler": tex + "_s"},
            {"specularIntensityMult": inten, "specularFalloffMult": fall, "specularFresnel": 0.97, "bumpiness": bump}, nm or tex)


# ---------------------------------------------------------------------------------------------------- shell textures
SHELL_TEX = dict(K26.SHELL_TEX)
SHELL_TEX["wall"] = ("lp27_wall", "lp27_wall_n", "lp27_wall_s", 10.0, 0.15)
SHELL_TEX["tile"] = ("lp27_dado", "lp27_dado_n", "lp27_dado_s", 22.0, 0.30)
SHELL_EXTRA_SPECS = list(K26.SHELL_EXTRA_SPECS)
SHELL_EXTRA_SPECS[0] = _ns("lp27_wall", 0.15, 10.0, 0.8, "lp27_wall_x")
SHELL_EXTRA_SPECS[2] = _ns("lp27_wall", 0.15, 10.0, 0.8, "lp27_wall_y")
SHELL_TEX_N = K26.SHELL_TEX_N


# ---------------------------------------------------------------------------------------------------- helpers
def _foot(name, s, t, yaw):
    (x0, y0, _z0), (x1, y1, _z1) = VB[name]
    a = math.radians(yaw); ca, sa = math.cos(a), math.sin(a)
    P = [(s + x * ca - y * sa, t + x * sa + y * ca) for x in (x0, x1) for y in (y0, y1)]
    return min(p[0] for p in P), max(p[0] for p in P), min(p[1] for p in P), max(p[1] for p in P)


def _clip(poly, ax, lim, low):
    """poly = [(p, uv)]; part with p[ax] <= lim (low) or >= lim."""
    out = []
    ins = (lambda p: p[ax] <= lim + 1e-9) if low else (lambda p: p[ax] >= lim - 1e-9)
    for i in range(len(poly)):
        (a, ua), (b, ub) = poly[i], poly[(i + 1) % len(poly)]
        if ins(a):
            out.append((a, ua))
        if ins(a) != ins(b) and abs(b[ax] - a[ax]) > 1e-9:
            k = (lim - a[ax]) / (b[ax] - a[ax])
            out.append((tuple(a[j] + (b[j] - a[j]) * k for j in range(3)), tuple(ua[j] + (ub[j] - ua[j]) * k for j in range(2))))
    return out if len(out) >= 3 else []


# ---------------------------------------------------------------------------------------------------- snack rack notch
RACK = "v_ret_gassweets"
NS1 = 7.262                                   # back of the notch (counter front is s = 6.95)
_re = B9._against(RACK, (NS1 - 0.004, 5.66), (-1.0, 0.0), 0.0)
_rf = _foot(RACK, _re[1], _re[2], _re[4])
NT0, NT1 = round(_rf[2] - 0.015, 3), round(_rf[3] + 0.015, 3)


def _notch(f):
    P = f["v"]
    if max(p[2] for p in P) > 1.36 or min(p[0] for p in P) > NS1 - 1e-4 or max(p[0] for p in P) < 6.90 \
            or max(p[1] for p in P) < NT0 + 1e-4 or min(p[1] for p in P) > NT1 - 1e-4:
        return [f]
    poly = list(zip([tuple(p) for p in P], [tuple(u) for u in f["uv"]]))
    keep = []
    a = _clip(poly, 1, NT0, True); rest = _clip(poly, 1, NT0, False)
    b = _clip(rest, 1, NT1, False); rest = _clip(rest, 1, NT1, True)
    c = _clip(rest, 0, NS1, False)
    for q in (a, b, c):
        if q:
            area = 0.0
            for i in range(1, len(q) - 1):
                u = [q[i][0][j] - q[0][0][j] for j in range(3)]; w = [q[i + 1][0][j] - q[0][0][j] for j in range(3)]
                area += math.sqrt((u[1] * w[2] - u[2] * w[1]) ** 2 + (u[2] * w[0] - u[0] * w[2]) ** 2 + (u[0] * w[1] - u[1] * w[0]) ** 2)
            if area > 2e-6:
                keep.append(dict(f, v=[p for p, _u in q], uv=[u for _p, u in q]))
    return keep


def _east_wall_old(f):
    """1.9.3 fittings on the back wall above the back counter (shelves, brackets, knife rack, clock, phone, hanging rail)."""
    P = f["v"]
    if not (0.10 < min(p[1] for p in P) and max(p[1] for p in P) < 6.60 and max(p[2] for p in P) < 2.62):
        return False
    smin, zmin = min(p[0] for p in P), min(p[2] for p in P)
    cz = sum(p[2] for p in P) / len(P)
    return (smin > 9.50 and cz > 1.36) or (smin > 9.80 and zmin > 0.99) or (_INV.get(f["mat"]) == "iron" and max(p[0] for p in P) > 9.90 and zmin > 1.10 and smin > 9.5)


BASK = (-0.57, -0.07, 3.93, 4.37)             # basket stack at the west end of the island gondola (s0, s1, t0, t1)
_HSTAT = {}


def hall_faces():
    out, st = [], {"east": 0, "notch_cut": 0}
    for f in _hf26():
        if _east_wall_old(f):
            st["east"] += 1; continue
        fs = _notch(f)
        if len(fs) != 1 or fs[0] is not f:
            st["notch_cut"] += 1
        out += fs
    # notch lining (dark), open to the hall and to the top
    _bx(out, NS1, NS1 + 0.012, NT0, NT1, 0.02, 1.018, "iron")
    _bx(out, 6.956, NS1 + 0.012, NT0 - 0.012, NT0, 0.02, 1.018, "iron")
    _bx(out, 6.956, NS1 + 0.012, NT1, NT1 + 0.012, 0.02, 1.018, "iron")
    # shopping baskets: base + 6 nested baskets (own geometry)
    s0, s1, t0, t1 = BASK
    _bx(out, s0, s1, t0, t1, F0, F0 + 0.10, "iron", 0.004)
    for k in range(6):
        z0 = F0 + 0.10 + 0.045 * k; z1 = z0 + (0.21 if k == 5 else 0.040)
        a = 0.012 + 0.004 * (5 - k)
        for (x0, x1, y0, y1) in ((s0 + a, s1 - a, t0 + a, t0 + a + 0.006), (s0 + a, s1 - a, t1 - a - 0.006, t1 - a),
                                 (s0 + a, s0 + a + 0.006, t0 + a, t1 - a), (s1 - a - 0.006, s1 - a, t0 + a, t1 - a)):
            _bx(out, x0, x1, y0, y1, z0, z1, "steel")
    _bx(out, s0 + 0.03, s1 - 0.03, t0 + 0.03, t1 - 0.03, F0 + 0.325, F0 + 0.331, "steel")          # bottom of the top basket
    for y in (t0 + 0.10, t1 - 0.106):
        _bx(out, s0 + 0.12, s1 - 0.12, y, y + 0.006, F0 + 0.545, F0 + 0.56, "iron")                # handles
    _HSTAT.clear(); _HSTAT.update(st)
    return [f for f in out if f]


# ---------------------------------------------------------------------------------------------------- market drawable
CIG_Z = (1.22, 1.84)                          # two rows of v_ret_247_cigs (0.62 m high) -> top 2.46
HEAD_Z = (2.475, 2.705)                       # lit header signs up to the band (2.72)
HEAD_KEYS = ("lp_tobacco", "smokes", "lotto", "lp_market", "cigars")
_cy = B9.wall_yaw((-1.0, 0.0))
_cf = _foot("v_ret_247_cigs", 0.0, 0.0, _cy)
CIG_W = _cf[3] - _cf[2]
CIG_T = [0.24 - _cf[2] + (CIG_W + 0.012) * k for k in range(5)]          # prop origins along the wall
GRIME7 = (  # cell, centre, width, z0, z1, wall normal
    ("smudge", (5.35, YN), 0.90, 1.00, 1.75, (0.0, -1.0)), ("drips", (6.25, YN), 0.50, 1.02, 1.62, (0.0, -1.0)),
    ("dust", (6.72, YN), 0.42, 1.00, 1.70, (0.0, -1.0)), ("dust", (5.05, YN), 0.36, 1.00, 1.60, (0.0, -1.0)),
    ("drips", (5.80, YN), 0.60, 2.05, 2.70, (0.0, -1.0)), ("smudge", (6.40, YS), 0.80, 1.02, 1.70, (0.0, 1.0)),
    ("drips", (6.05, YS), 0.50, 1.60, 2.66, (0.0, 1.0)), ("dust", (5.86, YS), 0.36, 1.00, 1.60, (0.0, 1.0)),
    ("drips", (7.60, YS), 0.60, 1.90, 2.70, (0.0, 1.0)), ("smudge", (8.80, YS), 0.90, 1.05, 1.75, (0.0, 1.0)),
    ("dust", (9.72, YS), 0.42, 1.00, 1.70, (0.0, 1.0)), ("drips", (7.55, YN), 0.50, 1.90, 2.70, (0.0, -1.0)),
    ("smudge", (7.70, YN), 0.80, 1.05, 1.75, (0.0, -1.0)), ("drips", (XW, 2.95), 0.50, 1.80, 2.70, (1.0, 0.0)),
    ("smudge", (0.80, YS), 0.50, 1.10, 1.80, (0.0, 1.0)), ("drips", (0.95, YS), 0.36, 2.00, 2.70, (0.0, 1.0)),
)


def market_faces():
    out = [f for f in _mk26() if f["mat"] != MAT["decal6"]]
    for k, key in enumerate(HEAD_KEYS):                                  # header light boxes over the cigarette racks
        t0, t1 = CIG_T[k] + _cf[2], CIG_T[k] + _cf[3]
        _bx(out, XE - 0.115, XE - 0.004, t0, t1, HEAD_Z[0], HEAD_Z[1], "top20")
        x0, y0, x1, y1 = HREG[key]
        _quad(out, (XE - 0.115, (t0 + t1) / 2), (t1 - t0) - 0.02, HEAD_Z[0] + 0.012, HEAD_Z[1] - 0.012, (-1.0, 0.0), "menu",
              (x0 / 1024.0, 1 - y1 / 512.0, x1 / 1024.0, 1 - y0 / 512.0), 0.002)
    _bx(out, XE - 0.02, XE - 0.004, CIG_T[0] + _cf[2] - 0.02, CIG_T[4] + _cf[3] + 0.02, CIG_Z[0] - 0.03, HEAD_Z[0], "top20")   # dark backing board
    # posters / notices on the free wall pieces
    _sign2(out, "open24", (6.20, YN), 0.56, 1.72, 2.00, (0.0, -1.0), 0.005)
    _sign(out, "p_2for1", (5.85, YN), 0.30, 1.28, 1.58, (0.0, -1.0), "signs20", 0.005)
    _sign(out, "p_smile", (6.05, YS), 0.30, 1.86, 2.16, (0.0, 1.0), "signs20", 0.005)
    _sign2(out, "phone", (8.80, YS), 0.50, 1.80, 2.05, (0.0, 1.0), 0.005)
    _sign2(out, "cashonly", (7.62, YS), 0.26, 1.52, 1.78, (0.0, 1.0), 0.005)
    _sign(out, "p_noid", (9.30, YS), 0.26, 1.50, 1.76, (0.0, 1.0), "signs20", 0.005)
    _sign(out, "coffee", (7.62, YN), 0.90, 1.56, 1.86, (0.0, -1.0), "signs20", 0.005)
    _sign(out, "p_lotto", (XW, 2.96), 0.30, 1.86, 2.16, (1.0, 0.0), "signs20", 0.005)
    for cell, c, w, z0, z1, n in GRIME7:
        _quad(out, c, w, z0, z1, n, "decal6", K25._CELL[cell], 0.0035)
    return [f for f in out if f]


def _market_specs():
    sp = list(K26._SPECS25)
    sp[MAT["teal20"]] = _ns("lp27_band", 0.25, 16.0)
    sp[MAT["decal6"]] = ("decal.sps", {"DiffuseSampler": "lp27_grime"}, {}, "lp27_grime")
    sp[MAT["menu"]] = ("emissive.sps", {"DiffuseSampler": "lp27_heads"}, {"emissiveMultiplier": 1.6}, "lp27_heads_e")
    used = {f["mat"] for f in market_faces()}
    return [(sp[i][0], sp[i][1], sp[i][2], sp[i][3] + "_mk") if i in used else K26.PANEL + ("lp20_unused_mk_%d" % i,) for i in range(len(sp))]


EXTRA_HALL_DRAWABLES = (("gs_v26_market", market_faces, _market_specs),)


# ---------------------------------------------------------------------------------------------------- props + collision
FRUIT = B9._against("v_ret_247_fruit", (ROW2[1][0] - 1.05, ROW2[0] + 0.03), (-1.0, 0.0))
DONUT = B9._against("v_ret_247_donuts", (ISLAND[1][-1] + 1.05, ISLAND[0] + 0.025), (1.0, 0.0))
SWEETS = ("v_ret_ml_sweet1", "v_ret_ml_sweet9", "v_ret_ml_sweetego", "v_ret_ml_sweet8", "v_ret_ml_sweet2")


def vanilla_props():
    out, stools = [], 0
    for e in _vp26():
        n, s, t, z, yaw = e
        hall = s < XE - 0.02 and t < YN - 0.02
        if n == RACK:
            continue                                                     # moves into the counter notch
        if n == "lr_prop_clubstool_01" and hall:
            stools += 1
            if stools < 3:
                continue                                                 # two of the three counter stools go
            e = (n, s, 6.70, z, yaw)
        if hall and s > 9.60 and z > 1.30:
            continue                                                     # stock of the old back-wall shelves / rail
        if hall and 6.95 < s < NS1 + 0.07 and NT0 - 0.05 < t < NT1 + 0.05 and z > 0.9:
            if n == "prop_cs_paper_cup" and t > 6.3:
                continue
            e = (n, 7.40, t, z, yaw)                                     # counter-top items clear of the notch
        if n == "prop_till_01" and hall and s < 7.6:
            e = (n, 7.60, t, z, yaw)
        if hall and n == "prop_juice_dispenser" and s < 8.1:
            e = (n, s, 6.60, z, yaw)
        if hall and n in ("prop_coffee_mac_02", "prop_knife_stand", "prop_radio_01") and s > 9.55:
            e = (n, 9.58 if n == "prop_coffee_mac_02" else 9.66, t, z, yaw)       # clear of the cigarette racks
        out.append(e)
    out.append(_re)
    for z in CIG_Z:
        for t in CIG_T:
            e = B9._against("v_ret_247_cigs", (XE - 0.004, t), (-1.0, 0.0), 0.0)
            out.append((e[0], e[1], e[2], z, e[4]))
    out += [FRUIT, DONUT]
    fy = B9.wall_yaw((-1.0, 0.0))
    out += [("v_ret_247_lottery", 7.50, 5.82, 1.02, fy), ("v_ret_247_lotterysign", 7.86, 5.10, 1.02, fy)]
    for k, t in enumerate((0.55, 1.05, 4.55, 5.15, 5.75)):               # candy boxes along the back counter, customer side of it
        out.append((SWEETS[k], 9.36, t, 0.92, 90.0))
    return out


def collision_boxes():
    M = "WOOD_SOLID_MEDIUM"
    out = [b for b in _cb26() if not (abs(b[0][5] - 1.05) < 1e-6 and abs(b[0][2] - 3.38) < 1e-6)]          # candy rack box at the island end
    f = _foot("v_ret_247_fruit", FRUIT[1], FRUIT[2], FRUIT[4]); d = _foot("v_ret_247_donuts", DONUT[1], DONUT[2], DONUT[4])
    out += [((f[0], f[1], f[2], f[3], F0, 0.84), M), ((d[0], d[1], d[2], d[3], F0, 1.91), M), ((BASK[0], BASK[1], BASK[2], BASK[3], F0, 0.55), M)]
    return out


# ---------------------------------------------------------------------------------------------------- lights (warmer)
_COOL_KINDS = ("window_day_fill", "cooler_glow")


def _warm(l):
    if not isinstance(l, dict) or l.get("kind") in _COOL_KINDS:
        return l
    c = l["color"]
    return dict(l, color=(c[0], round(min(1.0, c[1] * 0.965), 3), round(c[2] * 0.89, 3)), intensity=round(l["intensity"] * 1.06, 3))


def open_lights():
    return [_warm(l) for l in _ol26()]


def closed_lights():
    return [_warm(l) for l in _cl26()]


# ---------------------------------------------------------------------------------------------------- material lists
SHADER_SPECS[MAT["tile"]] = _ns("lp27_dado", 0.30, 22.0, 0.6, "lp27_dado_hall")
_used = {f["mat"] for f in hall_faces()}
for _i in range(len(SHADER_SPECS)):
    if _i not in _used and not SHADER_SPECS[_i][3].startswith("lp20_unused"):
        SHADER_SPECS[_i] = K26.PANEL + ("lp20_unused_%d" % _i,)
for _n in ("hall_faces", "vanilla_props", "collision_boxes", "open_lights", "closed_lights"):
    for _m in (K30, K21, K22, K23, K24, K25, K26):
        setattr(_m, _n, globals()[_n])
for _m in (K30, K21, K22, K23, K24, K25, K26):
    _m.SHELL_TEX, _m.SHELL_EXTRA_SPECS, _m.SHELL_TEX_N = SHELL_TEX, SHELL_EXTRA_SPECS, SHELL_TEX_N
