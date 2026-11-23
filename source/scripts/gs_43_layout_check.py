# LONG PIG — offline layout audit: AABB overlaps between floor-standing vanilla props (rotated bounds) and between props
# and the own collision boxes / partitions; door swing quadrants. Usage: python gs_43_layout_check.py <kit_module>
import sys, math, importlib, json
sys.path.insert(0, '.')
kit = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "gs_v029_kit")
from gs_v027_kit import VB
try:
    import gs_v029_vb as V9
    for k, v in V9.VB_V029.items():
        VB.setdefault(k, v)
except Exception:
    pass
FLOOR = 0.015
SMALL = 0.35       # ignore props whose footprint is smaller than this in both directions (cups, jars ...)


def aabb(name, s, t, zb, yaw):
    (x0, y0, z0), (x1, y1, z1) = VB[name]
    a = math.radians(yaw)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(s + x * ca - y * sa, t + x * sa + y * ca) for x in (x0, x1) for y in (y0, y1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), max(xs), min(ys), max(ys), zb, zb + (z1 - z0))


def ov(a, b, m=0.02):
    return (min(a[1], b[1]) - max(a[0], b[0]) > m and min(a[3], b[3]) - max(a[2], b[2]) > m and min(a[5], b[5]) - max(a[4], b[4]) > m)


props = [(n, s, t, z, y) for (n, s, t, z, y) in kit.vanilla_props() if n in VB]
boxes = []
for p in props:
    b = aabb(*p)
    if (b[1] - b[0]) >= SMALL or (b[3] - b[2]) >= SMALL:
        boxes.append((p[0], round(p[1], 2), round(p[2], 2), b))
issues = []
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        if ov(boxes[i][3], boxes[j][3], 0.03):
            issues.append(("prop/prop", boxes[i][:3], boxes[j][:3]))
cols = []
for c in kit.collision_boxes():
    (bb, mat) = c
    if len(bb) == 6:
        cols.append((bb[0], bb[1], bb[2], bb[3], bb[4], bb[5]))
    else:
        (a, b2) = bb
        cols.append((a[0], b2[0], a[1], b2[1], a[2], b2[2]))
for nm, s, t, b in boxes:
    for c in cols:
        if ov(b, c, 0.04):
            issues.append(("prop/collision", (nm, s, t), tuple(round(v, 2) for v in c)))
print(json.dumps({"kit": kit.__name__, "props": len(props), "big": len(boxes), "issues": len(issues)}))
for x in issues:
    print(x)

# ---- door swing: props / collision inside the quarter discs swept by each leaf (both sides)
if hasattr(kit, "all_doors"):
    import gs_boh29_kit as B9
    by_model = {v["model"]: v for v in B9.DOOR_SPECS.values()}
    print("doors")
    for did, arch, (ds, dt, dz), yaw in kit.all_doors():
        spec = by_model[arch]
        w = spec["x"][1] - spec["x"][0]
        sgn = -1.0 if spec["x"][0] < -0.5 else 1.0
        ca, sa = math.cos(yaw), math.sin(yaw)
        leaf = (sgn * ca, sgn * sa)                          # closed leaf direction from the hinge
        nrm = (-sa, ca)                                      # model +y
        hits = []
        for side in (1.0, -1.0):
            for nm, s, t, b in boxes:
                for (px, py) in ((b[0], b[2]), (b[1], b[2]), (b[0], b[3]), (b[1], b[3]), ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2)):
                    vx, vy = px - ds, py - dt
                    r = math.hypot(vx, vy)
                    a_leaf = vx * leaf[0] + vy * leaf[1]
                    a_n = side * (vx * nrm[0] + vy * nrm[1])
                    if r < w - 0.02 and a_leaf > -0.02 and a_n > 0.02 and b[4] < 2.0:
                        hits.append((("+" if side > 0 else "-") + "y", nm, s, t))
                        break
        print(did, arch, "w=%.2f" % w, "clear" if not hits else hits)
