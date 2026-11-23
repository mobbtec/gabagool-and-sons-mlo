"""Validate the generated 3.0.2 resource and all cigarette placements against installed game assets."""
import json
import os
from pathlib import Path
import sys

import numpy as np
import szio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shelf_geometry import inspect, read_actual_packs


def check(resource):
    stream = resource/'stream'
    drawables = {}
    for file in sorted(stream.rglob('*.ydr')):
        obj = szio.try_load_asset(file)
        if file.name in {'sc1_14_build2.ydr','sc1_14_grnd_02.ydr'}:
            # A decoder with no GTA name table returns a literal hash for normal_spec.
            # Writing the hash string as a name would point the game at a different shader.
            normals = [s for s in obj.shader_group.shaders if s.preset_filename=='normal_spec.sps']
            assert normals and all(str(s.name).lower() in {'normal_spec','hash_38dd00df'} for s in normals),file
        triangles = 0
        for models in obj.models.values():
            for model in models:
                for mesh in model.geometries:
                    coords = np.asarray(mesh.vertex_buffer['Position'],dtype=float)
                    indices = np.asarray(mesh.index_buffer).reshape(-1,3)
                    assert np.isfinite(coords).all() and len(indices) and 0 <= indices.min() <= indices.max() < len(coords), file
                    assert 0 <= mesh.shader_index < len(obj.shader_group.shaders), file
                    points = coords[indices]
                    cross = np.cross(points[:,1] - points[:,0], points[:,2] - points[:,0])
                    assert np.min(np.linalg.norm(cross,axis=1)) > 1e-11, file
                    triangles += len(indices)
        drawables[file.stem] = triangles
    assert len(drawables)==30
    for suffix in ('.ybn','.ydd','.ytd','.ymap','.ytyp'):
        for file in stream.rglob('*' + suffix):
            assert szio.try_load_asset(file) is not None, file
    mlo = next(a for a in szio.try_load_asset(stream/'gabagool_sons_mlo.ytyp').archetypes if a.name=='gs_longpig_int')
    assert len(mlo.entities)==449 and len(mlo.portals)==5
    assert sorted(r.name for r in mlo.rooms)==['gs_front','limbo']
    assert {s.name for s in mlo.entity_sets}=={'lp_open','lp_closed'}
    shelf = inspect(resource, read_actual_packs(Path(os.environ['GTA_ROOT'])), True)
    assert shelf['packs']==70 and shelf['lod_distances_m']==[25.]
    return {'models':drawables,'entities':len(mlo.entities),'portals':len(mlo.portals),'shelf':shelf}


if __name__=='__main__':
    resource,report = (Path(x) for x in sys.argv[sys.argv.index('--')+1:])
    report.write_text(json.dumps(check(resource), indent=2), encoding='utf8')
    print('Verified native resource',resource)
