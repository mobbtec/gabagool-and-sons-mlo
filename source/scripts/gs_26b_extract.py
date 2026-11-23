# LONG PIG — v0.1.6: copy the vanilla files that need a server override out of the game archives (read-only access
# to the RPFs) and dump their geometry near the shop for analysis.
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_26b_extract.py", encoding="utf-8").read())
# Writes: reference_vanilla/sc1_14/<file> (raw resources, internal reference only, never published)
#         docs/_raw/area_extract_v016.json
import os, sys, json, time, hashlib, traceback
from pathlib import Path
import numpy as np

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
REF = ROOT / "reference_vanilla" / "sc1_14"
OUT = ROOT / "docs" / "_raw" / "area_extract_v016.json"
sys.path.insert(0, str(ROOT / "source" / "scripts"))
import importlib
import gs_overrides as G
importlib.reload(G)
import szio
from szio.vfs import VPath

WANT = {"sc1_occl_01.ymap", "hei_sc1_occl_01.ymap", "lr_sc1_occl_01.ymap", "sc1_14_grnd_02.ydr"}
FZ = G.FLOOR_Z
R = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "copies": {}, "extracted": {}, "occluders": {}, "grnd": [],
     "mover_proc": {}, "errors": []}


def note(m):
    print("[gs_extract]", m, flush=True)


def prio(path):
    p = path.lower()
    if "/update/update.rpf" in p:
        return 3
    if "dlcpacks" in p:
        return 2 if "patch" in p else 1
    return 0


def in_room(L, margin=0.0):
    a, dep = G.chamfer(L[..., :2])
    return (L[..., 0] > -2.90 + margin) & (L[..., 0] < 16.15 - margin) & (L[..., 1] > -1.23 + margin) & \
           (L[..., 1] < 11.42 - margin) & (dep < -0.46 - margin)


archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
for base in (GTA / "update" / "x64" / "dlcpacks", GTA / "x64" / "dlcpacks"):
    if base.is_dir():
        archives += sorted(base.glob("*/dlc.rpf"))
for r in archives:
    if not r.exists():
        continue
    try:
        for p in VPath(str(r)).rglob("*"):
            nm = p.name.lower()
            if nm in WANT:
                b = p.read_bytes()
                R["copies"].setdefault(nm, []).append({"path": p.as_posix(), "bytes": len(b), "sha1": hashlib.sha1(b).hexdigest(),
                                                      "prio": prio(p.as_posix())})
    except Exception:
        R["errors"].append(f"scan {r}: " + traceback.format_exc()[-300:])
note({k: [(c["path"].split("/")[-3:], c["sha1"][:8]) for c in v] for k, v in R["copies"].items()})

REF.mkdir(parents=True, exist_ok=True)
for nm, cands in R["copies"].items():
    best = max(cands, key=lambda c: (c["prio"], c["path"]))
    data = VPath(best["path"]).read_bytes()
    (REF / nm).write_bytes(data)
    R["extracted"][nm] = {"from": best["path"], "sha1": hashlib.sha1(data).hexdigest(), "bytes": len(data),
                          "distinct_versions": sorted({c["sha1"] for c in cands})}

# occluders: full dump of every model occluder that reaches the shop area + box occluders within 60 m
for nm in ("sc1_occl_01.ymap", "hei_sc1_occl_01.ymap", "lr_sc1_occl_01.ymap"):
    try:
        m = szio.try_load_asset(REF / nm)
        rec = {"boxes": [], "models": [], "n_box": len(m.box_occluders), "n_model": len(m.model_occluders), "n_entities": len(m.entities)}
        for i, b in enumerate(m.box_occluders):
            c = np.array(b.center)
            if np.linalg.norm(c[:2] - G.O2) < 60:
                rec["boxes"].append({"index": i, "center": c.tolist(), "size": list(b.size), "cos_sin": list(b.cos_sin_z)})
        for i, mo in enumerate(m.model_occluders):
            V = np.asarray(mo.vertices, dtype=float).reshape(-1, 3)
            if len(V) and np.linalg.norm(V[:, :2].mean(0) - G.O2) < 150:
                rec["models"].append({"index": i, "flags": str(mo.flags), "vertices": V.round(3).tolist(),
                                      "indices": np.asarray(mo.indices).astype(int).tolist()})
        R["occluders"][nm] = rec
    except Exception:
        R["errors"].append(f"occl {nm}: " + traceback.format_exc()[-400:])

# ground drawable triangles near the shop
try:
    a = szio.try_load_asset(REF / "sc1_14_grnd_02.ydr")
    d = a
    pos = np.array([441.1499938964844, -1892.41796875, 24.780000686645508])          # entity in sc1_14_strm_0, rot identity
    sh = [s.name for s in d.shader_group.shaders] if d.shader_group else []
    shf = [s.preset_filename for s in d.shader_group.shaders] if d.shader_group else []
    lod = min(d.models.keys(), key=lambda k: int(k))
    for mi, mdl in enumerate(d.models[lod]):
        for gi, g in enumerate(mdl.geometries):
            P = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + pos
            I = np.asarray(g.index_buffer).astype(int).reshape(-1, 3)
            L = G.to_local(P)
            near = (L[:, 0] > -6) & (L[:, 0] < 20) & (L[:, 1] > -5) & (L[:, 1] < 15)
            for ti, tri in enumerate(I):
                if near[tri].any():
                    R["grnd"].append({"geom": gi, "tri": ti, "shader": shf[g.shader_index] if g.shader_index < len(shf) else None,
                                      "v": (L[tri] - [0, 0, FZ]).round(4).tolist()})
    R["grnd_shaders"] = shf
except Exception:
    R["errors"].append("grnd: " + traceback.format_exc()[-400:])

# mover collision: ground triangles under the floor with a procedural id (weeds)
try:
    b = szio.try_load_asset(ROOT / "reference_vanilla" / "sc1_14" / "sc1_14_0.ybn")
    stats = {}
    for ci, c in enumerate(b.children):
        if c is None or not hasattr(c, "geometry_primitives"):
            continue
        V = np.array([[float(x) for x in v.co] for v in c.geometry_vertices], dtype=float)
        for pi, pr in enumerate(c.geometry_primitives):
            if pr.primitive_type.name != "TRIANGLE":
                continue
            L = G.to_local(V[list(pr.vertices)])
            cen = L.mean(0)
            if abs(cen[2] - FZ) < 0.5 and (in_room(L, 0.0).any() or in_room(cen[None], 0.0)[0]):
                key = f"mat{pr.material.material_index}_proc{pr.material.procedural_id}"
                st = stats.setdefault(key, {"tris": 0, "z": [], "s": [], "t": []})
                st["tris"] += 1
                st["z"].append(float(cen[2] - FZ)); st["s"].append(float(cen[0])); st["t"].append(float(cen[1]))
    for k, st in stats.items():
        for ax in ("z", "s", "t"):
            st[ax] = [round(min(st[ax]), 3), round(max(st[ax]), 3)]
    R["mover_proc"] = stats
except Exception:
    R["errors"].append("mover: " + traceback.format_exc()[-400:])

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(R, fh, default=str)
print("GS_EXTRACT_DONE copies=%s grnd_tris=%d mover=%s errors=%d" % ({k: len(v) for k, v in R["copies"].items()},
                                                                    len(R["grnd"]), list(R["mover_proc"]), len(R["errors"])))
