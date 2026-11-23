# LONG PIG 2.5.0: lp25_grime - local wall dirt as alpha decals (own procedural, numpy / PIL; no photo source).
# 512 x 512 DXT5, four 256 px cells: 0 hand smudge, 1 kick / scuff band, 2 drips under a sign, 3 corner dust rising from the floor.
import sys, json, hashlib, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
OUT = ROOT / "source" / "textures" / "v250"; OUT.mkdir(exist_ok=True)
N = 256
yy, xx = np.mgrid[0:N, 0:N] / float(N - 1)
edge = np.clip(np.minimum(np.minimum(xx, 1 - xx), np.minimum(yy, 1 - yy)) / 0.16, 0, 1)   # every cell fades to nothing at its border


def noise(seed, blur):
    m = max(2, int(N / (blur * 2.5)))
    g = np.random.default_rng(seed).random((m, m)).astype(np.float32)
    a = np.asarray(Image.fromarray(g, "F").resize((N, N), Image.BICUBIC), float)
    return (a - a.min()) / (np.ptp(a) + 1e-9)


def lines(seed, cnt, vert):
    im = Image.new("L", (N, N), 0); d = ImageDraw.Draw(im); r = random.Random(seed)
    for _ in range(cnt):
        if vert:
            x, y0 = r.randrange(30, N - 30), r.randrange(10, 60); L = r.randrange(60, 170)
            d.line([(x, y0), (x + r.randrange(-3, 4), y0 + L)], fill=r.randrange(90, 220), width=r.choice((2, 3, 5)))
        else:
            x, y = r.randrange(10, N - 90), r.randrange(40, N - 40); L = r.randrange(40, 120)
            d.line([(x, y), (x + L, y + r.randrange(-5, 6))], fill=r.randrange(90, 220), width=r.choice((1, 2, 3)))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(2.0)), float) / 255.0


cells = [
    np.exp(-(((xx - 0.5) / 0.26) ** 2 + ((yy - 0.5) / 0.30) ** 2)) * (0.55 + 0.45 * noise(1, 30)),
    np.clip(lines(2, 40, False) * 1.3 + 0.35 * np.exp(-((yy - 0.6) / 0.25) ** 2) * noise(3, 40), 0, 1),
    np.clip(lines(4, 9, True) * 1.2, 0, 1) * (1 - 0.5 * yy),
    np.clip((yy - 0.25) / 0.75, 0, 1) ** 1.6 * (0.5 + 0.5 * noise(5, 25)),
]
A = np.zeros((2 * N, 2 * N)); C = np.zeros((2 * N, 2 * N, 3))
for k, c in enumerate(cells):
    i, j = divmod(k, 2)
    A[i * N:(i + 1) * N, j * N:(j + 1) * N] = np.clip(c, 0, 1) * edge * (0.42, 0.50, 0.45, 0.50)[k]
    C[i * N:(i + 1) * N, j * N:(j + 1) * N] = np.array(((70, 58, 46), (52, 46, 42), (84, 66, 44), (66, 58, 50))[k]) / 255.0
im = Image.fromarray(np.uint8(np.dstack([C, A[..., None]]) * 255 + 0.5), "RGBA")
data = gs_dds.encode_dds(im, "DXT5"); (OUT / "lp25_grime.dds").write_bytes(data)
im.save(OUT / "lp25_grime_preview.png")
(OUT / "v250_textures_report.json").write_text(json.dumps({"date": "2026-11-21", "files": {"lp25_grime": {"size": [512, 512], "format": "DXT5", "bytes": len(data),
    "sha256": hashlib.sha256(data).hexdigest(), "from": "own procedural (gs_15al_v250.py)", "cells": ["smudge", "scuff", "drips", "corner_dust"]}}}, indent=1))
print("DONE", len(data))
