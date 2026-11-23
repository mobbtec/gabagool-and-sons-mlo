# LONG PIG — v0.2.9 audit fix: the bright PINK surfaces in the offline previews are vanilla props whose textures were never
# copied into the INTERNAL preview reference (Blender paints a missing image texture magenta). In FiveM those props use
# their own game textures, so this is a preview-only artefact. This script (read-only access to the game archives) writes,
# for every vanilla archetype the MLO uses or may use in v0.2.9:
#   reference_vanilla/catalogue/<name>.ydr.xml   (if missing)   +   reference_vanilla/catalogue/<name>/<texture>.dds
# and the HIGH-LOD bounds to docs/_raw/vanilla_preview_v029.json. Nothing of this is shipped with the resource.
# Blender 5.1 console on the PC:
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_42_preview_textures.py", encoding="utf-8").read())
import os, json, time, traceback
from pathlib import Path
import numpy as np
import szio
from szio.vfs import VPath
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
GTA = Path(os.environ.get("GTA_ROOT", r"D:\Gamess\GTAV"))
OUT = ROOT / "reference_vanilla" / "catalogue"
LOG = ROOT / "docs" / "_raw" / "vanilla_preview_v029.json"
NAMES_FILE = ROOT / "source" / "scripts" / "gs_42_names.txt"
BUDGET = float(globals().get("GS_BUDGET", 1500))          # seconds for the whole run
BUDGET_GLOBAL = float(globals().get("GS_BUDGET_GLOBAL", 300))

names = [l.strip() for l in NAMES_FILE.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]

# ---- name -> archive path from every earlier read-only scan
paths = {}


def harvest(o):
    if isinstance(o, dict):
        n, p = o.get("name"), o.get("path")
        if isinstance(n, str) and isinstance(p, str) and p.lower().endswith((".ydr", ".yft")):
            n = n.lower()
            for ext in (".ydr", ".yft"):
                if n.endswith(ext):
                    n = n[:-4]
            paths.setdefault(n, p)
        for v in o.values():
            harvest(v)
    elif isinstance(o, list):
        for v in o:
            harvest(v)


for f in sorted((ROOT / "docs" / "_raw").glob("*.json")):
    if f.stat().st_size > 30_000_000 or f.name == LOG.name:
        continue
    try:
        harvest(json.loads(f.read_text(encoding="utf-8")))
    except Exception as e:
        print("[gs42] skip", f.name, repr(e)[:80], flush=True)

log = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "props": [], "errors": [], "not_found": []}
ytd_cache = {}
t0 = time.time()


def rpf_root(posix):
    i = posix.lower().rfind(".rpf/")
    return posix[:i + 4] if i >= 0 else None


def ytds_under(root):
    if root not in ytd_cache:
        try:
            ytd_cache[root] = [p for p in VPath(root).rglob("*") if p.name.lower().endswith(".ytd")]
        except Exception:
            ytd_cache[root] = []
    return ytd_cache[root]


def save_tex(tdir, t, tex):
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / f"{t}.dds").write_bytes(tex.data.read_bytes())


pending = {}          # texture -> [dirs] still missing after the local search (for the global pass)
OUT.mkdir(parents=True, exist_ok=True)
for name in names:
    if time.time() - t0 > BUDGET:
        log["errors"].append("budget reached before " + name)
        break
    rec = {"name": name, "path": paths.get(name)}
    try:
        if not rec["path"]:
            log["not_found"].append(name)
            continue
        a = szio.try_load_asset(VPath(rec["path"]))
        d = a.drawable if hasattr(a, "drawable") and a.drawable is not None else a
        if not (OUT / f"{name}.ydr.xml").exists():
            try:
                szio.save_asset(d, [AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)], OUT, name)
                rec["xml"] = "new"
            except Exception as e:
                log["errors"].append(f"cwxml {name}: {e!r}"[:300])
        lod = min(d.models.keys(), key=lambda k: int(k))
        P = np.concatenate([np.array(g.vertex_buffer["Position"], float).reshape(-1, 3) for m in d.models[lod] for g in m.geometries])
        rec["min"], rec["max"] = P.min(0).round(4).tolist(), P.max(0).round(4).tolist()
        rec["tris"] = int(sum(len(g.index_buffer) // 3 for m in d.models[lod] for g in m.geometries))
        want = sorted({p.value for sh in (d.shader_group.shaders if d.shader_group else []) for p in sh.parameters
                       if isinstance(p.value, str) and p.value})
        tdir = OUT / name
        have = {f.stem.lower() for f in tdir.glob("*.dds")} if tdir.is_dir() else set()
        left = [t for t in want if t.lower() not in have]
        emb = d.shader_group.embedded_textures if d.shader_group else {}
        for t in list(left):
            tex = emb.get(t) if emb else None
            if tex is not None and tex.data is not None:
                save_tex(tdir, t, tex); left.remove(t)
        root = rpf_root(rec["path"])
        if left and root:
            folder = rec["path"].rsplit("/", 1)[0].lower()
            stem = name.lower()
            ytds = sorted(ytds_under(root), key=lambda p: (0 if p.name.lower().startswith(stem) else 1,
                                                          0 if p.as_posix().lower().startswith(folder) else 1))
            for y in ytds:
                if not left or time.time() - t0 > BUDGET:
                    break
                try:
                    texs = getattr(szio.try_load_asset(y), "textures", {}) or {}
                    low = {k.lower(): v for k, v in texs.items()}
                    for t in list(left):
                        tex = low.get(t.lower())
                        if tex is not None and tex.data is not None:
                            save_tex(tdir, t, tex); left.remove(t)
                except Exception as e:
                    log["errors"].append(f"{y.name}: {e!r}"[:200])
        for t in left:
            pending.setdefault(t.lower(), []).append(str(tdir))
        rec["textures"] = want
        rec["missing_after_local"] = left
    except Exception:
        log["errors"].append(f"{name}: " + traceback.format_exc()[-300:])
    log["props"].append(rec)
    print("[gs42]", name, "tex", len(rec.get("textures", [])), "missing", len(rec.get("missing_after_local", [])),
          round(time.time() - t0), "s", flush=True)

# ---- global pass for shared texture dictionaries (prop_base_white_01, prop_metal_01 ...): generic prop txds
t1 = time.time()
if pending:
    roots = []
    for base in ("x64c.rpf/levels/gta5/props", "x64e.rpf/levels/gta5/props", "x64i.rpf/levels/gta5/props"):
        roots.append((GTA / base.split("/")[0]).as_posix() + "/" + "/".join(base.split("/")[1:]))
    seen = 0
    for r in roots:
        if not pending or time.time() - t1 > BUDGET_GLOBAL:
            break
        try:
            for y in VPath(r).rglob("*.ytd"):
                if not pending or time.time() - t1 > BUDGET_GLOBAL:
                    break
                seen += 1
                try:
                    texs = getattr(szio.try_load_asset(y), "textures", {}) or {}
                    for k, tex in texs.items():
                        dirs = pending.get(k.lower())
                        if dirs and tex is not None and tex.data is not None:
                            for dd in dirs:
                                save_tex(Path(dd), k, tex)
                            del pending[k.lower()]
                except Exception:
                    pass
        except Exception as e:
            log["errors"].append(f"global {r}: {e!r}"[:200])
    log["global_ytds_seen"] = seen
log["still_missing"] = sorted(pending)
log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
LOG.write_text(json.dumps(log, indent=1), encoding="utf-8")
print("GS42_DONE props=%d not_found=%d still_missing_tex=%d errors=%d secs=%d" % (
    len(log["props"]), len(log["not_found"]), len(pending), len(log["errors"]), time.time() - t0), flush=True)
