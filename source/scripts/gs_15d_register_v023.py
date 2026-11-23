# LONG PIG — register the v0.2.3 "90s lobby" sources / textures / vanilla prop references in assets/registry.json and
# regenerate the v0.2.3 section of assets/CREDITS.md. Pure Python.
#   python gs_15d_register_v023.py [<project_root>]
import sys, json, hashlib, datetime, re
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "scripts"))
import gs_v024_kit as K  # noqa: E402   (0.2.4: lobby + lounge; re-exports the 0.2.3 kit)

REG = ROOT / "assets" / "registry.json"
REP = ROOT / "source" / "textures" / "v023" / "lp3_textures_report.json"
MAN = ROOT / "assets" / "cc0" / "_downloads" / "fetch_manifest_v023.json"
r = json.loads(REG.read_text(encoding="utf-8"))
rep = json.loads(REP.read_text(encoding="utf-8"))
man = json.loads(MAN.read_text(encoding="utf-8")) if MAN.is_file() else {"files": []}
today = datetime.date.today().isoformat()
lic = {l["platform"]: l for l in man.get("licenses", [])}
TITLES = {"Tiles010": "Tiles 010", "PaintedBricks004": "Painted Bricks 004"}
for f in man.get("files", []):
    sid = f"cc0.{f['asset'].lower()}.{Path(f['file']).stem.lower()}"
    r["sources"] = [s for s in r["sources"] if s["id"] != sid]
    r["sources"].append({
        "id": sid, "path": f["file"], "sha256": f.get("sha256"), "bytes": f.get("bytes"), "origin": "CC0",
        "third_party": {"title": TITLES.get(f["asset"], f["asset"]), "author": "ambientCG (Lennart Demes)",
                        "url": f"https://ambientcg.com/a/{f['asset']}", "download_url": f["url"], "license": "CC0 1.0",
                        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                        "platform_license_page": "https://docs.ambientcg.com/license/",
                        "license_snapshot": lic.get("ambientcg", {}).get("file"),
                        "license_snapshot_sha256": lic.get("ambientcg", {}).get("sha256"), "retrieved": f.get("retrieved"),
                        "metadata_snapshot": f"assets/cc0/_downloads/info_{f['asset']}.json"},
        "approved": "user 2026-11-01 14:08 (chat): find the textures on the internet; files announced with size before download",
        "reviewed_by": "Claude (automated checks: size, sha256, license page)", "reviewed_on": today})
src_ids = {s["path"].split("/")[-1]: s["id"] for s in r["sources"]}
r["derived"] = [d for d in r["derived"] if not d["id"].startswith("lp.tex.lp3_")]
for t in rep["textures"]:
    p = ROOT / "source" / "textures" / "v023" / t["file"]
    data = p.read_bytes()
    derived = []
    for x in t["derived_from"]:
        z = x.split(":")[0].split("/")[-1]
        derived.append(src_ids.get(z, x))
    r["derived"].append({
        "id": f"lp.tex.{t['name']}", "path": f"source/textures/v023/{t['file']}", "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data), "origin": "CC0" if any(d.startswith("cc0.") for d in derived) else "ORIGINAL", "derived_from": derived,
        "own": {"author": "Pryir / Claude", "tool": "Python (Pillow, numpy), gs_dds, DejaVu fonts", "script": rep["script"],
                "script_version": rep["version"]},
        "build": {"script": rep["script"], "params": {"size": t["size"], "format": t["format"], "role": t["role"], "operations": t["operations"]}},
        "reviewed_by": "Claude (automated: sha256, provenance chain)", "reviewed_on": today})
allow = {a["archetype"]: a for a in r["vanilla_prop_allowlist"]}
uses = {}
for name, s, t, zb, yaw in K.vanilla_props():
    uses[name] = uses.get(name, 0) + 1
for name, n in sorted(uses.items()):
    if name not in allow:
        r["vanilla_prop_allowlist"].append({"archetype": name, "use": f"v0.2.3 90s lobby, {n} placement(s) by archetype name",
                                             "source_rpf": "game archive (see docs/_raw/vanilla_props_v023.json)", "shipped": False, "added": today})
    else:
        allow[name]["use"] = allow[name]["use"].split(" | v0.2.3")[0] + f" | v0.2.3: {n} placement(s)"
r["updated"] = today
REG.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")

cred = ROOT / "assets" / "CREDITS.md"
txt = cred.read_text(encoding="utf-8") if cred.is_file() else "# Credits\n"
txt = re.sub(r"\n## v0\.2\.3 90s lobby.*?(?=\n## |\Z)", "", txt, flags=re.S)
lines = ["", "## v0.2.3 90s lobby + v0.2.4 lounge (textures `source/textures/v023`)", "",
         "| Texture | Origin | Derived from |", "|---|---|---|"]
for t in rep["textures"]:
    lines.append(f"| {t['name']} | {'CC0 derivative' if t['derived_from'] else 'original (procedural / typographic)'} | {', '.join(t['derived_from']) or '—'} |")
lines += ["", "CC0 sources: ambientCG *Tiles 010*, *Painted Bricks 004* (Lennart Demes) — CC0 1.0.",
          "Fonts used inside the menu / mat images: DejaVu Sans (Bitstream Vera licence, free to embed).",
          "Vanilla GTA V props are referenced by archetype name only (nothing of Rockstar is shipped):",
          ", ".join(sorted(uses)) + ".", ""]
cred.write_text(txt.rstrip() + "\n" + "\n".join(lines), encoding="utf-8")
print("REGISTERED_V023", len(rep["textures"]), "textures,", len(man.get("files", [])), "sources,", len(uses), "vanilla archetypes")
