"""Take the stack to LibriSpeech: does the spectral-SHAPE front-end (the cross-speaker
winner on FSDD) give more SPEAKER-INVARIANT units on REAL continuous read speech? No word
alignments needed — measure, label-free, over a multi-speaker slice of dev-clean:

  · SPEAKER LEAKAGE  = I(unit; speaker) / H(speaker)  — LOWER = units don't reveal the
    speaker = more cross-speaker invariant (the front-end's job).
  · PHONETIC STRUCTURE = I(unit; prev-unit) / H(unit) — HIGHER = the units carry real
    sequential (phonetic) structure, not noise (guards against degenerate collapse).

A good cross-speaker front-end gives LOW speaker leakage at COMPARABLE phonetic structure.
A/B: ENERGY cochlear envelope vs SHAPE (log-band minus per-frame mean = the filter).

Run: python scripts/librispeech_crossspeaker.py [n_spk] [n_utt] [K]
"""
from __future__ import annotations
import math
import os
import random
import sys
from collections import Counter, defaultdict

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains.cross_speaker_clustering import cluster
from scripts.fsdd_segmentation_realspeech import frames, shape

LIBRI = "/tmp/LibriSpeech/dev-clean"
N_BANDS = 24


def load8k(path):
    x, fs = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    if fs != 8000:
        x = resample_poly(x, 8000, fs).astype(np.float32)
    p = max(float(np.abs(x).max()), 1.0)
    return (x * 0.7 / p).astype(np.float32)


def mi(xs, ys):
    n = len(xs)
    pj = Counter(zip(xs, ys)); px = Counter(xs); py = Counter(ys)
    return sum((c / n) * math.log2((c / n) / (px[a] / n * py[b] / n))
               for (a, b), c in pj.items())


def entropy(xs):
    n = len(xs)
    return -sum((c / n) * math.log2(c / n) for c in Counter(xs).values())


def run(front, utt_frames, utt_spk, K):
    F = np.vstack([front(M) for M in utt_frames])
    labels = list(cluster(F, K, seed=0))
    units, spk, prev = [], [], []
    off = 0
    for M, sp in zip(utt_frames, utt_spk):
        u = labels[off:off + len(M)]; off += len(M)
        for i, ui in enumerate(u):
            units.append(ui); spk.append(sp)
            prev.append(u[i - 1] if i > 0 else -1)
    Hu = entropy(units)
    # normalise by H(unit) so the comparison is FAIR across front-ends that use different
    # unit granularity: fraction of a unit's bits that are about the SPEAKER vs about the
    # phonetic SEQUENCE. (Raw I(unit;speaker) grows with unit count, an unfair artefact.)
    leak = mi(units, spk) / Hu if Hu > 0 else 0.0
    struct = mi(units, prev) / Hu if Hu > 0 else 0.0
    return leak, struct, Hu


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    n_utt = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    spk_dirs = sorted(os.listdir(LIBRI))[:n_spk]
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    rng = random.Random(0)

    utt_frames, utt_spk = [], []
    for sp in spk_dirs:
        flacs = []
        for root, _, fs_ in os.walk(os.path.join(LIBRI, sp)):
            flacs += [os.path.join(root, f) for f in fs_ if f.endswith(".flac")]
        for p in rng.sample(flacs, min(n_utt, len(flacs))):
            x = load8k(p)
            if len(x) < 2000:
                continue
            utt_frames.append(frames(s, bank, x)); utt_spk.append(sp)
    nf = sum(len(M) for M in utt_frames)
    print("=" * 66)
    print(f"LibriSpeech dev-clean — {len(utt_frames)} utts, {n_spk} speakers, "
          f"{nf} frames, K={K}")
    print(f"  cross-speaker UNIT invariance (label-free)")
    print("=" * 66)
    print(f"  {'front-end':14s} {'speaker-leak':>13s} {'phon-struct':>12s} {'H(unit)':>9s}")
    print("-" * 66)
    for name, front in [("energy", lambda M: M), ("shape", shape)]:
        leak, struct, Hu = run(front, utt_frames, utt_spk, K)
        print(f"  {name:14s} {leak:13.3f} {struct:12.3f} {Hu:9.2f}")
    print("=" * 66)
    print("  speaker-leak LOWER = more cross-speaker invariant; phon-struct HIGHER = real units")


if __name__ == "__main__":
    main()
