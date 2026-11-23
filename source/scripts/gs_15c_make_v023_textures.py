# LONG PIG — v0.2.3 "90s lobby" textures (no wood): GTA-ready DDS from two approved CC0 ambientCG sets
# (Tiles010, PaintedBricks004 — downloaded 2026-11-01, assets/cc0/_downloads/fetch_manifest_v023.json) plus ORIGINAL
# procedural / typographic textures (laminates, red vinyl recolour of our own leather, acoustic tile, troffer lens,
# backlit menu boards, entry mat, rubber base, grime decals). Nothing here comes from Rockstar files or third-party MLOs.
#   python gs_15c_make_v023_textures.py <cc0_downloads_dir> [<out_dir>]
# Fonts: DejaVu Sans (Bitstream Vera licence — free to embed in images).
import sys, io, json, hashlib, math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import gs_dds  # noqa: E402

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / "textures" / "v023"
V021 = HERE.parent / "textures" / "v021"
SLICE = HERE.parent / "textures" / "slice"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20261101)
REPORT = {"script": "source/scripts/gs_15c_make_v023_textures.py", "version": "0.2.3", "textures": []}


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def load(name):
    return Image.open(io.BytesIO((SRC / name).read_bytes())), name


def load_zip(zname, member):
    import zipfile
    with zipfile.ZipFile(SRC / zname) as z:
        return Image.open(io.BytesIO(z.read(member))), f"{zname}:{member}"


def load_png(path):
    return Image.open(path), str(path.relative_to(HERE.parent.parent)).replace("\\", "/")


def rgb(img):
    return np.asarray(img.convert("RGB"), dtype=np.float64) / 255.0


def grey(img):
    return np.asarray(img.convert("L"), dtype=np.float64) / 255.0


def hexcol(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def to_img(a):
    if a.ndim == 2:
        a = np.dstack([a, a, a])
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")


def resize(a, w, h=None):
    h = h or w
    img = to_img(a)
    if img.size != (w, h):
        img = img.resize((w, h), Image.Resampling.LANCZOS)
    return np.asarray(img, dtype=np.float64) / 255.0


def save(name, a, w, h=None, fmt="DXT1", role="diffuse", derived=(), ops=""):
    a = resize(a, w, h)
    png = OUT / f"{name}.png"
    to_img(a).save(png)
    gs_dds.convert(png, OUT / f"{name}.dds", fmt)
    data = (OUT / f"{name}.dds").read_bytes()
    REPORT["textures"].append({"name": name, "file": f"{name}.dds", "size": [w, h or w], "format": fmt, "role": role,
                               "bytes": len(data), "sha256": sha256(data), "derived_from": list(derived),
                               "origin": "derived_cc0" if derived else "original_procedural", "operations": ops})
    print("TEX", name, w, h or w, fmt, len(data))


# ------------------------------------------------------------------ procedural helpers (all tileable)
def fbm(n, octaves=5, base=4, persist=0.55, seed=0):
    """Tileable value-noise fBm on an n x n grid in [0, 1]."""
    rng = np.random.default_rng(seed)
    acc = np.zeros((n, n)); amp = 1.0; tot = 0.0
    for o in range(octaves):
        g = base * 2 ** o
        if g > n:
            break
        lat = rng.random((g, g))
        img = Image.fromarray((lat * 255).astype(np.uint8), "L")
        # tile 3x3 then crop -> seamless bicubic upsample
        big = Image.new("L", (g * 3, g * 3))
        for i in range(3):
            for j in range(3):
                big.paste(img, (i * g, j * g))
        up = np.asarray(big.resize((n * 3, n * 3), Image.Resampling.BICUBIC), dtype=np.float64)[n:2 * n, n:2 * n] / 255.0
        acc += amp * up; tot += amp; amp *= persist
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min() + 1e-9)


def blur(a, r):
    return np.asarray(to_img(a).filter(ImageFilter.GaussianBlur(r)), dtype=np.float64)[..., 0] / 255.0 if a.ndim == 2 else \
        np.asarray(to_img(a).filter(ImageFilter.GaussianBlur(r)), dtype=np.float64) / 255.0


def wrap_blur(a, r):
    """Gaussian blur with wrap-around (keeps tiling)."""
    n = a.shape[0]
    big = np.tile(a, (3, 3) if a.ndim == 2 else (3, 3, 1))
    b = blur(big, r)
    return b[n:2 * n, n:2 * n]


def spots(n, count, rmin, rmax, seed, ecc=1.0, wrap=True):
    """Soft round/elliptic spots mask (tileable)."""
    rng = np.random.default_rng(seed)
    m = np.zeros((n, n))
    yy, xx = np.mgrid[0:n, 0:n]
    for _ in range(count):
        cx, cy = rng.random() * n, rng.random() * n
        r = rmin + (rmax - rmin) * rng.random() ** 2
        a = rng.random() * math.pi
        for ox in ((-n, 0, n) if wrap else (0,)):
            for oy in ((-n, 0, n) if wrap else (0,)):
                dx, dy = xx - (cx + ox), yy - (cy + oy)
                u = dx * math.cos(a) + dy * math.sin(a)
                v = (-dx * math.sin(a) + dy * math.cos(a)) * ecc
                d = np.sqrt(u * u + v * v) / r
                m = np.maximum(m, np.clip(1.3 - d * 1.3, 0, 1) ** 0.8)
    return m


def height_to_normal(h, strength):
    """DirectX normal map (green = -dy) from a tileable height field."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    nx, ny, nz = -dx, dy, np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.dstack([nx / l * 0.5 + 0.5, ny / l * 0.5 + 0.5, nz / l * 0.5 + 0.5])


def mix(a, b, t):
    t = t[..., None] if (t.ndim == 2 and a.ndim == 3) else t
    return a * (1 - t) + b * t


def lerp_col(c0, c1, t):
    return hexcol(c0)[None, None, :] * (1 - t[..., None]) + hexcol(c1)[None, None, :] * t[..., None]


def tint(col, target_hex, detail=1.2, keep_hue=0.25):
    lum = col.mean(axis=2, keepdims=True)
    m = lum.mean()
    det = (lum - m) * detail
    tgt = hexcol(target_hex)[None, None, :]
    base = tgt * (1 + det / max(m, 1e-3))
    hue = col / np.maximum(lum, 1e-3) * tgt
    return np.clip(base * (1 - keep_hue) + hue * keep_hue * (1 + det / max(m, 1e-3)), 0, 1)


def renorm(n_rgb, flatten=1.0):
    v = n_rgb * 2 - 1
    v[..., 0] *= flatten; v[..., 1] *= flatten
    v /= np.linalg.norm(v, axis=2, keepdims=True) + 1e-9
    return v * 0.5 + 0.5


def spec_from_rough(r, gain, floor):
    return np.clip(floor + gain * (1 - r) ** 1.5, 0, 1)




from PIL import ImageDraw, ImageFont
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu") if Path("/usr/share/fonts/truetype/dejavu").is_dir() else HERE.parent / "tools" / "fonts"


def font(bold=True, cond=False, size=40):
    nm = "DejaVuSans" + ("Condensed" if cond else "") + ("-Bold" if bold else "") + ".ttf"
    return ImageFont.truetype(str(FONT_DIR / nm), size)


def save_rgba(name, img, fmt="DXT5", role="diffuse", ops=""):
    png = OUT / f"{name}.png"
    img.save(png)
    gs_dds.convert(png, OUT / f"{name}.dds", fmt)
    data = (OUT / f"{name}.dds").read_bytes()
    REPORT["textures"].append({"name": name, "file": f"{name}.dds", "size": list(img.size), "format": fmt, "role": role,
                               "bytes": len(data), "sha256": sha256(data), "derived_from": [],
                               "origin": "original_procedural", "operations": ops})
    print("TEX", name, img.size, fmt, len(data))


# ================================================================== 1. glazed wall tile (Tiles010): oxblood red + white
col, c_src = load_zip("Tiles010_1K-JPG.zip", "Tiles010_1K-JPG_Color.jpg")
nrm, n_src = load_zip("Tiles010_1K-JPG.zip", "Tiles010_1K-JPG_NormalDX.jpg")
rgh, r_src = load_zip("Tiles010_1K-JPG.zip", "Tiles010_1K-JPG_Roughness.jpg")
dsp, d_src = load_zip("Tiles010_1K-JPG.zip", "Tiles010_1K-JPG_Displacement.jpg")
c = rgb(col)
h = grey(dsp)
grout = np.clip((0.42 - h) * 6.0, 0, 1)                    # 1 in the joints
grout = np.maximum(grout, np.clip((0.62 - c.mean(2)) * 5.0, 0, 1) * (h < 0.5))
vein = np.clip((c.mean(2).mean() - c.mean(2)) * 4.0, 0, 1) * (1 - grout)
glaze_var = fbm(1024, 5, 3, 0.6, 51)
red = lerp_col("#7A1C1A", "#94251F", glaze_var) * (1 - 0.35 * vein[..., None])
red = mix(red, lerp_col("#C9C2B4", "#A9A295", glaze_var), grout)
save("lp3_tile_red", red, 1024, derived=[c_src, d_src], ops="recolour glaze oxblood #7A1C1A-#94251F, joints light grey (from displacement)")
white = lerp_col("#EEEAE0", "#E3DDCF", glaze_var) * (1 - 0.18 * vein[..., None])
white = mix(white, lerp_col("#8D877C", "#77716A", glaze_var), grout)
save("lp3_tile_white", white, 1024, derived=[c_src, d_src], ops="warm white glaze, darker joints (behind the counter)")
save("lp3_tile_n", renorm(rgb(nrm), 1.0), 1024, role="normal", derived=[n_src], ops="as is")
save("lp3_tile_s", np.clip(0.85 - grout * 0.75 - grey(rgh) * 0.15, 0, 1), 512, role="spec", derived=[r_src, d_src], ops="glossy glaze, matte joints")

# ================================================================== 2. painted brick (PaintedBricks004) — 2 m texture, warm cream paint
col, c_src = load_zip("PaintedBricks004_1K-JPG.zip", "PaintedBricks004_1K-JPG_Color.jpg")
ao, a_src = load_zip("PaintedBricks004_1K-JPG.zip", "PaintedBricks004_1K-JPG_AmbientOcclusion.jpg")
nrm, n_src = load_zip("PaintedBricks004_1K-JPG.zip", "PaintedBricks004_1K-JPG_NormalDX.jpg")
rgh, r_src = load_zip("PaintedBricks004_1K-JPG.zip", "PaintedBricks004_1K-JPG_Roughness.jpg")
a = grey(ao)
a = np.clip((a - np.percentile(a, 2)) / (np.percentile(a, 60) - np.percentile(a, 2) + 1e-6), 0, 1)
paint = lerp_col("#E6D9BD", "#DED0B2", fbm(1024, 5, 3, 0.6, 61)) * (0.72 + 0.28 * np.clip(a[..., None] * 1.3, 0, 1) ** 2.0)
dirt = np.clip((fbm(1024, 6, 2, 0.6, 62) - 0.6) * 2.0, 0, 1)
paint = mix(paint, paint * np.array([0.9, 0.87, 0.8]), dirt * 0.3)
tile2 = lambda x: np.tile(x, (2, 2, 1) if x.ndim == 3 else (2, 2))        # shell walls map 2.0 m per texture
save("lp3_paintbrick", tile2(paint), 2048, derived=[c_src, a_src], ops="cream paint from AO, original grime fBm, 2x2 repeat (2 m)")
save("lp3_paintbrick_n", tile2(renorm(rgb(nrm), 1.2)), 1024, role="normal", derived=[n_src], ops="2x2 repeat, bump x1.2")
save("lp3_paintbrick_s", tile2(spec_from_rough(grey(rgh), 0.35, 0.05)), 512, role="spec", derived=[r_src], ops="eggshell paint")

# ================================================================== 3. ORIGINAL: laminates (maroon trim laminate, cream speckle tabletop)
n = 1024
rng = np.random.default_rng(71)
def speckle(base0, base1, flecks, seed, density=0.012):
    r = np.random.default_rng(seed)
    t = lerp_col(base0, base1, fbm(n, 5, 4, 0.55, seed))
    for hexc, k in flecks:
        m = r.random((n, n)) < density * k
        m = wrap_blur(m.astype(float), 0.7) > 0.12
        t[m] = hexcol(hexc) * (0.85 + 0.3 * r.random((m.sum(), 1)))
    return t
lam_red = speckle("#5E1716", "#6B1C1A", [("#3A0E0D", 1.0), ("#8E3A33", 0.5)], 72, 0.010)
save("lp3_laminate_red", lam_red, 1024, ops="original maroon laminate with fine flecks")
lam_cream = speckle("#E6DDCA", "#DDD2BC", [("#7C2A26", 0.9), ("#3C5C5A", 0.7), ("#8A8478", 1.2)], 73, 0.009)
# 90s boomerang hint: faint pale arcs
yy, xx = np.mgrid[0:n, 0:n]
arcs = np.zeros((n, n))
for k in range(26):
    cx, cy, rr = rng.random() * n, rng.random() * n, 30 + rng.random() * 50
    for ox in (-n, 0, n):
        for oy in (-n, 0, n):
            d = np.abs(np.sqrt((xx - cx - ox) ** 2 + (yy - cy - oy) ** 2) - rr)
            arcs = np.maximum(arcs, np.clip(1.5 - d, 0, 1) * ((xx - cx - ox) * 0.7 + (yy - cy - oy) > 0))
lam_cream = mix(lam_cream, lam_cream * np.array([0.93, 0.92, 0.9]), arcs * 0.6)
save("lp3_laminate_cream", lam_cream, 1024, ops="original cream speckle laminate with faint boomerang arcs")
save("lp3_laminate_n", height_to_normal(fbm(512, 5, 8, 0.5, 74) * 0.15, 1.0), 512, role="normal", ops="almost flat")
save("lp3_laminate_s", np.full((256, 256), 0.62) - fbm(256, 4, 4, 0.5, 75) * 0.1, 256, role="spec", ops="semi-gloss laminate")

# ================================================================== 4. red vinyl (recolour of our own lp2_leather)
lea, l_src = load_png(V021 / "lp2_leather.png")
lea = rgb(lea)
vin = tint(lea, "#8C1A1C", detail=1.1, keep_hue=0.05)
save("lp3_vinyl_red", vin, 1024, derived=[l_src], ops="recolour of lp2_leather (own CC0-derived) to diner red #A11D1F")
ls, ls_src = load_png(V021 / "lp2_leather_s.png")
save("lp3_vinyl_s", np.clip(grey(ls) * 1.35 + 0.08, 0, 1), 512, role="spec", derived=[ls_src], ops="glossier vinyl")

# ================================================================== 5. ORIGINAL: mineral-fibre ceiling tile, 8 x 8 tiles per texture (5.15 m)
n = 2048
cell = n // 8
fiss = fbm(n, 7, 32, 0.62, 81)
worm = np.abs(fbm(n, 6, 24, 0.55, 82) - 0.5) < 0.02
pin = np.random.default_rng(83).random((n, n)) < 0.012
tile = 0.82 + 0.06 * fiss - 0.05 * worm - 0.30 * wrap_blur(pin.astype(float), 0.6)
tint_t = np.ones((n, n))
r8 = np.random.default_rng(84)
for i in range(8):
    for j in range(8):
        tint_t[i * cell:(i + 1) * cell, j * cell:(j + 1) * cell] = 0.96 + 0.06 * r8.random()
yy, xx = np.mgrid[0:n, 0:n]
edge = np.minimum(np.minimum(xx % cell, cell - 1 - xx % cell), np.minimum(yy % cell, cell - 1 - yy % cell))
bevel = np.clip(edge / 6.0, 0, 1)
stain = np.zeros((n, n))
for (cx, cy, rr) in ((int(cell * 2.5), int(cell * 5.4), 70), (int(cell * 6.3), int(cell * 1.6), 50)):
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rr
    stain = np.maximum(stain, np.clip(1 - d, 0, 1) ** 0.5 * (0.6 + 0.4 * fiss))
ceil = np.dstack([tile * tint_t] * 3) * hexcol("#EFE8D8")[None, None, :]
ceil = ceil * (0.82 + 0.18 * bevel[..., None])
ring = np.clip(1 - np.abs(stain - 0.25) * 8, 0, 1)
ceil = mix(ceil, ceil * np.array([0.86, 0.78, 0.62]), np.clip(stain * 0.6 + ring * 0.5, 0, 1))
save("lp3_ceiling_tile", ceil, 2048, ops="original fissured mineral-fibre tiles, 8x8 per texture, bevelled edges, 2 water stains")
save("lp3_ceiling_tile_n", height_to_normal(wrap_blur(tile, 0.8) * 0.5 + bevel * 0.6, 4.0), 1024, role="normal", ops="fissures + tile bevel")

# ================================================================== 6. ORIGINAL: troffer prismatic lens (emissive) + rubber base + entry mat
n = 256
yy, xx = np.mgrid[0:n, 0:n]
prism_ = 0.92 + 0.08 * (np.abs(((xx % 16) - 8)) + np.abs(((yy % 16) - 8))) / 16.0
lens = np.dstack([prism_] * 3) * hexcol("#FFF6E6")[None, None, :]
save("lp3_troffer", lens, 256, ops="original prismatic lens pattern (emissive diffuser)")
rub = lerp_col("#121212", "#1E1D1C", fbm(256, 5, 6, 0.6, 91))
save("lp3_rubber", rub, 256, ops="black rubber cove base / mat")
mat = Image.new("RGB", (1024, 512), (24, 24, 26))
dm = ImageDraw.Draw(mat)
for y in range(40, 472, 14):
    dm.rectangle([40, y, 984, y + 6], fill=(36, 36, 38))
dm.rectangle([0, 0, 1023, 511], outline=(14, 14, 14), width=22)
f = font(True, False, 96)
txt = "LONG PIG"
w = dm.textlength(txt, font=f)
dm.rectangle([512 - w / 2 - 30, 196, 512 + w / 2 + 30, 316], fill=(26, 26, 28))
dm.text((512 - w / 2, 200), txt, font=f, fill=(150, 34, 30))
save("lp3_mat", rgb(mat), 1024, 512, ops="original ribbed entry mat with own LONG PIG lettering (DejaVu Sans Bold)")

# ================================================================== 7. ORIGINAL: backlit menu boards (2048 x 1024 atlas: A top, B bottom)
W, H = 2048, 1024
menu = Image.new("RGB", (W, H), (247, 241, 226))
d = ImageDraw.Draw(menu)
RED, INK, YEL = (158, 30, 28), (30, 26, 24), (226, 178, 46)
def board(y0, title, cols):
    d.rectangle([0, y0, W - 1, y0 + 511], fill=(247, 241, 226))
    d.rectangle([0, y0, W - 1, y0 + 118], fill=RED)
    d.rectangle([0, y0 + 118, W - 1, y0 + 130], fill=YEL)
    ft = font(True, False, 84)
    tw = d.textlength(title, font=ft)
    d.text(((W - tw) / 2, y0 + 14), title, font=ft, fill=(250, 244, 230))
    cw = W / len(cols)
    for k, (head, items) in enumerate(cols):
        x0 = k * cw + 34
        d.text((x0, y0 + 150), head, font=font(True, True, 50), fill=RED)
        d.line([x0, y0 + 210, x0 + cw - 68, y0 + 210], fill=INK, width=3)
        for i, (it, pr) in enumerate(items):
            yy_ = y0 + 228 + i * 54
            d.text((x0, yy_), it, font=font(False, True, 38), fill=INK)
            pw = d.textlength(pr, font=font(True, True, 38))
            d.text((x0 + cw - 68 - pw, yy_), pr, font=font(True, True, 38), fill=INK)
        if k:
            d.line([k * cw, y0 + 150, k * cw, y0 + 490], fill=(200, 190, 170), width=3)
    d.rectangle([0, y0, W - 1, y0 + 511], outline=(60, 60, 62), width=10)
board(0, "LONG PIG  ·  DELI COUNTER", [
    ("SALUMI", [("Genoa Salami", "4.99"), ("Prosciutto", "8.49"), ("Mortadella", "4.29"), ("Capicola", "5.99"), ("Soppressata", "6.49")]),
    ("CHEESE", [("Provolone", "4.59"), ("Fresh Mozz", "5.29"), ("Parmigiano", "7.99"), ("Ricotta", "3.49"), ("Pecorino", "6.99")]),
    ("HEROES", [("Italian Combo", "6.95"), ("Meatball Parm", "6.50"), ("Chicken Cutlet", "6.75"), ("Eggplant Parm", "5.95"), ("Sausage & Pep.", "6.25")])])
board(512, "HOT FOOD  ·  ALL DAY", [
    ("BREAKFAST", [("Egg & Cheese", "2.25"), ("Bacon Egg Roll", "2.95"), ("Pancakes", "3.50"), ("Coffee", "0.75"), ("OJ", "1.25")]),
    ("TACOS", [("Carne Asada", "1.75"), ("Al Pastor", "1.75"), ("Pollo", "1.50"), ("Burrito", "4.25"), ("Nachos", "3.25")]),
    ("BURGERS", [("Hamburger", "2.75"), ("Cheeseburger", "2.99"), ("Double Pig", "4.50"), ("Fries", "1.25"), ("Onion Rings", "1.75")]),
    ("DRINKS", [("Soda", "0.99"), ("Iced Tea", "0.99"), ("Espresso", "1.25"), ("Beer & Wine", "ask"), ("Ice", "1.50")])])
save("lp3_menu", rgb(menu), 2048, 1024, ops="original typographic backlit menu boards (fictional items/prices), DejaVu fonts")

# ================================================================== 8. ORIGINAL: grime decals (DXT5 atlas 512: top = wall-base strip, bottom-left = floor wear, bottom-right = drips)
n = 512
img = np.zeros((n, n, 4))
g = fbm(n, 6, 6, 0.6, 101)
yy, xx = np.mgrid[0:n, 0:n]
strip = (yy < n // 2)
fall = np.clip(1 - yy / (n / 2), 0, 1) ** 2.2
img[..., :3] = lerp_col("#2B2118", "#3C2F22", g)
alpha = np.zeros((n, n))
alpha[strip] = (fall * (0.55 + 0.45 * g))[strip] * 0.85
bl = (yy >= n // 2) & (xx < n // 2)
cx, cy = n * 0.25, n * 0.75
rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (n * 0.24)
alpha[bl] = (np.clip(1 - rr, 0, 1) ** 1.4 * (0.4 + 0.6 * g))[bl] * 0.55
br = (yy >= n // 2) & (xx >= n // 2)
drip = np.zeros((n, n))
r2 = np.random.default_rng(102)
for k in range(9):
    x = int(n * 0.55 + r2.random() * n * 0.4)
    L = int(40 + r2.random() * 160)
    w = 2 + r2.random() * 4
    for yv in range(n // 2 + 6, min(n - 2, n // 2 + 6 + L)):
        drip[yv, max(0, int(x - w)):int(x + w)] = max(0.0, 1 - (yv - n // 2) / (L + 10))
alpha[br] = (wrap_blur(drip, 1.2) * 0.7)[br]
img[..., 3] = np.clip(alpha, 0, 1)
save_rgba("lp3_decal_grime", Image.fromarray((img * 255).astype(np.uint8), "RGBA"), "DXT5", ops="original grime: wall-base strip, floor wear blotch, drips")

(OUT / "lp3_textures_report.json").write_text(json.dumps(REPORT, indent=1), encoding="utf-8")
print("GS15C_DONE", len(REPORT["textures"]))

# ================================================================== 9. black & white checker floor (recolour of our lp_floor_checker = CC0 Tiles139)
fl, f_src = load_png(SLICE / "lp_floor_checker.png")
f = rgb(fl)
lum = f.mean(2)
thr = np.percentile(lum, 50)
dark = np.clip((thr - lum) * 12.0 + 0.5, 0, 1)
dark = wrap_blur(dark, 0.6)
wear = fbm(f.shape[0], 5, 4, 0.6, 111)
bw = mix(lerp_col("#EAE6DC", "#DCD6C8", wear), lerp_col("#141414", "#232120", wear), dark)
bw = bw * (0.9 + 0.1 * (lum / (lum.mean() + 1e-6))[..., None].clip(0.6, 1.4))
save("lp3_floor_bw", bw, 1024, derived=[f_src], ops="recolour of lp_floor_checker (CC0 Tiles139) to black / white vinyl checker")
(OUT / "lp3_textures_report.json").write_text(json.dumps(REPORT, indent=1), encoding="utf-8")
print("GS15C_FLOOR_DONE", len(REPORT["textures"]))
