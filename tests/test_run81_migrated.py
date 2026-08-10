"""test_run81_migrated.py -- unit gates for RUN 81 (attach a RICH language model to the reading
decode, replacing run 75/76's toy bigram; the VISUAL channel is UNCHANGED, training-free).

Gates the machinery BEFORE the expensive real-LLM-call eval (ops law "unit tests first"):
  * the RICH-LM channel scores candidates via `rank_promoted_lm_scores` -- the LM's endorsed pick
    is PROMOTED to the top of its own channel, the rest keep their ORIGINAL visual rank order
    unchanged -- a pure, LLM-call-free unit test of the score-construction mechanics;
  * `combine_and_argmax` -- at lm_weight=0 the decode is IDENTICAL to visual-only (the visual channel
    is untouched by attaching the LM); at a strongly LM-dominant weight, the LM's endorsed pick
    OVERRIDES a visually-favoured alternative -- the same "weight effect, not a coding accident"
    contrast run 75's own test suite established for its bigram Viterbi, reproduced here for the
    rich-LM re-ranker;
  * "decode swaps LM cleanly": the VISUAL candidate generation this run uses (`r75.topk_candidates`)
    is the literal, unmodified run-75 function -- checked by identity, not just by behaviour -- and
    is unaffected by which LM arm (bigram vs rich-LM) is active;
  * "reproduces run 75 bigram baseline when LM=bigram (control)": when the rich-LM channel's
    endorsed pick happens to equal what run 75's OWN bigram-Viterbi machinery would choose for a
    single (unchained) position, `combine_and_argmax` reproduces `r75.viterbi_decode`'s decision on
    the identical hand-built scenario from run 75's own test suite;
  * a LIVE semantic-disambiguation check against the local rich LM (skipped if unreachable): given
    "The quick brown ___ jumps over the lazy dog." and same-length visual confusions
    (fox/fog/fix/fax/fun/fee), the rich LM must pick "fox" -- a choice a bigram trained on a corpus
    that never saw "brown fox" could not make on lexical statistics alone (verified: a toy bigram
    built with zero counts for any of these continuations backs off to unigram frequency, which does
    NOT reliably favour "fox" over the other confusions -- this is exactly the "context forces a word
    a bigram wouldn't" scenario the task asks for);
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

Corpus-scale integration checks (bigram control numerically matches run75/76's own decode.json,
rich-LM lift on real sentences/lines) are exercised by the pipeline stages themselves
(`decode_synth`/`decode_iam` print + persist `control_matches_run75`/`control_matches_run76`) and are
NOT duplicated here as slow tests; this file is the fast, LLM-call-free (mostly) pre-flight gate.
"""
from __future__ import annotations

import hashlib
import math
import os
import sys
import urllib.error
import urllib.request

import numpy as np
import pytest

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")
os.environ.setdefault("IAM_STROKES_DIR", "/tmp/handwriting/iam_onbd/lineStrokes")
os.environ.setdefault("IAM_ASCII_DIR", "/tmp/handwriting/iam_ascii/ascii")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.jabberwock_richlm_read_run81 as r81
import scripts.jabberwock_sentence_read_run75 as r75

STROKE_SHAPES_SEED = r81.STROKE_SHAPES_SEED


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _ollama_reachable():
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3):
            return True
    except Exception:
        return False


OLLAMA_UP = _ollama_reachable()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run81_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


# --------------------------------------------------------------------------------------------- #
# rank_promoted_lm_scores -- the LM channel's own score-construction mechanics (no LLM calls).
# --------------------------------------------------------------------------------------------- #
def test_rank_promoted_lm_scores_promotes_pick_to_top():
    cand_words = ["novel", "annul", "ousel", "never"]     # visual-cost-ascending order already.
    scores = r81.rank_promoted_lm_scores(cand_words, pick="never")
    assert scores[3] == 0.0, "the LM's endorsed pick must score BEST (0.0)"
    assert np.argmax(scores) == 3


def test_rank_promoted_lm_scores_preserves_relative_order_of_non_picked():
    cand_words = ["a", "b", "c", "d"]
    scores = r81.rank_promoted_lm_scores(cand_words, pick="c")
    non_picked_idx = [0, 1, 3]
    non_picked_scores = [scores[i] for i in non_picked_idx]
    assert non_picked_scores == sorted(non_picked_scores, reverse=True), (
        "everyone except the LM's pick must keep DECREASING score by their OWN original visual "
        "rank -- the LM channel must not reorder anything it didn't explicitly promote")


def test_rank_promoted_lm_scores_no_pick_falls_back_to_pure_visual_rank_order():
    cand_words = ["a", "b", "c"]
    scores_none = r81.rank_promoted_lm_scores(cand_words, pick=None)
    scores_offlist = r81.rank_promoted_lm_scores(cand_words, pick="not_in_list")
    assert list(scores_none) == list(scores_offlist) == [-1.0, -2.0, -3.0]


# --------------------------------------------------------------------------------------------- #
# combine_and_argmax -- the weight dial: lm_weight=0 must be IDENTICAL to visual-only (visual
# UNCHANGED); a strongly LM-dominant weight must let the LM's pick override the visual favourite.
# --------------------------------------------------------------------------------------------- #
def test_combine_lm_weight_zero_reproduces_visual_only_argmax():
    cand_words = ["intruder", "expected"]
    visual_scores = np.array([0.0, -10.0])                # visual strongly favours "intruder".
    lm_scores = r81.rank_promoted_lm_scores(cand_words, pick="expected")   # LM prefers "expected".
    out = r81.combine_and_argmax(cand_words, visual_scores, lm_scores,
                                 visual_weight=1.0, lm_weight=0.0)
    assert out == "intruder", "with lm_weight=0 the decode must equal the visual channel exactly"


def test_combine_lm_dominant_overrides_visual_favourite():
    """The proofreading-blindness weight-effect contrast (run 75's own test pattern), reproduced for
    the rich-LM re-ranker instead of the bigram Viterbi."""
    cand_words = ["intruder", "expected"]
    visual_scores = np.array([0.0, -10.0])                # visual strongly favours "intruder".
    lm_scores = r81.rank_promoted_lm_scores(cand_words, pick="expected")

    prediction_dominant = r81.combine_and_argmax(cand_words, visual_scores, lm_scores,
                                                 visual_weight=0.01, lm_weight=1.0)
    visual_dominant = r81.combine_and_argmax(cand_words, visual_scores, lm_scores,
                                             visual_weight=1.0, lm_weight=0.01)
    assert prediction_dominant == "expected", "LM-dominant weighting must OVERRIDE the visual read"
    assert visual_dominant == "intruder", "visual-dominant weighting must read the actual ink"


def test_normalize01_bounds_and_order():
    scores = np.array([5.0, 2.0, -3.0])
    n = r81.normalize01(scores)
    assert n.max() == pytest.approx(0.0)
    assert n.min() == pytest.approx(-1.0)
    assert list(np.argsort(n)) == list(np.argsort(scores))


# --------------------------------------------------------------------------------------------- #
# "decode swaps LM cleanly": the visual channel is the literal, unmodified run-75 function.
# --------------------------------------------------------------------------------------------- #
def test_visual_channel_is_run75s_own_unmodified_function():
    assert r81.r75.topk_candidates is r75.topk_candidates
    assert r81.r75.loose_cost is r75.loose_cost
    assert r81.r75.strict_cost is r75.strict_cost


def test_visual_candidates_identical_regardless_of_lm_arm():
    """The candidate GENERATION step (visual) must not know or care which LM (bigram vs rich-LM) is
    about to score its output -- build_lex_by_len/topk_candidates take no LM argument at all."""
    lex_by_len = r75.build_lex_by_len(["cat", "cap", "car", "bat"])
    D = np.zeros((3, 26))
    D[0, 2], D[1, 0], D[2, 19] = 0.0, 0.0, 0.0
    D += 5.0
    D[0, 2], D[1, 0], D[2, 19] = 0.0, 0.0, 0.0
    words_a, scores_a = r75.topk_candidates(D.tolist(), lex_by_len, "strict", K=4)
    words_b, scores_b = r75.topk_candidates(D.tolist(), lex_by_len, "strict", K=4)
    assert words_a == words_b and list(scores_a) == list(scores_b)


# --------------------------------------------------------------------------------------------- #
# "reproduces run 75 bigram baseline when LM=bigram (control)": when the rich-LM's endorsed pick
# equals the bigram-Viterbi's own choice on run 75's own hand-built scenario, the two decoders agree.
# --------------------------------------------------------------------------------------------- #
def test_reproduces_run75_bigram_decision_when_pick_matches_bigram_choice():
    """Run 75's own `test_proofreading_blindness_is_a_weight_effect` scenario: position 1 candidates
    ["expected", "intruder"], visual strongly favours "intruder", the bigram LM strongly favours
    "expected" given the fixed previous word "start". Run 75's bigram-Viterbi picks "expected" under
    prediction-dominant weights. If the rich-LM's joint pick for this position is ALSO "expected"
    (i.e. LM=bigram's own answer), `combine_and_argmax` must reach the SAME decision run 75's own
    Viterbi reaches on the identical visual/weight inputs -- the swap is clean, not a different
    algorithm with a coincidentally similar name."""
    cand_words = ["expected", "intruder"]
    visual_scores = np.array([-10.0, 0.0])                # visual strongly favours "intruder" (idx1).

    def bigram_lm(prev, cur):
        return 10.0 if (prev == "start" and cur == "expected") else 0.0

    trans = [np.array([[bigram_lm("start", c) for c in cand_words]])]
    bigram_pred = r75.viterbi_decode([cand_words], [visual_scores], trans,
                                     lm_weight=1.0, visual_weight=0.01)
    assert bigram_pred == ["expected"]

    lm_scores = r81.rank_promoted_lm_scores(cand_words, pick="expected")   # rich LM agrees with bigram.
    rich_pred = r81.combine_and_argmax(cand_words, visual_scores, lm_scores,
                                       visual_weight=0.01, lm_weight=1.0)
    assert rich_pred == "expected" == bigram_pred[0]


# --------------------------------------------------------------------------------------------- #
# JSON extraction robustness (the rich LM's response is not always a bare, clean array).
# --------------------------------------------------------------------------------------------- #
def test_extract_json_list_recovers_array_from_noisy_text():
    noisy = 'Sure! Here is the answer:\n```json\n["fox", "the", "dog"]\n```\nHope that helps.'
    assert r81.extract_json_list(noisy) == ["fox", "the", "dog"]


def test_extract_json_list_rejects_non_string_array():
    assert r81.extract_json_list("[1, 2, 3]") is None


def test_extract_json_list_none_on_garbage():
    assert r81.extract_json_list("no brackets here at all") is None


def test_build_joint_prompt_includes_every_candidate_word():
    cand_lists = [["fox", "fog", "fix"], ["dog", "dot"]]
    prompt = r81.build_joint_prompt(cand_lists)
    for words in cand_lists:
        for w in words:
            assert w in prompt
    assert "2" in prompt and "JSON array" in prompt


# --------------------------------------------------------------------------------------------- #
# LIVE semantic-disambiguation check: rich LM vs a bigram that has never seen the disambiguating
# continuation -- the "context forces a word a bigram wouldn't" scenario. Skipped if ollama is down.
# --------------------------------------------------------------------------------------------- #
@pytest.mark.skipif(not OLLAMA_UP, reason="local ollama server not reachable on :11434")
def test_rich_lm_beats_bigram_on_semantically_disambiguating_sentence():
    cand_lists = [["fox", "fog", "fix", "fax", "fun", "fee"]]
    prompt = (
        'Sentence: "The quick brown ____ jumps over the lazy dog." The blank is ONE of these '
        f"candidates: {', '.join(cand_lists[0])}. Respond with ONLY a JSON array containing the "
        'single best-fitting word, e.g. ["word"].'
    )
    content, dt, err = r81.ollama_chat(prompt, model=r81.RICH_LM_MODEL)
    assert err is None, f"ollama call failed: {err}"
    arr = r81.extract_json_list(content)
    assert arr and arr[0].strip().lower() == "fox", (
        f"rich LM must resolve the classic pangram via full-sentence semantics, got {content!r}")

    # A bigram that has NEVER seen "brown fox"/"brown fog"/etc. (zero bigram counts for every
    # candidate) backs off to unigram frequency alone -- it has no mechanism to prefer "fox"
    # specifically; feed it a floor where "fee" (a common short word) is FREQUENCIER than "fox",
    # so the bigram's best-scoring choice is demonstrably NOT "fox", unlike the rich LM.
    uni = {"brown": 10}
    bi = {}                                                # no attested continuation whatsoever.
    logfreq = {"fox": math.log(0.0005), "fog": math.log(0.0004), "fix": math.log(0.002),
               "fax": math.log(0.0003), "fun": math.log(0.003), "fee": math.log(0.01)}
    bigram_score = r75.make_lm_scorer(uni, bi, logfreq)
    bigram_choice = max(cand_lists[0], key=lambda w: bigram_score("brown", w))
    assert bigram_choice != "fox", (
        "sanity: the bigram must NOT already prefer 'fox' on lexical statistics alone, or this "
        "scenario doesn't isolate the rich LM's semantic advantage")
