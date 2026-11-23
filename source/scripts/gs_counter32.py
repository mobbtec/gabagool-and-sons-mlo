# LONG PIG 0.3.2-c - DELI COUNTER, FULL REBUILD (owner brief "LONG PIG DELI COUNTER - FULL REWORK", 2026-11-15).
# Everything below the hanging menu boards is new own geometry on the SAME footprint (collision, interaction points,
# prop heights unchanged): one continuous service line - black toe kick, stainless kick plate, red-brown beadboard
# front, continuous stainless bumper rail, cream apron, cream laminate tops with a stainless edge - with two straight
# slanted-glass refrigerated cases in stainless frames (glass ends, glass top strip, steel service shelf, white deck,
# light strip, rear sliding doors) and a stainless prep bench with an under-counter fridge on the back wall.
# Replaces gs_v021_kit.deli_case / counter_body / back_counter (the food trays, slicer, ham stand, paper roll stay).
import math
import gs_v021_kit as V
from gs_v021_kit import Frame, F, emit, cbox, prism, tube, round_rect, FLOOR

LINE_T0, LINE_T1 = V.GATE_T[0], V.COFFEE_T[1]
PITCH, PLANK = 0.095, 0.089
Z_KICK, Z_PLATE, Z_BUMP0, Z_BUMP1 = 0.11, 0.27, 0.795, 0.86
BOARD_MAT = "walnut"
BOARD_MISSING, BOARD_LOW, BOARD_TOP, BOARD_SPRUNG = {9, 33, 34, 58}, {14, 47}, {22, 63}, {5, 41, 70}


def _ext(t0, t1):
    return (0.0 if abs(t0 - LINE_T0) < 1e-6 else 0.025, 0.0 if abs(t1 - LINE_T1) < 1e-6 else 0.025)


def _front(fr, t0, t1, louvre=False):
    """Customer face of one segment of the line (x = 0 .. L of fr, extended over the joints)."""
    out = []
    L = t1 - t0
    g0, g1 = _ext(t0, t1)
    a, b = -g0, L + g1
    out += cbox(fr, a, b, 0.075, 0.95, FLOOR, Z_KICK, "rubber", grain="x", skip=("-z",))                 # recessed toe kick
    out += cbox(fr, a, b, 0.022, 0.036, Z_KICK, Z_PLATE, "steel", ch=0.003, grain="x", skip=("+y",))     # kick plate
    if louvre:
        for k in range(5):
            z = Z_KICK + 0.028 + k * 0.022
            out += cbox(fr, 0.22, L - 0.22, 0.019, 0.023, z, z + 0.011, "iron", grain="x", skip=("+y",))
    out += cbox(fr, a, b, 0.030, 0.037, Z_PLATE, Z_BUMP0, "iron", grain="x", skip=("+y", "-z", "+z"))    # dark backing (grooves)
    k0 = int(math.floor((t0 - g0 - LINE_T0) / PITCH))
    k = k0
    while LINE_T0 + k * PITCH < t1 + g1 - 1e-6:
        xa = max(LINE_T0 + k * PITCH + (PITCH - PLANK) / 2, t0 - g0) - t0
        xb = min(LINE_T0 + k * PITCH + (PITCH + PLANK) / 2, t1 + g1) - t0
        if xb - xa > 0.012 and k not in BOARD_MISSING:                 # 1.2.0: worn painted boards, some gone / broken / sprung
            za = Z_PLATE + 0.012 + (0.19 if k in BOARD_LOW else 0.0)
            zb_ = Z_BUMP0 - 0.004 - (0.16 if k in BOARD_TOP else 0.0)
            y0 = 0.003 if k in BOARD_SPRUNG else 0.012
            out += cbox(fr, xa, xb, y0, y0 + 0.022, za, zb_, BOARD_MAT, ch=0.004, grain="z", skip=("+y",))
        k += 1
    out += cbox(fr, a, b, 0.006, 0.036, Z_PLATE, Z_PLATE + 0.014, "steel", ch=0.003, grain="x", skip=("+y",))   # base rail
    bump = round_rect(-0.034, 0.036, Z_BUMP0, Z_BUMP1, 0.022, seg=4, corners=(1, 0, 1, 0))
    out += prism(fr, bump, a, b, "steel", smooth="all", caps=(g0 == 0.0, g1 == 0.0))                      # bumper rail
    if g0 == 0.0:                                                                                         # south end of the line
        out += cbox(fr, -0.024, 0.0, 0.036, 0.98, Z_KICK, Z_BUMP1, "walnut", ch=0.004, grain="z", skip=("+x",))
    return out


def counter_body(t0, t1, zt=1.02, top="terrazzo"):
    out = []
    fr = V.front_frame(t0)
    L = t1 - t0
    g0, g1 = _ext(t0, t1)
    out += _front(fr, t0, t1)
    # carcass: closed to the customer, open shelves on the staff side
    out += cbox(fr, -g0, L + g1, 0.036, 0.062, Z_KICK, zt - 0.035, "enamel", grain="x", skip=("-y", "-z", "+z"))
    for xa, xb in ((0.0, 0.03), (L - 0.03, L)):
        out += cbox(fr, xa, xb, 0.062, 0.98, Z_KICK, zt - 0.035, "enamel", grain="z", skip=("-z", "+z"))
    for z in (Z_KICK, 0.48):
        out += cbox(fr, 0.03, L - 0.03, 0.062, 0.97, z, z + 0.025, "enamel", ch=0.003, grain="x")
    out += cbox(fr, -g0, L + g1, 0.030, 0.062, Z_BUMP1, zt - 0.035, "enamel", ch=0.003, grain="x", skip=("+y", "+z"))   # cream apron
    # top: cream laminate, stainless edge on the customer side and the open ends
    out += cbox(fr, -g0 - (0.012 if g0 == 0.0 else 0.0), L + g1, -0.020, 1.0, zt - 0.035, zt, top, ch=0.003, grain="x", skip=("-z",))
    edge = round_rect(-0.036, -0.018, zt - 0.040, zt + 0.002, 0.007, seg=3)
    out += prism(fr, edge, -g0 - (0.012 if g0 == 0.0 else 0.0), L + g1, "steel", smooth="all", caps=(True, True))
    return out


def _glass(out, vs, hint):
    emit(out, F(vs, "glass", [(0, 0), (1, 0), (1, 1), (0, 1)][:len(vs)], hint=hint))
    emit(out, F(vs, "glass", [(0, 0), (1, 0), (1, 1), (0, 1)][:len(vs)], hint=tuple(-c for c in hint)))


def deli_case(t0, t1, hero=False):
    """Straight slanted-glass refrigerated deli case in a stainless frame."""
    out = []
    fr = V.front_frame(t0)
    L = t1 - t0
    p = 0.032                                           # post / rail section
    zs, zg, zt = 0.86, 0.90, 1.31                       # sill bottom, glass bottom, top of the frame
    yf0, yf1 = 0.045, 0.200                             # front glass: y at the bottom / top
    yr = 0.84                                           # rear frame
    out += _front(fr, t0, t1, louvre=True)
    # insulated body (cream enamel), staff-side doors with pulls, work ledge
    out += cbox(fr, 0.0, L, 0.036, 0.98, Z_KICK, zs, "enamel", grain="x", skip=("-y", "-z", "+z"))
    for k in range(2):
        xa, xb = 0.02 + k * (L - 0.02) / 2, (k + 1) * (L - 0.02) / 2
        out += cbox(fr, xa, xb, 0.98, 1.0, Z_KICK + 0.02, 0.84, "enamel", ch=0.004, grain="z")
        out += cbox(fr, xb - 0.10, xb - 0.04, 1.0, 1.02, 0.70, 0.72, "steel", ch=0.003, grain="x")
    out += cbox(fr, 0.0, L, 0.86, 1.03, 0.945, 0.97, "steel", ch=0.004, grain="x")
    # white display deck + stainless sill all round
    out += cbox(fr, p, L - p, 0.05, yr, zs, zs + 0.02, "enamel", grain="x", skip=("-z",))
    out += cbox(fr, 0.0, L, 0.020, 0.060, zs, zg, "steel", ch=0.004, grain="x")
    out += cbox(fr, 0.0, L, yr, yr + p, zs, zg, "steel", ch=0.004, grain="x")
    for xa, xb in ((0.0, p), (L - p, L)):
        out += cbox(fr, xa, xb, 0.060, yr, zs, zg, "steel", ch=0.004, grain="y")
        # slanted front post, rear post, top side rail
        out += prism(fr, [(yf0 - 0.018, zg), (yf0 + 0.016, zg), (yf1 + 0.016, zt), (yf1 - 0.018, zt)], xa, xb, "steel", caps=(True, True))
        out += cbox(fr, xa, xb, yr, yr + p, zg, zt + 0.03, "steel", ch=0.003, grain="z")
        out += cbox(fr, xa, xb, yf1 - 0.018, yr, zt - 0.014, zt + 0.018, "steel", ch=0.003, grain="y")
    # long rails: front top, glass / shelf joint
    out += cbox(fr, p, L - p, yf1 - 0.018, yf1 + 0.016, zt - 0.014, zt + 0.018, "steel", ch=0.003, grain="x")
    ym = 0.50
    # front glass, top glass strip, glass ends
    _glass(out, [fr.p(p, yf0, zg), fr.p(L - p, yf0, zg), fr.p(L - p, yf1, zt - 0.012), fr.p(p, yf1, zt - 0.012)], fr.v(0.0, -1.0, 0.35))
    _glass(out, [fr.p(p, yf1 + 0.016, zt + 0.004), fr.p(L - p, yf1 + 0.016, zt + 0.004), fr.p(L - p, ym, zt + 0.004), fr.p(p, ym, zt + 0.004)],
           fr.v(0.0, 0.0, 1.0))
    for x, sg in ((p / 2, -1.0), (L - p / 2, 1.0)):
        _glass(out, [fr.p(x, yf0 + 0.02, zg), fr.p(x, yr, zg), fr.p(x, yr, zt - 0.012), fr.p(x, yf1 + 0.02, zt - 0.012)], fr.v(sg, 0.0, 0.0))
    # stainless service shelf over the rear half (hand-over point), with a rolled front lip
    out += cbox(fr, 0.0, L, ym, yr + p + 0.03, zt, zt + 0.03, "steel", ch=0.005, grain="x")
    out += tube(fr, [(0.0, ym, zt + 0.018), (L, ym, zt + 0.018)], 0.013, 8, "steel", caps=True)
    # light strip under the front rail, shining into the case
    out += cbox(fr, p + 0.02, L - p - 0.02, yf1 + 0.02, yf1 + 0.05, zt - 0.022, zt - 0.016, "glow", grain="x", skip=("+z",))
    out += cbox(fr, p, L - p, yf1 + 0.012, yf1 + 0.058, zt - 0.016, zt - 0.006, "steel", grain="x")
    # rear sliding glass doors with steel pulls
    for k in range(2):
        xa, xb = p + k * (L - 2 * p) / 2, p + (k + 1) * (L - 2 * p) / 2
        yy = yr - 0.03 + 0.012 * k
        _glass(out, [fr.p(xa, yy, zg), fr.p(xb, yy, zg), fr.p(xb, yy, zt - 0.01), fr.p(xa, yy, zt - 0.01)], fr.v(0.0, 1.0, 0.0))
        out += cbox(fr, xb - 0.06, xb - 0.03, yy + 0.002, yy + 0.016, 1.0, 1.16, "steel", grain="z")
    # price-tag rail along the inside of the front sill
    out += cbox(fr, p, L - p, 0.060, 0.066, zg, zg + 0.028, "enamel", grain="x")
    return out


def back_counter():
    """Stainless prep bench on the back wall: steel top, legs, lower shelf, an under-counter fridge at the kitchen end,
    enamel splashback with a steel rail, two walnut wall shelves on iron brackets between the menus (kept)."""
    out = []
    s0, s1 = V.BACK_S
    t0, t1 = V.BACK_T
    fr = Frame((s0, t1, 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))     # x along -t, y towards P1
    L, D = t1 - t0, s1 - s0
    out += cbox(fr, -0.02, L + 0.02, -0.03, D, 0.885, 0.92, "steel", ch=0.006, grain="x")
    out += cbox(fr, 0.0, L, 0.0, 0.02, 0.815, 0.885, "steel", ch=0.003, grain="x", skip=("+y",))            # apron
    fx0 = L - 1.95                                                                                          # fridge block (kitchen end)
    n = 5
    for k in range(n + 1):
        x = 0.02 + (fx0 - 0.08) * k / n
        out += cbox(fr, x, x + 0.04, 0.02, 0.06, FLOOR, 0.815, "steel", ch=0.004, grain="z", skip=("-z", "+z"))
        out += cbox(fr, x, x + 0.04, D - 0.07, D - 0.03, FLOOR, 0.815, "steel", ch=0.004, grain="z", skip=("-z", "+z"))
    out += cbox(fr, 0.02, fx0 - 0.02, 0.03, D - 0.02, 0.24, 0.265, "steel", ch=0.004, grain="x")            # lower shelf
    # under-counter fridge: enamel body, three doors, steel pulls, louvre
    out += cbox(fr, fx0, L - 0.02, 0.03, D, FLOOR + 0.10, 0.815, "enamel", grain="x", skip=("-z", "+z"))
    out += cbox(fr, fx0, L - 0.02, 0.06, D, FLOOR, FLOOR + 0.10, "rubber", grain="x", skip=("-z",))
    dw = (L - 0.02 - fx0) / 3
    for k in range(3):
        xa, xb = fx0 + k * dw + 0.008, fx0 + (k + 1) * dw - 0.008
        out += cbox(fr, xa, xb, 0.008, 0.03, FLOOR + 0.24, 0.80, "enamel", ch=0.006, grain="z", skip=("+y",))
        out += cbox(fr, xa + 0.04, xa + 0.06, -0.016, 0.008, 0.50, 0.72, "steel", ch=0.004, grain="z")
        for j in range(3):
            z = FLOOR + 0.125 + j * 0.03
            out += cbox(fr, xa + 0.03, xb - 0.03, 0.022, 0.03, z, z + 0.014, "iron", grain="x", skip=("+y",))
    sp = Frame((V.P1_S[0], t0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    # 0.3.2-e: no enamel band / rail - the white wall tile runs down to the steel upstand
    out += cbox(sp, 0.0, L, 0.0, 0.03, 0.92, 0.97, "steel", ch=0.004, grain="x", skip=("-y",))              # upstand
    wf = Frame((V.P1_S[0], 2.30, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    for z in (1.42, 1.86):
        out += cbox(wf, 0.0, 2.10, 0.0, 0.26, z, z + 0.035, "walnut", ch=0.006, grain="x")
        for x in (0.15, 1.05, 1.95):
            out += cbox(wf, x - 0.012, x + 0.012, 0.0, 0.012, z - 0.20, z, "iron", grain="z")
            out += cbox(wf, x - 0.012, x + 0.012, 0.0, 0.20, z - 0.02, z, "iron", grain="y")
            out += tube(wf, [(x, 0.01, z - 0.18), (x, 0.17, z - 0.02)], 0.006, 6, "iron")
    return out


def install():
    V.deli_case = deli_case
    V.counter_body = counter_body
    V.back_counter = back_counter
