# LONG PIG 3.0.0 textures (revision, headers must glow, LONG PIG header out, something on the empty wall):
#   lp30_wall   quiet old plaster: soft stains and a few faint runs only - no cracks, no flakes, no patches; smooth normal
#   lp30_heads  header light boxes: Cardiaque / Redwood / Debonaire / Meteorite / LOTTO (GTA-universe names, own lettering, Lora + Poppins OFL)
#   lp30_deli   painted wall lettering (alpha decal) for the wall behind the counter
import sys, json, hashlib, io, zipfile, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
SRC = ROOT / "source" / "textures" / "v200" / "src"
OUT = ROOT / "source" / "textures" / "v300"; OUT.mkdir(exist_ok=True)
rep = {"sources": {}, "files": {}, "date": "2026-11-22"}
G = "/usr/share/fonts/truetype/google-fonts/"


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


def F(nm, sz):
    try:
        return ImageFont.truetype(G + nm, sz)
    except Exception:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", sz)


# ---------------------------------------------------------------- wall
N = 1024; r = random.Random(30)
c0 = cc("PaintedPlaster017", "Color", N); t = np.tile(c0, (3, 3, 1))
L = (np.asarray(Image.fromarray(np.uint8(t * 255)).filter(ImageFilter.GaussianBlur(2.5)), float)[N:2 * N, N:2 * N] / 255.0) @ np.array([0.299, 0.587, 0.114])
w = np.clip(((L / L.mean() - 1.0) * 0.22 + 1.0)[..., None] * (np.array((214, 198, 164)) / 255.0), 0, 1)
w *= (0.94 + 0.09 * noise(N, 901, 260))[..., None] * (0.98 + 0.035 * noise(N, 902, 80))[..., None]
st = np.clip((noise(N, 903, 150) - 0.62) / 0.30, 0, 1)
w = w * (1 - 0.14 * st[..., None]) + 0.14 * st[..., None] * np.array([0.56, 0.45, 0.29])                 # soft yellowed areas
im = Image.new("L", (N, N), 0); d = ImageDraw.Draw(im)
for _ in range(7):
    x, y, Ln = r.randrange(30, N - 30), r.randrange(0, 200), r.randrange(160, 420)
    d.line([(x, y), (x + r.randrange(-3, 4), y + Ln)], fill=r.randrange(60, 120), width=r.choice((3, 5)))
rn = np.asarray(im.filter(ImageFilter.GaussianBlur(4.0)), float) / 255.0 * np.linspace(1.0, 0.2, N)[:, None]
w = w * (1 - 0.18 * rn[..., None]) + 0.18 * rn[..., None] * np.array([0.44, 0.36, 0.26])                  # a few faint, soft runs
save("lp30_wall", w, src="PaintedPlaster017")
flat = np.zeros((64, 64, 3)); flat[...] = (0.5, 0.5, 1.0)
save("lp30_wall_n", flat)
save("lp30_wall_s", np.repeat((0.05 + 0.05 * noise(256, 904, 80))[..., None], 3, -1))
# ---------------------------------------------------------------- headers (5 cells 512 x 136)
RED, WHITE, INK, YEL, CHOC = (196, 30, 34), (244, 240, 230), (40, 36, 34), (236, 180, 40), (74, 44, 30)
CELLS = (("cardiaque", "Cardiaque", "Lora-BoldItalic.ttf", RED, WHITE, "SMOOTH  &  SLIM"), ("redwood", "Redwood", "Lora-Bold.ttf", WHITE, RED, "FULL FLAVOR"),
         ("meteorite", "METEORITE", "Poppins-Bold.ttf", CHOC, YEL, "CHOCOLATE  •  CANDY  •  GUM"),
         ("debonaire", "DEBONAIRE", "Lora-Regular.ttf", WHITE, INK, "A FRESH AMERICAN TASTE"), ("lotto", "LOTTO", "Poppins-Bold.ttf", YEL, (176, 40, 30), "SAN ANDREAS  •  SCRATCH & WIN"))
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
save("lp30_heads", at); at.save(OUT / "lp30_heads_preview.png")
(OUT / "lp30_heads_regions.json").write_text(json.dumps(reg))
# ---------------------------------------------------------------- painted wall lettering, 1024 x 512, alpha
W_, H_ = 1024, 512
m = Image.new("L", (W_, H_), 0); d = ImageDraw.Draw(m)
f1 = F("Lora-BoldItalic.ttf", 250); bb = d.textbbox((0, 0), "Deli", font=f1)
d.text((W_ / 2 - (bb[0] + bb[2]) / 2, 170 - (bb[1] + bb[3]) / 2), "Deli", font=f1, fill=255)
f2 = F("Poppins-Bold.ttf", 44); s2 = "SANDWICHES  •  COLD CUTS  •  COFFEE"; b2 = d.textbbox((0, 0), s2, font=f2)
d.text((W_ / 2 - (b2[0] + b2[2]) / 2, 420 - (b2[1] + b2[3]) / 2), s2, font=f2, fill=255)
d.line([(120, 350), (904, 350)], fill=255, width=7)
a = np.asarray(m, float) / 255.0
nz = np.asarray(Image.fromarray(np.uint8(np.random.default_rng(31).random((128, 256)) * 255)).resize((W_, H_), Image.BICUBIC), float) / 255.0
fine = np.random.default_rng(32).random((H_, W_))
a = a * np.clip(0.55 + 0.75 * nz, 0, 1) * np.clip(0.80 + 0.5 * fine, 0, 1) * 0.88                          # sun-faded, brushed paint
rgb = np.zeros((H_, W_, 3)); rgb[...] = np.array((112, 60, 48)) / 255.0
save("lp30_deli", Image.fromarray(np.uint8(np.dstack([rgb, a[..., None]]) * 255 + 0.5), "RGBA"), "DXT5")
Image.fromarray(np.uint8(np.dstack([rgb, a[..., None]]) * 255 + 0.5), "RGBA").save(OUT / "lp30_deli_preview.png")
(OUT / "v300_textures_report.json").write_text(json.dumps(rep, indent=1))
print("DONE", len(rep["files"]))
