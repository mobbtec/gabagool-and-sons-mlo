# LONG PIG — v0.2.9 PREMIUM FINAL PASS (owner brief "PREMIUM FIVEM MLO FINAL PASS", 2026-11-02).
# Built on v0.2.8 (hall v0.2.7 + back of house). No change to the building, its openings or the facade. Adds:
#   * doors in the hall partitions: P1 hall <-> kitchen = wooden service door with a wired-glass vision panel
#     (v_ilev_cor_firedoor), P2 hall <-> staff corridor = steel staff door (v_ilev_roc_door1_l) + EMPLOYEES ONLY plaque;
#     back-of-house doors in gs_boh29_kit (staff room, storage, office = solid wood, WC = private wood door, cooler steel);
#   * AFTER HOURS: two MLO entity sets switched by the client (synced by the server):
#       lp_open   - drawable gs_ah_open (lit lenses + lights of the 11 public troffers, OPEN neon, flip card OPEN side out)
#                   + the dining chairs in place
#       lp_closed - drawable gs_ah_closed (CLOSED side out, night service lights) + chairs up on the tables, mop bucket
#     the base hall keeps the counter / queue troffers, cases, menus, soffit cans; the 11 public lenses are unlit in the base,
#     so with no set active (fallback) the hall simply looks closed;
#   * WORKING RESTAURANT props: receipt printer at the till, HALL LIGHTS label under the switch, interaction data for the
#     client (bell, printer, hood switch, ticket rail, office switch, hidden credenza compartment);
#   * kitchen / BOH rebuilt in gs_boh29_kit.
import math
import gs_v028_kit as K8
from gs_v028_kit import *                    # noqa: F401,F403
import gs_v027_kit as K7
from gs_v027_kit import _pbr
import gs_boh29_kit as B9
from gs_boh29_kit import uv8, card, box8, REG8

VERSION = "0.2.9-premium"
BOH = True
B9.register()                                # VB / MAT / door models again (the older kits may have been reloaded)
from gs_v027_kit import VB                   # noqa: E402  (the current shared dict)
MAT = V.MAT
V.REP.update({"lp8": 1.0, "troffer_off": 0.3})

SHADER_SPECS = list(K7.SHADER_SPECS)
SHADER_SPECS += [_pbr("lp8_atlas", "lp8_atlas", "lp_flat_n", "lp_matte_s", 10.0, 0.15),                  # 27 signs / labels / props
                 _pbr("lp5_troffer_off", "lp5_troffer", "lp_flat_n", "lp_matte_s", 24.0, 0.30)]       # 28 unlit prismatic lens
assert len(SHADER_SPECS) == len(MAT) == 29, (len(SHADER_SPECS), len(MAT))
BOH_SPECS = [SHADER_SPECS[MAT[m]] if m in MAT else B9.WOOD_SPEC for m in B9.BOH_MATS]

# ================================================================== 1. doors in the hall partitions (P1, P2)
SG.P1_DOOR = B9.P1_DOOR29                    # (-1.13, 0.05): 1.15 m fire-rated wood door + 2 x 1 cm
SG.P2_DOOR = (8.30, 9.22)                    # 0.90 m steel staff door + 2 x 1 cm
SG.DOOR_H = max(B9.door_top("kitchen"), B9.door_top("roc"))      # 2.35 m heads (leaves are 2.30 m)


def hall_doors():
    out = []
    arch, pos, yaw = B9.door_entity("kitchen", "t", (SG.P1_S[0] + SG.P1_S[1]) / 2, SG.P1_DOOR[0], SG.P1_DOOR[1])
    out.append(("gs_kitchen", arch, pos, yaw))
    arch, pos, yaw = B9.door_entity("roc", "s", (SG.P2_T[0] + SG.P2_T[1]) / 2, SG.P2_DOOR[0], SG.P2_DOOR[1])
    out.append(("gs_staff_p2", arch, pos, yaw))
    return out


def boh_doors():
    return B9.boh_doors()


def all_doors():
    return hall_doors() + boh_doors()


# ================================================================== 2. AFTER HOURS split of the hall lighting
PUBLIC_TROFFERS = [(0, 1), (4, 1), (8, 1), (-2, 4), (2, 4), (6, 4), (0, 6), (4, 6), (2, -1), (5, -1), (8, -1)]
_TROF = {(i, j): (ns, nt) for (i, j, ns, nt, lamp) in K6.TROFFERS}


def _public_rect(pt):
    for (i, j) in PUBLIC_TROFFERS:
        ns, nt = _TROF[(i, j)]
        if i * P - 1e-3 <= pt[0] <= (i + ns) * P + 1e-3 and j * P - 1e-3 <= pt[1] <= (j + nt) * P + 1e-3:
            return (i, j)
    return None


def _is_public_light(l):
    k = l["kind"]
    if k.startswith("troffer_lamp") or k == "ceiling_bounce":
        return _public_rect(l["pos"]) is not None
    return False


def hall_faces():
    out = []
    for f in K8.hall_faces():
        if f["mat"] == MAT["troffer"]:
            c = (sum(v[0] for v in f["v"]) / len(f["v"]), sum(v[1] for v in f["v"]) / len(f["v"]))
            if _public_rect(c) is not None and all(abs(v[2] - f["v"][0][2]) < 1e-4 for v in f["v"]) and f["v"][0][2] > CEIL - 0.05:
                f = dict(f, mat=MAT["troffer_off"])
        out.append(f)
    out += hall_detail_faces()
    return out


def lights():
    return [l for l in K8.lights() if not _is_public_light(l)]


def open_lights():
    return [l for l in K8.lights() if _is_public_light(l)] + [
        LT("open_neon_glow", "POINT", (SIGN["s"], SIGN["t"] + 0.05, SIGN["z"]), (1.0, 0.18, 0.12), 1.2, 1.6, 4.0,
           flags=("not_in_reflection", "no_specular"))]


def closed_lights():
    return [LT("ah_service_counter", "SPOT", (7.70, 5.00, CEIL - 0.25), (1.0, 0.86, 0.68), 2.2, 3.2, 6.0, cone=(70.0, 36.0),
               flags=("not_in_reflection",)),
            LT("ah_service_back", "SPOT", (9.40, 2.60, CEIL - 0.25), (1.0, 0.86, 0.68), 1.6, 3.0, 6.0, cone=(72.0, 40.0),
               flags=("not_in_reflection",)),
            LT("ah_night_hall", "POINT", (2.40, 3.40, CEIL - 0.35), (0.92, 0.95, 1.0), 0.35, 4.5, 2.0,
               flags=("not_in_reflection", "no_specular"))]


# ---------------------------------------------------------------- OPEN neon + flip card in W1 pane 1 (between blind and glass)
SIGN = dict(s=1.985, t=-1.405, z=1.95, w=0.62, h=0.248)
CARD = dict(s=1.985, t=-1.405, z=1.48, w=0.30, h=0.15)


def _sign_frame():
    # X = +s (reads left->right for a viewer on the street looking +t), Y = -t (towards the street)
    return Frame((SIGN["s"], SIGN["t"], 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))


def chains(fr, x, z_top, z_bot):
    return cbox(fr, x - 0.002, x + 0.002, -0.002, 0.002, z_bot, z_top, "lp8", grain="z")


def neon_faces(mat_neon):
    fr = _sign_frame()
    w, h, z = SIGN["w"], SIGN["h"], SIGN["z"]
    out = []
    out += box8(fr, -w / 2 - 0.012, w / 2 + 0.012, -0.010, 0.010, z - h / 2 - 0.012, z + h / 2 + 0.012, "black", mat="lp8")
    u0, v0, u1, v1 = uv8("open_neon")
    for y, hint, uu in ((0.0105, (0.0, -1.0, 0.0), (u0, u1)), (-0.0105, (0.0, 1.0, 0.0), (u0, u1))):
        vs = [fr.p(-w / 2, y, z - h / 2), fr.p(w / 2, y, z - h / 2), fr.p(w / 2, y, z + h / 2), fr.p(-w / 2, y, z + h / 2)]
        f = F(vs, "troffer", [(uu[0], v0), (uu[1], v0), (uu[1], v1), (uu[0], v1)], hint=hint)
        if f is not None:
            out.append(dict(f, mat=mat_neon))
    for x in (-w / 2 + 0.05, w / 2 - 0.05):
        out += chains(fr, x, 2.57, z + h / 2 + 0.012)
    return out


def flip_card_faces(out_key, in_key):
    """Hanging card: out_key faces the street (-t), in_key faces the room (+t)."""
    fr = Frame((CARD["s"], CARD["t"], 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
    fri = Frame((CARD["s"], CARD["t"], 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))      # reads +s... from inside
    w, h, z = CARD["w"], CARD["h"], CARD["z"]
    out = []
    out += box8(fr, -w / 2, w / 2, -0.002, 0.002, z, z + h, "paper", mat="lp8")
    emit(out, card(fr, -w / 2, w / 2, z, z + h, 0.0025, out_key, (0.0, -1.0, 0.0)))
    emit(out, card(fri, -w / 2, w / 2, z, z + h, 0.0025, in_key, (0.0, 1.0, 0.0)))
    for x in (-0.06, 0.06):
        out += chains(fr, x, SIGN["z"] - SIGN["h"] / 2 - 0.012, z + h)
    return out


OPEN_MATS = ["troffer", "neon8", "lp8"]
CLOSED_MATS = ["lp8"]


def open_faces():
    """gs_ah_open: lit lenses of the public troffers (4 mm under the unlit ones), OPEN neon, flip card OPEN side out."""
    out = []
    for f in K8.hall_faces():
        if f["mat"] != MAT["troffer"]:
            continue
        c = (sum(v[0] for v in f["v"]) / len(f["v"]), sum(v[1] for v in f["v"]) / len(f["v"]))
        if _public_rect(c) is not None and all(abs(v[2] - f["v"][0][2]) < 1e-4 for v in f["v"]) and f["v"][0][2] > CEIL - 0.05:
            out.append(dict(f, v=[(v[0], v[1], round(v[2] - 0.004, 5)) for v in f["v"]], mat="troffer"))
    out += neon_faces("neon8")
    out += flip_card_faces("open_card", "closed")
    return _remap(out, OPEN_MATS)


def closed_faces():
    return _remap(flip_card_faces("closed", "open_card"), CLOSED_MATS)


def _remap(faces, names):
    idx = {}
    for i, n in enumerate(names):
        idx[n] = i
        if n in MAT:
            idx[MAT[n]] = i
    out = []
    for f in faces:
        m = f["mat"]
        if m not in idx:
            raise KeyError(("material not in set drawable", m, names))
        out.append(dict(f, mat=idx[m]))
    return out


SET_SPECS = {
    "troffer": SHADER_SPECS[MAT["troffer"]],
    "neon8": ("emissive.sps", {"DiffuseSampler": "lp8_atlas"}, {"emissiveMultiplier": 2.4}, "lp8_neon"),
    "lp8": SHADER_SPECS[MAT["lp8"]],
}


def open_specs():
    return [SET_SPECS[n] for n in OPEN_MATS]


def closed_specs():
    return [SET_SPECS[n] for n in CLOSED_MATS]


# ---------------------------------------------------------------- dining chairs: in place (open) / up on the tables (closed)
CHAIR_NAMES = {"v_ret_gc_chair02", "bkr_prop_clubhouse_chair_01", "v_ret_fh_chair01", "hei_heist_din_chair_03"}
SEAT_H = 0.46                                  # seat surface above the chair's bottom (all four models are ordinary chairs)


def _is_dining_chair(e):
    n, s, t, zb, yaw = e
    return n in CHAIR_NAMES and zb < FLOOR + 0.01 and t < 6.94 and s < 6.0


def _tables():
    tabs = [(b, BANQ_T) for b in BANQ_TABLES] + list(CTABLES)
    return tabs


def chairs_open():
    return [e for e in K8.vanilla_props() if _is_dining_chair(e)]


def chairs_closed():
    """One chair per table goes up on the table (upside down, seat on the top), the others are pushed in."""
    out = []
    used = set()
    for (n, s, t, zb, yaw) in chairs_open():
        tab = min(_tables(), key=lambda q: (q[0] - s) ** 2 + (q[1] - t) ** 2)
        if tab not in used:
            used.add(tab)
            mn = VB[n][0]
            z_origin = ZT + 0.004 + (mn[2] + SEAT_H)                # flipped: local z -> -z, seat (local mn+SEAT_H) on the top
            ds, dt = s - tab[0], t - tab[1]
            L = math.hypot(ds, dt) or 1.0
            # seat on the table, 0.17 m towards the chair's own side; turned 180 deg so the backrest hangs over that edge
            out.append(("FLIP", n, (round(tab[0] + ds / L * 0.17, 4), round(tab[1] + dt / L * 0.17, 4), round(z_origin, 4)),
                        yaw + 180.0))
        else:
            ds, dt = tab[0] - s, tab[1] - t
            L = math.hypot(ds, dt) or 1.0
            out.append((n, s + ds / L * 0.18, t + dt / L * 0.18, zb, yaw))
    return out


def _quat_flip(yaw_deg):
    """Rotation = yaw about Z, then 180 deg about the model X axis -> (w, x, y, z)."""
    a = math.radians(yaw_deg) / 2
    qz = (math.cos(a), 0.0, 0.0, math.sin(a))
    qx = (0.0, 1.0, 0.0, 0.0)
    w1, x1, y1, z1 = qz
    w2, x2, y2, z2 = qx
    return (w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2)


def _ent(name, s, t, zb, yaw):
    mn = VB[name][0]
    return (name, (round(s, 4), round(t, 4), round(zb - mn[2], 4)), math.radians(yaw))


def set_entities():
    """-> {set_name: [(archetype, (s, t, z_origin), yaw_rad | quaternion (w, x, y, z))]}"""
    op = [("gs_ah_open", (0.0, 0.0, 0.0), 0.0)] + [_ent(*e) for e in chairs_open()]
    cl = [("gs_ah_closed", (0.0, 0.0, 0.0), 0.0)]
    for e in chairs_closed():
        if e[0] == "FLIP":
            _, n, pos, yaw = e
            cl.append((n, pos, _quat_flip(yaw)))
        else:
            cl.append(_ent(*e))
    cl += [_ent("v_serv_bktmop_h", 2.15, 4.55, FLOOR, 25.0), _ent("v_serv_wetfloorsn", 2.75, 4.25, FLOOR, -15.0)]
    return {"lp_open": op, "lp_closed": cl}


# ================================================================== 3. hall details (printer, plaque, switch label)
PRINTER = dict(s=7.76, t=4.90, z=1.02)
SWITCH_HALL = (6.86, 6.94, 1.16)               # existing v0.2.3 light switch (v_serv_switch_2) on the P2 hall face
BELL = (7.34, 0.02, 1.02 + 0.07)


def receipt_printer():
    out = []
    s, t, z = PRINTER["s"], PRINTER["t"], PRINTER["z"]
    out += cbox(WORLD, s - 0.10, s + 0.10, t - 0.085, t + 0.085, z, z + 0.13, "terrazzo", ch=0.012, grain="x")
    out += cbox(WORLD, s - 0.09, s + 0.06, t - 0.075, t + 0.075, z + 0.13, z + 0.145, "terrazzo", ch=0.01, grain="x")   # lid
    frf = Frame((s - 0.101, t + 0.085, 0.0), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))                  # face to -s
    emit(out, card(frf, 0.0, 0.17, z + 0.03, z + 0.115, 0.0, "printer", (-1.0, 0.0, 0.0)))
    out += cbox(WORLD, s - 0.135, s - 0.10, t - 0.03, t + 0.03, z + 0.105, z + 0.106, "terrazzo", grain="x")       # paper tongue
    return out


def p2_plaque():
    zt = SG.DOOR_H + 0.075 + 0.02
    sc = (SG.P2_DOOR[0] + SG.P2_DOOR[1]) / 2
    fr = Frame((sc, SG.P2_T[0], 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
    out = cbox(fr, -0.14, 0.14, 0.0, 0.006, zt, zt + 0.08, "steel", grain="x")
    emit(out, card(fr, -0.135, 0.135, zt + 0.004, zt + 0.076, 0.0065, "staff_only", (0.0, -1.0, 0.0)))
    return out


def switch_label():
    s, t, z = SWITCH_HALL
    fr = Frame((s, t, 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
    out = []
    emit(out, card(fr, -0.035, 0.035, z - 0.135, z - 0.07, 0.002, "switch_label", (0.0, -1.0, 0.0)))
    return out


def hall_detail_faces():
    return receipt_printer() + p2_plaque() + switch_label()


# ================================================================== 4. vanilla, collision, back of house
def vanilla_props():
    out = []
    for e in K7.vanilla_props():
        if (e[0], round(e[1], 2), round(e[2], 2)) in B9.CLEANING_OLD:
            continue
        if _is_dining_chair(e):
            continue                            # -> entity sets lp_open / lp_closed
        out.append(_audit_fix(e))
    return out + B9.boh_vanilla()


AUDIT_FIX = {("v_ret_gc_box2", 9.79, 2.11): (9.72, 2.11),
             ("prop_plant_int_04a", -2.5, 6.66): (-2.5, 6.64, 0.0)}     # plant leaves were inside partition P2


def _audit_fix(e):
    n, s, t, zb, yaw = e
    k = (n, round(s, 2), round(t, 2))
    if k in AUDIT_FIX:
        fx = AUDIT_FIX[k]
        s, t = fx[0], fx[1]
        yaw = fx[2] if len(fx) > 2 else yaw
    return (n, s, t, zb, yaw)


def vanilla_entities():
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        out.append(_ent(name, s, t, zb, yaw))
    for did, arch, pos, yaw in all_doors():
        out.append((arch, pos, yaw))
    return out


def collision_boxes():
    return K7.collision_boxes() + B9.boh_collision()


boh_faces = B9.boh_faces
boh_lights = B9.boh_lights
cpv_hall = K8.cpv_hall

# ================================================================== 5. data for the client scripts (MLO-local metres)
def interaction_data():
    sd = B9.SECRET_DOOR
    return {
        "switch_hall": SWITCH_HALL, "switch_office": B9.OFFICE_SWITCH, "bell": BELL,
        "printer": (PRINTER["s"] - 0.10, PRINTER["t"], PRINTER["z"] + 0.10),
        "printer_paper": (PRINTER["s"] - 0.14, PRINTER["t"], PRINTER["z"] + 0.106),
        "hood_switch": B9.HOOD_SWITCH, "hood_lamps": [(PG.XE - B9.HOOD_D + 0.29, t, 2.27) for t in B9.HOOD_LAMPS_T],
        "ticket_rail": (B9.TICKET_RAIL[0], B9.TICKET_RAIL[1], PG.YS + 0.045, B9.TICKET_RAIL[2]),
        "pickup_bell": (10.00, -0.50, 1.40),
        "secret_point": B9.SECRET_POINT, "secret_hinge": (sd["hinge"][0], sd["hinge"][1], sd["z0"]),
        "secret_width": sd["width"],
    }


CAM_VIEWS = dict(K8.CAM_VIEWS)
CAM_VIEWS.update({
    "GS29_KITCHEN": ((10.6, -0.6, 1.70), (14.5, 3.6, 1.10), "kitchen from the hall door: hot line, island, dish station"),
    "GS29_KITCHEN2": ((15.6, 4.3, 1.70), (11.0, 0.8, 1.05), "kitchen towards the hall door: rack, reach-ins, prep, hand sink"),
    "GS29_LINE": ((13.2, 0.2, 1.65), (16.0, 3.0, 1.30), "hot line under the hood: griddle, range, fryer"),
    "GS29_PREP": ((12.9, 1.2, 1.60), (12.9, -1.23, 1.20), "prep table, knife bar, task light, ticket rail"),
    "GS29_OFFICE": ((7.35, 8.8, 1.65), (6.0, 10.4, 0.70), "office: credenza (hidden compartment), desk, filing cabinet"),
    "GS29_SECRET": ((6.75, 9.5, 1.10), (5.9, 10.0, 0.40), "hidden compartment (credenza right bay)"),
    "GS29_DOORS_HALL": ((7.4, 3.6, 1.65), (9.6, 0.2, 1.20), "hall side: kitchen door (P1) behind the counter"),
    "GS29_P2": ((8.0, 4.6, 1.65), (8.76, 7.0, 1.60), "staff door P2 with EMPLOYEES ONLY"),
    "GS29_SIGN_OUT": ((1.98, -5.5, 1.55), (1.98, -1.4, 1.85), "OPEN neon + flip card from the street"),
    "GS29_STORAGE": ((10.6, 7.6, 1.65), (10.3, 9.6, 1.10), "storage stock rack with labelled cartons"),
})
