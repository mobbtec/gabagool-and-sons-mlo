# LONG PIG — find vanilla GTA V props for the deli / booths (read-only; names + HIGH-LOD bounds, nothing is copied).
# Blender 5.1 console on the PC (Sollumz 2.9 / PyMateria):
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_25_vanilla_props_scan.py", encoding="utf-8").read())
# Output: docs/_raw/vanilla_props_deli.json — candidates are referenced by archetype name only (VANILLA_REF).
#   "focus": deli / booth / counter words  -> name, archive, HIGH-LOD size, triangle count, texture names
#   "names": generic words (lamp, sign, shelf ...) -> name + archive only (too many to load)
# Words are matched against the alphabetic tokens of the model name (no "ham" inside "chamber").
import os, json, time, traceback, re
from pathlib import Path
import szio
from szio.vfs import VPath

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "docs" / "_raw" / "vanilla_props_deli.json"
FOCUS_PREFIX = ["slicer", "scale", "meat", "salami", "sausage", "cheese", "deli", "butcher", "cleaver", "knife", "kniv",
                "till", "register", "bread", "baguette", "olive", "pasta", "tomato", "napkin", "ketchup", "mustard",
                "booth", "diner", "stool", "fridge", "chiller", "coffee", "espresso", "menu", "sandwich", "pizza",
                "wine", "steak", "chicken", "turkey", "bacon", "beef", "pork", "condiment", "sauce", "dispenser",
                "chop", "cutting", "counter", "cabinet", "showcase", "salt", "pepper", "sugar", "kitch"]
FOCUS_EXACT = ["ham", "sub", "pig", "jar", "cup", "mug", "can", "tin", "oil", "tray", "food"]
NAMES_PREFIX = ["lamp", "light", "sign", "clock", "phone", "radio", "fan", "rack", "shelf", "display", "plate",
                "bottle", "crate", "box", "bin", "frame", "pic", "poster", "calendar", "fire", "ext"]
PREFIX_OK = ("prop_", "v_ret_", "v_res_", "v_ilev_", "v_club_", "v_corp_", "v_med_", "v_serv_", "v_int_", "p_", "hei_",
             "ba_", "bkr_", "ch_", "xm_", "sm_", "tr_", "vw_", "h4_", "sf_")

log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "archives": 0, "focus": [], "names": {}, "errors": []}


def tokens(stem):
    return re.findall(r"[a-z]+", stem)


def match(stem, prefixes, exact):
    tk = tokens(stem)
    hit = [k for k in prefixes if any((k in t) if len(k) >= 5 else t.startswith(k) for t in tk)]   # mkniferack -> knife
    hit += [k for k in exact if k in tk]
    return hit


def prio(path):
    p = path.lower()
    if "/update/update.rpf" in p:
        return 3
    if "dlcpacks" in p:
        return 2 if "patch" in p else 1
    return 0


def bbox(d):
    import numpy as np
    if not getattr(d, "models", None):
        return None
    lod = min(d.models.keys(), key=lambda k: int(k))
    mn = mx = None
    tris = 0
    for m in d.models[lod]:
        for g in m.geometries:
            P = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3)
            tris += len(g.index_buffer) // 3
            if len(P):
                a, b = P.min(0), P.max(0)
                mn = a if mn is None else np.minimum(mn, a)
                mx = b if mx is None else np.maximum(mx, b)
    if mn is None:
        return None
    tex = []
    try:
        for s in d.shader_group.shaders:
            for p in getattr(s, "parameters", []) or []:
                v = getattr(p, "texture_name", None) or getattr(p, "value", None)
                if isinstance(v, str) and v and v not in tex:
                    tex.append(v)
    except Exception:
        pass
    return {"size": [round(float(x), 3) for x in (mx - mn)], "min": [round(float(x), 3) for x in mn],
            "max": [round(float(x), 3) for x in mx], "tris": tris, "textures": tex[:12]}


archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
for base in (GTA / "update" / "x64" / "dlcpacks", GTA / "x64" / "dlcpacks"):
    if base.is_dir():
        archives += sorted(base.glob("*/dlc.rpf"))
seen = {}
for r in archives:
    if not r.exists():
        continue
    log["archives"] += 1
    try:
        for p in VPath(str(r)).rglob("*"):
            nm = p.name.lower()
            if not (nm.endswith(".ydr") or nm.endswith(".yft")):
                continue
            stem = nm.rsplit(".", 1)[0]
            if not stem.startswith(PREFIX_OK) or stem.endswith(("_lod", "_slod", "_hi")):
                continue
            pp = p.as_posix()
            f = match(stem, FOCUS_PREFIX, FOCUS_EXACT)
            if f:
                if stem not in seen or prio(pp) > prio(seen[stem][0].as_posix()):
                    seen[stem] = (p, f)
                continue
            g = match(stem, NAMES_PREFIX, [])
            if g:
                log["names"].setdefault(g[0], {})[stem] = pp.split("/")[-2] if "/" in pp else pp
    except Exception:
        log["errors"].append(f"scan {r.name}: " + traceback.format_exc()[-300:])
    print("[gs_props]", r.name, "focus", len(seen), flush=True)

t0 = time.time()
for i, (stem, (p, hit)) in enumerate(sorted(seen.items())):
    rec = {"name": stem, "path": p.as_posix(), "keys": hit}
    try:
        a = szio.try_load_asset(p)
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        rec.update(bbox(d) or {})
    except Exception as e:
        rec["error"] = repr(e)[:160]
    log["focus"].append(rec)
    if i % 100 == 0:
        print("[gs_props] bounds", i, "/", len(seen), round(time.time() - t0), "s", flush=True)
log["names"] = {k: dict(sorted(v.items())) for k, v in sorted(log["names"].items())}
log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(log, fh, indent=1)
print("GS_PROPS_DONE focus=%d names=%d errors=%d -> %s" % (len(log["focus"]), sum(len(v) for v in log["names"].values()),
                                                          len(log["errors"]), OUT))
