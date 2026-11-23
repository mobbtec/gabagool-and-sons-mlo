# LONG PIG — download the CC0 texture sets approved for the Vertical Slice (user approval 2026-10-30 18:2x).
# Blender 5.1 console on the PC (plain Python urllib, no game files involved):
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_27_fetch_cc0.py", encoding="utf-8").read())
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
    # (platform, asset, url, expected bytes, md5 or None)
    ("polyhaven", "brown_leather", PH + "brown_leather/brown_leather_albedo_2k.jpg", 2137518, "1bd381c43817743a2affdd1ce2d193c7"),
    ("polyhaven", "brown_leather", PH + "brown_leather/brown_leather_nor_dx_2k.jpg", 3143818, "f0ae424b5a80c601c250b8d125914bc2"),
    ("polyhaven", "brown_leather", PH + "brown_leather/brown_leather_rough_2k.jpg", 2801956, "95b48a5c95b02d87dadee46c26f1cfb5"),
    ("polyhaven", "kitchen_wood", PH + "kitchen_wood/kitchen_wood_diff_2k.jpg", 3557700, "e23ef649eda9bf19c44126b3ffdaaa8a"),
    ("polyhaven", "kitchen_wood", PH + "kitchen_wood/kitchen_wood_nor_dx_2k.jpg", 2915703, "d82cf49ab52367cd7b9167c5ab2c7625"),
    ("polyhaven", "kitchen_wood", PH + "kitchen_wood/kitchen_wood_rough_2k.jpg", 3520436, "c15c5f17129ea633ae63422e7d61c212"),
    ("polyhaven", "beige_wall_001", PH + "beige_wall_001/beige_wall_001_diff_2k.jpg", 235868, "c927ac1136767f1df758ae064f50a2d1"),
    ("polyhaven", "beige_wall_001", PH + "beige_wall_001/beige_wall_001_nor_dx_2k.jpg", 829245, "668e5b855f27a29f30ebdae30e8209c0"),
    ("polyhaven", "beige_wall_001", PH + "beige_wall_001/beige_wall_001_rough_2k.jpg", 656368, "6c2a7eb786d436459c231e9d230fb3cc"),
    ("ambientcg", "Tiles139", "https://ambientcg.com/get?file=Tiles139_2K-JPG.zip", 16290912, None),
    ("ambientcg", "OfficeCeiling003", "https://ambientcg.com/get?file=OfficeCeiling003_1K-JPG.zip", 7212931, None),
    ("ambientcg", "Terrazzo004", "https://ambientcg.com/get?file=Terrazzo004_1K-JPG.zip", 6719878, None),
    ("ambientcg", "Metal012", "https://ambientcg.com/get?file=Metal012_1K-JPG.zip", 3961854, None),
]
LICENSES = [("polyhaven", "https://polyhaven.com/license", "polyhaven_license.html"),
            ("ambientcg", "https://docs.ambientcg.com/license/", "ambientcg_license.html")]
INFO = {"brown_leather": "https://api.polyhaven.com/info/brown_leather",
        "kitchen_wood": "https://api.polyhaven.com/info/kitchen_wood",
        "beige_wall_001": "https://api.polyhaven.com/info/beige_wall_001",
        "Tiles139": "https://ambientcg.com/api/v2/full_json?id=Tiles139&include=downloadData,tagData",
        "OfficeCeiling003": "https://ambientcg.com/api/v2/full_json?id=OfficeCeiling003&include=downloadData,tagData",
        "Terrazzo004": "https://ambientcg.com/api/v2/full_json?id=Terrazzo004&include=downloadData,tagData",
        "Metal012": "https://ambientcg.com/api/v2/full_json?id=Metal012&include=downloadData,tagData"}


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.geturl()


def name_of(url):
    return url.split("file=")[-1] if "file=" in url else url.rsplit("/", 1)[-1]


DL.mkdir(parents=True, exist_ok=True)
LIC.mkdir(parents=True, exist_ok=True)
M = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "approved": "user, chat 2026-10-30 (Vertical Slice CC0 list, 7 sets)",
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
with open(DL / "fetch_manifest.json", "w", encoding="utf-8") as fh:
    json.dump(M, fh, indent=1)
print("GS_FETCH_DONE all_ok=%s files=%d/%d bytes=%d licenses=%d errors=%d" % (
    M["all_ok"], sum(f["ok"] for f in M["files"]), len(FILES), sum(f.get("bytes", 0) for f in M["files"]),
    len(M["licenses"]), len(M["errors"])))
