# LONG PIG — v0.2.3 streaming budget: 1024 px copies of our own 2048 px deli-food atlas (lp2_food / lp2_food_n),
# so gs_v021_hall.ydr stays under FiveM's 16 MiB physical-memory warning (native v0.2.3 build: 17.5 MiB).
# Source = ORIGINAL procedural atlas (gs_15_make_v021_textures.py); nothing third-party. Appends to the v023 report,
# then run gs_15d_register_v023.py to refresh assets/registry.json + CREDITS.md.
#   python gs_15e_stream_sizes_v023.py [<project_root>]
import sys, json, hashlib
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds  # noqa: E402

V021 = ROOT / "source" / "textures" / "v021"
OUT = ROOT / "source" / "textures" / "v023"
REP = OUT / "lp3_textures_report.json"
SIZE = 1024
JOBS = [("lp3_food", "lp2_food", "diffuse"), ("lp3_food_n", "lp2_food_n", "normal")]

rep = json.loads(REP.read_text(encoding="utf-8"))
names = {n for n, _, _ in JOBS}
rep["textures"] = [t for t in rep["textures"] if t["name"] not in names]
for name, src, role in JOBS:
    img = Image.open(V021 / f"{src}.png").convert("RGB").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    if role == "normal":  # re-normalise the filtered tangent-space vectors
        n = np.asarray(img, dtype=np.float64) / 127.5 - 1.0
        n /= np.linalg.norm(n, axis=2, keepdims=True).clip(1e-6)
        img = Image.fromarray(((n + 1.0) * 127.5).clip(0, 255).round().astype(np.uint8), "RGB")
    png = OUT / f"{name}.png"
    img.save(png)
    gs_dds.convert(png, OUT / f"{name}.dds", "DXT1")
    data = (OUT / f"{name}.dds").read_bytes()
    rep["textures"].append({"name": name, "file": f"{name}.dds", "size": [SIZE, SIZE], "format": "DXT1", "role": role,
                            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                            "derived_from": [f"source/textures/v021/{src}.png"], "origin": "original_procedural",
                            "operations": f"streaming copy of our original {src} (2048 -> {SIZE}, Lanczos"
                                          + (", re-normalised" if role == "normal" else "") + ")"})
    print("TEX", name, SIZE, len(data))
REP.write_text(json.dumps(rep, indent=1), encoding="utf-8")
print("GS15E_DONE", len(JOBS))
