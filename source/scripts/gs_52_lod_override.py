# LONG PIG 0.3.1-o (revision):
# the removed taco kiosk still showed from far away (vanilla LOD / SLOD1 models). Minimal override copies of the two LOD
# dictionaries, kiosk triangles removed (inside KIOSK_BOX, reaching above z 24), nothing else changed:
#   sc1_14_slod1_children.ydd            (sc1_14_build2_lod: 100 .. 300 m)
#   <dict of sc1_14_slod1>.ydd           (sc1_14_slod1: 300 .. 450 m)
# The roof billboard LOD (sc1_14_bb_meltdown_lod / _slod) gets the LONG PIG picture if its texture is embedded.
# Game files are only read; results go to source/lod_override/ (the build copies them into stream/vanilla_override).
import os, sys, json, traceback
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion
ROOT = Path(os.environ.get("GS_ROOT"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
sys.path.insert(0, str(ROOT / "source" / "scripts"))
import importlib, gs_overrides as G
importlib.reload(G)
OUT = ROOT / "source" / "lod_override"
OUT.mkdir(parents=True, exist_ok=True)
TARGET = [AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8)]
R = {"dicts": {}, "errors": [], "go": False}


def joaat(s):
    h = 0
    for c in s.lower().encode():
        h = (h + c) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= h >> 11; h = (h + (h << 15)) & 0xFFFFFFFF
    return h


POS = {"sc1_14_build2_lod": (423.11728, -1910.3502, 32.3534), "sc1_14_grnd_02_lod": (441.1034, -1894.213, 24.759754),
       "sc1_14_build1_lod": (465.78632, -1879.2302, 33.456093), "sc1_14_slod1": (441.1536, -1894.1444, 32.76549),
       "sc1_14_sc1_emissive_sc1_14b_lod": (423.11728, -1910.3502, 32.3534), "sc1_14_sc1_emissive_slod": (441.1536, -1894.1444, 32.76549)}
KEY = {("hash_%08X" % joaat(n)): n for n in list(POS) + ["sc1_14_bb_meltdown_lod", "sc1_14_bb_meltdown_slod"]}
EXPECT = {"sc1_14_build2_lod": (250, 340), "sc1_14_slod1": (4, 400)}


def cut(d, ent):
    ent = np.array(ent)
    per, total = [], 0
    for lod, models in d.models.items():
        for m in models:
            for g in m.geometries:
                pos = np.array(g.vertex_buffer["Position"], dtype=float).reshape(-1, 3) + ent
                ib = np.asarray(g.index_buffer).reshape(-1, 3)
                T = pos[ib]
                ins = ((T[:, :, :2] > G.KIOSK_BOX[0]) & (T[:, :, :2] < G.KIOSK_BOX[1])).all(axis=(1, 2))
                kill = ins & (T[:, :, 2].max(1) > G.KIOSK_ZKEEP)
                per.append([int(len(ib)), int(kill.sum())])
                if kill.any():
                    g.index_buffer = ib[~kill].reshape(-1).astype(np.asarray(g.index_buffer).dtype)
                    total += int(kill.sum())
    return total, per


def tris(d):
    return sum(len(np.asarray(g.index_buffer)) // 3 for lod, ms in d.models.items() for m in ms for g in m.geometries)


# The verified Legacy dictionaries reside together in the base game's SCentral block.
dictionary = VPath(str(GTA / "x64k.rpf/levels/gta5/_citye/scentral_01/scentral.rpf"))
names = ("sc1_14_bb_meltdown_slod_children.ydd", "sc1_14_slod1_children.ydd",
         "sc1_lod_14_29_31_32_33_children.ydd")
found = {name: [dictionary / name] for name in names}
ok_all = True
for nm, paths in sorted(found.items()):
    try:
        a = szio.try_load_asset(paths[-1])                      # last = newest patch level
        keys = [str(k) for k in a.drawables]
        hits = [k for k in keys if k in KEY]
        if not hits:
            continue
        rec = {"source": paths[-1].as_posix(), "all_sources": [p.as_posix() for p in paths], "drawables": {}}
        changed = False
        for k in keys:
            d = a.drawables[k]
            name = KEY.get(k, k)
            dr = {"tris_before": tris(d)}
            if name in POS and name in EXPECT:
                n, per = cut(d, POS[name])
                lo, hi = EXPECT[name]
                dr.update(removed=n, per_geometry=per, expected=[lo, hi])
                if not (lo <= n <= hi):
                    raise RuntimeError(f"{name}: removed {n}, expected {lo}..{hi} - source differs, abort")
                changed = changed or n > 0
            if name.startswith("sc1_14_bb_meltdown"):
                emb = list(d.shader_group.embedded_textures or [])
                dr["embedded"] = [[t, int(d.shader_group.embedded_textures[t].width), int(d.shader_group.embedded_textures[t].height)] for t in emb]
                dr["shader_tex"] = [[str(q.value) for q in s.parameters if isinstance(q.value, str)] for s in d.shader_group.shaders]
                if not emb and name == "sc1_14_bb_meltdown_lod":
                    # the LOD quad samples the shared wall atlas -> own embedded texture (cloned from the HD billboard's
                    # embedded texture object), UVs stretched to the full picture, orientation kept
                    import dataclasses as _dc
                    hd = szio.try_load_asset(ROOT / "reference_vanilla" / "sc1_14" / "sc1_14_bb_meltdown.ydr")
                    hd = hd.drawable if hasattr(hd, "drawable") and hd.drawable is not None else hd
                    hname = list(hd.shader_group.embedded_textures)[0]
                    ht = hd.shader_group.embedded_textures[hname]
                    raw = (ROOT / "source" / "textures" / "v031" / "lod" / "lp_billboard_256x128.dds").read_bytes()
                    src = type(ht.data)("lp_bb_lod.dds", raw)
                    nt = _dc.replace(ht, name="lp_bb_lod", data=src, width=256, height=128)
                    try:
                        d.shader_group.embedded_textures["lp_bb_lod"] = nt
                    except Exception:
                        d.shader_group.embedded_textures = {"lp_bb_lod": nt}
                    sh = d.shader_group.shaders[0]
                    plist = list(sh.parameters)
                    dr["param_names"] = [[str(q.name), type(q).__name__, str(q.value)[:30]] for q in plist]
                    for i_, q in enumerate(plist):
                        if isinstance(q.value, str) and q.value.lower() == "sc1_14_wall_lod":
                            try:
                                plist[i_] = _dc.replace(q, value="lp_bb_lod")
                            except Exception:
                                q.value = "lp_bb_lod"
                    try:
                        sh.parameters = plist
                    except Exception as e_:
                        dr["param_set_error"] = str(e_)
                    hv = None
                    for lod_, ms_ in hd.models.items():
                        for m_ in ms_:
                            for g_ in m_.geometries:
                                hu = np.array(g_.vertex_buffer["TexCoord0"], float).reshape(-1, 2)
                                hp = np.array(g_.vertex_buffer["Position"], float).reshape(-1, 3)
                                if hv is None or len(hu) > len(hv[0]):
                                    hv = (hu, hp)
                    for lod_, ms_ in d.models.items():
                        for m_ in ms_:
                            for g_ in m_.geometries:
                                vb = np.asarray(g_.vertex_buffer).copy()
                                uv = np.array(vb["TexCoord0"], float).reshape(-1, 2)
                                P_ = np.array(vb["Position"], float).reshape(-1, 3)
                                # each LOD corner takes the UV of the nearest HD picture vertex (same entity origin)
                                new = np.array([hv[0][int(np.argmin(np.linalg.norm(hv[1] - p_, axis=1)))] for p_ in P_])
                                dr["lod_uv_before"] = uv.round(3).tolist()
                                dr["lod_uv_after"] = new.round(3).tolist()
                                dr["lod_pos"] = P_.round(2).tolist()
                                vb["TexCoord0"] = new.astype(vb["TexCoord0"].dtype)
                                g_.vertex_buffer = vb
                    dr["retexture"] = "own embedded lp_bb_lod 256x128"
                    changed = True
                if emb:
                    t0 = d.shader_group.embedded_textures[emb[0]]
                    w, h = int(t0.width), int(t0.height)
                    dds = ROOT / "source" / "textures" / "v031" / "lod" / f"lp_billboard_{w}x{h}.dds"
                    if dds.exists() and len(emb) == 1:
                        dr["retexture"] = G.retexture_billboard(d, dds, w, h)
                        changed = True
                    else:
                        dr["retexture"] = f"skipped (no {dds.name} or {len(emb)} textures)"
            dr["tris_after"] = tris(d)
            rec["drawables"][name] = dr
        if changed:
            stem = nm[:-4]
            szio.save_asset(a, TARGET, OUT, stem)
            b = szio.try_load_asset(OUT / nm)
            rec["reload"] = {KEY.get(str(k), str(k)): tris(b.drawables[k]) for k in b.drawables}
            rec["reload_tex"] = {KEY.get(str(k), str(k)): [list(b.drawables[k].shader_group.embedded_textures or []), [[str(q.value) for q in s_.parameters if isinstance(q.value, str)] for s_ in b.drawables[k].shader_group.shaders]] for k in b.drawables if KEY.get(str(k), "").startswith("sc1_14_bb")}
            rec["file"] = nm
            rec["bytes"] = [(OUT / nm).stat().st_size]
            good = all(rec["reload"][n] == v["tris_after"] for n, v in rec["drawables"].items())
            rec["ok"] = bool(good)
            ok_all = ok_all and good
        R["dicts"][nm] = rec
    except Exception:
        ok_all = False
        R["errors"].append(f"{nm}: " + traceback.format_exc()[-500:])
R["go"] = bool(ok_all and not R["errors"] and any(v.get("file") for v in R["dicts"].values()))
(ROOT / "docs" / "_raw" / "lod_override_result.json").write_text(json.dumps(R, indent=1, default=str), encoding="utf-8")
print("[gs_lod] DONE go =", R["go"], {k: v.get("file") for k, v in R["dicts"].items()}, len(R["errors"]))
