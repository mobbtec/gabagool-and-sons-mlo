"""Gabagool & Sons — minimal DDS writer with full mip chain (BC1/DXT1, BC3/DXT5).

Pillow (>= 11) encodes single-level DXT1/DXT5 DDS files; this module encodes every mip level
separately and stitches them into one valid DDS file (legacy 128-byte header, no DX10 chunk),
which is what Sollumz embeds into YDR/YTD and what GTA V reads.

Usage:
    python gs_dds.py input.png output.dds [--format DXT1|DXT5] [--min-mip 4]
"""
from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path

from PIL import Image

DDSD_MIPMAPCOUNT = 0x20000
DDSCAPS_COMPLEX = 0x8
DDSCAPS_TEXTURE = 0x1000
DDSCAPS_MIPMAP = 0x400000


def _is_pow2(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def build_mips(img: Image.Image, min_size: int = 4) -> list[Image.Image]:
    """Downsample from the ORIGINAL image for every level (sharper than chained resizes)."""
    w, h = img.size
    levels = [img]
    while w > min_size and h > min_size:
        w, h = max(min_size, w // 2), max(min_size, h // 2)
        levels.append(img.resize((w, h), Image.Resampling.LANCZOS))
    return levels


def encode_dds(img: Image.Image, fmt: str = "DXT1", min_size: int = 4) -> bytes:
    fmt = fmt.upper()
    if fmt not in ("DXT1", "DXT5"):
        raise ValueError("fmt must be DXT1 or DXT5")
    img = img.convert("RGBA")
    if not (_is_pow2(img.width) and _is_pow2(img.height)):
        raise ValueError(f"texture size must be power of two, got {img.size}")
    levels = build_mips(img, min_size)
    header = None
    payload = bytearray()
    for i, lv in enumerate(levels):
        buf = io.BytesIO()
        lv.save(buf, "DDS", pixel_format=fmt)
        raw = buf.getvalue()
        if raw[:4] != b"DDS " or raw[84:88] != fmt.encode():
            raise RuntimeError(f"unexpected Pillow DDS output for level {i}")
        if header is None:
            header = bytearray(raw[:128])
        payload += raw[128:]
    flags = struct.unpack_from("<I", header, 8)[0] | DDSD_MIPMAPCOUNT
    struct.pack_into("<I", header, 8, flags)
    struct.pack_into("<I", header, 28, len(levels))
    caps = struct.unpack_from("<I", header, 108)[0] | DDSCAPS_TEXTURE | DDSCAPS_COMPLEX | DDSCAPS_MIPMAP
    struct.pack_into("<I", header, 108, caps)
    return bytes(header) + bytes(payload)


def verify_dds(data: bytes) -> dict:
    """Parse header and check the payload size matches the declared mip chain."""
    assert data[:4] == b"DDS ", "bad magic"
    h, w, mips = struct.unpack_from("<III", data, 12)[0], struct.unpack_from("<I", data, 16)[0], struct.unpack_from("<I", data, 28)[0]
    fourcc = data[84:88].decode()
    block = 8 if fourcc == "DXT1" else 16
    expected, ww, hh = 0, w, h
    for _ in range(mips):
        expected += max(1, (ww + 3) // 4) * max(1, (hh + 3) // 4) * block
        ww, hh = max(1, ww // 2), max(1, hh // 2)
    return {"width": w, "height": h, "mips": mips, "fourcc": fourcc,
            "payload": len(data) - 128, "expected_payload": expected, "ok": len(data) - 128 == expected}


def convert(src: Path, dst: Path, fmt: str = "DXT1", min_size: int = 4) -> dict:
    data = encode_dds(Image.open(src), fmt, min_size)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    info = verify_dds(data)
    info["file"] = str(dst)
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--format", default="DXT1")
    ap.add_argument("--min-mip", type=int, default=4)
    a = ap.parse_args()
    print(convert(Path(a.src), Path(a.dst), a.format, a.min_mip))
