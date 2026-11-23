# LONG PIG — register the v0.2.6 finish-and-refine textures (source/textures/v026, gs_15i) and the vanilla prop references of the
# v0.2.6 kit in assets/registry.json; regenerate the v0.2.6 section of assets/CREDITS.md. Pure Python.
#   python gs_15j_register_v026.py [<project_root>]
import sys, json, hashlib, datetime, re
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "scripts"))
import gs_v026_kit as K  # noqa: E402

REG = ROOT / "assets" / "registry.json"
REP = ROOT / "source" / "textures" / "v026" / "lp5_textures_report.json"
r = json.loads(REG.read_text(encoding="utf-8"))
rep = json.loads(REP.read_text(encoding="utf-8"))
today = datetime.date.today().isoformat()
known = {d["path"]: d["id"] for d in r.get("derived", [])}
r["derived"] = [d for d in r["derived"] if not d["id"].startswith("lp.tex.lp5_")]
for t in rep["textures"]:
    p = ROOT / "source" / "textures" / "v026" / t["file"]   # .dds, or .png for the runtime floor-B comparison
    data = p.read_bytes()
    parents = []
    for x in t["derived_from"]:
        dds = x[:-4] + ".dds" if x.endswith(".png") else x
        parents.append(known.get(dds, known.get(x, x)))
    r["derived"].append({
        "id": f"lp.tex.{t['name']}", "path": f"source/textures/v026/{t['file']}", "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data), "origin": "DERIVED_OWN" if parents else "ORIGINAL", "derived_from": parents,
        "own": {"author": "Pryir / Claude", "tool": "Python (Pillow, numpy, scipy), gs_dds, DejaVu fonts", "script": rep["script"],
                "script_version": rep["version"]},
        "build": {"script": rep["script"], "params": {"size": t["size"], "format": t["format"], "role": t["role"], "operations": t["operations"]}},
        "reviewed_by": "Claude (automated: sha256, provenance chain)", "reviewed_on": today})
allow = {a["archetype"]: a for a in r["vanilla_prop_allowlist"]}
uses = {}
for name, s, t, zb, yaw in K.vanilla_props():
    uses[name] = uses.get(name, 0) + 1
for name, n in sorted(uses.items()):
    if name not in allow:
        r["vanilla_prop_allowlist"].append({"archetype": name, "use": f"v0.2.6 refine, {n} placement(s) by archetype name",
                                             "source_rpf": "game archive (see docs/_raw/vanilla_catalogue_v021.json)", "shipped": False, "added": today})
    else:
        allow[name]["use"] = allow[name]["use"].split(" | v0.2.6")[0] + f" | v0.2.6: {n} placement(s)"
for name in K.REMOVED:
    if name.endswith("*"):
        for a_ in allow:
            if a_.startswith(name[:-1]) and a_ not in uses:
                allow[a_]["use"] = allow[a_]["use"].split(" | v0.2.6")[0] + f" | v0.2.6: REMOVED ({K.REMOVED[name]})"
        continue
    if name in allow and name not in uses:
        allow[name]["use"] = allow[name]["use"].split(" | v0.2.6")[0] + f" | v0.2.6: REMOVED ({K.REMOVED[name]})"
r["updated"] = today
REG.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")

cred = ROOT / "assets" / "CREDITS.md"
txt = cred.read_text(encoding="utf-8") if cred.is_file() else "# Credits\n"
txt = re.sub(r"\n## v0\.2\.6 finish-and-refine.*?(?=\n## |\Z)", "", txt, flags=re.S)
lines = ["", "## v0.2.6 finish-and-refine (textures `source/textures/v026`)", "",
         "| Texture | Origin | Derived from |", "|---|---|---|"]
for t in rep["textures"]:
    lines.append(f"| {t['name']} | {'derivative of our own texture' if t['derived_from'] else 'original (procedural / typographic)'} | {', '.join(t['derived_from']) or '—'} |")
lines += ["", "All v0.2.6 textures are aged / resized versions of our earlier textures (CC0 or original) or new original work",
          "(blinds, troffer lenses, decals, wall atlas with renders of our own room; fonts: DejaVu). No third-party or Rockstar pixels.",
          "Vanilla GTA V props referenced by archetype name only (nothing of Rockstar is shipped):",
          ", ".join(sorted(uses)) + ".", "Client-side only (not in the map): " + K.FAN_MODEL + " (ceiling fans), prop_gumball_01/02 (outside).", ""]
cred.write_text(txt.rstrip() + "\n" + "\n".join(lines), encoding="utf-8")
print("REGISTERED_V026", len(rep["textures"]), "textures,", len(uses), "vanilla archetypes")
