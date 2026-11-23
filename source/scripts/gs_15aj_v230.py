# LONG PIG 2.3.0 textures: palette of the shop's own sign / menu boards (brick red, cream, mustard yellow, dark brown)
# and worn South-LA finishes. CC0 photo sets from ambientCG (same zips as 2.0.0, source/textures/v200/src, SHA-256 in the
# report), graded and aged in code; own sign atlases (PIL, own artwork, no real brands).
import sys, json, hashlib, io, zipfile, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
SRC = ROOT / "source" / "textures" / "v200" / "src"
OUT = ROOT / "source" / "textures" / "v230"; OUT.mkdir(exist_ok=True)
RED, DRED, CREAM, YEL, BROWN = (164, 50, 38), (112, 32, 26), (228, 212, 178), (230, 172, 40), (56, 38, 30)
rep = {"palette": {"red": RED, "deep_red": DRED, "cream": CREAM, "yellow": YEL, "brown": BROWN}, "sources": {}, "files": {}}


def cc(aid, kind, n=1024):
    zp = SRC / f"{aid}_1K-JPG.zip"; data = zp.read_bytes()
    rep["sources"][aid] = {"url": "https://ambientcg.com/a/" + aid, "file": zp.name, "licence": "CC0 1.0", "sha256": hashlib.sha256(data).hexdigest()}
    z = zipfile.ZipFile(io.BytesIO(data)); nm = [x for x in z.namelist() if x.endswith(f"_{kind}.jpg")][0]
    return np.asarray(Image.open(io.BytesIO(z.read(nm))).convert("RGB").resize((n, n), Image.LANCZOS), float) / 255.0


def save(name, a, fmt="DXT1", src=None):
    im = a if isinstance(a, Image.Image) else Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + 0.5))
    data = gs_dds.encode_dds(im, fmt); (OUT / f"{name}.dds").write_bytes(data)
    rep["files"][name] = {"size": list(im.size), "format": fmt, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "from": src or "own procedural"}


def lum(a): return a @ np.array([0.299, 0.587, 0.114])


def tone(c, rgb, k=1.0):
    L = lum(c); d = (L / max(L.mean(), 1e-6) - 1.0) * k + 1.0
    return np.clip(d[..., None] * (np.array(rgb, float) / 255.0), 0, 1)


def spec(r, lo, hi):
    s = 1 - r.mean(-1); s = lo + (hi - lo) * (s - s.min()) / (np.ptp(s) + 1e-9); return np.repeat(s[..., None], 3, -1)


def noise(n, seed, blur):
    m = max(2, int(round(n / (blur * 2.5))))                                               # float value noise, tileable
    g = np.random.default_rng(seed).random((m, m)).astype(np.float32)
    im = Image.fromarray(np.tile(g, (3, 3)), "F").resize((3 * n, 3 * n), Image.BICUBIC)
    a = np.asarray(im, float)[n:2 * n, n:2 * n]
    return (a - a.min()) / (np.ptp(a) + 1e-9)


def blobs(n, seed, blur, thr):
    return np.clip((noise(n, seed, blur) - thr) / max(1e-6, 0.06), 0, 1)


def streaks(n, seed, cnt, horiz=True, lmax=0.35):
    im = Image.new("L", (n, n), 0); d = ImageDraw.Draw(im); r = random.Random(seed)
    for _ in range(cnt):
        x, y, L = r.randrange(n), r.randrange(n), int(n * r.uniform(0.04, lmax))
        d.line([(x, y), (x + L, y + r.randrange(-4, 5))] if horiz else [(x, y), (x + r.randrange(-3, 4), y + L)], fill=r.randrange(60, 200), width=r.choice((1, 1, 2, 3)))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(0.8)), float) / 255.0


def aged(name, aid, rgb, n=512, k=1.0, lo=0.05, hi=0.5, grime=0.18, scuff=0.0, chips=None, seed=1):
    c = tone(cc(aid, "Color", n), rgb, k)
    g = noise(n, seed, n / 9.0); f = noise(n, seed + 1, 3.0)
    c *= (1 - grime * g)[..., None] * (0.96 + 0.04 * f)[..., None]
    c = c * (1 - 0.35 * grime * g[..., None] * np.array([0.0, 0.25, 0.6]))                 # grime warms / yellows the paint
    s = spec(cc(aid, "Roughness", n), lo, hi) * (1 - 0.5 * g)[..., None]
    if scuff:
        sc = streaks(n, seed + 2, 90)
        c *= (1 - scuff * sc)[..., None]; s *= (1 - 0.6 * sc)[..., None]
    if chips is not None:                                                                  # paint chipped down to the old coat
        m = blobs(n, seed + 3, 6.0, 0.90)[..., None]
        c = c * (1 - m) + (np.array(chips, float) / 255.0) * (0.85 + 0.15 * f[..., None]) * m; s *= (1 - 0.7 * m)
    save(name, c, src=aid); save(name + "_n", cc(aid, "NormalDX", n), src=aid); save(name + "_s", s, src=aid)


# ---- floor: Tiles107 -> worn cream ceramic, dark soiled grout, traffic soil, a few stained / replaced tiles
c0 = cc("Tiles107", "Color"); nrm = cc("Tiles107", "NormalDX")
joint = np.clip(np.abs(nrm[..., :2] - 0.5).max(-1) * 8, 0, 1)
c = tone(c0, (204, 190, 160), 1.6)
rng = np.random.default_rng(23); t = 128
for i in range(8):
    for j in range(8):
        v = 1.0 + rng.normal(0, 0.035); tint = np.array([1.0, 1.0 - abs(rng.normal(0, 0.012)), 1.0 - abs(rng.normal(0, 0.03))])
        if rng.random() < 0.08:
            v *= 0.88; tint = np.array([1.0, 0.93, 0.82])                                   # replacement tile of another batch
        c[i * t:(i + 1) * t, j * t:(j + 1) * t] *= v * tint
soil = noise(1024, 31, 70); spots = blobs(1024, 32, 9.0, 0.80); fine = noise(1024, 33, 1.5)
c *= (1 - 0.26 * soil)[..., None] * (1 - 0.20 * spots)[..., None] * (0.95 + 0.05 * fine)[..., None]
c *= (1 - 0.40 * joint)[..., None]
c *= (1 - 0.35 * streaks(1024, 34, 60, lmax=0.2))[..., None]
save("lp23_floor", c, src="Tiles107"); save("lp23_floor_n", nrm, src="Tiles107")
save("lp23_floor_s", spec(cc("Tiles107", "Roughness"), 0.18, 0.62) * (1 - 0.6 * joint)[..., None] * (1 - 0.5 * soil)[..., None] * (1 - 0.6 * spots)[..., None], src="Tiles107")
# ---- walls / paint / laminate / metal
aged("lp23_wall", "PaintedPlaster017", (214, 196, 158), k=0.6, lo=0.03, hi=0.16, grime=0.24, seed=40)                 # dirty cream paint
aged("lp23_dado", "PaintedPlaster017", (138, 44, 34), k=0.6, lo=0.05, hi=0.30, grime=0.30, scuff=0.35, chips=(196, 180, 146), seed=50)   # brick-red gloss dado, scuffed
aged("lp23_dark", "PaintedPlaster017", BROWN, n=256, k=0.5, lo=0.05, hi=0.25, grime=0.25, scuff=0.3, seed=60)        # kick plates
aged("lp23_lam", "Plastic010", (212, 178, 104), k=1.2, lo=0.12, hi=0.5, grime=0.22, scuff=0.30, seed=70)             # mustard laminate, worn
aged("lp23_top", "Plastic010", (60, 44, 38), k=1.5, lo=0.15, hi=0.6, grime=0.15, scuff=0.25, seed=80)                # dark brown top
aged("lp23_white", "Plastic010", (222, 208, 178), k=1.0, lo=0.10, hi=0.45, grime=0.22, scuff=0.12, seed=90)          # aged cream enamel
aged("lp23_alu", "Metal009", (140, 138, 130), k=1.0, lo=0.25, hi=0.8, grime=0.25, scuff=0.2, seed=100)               # dull aluminium
# ---- wall band above the openings: red with two mustard pin lines, chipped (v = 0..1 across the height)
n = 512; b = tone(cc("PaintedPlaster017", "Color", n), RED, 0.6)
yl = tone(cc("PaintedPlaster017", "Color", n), YEL, 0.6)
for r0, r1 in ((36, 62), (450, 476)):
    b[r0:r1] = yl[r0:r1]
g = noise(n, 110, 60); m = blobs(n, 111, 6.0, 0.90)[..., None]
b *= (1 - 0.25 * g)[..., None]; b = b * (1 - m) + (np.array((206, 190, 156)) / 255.0) * m
b *= (1 - 0.3 * streaks(n, 112, 50, horiz=False, lmax=0.5))[..., None]                     # runs of dirt
save("lp23_band", b, src="PaintedPlaster017"); save("lp23_band_n", cc("PaintedPlaster017", "NormalDX", n), src="PaintedPlaster017")
save("lp23_band_s", spec(cc("PaintedPlaster017", "Roughness", n), 0.05, 0.3) * (1 - m), src="PaintedPlaster017")

# ---- sign atlas 1 (same regions as lp20_signs), sign palette
FN = "/usr/share/fonts/truetype/google-fonts/Poppins-%s.ttf"
def font(sz, w="Bold"): return ImageFont.truetype(FN % w, sz)
def fit(d, text, bw, bh, w="Bold", start=200):
    sz = start
    while sz > 8:
        f = font(sz, w); bb = d.textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] <= bw and bb[3] - bb[1] <= bh: return f, bb
        sz -= 2
    return font(8, w), d.textbbox((0, 0), text, font=font(8, w))
def ctext(d, box, text, fill, w="Bold", pad=0.1, shadow=None, start=200):
    x0, y0, x1, y1 = box; f, bb = fit(d, text, (x1 - x0) * (1 - 2 * pad), (y1 - y0) * (1 - 2 * pad), w, start)
    x = x0 + ((x1 - x0) - (bb[2] - bb[0])) / 2 - bb[0]; y = y0 + ((y1 - y0) - (bb[3] - bb[1])) / 2 - bb[1]
    if shadow: d.text((x + 3, y + 4), text, font=f, fill=shadow)
    d.text((x, y), text, font=f, fill=fill)
W_, H_ = 2048, 1024
at = Image.new("RGB", (W_, H_), BROWN); d = ImageDraw.Draw(at); REG = {}
def header(name, box, top, sub, bg, fg, bar, barfg):
    x0, y0, x1, y1 = box; d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=bg); d.rectangle([x0, y1 - 40, x1 - 1, y1 - 1], fill=bar)
    d.rectangle([x0 + 8, y0 + 8, x1 - 9, y1 - 49], outline=fg, width=3)
    ctext(d, (x0, y0 + 6, x1, y1 - 46), top, fg, pad=0.08, shadow=tuple(int(v * 0.55) for v in bg))
    ctext(d, (x0, y1 - 40, x1, y1), sub, barfg, "Medium", pad=0.14, start=40); REG[name] = box
header("ice_cold", (0, 0, 768, 256), "ICE COLD", "REFRESCOS  ·  BEBIDAS FRÍAS", RED, CREAM, YEL, DRED)
header("cold_beer", (768, 0, 1536, 256), "COLD BEER", "TAP INTO A COOL ONE", YEL, DRED, DRED, CREAM)
header("drinks", (0, 256, 768, 512), "DRINKS", "SODA  ·  ENERGY  ·  TEA", CREAM, RED, RED, CREAM)
header("water", (768, 256, 1536, 512), "WATER + JUICE", "STAY HYDRATED, LOS SANTOS", RED, CREAM, YEL, DRED)
header("dairy", (0, 512, 768, 768), "DAIRY & SNACKS", "GRAB  ·  GO", CREAM, DRED, YEL, DRED)
header("deals_cold", (768, 512, 1536, 768), "2 FOR $3", "MIX & MATCH ANY COLD DRINK", YEL, RED, RED, CREAM)
def plate(name, box, text, bg, fg, sub=None, border=None, at_=None, reg=None):
    dd = ImageDraw.Draw(at_) if at_ is not None else d
    x0, y0, x1, y1 = box; dd.rectangle([x0, y0, x1 - 1, y1 - 1], fill=bg)
    if border: dd.rectangle([x0 + 6, y0 + 6, x1 - 7, y1 - 7], outline=border, width=4)
    if sub:
        ctext(dd, (x0, y0, x1, y0 + (y1 - y0) * 0.68), text, fg, pad=0.08); ctext(dd, (x0, y0 + (y1 - y0) * 0.62, x1, y1), sub, fg, "Medium", pad=0.14, start=60)
    else: ctext(dd, box, text, fg, pad=0.1)
    (REG if reg is None else reg)[name] = box
plate("atm", (1536, 0, 2048, 170), "ATM", DRED, CREAM, border=YEL)
plate("hot_food", (1536, 170, 2048, 340), "HOT FOOD", RED, CREAM, sub="COMIDA PARA LLEVAR")
plate("coffee", (1536, 340, 2048, 510), "FRESH COFFEE", BROWN, CREAM, sub="BREWED ALL DAY  ·  99¢ REFILL", border=YEL)
plate("deals", (1536, 510, 2048, 766), "DEALS", YEL, DRED, sub="ON THE GO!")
plate("p_2for1", (0, 768, 256, 1024), "2 FOR 1", YEL, DRED, sub="CHIPS & DIPS", border=DRED)
plate("p_smile", (256, 768, 512, 1024), "SMILE", YEL, (30, 24, 20), sub="YOU'RE ON CAMERA", border=(30, 24, 20))
plate("p_noid", (512, 768, 768, 1024), "NO I.D.", CREAM, RED, sub="NO SALE!", border=RED)
plate("p_lotto", (768, 768, 1024, 1024), "LOTTO", RED, CREAM, sub="SCRATCH & WIN HERE", border=YEL)
plate("welcome", (1024, 768, 2048, 896), "WELCOME TO  LONG PIG MARKET", RED, CREAM, border=YEL)
plate("cashier", (1024, 896, 1536, 1024), "PAY HERE", CREAM, RED, border=RED)
plate("staff", (1536, 896, 2048, 1024), "STAFF ONLY", BROWN, CREAM, border=CREAM)
def weather(im, seed, k=0.10):
    a = np.asarray(im, float) / 255.0; nn = max(im.size)
    g = np.asarray(Image.fromarray(np.uint8(noise(1024, seed, 40) * 255)).resize(im.size, Image.BILINEAR), float) / 255.0
    f = np.asarray(Image.fromarray(np.uint8(noise(1024, seed + 1, 1.2) * 255)).resize(im.size, Image.BILINEAR), float) / 255.0
    a = a * (1 - k * g)[..., None] * (0.97 + 0.03 * f)[..., None]
    a = a * 0.94 + 0.06 * np.array([0.80, 0.74, 0.60])                                      # sun fade towards dusty cream
    return Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255))
save("lp23_signs", weather(at, 200), src="own artwork (gs_15aj_v230.py)")
# ---- sign atlas 2: kiosk fascia, lottery tickets, notices, specials (own artwork)
a2 = Image.new("RGB", (1024, 1024), BROWN); d2 = ImageDraw.Draw(a2); REG2 = {}
plate("fascia", (0, 0, 1024, 96), "LOTTO  •  TOBACCO  •  PHONE CARDS  •  CANDY  •  ICE", RED, CREAM, at_=a2, reg=REG2)
x0, y0 = 0, 96; d2.rectangle([0, 96, 511, 607], fill=(236, 228, 208))
TK = (("LUCKY PIG", "$1", RED, CREAM), ("GOLD RUSH", "$2", YEL, DRED), ("TRIPLE 7", "$5", (30, 90, 60), YEL), ("CASH COW", "$1", CREAM, RED),
      ("HOT 5s", "$5", DRED, YEL), ("BIG OINK", "$10", (24, 24, 28), YEL), ("FAT STACKS", "$2", (40, 70, 130), CREAM), ("PIGGY BANK", "$1", (214, 110, 140), (60, 20, 30)),
      ("LOS SANTOS LOOT", "$20", (20, 20, 22), (230, 190, 80)), ("JACKPOT JR", "$1", YEL, (30, 30, 30)), ("RED HOT", "$2", RED, YEL), ("WIN 4 LIFE", "$5", (30, 110, 120), CREAM),
      ("LUCKY PIG", "$1", RED, CREAM), ("BINGO", "$3", (120, 50, 130), YEL), ("CROSSWORD", "$3", CREAM, (30, 30, 30)), ("GOLD RUSH", "$2", YEL, DRED))
for i, (nm, pr, bg, fg) in enumerate(TK):
    cx, cy = (i % 4) * 128, 96 + (i // 4) * 128
    d2.rectangle([cx + 6, cy + 6, cx + 121, cy + 121], fill=bg, outline=(40, 30, 26), width=2)
    ctext(d2, (cx + 8, cy + 10, cx + 120, cy + 62), nm, fg, pad=0.06, start=40)
    d2.ellipse([cx + 40, cy + 62, cx + 88, cy + 110], fill=fg); ctext(d2, (cx + 40, cy + 62, cx + 88, cy + 110), pr, bg, pad=0.16, start=40)
    d2.rectangle([cx + 92, cy + 96, cx + 118, cy + 116], fill=(250, 250, 244)); ctext(d2, (cx + 92, cy + 96, cx + 118, cy + 116), "%02d" % (i + 1), (20, 20, 20), pad=0.1, start=20)
REG2["lotto_rack"] = (0, 96, 512, 608)
plate("open24", (512, 96, 1024, 352), "OPEN 24 HRS", YEL, RED, sub="ABIERTO  ·  7 DAYS", border=RED, at_=a2, reg=REG2)
plate("cashonly", (512, 352, 768, 608), "CASH ONLY", CREAM, (30, 24, 20), sub="UNDER $5", border=(30, 24, 20), at_=a2, reg=REG2)
plate("noloit", (768, 352, 1024, 608), "NO", CREAM, RED, sub="LOITERING", border=RED, at_=a2, reg=REG2)
plate("phone", (0, 608, 512, 864), "PHONE CARDS", RED, CREAM, sub="MONEY ORDERS  ·  BILL PAY", border=YEL, at_=a2, reg=REG2)
plate("ice", (512, 608, 1024, 864), "ICE", CREAM, RED, sub="$2.49 BAG  ·  ASK CASHIER", border=RED, at_=a2, reg=REG2)
plate("specials", (0, 864, 1024, 1024), "CHOPPED CHEESE $6.50  ·  BACON EGG & CHEESE $4.25", YEL, DRED, sub="COFFEE $1  ·  2 TACOS $5  ·  LOOSIES? DON'T ASK", border=DRED, at_=a2, reg=REG2)
save("lp23_signs2", weather(a2, 210, 0.14), src="own artwork (gs_15aj_v230.py)")
(OUT / "lp23_signs2_regions.json").write_text(json.dumps({k: list(v) for k, v in REG2.items()}))
at.save(OUT / "lp23_signs_preview.png"); a2.save(OUT / "lp23_signs2_preview.png")
(OUT / "v230_textures_report.json").write_text(json.dumps(rep, indent=1)); print(len(rep["files"]), sorted(rep["files"]))
