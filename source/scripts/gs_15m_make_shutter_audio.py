# LONG PIG — ORIGINAL synthesized sounds for the security roller shutters (numpy only, no samples, no recordings):
#   lp_shutter_run.ogg   relay click + tubular motor hum (gearbox harmonics, slight load wobble) + slat rattle in the guides,
#                        9 s, faded in Lua when the motion ends earlier
#   lp_shutter_stop.ogg  end-stop clunk: bar on the stop / sill, motor brake click, short metal ring and rattle tail
#   python gs_15m_make_shutter_audio.py [<project_root>]  -> source/fivem/gabagool_sons_mlo/html/sfx/*.ogg (+ .wav masters)
import sys, json, hashlib, subprocess
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
OUT = ROOT / "source" / "fivem" / "gabagool_sons_mlo" / "html" / "sfx"
MASTER = ROOT / "source" / "audio" / "shutters"
OUT.mkdir(parents=True, exist_ok=True)
MASTER.mkdir(parents=True, exist_ok=True)
SR = 44100
rng = np.random.default_rng(20261102)


def bp(x, lo, hi, order=3):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hit(n, f_lo, f_hi, decay):
    t = np.arange(n) / SR
    return bp(rng.normal(size=n), f_lo, f_hi) * np.exp(-t / decay)


def write(name, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
    pcm = (x * 32767).astype(np.int16)
    import wave
    wav = MASTER / f"{name}.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    ogg = OUT / f"{name}.ogg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "4", str(ogg)], check=True)
    data = ogg.read_bytes()
    print(name, len(x) / SR, "s", len(data), "bytes")
    return {"name": ogg.name, "seconds": round(len(x) / SR, 2), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


rep = {"script": "source/scripts/gs_15m_make_shutter_audio.py", "origin": "original synthesis (numpy / scipy), no samples", "files": []}

# ---------------------------------------------------------------- run: 9 s
dur = 9.0
n = int(SR * dur)
t = np.arange(n) / SR
f0 = 96.0 * (1 + 0.012 * np.sin(2 * np.pi * 0.7 * t) + 0.004 * rng.normal(size=n).cumsum() / np.sqrt(n))   # load wobble
ph = 2 * np.pi * np.cumsum(f0) / SR
motor = 0.55 * np.sin(ph) + 0.30 * np.sin(2 * ph + 0.3) + 0.16 * np.sin(3 * ph + 1.1) + 0.08 * np.sin(5 * ph)
motor += 0.05 * np.sin(12.5 * ph)                                                          # gear whine
motor *= 0.75 + 0.25 * np.sin(2 * np.pi * 3.1 * t) ** 2                                   # gearbox beating
hum_noise = bp(rng.normal(size=n), 180, 1400) * 0.10
rumble = lp(rng.normal(size=n), 70) * 0.9
# slat rattle: short metallic ticks as each slat passes the guides (~13 per second, jittered)
rattle = np.zeros(n)
pos = 0.12
while pos < dur - 0.05:
    i = int(pos * SR)
    L = int(SR * 0.03)
    amp = rng.uniform(0.25, 1.0)
    seg = hit(L, 1800, 5200, rng.uniform(0.004, 0.009)) * amp + hit(L, 500, 1400, 0.012) * amp * 0.5
    rattle[i:i + L] += seg[: max(0, min(L, n - i))]
    pos += 1.0 / 13.0 * rng.uniform(0.6, 1.4)
run = 0.55 * motor + hum_noise + 0.35 * rumble + 0.75 * rattle
env = np.minimum(1.0, t / 0.25) * np.minimum(1.0, (dur - t) / 0.4)                       # soft start / tail
run *= env
relay = np.zeros(n); relay[: int(SR * 0.04)] = hit(int(SR * 0.04), 2500, 8000, 0.003) * 1.6
run += relay
rep["files"].append(write("lp_shutter_run", run))

# ---------------------------------------------------------------- stop: 1.2 s
n = int(SR * 1.2)
t = np.arange(n) / SR
thump = np.sin(2 * np.pi * 58 * t) * np.exp(-t / 0.09) * 1.2
impact = hit(n, 700, 4200, 0.05) * 0.9
ring = (np.sin(2 * np.pi * 1730 * t) * 0.07 + np.sin(2 * np.pi * 2610 * t) * 0.04) * np.exp(-t / 0.18)
tail = np.zeros(n)
for k in range(5):
    i = int(SR * (0.07 + 0.05 * k + rng.uniform(0, 0.02)))
    L = int(SR * 0.025)
    tail[i:i + L] += hit(L, 1500, 5000, 0.006) * (0.5 / (k + 1))
brake = np.zeros(n); i = int(SR * 0.16); L = int(SR * 0.02); brake[i:i + L] = hit(L, 3000, 9000, 0.002) * 0.7
stop = thump + impact + ring + tail + brake
rep["files"].append(write("lp_shutter_stop", stop))
(MASTER / "lp_shutter_audio_report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
print("DONE_SHUTTER_AUDIO")
