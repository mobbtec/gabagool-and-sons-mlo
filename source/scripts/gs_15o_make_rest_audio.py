# LONG PIG v0.2.9 — ORIGINAL synthesized sounds for the WORKING RESTAURANT / AFTER HOURS / FAMILY BUSINESS features
# (numpy + scipy only, no samples, no recordings):
#   lp_bell.ogg      counter service bell: struck bell, inharmonic partials, ~1.4 s ring
#   lp_printer.ogg   receipt printer: dot-matrix head buzz in bursts + paper feed + tear
#   lp_hood.ogg      kitchen exhaust hood fan, 6 s seamless loop (motor hum + filtered airflow)
#   lp_switch.ogg    old toggle light switch click
#   lp_creak.ogg     old wooden cabinet door creak + latch
#   python gs_15o_make_rest_audio.py [<project_root>] -> source/fivem/gabagool_sons_mlo/html/sfx/*.ogg (+ .wav masters)
import sys, json, hashlib, subprocess, wave
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
OUT = ROOT / "source" / "fivem" / "gabagool_sons_mlo" / "html" / "sfx"
MASTER = ROOT / "source" / "audio" / "restaurant"
OUT.mkdir(parents=True, exist_ok=True)
MASTER.mkdir(parents=True, exist_ok=True)
SR = 44100
rng = np.random.default_rng(20261102 + 29)
REPORT = {"script": "source/scripts/gs_15o_make_rest_audio.py", "version": "0.2.9-premium", "sounds": []}


def bp(x, lo, hi, order=3):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def t_(sec):
    return np.arange(int(sec * SR)) / SR


def write(name, x, peak=0.89, desc=""):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    pcm = (x * 32767).astype(np.int16)
    wav = MASTER / f"{name}.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    ogg = OUT / f"{name}.ogg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "4", str(ogg)], check=True)
    data = ogg.read_bytes()
    REPORT["sounds"].append({"name": name, "file": f"html/sfx/{name}.ogg", "seconds": round(len(x) / SR, 2), "bytes": len(data),
                             "sha256": hashlib.sha256(data).hexdigest(), "origin": "original_synthesized", "description": desc})
    print("SND", name, round(len(x) / SR, 2), "s", len(data), "B")


# ---- counter bell: strike transient + inharmonic partials of a small brass dome
t = t_(1.6)
f0 = 2093.0
bell = np.zeros_like(t)
for ratio, amp, dec in ((1.0, 1.0, 0.55), (2.32, 0.55, 0.32), (3.71, 0.32, 0.20), (5.12, 0.18, 0.12), (0.51, 0.12, 0.8)):
    bell += amp * np.sin(2 * np.pi * f0 * ratio * t + rng.uniform(0, 6.28)) * np.exp(-t / dec)
bell *= 1.0 + 0.04 * np.sin(2 * np.pi * 5.5 * t)                     # slight beating
strike = bp(rng.normal(size=t.size), 3000, 9000) * np.exp(-t / 0.004) * 0.6
write("lp_bell", bell + strike, desc="service bell ding")

# ---- receipt printer: 6 bursts of head buzz (impulse train ~ 900 Hz), feed motor, tear
t = t_(1.9)
x = np.zeros_like(t)
for k in range(6):
    a, b = 0.05 + k * 0.21, 0.05 + k * 0.21 + 0.16
    m = (t >= a) & (t < b)
    tt = t[m] - a
    imp = (np.sin(2 * np.pi * 880 * tt) > 0.92).astype(float) * 0.9 + (np.sin(2 * np.pi * 1320 * tt) > 0.95) * 0.5
    x[m] += bp(imp, 600, 6000) * (0.8 + 0.2 * rng.random())
feed = (t > 1.30) & (t < 1.62)
x[feed] += bp(rng.normal(size=feed.sum()), 150, 900) * 0.25 + 0.15 * np.sin(2 * np.pi * 110 * t[feed])
tear = (t > 1.70) & (t < 1.80)
x[tear] += bp(rng.normal(size=tear.sum()), 1500, 7000) * np.linspace(1, 0.2, tear.sum()) * 0.8
write("lp_printer", x, peak=0.8, desc="receipt printer")

# ---- hood fan loop (seamless: integer cycles, noise faded across the seam)
dur = 6.0
t = t_(dur)
hum = 0.35 * np.sin(2 * np.pi * 100 * t) + 0.18 * np.sin(2 * np.pi * 200 * t) + 0.10 * np.sin(2 * np.pi * 50 * t)
blade = 0.10 * np.sin(2 * np.pi * 24 * t) * np.sin(2 * np.pi * 300 * t)
air = lp(bp(rng.normal(size=t.size), 80, 2500), 1800) * 0.9
n = int(0.5 * SR)                                                     # crossfade the noise ends -> no click at the loop point
fade = np.linspace(0, 1, n)
air[:n] = air[:n] * fade + air[-n:] * (1 - fade)
air = air[:t.size]
write("lp_hood", hum + blade + air, peak=0.6, desc="kitchen hood fan loop")

# ---- switch click
t = t_(0.25)
click = bp(rng.normal(size=t.size), 1200, 8000) * np.exp(-t / 0.006) + 0.4 * bp(rng.normal(size=t.size), 200, 1500) * np.exp(-(t - 0.03).clip(0) / 0.01) * (t > 0.03)
write("lp_switch", click, peak=0.7, desc="toggle switch")

# ---- cabinet creak + latch
t = t_(1.1)
f = 180 + 120 * np.sin(2 * np.pi * 1.3 * t) + 40 * rng.normal(size=t.size).cumsum() / np.sqrt(np.arange(1, t.size + 1))
phase = 2 * np.pi * np.cumsum(f) / SR
creak = np.sign(np.sin(phase)) * 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t)) * np.exp(-((t - 0.45) / 0.35) ** 2)
creak = bp(creak, 300, 4000)
latch = bp(rng.normal(size=t.size), 900, 6000) * np.exp(-(t - 0.02).clip(0) / 0.008) * (t > 0.02)
write("lp_creak", creak + latch * 0.8, peak=0.7, desc="cabinet door creak")

(MASTER / "lp_restaurant_audio_report.json").write_text(json.dumps(REPORT, indent=1))
