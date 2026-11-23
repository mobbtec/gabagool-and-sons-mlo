# LONG PIG 1.3.0 textures - internet photo textures only (ambientCG, CC0), resized, pixels not repainted:
#   lp13_floor      Tiles141 (white) + Tiles140 (black): the same 6 x 6 tile scan in two colours, alternated tile by tile
#   lp13_tile_white Tiles133B, unmodified (kitchen / WC wall tile)
import sys, json, hashlib, zipfile, io
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
DL = ROOT / "assets" / "cc0" / "_downloads"; OUT = ROOT / "source" / "textures" / "v031"; rep = {}
def img(a, key, size, mode="RGB"):
    z = zipfile.ZipFile(DL / f"{a}_1K-JPG.zip")
    return np.asarray(Image.open(io.BytesIO(z.read(next(x for x in z.namelist() if key in x and x.lower().endswith(".jpg"))))).convert(mode).resize((size, size), Image.LANCZOS), float)
def save(name, arr, src):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); data = gs_dds.encode_dds(im, "DXT1"); (OUT / f"{name}.dds").write_bytes(data)
    rep[name] = {"size": list(im.size), "sha256": hashlib.sha256(data).hexdigest(), "derived_from": src, "licence": "CC0 1.0 (ambientCG)"}; return im
def checker(key, size, mode="RGB"):
    a, b = img("Tiles141", key, size, mode), img("Tiles140", key, size, mode)
    yy, xx = np.mgrid[0:size, 0:size]; m = ((xx * 6 // size + yy * 6 // size) % 2 == 0)
    return np.where(m[..., None] if a.ndim == 3 else m, a, b)
prev = save("lp13_floor", img("Tiles012", "_Color", 1024), "Tiles012")          # ready-made checker floor, unmodified (revision)
n = img("Tiles012", "_NormalGL", 512) / 127.5 - 1.0; n /= np.linalg.norm(n, axis=2, keepdims=True); save("lp13_floor_n", (n + 1) * 127.5, "Tiles012")
r = img("Tiles012", "_Roughness", 256, "L"); save("lp13_floor_s", np.stack([(255 - r) * 0.6] * 3, 2), "Tiles012")
save("lp13_tile_white", img("Tiles133B", "_Color", 1024), "Tiles133B")
n = img("Tiles133B", "_NormalGL", 512) / 127.5 - 1.0; n /= np.linalg.norm(n, axis=2, keepdims=True); save("lp13_tile_white_n", (n + 1) * 127.5, "Tiles133B")
r = img("Tiles133B", "_Roughness", 256, "L"); save("lp13_tile_white_s", np.stack([(255 - r) * 0.8] * 3, 2), "Tiles133B")
prev.resize((512, 512)).save(OUT / "_floor130_prev.jpg", quality=88)
(OUT / "cc0_v130_report.json").write_text(json.dumps(rep, indent=1)); print(list(rep))
