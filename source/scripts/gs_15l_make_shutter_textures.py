# LONG PIG — security shutter textures (owner brief "FINAL MLO COMPLETION + ANIMATED SECURITY SHUTTERS", 2026-11-02):
# aged galvanised roller-shutter steel for the curtain slats, a painted bottom bar, the guide rails and the curtain back.
# ORIGINAL procedural work (numpy / PIL). No third-party or Rockstar pixels.
#   python gs_15l_make_shutter_textures.py [<project_root>]   -> source/textures/shutters/*.dds + lp7_textures_report.json
# Atlas lp7_shutter (1024 x 512, DXT1), rows from the TOP of the image:
#     0-255  curtain front: 4 slats of 64 px (slat 3 = top row ... slat 0 = bottom row); u = metres / 4.5
#   256-383  bottom bar (painted steel, scuffs, rust along the lower edge)
#   384-447  guide rail (galvanised channel, rust bleed at the foot)
#   448-511  curtain back (inside face, dull dusty grey) | black rubber seal (u > 0.75)
import sys, json, hashlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds  # noqa: E402

OUT = ROOT / "source" / "textures" / "shutters"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = {"script": "source/scripts/gs_15l_make_shutter_textures.py", "version": "0.2.7-shutters", "textures": []}
SEED = 20261102 + 715
rng = np.random.default_rng(SEED)


def to_img(a, mode="RGB"):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), mode)


def save(name, img, fmt="DXT1", role="diffuse", ops=""):
    png = OUT / f"{name}.png"
    img.save(png)
    gs_dds.convert(png, OUT / f"{name}.dds", fmt)
    data = (OUT / f"{name}.dds").read_bytes()
    REPORT["textures"].append({"name": name, "file": f"{name}.dds", "size": list(img.size), "format": fmt, "role": role,
                               "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "derived_from": [],
                               "origin": "original_procedural", "operations": ops})
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


def blur(a, rad):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(rad)),
                      dtype=np.float64) / 255.0


def scratches(h, w, n, seed, length=(20, 140), horiz=True):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    rr = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rr.uniform(0, w), rr.uniform(0, h)
        L = rr.uniform(*length)
        ang = rr.normal(0.0, 0.18) + (0.0 if horiz else np.pi / 2)
        d.line([(x, y), (x + L * np.cos(ang), y + L * np.sin(ang))], fill=int(rr.uniform(90, 255)), width=1)
    return np.asarray(im, dtype=np.float64) / 255.0


W, H = 1024, 512
img = np.zeros((H, W, 3))
spec = np.zeros((H, W))

# ---------------------------------------------------------------- curtain front (rows 0-255)
h = 256
yy, xx = np.mgrid[0:h, 0:W].astype(np.float64)
galv = np.array([0.56, 0.575, 0.585])
spangle = tnoise(h, W, 8, 32, SEED + 1, octaves=3)                      # zinc spangle / mottling
rollf = 0.5 + 0.5 * np.sin(yy * 2.0 * np.pi / 64.0 * 6.0)               # roll-forming lines inside each slat
base = galv[None, None, :] * (0.86 + 0.20 * spangle[..., None]) * (0.985 + 0.015 * rollf[..., None])
# streaks of grime running down from the box (vertical, continuous across slats -> tile vertically)
streak_seed = np.random.default_rng(SEED + 2)
streak = np.zeros(W)
for _ in range(70):
    c, wd, a = streak_seed.uniform(0, W), streak_seed.uniform(2, 18), streak_seed.uniform(0.05, 0.30)
    streak += a * np.exp(-((np.arange(W) - c) / wd) ** 2)
streak = np.clip(streak, 0, 0.55)
vert = tnoise(h, W, 2, 64, SEED + 3, octaves=2)
grime = streak[None, :] * (0.6 + 0.4 * vert)
# per-slat: dirt in the joints (top / bottom 6 px of every slat), slight shade per slat, rust pin-points at the joints
sl = (yy % 64)
joint = np.clip(1.0 - np.minimum(sl, 63 - sl) / 7.0, 0, 1) ** 1.5
shade = np.array([0.97, 1.02, 0.99, 1.01])[(yy // 64).astype(int)]
rust_pts = (tnoise(h, W, 16, 96, SEED + 4, octaves=2) > 0.80) * joint
rust_col = np.array([0.42, 0.23, 0.12])
sc = scratches(h, W, 150, SEED + 5, length=(10, 70))
dent = blur((tnoise(h, W, 4, 16, SEED + 6, octaves=2) > 0.83).astype(float), 3)
front = base * shade[..., None]
front = front * (1 - 0.55 * grime[..., None]) + np.array([0.20, 0.18, 0.15]) * 0.55 * grime[..., None]
front = front * (1 - 0.35 * joint[..., None]) + np.array([0.16, 0.15, 0.13]) * 0.35 * joint[..., None]
front = front * (1 - 0.8 * rust_pts[..., None]) + rust_col * 0.8 * rust_pts[..., None]
front = front + 0.06 * sc[..., None] - 0.06 * dent[..., None]
img[0:256] = front
spec[0:256] = np.clip(0.45 + 0.25 * spangle - 0.35 * grime - 0.5 * rust_pts - 0.2 * joint + 0.15 * sc, 0.05, 1)

# ---------------------------------------------------------------- bottom bar (rows 256-383): painted dark grey steel
h = 128
yy, xx = np.mgrid[0:h, 0:W].astype(np.float64)
paint = np.array([0.24, 0.25, 0.26]) * (0.9 + 0.2 * tnoise(h, W, 4, 32, SEED + 7, octaves=3))[..., None]
chips = blur((tnoise(h, W, 16, 128, SEED + 8, octaves=2) > 0.86).astype(float), 0.8) > 0.5
under = np.array([0.50, 0.50, 0.49])                                    # bare steel where the paint chipped
low = np.clip((yy - 88) / 40.0, 0, 1)                                   # rust bleeding up from the lower edge
rust2 = low * (0.6 + 0.4 * tnoise(h, W, 4, 64, SEED + 9, octaves=3))
bar = paint * (1 - chips[..., None]) + under * chips[..., None]
bar = bar * (1 - 0.7 * rust2[..., None]) + np.array([0.38, 0.20, 0.10]) * 0.7 * rust2[..., None]
bar = bar + 0.08 * scratches(h, W, 90, SEED + 10, length=(8, 60))[..., None]
img[256:384] = bar
spec[256:384] = np.clip(0.25 + 0.4 * chips - 0.3 * rust2, 0.05, 1)

# ---------------------------------------------------------------- guide rail (rows 384-447)
h = 64
yy, xx = np.mgrid[0:h, 0:W].astype(np.float64)
rail = galv[None, None, :] * (0.80 + 0.22 * tnoise(h, W, 4, 64, SEED + 11, octaves=3))[..., None]
foot = np.clip((xx - 820) / 204.0, 0, 1) * (0.5 + 0.5 * tnoise(h, W, 8, 32, SEED + 12, octaves=2))   # u -> rail length; foot at u=1
rail = rail * (1 - 0.75 * foot[..., None]) + np.array([0.36, 0.20, 0.11]) * 0.75 * foot[..., None]
rail = rail * (1 - 0.3 * streak[None, :, None] * 0.6)
img[384:448] = rail + 0.05 * scratches(h, W, 60, SEED + 13)[..., None]
spec[384:448] = np.clip(0.5 - 0.4 * foot, 0.05, 1)

# ---------------------------------------------------------------- curtain back (rows 448-511) + rubber seal
h = 64
back = np.array([0.40, 0.41, 0.42]) * (0.85 + 0.25 * tnoise(h, W, 4, 32, SEED + 14, octaves=3))[..., None]
img[448:512] = back
img[448:512, 768:] = np.array([0.06, 0.06, 0.065]) * (0.9 + 0.2 * tnoise(h, 256, 4, 8, SEED + 15, octaves=2))[..., None]
spec[448:512] = 0.15

save("lp7_shutter", to_img(img), ops="ORIGINAL aged galvanised roller-shutter atlas (slats, bottom bar, rail, curtain back, seal)")
save("lp7_shutter_s", to_img(np.dstack([spec, spec, spec])).resize((256, 128), Image.Resampling.LANCZOS), role="spec",
     ops="ORIGINAL specular mask for lp7_shutter")
save("lp7_flat_n", Image.new("RGB", (16, 16), (128, 128, 255)), role="normal", ops="flat normal (16 px)")
(OUT / "lp7_textures_report.json").write_text(json.dumps(REPORT, indent=1), encoding="utf-8")
print("DONE_SHUTTER_TEX", len(REPORT["textures"]))
