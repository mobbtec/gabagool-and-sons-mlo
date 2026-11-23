# LONG PIG 3.0.1 texture: lp30_slats - worn wooden venetian-blind slats (own procedural, no sources).
#   512 x 256: six slat strips of 32 px (different tone / wear), one strip of dirty cloth ladder tape, one strip of dark rail wood.
import sys, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
OUT = ROOT / "source" / "textures" / "v300"
W, H = 512, 256
rng = np.random.default_rng(3011)


def blur(a, rx, ry=None):
    im = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255))
    im = im.resize((max(2, int(a.shape[1] / rx)), max(2, int(a.shape[0] / (ry or rx)))), Image.BILINEAR).resize((a.shape[1], a.shape[0]), Image.BICUBIC)
    return np.asarray(im, float) / 255.0


img = np.zeros((H, W, 3))
tones = [(0.46, 0.30, 0.17), (0.40, 0.25, 0.14), (0.50, 0.34, 0.20), (0.36, 0.22, 0.12), (0.44, 0.29, 0.18), (0.42, 0.28, 0.15)]
for k, tone in enumerate(tones):
    y0 = k * 32
    grain = blur(rng.random((32, W)), 40, 1.2)                       # long streaks along the slat
    fine = blur(rng.random((32, W)), 9, 1.0)
    wear = blur(rng.random((32, W)), 60, 10)                         # where the varnish is gone
    wear = np.clip((wear - 0.52) * 5.0, 0, 1) * (0.35 + 0.65 * (k % 3 == 0))
    dirt = blur(rng.random((32, W)), 90, 16)
    v = 0.78 + 0.34 * grain + 0.12 * (fine - 0.5)
    strip = np.stack([tone[c] * v for c in range(3)], -1)
    pale = np.array([0.66, 0.56, 0.42])
    strip = strip * (1 - wear[..., None] * 0.75) + pale * wear[..., None] * 0.75
    strip *= (1.0 - 0.30 * np.clip((dirt - 0.45) * 3, 0, 1))[..., None]
    x = np.linspace(0, 1, W)
    ends = np.clip(1 - np.minimum(x, 1 - x) * 14, 0, 1) ** 2         # grimy ends
    strip *= (1 - 0.35 * ends)[None, :, None]
    yy = np.arange(32)
    edge = np.clip(1 - np.minimum(yy, 31 - yy) / 2.5, 0, 1)          # darker long edges
    strip *= (1 - 0.22 * edge)[:, None, None]
    for _ in range(3 + k % 3):                                       # chips / scratches
        cx, cy, L = rng.integers(10, W - 30), rng.integers(3, 29), rng.integers(6, 26)
        strip[cy:cy + 1, cx:cx + L] = strip[cy:cy + 1, cx:cx + L] * 0.4 + pale * 0.6
    img[y0:y0 + 32] = strip
t = blur(rng.random((32, W)), 30, 6)
weave = (np.indices((32, W)).sum(0) % 2) * 0.05
tape = np.stack([(0.62 + 0.14 * t - weave) * c for c in (1.0, 0.93, 0.78)], -1)
tape *= (1 - 0.35 * np.clip((blur(rng.random((32, W)), 70, 12) - 0.5) * 4, 0, 1))[..., None]
img[192:224] = tape
g = blur(rng.random((32, W)), 40, 1.2)
img[224:256] = np.stack([c * (0.8 + 0.4 * g) for c in (0.24, 0.15, 0.09)], -1)
im = Image.fromarray(np.uint8(np.clip(img, 0, 1) * 255 + 0.5))
data = gs_dds.encode_dds(im, "DXT1"); (OUT / "lp30_slats.dds").write_bytes(data); im.save(OUT / "lp30_slats_preview.png")
rp = OUT / "v300_textures_report.json"; rep = json.loads(rp.read_text())
rep["files"]["lp30_slats"] = {"size": [W, H], "format": "DXT1", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "from": "own procedural (gs_15ap_v300b.py)"}
rp.write_text(json.dumps(rep, indent=1))
print("ok", len(data))
