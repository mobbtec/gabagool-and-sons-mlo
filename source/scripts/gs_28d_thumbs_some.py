# LONG PIG — v0.2.1: thumbnails of the shortlisted vanilla props (internal reference only, never shipped).
# Renders every reference_vanilla/catalogue/<name>.ydr.xml (exported by gs_28b) in a temporary scene with EEVEE.
# Blender 5.1 console on the PC (the open .blend is NOT saved; the temporary scene is deleted at the end):
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_28c_catalogue_thumbs.py", encoding="utf-8").read())
# Output: docs/_raw/catalogue_thumbs/<name>.png
import bpy, os, glob, math, traceback
from pathlib import Path
from mathutils import Vector

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
SRC = ROOT / "reference_vanilla" / "catalogue"
OUT = ROOT / "docs" / "_raw" / "catalogue_thumbs"
OUT.mkdir(parents=True, exist_ok=True)
names = sorted(Path(p).name[:-8] for p in glob.glob(str(SRC / "*.ydr.xml")))
_w = set(x.strip().lower() for x in os.environ.get("GS_THUMBS", "").split(",") if x.strip())
names = [n for n in names if n.lower() in _w]

win = bpy.context.window
old_scene = win.scene
sc = bpy.data.scenes.new("gs_catalogue_tmp")
win.scene = sc
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 360
sc.render.film_transparent = False
w = bpy.data.worlds.new("gs_cat_world"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.30, 0.28, 0.26, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
cam = bpy.data.objects.new("gs_cat_cam", bpy.data.cameras.new("gs_cat_cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
lights = []
for i, e in enumerate((400, 150, 200)):
    L = bpy.data.objects.new(f"gs_cat_L{i}", bpy.data.lights.new(f"gs_cat_L{i}", "AREA")); sc.collection.objects.link(L); lights.append(L)
done, errs = [], []
for n in names:
    before = set(sc.collection.all_objects)
    try:
        bpy.ops.sollumz.import_assets(directory=str(SRC) + os.sep, files=[{"name": n + ".ydr.xml"}])
    except Exception:
        errs.append(n + ": " + traceback.format_exc()[-200:]); continue
    new = [o for o in sc.collection.all_objects if o not in before]
    meshes = [o for o in new if o.type == "MESH" and "bound" not in str(getattr(o, "sollum_type", "")).lower()]
    for o in new:
        if o.type == "MESH" and o not in meshes:
            o.hide_render = True
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    if pts:
        mn = Vector([min(p[k] for p in pts) for k in range(3)]); mx = Vector([max(p[k] for p in pts) for k in range(3)])
        c = (mn + mx) / 2; r = max((mx - mn).length / 2, 0.05)
        d = Vector((-0.55, -1.0, 0.45)).normalized()            # GTA props mostly face -Y: front-left view
        cam.location = c + d * r * 3.0
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        for L, (dx, dy, dz, e) in zip(lights, ((-1, -1.5, 1.5, 300), (1.5, -0.5, 1.0, 120), (0, 1.5, 2.0, 150))):
            L.location = c + Vector((dx, dy, dz)) * r * 2.5
            L.data.energy = e * r * r * 4; L.data.size = r * 2
            L.rotation_euler = (c - L.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = str(OUT / f"{n}.png")
        try:
            bpy.ops.render.render(write_still=True)
            done.append(n)
        except Exception:
            errs.append(n + " render: " + traceback.format_exc()[-200:])
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
win.scene = old_scene
for o in list(sc.collection.all_objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.data.scenes.remove(sc)
print("GS_CAT_THUMBS_DONE rendered=%d errors=%d %s" % (len(done), len(errs), errs[:3]))
