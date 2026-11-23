# LONG PIG — find vanilla GTA V door models and measure them (read-only, nothing is written into the game files).
# Runs INSIDE Blender 5.1 + Sollumz 2.9 on the PC (needs PyMateria for the RPF archives):
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_24_vanilla_doors.py", encoding="utf-8").read())
# Output: docs/_raw/vanilla_doors.json (path, bbox, size of every *door*.ydr / *door*.yft in the base game + update)
#         reference_vanilla/doors/<name>.ydr.xml for the shortlisted models (internal reference only, never shipped)
import os, sys, json, time, traceback, fnmatch
from pathlib import Path

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "docs" / "_raw" / "vanilla_doors.json"
XMLDIR = ROOT / "reference_vanilla" / "doors"
SHORTLIST = os.environ.get("GS_DOOR_SHORTLIST", "")  # comma separated names -> export CWXML for those only

import szio
from szio.vfs import VPath
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion

log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "gta": str(GTA), "archives": [], "doors": [], "errors": []}


def note(msg):
    print("[gs_doors]", msg, flush=True)


def bbox_of_drawable(d):
    import numpy as np
    mn, mx = None, None
    if not d.models:
        return None, None
    lod = min(d.models.keys(), key=lambda k: int(k))      # HIGH detail level
    for models in [d.models[lod]]:
        for m in models:
            for g in m.geometries:
                P = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3)
                if len(P) == 0:
                    continue
                a, b = P.min(0), P.max(0)
                mn = a if mn is None else np.minimum(mn, a)
                mx = b if mx is None else np.maximum(mx, b)
    return (mn.tolist(), mx.tolist()) if mn is not None else (None, None)


def scan():
    roots = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
    hits = []
    for r in roots:
        if not r.exists():
            continue
        t0 = time.time()
        n = 0
        try:
            vp = VPath(str(r))
            for p in vp.rglob("*"):
                nm = p.name.lower()
                if "door" in nm and (nm.endswith(".ydr") or nm.endswith(".yft")):
                    hits.append(p)
                n += 1
        except Exception:
            log["errors"].append(f"scan {r}: " + traceback.format_exc()[-600:])
        log["archives"].append({"rpf": r.name, "entries": n, "seconds": round(time.time() - t0, 1)})
        note(f"{r.name}: {n} entries, {len(hits)} door files so far, {time.time() - t0:.0f}s")
    return hits


def measure(paths):
    seen = {}
    for p in paths:
        nm = p.name.lower()
        rec = {"name": nm, "path": p.as_posix()}
        try:
            a = szio.try_load_asset(p)
            d = a
            if hasattr(a, "drawable") and a.drawable is not None:      # fragments
                d = a.drawable
            mn, mx = bbox_of_drawable(d)
            rec.update(min=mn, max=mx, size=[round(b - a_, 3) for a_, b in zip(mn, mx)] if mn else None,
                       type=type(a).__name__, has_bounds=getattr(d, "bounds", None) is not None)
        except Exception as e:
            rec["error"] = repr(e)[:200]
        # update.rpf overrides the base copy of the same name
        if nm not in seen or "update.rpf" in rec["path"]:
            seen[nm] = rec
    return sorted(seen.values(), key=lambda r: r["name"])


def export_shortlist(names):
    XMLDIR.mkdir(parents=True, exist_ok=True)
    data = json.load(open(OUT, encoding="utf-8"))
    by = {d["name"]: d for d in data["doors"]}
    done = []
    for n in names:
        rec = by.get(n.lower().strip())
        if not rec:
            log["errors"].append(f"shortlist: {n} not found")
            continue
        a = szio.try_load_asset(VPath(rec["path"]))
        stem = Path(rec["name"]).stem
        try:
            szio.save_asset(a, [AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)], XMLDIR, stem)
        except Exception as e:                       # szio CWXML writer fails on some fragments (Vector.w)
            log["errors"].append(f"cwxml {n}: {e!r}"[:300])
            if hasattr(a, "drawable") and a.drawable is not None:
                try:
                    szio.save_asset(a.drawable, [AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)], XMLDIR, stem)
                except Exception as e2:
                    log["errors"].append(f"cwxml drawable {n}: {e2!r}"[:300])
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        mn, mx = bbox_of_drawable(d)
        # embedded textures -> reference_vanilla/doors/<stem>/<tex>.dds (internal preview only, never shipped)
        if d.shader_group and d.shader_group.embedded_textures:
            tdir = XMLDIR / stem
            tdir.mkdir(parents=True, exist_ok=True)
            for tname, tex in d.shader_group.embedded_textures.items():
                if tex.data is not None:
                    (tdir / (tname + ".dds")).write_bytes(tex.data.read_bytes())
        lods = {str(k): sum(len(g.index_buffer) // 3 for m in v for g in m.geometries) for k, v in d.models.items()}
        txd = sorted({p.value for sh in (d.shader_group.shaders if d.shader_group else []) for p in sh.parameters if isinstance(p.value, str)})
        done.append({"name": stem, "path": rec["path"], "min": mn, "max": mx, "lod_tris": lods, "textures": txd,
                     "embedded": sorted(d.shader_group.embedded_textures) if d.shader_group else []})
    note(f"exported {done}")
    return done


try:
    if SHORTLIST:
        log["exported"] = export_shortlist([s for s in SHORTLIST.split(",") if s.strip()])
        with open(OUT.with_name("vanilla_doors_shortlist.json"), "w", encoding="utf-8") as fh:
            json.dump(log, fh, indent=1, default=str)
    else:
        paths = scan()
        log["doors"] = measure(paths)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(log, fh, indent=1)
        note(f"{len(log['doors'])} door models measured -> {OUT}")
except Exception:
    log["errors"].append(traceback.format_exc())
    print(traceback.format_exc())
print("GS_DOORS_DONE errors=%d" % len(log["errors"]))
