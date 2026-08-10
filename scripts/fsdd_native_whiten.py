"""Recognition through the agent's NATIVE Whiten primitive (the seeded-then-specified
matrix-primitive frozen edge, now live in the substrate). The within-class scatter W is
aggregated by the world-adapter (data summary), but the WHITENING transform — the matrix
factorisation + solve the DSL could not express — runs as the native `Whiten` Term
(s._inner.evaluate), NOT numpy. Confirms the agent's authored primitive reproduces the
derived cross-speaker fix natively.

Run: python scripts/fsdd_native_whiten.py [test_speaker] [n_per] [shrink]
"""
from __future__ import annotations
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import substrate_rs as srs
from substrate_rs import Substrate
from substrate_rs.speech import _audio
from scripts.speech_analysis_by_synthesis import load_wav, feat, DATA, FN, N_BANDS


def within_scatter(X, y, shrink):
    d = X.shape[1]; W = np.zeros((d, d)); n = 0
    for c in np.unique(y):
        Xc = X[y == c] - X[y == c].mean(0)
        W += Xc.T @ Xc; n += len(Xc)
    W /= max(n, 1)
    return (1 - shrink) * W + shrink * (np.trace(W) / d) * np.eye(d)


def native_whitener(s, W):
    """Return a fn X->L^-1 X via the NATIVE WhitenMany Term (Cholesky factored ONCE)."""
    Wmat = srs.Vec(items=[srs.Vec(items=[srs.Lit(float(v)) for v in row]) for row in W])._json
    def whiten_all(X):
        Xj = srs.Vec(items=[srs.Vec(items=[srs.Lit(float(v)) for v in x]) for x in X])._json
        return np.array([[float(v) for v in r]
                         for r in s._inner.evaluate({"type": "WhitenMany", "a": Wmat, "b": Xj}, {})])
    return whiten_all


def acc(trX, trY, teX, teY):
    Xn = trX / (np.linalg.norm(trX, axis=1, keepdims=True) + 1e-9)
    ok = 0
    for q, d in zip(teX, teY):
        qn = q / (np.linalg.norm(q) + 1e-9)
        ok += trY[int((Xn @ qn).argmax())] == d
    return ok / len(teY)


def run(test_spk, n_per, shrink, bank, s):
    files = [(os.path.join(DATA, fn), int(m.group(1)), m.group(2))
             for fn in sorted(os.listdir(DATA))
             if (m := FN.match(fn)) and int(m.group(3)) < n_per]
    trX, trY, teX, teY = [], [], [], []
    for path, digit, spk in files:
        samples, fs = load_wav(path)
        v = feat(s, bank, samples, fs).flatten().astype(np.float64)
        (teX if spk == test_spk else trX).append(v)
        (teY if spk == test_spk else trY).append(digit)
    trX = np.asarray(trX); trY = np.asarray(trY); teX = np.asarray(teX); teY = np.asarray(teY)
    base = acc(trX, trY, teX, teY)
    W = within_scatter(trX, trY, shrink)
    wh = native_whitener(s, W)                      # the agent's NATIVE WhitenMany primitive
    return base, acc(wh(trX), trY, wh(teX), teY)


def main():
    test_spk = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
    n_per = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    shrink = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
    speakers = [test_spk] if test_spk else ["george", "jackson", "theo", "nicolas"]
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    print("=" * 72)
    print(f"FSDD cross-speaker via the agent's NATIVE Whiten primitive (shrink={shrink})")
    print("=" * 72)
    bs, ws = [], []
    for spk in speakers:
        b, w = run(spk, n_per, shrink, bank, s)
        bs.append(b); ws.append(w)
        print(f"  [{spk:<9}] raw {b:5.1%}   native-Whiten {w:5.1%}   ({w-b:+.1%})")
    print("-" * 72)
    mb, mw = float(np.mean(bs)), float(np.mean(ws))
    print(f"  {'MEAN':<11}  raw {mb:5.1%}   native-Whiten {mw:5.1%}   ({mw-mb:+.1%})")
    print(f"\n  the agent's NATIVE matrix primitive {'reproduces the fix' if mw > mb else 'FAILS'} "
          f"({mw-mb:+.1%}) — whitening now runs in the substrate, not numpy.")
    print("=" * 72)


if __name__ == "__main__":
    main()
