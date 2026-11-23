# LONG PIG — v0.2.4 "red armchair lounge": ORIGINAL procedural rug texture (no third-party pixels).
# 90s lounge rug: charcoal wool field with low-contrast "confetti" (red / teal / mustard / cream), red border band
# with a cream diamond chain, black + cream pin lines. 1024 x 256 (the rug is 5.30 x 1.33 m = 4 : 1), DXT1.
# Appends to source/textures/v023/lp3_textures_report.json; then run gs_15d_register_v023.py.
#   python gs_15f_make_v024_textures.py [<project_root>]
import sys, json, hashlib, math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds  # noqa: E402

OUT = ROOT / "source" / "textures" / "v023"
REP = OUT / "lp3_textures_report.json"
W, H = 1024, 256
rng = np.random.default_rng(20261101 + 24)


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


CHAR, RED, TEAL, MUST, CREAM, BLACK = (hexc(c) for c in ("#242120", "#A3201F", "#2B8584", "#C99A3E", "#E2D8C2", "#121111"))

# ---- base: charcoal wool (two noise scales + fine fibre streaks along the long axis)
img = Image.new("RGB", (W, H), CHAR)
d = ImageDraw.Draw(img)
# ---- field confetti (90s): small squiggles, triangles, dots — low contrast, kept inside the border
inner = (40, 40, W - 40, H - 40)
cols = [RED, TEAL, MUST, CREAM]
for k in range(380):
    x = rng.uniform(inner[0] + 6, inner[2] - 6)
    y = rng.uniform(inner[1] + 6, inner[3] - 6)
    c = cols[k % 4]
    c = tuple(int(a * 0.62 + b * 0.38) for a, b in zip(c, CHAR))          # muted: worn wool, not plastic
    kind = k % 3
    s = rng.uniform(3.0, 6.5)
    if kind == 0:      # triangle
        a = rng.uniform(0, 2 * math.pi)
        pts = [(x + s * math.cos(a + i * 2.094), y + s * math.sin(a + i * 2.094)) for i in range(3)]
        d.polygon(pts, fill=c)
    elif kind == 1:    # squiggle
        a = rng.uniform(0, 2 * math.pi)
        pts = [(x + (i - 3) * 2.2 * math.cos(a) - 1.8 * math.sin(i * 1.6) * math.sin(a),
                y + (i - 3) * 2.2 * math.sin(a) + 1.8 * math.sin(i * 1.6) * math.cos(a)) for i in range(7)]
        d.line(pts, fill=c, width=2)
    else:              # dot
        d.ellipse((x - s * 0.45, y - s * 0.45, x + s * 0.45, y + s * 0.45), fill=c)
# ---- border: cream edge, red band with cream diamond chain, black + cream pin lines
def frame(m, w, c):
    d.rectangle((m, m, W - 1 - m, H - 1 - m), outline=c, width=w)


frame(0, 6, CREAM)
d.rectangle((6, 6, W - 7, H - 7), outline=RED, width=20)
frame(26, 4, BLACK)
frame(30, 3, CREAM)
for (x0, y0, x1, y1, horiz) in ((16, 16, W - 16, 16, True), (16, H - 17, W - 16, H - 17, True),
                                (16, 16, 16, H - 16, False), (W - 17, 16, W - 17, H - 16, False)):
    n = int(((x1 - x0) if horiz else (y1 - y0)) // 24)
    for i in range(n + 1):
        cx = x0 + i * 24 if horiz else x0
        cy = y0 if horiz else y0 + i * 24
        d.polygon([(cx - 6, cy), (cx, cy - 6), (cx + 6, cy), (cx, cy + 6)], fill=CREAM)
a = np.asarray(img, dtype=np.float64) / 255.0
# wool: multiplicative noise (coarse tufts + fine fibres)
coarse = np.asarray(Image.fromarray((rng.random((H // 4, W // 4)) * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BICUBIC),
                    dtype=np.float64) / 255.0
fine = rng.random((H, W))
fib = np.asarray(Image.fromarray((rng.random((H, W)) * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(1)), dtype=np.float64) / 255.0
mul = 0.90 + 0.10 * coarse + 0.07 * (fine - 0.5) + 0.05 * (fib - 0.5)
a = np.clip(a * mul[..., None], 0, 1)
# wear: slightly lighter, flattened pile in the middle of the long axis (foot traffic between the chairs)
yy, xx = np.mgrid[0:H, 0:W]
wear = np.exp(-(((xx - W * 0.5) / (W * 0.30)) ** 2 + ((yy - H * 0.55) / (H * 0.35)) ** 2))
a = np.clip(a * (1 + 0.06 * wear[..., None]), 0, 1)
out = Image.fromarray((a * 255 + 0.5).astype(np.uint8), "RGB")
png = OUT / "lp3_rug.png"
out.save(png)
gs_dds.convert(png, OUT / "lp3_rug.dds", "DXT1")
data = (OUT / "lp3_rug.dds").read_bytes()
rep = json.loads(REP.read_text(encoding="utf-8"))
rep["textures"] = [t for t in rep["textures"] if t["name"] != "lp3_rug"]
rep["textures"].append({"name": "lp3_rug", "file": "lp3_rug.dds", "size": [W, H], "format": "DXT1", "role": "diffuse",
                        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "derived_from": [],
                        "origin": "original_procedural",
                        "operations": "ORIGINAL procedural 90s lounge rug (v0.2.4): charcoal wool, muted confetti, red border with diamond chain"})
REP.write_text(json.dumps(rep, indent=1), encoding="utf-8")
print("GS15F_DONE lp3_rug", W, H, len(data))
