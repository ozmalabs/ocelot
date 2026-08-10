"""The jabberwock PAYS THE COST — train the phone model on the FULL corpus (scaling curve).

Creator: "pay the cost - train on the full corpus. the orders of magnitude are wrong, because
human cognition is very lossy, but nonetheless the formula is correct." The per-frame phone
model was data-limited (overfit at 80k frames). 113 phonebank shards (~450k words) are available
vs the 12 (~48k words) used so far. Train at INCREASING data budgets and read the SCALING CURVE:
per-frame phone acc (model-independent dev) + continuous content AUC vs #frames. If per-frame
climbs with data, the formula is correct (the magnitude needed may be huge — humans are lossy/
efficient and need far less — but the DIRECTION holds).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_pay_the_cost.py [max_frames] [ncent]
"""
import glob, os, pickle, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.jabberwock_earns_phone_model import ctxd
from scripts.jabberwock_earns_acoustic_phonetic import gather, utt_phones
from scripts.jabberwock_subword_recognizer import best_window_match
from collections import Counter

BANK = "/home/matt/data/phonebank"


def stream_pairs(glob_pat, n_frames):
    """(ctxd-frame, phone) pairs via per-word proportional alignment, up to n_frames."""
    X, Y = [], []
    for p in sorted(glob.glob(os.path.join(BANK, glob_pat))):
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if not (isinstance(e, (list, tuple)) and len(e) >= 3 and isinstance(e[0], str)):
                continue
            w, fr, ph = e[0].lower(), np.asarray(e[1], float), e[2]
            if not w.isalpha() or fr.shape[0] < 3 or not ph:
                continue
            cx = ctxd(fr); n = len(cx); P = len(ph)
            for i in range(n):
                X.append(cx[i]); Y.append(str(ph[int(i * P / n)]))
        if len(X) >= n_frames:
            break
    return np.array(X[:n_frames]), Y[:n_frames]


def fit_phone(X, Y, phset, pi, K):
    nP = len(phset); P = min(140, X.shape[0] - nP - 1)
    mu, Wp = _fit_pca(X, P); Wl = _fit_lda((X - mu) @ Wp, Y, k=min(P, nP - 1))
    def enc(Z):
        R = ((np.asarray(Z) - mu) @ Wp) @ Wl
        return R / np.clip(np.linalg.norm(R, axis=1, keepdims=True), 1e-9, None)
    E = enc(X); rng = np.random.default_rng(0); cent, cph = [], []
    idx_by = {}
    for i, y in enumerate(Y):
        idx_by.setdefault(y, []).append(i)
    for p in phset:
        ii = idx_by.get(p, [])
        if not ii:
            continue
        Zp = E[ii]; C = Zp[rng.choice(len(Zp), min(K, len(Zp)), replace=False)].copy()
        for _ in range(6):
            lab = (((Zp[:, None] - C[None]) ** 2).sum(2)).argmin(1)
            for k in range(len(C)):
                m = Zp[lab == k]
                if len(m):
                    C[k] = m.mean(0)
        for c in C:
            cent.append(c); cph.append(pi[p])
    cent = np.array(cent); cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
    return enc, cent, np.array(cph)


def main():
    max_frames = int(sys.argv[1]) if len(sys.argv) > 1 else 600000
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    print("=" * 80)
    print(f"PAY THE COST — phone-model scaling curve to {max_frames} frames, {K} centroids/phone")
    print("=" * 80)
    t0 = time.time()
    Xall, Yall = stream_pairs("train-clean-100_*.pkl", max_frames)
    Xde, Yde = stream_pairs("dev-clean_*.pkl", 30000)
    phset = sorted(set(Yall) | set(Yde)); pi = {p: i for i, p in enumerate(phset)}
    print(f"  loaded train {len(Xall)} frames, dev {len(Xde)}  phones={len(phset)} [{time.time()-t0:.0f}s]", flush=True)

    # continuous dev for the AUC destination test
    devpairs = gather("dev-clean", 30)
    func = set(p for p, _ in Counter(Yall).most_common(0))   # not used
    tr_words = Counter()
    # content vocab for negatives: frequent alpha words from cmu dict
    devframes = []
    for path, trx in devpairs:
        try:
            devframes.append((frames(L.load_flac(path)[0])[0], trx))
        except Exception:
            pass
    # build a content vocab from the dev transcripts + sampling pool
    allw = set()
    for _M, trx in devframes:
        for w in trx.lower().split():
            w = "".join(c for c in w if c.isalpha())
            if len(w) >= 4 and cmu_phones(w):
                allw.add(w)
    vocab = sorted(allw)
    rng = np.random.default_rng(0)

    def cont_auc(enc, cent, cph):
        pos, neg = [], []
        for M, trx in devframes:
            idx = cph[(enc(ctxd(M)) @ cent.T).argmax(1)]; seq, prev = [], -1
            for k in idx:
                if k != prev:
                    seq.append(phset[k]); prev = k
            present = set(w.lower() for w in L.normalise(trx))
            inw = [w for w in present if len(w) >= 4 and cmu_phones(w)]
            for w in inw:
                pos.append(best_window_match(seq, [str(x) for x in cmu_phones(w)]))
            cand = [v for v in vocab if v not in present]
            for w in (rng.choice(cand, min(len(inw), len(cand)), replace=False) if cand else []):
                neg.append(best_window_match(seq, [str(x) for x in cmu_phones(w)]))
        pos, neg = np.array(pos), np.array(neg)
        return float(np.mean(pos[:, None] < neg[None, :])) if len(pos) and len(neg) else 0.0

    print(f"\n  {'#frames':>9} {'per-frame acc':>14} {'cont AUC':>10}")
    for budget in (40000, 120000, 300000, max_frames):
        if budget > len(Xall):
            budget = len(Xall)
        enc, cent, cph = fit_phone(Xall[:budget], Yall[:budget], phset, pi, K)
        keep = [k for k in range(len(Yde)) if Yde[k] in pi]
        pred = cph[(enc(Xde[keep]) @ cent.T).argmax(1)]
        acc = float(np.mean([phset[pred[i]] == Yde[keep[i]] for i in range(len(keep))]))
        auc = cont_auc(enc, cent, cph)
        print(f"  {budget:9d} {acc:14.3f} {auc:10.3f}", flush=True)
        if budget == len(Xall):
            break
    print("=" * 80)
    print(f"  [{time.time()-t0:.0f}s]  baseline (12 shards/~40k frames): per-frame ~0.13, cont AUC ~0.53.")
    print("  per-frame RISING with data => the formula is correct (more cost -> better acoustic-phonetic model).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
