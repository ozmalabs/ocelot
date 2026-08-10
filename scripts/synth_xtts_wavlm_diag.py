"""XTTS diagnostic — is the 32% FFT a CLONING failure or the isolated-word confound? WavLM speaker verification.

The per-word FFT gave XTTS-v2 ~the same as piper (32% / 1.63x) -- suspicious, since XTTS is far better. Likely confound:
isolated-word synth ("chief.") vs coarticulated real "chief" from continuous speech -> realization mismatch swamps the
speaker. WavLM is speaker-discriminative AND pools over the clip (robust to exact word realization), so it tests whether the
VOICE was cloned. Per word: cos(synth,realX) vs cos(synth,realY) [verify], and the within band cos(realX,realX2).
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import soundfile as sf
import torch
import torchaudio

from scripts.phase0_synthesis import wavlm   # WAVLM_BASE layer-6 mean-pool, L2-normalised

OUT = os.environ.get("XTTS_DATA", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_data")


def emb(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    if sr != 16000:
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy()
    return wavlm(x)


def main():
    print("=" * 100)
    print("XTTS-v2 clone — WavLM SPEAKER verification (robust to word realization)")
    print("=" * 100)
    with open(os.path.join(OUT, "manifest.json")) as fh:
        man = json.load(fh)
    verts, selfs, others, withins = [], [], [], []
    for m in man["words"]:
        w = m["word"]; sp = os.path.join(OUT, f"synth_{w}.wav")
        if not os.path.exists(sp):
            continue
        es = emb(sp); ex = emb(os.path.join(OUT, m["realX"]))
        eY = [emb(os.path.join(OUT, p)) for p in m["realY"]]
        c_self = float(es @ ex); c_other = max((float(es @ y) for y in eY), default=-1)
        selfs.append(c_self); others.append(c_other); verts.append(int(c_self > c_other))
        if "realX2" in m:
            withins.append(float(ex @ emb(os.path.join(OUT, m["realX2"]))))
        mark = "OK" if c_self > c_other else "x "
        print(f"    [{mark}] {w:<12} cos(synth,realX) {c_self:+.3f}  cos(synth,realY) {c_other:+.3f}")

    vr = 100 * np.mean(verts) if verts else 0
    print("\n" + "=" * 100)
    print(f"  WavLM speaker-verify (synth closer to realX than realY):  {vr:.0f}%")
    print(f"  median cos(synth,realX) {np.median(selfs):+.3f}  vs cos(synth,realY) {np.median(others):+.3f}  "
          f"(real within-speaker cos {np.median(withins):+.3f})" if withins else "")
    print("-" * 100)
    if vr >= 70:
        print(f"  CLONE IS GOOD (voice) — XTTS verifies as the target {vr:.0f}% in WavLM space. The 32% per-word FFT was the")
        print("  ISOLATED-WORD confound (synth word vs coarticulated real), NOT a cloning failure. Re-test FFT on NATURAL")
        print("  speech (cloned SENTENCES vs real sentences) to honour the FFT metric without the realization mismatch.")
    else:
        print(f"  CLONE WEAK even in WavLM ({vr:.0f}%) — XTTS didn't capture this target's voice here; check reference quality /")
        print("  whether word-mode degraded the conditioning. Not just an FFT artefact.")
    print("=" * 100)


if __name__ == "__main__":
    main()
