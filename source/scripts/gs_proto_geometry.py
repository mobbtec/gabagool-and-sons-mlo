# LONG PIG (resource id gabagool_sons_mlo) — prototype interior geometry (pure Python, no bpy).
# 0.2.0: floor / ceiling UVs for the CC0 slice textures (FLOOR_UV_M, CEIL_UV_M); partitions + furniture: gs_slice_geometry.py
# 0.1.6: D3 = prop_map_door_01 like D2 (user choice), leaves 1.5 cm above floor / thresholds (were rubbing and stayed
#        ajar), reveals run up to the vanilla stops (no light slits), interior door holes as high as the GTA leaves.
# 0.1.5: all doors are vanilla GTA V models (v_ilev_csr_door_l/_r, prop_map_door_01, prop_sc1_12_door) placed behind the
#        vanilla frame stops; dark wood casings, window stools/aprons, tiled landings, portals outside the door handles.
# 0.1.4: interior window frames reach the vanilla frame front and the reveal (no light strips), back doors
#        D2 / D3 (wall openings, reveals, interior landings, portals, steel leaves), MLO wall collision exactly on the
#        visible wall faces (audit 05: vanilla collision sits 0.5-13 cm behind them), vertex colours (CPV).
#
# Everything is in the MLO-local frame of the building (docs/01):
#   x = s (along the SW facade), y = t (into the building), z = world Z - 24.45
# The MLO instance is placed at world (411.655, -1912.045, 24.45) with yaw -45.94 deg.
#
# The interior surfaces sit on the inner faces of the VANILLA collision walls, the openings sit exactly
# on the verified vanilla openings W1, W2, D1, so the interior lines up with the untouched exterior shell.
import math

import gs_overrides as G

Z0 = G.FLOOR_Z               # 24.45 world = local 0
FLOOR = 0.015                # visual + collision floor top (1.5 cm above the vanilla sidewalk that pokes inside)
CEIL = 3.40                  # prototype drop ceiling (window head 2.576, roof slab 5.72)
WAINSCOT = 1.00              # top of the dark wood band
FLOOR_UV_M = 2.0             # 0.2.0: metres per floor texture (lp_floor_checker = Tiles139, 6 x 6 tiles of 33 cm)
CEIL_UV_M = 5.15             # 0.2.0: metres per ceiling texture (lp_ceiling_tile = OfficeCeiling003, 8 x 8 tiles of 64 cm)

XW, YS, YN, XE = -2.90, -1.23, 11.42, 16.15   # inner faces of NW, SW, NE, SE walls (vanilla collision)
CH_IN = -0.46                                 # inner face of the corner chamfer (dep)

# openings (local)
# 0.1.4: frame boxes run from 5 mm behind the vanilla frame front (-1.500 / -3.114) to the reveal plane and are
#        1 mm wider than the vanilla mullions, so no light strip shows between frame, reveal and vanilla frame sides
W1 = dict(s=(1.263, 5.654), z=(25.052 - Z0, 27.026 - Z0), glass_t=-1.440, reveal_to=-1.383,
          mullions=[(1.263, 1.332), (2.637, 2.790), (4.131, 4.270), (5.575, 5.654)], frame_t=(-1.495, -1.383))
W2 = dict(t=(3.455, 6.394), z=(25.052 - Z0, 27.026 - Z0), glass_s=-3.055, reveal_to=-3.030,
          mullions=[(3.455, 3.534), (4.840, 4.979), (6.319, 6.394)], frame_s=(-3.109, -3.030))
FRAME_PAD = 0.001
# 0.1.4 back doors (vanilla steel doors, painted leaf removed in the build2 override)
# 0.1.5: vanilla frame stops measured in sc1_14_build2: D2 t -1.438..-1.403, D3 s -3.044..-3.014 (head z 2.628..2.681),
#        the new GTA leaves sit right behind the stops; our reveals stop 3-5 mm before the leaves (no coplanar strips)
D2 = dict(s=(13.914, 15.133), z=(24.629 - Z0, 27.078 - Z0), stop_t=(-1.438, -1.403), reveal_to=-1.403,
          landing_top=0.181, landing_depth=0.45)
D3 = dict(t=(9.183, 10.402), z=(24.689 - Z0, 27.078 - Z0), stop_s=(-3.044, -3.014), reveal_to=-3.014,
          landing_top=0.241, landing_depth=0.45, step_depth=0.25)
RAIL = 0.055
# D1: vanilla aluminium frame kept in build2 (jambs a 1.688..1.727 / 3.605..3.641, head z 2.525..2.576, dep -0.117..-0.087)
D1 = dict(a=(1.696, 3.624), z=(0.0, 27.026 - Z0), reveal_to=-0.179, trim_dep=(-0.179, -0.118),
          leaf_dep=-0.160, threshold_dep=-0.120)

# 0.1.5: every door is a vanilla GTA V door model, referenced by name only (nothing of Rockstar is shipped).
# bbox = HIGH-LOD model bounds in the model's own frame, measured from the game files (docs/_raw/vanilla_doors*.json);
# all four have the hinge on the model's x = 0 axis and the leaf along +x (csr_l, sc1_12) or -x (csr_r, map_door_01).
VDOORS = {
    "v_ilev_csr_door_l": dict(min=(0.0, -0.10303, -1.24072), max=(0.95508, 0.10596, 1.25146)),
    "v_ilev_csr_door_r": dict(min=(-0.95654, -0.10449, -1.24609), max=(-0.00098, 0.10449, 1.24609)),
    "prop_map_door_01": dict(min=(-1.21875, -0.11621, -1.06934), max=(0.0, 0.06592, 1.37012)),
    "prop_sc1_12_door": dict(min=(0.0, -0.12695, -1.17627), max=(1.21338, 0.02051, 1.17627)),
}
DOOR_GAP = 0.015          # 0.1.6: leaf bottom above the floor / threshold (0.004 -> the leaves rubbed and stayed ajar)

_D1_MID = (D1["a"][0] + D1["a"][1]) / 2.0
D1["hinge_a"] = (round(_D1_MID - VDOORS["v_ilev_csr_door_l"]["max"][0] - 0.0005, 4),
                 round(_D1_MID - VDOORS["v_ilev_csr_door_r"]["min"][0] + 0.0005, 4))      # (1.7044, 3.6170)
D1_LEAF_TOP = FLOOR + DOOR_GAP + (VDOORS["v_ilev_csr_door_l"]["max"][2] - VDOORS["v_ilev_csr_door_l"]["min"][2])
D2_LEAF_T = D2["stop_t"][1] + 0.003          # origin of prop_map_door_01 (yaw pi: slab local y -0.05..0 -> t -1.400..-1.350)
D3_LEAF_S = D3["stop_s"][1] + 0.003           # 0.1.6 origin of prop_map_door_01 (yaw +pi/2: slab local y -0.05..0 -> s -3.011..-2.961)
D2_LEAF_TOP = D2["landing_top"] + DOOR_GAP + (VDOORS["prop_map_door_01"]["max"][2] - VDOORS["prop_map_door_01"]["min"][2])
D3_LEAF_TOP = D3["landing_top"] + DOOR_GAP + (VDOORS["prop_map_door_01"]["max"][2] - VDOORS["prop_map_door_01"]["min"][2])
# 0.1.6: the steel leaves are taller than the vanilla openings (D3 by 6.7 cm): the interior holes are as high as the leaves,
# so a leaf swinging into the room never cuts through our soffit / casing (outside it slides behind the vanilla lintel)
D2["hole_top"] = round(max(D2["z"][1], D2_LEAF_TOP + 0.02), 3)
D3["hole_top"] = round(max(D3["z"][1], D3_LEAF_TOP + 0.02), 3)
CASING_W = 0.075          # interior door / window casings (dark wood), width and projection from the wall
CASING_P = 0.018


def ch(a, dep):
    s, t = G.chamfer_to_local(a, dep)
    return (float(s), float(t))


def ch_a_of(s, t):
    a, dep = G.chamfer((s, t))
    return float(a), float(dep)


def _chamfer_hit_t(t_value, dep=CH_IN):
    """a on the chamfer line (at depth dep) where y == t_value"""
    base = G.CH_A0 + dep * G.CH_OUT
    return float((t_value - base[1]) / G.CH_DIR[1])


def _chamfer_hit_s(s_value, dep=CH_IN):
    base = G.CH_A0 + dep * G.CH_OUT
    return float((s_value - base[0]) / G.CH_DIR[0])


A_SW = _chamfer_hit_t(YS)           # chamfer meets SW wall
A_NW = _chamfer_hit_s(XW)           # chamfer meets NW wall
P_SW = ch(A_SW, CH_IN)
P_NW = ch(A_NW, CH_IN)

FLOOR_POLY = [P_SW, (XE, YS), (XE, YN), (XW, YN), P_NW]        # convex pentagon (CCW seen from above)
DOOR_STRIP = [ch(D1["a"][0], CH_IN), ch(D1["a"][0], D1["threshold_dep"]), ch(D1["a"][1], D1["threshold_dep"]), ch(D1["a"][1], CH_IN)]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def face(verts, normal, mat, uv_fn):
    """Return a face record with verts ordered so the geometric normal matches `normal`."""
    n = _cross(_sub(verts[1], verts[0]), _sub(verts[2], verts[0]))
    if _dot(n, normal) < 0:
        verts = list(reversed(verts))
    return {"v": [tuple(round(c, 5) for c in v) for v in verts], "uv": [uv_fn(v) for v in verts], "mat": mat}


class Wall:
    """Vertical wall plane: p(u, z) = start + u * d (2D), facing `n` (2D, into the room)."""

    def __init__(self, name, start, end, n):
        self.name = name
        self.start = start
        L = math.hypot(end[0] - start[0], end[1] - start[1])
        self.L = L
        self.d = ((end[0] - start[0]) / L, (end[1] - start[1]) / L)
        self.n = n
        self.holes = []  # (u0, u1, z0, z1, reveal_depth, kind)

    def p(self, u, z, depth=0.0):
        return (self.start[0] + u * self.d[0] - depth * self.n[0], self.start[1] + u * self.d[1] - depth * self.n[1], z)

    def uv(self, su, sv, u_off=0.0):
        def f(v):
            # u along the wall from its start, v = height
            du = (v[0] - self.start[0]) * self.d[0] + (v[1] - self.start[1]) * self.d[1]
            return ((du + u_off) / su, v[2] / sv)
        return f

    def faces(self, mats):
        out = []
        n3 = (self.n[0], self.n[1], 0.0)
        cuts = sorted({0.0, self.L} | {h[0] for h in self.holes} | {h[1] for h in self.holes})
        for u0, u1 in zip(cuts[:-1], cuts[1:]):
            if u1 - u0 < 1e-4:
                continue
            um = (u0 + u1) / 2
            spans = [(FLOOR, CEIL)]
            for h in self.holes:
                if h[0] < um < h[1]:
                    new = []
                    for z0, z1 in spans:
                        if h[2] > z0:
                            new.append((z0, min(z1, h[2])))
                        if h[3] < z1:
                            new.append((max(z0, h[3]), z1))
                    spans = [s for s in new if s[1] - s[0] > 1e-4]
            for z0, z1 in spans:
                # split at the wainscot line
                bands = []
                if z0 < WAINSCOT < z1:
                    bands = [(z0, WAINSCOT, "wood"), (WAINSCOT, z1, "wall")]
                else:
                    bands = [(z0, z1, "wood" if z1 <= WAINSCOT + 1e-6 else "wall")]
                for b0, b1, kind in bands:
                    vs = [self.p(u0, b0), self.p(u1, b0), self.p(u1, b1), self.p(u0, b1)]
                    if kind == "wood":
                        out.append(face(vs, n3, mats["wood"], self.uv(0.6, 1.0)))
                    else:
                        out.append(face(vs, n3, mats["wall"], self.uv(2.0, 2.0)))
        # reveals of the openings
        for (u0, u1, z0, z1, depth, kind) in self.holes:
            d3 = (self.d[0], self.d[1], 0.0)
            # jambs
            out.append(face([self.p(u0, z0), self.p(u0, z0, depth), self.p(u0, z1, depth), self.p(u0, z1)], d3, mats["wall"], self.uv(2.0, 2.0)))
            out.append(face([self.p(u1, z0), self.p(u1, z0, depth), self.p(u1, z1, depth), self.p(u1, z1)], (-d3[0], -d3[1], 0.0), mats["wall"], self.uv(2.0, 2.0)))
            # head
            out.append(face([self.p(u0, z1), self.p(u1, z1), self.p(u1, z1, depth), self.p(u0, z1, depth)], (0, 0, -1), mats["wall"], lambda v: (v[0] / 2.0, v[1] / 2.0)))
            if kind == "window":  # sill (wood)
                out.append(face([self.p(u0, z0), self.p(u1, z0), self.p(u1, z0, depth), self.p(u0, z0, depth)], (0, 0, 1), mats["wood"], lambda v: (v[0] / 0.6, v[1] / 0.6)))
        return out


def box(x0, x1, y0, y1, z0, z1, mat, uv_scale=1.0):
    """Axis aligned box (6 faces, outward)."""
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    uvp = lambda v: ((v[0] + v[1]) / uv_scale, v[2] / uv_scale)
    uvz = lambda v: (v[0] / uv_scale, v[1] / uv_scale)
    return [
        face([c[0], c[1], c[2], c[3]], (0, 0, -1), mat, uvz), face([c[4], c[5], c[6], c[7]], (0, 0, 1), mat, uvz),
        face([c[0], c[1], c[5], c[4]], (0, -1, 0), mat, uvp), face([c[2], c[3], c[7], c[6]], (0, 1, 0), mat, uvp),
        face([c[1], c[2], c[6], c[5]], (1, 0, 0), mat, uvp), face([c[3], c[0], c[4], c[7]], (-1, 0, 0), mat, uvp),
    ]


def oriented_box(center2, ax2, half_u, half_v, z0, z1, mat):
    """Box whose horizontal axes are ax2 (2D unit) and its perpendicular."""
    ux, uy = ax2
    vx, vy = -uy, ux
    cx, cy = center2
    pts = []
    for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        pts.append((cx + su * half_u * ux + sv * half_v * vx, cy + su * half_u * uy + sv * half_v * vy))
    b = [(p[0], p[1], z0) for p in pts]
    t = [(p[0], p[1], z1) for p in pts]
    uvp = lambda v: ((v[0] * ux + v[1] * uy), v[2])
    uvz = lambda v: (v[0], v[1])
    out = [face(b, (0, 0, -1), mat, uvz), face(t, (0, 0, 1), mat, uvz)]
    sides = [((0, 1), (-vx, -vy)), ((1, 2), (ux, uy)), ((2, 3), (vx, vy)), ((3, 0), (-ux, -uy))]
    for (i, j), n in sides:
        out.append(face([b[i], b[j], t[j], t[i]], (n[0], n[1], 0.0), mat, uvp))
    return out


def shell_faces():
    """Floor, ceiling, walls with openings + reveals, interior window frames, door trims."""
    mats = {"floor": 0, "wall": 1, "wood": 2, "ceiling": 3, "trim": 4, "alu": 5}
    F = []
    # floor + ceiling
    fl = lambda v: (v[0] / FLOOR_UV_M, v[1] / FLOOR_UV_M)
    cl = lambda v: (v[0] / CEIL_UV_M, v[1] / CEIL_UV_M)
    F.append(face([(x, y, FLOOR) for x, y in FLOOR_POLY], (0, 0, 1), mats["floor"], fl))
    F.append(face([(x, y, FLOOR) for x, y in DOOR_STRIP], (0, 0, 1), mats["floor"], fl))
    F.append(face([(x, y, CEIL) for x, y in FLOOR_POLY], (0, 0, -1), mats["ceiling"], cl))

    walls = []
    sw = Wall("SW", P_SW, (XE, YS), (0.0, 1.0))
    sw.holes.append((W1["s"][0] - P_SW[0], W1["s"][1] - P_SW[0], W1["z"][0], W1["z"][1], abs(W1["reveal_to"] - YS), "window"))
    sw.holes.append((D2["s"][0] - P_SW[0], D2["s"][1] - P_SW[0], FLOOR, D2["hole_top"], abs(D2["reveal_to"] - YS), "door"))
    walls.append(sw)
    walls.append(Wall("SE", (XE, YS), (XE, YN), (-1.0, 0.0)))
    walls.append(Wall("NE", (XE, YN), (XW, YN), (0.0, -1.0)))
    nw = Wall("NW", (XW, YN), P_NW, (1.0, 0.0))
    nw.holes.append((YN - W2["t"][1], YN - W2["t"][0], W2["z"][0], W2["z"][1], abs(W2["reveal_to"] - XW), "window"))
    nw.holes.append((YN - D3["t"][1], YN - D3["t"][0], FLOOR, D3["hole_top"], abs(D3["reveal_to"] - XW), "door"))
    walls.append(nw)
    chw = Wall("CH", P_NW, P_SW, (-G.CH_OUT[0], -G.CH_OUT[1]))
    # u along chamfer wall runs from a = A_NW down to a = A_SW
    chw.holes.append((A_NW - D1["a"][1], A_NW - D1["a"][0], FLOOR, D1["z"][1], abs(D1["reveal_to"] - CH_IN), "door"))
    walls.append(chw)
    for w in walls:
        F += w.faces(mats)
    # 0.1.5: landings / steps up to the back door thresholds: tiled top (same floor), dark wood risers
    for b in back_door_steps():
        F += step_faces(*b, mats)

    # interior side of the window frames (vanilla mullions are one-sided, seen only from the street)
    # 0.1.5: clear aluminium like the vanilla frames (bronze trim read as a dark tunnel from the street)
    t0, t1 = W1["frame_t"]
    p = FRAME_PAD
    for s0, s1 in W1["mullions"]:
        F += box(s0 - p, s1 + p, t0, t1, W1["z"][0] - p, W1["z"][1] + p, mats["alu"])
    F += box(W1["s"][0] - p, W1["s"][1] + p, t0, t1, W1["z"][0] - p, W1["z"][0] + RAIL, mats["alu"])
    F += box(W1["s"][0] - p, W1["s"][1] + p, t0, t1, W1["z"][1] - RAIL - 0.009, W1["z"][1] + p, mats["alu"])
    s0_, s1_ = W2["frame_s"]
    for a0, a1 in W2["mullions"]:
        F += box(s0_, s1_, a0 - p, a1 + p, W2["z"][0] - p, W2["z"][1] + p, mats["alu"])
    F += box(s0_, s1_, W2["t"][0] - p, W2["t"][1] + p, W2["z"][0] - p, W2["z"][0] + RAIL, mats["alu"])
    F += box(s0_, s1_, W2["t"][0] - p, W2["t"][1] + p, W2["z"][1] - RAIL - 0.009, W2["z"][1] + p, mats["alu"])

    # D1: narrow trims between the GTA leaves and our reveal + head filler above the leaves (behind the vanilla frame)
    cd = (float(G.CH_DIR[0]), float(G.CH_DIR[1]))
    d0, d1 = D1["trim_dep"]
    dep_c, dep_h = (d0 + d1) / 2, (d1 - d0) / 2
    for a0, a1 in ((D1["a"][0], D1["hinge_a"][0]), (D1["hinge_a"][1], D1["a"][1])):
        F += oriented_box(ch((a0 + a1) / 2, dep_c), cd, (a1 - a0) / 2, dep_h, FLOOR, D1["z"][1], mats["alu"])
    hd0, hd1 = D1["leaf_dep"] - 0.045, D1["trim_dep"][1]
    F += oriented_box(ch((D1["a"][0] + D1["a"][1]) / 2, (hd0 + hd1) / 2), cd, (D1["a"][1] - D1["a"][0]) / 2, (hd1 - hd0) / 2,
                      D1_LEAF_TOP + 0.005, D1["z"][1], mats["alu"])
    # 0.1.6: dark steel strip on the vanilla head stops of D2 / D3 seen from the room above the leaves (keeps 6 materials)
    F += box(D2["s"][0], D2["s"][1], D2["stop_t"][0], D2["stop_t"][1] + 0.001, D2["z"][1], D2["hole_top"], mats["trim"])
    F += box(D3["stop_s"][0], D3["stop_s"][1] + 0.001, D3["t"][0], D3["t"][1], D3["z"][1], D3["hole_top"], mats["trim"])

    # 0.1.5: dark wood casings around every opening on the room side + window stools / aprons
    for w in walls:
        for (u0, u1, z0, z1, depth, kind) in w.holes:
            F += casing_faces(w, u0, u1, z0, z1, depth, kind, mats)
    return F


def wall_box(w, u0, u1, z0, z1, e0, e1, mat):
    """Box in the frame of wall w: u along the wall, z up, e = distance in front of the wall face (into the room)."""
    c = [w.p(u0, z0, -e0), w.p(u1, z0, -e0), w.p(u1, z0, -e1), w.p(u0, z0, -e1),
         w.p(u0, z1, -e0), w.p(u1, z1, -e0), w.p(u1, z1, -e1), w.p(u0, z1, -e1)]
    d3, n3 = (w.d[0], w.d[1], 0.0), (w.n[0], w.n[1], 0.0)
    uvw = w.uv(0.6, 0.6)
    uvz = lambda v: (v[0] / 0.6, v[1] / 0.6)
    return [face([c[0], c[1], c[2], c[3]], (0, 0, -1), mat, uvz), face([c[4], c[5], c[6], c[7]], (0, 0, 1), mat, uvz),
            face([c[0], c[1], c[5], c[4]], (-n3[0], -n3[1], 0), mat, uvw), face([c[2], c[3], c[7], c[6]], n3, mat, uvw),
            face([c[1], c[2], c[6], c[5]], d3, mat, uvw), face([c[3], c[0], c[4], c[7]], (-d3[0], -d3[1], 0), mat, uvw)]


def casing_faces(w, u0, u1, z0, z1, depth, kind, mats):
    """Interior casing (architrave) around a hole of wall w; windows also get a stool (sill board) and an apron.
    Door legs start on the landing (D2 / D3) or on the floor."""
    W, P = CASING_W, CASING_P
    wood = mats["wood"]
    ua, ub = max(0.0, u0 - W), min(w.L, u1 + W)
    out = []
    if kind == "window":
        out += wall_box(w, ua - 0.02, ub + 0.02, z0 - 0.005, z0 + 0.024, -depth, 0.035, wood)      # stool over the sill
        out += wall_box(w, ua, ub, z0 - 0.11, z0 - 0.005, 0.0, 0.015, wood)                       # apron
        zl = z0 + 0.024
    else:
        zl = {"SW": D2["landing_top"], "NW": D3["landing_top"]}.get(w.name, FLOOR)   # back doors: legs stand on the landing
    out += wall_box(w, ua, u0, zl, z1 + W, 0.0, P, wood)
    out += wall_box(w, u1, ub, zl, z1 + W, 0.0, P, wood)
    out += wall_box(w, ua, ub, z1, z1 + W, 0.0, P, wood)
    return out


def step_faces(x0, x1, y0, y1, z0, z1, mats):
    """Landing / step: floor tiles on top, dark wood risers (no bottom face)."""
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    fl = lambda v: (v[0] / FLOOR_UV_M, v[1] / FLOOR_UV_M)
    uvp = lambda v: ((v[0] + v[1]) / 0.6, v[2] / 1.0)
    return [face([c[4], c[5], c[6], c[7]], (0, 0, 1), mats["floor"], fl),
            face([c[0], c[1], c[5], c[4]], (0, -1, 0), mats["wood"], uvp), face([c[2], c[3], c[7], c[6]], (0, 1, 0), mats["wood"], uvp),
            face([c[1], c[2], c[6], c[5]], (1, 0, 0), mats["wood"], uvp), face([c[3], c[0], c[4], c[7]], (-1, 0, 0), mats["wood"], uvp)]


def glass_faces(which):
    """Two-sided glass pane filling the whole frame (frames cover the edges)."""
    out = []
    g = lambda v: (0.5, 0.5)
    if which == "W1":
        t = W1["glass_t"]
        for dt, n in ((-0.002, (0, -1, 0)), (0.002, (0, 1, 0))):
            vs = [(W1["s"][0], t + dt, W1["z"][0]), (W1["s"][1], t + dt, W1["z"][0]), (W1["s"][1], t + dt, W1["z"][1]), (W1["s"][0], t + dt, W1["z"][1])]
            out.append(face(vs, n, 0, g))
    else:
        s = W2["glass_s"]
        for ds, n in ((-0.002, (-1, 0, 0)), (0.002, (1, 0, 0))):
            vs = [(s + ds, W2["t"][0], W2["z"][0]), (s + ds, W2["t"][1], W2["z"][0]), (s + ds, W2["t"][1], W2["z"][1]), (s + ds, W2["t"][0], W2["z"][1])]
            out.append(face(vs, n, 0, g))
    return out


def vanilla_door_entities():
    """0.1.5: all door leaves are vanilla GTA V door models (archetype referenced by name, never shipped).
    Returns (id, archetype, position, yaw_rad, portal). Positions are the model origins in the MLO frame:
    hinge axis at the opening edge, leaf bottom DOOR_GAP above the floor / landing, slab right behind the vanilla stop."""
    th = math.atan2(float(G.CH_DIR[1]), float(G.CH_DIR[0]))
    zl = FLOOR + DOOR_GAP - VDOORS["v_ilev_csr_door_l"]["min"][2]
    zr = FLOOR + DOOR_GAP - VDOORS["v_ilev_csr_door_r"]["min"][2]
    l = ch(D1["hinge_a"][0], D1["leaf_dep"])
    r = ch(D1["hinge_a"][1], D1["leaf_dep"])
    z2 = D2["landing_top"] + DOOR_GAP - VDOORS["prop_map_door_01"]["min"][2]
    z3 = D3["landing_top"] + DOOR_GAP - VDOORS["prop_map_door_01"]["min"][2]
    r4 = lambda p: tuple(round(float(c), 4) for c in p)
    return [
        ("gs_d1_left", "v_ilev_csr_door_l", r4((l[0], l[1], zl)), th, "D1"),          # leaf along +a
        ("gs_d1_right", "v_ilev_csr_door_r", r4((r[0], r[1], zr)), th, "D1"),         # leaf along -a
        ("gs_d2", "prop_map_door_01", r4((D2["s"][0], D2_LEAF_T, z2)), math.pi, "D2"),   # hinge s 13.914, closer inside
        ("gs_d3", "prop_map_door_01", r4((D3_LEAF_S, D3["t"][1], z3)), math.pi / 2, "D3"),   # 0.1.6, hinge t 10.402, closer inside
    ]


def door_entities():
    return [e for e in vanilla_door_entities() if e[4] == "D1"]


def back_door_entities():
    return [e for e in vanilla_door_entities() if e[4] != "D1"]


def door_leaf_world_boxes():
    """Closed-leaf extents in the MLO frame (8 corners per door) -> clearance checks against walls / casings / portals."""
    out = {}
    for did, arch, pos, yaw, pk in vanilla_door_entities():
        mn, mx = VDOORS[arch]["min"], VDOORS[arch]["max"]
        c, s_ = math.cos(yaw), math.sin(yaw)
        pts = []
        for x in (mn[0], mx[0]):
            for y in (mn[1], mx[1]):
                for z in (mn[2], mx[2]):
                    pts.append((pos[0] + x * c - y * s_, pos[1] + x * s_ + y * c, pos[2] + z))
        out[did] = pts
    return out


def back_door_steps():
    """Interior landings (and the second D3 step) up to the vanilla thresholds: boxes (x0, x1, y0, y1, z0, z1).
    0.1.5: as wide as the casings, 2 mm above the vanilla threshold tops (0.179 / 0.239) -> no z-fighting."""
    m = CASING_W
    out = [(D2["s"][0] - m, D2["s"][1] + m, D2["reveal_to"], YS + D2["landing_depth"], FLOOR, D2["landing_top"])]
    out.append((D3["reveal_to"], XW + D3["landing_depth"], D3["t"][0] - m, D3["t"][1] + m, FLOOR, D3["landing_top"]))
    out.append((XW + D3["landing_depth"], XW + D3["landing_depth"] + D3["step_depth"], D3["t"][0] - m, D3["t"][1] + m,
                FLOOR, round((FLOOR + D3["landing_top"]) / 2, 3)))
    return out


def portals():
    """Exit portals (room gs_front -> limbo), slightly outside the interior glass / leaves.
    Corner order gives a normal pointing OUT of the room, towards limbo (the to-room).
    0.1.3: was reversed (normal into the room) -> in game the street was not drawn through the openings
    from inside, and leaving the room was not tracked. The working dealer_map MLO on the server has every
    1->0 portal with the normal pointing away from its room (dot = -1), see docs/03."""
    return {k: list(reversed(c)) for k, c in _portals_room_facing().items()}


def _portals_room_facing():
    m = 0.02
    out = {}
    t = -1.470
    s0, s1 = W1["s"][0] - m, W1["s"][1] + m
    z0, z1 = W1["z"][0] - m, W1["z"][1] + m
    out["W1"] = [(s0, t, z1), (s1, t, z1), (s1, t, z0), (s0, t, z0)]
    s = -3.085
    t0, t1 = W2["t"][0] - m, W2["t"][1] + m
    out["W2"] = [(s, t1, z1), (s, t0, z1), (s, t0, z0), (s, t1, z0)]
    dep = -0.030          # 0.1.5: outside the GTA leaves incl. their pull handles (leaf -0.160 +- 0.106)
    pa = ch(D1["a"][0] - m, dep)
    pb = ch(D1["a"][1] + m, dep)
    zt = D1["z"][1] + m
    out["D1"] = [(pb[0], pb[1], zt), (pa[0], pa[1], zt), (pa[0], pa[1], -m), (pb[0], pb[1], -m)]
    # back doors, 0.1.5: outside the GTA leaves incl. outer lever / knob, inside the vanilla reveals
    t = -1.500
    s0, s1 = D2["s"][0] - m, D2["s"][1] + m
    z0, z1 = D2["z"][0] - m, D2["z"][1] + m
    out["D2"] = [(s0, t, z1), (s1, t, z1), (s1, t, z0), (s0, t, z0)]
    s = -3.150
    t0, t1 = D3["t"][0] - m, D3["t"][1] + m
    z0, z1 = D3["z"][0] - m, D3["z"][1] + m
    out["D3"] = [(s, t1, z1), (s, t0, z1), (s, t0, z0), (s, t1, z0)]
    return out


def portal_normal(c):
    n = _cross(_sub(c[1], c[0]), _sub(c[2], c[0]))
    L = math.sqrt(_dot(n, n))
    return tuple(x / L for x in n)


ROOM_BB = ((-3.15, -1.55, -0.10), (16.25, 11.55, CEIL + 0.10))

LIGHTS = [  # (x, y, z) local, warm interior points under the ceiling
    (1.5, 3.5, CEIL - 0.15), (6.0, 2.0, CEIL - 0.15), (11.0, 2.5, CEIL - 0.15),
    (3.5, 8.5, CEIL - 0.15), (9.0, 8.0, CEIL - 0.15), (14.0, 8.0, CEIL - 0.15),
]


def floor_slab_tris(z_top, thick):
    """Closed slab under FLOOR_POLY + DOOR_STRIP for the MLO collision (list of triangles)."""
    tris = []
    for poly in (FLOOR_POLY, DOOR_STRIP):
        top = [(x, y, z_top) for x, y in poly]
        bot = [(x, y, z_top - thick) for x, y in poly]
        for i in range(1, len(poly) - 1):
            tris.append((top[0], top[i], top[i + 1]))
            tris.append((bot[0], bot[i + 1], bot[i]))
        for i in range(len(poly)):
            j = (i + 1) % len(poly)
            tris.append((bot[i], bot[j], top[j]))
            tris.append((bot[i], top[j], top[i]))
    return tris


def _box_tris(c8):
    """c8: 8 corners [b0..b3 (bottom ring), t0..t3 (top ring)] of a convex hexahedron -> 12 triangles, outward."""
    b, t = c8[:4], c8[4:]
    quads = [(b[0], b[3], b[2], b[1]), (t[0], t[1], t[2], t[3])]
    for i in range(4):
        j = (i + 1) % 4
        quads.append((b[i], b[j], t[j], t[i]))
    cen = tuple(sum(p[k] for p in c8) / 8 for k in range(3))
    tris = []
    for q in quads:
        for tri in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
            n = _cross(_sub(tri[1], tri[0]), _sub(tri[2], tri[0]))
            mid = tuple(sum(p[k] for p in tri) / 3 for k in range(3))
            if _dot(n, _sub(mid, cen)) < 0:
                tri = (tri[0], tri[2], tri[1])
            tris.append(tri)
    return tris


def _solid_spans(wall):
    """Wall rectangles (u0, u1, z0, z1) that are solid, i.e. the wall minus its openings, floor..ceiling."""
    cuts = sorted({0.0, wall.L} | {h[0] for h in wall.holes} | {h[1] for h in wall.holes})
    out = []
    for u0, u1 in zip(cuts[:-1], cuts[1:]):
        if u1 - u0 < 1e-4:
            continue
        um = (u0 + u1) / 2
        spans = [(0.0, CEIL)]
        for h in wall.holes:
            if h[0] < um < h[1]:
                new = []
                for z0, z1 in spans:
                    if h[2] > z0 + 1e-6:
                        new.append((z0, min(z1, h[2])))
                    if h[3] < z1:
                        new.append((max(z0, h[3]), z1))
                spans = [x for x in new if x[1] - x[0] > 1e-4]
        out += [(u0, u1, z0, z1) for z0, z1 in spans]
    return out


def shell_walls():
    """Same wall set (with holes) as shell_faces, for collision."""
    walls = []
    sw = Wall("SW", P_SW, (XE, YS), (0.0, 1.0))
    sw.holes.append((W1["s"][0] - P_SW[0], W1["s"][1] - P_SW[0], W1["z"][0], W1["z"][1], 0, "window"))
    sw.holes.append((D2["s"][0] - P_SW[0], D2["s"][1] - P_SW[0], -0.5, D2["hole_top"], 0, "door"))
    walls.append(sw)
    walls.append(Wall("SE", (XE, YS), (XE, YN), (-1.0, 0.0)))
    walls.append(Wall("NE", (XE, YN), (XW, YN), (0.0, -1.0)))
    nw = Wall("NW", (XW, YN), P_NW, (1.0, 0.0))
    nw.holes.append((YN - W2["t"][1], YN - W2["t"][0], W2["z"][0], W2["z"][1], 0, "window"))
    nw.holes.append((YN - D3["t"][1], YN - D3["t"][0], -0.5, D3["hole_top"], 0, "door"))
    walls.append(nw)
    chw = Wall("CH", P_NW, P_SW, (-G.CH_OUT[0], -G.CH_OUT[1]))
    chw.holes.append((A_NW - D1["a"][1], A_NW - D1["a"][0], -0.5, D1["z"][1], 0, "door"))
    walls.append(chw)
    return walls


WALL_COL_THICK = 0.10   # collision slab from the visible face outwards (overlaps the vanilla wall collision)


def wall_collision_tris():
    """0.1.4 (audit 05 F1): closed slabs on the visible wall faces, openings W1/W2/D1/D2/D3 left open."""
    tris = []
    for w in shell_walls():
        for u0, u1, z0, z1 in _solid_spans(w):
            c8 = [w.p(u0, z0), w.p(u1, z0), w.p(u1, z0, WALL_COL_THICK), w.p(u0, z0, WALL_COL_THICK),
                  w.p(u0, z1), w.p(u1, z1), w.p(u1, z1, WALL_COL_THICK), w.p(u0, z1, WALL_COL_THICK)]
            tris += _box_tris(c8)
    return tris


def step_collision_tris():
    tris = []
    for x0, x1, y0, y1, z0, z1 in back_door_steps():
        c8 = [(x0, y0, z0 - 0.10), (x1, y0, z0 - 0.10), (x1, y1, z0 - 0.10), (x0, y1, z0 - 0.10),
              (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        tris += _box_tris(c8)
    return tris


# ---------------------------------------------------------------- vertex colours (CPV, Sollumz "Color 1" = Colour0)
# R = natural (sky) ambient, G = artificial ambient (255 = fully self-lit -> the 0.1.3 night glow), B = 0, A = 1.
OPENING_POINTS = [((W1["s"][0] + W1["s"][1]) / 2, YS), ((XW, (W2["t"][0] + W2["t"][1]) / 2)), ch((D1["a"][0] + D1["a"][1]) / 2, CH_IN),
                  ((D2["s"][0] + D2["s"][1]) / 2, YS), (XW, (D3["t"][0] + D3["t"][1]) / 2)]
CPV_G = 0.30


def cpv_shell(v):
    d = min(math.hypot(v[0] - p[0], v[1] - p[1]) for p in OPENING_POINTS)
    r = 0.10 + 0.30 * math.exp(-d / 2.5)
    return (round(r, 3), CPV_G, 0.0, 1.0)


def cpv_glass(v):
    return (0.35, 0.05, 0.0, 1.0)


def cpv_door(v):
    return (0.30, CPV_G, 0.0, 1.0)


if __name__ == "__main__":
    print("A_SW", round(A_SW, 3), "P_SW", P_SW, "A_NW", round(A_NW, 3), "P_NW", P_NW)
    sf = shell_faces()
    print("shell faces", len(sf), "glass", len(glass_faces("W1")) + len(glass_faces("W2")))
    for k, c in portals().items():
        print("portal", k, [tuple(round(x, 3) for x in p) for p in c], "normal", tuple(round(x, 3) for x in portal_normal(c)))
    for e in vanilla_door_entities():
        print("door", e)
    print("D1 hinge_a", D1["hinge_a"], "leaf tops D1/D2/D3", round(D1_LEAF_TOP, 4), round(D2_LEAF_TOP, 4), round(D3_LEAF_TOP, 4))
    print("steps", back_door_steps())
    print("wall collision tris", len(wall_collision_tris()), "step tris", len(step_collision_tris()))
    for did, pts in door_leaf_world_boxes().items():
        xs, ys, zs = zip(*pts)
        print("leaf box", did, (round(min(xs), 3), round(max(xs), 3)), (round(min(ys), 3), round(max(ys), 3)), (round(min(zs), 3), round(max(zs), 3)))
