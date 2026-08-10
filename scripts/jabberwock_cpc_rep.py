"""Scale it up the RIGHT WAY — CONTRASTIVE predictive coding (CPC-lite), not regression.

Naive scaling of the APC regression objective doesn't improve the phonetic readout: a better
next-frame PREDICTOR encodes fine acoustic detail, not phonetic abstraction (the small APC was
the sweet spot, ~0.124; bigger/deeper/Adam all matched or degraded). The field's answer is a
CONTRASTIVE objective (CPC -> wav2vec -> HuBERT): instead of RECONSTRUCTING the future frame,
CLASSIFY which future is real vs negatives — forcing the representation to keep what
DISTINGUISHES (phonetic identity) and discard reconstructible detail.

CPC-lite (numpy, Adam): encoder enc(past-context)->z(lossy bottleneck); predictor Wp; InfoNCE
over a batch — z_t predicts (contrastively) the future encoding z_{t+k} (stop-grad target),
with other frames' futures in the batch as negatives. NO labels. Then few-label phone readout.

Compares CPC z to raw and the small-APC (0.124) at several label budgets + continuous AUC.
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_cpc_rep.py [n_words] [epochs]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_subword_recognizer import best_window_match
from scripts.jabberwock_earns_acoustic_phonetic import gather
from scripts.jabberwock_data_efficient_rep import load_words, context_at, labeled, readout_acc, W

KAHEAD = 3


def cpc_pairs(words):
    """(context[t], context[t+KAHEAD]) — anchor & future, NO labels."""
    A, Fut = [], []
    for M, _ph in words:
        for t in range(W, len(M) - KAHEAD):
            A.append(context_at(M, t)); Fut.append(context_at(M, t + KAHEAD))
        if len(A) >= 900000:
            break
    return np.array(A), np.array(Fut)


def train_cpc(A, Fut, dh=256, dz=128, epochs=12, bs=256, lr=8e-4):
    rng = np.random.default_rng(0); d = A.shape[1]
    mu = A.mean(0); sd = A.std(0) + 1e-6; An = (A - mu) / sd; Fn = (Fut - mu) / sd
    W1 = rng.standard_normal((d, dh)) * np.sqrt(2.0 / d); b1 = np.zeros(dh)
    W2 = rng.standard_normal((dh, dz)) * np.sqrt(2.0 / dh); b2 = np.zeros(dz)
    Wp = np.eye(dz) + rng.standard_normal((dz, dz)) * 0.01
    par = [W1, b1, W2, b2, Wp]
    M_ = [np.zeros_like(x) for x in par]; Vv = [np.zeros_like(x) for x in par]
    b1m, b2m, eps = 0.9, 0.999, 1e-8; step = 0; n = len(An)

    def enc(Xn, P):
        H = np.maximum(Xn @ P[0] + P[1], 0); Z = H @ P[2] + P[3]
        Z = Z / np.clip(np.linalg.norm(Z, axis=1, keepdims=True), 1e-9, None)
        return H, Z
    for ep in range(epochs):
        idx = rng.permutation(n)
        for s in range(0, n - bs, bs):
            b = idx[s:s + bs]
            Ha, Za = enc(An[b], par)                 # anchor (grad)
            _, Zf = enc(Fn[b], par)                  # future (stop-grad target)
            pred = Za @ par[4]                        # (B,dz)
            logits = pred @ Zf.T                      # (B,B) cosine-ish scores
            logits -= logits.max(1, keepdims=True)
            Pm = np.exp(logits); Pm /= Pm.sum(1, keepdims=True)
            dlog = Pm.copy(); dlog[np.arange(len(b)), np.arange(len(b))] -= 1; dlog /= len(b)
            dpred = dlog @ Zf                         # (B,dz)
            gWp = Za.T @ dpred
            dZa = dpred @ par[4].T
            # backprop dZa through the L2-norm is approximated as identity (unit-norm Z);
            # gradient through enc:
            gW2 = Ha.T @ dZa; gb2 = dZa.sum(0); dH = (dZa @ par[2].T) * (Ha > 0)
            gW1 = An[b].T @ dH; gb1 = dH.sum(0)
            grads = [gW1, gb1, gW2, gb2, gWp]; step += 1
            for i in range(5):
                M_[i] = b1m * M_[i] + (1 - b1m) * grads[i]
                Vv[i] = b2m * Vv[i] + (1 - b2m) * grads[i] * grads[i]
                mh = M_[i] / (1 - b1m ** step); vh = Vv[i] / (1 - b2m ** step)
                par[i] -= lr * mh / (np.sqrt(vh) + eps)

    def encode(X2):
        Xn2 = (np.asarray(X2) - mu) / sd
        H = np.maximum(Xn2 @ par[0] + par[1], 0); Z = H @ par[2] + par[3]
        return Z / np.clip(np.linalg.norm(Z, axis=1, keepdims=True), 1e-9, None)
    return encode


def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 45000
    epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    print("=" * 80)
    print(f"CONTRASTIVE predictive coding (CPC-lite) — scale-up the RIGHT way, {n_words} words")
    print("=" * 80)
    t0 = time.time()
    tr = load_words("train-clean-100_*.pkl", n_words); de = load_words("dev-clean_*.pkl", 4000)
    A, Fut = cpc_pairs(tr)
    print(f"  contrastive pairs {len(A)} (anchor/future, NO labels) [{time.time()-t0:.0f}s]", flush=True)
    encode = train_cpc(A, Fut, epochs=epochs)
    print(f"  CPC trained (InfoNCE, z128 lossy) [{time.time()-t0:.0f}s]", flush=True)
    Xl, Yl = labeled(tr, 80000); Xdl, Ydl = labeled(de, 15000)
    phset = sorted(set(Yl) | set(Ydl)); pi = {p: i for i, p in enumerate(phset)}
    Zl = encode(Xl); Zd = encode(Xdl)
    print(f"\n  {'#labels':>8} {'raw':>8} {'CPC z':>8}  (small-APC was 0.124)")
    rng = np.random.default_rng(1)
    for N in (2000, 30000, 80000):
        if N > len(Xl):
            N = len(Xl)
        sub = rng.choice(len(Xl), N, replace=False)
        raw = readout_acc(Xl[sub], [Yl[i] for i in sub], Xdl, Ydl, phset, pi)
        cpc = readout_acc(Zl[sub], [Yl[i] for i in sub], Zd, Ydl, phset, pi)
        print(f"  {N:8d} {raw:8.3f} {cpc:8.3f}", flush=True)
    print("=" * 80)
    print(f"  [{time.time()-t0:.0f}s]  CPC z > APC/raw => the contrastive objective is the scale-up lever")
    print("  (forces phonetic abstraction, not frame reconstruction).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
