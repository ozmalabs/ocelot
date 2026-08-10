"""Manifold approach, step 0: does speech lie on a LOW-DIM MANIFOLD? Estimate intrinsic dimension.

The manifold approach's whole premise: intrinsic dim << ambient dim, so the manifold coordinates are
a data-efficient representation. Measure the intrinsic dimension of the cochleagram (Levina-Bickel
MLE 2004 + TwoNN Facco 2017 + PCA variance), for:
  - ALL frames (the full acoustic manifold incl speaker/prosody nuisance)
  - WITHIN one phone class (the local phonetic/articulatory manifold = the DOF of producing that phone)
If intrinsic dim is small (<< 32 ambient bands), the manifold approach is justified; the gap between
the all-frames dim and the within-phone dim quantifies the nuisance (speaker) vs phonetic structure.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_manifold_intrinsic_dim.py [N]
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import defaultdict
from scripts.jabberwock_subword_recognizer import _load_ph


def knn_sorted_dists(X, k):
    X = np.asarray(X, float)
    G = X @ X.T; sq = np.diag(G).copy()
    D2 = np.maximum(sq[:, None] + sq[None, :] - 2 * G, 0.0)
    np.fill_diagonal(D2, np.inf)
    idx = np.argpartition(D2, kth=k, axis=1)[:, :k]
    d = np.sqrt(np.take_along_axis(D2, idx, axis=1))
    d.sort(axis=1)
    return d                                   # (N,k) ascending NN distances (excl self)


def mle_id(X, k=12):
    """Levina-Bickel MLE intrinsic dimension (averaged over points)."""
    d = knn_sorted_dists(X, k)
    Tk = d[:, k - 1:k]                          # k-th NN dist
    with np.errstate(divide="ignore"):
        logs = np.log(Tk / d[:, :k - 1] + 1e-12)
    m = (k - 1) / np.clip(logs.sum(1), 1e-9, None)
    m = m[np.isfinite(m)]
    return float(np.mean(m))


def twonn_id(X):
    """Facco TwoNN: mu = r2/r1; d = slope of -log(1-F(mu)) vs log(mu)."""
    d = knn_sorted_dists(X, 2)
    mu = d[:, 1] / np.clip(d[:, 0], 1e-12, None)
    mu = np.sort(mu[mu > 1.0 + 1e-9])
    n = len(mu)
    F = (np.arange(1, n + 1)) / (n + 1)
    x = np.log(mu); y = -np.log(1 - F)
    return float(np.sum(x * y) / np.sum(x * x))   # slope through origin


def pca_dims(X):
    Xc = X - X.mean(0)
    s = np.linalg.svd(Xc, compute_uv=False)
    v = (s ** 2); v /= v.sum()
    cum = np.cumsum(v)
    pr = (v.sum() ** 2) / (v ** 2).sum()          # participation ratio
    d90 = int(np.searchsorted(cum, 0.90) + 1); d95 = int(np.searchsorted(cum, 0.95) + 1)
    return pr, d90, d95


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    data = _load_ph("train-clean-100_*.pkl", 8)
    rng = np.random.default_rng(0)
    # ALL frames (ambient = 32 bands), labeled by phone via proportional alignment
    frames, phones = [], []
    for w, fr, ph in data:
        fr = np.asarray(fr, float); n = len(fr); P = len(ph)
        for i in range(n):
            frames.append(fr[i]); phones.append(str(ph[int(i * P / n)]))
        if len(frames) >= 60000:
            break
    frames = np.array(frames); phones = np.array(phones)
    amb = frames.shape[1]
    print("=" * 78)
    print(f"INTRINSIC DIMENSION OF SPEECH (ambient = {amb} cochleagram bands)")
    print("=" * 78)

    s = rng.choice(len(frames), min(N, len(frames)), replace=False)
    Xall = frames[s]
    pr, d90, d95 = pca_dims(Xall)
    print(f"  ALL frames (incl speaker/prosody): MLE {mle_id(Xall):.1f}  TwoNN {twonn_id(Xall):.1f}  "
          f"| PCA participation {pr:.1f}, 90%@{d90}d, 95%@{d95}d", flush=True)

    # WITHIN one phone class (the local phonetic / articulatory manifold)
    by = defaultdict(list)
    for i in range(len(frames)):
        by[phones[i]].append(i)
    big = sorted(by, key=lambda p: -len(by[p]))[:4]
    for p in big:
        ii = np.array(by[p]); ii = ii[rng.choice(len(ii), min(N, len(ii)), replace=False)]
        Xp = frames[ii]
        print(f"  within phone '{p}' (n={len(ii)}): MLE {mle_id(Xp):.1f}  TwoNN {twonn_id(Xp):.1f}",
              flush=True)
    print("=" * 78)
    print("  If MLE/TwoNN << 32, speech lies on a LOW-DIM MANIFOLD -> the manifold approach is justified;")
    print("  within-phone dim ~ the articulatory DOF; all-frames - within-phone ~ the speaker nuisance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
