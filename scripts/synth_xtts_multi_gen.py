"""XTTS multi-speaker test — GEN (XPU venv): clone the fixed sentence pool for EACH speaker from its clean reference."""
import os
import json
import time

import numpy as np
import torch
import soundfile as sf

os.environ["COQUI_TOS_AGREED"] = "1"
OUT = os.environ.get("XTTS_MULTI", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_multi")

import torchaudio
def _load(p, *a, **k):
    x, sr = sf.read(str(p), dtype="float32"); x = x[None, :] if x.ndim == 1 else x.T
    return torch.from_numpy(np.ascontiguousarray(x)), sr
def _save(p, t, sr, *a, **k):
    arr = t.detach().cpu().numpy(); arr = arr.T if arr.ndim == 2 else arr; sf.write(str(p), arr, sr)
torchaudio.load = _load; torchaudio.save = _save


def main():
    man = json.load(open(os.path.join(OUT, "manifest.json")))
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
    try:
        tts = tts.to("xpu"); dev = "xpu"
    except Exception:
        dev = "cpu"
    t0 = time.time(); n = 0
    for sp, d in man["speakers"].items():
        ref = os.path.join(OUT, d["reference"])
        for si, text in enumerate(man["sentences"]):
            outp = os.path.join(OUT, f"clone_{sp}_{si}.wav")
            try:
                tts.tts_to_file(text=text, speaker_wav=ref, language="en", file_path=outp); n += 1
            except Exception as e:
                print(f"  [skip] {sp} {si}: {str(e)[:60]}")
    print(f"  GEN done on {dev}: {n} clones ({len(man['speakers'])} speakers x {len(man['sentences'])} sentences) in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
