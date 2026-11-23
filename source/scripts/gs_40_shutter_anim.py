# LONG PIG — offline animation frames of the security shutters (Blender / Cycles preview, NOT the game).
# Builds the same scene as gs_21_preview_render.py (overridden vanilla shell + MLO + props), imports the 8 shutter models
# once per placement and renders the closing motion with the SAME timing / easing as client/shutters.lua:
#   position = ease(t / Duration), Duration 6.5 s, smootherstep; panels above the box bottom are hidden (inside the box).
# Env: GS_ROOT, GS_ANIM_VIEW (default SH_CORNER), GS_ANIM_FRAMES (frames over the motion, default 40),
#      GS_ANIM_OUT (folder under screenshots, default shutter_anim), GS_SAMPLES, GS_W, GS_H, GS_DENOISE.
import os, sys, math, json, time
from pathlib import Path

os.environ["GS_VIEWS"] = "__none__"          # gs_21: set the scene up, render nothing
os.environ.pop("GS_SHUTTERS", None)          # shutters are added here, once
ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
exec(open(ROOT / "source" / "scripts" / "gs_21_preview_render.py", encoding="utf-8").read(), globals())

import importlib
import gs_shutter_geometry as SHG
importlib.reload(SHG)

SDIR = ROOT / "build" / "shutters" / "export_cwxml"
VIEW = os.environ.get("GS_ANIM_VIEW", "SH_CORNER")
NF = int(os.environ.get("GS_ANIM_FRAMES", "40"))
AOUT = ROOT / "screenshots" / os.environ.get("GS_ANIM_OUT", "shutter_anim")
AOUT.mkdir(parents=True, exist_ok=True)

# ---- one object (with children) per placement, imported once
slots = []
for m, (s, t, z), (ix, iy), vis in SHG.placements(0.0):
    before = set(bpy.data.objects)
    bpy.ops.sollumz.import_assets(directory=str(SDIR) + os.sep, files=[{"name": f"{m}.ydr.xml"}])
    new = [o for o in bpy.data.objects if o not in before]
    root = None
    for o in new:
        if "bound" in str(o.sollum_type).lower() or o.name.endswith("_col"):
            o.hide_render = True
        if o.parent is None:
            root = o
    root.parent = inst
    root.location = (s, t, z)
    root.rotation_euler = (0, 0, math.atan2(-ix, iy))
    meshes = [o for o in new if o.type == "MESH" and not o.hide_render]
    slots.append((root, meshes))

eye, tgt = VIEWS[VIEW]
e = world_of(eye[0], eye[1], G.FLOOR_Z + eye[2])
tg = world_of(tgt[0], tgt[1], G.FLOOR_Z + tgt[2])
cam.data.sensor_fit = "AUTO"
cam.data.lens = 22
cam.location = e
cam.rotation_euler = (tg - e).to_track_quat("-Z", "Y").to_euler()

log = []
for i in range(NF):
    u = i / (NF - 1)                         # time fraction of the 6.5 s motion
    p = SHG.ease(u)                          # curtain position, same easing as the client
    for (root, meshes), (m, (s, t, z), _d, vis) in zip(slots, SHG.placements(p)):
        root.location = (s, t, z)
        for o in meshes:
            o.hide_render = not vis
    sc.render.filepath = str(AOUT / f"f{i:03d}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    log.append({"frame": i, "u": round(u, 4), "p": round(p, 4), "sec": round(time.time() - t0, 1)})
    print("GS_ANIM frame", i, "u", round(u, 3), "p", round(p, 3), "sec", log[-1]["sec"], flush=True)
(AOUT / "frames.json").write_text(json.dumps({"view": VIEW, "frames": log, "duration_s": 6.5}, indent=1))
print("GS_ANIM_DONE", AOUT)
