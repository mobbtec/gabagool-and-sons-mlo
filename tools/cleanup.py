"""Clean verified surfaces in LONG PIG v3.x without altering game archives.

Run in Blender with Sollumz enabled. After '--', pass input and output mlo
directories. These may contain a newer lighting build of the same models.
"""
import dataclasses
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import szio
from szio.gta5 import AssetFormat, AssetTarget, AssetVersion


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def geometry_rows(drawable):
    for lod, models in drawable.models.items():
        for i, model in enumerate(models):
            for j, geom in enumerate(model.geometries):
                yield (lod.name, i, j), geom


def shell(geometry):
    # The original random broken tile pattern included repeated corner
    # positions. Remove only triangles with exactly coincident vertices.
    idx = geometry.index_buffer.reshape(-1,3)
    points = geometry.vertex_buffer["Position"][idx]
    remove = np.zeros(len(idx), bool)
    for i,j in ((0,1),(1,2),(2,0)):
        remove |= (points[:,i] == points[:,j]).all(axis=1)
    if int(remove.sum()) not in (0,5):
        raise ValueError("Unexpected floor topology")
    geometry.index_buffer = np.ascontiguousarray(idx[~remove].ravel())
    return int(remove.sum())


def hall(geometry):
    vb = geometry.vertex_buffer.copy()
    xyz = vb["Position"]
    # Two neighbouring back-to-back booth backs intersect at their overhanging
    # wooden end profiles. Pull only the overhanging edge on the two exposed
    # end boards inward and preserve every apron, cushion and bevel.
    ends = np.isclose(xyz[:,1,None], [-1.225,-1.190,-0.040,-0.005], atol=0.00001,rtol=0).any(axis=1)
    edits = []
    for center in (2.50, 4.35):
        for side in (-1,1):
            for old_y, new_y, heights, locations in (
                (-0.015, 0.001, (0.015,1.040), 8),  # side boards
                (-0.012, 0.001, (1.040,1.080), 4),  # long cap rail
                (-0.006, 0.005, (1.094,), 2),       # crown of its fillet
            ):
                old_x = center + side * old_y
                new_x = center + side * new_y
                z_mask = np.isclose(xyz[:,2,None], heights, atol=0.00001,rtol=0).any(axis=1)
                select = ends & z_mask & np.isclose(xyz[:,0], old_x, atol=0.00001, rtol=0)
                seen = len(np.unique(xyz[select],axis=0))
                if seen not in (0,locations):
                    raise ValueError(f"Unexpected end profile at {old_x}: {seen}")
                edits.append(int(select.sum()))
                xyz[select,0] = new_x
    if any(edits) and not all(edits):
        raise ValueError("Only part of the expected bench profile matched")
    geometry.vertex_buffer = vb
    return edits


def counter_end_caps(geometry):
    # gs_counter32._front emits end caps on both pieces where each counter
    # module meets its neighbour. These are inside the continuous kickplate,
    # solid backing and rubber toe kick. Exclude glass and all detached parts.
    verts = geometry.vertex_buffer["Position"]
    idx = geometry.index_buffer.reshape(-1,3)
    pts = verts[idx]
    candidate = np.zeros(len(idx), bool)
    for seam in (2.625,4.775):
        candidate |= np.max(np.abs(pts[:,:,1]-seam),axis=1) < 1e-5
    candidate &= (pts[:,:,0].min(axis=1) >= 6.995) & (pts[:,:,0].max(axis=1) <= 7.96)
    candidate &= (pts[:,:,2].min(axis=1) >= 0.0149) & (pts[:,:,2].max(axis=1) <= 0.80)
    remove = set()
    seen = {}
    for i in np.flatnonzero(candidate):
        face = pts[i]
        coords = tuple(sorted(tuple(v) for v in face))
        normal = np.cross(face[1]-face[0],face[2]-face[0])
        if coords in seen:
            other,opposite = seen[coords]
            if np.dot(opposite,normal)<0:
                remove.update((other,i))
        else:
            seen[coords] = (i,normal)
    if remove:
        keep = np.ones(len(idx),bool)
        keep[list(remove)]=False
        geometry.index_buffer=np.ascontiguousarray(idx[keep].ravel())
    return len(remove)


def capture(drawable):
    buffers={k:(g.shader_index,digest(g.vertex_buffer.tobytes()),digest(g.index_buffer.tobytes())) for k,g in geometry_rows(drawable)}
    textures={k:digest(t.data.read_bytes()) for k,t in (drawable.shader_group.embedded_textures or {}).items()}
    lights=[dataclasses.asdict(l) for l in drawable.lights or []]
    return buffers,textures,lights


def save_clean(source,target):
    target.mkdir(parents=True,exist_ok=True)
    if source.resolve() == target.resolve():
        raise ValueError("Use separate input and output directories")
    counts={}
    for name in ("gs_proto_shell","gs_v021_hall"):
        d=szio.try_load_asset(source/(name+".ydr"))
        caps=0
        for key,g in geometry_rows(d):
            if key == ("HIGH",0,0) and g.shader_index==0:
                counts[name]=shell(g) if name=="gs_proto_shell" else hall(g)
            if name=="gs_v021_hall" and g.shader_index in (3,6,15) and key[:2]==("HIGH",0):
                caps+=counter_end_caps(g)
        if name=="gs_v021_hall":
            counts["hidden_counter_triangles"]=caps
        expected=capture(d)
        szio.save_asset(d,[AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8)],target,name)
        check=szio.try_load_asset(target/(name+".ydr"))
        actual=capture(check)
        for prop,want,got in zip(("vertex/index streams","texture payloads","light records"),expected,actual):
            if want!=got:
                raise ValueError((name,prop,"native round-trip changed content"))
        print("VERIFIED",name,counts[name],len(expected[0]),len(expected[1]),len(expected[2]))
    return counts


if __name__ == "__main__":
    args=sys.argv[sys.argv.index("--")+1:]
    if len(args)!=2:raise ValueError("Expected input and output mlo directories")
    save_clean(*map(Path,args))
