# LONG PIG — v0.2.5 STYLE RESET textures ("South Los Santos 1995-2001, worn, not antique"; see docs/style_reset/*).
# Every texture here is DERIVED from our own v0.2.x textures (which are CC0 derivatives or original procedural work, see
# assets/registry.json) or ORIGINAL procedural / typographic work. No third-party pixels, no Rockstar textures.
#   python gs_15g_make_v025_textures.py [<project_root>]      -> source/textures/v025/*.dds + lp4_textures_report.json
# Aging is authored per element (tile-by-tile glaze variation, replaced tiles, dirty grout, repaint patches), all TILEABLE:
# per-tile random values are keyed by the tile centroid modulo the texture size, noise is generated on a wrapped lattice.
import sys, json, hashlib, math, colorsys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage as ndi

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds  # noqa: E402

T = ROOT / "source" / "textures"
V023, V021, SLICE = T / "v023", T / "v021", T / "slice"
OUT = T / "v025"
OUT.mkdir(parents=True, exist_ok=True)
FONT = Path("/usr/share/fonts/truetype/dejavu")
REPORT = {"script": "source/scripts/gs_15g_make_v025_textures.py", "version": "0.2.5", "textures": []}
SEED = 20261101 + 25


def font(name, size):
    for base in (FONT, Path(r"C:\Windows\Fonts")):
        p = base / name
        if p.is_file():
            return ImageFont.truetype(str(p), size)
    return ImageFont.truetype(name, size)


def rel(p):
    return str(Path(p).relative_to(ROOT)).replace("\\", "/")


def arr(img):
    return np.asarray(img.convert("RGB"), dtype=np.float64) / 255.0


def to_img(a, mode="RGB"):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), mode)


def save(name, img, fmt="DXT1", role="diffuse", derived=(), ops=""):
    png = OUT / f"{name}.png"
    img.save(png)
    gs_dds.convert(png, OUT / f"{name}.dds", fmt)
    data = (OUT / f"{name}.dds").read_bytes()
    REPORT["textures"].append({"name": name, "file": f"{name}.dds", "size": list(img.size), "format": fmt, "role": role,
                               "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                               "derived_from": [rel(d) for d in derived],
                               "origin": "derived_own" if derived else "original_procedural", "operations": ops})
    print("TEX", name, img.size, fmt, len(data))


def tnoise(h, w, cy, cx, seed, octaves=4, persist=0.55):
    """Tileable value noise in [0,1] (h x w), base lattice cy x cx."""
    r = np.random.default_rng(seed)
    acc = np.zeros((h, w)); amp = 1.0; tot = 0.0
    for o in range(octaves):
        gy, gx = cy * 2 ** o, cx * 2 ** o
        if gy > h // 2 or gx > w // 2:
            break
        lat = (r.random((gy, gx)) * 255).astype(np.uint8)
        big = Image.fromarray(np.tile(lat, (3, 3)), "L").resize((w * 3, h * 3), Image.Resampling.BICUBIC)
        acc += amp * np.asarray(big, dtype=np.float64)[h:2 * h, w:2 * w] / 255.0
        tot += amp; amp *= persist
    return acc / tot


def tile_values(mask, seed, nvals=4):
    """Per connected component of `mask` (tileable): `nvals` uniform random values in [0,1] + label image."""
    h, w = mask.shape
    big = np.tile(mask, (3, 3))
    lab, n = ndi.label(big)
    idx = np.arange(1, n + 1)
    cy = np.asarray(ndi.mean(np.repeat(np.arange(3 * h)[:, None], 3 * w, 1), lab, idx))
    cx = np.asarray(ndi.mean(np.repeat(np.arange(3 * w)[None, :], 3 * h, 0), lab, idx))
    keys = (np.round(cy % h / 6).astype(np.int64) * 100003 + np.round(cx % w / 6).astype(np.int64))
    vals = np.zeros((n + 1, nvals))
    for i, k in enumerate(keys):
        vals[i + 1] = np.random.default_rng(seed * 7919 + int(k)).random(nvals)
    center = lab[h:2 * h, w:2 * w]
    return vals[center], center


def hsv_adjust(a, sat=1.0, val=1.0, hue_shift=0.0):
    img = to_img(a).convert("HSV")
    hsv = np.asarray(img, dtype=np.float64) / 255.0
    hsv[..., 0] = (hsv[..., 0] + hue_shift) % 1.0
    hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 1)
    hsv[..., 2] = np.clip(hsv[..., 2] * val, 0, 1)
    return arr(Image.fromarray((hsv * 255).astype(np.uint8), "HSV").convert("RGB"))


def col(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def blur(a, r):
    if a.ndim == 2:
        return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(r)), dtype=np.float64) / 255.0
    return arr(to_img(a).filter(ImageFilter.GaussianBlur(r)))


# ======================================================================== 1. faded oxblood wall tile (lower walls)
src = V023 / "lp3_tile_red.png"
a = arr(Image.open(src))
s_ = np.asarray(Image.open(src).convert("HSV"), dtype=np.float64)[..., 1] / 255.0
grout = s_ < 0.5
tv, _ = tile_values(~grout, SEED + 1, 4)
base = hsv_adjust(a, sat=0.58, val=0.86, hue_shift=0.008)           # dusty brick-red / faded oxblood
lum = base.mean(2, keepdims=True)
var = (tv[..., 0:1] - 0.5) * 0.13                                     # glaze lot variation tile to tile
base = base * (1 + var)
repl = (tv[..., 1] > 0.955)[..., None]                               # ~4 % replacement tiles: browner, slightly glossier
base = np.where(repl, hsv_adjust(base, sat=0.85, val=1.05, hue_shift=0.025), base)
dust = tnoise(1024, 1024, 4, 4, SEED + 2)[..., None]
base = base * (0.93 + 0.10 * dust) + 0.035 * (dust - 0.5)
# crazing: fine hairline cracks on ~15 % of tiles
craz = np.zeros((1024, 1024))
im = Image.new("L", (1024, 1024), 0); d = ImageDraw.Draw(im)
r = np.random.default_rng(SEED + 3)
for k in range(260):
    x, y = r.uniform(0, 1024), r.uniform(0, 1024)
    pts = [(x, y)]
    for j in range(r.integers(3, 7)):
        x += r.normal(0, 9); y += r.normal(0, 9); pts.append((x, y))
    d.line(pts, fill=int(r.uniform(60, 140)), width=1)
craz = np.asarray(im, dtype=np.float64) / 255.0 * (tv[..., 2] > 0.85)
base = base * (1 - 0.18 * craz[..., None])
# dirty grout: grey-brown, darker at the bottom of each course (dust settles)
gcol = col("#7d7166") * (0.8 + 0.25 * tnoise(1024, 1024, 8, 8, SEED + 4))[..., None]
base = np.where(grout[..., None], gcol, base)
save("lp4_tile_red", to_img(base), derived=[src], ops="desaturate/darken to faded oxblood, per-tile glaze variation, ~4% replacement tiles, crazing, dusty grey-brown grout")

# ======================================================================== 2. aged white subway tile (splashback)
src = V023 / "lp3_tile_white.png"
a = arr(Image.open(src))
v_ = np.asarray(Image.open(src).convert("HSV"), dtype=np.float64)[..., 2] / 255.0
grout = v_ < 0.80
tv, _ = tile_values(~grout, SEED + 11, 3)
base = a * col("#f7f1e4") / col("#ffffff") * 0.985                    # slightly yellowed glaze
base = base * (1 + (tv[..., 0:1] - 0.5) * 0.06)
newt = (tv[..., 1] > 0.965)[..., None]
base = np.where(newt, np.clip(base * col("#ffffff") / col("#f7f1e4") * 1.01, 0, 1), base)   # a whiter replacement tile
base = np.where(grout[..., None], col("#8f8476") * (0.85 + 0.2 * tnoise(1024, 1024, 8, 8, SEED + 12))[..., None], base)
save("lp4_tile_white", to_img(base), derived=[src], ops="yellowed glaze, tile-to-tile variation, one whiter replacement tile per repeat, grease-grey grout")

# ======================================================================== 3. painted CMU / brick, aged cream with repaint patches
src = V023 / "lp3_paintbrick.png"
a = arr(Image.open(src))
N = a.shape[0]
base = a * (col("#e3d8bf") / a.reshape(-1, 3).mean(0))                 # warm faded cream
base = hsv_adjust(base, sat=0.95, val=0.97)
# repaint patches: soft-edged rectangles of slightly different cream (fresh paint lighter, old paint yellower)
pm = Image.new("L", (N, N), 128); d = ImageDraw.Draw(pm)
r = np.random.default_rng(SEED + 21)
for k in range(9):
    x0, y0 = r.uniform(0, N), r.uniform(0, N)
    w_, h_ = r.uniform(N * 0.08, N * 0.3), r.uniform(N * 0.06, N * 0.22)
    vv = int(128 + r.choice([-1, 1]) * r.uniform(18, 34))
    for ox in (-N, 0, N):
        for oy in (-N, 0, N):
            d.rectangle((x0 + ox, y0 + oy, x0 + w_ + ox, y0 + h_ + oy), fill=vv)
pm = (np.asarray(pm.filter(ImageFilter.GaussianBlur(6)), dtype=np.float64) - 128) / 128.0
base = base * (1 + 0.06 * pm[..., None]) + np.array([0.0, 0.0, -0.025]) * np.clip(-pm, 0, 1)[..., None]
dirt = tnoise(N, N, 4, 4, SEED + 22)
base = base * (0.95 + 0.07 * dirt[..., None])
save("lp4_paintbrick", to_img(base), derived=[src], ops="recolour to aged cream, soft repaint patches (lighter / yellower), low-frequency dust")

# ======================================================================== 4. aged black / off-white checker floor
src = V023 / "lp3_floor_bw.png"
a = arr(Image.open(src))
v_ = np.asarray(Image.open(src).convert("HSV"), dtype=np.float64)[..., 2] / 255.0
blk, wht = v_ < 0.35, v_ > 0.65
tvb, _ = tile_values(blk, SEED + 31, 3)
tvw, _ = tile_values(wht, SEED + 32, 3)
t = np.clip((v_ - 0.10) / 0.82, 0, 1)[..., None]                     # 0 = black tile, 1 = white tile
dark, light = col("#2b2927"), col("#dcd4c2")
base = dark * (1 - t) + light * t
base = base * (1 + np.where(blk, (tvb[..., 0] - 0.5) * 0.18, (tvw[..., 0] - 0.5) * 0.07)[..., None])
base = base + (a - a.mean(2, keepdims=True)) * 0.5                   # keep the original surface grain
wear = tnoise(1024, 1024, 3, 3, SEED + 33)
base = base * (0.94 + 0.08 * wear[..., None]) + 0.03 * (wear[..., None] - 0.5)
# chips at a few tile corners (lighter substrate showing on black, grey on white)
im = Image.new("L", (1024, 1024), 0); d = ImageDraw.Draw(im)
r = np.random.default_rng(SEED + 34)
step = 1024 / 6
for k in range(14):
    cx, cy = step * r.integers(0, 7), step * r.integers(0, 7)
    rr = r.uniform(3, 7)
    d.ellipse((cx - rr, cy - rr, cx + rr * 1.6, cy + rr), fill=255)
chips = np.asarray(im.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float64)[..., None] / 255.0
base = base * (1 - chips) + col("#8a8174") * chips
save("lp4_floor_bw", to_img(base), derived=[src], ops="lower contrast: charcoal + aged off-white, per-tile variation, traffic dulling, corner chips")
fs = Image.open(SLICE / "lp_floor_checker_s.png").convert("RGB") if (SLICE / "lp_floor_checker_s.png").is_file() else Image.new("RGB", (512, 512), (90, 90, 90))
fsa = arr(fs) * 0.55
save("lp4_floor_s", to_img(fsa), role="spec", derived=[SLICE / "lp_floor_checker_s.png"], ops="specular x0.55 (dull, walked-on vinyl)")

# ======================================================================== 5. yellowed acoustic ceiling tile
src = V023 / "lp3_ceiling_tile.png"
a = arr(Image.open(src))
N = a.shape[0]
v_ = np.asarray(Image.open(src).convert("HSV"), dtype=np.float64)[..., 2] / 255.0
tiles = v_ > 0.72
tv, _ = tile_values(tiles, SEED + 41, 3)
base = a * (col("#dcd4bd") / a.reshape(-1, 3).mean(0))
base = base * (1 + (tv[..., 0:1] - 0.5) * 0.08)
newt = ((tv[..., 1] > 0.975) & tiles)[..., None]                      # replaced tile: whiter, cleaner
base = np.where(newt, base * (col("#e8e3d6") / col("#dcd4bd")), base)
base = base * (0.96 + 0.06 * tnoise(N, N, 4, 4, SEED + 42)[..., None])
save("lp4_ceiling_tile", to_img(base), derived=[src], ops="yellowed acoustic tile, tile-to-tile tone variation, rare whiter replacement tile")

# ======================================================================== 6. dull oxblood vinyl + worn laminates
src = V023 / "lp3_vinyl_red.png"
a = arr(Image.open(src))
base = hsv_adjust(a, sat=0.62, val=0.70, hue_shift=0.006)
wear = tnoise(1024, 1024, 5, 5, SEED + 51, octaves=5)
crease = np.clip((wear - 0.62) * 3.0, 0, 1)[..., None]
base = base * (1 - 0.0 * crease) + (base * 1.35 + 0.04) * crease * 0.55 + base * crease * -0.55   # rubbed lighter patches
save("lp4_vinyl_red", to_img(base), derived=[src], ops="desaturate/darken to dull oxblood, rubbed lighter wear patches")
src = V023 / "lp3_laminate_red.png"
a = arr(Image.open(src))
base = hsv_adjust(a, sat=0.55, val=0.78, hue_shift=0.02)               # muted brown-burgundy laminate
base = base * (0.95 + 0.08 * tnoise(1024, 1024, 6, 6, SEED + 52)[..., None])
save("lp4_laminate_red", to_img(base), derived=[src], ops="muted brown-burgundy, low-frequency rubbing")
src = V023 / "lp3_laminate_cream.png"
a = arr(Image.open(src))
base = a * (col("#e1d6bd") / a.reshape(-1, 3).mean(0))
im = Image.new("L", (1024, 1024), 0); d = ImageDraw.Draw(im)
r = np.random.default_rng(SEED + 53)
for k in range(220):                                                   # fine scratches
    x, y = r.uniform(0, 1024), r.uniform(0, 1024); ang = r.uniform(0, math.pi); L = r.uniform(10, 70)
    d.line((x, y, x + L * math.cos(ang), y + L * math.sin(ang)), fill=int(r.uniform(40, 110)), width=1)
for k in range(5):                                                     # faint cup rings
    x, y, rr = r.uniform(80, 940), r.uniform(80, 940), r.uniform(22, 30)
    d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=70, width=3)
sc = np.asarray(im.filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float64)[..., None] / 255.0
base = base * (1 - 0.22 * sc)
save("lp4_laminate_cream", to_img(base), derived=[src], ops="yellowed cream laminate, fine scratches, faint cup rings")

# ======================================================================== 7. faded menus, yellowed troffer lens, faded flag
src = V023 / "lp3_menu.png"
a = arr(Image.open(src))
H_, W_ = a.shape[:2]
base = hsv_adjust(a, sat=0.62, val=0.97)
base = base * col("#fbf1dc") / col("#ffffff")                         # yellowed backlit film
xx = np.linspace(0, 1, W_)[None, :, None]
base = base + 0.06 * (1 - xx) * (1 - base)                            # sun-fade from the window side
img = to_img(base)
d = ImageDraw.Draw(img)
r = np.random.default_rng(SEED + 61)
f = font("DejaVuSansCondensed-Bold.ttf", 34)
for (x, y, txt) in ((int(W_ * 0.405), int(H_ * 0.80), "3.25"), (int(W_ * 0.645), int(H_ * 0.86), "1.95"),
                    (int(W_ * 0.93), int(H_ * 0.30), "7.25")):      # stick-on price corrections (newer, whiter labels)
    d.rectangle((x - 46, y - 22, x + 46, y + 22), fill=(246, 244, 236))
    d.text((x - 38, y - 19), txt, fill=(40, 34, 30), font=f)
save("lp4_menu", img, derived=[src], ops="faded / yellowed backlit menu film, sun-fade gradient, 3 stick-on price corrections")
src = V023 / "lp3_troffer.png"
save("lp4_troffer", to_img(arr(Image.open(src)) * col("#f6edd6")), derived=[src], ops="slightly yellowed fluorescent diffuser")
src = V021 / "lp2_flag.png"
a = arr(Image.open(src))
base = hsv_adjust(a, sat=0.50, val=0.92)
base = base * 0.88 + col("#d8cdb4") * 0.12                            # sun-bleached cloth
base = base * (0.93 + 0.09 * tnoise(a.shape[0], a.shape[1], 4, 4, SEED + 62)[..., None])
save("lp4_flag", to_img(base), derived=[src], ops="sun-bleached tricolore: desaturated, cream cast, dust")

# ======================================================================== 8. ORIGINAL notices atlas (paper goods of a 1990s LA-style deli)
# 1024 x 1024: 3 columns x 4 rows of 256 x 256 cells on the left (index = row * 3 + col), the right column is two
# 256 x 512 letterboards.  Cell list is mirrored in gs_v025_kit.NOTICE_CELLS.
A = Image.new("RGB", (1024, 1024), (230, 224, 210))
D = ImageDraw.Draw(A)
r = np.random.default_rng(SEED + 71)


def cell_box(i):
    cx, cy = i % 3, i // 3
    return (cx * 256, cy * 256, cx * 256 + 256, cy * 256 + 256)


def paper(box, colr=(236, 230, 214), border=None):
    D.rectangle(box, fill=colr)
    if border:
        D.rectangle((box[0] + 6, box[1] + 6, box[2] - 7, box[3] - 7), outline=border, width=3)


def ctext(box, y, txt, f, fill=(30, 30, 30)):
    w = D.textlength(txt, font=f)
    D.text(((box[0] + box[2]) / 2 - w / 2, box[1] + y), txt, fill=fill, font=f)


def hand(box, x, y, txt, size=19, fill=(28, 40, 90)):
    """Pseudo hand lettering: oblique glyphs with per-letter jitter."""
    f = font("DejaVuSans-Oblique.ttf", size)
    for ch in txt:
        D.text((box[0] + x, box[1] + y + r.normal(0, 0.8)), ch, fill=fill, font=f)
        x += D.textlength(ch, font=f) * r.uniform(0.92, 1.04)


def pig(cx, cy, s, fill):
    """Simple ORIGINAL pig mark (not the GTA logo): body ellipse, head circle, ear, snout, legs, curly tail."""
    D.ellipse((cx - 1.0 * s, cy - 0.55 * s, cx + 0.7 * s, cy + 0.5 * s), fill=fill)
    D.ellipse((cx + 0.45 * s, cy - 0.62 * s, cx + 1.15 * s, cy + 0.08 * s), fill=fill)
    D.polygon([(cx + 0.62 * s, cy - 0.55 * s), (cx + 0.72 * s, cy - 0.9 * s), (cx + 0.86 * s, cy - 0.58 * s)], fill=fill)
    D.ellipse((cx + 1.02 * s, cy - 0.38 * s, cx + 1.3 * s, cy - 0.12 * s), fill=fill)
    for lx in (-0.75, -0.35, 0.15, 0.45):
        D.rectangle((cx + lx * s, cy + 0.35 * s, cx + (lx + 0.16) * s, cy + 0.78 * s), fill=fill)
    D.arc((cx - 1.32 * s, cy - 0.45 * s, cx - 0.92 * s, cy - 0.05 * s), 90, 400, fill=fill, width=max(2, int(s * 0.08)))


B = font("DejaVuSans-Bold.ttf", 22); Bs = font("DejaVuSans-Bold.ttf", 15); Rg = font("DejaVuSans.ttf", 13)
Rs = font("DejaVuSans.ttf", 11); Se = font("DejaVuSerif-Bold.ttf", 20); Mo = font("DejaVuSansMono.ttf", 11)
# 0 food service permit
b = cell_box(0); paper(b, (240, 236, 222), (90, 110, 140))
ctext(b, 16, "COUNTY OF LOS SANTOS", Bs, (40, 60, 100)); ctext(b, 36, "DEPARTMENT OF PUBLIC HEALTH", Rs, (40, 60, 100))
ctext(b, 62, "FOOD SERVICE PERMIT", font("DejaVuSerif-Bold.ttf", 16), (25, 25, 25))
for i, line in enumerate(("LONG PIG DELI & MARKET", "JAMESTOWN ST.  RANCHO", "PERMIT NO. 0427-95", "CLASS: RETAIL FOOD / DELI", "VALID THROUGH 12-31-2001")):
    ctext(b, 100 + i * 19, line, Rg)
D.ellipse((b[0] + 24, b[1] + 196, b[0] + 74, b[1] + 246), outline=(150, 60, 50), width=3)
D.text((b[0] + 34, b[1] + 214), "SEAL", fill=(150, 60, 50), font=Rs)
hand(b, 120, 214, "R. Delgado", 16, (20, 30, 80))
# 1 letter grade card "A"
b = cell_box(1); paper(b, (244, 242, 236), (40, 80, 160))
ctext(b, 14, "COUNTY OF LOS SANTOS", Bs, (40, 80, 160)); ctext(b, 33, "RESTAURANT GRADE", Rg, (40, 80, 160))
ctext(b, 48, "A", font("DejaVuSans-Bold.ttf", 150), (36, 78, 168))
ctext(b, 226, "SCORE 90-100", Rs, (40, 80, 160))
# 2 calendar November 2001 with the shop pig
b = cell_box(2); paper(b, (242, 238, 228))
D.rectangle((b[0], b[1], b[2], b[1] + 92), fill=(176, 64, 56)); pig(b[0] + 104, b[1] + 50, 30, (236, 226, 206))
ctext(b, 96, "LONG PIG  ·  DELI & MARKET", Rs, (60, 60, 60)); ctext(b, 112, "NOVEMBER  2001", Bs, (40, 40, 40))
for j, dname in enumerate("SMTWTFS"):
    D.text((b[0] + 18 + j * 32, b[1] + 134), dname, fill=(150, 60, 50) if j == 0 else (60, 60, 60), font=Rs)
day = 1
for wk in range(5):
    for j in range(7):
        if (wk == 0 and j < 4) or day > 30:
            continue
        D.text((b[0] + 18 + j * 32, b[1] + 152 + wk * 20), str(day), fill=(50, 50, 50), font=Rs); day += 1
D.ellipse((b[0] + 79, b[1] + 209, b[0] + 101, b[1] + 227), outline=(200, 40, 40), width=2)
# 3 staff schedule (hand)
b = cell_box(3); paper(b, (246, 246, 240))
for k in range(12):
    D.line((b[0] + 8, b[1] + 46 + k * 17, b[2] - 8, b[1] + 46 + k * 17), fill=(170, 190, 215), width=1)
D.line((b[0] + 70, b[1] + 40, b[0] + 70, b[3] - 10), fill=(210, 140, 140), width=1)
hand(b, 14, 10, "SCHEDULE wk of 11/5", 18, (30, 30, 30))
for k, (n, sh) in enumerate((("TONY", "6a-2p  M-F"), ("MARIA", "11-7  T-Sa"), ("LUIS", "2-10  W-Su"), ("DEE", "6a-2p Sa/Su"),
                              ("FRANKIE", "close Fri"), ("", ""), ("NO SWAPS w/o", ""), ("asking ME  - Sal", ""))):
    hand(b, 14, 31 + (k + 1) * 17, n, 14); hand(b, 80, 31 + (k + 1) * 17, sh, 14)
# 4 CASH ONLY / 5 NO LOITERING (store-bought signs)
b = cell_box(4); paper(b, (238, 232, 214)); D.rectangle((b[0] + 10, b[1] + 60, b[2] - 10, b[1] + 196), outline=(150, 40, 36), width=5)
ctext(b, 82, "CASH", font("DejaVuSans-Bold.ttf", 46), (150, 40, 36)); ctext(b, 136, "ONLY", font("DejaVuSans-Bold.ttf", 46), (150, 40, 36))
ctext(b, 206, "SORRY - NO CHECKS", Rs, (90, 80, 70))
b = cell_box(5); paper(b, (232, 226, 206)); D.rectangle((b[0], b[1] + 50, b[2], b[1] + 206), fill=(34, 34, 34))
ctext(b, 70, "NO", font("DejaVuSans-Bold.ttf", 44), (236, 214, 60)); ctext(b, 122, "LOITERING", font("DejaVuSans-Bold.ttf", 34), (236, 214, 60))
ctext(b, 166, "VIOLATORS WILL BE PROSECUTED", Rs, (220, 210, 190))
# 6 hand-written special on lined paper
b = cell_box(6); paper(b, (248, 244, 222))
for k in range(13):
    D.line((b[0], b[1] + 30 + k * 17, b[2], b[1] + 30 + k * 17), fill=(160, 185, 215), width=1)
hand(b, 18, 20, "TODAY'S SPECIAL!!", 23, (170, 30, 30))
hand(b, 18, 66, "Meatball hero", 22, (25, 30, 80)); hand(b, 18, 96, "w/ provolone", 22, (25, 30, 80))
hand(b, 18, 130, "+ soda  $4.25", 24, (25, 30, 80)); hand(b, 18, 176, "Lasagna Fri only", 19, (25, 30, 80))
# 7 cork community board with flyers
b = cell_box(7)
cork = (np.random.default_rng(SEED + 72).random((256, 256, 1)) * 0.25 + 0.75) * np.array([0.69, 0.52, 0.33])
A.paste(to_img(cork).filter(ImageFilter.GaussianBlur(0.6)), (b[0], b[1]))
D = ImageDraw.Draw(A)
for (x0, y0, w_, h_, c_, lines) in ((14, 14, 96, 120, (244, 240, 226), ["ROOM", "for rent", "no pets", "555-0142"]),
                                    (122, 22, 118, 90, (246, 214, 214), ["LOST CAT", "grey tabby", "REWARD"]),
                                    (24, 146, 104, 98, (214, 232, 246), ["ST. MARY'S", "RAFFLE", "Dec 9"]),
                                    (138, 124, 104, 120, (250, 244, 196), ["GUITAR", "LESSONS", "$10/hr", "ask Luis"])):
    D.rectangle((b[0] + x0, b[1] + y0, b[0] + x0 + w_, b[1] + y0 + h_), fill=c_, outline=(170, 160, 140))
    for k, ln in enumerate(lines):
        D.text((b[0] + x0 + 8, b[1] + y0 + 10 + k * 22), ln, fill=(40, 40, 40), font=Bs if k == 0 else Rg)
    D.ellipse((b[0] + x0 + w_ / 2 - 4, b[1] + y0 + 2, b[0] + x0 + w_ / 2 + 4, b[1] + y0 + 10), fill=(200, 40, 40))
# 8 old store photo (1979 opening), drawn sepia — original illustration
b = cell_box(8); paper(b, (236, 230, 216))
ph = Image.new("RGB", (220, 170), (150, 128, 100)); pd = ImageDraw.Draw(ph)
pd.rectangle((0, 120, 220, 170), fill=(120, 100, 80)); pd.rectangle((20, 40, 200, 122), fill=(176, 152, 120))
pd.rectangle((20, 26, 200, 46), fill=(92, 70, 52)); pd.text((60, 29), "LONG  PIG", fill=(230, 212, 180), font=Bs)
pd.rectangle((36, 60, 96, 118), fill=(110, 90, 70)); pd.rectangle((120, 60, 184, 118), fill=(110, 90, 70))
for fx in (54, 84, 140, 168):
    pd.ellipse((fx - 6, 92, fx + 6, 104), fill=(60, 48, 38)); pd.rectangle((fx - 7, 104, fx + 7, 140), fill=(60, 48, 38))
ph = ph.filter(ImageFilter.GaussianBlur(1.1))
A.paste(ph, (b[0] + 18, b[1] + 16)); D = ImageDraw.Draw(A)
hand(b, 22, 196, "grand opening  -  '79", 17, (70, 60, 50))
# 9 faded espresso poster (original typographic)
b = cell_box(9); paper(b, (222, 210, 184))
D.rectangle((b[0] + 12, b[1] + 12, b[2] - 12, b[3] - 12), outline=(120, 60, 50), width=4)
ctext(b, 30, "CAFFÈ", font("DejaVuSerif-Bold.ttf", 40), (110, 58, 48)); ctext(b, 80, "ESPRESSO", font("DejaVuSerif-Bold.ttf", 30), (110, 58, 48))
D.ellipse((b[0] + 98, b[1] + 124, b[0] + 158, b[1] + 172), outline=(80, 60, 50), width=4); D.arc((b[0] + 152, b[1] + 132, b[0] + 176, b[1] + 160), 270, 90, fill=(80, 60, 50), width=4)
ctext(b, 186, "come una volta", font("DejaVuSerif-Italic.ttf", 18), (80, 70, 60)); ctext(b, 212, "50¢", Bs, (110, 58, 48))
# 10 newspaper clipping
b = cell_box(10); paper(b, (226, 220, 200))
ctext(b, 10, "LOS SANTOS METRO", font("DejaVuSerif-Bold.ttf", 16), (40, 40, 40)); D.line((b[0] + 10, b[1] + 32, b[2] - 10, b[1] + 32), fill=(60, 60, 60), width=2)
ctext(b, 40, "Rancho deli marks 20 years", font("DejaVuSerif-Bold.ttf", 15), (30, 30, 30))
ph = Image.new("RGB", (100, 80), (140, 136, 128)); pd = ImageDraw.Draw(ph); pd.ellipse((30, 12, 70, 52), fill=(80, 78, 74)); pd.rectangle((24, 50, 76, 80), fill=(80, 78, 74))
A.paste(ph.filter(ImageFilter.GaussianBlur(0.8)), (b[0] + 14, b[1] + 66)); D = ImageDraw.Draw(A)
for k in range(9):
    D.line((b[0] + 124, b[1] + 70 + k * 10, b[2] - 12, b[1] + 70 + k * 10), fill=(110, 110, 104), width=3)
for k in range(8):
    D.line((b[0] + 14, b[1] + 158 + k * 10, b[2] - 12 - (40 if k == 7 else 0), b[1] + 158 + k * 10), fill=(110, 110, 104), width=3)
# 11 "WE CARD" sticker + phone numbers
b = cell_box(11); paper(b, (238, 236, 230))
D.rectangle((b[0] + 14, b[1] + 14, b[2] - 14, b[1] + 120), fill=(30, 70, 140)); ctext(b, 26, "WE CARD", font("DejaVuSans-Bold.ttf", 34), (250, 250, 250))
ctext(b, 72, "UNDER 21? NO BEER & WINE", Rs, (250, 250, 250)); ctext(b, 92, "BORN AFTER 11/05/1980", Rs, (250, 250, 250))
for k, ln in enumerate(("DELIVERY  555-0180", "BAKERY  Tue/Fri 6am", "ICE  555-0119")):
    hand(b, 18, 140 + k * 30, ln, 17, (40, 40, 40))
# right column: two black felt letterboards (256 x 512 each)
for k, lines in enumerate((["TODAY'S", "SPECIALS", "", "MEATBALL HERO", "  4.25", "EGGPLANT PARM", "  4.75", "SOUP DU JOUR", "  1.95",
                             "COFFEE  .75"],
                            ["SANDWICHES", "HALF / WHOLE", "", "ITALIAN COMBO", " 3.50  5.95", "TURKEY", " 3.25  5.50",
                             "HAM & SWISS", " 3.25  5.50", "PASTRAMI", " 3.75  6.25"])):
    x0, y0 = 768, k * 512
    D.rectangle((x0, y0, x0 + 256, y0 + 512), fill=(36, 34, 33))
    for g in range(0, 512, 6):
        D.line((x0, y0 + g, x0 + 256, y0 + g), fill=(44, 42, 41), width=1)               # felt grooves
    for i, ln in enumerate(lines):
        f = font("DejaVuSansCondensed-Bold.ttf", 30 if i < 2 else 23)
        yy = y0 + 22 + i * 46 + (0 if i < 2 else -10)
        xx = x0 + 14
        for ch in ln:                                                                      # plastic letters, a bit crooked
            D.text((xx, yy + r.normal(0, 1.0)), ch, fill=(232, 228, 218) if i != 1 else (222, 88, 70), font=f)
            xx += D.textlength(ch, font=f) + 1
    D.rectangle((x0 + 2, y0 + 2, x0 + 253, y0 + 509), outline=(150, 150, 148), width=4)    # aluminium frame edge
na = arr(A)
na = na * (0.96 + 0.06 * tnoise(1024, 1024, 8, 8, SEED + 73)[..., None])                 # paper tooth / yellowing
save("lp4_notices", to_img(na), ops="ORIGINAL typographic / drawn notices atlas: health permit, grade card, calendar 2001, staff schedule, CASH ONLY, NO LOITERING, special, cork flyers, 1979 shop photo, espresso poster, clipping, WE CARD, 2 letterboards")

# ======================================================================== 9. ORIGINAL wear decal atlas (DXT5) — 4 x 2 cells of 256 x 256
W8 = np.zeros((512, 1024, 4))
yy, xx = np.mgrid[0:256, 0:256] / 255.0
def put(i, rgb, alpha):
    cx, cy = i % 4, i // 4
    W8[cy * 256:(cy + 1) * 256, cx * 256:(cx + 1) * 256, :3] = rgb
    W8[cy * 256:(cy + 1) * 256, cx * 256:(cx + 1) * 256, 3] = np.clip(alpha, 0, 1)
n1 = tnoise(256, 256, 4, 4, SEED + 81); n2 = tnoise(256, 256, 8, 8, SEED + 82)
edge = np.minimum(np.minimum(xx, 1 - xx), np.minimum(yy, 1 - yy))
fadeE = np.clip(edge * 8, 0, 1)
# 0 wall-base grime strip (strong at v=1 -> bottom)
put(0, np.dstack([0.17 + 0.05 * n1, 0.13 + 0.04 * n1, 0.09 + 0.03 * n1]), (yy ** 2.2) * (0.5 + 0.5 * n1) * 0.85 * np.clip(np.minimum(xx, 1 - xx) * 12, 0, 1))
# 1 floor traffic wear (soft, slightly lighter/greyer) — alpha only, grey-brown
rr = np.hypot(xx - 0.5, yy - 0.5) / 0.5
put(1, np.dstack([0.32 + 0 * xx, 0.29 + 0 * xx, 0.25 + 0 * xx]), np.clip(1 - rr, 0, 1) ** 1.3 * (0.35 + 0.65 * n1) * 0.55)
# 2 drips (wall)
dr = np.zeros((256, 256)); rd = np.random.default_rng(SEED + 83)
for k in range(8):
    x = int(rd.uniform(20, 236)); L = int(rd.uniform(60, 230)); w_ = rd.uniform(1.5, 4)
    for y in range(4, min(255, 4 + L)):
        dr[y, max(0, int(x - w_)):int(x + w_)] = max(dr[y, max(0, int(x - w_))], 1 - y / (L + 10))
put(2, np.dstack([0.22 + 0 * xx, 0.17 + 0 * xx, 0.11 + 0 * xx]), blur(dr, 1.0) * 0.6 * fadeE)
# 3 heel marks / rubber scuffs (floor or kick plates)
sc = Image.new("L", (256, 256), 0); d = ImageDraw.Draw(sc); rd = np.random.default_rng(SEED + 84)
for k in range(26):
    x, y = rd.uniform(20, 236), rd.uniform(20, 236); ang = rd.uniform(-0.6, 0.6); L = rd.uniform(8, 34)
    d.line((x, y, x + L * math.cos(ang), y + L * math.sin(ang)), fill=int(rd.uniform(120, 230)), width=int(rd.uniform(2, 5)))
put(3, np.dstack([0.06 + 0 * xx] * 3), blur(np.asarray(sc, dtype=np.float64) / 255.0, 0.7) * 0.75 * fadeE)
# 4 ceiling water stain: brown tide rings
ring = np.zeros((256, 256))
for k, (rad, wdt, a_) in enumerate(((0.36, 0.035, 0.7), (0.28, 0.025, 0.45), (0.18, 0.03, 0.3))):
    rr2 = np.hypot(xx - 0.5 + 0.03 * k, yy - 0.5) * (1 + 0.15 * (n1 - 0.5))
    ring = np.maximum(ring, a_ * np.exp(-((rr2 - rad) / wdt) ** 2))
fill_ = np.clip(1 - np.hypot(xx - 0.5, yy - 0.5) / 0.36, 0, 1) * 0.18
put(4, np.dstack([0.45 + 0 * xx, 0.33 + 0 * xx, 0.18 + 0 * xx]), (ring + fill_) * fadeE)
# 5 plaster patch (lighter, slightly rough, sanded edge)
pp = np.clip((0.42 - np.maximum(abs(xx - 0.5) * 1.1, abs(yy - 0.5))) * 9, 0, 1) * (0.75 + 0.25 * n2)
put(5, np.dstack([0.93 + 0.03 * n2, 0.91 + 0.03 * n2, 0.86 + 0.03 * n2]), pp * 0.8)
# 6 removed-fixture ghost: cleaner rectangle + 4 screw holes (dark)
gh = np.clip((0.40 - np.maximum(abs(xx - 0.5) * 1.3, abs(yy - 0.5))) * 30, 0, 1) * 0.35
holes = np.zeros((256, 256))
for (hx, hy) in ((0.30, 0.22), (0.70, 0.22), (0.30, 0.78), (0.70, 0.78)):
    holes = np.maximum(holes, np.clip(1 - np.hypot(xx - hx, yy - hy) / 0.018, 0, 1))
rgb6 = np.dstack([0.95 - 0.85 * holes, 0.93 - 0.85 * holes, 0.88 - 0.8 * holes])
put(6, rgb6, np.maximum(gh, holes))
# 7 grey duct-tape repair "X"
tp = Image.new("L", (256, 256), 0); d = ImageDraw.Draw(tp)
d.line((48, 64, 208, 192), fill=255, width=34); d.line((52, 196, 204, 60), fill=255, width=34)
tpa = blur(np.asarray(tp, dtype=np.float64) / 255.0, 0.8)
put(7, np.dstack([0.56 + 0.06 * n2, 0.57 + 0.06 * n2, 0.58 + 0.06 * n2]), tpa * (0.92 + 0.08 * n2))
save("lp4_decal_wear", Image.fromarray((np.clip(W8, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA"), "DXT5",
     ops="ORIGINAL wear decals: wall-base grime, floor traffic, drips, heel scuffs, ceiling water stain, plaster patch, removed-fixture ghost, tape repair")

(OUT / "lp4_textures_report.json").write_text(json.dumps(REPORT, indent=1), encoding="utf-8")
print("GS15G_DONE", len(REPORT["textures"]))
