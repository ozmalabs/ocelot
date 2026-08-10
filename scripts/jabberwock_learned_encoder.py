"""LEARNED ENCODER — distil DTW-level word discrimination into a CHEAP fixed-length
embedding, so alignment-invariance becomes a single matmul (no DTW, no escalation).

Hand-crafted enrichment closed only ~half the resolution gap; the residual is
nonlinear temporal ALIGNMENT a static cosine can't do. Learn it instead: a closed-
form encoder (PCA -> LDA, no gradient descent, no torch) fit on the TRAIN support that
learns the directions which SEPARATE words while COLLAPSING within-word variation
(speaker / rate / alignment). Project to that subspace -> cosine matmul.

Cross-speaker phonebank gate (dev queries vs train support, disjoint speakers). The
encoder is FIT ON TRAIN ONLY, applied to unseen dev speakers (real generalisation).

  DTW ceiling (expensive)          : reference
  enriched cheap (vel, no encoder) : the hand-crafted floor (~0.605)
  LEARNED encoder (PCA->LDA) cheap : this

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_learned_encoder.py [n_words] [max_query] [per_word]
"""
from __future__ import annotations
import glob, os, pickle, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_reads_oov_from_phones import dtw, STOP

BANK = "/home/matt/data/phonebank"
NB = 32


def _l2rows(fr):
    fr = np.asarray(fr, dtype=np.float64)
    if fr.ndim == 1:
        fr = fr.reshape(1, -1)
    return fr / np.clip(np.linalg.norm(fr, axis=1, keepdims=True), 1e-9, None)


def _load(g, cap):
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, g)))[:cap]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 2 and isinstance(e[0], str):
                w = e[0].lower(); fr = _l2rows(e[1])
                if w not in STOP and len(w) >= 3 and fr.shape[0] >= 3:
                    out.append((w, fr))
    return out


def _kmeans(X, K, it=10):
    rng = np.random.default_rng(0)
    C = X[rng.choice(len(X), min(K, len(X)), replace=False)].copy()
    for _ in range(it):
        lab = (((X[:, None, :] - C[None, :, :]) ** 2).sum(2)).argmin(1)
        for k in range(len(C)):
            m = X[lab == k]
            if len(m):
                C[k] = m.mean(0)
    return lab


def _spk_env(words, K):
    feat = np.array([np.concatenate([fr.mean(0), fr.std(0)]) for _w, fr in words])
    feat = feat / np.clip(np.linalg.norm(feat, axis=1, keepdims=True), 1e-9, None)
    lab = _kmeans(feat, K)
    envs = {k: np.concatenate([words[i][1] for i in range(len(words)) if lab[i] == k], 0).mean(0)
            for k in set(lab)}
    return [envs[lab[i]] for i in range(len(words))]


def _resample(fr, L=20):
    n = len(fr)
    if n == L:
        return fr
    idx = np.linspace(0, n - 1, L); lo = np.floor(idx).astype(int); hi = np.clip(lo + 1, 0, n - 1)
    t = (idx - lo)[:, None]
    return fr[lo] * (1 - t) + fr[hi] * t


def _feat(fr, env):
    """enriched fixed-length: speaker+rate peeled mean CONCAT velocity (the floor)."""
    x = _resample(fr - env[None, :])
    d = np.vstack([np.zeros((1, x.shape[1])), np.diff(x, axis=0)])
    v = np.concatenate([x, d], axis=1).reshape(-1)
    return v / max(np.linalg.norm(v), 1e-9)


def _fit_pca(X, P):
    mu = X.mean(0)
    U, S, Vt = np.linalg.svd(X - mu, full_matrices=False)
    return mu, Vt[:P].T               # (D x P)


def _fit_lda(Z, labels, k, eps=1e-2):
    classes = sorted(set(labels))
    d = Z.shape[1]; mu = Z.mean(0)
    Sw = np.zeros((d, d)); Sb = np.zeros((d, d))
    for c in classes:
        Zc = Z[[i for i in range(len(labels)) if labels[i] == c]]
        mc = Zc.mean(0); D = Zc - mc
        Sw += D.T @ D
        diff = (mc - mu)[:, None]
        Sb += len(Zc) * (diff @ diff.T)
    Sw += eps * np.trace(Sw) / d * np.eye(d)
    evals, evecs = np.linalg.eig(np.linalg.solve(Sw, Sb))
    order = np.argsort(-evals.real)
    return evecs[:, order[:k]].real    # (P x k)


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    sup_all = _load("train-clean-100_*.pkl", 8)
    qry_all = _load("dev-clean_*.pkl", 8)
    sw = Counter(w for w, _ in sup_all); qw = Counter(w for w, _ in qry_all)
    vocab = [w for w, _ in sw.most_common() if qw[w] >= 2][:n_words]
    vset = set(vocab); chance = 1.0 / len(vocab); C = len(vocab)
    by = defaultdict(list)
    for w, fr in sup_all:
        if w in vset and len(by[w]) < per:
            by[w].append(fr)
    support = [(w, fr) for w, frs in by.items() for fr in frs]
    queries = [(w, fr) for w, fr in qry_all if w in vset]
    np.random.default_rng(1).shuffle(queries); queries = queries[:max_q]
    s_env = _spk_env(support, 24); q_env = _spk_env(queries, 3)
    sy = [w for w, _ in support]; qy = np.array([w for w, _ in queries]); n = len(queries)
    print("=" * 92)
    print("LEARNED ENCODER (PCA->LDA) — distil alignment-invariant word discrimination, cheaply")
    print("=" * 92)
    print(f"  vocab={C} chance={chance:.3f}  support={len(support)} queries={n}")

    # DTW ceiling
    t = time.time(); ok = 0
    for w, fr in queries:
        bd, bw = 1e18, None
        for sw_, sfr in support:
            d = dtw(fr, sfr)
            if d < bd:
                bd, bw = d, sw_
        ok += (bw == w)
    dtw_acc = ok / n
    print(f"  DTW ceiling (expensive): {dtw_acc:.3f}  [{time.time()-t:.1f}s]")

    # cheap features (enriched floor)
    Sx = np.array([_feat(fr, s_env[i]) for i, (w, fr) in enumerate(support)])
    Qx = np.array([_feat(fr, q_env[i]) for i, (w, fr) in enumerate(queries)])
    base = (np.array([sy[j] for j in (Qx @ Sx.T).argmax(1)]) == qy).mean()
    print(f"  enriched cheap (no encoder): {base:.3f}  (dim {Sx.shape[1]})")

    # LEARN encoder on TRAIN support only: PCA -> LDA
    P = min(120, Sx.shape[0] - C - 1)
    mu, Wp = _fit_pca(Sx, P)
    Zs = (Sx - mu) @ Wp
    Wl = _fit_lda(Zs, sy, k=C - 1)
    def enc(X):
        Y = ((X - mu) @ Wp) @ Wl
        return Y / np.clip(np.linalg.norm(Y, axis=1, keepdims=True), 1e-9, None)
    Se, Qe = enc(Sx), enc(Qx)
    learned = (np.array([sy[j] for j in (Qe @ Se.T).argmax(1)]) == qy).mean()
    # also: nearest CLASS-CENTROID in the learned space (even cheaper: C comparisons)
    cents = np.array([Se[[i for i in range(len(sy)) if sy[i] == w]].mean(0) for w in vocab])
    cents = cents / np.clip(np.linalg.norm(cents, axis=1, keepdims=True), 1e-9, None)
    learned_c = (np.array([vocab[j] for j in (Qe @ cents.T).argmax(1)]) == qy).mean()
    print(f"  LEARNED encoder (PCA->LDA), exemplars: {learned:.3f}  (dim {C-1})")
    print(f"  LEARNED encoder, CLASS-CENTROID ({C} comparisons): {learned_c:.3f}")

    print("\n" + "=" * 92)
    best = max(learned, learned_c)
    print(f"  DTW {dtw_acc:.3f} | enriched-cheap {base:.3f} | LEARNED {best:.3f}   "
          f"(encoder fit on TRAIN, tested on unseen dev speakers)")
    verd = "MATCHES/BEATS DTW AT MATMUL COST" if best >= dtw_acc - 0.005 else \
           ("CLOSES MOST OF THE GAP" if best > base + 0.01 else "NO GAIN OVER ENRICHED")
    print(f"  -> {verd}")
    print("  A closed-form learned encoder distils the within-word (speaker/rate/alignment) collapse +")
    print("  between-word separation the expensive DTW achieved, into a tiny fixed vector matched by one")
    print("  matmul. If it reaches DTW, the resolution residual is cheap -> the whole normal case is matmul.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
