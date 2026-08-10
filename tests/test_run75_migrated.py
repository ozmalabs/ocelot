"""test_run75_migrated.py -- unit gates for RUN 75 (prediction-dominant sentence reading: word
n-gram LM x loose/strict visual, Viterbi over the sentence, the jumbled/misspell/proofreading
controls).

Gates the machinery BEFORE the expensive real-data eval (ops law "unit tests first"):
  * the LOOSE (open-bigram/bag) visual cost is INVARIANT to a transposition of the interior
    per-char distance rows -- the exact property the JUMBLED control measures -- while the STRICT
    visual cost is NOT (a contrast, not just a one-sided assertion);
  * the bigram-LM scorer (with stupid-backoff to the run-61 unigram floor) prefers an attested
    context-consistent continuation over an unseen/rare one;
  * Viterbi decode over a small synthetic sentence recovers the expected word sequence, and the
    SAME machinery reproduces "proofreading blindness": a strongly-predicted word overrides a
    visually-favoured alternative when the LM is weighted heavily, and vice versa when the visual
    weight dominates -- demonstrating the phenomenon is a WEIGHT effect, not a coding accident;
  * `decode_isolated` (arm A's mechanism) picks the correct lexicon word on a hand-built example --
    the same "no sentence context, full-lexicon collapse" mechanism run 70 established at 30.5%;
    a real-data pin test (skipped if run 70's checkpoint is absent) confirms that number is still
    what this run cites as "the baseline to beat";
  * jumble/misspell eligibility thresholds (word length >= 4 / >= 3) behave as documented;
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

Native (substrate_rs) / real-corpus tests are skipped if the DeepWriting corpus or run 61/69
checkpoints are not present; pure-python tests (the bulk of this file) need neither.
"""
from __future__ import annotations

import hashlib
import math
import os
import sys

import numpy as np
import pytest

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.jabberwock_sentence_read_run75 as r75

STROKE_SHAPES_SEED = r75.STROKE_SHAPES_SEED
TRAIN_NPZ_PRESENT = os.path.exists(r75.dww.TRAIN_NPZ)
RUN69_PREP_PRESENT = os.path.exists(r75.RUN69_PREP)
RUN61_LEXICON_PRESENT = os.path.exists(r75.RUN61_LEXICON)
RUN70_SUMMARY_PRESENT = os.path.exists(r75.RUN70_SUMMARY)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run75_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


# --------------------------------------------------------------------------------------------- #
# THE central invariance: loose (open-bigram/bag) visual cost is transposition-robust; strict is
# not. This IS the jumbled-interior claim, tested directly on the cost function.
# --------------------------------------------------------------------------------------------- #
def _fake_D(letters_per_pos: list, noise=None) -> np.ndarray:
    """Build a (L,26) distance matrix where position i's row favors `letters_per_pos[i]` (a
    lowercase letter, cost 0.0) with all other classes at a higher cost."""
    rng = np.random.default_rng(0) if noise is None else noise
    L = len(letters_per_pos)
    D = 5.0 + rng.uniform(0, 0.1, size=(L, 26))
    for i, ch in enumerate(letters_per_pos):
        D[i, ord(ch) - 97] = 0.0
    return D


def test_loose_cost_invariant_to_interior_transposition():
    """A candidate word's LOOSE cost is IDENTICAL whether the query's interior distance rows are
    in their original order or with two interior rows swapped -- the exact invariance the JUMBLED
    control needs. STRICT cost, in contrast, is NOT invariant (the two channels genuinely differ)."""
    word = "chart"                                    # length 5: interior = positions 1,2,3.
    D = _fake_D(list(word))
    cls_arr = np.array([[ord(c) - 97 for c in word]], dtype=np.int64)

    loose_before = r75.loose_cost(D, cls_arr)[0]
    strict_before = r75.strict_cost(D, cls_arr)[0]

    D_swapped = D.copy()
    D_swapped[[1, 2]] = D_swapped[[2, 1]]              # transpose two INTERIOR rows.
    loose_after = r75.loose_cost(D_swapped, cls_arr)[0]
    strict_after = r75.strict_cost(D_swapped, cls_arr)[0]

    assert loose_before == pytest.approx(loose_after), "loose cost must be transposition-invariant"
    assert not np.isclose(strict_before, strict_after), (
        "strict cost SHOULD change under an interior transposition (the contrast case) -- if it "
        "doesn't, the fake D fixture isn't discriminative")


def test_loose_cost_anchors_first_and_last_strictly():
    """Corrupting the FIRST letter's row (not an interior letter) DOES change the loose cost --
    only the interior is position-robust, first/last stay anchored."""
    word = "chart"
    D = _fake_D(list(word))
    cls_arr = np.array([[ord(c) - 97 for c in word]], dtype=np.int64)
    base = r75.loose_cost(D, cls_arr)[0]
    D2 = D.copy()
    D2[0, :] = 5.0
    D2[0, ord("z") - 97] = 0.0                         # first letter now looks like 'z'.
    after = r75.loose_cost(D2, cls_arr)[0]
    assert after > base, "corrupting the anchored first letter must worsen the loose cost"


def test_jumble_interior_eligibility():
    rows3 = [[0.0] * 26 for _ in range(3)]             # length 3: only 1 interior letter.
    out3, elig3 = r75.jumble_interior(rows3)
    assert not elig3
    rows4 = [[float(i)] * 26 for i in range(4)]        # length 4: 2 interior letters -> eligible.
    out4, elig4 = r75.jumble_interior(rows4)
    assert elig4
    assert out4[1] == rows4[2] and out4[2] == rows4[1]
    assert out4[0] == rows4[0] and out4[3] == rows4[3], "first/last must be untouched by jumbling"


def test_misspell_interior_eligibility_and_corruption():
    rows2 = [[0.0] * 26 for _ in range(2)]
    _, elig2 = r75.misspell_interior(rows2, [0, 1])
    assert not elig2, "length < 3 has no interior letter to misspell"
    rows4 = [[5.0] * 26 for _ in range(4)]
    true_classes = [0, 2, 4, 6]                        # letters a, c, e, g.
    out, elig = r75.misspell_interior(rows4, true_classes)
    assert elig
    corrupted_row = out[1]
    wrong_c = (true_classes[1] + 13) % 26
    assert corrupted_row[wrong_c] == 0.0
    assert corrupted_row[true_classes[1]] != 0.0, "the true letter must NOT be the cheapest option"
    assert out[0] == rows4[0] and out[2] == rows4[2] and out[3] == rows4[3]


# --------------------------------------------------------------------------------------------- #
# The bigram LM (stupid backoff to the run-61 unigram floor).
# --------------------------------------------------------------------------------------------- #
def test_lm_scorer_prefers_attested_bigram_over_backoff():
    uni = {"the": 100, "^": 50}
    bi = {"the|dog": 40, "the|xyzzy": 0}
    logfreq = {"dog": math.log(0.01), "xyzzy": math.log(1e-9), "cat": math.log(0.005)}
    score = r75.make_lm_scorer(uni, bi, logfreq)
    s_dog = score("the", "dog")            # attested bigram, high count.
    s_cat = score("the", "cat")            # unseen bigram -> backoff to unigram floor.
    assert s_dog > s_cat, "an attested, frequent bigram must outscore an unseen backoff candidate"


def test_lm_scorer_backoff_uses_logfreq_floor_ordering():
    uni = {"a": 10}
    bi = {}                                # nothing attested -- pure backoff for both.
    logfreq = {"common": math.log(0.05), "rare": math.log(1e-8)}
    score = r75.make_lm_scorer(uni, bi, logfreq)
    assert score("a", "common") > score("a", "rare")


# --------------------------------------------------------------------------------------------- #
# Viterbi decode + THE PROOFREADING-BLINDNESS phenomenon as a weight effect.
# --------------------------------------------------------------------------------------------- #
def test_viterbi_decode_simple_sequence():
    """Two positions, unambiguous visual + LM agreeing -- Viterbi must recover both words."""
    cand_words = [["cat", "dog"], ["ran", "sat"]]
    visual_scores = [np.array([5.0, 0.0]), np.array([5.0, 0.0])]   # both favor index 1.

    def lm(prev, cur):
        return 1.0 if (prev, cur) in {("^", "dog"), ("dog", "sat")} else -5.0

    trans = [np.array([[lm("^", c) for c in cand_words[0]]]),
             np.array([[lm(p, c) for c in cand_words[1]] for p in cand_words[0]])]
    out = r75.viterbi_decode(cand_words, visual_scores, trans, lm_weight=1.0, visual_weight=1.0)
    assert out == ["dog", "sat"]


def test_proofreading_blindness_is_a_weight_effect():
    """Position 0 is fixed ('start'). Position 1's LM strongly favors 'expected' given 'start';
    the VISUAL strongly favors a DIFFERENT word 'intruder' (simulating a donor-ink substitution).
    A strongly PREDICTION-dominant weighting must OVERRIDE the visual (read 'expected'); a
    strongly VISUAL-dominant weighting must read the actual ink ('intruder') instead -- the
    override is a property of the WEIGHT, not an artifact of the decode machinery."""
    cand_words = [["start"], ["expected", "intruder"]]
    visual_scores = [np.array([0.0]), np.array([-10.0, 0.0])]      # visual strongly favors intruder.

    def lm(prev, cur):
        if prev == "start" and cur == "expected":
            return 10.0                                            # LM strongly predicts 'expected'.
        return 0.0

    trans = [np.array([[0.0]]),
             np.array([[lm("start", c) for c in cand_words[1]]])]

    prediction_dominant = r75.viterbi_decode(cand_words, visual_scores, trans,
                                             lm_weight=1.0, visual_weight=0.01)
    visual_dominant = r75.viterbi_decode(cand_words, visual_scores, trans,
                                         lm_weight=0.01, visual_weight=1.0)
    assert prediction_dominant[1] == "expected", "prediction-dominant weighting must OVERRIDE the ink"
    assert visual_dominant[1] == "intruder", "visual-dominant weighting must read the actual ink"


# --------------------------------------------------------------------------------------------- #
# decode_isolated (arm A's mechanism) + the run-70 baseline citation.
# --------------------------------------------------------------------------------------------- #
def test_decode_isolated_picks_correct_lexicon_word():
    lex_by_len = r75.build_lex_by_len(["cat", "car", "cap", "dog"])
    word = "cat"
    D = _fake_D(list(word))
    rows = D.tolist()
    pred = r75.decode_isolated(rows, lex_by_len, "strict")
    assert pred == "cat"


def test_decode_isolated_loose_also_recovers_clean_signal():
    lex_by_len = r75.build_lex_by_len(["chart", "charm", "chard"])
    word = "chart"
    D = _fake_D(list(word))
    pred = r75.decode_isolated(D.tolist(), lex_by_len, "loose")
    assert pred == "chart"


@pytest.mark.skipif(not RUN70_SUMMARY_PRESENT, reason="run 70 checkpoint not present")
def test_run70_baseline_is_still_30_5_percent():
    """Pin test: run 70's own within-writer isolated-word lexicon accuracy (the number this run
    calls 'the baseline to beat') is still what the docstring/constants cite."""
    import json
    summary = json.load(open(r75.RUN70_SUMMARY))
    within_b = summary["reps"]["within|b"]
    pct = 100 * within_b["word_acc"]
    assert abs(pct - r75.RUN70_ISOLATED_WORD) < 1.0, (
        f"run 70's within-writer lexicon word acc drifted: {pct:.1f}% vs cited "
        f"{r75.RUN70_ISOLATED_WORD}%")


# --------------------------------------------------------------------------------------------- #
# build_lex_by_len / topk_candidates plumbing.
# --------------------------------------------------------------------------------------------- #
def test_build_lex_by_len_groups_by_length_and_filters_range():
    lex_by_len = r75.build_lex_by_len(["cat", "cats", "ab", "toolongwordxyz"])
    assert 3 in lex_by_len and "cat" in lex_by_len[3][0]
    assert 4 in lex_by_len and "cats" in lex_by_len[4][0]
    assert 2 not in lex_by_len, "below WORD_MIN_LEN must be excluded"
    assert all(len(w) <= r75.WORD_MAX_LEN for L, (ws, _) in lex_by_len.items() for w in ws)


def test_topk_candidates_orders_by_cost_ascending():
    lex_by_len = r75.build_lex_by_len(["cat", "cap", "car", "bat"])
    D = _fake_D(list("cat"))
    words, scores = r75.topk_candidates(D.tolist(), lex_by_len, "strict", K=4)
    assert words[0] == "cat"
    assert list(scores) == sorted(scores, reverse=True), "scores (-cost) must be descending"


def test_topk_with_forced_guarantees_membership_outside_topk():
    """The whole point of `topk_with_forced`: a word that would NOT survive top-K visual pruning
    (because the query ink looks nothing like it) must still be present in the returned candidate
    list -- otherwise the proofreading-blindness test would confound 'prediction never overrides
    visual' with 'the candidate pool already discarded the prediction'."""
    words_pool = ["cat"] + [f"c{chr(97+i)}t" for i in range(24)]   # 25 length-3 lexicon entries.
    lex_by_len = r75.build_lex_by_len(words_pool)
    D = _fake_D(list("bin"))                          # ink looks like 'bin', nothing like the pool.
    words_plain, _ = r75.topk_candidates(D.tolist(), lex_by_len, "strict", K=3)
    assert "cat" not in words_plain, "sanity: 'cat' should NOT survive top-3 pruning against 'bin' ink"
    words_forced, scores_forced = r75.topk_with_forced(D.tolist(), lex_by_len, "strict", 3, ["cat"])
    assert "cat" in words_forced
    assert len(scores_forced) == len(words_forced)


# --------------------------------------------------------------------------------------------- #
# Real-data integration (skipped if the corpus / run 61/69 checkpoints aren't present).
# --------------------------------------------------------------------------------------------- #
requires_real = pytest.mark.skipif(
    not (TRAIN_NPZ_PRESENT and RUN69_PREP_PRESENT and RUN61_LEXICON_PRESENT),
    reason="DeepWriting corpus or run 61/69 checkpoints not present")


@pytest.fixture(scope="module")
def small_prep():
    if not (TRAIN_NPZ_PRESENT and RUN69_PREP_PRESENT and RUN61_LEXICON_PRESENT):
        pytest.skip("DeepWriting corpus or run 61/69 checkpoints not present")
    dw = r75.dww.load_deepwriting(r75.SPLIT)
    glyphs = r75.dww.extract_char_glyphs(dw)
    return r75.build_prep(target_n=15, dw=dw, all_glyphs=glyphs)


@requires_real
def test_prep_reuses_run69_bg_writers(small_prep):
    assert small_prep["bg_writers_match_run69"]
    assert set(small_prep["bg_writers"]).isdisjoint(set(small_prep["ho_writers"]))


@requires_real
def test_prep_sentences_nonempty_and_within_length_window(small_prep):
    assert small_prep["n_sentences"] > 0
    for s in small_prep["sentences"]:
        assert r75.SENTENCE_MIN_WORDS <= len(s["words"]) <= r75.SENTENCE_MAX_WORDS
        assert len(s["iids"]) == len(s["words"])


@requires_real
def test_prep_test_writers_subset_of_held_out(small_prep):
    ho = set(small_prep["ho_writers"])
    bg = set(small_prep["bg_writers"])
    tw = set(small_prep["test_writers"])
    assert tw.issubset(ho)
    assert tw.isdisjoint(bg)


@requires_real
def test_prep_lm_has_nonzero_bigram_mass(small_prep):
    assert len(small_prep["lm"]["bigram"]) > 0
    assert len(small_prep["lm"]["unigram"]) > 0
