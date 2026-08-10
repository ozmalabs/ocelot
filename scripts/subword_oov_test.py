"""SUB-WORD PHONOTACTIC OOV SIGNAL — does a unit-bigram surprise catch the HIGH-MARGIN OOV that whole-word distance missed?

The jabberwock's design: VQ the bank's per-frame wav2vec2-L6 latents into K~40 acoustic units (k-means, teacher-free =
phone-like recurring states); segment each word by collapsing consecutive same-unit frames -> a discrete unit SEQUENCE; fit a
bigram over the bank words' sequences. The per-word OOV signal = average NEG-LOG-PROB of the heard word's unit-to-unit
TRANSITIONS (phonotactic surprise) -- a high-margin OOV uses ordinary units but in a place/manner order the bank never makes
(legal units, illegal transition), which whole-word trajectory distance averages away. A max-frame-distance-to-centroid term
is kept only as a backstop for genuinely novel sounds.

BAR (jabberwock, aimed at the residual): among HIGH-MARGIN words (clear the margin gate), phonotactic surprise separates OOV
from in-vocab with AUROC >= 0.75 (lower than whole-word 0.878 -- it's the hard residual), AND adding it lifts ACT accuracy at
matched 50% coverage by >= +8 over margin-alone (the bar whole-word distance missed at +1.4). KILL: if it ALSO can't separate
high-margin OOV (AUROC ~0.5-0.6), this ear has NO pre-lexical OOV signal -> the agent must DEFER-and-LEARN ('teach me').

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.subword_oov_test
"""
from __future__ import annotations

import os
import pickle
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from scripts.phase0_learned_latent import dtw, fit_pca, pca_apply, NWAY, PRUNE
from scripts.strong_ear_routing_confidence import auroc

CACHE = "/tmp/p0lat_cache_L6.pkl"
KMAX_BANK = 8
K_UNITS = 40
BIGRAM_ALPHA = 0.5
MARGIN_THRESH = 0.124
N_INVOCAB = 500
N_OOV = 500


def assign(X, C):
    return (-2.0 * X @ C.T + (C ** 2).sum(1)[None, :]).argmin(1)


def kmeans(X, K, iters=25, seed=0):
    rng = np.random.RandomState(seed)
    C = X[rng.choice(len(X), K, replace=False)].copy()
    for _ in range(iters):
        a = assign(X, C)
        for k in range(K):
            m = a == k
            if m.any():
                C[k] = X[m].mean(0)
    return C


def decompose(frames, C):
    """frames [T,d] -> (unit sequence, max frame-distance to its centroid)."""
    a = assign(frames, C)
    d2 = ((frames - C[a]) ** 2).sum(1)
    seq = [int(a[0])]
    for x in a[1:]:
        if int(x) != seq[-1]:
            seq.append(int(x))
    return seq, float(np.sqrt(d2.max()))


def phonotactic(seq, logP):
    if len(seq) < 2:
        return 0.0
    return float(np.mean([-logP[seq[i], seq[i + 1]] for i in range(len(seq) - 1)]))


def main():
    print("=" * 100)
    print("SUB-WORD PHONOTACTIC OOV SIGNAL — unit-bigram surprise on the high-margin residual")
    print("=" * 100)
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train, test = data["train"], data["test"]
    mu_p, V_p = fit_pca([t[4] for t in train])
    def proj(lat):
        return pca_apply(lat, mu_p, V_p)

    vc = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        vc[w] += 1
    vocab = [w for w, c in sorted(vc.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2]
    vset = set(vocab)
    bank = defaultdict(list); cnt = defaultdict(int); bank_frames = []
    for (w, sp, uid, cf, lat) in train:
        if w in vset and cnt[w] < KMAX_BANK:
            P = proj(lat); bank[w].append(P); bank_frames.append(P); cnt[w] += 1
    vocab = [w for w in vocab if bank[w]]
    PW = np.stack([np.stack([e.mean(0) for e in bank[w]]).mean(0) for w in vocab]); PW /= (np.linalg.norm(PW, axis=1, keepdims=True) + 1e-9)

    # ---- codebook (teacher-free VQ) ----
    AF = np.concatenate(bank_frames, 0)
    if len(AF) > 40000:
        AF = AF[np.linspace(0, len(AF) - 1, 40000).astype(int)]
    print(f"  VQ {len(AF)} bank frames -> {K_UNITS} acoustic units (k-means)...", flush=True)
    C = kmeans(AF.astype(np.float32), K_UNITS)

    # ---- bigram over bank words' unit sequences ----
    trans = np.full((K_UNITS, K_UNITS), BIGRAM_ALPHA, np.float64)
    bank_seqs = []
    for w in vocab:
        for e in bank[w]:
            seq, _seg = decompose(e, C)
            bank_seqs.append((w, seq))
            for i in range(len(seq) - 1):
                trans[seq[i], seq[i + 1]] += 1
    logP = np.log(trans / trans.sum(1, keepdims=True))
    # teacher-free calibration: surprise distribution over bank words
    bank_surp = np.array([phonotactic(seq, logP) for (_w, seq) in bank_seqs])
    surp_thresh = float(np.percentile(bank_surp, 90))
    print(f"  bigram fit; bank-word surprise median {np.median(bank_surp):.2f}, theta_surp(@90th) {surp_thresh:.2f}\n", flush=True)

    def recognise(traj):
        pv = traj.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
        top = np.argsort(-(PW @ pv))[:PRUNE]
        scored = sorted(((vocab[i], min(dtw(traj, e) for e in bank[vocab[i]])) for i in top), key=lambda x: x[1])
        (w1, d1), (w2, d2) = scored[0], scored[1]
        return w1, (d2 - d1) / (d2 + d1 + 1e-9)

    invocab = [(w, proj(lat)) for (w, sp, uid, cf, lat) in test if w in vset][:N_INVOCAB]
    oov = [(w, proj(lat)) for (w, sp, uid, cf, lat) in test if w not in vset][:N_OOV]
    print(f"  scoring {len(invocab)} in-vocab + {len(oov)} OOV test words (recognise + decompose)...", flush=True)

    rows = []   # (is_oov, margin, surprise, correct)
    for (is_oov, items) in ((0, invocab), (1, oov)):
        for (gold, traj) in items:
            w1, m = recognise(traj)
            seq, seg = decompose(traj, C)
            s = phonotactic(seq, logP)
            correct = int(w1 == gold) if is_oov == 0 else 0
            rows.append((is_oov, m, s, correct))

    is_oov = np.array([r[0] for r in rows]); marg = np.array([r[1] for r in rows])
    surp = np.array([r[2] for r in rows]); cor = np.array([r[3] for r in rows])

    # high-margin subset (those that CLEAR the margin gate = the residual the margin gate accepts)
    hm = marg > MARGIN_THRESH
    au_all = auroc(surp, is_oov)
    au_hm = auroc(surp[hm], is_oov[hm])
    n_hm_oov = int(is_oov[hm].sum())

    # matched 50% coverage: margin-only vs margin+surprise
    N = len(rows); TGT = 0.50
    def margin_only_at(target):
        thr = np.quantile(marg, 1 - target); act = marg > thr
        return 100 * act.mean(), 100 * cor[act].mean(), 100 * is_oov[act].mean()
    def surp_margin_at(target, tsurp):
        known = surp <= tsurp
        n_act = min(int(round(target * N)), int(known.sum()))
        if n_act <= 0:
            return 0.0, float("nan"), float("nan")
        thr = np.sort(marg[known])[::-1][n_act - 1]; act = known & (marg >= thr)
        return 100 * act.mean(), 100 * cor[act].mean(), 100 * is_oov[act].mean()
    cov_mo, acc_mo, oov_mo = margin_only_at(TGT)
    cov_sm, acc_sm, oov_sm = surp_margin_at(TGT, surp_thresh)

    print("\n" + "=" * 100)
    print(f"  {len(rows)} words ({100*is_oov.mean():.0f}% OOV); high-margin subset (margin>{MARGIN_THRESH}): {hm.sum()} words, {n_hm_oov} OOV")
    print(f"  phonotactic surprise: in-vocab median {np.median(surp[is_oov==0]):.2f}, OOV {np.median(surp[is_oov==1]):.2f}")
    print(f"  AUROC(OOV vs in-vocab):  all words {au_all:.3f}   |   HIGH-MARGIN subset {au_hm:.3f}  (bar >=0.75)")
    print(f"  matched {TGT*100:.0f}% coverage:")
    print(f"    MARGIN-only:      {cov_mo:.0f}% cov, ACT acc {acc_mo:.1f}%  ({oov_mo:.0f}% OOV in ACT)")
    print(f"    SURPRISE+MARGIN:  {cov_sm:.0f}% cov, ACT acc {acc_sm:.1f}%  ({oov_sm:.0f}% OOV in ACT)   delta {acc_sm-acc_mo:+.1f}")
    print("-" * 100)
    if au_hm >= 0.75 and (acc_sm - acc_mo) >= 8.0:
        print(f"  PORT — sub-word phonotactic surprise SEPARATES the high-margin OOV (AUROC {au_hm:.2f}>=0.75) where whole-word")
        print(f"  distance couldn't, and lifts matched-coverage accuracy {acc_mo:.0f}->{acc_sm:.0f}% ({acc_sm-acc_mo:+.1f}>=+8). The")
        print("  illegal-TRANSITION signal catches legal-units-illegal-order OOV. Wire it graph-native into the live adapter.")
    elif au_hm < 0.6:
        print(f"  KILL (defer-and-learn) — sub-word surprise can't separate high-margin OOV either (AUROC {au_hm:.2f}). This ear has")
        print("  NO pre-lexical OOV signal for the hard residual; the honest design is DEFER-AND-LEARN: treat low confidence as")
        print("  'teach me' (mint an Unknown, ask), not pretend to detect. The margin gate handles the easy OOV; the rest is taught.")
    else:
        print(f"  PARTIAL — high-margin AUROC {au_hm:.2f}, matched-coverage delta {acc_sm-acc_mo:+.1f}. Real phonotactic signal, under")
        print("  the bar; helps but doesn't fully close the high-margin OOV residual on this rig.")
    print("=" * 100)


if __name__ == "__main__":
    main()
