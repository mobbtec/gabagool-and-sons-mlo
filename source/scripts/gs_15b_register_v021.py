# LONG PIG — register the v0.2.1 hero-kit textures and vanilla prop references in assets/registry.json
# (+ regenerate the v0.2.1 section of assets/CREDITS.md). Pure Python.
#   python gs_15b_register_v021.py [<project_root>]
import sys, json, hashlib, datetime, re
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "scripts"))
import gs_v021_kit as K  # noqa: E402

REG = ROOT / "assets" / "registry.json"
REP = ROOT / "source" / "textures" / "v021" / "lp2_textures_report.json"
r = json.loads(REG.read_text(encoding="utf-8"))
rep = json.loads(REP.read_text(encoding="utf-8"))
today = datetime.date.today().isoformat()
src_ids = {s["path"].split("/")[-1]: s["id"] for s in r["sources"]}

r["derived"] = [d for d in r["derived"] if not d["id"].startswith("lp.tex.lp2_")]
for t in rep["textures"]:
    p = ROOT / "source" / "textures" / "v021" / t["file"]
    data = p.read_bytes()
    derived = [src_ids.get(x, x) for x in t["derived_from"]]
    r["derived"].append({
        "id": f"lp.tex.{t['name']}", "path": f"source/textures/v021/{t['file']}", "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data), "origin": "CC0" if derived else "ORIGINAL", "derived_from": derived,
        "own": {"author": "Pryir / Claude", "tool": "Python (Pillow, numpy), gs_dds", "script": rep["script"], "script_version": rep["version"]},
        "build": {"script": rep["script"], "params": {"size": t["size"], "format": t["format"], "role": t["role"], "operations": t["operations"]}},
        "reviewed_by": "Claude (automated: sha256, provenance chain)", "reviewed_on": today})

allow = {a["archetype"]: a for a in r["vanilla_prop_allowlist"]}
uses = {}
for name, s, t, zb, yaw in K.vanilla_props():
    uses.setdefault(name, 0)
    uses[name] += 1
for name, n in sorted(uses.items()):
    if name not in allow:
        r["vanilla_prop_allowlist"].append({"archetype": name, "use": f"v0.2.1 hero build, {n} placement(s) by archetype name",
                                             "source_rpf": "game archive (see docs/_raw/vanilla_catalogue_v021.json)", "shipped": False, "added": today})
    else:
        allow[name]["use"] = allow[name]["use"].split(" | v0.2.1")[0] + f" | v0.2.1: {n} placement(s)"
r["updated"] = today
REG.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")

cred = ROOT / "assets" / "CREDITS.md"
txt = cred.read_text(encoding="utf-8") if cred.is_file() else "# Credits\n"
txt = re.sub(r"\n## v0\.2\.1 hero kit.*?(?=\n## |\Z)", "", txt, flags=re.S)
lines = ["", "## v0.2.1 hero kit (textures `source/textures/v021`)", "",
         "| Texture | Origin | Derived from |", "|---|---|---|"]
for t in rep["textures"]:
    lines.append(f"| {t['name']} | {'CC0 derivative' if t['derived_from'] else 'original (procedural)'} | {', '.join(t['derived_from']) or '—'} |")
lines += ["", "CC0 sources: Poly Haven *Kitchen Wood* (Rob Tuytel), *Brown Leather* — CC0 1.0, see sources in `assets/registry.json`.",
          "Vanilla GTA V props are referenced by archetype name only (nothing of Rockstar is shipped):",
          ", ".join(sorted(uses)) + ".", ""]
cred.write_text(txt.rstrip() + "\n" + "\n".join(lines), encoding="utf-8")
print("REGISTERED", len(rep["textures"]), "textures,", len(uses), "vanilla archetypes")
