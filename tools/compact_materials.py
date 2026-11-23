"""Remove shader slots never selected by any geometry or LOD in the packaged MLO.

Run with Blender/Sollumz. Pass an input FiveM resource, a separate resource output
directory and a JSON report path after '--'. Only changed YDRs are written.
"""
from pathlib import Path
import dataclasses, enum, hashlib, json, struct, sys
import numpy as np
import szio
from szio.gta5 import AssetFormat, AssetTarget, AssetVersion

def geom_records(d):
    for lod,models in d.models.items():
        for m in models:
            for g in m.geometries:
                yield lod,m,g

def to_value(x):
    if isinstance(x,enum.Enum):return x.value
    if dataclasses.is_dataclass(x):return {f.name:to_value(getattr(x,f.name)) for f in dataclasses.fields(x)}
    if isinstance(x,(str,int,float,bool)) or x is None:return x
    if isinstance(x,dict):return {str(k):to_value(v) for k,v in x.items()}
    return [to_value(v.item() if isinstance(v,np.generic) else v) for v in x]

def texture_refs(shaders):
    return {param.value.lower() for shader in shaders for param in shader.parameters if isinstance(param.value,str)}

def samples(d):
    # Test the live shader parameters and complete vertex/index data on every mesh,
    # independent of the new consecutive shader IDs. Preserve the raw DDS payload.
    sg=d.shader_group
    return dict(
        surfaces=[(lod.name,g.vertex_data_type.name,
                   hashlib.sha256(g.vertex_buffer.tobytes()).hexdigest(),
                   hashlib.sha256(g.index_buffer.tobytes()).hexdigest(),
                   to_value(sg.shaders[g.shader_index])) for lod,m,g in geom_records(d)],
        textures={n:hashlib.sha256(t.data.read_bytes()).hexdigest() for n,t in sg.embedded_textures.items()},
        lights=to_value(d.lights), lods=to_value(d.lod_thresholds))

def memory(path):
    magic,version,v,p=struct.unpack('<4sIII',path.read_bytes()[:16])
    assert magic==b'RSC7'
    shifts=[(27,1,0),(26,1,1),(25,1,2),(24,1,3),(17,127,4),(11,63,5),(7,15,6),(5,3,7),(4,1,8)]
    return (512<<(p&15))*sum(((p>>s)&mask)<<b for s,mask,b in shifts)

def pack(src,dst):
    a=szio.try_load_asset(src);sg=a.shader_group
    used=sorted({g.shader_index for _,_,g in geom_records(a)})
    if len(used)==len(sg.shaders):return None
    before=samples(a)
    kept=[sg.shaders[i] for i in used]
    unused_refs=texture_refs(sg.shaders)-texture_refs(kept)
    drops=sorted(n for n in sg.embedded_textures if n.lower() in unused_refs)
    count=len(sg.shaders)
    lookup={old:new for new,old in enumerate(used)}
    for _,_,g in geom_records(a):g.shader_index=lookup[g.shader_index]
    sg.shaders=kept
    for n in drops:
        del sg.embedded_textures[n]
        del before['textures'][n]
    dst.parent.mkdir(parents=True,exist_ok=True)
    szio.save_asset(a,[AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8)],dst.parent,dst.stem)
    again=szio.try_load_asset(dst)
    assert len(again.shader_group.shaders)==len(used)
    reread=samples(again)
    assert reread==before, (src.name,[k for k in before if before[k]!=reread[k]])
    assert memory(dst)<=memory(src)
    return dict(slots_before=count,slots_after=len(used),textures_removed=drops,
                gpu_before=memory(src),gpu_after=memory(dst),bytes_before=src.stat().st_size,bytes_after=dst.stat().st_size)

if __name__=='__main__':
    src,dst,report=[Path(v).resolve() for v in sys.argv[sys.argv.index('--')+1:]]
    assert src!=dst
    results={}
    for f in sorted((src/'stream/mlo').glob('*.ydr')):
        result=pack(f,dst/'stream/mlo'/f.name)
        if result:results[f.name]=result
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(results,indent=2),encoding='utf8')
    print('VERIFIED_NATIVE_MATERIALS',json.dumps(results))
