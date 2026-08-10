"""Cross-speaker unit invariance on VCTK PARALLEL utterances — the SAME sentence (text_id)
read by many speakers, so content is HELD FIXED and I(unit;speaker) within a sentence is
PURE speaker leakage (no content confound, unlike non-parallel LibriSpeech).

Metric (label-free): build a global unit codebook; per sentence (text_id, all speakers
saying the same words), SPEAKER LEAKAGE = I(unit;speaker)/H(unit) — LOWER = the same
phoneme maps to the same unit regardless of speaker = cross-speaker invariant. Average
over sentences. A/B: ENERGY cochlear envelope vs SHAPE (log-band minus per-frame mean).

Run: python scripts/vctk_crossspeaker.py [n_text] [K]
"""
from __future__ import annotations
import glob
import io
import math
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains.cross_speaker_clustering import cluster
from scripts.fsdd_segmentation_realspeech import frames, shape

N_BANDS = 24


def load8k(b):
    x, fs = sf.read(io.BytesIO(b), dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    if fs != 8000:
        from math import gcd
        g = gcd(fs, 8000)
        x = resample_poly(x, 8000 // g, fs // g).astype(np.float32)
    p = max(float(np.abs(x).max()), 1.0)
    return (x * 0.7 / p).astype(np.float32)


def mi(xs, ys):
    n = len(xs)
    if n == 0:
        return 0.0
    pj = Counter(zip(xs, ys)); px = Counter(xs); py = Counter(ys)
    return sum((c / n) * math.log2((c / n) / (px[a] / n * py[b] / n))
               for (a, b), c in pj.items())


def entropy(xs):
    n = len(xs)
    return -sum((c / n) * math.log2(c / n) for c in Counter(xs).values()) if n else 0.0


def run(front, utt_frames, utt_text, utt_spk, K):
    F = np.vstack([front(M) for M in utt_frames])
    labels = list(cluster(F, K, seed=0))
    # split units per utterance, regroup by text_id
    by_text = {}
    off = 0
    for M, tid, sp in zip(utt_frames, utt_text, utt_spk):
        u = labels[off:off + len(M)]; off += len(M)
        d = by_text.setdefault(tid, {"u": [], "s": []})
        d["u"].extend(u); d["s"].extend([sp] * len(u))
    leaks, structs = [], []
    for d in by_text.values():
        u, sp = d["u"], d["s"]
        Hu = entropy(u)
        if Hu <= 0 or len(set(sp)) < 2:
            continue
        leaks.append(mi(u, sp) / Hu)
        prev = [u[i - 1] if i > 0 else -1 for i in range(len(u))]
        structs.append(mi(u, prev) / Hu)
    return float(np.mean(leaks)), float(np.mean(structs))


def main():
    n_text = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    d = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob("/tmp/vctk48/*.parquet"))],
                  ignore_index=True)
    vc = d.groupby("text_id").speaker_id.nunique().sort_values(ascending=False)
    texts = list(vc[vc >= 6].index[:n_text])
    sub = d[d.text_id.isin(texts)]

    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    utt_frames, utt_text, utt_spk = [], [], []
    for _, row in sub.iterrows():
        x = load8k(row["audio"]["bytes"])
        if len(x) < 2000:
            continue
        utt_frames.append(frames(s, bank, x))
        utt_text.append(row["text_id"]); utt_spk.append(row["speaker_id"])
        try:
            s.memory_drop_disposable()        # reclaim the per-utterance AudioBuffers
        except Exception:
            pass
    nf = sum(len(M) for M in utt_frames)
    print("=" * 66)
    print(f"VCTK PARALLEL — {len(utt_frames)} utts, {len(texts)} sentences x up to "
          f"{d.speaker_id.nunique()} speakers, {nf} frames, K={K}")
    print(f"  speaker leakage WITHIN-sentence (content fixed; pure speaker, no confound)")
    print("=" * 66)
    print(f"  {'front-end':14s} {'speaker-leak':>13s} {'phon-struct':>12s}")
    print("-" * 66)
    for name, front in [("energy", lambda M: M), ("shape", shape)]:
        leak, struct = run(front, utt_frames, utt_text, utt_spk, K)
        print(f"  {name:14s} {leak:13.3f} {struct:12.3f}")
    print("=" * 66)
    print("  speaker-leak LOWER = same phoneme -> same unit across speakers = invariant")


if __name__ == "__main__":
    main()
