# LONG PIG — Vertical Slice textures (v0.2.0): GTA-ready DDS (DXT1, full mip chain) from the approved CC0 originals
# plus a few ORIGINAL procedural textures. Pure Python (Pillow + numpy + source/tools/gs_dds.py).
#   python gs_14_make_slice_textures.py <cc0_downloads_dir> [<out_dir>]
# Inputs (byte-exact originals, see assets/cc0/_downloads/fetch_manifest.json):
#   Poly Haven 2K JPG: brown_leather, kitchen_wood, beige_wall_001 (diff/albedo, nor_dx, rough)
#   ambientCG zips: Tiles139_2K-JPG, OfficeCeiling003_1K-JPG, Terrazzo004_1K-JPG, Metal012_1K-JPG
# Every output is seamless (pointwise edits, whole-image resampling or whole-tile copies only).
# ORIGINAL textures: brass, flat normal, matte spec, deli food atlas (no menu board: vanilla GTA menu prop instead).
# Outputs per material <name>: <name>.dds (diffuse), <name>_n.dds (DirectX normal), <name>_s.dds (spec, grey),
# and a JSON report (derived_from, operations, sizes) for assets/registry.json.
import sys, io, json, zipfile, hashlib, math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import gs_dds  # noqa: E402

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / "textures" / "slice"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20261030)
REPORT = {"script": "source/scripts/gs_14_make_slice_textures.py", "version": "0.2.0", "textures": []}


# ------------------------------------------------------------------ io helpers
def sha256(b):
    return hashlib.sha256(b).hexdigest()


def load_file(name):
    p = SRC / name
    return Image.open(io.BytesIO(p.read_bytes())), name


def load_zip(zname, member):
    zf = zipfile.ZipFile(SRC / zname)
    return Image.open(io.BytesIO(zf.read(member))), f"{zname}:{member}"


def rgb(img):
    return np.asarray(img.convert("RGB"), dtype=np.float64) / 255.0


def grey(img):
    return np.asarray(img.convert("L"), dtype=np.float64) / 255.0


def hexcol(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def resize(a, size):
    mode = "RGB" if a.ndim == 3 else "L"
    img = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), mode)
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(img, dtype=np.float64) / 255.0


def save(name, a, size, fmt="DXT1", role="diffuse", derived=(), ops=""):
    a = resize(a, size)
    if a.ndim == 2:
        a = np.dstack([a, a, a])
    png = OUT / f"{name}.png"
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(png)
    info = gs_dds.convert(png, OUT / f"{name}.dds", fmt)
    data = (OUT / f"{name}.dds").read_bytes()
    REPORT["textures"].append({"name": name, "role": role, "size": size, "format": fmt, "dds_bytes": len(data),
                               "dds_sha256": sha256(data), "derived_from": list(derived), "operations": ops,
                               "mips": info.get("mips") if isinstance(info, dict) else None})
    print(f"{name:28s} {size:5d} {fmt} {len(data):9d} B  <- {', '.join(derived) or 'ORIGINAL'}")


def tint(src, target_hex, detail=1.0, keep_hue=0.0):
    """Recolour keeping the source's light/dark detail: out = target * (src / mean(src))^detail (in linear light).
    keep_hue blends in the source's own per-channel variation (0 = pure target hue)."""
    lin = srgb_to_lin(src)
    lum = lin @ np.array([0.2126, 0.7152, 0.0722])
    rel = (lum / max(lum.mean(), 1e-6)) ** detail
    tgt = srgb_to_lin(hexcol(target_hex))
    out = tgt[None, None, :] * rel[..., None]
    if keep_hue > 0:
        chan = lin / np.maximum(lin.mean(axis=(0, 1)), 1e-6)[None, None, :]
        out = out * ((chan / np.maximum(rel[..., None], 1e-6)) ** keep_hue)
    return lin_to_srgb(out)


def spec_from_rough(rough, k, base=0.0, gamma=1.5):
    return np.clip(base + k * (1.0 - rough) ** gamma, 0, 1)


def renorm_normal(a):
    v = a * 2.0 - 1.0
    v /= np.maximum(np.linalg.norm(v, axis=2, keepdims=True), 1e-6)
    return v * 0.5 + 0.5


def normal_flatten(a, k):
    """Scale the bumpiness of a normal map (k < 1 flatter)."""
    v = a * 2.0 - 1.0
    v[..., 0] *= k
    v[..., 1] *= k
    v /= np.maximum(np.linalg.norm(v, axis=2, keepdims=True), 1e-6)
    return v * 0.5 + 0.5


# ================================================================== 1. floor: muted cream / brown checker (Tiles139)
col, c_src = load_zip("Tiles139_2K-JPG.zip", "Tiles139_2K-JPG_Color.jpg")
nrm, n_src = load_zip("Tiles139_2K-JPG.zip", "Tiles139_2K-JPG_NormalDX.jpg")
rgh, r_src = load_zip("Tiles139_2K-JPG.zip", "Tiles139_2K-JPG_Roughness.jpg")
dsp, d_src = load_zip("Tiles139_2K-JPG.zip", "Tiles139_2K-JPG_Displacement.jpg")
C, N, Rg, D = rgb(col), rgb(nrm), grey(rgh), grey(dsp)
H = C.shape[0]
# 6 x 6 hand-laid tiles; grout lines measured on the displacement map (docs: gs_14 report)
cuts = [-10, 332, 683, 1030, 1371, 1715, H - 10]
idx = np.zeros(H, dtype=int)
for k in range(6):
    a0, a1 = cuts[k], cuts[k + 1]
    for p in range(a0, a1):
        idx[p % H] = k
par = (idx[:, None] + idx[None, :]) % 2                       # checker parity per pixel (rows x cols)
# grout = narrow dips of the displacement next to the measured grid lines (the tiles themselves are tilted, so a
# plain height threshold would mark whole tile corners as grout)
dist = np.full(H, 99.0)
for c in cuts:
    for cc in (c % H, c % H - H, c % H + H):
        dist = np.minimum(dist, np.abs(np.arange(H) - cc))
near = np.minimum(dist[:, None], dist[None, :])                # px to the nearest grid line (rows / cols)
blur = np.asarray(Image.fromarray((D * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12)), float) / 255
hp = D - blur
grout = np.clip((-hp - 0.015) / 0.04, 0, 1) * np.clip((16 - near) / 6, 0, 1)
grout = np.maximum(grout, np.clip((3.5 - near) / 2.0, 0, 1))    # guaranteed thin joint on the grid itself
cream = tint(C, "#D9CAAB", detail=0.85, keep_hue=0.25)
brown = tint(C, "#6A4630", detail=0.95, keep_hue=0.25)
tile = np.where(par[..., None] == 0, cream, brown)
gro = tint(C, "#8E8577", detail=0.6)
F = tile * (1 - grout[..., None]) + gro * grout[..., None]
save("lp_floor_checker", F, 2048, derived=[c_src, d_src],
     ops="checker recolour of the 6x6 tiles (parity from the measured grout grid), cream #D9CAAB / brown #6A4630, grout #8E8577")
save("lp_floor_checker_n", renorm_normal(normal_flatten(N, 0.8)), 1024, role="normal", derived=[n_src], ops="resize 1024, bump x0.8")
save("lp_floor_checker_s", spec_from_rough(Rg, 0.75, 0.05) * (1 - 0.6 * grout), 512, role="spec", derived=[r_src, d_src],
     ops="spec = 0.05 + 0.75 (1-rough)^1.5, grout x0.4")

# ================================================================== 2. walls: cream plaster (beige_wall_001)
col, c_src = load_file("beige_wall_001_diff_2k.jpg")
nrm, n_src = load_file("beige_wall_001_nor_dx_2k.jpg")
rgh, r_src = load_file("beige_wall_001_rough_2k.jpg")
save("lp_wall_plaster", tint(rgb(col), "#E2D5BA", detail=1.0, keep_hue=0.3), 1024, derived=[c_src], ops="tint #E2D5BA")
save("lp_wall_plaster_n", renorm_normal(normal_flatten(rgb(nrm), 0.6)), 512, role="normal", derived=[n_src], ops="bump x0.6")
save("lp_wall_plaster_s", spec_from_rough(grey(rgh), 0.18, 0.02), 512, role="spec", derived=[r_src], ops="spec 0.02 + 0.18 (1-rough)^1.5")

# ================================================================== 3. walnut (kitchen_wood): booths, wainscot, casings, counter
col, c_src = load_file("kitchen_wood_diff_2k.jpg")
nrm, n_src = load_file("kitchen_wood_nor_dx_2k.jpg")
rgh, r_src = load_file("kitchen_wood_rough_2k.jpg")
save("lp_wood_walnut", tint(rgb(col), "#4B2F1E", detail=1.25, keep_hue=0.35), 1024, derived=[c_src], ops="tint walnut #4B2F1E, detail x1.25")
save("lp_wood_walnut_n", renorm_normal(normal_flatten(rgb(nrm), 0.7)), 1024, role="normal", derived=[n_src], ops="bump x0.7")
save("lp_wood_walnut_s", spec_from_rough(grey(rgh), 0.45, 0.05), 512, role="spec", derived=[r_src], ops="satin: 0.05 + 0.45 (1-rough)^1.5")

# ================================================================== 4. ceiling tiles (OfficeCeiling003): fixtures removed, yellowed
col, c_src = load_zip("OfficeCeiling003_1K-JPG.zip", "OfficeCeiling003_1K-JPG_Color.jpg")
nrm, n_src = load_zip("OfficeCeiling003_1K-JPG.zip", "OfficeCeiling003_1K-JPG_NormalDX.jpg")
rgh, r_src = load_zip("OfficeCeiling003_1K-JPG.zip", "OfficeCeiling003_1K-JPG_Roughness.jpg")
C, N, Rg = rgb(col), rgb(nrm), grey(rgh)
P = 128                                                                     # 8 x 8 grid, measured
for (cx, cy) in ((3, 3), (7, 3), (3, 7), (7, 7)):                           # light panels (Emission map) -> plain tile left of it
    sl_dst = (slice(cy * P, (cy + 1) * P), slice(cx * P, (cx + 1) * P))
    sl_src = (slice(cy * P, (cy + 1) * P), slice((cx - 1) * P, cx * P))
    for A in (C, N, Rg):
        A[sl_dst] = A[sl_src]
save("lp_ceiling_tile", tint(C, "#DCD1B8", detail=1.0, keep_hue=0.2), 1024, derived=[c_src],
     ops="4 light-panel tiles replaced by the neighbouring plain tile, tint #DCD1B8")
save("lp_ceiling_tile_n", renorm_normal(N), 512, role="normal", derived=[n_src], ops="same tile copies")
save("lp_ceiling_tile_s", spec_from_rough(Rg, 0.10, 0.0), 512, role="spec", derived=[r_src], ops="0.10 (1-rough)^1.5")

# ================================================================== 5. burgundy leather (brown_leather)
col, c_src = load_file("brown_leather_albedo_2k.jpg")
nrm, n_src = load_file("brown_leather_nor_dx_2k.jpg")
rgh, r_src = load_file("brown_leather_rough_2k.jpg")
save("lp_leather_burgundy", tint(rgb(col), "#5E1A1D", detail=1.1, keep_hue=0.0), 1024, derived=[c_src], ops="tint burgundy #5E1A1D")
save("lp_leather_burgundy_n", renorm_normal(rgb(nrm)), 1024, role="normal", derived=[n_src], ops="resize")
save("lp_leather_burgundy_s", spec_from_rough(grey(rgh), 0.55, 0.06), 512, role="spec", derived=[r_src], ops="0.06 + 0.55 (1-rough)^1.5")

# ================================================================== 6. terrazzo table / counter tops (Terrazzo004)
col, c_src = load_zip("Terrazzo004_1K-JPG.zip", "Terrazzo004_1K-JPG_Color.jpg")
nrm, n_src = load_zip("Terrazzo004_1K-JPG.zip", "Terrazzo004_1K-JPG_NormalDX.jpg")
rgh, r_src = load_zip("Terrazzo004_1K-JPG.zip", "Terrazzo004_1K-JPG_Roughness.jpg")
save("lp_terrazzo", tint(rgb(col), "#CDBFA6", detail=1.0, keep_hue=0.5), 1024, derived=[c_src], ops="warm tint #CDBFA6")
save("lp_terrazzo_n", renorm_normal(normal_flatten(rgb(nrm), 0.5)), 512, role="normal", derived=[n_src], ops="bump x0.5 (polished)")
save("lp_terrazzo_s", spec_from_rough(grey(rgh), 0.85, 0.15), 512, role="spec", derived=[r_src], ops="polished 0.15 + 0.85 (1-rough)^1.5")

# ================================================================== 7. stainless steel (Metal012)
col, c_src = load_zip("Metal012_1K-JPG.zip", "Metal012_1K-JPG_Color.jpg")
nrm, n_src = load_zip("Metal012_1K-JPG.zip", "Metal012_1K-JPG_NormalDX.jpg")
rgh, r_src = load_zip("Metal012_1K-JPG.zip", "Metal012_1K-JPG_Roughness.jpg")
save("lp_steel", tint(rgb(col), "#A9ADAE", detail=1.0, keep_hue=0.0), 512, derived=[c_src], ops="neutral steel #A9ADAE")
save("lp_steel_n", renorm_normal(normal_flatten(rgb(nrm), 0.5)), 512, role="normal", derived=[n_src], ops="bump x0.5")
save("lp_steel_s", spec_from_rough(grey(rgh), 1.0, 0.25), 512, role="spec", derived=[r_src], ops="0.25 + (1-rough)^1.5")


# ================================================================== 8. ORIGINAL: brass, flat normal, deli food atlas
def fnoise(h, w, beta=2.0, seed=0):
    rng = np.random.default_rng(seed)
    wn = rng.normal(size=(h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    n = np.real(np.fft.ifft2(np.fft.fft2(wn) / f ** (beta / 2.0)))
    n -= n.mean()
    return n / (np.abs(n).max() + 1e-9)


B = np.ones((64, 64, 3)) * hexcol("#A8834A") * (1 + 0.06 * fnoise(64, 64, 2.5, 3)[..., None])
save("lp_brass", B, 64, ops="ORIGINAL flat aged brass #A8834A")
save("lp_brass_s", np.full((64, 64), 0.75), 64, role="spec", ops="ORIGINAL")
save("lp_flat_n", np.dstack([np.full((64, 64), 0.5), np.full((64, 64), 0.5), np.ones((64, 64))]), 64, role="normal", ops="ORIGINAL flat")
save("lp_matte_s", np.full((64, 64), 0.08), 64, role="spec", ops="ORIGINAL low spec")
save("lp_glow", np.ones((64, 64, 3)) * hexcol("#FFE4B8"), 64, ops="ORIGINAL warm white for emissive bulbs / globes / case light strips")

# deli food atlas 1024: 4 x 4 cells of 256 (u,v cells used by gs_slice_geometry)
S = 1024
A = np.zeros((S, S, 3))
cell = 256


def put(cx, cy, img):
    A[cy * cell:(cy + 1) * cell, cx * cell:(cx + 1) * cell] = img


yy, xx = np.mgrid[0:cell, 0:cell] / cell
n1 = fnoise(cell, cell, 1.6, 11)
n2 = fnoise(cell, cell, 2.6, 12)
# (0,0) salami casing: dark red-brown with white bloom
cas = hexcol("#5C2A22") * (1 + 0.18 * n2[..., None])
bloom = np.clip((fnoise(cell, cell, 1.2, 13) - 0.25) * 3, 0, 1)
put(0, 0, cas * (1 - 0.55 * bloom[..., None]) + hexcol("#D9D2C4") * 0.55 * bloom[..., None])
# (1,0) salami cut face: red with white fat specks
spk = (fnoise(cell, cell, 0.6, 14) > 0.45).astype(float)
spk = np.asarray(Image.fromarray((spk * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), float) / 255
put(1, 0, hexcol("#9E2F2C") * (1 + 0.12 * n1[..., None]) * (1 - spk[..., None]) + hexcol("#EDE3D3") * spk[..., None])
# (2,0) provolone wax / rind: yellow
put(2, 0, hexcol("#D9A93E") * (1 + 0.10 * n2[..., None]))
# (3,0) provolone cut face: pale cream
put(3, 0, hexcol("#EFE2B8") * (1 + 0.05 * n1[..., None]))
# (0,1) prosciutto skin: amber-brown
put(0, 1, hexcol("#86563A") * (1 + 0.15 * n2[..., None]))
# (1,1) ham / mortadella cut: pink with fat dots
dots = (fnoise(cell, cell, 0.4, 15) > 0.55).astype(float)
dots = np.asarray(Image.fromarray((dots * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)), float) / 255
put(1, 1, hexcol("#D98C8C") * (1 + 0.06 * n1[..., None]) * (1 - dots[..., None]) + hexcol("#F4E9E1") * dots[..., None])
# (2,1) roast beef: dark red-brown
put(2, 1, hexcol("#6E2E26") * (1 + 0.15 * n1[..., None]))
# (3,1) white paper / tray liner
put(3, 1, hexcol("#EEE8DC") * (1 + 0.03 * n1[..., None]))
# (0,2) mozzarella / ricotta: white
put(0, 2, hexcol("#F2EFE6") * (1 + 0.03 * n2[..., None]))
# (1,2) olives: dark green with highlights
put(1, 2, hexcol("#3E4A22") * (1 + 0.35 * fnoise(cell, cell, 0.8, 16)[..., None]))
# (2,2) roasted peppers: red
put(2, 2, hexcol("#B5281F") * (1 + 0.2 * n2[..., None]))
# (3,2) bread crust
put(3, 2, hexcol("#B07A3E") * (1 + 0.15 * n2[..., None]))
# (0..3,3) price tag strip (cream) + string (twine)
put(0, 3, hexcol("#E8DCC2") * (1 + 0.02 * n1[..., None]))
put(1, 3, hexcol("#B9A27A") * (1 + 0.10 * n1[..., None]))
put(2, 3, hexcol("#2F5D3A") * (1 + 0.05 * n1[..., None]))          # accent green (tags)
put(3, 3, hexcol("#A3262A") * (1 + 0.05 * n1[..., None]))          # accent red
save("lp_deli_food", np.clip(A, 0, 1), 1024, ops="ORIGINAL procedural deli food atlas (4x4 cells of 256 px)")
save("lp_deli_food_s", np.full((64, 64), 0.25), 64, role="spec", ops="ORIGINAL moist spec")

# 0.2.0: no own menu board — the user wants a vanilla GTA menu prop (placed by archetype name in the MLO)

(OUT / "lp_slice_textures_report.json").write_text(json.dumps(REPORT, indent=1))
print("GS_SLICE_TEX_DONE", len(REPORT["textures"]), "textures,",
      sum(t["dds_bytes"] for t in REPORT["textures"]), "bytes ->", OUT)
