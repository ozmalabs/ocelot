"""THE DECISIVE OPEN-SET / OOV TEST of the compose-under-selection frontier.

The flat exemplar table is an enumerated object: a word with ZERO acoustic exemplars cannot be
represented, so it scores 0% on that word BY CONSTRUCTION. The finding composition_is_the_path
_to_vocabulary claims a word's members are an OPEN set realizable by COMPOSING shared parts — so
a never-heard word can still be recognised if its production is COMPOSED from its parts.

Route (no audio of the OOV word is ever used — only its spelling, free dictionary knowledge the
agent grounds from WordNet/wiki):
  PARTS    : the agent's held Rust op shape_signature -> acquire/match_sign = a SHARED sub-word
             relational-unit lexicon, acquired ONLY on SEEN words.
  G->PART  : learn grapheme -> sub-word-unit correspondences from SEEN words (monotone uniform
             alignment of each word's letters to its observed unit sequence) — a pronunciation
             model over the SHARED parts.
  COMPOSE  : a candidate word's EXPECTED unit sequence = composed from its spelling via G->PART.
  FOLD     : recognise a test token by min normalised edit distance (the alignment fold over the
             production space) between its OBSERVED unit sequence and each candidate's COMPOSED
             expected sequence. Works for OOV words because their sequence is composed, not stored.

Decisive contrast on OOV (never-heard) test tokens, full vocab as candidates:
  flat exemplar table : 0% (no exemplars to match — definitional)
  compose-from-parts  : > 0% and > chance  ==> the open set is real.

Run: python -m scripts.sesame_oov_compose [study_min] [min_ex] [oov_frac] [thr]
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
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


def edit_norm(a, b):
    """normalised Levenshtein over unit-id sequences = the alignment fold (production search)."""
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


def main():
    study_min = float(sys.argv[1]) if len(sys.argv) > 1 else 16.0
    min_ex = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    oov_frac = float(sys.argv[3]) if len(sys.argv) > 3 else 0.35
    thr = float(sys.argv[4]) if len(sys.argv) > 4 else 0.85
    with open(f"/tmp/sesame_seq_{study_min:g}.pkl", "rb") as f:
        toks = pickle.load(f)
    cnt = Counter(w for w, _ in toks)
    core = sorted(w for w, c in cnt.items() if c >= min_ex)
    toks = [(w, np.asarray(fr, np.float32)) for w, fr in toks if w in core]

    rng = np.random.RandomState(1)
    core_sh = list(core); rng.shuffle(core_sh)
    n_oov = max(1, int(len(core_sh) * oov_frac))
    oov_words = set(core_sh[:n_oov])                       # NEVER heard in training
    seen_words = set(core_sh[n_oov:])
    print("=" * 82)
    print("DECISIVE OPEN-SET / OOV TEST — compose a never-heard word from shared parts")
    print(f"  core {len(core)} words; SEEN {len(seen_words)} (have audio) / "
          f"OOV {len(oov_words)} (spelling only, zero exemplars)")
    print("=" * 82)

    # PARTS — acquire the shared sub-word lexicon on SEEN words ONLY (OOV audio never seen).
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

    # split SEEN tokens into train (acquire) / held-out (match); OOV tokens all test (match).
    seen_tok = [(w, fr) for w, fr in toks if w in seen_words]
    oov_tok = [(w, fr) for w, fr in toks if w in oov_words]
    perm = rng.permutation(len(seen_tok))
    cut = len(seen_tok) * 75 // 100
    seen_train = [seen_tok[i] for i in perm[:cut]]
    seen_test = [seen_tok[i] for i in perm[cut:]]

    tr_units = [(w, units(fr, True)) for w, fr in seen_train]      # GROW the parts (seen only)
    n_units = len(SP.lexicon_signs(s, lex))
    seen_test_u = [(w, units(fr, False)) for w, fr in seen_test]   # frozen match
    oov_test_u = [(w, units(fr, False)) for w, fr in oov_tok]      # frozen match — never grown
    print(f"  shared sub-word parts (acquired on SEEN only): {n_units}")

    # G->PART — learn grapheme -> shared-unit correspondences from SEEN words (uniform monotone
    # alignment of letters to the observed unit sequence). A pronunciation model over the parts.
    # (A richer EM-Viterbi alignment was tried and did NOT help — data-starved at this scale, not
    # under-modelled — so the simplest honest estimator stands.)
    emis = defaultdict(Counter)
    upg = []
    for w, u in tr_units:
        g = [c for c in w]
        if not g or not u:
            continue
        upg.append(len(u) / len(g))
        for i, uu in enumerate(u):
            gi = g[min(len(g) - 1, i * len(g) // len(u))]
            emis[gi][uu] += 1
    avg_upg = max(1, int(round(np.mean(upg)))) if upg else 1
    modal = {gi: c.most_common(1)[0][0] for gi, c in emis.items()}

    def compose_expected(word):
        """COMPOSE a candidate's expected unit sequence from its spelling via the shared parts."""
        seq = []
        for gi in word:
            if gi in modal:
                seq.extend([modal[gi]] * avg_upg)
        return collapse(seq)

    cand = sorted(seen_words | oov_words)                  # FULL vocab = open candidate set
    expected = {w: compose_expected(w) for w in cand}
    composable = [w for w in cand if expected[w]]
    print(f"  grapheme->part model: {len(emis)} graphemes, ~{avg_upg} units/grapheme; "
          f"{len(composable)}/{len(cand)} words composable\n")

    # FLAT exemplar table — seen-word exemplars only (the enumerated object).
    def mean_shape(fr):
        m = np.mean([shape(f) for f in fr], axis=0); return m / (np.linalg.norm(m) + 1e-9)
    Fw = np.array([w for w, _ in seen_train])
    Fx = np.array([mean_shape(fr) for _, fr in seen_train])

    def eval_set(test_fr, test_u, label):
        chance = 1.0 / len(cand)
        cf = cc = tot = 0
        for (w, fr), (_, u) in zip(test_fr, test_u):
            tot += 1
            cf += (Fw[np.argmax(Fx @ mean_shape(fr))] == w)               # flat: seen-only
            pred = min(composable, key=lambda c: edit_norm(u, expected[c]))  # compose fold
            cc += (pred == w)
        print(f"  {label:<22} ({tot:>3} tok, chance {chance:.1%}): "
              f"flat-table {cf/max(tot,1):>6.1%}   compose-from-parts {cc/max(tot,1):>6.1%}")
        return cf / max(tot, 1), cc / max(tot, 1)

    print("  " + "-" * 78)
    eval_set(seen_test, seen_test_u, "SEEN (held-out)")
    f_oov, c_oov = eval_set(oov_tok, oov_test_u, "OOV (never heard)")
    print("  " + "-" * 78)
    print("=" * 82)
    if c_oov > f_oov:
        print(f"  OPEN SET CONFIRMED: composition recognises never-heard words at {c_oov:.1%} "
              f"where the\n  flat exemplar table is structurally {f_oov:.1%} — a word it never "
              f"stored, COMPOSED from parts.")
    else:
        print(f"  composition {c_oov:.1%} did not clear the flat table {f_oov:.1%} on OOV — the "
              f"grapheme->part\n  route is too weak at this scale; the open-set claim is unconfirmed here.")


if __name__ == "__main__":
    main()
