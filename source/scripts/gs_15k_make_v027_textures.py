# LONG PIG — v0.2.7 textures (owner feedback 2026-11-02 after the first in-game look at v0.2.6): new entrance logo mat
# (US restaurant style: nylon carpet logo mat on rubber backing with border), story atlas #2 (vinyl banner, enamel
# thermometer sign, tray-station flap, take-out menus, newspaper, tip label, food-stamps card, tomato / olive-oil labels),
# leak / spill decals, a wet puddle decal (normal_spec_decal: shiny), and smaller copies of three over-sized maps.
# ORIGINAL procedural / typographic work or resized copies of our own textures. No third-party / Rockstar pixels.
#   python gs_15k_make_v027_textures.py [<project_root>]   -> source/textures/v027/*.dds + lp6_textures_report.json
import sys, json, hashlib, math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds  # noqa: E402

T = ROOT / "source" / "textures"
V025, V023 = T / "v025", T / "v023"
OUT = T / "v027"
OUT.mkdir(parents=True, exist_ok=True)
FONT = Path("/usr/share/fonts/truetype/dejavu")
REPORT = {"script": "source/scripts/gs_15k_make_v027_textures.py", "version": "0.2.7", "textures": []}
SEED = 20261102 + 27
r = np.random.default_rng(SEED)


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


def save(name, img, fmt="DXT1", role="diffuse", derived=(), ops=""):
    png = OUT / f"{name}.png"
    img.save(png)
    gs_dds.convert(png, OUT / f"{name}.dds", fmt)
    data = (OUT / f"{name}.dds").read_bytes()
    REPORT["textures"].append({"name": name, "file": f"{name}.dds", "size": list(img.size), "format": fmt, "role": role,
                               "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                               "derived_from": [rel(d) for d in derived], "origin": "derived_own" if derived else "original_procedural",
                               "operations": ops})
    print("TEX", name, img.size, fmt, len(data))


def tnoise(h, w, cy, cx, seed, octaves=4, persist=0.55):
    rr = np.random.default_rng(seed)
    acc = np.zeros((h, w)); amp = 1.0; tot = 0.0
    for o in range(octaves):
        gy, gx = cy * 2 ** o, cx * 2 ** o
        if gy > h // 2 or gx > w // 2:
            break
        lat = (rr.random((gy, gx)) * 255).astype(np.uint8)
        big = Image.fromarray(np.tile(lat, (3, 3)), "L").resize((w * 3, h * 3), Image.Resampling.BICUBIC)
        acc += amp * np.asarray(big, dtype=np.float64)[h:2 * h, w:2 * w] / 255.0
        tot += amp; amp *= persist
    return acc / tot


def col(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def blur(a, rad):
    if a.ndim == 2:
        return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(rad)), dtype=np.float64) / 255.0
    return arr(to_img(a).filter(ImageFilter.GaussianBlur(rad)))


def normal_from_height(h, strength):
    gy, gx = np.gradient(h)
    nx, ny = -gx * strength, gy * strength
    nz = np.ones_like(h)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.dstack([nx / L * 0.5 + 0.5, ny / L * 0.5 + 0.5, nz / L * 0.5 + 0.5])


# ======================================================================== 1. ENTRANCE LOGO MAT (6' x 4', drawn 1.5:1, stored 2:1)
W, H = 1536, 1024
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
fib = tnoise(H, W, 256, 384, SEED + 1, octaves=2)
base = col("#2d2c2b") * (0.86 + 0.24 * fib)[..., None]                     # charcoal cut-pile nylon
bw = 62                                                                     # moulded rubber border
db = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
border = db < bw
ribs = 0.5 + 0.5 * np.sin(db * 2 * math.pi / 9.0)
rub = col("#1d1d1d") * (0.85 + 0.25 * ribs)[..., None]
base = np.where(border[..., None], rub, base)
im = to_img(base); D = ImageDraw.Draw(im)
D.rectangle((bw + 26, bw + 26, W - bw - 27, H - bw - 27), outline=(110, 36, 30), width=10)          # inlay pinstripe
cx, cy, R = W / 2, H / 2 + 10, 330
D.ellipse((cx - R * 1.5, cy - R, cx + R * 1.5, cy + R), outline=(116, 38, 32), width=16)
s = 92                                                                       # simple original pig mark
D.ellipse((cx - 1.0 * s, cy - 0.95 * R + 70, cx + 0.7 * s, cy - 0.95 * R + 70 + 1.05 * s), fill=(116, 38, 32))
D.ellipse((cx + 0.45 * s, cy - 0.95 * R + 60, cx + 1.15 * s, cy - 0.95 * R + 60 + 0.7 * s), fill=(116, 38, 32))
D.ellipse((cx + 1.02 * s, cy - 0.95 * R + 90, cx + 1.3 * s, cy - 0.95 * R + 116), fill=(116, 38, 32))
for lx in (-0.75, -0.35, 0.15, 0.45):
    D.rectangle((cx + lx * s, cy - 0.95 * R + 70 + 0.95 * s, cx + (lx + 0.16) * s, cy - 0.95 * R + 70 + 1.35 * s), fill=(116, 38, 32))
f1 = font("DejaVuSans-Bold.ttf", 150)
t1 = "LONG PIG"
D.text((cx - D.textlength(t1, font=f1) / 2, cy + 6), t1, fill=(126, 42, 34), font=f1)
f2 = font("DejaVuSans-Bold.ttf", 58)
t2 = "DELI  \u00b7  EST. 1979"
D.text((cx - D.textlength(t2, font=f2) / 2, cy + 176), t2, fill=(150, 132, 108), font=f2)
a = arr(im)
logo = (a[..., 0] - a[..., 2]) > 0.08                                       # tufted inlay keeps the pile texture
a = np.where(logo[..., None], a * (0.82 + 0.3 * fib)[..., None], a)
# traffic wear: flattened, lighter, grittier pile on the walking line (far side = inside), crumbs, a coffee drip
wear = np.exp(-(((xx - W * 0.52) / (W * 0.24)) ** 2 + ((yy - H * 0.48) / (H * 0.45)) ** 2))
a = a * (1 - 0.06 * wear[..., None]) + col("#6e665a") * 0.20 * wear[..., None] * tnoise(H, W, 24, 36, SEED + 2)[..., None]
grit = (tnoise(H, W, 180, 260, SEED + 3, octaves=1) > 0.90) * ~border * (wear > 0.25)
a = np.where(grit[..., None], a * 0.8 + col("#8a8070") * 0.2, a)
st = np.exp(-(((xx - W * 0.71) / 70) ** 2 + ((yy - H * 0.32) / 46) ** 2)) * 0.35
a = a * (1 - st[..., None]) + col("#3a2a1c") * st[..., None]
a = a * (0.94 + 0.08 * tnoise(H, W, 4, 6, SEED + 4)[..., None])
save("lp6_mat", to_img(a).resize((1024, 512), Image.Resampling.LANCZOS),
     ops="ORIGINAL 6x4 ft nylon logo mat: charcoal pile, ribbed rubber border, red inlay (pig mark, LONG PIG, EST. 1979), traffic wear, grit, stain")
h = 0.5 * fib + np.where(border, 0.6 * ribs, 0.0) + 0.15 * logo
save("lp6_mat_n", to_img(normal_from_height(blur(h, 1.0), 6.0)).resize((512, 256), Image.Resampling.LANCZOS), role="normal",
     ops="ORIGINAL pile + rib normal")

# ======================================================================== 2. STORY ATLAS #2 (1024 x 1024)
A = Image.new("RGB", (1024, 1024), (225, 218, 202)); D = ImageDraw.Draw(A)
REG6 = {"banner": (0, 0, 1024, 136), "thermo": (0, 136, 128, 520), "flap": (128, 136, 384, 392), "menus": (384, 136, 640, 392),
        "news": (640, 136, 1024, 392), "tips": (128, 392, 384, 520), "stamps": (384, 392, 640, 520), "can_label": (640, 392, 1024, 456),
        "tin_label": (640, 456, 832, 744), "tin_label2": (832, 456, 1024, 744), "station_top": (0, 520, 640, 1024)}


def ctext(box, y, txt, f, fill=(30, 30, 30)):
    w_ = D.textlength(txt, font=f)
    D.text(((box[0] + box[2]) / 2 - w_ / 2, box[1] + y), txt, fill=fill, font=f)


# vinyl banner over the storefront (inside), sun-faded, grommets
b = REG6["banner"]
D.rectangle(b, fill=(236, 228, 206))
D.rectangle((b[0] + 8, b[1] + 8, b[2] - 9, b[3] - 9), outline=(150, 46, 38), width=5)
ctext(b, 18, "LONG PIG DELI", font("DejaVuSans-Bold.ttf", 54), (150, 46, 38))
ctext(b, 84, "HEROES  \u00b7  SALUMI  \u00b7  PARTY TRAYS  \u00b7  HOT FOOD  \u00b7  SINCE 1979", font("DejaVuSans-Bold.ttf", 22), (60, 66, 44))
for gx in (22, 340, 684, 1001):
    for gy in (20, 116):
        D.ellipse((gx - 7, gy - 7, gx + 7, gy + 7), fill=(170, 160, 140), outline=(90, 84, 70), width=2)
# enamel thermometer sign (vertical)
b = REG6["thermo"]
D.rectangle(b, fill=(150, 40, 34))
D.rectangle((b[0] + 6, b[1] + 6, b[2] - 7, b[3] - 7), outline=(232, 222, 196), width=3)
ctext(b, 18, "COLD", font("DejaVuSans-Bold.ttf", 26), (232, 222, 196))
ctext(b, 48, "CUTS", font("DejaVuSans-Bold.ttf", 26), (232, 222, 196))
D.rounded_rectangle((b[0] + 50, b[1] + 92, b[0] + 78, b[1] + 330), radius=12, fill=(236, 230, 214))
D.ellipse((b[0] + 44, b[1] + 312, b[0] + 84, b[1] + 352), fill=(190, 30, 26))
D.rectangle((b[0] + 60, b[1] + 200, b[0] + 68, b[1] + 320), fill=(190, 30, 26))
fs = font("DejaVuSans.ttf", 11)
for k, tval in enumerate(range(120, -1, -20)):
    yv = b[1] + 100 + k * 33
    D.line((b[0] + 80, yv, b[0] + 90, yv), fill=(232, 222, 196), width=2)
    D.text((b[0] + 92, yv - 6), str(tval), fill=(232, 222, 196), font=fs)
ctext(b, 356, "LONG PIG", font("DejaVuSans-Bold.ttf", 15), (232, 222, 196))
# tray-station push flap (stainless with embossed THANK YOU)
b = REG6["flap"]
g = 0.62 + 0.10 * tnoise(256, 256, 2, 64, SEED + 5, octaves=2)
A.paste(to_img(np.dstack([g, g, g * 1.01])), b[:2])
ctext(b, 92, "THANK", font("DejaVuSans-Bold.ttf", 46), (88, 88, 90))
ctext(b, 144, "YOU", font("DejaVuSans-Bold.ttf", 46), (88, 88, 90))
D.rectangle((b[0] + 30, b[1] + 230, b[2] - 30, b[1] + 248), fill=(70, 66, 60))           # grimy finger plate
# take-out menu cover
b = REG6["menus"]
D.rectangle(b, fill=(244, 238, 218))
ctext(b, 24, "LONG PIG", font("DejaVuSerif-Bold.ttf", 40), (150, 46, 38))
ctext(b, 74, "DELI  \u00b7  RANCHO", font("DejaVuSans.ttf", 20), (60, 60, 60))
ctext(b, 118, "TAKE-OUT MENU", font("DejaVuSans-Bold.ttf", 26), (30, 30, 30))
ctext(b, 168, "555-0179  \u00b7  WE CATER", font("DejaVuSans.ttf", 20), (60, 60, 60))
ctext(b, 206, "open 7 days", font("DejaVuSerif-Italic.ttf", 18), (60, 60, 60))
# newspaper (fictional local weekly)
b = REG6["news"]
D.rectangle(b, fill=(214, 208, 192))
ctext(b, 8, "RANCHO WEEKLY", font("DejaVuSerif-Bold.ttf", 34), (30, 30, 30))
D.line((b[0] + 10, b[1] + 50, b[2] - 10, b[1] + 50), fill=(30, 30, 30), width=2)
D.text((b[0] + 12, b[1] + 56), "NOV. 8, 2001  \u00b7  50 CENTS", fill=(40, 40, 40), font=font("DejaVuSans.ttf", 13))
D.text((b[0] + 12, b[1] + 76), "JAMESTOWN ST. POTHOLES: AGAIN", fill=(20, 20, 20), font=font("DejaVuSans-Bold.ttf", 15))
D.rectangle((b[0] + 12, b[1] + 102, b[0] + 160, b[1] + 200), fill=(120, 116, 108))
for col_x in (172, 270):
    for k in range(14):
        ly = b[1] + 104 + k * 10
        D.line((b[0] + col_x, ly, b[0] + col_x + 88 - (k % 5) * 6, ly), fill=(90, 88, 82), width=2)
for k in range(5):
    ly = b[1] + 210 + k * 9
    D.line((b[0] + 12, ly, b[0] + 360 - (k % 3) * 20, ly), fill=(90, 88, 82), width=2)
# tip-jar label and food stamps card
b = REG6["tips"]
D.rectangle(b, fill=(250, 244, 170))
ctext(b, 18, "TIPS", font("DejaVuSans-Bold.ttf", 52), (30, 30, 30))
ctext(b, 82, "thank you!", font("DejaVuSans-Oblique.ttf", 26), (30, 40, 110))
b = REG6["stamps"]
D.rectangle(b, fill=(238, 236, 228))
D.rectangle((b[0] + 6, b[1] + 6, b[2] - 7, b[3] - 7), outline=(40, 90, 60), width=4)
ctext(b, 20, "WE ACCEPT", font("DejaVuSans-Bold.ttf", 28), (40, 90, 60))
ctext(b, 58, "FOOD STAMPS", font("DejaVuSans-Bold.ttf", 30), (40, 90, 60))
ctext(b, 98, "& WIC", font("DejaVuSans.ttf", 18), (40, 40, 40))
# tomato-can label strip (generic Italian-style, fictional brand) and olive-oil tin labels
b = REG6["can_label"]
D.rectangle(b, fill=(190, 40, 30))
for k in range(4):
    x0 = b[0] + 10 + k * 96
    D.ellipse((x0, b[1] + 16, x0 + 34, b[1] + 50), fill=(220, 60, 40))
    D.polygon([(x0 + 12, b[1] + 16), (x0 + 17, b[1] + 8), (x0 + 22, b[1] + 16)], fill=(60, 110, 40))
    D.text((x0 + 40, b[1] + 20), "PELATI", fill=(244, 230, 200), font=font("DejaVuSans-Bold.ttf", 15))
for key, c0, c1, txt in (("tin_label", (196, 170, 60), (40, 80, 40), "OLIO"), ("tin_label2", (40, 80, 50), (220, 190, 80), "OLIVA")):
    b = REG6[key]
    D.rectangle(b, fill=c0)
    D.rectangle((b[0] + 10, b[1] + 10, b[2] - 11, b[3] - 11), outline=c1, width=4)
    ctext(b, 40, txt, font("DejaVuSerif-Bold.ttf", 38), c1)
    ctext(b, 96, "EXTRA", font("DejaVuSans-Bold.ttf", 20), c1)
    ctext(b, 122, "VERGINE", font("DejaVuSans-Bold.ttf", 20), c1)
    D.ellipse((b[0] + 66, b[1] + 170, b[0] + 126, b[1] + 230), outline=c1, width=4)
    ctext(b, 240, "5 L", font("DejaVuSans.ttf", 18), c1)
# tray-station top (laminate with grime ring where trays sit)
b = REG6["station_top"]
wv, hv = b[2] - b[0], b[3] - b[1]
tex = np.dstack([0.70 + 0 * np.zeros((hv, wv)), 0.62 + 0 * np.zeros((hv, wv)), 0.50 + 0 * np.zeros((hv, wv))])
tex = tex * (0.92 + 0.10 * tnoise(hv, wv, 4, 8, SEED + 6)[..., None])
yy2, xx2 = np.mgrid[0:hv, 0:wv]
ring = np.exp(-((np.hypot((xx2 - wv * 0.45) / 1.6, yy2 - hv * 0.5) - 90) / 8) ** 2) * 0.25
tex = tex * (1 - ring[..., None])
A.paste(to_img(tex), b[:2])
aa = arr(A) * (0.95 + 0.06 * tnoise(1024, 1024, 8, 8, SEED + 7)[..., None])
# sun fading on the banner and the thermometer sign
fade = np.zeros((1024, 1024)); fade[0:136, :] = 0.25; fade[136:520, 0:128] = 0.18
aa = aa * (1 - fade[..., None]) + np.array([0.92, 0.88, 0.80]) * fade[..., None]
save("lp6_atlas", to_img(aa), ops="ORIGINAL: storefront banner, thermometer sign, tray-station flap, take-out menu, fictional weekly, tip label, "
     "food-stamps card, tomato-can label, olive-oil tin labels, station top")
json.dump(REG6, open(OUT / "lp6_atlas_regions.json", "w"), indent=1)

# ======================================================================== 3. LEAK / SPILL DECALS (DXT5, 2 x 2 cells of 256)
DC = np.zeros((512, 512, 4))
cy_, cx_ = np.mgrid[0:256, 0:256].astype(np.float64)
u, v = cx_ / 255.0, cy_ / 255.0


def put(i, rgb, alpha):
    x, y = (i % 2) * 256, (i // 2) * 256
    DC[y:y + 256, x:x + 256, :3] = rgb
    DC[y:y + 256, x:x + 256, 3] = np.clip(alpha, 0, 1)


for i, (wid, seed) in enumerate(((0.30, 11), (0.16, 12))):                 # 0, 1: leak streaks from the ceiling joint (top = v 0)
    n = tnoise(256, 256, 2, 16, SEED + seed, octaves=3)
    cxw = 0.5 + 0.08 * (tnoise(256, 256, 8, 1, SEED + seed + 5, octaves=2) - 0.5)
    prof = np.exp(-((u - cxw) / (wid * (0.55 + 0.6 * (1 - v)))) ** 2)
    length = 0.55 + 0.45 * n
    body = prof * np.clip((length - v) / 0.25, 0, 1)
    tide = np.exp(-((v - length * 0.92) / 0.02) ** 2) * prof * 1.4             # dried tide line at the lower edge
    put(i * 1, np.dstack([u * 0 + 0.47, u * 0 + 0.36, u * 0 + 0.22]), np.clip(body * 0.45 + tide * 0.45, 0, 0.75))
rd = np.hypot(u - 0.5, (v - 0.5) * 1.25) / 0.42 + 0.22 * (tnoise(256, 256, 6, 6, SEED + 13) - 0.5)
put(2, np.dstack([u * 0 + 0.24, u * 0 + 0.14, u * 0 + 0.07]), np.clip((1 - rd) * 3, 0, 1) * 0.55)          # sticky soda spill
fp = np.zeros((256, 256))                                                                                 # wet shoe prints
for k in range(5):
    px, py = 60 + k * 36, 220 - k * 42
    fp += np.exp(-(((u * 256 - px) / 14) ** 2 + ((v * 256 - py) / 26) ** 2))
put(3, np.dstack([u * 0 + 0.18, u * 0 + 0.17, u * 0 + 0.16]), np.clip(fp, 0, 1) * 0.30)
save("lp6_decal", Image.fromarray((np.clip(DC, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA"), fmt="DXT5",
     ops="ORIGINAL decals: 2 ceiling leak streaks with tide lines, sticky soda spill, wet shoe prints")

# ======================================================================== 4. PUDDLE (normal_spec_decal: dark, glossy, irregular)
cy2, cx2 = np.mgrid[0:256, 0:256].astype(np.float64)
uu, vv = cx2 / 255.0, cy2 / 255.0
rd = np.hypot(uu - 0.5, vv - 0.5) / 0.44 + 0.30 * (tnoise(256, 256, 5, 5, SEED + 21) - 0.5)
mask = np.clip((1 - rd) * 6, 0, 1)
rgb = np.dstack([uu * 0 + 0.10, uu * 0 + 0.11, uu * 0 + 0.12])
save("lp6_puddle", Image.fromarray((np.clip(np.dstack([rgb, mask * 0.55]), 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA"), fmt="DXT5",
     ops="ORIGINAL puddle mask (dark, translucent)")
save("lp6_puddle_s", Image.new("RGB", (64, 64), (255, 255, 255)), role="spec", ops="ORIGINAL full specular")

# ======================================================================== 5. MEMORY: smaller copies (hall < 16 MiB with the new maps)
for nm, src, size in (("lp6_food_n", V023 / "lp3_food_n.png", 512), ("lp6_laminate_red", V025 / "lp4_laminate_red.png", 512),
                      ("lp6_laminate_cream", V025 / "lp4_laminate_cream.png", 512)):
    save(nm, load(src).convert("RGB").resize((size, size), Image.Resampling.LANCZOS), role="resized", derived=[src],
         ops=f"resized to {size} for the hall memory budget")

(OUT / "lp6_textures_report.json").write_text(json.dumps(REPORT, indent=1), encoding="utf-8")
print("DONE_V027_TEX", len(REPORT["textures"]))
