# LONG PIG 1.2.1 colour regrades of existing CC0-derived textures (owner 2026-11-16):
#   lp11_board      PaintedWood003 - was a loud red in game -> dull dark oxblood-brown
#   lp10_tile_blue  Tiles135B glaze -> very faded pale yellow (file name kept: it is the counter back-wall tile)
import sys, json, hashlib, zipfile, io
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
DL = ROOT / "assets" / "cc0" / "_downloads"
OUT = ROOT / "source" / "textures" / "v031"
def col(zname):
    z = zipfile.ZipFile(DL / zname)
    return np.asarray(Image.open(io.BytesIO(z.read(next(x for x in z.namelist() if "_Color" in x)))).convert("RGB").resize((512, 512), Image.LANCZOS), float)
rep = {}
def save(name, arr, src):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); data = gs_dds.encode_dds(im, "DXT1")
    (OUT / f"{name}.dds").write_bytes(data); rep[name] = {"sha256": hashlib.sha256(data).hexdigest(), "derived_from": src, "licence": "CC0 1.0 (ambientCG)"}
    return im
w = col("PaintedWood003_1K-JPG.zip")
g = w.mean(2, keepdims=True)
a = save("lp11_board", (w * 0.5 + g * 0.5) * np.array([0.40, 0.31, 0.29]), "PaintedWood003")
c = col("Tiles135B_1K-JPG.zip")
glaze = np.clip((c[..., 2] - c[..., 0] - 6.0) / 18.0, 0.0, 1.0)[..., None]
lum = (0.3 * c[..., 0] + 0.59 * c[..., 1] + 0.11 * c[..., 2])[..., None] / 70.0
b = save("lp10_tile_blue", c * (1 - glaze) + np.array([188.0, 172.0, 118.0]) * np.clip(lum, 0.6, 1.12) * glaze, "Tiles135B")
s = Image.new("RGB", (1024, 512)); s.paste(a, (0, 0)); s.paste(b, (512, 0)); s.save(OUT / "_regrade_prev.jpg", quality=88)
(OUT / "cc0_v121_report.json").write_text(json.dumps(rep, indent=1)); print(list(rep))
