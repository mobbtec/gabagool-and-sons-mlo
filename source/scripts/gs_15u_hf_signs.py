# LONG PIG 0.3.1-n: Higgsfield pictures (owner's account, free allowance) into the notice / banner atlases.
# cork board -> lp4_notices cell 7; letter boards -> lp4_notices right column; banner -> lp6_atlas top strip.
# Originals: source/textures/v031/hf_wall/*_hf.png. Backups of the old atlases: backups/pre031l_20261113/*_pre_n.*
import sys, json, hashlib
from pathlib import Path
from PIL import Image, ImageEnhance
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source" / "tools"))
import gs_dds
HF = ROOT / "source" / "textures" / "v031" / "hf_wall"
BK = ROOT / "backups" / "pre031l_20261113"
rep = {}


def fit(img, w, h, sat=0.92, bri=0.96):
    img = img.convert("RGB")
    r = w / h
    iw, ih = img.size
    if iw / ih > r:
        nw = int(round(ih * r)); x = (iw - nw) // 2; img = img.crop((x, 0, x + nw, ih))
    else:
        nh = int(round(iw / r)); y = (ih - nh) // 2; img = img.crop((0, y, iw, y + nh))
    img = img.resize((w, h), Image.LANCZOS)
    return ImageEnhance.Brightness(ImageEnhance.Color(img).enhance(sat)).enhance(bri)


n = Image.open(BK / "lp4_notices_pre_n.dds").convert("RGB")
# 0.3.1-o (revision): *_hf2 / staffboard_hf win
for names, box in ((("staffboard_hf", "cork_hf"), (256, 512, 512, 768)), (("board_specials_hf2", "board_specials_hf"), (768, 0, 1024, 512)),
                   (("board_sandwiches_hf2", "board_sandwiches_hf"), (768, 512, 1024, 1024))):
    name = next((n_ for n_ in names if (HF / f"{n_}.png").exists()), names[-1])
    p = HF / f"{name}.png"
    if p.exists():
        n.paste(fit(Image.open(p), box[2] - box[0], box[3] - box[1]), box[:2])
        rep[name] = {"into": "lp4_notices", "box": box, "sha256_src": hashlib.sha256(p.read_bytes()).hexdigest()}
data = gs_dds.encode_dds(n, "DXT1")
(ROOT / "source" / "textures" / "v025" / "lp4_notices.dds").write_bytes(data)
rep["lp4_notices"] = {"sha256": hashlib.sha256(data).hexdigest(), "size": list(n.size)}
a = Image.open(BK / "lp6_atlas_pre_n.dds").convert("RGB")
p = HF / "banner_hf.png"
if p.exists():
    a.paste(fit(Image.open(p), 1024, 136, sat=0.85, bri=0.92), (0, 0))
    rep["banner_hf"] = {"into": "lp6_atlas", "box": (0, 0, 1024, 136), "sha256_src": hashlib.sha256(p.read_bytes()).hexdigest()}
data = gs_dds.encode_dds(a, "DXT1")
(ROOT / "source" / "textures" / "v027" / "lp6_atlas.dds").write_bytes(data)
a.save(ROOT / "source" / "textures" / "v027" / "lp6_atlas.png")
rep["lp6_atlas"] = {"sha256": hashlib.sha256(data).hexdigest(), "size": list(a.size)}
(ROOT / "source" / "textures" / "v031" / "hf_signs_report.json").write_text(json.dumps(rep, indent=1))
pv = Image.new("RGB", (1200, 600)); pv.paste(n.resize((600, 600)), (0, 0)); pv.paste(a.resize((600, 600)), (600, 0))
pv.save(ROOT / "docs" / "_raw" / "v031l" / "signs_after.jpg", quality=85)
print(sorted(rep))
