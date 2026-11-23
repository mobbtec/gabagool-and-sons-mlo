# LONG PIG — v0.2.5 STYLE RESET (docs/style_reset/*: "worn South Los Santos Italian-American deli, 1995-2001").
# Built on the v0.2.3 lobby kit (walls, ceiling, booths, banquettes, ledge, counters) — the v0.2.4 lounge is NOT used.
#   P0 removals: ATM, yellow drinks fridge, both big plants, candle sconces + picture light + casino-vault paintings,
#                beer neons on the glass (+ their spill lights), chalk menus, jukebox / red barrel chairs / rug / rail.
#   P0 move:     gumball machines -> outside on the NW pier, spawned client-side (client/exterior.lua, toggle in config).
#   Materials:   lp4_* (gs_15g): faded oxblood tile, aged cream paint, dull vinyl, worn laminates, aged checker, yellowed
#                ceiling, faded menus; wear decal map (lp4_decal_wear) placed where people actually walk, sit and touch.
#   Hero wall:   cashier back wall (P1) — upper supply shelf, letterboards, permit, grade card, calendar, schedule, phone.
#   Identity:    faded tricolore + family / shop-history photo wall on P2, cork community board at the entrance.
# Pure Python (face dicts); consumed by gs_20 (build) and gs_21 (preview) like the earlier kits.
import math
import gs_v023_kit as K3
import gs_v024_kit as K4                     # globe_pendant only (the lounge itself is not used)
from gs_v023_kit import *                    # noqa: F401,F403  (MAT, VB, LT, CORONA, cpv_hall, ROOM_TIMECYCLE, ...)
from gs_v023_kit import (V, PG, SG, WORLD, Frame, F, emit, cbox, prism, lathe, tube, FLOOR, CEIL, LT, CORONA, C_TUNGSTEN,
                         FILL_FLAGS, wall_yaw, VB, P, P1_S, P2_T, BACK_S, COUNTER_FRONT, BANQ, BANQ_TABLES, BANQ_T, ZT,
                         TABLE2, LEDGE, decal_quad)
from gs_v025_vb import VB_V025

VB.update(VB_V025)
V.MAT.update({"notice": 20})
V.REP.update({"notice": 1.0})
MAT = V.MAT


def _pbr(nm, d, n, s, falloff, inten=1.0, bump=1.0):
    return ("normal_spec.sps", {"DiffuseSampler": d, "BumpSampler": n, "SpecSampler": s},
            {"specularIntensityMult": inten, "specularFalloffMult": falloff, "specularFresnel": 0.97, "bumpiness": bump}, nm)


SHADER_SPECS = list(K3.SHADER_SPECS)
SHADER_SPECS[0] = _pbr("lp4_laminate_red", "lp4_laminate_red", "lp3_laminate_n", "lp3_laminate_s", 45.0, 0.55)
SHADER_SPECS[1] = _pbr("lp4_vinyl_red", "lp4_vinyl_red", "lp2_leather_n", "lp3_vinyl_s", 35.0, 0.7)
SHADER_SPECS[2] = _pbr("lp4_laminate_cream", "lp4_laminate_cream", "lp3_laminate_n", "lp3_laminate_s", 45.0, 0.55)
SHADER_SPECS[10] = _pbr("lp4_flag", "lp4_flag", "lp2_flag_n", "lp_matte_s", 8.0, 0.2)
SHADER_SPECS[13] = _pbr("lp4_tile_red", "lp4_tile_red", "lp3_tile_n", "lp3_tile_s", 90.0, 0.75)
SHADER_SPECS[14] = _pbr("lp4_tile_white", "lp4_tile_white", "lp3_tile_n", "lp3_tile_s", 90.0, 0.8)
SHADER_SPECS[16] = ("emissive.sps", {"DiffuseSampler": "lp4_menu"}, {"emissiveMultiplier": 1.05}, "lp4_menu")
SHADER_SPECS[17] = ("emissive.sps", {"DiffuseSampler": "lp4_troffer"}, {"emissiveMultiplier": 1.9}, "lp4_troffer")
SHADER_SPECS[18] = ("decal.sps", {"DiffuseSampler": "lp4_decal_wear"}, {}, "lp4_decal_wear")
SHADER_SPECS.append(_pbr("lp4_notices", "lp4_notices", "lp_flat_n", "lp_matte_s", 8.0, 0.12))          # 20 paper goods
assert len(SHADER_SPECS) == len(MAT)
# shell materials (gs_20): (diffuse, normal, spec, falloff, intensity)
SHELL_TEX = {"floor": ("lp4_floor_bw", "lp_floor_checker_n", "lp4_floor_s", 40.0, 0.6),
             "wall": ("lp4_paintbrick", "lp3_paintbrick_n", "lp3_paintbrick_s", 10.0, 0.35),
             "tile": ("lp4_tile_red", "lp3_tile_n", "lp3_tile_s", 90.0, 0.75),
             "ceil": ("lp4_ceiling_tile", "lp3_ceiling_tile_n", "lp_ceiling_tile_s", 6.0, 0.3)}

CAM_VIEWS = dict(K3.CAM_VIEWS)
CAM_VIEWS.update({
    "VJ": ((3.2, 1.5, 1.62), (9.9, 3.4, 2.0), "cashier back wall (hero)"),
    "VK": ((1.6, 4.4, 1.60), (1.0, 6.94, 1.6), "family photo wall + flag (P2)"),
    "VL": ((3.0, 2.0, 1.62), (6.4, -1.23, 1.6), "entrance pier: community board, grade card"),
    "VM": ((-1.2, 1.4, 1.62), (2.5, 3.3, 0.8), "centre tables from the entrance"),
})

# ================================================================== wall frames (Y = into the room, X = viewer's right)
def wall_frame(wall, u0=0.0):
    """Frame on a wall face; local x along the wall (viewer's right), y into the room, z up; origin at x = u0."""
    if wall == "P1":
        return Frame((P1_S[0], -u0, 0.0), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)), (-1.0, 0.0, 0.0)
    if wall == "P2":
        return Frame((u0, P2_T[0], 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)), (0.0, -1.0, 0.0)
    if wall == "SW":
        return Frame((-u0, PG.YS, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (0.0, 1.0, 0.0)
    if wall == "NW":
        return Frame((PG.XW, u0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)), (1.0, 0.0, 0.0)
    raise KeyError(wall)


def wall_u(wall, s, t):
    """Wall coordinate of a point (s, t) for wall_frame(wall) with u0 = 0."""
    return {"P1": -t, "P2": s, "SW": -s, "NW": t}[wall]


# notices atlas cells (gs_15g): 3 x 4 grid of 256 px cells on the left + 2 letterboards in the right column
NOTICE = {"permit": 0, "grade": 1, "calendar": 2, "schedule": 3, "cash_only": 4, "no_loiter": 5, "special": 6, "cork": 7,
          "shop_photo": 8, "espresso": 9, "clipping": 10, "we_card": 11}


def notice_uv(key):
    if key == "board_a":
        return (0.75, 0.5, 1.0, 1.0)
    if key == "board_b":
        return (0.75, 0.0, 1.0, 0.5)
    i = NOTICE[key]
    cx, cy = i % 3, i // 3
    return (cx / 4.0, 1.0 - (cy + 1) / 4.0, (cx + 1) / 4.0, 1.0 - cy / 4.0)


def notice(wall, s, t, z0, w, h, key, d=0.012, frame=None, fw=0.022, fd=0.016):
    """Paper / card / board on a wall, centred at (s, t), bottom at z0; optional frame ('black' | 'alu' | 'brown')."""
    out = []
    fr, n = wall_frame(wall)
    u = wall_u(wall, s, t)
    u0, v0, u1, v1 = notice_uv(key)
    dd = d + (fd * 0.5 if frame else 0.0)
    vs = [fr.p(u - w / 2, dd, z0), fr.p(u + w / 2, dd, z0), fr.p(u + w / 2, dd, z0 + h), fr.p(u - w / 2, dd, z0 + h)]
    emit(out, F(vs, "notice", [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], hint=n))
    if frame:
        m = {"black": "rubber", "alu": "steel", "brown": "walnut"}[frame]
        for (a0, a1, b0, b1) in ((u - w / 2 - fw, u + w / 2 + fw, z0 - fw, z0), (u - w / 2 - fw, u + w / 2 + fw, z0 + h, z0 + h + fw),
                                 (u - w / 2 - fw, u - w / 2, z0, z0 + h), (u + w / 2, u + w / 2 + fw, z0, z0 + h)):
            out += cbox(fr, a0, a1, d - 0.004, d + fd, b0, b1, m, ch=0.003, grain="x" if (b1 - b0) < (a1 - a0) else "z", skip=("-y",))
        out += cbox(fr, u - w / 2, u + w / 2, d - 0.004, d + 0.002, z0, z0 + h, m, grain="x", skip=("-y",))   # backing
    return out


# ================================================================== P1 cashier back wall (hero)
SHELF_Z = 2.44                       # just above the splashback cap: stays visible under the hanging menus
BRACKETS_T = (0.62, 2.20, 3.30, 4.95, 6.30)   # clear of the letterboards, the clock and the old wall shelf
SHELF_T = (0.25, 6.45)


def p1_wall_faces():
    out = []
    fr, n = wall_frame("P1")
    # upper supply shelf (laminate board, steel L-brackets)
    a, b = -SHELF_T[1], -SHELF_T[0]
    out += cbox(fr, a, b, 0.0, 0.30, SHELF_Z, SHELF_Z + 0.03, "walnut", ch=0.004, grain="x")
    out += cbox(fr, a, b, 0.296, 0.304, SHELF_Z - 0.012, SHELF_Z + 0.04, "steel", grain="x")             # lip
    for t in BRACKETS_T:
        u = -t
        out += cbox(fr, u - 0.012, u + 0.012, 0.0, 0.01, SHELF_Z - 0.18, SHELF_Z, "steel", grain="z")
        out += cbox(fr, u - 0.012, u + 0.012, 0.0, 0.26, SHELF_Z - 0.02, SHELF_Z, "steel", grain="y")
        out += tube(fr, [(u, 0.008, SHELF_Z - 0.16), (u, 0.22, SHELF_Z - 0.02)], 0.006, 6, "steel")
        for zz in (SHELF_Z - 0.15, SHELF_Z - 0.05):                                                  # screw heads
            out += lathe(fr.child(u, 0.011, zz).tilt_x(-math.pi / 2), [(0.0, 0.0), (0.006, 0.0), (0.006, 0.003), (0.0, 0.004)], 6, "steel")
    # letterboards replacing the chalk menus (aluminium frame) + paper goods
    out += notice("P1", P1_S[0], 1.30, 1.40, 0.54, 0.98, "board_a", d=0.024, frame="alu", fw=0.025)
    out += notice("P1", P1_S[0], 5.40, 1.40, 0.54, 0.98, "board_b", d=0.024, frame="alu", fw=0.025)
    out += notice("P1", P1_S[0], 4.62, 1.40, 0.27, 0.27, "permit", frame="black")
    out += notice("P1", P1_S[0], 0.44, 1.60, 0.30, 0.30, "calendar", d=0.010)
    out += notice("P1", P1_S[0], 6.22, 1.80, 0.25, 0.25, "schedule", d=0.010)
    out += notice("P1", P1_S[0], 2.02, 1.48, 0.25, 0.25, "special", d=0.010)
    out += notice("P1", P1_S[0], 2.02, 1.98, 0.22, 0.22, "we_card", d=0.010)
    out += wall_phone(6.24, 1.30)
    return out


def wall_phone(t, z0):
    """Beige 1990s wall phone: base plate, handset in the cradle, coiled cord."""
    out = []
    fr, n = wall_frame("P1")
    u = -t
    out += cbox(fr, u - 0.055, u + 0.055, 0.0, 0.05, z0, z0 + 0.20, "terrazzo", ch=0.008, grain="z")
    out += cbox(fr, u - 0.03, u + 0.03, 0.05, 0.085, z0 + 0.02, z0 + 0.19, "terrazzo", ch=0.012, grain="z")   # handset
    out += cbox(fr, u - 0.034, u + 0.034, 0.05, 0.09, z0 + 0.16, z0 + 0.20, "terrazzo", ch=0.012, grain="x")  # ear cap
    out += cbox(fr, u - 0.034, u + 0.034, 0.05, 0.09, z0 + 0.00, z0 + 0.04, "terrazzo", ch=0.012, grain="x")  # mouth cap
    pts = []
    for k in range(57):                                                                                         # coiled cord
        a = k * 0.55
        pts.append((u + 0.032 + 0.012 * math.cos(a), 0.06 + 0.012 * math.sin(a), z0 - 0.005 - 0.004 * k))
    out += tube(fr, pts, 0.0028, 4, "terrazzo")
    return out


def p1_vanilla():
    out = []
    zs = SHELF_Z + 0.03
    yaw = wall_yaw((-1.0, 0.0))                       # fronts towards the customers (-s)
    s_sh = P1_S[0] - 0.15
    for t, nmax in ((0.40, 7), (0.53, 5)):           # nested paper-cup sleeves
        for k in range(nmax):
            out.append(("prop_cs_paper_cup", s_sh, t, zs + 0.021 * k, 0.0))
    out += [("prop_food_napkin_02", P1_S[0] - 0.02, 0.82, zs, yaw), ("prop_food_napkin_02", P1_S[0] - 0.02, 1.02, zs, yaw + 4.0)]
    out += [("prop_paper_bag_small", s_sh, 1.30, zs, 90.0), ("prop_paper_bag_small", s_sh, 1.40, zs, 86.0),
            ("prop_paper_bag_small", s_sh, 1.50, zs, 93.0)]
    out += [("v_ret_gc_box2", s_sh, 1.95, zs, 0.0), ("v_ret_gc_box2", s_sh, 2.27, zs, 7.0), ("v_ret_gc_box2", s_sh, 2.11, zs + 0.27, 41.0),
            ("prop_beer_box_01", s_sh, 2.85, zs, 90.0), ("v_ret_ml_6bottles", P1_S[0] - 0.06, 3.35, zs, yaw)]
    for k, t in enumerate((3.70, 3.79, 3.88, 3.97, 4.06)):                                                   # soda overstock
        out.append(("v_res_tt_can03", P1_S[0] - 0.08, t, zs, 17.0 * k))
    for k, t in enumerate((3.72, 3.84, 3.96)):
        out.append(("v_res_tt_can03", P1_S[0] - 0.19, t, zs, 40.0 * k))
    out += [("v_ret_gc_box2", s_sh, 4.95, zs, -4.0), ("v_res_foodjarb", s_sh, 5.45, zs, 0.0), ("v_res_foodjarc", s_sh, 5.68, zs, 0.0),
            ("prop_food_napkin_02", P1_S[0] - 0.02, 6.05, zs, yaw), ("prop_food_napkin_02", P1_S[0] - 0.02, 6.25, zs, yaw - 3.0)]
    # clock above the permit, plastic tray stack on the back counter, family photo by the till side of the wall
    ck = VB["v_ret_gc_clock"]
    out.append(("v_ret_gc_clock", P1_S[0] - ck[1][1] - 0.02, 4.62, 1.92, yaw))
    for k in range(5):
        out.append(("prop_food_tray_01", P1_S[0] - 0.24, 1.30, 0.92 + 0.016 * k, 90.0 + (k % 2) * 2.0))
    out.append(("prop_cs_photoframe_01", P1_S[0] - 0.03, 6.40, 0.921, yaw - 12.0))
    return out


# ================================================================== P2 dining wall: faded flag + family / shop history
def p2_flag(s, z_b):
    """V.wall_flag (built on the SW wall) mirrored onto P2: t' = P2 - (t - YS); winding reversed to keep the normals."""
    out = []
    for f in V.wall_flag(s, z_b, angle=math.radians(28), pole=0.85, hoist=(0.08, 0.46), fly=0.56):
        vs = [(x, P2_T[0] - (y - PG.YS), z) for (x, y, z) in f["v"]]
        out.append(dict(f, v=vs[::-1], uv=f["uv"][::-1]))
    return out


def p2_wall_faces():
    out = []
    out += p2_flag(-1.20, 1.72)
    out += notice("P2", 0.25, P2_T[0], 1.70, 0.26, 0.26, "shop_photo", d=0.006, frame="black")
    out += notice("P2", 2.75, P2_T[0], 1.30, 0.46, 0.46, "espresso", d=0.006, frame="brown", fw=0.03)
    out += notice("P2", 4.50, P2_T[0], 1.38, 0.26, 0.26, "clipping", d=0.006, frame="black")
    return out


def p2_vanilla():
    out = []
    zw = P2_T[0]
    yaw = wall_yaw((0.0, -1.0))

    def on_p2(name, s, zb):
        b = VB[name]
        return (name, s, zw - (b[1][1] + 0.003), zb, yaw)
    # family cluster: mixed sizes, uneven spacing (photos collected over 20 years)
    out += [on_p2("prop_ped_pic_03", -0.38, 1.44), on_p2("prop_ped_pic_01_sm", -0.05, 1.62), on_p2("prop_ped_pic_06", 0.62, 1.30),
            on_p2("prop_ped_pic_08_sm", 0.95, 1.52), on_p2("prop_ped_pic_04", 0.66, 1.76), on_p2("prop_ped_pic_05_sm", 1.20, 1.36),
            on_p2("prop_ped_pic_03_sm", -0.30, 1.90)]
    out += [on_p2("v_ret_gc_clock", 1.80, 2.18)]
    out += [on_p2("prop_ped_pic_06_sm", 4.12, 1.47), on_p2("prop_ped_pic_08", 4.88, 1.42)]
    return out


# ================================================================== SW piers: entrance board, grade card, removed sconce
PIER_A = (PG.P_SW[0] + PG.W1["s"][0] - PG.CASING_W) / 2       # between the chamfer and W1
PIER_B = 6.35                                                   # between W1 and the counter


def sw_wall_faces():
    out = []
    out += notice("SW", PIER_B, PG.YS, 1.22, 0.62, 0.62, "cork", d=0.006, frame="alu", fw=0.022)
    out += notice("SW", 5.86, PG.YS, 1.48, 0.20, 0.20, "grade", d=0.010)
    out += notice("SW", PIER_A, PG.YS, 1.20, 0.28, 0.28, "no_loiter", d=0.010)
    return out


def sw_vanilla():
    wl = VB["v_med_cor_walllight"]
    return [("v_med_cor_walllight", PIER_B, PG.YS + wl[1][1] + 0.004, 1.98, wall_yaw((0.0, 1.0)))]


# ================================================================== centre: two utility tables, mismatched chairs
CTABLES = [(0.85, 3.05), (3.35, 3.05)]
CT_SIZE = 0.76


def centre_faces():
    out = []
    for sc, tc in CTABLES:
        out += K3.table2(sc, tc, size=CT_SIZE)
        out += K4.globe_pendant(sc, tc)
    return out


def centre_vanilla():
    out = []
    (a, at), (b, bt) = CTABLES
    out += [("v_ret_gc_chair02", a - 0.66, at + 0.02, FLOOR, wall_yaw((1.0, 0.0)) + 6.0),
            ("bkr_prop_clubhouse_chair_01", a + 0.02, at + 0.64, FLOOR, wall_yaw((0.0, -1.0)) - 4.0),
            ("v_ret_fh_chair01", a + 0.66, at - 0.04, FLOOR, wall_yaw((-1.0, 0.0)) + 9.0),
            ("hei_heist_din_chair_03", b - 0.02, bt + 0.64, FLOOR, wall_yaw((0.0, -1.0)) + 3.0),
            ("v_ret_gc_chair02", b + 0.66, bt + 0.03, FLOOR, wall_yaw((-1.0, 0.0)) - 7.0)]
    out += [("v_res_mp_ashtraya", a - 0.12, at + 0.10, ZT, 0.0), ("prop_food_ketchup", a + 0.20, at + 0.22, ZT, 0.0),
            ("prop_cs_paper_cup", a + 0.08, at - 0.18, ZT, 0.0),
            ("prop_bar_napkindisp", b + 0.18, bt + 0.20, ZT, 90.0)]                              # 2nd table nearly clean
    return out


def centre_collision():
    out = []
    for sc, tc in CTABLES:
        h = CT_SIZE / 2
        out.append(((sc - h, sc + h, tc - h, tc + h, ZT - 0.05, ZT), "WOOD_SOLID_MEDIUM"))
        out.append(((sc - 0.04, sc + 0.04, tc - 0.04, tc + 0.04, FLOOR, ZT - 0.05), "METAL_SOLID_SMALL"))
    return out


# ================================================================== counter: CASH ONLY tent card at the till
def counter_faces():
    out = []
    c = (7.30, 4.66, 1.02)                                                           # on the counter top, next to the till
    w, h, ang = 0.13, 0.10, math.radians(68)
    for sg in (-1.0, 1.0):
        n = (sg * math.cos(ang), 0.0, math.sin(ang))
        dz = h * math.sin(ang)
        ds = -sg * h * math.cos(ang)
        p0 = (c[0] + sg * 0.035, c[1] - w / 2, c[2])
        vs = [p0, (p0[0], p0[1] + w, p0[2]), (p0[0] + ds, p0[1] + w, p0[2] + dz), (p0[0] + ds, p0[1], p0[2] + dz)]
        u0, v0, u1, v1 = notice_uv("cash_only")
        uv = [(u1, v0), (u0, v0), (u0, v1), (u1, v1)] if sg < 0 else [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        emit(out, F(vs, "notice", uv, hint=(sg * math.sin(ang), 0.0, math.cos(ang))))
    return out


# ================================================================== wear / damage map (lp4_decal_wear, 4 x 2 cells)
def dcell(i):
    cx, cy = i % 4, i // 4
    return (cx / 4.0, 1.0 - (cy + 1) / 2.0, (cx + 1) / 4.0, 1.0 - cy / 2.0)    # (u0, v_bottom, u1, v_top)


GRIME, TRAFFIC, DRIPS, SCUFF, WATER, PATCH, GHOST, TAPE = range(8)
FLOOR_WEAR = [(-0.55, 1.20, 0.90), (0.6, 1.55, 0.80), (2.3, 1.35, 0.75), (4.3, 1.45, 0.70), (6.35, 1.6, 0.70), (6.35, 3.7, 0.70),
              (6.45, 5.1, 0.65), (8.6, 2.0, 0.55), (8.6, 4.8, 0.55)]                 # entrance -> queue -> register, staff aisle
SCUFFS = [(6.78, 1.2), (6.78, 3.3), (6.78, 5.3), (2.1, 0.42), (4.3, 0.42), (-0.6, 4.6), (0.3, 5.15), (2.6, 5.2)]
WATER_TILES = [(3, 7), (9, 3)]


def decal_faces():
    out = []
    z = FLOOR + 0.002
    # wall-base grime along every full wall run (in front of the tile)
    u0, vb, u1, vt = dcell(GRIME)
    for fr, runs, _ in V.wall_runs():
        for a, b, kind in runs:
            if kind != "full" or b - a < 0.4:
                continue
            u = a + 0.1
            while u < b - 0.3:
                L = min(1.6, b - u - 0.1)
                emit(out, decal_quad(fr.p(u, 0.0155, FLOOR + 0.10), V.mul(fr.X, L), (0.0, 0.0, 0.26), (u0, vb, u1, vt)))
                u += L + 0.9
    for (s, t, r) in FLOOR_WEAR:
        emit(out, decal_quad((s - r, t - r, z), (2 * r, 0.0, 0.0), (0.0, 2 * r, 0.0), dcell(TRAFFIC)))
    for (s, t) in SCUFFS:
        emit(out, decal_quad((s - 0.30, t - 0.30, z + 0.0005), (0.6, 0.0, 0.0), (0.0, 0.6, 0.0), dcell(SCUFF)))
    for (i, j) in WATER_TILES:                                                    # two stained ceiling tiles (facing down)
        sc, tc = (i + 0.5) * P, (j + 0.5) * P
        q = 0.27
        emit(out, decal_quad((sc - q, tc + q, CEIL - 0.003), (2 * q, 0.0, 0.0), (0.0, -2 * q, 0.0), dcell(WATER)))
    # drips under the W2 ledge (spilled drinks), plaster patches, the ghost of the removed candle sconce, tape repair
    fr, n = wall_frame("NW")
    emit(out, decal_quad(fr.p(4.40, 0.0175, 0.12), (0.0, 0.32, 0.0), (0.0, 0.0, 0.42), dcell(DRIPS)))
    fr, n = wall_frame("P2")
    emit(out, decal_quad(fr.p(6.57, 0.004, 1.22), (0.24, 0.0, 0.0), (0.0, 0.0, 0.22), dcell(PATCH)))
    fr, n = wall_frame("SW")
    ua = wall_u("SW", PIER_A, PG.YS)
    emit(out, decal_quad(fr.p(ua - 0.11, 0.004, 1.62), V.mul(fr.X, 0.22), (0.0, 0.0, 0.28), dcell(GHOST)))
    emit(out, decal_quad(fr.p(ua - 0.13, 0.004, 2.10), V.mul(fr.X, 0.26), (0.0, 0.0, 0.20), dcell(PATCH)))
    emit(out, decal_quad((-0.52, 6.55, 0.485), (0.14, 0.0, 0.0), (0.0, 0.14, 0.0), dcell(TAPE)))   # repaired banquette seat
    return out


# ================================================================== assemble
def hall_faces():
    out = []
    out += K3.wall_kit_faces()
    out += K3.ceiling_faces_all()
    out += K3.booths_faces()
    out += K3.banquette_faces()
    out += K3.ledge_faces()
    out += V.counters_faces()
    out += K3.entry_mat()
    out += centre_faces()
    out += p1_wall_faces()
    out += p2_wall_faces()
    out += sw_wall_faces()
    out += counter_faces()
    out += decal_faces()
    return out


REMOVED = {"prop_atm_01": "P0 LP-001 ATM", "v_ret_ml_fridge02": "P0 LP-002 yellow drinks fridge",
           "v_res_rubberplant": "P0 LP-003 big plant", "prop_plant_int_01b": "P0 LP-003 big plant",
           "v_ret_fh_walllighton": "P0 LP-004 candle sconces", "ch_chint02_picture_light": "LP-012 gallery picture light",
           "ch_prop_vault_painting_01e": "LP-012 gallery art", "ch_prop_vault_painting_01a": "LP-012 gallery art",
           "ch_prop_vault_painting_01c": "LP-012 gallery art", "v_med_wallpicture1": "LP-011 anonymous print",
           "v_med_wallpicture2": "LP-011 anonymous print", "prop_beer_neon_02": "P0 LP-005 glass neon (gun / beer)",
           "prop_beer_neon_03": "P0 LP-005 glass neon (beer)", "prop_beer_neon_04": "P0 LP-005 glass neon (logger)",
           "v_19_vanmenuplain": "LP-007 chalk menus -> letterboards", "prop_jukebox_02": "LP-020 jukebox",
           "prop_gumball_01": "P0 LP-006 moved outside", "prop_gumball_02": "P0 LP-006 moved outside"}
BANQ_CHAIRS = ["v_ret_gc_chair02", "bkr_prop_clubhouse_chair_01", "v_ret_fh_chair01", "v_ret_gc_chair02"]
_DRESS = {"prop_bar_napkindisp", "prop_food_ketchup", "prop_food_mustard", "v_res_mp_ashtraya", "prop_food_sugarjar", "v_ret_gc_cup"}


def _banquette_item(name, s, t, zb):
    return name in _DRESS and abs(zb - ZT) < 0.01 and abs(t - BANQ_T) < 0.4 and any(abs(s - b) < 0.45 for b in BANQ_TABLES)


def vanilla_props():
    out = []
    ci = 0
    for name, s, t, zb, yaw in K3.vanilla_props():
        if name in REMOVED or _banquette_item(name, s, t, zb):
            continue
        if name == "v_ret_gc_chair02" and abs(t - (BANQ_T - 0.66)) < 0.05:
            name = BANQ_CHAIRS[ci % len(BANQ_CHAIRS)]
            yaw += (-5.0, 4.0, -9.0, 6.0)[ci % 4]
            ci += 1
        out.append((name, s, t, zb, yaw))
    # banquette tables: different habits per table (one deliberately clean)
    tw = BANQ_T + 0.25
    b0, b1, b2, b3 = BANQ_TABLES
    out += [("prop_bar_napkindisp", b0 - 0.13, tw, ZT, 0.0), ("prop_food_ketchup", b0 + 0.06, tw + 0.02, ZT, 0.0),
            ("prop_food_mustard", b0 + 0.13, tw + 0.03, ZT, 0.0), ("v_res_mp_ashtraya", b0 + 0.17, BANQ_T - 0.15, ZT, 0.0)]
    out += [("prop_food_sugarjar", b1 + 0.08, tw + 0.02, ZT, 0.0), ("v_ret_gc_cup", b1 - 0.15, BANQ_T - 0.18, ZT, 0.0),
            ("v_ret_gc_cup", b1 + 0.16, BANQ_T - 0.10, ZT, 0.0), ("v_res_mmug", b1 - 0.02, BANQ_T + 0.05, ZT, 140.0)]
    out += [("prop_bar_napkindisp", b2 - 0.10, tw, ZT, 0.0)]
    out += [("v_res_mp_ashtraya", b3 - 0.12, BANQ_T - 0.10, ZT, 0.0), ("prop_food_ketchup", b3 + 0.15, tw, ZT, 0.0),
            ("prop_cs_paper_cup", b3 + 0.02, BANQ_T + 0.02, ZT, 0.0)]
    out += centre_vanilla() + p1_vanilla() + p2_vanilla() + sw_vanilla()
    return out


def vanilla_entities():
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        mn = VB[name][0]
        out.append((name, (round(s, 4), round(t, 4), round(zb - mn[2], 4)), math.radians(yaw)))
    return out


def lights():
    L = [l for l in K3.lights() if l["kind"] not in ("sconce", "picture_light", "neon_spill")]
    for sc, tc in CTABLES:
        L.append(LT("centre_globe_key", "SPOT", (sc, tc, K4.PENDANT_Z - 0.20), C_TUNGSTEN, 6.0, 3.2, 14.0, cone=(62.0, 28.0),
                    flags=("static_shadows", "not_in_reflection")))
        L.append(CORONA("centre_globe", (sc, tc, K4.PENDANT_Z), C_TUNGSTEN, 0.5, 0.55))
    L.append(LT("entrance_wall_light", "POINT", (PIER_B, PG.YS + 0.18, 2.23), (1.0, 0.92, 0.80), 1.4, 2.8, 8.0, flags=FILL_FLAGS))
    return L


def collision_boxes():
    return K3.collision_boxes() + centre_collision()


SEATS = {"booths": 4 * V.N_BOOTHS, "banquettes": len(BANQ_TABLES), "banquette_chairs": len(BANQ_TABLES), "ledge": 3, "counter": 3,
         "centre_tables": 5}

# exterior (client-side spawn, see client/exterior.lua): (model, s, t, front direction in MLO-local axes)
EXTERIOR = [("prop_gumball_02", -3.49, 2.55, (-1.0, 0.0)), ("prop_gumball_01", -3.66, 1.75, (-1.0, 0.0))]
