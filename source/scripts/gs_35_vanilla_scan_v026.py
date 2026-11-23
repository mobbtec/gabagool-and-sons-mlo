# LONG PIG — v0.2.6: read-only scan of the owner's installed GTA V for base-game / pre-2019 DLC prop archetypes that the
# v0.2.6 brief needs (ceiling fans, cleaning corner, extinguisher, vents, switches, mats, counter/deli prep items).
# Records names, archive paths and HIGH-LOD bounds; writes internal CodeWalker-XML copies of a short candidate list for
# OFFLINE preview renders only. Nothing is shipped: the MLO references props by archetype name.
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_35_vanilla_scan_v026.py", encoding="utf-8").read())
# Output: docs/_raw/vanilla_scan_v026.json (+ reference_vanilla/catalogue/<name>.ydr.xml for the preview list)
import os, json, time, traceback, re
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "reference_vanilla" / "catalogue"
LOG = ROOT / "docs" / "_raw" / "vanilla_scan_v026.json"
BUDGET_LIST = float(globals().get("GS_BUDGET_LIST", 480))
BUDGET_LOAD = float(globals().get("GS_BUDGET_LOAD", 300))
TOKENS = {"mop", "bucket", "broom", "dustpan", "wetfloor", "wet", "caution", "exting", "extinguisher", "fan", "blade", "blades",
          "vent", "aircon", "switch", "lightswitch", "doormat", "rubbermat", "slicer", "receipt", "receipts", "tongs", "bleach",
          "cleaner", "papertowel", "towel", "rag", "notepad", "clipboard", "calculator", "stapler", "spray", "squeegee",
          "dispenser", "soap", "sponge", "sink", "pen", "pencil", "tape", "cashtray", "mat", "grille", "grill", "diffuser"}
PREFIX = ("prop_", "v_ret_", "v_res_", "v_ind_", "v_ilev_", "v_serv_", "v_corp_", "v_med_", "v_club_", "bkr_prop_", "hei_prop_",
          "ex_prop_", "gr_prop_", "imp_prop_", "xm_prop_", "lr_prop_", "ba_prop_", "v_74_", "v_61_", "v_8_")
SKIP = ("_lod", "_slod", "_hi", "_dam", "_frag", "_proxy", "_emissive", "_ovr", "_decal", "_shadow", "_occl")
PREVIEW = ["bkr_prop_biker_ceiling_fan_base", "prop_outdoor_fan_01", "v_ret_gc_fan", "prop_fire_exting_1a", "prop_fire_exting_1b",
           "prop_cs_mop_s", "prop_cs_bucket_s", "prop_mop_bucket_01", "prop_bucket_01a", "prop_broom_01", "prop_tool_broom",
           "prop_wet_floor_sign_01", "prop_sign_wet_01", "v_ilev_light_switch", "prop_cs_dustpan", "prop_mat_box",
           # chosen for v0.2.6 (preview references)
           "v_serv_bktmop_h", "v_serv_wetfloorsn", "v_ind_cs_spray", "v_serv_switch_2", "v_ret_gc_pen1", "prop_notepad_02"]

t0 = time.time()
found = {}
archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
for base in (GTA / "update" / "x64" / "dlcpacks", GTA / "x64" / "dlcpacks"):
    if base.is_dir():
        for d in sorted(base.iterdir()):
            if d.name.lower().startswith(("mpbiker", "mpheist", "mplowrider", "mpexecutive", "mpimportexport", "mpgunrunning",
                                          "mpchristmas2017", "mpbattle", "patchday")) and (d / "dlc.rpf").is_file():
                archives.append(d / "dlc.rpf")
for a in archives:
    if time.time() - t0 > BUDGET_LIST:
        print("[gs35] list budget reached", flush=True)
        break
    try:
        for p in VPath(str(a)).rglob("*"):
            nm = p.name.lower()
            if not (nm.endswith(".ydr") or nm.endswith(".yft")):
                continue
            n = nm[:-4]
            if not n.startswith(PREFIX) or any(s in n for s in SKIP):
                continue
            toks = set(re.split(r"[_\d]+", n))
            if toks & TOKENS or any(k in n for k in ("mop", "bucket", "broom", "exting", "ceiling_fan", "wetfloor", "wet_floor",
                                                       "lightswitch", "light_switch", "doormat", "slicer", "receipt")):
                found.setdefault(n, p.as_posix())
    except Exception as e:
        print("[gs35] scan error", a.name, repr(e)[:160], flush=True)
    print("[gs35] scanned", a.name, "matches", len(found), round(time.time() - t0), "s", flush=True)

log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "props": [], "errors": [], "n_matches": len(found)}
OUT.mkdir(parents=True, exist_ok=True)
order = [n for n in PREVIEW if n in found] + sorted(n for n in found if n not in PREVIEW)
t1 = time.time()
for name in order:
    rec = {"name": name, "path": found[name]}
    if time.time() - t1 < BUDGET_LOAD:
        try:
            a = szio.try_load_asset(VPath(rec["path"]))
            d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
            lod = min(d.models.keys(), key=lambda k: int(k))
            P = np.concatenate([np.array(g.vertex_buffer["Position"], float).reshape(-1, 3) for m in d.models[lod] for g in m.geometries])
            rec["min"], rec["max"] = P.min(0).round(4).tolist(), P.max(0).round(4).tolist()
            rec["tris"] = int(sum(len(g.index_buffer) // 3 for m in d.models[lod] for g in m.geometries))
            rec["lights"] = len(d.lights or [])
            rec["textures"] = sorted({p.value for sh in (d.shader_group.shaders if d.shader_group else []) for p in sh.parameters
                                      if isinstance(p.value, str) and p.value})[:12]
            if name in PREVIEW and not (OUT / f"{name}.ydr.xml").exists():
                try:
                    szio.save_asset(d, [AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)], OUT, name)
                    rec["preview_xml"] = True
                except Exception as e:
                    log["errors"].append(f"cwxml {name}: {e!r}"[:300])
        except Exception:
            log["errors"].append(f"{name}: " + traceback.format_exc()[-300:])
    log["props"].append(rec)
log["not_found_preview"] = [n for n in PREVIEW if n not in found]
log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
LOG.write_text(json.dumps(log, indent=1), encoding="utf-8")
print("GS35_DONE matches=%d with_bounds=%d errors=%d secs=%d" % (len(found), sum(1 for p in log["props"] if p.get("min")),
                                                                 len(log["errors"]), time.time() - t0))
