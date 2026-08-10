"""The jabberwock EARNS a NONLINEAR phone model — kernel/RBF (Nystrom) + LDA.

The linear PCA->LDA phone encoder caps at ~0.13 per-frame (phones aren't linearly
separable). The agent earns NONLINEAR capacity closed-form (no gradient/torch): a
kernel feature map. ANCHORS = k-means over the frame features (the agent's k-means);
RBF features phi(x)_j = exp(-gamma ||x - a_j||^2) to each anchor (the nonlinear lift,
gamma from the data's median distance); then PCA->LDA on phi (WithinScatter) = an
approximate KERNEL-LDA. Phone centroids (GMM) in that space. All the agent's primitives.

Measures per-frame phone accuracy + boundary-free content recall vs the LINEAR baseline.
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_earns_nonlinear_phone.py [n_test] [n_anchor]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.jabberwock_subword_recognizer import _load_ph, best_window_match
from scripts.jabberwock_earns_phone_model import ctxd


def kmeans(Z, K, it=6):
    rng = np.random.default_rng(0)
    C = Z[rng.choice(len(Z), min(K, len(Z)), replace=False)].copy()
    for _ in range(it):
        lab = (((Z[:, None, :] - C[None]) ** 2).sum(2)).argmin(1)
        for k in range(len(C)):
            m = Z[lab == k]
            if len(m):
                C[k] = m.mean(0)
    return C


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    n_anchor = int(sys.argv[2]) if len(sys.argv) > 2 else 256
    train = _load_ph("train-clean-100_*.pkl", 12)[:8000]
    dev = _load_ph("dev-clean_*.pkl", 12)
    print("=" * 84)
    print(f"EARN A NONLINEAR PHONE MODEL — kernel/RBF (Nystrom, {n_anchor} anchors) + LDA")
    print("=" * 84)

    phones_set = sorted({p for _w, _f, ph in train for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}; nP = len(phones_set)

    # flat-start (proportional) training pairs (EM didn't help; keep it simple)
    Xtr, Ytr = [], []
    for w, fr, ph in train:
        cx = ctxd(fr); n = len(cx); P = len(ph)
        for i in range(n):
            Xtr.append(cx[i]); Ytr.append(ph[int(i * P / n)])
        if len(Xtr) >= 40000:
            break
    Xtr = np.array(Xtr)
    print(f"  phones={nP}  train frames={len(Xtr)}  feat dim={Xtr.shape[1]}", flush=True)

    # ANCHORS + RBF gamma (data-derived) — the nonlinear lift
    rng = np.random.default_rng(0)
    sub = Xtr[rng.choice(len(Xtr), min(12000, len(Xtr)), replace=False)]
    anchors = kmeans(sub, n_anchor)
    d2a = ((sub[:2000, None, :] - anchors[None]) ** 2).sum(2)
    gamma = 1.0 / (np.median(d2a) + 1e-9)
    print(f"  anchors={len(anchors)}  rbf gamma={gamma:.4g}", flush=True)

    def rbf(X):
        xn = (X ** 2).sum(1)[:, None]; an = (anchors ** 2).sum(1)[None, :]
        d2 = np.maximum(xn + an - 2.0 * X @ anchors.T, 0.0)
        return np.exp(-gamma * d2)

    def build(feat_fn, tag, eval_dev=True):
        Ftr = feat_fn(Xtr)
        P = min(200, Ftr.shape[0] - nP - 1)
        mu, Wp = _fit_pca(Ftr, P)
        Wl = _fit_lda((Ftr - mu) @ Wp, Ytr, k=min(P, nP - 1))
        def enc(Z):
            R = ((feat_fn(np.asarray(Z)) - mu) @ Wp) @ Wl
            return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)
        E = ((Ftr - mu) @ Wp) @ Wl; E /= np.clip(np.linalg.norm(E, axis=1, keepdims=True), 1e-9, None)
        cent, cph = [], []
        for p in phones_set:
            Zp = E[[i for i in range(len(Ytr)) if Ytr[i] == p]]
            if not len(Zp):
                continue
            for c in kmeans(Zp, 4):
                cent.append(c); cph.append(pi[p])
        cent = np.array(cent); cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
        return enc, cent, np.array(cph)

    # LINEAR baseline (identity feature) vs NONLINEAR (rbf)
    def report(enc, cent, cph, tag):
        Xde, Yde = [], []
        for w, fr, ph in dev[:1500]:
            cx = ctxd(fr); n = len(cx); P = len(ph)
            for i in range(n):
                Xde.append(cx[i]); Yde.append(ph[int(i * P / n)])
        Xde = np.array(Xde)
        pred = cph[(enc(Xde) @ cent.T).argmax(1)]
        acc = np.mean([phones_set[pred[k]] == Yde[k] for k in range(len(Yde))])
        print(f"  [{tag:9}] per-frame phone acc (dev): {acc:.3f}", flush=True)
        return acc

    lin = build(lambda X: X, "linear"); la = report(*lin, "linear")
    nl = build(rbf, "rbf"); na = report(*nl, "rbf")

    # boundary-free content recall with the nonlinear model
    enc, cent, cph = nl
    func = set(w for w, _ in Counter(w for w, _, _ in train).most_common(50))
    def is_content(w): return w not in func and len(w) >= 4
    def decode(M):
        idx = cph[(enc(ctxd(M)) @ cent.T).argmax(1)]
        seq, prev = [], -1
        for k in idx:
            if k != prev:
                seq.append(phones_set[k]); prev = k
        return seq
    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); tsp = set(spk[-6:])
    test = [p for p in pairs if p[1] in tsp][:n_test]
    rx35 = rx50 = tot = 0; t0 = time.time()
    for (path, sp, ch, ut, tr) in test:
        try:
            M, _e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        pseq = decode(M)
        for w in set(w.lower() for w in L.normalise(tr)):
            if not is_content(w):
                continue
            tgt = cmu_phones(w)
            if not tgt:
                continue
            tot += 1; d = best_window_match(pseq, [str(x) for x in tgt])
            rx35 += (d <= 0.35); rx50 += (d <= 0.50)
    print("=" * 84)
    print(f"  per-frame phone acc: LINEAR {la:.3f} -> NONLINEAR {na:.3f}  (delta {na-la:+.3f})")
    print(f"  nonlinear boundary-free content recall: @0.35 {rx35/max(tot,1):.3f}  @0.50 {rx50/max(tot,1):.3f}  "
          f"({tot} words) [{time.time()-t0:.0f}s]")
    print(f"  (linear baseline: per-frame ~0.13, content @0.50 ~0.35)")
    print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
