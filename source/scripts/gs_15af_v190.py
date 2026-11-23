# LONG PIG 1.9.0 textures: counter-top stone (ambientCG Marble009, CC0), tinted case glass, kitchen pass plate redraw.
import sys, json, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
OUT = ROOT / "source" / "textures" / "v190"; SRC = OUT / "src"
rep = {"source": {"asset": "Marble009", "url": "https://ambientcg.com/view?id=Marble009", "file": "Marble009_1K-JPG.zip", "licence": "CC0 1.0",
                  "sha256": hashlib.sha256((SRC / "Marble009_1K-JPG.zip").read_bytes()).hexdigest()}, "files": {}}
def save(name, img, fmt):
    data = gs_dds.encode_dds(img, fmt); (OUT / f"{name}.dds").write_bytes(data)
    rep["files"][name] = {"size": list(img.size), "format": fmt, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
col = Image.open(SRC / "Marble009_1K-JPG_Color.jpg").convert("RGB")
save("lp19_stone", col, "DXT1")                                   # 1024, unmodified colour
save("lp19_stone_n", Image.open(SRC / "Marble009_1K-JPG_NormalDX.jpg").convert("RGB").resize((512, 512), Image.LANCZOS), "DXT1")
rough = Image.open(SRC / "Marble009_1K-JPG_Roughness.jpg").convert("L").resize((256, 256), Image.LANCZOS)
save("lp19_stone_s", ImageOps.invert(rough).convert("RGB"), "DXT1")
save("lp19_case_glass", Image.new("RGBA", (64, 64), (172, 208, 198, 104)), "DXT5")     # was alpha 46: glass reads as glass
# kitchen pass plate (lp8 atlas region 768,384..1024,448): new enamel plate
p = ROOT / "source" / "textures" / "v029" / "lp8_atlas.png"
at = Image.open(p).convert("RGB"); d = ImageDraw.Draw(at)
x0, y0, x1, y1 = 768, 384, 1024, 448
d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=(232, 226, 208)); d.rectangle([x0 + 3, y0 + 3, x1 - 4, y1 - 4], outline=(104, 26, 30), width=2)
f = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 30)
w = d.textlength("ORDER UP", font=f); d.text((x0 + (256 - w) / 2, y0 + 10), "ORDER UP", font=f, fill=(104, 26, 30))
at.save(p); data = gs_dds.encode_dds(at, "DXT1"); (p.with_suffix(".dds")).write_bytes(data)
rep["files"]["lp8_atlas (pass_label redrawn)"] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
(OUT / "v190_textures_report.json").write_text(json.dumps(rep, indent=1)); print(json.dumps(rep["files"], indent=0)[:600])
