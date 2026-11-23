# LONG PIG — internal reference copies of the vanilla props used in the Vertical Slice, for the offline preview renders
# only (CodeWalker XML + their textures). The FiveM resource never contains these files: the MLO references the props
# by archetype name. Read-only access to the game archives.
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_25d_prop_export.py", encoding="utf-8").read())
# Output: reference_vanilla/props/<name>.ydr.xml (+ <name>/<tex>.dds) and docs/_raw/vanilla_props_slice.json
import os, json, time, traceback
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
OUT = ROOT / "reference_vanilla" / "props"
LOG = ROOT / "docs" / "_raw" / "vanilla_props_slice.json"
PROPS = ["prop_till_01", "v_ret_ml_scale", "prop_coffee_mac_02", "v_res_fa_bread01", "v_res_fa_bread02", "v_res_fa_chopbrd",
         "prop_cleaver", "prop_knife_stand", "prop_bar_napkindisp", "prop_food_ketchup", "prop_food_mustard",
         "prop_food_sugarjar", "v_ilev_fh_kitchenstool", "prop_wine_red", "prop_wine_white", "v_19_vanmenuplain",
         "tr_int1_chalkboard"]

paths = {}
for src in ("vanilla_props_deli.json", "vanilla_menus.json"):
    j = json.load(open(ROOT / "docs" / "_raw" / src, encoding="utf-8"))
    for h in j.get("focus", []) + j.get("hits", []):
        paths.setdefault(h["name"], h["path"])
log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "props": [], "errors": []}
ytd_cache = {}


def rpf_root(posix):
    i = posix.lower().rfind(".rpf/")
    return posix[:i + 4] if i >= 0 else None


def ytds_under(root):
    if root not in ytd_cache:
        ytd_cache[root] = [p for p in VPath(root).rglob("*") if p.name.lower().endswith(".ytd")]
    return ytd_cache[root]


OUT.mkdir(parents=True, exist_ok=True)
for name in PROPS:
    rec = {"name": name, "path": paths.get(name)}
    try:
        if not rec["path"]:
            raise KeyError("not in the scans")
        a = szio.try_load_asset(VPath(rec["path"]))
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        try:
            szio.save_asset(d, [AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)], OUT, name)
        except Exception as e:
            log["errors"].append(f"cwxml {name}: {e!r}"[:300])
        lod = min(d.models.keys(), key=lambda k: int(k))
        P = np.concatenate([np.array(g.vertex_buffer["Position"], float).reshape(-1, 3) for m in d.models[lod] for g in m.geometries])
        rec["min"], rec["max"] = P.min(0).round(4).tolist(), P.max(0).round(4).tolist()
        want = sorted({p.value for sh in (d.shader_group.shaders if d.shader_group else []) for p in sh.parameters
                       if isinstance(p.value, str) and p.value})
        rec["textures"] = want
        tdir = OUT / name
        tdir.mkdir(parents=True, exist_ok=True)
        emb = d.shader_group.embedded_textures if d.shader_group else {}
        left = []
        for t in want:
            if t in emb and emb[t].data is not None:
                (tdir / f"{t}.dds").write_bytes(emb[t].data.read_bytes())
            else:
                left.append(t)
        root = rpf_root(rec["path"])
        if left and root:
            folder = rec["path"].rsplit("/", 1)[0].lower()
            for y in sorted(ytds_under(root), key=lambda p: 0 if p.as_posix().lower().startswith(folder) else 1):
                if not left:
                    break
                try:
                    texs = getattr(szio.try_load_asset(y), "textures", {}) or {}
                    for t in list(left):
                        tex = texs.get(t) or texs.get(t.lower())
                        if tex is not None and tex.data is not None:
                            (tdir / f"{t}.dds").write_bytes(tex.data.read_bytes())
                            left.remove(t)
                except Exception as e:
                    log["errors"].append(f"{y.name}: {e!r}"[:200])
        rec["missing_textures"] = left
    except Exception:
        log["errors"].append(f"{name}: " + traceback.format_exc()[-300:])
    log["props"].append(rec)
    print("[gs_props_x]", name, rec.get("min"), rec.get("max"), "missing", rec.get("missing_textures"), flush=True)
LOG.parent.mkdir(parents=True, exist_ok=True)
with open(LOG, "w", encoding="utf-8") as fh:
    json.dump(log, fh, indent=1)
print("GS_PROPS_X_DONE props=%d errors=%d" % (len(log["props"]), len(log["errors"])))
