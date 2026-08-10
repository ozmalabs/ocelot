"""RUN 83 unit gates — wire the handwriting visual (run 75/76) into the DEEP AbS
PREDICTIVE READER (domains/predictive_reading.py) and prove the wiring, on a bare
substrate, donkey=0. These are the pre-registered unit checks the ops law requires
BEFORE the corpus stages:

  * predict_next_words FIRES on a Brown (non-narrative) sentence context, and we
    report WHICH sources fire (context / recurring_beat / register / production /
    class_prior). The RICH claim: it predicts from the WHOLE accumulated context +
    register, not order-1.
  * prediction_guided_segment DISAMBIGUATES a noisy handwriting-style token where
    the PREDICTION flips an ambiguous char to the context-correct word (the
    payoff-b unit case, on OUR signal form) — and bottom-up alone cannot.
  * the handwriting VISUAL lattice (run 75's topk_candidates over per-char distance
    rows) feeds the predicted-set membership prior CLEANLY (re-rank picks the
    predicted word when visual is ambiguous).
  * a bottom-up (visual-alone) baseline arm exists and is the pw=0 control.
  * NO external LLM is imported.
  * seed-guard: seeds/stroke_shapes.json md5 UNCHANGED across the test.
"""
import hashlib
import os
import sys

import numpy as np

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs                       # noqa: E402
from domains import predictive_reading as pr     # noqa: E402
import scripts.jabberwock_sentence_read_run75 as r75   # noqa: E402

STROKE_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")


def _md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _fresh():
    s = srs.Substrate()
    s.add_node("Agent", {})
    return s


def test_predict_next_words_fires_on_brown_and_is_rich():
    """It predicts from the WHOLE prior context + register, not just prev word."""
    s = _fresh()
    seen = ["the state government said the new tax would help schools .",
            "the new report said the state would raise the tax again ."]
    model = pr.build_writer_model(s, seen)
    pred = pr.predict_next_words(
        s, model["writer_style"],
        context="the committee reviewed the new tax report",
        seen_vocab=["the", "state", "government", "tax", "report", "new"])
    srcs = set(pred["provenance"].values())
    # RICH: context content words from the WHOLE context are predicted (not order-1).
    assert "report" in pred["predicted_words"]           # a context word 4 tokens back
    assert "committee" in pred["predicted_words"]
    assert "context" in srcs
    assert "register" in srcs
    # recurring beat harvested across the two seen sentences ("the ... tax", "state").
    assert "recurring_beat" in srcs
    # non-narrative => production (throughline beat) does NOT fire.
    assert pred["production"] is None


def test_payoff_b_prediction_flips_ambiguous_token_on_our_signal():
    """prediction_guided_segment recovers a char-substituted / run-together token
    that bottom-up leaves OOV — the headline payoff-b, on OUR noisy-signal form."""
    s = _fresh()
    # base lexicon (closed-class) does NOT contain 'river'; the reader has PREDICTED
    # it from context. The noisy token 'r1ver' is a char-substitution of 'river'.
    predicted = ["river", "bird", "flew"]
    truth = ["river"]
    bottom = pr.bottom_up_segment(s, "r1ver")
    guided = pr.prediction_guided_segment(s, predicted, "r1ver")
    acc_b = pr.segmentation_accuracy(bottom, truth)
    acc_g = pr.segmentation_accuracy(guided, truth)
    assert acc_g == 1.0                      # prediction confirms the noisy chars
    assert acc_b < 1.0                       # bottom-up cannot: no codebook word
    # missing-space case, same prediction.
    guided2 = pr.prediction_guided_segment(s, ["the", "bird", "river"],
                                           "thebirdriver")
    assert guided2 == ["the", "bird", "river"]


def test_visual_lattice_feeds_predicted_prior_cleanly():
    """The run-75 visual lattice (topk over per-char distance rows) re-ranked by the
    predicted-set membership prior picks the predicted word when visual is a tie."""
    # two length-4 lexicon words; the distance rows are AMBIGUOUS between them.
    lex_by_len = r75.build_lex_by_len(["that", "than", "then", "them", "this"])
    # rows: L=4, 26 cols. Make 'that' and 'than' near-tied (differ only pos 3 t/n).
    rows = np.full((4, 26), 5.0)
    for l, ch in enumerate("that"):
        rows[l, ord(ch) - 97] = 0.0
    # make pos-3 't' vs 'n' a near tie so visual alone is ambiguous.
    rows[3, ord("n") - 97] = 0.05
    cand_words, vscores = r75.topk_candidates(list(rows.tolist()), lex_by_len,
                                              "strict", K=10)
    assert "that" in cand_words and "than" in cand_words
    vs = np.asarray(vscores, dtype=float)
    vs = (vs - vs.mean()) / (vs.std() + 1e-9)
    # PREDICTION says 'than' (context prior). Re-rank: visual + pw*membership.
    predicted = {"than"}
    pw = 2.0
    combined = [vs[i] + pw * (1.0 if w in predicted else 0.0)
                for i, w in enumerate(cand_words)]
    pick_guided = cand_words[int(np.argmax(combined))]
    pick_bottom = cand_words[int(np.argmax(vs))]           # pw=0 control
    assert pick_bottom == "that"          # visual-alone prefers the (marginally) closer
    assert pick_guided == "than"          # prediction flips it to the predicted word


def test_no_external_llm_imported():
    import domains.predictive_reading as m
    src = open(m.__file__).read()
    for bad in ("import openai", "ollama", "gemma", "langchain", "anthropic",
                "genai", "requests.post"):
        assert bad not in src


def test_seed_guard_unchanged():
    before = _md5(STROKE_SEED)
    s = _fresh()
    model = pr.build_writer_model(s, ["the cat sat on the mat .",
                                      "the cat ran to the mat ."])
    pr.predict_next_words(s, model["writer_style"], context="the cat", seen_vocab=[])
    pr.abs_compare(s, ["the", "cat", "mat"], ["the", "cat", "sat"])
    assert _md5(STROKE_SEED) == before
