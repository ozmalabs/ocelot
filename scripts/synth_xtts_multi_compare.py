"""XTTS multi-speaker test — COMPARE (main venv): the speaker-verification matrix. Does the clone of S verify as S?

For each speaker S, each cloned sentence: cos(clone, centroid_S) vs cos(clone, centroid_other). Verify if own-centroid wins.
Reports per-speaker verify + overall, and how close clones get to the real within-speaker band (so we see clone tightness).
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

from scripts.phase0_synthesis import wavlm

OUT = os.environ.get("XTTS_MULTI", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_multi")


def L(p):
    x, sr = sf.read(p, dtype="float32"); x = x.mean(1) if x.ndim > 1 else x
    return torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy() if sr != 16000 else x


def main():
    print("=" * 100)
    print("XTTS multi-speaker — speaker-verification matrix (clone of S vs all speakers' centroids)")
    print("=" * 100)
    man = json.load(open(os.path.join(OUT, "manifest.json")))
    spks = list(man["speakers"])
    cent = {}
    within = []
    for sp, d in man["speakers"].items():
        embs = [wavlm(L(os.path.join(OUT, p))) for p in d["enroll"]]
        c = np.mean(embs, 0); cent[sp] = c / (np.linalg.norm(c) + 1e-9)
        within += [float(embs[i] @ embs[j]) for i in range(len(embs)) for j in range(i + 1, len(embs))]
    nsent = len(man["sentences"])

    print(f"  {len(spks)} speakers; real within-speaker cos median {np.median(within):.3f} (the clone target)\n")
    verts = []; selfc = []; otherc = []
    for sp in spks:
        for si in range(nsent):
            cp = os.path.join(OUT, f"clone_{sp}_{si}.wav")
            if not os.path.exists(cp):
                continue
            e = wavlm(L(cp))
            cs = float(e @ cent[sp]); co = max(float(e @ cent[o]) for o in spks if o != sp)
            verts.append(int(cs > co)); selfc.append(cs); otherc.append(co)
        # per-speaker line
        rows = [(o, float(np.mean([wavlm(L(os.path.join(OUT, f"clone_{sp}_{si}.wav"))) for si in range(nsent)
                                   if os.path.exists(os.path.join(OUT, f"clone_{sp}_{si}.wav"))], 0) @ cent[o])) for o in spks]
        best = max(rows, key=lambda r: r[1])
        own = dict(rows)[sp]
        ok = "OK" if best[0] == sp else "x "
        print(f"    [{ok}] clone({sp}) -> own {own:+.3f}   nearest centroid: {best[0]} {best[1]:+.3f}")

    vr = 100 * np.mean(verts) if verts else 0
    print("\n" + "=" * 100)
    print(f"  CLONE speaker-verify (clone of S closest to centroid S):  {vr:.0f}%  ({sum(verts)}/{len(verts)})")
    print(f"    median cos(clone, own) {np.median(selfc):+.3f}  vs cos(clone, other) {np.median(otherc):+.3f}  |  real within {np.median(within):+.3f}")
    print("-" * 100)
    if vr >= 80:
        print(f"  XTTS CLONES IDENTITY — {vr:.0f}% verify; clones land closest to their own speaker. The 8842 single-result was hard/")
        print("  reference; XTTS-v2 captures speaker identity. Forward model viable for AbS; tighten toward the within band next.")
    elif vr >= 55:
        print(f"  PARTIAL — {vr:.0f}% verify: XTTS clones the right person more often than not, but not reliably, and well short of")
        print(f"  the within band ({np.median(selfc):+.2f} vs {np.median(within):+.2f}). Zero-shot cloning is loose for LibriSpeech ids.")
    else:
        print(f"  SYSTEMATIC UNDERPERFORMANCE — {vr:.0f}%: XTTS clones do NOT reliably verify as their target speaker (closer to others).")
        print("  Zero-shot XTTS-v2 doesn't tightly capture arbitrary LibriSpeech identities by WavLM here. Not an 8842 fluke / not XPU.")
    print("=" * 100)


if __name__ == "__main__":
    main()
