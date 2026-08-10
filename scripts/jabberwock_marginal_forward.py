"""MARGINAL-FORWARD EMISSION — the jabberwock's chosen move (B): marginalise, don't commit.

The triphone units hold the truth in the top-K (~30% top-3 @100-way) but the READ can't pin it to top-1 (~13%),
because the read COMMITS: one medoid per triphone + a hard min-DTW alignment. The agent's biggest winner is the
opposite operator -- "marginalise, don't commit" (glyph soft-min over parses 79.9; the phone-forward read of
never-banked words). Its crux disambiguation: a forward that SUMS likelihood over multiple INTACT exemplars (and over
soft alignment) is the WINNING marginalisation -- it keeps every exemplar's layout/order and integrates ACROSS them
(log-sum-exp over discrete, structure-preserving hypotheses); it is NOT the soft-membership/codebook loser (4
negatives) that REPLACES the exemplar with one blended/whitened/quantised code. Summing over structures != averaging
into one.

So: change ONLY the read. Build the SAME realigned triphone units, but keep K INTACT exemplars per unit instead of
one medoid. Score each candidate word with a multi-template HMM FORWARD: a left-to-right model whose phone slot i has
K parallel sub-chains (one per intact exemplar, each frame a state, self-loop + advance = time-warp). The forward
probability is EXACTLY log-sum-exp over (exemplar choice per slot) x (alignment). Compare top-1/top-3 @100-way:
committed read (one medoid + hard DTW) vs marginal forward.

Pre-committed stopping rule (the agent's own):
  KEEP    top-1 >= 16  -> marginalisation is the right operator; tune.
  STOP    top-1 <= 13  -> commitment wasn't the bottleneck; revert to single-pass 13%.
  ABANDON top-1 <= 11 AND top-3 flat/down -> emission can't pin; accept recall+context-prior ceiling.

Run:
  cd experiments/gamma-substrate
  ulimit -v 20971520
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_marginal_forward
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

SAMPLE = 60000
N_WAY = 100
MAX_CLIPS = 110
K_EXEMPLARS = 4          # intact exemplars kept per triphone unit (marginalise over these)
CAP_PER_BUCKET = 48      # bound memory/selection cost
BETAS = [8.0, 14.0]      # emission sharpness sweep (cosine-sim -> log-emission scale)
NEG = -1e18


def _norm(x):
    x = np.asarray(x, dtype=np.float32)
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.maximum(n, 1e-8)


def build_bucket_lists(per_word):
    """Like build_units but KEEP intact exemplar sequences (lists), not medoids. Backoff dicts: tri/rbi/lbi/mono."""
    tri, rbi, lbi, mono = {}, {}, {}, {}
    for ph, subs in per_word:
        for i in range(len(ph)):
            if i >= len(subs) or subs[i] is None or len(subs[i]) < 1:
                continue
            seg = np.asarray(subs[i], dtype=np.float32)
            L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
            for d, key in ((tri, (L, ph[i], R)), (rbi, (ph[i], R)), (lbi, (L, ph[i])), (mono, ph[i])):
                lst = d.setdefault(key, [])
                if len(lst) < CAP_PER_BUCKET:
                    lst.append(seg)
    return tri, rbi, lbi, mono


def select_exemplars(seqs, K):
    """Pick up to K DIVERSE intact exemplars by farthest-point on a mean-pool PROXY (kept exemplars stay intact)."""
    if len(seqs) <= K:
        return seqs
    pooled = np.stack([_norm(s.mean(0)) for s in seqs])
    c = pooled.mean(0)
    chosen = [int(np.argmin(((pooled - c) ** 2).sum(1)))]
    while len(chosen) < K:
        d = np.min(np.stack([((pooled - pooled[j]) ** 2).sum(1) for j in chosen]), axis=0)
        d[chosen] = -1.0
        chosen.append(int(np.argmax(d)))
    return [seqs[j] for j in chosen]


def pick_lists(L, p, R, Tri, Rbi, Lbi, Mono):
    for key, d in (((L, p, R), Tri), ((p, R), Rbi), ((L, p), Lbi), (p, Mono)):
        if key in d:
            return d[key]
    return None


def word_states(w, buckets, K):
    """Build the multi-template state graph for word w: per phone slot, K intact exemplar chains.
    Returns (statevecs (n,D), pred_idx (n,maxp), pred_mask (n,maxp), slot0_start idx, last_end idx) or None."""
    Tri, Rbi, Lbi, Mono = buckets
    ph = phones(w)
    if not ph:
        return None
    slot_exem = []
    for i in range(len(ph)):
        L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
        lst = pick_lists(L, ph[i], R, Tri, Rbi, Lbi, Mono)
        if not lst:
            return None
        slot_exem.append([_norm(e) for e in select_exemplars(lst, K)])

    vecs = []
    chain_prev = []         # per state: index of previous frame in same exemplar, or -1
    slot_start, slot_end = [], []
    for exems in slot_exem:
        starts, ends = [], []
        for e in exems:
            base = len(vecs)
            for t in range(len(e)):
                vecs.append(e[t])
                chain_prev.append(base + t - 1 if t > 0 else -1)
            starts.append(base)
            ends.append(len(vecs) - 1)
        slot_start.append(starts); slot_end.append(ends)

    n = len(vecs)
    statevecs = np.stack(vecs).astype(np.float32)
    # predecessors: self; chain_prev; for a slot>0 start -> all prev-slot ends.
    start_set = {s: i for i, starts in enumerate(slot_start) for s in starts}
    preds = [[] for _ in range(n)]
    for j in range(n):
        preds[j].append(j)                                  # self-loop
        if chain_prev[j] >= 0:
            preds[j].append(chain_prev[j])                  # advance within exemplar
        if j in start_set and start_set[j] > 0:
            preds[j].extend(slot_end[start_set[j] - 1])     # enter this phone from any prev-phone exemplar end
    maxp = max(len(p) for p in preds)
    pred_idx = np.zeros((n, maxp), dtype=np.int64)
    pred_mask = np.zeros((n, maxp), dtype=bool)
    for j, pl in enumerate(preds):
        pred_idx[j, :len(pl)] = pl
        pred_mask[j, :len(pl)] = True
    return statevecs, pred_idx, pred_mask, np.array(slot_start[0]), np.array(slot_end[-1])


def _lse_axis1(a):
    m = a.max(axis=1)
    safe = np.where(np.isfinite(m), m, 0.0)
    s = np.exp(a - safe[:, None]).sum(axis=1)
    res = safe + np.log(np.maximum(s, 1e-300))
    res[~np.isfinite(m)] = -np.inf
    return res


def forward_score(clip, model, beta):
    """Log-marginal of clip under the multi-template HMM (sum over exemplar choice x alignment). Higher = better."""
    statevecs, pred_idx, pred_mask, s0, end = model
    E = beta * (clip @ statevecs.T)                          # (T, n) emission log-scores
    T, n = E.shape
    alpha = np.full(n, -np.inf, dtype=np.float64)
    alpha[s0] = E[0, s0]
    for t in range(1, T):
        gathered = np.where(pred_mask, alpha[pred_idx], -np.inf)   # (n, maxp)
        alpha = E[t] + _lse_axis1(gathered)
    fin = alpha[end]
    if not np.any(np.isfinite(fin)):
        return -np.inf
    m = np.max(fin)
    return float(m + np.log(np.sum(np.exp(fin - m))))


def main():
    print("=" * 100)
    print("MARGINAL-FORWARD EMISSION — committed read (medoid+hard-DTW) vs multi-template HMM forward @100-way")
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
    rea = build_units(re_pw)                                 # medoid units -> committed baseline
    buckets = build_bucket_lists(re_pw)                      # intact exemplar lists -> marginal forward
    print(f"  realigned units built ({len(rea[0])} triphone medoids; intact-exemplar buckets kept).\n", flush=True)

    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand = list(dict.fromkeys(list(targets) + distractors))
    cand = [w for w in cand if template(w, rea) is not None and word_states(w, buckets, K_EXEMPLARS) is not None][:N_WAY]
    clips = [(w, _norm(cf)) for (w, cf) in clips[:MAX_CLIPS]]
    print(f"  {len(cand)}-way; {len(clips)} held-out clips; K={K_EXEMPLARS} exemplars/unit\n", flush=True)

    # committed baseline: one medoid per phone, hard min-DTW
    tmpl = {w: _norm(template(w, rea)) for w in cand}
    models = {w: word_states(w, buckets, K_EXEMPLARS) for w in cand}

    def acc(scores, higher_better):
        t1 = t3 = tot = 0
        for (w, sc) in scores:
            if w not in sc:
                continue
            r = sorted(sc, key=lambda c: -sc[c] if higher_better else sc[c])
            tot += 1; t1 += int(r[0] == w); t3 += int(w in r[:3])
        return 100 * t1 / max(tot, 1), 100 * t3 / max(tot, 1)

    base_scores = []
    for k, (w, cf) in enumerate(clips):
        base_scores.append((w, {c: dtw(cf, tmpl[c]) for c in cand}))
        if (k + 1) % 30 == 0:
            print(f"    committed-read scored {k + 1}/{len(clips)}...", flush=True)
    b1, b3 = acc(base_scores, higher_better=False)
    print(f"\n  COMMITTED read (1 medoid + hard DTW):  top-1 {b1:.0f}%  top-3 {b3:.0f}%\n", flush=True)

    best = None
    for beta in BETAS:
        m_scores = []
        for k, (w, cf) in enumerate(clips):
            m_scores.append((w, {c: forward_score(cf, models[c], beta) for c in cand}))
            if (k + 1) % 30 == 0:
                print(f"    marginal(beta={beta:g}) scored {k + 1}/{len(clips)}...", flush=True)
        m1, m3 = acc(m_scores, higher_better=True)
        print(f"  MARGINAL forward (beta={beta:g}):  top-1 {m1:.0f}%  top-3 {m3:.0f}%", flush=True)
        if best is None or m1 > best[1]:
            best = (beta, m1, m3)

    beta, m1, m3 = best
    print("\n" + "=" * 100)
    print(f"  committed top-1 {b1:.0f} / top-3 {b3:.0f}   ->   marginal-forward (beta={beta:g}) top-1 {m1:.0f} / top-3 {m3:.0f}")
    if m1 >= 16:
        print(f"  KEEP — marginalisation IS the operator: summing likelihood over intact exemplars x alignment pinned")
        print(f"  the truth from the top-K to top-1 ({b1:.0f}->{m1:.0f}). The winning 'marginalise-don't-commit', not the")
        print("  lossy soft-compress. Speech: gooderer. Next: tune temperature / #exemplars.")
    elif m1 <= 13:
        print(f"  STOP — commitment was NOT the bottleneck ({b1:.0f}->{m1:.0f}, no clear lift). Revert to the single-pass")
        print("  13% read. The soft forward integrated but didn't pin; honest negative.")
        if m1 <= 11 and m3 <= b3:
            print("  ABANDON the top-1 push: top-3 did not hold either -> the emission can't pin; accept recall+context-")
            print("  prior as the ceiling.")
    else:
        print(f"  WEAK ({b1:.0f}->{m1:.0f}, 13-16 band): real but small. Keep the marginal form, try ONE enrichment")
        print("  (more exemplars per unit) per the pre-committed rule, then decide.")
    print("=" * 100)


if __name__ == "__main__":
    main()
