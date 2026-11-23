# LONG PIG 2.8.0 textures (owner 2026-11-21 20:31: fewer cracks, tobacco unit like the 24/7 reference). Derived from gs_15am_v270.py.
# OLD HEADER OF 2.7.0 FOLLOWS (band / dado / grime are still the v270 files):
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
OUT = ROOT / "source" / "textures" / "v280"; OUT.mkdir(exist_ok=True)
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
    for _ in range(2):
        x, y = r.randrange(80, N - 80), r.randrange(80, N - 80); pts = [(x, y)]
        for _k in range(r.randrange(8, 18)):
            x += r.randrange(-16, 17); y += r.randrange(8, 26); pts.append((min(max(x, 12), N - 12), min(y, N - 12)))
        d.line(pts, fill=230, width=1)
cr = mask(N, cracks, 0.6)
w *= (1 - 0.22 * cr)[..., None]
def scuffs(d):
    for _ in range(46):
        x, y, L = r.randrange(10, N - 140), r.randrange(10, N - 10), r.randrange(30, 130)
        d.line([(x, y), (x + L, y + r.randrange(-6, 7))], fill=r.randrange(60, 160), width=r.choice((1, 1, 2)))
sc = mask(N, scuffs, 1.0)
w *= (1 - 0.13 * sc)[..., None]
pe = np.clip((noise(N, 706, 14) * 0.6 + noise(N, 707, 5) * 0.4 - 0.775) / 0.03, 0, 1) * np.clip((noise(N, 708, 160) - 0.5) / 0.2, 0, 1)   # flaked paint, in clusters
pe_s = np.asarray(Image.fromarray(np.uint8(pe * 255)).filter(ImageFilter.GaussianBlur(1.6)), float) / 255.0
w *= (1 - 0.35 * np.clip(pe_s - pe, 0, 1))[..., None]                                                     # shadow line round each flake
w = w * (1 - pe[..., None]) + pe[..., None] * np.array([0.74, 0.68, 0.57]) * (0.9 + 0.1 * noise(N, 709, 3))[..., None]
save("lp28_wall", w, src="PaintedPlaster017")
nn = nrm(512, 0.45); cr5 = np.asarray(Image.fromarray(np.uint8(cr * 255)).resize((512, 512), Image.BILINEAR), float) / 255.0
save("lp28_wall_n", nn, src="PaintedPlaster017")
sp = (0.05 + 0.07 * noise(512, 705, 120)) * (1 - 0.5 * np.asarray(Image.fromarray(np.uint8(st * 255)).resize((512, 512)), float) / 255.0)
save("lp28_wall_s", np.repeat(sp[..., None], 3, -1))
# ------------------------------------------------------------------ pegboard (0.2 m tile, 8 x 8 holes) for the tobacco unit
n = 256; pg = np.ones((n, n, 3)) * (np.array((226, 216, 192)) / 255.0); hh = np.zeros((n, n))
yy, xx = np.mgrid[0:n, 0:n]
for i in range(8):
    for j in range(8):
        hh = np.maximum(hh, np.clip(1.6 - np.hypot(xx - (16 + 32 * j), yy - (16 + 32 * i)) / 3.2, 0, 1))
pg = pg * (1 - 0.82 * hh[..., None]) * (0.95 + 0.05 * noise(n, 801, 60))[..., None]
save("lp28_peg", pg)
gy, gx = np.gradient(hh); v = np.dstack([-2.5 * gx, 2.5 * gy, np.ones((n, n))]); v /= np.linalg.norm(v, axis=-1, keepdims=True)
save("lp28_peg_n", v * 0.5 + 0.5); save("lp28_peg_s", np.repeat((0.12 * (1 - hh))[..., None], 3, -1))
# ------------------------------------------------------------------ lit header signs: GTA-universe tobacco brand NAMES in own lettering
# (Lora / Poppins, OFL) - no Rockstar artwork is copied; + own LONG PIG and LOTTO boards. 5 cells 512 x 136 (bay 1.225 x 0.31 m).
G = "/usr/share/fonts/truetype/google-fonts/"
def F(nm, sz):
    try:
        return ImageFont.truetype(G + nm, sz)
    except Exception:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", sz)
RED, WHITE, INK, YEL = (196, 30, 34), (244, 240, 230), (40, 36, 34), (236, 180, 40)
CELLS = (("cardiaque", "Cardiaque", "Lora-BoldItalic.ttf", RED, WHITE, "SMOOTH  &  SLIM"), ("redwood", "Redwood", "Lora-Bold.ttf", WHITE, RED, "FULL FLAVOR"),
         ("longpig", "LONG PIG", "Poppins-Bold.ttf", (116, 70, 57), YEL, "TOBACCO  \u2022  LOTTO  \u2022  CANDY"),
         ("debonaire", "DEBONAIRE", "Lora-Regular.ttf", WHITE, INK, "A FRESH AMERICAN TASTE"), ("lotto", "LOTTO", "Poppins-Bold.ttf", YEL, (176, 40, 30), "SAN ANDREAS  \u2022  SCRATCH & WIN"))
at = Image.new("RGB", (1024, 512), (20, 14, 12)); reg = {}
for k, (key, big, fn, bg, fg, small) in enumerate(CELLS):
    x0, y0 = (k % 2) * 512, (k // 2) * 160 + 8
    c = Image.new("RGB", (512, 136), bg); d = ImageDraw.Draw(c)
    f1 = F(fn, 78); bb = d.textbbox((0, 0), big, font=f1)
    while bb[2] - bb[0] > 430:
        f1 = F(fn, f1.size - 3); bb = d.textbbox((0, 0), big, font=f1)
    d.text((256 - (bb[0] + bb[2]) / 2, 56 - (bb[1] + bb[3]) / 2), big, font=f1, fill=fg)
    f2 = F("Poppins-Bold.ttf", 15); b2 = d.textbbox((0, 0), small, font=f2)
    d.text((256 - (b2[0] + b2[2]) / 2, 112 - (b2[1] + b2[3]) / 2), small, font=f2, fill=fg)
    d.line([(150, 96), (362, 96)], fill=fg, width=2)
    at.paste(c, (x0, y0)); reg[key] = [x0, y0, x0 + 512, y0 + 136]
a = np.asarray(at, float) / 255.0
yy = np.linspace(0, 1, 512)[:, None, None]
a *= (0.92 + 0.08 * np.asarray(Image.fromarray(np.uint8(noise(512, 831, 90) * 255)).resize((1024, 512)), float)[..., None] / 255.0)
save("lp28_heads", a); at.save(OUT / "lp28_heads_preview.png")
(OUT / "lp28_heads_regions.json").write_text(json.dumps(reg))
(OUT / "v280_textures_report.json").write_text(json.dumps(rep, indent=1))
print("DONE", len(rep["files"]))
