# LONG PIG (resource gabagool_sons_mlo) — v0.2.1 HERO KIT geometry (pure Python, no bpy).
# Replaces the rejected v0.2.0 slice furniture (gs_slice_geometry.furniture_faces) with:
#   * a real wall-joinery kit for the front hall (baseboard, frame-and-panel wainscot, cap rail, picture rail, cornice),
#   * a coffered/beamed ceiling with practical fixtures (opal pendants, flush domes, counter soffit with recessed cans),
#   * rebuilt booths (padded channel-tufted backs, crowned cushions with piping, walnut end caps) + terrazzo tables on
#     cast-iron pedestals,
#   * a commercial curved-glass deli case + counters clad in the same joinery, back counter, wall shelf,
#   * sculpted deli food (salami, prosciutto, provolone, mortadella, cheese, olives, peppers, mozzarella) on an original
#     procedural atlas, a hanging rail, a meat slicer and a deli-paper roll,
#   * an Italian tricolore cloth flag on a wall bracket (original, plain colours).
# Vanilla GTA V props are referenced by archetype name only (placements in vanilla_props()).
# Frame: MLO-local (s, t, z) like gs_proto_geometry; z above the vanilla floor slab (FLOOR = 0.015).
# Every face record: {"v": [...], "uv": [...], "mat": index, "smooth": bool}.
import math
import random

import gs_proto_geometry as PG
import gs_slice_geometry as SG

FLOOR, CEIL = PG.FLOOR, PG.CEIL
MAT = {"walnut": 0, "leather": 1, "terrazzo": 2, "steel": 3, "enamel": 4, "brass": 5, "iron": 6, "glass": 7,
       "food": 8, "glow": 9, "flag": 10, "opal": 11, "plaster": 12}
REP = {"walnut": 1.0, "leather": 0.45, "terrazzo": 0.9, "steel": 0.8, "enamel": 0.6, "brass": 0.5, "iron": 0.5,
       "glass": 1.0, "glow": 1.0, "opal": 1.0, "plaster": 2.0, "flag": 1.0, "food": 1.0}
FOOD_CELLS = ["salami_casing", "salami_cut", "prosciutto_rind", "prosciutto_cut", "provolone_wax", "cheese_cut", "parm_rind",
              "mortadella_cut", "olives_green", "olives_black", "peppers", "mozzarella", "mortadella_casing", "twine", "paper", "salami_fine_cut"]

# ------------------------------------------------------------------ layout v0.2.1 (measured on the v0.1.6 shell)
BOOTH_S0, BOOTH_PITCH, N_BOOTHS = 0.65, 1.85, 3          # 0.2.1: 20 cm closer to the entrance chamfer -> 0.80 m staff pass
BENCH_D = 0.55                                           # bench depth (back face -> cushion front)
BENCH_T = (-1.19, -0.04)                                 # bench length along t (window end .. aisle end)
TABLE_W, TABLE_T = 0.75, (-1.17, -0.10)
COUNTER_FRONT, COUNTER_BACK = SG.COUNTER_FRONT, SG.COUNTER_BACK        # 7.00 / 8.00
CASES_T = SG.CASES_T                                     # [(0.50, 2.60), (2.65, 4.75)]
REGISTER_T, COFFEE_T, GATE_T = SG.REGISTER_T, SG.COFFEE_T, SG.GATE_T
BACK_S, BACK_T = SG.BACK_S, SG.BACK_T
P1_S, P2_T = SG.P1_S, SG.P2_T
SOFFIT = dict(s=(COUNTER_FRONT, COUNTER_BACK), t=(PG.YS, P2_T[0]), z=2.95)
BEAM_S = [-1.10, 0.65, 2.50, 4.35, 6.20]                 # primary beams (run along t)
BEAM_T = [0.0, 3.45]                                     # secondary beams (run along s, between primaries)
PRIMARY = dict(w=0.16, bottom=CEIL - 0.22)
SECONDARY = dict(w=0.13, bottom=CEIL - 0.16)
HERO_BOOTH = 2                                           # booth index of Hero Zone A (nearest the counter)


# Matched camera viewpoints (V-matrix of the art direction V3 §13.2): eye / target in MLO-local metres, FOV 60.
# The SAME table drives the Cycles previews (gs_21) and the in-game scripted camera (/gs_cam in client/debug.lua).
CAM_VIEWS = {
    "V01": ((-1.2, 1.4, 1.65), (6.2, 0.6, 1.35), "hall from the entrance"),
    "V02": ((2.0, 1.2, 1.65), (2.0, 6.9, 1.6), "P2 wall (former blank wall)"),
    "V03": ((5.25, 1.25, 1.62), (5.30, -0.85, 0.95), "hero booth, standing"),
    "V04": ((5.85, -0.62, 1.15), (4.7, -0.62, 0.95), "hero booth, seated eye height"),
    "V05": ((5.2, 1.9, 1.62), (7.6, 1.5, 1.15), "deli counter, customer side"),
    "V06": ((9.0, 3.6, 1.65), (7.4, 1.4, 1.05), "counter, staff side"),
    "V07": ((6.3, 2.2, 1.75), (7.32, 2.6, 2.45), "hanging salumi"),
    "V08": ((3.46, -7.5, 1.6), (3.46, 1.0, 1.2), "storefront W1 from the street"),
    "V11": ((1.0, 4.8, 1.6), (3.6, 0.6, 3.2), "ceiling and fixtures"),
    "V12": ((2.6, 3.3, 1.6), (-1.4, -0.4, 1.3), "entrance D1 from inside"),
    "V12b": ((8.75, 5.9, 1.6), (8.75, 9.0, 1.4), "staff corridor through the P2 door"),
    "VA": ((4.9, 0.9, 1.7), (6.6, -1.2, 1.9), "pier: flag, picture, sconce"),
    "VB": ((6.25, 1.4, 1.45), (7.35, 1.6, 0.95), "deli case close-up"),
    "VC": ((8.55, 2.1, 1.6), (9.55, 1.6, 1.0), "slicer / back counter"),
}


def booth_bays():
    return [BOOTH_S0 + k * BOOTH_PITCH for k in range(N_BOOTHS)]


def table_center(a):
    return (a + BOOTH_PITCH / 2, (TABLE_T[0] + TABLE_T[1]) / 2)


# ================================================================== vector + face helpers
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))


def norm(a):
    l = length(a)
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-12 else (0.0, 0.0, 1.0)


def newell(vs):
    n = [0.0, 0.0, 0.0]
    for i in range(len(vs)):
        c, d = vs[i], vs[(i + 1) % len(vs)]
        n[0] += (c[1] - d[1]) * (c[2] + d[2])
        n[1] += (c[2] - d[2]) * (c[0] + d[0])
        n[2] += (c[0] - d[0]) * (c[1] + d[1])
    return tuple(n)


def F(vs, mat, uvs, hint=None, smooth=False):
    vs, uvs = list(vs), list(uvs)
    n = newell(vs)
    if length(n) < 1e-11:
        return None
    if hint is not None and dot(n, hint) < 0:
        vs.reverse()
        uvs.reverse()
    return {"v": [tuple(round(c, 5) for c in v) for v in vs], "uv": [(round(u, 5), round(w, 5)) for u, w in uvs],
            "mat": MAT[mat] if isinstance(mat, str) else mat, "smooth": bool(smooth)}


def emit(out, f):
    if f is not None:
        out.append(f)


class Frame:
    """Local frame: p(x, y, z) = O + x X + y Y + z Z (axes need not be right-handed)."""

    def __init__(self, O=(0.0, 0.0, 0.0), X=(1.0, 0.0, 0.0), Y=(0.0, 1.0, 0.0), Z=(0.0, 0.0, 1.0)):
        self.O, self.X, self.Y, self.Z = O, X, Y, Z

    def p(self, x, y, z):
        return (self.O[0] + x * self.X[0] + y * self.Y[0] + z * self.Z[0],
                self.O[1] + x * self.X[1] + y * self.Y[1] + z * self.Z[1],
                self.O[2] + x * self.X[2] + y * self.Y[2] + z * self.Z[2])

    def v(self, x, y, z):
        return (x * self.X[0] + y * self.Y[0] + z * self.Z[0], x * self.X[1] + y * self.Y[1] + z * self.Z[1],
                x * self.X[2] + y * self.Y[2] + z * self.Z[2])

    def child(self, x, y, z, yaw=0.0):
        c, s = math.cos(yaw), math.sin(yaw)
        return Frame(self.p(x, y, z), self.v(c, s, 0.0), self.v(-s, c, 0.0), self.Z)

    def tilt_x(self, ang):
        """Rotate about the local X axis (Y towards Z)."""
        c, s = math.cos(ang), math.sin(ang)
        return Frame(self.O, self.X, add(mul(self.Y, c), mul(self.Z, s)), add(mul(self.Z, c), mul(self.Y, -s)))


WORLD = Frame()


def _seed_uv(*key):
    h = hash(tuple(round(k, 3) for k in key)) & 0xFFFFFF
    return ((h % 997) / 997.0, ((h // 997) % 991) / 991.0)


# ------------------------------------------------------------------ 2D polygon triangulation (ear clipping)
def _area2(P):
    return sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P))) / 2.0


def _in_tri(p, a, b, c):
    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    neg = d1 < -1e-12 or d2 < -1e-12 or d3 < -1e-12
    pos = d1 > 1e-12 or d2 > 1e-12 or d3 > 1e-12
    return not (neg and pos)


def triangulate(P):
    n = len(P)
    if n < 3:
        return []
    idx = list(range(n)) if _area2(P) > 0 else list(range(n))[::-1]
    tris, guard = [], 0
    while len(idx) > 3 and guard < 4 * n * n:
        guard += 1
        done = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = P[i0], P[i1], P[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-12:
                continue
            if any(_in_tri(P[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            done = True
            break
        if not done:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


# ================================================================== primitives
def prism(fr, prof, x0, x1, mat, rep=None, smooth=(), caps=(True, True), uoff=None, voff=None, skip_dirs=(),
          nseg=1, deform=None, rep_u=None, grain_u=False):
    """Extrude a closed (y, z) profile along the local X axis of `fr` from x0 to x1.
    smooth: 'all' or set of segment indices (segment i = prof[i] -> prof[i+1]); skip_dirs: local (0, y, z) unit
    directions whose side faces are dropped (e.g. against a wall). deform(x, y, z) -> (y, z) bends the solid
    (nseg subdivisions along X). UV: v along X (wood grain), u around the profile."""
    rep = rep or REP.get(mat, 1.0)
    rep_u = rep_u or rep
    P = list(prof)
    n = len(P)
    if isinstance(smooth, str):
        sm = set(range(n)) if smooth == "all" else set()
    else:
        sm = set(smooth)
    if _area2(P) < 0:
        P = P[::-1]
        sm = {(n - 2 - i) % n for i in sm}
    if uoff is None or voff is None:
        su, sv = _seed_uv(*fr.O, x0, x1, len(P))
        uoff = su if uoff is None else uoff
        voff = sv if voff is None else voff
    xs = [x0 + (x1 - x0) * k / nseg for k in range(nseg + 1)]

    def pt(x, q):
        y, z = (deform(x, q[0], q[1]) if deform else q)
        return fr.p(x, y, z)

    cum = [0.0]
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    out = []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        dy, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dy, dz)
        if L < 1e-9:
            continue
        ny, nz = dz / L, -dy / L
        if any(abs(ny * d[1] + nz * d[2]) > 0.995 and ny * d[1] + nz * d[2] > 0 for d in skip_dirs):
            continue
        ua, ub = cum[i] / rep_u + uoff, cum[i + 1] / rep_u + uoff
        for k in range(nseg):
            xa, xb = xs[k], xs[k + 1]
            va, vb = xa / rep + voff, xb / rep + voff
            vs = [pt(xa, a), pt(xb, a), pt(xb, b), pt(xa, b)]
            uv = [(ua, va), (ua, vb), (ub, vb), (ub, va)] if not grain_u else [(va, ua), (vb, ua), (vb, ub), (va, ub)]
            emit(out, F(vs, mat, uv, hint=fr.v(0.0, ny, nz), smooth=i in sm))
    for x, flag, sgn in ((x0, caps[0], -1.0), (x1, caps[1], 1.0)):
        if not flag:
            continue
        pts = [pt(x, q) for q in P]
        for tri in triangulate(P):
            vs = [pts[j] for j in tri]
            uv = [(P[j][0] / rep + uoff, P[j][1] / rep + voff) for j in tri]
            emit(out, F(vs, mat, uv, hint=fr.v(sgn, 0.0, 0.0)))
    return out


def chamfer_rect(p0, p1, q0, q1, ch):
    if ch <= 0:
        return [(p0, q0), (p1, q0), (p1, q1), (p0, q1)]
    return [(p0 + ch, q0), (p1 - ch, q0), (p1, q0 + ch), (p1, q1 - ch), (p1 - ch, q1), (p0 + ch, q1), (p0, q1 - ch), (p0, q0 + ch)]


def round_rect(p0, p1, q0, q1, r, seg=3, corners=(1, 1, 1, 1)):
    """Rounded rectangle (CCW): corners = radii multipliers for (p0q0, p1q0, p1q1, p0q1)."""
    pts = []
    cs = [((p0, q0), math.pi, 1.5 * math.pi), ((p1, q0), 1.5 * math.pi, 2 * math.pi), ((p1, q1), 0.0, 0.5 * math.pi),
          ((p0, q1), 0.5 * math.pi, math.pi)]
    for (c, a0, a1), m in zip(cs, corners):
        rr = r * m
        if rr <= 1e-6:
            pts.append(c)
            continue
        cx = c[0] + (rr if c[0] == p0 else -rr)
        cy = c[1] + (rr if c[1] == q0 else -rr)
        for k in range(seg + 1):
            a = a0 + (a1 - a0) * k / seg
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _axes(fr, grain):
    if grain == "x":
        return Frame(fr.O, fr.X, fr.Y, fr.Z)
    if grain == "y":
        return Frame(fr.O, fr.Y, fr.Z, fr.X)
    return Frame(fr.O, fr.Z, fr.X, fr.Y)


def cbox(fr, x0, x1, y0, y1, z0, z1, mat, ch=0.0, grain="x", rep=None, smooth=(), skip=(), caps=None):
    """Box with chamfered long edges, extruded along the grain axis. skip: {'-x','+x','-y','+y','-z','+z'} (fr axes)."""
    f2 = _axes(fr, grain)
    if grain == "x":
        a0, a1, prof = x0, x1, chamfer_rect(y0, y1, z0, z1, ch)
    elif grain == "y":
        a0, a1, prof = y0, y1, chamfer_rect(z0, z1, x0, x1, ch)
    else:
        a0, a1, prof = z0, z1, chamfer_rect(x0, x1, y0, y1, ch)
    axis_of = {"x": fr.X, "y": fr.Y, "z": fr.Z}
    dirs, cap = [], [True, True]
    for sname in skip:
        sg = -1.0 if sname[0] == "-" else 1.0
        d = mul(axis_of[sname[1]], sg)
        loc = (dot(d, f2.X), dot(d, f2.Y), dot(d, f2.Z))
        if abs(loc[0]) > 0.99:
            cap[0 if loc[0] < 0 else 1] = False
        else:
            dirs.append(loc)
    if caps is not None:
        cap = [cap[0] and caps[0], cap[1] and caps[1]]
    return prism(f2, prof, a0, a1, mat, rep=rep, smooth=smooth, caps=tuple(cap), skip_dirs=dirs)


def lathe(fr, prof, n, mat, rep=None, tiles_u=1.0, smooth=True, phase=0.0, a0=0.0, a1=2 * math.pi, uv_mode="wrap", cell=None):
    """Surface of revolution about local Z: prof = [(r, z), ...] traversed with the solid on the left
    (outer wall going up -> normal points outward). cell: food-atlas cell name -> UVs inside that cell."""
    rep = rep or REP.get(mat, 1.0)
    out = []
    angs = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    cum = [0.0]
    for j in range(len(prof) - 1):
        cum.append(cum[-1] + math.hypot(prof[j + 1][0] - prof[j][0], prof[j + 1][1] - prof[j][1]))
    tot = cum[-1] or 1.0
    for j in range(len(prof) - 1):
        (r0, z0), (r1, z1) = prof[j], prof[j + 1]
        dr, dz = r1 - r0, z1 - z0
        for i in range(n):
            aa, ab = angs[i] + phase, angs[i + 1] + phase
            ca, sa, cb, sb = math.cos(aa), math.sin(aa), math.cos(ab), math.sin(ab)
            vs = [fr.p(r0 * ca, r0 * sa, z0), fr.p(r0 * cb, r0 * sb, z0), fr.p(r1 * cb, r1 * sb, z1), fr.p(r1 * ca, r1 * sa, z1)]
            if cell:
                uv = [cell_uv(cell, i / n, cum[j] / tot), cell_uv(cell, (i + 1) / n, cum[j] / tot),
                      cell_uv(cell, (i + 1) / n, cum[j + 1] / tot), cell_uv(cell, i / n, cum[j + 1] / tot)]
            else:
                ua, ub = tiles_u * i / n, tiles_u * (i + 1) / n
                uv = [(ua, cum[j] / rep), (ub, cum[j] / rep), (ub, cum[j + 1] / rep), (ua, cum[j + 1] / rep)]
            if r0 < 1e-7:
                vs, uv = vs[1:], uv[1:]
            elif r1 < 1e-7:
                vs, uv = vs[:3], uv[:3]
            am = (aa + ab) / 2
            hint = fr.v(dz * math.cos(am), dz * math.sin(am), -dr)
            emit(out, F(vs, mat, uv, hint=hint, smooth=smooth))
    return out


def disc_cap(fr, r, z, n, mat, up=True, cell=None, phase=0.0):
    """Flat disc (cut faces of salami / cheese) with radial atlas UVs."""
    out = []
    c = fr.p(0, 0, z)
    for i in range(n):
        a, b = phase + 2 * math.pi * i / n, phase + 2 * math.pi * (i + 1) / n
        vs = [c, fr.p(r * math.cos(a), r * math.sin(a), z), fr.p(r * math.cos(b), r * math.sin(b), z)]
        if cell:
            uv = [cell_uv(cell, 0.5, 0.5), cell_uv(cell, 0.5 + 0.47 * math.cos(a), 0.5 + 0.47 * math.sin(a)),
                  cell_uv(cell, 0.5 + 0.47 * math.cos(b), 0.5 + 0.47 * math.sin(b))]
        else:
            uv = [(0.5, 0.5), (0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)), (0.5 + 0.5 * math.cos(b), 0.5 + 0.5 * math.sin(b))]
        emit(out, F(vs, mat, uv, hint=fr.v(0, 0, 1 if up else -1)))
    return out


def grid(fr, fn, nu, nv, mat, uvfn, flip=False, smooth=True, hint_fn=None):
    """Parametric surface fn(u, v) -> local (x, y, z), u, v in [0, 1]; hint_fn(u, v) -> local outward direction."""
    P = [[fr.p(*fn(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    out = []
    for i in range(nu):
        for j in range(nv):
            vs = [P[i][j], P[i + 1][j], P[i + 1][j + 1], P[i][j + 1]]
            uv = [uvfn(i / nu, j / nv), uvfn((i + 1) / nu, j / nv), uvfn((i + 1) / nu, (j + 1) / nv), uvfn(i / nu, (j + 1) / nv)]
            n = cross(sub(P[i + 1][j], P[i][j]), sub(P[i][j + 1], P[i][j]))
            if length(n) < 1e-12:
                n = cross(sub(P[i + 1][j + 1], P[i][j]), sub(P[i][j + 1], P[i + 1][j]))
            if hint_fn is not None:
                n = fr.v(*hint_fn((i + 0.5) / nu, (j + 0.5) / nv))
            emit(out, F(vs, mat, uv, hint=mul(n, -1.0) if flip else n, smooth=smooth))
    return out


def tube(fr, pts, r, n, mat, smooth=True, caps=False, rep=None, cell=None):
    """Tube of radius r along a local polyline (parallel-transport frames)."""
    rep = rep or REP.get(mat, 1.0)
    W = [fr.p(*p) for p in pts]
    m = len(W)
    T = []
    for k in range(m):
        a, b = W[max(0, k - 1)], W[min(m - 1, k + 1)]
        T.append(norm(sub(b, a)))
    up = (0.0, 0.0, 1.0) if abs(T[0][2]) < 0.9 else (1.0, 0.0, 0.0)
    N1 = [norm(cross(T[0], up))]
    for k in range(1, m):
        prev = N1[-1]
        q = sub(prev, mul(T[k], dot(prev, T[k])))
        N1.append(norm(q) if length(q) > 1e-9 else prev)
    rings = []
    for k in range(m):
        n2 = cross(T[k], N1[k])
        rings.append([add(W[k], add(mul(N1[k], r * math.cos(2 * math.pi * i / n)), mul(n2, r * math.sin(2 * math.pi * i / n))))
                      for i in range(n + 1)])
    cum = [0.0]
    for k in range(1, m):
        cum.append(cum[-1] + length(sub(W[k], W[k - 1])))
    out = []
    for k in range(m - 1):
        for i in range(n):
            vs = [rings[k][i], rings[k][i + 1], rings[k + 1][i + 1], rings[k + 1][i]]
            if cell:
                uv = [cell_uv(cell, i / n, (cum[k] / rep) % 1.0), cell_uv(cell, (i + 1) / n, (cum[k] / rep) % 1.0),
                      cell_uv(cell, (i + 1) / n, min(0.999, (cum[k] / rep) % 1.0 + (cum[k + 1] - cum[k]) / rep)),
                      cell_uv(cell, i / n, min(0.999, (cum[k] / rep) % 1.0 + (cum[k + 1] - cum[k]) / rep))]
            else:
                uv = [(i / n, cum[k] / rep), ((i + 1) / n, cum[k] / rep), ((i + 1) / n, cum[k + 1] / rep), (i / n, cum[k + 1] / rep)]
            mid = mul(add(add(vs[0], vs[1]), add(vs[2], vs[3])), 0.25)
            emit(out, F(vs, mat, uv, hint=sub(mid, mul(add(W[k], W[k + 1]), 0.5)), smooth=smooth))
    if caps:
        for k, sg in ((0, -1.0), (m - 1, 1.0)):
            ring = rings[k][:n]
            for i in range(n):
                vs = [W[k], ring[i], ring[(i + 1) % n]]
                emit(out, F(vs, mat, [(0.5, 0.5)] * 3, hint=mul(T[k], sg)))
    return out


def cell_uv(name, u, v, inset=0.02):
    i = FOOD_CELLS.index(name)
    r, c = divmod(i, 4)
    u = min(max(u, 0.0), 1.0)
    v = min(max(v, 0.0), 1.0)
    return ((c + inset + (1 - 2 * inset) * u) / 4.0, 1.0 - (r + inset + (1 - 2 * inset) * v) / 4.0)


# ================================================================== 1. WALL JOINERY KIT
BASE_H = 0.165
CAP_TOP = 1.00
PICTURE_Z = 2.70


def wall_frame(start2, d2, n2):
    return Frame((start2[0], start2[1], 0.0), (d2[0], d2[1], 0.0), (n2[0], n2[1], 0.0), (0.0, 0.0, 1.0))


def baseboard(fr, u0, u1):
    z = FLOOR
    prof = [(0, z), (0.028, z), (0.028, z + 0.008), (0.025, z + 0.020), (0.018, z + 0.028), (0.018, z + 0.128),
            (0.021, z + 0.136), (0.025, z + 0.148), (0.022, z + 0.158), (0.014, z + BASE_H), (0, z + BASE_H)]
    return prism(fr, prof, u0, u1, "walnut", smooth={2, 3, 5, 6, 7, 8}, skip_dirs=[(0.0, -1.0, 0.0)])


def raised_panel(fr, a0, a1, b0, b1, y_back=0.009, y_top=0.017, inset=0.038, grain="z"):
    """Raised (fielded) panel between frame members: bevelled border + flat field, crisp highlight lines."""
    out = []
    o = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
    i = [(a0 + inset, b0 + inset), (a1 - inset, b0 + inset), (a1 - inset, b1 - inset), (a0 + inset, b1 - inset)]
    su, sv = _seed_uv(*fr.O, a0, b0)

    def uv(p):
        return ((p[0] + su) / REP["walnut"], (p[1] + sv) / REP["walnut"]) if grain == "x" else \
            ((p[0] + su) / REP["walnut"] * 1.0, (p[1] + sv) / REP["walnut"])
    for k in range(4):
        q = [o[k], o[(k + 1) % 4], i[(k + 1) % 4], i[k]]
        vs = [fr.p(q[0][0], y_back, q[0][1]), fr.p(q[1][0], y_back, q[1][1]), fr.p(q[2][0], y_top, q[2][1]), fr.p(q[3][0], y_top, q[3][1])]
        emit(out, F(vs, "walnut", [uv(p) for p in q], hint=fr.v(0, 1, 0)))
    emit(out, F([fr.p(p[0], y_top, p[1]) for p in i], "walnut", [uv(p) for p in i], hint=fr.v(0, 1, 0)))
    return out


def wainscot(fr, u0, u1, top, panel_w=0.60, stile=0.075, depth=0.020):
    """Frame-and-panel wainscot between u0 and u1 (wall-local), bottom rail on the baseboard, top rail under `top`."""
    out = []
    zb0 = FLOOR + BASE_H
    zb1 = zb0 + 0.095
    if top >= 0.9:
        zt1 = top - 0.058
        zt0 = zt1 - 0.085
    else:
        zt1 = top
        zt0 = top - 0.070
    L = u1 - u0
    nb = max(1, int(round((L - stile) / (panel_w + stile))))
    bay = (L - stile * (nb + 1)) / nb
    if bay < 0.12:
        nb, bay = 1, L - 2 * stile
    out += cbox(fr, u0, u1, 0.0, depth, zb0, zb1, "walnut", ch=0.004, grain="x", skip=("-y",))
    out += cbox(fr, u0, u1, 0.0, depth, zt0, zt1, "walnut", ch=0.004, grain="x", skip=("-y",))
    for k in range(nb + 1):
        x = u0 + k * (bay + stile)
        out += cbox(fr, x, x + stile, 0.0, depth, zb1, zt0, "walnut", ch=0.004, grain="z", skip=("-y",), caps=(False, False))
    for k in range(nb):
        a0 = u0 + stile + k * (bay + stile)
        out += raised_panel(fr, a0, a0 + bay, zb1, zt0)
    return out


def cap_rail(fr, u0, u1, top=CAP_TOP):
    prof = [(0, top - 0.058), (0.024, top - 0.058), (0.030, top - 0.052), (0.036, top - 0.040), (0.037, top - 0.022),
            (0.032, top - 0.008), (0.022, top), (0, top)]
    return prism(fr, prof, u0, u1, "walnut", smooth={1, 2, 3, 4, 5}, skip_dirs=[(0.0, -1.0, 0.0)])


def picture_rail(fr, u0, u1, z=PICTURE_Z):
    prof = [(0, z), (0.012, z), (0.020, z + 0.010), (0.024, z + 0.024), (0.020, z + 0.038), (0, z + 0.045)]
    return prism(fr, prof, u0, u1, "walnut", smooth={1, 2, 3}, skip_dirs=[(0.0, -1.0, 0.0)])


def cornice(fr, u0, u1):
    """Cove cornice at the wall/ceiling junction (painted cream, plaster texture)."""
    C = CEIL
    cove = [(0.11 + 0.08 * math.cos(math.radians(a)), C - 0.12 + 0.08 * math.sin(math.radians(a))) for a in (180, 157.5, 135, 112.5, 90)]
    prof = [(0, C - 0.155), (0.014, C - 0.155), (0.014, C - 0.135), (0.03, C - 0.125)] + cove + [(0.135, C - 0.04), (0.135, C - 0.002), (0, C - 0.002)]
    return prism(fr, prof, u0, u1, "plaster", smooth={3, 4, 5, 6, 7}, skip_dirs=[(0.0, -1.0, 0.0), (0.0, 0.0, 1.0)])


def wall_runs():
    """Hall walls (wall frame, [(u0, u1, 'full'|'sill')], (u_crown0, u_crown1))."""
    W, cw = PG.W1, PG.CASING_W
    out = []
    # SW (storefront) wall: from the chamfer corner to the counter front
    fr = wall_frame(PG.P_SW, (1.0, 0.0), (0.0, 1.0))
    u = lambda s: s - PG.P_SW[0]
    out.append((fr, [(0.0, u(W["s"][0] - cw), "full"), (u(W["s"][0] - cw), u(W["s"][1] + cw), "sill"),
                     (u(W["s"][1] + cw), u(P1_S[0]), "full")], (0.0, u(P1_S[0]))))
    # chamfer with D1
    a_nw, a_sw = PG.A_NW, PG.A_SW
    ch_dir = (PG.P_SW[0] - PG.P_NW[0], PG.P_SW[1] - PG.P_NW[1])
    L = math.hypot(*ch_dir)
    d2 = (ch_dir[0] / L, ch_dir[1] / L)
    n2 = (-d2[1], d2[0]) if (-d2[1] * 1.0 + d2[0] * 1.0) > 0 else (d2[1], -d2[0])     # into the room (towards +s,+t)
    fr = wall_frame(PG.P_NW, d2, n2)
    h0, h1 = a_nw - PG.D1["a"][1], a_nw - PG.D1["a"][0]
    out.append((fr, [(0.0, h0 - cw, "full"), (h1 + cw, L, "full")], (0.0, L)))
    # NW (side) wall with W2: u = YN - t, hall part t in [P_NW.t, P2]
    W2 = PG.W2
    fr = wall_frame((PG.XW, PG.YN), (0.0, -1.0), (1.0, 0.0))
    u = lambda t: PG.YN - t
    out.append((fr, [(u(P2_T[0]), u(W2["t"][1] + cw), "full"), (u(W2["t"][1] + cw), u(W2["t"][0] - cw), "sill"),
                     (u(W2["t"][0] - cw), u(PG.P_NW[1]), "full")], (u(P2_T[0]), u(PG.P_NW[1]))))
    # P2 hall face (the former blank wall): s from XW to the counter
    fr = wall_frame((PG.XW, P2_T[0]), (1.0, 0.0), (0.0, -1.0))
    out.append((fr, [(0.0, SG.P2_DOOR[0] - cw - PG.XW, "full"), (SG.P2_DOOR[1] + cw - PG.XW, P1_S[0] - PG.XW, "full")],
                (0.0, P1_S[0] - PG.XW)))
    return out


def wall_kit_faces():
    out = []
    for fr, runs, (c0, c1) in wall_runs():
        for u0, u1, kind in runs:
            if u1 - u0 < 0.05:
                continue
            out += baseboard(fr, u0, u1)
            if kind == "full":
                out += wainscot(fr, u0, u1, CAP_TOP)
                out += cap_rail(fr, u0, u1)
            else:
                out += wainscot(fr, u0, u1, 0.49, panel_w=0.70)
        out += picture_rail(fr, runs[0][0], runs[-1][1])
        out += cornice(fr, c0, c1)
    return out


# ================================================================== 2. CEILING: beams, soffit, fixtures
def chamfer_s_at(t):
    """s of the inner chamfer face at height t (line P_SW -> P_NW)."""
    (s0, t0), (s1, t1) = PG.P_SW, PG.P_NW
    return s0 + (t - t0) * (s1 - s0) / (t1 - t0)


def chamfer_t_at(s):
    (s0, t0), (s1, t1) = PG.P_SW, PG.P_NW
    return t0 + (s - s0) * (t1 - t0) / (s1 - s0)


def ceiling_faces():
    out = []
    W = WORLD
    pw, sw = PRIMARY["w"] / 2, SECONDARY["w"] / 2
    for s in BEAM_S:
        t0 = PG.YS if s >= PG.P_SW[0] else chamfer_t_at(s) - 0.05
        out += cbox(W, s - pw, s + pw, t0, P2_T[0], PRIMARY["bottom"], CEIL, "walnut", ch=0.012, grain="y", skip=("+z",))
    # secondary beams between primaries (butt joints, shallower)
    edges = sorted(BEAM_S)
    for t in BEAM_T:
        s_start = max(PG.XW, chamfer_s_at(t) - 0.05) if t < PG.P_NW[1] else PG.XW
        stops = [s_start] + edges + [SOFFIT["s"][0]]
        for a, b in zip(stops[:-1], stops[1:]):
            a1 = a + (pw if a in edges else 0.0)
            b1 = b - (pw if b in edges else 0.0)
            if b1 - a1 > 0.1:
                out += cbox(W, a1, b1, t - sw, t + sw, SECONDARY["bottom"], CEIL, "walnut", ch=0.010, grain="x", skip=("+z",))
    # counter soffit (bulkhead): plaster underside + walnut fascia with a small cornice
    s0, s1 = SOFFIT["s"]
    t0, t1 = SOFFIT["t"]
    z = SOFFIT["z"]
    out += cbox(W, s0, s1, t0, t1, z, CEIL, "plaster", ch=0.0, grain="y", skip=("+z",), caps=(False, False))
    out += cbox(W, s0 - 0.03, s0 + 0.002, t0, t1, z - 0.02, z + 0.22, "walnut", ch=0.006, grain="y", caps=(False, False))
    out += cbox(W, s0 - 0.045, s0 + 0.002, t0, t1, z + 0.22, z + 0.255, "walnut", ch=0.008, grain="y", caps=(False, False))
    return out


def pendant_fixture(s, t, z_shade_bottom=2.12):
    """Opal schoolhouse pendant: brass canopy + rod + fitter, opal glass bell (emissive), warm bulb."""
    out = []
    fr = WORLD.child(s, t, 0.0)
    out += lathe(fr, [(0.0, CEIL - 0.035), (0.065, CEIL - 0.035), (0.07, CEIL - 0.02), (0.06, CEIL - 0.002), (0.0, CEIL - 0.002)][::-1], 16, "brass")
    top = z_shade_bottom + 0.30
    out += lathe(fr, [(0.009, CEIL - 0.035), (0.009, top + 0.075)][::-1], 8, "brass")
    out += lathe(fr, [(0.0, top + 0.075), (0.028, top + 0.075), (0.032, top + 0.05), (0.05, top + 0.03), (0.058, top), (0.0, top)][::-1], 16, "brass")
    bell = [(0.052, top), (0.052, top - 0.035), (0.075, top - 0.06), (0.115, top - 0.11), (0.142, top - 0.17), (0.152, top - 0.225),
            (0.148, top - 0.265), (0.13, top - 0.29), (0.118, top - 0.30)]
    out += lathe(fr, bell, 20, "opal", smooth=True)
    out += lathe(fr, [(p[0] - 0.004, p[1]) for p in bell][::-1], 20, "opal", smooth=True)      # inner face
    out += lathe(fr, [(0.0, top - 0.10), (0.03, top - 0.11), (0.032, top - 0.15), (0.0, top - 0.17)][::-1], 10, "glow")
    return out, (s, t, top - 0.14)


def flush_dome(s, t):
    out = []
    fr = WORLD.child(s, t, 0.0)
    out += lathe(fr, [(0.0, CEIL - 0.003), (0.19, CEIL - 0.003), (0.19, CEIL - 0.018), (0.175, CEIL - 0.03), (0.0, CEIL - 0.03)], 24, "brass")
    dome = [(0.172, CEIL - 0.03)] + [(0.172 * math.cos(math.radians(a)), CEIL - 0.03 - 0.10 * math.sin(math.radians(a))) for a in (20, 40, 60, 75, 90)]
    out += lathe(fr, dome, 24, "opal")
    out += lathe(fr, [(0.0, CEIL - 0.13), (0.012, CEIL - 0.136), (0.0, CEIL - 0.14)], 8, "brass")      # finial
    return out, (s, t, CEIL - 0.24)


def recessed_can(s, t, z):
    out = []
    fr = WORLD.child(s, t, 0.0)
    out += lathe(fr, [(0.05, z - 0.004), (0.078, z - 0.004), (0.078, z + 0.001), (0.05, z + 0.001)][::-1], 16, "brass")
    out += lathe(fr, [(0.0, z + 0.004), (0.05, z + 0.004), (0.05, z - 0.004)][::-1], 16, "steel")
    out += disc_cap(fr, 0.035, z - 0.001, 12, "glow", up=False)
    return out


# ---------------------------------------------------------------- 0.2.2 light rig (own values, see docs/research/LIGHTING_METHODS.md)
# Methods (learned, not copied): one physical fixture = a KEY spot with shadows + a weak FILL / bounce without shadows,
# visible bulbs get CORONA-ONLY lights, fills skip specular + reflections, few shadow casters, fade distances for perf.
LIGHT_FLAGS = ["interior_only", "exterior_only", "dont_use_in_cutscene", "vehicle", "ignore_light_state", "texture_projection",
               "cast_shadows", "static_shadows", "dynamic_shadows", "calc_from_sun", "enable_buzzing", "force_buzzing",
               "draw_volume", "no_specular", "both_int_and_ext", "corona_only", "not_in_reflection", "only_in_reflection",
               "enable_culling_plane", "enable_vol_outer_color", "higher_res_shadows", "only_low_res_shadows", "far_lod_light",
               "dont_light_alpha", "cast_shadows_if_possible", "cutscene", "moving_light_source", "use_vehicle_twin",
               "force_medium_lod_light", "corona_only_lod_light", "delayed_render", "already_tested_for_occlusion"]
KEY_FLAGS = ("static_shadows", "dynamic_shadows", "not_in_reflection")
FILL_FLAGS = ("no_specular", "not_in_reflection")
C_TUNGSTEN = (1.0, 0.78, 0.55)      # ~2700 K practicals
C_FILL = (0.96, 0.80, 0.62)         # slightly desaturated warm fill
C_AMBER = (1.0, 0.64, 0.36)         # ~2200 K festoon / sconce bulbs
C_CASE = (1.0, 0.93, 0.84)          # deli case strip: neutral so the food reads
FADE = (35, 18, 20)                 # light / shadow / specular fade distances (m)


def flags_total(names):
    return sum(1 << LIGHT_FLAGS.index(n) for n in names)


def LT(kind, typ, pos, color, I, R, exp, aim=(0.0, 0.0, -1.0), cone=(0.0, 0.0), flags=(), corona=(0.0, 0.0), fade=FADE):
    n = math.sqrt(sum(a * a for a in aim)) or 1.0
    return dict(kind=kind, type=typ, pos=tuple(round(c, 4) for c in pos), dir=tuple(a / n for a in aim), color=color,
                intensity=I, falloff=R, exponent=exp, cone_out=cone[0], cone_in=cone[1], flags=tuple(flags),
                corona_size=corona[0], corona_int=corona[1], fade=fade)


def CORONA(kind, pos, color, size, inten, I=6.0):
    """Corona-only light: draws the bulb glare/glow, lights nothing (cheap; visible from the street)."""
    return LT(kind, "POINT", pos, color, I, 0.4, 8.0, flags=("corona_only", "not_in_reflection"), corona=(size, inten),
              fade=(60, 0, 0))


ROOM_TIMECYCLE = "lp_longpig_hall"   # own timecycle modifier, defined in stream/lp_timecycle.xml (values: LONG_PIG_LIGHT_PLOT.md)


def cpv_hall(v):
    """0.2.2 vertex colours: R = natural ambient (near openings, as before), G = artificial ambient with a baked gradient:
    contact darkening at the floor, full on the walls at eye height, falling off towards the ceiling so the practical
    pools read on a darker ceiling; booth seat recesses a little darker. B unused, A opaque. Values are our own."""
    r, _, _, _ = PG.cpv_shell(v)
    s, t, z = v
    if z < 0.30:
        g = 0.27 + 0.07 * (z / 0.30)
    elif z < 2.20:
        g = 0.34
    else:
        g = 0.34 - 0.15 * min(1.0, (z - 2.20) / 1.20)
    if t < -0.50 and z < 1.25 and s < BEAM_S[4]:
        g *= 0.88
    return (round(r, 3), round(g, 3), 0.0, 1.0)


def ceiling_fixtures():
    """-> faces, lights (dicts), vanilla (name, s, t, z_bottom, yaw)."""
    out, lights, van = [], [], []
    for a in booth_bays():                                   # Zone A key: booth pendants over the tables
        sc, tc = table_center(a)
        f, lp = pendant_fixture(sc, tc + 0.05)
        out += f
        lights.append(LT("booth_pendant_key", "SPOT", lp, C_TUNGSTEN, 8.0, 3.0, 16.0, cone=(55.0, 25.0), flags=KEY_FLAGS))
        lights.append(LT("booth_pendant_bounce", "POINT", (lp[0], lp[1], lp[2] + 0.26), C_FILL, 0.8, 1.2, 4.0, flags=FILL_FLAGS))
    t_mid = (BEAM_T[0] + BEAM_T[1]) / 2
    t_far = (BEAM_T[1] + P2_T[0]) / 2
    bays_s = [(-2.9, BEAM_S[0]), (BEAM_S[0], BEAM_S[1]), (BEAM_S[1], BEAM_S[2]), (BEAM_S[2], BEAM_S[3]), (BEAM_S[3], BEAM_S[4])]
    fans = {(BEAM_S[1], BEAM_S[2]), (BEAM_S[3], BEAM_S[4])}
    for a, b in bays_s:
        sc = (a + b) / 2
        if (a, b) in fans:
            van.append(("bkr_prop_biker_ceiling_fan_base", sc, t_mid, CEIL - 1.009, 0.0))
            lights.append(LT("fan_fill", "POINT", (sc, t_mid, 2.32), C_FILL, 0.9, 3.8, 6.0, flags=FILL_FLAGS))
            lights.append(CORONA("fan_glass", (sc, t_mid, 2.34), C_TUNGSTEN, 0.30, 0.5))
        elif a > -2.0:
            f, lp = flush_dome(sc, t_mid)
            out += f
            lights.append(LT("dome_fill", "POINT", lp, C_FILL, 0.6, 3.8, 6.0, flags=FILL_FLAGS))
        f, lp = flush_dome(sc, t_far)
        out += f
        lights.append(LT("dome_fill", "POINT", lp, C_FILL, 0.6, 3.8, 6.0, flags=FILL_FLAGS))
    # entrance bay (chamfer side, t 0.57 .. 3.45 at s < -1.10)
    f, lp = flush_dome(-2.05, 2.75)
    out += f
    lights.append(LT("dome_fill", "POINT", lp, C_FILL, 0.7, 3.8, 6.0, flags=FILL_FLAGS))
    # Zone B key: queue bay in front of the counter, two enamel deli pendants (vanilla) with visible bulbs
    for t in ((CASES_T[0][0] + CASES_T[0][1]) / 2, (CASES_T[1][0] + CASES_T[1][1]) / 2):
        sq = (BEAM_S[4] + COUNTER_FRONT) / 2 + 0.02
        van.append(("bkr_prop_biker_pendant_light", sq, t, CEIL - 1.284, 0.0))
        lights.append(LT("queue_pendant_key", "SPOT", (sq, t, 2.02), C_TUNGSTEN, 7.0, 3.2, 14.0, cone=(58.0, 26.0), flags=KEY_FLAGS))
        lights.append(CORONA("queue_bulb", (sq, t, 2.04), C_TUNGSTEN, 0.45, 0.8))
    # soffit cans over the cases / register: narrow accents (no shadows), small corona on the trim disc
    for t in (1.05, 2.05, 3.20, 4.20, 5.10, 6.15):
        out += recessed_can(7.55, t, SOFFIT["z"])
        lights.append(LT("soffit_can", "SPOT", (7.55, t, SOFFIT["z"] - 0.03), (1.0, 0.86, 0.68), 5.0, 2.4, 16.0, cone=(36.0, 14.0),
                         flags=("not_in_reflection",), corona=(0.12, 0.35)))
    # staff aisle / back counter work light (hidden fill under the soffit edge)
    lights.append(LT("staff_fill", "POINT", (8.85, 3.40, 2.85), C_FILL, 0.7, 3.5, 6.0, flags=FILL_FLAGS))
    return out, lights, van


def festoon_runs():
    """String-light runs at the window heads (inside): (start, end, sag, n_bulbs). W1 on the SW wall, W2 on the NW wall."""
    zt = PG.W1["z"][1] + 0.16
    s0, s1 = PG.W1["s"][0] - 0.18, PG.W1["s"][1] + 0.18
    t0, t1 = PG.W2["t"][0] - 0.18, PG.W2["t"][1] + 0.18
    return [((s0, PG.YS + 0.09, zt), (s1, PG.YS + 0.09, zt), 0.11, 13),
            ((PG.XW + 0.09, t0, zt), (PG.XW + 0.09, t1, zt), 0.09, 9)]


def _sag(a, b, sag, u):
    return tuple(a[k] + (b[k] - a[k]) * u for k in range(3))[:2] + (a[2] + (b[2] - a[2]) * u - 4.0 * sag * u * (1.0 - u),)


def festoon_faces_lights():
    out, L = [], []
    for ri, (a, b, sag, n) in enumerate(festoon_runs()):
        pts = [_sag(a, b, sag, i / 24) for i in range(25)]
        out += tube(WORLD, pts, 0.0035, 5, "iron", smooth=True)
        for end in (a, b):                                   # cup hooks
            out += cbox(WORLD, end[0] - 0.008, end[0] + 0.008, end[1] - 0.008, end[1] + 0.008, end[2] - 0.004, end[2] + 0.03, "brass")
        for i in range(n):
            u = (i + 0.5) / n
            p = _sag(a, b, sag, u)
            fr = WORLD.child(p[0], p[1], p[2] - 0.004)
            out += lathe(fr, [(0.0, -0.030), (0.0085, -0.029), (0.0085, -0.004), (0.0, -0.003)], 8, "iron")       # socket
            globe = [(0.0, -0.078)] + [(0.021 * math.sin(math.radians(x)), -0.056 - 0.021 * math.cos(math.radians(x)))
                                        for x in (30, 60, 90, 120, 150)] + [(0.0, -0.031)]
            out += lathe(fr, globe, 10, "glow", smooth=True)
            L.append(CORONA("festoon_bulb", (p[0], p[1], p[2] - 0.06), C_AMBER, 0.22, 1.2))
        for u in ((0.28, 0.72) if n > 10 else (0.5,)):        # a few real (weak) lights so the string glows on the wall
            p = _sag(a, b, sag, u)
            L.append(LT("festoon_glow", "POINT", (p[0] + (0.05 if ri == 1 else 0.0), p[1] + (0.05 if ri == 0 else 0.0), p[2] - 0.08),
                        C_AMBER, 0.8, 2.2, 6.0,
                        flags=FILL_FLAGS))
    return out, L


# ================================================================== 3. BOOTHS
def bench(fr, L, back_detail=False):
    """Bench unit in local frame: x along the length (0..L), y from the back face (0) to the cushion front (BENCH_D), z up.
    Channel-tufted padded back, two crowned seat cushions with piping, walnut seat box / back shell / cap / end caps."""
    out = []
    D = BENCH_D
    zf = FLOOR
    # plinth (recessed toe kick) + seat box
    out += cbox(fr, 0.02, L - 0.02, 0.07, D - 0.06, zf, zf + 0.09, "walnut", ch=0.003, grain="x", skip=("-z",))
    out += cbox(fr, 0.0, L, 0.03, D - 0.035, zf + 0.09, 0.40, "walnut", ch=0.0, grain="x", skip=("-z", "+z", "-x", "+x"))
    # seat front: frame and panel
    fy = Frame(fr.p(0, D - 0.035, 0), fr.X, fr.Y, fr.Z)
    out += cbox(fy, 0.0, L, 0.0, 0.02, zf + 0.09, zf + 0.165, "walnut", ch=0.004, grain="x", skip=("-y",))
    out += cbox(fy, 0.0, L, 0.0, 0.02, 0.335, 0.40, "walnut", ch=0.004, grain="x", skip=("-y",))
    nst = 3 if L > 0.9 else 2
    sw = 0.07
    bay = (L - sw * nst) / (nst - 1)
    for k in range(nst):
        x = k * (bay + sw)
        out += cbox(fy, x, x + sw, 0.0, 0.02, zf + 0.165, 0.335, "walnut", ch=0.004, grain="z", skip=("-y",), caps=(False, False))
    for k in range(nst - 1):
        a0 = sw + k * (bay + sw)
        out += raised_panel(fy, a0, a0 + bay, zf + 0.165, 0.335, inset=0.03)
    # back shell
    out += cbox(fr, 0.0, L, 0.0, 0.035, zf + 0.09, 1.045, "walnut", ch=0.0, grain="x", skip=("-x", "+x", "+z"))
    if back_detail:   # exposed back (end benches): frame and panel facing -y
        fb = Frame(fr.p(L, 0.0, 0.0), mul(fr.X, -1.0), mul(fr.Y, -1.0), fr.Z)
        out += cbox(fb, 0.0, L, 0.0, 0.018, zf + 0.09, zf + 0.20, "walnut", ch=0.004, grain="x", skip=("-y",))
        out += cbox(fb, 0.0, L, 0.0, 0.018, 0.93, 1.045, "walnut", ch=0.004, grain="x", skip=("-y",))
        for k in range(nst):
            x = k * (bay + sw)
            out += cbox(fb, x, x + sw, 0.0, 0.018, zf + 0.20, 0.93, "walnut", ch=0.004, grain="z", skip=("-y",), caps=(False, False))
        for k in range(nst - 1):
            a0 = sw + k * (bay + sw)
            out += raised_panel(fb, a0, a0 + bay, zf + 0.20, 0.93, inset=0.04)
    # seat cushions (rounded profile, crowned, piped front edge)
    zc0, zc1 = 0.398, 0.472
    prof = round_rect(0.075, D + 0.012, zc0, zc1, 0.03, seg=4, corners=(0.3, 0.4, 1.0, 0.5))
    half = L / 2
    for xa, xb in ((0.035, half - 0.004), (half + 0.004, L - 0.035)):
        def crown(x, y, z, xa=xa, xb=xb):
            u = (x - xa) / (xb - xa)
            k = math.sin(math.pi * u) ** 0.6
            h = (z - zc0) / (zc1 - zc0)
            return (y + 0.006 * k * max(0.0, (y - 0.3) / 0.27), z + 0.011 * k * h * min(1.0, (D + 0.01 - y) / 0.06 + 0.2))
        out += prism(fr, prof, xa, xb, "leather", rep=REP["leather"], smooth="all", nseg=8, deform=crown, caps=(True, True))
        pts = []
        for k in range(9):
            x = xa + (xb - xa) * k / 8
            y, z = crown(x, D + 0.003, zc1 - 0.006)
            pts.append((x, y, z))
        out += tube(fr, pts, 0.0055, 6, "leather")
    # back: leather backing plane + channel pillows
    b0 = (0.105, 0.474)            # bottom edge (y, z) of the back cushion
    b1 = (0.050, 1.030)            # top edge
    ax = (b1[0] - b0[0], b1[1] - b0[1])
    al = math.hypot(*ax)
    nrm = (ax[1] / al, -ax[0] / al)       # into the seat side (+y, slight -z)
    if nrm[0] < 0:
        nrm = (-nrm[0], -nrm[1])
    emit(out, F([fr.p(0.0, b0[0] - 0.01, b0[1]), fr.p(L, b0[0] - 0.01, b0[1]), fr.p(L, b1[0] - 0.01, b1[1]), fr.p(0.0, b1[0] - 0.01, b1[1])],
                "leather", [(0, 0), (L / REP["leather"], 0), (L / REP["leather"], al / REP["leather"]), (0, al / REP["leather"])],
                hint=fr.v(0, nrm[0], nrm[1])))
    nch = max(3, int(round(L / 0.27)))
    cw = L / nch
    for k in range(nch):
        xa, xb = k * cw + 0.004, (k + 1) * cw - 0.004
        su, sv = _seed_uv(k, L)

        def pillow(u, v, xa=xa, xb=xb):
            bulge = 0.004 + 0.046 * (math.sin(math.pi * u) ** 0.55) * (math.sin(math.pi * v) ** 0.32)
            yb, zb = b0[0] + ax[0] * v, b0[1] + ax[1] * v
            return (xa + (xb - xa) * u, yb + nrm[0] * bulge, zb + nrm[1] * bulge)
        out += grid(fr, pillow, 6, 12, "leather", lambda u, v, xa=xa, xb=xb, su=su, sv=sv:
                    ((xa + (xb - xa) * u) / REP["leather"] + su, v * al / REP["leather"] + sv),
                    hint_fn=lambda u, v: (0.0, nrm[0], nrm[1]))
    # top cap rail (rounded)
    cap = [(-0.012, 1.040), (0.080, 1.040), (0.080, 1.068), (0.071, 1.090), (0.050, 1.102), (0.010, 1.102), (-0.006, 1.094), (-0.012, 1.080)]
    out += prism(fr, cap, -0.035, L + 0.035, "walnut", smooth={2, 3, 4, 5, 6})
    # end caps (side panels) with a raised panel on the outside
    side = [(-0.015, zf), (D + 0.015, zf), (D + 0.015, 0.50), (D - 0.005, 0.535), (D - 0.05, 0.553), (0.22, 0.582),
            (0.155, 0.612), (0.118, 0.68), (0.10, 1.04), (-0.015, 1.04)]
    for x0, x1, outward in ((-0.035, 0.0, -1.0), (L, L + 0.035, 1.0)):
        out += prism(fr, side, x0, x1, "walnut", caps=(True, True))
        xo = x0 if outward < 0 else x1
        fo = Frame(fr.p(xo, 0.0, 0.0), fr.Y, mul(fr.X, outward), fr.Z)
        out += raised_panel(fo, 0.05, D - 0.04, zf + 0.11, 0.45, y_back=0.0, y_top=0.008, inset=0.03)
    return out


def booth_table(sc, t0, t1):
    """Terrazzo top in a bull-nosed walnut band, cast-iron pedestal."""
    out = []
    W = WORLD
    s0, s1 = sc - TABLE_W / 2, sc + TABLE_W / 2
    zt = 0.768
    band = 0.045
    edge = [(-band, zt - 0.033), (-0.005, zt - 0.033), (0.0, zt - 0.026), (0.003, zt - 0.016), (0.0, zt - 0.006), (-0.005, zt), (-band, zt)]
    # long sides along t (full length), short sides along s between them (butt joints, like the real thing)
    for sgn, s_edge in ((-1.0, s0), (1.0, s1)):
        fr = Frame((s_edge, 0.0, 0.0), (0.0, 1.0, 0.0), (sgn, 0.0, 0.0), (0.0, 0.0, 1.0))
        out += prism(fr, edge, t0, t1, "walnut", smooth={1, 2, 3, 4})
    for sgn, t_edge in ((-1.0, t0), (1.0, t1)):
        fr = Frame((0.0, t_edge, 0.0), (1.0, 0.0, 0.0), (0.0, sgn, 0.0), (0.0, 0.0, 1.0))
        out += prism(fr, edge, s0 + band, s1 - band, "walnut", smooth={1, 2, 3, 4}, caps=(False, False))
    out += cbox(W, s0 + band, s1 - band, t0 + band, t1 - band, zt - 0.030, zt - 0.001, "terrazzo", grain="x", skip=("-z",))
    out += cbox(W, s0 + 0.02, s1 - 0.02, t0 + 0.02, t1 - 0.02, zt - 0.05, zt - 0.033, "walnut", grain="x")
    ped = [(0.0, FLOOR), (0.235, FLOOR), (0.238, FLOOR + 0.012), (0.215, FLOOR + 0.024), (0.12, FLOOR + 0.042), (0.06, FLOOR + 0.07),
           (0.042, FLOOR + 0.11), (0.036, FLOOR + 0.16), (0.034, zt - 0.12), (0.042, zt - 0.10), (0.085, zt - 0.075),
           (0.11, zt - 0.062), (0.11, zt - 0.05), (0.0, zt - 0.05)]
    out += lathe(WORLD.child(sc, (t0 + t1) / 2 + 0.08, 0.0), ped, 20, "iron", rep=0.5, tiles_u=2.0)
    # wall cleat under the window end
    out += cbox(W, s0 + 0.10, s1 - 0.10, PG.YS + 0.03, t0 + 0.06, zt - 0.09, zt - 0.05, "walnut", ch=0.004, grain="x")
    return out


def booths_faces():
    out = []
    L = BENCH_T[1] - BENCH_T[0]
    for k, a in enumerate(booth_bays()):
        # bench A: back at s = a, faces +s ; bench B: back at s = a + pitch, faces -s
        frA = Frame((a, BENCH_T[0], 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        frB = Frame((a + BOOTH_PITCH, BENCH_T[1], 0.0), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        out += bench(frA, L, back_detail=(k == 0))
        out += bench(frB, L, back_detail=(k == N_BOOTHS - 1))
        sc, _ = table_center(a)
        out += booth_table(sc, TABLE_T[0], TABLE_T[1])
    return out


def booth_collision_boxes():
    out = []
    for a in booth_bays():
        out.append(((a, BENCH_T[0] - 0.035, FLOOR), (a + BENCH_D, BENCH_T[1] + 0.035, 0.47), "LEATHER"))
        out.append(((a, BENCH_T[0] - 0.035, FLOOR), (a + 0.12, BENCH_T[1] + 0.035, 1.10), "WOOD_SOLID_MEDIUM"))
        b = a + BOOTH_PITCH
        out.append(((b - BENCH_D, BENCH_T[0] - 0.035, FLOOR), (b, BENCH_T[1] + 0.035, 0.47), "LEATHER"))
        out.append(((b - 0.12, BENCH_T[0] - 0.035, FLOOR), (b, BENCH_T[1] + 0.035, 1.10), "WOOD_SOLID_MEDIUM"))
        sc, _ = table_center(a)
        out.append(((sc - TABLE_W / 2, TABLE_T[0], 0.72), (sc + TABLE_W / 2, TABLE_T[1], 0.77), "WOOD_SOLID_MEDIUM"))
        out.append(((sc - 0.05, -0.68, FLOOR), (sc + 0.05, -0.52, 0.72), "METAL_SOLID_SMALL"))
    return out


# ================================================================== 4. COUNTERS + DELI CASE (Hero Zone B)
def front_frame(t0):
    """Counter frame: x along t from t0, y from the customer face (s = COUNTER_FRONT) towards the staff side, z up."""
    return Frame((COUNTER_FRONT, t0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


def panel_front(fr, L, z0, z1, y_face=0.03, nbays=None):
    """Walnut frame-and-panel cladding on the customer face (outward = -y of fr) between z0 and z1."""
    out = []
    ff = Frame(fr.p(0.0, y_face, 0.0), fr.X, mul(fr.Y, -1.0), fr.Z)
    out += cbox(ff, 0.0, L, 0.0, 0.022, z0, z0 + 0.09, "walnut", ch=0.004, grain="x", skip=("-y",))
    out += cbox(ff, 0.0, L, 0.0, 0.022, z1 - 0.08, z1, "walnut", ch=0.004, grain="x", skip=("-y",))
    sw = 0.075
    nb = nbays or max(1, int(round((L - sw) / 0.55)))
    bay = (L - sw * (nb + 1)) / nb
    for k in range(nb + 1):
        x = k * (bay + sw)
        out += cbox(ff, x, x + sw, 0.0, 0.022, z0 + 0.09, z1 - 0.08, "walnut", ch=0.004, grain="z", skip=("-y",), caps=(False, False))
    for k in range(nb):
        a0 = sw + k * (bay + sw)
        out += raised_panel(ff, a0, a0 + bay, z0 + 0.09, z1 - 0.08)
    return out


def top_slab(fr, x0, x1, y0, y1, zt, mat="terrazzo", band=0.04):
    """Counter top: field + bull-nosed walnut band on the customer edge and the ends."""
    out = []
    edge = [(-band, zt - 0.04), (-0.006, zt - 0.04), (0.0, zt - 0.032), (0.004, zt - 0.02), (0.0, zt - 0.008), (-0.006, zt), (-band, zt)]
    out += prism(Frame(fr.p(0.0, y0, 0.0), fr.X, mul(fr.Y, -1.0), fr.Z), edge, x0, x1, "walnut", smooth={1, 2, 3, 4})
    for xe, sg in ((x0, -1.0), (x1, 1.0)):
        fe = Frame(fr.p(xe, 0.0, 0.0), fr.Y, mul(fr.X, sg), fr.Z)
        out += prism(fe, edge, y0 + band, y1, "walnut", smooth={1, 2, 3, 4}, caps=(False, True))
    out += cbox(fr, x0 + band, x1 - band, y0 + band, y1, zt - 0.03, zt - 0.001, mat, grain="x", skip=("-z",))
    return out


def counter_body(t0, t1, zt=1.02, top="terrazzo"):
    out = []
    fr = front_frame(t0)
    L = t1 - t0
    out += cbox(fr, 0.0, L, 0.06, 0.95, FLOOR, FLOOR + 0.10, "iron", ch=0.003, grain="x", skip=("-z",))
    out += cbox(fr, 0.0, L, 0.03, 0.98, FLOOR + 0.10, zt - 0.04, "walnut", grain="x", skip=("-z", "+z"))
    out += panel_front(fr, L, FLOOR + 0.10, zt - 0.04)
    out += top_slab(fr, -0.01, L + 0.01, -0.03, 1.0, zt, top)
    # staff side: open shelf
    out += cbox(fr, 0.03, L - 0.03, 0.55, 0.98, 0.48, 0.50, "walnut", grain="x")
    return out


def deli_case(t0, t1, hero=False):
    """Commercial curved-glass refrigerated case: steel kick + louvre, walnut panel front, stainless bumper, deck,
    curved front glass (double surface), top glass, rear sliding glass, cream enamel ends with steel glass clamps,
    LED-style light strip, staff-side enamel doors and work ledge."""
    out = []
    fr = front_frame(t0)
    L = t1 - t0
    e = 0.035                                         # end panel thickness (inside the case footprint)
    zf = FLOOR
    out += cbox(fr, e, L - e, 0.06, 0.95, zf, zf + 0.10, "steel", ch=0.003, grain="x", skip=("-z",))
    out += cbox(fr, e, L - e, 0.03, 0.98, zf + 0.10, 0.86, "enamel", grain="x", skip=("-z", "-y", "+y"))
    # louvre grille (customer side)
    out += cbox(fr, e, L - e, 0.028, 0.034, zf + 0.10, zf + 0.20, "iron", grain="x", skip=("+y",))
    for k in range(6):
        z = zf + 0.112 + k * 0.015
        out += cbox(fr, e + 0.02, L - e - 0.02, 0.012, 0.03, z, z + 0.006, "steel", ch=0.002, grain="x")
    out += panel_front(Frame(fr.p(e, 0.0, 0.0), fr.X, fr.Y, fr.Z), L - 2 * e, zf + 0.20, 0.80)
    bump = round_rect(-0.012, 0.06, 0.795, 0.86, 0.018, seg=3, corners=(1, 0, 1, 1))
    out += prism(fr, bump, e, L - e, "steel", smooth="all", caps=(False, False))
    out += cbox(fr, e, L - e, 0.06, 0.84, 0.86, 0.88, "iron", grain="x", skip=("-z",))        # display deck (dark: food contrast)
    # front glass: quarter ellipse from the lip to the top
    cy, cz, ry, rz = 0.47, 0.88, 0.415, 0.42
    curve = [(cy + ry * math.cos(math.radians(a)), cz + rz * math.sin(math.radians(a))) for a in range(180, 89, -9)]
    for off, side in ((0.0, 1.0), (0.006, -1.0)):
        for i in range(len(curve) - 1):
            (ya, za), (yb, zb) = curve[i], curve[i + 1]
            # offset towards the inside (towards the ellipse centre)
            def inward(y, z):
                dy, dz = cy - y, cz - z
                l = math.hypot(dy, dz)
                return (y + off * dy / l, z + off * dz / l)
            ya, za = inward(ya, za)
            yb, zb = inward(yb, zb)
            vs = [fr.p(e, ya, za), fr.p(L - e, ya, za), fr.p(L - e, yb, zb), fr.p(e, yb, zb)]
            nmid = ((ya + yb) / 2 - cy, (za + zb) / 2 - cz)
            emit(out, F(vs, "glass", [(0, i / 10), (1, i / 10), (1, (i + 1) / 10), (0, (i + 1) / 10)],
                        hint=fr.v(0.0, nmid[0] * side, nmid[1] * side), smooth=True))
    # top glass (flat) + rear sliding doors (glass)
    for zz, side in ((1.30, 1.0), (1.294, -1.0)):
        emit(out, F([fr.p(e, 0.47, zz), fr.p(L - e, 0.47, zz), fr.p(L - e, 0.80, zz), fr.p(e, 0.80, zz)], "glass",
                    [(0, 0), (1, 0), (1, 1), (0, 1)], hint=fr.v(0, 0, side)))
    for k in range(2):
        xa, xb = e + k * (L - 2 * e) / 2, e + (k + 1) * (L - 2 * e) / 2
        yy = 0.80 + 0.012 * k
        for dy, side in ((0.0, 1.0), (-0.004, -1.0)):
            emit(out, F([fr.p(xa, yy + dy, 0.90), fr.p(xb, yy + dy, 0.90), fr.p(xb, yy + dy, 1.29), fr.p(xa, yy + dy, 1.29)], "glass",
                        [(0, 0), (1, 0), (1, 1), (0, 1)], hint=fr.v(0, side, 0)))
        out += cbox(fr, xa, xb, yy - 0.01, yy + 0.006, 1.27, 1.29, "steel", grain="x")
        out += cbox(fr, xb - 0.06, xb - 0.03, yy + 0.004, yy + 0.02, 1.0, 1.18, "steel", grain="z")     # door pull
    # top frame bars (steel) at the glass joints
    out += tube(fr, [(e, 0.47, 1.302), (L - e, 0.47, 1.302)], 0.009, 8, "steel")
    out += tube(fr, [(e, 0.805, 1.302), (L - e, 0.805, 1.302)], 0.009, 8, "steel")
    out += cbox(fr, e, L - e, 0.80, 0.83, 0.86, 0.90, "steel", grain="x")
    # light canopy under the top glass + emissive strip facing down into the case
    out += cbox(fr, e, L - e, 0.45, 0.52, 1.27, 1.293, "steel", grain="x")
    out += cbox(fr, e + 0.02, L - e - 0.02, 0.475, 0.505, 1.266, 1.270, "glow", grain="x", skip=("+z",))
    # end panels (cream enamel) following the glass profile, with steel clamps along the curve
    outer = [(cy + (ry + 0.03) * math.cos(math.radians(a)), cz + (rz + 0.03) * math.sin(math.radians(a))) for a in range(180, 89, -15)]
    side = [(0.0, zf), (1.0, zf), (1.0, 0.975), (0.85, 0.975), (0.85, 1.33), (0.47, 1.33)] + outer[::-1] + [(0.02, 0.86), (0.0, 0.84)]
    for xa, xb in ((0.0, e), (L - e, L)):
        out += prism(fr, side, xa, xb, "enamel", caps=(True, True))
    for x in (e + 0.006, L - e - 0.006):
        out += tube(fr, [(x, p[0], p[1]) for p in curve] + [(x, 0.80, 1.30)], 0.007, 6, "steel")
    # staff side: enamel doors + work ledge
    for k in range(2):
        xa, xb = e + 0.01 + k * (L - 2 * e) / 2, e - 0.01 + (k + 1) * (L - 2 * e) / 2
        out += cbox(fr, xa, xb, 0.98, 1.0, zf + 0.12, 0.84, "enamel", ch=0.004, grain="z")
        out += cbox(fr, xb - 0.10, xb - 0.04, 1.0, 1.02, 0.70, 0.72, "steel", ch=0.003, grain="x")
    out += cbox(fr, e, L - e, 0.84, 1.02, 0.94, 0.965, "steel", ch=0.004, grain="x")
    return out


def case_food(t0, t1, hero):
    """Trays on the deck (front row) and on a riser (back row), price tags, dividers."""
    out = []
    fr = front_frame(t0)
    L = t1 - t0
    e = 0.035
    deck = 0.88
    out += cbox(fr, e, L - e, 0.44, 0.80, deck, deck + 0.05, "iron", grain="x", skip=("-z",))    # riser
    rng = random.Random(7 if hero else 11)
    front = ["salami_fan", "prosciutto_fold", "mortadella", "olives_green", "cheese_wedges", "peppers"]
    back = ["salami_logs", "provolone_cut", "mozzarella", "olives_black", "salami_fine"]
    if not hero:
        front = ["peppers", "cheese_wedges", "salami_fan", "olives_black", "mozzarella", "prosciutto_fold"]
        back = ["olives_green", "salami_logs", "mortadella", "salami_fine", "provolone_cut"]
    usable = L - 2 * e - 0.02
    for row, items, (y0, y1), z in (("front", front, (0.10, 0.40), deck), ("back", back, (0.47, 0.78), deck + 0.05)):
        w = usable / len(items)
        for k, kind in enumerate(items):
            x0 = e + 0.01 + k * w + 0.008
            x1 = x0 + w - 0.016
            out += tray(fr, x0, x1, y0, y1, z)
            out += tray_food(fr, kind, x0 + 0.012, x1 - 0.012, y0 + 0.012, y1 - 0.012, z + 0.006, rng)
            # price ticket on a steel pick
            px = (x0 + x1) / 2
            out += tube(fr, [(px, y0 + 0.01, z + 0.01), (px, y0 + 0.012, z + 0.07)], 0.0016, 4, "steel")
            tk = [fr.p(px - 0.035, y0 + 0.004, z + 0.06), fr.p(px + 0.035, y0 + 0.004, z + 0.06),
                  fr.p(px + 0.035, y0 + 0.016, z + 0.105), fr.p(px - 0.035, y0 + 0.016, z + 0.105)]
            emit(out, F(tk, "food", [cell_uv("paper", 0.1, 0.9), cell_uv("paper", 0.9, 0.9), cell_uv("paper", 0.9, 0.3), cell_uv("paper", 0.1, 0.3)],
                        hint=fr.v(0, -1, 0.3)))
            emit(out, F(tk[::-1], "food", [cell_uv("paper", 0.5, 0.5)] * 4, hint=fr.v(0, 1, -0.3)))
    return out


def tray(fr, x0, x1, y0, y1, z, h=0.035, t=0.004):
    out = []
    out += cbox(fr, x0, x1, y0, y1, z, z + 0.004, "steel", grain="x", skip=("-z",))
    out += cbox(fr, x0, x1, y0, y0 + t, z, z + h, "steel", grain="x", skip=("-z",))
    out += cbox(fr, x0, x1, y1 - t, y1, z, z + h, "steel", grain="x", skip=("-z",))
    out += cbox(fr, x0, x0 + t, y0 + t, y1 - t, z, z + h, "steel", grain="y", skip=("-z",))
    out += cbox(fr, x1 - t, x1, y0 + t, y1 - t, z, z + h, "steel", grain="y", skip=("-z",))
    return out


# ------------------------------------------------------------------ food models (original, atlas lp2_food)
def sausage(fr, L, r, cell_side="salami_casing", cut0=None, cut1=None, n=12, bend=0.0, taper=0.85, seed=0, lump=0.06):
    """Cured sausage along local X (0..L): irregular radius, slight bend, rounded or cut ends."""
    rnd = random.Random(seed)
    m = 14
    pts, radii = [], []
    ph = rnd.random() * 6.28
    for k in range(m + 1):
        u = k / m
        x = L * u
        y = bend * L * (u - 0.5) ** 2 * 4 - bend * L
        prof = math.sin(math.pi * (0.06 + 0.88 * u)) ** 0.18
        endr = 1.0 if (u > 0.08 and u < 0.92) else (taper if (u <= 0.08 and cut0 is None) or (u >= 0.92 and cut1 is None) else 1.0)
        rr = r * prof * endr * (1 + lump * math.sin(ph + u * 17) * (0.6 + 0.4 * rnd.random()))
        pts.append((x, y, 0.0))
        radii.append(rr)
    out = []
    W = [fr.p(*p) for p in pts]
    T = [norm(sub(W[min(m, k + 1)], W[max(0, k - 1)])) for k in range(m + 1)]
    up = fr.Z
    rings = []
    for k in range(m + 1):
        n1 = norm(cross(T[k], up))
        n2 = cross(T[k], n1)
        rings.append([add(W[k], add(mul(n1, radii[k] * math.cos(2 * math.pi * i / n)), mul(n2, radii[k] * math.sin(2 * math.pi * i / n))))
                      for i in range(n + 1)])
    for k in range(m):
        for i in range(n):
            vs = [rings[k][i], rings[k][i + 1], rings[k + 1][i + 1], rings[k + 1][i]]
            uv = [cell_uv(cell_side, i / n, k / m), cell_uv(cell_side, (i + 1) / n, k / m),
                  cell_uv(cell_side, (i + 1) / n, (k + 1) / m), cell_uv(cell_side, i / n, (k + 1) / m)]
            mid = mul(add(add(vs[0], vs[1]), add(vs[2], vs[3])), 0.25)
            emit(out, F(vs, "food", uv, hint=sub(mid, mul(add(W[k], W[k + 1]), 0.5)), smooth=True))
    for k, cut, sg in ((0, cut0, -1.0), (m, cut1, 1.0)):
        ring = rings[k][:n]
        if cut:
            for i in range(n):
                a, b = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
                vs = [W[k], ring[i], ring[(i + 1) % n]]
                uv = [cell_uv(cut, 0.5, 0.5), cell_uv(cut, 0.5 + 0.46 * math.cos(a), 0.5 + 0.46 * math.sin(a)),
                      cell_uv(cut, 0.5 + 0.46 * math.cos(b), 0.5 + 0.46 * math.sin(b))]
                emit(out, F(vs, "food", uv, hint=mul(T[k], sg)))
        else:
            tip = add(W[k], mul(T[k], sg * radii[k] * 0.6))
            for i in range(n):
                vs = [tip, ring[i], ring[(i + 1) % n]]
                emit(out, F(vs, "food", [cell_uv(cell_side, 0.5, 0.02 if k == 0 else 0.98)] * 3, hint=mul(T[k], sg), smooth=True))
    return out, (W[0], W[-1], radii[0], radii[-1])


def slice_disc(fr, x, y, z, r, tilt, yaw, cell="salami_cut", th=0.003, n=12):
    f = fr.child(x, y, z, yaw).tilt_x(tilt)
    out = disc_cap(f, r, th, n, "food", up=True, cell=cell)
    out += lathe(f, [(r, 0.0), (r, th)], n, "food", cell="salami_casing")
    return out


def tray_food(fr, kind, x0, x1, y0, y1, z, rng):
    out = []
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, d = x1 - x0, y1 - y0
    if kind in ("salami_fan", "salami_fine"):
        cell = "salami_cut" if kind == "salami_fan" else "salami_fine_cut"
        for row in range(3):
            for k in range(5):
                x = x0 + 0.045 + k * (w - 0.09) / 4
                y = y0 + 0.055 + row * (d - 0.10) / 2
                out += slice_disc(fr, x, y, z + 0.004 + 0.004 * k, 0.040 + 0.004 * rng.random(), -0.10, rng.random() * 0.3, cell)
        if kind == "salami_fan":
            f = fr.child(x1 - 0.02, cy, z + 0.035, math.radians(180))
            o, _ = sausage(f, 0.16, 0.034, cut0="salami_cut", seed=3)
            out += o
    elif kind == "salami_logs":
        for k in range(3):
            f = fr.child(x0 + 0.02, y0 + 0.05 + k * (d - 0.1) / 2, z + 0.036, rng.uniform(-0.08, 0.08))
            o, _ = sausage(f, w - 0.05, 0.034 + 0.006 * rng.random(), cut1="salami_cut" if k != 1 else "salami_fine_cut", seed=10 + k)
            out += o
    elif kind == "prosciutto_fold":
        for row in range(3):
            for k in range(4):
                x = x0 + 0.035 + k * (w - 0.07) / 3
                y = y0 + 0.045 + row * (d - 0.08) / 2
                f = fr.child(x, y, z + 0.008 + 0.004 * row, rng.uniform(-0.3, 0.3))
                out += grid(f, lambda u, v: ((u - 0.5) * 0.09, (v - 0.5) * 0.07, 0.012 * math.sin(math.pi * u) + 0.006 * math.sin(3 * math.pi * v)),
                            4, 4, "food", lambda u, v: cell_uv("prosciutto_cut", u, 0.1 + 0.8 * v), hint_fn=lambda u, v: (0, 0, 1))
    elif kind == "mortadella":
        f = fr.child(cx - 0.02, y1 - 0.005, z + 0.072, -math.pi / 2)          # cut face towards the customer
        o, _ = sausage(f, d - 0.07, 0.070, cell_side="mortadella_casing", cut1="mortadella_cut", n=16, taper=0.9, seed=21, lump=0.02)
        out += o
        for k in range(3):
            out += slice_disc(fr, x1 - 0.045, y0 + 0.05 + 0.05 * k, z + 0.004 + 0.003 * k, 0.045, -0.15, 0.0, "mortadella_cut")
    elif kind == "cheese_wedges":
        # half wheel (cut face to the customer) + two neat wedges
        f = fr.child(x0 + 0.13, y1 - 0.03, z, math.pi)
        out += wedge(f, 0.12, 0.085, math.pi)
        for k in range(2):
            f = fr.child(x1 - 0.05 - k * 0.075, y0 + 0.03, z, math.radians(55))
            out += wedge(f, 0.10, 0.06, 0.55)
    elif kind == "provolone_cut":
        f = fr.child(cx, cy, z, 0.3)
        out += lathe(f, [(0.0, 0.0), (0.075, 0.0), (0.085, 0.03), (0.08, 0.075), (0.06, 0.10)], 16, "food", cell="provolone_wax", a0=0.0, a1=5.2)
        out += disc_cap(f, 0.06, 0.10, 14, "food", cell="cheese_cut")
        for a in (0.0, 5.2):
            cut = f.child(0, 0, 0, a)
            prof = [(0.0, 0.0), (0.075, 0.0), (0.085, 0.03), (0.08, 0.075), (0.06, 0.10), (0.0, 0.10)]
            vs = [cut.p(r, 0.0, zz) for r, zz in prof]
            for tri in triangulate(prof):
                emit(out, F([vs[j] for j in tri], "food", [cell_uv("cheese_cut", 0.5 + prof[j][0] * 3, 0.3 + prof[j][1] * 3) for j in tri],
                            hint=cut.v(0, -1 if a == 0.0 else 1, 0)))
    elif kind in ("olives_green", "olives_black", "peppers", "mozzarella"):
        cell = {"olives_green": "olives_green", "olives_black": "olives_black", "peppers": "peppers", "mozzarella": "mozzarella"}[kind]
        h = 0.025 if kind != "mozzarella" else 0.012
        out += grid(fr, lambda u, v: (x0 + u * w, y0 + v * d, z + h * (math.sin(math.pi * u) * math.sin(math.pi * v)) ** 0.4 + 0.004),
                    6, 5, "food", lambda u, v: cell_uv(cell, u, v), hint_fn=lambda u, v: (0, 0, 1))
        if kind == "mozzarella":
            for k in range(5):
                f = fr.child(x0 + 0.04 + (k % 3) * (w - 0.08) / 2, y0 + 0.06 + (k // 3) * (d - 0.12), z + 0.012, 0.0)
                rr = 0.032 + 0.006 * rng.random()
                prof = [(0.0, 0.0)] + [(rr * math.sin(math.radians(a)), rr - rr * math.cos(math.radians(a))) for a in (30, 60, 90, 120, 150)] + [(0.0, 2 * rr)]
                out += lathe(f, prof, 12, "food", cell="mozzarella")
    return out


def wedge(fr, r, h, ang):
    """Cheese wedge (pie slice) with rind on the arc and cut faces."""
    out = []
    out += lathe(fr, [(r, 0.0), (r * 1.02, h * 0.5), (r, h)], 8, "food", cell="parm_rind", a0=0.0, a1=ang)
    for a, sg in ((0.0, -1.0), (ang, 1.0)):
        c = fr.child(0, 0, 0, a)
        vs = [c.p(0, 0, 0), c.p(r, 0, 0), c.p(r, 0, h), c.p(0, 0, h)]
        emit(out, F(vs, "food", [cell_uv("cheese_cut", 0.5, 0.5), cell_uv("cheese_cut", 0.85, 0.5), cell_uv("cheese_cut", 0.85, 0.75),
                                 cell_uv("cheese_cut", 0.5, 0.75)], hint=c.v(0, sg, 0)))
    pts = [(0.0, 0.0)] + [(r * math.cos(ang * k / 8), r * math.sin(ang * k / 8)) for k in range(9)]
    for z, up in ((h, True), (0.0, False)):
        for k in range(1, 9):
            vs = [fr.p(0, 0, z), fr.p(pts[k][0], pts[k][1], z), fr.p(pts[k + 1][0], pts[k + 1][1], z)]
            emit(out, F(vs, "food", [cell_uv("cheese_cut", 0.5 + p[0] * 2, 0.5 + p[1] * 2) for p in ((0, 0), pts[k], pts[k + 1])],
                        hint=fr.v(0, 0, 1 if up else -1)))
    return out


def prosciutto(fr, L=0.50, rmax=0.125, cut=None):
    """Whole prosciutto leg along local -Z from the shank (z=0) downwards; flattened, rind texture, optional cut face."""
    out = []
    prof = [(0.018, 0.0), (0.024, -0.04), (0.03, -0.10), (0.06, -0.17), (0.10, -0.25), (rmax, -0.33), (rmax * 0.98, -0.40),
            (rmax * 0.85, -0.45), (rmax * 0.55, -0.49), (0.0, -L)]
    if cut:
        prof = prof[:-2] + [(rmax * 0.8, -0.455)]
    flat = Frame(fr.O, fr.X, mul(fr.Y, 0.64), add(fr.Z, mul(fr.X, 0.16)))        # flattened, the heavy end leans (rump side)
    out += lathe(flat, prof[::-1], 16, "food", cell="prosciutto_rind")
    if cut:
        out += disc_cap(flat, rmax * 0.8, -0.455, 16, "food", up=False, cell="prosciutto_cut")
    out += lathe(fr, [(0.0, 0.02), (0.02, 0.02), (0.022, 0.0), (0.018, -0.02)][::-1], 8, "food", cell="prosciutto_rind")
    out += tube(fr, [(0.0, 0.0, -0.035 + 0.008 * k) for k in range(5)], 0.024, 8, "food", cell="twine")     # tied shank
    return out


def provolone(fr, H=0.34, R=0.085):
    """Hanging provolone (pear shape) with a twine net, top at z = 0 hanging down."""
    out = []
    prof = [(0.0, -H), (R * 0.75, -H + 0.02), (R, -H + 0.08), (R * 0.98, -H * 0.55), (R * 0.75, -H * 0.25), (R * 0.42, -0.04), (0.03, -0.01), (0.0, 0.0)]
    out += lathe(fr, prof, 16, "food", cell="provolone_wax")
    for zr in (-H + 0.08, -H * 0.55, -H * 0.25):
        rr = max(p for p in [R * 0.98 if zr == -H * 0.55 else (R if zr == -H + 0.08 else R * 0.75)])
        out += tube(fr, [(rr * 1.02 * math.cos(2 * math.pi * k / 12), rr * 1.02 * math.sin(2 * math.pi * k / 12), zr) for k in range(13)], 0.0035, 4, "food", cell="twine")
    for k in range(4):
        a = 2 * math.pi * k / 4
        path = [(p[0] * 1.03 * math.cos(a), p[0] * 1.03 * math.sin(a), p[1]) for p in prof[1:-1]]
        out += tube(fr, path, 0.0035, 4, "food", cell="twine")
    return out


def hanging_rail():
    """Brass rail under the counter soffit with hanging salumi (Hero Zone B, view V07)."""
    out = []
    s, z = COUNTER_FRONT + 0.32, SOFFIT["z"] - 0.17
    t0, t1 = CASES_T[0][0] + 0.10, CASES_T[1][1] - 0.10
    out += tube(WORLD, [(s, t0, z), (s, t1, z)], 0.013, 10, "brass", caps=True)
    for t in (t0 + 0.05, (t0 + t1) / 2, t1 - 0.05):
        out += tube(WORLD, [(s, t, z), (s, t, SOFFIT["z"])], 0.006, 6, "brass")
        out += lathe(WORLD.child(s, t, 0.0), [(0.0, SOFFIT["z"] - 0.012), (0.03, SOFFIT["z"] - 0.012), (0.03, SOFFIT["z"]), (0.0, SOFFIT["z"])][::-1], 10, "brass")
    rnd = random.Random(5)
    items = ["salami", "salami", "provolone", "salami", "prosciutto", "salami", "salami_long", "provolone_small", "salami", "salami_long", "salami"]
    n = len(items)
    for k, kind in enumerate(items):
        t = t0 + 0.12 + k * (t1 - t0 - 0.24) / (n - 1)
        # S hook + twine loop
        out += tube(WORLD, [(s, t, z + 0.01), (s + 0.012, t, z + 0.02), (s + 0.018, t, z), (s, t, z - 0.03), (s - 0.01, t, z - 0.05)], 0.0025, 4, "steel")
        drop = 0.06 + 0.05 * rnd.random()
        out += tube(WORLD, [(s - 0.01, t, z - 0.05), (s - 0.012, t + 0.008, z - 0.05 - drop * 0.5), (s - 0.01, t, z - 0.05 - drop)], 0.003, 4, "food", cell="twine")
        top = z - 0.05 - drop
        if kind.startswith("salami"):
            Ls = 0.42 + 0.06 * rnd.random() if kind == "salami_long" else 0.26 + 0.10 * rnd.random()
            f = Frame((s - 0.01, t, top), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
            o, _ = sausage(f, Ls, 0.032 + 0.012 * rnd.random(), seed=40 + k, bend=0.02 * rnd.random())
            out += o
            out += tube(WORLD, [(s - 0.01, t, top + 0.002), (s - 0.01, t, top - 0.03)], 0.012, 6, "food", cell="twine")
        elif kind.startswith("provolone"):
            out += provolone(WORLD.child(s - 0.01, t, top, rnd.random() * 6), H=0.34 if kind == "provolone" else 0.24, R=0.085 if kind == "provolone" else 0.06)
        else:
            out += prosciutto(WORLD.child(s - 0.01, t, top, math.radians(90)))
    return out


def slicer(sc, tc, yaw):
    """Gravity-feed meat slicer (generic period design, cream enamel + stainless), operator at local -y."""
    out = []
    fr = WORLD.child(sc, tc, 0.92, yaw)
    base = round_rect(-0.22, 0.22, -0.16, 0.16, 0.05, seg=3)
    fb = Frame(fr.O, fr.Z, fr.X, fr.Y)            # extrude along Z, profile in (x, y)
    out += prism(fb, base, 0.0, 0.085, "enamel", smooth="all")
    for x, y in ((-0.17, -0.11), (0.17, -0.11), (-0.17, 0.11), (0.17, 0.11)):
        out += lathe(fr.child(x, y, 0.0), [(0.0, -0.001), (0.025, -0.001), (0.022, 0.012), (0.0, 0.012)][::-1], 8, "iron")
    # tower + blade housing
    out += cbox(fr, 0.02, 0.16, 0.02, 0.13, 0.085, 0.30, "enamel", ch=0.02, grain="z", smooth="all")
    blade = fr.child(0.03, 0.0, 0.25).tilt_x(math.radians(-90))
    blade = Frame(blade.O, blade.X, blade.Y, blade.Z)
    out += lathe(blade, [(0.0, 0.004), (0.15, 0.004), (0.153, 0.0), (0.15, -0.004), (0.0, -0.004)], 32, "steel")
    out += lathe(blade, [(0.0, 0.016), (0.035, 0.016), (0.045, 0.006), (0.0, 0.006)][::-1], 16, "steel")
    out += tube(blade, [(0.163 * math.cos(math.radians(a)), 0.163 * math.sin(math.radians(a)), 0.0) for a in range(-40, 230, 15)], 0.013, 8, "enamel")
    out += lathe(fr.child(0.03, 0.0, 0.43), [(0.0, 0.0), (0.03, 0.0), (0.035, 0.03), (0.0, 0.045)], 12, "enamel")      # sharpener cap
    # carriage + pusher
    car = fr.child(-0.08, -0.09, 0.12)
    out += cbox(car, -0.13, 0.13, -0.10, 0.10, 0.0, 0.012, "steel", ch=0.003, grain="x")
    out += cbox(car, -0.13, -0.11, -0.10, 0.10, 0.012, 0.11, "steel", ch=0.003, grain="z")
    out += cbox(car, -0.06, 0.06, 0.06, 0.08, 0.012, 0.10, "steel", ch=0.003, grain="x")
    out += tube(car, [(0.0, 0.07, 0.10), (0.0, 0.07, 0.17)], 0.008, 8, "steel")
    out += lathe(car.child(0.0, 0.07, 0.17), [(0.0, 0.0), (0.02, 0.005), (0.022, 0.025), (0.0, 0.035)], 10, "iron")
    out += tube(car, [(0.13, -0.10, 0.05), (0.20, -0.14, 0.06), (0.24, -0.14, 0.06)], 0.009, 8, "iron", caps=True)   # handle
    out += lathe(fr.child(0.21, 0.0, 0.09).tilt_x(math.radians(90)), [(0.0, 0.0), (0.035, 0.0), (0.04, 0.02), (0.0, 0.03)], 12, "iron")  # gauge knob
    return out


def paper_roll(sc, tc, yaw):
    out = []
    fr = WORLD.child(sc, tc, 0.92, yaw)
    for x in (-0.25, 0.25):
        out += cbox(fr, x - 0.008, x + 0.008, -0.08, 0.08, 0.0, 0.012, "iron", ch=0.003, grain="y")
        out += tube(fr, [(x, 0.06, 0.0), (x, 0.0, 0.11), (x, -0.02, 0.13)], 0.008, 6, "iron")
    rollf = Frame(fr.p(-0.24, 0.0, 0.11), fr.Y, fr.Z, fr.X)
    out += lathe(rollf, [(0.0, 0.0), (0.058, 0.0), (0.06, 0.004), (0.06, 0.476), (0.058, 0.48), (0.0, 0.48)], 16, "food", cell="paper")
    out += tube(fr, [(-0.25, -0.075, 0.07), (0.25, -0.075, 0.07)], 0.007, 6, "steel")
    sheet = [fr.p(-0.23, -0.06, 0.08), fr.p(0.23, -0.06, 0.08), fr.p(0.23, -0.10, 0.0), fr.p(-0.23, -0.10, 0.0)]
    emit(out, F(sheet, "food", [cell_uv("paper", 0, 0), cell_uv("paper", 1, 0), cell_uv("paper", 1, 1), cell_uv("paper", 0, 1)], hint=fr.v(0, -1, 1)))
    emit(out, F(sheet[::-1], "food", [cell_uv("paper", 0.5, 0.5)] * 4, hint=fr.v(0, 1, -1)))
    return out


def prosciutto_stand(sc, tc, yaw):
    out = []
    fr = WORLD.child(sc, tc, 0.92, yaw)
    out += cbox(fr, -0.24, 0.24, -0.09, 0.09, 0.0, 0.035, "walnut", ch=0.006, grain="x")
    out += cbox(fr, 0.17, 0.20, -0.03, 0.03, 0.035, 0.22, "steel", ch=0.004, grain="z")
    out += tube(fr, [(0.185, 0.0, 0.20), (0.185, 0.0, 0.25), (0.10, 0.0, 0.25)], 0.012, 8, "steel")
    dvec = norm(fr.v(-0.42, 0.0, -0.135))                # shank in the clamp, the leg rests on the board
    up = norm(fr.v(-0.135, 0.0, 0.42))
    leg = Frame(fr.p(0.17, 0.0, 0.262), fr.Y, up, mul(dvec, -1.0))
    out += prosciutto(leg, L=0.48, cut="yes")
    out += cbox(fr, -0.20, -0.14, -0.05, 0.05, 0.035, 0.10, "steel", ch=0.004, grain="z")
    return out


def back_counter():
    """Staff back counter on P1: enamel cabinets, butcher-block top, steel kick; wall shelf between the menus."""
    out = []
    s0, s1 = BACK_S
    t0, t1 = BACK_T
    fr = Frame((s0, t1, 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))     # x along -t, y towards P1
    L = t1 - t0
    D = s1 - s0
    out += cbox(fr, 0.0, L, 0.05, D, FLOOR, FLOOR + 0.10, "steel", ch=0.003, grain="x", skip=("-z",))
    out += cbox(fr, 0.0, L, 0.02, D, FLOOR + 0.10, 0.87, "enamel", grain="x", skip=("-z", "+z"))
    nd = int(round(L / 0.52))
    dw = L / nd
    for k in range(nd):
        xa, xb = k * dw + 0.006, (k + 1) * dw - 0.006
        out += cbox(fr, xa, xb, 0.0, 0.02, FLOOR + 0.12, 0.86, "enamel", ch=0.005, grain="z", skip=("+y",))
        hx = xa + 0.05 if k % 2 == 0 else xb - 0.05
        out += cbox(fr, hx - 0.008, hx + 0.008, -0.02, 0.0, 0.60, 0.74, "steel", ch=0.003, grain="z")
    out += cbox(fr, -0.02, L + 0.02, -0.03, D, 0.87, 0.92, "walnut", ch=0.008, grain="x")      # butcher-block top
    # enamel splashback on P1 between the butcher block and the menus / shelf
    sp = Frame((P1_S[0], t0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    out += cbox(sp, 0.0, L, 0.0, 0.008, 0.92, 1.32, "enamel", ch=0.002, grain="x", skip=("-y",))
    out += cbox(sp, 0.0, L, 0.0, 0.02, 1.32, 1.345, "steel", ch=0.004, grain="x", skip=("-y",))
    # wall shelf between the two menu boards (replaces the black chalkboard of v0.2.0)
    wf = Frame((P1_S[0], 2.30, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    for z in (1.42, 1.86):
        out += cbox(wf, 0.0, 2.10, 0.0, 0.26, z, z + 0.035, "walnut", ch=0.006, grain="x")
        for x in (0.15, 1.05, 1.95):
            out += cbox(wf, x - 0.012, x + 0.012, 0.0, 0.012, z - 0.20, z, "iron", grain="z")
            out += cbox(wf, x - 0.012, x + 0.012, 0.0, 0.20, z - 0.02, z, "iron", grain="y")
            out += tube(wf, [(x, 0.01, z - 0.18), (x, 0.17, z - 0.02)], 0.006, 6, "iron")
    return out


def counters_faces():
    out = []
    for k, (t0, t1) in enumerate(CASES_T):
        out += deli_case(t0, t1, hero=(k == 0))
        out += case_food(t0, t1, hero=(k == 0))
    out += counter_body(REGISTER_T[0], REGISTER_T[1], 1.02)
    out += counter_body(COFFEE_T[0], COFFEE_T[1], 1.05)
    out += counter_body(GATE_T[0], GATE_T[1], 1.02)
    out += back_counter()
    out += slicer(BACK_S[0] + 0.33, 1.45, math.radians(-90))
    out += paper_roll(BACK_S[0] + 0.35, 2.75, math.radians(-90))
    out += prosciutto_stand(BACK_S[0] + 0.33, 3.45, math.radians(90))
    out += hanging_rail()
    return out


def counter_collision_boxes():
    out = []
    for t0, t1 in CASES_T:
        out.append(((COUNTER_FRONT - 0.01, t0, FLOOR), (COUNTER_BACK + 0.02, t1, 1.33), "GLASS_SHOOT_THROUGH"))
    for (t0, t1), zt in ((REGISTER_T, 1.02), (COFFEE_T, 1.05), (GATE_T, 1.02)):
        out.append(((COUNTER_FRONT - 0.04, t0 - 0.01, FLOOR), (COUNTER_BACK, t1 + 0.01, zt), "WOOD_SOLID_MEDIUM"))
    out.append(((BACK_S[0] - 0.03, BACK_T[0], FLOOR), (BACK_S[1], BACK_T[1], 0.92), "METAL_SOLID_MEDIUM"))
    return out


# ================================================================== 5. ITALIAN TRICOLORE (Hero Zone A)
def wall_flag(s, z_b, angle=math.radians(32), pole=1.0, hoist=(0.10, 0.56), fly=0.68):
    """Wall-mounted cloth flag on the SW pier: iron bracket, walnut pole with brass finial, hoist along the pole,
    cloth hanging in the plane s = const (perpendicular to the wall), soft folds, double-sided."""
    out = []
    t_w = PG.YS
    W = WORLD
    out += cbox(W, s - 0.03, s + 0.03, t_w, t_w + 0.012, z_b - 0.06, z_b + 0.06, "iron", ch=0.003, grain="z")
    d = (0.0, math.cos(angle), math.sin(angle))
    p0 = (s, t_w + 0.012, z_b)
    sock = [add(p0, mul(d, x)) for x in (0.0, 0.10)]
    out += tube(W, sock, 0.016, 10, "iron", caps=True)
    pts = [add(p0, mul(d, x)) for x in (0.05, pole)]
    out += tube(W, pts, 0.011, 10, "walnut", caps=True)
    tip = add(p0, mul(d, pole + 0.02))
    out += lathe(W.child(*tip), [(0.0, -0.02), (0.018, -0.012), (0.022, 0.0), (0.018, 0.012), (0.004, 0.024), (0.0, 0.04)], 10, "brass")

    def cloth(u, v, side):
        x = hoist[0] + (hoist[1] - hoist[0]) * u
        base = add(p0, mul(d, x))
        fold = 0.035 * math.sin(2 * math.pi * (1.6 * u + 0.35 * v) + 0.6) * (0.25 + v) + 0.012 * math.sin(2 * math.pi * 3.1 * v)
        sag = -0.03 * math.sin(math.pi * u) * v
        return (base[0] + fold + side * 0.0015, base[1] + sag, base[2] - fly * v * (1.0 - 0.05 * u))
    for side in (1.0, -1.0):
        out += grid(W, lambda u, v, side=side: cloth(u, v, side), 10, 12, "flag", lambda u, v: (v, 1.0 - u),
                    hint_fn=lambda u, v, side=side: (side, 0.0, 0.0))
    # hoist sleeve along the pole
    out += tube(W, [add(p0, mul(d, x)) for x in (hoist[0], hoist[1])], 0.016, 8, "flag")
    return out


# ================================================================== 6. VANILLA PROPS (archetype names only)
VB = {   # HIGH-LOD bounds (min, max) from docs/_raw/vanilla_catalogue_v021.json / gs_25d
    "v_ret_fh_walllighton": ((-0.139, -0.075, -0.178), (0.139, 0.075, 0.178)),
    "ch_chint02_picture_light": ((-0.352, -0.042, 0.0), (0.352, 0.057, 0.109)),
    "v_med_wallpicture1": ((-0.345, -0.008, -0.306), (0.345, 0.016, 0.306)),
    "ch_prop_vault_painting_01e": ((-0.377, -0.038, -0.046), (0.376, 0.009, 0.917)),
    "prop_game_clock_01": ((-0.216, -0.026, -0.216), (0.216, 0.026, 0.216)),
    "prop_wine_bot_01": ((-0.054, -0.055, 0.0), (0.054, 0.055, 0.392)),
    "prop_wine_red": ((-0.054, -0.055, 0.0), (0.054, 0.055, 0.392)),
    "prop_drink_redwine": ((-0.052, -0.052, 0.0), (0.052, 0.052, 0.175)),
    "prop_wine_glass": ((-0.052, -0.052, 0.0), (0.052, 0.052, 0.175)),
    "v_ret_fh_plate1": ((-0.191, -0.188, -0.012), (0.191, 0.188, 0.012)),
    "prop_bar_napkindisp": ((-0.107, -0.111, 0.0), (0.107, 0.111, 0.286)),
    "prop_food_napkin_01": ((-0.09, -0.152, 0.001), (0.09, 0.155, 0.147)),
    "prop_food_sugarjar": ((-0.049, -0.049, 0.0), (0.049, 0.049, 0.237)),
    "bkr_prop_biker_ceiling_fan_base": ((-0.699, -0.617, -1.009), (0.703, 0.731, 0.0)),
    "bkr_prop_biker_pendant_light": ((-0.253, -0.253, -1.284), (0.253, 0.253, 0.0)),
    "winerow": ((-0.189, -0.165, 0.0), (0.189, 0.165, 0.392)),
    "v_res_foodjara": ((-0.1, -0.1, 0.0), (0.1, 0.1, 0.331)),
    "prop_metalfoodjar_01": ((-0.09, -0.09, 0.0), (0.09, 0.09, 0.2)),
    "lr_prop_clubstool_01": ((-0.257, -0.257, -0.001), (0.257, 0.257, 0.792)),
    "prop_plant_int_01a": ((-0.444, -0.531, 0.0), (0.518, 0.467, 1.955)),
}
VB.update({k: v for k, v in SG.VANILLA_BOUNDS.items() if k != "tr_int1_chalkboard"})


def wall_yaw(n2):
    """Yaw (deg) that turns a wall prop's front (local -y) towards the room normal n2."""
    return math.degrees(math.atan2(n2[0], -n2[1]))


def vanilla_props():
    """(name, s, t, z_bottom, yaw_deg) — z_bottom = world z of the model's lowest point."""
    out = []
    bs = BACK_S[0]
    zt_table = 0.768
    out += [("prop_till_01", 7.45, 5.10, 1.02, 90.0)]
    out += [("v_ret_ml_scale", COUNTER_FRONT + 0.63, 2.15, 1.305, 90.0)]
    out += [("prop_coffee_mac_02", P1_S[0] - 0.012 - 0.21, 5.95, 0.92, -90.0)]
    out += [("v_res_fa_bread01", bs + 0.30, 4.35, 0.92, 0.0), ("v_res_fa_bread02", bs + 0.30, 4.60, 0.92, 15.0)]
    out += [("v_res_fa_chopbrd", bs + 0.32, 3.95, 0.92, 90.0), ("prop_cleaver", bs + 0.30, 3.95, 0.941, 80.0)]
    out += [("prop_knife_stand", bs + 0.55, 5.25, 0.92, 0.0)]
    # booth tables: deliberately different settings
    tables = []
    for k, a in enumerate(booth_bays()):
        sc, tc = table_center(a)
        tables.append((sc, tc))
    (s1, _), (s2, _), (s3, _) = tables
    out += [("prop_bar_napkindisp", s1, -1.03, zt_table, 90.0), ("v_ret_fh_plate1", s1 - 0.18, -0.55, zt_table, 0.0),
            ("v_ret_fh_plate1", s1 + 0.18, -0.70, zt_table, 30.0), ("prop_food_sugarjar", s1 + 0.10, -1.02, zt_table, 0.0)]
    out += [("prop_food_napkin_01", s2, -1.03, zt_table, 90.0), ("prop_wine_red", s2 - 0.08, -0.95, zt_table, 40.0),
            ("prop_wine_glass", s2 - 0.17, -0.45, zt_table, 0.0), ("prop_wine_glass", s2 + 0.18, -0.62, zt_table, 0.0)]
    out += [("prop_food_napkin_01", s3 - 0.13, -1.04, zt_table, 90.0), ("prop_wine_bot_01", s3 + 0.08, -0.98, zt_table, 10.0),
            ("prop_drink_redwine", s3 - 0.20, -0.42, zt_table, 0.0), ("prop_drink_redwine", s3 + 0.21, -0.66, zt_table, 0.0),
            ("v_ret_fh_plate1", s3 - 0.18, -0.58, zt_table, 0.0), ("v_ret_fh_plate1", s3 + 0.17, -0.40, zt_table, 75.0),
            ("prop_food_sugarjar", s3 + 0.12, -1.06, zt_table, 0.0)]
    # coffee counter: sugar jars + stools
    out += [("prop_food_sugarjar", COUNTER_FRONT + 0.12, 5.80, 1.05, 0.0), ("prop_food_sugarjar", COUNTER_FRONT + 0.12, 6.50, 1.05, 0.0)]
    for tt in (5.70, 6.20, 6.70):
        out.append(("lr_prop_clubstool_01", COUNTER_FRONT - 0.42, tt, FLOOR, 0.0))
    # menus: 2 x "Today's Specials" (owner choice) — the black chalkboard is replaced by the walnut stock shelf
    mb = VB["v_19_vanmenuplain"]
    out += [("v_19_vanmenuplain", SG.MENU_BACK_S - mb[1][1], 1.30, 1.35, 90.0),
            ("v_19_vanmenuplain", SG.MENU_BACK_S - mb[1][1], 5.40, 1.35, 90.0)]
    # stock on the wall shelf (P1 face at s = 9.94, shelf depth 0.26 -> front at 9.68)
    out += [("winerow", P1_S[0] - 0.17, 2.62, 1.455, 90.0), ("winerow", P1_S[0] - 0.17, 3.05, 1.455, 90.0),
            ("winerow", P1_S[0] - 0.17, 3.85, 1.455, 90.0),
            ("v_res_foodjara", P1_S[0] - 0.13, 2.55, 1.895, 0.0), ("v_res_foodjara", P1_S[0] - 0.13, 2.80, 1.895, 25.0),
            ("prop_metalfoodjar_01", P1_S[0] - 0.13, 3.35, 1.895, 0.0), ("prop_metalfoodjar_01", P1_S[0] - 0.13, 3.58, 1.895, 0.0),
            ("v_res_foodjara", P1_S[0] - 0.13, 4.05, 1.895, 60.0)]
    # Hero Zone A pier (SW wall between the window casing and the counter): sconce, landscape picture + light, clock
    yaw_sw = wall_yaw((0.0, 1.0))
    sw = VB["v_ret_fh_walllighton"]
    out += [("v_ret_fh_walllighton", 5.93, PG.YS + sw[1][1], 1.66 + sw[0][2], yaw_sw)]
    out += [("v_ret_fh_walllighton", (PG.P_SW[0] + PG.W1["s"][0] - PG.CASING_W) / 2, PG.YS + sw[1][1], 1.66 + sw[0][2], yaw_sw)]
    pic = VB["ch_prop_vault_painting_01e"]          # antique portrait in a dark frame ("the founder")
    out += [("ch_prop_vault_painting_01e", 6.47, PG.YS + pic[1][1] + 0.002, 1.40, yaw_sw)]
    out += [("ch_chint02_picture_light", 6.47, PG.YS + 0.06, 1.40 + (pic[1][2] - pic[0][2]), yaw_sw)]
    # clock over the entrance (chamfer wall, between the picture rail and the cornice)
    ch_mid = ((PG.P_SW[0] + PG.P_NW[0]) / 2, (PG.P_SW[1] + PG.P_NW[1]) / 2)
    d = (PG.P_SW[0] - PG.P_NW[0], PG.P_SW[1] - PG.P_NW[1])
    l = math.hypot(*d)
    n2 = (d[1] / l, -d[0] / l)
    if n2[0] + n2[1] < 0:
        n2 = (-n2[0], -n2[1])
    ck = VB["prop_game_clock_01"]
    out += [("prop_game_clock_01", ch_mid[0] + n2[0] * ck[1][1], ch_mid[1] + n2[1] * ck[1][1], 2.99 - 0.216, wall_yaw(n2))]
    # ceiling vanilla (fans, queue pendants)
    _, _, van = ceiling_fixtures()
    out += van
    # a large plant in the entrance bay corner
    out += [("prop_plant_int_01a", -2.40, 3.05, FLOOR, 20.0)]
    return out


def vanilla_entities():
    """-> (name, (s, t, z) of the model origin, yaw_rad) with the bounds applied."""
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        mn = VB[name][0]
        out.append((name, (round(s, 4), round(t, 4), round(zb - mn[2], 4)), math.radians(yaw)))
    return out


# ================================================================== 7. LIGHTS, COLLISION, EVERYTHING
def lights():
    _, L, _ = ceiling_fixtures()
    sconce_flags = ("not_in_reflection",)
    L += [LT("sconce", "POINT", (5.93, PG.YS + 0.20, 1.72), C_AMBER, 1.4, 1.8, 8.0, flags=sconce_flags, corona=(0.35, 0.6)),
          LT("sconce", "POINT", ((PG.P_SW[0] + PG.W1["s"][0] - PG.CASING_W) / 2, PG.YS + 0.20, 1.72), C_AMBER, 1.4, 1.8, 8.0,
             flags=sconce_flags, corona=(0.35, 0.6)),
          # picture light: aimed down and back onto the painting (wall at t = YS, picture centre z 1.40)
          LT("picture_light", "SPOT", (6.47, PG.YS + 0.30, 2.25), (1.0, 0.82, 0.60), 3.0, 1.7, 8.0, aim=(0.0, -0.32, -0.95),
             cone=(42.0, 18.0), flags=("static_shadows", "not_in_reflection"))]
    for t0, t1 in CASES_T:
        for f in (0.28, 0.72):
            L.append(LT("case", "POINT", (COUNTER_FRONT + 0.45, t0 + (t1 - t0) * f, 1.20), C_CASE, 1.2, 1.2, 4.0,
                        flags=("dont_light_alpha", "not_in_reflection")))
    L += festoon_faces_lights()[1]
    return L


def ceiling_faces_all():
    f, _, _ = ceiling_fixtures()
    return ceiling_faces() + f + festoon_faces_lights()[0]


def hall_faces():
    """Everything of the v0.2.1 hall drawable (architecture kit + furniture + food + fixtures + flag)."""
    out = []
    out += wall_kit_faces()
    out += ceiling_faces_all()
    out += booths_faces()
    out += counters_faces()
    out += wall_flag(6.93, 2.36)
    return out


def collision_boxes():
    """-> [((x0, x1, y0, y1, z0, z1), material)] like gs_slice_geometry."""
    out = []
    for (mn, mx, m) in booth_collision_boxes() + counter_collision_boxes():
        out.append(((mn[0], mx[0], mn[1], mx[1], mn[2], mx[2]), m))
    return out + SG.partition_collision_boxes()


box_tris = SG.box_tris
