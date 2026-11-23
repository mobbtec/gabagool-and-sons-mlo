# LONG PIG 2.4.0 textures (owner's in-game screenshots of 2.3.0 + brief "PLEBMASTERS PROP CATALOG AND QA"):
#   * lp24_wall  - calm dirty-cream painted plaster, 1024 px for a 2.56 m repeat (2.5 mm / px); no per-pixel noise, no
#                  green cast, only large soft tone drift. Dirt is NOT baked wall-wide any more.
#   * lp24_dado  - brick-red gloss paint, v = 0 at the floor .. 1 at the dado top (1 m): scuffs and dirt only in the
#                  lowest 25 cm; the white "confetti" chips of 2.3.0 are gone.
#   * lp24_band  - red band with two mustard pin lines, no chips, faint dust only.
#   * lp24_alu   - dark anodised aluminium for the kiosk / case frames.
# Sources: CC0 ambientCG zips already in source/textures/v200/src (PaintedPlaster017, Metal009); SHA-256 in the report.
import sys, json, hashlib, io, zipfile, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
SRC = ROOT / "source" / "textures" / "v200" / "src"
OUT = ROOT / "source" / "textures" / "v240"; OUT.mkdir(exist_ok=True)
RED, YEL = (150, 44, 34), (226, 168, 40)
rep = {"sources": {}, "files": {}}


def cc(aid, kind, n=1024):
    zp = SRC / f"{aid}_1K-JPG.zip"; data = zp.read_bytes()
    rep["sources"][aid] = {"url": "https://ambientcg.com/a/" + aid, "file": zp.name, "licence": "CC0 1.0", "sha256": hashlib.sha256(data).hexdigest()}
    z = zipfile.ZipFile(io.BytesIO(data)); nm = [x for x in z.namelist() if x.endswith(f"_{kind}.jpg")][0]
    return np.asarray(Image.open(io.BytesIO(z.read(nm))).convert("RGB").resize((n, n), Image.LANCZOS), float) / 255.0


def save(name, a, fmt="DXT1", src=None):
    im = a if isinstance(a, Image.Image) else Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + 0.5))
    data = gs_dds.encode_dds(im, fmt); (OUT / f"{name}.dds").write_bytes(data)
    rep["files"][name] = {"size": list(im.size), "format": fmt, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "from": src or "own procedural"}
    return im


def lum(a): return a @ np.array([0.299, 0.587, 0.114])


def noise(n, seed, blur):
    m = max(2, int(round(n / (blur * 2.5))))
    g = np.random.default_rng(seed).random((m, m)).astype(np.float32)
    im = Image.fromarray(np.tile(g, (3, 3)), "F").resize((3 * n, 3 * n), Image.BICUBIC)
    a = np.asarray(im, float)[n:2 * n, n:2 * n]
    return (a - a.min()) / (np.ptp(a) + 1e-9)


def soft(a, r):
    """Tileable gaussian blur of an RGB float image."""
    n = a.shape[0]; t = np.tile(a, (3, 3, 1))
    im = Image.fromarray(np.uint8(np.clip(t, 0, 1) * 255)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, float)[n:2 * n, n:2 * n] / 255.0


def paint(aid, rgb, n, k, r=1.2):
    """Photo luminance, slightly blurred (kills the sandy pixel noise), contrast k around the mean, tinted to rgb."""
    L = lum(soft(cc(aid, "Color", n), r)); d = (L / L.mean() - 1.0) * k + 1.0
    return np.clip(d[..., None] * (np.array(rgb, float) / 255.0), 0, 1)


def flat_normal(aid, n, keep):
    a = soft(cc(aid, "NormalDX", n), 1.0); f = np.array([0.5, 0.5, 1.0])
    v = (a * keep + f * (1 - keep)) * 2 - 1
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    return v * 0.5 + 0.5


def streaks(n, seed, cnt, y0, y1, lmax=0.25):
    im = Image.new("L", (n, n), 0); d = ImageDraw.Draw(im); r = random.Random(seed)
    for _ in range(cnt):
        x, y, L = r.randrange(n), r.randrange(int(y0 * n), int(y1 * n)), int(n * r.uniform(0.03, lmax))
        d.line([(x, y), (x + L, y + r.randrange(-3, 4))], fill=r.randrange(70, 190), width=r.choice((1, 1, 2)))
        d.line([(x - n, y), (x + L - n, y)], fill=120, width=1)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(0.9)), float) / 255.0


# ---- wall
N = 1024
w = paint("PaintedPlaster017", (216, 200, 166), N, 0.22, 1.6)
drift = noise(N, 401, 260); drift2 = noise(N, 402, 90)
w *= (0.965 + 0.05 * drift)[..., None] * (0.985 + 0.03 * drift2)[..., None]
w *= 1 - 0.035 * (1 - drift)[..., None] * np.array([0.0, 0.35, 1.0])                       # old paint yellows a little, never green
save("lp24_wall", w, src="PaintedPlaster017")
save("lp24_wall_n", flat_normal("PaintedPlaster017", 512, 0.35), src="PaintedPlaster017")
sp = 0.05 + 0.07 * noise(512, 403, 120)
save("lp24_wall_s", np.repeat(sp[..., None], 3, -1), src="own procedural")
# ---- dado: v (image row) runs top -> bottom = dado top -> floor
n = 512
d0 = paint("PaintedPlaster017", RED, n, 0.25, 1.4)
yy = np.linspace(0, 1, n)[:, None]                                                         # 0 top .. 1 floor
low = np.clip((yy - 0.72) / 0.28, 0, 1)                                                    # lowest 28 cm
dirt = noise(n, 411, 40) * 0.6 + noise(n, 412, 8) * 0.4
sc = streaks(n, 413, 70, 0.74, 0.97)
d0 *= (1 - 0.30 * low * dirt)[..., None]
d0 *= (1 - 0.30 * sc * low)[..., None]
d0 = d0 * (1 - 0.10 * low[..., None]) + 0.10 * low[..., None] * np.array([0.30, 0.26, 0.22])   # floor dust
d0 *= (0.97 + 0.04 * noise(n, 414, 200))[..., None]
save("lp24_dado", d0, src="PaintedPlaster017")
save("lp24_dado_n", flat_normal("PaintedPlaster017", 256, 0.30), src="PaintedPlaster017")
ds = (0.30 + 0.12 * noise(n, 415, 100)) * (1 - 0.7 * low * dirt) * (1 - 0.6 * sc)
save("lp24_dado_s", np.repeat(ds[..., None], 3, -1), src="own procedural")
# ---- band (v across the height)
b = paint("PaintedPlaster017", RED, n, 0.22, 1.4); yl = paint("PaintedPlaster017", YEL, n, 0.22, 1.4)
for r0, r1 in ((40, 60), (452, 472)):
    b[r0:r1] = yl[r0:r1]
b *= (0.95 + 0.06 * noise(n, 421, 200))[..., None]
dust = np.clip((np.linspace(1, 0, n)[:, None] - 0.9) / 0.1, 0, 1)                          # dust on the top edge
b = b * (1 - 0.18 * dust[..., None]) + 0.18 * dust[..., None] * np.array([0.42, 0.38, 0.32])
save("lp24_band", b, src="PaintedPlaster017")
save("lp24_band_n", flat_normal("PaintedPlaster017", 256, 0.30), src="PaintedPlaster017")
save("lp24_band_s", np.repeat((0.22 + 0.08 * noise(n, 422, 100))[..., None], 3, -1), src="own procedural")
# ---- dark anodised aluminium
m = cc("Metal009", "Color", 256); L = lum(soft(m, 0.8)); L = (L / L.mean() - 1.0) * 0.5 + 1.0
a = np.clip(L[..., None] * (np.array((74, 72, 70)) / 255.0), 0, 1) * (0.94 + 0.08 * noise(256, 431, 60))[..., None]
save("lp24_alu", a, src="Metal009"); save("lp24_alu_n", flat_normal("Metal009", 256, 0.5), src="Metal009")
r_ = 1 - cc("Metal009", "Roughness", 256).mean(-1); r_ = 0.35 + 0.4 * (r_ - r_.min()) / (np.ptp(r_) + 1e-9)
save("lp24_alu_s", np.repeat(r_[..., None], 3, -1), src="Metal009")
# ---- preview + report
sheet = Image.new("RGB", (1024 + 512 * 2, 1024), (30, 30, 30))
for nm, xy, sz in (("lp24_wall", (0, 0), 1024), ("lp24_dado", (1024, 0), 512), ("lp24_band", (1536, 0), 512), ("lp24_alu", (1024, 512), 512)):
    sheet.paste(Image.fromarray(np.uint8(np.clip({"lp24_wall": w, "lp24_dado": d0, "lp24_band": b, "lp24_alu": np.kron(a, np.ones((2, 2, 1)))}[nm], 0, 1) * 255)), xy)
sheet.save(OUT / "preview_sheet.jpg", quality=88)
rep["date"] = "2026-11-21"
(OUT / "v240_textures_report.json").write_text(json.dumps(rep, indent=1))
print("DONE", len(rep["files"]), "files ->", OUT)
