# LONG PIG — v0.2.6 finish-and-refine textures (brief: LONG_PIG_V026_MASTER_STYLE_LIGHTING_PRODUCTION_BRIEF, owner 2026-11-01).
# PRESERVE FIRST: every map here is either DERIVED from our own v0.2.x textures (CC0 derivatives / original work, see
# assets/registry.json) or ORIGINAL procedural / typographic work. No third-party pixels, no Rockstar textures, nothing
# from the reference MLO. Photos in the wall atlas are renders of OUR OWN interior (Blender, no vanilla props).
#   python gs_15i_make_v026_textures.py [<project_root>]      -> source/textures/v026/*.dds + lp5_textures_report.json
import sys, json, hashlib, math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from scipy import ndimage as ndi

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds  # noqa: E402

T = ROOT / "source" / "textures"
V025, V023, V021, SLICE = T / "v025", T / "v023", T / "v021", T / "slice"
OUT = T / "v026"
OUT.mkdir(parents=True, exist_ok=True)
PHOTO_SRC = OUT / "photo_src"                         # renders of our own hall (gs_21 GS_NO_VANILLA=1), optional
FONT = Path("/usr/share/fonts/truetype/dejavu")
REPORT = {"script": "source/scripts/gs_15i_make_v026_textures.py", "version": "0.2.6", "textures": []}
SEED = 20261101 + 26


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


def load(p):
    p = Path(p)
    return Image.open(p if p.is_file() else p.with_suffix(".dds"))


def save(name, img, fmt="DXT1", role="diffuse", derived=(), ops="", png_only=False):
    png = OUT / f"{name}.png"
    img.save(png)
    rec = {"name": name, "size": list(img.size), "format": fmt, "role": role, "derived_from": [rel(d) for d in derived],
           "origin": "derived_own" if derived else "original_procedural", "operations": ops}
    if png_only:
        data = png.read_bytes()
        rec.update(file=f"{name}.png", format="PNG (runtime texture)")
    else:
        gs_dds.convert(png, OUT / f"{name}.dds", fmt)
        data = (OUT / f"{name}.dds").read_bytes()
        rec["file"] = f"{name}.dds"
    rec.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    REPORT["textures"].append(rec)
    print("TEX", name, img.size, rec["format"], len(data))


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


def col(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def blur(a, r):
    if a.ndim == 2:
        return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(r)), dtype=np.float64) / 255.0
    return arr(to_img(a).filter(ImageFilter.GaussianBlur(r)))


def grid_values(n, size, seed, k=4):
    """Per-tile random values for a regular n x n tile grid on a size x size texture -> (size, size, k)."""
    v = np.random.default_rng(seed).random((n, n, k))
    idx = np.minimum((np.arange(size) * n) // size, n - 1)
    return v[idx][:, idx]


def normal_from_height(h, strength):
    gy, gx = np.gradient(h)
    nx, ny = -gx * strength, gy * strength
    nz = np.ones_like(h)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.dstack([nx / L * 0.5 + 0.5, ny / L * 0.5 + 0.5, nz / L * 0.5 + 0.5])


# ======================================================================== 1. FLOOR A (default) — same checker, aged further
# 4 m repeat (12 x 12 tiles of 33 cm) instead of 2 m: the tile-to-tile pattern no longer repeats every six tiles.
src = V025 / "lp4_floor_bw.png"
a = np.tile(arr(load(src)), (2, 2, 1))                                     # 2048 x 2048
v3 = np.tile(np.asarray(load(V023 / "lp3_floor_bw.png").convert("HSV"), dtype=np.float64)[..., 2] / 255.0, (2, 2))
N = a.shape[0]
blk, wht = v3 < 0.35, v3 > 0.65
grout = ~(blk | wht)
tv = grid_values(12, N, SEED + 1, 4)
dark, light = col("#383430"), col("#c9c2b1")                               # lifted charcoal, greyed off-white
lum = a.mean(2, keepdims=True)
t = np.clip((lum - 0.16) / 0.66, 0, 1)
base = a * 0.45 + (dark * (1 - t) + light * t) * 0.55                      # pull both ends toward the muted pair
base = base * (1 + np.where(blk, (tv[..., 0] - 0.5) * 0.16, (tv[..., 0] - 0.5) * 0.09)[..., None])
repl_w = wht & (tv[..., 1] > 0.965)                                        # newer replacement whites: cooler, cleaner
repl_b = blk & (tv[..., 1] < 0.02)                                         # one browner black (different batch)
base = np.where(repl_w[..., None], base * col("#d9d6cc") / col("#c9c2b1"), base)
base = np.where(repl_b[..., None], base * col("#433830") / col("#383430"), base)
# edge wear on the light tiles (dirt collects at the edge, the middle is mopped)
dist = ndi.distance_transform_edt(wht)
edge = np.exp(-dist / 7.0) * wht
base = base * (1 - 0.10 * edge[..., None])
# dirty grout, darker and browner
gn = tnoise(N, N, 16, 16, SEED + 2)
base = np.where(grout[..., None], col("#4a443c") * (0.78 + 0.35 * gn)[..., None], base)
# low-frequency grime + micro scratches on the black tiles
gr = tnoise(N, N, 3, 3, SEED + 3)
base = base * (0.90 + 0.12 * gr[..., None]) - 0.02 * (gr[..., None] - 0.5)
im = Image.new("L", (N, N), 0); d = ImageDraw.Draw(im); r = np.random.default_rng(SEED + 4)
for k in range(420):
    x, y = r.uniform(0, N), r.uniform(0, N); ang = r.uniform(0, math.pi); L = r.uniform(8, 60)
    d.line((x, y, x + L * math.cos(ang), y + L * math.sin(ang)), fill=int(r.uniform(40, 120)), width=1)
scr = np.asarray(im, dtype=np.float64)[..., None] / 255.0 * blk[..., None]
base = base + 0.10 * scr
save("lp5_floor_bw", to_img(base), derived=[src, V023 / "lp3_floor_bw.png"],
     ops="4 m repeat (2x2 of lp4), desaturated + lowered contrast, 12x12 per-tile variation, replacement tiles, edge dirt on light tiles, dirty grout, grime, scratches")
nsrc = SLICE / "lp_floor_checker_n.png"
save("lp5_floor_n", Image.fromarray(np.tile(np.asarray(load(nsrc).convert("RGB")), (2, 2, 1))).resize((1024, 1024), Image.Resampling.LANCZOS),
     role="normal", derived=[nsrc], ops="tiled 2x2 for the 4 m repeat, resized to 1024")
ssrc = V025 / "lp4_floor_s.png"
sp = np.tile(arr(load(ssrc)), (2, 2, 1))
sp = sp * (0.85 + 0.3 * grid_values(12, sp.shape[0], SEED + 1, 1)[..., 0:1])          # uneven sheen per tile
save("lp5_floor_s", to_img(sp).resize((512, 512), Image.Resampling.LANCZOS), role="spec", derived=[ssrc],
     ops="tiled 2x2 for the 4 m repeat, per-tile sheen variation, 512")

# ======================================================================== 2. FLOOR B (OPTIONAL comparison only, runtime swap)
# small gray-beige commercial quarry tile, 24 x 24 tiles per 4 m (16.7 cm), aged grout. ORIGINAL procedural.
NB = 1024; nt = 24; pitch = NB / nt; gw = 3.0
yy, xx = np.mgrid[0:NB, 0:NB].astype(np.float64)
fx, fy = (xx % pitch), (yy % pitch)
dg = np.minimum(np.minimum(fx, pitch - fx), np.minimum(fy, pitch - fy))
groutB = dg < gw / 2
tvB = grid_values(nt, NB, SEED + 11, 4)
pal = np.array([col("#a1988a"), col("#998f81"), col("#a79e8f"), col("#928979")])
baseB = pal[(tvB[..., 0] * 4).astype(int).clip(0, 3)]
baseB = baseB * (1 + (tvB[..., 1:2] - 0.5) * 0.08)
repB = tvB[..., 2] > 0.97
baseB = np.where(repB[..., None], col("#b1a999"), baseB)
grain = tnoise(NB, NB, 64, 64, SEED + 12, octaves=2)
baseB = baseB * (0.94 + 0.10 * grain[..., None])
baseB = baseB * (1 - 0.10 * np.exp(-dg / 5.0)[..., None])
baseB = np.where(groutB[..., None], col("#5a5349") * (0.8 + 0.3 * tnoise(NB, NB, 16, 16, SEED + 13))[..., None], baseB)
baseB = baseB * (0.90 + 0.12 * tnoise(NB, NB, 3, 3, SEED + 14)[..., None])
save("lp5_floor_b", to_img(baseB), ops="ORIGINAL: 24x24 gray-beige quarry tiles per 4 m, tone mix, replacement tiles, dirty grout", png_only=True)
hB = np.clip(dg / 3.0, 0, 1) * 0.6 + 0.05 * grain
save("lp5_floor_b_n", to_img(normal_from_height(blur(hB, 0.8), 2.5)), role="normal", ops="ORIGINAL: normal from grout height",
     png_only=True)

# ======================================================================== 3. CEILING — same yellowed acoustic tile, NO baked replaced tile
# (replacement tiles / stains are placed one by one as decals, so nothing repeats every 5 m)
src = V023 / "lp3_ceiling_tile.png"
a = arr(load(src))
N = a.shape[0]
v_ = np.asarray(load(src).convert("HSV"), dtype=np.float64)[..., 2] / 255.0
tiles = v_ > 0.72
tvc = grid_values(8, N, SEED + 21, 2)
base = a * (col("#d6cfba") / a.reshape(-1, 3).mean(0))
base = base * (1 + (tvc[..., 0:1] - 0.5) * 0.07 * tiles[..., None])
base = base * (0.96 + 0.06 * tnoise(N, N, 4, 4, SEED + 22)[..., None])
save("lp5_ceiling_tile", to_img(base), derived=[src], ops="yellowed acoustic tile, per-tile tone, no baked replacement tile")

# ======================================================================== 4. TROFFER LENS — 4 variants (2 x 2 of 256 x 128)
TR = Image.new("RGB", (512, 256))
for vi, (rgb, gain, dead, bugs) in enumerate([((0.93, 0.97, 1.00), 0.95, False, False),     # 0 cool white
                                              ((1.00, 0.94, 0.83), 0.90, False, False),     # 1 aged warm tube, yellowed lens
                                              ((0.90, 0.95, 0.92), 0.55, True, False),      # 2 weak fixture, one tube dead
                                              ((0.93, 0.97, 1.00), 0.88, False, True)]):    # 3 cool, dirt + insects at one end
    h, w = 128, 256
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    bands = np.zeros((h, w))
    for k, yc in enumerate((0.25, 0.5, 0.75)):
        if dead and k == 1:
            continue
        bands += np.exp(-((y / h - yc) ** 2) / (2 * 0.075 ** 2))
    prism = 0.94 + 0.06 * (np.abs(np.sin(x * math.pi / 3.0)) * np.abs(np.sin(y * math.pi / 3.0)))
    vign = np.clip(np.minimum(np.minimum(x, w - 1 - x), np.minimum(y, h - 1 - y)) / 10.0, 0, 1) ** 0.6
    lum = (0.55 + 0.45 * np.clip(bands, 0, 1)) * prism * (0.80 + 0.20 * vign)
    img = np.dstack([lum * c for c in rgb]) * gain
    if bugs:
        dirt = np.clip(1 - x / (w * 0.35), 0, 1) * 0.22 * tnoise(h, w, 4, 8, SEED + 31)
        img = img * (1 - dirt[..., None])
        rr = np.random.default_rng(SEED + 32)
        for k in range(9):
            cx, cy = rr.uniform(6, 60), rr.uniform(10, h - 10)
            img[int(cy) - 1:int(cy) + 2, int(cx) - 2:int(cx) + 2] *= 0.45
    TR.paste(to_img(img), ((vi % 2) * 256, (vi // 2) * 128))
save("lp5_troffer", TR, ops="ORIGINAL prismatic lens, 3 tube bands, 4 variants: cool, aged warm, weak (tube out), dirty")

# ======================================================================== 5. VERTICAL BLIND SLATS — 4 columns of 64 x 512
BL = np.zeros((512, 256, 3))
for ci, (c0, desc) in enumerate([("#d6cfbc", "standard"), ("#d3c5a2", "sun-yellowed"), ("#d2cab6", "stained"), ("#e3dfd5", "replacement")]):
    h, w = 512, 64
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    c = col(c0)
    curve = 0.93 + 0.07 * np.sin(x / (w - 1) * math.pi)                      # slat curvature shading across the width
    emb = 0.985 + 0.03 * tnoise(h, w, 64, 8, SEED + 41 + ci, octaves=2)        # vertical emboss
    v = y / (h - 1)                                                           # 0 = top of the image = top of the slat
    grime = np.clip((v - 0.80) / 0.20, 0, 1) ** 1.5 * 0.16                   # hands at the bottom
    dust = np.clip((0.06 - v) / 0.06, 0, 1) * 0.08
    pocket = ((v > 0.965) & (v < 0.985)) * 0.10                               # weight pocket seam
    img = c * (curve * emb * (1 - grime - dust - pocket))[..., None]
    if ci == 2:
        st = np.exp(-(((x - 30) / 18) ** 2 + ((y - 300) / 70) ** 2))
        img = img * (1 - 0.18 * st[..., None]) + col("#a08a60") * 0.10 * st[..., None]
        img[200:203, :] *= 0.86                                               # bent crease
    BL[:, ci * 64:(ci + 1) * 64] = img
save("lp5_blind", to_img(BL), ops="ORIGINAL PVC vertical blind slats: standard / sun-yellowed / stained + crease / whiter replacement")

# ======================================================================== 6. WEAR / HISTORY DECALS (DXT5, 4 x 4 cells of 256)
DC = np.zeros((1024, 1024, 4))
rr = np.random.default_rng(SEED + 51)


def put(i, rgb, alpha):
    cx, cy = i % 4, i // 4
    DC[cy * 256:(cy + 1) * 256, cx * 256:(cx + 1) * 256, :3] = rgb
    DC[cy * 256:(cy + 1) * 256, cx * 256:(cx + 1) * 256, 3] = np.clip(alpha, 0, 1)


cy_, cx_ = np.mgrid[0:256, 0:256].astype(np.float64)
u, v = cx_ / 255.0, cy_ / 255.0
n1 = tnoise(256, 256, 8, 8, SEED + 52)
n2 = tnoise(256, 256, 16, 16, SEED + 53)
# 0 vent halo: soot around a square diffuser (centre 60 % is covered by the vent)
dsq = np.maximum(np.abs(u - 0.5), np.abs(v - 0.5))
ring = np.clip((dsq - 0.28) / 0.04, 0, 1) * np.clip((0.5 - dsq) / 0.20, 0, 1)
streak = 0.6 + 0.4 * tnoise(256, 256, 2, 24, SEED + 54)
put(0, np.dstack([u * 0 + 0.30, u * 0 + 0.28, u * 0 + 0.25]), ring * streak * 0.75)
# 1 replacement ceiling tile (opaque): whiter, fissured mineral fibre
fis = tnoise(256, 256, 32, 32, SEED + 55, octaves=3)
put(1, np.dstack([0.90 + 0.06 * fis, 0.885 + 0.06 * fis, 0.85 + 0.06 * fis]) * (0.97 + 0.04 * n1)[..., None], np.ones((256, 256)))
# 2 wall-top grime (top of the cell = the ceiling joint), streaky
put(2, np.dstack([u * 0 + 0.36, u * 0 + 0.33, u * 0 + 0.28]), (1 - v) ** 2.2 * (0.55 + 0.45 * tnoise(256, 256, 2, 32, SEED + 56)) * 0.65)
# 3 sticker residue: torn paper + adhesive rectangles
im = Image.new("RGBA", (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
for k in range(3):
    x0, y0 = rr.uniform(20, 140), rr.uniform(20, 160); w_, h_ = rr.uniform(50, 100), rr.uniform(30, 70)
    d.rectangle((x0, y0, x0 + w_, y0 + h_), fill=(120, 112, 98, 70))
    for j in range(6):
        px, py = x0 + rr.uniform(0, w_), y0 + rr.uniform(0, h_)
        d.polygon([(px, py), (px + rr.uniform(4, 14), py + rr.uniform(-3, 6)), (px + rr.uniform(0, 8), py + rr.uniform(5, 12))], fill=(236, 230, 214, 230))
    for (qx, qy) in ((x0, y0), (x0 + w_ - 14, y0), (x0, y0 + h_ - 10), (x0 + w_ - 14, y0 + h_ - 10)):
        d.rectangle((qx, qy, qx + 14, qy + 10), fill=(214, 200, 160, 150))           # yellowed tape corners
s3 = np.asarray(im, dtype=np.float64) / 255.0
put(3, s3[..., :3], s3[..., 3])
# 4 frame ghost: unfaded paint where a picture hung for years + dust line on top + nail hole
inside = (np.abs(u - 0.5) < 0.40) & (np.abs(v - 0.55) < 0.36)
gh = blur(inside.astype(float), 3)
dustl = np.exp(-((v - 0.19) / 0.012) ** 2) * (np.abs(u - 0.5) < 0.40)
nail = np.exp(-(((u - 0.5) / 0.012) ** 2 + ((v - 0.08) / 0.012) ** 2))
rgb4 = np.dstack([u * 0 + 0.95, u * 0 + 0.92, u * 0 + 0.84])
rgb4 = np.where((dustl + nail)[..., None] > 0.3, np.array([0.30, 0.27, 0.22]), rgb4)
put(4, rgb4, np.maximum(gh * 0.45, np.clip(dustl * 0.6 + nail, 0, 1)))
# 5 anchor holes + hairline cracks
im = Image.new("RGBA", (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
for (hx, hy) in ((70, 80), (180, 86), (124, 190)):
    d.ellipse((hx - 9, hy - 9, hx + 9, hy + 9), fill=(150, 142, 128, 200))
    d.ellipse((hx - 5, hy - 5, hx + 5, hy + 5), fill=(225, 222, 214, 255))
    d.ellipse((hx - 2, hy - 2, hx + 2, hy + 2), fill=(40, 36, 30, 255))
    x, y = hx, hy
    for j in range(5):
        nx_, ny_ = x + rr.normal(0, 7), y + rr.normal(6, 4); d.line((x, y, nx_, ny_), fill=(90, 84, 74, 150), width=1); x, y = nx_, ny_
s5 = np.asarray(im, dtype=np.float64) / 255.0
put(5, s5[..., :3], s5[..., 3])
# 6 hand rub (greasy smudge)
rub = np.exp(-(((u - 0.5) / 0.30) ** 2 + ((v - 0.5) / 0.22) ** 2)) * (0.6 + 0.4 * n1)
put(6, np.dstack([u * 0 + 0.28, u * 0 + 0.24, u * 0 + 0.20]), rub * 0.38)
# 7 vinyl edge wear: lighter, cracked worn band across the cell (horizontal)
bandv = np.exp(-((v - 0.5) / 0.16) ** 2) * (0.5 + 0.5 * tnoise(256, 256, 2, 8, SEED + 57))
cr = (tnoise(256, 256, 24, 24, SEED + 58, octaves=2) > 0.62) * bandv
put(7, np.dstack([u * 0 + 0.80, u * 0 + 0.62, u * 0 + 0.56]) * (1 - 0.35 * cr)[..., None], np.clip(bandv * 0.55 + cr * 0.3, 0, 1))
# 8 chipped tile edges: pale ceramic body showing
im = Image.new("RGBA", (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
for k in range(7):
    cx, cy = rr.uniform(20, 236), rr.uniform(20, 236); rad = rr.uniform(4, 11)
    pts = [(cx + rad * rr.uniform(0.6, 1.3) * math.cos(a_), cy + rad * rr.uniform(0.6, 1.3) * math.sin(a_)) for a_ in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
    d.polygon(pts, fill=(216, 206, 190, 255), outline=(110, 92, 80, 255))
s8 = np.asarray(im, dtype=np.float64) / 255.0
put(8, s8[..., :3], s8[..., 3])
# 9 paint patch: mismatched brushed cream patch with ragged edges
pm = (np.maximum(np.abs(u - 0.5) / 0.42, np.abs(v - 0.5) / 0.36) + 0.12 * (n2 - 0.5)) < 1.0
br = 0.96 + 0.05 * tnoise(256, 256, 4, 32, SEED + 59, octaves=2)
put(9, np.dstack([0.92 * br, 0.88 * br, 0.77 * br]), blur(pm.astype(float), 2.5) * (0.42 + 0.12 * n1))
# 10 mop marks (arcs)
im = Image.new("L", (256, 256), 0); d = ImageDraw.Draw(im)
for k in range(9):
    rad = rr.uniform(60, 140); cx, cy = rr.uniform(60, 200), rr.uniform(140, 260)
    d.arc((cx - rad, cy - rad, cx + rad, cy + rad), rr.uniform(200, 240), rr.uniform(290, 340), fill=int(rr.uniform(120, 220)), width=int(rr.uniform(6, 14)))
mm = blur(np.asarray(im, dtype=np.float64) / 255.0, 2)
put(10, np.dstack([u * 0 + 0.30, u * 0 + 0.28, u * 0 + 0.25]), mm * 0.20)
# 11 scuff band (horizontal rubs)
sb = np.exp(-((v - 0.5) / 0.18) ** 2) * (tnoise(256, 256, 4, 1, SEED + 60, octaves=3) > 0.45) * (0.6 + 0.4 * tnoise(256, 256, 32, 4, SEED + 61))
put(11, np.dstack([u * 0 + 0.35, u * 0 + 0.33, u * 0 + 0.31]), blur(sb, 1.0) * 0.45)
# 12 dark grease patch (floor behind the counter, by the bin)
gp = np.exp(-(((u - 0.5) / 0.36) ** 2 + ((v - 0.5) / 0.30) ** 2)) * (0.55 + 0.45 * n2)
put(12, np.dstack([u * 0 + 0.20, u * 0 + 0.17, u * 0 + 0.13]), gp * 0.40)
# 13 small ceiling stain ring
rd = np.hypot(u - 0.5, v - 0.5) / 0.42 + 0.15 * (n1 - 0.5)
st = np.clip(1 - rd, 0, 1) ** 0.5 * 0.25 + np.exp(-((rd - 0.92) / 0.05) ** 2) * 0.5
put(13, np.dstack([u * 0 + 0.55, u * 0 + 0.44, u * 0 + 0.28]), np.clip(st, 0, 0.7) * (rd < 1.05))
# 14 street grit at the entrance
gs = (tnoise(256, 256, 64, 64, SEED + 62, octaves=1) > 0.70) * (1 - np.clip(np.hypot(u - 0.5, v - 0.5) / 0.5, 0, 1))
put(14, np.dstack([u * 0 + 0.24, u * 0 + 0.22, u * 0 + 0.19]), blur(gs.astype(float), 0.6) * 0.75 + 0.18 * (1 - np.clip(np.hypot(u - 0.5, v - 0.5) / 0.5, 0, 1)))
# 15 cup rings
im = Image.new("L", (256, 256), 0); d = ImageDraw.Draw(im)
for (cx, cy, rad) in ((80, 90, 34), (98, 104, 33), (176, 170, 30)):
    d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=170, width=4)
put(15, np.dstack([u * 0 + 0.40, u * 0 + 0.30, u * 0 + 0.20]), blur(np.asarray(im, dtype=np.float64) / 255.0, 1.0) * 0.6)
save("lp5_decal", to_img(DC, "RGBA") if False else Image.fromarray((np.clip(DC, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA"), fmt="DXT5",
     ops="ORIGINAL decals: vent halo, replacement ceiling tile, wall-top grime, sticker residue, frame ghost, anchor holes, hand rub, "
         "vinyl edge wear, tile chips, paint patch, mop marks, scuff band, grease patch, small ceiling stain, street grit, cup rings")

# ======================================================================== 7. WALL STORY ATLAS (posters, photos, notices) 1024 x 1024
W = Image.new("RGB", (1024, 1024), (226, 220, 206))
D = ImageDraw.Draw(W)
r = np.random.default_rng(SEED + 71)
REG = {"supplier": (0, 0, 512, 768), "photo_counter": (512, 0, 768, 192), "photo_booths": (768, 0, 1024, 192),
       "photo_family": (512, 192, 704, 448), "plaque": (704, 192, 1024, 416), "hours": (512, 448, 704, 704),
       "catering": (704, 416, 1024, 704), "note": (0, 768, 256, 1024), "certificate": (256, 768, 576, 1024),
       "tin_sign": (576, 704, 1024, 1024)}


def ctext(box, y, txt, f, fill=(30, 30, 30)):
    w = D.textlength(txt, font=f)
    D.text(((box[0] + box[2]) / 2 - w / 2, box[1] + y), txt, fill=fill, font=f)


def hand(box, x, y, txt, size=19, fill=(28, 40, 90)):
    f = font("DejaVuSans-Oblique.ttf", size)
    for ch in txt:
        D.text((box[0] + x, box[1] + y + r.normal(0, 0.8)), ch, fill=fill, font=f)
        x += D.textlength(ch, font=f) * r.uniform(0.92, 1.04)


# supplier poster (fictional brand) — cream stock, red/olive two-colour print, sun-faded
b = REG["supplier"]
D.rectangle(b, fill=(232, 222, 196))
D.rectangle((b[0] + 14, b[1] + 14, b[2] - 15, b[3] - 15), outline=(150, 52, 40), width=5)
ctext(b, 44, "VESPUCCI FINE FOODS", font("DejaVuSerif-Bold.ttf", 33), (150, 52, 40))   # fictional (GTA place name), no real brand
ctext(b, 98, "IMPORTERS  ·  DISTRIBUTORS", font("DejaVuSans.ttf", 18), (70, 80, 50))
cx, cy = 256, 360
D.ellipse((cx - 190, cy - 52, cx + 110, cy + 52), fill=(146, 58, 52))                     # salami
for k in range(40):
    px, py = cx - 170 + r.uniform(0, 260), cy - 40 + r.uniform(0, 80)
    D.ellipse((px - 4, py - 3, px + 4, py + 3), fill=(226, 196, 180))
D.ellipse((cx + 70, cy - 52, cx + 150, cy + 52), fill=(196, 104, 92), outline=(120, 40, 36), width=3)
D.polygon([(cx - 120, cy + 150), (cx + 150, cy + 80), (cx + 150, cy + 170), (cx - 120, cy + 210)], fill=(226, 190, 96))  # cheese wedge
for (hx, hy, hr) in ((cx - 40, cy + 160, 12), (cx + 60, cy + 140, 9), (cx + 110, cy + 150, 7)):
    D.ellipse((hx - hr, hy - hr * 0.7, hx + hr, hy + hr * 0.7), fill=(190, 150, 70))
D.ellipse((cx - 200, cy - 170, cx + 20, cy - 90), fill=(196, 150, 92))                    # bread loaf
for k in range(4):
    D.arc((cx - 170 + k * 45, cy - 160, cx - 120 + k * 45, cy - 110), 200, 340, fill=(150, 104, 60), width=4)
ctext(b, 600, "PROVOLONE · GENOA · MORTADELLA", font("DejaVuSans-Bold.ttf", 18), (70, 80, 50))
ctext(b, 640, "SERVED HERE", font("DejaVuSerif-Bold.ttf", 34), (150, 52, 40))
ctext(b, 700, "Distributed in Los Santos since 1952", font("DejaVuSerif-Italic.ttf", 16), (90, 80, 70))
reg = np.asarray(W.crop(b), dtype=np.float64) / 255.0
hh, ww = reg.shape[:2]
fade = np.clip(np.mgrid[0:hh, 0:ww][1] / ww * 0.6 + (1 - np.mgrid[0:hh, 0:ww][0] / hh) * 0.4, 0, 1)[..., None]
reg = reg * (1 - 0.30 * fade) + np.array([0.93, 0.90, 0.80]) * 0.30 * fade                # sun-bleached towards the top-right
reg = reg * (0.95 + 0.06 * tnoise(hh, ww, 6, 4, SEED + 72)[..., None])
W.paste(to_img(reg), b[:2])


def photo(key, title):
    b = REG[key]
    w_, h_ = b[2] - b[0], b[3] - b[1]
    p = PHOTO_SRC / f"{key}.png"
    if p.is_file():
        im = ImageOps.fit(Image.open(p).convert("RGB"), (w_ - 16, h_ - 16), Image.Resampling.LANCZOS)
    else:                                                                                      # placeholder until rendered
        im = Image.new("RGB", (w_ - 16, h_ - 16), (150, 120, 100))
        ImageDraw.Draw(im).rectangle((0, (h_ - 16) * 0.6, w_, h_), fill=(90, 70, 60))
    a_ = arr(im)
    a_ = a_ * np.array([1.06, 0.98, 0.86]) + np.array([0.05, 0.03, 0.0])                     # warm 1980s print cast
    a_ = 0.10 + 0.80 * a_                                                                     # faded: lifted blacks, softer highlights
    a_ = a_ + 0.03 * (np.random.default_rng(SEED + len(key)).random(a_.shape[:2])[..., None] - 0.5)
    D.rectangle(b, fill=(238, 234, 222))                                                       # white print border
    W.paste(to_img(a_), (b[0] + 8, b[1] + 8))


photo("photo_counter", "counter")
photo("photo_booths", "booths")
photo("photo_family", "family")
# youth baseball sponsor plaque: dark laminate board, brass plate
b = REG["plaque"]
D.rectangle(b, fill=(78, 50, 36))
D.rectangle((b[0] + 18, b[1] + 18, b[2] - 19, b[3] - 19), fill=(178, 150, 86), outline=(120, 96, 50), width=3)
ctext(b, 36, "RANCHO YOUTH BASEBALL", font("DejaVuSerif-Bold.ttf", 17), (50, 36, 20))
ctext(b, 72, "PANTHERS  ·  1997 SEASON", font("DejaVuSans.ttf", 16), (50, 36, 20))
ctext(b, 112, "THANK YOU", font("DejaVuSerif-Bold.ttf", 30), (50, 36, 20))
ctext(b, 152, "LONG PIG DELI", font("DejaVuSerif-Bold.ttf", 24), (50, 36, 20))
ctext(b, 186, "for your support", font("DejaVuSerif-Italic.ttf", 15), (50, 36, 20))
# store hours card (printed, taped)
b = REG["hours"]
D.rectangle(b, fill=(240, 236, 224))
ctext(b, 18, "STORE HOURS", font("DejaVuSans-Bold.ttf", 22), (150, 40, 34))
for k, line in enumerate(("MON-FRI  6AM - 9PM", "SATURDAY  7AM - 9PM", "SUNDAY  7AM - 3PM")):
    ctext(b, 70 + k * 34, line, font("DejaVuSansMono.ttf", 15))
hand(b, 22, 186, "closed Thanksgiving", 15, (40, 40, 110))
hand(b, 40, 210, "- Sal", 15, (40, 40, 110))
# catering notice with a hand-corrected price
b = REG["catering"]
D.rectangle(b, fill=(244, 236, 206))
ctext(b, 16, "PARTY TRAYS & HEROS", font("DejaVuSans-Bold.ttf", 24), (40, 40, 40))
ctext(b, 56, "3 FT  ·  6 FT  ·  COLD CUT TRAYS", font("DejaVuSans.ttf", 16))
fb = font("DejaVuSans-Bold.ttf", 22)
D.text((b[0] + 30, b[1] + 92), "6 FT HERO", fill=(30, 30, 30), font=fb)
px = b[0] + 30 + D.textlength("6 FT HERO  ", font=fb)
D.text((px, b[1] + 92), "$39.95", fill=(30, 30, 30), font=fb)
D.line((px - 2, b[1] + 106, px + D.textlength("$39.95", font=fb) + 2, b[1] + 104), fill=(40, 40, 140), width=3)
hand(b, px - b[0] + 8, 118, "$49.95", 20, (40, 40, 140))
ctext(b, 150, "ORDER 24 HRS AHEAD", font("DejaVuSans.ttf", 18))
ctext(b, 184, "CALL 555-0179", font("DejaVuSans-Bold.ttf", 26), (150, 40, 34))
ctext(b, 232, "ask for Sal or Rosa", font("DejaVuSerif-Italic.ttf", 16))
# handwritten note
b = REG["note"]
D.rectangle(b, fill=(250, 244, 170))
hand(b, 16, 30, "NO PUBLIC", 26, (30, 30, 30))
hand(b, 16, 66, "RESTROOM", 26, (30, 30, 30))
hand(b, 16, 112, "sorry - try the", 17, (30, 30, 30))
hand(b, 16, 138, "gas station", 17, (30, 30, 30))
hand(b, 120, 190, "mgmt", 17, (30, 30, 30))
# food handler certificate (county, fictional)
b = REG["certificate"]
D.rectangle(b, fill=(236, 232, 218))
D.rectangle((b[0] + 10, b[1] + 10, b[2] - 11, b[3] - 11), outline=(60, 90, 70), width=4)
ctext(b, 26, "COUNTY OF LOS SANTOS", font("DejaVuSerif-Bold.ttf", 18), (60, 90, 70))
ctext(b, 54, "FOOD HANDLER CERTIFICATE", font("DejaVuSans-Bold.ttf", 18))
ctext(b, 100, "This certifies that", font("DejaVuSerif-Italic.ttf", 14))
ctext(b, 126, "S. R. DeLUCA", font("DejaVuSerif-Bold.ttf", 22))
ctext(b, 162, "has completed the required course", font("DejaVuSerif-Italic.ttf", 13))
ctext(b, 196, "No. 99-41877    Expires 06/2001", font("DejaVuSansMono.ttf", 13))
D.ellipse((b[0] + 250, b[1] + 186, b[0] + 300, b[1] + 236), outline=(150, 40, 34), width=3)
# tin sign: generic soda price sign (no brand)
b = REG["tin_sign"]
D.rectangle(b, fill=(150, 46, 38))
D.rectangle((b[0] + 12, b[1] + 12, b[2] - 13, b[3] - 13), outline=(232, 222, 196), width=4)
ctext(b, 40, "ICE COLD", font("DejaVuSans-Bold.ttf", 56), (232, 222, 196))
ctext(b, 110, "SODA", font("DejaVuSerif-Bold.ttf", 78), (232, 222, 196))
ctext(b, 214, "FOUNTAIN  ·  CANS  ·  BOTTLES", font("DejaVuSans.ttf", 20), (232, 222, 196))
reg = np.asarray(W.crop(b), dtype=np.float64) / 255.0
hh, ww = reg.shape[:2]
rust = (tnoise(hh, ww, 12, 16, SEED + 73) > 0.66) * np.clip(1 - np.mgrid[0:hh, 0:ww][0] / hh * 4, 0, 1) + \
       (tnoise(hh, ww, 12, 16, SEED + 74) > 0.70) * np.clip((np.mgrid[0:hh, 0:ww][0] / hh - 0.8) * 5, 0, 1)
reg = reg * (0.88 + 0.08 * tnoise(hh, ww, 4, 6, SEED + 75)[..., None])
reg = np.where(rust[..., None] > 0.5, np.array([0.45, 0.28, 0.18]), reg)
W.paste(to_img(reg), b[:2])
# global paper aging
wa = arr(W) * (0.96 + 0.05 * tnoise(1024, 1024, 8, 8, SEED + 76)[..., None])
save("lp5_wall", to_img(wa), ops="ORIGINAL wall story atlas: fictional supplier poster, 3 photos of our own interior (renders), sponsor plaque, "
     "hours card, catering notice, handwritten note, food-handler certificate, generic soda tin sign")
json.dump(REG, open(OUT / "lp5_wall_regions.json", "w"), indent=1)

# ======================================================================== 8. MEMORY: smaller copies of over-sized maps (hall budget < 16 MiB)
for nm, src, size in (("lp5_plaster", SLICE / "lp_wall_plaster.png", 512), ("lp5_plaster_n", SLICE / "lp_wall_plaster_n.png", 256),
                      ("lp5_plaster_s", SLICE / "lp_wall_plaster_s.png", 256), ("lp5_food_s", V021 / "lp2_food_s.png", 512),
                      ("lp5_leather_n", V021 / "lp2_leather_n.png", 512)):
    save(nm, load(src).convert("RGB").resize((size, size), Image.Resampling.LANCZOS), role="resized", derived=[src],
         ops=f"resized to {size} for the hall memory budget")

(OUT / "lp5_textures_report.json").write_text(json.dumps(REPORT, indent=1), encoding="utf-8")
print("DONE_V026_TEX", len(REPORT["textures"]))
