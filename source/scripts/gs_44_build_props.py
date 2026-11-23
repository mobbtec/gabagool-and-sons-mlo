# LONG PIG v0.2.9 — own interactive props spawned by the client scripts (never placed in the MLO):
#   lp_secret_door        walnut leaf of the credenza's hidden bay (FAMILY BUSINESS); hinge = model origin, leaf along -X,
#                         outer face towards -Y, bottom at z = 0
#   lp_ticket_1/2/3       kitchen order tickets (WORKING RESTAURANT): hang from the top edge (origin), text on -Y
# Run inside Blender (same way as gs_20 / gs_38):  exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_44_build_props.py").read())
# Output: build/props/export_native|export_cwxml/  *.ydr (embedded textures) + lp_props.ytyp; docs/_raw/props_build_result*.json
# Textures: lp8_props (512x256) + lp_wood_walnut_512 from gs_15p_make_v029_prop_textures.py (streaming budget).
import bpy, bmesh, os, sys, math, json, shutil, importlib, traceback, datetime
from pathlib import Path

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
SCRIPTS = ROOT / "source" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import szio
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion, is_provider_available

NATIVE = is_provider_available(AssetFormat.NATIVE)
FMT = AssetFormat.NATIVE if NATIVE else AssetFormat.CWXML
EXT = "" if NATIVE else ".xml"
OUTD = ROOT / "build" / "props" / ("export_native" if NATIVE else "export_cwxml")
RES = ROOT / "build" / "gabagool_sons_mlo"
TEXDIRS = [ROOT / "source" / "textures" / d for d in ("v029", "slice", "v026", "v031", "v027", "v300")]
RAW = ROOT / "docs" / "_raw"
BLEND = ROOT / "source" / "blender" / "props"
for d in (OUTD, RAW, BLEND):
    d.mkdir(parents=True, exist_ok=True)
YTYP = "lp_props"
L8W, L8H = 512.0, 256.0                      # lp8_props.dds (gs_15p): small crop of the sign atlas, not the whole 1024x512
REG8 = {"ticket1": (0, 0, 96, 192), "ticket2": (96, 0, 192, 192), "ticket3": (192, 0, 288, 192),
        "paper": (288, 0, 320, 32), "brass": (320, 0, 352, 32)}

SZ = next(n for n in bpy.context.preferences.addons.keys() if n.split(".")[-1] == "sollumz")


def M(sub):
    return importlib.import_module(f"{SZ}.{sub}")


P = M("sollumz_properties"); SollumType = P.SollumType; ArchetypeType = P.ArchetypeType
dh = M("tools.drawablehelper"); shm = M("ydr.shader_materials"); matops = M("ydr.operators.materials")
R = {"timestamp": datetime.datetime.now().isoformat(timespec="seconds"), "blender": bpy.app.version_string, "format": FMT.name,
     "steps": [], "errors": []}


def step(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    print(("PASS " if ok else "FAIL ") + name, json.dumps(kw, default=str)[:900] if kw else "")
    return ok


def image(name):
    for d in TEXDIRS:
        p = d / f"{name}.dds"
        if p.is_file():
            img = bpy.data.images.load(str(p), check_existing=True)
            img.name = f"{name}.dds"
            return img
    raise FileNotFoundError(name)


def material(name, diffuse, spec_mult, falloff, bump="lp_flat_n", spec="lp_matte_s"):
    mat = shm.create_shader("normal_spec.sps")
    mat.name = name
    for node_name, tex in (("DiffuseSampler", diffuse), ("BumpSampler", bump), ("SpecSampler", spec)):
        node = mat.node_tree.nodes.get(node_name)
        node.image = image(tex)
        node.texture_properties.embedded = True
    for pname, val in (("specularIntensityMult", spec_mult), ("specularFalloffMult", falloff), ("specularFresnel", 0.97), ("bumpiness", 1.0)):
        mat.node_tree.nodes.get(pname).set(0, float(val))
    return mat


def uv8(key, pad=1.5):
    x0, y0, x1, y1 = REG8[key]
    return ((x0 + pad) / L8W, 1.0 - (y1 - pad) / L8H, (x1 - pad) / L8W, 1.0 - (y0 + pad) / L8H)


def quad(vs, uv, mat):
    return {"v": vs, "uv": uv, "mat": mat}


def box(x0, x1, y0, y1, z0, z1, mat, uvb=(0.0, 0.0, 1.0, 1.0), scale=None):
    """Axis box; wood faces get world-scaled UVs (scale = metres per texture) so the grain is continuous."""
    out = []
    u0, v0, u1, v1 = uvb
    def uvq(a0, a1, b0, b1):
        if scale:
            return [(a0 / scale, b0 / scale), (a1 / scale, b0 / scale), (a1 / scale, b1 / scale), (a0 / scale, b1 / scale)]
        return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    out.append(quad([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], uvq(x0, x1, z0, z1), mat))       # -y
    out.append(quad([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], uvq(x0, x1, z0, z1), mat))       # +y
    out.append(quad([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], uvq(y0, y1, z0, z1), mat))       # -x
    out.append(quad([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], uvq(y0, y1, z0, z1), mat))       # +x
    out.append(quad([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], uvq(x0, x1, y0, y1), mat))       # +z
    out.append(quad([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], uvq(x0, x1, y0, y1), mat))       # -z
    return out


def secret_door():
    W, H, T = 0.58, 0.61, 0.018
    f = box(-W, 0.0, -T, 0.0, 0.0, H, 0, scale=0.6)                                     # leaf (walnut)
    f += box(-W + 0.05, -0.05, -T - 0.006, -T, 0.05, H - 0.05, 0, scale=0.6)            # raised panel on the outer face
    kx, kz = -W + 0.045, H - 0.11                                                        # brass knob (simple 8-sided stack)
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        r = 0.012
        p0 = (kx + r * math.cos(a0), -T, kz + r * math.sin(a0)); p1 = (kx + r * math.cos(a1), -T, kz + r * math.sin(a1))
        q0 = (kx + r * math.cos(a0), -T - 0.026, kz + r * math.sin(a0)); q1 = (kx + r * math.cos(a1), -T - 0.026, kz + r * math.sin(a1))
        bu = uv8("brass")
        f.append(quad([p0, p1, q1, q0], [(bu[0], bu[1]), (bu[2], bu[1]), (bu[2], bu[3]), (bu[0], bu[3])], 1))
    bu = uv8("brass")
    cap = [(kx + 0.016 * math.cos(2 * math.pi * k / 8), -T - 0.026, kz + 0.016 * math.sin(2 * math.pi * k / 8)) for k in range(8)]
    for k in range(1, 7):
        f.append({"v": [cap[0], cap[k], cap[k + 1]], "uv": [(bu[0], bu[1]), (bu[2], bu[1]), (bu[2], bu[3])], "mat": 1})
    return f, ["wood", "atlas"]


def ticket(key):
    w, h = 0.075, 0.18
    u0, v0, u1, v1 = uv8(key)
    p0, p1, p2, p3 = (-w / 2, 0.0, -h), (w / 2, 0.0, -h), (w / 2, 0.0, 0.0), (-w / 2, 0.0, 0.0)
    f = [quad([p0, p1, p2, p3], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], 0)]                          # front (faces -y)
    pu = uv8("paper")
    f.append(quad([p1, p0, p3, p2], [(pu[0], pu[1]), (pu[2], pu[1]), (pu[2], pu[3]), (pu[0], pu[3])], 0))   # back
    return f, ["atlas"]


def blind_slat():
    """0.3.1-c: one PVC slat of the vertical blinds (same section as gs_v026_kit._slat), pivot = top centre, hangs to
    z = -1.84; double sided. Turned by client/blinds.lua."""
    W, H = 0.089, 1.84
    cs = [(-W / 2 + W * k / 3, 0.004 * (1 - (2 * k / 3 - 1) ** 2)) for k in range(4)]
    f = []
    for k in range(3):
        (x0, y0), (x1, y1) = cs[k], cs[k + 1]
        ua, ub = 0.01 + 0.23 * k / 3, 0.01 + 0.23 * (k + 1) / 3
        vs = [(x0, y0, -H), (x1, y1, -H), (x1, y1, 0.0), (x0, y0, 0.0)]
        uv = [(ua, 0.0), (ub, 0.0), (ub, 1.0), (ua, 1.0)]
        f.append(quad(vs, uv, 0))
        bk = [(x, y - 0.0008, z) for x, y, z in vs]                 # 0.3.1-d: own vertices -> visible from the street too
        f.append(quad(bk[::-1], uv[::-1], 0))
    return f, ["blind"]


def roller():
    """3.0.1: worn WOODEN venetian blind for one window bay (client/blinds.lua) - owner 2026-11-22: horizontal wooden slats,
    battered, 1990s. 50 mm slats on cloth ladder tapes; a few sag at one end, two are gone, one is snapped and hangs.
    Origin = centre of the bottom rail; the slats run UP from it (2.0 m); the blind slides up behind the wall above the window."""
    import random
    rnd = random.Random(1994)
    W, H, P, SW, TH = 1.335, 2.00, 0.044, 0.050, 0.003
    f = []
    n = int((H - 0.06) / P)
    gone = {9, 27}
    snapped = 17
    sag = {5: (0.0, -0.022), 13: (-0.030, 0.0), 22: (0.0, -0.014), 31: (-0.018, 0.0), 36: (0.0, -0.026)}

    def slat(x0, x1, z0, z1, tilt, row, u0, u1):
        dy, dz = math.cos(tilt) * SW / 2, math.sin(tilt) * SW / 2
        v0, v1 = 1.0 - (row * 32 + 31.0) / 256.0, 1.0 - (row * 32 + 1.0) / 256.0
        a, b, c, d = (x0, -dy, z0 - dz), (x1, -dy, z1 - dz), (x1, dy, z1 + dz), (x0, dy, z0 + dz)
        uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        f.append(quad([a, b, c, d], uv, 0))
        f.append(quad([(p[0], p[1], p[2] - TH) for p in (d, c, b, a)], uv[::-1], 0))
        f.append(quad([(a[0], a[1], a[2] - TH), (b[0], b[1], b[2] - TH), b, a], [(u0, v0), (u1, v0), (u1, v0 + 0.01), (u0, v0 + 0.01)], 0))   # room-side edge
    for k in range(n):
        if k in gone:
            continue
        z = 0.06 + P * k
        tilt = math.radians(30.0 + rnd.uniform(-6.0, 6.0))
        dx = rnd.uniform(-0.006, 0.006)
        u0 = rnd.uniform(0.0, 0.12); row = rnd.randrange(6)
        l, r = sag.get(k, (0.0, 0.0))
        if k == snapped:                                                                      # snapped: the stub stays, the rest hangs
            slat(-W / 2 + dx, -0.12, z, z, tilt, row, u0, u0 + 0.40)
            slat(-0.10, W / 2 - 0.05, z - 0.004, z - 0.150, math.radians(48.0), row, u0 + 0.42, u0 + 0.86)
            continue
        slat(-W / 2 + dx, W / 2 + dx, z + l, z + r, tilt, row, u0, u0 + 0.86)
    tv0, tv1 = 1.0 - 222.0 / 256.0, 1.0 - 194.0 / 256.0
    for x in (-W / 2 + 0.19, W / 2 - 0.19):                                                   # cloth ladder tapes, both sides of the slats
        for y in (-0.024, 0.024):
            vs = [(x - 0.0125, y, 0.03), (x + 0.0125, y, 0.03), (x + 0.0125, y, H), (x - 0.0125, y, H)]
            uv = [(0.02, tv0), (0.98, tv0), (0.98, tv1), (0.02, tv1)]
            uv = [uv[0], uv[3], uv[2], uv[1]]                                                 # tape runs along the texture strip
            f.append(quad(vs, uv, 0)); f.append(quad(vs[::-1], uv[::-1], 0))
    rv = 1.0 - 240.0 / 256.0
    f += box(-W / 2 - 0.004, W / 2 + 0.004, -0.026, 0.026, 0.0, 0.020, 0, uvb=(0.02, rv - 0.04, 0.98, rv + 0.04))   # wooden bottom rail
    x = W / 2 - 0.11                                                                          # pull cord with a wooden tassel
    f += box(x - 0.0015, x + 0.0015, -0.030, -0.027, 0.42, H, 0, uvb=(0.05, tv0, 0.10, tv1))
    f += box(x - 0.008, x + 0.008, -0.036, -0.021, 0.38, 0.42, 0, uvb=(0.02, rv - 0.04, 0.10, rv + 0.04))
    return f, ["slat"]


def sign_board():
    """0.3.1-e: hanging blade-sign board, pivot = top centre (swings / hangs crooked, client/signs.lua)."""
    f = box(-0.45, 0.45, -0.012, 0.012, -0.50, -0.06, 0)
    for x in (-0.36, 0.36):
        f += box(x - 0.006, x + 0.006, -0.006, 0.006, -0.06, 0.0, 1, scale=0.5)        # hangers
    return f, ["sign_hang", "wood"]


def sign_bracket():
    """Wall bracket: plate at y = 0 (wall), bar out along -y."""
    f = box(-0.02, 0.02, -1.05, 0.0, -0.02, 0.02, 0, scale=0.5)
    f += box(-0.06, 0.06, -0.012, 0.0, -0.14, 0.06, 0, scale=0.5)
    f += box(-0.012, 0.012, -0.60, -0.02, -0.03, -0.012, 0, scale=0.5)
    return f, ["wood"]


def aframe():
    """Pavement A-frame board: two leaning panels, 0.60 x 0.95 m, art on both outer faces."""
    f = []
    for sg in (-1.0, 1.0):
        a = [(-0.3 * -sg, 0.28 * sg, 0.0), (0.3 * -sg, 0.28 * sg, 0.0), (0.3 * -sg, 0.02 * sg, 0.95), (-0.3 * -sg, 0.02 * sg, 0.95)]
        uv = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        f.append(quad(a, uv, 0))
        b = [(x, y - 0.012 * sg, z) for x, y, z in a]
        f.append(quad(b[::-1], [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)], 1))
    return f, ["sign_patio", "wood"]


def saloon_leaf():
    """1.9.2: half-height staff door leaf, level with the stub wall (top 1.02), clad in dark boards like the counter front
    (lp6_laminate_red, vertical grain), stainless kick plates and push plates on both faces.
    Origin = hinge axis at floor level, leaf along +X (0.56 m). Swung by client/saloon.lua (no collision)."""
    W, Z0, Z1, T = 0.56, 0.13, 1.02, 0.018
    f = []
    def vb(x0, x1, y0, y1, z0, z1):
        q = box(x0, x1, y0, y1, z0, z1, 0, scale=0.6)
        for face in q:
            face["uv"] = [(b, a) for a, b in face["uv"]]                   # grain vertical (u along z), like the kit
        return q
    f += vb(0.0, 0.055, -T, T, Z0, Z1)                                       # hinge stile
    f += vb(W - 0.055, W, -T, T, Z0, Z1)                                     # lock stile
    f += vb(0.055, W - 0.055, -T, T, Z1 - 0.06, Z1)                          # top rail
    f += vb(0.055, W - 0.055, -T, T, Z0, Z0 + 0.10)                          # bottom rail
    f += vb(0.055, W - 0.055, -0.006, 0.006, Z0 + 0.10, Z1 - 0.06)           # panel core = groove bottoms
    n = 5
    pw = (W - 0.11) / n
    for k in range(n):
        f += vb(0.055 + k * pw + 0.003, 0.055 + (k + 1) * pw - 0.003, -0.013, 0.013, Z0 + 0.10, Z1 - 0.06)
    for ya, yb in ((T, T + 0.002), (-T - 0.002, -T)):
        f += box(0.012, W - 0.012, ya, yb, Z0 + 0.008, Z0 + 0.092, 1, scale=0.8)       # kick plates
    for ya, yb in ((0.013, T + 0.002), (-T - 0.002, -0.013)):
        f += box(W - 0.19, W - 0.07, ya, yb, 0.78, 0.94, 1, scale=0.8)                  # push plates
    return f, ["board", "steel"]


def mesh_from_faces(name, faces, mats, sc):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    for fdef in faces:
        vs = [bm.verts.new(co) for co in fdef["v"]]
        bf = bm.faces.new(vs)
        bf.material_index = fdef["mat"]
        for loop, (u, v) in zip(bf.loops, fdef["uv"]):
            loop[uv].uv = (u, v)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.normal_update(); bm.to_mesh(me); bm.free()
    col = me.color_attributes.new("Color 1", "BYTE_COLOR", "CORNER")
    for li in range(len(me.loops)):
        col.data[li].color_srgb = (0.55, 0.30, 0.0, 1.0)            # interior props: natural ambient 0.55, artificial 0.30
    me.color_attributes.active_color = col
    me.color_attributes.render_color_index = me.color_attributes.active_color_index
    for m in mats:
        me.materials.append(m)
    obj = bpy.data.objects.new(name, me)
    sc.collection.objects.link(obj)
    return obj


def build():
    sc = bpy.data.scenes.new("lp_props") if not bpy.app.background else bpy.context.scene
    if not bpy.app.background and bpy.context.window is not None:
        bpy.context.window.scene = sc
    sc.name = "lp_props"
    mats = {"wood": material("lp_wood_walnut_p", "lp_wood_walnut_512", 0.35, 30.0), "atlas": material("lp8_props_p", "lp8_props", 0.12, 8.0),
            "blind": material("lp5_blind_p", "lp5_blind", 0.25, 12.0),
            "slat": material("lp30_slats_p", "lp30_slats", 0.30, 22.0),
            "sign_hang": material("lp_sign_hang_p", "lp_sign_hang", 0.12, 10.0),
            "sign_patio": material("lp_sign_patio_p", "lp_sign_patio", 0.10, 8.0),
            "board": material("lp_board_p", "lp12_board", 0.35, 30.0, bump="lp12_board_n", spec="lp12_board_s"),       # 1.9.3: same boards as the counter front
            "steel": material("lp_steel_p", "lp_steel", 1.5, 160.0, bump="lp_steel_n", spec="lp_steel_s")}            # same steel as the cases
    models = {"lp_secret_door": secret_door(), "lp_ticket_1": ticket("ticket1"), "lp_ticket_2": ticket("ticket2"),
              "lp_ticket_3": ticket("ticket3"), "lp_blind_slat": blind_slat(), "lp_roller": roller(),
              "lp_sign_board": sign_board(), "lp_sign_bracket": sign_bracket(), "lp_aframe": aframe(),
              "lp_saloon_leaf": saloon_leaf()}
    drawables = {}
    for name, (faces, mnames) in models.items():
        ml = [mats[n] for n in mnames]
        obj = mesh_from_faces(name, faces, ml, sc)
        for m in ml:
            matops.post_create_shader_update_object(obj, m)
        d = dh.convert_obj_to_drawable(obj)
        d.name = name
        drawables[name] = d
    ytyp = sc.ytyps.add(); ytyp.name = YTYP
    sc.ytyp_index = len(sc.ytyps) - 1
    for name, d in drawables.items():
        a = ytyp.new_archetype(ArchetypeType.BASE)
        a.name = name
        a.asset = d
        a.lod_dist = 60.0
        a.flags.total = "0"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND / "lp_props.blend"))
    step("build_scene", True, models=list(drawables))
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


def validate(names):
    v, ok = {}, True
    for n in names:
        d = szio.try_load_asset(OUTD / f"{n}.ydr{EXT}")
        if d is None:
            ok = False; v[n] = "load failed"; continue
        tex = sorted(d.shader_group.embedded_textures) if d.shader_group else []
        v[n] = {"textures": tex, "shaders": [s.name for s in d.shader_group.shaders]}
        need = {"lp_blind_slat": "lp5_blind", "lp_roller": "lp30_slats", "lp_saloon_leaf": "lp12_board", "lp_sign_board": "lp_sign_hang", "lp_sign_bracket": "lp_wood_walnut_512",
                "lp_aframe": "lp_sign_patio"}.get(n, "lp8_props")
        ok = ok and need in tex and "lp8_atlas" not in tex
    yt = szio.try_load_asset(OUTD / f"{YTYP}.ytyp{EXT}")
    arch = sorted(a.name for a in yt.archetypes) if yt else []
    v["ytyp"] = arch
    ok = ok and arch == sorted(names)
    step("validate", ok, **v)


def deploy():
    if not RES.is_dir():
        step("deploy", True, skipped="resource folder not built yet (gs_20 copies build/props on its next run)")
        return
    dst = RES / "stream" / "props"
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
    validate(names)
    deploy()
except Exception:
    R["errors"].append(traceback.format_exc())
    print(traceback.format_exc())
R["go"] = bool(R["steps"]) and all(s["ok"] for s in R["steps"]) and not R["errors"]
out = RAW / ("props_build_result.json" if NATIVE else "props_build_result_cwxml_dryrun.json")
out.write_text(json.dumps(R, indent=1, default=str), encoding="utf-8")
print("GS_PROPS_DONE go=%s format=%s -> %s" % (R["go"], FMT.name, out))
