# Gabagool & Sons — vanilla override builder (pure szio, no bpy).
#
# Builds minimal override copies of the vanilla Long Pig shell so that the existing
# openings become real openings, and NOTHING else changes:
#   sc1_14_build2.ydr                 - remove only painted glass + concrete backing of W1, W2 and the two
#                                       leaves (+stickers, handles, backing) of the entrance D1
#   sc1_14_sc1_emissive_sc1_14b.ydr   - remove only the night "lit window" planes of W1, W2, D1
#   sc1_14_0.ybn (mover)              - split the chamfer wall box so that the D1 doorway is open
#   hi@sc1_14_0.ybn (weapon)          - remove the D1 leaf boxes and 3 invisible boxes inside the shop
#
# Every selection is done by world coordinates of the verified openings (docs/02, docs/03), and the
# exact number of selected triangles / primitives is asserted, so a wrong source file aborts the build.
# Works with native (.ydr/.ybn, PyMateria on the PC) or CodeWalker XML inputs (container dry-run).
import json
import math
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------- building frame (docs/01)
YAW_DEG = -45.94
YAW = math.radians(YAW_DEG)
O2 = np.array([411.655, -1912.045])
FLOOR_Z = 24.45
U = np.array([math.cos(YAW), math.sin(YAW)])    # +s along the SW facade
V = np.array([-math.sin(YAW), math.cos(YAW)])   # +t into the building (NE)
ENT_BUILD2 = np.array([420.745636, -1910.35583, 32.4757])  # sc1_14_build2 + emissive entity, rot identity
# chamfer (entrance wall) frame: a = along chamfer from the W corner, dep = + outwards
CH_A0 = np.array([0.3, -1.6])
CH_DIR = np.array([-0.68266075, 0.73073545])
CH_OUT = np.array([-0.73073545, -0.68266075])

# D1 doorway (between the two door-frame casings) — verified from build2 faces
D1_A = (1.728, 3.605)
D1_Z = (24.447, 26.975)
D1_LEAF_DEP = -0.135  # plane of the vanilla leaves

# 0.1.4 back doors (verified from build2 faces + both collision files, docs/02):
#   D2 = steel service door on the SW facade at the top of the steps (painted leaf t -1.406, landing 24.629)
#   D3 = steel door on the NW facade next to the bins (painted leaf s -3.015, threshold 24.689)
D2 = dict(s=(13.914, 15.133), z=(24.629, 27.078), plane_t=-1.406)
D3 = dict(t=(9.183, 10.402), z=(24.689, 27.078), plane_s=-3.015)


def to_local(world):
    w = np.asarray(world, dtype=float)
    d = w[..., :2] - O2
    return np.stack([d @ U, d @ V, w[..., 2]], axis=-1)


def to_world(s, t, z):
    p = O2 + s * U + t * V
    return np.array([p[0], p[1], z])


def chamfer(local_st):
    p = np.asarray(local_st)[..., :2] - CH_A0
    return p @ CH_DIR, p @ CH_OUT


def chamfer_to_local(a, dep):
    st = CH_A0 + a * CH_DIR + dep * CH_OUT
    return st[0], st[1]


# ---------------------------------------------------------------- drawable helpers
def _shader_tex(shader):
    for p in shader.parameters:
        if p.name == "DiffuseSampler" and isinstance(p.value, str):
            return p.value.lower()
    for p in shader.parameters:
        if isinstance(p.value, str):
            return p.value.lower()
    return ""


def tri_records(drawable, ent_pos):
    """Yield per-triangle info: geometry key, tri index, local coords, local normal, shader, tex."""
    sg = drawable.shader_group
    for lod, models in drawable.models.items():
        for mi, m in enumerate(models):
            for gi, g in enumerate(m.geometries):
                pos = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos
                loc = to_local(pos)
                idx = np.array(g.index_buffer, dtype=np.int64).reshape(-1, 3)
                sh = sg.shaders[g.shader_index]
                tex = _shader_tex(sh)
                for ti, tri in enumerate(idx):
                    W = pos[tri]
                    n = np.cross(W[1] - W[0], W[2] - W[0])
                    nn = np.linalg.norm(n)
                    n = n / nn if nn > 0 else n
                    nl = np.array([n[:2] @ U, n[:2] @ V, n[2]])
                    L = loc[tri]
                    a, dep = chamfer(L)
                    yield dict(key=(int(lod), mi, gi), tri=ti, L=L, a=a, dep=dep, n=nl, area=nn / 2,
                               shader=sh.name, tex=tex)


def _in(v, lo, hi):
    return bool(np.all(v >= lo) and np.all(v <= hi))


# Expected triangle counts — from the container audit of the CodeWalker XML export of the same file.
BUILD2_RULES = {
    # W1 storefront (SW facade): 3 painted glass panes, 4 tris each
    "W1_glass": dict(expect=12, test=lambda r: r["tex"] == "sc1_14_t_page8" and _in(r["L"][:, 1], -1.470, -1.458)
                     and _in(r["L"][:, 0], 1.30, 5.60) and _in(r["L"][:, 2], 25.10, 26.97) and r["n"][1] < -0.99),
    # W1 concrete backing plane 8 cm behind the glass (faces the street)
    "W1_backing": dict(expect=18, test=lambda r: r["tex"] == "im_wall_concrete32" and _in(r["L"][:, 1], -1.392, -1.380)
                       and _in(r["L"][:, 0], 1.25, 5.66) and _in(r["L"][:, 2], 25.04, 27.03) and r["n"][1] < -0.99),
    # W2 window (NW facade): 2 panes
    "W2_glass": dict(expect=8, test=lambda r: r["tex"] == "sc1_14_t_page8" and _in(r["L"][:, 0], -3.084, -3.072)
                     and _in(r["L"][:, 1], 3.50, 6.35) and _in(r["L"][:, 2], 25.10, 26.97) and r["n"][0] < -0.99),
    "W2_backing": dict(expect=12, test=lambda r: r["tex"] == "im_wall_concrete32" and _in(r["L"][:, 0], -3.038, -3.026)
                       and _in(r["L"][:, 1], 3.44, 6.40) and _in(r["L"][:, 2], 25.04, 27.03) and r["n"][0] < -0.99),
    # D1 entrance: everything that belongs to the two leaves (glass, stiles, rails, kick plates, handles, stickers)
    "D1_leaves": dict(expect=88, test=lambda r: r["tex"] in ("sc1_14_t_page8", "im_sc1_12_signs_01b")
                      and _in(r["a"], 1.725, 3.610) and _in(r["dep"], -0.160, -0.085) and _in(r["L"][:, 2], 24.44, 26.98)),
    # D1 concrete backing plane behind the leaves
    "D1_backing": dict(expect=6, test=lambda r: r["tex"] == "im_wall_concrete32" and _in(r["a"], 1.69, 3.63)
                       and _in(r["dep"], -0.215, -0.175) and _in(r["L"][:, 2], 24.44, 27.03) and r["n"][0] * CH_OUT[0] + r["n"][1] * CH_OUT[1] > 0.99),
    # 0.1.4: third-party posters stuck on the outside of the glass (9 on W1, 6 on W2), 2 tris each
    "W1_stickers": dict(expect=18, test=lambda r: r["tex"] == "im_sc1_12_signs_01b" and _in(r["L"][:, 1], -1.510, -1.478)
                        and _in(r["L"][:, 0], 1.30, 5.60) and _in(r["L"][:, 2], 25.10, 26.97) and r["n"][1] < -0.99),
    "W2_stickers": dict(expect=12, test=lambda r: r["tex"] == "im_sc1_12_signs_01b" and _in(r["L"][:, 0], -3.120, -3.100)
                        and _in(r["L"][:, 1], 3.50, 6.35) and _in(r["L"][:, 2], 25.10, 26.97) and r["n"][0] < -0.99),
    # 0.1.4: back doors — painted steel leaf + concrete plate right behind it (frames, casings, steps untouched)
    "D2_leaf": dict(expect=6, test=lambda r: r["tex"] == "sc1_14_t_page8" and _in(r["L"][:, 1], -1.412, -1.400)
                    and _in(r["L"][:, 0], 13.90, 15.14) and _in(r["L"][:, 2], 24.60, 27.09) and r["n"][1] < -0.99),
    "D2_backing": dict(expect=4, test=lambda r: r["tex"] == "im_wall_concrete32" and _in(r["L"][:, 1], -1.390, -1.374)
                       and _in(r["L"][:, 0], 13.86, 15.19) and _in(r["L"][:, 2], 25.26, 27.14) and r["n"][1] < -0.99),
    "D3_leaf": dict(expect=6, test=lambda r: r["tex"] == "sc1_14_t_page8" and _in(r["L"][:, 0], -3.020, -3.010)
                    and _in(r["L"][:, 1], 9.17, 10.41) and _in(r["L"][:, 2], 24.60, 27.09) and r["n"][0] < -0.99),
    "D3_backing": dict(expect=6, test=lambda r: r["tex"] == "im_wall_concrete32" and _in(r["L"][:, 0], -2.995, -2.985)
                       and _in(r["L"][:, 1], 9.14, 10.45) and _in(r["L"][:, 2], 24.47, 27.14) and r["n"][0] < -0.99),
}
BUILD2_REMOVED_TRIS = sum(r["expect"] for r in BUILD2_RULES.values())   # 144 (0.1.x) + 30 stickers + 22 back doors = 196

EMISSIVE_RULES = {
    "W1_night": dict(expect=12, test=lambda r: _in(r["L"][:, 1], -1.476, -1.466) and _in(r["L"][:, 0], 1.30, 5.60)),
    "W2_night": dict(expect=8, test=lambda r: _in(r["L"][:, 0], -3.098, -3.090) and _in(r["L"][:, 1], 3.50, 6.35)),
    "D1_night": dict(expect=8, test=lambda r: _in(r["a"], 1.75, 3.58) and _in(r["dep"], -0.146, -0.136)),
}


def select(drawable, ent_pos, rules):
    sel = {k: [] for k in rules}
    for r in tri_records(drawable, ent_pos):
        hits = [k for k, rule in rules.items() if rule["test"](r)]
        if len(hits) > 1:
            raise RuntimeError(f"triangle {r['key']}/{r['tri']} matched several rules: {hits}")
        if hits:
            sel[hits[0]].append(r)
    report = {}
    for k, rule in rules.items():
        n = len(sel[k])
        report[k] = {"expected": rule["expect"], "found": n,
                     "geometries": sorted({f"g{r['key'][2]}" for r in sel[k]}),
                     "area_m2": round(float(sum(r["area"] for r in sel[k])), 3)}
        if n != rule["expect"]:
            raise RuntimeError(f"{k}: expected {rule['expect']} triangles, found {n} — source file differs, abort")
    return sel, report


def remove_triangles(drawable, sel):
    """Remove the selected triangles from the index buffers. Vertex buffers stay untouched."""
    kill = {}
    for recs in sel.values():
        for r in recs:
            kill.setdefault(r["key"], set()).add(r["tri"])
    per_geom = {}
    for (lod, mi, gi), tris in kill.items():
        lod_key = [k for k in drawable.models if int(k) == lod][0]
        g = drawable.models[lod_key][mi].geometries[gi]
        ib = np.asarray(g.index_buffer)
        n_before = len(ib) // 3
        keep = np.ones(n_before, dtype=bool)
        keep[sorted(tris)] = False
        g.index_buffer = ib.reshape(-1, 3)[keep].reshape(-1).astype(ib.dtype)
        per_geom[f"g{gi}"] = {"tris_before": int(n_before), "tris_after": int(keep.sum()), "removed": int(n_before - keep.sum())}
    return per_geom


def drop_empty_geometries(drawable):
    dropped = []
    for lod, models in drawable.models.items():
        for m in models:
            new = []
            for gi, g in enumerate(m.geometries):
                if len(g.index_buffer) == 0:
                    dropped.append(gi)
                else:
                    new.append(g)
            m.geometries = new
    return dropped


def drawable_stats(drawable):
    out = {"shaders": len(drawable.shader_group.shaders) if drawable.shader_group else 0,
           "embedded_textures": len(drawable.shader_group.embedded_textures) if drawable.shader_group else 0,
           "geometries": []}
    for lod, models in drawable.models.items():
        for mi, m in enumerate(models):
            for gi, g in enumerate(m.geometries):
                out["geometries"].append({"lod": int(lod), "model": mi, "geom": gi, "shader": g.shader_index,
                                          "verts": int(len(g.vertex_buffer)), "tris": int(len(g.index_buffer) // 3),
                                          "layout": list(g.vertex_buffer.dtype.names)})
    return out


# ---------------------------------------------------------------- bound helpers
def _prim_corners(prim, verts):
    P = np.array([[float(x) for x in verts[i].co] for i in prim.vertices])
    if prim.primitive_type.name == "BOX":
        v0, v1, v2, v3 = P
        P = np.vstack([P, (v1 + v2 + v3 - v0) / 2, (v0 + v2 + v3 - v1) / 2, (v0 + v1 + v3 - v2) / 2, (v0 + v1 + v2 - v3) / 2])
    return P


def _box_frame(prim, verts):
    """Exact frame of a BOX primitive: centre, 3 unit axes, 3 half extents."""
    P = np.array([[float(x) for x in verts[i].co] for i in prim.vertices])
    v0, v1, v2, v3 = P
    c = P.mean(0)
    a1 = ((v2 + v3) - (v0 + v1)) * 0.5
    e = [a1, (v2 - a1) - v0, (v3 - a1) - v0]
    axes = [x / np.linalg.norm(x) for x in e]
    half = [np.linalg.norm(x) / 2 for x in e]
    return c, axes, half


def _box_vertices(center, axes, half):
    """4 corners in the GTA/Sollumz convention (same sign-parity corners, like bound_box[0,5,2,7])."""
    A, B, C = (np.asarray(axes[i]) * half[i] for i in range(3))
    signs = [(-1, -1, -1), (1, -1, 1), (-1, 1, 1), (1, 1, -1)]
    return [center + sa * A + sb * B + sc * C for sa, sb, sc in signs]


def interior_depth(local_pts):
    """Penetration depth of points into the shop interior volume (negative = outside)."""
    L = np.asarray(local_pts)
    s, t, z = L[:, 0], L[:, 1], L[:, 2]
    _, dep = chamfer(L)
    return np.minimum.reduce([s + 2.90, t + 1.23, 11.42 - t, 16.15 - s, -0.46 - dep, z - FLOOR_Z, 30.17 - z])


def edit_mover_bound(bound, BoundVertex, BoundPrimitive, BoundPrimitiveType):
    """sc1_14_0.ybn: split the single chamfer-wall box (METAL_CORRUGATED_IRON, a 0.03..5.20, z 24.44..32.43)
    into 3 boxes leaving the D1 doorway (a 1.728..3.605, z <= 26.975) open."""
    hits = []
    for ci, c in enumerate(bound.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        for pi, p in enumerate(c.geometry_primitives):
            if p.primitive_type.name != "BOX" or p.material.material_index != 63:
                continue
            L = to_local(_prim_corners(p, c.geometry_vertices))
            a, dep = chamfer(L)
            if a.min() < 0.2 and a.max() > 5.0 and dep.min() > -0.5 and dep.max() < 0.2 and L[:, 2].min() < 24.6 and L[:, 2].max() > 32.0:
                hits.append((ci, pi))
    if len(hits) != 1:
        raise RuntimeError(f"mover chamfer box: expected exactly 1 match, found {hits}")
    ci, pi = hits[0]
    child = bound.children[ci]
    old = child.geometry_primitives[pi]
    c, axes, half = _box_frame(old, child.geometry_vertices)
    # identify long / vertical / thickness axes
    order = sorted(range(3), key=lambda i: half[i])
    i_thick, i_mid, i_long = order
    i_z = max(range(3), key=lambda i: abs(axes[i][2]))
    i_long = [i for i in range(3) if i not in (i_thick, i_z)][0]
    ax_long, ax_z, ax_th = axes[i_long], axes[i_z], axes[i_thick]
    if ax_z[2] < 0:
        ax_z = -ax_z
    h_long, h_z, h_th = half[i_long], half[i_z], half[i_thick]

    def param_long(a):
        s, t = chamfer_to_local(a, D1_LEAF_DEP)
        w = to_world(s, t, 0)
        return float((w[:2] - c[:2]) @ ax_long[:2])

    pa, pb = sorted([param_long(D1_A[0]), param_long(D1_A[1])])
    z0, z1 = c[2] - h_z, c[2] + h_z
    zt = D1_Z[1]
    pieces = [  # (long_min, long_max, z_min, z_max)
        (-h_long, pa, z0, z1),
        (pb, h_long, z0, z1),
        (pa, pb, zt, z1),
    ]
    new_prims = []
    for lmin, lmax, zmin, zmax in pieces:
        center = c + ax_long * ((lmin + lmax) / 2) + ax_z * ((zmin + zmax) / 2 - c[2])
        hv = [0, 0, 0]
        ax = [None, None, None]
        ax[0], hv[0] = ax_long, (lmax - lmin) / 2
        ax[1], hv[1] = ax_z, (zmax - zmin) / 2
        ax[2], hv[2] = ax_th, h_th
        vids = []
        for v in _box_vertices(center, ax, hv):
            from szio.types import Vector as _SzVec
            child.geometry_vertices.append(BoundVertex(_SzVec(tuple(float(x) for x in v)), child.geometry_vertices[0].color))
            vids.append(len(child.geometry_vertices) - 1)
        new_prims.append(BoundPrimitive(primitive_type=BoundPrimitiveType.BOX, material=old.material,
                                        material_color=old.material_color, vertices=tuple(vids), radius=None))
    child.geometry_primitives[pi] = new_prims[0]
    child.geometry_primitives.extend(new_prims[1:])
    back = remove_back_door_boxes(bound, material_index=55)          # 0.1.4: D2 + D3 steel leaf boxes
    return {"child": ci, "replaced_prim": pi, "old_box": {"center": c.round(3).tolist(), "half": [round(h, 3) for h in half]},
            "doorway_long_params": [round(pa, 3), round(pb, 3)], "new_boxes": len(new_prims), "back_door_boxes_removed": back}


def _back_door_of(L):
    """Which back doorway a thin leaf box belongs to (local corners), or None."""
    s, t, z = L[:, 0], L[:, 1], L[:, 2]
    if _in(s, 13.86, 15.19) and _in(t, -1.45, -1.38) and _in(z, 24.60, 27.14):
        return "D2"
    if _in(s, -3.05, -2.99) and _in(t, 9.13, 10.46) and _in(z, 24.60, 27.14):
        return "D3"
    return None


def remove_back_door_boxes(bound, material_index):
    """Remove the single thin 'door leaf' box of D2 and of D3 (mover: METAL mat 55, weapon: mat 56).
    The wall boxes left and right of each doorway are separate primitives and stay."""
    removed = []
    for ci, c in enumerate(bound.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        keep = []
        for pi, p in enumerate(c.geometry_primitives):
            if p.primitive_type.name == "BOX" and p.material.material_index == material_index:
                door = _back_door_of(to_local(_prim_corners(p, c.geometry_vertices)))
                if door:
                    removed.append({"door": door, "child": ci, "prim": pi, "mat": material_index})
                    continue
            keep.append(p)
        c.geometry_primitives = keep
    if sorted(r["door"] for r in removed) != ["D2", "D3"]:
        raise RuntimeError(f"back door leaf boxes (mat {material_index}): expected D2 + D3, found {removed}")
    return removed


def back_doors_clear_check(bound, kind):
    """Sample both back doorways (in front of, in and behind the leaf plane) at ped heights."""
    pts = {"D2": [], "D3": []}
    for s in np.linspace(D2["s"][0] + 0.15, D2["s"][1] - 0.15, 4):
        for t in (-1.50, D2["plane_t"], -1.30):
            for z in (24.95, 25.6, 26.5):
                pts["D2"].append(to_world(s, t, z))
    for t in np.linspace(D3["t"][0] + 0.15, D3["t"][1] - 0.15, 4):
        for s in (-3.10, D3["plane_s"], -2.85):
            for z in (25.0, 25.7, 26.5):
                pts["D3"].append(to_world(s, t, z))
    out = {"kind": kind}
    for door, P in pts.items():
        P = np.array(P)
        blocking = []
        for ci, c in enumerate(bound.children):
            if c is None or not hasattr(c, "geometry_primitives"):
                continue
            for pi, p in enumerate(c.geometry_primitives):
                if p.primitive_type.name != "BOX":
                    continue
                cc, axes, half = _box_frame(p, c.geometry_vertices)
                d = P - cc
                inside = np.all([np.abs(d @ axes[i]) <= half[i] + 1e-3 for i in range(3)], axis=0)
                if inside.any():
                    blocking.append({"child": ci, "prim": pi, "mat": p.material.material_index, "points": int(inside.sum())})
        out[door] = {"sample_points": int(len(P)), "blocking_boxes": blocking}
    return out


def _trim_box_to_wall(prim, verts, BoundVertex, wall):
    """Cut a vanilla weapon box that reaches into the shop back to the wall slab only.
    wall = ("t", 11.42) keeps the part with t >= 11.42 (NE wall), ("s", 16.15) keeps s >= 16.15 (SE wall)."""
    from szio.types import Vector as _SzVec
    c, axes, half = _box_frame(prim, verts)
    key, limit = wall
    k = 1 if key == "t" else 0
    # local direction of each axis
    loc_axes = [np.array([ax[:2] @ U, ax[:2] @ V, ax[2]]) for ax in axes]
    i = max(range(3), key=lambda j: abs(loc_axes[j][k]))
    sign = 1.0 if loc_axes[i][k] > 0 else -1.0
    cl = to_local(c[None])[0]
    lo, hi = cl[k] - half[i], cl[k] + half[i]          # extent along the wall normal (local)
    new_lo = max(lo, limit)
    if new_lo >= hi - 1e-3:
        raise RuntimeError("trim would delete the box")
    new_half = (hi - new_lo) / 2
    shift = (new_lo + hi) / 2 - cl[k]                 # move centre along local axis k
    c_new = c + axes[i] * (shift * sign)
    h_new = list(half)
    h_new[i] = new_half
    vids = []
    for v in _box_vertices(c_new, axes, h_new):
        verts.append(BoundVertex(_SzVec(tuple(float(x) for x in v)), verts[0].color))
        vids.append(len(verts) - 1)
    prim.vertices = tuple(vids)
    return {"axis_local": key, "from": [round(float(lo), 3), round(float(hi), 3)], "to": [round(float(new_lo), 3), round(float(hi), 3)]}


def edit_weapon_bound(bound, BoundVertex):
    """hi@sc1_14_0.ybn: remove the 8 D1 leaf boxes; the 3 vanilla wall boxes that reach 0.7-3 m into the
    empty shop volume are trimmed back to the wall slab (bullets still stop at the walls)."""
    removed = {"D1_leaves": [], "trimmed_wall_boxes": [], "back_door_leaves": []}
    for ci, c in enumerate(bound.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        keep = []
        for pi, p in enumerate(c.geometry_primitives):
            if p.primitive_type.name == "BOX":
                L = to_local(_prim_corners(p, c.geometry_vertices))
                a, dep = chamfer(L)
                door = _back_door_of(L) if p.material.material_index == 56 else None
                if door:                                                    # 0.1.4: D2 / D3 steel leaves
                    removed["back_door_leaves"].append({"door": door, "child": ci, "prim": pi, "mat": 56})
                    continue
                if _in(a, 1.70, 3.64) and _in(dep, -0.20, -0.06) and _in(L[:, 2], 24.40, 27.00):
                    removed["D1_leaves"].append({"child": ci, "prim": pi, "mat": p.material.material_index})
                    continue
                if p.material.material_index == 63 and interior_depth(L).max() > 0.5:
                    wall = ("t", 11.42) if L[:, 1].max() > 11.6 else ("s", 16.15) if L[:, 0].max() > 16.3 else None
                    if wall is None:
                        raise RuntimeError(f"interior box {pi} not attached to a known wall")
                    info = _trim_box_to_wall(p, c.geometry_vertices, BoundVertex, wall)
                    removed["trimmed_wall_boxes"].append({"child": ci, "prim": pi, "mat": p.material.material_index, **info})
            keep.append(p)
        c.geometry_primitives = keep
    if sorted(r["door"] for r in removed["back_door_leaves"]) != ["D2", "D3"]:
        raise RuntimeError(f"weapon bound: back door leaves expected D2 + D3, found {removed['back_door_leaves']}")
    if len(removed["D1_leaves"]) != 8 or len(removed["trimmed_wall_boxes"]) != 3:
        raise RuntimeError(f"weapon bound: unexpected match counts {[(k, len(v)) for k, v in removed.items()]}")
    left = [pi for ci, c in enumerate(bound.children) if c is not None and hasattr(c, "geometry_primitives")
            for pi, p in enumerate(c.geometry_primitives) if p.primitive_type.name == "BOX"
            and interior_depth(to_local(_prim_corners(p, c.geometry_vertices))).max() > 0.05 and p.material.material_index == 63]
    if left:
        raise RuntimeError(f"weapon bound: boxes still inside the shop: {left}")
    return removed


def bound_stats(bound):
    out = []
    for ci, c in enumerate(bound.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            out.append(None)
            continue
        from collections import Counter
        cnt = Counter(p.primitive_type.name for p in c.geometry_primitives)
        out.append({"child": ci, "type_flags": int(c.composite_collision_type_flags), "prims": len(c.geometry_primitives),
                    "by_type": dict(cnt), "verts": len(c.geometry_vertices)})
    return out


def doorway_clear_check(bound, kind):
    """Sample points in the D1 doorway (ped capsule height) and report primitives that still contain them."""
    pts = []
    for a in np.linspace(D1_A[0] + 0.15, D1_A[1] - 0.15, 5):
        for z in (24.7, 25.5, 26.4):
            for dep in (0.05, -0.135, -0.30, -0.45):
                s, t = chamfer_to_local(a, dep)
                pts.append(to_world(s, t, z))
    pts = np.array(pts)
    blocking = []
    for ci, c in enumerate(bound.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        for pi, p in enumerate(c.geometry_primitives):
            if p.primitive_type.name != "BOX":
                continue
            cc, axes, half = _box_frame(p, c.geometry_vertices)
            d = pts - cc
            inside = np.all([np.abs(d @ axes[i]) <= half[i] + 1e-3 for i in range(3)], axis=0)
            if inside.any():
                blocking.append({"child": ci, "prim": pi, "mat": p.material.material_index, "points": int(inside.sum())})
    return {"kind": kind, "sample_points": int(len(pts)), "blocking_boxes": blocking}


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


def verify_mover_split(orig_bound, new_bound, info):
    """Grid-sample the original chamfer box: every point outside the doorway must still be solid in the new
    bound, every point inside the doorway must be free."""
    ci, pi = info["child"], info["replaced_prim"]
    oc = orig_bound.children[ci]
    c, axes, half = _box_frame(oc.geometry_primitives[pi], oc.geometry_vertices)
    g = np.stack(np.meshgrid(*[np.linspace(-h * 0.98, h * 0.98, n) for h, n in zip(half, (7, 25, 25))], indexing="ij"), -1).reshape(-1, 3)
    pts = c + g[:, 0:1] * axes[0] + g[:, 1:2] * axes[1] + g[:, 2:3] * axes[2]
    L = to_local(pts)
    a, dep = chamfer(L)
    in_door = (a > D1_A[0] + 0.01) & (a < D1_A[1] - 0.01) & (L[:, 2] < D1_Z[1] - 0.01)
    near_edge = (np.abs(a - D1_A[0]) < 0.02) | (np.abs(a - D1_A[1]) < 0.02) | (np.abs(L[:, 2] - D1_Z[1]) < 0.02)
    solid = np.zeros(len(pts), dtype=bool)
    nc = new_bound.children[ci]
    for p in nc.geometry_primitives:
        if p.primitive_type.name != "BOX" or p.material.material_index != 63:
            continue
        cc, ax, hf = _box_frame(p, nc.geometry_vertices)
        d = pts - cc
        solid |= np.all([np.abs(d @ ax[i]) <= hf[i] + 1e-3 for i in range(3)], axis=0)
    ok_wall = solid[~in_door & ~near_edge].all()
    ok_door = (~solid[in_door & ~near_edge]).all()
    return {"samples": int(len(pts)), "wall_samples": int((~in_door & ~near_edge).sum()), "door_samples": int((in_door & ~near_edge).sum()),
            "wall_still_solid": bool(ok_wall), "doorway_free": bool(ok_door)}


def texture_fingerprints(drawable):
    """name -> (width, height, dds bytes, md5 of the pixel payload) for every embedded texture."""
    import hashlib
    out = {}
    sg = drawable.shader_group
    if sg is None:
        return out
    for name, tex in sg.embedded_textures.items():
        data = None
        try:
            data = tex.data.read_bytes() if tex.data is not None else None
        except Exception:
            data = None
        if data is None:
            out[name] = (tex.width, tex.height, 0, None)
            continue
        hdr = 148 if data[84:88] == b"DX10" else 128
        out[name] = (tex.width, tex.height, len(data), hashlib.md5(data[hdr:]).hexdigest())
    return out


def compare_textures(before, after):
    diff = []
    for name, fp in before.items():
        fa = after.get(name)
        if fa is None:
            diff.append((name, "missing"))
        elif fp[3] is not None and fp[3] != fa[3]:
            diff.append((name, f"payload differs {fp[2]}->{fa[2]}"))
        elif fp[:2] != fa[:2]:
            diff.append((name, f"size {fp[:2]}->{fa[:2]}"))
    extra = [n for n in after if n not in before]
    return {"compared": len(before), "with_data": sum(1 for f in before.values() if f[3]), "differences": diff, "extra": extra}


# ================================================================ 0.1.6: ground decals under the shop + block occluder
# sc1_14_grnd_02.ydr (entity in sc1_14_strm_0 and its hei_/lr_ copies, identity rotation): a decal patch and the edges of the
# sidewalk mesh lie up to 0.20 m above the MLO floor inside the shop (dirty smudge near the NE wall). Everything of this
# drawable inside the interior floor polygon is cut away; outside the polygon the mesh stays identical (triangles crossing
# the wall line are split, the outside part keeps its exact surface and interpolated vertex attributes).
ENT_GRND02 = np.array([441.1499938964844, -1892.41796875, 24.780000686645508])


def _poly_halfplanes(poly):
    """Convex CCW polygon (local s,t) -> list of (point, inward normal)."""
    P = np.asarray(poly, dtype=float)
    out = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        d = b - a
        out.append((a, np.array([-d[1], d[0]]) / np.linalg.norm(d)))
    return out


def _clip_convex(pts, a, n, keep_inside):
    """Sutherland-Hodgman against one half-plane; keep_inside=True keeps (p-a).n >= 0."""
    out = []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        dp, dq = float((p - a) @ n), float((q - a) @ n)
        if not keep_inside:
            dp, dq = -dp, -dq
        if dp >= 0:
            out.append(p)
        if (dp >= 0) != (dq >= 0):
            out.append(p + (q - p) * (dp / (dp - dq)))
    return out


def _tri_minus_poly(tri2, hps):
    """Triangle (3x2) minus convex polygon -> list of convex pieces (lists of 2D points)."""
    pieces = []
    for i, (a, n) in enumerate(hps):
        cur = [np.array(p, dtype=float) for p in tri2]
        for j in range(i):
            cur = _clip_convex(cur, hps[j][0], hps[j][1], True)
            if len(cur) < 3:
                break
        if len(cur) >= 3:
            cur = _clip_convex(cur, a, n, False)
        if len(cur) >= 3:
            area = 0.5 * abs(sum(cur[k][0] * cur[(k + 1) % len(cur)][1] - cur[(k + 1) % len(cur)][0] * cur[k][1] for k in range(len(cur))))
            if area > 1e-7:
                pieces.append(cur)
    return pieces


def _inside_poly(P2, hps, eps=0.0):
    ok = np.ones(len(P2), dtype=bool)
    for a, n in hps:
        ok &= ((P2 - a) @ n) > eps
    return ok


def clip_out_polygon(drawable, ent_pos, poly):
    """Remove the part of every triangle of `drawable` that lies inside the convex local polygon `poly`."""
    hps = _poly_halfplanes(poly)
    stats = {}
    for lod, models in drawable.models.items():
        for mi, m in enumerate(models):
            for gi, g in enumerate(m.geometries):
                vb = g.vertex_buffer
                pos = np.array(vb["Position"], dtype=float).reshape(-1, 3) + ent_pos
                L = to_local(pos)
                P2 = L[:, :2]
                inside_v = _inside_poly(P2, hps, 1e-6)
                idx = np.asarray(g.index_buffer, dtype=np.int64).reshape(-1, 3)
                lo, hi = np.min(np.asarray(poly), 0), np.max(np.asarray(poly), 0)
                keep, new_tris, new_rows = [], [], []
                n_cut = n_split = 0
                base = len(vb)
                for tri in idx:
                    T = P2[tri]
                    if (T[:, 0].max() < lo[0] or T[:, 0].min() > hi[0] or T[:, 1].max() < lo[1] or T[:, 1].min() > hi[1]):
                        keep.append(tri); continue
                    v0, v1 = T[1] - T[0], T[2] - T[0]
                    den = v0[0] * v1[1] - v1[0] * v0[1]
                    if abs(den) < 1e-9:                                   # vertical triangle: decide by centroid
                        if _inside_poly(T.mean(0)[None], hps)[0]:
                            n_cut += 1
                        else:
                            keep.append(tri)
                        continue
                    if inside_v[tri].all():
                        n_cut += 1; continue
                    pieces = _tri_minus_poly(T, hps)
                    full = 0.5 * abs(den)
                    parea = sum(0.5 * abs(sum(p[k][0] * p[(k + 1) % len(p)][1] - p[(k + 1) % len(p)][0] * p[k][1] for k in range(len(p)))) for p in pieces)
                    if abs(parea - full) < 1e-7:                         # untouched
                        keep.append(tri); continue
                    n_split += 1
                    for piece in pieces:
                        ids = []
                        for q in piece:
                            w = q - T[0]
                            l1 = (w[0] * v1[1] - v1[0] * w[1]) / den
                            l2 = (v0[0] * w[1] - w[0] * v0[1]) / den
                            bary = np.array([1.0 - l1 - l2, l1, l2])
                            row = np.zeros(1, dtype=vb.dtype)
                            for f in vb.dtype.names:
                                vals = np.asarray(vb[f][tri], dtype=float)
                                bl = np.tensordot(bary, vals, axes=(0, 0))
                                if np.issubdtype(vb.dtype[f].base, np.integer):
                                    bl = np.clip(np.round(bl), np.iinfo(vb.dtype[f].base).min, np.iinfo(vb.dtype[f].base).max)
                                row[f] = bl
                            new_rows.append(row)
                            ids.append(base + len(new_rows) - 1)
                        for k in range(1, len(ids) - 1):
                            t3 = [ids[0], ids[k], ids[k + 1]]
                            # keep the original winding (2D orientation)
                            A, B, C = piece[0], piece[k], piece[k + 1]
                            if np.sign((B[0] - A[0]) * (C[1] - A[1]) - (C[0] - A[0]) * (B[1] - A[1])) != np.sign(den):
                                t3 = [t3[0], t3[2], t3[1]]
                            new_tris.append(t3)
                if n_cut or n_split:
                    if new_rows:
                        g.vertex_buffer = np.concatenate([vb] + new_rows)
                    allt = np.array(keep + new_tris, dtype=np.int64).reshape(-1)
                    if len(g.vertex_buffer) > 65535:
                        raise RuntimeError("vertex buffer too large after clipping")
                    g.index_buffer = allt.astype(np.asarray(g.index_buffer).dtype)
                    stats[f"g{gi}"] = {"tris_before": int(len(idx)), "removed_inside": n_cut, "split": n_split,
                                       "new_tris": len(new_tris), "new_verts": len(new_rows), "tris_after": int(len(allt) // 3)}
    return stats


def surface_above_floor(drawable, ent_pos, poly, z_floor_local, step=0.05):
    """Samples (step grid) inside `poly` where any triangle of the drawable is above z_floor_local (local, from FLOOR_Z)."""
    hps = _poly_halfplanes(poly)
    P = np.asarray(poly)
    xs = np.arange(P[:, 0].min(), P[:, 0].max(), step) + step / 2
    ys = np.arange(P[:, 1].min(), P[:, 1].max(), step) + step / 2
    X, Y = np.meshgrid(xs, ys)
    S = np.stack([X.ravel(), Y.ravel()], 1)
    S = S[_inside_poly(S, hps, 0.005)]
    hit = np.zeros(len(S), dtype=bool)
    for lod, models in drawable.models.items():
        for m in models:
            for g in m.geometries:
                L = to_local(np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos)
                for a, b, c in np.asarray(g.index_buffer, dtype=np.int64).reshape(-1, 3):
                    A, B, C = L[a], L[b], L[c]
                    v0, v1 = B[:2] - A[:2], C[:2] - A[:2]
                    den = v0[0] * v1[1] - v1[0] * v0[1]
                    if abs(den) < 1e-9:
                        continue
                    lo = np.minimum(np.minimum(A[:2], B[:2]), C[:2]); hi = np.maximum(np.maximum(A[:2], B[:2]), C[:2])
                    msk = (S[:, 0] >= lo[0]) & (S[:, 0] <= hi[0]) & (S[:, 1] >= lo[1]) & (S[:, 1] <= hi[1])
                    if not msk.any():
                        continue
                    Q = S[msk] - A[:2]
                    l1 = (Q[:, 0] * v1[1] - v1[0] * Q[:, 1]) / den
                    l2 = (v0[0] * Q[:, 1] - Q[:, 0] * v0[1]) / den
                    l0 = 1 - l1 - l2
                    z = l0 * A[2] + l1 * B[2] + l2 * C[2] - FLOOR_Z
                    up = (l0 >= 0) & (l1 >= 0) & (l2 >= 0) & (z > z_floor_local)
                    hit[np.where(msk)[0][up]] = True
    return int(hit.sum()), int(len(S))


# sc1_occl_01.ymap / hei_sc1_occl_01.ymap / lr_sc1_occl_01.ymap: one model occluder of the block contains a closed prism
# exactly around the shop (10 vertices, 13 triangles, z -8.6..+5.7 local). Seen from the street through W1 -> room -> W2 it
# culls everything behind the shop. Its three street faces (SW facade with W1/D2, entrance chamfer with D1, NW facade with
# W2/D3) are removed; the NE and SE faces (solid party walls) and the roof stay.
SHOP_BOX_REGION = ((-3.6, 16.8), (-1.9, 12.1))


def _is_street_face_vertex(L):
    s, t = L[..., 0], L[..., 1]
    return (np.abs(t + 1.30) < 0.12) | ((s > -2.97) & (s < -2.75))


def cut_shop_occluder(mapdata):
    found = []
    for mi, mo in enumerate(mapdata.model_occluders):
        V = np.asarray(mo.vertices, dtype=float).reshape(-1, 3)
        I = np.asarray(mo.indices).reshape(-1, 3).astype(np.int64)
        L = to_local(V)
        (s0, s1), (t0, t1) = SHOP_BOX_REGION
        near = (L[:, 0] > s0) & (L[:, 0] < s1) & (L[:, 1] > t0) & (L[:, 1] < t1)
        box = [ti for ti, tri in enumerate(I) if near[tri].all()]
        if not box:
            continue
        kill = []
        for ti in box:
            tri = I[ti]
            zs = L[tri, 2]
            if np.ptp(zs) < 0.01:                     # roof
                continue
            if _is_street_face_vertex(L[tri]).all():
                kill.append(ti)
        keep = np.ones(len(I), dtype=bool)
        keep[kill] = False
        mo.indices = I[keep].astype(np.uint8)
        found.append({"model": mi, "box_tris": box, "removed": kill, "tris_before": int(len(I)), "tris_after": int(keep.sum())})
    return found


# ================================================================== 0.3.0 STREET: taco kiosk + its signs removed
# revision; after the first in-game test
# (raised plinth with a cap): "сделай срез и сделай одинаково всё как на той парковке" -> the plinth goes too, the hole in
# the ground is closed FLUSH with the lot (own triangles with the parking tarmac material in sc1_14_grnd_02, own boxes
# in the static collision). The kiosk, the TACOS sign and the small sign poles are part of sc1_14_build2 (+ 28 emissive
# tris + boxes / triangles of the static collision). Counts from the CodeWalker XML audit (docs/_raw/kiosk_scan_v030.json).
STREET_ON = False
KIOSK_BOX = (np.array([384.5, -1946.0]), np.array([407.5, -1922.5]))          # world XY; 3 m clear gap to the shop
KIOSK_ZKEEP = 24.0
KIOSK_PAD = [(393.82, -1931.04), (395.03, -1933.80), (398.23, -1936.61), (400.61, -1936.53), (403.01, -1933.80),
             (403.98, -1930.63), (401.87, -1928.20), (399.02, -1925.70), (394.59, -1927.50)]   # plinth kerb outline, CCW
KIOSK_PAD_GZ = [23.623, 23.618, 23.573, 23.500, 23.579, 23.703, 23.795, 23.802, 23.773]         # lot level at each corner
KIOSK_PLINTH_SCALE = 1.25                         # plinth geometry / collision = inside the outline scaled by this
# 0.3.0-d (revision, "всё мигает"): the hole in the ground IS the outline (raster audit of all
# ground drawables, docs/_raw/site_top.npy). The fill now lies 3 cm UNDER the lot level (no z-fight with the lot, it only
# shows through the hole), uses the lot ground of the long NW edge (sc1_27 ground, not the 4-layer tarmac whose blend
# colours gave grey cracked concrete) and the collision is the same fan as triangles (was 0.5 m stepped boxes).
KIOSK_FILL_SCALE = 1.06
KIOSK_FILL_LIFT = -0.03
KIOSK_FILL_TEX = "sc1_27_rsn_ns_ground_0001"
KIOSK_EXPECT = {"build2": 2078 + 134, "emissive": 28}
# 0.3.0-e: exact hole in the ground (visibility polygon over ALL ground drawables, docs/_raw/kiosk_hole_poly.json): the
# fill is this polygon with its corners snapped to the existing ground vertices -> flush, no overlap, no shadow line.
KIOSK_HOLE_C = (398.45, -1930.95)
KIOSK_HOLE = [(402.47, -1929.82, 23.76), (400.34, -1927.96, 23.80), (399.30, -1927.05, 23.79), (396.81, -1929.73, 23.77),
              (394.89, -1931.82, 23.66), (394.33, -1932.43, 23.62), (398.26, -1936.36, 23.56), (398.89, -1935.74, 23.61),
              (401.65, -1933.98, 23.72), (402.32, -1933.23, 23.71), (404.10, -1931.25, 23.70)]     # CW from above
KIOSK_SKIRT = (1.04, -0.08)                       # hidden strip under the lot edge: scale, drop


def _hole_ccw():
    H = np.array(KIOSK_HOLE, dtype=float)
    x, y = H[:, 0], H[:, 1]
    if np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)) < 0:
        H = H[::-1]
    return H


def _seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(float(ab @ ab), 1e-12), 0.0, 1.0)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def _in_poly(P, Q):
    P = np.asarray(P, float).reshape(-1, 2)
    ins = np.zeros(len(P), dtype=bool)
    n = len(Q)
    for i in range(n):
        a, b = Q[i], Q[(i + 1) % n]
        c = ((a[1] > P[:, 1]) != (b[1] > P[:, 1])) & (P[:, 0] < (b[0] - a[0]) * (P[:, 1] - a[1]) / (b[1] - a[1] + 1e-12) + a[0])
        ins ^= c
    return ins


def _local_to_world_xy(L):
    L = np.asarray(L, dtype=float)
    return O2 + L[..., 0:1] * U + L[..., 1:2] * V


def in_kiosk_box_world(W):
    W = np.asarray(W, dtype=float).reshape(-1, 3)
    return bool(np.all((W[:, :2] > KIOSK_BOX[0]) & (W[:, :2] < KIOSK_BOX[1])))


def _pad_poly(scale):
    P = np.array(KIOSK_PAD)
    c = P.mean(0)
    return c + (P - c) * scale, c


def in_pad(xy, scale):
    Q, _ = _pad_poly(scale)
    xy = np.asarray(xy, dtype=float).reshape(-1, 2)
    ok = np.ones(len(xy), dtype=bool)
    for i in range(len(Q)):
        a, b = Q[i], Q[(i + 1) % len(Q)]
        ok &= ((b[0] - a[0]) * (xy[:, 1] - a[1]) - (b[1] - a[1]) * (xy[:, 0] - a[0])) >= 0
    return ok


def pad_z(x, y):
    """Lot level inside the outline: the fan (centre + corners) interpolated."""
    Q, c = _pad_poly(1.0)
    zc = float(np.mean(KIOSK_PAD_GZ))
    p = np.array([x, y])
    best = None
    for i in range(len(Q)):
        a, b = Q[i], Q[(i + 1) % len(Q)]
        M = np.array([[a[0] - c[0], b[0] - c[0]], [a[1] - c[1], b[1] - c[1]]])
        try:
            u, v = np.linalg.solve(M, p - c)
        except np.linalg.LinAlgError:
            continue
        z = zc + u * (KIOSK_PAD_GZ[i] - zc) + v * (KIOSK_PAD_GZ[(i + 1) % len(Q)] - zc)
        score = min(u, v)
        if best is None or score > best[0]:
            best = (score, z)
    return float(best[1])


def _kiosk_tri(r, zkeep=KIOSK_ZKEEP):
    W = _local_to_world_xy(r["L"])
    if not np.all((W > KIOSK_BOX[0]) & (W < KIOSK_BOX[1])):
        return False
    return bool(r["L"][:, 2].max() > zkeep or in_pad(W, KIOSK_PLINTH_SCALE).all())


def enable_street():
    global STREET_ON, BUILD2_REMOVED_TRIS
    STREET_ON = True
    BUILD2_RULES["KIOSK"] = dict(expect=KIOSK_EXPECT["build2"], test=_kiosk_tri)
    EMISSIVE_RULES["KIOSK"] = dict(expect=KIOSK_EXPECT["emissive"], test=_kiosk_tri)
    BUILD2_REMOVED_TRIS = sum(r["expect"] for r in BUILD2_RULES.values())


def _pad_cells(step=0.5):
    Q, c = _pad_poly(1.0)
    out = []
    x0, y0 = Q.min(0)
    x1, y1 = Q.max(0)
    nx, ny = int(math.ceil((x1 - x0) / step)), int(math.ceil((y1 - y0) / step))
    for ix in range(nx):
        for iy in range(ny):
            cx, cy = x0 + (ix + 0.5) * step, y0 + (iy + 0.5) * step
            if in_pad([(cx, cy)], 1.03)[0]:
                out.append((cx, cy, step / 2 + 0.01, pad_z(cx, cy)))
    return out


def kiosk_bound_edit(bound, BoundVertex, BoundPrimitive, BoundPrimitiveType, lo=40, hi=400):
    """Remove every collision primitive of the kiosk / signs (inside KIOSK_BOX, reaching above z 24.3) and the plinth
    boxes (inside the outline, not the ground triangles); close the hole with boxes whose tops follow the lot level."""
    from szio.types import Vector as _SzVec
    removed = {}
    ref = None
    for ci, c in enumerate(bound.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        keep = []
        for p in c.geometry_primitives:
            Pw = _prim_corners(p, c.geometry_vertices)
            if in_kiosk_box_world(Pw):
                high = Pw[:, 2].max() > 24.3
                plinth = (not high) and p.primitive_type.name != "TRIANGLE" and bool(in_pad(Pw[:, :2], KIOSK_PLINTH_SCALE).all())
                if high or plinth:
                    k = f"c{ci}:{p.primitive_type.name}:{p.material.material_index}" + (":plinth" if plinth else "")
                    removed[k] = removed.get(k, 0) + 1
                    if ref is None and p.primitive_type.name == "BOX" and p.material.material_index == 1:
                        ref = (ci, p)
                    continue
            keep.append(p)
        c.geometry_primitives = keep
    n_removed = n = sum(removed.values())
    if not (lo <= n <= hi):
        raise RuntimeError(f"kiosk collision: removed {n} primitives, expected {lo}..{hi} - source differs, abort ({removed})")
    if ref is None:
        raise RuntimeError("kiosk collision: no concrete box (mat 1) among the removed ones to copy the material from")
    # 0.3.0-d: smooth fill = the same fan as the visible ground, as TRIANGLE primitives cloned from the nearest lot triangle
    import copy as _copy, dataclasses as _dc
    Q, c2 = _pad_poly(KIOSK_FILL_SCALE)
    tref = None
    for ci, c in enumerate(bound.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        for p in c.geometry_primitives:
            if p.primitive_type.name != "TRIANGLE":
                continue
            Pw = _prim_corners(p, c.geometry_vertices)
            n = np.cross(Pw[1] - Pw[0], Pw[2] - Pw[0])
            ln = np.linalg.norm(n)
            if ln < 1e-9 or abs(n[2]) / ln < 0.9:
                continue
            dd = float(np.linalg.norm(Pw.mean(0)[:2] - c2))
            if dd < 12.0 and abs(Pw[:, 2].mean() - float(np.mean(KIOSK_PAD_GZ))) < 0.6 and (tref is None or dd < tref[0]):
                tref = (dd, ci, p)
    if tref is not None:
        _, ci, rp = tref
        child = bound.children[ci]
        H = _hole_ccw()                                                            # 0.3.0-e: the exact hole, 3 % bigger
        c2 = np.array(KIOSK_HOLE_C)
        w = 1.0 / np.maximum(np.linalg.norm(H[:, :2] - c2, axis=1), 0.1)
        zc = float((H[:, 2] * w).sum() / w.sum())
        Q = c2 + (H[:, :2] - c2) * 1.03
        pts = [(c2[0], c2[1], zc)] + [(q[0], q[1], float(H[i, 2])) for i, q in enumerate(Q)]
        # the exporter keeps the child's quantisation box: a vertex outside it wraps and the triangle is lost (weapon
        # bound, first try: 2 of 9 gone) -> keep every point inside the box of the child's existing vertices
        EV = np.array([[float(x) for x in v.co] for v in child.geometry_vertices])
        lo_, hi_ = EV.min(0) + 0.05, EV.max(0) - 0.05
        clamped = sum(1 for q in pts if (np.array(q) < lo_).any() or (np.array(q) > hi_).any())
        pts = [tuple(np.minimum(np.maximum(np.array(q), lo_), hi_)) for q in pts]
        removed["_fill_points_clamped"] = 0
        fill_clamped = clamped
        base = len(child.geometry_vertices)
        for v in pts:
            child.geometry_vertices.append(BoundVertex(_SzVec(tuple(float(x) for x in v)), child.geometry_vertices[0].color))
        added = 0
        for k in range(len(Q)):
            vids = (base, base + 1 + k, base + 1 + (k + 1) % len(Q))                # CCW from above
            try:
                np_ = _dc.replace(rp, vertices=vids)
            except Exception:
                np_ = _copy.copy(rp)
                np_.vertices = vids
            child.geometry_primitives.append(np_)
            added += 1
        removed.pop("_fill_points_clamped", None)
        return {"removed": removed, "removed_total": n_removed, "cap_boxes": added, "cap_kind": "triangles", "cap_child": ci,
                "fill_points_clamped": fill_clamped, "child_box": [lo_.round(2).tolist(), hi_.round(2).tolist()],
                "cap_material": int(rp.material.material_index), "cap_ref_dist_m": round(tref[0], 2)}
    ci, rp = ref                                                                   # no lot triangle in this bound: boxes
    child = bound.children[ci]
    added = 0
    axes = [np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])]
    for cx, cy, h, zt in _pad_cells():
        center = np.array([cx, cy, zt - 0.30])
        vids = []
        for v in _box_vertices(center, axes, [h, h, 0.30]):
            child.geometry_vertices.append(BoundVertex(_SzVec(tuple(float(x) for x in v)), child.geometry_vertices[0].color))
            vids.append(len(child.geometry_vertices) - 1)
        child.geometry_primitives.append(BoundPrimitive(primitive_type=BoundPrimitiveType.BOX, material=rp.material,
                                                        material_color=rp.material_color, vertices=tuple(vids), radius=None))
        added += 1
    return {"removed": removed, "removed_total": n_removed, "cap_boxes": added, "cap_kind": "boxes", "cap_child": ci,
            "cap_material": int(rp.material.material_index)}


PATIO_TILE_TEX = "sc1_23_rsn_ns_ground_0001"      # the cracked tile walkway between the shop and the kiosk site
PATIO_R = 20.0


_TILE_MAP = {}
# 0.3.1-j (owner, screenshot of the asphalt wedge next to the fence): the tarmac between the fence and the patio becomes
# tile too - a rectangle along the fence, a = 0 .. 9.2 m, b = 0 .. 2.6 m (a along the fence line, b into the patio).
PATIO_F = np.array([393.30, -1931.60])
PATIO_A = np.array([0.756, -0.655])
PATIO_B = np.array([0.655, 0.756])
PATIO_RECT = (-1.5, 9.2, -0.05, 2.6)                     # a0, a1, b0, b1  (0.3.1-j .. k)
# 0.3.1-l (revision): the vanilla
# kerb (IM_Kerbs03, sc1_14_grnd_02) ended 4.67 m before the fence and a tarmac pocket was left between it and the tile
# patch. The kerb now runs on to the fence (extend_kerb) and the patio boundary follows it: tile west of the middle of
# the kerb, tarmac east of it, from the fence (b = -0.05) up to the end of the vanilla kerb (b = 4.75).
PATIO_RECT = (-1.5, 9.4, -0.60, 4.75)                    # a0, (a1 = kerb middle at b0 of the kerb), b0 (strip outside the fence too), b1
KERB_EXT = dict(a_in=9.25, b0=4.67, slope=0.0289, top_w=0.29, bevel=(0.02, 0.02), b_end=-0.02, step=0.5,
                road_h=0.09, patio_h=0.02, bury=0.04, u0=6.618, du_db=-0.24434,
                v=dict(inner=-1.198, outer=-1.119, bevel=-1.106, bottom=-1.001))


def _patio_halfplanes():
    a0, a1, b0, b1 = PATIO_RECT
    F, A, B = PATIO_F, PATIO_A, PATIO_B
    k = KERB_EXT
    # east edge = the middle line of the kerb (direction (slope, 1) in (a, b)); inside = west of it
    P0 = F + (k["a_in"] + k["top_w"] / 2) * A + k["b0"] * B
    n = -A + k["slope"] * B
    n = n / np.linalg.norm(n)
    return [(B, float(B @ F + b0)), (-B, float(-(B @ F) - b1)), (A, float(A @ F + a0)), (n, float(n @ P0))]


def _ground_z(drawable, ent_pos, xy, texs):
    """Highest ground surface (geometries with one of texs) at world xy; None outside."""
    sg = drawable.shader_group
    best = None
    for lod, models in drawable.models.items():
        for m in models:
            for g in m.geometries:
                if _shader_tex(sg.shaders[g.shader_index]) not in texs:
                    continue
                pos = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos
                I = np.asarray(g.index_buffer, dtype=np.int64).reshape(-1, 3)
                T = pos[I]
                lo, hi = T[:, :, :2].min(1), T[:, :, :2].max(1)
                cand = np.where((lo[:, 0] <= xy[0]) & (hi[:, 0] >= xy[0]) & (lo[:, 1] <= xy[1]) & (hi[:, 1] >= xy[1]))[0]
                for ti in cand:
                    t = T[ti]
                    M = np.array([t[1, :2] - t[0, :2], t[2, :2] - t[0, :2]]).T
                    if abs(np.linalg.det(M)) < 1e-10:
                        continue
                    u, v = np.linalg.solve(M, np.asarray(xy) - t[0, :2])
                    if u >= -1e-6 and v >= -1e-6 and u + v <= 1 + 1e-6:
                        z = float(t[0, 2] + u * (t[1, 2] - t[0, 2]) + v * (t[2, 2] - t[0, 2]))
                        best = z if best is None else max(best, z)
    return best


def extend_kerb(drawable, ent_pos, tex="im_kerbs03"):
    """0.3.1-l: continue the vanilla kerb from its end (b = 4.67) straight on to the fence (b = -0.02), same profile, same
    texture / UV run / vertex colours as the vanilla piece (vertex records cloned from the kerb's own end vertices), top
    following the ground (road side + 9 cm, patio side + 2 cm), faces buried 4 cm. The vanilla end cap is removed (it is
    inside the kerb now) and a new cap closes the kerb at the fence. Run AFTER clip_tarmac_to_tile (samples the final ground)."""
    k = KERB_EXT
    F, A, B = PATIO_F, PATIO_A, PATIO_B
    sg = drawable.shader_group
    g = None
    for lod, models in drawable.models.items():
        for m in models:
            for gg in m.geometries:
                if _shader_tex(sg.shaders[gg.shader_index]) == tex:
                    pos = np.array(gg.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos
                    ab = np.c_[(pos[:, :2] - F) @ A, (pos[:, :2] - F) @ B]
                    if (np.abs(ab[:, 1] - k["b0"]) < 0.03).sum() >= 4 and (np.abs(ab[:, 0] - 9.4) < 0.4).any():
                        g = gg
    if g is None:
        raise RuntimeError("extend_kerb: kerb geometry not found")
    vb = np.asarray(g.vertex_buffer)
    ib = np.asarray(g.index_buffer, dtype=np.int64).reshape(-1, 3)
    pos = np.array(vb["Position"], dtype=float).reshape(-1, 3) + ent_pos
    ab = np.c_[(pos[:, :2] - F) @ A, (pos[:, :2] - F) @ B]
    nrm = np.array(vb["Normal"], dtype=float).reshape(-1, 3)
    uvs = np.array(vb["TexCoord0"], dtype=float).reshape(-1, 2)
    at_end = (np.abs(ab[:, 1] - k["b0"]) < 0.03) & (ab[:, 0] > k["a_in"] - 0.1) & (ab[:, 0] < k["a_in"] + 0.45)
    capn = -B
    is_cap = at_end & (np.abs(nrm[:, :2] @ capn) > 0.9)
    long_ = at_end & ~is_cap

    def pick(vname, want_low=False):
        c = np.where(long_ & (np.abs(uvs[:, 1] - k["v"][vname]) < 0.004))[0]
        if not len(c):
            raise RuntimeError(f"extend_kerb: end vertex '{vname}' not found")
        return int(c[np.argmin(pos[c, 2])] if want_low else c[0])

    T = {nm: pick(nm) for nm in ("inner", "outer", "bevel", "bottom")}
    top0 = float(pos[T["inner"], 2])
    # remove the vanilla end cap (all three vertices on the cap plane, cap normal)
    capt = np.array([all(is_cap[v] for v in t) for t in ib], dtype=bool)
    n_cap = int(capt.sum())
    if not (2 <= n_cap <= 4):
        raise RuntimeError(f"extend_kerb: {n_cap} cap triangles (expected 3) - source differs, abort")
    # winding convention of this mesh (cross of a long top triangle vs its vertex normal)
    conv = 1.0
    for t in ib[~capt]:
        if T["inner"] in t and T["outer"] in t:
            W = pos[t]
            cr = np.cross(W[1] - W[0], W[2] - W[0])
            conv = 1.0 if cr[2] > 0 else -1.0
            break
    texs = {PATIO_TILE_TEX, "dc_parking_tarmac_01", KIOSK_FILL_TEX}
    stations = list(np.arange(k["b0"], k["b_end"], -k["step"])) + [k["b_end"]]
    stations = sorted(set(round(float(s), 4) for s in stations), reverse=True)
    recs, tris = [], []
    n0 = len(vb)

    def world(a, b, z):
        p2 = F + a * A + b * B
        return np.array([p2[0], p2[1], z])

    def rec(tmpl, P, u, v, normal=None):
        r = vb[tmpl:tmpl + 1].copy()
        r["Position"][0] = tuple(P - ent_pos)
        r["TexCoord0"][0] = (u, v)
        if normal is not None:
            r["Normal"][0] = tuple(normal)
        recs.append(r)
        return n0 + len(recs) - 1

    zs = []
    rows = []
    for si, b in enumerate(stations):
        ai = k["a_in"] + k["slope"] * (b - k["b0"])
        ao = ai + k["top_w"]
        ab_ = ao + k["bevel"][0]
        bs = max(b, 0.06)                                          # the lot ends right at the fence line
        zp = _ground_z(drawable, ent_pos, (F + (ai - 0.06) * A + bs * B), texs)
        zr = _ground_z(drawable, ent_pos, (F + (ab_ + 0.08) * A + bs * B), texs)
        if zp is None or zr is None:
            if not zs:
                raise RuntimeError("extend_kerb: no ground under the kerb end")
            zp, zr = zs[-1][2], zs[-1][3]
        top = max(zp + k["patio_h"], zr + k["road_h"])
        w = min(1.0, (k["b0"] - b) / 0.6)                       # blend into the vanilla end over the first 0.6 m
        top = (1 - w) * top0 + w * top
        zs.append((round(b, 2), round(top, 3), round(zp, 3), round(zr, 3)))
        u = k["u0"] + k["du_db"] * (b - k["b0"])
        if si == 0:
            row = dict(inner=T["inner"], outer=T["outer"], bevel=T["bevel"], bottom=T["bottom"])
            P_ib = world(ai, b, min(zp, top) - k["bury"])
        else:
            row = dict(inner=rec(T["inner"], world(ai, b, top), u, k["v"]["inner"]),
                       outer=rec(T["outer"], world(ao, b, top), u, k["v"]["outer"]),
                       bevel=rec(T["bevel"], world(ab_, b, top - k["bevel"][1]), u, k["v"]["bevel"]),
                       bottom=rec(T["bottom"], world(ab_, b, zr - k["bury"]), u, k["v"]["bottom"]))
            P_ib = world(ai, b, zp - k["bury"])
        nin = tuple(-nrm[T["bottom"]])                                   # inner face looks to the patio
        h_in = max(0.0, top - (zp - k["bury"]))
        row["in_top"] = rec(T["bottom"], world(ai, b, top), u, k["v"]["bevel"], nin)
        row["in_bot"] = rec(T["bottom"], P_ib, u, k["v"]["bevel"] + 0.105 * h_in / 0.13, nin)
        row["P"] = dict(ai=ai, ao=ao, ab=ab_, top=top, zp=zp, zr=zr, u=u)
        rows.append(row)

    allpos = lambda i: (np.asarray(vb["Position"][i], float) + ent_pos) if i < n0 else (np.asarray(recs[i - n0]["Position"][0], float) + ent_pos)

    def quad(p, q, r, s, want):                                   # p,q at station i ; r,s at station i+1 (same slots)
        for t in ((p, q, s), (p, s, r)):
            W = [allpos(x) for x in t]
            cr = np.cross(W[1] - W[0], W[2] - W[0])
            if float(cr @ np.asarray(want)) * conv < 0:
                t = (t[0], t[2], t[1])
            tris.append(t)

    up = np.array([0.0, 0.0, 1.0])
    out_n = np.array([A[0], A[1], 0.0])
    for r0, r1 in zip(rows[:-1], rows[1:]):
        quad(r0["inner"], r0["outer"], r1["inner"], r1["outer"], up)
        quad(r0["outer"], r0["bevel"], r1["outer"], r1["bevel"], up + out_n)
        quad(r0["bevel"], r0["bottom"], r1["bevel"], r1["bottom"], out_n)
        quad(r0["in_top"], r0["in_bot"], r1["in_top"], r1["in_bot"], -out_n)
    # cap at the fence (normal -B), one fan: inner-bottom, inner-top, outer-top, bevel, bottom
    e = rows[-1]
    capw = np.array([-B[0], -B[1], 0.0])
    P = e["P"]
    cu = P["u"]
    cid = [rec(T["inner"], world(P["ai"], stations[-1], P["zp"] - k["bury"]), cu, k["v"]["inner"], capw),
           rec(T["inner"], world(P["ai"], stations[-1], P["top"]), cu, k["v"]["inner"], capw),
           rec(T["outer"], world(P["ao"], stations[-1], P["top"]), cu, k["v"]["outer"], capw),
           rec(T["bevel"], world(P["ab"], stations[-1], P["top"] - k["bevel"][1]), cu, k["v"]["bevel"], capw),
           rec(T["bottom"], world(P["ab"], stations[-1], P["zr"] - k["bury"]), cu, k["v"]["bottom"], capw)]
    for j in range(1, len(cid) - 1):
        t = (cid[0], cid[j], cid[j + 1])
        W = [allpos(x) for x in t]
        cr = np.cross(W[1] - W[0], W[2] - W[0])
        if float(cr @ capw) * conv < 0:
            t = (t[0], t[2], t[1])
        tris.append(t)
    if n0 + len(recs) > 65535:
        raise RuntimeError("extend_kerb: 16-bit index overflow")
    g.vertex_buffer = np.concatenate([vb] + recs)
    keep = ib[~capt]
    g.index_buffer = np.concatenate([keep.reshape(-1), np.array(tris, dtype=np.int64).reshape(-1)]).astype(np.asarray(g.index_buffer).dtype)
    return {"stations": len(stations), "removed_cap_tris": n_cap, "added_tris": len(tris), "added_verts": len(recs),
            "winding": conv, "top_z": [z[1] for z in zs], "patio_z": [z[2] for z in zs], "road_z": [z[3] for z in zs],
            "b": [z[0] for z in zs], "len_m": round(k["b0"] - k["b_end"], 2)}


def _split(poly, xy, n, c):
    """poly: list of barycentric weights (3,); keep n.p >= c in 'ins', the rest in 'outs'."""
    ins, outs = [], []
    k = len(poly)
    for i in range(k):
        w0, w1 = poly[i], poly[(i + 1) % k]
        f0, f1 = float(n @ (w0 @ xy)) - c, float(n @ (w1 @ xy)) - c
        if f0 >= 0:
            ins.append(w0)
        if f0 <= 0:
            outs.append(w0)
        if (f0 > 0 > f1) or (f0 < 0 < f1):
            w = w0 + (w1 - w0) * (f0 / (f0 - f1))
            ins.append(w)
            outs.append(w)
    return ins, outs


def _poly_area(poly, xy):
    P = np.array([w @ xy for w in poly])
    if len(P) < 3:
        return 0.0
    x, y = P[:, 0], P[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def _blend(vb, tri, w):
    """One vertex record = barycentric blend of the three vertices of tri (every field, cast back to its dtype)."""
    rec = vb[tri[0]:tri[0] + 1].copy()
    for nm in vb.dtype.names:
        vals = np.array([np.asarray(vb[nm][i], dtype=float) for i in tri])
        v = (w[:, None] * vals.reshape(3, -1)).sum(0) if vals.ndim > 1 else float((w * vals).sum())
        dt = vb.dtype[nm]
        base = dt.base if dt.shape else dt
        if np.issubdtype(base, np.integer):
            v = np.clip(np.round(v), np.iinfo(base).min, np.iinfo(base).max)
        rec[nm][0] = np.asarray(v).reshape(rec[nm][0].shape) if dt.shape else v
    return rec


# 0.3.1-m (owner screenshot 2026-11-13 23:03: the tiles meet the hatched parking tarmac with no kerb between the end of
# the vanilla kerb and the planter kerb): a kerb along that tile / tarmac edge. Q = points on the edge in patio (a, b);
# the first point is the foot of the vanilla kerb end, the run pivots there and follows the edge to the planter kerb.
KERB_RUN2 = dict(path=[(-3.64, 8.92), (-5.00, 8.46), (-6.97, 7.50)], L0=(1.0, 0.0), top_w=0.29, bevel=(0.02, 0.02),
                 height=0.08, bury=0.04, step=0.55, blend=0.7, u0=4.236, du=0.24434, z0_top=23.775, z0_bot=23.625,
                 v=dict(inner=-1.198, outer=-1.12, bevel=-1.107, bottom=-1.001))


def add_kerb_run(drawable, ent_pos, cfg=None, tex="im_kerbs03"):
    """Kerb (vanilla IM_Kerbs03 material, vertex records cloned from the vanilla kerb end next to it) along cfg['path']:
    road on the right of the walking direction, body on the left (tile side), raised cfg['height'] over the ground."""
    k = cfg or KERB_RUN2
    F, A, B = PATIO_F, PATIO_A, PATIO_B
    sg = drawable.shader_group
    Q = [np.array(q, float) for q in k["path"]]
    g = None
    for lod, models in drawable.models.items():
        for m in models:
            for gg in m.geometries:
                if _shader_tex(sg.shaders[gg.shader_index]) == tex:
                    pos = np.array(gg.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos
                    ab = np.c_[(pos[:, :2] - F) @ A, (pos[:, :2] - F) @ B]
                    if (np.linalg.norm(ab - Q[0], axis=1) < 0.06).sum() >= 2:
                        g = gg
    if g is None:
        raise RuntimeError("add_kerb_run: vanilla kerb end not found at the path start")
    vb = np.asarray(g.vertex_buffer)
    ib = np.asarray(g.index_buffer, dtype=np.int64).reshape(-1, 3)
    pos = np.array(vb["Position"], dtype=float).reshape(-1, 3) + ent_pos
    ab = np.c_[(pos[:, :2] - F) @ A, (pos[:, :2] - F) @ B]
    uvs = np.array(vb["TexCoord0"], dtype=float).reshape(-1, 2)
    near = np.linalg.norm(ab - Q[0], axis=1) < 0.40
    T = {}
    for nm, vv in k["v"].items():
        c = np.where(near & (np.abs(uvs[:, 1] - vv) < 0.004))[0]
        if not len(c):
            raise RuntimeError(f"add_kerb_run: template vertex '{nm}' not found")
        T[nm] = int(c[0])
    conv = 1.0
    for t in ib:
        W = pos[t]
        cr = np.cross(W[1] - W[0], W[2] - W[0])
        if abs(cr[2]) > 0.9 * np.linalg.norm(cr) > 1e-9:
            nz = float(np.asarray(vb["Normal"][t[0]], float).reshape(-1)[2])
            conv = 1.0 if cr[2] * nz > 0 else -1.0
            break
    texs = {PATIO_TILE_TEX, "dc_parking_tarmac_01", KIOSK_FILL_TEX}
    # sections: (q, L, dist)  q = edge point, L = unit vector to the tile side (scaled at mitres)
    def left(h):
        return np.array([-h[1], h[0]])
    hs = [(Q[i + 1] - Q[i]) / np.linalg.norm(Q[i + 1] - Q[i]) for i in range(len(Q) - 1)]
    secs = []
    L0, L1 = np.array(k["L0"], float), left(hs[0])
    a0, a1 = math.atan2(L0[1], L0[0]), math.atan2(L1[1], L1[0])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    nf = max(2, int(abs(da) / math.radians(24)) + 1)
    dist = 0.0
    for j in range(nf + 1):                                           # fan about the pivot Q0
        an = a0 + da * j / nf
        secs.append((Q[0], np.array([math.cos(an), math.sin(an)]), dist))
        dist += abs(da) / nf * k["top_w"] * 0.5
    for i in range(len(hs)):
        seg = float(np.linalg.norm(Q[i + 1] - Q[i]))
        n = max(1, int(round(seg / k["step"])))
        for j in range(1, n + 1):
            q = Q[i] + hs[i] * seg * j / n
            L = left(hs[i])
            if j == n and i + 1 < len(hs):                            # mitre
                Lm = left(hs[i]) + left(hs[i + 1])
                Lm /= np.linalg.norm(Lm)
                L = Lm / float(Lm @ left(hs[i]))
            secs.append((q, L, dist + seg * j / n))
        dist += seg
    recs, tris = [], []
    n0 = len(vb)

    def world(p2, z):
        w = F + p2[0] * A + p2[1] * B
        return np.array([w[0], w[1], z])

    def rec(tmpl, P, u, v, normal):
        r = vb[tmpl:tmpl + 1].copy()
        r["Position"][0] = tuple(P - ent_pos)
        r["TexCoord0"][0] = (u, v)
        r["Normal"][0] = tuple(normal)
        recs.append(r)
        return n0 + len(recs) - 1

    rows, zlog = [], []
    bw, bh = k["bevel"]
    for (q, L, ds) in secs:
        Lw = np.array([(L[0] * A + L[1] * B)[0], (L[0] * A + L[1] * B)[1], 0.0])
        Lw /= np.linalg.norm(Lw)
        zt = _ground_z(drawable, ent_pos, F + (q + L * 0.45)[0] * A + (q + L * 0.45)[1] * B, texs)
        zr = _ground_z(drawable, ent_pos, F + (q - L * 0.12)[0] * A + (q - L * 0.12)[1] * B, texs)
        if zt is None or zr is None:
            if not zlog:
                raise RuntimeError("add_kerb_run: no ground at the path start")
            zt, zr = zlog[-1][1], zlog[-1][2]
        w = min(1.0, ds / k["blend"])
        top = (1 - w) * k["z0_top"] + w * (max(zt, zr) + k["height"])
        zb_r = (1 - w) * k["z0_bot"] + w * (zr - k["bury"])
        zb_t = min(zt, top) - k["bury"]
        zlog.append((round(ds, 2), round(zt, 3), round(zr, 3), round(top, 3)))
        u = k["u0"] + k["du"] * ds
        up = (0.0, 0.0, 1.0)
        road = -Lw
        nb = road * 0.7 + np.array([0, 0, 0.7])
        rows.append(dict(
            inner=rec(T["inner"], world(q + L * (bw + k["top_w"]), top), u, k["v"]["inner"], up),
            outer=rec(T["outer"], world(q + L * bw, top), u, k["v"]["outer"], up),
            bev_t=rec(T["outer"], world(q + L * bw, top), u, k["v"]["outer"], nb),
            bevel=rec(T["bevel"], world(q, top - bh), u, k["v"]["bevel"], nb),
            side_t=rec(T["bevel"], world(q, top - bh), u, k["v"]["bevel"], road),
            bottom=rec(T["bottom"], world(q, zb_r), u, k["v"]["bottom"], road),
            in_top=rec(T["bottom"], world(q + L * (bw + k["top_w"]), top), u, k["v"]["bevel"], Lw),
            in_bot=rec(T["bottom"], world(q + L * (bw + k["top_w"]), zb_t), u, k["v"]["bevel"] + 0.105 * max(0.0, top - zb_t) / 0.13, Lw),
            Lw=Lw, q=q, L=L, top=top, zb_r=zb_r, zb_t=zb_t, u=u))

    def P_(i):
        return np.asarray(recs[i - n0]["Position"][0], float) + ent_pos

    def quad(p, q_, r, s_, want):
        for t in ((p, q_, s_), (p, s_, r)):
            W = [P_(x) for x in t]
            cr = np.cross(W[1] - W[0], W[2] - W[0])
            if np.linalg.norm(cr) < 1e-7:
                continue
            if float(cr @ np.asarray(want)) * conv < 0:
                t = (t[0], t[2], t[1])
            tris.append(t)

    up = np.array([0.0, 0.0, 1.0])
    for r0, r1 in zip(rows[:-1], rows[1:]):
        road = -(r0["Lw"] + r1["Lw"]) / 2
        quad(r0["inner"], r0["outer"], r1["inner"], r1["outer"], up)
        quad(r0["bev_t"], r0["bevel"], r1["bev_t"], r1["bevel"], up + road)
        quad(r0["side_t"], r0["bottom"], r1["side_t"], r1["bottom"], road)
        quad(r0["in_top"], r0["in_bot"], r1["in_top"], r1["in_bot"], -road)
    e = rows[-1]
    hw = hs[-1][0] * A + hs[-1][1] * B
    capn = np.array([hw[0], hw[1], 0.0])
    q, L = e["q"], e["L"]
    cid = [rec(T["inner"], world(q + L * (bw + k["top_w"]), e["zb_t"]), e["u"], k["v"]["inner"], capn),
           rec(T["inner"], world(q + L * (bw + k["top_w"]), e["top"]), e["u"], k["v"]["inner"], capn),
           rec(T["outer"], world(q + L * bw, e["top"]), e["u"], k["v"]["outer"], capn),
           rec(T["bevel"], world(q, e["top"] - bh), e["u"], k["v"]["bevel"], capn),
           rec(T["bottom"], world(q, e["zb_r"]), e["u"], k["v"]["bottom"], capn)]
    for j in range(1, len(cid) - 1):
        t = (cid[0], cid[j], cid[j + 1])
        W = [P_(x) for x in t]
        cr = np.cross(W[1] - W[0], W[2] - W[0])
        if float(cr @ capn) * conv < 0:
            t = (t[0], t[2], t[1])
        tris.append(t)
    if n0 + len(recs) > 65535:
        raise RuntimeError("add_kerb_run: 16-bit index overflow")
    g.vertex_buffer = np.concatenate([vb] + recs)
    g.index_buffer = np.concatenate([ib.reshape(-1), np.array(tris, dtype=np.int64).reshape(-1)]).astype(np.asarray(g.index_buffer).dtype)
    return {"sections": len(secs), "added_tris": len(tris), "added_verts": len(recs), "winding": conv,
            "len_m": round(dist, 2), "z": zlog}


def clip_tarmac_to_tile(drawable, ent_pos, tex="dc_parking_tarmac_01"):
    """Cut the tarmac triangles along PATIO_RECT: the part inside goes to the tile geometry (same mapping / colour as
    retile_patio), the part outside stays tarmac. New vertices are barycentric blends -> no gaps, flush edges.
    Decal triangles lying fully inside the rectangle are removed (no parking marks / splats on the tiles)."""
    if not _TILE_MAP:
        raise RuntimeError("clip_tarmac_to_tile: run retile_patio first")
    sg = drawable.shader_group
    HP = _patio_halfplanes()
    c2 = np.array(KIOSK_HOLE_C)
    gtar = gtile = None
    decals = []
    for lod, models in drawable.models.items():
        for m in models:
            for g in m.geometries:
                t = _shader_tex(sg.shaders[g.shader_index])
                sh = sg.shaders[g.shader_index].name.lower()
                pos = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos
                near = int((np.linalg.norm(pos[:, :2] - c2, axis=1) < 20).sum())
                if t == tex and (gtar is None or near > gtar[1]):
                    gtar = (g, near)
                if t == PATIO_TILE_TEX and (gtile is None or near > gtile[1]):
                    gtile = (g, near)
                if "decal" in sh or "decal" in str(getattr(sg.shaders[g.shader_index], "filename", "")).lower():
                    decals.append(g)
    if gtar is None or gtile is None:
        raise RuntimeError("clip_tarmac_to_tile: geometries not found")
    gtar, gtile = gtar[0], gtile[0]

    def inside_all(P):
        return all(float(n @ P[:2]) - c >= -1e-6 for n, c in HP)

    vb = np.asarray(gtar.vertex_buffer)
    ib = np.asarray(gtar.index_buffer).reshape(-1, 3).astype(np.int64)
    pos = np.array(vb["Position"], dtype=float).reshape(-1, 3) + ent_pos
    keep_tris, out_recs, out_tris, in_recs, in_tris = [], [], [], [], []
    moved = cut = 0
    for tri in ib:
        T = pos[tri]
        if all(not any(float(n @ T[k, :2]) - c >= 0 for k in range(3)) for n, c in HP[:1]) and False:
            pass
        flags = [inside_all(T[k]) for k in range(3)]
        xy = T[:, :2]
        # quick reject: all three vertices outside the same half-plane
        if any(all(float(n @ T[k, :2]) - c < 0 for k in range(3)) for n, c in HP):
            keep_tris.append(tri)
            continue
        if all(flags):
            in_tris.append([("old", int(v)) for v in tri])
            moved += 1
            continue
        cur = [np.eye(3)[0], np.eye(3)[1], np.eye(3)[2]]
        pieces_out = []
        for n, c in HP:
            ins, outs = _split(cur, xy, n, c)
            if len(outs) >= 3 and _poly_area(outs, xy) > 1e-5:
                pieces_out.append(outs)
            cur = ins
            if len(cur) < 3 or _poly_area(cur, xy) <= 1e-5:
                cur = []
                break
        if not cur:
            keep_tris.append(tri)                        # touches the rectangle only on an edge
            continue
        cut += 1
        for piece in pieces_out:
            base = len(vb) + len(out_recs)
            for w in piece:
                out_recs.append(_blend(vb, tri, np.asarray(w, float)))
            for k in range(1, len(piece) - 1):
                out_tris.append([base, base + k, base + k + 1])
        rec_ids = []
        for w in cur:
            in_recs.append((tri, np.asarray(w, float)))
            rec_ids.append(("new", len(in_recs) - 1))
        for k in range(1, len(cur) - 1):
            in_tris.append([rec_ids[0], rec_ids[k], rec_ids[k + 1]])
    # tarmac geometry: kept triangles + outside pieces
    vb2 = np.concatenate([vb] + out_recs) if out_recs else vb
    if len(vb2) > 65535:
        raise RuntimeError("clip_tarmac_to_tile: 16-bit overflow (tarmac)")
    ib2 = np.array(keep_tris + out_tris, dtype=np.int64).reshape(-1)
    # tile geometry: whole moved triangles + inside pieces, tile mapping
    vbt = np.asarray(gtile.vertex_buffer)
    ibt = np.asarray(gtile.index_buffer).reshape(-1)
    M2, off, th, colour, ref = _TILE_MAP["M2"], _TILE_MAP["off"], _TILE_MAP["th"], _TILE_MAP["colour"], _TILE_MAP["ref"]
    recs, idmap = [], {}
    names_t = set(vb.dtype.names)

    def tile_rec(src):
        r = vbt[ref:ref + 1].copy()
        for nm in vbt.dtype.names:
            if nm in names_t and nm not in ("TexCoord0", "Tangent", "Colour0", "Normal"):
                r[nm][0] = src[nm][0]
        p = np.asarray(src["Position"][0], dtype=float) + ent_pos
        r["TexCoord0"][0] = M2 @ p[:2] + off
        r["Normal"][0] = (0.0, 0.0, 1.0)
        if colour is not None and "Colour0" in vbt.dtype.names:
            r["Colour0"][0] = tuple(np.asarray(colour).astype(vbt["Colour0"].dtype))
        if "Tangent" in vbt.dtype.names:
            tg = np.asarray(r["Tangent"][0], dtype=float).reshape(-1)
            r["Tangent"][0] = (math.cos(th), math.sin(th), 0.0, tg[3] if len(tg) > 3 else 1.0)
        return r

    tri_out = []
    n0 = len(vbt)
    for tri in in_tris:
        ids = []
        for kind, k in tri:
            key = (kind, k)
            if key not in idmap:
                src = vb[k:k + 1] if kind == "old" else _blend(vb, in_recs[k][0], in_recs[k][1])
                recs.append(tile_rec(src))
                idmap[key] = n0 + len(recs) - 1
            ids.append(idmap[key])
        tri_out.append(ids)
    if n0 + len(recs) > 65535:
        raise RuntimeError("clip_tarmac_to_tile: 16-bit overflow (tile)")
    gtar.vertex_buffer = vb2
    gtar.index_buffer = ib2.astype(np.asarray(gtar.index_buffer).dtype)
    if recs:
        gtile.vertex_buffer = np.concatenate([vbt] + recs)
        gtile.index_buffer = np.concatenate([ibt, np.array(tri_out, dtype=np.int64).reshape(-1).astype(ibt.dtype)])
    # decals fully inside the rectangle
    dec_removed = 0
    for g in decals:
        dp = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos
        di = np.asarray(g.index_buffer).reshape(-1, 3)
        kill = np.array([all(inside_all(dp[v]) for v in t) for t in di], dtype=bool) if len(di) else np.zeros(0, bool)
        if kill.any():
            g.index_buffer = di[~kill].reshape(-1).astype(np.asarray(g.index_buffer).dtype)
            dec_removed += int(kill.sum())
    return {"tarmac_tris_moved_whole": moved, "tarmac_tris_cut": cut, "tarmac_tris_after": int(len(ib2) // 3),
            "tile_tris_added": len(tri_out), "tile_verts_added": len(recs), "decal_tris_removed": dec_removed}


def retile_patio(drawable, ent_pos):
    """0.3.1 (owner: "слева, где забор, поставить одинаковую текстуру дорожки, именно разбитой GTA-шной, чтобы была одна
    дорога"): every triangle of the pale apron (KIOSK_FILL_TEX geometry, incl. the fill of the kiosk hole) within PATIO_R
    of the site moves to the geometry of the tile walkway; planar UV = the similarity mapping of the biggest walkway
    triangle next to the site (same tile size and direction). The textures stay the vanilla ones of this drawable."""
    sg = drawable.shader_group
    gc = gt = None
    c2 = np.array(KIOSK_HOLE_C)
    for lod, models in drawable.models.items():
        for m in models:
            for g in m.geometries:
                t = _shader_tex(sg.shaders[g.shader_index])
                pos = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos
                near = int((np.linalg.norm(pos[:, :2] - c2, axis=1) < PATIO_R).sum())
                if t == KIOSK_FILL_TEX and (gc is None or near > gc[1]):
                    gc = (g, near)
                if t == PATIO_TILE_TEX and (gt is None or near > gt[1]):
                    gt = (g, near)
    if gc is None or gt is None or gc[1] < 6 or gt[1] < 6:
        raise RuntimeError(f"patio retile: geometries not found ({gc and gc[1]}, {gt and gt[1]})")
    gc, gt = gc[0], gt[0]
    vbc, vbt = np.asarray(gc.vertex_buffer), np.asarray(gt.vertex_buffer)
    ibc = np.asarray(gc.index_buffer).reshape(-1, 3)
    ibt = np.asarray(gt.index_buffer).reshape(-1, 3)
    pc = np.array(vbc["Position"], dtype=float).reshape(-1, 3) + ent_pos
    pt = np.array(vbt["Position"], dtype=float).reshape(-1, 3) + ent_pos
    uvt = np.array(vbt["TexCoord0"], dtype=float).reshape(-1, 2)
    # mapping of the biggest flat walkway triangle near the site
    T = pt[ibt]
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    area = np.linalg.norm(nrm, axis=1) / 2
    dc = np.linalg.norm(T.mean(1)[:, :2] - c2, axis=1)
    ok = (dc < 16.0) & (np.abs(nrm[:, 2]) > 0.9 * np.maximum(np.linalg.norm(nrm, axis=1), 1e-9))
    if not ok.any():
        raise RuntimeError("patio retile: no walkway triangle near the site")
    score = np.where(ok, area, -1.0)
    ti = int(np.argmax(score))
    co = np.linalg.solve(np.c_[T[ti][:, :2], np.ones(3)], uvt[ibt[ti]])          # rows: x, y, 1 -> (u, v)
    M = co[:2].T                                                                   # [[du/dx, du/dy], [dv/dx, dv/dy]]
    det = float(np.linalg.det(M))
    sc = math.sqrt(abs(det))
    if not (0.05 <= sc <= 2.0):
        sc = 0.25
    th = math.atan2(M[0, 1], M[0, 0])
    sgn = 1.0 if det >= 0 else -1.0
    M2 = sc * np.array([[math.cos(th), math.sin(th)], [-sgn * math.sin(th), sgn * math.cos(th)]])
    off = uvt[ibt[ti][0]] - M2 @ T[ti][0, :2]
    # 0.3.1-l (owner screenshots 21:43, "ledge" lines where the kiosk stood): that triangle lies 15 m away; at the old
    # kiosk outline the walkway's grout is 0.03 UV (8 cm) off this mapping -> the tiles jumped along the outline. The
    # walkway UVs are per-island (integer offsets), so the offset is corrected by the median FRACTIONAL residual of the
    # flat walkway vertices within 2.5 m of the outline.
    fit_rms = None
    Hh0 = _hole_ccw()[:, :2]
    fv = np.unique(ibt[ok])
    dh0 = np.min(np.stack([_seg_dist(pt[fv, :2], Hh0[i], Hh0[(i + 1) % len(Hh0)]) for i in range(len(Hh0))]), axis=0)
    fv = fv[dh0 < 2.5]
    if len(fv) >= 4:
        r = uvt[fv] - ((M2 @ pt[fv, :2].T).T + off)
        r -= np.round(r)
        corr = np.median(r, axis=0)
        off = off + corr
        r2 = r - corr
        fit_rms = [round(float(x), 4) for x in corr] + [round(float(np.sqrt((r2 ** 2).mean())), 4), int(len(fv))]
    # triangles to move
    cen = pc[ibc].mean(1)
    move = np.linalg.norm(cen[:, :2] - c2, axis=1) < PATIO_R
    used = np.unique(ibc[move])
    remap = {int(v): i for i, v in enumerate(used)}
    add = np.repeat(vbt[int(ibt[ti][0]):int(ibt[ti][0]) + 1], len(used), axis=0).copy()
    names_c = set(vbc.dtype.names)
    for i, v in enumerate(used):
        for nm in vbt.dtype.names:
            if nm in names_c and nm not in ("TexCoord0", "Tangent"):
                add[nm][i] = vbc[nm][v]
        add["TexCoord0"][i] = M2 @ pc[v, :2] + off
        if "Tangent" in vbt.dtype.names:
            tg = np.array(add["Tangent"][i], dtype=float).reshape(-1)
            add["Tangent"][i] = (math.cos(th), math.sin(th), 0.0, tg[3] if len(tg) > 3 else 1.0)
    # 0.3.1-d (revision): the apron polygons kept their own baked vertex shading -> darker / lighter
    # polygons with zigzag edges on one tile surface. One colour (median of the walkway next to the site) for all.
    seam = None
    if "Colour0" in vbt.dtype.names:
        nt = np.linalg.norm(pt[:, :2] - c2, axis=1) < 18.0
        if nt.sum() >= 4:
            med = np.median(np.array(vbt["Colour0"][nt], dtype=float).reshape(-1, 4), axis=0)
            for i in range(len(add)):
                add["Colour0"][i] = tuple(med.astype(vbt["Colour0"].dtype))
            seam = [float(x) for x in med]
        for i in range(len(add)):
            add["Normal"][i] = (0.0, 0.0, 1.0)
    n0 = len(vbt)
    if n0 + len(add) > 65535:
        raise RuntimeError("patio retile: 16-bit index overflow")
    new_tris = np.array([[n0 + remap[int(x)] for x in tri] for tri in ibc[move]], dtype=ibt.dtype)
    gt.vertex_buffer = np.concatenate([vbt, add])
    gt.index_buffer = np.concatenate([ibt.reshape(-1), new_tris.reshape(-1)])
    gc.index_buffer = ibc[~move].reshape(-1).astype(np.asarray(gc.index_buffer).dtype)
    # 0.3.1-l: the walkway vertices ON the old kiosk outline kept the darker baked shade of the kiosk wall foot (R 219..233
    # instead of 255) -> a dark band read as a ledge. They take the patio colour too.
    edge_fixed = 0
    if seam is not None:
        Hh = _hole_ccw()[:, :2]
        nh = len(Hh)
        vbt2 = np.asarray(gt.vertex_buffer)
        P2 = np.array(vbt2["Position"], dtype=float).reshape(-1, 3)[:n0] + ent_pos
        dh = np.min(np.stack([_seg_dist(P2[:, :2], Hh[i], Hh[(i + 1) % nh]) for i in range(nh)]), axis=0)
        nz = np.array(vbt2["Normal"], dtype=float).reshape(-1, 3)[:n0, 2]
        for i in np.where((dh < 0.35) & (nz > 0.9))[0]:
            vbt2["Colour0"][i] = tuple(np.asarray(seam).astype(vbt2["Colour0"].dtype))
            edge_fixed += 1
        gt.vertex_buffer = vbt2
    _TILE_MAP.update(M2=M2, off=off, th=th, colour=seam, ref=int(ibt[ti][0]))
    return {"moved_tris": int(move.sum()), "left_in_apron_geometry": int((~move).sum()), "moved_verts": int(len(used)),
            "uv_per_m": round(sc, 4), "uv_angle_deg": round(math.degrees(th), 1), "ref_tri_area": round(float(area[ti]), 2),
            "ref_tri_dist": round(float(dc[ti]), 1), "tile_geometry_verts": int(n0 + len(add)), "uniform_colour": seam,
            "uv_fit_rms": fit_rms, "outline_verts_recoloured": edge_fixed}


def retexture_billboard(drawable, dds_path, width, height):
    """0.3.1 (owner: the billboard on the shop -> LONG PIG): the embedded texture of the vanilla roof billboard drawable is
    replaced by the owner's own texture (same name, same quad)."""
    import dataclasses as _dc
    from pathlib import Path as _P
    sg = drawable.shader_group
    out = {"textures": [], "mode": None}
    for name in list(sg.embedded_textures):
        tex = sg.embedded_textures[name]
        out["textures"].append([name, int(tex.width), int(tex.height), type(tex).__name__, type(tex.data).__name__])
        raw = _P(dds_path).read_bytes()
        src = tex.data
        cls = type(src)
        out["data_attrs"] = [k for k in dir(src) if not k.startswith("__")][:20]
        newsrc = None
        nm_ = getattr(src, "name", None) or (name + ".dds")
        for mk in (lambda: cls(nm_, raw), lambda: cls(raw), lambda: cls(data=raw)):       # szio _DataSourceBytes(name, data)
            try:
                cand = mk()
                if cand.read_bytes() == raw:
                    newsrc = cand
                    break
            except Exception:
                continue
        if newsrc is None:
            pass
        if newsrc is None:
            raise RuntimeError(f"billboard: cannot build a {cls.__name__} from bytes ({out['data_attrs']})")
        try:
            sg.embedded_textures[name] = _dc.replace(tex, data=newsrc, width=width, height=height)
            out["mode"] = "replace"
        except Exception as e:
            tex.data = newsrc
            tex.width, tex.height = width, height
            out["mode"] = "setattr (%s)" % type(e).__name__
    return out


def cut_kiosk_occluder(mapdata):
    """0.3.0-e (owner: "фулл всё мигает", screenshot: the world behind the kiosk site is not drawn): the block occluder
    still had the kiosk volume -> everything behind the removed kiosk was culled. Remove the occluder triangles / boxes
    of the kiosk (inside KIOSK_BOX in XY)."""
    out = {"model_tris_removed": 0, "models_hit": [], "boxes_removed": 0, "box_attrs": None, "box_near": []}
    for mi, mo in enumerate(mapdata.model_occluders):
        V = np.asarray(mo.vertices, dtype=float).reshape(-1, 3)
        I = np.asarray(mo.indices).reshape(-1, 3).astype(np.int64)
        if not len(I):
            continue
        inb = np.all((V[:, :2] > KIOSK_BOX[0]) & (V[:, :2] < KIOSK_BOX[1]), axis=1)
        kill = inb[I].all(axis=1)
        if kill.any():
            out["models_hit"].append({"model": mi, "tris": int(len(I)), "removed": int(kill.sum()),
                                      "z": [round(float(V[I[kill]][..., 2].min()), 2), round(float(V[I[kill]][..., 2].max()), 2)],
                                      "xy_min": V[I[kill]].reshape(-1, 3)[:, :2].min(0).round(1).tolist(),
                                      "xy_max": V[I[kill]].reshape(-1, 3)[:, :2].max(0).round(1).tolist()})
            out["model_tris_removed"] += int(kill.sum())
            mo.indices = I[~kill].astype(np.uint8)
    boxes = list(mapdata.box_occluders)
    if boxes:
        b0 = boxes[0]
        out["box_attrs"] = {a: repr(getattr(b0, a))[:60] for a in dir(b0) if not a.startswith("_") and not callable(getattr(b0, a))}
        keep = []
        for b in boxes:
            c = None
            for nm in ("center", "position", "centre"):
                if hasattr(b, nm):
                    c = np.array([float(x) for x in getattr(b, nm)][:2])
                    break
            if c is None and hasattr(b, "center_x"):
                c = np.array([float(b.center_x), float(b.center_y)]) * (0.25 if abs(float(b.center_x)) > 3000 else 1.0)
            if c is not None and np.linalg.norm(c - np.array([398.8, -1931.2])) < 40:
                out["box_near"].append(c.round(1).tolist())
            if c is not None and np.all((c > KIOSK_BOX[0]) & (c < KIOSK_BOX[1])):
                out["boxes_removed"] += 1
                continue
            keep.append(b)
        if out["boxes_removed"]:
            mapdata.box_occluders = keep
    return out


def kiosk_left(bound):
    """Primitives still inside the kiosk box above z 24.3 (must be 0 after the edit) + fill primitives found (fan
    triangles sharing the centre vertex, or the 0.52 m fallback boxes)."""
    left = cap = 0
    dbg = []
    c2 = np.array(KIOSK_HOLE_C)
    for c in bound.children:
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        for p in c.geometry_primitives:
            Pw = _prim_corners(p, c.geometry_vertices)
            if in_kiosk_box_world(Pw):
                if Pw[:, 2].max() > 24.3:
                    left += 1
                elif p.primitive_type.name == "TRIANGLE":
                    if in_pad(Pw[:, :2], 1.4).all():
                        dbg.append([round(float(np.linalg.norm(Pw[:, :2] - c2, axis=1).min()), 3), round(float(Pw[:, 2].min()), 3),
                                    round(float(Pw[:, 2].max()), 3)])
                    if np.linalg.norm(Pw[:, :2] - c2, axis=1).min() < 0.20 and in_pad(Pw[:, :2], 1.3).all():   # BVH quantisation
                        cap += 1
                elif p.primitive_type.name == "BOX" and abs((Pw[:, 2].max() - Pw[:, 2].min()) - 0.60) < 0.002 \
                        and abs((Pw[:, 0].max() - Pw[:, 0].min()) - 0.52) < 0.002:
                    cap += 1
    return {"left": left, "cap_boxes": cap, "tris_in_pad": dbg[:40]}


def add_kiosk_pad(drawable, ent_pos, tex=None):
    tex = tex or KIOSK_FILL_TEX
    """Ground fill where the kiosk stood: a triangle fan appended to the PARKING TARMAC geometry of sc1_14_grnd_02 (same
    shader / texture as the lot next to it; vertex attributes copied from the nearest tarmac vertex, UV by the affine
    world->UV mapping of the tarmac around it), every corner at the lot level + 2 cm."""
    sg = drawable.shader_group
    Q, c2 = _pad_poly(KIOSK_FILL_SCALE)
    best = None
    for lod, models in drawable.models.items():
        for m in models:
            for g in m.geometries:
                if _shader_tex(sg.shaders[g.shader_index]) != tex:
                    continue
                pos = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos
                d = np.linalg.norm(pos[:, :2] - c2, axis=1)
                if best is None or (d < 14.0).sum() > best[2]:
                    best = (g, pos, int((d < 14.0).sum()), d)
    if best is None or best[2] < 6:
        raise RuntimeError(f"kiosk fill: no '{tex}' geometry with vertices near the kiosk")
    g, pos, n_near, d = best
    vb = np.asarray(g.vertex_buffer)
    near = d < 14.0
    uv = np.array(vb["TexCoord0"], dtype=float).reshape(-1, 2)
    A = np.c_[pos[near][:, :2], np.ones(near.sum())]
    coef, *_ = np.linalg.lstsq(A, uv[near], rcond=None)
    rms = float(np.sqrt(((A @ coef - uv[near]) ** 2).mean()))
    mode = "fit"
    if rms > 0.02:                                # not one planar mapping: continue the mapping of the nearest big tarmac triangle
        idx = np.asarray(g.index_buffer, dtype=np.int64).reshape(-1, 3)
        T = pos[idx]
        nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        area = np.linalg.norm(nrm, axis=1) / 2
        ok = (area > 0.5) & (np.abs(nrm[:, 2]) > 0.9 * np.linalg.norm(nrm, axis=1))
        dc = np.linalg.norm(T.mean(1)[:, :2] - c2, axis=1)
        dc[~ok] = 1e9
        ti = int(np.argmin(dc))
        coef = np.linalg.solve(np.c_[T[ti][:, :2], np.ones(3)], uv[idx[ti]])
        mode = "nearest triangle %.1f m" % float(dc[ti])
    # 0.3.0-e: exact hole polygon, corners snapped to the nearest existing ground vertex of ANY geometry of this drawable
    allpos = []
    for lod, models in drawable.models.items():
        for m in models:
            for gg in m.geometries:
                allpos.append(np.array(gg.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent_pos)
    allpos = np.concatenate(allpos)
    H = _hole_ccw()
    snapped = 0
    for i in range(len(H)):
        dd = np.linalg.norm(allpos - H[i], axis=1)
        j = int(np.argmin(dd))
        if dd[j] < 0.10:
            H[i] = allpos[j]
            snapped += 1
    cxy = np.array(KIOSK_HOLE_C)
    w = 1.0 / np.maximum(np.linalg.norm(H[:, :2] - cxy, axis=1), 0.1)
    zc = float((H[:, 2] * w).sum() / w.sum())
    n = len(H)
    sk_s, sk_dz = KIOSK_SKIRT
    pts = [(cxy[0], cxy[1], zc)] + [tuple(h) for h in H] \
        + [(cxy[0] + (h[0] - cxy[0]) * sk_s, cxy[1] + (h[1] - cxy[1]) * sk_s, h[2] + sk_dz) for h in H]
    add = np.repeat(vb[0:1], len(pts), axis=0).copy()
    for i, (x, y, z) in enumerate(pts):
        add[i] = vb[int(np.argmin(np.linalg.norm(pos[:, :2] - np.array([x, y]), axis=1)))]   # colours of the lot next to it
        add["Position"][i] = (x - ent_pos[0], y - ent_pos[1], z - ent_pos[2])
        add["Normal"][i] = (0.0, 0.0, 1.0)
        add["TexCoord0"][i] = np.array([x, y, 1.0]) @ coef
    n0 = len(vb)
    tris = []
    for k in range(n):
        a_, b_ = n0 + 1 + k, n0 + 1 + (k + 1) % n
        tris += [n0, a_, b_]                                                       # CCW from above = facing up
        tris += [a_, a_ + n, b_ + n, a_, b_ + n, b_]                               # skirt
    ib = np.asarray(g.index_buffer)
    if n0 + len(pts) > 65535:
        raise RuntimeError("kiosk fill: 16-bit index overflow")
    g.vertex_buffer = np.concatenate([vb, add])
    g.index_buffer = np.concatenate([ib.reshape(-1), np.array(tris, dtype=ib.dtype)])
    return {"geometry_tex": tex, "verts_near": n_near, "uv_fit_rms": round(rms, 4), "uv_mode": mode,
            "uv_per_m": [round(float(np.linalg.norm(coef[0])), 4), round(float(np.linalg.norm(coef[1])), 4)],
            "added_verts": len(pts), "added_tris": len(tris) // 3, "hole_corners": n, "snapped": snapped,
            "centre_z": round(zc, 3)}
