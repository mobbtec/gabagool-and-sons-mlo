# LONG PIG v0.2.9 — BACK OF HOUSE, premium final pass (owner brief "PREMIUM FIVEM MLO FINAL PASS", 2026-11-02).
# Same rooms and partitions as v0.2.8 (gs_boh_kit.py, concept plan v2) — nothing outside the vanilla envelope. Changes:
#   * kitchen rebuilt as a working line: hot line under a 4.7 m hood on the SE wall (griddle stand + griddle, 6-burner
#     range, twin fryer, landing table), dish station (3-bay sink + dish table) on P7, prep table with knife bar,
#     under-shelf task light and ticket rail on the SW wall, island, wire rack + 2 reach-ins on P1, hand sink, mats, grease;
#   * a real door in every doorway that needs one (staff room, storage from the corridor, office = solid wood, staff WC =
#     private wood door; cooler keeps its steel door; kitchen <-> storage stays an open service pass);
#   * office re-planned (desk / filing cabinet no longer intersect) + credenza with the FAMILY BUSINESS hidden compartment;
#   * storage stock rack with labelled cartons, corridor time clock, WC pipes + signs, fixes from the layout audit.
# Vanilla props are referenced by archetype name only; z values in the vanilla lists are BOTTOM heights (the kit subtracts
# the model's min z when it writes the entity, see gs_v025_kit.vanilla_entities).
import math
import gs_boh_kit as B
from gs_boh_kit import (V, PG, WORLD, Frame, F, emit, cbox, lathe, tube, FLOOR, CEIL, LT, VB, P, DAY_HOURS, wall_yaw, K6, K7,
                        WT, DOOR_H, _plane, _rect, _bands, _wall_overlay, steel_table, wall_shelf, counter_unit, table_rect,
                        wc_mirror, wall_notice, vent_grille, floor_drain, rubber_mat, WC_S, COOL_S, COOL_T, NIGHT_HOURS,
                        _on_wall, _against, BOH_TROFFERS, COOL_LAMPS, WC_LIGHT)
import gs_v029_vb

for _k, _v in gs_v029_vb.VB_V029.items():
    VB.setdefault(_k, _v)
V.MAT.setdefault("lp8", 27)
V.MAT.setdefault("troffer_off", 28)
V.REP.setdefault("lp8", 1.0)
V.REP.setdefault("troffer_off", 0.3)
MAT = V.MAT
YS, YN, XE = PG.YS, PG.YN, PG.XE

WOOD = 1001                           # BOH-only material (sentinel index): real walnut for the office furniture
BOH_MATS = list(B.BOH_MATS) + ["lp8", "wood29"]
_REMAP = {MAT[m]: i for i, m in enumerate(BOH_MATS) if m in MAT}
_REMAP[WOOD] = BOH_MATS.index("wood29")
WOOD_SPEC = ("normal_spec.sps", {"DiffuseSampler": "lp_wood_walnut", "BumpSampler": "lp_flat_n", "SpecSampler": "lp_matte_s"},
             {"specularIntensityMult": 0.35, "specularFalloffMult": 30.0, "specularFresnel": 0.97, "bumpiness": 1.0}, "lp_wood_walnut")

# ================================================================== lp8 atlas regions (gs_15n_make_v029_textures.py)
L8W, L8H = 1024.0, 512.0
REG8 = {
    "open_neon": (0, 0, 320, 128), "closed": (320, 0, 576, 128), "open_card": (576, 0, 832, 128),
    "staff_only": (832, 0, 1024, 64), "restroom": (832, 64, 1024, 128),
    "ticket1": (0, 128, 96, 320), "ticket2": (96, 128, 192, 320), "ticket3": (192, 128, 288, 320),
    "wash_hands": (288, 128, 480, 256), "ledger1": (480, 128, 640, 256), "ledger2": (640, 128, 800, 256),
    "pages": (800, 128, 1024, 256),
    "carton_cups": (288, 256, 480, 384), "carton_napkins": (480, 256, 672, 384), "carton_togo": (672, 256, 864, 384),
    "carton_foil": (864, 256, 1024, 384),
    "printer": (0, 320, 128, 384), "envelope": (128, 320, 288, 416), "kraft": (0, 384, 128, 512),
    "cigar": (288, 384, 480, 480), "photo": (480, 384, 608, 512), "dial": (608, 384, 704, 480),
    "switch_label": (704, 384, 768, 448), "pass_label": (768, 384, 1024, 448), "fryer_panel": (768, 448, 1024, 512),
    "black": (704, 448, 736, 480), "brass": (736, 448, 768, 480), "steel_dark": (128, 416, 160, 448),
    "paper": (160, 416, 192, 448), "cardboard": (192, 416, 288, 512), "felt_green": (608, 480, 704, 512),
}


def uv8(key, pad=1.5):
    x0, y0, x1, y1 = REG8[key]
    return ((x0 + pad) / L8W, 1.0 - (y1 - pad) / L8H, (x1 - pad) / L8W, 1.0 - (y0 + pad) / L8H)


def card(fr, x0, x1, z0, z1, y, key, hint, mat="lp8", flip=False):
    """Flat rectangle in a frame plane y = const, showing atlas region key (reads left -> right along +x)."""
    u0, v0, u1, v1 = uv8(key)
    if flip:
        u0, u1 = u1, u0
    vs = [fr.p(x0, y, z0), fr.p(x1, y, z0), fr.p(x1, y, z1), fr.p(x0, y, z1)]
    return F(vs, mat, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=hint)


def box8(fr, x0, x1, y0, y1, z0, z1, side_key, top_key=None, front=("-y",), mat="lp8"):
    """Solid box textured from the atlas: every face gets side_key, the top top_key (or side_key)."""
    out = []
    P_ = lambda x, y, z: fr.p(x, y, z)
    faces = {
        "-y": ([P_(x0, y0, z0), P_(x1, y0, z0), P_(x1, y0, z1), P_(x0, y0, z1)], fr.v(0, -1, 0)),
        "+y": ([P_(x1, y1, z0), P_(x0, y1, z0), P_(x0, y1, z1), P_(x1, y1, z1)], fr.v(0, 1, 0)),
        "-x": ([P_(x0, y1, z0), P_(x0, y0, z0), P_(x0, y0, z1), P_(x0, y1, z1)], fr.v(-1, 0, 0)),
        "+x": ([P_(x1, y0, z0), P_(x1, y1, z0), P_(x1, y1, z1), P_(x1, y0, z1)], fr.v(1, 0, 0)),
        "+z": ([P_(x0, y0, z1), P_(x1, y0, z1), P_(x1, y1, z1), P_(x0, y1, z1)], fr.v(0, 0, 1)),
    }
    for k, (vs, n) in faces.items():
        key = (top_key or side_key) if k == "+z" else side_key
        u0, v0, u1, v1 = uv8(key)
        emit(out, F(vs, mat, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=n))
    return out


# ================================================================== doors (vanilla GTA V leaves, referenced by name)
# x = leaf extent along the model X axis from the hinge (x = 0), z = model z range, y_off = slab centre offset (model y)
DOOR_SPECS = {
    "steel": dict(model="prop_map_door_01", x=(-1.21875, 0.0), z=(-1.06934, 1.37012), y_off=0.025,
                  min=(-1.21875, -0.11621, -1.06934), max=(0.0, 0.06592, 1.37012)),
    "roc": dict(model="v_ilev_roc_door1_l", x=(-0.0005, 0.9004), z=(-1.1499, 1.1499), y_off=0.0,
                min=(-0.0005, -0.0869, -1.1499), max=(0.9004, 0.0869, 1.1499)),
    "office": dict(model="v_ilev_sol_off_door01", x=(-1.1733, 0.0), z=(-1.0923, 1.0923), y_off=0.0,
                   min=(-1.1733, -0.1123, -1.0923), max=(0.0, 0.1123, 1.0923)),
    "wc": dict(model="v_ilev_ra_door3", x=(0.0, 1.1016), z=(-1.1499, 1.1499), y_off=0.0,
               min=(0.0, -0.1177, -1.1499), max=(1.1016, 0.1177, 1.1499)),
    "kitchen": dict(model="v_ilev_cor_firedoor", x=(-1.1499, 0.0), z=(-1.0195, 1.2803), y_off=0.0,
                    min=(-1.1499, -0.0474, -1.0195), max=(0.0, 0.0474, 1.2803)),
}
def register():
    """(Re)register the v0.2.9 vanilla bounds, materials and door models in the shared tables (they are rebuilt when the
    preview / build scripts reload the older kit modules)."""
    import sys
    global VB
    tables = [VB, getattr(B, "VB", None), getattr(sys.modules.get("gs_v027_kit"), "VB", None)]
    for tb in tables:
        if tb is not None:
            for k, v in gs_v029_vb.VB_V029.items():
                tb.setdefault(k, v)
    VB = sys.modules["gs_v027_kit"].VB if "gs_v027_kit" in sys.modules else VB
    V.MAT.setdefault("lp8", 27)
    V.MAT.setdefault("troffer_off", 28)
    V.REP.setdefault("lp8", 1.0)
    V.REP.setdefault("troffer_off", 0.3)
    for _spec in DOOR_SPECS.values():                               # door models known to the build / validation
        PG.VDOORS.setdefault(_spec["model"], dict(min=_spec["min"], max=_spec["max"]))


register()


def door_w(k):
    return DOOR_SPECS[k]["x"][1] - DOOR_SPECS[k]["x"][0]


def door_top(k):
    z0, z1 = DOOR_SPECS[k]["z"]
    return round(FLOOR + PG.DOOR_GAP + (z1 - z0) + 0.02, 3)


def door_hole(k, u0, did):
    return (u0, round(u0 + door_w(k) + 0.02, 4), door_top(k), "door:" + k + ":" + did)


def door_entity(kind, axis, fixed, h0, h1):
    """-> (archetype, (s, t, z_origin), yaw_rad): hinge 1 cm inside the jamb, slab centred in the partition."""
    spec = DOOR_SPECS[kind]
    leaf_neg = spec["x"][0] < -0.5
    z = round(FLOOR + PG.DOOR_GAP - spec["z"][0], 4)
    u = round(h1 - 0.01, 4) if leaf_neg else round(h0 + 0.01, 4)
    if axis == "s":                                     # wall along s at t = fixed; yaw 0: model x = +s, model y = +t
        return spec["model"], (u, round(fixed + spec["y_off"], 4), z), 0.0
    return spec["model"], (round(fixed - spec["y_off"], 4), u, z), math.pi / 2     # yaw 90: model x = +t, model y = -s


# ================================================================== partitions (same lines as v0.2.8, doors in the holes)
PARTS = [
    ("P1n corridor|storage", "t", 10.00, 7.06, YN, [door_hole("roc", 7.20, "gs_boh_storage")], ("std", "std")),
    ("P3 corridor|rooms", "s", 8.42, 0.54, 9.94, [door_hole("roc", 3.00, "gs_boh_staff"), door_hole("office", 6.72, "gs_boh_office"),
                                                  door_hole("wc", 8.62, "gs_boh_wc")], ("std", "std")),
    ("P4 entry|backroom", "t", 0.60, 8.48, YN, [], ("std", "std")),
    ("P5 backroom|office", "t", 5.60, 8.48, YN, [], ("std", "std")),
    ("P6 office|WC", "t", 8.30, 8.48, YN, [], ("std", "white")),
    ("P7 kitchen|storage", "s", 5.00, 10.06, XE, [(10.31, 11.31, DOOR_H, "open"), door_hole("steel", 13.40, "gs_boh_cooler")],
     ("white", "std")),
    ("P8 storage|cooler", "t", 12.80, 5.06, 8.66, [], ("std", "cool")),
    ("P9 cooler|storage", "s", 8.60, 12.86, XE, [], ("cool", "std")),
]


def partition_faces():
    """v0.2.8 partition builder over the v0.2.9 PARTS (hole tops follow the door heights)."""
    saved = B.PARTS
    B.PARTS = PARTS
    try:
        return B.partition_faces()
    finally:
        B.PARTS = saved


def boh_doors():
    """-> [(id, archetype, (s, t, z), yaw_rad)]"""
    out = []
    for name, axis, fixed, a0, a1, holes, fin in PARTS:
        for (h0, h1, top, kind) in holes:
            if not kind.startswith("door:"):
                continue
            _, k, did = kind.split(":")
            arch, pos, yaw = door_entity(k, axis, fixed, h0, h1)
            out.append((did, arch, pos, yaw))
    return out


# ================================================================== finishes (P1 kitchen face follows the new P1 door)
P1_DOOR29 = (-1.13, 0.05)            # hall <-> kitchen door gap on P1 (was -0.93 .. 0.07): v_ilev_cor_firedoor 1.15 m


def finishes():
    out = []
    D2 = PG.D2
    out += _wall_overlay((10.06, YS), (XE, YS), (0.0, 1.0), "white",
                         holes=[(D2["s"][0] - 10.06 - 0.075, D2["s"][1] - 10.06 + 0.075, D2["hole_top"] + 0.075)])
    out += _wall_overlay((XE, YS), (XE, 4.94), (-1.0, 0.0), "white")
    top = door_top("kitchen") + 0.075
    out += _wall_overlay((10.06, 4.94), (10.06, YS), (1.0, 0.0), "white",
                         holes=[(4.94 - P1_DOOR29[1] - 0.075, 4.94 - P1_DOOR29[0] + 0.075, top)])
    out += _wall_overlay((XE, 5.06), (XE, 8.54), (-1.0, 0.0), "cool")
    out += _wall_overlay((WC_S[0], YN), (WC_S[1], YN), (0.0, -1.0), "white")
    out += _wall_overlay((9.94, 8.48), (9.94, YN), (-1.0, 0.0), "white")
    for (s0, s1, t0, t1, mat) in ((10.06, XE, YS, 4.94, "tile"), (WC_S[0], WC_S[1], 8.48, YN, "tile_white"),
                                  (COOL_S[0], COOL_S[1], COOL_T[0], COOL_T[1], "rubber")):
        z = FLOOR + 0.004
        rep = 0.45 if mat != "rubber" else 1.0
        vs = [(s0, t0, z), (s1, t0, z), (s1, t1, z), (s0, t1, z)]
        emit(out, F(vs, mat, [(s0 / rep, t0 / rep), (s1 / rep, t0 / rep), (s1 / rep, t1 / rep), (s0 / rep, t1 / rep)], hint=(0, 0, 1)))
    return out


# ================================================================== kitchen equipment (own geometry)
HOOD_T = (0.20, 4.88)                # hood along the SE wall (t), depth 1.10 m from the wall
HOOD_D = 1.10
HOOD_LAMPS_T = (0.95, 2.55, 4.15)    # lamp lenses under the hood = positions of the hood-switch lights (client)
GRIDDLE_STAND = (15.32, 16.13, 0.25, 1.80)
RANGE_T = 2.60
FRYER = (15.35, 16.13, 3.38, 3.88)
LANDING = (15.38, 16.13, 3.93, 4.85)
ISLAND = (12.10, 13.90, 1.45, 2.25)
PREP = (12.20, 13.70, YS + 0.01, YS + 0.73)
DISH_TABLE = (12.80, 13.34, 4.12, 4.93)
SINK3_S = 12.10                       # centre of the 3-bay sink on P7
RACK_K = (10.07, 10.52, 0.20, 1.40)   # dry-goods wire rack on P1 (kitchen side)
FRIDGES_T = (1.95, 2.85)
TICKET_RAIL = (10.45, 11.15, 1.52)    # s range + height, on the SW wall (kitchen side), next to the hall door
HOOD_SWITCH = (XE - 0.009, 0.12, 1.35)


def hood_frame():
    return Frame((XE, HOOD_T[0], 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


def exhaust_hood29():
    """Wall canopy hood on the SE wall: sloped front, skirts, baffle filters, gutter, 3 lamp lenses (off unless the hood
    is switched on - the client draws their light), fire-suppression line with nozzles, duct."""
    fr = hood_frame()
    L, Dp = HOOD_T[1] - HOOD_T[0], HOOD_D
    z0, z1, zt = 2.05, 2.30, 2.62
    out = []
    out += cbox(fr, 0.0, L, 0.0, Dp - 0.30, z1, zt, "steel", grain="x")
    vs = [fr.p(0.0, Dp, z1), fr.p(L, Dp, z1), fr.p(L, Dp - 0.30, zt), fr.p(0.0, Dp - 0.30, zt)]
    emit(out, F(vs, "steel", [(0, 0), (L, 0), (L, 0.4), (0, 0.4)], hint=fr.v(0.0, 0.73, 0.68)))
    out += cbox(fr, 0.0, L, Dp - 0.02, Dp, z0, z1, "steel", grain="x")
    for x0 in (0.0, L - 0.02):
        out += cbox(fr, x0, x0 + 0.02, 0.0, Dp, z0, z1, "steel", grain="y")
        xs = x0 if x0 == 0.0 else x0 + 0.02
        vs = [fr.p(xs, Dp, z1), fr.p(xs, 0.0, z1), fr.p(xs, 0.0, zt), fr.p(xs, Dp - 0.30, zt)]
        emit(out, F(vs, "steel", [(0, 0), (1, 0), (1, 0.3), (0, 0.3)], hint=fr.v(-1.0 if x0 == 0.0 else 1.0, 0.0, 0.0)))
    nf = int((L - 0.1) / 0.45)
    for k in range(nf):
        a = 0.05 + k * (L - 0.1) / nf
        b = a + (L - 0.1) / nf - 0.012
        vs = [fr.p(a, 0.10, z1 + 0.015), fr.p(b, 0.10, z1 + 0.015), fr.p(b, Dp - 0.12, z1 + 0.015), fr.p(a, Dp - 0.12, z1 + 0.015)]
        emit(out, F(vs, "iron", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=fr.v(0.0, 0.0, -1.0)))
    out += cbox(fr, 0.02, L - 0.02, Dp - 0.08, Dp - 0.02, z0 - 0.02, z0 + 0.02, "steel", grain="x")
    for tl in HOOD_LAMPS_T:                                                   # lamp lenses (enamel white, unlit)
        x = tl - HOOD_T[0]
        out += cbox(fr, x - 0.13, x + 0.13, Dp - 0.36, Dp - 0.22, z1 - 0.012, z1 + 0.004, "enamel", grain="x", skip=("+z",))
    # wet-chemical fire suppression: line along the hood, drops with nozzles over each appliance
    out += tube(fr, [(0.05, Dp - 0.50, z1 + 0.06), (L - 0.05, Dp - 0.50, z1 + 0.06)], 0.012, 6, "steel")
    for tl in (1.0, 2.6, 3.62, 4.4):
        x = tl - HOOD_T[0]
        out += tube(fr, [(x, Dp - 0.50, z1 + 0.06), (x, Dp - 0.50, z1 - 0.05)], 0.008, 6, "steel")
        out += lathe(fr.child(x, Dp - 0.50, z1 - 0.07), [(0.0, 0.0), (0.016, 0.0), (0.012, 0.02), (0.0, 0.02)], 6, "iron")
    xc = L / 2
    out += cbox(fr, xc - 0.28, xc + 0.28, 0.08, 0.62, zt, CEIL, "steel", grain="z")                    # duct
    return out


def fryer(s0, s1, t0, t1):
    """Twin-vat floor fryer: cabinet on legs, two oil vats (dark), baskets on the hanger, flue, control panel."""
    out = []
    zt = 0.92
    for (s, t) in ((s0 + 0.05, t0 + 0.05), (s1 - 0.05, t0 + 0.05), (s1 - 0.05, t1 - 0.05), (s0 + 0.05, t1 - 0.05)):
        out += tube(WORLD, [(s, t, FLOOR), (s, t, FLOOR + 0.12)], 0.02, 8, "steel", caps=True)
    out += cbox(WORLD, s0, s1, t0, t1, FLOOR + 0.12, zt - 0.04, "steel", ch=0.004, grain="z")
    out += cbox(WORLD, s0, s1, t0, t1, zt - 0.04, zt, "steel", grain="x")
    tm = (t0 + t1) / 2
    for (a, b) in ((t0 + 0.03, tm - 0.01), (tm + 0.01, t1 - 0.03)):                # oil (dark iron, slightly sunk)
        vs = [(s0 + 0.10, a, zt + 0.0015), (s1 - 0.14, a, zt + 0.0015), (s1 - 0.14, b, zt + 0.0015), (s0 + 0.10, b, zt + 0.0015)]
        emit(out, F(vs, "iron", [(0, 0), (1, 0), (1, 1), (0, 1)], hint=(0.0, 0.0, 1.0)))
        # basket resting on the hanger (wire frame) + handle to the front
        ba, bb = a + 0.02, b - 0.02
        for zz in (zt + 0.06, zt + 0.17):
            out += tube(WORLD, [(s0 + 0.16, ba, zz), (s1 - 0.20, ba, zz), (s1 - 0.20, bb, zz), (s0 + 0.16, bb, zz), (s0 + 0.16, ba, zz)],
                        0.004, 4, "steel")
        for (ss, tt) in ((s0 + 0.16, ba), (s1 - 0.20, ba), (s1 - 0.20, bb), (s0 + 0.16, bb)):
            out += tube(WORLD, [(ss, tt, zt + 0.06), (ss, tt, zt + 0.17)], 0.004, 4, "steel")
        out += tube(WORLD, [(s0 + 0.16, (ba + bb) / 2, zt + 0.15), (s0 - 0.10, (ba + bb) / 2, zt + 0.22)], 0.009, 6, "iron")
    out += cbox(WORLD, s1 - 0.12, s1, t0, t1, zt, zt + 0.34, "steel", grain="y")                 # flue / back riser
    out += cbox(WORLD, s1 - 0.10, s1 - 0.06, t0 + 0.02, t1 - 0.02, zt + 0.22, zt + 0.25, "steel", grain="y")   # hanger rod
    fr = Frame((s0 - 0.002, t1, 0.0), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    emit(out, card(fr, 0.03, t1 - t0 - 0.03, 0.70, 0.82, 0.0, "fryer_panel", (-1.0, 0.0, 0.0)))
    return out


def wire_rack(s0, s1, t0, t1, levels, mat="steel"):
    """Chrome wire shelving unit: 4 posts, wire decks (thin boxes)."""
    out = []
    ztop = levels[-1] + 0.05
    for (s, t) in ((s0 + 0.012, t0 + 0.012), (s1 - 0.012, t0 + 0.012), (s1 - 0.012, t1 - 0.012), (s0 + 0.012, t1 - 0.012)):
        out += tube(WORLD, [(s, t, FLOOR), (s, t, ztop)], 0.012, 8, mat, caps=True)
    for z in levels:
        out += cbox(WORLD, s0, s1, t0, t1, z - 0.012, z, mat, grain="x" if (s1 - s0) > (t1 - t0) else "y")
        for k in range(1, 6):                                           # wire grid read on the deck top
            if (s1 - s0) > (t1 - t0):
                x = s0 + (s1 - s0) * k / 6
                out += cbox(WORLD, x - 0.003, x + 0.003, t0, t1, z, z + 0.004, "iron", grain="y")
            else:
                y = t0 + (t1 - t0) * k / 6
                out += cbox(WORLD, s0, s1, y - 0.003, y + 0.003, z, z + 0.004, "iron", grain="x")
    return out


def knife_bar(p0, p1, z, n=(0.0, 1.0)):
    """Magnetic knife strip on a wall + 5 knives (steel blades, black handles)."""
    out = []
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    fr = Frame((p0[0], p0[1], 0.0), (d[0], d[1], 0.0), (n[0], n[1], 0.0), (0.0, 0.0, 1.0))
    out += cbox(fr, 0.0, L, 0.0, 0.018, z - 0.02, z + 0.02, "iron", grain="x")
    for k, (bl, hw) in enumerate(((0.20, 0.022), (0.16, 0.018), (0.26, 0.030), (0.12, 0.016), (0.22, 0.026))):
        x = 0.06 + k * (L - 0.12) / 4
        out += cbox(fr, x - hw, x + hw, 0.019, 0.023, z - 0.02 - bl, z - 0.02, "steel", grain="z")    # blade
        out += cbox(fr, x - 0.012, x + 0.012, 0.019, 0.032, z - 0.02, z + 0.10, "rubber", ch=0.004, grain="z")   # handle
    return out


def strip_light(fr, x0, x1, y, z):
    """Under-shelf fluorescent: slim steel housing with a diffuser facing down (emissive troffer lens)."""
    out = []
    out += cbox(fr, x0, x1, y - 0.035, y + 0.035, z, z + 0.035, "steel", grain="x")
    vs = [fr.p(x0 + 0.02, y - 0.03, z - 0.002), fr.p(x1 - 0.02, y - 0.03, z - 0.002), fr.p(x1 - 0.02, y + 0.03, z - 0.002),
          fr.p(x0 + 0.02, y + 0.03, z - 0.002)]
    emit(out, F(vs, "troffer", [(0.1, 0.1), (0.9, 0.1), (0.9, 0.3), (0.1, 0.3)], hint=fr.v(0.0, 0.0, -1.0)))
    return out


def ticket_rail():
    s0, s1, z = TICKET_RAIL
    fr = Frame((s1, YS + 0.009, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    out = []
    out += cbox(fr, 0.0, s1 - s0, 0.0, 0.030, z - 0.018, z + 0.018, "steel", ch=0.004, grain="x")
    out += cbox(fr, 0.0, s1 - s0, 0.0, 0.004, z + 0.04, z + 0.115, "lp8", grain="x")    # label backing (overwritten below)
    emit(out, card(fr, 0.02, s1 - s0 - 0.02, z + 0.045, z + 0.11, 0.0045, "pass_label", (0.0, 1.0, 0.0)))
    for k, key in enumerate(("ticket2", "ticket1")):                      # two orders already up (static)
        x = 0.10 + k * 0.13
        emit(out, card(fr, x, x + 0.075, z - 0.17, z + 0.012, 0.032 + 0.001 * k, key, (0.0, 1.0, 0.0)))
    return out


def kitchen_faces():
    out = []
    out += exhaust_hood29()
    s0, s1, t0, t1 = GRIDDLE_STAND
    out += steel_table(s0, s1, t0, t1, zt=0.74, shelf=0.20)
    out += fryer(*FRYER)
    out += steel_table(*LANDING, splash="+s")
    out += steel_table(*ISLAND)
    out += steel_table(*PREP, splash="-t")
    out += steel_table(*DISH_TABLE, splash="+t")
    out += wire_rack(*RACK_K, levels=(0.18, 0.58, 0.98, 1.38, 1.78))
    # shelves: over the prep table (SW wall) and over the dish station (P7)
    out += wall_shelf((PREP[0], YS + 0.009), (PREP[1], YS + 0.009), (0.0, 1.0), 1.78)
    out += wall_shelf((11.40, 4.931), (13.30, 4.931), (0.0, -1.0), 1.64)
    frs = Frame((PREP[0], YS + 0.009, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    out += strip_light(frs, 0.10, PREP[1] - PREP[0] - 0.10, 0.20, 1.71)
    out += knife_bar((12.35, YS + 0.009), (12.95, YS + 0.009), 1.34)
    out += ticket_rail()
    # floor: drain, rubber mats at the line / sink / prep, grease and mop marks
    out += floor_drain(14.55, 2.60)
    out += rubber_mat(14.60, 15.20, 0.35, 4.75)
    out += rubber_mat(11.50, 12.70, 3.55, 4.08)
    out += rubber_mat(12.30, 13.60, -0.46, 0.02)
    for (s, t, q, cell) in ((14.95, 1.05, 0.55, K6.GREASE), (14.95, 2.70, 0.6, K6.GREASE), (14.90, 3.65, 0.45, K6.GREASE),
                            (13.0, 2.9, 0.6, K6.MOP), (12.0, 0.6, 0.5, K6.MOP)):
        emit(out, K6.d5((s - q, t - q, FLOOR + 0.0045), (2 * q, 0.0, 0.0), (0.0, 2 * q, 0.0), cell, (0.0, 0.0, 1.0)))
    # grease mist on the tile behind the line (above the equipment, below the hood)
    emit(out, K6.d5((XE - 0.011, 0.30, 1.05), (0.0, 4.5, 0.0), (0.0, 0.0, 0.95), K6.SCUFF_BAND, (-1.0, 0.0, 0.0)))
    # wash-hands sign over the hand sink
    frw = Frame((11.60, YS + 0.009, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    emit(out, card(frw, -0.15, 0.15, 1.30, 1.50, 0.003, "wash_hands", (0.0, 1.0, 0.0)))
    return out


def kitchen_collision():
    m = "METAL_SOLID_MEDIUM"
    return [((GRIDDLE_STAND[0], GRIDDLE_STAND[1], GRIDDLE_STAND[2], GRIDDLE_STAND[3], FLOOR, 0.90), m),
            ((FRYER[0], FRYER[1], FRYER[2], FRYER[3], FLOOR, 1.26), m),
            ((LANDING[0], LANDING[1], LANDING[2], LANDING[3], FLOOR, 0.91), m),
            ((ISLAND[0], ISLAND[1], ISLAND[2], ISLAND[3], FLOOR, 0.91), m),
            ((PREP[0], PREP[1], PREP[2], PREP[3], FLOOR, 0.91), m),
            ((DISH_TABLE[0], DISH_TABLE[1], DISH_TABLE[2], DISH_TABLE[3], FLOOR, 0.91), m),
            ((RACK_K[0], RACK_K[1], RACK_K[2], RACK_K[3], FLOOR, 1.83), m)]


def kitchen_vanilla():
    out = []
    n_e = (-1.0, 0.0)
    yaw_e = wall_yaw(n_e)
    gs = GRIDDLE_STAND
    out.append(("prop_griddle_01", (gs[0] + gs[1]) / 2, (gs[2] + gs[3]) / 2, 0.74, yaw_e))
    out.append(_against("prop_cooker_03", (XE - 0.009, RANGE_T), n_e))
    out += [("prop_kitch_pot_huge", 15.88, 2.25, 0.905, 15.0), ("prop_kitch_pot_lrg", 15.50, 2.95, 0.905, 200.0),
            ("prop_kitch_pot_fry", 15.45, 2.25, 0.905, 95.0)]
    out += [("v_res_tt_pot02", 15.75, 0.55, 0.905, 0.0), ("prop_kitch_pot_lrg2", 15.80, 4.20, 0.91, 60.0),
            ("v_res_tt_pot01", 15.55, 4.60, 0.91, 0.0), ("prop_ladel", 15.62, 4.05, 0.91, 30.0)]
    # dish station on P7
    out.append(_against("prop_ff_sink_02", (SINK3_S, 4.94), (0.0, -1.0)))
    out += [("prop_detergent_01a", 13.05, 4.78, 0.91, 200.0), ("prop_detergent_01b", 13.20, 4.70, 0.91, 170.0),
            ("v_res_tt_platepile", 12.98, 4.40, 0.91, 0.0)]
    out += [("v_res_tt_platepile", 11.75, 4.77, 1.645, 0.0), ("v_res_tt_platepile", 12.05, 4.77, 1.645, 30.0),
            ("v_ind_cs_tray02", 12.50, 4.76, 1.645, 90.0), ("v_ind_cs_tray02", 12.52, 4.76, 1.725, 92.0),
            ("v_res_m_pot1", 12.95, 4.80, 1.645, 0.0)]
    # reach-in fridges + dry-goods rack on P1
    for t in FRIDGES_T:
        out.append(_against("prop_fridge_01", (10.06 + 0.009, t), (1.0, 0.0)))
    rs = (RACK_K[0] + RACK_K[1]) / 2
    out += [("v_ret_247_flour", rs, 0.40, 0.58, 0.0), ("v_ret_247_flour", rs, 0.65, 0.58, 12.0), ("v_ret_247_flour", rs, 0.90, 0.58, -8.0),
            ("v_ind_cs_bottle", rs, 0.45, 0.18, 0.0), ("v_ind_cs_bottle", rs, 0.75, 0.18, 20.0),
            ("v_res_foodjarb", rs, 0.40, 0.98, 0.0), ("v_res_foodjarc", rs, 0.62, 0.98, 0.0), ("prop_metalfoodjar_01", rs, 0.85, 0.98, 0.0),
            ("v_res_tt_can01", rs, 1.10, 0.98, 0.0), ("v_res_tt_can02", rs, 1.22, 0.98, 30.0),
            ("prop_pizza_box_02", rs, 0.80, 1.78, 90.0), ("prop_pizza_box_02", rs, 0.81, 1.87, 93.0), ("prop_pizza_box_02", rs, 0.79, 1.96, 88.0),
            ("prop_paper_bag_small", rs, 1.15, 1.38, 90.0), ("prop_paper_bag_small", rs, 1.25, 1.38, 80.0),
            ("v_ind_rc_plaztray", rs, 0.80, 1.38, 90.0)]
    # prep table (SW wall)
    pz = 0.91
    out += [("v_res_fa_chopbrd", 12.55, YS + 0.40, pz, 0.0), ("v_res_fa_chopbrd", 13.25, YS + 0.38, pz, 4.0),
            ("prop_cleaver", 12.62, YS + 0.36, pz + 0.02, 70.0), ("prop_knife_stand", 12.30, YS + 0.12, pz, 0.0),
            ("v_ind_cs_tray01", 12.95, YS + 0.20, pz, 0.0), ("v_ret_247_flour", 13.58, YS + 0.12, pz, 0.0),
            ("v_ind_cfbottle", 13.48, YS + 0.10, pz, 0.0), ("v_ret_ta_spray", 13.62, YS + 0.30, pz, 25.0)]
    out += [("v_res_tt_pot03", 12.45, YS + 0.30, 0.25, 0.0), ("v_ind_rc_plaztray", 13.20, YS + 0.36, 0.25, 0.0)]
    out += [("prop_metalfoodjar_01", 12.40, YS + 0.12, 1.79, 0.0), ("prop_metalfoodjar_01", 12.62, YS + 0.12, 1.79, 0.0),
            ("v_res_foodjara", 12.90, YS + 0.14, 1.79, 0.0), ("v_res_foodjarb", 13.15, YS + 0.14, 1.79, 0.0),
            ("v_ind_cs_bottle", 13.45, YS + 0.16, 1.79, 0.0)]
    # island
    out += [("v_ind_cs_tray01", 12.55, 1.85, 0.91, 90.0), ("v_ind_cs_tray01", 13.10, 1.85, 0.91, 90.0),
            ("v_res_fa_chopbrd", 13.62, 1.78, 0.91, 85.0), ("prop_ladel", 13.55, 2.08, 0.91, 30.0),
            ("prop_kitch_pot_med", 12.40, 1.80, 0.25, 0.0), ("v_res_tt_pot01", 13.25, 1.85, 0.25, 0.0)]
    # hand sink, soap, paper towels; bin; extinguisher by D2; hood switch
    out.append(_on_wall("prop_ff_sink_01", (11.60, YS + 0.009), (0.0, 1.0), 0.80))
    out.append(_on_wall("prop_soap_disp_01", (11.28, YS + 0.009), (0.0, 1.0), 1.08))
    out.append(_on_wall("prop_handdry_01", (11.95, YS + 0.009), (0.0, 1.0), 1.12))
    out.append(("prop_cs_bin_02", 13.42, -0.20, FLOOR, 0.0))
    out.append(("prop_fire_exting_1a", XE - 0.14, -0.95, FLOOR, wall_yaw(n_e)))
    sw = VB["v_serv_switch_2"]
    out.append(("v_serv_switch_2", HOOD_SWITCH[0] - sw[0][0], HOOD_SWITCH[1], HOOD_SWITCH[2] + sw[0][2], 180.0))
    return out


# ================================================================== storage, cooler, corridor, entry, back room, office, WC
STOCK_RACK = (10.07, 10.52, 8.45, 9.65)
CARTONS = [  # (s0, s1, t0, t1, z_bottom, label) on the stock rack decks
    (10.10, 10.49, 8.50, 8.92, 0.18, "carton_cups"), (10.10, 10.49, 8.96, 9.38, 0.18, "carton_cups"),
    (10.10, 10.49, 8.50, 8.92, 0.58, "carton_napkins"), (10.10, 10.49, 8.96, 9.60, 0.58, "carton_togo"),
    (10.10, 10.49, 8.50, 9.05, 0.98, "carton_foil"), (10.10, 10.49, 9.10, 9.60, 0.98, "carton_napkins"),
    (10.12, 10.47, 8.55, 9.00, 1.38, "carton_cups")]


def carton(s0, s1, t0, t1, zb, label, h=0.30):
    """Stock carton: kraft sides, label on the face towards the room (+s), taped top."""
    out = []
    out += box8(WORLD, s0, s1, t0, t1, zb, zb + h, "cardboard", top_key="kraft")
    fr = Frame((s1 + 0.001, t0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    emit(out, card(fr, 0.02, t1 - t0 - 0.02, zb + 0.03, zb + h - 0.03, 0.0, label, (1.0, 0.0, 0.0)))
    return out


def storage_faces():
    out = []
    out += wall_notice((10.07, 9.4 + 0.5), (1.0, 0.0), 1.35, 0.26, 0.26, "schedule")
    out += wire_rack(*STOCK_RACK, levels=(0.18, 0.58, 0.98, 1.38, 1.78))
    for c in CARTONS:
        out += carton(*c)
    return out


def corridor_faces():
    out = B.corridor_faces()
    return out


def staff_entry_faces():
    return B.staff_entry_faces()


def backroom_faces():
    return B.backroom_faces()


# ---------------------------------------------------------------- office: re-planned + FAMILY BUSINESS credenza
DESK_S = 6.62                         # desk centre (was 6.95 -> it intersected the filing cabinet)
FILECAB_T = 10.15                     # filing cabinet on the NE office wall, clear of the desk and of the door swing
CRED = (5.67, 6.13, 9.05, 10.31)      # credenza on P5 (office side), s0..s1 (depth), t0..t1 (length)
CRED_TOP = 0.76
SECRET_DOOR = dict(hinge=(6.13, 10.29), width=0.58, z0=0.105, z1=0.715)   # right-hand leaf (north half), opens to +s
SECRET_POINT = (6.45, 9.98, 0.55)     # interaction point in front of the credenza (MLO-local)


def credenza():
    """Old walnut credenza: plinth, carcass, top with overhang, LEFT door + drawer (static), RIGHT bay = hidden
    compartment (its leaf is the client-side object lp_secret_door): inner box, shelf, felt-lined floor."""
    s0, s1, t0, t1 = CRED
    out = []
    zt = CRED_TOP
    tm = (t0 + t1) / 2
    out += cbox(WORLD, s0 + 0.04, s1 - 0.03, t0 + 0.03, t1 - 0.03, FLOOR, 0.105, "rubber", grain="y")            # plinth (dark)
    out += cbox(WORLD, s0, s1, t0, t1, zt - 0.03, zt, WOOD, ch=0.006, grain="y")                              # top
    out += cbox(WORLD, s0, s1 - 0.02, t0, t0 + 0.02, 0.105, zt - 0.03, WOOD, grain="z")                       # end panels
    out += cbox(WORLD, s0, s1 - 0.02, t1 - 0.02, t1, 0.105, zt - 0.03, WOOD, grain="z")
    out += cbox(WORLD, s0, s0 + 0.02, t0, t1, 0.105, zt - 0.03, WOOD, grain="y")                              # back
    out += cbox(WORLD, s0, s1 - 0.02, t0, t1, 0.105, 0.125, WOOD, grain="y")                                  # bottom
    out += cbox(WORLD, s0, s1 - 0.02, tm - 0.01, tm + 0.01, 0.105, zt - 0.03, WOOD, grain="z")                # divider
    # LEFT bay: closed door + drawer (static)
    out += cbox(WORLD, s1 - 0.02, s1, t0 + 0.02, tm - 0.01, 0.105, 0.56, WOOD, ch=0.003, grain="z")
    out += cbox(WORLD, s1 - 0.02, s1, t0 + 0.02, tm - 0.01, 0.57, zt - 0.035, WOOD, ch=0.003, grain="y")
    for (zz, tt) in ((0.50, tm - 0.07), (0.66, (t0 + tm) / 2)):
        out += lathe(Frame((s1, tt, zz), (0, 1, 0), (0, 0, 1), (1, 0, 0)), [(0.0, 0.0), (0.012, 0.0), (0.014, 0.018), (0.0, 0.026)], 8,
                     "steel")
    # RIGHT bay interior (seen only when the hidden leaf is open): dark felt floor, inner shelf, false back pulled forward
    vs = [(s0 + 0.02, tm + 0.01, 0.126), (s1 - 0.02, tm + 0.01, 0.126), (s1 - 0.02, t1 - 0.02, 0.126), (s0 + 0.02, t1 - 0.02, 0.126)]
    u0, v0, u1, v1 = uv8("felt_green")
    emit(out, F(vs, "lp8", [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=(0, 0, 1)))
    out += cbox(WORLD, s0 + 0.02, s1 - 0.04, tm + 0.01, t1 - 0.02, 0.43, 0.445, WOOD, grain="y")             # inner shelf
    out += cbox(WORLD, s0 + 0.06, s0 + 0.075, tm + 0.03, t1 - 0.04, 0.13, 0.42, WOOD, grain="y")             # false back (ajar)
    # contents: small steel safe (bottom), ledgers + envelopes + cigar box + photo (shelf)
    ss0, ss1, st0, st1 = s0 + 0.09, s0 + 0.37, tm + 0.04, tm + 0.34
    out += cbox(WORLD, ss0, ss1, st0, st1, 0.126, 0.40, "iron", ch=0.008, grain="z")
    frd = Frame((ss1 + 0.001, st1, 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    emit(out, card(frd, 0.08, 0.20, 0.20, 0.32, 0.0, "dial", (1.0, 0.0, 0.0)))
    out += cbox(WORLD, ss1, ss1 + 0.018, st0 + 0.04, st0 + 0.07, 0.24, 0.30, "steel", grain="z")                # handle
    ledgers = [(s0 + 0.08, s0 + 0.33, tm + 0.05, tm + 0.085, "ledger1"), (s0 + 0.08, s0 + 0.33, tm + 0.088, tm + 0.12, "ledger2"),
               (s0 + 0.08, s0 + 0.33, tm + 0.123, tm + 0.16, "ledger1")]
    for (a, b, c, d, key) in ledgers:                                                                             # standing books
        out += box8(WORLD, a, b, c, d, 0.446, 0.446 + 0.24, key, top_key="pages")
    out += box8(WORLD, s0 + 0.10, s0 + 0.32, tm + 0.20, tm + 0.31, 0.446, 0.466, "envelope", top_key="envelope")   # envelopes
    out += box8(WORLD, s0 + 0.11, s0 + 0.31, tm + 0.21, tm + 0.30, 0.466, 0.482, "envelope", top_key="envelope")
    out += box8(WORLD, s0 + 0.12, s0 + 0.36, t1 - 0.17, t1 - 0.04, 0.446, 0.50, "cigar", top_key="cigar")         # cigar box
    frp = Frame((s0 + 0.08, t1 - 0.15, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    emit(out, card(frp, 0.0, 0.10, 0.50, 0.63, 0.30, "photo", (1.0, 0.0, 0.0)))                                    # leaning photo
    return out


def office_faces():
    out = []
    out += wall_notice((7.0, 11.411), (0.0, -1.0), 1.35, 0.30, 0.30, "calendar")
    out += wall_notice((7.5, 11.411), (0.0, -1.0), 1.45, 0.26, 0.26, "permit")
    out += wall_notice((5.669, 10.6), (1.0, 0.0), 1.50, 0.26, 0.26, "shop_photo", d=0.006)
    out += wall_notice((5.669, 10.95), (1.0, 0.0), 1.38, 0.22, 0.22, "we_card")
    out += wall_shelf((5.669, 9.90), (5.669, 11.30), (1.0, 0.0), 1.80, depth=0.28, mat=WOOD)
    out += credenza()
    return out


def wc_faces():
    out = B.wc_faces()
    # exposed supply / waste pipes (old building): sink feeds + trap, toilet feed, corner riser
    s_w = WC_S[0] + 0.009
    for dt in (-0.10, 0.10):
        out += tube(WORLD, [(s_w, 10.05 + dt, 0.42), (s_w + 0.14, 10.05 + dt, 0.42), (s_w + 0.14, 10.05 + dt, 0.70)], 0.007, 6, "steel")
        out += lathe(Frame((s_w + 0.006, 10.05 + dt, 0.42), (0, 1, 0), (0, 0, 1), (1, 0, 0)),
                     [(0.0, 0.0), (0.022, 0.0), (0.022, 0.03), (0.0, 0.03)], 8, "steel")
    out += tube(WORLD, [(s_w + 0.24, 10.05, 0.70), (s_w + 0.24, 10.05, 0.48), (s_w + 0.17, 10.05, 0.40), (s_w, 10.05, 0.40)], 0.018, 8, "steel")
    out += tube(WORLD, [(9.08, YN - 0.009, 0.18), (9.08, YN - 0.07, 0.18), (9.08, YN - 0.07, 0.42)], 0.007, 6, "steel")
    out += tube(WORLD, [(WC_S[1] - 0.06, YN - 0.06, FLOOR), (WC_S[1] - 0.06, YN - 0.06, CEIL)], 0.035, 10, "iron")
    for z in (0.6, 1.6, 2.6):
        out += lathe(Frame((WC_S[1] - 0.06, YN - 0.06, z)), [(0.0, 0.0), (0.045, 0.0), (0.045, 0.03), (0.0, 0.03)], 10, "steel")
    frw = Frame((WC_S[0] + 0.009, 10.30, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    emit(out, card(frw, 0.10, 0.38, 1.40, 1.58, 0.003, "wash_hands", (1.0, 0.0, 0.0)))
    return out


def door_plaques():
    """RESTROOM plaque over the WC door (corridor side). The EMPLOYEES ONLY plaque on P2 is in the hall kit."""
    out = []
    zt = door_top("wc") + 0.065
    frc = Frame((9.18, 8.42 - WT / 2, 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
    out += cbox(frc, -0.13, 0.13, 0.0, 0.006, zt, zt + 0.085, "steel", grain="x")
    emit(out, card(frc, -0.125, 0.125, zt + 0.004, zt + 0.081, 0.0065, "restroom", (0.0, -1.0, 0.0)))
    return out


def cooler_faces():
    return B.cooler_faces()


def boh_fixtures():
    out, L = B.boh_fixtures()
    # kitchen task light under the prep shelf (static)
    L.append(LT("boh_task_prep", "SPOT", ((PREP[0] + PREP[1]) / 2, YS + 0.22, 1.70), (0.96, 0.99, 1.0), 1.5, 2.2, 2.0,
                aim=(0.0, 0.25, -1.0), cone=(84.0, 60.0), flags=("not_in_reflection",)))
    return out, L


def boh_lights():
    out = []
    for l in boh_fixtures()[1]:
        if l["kind"] == "boh_task_prep":
            out.append(dict(l, time=0xFFFFFF))
            continue
        out.append(dict(l, time=DAY_HOURS))
        out.append(dict(l, intensity=round(l["intensity"] * 0.55, 3), time=NIGHT_HOURS))
    return out


def boh_faces():
    f, _ = partition_faces()
    f += finishes()
    f += boh_fixtures()[0]
    for fn in (kitchen_faces, storage_faces, corridor_faces, staff_entry_faces, backroom_faces, office_faces, wc_faces,
               cooler_faces, door_plaques):
        f += fn()
    out = []
    for x in f:
        if x is None:
            continue
        if x["mat"] not in _REMAP:
            raise KeyError(("material not in BOH_MATS", x["mat"]))
        out.append(dict(x, mat=_REMAP[x["mat"]]))
    return out


def boh_collision():
    _, col = partition_faces()
    col += kitchen_collision()
    col += [((STOCK_RACK[0], STOCK_RACK[1], STOCK_RACK[2], STOCK_RACK[3], FLOOR, 1.83), "METAL_SOLID_MEDIUM"),
            ((4.92, 5.56, 9.08, 10.32, FLOOR, 0.90), "WOOD_SOLID_MEDIUM"),
            ((2.15, 3.75, 9.83, 10.68, 0.70, 0.76), "WOOD_SOLID_MEDIUM"),
            ((0.70, 1.30, 10.80, 11.38, FLOOR, 0.62), "WOOD_SOLID_MEDIUM"),
            ((CRED[0], CRED[1], CRED[2], CRED[3], FLOOR, CRED_TOP), "WOOD_SOLID_MEDIUM")]
    return col


# ---------------------------------------------------------------- vanilla (archetype names only), z = bottom height
# ---- 0.2.9 stock on the (previously empty) vanilla steel shelving: deck tops measured on the models' HIGH LOD
#      prop_shelves_01 decks 0.08 / 0.74 / 1.31 m (clear 0.57 / 0.47 / 0.46), prop_shelves_02 decks 0.08 / 0.96 m;
#      the middle upright of both models is at x = 0 -> nothing crosses it. (name, dx along the shelf, dt, deck, yaw)
SHELF_DECKS = {"prop_shelves_01": (0.08, 0.74, 1.31), "prop_shelves_02": (0.08, 0.96)}
STOCK_A = [  # dry goods + paper, storage NE wall (prop_shelves_01 at s 11.75)
    ("prop_cardbordbox_03a", -0.90, 0.0, 0, 90.0), ("v_ret_247_flour", -0.35, -0.06, 0, 8.0),
    ("v_ret_247_flour", -0.13, 0.04, 0, -6.0), ("prop_cardbordbox_02a", 0.40, 0.0, 0, 5.0), ("v_ind_cfbox2", 1.00, 0.05, 0, 0.0),
    ("prop_paper_box_01", -1.05, 0.0, 1, 90.0), ("v_ind_cfbox", -0.55, 0.05, 1, 10.0), ("v_res_tt_can01", -0.30, -0.15, 1, 0.0),
    ("v_res_tt_can02", -0.22, -0.12, 1, 0.0), ("v_res_tt_can01", -0.26, -0.03, 1, 0.0), ("v_ind_cs_bottle", 0.30, 0.05, 1, 0.0),
    ("v_ind_cs_bottle", 0.55, 0.0, 1, 15.0), ("v_ind_cs_bottle", 0.80, 0.06, 1, -10.0), ("v_ret_gc_box2", 1.10, 0.0, 1, 5.0),
    ("prop_metalfoodjar_01", -1.20, -0.05, 2, 0.0), ("prop_metalfoodjar_01", -1.00, 0.0, 2, 0.0),
    ("prop_metalfoodjar_01", -0.80, -0.07, 2, 0.0), ("prop_pizza_box_02", -0.40, 0.0, 2, 0.0),
    ("v_ind_cs_tray01", 0.45, 0.0, 2, 0.0), ("v_res_foodjarb", 1.00, -0.05, 2, 0.0), ("v_res_foodjarb", 1.20, 0.02, 2, 0.0)]
STOCK_B = [  # bulk boxes, storage NE wall east (prop_shelves_02 at s 14.65)
    ("prop_cardbordbox_03a", -0.92, 0.0, 0, 90.0), ("prop_paper_box_01", -0.25, 0.0, 0, 0.0),
    ("prop_paper_box_01", -0.25, 0.02, 0, 0.0, 0.364), ("v_ind_cfbox2", 0.60, 0.05, 0, 0.0), ("v_ind_cfbox", 1.10, 0.0, 0, -15.0),
    ("prop_cardbordbox_02a", -0.95, 0.0, 1, 4.0), ("v_ret_247_flour", -0.42, -0.05, 1, 0.0), ("v_ret_247_flour", -0.18, 0.03, 1, 12.0),
    ("v_ret_247_flour", -0.32, -0.01, 1, 80.0, 0.27), ("v_ind_cs_tray01", 0.55, 0.0, 1, 0.0), ("v_ret_gc_box2", 1.15, 0.0, 1, -5.0)]
STOCK_C = [  # paper goods / cleaning, storage south rack (prop_shelves_01 at s 14.40, facing the aisle)
    ("prop_toilet_roll_02", -1.15, 0.0, 0, 90.0), ("prop_toilet_roll_02", -0.90, 0.03, 0, 80.0), ("v_ind_cfbox2", -0.30, 0.0, 0, 0.0),
    ("prop_cardbordbox_02a", 0.45, 0.0, 0, -3.0), ("v_ind_cfbox", 1.05, 0.05, 0, 20.0),
    ("v_ind_cs_bottle", -1.12, 0.0, 1, 0.0), ("v_ind_cs_bottle", -0.86, 0.04, 1, 30.0), ("v_ret_ta_spray", -0.62, -0.05, 1, 0.0),
    ("prop_paper_box_01", -0.25, 0.0, 1, 0.0), ("prop_pizza_box_02", 0.50, 0.0, 1, 3.0), ("prop_pizza_box_02", 0.52, 0.01, 1, -4.0, 0.09),
    ("prop_pizza_box_02", 0.49, 0.0, 1, 8.0, 0.18), ("v_ind_cfbox", 1.10, 0.0, 1, 0.0),
    ("v_res_tt_can02", -1.15, -0.10, 2, 0.0), ("v_res_tt_can02", -1.06, -0.08, 2, 0.0), ("v_res_tt_can01", -1.10, 0.02, 2, 0.0),
    ("v_ret_gc_box2", -0.55, 0.0, 2, 0.0), ("v_ind_cs_tray01", 0.45, 0.0, 2, 0.0), ("prop_metalfoodjar_01", 1.05, 0.0, 2, 0.0),
    ("prop_metalfoodjar_01", 1.25, -0.04, 2, 0.0)]


def shelf_stock():
    out = []
    for (model, s0, t0, yaw0), items in ((("prop_shelves_01", 11.75, 11.006, 0.0), STOCK_A),
                                         (("prop_shelves_02", 14.65, 11.006, 0.0), STOCK_B),
                                         (("prop_shelves_01", 14.40, 9.074, 180.0), STOCK_C)):
        sg = 1.0 if yaw0 == 0.0 else -1.0                     # model +x along +s (yaw 0) or -s (yaw 180)
        decks = SHELF_DECKS[model]
        for it in items:
            name, dx, dt, deck, yaw = it[:5]
            dz = it[5] if len(it) > 5 else 0.0
            out.append((name, s0 + sg * dx, t0 + sg * dt, FLOOR + decks[deck] + dz, yaw0 + yaw))
    return out


def boh_vanilla():
    out = kitchen_vanilla()
    # ---- storage (v0.2.8 positions, fixes from the layout audit)
    out.append(_against("prop_shelves_01", (11.75, YN), (0.0, -1.0)))
    out.append(_against("prop_shelves_02", (14.65, YN), (0.0, -1.0)))
    out.append(_against("prop_shelves_01", (14.40, 8.66), (0.0, 1.0)))
    out += [("prop_boxpile_01a", 12.15, 6.45, FLOOR, 90.0),
            ("prop_cardbordbox_03a", 12.25, 8.25, FLOOR, -8.0), ("prop_cardbordbox_02a", 12.23, 8.22, FLOOR + 0.514, 20.0),
            ("prop_cs_trolley_01", 15.35, 10.05, FLOOR, 0.0),
            ("prop_paper_box_01", 11.05, 9.85, FLOOR, 30.0), ("prop_paper_box_01", 11.08, 9.89, FLOOR + 0.364, 5.0),
            ("v_ind_cfbox2", 13.05, 10.05, FLOOR, 0.0), ("v_ind_cfbox", 13.62, 10.15, FLOOR, 40.0)]
    out += [("prop_food_bin_01", 11.80, 5.45, FLOOR, 180.0), ("prop_food_bin_02", 12.42, 5.45, FLOOR, 175.0),
            ]
    out += shelf_stock()
    # ---- walk-in cooler
    out.append(_against("v_ind_cf_shelf", (XE - 0.009, 6.80), (-1.0, 0.0)))
    out.append(_against("prop_ff_shelves_01", (14.10, 8.54), (0.0, -1.0)))
    out += [("prop_fruit_plas_crate_01", 13.30, 6.58, FLOOR, 5.0), ("prop_fruit_plas_crate_01", 13.32, 6.60, FLOOR + 0.36, -4.0),
            ("v_ind_cf_crate2", 13.35, 7.34, FLOOR, 0.0), ("v_ind_cf_crate2", 13.36, 7.33, FLOOR + 0.40, 4.0)]   # 0.2.9 audit: no corner overlaps
    # ---- cleaning corner at the staff entry (as v0.2.8) + corridor extinguisher + time clock
    out += [("v_serv_bktmop_h", -2.30, 7.42, FLOOR, 8.0), ("prop_tool_broom", -1.85, 7.17, FLOOR, 0.0),
            ("v_serv_wetfloorsn", -1.45, 7.38, FLOOR, 22.0), ("v_ind_cs_spray", -2.66, 7.25, FLOOR, 40.0)]
    out.append(("prop_fire_exting_1a", 6.10, 8.36 - 0.13, FLOOR, wall_yaw((0.0, -1.0))))
    out.append(_on_wall("v_ind_tor_clockincard", (1.30, 8.42 - WT / 2), (0.0, -1.0), 0.62))
    # ---- staff entry
    out.append(_on_wall("prop_coathook_01", (0.54, 9.85), (-1.0, 0.0), 1.70))
    out.append(("v_club_roc_jacket1", 0.54 - 0.08, 9.75, 1.72 - 0.866, wall_yaw((-1.0, 0.0))))
    out.append(_against("prop_shelves_02", (-0.92, YN), (0.0, -1.0)))
    out += [("prop_bin_07a", -0.10, 7.55, FLOOR, 15.0), ("prop_sacktruck_02a", -0.20, 9.00, FLOOR, 200.0)]
    # ---- back room
    out += [("v_res_fa_chair01", 2.40, 9.72, FLOOR, wall_yaw((0.0, 1.0)) + 8.0), ("v_res_fa_chair01", 3.50, 9.74, FLOOR, wall_yaw((0.0, 1.0)) - 6.0),
            ("v_res_fa_chair01", 2.40, 10.95, FLOOR, wall_yaw((0.0, -1.0)) + 5.0), ("v_ret_gc_chair02", 3.50, 10.92, FLOOR, wall_yaw((0.0, -1.0)) - 9.0)]
    out += [("v_res_mmug", 2.70, 10.10, 0.76, 30.0), ("v_res_mp_ashtraya", 3.30, 10.40, 0.76, 0.0),
            ("prop_cs_paper_cup", 3.05, 10.05, 0.76, 0.0), ("prop_pizza_box_02", 2.55, 10.42, 0.76, 15.0)]
    out.append(_against("prop_fridge_03", (5.54, 10.95), (-1.0, 0.0)))
    out += [("prop_micro_01", 5.20, 9.45, 0.90, wall_yaw((-1.0, 0.0))), ("prop_coffee_mac_02", 5.25, 10.05, 0.90, wall_yaw((-1.0, 0.0))),
            ("v_res_mmug", 5.05, 9.85, 0.90, 0.0), ("v_res_mmug", 5.08, 9.95, 0.90, 70.0)]
    out.append(("prop_tv_01", 1.08, 11.10, 0.62, wall_yaw((0.55, -0.83))))
    # ---- office (re-planned)
    out.append(_against("prop_office_desk_01", (DESK_S, YN), (0.0, -1.0), gap=0.06))
    out += [("v_res_tre_officechair", DESK_S, 10.25, FLOOR, wall_yaw((0.0, 1.0)) + 12.0),
            ("prop_monitor_03b", 6.30, 11.12, 0.733, wall_yaw((0.0, -1.0)) + 8.0),
            ("prop_keyboard_01a", 6.40, 10.84, 0.733, wall_yaw((0.0, -1.0))),
            ("prop_cd_folder_pile1", 5.98, 10.80, 0.733, 0.0), ("prop_cs_documents_01", 6.85, 10.82, 0.733, 15.0),
            ("prop_office_phone_tnt", 7.02, 11.14, 0.733, wall_yaw((0.0, -1.0)) - 20.0),
            ("prop_inout_tray_01", 7.25, 10.85, 0.733, 0.0), ("v_res_desklamp", 7.36, 11.20, 0.733, 0.0)]
    out.append(_against("v_med_cor_filingcab", (8.24, FILECAB_T), (-1.0, 0.0)))
    out.append(_on_wall("prop_coathook_01", (8.24, 9.05), (-1.0, 0.0), 1.70))
    out.append(("v_club_roc_jacket2", 8.24 - 0.08, 8.95, 1.72 - 0.774, wall_yaw((-1.0, 0.0))))
    out.append(("v_ret_csr_bin", 7.95, 10.63, FLOOR, 0.0))
    out.append(_on_wall("prop_fib_clipboard", (5.66, 9.65), (1.0, 0.0), 1.30))
    out += [("prop_cs_photoframe_01", 5.80, 9.30, CRED_TOP, wall_yaw((1.0, 0.0)) + 10.0),
            ("v_res_mp_ashtraya", 5.85, 9.60, CRED_TOP, 0.0)]
    out.append(office_switch())
    # ---- staff WC
    out.append(_against("prop_toilet_01", (9.30, YN - 0.009), (0.0, -1.0)))
    out.append(_against("prop_sink_06", (8.36 + 0.009, 10.05), (1.0, 0.0)))
    out.append(_on_wall("prop_toilet_roll_02", (9.94 - 0.009, 10.90), (-1.0, 0.0), 0.75))
    out.append(("prop_toilet_brush_01", 9.75, 11.20, FLOOR + 0.004, 0.0))
    out.append(_on_wall("prop_handdry_01", (9.94 - 0.009, 10.00), (-1.0, 0.0), 1.30))
    out.append(_on_wall("prop_soap_disp_01", (8.36 + 0.009, 9.72), (1.0, 0.0), 1.15))
    out.append(("v_ret_csr_bin", 8.62, 10.70, FLOOR + 0.004, 0.0))
    out.append(_on_wall("v_serv_metro_walllightcage", (WC_LIGHT[0], WC_LIGHT[1]), (0.0, -1.0), WC_LIGHT[2] - 0.19))
    return out


OFFICE_SWITCH = (6.55, 8.48 + 0.0, 1.16)  # After Hours switch in the office, P3 office face, west of the door


def office_switch():
    """v_serv_switch_2 on the office side of P3 (faces +t): model +x is its front."""
    sw = VB["v_serv_switch_2"]
    s, t, z = OFFICE_SWITCH
    return ("v_serv_switch_2", s, t - sw[0][0], z + sw[0][2], 90.0)


CLEANING_OLD = B.CLEANING_OLD
