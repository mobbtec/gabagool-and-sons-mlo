# LONG PIG — read-only scan of the vanilla map data around the shop (v0.1.6 bug hunt).
# Blender 5.1 console on the PC (Sollumz 2.9 / PyMateria):
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_26_area_scan.py", encoding="utf-8").read())
# Finds, for the shop volume (MLO-local s -3.3..16.6, t -1.7..11.9):
#   1. box / model occluders (they cull the world seen through W1 -> room -> W2 from the street)
#   2. ymap grass instances inside the footprint (weeds through the floor)
#   3. drawables of nearby entities with geometry between the vanilla ground and 0.5 m inside the footprint
#      (decals / sidewalk bleeding through the MLO floor)
#   4. ground polygons of the mover collision inside the footprint with a procedural id (procedural weeds)
# Output: docs/_raw/area_scan_v016.json. Nothing is written into the game files.
import os, sys, json, time, traceback, math
from pathlib import Path
import numpy as np

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "docs" / "_raw" / "area_scan_v016.json"
sys.path.insert(0, str(ROOT / "source" / "scripts"))
import importlib
import gs_overrides as G
importlib.reload(G)
import szio
from szio.vfs import VPath

FZ = G.FLOOR_Z
S_RANGE, T_RANGE = (-3.3, 16.6), (-1.7, 11.9)
R = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "ymaps_checked": 0, "occluders": [], "grass": [], "entities": [],
     "drawables": [], "mover_proc": {}, "errors": []}


def note(m):
    print("[gs_area]", m, flush=True)


def in_room(L, margin=0.0):
    s, t = L[..., 0], L[..., 1]
    a, dep = G.chamfer(L[..., :2])
    return (s > -2.90 + margin) & (s < 16.15 - margin) & (t > -1.23 + margin) & (t < 11.42 - margin) & (dep < -0.46 - margin)


corners = np.array([G.to_world(s, t, FZ) for s in S_RANGE for t in T_RANGE])
WMIN = corners.min(0) - [0, 0, 2.0]
WMAX = corners.max(0) + [0, 0, 8.0]
note(f"shop world AABB {WMIN.round(2)} .. {WMAX.round(2)}")


def aabb_hit(mn, mx):
    return all(mx[i] >= WMIN[i] and mn[i] <= WMAX[i] for i in range(3))


# ---------------------------------------------------------------- collect archives
archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
for base in (GTA / "update" / "x64" / "dlcpacks", GTA / "x64" / "dlcpacks"):
    if base.is_dir():
        archives += sorted(base.glob("*/dlc.rpf"))
ymaps, ydrs = [], {}
for r in archives:
    if not r.exists():
        continue
    try:
        for p in VPath(str(r)).rglob("*"):
            nm = p.name.lower()
            if nm.endswith(".ymap") and ("sc1" in nm or "occl" in nm and "scentral" in p.as_posix().lower()):
                ymaps.append(p)
            elif nm.endswith(".ydr") and nm.startswith(("sc1_", "hei_sc1_", "lr_sc1_")):
                ydrs.setdefault(nm[:-4], p)            # base game first, DLC copies kept only if new
    except Exception:
        R["errors"].append(f"scan {r}: " + traceback.format_exc()[-300:])
note(f"{len(archives)} archives, {len(ymaps)} candidate ymaps, {len(ydrs)} sc1 drawables")

# ---------------------------------------------------------------- ymaps
near = {}
for p in ymaps:
    try:
        m = szio.try_load_asset(p)
        if m is None or not hasattr(m, "entities"):
            continue
        R["ymaps_checked"] += 1
        sm, sx = np.array(m.streaming_extents[0]), np.array(m.streaming_extents[1])
        em, ex = np.array(m.entities_extents[0]), np.array(m.entities_extents[1])
        if not (aabb_hit(sm, sx) or aabb_hit(em, ex)):
            continue
        for i, b in enumerate(m.box_occluders):
            c = np.array(b.center); sz = np.array(b.size)
            r_ = 0.5 * math.hypot(sz[0], sz[1])
            if aabb_hit(c - [r_, r_, sz[2] / 2], c + [r_, r_, sz[2] / 2]):
                L = G.to_local(c[None])[0]
                R["occluders"].append({"ymap": p.as_posix(), "kind": "box", "index": i, "center": c.round(2).tolist(),
                                       "size": sz.round(2).tolist(), "cos_sin": [round(x, 4) for x in b.cos_sin_z],
                                       "center_local": L.round(2).tolist(), "total_box": len(m.box_occluders),
                                       "total_model": len(m.model_occluders), "entities": len(m.entities)})
        for i, mo in enumerate(m.model_occluders):
            V = np.asarray(mo.vertices, dtype=float).reshape(-1, 3)
            if len(V) and aabb_hit(V.min(0), V.max(0)):
                L = G.to_local(V)
                R["occluders"].append({"ymap": p.as_posix(), "kind": "model", "index": i, "verts": int(len(V)),
                                       "tris": int(len(mo.indices) // 3), "min": V.min(0).round(2).tolist(),
                                       "max": V.max(0).round(2).tolist(), "verts_inside_shop": int(in_room(L).sum()),
                                       "flags": str(mo.flags), "total_box": len(m.box_occluders),
                                       "total_model": len(m.model_occluders), "entities": len(m.entities)})
        for i, g in enumerate(m.grass_instance_lists):
            gm, gx = np.array(g.extents[0]), np.array(g.extents[1])
            if not aabb_hit(gm, gx):
                continue
            P = g.unpack_instances()["Position"]
            L = G.to_local(P)
            ins = in_room(L)
            if ins.any():
                R["grass"].append({"ymap": p.as_posix(), "index": i, "archetype": g.archetype_name, "instances": int(len(P)),
                                   "inside_shop": int(ins.sum()), "inside_local_min": L[ins].min(0).round(2).tolist(),
                                   "inside_local_max": L[ins].max(0).round(2).tolist()})
        for e in m.entities:
            pos = np.array(e.position)
            if np.linalg.norm(pos[:2] - G.O2) < 45.0:
                q = e.rotation
                near.setdefault(e.archetype_name.lower(), []).append(
                    {"ymap": p.as_posix(), "pos": pos.round(3).tolist(), "rot": [round(float(x), 4) for x in (q.w, q.x, q.y, q.z)],
                     "lod": e.lod_level.name, "lod_dist": e.lod_dist})
    except Exception:
        R["errors"].append(f"ymap {p.as_posix()}: " + traceback.format_exc()[-300:])
R["entities"] = [{"archetype": k, "placements": v} for k, v in sorted(near.items())]
note(f"ymaps checked {R['ymaps_checked']}, occluders near {len(R['occluders'])}, grass lists inside {len(R['grass'])}, "
     f"nearby archetypes {len(near)}")

# ---------------------------------------------------------------- drawables with geometry just above the ground inside
for name, places in sorted(near.items()):
    if name not in ydrs:
        continue
    try:
        a = szio.try_load_asset(ydrs[name])
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        if not getattr(d, "models", None):
            continue
        lod = min(d.models.keys(), key=lambda k: int(k))
        sh_names = [s.name for s in d.shader_group.shaders] if d.shader_group else []
        for pl in places:
            if pl["lod"] not in ("HD", "ORPHANHD"):
                continue
            w, x, y, z = pl["rot"]
            from mathutils import Quaternion
            qm = np.array(Quaternion((w, -x, -y, -z)).to_matrix())        # ymap entities store the inverse rotation
            hits = []
            for mi, mdl in enumerate(d.models[lod]):
                for gi, g in enumerate(mdl.geometries):
                    P = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3)
                    W = P @ qm.T + np.array(pl["pos"])
                    L = G.to_local(W)
                    zl = L[:, 2] - FZ
                    ins = in_room(L, 0.03) & (zl > -0.30) & (zl < 0.50)
                    if ins.any():
                        si = getattr(g, "shader_index", None)
                        hits.append({"model": mi, "geom": gi, "shader": sh_names[si] if isinstance(si, int) and si < len(sh_names) else si,
                                     "verts_inside": int(ins.sum()), "z_local_min": round(float(zl[ins].min()), 3),
                                     "z_local_max": round(float(zl[ins].max()), 3),
                                     "s_range": [round(float(L[ins, 0].min()), 2), round(float(L[ins, 0].max()), 2)],
                                     "t_range": [round(float(L[ins, 1].min()), 2), round(float(L[ins, 1].max()), 2)]})
            if hits:
                R["drawables"].append({"archetype": name, "path": ydrs[name].as_posix(), "placement": pl, "hits": hits})
    except Exception:
        R["errors"].append(f"ydr {name}: " + traceback.format_exc()[-300:])
note(f"drawables with geometry near the floor inside: {[d_['archetype'] for d_ in R['drawables']]}")

# ---------------------------------------------------------------- mover collision: procedural ids under the floor
try:
    b = szio.try_load_asset(ROOT / "reference_vanilla" / "sc1_14" / "sc1_14_0.ybn")
    stats = {}
    for ci, c in enumerate(b.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        V = np.array([tuple(v.position) for v in c.geometry_vertices], dtype=float)
        for pi, pr in enumerate(c.geometry_primitives):
            if pr.primitive_type.name != "TRIANGLE":
                continue
            T = V[list(pr.vertices)]
            L = G.to_local(T)
            cen = L.mean(0)
            if in_room(cen[None], 0.0)[0] and abs(cen[2] - FZ) < 0.4:
                key = f"mat{pr.material.material_index}_proc{pr.material.procedural_id}"
                stats.setdefault(key, {"tris": 0, "z_local": []})
                stats[key]["tris"] += 1
                stats[key]["z_local"].append(round(float(cen[2] - FZ), 3))
    for k in stats:
        z = stats[k].pop("z_local")
        stats[k]["z_local_min_max"] = [min(z), max(z)]
    R["mover_proc"] = stats
except Exception:
    R["errors"].append("mover: " + traceback.format_exc()[-400:])
note(f"mover ground under the floor: {R['mover_proc']}")

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(R, fh, indent=1, default=str)
print("GS_AREA_DONE occl=%d grass=%d drawables=%d errors=%d -> %s" % (len(R["occluders"]), len(R["grass"]), len(R["drawables"]),
                                                                     len(R["errors"]), OUT))
