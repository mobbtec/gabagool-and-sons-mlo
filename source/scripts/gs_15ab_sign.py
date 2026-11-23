# LONG PIG 1.4.0: hall sign over the booth window redrawn (owner allowed own drawing, 2026-11-16): worn red board with a
# white pig. Drawn from scratch with Pillow / numpy - NOT cut from any game texture. Goes into lp6_atlas top strip.
import sys, hashlib, json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
W, H, K = 1024, 136, 4
FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FI = "/usr/share/fonts/truetype/lato/Lato-SemiboldItalic.ttf"
def font(p, s): return ImageFont.truetype(p, s * K)
im = Image.new("RGB", (W * K, H * K), (150, 38, 34))
d = ImageDraw.Draw(im)
S = lambda *a: [int(v * K) for v in a]
d.rectangle(S(0, 0, W, H), outline=(60, 18, 16), width=3 * K)
# pig (white, cream outline): body, head, snout, ear, legs, tail
pig, edge = (238, 232, 216), (196, 170, 120)
def blob(draw, col, grow=0):
    g = grow
    draw.ellipse(S(60 - g, 14 - g, 520 + g, 112 + g), fill=col)                      # body
    draw.ellipse(S(455 - g, 30 - g, 585 + g, 108 + g), fill=col)                     # head
    draw.rounded_rectangle(S(560 - g, 62 - g, 612 + g, 96 + g), radius=10 * K, fill=col)   # snout
    draw.polygon(S(498 - g, 40, 520, 10 - g, 548 + g, 44), fill=col)                 # ear
    for x in (110, 170, 400, 455):
        draw.rounded_rectangle(S(x - g, 92, x + 34 + g, 128 + g), radius=5 * K, fill=col)
    draw.arc(S(30 - g, 40 - g, 74 + g, 78 + g), 60, 330, fill=col, width=(7 + g) * K)      # tail
blob(d, edge, 4); blob(d, pig, 0)
d.ellipse(S(548, 52, 556, 60), fill=(60, 40, 36))
d.text(S(108, 12), "LONG", font=font(FB, 50), fill=(52, 92, 168))
d.text(S(292, 12), "PIG", font=font(FB, 50), fill=(190, 44, 40))
d.text(S(110, 66), "MINI MARKET", font=font(FB, 24), fill=(190, 44, 40))
d.text(S(330, 68), "& deli", font=font(FI, 22), fill=(52, 92, 168))
for i, t in enumerate(("HEROES · SALUMI", "HOT FOOD · COLD BEER", "SINCE 1979")):
    d.text(S(650, 14 + i * 38), t, font=font(FB, 25), fill=(236, 196, 70))
a = np.asarray(im.resize((W, H), Image.LANCZOS), float)
rng = np.random.default_rng(1979)
low = np.asarray(Image.fromarray((rng.random((H // 8 + 1, W // 8 + 1)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255.0
fine = rng.random((H, W))
a *= (0.80 + 0.28 * low)[..., None]                                                   # sun fade / grime
chips = (low > 0.80) & (fine > 0.45)                               # flaked paint -> bare board
a[chips] = a[chips] * 0.25 + np.array([120, 104, 86]) * 0.75
cr = Image.new("L", (W, H), 0); dc = ImageDraw.Draw(cr)
for _ in range(26):                                                                   # hairline cracks
    x, y = rng.integers(0, W), rng.integers(0, H); pts = [(x, y)]
    for _k in range(rng.integers(4, 12)):
        x += rng.integers(-18, 19); y += rng.integers(-6, 7); pts.append((x, y))
    dc.line(pts, fill=160, width=1)
a *= (1 - np.asarray(cr, float)[..., None] / 255.0 * 0.55)
a[:, :3] *= 0.6; a[:, -3:] *= 0.6; a[:3] *= 0.6; a[-3:] *= 0.6
strip = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
p = ROOT / "source" / "textures" / "v027" / "lp6_atlas.dds"
atlas = Image.open(p).convert("RGBA"); atlas.paste(strip, (0, 0))
fmt = "DXT5" if np.asarray(atlas)[..., 3].min() < 255 else "DXT1"
data = gs_dds.encode_dds(atlas if fmt == "DXT5" else atlas.convert("RGB"), fmt); p.write_bytes(data)
strip.save(ROOT / "source" / "textures" / "v027" / "_sign140_prev.png")
print(fmt, hashlib.sha256(data).hexdigest()[:16])
