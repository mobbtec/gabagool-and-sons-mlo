# LONG PIG — v0.2.3 "full lobby": locate base-game prop archetypes by name in the owner's installed GTA V (read-only),
# record bounds (for placement) and write internal CodeWalker-XML copies for OFFLINE preview renders only.
# The FiveM resource never contains these files: the MLO references the props by archetype name.
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_34_find_export_props.py", encoding="utf-8").read())
# Output: reference_vanilla/catalogue/<name>.ydr.xml (+ textures) and docs/_raw/vanilla_props_v023.json
import os, json, time, traceback
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "reference_vanilla" / "catalogue"
LOG = ROOT / "docs" / "_raw" / "vanilla_props_v023.json"
BUDGET_S = float(globals().get("GS_BUDGET_S", 900))
NAMES = [
    # ceiling / wall utilities (make the room read as a real, inspected business)
    "v_res_fa_smokealarm", "v_ilev_fib_sprklr", "prop_fire_exting_1a", "prop_fire_exting_2a", "v_res_tre_plugsocket",
    "prop_wall_light_09a", "v_ret_gc_clock",
    # 90s counter / customer stuff
    "prop_jukebox_01", "prop_jukebox_02", "prop_gumball_01", "prop_gumball_02", "prop_gumball_03", "prop_radio_01",
    "prop_paper_bag_01", "prop_paper_bag_small", "prop_cs_newspaper", "prop_ashtray_01", "v_res_mp_ashtraya", "v_ret_fh_ashtray",
    "prop_food_ketchup", "prop_food_mustard", "prop_bar_napkindisp", "prop_food_sugarjar", "v_ret_gc_cup", "v_res_mmug",
    "prop_coffee_cup_trailer", "v_res_tt_platepile", "v_res_foodjarb", "v_res_foodjarc", "prop_wine_white", "prop_wine_rose",
    "prop_bread_rack_02", "v_ret_247_bread1", "prop_cs_paper_cup",
    # banquette zone
    "v_res_d_roundtable", "v_res_m_dinechair", "v_ret_tablesml", "v_res_fa_chair01",
    # heritage wall
    "v_ilev_trev_pictureframe", "v_med_wallpicture1", "v_med_wallpicture2", "prop_ped_pic_01", "prop_ped_pic_02",
    "prop_ped_pic_05", "prop_ped_pic_07", "ch_prop_vault_painting_01a", "ch_prop_vault_painting_01c",
    # plants / floor
    "prop_plant_int_01b", "prop_plant_int_04a", "v_res_rubberplant", "prop_bin_08a", "prop_bin_05a", "prop_cs_bin_01",
    "v_ret_ml_fridge02", "prop_bar_fridge_03", "prop_crate_11a", "v_res_fh_crateopen",
    # matches the exterior awning (ATM / BEER & WINE) + 90s mini-market seating
    "prop_atm_01", "prop_atm_02", "prop_beer_neon_01", "prop_beer_neon_02", "prop_beer_neon_03", "prop_beer_neon_04",
    "prop_vend_soda_01", "prop_vend_soda_02", "prop_vend_coffe_01", "v_ret_gc_chair02", "v_ret_gc_chair01", "prop_bar_stool_01",
    "v_ret_ta_stool", "prop_chair_01a", "prop_chair_01b", "prop_till_02", "v_ret_247_cigs",
    # 0.2.5 style reset (internal preview references only)
    "prop_ped_pic_03", "prop_ped_pic_04", "prop_ped_pic_06", "prop_ped_pic_08", "prop_ped_pic_01_sm", "prop_ped_pic_03_sm",
    "prop_ped_pic_05_sm", "prop_ped_pic_06_sm", "prop_ped_pic_08_sm", "prop_cs_photoframe_01", "v_ret_gc_box2", "v_ret_box",
    "v_ret_ps_box_01", "prop_beer_box_01", "v_res_tt_can01", "v_res_tt_can02", "v_res_tt_can03", "prop_food_napkin_02",
    "prop_food_tray_01",
]
paths = {}
for f in ("vanilla_catalogue_v021.json", "vanilla_props_deli.json"):
    try:
        data = json.load(open(ROOT / "docs" / "_raw" / f, encoding="utf-8"))
        items = data.get("items", []) + data.get("focus", []) + data.get("names", [])
        for h in items:
            if isinstance(h, dict) and h.get("path"):
                paths.setdefault(h["name"].lower(), h["path"])
    except Exception:
        pass
t0 = time.time()
want = {n.lower() for n in NAMES if n.lower() not in paths}
print("[gs34] known paths", sum(n.lower() in paths for n in NAMES), "to search", len(want), flush=True)
if want:
    archives = sorted(GTA.glob("x64*.rpf")) + [GTA / "update" / "update.rpf"]
    for base in (GTA / "update" / "x64" / "dlcpacks", GTA / "x64" / "dlcpacks"):
        if base.is_dir():
            archives += sorted(base.glob("*/dlc.rpf"))
    for a in archives:
        if not want or time.time() - t0 > BUDGET_S:
            break
        try:
            for p in VPath(str(a)).rglob("*"):
                nm = p.name.lower()
                if not (nm.endswith(".ydr") or nm.endswith(".yft")):
                    continue
                n = nm[:-4]
                if n in want:
                    paths[n] = p.as_posix()
                    want.discard(n)
        except Exception as e:
            print("[gs34] scan error", a.name, repr(e)[:160], flush=True)
        print("[gs34] scanned", a.name, "left", len(want), round(time.time() - t0), "s", flush=True)

log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "props": [], "not_found": sorted(want), "errors": []}
OUT.mkdir(parents=True, exist_ok=True)
DONE = set()
try:
    for p in json.load(open(LOG, encoding="utf-8"))["props"]:
        if p.get("min"):
            DONE.add(p["name"])
except Exception:
    pass
for name in NAMES:
    rec = {"name": name, "path": paths.get(name.lower())}
    if not rec["path"]:
        log["props"].append(rec)
        continue
    try:
        a = szio.try_load_asset(VPath(rec["path"]))
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        if not (OUT / f"{name}.ydr.xml").exists():
            try:
                szio.save_asset(d, [AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)], OUT, name)
            except Exception as e:
                log["errors"].append(f"cwxml {name}: {e!r}"[:300])
        lod = min(d.models.keys(), key=lambda k: int(k))
        P = np.concatenate([np.array(g.vertex_buffer["Position"], float).reshape(-1, 3) for m in d.models[lod] for g in m.geometries])
        rec["min"], rec["max"] = P.min(0).round(4).tolist(), P.max(0).round(4).tolist()
        rec["lights"] = len(d.lights or [])
        rec["tris"] = int(sum(len(g.index_buffer) // 3 for m in d.models[lod] for g in m.geometries))
        tdir = OUT / name
        tdir.mkdir(parents=True, exist_ok=True)
        emb = d.shader_group.embedded_textures if d.shader_group else {}
        for t, tex in (emb or {}).items():
            if tex.data is not None:
                (tdir / f"{t}.dds").write_bytes(tex.data.read_bytes())
        rec["textures"] = sorted({p.value for sh in (d.shader_group.shaders if d.shader_group else []) for p in sh.parameters
                                  if isinstance(p.value, str) and p.value})
    except Exception:
        log["errors"].append(f"{name}: " + traceback.format_exc()[-300:])
    log["props"].append(rec)
    print("[gs34]", name, rec.get("min"), rec.get("max"), flush=True)
log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
LOG.write_text(json.dumps(log, indent=1), encoding="utf-8")
print("GS34_DONE found=%d not_found=%d errors=%d" % (sum(1 for p in log["props"] if p.get("min")), len(log["not_found"]),
                                                       len(log["errors"])))
