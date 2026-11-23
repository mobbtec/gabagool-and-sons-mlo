# LONG PIG 0.3.2-g: faded dark-blue wall tile for the back wall of the deli counter (owner 2026-11-16).
# Source: ambientCG "Tiles135C" (CC0), Tiles135C_1K-JPG.zip. Only conversion: resize, mild desaturation, roughness -> spec.
import sys, json, hashlib, zipfile, io, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
DL = ROOT / "assets" / "cc0" / "_downloads"
OUT = ROOT / "source" / "textures" / "v031"
URL = "https://ambientcg.com/get?file=Tiles135C_1K-JPG.zip"
zp = DL / "Tiles135C_1K-JPG.zip"
if not zp.exists():
    zp.write_bytes(urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read())
z = zipfile.ZipFile(zp)
names = z.namelist()
def img(key):
    n = next(x for x in names if key in x and x.lower().endswith(".jpg"))
    return Image.open(io.BytesIO(z.read(n)))
rep = {"_zip": {"file": zp.name, "bytes": zp.stat().st_size, "sha256": hashlib.sha256(zp.read_bytes()).hexdigest(), "source": URL,
                "licence": "CC0 1.0 (ambientCG)", "files": names}}
def save(name, im, fmt):
    data = gs_dds.encode_dds(im, fmt)
    (OUT / f"{name}.dds").write_bytes(data)
    rep[name] = {"size": list(im.size), "format": fmt, "sha256": hashlib.sha256(data).hexdigest(), "derived_from": "Tiles135C"}
c = img("_Color").convert("RGB").resize((512, 512), Image.LANCZOS)
c = ImageEnhance.Brightness(ImageEnhance.Color(c).enhance(0.60)).enhance(1.0)
save("lp10_tile_blue", c, "DXT1")
c.save(OUT / "_tile_blue_prev.jpg", quality=88)
n = np.asarray(img("_NormalGL").convert("RGB").resize((512, 512), Image.LANCZOS), float) / 127.5 - 1.0
n /= np.linalg.norm(n, axis=2, keepdims=True)
save("lp10_tile_blue_n", Image.fromarray(np.clip((n + 1.0) * 127.5, 0, 255).astype(np.uint8)), "DXT1")
r = np.asarray(img("_Roughness").convert("L").resize((256, 256), Image.LANCZOS), float)
s = np.clip(255.0 - r, 0, 255) * 0.8
save("lp10_tile_blue_s", Image.fromarray(np.stack([s] * 3, 2).astype(np.uint8)), "DXT1")
(OUT / "cc0_v110_report.json").write_text(json.dumps(rep, indent=1))
print(json.dumps({k: v.get("size") for k, v in rep.items()}))
