# LONG PIG v0.3.0 street — READ-ONLY audit for removing the taco kiosk (revision).
# Blender console:  exec(open(R+'/source/scripts/gs_48_street_audit.py', encoding='utf-8').read())   (GS_ROOT set)
# Reads the local reference copies (reference_vanilla/sc1_14) and copies the LOD drawables of the block next to them
# (local analysis copies / source for the owner's minimal override, never shipped unchanged). Nothing is written into the game.
import os, sys, json, traceback
from pathlib import Path
import numpy as np
ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
sys.path.insert(0, str(ROOT / "source" / "scripts"))
import importlib, szio
from szio.vfs import VPath
import gs_overrides as G
importlib.reload(G)
REF = ROOT / "reference_vanilla" / "sc1_14"
OUT = ROOT / "docs" / "_raw" / "street_audit_v030.json"
KB = (np.array([384.5, -1946.0]), np.array([407.5, -1922.5]))          # kiosk + signs, world XY
HOLE_C = np.array([399.0, -1932.0])
A = {"errors": [], "lod_files": [], "bounds": {}, "grnd": {}, "lods": {}}


def inbox(W):
    W = np.asarray(W, dtype=float).reshape(-1, 3)
    return bool(np.all((W[:, :2] > KB[0]) & (W[:, :2] < KB[1])))


try:
    base = VPath(str(GTA / "x64k.rpf")) / "levels" / "gta5" / "_citye" / "scentral_01"
    for p in base.rglob("*"):
        nm = p.name.lower()
        if nm.startswith("sc1_14") and ("lod" in nm) and nm.endswith((".ydr", ".ytd")):
            A["lod_files"].append(p.as_posix()[-70:])
            if nm.endswith(".ydr") and not (REF / nm).exists():
                (REF / nm).write_bytes(p.read_bytes())
except Exception:
    A["errors"].append("lod scan: " + traceback.format_exc()[-400:])

for fn in ("sc1_14_0.ybn", "hi@sc1_14_0.ybn"):
    try:
        b = szio.try_load_asset(REF / fn)
        rep = {"children": 0, "in_box": [], "ground_near_hole": []}
        for ci, c in enumerate(b.children):
            if c is None or not hasattr(c, "geometry_primitives"):
                continue
            rep["children"] += 1
            V = c.geometry_vertices
            agg = {}
            for pi, p in enumerate(c.geometry_primitives):
                P = G._prim_corners(p, V)
                t = p.primitive_type.name
                if inbox(P):
                    k = (t, int(p.material.material_index))
                    a = agg.setdefault(k, [0, 1e9, -1e9])
                    a[0] += 1; a[1] = min(a[1], float(P[:, 2].min())); a[2] = max(a[2], float(P[:, 2].max()))
                if P[:, 2].max() < 24.3 and np.linalg.norm(P[:, :2].mean(0) - HOLE_C) < 4.0:
                    rep["ground_near_hole"].append([ci, pi, t, int(p.material.material_index), np.round(P.mean(0), 2).tolist(), len(P)])
            if agg:
                rep["in_box"].append({"child": ci, "prims": len(c.geometry_primitives),
                                      "by_type_mat": {f"{k[0]}:{k[1]}": [v[0], round(v[1], 2), round(v[2], 2)] for k, v in agg.items()}})
        A["bounds"][fn] = rep
    except Exception:
        A["errors"].append(fn + ": " + traceback.format_exc()[-500:])

try:
    gd = szio.try_load_asset(REF / "sc1_14_grnd_02.ydr")
    ENT = np.array([441.15, -1892.42, 24.78])
    geos = []
    for lod, models in gd.models.items():
        for mi, m in enumerate(models):
            for gi, g in enumerate(m.geometries):
                vb = g.vertex_buffer
                pos = np.array(vb["Position"], dtype=float).reshape(-1, 3) + ENT
                idx = np.array(g.index_buffer, dtype=np.int64).reshape(-1, 3)
                c = pos[idx].mean(1)
                d = np.linalg.norm(c[:, :2] - HOLE_C, axis=1)
                sh = gd.shader_group.shaders[g.shader_index]
                near = d < 9.0
                geos.append({"lod": int(lod), "gi": gi, "shader": sh.name, "tex": G._shader_tex(sh), "tris": int(len(idx)), "near": int(near.sum()),
                             "z_near": [round(float(c[near][:, 2].min()), 2), round(float(c[near][:, 2].max()), 2)] if near.any() else None,
                             "dtype": str(getattr(vb, "dtype", type(vb))), "ib_dtype": str(np.asarray(g.index_buffer).dtype), "verts": int(len(pos))})
    A["grnd"] = geos
except Exception:
    A["errors"].append("grnd: " + traceback.format_exc()[-500:])

for fn, ent in (("sc1_14_build2_lod.ydr", (423.12, -1910.35, 32.35)), ("sc1_14_slod1.ydr", (441.15, -1894.14, 32.76)),
                ("sc1_14_grnd_02_lod.ydr", (441.10, -1894.21, 24.76)), ("sc1_14_sc1_emissive_sc1_14b_lod.ydr", (423.12, -1910.35, 32.35))):
    try:
        d = szio.try_load_asset(REF / fn)
        n = tot = 0
        zz = []
        for lod, models in d.models.items():
            for m in models:
                for g in m.geometries:
                    pos = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + np.array(ent)
                    for tri in np.array(g.index_buffer, dtype=np.int64).reshape(-1, 3):
                        tot += 1
                        if inbox(pos[tri]):
                            n += 1; zz.append(float(pos[tri][:, 2].max()))
        A["lods"][fn] = {"tris": tot, "in_box": n, "zmax": round(max(zz), 2) if zz else None, "zmin": round(min(zz), 2) if zz else None}
    except Exception:
        A["errors"].append(fn + ": " + traceback.format_exc()[-300:])

OUT.write_text(json.dumps(A, indent=1), encoding="utf-8")
print("GS_STREET_AUDIT_DONE errors=%d lods=%s -> %s" % (len(A["errors"]), A["lods"], OUT))
