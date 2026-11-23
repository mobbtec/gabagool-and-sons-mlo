# LONG PIG 2.7.0 textures (owner 2026-11-21 19:48):
#   lp27_band / lp27_dado - the colour of the owner's swatch (sign red-brown, RGB 116 70 57) instead of bright red + yellow pins
#   lp27_wall             - same calm plaster base but OLD: stains, runs, hairline cracks, repaint patches, scuffs (2.56 m repeat)
#   lp27_grime            - lp25_grime with stronger alpha (local decals)
#   lp27_heads            - own lit header signs for the tobacco wall (LONG PIG brands only; Poppins, OFL)
# Sources: CC0 ambientCG PaintedPlaster017 (zip in source/textures/v200/src), rest own procedural.
import sys, json, hashlib, io, zipfile, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
SRC = ROOT / "source" / "textures" / "v200" / "src"
OUT = ROOT / "source" / "textures" / "v270"; OUT.mkdir(exist_ok=True)
SIGN = (116, 70, 57)
rep = {"swatch_rgb": SIGN, "sources": {}, "files": {}, "date": "2026-11-21"}


def cc(aid, kind, n):
    zp = SRC / f"{aid}_1K-JPG.zip"; data = zp.read_bytes()
    rep["sources"][aid] = {"url": "https://ambientcg.com/a/" + aid, "file": zp.name, "licence": "CC0 1.0", "sha256": hashlib.sha256(data).hexdigest()}
    z = zipfile.ZipFile(io.BytesIO(data)); nm = [x for x in z.namelist() if x.endswith(f"_{kind}.jpg")][0]
    return np.asarray(Image.open(io.BytesIO(z.read(nm))).convert("RGB").resize((n, n), Image.LANCZOS), float) / 255.0


def save(name, a, fmt="DXT1", src=None):
    im = a if isinstance(a, Image.Image) else Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + 0.5))
    data = gs_dds.encode_dds(im, fmt); (OUT / f"{name}.dds").write_bytes(data)
    rep["files"][name] = {"size": list(im.size), "format": fmt, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "from": src or "own procedural"}


def noise(n, seed, blur):
    m = max(2, int(round(n / (blur * 2.5))))
    g = np.random.default_rng(seed).random((m, m)).astype(np.float32)
    a = np.asarray(Image.fromarray(np.tile(g, (3, 3)), "F").resize((3 * n, 3 * n), Image.BICUBIC), float)[n:2 * n, n:2 * n]
    return (a - a.min()) / (np.ptp(a) + 1e-9)


def soft(a, r):
    n = a.shape[0]; t = np.tile(a, (3, 3, 1))
    return np.asarray(Image.fromarray(np.uint8(np.clip(t, 0, 1) * 255)).filter(ImageFilter.GaussianBlur(r)), float)[n:2 * n, n:2 * n] / 255.0


def paint(rgb, n, k, r=1.4):
    L = soft(cc("PaintedPlaster017", "Color", n), r) @ np.array([0.299, 0.587, 0.114]); d = (L / L.mean() - 1.0) * k + 1.0
    return np.clip(d[..., None] * (np.array(rgb, float) / 255.0), 0, 1)


def nrm(n, keep):
    a = soft(cc("PaintedPlaster017", "NormalDX", n), 1.0); v = (a * keep + np.array([0.5, 0.5, 1.0]) * (1 - keep)) * 2 - 1
    v /= np.linalg.norm(v, axis=-1, keepdims=True); return v * 0.5 + 0.5


def mask(n, fn, blur):
    im = Image.new("L", (n, n), 0); fn(ImageDraw.Draw(im)); return np.asarray(im.filter(ImageFilter.GaussianBlur(blur)), float) / 255.0


# ------------------------------------------------------------------ old wall
N = 1024; r = random.Random(27)
w = paint((212, 195, 160), N, 0.30, 1.5)
w *= (0.93 + 0.10 * noise(N, 701, 240))[..., None] * (0.97 + 0.05 * noise(N, 702, 70))[..., None]
st = np.clip((noise(N, 703, 110) - 0.60) / 0.25, 0, 1) * (0.6 + 0.4 * noise(N, 704, 20))               # old damp / nicotine stains
w = w * (1 - 0.30 * st[..., None]) + 0.30 * st[..., None] * np.array([0.52, 0.40, 0.24])
def runs(d):
    for _ in range(22):
        x, y, L = r.randrange(20, N - 20), r.randrange(0, N - 320), r.randrange(90, 300)
        d.line([(x, y), (x + r.randrange(-4, 5), y + L)], fill=r.randrange(70, 170), width=r.choice((2, 3, 4, 6)))
rn = mask(N, runs, 2.2) * np.linspace(1.0, 0.25, N)[:, None]
w = w * (1 - 0.32 * rn[..., None]) + 0.32 * rn[..., None] * np.array([0.40, 0.32, 0.22])
def patches(d):
    for _ in range(3):
        x, y, a, b = r.randrange(60, N - 360), r.randrange(60, N - 300), r.randrange(160, 300), r.randrange(110, 220)
        d.rectangle([x, y, x + a, y + b], fill=255)
pt = mask(N, patches, 3.0)
w = w * (1 - 0.5 * pt[..., None]) + 0.5 * pt[..., None] * w * np.array([1.045, 1.035, 0.99])                 # patches repainted in a fresher cream
def cracks(d):
    for _ in range(7):
        x, y = r.randrange(80, N - 80), r.randrange(80, N - 80); pts = [(x, y)]
        for _k in range(r.randrange(8, 18)):
            x += r.randrange(-16, 17); y += r.randrange(8, 26); pts.append((min(max(x, 12), N - 12), min(y, N - 12)))
        d.line(pts, fill=230, width=1)
cr = mask(N, cracks, 0.6)
w *= (1 - 0.42 * cr)[..., None]
def scuffs(d):
    for _ in range(46):
        x, y, L = r.randrange(10, N - 140), r.randrange(10, N - 10), r.randrange(30, 130)
        d.line([(x, y), (x + L, y + r.randrange(-6, 7))], fill=r.randrange(60, 160), width=r.choice((1, 1, 2)))
sc = mask(N, scuffs, 1.0)
w *= (1 - 0.13 * sc)[..., None]
pe = np.clip((noise(N, 706, 14) * 0.6 + noise(N, 707, 5) * 0.4 - 0.745) / 0.03, 0, 1) * np.clip((noise(N, 708, 160) - 0.5) / 0.2, 0, 1)   # flaked paint, in clusters
pe_s = np.asarray(Image.fromarray(np.uint8(pe * 255)).filter(ImageFilter.GaussianBlur(1.6)), float) / 255.0
w *= (1 - 0.35 * np.clip(pe_s - pe, 0, 1))[..., None]                                                     # shadow line round each flake
w = w * (1 - pe[..., None]) + pe[..., None] * np.array([0.74, 0.68, 0.57]) * (0.9 + 0.1 * noise(N, 709, 3))[..., None]
save("lp27_wall", w, src="PaintedPlaster017")
nn = nrm(512, 0.45); cr5 = np.asarray(Image.fromarray(np.uint8(cr * 255)).resize((512, 512), Image.BILINEAR), float) / 255.0
gy, gx = np.gradient(cr5); nn[..., 0] = np.clip(nn[..., 0] - 1.6 * gx, 0, 1); nn[..., 1] = np.clip(nn[..., 1] + 1.6 * gy, 0, 1)
save("lp27_wall_n", nn, src="PaintedPlaster017")
sp = (0.05 + 0.07 * noise(512, 705, 120)) * (1 - 0.5 * np.asarray(Image.fromarray(np.uint8(st * 255)).resize((512, 512)), float) / 255.0)
save("lp27_wall_s", np.repeat(sp[..., None], 3, -1))
# ------------------------------------------------------------------ dado (v: image top = dado top, bottom = floor) + band in the sign colour
n = 512
d0 = paint((108, 64, 52), n, 0.28)
yy = np.linspace(0, 1, n)[:, None]; low = np.clip((yy - 0.66) / 0.34, 0, 1)
dirt = noise(n, 711, 40) * 0.6 + noise(n, 712, 8) * 0.4
def sc2(d):
    for _ in range(90):
        x, y, L = r.randrange(n), r.randrange(int(0.55 * n), int(0.97 * n)), r.randrange(16, 120)
        d.line([(x, y), (x + L, y + r.randrange(-3, 4))], fill=r.randrange(70, 200), width=r.choice((1, 1, 2)))
s2 = mask(n, sc2, 0.9)
ch = np.clip((noise(n, 713, 5) - 0.86) / 0.05, 0, 1) * low                                                # chips down to the old cream coat, floor zone only
d0 *= (1 - 0.34 * low * dirt)[..., None] * (1 - 0.30 * s2)[..., None] * (0.94 + 0.08 * noise(n, 714, 150))[..., None]
d0 = d0 * (1 - ch[..., None]) + ch[..., None] * np.array([0.70, 0.64, 0.52])
d0 = d0 * (1 - 0.14 * low[..., None]) + 0.14 * low[..., None] * np.array([0.26, 0.23, 0.20])
save("lp27_dado", d0, src="PaintedPlaster017"); save("lp27_dado_n", nrm(256, 0.35), src="PaintedPlaster017")
save("lp27_dado_s", np.repeat(((0.26 + 0.10 * noise(n, 715, 100)) * (1 - 0.7 * low * dirt) * (1 - 0.6 * s2))[..., None], 3, -1))
b = paint(SIGN, n, 0.24)
for r0, r1 in ((40, 60), (452, 472)):
    b[r0:r1] *= 0.80                                                                                       # pin lines: same colour, a shade deeper
b *= (0.93 + 0.09 * noise(n, 721, 180))[..., None]
dust = np.clip((np.linspace(1, 0, n)[:, None] - 0.88) / 0.12, 0, 1)
b = b * (1 - 0.22 * dust[..., None]) + 0.22 * dust[..., None] * np.array([0.40, 0.36, 0.31])
def bruns(d):
    for _ in range(14):
        x, y = r.randrange(n), r.randrange(60, 300)
        d.line([(x, y), (x + r.randrange(-2, 3), y + r.randrange(60, 200))], fill=r.randrange(80, 160), width=r.choice((2, 3)))
b *= (1 - 0.16 * mask(n, bruns, 1.6))[..., None]
save("lp27_band", b, src="PaintedPlaster017"); save("lp27_band_n", nrm(256, 0.35), src="PaintedPlaster017")
save("lp27_band_s", np.repeat((0.20 + 0.08 * noise(n, 722, 100))[..., None], 3, -1))
# ------------------------------------------------------------------ stronger grime decals
g = np.asarray(Image.open(ROOT / "source" / "textures" / "v250" / "lp25_grime_preview.png").convert("RGBA"), float) / 255.0
g[..., 3] = np.clip(g[..., 3] * 1.75, 0, 0.92); g[..., :3] *= 0.9
save("lp27_grime", Image.fromarray(np.uint8(g * 255 + 0.5), "RGBA"), "DXT5", "lp25_grime (own procedural)")
# ------------------------------------------------------------------ header signs (6 cells 512 x 96 in a 1024 x 512 atlas)
FN = "/usr/share/fonts/truetype/google-fonts/Poppins-%s.ttf"
try:
    ImageFont.truetype(FN % "Bold", 20)
except Exception:
    FN = "/usr/share/fonts/truetype/dejavu/DejaVuSans-%s.ttf"
CREAM, YEL, DK = (238, 226, 198), (232, 176, 48), (54, 34, 28)
CELLS = (("lp_tobacco", "LONG PIG", "TOBACCO", SIGN, CREAM), ("smokes", "SMOKES", "PAY HERE", YEL, DK), ("lotto", "LOTTO", "SCRATCH & WIN", CREAM, SIGN),
         ("lp_market", "LONG PIG", "MARKET & DELI", SIGN, YEL), ("cigars", "CIGARS", "LIGHTERS  PAPERS", DK, YEL), ("cards", "PHONE CARDS", "TOP-UP HERE", YEL, DK))
at = Image.new("RGB", (1024, 512), (20, 14, 12)); reg = {}
for k, (key, big, small, bg, fg) in enumerate(CELLS):
    x0, y0 = (k % 2) * 512, (k // 2) * 128 + 16
    c = Image.new("RGB", (512, 96), bg); d = ImageDraw.Draw(c)
    d.rectangle([5, 5, 506, 90], outline=fg, width=3)
    f1 = ImageFont.truetype(FN % "Bold", 46); bb = d.textbbox((0, 0), big, font=f1)
    while bb[2] - bb[0] > 300:
        f1 = ImageFont.truetype(FN % "Bold", f1.size - 2); bb = d.textbbox((0, 0), big, font=f1)
    d.text((22 - bb[0], 48 - (bb[1] + bb[3]) / 2), big, font=f1, fill=fg)
    f2 = ImageFont.truetype(FN % "Bold", 17); b2 = d.textbbox((0, 0), small, font=f2)
    d.text((492 - b2[2], 48 - (b2[1] + b2[3]) / 2), small, font=f2, fill=fg)
    at.paste(c, (x0, y0)); reg[key] = [x0, y0, x0 + 512, y0 + 96]
a = np.asarray(at, float) / 255.0
a *= (0.90 + 0.10 * np.asarray(Image.fromarray(np.uint8(noise(512, 731, 90) * 255)).resize((1024, 512)), float)[..., None] / 255.0)   # aged lightbox faces
save("lp27_heads", a); at.save(OUT / "lp27_heads_preview.png")
(OUT / "lp27_heads_regions.json").write_text(json.dumps(reg))
sheet = Image.new("RGB", (1536, 1024), (30, 30, 30))
sheet.paste(Image.fromarray(np.uint8(np.clip(w, 0, 1) * 255)), (0, 0)); sheet.paste(Image.fromarray(np.uint8(np.clip(d0, 0, 1) * 255)), (1024, 0))
sheet.paste(Image.fromarray(np.uint8(np.clip(b, 0, 1) * 255)), (1024, 512)); sheet.save(OUT / "preview_sheet.jpg", quality=88)
(OUT / "v270_textures_report.json").write_text(json.dumps(rep, indent=1))
print("DONE", len(rep["files"]))
