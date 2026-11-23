# LONG PIG — build the exterior security roller shutters (own models) with Sollumz.
# Run inside Blender (same way as gs_20):  exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_38_build_shutters.py").read())
# Container dry run:  GS_ROOT=... python run_script.py -- gs_38_build_shutters.py   (CWXML)
# Output: build/shutters/export_native|export_cwxml/  lp_shut_*.ydr (embedded textures, embedded collision on curtain parts)
#         + lp_shutters.ytyp; copied into build/gabagool_sons_mlo/stream/shutters/ when the resource folder exists.
#         docs/_raw/shutters_build_result[_cwxml_dryrun].json
import bpy, bmesh, os, sys, math, json, shutil, importlib, traceback, datetime
from pathlib import Path

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
SCRIPTS = ROOT / "source" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import gs_shutter_geometry as SH
importlib.reload(SH)

import szio
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion, is_provider_available

NATIVE = is_provider_available(AssetFormat.NATIVE)
FMT = AssetFormat.NATIVE if NATIVE else AssetFormat.CWXML
TARGET = [AssetTarget(FMT, AssetVersion.GEN8)]
EXT = "" if NATIVE else ".xml"
OUTD = ROOT / "build" / "shutters" / ("export_native" if NATIVE else "export_cwxml")
RES = ROOT / "build" / "gabagool_sons_mlo"
TEX = ROOT / "source" / "textures" / "shutters"
RAW = ROOT / "docs" / "_raw"
BLEND = ROOT / "source" / "blender" / "shutters"
for d in (OUTD, RAW, BLEND):
    d.mkdir(parents=True, exist_ok=True)
YTYP = "lp_shutters"

SZ = next(n for n in bpy.context.preferences.addons.keys() if n.split(".")[-1] == "sollumz")


def M(sub):
    return importlib.import_module(f"{SZ}.{sub}")


P = M("sollumz_properties"); SollumType = P.SollumType; ArchetypeType = P.ArchetypeType
dh = M("tools.drawablehelper"); boh = M("tools.boundhelper"); shm = M("ydr.shader_materials"); colm = M("ybn.collision_materials")
matops = M("ydr.operators.materials")

R = {"timestamp": datetime.datetime.now().isoformat(timespec="seconds"), "blender": bpy.app.version_string, "format": FMT.name,
     "steps": [], "errors": []}


def step(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    print(("PASS " if ok else "FAIL ") + name, json.dumps(kw, default=str)[:900] if kw else "")
    return ok


def image(name):
    p = TEX / f"{name}.dds"
    if not p.is_file():
        raise FileNotFoundError(p)
    img = bpy.data.images.load(str(p), check_existing=True)
    img.name = f"{name}.dds"
    return img


def shutter_material():
    mat = shm.create_shader("normal_spec.sps")
    mat.name = "lp7_shutter"
    for node_name, tex in (("DiffuseSampler", "lp7_shutter"), ("BumpSampler", "lp7_flat_n"), ("SpecSampler", "lp7_shutter_s")):
        node = mat.node_tree.nodes.get(node_name)
        node.image = image(tex)
        node.texture_properties.embedded = True
    for pname, val in (("specularIntensityMult", 0.6), ("specularFalloffMult", 40.0), ("specularFresnel", 0.97), ("bumpiness", 0.4)):
        node = mat.node_tree.nodes.get(pname)
        node.set(0, float(val))
    return mat


def colmat(name):
    for i, m in enumerate(colm.collisionmats):
        if m.name == name:
            return colm.create_collision_material_from_index(i)
    raise KeyError(name)


def cpv(co):
    # exterior props: R = natural ambient (full), G = artificial ambient (almost none -> no glow at night)
    return (0.92, 0.04, 0.0, 1.0)


def mesh_from_faces(name, faces, mat, sc):
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
            vs = [bm.verts.new(v.co) for v in vs]
            bf = bm.faces.new(vs)
        bf.material_index = 0
        for loop, (u, v) in zip(bf.loops, f["uv"]):
            loop[uv].uv = (u, v)
    bm.normal_update(); bm.to_mesh(me); bm.free()
    col = me.color_attributes.new("Color 1", "BYTE_COLOR", "CORNER")
    for li in range(len(me.loops)):
        col.data[li].color_srgb = cpv(None)
    me.color_attributes.active_color = col
    me.color_attributes.render_color_index = me.color_attributes.active_color_index
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    sc.collection.objects.link(obj)
    return obj


def collision_child(drawable, box, name):
    x0, x1, y0, y1, z0, z1 = box
    me = bpy.data.meshes.new(name + "_col")
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for q in idx:
        bm.faces.new([vs[i] for i in q])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    me.materials.append(colmat("METAL_SOLID_MEDIUM"))
    o = bpy.data.objects.new(name + "_col", me)
    bpy.context.scene.collection.objects.link(o)
    comp = boh.convert_obj_to_composite(o, SollumType.BOUND_GEOMETRYBVH, "General (Default)")
    comp.name = name + "_col"
    comp.parent = drawable
    return comp


def build():
    bpy.ops.wm.read_homefile(use_empty=True) if bpy.app.background else None
    sc = bpy.data.scenes.new("lp_shutters") if not bpy.app.background else bpy.context.scene
    if not bpy.app.background and bpy.context.window is not None:
        bpy.context.window.scene = sc
    sc.name = "lp_shutters"
    mat = shutter_material()
    drawables = {}
    for name, (faces, cbox) in SH.models().items():
        obj = mesh_from_faces(name, faces, mat, sc)
        matops.post_create_shader_update_object(obj, mat)
        d = dh.convert_obj_to_drawable(obj)
        d.name = name
        if cbox is not None:
            collision_child(d, cbox, name)
        drawables[name] = d
    ytyp = sc.ytyps.add(); ytyp.name = YTYP
    sc.ytyp_index = len(sc.ytyps) - 1
    for name, d in drawables.items():
        a = ytyp.new_archetype(ArchetypeType.BASE)
        a.name = name
        a.asset = d
        a.lod_dist = 150.0
        a.flags.total = "0"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND / "lp_shutters.blend"))
    step("build_scene", True, models=list(drawables), tris={n: sum(len(p.vertices) - 2 for o in d.children_recursive if o.type == "MESH"
                                                                 and o.sollum_type == SollumType.DRAWABLE_MODEL for p in o.data.polygons)
                                                             for n, d in drawables.items()})
    return list(drawables)


def export(names):
    for f in OUTD.iterdir():
        if f.is_file():
            f.unlink()
    res = bpy.ops.sollumz.export_assets(
        directory=str(OUTD), direct_export=True, use_custom_settings=True,
        target_formats={FMT.name}, target_versions={"GEN8"}, limit_to_selected=False,
        exclude_skeleton=False, ymap_exclude_entities=False, ymap_box_occluders=False,
        ymap_model_occluders=False, ymap_car_generators=False, apply_transforms=False,
        mesh_domain="FACE_CORNER", export_ytyps=True, export_ytyps_include="ALL",
        export_ymaps=False, export_ymaps_include="ALL", export_ytds=False, export_ytds_include="ALL")
    files = {f.name: f.stat().st_size for f in OUTD.iterdir() if f.is_file()}
    want = [f"{n}.ydr{EXT}" for n in names] + [f"{YTYP}.ytyp{EXT}"]
    missing = [w for w in want if w not in files]
    step("export", res == {"FINISHED"} and not missing, files=files, missing=missing)
    return files


def validate(names):
    v = {}
    ok = True
    for n in names:
        d = szio.try_load_asset(OUTD / f"{n}.ydr{EXT}")
        if d is None:
            ok = False; v[n] = "load failed"; continue
        tex = sorted(d.shader_group.embedded_textures) if d.shader_group else []
        bnd = getattr(d, "bounds", None) if hasattr(d, "bounds") else getattr(d, "bound", None)
        want_bound = not n.startswith("lp_shut_rail")
        v[n] = {"textures": tex, "bound": bnd is not None, "shaders": [s.name for s in d.shader_group.shaders]}
        ok = ok and set(tex) >= {"lp7_shutter", "lp7_shutter_s", "lp7_flat_n"} and (bnd is not None) == want_bound
    yt = szio.try_load_asset(OUTD / f"{YTYP}.ytyp{EXT}")
    arch = sorted(a.name for a in yt.archetypes) if yt else []
    v["ytyp"] = {"archetypes": arch, "lod": sorted({float(a.lod_dist) for a in yt.archetypes}) if yt else []}
    ok = ok and arch == sorted(names)
    step("validate", ok, **v)
    return v


def deploy():
    if not RES.is_dir():
        step("deploy", True, skipped="resource folder not built yet (gs_20 copies build/shutters on its next run)")
        return
    dst = RES / "stream" / "shutters"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for f in OUTD.iterdir():
        if f.is_file():
            shutil.copy2(f, dst / f.name)
    step("deploy", True, to=str(dst), files=sorted(p.name for p in dst.iterdir()))


try:
    names = build()
    export(names)
    R["validation"] = validate(names)
    deploy()
except Exception:
    R["errors"].append(traceback.format_exc())
    print(traceback.format_exc())
R["go"] = bool(R["steps"]) and all(s["ok"] for s in R["steps"]) and not R["errors"]
out = RAW / ("shutters_build_result.json" if NATIVE else "shutters_build_result_cwxml_dryrun.json")
out.write_text(json.dumps(R, indent=1, default=str), encoding="utf-8")
print("GS_SHUTTERS_DONE go=%s format=%s -> %s" % (R["go"], FMT.name, out))
