# LONG PIG 1.6.0: faded Italian-flag tile bands for the counter back wall. Base = ambientCG Tiles136B (CC0, the hall wall
# tile); the green / red bands are a colour grade of that same photo (owner asked for a faded flag in tile).
import sys, json, hashlib, shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
OUT = ROOT / "source" / "textures" / "v031"
a = np.asarray(Image.open(OUT / "lp14_wall.dds").convert("RGB").resize((512, 512), Image.LANCZOS), float)
rep = {}
def save(name, tint):
    g = a.mean(2, keepdims=True)
    x = a * np.array(tint) / 255.0
    x = x * 0.85 + g * np.array(tint).mean() / 255.0 * 0.15
    im = Image.fromarray(np.clip(x, 0, 255).astype(np.uint8)); data = gs_dds.encode_dds(im, "DXT1"); (OUT / f"{name}.dds").write_bytes(data)
    rep[name] = {"sha256": hashlib.sha256(data).hexdigest(), "derived_from": "Tiles136B (colour grade)", "licence": "CC0 1.0 (ambientCG)"}; return im
g = save("lp16_tile_green", (118, 158, 112)); r = save("lp16_tile_red", (178, 92, 84))
shutil.copyfile(OUT / "lp14_wall_n.dds", OUT / "lp16_tile_n.dds"); shutil.copyfile(OUT / "lp14_wall_s.dds", OUT / "lp16_tile_s.dds")
s = Image.new("RGB", (1536, 512)); s.paste(g, (0, 0)); s.paste(Image.fromarray(a.astype(np.uint8)), (512, 0)); s.paste(r, (1024, 0)); s.save(OUT / "_flag_prev.jpg", quality=85)
(OUT / "cc0_v160_report.json").write_text(json.dumps(rep, indent=1)); print(list(rep))
