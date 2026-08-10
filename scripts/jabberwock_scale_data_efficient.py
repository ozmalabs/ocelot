"""SCALE UP the data-efficient representation — more unlabeled audio, wider/deeper encoder,
multi-step prediction. Pay the cost on the RIGHT object (the self-supervised predictive rep).

The small APC (1 hidden, 64-d, 267k pairs) already beat raw and was data-efficient (APC@2k labels
> raw@60k). Now scale it: ~10x unlabeled data, 288->512->256 encoder -> 256-d bottleneck, predict
the NEXT 3 frames (richer residual signal). Measure per-frame phone acc (full + low-label) and the
continuous content AUC. Does scaling the data-efficient rep climb per-frame and start crossing the
continuous floor?

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_scale_data_efficient.py [n_words] [epochs]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_subword_recognizer import best_window_match
from scripts.jabberwock_earns_acoustic_phonetic import gather
from scripts.jabberwock_data_efficient_rep import load_words, context_at, labeled, readout_acc, apc_pairs, W, KAHEAD


def apc_pairs_multi(words, K=3):
    """(past-context[t], NEXT K frames flattened) — richer self-supervision, NO labels."""
    Xc, Yt = [], []
    for M, _ph in words:
        for t in range(W, len(M) - K):
            Xc.append(context_at(M, t)); Yt.append(M[t + 1:t + 1 + K].reshape(-1))
        if len(Xc) >= 1200000:
            break
    return np.array(Xc), np.array(Yt)


def train_apc_deep(Xc, Yt, h1=512, h2=256, dz=64, epochs=18, bs=512, lr=8e-4):
    """deeper/wider APC trained with ADAM (plain SGD can't optimise the bigger net)."""
    rng = np.random.default_rng(0); d = Xc.shape[1]; do = Yt.shape[1]
    mu = Xc.mean(0); sd = Xc.std(0) + 1e-6; Xn = (Xc - mu) / sd
    P = [rng.standard_normal((d, h1)) * np.sqrt(2.0 / d), np.zeros(h1),
         rng.standard_normal((h1, h2)) * np.sqrt(2.0 / h1), np.zeros(h2),
         rng.standard_normal((h2, dz)) * np.sqrt(2.0 / h2), np.zeros(dz),
         rng.standard_normal((dz, do)) * np.sqrt(2.0 / dz), np.zeros(do)]
    M_ = [np.zeros_like(x) for x in P]; Vv = [np.zeros_like(x) for x in P]
    b1, b2, eps = 0.9, 0.999, 1e-8; step = 0; n = len(Xn)
    for ep in range(epochs):
        idx = rng.permutation(n)
        for s in range(0, n, bs):
            b = idx[s:s + bs]; A = Xn[b]; T = Yt[b]
            H1 = np.maximum(A @ P[0] + P[1], 0)
            H2 = np.maximum(H1 @ P[2] + P[3], 0)
            Z = H2 @ P[4] + P[5]
            O = Z @ P[6] + P[7]
            gO = 2 * (O - T) / len(b)
            gW4 = Z.T @ gO; gb4 = gO.sum(0); gZ = gO @ P[6].T
            gW3 = H2.T @ gZ; gb3 = gZ.sum(0); gH2 = (gZ @ P[4].T) * (H2 > 0)
            gW2 = H1.T @ gH2; gb2 = gH2.sum(0); gH1 = (gH2 @ P[2].T) * (H1 > 0)
            gW1 = A.T @ gH1; gb1 = gH1.sum(0)
            grads = [gW1, gb1, gW2, gb2, gW3, gb3, gW4, gb4]
            step += 1
            for i in range(8):
                M_[i] = b1 * M_[i] + (1 - b1) * grads[i]
                Vv[i] = b2 * Vv[i] + (1 - b2) * grads[i] * grads[i]
                mh = M_[i] / (1 - b1 ** step); vh = Vv[i] / (1 - b2 ** step)
                P[i] -= lr * mh / (np.sqrt(vh) + eps)
    def encode(X2):
        Xn2 = (np.asarray(X2) - mu) / sd
        H1 = np.maximum(Xn2 @ P[0] + P[1], 0); H2 = np.maximum(H1 @ P[2] + P[3], 0)
        return H2 @ P[4] + P[5]
    return encode


def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 45000
    epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    print("=" * 80)
    print(f"SCALE UP the data-efficient representation — {n_words} words, deeper/wider APC, multi-step")
    print("=" * 80)
    t0 = time.time()
    tr = load_words("train-clean-100_*.pkl", n_words)
    de = load_words("dev-clean_*.pkl", 4000)
    Xc, Yt = apc_pairs(tr)          # single-step (predict M[t+3]) — the objective the small APC used
    print(f"  self-supervised pairs {len(Xc)} (predict +{KAHEAD} frame, NO labels) [{time.time()-t0:.0f}s]", flush=True)
    encode = train_apc_deep(Xc, Yt, epochs=epochs)
    print(f"  scaled APC trained (288->512->256->z64 lossy bottleneck, Adam) [{time.time()-t0:.0f}s]", flush=True)

    Xl, Yl = labeled(tr, 80000); Xdl, Ydl = labeled(de, 15000)
    phset = sorted(set(Yl) | set(Ydl)); pi = {p: i for i, p in enumerate(phset)}
    Zl = encode(Xl); Zd = encode(Xdl)
    print(f"\n  {'#labels':>8} {'raw':>8} {'scaled-APC z':>14}")
    rng = np.random.default_rng(1)
    for N in (2000, 30000, 80000):
        if N > len(Xl):
            N = len(Xl)
        sub = rng.choice(len(Xl), N, replace=False)
        raw = readout_acc(Xl[sub], [Yl[i] for i in sub], Xdl, Ydl, phset, pi)
        apc = readout_acc(Zl[sub], [Yl[i] for i in sub], Zd, Ydl, phset, pi)
        print(f"  {N:8d} {raw:8.3f} {apc:14.3f}", flush=True)

    # continuous content AUC with the scaled representation (full-label phone readout -> decode)
    # build z->phone classifier (LDA+centroids) on full labels
    m = Zl.mean(0); s = Zl.std(0) + 1e-6
    from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
    Zn = (Zl - m) / s; nP = len(phset); Pd = min(120, Zn.shape[1] - 1)
    mu2, Wp = _fit_pca(Zn, Pd); Wl = _fit_lda((Zn - mu2) @ Wp, Yl, k=min(Pd, nP - 1))
    def penc(zc):
        R = ((np.asarray(zc) - mu2) @ Wp) @ Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)
    E = penc(Zn); idx_by = {}
    for i, y in enumerate(Yl):
        idx_by.setdefault(y, []).append(i)
    cent, cph = [], []
    for p in phset:
        ii = idx_by.get(p, [])
        if ii:
            cent.append(E[ii].mean(0)); cph.append(pi[p])
    cent = np.array(cent); cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None); cph = np.array(cph)

    devpairs = gather("dev-clean", 30); rng2 = np.random.default_rng(0)
    vocab = sorted({w for _p, trx in devpairs for w in
                    ["".join(c for c in x.lower() if c.isalpha()) for x in trx.split()]
                    if len(w) >= 4 and cmu_phones(w)})
    pos, neg = [], []
    for path, trx in devpairs:
        try:
            M = frames(L.load_flac(path)[0])[0]
        except Exception:
            continue
        zc = encode(np.array([context_at(M, t) for t in range(len(M))]))
        idx = cph[(penc((zc - m) / s) @ cent.T).argmax(1)]; seq, prev = [], -1
        for k in idx:
            if k != prev:
                seq.append(phset[k]); prev = k
        present = set(w.lower() for w in L.normalise(trx))
        inw = [w for w in present if len(w) >= 4 and cmu_phones(w)]
        for w in inw:
            pos.append(best_window_match(seq, [str(x) for x in cmu_phones(w)]))
        cand = [v for v in vocab if v not in present]
        for w in (rng2.choice(cand, min(len(inw), len(cand)), replace=False) if cand else []):
            neg.append(best_window_match(seq, [str(x) for x in cmu_phones(w)]))
    pos, neg = np.array(pos), np.array(neg)
    auc = float(np.mean(pos[:, None] < neg[None, :])) if len(pos) and len(neg) else 0.0
    print("=" * 80)
    print(f"  continuous content AUC (scaled APC): {auc:.3f}  (chance 0.5; small-APC/raw were ~0.46)")
    print(f"  [{time.time()-t0:.0f}s]")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
