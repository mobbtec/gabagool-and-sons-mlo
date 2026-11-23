"""Recess the exposed west end of the long cooler canopy inside the window jamb."""
from pathlib import Path
import sys
import numpy as np, szio
from szio.gta5 import AssetFormat, AssetVersion, AssetTarget

root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
from cleanup import capture, geometry_rows

def fix(src,dest):
    if src.resolve()==dest.resolve(): raise ValueError("Use a different output file")
    draw=szio.try_load_asset(src)
    found=0
    for key,geom in geometry_rows(draw):
        if key[:2]!=('HIGH',0) or geom.shader_index!=39:continue
        vb=geom.vertex_buffer.copy()
        xyz=vb['Position']
        x=np.isclose(xyz[:,0],-2.9,atol=0.00001,rtol=0)
        y=np.isclose(xyz[:,1,None],(6.26,6.94),atol=0.00001,rtol=0).any(axis=1)
        z=np.isclose(xyz[:,2,None],(2.285,2.92),atol=0.00001,rtol=0).any(axis=1)
        mask=x&y&z
        unique=np.unique(xyz[mask],axis=0)
        if len(unique)!=4: continue
        # Four box corners; update the vertex-attribute splits at their UV seams as well.
        xyz[mask,0]=-2.898
        geom.vertex_buffer=vb
        found+=1
        print('COOLER', key, int(mask.sum()), 'vertex records, four corners, .002 m clearance')
    if found!=1: raise ValueError(f"Expected one west canopy end, found {found}")
    expected=capture(draw)
    dest.parent.mkdir(parents=True,exist_ok=True)
    szio.save_asset(draw,[AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8)],dest.parent,dest.stem)
    decoded=szio.try_load_asset(dest)
    assert capture(decoded)==expected
    print('VERIFIED',sum(len(g.index_buffer)//3 for k,g in geometry_rows(draw)), 'triangles', len(expected[1]), 'textures', len(expected[2]),'lights')

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:]
    fix(*map(Path,args))
