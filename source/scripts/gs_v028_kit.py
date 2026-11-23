# LONG PIG — v0.2.8: back of house completed (gs_boh_kit: partitions per plan v2, kitchen, storage, walk-in cooler,
# corridor, staff entry, staff back room, office, staff WC) on top of the v0.2.7 hall (night light, feedback items,
# shutters). The hall drawable is unchanged except: the v0.2.6 cleaning corner moves to the staff entry (two of its props
# stood where the new P1n wall is) and the mop-corner puddle moves with it.
import gs_v027_kit as K7
from gs_v027_kit import *                    # noqa: F401,F403
import gs_boh_kit as B

VERSION = "0.2.8-boh"
BOH = True
BOH_SPECS = B.BOH_SPECS
boh_faces = B.boh_faces
boh_lights = B.boh_lights
boh_doors = B.boh_doors

CAM_VIEWS = dict(K7.CAM_VIEWS)
CAM_VIEWS.update({
    "GS28_KITCHEN": ((10.6, -0.6, 1.70), (14.5, 3.6, 1.10), "kitchen from the P1 door: range + hood, island, sink"),
    "GS28_KITCHEN2": ((15.6, 4.3, 1.70), (11.0, 0.8, 1.05), "kitchen towards P1: fridges, shelving, hand sink, D2"),
    "GS28_STORAGE": ((10.5, 7.7, 1.65), (14.8, 10.6, 1.10), "storage from the corridor door"),
    "GS28_COOLER": ((14.0, 5.4, 1.65), (15.4, 8.2, 1.10), "walk-in cooler"),
    "GS28_CORRIDOR": ((9.4, 7.7, 1.65), (-1.5, 7.9, 1.30), "corridor towards the staff entry"),
    "GS28_ENTRY": ((0.2, 7.6, 1.65), (-2.4, 10.4, 1.10), "staff entry (D3), cleaning corner"),
    "GS28_BACKROOM": ((3.45, 8.7, 1.65), (2.2, 11.1, 0.90), "staff back room"),
    "GS28_OFFICE": ((7.35, 8.8, 1.65), (6.6, 11.3, 0.95), "office"),
    "GS28_WC": ((9.3, 8.7, 1.65), (9.1, 11.3, 0.80), "staff WC"),
})

def floor_faces():
    """v0.2.7 floor + the mop-corner puddle moved into the staff entry (was in front of the new storage door)."""
    out = []
    for f in K7_floor_faces_orig():
        cx = sum(v[0] for v in f["v"]) / len(f["v"]); cy = sum(v[1] for v in f["v"]) / len(f["v"])
        if f["mat"] == MAT["puddle"] and abs(cx - 9.86) < 0.05 and abs(cy - 7.78) < 0.05:
            continue
        out.append(f)
    emit(out, K7.floor_quad(-1.95, 7.80, 0.62, 0.48, 70.0, 0, mat="puddle"))
    return out


K7_floor_faces_orig = getattr(K7, "_floor_faces_v027", None) or K7.floor_faces
K7._floor_faces_v027 = K7_floor_faces_orig
K7.floor_faces = floor_faces                 # hall_faces() of the v0.2.7 kit looks the function up at call time


def hall_faces():
    return K7.hall_faces()


def vanilla_props():
    out = []
    for e in K7.vanilla_props():
        if (e[0], round(e[1], 2), round(e[2], 2)) in B.CLEANING_OLD:
            continue
        out.append(e)
    return out + B.boh_vanilla()


def vanilla_entities():
    out = []
    for name, s, t, zb, yaw in vanilla_props():
        mn = VB[name][0]
        out.append((name, (round(s, 4), round(t, 4), round(zb - mn[2], 4)), math.radians(yaw)))
    for did, arch, pos, yaw in B.boh_doors():
        out.append((arch, pos, yaw))
    return out


def collision_boxes():
    return K7.collision_boxes() + B.boh_collision()
