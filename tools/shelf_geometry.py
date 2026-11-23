"""Check actual Legacy stock meshes against shelf triangles in the shipped native YDR and YTYP."""

from collections import defaultdict
from pathlib import Path

import numpy as np
import szio
from szio.vfs import VPath


def path_in(folder, name):
    matches = list(folder.rglob(name))
    if len(matches) != 1:
        raise ValueError(f'{folder}: found {len(matches)} copies of {name}')
    return matches[0]


def read_actual_packs(game):
    models = {}
    folder = VPath(str(game/'x64c.rpf/levels/gta5/props/commercial/v_fastfood.rpf'))
    for suffix in ('','2','3','4','5','6'):
        name = 'v_ret_ml_cigs' + suffix
        fragment = szio.try_load_asset(folder/(name+'.yft'))
        g = next(iter(fragment.drawable.models.values()))[0].geometries[0]
        verts = g.vertex_buffer
        positions = np.asarray(verts['Position'], dtype=float)
        cells = []
        for sign in (-1,1):
            mask = verts['Normal'][:, 1] * sign > .999
            assert mask.sum() == 4
            uv_centre = verts['TexCoord0'][mask].mean(0)
            cells.append(tuple((uv_centre * [4,2]).astype(int)))
        assert cells[0] == cells[1] and len(g.index_buffer) == 36
        models[name] = positions
    return models


def geometry(folder):
    market = szio.try_load_asset(path_in(folder, 'gs_v26_market.ydr'))
    tris = []
    for model in next(iter(market.models.values())):
        for g in model.geometries:
            points = np.asarray(g.vertex_buffer['Position'], dtype=float)
            tris.extend(points[np.asarray(g.index_buffer).reshape(-1,3)])
    return np.asarray(tris)


def inside_xy(tri, pt):
    a,b,c = tri[:,:2]
    edges = (b-a, c-b, a-c)
    cross = [e[0]*(pt-p)[1] - e[1]*(pt-p)[0] for p,e in zip((a,b,c),edges)]
    return min(cross) >= -1e-8 or max(cross) <= 1e-8


def penetrates(tri, lo, hi):
    """Separating axes for a triangle and an axis-aligned box."""
    basis = np.eye(3)
    points = tri - (hi+lo)/2
    half = (hi-lo)/2
    edges = (points[1]-points[0],points[2]-points[1],points[0]-points[2])
    axes = [np.cross(edges[0],edges[1])]
    axes.extend(np.cross(edge,axis) for edge in edges for axis in basis)
    for ax in axes:
        if np.linalg.norm(ax)<1e-10:
            continue
        projections = points @ ax
        radius = abs(ax) @ half
        if projections.min() > radius or projections.max() < -radius:
            return False
    return True


def inspect(folder, models, updated):
    all_tri = geometry(folder)
    normals = np.cross(all_tri[:,1]-all_tri[:,0],all_tri[:,2]-all_tri[:,0])
    surfaces = all_tri[(normals[:,2] > 1e-9) & (np.ptp(all_tri[:,:,2],axis=1)<1e-6)]
    tri_lo,tri_hi=all_tri.min(1),all_tri.max(1)
    ytyp=szio.try_load_asset(path_in(folder, 'gabagool_sons_mlo.ytyp'))
    mlo=next(a for a in ytyp.archetypes if a.type.name=='MLO')
    rows = defaultdict(list)
    bounds, gaps, air, lod_distances, flags = [], [], [], set(), set()
    for ent in mlo.entities:
        if ent.archetype_name not in models:
            continue
        lod_distances.add(float(ent.lod_dist))
        flags.add(int(ent.flags.value))
        # Native CEntityDef stores the inverse quaternion. The original stock has local depth along Y.
        q = np.asarray(ent.rotation, float); q /= np.linalg.norm(q); u = -q[1:]
        v = models[ent.archetype_name] * [ent.scale_xy,ent.scale_xy,ent.scale_z]
        verts = v + 2*np.cross(u,np.cross(u,v)+q[0]*v) + np.asarray(ent.position,float)
        lo,hi = verts.min(0),verts.max(0)
        assert abs((hi-lo)[0]-.0390625)<.0001 and abs((hi-lo)[1]-.0859375)<.0001
        assert 9.721 < lo[0] < hi[0] < 9.926
        bay = 0 if ent.position[1] < 1.445 else 2
        ends = (.22,1.445) if bay == 0 else (2.73,3.955)
        assert ends[0]<lo[1]<hi[1]<ends[1]
        rows[(bay,round(float(lo[2]),3))].append((lo,hi,ent.archetype_name))
        for x in (lo[0]+.0001,hi[0]-.0001):
            for y in (lo[1]+.0001,hi[1]-.0001):
                covers=[tri[0,2] for tri in surfaces if lo[2]-.05<tri[0,2]<lo[2]+.002 and inside_xy(tri,np.array([x,y]))]
                assert covers, (lo,hi,'unsupported corner')
                air.append(lo[2]-max(covers))
        if updated:
            inner_lo,inner_hi=lo+.0002,hi-.0002
            candidates=all_tri[(tri_hi>=inner_lo).all(1)&(tri_lo<=inner_hi).all(1)]
            assert not any(penetrates(tr,inner_lo,inner_hi) for tr in candidates),(ent.archetype_name,lo,'triangle inside pack')
        bounds.append((lo,hi))
    for i,(lo,hi) in enumerate(bounds):
        for other_lo,other_hi in bounds[:i]:
            assert not (np.minimum(hi,other_hi)>np.maximum(lo,other_lo)).all(), (i,lo,hi,other_lo,other_hi)
    result=[]
    for (bay,z), items in sorted(rows.items()):
        items.sort(key=lambda v:v[0][1]); names=[n for _,_,n in items]
        assert len(items) == (10 if updated else 8)
        gaps.extend(b[0][1]-a[1][1] for a,b in zip(items,items[1:]))
        if updated:
            assert set(names)=={'v_ret_ml_cigs','v_ret_ml_cigs2'} if bay==0 else names[3:7]==['v_ret_ml_cigs5']*4
        result.append({'bay':bay,'bottom_z':z,'count':len(items),'labels':names})
    assert len(rows)==7
    assert max(abs(v) for v in air)<(.00015 if updated else .001)
    return {'packs':len(bounds),'rows':result,'support_points_checked':len(air),'lod_distances_m':sorted(lod_distances),
            'entity_flags':sorted(flags),'support_error_mm':[round(float(x)*1000,3) for x in (min(air),max(air))],
            'between_pack_edges_mm':sorted({round(float(x)*1000,2) for x in gaps}),'checked_market_triangles':len(all_tri)}
