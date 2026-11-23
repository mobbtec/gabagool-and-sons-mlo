# LONG PIG 1.2.0 textures + brick table. Sources (all CC0, ambientCG): Tiles135B / Tiles135C (already downloaded),
# PaintedWood003 (PaintedWood003_1K-JPG.zip). Only conversion: crop, resize, colour grade, masks.
import sys, json, hashlib, zipfile, io, math, urllib.request, glob
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
DL = ROOT / "assets" / "cc0" / "_downloads"
OUT = ROOT / "source" / "textures" / "v031"
rep = {}
def zimg(zname, key, url=None):
    zp = DL / zname
    if not zp.exists():
        zp.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
    z = zipfile.ZipFile(zp)
    rep.setdefault("_zips", {})[zname] = {"bytes": zp.stat().st_size, "sha256": hashlib.sha256(zp.read_bytes()).hexdigest()}
    return Image.open(io.BytesIO(z.read(next(x for x in z.namelist() if key in x and x.lower().endswith(".jpg")))))
def save(name, im, fmt, src):
    data = gs_dds.encode_dds(im, fmt)
    (OUT / f"{name}.dds").write_bytes(data)
    rep[name] = {"size": list(im.size), "format": fmt, "sha256": hashlib.sha256(data).hexdigest(), "derived_from": src, "licence": "CC0 1.0 (ambientCG)"}
def nrm(im, size):
    n = np.asarray(im.convert("RGB").resize((size, size), Image.LANCZOS), float) / 127.5 - 1.0
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return Image.fromarray(np.clip((n + 1.0) * 127.5, 0, 255).astype(np.uint8))
def spec(im, size, k=0.8):
    s = np.clip(255.0 - np.asarray(im.convert("L").resize((size, size), Image.LANCZOS), float), 0, 255) * k
    return Image.fromarray(np.stack([s] * 3, 2).astype(np.uint8))
# 1. blue counter wall: the LESS damaged variant B (revision)
B = "Tiles135B_1K-JPG.zip"
c = zimg(B, "_Color").convert("RGB").resize((512, 512), Image.LANCZOS)
save("lp10_tile_blue", ImageEnhance.Brightness(ImageEnhance.Color(c).enhance(0.60)).enhance(1.0), "DXT1", "Tiles135B")
save("lp10_tile_blue_n", nrm(zimg(B, "_NormalGL"), 512), "DXT1", "Tiles135B")
save("lp10_tile_blue_s", spec(zimg(B, "_Roughness"), 256), "DXT1", "Tiles135B")
# 2. normal / spec of the damaged variant C for the red panels (shell) and the kitchen tile (back rooms)
C = "Tiles135C_1K-JPG.zip"
save("lp10_tile_dirty_n", nrm(zimg(C, "_NormalGL"), 512), "DXT1", "Tiles135C")
save("lp10_tile_dirty_s", spec(zimg(C, "_Roughness"), 256), "DXT1", "Tiles135C")
# 3. floor damage decal: the bare, broken-out patches of variant C (large blobs only), alpha-cut
cc = np.asarray(zimg(C, "_Color").convert("RGB").resize((512, 512), Image.LANCZOS), float)
glaze = np.clip((cc[..., 2] - cc[..., 0] - 6.0) / 18.0, 0.0, 1.0)
dmg = Image.fromarray(((1.0 - glaze) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))
a = (np.asarray(dmg, float) > 150).astype(np.uint8) * 255
a = np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(1.2)))
rgba = np.dstack([np.clip(cc * 0.62, 0, 255).astype(np.uint8), a])
save("lp11_floor_dmg", Image.fromarray(rgba, "RGBA"), "DXT5", "Tiles135C")
Image.fromarray(rgba, "RGBA").save(OUT / "_floor_dmg_prev.png")
# 4. counter boards: worn red painted wood, graded to the oxblood of the interior
W = "PaintedWood003_1K-JPG.zip"
w = np.asarray(zimg(W, "_Color", "https://ambientcg.com/get?file=" + W).convert("RGB").resize((512, 512), Image.LANCZOS), float)
w = np.clip(w * np.array([0.50, 0.42, 0.42]), 0, 255).astype(np.uint8)
save("lp11_board", Image.fromarray(w), "DXT1", "PaintedWood003")
save("lp11_board_n", nrm(zimg(W, "_NormalGL"), 256), "DXT1", "PaintedWood003")
Image.fromarray(w).save(OUT / "_board_prev.jpg")
(OUT / "cc0_v120_report.json").write_text(json.dumps(rep, indent=1))
# 5. brick table: real bricks of the wall texture (lp4_paintbrick, 2 m per repeat) at chosen spots of four hall wall faces
im = np.asarray(Image.open(glob.glob(str(ROOT / "source" / "textures" / "*" / "lp4_paintbrick.dds"))[0]).convert("L"), float)
N = im.shape[0]
def runs(v, k):
    thr = v.mean() - k * v.std(); out = []; s = None
    for i, x in enumerate(v):
        if x < thr:
            if s is None: s = i
            e = i
        elif s is not None:
            out.append((s, e)); s = None
    if s is not None: out.append((s, e))
    return out
PITCH = N / 24.0                                                 # 24 regular courses per 2 m; brick lengths vary, so a fixed 22 cm is used
FACES = {"ch_r": ((-2.9, 2.5), (-1.84, 1.36), 0.0, 0.778, (0.731, 0.682)), "w_pier": ((-2.9, 3.46), (-2.9, 2.5), 3.982, 4.46, (1.0, 0.0)),
         "sw_pier": ((0.58, -1.23), (1.26, -1.23), 0.0, 0.34, (0.0, 1.0)), "ch_l": ((-0.52, -0.05), (0.58, -1.23), 1.742, 2.552, (0.731, 0.682))}
SPOTS = (("ch_r", 0.45, 1.90, "out"), ("ch_r", 0.95, 2.40, "out"), ("ch_r", 0.70, 1.45, "hole"), ("w_pier", 0.50, 2.20, "out"),
         ("w_pier", 0.30, 1.50, "hole"), ("sw_pier", 0.30, 2.00, "out"), ("sw_pier", 0.40, 2.70, "out"), ("ch_l", 0.60, 1.70, "out"),
         ("ch_l", 1.10, 2.30, "hole"), ("ch_l", 0.90, 2.85, "out"), ("ch_r", 1.20, 1.25, "out"), ("ch_l", 0.35, 1.30, "hole"))
bricks = []
for face, x, z, kind in SPOTS:
    A, Bp, uA, uB, n = FACES[face]
    L = math.hypot(Bp[0] - A[0], Bp[1] - A[1])
    u = uA + (uB - uA) * x / L
    px = (u % 1.0) * N; py = (1.0 - ((z / 2.0) % 1.0)) * N
    k = math.floor(py / PITCH); r0 = k * PITCH + 3.0; r1 = (k + 1) * PITCH - 3.0
    du = (uB - uA) / L                                              # u per metre along the face
    x0, x1 = x - 0.11, x + 0.11
    z0 = z + (py - r1) / N * 2.0; z1 = z + (py - r0) / N * 2.0
    if x0 < 0.03 or x1 > L - 0.03: continue
    bricks.append({"face": face, "A": A, "B": Bp, "n": n, "x": [x0, x1], "z": [z0, z1], "kind": kind,
                   "u": [uA + du * x0, uA + du * x1], "v": [z0 / 2.0, z1 / 2.0]})
(ROOT / "source" / "scripts" / "gs_v120_bricks.json").write_text(json.dumps(bricks, indent=1))
print(len(bricks), [(b["face"], b["kind"], round(b["x"][1] - b["x"][0], 3), round(b["z"][1] - b["z"][0], 3)) for b in bricks])
