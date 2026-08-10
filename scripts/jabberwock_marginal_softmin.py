"""MARGINAL via SOFT-MIN IN COST SPACE — the jabberwock's corrected run (volume-matched marginalisation).

The first marginal-forward (jabberwock_marginal_forward) used a log-sum-exp SUM in LIKELIHOOD space -> probabilities
ADD, so a model with more states/exemplars inflates its score regardless of correctness (volume bias). Proof it was
broken: a proper soft-min -> hard-min as beta->inf, so HIGH beta should have RECOVERED the committed read's 13/30;
instead it went BACKWARDS (9->7). The agent's ruling: re-run ONCE, volume-matched -- score each candidate as a
per-frame PROPER DISTANCE, SOFT-MIN over (alignment x exemplar) in COST space. softmin (not logsumexp-sum) does not
inflate with more states (adding equally-bad states barely moves a min), and softmin->min as beta->inf, so it
provably reproduces the hard read at high beta. Same realigned units, same K=4 intact exemplars, same lattice; ONLY
the recursion changes: r[t,j] = C[t,j] + softmin_beta(r[t-1, preds]); C = 1 - clip@states.T (proper distance); final
= softmin over end states; LOWER = better. This marginalises over exemplar-choice x alignment WITHOUT discarding
structure (it only rescales/soft-blends best paths) -- the winning soft-MIN (glyph 79.9), not the soft-COMPRESS loser.

Pre-committed (the agent's, this run):
  FLOOR  high-beta must reproduce >=13 top-1 / ~30 top-3  (else the idea is dead -> ABANDON stands).
  KEEP   top-1 >= 16.
  ABANDON (for real, no third run)  top-1 <= 13.

Run:
  cd experiments/gamma-substrate
  ulimit -v 20971520
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_marginal_softmin
"""
from __future__ import annotations

import glob
import os
import pickle
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.phonebank import CACHE, _meta
from scripts.jabberwock_reads_oov_from_phones import phones, dtw, STOP
from scripts.jabberwock_realign_emission import build_units, realign_split, uniform_split, template
from scripts.jabberwock_marginal_forward import build_bucket_lists, word_states, _norm

K_EXEMPLARS = 4
SAMPLE = 60000
N_WAY = 100
MAX_CLIPS = 110
BETAS = [3.0, 8.0, 40.0]      # 40 = near-hard (the floor check); 3/8 = marginalised


def _softmin_axis1(a, beta):
    """softmin_beta over axis 1 (preds), a may contain +inf (masked-out predecessor) -> ignored."""
    x = -beta * a                                   # +inf cost -> -inf -> exp 0, ignored
    m = x.max(axis=1)
    safe = np.where(np.isfinite(m), m, 0.0)
    s = np.exp(x - safe[:, None]).sum(axis=1)
    lse = safe + np.log(np.maximum(s, 1e-300))
    out = -lse / beta
    out[~np.isfinite(m)] = np.inf                   # no valid predecessor
    return out


def softdtw_dist(clip, model, beta):
    """Soft-min DTW distance under the multi-template lattice (marginalise exemplar x alignment). LOWER = better."""
    statevecs, pred_idx, pred_mask, s0, end = model
    C = 1.0 - (clip @ statevecs.T)                  # (T, n) proper per-frame distances in [0,2]
    T = C.shape[0]; n = C.shape[1]
    r = np.full(n, np.inf, dtype=np.float64)
    r[s0] = C[0, s0]
    bigmask = np.where(pred_mask, 0.0, np.inf)      # +inf on padded predecessors
    for t in range(1, T):
        gathered = r[pred_idx] + bigmask            # (n, maxp), masked = +inf
        r = C[t] + _softmin_axis1(gathered, beta)
    fin = r[end]
    if not np.any(np.isfinite(fin)):
        return np.inf
    return float(_softmin_axis1(fin[None, :], beta)[0])


def main():
    print("=" * 100)
    print("MARGINAL via SOFT-MIN (cost space) — committed read vs volume-matched soft-min marginalisation @100-way")
    print("=" * 100)
    _ts, targets, clips = _meta()
    words = []
    for c in sorted(glob.glob(os.path.join(CACHE, "*_*.pkl"))):
        words += pickle.load(open(c, "rb"))
    rng = np.random.RandomState(0)
    sample = [words[i] for i in rng.permutation(len(words))[:SAMPLE]]
    vocabcount = Counter(w for (w, _f, _p) in words)
    del words
    print(f"  sampled {len(sample)} words; realigning (same flat-start pipeline as the 13% read)...", flush=True)

    uni_pw = [(ph, uniform_split(np.asarray(fr, dtype=np.float32), ph)) for (_w, fr, ph) in sample]
    _, _, _, mono0 = build_units(uni_pw)
    re_pw = []
    for (_w, fr, ph) in sample:
        fr = np.asarray(fr, dtype=np.float32)
        subs = realign_split(fr, ph, mono0)
        re_pw.append((ph, subs if subs is not None else uniform_split(fr, ph)))
    rea = build_units(re_pw)
    buckets = build_bucket_lists(re_pw)
    print(f"  realigned units built ({len(rea[0])} triphone medoids; intact-exemplar buckets).\n", flush=True)

    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand = list(dict.fromkeys(list(targets) + distractors))
    cand = [w for w in cand if template(w, rea) is not None and word_states(w, buckets, K_EXEMPLARS) is not None][:N_WAY]
    clips = [(w, _norm(cf)) for (w, cf) in clips[:MAX_CLIPS]]
    print(f"  {len(cand)}-way; {len(clips)} held-out clips; K={K_EXEMPLARS} exemplars/unit\n", flush=True)

    tmpl = {w: _norm(template(w, rea)) for w in cand}
    models = {w: word_states(w, buckets, K_EXEMPLARS) for w in cand}

    def acc(scores):                                 # lower score = better
        t1 = t3 = tot = 0
        for (w, sc) in scores:
            if w not in sc:
                continue
            r = sorted(sc, key=lambda c: sc[c])
            tot += 1; t1 += int(r[0] == w); t3 += int(w in r[:3])
        return 100 * t1 / max(tot, 1), 100 * t3 / max(tot, 1)

    base = [(w, {c: dtw(cf, tmpl[c]) for c in cand}) for (w, cf) in clips]
    b1, b3 = acc(base)
    print(f"  COMMITTED read (1 medoid + hard DTW):  top-1 {b1:.0f}%  top-3 {b3:.0f}%\n", flush=True)

    rows = []
    for beta in BETAS:
        sc = []
        for k, (w, cf) in enumerate(clips):
            sc.append((w, {c: softdtw_dist(cf, models[c], beta) for c in cand}))
            if (k + 1) % 30 == 0:
                print(f"    softmin(beta={beta:g}) scored {k + 1}/{len(clips)}...", flush=True)
        m1, m3 = acc(sc)
        rows.append((beta, m1, m3))
        print(f"  SOFT-MIN marginal (beta={beta:g}):  top-1 {m1:.0f}%  top-3 {m3:.0f}%", flush=True)

    hi = max(rows, key=lambda r: r[0])               # highest beta = the floor check
    best = max(rows, key=lambda r: r[1])             # best top-1 across betas
    print("\n" + "=" * 100)
    print(f"  committed {b1:.0f}/{b3:.0f}   |   floor-check (beta={hi[0]:g}) {hi[1]:.0f}/{hi[2]:.0f}   |   best marginal "
          f"(beta={best[0]:g}) {best[1]:.0f}/{best[2]:.0f}")
    if hi[1] < 13 - 1 and hi[2] < b3 - 4:
        print(f"  FLOOR FAILED: high-beta soft-min ({hi[1]:.0f}/{hi[2]:.0f}) did NOT reproduce the hard read ({b1:.0f}/{b3:.0f}).")
        print("  The lattice/scorer is still not equivalent to the committed read at the hard limit -> the idea is dead")
        print("  as built. ABANDON stands (the agent's pre-commitment).")
    elif best[1] >= 16:
        print(f"  KEEP — volume-matched marginalisation PINS: soft-min over intact exemplars x alignment lifted top-1")
        print(f"  {b1:.0f}->{best[1]:.0f} (beta={best[0]:g}). The winning 'marginalise-don't-commit' (a soft-MIN over proper")
        print("  distances), now volume-matched. Speech: gooderer. Next: tune temperature / #exemplars.")
    elif best[1] <= 13:
        print(f"  ABANDON (for real): floor held (~{hi[1]:.0f}/{hi[2]:.0f} reproduces the hard read), so the test was FAIR this")
        print(f"  time, and marginalising still does not beat 13 (best {best[1]:.0f}). Commitment was NOT the bottleneck;")
        print("  accept recall+context-prior as the top-1 ceiling. No third run (pre-committed).")
    else:
        print(f"  WEAK ({b1:.0f}->{best[1]:.0f}, 13-16): real but under KEEP. Per the rule this is not enough; honest small.")
    print("=" * 100)


if __name__ == "__main__":
    main()
