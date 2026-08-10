"""XTTS LibriTTS test — PREP: clean 24kHz references (the full-band upgrade) for the cloning verification.

The looseness suspect: LibriSpeech references are 16kHz ASR-quality, but XTTS outputs 24kHz and clones best from clean
full-band audio. LibriTTS is the SAME LibriVox speakers at 24kHz TTS-quality. Clean single-utterance 24kHz reference + enroll
per speaker; reuse synth_xtts_multi_gen / _compare (set XTTS_MULTI to this dir). Tests whether reference quality was the gap.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np
import soundfile as sf

LIBRITTS = "/home/matt/data/LibriTTS/test-clean"
OUT = os.environ.get("XTTS_MULTI", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_libritts")
N_SPK = 6
N_ENROLL = 4
SENTS = [
    "the morning sun rose over the quiet village by the river",
    "he opened the heavy door and stepped into the silent hall",
    "she could hardly believe what the stranger had just told her",
]


def main():
    os.makedirs(OUT, exist_ok=True)
    spks = sorted(os.listdir(LIBRITTS))
    # speakers with enough utterances
    chosen = []
    for sp in spks:
        wavs = glob.glob(os.path.join(LIBRITTS, sp, "**", "*.wav"), recursive=True)
        if len(wavs) >= N_ENROLL + 2:
            chosen.append((sp, wavs))
        if len(chosen) >= N_SPK:
            break

    man = {"sentences": SENTS, "speakers": {}}
    for sp, wavs in chosen:
        loaded = []
        for f in wavs[:14]:
            x, sr = sf.read(f, dtype="float32")
            if x.ndim > 1:
                x = x.mean(1)
            loaded.append((len(x), sr, x))
        loaded.sort(key=lambda z: -z[0])
        sr0 = loaded[0][1]
        rp = f"ref_{sp}.wav"; sf.write(os.path.join(OUT, rp), loaded[0][2][: 15 * sr0], sr0)   # keep native 24k
        enroll = []
        for j in range(1, 1 + N_ENROLL):
            n, sr, x = loaded[j]
            p = f"enroll_{sp}_{j}.wav"; sf.write(os.path.join(OUT, p), x, sr); enroll.append(p)
        man["speakers"][sp] = {"reference": rp, "enroll": enroll}

    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(man, fh, indent=1)
    print(f"  PREP (LibriTTS 24kHz): {len(chosen)} speakers {[s for s,_ in chosen]}; clean full-band refs + {N_ENROLL} enroll -> {OUT}")


if __name__ == "__main__":
    main()
