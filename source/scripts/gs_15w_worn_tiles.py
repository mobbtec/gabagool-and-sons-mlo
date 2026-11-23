# LONG PIG 1.1.1: worn tile with missing pieces everywhere (owner 2026-11-16). Same CC0 source as the blue counter wall:
# ambientCG "Tiles135C" (CC0), Tiles135C_1K-JPG.zip. Colour grade only - the damage / grime of the photo is kept:
#   lp10_tile_red   oxblood glaze (hall wainscot, sills)      lp10_tile_dirty  yellowed off-white glaze (kitchen, WC walls)
import sys, json, hashlib, zipfile, io
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
OUT = ROOT / "source" / "textures" / "v031"
zp = ROOT / "assets" / "cc0" / "_downloads" / "Tiles135C_1K-JPG.zip"
z = zipfile.ZipFile(zp)
col = next(x for x in z.namelist() if "_Color" in x)
c = np.asarray(Image.open(io.BytesIO(z.read(col))).convert("RGB").resize((512, 512), Image.LANCZOS), float)
r, g, b = c[..., 0], c[..., 1], c[..., 2]
glaze = np.clip((b - r - 6.0) / 18.0, 0.0, 1.0)[..., None]          # 1 on blue glaze, 0 on grout / bare wall / dirt
lum = (0.3 * r + 0.59 * g + 0.11 * b)[..., None] / 70.0                     # shade of the glaze (about 1.0 on a clean tile)
rep = {}
def save(name, arr):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    data = gs_dds.encode_dds(im, "DXT1")
    (OUT / f"{name}.dds").write_bytes(data)
    rep[name] = {"size": [512, 512], "format": "DXT1", "sha256": hashlib.sha256(data).hexdigest(), "derived_from": "Tiles135C",
                 "source": "https://ambientcg.com/get?file=Tiles135C_1K-JPG.zip", "licence": "CC0 1.0 (ambientCG)"}
    return im
red = save("lp10_tile_red", c * (1 - glaze) + np.array([80.0, 28.0, 28.0]) * lum * glaze)
dirty = save("lp10_tile_dirty", c * (1 - glaze) * 0.95 + np.array([196.0, 186.0, 160.0]) * np.clip(lum, 0.55, 1.15) * glaze)
for nm in ("lp10_tile_dirty_n", "lp10_tile_dirty_s"):                     # BOH specs expect <name>_n / <name>_s
    (OUT / f"{nm}.dds").write_bytes((OUT / nm.replace("dirty", "blue")).with_suffix(".dds").read_bytes()) if False else \
        (OUT / f"{nm}.dds").write_bytes((OUT / (nm.replace("dirty", "blue") + ".dds")).read_bytes())
sheet = Image.new("RGB", (1024, 512)); sheet.paste(red, (0, 0)); sheet.paste(dirty, (512, 0)); sheet.save(OUT / "_worn_tiles_prev.jpg", quality=88)
(OUT / "cc0_v111_report.json").write_text(json.dumps(rep, indent=1)); print(list(rep))
