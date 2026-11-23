# LONG PIG — exterior security roller shutters: measured placement + own models (pure Python, no bpy).
# Owner brief 2026-11-02 "FINAL MLO COMPLETION + ANIMATED SECURITY SHUTTERS", part 1.
#
# MEASURED (docs/_raw/shutter_facade_measure.json, gs_38 measure step over the vanilla sc1_14_build2 geometry):
# the facade already carries a steel shutter box (texture sc1_14_t_page8) over every opening:
#   W1  box s 1.148..5.768, front t -1.814, wall face t -1.575, bottom z 2.656, top z 3.001; opening s 1.263..5.654, sill 0.602
#   W2  box t 3.306..6.511, front s -3.461, wall face s -3.223, same heights;            opening t 3.455..6.394, sill 0.602
#   D1  box a 1.470..3.882 (chamfer frame of gs_overrides), front dep +0.256, wall face dep 0; opening a 1.691..3.645, ground
# MLO-local frame (s, t, z): z = world Z - 24.45. Nothing here is copied from game files: only the positions are measured.
#
# Model frame (every shutter model): x = to the right as seen from the street, -y = out to the street (front), z up.
#   panels / bars: origin at the bottom centre ON THE CURTAIN PLANE (0.055 m in front of the wall face)
#   rails:         origin at the bottom centre ON THE WALL FACE
# Curtain kinematics (client/shutters.lua uses the same numbers, written by lua_config()):
#   bar bottom z(p) = Z_OPEN + (z_closed - Z_OPEN) * ease(p), p = 0 open .. 1 closed
#   panel k bottom = bar bottom + BAR_H + k * PANEL_H; drawn only while its bottom is below the box (BOX_BOTTOM)
import math

CH_A0 = (0.3, -1.6)
CH_DIR = (-0.68266075, 0.73073545)
CH_OUT = (-0.73073545, -0.68266075)

BOX_BOTTOM = 2.656
BOX_TOP = 3.001
Z_OPEN = 2.600                    # bar bottom when open: the bar shows 5.6 cm under the box (like a real shutter)
CURTAIN_D = 0.055                 # curtain plane in front of the wall face
RAIL_W, RAIL_D = 0.075, 0.085
EDGE_IN = 0.045                   # curtain edge inside each rail
SLAT = 0.075
PANEL_H = 4 * SLAT                # 0.30 m panels (4 slats): shorter than the box (0.345 m) so a panel always fits inside
BAR_H = 0.07
TEX_U_M = 4.5                     # metres of curtain per texture width (same pixel density on every opening)


def _chamfer_st(a, dep):
    return (CH_A0[0] + a * CH_DIR[0] + dep * CH_OUT[0], CH_A0[1] + a * CH_DIR[1] + dep * CH_OUT[1])


def _openings():
    out = {}
    # W1 storefront (SW facade): seen from the street, right = +s, out = -t
    out["w1"] = dict(c=((1.263 + 5.654) / 2, -1.575), R=(1.0, 0.0), N=(0.0, -1.0), hw=(5.654 - 1.263) / 2,
                     z_closed=0.560, rail_bottom=0.500, box=(1.148, 5.768), kind="window")
    # W2 side window (NW facade): right = -t, out = -s
    out["w2"] = dict(c=(-3.223, (3.455 + 6.394) / 2), R=(0.0, -1.0), N=(-1.0, 0.0), hw=(6.394 - 3.455) / 2,
                     z_closed=0.560, rail_bottom=0.500, box=(3.306, 6.511), kind="window")
    # D1 entrance on the corner chamfer: right = -CH_DIR, out = CH_OUT
    ac = (1.691 + 3.645) / 2
    out["d1"] = dict(c=_chamfer_st(ac, 0.0), R=(-CH_DIR[0], -CH_DIR[1]), N=CH_OUT, hw=(3.645 - 1.691) / 2,
                     z_closed=0.0, rail_bottom=-0.004, box=(1.470, 3.882), kind="door")
    for k, o in out.items():
        o["W"] = 2 * (o["hw"] + EDGE_IN)
        o["n_panels"] = int(math.ceil((BOX_BOTTOM - (o["z_closed"] + BAR_H)) / PANEL_H))
        o["rail_len"] = round(BOX_BOTTOM - o["rail_bottom"], 4)
    return out


OPENINGS = _openings()


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6.0 * x - 15.0) + 10.0)          # smootherstep: soft start and stop


def bar_z(o, p):
    return Z_OPEN + (o["z_closed"] - Z_OPEN) * p


def placements(p):
    """-> [(model, (s, t, z), heading_dir_st (= +Y = inward), visible)] at curtain progress p (already eased)."""
    out = []
    for key, o in OPENINGS.items():
        (cs, ct), (Rx, Ry), (Nx, Ny) = o["c"], o["R"], o["N"]
        inward = (-Nx, -Ny)
        for sg in (-1.0, 1.0):
            u = sg * (o["hw"] + RAIL_W / 2)
            out.append((f"lp_shut_rail_{'d' if o['kind'] == 'door' else 'w'}", (cs + Rx * u, ct + Ry * u, o["rail_bottom"]), inward, True))
        cp = (cs + Nx * CURTAIN_D, ct + Ny * CURTAIN_D)
        zb = bar_z(o, p)
        out.append((f"lp_shut_{key}_bar", (cp[0], cp[1], zb), inward, True))
        for k in range(o["n_panels"]):
            z = zb + BAR_H + k * PANEL_H
            out.append((f"lp_shut_{key}_pnl", (cp[0], cp[1], z), inward, z < BOX_BOTTOM - 0.002))
    return out


# ================================================================== model faces (atlas lp7_shutter, 1024 x 512)
def _v(row0, row1):
    return 1.0 - row1 / 512.0, 1.0 - row0 / 512.0


V_SLAT = [_v((3 - k) * 64 + 1, (4 - k) * 64 - 1) for k in range(4)]      # slat k = 0 (bottom) .. 3
V_BAR = _v(258, 382)
V_RAIL = _v(386, 446)
V_BACK = _v(450, 510)
U_RUBBER = (0.76, 0.99)


def _newell(vs):
    n = [0.0, 0.0, 0.0]
    for i in range(len(vs)):
        a, b = vs[i], vs[(i + 1) % len(vs)]
        n[0] += (a[1] - b[1]) * (a[2] + b[2]); n[1] += (a[2] - b[2]) * (a[0] + b[0]); n[2] += (a[0] - b[0]) * (a[1] + b[1])
    return n


def quad(vs, uvs, hint, mat=0):
    vs, uvs = list(vs), list(uvs)
    n = _newell(vs)
    if sum(n[i] * hint[i] for i in range(3)) < 0:
        vs.reverse(); uvs.reverse()
    return {"v": [tuple(round(c, 5) for c in v) for v in vs], "uv": [(round(u, 5), round(w, 5)) for u, w in uvs], "mat": mat,
            "smooth": False}


def box(x0, x1, y0, y1, z0, z1, ureg, vreg, skip=()):
    """Box with every face mapped onto the atlas rectangle (ureg x vreg)."""
    (u0, u1), (v0, v1) = ureg, vreg
    uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    F = []
    faces = {"-y": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
             "+y": ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0, 1, 0)),
             "-x": ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1, 0, 0)),
             "+x": ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)),
             "-z": ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], (0, 0, -1)),
             "+z": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1))}
    for k, (vs, n) in faces.items():
        if k not in skip:
            F.append(quad(vs, uv, n))
    return F


# one slat (75 mm): hook joint, rolled shoulders, flat crown — y < 0 is the street side
SLAT_PROFILE = [(0.000, -0.004), (0.006, -0.010), (0.013, -0.016), (0.037, -0.019), (0.062, -0.016), (0.069, -0.010),
                (0.075, -0.004)]


def panel_faces(W):
    F = []
    x0, x1 = -W / 2, W / 2
    ua, ub = 0.0, W / TEX_U_M
    for k in range(4):
        z0 = k * SLAT
        v0, v1 = V_SLAT[k]
        L = len(SLAT_PROFILE) - 1
        for i in range(L):
            (za, ya), (zc, yc) = SLAT_PROFILE[i], SLAT_PROFILE[i + 1]
            va, vc = v0 + (v1 - v0) * i / L, v0 + (v1 - v0) * (i + 1) / L
            vs = [(x0, ya, z0 + za), (x1, ya, z0 + za), (x1, yc, z0 + zc), (x0, yc, z0 + zc)]
            nz = -(yc - ya)
            F.append(quad(vs, [(ua, va), (ub, va), (ub, vc), (ua, vc)], (0.0, -(zc - za), nz)))
        # end caps of the slat profile (hidden in the rails, closed for the shadow pass)
        for x, sg in ((x0, -1.0), (x1, 1.0)):
            pts = [(x, y, z0 + z) for (z, y) in SLAT_PROFILE] + [(x, 0.004, z0 + SLAT), (x, 0.004, z0)]
            vb0, vb1 = V_BACK
            for i in range(len(pts) - 2):                              # fan
                tri = [pts[0], pts[i + 1], pts[i + 2]]
                F.append(quad(tri, [(0.1, vb0), (0.12, vb0), (0.12, vb1)], (sg, 0.0, 0.0)))
    vb0, vb1 = V_BACK                                                  # inside face: one flat sheet
    F.append(quad([(x1, 0.004, 0.0), (x0, 0.004, 0.0), (x0, 0.004, PANEL_H), (x1, 0.004, PANEL_H)],
                  [(ua, vb0), (min(0.74, ub), vb0), (min(0.74, ub), vb1), (ua, vb1)], (0.0, 1.0, 0.0)))
    return F


def bar_faces(W, hw):
    F = []
    x0, x1 = -W / 2, W / 2
    ub = W / TEX_U_M
    vr = V_BAR
    F += box(x0, x1, -0.012, 0.004, 0.0, BAR_H, (0.0, ub), vr)                                  # main plate
    F += box(-hw + 0.006, hw - 0.006, -0.032, -0.012, 0.020, 0.052, (0.0, ub * 0.98), vr)      # front lip (between the rails)
    F += box(x0 + 0.01, x1 - 0.01, -0.009, 0.004, -0.008, 0.0, U_RUBBER, V_BACK)               # rubber seal
    for xc in (-hw * 0.55, hw * 0.55):                                                           # two lift handles
        for sx in (-0.055, 0.055):
            F += box(xc + sx - 0.008, xc + sx + 0.008, -0.070, -0.032, 0.030, 0.042, (0.10, 0.14), vr)
        F += box(xc - 0.063, xc + 0.063, -0.082, -0.070, 0.030, 0.042, (0.10, 0.20), vr)
    F += box(-0.022, 0.022, -0.046, -0.032, 0.022, 0.050, (0.30, 0.33), vr)                    # lock housing
    F += box(-0.007, 0.007, -0.050, -0.046, 0.030, 0.044, U_RUBBER, V_BACK)                    # key slot
    return F


def rail_faces(L):
    """Guide channel on the wall face: back + front plates, outer webs, lips leaving the curtain slot (symmetric)."""
    F = []
    a = RAIL_W / 2
    uu = (0.0, 1.0)
    vr = V_RAIL
    F += box(-a, a, -0.004, 0.0, 0.0, L, uu, vr, skip=("+y",))                                 # back plate on the wall
    F += box(-a, a, -RAIL_D, -RAIL_D + 0.004, 0.0, L, uu, vr)                                    # street-side face plate
    for sx in (-1.0, 1.0):
        x_out = sx * a
        F += box(min(x_out, x_out - sx * 0.004), max(x_out, x_out - sx * 0.004), -RAIL_D + 0.004, -0.072, 0.0, L, uu, vr)   # lip
        F += box(min(x_out, x_out - sx * 0.004), max(x_out, x_out - sx * 0.004), -0.038, -0.004, 0.0, L, uu, vr)          # lip
    F += box(-a, a, -RAIL_D, 0.0, 0.0, 0.006, (0.9, 1.0), vr)                                   # foot stop
    for z in (0.25, L * 0.5, L - 0.25):                                                          # anchor heads
        F += box(-0.010, 0.010, -RAIL_D - 0.004, -RAIL_D, z - 0.010, z + 0.010, U_RUBBER, V_BACK)
    return F


def models():
    """-> {name: (faces, collision_box or None)}; collision box = (x0, x1, y0, y1, z0, z1) in model space."""
    out = {}
    for key, o in OPENINGS.items():
        W, hw = o["W"], o["hw"]
        out[f"lp_shut_{key}_pnl"] = (panel_faces(W), (-W / 2, W / 2, -0.022, 0.006, 0.0, PANEL_H))
        out[f"lp_shut_{key}_bar"] = (bar_faces(W, hw), (-W / 2, W / 2, -0.034, 0.006, -0.008, BAR_H))
    out["lp_shut_rail_w"] = (rail_faces(OPENINGS["w1"]["rail_len"]), None)
    out["lp_shut_rail_d"] = (rail_faces(OPENINGS["d1"]["rail_len"]), None)
    return out


def lua_config():
    """Numbers for client/shutters_data.lua (generated: keeps Lua and the models in step)."""
    L = ["-- GENERATED by source/scripts/gs_shutter_geometry.py (gs_38) - do not edit by hand.",
         "-- Measured facade openings in MLO-local coordinates (s, t, z); models: stream/shutters/*.ydr",
         "LPS_DATA = {", f"    BOX_BOTTOM = {BOX_BOTTOM}, Z_OPEN = {Z_OPEN}, CURTAIN_D = {CURTAIN_D}, BAR_H = {BAR_H}, PANEL_H = {PANEL_H},",
         f"    RAIL_W = {RAIL_W},", "    OPENINGS = {"]
    for key, o in OPENINGS.items():
        L.append(f"        {{ id = '{key}', c = vector2({o['c'][0]:.4f}, {o['c'][1]:.4f}), R = vector2({o['R'][0]:.6f}, {o['R'][1]:.6f}), "
                 f"N = vector2({o['N'][0]:.6f}, {o['N'][1]:.6f}), hw = {o['hw']:.4f}, z_closed = {o['z_closed']:.3f}, "
                 f"rail_bottom = {o['rail_bottom']:.3f}, n_panels = {o['n_panels']}, kind = '{o['kind']}',")
        L.append(f"          rail = `lp_shut_rail_{'d' if o['kind'] == 'door' else 'w'}`, bar = `lp_shut_{key}_bar`, pnl = `lp_shut_{key}_pnl` }},")
    L += ["    },", "}", ""]
    return "\n".join(L)


if __name__ == "__main__":
    for k, o in OPENINGS.items():
        print(k, {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in o.items() if kk not in ("c", "R", "N")}, o["c"])
    ms = models()
    print({k: len(v[0]) for k, v in ms.items()})
    print(lua_config())
