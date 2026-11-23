# Procedural, original prototype textures for the Gabagool & Sons greybox interior.
import sys, random, math
sys.path.insert(0, "/mnt/user-data/outputs/Gabagool_and_Sons/source/tools")
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import gs_dds
OUT = "/mnt/user-data/outputs/Gabagool_and_Sons/source/textures/proto/"
rng = np.random.default_rng(7)

def noise(w, h, scale, amp):
    n = rng.normal(0, 1, (h // scale + 2, w // scale + 2))
    img = Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BICUBIC)
    return (np.asarray(img, dtype=float) / 255 - 0.5) * amp

def save(name, arr, fmt="DXT1"):
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA" if arr.shape[2] == 4 else "RGB")
    img.save(OUT + name + ".png")
    info = gs_dds.convert(__import__("pathlib").Path(OUT + name + ".png"), __import__("pathlib").Path(OUT + name + ".dds"), fmt)
    print(name, img.size, info)

# 1. floor: classic black & white checker vinyl, 2x2 tiles per texture (texture = 0.6 m -> 30 cm tiles)
W = 512; t = W // 2
a = np.zeros((W, W, 3))
for i in range(2):
    for j in range(2):
        white = (i + j) % 2 == 0
        base = np.array([226, 222, 210]) if white else np.array([28, 28, 30])
        a[i*t:(i+1)*t, j*t:(j+1)*t] = base
n = noise(W, W, 16, 18)[..., None] + noise(W, W, 4, 6)[..., None]
a += n
# grout lines
g = 3
for k in (0, t, W - g):
    a[k:k+g, :] = [120, 118, 112]; a[:, k:k+g] = [120, 118, 112]
save("gs_proto_floor", a)

# 2. wall: warm cream plaster
W = 256
a = np.ones((W, W, 3)) * np.array([214, 196, 160])
a += noise(W, W, 32, 22)[..., None] + noise(W, W, 4, 8)[..., None]
save("gs_proto_wall", a)

# 3. wainscot: dark stained vertical wood boards (texture = 0.6 m wide, 1.0 m high)
W = 256
a = np.zeros((W, W, 3))
boards = 4
for b in range(boards):
    x0, x1 = b * W // boards, (b + 1) * W // boards
    tone = np.array([86, 52, 30]) * (0.9 + 0.2 * rng.random())
    grain = noise(W, W, 3, 30)
    grain = np.asarray(Image.fromarray(((grain + 15) * 8).clip(0, 255).astype(np.uint8)).resize((W // 16, W)).resize((W, W), Image.Resampling.BICUBIC), float) / 255 * 30 - 15
    a[:, x0:x1] = tone + grain[:, x0:x1, None]
    a[:, x0:x0 + 2] = [40, 24, 14]
a[:10, :] = [60, 36, 20]  # top rail
save("gs_proto_wood", a)

# 4. ceiling: off-white acoustic tiles, 1 tile per texture (0.6 m)
W = 256
a = np.ones((W, W, 3)) * np.array([226, 224, 216])
a += noise(W, W, 2, 14)[..., None]
a[:3, :] = [150, 148, 142]; a[:, :3] = [150, 148, 142]
save("gs_proto_ceiling", a)

# 5. trim: dark bronze anodised aluminium
W = 64
a = np.ones((W, W, 3)) * np.array([58, 48, 38]) + noise(W, W, 8, 10)[..., None]
save("gs_proto_trim", a)

# 5b. 0.1.5: clear anodised aluminium for the interior window frames / door trims (matches the grey vanilla
#     storefront frames seen from the street; the bronze trim made the frames look like a dark tunnel from outside)
W = 64
a = np.ones((W, W, 3)) * np.array([138, 140, 144]) + noise(W, W, 8, 8)[..., None]
a += np.linspace(-6, 6, W)[None, :, None]          # faint brushed gradient
save("gs_proto_alu", a)

# 6. glass: very light tint, low alpha (DXT5)
W = 64
a = np.zeros((W, W, 4)); a[..., :3] = [196, 214, 214]; a[..., 3] = 46
a[..., :3] += noise(W, W, 16, 6)[..., None]
save("gs_proto_glass", a, "DXT5")

# 7. flat normal map + glass spec map (needed by glass_env.sps)
W = 64
a = np.zeros((W, W, 3)); a[...] = [128, 128, 255]
save("gs_proto_flat_n", a)
a = np.zeros((W, W, 3)); a[...] = [200, 200, 200]
save("gs_proto_glass_s", a)
