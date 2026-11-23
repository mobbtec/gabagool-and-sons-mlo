# LONG PIG 0.3.1 textures (own procedural, Pillow + numpy; no Rockstar pixels):
#   lp_billboard   1024x512  roof billboard (replaces the embedded texture of sc1_14_bb_meltdown / sc1_14_bb_mollis)
#   lp8_atlas      region "open_neon" (320x128) repainted: lit price board instead of the OPEN neon (owner 2026-11-12)
import sys, json, hashlib, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
FD = Path("/usr/share/fonts/truetype")
def font(name, size):
    for p in (FD / "google-fonts" / name, FD / "dejavu" / name, FD / "liberation2" / name, FD / "liberation" / name):
        if p.is_file():
            return ImageFont.truetype(str(p), size)
    return ImageFont.truetype(str(FD / "dejavu" / "DejaVuSans-Bold.ttf"), size)
def noise(h, w, scale, seed):
    r = np.random.default_rng(seed)
    a = r.random((max(2, h // scale + 2), max(2, w // scale + 2)))
    return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), float) / 255.0
OUT = ROOT / "source" / "textures" / "v031"
OUT.mkdir(parents=True, exist_ok=True)
rep = {}

# ------------------------------------------------------------------ billboard
W, H = 1024, 512
img = Image.new("RGB", (W, H), (146, 34, 30))
d = ImageDraw.Draw(img)
d.rectangle((0, 300, W, H), fill=(46, 96, 160))                                  # blue band
d.rectangle((0, 292, W, 300), fill=(232, 222, 196))
CREAM, YEL, RED, BLUE = (236, 228, 204), (240, 200, 60), (160, 30, 28), (40, 86, 150)
# own pig silhouette (ellipses + polygons)
pig = Image.new("L", (W, H), 0)
pd = ImageDraw.Draw(pig)
pd.ellipse((70, 150, 520, 400), fill=255)                                        # body
pd.ellipse((440, 180, 610, 350), fill=255)                                       # head
pd.rounded_rectangle((585, 250, 650, 310), radius=18, fill=255)                  # snout
pd.polygon([(470, 195), (488, 130), (530, 185)], fill=255)                       # ears
pd.polygon([(535, 185), (570, 135), (590, 200)], fill=255)
for x in (130, 205, 380, 450):
    pd.polygon([(x, 370), (x + 46, 370), (x + 38, 452), (x + 6, 452)], fill=255)  # legs
for k in range(40):                                                              # curly tail
    a = k / 39 * 2.4 * math.pi
    r = 26 - k * 0.35
    pd.ellipse((62 + math.cos(a) * r - 6, 215 - math.sin(a) * r - 6, 62 + math.cos(a) * r + 6, 215 - math.sin(a) * r + 6), fill=255)
img.paste(Image.new("RGB", (W, H), CREAM), (0, 0), pig)
d = ImageDraw.Draw(img)
d.ellipse((560, 232, 572, 244), fill=(40, 30, 30))                               # eye
f_big = font("Poppins-Bold.ttf", 118)
d.text((40, 4), "LONG", font=f_big, fill=CREAM, stroke_width=3, stroke_fill=(90, 18, 16))
d.text((392, 4), "PIG", font=f_big, fill=YEL, stroke_width=3, stroke_fill=(90, 18, 16))
f_mm = font("Poppins-Bold.ttf", 54)
d.text((150, 205), "MINI", font=f_mm, fill=RED)
d.text((150, 262), "MARKET", font=f_mm, fill=BLUE)
d.text((60, 440), "& Fast Foods", font=font("Lora-Italic-Variable.ttf", 56), fill=CREAM)
f_r = font("Poppins-Bold.ttf", 44)
x0 = 690
d.rounded_rectangle((x0 - 14, 26, W - 22, 122), radius=10, fill=YEL)
d.text((x0 + 6, 38), "OPEN NOW", font=font("Poppins-Bold.ttf", 54), fill=(120, 24, 22))
for i, t in enumerate(("BREAKFAST", "TACOS", "BURGERS", "SANDWICHES")):
    d.text((x0, 138 + i * 38), t, font=font("Poppins-Bold.ttf", 34), fill=YEL)
d.text((x0, 318), "MON - SUN", font=f_r, fill=CREAM)
d.text((x0, 366), "6 AM - 2 AM", font=f_r, fill=YEL)
d.text((x0, 430), "1-999-LONGPIG", font=font("Poppins-BoldItalic.ttf", 34), fill=CREAM)
a = np.asarray(img, float)
# ageing: large fade, speckle, cracks, streaks, edge grime
a *= (0.80 + 0.28 * noise(H, W, 90, 1))[..., None]
a = a * 0.90 + 0.10 * 150
sp = noise(H, W, 3, 2)
a[sp > 0.80] = a[sp > 0.80] * 0.72 + 55
r = np.random.default_rng(5)
cr = Image.new("L", (W, H), 0)
cd = ImageDraw.Draw(cr)
for _ in range(90):
    x, y = r.uniform(0, W), r.uniform(0, H)
    ang = r.uniform(0, 2 * math.pi)
    pts = [(x, y)]
    for _ in range(int(r.uniform(4, 14))):
        ang += r.normal(0, 0.6)
        x += math.cos(ang) * r.uniform(6, 22)
        y += math.sin(ang) * r.uniform(6, 22)
        pts.append((x, y))
    cd.line(pts, fill=int(r.uniform(90, 200)), width=1)
c = np.asarray(cr, float) / 255.0
a = a * (1 - 0.55 * c[..., None]) + 30 * c[..., None]
st = noise(H, W // 8, 40, 7).repeat(8, axis=1)[:, :W]
a *= (0.90 + 0.14 * st)[..., None]
yy, xx = np.mgrid[0:H, 0:W]
edge = np.minimum.reduce([xx, W - 1 - xx, yy, H - 1 - yy]) / 26.0
a *= np.clip(0.55 + 0.45 * edge, 0, 1)[..., None]
img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
img.save(OUT / "lp_billboard.png")
data = gs_dds.encode_dds(img, "DXT1")
(OUT / "lp_billboard.dds").write_bytes(data)
rep["lp_billboard"] = {"size": [W, H], "format": "DXT1", "sha256": hashlib.sha256(data).hexdigest(), "origin": "own procedural (Pillow / numpy), fonts Poppins + Lora (OFL)"}

# ------------------------------------------------------------------ price board into the lp8 atlas (region open_neon)
AT = ROOT / "source" / "textures" / "v029" / "lp8_atlas.png"
atlas = Image.open(AT).convert("RGB")
w, h = 320, 128
b = Image.new("RGB", (w, h), (20, 24, 22))
bd = ImageDraw.Draw(b)
bd.rectangle((3, 3, w - 4, h - 4), outline=(200, 170, 90), width=2)
bd.text((12, 6), "TODAY", font=font("Poppins-Bold.ttf", 24), fill=(240, 200, 70))
bd.text((118, 12), "LONG PIG PRICES", font=font("Poppins-Medium.ttf", 15), fill=(200, 196, 180))
rows = (("HERO + SODA", "4.99"), ("TACOS  x2", "3.25"), ("BURGER", "2.75"), ("COFFEE", ".75"))
fr = font("Poppins-Bold.ttf", 19)
for i, (n, p) in enumerate(rows):
    y = 38 + i * 21
    bd.text((14, y), n, font=fr, fill=(236, 230, 214))
    tw = bd.textlength(p, font=fr)
    bd.text((w - 14 - tw, y), p, font=fr, fill=(255, 120, 90))
    bd.line((14 + bd.textlength(n, font=fr) + 6, y + 19, w - 20 - tw, y + 19), fill=(90, 96, 90), width=1)
ba = np.asarray(b, float) * (0.86 + 0.2 * noise(h, w, 30, 9))[..., None]
atlas.paste(Image.fromarray(np.clip(ba, 0, 255).astype(np.uint8)), (0, 0))
atlas.save(AT)
data = gs_dds.encode_dds(atlas, "DXT1")
(AT.with_suffix(".dds")).write_bytes(data)
rep["lp8_atlas"] = {"size": list(atlas.size), "format": "DXT1", "sha256": hashlib.sha256(data).hexdigest(), "changed_region": "open_neon -> price board (own)"}
json.dump(rep, open(OUT / "v031_textures_report.json", "w"), indent=1)
print(json.dumps(rep, indent=1))
