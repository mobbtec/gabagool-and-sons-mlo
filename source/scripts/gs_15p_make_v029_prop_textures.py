# LONG PIG v0.2.9 — small streaming copies for the spawned props (gs_44_build_props.py), so each ticket / the credenza
# leaf does not embed the whole 1024x512 sign atlas or the 1024 px walnut:
#   lp8_props.dds           512x256 DXT1: ticket1..3 (0..288 x 0..192), paper (288..320 x 0..32), brass (320..352 x 0..32)
#                           -> crops of our own procedural lp8_atlas.png (gs_15n_make_v029_textures.py)
#   lp_wood_walnut_512.dds  512 px DXT1 copy of our own lp_wood_walnut.png (Lanczos)
#   python gs_15p_make_v029_prop_textures.py [<project_root>]
import sys, json, hashlib
from pathlib import Path
from PIL import Image

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds  # noqa: E402

V29 = ROOT / "source" / "textures" / "v029"
SLICE = ROOT / "source" / "textures" / "slice"
REG = json.loads((V29 / "lp8_atlas_regions.json").read_text(encoding="utf-8"))["regions"]
PROPS_LAYOUT = {"ticket1": (0, 0), "ticket2": (96, 0), "ticket3": (192, 0), "paper": (288, 0), "brass": (320, 0)}

atlas = Image.open(V29 / "lp8_atlas.png").convert("RGB")
out = Image.new("RGB", (512, 256), (232, 226, 210))
regions = {}
for key, (x, y) in PROPS_LAYOUT.items():
    x0, y0, x1, y1 = REG[key]
    out.paste(atlas.crop((x0, y0, x1, y1)), (x, y))
    regions[key] = [x, y, x + (x1 - x0), y + (y1 - y0)]
out.save(V29 / "lp8_props.png")
info1 = gs_dds.convert(V29 / "lp8_props.png", V29 / "lp8_props.dds", "DXT1")
(V29 / "lp8_props_regions.json").write_text(json.dumps({"size": [512, 256], "regions": regions}, indent=1), encoding="utf-8")

wal = Image.open(SLICE / "lp_wood_walnut.png").convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
wal.save(V29 / "lp_wood_walnut_512.png")
info2 = gs_dds.convert(V29 / "lp_wood_walnut_512.png", V29 / "lp_wood_walnut_512.dds", "DXT1")

rep_p = V29 / "lp8_textures_report.json"
rep = json.loads(rep_p.read_text(encoding="utf-8"))
rep["textures"] = [t for t in rep["textures"] if t["name"] not in ("lp8_props", "lp_wood_walnut_512")]
for name, size, src, ops in (("lp8_props", [512, 256], ["source/textures/v029/lp8_atlas.png"], "crops of our own sign atlas"),
                             ("lp_wood_walnut_512", [512, 512], ["source/textures/slice/lp_wood_walnut.png"],
                              "streaming copy of our own walnut (1024 -> 512, Lanczos)")):
    data = (V29 / f"{name}.dds").read_bytes()
    rep["textures"].append({"name": name, "file": f"{name}.dds", "size": size, "format": "DXT1", "role": "diffuse",
                            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "derived_from": src,
                            "origin": "original_procedural", "operations": ops})
    print("TEX", name, size, len(data))
rep_p.write_text(json.dumps(rep, indent=1), encoding="utf-8")
print("GS15P_DONE")
