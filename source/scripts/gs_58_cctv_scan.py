# LONG PIG 2.7.0: READ-ONLY bounds scan of the 24/7 store set and fruit / basket props in the owner's game. Nothing is written
# into the game folder. Result: docs/_raw/scan_247.json
import os, re, json, traceback
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
ROOT = Path(os.environ.get("GS_ROOT"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
PAT = re.compile(r"(cctv|sec_cam|securitycam|prop_cs_cctv|v_serv_.*cam)")
R = {"items": {}, "errors": []}
found = {}
for r in sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]:
    if not r.exists():
        continue
    try:
        for p in VPath(str(r)).rglob("*"):
            nm = p.name.lower()
            if not nm.endswith((".ydr", ".yft")):
                continue
            stem = nm[:-4]
            if not stem.endswith(("_lod", "_slod", "+hi", "_hi")) and PAT.search(stem):
                found.setdefault(stem, p)
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
                            "tex": sorted({str(q.value) for s in d.shader_group.shaders for q in s.parameters if isinstance(q.value, str)})[:6],
                            "lights": len(getattr(d, "lights", None) or [])}
    except Exception:
        R["errors"].append(f"{stem}: " + traceback.format_exc()[-300:])
(ROOT / "docs" / "_raw" / "scan_cctv.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
print("[gs_247] DONE", len(R["items"]), len(R["errors"]))
