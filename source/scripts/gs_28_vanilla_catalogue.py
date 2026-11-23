# LONG PIG — v0.2.1 art pass: catalogue of vanilla GTA V interior props by category (read-only; names, archive,
# HIGH-LOD bounds, triangle count, texture names). Nothing is copied: chosen props are placed by archetype name.
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_28_vanilla_catalogue.py", encoding="utf-8").read())
# Output: docs/_raw/vanilla_catalogue_v021.json
import os, json, time, traceback, re
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "docs" / "_raw" / "vanilla_catalogue_v021.json"
CATS = {
    "seating": ["sofa", "couch", "armchair", "chair", "stool", "booth", "bench", "settee", "chesterfield", "seat", "banquette"],
    "lighting": ["lamp", "chandelier", "pendant", "sconce", "ceillight", "ceilinglight", "ceil_light", "walllight", "wall_light",
                 "lightshade", "shade", "bulb", "fluor", "spotlight", "downlight", "fan"],
    "decor": ["pic", "picture", "painting", "frame", "poster", "clock", "flag", "plant", "vase", "statue", "mirror", "cert",
              "award", "trophy", "photo", "curtain", "rug", "carpet", "blind", "pennant", "scarf", "calendar", "crucifix",
              "cross", "madonna", "radio", "tv"],
    "retail": ["shelf", "shelves", "rack", "can", "jar", "pasta", "oil", "wine", "bottle", "olive", "tomato", "cheese",
               "coffee", "cup", "plate", "bread", "deli", "menu", "till", "register", "scale", "napkin", "tray", "crate",
               "barrel", "box", "food", "meat", "ham", "sausage", "salami", "fridge", "display", "case", "counter", "espresso"],
    "tables": ["table", "desk"],
}
SHORT = {"can", "jar", "cup", "ham", "fan", "tv", "pic", "box", "oil", "rug"}          # whole-token matches only
SKIP = ("_lod", "_slod", "_hi", "_dam", "_frag", "_proxy", "_emissive", "_ovr", "_decal", "_shadow", "_occl")

log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "items": [], "errors": []}


def cats_of(stem):
    tk = re.findall(r"[a-z]+", stem)
    out = []
    for cat, keys in CATS.items():
        for k in keys:
            if (k in tk) if k in SHORT else any(k in t for t in tk):
                out.append(f"{cat}:{k}")
    return out


def prio(path):
    p = path.lower()
    return 3 if "/update/update.rpf" in p else (2 if "dlcpacks" in p and "patch" in p else (1 if "dlcpacks" in p else 0))


archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
for base in (GTA / "update" / "x64" / "dlcpacks", GTA / "x64" / "dlcpacks"):
    if base.is_dir():
        archives += sorted(base.glob("*/dlc.rpf"))
seen = {}
for r in archives:
    if not r.exists():
        continue
    try:
        for p in VPath(str(r)).rglob("*"):
            nm = p.name.lower()
            if not (nm.endswith(".ydr") or nm.endswith(".yft")):
                continue
            stem = nm.rsplit(".", 1)[0]
            if stem.endswith(SKIP) or "_lod" in stem:
                continue
            c = cats_of(stem)
            if not c:
                continue
            pp = p.as_posix()
            if stem not in seen or prio(pp) > prio(seen[stem][0].as_posix()):
                seen[stem] = (p, c)
    except Exception:
        log["errors"].append(f"scan {r.name}: " + traceback.format_exc()[-300:])
print("[gs_cat] candidates", len(seen), flush=True)

t0 = time.time()
for i, (stem, (p, c)) in enumerate(sorted(seen.items())):
    rec = {"name": stem, "rpf": p.as_posix().split("/")[-2], "path": p.as_posix(), "cats": c}
    try:
        a = szio.try_load_asset(p)
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        if getattr(d, "models", None):
            lod = min(d.models.keys(), key=lambda k: int(k))
            geoms = [g for m in d.models[lod] for g in m.geometries]
            P = np.concatenate([np.array(g.vertex_buffer["Position"], float).reshape(-1, 3) for g in geoms])
            rec["min"] = P.min(0).round(3).tolist()
            rec["max"] = P.max(0).round(3).tolist()
            rec["tris"] = int(sum(len(g.index_buffer) // 3 for g in geoms))
            rec["geoms"] = len(geoms)
            rec["shaders"] = sorted({s.preset_filename for s in d.shader_group.shaders}) if d.shader_group else []
            rec["lights"] = len(getattr(d, "lights", []) or [])
    except Exception as e:
        rec["error"] = repr(e)[:120]
    log["items"].append(rec)
    if i % 500 == 0:
        print("[gs_cat] bounds", i, "/", len(seen), round(time.time() - t0), "s", flush=True)
log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(log, fh)
print("GS_CATALOGUE_DONE items=%d errors=%d -> %s" % (len(log["items"]), len(log["errors"]), OUT))
