# LONG PIG 0.3.1-l: own synthesized water-drip sounds (no samples): a drop hitting water in a bucket = short rising
# "plink" (bubble resonance) + a tiny noise splash; three variants. numpy -> 16-bit WAV -> OGG (ffmpeg).
import subprocess, wave, hashlib, json
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "source" / "fivem" / "gabagool_sons_mlo" / "html" / "sfx"
TMP = ROOT / "docs" / "_raw" / "v031l"
SR = 44100
rng = np.random.default_rng(31)
rep = {}
for k, (f0, f1, dec, splash, delay2) in enumerate(((820, 1650, 0.055, 0.25, 0.09), (1050, 2100, 0.045, 0.18, 0.0),
                                                     (700, 1400, 0.070, 0.30, 0.13)), start=1):
    n = int(SR * 0.45)
    t = np.arange(n) / SR
    # bubble: exponential pitch rise f0 -> f1 over ~40 ms, exponential decay
    f = f0 * (f1 / f0) ** np.clip(t / 0.04, 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    plink = np.sin(ph) * np.exp(-t / dec)
    # impact click + splash (filtered noise burst)
    nz = rng.standard_normal(n)
    nz = np.convolve(nz, np.ones(6) / 6, mode="same") - np.convolve(nz, np.ones(60) / 60, mode="same")
    spl = nz * np.exp(-t / 0.012) * splash
    sig = plink + spl
    if delay2:                                                    # a smaller second drop / ripple
        d = int(SR * delay2)
        sig[d:] += 0.35 * (np.sin(2 * np.pi * np.cumsum(f[: n - d] * 1.25) / SR) * np.exp(-t[: n - d] / (dec * 0.7)))
    sig = np.convolve(sig, np.r_[1.0, np.zeros(int(SR * 0.011)), 0.22, np.zeros(int(SR * 0.017)), 0.12], mode="full")[:n]   # small room
    sig *= np.clip(t / 0.0015, 0, 1)
    sig = sig / np.abs(sig).max() * 0.8
    pcm = (sig * 32767).astype(np.int16)
    wav = TMP / f"lp_drip{k}.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    ogg = OUT / f"lp_drip{k}.ogg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "4", str(ogg)], check=True)
    rep[ogg.name] = {"bytes": ogg.stat().st_size, "sha256": hashlib.sha256(ogg.read_bytes()).hexdigest(), "origin": "own synthesis (numpy)"}
(TMP / "drip_sfx_report.json").write_text(json.dumps(rep, indent=1))
print(rep)
