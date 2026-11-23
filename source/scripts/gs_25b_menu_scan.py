# LONG PIG — find vanilla GTA V menu boards / chalkboards / price boards (read-only, names + HIGH-LOD bounds).
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_25b_menu_scan.py", encoding="utf-8").read())
# Output: docs/_raw/vanilla_menus.json. Any model name (no prefix filter) containing one of WORDS is listed;
# bounds + texture names are read for every hit so the boards can be judged without opening CodeWalker.
import os, json, time, traceback
from pathlib import Path
import szio
from szio.vfs import VPath

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "docs" / "_raw" / "vanilla_menus.json"
WORDS = ("menu", "chalk", "blackb", "specials", "pricelist", "price_", "foodboard", "menub", "_board", "board_", "tvmenu")
SKIP = ("_lod", "_slod", "skateboard", "snowboard", "surfboard", "dashboard", "keyboard", "cardboard", "billboard",
        "clipboard", "skirtingboard", "chopboard", "floorboard")

log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "hits": [], "errors": []}
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
            if not (nm.endswith(".ydr") or nm.endswith(".yft") or nm.endswith(".ydd")):
                continue
            stem = nm.rsplit(".", 1)[0]
            if any(s in stem for s in SKIP) or not any(w in stem for w in WORDS):
                continue
            seen[stem] = p
    except Exception:
        log["errors"].append(f"scan {r.name}: " + traceback.format_exc()[-300:])

import numpy as np
for stem, p in sorted(seen.items()):
    rec = {"name": stem, "path": p.as_posix()}
    try:
        a = szio.try_load_asset(p)
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        if getattr(d, "models", None):
            lod = min(d.models.keys(), key=lambda k: int(k))
            P = np.concatenate([np.array(g.vertex_buffer["Position"], float).reshape(-1, 3) for m in d.models[lod] for g in m.geometries])
            rec["min"] = P.min(0).round(3).tolist()
            rec["max"] = P.max(0).round(3).tolist()
            rec["size"] = (P.max(0) - P.min(0)).round(3).tolist()
            rec["tris"] = int(sum(len(g.index_buffer) // 3 for m in d.models[lod] for g in m.geometries))
        tex = []
        for s in (d.shader_group.shaders if d.shader_group else []):
            for prm in getattr(s, "parameters", []) or []:
                v = getattr(prm, "texture_name", None) or getattr(prm, "value", None)
                if isinstance(v, str) and v and v not in tex:
                    tex.append(v)
        rec["textures"] = tex[:16]
    except Exception as e:
        rec["error"] = repr(e)[:160]
    log["hits"].append(rec)
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(log, fh, indent=1)
print("GS_MENUS_DONE hits=%d errors=%d -> %s" % (len(log["hits"]), len(log["errors"]), OUT))
