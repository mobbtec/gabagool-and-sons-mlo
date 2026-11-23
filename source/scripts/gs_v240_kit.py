# LONG PIG 2.4.0 - quality pass on 2.3.0 (owner's in-game screenshots 2026-11-21 15:15 + brief "PLEBMASTERS PROP CATALOG
# AND QA"). Protected as before: exterior, ceiling, every light, fans, the two overhead menu boards, layout, palette.
#   WALLS   * calm plaster lp24_wall at a real 2.56 m repeat, world-planar UVs on every wall face (the sandy noise of
#             2.3.0 was a 512 px photo repeated every ~1 m); dado lp24_dado with wear only near the floor, clean band;
#           * leftovers removed: 8 "missing tile" recesses of 1.5.0 (they showed as rectangles under the paint) are
#             filled flush, 5 leak decals of 0.9 on the hall walls (the greenish mould) are gone, the old shelf rail with
#             brackets on the east wall (1.9.x) is gone.
#   KIOSK   * dark thin frames, glass to the fascia + transom glass up to 2.90 m on the open sides, no roof slab, real
#             service opening with a steel deal tray, stepped lottery ticket rack on the counter, second row of
#             cigarette racks (v_ret_247_cigs) on the back wall.
#   CASES   * heated case and pastry case rebuilt: steel plinth, pans, slanted front glass, shelf, canopy; dense food.
#   STOCK   * archive boxes (v_ret_gc_box1/2) out of the hall, floor stacks at the window gone, ONE chest cooler moved to
#             the solid wall next to the kiosk (the window is clear), newspaper machine removed.
# NOT in 2.4.0 (next): window frames + blinds as one set, cooler variety, FPS work (waiting for the owner's numbers).
import json, math
from pathlib import Path
import gs_v230_kit as K23
from gs_v230_kit import *                    # noqa: F401,F403

VERSION = "2.4.0"
K22, K21, K30, V, B9, PG = K23.K22, K23.K21, K23.K30, K23.V, K23.B9, K23.PG
F0 = K23.F0
XW, YS, XE, YN = K23.XW, K23.YS, K23.XE, K23.YN
_quad, _bx, _sign, _sign2 = K22._quad, K22._bx, K22._sign, K23._sign2
REG2 = K23.REG2
_hf23, _vp23, _cb23 = K23.hall_faces, K23.vanilla_props, K23.collision_boxes
_kept21, _shell23 = K21.kept_faces, PG.shell_faces
_INV = {v: k for k, v in MAT.items()}
_ns = K23._ns
WALL_REP = 2.56

SHADER_SPECS[MAT["teal20"]] = _ns("lp24_band", 0.3, 16.0)
SHADER_SPECS[MAT["alu20"]] = _ns("lp24_alu", 0.7, 60.0)
SHELL_TEX = dict(K23.SHELL_TEX)
SHELL_TEX["wall"] = ("lp24_wall", "lp24_wall_n", "lp24_wall_s", 10.0, 0.15)
SHELL_TEX["tile"] = ("lp24_dado", "lp24_dado_n", "lp24_dado_s", 24.0, 0.35)
_WALLSPEC = ("normal_spec.sps", {"DiffuseSampler": "lp24_wall", "BumpSampler": "lp24_wall_n", "SpecSampler": "lp24_wall_s"},
             {"specularIntensityMult": 0.15, "specularFalloffMult": 10.0, "specularFresnel": 0.97, "bumpiness": 0.6})
SHELL_EXTRA_SPECS = list(K23.SHELL_EXTRA_SPECS)
SHELL_EXTRA_SPECS[0] = _WALLSPEC + ("lp24_wall_x",)
SHELL_EXTRA_SPECS[2] = _WALLSPEC + ("lp24_wall_y",)
SHELL_TEX_N = K23.SHELL_TEX_N


# ------------------------------------------------------------------------------------------------ shell
def _newell(P):
    nx = ny = nz = 0.0
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        nx += (a[1] - b[1]) * (a[2] + b[2]); ny += (a[2] - b[2]) * (a[0] + b[0]); nz += (a[0] - b[0]) * (a[1] + b[1])
    L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / L, ny / L, nz / L


_PSW, _PNW = PG.P_SW, PG.P_NW
_CL = math.hypot(_PNW[0] - _PSW[0], _PNW[1] - _PSW[1])
_CN = ((_PNW[1] - _PSW[1]) / _CL, -(_PNW[0] - _PSW[0]) / _CL)          # normal of the chamfer wall
if _CN[0] * (2.0 - _PSW[0]) + _CN[1] * (2.0 - _PSW[1]) < 0:            # make it point into the room
    _CN = (-_CN[0], -_CN[1])
_PLANES = (lambda p: (YS - p[1], (0.0, -1.0)), lambda p: (XW - p[0], (-1.0, 0.0)),
           lambda p: (-((p[0] - _PSW[0]) * _CN[0] + (p[1] - _PSW[1]) * _CN[1]), (-_CN[0], -_CN[1])))


def _recess(f):
    """None | 'side' | flush copy of the back face of an old missing-tile recess (5.5 / 3.5 cm behind a hall wall)."""
    P = f["v"]
    if max(max(p[i] for p in P) - min(p[i] for p in P) for i in range(3)) > 0.45 or min(p[2] for p in P) < 1.2:
        return None
    for pl in _PLANES:
        ds = [pl(p) for p in P]
        dd = [d[0] for d in ds]
        if min(dd) > -0.002 and max(dd) < 0.07 and max(dd) > 0.02:
            if min(dd) < 0.02:
                return "side"
            o = ds[0][1]
            return dict(f, v=[(p[0] - o[0] * d, p[1] - o[1] * d, p[2]) for p, d in zip(P, dd)], mat=1)
    return None


def _wall_uv(f):
    P = f["v"]; n = _newell(P)
    if abs(n[2]) > 0.7:
        return [(p[0] / WALL_REP, p[1] / WALL_REP) for p in P]
    L = math.hypot(n[0], n[1]); d = (-n[1] / L, n[0] / L)
    return [((p[0] * d[0] + p[1] * d[1]) / WALL_REP, p[2] / WALL_REP) for p in P]


def _dado_uv(f):
    P = f["v"]; n = _newell(P)
    if abs(n[2]) > 0.7:
        return [(p[0] / 1.6, 0.55 + 0.2 * (p[1] % 1.0)) for p in P]
    L = math.hypot(n[0], n[1]); d = (-n[1] / L, n[0] / L)
    if max(p[2] for p in P) <= PG.WAINSCOT + 0.02:
        return [((p[0] * d[0] + p[1] * d[1]) / 1.6, p[2] / PG.WAINSCOT) for p in P]         # v 0 = floor (worn) .. 1 = dado top
    return [((p[0] * d[0] + p[1] * d[1]) / 1.6, 0.45 + 0.12 * p[2]) for p in P]             # red window surrounds: clean part only


def _shell_240(*a, **k):
    out = []
    st = {"holes": 0, "sides": 0, "leaks": 0}
    for f in _shell23(*a, **k):
        if not isinstance(f, dict):
            out.append(f); continue
        m = f["mat"]
        if m == 9 and min(p[2] for p in f["v"]) > 0.2 and max(p[0] for p in f["v"]) < XE + 0.05 and max(p[1] for p in f["v"]) < YN + 0.05:
            st["leaks"] += 1; continue                                     # 0.9 leak decals on the hall walls
        if m in (1, 6):
            r = _recess(f)
            if r == "side":
                st["sides"] += 1; continue
            if r:
                st["holes"] += 1; f = r; m = 1
        if m in (1, 6, 8):
            f = dict(f, uv=_wall_uv(f))
        elif m == 2:
            f = dict(f, uv=_dado_uv(f))
        out.append(f)
    _shell_240.stats = st
    return out


PG.shell_faces = _shell_240


def kept_faces():
    out = []
    for f in _kept21():
        P = f["v"]; m = _INV.get(f["mat"])
        if m in ("iron", "steel") and min(p[0] for p in P) > 9.60 and max(p[2] for p in P) < 2.50 and max(p[1] for p in P) < 6.60:
            continue                                                       # 1.9.x shelf rail + brackets on the east wall
        out.append(f)
    return out


K21.kept_faces = kept_faces

# ------------------------------------------------------------------------------------------------ kiosk
PW = 0.035                                   # frame profile
GZ = (1.05, 2.115)                           # main glass
TZ = (2.28, 2.90)                            # transom glass (chamfer + north face)
SLOT = (0.95, 1.55, 1.36)                    # service opening on the west face: u0, u1, head


def _kiosk(out):
    for i, (a, b, L, d, n) in enumerate(K22._segs()):
        fr = V.Frame(O=(a[0], a[1], 0.0), X=(d[0], d[1], 0.0), Y=(n[0], n[1], 0.0))
        cb = lambda x0, x1, y0, y1, z0, z1, mat, ch=0.0: out.extend(V.cbox(fr, x0, x1, y0, y1, z0, z1, mat, ch=ch))

        def gl(u0, u1, z0, z1):
            c = (a[0] + d[0] * (u0 + u1) / 2 - n[0] * 0.03, a[1] + d[1] * (u0 + u1) / 2 - n[1] * 0.03)
            for nn in (n, (-n[0], -n[1])):
                _quad(out, c, u1 - u0, z0, z1, nn, "glass", (0.0, 0.0, 1.0, 1.0), 0.0)
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
        Y0, Y1 = -0.052, -0.008
        cb(0.0, L, Y0, Y1, GZ[1], 2.15, "alu20")                           # head
        cb(-0.03, L + 0.03, -0.09, 0.03, 2.15, 2.28, "alu20")              # fascia beam (lettering of 2.3.0 sits on it)
        if i == 0:
            u0, u1, zh = SLOT
            posts = (0.0, 0.80 - PW / 2, 1.70 - PW / 2, L - PW)
            cb(0.0, u0, Y0, Y1, 1.02, GZ[0], "alu20"); cb(u1, L, Y0, Y1, 1.02, GZ[0], "alu20")
            for u in (u0 - 0.025, u1):
                cb(u, u + 0.025, Y0, Y1, 1.02, zh, "alu20")
            cb(u0 - 0.025, u1 + 0.025, Y0, Y1, zh - 0.025, zh, "alu20")
            gl(0.0, u0, GZ[0], GZ[1]); gl(u0, u1, zh, GZ[1]); gl(u1, L, GZ[0], GZ[1])
            cb(u0, u1, -0.20, 0.17, 1.02, 1.030, "steel", 0.002)           # deal tray
            for u in (u0 - 0.012, u1):
                cb(u, u + 0.012, -0.20, 0.17, 1.02, 1.048, "steel")
            # stepped lottery ticket rack behind the glass
            x0, y0, x1, y1 = REG2["lotto_rack"]; h4 = (y1 - y0) / 4.0
            r0, r1 = 0.10, 0.74
            for k4 in range(4):
                zb = 1.03 + 0.095 * k4
                cb(r0, r1, -0.36, -0.135 - 0.05 * k4, 1.02, zb + 0.09, "top20")
                yb, yt = -0.10 - 0.05 * k4, -0.13 - 0.05 * k4
                vt, vb = 1 - (y0 + (3 - k4) * h4) / 1024.0, 1 - (y0 + (4 - k4) * h4) / 1024.0
                V.emit(out, V.F([fr.p(r1, yb, zb), fr.p(r0, yb, zb), fr.p(r0, yt, zb + 0.09), fr.p(r1, yt, zb + 0.09)], "signs23b",
                                [(x0 / 1024.0, vb), (x1 / 1024.0, vb), (x1 / 1024.0, vt), (x0 / 1024.0, vt)], hint=(n[0], n[1], 0.3)))
        else:
            kk = max(1, int(round(L / 1.15)))
            posts = tuple(min(max(L * j / kk - PW / 2, 0.0), L - PW) for j in range(kk + 1))
            cb(0.0, L, Y0, Y1, 1.02, GZ[0], "alu20")
            gl(0.0, L, GZ[0], GZ[1])
            gl(0.0, L, TZ[0], TZ[1])                                       # transom up to the menu-board line
            cb(0.0, L, Y0, Y1, TZ[1], TZ[1] + PW, "alu20")
            for u in posts:
                cb(u, u + PW, Y0, Y1, TZ[0], TZ[1], "alu20")
        for u in posts:
            cb(u, u + PW, Y0, Y1, GZ[0], GZ[1], "alu20")
    # back walls inside: one shelf under the cigarette racks (south), four shelves on the east wall
    _bx(out, 7.30, 9.60, YS + 0.01, YS + 0.20, 1.12, 1.14, "white20")
    for z in (1.12, 1.38, 1.64, 1.90):
        _bx(out, XE - 0.20, XE - 0.01, 0.17, 1.47, z, z + 0.02, "white20")
    _bx(out, 7.20, 9.74, YS + 0.004, YS + 0.018, 1.94, 2.62, "top20")      # backing board of the upper cigarette racks


# ------------------------------------------------------------------------------------------------ food cases
def _case(out, c0, c1, h, shelf, pans):
    s0, s1 = K22.SERVICE[0] + 0.04, K22.SERVICE[1] - 0.04
    _bx(out, s0, s1, c0, c1, 0.94, 1.00, "steel", 0.003)                   # plinth
    _bx(out, s0 - 0.004, s0, c0 + 0.03, c1 - 0.03, 0.948, 0.992, "top20")  # control strip
    _bx(out, s0 + 0.09, s1, c0, c1, h, h + 0.05, "steel", 0.004)           # canopy
    _bx(out, s0 + 0.10, s0 + 0.16, c0 + 0.04, c1 - 0.04, h - 0.012, h, "top20")   # lamp housing under the canopy
    _bx(out, s0, s0 + 0.022, c0, c1, 1.00, 1.014, "alu20")                 # glass channel
    for t in (c0, c1 - 0.02):
        _bx(out, s1 - 0.02, s1, t, t + 0.02, 1.00, h, "alu20")             # rear posts
    fa, fb = (s0 + 0.011, 1.00), (s0 + 0.10, h)                            # slanted front glass
    for hint in ((-1.0, 0.0, 0.2), (1.0, 0.0, -0.2)):
        V.emit(out, V.F([(fa[0], c0, fa[1]), (fa[0], c1, fa[1]), (fb[0], c1, fb[1]), (fb[0], c0, fb[1])], "glass", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=hint))
    for t, hn in ((c0 + 0.008, -1.0), (c1 - 0.008, 1.0)):                  # side glass
        for sg in (1.0, -1.0):
            V.emit(out, V.F([(fa[0], t, 1.00), (s1, t, 1.00), (s1, t, h), (fb[0], t, h)], "glass", [(0, 0), (1, 0), (1, 1), (0.15, 1)], hint=(0.0, hn * sg, 0.0)))
    if shelf:
        _bx(out, s0 + 0.15, s1 - 0.03, c0 + 0.03, c1 - 0.03, shelf, shelf + 0.012, "steel")
        _bx(out, s0 + 0.145, s0 + 0.15, c0 + 0.03, c1 - 0.03, shelf - 0.02, shelf + 0.02, "white20")     # ticket strip
    w = (c1 - c0 - 0.06 - 0.02 * (pans - 1)) / pans
    out_t = []
    for k in range(pans):
        t0 = c0 + 0.03 + k * (w + 0.02)
        _bx(out, s0 + 0.06, s1 - 0.05, t0, t0 + w, 1.00, 1.03, "steel", 0.004)
        out_t.append(t0 + w / 2)
    return out_t


HOT, PASTRY = (K22.HOTCASE[0], K22.HOTCASE[1], 1.50, 1.26, 4), (K22.DELICASE[0], K22.DELICASE[1], 1.42, 1.22, 2)
_PAN_T = {}


def _service(out):
    s0, s1, t0, t1 = K22.SERVICE
    _bx(out, s0 + 0.03, s1 - 0.02, t0, t1, F0, 0.10, "dark20")
    _bx(out, s0, s1, t0, t1, 0.10, 0.90, "lam20", 0.003)
    _bx(out, s0 - 0.04, s1 + 0.03, t0 - 0.02, t1 + 0.02, 0.90, 0.94, "steel", 0.006)
    _PAN_T["hot"] = _case(out, *HOT)
    _PAN_T["pastry"] = _case(out, *PASTRY)
    _bx(out, 7.00, 7.05, 1.57, 1.93, 0.15, 1.00, "alu20")                                    # staff gate
    s0, s1, t0, t1 = K22.COFFEE
    _bx(out, s0 + 0.03, s1, t0 + 0.03, t1, F0, 0.10, "dark20")
    _bx(out, s0, s1, t0, t1, 0.10, 0.90, "lam20", 0.003)
    _bx(out, s0 - 0.04, s1, t0 - 0.03, t1, 0.90, 0.94, "top20", 0.006)
    _bx(out, 9.30, 9.92, 2.00, 6.00, F0, 0.86, "steel"); _bx(out, 9.28, 9.92, 1.98, 6.02, 0.86, 0.90, "steel")   # staff bench


K22._kiosk, K22._service = _kiosk, _service


def hall_faces():
    out = []
    for f in _hf23():
        P = f["v"]; n = float(len(P))
        cs, ct, cz = sum(p[0] for p in P) / n, sum(p[1] for p in P) / n, sum(p[2] for p in P) / n
        if _INV.get(f["mat"]) == "signs20" and abs(cs - 7.024) < 0.02 and abs(ct + 0.78) < 0.05 and 1.15 < cz < 1.47:
            continue                                                       # flat LOTTO sticker where the real rack now stands
        out.append(f)
    return out


def vanilla_props():
    out = []
    for e in _vp23():
        n, s, t, z, yaw = e
        hall = s < XE - 0.02 and t < YN - 0.02
        if hall and n in ("v_ret_gc_box1", "v_ret_gc_box2", "prop_news_disp_02a_s", "prop_bar_cooler_03", "prop_bar_cooler_01"):
            continue
        if n == "prop_cs_beer_box" and t < YS + 0.9:
            continue                                                       # floor stacks under the window
        if n == "prop_cs_beer_box" and abs(s - 4.42) < 0.05 and z > F0 + 0.6:
            continue                                                       # end-cap stack two cases high
        if 7.0 < s < 7.7 and 2.25 < t < 5.15 and 0.97 < z < 1.30:
            continue                                                       # food of the old cases
        out.append(e)
    out.append(B9._against("prop_bar_cooler_01", (6.25, YS), (0.0, 1.0)))  # the one chest cooler: solid wall, window clear
    for s in K23.CIG_S:
        e = B9._against("v_ret_247_cigs", (s, YS + 0.018), (0.0, 1.0))
        out.append((e[0], e[1], e[2], 1.96, e[4]))
    SS = (7.20, 7.36, 7.52)
    hot = (("prop_cs_hotdog_01", 90.0), ("prop_cs_burger_01", 0.0), ("prop_taco_01", 90.0), ("prop_cs_hotdog_02", 90.0))
    for k, t in enumerate(_PAN_T["hot"]):
        nm, yw = hot[k % 4]
        for j, s in enumerate(SS):
            out.append((nm, s, t - 0.07, 1.03, yw + (6.0, -8.0, 4.0)[j])); out.append((nm, s, t + 0.07, 1.03, yw + (-5.0, 7.0, -3.0)[j]))
    for k, t in enumerate((2.52, 2.78, 3.04, 3.30, 3.52)):
        out.append((("prop_cs_burger_01", "prop_taco_02", "prop_cs_hotdog_02", "prop_cs_burger_01", "prop_taco_02")[k], 7.42, t, HOT[3] + 0.012, (10.0, 95.0, 80.0, -15.0, 100.0)[k]))
    dn = ("prop_donut_01", "prop_donut_02", "prop_donut_02b", "prop_amb_donut")
    for k, t in enumerate(_PAN_T["pastry"]):
        for j, s in enumerate(SS):
            out.append((dn[(k + j) % 4], s, t - 0.10, 1.03, 20.0 * j)); out.append((dn[(k + j + 2) % 4], s, t + 0.08, 1.03, -35.0 * j))
    for k, t in enumerate((4.30, 4.50, 4.72, 4.93)):
        out.append((("prop_food_cb_donuts", "prop_donut_02", "prop_donut_01", "prop_food_cb_donuts")[k], 7.44, t, PASTRY[3] + 0.012, (90.0, 0.0, 40.0, 80.0)[k]))
    return out


def collision_boxes():
    M = "WOOD_SOLID_MEDIUM"
    out = [b for b in _cb23() if not (b[0][2] <= YS + 0.001 and b[0][3] <= YS + 0.75 and b[0][0] < 6.5 and b[0][5] < 1.3)]   # old window-side row
    out += [((5.78, 6.72, YS, YS + 0.68, F0, 0.93), M),
            ((7.55, XE, 1.49, 1.55, 2.28, TZ[1] + PW), M), ((7.05, 7.60, 1.00, 1.50, 2.28, TZ[1] + PW), M)]
    return out


_used = {f["mat"] for f in hall_faces()}
for _i in range(len(SHADER_SPECS)):
    if _i not in _used and not SHADER_SPECS[_i][3].startswith("lp20_unused"):
        SHADER_SPECS[_i] = ("default.sps", {"DiffuseSampler": "lp20_panel_off"}, {}, "lp20_unused_%d" % _i)
for _n in ("hall_faces", "vanilla_props", "collision_boxes"):
    for _m in (K30, K21, K22, K23):
        setattr(_m, _n, globals()[_n])
for _m in (K30, K21, K22, K23):
    _m.SHELL_TEX, _m.SHELL_EXTRA_SPECS, _m.SHELL_TEX_N = SHELL_TEX, SHELL_EXTRA_SPECS, SHELL_TEX_N
