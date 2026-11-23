# Gabagool & Sons — PHASE 0.3 pipeline smoke test (runs INSIDE Blender 5.1 + Sollumz 2.9.0)
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_02_smoke_test.py", encoding="utf-8").read())
#
# 1. builds a tiny GTA drawable (beveled crate, default.sps, embedded DDS texture, embedded box bound)
# 2. builds a standalone static collision (YBN, BVH poly mesh) + YTYP archetype + test YMAP (entity, not placed in-game)
# 3. exports Native (if PyMateria available) + CW XML for GTA V Legacy (gen8)
# 4. re-imports FROM THE EXPORTED FILES into an empty scene and compares geometry/material/collision/transform
# 5. saves .blend sources, a preview render (GUI only) and docs/_raw/smoke_test_result.json
import bpy, bmesh, os, sys, json, importlib, datetime, traceback, math
from mathutils import Vector, Matrix

ROOT = os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons")
EXP = os.path.join(ROOT, "source", "exports", "smoke")
BLEND_DIR = os.path.join(ROOT, "source", "blender", "smoke")
RAW = os.path.join(ROOT, "docs", "_raw")
TEX = os.path.join(ROOT, "source", "textures", "smoke", "gs_smoke_diffuse.dds")
SHOTS = os.path.join(ROOT, "screenshots", "pipeline")
for d in (EXP, BLEND_DIR, RAW, SHOTS):
    os.makedirs(d, exist_ok=True)

SZ = next(n for n in bpy.context.preferences.addons.keys() if n.split(".")[-1] == "sollumz")


def M(sub):
    return importlib.import_module(f"{SZ}.{sub}")


P = M("sollumz_properties"); SollumType = P.SollumType; ArchetypeType = P.ArchetypeType
bh = M("tools.blenderhelper"); dh = M("tools.drawablehelper"); boh = M("tools.boundhelper")
mh = M("tools.meshhelper"); shm = M("ydr.shader_materials"); colm = M("ybn.collision_materials")
matops = M("ydr.operators.materials")
from importlib import import_module
szio_gta5 = import_module("szio.gta5")
NATIVE_OK = szio_gta5.is_provider_available(szio_gta5.AssetFormat.NATIVE)
CWXML_OK = szio_gta5.is_provider_available(szio_gta5.AssetFormat.CWXML)

R = {"timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
     "blender": bpy.app.version_string, "sollumz_module": SZ,
     "native_available": NATIVE_OK, "cwxml_available": CWXML_OK, "steps": [], "errors": []}


def step(step_name, ok, **kw):
    R["steps"].append({"step": step_name, "ok": bool(ok), **kw})
    print(("PASS " if ok else "FAIL ") + step_name, json.dumps(kw, default=str)[:900] if kw else "")


def new_scene(name):
    """GUI: isolate each phase in its own scene (reloading the file from the console is unsafe).
    Background: start from an empty home file."""
    if not bpy.app.background and bpy.context.window is not None:
        sc = bpy.data.scenes.new(name)
        bpy.context.window.scene = sc
    else:
        bpy.ops.wm.read_homefile(use_empty=True)
        sc = bpy.context.scene
        sc.name = name
    sc.unit_settings.system = "METRIC"
    return sc


def colmat(name):
    for i, m in enumerate(colm.collisionmats):
        if m.name == name:
            return colm.create_collision_material_from_index(i)
    raise KeyError(name)


def box_uv(bm, scale=1.0):
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            co = l.vert.co
            if ax == 0:
                u, v = (co.y if n.x > 0 else -co.y), co.z
            elif ax == 1:
                u, v = (-co.x if n.y > 0 else co.x), co.z
            else:
                u, v = co.x, co.y
            l[uv].uv = (u * scale + 0.5, v * scale)


def world_bbox(objs):
    pts = []
    for o in objs:
        if o.type == "MESH":
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    if not pts:
        return None
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    return [round(v, 4) for v in mn], [round(v, 4) for v in mx]


def stats(drawable):
    models = [c for c in drawable.children_recursive if c.type == "MESH" and c.sollum_type == SollumType.DRAWABLE_MODEL]
    bounds = [c for c in drawable.children_recursive if c.sollum_type in (SollumType.BOUND_BOX, SollumType.BOUND_POLY_TRIANGLE, SollumType.BOUND_POLY_BOX)]
    mats = sorted({m.shader_properties.filename for o in models for m in o.data.materials if m})
    imgs = sorted({n.image.name.split(".")[0] for o in models for m in o.data.materials if m
                   for n in m.node_tree.nodes if isinstance(n, bpy.types.ShaderNodeTexImage) and n.image})
    bpy.context.view_layer.update()
    upos = {tuple(round(c, 4) for c in v.co) for o in models for v in o.data.vertices}
    return {"name": drawable.name, "location": [round(v, 4) for v in drawable.matrix_world.translation],
            "models": len(models), "verts": sum(len(o.data.vertices) for o in models), "unique_positions": len(upos),
            "tris": sum(len(p.vertices) - 2 for o in models for p in o.data.polygons),
            "shaders": mats, "images": imgs, "bbox": world_bbox(models), "bounds": len(bounds),
            "bound_types": sorted({str(b.sollum_type) for b in bounds})}


try:
    # ---------------------------------------------------------------- 1. build source scene
    sc = new_scene("gs_smoke_source")

    W, D, H = 0.8, 0.5, 0.6
    me = bpy.data.meshes.new("gs_smoke_box")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(W, D, H), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, H / 2), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.025, segments=2, affect="EDGES", profile=0.5)
    bm.normal_update()
    box_uv(bm, 1.0)
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new("gs_smoke_box", me)
    sc.collection.objects.link(obj)
    obj.location = (1.5, -2.0, 0.0)  # non-zero origin: verifies transforms survive the round trip

    mat = shm.create_shader("default.sps")
    me.materials.append(mat)
    img = bpy.data.images.load(TEX, check_existing=True)
    img.name = "gs_smoke_diffuse.dds"
    tex_node = mat.node_tree.nodes.get("DiffuseSampler")
    tex_node.image = img
    tex_node.texture_properties.embedded = True
    matops.post_create_shader_update_object(obj, mat)
    step("texture_loaded", img.size[0] == 256 and img.size[1] == 256, size=list(img.size), file=TEX)

    drawable = dh.convert_obj_to_drawable(obj)
    drawable.name = "gs_smoke_box"

    comp = bh.create_empty_object(SollumType.BOUND_COMPOSITE, "gs_smoke_box.col")
    comp.parent = drawable
    bbox = bh.create_blender_object(SollumType.BOUND_BOX, "gs_smoke_box.box")
    mh.create_box_from_extents(bbox.data, Vector((-W / 2, -D / 2, 0.0)), Vector((W / 2, D / 2, H)))
    bbox.data.materials.append(colmat("WOOD_SOLID_MEDIUM"))
    bbox.parent = comp
    boh.apply_flag_preset(comp, "General (Default)")
    boh.apply_flag_preset(bbox, "General (Default)")

    # standalone static collision (what the MLO shell will use): 3 x 3 m slab, 0.2 m thick
    sme = bpy.data.meshes.new("gs_smoke_col")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(3.0, 3.0, 0.2), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(1.5, -2.0, -0.1), verts=bm.verts)
    bm.to_mesh(sme); bm.free()
    sobj = bpy.data.objects.new("gs_smoke_col", sme)
    sc.collection.objects.link(sobj)
    sme.materials.append(colmat("CONCRETE"))
    col_comp = boh.convert_obj_to_composite(sobj, SollumType.BOUND_GEOMETRYBVH, "General (Default)")
    col_comp.name = "gs_smoke_col"

    # YTYP with one base archetype
    ytyp = sc.ytyps.add(); ytyp.name = "gs_smoke"
    sc.ytyp_index = len(sc.ytyps) - 1
    arch = ytyp.new_archetype(ArchetypeType.BASE)
    arch.name = "gs_smoke_box"
    arch.asset = drawable
    arch.lod_dist = 100.0

    # test YMAP (round-trip only — this file is NOT shipped to the game: TEST_ONLY_NOT_PLACED)
    from importlib import import_module as _im
    get_maps = _im(f"{SZ}.ymap_next.properties.map").get_maps
    maps = get_maps(bpy.context, create_if_missing=True)
    grp = maps.new_group(); grp.name = "gs_smoke_map"
    md = grp.new_map(); md.name = "gs_smoke_map"; md_uuid = md.uuid
    ent = grp.new_entity()
    ent.archetype_name = "gs_smoke_box"
    ent.lod_level = "HD"
    ent.position = (1.5, -2.0, 0.0)
    ent.lod_dist = 100.0
    ent.map_data_uuid = md_uuid

    src_stats = stats(drawable)
    R["source"] = src_stats
    step("source_built", src_stats["models"] == 1 and src_stats["bounds"] == 1, **src_stats)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLEND_DIR, "gs_smoke_source.blend"))

    # ---------------------------------------------------------------- 2. export
    for f in os.listdir(EXP):
        fp = os.path.join(EXP, f)
        if os.path.isfile(fp):
            os.remove(fp)
    fmts = set()
    if NATIVE_OK: fmts.add("NATIVE")
    if CWXML_OK: fmts.add("CWXML")
    res = bpy.ops.sollumz.export_assets(
        directory=EXP, direct_export=True, use_custom_settings=True,
        target_formats=fmts, target_versions={"GEN8"}, limit_to_selected=False,
        exclude_skeleton=False, ymap_exclude_entities=False, ymap_box_occluders=False,
        ymap_model_occluders=False, ymap_car_generators=False, apply_transforms=False,
        mesh_domain="FACE_CORNER", export_ytyps=True, export_ytyps_include="ALL",
        export_ymaps=True, export_ymaps_include="ALL", export_ytds=False, export_ytds_include="ALL")
    files = {}
    for dp, dn, fn in os.walk(EXP):
        for f in fn:
            files[os.path.relpath(os.path.join(dp, f), EXP)] = os.path.getsize(os.path.join(dp, f))
    R["export_files"] = files
    want = []
    if NATIVE_OK: want += ["gs_smoke_box.ydr", "gs_smoke_col.ybn", "gs_smoke.ytyp", "gs_smoke_map.ymap"]
    if CWXML_OK: want += ["gs_smoke_box.ydr.xml", "gs_smoke_col.ybn.xml", "gs_smoke.ytyp.xml", "gs_smoke_map.ymap.xml"]
    missing = [w for w in want if w not in files]
    empty = [k for k, v in files.items() if v == 0]
    step("export", res == {"FINISHED"} and not missing and not empty, result=list(res), missing=missing, empty=empty, files=files)

    # ---------------------------------------------------------------- 3. re-import from exported files
    def reimport(names, tag):
        new_scene(f"gs_smoke_reimport_{tag}")
        r = bpy.ops.sollumz.import_assets(directory=EXP, files=[{"name": n} for n in names],
                                          import_as_asset=False, split_by_group=True,
                                          dwd_import_external_skeleton="NO", frag_import_vehicle_windows=False,
                                          ymap_skip_missing_entities=True, ymap_exclude_entities=False,
                                          ymap_box_occluders=False, ymap_model_occluders=False,
                                          ymap_car_generators=False, ymap_instance_entities=True,
                                          ytyp_mlo_instance_entities=True, textures_mode="PACK",
                                          textures_extract_custom_directory="")
        return r

    def compare(tag, ext):
        names = [f"gs_smoke_box.ydr{ext}", f"gs_smoke_col.ybn{ext}", f"gs_smoke.ytyp{ext}"]
        r = reimport(names, tag)
        d = next((o for o in bpy.context.scene.objects if o.sollum_type == SollumType.DRAWABLE and o.name.startswith("gs_smoke_box")), None)
        if d is None:
            step(f"reimport_{tag}", False, result=list(r), reason="drawable not found"); return
        st = stats(d)
        col = next((o for o in bpy.context.scene.objects if o.sollum_type == SollumType.BOUND_COMPOSITE and o.name.startswith("gs_smoke_col")), None)
        col_tris = 0
        if col:
            col_tris = sum(len(c.data.polygons) for c in col.children_recursive if c.type == "MESH")
        ytyps = [(y.name, [a.name for a in y.archetypes]) for y in bpy.context.scene.ytyps]
        s = src_stats
        same_geo = st["unique_positions"] == s["unique_positions"] and st["tris"] == s["tris"]  # GTA vertex buffers split verts per normal/UV
        # a drawable is exported in its local space; the YDR has no world placement — compare local bbox
        lb = [[round(st["bbox"][0][i] - st["location"][i], 3) for i in range(3)], [round(st["bbox"][1][i] - st["location"][i], 3) for i in range(3)]]
        ls = [[round(s["bbox"][0][i] - s["location"][i], 3) for i in range(3)], [round(s["bbox"][1][i] - s["location"][i], 3) for i in range(3)]]
        same_box = all(abs(a - b) < 1e-3 for x, y in zip(lb, ls) for a, b in zip(x, y))
        same_shader = st["shaders"] == s["shaders"]
        tex_ok = any("gs_smoke_diffuse" in i for i in st["images"])
        ok = r == {"FINISHED"} and same_geo and same_box and same_shader and tex_ok and st["bounds"] == 1 and col_tris >= 6 \
            and ("gs_smoke", ["gs_smoke_box"]) in ytyps
        step(f"reimport_{tag}", ok, result=list(r), stats=st, local_bbox=lb, src_local_bbox=ls, same_geo=same_geo,
             same_bbox=same_box, same_shader=same_shader, embedded_texture=tex_ok, static_col_polys=col_tris, ytyps=ytyps)
        return d

    if NATIVE_OK:
        d = compare("native", "")
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLEND_DIR, "gs_smoke_reimport_native.blend"))
        # preview render of the re-imported native asset (GUI Blender only)
        if not bpy.app.background and d is not None:
            try:
                sc = bpy.context.scene
                cam_data = bpy.data.cameras.new("gs_cam"); cam = bpy.data.objects.new("gs_cam", cam_data)
                sc.collection.objects.link(cam); sc.camera = cam
                tgt = d.matrix_world.translation + Vector((0, 0, 0.3))
                cam.location = tgt + Vector((1.6, -1.9, 1.1))
                cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
                sun = bpy.data.objects.new("gs_sun", bpy.data.lights.new("gs_sun", "SUN")); sc.collection.objects.link(sun)
                sun.rotation_euler = (math.radians(50), 0, math.radians(30)); sun.data.energy = 3.0
                sc.world = sc.world or bpy.data.worlds.new("World")
                sc.render.engine = "BLENDER_EEVEE"
                sc.render.resolution_x, sc.render.resolution_y = 960, 540
                sc.render.filepath = os.path.join(SHOTS, "smoke_reimport_native_preview.png")
                bpy.ops.render.render(write_still=True)
                step("preview_render", os.path.isfile(sc.render.filepath), file=sc.render.filepath)
            except Exception:
                step("preview_render", False, error=traceback.format_exc()[-600:])
    if CWXML_OK:
        compare("cwxml", ".xml")
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLEND_DIR, "gs_smoke_reimport_cwxml.blend"))

    # ymap round trip: entity name/position
    ym = "gs_smoke_map.ymap" if NATIVE_OK else "gs_smoke_map.ymap.xml"
    new_scene("gs_smoke_ymap")
    r = bpy.ops.sollumz.import_ymap(directory=EXP, files=[{"name": ym}])
    maps = get_maps(bpy.context)
    ents = [(e.archetype_name, [round(v, 3) for v in e.position]) for g in maps.groups for e in g.entities] if maps else []
    step("ymap_roundtrip", ("gs_smoke_box", [1.5, -2.0, 0.0]) in ents, result=list(r), entities=ents)
except Exception:
    R["errors"].append(traceback.format_exc())
    print(traceback.format_exc())

try:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLEND_DIR, "gs_smoke_test_all_scenes.blend"))
except Exception:
    R["errors"].append("save failed: " + traceback.format_exc()[-300:])
R["go"] = bool(R["steps"]) and all(s["ok"] for s in R["steps"]) and not R["errors"]
out = os.path.join(RAW, "smoke_test_result.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(R, fh, indent=2, ensure_ascii=False, default=str)
print("GS_SMOKE_DONE go=%s -> %s" % (R["go"], out))
