# LONG PIG 2.0.0 textures (convenience-store rework). CC0 photo sets from ambientCG (CC0 1.0, zips + SHA-256 in
# source/textures/v200/src), graded in code; own procedural ceiling / light panels; own sign atlas (gs_15ag_signs200.py).
import sys, json, hashlib, io, zipfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
OUT = ROOT / "source" / "textures" / "v200"; SRC = OUT / "src"
rep = {"sources": {}, "files": {}}
def cc(aid, kind, n=1024):
    zp = SRC / f"{aid}_1K-JPG.zip"; data = zp.read_bytes()
    rep["sources"][aid] = {"url": "https://ambientcg.com/a/" + aid, "file": zp.name, "licence": "CC0 1.0", "sha256": hashlib.sha256(data).hexdigest()}
    z = zipfile.ZipFile(io.BytesIO(data)); nm = [x for x in z.namelist() if x.endswith(f"_{kind}.jpg")][0]
    im = Image.open(io.BytesIO(z.read(nm))).convert("RGB")
    return np.asarray(im.resize((n, n), Image.LANCZOS), float) / 255.0
def save(name, a, fmt="DXT1", alpha=None, src=None):
    im = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + 0.5)) if not isinstance(a, Image.Image) else a
    if alpha is not None:
        im = im.convert("RGBA"); im.putalpha(Image.fromarray(np.uint8(np.clip(alpha, 0, 1) * 255)))
    data = gs_dds.encode_dds(im, fmt); (OUT / f"{name}.dds").write_bytes(data)
    rep["files"][name] = {"size": list(im.size), "format": fmt, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "from": src or "own procedural"}
def lum(a): return a @ np.array([0.299, 0.587, 0.114])
def tone(c, rgb, k=1.0):
    L = lum(c); d = (L / max(L.mean(), 1e-6) - 1.0) * k + 1.0
    return np.clip(d[..., None] * (np.array(rgb, float) / 255.0), 0, 1)
def spec(r, lo, hi):
    s = 1 - r.mean(-1); s = lo + (hi - lo) * (s - s.min()) / (np.ptp(s) + 1e-9); return np.repeat(s[..., None], 3, -1)
def noise(n, seed, blur):
    g = np.random.default_rng(seed).random((n, n)); im = Image.fromarray(np.uint8(g * 255)).filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(im, float); return (a - a.min()) / (np.ptp(a) + 1e-9)
def surf(name, aid, rgb, n=512, k=1.0, lo=0.05, hi=0.5):
    save(name, tone(cc(aid, "Color", n), rgb, k), src=aid); save(name + "_n", cc(aid, "NormalDX", n), src=aid); save(name + "_s", spec(cc(aid, "Roughness", n), lo, hi), src=aid)
# floor: Tiles107 (8 x 8 white tiles) -> warm off-white ceramic, 2.56 m per repeat (32 cm tiles), light foot-traffic soil
c = tone(cc("Tiles107", "Color"), (206, 199, 184), 1.6); g = noise(1024, 7, 40)
c = c * (0.93 + 0.07 * g[..., None]); nrm = cc("Tiles107", "NormalDX"); joint = np.clip(np.abs(nrm[..., :2] - 0.5).max(-1) * 8, 0, 1)
c = c * (1 - 0.22 * joint[..., None]); save("lp20_floor", c, src="Tiles107"); save("lp20_floor_n", nrm, src="Tiles107")
save("lp20_floor_s", spec(cc("Tiles107", "Roughness"), 0.25, 0.75) * (1 - 0.5 * joint[..., None]), src="Tiles107")
surf("lp20_wall", "PaintedPlaster017", (182, 178, 168), k=0.5, lo=0.03, hi=0.18)       # light warm grey paint
surf("lp20_teal", "PaintedPlaster017", (34, 112, 124), n=256, k=0.5, lo=0.05, hi=0.25)  # accent stripe
surf("lp20_dark", "PaintedPlaster017", (58, 64, 70), n=256, k=0.5, lo=0.05, hi=0.25)    # base band / kick plates
surf("lp20_lam", "Wood058", (176, 146, 106), k=1.0, lo=0.10, hi=0.45)                   # light wood laminate (counter fronts)
surf("lp20_top", "Plastic010", (62, 62, 66), k=1.5, lo=0.15, hi=0.6)                    # dark grey counter top
surf("lp20_white", "Plastic010", (214, 214, 208), k=1.0, lo=0.10, hi=0.5)               # white powder-coated metal
surf("lp20_alu", "Metal009", (150, 150, 146), k=1.0, lo=0.3, hi=0.9)                    # brushed aluminium frames
# ceiling: own 8 x 8 mineral-fibre tiles per repeat, clean
N = 1024; t = N // 8; a = 0.80 + 0.03 * noise(N, 11, 1.2) + 0.02 * noise(N, 12, 25); a = np.repeat(a[..., None], 3, -1) * np.array([1.0, 0.99, 0.96])
for i in range(8):
    a[i * t:i * t + 3, :] = (0.88, 0.88, 0.86); a[:, i * t:i * t + 3] = (0.88, 0.88, 0.86); a[i * t + 3:i * t + 5, :] *= 0.86; a[:, i * t + 3:i * t + 5] *= 0.86
save("lp20_ceil", a)
p = np.full((64, 64, 3), 0.97); p[::16, :] = 0.90; p[:, ::16] = 0.90; save("lp20_panel", p); save("lp20_panel_off", p * 0.55)
at = Image.open(SRC / "lp20_signs.png").convert("RGB"); save("lp20_signs", at, src="own artwork (gs_15ag_signs200.py)")
(OUT / "v200_textures_report.json").write_text(json.dumps(rep, indent=1)); print(len(rep["files"]), sorted(rep["files"]))
