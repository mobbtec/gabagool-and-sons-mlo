# LONG PIG 0.3.1-o: READ-ONLY look at the vanilla LOD dictionaries around the removed kiosk (nothing written to the game).
import os, json, traceback
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
ROOT = Path(os.environ.get("GS_ROOT"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
R = {"ydds": [], "errors": [], "found": {}}
WANT = {"sc1_14_build2_lod", "sc1_14_grnd_02_lod", "sc1_14_slod1", "sc1_14_bb_meltdown_lod", "sc1_14_bb_mollis_lod",
        "sc1_14_sc1_emissive_sc1_14b_lod", "sc1_14_sc1_emissive_slod"}
archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
for base in (GTA / "update" / "x64" / "dlcpacks", GTA / "x64" / "dlcpacks"):
    if base.is_dir():
        archives += sorted(base.glob("*/dlc.rpf"))
cands = []
for r in archives:
    if not r.exists():
        continue
    try:
        for p in VPath(str(r)).rglob("*.ydd"):
            pp = p.as_posix().lower()
            if "sc1_14" in p.name.lower() or "sc1_lod" in p.name.lower() or ("scentral" in pp and "sc1_" in p.name.lower() and "lod" in p.name.lower()):
                cands.append(p)
    except Exception:
        R["errors"].append(f"scan {r}: " + traceback.format_exc()[-300:])
R["candidates"] = [p.as_posix() for p in cands]
first = True
for p in cands:
    try:
        a = szio.try_load_asset(p)
        rec = {"path": p.as_posix(), "type": type(a).__name__}
        if first and a is not None:
            rec["dir"] = [x for x in dir(a) if not x.startswith("__")]
            first = False
        dd = getattr(a, "drawables", None)
        names = []
        if dd is not None:
            it = dd.items() if hasattr(dd, "items") else enumerate(dd)
            for k, d in it:
                nm = str(getattr(d, "name", k))
                names.append([str(k), nm])
                key = nm.lower().replace(".#dr", "")
                if key in WANT or str(k).lower() in WANT:
                    tex = []
                    try:
                        for t in (d.shader_group.embedded_textures or {}).values() if hasattr(d.shader_group.embedded_textures, "values") else (d.shader_group.embedded_textures or []):
                            tex.append([getattr(t, "name", str(t)), getattr(t, "width", None), getattr(t, "height", None)])
                    except Exception as e:
                        tex = ["err " + str(e)]
                    R["found"][key] = {"ydd": p.as_posix(), "key": str(k), "dtype": type(d).__name__, "embedded": tex,
                                       "shaders": [[s.name, [str(q.value) for q in s.parameters if isinstance(q.value, str)]] for s in d.shader_group.shaders],
                                       "sg_dir": [x for x in dir(d.shader_group) if not x.startswith("_")],
                                       "ddir": [x for x in dir(d) if not x.startswith("_")]}
        rec["drawables"] = names
        R["ydds"].append(rec)
    except Exception:
        R["errors"].append(f"load {p.as_posix()}: " + traceback.format_exc()[-400:])
(ROOT / "docs" / "_raw" / "lod_explore.json").write_text(json.dumps(R, indent=1, default=str), encoding="utf-8")
print("[gs_lod] DONE", len(cands), list(R["found"]), len(R["errors"]))
