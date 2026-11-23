# LONG PIG 2.5.0: READ-ONLY bounds scan of the Pleb Masters Forge candidates in the owner's game (names from
# gs_54_names.txt). Looks at x64*.rpf, update.rpf and every dlc.rpf under update/x64/dlcpacks; .ydr and .yft only.
# Nothing is exported or written into the game folder. Result: docs/_raw/forge_scan.json
import os, json, traceback
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
ROOT = Path(os.environ.get("GS_ROOT"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
WANT = set(x.strip().lower() for x in (ROOT / "source" / "scripts" / "gs_54_names.txt").read_text().split() if x.strip())
R = {"items": {}, "errors": [], "not_found": [], "other_ext": {}}
archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"] + sorted((GTA / "update" / "x64" / "dlcpacks").glob("*/dlc.rpf"))
found = {}
for r in archives:
    if not r.exists():
        continue
    try:
        for p in VPath(str(r)).rglob("*"):
            nm = p.name.lower()
            if "." not in nm:
                continue
            stem, ext = nm.rsplit(".", 1)
            if stem in WANT:
                if ext in ("ydr", "yft"):
                    found.setdefault(stem, p)
                else:
                    R["other_ext"].setdefault(stem, []).append(p.as_posix().split("GTAV/")[-1])
    except Exception:
        R["errors"].append(f"scan {r}: " + traceback.format_exc()[-200:])
for stem, p in sorted(found.items()):
    try:
        a = szio.try_load_asset(p)
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        mn, mx, tris = None, None, 0
        for lod, ms in d.models.items():
            for m in ms:
                for g in m.geometries:
                    P = np.array(g.vertex_buffer["Position"], float).reshape(-1, 3)
                    mn = P.min(0) if mn is None else np.minimum(mn, P.min(0)); mx = P.max(0) if mx is None else np.maximum(mx, P.max(0))
                    tris += len(np.asarray(g.index_buffer)) // 3
            break
        R["items"][stem] = {"min": mn.round(3).tolist(), "max": mx.round(3).tolist(), "tris": tris, "rpf": p.as_posix().split("GTAV/")[-1],
                            "tex": sorted({str(q.value) for s in d.shader_group.shaders for q in s.parameters if isinstance(q.value, str)})[:6]}
    except Exception:
        R["errors"].append(f"{stem}: " + traceback.format_exc()[-300:])
R["not_found"] = sorted(WANT - set(R["items"]))
(ROOT / "docs" / "_raw" / "forge_scan.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
print("[gs_forge] DONE", len(R["items"]), "found,", len(R["not_found"]), "not found,", len(R["errors"]), "errors")
