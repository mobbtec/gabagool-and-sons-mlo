# LONG PIG — dump the textures of the vanilla menu / chalkboard candidates so they can be compared as pictures
# (read-only; internal reference only, never shipped — the chosen prop is placed by archetype name).
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_25c_menu_textures.py", encoding="utf-8").read())
# Output: reference_vanilla/menus/<model>/<texture>.dds + docs/_raw/vanilla_menus_textures.json
import os, json, time, traceback
from pathlib import Path
import szio
from szio.vfs import VPath

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
OUT = ROOT / "reference_vanilla" / "menus"
LOG = ROOT / "docs" / "_raw" / "vanilla_menus_textures.json"
CANDIDATES = ["v_res_mchalkbrd", "v_ilev_mchalkbrd_1", "v_ilev_mchalkbrd_2", "v_ilev_mchalkbrd_3", "v_ilev_mchalkbrd_4",
              "v_ilev_mchalkbrd_5", "v_19_vanmenuplain", "tr_int1_chalkboard", "bkr_prop_clubhouse_blackboard_01a",
              "prop_drinkmenu", "prop_bahammenu"]
SKIP_TEX = ("_n", "_s", "prop_metal", "edge_blends", "script_rt", "prop_glass", "prop_base")

menus = json.load(open(ROOT / "docs" / "_raw" / "vanilla_menus.json", encoding="utf-8"))
by = {h["name"]: h for h in menus["hits"]}
log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "models": [], "errors": []}
ytd_cache = {}


def rpf_root(posix):
    p = posix.lower()
    i = p.rfind(".rpf/")
    return posix[:i + 4] if i >= 0 else None


def ytds_under(root):
    if root not in ytd_cache:
        ytd_cache[root] = [p for p in VPath(root).rglob("*") if p.name.lower().endswith(".ytd")]
    return ytd_cache[root]


for name in CANDIDATES:
    rec = {"name": name, "found": {}, "missing": []}
    try:
        h = by[name]
        rec["path"] = h["path"]
        want = [t for t in h.get("textures", []) if not t.lower().endswith(("_n", "_s")) and not t.lower().startswith(SKIP_TEX)]
        a = szio.try_load_asset(VPath(h["path"]))
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        dst = OUT / name
        dst.mkdir(parents=True, exist_ok=True)
        emb = d.shader_group.embedded_textures if d.shader_group else {}
        for t in list(want):
            if t in emb and emb[t].data is not None:
                (dst / f"{t}.dds").write_bytes(emb[t].data.read_bytes())
                rec["found"][t] = "embedded"
                want.remove(t)
        # external textures: look in the .ytd files of the same archive (the model's folder first)
        root = rpf_root(h["path"])
        if want and root:
            folder = h["path"].rsplit("/", 1)[0].lower()
            ytds = sorted(ytds_under(root), key=lambda p: 0 if p.as_posix().lower().startswith(folder) else 1)
            for y in ytds:
                if not want:
                    break
                try:
                    td = szio.try_load_asset(y)
                    texs = getattr(td, "textures", {}) or {}
                    for t in list(want):
                        tex = texs.get(t) or texs.get(t.lower())
                        if tex is not None and tex.data is not None:
                            (dst / f"{t}.dds").write_bytes(tex.data.read_bytes())
                            rec["found"][t] = y.as_posix()
                            want.remove(t)
                except Exception as e:
                    log["errors"].append(f"{y.name}: {e!r}"[:200])
        rec["missing"] = want
    except Exception:
        log["errors"].append(f"{name}: " + traceback.format_exc()[-300:])
    log["models"].append(rec)
    print("[gs_menus]", name, list(rec["found"]), "missing", rec["missing"], flush=True)
LOG.parent.mkdir(parents=True, exist_ok=True)
with open(LOG, "w", encoding="utf-8") as fh:
    json.dump(log, fh, indent=1)
print("GS_MENU_TEX_DONE models=%d textures=%d errors=%d" % (len(log["models"]), sum(len(m["found"]) for m in log["models"]),
                                                            len(log["errors"])))
