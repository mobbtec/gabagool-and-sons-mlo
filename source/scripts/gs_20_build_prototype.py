# LONG PIG (resource gabagool_sons_mlo) — build v0.2.1-hero (Premium revision: Hero Zones A + B, art direction V2/V3)
#   0.2.1: gs_slice_furniture replaced by gs_v021_hall (gs_v021_kit.py): wall joinery kit (baseboard, frame-and-panel
#   wainscot, cap/picture rails, cornice), coffered ceiling + counter soffit with practical fixtures, rebuilt booths and
#   tables, curved-glass deli cases with sculpted food, hanging salumi rail, slicer, tricolore flag; lights matched to
#   fixtures; vanilla props by archetype name (fans, enamel pendants, sconces, wine, plates, frames, clock, stools ...)
#   0.2.0: CC0 PBR materials (normal_spec: floor checker, plaster, walnut, ceiling tiles), partitions P1 / P2,
#   furniture drawable gs_slice_furniture (3 burgundy booths, 2 deli cases, register / coffee bar / gate, back counter,
#   meat rail, pendants + globes, 8 extra lights), furniture collision, vanilla props by archetype name (till, scale,
#   espresso machine, bread, condiments, stools, "Today's Specials" menus + blank chalkboard) — gs_slice_geometry.py
#   transparent storefront W1 + window W2 + entrance D1 (0.1.x), 0.1.4: stickers removed, frames aligned,
#   back doors D2 / D3 working, MLO wall collision on the visible faces, vertex colours against the night glow
#   0.1.5: all door leaves are vanilla GTA V door models referenced by archetype name (v_ilev_csr_door_l/_r at D1,
#   prop_map_door_01 at D2, prop_sc1_12_door at D3) — our own door drawables are gone; casings, stools, tiled landings
#   0.1.6: D3 = prop_map_door_01; overrides of sc1_14_grnd_02.ydr (decals inside the shop cut away) and of the block
#   occluder sc1_occl_01 / hei_sc1_occl_01 / lr_sc1_occl_01.ymap (the shop's street faces removed)
# Runs INSIDE Blender 5.1 + Sollumz 2.9.0:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_20_build_prototype.py", encoding="utf-8").read())
#
# A. vanilla overrides (from the raw files extracted with CodeWalker; the game archives are never touched):
#      sc1_14_build2.ydr, sc1_14_sc1_emissive_sc1_14b.ydr, sc1_14_0.ybn, hi@sc1_14_0.ybn
# B. minimal MLO "gs_longpig_int": shell (floor, walls, ceiling, reveals, interior frames), glass W1/W2,
#    4 vanilla door entities (by name), MLO collision with room id, rooms/portals, YTYP + YMAP instance
# C. export (Native gen8 when PyMateria is available, else CodeWalker XML), reload every file, check it
# D. assemble the FiveM resource build/gabagool_sons_mlo and write docs/_raw/prototype_build_result.json
import bpy, bmesh, os, sys, json, math, importlib, datetime, traceback, shutil
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
SCRIPTS = ROOT / "source" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import gs_overrides as G
import gs_proto_geometry as PG
importlib.reload(G)
importlib.reload(PG)
import gs_slice_geometry as SG
importlib.reload(SG)
import gs_v021_kit as K021
importlib.reload(K021)
import gs_v023_vb
importlib.reload(gs_v023_vb)
import gs_v023_kit as K023                               # 0.2.3: 90s lobby rebuild (no wood), reuses the 0.2.1 primitives
importlib.reload(K023)
import gs_v024_kit as K024                               # 0.2.4 lounge (only its globe pendant is reused by 0.2.5)
importlib.reload(K024)
import gs_v025_vb
importlib.reload(gs_v025_vb)
import gs_v025_kit as K025                               # 0.2.5: STYLE RESET (docs/style_reset), re-exports the 0.2.3 kit
importlib.reload(K025)
import gs_v026_vb
importlib.reload(gs_v026_vb)
import gs_v026_kit as K026                               # 0.2.6: finish-and-refine pass (owner brief v0.2.6), built on 0.2.5
importlib.reload(K026)
import gs_v027_vb
importlib.reload(gs_v027_vb)
import gs_v027_kit as K027                               # 0.2.7: owner's in-game feedback (night light, mat, litter, ...)
importlib.reload(K027)
import gs_v028_vb
importlib.reload(gs_v028_vb)
import gs_boh_kit
importlib.reload(gs_boh_kit)
import gs_v028_kit as K                                  # 0.2.8: back of house (kitchen, storage, cooler, rooms, WC)
importlib.reload(K)
import gs_v029_vb
importlib.reload(gs_v029_vb)
import gs_boh29_kit
importlib.reload(gs_boh29_kit)
import gs_v029_kit                                       # 0.2.9: premium final pass (doors, kitchen, After Hours, details)
importlib.reload(gs_v029_kit)
K = importlib.import_module(os.environ.get("GS_KIT", "gs_v029_kit"))
if getattr(K, "STREET", False):                          # 0.3.0: taco kiosk + signs removed (gs_overrides, STREET section)
    G.enable_street()
HALL = "gs_v021_hall"                                    # drawable name kept (ytyp / server file names unchanged)
# 0.2.1: the two old ceiling points of the hall are replaced by fixture-matched lights (K.lights); back rooms keep theirs
SHELL_LIGHTS = [p for p in PG.LIGHTS if p[0] > SG.P1_S[1] or p[1] > SG.P2_T[1]]
SMALL_PROPS = ("prop_food_", "prop_bar_napkin", "prop_cleaver", "v_res_fa_", "prop_wine", "prop_drink", "v_ret_fh_plate",
               "prop_metalfoodjar", "v_res_foodjar", "winerow", "prop_knife", "v_ret_ml_scale",
               # 0.2.3 dressing
               "v_ret_gc_cup", "v_res_mmug", "prop_cs_paper_cup", "v_res_mp_ashtray", "prop_paper_bag", "v_ilev_fib_sprklr",
               "v_res_tre_plugsocket", "prop_ped_pic", "v_res_tt_platepile", "prop_radio_01",
               # 0.2.5 cashier wall supplies
               "v_res_tt_can", "v_ret_gc_box2", "prop_food_napkin", "prop_food_tray", "prop_cs_photoframe",
               "prop_beer_box", "v_ret_ml_6bottles",
               # 0.2.6 till / service details
               "v_ret_gc_pen", "prop_notepad", "v_ind_cs_spray", "v_serv_switch",
               # 0.2.7 floor litter
               "ng_proc_", "v_res_tt_litter",
               # 0.2.8 back of house small items
               "prop_kitch_pot", "prop_ladel", "prop_micro", "prop_keyboard", "prop_office_phone", "v_res_desklamp",
               "prop_cd_folder", "prop_cs_documents", "v_ret_csr_bin", "prop_toilet_roll", "prop_toilet_brush", "prop_handdry",
               "prop_soap_disp", "prop_coathook", "v_club_roc_jacket", "v_ind_cfbox", "prop_paper_box", "prop_fib_clipboard",
               "v_serv_metro_walllightcage")

import szio
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion, is_provider_available
from szio.gta5.bounds import BoundVertex, BoundPrimitive, BoundPrimitiveType

NATIVE = is_provider_available(AssetFormat.NATIVE)
FMT = AssetFormat.NATIVE if NATIVE else AssetFormat.CWXML
TARGET = [AssetTarget(FMT, AssetVersion.GEN8)]
EXT = "" if NATIVE else ".xml"

BUILD = ROOT / "build" / "prototype"
EXPORT = BUILD / ("export_native" if NATIVE else "export_cwxml")
OVR = BUILD / ("vanilla_override_native" if NATIVE else "vanilla_override_cwxml")
RES = ROOT / "build" / "gabagool_sons_mlo"
FIVEM_SRC = ROOT / "source" / "fivem" / "gabagool_sons_mlo"
TEX = ROOT / "source" / "textures" / "proto"
TEX_SLICE = ROOT / "source" / "textures" / "slice"       # 0.2.0: CC0-derived + original slice textures (gs_14)
TEX_V021 = ROOT / "source" / "textures" / "v021"         # 0.2.1: CC0-derived + original hero-kit textures (gs_15)
TEX_V023 = ROOT / "source" / "textures" / "v023"         # 0.2.3: CC0 Tiles010 / PaintedBricks004 + original 90s lobby set (gs_15c)
TEX_V025 = ROOT / "source" / "textures" / "v025"         # 0.2.5: aged / faded derivatives + original notices & wear decals (gs_15g)
TEX_V026 = ROOT / "source" / "textures" / "v026"         # 0.2.6: floor A 4 m, troffer lenses, blinds, decals, wall story (gs_15i)
TEX_V027 = ROOT / "source" / "textures" / "v027"         # 0.2.7: logo mat, signs / labels atlas, leaks, puddles, 512 laminates (gs_15k)
TEX_V029 = ROOT / "source" / "textures" / "v029"         # 0.2.9: lp8 atlas (signs, neon, tickets, ledgers, cartons) (gs_15n)
RAW = ROOT / "docs" / "_raw"
BLEND = ROOT / "source" / "blender" / "prototype"
for d in (EXPORT, OVR, RAW, BLEND):
    d.mkdir(parents=True, exist_ok=True)

MLO_NAME = "gs_longpig_int"
YTYP_NAME = "gabagool_sons_mlo"
YMAP_NAME = "gs_longpig_int_milo_"          # vanilla / CodeWalker convention for MLO placement ymaps
ENT_FLAGS_SHADOWS = 1572864                  # cast static + dynamic shadows (as in the working MLOs on the server)
MLO_POS = (float(G.O2[0]), float(G.O2[1]), G.FLOOR_Z)
MLO_YAW = math.radians(G.YAW_DEG)

SZ = next(n for n in bpy.context.preferences.addons.keys() if n.split(".")[-1] == "sollumz")


def M(sub):
    return importlib.import_module(f"{SZ}.{sub}")


P = M("sollumz_properties"); SollumType = P.SollumType; ArchetypeType = P.ArchetypeType; LightType = P.LightType
bh = M("tools.blenderhelper"); dh = M("tools.drawablehelper"); boh = M("tools.boundhelper")
mh = M("tools.meshhelper"); shm = M("ydr.shader_materials"); colm = M("ybn.collision_materials")
matops = M("ydr.operators.materials")
get_maps = M("ymap_next.properties.map").get_maps

R = {"timestamp": datetime.datetime.now().isoformat(timespec="seconds"), "blender": bpy.app.version_string,
     "sollumz_module": SZ, "format": FMT.name, "root": str(ROOT), "steps": [], "errors": []}


def step(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    print(("PASS " if ok else "FAIL ") + name, json.dumps(kw, default=str)[:1200] if kw else "")
    return ok


# ======================================================================== A. vanilla overrides
def vanilla_path(fn):
    if NATIVE:
        return ROOT / "reference_vanilla" / "sc1_14" / fn
    return ROOT / "reference_vanilla" / "xml" / (fn + ".xml")


def load(path):
    a = szio.try_load_asset(path)
    if a is None:
        raise RuntimeError(f"cannot load {path}")
    return a


def build_overrides():
    rep = {}
    for f in OVR.iterdir():
        if f.is_file():
            f.unlink()
    # --- sc1_14_build2.ydr
    src = vanilla_path("sc1_14_build2.ydr")
    d = load(src)
    before = G.drawable_stats(d)
    tex_before = G.texture_fingerprints(d)
    sel, selrep = G.select(d, G.ENT_BUILD2, G.BUILD2_RULES)
    per = G.remove_triangles(d, sel)
    dropped = G.drop_empty_geometries(d)
    szio.save_asset(d, TARGET, OVR, "sc1_14_build2")
    d2 = load(OVR / ("sc1_14_build2.ydr" + EXT))
    after = G.drawable_stats(d2)
    tex_cmp = G.compare_textures(tex_before, G.texture_fingerprints(d2))
    size_src, size_out = src.stat().st_size, (OVR / ("sc1_14_build2.ydr" + EXT)).stat().st_size
    left = {k: 0 for k in G.BUILD2_RULES}
    for rec in G.tri_records(d2, G.ENT_BUILD2):
        for k, rule in G.BUILD2_RULES.items():
            if rule["test"](rec):
                left[k] += 1
    by_b = {g["shader"]: g for g in before["geometries"]}
    by_a = {g["shader"]: g for g in after["geometries"]}
    untouched_ok = all(by_a.get(sh, {}).get("tris") == g["tris"] and by_a.get(sh, {}).get("verts") == g["verts"]
                       for sh, g in by_b.items() if f"g{g['geom']}" not in per)
    rep["sc1_14_build2"] = {"source": str(src), "selection": selrep, "per_geometry": per, "dropped_geometries": dropped,
                            "geoms": [len(before["geometries"]), len(after["geometries"])],
                            "tris": [sum(g["tris"] for g in before["geometries"]), sum(g["tris"] for g in after["geometries"])],
                            "embedded_textures": [before["embedded_textures"], after["embedded_textures"]],
                            "shaders": [before["shaders"], after["shaders"]], "left_after_reload": left,
                            "textures": tex_cmp, "file_size": [size_src, size_out]}
    tex_ok = not tex_cmp["differences"] and not tex_cmp["extra"] and (not NATIVE or tex_cmp["with_data"] == tex_cmp["compared"])
    size_ok = (not NATIVE) or (0.8 < size_out / size_src < 1.25)
    step("override_build2", sum(left.values()) == 0 and untouched_ok and before["embedded_textures"] == after["embedded_textures"] and tex_ok and size_ok
         and rep["sc1_14_build2"]["tris"][0] - rep["sc1_14_build2"]["tris"][1] == G.BUILD2_REMOVED_TRIS, **rep["sc1_14_build2"])

    # --- sc1_14_sc1_emissive_sc1_14b.ydr
    src = vanilla_path("sc1_14_sc1_emissive_sc1_14b.ydr")
    e = load(src)
    eb = G.drawable_stats(e)
    etex_before = G.texture_fingerprints(e)
    sel, selrep = G.select(e, G.ENT_BUILD2, G.EMISSIVE_RULES)
    per = G.remove_triangles(e, sel)
    dropped = G.drop_empty_geometries(e)
    szio.save_asset(e, TARGET, OVR, "sc1_14_sc1_emissive_sc1_14b")
    e2 = load(OVR / ("sc1_14_sc1_emissive_sc1_14b.ydr" + EXT))
    ea = G.drawable_stats(e2)
    etex = G.compare_textures(etex_before, G.texture_fingerprints(e2))
    rep["sc1_14_sc1_emissive_sc1_14b"] = {"source": str(src), "selection": selrep, "per_geometry": per, "dropped_geometries": dropped,
                                          "geoms": [len(eb["geometries"]), len(ea["geometries"])],
                                          "tris": [sum(g["tris"] for g in eb["geometries"]), sum(g["tris"] for g in ea["geometries"])],
                                          "textures": etex}
    step("override_emissive", rep["sc1_14_sc1_emissive_sc1_14b"]["tris"][0] - rep["sc1_14_sc1_emissive_sc1_14b"]["tris"][1] == sum(r_["expect"] for r_ in G.EMISSIVE_RULES.values())
         and not etex["differences"] and (not NATIVE or etex["with_data"] == etex["compared"]),
         **rep["sc1_14_sc1_emissive_sc1_14b"])

    # --- sc1_14_0.ybn (mover)
    src = vanilla_path("sc1_14_0.ybn")
    b_orig = load(src)
    b = load(src)
    pre = G.doorway_clear_check(b, "mover before")
    info = G.edit_mover_bound(b, BoundVertex, BoundPrimitive, BoundPrimitiveType)
    if G.STREET_ON:
        info["kiosk"] = G.kiosk_bound_edit(b, BoundVertex, BoundPrimitive, BoundPrimitiveType)
    szio.save_asset(b, TARGET, OVR, "sc1_14_0")
    b2 = load(OVR / ("sc1_14_0.ybn" + EXT))
    if G.STREET_ON:
        info["kiosk"]["after_reload"] = G.kiosk_left(b2)
        step("override_mover_kiosk", info["kiosk"]["after_reload"]["left"] == 0
             and info["kiosk"]["after_reload"]["cap_boxes"] == info["kiosk"]["cap_boxes"], **info["kiosk"])
    post = G.doorway_clear_check(b2, "mover after")
    vol = G.verify_mover_split(b_orig, b2, info)
    back = G.back_doors_clear_check(b2, "mover after")
    back_pre = G.back_doors_clear_check(b_orig, "mover before")
    rep["sc1_14_0"] = {"source": str(src), "edit": info, "children": [G.bound_stats(b_orig), G.bound_stats(b2)],
                       "doorway_before": pre, "doorway_after": post, "volume_check": vol, "back_doors_before": back_pre,
                       "back_doors_after": back}
    step("override_mover_ybn", not post["blocking_boxes"] and pre["blocking_boxes"] and vol["wall_still_solid"] and vol["doorway_free"]
         and not back["D2"]["blocking_boxes"] and not back["D3"]["blocking_boxes"]
         and bool(back_pre["D2"]["blocking_boxes"]) and bool(back_pre["D3"]["blocking_boxes"]),
         **{k: v for k, v in rep["sc1_14_0"].items() if k != "children"})

    # --- hi@sc1_14_0.ybn (weapon)
    src = vanilla_path("hi@sc1_14_0.ybn")
    h = load(src)
    hb = G.bound_stats(h)
    pre = G.doorway_clear_check(h, "weapon before")
    info = G.edit_weapon_bound(h, BoundVertex)
    if G.STREET_ON:
        info["kiosk"] = G.kiosk_bound_edit(h, BoundVertex, BoundPrimitive, BoundPrimitiveType)
    szio.save_asset(h, TARGET, OVR, "hi@sc1_14_0")
    h2 = load(OVR / ("hi@sc1_14_0.ybn" + EXT))
    if G.STREET_ON:
        info["kiosk"]["after_reload"] = G.kiosk_left(h2)
        step("override_weapon_kiosk", info["kiosk"]["after_reload"]["left"] == 0
             and info["kiosk"]["after_reload"]["cap_boxes"] == info["kiosk"]["cap_boxes"], **info["kiosk"])
    post = G.doorway_clear_check(h2, "weapon after")
    back = G.back_doors_clear_check(h2, "weapon after")
    rep["hi@sc1_14_0"] = {"source": str(src), "edit": info, "children": [hb, G.bound_stats(h2)], "doorway_before": pre, "doorway_after": post,
                          "back_doors_after": back}
    step("override_weapon_ybn", not post["blocking_boxes"] and bool(pre["blocking_boxes"])
         and not back["D2"]["blocking_boxes"] and not back["D3"]["blocking_boxes"],
         **{k: v for k, v in rep["hi@sc1_14_0"].items() if k != "children"})

    # --- 0.1.6: sc1_14_grnd_02.ydr — ground decal / sidewalk pieces inside the shop floor polygon cut away
    src = ROOT / "reference_vanilla" / "sc1_14" / "sc1_14_grnd_02.ydr"
    if NATIVE and src.is_file():
        gd = load(src)
        gb = G.drawable_stats(gd)
        gtex = G.texture_fingerprints(gd)
        poke_before = G.surface_above_floor(gd, G.ENT_GRND02, PG.FLOOR_POLY, 0.013)
        per = G.clip_out_polygon(gd, G.ENT_GRND02, PG.FLOOR_POLY)
        if G.STREET_ON:
            per["kiosk_pad"] = G.add_kiosk_pad(gd, G.ENT_GRND02)
            per["patio_retile"] = G.retile_patio(gd, G.ENT_GRND02)
            per["patio_tarmac_clip"] = G.clip_tarmac_to_tile(gd, G.ENT_GRND02)
            per["kerb_ext"] = G.extend_kerb(gd, G.ENT_GRND02)                   # 0.3.1-l: kerb on to the fence
            per["kerb_run2"] = G.add_kerb_run(gd, G.ENT_GRND02)                 # 0.3.1-m: kerb at the parking hatch edge
        szio.save_asset(gd, TARGET, OVR, "sc1_14_grnd_02")
        gd2 = load(OVR / "sc1_14_grnd_02.ydr")
        poke_after = G.surface_above_floor(gd2, G.ENT_GRND02, PG.FLOOR_POLY, 0.013)
        gcmp = G.compare_textures(gtex, G.texture_fingerprints(gd2))
        ga = G.drawable_stats(gd2)
        rep["sc1_14_grnd_02"] = {"source": str(src), "per_geometry": per, "poke_samples_before": poke_before,
                                 "poke_samples_after": poke_after, "geoms": [len(gb["geometries"]), len(ga["geometries"])],
                                 "textures": gcmp, "file_size": [src.stat().st_size, (OVR / "sc1_14_grnd_02.ydr").stat().st_size]}
        step("override_grnd02", poke_before[0] > 0 and poke_after[0] == 0 and len(gb["geometries"]) == len(ga["geometries"])
             and not gcmp["differences"] and not gcmp["extra"], **rep["sc1_14_grnd_02"])
    else:
        step("override_grnd02", not NATIVE, skipped="dry run without the extracted source" if not NATIVE else f"missing {src}")

    # --- 0.1.6: block occluder — remove the shop's street faces (W1/D2 facade, D1 chamfer, W2/D3 facade)
    for nm in ("sc1_occl_01", "hei_sc1_occl_01", "lr_sc1_occl_01"):
        src = ROOT / "reference_vanilla" / "sc1_14" / f"{nm}.ymap"
        if not (NATIVE and src.is_file()):
            step(f"override_{nm}", not NATIVE, skipped="dry run without the extracted source" if not NATIVE else f"missing {src}")
            continue
        md = load(src)
        nb, nm_ = len(md.box_occluders), len(md.model_occluders)
        tri_before = [len(np.asarray(m.indices).reshape(-1, 3)) for m in md.model_occluders]
        cut = G.cut_shop_occluder(md)
        kio = {"model_tris_removed": 0, "boxes_removed": 0}
        if G.STREET_ON:
            try:
                kio = G.cut_kiosk_occluder(md)
            except Exception as e:
                kio = {"model_tris_removed": 0, "boxes_removed": 0, "error": repr(e)}
        szio.save_asset(md, TARGET, OVR, nm)
        md2 = load(OVR / f"{nm}.ymap")
        tri_after = [len(np.asarray(m.indices).reshape(-1, 3)) for m in md2.model_occluders]
        ok = (len(cut) == 1 and len(cut[0]["removed"]) == 6 and len(md2.box_occluders) == nb - kio["boxes_removed"]
              and len(md2.model_occluders) == nm_
              and sum(tri_before) - sum(tri_after) == 6 + kio["model_tris_removed"] and len(md2.entities) == len(md.entities))
        rep[nm] = {"source": str(src), "cut": cut, "kiosk_occluder": kio, "boxes": [nb, len(md2.box_occluders)], "models": [nm_, len(md2.model_occluders)],
                   "tris": [sum(tri_before), sum(tri_after)], "file_size": [src.stat().st_size, (OVR / f"{nm}.ymap").stat().st_size]}
        step(f"override_{nm}", ok, **rep[nm])
    # --- 0.3.1: roof billboard of the shop -> LONG PIG (own texture in the vanilla quad)
    bb_dds = ROOT / "source" / "textures" / "v031" / "lp_billboard.dds"
    for nm in ("sc1_14_bb_meltdown",):      # sc1_14_bb_mollis (old-billboard IPL) has no embedded texture - not touched
        src = ROOT / "reference_vanilla" / "sc1_14" / f"{nm}.ydr"
        if not (NATIVE and G.STREET_ON and src.is_file() and bb_dds.is_file()):
            continue
        try:
            d = load(src)
            info = G.retexture_billboard(d, bb_dds, 1024, 512)
            szio.save_asset(d, TARGET, OVR, nm)
            d2 = load(OVR / (nm + ".ydr" + EXT))
            fp = G.texture_fingerprints(d2) if hasattr(G, "texture_fingerprints") else {}
            info["after"] = {k: [v[0], v[1], v[2]] for k, v in fp.items()}
            ok = bool(fp) and all(v[0] == 1024 and v[1] == 512 and v[2] > 100000 for v in fp.values())
        except Exception as e:
            info, ok = {"error": repr(e)}, False
        rep[nm] = info
        step(f"override_{nm}", ok, **info)
    # --- 0.3.1-h: far view of the roof billboard - the LOD texture dictionaries get the LONG PIG picture too
    # (every ~2:1 texture is replaced by the own picture at the same size; informative step, never blocks the build)
    lod_dir = ROOT / "source" / "textures" / "v031" / "lod"
    for nm in ("sc1_14_nbill_lod", "sc1_14_nbill_slod"):
        src = ROOT / "reference_vanilla" / "sc1_14" / f"{nm}.ytd"
        if not (NATIVE and G.STREET_ON and src.is_file() and lod_dir.is_dir()):
            continue
        info = {"textures": [], "replaced": []}
        try:
            import dataclasses as _dc
            y = load(src)
            for tn in list(y.textures):
                tx = y.textures[tn]
                w, h = int(tx.width), int(tx.height)
                info["textures"].append([tn, w, h])
                f = lod_dir / f"lp_billboard_{w}x{h}.dds"
                if h and 1.8 <= w / h <= 2.2 and f.is_file():
                    raw = f.read_bytes()
                    ds = type(tx.data)(getattr(tx.data, "name", None) or (tn + ".dds"), raw)
                    try:
                        y.textures[tn] = _dc.replace(tx, data=ds)
                    except Exception:
                        tx.data = ds
                    info["replaced"].append(tn)
            if info["replaced"]:
                szio.save_asset(y, TARGET, OVR, nm)
                y2 = load(OVR / (nm + ".ytd" + EXT))
                info["after"] = [[k, int(v.width), int(v.height)] for k, v in y2.textures.items()]
        except Exception as e:
            info["error"] = repr(e)
        rep[nm] = info
        step(f"override_{nm}", True, **info)
    return rep


# ======================================================================== B. MLO scene
def new_scene(name):
    if not bpy.app.background and bpy.context.window is not None:
        sc = bpy.data.scenes.new(name)
        bpy.context.window.scene = sc
    else:
        bpy.ops.wm.read_homefile(use_empty=True)
        sc = bpy.context.scene
        sc.name = name
    sc.unit_settings.system = "METRIC"
    return sc


def colmat(name, room_id=0):
    for i, m in enumerate(colm.collisionmats):
        if m.name == name:
            mat = colm.create_collision_material_from_index(i)
            mat.collision_properties.room_id = room_id
            return mat
    raise KeyError(name)


def image(name):
    p = ROOT / "source" / "textures" / "v170" / f"{name}.dds"     # 1.7.0: half-size copies (top mip dropped) of small-area textures
    if (ROOT / "source" / "textures" / "v180" / f"{name}.dds").is_file():
        p = ROOT / "source" / "textures" / "v180" / f"{name}.dds"   # 1.8.0: own sign / price-tag atlas
    if (ROOT / "source" / "textures" / "v190" / f"{name}.dds").is_file():
        p = ROOT / "source" / "textures" / "v190" / f"{name}.dds"   # 1.9.0: counter stone, case glass
    if (ROOT / "source" / "textures" / "v200" / f"{name}.dds").is_file():
        p = ROOT / "source" / "textures" / "v200" / f"{name}.dds"   # 2.0.0: convenience-store rework
    if (ROOT / "source" / "textures" / "v230" / f"{name}.dds").is_file():
        p = ROOT / "source" / "textures" / "v230" / f"{name}.dds"   # 2.3.0: sign palette, worn finishes
    if (ROOT / "source" / "textures" / "v240" / f"{name}.dds").is_file():
        p = ROOT / "source" / "textures" / "v240" / f"{name}.dds"   # 2.4.0: calm plaster, clean dado / band, dark aluminium
    if (ROOT / "source" / "textures" / "v250" / f"{name}.dds").is_file():
        p = ROOT / "source" / "textures" / "v250" / f"{name}.dds"   # 2.5.0: local grime decals
    if (ROOT / "source" / "textures" / "v270" / f"{name}.dds").is_file():
        p = ROOT / "source" / "textures" / "v270" / f"{name}.dds"   # 2.7.0: sign-colour band / dado, old walls, header signs
    if (ROOT / "source" / "textures" / "v280" / f"{name}.dds").is_file():
        p = ROOT / "source" / "textures" / "v280" / f"{name}.dds"   # 2.8.0: calmer wall, pegboard, brand headers
    if (ROOT / "source" / "textures" / "v300" / f"{name}.dds").is_file():
        p = ROOT / "source" / "textures" / "v300" / f"{name}.dds"   # 3.0.0: quiet wall, headers, wall lettering
    if not p.is_file():
        p = TEX / f"{name}.dds"
    if not p.is_file():
        p = TEX_SLICE / f"{name}.dds"
    if not p.is_file():
        p = TEX_V021 / f"{name}.dds"
    if not p.is_file():
        p = TEX_V023 / f"{name}.dds"
    if not p.is_file():
        p = TEX_V025 / f"{name}.dds"
    if not p.is_file():
        p = TEX_V026 / f"{name}.dds"
    if not p.is_file():
        p = TEX_V027 / f"{name}.dds"
    if not p.is_file():
        p = TEX_V029 / f"{name}.dds"
    if not p.is_file():
        p = ROOT / "source" / "textures" / "v031" / f"{name}.dds"     # 0.3.1: CC0 back-of-house sets, Higgsfield images
    if not p.is_file():
        raise FileNotFoundError(p)
    img = bpy.data.images.load(str(p), check_existing=True)
    img.name = f"{name}.dds"
    return img


def shader(shader_file, textures, params=None, name=None):
    mat = shm.create_shader(shader_file)
    if name:
        mat.name = name
    for node_name, tex in textures.items():
        node = mat.node_tree.nodes.get(node_name)
        if node is None:
            raise KeyError(f"{shader_file}: no node {node_name}")
        node.image = image(tex)
        node.texture_properties.embedded = True
    for pname, val in (params or {}).items():
        node = mat.node_tree.nodes.get(pname)
        if node is None:
            raise KeyError(f"{shader_file}: no parameter {pname}")
        vals = val if isinstance(val, (list, tuple)) else [val]
        for i, x in enumerate(vals):
            node.set(i, float(x))
    return mat


def mesh_from_faces(name, faces, materials, sc, cpv=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    cache = {}
    for f in faces:
        vs = []
        for co in f["v"]:
            key = tuple(round(c, 5) for c in co)
            if key not in cache:
                cache[key] = bm.verts.new(key)
            vs.append(cache[key])
        if len({id(v) for v in vs}) < 3:
            continue
        try:
            bf = bm.faces.new(vs)
        except ValueError:
            # duplicate face (shared corner verts) -> make unique copies
            vs = [bm.verts.new(v.co) for v in vs]
            bf = bm.faces.new(vs)
        bf.material_index = f["mat"]
        bf.smooth = bool(f.get("smooth", False))
        for loop, (u, v) in zip(bf.loops, f["uv"]):
            loop[uv].uv = (u, v)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    if cpv is not None:
        # 0.1.4: Sollumz exports the "Color 1" corner attribute as Colour0 (sRGB bytes). Without it every vertex is
        # white = full artificial ambient -> the interior and the windows glowed at night (0.1.3).
        col = me.color_attributes.new("Color 1", "BYTE_COLOR", "CORNER")
        for poly in me.polygons:
            for li in poly.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                col.data[li].color_srgb = cpv((co.x, co.y, co.z))
        me.color_attributes.active_color = col
        me.color_attributes.render_color_index = me.color_attributes.active_color_index
    for m in materials:
        me.materials.append(m)
    obj = bpy.data.objects.new(name, me)
    sc.collection.objects.link(obj)
    return obj


def make_drawable(name, faces, materials, sc, cpv=None):
    obj = mesh_from_faces(name, faces, materials, sc, cpv)
    for m in materials:
        matops.post_create_shader_update_object(obj, m)
    drawable = dh.convert_obj_to_drawable(obj)
    drawable.name = name
    return drawable


def add_light(parent, L, sc, idx, color=(1.0, 0.90, 0.76), intensity=1.0, falloff=6.0, exponent=12.0):
    """L = (x, y, z) for a plain warm point (shell back rooms) or a 0.2.2 light dict from K.LT / K.CORONA
    (type POINT|SPOT, dir, cone_out/cone_in in degrees, flags by name, corona, fade distances)."""
    if not isinstance(L, dict):
        L = dict(type="POINT", pos=tuple(L), dir=(0.0, 0.0, -1.0), color=color, intensity=intensity, falloff=falloff,
                 exponent=exponent, cone_out=0.0, cone_in=0.0, flags=(), corona_size=0.0, corona_int=0.0, fade=(0, 0, 0))
    spot = L["type"] == "SPOT"
    ldata = bpy.data.lights.new(f"gs_light_{idx}", "SPOT" if spot else "POINT")
    lobj = bh.create_blender_object(SollumType.LIGHT, f"gs_light_{idx}", ldata)
    if lobj.name not in sc.collection.objects:
        try:
            sc.collection.objects.link(lobj)
        except RuntimeError:
            pass
    lobj.data.sollum_type = LightType.SPOT if spot else LightType.POINT
    lobj.location = L["pos"]
    if spot:
        # Sollumz exports direction = -(local Z): rotate -Z onto the aim vector
        lobj.rotation_mode = "QUATERNION"
        lobj.rotation_quaternion = Vector((0.0, 0.0, -1.0)).rotation_difference(Vector(L["dir"]))
    lobj.parent = parent
    ldata.color = L["color"]
    lp = ldata.light_properties
    lp.intensity = L["intensity"]
    lp.falloff = L["falloff"]
    lp.falloff_exponent = L["exponent"]
    if spot:
        lp.cone_outer_angle = math.radians(L["cone_out"])
        lp.cone_inner_angle = math.radians(L["cone_in"])
    lp.corona_size = L["corona_size"]
    lp.corona_intensity = L["corona_int"]
    # 0.3.1-o optimisation: interior lights stop 25 m away (was 35), shadows 14 m (was 18), specular 15 m (was 20)
    _f = L["fade"]
    lp.light_fade_distance, lp.shadow_fade_distance, lp.specular_fade_distance = (min(_f[0], 25) if _f[0] else _f[0],
                                                                                   min(_f[1], 14) if _f[1] else _f[1],
                                                                                   min(_f[2], 15) if _f[2] else _f[2])
    ldata.time_flags.total = str(L.get("time", 0xFFFFFF))                   # 0.2.6: day-only window fills
    ldata.light_flags.total = str(K.flags_total(L["flags"]))
    return lobj


def quat_z(yaw):
    return Quaternion((0.0, 0.0, 1.0), yaw)


def build_mlo():
    sc = new_scene("gs_prototype_mlo")
    info = {}

    # ---------- materials
    def pbr(nm, diff, nrm, spec, falloff, intensity=1.0, bump=1.0):
        return shader("normal_spec.sps", {"DiffuseSampler": diff, "BumpSampler": nrm, "SpecSampler": spec},
                      {"specularIntensityMult": intensity, "specularFalloffMult": falloff, "specularFresnel": 0.97,
                       "bumpiness": bump}, name=nm)

    # 0.2.0: CC0 PBR shell materials (textures: gs_14_make_slice_textures.py, provenance in assets/registry.json)
    SHT = getattr(K, "SHELL_TEX", {})                                     # 0.2.5: shell textures from the kit

    def shell_pbr(key, nm, d, n, s_, fo, it=1.0):
        if key in SHT:
            d, n, s_, fo, it = SHT[key]
            nm = d + ("_shell" if key == "tile" else "")
        return pbr(nm, d, n, s_, fo, it)
    m_floor = shell_pbr("floor", "lp3_floor_bw", "lp3_floor_bw", "lp_floor_checker_n", "lp_floor_checker_s", 60.0)   # 0.2.3 black / white vinyl
    # 0.2.3: no wood — cream painted brick walls, oxblood glazed tile band / sills, own mineral-fibre ceiling tile
    m_wall = shell_pbr("wall", "lp3_paintbrick", "lp3_paintbrick", "lp3_paintbrick_n", "lp3_paintbrick_s", 10.0, 0.4)
    m_wood = shell_pbr("tile", "lp3_tile_red_shell", "lp3_tile_red", "lp3_tile_n", "lp3_tile_s", 140.0, 1.1)
    m_ceil = shell_pbr("ceil", "lp3_ceiling_tile", "lp3_ceiling_tile", "lp3_ceiling_tile_n", "lp_ceiling_tile_s", 6.0, 0.3)
    m_trim = shader("default.sps", {"DiffuseSampler": "gs_proto_trim"}, name="gs_proto_trim")
    m_alu = shader("default.sps", {"DiffuseSampler": "gs_proto_alu"}, name="gs_proto_alu")       # 0.1.5 window frames

    def glass_mat(nm):
        return shader("glass_env.sps", {"DiffuseSampler": "gs_proto_glass", "BumpSampler": "gs_proto_flat_n", "SpecSampler": "gs_proto_glass_s"},
                      {"specularIntensityMult": 1.0, "specularFalloffMult": 100.0, "specularFresnel": 0.97, "bumpiness": 0.2}, name=nm)

    # ---------- drawables
    shell_mats = {"floor": 0, "wall": 1, "wood": 2, "ceiling": 3, "trim": 4, "alu": 5}
    shell = make_drawable("gs_proto_shell", PG.shell_faces() + SG.partition_faces(shell_mats),
                          [m_floor, m_wall, m_wood, m_ceil, m_trim, m_alu]
                          + [shader(sh_, tx_, pr_, name=nm_) for (sh_, tx_, pr_, nm_) in getattr(K, "SHELL_EXTRA_SPECS", [])],   # 1.2.1
                          sc, K.cpv_hall)
    for i, p in enumerate(SHELL_LIGHTS):
        add_light(shell, p, sc, i)
    # 0.2.1: hall drawable (order = K.MAT) — architecture kit + furniture + food + fixtures + flag
    f_mats = [shader(sh, tex, prm, name=nm) for (sh, tex, prm, nm) in K.SHADER_SPECS]     # 0.2.3: from the kit (no wood)
    assert len(f_mats) == len(K.MAT)
    furniture = make_drawable(HALL, K.hall_faces(), f_mats, sc, K.cpv_hall)
    for i, L in enumerate(K.lights()):
        add_light(furniture, L, sc, 100 + i)
    # 0.2.8: back of house in its own drawable (own material subset + lights), so the hall keeps its memory budget
    boh_drw = None
    if getattr(K, "BOH", False):
        b_mats = [shader(sh, tex, prm, name=nm + "_boh") for (sh, tex, prm, nm) in K.BOH_SPECS]
        boh_drw = make_drawable("gs_boh", K.boh_faces(), b_mats, sc, K.cpv_hall)
        for i, L in enumerate(K.boh_lights()):
            add_light(boh_drw, L, sc, 400 + i)
    # 0.2.9: AFTER HOURS entity-set drawables (lit public troffers + OPEN neon / CLOSED card + night service lights)
    set_drws = {}
    if hasattr(K, "set_entities"):
        for nm_, faces_fn, specs_fn, lights_fn, base_i in (("gs_ah_open", K.open_faces, K.open_specs, K.open_lights, 600),
                                                          ("gs_ah_closed", K.closed_faces, K.closed_specs, K.closed_lights, 700)):
            mats_ = [shader(sh, tex, prm, name=n_ + "_" + nm_) for (sh, tex, prm, n_) in specs_fn()]
            d_ = make_drawable(nm_, faces_fn(), mats_, sc, K.cpv_hall)
            for i, L in enumerate(lights_fn()):
                add_light(d_, L, sc, base_i + i)
            set_drws[nm_] = d_
    # 2.6.0: extra drawables of the hall (own material lists, same room as the hall), e.g. gs_v26_market
    xtra_drws = []
    for nm_, faces_fn, specs_fn in getattr(K, "EXTRA_HALL_DRAWABLES", ()):
        mats_ = [shader(sh, tex, prm, name=n_) for (sh, tex, prm, n_) in specs_fn()]
        xtra_drws.append((nm_, make_drawable(nm_, faces_fn(), mats_, sc, K.cpv_hall)))
    glass_w1 = make_drawable("gs_proto_glass_w1", PG.glass_faces("W1"), [glass_mat("gs_proto_glass_w1")], sc, PG.cpv_glass)
    glass_w2 = make_drawable("gs_proto_glass_w2", PG.glass_faces("W2"), [glass_mat("gs_proto_glass_w2")], sc, PG.cpv_glass)
    # 0.1.5: no own door drawables any more — the leaves are vanilla GTA V doors placed as MLO entities below

    # ---------- MLO collision (floor + ceiling slabs, room id 1)
    me = bpy.data.meshes.new(MLO_NAME)
    bm = bmesh.new()
    for tri in PG.floor_slab_tris(PG.FLOOR, 0.15):
        vs = [bm.verts.new(v) for v in tri]
        f = bm.faces.new(vs); f.material_index = 0
    for tri in PG.floor_slab_tris(PG.CEIL + 0.12, 0.12):
        vs = [bm.verts.new(v) for v in tri]
        f = bm.faces.new(vs); f.material_index = 1
    # 0.1.4 (audit 05 F1): wall slabs on the visible faces, openings left open; landings at the back doors
    for tri in PG.wall_collision_tris():
        vs = [bm.verts.new(v) for v in tri]
        f = bm.faces.new(vs); f.material_index = 1
    for tri in PG.step_collision_tris():
        vs = [bm.verts.new(v) for v in tri]
        f = bm.faces.new(vs); f.material_index = 2
    # 0.2.0: partitions + furniture boxes (benches, tables, counters, cases)
    col_names = ["LINOLEUM", "PLASTER_SOLID", "CONCRETE", "WOOD_SOLID_MEDIUM", "LEATHER", "METAL_SOLID_SMALL",
                 "METAL_SOLID_MEDIUM", "GLASS_SHOOT_THROUGH"]
    for box_, mname in K.collision_boxes():
        for tri in SG.box_tris(box_):
            vs = [bm.verts.new(v) for v in tri]
            f = bm.faces.new(vs); f.material_index = col_names.index(mname)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.normal_update(); bm.to_mesh(me); bm.free()
    cobj = bpy.data.objects.new(MLO_NAME, me)
    sc.collection.objects.link(cobj)
    me.materials.append(colmat("LINOLEUM", room_id=1))
    me.materials.append(colmat("PLASTER_SOLID", room_id=1))
    me.materials.append(colmat("CONCRETE", room_id=1))
    for mname in col_names[3:]:
        me.materials.append(colmat(mname, room_id=1))
    col = boh.convert_obj_to_composite(cobj, SollumType.BOUND_GEOMETRYBVH, "General (Default)")
    col.name = MLO_NAME

    # ---------- YTYP
    ytyp = sc.ytyps.add(); ytyp.name = YTYP_NAME
    sc.ytyp_index = len(sc.ytyps) - 1

    def base_arch(name, asset, lod, flags=0, special="NOTHING_SPECIAL"):
        a = ytyp.new_archetype(ArchetypeType.BASE)
        a.name = name
        a.asset = asset
        a.lod_dist = lod
        a.flags.total = str(flags)
        a.special_attribute = special
        return a

    base_arch("gs_proto_shell", shell, 150.0, flags=32)            # Static
    base_arch("gs_proto_glass_w1", glass_w1, 150.0, flags=32)
    base_arch("gs_proto_glass_w2", glass_w2, 150.0, flags=32)
    base_arch(HALL, furniture, 100.0, flags=32)
    if boh_drw is not None:
        base_arch("gs_boh", boh_drw, 100.0, flags=32)
    for nm_, d_ in set_drws.items():
        base_arch(nm_, d_, 100.0, flags=32)
    for nm_, d_ in xtra_drws:
        base_arch(nm_, d_, 100.0, flags=32)

    mlo = ytyp.new_archetype(ArchetypeType.MLO)
    mlo.name = MLO_NAME
    mlo.asset = col
    mlo.lod_dist = 150.0
    # the MLO archetype must name its interior collision as physics dictionary (v0.1 crash: proxy == null)
    mlo.physics_dictionary = MLO_NAME
    mlo_index = len(ytyp.archetypes) - 1
    ytyp.archetypes.select(mlo_index)

    limbo = mlo.new_room(); limbo.name = "limbo"
    limbo.bb_min = PG.ROOM_BB[0]; limbo.bb_max = PG.ROOM_BB[1]
    limbo.timecycle = ""
    front = mlo.new_room(); front.name = "gs_front"
    front.bb_min = PG.ROOM_BB[0]; front.bb_max = PG.ROOM_BB[1]
    front.timecycle = K.ROOM_TIMECYCLE          # 0.2.2: own modifier (stream/lp_timecycle.xml, TIMECYCLEMOD_FILE)

    portal_ids = {}
    for key, corners in PG.portals().items():
        p = mlo.new_portal()
        p.room_from_id = str(front.id)
        p.room_to_id = str(limbo.id)
        p.corner1, p.corner2, p.corner3, p.corner4 = [Vector(c) for c in corners]
        portal_ids[key] = p.id

    def mlo_entity(arch_name, pos, yaw=0.0, room=None, portal=None, lod=150.0, flags=ENT_FLAGS_SHADOWS):
        e = mlo.new_entity()
        e.flags.total = str(flags)
        e.archetype_name = arch_name
        e.position = pos
        if isinstance(yaw, (tuple, list)):                # 0.2.9: full quaternion (w, x, y, z), e.g. chairs up on tables
            e.rotation = tuple(float(c) for c in yaw)
        else:
            q = quat_z(yaw)
            e.rotation = (q.w, q.x, q.y, q.z)
        e.lod_dist = lod
        if portal is not None:
            e.attached_portal_id = str(portal)
        else:
            e.attached_room_id = str(front.id)
        return e

    mlo_entity("gs_proto_shell", (0.0, 0.0, 0.0))
    mlo_entity("gs_proto_glass_w1", (0.0, 0.0, 0.0), portal=portal_ids["W1"], flags=0)
    mlo_entity("gs_proto_glass_w2", (0.0, 0.0, 0.0), portal=portal_ids["W2"], flags=0)
    for did, arch_name, pos, yaw, portal_key in PG.vanilla_door_entities():
        mlo_entity(arch_name, pos, yaw, portal=portal_ids[portal_key], lod=100.0)
    # 0.2.0: furniture + vanilla props (archetype names only, nothing of Rockstar is shipped)
    mlo_entity(HALL, (0.0, 0.0, 0.0), lod=100.0)
    for nm_, d_ in xtra_drws:
        mlo_entity(nm_, (0.0, 0.0, 0.0), lod=100.0)
    if boh_drw is not None:
        mlo_entity("gs_boh", (0.0, 0.0, 0.0), lod=100.0)
    for arch_name, pos, yaw in K.vanilla_entities():
        small = arch_name.startswith(SMALL_PROPS)
        mlo_entity(arch_name, pos, yaw, lod=25.0 if small else 55.0, flags=0 if small else ENT_FLAGS_SHADOWS)   # 0.3.1-o: was 40 / 80
    # 0.2.9: entity sets (AFTER HOURS): lp_open is the MLO instance default (ymap), the client switches lp_open / lp_closed
    set_info = {}
    if hasattr(K, "set_entities"):
        for set_name, ents in K.set_entities().items():
            es = mlo.new_entity_set()
            es.name = set_name
            for arch_name, pos, rot in ents:
                small = arch_name.startswith(SMALL_PROPS)
                e = mlo_entity(arch_name, pos, rot, lod=100.0 if arch_name.startswith("gs_") else (25.0 if small else 55.0),
                               flags=0 if small else ENT_FLAGS_SHADOWS)
                e.attached_entity_set_id = str(es.id)
            set_info[set_name] = len(ents)
    exit_portals = mlo.calc_num_exit_portals()

    # ---------- YMAP (MLO instance)
    maps = get_maps(bpy.context, create_if_missing=True)
    grp = maps.new_group(); grp.name = YMAP_NAME
    md = grp.new_map(); md.name = YMAP_NAME
    ent = grp.new_entity()
    ent.archetype_name = MLO_NAME
    ent.is_mlo = True
    ent.position = MLO_POS
    q = quat_z(MLO_YAW)
    ent.rotation = (q.w, q.x, q.y, q.z)
    ent.lod_dist = 200.0
    ent.lod_level = "HD"
    ent.flags.total = str(ENT_FLAGS_SHADOWS)
    ent.mlo_num_exit_portals = exit_portals
    ent.map_data_uuid = md.uuid

    info.update({"entity_sets": set_info, "kit": K.__name__, "version": getattr(K, "VERSION", "?")})
    info.update({"drawables": ["gs_proto_shell", "gs_proto_glass_w1", "gs_proto_glass_w2", HALL],
                 "vanilla_props": [e[0] for e in K.vanilla_entities()],
                 "furniture_tris": sum(len(p.vertices) - 2 for o in furniture.children_recursive if o.type == "MESH" for p in o.data.polygons),
                 "vanilla_doors": [(e[0], e[1]) for e in PG.vanilla_door_entities()],
                 "collision": MLO_NAME, "rooms": [r.name for r in mlo.rooms], "portals": list(portal_ids),
                 "entities": [e.archetype_name for e in mlo.entities], "exit_portals": exit_portals,
                 "shell_tris": sum(len(p.vertices) - 2 for o in shell.children_recursive if o.type == "MESH" and o.sollum_type == SollumType.DRAWABLE_MODEL for p in o.data.polygons),
                 "lights": len([o for o in shell.children_recursive if o.sollum_type == SollumType.LIGHT])})
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND / "gs_prototype_mlo.blend"))
    return info


def export_mlo():
    for f in EXPORT.iterdir():
        if f.is_file():
            f.unlink()
    res = bpy.ops.sollumz.export_assets(
        directory=str(EXPORT), direct_export=True, use_custom_settings=True,
        target_formats={FMT.name}, target_versions={"GEN8"}, limit_to_selected=False,
        exclude_skeleton=False, ymap_exclude_entities=False, ymap_box_occluders=False,
        ymap_model_occluders=False, ymap_car_generators=False, apply_transforms=False,
        mesh_domain="FACE_CORNER", export_ytyps=True, export_ytyps_include="ALL",
        export_ymaps=True, export_ymaps_include="ALL", export_ytds=False, export_ytds_include="ALL")
    files = {f.name: f.stat().st_size for f in EXPORT.iterdir() if f.is_file()}
    want = [f"{n}{EXT}" for n in ("gs_proto_shell.ydr", "gs_proto_glass_w1.ydr", "gs_proto_glass_w2.ydr", f"{HALL}.ydr",
                                  f"{MLO_NAME}.ybn", f"{YTYP_NAME}.ytyp", f"{YMAP_NAME}.ymap")]
    if getattr(K, "BOH", False):
        want.append(f"gs_boh.ydr{EXT}")
    want += [f"{nm_}.ydr{EXT}" for nm_, _f, _s in getattr(K, "EXTRA_HALL_DRAWABLES", ())]
    if hasattr(K, "set_entities"):
        want += [f"gs_ah_open.ydr{EXT}", f"gs_ah_closed.ydr{EXT}"]
    missing = [w for w in want if w not in files]
    stale = [f for f in files if f.startswith(("gs_proto_door", "gs_proto_backdoor"))]
    step("export_mlo", res == {"FINISHED"} and not missing and not stale and all(v > 0 for v in files.values()), result=list(res),
         files=files, missing=missing, stale_own_doors=stale)
    return files


def fixup_mlo_bounds():
    """Sollumz writes a zero bounding box for CMloArchetypeDef and therefore point-sized ymap entity extents.
    Vanilla MLOs carry real bounds: set them from the room box and recompute the ymap entities extents."""
    from szio.types import Vector as SzVec
    yt = load(EXPORT / f"{YTYP_NAME}.ytyp{EXT}")
    m = next(a for a in yt.archetypes if a.name == MLO_NAME)
    mn, mx = PG.ROOM_BB
    c = [(a + b) / 2 for a, b in zip(mn, mx)]
    r = math.sqrt(sum(((b - a) / 2) ** 2 for a, b in zip(mn, mx)))
    m.bb_min, m.bb_max, m.bs_center, m.bs_radius = SzVec(mn), SzVec(mx), SzVec(c), r
    m.physics_dictionary = MLO_NAME
    szio.save_asset(yt, TARGET, EXPORT, YTYP_NAME)
    ym = load(EXPORT / f"{YMAP_NAME}.ymap{EXT}")
    rot = quat_z(MLO_YAW).to_matrix()
    pts = [Vector(MLO_POS) + rot @ Vector((x, y, z)) for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])]
    emin = [min(p[i] for p in pts) for i in range(3)]
    emax = [max(p[i] for p in pts) for i in range(3)]
    ym.entities_extents = (SzVec(emin), SzVec(emax))
    # like every working MLO placement ymap: reference the interior collision and flag HAS_PHYSICS,
    # MLO instance at LOD level HD (Sollumz writes ORPHANHD for parentless entities)
    from szio.gta5.maps import MapContentFlags
    from szio.gta5.entities import EntityLodLevel, EntityFlags
    ym.physics_dictionaries = [MLO_NAME]
    ym.content_flags = ym.content_flags | MapContentFlags.HAS_PHYSICS
    for e in ym.entities:
        if e.archetype_name == MLO_NAME:
            e.lod_level = EntityLodLevel.HD
            e.flags = EntityFlags(ENT_FLAGS_SHADOWS)
            if hasattr(K, "set_entities"):                    # 0.2.9: AFTER HOURS default = open, even without scripts
                e.default_entity_sets = ["lp_open"]
    szio.save_asset(ym, TARGET, EXPORT, YMAP_NAME)
    yt2 = load(EXPORT / f"{YTYP_NAME}.ytyp{EXT}")
    m2 = next(a for a in yt2.archetypes if a.name == MLO_NAME)
    ym2 = load(EXPORT / f"{YMAP_NAME}.ymap{EXT}")
    ok = abs(float(m2.bs_radius) - r) < 1e-3 and abs(float(ym2.entities_extents[1][0]) - emax[0]) < 1e-2 and len(m2.portals) == 5 \
        and m2.physics_dictionary == MLO_NAME and list(ym2.physics_dictionaries) == [MLO_NAME] \
        and int(ym2.content_flags.value) == 73 and ym2.entities[0].lod_level.name == "HD"
    step("fixup_mlo_bounds", ok, mlo_bb=[mn, mx], bs_radius=round(r, 3), mlo_physics_dictionary=m2.physics_dictionary,
         ymap_physics_dictionaries=list(ym2.physics_dictionaries), ymap_content_flags=int(ym2.content_flags.value),
         mlo_instance_lod_level=ym2.entities[0].lod_level.name,
         entities_extents=[[round(float(x), 2) for x in ym2.entities_extents[0]], [round(float(x), 2) for x in ym2.entities_extents[1]]],
         streaming_extents=[[round(float(x), 2) for x in ym2.streaming_extents[0]], [round(float(x), 2) for x in ym2.streaming_extents[1]]])


# ======================================================================== C. validation of exported files
def validate():
    v = {}
    sh = load(EXPORT / f"gs_proto_shell.ydr{EXT}")
    st = G.drawable_stats(sh)
    v["shell"] = {"geometries": len(st["geometries"]), "tris": sum(g["tris"] for g in st["geometries"]),
                  "shaders": [s.name for s in sh.shader_group.shaders], "embedded_textures": sorted(sh.shader_group.embedded_textures),
                  "lights": len(sh.lights)}
    # 0.2.0: 4 normal_spec materials x 3 textures + trim + alu
    _sx = getattr(K, "SHELL_EXTRA_SPECS", [])                                  # 1.2.1: extra shell materials from the kit
    _sxt = len({t_ for (_s, tx_, _p, _n) in _sx for t_ in tx_.values()})
    ok_shell = v["shell"]["geometries"] == 6 + len(_sx) and len(v["shell"]["embedded_textures"]) == getattr(K, "SHELL_TEX_N", 14) + _sxt and v["shell"]["lights"] == len(SHELL_LIGHTS)
    fu = load(EXPORT / f"{HALL}.ydr{EXT}")
    fst = G.drawable_stats(fu)
    v["furniture"] = {"geometries": len(fst["geometries"]), "tris": sum(g["tris"] for g in fst["geometries"]),
                      "shaders": [s.name for s in fu.shader_group.shaders], "embedded_textures": sorted(fu.shader_group.embedded_textures),
                      "lights": len(fu.lights)}
    used_mats = len({f["mat"] for f in K.hall_faces()})
    ok_furn = v["furniture"]["geometries"] >= used_mats and v["furniture"]["lights"] == len(K.lights()) \
        and "emissive" in v["furniture"]["shaders"] and "glass_env" in v["furniture"]["shaders"] and v["furniture"]["tris"] > getattr(K, "HALL_MIN_TRIS", 20000)
    # 0.1.4: vertex colours exported (Colour0), green = artificial ambient ~0.30, nothing fully self-lit
    cpv = {"layouts": [], "g_max": None, "g_min": None, "r_range": None}
    gs, rs = [], []
    for lod, models in sh.models.items():
        for mdl in models:
            for g in mdl.geometries:
                names = list(g.vertex_buffer.dtype.names)
                cpv["layouts"].append(names)
                if "Colour0" in names:
                    c = np.asarray(g.vertex_buffer["Colour0"]).reshape(len(g.vertex_buffer), -1)
                    rs += c[:, 0].tolist(); gs += c[:, 1].tolist()
    if gs:
        cpv.update(g_min=int(min(gs)), g_max=int(max(gs)), r_range=[int(min(rs)), int(max(rs))])
    v["shell"]["cpv"] = cpv
    # 0.2.2: baked artificial-ambient gradient (floor contact / ceiling darker), still never self-lit
    ok_shell = ok_shell and bool(gs) and cpv["g_max"] <= 95 and cpv["g_min"] >= 45
    for nm in ("gs_proto_glass_w1", "gs_proto_glass_w2"):
        d = load(EXPORT / f"{nm}.ydr{EXT}")
        v[nm] = {"shaders": [s.name for s in d.shader_group.shaders], "embedded_textures": sorted(d.shader_group.embedded_textures),
                 "tris": sum(g["tris"] for g in G.drawable_stats(d)["geometries"]), "has_bounds": d.bounds is not None}
    ok_glass = all("glass_env" in v[n]["shaders"] for n in ("gs_proto_glass_w1", "gs_proto_glass_w2"))

    col = load(EXPORT / f"{MLO_NAME}.ybn{EXT}")
    rooms_in_col = sorted({p.material.room_id for c in [col] + list(getattr(col, "children", []) or []) if c is not None
                           for p in getattr(c, "geometry_primitives", [])})
    v["collision"] = {"stats": G.bound_stats(col) if hasattr(col, "children") else str(type(col)), "room_ids": rooms_in_col}
    ok_col = rooms_in_col == [1]

    yt = load(EXPORT / f"{YTYP_NAME}.ytyp{EXT}")
    arch = {a.name: a for a in yt.archetypes}
    m = arch.get(MLO_NAME)
    v["ytyp"] = {"archetypes": {a.name: {"type": a.type.name, "flags": a.flags, "special": a.special_attribute, "lod": a.lod_dist,
                                         "txd": a.texture_dictionary} for a in yt.archetypes}}
    ok_ytyp = m is not None and m.type.name == "MLO"
    if m is not None:
        v["ytyp"]["rooms"] = [{"name": r.name, "bb": [list(map(float, r.bb_min)), list(map(float, r.bb_max))], "portals": r.portal_count,
                               "objects": r.attached_objects, "timecycle": r.timecycle} for r in m.rooms]
        v["ytyp"]["portals"] = [{"from": p.room_from, "to": p.room_to, "objects": p.attached_objects,
                                 "corners": [[round(float(x), 3) for x in c] for c in p.corners]} for p in m.portals]
        v["ytyp"]["entities"] = [{"archetype": e.archetype_name, "pos": [round(float(x), 3) for x in e.position],
                                  "rot": [round(float(x), 4) for x in e.rotation]} for e in m.entities]
        ok_ytyp = ok_ytyp and [r.name for r in m.rooms] == ["limbo", "gs_front"] and len(m.portals) == 5 \
            and all(p.room_from == 1 and p.room_to == 0 for p in m.portals) \
            and len(m.entities) == 8 + (1 if getattr(K, "BOH", False) else 0) + len(getattr(K, "EXTRA_HALL_DRAWABLES", ())) + len(K.vanilla_entities())
        _d1 = {e[1] for e in PG.vanilla_door_entities()}              # D1 / D2 / D3 leaves are checked as doors below
        want_props = sorted({e[0] for e in K.vanilla_entities()} - _d1)
        v["ytyp"]["vanilla_props"] = sorted({e.archetype_name for e in m.entities if e.archetype_name in K.VB} - _d1)
        ok_ytyp = ok_ytyp and v["ytyp"]["vanilla_props"] == want_props and not any(a in arch for a in K.VB)
        # 0.1.3: every exit portal must face away from its room (same as the working dealer_map MLO)
        rc = [(a + b) / 2 for a, b in zip(PG.ROOM_BB[0], PG.ROOM_BB[1])]
        facing = []
        for p in m.portals:
            c = [tuple(float(x) for x in q) for q in p.corners]
            n = PG.portal_normal(c)
            pc = [sum(q[i] for q in c) / 4 for i in range(3)]
            dv = PG._sub(rc, pc)
            L = math.sqrt(PG._dot(dv, dv))
            facing.append(round(PG._dot(n, dv) / L, 3))
        v["ytyp"]["portal_facing_dot"] = facing
        ok_ytyp = ok_ytyp and all(f < 0 for f in facing)
        # 0.1.5: the four door entities reference vanilla archetypes (not defined in our ytyp), each attached to its portal
        k_doors = K.all_doors() if hasattr(K, "all_doors") else (K.boh_doors() if getattr(K, "BOH", False) else [])
        want_doors = sorted([e[1] for e in PG.vanilla_door_entities()] + [d[1] for d in k_doors])
        got_doors = sorted(e.archetype_name for e in m.entities if e.archetype_name in PG.VDOORS)
        own_doors = [a for a in arch if a.startswith(("gs_proto_door", "gs_proto_backdoor"))]
        v["ytyp"]["door_entities"] = got_doors
        v["ytyp"]["own_door_archetypes"] = own_doors
        ok_ytyp = ok_ytyp and got_doors == want_doors and not own_doors and not any(a in arch for a in PG.VDOORS)
        # 0.2.9: entity sets (AFTER HOURS)
        if hasattr(K, "set_entities"):
            sets = {es.name: len(es.entities) for es in (m.entity_sets or [])}
            want_sets = {k: len(v) for k, v in K.set_entities().items()}
            v["ytyp"]["entity_sets"] = sets
            ok_ytyp = ok_ytyp and sets == want_sets and all(a in arch for a in ("gs_ah_open", "gs_ah_closed"))

    ym = load(EXPORT / f"{YMAP_NAME}.ymap{EXT}")
    ents = [{"archetype": e.archetype_name, "type": type(e).__name__, "pos": [round(float(x), 3) for x in e.position],
             "rot": [round(float(x), 5) for x in e.rotation], "lod": e.lod_dist,
             "exit_portals": getattr(e, "num_exit_portals", None)} for e in ym.entities]
    v["ymap"] = {"entities": ents, "flags": str(ym.flags), "content_flags": str(ym.content_flags),
                 "physics_dictionaries": list(ym.physics_dictionaries), "mlo_physics_dictionary": m.physics_dictionary if m else None,
                 "streaming_extents": [[round(float(x), 2) for x in p] for p in ym.streaming_extents],
                 "entities_extents": [[round(float(x), 2) for x in p] for p in ym.entities_extents]}
    ok_ymap = len(ents) == 1 and ents[0]["archetype"] == MLO_NAME and ents[0]["type"] == "EntityMloInstance" \
        and all(abs(a - b) < 1e-3 for a, b in zip(ents[0]["pos"], MLO_POS)) \
        and list(ym.physics_dictionaries) == [MLO_NAME] and m is not None and m.physics_dictionary == MLO_NAME
    # world-space check of the door hinge positions vs the vanilla doorway (a, dep)
    if m is not None:
        hinge = []
        for e in m.entities:
            if e.archetype_name in ("v_ilev_csr_door_l", "v_ilev_csr_door_r"):
                p = Vector((float(e.position[0]), float(e.position[1]), float(e.position[2])))
                world = Matrix.Translation(MLO_POS) @ quat_z(MLO_YAW).to_matrix().to_4x4() @ p
                loc = G.to_local(world[:])
                a, dep = G.chamfer(loc)
                hinge.append({"world": [round(c, 3) for c in world], "a": round(float(a), 3), "dep": round(float(dep), 3)})
        v["door_hinges_world"] = hinge
        ok_ymap = ok_ymap and len(hinge) == 2 and all(abs(h["dep"] - PG.D1["leaf_dep"]) < 0.005 for h in hinge) \
            and sorted(round(h["a"], 3) for h in hinge) == [round(x, 3) for x in PG.D1["hinge_a"]]
    step("validate_shell", ok_shell, **v["shell"])
    step("validate_glass", ok_glass, **{k: v[k] for k in ("gs_proto_glass_w1", "gs_proto_glass_w2")})
    step("validate_furniture", ok_furn, **v["furniture"])
    step("validate_mlo_collision", ok_col, **v["collision"])
    step("validate_ytyp", ok_ytyp, **v["ytyp"])
    step("validate_ymap", ok_ymap, **v["ymap"], door_hinges_world=v.get("door_hinges_world"))
    return v


# ======================================================================== D. FiveM resource
def assemble_resource():
    if RES.exists():
        shutil.rmtree(RES)
    (RES / "stream" / "mlo").mkdir(parents=True)
    (RES / "stream" / "vanilla_override").mkdir(parents=True)
    for f in EXPORT.iterdir():
        if f.is_file() and not f.name.endswith(".ymap" + EXT):
            if f.name.endswith(".ytyp" + EXT):
                shutil.copy2(f, RES / "stream" / f.name)
            else:
                shutil.copy2(f, RES / "stream" / "mlo" / f.name)
    for f in EXPORT.iterdir():
        if f.name.endswith(".ymap" + EXT):
            shutil.copy2(f, RES / "stream" / f.name)
    for f in OVR.iterdir():
        if f.is_file():
            shutil.copy2(f, RES / "stream" / "vanilla_override" / f.name)
    # 0.3.1-o: LOD dictionaries without the kiosk + LONG PIG billboard LOD (made by gs_52_lod_override.py)
    _lod = ROOT / "source" / "lod_override"
    if NATIVE and _lod.is_dir():
        for f in _lod.glob("*.ydd"):
            shutil.copy2(f, RES / "stream" / "vanilla_override" / f.name)
    # _manifest.ymf: ymap -> ytyp dependency (INTERIOR_DATA) + interior collision, as in working MLOs
    import gs_22_make_manifest as MF
    importlib.reload(MF)
    (RES / "stream" / "_manifest.ymf").write_bytes(MF.build(imap_name=YMAP_NAME, ityp_name=YTYP_NAME,
                                                             interior_name=MLO_NAME, bounds_name=MLO_NAME))
    # 0.2.9: interactive props (gs_44 output: hidden credenza leaf, order ticket + lp_props.ytyp) -> stream/props
    props_dir = ROOT / "build" / "props" / ("export_native" if NATIVE else "export_cwxml")
    if props_dir.is_dir() and any(props_dir.iterdir()):
        (RES / "stream" / "props").mkdir(parents=True, exist_ok=True)
        for f in props_dir.iterdir():
            if f.is_file():
                shutil.copy2(f, RES / "stream" / "props" / f.name)
    # 0.2.7: exterior security shutters (gs_38 output, own models + lp_shutters.ytyp) -> stream/shutters
    shut = ROOT / "build" / "shutters" / ("export_native" if NATIVE else "export_cwxml")
    if shut.is_dir() and any(shut.iterdir()):
        (RES / "stream" / "shutters").mkdir(parents=True, exist_ok=True)
        for f in shut.iterdir():
            if f.is_file():
                shutil.copy2(f, RES / "stream" / "shutters" / f.name)
    if FIVEM_SRC.is_dir():
        for p in FIVEM_SRC.rglob("*"):
            if p.is_file():
                dst = RES / p.relative_to(FIVEM_SRC)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)
    files = sorted(str(p.relative_to(RES)).replace("\\", "/") for p in RES.rglob("*") if p.is_file())
    sizes = {str(p.relative_to(RES)).replace("\\", "/"): p.stat().st_size for p in RES.rglob("*") if p.is_file()}
    step("assemble_resource", (RES / "fxmanifest.lua").is_file() and any(f.endswith(".ytyp" + EXT) for f in files)
         and (RES / "stream" / "_manifest.ymf").is_file() and any(f.endswith(f"{YMAP_NAME}.ymap" + EXT) for f in files), files=sizes)
    return sizes


try:
    R["overrides"] = build_overrides()
except Exception:
    R["errors"].append("overrides: " + traceback.format_exc())
    print(traceback.format_exc())
try:
    R["mlo"] = build_mlo()
    step("build_mlo_scene", True, **R["mlo"])
    R["export_files"] = export_mlo()
    fixup_mlo_bounds()
    R["validation"] = validate()
except Exception:
    R["errors"].append("mlo: " + traceback.format_exc())
    print(traceback.format_exc())
try:
    R["resource"] = assemble_resource()
except Exception:
    R["errors"].append("resource: " + traceback.format_exc())
    print(traceback.format_exc())

R["go"] = bool(R["steps"]) and all(s["ok"] for s in R["steps"]) and not R["errors"]
out = RAW / ("prototype_build_result.json" if NATIVE else "prototype_build_result_cwxml_dryrun.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(R, fh, indent=1, ensure_ascii=False, default=str)
print("GS_PROTO_DONE go=%s format=%s -> %s" % (R["go"], FMT.name, out))
