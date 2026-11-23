# Stage A: preliminary blockout of the LONG PIG interior + Cycles views of the key zones.
# NOT game assets: simple boxes and procedural colours to check scale, layout, palette and light mood.
# usage: <bpy python> gs_32_concept_blockout.py <out_dir> [res_x] [samples] [views,comma]
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gs_30_concept_layout as L

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/concept"
RES_X = int(sys.argv[2]) if len(sys.argv) > 2 else 1280
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 48
ONLY = sys.argv[4].split(",") if len(sys.argv) > 4 else None
os.makedirs(OUT, exist_ok=True)
random.seed(7)
FONT_DIR = "/usr/share/fonts/truetype"

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
COL = SC.collection


# ------------------------------------------------------------------ helpers
def lin(hexcol):
    h = hexcol.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


MATS = {}


def mat(name, color="#808080", rough=0.6, metal=0.0, emit=None, es=0.0, coat=0.0, alpha=None):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(color), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(emit), 1)
        b.inputs["Emission Strength"].default_value = es
    MATS[name] = m
    return m


def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    MATS[name] = m
    return m, nt, b, tc


def sock(coll, ident):
    for x in coll:
        if x.identifier == ident:
            return x
    raise KeyError(ident)


def ramp(nt, src, stops, interp="LINEAR"):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.interpolation = interp
    el = r.color_ramp.elements
    while len(el) > len(stops):
        el.remove(el[-1])
    while len(el) < len(stops):
        el.new(0.5)
    for e, (pos, col) in zip(el, stops):
        e.position = pos
        e.color = (*lin(col), 1)
    nt.links.new(src, r.inputs[0])
    return r


def mat_checker(name, c1, c2, size, rough=0.45, worn=True):
    m, nt, b, tc = node_mat(name)
    ck = nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 1.0 / size
    ck.inputs["Color1"].default_value = (*lin(c1), 1)
    ck.inputs["Color2"].default_value = (*lin(c2), 1)
    nt.links.new(tc.outputs["Object"], ck.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.5 if worn else 0.0
    nt.links.new(ck.outputs["Color"], sock(mix.inputs, "A_Color"))
    r = ramp(nt, nz.outputs["Fac"], [(0.35, "#bdb5a8"), (0.65, "#ffffff")])
    nt.links.new(r.outputs["Color"], sock(mix.inputs, "B_Color"))
    nt.links.new(sock(mix.outputs, "Result_Color"), b.inputs["Base Color"])
    rr = ramp(nt, nz.outputs["Fac"], [(0.3, "#9a9a9a"), (0.7, "#6a6a6a")])
    nt.links.new(rr.outputs["Color"], b.inputs["Roughness"])
    return m


def mat_grid(name, col, mortar_col, w, h, mortar, rough=0.5, offset=0.0, coat=0.0, axes="XY"):
    """tiles / drop ceiling via brick texture on object coords (axes picks the plane)."""
    m, nt, b, tc = node_mat(name)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    a0, a1 = {"XY": ("X", "Y"), "XZ": ("X", "Z"), "YZ": ("Y", "Z")}[axes]
    nt.links.new(sep.outputs[a0], comb.inputs["X"])
    nt.links.new(sep.outputs[a1], comb.inputs["Y"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = offset
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = w
    br.inputs["Row Height"].default_value = h
    br.inputs["Mortar Size"].default_value = mortar
    br.inputs["Mortar Smooth"].default_value = 0.2
    br.inputs["Bias"].default_value = 0.0
    c = lin(col)
    br.inputs["Color1"].default_value = (*c, 1)
    br.inputs["Color2"].default_value = (c[0] * 0.95, c[1] * 0.95, c[2] * 0.93, 1)
    br.inputs["Mortar"].default_value = (*lin(mortar_col), 1)
    nt.links.new(comb.outputs[0], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(br.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_wood(name, dark, light, scale=6.0, rough=0.45, coat=0.3, along="X"):
    m, nt, b, tc = node_mat(name)
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = along
    wv.inputs["Scale"].default_value = scale
    wv.inputs["Distortion"].default_value = 7.0
    wv.inputs["Detail"].default_value = 3.0
    wv.inputs["Detail Scale"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    r = ramp(nt, wv.outputs["Fac"], [(0.0, dark), (0.55, light), (1.0, dark)])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.25
    return m


def mat_beadboard(name, dark, light, pitch=0.10):
    m, nt, b, tc = node_mat(name)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(sep.outputs["X"], add.inputs[0])
    nt.links.new(sep.outputs["Y"], add.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 1.0 / pitch
    nt.links.new(add.outputs[0], mul.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "FRACT"
    nt.links.new(mul.outputs[0], fr.inputs[0])
    groove = ramp(nt, fr.outputs[0], [(0.0, "#000000"), (0.06, "#ffffff"), (0.94, "#ffffff"), (1.0, "#000000")])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = 3.0
    wv.inputs["Distortion"].default_value = 9.0
    wv.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    r = ramp(nt, wv.outputs["Fac"], [(0.0, dark), (0.6, light), (1.0, dark)])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.6
    nt.links.new(r.outputs["Color"], sock(mix.inputs, "A_Color"))
    nt.links.new(groove.outputs["Color"], sock(mix.inputs, "B_Color"))
    nt.links.new(sock(mix.outputs, "Result_Color"), b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    nt.links.new(groove.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.4
    b.inputs["Coat Weight"].default_value = 0.4
    return m


def mat_gingham(name, k=12.0):
    m, nt, b, tc = node_mat(name)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    outs = []
    for ax in ("X", "Y"):
        mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = k
        nt.links.new(sep.outputs[ax], mu.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"
        nt.links.new(mu.outputs[0], fr.inputs[0])
        gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.5
        nt.links.new(fr.outputs[0], gt.inputs[0])
        outs.append(gt)
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = "MULTIPLY_ADD"
    nt.links.new(outs[0].outputs[0], ad.inputs[0]); ad.inputs[1].default_value = 0.5
    nt.links.new(outs[1].outputs[0], ad.inputs[2])
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = 0.6667
    nt.links.new(ad.outputs[0], sc.inputs[0])
    r = ramp(nt, sc.outputs[0], [(0.0, "#f1efe8"), (0.3, "#8fb592"), (0.66, "#5e8d63"), (0.99, "#2f5d3a")], "CONSTANT")
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Sheen Weight"].default_value = 0.3
    return m


def mat_photo(name, seed):
    m, nt, b, tc = node_mat(name)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 7.0 + seed
    nz.inputs["Detail"].default_value = 2.0
    nz.noise_dimensions = "4D"
    nz.inputs[1].default_value = seed * 3.1  # W
    nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
    r = ramp(nt, nz.outputs["Fac"], [(0.3, "#1c1a17"), (0.55, "#8d877c"), (0.75, "#dcd6c8")])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.15
    return m


def mat_glass(name, tint="#ffffff", refl=0.08):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*lin(tint), 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.02
    mx = nt.nodes.new("ShaderNodeMixShader")
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    mp = nt.nodes.new("ShaderNodeMath"); mp.operation = "MULTIPLY_ADD"
    nt.links.new(fr.outputs[0], mp.inputs[0]); mp.inputs[1].default_value = 0.6; mp.inputs[2].default_value = refl
    nt.links.new(mp.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    MATS[name] = m
    return m


def mat_emit(name, col, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*lin(col), 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    MATS[name] = m
    return m


def obj_from_bm(name, bm, m, parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    if m is not None:
        o.data.materials.append(m)
    COL.objects.link(o)
    return o


def box(name, x0, x1, y0, y1, z0, z1, m, rot=None, pivot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    if rot:
        px, py = pivot
        bmesh.ops.rotate(bm, cent=(px, py, 0), matrix=Matrix.Rotation(math.radians(rot), 3, "Z"), verts=bm.verts)
    return obj_from_bm(name, bm, m)


def cbox(name, cx, cy, cz, sx, sy, sz, m, rot=0.0, pivot=None):
    return box(name, cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2, m, rot or None, pivot or (cx, cy))


def cyl(name, cx, cy, z0, r, h, m, seg=20, r2=None, axis="Z", rot=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    if axis == "X":
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"), verts=bm.verts)
    elif axis == "Y":
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)
    if rot:
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(rot), 3, "Z"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(cx, cy, z0 + (h / 2 if axis == "Z" else 0)), verts=bm.verts)
    o = obj_from_bm(name, bm, m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def sphere(name, cx, cy, cz, r, m, scale=(1, 1, 1), seg=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts)
    o = obj_from_bm(name, bm, m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def poly_slab(name, poly, z0, z1, m):
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z1)) for x, y in poly]  # solidify extrudes against the (+Z) normal
    f = bm.faces.new(vs)
    bm.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
        bm.normal_update()
    bmesh.ops.solidify(bm, geom=[f], thickness=z1 - z0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, m)


FONTS = {}


def font(fname):
    if fname not in FONTS:
        for root, _, files in os.walk(FONT_DIR):
            if fname in files:
                FONTS[fname] = bpy.data.fonts.load(os.path.join(root, fname))
                break
    return FONTS[fname]


def text(name, body, loc, rot_deg_z, size, m, fname="DejaVuSerif-Bold.ttf", align="CENTER", extrude=0.003, facing="-X", spacing=1.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = font(fname)
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.space_character = spacing
    o = bpy.data.objects.new(name, cu)
    o.data.materials.append(m)
    COL.objects.link(o)
    # text is in XY plane facing +Z; stand it up, then turn to face the requested direction
    face = {"-X": -90, "+X": 90, "-Y": 0, "+Y": 180}[facing]
    o.rotation_euler = (math.radians(90), 0, math.radians(face + rot_deg_z))
    o.location = loc
    return o


# ------------------------------------------------------------------ materials
M = dict(
    plaster=mat("plaster_cream", "#E2D6BC", 0.85),
    plaster_back=mat("plaster_back", "#d8ccb2", 0.85),
    trim=mat_wood("walnut_trim", "#2a1a10", "#4a2e1c", 9.0, 0.4, 0.5, "Z"),
    beadboard=mat_beadboard("walnut_beadboard", "#3a2418", "#6a4428"),
    panel=mat_beadboard("dark_panel", "#2e1c12", "#4e3220", 0.30),
    floor_front=mat_checker("vct_front", "#d6c9ab", "#5a2c27", 0.305),
    floor_grey=mat_checker("vct_grey", "#c9c4b8", "#a9a49a", 0.305),
    floor_quarry=mat_grid("quarry_tile", "#8a3b26", "#5a4a40", 0.152, 0.152, 0.006, 0.6),
    floor_office=mat_checker("vct_office", "#bdb6a6", "#8a8578", 0.305),
    floor_wood=mat_wood("plank_floor", "#3a2416", "#6a4426", 2.0, 0.55, 0.2, "Y"),
    ceiling=mat_grid("drop_ceiling", "#DDD3BC", "#c7c2b5", 0.61, 0.61, 0.010, 0.9),
    ceiling_k=mat_grid("ceiling_kitchen", "#e9e7e0", "#bfc3c3", 0.61, 1.22, 0.010, 0.6),
    subway=mat_grid("subway_s", "#EDEBE4", "#b9b4aa", 0.152, 0.076, 0.004, 0.18, 0.5, 0.6, "YZ"),
    subway_x=mat_grid("subway_x", "#EDEBE4", "#b9b4aa", 0.152, 0.076, 0.004, 0.18, 0.5, 0.6, "XZ"),
    leather=mat("oxblood_leather", "#5E1A1D", 0.42, coat=0.25),
    leather_edge=mat("oxblood_piping", "#3e1012", 0.4),
    formica=mat("formica_cream", "#d8ceb6", 0.3, coat=0.5),
    chrome=mat("chrome", "#d8d8d8", 0.12, 1.0),
    brass=mat("aged_brass", "#A8834A", 0.32, 1.0),
    steel=mat("stainless", "#B9BCBC", 0.3, 1.0),
    enamel_w=mat("white_enamel", "#ecebe6", 0.3, coat=0.4),
    enamel_g=mat("green_enamel", "#2F5D3A", 0.35, coat=0.5),
    red=mat("italian_red", "#A3262A", 0.5),
    green=mat("italian_green", "#2F5D3A", 0.5),
    white=mat("paint_white", "#ece8de", 0.6),
    black=mat("menu_black", "#1b1917", 0.7),
    letters=mat("letters_cream", "#efe4c8", 0.5),
    gold=mat("gold_leaf", "#c9a24f", 0.28, 1.0),
    chair_wood=mat_wood("bentwood", "#2b1a10", "#53351f", 14.0, 0.4, 0.4, "Z"),
    gingham=mat_gingham("gingham"),
    meat=mat("cured_meat", "#7a2a22", 0.5),
    meat2=mat("ham_pink", "#b8645c", 0.45),
    cheese=mat("provolone", "#d9b25a", 0.55),
    bread=mat("bread", "#b07a3c", 0.8),
    cardboard=mat("cardboard", "#a07d52", 0.9),
    grey=mat("grey_metal", "#6e7477", 0.5, 0.6),
    dark=mat("dark_plastic", "#222222", 0.5),
    glass=mat_glass("glass_clear"),
    case_glass=mat_glass("case_glass", "#f4fbfb", 0.1),
    asphalt=mat("asphalt", "#3a3a3a", 0.9),
    sidewalk=mat("sidewalk", "#9c978c", 0.85),
    facade=mat("facade_brick", "#7b4b3a", 0.9),
    bronze=mat("storefront_bronze", "#3b2f25", 0.4, 0.8),
    blinds=mat("blinds_wood", "#8A5A2E", 0.5),
    tv=mat("crt_screen", "#20262a", 0.15, coat=1.0),
    paper=mat("paper", "#f2efe6", 0.9),
)
PRODUCT_COLS = ["#8e2e26", "#3a5a3c", "#d8cca0", "#b08a3e", "#2c3f5e", "#6a2a2e", "#c9b67e", "#4a6a48", "#e6e2d6", "#8a4a2a"]
PM = [mat(f"product_{i}", c, 0.5) for i, c in enumerate(PRODUCT_COLS)]


# ------------------------------------------------------------------ shell (existing vanilla walls + openings)
H_SHELL = 3.40
WALL = 0.30
OPEN_Z = {"W1": (0.602, 2.576), "W2": (0.602, 2.576), "D1": (0.0, 2.48), "D2": (0.179, 2.628), "D3": (0.239, 2.628)}


def build_shell():
    poly = L.FLOOR_POLY
    n = len(poly)
    walls = []
    for i in range(n):
        p0, p1 = Vector((*poly[i], 0)), Vector((*poly[(i + 1) % n], 0))
        d = (p1 - p0).normalized()
        outn = Vector((d.y, -d.x, 0))  # polygon is CCW -> right normal points out
        a, b = p0 - d * WALL, p1 + d * WALL
        q = [a, b, b + outn * WALL, a + outn * WALL]
        bm = bmesh.new()
        vs = [bm.verts.new((v.x, v.y, H_SHELL)) for v in q]
        f = bm.faces.new(vs)
        bm.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
            bm.normal_update()
        bmesh.ops.solidify(bm, geom=[f], thickness=H_SHELL)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        walls.append(obj_from_bm(f"shell_wall_{i}", bm, M["plaster"]))
    # openings
    cutters = []
    for key, o in L.OPENINGS.items():
        (x0, y0), (x1, y1) = o["p0"], o["p1"]
        z0, z1 = OPEN_Z[key]
        p0, p1 = Vector((x0, y0, 0)), Vector((x1, y1, 0))
        d = (p1 - p0).normalized()
        c = (p0 + p1) / 2
        nrm = Vector((-d.y, d.x, 0))
        if not L.inside(tuple(c + nrm * 0.1)[:2]):
            nrm = -nrm  # nrm = inward normal
        ln = (p1 - p0).length
        cu = cbox(f"cut_{key}", c.x, c.y, (z0 + z1) / 2, ln, 1.4, z1 - z0, None, math.degrees(math.atan2(d.y, d.x)))
        cu.hide_render = True
        cutters.append((key, cu, c, d, nrm, ln, z0, z1))
    for w in walls:
        for key, cu, *_ in cutters:
            mod = w.modifiers.new(f"cut_{key}", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.solver = "EXACT"
            mod.object = cu
    # glazing + bronze storefront frames
    for key, cu, c, d, nrm, ln, z0, z1 in cutters:
        ang = math.degrees(math.atan2(d.y, d.x))
        if key in ("W1", "W2"):
            gp = c - nrm * 0.20
            cbox(f"glass_{key}", gp.x, gp.y, (z0 + z1) / 2, ln, 0.012, z1 - z0, M["glass"], ang)
            for k in range(4 if key == "W1" else 3):
                u = -ln / 2 + k * ln / (3 if key == "W1" else 2)
                p = gp + d * u
                cbox(f"mullion_{key}_{k}", p.x, p.y, (z0 + z1) / 2, 0.06, 0.10, z1 - z0, M["bronze"], ang)
            for zz in (z0 + 0.03, z1 - 0.03):
                cbox(f"rail_{key}_{zz:.2f}", gp.x, gp.y, zz, ln, 0.10, 0.06, M["bronze"], ang)
        elif key == "D1":
            gp = c - nrm * 0.15
            for side in (-1, 1):
                p = gp + d * side * ln / 4
                cbox(f"d1_glass_{side}", p.x, p.y, 1.24, ln / 2 - 0.12, 0.012, 2.3, M["glass"], ang)
                for u in (-ln / 4 + 0.03, ln / 4 - 0.03):
                    q = p + d * u
                    cbox(f"d1_stile_{side}_{u:.2f}", q.x, q.y, 1.24, 0.06, 0.05, 2.46, M["bronze"], ang)
                cbox(f"d1_bar_{side}", p.x, p.y, 1.05, ln / 2 - 0.1, 0.06, 0.04, M["chrome"], ang)
        else:
            gp = c - nrm * 0.16
            cbox(f"steel_door_{key}", gp.x, gp.y, (z0 + z1) / 2, ln - 0.02, 0.045, z1 - z0, M["grey"], ang)
            step = c + nrm * 0.2
            cbox(f"step_{key}", step.x, step.y, z0 / 2, ln + 0.1, 0.4, z0, M["floor_grey"], ang)
    # roof + exterior
    poly_slab("roof", [(x, y) for x, y in L.FLOOR_POLY], H_SHELL, H_SHELL + 0.25, M["plaster"])
    box("street", -40, 40, -40, -5.2, -0.30, -0.25, M["asphalt"])
    box("sidewalk_sw", -40, 40, -5.2, 30, -0.22, -0.02, M["sidewalk"])
    for i, (x, w, h) in enumerate([(-14, 9, 7), (-3, 8, 5), (7, 10, 9), (19, 9, 6)]):
        box(f"opposite_{i}", x, x + w, -26, -16, -0.25, h, M["facade"])
    for i, (y, w, h) in enumerate([(-6, 9, 6), (5, 8, 8), (15, 10, 5)]):
        box(f"side_{i}", -28, -18, y, y + w, -0.25, h, M["facade"])


# ------------------------------------------------------------------ zones: floors, ceilings, partitions, wall finishes
FLOOR_M = {"gs_front": "floor_front", "gs_counter": "floor_front", "gs_corridor": "floor_grey", "gs_staff_entry": "floor_grey",
           "gs_backroom": "floor_wood", "gs_office": "floor_office", "gs_wc": "floor_grey", "gs_kitchen": "floor_quarry",
           "gs_storage": "floor_grey", "gs_cooler": "floor_quarry"}


def build_rooms():
    for name, code, poly, _ in L.ZONES:
        ext = [(x, y) for x, y in poly]
        poly_slab(f"floor_{code}", ext, -0.05, 0.0, M[FLOOR_M[code]])
        h = L.CEILING[code]
        poly_slab(f"ceil_{code}", ext, h, h + 0.03, M["ceiling_k" if code in ("gs_kitchen", "gs_cooler", "gs_wc") else "ceiling"])
    poly_slab("floor_gaps", [(x, y) for x, y in L.FLOOR_POLY], -0.08, -0.03, M["floor_grey"])
    # partitions
    for name, p0, p1, gaps in L.PARTITIONS:
        p0, p1 = Vector((*p0, 0)), Vector((*p1, 0))
        ln = (p1 - p0).length
        d = (p1 - p0).normalized()
        ang = math.degrees(math.atan2(d.y, d.x))
        cuts = [0.0]
        for g0, g1, kind in sorted(gaps):
            cuts += [g0, g1]
        cuts.append(ln)
        for a, b in zip(cuts[0::2], cuts[1::2]):
            if b - a > 1e-3:
                c = p0 + d * (a + b) / 2
                cbox(f"part_{name}_{a:.2f}", c.x, c.y, H_SHELL / 2, b - a, L.WALL_T, H_SHELL, M["plaster_back"], ang)
        for g0, g1, kind in gaps:
            c = p0 + d * (g0 + g1) / 2
            if kind == "door":
                cbox(f"head_{name}_{g0:.2f}", c.x, c.y, (2.10 + H_SHELL) / 2, g1 - g0, L.WALL_T, H_SHELL - 2.10, M["plaster_back"], ang)
                for u in (g0, g1):
                    q = p0 + d * u
                    cbox(f"jamb_{name}_{u:.2f}", q.x, q.y, 1.05, 0.05, L.WALL_T + 0.04, 2.10, M["trim"], ang)
            else:  # pass-through window: wall below and above
                cbox(f"pass_lo_{name}", c.x, c.y, 0.525, g1 - g0, L.WALL_T, 1.05, M["plaster_back"], ang)
                cbox(f"pass_hi_{name}", c.x, c.y, (1.62 + H_SHELL) / 2, g1 - g0, L.WALL_T, H_SHELL - 1.62, M["plaster_back"], ang)
                cbox(f"pass_sill_{name}", c.x, c.y, 1.06, g1 - g0 + 0.1, L.WALL_T + 0.16, 0.03, M["steel"], ang)


def wainscot(x0, y0, x1, y1, inward, h=1.05, m="beadboard", name="wains"):
    p0, p1 = Vector((x0, y0, 0)), Vector((x1, y1, 0))
    d = (p1 - p0).normalized()
    ln = (p1 - p0).length
    nv = Vector((inward[0], inward[1], 0))
    c = (p0 + p1) / 2 + nv * 0.012
    ang = math.degrees(math.atan2(d.y, d.x))
    cbox(f"{name}_{x0:.1f}_{y0:.1f}", c.x, c.y, h / 2, ln, 0.024, h, M[m], ang)
    cr = (p0 + p1) / 2 + nv * 0.03
    cbox(f"{name}_rail_{x0:.1f}_{y0:.1f}", cr.x, cr.y, h + 0.03, ln, 0.06, 0.06, M["trim"], ang)
    cb = (p0 + p1) / 2 + nv * 0.02
    cbox(f"{name}_base_{x0:.1f}_{y0:.1f}", cb.x, cb.y, 0.06, ln, 0.04, 0.12, M["trim"], ang)


def build_finishes():
    # front of house: walnut beadboard wainscot + chair rail, cream plaster above
    wainscot(-2.84, 6.94, 7.0, 6.94, (0, -1))
    wainscot(5.70, -1.23, 7.0, -1.23, (0, 1))
    wainscot(-2.90, 2.55, -2.90, 3.40, (1, 0))
    wainscot(-2.90, 6.45, -2.90, 6.94, (1, 0))
    # back wall behind counter (P1, west face): subway tile backsplash, sign band
    box("backsplash_a", 9.925, 9.94, 0.05, 2.50, 0.0, 1.70, M["subway"])
    box("backsplash_b", 9.925, 9.94, 3.70, 6.94, 0.0, 1.70, M["subway"])
    # kitchen: subway tile to 2.0 on all walls
    box("k_tile_s", 10.12, 16.15, -1.23, -1.21, 0.0, 2.0, M["subway_x"])
    box("k_tile_e", 16.13, 16.15, -1.23, 5.0, 0.0, 2.0, M["subway"])
    box("k_tile_w", 10.06, 10.08, -1.23, 4.94, 0.0, 2.0, M["subway"])
    box("k_tile_n", 10.12, 16.15, 4.92, 4.94, 0.0, 2.0, M["subway_x"])
    # back room: dark wood panelling to 2.1 + picture rail
    for (x0, y0, x1, y1, inw) in [(0.72, 11.42, 5.6, 11.42, (0, -1)), (0.72, 8.24, 5.6, 8.24, (0, 1)), (0.72, 8.24, 0.72, 11.42, (1, 0)), (5.54, 8.24, 5.54, 11.42, (-1, 0))]:
        wainscot(x0, y0, x1, y1, inw, h=2.1, m="panel", name="panel")
    # framed photos: hall (P2 face) and back room
    for i, (s, z, w, h) in enumerate([(-1.9, 1.75, 0.5, 0.4), (-1.2, 1.85, 0.4, 0.55), (-0.5, 1.7, 0.6, 0.45), (5.2, 1.8, 0.5, 0.4), (5.9, 1.75, 0.4, 0.5)]):
        cbox(f"frame_h{i}", s, 6.925, z, w + 0.06, 0.03, h + 0.06, M["trim"])
        cbox(f"photo_h{i}", s, 6.903, z, w, 0.006, h, mat_photo(f"photo_h{i}", i))
    for i, (s, z, w, h) in enumerate([(1.6, 1.62, 0.4, 0.3), (2.2, 1.7, 0.45, 0.35), (2.9, 1.6, 0.3, 0.4), (3.6, 1.68, 0.5, 0.35), (4.3, 1.62, 0.35, 0.45)]):
        cbox(f"frame_b{i}", s, 11.38, z, w + 0.05, 0.025, h + 0.05, M["black"])
        cbox(f"photo_b{i}", s, 11.366, z, w, 0.005, h, mat_photo(f"photo_b{i}", i + 10))
    # wall clock in hall
    cyl("clock", 3.0, 6.92, 2.45, 0.17, 0.04, M["white"], 32, axis="Y")
    cyl("clock_rim", 3.0, 6.935, 2.45, 0.19, 0.03, M["chrome"], 32, axis="Y")
    # hall sign on P2: dark green board, gold letters (original brand)
    cbox("hall_sign", 2.1, 6.925, 2.62, 3.2, 0.04, 0.5, M["enamel_g"])
    text("hall_sign_txt", "LONG PIG", (2.1, 6.90, 2.68), 0, 0.27, M["gold"], facing="-Y")
    text("hall_sign_sub", "SALUMERIA  ·  ITALIAN DELI  ·  EST. 1974", (2.1, 6.90, 2.47), 0, 0.085, M["letters"], "DejaVuSansCondensed-Bold.ttf", facing="-Y")


# ------------------------------------------------------------------ furniture
def products_on_shelf(prefix, x0, x1, y0, y1, z, hmax, dense=0.09):
    x = x0
    i = 0
    while x < x1 - dense:
        w = random.uniform(0.06, 0.11)
        h = random.uniform(0.12, hmax)
        m = random.choice(PM)
        if random.random() < 0.5:
            cyl(f"{prefix}_c{i}", x + w / 2, (y0 + y1) / 2, z, w / 2, h, m, 10)
        else:
            box(f"{prefix}_b{i}", x, x + w * 0.9, y0 + 0.02, y1 - 0.02, z, z + h, m)
        x += w + 0.01
        i += 1


def products_on_shelf_y(prefix, x0, x1, y0, y1, z, hmax, dense=0.09):
    y = y0
    i = 0
    while y < y1 - dense:
        w = random.uniform(0.06, 0.11)
        h = random.uniform(0.12, hmax)
        m = random.choice(PM)
        if random.random() < 0.5:
            cyl(f"{prefix}_c{i}", (x0 + x1) / 2, y + w / 2, z, w / 2, h, m, 10)
        else:
            box(f"{prefix}_b{i}", x0 + 0.02, x1 - 0.02, y, y + w * 0.9, z, z + h, m)
        y += w + 0.01
        i += 1


def booth_bench(i, s, t, w, d, h, table_s):
    back_side = -1 if table_s > s else 1
    x0, x1 = s - w / 2, s + w / 2
    y0, y1 = t - d / 2, t + d / 2 - 0.05
    box(f"bench_base_{i}", x0, x1, y0, y1, 0.0, 0.40, M["trim"])
    box(f"bench_seat_{i}", x0 + 0.02, x1 - 0.02, y0 + 0.02, y1 - 0.02, 0.40, 0.48, M["leather"])
    bx = s + back_side * (w / 2 - 0.08)
    box(f"bench_back_{i}", bx - 0.08, bx + 0.08, y0, y1, 0.40, h, M["leather"])
    box(f"bench_cap_{i}", bx - 0.10, bx + 0.10, y0 - 0.01, y1 + 0.01, h, h + 0.04, M["trim"])
    for k in range(4):  # channel tufting lines
        yy = y0 + 0.12 + k * (y1 - y0 - 0.24) / 3
        box(f"bench_ch_{i}_{k}", bx - 0.085, bx + 0.085, yy - 0.006, yy + 0.006, 0.52, h - 0.05, M["leather_edge"])


def build_furniture():
    tables_s = [b[0] for k, b, n in L.FURNITURE if k == "booth_table"]
    for i, (kind, b, note) in enumerate(L.FURNITURE):
        s, t, w, d, h, rot = b[:6]
        z0 = b[6] if len(b) > 6 else 0.0
        nm = f"{kind}_{i}"
        if kind == "booth_bench":
            ts = min(tables_s, key=lambda x: abs(x - s))
            booth_bench(i, s, t, w, d, h, ts)
        elif kind == "booth_table":
            box(nm + "_top", s - w / 2, s + w / 2, t - d / 2, t + d / 2 - 0.05, h - 0.03, h, M["formica"])
            box(nm + "_edge", s - w / 2 - 0.005, s + w / 2 + 0.005, t - d / 2, t + d / 2 - 0.045, h - 0.035, h - 0.005, M["chrome"])
            cyl(nm + "_post", s, t + 0.1, 0.0, 0.04, h - 0.03, M["chrome"])
            cyl(nm + "_foot", s, t + 0.1, 0.0, 0.25, 0.03, M["chrome"], 24)
            for k, (dx, dy) in enumerate([(-0.2, -0.3), (0.18, 0.25)]):
                cyl(nm + f"_napkin{k}", s + dx, t + dy, h, 0.05, 0.12, M["chrome"], 12)
        elif kind == "cafe_table":
            cyl(nm + "_top", s, t, h - 0.03, w / 2, 0.03, M["formica"], 28)
            cyl(nm + "_rim", s, t, h - 0.035, w / 2 + 0.006, 0.025, M["chrome"], 28)
            cyl(nm + "_post", s, t, 0, 0.035, h - 0.03, M["chrome"])
            cyl(nm + "_foot", s, t, 0, 0.22, 0.03, M["chrome"], 24)
        elif kind == "chair":
            a = math.radians(rot)
            cyl(nm + "_seat", s, t, 0.43, 0.21, 0.04, M["chair_wood"], 20)
            for k in range(4):
                aa = math.pi / 4 + k * math.pi / 2
                cyl(nm + f"_leg{k}", s + 0.15 * math.cos(aa), t + 0.15 * math.sin(aa), 0, 0.015, 0.43, M["chair_wood"], 8)
            bx, by = s + math.cos(a) * 0.19, t + math.sin(a) * 0.19
            cbox(nm + "_back", bx, by, 0.70, 0.03, 0.36, 0.40, M["chair_wood"], rot)
        elif kind == "coffee_stool":
            cyl(nm + "_seat", s, t, h - 0.08, 0.19, 0.08, M["leather"], 20)
            cyl(nm + "_post", s, t, 0, 0.03, h - 0.08, M["chrome"])
            cyl(nm + "_foot", s, t, 0, 0.18, 0.03, M["chrome"], 20)
        elif kind == "column":
            box(nm, s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, h, M["white"])
            for k, (mm, z) in enumerate([("green", 2.55), ("white", 2.70), ("red", 2.85)]):
                box(nm + f"_band{k}", s - w / 2 - 0.006, s + w / 2 + 0.006, t - d / 2 - 0.006, t + d / 2 + 0.006, z, z + 0.15, M[mm])
            box(nm + "_base", s - w / 2 - 0.02, s + w / 2 + 0.02, t - d / 2 - 0.02, t + d / 2 + 0.02, 0, 0.12, M["trim"])
        elif kind == "gondola":
            box(nm + "_core", s - w / 2, s + w / 2, t - 0.03, t + 0.03, 0, h, M["steel"])
            for z in (0.1, 0.5, 0.9, 1.3):
                for side in (-1, 1):
                    y0, y1 = (t - d / 2, t - 0.03) if side < 0 else (t + 0.03, t + d / 2)
                    box(nm + f"_sh{z}_{side}", s - w / 2, s + w / 2, y0, y1, z - 0.02, z, M["steel"])
                    if z < 1.3:
                        products_on_shelf(nm + f"_p{z}_{side}", s - w / 2 + 0.03, s + w / 2 - 0.03, y0, y1, z, 0.30)
        elif kind == "shelf_wall":
            box(nm + "_frame", s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, 0.08, M["grey"])
            for x in (s - w / 2, s + w / 2 - 0.04):
                box(nm + f"_up{x:.2f}", x, x + 0.04, t - d / 2, t + d / 2, 0, h, M["grey"])
            for z in [0.08 + k * (h - 0.1) / 4 for k in range(5)]:
                box(nm + f"_sh{z:.2f}", s - w / 2, s + w / 2, t - d / 2, t + d / 2, z, z + 0.02, M["grey"])
                if z < h - 0.3:
                    if w >= d:
                        products_on_shelf(nm + f"_p{z:.2f}", s - w / 2 + 0.05, s + w / 2 - 0.05, t - d / 2, t + d / 2, z + 0.02, 0.32)
                    else:
                        products_on_shelf_y(nm + f"_p{z:.2f}", s - w / 2, s + w / 2, t - d / 2 + 0.05, t + d / 2 - 0.05, z + 0.02, 0.32)
        elif kind in ("deli_case", "pastry_case"):
            x0, x1, y0, y1 = s - w / 2, s + w / 2, t - d / 2, t + d / 2
            box(nm + "_base", x0, x1, y0, y1, 0.0, 0.85, M["enamel_w"])
            box(nm + "_kick", x0 - 0.005, x0 + 0.05, y0, y1, 0.0, 0.14, M["steel"])
            box(nm + "_band", x0 - 0.006, x0 + 0.02, y0, y1, 0.70, 0.80, M["red"] if kind == "deli_case" else M["green"])
            box(nm + "_deck", x0 + 0.05, x1, y0 + 0.02, y1 - 0.02, 0.85, 0.88, M["steel"])
            box(nm + "_top", x0 + 0.70, x1, y0, y1, h - 0.03, h, M["steel"])
            # curved front glass approximated by 4 facets
            for k in range(4):
                a0 = math.radians(90 - k * 22.5)
                a1 = math.radians(90 - (k + 1) * 22.5)
                r = 0.42
                cx, cz = x0 + 0.70, 0.88
                p0 = (cx - r * math.cos(a0), cz + r * math.sin(a0) * (h - 0.88) / r)
                p1 = (cx - r * math.cos(a1), cz + r * math.sin(a1) * (h - 0.88) / r)
                mx, mz = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
                ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                o = cbox(nm + f"_glass{k}", mx, t, mz, ln, d - 0.04, 0.008, M["case_glass"])
                o.rotation_euler = (0, -math.atan2(p1[1] - p0[1], p1[0] - p0[0]), 0)
                o.location = (0, 0, 0)
                o.data.transform(Matrix.Translation((-mx, -t, -mz)))
                o.location = (mx, t, mz)
            for yy in (y0 + 0.01, y1 - 0.01):
                box(nm + f"_end{yy:.2f}", x0 + 0.28, x1, yy - 0.01, yy + 0.01, 0.85, h, M["case_glass"])
            # goods
            for k in range(int((d - 0.1) / 0.24)):
                yy = y0 + 0.08 + k * 0.24
                if kind == "deli_case":
                    mm = [M["meat"], M["meat2"], M["cheese"], M["meat2"], M["meat"], M["cheese"], M["meat2"], M["meat"]][k % 8]
                    o = cyl(nm + f"_log{k}", x0 + 0.42, yy + 0.1, 0.96, 0.06, 0.38, mm, 14, axis="X")
                    box(nm + f"_tray{k}", x0 + 0.15, x0 + 0.33, yy, yy + 0.2, 0.88, 0.92, mm)
                else:
                    for j in range(3):
                        sphere(nm + f"_pastry{k}_{j}", x0 + 0.18 + j * 0.11, yy + 0.1, 0.93, 0.045, M["bread"], (1.2, 0.8, 0.6), 10)
            sphere(nm + "_light", x0 + 0.65, t, h - 0.05, 0.02, mat_emit("case_led", "#fff4e0", 6.0), (1, (d - 0.1) / 0.04, 1), 8)
        elif kind in ("counter", "gate"):
            box(nm + "_body", s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, h - 0.04, M["beadboard"])
            box(nm + "_top", s - w / 2 - 0.03, s + w / 2, t - d / 2, t + d / 2, h - 0.04, h, M["formica"])
            box(nm + "_kick", s - w / 2 - 0.005, s + w / 2, t - d / 2, t + d / 2, 0, 0.1, M["trim"])
            if kind == "counter":
                cbox(nm + "_register", s - 0.05, t, h + 0.13, 0.35, 0.40, 0.26, M["dark"])
                cbox(nm + "_reg_disp", s + 0.08, t, h + 0.32, 0.06, 0.24, 0.10, M["dark"])
                cyl(nm + "_paper", s + 0.25, t + 0.15, h, 0.08, 0.32, M["paper"], 16, axis="Y")
        elif kind == "back_counter":
            box(nm + "_body", s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, h - 0.03, M["steel"])
            box(nm + "_top", s - w / 2, s + w / 2, t - d / 2, t + d / 2, h - 0.03, h, M["steel"])
            for k, yy in enumerate([t - 2.4, t - 1.2]):  # slicers
                cbox(nm + f"_slicer_base{k}", s, yy, h + 0.12, 0.45, 0.40, 0.24, M["enamel_w"])
                cyl(nm + f"_slicer_blade{k}", s - 0.05, yy - 0.04, h + 0.28, 0.15, 0.03, M["steel"], 28, axis="X", rot=90)
            cbox(nm + "_scale", s, t - 0.2, h + 0.06, 0.35, 0.35, 0.12, M["enamel_w"])
            cbox(nm + "_espresso", s + 0.02, t + 2.4, h + 0.25, 0.45, 0.75, 0.50, M["chrome"])
            cbox(nm + "_espresso_top", s + 0.02, t + 2.4, h + 0.52, 0.40, 0.70, 0.04, M["brass"])
            for k in range(6):
                sphere(nm + f"_loaf{k}", s, t + 0.4 + k * 0.17, h + 0.08, 0.07, M["bread"], (1.0, 2.6, 0.8) if k % 2 else (1.2, 1.6, 0.9), 10)
            for k in range(5):
                cyl(nm + f"_cup{k}", s + 0.12, t + 2.0 + k * 0.08, h + 0.5 + 0.06, 0.03, 0.06, M["white"], 10)
        elif kind == "menu_board":
            boards = [
                ("HOT HEROES", ["Sausage & Peppers   6.95", "Meatball Parm   6.50", "Chicken Cutlet   6.75", "Eggplant Parm   6.25", "Veal Parm   7.95"]),
                ("COLD CUTS  /lb", ["Capicola   7.99", "Prosciutto   14.99", "Genoa Salami   6.99", "Mortadella   5.49", "Soppressata   8.99"]),
                ("FROM THE COUNTER", ["Fresh Mozzarella daily", "Homemade Sausage", "Party Heroes 3-6 ft", "Espresso  ·  Cannoli", "Catering for all occasions"]),
            ]
            bw = d / 3
            for k, (title, lines) in enumerate(boards):
                yc = t - d / 2 + bw * (k + 0.5)
                box(nm + f"_frame{k}", s - 0.03, s + 0.02, yc - bw / 2 + 0.03, yc + bw / 2 - 0.03, z0, z0 + 0.85, M["trim"])
                box(nm + f"_board{k}", s - 0.035, s + 0.0, yc - bw / 2 + 0.07, yc + bw / 2 - 0.07, z0 + 0.04, z0 + 0.81, M["black"])
                text(nm + f"_t{k}", title, (s - 0.045, yc, z0 + 0.72), 0, 0.085, M["gold"], "DejaVuSerifCondensed-Bold.ttf", facing="-X")
                for j, ln in enumerate(lines):
                    text(nm + f"_l{k}_{j}", ln, (s - 0.045, yc, z0 + 0.59 - j * 0.115), 0, 0.058, M["letters"], "DejaVuSansCondensed-Bold.ttf", facing="-X")
            # sign band above the boards (original brand)
            box(nm + "_signband", s - 0.03, s + 0.02, t - d / 2 + 0.03, t + d / 2 - 0.03, 2.66, 3.12, M["enamel_g"])
            box(nm + "_signtrim", s - 0.045, s + 0.0, t - d / 2, t + d / 2, 2.62, 2.66, M["gold"])
            text(nm + "_sign", "LONG  PIG", (s - 0.05, t, 2.90), 0, 0.32, M["gold"], "DejaVuSerif-Bold.ttf", facing="-X")
        elif kind == "meat_rail":
            z = z0
            for yy in (t - d / 2 - 0.1, t + d / 2 + 0.1):
                cyl(nm + f"_hanger{yy:.1f}", s, yy, z, 0.008, L.CEILING["gs_counter"] - z, M["brass"], 6)
            cyl(nm + "_bar", s, t, z, 0.018, d + 0.2, M["brass"], 10, axis="Y")
            y = t - d / 2
            k = 0
            while y < t + d / 2:
                kind2 = k % 4
                if kind2 in (0, 2):
                    ln = random.uniform(0.35, 0.55)
                    cyl(nm + f"_salami{k}", s, y, z - ln - 0.06, 0.035, ln, M["meat"], 10)
                elif kind2 == 1:
                    sphere(nm + f"_provolone{k}", s, y, z - 0.32, 0.085, M["cheese"], (1, 1, 2.0), 12)
                else:
                    sphere(nm + f"_prosciutto{k}", s, y, z - 0.40, 0.10, M["meat2"], (0.8, 1.0, 2.6), 12)
                cyl(nm + f"_string{k}", s, y, z - 0.08, 0.003, 0.08, M["paper"], 4)
                y += random.uniform(0.16, 0.24)
                k += 1
        elif kind == "window_display":
            box(nm + "_platform", s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, h, M["beadboard"])
            box(nm + "_top", s - w / 2, s + w / 2 + 0.02, t - d / 2, t + d / 2, h, h + 0.03, M["green"])
            for k in range(3):
                products_on_shelf_y(nm + f"_p{k}", s - w / 2 + 0.05 + k * 0.17, s - w / 2 + 0.2 + k * 0.17, t - d / 2 + 0.1, t + d / 2 - 0.1, h + 0.03, 0.28 + k * 0.08)
            cbox(nm + "_tin_pyramid", s - 0.05, t, h + 0.65, 0.2, 0.6, 0.02, M["steel"])
        elif kind == "gingham_table":
            box(nm + "_top", s - w / 2, s + w / 2, t - d / 2, t + d / 2, h - 0.03, h, M["gingham"])
            for side in (-1, 1):
                box(nm + f"_drape_x{side}", s - w / 2 - 0.01 if side < 0 else s + w / 2, s - w / 2 if side < 0 else s + w / 2 + 0.01, t - d / 2, t + d / 2, h - 0.22, h, M["gingham"])
                box(nm + f"_drape_y{side}", s - w / 2, s + w / 2, t - d / 2 - 0.01 if side < 0 else t + d / 2, t - d / 2 if side < 0 else t + d / 2 + 0.01, h - 0.22, h, M["gingham"])
            for dx in (-0.85, 0.85):
                for dy in (-0.45, 0.45):
                    cyl(nm + f"_leg{dx}{dy}", s + dx, t + dy, 0, 0.025, h - 0.03, M["chair_wood"], 8)
            for k in range(3):
                cyl(nm + f"_plate{k}", s - 0.5 + k * 0.5, t + random.uniform(-0.2, 0.2), h, 0.12, 0.015, M["white"], 20)
            cyl(nm + "_wine", s + 0.2, t + 0.1, h, 0.04, 0.3, M["green"], 12)
            cbox(nm + "_cards", s - 0.2, t - 0.15, h + 0.01, 0.09, 0.06, 0.02, M["paper"])
        elif kind == "kitchenette":
            box(nm + "_base", s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, h - 0.03, M["enamel_w"])
            box(nm + "_top", s - w / 2, s + w / 2, t - d / 2, t + d / 2, h - 0.03, h, M["formica"])
            box(nm + "_fridge", s - w / 2, s + w / 2, t + d / 2 - 0.62, t + d / 2, 0, 1.6, M["enamel_w"])
            cyl(nm + "_pot", s, t - 0.6, h, 0.12, 0.18, M["steel"], 16)
            box(nm + "_shelf", s - w / 2, s - w / 2 + 0.25, t - d / 2, t + d / 2 - 0.7, 1.55, 1.57, M["trim"])
            for k in range(5):
                cyl(nm + f"_plate{k}", s - w / 2 + 0.12, t - d / 2 + 0.2 + k * 0.28, 1.57, 0.11, 0.02, M["white"], 16, axis="X")
        elif kind == "tv":
            box(nm + "_arm", s - 0.05, s + 0.05, t + 0.2, t + 0.62, 1.95, 2.0, M["black"])
            cbox(nm + "_body", s, t, 1.82, 0.42, 0.45, 0.36, M["dark"], 35)
            cbox(nm + "_screen", s - 0.12, t - 0.15, 1.83, 0.3, 0.02, 0.26, M["tv"], 35)
        elif kind == "desk":
            box(nm + "_top", s - w / 2, s + w / 2, t - d / 2, t + d / 2, h - 0.03, h, M["grey"])
            box(nm + "_ped", s + w / 2 - 0.42, s + w / 2, t - d / 2, t + d / 2, 0, h - 0.03, M["grey"])
            box(nm + "_ped2", s - w / 2, s - w / 2 + 0.04, t - d / 2, t + d / 2, 0, h - 0.03, M["grey"])
            for k in range(4):
                box(nm + f"_paper{k}", s - 0.5 + k * 0.2, s - 0.3 + k * 0.2, t - 0.2, t + 0.08, h, h + 0.01 + k * 0.005, M["paper"])
            cbox(nm + "_phone", s + 0.45, t, h + 0.05, 0.2, 0.22, 0.1, M["black"])
            cbox(nm + "_ashtray", s + 0.15, t + 0.15, h + 0.01, 0.12, 0.12, 0.02, M["brass"])
        elif kind in ("filing", "safe", "crates", "hand_truck", "range_hood", "prep_table", "sink", "meat_saw", "cooler_rack"):
            mm = {"filing": "grey", "safe": "dark", "crates": "cardboard", "hand_truck": "grey", "range_hood": "steel",
                  "prep_table": "steel", "sink": "steel", "meat_saw": "enamel_w", "cooler_rack": "steel"}[kind]
            if kind == "prep_table" and w > 1.5:
                box(nm + "_block", s - w / 2, s - w / 2 + 0.75, t - d / 2, t + d / 2, 0, h, mat_wood("butcher_block", "#7a5530", "#b58a55", 18.0, 0.7, 0.0, "X"))
                box(nm + "_steel", s - w / 2 + 0.78, s + w / 2, t - d / 2, t + d / 2, h - 0.04, h, M["steel"])
                for dx in (s - w / 2 + 0.8, s + w / 2 - 0.04):
                    for dy in (t - d / 2, t + d / 2 - 0.04):
                        box(nm + f"_leg{dx:.2f}{dy:.2f}", dx, dx + 0.04, dy, dy + 0.04, 0, h - 0.04, M["steel"])
                box(nm + "_shelf", s - w / 2 + 0.78, s + w / 2, t - d / 2, t + d / 2, 0.2, 0.22, M["steel"])
            elif kind == "range_hood":
                box(nm + "_range", s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, h, M["steel"])
                for k in range(6):
                    cyl(nm + f"_burner{k}", s - 0.15 + (k % 2) * 0.3, t - 0.8 + (k // 2) * 0.8, h, 0.1, 0.02, M["dark"], 16)
                box(nm + "_hood", s - w / 2 - 0.1, s + w / 2, t - d / 2 - 0.1, t + d / 2 + 0.1, 2.0, 2.6, M["steel"])
                cbox(nm + "_pot", s - 0.15, t - 0.8, h + 0.13, 0.3, 0.3, 0.26, M["steel"])
            elif kind == "cooler_rack":
                box(nm + "_bar", s - w / 2, s + w / 2, t - 0.02, t + 0.02, 1.95, 2.0, M["steel"])
                for k in range(9):
                    sphere(nm + f"_ham{k}", s - w / 2 + 0.2 + k * 0.32, t, 1.45, 0.12, M["meat2"], (0.8, 0.8, 2.3), 12)
                for k in range(4):
                    box(nm + f"_crate{k}", s - w / 2 + k * 0.75, s - w / 2 + k * 0.75 + 0.6, t - 0.6, t - 0.2, 0, 0.3 + (k % 2) * 0.3, M["cardboard"])
            elif kind == "sink":
                box(nm, s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, h, M[mm])
                box(nm + "_splash", s - w / 2, s + w / 2, t - d / 2, t - d / 2 + 0.03, h, h + 0.25, M[mm])
            elif kind == "meat_saw":
                box(nm + "_base", s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, 0.85, M["steel"])
                box(nm + "_head", s - w / 2 + 0.05, s + w / 2 - 0.05, t - d / 2 + 0.15, t + d / 2 - 0.15, 0.85, h, M["enamel_w"])
                box(nm + "_table", s - w / 2 - 0.05, s + w / 2 + 0.05, t - d / 2 - 0.05, t + d / 2 + 0.05, 0.85, 0.89, M["steel"])
            elif kind == "hand_truck":
                box(nm + "_frame", s - 0.2, s + 0.2, t + 0.1, t + 0.14, 0.05, h, M["grey"])
                cyl(nm + "_wheel1", s - 0.18, t, 0.0, 0.1, 0.05, M["dark"], 16, axis="X")
            else:
                box(nm, s - w / 2, s + w / 2, t - d / 2, t + d / 2, 0, h, M[mm])
                if kind == "crates":
                    for k in range(6):
                        cyl(nm + f"_btl{k}", s - 0.25 + (k % 3) * 0.25, t - 0.2 + (k // 3) * 0.4, h, 0.035, 0.28, M["green"] if k % 2 else M["cardboard"], 10)


# ------------------------------------------------------------------ lights
def kelvin(k):
    return {2400: (1.0, 0.60, 0.29), 2700: (1.0, 0.68, 0.40), 3000: (1.0, 0.75, 0.50), 4000: (1.0, 0.86, 0.72)}[k]


LIGHT_OBJS = []


def add_point(name, loc, watts, k=2700, radius=0.05, group="warm"):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = watts
    ld.color = kelvin(k)
    ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    COL.objects.link(o)
    LIGHT_OBJS.append((o, group, watts))
    return o


def add_area(name, loc, size, watts, k=3000, group="troffer"):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size
    ld.energy = watts
    ld.color = kelvin(k)
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    COL.objects.link(o)
    LIGHT_OBJS.append((o, group, watts))
    return o


def build_lights():
    amber = mat_emit("amber_glass", "#ff9a3c", 3.0)
    globe = mat_emit("opal_globe", "#ffe2b8", 4.0)
    troffer = mat_emit("troffer_lens", "#fff3dc", 3.0)
    troffer_c = mat_emit("troffer_lens_cool", "#eef4ff", 3.0)
    green_in = mat_emit("lamp_inner", "#ffd7a0", 2.0)
    for i, (kind, (s, t, z), note) in enumerate(L.LIGHTS):
        ceil = 3.2
        for code, poly in [(c, p) for _, c, p, _ in L.ZONES]:
            if L.inside((s, t), poly):
                ceil = L.CEILING[code]
        nm = f"lt_{kind}_{i}"
        if kind == "pendant_amber":
            cyl(nm + "_cord", s, t, z + 0.2, 0.004, ceil - z - 0.2, M["black"], 6)
            cyl(nm + "_shade", s, t, z, 0.20, 0.22, amber, 24, r2=0.06)
            add_point(nm, (s, t, z - 0.02), 45, 2400, 0.08)
        elif kind == "schoolhouse":
            cyl(nm + "_rod", s, t, z + 0.18, 0.008, ceil - z - 0.18, M["brass"], 8)
            cyl(nm + "_fitter", s, t, z + 0.12, 0.06, 0.07, M["brass"], 16)
            sphere(nm + "_globe", s, t, z, 0.15, globe, (1, 1, 0.9), 20)
            add_point(nm, (s, t, z - 0.18), 70, 2700, 0.12)
        elif kind == "sconce_brass":
            inward = (0, 1) if t < -1.0 else (1, 0)
            bx, by = s + inward[0] * 0.03, t + inward[1] * 0.03
            cbox(nm + "_plate", bx, by, z, 0.12 if inward[0] == 0 else 0.02, 0.02 if inward[0] == 0 else 0.12, 0.2, M["brass"])
            sphere(nm + "_shade", s + inward[0] * 0.15, t + inward[1] * 0.15, z + 0.05, 0.08, amber, (1, 1, 1.2), 14)
            add_point(nm, (s + inward[0] * 0.18, t + inward[1] * 0.18, z + 0.05), 18, 2400, 0.05)
        elif kind == "fan_light":
            cyl(nm + "_rod", s, t, z + 0.05, 0.015, ceil - z - 0.05, M["brass"], 8)
            cyl(nm + "_motor", s, t, z, 0.12, 0.12, M["brass"], 20)
            for k in range(4):
                o = cbox(nm + f"_blade{k}", s + 0.42 * math.cos(k * math.pi / 2 + 0.3), t + 0.42 * math.sin(k * math.pi / 2 + 0.3), z + 0.05, 0.62, 0.13, 0.012, M["trim"], math.degrees(k * math.pi / 2 + 0.3))
            sphere(nm + "_bowl", s, t, z - 0.05, 0.11, globe, (1, 1, 0.6), 16)
            add_point(nm, (s, t, z - 0.15), 40, 2700, 0.1)
        elif kind in ("troffer_day", "troffer_cool"):
            box(nm + "_lens", s - 0.3, s + 0.3, t - 0.6, t + 0.6, ceil - 0.01, ceil, troffer if kind == "troffer_day" else troffer_c)
            add_area(nm, (s, t, ceil - 0.02), (0.6, 1.2), 90 if kind == "troffer_day" else 110, 3000 if kind == "troffer_day" else 4000,
                     "troffer" if kind == "troffer_day" else "kitchen")
        elif kind == "pendant_green":
            cyl(nm + "_cord", s, t, z + 0.18, 0.004, ceil - z - 0.18, M["black"], 6)
            cyl(nm + "_shade", s, t, z, 0.26, 0.18, M["enamel_g"], 24, r2=0.05)
            cyl(nm + "_inner", s, t, z + 0.001, 0.25, 0.005, green_in, 24)
            add_point(nm, (s, t, z - 0.02), 110, 2700, 0.06, "back")
        elif kind == "desk_lamp":
            cyl(nm + "_base", s, t, z - 0.29, 0.07, 0.02, M["brass"], 16)
            cyl(nm + "_stem", s, t, z - 0.27, 0.01, 0.25, M["brass"], 8)
            cyl(nm + "_shade", s, t, z - 0.04, 0.12, 0.12, M["enamel_g"], 20, r2=0.06)
            add_point(nm, (s, t, z - 0.06), 14, 2700, 0.03, "back")
        elif kind == "bulb":
            cyl(nm + "_cord", s, t, z + 0.05, 0.004, ceil - z - 0.05, M["black"], 6)
            sphere(nm + "_bulb", s, t, z, 0.05, globe, (1, 1, 1.3), 12)
            add_point(nm, (s, t, z - 0.02), 45 if t < 9 or s > 10 else 35, 2700, 0.03, "back" if s < 10 else "kitchen")
        elif kind == "neon_open":
            neon = mat_emit("neon_red", "#ff2a1a", 12.0)
            text(nm + "_txt", "OPEN", (s, t + 0.02, z), 0, 0.22, neon, "DejaVuSans-Bold.ttf", extrude=0.012, facing="-Y")
            add_point(nm, (s, t + 0.12, z), 6, 2400, 0.1, "neon").data.color = (1.0, 0.15, 0.08)


def build_blinds(state="OPEN"):
    """W1 / W2 wood venetian blinds — OPEN = stacked under the head (concept)."""
    for key in ("W1", "W2"):
        o = L.OPENINGS[key]
        (x0, y0), (x1, y1) = o["p0"], o["p1"]
        z1 = OPEN_Z[key][1]
        if key == "W1":
            box("blind_stack_W1", x0, x1, -1.23 + 0.02, -1.23 + 0.09, z1 - 0.16, z1 - 0.02, M["blinds"])
            box("blind_head_W1", x0 - 0.03, x1 + 0.03, -1.23, -1.23 + 0.10, z1 - 0.02, z1 + 0.03, M["trim"])
        else:
            box("blind_stack_W2", -2.90 + 0.02, -2.90 + 0.09, y0, y1, z1 - 0.16, z1 - 0.02, M["blinds"])
            box("blind_head_W2", -2.90, -2.90 + 0.10, y0 - 0.03, y1 + 0.03, z1 - 0.02, z1 + 0.03, M["trim"])


# ------------------------------------------------------------------ world + time of day
def setup_world():
    w = bpy.data.worlds.new("world")
    SC.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    try:
        sky.sun_disc = False
    except Exception:
        pass
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.angle = math.radians(1.0)
    sun = bpy.data.objects.new("sun", sun_d)
    COL.objects.link(sun)
    return bg, sky, sun


def set_time(bg, sky, sun, tod):
    # sun from the street side (SW facade in -Y); azimuth in local frame
    if tod == "day":
        elev, az = 38, -125
        sky.sun_elevation = math.radians(elev)
        sky.sun_rotation = math.radians(az + 90)
        bg.inputs["Strength"].default_value = 0.35
        sun.data.energy = 3.5
        sun.data.color = (1.0, 0.95, 0.88)
        sun.hide_render = False
    else:
        bg.inputs["Strength"].default_value = 0.0 if tod == "night" else 0.08
        sky.sun_elevation = math.radians(-2 if tod == "evening" else -20)
        sun.hide_render = True
    a = math.radians(az if tod == "day" else 0)
    e = math.radians(elev if tod == "day" else 10)
    sun.rotation_euler = (math.pi / 2 - e, 0, a + math.pi / 2)
    for o, group, watts in LIGHT_OBJS:
        on = {"day": group in ("warm", "troffer", "kitchen", "back"),
              "evening": group in ("warm", "back", "neon", "kitchen"),
              "night": group in ("warm", "back", "neon", "kitchen")}[tod]
        o.hide_render = not on
        if group == "warm":
            o.data.energy = watts * (0.6 if tod == "day" else 1.0)
    SC.view_settings.exposure = {"day": 0.0, "evening": 0.4, "night": 0.9}[tod]


VIEWS = {
    "v0_overview_cutaway": dict(cam=(1.5, -8.5, 23.0), at=(6.6, 5.0, 0.0), lens=30, tod="day", free=True, cutaway=True,
                                title="Разрез сверху: зонирование"),
    "v1_entrance_day": dict(cam=(-1.05, 1.15, 1.62), at=(8.6, 4.0, 1.45), lens=16, tod="day",
                            title="Вход D1 → зал и прилавок, день"),
    "v2_booths_evening": dict(cam=(6.55, 2.05, 1.55), at=(0.6, -0.95, 0.95), lens=17, tod="evening",
                              title="Кабинки у витрины W1, вечер"),
    "v3_counter_day": dict(cam=(3.6, 1.6, 1.62), at=(9.6, 3.7, 1.85), lens=20, tod="day",
                           title="Прилавок, меню-борды, колбасы, день"),
    "v4_backroom_night": dict(cam=(5.30, 8.48, 1.72), at=(1.3, 10.9, 0.85), lens=15, tod="night",
                              title="Задняя комната, ночь"),
    "v5_kitchen_day": dict(cam=(10.55, 4.55, 1.70), at=(15.4, -0.4, 1.0), lens=16, tod="day",
                           title="Кухня / разделка у D2, день"),
}


def camera(v):
    cd = bpy.data.cameras.new("cam")
    cd.lens = v["lens"]
    cd.sensor_width = 36
    cd.clip_start = 0.05
    co = bpy.data.objects.new("cam", cd)
    COL.objects.link(co)
    co.location = v["cam"]
    d = Vector(v["at"]) - Vector(v["cam"])
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.shift_y = 0.0
    if v.get("free"):
        SC.camera = co
        return co
    # two-point perspective: keep verticals vertical (shift instead of pitch)
    pitch = math.atan2(d.z, Vector((d.x, d.y)).length)
    yaw = math.atan2(d.y, d.x)
    co.rotation_euler = (math.pi / 2, 0, yaw - math.pi / 2)
    cd.shift_y = math.tan(pitch) * cd.lens / cd.sensor_width * 0.95
    SC.camera = co
    return co


def main():
    build_shell()
    build_rooms()
    build_finishes()
    build_furniture()
    build_lights()
    build_blinds()
    bg, sky, sun = setup_world()
    SC.render.engine = "CYCLES"
    SC.cycles.device = "CPU"
    SC.cycles.samples = SAMPLES
    SC.cycles.use_adaptive_sampling = True
    SC.cycles.adaptive_threshold = 0.03
    SC.cycles.max_bounces = 6
    SC.cycles.diffuse_bounces = 3
    SC.cycles.glossy_bounces = 2
    SC.cycles.transparent_max_bounces = 8
    SC.cycles.caustics_reflective = False
    SC.cycles.caustics_refractive = False
    SC.cycles.sample_clamp_indirect = 6.0
    try:
        SC.cycles.use_denoising = True
    except Exception:
        pass
    SC.render.resolution_x = RES_X
    SC.render.resolution_y = int(RES_X * 9 / 16)
    SC.view_settings.view_transform = "AgX"
    try:
        SC.view_settings.look = "AgX - Medium High Contrast"
    except Exception as e:
        print("look:", e)
    SC.render.image_settings.file_format = "PNG"
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "gs_concept_blockout_v2.blend"))
    for key, v in VIEWS.items():
        if ONLY and key not in ONLY:
            continue
        set_time(bg, sky, sun, v["tod"])
        for o in bpy.data.objects:
            if o.name.startswith(("roof", "ceil_")) or o.name.startswith("lt_") and ("_cord" in o.name or "_rod" in o.name):
                o.hide_render = bool(v.get("cutaway"))
        camera(v)
        SC.render.filepath = os.path.join(OUT, key + ".png")
        bpy.ops.render.render(write_still=True)
        print("rendered", key, flush=True)


main()
