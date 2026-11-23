# LONG PIG v0.3.0 FIX PASS — READ-ONLY scan of the vanilla map around the small blue kiosk (BB.Q Beef Chicken) and the black
# billboard SW of the shop (owner brief LONG_PIG_EXTERIOR_INTERIOR_FIX_PASS, items 3-4). Nothing is written into the game.
# Blender 5.1 console on the PC (Sollumz 2.9 / PyMateria):
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_47_kiosk_scan.py", encoding="utf-8").read())
# Output:
#   docs/_raw/kiosk_scan_v030.json                every entity / drawable / bound / grass list / occluder touching the area
#   reference_vanilla/kiosk_xml/<name>.<ext>.xml  CodeWalker XML of the drawables / bounds that have geometry in the area
#                                                 (local analysis copies, never shipped)
import os, sys, json, time, traceback, math
from pathlib import Path
import numpy as np

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "docs" / "_raw" / "kiosk_scan_v030.json"
XML = ROOT / "reference_vanilla" / "kiosk_xml"
XML.mkdir(parents=True, exist_ok=True)
import szio
from szio.vfs import VPath
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion

KIOSK_C = np.array([399.0, -1931.5])
AMIN = np.array([386.0, -1950.0, 15.0])         # kiosk + billboard + the lot up to the shop facade
AMAX = np.array([420.0, -1908.0, 48.0])
R = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "area_min": AMIN.tolist(), "area_max": AMAX.tolist(), "ymaps": [],
     "entities": [], "drawables": [], "bounds": [], "grass": [], "occluders": [], "exported": [], "errors": []}
CW = [AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)]
EXTRA = {"prop_billboard_05", "prop_dumpster_01a", "prop_roofvent_16a", "prop_table_03b", "prop_table_03b_chr", "prop_parasol_04",
         "prop_bollard_02a"}


def note(m):
    print("[gs_kiosk]", m, flush=True)


def hit(mn, mx):
    return all(mx[i] >= AMIN[i] and mn[i] <= AMAX[i] for i in range(3))


def export(asset, name, ext):
    try:
        szio.save_asset(asset, CW, XML, name)
        R["exported"].append(f"{name}.{ext}.xml")
    except Exception:
        R["errors"].append(f"export {name}: " + traceback.format_exc()[-300:])


# ---------------------------------------------------------------- archives -> ymaps / ydrs / yfts / ybns
archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
for base in (GTA / "update" / "x64" / "dlcpacks", GTA / "x64" / "dlcpacks"):
    if base.is_dir():
        archives += sorted(base.glob("*/dlc.rpf"))
ymaps, models, ybns = [], {}, []
for r in archives:
    if not r.exists():
        continue
    try:
        for p in VPath(str(r)).rglob("*"):
            nm = p.name.lower()
            pp = p.as_posix().lower()
            if nm.endswith(".ymap") and ("sc1" in nm) and "scentral" in pp:
                ymaps.append(p)
            elif nm.endswith((".ydr", ".yft")):
                stem = nm[:-4]
                if stem.startswith(("sc1_", "hei_sc1_", "lr_sc1_")) or stem in EXTRA:
                    models.setdefault(stem, p)                 # base game first
            elif nm.endswith(".ybn") and ("sc1_" in nm) and "scentral" in pp:
                ybns.append(p)
    except Exception:
        R["errors"].append(f"scan {r}: " + traceback.format_exc()[-300:])
note(f"{len(archives)} archives, {len(ymaps)} sc1 ymaps, {len(models)} models, {len(ybns)} sc1 bounds")

# ---------------------------------------------------------------- ymaps: entities near the kiosk / lot, occluders, grass
near = {}
SEEN = {}
for p in ymaps:
    try:
        m = szio.try_load_asset(p)
        if m is None or not hasattr(m, "entities"):
            continue
        sm, sx = np.array(m.streaming_extents[0]), np.array(m.streaming_extents[1])
        em, ex = np.array(m.entities_extents[0]), np.array(m.entities_extents[1])
        if not (hit(sm, sx) or hit(em, ex)):
            continue
        R["ymaps"].append({"ymap": p.as_posix(), "parent": str(getattr(m, "parent", "")), "entities": len(m.entities),
                           "entities_extents": [em.round(2).tolist(), ex.round(2).tolist()]})
        for i, e in enumerate(m.entities):
            pos = np.array(e.position)
            if np.linalg.norm(pos[:2] - KIOSK_C) < 140.0:
                q = e.rotation
                near.setdefault(e.archetype_name.lower(), []).append(
                    {"ymap": p.as_posix(), "index": i, "pos": pos.round(3).tolist(),
                     "rot": [round(float(x), 4) for x in (q.w, q.x, q.y, q.z)], "lod": e.lod_level.name, "lod_dist": e.lod_dist,
                     "parent_index": getattr(e, "parent_index", None), "flags": str(getattr(e, "flags", ""))})
        for i, b in enumerate(m.box_occluders):
            c = np.array(b.center); sz = np.array(b.size)
            r_ = 0.5 * math.hypot(sz[0], sz[1])
            if hit(c - [r_, r_, sz[2] / 2], c + [r_, r_, sz[2] / 2]):
                R["occluders"].append({"ymap": p.as_posix(), "kind": "box", "index": i, "center": c.round(2).tolist(),
                                       "size": sz.round(2).tolist()})
        for i, mo in enumerate(m.model_occluders):
            V = np.asarray(mo.vertices, dtype=float).reshape(-1, 3)
            if len(V) and hit(V.min(0), V.max(0)):
                R["occluders"].append({"ymap": p.as_posix(), "kind": "model", "index": i, "verts": int(len(V)),
                                       "min": V.min(0).round(2).tolist(), "max": V.max(0).round(2).tolist()})
        for i, g in enumerate(m.grass_instance_lists):
            gm, gx = np.array(g.extents[0]), np.array(g.extents[1])
            if not hit(gm, gx):
                continue
            P = g.unpack_instances()["Position"]
            ins = (P[:, 0] > AMIN[0]) & (P[:, 0] < AMAX[0]) & (P[:, 1] > AMIN[1]) & (P[:, 1] < AMAX[1])
            if ins.any():
                R["grass"].append({"ymap": p.as_posix(), "index": i, "archetype": g.archetype_name, "instances": int(len(P)),
                                   "inside": int(ins.sum()), "min": P[ins].min(0).round(2).tolist(), "max": P[ins].max(0).round(2).tolist()})
        if any(k in p.name.lower() for k in ("sc1_14", "sc1_rd", "sc1_lod")):
            stem = p.name[:-5]
            SEEN[stem] = SEEN.get(stem, 0) + 1
            export(m, stem if SEEN[stem] == 1 else f"{stem}__copy{SEEN[stem]}", "ymap")
            R["ymaps"][-1]["exported_as"] = stem if SEEN[stem] == 1 else f"{stem}__copy{SEEN[stem]}"
    except Exception:
        R["errors"].append(f"ymap {p.as_posix()}: " + traceback.format_exc()[-300:])
note(f"ymaps touching the area {len(R['ymaps'])}, archetypes within 140 m {len(near)}")

# ---------------------------------------------------------------- drawables of those entities with geometry in the area
from mathutils import Quaternion
for name, places in sorted(near.items()):
    if name not in models:
        continue
    try:
        a = szio.try_load_asset(models[name])
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        if not getattr(d, "models", None):
            continue
        sh_names = [s.name for s in d.shader_group.shaders] if d.shader_group else []
        rec = None
        for pl in places:
            w, x, y, z = pl["rot"]
            qm = np.array(Quaternion((w, -x, -y, -z)).to_matrix())        # ymap entities store the inverse rotation
            hits = []
            for lod, mods in d.models.items():
                for mi, mdl in enumerate(mods):
                    for gi, g in enumerate(mdl.geometries):
                        P = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3)
                        W = P @ qm.T + np.array(pl["pos"])
                        ins = np.all((W > AMIN) & (W < AMAX), axis=1)
                        if ins.any():
                            si = getattr(g, "shader_index", None)
                            hits.append({"lod": str(lod), "model": mi, "geom": gi,
                                         "shader": sh_names[si] if isinstance(si, int) and si < len(sh_names) else si,
                                         "verts_in": int(ins.sum()), "verts": int(len(P)),
                                         "min": W[ins].min(0).round(2).tolist(), "max": W[ins].max(0).round(2).tolist()})
            if hits:
                rec = rec or {"archetype": name, "path": models[name].as_posix(), "placements": []}
                rec["placements"].append({"placement": pl, "hits": hits})
        if rec:
            R["drawables"].append(rec)
            ext = models[name].name.lower()[-3:]
            export(a, name, ext)
    except Exception:
        R["errors"].append(f"model {name}: " + traceback.format_exc()[-300:])
note(f"drawables with geometry in the area: {[d_['archetype'] for d_ in R['drawables']]}")

# ---------------------------------------------------------------- static bounds with primitives in the area
for p in ybns:
    try:
        b = szio.try_load_asset(p)
        if b is None or not hasattr(b, "children"):
            continue
        n_in, kids = 0, []
        for ci, c in enumerate(b.children):
            if c is None or not hasattr(c, "geometry_vertices"):
                continue
            V = np.array([tuple(v.position) for v in c.geometry_vertices], dtype=float)
            if not len(V):
                continue
            ins = np.all((V > AMIN) & (V < AMAX), axis=1)
            if ins.any():
                n_in += int(ins.sum())
                kids.append({"child": ci, "verts_in": int(ins.sum()), "verts": int(len(V)),
                             "prims": len(c.geometry_primitives)})
        if n_in:
            R["bounds"].append({"ybn": p.as_posix(), "verts_in": n_in, "children": kids})
            export(b, p.name[:-4], "ybn")
    except Exception:
        R["errors"].append(f"ybn {p.as_posix()}: " + traceback.format_exc()[-300:])
note(f"bounds with vertices in the area: {[b_['ybn'].split('/')[-1] for b_ in R['bounds']]}")

R["entities"] = [{"archetype": k, "placements": v} for k, v in sorted(near.items())]
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(R, fh, indent=1, default=str)
print("GS_KIOSK_SCAN_DONE ymaps=%d entities=%d drawables=%d bounds=%d grass=%d occl=%d exported=%d errors=%d -> %s" % (
    len(R["ymaps"]), len(R["entities"]), len(R["drawables"]), len(R["bounds"]), len(R["grass"]), len(R["occluders"]),
    len(R["exported"]), len(R["errors"]), OUT))
