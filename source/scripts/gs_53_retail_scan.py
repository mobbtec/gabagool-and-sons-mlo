# LONG PIG 0.3.2: READ-ONLY scan of vanilla retail props (names, bounds, triangles). Optional: CWXML export of chosen names
# into reference_vanilla/catalogue (analysis copies, never shipped). Env GS_EXPORT = comma-separated names.
import os, re, json, traceback
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion
ROOT = Path(os.environ.get("GS_ROOT"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
PAT = re.compile(r"^(v_ret_247|v_ret_ml_|v_ret_fh_|v_ret_ps_|v_ret_gc_|prop_vend_|v_res_fa_(crisp|cereal|tin|boot)|ng_proc_(food|sodacan|beerbottle|candy|crisps|sodabot|ciggy)"
                 r"|prop_.*(fridge|beer|crisp|snack|sweet|candy|magaz|news|shop|display|juice|ecola|sprunk|choc|gum|cola|pizza|burger|taco|donut|hotdog|icecream|freezer|chiller|cooler|shelf|shelv|crate|trolley|basket|cig|lighter|energy|drink|can_|cereal|sauce))")
WANT = set(x.strip().lower() for x in os.environ.get("GS_EXPORT", "").split(",") if x.strip())
R = {"items": {}, "errors": [], "exported": []}
archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
found = {}
for r in archives:
    if not r.exists():
        continue
    try:
        for p in VPath(str(r)).rglob("*.ydr"):
            stem = p.name[:-4].lower()
            if stem.endswith(("_lod", "_slod", "+hi")):
                continue
            if PAT.search(stem) or stem in WANT:
                found.setdefault(stem, p)
    except Exception:
        R["errors"].append(f"scan {r}: " + traceback.format_exc()[-200:])
CW = [AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)]
for stem, p in sorted(found.items()):
    if WANT and stem not in WANT:
        continue
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
            break                                              # HIGH lod only
        R["items"][stem] = {"min": mn.round(3).tolist(), "max": mx.round(3).tolist(), "tris": tris, "rpf": p.as_posix().split("GTAV/")[-1],
                            "tex": sorted({str(q.value) for s in d.shader_group.shaders for q in s.parameters if isinstance(q.value, str)})[:6]}
        if stem in WANT:
            szio.save_asset(a, CW, ROOT / "reference_vanilla" / "catalogue", stem)
            R["exported"].append(stem)
    except Exception:
        R["errors"].append(f"{stem}: " + traceback.format_exc()[-200:])
out = ROOT / "docs" / "_raw" / ("retail_scan_export.json" if WANT else "retail_scan.json")
out.write_text(json.dumps(R, indent=1), encoding="utf-8")
print("[gs_retail] DONE", len(R["items"]), len(R["exported"]), len(R["errors"]))
