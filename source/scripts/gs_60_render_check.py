# LONG PIG: quick Eevee check renders of the built MLO scene (Blender, not FiveM). Vanilla props are not in the scene:
# they are drawn as plain boxes from their bounds so the composition can be judged.
#   GS_KIT must be set; exec(open(R+'/source/scripts/gs_60_render_check.py', encoding='utf-8').read())
import bpy, os, sys, math, importlib
from mathutils import Vector
ROOT = os.environ["GS_ROOT"]
sys.path.insert(0, ROOT + "/source/scripts")
for k in [k for k in sys.modules if k.startswith("gs_")]:
    sys.modules.pop(k)
K = importlib.import_module(os.environ.get("GS_KIT", "gs_v220_kit"))
# the scene file source/blender/prototype/gs_prototype_mlo.blend must be open (separate console command)
sc = bpy.context.scene
OUT = ROOT + "/docs/render_check"; os.makedirs(OUT, exist_ok=True)
for o in list(bpy.data.objects):
    if o.name.startswith("chk_"):
        bpy.data.objects.remove(o, do_unlink=True)                      # leftovers of an earlier run
for o in list(sc.objects):
    if o.type == "LIGHT" or "bound" in str(getattr(o, "sollum_type", "")).lower():
        o.hide_render = True                                            # scene lights and collision are not part of the picture
col = bpy.data.collections.new("check_props"); sc.collection.children.link(col)
def mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1.0); return m
M = {"fridge": mat("chk_fridge", (0.55, 0.68, 0.8)), "shelf": mat("chk_shelf", (0.75, 0.6, 0.4)), "other": mat("chk_other", (0.6, 0.6, 0.6))}
for n, s, t, zb, yaw in K.vanilla_props():
    if not (s < 9.92 and t < 6.92) or zb > 2.3:
        continue
    mn, mx = K.VB[n]
    size = [mx[i] - mn[i] for i in range(3)]
    if max(size) < 0.25:
        continue
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    me = bpy.data.meshes.new("chk_box")
    me.from_pydata([(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz), (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)], [],
                   [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    o = bpy.data.objects.new("chk_box", me); col.objects.link(o)
    a = math.radians(yaw); cx, cy = (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2
    o.location = (s + cx * math.cos(a) - cy * math.sin(a), t + cx * math.sin(a) + cy * math.cos(a), zb + size[2] / 2)
    o.rotation_euler = (0, 0, a)
    o.data.materials.append(M["fridge" if "fridge" in n or "cooler" in n else "shelf" if "shelves" in n else "other"])
for (x, y) in ((-1.0, 0.5), (2.0, 0.5), (5.0, 0.5), (-1.0, 3.3), (2.0, 3.3), (5.0, 3.3), (2.0, 5.6), (5.0, 5.6), (8.5, 0.5), (8.5, 3.5), (8.5, 6.0)):
    ld = bpy.data.lights.new("chk_l", "POINT"); ld.energy = 130.0; ld.shadow_soft_size = 0.5; ld.color = (1.0, 0.93, 0.82)
    lo = bpy.data.objects.new("chk_l", ld); lo.location = (x, y, 3.1); sc.collection.objects.link(lo)
w = sc.world or bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.55, 1.0); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
try:
    sc.render.engine = "BLENDER_EEVEE"
except Exception:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
cd = bpy.data.cameras.new("chk_cam"); cd.lens = 20; cd.clip_start = 0.05
cam = bpy.data.objects.new("chk_cam", cd); sc.collection.objects.link(cam); sc.camera = cam
VIEWS = {"B1_entrance": ((-1.3, 1.2, 1.65), (6.5, 3.2, 1.25)), "B2_coolers": ((0.4, 5.55, 1.65), (7.0, 1.2, 1.2)), "B3_cashier": ((4.4, -0.4, 1.6), (8.0, 0.4, 1.3)),
         "B4_back": ((6.5, 5.9, 2.0), (0.0, 1.0, 1.0)), "B5_kiosk": ((5.2, 2.6, 1.6), (8.2, 0.2, 1.2)), "B6_service": ((5.0, 3.6, 1.6), (7.6, 4.2, 1.1)),
         "B7_tobacco": ((6.3, 3.3, 1.65), (9.9, 3.3, 1.75)), "B8_snack": ((5.0, 6.3, 1.6), (7.3, 5.5, 0.6)), "B9_front": ((-1.7, 0.5, 1.65), (2.0, 2.9, 0.9)), "C1_unit": ((7.9, 2.2, 1.7), (9.9, 3.6, 1.85)), "C2_open": ((5.6, 6.4, 1.75), (7.2, 5.6, 0.75)), "C3_corner": ((-0.9, 0.9, 1.5), (0.6, -1.0, 0.4))}
done = []
for name, (eye, at) in VIEWS.items():
    if os.environ.get("GS_VIEWS") and name not in os.environ["GS_VIEWS"].split(","):
        continue
    cam.location = eye
    cam.rotation_euler = (Vector(at) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = OUT + "/" + name + ".jpg"
    bpy.ops.render.render(write_still=True); done.append(name)
print("GS_RENDER_DONE", done)
