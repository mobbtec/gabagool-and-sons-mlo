# LONG PIG v0.2.9 — provenance: adds the v0.2.9 own assets (procedural textures, synthesized sounds) to assets/registry.json
# ('derived') and every vanilla archetype the v0.2.9 MLO references by name to 'vanilla_prop_allowlist' (names only, no game
# file is shipped). Run from source/scripts with the kit importable:  python gs_15q_register_v029.py [<project_root>]
import sys, json, hashlib, datetime
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
REG = ROOT / "assets" / "registry.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gs_v029_kit as K  # noqa: E402

today = datetime.date.today().isoformat()
reg = json.loads(REG.read_text(encoding="utf-8"))
have = {r["id"] for r in reg["derived"] + reg["sources"]}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def own(rid, path, origin, derived_from, script, params):
    p = ROOT / path
    if rid in have or not p.is_file():
        return 0
    reg["derived"].append({"id": rid, "path": path, "sha256": sha(p), "bytes": p.stat().st_size, "origin": origin,
                           "derived_from": derived_from,
                           "own": {"author": "Pryir / Claude", "tool": "Python (Pillow, numpy, scipy, ffmpeg), gs_dds, DejaVu fonts",
                                   "script": script, "script_version": "0.2.9"},
                           "build": {"script": script, "params": params}, "added": today})
    return 1


n = 0
n += own("lp.tex.lp8_atlas", "source/textures/v029/lp8_atlas.dds", "ORIGINAL", [], "source/scripts/gs_15n_make_v029_textures.py",
         {"size": [1024, 512], "format": "DXT1", "content": "signs, labels, tickets, ledgers, cartons (procedural + DejaVu text)"})
n += own("lp.tex.lp8_props", "source/textures/v029/lp8_props.dds", "DERIVED_OWN", ["lp.tex.lp8_atlas"],
         "source/scripts/gs_15p_make_v029_prop_textures.py", {"size": [512, 256], "format": "DXT1", "operations": "crops"})
n += own("lp.tex.lp_wood_walnut_512", "source/textures/v029/lp_wood_walnut_512.dds", "DERIVED_OWN", ["lp.tex.lp_wood_walnut"],
         "source/scripts/gs_15p_make_v029_prop_textures.py", {"size": [512, 512], "format": "DXT1", "operations": "resize"})
for s in ("lp_bell", "lp_printer", "lp_hood", "lp_switch", "lp_creak"):
    n += own(f"lp.snd.{s}", f"source/fivem/gabagool_sons_mlo/html/sfx/{s}.ogg", "ORIGINAL", [],
             "source/scripts/gs_15o_make_rest_audio.py", {"format": "ogg vorbis q4, mono 44.1 kHz", "content": "numpy/scipy synthesis"})

names = {}
for e in K.vanilla_props():
    names.setdefault(e[0], []).append("prop")
for d in K.all_doors():
    names.setdefault(d[1], []).append("door")
for setn, ents in K.set_entities().items():
    for e in ents:
        if not e[0].startswith("gs_"):
            names.setdefault(e[0], []).append(setn)
allowed = {a["archetype"] for a in reg["vanilla_prop_allowlist"]}
added = 0
for nm in sorted(names):
    if nm in allowed:
        continue
    kinds = names[nm]
    use = f"v0.2.9 premium pass, {len(kinds)} placement(s) by archetype name ({', '.join(sorted(set(kinds)))})"
    reg["vanilla_prop_allowlist"].append({"archetype": nm, "use": use,
                                          "source_rpf": "game archive (see docs/_raw/vanilla_preview_v029.json)",
                                          "shipped": False, "added": today})
    added += 1
reg["updated"] = today
REG.write_text(json.dumps(reg, indent=1, ensure_ascii=False), encoding="utf-8")
print("GS15Q_DONE own", n, "allowlist +", added, "total", len(reg["vanilla_prop_allowlist"]))
