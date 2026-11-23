# Gabagool & Sons — offline preview of the v0.2.1 hero build INSIDE the (overridden) vanilla shell (Blender, Cycles).
# GS_LIGHTING=day|night (night: no sun, dark sky). Interior lights: Blender power from the GTA intensity x falloff.
# Not a substitute for the in-game test: it only proves that the interior lines up with the real
# openings of sc1_14_build2 and that the overridden shell is open at W1, W2 and D1.
import bpy, os, sys, math, importlib, json
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion, Euler

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
sys.path.insert(0, str(ROOT / "source" / "scripts"))
import gs_overrides as G
import gs_proto_geometry as PG
import gs_slice_geometry as SG
import gs_v021_kit as K021
import gs_v023_vb
import gs_v023_kit as K023             # 0.2.3 90s lobby
import gs_v024_kit as K024             # 0.2.4 (globe pendant reused)
import gs_v025_vb
import gs_v025_kit as K025             # 0.2.5 style reset
import gs_v026_vb
import gs_v026_kit as K026             # 0.2.6 finish-and-refine
import gs_v027_vb
import gs_v027_kit as K027             # 0.2.7 owner's in-game feedback
import gs_v028_vb, gs_boh_kit
import gs_v028_kit as K                # 0.2.8 back of house
# 0.2.9: GS_KIT selects the kit module (before/after renders), default = newest available
_kit = os.environ.get('GS_KIT') or ('gs_v029_kit' if (ROOT / 'source' / 'scripts' / 'gs_v029_kit.py').is_file() else 'gs_v028_kit')
K = importlib.import_module(_kit)
importlib.reload(G); importlib.reload(PG); importlib.reload(SG); importlib.reload(K021); importlib.reload(gs_v023_vb); importlib.reload(K023); importlib.reload(K024); importlib.reload(gs_v025_vb); importlib.reload(K025); importlib.reload(gs_v026_vb); importlib.reload(K026); importlib.reload(gs_v027_vb); importlib.reload(K027); importlib.reload(gs_v028_vb); importlib.reload(gs_boh_kit); importlib.reload(K)

SZ = next(n for n in bpy.context.preferences.addons.keys() if n.split(".")[-1] == "sollumz")
SollumType = importlib.import_module(f"{SZ}.sollumz_properties").SollumType
BUILD = ROOT / "build" / "prototype"
NATIVE_DIR = BUILD / "vanilla_override_native"
OVR = NATIVE_DIR if (NATIVE_DIR / "sc1_14_build2.ydr").is_file() else BUILD / "vanilla_override_cwxml"
EXT = "" if OVR == NATIVE_DIR else ".xml"
OUT = ROOT / "screenshots" / os.environ.get("GS_OUTDIR", "prototype_preview")
OUT.mkdir(parents=True, exist_ok=True)
SAMPLES = int(os.environ.get("GS_SAMPLES", "24"))
RES = (int(os.environ.get("GS_W", "1280")), int(os.environ.get("GS_H", "720")))

bpy.ops.wm.open_mainfile(filepath=os.environ.get('GS_BLEND') or str(ROOT / "source" / "blender" / "prototype" / "gs_prototype_mlo.blend"))
sc = bpy.context.scene

# ---- MLO instance transform: parent the MLO drawables to an empty placed like the ymap entity
inst = bpy.data.objects.new("MLO_INSTANCE_gs_longpig_int", None)
sc.collection.objects.link(inst)
inst.location = (float(G.O2[0]), float(G.O2[1]), G.FLOOR_Z)
inst.rotation_euler = (0, 0, math.radians(G.YAW_DEG))
by_name = {o.name: o for o in sc.objects}
for nm in ("gs_proto_shell", "gs_proto_glass_w1", "gs_proto_glass_w2", "gs_slice_furniture", "gs_v021_hall", "gs_boh",
           "gs_ah_open", "gs_ah_closed"):
    if nm in by_name:
        by_name[nm].parent = inst
# 0.2.9: AFTER HOURS entity sets - GS_AH=open (default, = ymap default set) | closed
AH = os.environ.get("GS_AH", "open")
_set_active = "lp_closed" if AH == "closed" else "lp_open"
for nm, setn in (("gs_ah_open", "lp_open"), ("gs_ah_closed", "lp_closed")):
    if nm in by_name:
        for o in [by_name[nm]] + list(by_name[nm].children_recursive):
            o.hide_render = (setn != _set_active) or o.hide_render
# 0.2.0: vanilla props of the slice (internal reference XML from gs_25d, never shipped) at their MLO entity transforms
PROPS_DIR = ROOT / "reference_vanilla" / "props"
CAT_DIR = ROOT / "reference_vanilla" / "catalogue"
NO_VANILLA = os.environ.get("GS_NO_VANILLA", "0") == "1"      # 0.2.6: renders of our own geometry only (photo textures)
_ents = [] if NO_VANILLA else list(K.vanilla_entities())
if not NO_VANILLA and hasattr(K, "set_entities"):
    _ents += [e for e in K.set_entities()[_set_active] if not e[0].startswith("gs_ah_")]
if not NO_VANILLA and getattr(K, "FANS", None):                  # 0.2.6 fans are client-side in game; shown here for review
    _ents += [(K.FAN_MODEL, (fs, ft, K.CEIL), math.radians(17.0 * k)) for k, (fs, ft) in enumerate(K.FANS)]
for arch, pos, yaw in _ents:
    pdir = PROPS_DIR if (PROPS_DIR / f"{arch}.ydr.xml").is_file() else CAT_DIR
    if not (pdir / f"{arch}.ydr.xml").is_file():
        print("missing prop reference", arch); continue
    before = set(bpy.data.objects)
    bpy.ops.sollumz.import_assets(directory=str(pdir) + os.sep, files=[{"name": f"{arch}.ydr.xml"}])
    for o in [o for o in bpy.data.objects if o not in before]:
        if o.parent is None:
            o.parent = inst
            o.location = pos
            if isinstance(yaw, (tuple, list)):               # 0.2.9 full quaternion (chairs up on the tables)
                o.rotation_mode = "QUATERNION"
                o.rotation_quaternion = tuple(yaw)
            else:
                o.rotation_euler = (0, 0, yaw)
# 0.2.7: exterior security shutters (own models, build/shutters) at curtain progress GS_SHUTTERS (0 open .. 1 closed)
if os.environ.get("GS_SHUTTERS") not in (None, ""):
    import gs_shutter_geometry as SHG
    importlib.reload(SHG)
    _sp = float(os.environ["GS_SHUTTERS"])
    _sdir = ROOT / "build" / "shutters" / "export_cwxml"
    for _m, (_s, _t, _z), (_ix, _iy), _vis in SHG.placements(SHG.ease(_sp)):
        if not _vis:
            continue
        before = set(bpy.data.objects)
        bpy.ops.sollumz.import_assets(directory=str(_sdir) + os.sep, files=[{"name": f"{_m}.ydr.xml"}])
        for o in [o for o in bpy.data.objects if o not in before]:
            if "bound" in str(o.sollum_type).lower() or o.name.endswith("_col"):
                o.hide_render = True
            if o.parent is None:
                o.parent = inst
                o.location = (_s, _t, _z)
                o.rotation_euler = (0, 0, math.atan2(-_ix, _iy))
# 0.1.5: vanilla GTA doors (internal reference XML exported by gs_24, never shipped) at the MLO entity transforms
DOORS_DIR = ROOT / "reference_vanilla" / "doors"
open_deg = float(os.environ.get("GS_DOOR_OPEN", "0"))
for did, arch, pos, yaw, pk in ([] if NO_VANILLA else PG.vanilla_door_entities()):   # interior doors: K.vanilla_entities()
    if not (DOORS_DIR / f"{arch}.ydr.xml").is_file():
        print("missing door reference", arch); continue
    before = set(bpy.data.objects)
    bpy.ops.sollumz.import_assets(directory=str(DOORS_DIR) + os.sep, files=[{"name": f"{arch}.ydr.xml"}])
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None:
            o.parent = inst
            o.location = pos
            o.rotation_euler = (0, 0, yaw + math.radians(open_deg) * (1 if did != "gs_d1_right" else -1))
# textures of the door references: PNG next to the DDS (Blender cannot read some DXT1 DDS), drop missing maps
_idx = {}
for f in list(DOORS_DIR.rglob("*.png")) + list(PROPS_DIR.rglob("*.png")) + list(CAT_DIR.rglob("*.png")) + \
        list((ROOT / "source" / "textures" / "slice").glob("*.png")) + list((ROOT / "source" / "textures" / "v021").glob("*.png")):
    _idx.setdefault(f.stem.lower(), str(f))
for im in bpy.data.images:
    k = os.path.splitext(os.path.basename(im.filepath or im.name))[0].lower()
    if k in _idx and not (im.filepath and os.path.isfile(bpy.path.abspath(im.filepath)) and im.size[0] > 0 and im.filepath.endswith(".png")):
        if "gs_proto" in k:
            continue
        im.filepath = _idx[k]; im.source = "FILE"; im.reload()
for m in bpy.data.materials:
    if not m.node_tree or "gs_proto" in m.name:
        continue
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type == "TEX_IMAGE" and nd.name != "DiffuseSampler" and (nd.image is None or not nd.image.filepath):
            for l in list(nd.outputs[0].links) + list(nd.outputs[1].links):
                nt.links.remove(l)
    ds = nt.nodes.get("DiffuseSampler"); bs = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if ds and bs and ds.image is not None and ds.image.filepath:
        for l in list(bs.inputs["Base Color"].links):
            nt.links.remove(l)
        nt.links.new(ds.outputs[0], bs.inputs["Base Color"])
# 0.2.9: preview-only fallback - a texture that is still missing renders neutral grey instead of Blender's magenta
for m in bpy.data.materials:
    if not m.node_tree or "gs_proto" in m.name:
        continue
    nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    for nd in list(nt.nodes):
        if nd.type != "TEX_IMAGE":
            continue
        im = nd.image
        ok = im is not None and (im.packed_file is not None or (im.filepath and os.path.isfile(bpy.path.abspath(im.filepath))))
        if not ok:
            for l in list(nd.outputs[0].links) + list(nd.outputs[1].links):
                nt.links.remove(l)
            if bs is not None and nd.name == "DiffuseSampler":
                bs.inputs["Base Color"].default_value = (0.45, 0.45, 0.44, 1.0)
col = by_name.get("gs_longpig_int")
if col:
    col.hide_render = True
    col.parent = inst

# ---- import the overridden vanilla shell (+ night emissive) at its ymap entity position
if not NO_VANILLA:
    before = set(bpy.data.objects)
    bpy.ops.sollumz.import_assets(directory=str(OVR), files=[{"name": f"sc1_14_build2.ydr{EXT}"}], import_as_asset=False,
                                  split_by_group=True, textures_mode="PACK", textures_extract_custom_directory="")
    new = [o for o in bpy.data.objects if o not in before]
    root = next(o for o in new if o.sollum_type == SollumType.DRAWABLE)
    root.location = tuple(G.ENT_BUILD2)
    for o in new:
        if o.type == "MESH":
            o.hide_render = False

# never render collision meshes
for o in sc.objects:
    if "bound" in str(o.sollum_type).lower():
        o.hide_render = True

# ---- light + world
NIGHT = os.environ.get("GS_LIGHTING", "day") == "night"
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(42), 0, math.radians(200)); sun.data.energy = 0.0 if NIGHT else 4.0; sun.data.angle = math.radians(2)
world = sc.world or bpy.data.worlds.new("World"); sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.02, 0.03, 0.06, 1) if NIGHT else (0.55, 0.68, 0.85, 1)
bg.inputs[1].default_value = 0.3 if NIGHT else 0.9
# interior lights: Blender power from the GTA light (intensity x falloff), radius 3 cm
# 0.2.2: spots too; corona-only lights draw a glare sprite in game and light nothing -> no energy in the preview.
# Energy ~ I * R^2 (range-limited GTA light), calibrated to the 0.2.1 look for R ~ 3-4 m.
for o in sc.objects:
    if o.type == "LIGHT" and o.data.type in ("POINT", "SPOT"):
        lp = getattr(o.data, "light_properties", None)
        lf = getattr(o.data, "light_flags", None)
        I = float(getattr(lp, "intensity", 1.0)) if lp else 1.0
        R = float(getattr(lp, "falloff", 4.0)) if lp else 4.0
        co = bool(getattr(lf, "corona_only", False)) if lf else False
        try:                                                          # 0.2.7: day / night light sets (hour masks)
            tf = int(o.data.time_flags.total)
        except Exception:
            tf = 0xFFFFFF
        hour_on = bool(tf >> (23 if NIGHT else 12) & 1)
        o.data.energy = 0.0 if (co or not hour_on) else 8.0 * I * R * R
        o.data.shadow_soft_size = 0.03
# ground plane under everything (the vanilla terrain is a different drawable)
bpy.ops.mesh.primitive_plane_add(size=80, location=(415, -1915, 24.43))
gp = bpy.context.active_object
gm = bpy.data.materials.new("ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.31, 0.30, 1)
gp.data.materials.append(gm)

sc.render.engine = "CYCLES"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = os.environ.get("GS_DENOISE", "0") == "1"
try:
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
# preview only: glass_env as clear glass (the Sollumz node setup renders it milky in Cycles)
for m in bpy.data.materials:
    if m.node_tree and ("glass" in m.name.lower()):
        bs = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bs:
            for l in list(bs.inputs["Alpha"].links):
                m.node_tree.links.remove(l)
            bs.inputs["Alpha"].default_value = 0.12
            for l in list(bs.inputs["Base Color"].links):
                m.node_tree.links.remove(l)
            bs.inputs["Base Color"].default_value = (0.85, 0.92, 0.9, 1)
            bs.inputs["Roughness"].default_value = 0.03
            m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.film_transparent = False
try:
    sc.cycles.device = "CPU"
except Exception:
    pass

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 22


def world_of(s, t, z):
    w = G.to_world(s, t, z)
    return Vector((float(w[0]), float(w[1]), float(w[2])))


VIEWS = {
    "01_street_W1": ((3.46, -9.5, 1.7), (3.46, 0.0, 1.5)),
    "02_sidewalk_D1": ((-4.6, -2.6, 1.7), (-0.6, 1.4, 1.3)),
    "03_side_W2": ((-10.0, 5.0, 1.7), (0.0, 5.0, 1.5)),
    "04_inside_to_W1_D1": ((9.0, 6.5, 1.65), (1.0, -1.0, 1.4)),
    "05_inside_to_W2": ((5.5, 4.9, 1.65), (-3.0, 4.9, 1.6)),
    # 0.1.5 door checks
    "06_inside_D1": ((2.6, 3.3, 1.6), (-1.4, -0.4, 1.3)),
    "07_inside_D2": ((14.52, 2.4, 1.6), (14.52, -1.4, 1.3)),
    "08_outside_D2": ((14.52, -4.6, 1.6), (14.52, -1.4, 1.3)),
    "09_inside_D3": ((0.8, 9.8, 1.6), (-3.0, 9.8, 1.4)),
    "10_outside_D3": ((-6.5, 9.8, 1.6), (-3.0, 9.8, 1.4)),
    "11_inside_W1_sill": ((3.46, 2.2, 1.3), (3.46, -1.3, 0.9)),
    # 0.2.0 vertical slice
    "12_slice_booths": ((6.4, 2.6, 1.6), (1.6, -0.8, 0.9)),
    "13_slice_cases": ((4.6, 2.2, 1.6), (7.6, 3.2, 1.0)),
    "14_slice_back_counter": ((7.4, 0.2, 1.65), (9.9, 4.0, 1.6)),
    "15_slice_hall_wide": ((-1.8, 5.8, 2.2), (6.5, 0.8, 1.0)),
    "16_slice_street_W1": ((3.46, -7.5, 1.6), (3.46, 1.0, 1.2)),
    "17_slice_booth_close": ((2.9, 0.5, 1.25), (1.4, -0.9, 0.75)),
    # 0.2.7 security shutters (exterior)
    "SH_W1": ((3.46, -8.5, 1.7), (3.46, -1.5, 1.6)),
    "SH_D1": ((-5.2, -3.4, 1.7), (-1.5, 0.35, 1.3)),
    "SH_W2": ((-9.0, 4.9, 1.7), (-3.2, 4.9, 1.6)),
    "SH_D1_TOP": ((-2.75, -1.35, 1.85), (-1.0, 0.25, 2.55)),
    "SH_CORNER": ((-6.0, -5.0, 1.8), (0.5, 1.0, 1.4)),
}
for _k, (_e, _t, _lab) in K.CAM_VIEWS.items():
    VIEWS[_k] = (_e, _t)
# 0.2.6: viewpoints for the "old snapshots" in the wall atlas (rendered with GS_NO_VANILLA=1, our own geometry only)
VIEWS.update({"photo_counter": ((4.2, 2.6, 1.5), (7.6, 3.1, 1.2)), "photo_booths": ((4.6, 1.1, 1.3), (2.4, -0.9, 0.8)),
              "photo_family": ((5.6, 4.6, 1.5), (7.4, 5.4, 1.3))})
only = os.environ.get("GS_VIEWS")
results = {}
for name, (eye, tgt) in VIEWS.items():
    if only and name not in only.split(","):
        continue
    e = world_of(*[eye[0], eye[1], G.FLOOR_Z + eye[2]])
    t = world_of(*[tgt[0], tgt[1], G.FLOOR_Z + tgt[2]])
    if name in K.CAM_VIEWS:
        cam.data.sensor_fit = "VERTICAL"
        cam.data.angle = math.radians(50.0)       # same vertical FOV as /gs_cam in the game (SetCamFov 50)
    else:
        cam.data.sensor_fit = "AUTO"
        cam.data.lens = 22
    cam.location = e
    cam.rotation_euler = (t - e).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = str(OUT / f"{name}{'_night' if NIGHT else ''}.png")
    bpy.ops.render.render(write_still=True)
    results[name] = str(OUT / f"{name}.png")
    print("rendered", name)
print("GS_PREVIEW_DONE", json.dumps(results))
