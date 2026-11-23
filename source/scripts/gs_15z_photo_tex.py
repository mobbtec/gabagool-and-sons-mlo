# LONG PIG 1.2.1 (revision): unmodified CC0 photo textures,
# only resized. ambientCG Tiles095 (faded yellow-beige wall tile) and WoodSiding005 (dark red-brown boards), 1K-JPG zips.
import sys, json, hashlib, zipfile, io
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
DL = ROOT / "assets" / "cc0" / "_downloads"
OUT = ROOT / "source" / "textures" / "v031"
rep = {}
def img(a, key):
    z = zipfile.ZipFile(DL / f"{a}_1K-JPG.zip")
    return Image.open(io.BytesIO(z.read(next(x for x in z.namelist() if key in x and x.lower().endswith(".jpg")))))
def save(name, im, src):
    data = gs_dds.encode_dds(im, "DXT1"); (OUT / f"{name}.dds").write_bytes(data)
    rep[name] = {"size": list(im.size), "sha256": hashlib.sha256(data).hexdigest(), "derived_from": src,
                 "source": f"https://ambientcg.com/get?file={src}_1K-JPG.zip", "licence": "CC0 1.0 (ambientCG)"}
def nrm(im, size):
    n = np.asarray(im.convert("RGB").resize((size, size), Image.LANCZOS), float) / 127.5 - 1.0
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return Image.fromarray(np.clip((n + 1.0) * 127.5, 0, 255).astype(np.uint8))
def spec(im, size, k=0.7):
    s = np.clip(255.0 - np.asarray(im.convert("L").resize((size, size), Image.LANCZOS), float), 0, 255) * k
    return Image.fromarray(np.stack([s] * 3, 2).astype(np.uint8))
for a, nm in (("Tiles095", "lp12_wall_tile"), ("WoodSiding005", "lp12_board")):
    save(nm, img(a, "_Color").convert("RGB").resize((1024, 1024), Image.LANCZOS), a)
    save(nm + "_n", nrm(img(a, "_NormalGL"), 512), a)
    save(nm + "_s", spec(img(a, "_Roughness"), 256), a)
(OUT / "cc0_v121_report.json").write_text(json.dumps(rep, indent=1)); print(list(rep))
