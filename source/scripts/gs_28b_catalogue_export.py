# LONG PIG — v0.2.1: internal reference copies of SHORTLISTED vanilla catalogue props (gs_28), for offline preview renders
# only (CodeWalker XML + their textures). The FiveM resource never contains these files: the MLO references the props
# by archetype name. Read-only access to the game archives.
# Blender 5.1 console on the PC (batch 1 = default; batch 2: type  GS_BATCH = 2  first):
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_28b_catalogue_export.py", encoding="utf-8").read())
# Output: reference_vanilla/catalogue/<name>.ydr.xml (+ <name>/<tex>.dds) and docs/_raw/vanilla_catalogue_export[_b2].json
import os, json, time, traceback
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
OUT = ROOT / "reference_vanilla" / "catalogue"
BATCH = int(globals().get("GS_BATCH", os.environ.get("GS_BATCH", "1")))
LOG = ROOT / "docs" / "_raw" / ("vanilla_catalogue_export.json" if BATCH == 1 else f"vanilla_catalogue_export_b{BATCH}.json")
PROPS = [
    # seating
    "ch_chint09_seating_booth", "bkr_prop_clubhouse_armchair_01a", "bkr_prop_clubhouse_sofa_01a", "bkr_prop_clubhouse_chair_01",
    "bkr_prop_clubhouse_chair_03", "prop_chair_03", "prop_chair_08", "m25_1_prop_m51_dinechair_01a", "hei_heist_din_chair_03",
    "bkr_prop_biker_barstool_02", "bkr_prop_biker_barstool_04", "v_club_bahbarstool", "lr_prop_clubstool_01",
    # tables
    "bkr_int02_table_01", "hei_heist_din_table_04",
    # lighting (most carry their own light definitions)
    "bkr_bar_lampshade01", "hei_heist_lit_lightpendant_003", "apa_mp_h_lit_lightpendant_01", "m25_2_int_01_l_mb_pendant_02",
    "m25_2_int_01_l_mb_pendant_003", "m25_2_int_01_l_din_ceil_lamp", "ch_prop_ch_lamp_ceiling_02b", "xm_prop_lab_ceiling_lampb",
    "m26_1_int_02_lamp_wall_008", "xm_prop_base_wall_lampa", "v_ret_gc_lamp", "v_39_halllampon", "bkr_int_02_lamp_no_mod",
    "bkr_prop_biker_ceiling_fan_base", "ch_chint02_picture_light",
    # decor
    "ch_prop_vault_painting_01a", "ch_prop_vault_painting_01c", "ch_prop_vault_painting_01e", "ex_office_swag_paintings01",
    "prop_ped_pic_01", "v_ret_gc_clock", "prop_game_clock_01", "prop_plant_int_01a", "prop_plant_int_03a", "prop_plant_fern_02a",
    "bkr_rec_flags", "ind_prop_dlc_flag_02",
]
PROPS2 = [
    # seating / tables (diner + family-restaurant families)
    "v_ret_fh_dinetable", "v_ret_fh_chair01", "v_ret_fh_kitchtable", "v_res_fa_chair01", "v_res_fa_chair02", "v_res_m_dinechair",
    "v_ret_gc_chair01", "v_ret_gc_chair02", "v_res_d_roundtable", "v_ret_tablesml", "v_ret_csr_table", "v_ret_ta_stool",
    # lighting: sconces, pendants, bulbs, fans
    "v_ret_fh_walllighton", "dt1_05_walllight", "prop_walllight_ld_01", "v_med_cor_walllight", "v_serv_metro_walllightcage",
    "xm3_int3_wall_picture_lamp", "bkr_prop_biker_pendant_light", "ch_prop_tunnel_hang_lamp", "hei_heist_lit_lightpendant_02",
    "m25_2_int_01_kit_pendant_001", "m25_2_int_01_mb_pendant005", "v_72_light_pendant", "prop_barebulb_01", "v_res_fa_lamp1on",
    "v_ret_gc_fan", "v_res_fa_fan",
    # heritage wall
    "prop_ped_pic_02", "prop_ped_pic_05", "prop_ped_pic_07", "v_med_wallpicture1", "v_med_wallpicture2", "v_ilev_trev_pictureframe",
    "m26_1_prop_m61_photo_01a", "m26_1_prop_m61_photoref_00a", "m26_1_int_01_frame_001", "v_res_m_statue",
    # table dressing and retail stock
    "prop_wine_bot_01", "prop_wine_red", "winerow", "prop_wine_glass", "prop_drink_redwine", "v_res_foodjara", "prop_metalfoodjar_01",
    "v_res_tt_plate01", "v_ret_fh_plate1", "v_ret_ml_6bottles", "v_ret_ml_liqshelfb", "v_ret_ml_tablea", "v_ret_247shelves01",
    "v_ret_fh_shelf_01", "v_ret_fh_displayc", "prop_bread_rack_01", "v_ret_gc_mugdisplay", "prop_food_napkin_01",
]
if BATCH == 2:
    PROPS = PROPS2

paths = {}
for h in json.load(open(ROOT / "docs" / "_raw" / "vanilla_catalogue_v021.json", encoding="utf-8"))["items"]:
    paths.setdefault(h["name"], h["path"])
for key in ("focus", "names"):
    for h in json.load(open(ROOT / "docs" / "_raw" / "vanilla_props_deli.json", encoding="utf-8")).get(key, []):
        if isinstance(h, dict) and h.get("path"):
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
    print("[gs_cat_x]", name, rec.get("min"), rec.get("max"), "missing", rec.get("missing_textures"), flush=True)
LOG.parent.mkdir(parents=True, exist_ok=True)
with open(LOG, "w", encoding="utf-8") as fh:
    json.dump(log, fh, indent=1)
print("GS_CAT_EXPORT_DONE props=%d errors=%d" % (len(log["props"]), len(log["errors"])))
