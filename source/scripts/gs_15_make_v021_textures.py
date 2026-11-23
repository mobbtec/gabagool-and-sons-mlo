# LONG PIG — v0.2.1 hero-kit textures: GTA-ready DDS (full mip chain) from the approved CC0 originals plus ORIGINAL
# procedural textures (food atlas, enamel, cast iron, opal glass, Italian tricolore cloth). Pure Python (Pillow + numpy
# + source/tools/gs_dds.py). Nothing here is derived from Rockstar files.
#   python gs_15_make_v021_textures.py <cc0_downloads_dir> [<out_dir>]
# CC0 inputs (byte-exact originals, see assets/cc0/_downloads/fetch_manifest.json): Poly Haven kitchen_wood,
# brown_leather (diff/albedo, nor_dx, rough).
# Outputs per material <name>: <name>.dds diffuse, <name>_n.dds DirectX normal, <name>_s.dds spec (grey) + JSON report.
import sys, io, json, hashlib, math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import gs_dds  # noqa: E402

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / "textures" / "v021"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20261031)
REPORT = {"script": "source/scripts/gs_15_make_v021_textures.py", "version": "0.2.1", "textures": []}


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def load(name):
    return Image.open(io.BytesIO((SRC / name).read_bytes())), name


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


# ================================================================== 1. walnut (deep, slightly red, low saturation)
col, c_src = load("kitchen_wood_diff_2k.jpg")
nrm, n_src = load("kitchen_wood_nor_dx_2k.jpg")
rgh, r_src = load("kitchen_wood_rough_2k.jpg")
wal = tint(rgb(col), "#3E2519", detail=1.45, keep_hue=0.20)
save("lp2_walnut", wal, 1024, derived=[c_src], ops="tint dark walnut #3E2519, detail x1.45")
save("lp2_walnut_n", renorm(rgb(nrm), 0.9), 1024, role="normal", derived=[n_src], ops="bump x0.9")
save("lp2_walnut_s", spec_from_rough(grey(rgh), 0.55, 0.06), 512, role="spec", derived=[r_src], ops="satin: 0.06 + 0.55 (1-rough)^1.5")

# ================================================================== 2. oxblood leather (vinyl/leather upholstery)
col, c_src = load("brown_leather_albedo_2k.jpg")
nrm, n_src = load("brown_leather_nor_dx_2k.jpg")
rgh, r_src = load("brown_leather_rough_2k.jpg")
lea = tint(rgb(col), "#4E1519", detail=1.6, keep_hue=0.10)
wear = fbm(2048, 6, 3, 0.6, 11)
lea = mix(lea, lea * np.array([1.18, 1.08, 1.06]), np.clip((wear - 0.62) * 3, 0, 1) * 0.6)   # soft polish patches
save("lp2_leather", lea, 1024, derived=[c_src], ops="tint oxblood #4E1519, detail x1.6, original fBm polish patches")
save("lp2_leather_n", renorm(rgb(nrm), 1.3), 1024, role="normal", derived=[n_src], ops="bump x1.3")
save("lp2_leather_s", spec_from_rough(grey(rgh), 0.65, 0.10) * (0.85 + 0.3 * wear), 512, role="spec", derived=[r_src],
     ops="0.10 + 0.65 (1-rough)^1.5, modulated by polish patches")

# ================================================================== 3. ORIGINAL: cream enamel (deli case body, light fittings)
n = 512
e_n = fbm(n, 6, 4, 0.5, 21)
enamel = lerp_col("#E9E1CF", "#D9CFB8", e_n * 0.7)
scr = spots(n, 26, 1.0, 2.2, 22, ecc=12.0)
enamel = mix(enamel, enamel * 0.86, scr * 0.5)
save("lp2_enamel", enamel, 512, ops="procedural cream enamel, fBm tone + fine scratches")
save("lp2_enamel_n", height_to_normal(wrap_blur(e_n, 2) * 0.4 - scr * 0.6, 3.0), 512, role="normal", ops="from enamel height")
save("lp2_enamel_s", np.clip(0.75 - scr * 0.3 - e_n * 0.1, 0, 1), 256, role="spec", ops="glossy enamel")

# ================================================================== 4. ORIGINAL: cast iron (table bases, rail brackets)
n = 512
ir = fbm(n, 7, 6, 0.6, 31)
iron = lerp_col("#1B1A19", "#34302C", ir)
rust = np.clip((fbm(n, 5, 4, 0.6, 32) - 0.72) * 4, 0, 1)
iron = mix(iron, lerp_col("#3A2418", "#5A3420", ir), rust * 0.45)
save("lp2_iron", iron, 512, ops="procedural cast iron, fBm + faint rust")
save("lp2_iron_n", height_to_normal(ir, 6.0), 512, role="normal", ops="pitting from fBm")
save("lp2_iron_s", np.clip(0.35 + ir * 0.2 - rust * 0.25, 0, 1), 256, role="spec", ops="semi-matte metal")

# ================================================================== 5. ORIGINAL: opal (milk) glass for lit shades
n = 256
yy = np.linspace(0, 1, n)[:, None] * np.ones((1, n))
opal = lerp_col("#FFF3DC", "#F2D9AE", yy ** 1.5)
save("lp2_opal", opal, 256, ops="procedural warm milk-glass gradient (emissive)")

# ================================================================== 6. ORIGINAL: Italian tricolore cloth (flag), 2:3
W, H = 768, 512
x = np.linspace(0, 1, W)[None, :] * np.ones((H, 1))
flag = np.zeros((H, W, 3))
flag[:] = hexcol("#F4F2EA")
flag[x < 1 / 3] = hexcol("#0F7A41")
flag[x > 2 / 3] = hexcol("#C8202F")
# woven cloth: fine warp/weft + soft fading at the hoist side (sun) + slight edge hem
yy_, xx_ = np.mgrid[0:H, 0:W]
weave = 0.5 + 0.25 * np.sin(xx_ * math.pi / 1.5) * np.sin(yy_ * math.pi / 1.5)
fade = fbm(512, 5, 3, 0.6, 41)
fade = np.asarray(Image.fromarray((fade * 255).astype(np.uint8)).resize((W, H)), dtype=np.float64) / 255.0
flag = flag * (0.93 + 0.07 * weave[..., None]) * (0.92 + 0.08 * fade[..., None])
hem = (xx_ < 10) | (xx_ > W - 8) | (yy_ < 8) | (yy_ > H - 8)
flag[hem] *= 0.9
save("lp2_flag", flag, 512, 512, ops="original Italian tricolore (green/white/red, plain), procedural weave + fade")
hgt = weave * 0.6 + hem * 0.4
save("lp2_flag_n", height_to_normal(np.asarray(Image.fromarray((hgt * 255).astype(np.uint8)).resize((512, 512)), dtype=np.float64) / 255.0, 1.5),
     512, role="normal", ops="weave normal")

# ================================================================== 7. ORIGINAL: food atlas 2048 (4 x 4 cells of 512)
C = 512
cells = {}
yy, xx = np.mgrid[0:C, 0:C]
r_c = np.sqrt((xx - C / 2 + 0.5) ** 2 + (yy - C / 2 + 0.5) ** 2) / (C / 2)        # radial coordinate for cut faces


def cell_salami_casing():
    base = lerp_col("#3A1A15", "#5E2A20", fbm(C, 6, 4, 0.6, 51))
    bloom = np.clip((fbm(C, 6, 3, 0.65, 52) - 0.42) * 1.6, 0, 1)                 # dusty white mould bloom
    bloom = np.maximum(bloom, wrap_blur(spots(C, 60, 3, 10, 53), 2.0) * 0.45)
    col = mix(base, lerp_col("#B9B0A2", "#DCD5C8", fbm(C, 4, 8, 0.5, 54)), bloom * 0.62)
    wrinkle = np.abs(np.sin(yy / C * 2 * math.pi * 9 + fbm(C, 4, 3, 0.5, 55) * 6)) ** 3
    col *= (0.88 + 0.12 * (1 - wrinkle))[..., None]
    return col, bloom * 0.3 + wrinkle * 0.5 + fbm(C, 6, 8, 0.5, 56) * 0.4, 0.15 + 0.15 * (1 - bloom)


def cell_salami_cut():
    meat = lerp_col("#8E1F26", "#B5323A", fbm(C, 6, 6, 0.6, 61))
    fat = np.maximum(spots(C, 420, 2.5, 9, 62, ecc=1.7), spots(C, 160, 5, 12, 67, ecc=2.4) * 0.9)
    pep = spots(C, 90, 1.2, 2.4, 63)
    col = mix(meat, lerp_col("#F1E2D0", "#FFF4E6", fbm(C, 3, 8, 0.5, 64)), np.clip(fat * 1.4, 0, 1))
    col = mix(col, np.full_like(col, 0.07), pep * 0.9)
    rim = np.clip((r_c - 0.92) * 14, 0, 1)                                          # casing ring
    col = mix(col, lerp_col("#4A1E1A", "#6B2A22", fbm(C, 3, 8, 0.5, 65)), rim)
    return col, fat * 0.4 + fbm(C, 5, 16, 0.5, 66) * 0.3, 0.30 + fat * 0.25


def cell_prosciutto_rind():
    t = fbm(C, 6, 3, 0.6, 71)
    col = lerp_col("#6E3A1C", "#A2663A", t)
    col = mix(col, lerp_col("#4A2612", "#6A3A1E", t), np.clip((fbm(C, 5, 4, 0.6, 72) - 0.45) * 3, 0, 1) * 0.8)
    lard = np.clip((fbm(C, 4, 2, 0.6, 74) - 0.62) * 4, 0, 1)                      # sugna (lard paste) patches
    col = mix(col, lerp_col("#D8CDB8", "#EDE4D2", fbm(C, 3, 8, 0.5, 75)), lard * 0.7)
    salt = spots(C, 140, 1.0, 2.5, 73)
    col = mix(col, np.full_like(col, 0.93), salt * 0.5)
    return col, t * 0.6 + salt * 0.3, 0.35 + 0.2 * t


def cell_prosciutto_cut():
    # rose meat in the middle, ivory fat rim at the top half: v (rows) 0 = fat side
    meat = lerp_col("#B4404A", "#D2646A", fbm(C, 6, 5, 0.6, 81))
    fatline = np.clip((0.22 - yy / C + 0.05 * fbm(C, 4, 3, 0.5, 82)) * 12, 0, 1)
    col = mix(meat, lerp_col("#F4EADB", "#FFF8EC", fbm(C, 4, 6, 0.5, 83)), fatline)
    marb = np.clip((fbm(C, 6, 8, 0.6, 84) - 0.66) * 4, 0, 1)
    col = mix(col, np.full_like(col, 0.92), marb * 0.45)
    return col, marb * 0.3 + fbm(C, 5, 16, 0.5, 85) * 0.3, 0.45 + 0.2 * fatline


def cell_provolone_wax():
    t = fbm(C, 6, 3, 0.6, 91)
    col = lerp_col("#B9801F", "#DDA840", t)
    grooves = np.abs(np.sin(yy / C * 2 * math.pi * 3)) ** 16                       # faint rope impressions
    col *= (1 - 0.10 * grooves)[..., None]
    col = mix(col, lerp_col("#8C5E1E", "#A87128", t), np.clip((fbm(C, 4, 6, 0.6, 92) - 0.7) * 3, 0, 1) * 0.5)
    return col, grooves * 0.7 + t * 0.3, 0.55


def cell_cheese_cut():
    t = fbm(C, 5, 4, 0.6, 101)
    col = lerp_col("#EFE0B0", "#F7EBC6", t)
    holes = spots(C, 14, 6, 16, 102, ecc=1.2)
    col = mix(col, lerp_col("#D8C48C", "#E0CC94", t), holes)
    rind = np.clip((r_c - 0.9) * 10, 0, 1)
    col = mix(col, hexcol("#C79A3A")[None, None, :] * np.ones_like(col), rind)
    return col, -holes * 0.6 + t * 0.2, 0.30


def cell_parm_rind():
    t = fbm(C, 7, 6, 0.6, 111)
    col = lerp_col("#C69A4A", "#E2BE75", t)
    return col, t, 0.25


def cell_mortadella():
    meat = lerp_col("#E59C9A", "#F2B4B0", fbm(C, 5, 4, 0.6, 121))
    fat = spots(C, 70, 5, 13, 122, ecc=1.1)
    pist = spots(C, 26, 3, 6, 123)
    col = mix(meat, np.full_like(meat, 0.97), fat)
    col = mix(col, hexcol("#6E9A3A")[None, None, :] * np.ones_like(col), pist)
    rim = np.clip((r_c - 0.95) * 20, 0, 1)
    col = mix(col, hexcol("#B76C64")[None, None, :] * np.ones_like(col), rim)
    return col, fat * 0.3, 0.45


def cell_olives(c0, c1, seed):
    base = lerp_col(c0, c1, fbm(C, 4, 4, 0.6, seed))
    m = np.zeros((C, C)); hl = np.zeros((C, C))
    rng = np.random.default_rng(seed)
    for _ in range(140):
        cx, cy, r = rng.random() * C, rng.random() * C, 18 + 10 * rng.random()
        d = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.3) ** 2) / r
        m = np.maximum(m, np.clip(1 - d, 0, 1) ** 0.5)
        hl = np.maximum(hl, np.clip(1 - np.sqrt((xx - cx + r * 0.3) ** 2 + (yy - cy + r * 0.35) ** 2) / (r * 0.25), 0, 1))
    col = base * (0.35 + 0.65 * m[..., None]) + hl[..., None] * 0.35
    return col, m, 0.6 + 0.3 * hl


def cell_peppers():
    t = fbm(C, 5, 3, 0.6, 141)
    warp = fbm(C, 4, 2, 0.55, 142)
    col = lerp_col("#9E1712", "#D8401A", t)
    folds = np.abs(np.sin((xx * 0.7 + yy * 0.5 + 160 * warp) / C * 2 * math.pi * 4.5)) ** 0.5
    yellow = np.clip((fbm(C, 3, 2, 0.6, 143) - 0.68) * 4, 0, 1)                     # some yellow pepper strips
    col = mix(col, lerp_col("#D99A1C", "#F0C040", t), yellow * 0.9)
    char = np.clip((fbm(C, 6, 6, 0.6, 144) - 0.7) * 5, 0, 1)
    col = mix(col * (0.55 + 0.45 * folds)[..., None], np.full_like(col, 0.12), char * 0.6)
    return col, folds * 0.7 + t * 0.3, 0.8


def cell_mozzarella():
    t = fbm(C, 5, 3, 0.6, 151)
    col = lerp_col("#F2F0E8", "#FFFFFA", t)
    return col, t * 0.3, 0.6


def cell_mortadella_casing():
    t = fbm(C, 5, 4, 0.6, 161)
    col = lerp_col("#B9796E", "#D79A8E", t)
    net = (np.abs(np.sin((xx + yy) / C * 2 * math.pi * 10)) ** 30 + np.abs(np.sin((xx - yy) / C * 2 * math.pi * 10)) ** 30)
    col = mix(col, np.full_like(col, 0.82), np.clip(net, 0, 1) * 0.35)
    return col, np.clip(net, 0, 1) * 0.6 + t * 0.2, 0.45


def cell_twine():
    t = np.abs(np.sin((xx + yy * 0.6) / C * 2 * math.pi * 24)) ** 0.7
    col = lerp_col("#B9A27A", "#E1CFA6", t * 0.7 + 0.3 * fbm(C, 4, 8, 0.5, 171))
    return col, t, 0.1


def cell_paper():
    t = fbm(C, 5, 6, 0.55, 181)
    col = lerp_col("#E9E1D2", "#F6F0E4", t)
    return col, t * 0.3, 0.2


def cell_salami_cut_fine():   # finocchiona-style, fine grain
    meat = lerp_col("#9B2A2E", "#B9474A", fbm(C, 6, 8, 0.6, 191))
    fat = spots(C, 700, 1.5, 4.5, 192)
    col = mix(meat, np.full_like(meat, 0.95), np.clip(fat * 1.3, 0, 1))
    rim = np.clip((r_c - 0.93) * 14, 0, 1)
    col = mix(col, hexcol("#E9E0D2")[None, None, :] * np.ones_like(col), rim)       # white bloom casing
    return col, fat * 0.3, 0.3


order = [cell_salami_casing, cell_salami_cut, cell_prosciutto_rind, cell_prosciutto_cut,
         cell_provolone_wax, cell_cheese_cut, cell_parm_rind, cell_mortadella,
         lambda: cell_olives("#4E5A1C", "#7A8530", 131), lambda: cell_olives("#2A1622", "#4A2A36", 132), cell_peppers, cell_mozzarella,
         cell_mortadella_casing, cell_twine, cell_paper, cell_salami_cut_fine]
FOOD_CELLS = ["salami_casing", "salami_cut", "prosciutto_rind", "prosciutto_cut", "provolone_wax", "cheese_cut", "parm_rind",
              "mortadella_cut", "olives_green", "olives_black", "peppers", "mozzarella", "mortadella_casing", "twine", "paper", "salami_fine_cut"]
atl = np.zeros((C * 4, C * 4, 3)); hgt = np.zeros((C * 4, C * 4)); spc = np.zeros((C * 4, C * 4))
for i, fn in enumerate(order):
    c, h, s = fn()
    r, k = divmod(i, 4)
    atl[r * C:(r + 1) * C, k * C:(k + 1) * C] = np.clip(c, 0, 1)
    hh = np.asarray(h, dtype=np.float64)
    hgt[r * C:(r + 1) * C, k * C:(k + 1) * C] = (hh - hh.min()) / (hh.max() - hh.min() + 1e-9)
    spc[r * C:(r + 1) * C, k * C:(k + 1) * C] = np.clip(np.broadcast_to(s, (C, C)), 0, 1)
save("lp2_food", atl, 2048, ops="ORIGINAL procedural deli food atlas 4x4: " + ", ".join(FOOD_CELLS))
save("lp2_food_n", height_to_normal(hgt, 2.5), 2048, role="normal", ops="from atlas height fields")
save("lp2_food_s", spc, 1024, role="spec", ops="per-cell gloss")
REPORT["food_cells"] = FOOD_CELLS

(OUT / "lp2_textures_report.json").write_text(json.dumps(REPORT, indent=1), encoding="utf-8")
print("GS15_DONE", len(REPORT["textures"]))
