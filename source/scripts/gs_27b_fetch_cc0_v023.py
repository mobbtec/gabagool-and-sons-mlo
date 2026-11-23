# LONG PIG — v0.2.3: download two CC0 ambientCG sets for the 90s lobby walls (user request 2026-11-01 14:08).
# Blender 5.1 console on the PC (plain Python urllib, no game files involved):
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_27b_fetch_cc0_v023.py", encoding="utf-8").read())
# Writes (nothing else is touched):
#   assets/cc0/_downloads/<file>                    originals, byte-exact, never edited
#   assets/cc0/_downloads/fetch_manifest.json       url, bytes, md5 (Poly Haven publishes it), sha256, time
#   assets/licenses/polyhaven_license.html          license page snapshots (+ sha256 in the manifest)
#   assets/licenses/ambientcg_license.html
#   assets/cc0/_downloads/info_<asset>.json          platform metadata of each asset (authors, dates)
import os, json, time, hashlib, urllib.request, traceback
from pathlib import Path

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
DL = ROOT / "assets" / "cc0" / "_downloads"
LIC = ROOT / "assets" / "licenses"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LONGPIG-asset-fetch/1.0"}
PH = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/"
FILES = [
    # v0.2.3 (user request 2026-11-01 14:08 "find the textures on the internet"): 90s lobby walls
    ("ambientcg", "Tiles010", "https://ambientcg.com/get?file=Tiles010_1K-JPG.zip", 4331091, None),
    ("ambientcg", "PaintedBricks004", "https://ambientcg.com/get?file=PaintedBricks004_1K-JPG.zip", 6964286, None),
]
LICENSES = [("polyhaven", "https://polyhaven.com/license", "polyhaven_license.html"),
            ("ambientcg", "https://docs.ambientcg.com/license/", "ambientcg_license.html")]
INFO = {"Tiles010": "https://ambientcg.com/api/v2/full_json?id=Tiles010&include=downloadData,tagData",
        "PaintedBricks004": "https://ambientcg.com/api/v2/full_json?id=PaintedBricks004&include=downloadData,tagData"}


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.geturl()


def name_of(url):
    return url.split("file=")[-1] if "file=" in url else url.rsplit("/", 1)[-1]


DL.mkdir(parents=True, exist_ok=True)
LIC.mkdir(parents=True, exist_ok=True)
M = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "approved": "user, chat 2026-11-01 14:08 (v0.2.3 walls: Tiles010 + PaintedBricks004)",
     "files": [], "licenses": [], "info": {}, "errors": []}
for plat, asset, url, size, md5 in FILES:
    fn = name_of(url)
    dst = DL / fn
    rec = {"platform": plat, "asset": asset, "file": f"assets/cc0/_downloads/{fn}", "url": url, "expected_bytes": size,
           "md5_published": md5}
    try:
        if dst.exists() and dst.stat().st_size == size:
            data = dst.read_bytes()
            rec["note"] = "already present"
        else:
            data, final = get(url)
            rec["final_url"] = final
            tmp = dst.with_suffix(dst.suffix + ".part")
            tmp.write_bytes(data)
            os.replace(tmp, dst)
        rec["bytes"] = len(data)
        rec["md5"] = hashlib.md5(data).hexdigest()
        rec["sha256"] = hashlib.sha256(data).hexdigest()
        rec["ok"] = len(data) == size and (md5 is None or rec["md5"] == md5)
        rec["retrieved"] = time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        rec["ok"] = False
        M["errors"].append(f"{fn}: " + traceback.format_exc()[-300:])
    M["files"].append(rec)
    print("[gs_fetch]", fn, rec.get("bytes"), "OK" if rec["ok"] else "FAIL", flush=True)

for plat, url, fn in LICENSES:
    try:
        data, final = get(url)
        (LIC / fn).write_bytes(data)
        M["licenses"].append({"platform": plat, "url": url, "final_url": final, "file": f"assets/licenses/{fn}",
                              "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                              "retrieved": time.strftime("%Y-%m-%d %H:%M:%S")})
    except Exception:
        M["errors"].append(f"license {plat}: " + traceback.format_exc()[-300:])
for asset, url in INFO.items():
    try:
        data, _ = get(url)
        p = DL / f"info_{asset}.json"
        p.write_bytes(data)
        M["info"][asset] = {"url": url, "file": f"assets/cc0/_downloads/info_{asset}.json",
                            "sha256": hashlib.sha256(data).hexdigest()}
    except Exception:
        M["errors"].append(f"info {asset}: " + traceback.format_exc()[-300:])

M["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
M["all_ok"] = all(f["ok"] for f in M["files"]) and len(M["licenses"]) == 2 and not M["errors"]
with open(DL / "fetch_manifest_v023.json", "w", encoding="utf-8") as fh:
    json.dump(M, fh, indent=1)
print("GS_FETCH_DONE all_ok=%s files=%d/%d bytes=%d licenses=%d errors=%d" % (
    M["all_ok"], sum(f["ok"] for f in M["files"]), len(FILES), sum(f.get("bytes", 0) for f in M["files"]),
    len(M["licenses"]), len(M["errors"])))
