# Offline preview of one own prop after gs_44 (Blender render, not FiveM). GS_PROP = object name prefix.
import bpy, os, math
from mathutils import Vector
RT = os.environ["GS_ROOT"]; NAME = os.environ.get("GS_PROP", "lp_roller")
sc = bpy.context.scene
keep = set()
for o in bpy.data.objects:
    if o.name.startswith(NAME):
        keep.add(o); keep.update(o.children_recursive)
for o in bpy.data.objects:
    o.hide_render = o not in keep
root = [o for o in keep if o.parent not in keep][0]
c = root.matrix_world.translation
cam = bpy.data.objects.new("pv_cam", bpy.data.cameras.new("pv_cam")); sc.collection.objects.link(cam)
cam.location = c + Vector((1.1, -2.6, 1.25)); cam.data.lens = 40
d = (c + Vector((0.0, 0.0, 1.0))) - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
sun = bpy.data.objects.new("pv_sun", bpy.data.lights.new("pv_sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(55), 0.0, math.radians(25))
w = bpy.data.worlds.new("pv_w"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.80, 0.9, 1.0); sc.world = w
sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y = 900, 1000
sc.render.image_settings.file_format = "JPEG"
sc.render.filepath = RT + "/docs/render_check/" + NAME + ".jpg"
bpy.ops.render.render(write_still=True)
print("PREVIEW_DONE", sc.render.filepath)
