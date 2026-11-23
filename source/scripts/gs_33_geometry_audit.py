# Geometry / portal / collision audit of the LONG PIG building against the GTA V data (read-only).
# usage: <bpyenv python> gs_33_geometry_audit.py <vanilla_xml_dir> <override_xml_dir> <out_json>
#   vanilla_xml_dir : CodeWalker XML of the untouched game files (sc1_14_0.ybn.xml, hi@sc1_14_0.ybn.xml, sc1_14_build2.ydr.xml)
#   override_xml_dir: CodeWalker XML of our override copies (same names) = what the game uses with the resource
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import szio
import gs_overrides as G
import gs_proto_geometry as PG
import gs_30_concept_layout as CL

VAN, OVR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
Z0 = G.FLOOR_Z
NEAR = dict(s=(-6.0, 19.0), t=(-4.5, 14.5), z=(Z0 - 1.5, Z0 + 8.5))


# ------------------------------------------------------------------ collision -> local triangles
def box_tris(P8):
    # P8: corners from G._box_vertices (4) completed to 8 with G._prim_corners convention -> use hull of 8 points
    from itertools import combinations
    c = P8.mean(0)
    tris = []
    # build the 6 faces from the box frame instead (robust)
    return tris


def prim_triangles(p, verts):
    t = p.primitive_type.name
    if t == "TRIANGLE":
        P = np.array([[float(x) for x in verts[i].co] for i in p.vertices])
        return [P]
    if t == "BOX":
        c, axes, half = G._box_frame(p, verts)
        A, B, C = (np.asarray(axes[i]) * half[i] for i in range(3))
        corners = {}
        for sa in (-1, 1):
            for sb in (-1, 1):
                for sc in (-1, 1):
                    corners[(sa, sb, sc)] = c + sa * A + sb * B + sc * C
        faces = []
        for ax in range(3):
            for sgn in (-1, 1):
                quad = []
                for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    k = [0, 0, 0]
                    k[ax] = sgn
                    others = [i for i in range(3) if i != ax]
                    k[others[0]], k[others[1]] = u, v
                    quad.append(corners[tuple(k)])
                faces += [np.array([quad[0], quad[1], quad[2]]), np.array([quad[0], quad[2], quad[3]])]
        return faces
    return []


def load_bound_tris(path, tag):
    b = szio.try_load_asset(path)
    out = []   # (tri_local(3x3), meta)
    other = []
    for ci, c in enumerate(b.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        verts = c.geometry_vertices
        for pi, p in enumerate(c.geometry_primitives):
            tt = p.primitive_type.name
            meta = dict(file=tag, child=ci, prim=pi, type=tt, mat=int(p.material.material_index))
            if tt in ("TRIANGLE", "BOX"):
                for T in prim_triangles(p, verts):
                    L = G.to_local(T)
                    if (L[:, 0].max() < NEAR["s"][0] or L[:, 0].min() > NEAR["s"][1] or L[:, 1].max() < NEAR["t"][0]
                            or L[:, 1].min() > NEAR["t"][1] or L[:, 2].max() < NEAR["z"][0] or L[:, 2].min() > NEAR["z"][1]):
                        continue
                    out.append((L, meta))
            else:
                P = np.array([[float(x) for x in verts[i].co] for i in p.vertices])
                L = G.to_local(P)
                if (NEAR["s"][0] < L[:, 0].mean() < NEAR["s"][1]) and (NEAR["t"][0] < L[:, 1].mean() < NEAR["t"][1]):
                    other.append(dict(meta, center=L.mean(0).round(3).tolist(), radius=float(p.radius or 0)))
    return out, other


def interior_depth(L):
    s, t, z = L[:, 0], L[:, 1], L[:, 2]
    _, dep = G.chamfer(L)
    return np.minimum.reduce([s - PG.XW, t - PG.YS, PG.YN - t, PG.XE - s, PG.CH_IN - dep, z - Z0, (Z0 + 5.72) - z])


# ------------------------------------------------------------------ ray casting (Moller-Trumbore, vectorized over tris)
class Caster:
    def __init__(self, tris):
        T = np.array([t for t, _ in tris]) if tris else np.zeros((0, 3, 3))
        self.v0 = T[:, 0]
        self.e1 = T[:, 1] - T[:, 0]
        self.e2 = T[:, 2] - T[:, 0]
        self.meta = [m for _, m in tris]

    def hit(self, o, d, tmax=40.0):
        o = np.asarray(o, float); d = np.asarray(d, float); d = d / np.linalg.norm(d)
        p = np.cross(d, self.e2)
        det = np.einsum("ij,ij->i", self.e1, p)
        ok = np.abs(det) > 1e-9
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = o - self.v0
        u = np.einsum("ij,ij->i", tv, p) * inv
        q = np.cross(tv, self.e1)
        v = (q @ d) * inv
        tt = np.einsum("ij,ij->i", self.e2, q) * inv
        m = ok & (u >= -1e-7) & (v >= -1e-7) & (u + v <= 1 + 1e-7) & (tt > 1e-4) & (tt < tmax)
        if not m.any():
            return None, None
        i = np.argmin(np.where(m, tt, np.inf))
        return float(tt[i]), self.meta[i]


def scan_wall(caster, name, origins, d, coord, zs):
    rows = []
    for z in zs:
        for o in origins:
            oo = np.array([o[0], o[1], Z0 + z])
            dist, meta = caster.hit(oo, d)
            if dist is None:
                rows.append(dict(z=z, along=float(o[coord]), hit=None))
            else:
                h = oo + dist * np.asarray(d) / np.linalg.norm(d)
                rows.append(dict(z=z, along=float(o[coord]), hit=h.round(4).tolist(), mat=meta["mat"], type=meta["type"], file=meta["file"]))
    return dict(name=name, dir=list(d), rows=rows)


def summarize_wall(scan, axis, expected):
    vals = np.array([r["hit"][axis] for r in scan["rows"] if r["hit"] is not None])
    misses = [(round(r["along"], 2), r["z"]) for r in scan["rows"] if r["hit"] is None]
    if len(vals) == 0:
        return dict(name=scan["name"], hits=0, misses=len(misses))
    dev = vals - expected
    off = [(round(r["along"], 2), r["z"], round(r["hit"][axis] - expected, 3), r["mat"], r["type"], r["file"])
           for r in scan["rows"] if r["hit"] is not None and abs(r["hit"][axis] - expected) > 0.02]
    return dict(name=scan["name"], expected=expected, hits=int(len(vals)), median=float(np.median(vals)),
                p05=float(np.percentile(vals, 5)), p95=float(np.percentile(vals, 95)), min=float(vals.min()), max=float(vals.max()),
                n_off_2cm=len(off), off_samples=off[:40], misses=misses[:60], n_miss=len(misses))


def wall_scans(caster):
    zs = [0.10, 0.40, 0.90, 1.50, 2.20, 2.90, 3.60, 4.40, 5.30]
    sw = [(s, 5.0) for s in np.arange(0.8, 16.01, 0.25)]
    ne = [(s, 5.0) for s in np.arange(-2.7, 16.01, 0.25)]
    se = [(8.0, t) for t in np.arange(-1.1, 11.31, 0.25)]
    nw = [(8.0, t) for t in np.arange(2.6, 11.31, 0.25)]
    out = {}
    out["SW"] = scan_wall(caster, "SW (W1, D2)", sw, (0, -1, 0), 0, zs)
    out["NE"] = scan_wall(caster, "NE", ne, (0, 1, 0), 0, zs)
    out["SE"] = scan_wall(caster, "SE", se, (1, 0, 0), 1, zs)
    out["NW"] = scan_wall(caster, "NW (W2, D3)", nw, (-1, 0, 0), 1, zs)
    # chamfer: rays along CH_OUT from 2 m inside
    rows = []
    for a in np.arange(0.15, 5.11, 0.2):
        s, t = G.chamfer_to_local(a, -2.0)
        for z in zs:
            oo = np.array([s, t, Z0 + z])
            dvec = np.array([G.CH_OUT[0], G.CH_OUT[1], 0.0])
            dist, meta = caster.hit(oo, dvec)
            if dist is None:
                rows.append(dict(z=z, along=float(a), hit=None))
            else:
                h = oo + dist * dvec
                _, dep = G.chamfer(h[None, :2])
                rows.append(dict(z=z, along=float(a), hit=[float(dep[0]), 0, 0], mat=meta["mat"], type=meta["type"], file=meta["file"]))
    out["CH"] = dict(name="chamfer (D1), value = depth along CH_OUT", dir=list(G.CH_OUT), rows=rows)
    return out


def vertical_scans(caster):
    up, down = [], []
    for s in np.arange(-2.5, 16.0, 0.75):
        for t in np.arange(-1.0, 11.3, 0.75):
            if not CL.inside((s, t)):
                continue
            d1, m1 = caster.hit((s, t, Z0 + 1.0), (0, 0, 1))
            up.append(None if d1 is None else Z0 + 1.0 + d1)
            d2, m2 = caster.hit((s, t, Z0 + 1.0), (0, 0, -1), tmax=3.0)
            down.append(None if d2 is None else Z0 + 1.0 - d2)
    u = np.array([x for x in up if x is not None])
    dn = np.array([x for x in down if x is not None])
    return dict(roof_hits=int(len(u)), roof_misses=int(sum(x is None for x in up)),
                roof_min=float(u.min()) if len(u) else None, roof_median=float(np.median(u)) if len(u) else None,
                roof_max=float(u.max()) if len(u) else None,
                floor_hits=int(len(dn)), floor_misses=int(sum(x is None for x in down)),
                floor_values=sorted(set(round(float(x) - Z0, 3) for x in dn))[:20])


# ------------------------------------------------------------------ portals of the built MLO (v0.1.3 source of truth)
def portal_audit():
    res = {}
    room_c = np.array([(PG.ROOM_BB[0][i] + PG.ROOM_BB[1][i]) / 2 for i in range(3)])
    for k, c in PG.portals().items():
        C = np.array(c)
        n = np.array(PG.portal_normal(c))
        center = C.mean(0)
        plan_dev = float(np.abs((C - center) @ n).max())
        out_dot = float(n @ ((center - room_c) / np.linalg.norm(center - room_c)))
        inside_bb = bool(np.all(C >= np.array(PG.ROOM_BB[0]) - 1e-6) and np.all(C <= np.array(PG.ROOM_BB[1]) + 1e-6))
        e = dict(corners=C.round(4).tolist(), normal=n.round(4).tolist(), planarity_m=plan_dev,
                 normal_dot_outward=round(out_dot, 4), points_out=out_dot > 0.5, inside_room_bb=inside_bb)
        if k == "W1":
            e.update(opening=dict(s=PG.W1["s"], z=[round(x, 3) for x in PG.W1["z"]]),
                     cover_margin_m=dict(s0=round(PG.W1["s"][0] - C[:, 0].min(), 4), s1=round(C[:, 0].max() - PG.W1["s"][1], 4),
                                         z0=round(PG.W1["z"][0] - C[:, 2].min(), 4), z1=round(C[:, 2].max() - PG.W1["z"][1], 4)),
                     plane_t=float(C[0, 1]), vanilla_glass_t=-1.464, mlo_glass_t=PG.W1["glass_t"], frame_front_t=-1.505,
                     between_glass_and_frame=bool(-1.505 < C[0, 1] < PG.W1["glass_t"]))
        elif k == "W2":
            e.update(opening=dict(t=PG.W2["t"], z=[round(x, 3) for x in PG.W2["z"]]),
                     cover_margin_m=dict(t0=round(PG.W2["t"][0] - C[:, 1].min(), 4), t1=round(C[:, 1].max() - PG.W2["t"][1], 4),
                                         z0=round(PG.W2["z"][0] - C[:, 2].min(), 4), z1=round(C[:, 2].max() - PG.W2["z"][1], 4)),
                     plane_s=float(C[0, 0]), vanilla_glass_s=(-3.084, -3.078), mlo_glass_s=PG.W2["glass_s"], frame_front_s=-3.12,
                     between_glass_and_frame=bool(-3.12 < C[0, 0] < PG.W2["glass_s"]))
        else:
            a, dep = G.chamfer(C[:, :2])
            e.update(opening=dict(a=PG.D1["a"], z=[0.0, round(PG.D1["z"][1], 3)]),
                     cover_margin_m=dict(a0=round(PG.D1["a"][0] - float(a.min()), 4), a1=round(float(a.max()) - PG.D1["a"][1], 4),
                                         z0=round(0.0 - C[:, 2].min(), 4), z1=round(C[:, 2].max() - PG.D1["z"][1], 4)),
                     plane_dep=float(dep.mean()), leaf_dep=PG.D1["leaf_dep"], reveal_dep=PG.D1["reveal_to"],
                     outside_leaves=bool(PG.D1["reveal_to"] < dep.mean() < PG.D1["leaf_dep"]) is False and bool(dep.mean() > PG.D1["leaf_dep"]))
        res[k] = e
    return res


# ------------------------------------------------------------------ concept layout vs measured shell
def layout_audit(measured):
    XW, YS, YN, XE = measured["XW"], measured["YS"], measured["YN"], measured["XE"]
    rooms = []
    half = CL.WALL_T / 2
    for name, code, poly, _ in CL.ZONES:
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        rooms.append(dict(code=code, name=name, area_m2=round(CL.poly_area(poly), 2),
                          bbox_s=(round(min(xs), 3), round(max(xs), 3)), bbox_t=(round(min(ys), 3), round(max(ys), 3)),
                          width_s=round(max(xs) - min(xs), 3), depth_t=round(max(ys) - min(ys), 3)))
    # door clear widths and corridor
    doors = []
    for pname, p0, p1, gaps in CL.PARTITIONS:
        for g0, g1, kind in gaps:
            doors.append(dict(partition=pname, kind=kind, clear_m=round(g1 - g0, 3)))
    corridor_clear = round((8.12 - half) - (7.0 + half), 3)
    return dict(rooms=rooms, doors=doors, corridor_clear_m=corridor_clear,
                outer_check=dict(XW=XW, YS=YS, YN=YN, XE=XE, layout_poly=CL.FLOOR_POLY))


def main():
    van_tris, van_other = [], []
    for f in ("sc1_14_0.ybn.xml", "hi@sc1_14_0.ybn.xml"):
        t, o = load_bound_tris(os.path.join(VAN, f), "van:" + f)
        van_tris += t; van_other += o
    ovr_tris, ovr_other = [], []
    for f in ("sc1_14_0.ybn.xml", "hi@sc1_14_0.ybn.xml"):
        t, o = load_bound_tris(os.path.join(OVR, f), "ovr:" + f)
        ovr_tris += t; ovr_other += o

    # vanilla prims that intrude into the interior volume (> 5 cm)
    intr = {}
    for L, m in van_tris:
        d = interior_depth(L)
        if d.max() > 0.05:
            key = (m["file"], m["child"], m["prim"])
            intr.setdefault(key, dict(m, max_depth=0.0, bbox=None))
            e = intr[key]
            e["max_depth"] = max(e["max_depth"], float(d.max()))
            bb = np.vstack([L.min(0), L.max(0)])
            e["bbox"] = bb if e["bbox"] is None else np.vstack([np.minimum(e["bbox"][0], bb[0]), np.maximum(e["bbox"][1], bb[1])])
    intr_list = [dict(v, bbox=[[round(x, 3) for x in v["bbox"][0]], [round(x, 3) for x in v["bbox"][1]]]) for v in intr.values()]
    intr_list.sort(key=lambda e: -e["max_depth"])
    ovr_intr = set()
    for L, m in ovr_tris:
        if interior_depth(L).max() > 0.05:
            ovr_intr.add((m["file"], m["child"], m["prim"], m["type"], m["mat"]))

    # cast against the vanilla collision WITHOUT the intruding blockers = the building envelope
    env = Caster([(L, m) for L, m in van_tris if (m["file"], m["child"], m["prim"]) not in intr])
    scans = wall_scans(env)
    walls = dict(SW=summarize_wall(scans["SW"], 1, PG.YS), NE=summarize_wall(scans["NE"], 1, PG.YN),
                 SE=summarize_wall(scans["SE"], 0, PG.XE), NW=summarize_wall(scans["NW"], 0, PG.XW),
                 CH=summarize_wall(scans["CH"], 0, PG.CH_IN))
    vert = vertical_scans(env)
    # the same scan against the override collision (what the game uses with the resource) at walk heights
    ovr = Caster(ovr_tris)
    walk = wall_scans(ovr)
    walk_sum = dict(SW=summarize_wall(walk["SW"], 1, PG.YS), NE=summarize_wall(walk["NE"], 1, PG.YN),
                    SE=summarize_wall(walk["SE"], 0, PG.XE), NW=summarize_wall(walk["NW"], 0, PG.XW),
                    CH=summarize_wall(walk["CH"], 0, PG.CH_IN))
    # walk-in test through D1 (override): rays from 3 m outside to 3 m inside along -CH_OUT at body heights
    d1_rays = []
    for a in np.arange(PG.D1["a"][0] + 0.15, PG.D1["a"][1] - 0.149, 0.2):
        for z in (0.05, 0.3, 0.9, 1.5, 1.9):
            s, t = G.chamfer_to_local(a, 3.0)
            o = np.array([s, t, Z0 + z])
            d = -np.array([G.CH_OUT[0], G.CH_OUT[1], 0.0])
            dist, meta = ovr.hit(o, d, tmax=6.0)
            d1_rays.append(dict(a=round(float(a), 2), z=z, blocked_at=None if dist is None else round(3.0 - dist, 3),
                                by=None if meta is None else (meta["file"], meta["type"], meta["mat"])))

    measured = dict(YS=walls["SW"]["median"], YN=walls["NE"]["median"], XE=walls["SE"]["median"], XW=walls["NW"]["median"])
    res = dict(
        frame=dict(origin=G.O2.tolist(), yaw_deg=G.YAW_DEG, floor_z=Z0),
        envelope_walls=walls, roof_floor=vert,
        vanilla_intruders=intr_list, override_intruders=sorted([list(k) for k in ovr_intr]),
        non_mesh_prims_near=van_other[:50],
        override_walls=walk_sum, d1_walk_in=d1_rays,
        portals=portal_audit(), layout=layout_audit(measured),
        shell_constants=dict(XW=PG.XW, YS=PG.YS, YN=PG.YN, XE=PG.XE, CH_IN=PG.CH_IN, FLOOR=PG.FLOOR, CEIL=PG.CEIL,
                             ROOM_BB=PG.ROOM_BB, FLOOR_POLY=PG.FLOOR_POLY),
    )
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    # console summary
    for k, w in walls.items():
        print(f"wall {k}: median {w.get('median')} p05 {w.get('p05')} p95 {w.get('p95')} off>2cm {w.get('n_off_2cm')} misses {w.get('n_miss')}")
    print("roof/floor", {k: v for k, v in vert.items() if k != 'floor_values'}, vert["floor_values"])
    print("vanilla intruders:", len(intr_list), [(e["file"].split(':')[1], e["prim"], e["type"], e["mat"], round(e["max_depth"], 2)) for e in intr_list[:12]])
    print("override intruders:", len(ovr_intr))
    for k, w in walk_sum.items():
        print(f"override wall {k}: median {w.get('median')} off>2cm {w.get('n_off_2cm')} misses {w.get('n_miss')}")
    blocked = [r for r in d1_rays if r["blocked_at"] is not None and r["blocked_at"] < 2.9]
    print("D1 walk-in rays", len(d1_rays), "blocked before inside:", len(blocked), blocked[:6])
    for k, p in res["portals"].items():
        print("portal", k, {x: p[x] for x in p if x not in ("corners",)})
    print("layout corridor", res["layout"]["corridor_clear_m"], "doors", [(d["partition"][:14], d["clear_m"]) for d in res["layout"]["doors"]])


main()
