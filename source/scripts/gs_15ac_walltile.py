# LONG PIG 1.4.1: hall / back-room wall finish = ambientCG Tiles136B (CC0), unmodified, resized. Owner picked it from a sheet.
import sys, json, hashlib, zipfile, io, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
A = "Tiles136B"; zp = ROOT / "assets" / "cc0" / "_downloads" / f"{A}_1K-JPG.zip"; OUT = ROOT / "source" / "textures" / "v031"
if not zp.exists():
    zp.write_bytes(urllib.request.urlopen(urllib.request.Request(f"https://ambientcg.com/get?file={A}_1K-JPG.zip", headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
z = zipfile.ZipFile(zp)
def img(key): return Image.open(io.BytesIO(z.read(next(x for x in z.namelist() if key in x and x.lower().endswith(".jpg")))))
rep = {"_zip": {"bytes": zp.stat().st_size, "sha256": hashlib.sha256(zp.read_bytes()).hexdigest()}}
def save(name, im):
    data = gs_dds.encode_dds(im, "DXT1"); (OUT / f"{name}.dds").write_bytes(data); rep[name] = {"size": list(im.size), "sha256": hashlib.sha256(data).hexdigest(), "derived_from": A, "licence": "CC0 1.0 (ambientCG)"}
c = img("_Color").convert("RGB").resize((1024, 1024), Image.LANCZOS); save("lp14_wall", c); c.resize((640, 640)).save(OUT / "_wall141_prev.jpg", quality=88)
n = np.asarray(img("_NormalGL").convert("RGB").resize((512, 512), Image.LANCZOS), float) / 127.5 - 1; n /= np.linalg.norm(n, axis=2, keepdims=True)
save("lp14_wall_n", Image.fromarray(np.clip((n + 1) * 127.5, 0, 255).astype(np.uint8)))
r = np.asarray(img("_Roughness").convert("L").resize((256, 256), Image.LANCZOS), float); save("lp14_wall_s", Image.fromarray(np.stack([(255 - r) * 0.7] * 3, 2).astype(np.uint8)))
(OUT / "cc0_v141_report.json").write_text(json.dumps(rep, indent=1)); print(zp.stat().st_size, list(rep))
