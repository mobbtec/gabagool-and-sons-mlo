# LONG PIG — assemble the shutter preview frames (gs_40) into a GIF + an MP4 with the shutter sounds.
# Timeline (8 fps): open hold 0.75 s | /close_pig 6.5 s | closed hold 1.0 s | /open_pig 6.5 s (same frames reversed —
# smootherstep is symmetric) | open hold 0.5 s.  Overlay: command, time, progress, "Blender preview — not FiveM".
# usage: python gs_41_shutter_gif.py <frames_dir> <out_basename> <run.ogg> <stop.ogg>
import sys, json, subprocess, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

src, outbase, run_ogg, stop_ogg = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
FPS = 8
meta = json.loads((src / "frames.json").read_text())
n = len(meta["frames"])
DUR = meta["duration_s"]
fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)


def frame(i, cmd, t, p):
    im = Image.open(src / f"f{i:03d}.png").convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    d.rectangle([0, 0, W, 30], fill=(0, 0, 0, 170))
    d.text((10, 6), cmd, font=fb, fill=(255, 210, 90))
    d.text((150, 8), f"{t:4.1f} / {DUR:.1f} s", font=fs, fill=(235, 235, 235))
    x0, x1 = 260, W - 150
    d.rectangle([x0, 11, x1, 19], outline=(200, 200, 200, 220))
    d.rectangle([x0 + 1, 12, x0 + 1 + int((x1 - x0 - 2) * p), 18], fill=(150, 170, 185, 255))
    d.text((x1 + 10, 8), f"closed {round(p * 100):3d} %", font=fs, fill=(235, 235, 235))
    lab = "LONG PIG shutters - Blender preview, not FiveM"
    tw = d.textlength(lab, font=fs)
    d.rectangle([W - tw - 16, H - 24, W, H], fill=(0, 0, 0, 150))
    d.text((W - tw - 8, H - 20), lab, font=fs, fill=(230, 230, 230))
    return im


seq = []
P = [f["p"] for f in meta["frames"]]
U = [f["u"] for f in meta["frames"]]
for _ in range(6):
    seq.append(frame(0, "open", 0.0, 0.0))
for i in range(n):
    seq.append(frame(i, "/close_pig", U[i] * DUR, P[i]))
for _ in range(8):
    seq.append(frame(n - 1, "closed", DUR, 1.0))
for i in reversed(range(n)):
    seq.append(frame(i, "/open_pig", (1 - U[i]) * DUR, P[i]))
for _ in range(4):
    seq.append(frame(0, "open", DUR, 0.0))

tmp = outbase.parent / (outbase.name + "_frames")
shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
for k, im in enumerate(seq):
    im.save(tmp / f"g{k:04d}.png")
total = len(seq) / FPS
# GIF: one shared palette, light dither
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "g%04d.png"),
                "-vf", "split[a][b];[a]palettegen=max_colors=192:stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a",
                "-loop", "0", str(outbase) + ".gif"], check=True)
# MP4 with the original synthesized sounds: motor while moving (faded out at the stop), clunk at each end
t_close, t_open = 6 / FPS, (6 + n + 8) / FPS
mv = DUR
ms = lambda x: int(round(x * 1000))
fc = (f"[1:a]asplit=2[ra][rb];[2:a]asplit=2[sa][sb];"
      f"[ra]atrim=0:{mv},afade=t=out:st={mv - 0.25}:d=0.25,adelay={ms(t_close)}:all=1[r1];"
      f"[rb]atrim=0:{mv},afade=t=out:st={mv - 0.25}:d=0.25,adelay={ms(t_open)}:all=1[r2];"
      f"[sa]adelay={ms(t_close + mv)}:all=1[s1];"
      f"[sb]adelay={ms(t_open + mv)}:all=1[s2];"
      f"[r1][r2][s1][s2]amix=inputs=4:normalize=0,apad,atrim=0:{total}[a];"
      f"[0:v]pad=ceil(iw/2)*2:ceil(ih/2)*2[v]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "g%04d.png"),
                "-i", run_ogg, "-i", stop_ogg, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24", "-crf", "20", "-preset", "veryfast",
                "-c:a", "aac", "-b:a", "128k", "-shortest", str(outbase) + ".mp4"], check=True)
shutil.rmtree(tmp, ignore_errors=True)
print("frames", len(seq), "seconds", total, "->", str(outbase) + ".gif", str(outbase) + ".mp4")
