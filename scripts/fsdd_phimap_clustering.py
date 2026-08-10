"""Does the agent's PhiMap (golden-ratio low-discrepancy map, frac(n·φ⁻¹)) help the
cross-speaker clustering frontier? The bound is representational (words overlap linearly).
PhiMap's purpose is low-discrepancy SAMPLING — so use it to draw QUASI-random Fourier
features: lift x -> cos(W x + b) with W's frequencies placed by PhiMap (quasi-Monte-Carlo)
instead of pseudo-random. An RBF-kernel lift can separate words that overlap linearly;
the low-discrepancy frequencies should approximate the kernel with less variance.

A/B on the nuisance-conditioned (speaker-removed, +7.4%) base: linear vs random-RFF vs
phi-RFF. LABEL-FREE; labels only score purity. Uses the agent's PhiMap (verified against
the native PhiMap term) + its composed clusterer + native BetweenScatter/WhitenMany.

Run: python scripts/fsdd_phimap_clustering.py [n_per] [D]
"""
from __future__ import annotations
import os
import sys
from collections import Counter

import numpy as np
from scipy.special import ndtri  # inverse normal CDF

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import substrate_rs as srs
from substrate_rs import Substrate, Div, Mod, Times, Lit, Var
from substrate_rs.speech import _audio
from domains.cross_speaker_clustering import cluster
from scripts.speech_analysis_by_synthesis import load_wav, feat, DATA, FN, N_BANDS

PHI_K = 2654435769          # floor(2^32 / phi), the integer golden multiplier
M32 = 4294967296.0


def phi_seq(n, s):
    """The agent's PhiMap over indices 1..n: frac(k·φ⁻¹) via the integer golden form.
    Verified against the native PhiMap Term on a sample."""
    k = np.arange(1, n + 1, dtype=np.int64)
    seq = ((k * PHI_K) % int(M32)) / M32
    # verify a few against the native PhiMap term (the agent's held operator)
    for kk in (1, 7, 99):
        term = Div(a=Mod(a=Times(items=(Lit(int(kk)), Lit(PHI_K))), b=Lit(M32)),
                   b=Lit(M32)).to_dict()
        assert abs(float(s._inner.evaluate(term, {})) - (((kk * PHI_K) % int(M32)) / M32)) < 1e-12
    return seq


def purity(a, truth):
    return sum(Counter([truth[i] for i in range(len(a)) if a[i] == c]
                       ).most_common(1)[0][1] for c in set(a)) / len(truth)


def pur3(M, k, truth):
    return float(np.mean([purity(cluster(M, k, seed=sd), truth) for sd in range(3)]))


def rff(X, W, b):
    return np.sqrt(2.0 / W.shape[0]) * np.cos(X @ W.T + b)


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    D = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)

    M, word, spk, sid = [], [], [], {}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            M.append(feat(s, bank, load_wav(os.path.join(DATA, fn))[0], 8000)
                     .flatten().astype(np.float64))
            word.append(int(m.group(1))); spk.append(sid.setdefault(m.group(2), len(sid)))
    M = np.asarray(M); k = len(set(word)); n, d = M.shape

    # nuisance-conditioned base (native BetweenScatter -> WhitenMany), the +7.4% win.
    def _mat(A): return srs.Vec(items=[srs.Vec(items=[srs.Lit(float(v)) for v in r]) for r in A])._json
    Sb = np.array([[float(v) for v in r] for r in s._inner.evaluate(
        {"type": "BetweenScatter", "a": _mat(M), "b": srs.Vec(items=[srs.Lit(float(a)) for a in spk])._json}, {})])
    Wr = Sb + 0.2 * (np.trace(Sb) / d) * np.eye(d)
    Mnc = np.array([[float(v) for v in r] for r in s._inner.evaluate(
        {"type": "WhitenMany", "a": _mat(Wr), "b": _mat(M)}, {})])

    # standardise + RBF bandwidth (median heuristic)
    Z = (Mnc - Mnc.mean(0)) / (Mnc.std(0) + 1e-9)
    sub = Z[np.random.RandomState(0).choice(n, min(n, 200), replace=False)]
    med = np.median(np.linalg.norm(sub[:, None] - sub[None], axis=2))
    gamma = 1.0 / (2.0 * med ** 2 + 1e-9)
    scale = np.sqrt(2.0 * gamma)

    print("=" * 66)
    print(f"PhiMap clustering — {n} tokens, k={k}, D={D} Fourier features")
    print("=" * 66)
    print(f"  linear (NC base)             : {pur3(Mnc, k, word):.3f}")

    rng = np.random.RandomState(0)
    b = rng.uniform(0, 2 * np.pi, D)
    # pseudo-random RFF
    Wrand = rng.standard_normal((D, d)) * scale
    print(f"  RFF random (pseudo-Gaussian) : {pur3(rff(Z, Wrand, b), k, word):.3f}")
    # phi quasi-random RFF: PhiMap low-discrepancy -> inverse-normal -> Gaussian freqs
    seq = phi_seq(D * d, s)
    Wphi = ndtri(np.clip(seq, 1e-6, 1 - 1e-6)).reshape(D, d) * scale
    print(f"  RFF phi (PhiMap quasi-random): {pur3(rff(Z, Wphi, b), k, word):.3f}")
    print("=" * 66)


if __name__ == "__main__":
    main()
