# Gabagool & Sons — vanilla building reference scene (Blender 5.1 + Sollumz 2.9.0)
# Imports CodeWalker XML exports of the Long Pig block (sc1_14) at their exact world transforms
# (from sc1_14_strm_0.ymap) into collection 01_ORIGINAL_BUILDING_REFERENCE_ONLY, then dumps
# per-geometry analysis + optional renders. Nothing here is exported to the game.
import bpy, os, sys, json, math, importlib, traceback
from mathutils import Vector, Matrix, Quaternion

ROOT = os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons")
XML = os.path.join(ROOT, "reference_vanilla", "xml")
OUT = os.path.join(ROOT, "docs", "_raw")
SHOTS = os.path.join(ROOT, "screenshots", "vanilla_reference")
BLEND = os.path.join(ROOT, "source", "blender", "reference")
for d in (OUT, SHOTS, BLEND):
    os.makedirs(d, exist_ok=True)

SZ = next(n for n in bpy.context.preferences.addons.keys() if n.split(".")[-1] == "sollumz")
P = importlib.import_module(f"{SZ}.sollumz_properties"); ST = P.SollumType

# exact entity transforms from base/patchday sc1_14_strm_0.ymap (CodeWalker XML export)
# GTA ymap stores the INVERSE rotation quaternion for entities (CodeWalker convention: rotation = conj(world rot)).
ENTITIES = {
    "sc1_14_build2":               ((420.745636, -1910.35583, 32.4757), (0.0, 0.0, 0.0, 1.0)),
    "sc1_14_sc1_emissive_sc1_14b": ((420.745636, -1910.35583, 32.4757), (0.0, 0.0, 0.0, 1.0)),
    "sc1_14_detail_03":            ((414.708, -1916.407, 27.634), (0.0, 0.0, 0.0, 1.0)),
    "sc1_14_tacorail":             ((419.712, -1924.225, 24.689), (0.0, 0.0, 0.0, 1.0)),
}
FILES = ["sc1_14_build2.ydr.xml", "sc1_14_sc1_emissive_sc1_14b.ydr.xml", "sc1_14_detail_03.ydr.xml",
         "sc1_14_tacorail.ydr.xml", "sc1_14_0.ybn.xml", "hi@sc1_14_0.ybn.xml", "ma@sc1_14_0.ybn.xml"]


def ensure_coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def reset():
    if bpy.app.background:
        bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    return sc


sc = reset()
ref = ensure_coll("01_ORIGINAL_BUILDING_REFERENCE_ONLY")
log = {"imports": [], "errors": []}
before = set(bpy.data.objects)
for f in FILES:
    p = os.path.join(XML, f)
    if not os.path.isfile(p):
        log["errors"].append(f"missing {p}"); continue
    try:
        r = bpy.ops.sollumz.import_assets(directory=XML, files=[{"name": f}], import_as_asset=False,
                                          split_by_group=True, textures_mode="IMPORT_DIR",
                                          textures_extract_custom_directory="")
        log["imports"].append([f, list(r)])
    except Exception:
        log["errors"].append(f + ": " + traceback.format_exc()[-400:])
new_objs = [o for o in bpy.data.objects if o not in before]
roots = [o for o in new_objs if o.parent is None]
for o in roots:
    base = o.name.split(".")[0]
    for c in list(o.users_collection):
        c.objects.unlink(o)
    ref.objects.link(o)
    for ch in o.children_recursive:
        for c in list(ch.users_collection):
            c.objects.unlink(ch)
        ref.objects.link(ch)
    if base in ENTITIES:
        pos, q = ENTITIES[base]
        o.location = pos
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = Quaternion((q[3], -q[0], -q[1], -q[2]))
    # static collisions (.ybn) are already in world space
    o["gs_reference_only"] = True
bpy.context.view_layer.update()

# ---- geometry analysis of the block drawable -----------------------------------------------
SHOP_C = Vector((420.75, -1910.36))   # build2 origin; shop sits around it (door ~ 422.2,-1906.0)
rows = []
for o in ref.all_objects:
    if o.type != "MESH":
        continue
    mw = o.matrix_world
    vs = [mw @ v.co for v in o.data.vertices]
    if not vs:
        continue
    mn = [min(v[i] for v in vs) for i in range(3)]; mx = [max(v[i] for v in vs) for i in range(3)]
    near = sum(1 for v in vs if (Vector((v.x, v.y)) - SHOP_C).length < 16.0)
    mats = [m.name for m in o.data.materials if m]
    shader = []
    for m in o.data.materials:
        if m is None: continue
        sp = getattr(m, "shader_properties", None)
        shader.append(sp.filename if sp else "")
    imgs = sorted({n.image.name for m in o.data.materials if m and m.node_tree
                   for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image})
    rows.append({"object": o.name, "parent": o.parent.name if o.parent else None, "sollum_type": str(o.sollum_type),
                 "verts": len(vs), "polys": len(o.data.polygons), "verts_within_16m": near,
                 "world_min": [round(x, 3) for x in mn], "world_max": [round(x, 3) for x in mx],
                 "materials": mats, "shaders": shader, "images": imgs})
rows.sort(key=lambda r: -r["verts_within_16m"])
log["objects"] = rows

with open(os.path.join(OUT, "vanilla_reference_analysis.json"), "w", encoding="utf-8") as fh:
    json.dump(log, fh, indent=1, ensure_ascii=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLEND, "longpig_vanilla_reference.blend"))
print("GS_REF_DONE objects:", len(rows), "errors:", len(log["errors"]))
for e in log["errors"]:
    print("ERR", e)
