# LONG PIG 0.3.1-l (owner 2026-11-13 21:43: "измени эту текстуру грязную ... сделай везде грязность другую, где-то течёт"):
# 1) back-of-house plaster = Poly Haven "painted_plaster_wall" (CC0, 2 m) instead of the blotchy concrete_wall_003,
#    graded to the warm off-white of the BOH tiles (colour balance only, the photo stays the photo);
# 2) lp9_boh_leaks = atlas of ambientCG leak decals (CC0) for LOCAL stains: ceiling leaks, a pipe streak, damp at the
#    tile line. Only conversion here: crop, resize, colour + opacity -> DXT5 with full mips.
import sys, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
DL = ROOT / "assets" / "cc0" / "_downloads"
OUT = ROOT / "source" / "textures" / "v031"
rep = {}


def save(name, img, fmt, src, url, licence, extra=None):
    data = gs_dds.encode_dds(img, fmt)
    (OUT / f"{name}.dds").write_bytes(data)
    rep[name] = dict({"size": list(img.size), "format": fmt, "sha256": hashlib.sha256(data).hexdigest(),
                      "derived_from": src, "source": url, "licence": licence}, **(extra or {}))


# ---------------------------------------------------------------- 1. plaster
A = "painted_plaster_wall"
TARGET = np.array([196.0, 189.0, 176.0])                 # warm off-white, a step below the cream wall tiles
d = np.asarray(Image.open(DL / f"{A}_diff_2k.jpg").convert("RGB").resize((1024, 1024), Image.LANCZOS), float)
gain = TARGET / d.reshape(-1, 3).mean(0)
d = np.clip(d * gain, 0, 255).astype(np.uint8)
save("lp9_boh_plaster", Image.fromarray(d), "DXT1", f"{A}_diff_2k.jpg", f"https://polyhaven.com/a/{A}", "CC0 1.0 (Poly Haven)",
     {"physical_m": 2.0, "colour_gain": [round(float(g), 3) for g in gain]})
n = np.asarray(Image.open(DL / f"{A}_nor_dx_2k.jpg").convert("RGB").resize((512, 512), Image.LANCZOS), float) / 255.0
v = n * 2 - 1
v /= np.linalg.norm(v, axis=2, keepdims=True) + 1e-9
save("lp9_boh_plaster_n", Image.fromarray(np.clip((v * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)), "DXT1",
     f"{A}_nor_dx_2k.jpg", f"https://polyhaven.com/a/{A}", "CC0 1.0 (Poly Haven)")
r = np.asarray(Image.open(DL / f"{A}_rough_2k.jpg").convert("L").resize((512, 512), Image.LANCZOS), float) / 255.0
s = np.clip(0.03 + 0.22 * (1 - r) ** 1.5, 0, 1)
save("lp9_boh_plaster_s", Image.fromarray((s * 255).astype(np.uint8)).convert("RGB"), "DXT1", f"{A}_rough_2k.jpg",
     f"https://polyhaven.com/a/{A}", "CC0 1.0 (Poly Haven)")

# ---------------------------------------------------------------- 2. leak decal atlas (1024 x 1024, DXT5)
def leak(nm):
    c = Image.open(DL / f"{nm}_1K-PNG" / f"{nm}_1K-PNG_Color.png").convert("RGB")
    o = Image.open(DL / f"{nm}_1K-PNG" / f"{nm}_1K-PNG_Opacity.png").convert("L")
    rgba = c.copy()
    rgba.putalpha(o)
    return rgba


atlas = Image.new("RGBA", (1024, 1024), (90, 86, 70, 0))
L2 = leak("Leaking002")                                    # 1024 x 512, streaks in the top half
top = L2.crop((0, 0, 1024, 256))
atlas.paste(top.crop((0, 0, 512, 256)).resize((512, 512), Image.LANCZOS), (0, 0))          # A  ceiling leak (left half)
atlas.paste(top.crop((512, 0, 1024, 256)).resize((512, 512), Image.LANCZOS), (512, 0))     # A2 ceiling leak (right half)
L6 = leak("Leaking006")                                    # 256 x 1024, one streak
atlas.paste(L6.resize((128, 512), Image.LANCZOS), (0, 512))                                # B  pipe streak
L8 = leak("Leaking008")                                    # 1024 x 256, damp band
atlas.paste(L8.resize((896, 256), Image.LANCZOS), (128, 512))                              # C  damp band
atlas.paste(L8.transpose(Image.FLIP_LEFT_RIGHT).resize((896, 256), Image.LANCZOS), (128, 768))   # D damp band (mirrored)
a = np.asarray(atlas, float)


def taper(x0, y0, x1, y1, side=0.18, top=0.0, gain=1.0):
    """Soft left / right (and top) edges inside a region so no decal shows its rectangle."""
    w, h = x1 - x0, y1 - y0
    u = (np.arange(w) + 0.5) / w
    wx = np.clip(np.minimum(u, 1 - u) / side, 0, 1) ** 1.5
    wy = np.ones(h)
    if top > 0:
        vv = (np.arange(h) + 0.5) / h
        wy = np.clip(vv / top, 0, 1)
    a[y0:y1, x0:x1, 3] *= gain * wy[:, None] * wx[None, :]


taper(0, 0, 512, 512, gain=1.35)            # A   ceiling leaks: stronger than the source, soft sides
taper(512, 0, 1024, 512, gain=1.35)         # A2
taper(0, 512, 128, 1024, side=0.10)         # B   streak
taper(128, 512, 1024, 768, side=0.12, top=0.25)   # C damp
taper(128, 768, 1024, 1024, side=0.12, top=0.25)  # D damp
a[..., 3] = np.clip(a[..., 3], 0, 255)
# no alpha bleeding of black: colour where alpha = 0 takes the mean leak colour (keeps mip edges clean)
mean = a[a[..., 3] > 60][:, :3].mean(0)
m0 = a[..., 3] < 1
a[m0, :3] = mean
# 512 x 512 in the game (gs_boh.ydr must stay < 16 MiB physical; the stains are soft, 512 is plenty)
save("lp9_boh_leaks", Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((512, 512), Image.LANCZOS), "DXT5",
     "Leaking002/006/008_1K-PNG (Color + Opacity)", "https://ambientcg.com/view?id=Leaking002 | Leaking006 | Leaking008",
     "CC0 1.0 (ambientCG)", {"regions_px": {"A": [0, 0, 512, 512], "A2": [512, 0, 1024, 512], "B": [0, 512, 128, 1024],
                                            "C": [128, 512, 1024, 768], "D": [128, 768, 1024, 1024]}})
# ---------------------------------------------------------------- 3. one ceiling tile (the fallen tile in the kitchen)
# a single 64 cm cell of our own ceiling texture (lp5_ceiling_tile, 2048 px = 8 x 8 cells) - so the back-of-house drawable
# does not carry the whole 2048 px ceiling sheet for one face
src_c = ROOT / "source" / "textures" / "v026" / "lp5_ceiling_tile.dds"
cell = Image.open(src_c).convert("RGB").crop((768, 512, 1024, 768))
save("lp9_ceil_tile1", cell, "DXT1", "v026/lp5_ceiling_tile.dds cell (3, 2)", "own texture (derivative of OfficeCeiling003, CC0)",
     "CC0 1.0 / own")
(OUT / "cc0_v031l_report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
prev = Image.new("RGB", (1024 + 512, 512), (40, 40, 40))
prev.paste(Image.open(OUT / "lp9_boh_plaster.dds").convert("RGB").resize((512, 512)), (0, 0))
bg = Image.new("RGBA", (512, 512), (196, 189, 176, 255))
bg.alpha_composite(Image.open(OUT / "lp9_boh_leaks.dds").convert("RGBA"))
prev.paste(bg.convert("RGB").resize((512, 512)), (512, 0))
pl = Image.open(OUT / "lp9_boh_plaster.dds").convert("RGBA").resize((512, 512))
pl.alpha_composite(Image.open(OUT / "lp9_boh_leaks.dds").convert("RGBA").crop((0, 0, 256, 256)).resize((512, 512)))
prev.paste(pl.convert("RGB"), (1024, 0))
prev.save(OUT / "_cc0_v031l_prev.jpg", quality=85)
print("ok", list(rep))
