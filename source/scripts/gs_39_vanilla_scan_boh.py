# LONG PIG — v0.2.8: read-only scan for the BACK OF HOUSE (kitchen, restroom, storage, office)  [from gs_35 / gs_37]
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
LOG = ROOT / "docs" / "_raw" / "vanilla_scan_boh.json"
BUDGET_LIST = float(globals().get("GS_BUDGET_LIST", 480))
BUDGET_LOAD = float(globals().get("GS_BUDGET_LOAD", 420))
TOKENS = {"cooker", "griddle", "grill", "fryer", "oven", "hob", "stove", "hood", "extractor", "sink", "tap", "faucet", "fridge",
          "freezer", "kitch", "kitchen", "pot", "pan", "pans", "ladel", "ladle", "colander", "toilet", "urinal", "basin", "mirror",
          "soap", "towel", "handdry", "dryer", "toiletroll", "brush", "bin", "bins", "shelf", "shelves", "rack", "racks", "boxpile",
          "cardbox", "cardbordbox", "crate", "crates", "pallet", "sacktruck", "trolley", "trolly", "desk", "filecab", "cabinet",
          "safe", "phone", "calendar", "lamp", "monitor", "keyboard", "coathook", "jacket", "clipboard", "folder", "fusebox",
          "boiler", "heater", "sack", "flour", "spray", "bleach", "detergent", "register", "micro", "microwave", "toaster",
          "counter", "worktop", "steel", "drain", "dish", "dishes", "rubbergloves"}
PREFIX = ("ng_proc_", "prop_", "v_ret_", "v_res_", "v_ind_", "v_ilev_", "v_serv_", "v_corp_", "v_med_", "v_club_", "bkr_prop_", "hei_prop_",
          "ex_prop_", "gr_prop_", "imp_prop_", "xm_prop_", "lr_prop_", "ba_prop_", "v_74_", "v_61_", "v_8_")
SKIP = ("_lod", "_slod", "_hi", "_dam", "_frag", "_proxy", "_emissive", "_ovr", "_decal", "_shadow", "_occl")
PREVIEW = ["prop_ff_sink_01", "prop_ff_sink_02", "prop_ff_counter_01", "prop_ff_counter_02", "prop_ff_counter_03", "prop_ff_shelves_01",
           "prop_ff_noodle_01", "prop_ff_noodle_02", "prop_chip_fryer", "prop_griddle_01", "prop_griddle_02", "prop_cooker_03",
           "prop_kitch_pot_lrg", "prop_kitch_pot_huge", "prop_kitch_pot_med", "prop_kitch_pot_sm", "prop_kitch_pot_fry", "prop_ladel",
           "prop_kitch_juicer", "prop_micro_01", "prop_micro_02", "prop_toaster_01", "prop_toaster_02", "prop_bar_sink_01",
           "prop_fridge_01", "prop_fridge_03", "prop_bar_fridge_01", "prop_bar_fridge_03", "prop_trailr_fridge", "v_ret_ml_fridge",
           "prop_toilet_01", "prop_toilet_02", "prop_toilet_03", "prop_sink_02", "prop_sink_04", "prop_sink_05", "prop_sink_06",
           "prop_toilet_roll_01", "prop_toilet_roll_02", "prop_toilet_roll_05", "prop_toilet_brush_01", "prop_toilet_soap_01",
           "prop_toilet_soap_02", "prop_handdry_01", "prop_handdry_02", "prop_towel_rail_02", "prop_bin_05a", "prop_bin_07a",
           "prop_bin_08open", "prop_cs_bin_01", "prop_cs_bin_02", "prop_cs_bin_03", "prop_boxpile_01a", "prop_boxpile_02b",
           "prop_boxpile_06a", "prop_cardbordbox_02a", "prop_cardbordbox_03a", "prop_cardbordbox_04a", "prop_cs_cardbox_01",
           "prop_sacktruck_01", "prop_sacktruck_02a", "prop_box_wood01a", "prop_box_wood02a", "prop_office_desk_01", "prop_off_chair_01",
           "prop_off_chair_03", "prop_off_chair_04", "prop_off_chair_05", "prop_monitor_01a", "prop_monitor_01b", "prop_monitor_02",
           "prop_keyboard_01a", "prop_office_phone_tnt", "prop_cs_documents_01", "prop_ld_int_safe_01", "p_v_43_safe_s", "v_res_filebox",
           "prop_fire_exting_1a", "v_ind_cs_toolboard", "v_ret_csr_bin", "prop_ff_shelves_01", "prop_rub_cabinet01", "prop_rub_cabinet02",
           "v_ind_cfbox", "v_ind_cfbox2", "prop_paper_box_01", "v_res_tre_officechair", "prop_cleaning_trolly", "prop_mop_bucket_01a",
           "v_med_cor_filingcab", "v_corp_filecablow", "v_corp_offchair", "v_res_desklamp", "prop_desk_lamp_01"]

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
        print("[gs39] list budget reached", flush=True)
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
            if toks & TOKENS or n in PREVIEW:
                found.setdefault(n, p.as_posix())
    except Exception as e:
        print("[gs39] scan error", a.name, repr(e)[:160], flush=True)
    print("[gs39] scanned", a.name, "matches", len(found), round(time.time() - t0), "s", flush=True)

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
print("GS39_DONE matches=%d with_bounds=%d errors=%d secs=%d" % (len(found), sum(1 for p in log["props"] if p.get("min")),
                                                                 len(log["errors"]), time.time() - t0))
