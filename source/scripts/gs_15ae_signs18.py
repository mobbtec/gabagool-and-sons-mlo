# LONG PIG 1.8.0 - own drawn sign / price-tag atlas lp18_signs (512x512, DXT1). Pillow only; fonts Poppins / Lato (SIL OFL).
import sys, json, hashlib, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FM = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
K = 4                                                   # supersampling
CREAM, MAROON, INK, GREEN = (232, 222, 196), (104, 26, 30), (38, 30, 28), (38, 84, 58)
def font(p, s): return ImageFont.truetype(p, int(s * K))
REG = {}
im = Image.new("RGB", (512 * K, 512 * K), CREAM)
d = ImageDraw.Draw(im)
def fit(text, path, size, maxw):
    f = font(path, size)
    while d.textlength(text, font=f) > maxw * K and size > 6:
        size -= 1; f = font(path, size)
    return f
def ctext(cx, y, text, f, fill):
    w = d.textlength(text, font=f); d.text((cx * K - w / 2, y * K), text, font=f, fill=fill)
def cell(key, x0, y0, x1, y1, bg=CREAM, border=MAROON, bw=3):
    REG[key] = [x0, y0, x1, y1]
    d.rectangle([x0 * K, y0 * K, x1 * K - 1, y1 * K - 1], fill=bg)
    if border:
        d.rectangle([(x0 + 3) * K, (y0 + 3) * K, (x1 - 3) * K - 1, (y1 - 3) * K - 1], outline=border, width=bw * K)
TAGS = [("salami_fan", "GENOA SALAMI", "7.99"), ("salami_fine", "SOPPRESSATA", "9.49"), ("prosciutto_fold", "PROSCIUTTO", "14.99"),
        ("mortadella", "MORTADELLA", "6.49"), ("salami_logs", "DRY SALAMI", "8.99"), ("cheese_wedges", "PECORINO", "11.99"),
        ("provolone_cut", "PROVOLONE", "6.99"), ("mozzarella", "MOZZARELLA", "5.49"), ("olives_green", "GREEN OLIVES", "4.99"),
        ("olives_black", "BLACK OLIVES", "4.99"), ("peppers", "ROAST PEPPERS", "5.29"), ("ask", "SLICED TO ORDER", "")]
for i, (key, name, price) in enumerate(TAGS):
    x0, y0 = (i % 4) * 128, (i // 4) * 64
    cell("tag_" + key, x0, y0, x0 + 128, y0 + 64, bw=2)
    ctext(x0 + 64, y0 + 9, name, fit(name, FB, 15, 108), MAROON)
    if price:
        ctext(x0 + 64, y0 + 28, "$" + price, font(FB, 21), INK)
        d.text(((x0 + 99) * K, (y0 + 40) * K), "/lb", font=font(FM, 9), fill=INK)
    else:
        ctext(x0 + 64, y0 + 32, "ASK AT THE COUNTER", fit("ASK AT THE COUNTER", FM, 10, 108), INK)
cell("pay", 0, 192, 256, 288, bg=CREAM, border=GREEN)                 # 1.9.0: redrawn (owner), cream enamel plate
d.rectangle([9 * K, 201 * K, 247 * K - 1, 279 * K - 1], outline=GREEN, width=K)
ctext(128, 204, "PAY HERE", font(FB, 40), GREEN); ctext(128, 256, "THANK YOU  ·  CASH ONLY", font(FM, 11), INK)
cell("staff", 256, 192, 512, 288, bg=CREAM, border=MAROON)
ctext(384, 207, "EMPLOYEES", font(FB, 34), MAROON); ctext(384, 247, "ONLY", font(FB, 26), INK)
cell("clock", 0, 288, 96, 384, bg=(226, 220, 200), border=None)             # 1.9.1: face of the broken wall clock
import math as _m
for h in range(12):
    a_ = _m.radians(h * 30); r0 = 38 if h % 3 else 33
    d.line([((48 + r0 * _m.sin(a_)) * K, (336 - r0 * _m.cos(a_)) * K), ((48 + 43 * _m.sin(a_)) * K, (336 - 43 * _m.cos(a_)) * K)], fill=INK, width=(3 if h % 3 == 0 else 1) * K)
for txt, (cx, cy) in (("12", (48, 301)), ("3", (77, 329)), ("6", (48, 357)), ("9", (19, 329))):
    ctext(cx, cy, txt, font(FB, 11), INK)
d.line([(30 * K, 300 * K), (44 * K, 322 * K), (40 * K, 338 * K), (58 * K, 352 * K), (62 * K, 376 * K)], fill=(60, 55, 50), width=K)     # cracks
d.line([(44 * K, 322 * K), (66 * K, 316 * K), (80 * K, 300 * K)], fill=(60, 55, 50), width=K)
cell("wash", 0, 384, 192, 512, bg=(238, 236, 226), border=(30, 70, 120))
ctext(96, 398, "NOTICE", font(FB, 22), (30, 70, 120))
for k, line in enumerate(("EMPLOYEES MUST", "WASH HANDS", "BEFORE RETURNING", "TO WORK")):
    ctext(96, 430 + k * 18, line, font(FB if k == 1 else FM, 15 if k == 1 else 12), INK)
cell("menu", 192, 384, 320, 512, bg=CREAM, border=MAROON)
ctext(256, 394, "LONG PIG", font(FB, 20), MAROON); ctext(256, 418, "DELI COUNTER", font(FM, 10), INK)
for k, (a, b) in enumerate((("HEROES", "6.99"), ("HOT FOOD", "5.49"), ("BREAKFAST", "4.99"), ("COFFEE", "1.50"))):
    y = 438 + k * 16
    d.text((204 * K, y * K), a, font=font(FM, 11), fill=INK)
    w = d.textlength("$" + b, font=font(FB, 11)); d.text((308 * K - w, y * K), "$" + b, font=font(FB, 11), fill=MAROON)
cell("takeout", 320, 384, 512, 512, bg=MAROON, border=CREAM)
ctext(416, 408, "TAKE OUT", font(FB, 30), CREAM); ctext(416, 452, "ORDER AT THE COUNTER", fit("ORDER AT THE COUNTER", FM, 12, 160), CREAM)
im = im.resize((512, 512), Image.LANCZOS)
# age: uneven yellowing + faint speckle (seeded), light blur like old lamination
rng = random.Random(18)
px = im.load()
lo = Image.new("L", (16, 16)); lo.putdata([rng.randint(0, 255) for _ in range(256)]); lo = lo.resize((512, 512), Image.BICUBIC).load()
for y in range(512):
    for x in range(512):
        r, g, b = px[x, y]; a = lo[x, y] / 255.0; n = rng.randint(-5, 5)
        px[x, y] = (max(0, min(255, int(r * (0.90 + 0.08 * a)) + n)), max(0, min(255, int(g * (0.87 + 0.09 * a)) + n)), max(0, min(255, int(b * (0.78 + 0.12 * a)) + n)))
im = im.filter(ImageFilter.GaussianBlur(0.35))
out = ROOT / "source" / "textures" / "v180"
im.save(out / "lp18_signs.png")
data = gs_dds.encode_dds(im, "DXT1"); (out / "lp18_signs.dds").write_bytes(data)
rep = {"name": "lp18_signs", "size": [512, 512], "format": "DXT1", "sha256": hashlib.sha256(data).hexdigest(), "origin": "own procedural (Pillow), script gs_15ae_signs18.py",
       "fonts": "Poppins (SIL OFL 1.1)", "regions": REG}
(out / "lp18_signs.json").write_text(json.dumps(rep, indent=1)); print(rep["sha256"][:12], len(data), len(REG))
