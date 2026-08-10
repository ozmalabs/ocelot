"""DRIVE THE CATEGORICAL-QUANTISER LEVER — unblock the compositional frontier.

The compose-under-selection null was bottlenecked on the PARTS: acquire_sign is a fixed-threshold
greedy leader-follower (too few units = lossy, too many = sparse). The agent's held categorical
quantiser is distributional_categories.cluster_by_modes: a LABEL-FREE, TOLD-k-FREE continuous->
discrete map — categories are the density MODES of the data (carved at valleys), found by the
agent's OWN order-N peak operator (density = Count over near-neighbours; climb = mean-shift to a
mode). The part count EMERGES from the distribution, not a swept threshold.

Swap the quantiser, hold everything else, re-run BOTH measurements and compare to acquire_sign:
  PART A  in-vocab vocab-size sweep  (flat exemplar table vs compositional production grammar)
  PART B  the decisive OOV / open-set test (never-heard word, composed from spelling via parts)

flat-table numbers are quantiser-INDEPENDENT (mean shape, no parts) so they are the fixed
reference; only COMPOSE moves. Run: python -m scripts.sesame_quantiser_compose [study_min] [min_ex] [pctile]
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import math
import pickle
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import substrate_rs as srs
from domains.distributional_categories import cluster_by_modes

CLUSTER_SAMPLE = 2500


def shape(frame):
    return np.asarray(srs.Substrate.shape_signature([float(x) for x in frame]), np.float32)


def collapse(seq):
    out = []
    for u in seq:
        if not out or out[-1] != u:
            out.append(u)
    return out


def edit_norm(a, b):
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1] / max(len(a), len(b))


def learn_quantiser(frame_vecs, pctile, seed=0):
    """the agent's held categorical quantiser: density-mode centroids (told-k-free)."""
    M = np.asarray(frame_vecs, np.float32)
    rng = np.random.RandomState(seed)
    samp = M[rng.permutation(len(M))[:CLUSTER_SAMPLE]]
    labels, n_modes = cluster_by_modes(samp, pctile=pctile, seed=seed)
    labels = np.asarray(labels)
    cents = np.array([samp[labels == k].mean(0) for k in range(n_modes)])    # mode prototypes
    return cents


def quantise_seq(frames, cents):
    sq = []
    for f in frames:
        v = shape(f)
        sq.append(int(np.argmin(((cents - v) ** 2).sum(1))))                 # nearest mode
    return collapse(sq)


def main():
    study_min = float(sys.argv[1]) if len(sys.argv) > 1 else 16.0
    min_ex = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    pctile = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
    with open(f"/tmp/sesame_seq_{study_min:g}.pkl", "rb") as f:
        toks = pickle.load(f)
    cnt = Counter(w for w, _ in toks)
    core = sorted(w for w, c in cnt.items() if c >= min_ex)
    core_by_freq = sorted(core, key=lambda w: -cnt[w])
    toks = [(w, np.asarray(fr, np.float32)) for w, fr in toks if w in core]
    print("=" * 84)
    print("CATEGORICAL QUANTISER (density modes) -> compositional frontier")
    print(f"  {study_min:g} min; core {len(core)} words, {len(toks)} tokens; pctile={pctile}")
    print("=" * 84)

    def mean_shape(fr):
        m = np.mean([shape(f) for f in fr], 0); return m / (np.linalg.norm(m) + 1e-9)

    # ---------- PART A : in-vocab vocab-size sweep ----------
    rng = np.random.RandomState(0)
    idx = rng.permutation(len(toks)); cut = len(toks) * 75 // 100
    train = [toks[i] for i in idx[:cut]]; test = [toks[i] for i in idx[cut:]]
    cents = learn_quantiser([shape(f) for _, fr in train for f in fr], pctile)
    print(f"  PART A — learned parts (density modes): {len(cents)}")
    tr_u = [(w, quantise_seq(fr, cents)) for w, fr in train]
    te_u = [(w, quantise_seq(fr, cents)) for w, fr in test]
    flat_tr = [(w, mean_shape(fr)) for w, fr in train]
    ALPH = len(cents)

    def build_grammar(items):
        uni = defaultdict(lambda: np.ones(ALPH)); bi = defaultdict(lambda: defaultdict(lambda: np.ones(ALPH)))
        for w, u in items:
            if not u:
                continue
            uni[w][u[0]] += 1
            for a, b in zip(u, u[1:]):
                bi[w][a][b] += 1
        U = {w: v / v.sum() for w, v in uni.items()}
        B = {w: {a: r / r.sum() for a, r in d.items()} for w, d in bi.items()}
        return U, B

    def fold_score(u, w, U, B):
        if not u or w not in U:
            return -1e9
        lp = math.log(U[w][u[0]])
        Bw = B.get(w, {})
        for a, b in zip(u, u[1:]):
            row = Bw.get(a); lp += math.log(row[b] if row is not None else 1.0 / ALPH)
        return lp / len(u)

    print(f"  {'vocab':>6} {'flat-1NN':>10} {'compose':>10} {'delta':>8}   (acquire_sign compose)")
    ref = {10: 21.7, 20: 14.7, 30: 11.5, 40: 10.0, len(core): 7.9}
    for K in [k for k in (10, 20, 30, 40, len(core)) if k <= len(core)]:
        kw = set(core_by_freq[:K])
        U, B = build_grammar([(w, u) for w, u in tr_u if w in kw])
        candK = sorted(kw)
        Fw = np.array([w for w, _ in flat_tr if w in kw]); Fx = np.array([v for w, v in flat_tr if w in kw])
        cf = cc = tot = 0
        for (w, fr), (_, u) in zip(test, te_u):
            if w not in kw:
                continue
            tot += 1
            cf += (Fw[np.argmax(Fx @ mean_shape(fr))] == w)
            cc += (max(candK, key=lambda c: fold_score(u, c, U, B)) == w)
        af, ac = cf / max(tot, 1), cc / max(tot, 1)
        print(f"  {K:>6} {af:>9.1%} {ac:>9.1%} {ac-af:>+8.1%}   (was {ref.get(K,0):.1f}%)")

    # ---------- PART B : the decisive OOV / open-set test ----------
    rng2 = np.random.RandomState(1)
    core_sh = list(core); rng2.shuffle(core_sh)
    n_oov = max(1, int(len(core_sh) * 0.35))
    oov_words = set(core_sh[:n_oov]); seen_words = set(core_sh[n_oov:])
    seen_tok = [(w, fr) for w, fr in toks if w in seen_words]
    oov_tok = [(w, fr) for w, fr in toks if w in oov_words]
    perm = rng2.permutation(len(seen_tok)); cutS = len(seen_tok) * 75 // 100
    seen_train = [seen_tok[i] for i in perm[:cutS]]; seen_test = [seen_tok[i] for i in perm[cutS:]]
    centsB = learn_quantiser([shape(f) for _, fr in seen_train for f in fr], pctile, seed=1)  # SEEN only
    print(f"\n  PART B — OOV test; parts on SEEN only (density modes): {len(centsB)}; "
          f"SEEN {len(seen_words)} / OOV {len(oov_words)}, chance {1/len(core):.1%}")
    trB = [(w, quantise_seq(fr, centsB)) for w, fr in seen_train]

    emis = defaultdict(Counter); upg = []
    for w, u in trB:
        g = list(w)
        if not g or not u:
            continue
        upg.append(len(u) / len(g))
        for i, uu in enumerate(u):
            emis[g[min(len(g) - 1, i * len(g) // len(u))]][uu] += 1
    avg_upg = max(1, int(round(np.mean(upg)))) if upg else 1
    modal = {gi: c.most_common(1)[0][0] for gi, c in emis.items()}
    cand = sorted(seen_words | oov_words)
    expected = {w: collapse([modal[gi] for gi in w if gi in modal]) for w in cand}
    composable = [w for w in cand if expected[w]]
    FwB = np.array([w for w, _ in seen_train]); FxB = np.array([mean_shape(fr) for _, fr in seen_train])

    def eval_set(items, label):
        cf = cc = tot = 0
        for w, fr in items:
            tot += 1
            cf += (FwB[np.argmax(FxB @ mean_shape(fr))] == w)
            u = quantise_seq(fr, centsB)
            cc += (min(composable, key=lambda c: edit_norm(u, expected[c])) == w)
        print(f"  {label:<20} ({tot:>3} tok): flat {cf/max(tot,1):>6.1%}   compose {cc/max(tot,1):>6.1%}")

    eval_set(seen_test, "SEEN (held-out)")
    eval_set(oov_tok, "OOV (never heard)")
    print("=" * 84)
    print("  acquire_sign was: in-vocab compose 21.7..7.9%, OOV compose 2.3%. Did density-mode")
    print("  parts (the agent's learned categorical quantiser) sharpen composition?")


if __name__ == "__main__":
    main()
