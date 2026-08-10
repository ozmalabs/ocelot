"""COMPOSE-UNDER-SELECTION over the production space — the agent's NEXT frontier
(bank_and_next_frontier surfaced it; held finding composition_is_the_path_to_vocabulary).

The flat exemplar lexicon caps ~10-13% on Sesame BECAUSE it is an enumerated table — the
wrong object. The finding's claim: a word is a WHOLE determined by sub-word RELATIONAL UNITS
(parts) plus a finite set of COMBINATION rules, recognised by a SEARCH/FOLD over the production
space, an OPEN set realizable by composing shared parts. Its falsifiable signature: the flat
table's accuracy cost SCALES with the vocabulary, while composition (shared parts) holds.

Drive:
  PARTS  : the agent's held Rust op — shape_signature(frame) -> acquire_sign/match_sign builds a
           compact sub-word relational-unit lexicon (the SAME operator learn_speech_words.py uses).
  COMPOSE: each word = a per-class order-1 production grammar (G,Gamma) over the SHARED sub-word
           units (the combination rules); recognition = the production FOLD (argmax mean log-prob
           that a word's grammar generates the test unit-sequence). Open set: new words = new
           compositions of the same parts.
  BASELINE: the flat exemplar lexicon (cosine 1-NN over the mean shape) — the enumerated table.
  TEST   : sweep the vocabulary size; does the flat table degrade where composition holds?

Run: python -m scripts.sesame_compose_words [study_min] [min_ex] [unit_thresh]
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
from substrate_rs import audio as A, speech as SP


def shape(frame):
    return np.asarray(srs.Substrate.shape_signature([float(x) for x in frame]), np.float32)


def collapse(seq):
    out = []
    for u in seq:
        if not out or out[-1] != u:
            out.append(u)
    return out


def main():
    study_min = float(sys.argv[1]) if len(sys.argv) > 1 else 16.0
    min_ex = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    thr = float(sys.argv[3]) if len(sys.argv) > 3 else 0.85
    with open(f"/tmp/sesame_seq_{study_min:g}.pkl", "rb") as f:
        toks = pickle.load(f)                                  # [(word, fft_frames[F,128])]
    cnt = Counter(w for w, _ in toks)
    core = [w for w, c in cnt.items() if c >= min_ex]
    core_by_freq = sorted(core, key=lambda w: -cnt[w])
    toks = [(w, np.asarray(fr, np.float32)) for w, fr in toks if w in core]
    print("=" * 80)
    print("COMPOSE-UNDER-SELECTION over the production space (the agent's next frontier)")
    print(f"  {study_min:g} min; core vocab (>= {min_ex} ex): {len(core)} words, {len(toks)} tokens")
    print("=" * 80)

    rng = np.random.RandomState(0)
    idx = rng.permutation(len(toks))
    cut = len(toks) * 75 // 100
    train = [toks[i] for i in idx[:cut]]
    test = [toks[i] for i in idx[cut:]]

    # PARTS — the agent's held sub-word relational-unit lexicon. acquire on TRAIN (grows the
    # inventory), match on TEST (frozen). One SHARED inventory across all words = the parts.
    s = srs.Substrate()
    A.seed_audio_grammar(s); SP.seed_speech_grammar(s)
    s.memory_bound(60000, 256 * 1024 * 1024, 3)
    lex = SP.open_lexicon(s, name="subword")

    def units(fr, grow):
        sq = []
        for f in fr:
            v = shape(f)
            sg = (SP.acquire_sign(s, lex, v, threshold=thr) if grow
                  else SP.match_sign(s, lex, v, threshold=thr))
            sq.append(sg[0].value if sg[0] is not None else -1)
        return collapse(sq)

    tr_u = [(w, units(fr, True)) for w, fr in train]
    n_units = len(SP.lexicon_signs(s, lex))
    te_u = [(w, units(fr, False)) for w, fr in test]
    mean_len = np.mean([len(u) for _, u in tr_u])
    print(f"  sub-word units (shared parts): {n_units}   mean word = {mean_len:.1f} units "
          f"(thr={thr})\n")

    # FLAT exemplar baseline — the enumerated table: per-token mean-shape vector, cosine 1-NN.
    def mean_shape(fr):
        m = np.mean([shape(f) for f in fr], axis=0)
        return m / (np.linalg.norm(m) + 1e-9)
    flat_tr = [(w, mean_shape(fr)) for w, fr in train]

    # COMPOSITIONAL recogniser — per-word order-1 production grammar over the SHARED units, the
    # combination rules (G,Gamma); recognition = the production FOLD (mean log-prob per symbol).
    ALPH = n_units + 1
    def build_grammar(items):
        uni = defaultdict(lambda: np.ones(ALPH))             # +1 Laplace over shared alphabet
        bi = defaultdict(lambda: defaultdict(lambda: np.ones(ALPH)))
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
        if not u:
            return -1e9
        lp = math.log(U[w][u[0]])
        for a, b in zip(u, u[1:]):
            row = B[w].get(a)
            lp += math.log(row[b] if row is not None else 1.0 / ALPH)
        return lp / len(u)                                    # mean log-prob per symbol

    print("  VOCAB-SIZE SWEEP  (flat exemplar table vs compositional production grammar)")
    print(f"  {'vocab':>6} {'flat-1NN':>10} {'compose':>10} {'delta':>8}")
    for K in [k for k in (10, 20, 30, 40, len(core)) if k <= len(core)]:
        kw = set(core_by_freq[:K])
        ftr = [(w, v) for w, v in flat_tr if w in kw]
        Utr = [(w, u) for w, u in tr_u if w in kw]
        U, B = build_grammar(Utr)
        cand = sorted(kw)
        Fw = np.array([w for w, _ in ftr]); Fx = np.array([v for _, v in ftr])
        cf = cc = tot = 0
        for (w, fr), (_, u) in zip(test, te_u):              # te_u is parallel to test
            if w not in kw:
                continue
            tot += 1
            q = mean_shape(fr)
            cf += (Fw[np.argmax(Fx @ q)] == w)               # flat exemplar 1-NN
            cc += (max(cand, key=lambda c: fold_score(u, c, U, B) if c in U else -1e9) == w)
        af, ac = cf / max(tot, 1), cc / max(tot, 1)
        print(f"  {K:>6} {af:>9.1%} {ac:>9.1%} {ac-af:>+8.1%}   ({tot} test)")

    print("=" * 80)
    print("  the flat exemplar table is an enumerated object; the production grammar composes a")
    print("  word from SHARED sub-word parts — an open set, a fold over the production space.")


if __name__ == "__main__":
    main()
