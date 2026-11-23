# Dump world-space faces (per material) of the vanilla block drawables + collision primitives near
# the Long Pig shop to JSON for plotting/footprint analysis. Run after gs_10 (opens the saved blend).
import bpy, os, json
from mathutils import Vector

ROOT = os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons")
blend = os.path.join(ROOT, "source", "blender", "reference", "longpig_vanilla_reference.blend")
if not any("drawable_model" in str(o.sollum_type) for o in bpy.data.objects):
    bpy.ops.wm.open_mainfile(filepath=blend)
print("objects in file:", len(bpy.data.objects))
C = Vector((420.75, -1910.36, 0))
R = 22.0
out = {"faces": [], "col": []}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    mw = o.matrix_world
    st = str(o.sollum_type)
    if "drawable_model" in st:
        me = o.data
        for p in me.polygons:
            vs = [mw @ me.vertices[i].co for i in p.vertices]
            cx = sum(v.x for v in vs) / len(vs); cy = sum(v.y for v in vs) / len(vs)
            if (Vector((cx, cy, 0)) - C).length > R:
                continue
            m = me.materials[p.material_index] if p.material_index < len(me.materials) else None
            tex = ""
            if m and m.node_tree:
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n.image and n.name in ("DiffuseSampler", "DiffuseSampler2"):
                        tex = n.image.name; break
            n_w = (mw.to_3x3() @ p.normal).normalized()
            out["faces"].append({"obj": o.parent.name if o.parent else o.name, "mat": m.name if m else "",
                                 "shader": m.shader_properties.filename if m else "", "tex": tex,
                                 "v": [[round(v.x, 3), round(v.y, 3), round(v.z, 3)] for v in vs],
                                 "n": [round(n_w.x, 3), round(n_w.y, 3), round(n_w.z, 3)], "area": round(p.area, 4)})
    elif "bound" in st:
        vs = [mw @ Vector(c) for c in o.bound_box]
        cx = sum(v.x for v in vs) / 8; cy = sum(v.y for v in vs) / 8
        if (Vector((cx, cy, 0)) - C).length > R:
            continue
        mats = [m.name for m in o.data.materials if m]
        out["col"].append({"obj": o.name, "type": st, "bb": [[round(v.x, 3), round(v.y, 3), round(v.z, 3)] for v in vs],
                           "mats": mats, "file": o.parent.parent.name if o.parent and o.parent.parent else (o.parent.name if o.parent else "")})
p = os.path.join(ROOT, "docs", "_raw", "vanilla_faces_near_shop.json")
with open(p, "w") as fh:
    json.dump(out, fh)
print("GS_FACES", len(out["faces"]), "col", len(out["col"]), p)
