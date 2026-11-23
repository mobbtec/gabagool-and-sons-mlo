# Converts native ytyp/ymap/ybn/ydr files of a working reference resource to CodeWalker XML (via szio),
# so their structure can be compared with ours. Runs inside Blender (needs PyMateria for native input).
#   exec(open(r"D:\Gabagool_and_Sons\source\scripts\gs_23_dump_reference_xml.py", encoding="utf-8").read())
import os, traceback
from pathlib import Path
import szio
from szio.gta5 import AssetTarget, AssetFormat, AssetVersion

ROOT = Path(os.environ.get("GS_ROOT", r"D:\Gabagool_and_Sons"))
JOBS = [
    (ROOT / "build" / "dealer_map" / "stream", ["concess_free_patoche_milo_.ymap", "concess_free_patoche.ytyp", "patoche_free_door1.ydr"]),
    (ROOT / "build" / "hospital_map" / "stream", ["rc12b_hospitalinterior.ymap"]),
    (ROOT / "build" / "gabagool_sons_mlo" / "stream", ["gabagool_sons_mlo.ymap", "gabagool_sons_mlo.ytyp"]),
    (ROOT / "build" / "gabagool_sons_mlo" / "stream" / "mlo", ["gs_proto_door.ydr"]),
]
OUT = ROOT / "reference_other_xml"
OUT.mkdir(parents=True, exist_ok=True)
log = []
for folder, names in JOBS:
    for n in names:
        p = folder / n
        try:
            a = szio.try_load_asset(p)
            stem, ext = n.rsplit(".", 1)
            sub = OUT / folder.parts[-2] if folder.name in ("stream", "mlo") else OUT
            sub = OUT / (folder.parent.name if folder.name == "stream" else folder.parent.parent.name)
            sub.mkdir(parents=True, exist_ok=True)
            szio.save_asset(a, [AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8)], sub, stem)
            log.append(f"OK   {p} -> {sub}")
        except Exception:
            log.append(f"FAIL {p}\n{traceback.format_exc()[-500:]}")
(OUT / "_dump_log.txt").write_text("\n".join(log), encoding="utf-8")
print("GS_DUMP_DONE\n" + "\n".join(log))
