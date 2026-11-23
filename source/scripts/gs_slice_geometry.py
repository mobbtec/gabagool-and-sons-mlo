# LONG PIG (resource gabagool_sons_mlo) — VERTICAL SLICE geometry v0.2.0 (pure Python, no bpy).
# Hall + counter of the approved layout v2 (gs_30_concept_layout.py): partitions P1 / P2 with open door gaps,
# 3 burgundy booths at W1, 2 refrigerated deli cases with curved glass, register counter, coffee bar, staff gate,
# back counter with two slicers, wall shelf, meat rail with hanging salumi, pendant lamps / schoolhouse globes.
# Vanilla GTA V props (register, scale, espresso machine, bread, menus ...) are referenced by archetype name only.
# Frame: MLO-local (s, t, z) like gs_proto_geometry; z above the vanilla floor slab (FLOOR = 0.015).
import math
import gs_proto_geometry as PG

FLOOR, CEIL = PG.FLOOR, PG.CEIL
face = PG.face

# ------------------------------------------------------------------ materials of the furniture drawable
MAT = {"leather": 0, "walnut": 1, "terrazzo": 2, "steel": 3, "brass": 4, "glass": 5, "food": 6, "glow": 7}
# texture repeat (metres per texture) for the tiling materials
REP = {"leather": 0.40, "walnut": 0.60, "terrazzo": 0.80, "steel": 0.80, "brass": 0.50}

# ------------------------------------------------------------------ layout (s along SW facade, t inwards)
P1_S = (9.94, 10.06)            # partition hall/counter | kitchen
P1_T = (PG.YS, 7.06)
P1_DOOR = (-0.93, 0.07)          # t range, open gap (door leaf later, stage C)
P2_T = (6.94, 7.06)              # partition hall | north rooms
P2_S = (PG.XW, 10.06)
P2_DOOR = (8.25, 9.25)           # s range behind the counter (staff corridor)
DOOR_H = 2.10

BOOTH_S0, BOOTH_PITCH, N_BOOTHS = 0.85, 1.85, 3
BENCH_T = (-1.165, -0.03)        # bench length along t (window end clear of the W1 window stool)
TABLE_T = (-1.16, -0.08)
COUNTER_FRONT, COUNTER_BACK = 7.00, 8.00
CASES_T = [(0.50, 2.60), (2.65, 4.75)]
REGISTER_T = (4.80, 5.40)
COFFEE_T = (5.45, 6.85)
GATE_T = (-0.37, 0.45)           # short counter between the staff opening (by the window wall) and case 1
BACK_S = (9.24, 9.94)
BACK_T = (0.20, 6.50)
RAIL_S, RAIL_T, RAIL_Z = 8.30, (1.00, 5.80), 2.42


def booth_bays():
    return [BOOTH_S0 + k * BOOTH_PITCH for k in range(N_BOOTHS)]


def table_center(a):
    return (a + 0.925, (TABLE_T[0] + TABLE_T[1]) / 2)


# ------------------------------------------------------------------ primitive helpers
def uv_planar(rep):
    """World planar mapping chosen per face normal (box style)."""
    def make(normal):
        nx, ny, nz = (abs(c) for c in normal)
        if nz >= max(nx, ny):
            return lambda v: (v[0] / rep, v[1] / rep)
        if nx >= ny:
            return lambda v: (v[1] / rep, v[2] / rep)
        return lambda v: (v[0] / rep, v[2] / rep)
    return make


def quad(vs, normal, mat, uvf):
    return face(vs, normal, mat, uvf(normal) if callable(uvf(normal)) else uvf)


def abox(x0, x1, y0, y1, z0, z1, mat, rep=None, skip=()):
    """Axis aligned box, outward faces; skip: subset of {'-x','+x','-y','+y','-z','+z'}."""
    rep = rep or 1.0
    mk = uv_planar(rep)
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    spec = [("-z", [0, 1, 2, 3], (0, 0, -1)), ("+z", [4, 5, 6, 7], (0, 0, 1)), ("-y", [0, 1, 5, 4], (0, -1, 0)),
            ("+y", [2, 3, 7, 6], (0, 1, 0)), ("+x", [1, 2, 6, 5], (1, 0, 0)), ("-x", [3, 0, 4, 7], (-1, 0, 0))]
    return [face([c[i] for i in idx], n, mat, mk(n)) for key, idx, n in spec if key not in skip]


def mbox(x0, x1, y0, y1, z0, z1, m, skip=()):
    return abox(x0, x1, y0, y1, z0, z1, MAT[m], REP.get(m, 1.0), skip)


def ring(cx, cy, r, z, n, phase=0.0):
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + r * math.sin(phase + 2 * math.pi * i / n), z) for i in range(n)]


def frustum_z(cx, cy, z0, z1, r0, r1, n, mat, uv=None, caps=(True, True)):
    """Vertical frustum / cylinder (r0 at z0, r1 at z1)."""
    uv = uv or (lambda i, z: (i / n, z))
    b, t = ring(cx, cy, r0, z0, n), ring(cx, cy, r1, z1, n)
    out = []
    for i in range(n):
        j = (i + 1) % n
        mx, my = (b[i][0] + b[j][0]) / 2 - cx, (b[i][1] + b[j][1]) / 2 - cy
        vs = [b[i], b[j], t[j], t[i]]
        uvs = [uv(i, z0), uv(i + 1, z0), uv(i + 1, z1), uv(i, z1)]
        out.append(face_uv(vs, (mx, my, (r0 - r1) / max(z1 - z0, 1e-6) * math.hypot(mx, my)), mat, uvs))
    if caps[0] and r0 > 1e-4:
        out.append(face_uv(list(reversed(b)), (0, 0, -1), mat, [uv(0.5, z0)] * n))
    if caps[1] and r1 > 1e-4:
        out.append(face_uv(t, (0, 0, 1), mat, [uv(0.5, z1)] * n))
    return out


def face_uv(verts, normal, mat, uvs):
    n = PG._cross(PG._sub(verts[1], verts[0]), PG._sub(verts[2], verts[0]))
    if PG._dot(n, normal) < 0:
        verts, uvs = list(reversed(verts)), list(reversed(uvs))
    return {"v": [tuple(round(c, 5) for c in v) for v in verts], "uv": [tuple(u) for u in uvs], "mat": mat}


def cyl_axis(p0, p1, r, n, mat, uv_side, uv_cap0=None, uv_cap1=None):
    """Cylinder between p0 and p1 (any direction). uv_side(i, k) -> uv (k = 0 at p0, 1 at p1)."""
    ax = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(a * a for a in ax))
    a = [c / L for c in ax]
    ref = (0, 0, 1) if abs(a[2]) < 0.9 else (1, 0, 0)
    u = PG._cross(a, ref)
    lu = math.sqrt(sum(c * c for c in u))
    u = [c / lu for c in u]
    w = PG._cross(a, u)
    rim = lambda p, i: tuple(p[k] + r * (math.cos(2 * math.pi * i / n) * u[k] + math.sin(2 * math.pi * i / n) * w[k]) for k in range(3))
    out = []
    for i in range(n):
        q = [rim(p0, i), rim(p0, i + 1), rim(p1, i + 1), rim(p1, i)]
        nm = tuple((math.cos(2 * math.pi * (i + 0.5) / n) * u[k] + math.sin(2 * math.pi * (i + 0.5) / n) * w[k]) for k in range(3))
        out.append(face_uv(q, nm, mat, [uv_side(i, 0), uv_side(i + 1, 0), uv_side(i + 1, 1), uv_side(i, 1)]))
    if uv_cap0:
        vs = [rim(p0, i) for i in range(n)]
        out.append(face_uv(vs, tuple(-c for c in a), mat, [uv_cap0(i) for i in range(n)]))
    if uv_cap1:
        vs = [rim(p1, i) for i in range(n)]
        out.append(face_uv(vs, tuple(a), mat, [uv_cap1(i) for i in range(n)]))
    return out


def lathe(cx, cy, prof, n, mat, uvf):
    """Surface of revolution around the vertical axis at (cx, cy). prof = [(z, r), ...] top to bottom; r = 0 closes."""
    out = []
    for k in range(len(prof) - 1):
        (za, ra), (zb, rb) = prof[k], prof[k + 1]
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            pa0 = (cx + ra * math.cos(a0), cy + ra * math.sin(a0), za)
            pa1 = (cx + ra * math.cos(a1), cy + ra * math.sin(a1), za)
            pb0 = (cx + rb * math.cos(a0), cy + rb * math.sin(a0), zb)
            pb1 = (cx + rb * math.cos(a1), cy + rb * math.sin(a1), zb)
            am = (a0 + a1) / 2
            nz = (rb - ra) / max(abs(za - zb), 1e-6) if za > zb else 0.0
            nrm = (math.cos(am), math.sin(am), -nz)
            if ra < 1e-5:
                vs, uv = [pa0, pb0, pb1], [uvf(i / n, k), uvf(i / n, k + 1), uvf((i + 1) / n, k + 1)]
            elif rb < 1e-5:
                vs, uv = [pa0, pb0, pa1], [uvf(i / n, k), uvf(i / n, k + 1), uvf((i + 1) / n, k)]
            else:
                vs, uv = [pa0, pb0, pb1, pa1], [uvf(i / n, k), uvf(i / n, k + 1), uvf((i + 1) / n, k + 1), uvf((i + 1) / n, k)]
            out.append(face_uv(vs, nrm, mat, uv))
    return out


def flip(faces):
    """Same faces seen from the other side (reversed winding)."""
    return [{"v": list(reversed(f["v"])), "uv": list(reversed(f["uv"])), "mat": f["mat"]} for f in faces]


def sphere(c, r, nlat, nlon, mat, uvf, zscale=1.0):
    out = []
    pts = lambda i, j: (c[0] + r * math.sin(math.pi * i / nlat) * math.cos(2 * math.pi * j / nlon),
                        c[1] + r * math.sin(math.pi * i / nlat) * math.sin(2 * math.pi * j / nlon),
                        c[2] + zscale * r * math.cos(math.pi * i / nlat))
    for i in range(nlat):
        for j in range(nlon):
            vs = [pts(i, j), pts(i + 1, j), pts(i + 1, j + 1), pts(i, j + 1)]
            if i == 0:
                vs = [vs[0], vs[1], vs[2]]
            elif i == nlat - 1:
                vs = [vs[0], vs[1], vs[3]]
            mid = tuple(sum(v[k] for v in vs) / len(vs) - c[k] for k in range(3))
            out.append(face_uv(vs, mid, mat, [uvf(v) for v in vs]))
    return out


# ------------------------------------------------------------------ atlas (deli food) helpers
CELL = 0.25
INSET = 0.02


def cell_uv(cx, cy, fu=0.5, fv=0.5):
    """uv inside atlas cell (cx, cy) (cy counted from the top of the image); fu, fv in [0, 1]."""
    fu, fv = min(max(fu, 0.0), 1.0), min(max(fv, 0.0), 1.0)
    u = cx * CELL + INSET + fu * (CELL - 2 * INSET)
    v = 1.0 - (cy + 1) * CELL + INSET + fv * (CELL - 2 * INSET)
    return (u, v)


def cell_planar(cx, cy, origin, size):
    """Planar uv into a cell from world (x, y) around origin, size = extent mapped to the full cell."""
    return lambda v: cell_uv(cx, cy, 0.5 + (v[0] - origin[0]) / size, 0.5 + (v[1] - origin[1]) / size)


def cell_box(x0, x1, y0, y1, z0, z1, top_cell, side_cell):
    """Food block: top face from top_cell, sides from side_cell (atlas)."""
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    sx, sy = max(x1 - x0, 1e-3), max(y1 - y0, 1e-3)
    top = lambda v: cell_uv(*top_cell, (v[0] - x0) / sx, (v[1] - y0) / sy)
    side = lambda v: cell_uv(*side_cell, ((v[0] - x0) / sx + (v[1] - y0) / sy) / 2, (v[2] - z0) / max(z1 - z0, 1e-3))
    m = MAT["food"]
    return [face([c[4], c[5], c[6], c[7]], (0, 0, 1), m, top),
            face([c[0], c[1], c[5], c[4]], (0, -1, 0), m, side), face([c[2], c[3], c[7], c[6]], (0, 1, 0), m, side),
            face([c[1], c[2], c[6], c[5]], (1, 0, 0), m, side), face([c[3], c[0], c[4], c[7]], (-1, 0, 0), m, side)]


# ================================================================== partitions (part of the shell drawable)
def partition_faces(mats):
    """P1 and P2 (12 cm), wainscot + plaster on both sides, plaster jambs / head at the door gaps, walnut casings."""
    F = []
    wood, wall = mats["wood"], mats["wall"]

    def band_faces(fixed_axis, fixed, a0, a1, normal, z0, z1):
        out = []
        cuts = [(z0, min(z1, PG.WAINSCOT), "wood"), (max(z0, PG.WAINSCOT), z1, "wall")]
        for b0, b1, kind in cuts:
            if b1 - b0 < 1e-4:
                continue
            if fixed_axis == "s":
                vs = [(fixed, a0, b0), (fixed, a1, b0), (fixed, a1, b1), (fixed, a0, b1)]
                uvf = (lambda v: (v[1] / 0.6, v[2] / 1.0)) if kind == "wood" else (lambda v: (v[1] / 2.0, v[2] / 2.0))
            else:
                vs = [(a0, fixed, b0), (a1, fixed, b0), (a1, fixed, b1), (a0, fixed, b1)]
                uvf = (lambda v: (v[0] / 0.6, v[2] / 1.0)) if kind == "wood" else (lambda v: (v[0] / 2.0, v[2] / 2.0))
            out.append(face(vs, normal, wood if kind == "wood" else wall, uvf))
        return out

    def wall_runs(a_lo, a_hi, gap):
        return [(a_lo, gap[0], FLOOR, CEIL), (gap[1], a_hi, FLOOR, CEIL), (gap[0], gap[1], DOOR_H, CEIL)]

    # P1 at s = 9.94 .. 10.06 (faces -s towards the counter, +s towards the kitchen)
    for a0, a1, z0, z1 in wall_runs(P1_T[0], P2_T[0], P1_DOOR):
        F += band_faces("s", P1_S[0], a0, a1, (-1, 0, 0), z0, z1)
    for a0, a1, z0, z1 in wall_runs(P1_T[0], P1_T[1], P1_DOOR):
        F += band_faces("s", P1_S[1], a0, a1, (1, 0, 0), z0, z1)
    # P2 at t = 6.94 .. 7.06 (faces -t towards the hall, +t towards the north rooms)
    for a0, a1, z0, z1 in wall_runs(P2_S[0], P1_S[0], P2_DOOR):
        F += band_faces("t", P2_T[0], a0, a1, (0, -1, 0), z0, z1)
    for a0, a1, z0, z1 in wall_runs(P2_S[0], P2_S[1], P2_DOOR):
        F += band_faces("t", P2_T[1], a0, a1, (0, 1, 0), z0, z1)
    # jambs + heads of the gaps (plaster)
    pl = lambda v: ((v[0] + v[1]) / 2.0, v[2] / 2.0)
    for t in P1_DOOR:
        n = (0, 1, 0) if t == P1_DOOR[0] else (0, -1, 0)
        F.append(face([(P1_S[0], t, FLOOR), (P1_S[1], t, FLOOR), (P1_S[1], t, DOOR_H), (P1_S[0], t, DOOR_H)], n, wall, pl))
    F.append(face([(P1_S[0], P1_DOOR[0], DOOR_H), (P1_S[1], P1_DOOR[0], DOOR_H), (P1_S[1], P1_DOOR[1], DOOR_H),
                   (P1_S[0], P1_DOOR[1], DOOR_H)], (0, 0, -1), wall, pl))
    for s in P2_DOOR:
        n = (1, 0, 0) if s == P2_DOOR[0] else (-1, 0, 0)
        F.append(face([(s, P2_T[0], FLOOR), (s, P2_T[1], FLOOR), (s, P2_T[1], DOOR_H), (s, P2_T[0], DOOR_H)], n, wall, pl))
    F.append(face([(P2_DOOR[0], P2_T[0], DOOR_H), (P2_DOOR[1], P2_T[0], DOOR_H), (P2_DOOR[1], P2_T[1], DOOR_H),
                   (P2_DOOR[0], P2_T[1], DOOR_H)], (0, 0, -1), wall, pl))
    # end of P1 against the SW wall / P2 end against the NW wall need no faces (hidden). Free end of P2 at s 10.06 meets P1.
    # walnut casings (7.5 cm, 1.8 cm proud) on both sides of both gaps
    W, P = PG.CASING_W, PG.CASING_P
    for side, sx in ((-1, P1_S[0]), (1, P1_S[1])):
        x0, x1 = (sx - P, sx) if side < 0 else (sx, sx + P)
        F += abox(x0, x1, P1_DOOR[0] - W, P1_DOOR[0], FLOOR, DOOR_H + W, wood, 0.6)
        F += abox(x0, x1, P1_DOOR[1], P1_DOOR[1] + W, FLOOR, DOOR_H + W, wood, 0.6)
        F += abox(x0, x1, P1_DOOR[0], P1_DOOR[1], DOOR_H, DOOR_H + W, wood, 0.6)
    for side, ty in ((-1, P2_T[0]), (1, P2_T[1])):
        y0, y1 = (ty - P, ty) if side < 0 else (ty, ty + P)
        F += abox(P2_DOOR[0] - W, P2_DOOR[0], y0, y1, FLOOR, DOOR_H + W, wood, 0.6)
        F += abox(P2_DOOR[1], P2_DOOR[1] + W, y0, y1, FLOOR, DOOR_H + W, wood, 0.6)
        F += abox(P2_DOOR[0], P2_DOOR[1], y0, y1, DOOR_H, DOOR_H + W, wood, 0.6)
    return F


def partition_collision_boxes():
    out = []
    for a0, a1, z0, z1 in ((P1_T[0], P1_DOOR[0], 0.0, CEIL), (P1_DOOR[1], P1_T[1], 0.0, CEIL), (P1_DOOR[0], P1_DOOR[1], DOOR_H, CEIL)):
        out.append(((P1_S[0], P1_S[1], a0, a1, z0, z1), "PLASTER_SOLID"))
    for a0, a1, z0, z1 in ((P2_S[0], P2_DOOR[0], 0.0, CEIL), (P2_DOOR[1], P1_S[0], 0.0, CEIL), (P2_DOOR[0], P2_DOOR[1], DOOR_H, CEIL)):
        out.append(((a0, a1, P2_T[0], P2_T[1], z0, z1), "PLASTER_SOLID"))
    return out


# ================================================================== booths
SEAT_Z, SEAT_TOP, BACK_TOP, CAP_TOP = 0.36, 0.46, 1.10, 1.13


def bench(a, facing):
    """One booth bench. a = s of the back plane (outer face); facing +1 -> seat towards +s, -1 -> towards -s."""
    F = []
    t0, t1 = BENCH_T
    sg = facing
    S = lambda d: a + sg * d                         # distance d from the back plane into the seat
    lo = lambda d0, d1: (min(S(d0), S(d1)), max(S(d0), S(d1)))
    # back panel + cap (walnut)
    x0, x1 = lo(0.0, 0.08)
    F += mbox(x0, x1, t0, t1, FLOOR, BACK_TOP, "walnut", skip=("-z",))
    x0, x1 = lo(0.0, 0.10)
    F += mbox(x0, x1, t0 - 0.01, t1 + 0.01, BACK_TOP, CAP_TOP, "walnut", skip=("-z",))
    # plinth (walnut, 4 cm toe recess)
    x0, x1 = lo(0.08, 0.47)
    F += mbox(x0, x1, t0 + 0.03, t1 - 0.03, FLOOR, SEAT_Z, "walnut", skip=("-z",))
    # seat cushion (leather) with a soft front edge
    x0, x1 = lo(0.08, 0.53)
    F += mbox(x0, x1, t0 + 0.03, t1 - 0.03, SEAT_Z, SEAT_TOP - 0.02, "leather", skip=("-z",))
    xa, xb = lo(0.08, 0.51)
    F += mbox(xa, xb, t0 + 0.03, t1 - 0.03, SEAT_TOP - 0.02, SEAT_TOP, "leather", skip=("-z",))
    # channel-tufted back cushion: 5 vertical rolls, each with a centre ridge, leaning back 6 cm over its height
    n = 5
    tw = (t1 - t0 - 0.06) / n
    lean = 0.06
    for k in range(n):
        ta, tb = t0 + 0.03 + k * tw, t0 + 0.03 + (k + 1) * tw
        tm = (ta + tb) / 2
        z0, z1 = SEAT_TOP, BACK_TOP - 0.06
        fb, ft = 0.20, 0.20 - lean                 # front face distance from the back plane, bottom / top
        ridge = 0.022
        P = lambda d, t, z: (S(d), t, z)
        quads = [
            [P(fb, ta, z0), P(fb + ridge, tm, z0), P(ft + ridge, tm, z1), P(ft, ta, z1)],
            [P(fb + ridge, tm, z0), P(fb, tb, z0), P(ft, tb, z1), P(ft + ridge, tm, z1)],
        ]
        for q in quads:
            F.append(face(q, (sg, 0, 0.05), MAT["leather"], lambda v: (v[1] / REP["leather"], v[2] / REP["leather"])))
        # top roll cap
        F.append(face([P(0.08, ta, z1), P(0.08, tb, z1), P(ft, tb, z1), P(ft + ridge, tm, z1), P(ft, ta, z1)], (0, 0, 1),
                      MAT["leather"], lambda v: (v[0] / REP["leather"], v[1] / REP["leather"])))
    # side end panels (walnut) at the aisle end and at the window end
    for ta, tb in ((t1, t1 + 0.025), (t0 - 0.025, t0)):
        x0, x1 = lo(0.0, 0.55)
        F += mbox(x0, x1, ta, tb, FLOOR, SEAT_TOP + 0.02, "walnut", skip=("-z",))
        x0, x1 = lo(0.0, 0.22)
        F += mbox(x0, x1, ta, tb, SEAT_TOP + 0.02, CAP_TOP, "walnut", skip=("-z",))
    return F


def booth_table(a):
    F = []
    sc, _ = table_center(a)
    s0, s1 = a + 0.56, a + 1.29
    t0, t1 = TABLE_T
    F += mbox(s0 - 0.005, s1 + 0.005, t0 - 0.005, t1 + 0.005, 0.722, 0.752, "steel")      # chrome edge band
    F += mbox(s0, s1, t0, t1, 0.752, 0.765, "terrazzo", skip=("-z",))                        # terrazzo top
    pc = (sc, -0.42)
    F += frustum_z(pc[0], pc[1], 0.035, 0.722, 0.035, 0.035, 8, MAT["steel"], caps=(False, False))
    F += frustum_z(pc[0], pc[1], FLOOR, 0.035, 0.22, 0.20, 12, MAT["steel"], caps=(False, True))
    F += frustum_z(pc[0], pc[1], 0.69, 0.722, 0.10, 0.10, 8, MAT["steel"], caps=(True, False))   # top flange
    return F


def booths_faces():
    F = []
    for a in booth_bays():
        F += bench(a, +1)
        F += booth_table(a)
        F += bench(a + BOOTH_PITCH, -1)
    return F


def booth_collision_boxes():
    out = []
    for a in booth_bays():
        for back, sg in ((a, 1), (a + BOOTH_PITCH, -1)):
            x0, x1 = sorted((back, back + sg * 0.53))
            out.append(((x0, x1, BENCH_T[0] - 0.025, BENCH_T[1] + 0.025, 0.0, SEAT_TOP), "LEATHER"))
            x0, x1 = sorted((back, back + sg * 0.22))
            out.append(((x0, x1, BENCH_T[0] - 0.025, BENCH_T[1] + 0.025, SEAT_TOP, CAP_TOP), "WOOD_SOLID_MEDIUM"))
        sc, _ = table_center(a)
        out.append(((a + 0.555, a + 1.295, TABLE_T[0] - 0.005, TABLE_T[1] + 0.005, 0.72, 0.765), "WOOD_SOLID_MEDIUM"))
        out.append(((sc - 0.04, sc + 0.04, -0.46, -0.38, 0.0, 0.72), "METAL_SOLID_SMALL"))
    return out


# ================================================================== counter line
def cabinet(s0, s1, t0, t1, top_z, top_mat="terrazzo", overhang=0.03, kick=0.10):
    """Walnut counter body facing -s (customers), steel kick plate, brass trim, top slab."""
    F = []
    F += mbox(s0 + 0.06, s1, t0, t1, FLOOR, kick, "steel", skip=("-z",))                  # recessed kick plate
    F += mbox(s0, s1, t0, t1, kick, top_z - 0.04, "walnut", skip=("-z",))
    F += mbox(s0 - 0.006, s0, t0, t1, top_z - 0.10, top_z - 0.085, "brass")                # brass line under the top
    F += mbox(s0 - overhang, s1, t0 - 0.01, t1 + 0.01, top_z - 0.04, top_z, top_mat)
    return F


def deli_case(t0, t1):
    """Refrigerated case: walnut base, steel deck, curved front glass (5 facets), flat top glass, glass ends,
    warm light strip, steel trays with salumi / cheese (atlas)."""
    F = []
    s0, s1 = COUNTER_FRONT, COUNTER_BACK
    deck = 0.85
    F += mbox(s0 + 0.06, s1, t0, t1, FLOOR, 0.10, "steel", skip=("-z",))
    F += mbox(s0, s1, t0, t1, 0.10, deck - 0.03, "walnut", skip=("-z",))
    F += mbox(s0 - 0.006, s0, t0, t1, deck - 0.09, deck - 0.075, "brass")
    F += mbox(s0, s1, t0, t1, deck - 0.03, deck, "steel")                                      # deck
    F += mbox(s1 - 0.04, s1, t0, t1, deck, deck + 0.06, "steel")                               # rear lip
    # glass: quarter ellipse from (s0 + 0.04, deck) to (s0 + 0.50, 1.30)
    cs, cz, rs, rz = s0 + 0.50, deck, 0.46, 0.45
    prof = [(cs - rs * math.cos(math.radians(p)), cz + rz * math.sin(math.radians(p))) for p in (0, 22.5, 45, 67.5, 90)]
    prof.append((s1 - 0.04, 1.30))
    g = MAT["glass"]
    gl = lambda v: ((v[1]) / 1.0, (v[0] + v[2]) / 1.0)
    ga, gb = t0 + 0.012, t1 - 0.012
    for (pa, pb) in zip(prof[:-1], prof[1:]):
        vs = [(pa[0], ga, pa[1]), (pa[0], gb, pa[1]), (pb[0], gb, pb[1]), (pb[0], ga, pb[1])]
        nrm = (-(pb[1] - pa[1]), 0, (pb[0] - pa[0]))
        F.append(face(vs, nrm, g, gl))
        F.append(face(vs, tuple(-c for c in nrm), g, gl))                                      # inner side
    for tt, sgn in ((ga, -1), (gb, 1)):                                                         # end glasses (convex)
        vs = [(p[0], tt, p[1]) for p in prof] + [(s1 - 0.04, tt, deck)]
        F.append(face(vs, (0, sgn, 0), g, gl))
        F.append(face(vs, (0, -sgn, 0), g, gl))
    # steel frame: end posts following the profile + top rail
    for tt in (t0, t1 - 0.012):
        for (pa, pb) in zip(prof[:-1], prof[1:]):
            F += mbox(min(pa[0], pb[0]) - 0.006, max(pa[0], pb[0]) + 0.006, tt, tt + 0.012,
                      min(pa[1], pb[1]) - 0.006, max(pa[1], pb[1]) + 0.006, "steel")
    F += mbox(prof[-2][0] - 0.01, prof[-2][0] + 0.01, t0, t1, 1.295, 1.315, "steel")
    F += mbox(s1 - 0.05, s1, t0, t1, 1.295, 1.315, "steel")
    # warm light strip under the top glass
    lz = 1.275
    F.append(face([(s1 - 0.20, t0 + 0.05, lz), (s1 - 0.08, t0 + 0.05, lz), (s1 - 0.08, t1 - 0.05, lz), (s1 - 0.20, t1 - 0.05, lz)],
                  (0, 0, -1), MAT["glow"], lambda v: (0.5, 0.5)))
    F += mbox(s1 - 0.21, s1 - 0.07, t0 + 0.04, t1 - 0.04, lz, lz + 0.02, "steel", skip=("-z",))
    # trays + food: two rows, front row lower (tilted look by height), 5 trays per row
    F += case_food(s0 + 0.10, s0 + 0.47, t0 + 0.06, t1 - 0.06, deck, 0, seed=int(t0 * 10))
    F += case_food(s0 + 0.52, s1 - 0.08, t0 + 0.06, t1 - 0.06, deck + 0.06, 1, seed=int(t0 * 10) + 7)
    if True:   # riser under the back row
        F += mbox(s0 + 0.50, s1 - 0.06, t0 + 0.04, t1 - 0.04, deck, deck + 0.06, "steel", skip=("-z",))
    return F


FOOD_KINDS = ["salami_logs", "sliced_salami", "provolone", "ham", "mozzarella", "olives", "peppers", "roast_beef",
              "mortadella", "prosciutto"]


def case_food(s0, s1, t0, t1, z, row, seed=0):
    F = []
    n = 5
    tw = (t1 - t0) / n
    for k in range(n):
        ta, tb = t0 + k * tw + 0.012, t0 + (k + 1) * tw - 0.012
        F += mbox(s0, s1, ta, tb, z, z + 0.012, "steel", skip=("-z",))                       # tray base
        for (xa, xb, ya, yb) in ((s0, s1, ta, ta + 0.008), (s0, s1, tb - 0.008, tb), (s0, s0 + 0.008, ta, tb), (s1 - 0.008, s1, ta, tb)):
            F += mbox(xa, xb, ya, yb, z + 0.012, z + 0.035, "steel", skip=("-z",))             # tray rim
        kind = FOOD_KINDS[(seed + k * 3 + row * 5) % len(FOOD_KINDS)]
        F += food_in_tray(kind, s0 + 0.015, s1 - 0.015, ta + 0.015, tb - 0.015, z + 0.012)
    return F


def food_in_tray(kind, s0, s1, t0, t1, z):
    F = []
    m = MAT["food"]
    sc, tc = (s0 + s1) / 2, (t0 + t1) / 2
    if kind == "salami_logs":            # 2 logs along s, cut face towards the customer (-s)
        for tt in (t0 + (t1 - t0) * 0.28, t0 + (t1 - t0) * 0.72):
            r = 0.035
            F += cyl_axis((s0 + 0.01, tt, z + r), (s1 - 0.01, tt, z + r), r, 10, m,
                          lambda i, k: cell_uv(0, 0, i / 10, k), lambda i: cell_uv(1, 0, 0.5 + 0.45 * math.cos(2 * math.pi * i / 10), 0.5 + 0.45 * math.sin(2 * math.pi * i / 10)),
                          lambda i: cell_uv(0, 0, 0.5, 0.5))
    elif kind == "sliced_salami":        # shingled slices: thin discs stepping up
        for i in range(6):
            r = 0.045
            x = s0 + 0.05 + i * (s1 - s0 - 0.10) / 5
            F += cyl_axis((x, tc, z + 0.002 + i * 0.004), (x, tc, z + 0.008 + i * 0.004), r, 10, m,
                          lambda i_, k: cell_uv(0, 0, i_ / 10, k), None,
                          lambda j: cell_uv(1, 0, 0.5 + 0.45 * math.cos(2 * math.pi * j / 10), 0.5 + 0.45 * math.sin(2 * math.pi * j / 10)))
    elif kind == "provolone":            # wedges (triangular prisms) with wax rind
        for i in range(3):
            x = s0 + 0.03 + i * (s1 - s0 - 0.06) / 3
            w = (s1 - s0 - 0.06) / 3 - 0.01
            h = 0.06
            a, b, c = (x, t0 + 0.02, z), (x + w, t0 + 0.02, z), (x + w / 2, t1 - 0.02, z)
            top = [(p[0], p[1], z + h) for p in (a, b, c)]
            F.append(face_uv(top, (0, 0, 1), m, [cell_uv(3, 0, 0.1, 0.1), cell_uv(3, 0, 0.9, 0.1), cell_uv(3, 0, 0.5, 0.9)]))
            for p, q in ((a, b), (b, c), (c, a)):
                vs = [p, q, (q[0], q[1], z + h), (p[0], p[1], z + h)]
                mid = ((p[0] + q[0]) / 2 - (a[0] + b[0] + c[0]) / 3, (p[1] + q[1]) / 2 - (a[1] + b[1] + c[1]) / 3, 0)
                cellx = 2 if (p, q) == (c, a) else 3
                F.append(face_uv(vs, mid, m, [cell_uv(cellx, 0, 0, 0), cell_uv(cellx, 0, 1, 0), cell_uv(cellx, 0, 1, 1), cell_uv(cellx, 0, 0, 1)]))
    elif kind in ("ham", "mortadella", "roast_beef"):   # half loaf, cut face up
        top = {"ham": (1, 1), "mortadella": (1, 1), "roast_beef": (2, 1)}[kind]
        side = {"ham": (0, 1), "mortadella": (1, 1), "roast_beef": (2, 1)}[kind]
        F += cell_box(s0 + 0.03, s1 - 0.03, t0 + 0.02, t1 - 0.02, z, z + 0.07, top, side)
    elif kind == "mozzarella":
        for (fx, fy) in ((0.28, 0.3), (0.72, 0.3), (0.3, 0.72), (0.7, 0.7), (0.5, 0.5)):
            c = (s0 + (s1 - s0) * fx, t0 + (t1 - t0) * fy, z + 0.032)
            F += sphere(c, 0.035, 4, 8, m, lambda v: cell_uv(0, 2, 0.5, 0.5), zscale=0.9)
    elif kind == "olives":
        F += cell_box(s0 + 0.005, s1 - 0.005, t0 + 0.005, t1 - 0.005, z, z + 0.03, (1, 2), (1, 2))
    elif kind == "peppers":
        F += cell_box(s0 + 0.005, s1 - 0.005, t0 + 0.005, t1 - 0.005, z, z + 0.025, (2, 2), (2, 2))
    elif kind == "prosciutto":           # folded slices: low ridged slab
        F += cell_box(s0 + 0.01, s1 - 0.01, t0 + 0.01, t1 - 0.01, z, z + 0.02, (1, 1), (0, 1))
        for i in range(4):
            x = s0 + 0.03 + i * (s1 - s0 - 0.06) / 4
            F += cell_box(x, x + 0.05, t0 + 0.02, t1 - 0.02, z + 0.02, z + 0.035, (1, 1), (1, 1))
    # price tag (cream) stuck in front
    F += cell_box(s0 + 0.005, s0 + 0.012, tc - 0.03, tc + 0.03, z, z + 0.06, (0, 3), (0, 3))
    return F


def counters_faces():
    F = []
    for t0, t1 in CASES_T:
        F += deli_case(t0, t1)
    F += cabinet(COUNTER_FRONT, COUNTER_BACK, REGISTER_T[0], REGISTER_T[1], 1.02)
    F += cabinet(COUNTER_FRONT, COUNTER_BACK, GATE_T[0], GATE_T[1], 1.02)
    # coffee bar: body + terrazzo top with a 28 cm knee overhang towards the hall, steel foot rail
    F += cabinet(COUNTER_FRONT, COUNTER_BACK, COFFEE_T[0], COFFEE_T[1], 1.05, overhang=0.28)
    F += cyl_axis((COUNTER_FRONT - 0.18, COFFEE_T[0] + 0.05, 0.22), (COUNTER_FRONT - 0.18, COFFEE_T[1] - 0.05, 0.22), 0.022, 8,
                  MAT["brass"], lambda i, k: (i / 8, k * 3))
    for tt in (COFFEE_T[0] + 0.10, COFFEE_T[1] - 0.10):
        F += mbox(COUNTER_FRONT - 0.20, COUNTER_FRONT, tt - 0.015, tt + 0.015, 0.20, 0.24, "brass")
    # back counter: walnut doors (towards -s), steel top, steel backsplash on P1, open shelf above
    s0, s1 = BACK_S
    t0, t1 = BACK_T
    F += mbox(s0 + 0.06, s1, t0, t1, FLOOR, 0.10, "steel", skip=("-z",))
    F += mbox(s0, s1, t0, t1, 0.10, 0.88, "walnut", skip=("-z",))
    for k in range(9):                                                                          # door reveals
        tt = t0 + (t1 - t0) * (k + 1) / 10
        F += mbox(s0 - 0.004, s0, tt - 0.003, tt + 0.003, 0.14, 0.84, "steel")
    F += mbox(s0 - 0.02, s1, t0 - 0.01, t1 + 0.01, 0.88, 0.92, "steel")
    F += mbox(s1 - 0.012, s1, t0, t1, 0.92, 1.25, "steel", skip=("+x",))                       # backsplash
    F += slicer(s0 + 0.30, 2.05)
    F += slicer(s0 + 0.30, 3.05)
    return F


def slicer(sc, tc):
    """Simple deli slicer (original, ~250 tris): steel base, round blade with guard, carriage + pusher."""
    F = []
    z = 0.92
    F += mbox(sc - 0.20, sc + 0.20, tc - 0.17, tc + 0.17, z, z + 0.10, "steel")
    F += mbox(sc - 0.04, sc + 0.06, tc + 0.05, tc + 0.15, z + 0.10, z + 0.32, "steel")             # motor housing
    blade_c = (sc + 0.0, tc + 0.03, z + 0.26)
    F += cyl_axis((blade_c[0] - 0.012, blade_c[1], blade_c[2]), (blade_c[0] + 0.012, blade_c[1], blade_c[2]), 0.15, 16,
                  MAT["steel"], lambda i, k: (i / 16, k), lambda i: (0.5, 0.5), lambda i: (0.5, 0.5))
    F += cyl_axis((blade_c[0] - 0.03, blade_c[1], blade_c[2]), (blade_c[0] - 0.012, blade_c[1], blade_c[2]), 0.05, 10,
                  MAT["steel"], lambda i, k: (i / 10, k), lambda i: (0.5, 0.5), None)
    F += mbox(sc - 0.19, sc - 0.03, tc - 0.16, tc + 0.02, z + 0.10, z + 0.12, "steel")             # carriage plate
    F += mbox(sc - 0.19, sc - 0.03, tc - 0.16, tc - 0.13, z + 0.12, z + 0.20, "steel")             # back stop
    F += cyl_axis((sc - 0.11, tc - 0.10, z + 0.12), (sc - 0.11, tc - 0.10, z + 0.30), 0.012, 6, MAT["steel"],
                  lambda i, k: (i / 6, k), None, lambda i: (0.5, 0.5))                              # pusher arm
    F += cyl_axis((sc - 0.11, tc - 0.10, z + 0.30), (sc - 0.11, tc - 0.10, z + 0.34), 0.03, 8, MAT["brass"],
                  lambda i, k: (i / 8, k), lambda i: (0.5, 0.5), lambda i: (0.5, 0.5))              # knob
    return F


def counter_collision_boxes():
    out = []
    for t0, t1 in CASES_T:
        out.append(((COUNTER_FRONT, COUNTER_BACK, t0, t1, 0.0, 0.85), "WOOD_SOLID_MEDIUM"))
        out.append(((COUNTER_FRONT + 0.04, COUNTER_BACK, t0, t1, 0.85, 1.32), "GLASS_SHOOT_THROUGH"))
    out.append(((COUNTER_FRONT, COUNTER_BACK, REGISTER_T[0], REGISTER_T[1], 0.0, 1.02), "WOOD_SOLID_MEDIUM"))
    out.append(((COUNTER_FRONT, COUNTER_BACK, GATE_T[0], GATE_T[1], 0.0, 1.02), "WOOD_SOLID_MEDIUM"))
    out.append(((COUNTER_FRONT, COUNTER_BACK, COFFEE_T[0], COFFEE_T[1], 0.0, 1.05), "WOOD_SOLID_MEDIUM"))
    out.append(((COUNTER_FRONT - 0.28, COUNTER_FRONT, COFFEE_T[0], COFFEE_T[1], 1.01, 1.05), "WOOD_SOLID_MEDIUM"))
    out.append(((BACK_S[0] - 0.02, BACK_S[1], BACK_T[0], BACK_T[1], 0.0, 0.92), "METAL_SOLID_MEDIUM"))
    return out


# ================================================================== meat rail (hanging salumi) + lamps
def meat_rail_faces():
    F = []
    s = RAIL_S
    t0, t1 = RAIL_T
    br = MAT["brass"]
    F += cyl_axis((s, t0, RAIL_Z), (s, t1, RAIL_Z), 0.014, 8, br, lambda i, k: (i / 8, k * 6), lambda i: (0.5, 0.5), lambda i: (0.5, 0.5))
    for tt in (t0 + 0.05, (t0 + t1) / 2, t1 - 0.05):
        F += cyl_axis((s, tt, RAIL_Z), (s, tt, CEIL), 0.008, 6, br, lambda i, k: (i / 6, k * 2))
    m = MAT["food"]
    k = 0
    tt = t0 + 0.14
    while tt < t1 - 0.10:
        kind = ("salami", "provolone", "salami", "prosciutto", "salami", "salami", "provolone", "salami")[k % 8]
        top = RAIL_Z - 0.04 - 0.025 * (k % 3)
        F += cyl_axis((s, tt, RAIL_Z), (s, tt, top), 0.004, 4, m, lambda i, kk: cell_uv(1, 3, i / 4, kk))   # twine
        if kind == "salami":
            L = (0.30, 0.38, 0.26, 0.34)[k % 4]
            r = (0.036, 0.030, 0.042, 0.033)[k % 4]
            prof = [(top, 0.0), (top - 0.012, r * 0.7), (top - 0.03, r), (top - L + 0.03, r), (top - L + 0.01, r * 0.7), (top - L, 0.0)]
            F += lathe(s, tt, prof, 10, m, lambda u, kk: cell_uv(0, 0, u, kk / 5))
        elif kind == "provolone":       # pear-shaped cheese tied with cord
            L = 0.30
            prof = [(top, 0.0), (top - 0.03, 0.025), (top - 0.08, 0.045), (top - 0.15, 0.068), (top - 0.23, 0.075),
                    (top - 0.28, 0.06), (top - L, 0.0)]
            F += lathe(s, tt, prof, 12, m, lambda u, kk: cell_uv(2, 0, u, kk / 6))
            for zc, rr in ((top - 0.11, 0.059), (top - 0.19, 0.075)):
                F += frustum_z(s, tt, zc - 0.006, zc + 0.006, rr + 0.003, rr + 0.003, 12, m, uv=lambda i, z: cell_uv(1, 3, i / 12, 0.5), caps=(False, False))
        else:                           # prosciutto: hock up, rounded wide end down
            L = 0.52
            prof = [(top, 0.0), (top - 0.01, 0.022), (top - 0.08, 0.026), (top - 0.16, 0.055), (top - 0.28, 0.095),
                    (top - 0.40, 0.115), (top - 0.47, 0.10), (top - 0.51, 0.06), (top - L, 0.0)]
            F += lathe(s, tt, prof, 12, m, lambda u, kk: cell_uv(0, 1, u, kk / 8))
        tt += 0.19 + (0.06 if kind in ("prosciutto", "provolone") else 0.0)
        k += 1
    return F


PENDANTS = [(table_center(a)[0], -0.62, 2.05) for a in booth_bays()]
GLOBES = [(6.70, 1.55, 2.45), (6.70, 3.70, 2.45), (6.70, 5.85, 2.45)]


def lamps_faces():
    F = []
    br, gl = MAT["brass"], MAT["glow"]
    for (x, y, z) in PENDANTS:
        F += frustum_z(x, y, z, z + 0.20, 0.23, 0.07, 16, br, uv=lambda i, zz: (i / 16, zz * 4), caps=(False, True))
        F += flip(frustum_z(x, y, z + 0.002, z + 0.198, 0.226, 0.068, 16, br, uv=lambda i, zz: (i / 16, zz * 4), caps=(False, False)))
        F += sphere((x, y, z + 0.06), 0.05, 4, 8, gl, lambda v: (0.5, 0.5))
        F += cyl_axis((x, y, z + 0.20), (x, y, CEIL), 0.006, 6, br, lambda i, k: (i / 6, k * 2))
        F += frustum_z(x, y, CEIL - 0.02, CEIL, 0.06, 0.06, 12, br, caps=(True, False))
    for (x, y, z) in GLOBES:
        F += sphere((x, y, z), 0.16, 6, 12, gl, lambda v: (0.5, 0.5), zscale=1.05)
        F += frustum_z(x, y, z + 0.15, z + 0.22, 0.07, 0.05, 12, br, caps=(False, True))
        F += cyl_axis((x, y, z + 0.22), (x, y, CEIL), 0.006, 6, br, lambda i, k: (i / 6, k * 2))
        F += frustum_z(x, y, CEIL - 0.02, CEIL, 0.06, 0.06, 12, br, caps=(True, False))
    return F


def lights():
    """Point lights (MLO-local): pendants 2700K over the booths, globes over the cases, warm strips in the cases."""
    out = [dict(pos=(x, y, z + 0.02), color=(1.0, 0.76, 0.50), intensity=1.6, falloff=4.0, exponent=8.0) for (x, y, z) in PENDANTS]
    out += [dict(pos=(x, y, z), color=(1.0, 0.82, 0.62), intensity=1.4, falloff=5.0, exponent=8.0) for (x, y, z) in GLOBES]
    for t0, t1 in CASES_T:
        out.append(dict(pos=(COUNTER_BACK - 0.20, (t0 + t1) / 2, 1.20), color=(1.0, 0.86, 0.70), intensity=0.8, falloff=1.4, exponent=4.0))
    return out


# ================================================================== everything
def furniture_faces():
    return booths_faces() + counters_faces() + meat_rail_faces() + lamps_faces()


def collision_boxes():
    return booth_collision_boxes() + counter_collision_boxes() + partition_collision_boxes()


def box_tris(b):
    x0, x1, y0, y1, z0, z1 = b
    c8 = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return PG._box_tris(c8)


# ------------------------------------------------------------------ vanilla props (archetype name only, VANILLA_REF)
# HIGH-LOD bounds measured from the game files (gs_25d -> docs/_raw/vanilla_props_slice.json), model space.
VANILLA_BOUNDS = {
    "prop_till_01": ((-0.1953, -0.1738, -0.1191), (0.1953, 0.2827, 0.2832)),
    "v_ret_ml_scale": ((-0.1665, -0.1841, -0.0532), (0.1665, 0.1841, 0.0532)),
    "prop_coffee_mac_02": ((-0.1187, -0.2017, -0.2476), (0.1187, 0.1968, 0.2461)),
    "v_res_fa_bread01": ((-0.0747, -0.0869, -0.1724), (0.0752, 0.0762, 0.1724)),
    "v_res_fa_bread02": ((-0.0815, -0.0688, -0.1025), (0.0815, 0.0811, 0.1191)),
    "v_res_fa_chopbrd": ((-0.2427, -0.1807, -0.0103), (0.2427, 0.1807, 0.0103)),
    "prop_cleaver": ((-0.0737, -0.2266, 0.0005), (0.0737, 0.2241, 0.0205)),
    "prop_knife_stand": ((-0.0493, -0.2012, 0.0015), (0.0493, 0.2319, 0.3979)),
    "prop_bar_napkindisp": ((-0.1074, -0.1113, 0.0), (0.1074, 0.1113, 0.2861)),
    "prop_food_ketchup": ((-0.0337, -0.0337, -0.0), (0.0337, 0.0337, 0.2583)),
    "prop_food_mustard": ((-0.0337, -0.0337, -0.0), (0.0337, 0.0337, 0.2583)),
    "prop_food_sugarjar": ((-0.0488, -0.0488, -0.0), (0.0488, 0.0488, 0.2368)),
    "v_ilev_fh_kitchenstool": ((-0.1763, -0.1738, 0.0), (0.1753, 0.1758, 0.8545)),
    "v_19_vanmenuplain": ((-0.4834, -0.0293, -0.6538), (0.4834, 0.0293, 0.6538)),
    "tr_int1_chalkboard": ((-0.0195, -1.1138, -0.7856), (0.0195, 1.1138, 0.7856)),
}
MENU_BACK_S = P1_S[0] - 0.014           # just in front of the steel backsplash on P1


def vanilla_props():
    """(name, s, t, z_bottom, yaw_deg): yaw rotates the model about z in the MLO frame; the model's lowest point is put
    on z_bottom. Facings from the model normals (gs_25d): till keys on -y (yaw 90 -> staff side +s), espresso front -y
    (yaw -90 -> faces the staff aisle), menu board front +y (yaw 90 -> faces -s), chalkboard front +x (yaw 180)."""
    out = []
    bs = BACK_S[0]
    out += [("prop_till_01", 7.45, 5.10, 1.02, 90.0)]
    out += [("v_ret_ml_scale", bs + 0.30, 1.10, 0.92, 90.0)]
    out += [("prop_coffee_mac_02", P1_S[0] - 0.012 - 0.21, 5.95, 0.92, -90.0)]
    out += [("v_res_fa_bread01", bs + 0.30, 4.35, 0.92, 0.0), ("v_res_fa_bread02", bs + 0.30, 4.60, 0.92, 15.0)]
    out += [("v_res_fa_chopbrd", bs + 0.32, 3.85, 0.92, 90.0), ("prop_cleaver", bs + 0.30, 3.85, 0.941, 80.0)]
    out += [("prop_knife_stand", bs + 0.55, 5.25, 0.92, 0.0)]
    for a in booth_bays():
        sc, tc = table_center(a)
        out += [("prop_bar_napkindisp", sc, -1.02, 0.765, 90.0), ("prop_food_ketchup", sc - 0.12, -1.04, 0.765, 0.0),
                ("prop_food_mustard", sc + 0.12, -1.04, 0.765, 0.0)]
    out += [("prop_food_sugarjar", COUNTER_FRONT - 0.12, 5.80, 1.05, 0.0), ("prop_food_sugarjar", COUNTER_FRONT - 0.12, 6.50, 1.05, 0.0)]
    for tt in (5.70, 6.15, 6.60):
        out.append(("v_ilev_fh_kitchenstool", COUNTER_FRONT - 0.48, tt, FLOOR, 0.0))
    # menus (user choice 2026-10-30): 2 x "Today's Specials" at the ends + the blank chalkboard in the middle, on P1
    mb = VANILLA_BOUNDS["v_19_vanmenuplain"]
    cb = VANILLA_BOUNDS["tr_int1_chalkboard"]
    out += [("v_19_vanmenuplain", MENU_BACK_S - mb[1][1], 1.30, 1.35, 90.0),
            ("v_19_vanmenuplain", MENU_BACK_S - mb[1][1], 5.40, 1.35, 90.0),
            ("tr_int1_chalkboard", MENU_BACK_S - cb[1][0], 3.35, 1.19, 180.0)]
    return out


def vanilla_entities():
    """-> (name, (s, t, z) of the model origin, yaw_rad) with the bounds applied."""
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        mn = VANILLA_BOUNDS[name][0]
        out.append((name, (round(s, 4), round(t, 4), round(zb - mn[2], 4)), math.radians(yaw)))
    return out
