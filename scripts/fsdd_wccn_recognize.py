"""Measure the fix the agent DERIVED once it was seeded the projection concept.

After seeding linear_discriminant_analysis + the discriminant_projection shape, the
agent's live derivation (agent_derives_xspeaker) flipped from frozen edge to deriving:
"a structured nuisance in a within-class scatter DIRECTION is removed by WHITENING by
the within-class covariance / projecting onto its complement (Fisher/LDA/WCCN)." This
enacts that derived transform and measures it on FSDD cross-speaker.

WCCN: W = within-class (within-digit) scatter = avg per-digit covariance — the
directions a digit's tokens spread across SPEAKERS. Whiten by W^(-1/2) so those
within-class (speaker) directions are suppressed; then 1-NN. Baseline = the same flat
1-NN with NO whitening.

The agent derived the TRANSFORM (the shape); this shell computes W^(-1/2) (the linear
algebra the substrate lacks as a primitive — a separate frozen edge) and measures.

Run: python scripts/fsdd_wccn_recognize.py [test_speaker] [n_per] [shrink]
"""
from __future__ import annotations
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from scripts.speech_analysis_by_synthesis import load_wav, feat, DATA, FN, N_BANDS


def within_class_whitener(X, y, shrink):
    """W = within-class scatter; return A = W^(-1/2) (symmetric whitening)."""
    d = X.shape[1]
    W = np.zeros((d, d))
    n = 0
    for c in np.unique(y):
        Xc = X[y == c]
        Xc = Xc - Xc.mean(0)
        W += Xc.T @ Xc
        n += len(Xc)
    W /= max(n, 1)
    W = (1 - shrink) * W + shrink * (np.trace(W) / d) * np.eye(d)   # shrinkage reg
    vals, vecs = np.linalg.eigh(W)
    vals = np.clip(vals, 1e-8, None)
    return vecs @ np.diag(vals ** -0.5) @ vecs.T


def acc(trX, trY, teX, teY):
    Xn = trX / (np.linalg.norm(trX, axis=1, keepdims=True) + 1e-9)
    ok = 0
    for q, d in zip(teX, teY):
        qn = q / (np.linalg.norm(q) + 1e-9)
        ok += trY[int((Xn @ qn).argmax())] == d
    return ok / len(teY)


def run(test_spk, n_per, shrink, bank, s):
    files = []
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            files.append((os.path.join(DATA, fn), int(m.group(1)), m.group(2)))
    trX, trY, teX, teY = [], [], [], []
    for path, digit, spk in files:
        samples, fs = load_wav(path)
        v = feat(s, bank, samples, fs).flatten().astype(np.float64)
        if spk == test_spk:
            teX.append(v); teY.append(digit)
        else:
            trX.append(v); trY.append(digit)
    trX = np.asarray(trX); trY = np.asarray(trY)
    teX = np.asarray(teX); teY = np.asarray(teY)
    base = acc(trX, trY, teX, teY)
    A = within_class_whitener(trX, trY, shrink)
    w = acc(trX @ A.T, trY, teX @ A.T, teY)
    return base, w


def main():
    test_spk = sys.argv[1] if len(sys.argv) > 1 else None
    n_per = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    shrink = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
    speakers = [test_spk] if test_spk else ["george", "jackson", "theo", "nicolas"]
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    print("=" * 74)
    print(f"FSDD cross-speaker — the agent's DERIVED fix: WCCN whitening (shrink={shrink})")
    print(f"  {n_per}/digit/speaker; flat 1-NN; baseline = no whitening")
    print("=" * 74)
    bs, ws = [], []
    for spk in speakers:
        b, w = run(spk, n_per, shrink, bank, s)
        bs.append(b); ws.append(w)
        print(f"  [{spk:<9}] raw {b:5.1%}   WCCN-whitened {w:5.1%}   ({w-b:+.1%})")
    print("-" * 74)
    mb, mw = float(np.mean(bs)), float(np.mean(ws))
    print(f"  {'MEAN':<11}  raw {mb:5.1%}   WCCN-whitened {mw:5.1%}   ({mw-mb:+.1%})")
    print(f"\n  the agent's seeded-then-derived projection {'HELPS' if mw > mb else 'does NOT help'} "
          f"cross-speaker ({mw-mb:+.1%}).")
    print("=" * 74)


if __name__ == "__main__":
    main()
