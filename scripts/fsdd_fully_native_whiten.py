"""FULLY-NATIVE cross-speaker whitening: BOTH matrix ops the agent specified run in the
substrate now — WithinScatter (the covariance primitive, computes W) AND Whiten (the
factorisation+solve, applies L^-1). The only numpy left is the world-adapter (cochlea
features via held ops, data marshalling, the cosine-NN readout). The derived cross-
speaker fix is computed entirely by agent-authored native primitives.

Run: python scripts/fsdd_fully_native_whiten.py [test_speaker] [n_per]
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


def _vec(xs):
    return srs.Vec(items=[srs.Lit(float(v)) for v in xs])


def acc(trX, trY, teX, teY):
    Xn = trX / (np.linalg.norm(trX, axis=1, keepdims=True) + 1e-9)
    ok = sum(trY[int((Xn @ (q / (np.linalg.norm(q) + 1e-9))).argmax())] == d
             for q, d in zip(teX, teY))
    return ok / len(teY)


def run(test_spk, n_per, bank, s):
    files = [(os.path.join(DATA, fn), int(m.group(1)), m.group(2))
             for fn in sorted(os.listdir(DATA))
             if (m := FN.match(fn)) and int(m.group(3)) < n_per]
    trX, trY, teX, teY = [], [], [], []
    for path, digit, spk in files:
        v = feat(s, bank, load_wav(path)[0], 8000).flatten().astype(np.float64)
        (teX if spk == test_spk else trX).append(v)
        (teY if spk == test_spk else trY).append(digit)
    trX = np.asarray(trX); trY = np.asarray(trY); teX = np.asarray(teX); teY = np.asarray(teY)
    base = acc(trX, trY, teX, teY)

    # NATIVE WithinScatter: W computed in the substrate from the train data + labels.
    data = srs.Vec(items=[_vec(r) for r in trX])._json
    labs = _vec(trY.astype(float))._json
    Wval = s._inner.evaluate({"type": "WithinScatter", "a": data, "b": labs}, {})
    Wmat = srs.Vec(items=[_vec([float(v) for v in row]) for row in Wval])._json

    # NATIVE WhitenMany: factor L ONCE, apply L^-1 to every row, in the substrate.
    def whiten_all(X):
        Xj = srs.Vec(items=[_vec(x) for x in X])._json
        return np.array([[float(v) for v in r] for r in s._inner.evaluate(
            {"type": "WhitenMany", "a": Wmat, "b": Xj}, {})])
    return base, acc(whiten_all(trX), trY, whiten_all(teX), teY)


def main():
    test_spk = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
    n_per = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    speakers = [test_spk] if test_spk else ["george", "jackson", "theo", "nicolas"]
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    print("=" * 74)
    print("FSDD cross-speaker — FULLY NATIVE (WithinScatter + Whiten, both in-substrate)")
    print("=" * 74)
    bs, ws = [], []
    for spk in speakers:
        b, w = run(spk, n_per, bank, s)
        bs.append(b); ws.append(w)
        print(f"  [{spk:<9}] raw {b:5.1%}   native WithinScatter+Whiten {w:5.1%}   ({w-b:+.1%})")
    print("-" * 74)
    mb, mw = float(np.mean(bs)), float(np.mean(ws))
    print(f"  {'MEAN':<11}  raw {mb:5.1%}   fully-native {mw:5.1%}   ({mw-mb:+.1%})")
    print(f"\n  the agent's derived fix now runs ENTIRELY on agent-authored native "
          f"primitives ({mw-mb:+.1%}); no matrix numpy.")
    print("=" * 74)


if __name__ == "__main__":
    main()
