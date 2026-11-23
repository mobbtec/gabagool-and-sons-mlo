"""Reopen the native release and check placement fingerprints, all model indices and all GTA resource headers."""
from pathlib import Path
from collections import Counter
import dataclasses,hashlib,enum,json,sys,struct
import numpy as np,szio

def name_dict(o,exclude=()):
    return {f.name:getattr(o,f.name) for f in dataclasses.fields(o) if f.name not in exclude}

def canon(o):
    if o is None or isinstance(o,(str,int,float,bool)):return o
    if isinstance(o,enum.Enum):return o.value
    if dataclasses.is_dataclass(o):return canon(name_dict(o))
    if isinstance(o,dict):return {str(k):canon(v) for k,v in o.items()}
    if isinstance(o,np.generic):return o.item()
    return [canon(v) for v in o]
def digest(o):return json.dumps(canon(o),sort_keys=True)
def entity(e,drop=()):
    # Scene GUIDs can be regenerated for a fresh source build; compare all spatial,
    # draw and extension fields which carry player-visible behaviour.
    return digest(name_dict(e,('guid',)+drop))
def phys(p):
    magic,ver,virt,gpu=struct.unpack('<4sIII',p.read_bytes()[:16]);assert magic==b'RSC7'
    vals=((27,1,0),(26,1,1),(25,1,2),(24,1,3),(17,127,4),(11,63,5),(7,15,6),(5,3,7),(4,1,8))
    return (512<<(gpu&15))*sum(((gpu>>s)&mask)<<b for s,mask,b in vals)
def mlo(root):
    y=szio.try_load_asset(root/'stream/gabagool_sons_mlo.ytyp')
    return y,next(a for a in y.archetypes if a.name=='gs_longpig_int')
def is_pack(n):return n=='v_ret_ml_cigs' or n in ['v_ret_ml_cigs'+str(k) for k in range(2,7)]
def real_stock(e):return e.archetype_name.startswith(('v_ret_ml_chips','v_ret_ml_sweet')) or is_pack(e.archetype_name)
def goods(es):return Counter(entity(e,('lod_dist',) if real_stock(e) else ()) for e in es if not is_pack(e.archetype_name))
def audit(oldroot,newroot):
    y0,a=mlo(oldroot);y1,b=mlo(newroot)
    assert {x.name for x in y0.archetypes}=={x.name for x in y1.archetypes}
    assert len(b.entities)-len(a.entities)==14
    assert goods(a.entities)==goods(b.entities)
    stock=[e for e in b.entities if real_stock(e)]
    assert all(e.lod_dist==25 for e in stock) and all(e.lod_dist==55 for e in a.entities if real_stock(e))
    assert [r.name for r in a.rooms]==[r.name for r in b.rooms]
    for old,r in zip(a.rooms,b.rooms):
        assert digest(name_dict(old,('attached_objects',)))==digest(name_dict(r,('attached_objects',)))
        assert goods([a.entities[i] for i in old.attached_objects])==goods([b.entities[i] for i in r.attached_objects])
    for old,p in zip(a.portals,b.portals,strict=True):
        assert digest(name_dict(old,('attached_objects',)))==digest(name_dict(p,('attached_objects',)))
        assert [entity(a.entities[i]) for i in old.attached_objects]==[entity(b.entities[i]) for i in p.attached_objects]
    for s,t in zip(a.entity_sets,b.entity_sets,strict=True):
        assert s.name==t.name and s.locations==t.locations and [entity(e) for e in s.entities]==[entity(e) for e in t.entities]
    models={}
    for p in (newroot/'stream').rglob('*.ydr'):
        g=szio.try_load_asset(p);assert g is not None,p
        tri=deg=0
        for lod,ml in g.models.items():
            for md in ml:
                for geom in md.geometries:
                    ib=geom.index_buffer.reshape(-1,3); v=geom.vertex_buffer
                    assert len(ib) and ib.max()<len(v) and geom.shader_index<len(g.shader_group.shaders)
                    points=np.asarray(v['Position'],dtype=float)
                    assert np.isfinite(points).all()
                    coords=points[ib]
                    areas=np.linalg.norm(np.cross(coords[:,1]-coords[:,0],coords[:,2]-coords[:,0]),axis=1)
                    tri+=len(ib);deg+=int(np.sum(areas<1e-11))
        models[p.stem]=dict(tris=tri,degenerate=deg,physical=phys(p),lights=len(g.lights or []))
    assert all(rec['physical']<16*1048576 for rec in models.values())
    assert not models['gs_proto_shell']['degenerate']
    assert not models['gs_v26_market']['degenerate']
    other={}
    for suffix in ['*.ytyp','*.ybn','*.ymap','*.ydd','*.ytd']:
        for p in (newroot/'stream').rglob(suffix):
            asset=szio.try_load_asset(p);assert asset is not None,p
            other[p.name]=type(asset).__name__
    return dict(entities_before=len(a.entities),entities_after=len(b.entities), native_ydr=models,other_assets=other,short_lod=len(stock),
                portals=len(b.portals),rooms=[r.name for r in b.rooms],
                sets={s.name:len(s.entities) for s in b.entity_sets})

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    out=audit(Path(args[0]),Path(args[1]))
    Path(args[2]).write_text(json.dumps(out,indent=2),encoding='utf8')
    print('FINAL_NATIVE_OK',out['short_lod'],len(out['native_ydr']),out['sets'],{k:v['degenerate'] for k,v in out['native_ydr'].items() if v['degenerate']})
