# LONG PIG 2.0.0 sign atlas (own artwork, PIL): cooler headers, ATM / HOT FOOD / COFFEE, deals banner, posters. No real brands.
import json, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F = "/usr/share/fonts/truetype/google-fonts/Poppins-%s.ttf"
def font(sz, w="Bold"): return ImageFont.truetype(F % w, sz)
W, H = 2048, 1024
at = Image.new("RGB", (W, H), (30, 30, 30)); REG = {}
def grad(w, h, c0, c1):
    im = Image.new("RGB", (w, h)); px = im.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        c = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
        for x in range(w): px[x, y] = c
    return im
def fit(d, text, box_w, box_h, w="Bold", start=200):
    sz = start
    while sz > 8:
        f = font(sz, w); b = d.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= box_w and b[3] - b[1] <= box_h: return f, b
        sz -= 2
    return font(8, w), d.textbbox((0, 0), text, font=font(8, w))
def ctext(d, box, text, fill, w="Bold", pad=0.1, shadow=None, start=200):
    x0, y0, x1, y1 = box; bw, bh = (x1 - x0) * (1 - 2 * pad), (y1 - y0) * (1 - 2 * pad)
    f, b = fit(d, text, bw, bh, w, start)
    x = x0 + ((x1 - x0) - (b[2] - b[0])) / 2 - b[0]; y = y0 + ((y1 - y0) - (b[3] - b[1])) / 2 - b[1]
    if shadow: d.text((x + 3, y + 4), text, font=f, fill=shadow)
    d.text((x, y), text, font=f, fill=fill)
def ice(im, seed, n=60):
    rnd = random.Random(seed); d = ImageDraw.Draw(im, "RGBA"); w, h = im.size
    for _ in range(n):
        x, y, r = rnd.randrange(w), rnd.randrange(h), rnd.randrange(6, 40)
        d.polygon([(x, y - r), (x + r * 0.8, y - r * 0.2), (x + r * 0.5, y + r), (x - r * 0.6, y + r * 0.7), (x - r, y - r * 0.1)], fill=(255, 255, 255, rnd.randrange(14, 46)))
def header(name, box, top, sub, c0, c1, accent, seed):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    im = grad(w, h, c0, c1); ice(im, seed); d = ImageDraw.Draw(im)
    d.rectangle([0, h - 34, w, h], fill=accent)
    ctext(d, (0, 6, w, h - 60 if sub else h - 30), top, (255, 255, 255), shadow=(0, 40, 60), pad=0.06)
    if sub: ctext(d, (0, h - 34, w, h), sub, (255, 255, 255), "Medium", pad=0.12, start=40)
    at.paste(im, (x0, y0)); REG[name] = box
header("ice_cold", (0, 0, 768, 256), "ICE COLD", "REFRESCOS  ·  BEBIDAS FRÍAS", (24, 150, 190), (8, 86, 140), (214, 48, 44), 1)
header("cold_beer", (768, 0, 1536, 256), "COLD BEER", "TAP INTO A COOL ONE", (18, 128, 120), (6, 70, 78), (236, 176, 32), 2)
header("drinks", (0, 256, 768, 512), "DRINKS", "SODA  ·  ENERGY  ·  TEA", (40, 110, 200), (16, 52, 130), (20, 170, 190), 3)
header("water", (768, 256, 1536, 512), "WATER + JUICE", "STAY HYDRATED, LOS SANTOS", (60, 170, 215), (18, 104, 170), (255, 255, 255), 4)
header("dairy", (0, 512, 768, 768), "DAIRY & SNACKS", "GRAB · GO", (236, 236, 228), (196, 204, 204), (24, 130, 140), 5)
header("deals_cold", (768, 512, 1536, 768), "2 FOR $3", "MIX & MATCH ANY COLD DRINK", (214, 48, 44), (150, 24, 30), (236, 176, 32), 6)
d = ImageDraw.Draw(at)
# dairy header has light bg: redraw text dark
x0, y0, x1, y1 = REG["dairy"]; im = grad(768, 256, (236, 236, 228), (200, 208, 208)); dd = ImageDraw.Draw(im); dd.rectangle([0, 222, 768, 256], fill=(24, 130, 140))
ctext(dd, (0, 6, 768, 196), "DAIRY & SNACKS", (24, 110, 124), pad=0.06); ctext(dd, (0, 222, 768, 256), "GRAB  ·  GO", (255, 255, 255), "Medium", pad=0.12, start=40); at.paste(im, (x0, y0))
def plate(name, box, text, bg, fg, sub=None, border=None):
    x0, y0, x1, y1 = box; d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=bg)
    if border: d.rectangle([x0 + 6, y0 + 6, x1 - 7, y1 - 7], outline=border, width=4)
    if sub:
        ctext(d, (x0, y0, x1, y0 + (y1 - y0) * 0.68), text, fg, pad=0.08); ctext(d, (x0, y0 + (y1 - y0) * 0.62, x1, y1), sub, fg, "Medium", pad=0.14, start=60)
    else: ctext(d, box, text, fg, pad=0.1)
    REG[name] = box
plate("atm", (1536, 0, 2048, 170), "ATM", (14, 60, 150), (255, 255, 255), border=(255, 255, 255))
plate("hot_food", (1536, 170, 2048, 340), "HOT FOOD", (206, 52, 36), (255, 236, 170), sub="COMIDA PARA LLEVAR")
plate("coffee", (1536, 340, 2048, 510), "FRESH COFFEE", (70, 44, 30), (246, 226, 190), sub="BREWED ALL DAY  ·  99¢ REFILL")
plate("deals", (1536, 510, 2048, 766), "DEALS", (24, 130, 140), (255, 255, 255), sub="ON THE GO!")
plate("p_2for1", (0, 768, 256, 1024), "2 FOR 1", (236, 176, 32), (120, 20, 20), sub="CHIPS & DIPS", border=(120, 20, 20))
plate("p_smile", (256, 768, 512, 1024), "SMILE", (240, 196, 40), (30, 30, 30), sub="YOU'RE ON CAMERA", border=(30, 30, 30))
plate("p_noid", (512, 768, 768, 1024), "NO I.D.", (250, 250, 244), (190, 30, 30), sub="NO SALE!", border=(190, 30, 30))
plate("p_lotto", (768, 768, 1024, 1024), "LOTTO", (250, 132, 20), (255, 255, 255), sub="SCRATCH & WIN HERE", border=(255, 240, 120))
plate("welcome", (1024, 768, 2048, 896), "WELCOME TO  LONG PIG MARKET", (24, 130, 140), (255, 255, 255))
plate("cashier", (1024, 896, 1536, 1024), "PAY HERE", (250, 250, 244), (24, 110, 124), border=(24, 130, 140))
plate("staff", (1536, 896, 2048, 1024), "STAFF ONLY", (40, 40, 44), (255, 255, 255), border=(255, 255, 255))
at.save("lp20_signs.png"); json.dump({k: list(v) for k, v in REG.items()}, open("lp20_signs_regions.json", "w"), indent=0); print(len(REG))
