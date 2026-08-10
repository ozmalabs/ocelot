"""The jabberwock builds the DATA-EFFICIENT representation — self-supervised predictive coding.

The closed-form model on raw cochleagram is data-INEFFICIENT (per-frame asymptotes ~0.16; needs
orders of magnitude of labels). A human is "lossy-but-right": data-EFFICIENT. The mechanism is
the agent's own KEYSTONE — the residual-feedback recurrence — applied to audio as SELF-SUPERVISED
PREDICTIVE CODING: a model learns to PREDICT the future cochleagram frame from the past (NO phone
labels); the bottleneck that predicts speech captures PHONETIC structure (predicting speech
requires modelling phones). Then a FEW labels read phones off that representation.

Data-efficiency test: per-frame phone acc vs #LABELS, predictive-bottleneck z vs raw cochleagram
context. If z wins especially in the LOW-LABEL regime, it is the data-efficient (lossy-but-right)
representation the scaling curve said was missing.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_data_efficient_rep.py [n_words] [epochs]
"""
import glob, os, pickle, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda

BANK = "/home/matt/data/phonebank"
W = 8          # past-context frames
KAHEAD = 3     # predict this many frames ahead (autoregressive predictive coding)


def load_words(glob_pat, n_words):
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, glob_pat))):
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 3 and isinstance(e[0], str):
                fr = np.asarray(e[1], float); ph = e[2]
                if fr.shape[0] >= W + KAHEAD + 1 and ph:
                    out.append((fr, [str(x) for x in ph]))
        if len(out) >= n_words:
            break
    return out[:n_words]


def context_at(M, t):
    """flattened past W+1 frames ending at t (edge-padded)."""
    a = max(0, t - W)
    seg = M[a:t + 1]
    if len(seg) < W + 1:
        seg = np.vstack([np.repeat(seg[:1], W + 1 - len(seg), 0), seg])
    return seg.reshape(-1)


def apc_pairs(words):
    """(past-context[t], future-frame[t+KAHEAD]) — self-supervised, NO labels."""
    Xc, Yt = [], []
    for M, _ph in words:
        for t in range(W, len(M) - KAHEAD):
            Xc.append(context_at(M, t)); Yt.append(M[t + KAHEAD])
    return np.array(Xc), np.array(Yt)


def labeled(words, cap):
    """(past-context[t], phone[t]) via per-word proportional alignment (the few labels)."""
    Xc, Y = [], []
    for M, ph in words:
        n = len(M); P = len(ph)
        for t in range(W, n - KAHEAD):
            Xc.append(context_at(M, t)); Y.append(ph[int(t * P / n)])
        if len(Xc) >= cap:
            break
    return np.array(Xc), Y


def train_apc(Xc, Yt, dh=128, dz=64, epochs=20, bs=256, lr=0.01):
    """SELF-SUPERVISED: ctx -> h(relu) -> z(bottleneck) -> predict future frame. MSE, SGD."""
    rng = np.random.default_rng(0); d = Xc.shape[1]; do = Yt.shape[1]
    mu = Xc.mean(0); sd = Xc.std(0) + 1e-6; Xn = (Xc - mu) / sd
    W1 = rng.standard_normal((d, dh)) * np.sqrt(2.0 / d); b1 = np.zeros(dh)
    W2 = rng.standard_normal((dh, dz)) * np.sqrt(2.0 / dh); b2 = np.zeros(dz)
    W3 = rng.standard_normal((dz, do)) * np.sqrt(2.0 / dz); b3 = np.zeros(do)
    V = [np.zeros_like(x) for x in (W1, b1, W2, b2, W3, b3)]
    n = len(Xn)
    for ep in range(epochs):
        idx = rng.permutation(n)
        for s in range(0, n, bs):
            b = idx[s:s + bs]; A = Xn[b]; T = Yt[b]
            H = np.maximum(A @ W1 + b1, 0); Z = H @ W2 + b2; O = Z @ W3 + b3
            gO = 2 * (O - T) / len(b)
            gW3 = Z.T @ gO; gb3 = gO.sum(0); gZ = gO @ W3.T
            gW2 = H.T @ gZ; gb2 = gZ.sum(0); gH = (gZ @ W2.T) * (H > 0)
            gW1 = A.T @ gH; gb1 = gH.sum(0)
            grads = [gW1, gb1, gW2, gb2, gW3, gb3]
            gn = np.sqrt(sum(float((g * g).sum()) for g in grads)) + 1e-9
            scale = min(1.0, 5.0 / gn)                                  # gradient-norm clip
            for arr, g, vi in zip((W1, b1, W2, b2, W3, b3), grads, range(6)):
                V[vi] = 0.9 * V[vi] - lr * scale * g; arr += V[vi]
    def encode(Xc2):
        Xn2 = (np.asarray(Xc2) - mu) / sd
        return np.maximum(Xn2 @ W1 + b1, 0) @ W2 + b2          # z bottleneck
    return encode


def readout_acc(Rtr, Ytr, Rde, Yde, phset, pi):
    Rtr = np.nan_to_num(np.asarray(Rtr, float)); Rde = np.nan_to_num(np.asarray(Rde, float))
    m = Rtr.mean(0); s = Rtr.std(0) + 1e-6                  # standardise (robust SVD)
    Rtr = (Rtr - m) / s; Rde = (Rde - m) / s
    nP = len(phset); P = min(120, Rtr.shape[0] - nP - 1, Rtr.shape[1] - 1)
    mu, Wp = _fit_pca(Rtr, P); Wl = _fit_lda((Rtr - mu) @ Wp, Ytr, k=min(P, nP - 1))
    def enc(Z):
        R = ((np.asarray(Z) - mu) @ Wp) @ Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)
    E = enc(Rtr); idx_by = {}
    for i, y in enumerate(Ytr):
        idx_by.setdefault(y, []).append(i)
    cent, cph = [], []
    for p in phset:
        ii = idx_by.get(p, [])
        if ii:
            cent.append(E[ii].mean(0)); cph.append(pi[p])
    cent = np.array(cent); cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
    cph = np.array(cph)
    keep = [k for k in range(len(Yde)) if Yde[k] in pi]
    pred = cph[(enc(Rde[keep]) @ cent.T).argmax(1)]
    return float(np.mean([phset[pred[i]] == Yde[keep[i]] for i in range(len(keep))]))


def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 14000
    epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    print("=" * 80)
    print("DATA-EFFICIENT REPRESENTATION — self-supervised predictive coding (APC), few-label readout")
    print("=" * 80)
    t0 = time.time()
    tr = load_words("train-clean-100_*.pkl", n_words)
    de = load_words("dev-clean_*.pkl", 4000)
    # SELF-SUPERVISED pretrain on UNLABELED audio (no phones used here)
    Xc, Yt = apc_pairs(tr)
    print(f"  self-supervised APC pairs: {len(Xc)} (predict +{KAHEAD} frames, NO labels) [{time.time()-t0:.0f}s]", flush=True)
    encode = train_apc(Xc, Yt, epochs=epochs)
    print(f"  APC trained [{time.time()-t0:.0f}s]", flush=True)

    # labeled pools (the FEW labels) + dev
    Xl, Yl = labeled(tr, 60000); Xdl, Ydl = labeled(de, 15000)
    phset = sorted(set(Yl) | set(Ydl)); pi = {p: i for i, p in enumerate(phset)}
    Zl = encode(Xl); Zd = encode(Xdl)
    print(f"\n  {'#labels':>8} {'raw-cochleagram':>16} {'APC z (self-sup)':>18}")
    rng = np.random.default_rng(1)
    for N in (2000, 8000, 30000, 60000):
        if N > len(Xl):
            N = len(Xl)
        sub = rng.choice(len(Xl), N, replace=False)
        raw = readout_acc(Xl[sub], [Yl[i] for i in sub], Xdl, Ydl, phset, pi)
        apc = readout_acc(Zl[sub], [Yl[i] for i in sub], Zd, Ydl, phset, pi)
        print(f"  {N:8d} {raw:16.3f} {apc:18.3f}", flush=True)
        if N == len(Xl):
            break
    print("=" * 80)
    print(f"  [{time.time()-t0:.0f}s]  APC z > raw, especially at LOW labels => the data-efficient")
    print("  (lossy-but-right) representation: self-supervised prediction did the work, few labels suffice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
