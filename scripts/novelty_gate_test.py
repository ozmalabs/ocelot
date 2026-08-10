"""OOV NOVELTY GATE — does normalised nearest-exemplar distance separate OOV from cross-speaker in-vocab? (ruler first).

The jabberwock's design: novelty r = d1 / spread(matched_word), where d1 = best-match DTW distance and spread = the matched
word's OWN cross-speaker DTW spread (leave-one-out on the bank: each exemplar's distance to the nearest OTHER-speaker exemplar
of the SAME word — that IS "a known word from a new speaker", zero OOV labels). A known word from a new mouth lands r~1 (inside
its speaker spread); an OOV is different IN KIND so r>>1 (past any known word's spread). Threshold = ~95th pct of the leave-
one-out r distribution. Compose: ACT iff KNOWN (r<=theta_nov) AND confident (margin>theta_margin); DEFER if NOVEL or unconfident.

BAR (jabberwock): (i) r separates OOV from in-vocab AUROC >= 0.85 (label = word-outside-bank, grade-only); (ii) the combined
gate RECOVERS ACT-set accuracy to >= 90% on the OOV-containing stream (vs margin-alone 66.7) at coverage not collapsing far
below the in-vocab 49%. KILL: AUROC ~0.5 -> whole-word distance can't separate OOV from cross-speaker in-vocab -> needs a
sub-word/phonotactic signal instead.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.novelty_gate_test
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
MARGIN_THRESH = 0.124        # from the selective-action gate (median in-vocab margin)
NOV_PCT = 95
N_INVOCAB = 500
N_OOV = 500


def _l2(M):
    M = np.asarray(M, np.float32); n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


def main():
    print("=" * 100)
    print("OOV NOVELTY GATE — normalised nearest-exemplar distance r = d1/spread(word) (ruler)")
    print("=" * 100)
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train, test = data["train"], data["test"]
    mu_p, V_p = fit_pca([t[4] for t in train])
    def proj(lat):
        return pca_apply(lat, mu_p, V_p)

    # bank with speakers
    bank = defaultdict(list); cnt = defaultdict(int)
    vc = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        vc[w] += 1
    vocab = [w for w, c in sorted(vc.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2]
    vset = set(vocab)
    for (w, sp, uid, cf, lat) in train:
        if w in vset and cnt[w] < KMAX_BANK:
            bank[w].append((sp, proj(lat))); cnt[w] += 1
    vocab = [w for w in vocab if bank[w]]
    PW = np.stack([np.stack([e.mean(0) for (_s, e) in bank[w]]).mean(0) for w in vocab])
    PW /= (np.linalg.norm(PW, axis=1, keepdims=True) + 1e-9)
    print(f"  bank: {len(vocab)}-way; computing per-word cross-speaker spread (leave-one-out)...", flush=True)

    # spread[w] = median over exemplars of (nearest OTHER-speaker same-word DTW). calibration r ~ d_loo/spread.
    spread = {}; cal_r = []
    for w in vocab:
        exs = bank[w]
        d_loo = []
        for i, (spi, ei) in enumerate(exs):
            others = [ej for j, (spj, ej) in enumerate(exs) if spj != spi]
            if others:
                d_loo.append(min(dtw(ei, ej) for ej in others))
        if d_loo:
            s = float(np.median(d_loo))
            spread[w] = max(s, 1e-6)
            cal_r.extend([d / spread[w] for d in d_loo])
    gmed = float(np.median([s for s in spread.values()])) if spread else 1.0
    for w in vocab:
        spread.setdefault(w, gmed)
    theta_nov = float(np.percentile(cal_r, NOV_PCT)) if cal_r else 2.0
    print(f"  {len(spread)} words with cross-speaker spread; calibration r median {np.median(cal_r):.2f}, "
          f"theta_nov(@{NOV_PCT}th) = {theta_nov:.2f}\n", flush=True)

    def recognise(traj):
        pv = traj.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
        top = np.argsort(-(PW @ pv))[:PRUNE]
        scored = sorted(((vocab[i], min(dtw(traj, e) for (_s, e) in bank[vocab[i]])) for i in top), key=lambda x: x[1])
        (w1, d1), (w2, d2) = scored[0], scored[1]
        return w1, d1, (d2 - d1) / (d2 + d1 + 1e-9)

    # test stream: in-vocab (true word in bank) + OOV (true word not in bank)
    invocab = [(w, proj(lat)) for (w, sp, uid, cf, lat) in test if w in vset][:N_INVOCAB]
    oov = [(w, proj(lat)) for (w, sp, uid, cf, lat) in test if w not in vset][:N_OOV]
    print(f"  scoring {len(invocab)} in-vocab + {len(oov)} OOV test words...", flush=True)

    rows = []   # (is_oov, r, margin, correct)
    for (gold, traj) in invocab:
        w1, d1, m = recognise(traj)
        rows.append((0, d1 / spread[w1], m, int(w1 == gold)))
    for (gold, traj) in oov:
        w1, d1, m = recognise(traj)
        rows.append((1, d1 / spread[w1], m, 0))           # OOV: matched word is never the (OOV) gold -> correct=0

    is_oov = np.array([r[0] for r in rows]); rr = np.array([r[1] for r in rows])
    marg = np.array([r[2] for r in rows]); cor = np.array([r[3] for r in rows])
    au = auroc(rr, is_oov)                                  # does r rank OOV above in-vocab

    # gates on the MIXED stream
    known = rr <= theta_nov
    confident = marg > MARGIN_THRESH
    act_margin = confident                                  # margin-alone (the old gate)
    act_comb = known & confident                            # novelty AND margin
    base = 100 * cor.mean()
    def stats(mask):
        return (100 * mask.mean(), 100 * cor[mask].mean() if mask.any() else float("nan"))
    cov_m, acc_m = stats(act_margin)
    cov_c, acc_c = stats(act_comb)
    # OOV catch: fraction of OOV deferred by novelty
    oov_deferred = 100 * (~known)[is_oov == 1].mean()
    inv_kept = 100 * known[is_oov == 0].mean()

    # ---- the jabberwock's DECISIVE measurement: MATCHED-COVERAGE at the live operating point (~50%) ----
    N = len(rows); TGT = 0.50
    def margin_only_at(target):
        thr = np.quantile(marg, 1 - target)
        act = marg > thr
        return 100 * act.mean(), (100 * cor[act].mean() if act.any() else float("nan")), (100 * is_oov[act].mean() if act.any() else float("nan"))
    def nov_margin_at(target, tnov):
        known = rr <= tnov
        n_act = min(int(round(target * N)), int(known.sum()))
        if n_act <= 0:
            return 0.0, float("nan"), float("nan")
        thr = np.sort(marg[known])[::-1][n_act - 1]
        act = known & (marg >= thr)
        return 100 * act.mean(), 100 * cor[act].mean(), 100 * is_oov[act].mean()
    cov_mo, acc_mo, oov_mo = margin_only_at(TGT)
    cov_nm, acc_nm, oov_nm = nov_margin_at(TGT, theta_nov)

    print("\n" + "=" * 100)
    print(f"  mixed stream: {len(rows)} words ({100*is_oov.mean():.0f}% OOV); base act-on-all {base:.1f}%")
    print(f"  novelty signal r:  AUROC(OOV vs in-vocab) = {au:.3f}   (in-vocab r median {np.median(rr[is_oov==0]):.2f}, OOV {np.median(rr[is_oov==1]):.2f})")
    print(f"  novelty gate @theta_nov {theta_nov:.2f}:  defers {oov_deferred:.0f}% of OOV, keeps {inv_kept:.0f}% of in-vocab")
    print(f"  --- conservative operating point (theta_nov {theta_nov:.2f}, where the gates overlap): ---")
    print(f"    MARGIN-only:    {cov_m:.1f}% cov, ACT acc {acc_m:.1f}%")
    print(f"    NOVELTY+MARGIN: {cov_c:.1f}% cov, ACT acc {acc_c:.1f}%   (+{acc_c-acc_m:.1f}, the redundant region)")
    print(f"  --- DECISIVE: MATCHED {TGT*100:.0f}% coverage (the live operating point where margin LEAKS OOV): ---")
    print(f"    MARGIN-only @{cov_mo:.0f}%:    ACT acc {acc_mo:.1f}%   (ACT set is {oov_mo:.0f}% OOV)")
    print(f"    NOVELTY+MARGIN @{cov_nm:.0f}%: ACT acc {acc_nm:.1f}%   (ACT set is {oov_nm:.0f}% OOV)   delta {acc_nm-acc_mo:+.1f}")
    print("-" * 100)
    if au >= 0.85 and (acc_nm - acc_mo) >= 8.0:
        print(f"  PORT — at matched {TGT*100:.0f}% coverage the novelty gate beats margin-alone by {acc_nm-acc_mo:+.1f} (>=+8): it catches the")
        print(f"  HIGH-margin OOV the margin gate is blind to ({oov_mo:.0f}%->{oov_nm:.0f}% OOV in the ACT set), {acc_mo:.0f}%->{acc_nm:.0f}% accuracy.")
        print("  The second gate earns its keep on exactly the OOV margin leaks. Wire it into the live adapter graph-native.")
    elif au < 0.65:
        print(f"  KILL — r can't separate OOV from cross-speaker in-vocab (AUROC {au:.2f}); whole-word distance is the wrong signal.")
    elif (acc_nm - acc_mo) >= 2.0:
        print(f"  PARTIAL — novelty beats margin by {acc_nm-acc_mo:+.1f} at matched coverage (real, under +8). Helps but the high-margin")
        print("  OOV leak isn't fully closed; the residual is the sub-word/phonotactic case.")
    else:
        print(f"  COLLAPSES TO (B) — novelty adds only {acc_nm-acc_mo:+.1f} even at matched coverage: the margin gate already does the")
        print("  OOV work; just run margin at lower coverage. The residual high-margin-OOV leak is the SUB-WORD build (C).")
    print("=" * 100)


if __name__ == "__main__":
    main()
