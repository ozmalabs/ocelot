"""RUN 82 unit gates -- the jabberwock READS handwriting with its OWN language faculty.

Exercises the real graph-native reading-prediction faculty (predict_context_term + the
semantic_reading_context seed Rules), confirms the handwriting visual candidates feed it cleanly,
reproduces run 75's bigram control arm, verifies the faculty is the jabberwock's OWN (no external LLM),
and asserts the stroke-shapes seed md5 is untouched.

Run:  OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=.:runners/dsl/python \\
        /home/matt/ozma/internal/research/.venv/bin/python3 -m pytest tests/test_run82_migrated.py -q
"""
import hashlib
import os
import sys

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.jabberwock_nativeread_run82 as r82
import scripts.jabberwock_sentence_read_run75 as r75


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def test_faculty_word_superiority_flip():
    """THE headline unit case: a visually-WRONG read is CORRECTED by can_follow priming -- run the real
    seed Rules (activate_recognised + prime_successors) and evaluate predict_context_term."""
    md5_before = _md5(r82.STROKE_SHAPES_SEED)
    res = r82._faculty_wordsuperiority_check()
    assert res["no_context_misreads_wA"], res
    assert res["context_corrects_to_wB"], res
    assert res["flip_ok"], res
    # the prime spread onto the successor (context_primed=1.0), not onto the visual best.
    assert res["primed_B_expected1"] == 1.0, res
    assert (res["primed_A_expected0"] in (0.0, None)), res
    # seed md5 untouched by loading + running the faculty.
    assert _md5(r82.STROKE_SHAPES_SEED) == md5_before


def test_can_follow_populated_donkey0():
    """The seed ships a SPARSE can_follow lexicon; we populate it donkey=0 from Brown (graph data)."""
    bigram, stats = r82.load_can_follow()
    assert stats["seed_prepopulated_can_follow_edges"] == 0
    assert stats["n_can_follow_edges"] > 10000, stats     # rich, real transition data.
    assert stats["n_distinct_heads"] > 1000, stats


def test_visual_candidates_feed_faculty_cleanly():
    """The run-75 handwriting VISUAL candidate distribution feeds the faculty scorer cleanly, and the
    scorer handles the sentence-start marker '^'."""
    prep = r75._load(os.path.join(r82.RUN75_CKPT, "prep.json"))
    rd = r75._load(os.path.join(r82.RUN75_CKPT, "read.json"))
    dists = {iid: rec["within_dists"] for iid, rec in rd["instances"].items()}
    lexicon = r75._load(r82.RUN61_LEXICON)
    lex_by_len = r75.build_lex_by_len(lexicon["lexicon"])
    bigram = prep["lm"]["bigram"]
    fac_bin = r82.make_faculty_binary(bigram)
    fac_wt = r82.make_faculty_weighted(bigram)
    s0 = prep["sentences"][0]
    rows = dists[s0["iids"][0]]
    words, vscores = r75.topk_candidates(rows, lex_by_len, "strict", r82.BEAM_K)
    assert len(words) > 0
    # scorer accepts '^' start + any candidate; returns a float; binary in {0,1}; weighted >= 0.
    for cur in words[:5]:
        b = fac_bin("^", cur)
        w = fac_wt("^", cur)
        assert b in (0.0, 1.0)
        assert w >= 0.0
        assert isinstance(b, float) and isinstance(w, float)


def test_bigram_control_reproduces_run75():
    """CONTROL arm: run 75's OWN bigram + decode, at the primary weight, must reproduce run 75's stored
    arm-B word accuracy exactly (the clean-LM-swap fact)."""
    prep = r75._load(os.path.join(r82.RUN75_CKPT, "prep.json"))
    rd = r75._load(os.path.join(r82.RUN75_CKPT, "read.json"))
    dists = {iid: rec["within_dists"] for iid, rec in rd["instances"].items()}
    lexicon = r75._load(r82.RUN61_LEXICON)
    lex_by_len = r75.build_lex_by_len(lexicon["lexicon"])
    bigram_score = r75.make_lm_scorer(prep["lm"]["unigram"], prep["lm"]["bigram"], lexicon["logfreq"])
    preds = r75.decode_all_sentence(prep["sentences"], dists, lex_by_len, "strict",
                                    bigram_score, r82.PRIMARY_VISUAL_WEIGHT)
    rep = r75._acc_report(preds)
    run75 = r75._load(os.path.join(r82.RUN75_CKPT, "decode.json"))
    assert abs(rep["word_acc"] - run75["reps"]["B"]["word_acc"]) < 1e-9, (
        rep["word_acc"], run75["reps"]["B"]["word_acc"])


def test_faculty_is_the_jabberwocks_own_no_external_llm():
    """donkey=0: the run 82 script uses NO external LLM / n-gram service -- only the jabberwock's own
    can_follow faculty + the same Brown corpus the bigram control uses."""
    src = open(r82.__file__).read().lower()
    for banned in ("ollama", "openai", "anthropic", "http://localhost", "urllib.request", "api/chat",
                   "kenlm"):
        assert banned not in src, f"run 82 must not touch an external LM: found {banned!r}"
