"""Drive the agent's #1 frontier: CATEGORICAL quantization (continuous -> discrete category
map / learned decision boundary). Categorical perception: snap the continuous, speaker-
variable acoustic cues to a SMALL set of discrete phoneme categories with sharp
boundaries; within-category (speaker) variation is discarded. So a digit's CATEGORICAL
representation (a bag of phoneme-categories) should be more SPEAKER-INVARIANT than the
continuous (soft) one.

Test: cross-speaker FSDD digit clustering, CONTINUOUS (mean-pooled frame shape) vs
CATEGORICAL (vector-quantized category histogram over the same frames), +/- NC.

Run: python scripts/fsdd_categorical.py [n_per] [K]
"""
from __future__ import annotations
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import substrate_rs as srs
from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains.cross_speaker_clustering import cluster
from scripts.fsdd_segmentation_realspeech import frames, shape
from scripts.speech_analysis_by_synthesis import load_wav, DATA, FN

N_BANDS = 24


def purity(a, t):
    return sum(Counter([t[i] for i in range(len(a)) if a[i] == c]).most_common(1)[0][1]
               for c in set(a)) / len(t)


def pur3(F, k, t):
    return float(np.mean([purity(cluster(F, k, seed=sd), t) for sd in range(3)]))


def _mat(s, A):
    return srs.Vec(items=[srs.Vec(items=[srs.Lit(float(v)) for v in r]) for r in A])._json


def nc(s, F, spk):
    d = F.shape[1]
    Sb = np.array([[float(v) for v in r] for r in s._inner.evaluate(
        {"type": "BetweenScatter", "a": _mat(s, F),
         "b": srs.Vec(items=[srs.Lit(float(a)) for a in spk])._json}, {})])
    Wr = Sb + 0.2 * (np.trace(Sb) / d) * np.eye(d)
    return np.array([[float(v) for v in r] for r in s._inner.evaluate(
        {"type": "WhitenMany", "a": _mat(s, Wr), "b": _mat(s, F)}, {})])


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)

    utt_frames, word, spk, sid = [], [], [], {}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            M = shape(frames(s, bank, load_wav(os.path.join(DATA, fn))[0]))
            utt_frames.append(M)
            word.append(int(m.group(1))); spk.append(sid.setdefault(m.group(2), len(sid)))
    k = len(set(word))

    # CONTINUOUS rep: mean-pooled frame shape per utterance (soft, keeps speaker variation).
    CONT = np.array([M.mean(0) for M in utt_frames])

    # CATEGORICAL rep: vector-quantize ALL frames to K phoneme-CATEGORIES (the learned
    # decision boundaries), then each utterance -> normalized category HISTOGRAM (bag of
    # phoneme-categories; within-category speaker variation discarded by the hard snap).
    allF = np.vstack(utt_frames)
    labels = cluster(allF, K, seed=0)
    CAT, off = [], 0
    for M in utt_frames:
        h = np.bincount(labels[off:off + len(M)], minlength=K).astype(float)
        off += len(M)
        CAT.append(h / (h.sum() + 1e-9))
    CAT = np.array(CAT)

    print("=" * 58)
    print(f"CATEGORICAL QUANTIZATION — FSDD cross-speaker, {len(word)} utts, K={K}")
    print("=" * 58)
    print(f"  {'representation':30s} {'raw':>7s} {'+NC':>7s}")
    print("-" * 58)
    print(f"  {'continuous (mean shape)':30s} {pur3(CONT,k,word):7.3f} "
          f"{pur3(nc(s,CONT,spk),k,word):7.3f}")
    print(f"  {'categorical (VQ histogram)':30s} {pur3(CAT,k,word):7.3f} "
          f"{pur3(nc(s,CAT,spk),k,word):7.3f}")
    print("=" * 58)


if __name__ == "__main__":
    main()
