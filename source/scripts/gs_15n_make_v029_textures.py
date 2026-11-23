# LONG PIG v0.2.9 (premium final pass) — ORIGINAL procedural atlas for the new details and interactive features:
# OPEN neon / CLOSED card (After Hours), door plaques, kitchen order tickets, wash-hands sign, office ledgers, stock carton
# labels, receipt printer face, envelope, cigar box, sepia photo, safe dial, switch label, pass label, fryer panel.
# numpy / PIL only (text rasterised from the DejaVu fonts, Bitstream Vera licence). No third-party or Rockstar pixels.
#   python gs_15n_make_v029_textures.py [<project_root>]  -> source/textures/v029/lp8_atlas.dds (+ regions json, report)
import sys, json, hashlib, math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds  # noqa: E402

OUT = ROOT / "source" / "textures" / "v029"
OUT.mkdir(parents=True, exist_ok=True)
FONT = Path("/usr/share/fonts/truetype/dejavu")
REPORT = {"script": "source/scripts/gs_15n_make_v029_textures.py", "version": "0.2.9-premium", "textures": []}
rng = np.random.default_rng(20261102 + 929)
W, H = 1024, 512

REG = {
    "open_neon": (0, 0, 320, 128), "closed": (320, 0, 576, 128), "open_card": (576, 0, 832, 128),
    "staff_only": (832, 0, 1024, 64), "restroom": (832, 64, 1024, 128),
    "ticket1": (0, 128, 96, 320), "ticket2": (96, 128, 192, 320), "ticket3": (192, 128, 288, 320),
    "wash_hands": (288, 128, 480, 256), "ledger1": (480, 128, 640, 256), "ledger2": (640, 128, 800, 256),
    "pages": (800, 128, 1024, 256),
    "carton_cups": (288, 256, 480, 384), "carton_napkins": (480, 256, 672, 384), "carton_togo": (672, 256, 864, 384),
    "carton_foil": (864, 256, 1024, 384),
    "printer": (0, 320, 128, 384), "envelope": (128, 320, 288, 416), "kraft": (0, 384, 128, 512),
    "cigar": (288, 384, 480, 480), "photo": (480, 384, 608, 512), "dial": (608, 384, 704, 480),
    "switch_label": (704, 384, 768, 448), "pass_label": (768, 384, 1024, 448), "fryer_panel": (768, 448, 1024, 512),
    "black": (704, 448, 736, 480), "brass": (736, 448, 768, 480), "steel_dark": (128, 416, 160, 448),
    "paper": (160, 416, 192, 448), "cardboard": (192, 416, 288, 512), "felt_green": (608, 480, 704, 512),
}


def font(name, size):
    return ImageFont.truetype(str(FONT / name), size)


def noise(h, w, scale, seed):
    r = np.random.default_rng(seed)
    a = r.random((max(2, h // scale + 2), max(2, w // scale + 2)))
    img = Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(img, float) / 255.0


atlas = Image.new("RGB", (W, H), (128, 128, 128))
D = ImageDraw.Draw(atlas)


def box(key):
    return REG[key]


def fill(key, col, grain=0.06, seed=1):
    x0, y0, x1, y1 = box(key)
    w, h = x1 - x0, y1 - y0
    n = noise(h, w, 8, seed) - 0.5
    a = np.zeros((h, w, 3))
    for i in range(3):
        a[:, :, i] = col[i] / 255.0 + n * grain
    atlas.paste(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)), (x0, y0))


def text_c(key, txt, f, col, cy=None, dx=0):
    x0, y0, x1, y1 = box(key)
    tw = D.textlength(txt, font=f)
    bb = f.getbbox(txt)
    th = bb[3] - bb[1]
    cy = (y0 + y1) / 2 if cy is None else y0 + cy
    D.text(((x0 + x1) / 2 - tw / 2 + dx, cy - th / 2 - bb[1]), txt, font=f, fill=col)


def age(key, amount=0.10, seed=3, yellow=0.0):
    """Multiply grime + slight yellowing over a region."""
    x0, y0, x1, y1 = box(key)
    reg = np.asarray(atlas.crop((x0, y0, x1, y1)), float) / 255.0
    h, w = reg.shape[:2]
    n = noise(h, w, 16, seed)
    m = 1.0 - amount * n[:, :, None]
    reg = reg * m
    if yellow:
        reg[:, :, 2] *= (1.0 - yellow)
        reg[:, :, 1] *= (1.0 - yellow * 0.35)
    atlas.paste(Image.fromarray((np.clip(reg, 0, 1) * 255).astype(np.uint8)), (x0, y0))


# ---------------------------------------------------------------- OPEN neon (emissive): black panel, red tubes, blue frame
x0, y0, x1, y1 = box("open_neon")
neon = Image.new("RGB", (x1 - x0, y1 - y0), (6, 6, 8))
nd = ImageDraw.Draw(neon)
glow = Image.new("RGB", neon.size, (0, 0, 0))
gd = ImageDraw.Draw(glow)
for d_, col, wdt in ((gd, (40, 70, 255), 9), (nd, (150, 190, 255), 3)):
    d_.rounded_rectangle((10, 10, neon.size[0] - 10, neon.size[1] - 10), radius=22, outline=col, width=wdt)
fo = font("DejaVuSans-Bold.ttf", 74)
for d_, col, sw in ((gd, (255, 40, 30), 5), (nd, (255, 215, 200), 0)):
    tw = d_.textlength("OPEN", font=fo)
    d_.text((neon.size[0] / 2 - tw / 2, 18), "OPEN", font=fo, fill=col, stroke_width=sw, stroke_fill=col)
glow = glow.filter(ImageFilter.GaussianBlur(7))
neon = Image.fromarray(np.clip(np.asarray(neon, int) + np.asarray(glow, int), 0, 255).astype(np.uint8))
atlas.paste(neon, (x0, y0))

# ---------------------------------------------------------------- CLOSED hanging card / OPEN card (back side)
for key, l1, l2, col in (("closed", "SORRY", "WE'RE CLOSED", (170, 25, 25)), ("open_card", "COME IN", "WE'RE OPEN", (25, 110, 45))):
    fill(key, (236, 230, 214), 0.04, seed=11)
    x0, y0, x1, y1 = box(key)
    D.rectangle((x0 + 6, y0 + 6, x1 - 7, y1 - 7), outline=(40, 40, 40), width=3)
    text_c(key, l1, font("DejaVuSans-Bold.ttf", 30), (30, 30, 30), cy=38)
    text_c(key, l2, font("DejaVuSans-Bold.ttf", 25), col, cy=84)
    D.ellipse(((x0 + x1) / 2 - 5, y0 + 10, (x0 + x1) / 2 + 5, y0 + 20), fill=(90, 90, 90))
    age(key, 0.12, seed=12, yellow=0.06)

# ---------------------------------------------------------------- door plaques (engraved brass / black)
fill("staff_only", (22, 22, 22), 0.03, seed=21)
D.rectangle(tuple(np.add(box("staff_only"), (3, 3, -4, -4))), outline=(170, 140, 70), width=2)
text_c("staff_only", "EMPLOYEES ONLY", font("DejaVuSans-Bold.ttf", 19), (200, 170, 95))
fill("restroom", (176, 140, 62), 0.05, seed=22)
D.rectangle(tuple(np.add(box("restroom"), (3, 3, -4, -4))), outline=(90, 66, 22), width=2)
text_c("restroom", "RESTROOM", font("DejaVuSerif-Bold.ttf", 22), (40, 28, 10), cy=22)
text_c("restroom", "EMPLOYEES", font("DejaVuSans-Bold.ttf", 13), (40, 28, 10), cy=46)
age("restroom", 0.18, seed=23)

# ---------------------------------------------------------------- kitchen order tickets (thermal-ish paper, handwriting-like)
orders = [["T-4  #117", "2 ITAL SUB", " - no onion", "1 MEATBALL", "1 CHIPS", "11:42"],
          ["TOGO #118", "1 CAPICOLA", "1 PROV HERO", " - xtra pep", "2 SODA", "11:46"],
          ["T-2  #119", "3 SLICE", "1 SAUSAGE", " PEPPERS", "1 CANNOLI", "11:51"]]
fm = font("DejaVuSansMono-Bold.ttf", 11)
for k, lines in enumerate(orders, 1):
    key = f"ticket{k}"
    fill(key, (241, 238, 228), 0.03, seed=30 + k)
    x0, y0, x1, y1 = box(key)
    D.text((x0 + 8, y0 + 8), "LONG PIG", font=font("DejaVuSans-Bold.ttf", 12), fill=(30, 30, 30))
    D.line((x0 + 6, y0 + 26, x1 - 6, y0 + 26), fill=(80, 80, 80), width=1)
    for i, ln in enumerate(lines):
        D.text((x0 + 7, y0 + 34 + i * 22), ln, font=fm, fill=(40, 40, 52) if i else (150, 20, 20))
    for yy in range(y0 + 2, y1, 9):                                    # torn edge at the bottom / top
        D.point((x0 + int(rng.integers(0, x1 - x0)), y1 - 2), fill=(200, 200, 190))
    age(key, 0.10, seed=40 + k, yellow=0.04)

# ---------------------------------------------------------------- wash hands sign
fill("wash_hands", (245, 245, 240), 0.03, seed=50)
x0, y0, x1, y1 = box("wash_hands")
D.rectangle((x0 + 5, y0 + 5, x1 - 6, y1 - 6), outline=(20, 70, 150), width=4)
text_c("wash_hands", "EMPLOYEES", font("DejaVuSans-Bold.ttf", 22), (20, 70, 150), cy=32)
text_c("wash_hands", "MUST WASH", font("DejaVuSans-Bold.ttf", 26), (20, 20, 20), cy=64)
text_c("wash_hands", "HANDS", font("DejaVuSans-Bold.ttf", 30), (20, 20, 20), cy=96)
age("wash_hands", 0.14, seed=51, yellow=0.08)

# ---------------------------------------------------------------- ledgers (cloth covers with a paper label) + page block
for key, col, title, year in (("ledger1", (34, 62, 44), "LEDGER", "1993 - 1995"), ("ledger2", (96, 26, 30), "ACCOUNTS", "1997")):
    fill(key, col, 0.12, seed=60 + len(title))
    x0, y0, x1, y1 = box(key)
    lx0, ly0, lx1, ly1 = x0 + 22, y0 + 34, x1 - 22, y0 + 94
    D.rectangle((lx0, ly0, lx1, ly1), fill=(222, 210, 180), outline=(60, 50, 30))
    D.text((lx0 + 8, ly0 + 8), title, font=font("DejaVuSerif-Bold.ttf", 15), fill=(30, 25, 20))
    D.text((lx0 + 8, ly0 + 32), year, font=font("DejaVuSerif.ttf", 13), fill=(30, 25, 20))
    age(key, 0.22, seed=70 + len(title))
fill("pages", (226, 214, 184), 0.04, seed=80)
x0, y0, x1, y1 = box("pages")
for yy in range(y0 + 2, y1, 3):
    D.line((x0, yy, x1, yy), fill=(196, 182, 150) if (yy // 3) % 2 else (232, 222, 196), width=1)
age("pages", 0.15, seed=81)

# ---------------------------------------------------------------- stock cartons (kraft + printed label)
fill("cardboard", (170, 128, 82), 0.10, seed=90)
for key, l1, l2 in (("carton_cups", "HOT CUPS", "16 OZ  1000 CT"), ("carton_napkins", "NAPKINS", "2-PLY  6000 CT"),
                    ("carton_togo", "TO-GO", "CONTAINERS 250"), ("carton_foil", "FOIL", "SHEETS 12x14")):
    fill(key, (168, 126, 80), 0.10, seed=91 + len(key))
    x0, y0, x1, y1 = box(key)
    D.rectangle((x0 + 4, y0 + 4, x1 - 5, y1 - 5), outline=(120, 86, 50), width=2)
    text_c(key, l1, font("DejaVuSans-Bold.ttf", 22 if len(l1) < 8 else 18), (30, 30, 34), cy=48)
    text_c(key, l2, font("DejaVuSans.ttf", 13), (30, 30, 34), cy=80)
    D.line((x0 + 10, y0 + 102, x1 - 10, y0 + 102), fill=(110, 80, 46), width=6)       # tape
    age(key, 0.20, seed=95 + len(key))
fill("kraft", (160, 120, 78), 0.10, seed=96)

# ---------------------------------------------------------------- receipt printer face, envelope, cigar box, photo, dial
fill("printer", (205, 196, 176), 0.05, seed=100)
x0, y0, x1, y1 = box("printer")
D.rectangle((x0 + 14, y0 + 14, x1 - 14, y0 + 22), fill=(30, 30, 30))                       # paper slot
D.rectangle((x0 + 20, y0 + 36, x0 + 44, y0 + 50), fill=(60, 140, 60))                      # feed button
D.ellipse((x1 - 30, y0 + 38, x1 - 22, y0 + 46), fill=(40, 200, 60))                        # power LED
D.text((x0 + 52, y0 + 38), "TM-200", font=font("DejaVuSans.ttf", 10), fill=(60, 60, 60))
age("printer", 0.18, seed=101, yellow=0.05)
fill("envelope", (190, 150, 96), 0.08, seed=110)
x0, y0, x1, y1 = box("envelope")
D.line((x0, y0, (x0 + x1) // 2, y0 + 50), fill=(150, 112, 70), width=2)
D.line((x1, y0, (x0 + x1) // 2, y0 + 50), fill=(150, 112, 70), width=2)
D.text((x0 + 18, y0 + 62), "J.  -  WEDS", font=font("DejaVuSans.ttf", 15), fill=(40, 30, 60))
age("envelope", 0.18, seed=111)
fill("cigar", (120, 62, 30), 0.12, seed=120)
x0, y0, x1, y1 = box("cigar")
D.rectangle((x0 + 30, y0 + 18, x1 - 30, y1 - 18), fill=(214, 182, 96), outline=(120, 20, 20), width=3)
text_c("cigar", "PALERMO", font("DejaVuSerif-Bold.ttf", 22), (120, 20, 20), cy=38)
text_c("cigar", "HAND ROLLED", font("DejaVuSerif.ttf", 11), (60, 30, 10), cy=62)
age("cigar", 0.2, seed=121)
x0, y0, x1, y1 = box("photo")                                                               # sepia snapshot (own drawing)
ph = Image.new("RGB", (x1 - x0, y1 - y0), (226, 214, 190))
pd = ImageDraw.Draw(ph)
pd.rectangle((8, 8, ph.size[0] - 9, ph.size[1] - 26), fill=(142, 112, 80))
pd.rectangle((8, 70, ph.size[0] - 9, ph.size[1] - 26), fill=(104, 80, 58))                  # counter
for k, (cx, hh) in enumerate(((34, 40), (62, 46), (92, 38))):                                  # three figures
    pd.ellipse((cx - 8, 70 - hh, cx + 8, 70 - hh + 16), fill=(70, 52, 36))
    pd.rectangle((cx - 12, 70 - hh + 16, cx + 12, 92), fill=(60, 44, 30) if k != 1 else (230, 222, 205))
pd.text((12, ph.size[1] - 22), "'71 opening", font=font("DejaVuSerif-Italic.ttf", 12), fill=(70, 50, 30))
ph = ph.filter(ImageFilter.GaussianBlur(0.8))
atlas.paste(ph, (x0, y0))
age("photo", 0.25, seed=131, yellow=0.1)
fill("dial", (30, 30, 30), 0.04, seed=140)
x0, y0, x1, y1 = box("dial")
cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, 40
D.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(150, 150, 150), outline=(220, 220, 220), width=3)
for k in range(40):
    a = 2 * math.pi * k / 40
    r0 = r - (9 if k % 5 == 0 else 5)
    D.line((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + (r - 2) * math.cos(a), cy + (r - 2) * math.sin(a)), fill=(20, 20, 20), width=2)
D.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(60, 60, 60))
fill("switch_label", (238, 232, 216), 0.03, seed=150)
text_c("switch_label", "HALL", font("DejaVuSans-Bold.ttf", 14), (30, 30, 30), cy=20)
text_c("switch_label", "LIGHTS", font("DejaVuSans-Bold.ttf", 12), (30, 30, 30), cy=42)
age("switch_label", 0.15, seed=151, yellow=0.08)
fill("pass_label", (20, 20, 20), 0.03, seed=160)
text_c("pass_label", "ORDERS  -  PASS", font("DejaVuSans-Bold.ttf", 24), (230, 200, 60))
fill("fryer_panel", (150, 150, 152), 0.05, seed=170)
x0, y0, x1, y1 = box("fryer_panel")
for k in range(2):
    cx = x0 + 60 + k * 136
    D.ellipse((cx - 18, y0 + 14, cx + 18, y0 + 50), fill=(25, 25, 25))
    D.text((cx - 22, y0 + 50), f"VAT {k + 1}", font=font("DejaVuSans-Bold.ttf", 10), fill=(20, 20, 20))
age("fryer_panel", 0.25, seed=171)
fill("black", (16, 16, 16), 0.02, seed=180)
fill("brass", (176, 138, 64), 0.08, seed=181)
fill("steel_dark", (70, 72, 74), 0.06, seed=182)
fill("paper", (236, 232, 220), 0.03, seed=183)
fill("felt_green", (44, 78, 58), 0.10, seed=184)

atlas.save(OUT / "lp8_atlas.png")
gs_dds.convert(OUT / "lp8_atlas.png", OUT / "lp8_atlas.dds", "DXT1")
data = (OUT / "lp8_atlas.dds").read_bytes()
REPORT["textures"].append({"name": "lp8_atlas", "file": "lp8_atlas.dds", "size": [W, H], "format": "DXT1", "role": "diffuse/emissive",
                           "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "derived_from": [],
                           "origin": "original_procedural", "operations": "PIL drawing, DejaVu text, procedural noise"})
(OUT / "lp8_atlas_regions.json").write_text(json.dumps({"size": [W, H], "regions": REG}, indent=1))
(OUT / "lp8_textures_report.json").write_text(json.dumps(REPORT, indent=1))
print("TEX lp8_atlas", len(data))
