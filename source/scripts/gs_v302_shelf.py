"""LONG PIG 3.0.2: the two tobacco bays of the existing five-bay shop fixture."""

import gs_v300_kit as base

# The six Legacy YFTs use the same cuboid and assign different cells of gz_v_ml_cigarettes.
# The signed bounds below are from the drawable vertices, before rotating the label to the aisle.
PACK_WIDTH = .0859375
PACK_DEPTH = .0390625
PACK_HALF_HEIGHT = .0634765625
PITCH = .096
GROUP_GAP = .043
TRAY_HEIGHT = .006

# Numbers index the original game's six cigarette archetypes. Each tuple is a contiguous block.
REDWOOD = ((2, 5), (1, 5))
CENTRE_LOW = ((6, 3), (5, 4), (4, 3))
CENTRE_HIGH = ((3, 3), (5, 4), (4, 3))


def display_rows():
    for bay, rows in ((0, (1, 2)), (2, range(5))):
        t0, t1 = base._bay(bay)
        for index in rows:
            z, _clear = base._rows(bay)[index]
            products = REDWOOD if bay == 0 else (CENTRE_LOW if index < 2 else CENTRE_HIGH)
            spans = [PACK_WIDTH + (count - 1) * PITCH for _variant, count in products]
            width = sum(spans) + (len(spans) - 1) * GROUP_GAP
            t = (t0 + t1 - width) / 2
            groups = []
            for (variant, count), span in zip(products, spans):
                groups.append((base.CIGS[variant - 1], count, t, t + span))
                t += span + GROUP_GAP
            yield bay, index, z, groups


def packs(z, groups):
    shelf_front = base.XE - .004 - base.D
    s = shelf_front + .015 + PACK_DEPTH / 2
    # The old _ent function rounds the stock model's minimum z to whole millimetres.
    # Compensate for that conversion so the real YFT, not just the scan, touches its tray.
    out = []
    for name, count, t0, _t1 in groups:
        zb = z + TRAY_HEIGHT + PACK_HALF_HEIGHT + base.VB[name][0][2]
        for slot in range(count):
            out.append((name, s, t0 + PACK_WIDTH / 2 + PITCH * slot, zb, -90.0))
    return out


def trays(out):
    front = base.XE - .004 - base.D
    front_edge, back_edge = front + .008, front + .181
    for _bay, _index, z, groups in display_rows():
        for _name, _count, t0, t1 in groups:
            a, b = t0 - .008, t1 + .008
            out += base.V.cbox(base.V.WORLD, front_edge, back_edge, a, b, z, z + TRAY_HEIGHT,
                               'top20', skip=('-z',))
            # Narrow side fences: low at the lip, rising toward the empty stock channel behind the packs.
            for lo, hi in ((a, a + .003), (b - .003, b)):
                x0, x1, x2 = front_edge + .003, front + .081, back_edge - .002
                z0 = z + TRAY_HEIGHT
                profile = [(x0, z0), (x2, z0), (x2, z0 + .033), (x1, z0 + .016), (x0, z0 + .008)]
                # Explicit planar faces keep the thin deck and the guides free of coplanar surfaces.
                for t, norm in ((lo, (0,-1,0)), (hi, (0,1,0))):
                    verts = [(x,t,h) for x,h in profile]
                    base.V.emit(out, base.V.F(verts, 'alu20', [(x,h) for x,h in profile], hint=norm))
                for (xa, za), (xb, zb) in zip(profile[1:], profile[2:] + profile[:1]):
                    verts=[(xa,lo,za),(xb,lo,zb),(xb,hi,zb),(xa,hi,za)]
                    uv=[(xa+za,lo),(xb+zb,lo),(xb+zb,hi),(xa+za,hi)]
                    base.V.emit(out, base.V.F(verts,'alu20',uv,hint=(zb-za,0,xa-xb)))


def install():
    if getattr(base._unit_props, '_shelf_302', False):
        return
    old_unit, old_props = base._unit, base._unit_props

    def unit(out):
        old_unit(out)
        trays(out)

    def unit_props():
        replacements = {(bay, round(z,4)):packs(z, groups) for bay, _, z, groups in display_rows()}
        out = []
        for item in old_props():
            name, _, t, z, _ = item
            if name not in base.CIGS:
                out.append(item)
                continue
            bay = 0 if t < base._bay(0)[1] else 2
            out.extend(replacements.pop((bay, round(z,4)), ()))
        if replacements:
            raise ValueError(f'Missing original tobacco rows: {tuple(replacements)}')
        return out

    unit_props._shelf_302 = True
    base._unit, base._unit_props = unit, unit_props
