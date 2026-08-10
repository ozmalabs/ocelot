"""XTTS pipeline, step 2/3 — GEN (XPU venv): XTTS-v2 clones each held-out word from the target reference, on the B580.

Standalone (no project imports): reads the manifest, clones each word in the target's voice, writes synth_<word>.wav.
torchaudio IO is routed through soundfile (FFmpeg-8.1-proof, bypasses the broken torchcodec). Runs on XPU if available.

Run (in the XPU venv):
  <xpu-venv>/bin/python scripts/synth_xtts_gen.py
"""
import os
import json
import time

import numpy as np
import torch
import soundfile as sf

os.environ["COQUI_TOS_AGREED"] = "1"
OUT = os.environ.get("XTTS_DATA", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_data")

# ---- route torchaudio IO through soundfile (bypass torchcodec / FFmpeg 8.1) ----
import torchaudio
def _load(path, *a, **k):
    x, sr = sf.read(str(path), dtype="float32"); x = x[None, :] if x.ndim == 1 else x.T
    return torch.from_numpy(np.ascontiguousarray(x)), sr
def _save(path, t, sr, *a, **k):
    arr = t.detach().cpu().numpy(); arr = arr.T if arr.ndim == 2 else arr; sf.write(str(path), arr, sr)
torchaudio.load = _load; torchaudio.save = _save


def main():
    with open(os.path.join(OUT, "manifest.json")) as fh:
        man = json.load(fh)
    ref = os.path.join(OUT, man["reference"])
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
    dev = "cpu"
    try:
        tts = tts.to("xpu"); dev = "xpu"
    except Exception as e:
        print("  xpu move failed -> cpu:", str(e)[:80])
    print(f"  XTTS-v2 on {dev}; cloning {len(man['words'])} held-out words from {man['reference']}...", flush=True)

    # precompute the speaker conditioning ONCE from the reference (fast + consistent)
    t0 = time.time(); n = 0
    for m in man["words"]:
        w = m["word"]; outp = os.path.join(OUT, f"synth_{w}.wav")
        try:
            tts.tts_to_file(text=w + ".", speaker_wav=ref, language="en", file_path=outp)
            n += 1
        except Exception as e:
            print(f"    [skip] {w}: {type(e).__name__} {str(e)[:80]}", flush=True)
    print(f"  GEN done on {dev}: {n}/{len(man['words'])} cloned in {time.time()-t0:.0f}s -> {OUT}/synth_*.wav")


if __name__ == "__main__":
    main()
