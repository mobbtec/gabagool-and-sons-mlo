# LONG PIG 0.3.1-j: back-of-house finishes from CC0 Poly Haven sets (owner 2026-11-13: textures only from the internet
# or Higgsfield). Originals in assets/cc0/_downloads (byte-exact, md5 = Poly Haven API). This script only converts:
# resize, DDS DXT1 with full mips, normal map re-normalised, spec map = function of the roughness map.
import sys, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
DL = ROOT / "assets" / "cc0" / "_downloads"
OUT = ROOT / "source" / "textures" / "v031"
SETS = {   # out name: (asset, physical size m, spec gain, spec floor, normal flatten)
    "lp9_boh_tile": ("long_white_tiles", 1.27, 0.55, 0.06, 1.0),
    # lp9_boh_plaster: since 0.3.1-l made by gs_15t_cc0_v031l.py (painted_plaster_wall)
    "lp9_boh_floor": ("terracotta_floor_tiles", 2.08, 0.35, 0.04, 1.0),
}
rep = {}
for out, (a, size_m, gain, floor, flat) in SETS.items():
    src = {m: DL / f"{a}_{m}_2k.jpg" for m in ("diff", "nor_dx", "rough")}
    rot = out == "lp9_boh_tile"                 # long tiles laid horizontally (stacked bond) - rotate 90 deg
    d = Image.open(src["diff"]).convert("RGB").resize((1024, 1024), Image.LANCZOS)
    nimg = Image.open(src["nor_dx"]).convert("RGB").resize((512, 512), Image.LANCZOS)   # 0.3.1-l: 512 (gs_boh memory)
    rimg = Image.open(src["rough"]).convert("L")
    if rot:
        d, nimg, rimg = d.transpose(Image.ROTATE_90), nimg.transpose(Image.ROTATE_90), rimg.transpose(Image.ROTATE_90)
    n = np.asarray(nimg, float) / 255.0
    if rot:                                      # rotate the tangent-space vectors with the image: (x, y) -> (-y, x)
        n = n * 2 - 1
        n = np.stack([n[..., 1], -n[..., 0], n[..., 2]], axis=2) * 0.5 + 0.5
    v = n * 2 - 1
    v[..., :2] *= flat
    v /= np.linalg.norm(v, axis=2, keepdims=True) + 1e-9
    n = Image.fromarray(np.clip((v * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8))
    r = np.asarray(rimg.resize((512, 512), Image.LANCZOS), float) / 255.0
    s = np.clip(floor + gain * (1 - r) ** 1.5, 0, 1)
    s = Image.fromarray((s * 255).astype(np.uint8)).convert("RGB")
    for suffix, img in (("", d), ("_n", n), ("_s", s)):
        data = gs_dds.encode_dds(img, "DXT1")
        (OUT / f"{out}{suffix}.dds").write_bytes(data)
        rep[out + suffix] = {"size": list(img.size), "format": "DXT1", "sha256": hashlib.sha256(data).hexdigest(),
                             "derived_from": str(src["diff" if suffix == "" else ("nor_dx" if suffix == "_n" else "rough")].name),
                             "source": f"https://polyhaven.com/a/{a}", "licence": "CC0 1.0 (Poly Haven)", "physical_m": size_m}
old = json.loads((OUT / "cc0_v031_report.json").read_text(encoding="utf-8")) if (OUT / "cc0_v031_report.json").exists() else {}
old = {k: v for k, v in old.items() if not k.startswith("lp9_boh_plaster")}
old.update(rep)
(OUT / "cc0_v031_report.json").write_text(json.dumps(old, indent=1), encoding="utf-8")
s = Image.new("RGB", (len(SETS) * 344, 344), (20, 20, 20))
for i, out in enumerate(SETS):
    s.paste(Image.open(OUT / f"{out}.dds").convert("RGB").resize((340, 340)), (i * 344, 0))
s.save(OUT / "_cc0_prev.jpg", quality=80)
print("ok", len(rep))
