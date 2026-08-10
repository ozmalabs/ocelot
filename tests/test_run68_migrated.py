"""test_run68_migrated.py -- unit gates for RUN 68 (bidirectional interactive-activation reading).

Gates the machinery BEFORE the expensive eval (ops law "unit tests first"):
  * the IA loop converges to a fixpoint on a synthetic candidate set;
  * lambda=0.0 reproduces the one-directional (arm A) decode EXACTLY -- a hard invariant of the
    two-tier normalization design (see the design note in jabberwock_ia_read_run68.py);
  * a synthetic WEAK-LETTER case: top-down feedback FLIPS the decode to the lexicon-correct word
    when bottom-up evidence for one letter is ambiguous but the other positions pin the word (the
    word-superiority-effect mechanism, McClelland & Rumelhart 1981);
  * arm A reproduces run 61's exact lexicon_flat baseline (234/300 = 78.0% word, 90.3% char) on
    run 61's REAL cross-writer DigiLeTs lattice, read READ-ONLY;
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

System python3 (per ops law: this run has no substrate_rs dependency -- it consumes run 61's
precomputed geometry distances, no native calls).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np
import pytest

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.jabberwock_ia_read_run68 as r68

STROKE_SHAPES_SEED = r68.STROKE_SHAPES_SEED


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run68_migrated.py"


# --------------------------------------------------------------------------------------------- #
# Synthetic harness: a tiny length-3 candidate set + hand-built bottom-up evidence.
# --------------------------------------------------------------------------------------------- #
def _b_for(word: str, strength: float = 5.0) -> np.ndarray:
    """Strong, unambiguous bottom-up evidence for `word` at every position (b[i][true]=strength,
    all other letters 0)."""
    L = len(word)
    b = np.zeros((L, 26), dtype=np.float64)
    for i, ch in enumerate(word):
        b[i, r68._lower26(ch)] = strength
    return b


CANDS3 = ["cat", "car", "cap", "dog"]


def test_ia_converges_to_fixpoint():
    """The loop reaches a fixpoint (raw_W stops changing) within MAX_ITERS, for lambda>0."""
    b = _b_for("cat", strength=2.0)
    res = r68.ia_decode(b, CANDS3, None, lam=0.5, max_iters=r68.MAX_ITERS)
    assert res["converged"], "IA loop did not converge within MAX_ITERS"
    assert res["n_iters"] <= r68.MAX_ITERS
    # re-running one more iteration from the converged a_L should not move raw_W (true fixpoint).
    res2 = r68.ia_decode(res["a_L"], CANDS3, None, lam=0.0, max_iters=1)
    # raw_W at the fixpoint (computed from res["a_L"] with no further feedback) should already
    # rank the same top word as the converged decode.
    assert res2["word"] == res["word"]


def test_lambda_zero_matches_one_directional():
    """lambda=0.0 is EXACTLY the one-directional (arm A) argmax -- word-for-word AND score-for-
    score, on several synthetic evidence patterns, not just a coincidence on one example."""
    for word, strength in [("cat", 3.0), ("car", 1.5), ("cap", 0.3)]:
        b = _b_for(word, strength=strength)
        arm_a_raw = np.array([sum(b[i, r68._lower26(ch)] for i, ch in enumerate(w))
                               for w in CANDS3])
        arm_a_word = CANDS3[int(np.argmax(arm_a_raw))]

        res = r68.ia_decode(b, CANDS3, None, lam=0.0, max_iters=r68.MAX_ITERS)
        assert res["word"] == arm_a_word
        assert res["n_iters"] == 1, "lambda=0 must be an immediate fixpoint (no feedback to iterate)"
        assert np.allclose(res["raw_W"], arm_a_raw), "lambda=0 raw scores must match arm A exactly"
        assert np.array_equal(res["a_L"], b), "lambda=0 must leave a_L == b (no feedback applied)"


def test_lambda_zero_matches_one_directional_on_real_lattice_row():
    """Same invariant, but on a REAL run-61 lattice row (not hand-built evidence) -- confirms the
    exact-reproduction property holds on the actual geometry distances, not just clean synthetics."""
    if not os.path.exists(r68.RUN61_LATTICES):
        pytest.skip("run 61 lattices not present")
    lat = r68._load_json(r68.RUN61_LATTICES)
    lex = r68._load_json(r68.RUN61_LEXICON)
    lex_by_len = r68.build_lex_by_len(lex["lexicon"])
    L0 = lat["lattices"][0]
    b = r68.bottom_up_from_dists62(L0["dists"])
    cands = lex_by_len[len(L0["word"])]
    arm_a_raw = np.array([sum(b[i, r68._lower26(ch)] for i, ch in enumerate(w)) for w in cands])
    arm_a_word = cands[int(np.argmax(arm_a_raw))]
    res = r68.ia_decode(b, cands, None, lam=0.0)
    assert res["word"] == arm_a_word
    assert res["n_iters"] == 1


def test_wse_flip_synthetic():
    """THE WSE MECHANISM (McClelland & Rumelhart 1981): a POPULATION of lexicon words consistent
    with the TRUE letter at position 0 ('a': at/an/as/ax/ab) collectively out-votes a single
    strong DISTRACTOR word ('ip') that individually edges out any ONE 'a'-word bottom-up. This is
    the real IA mechanism -- it is not that any single competing word is stronger, it is that many
    weaker-but-consistent words pool activation onto the shared correct letter. Bottom-up ALONE
    (arm A) has no way to aggregate across candidates, so it picks the single best-scoring
    candidate ('ip', WRONG); the bidirectional loop pools p_W-weighted feedback from ALL five
    'a'-words onto position 0, and once a_L[0,'a'] > a_L[0,'i'] the correct word 'at' overtakes
    'ip' in the word-level sum too."""
    cands = ["at", "an", "as", "ax", "ab", "ip"]     # 5 words share pos0='a' (true); "ip"=pos0='i'.
    L = 2
    b = np.zeros((L, 26), dtype=np.float64)
    b[0, r68._lower26("a")] = 1.0
    b[0, r68._lower26("i")] = 1.05                    # 'i' edges out 'a' bottom-up, individually.
    for ch in ("t", "n", "s", "x", "b"):
        b[1, r68._lower26(ch)] = 1.0                  # each 'a'-word's own 2nd letter, comparable.
    b[1, r68._lower26("p")] = 1.10                    # "ip"'s 2nd letter, slightly ahead too.

    arm_a = r68.ia_decode(b, cands, None, lam=0.0)
    assert arm_a["word"] == "ip", "test setup check: one-directional must pick the WRONG word"

    arm_b = r68.ia_decode(b, cands, None, lam=0.5, max_iters=50)
    assert arm_b["word"] == "at", ("bidirectional feedback should flip the decode to the true "
                                    "word via population support at the ambiguous letter (WSE)")
    assert arm_b["converged"], "expect a true fixpoint within 50 iterations on this small example"


def test_wse_flip_requires_feedback_strength():
    """Sanity: the flip in the previous test is a genuine population-support effect, not a
    lambda artifact -- if the bottom-up gap at the ambiguous position is made HUGE (instead of a
    near-tie), no reasonable feedback strength should be able to override it (feedback multiplies
    a decent posterior, it does not manufacture one -- the C2 'multiplier not substitute'
    warning)."""
    cands = ["at", "an", "as", "ax", "ab", "ip"]
    L = 2
    b = np.zeros((L, 26), dtype=np.float64)
    b[0, r68._lower26("a")] = 1.0
    b[0, r68._lower26("i")] = 5.0                     # huge gap now, not a near-tie.
    for ch in ("t", "n", "s", "x", "b"):
        b[1, r68._lower26(ch)] = 1.0
    b[1, r68._lower26("p")] = 1.10

    for lam in (0.25, 0.5, 1.0):
        r = r68.ia_decode(b, cands, None, lam=lam, max_iters=r68.MAX_ITERS)
        assert r["word"] == "ip", (f"a huge bottom-up gap must resist feedback (lam={lam}); "
                                    f"got {r['word']}")


def test_arm_a_reproduces_run61_baseline():
    """Arm A (one-directional over the FULL 300-word run-61 lattice, flat lexicon prior) must
    reproduce run 61's published lexicon_flat result EXACTLY: 234/300 = 78.0% word, 90.3% char."""
    if not (os.path.exists(r68.RUN61_LATTICES) and os.path.exists(r68.RUN61_LEXICON)):
        pytest.skip("run 61 checkpoints not present")
    lex = r68._load_json(r68.RUN61_LEXICON)
    lat = r68._load_json(r68.RUN61_LATTICES)
    assert not lat.get("partial")
    lex_by_len = r68.build_lex_by_len(lex["lexicon"])

    word_ok = 0
    char_ok = 0
    n_char = 0
    for Lw in lat["lattices"]:
        word = Lw["word"]
        b = r68.bottom_up_from_dists62(Lw["dists"])
        cands = lex_by_len.get(len(word), [])
        res = r68.ia_decode(b, cands, None, lam=0.0)
        word_ok += (res["word"] == word)
        m = min(len(res["word"]), len(word))
        char_ok += sum(1 for i in range(m) if res["word"][i] == word[i])
        n_char += len(word)

    n = len(lat["lattices"])
    assert n == 300
    assert word_ok == 234, f"expected 234/300 word-correct (run 61 lexicon_flat), got {word_ok}"
    assert abs(char_ok / n_char - 0.9030172413793104) < 1e-9


def test_seed_guard_md5_present():
    """The seed file this arc guards actually exists (sanity -- a missing file would make the
    autouse seed_guard fixture vacuously pass)."""
    assert os.path.exists(STROKE_SHAPES_SEED)
