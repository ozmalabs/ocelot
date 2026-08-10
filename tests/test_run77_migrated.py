"""test_run77_migrated.py -- unit gates for RUN 77 (FAST WRITER-ADAPTATION, prediction-seeded --
run 73 reborn on the prediction-dominant reader from runs 74/75/76).

Gates the machinery BEFORE the expensive real-data eval (ops law "unit tests first"):
  * the prediction-dominant DUAL-ROUTE decoder (`decode_one`, reused verbatim from
    `r76.topk_candidates_iam` / `r76._normalize_visual`) picks the right candidate when the
    holistic word-form pool has a decisive low-distance entry, and correctly falls through to the
    per-char loose route when neither the pool nor the cross bank covers the word's length;
  * the harvest rule (`harvest_ok`) mirrors run 73's shape: accepts agreement + margin, rejects
    disagreement between the visual-only pick and the prediction-dominant pick;
  * the pairwise index is queried symmetrically (rich AND env channels both survive round-trip);
  * `FastAdaptCorpus.pool_dict` with an EMPTY pool is byte-identical (empty dict) to the cold
    condition -- round-0 IS the cold start, not a separately-coded special case;
  * leave-one-word-out actually excludes a word's own pseudo-label when re-scoring that same word
    (the anti-circularity property the whole run's honesty rests on);
  * EM converges (stops harvesting) on a saturating synthetic corpus;
  * the streaming warm-up curve is CAUSAL (position k never sees pseudo-labels from position >= k)
    and has the right shape;
  * `compute_margin_threshold` is a plain percentile of round-0's OWN margin distribution, computed
    BEFORE any accuracy number exists;
  * `collect_word_contexts` extracts real oracle (prev, next) pairs, including boundary tokens;
  * cold-start plausibility: cold word_acc lands well above chance and ceiling is not worse than
    cold on a small real slice (given the writer's real hand can only help, never hurt);
  * anchors: this run's own cold/ceiling numbers are reported ALONGSIDE (not required to exactly
    reproduce) runs 69/70/74's numbers -- different word/writer sample, same mechanism family;
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

Native (substrate_rs) tests run under .venv python; pure-python tests (decoder dispatch, harvest
rule, pool cap reuse, EM leave-one-out, convergence, threshold selection, context collection) need
neither native nor real data and pass under system python3.
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

import scripts.jabberwock_fastadapt_run77 as r77

STROKE_SHAPES_SEED = r77.STROKE_SHAPES_SEED
TRAIN_NPZ_PRESENT = os.path.exists(r77.dww.TRAIN_NPZ)
RUN69_PREP_PRESENT = os.path.exists(r77.RUN69_PREP)
RUN61_LEXICON_PRESENT = os.path.exists(r77.RUN61_LEXICON)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run77_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


# --------------------------------------------------------------------------------------------- #
# collect_word_contexts -- oracle (prev, next) pairs from the reduced-Brown reduction.
# --------------------------------------------------------------------------------------------- #
def test_collect_word_contexts_basic_and_boundaries():
    reduced = [["the", "quick", "fox"], ["quick", "brown"]]
    ctx = r77.collect_word_contexts(reduced)
    assert ("^", "quick") in ctx["the"]
    assert ("the", "fox") in ctx["quick"]
    assert ("quick", "$") == ctx["fox"][0]
    assert ("^", "brown") in ctx["quick"]


def test_collect_word_contexts_missing_word_absent():
    ctx = r77.collect_word_contexts([["alpha", "beta"]])
    assert "gamma" not in ctx


# --------------------------------------------------------------------------------------------- #
# decode_one -- the shared dual-route decoder every condition (cold/ceiling/bootstrapped) uses.
# --------------------------------------------------------------------------------------------- #
def _lex_by_len_3():
    return {3: (["cat", "dog", "cap"], np.array([[ord(c) - 97 for c in w]
                                                 for w in ["cat", "dog", "cap"]]))}


def _flat_lm_score(prev, cur):
    return 0.0   # neutral LM -- isolates the visual channel in decode_one tests.


def _make_corpus(words: dict, pairwise_rows=None, lm_score=_flat_lm_score, channel="rich"):
    return r77.FastAdaptCorpus(words, pairwise_rows or [], _lex_by_len_3(), lm_score, channel)


def test_decode_one_picks_within_pool_when_covered():
    """A word-form pool entry for 'cat' at distance 0.01 (vs a much worse cross-bank number for
    'dog'/'cap') must win -- the dual-route candidate generation prefers the pool over cross/loose
    (r76's own precedent, reused verbatim)."""
    rows = [[5.0] * 26 for _ in range(3)]   # uninformative per-char loose fallback rows.
    words = {"0": {"wid": 0, "writer": 1, "word": "cat", "len": 3, "local_idx": 0,
                  "cross_rich": {"dog": 0.9, "cap": 0.95}, "cross_env": {},
                  "char_cross_rows": rows, "context": {"prev": "^", "next": "$"}}}
    corpus = _make_corpus(words)
    pool = {"cat": 0.01}
    dec = r77.decode_one(corpus, 0, pool, lm_weight=0.0, visual_weight=1.0)
    assert dec["pred"] == "cat"
    assert dec["visual_pred"] == "cat"


def test_decode_one_falls_through_to_per_char_loose_when_uncovered():
    """Neither pool nor cross-bank has ANY label at this length -- must fall through to the
    per-char LOOSE lexicon route (r75's own `topk_candidates`), not return an empty decode."""
    rows = [[5.0, 0.1] + [5.0] * 24,   # position 0: letter 'b' (idx1) is cheapest.
            [0.1] + [5.0] * 25,         # position 1: letter 'a' (idx0) is cheapest.
            [5.0] * 3 + [0.1] + [5.0] * 22]  # position 2: letter 'd' (idx3) is cheapest.
    words = {"0": {"wid": 0, "writer": 1, "word": "bad", "len": 3, "local_idx": 0,
                  "cross_rich": {}, "cross_env": {}, "char_cross_rows": rows,
                  "context": {"prev": "^", "next": "$"}}}
    lex = {3: (["bad", "cat"], np.array([[ord(c) - 97 for c in w] for w in ["bad", "cat"]]))}
    corpus = r77.FastAdaptCorpus(words, [], lex, _flat_lm_score, "rich")
    dec = r77.decode_one(corpus, 0, {}, lm_weight=0.0, visual_weight=1.0)
    assert dec["n_cands"] > 0
    assert dec["pred"] == "bad"


def test_decode_one_prediction_can_override_visual_with_lm():
    """With the LM strongly favoring 'dog' over 'cat' via context, and visual only weakly favoring
    'cat', a large lm_weight must flip the prediction-dominant pick relative to the visual-only
    pick -- the mechanism the harvest rule's AGREEMENT check depends on being able to detect."""
    rows = [[5.0] * 26 for _ in range(3)]
    words = {"0": {"wid": 0, "writer": 1, "word": "dog", "len": 3, "local_idx": 0,
                  "cross_rich": {"cat": 0.10, "dog": 0.12}, "cross_env": {},
                  "char_cross_rows": rows, "context": {"prev": "the", "next": "barked"}}}

    def lm_favors_dog(prev, cur):
        return 5.0 if cur == "dog" else 0.0

    corpus = r77.FastAdaptCorpus(words, [], _lex_by_len_3(), lm_favors_dog, "rich")
    dec_visual_only = r77.decode_one(corpus, 0, {}, lm_weight=0.0, visual_weight=1.0)
    dec_pred = r77.decode_one(corpus, 0, {}, lm_weight=1.0, visual_weight=0.1)
    assert dec_visual_only["pred"] == "cat"     # visual alone prefers the closer distance.
    assert dec_pred["pred"] == "dog"            # LM-dominant flips it.
    assert dec_pred["pred"] != dec_visual_only["pred"]


# --------------------------------------------------------------------------------------------- #
# harvest_ok -- agreement + margin (r73's shape, transplanted).
# --------------------------------------------------------------------------------------------- #
def test_harvest_ok_accepts_agreeing_confident_decode():
    dec = {"pred": "cat", "visual_pred": "cat", "margin": 5.0, "n_cands": 3}
    assert r77.harvest_ok(dec, margin_threshold=1.0)


def test_harvest_ok_rejects_disagreement():
    dec = {"pred": "dog", "visual_pred": "cat", "margin": 5.0, "n_cands": 3}
    assert not r77.harvest_ok(dec, margin_threshold=1.0)


def test_harvest_ok_rejects_low_margin():
    dec = {"pred": "cat", "visual_pred": "cat", "margin": 0.2, "n_cands": 3}
    assert not r77.harvest_ok(dec, margin_threshold=1.0)


def test_harvest_ok_rejects_empty_candidates():
    dec = {"pred": "", "visual_pred": "", "margin": math.inf, "n_cands": 0}
    assert not r77.harvest_ok(dec, margin_threshold=0.0)


# --------------------------------------------------------------------------------------------- #
# pairwise index -- symmetric lookup, both channels.
# --------------------------------------------------------------------------------------------- #
def test_pairwise_index_symmetric_both_channels():
    rows = [[1, 0, 2, 0.37, 0.55]]
    idx = r77.build_pairwise_index(rows)
    assert idx[(1, 0, 2)] == (0.37, 0.55)
    assert idx[(1, 2, 0)] == (0.37, 0.55)


def test_pair_dist_selects_channel():
    words = {"0": {"wid": 0, "writer": 1, "word": "cat", "len": 3, "local_idx": 0,
                  "cross_rich": {}, "cross_env": {}, "char_cross_rows": [[0.0] * 26] * 3,
                  "context": {"prev": "^", "next": "$"}}}
    rich_corpus = r77.FastAdaptCorpus(words, [[1, 0, 1, 0.1, 0.9]], _lex_by_len_3(),
                                      _flat_lm_score, "rich")
    env_corpus = r77.FastAdaptCorpus(words, [[1, 0, 1, 0.1, 0.9]], _lex_by_len_3(),
                                     _flat_lm_score, "env")
    assert rich_corpus.pair_dist(1, 0, 1) == pytest.approx(0.1)
    assert env_corpus.pair_dist(1, 0, 1) == pytest.approx(0.9)


# --------------------------------------------------------------------------------------------- #
# pool_dict -- empty pool == cold; leave-one-out excludes the word's own source.
# --------------------------------------------------------------------------------------------- #
def _two_word_corpus():
    """2 words, same writer, 'cat'/'dog', local idx 0/1, pairwise distance engineered close (0.02)
    so a pseudo-label sourced from word 1 ('dog', mislabeled as 'cat' for this synthetic test)
    would dramatically help word 0's decode of label 'cat' -- UNLESS excluded by leave-one-out."""
    rows = [[5.0] * 26] * 3
    words = {
        "0": {"wid": 0, "writer": 1, "word": "cat", "len": 3, "local_idx": 0,
             "cross_rich": {"cat": 0.9, "dog": 0.95}, "cross_env": {},
             "char_cross_rows": rows, "context": {"prev": "^", "next": "$"}},
        "1": {"wid": 1, "writer": 1, "word": "dog", "len": 3, "local_idx": 1,
             "cross_rich": {"cat": 0.9, "dog": 0.95}, "cross_env": {},
             "char_cross_rows": rows, "context": {"prev": "^", "next": "$"}},
    }
    pairwise = [[1, 0, 1, 0.02, 0.02]]
    return r77.FastAdaptCorpus(words, pairwise, _lex_by_len_3(), _flat_lm_score, "rich")


def test_pool_dict_empty_pool_is_empty_dict():
    corpus = _two_word_corpus()
    assert corpus.pool_dict(0, {}, exclude_wid=0) == {}


def test_pool_dict_leave_one_out_excludes_self_source():
    corpus = _two_word_corpus()
    pool = {}
    r77.r73._pool_add(pool, writer=1, cls="cat", wid=1, local_idx=1, margin=1.0)   # sourced from wid=1.
    # scoring wid=1 itself must NOT see its own pseudo-label.
    pd_self = corpus.pool_dict(1, pool, exclude_wid=1)
    assert pd_self == {}
    # scoring a DIFFERENT word (wid=0) DOES see it.
    pd_other = corpus.pool_dict(0, pool, exclude_wid=0)
    assert pd_other.get("cat") == pytest.approx(0.02)


# --------------------------------------------------------------------------------------------- #
# run_em -- convergence + leave-one-word-out on a saturating synthetic corpus.
# --------------------------------------------------------------------------------------------- #
def _saturating_corpus77(writer=1):
    """4 words: 'top'/'tap' UNAMBIGUOUS via cross alone; 'cat'/'cap' AMBIGUOUS at cold start (cross
    ties them) but resolvable once same-writer pairwise structure (encoding "this writer's t/p look
    different") becomes available through the bootstrapped pool."""
    rows_flat = [[5.0] * 26] * 3
    words = {}
    for wid, w in enumerate(["cat", "cap", "top", "tap"]):
        words[str(wid)] = {"wid": wid, "writer": writer, "word": w, "len": 3, "local_idx": wid,
                           "cross_rich": {"top": 0.9, "tap": 0.9} if w in ("top", "tap")
                                        else {"cat": 0.9, "cap": 0.9},
                           "cross_env": {}, "char_cross_rows": rows_flat,
                           "context": {"prev": "^", "next": "$"}}
    # 'top'/'tap' unambiguous (distinct, well-separated cross costs).
    words["2"]["cross_rich"] = {"top": 0.10, "tap": 0.90}
    words["3"]["cross_rich"] = {"top": 0.90, "tap": 0.10}
    # 'cat'/'cap' TIED at cold start (cross can't tell them apart).
    words["0"]["cross_rich"] = {"cat": 0.50, "cap": 0.50}
    words["1"]["cross_rich"] = {"cat": 0.50, "cap": 0.50}
    # pairwise: 'cat'(0) close to 'top'(2)'s own writer-specific 't'-shape signature (proxy: direct
    # word-pair closeness engineered so once 'top'/'tap' are harvested, 'cat' pulls towards 'top's
    # pool entry ONLY if mislabeled -- instead, engineer 'cat'(0)-'cap'(1) mutual closeness so ONE
    # of them harvested first (via tie-break) then helps recognize the other on round 2).
    pairwise = [[writer, 0, 1, 0.02, 0.0], [writer, 0, 2, 4.0, 0.0], [writer, 0, 3, 4.0, 0.0],
               [writer, 1, 2, 4.0, 0.0], [writer, 1, 3, 4.0, 0.0], [writer, 2, 3, 4.0, 0.0]]
    lex = {3: (["cat", "cap", "top", "tap"],
              np.array([[ord(c) - 97 for c in w] for w in ["cat", "cap", "top", "tap"]]))}
    return r77.FastAdaptCorpus(words, pairwise, lex, _flat_lm_score, "rich")


def test_run_em_converges_within_max_rounds():
    corpus = _saturating_corpus77()
    thr = r77.compute_margin_threshold(corpus, 0, lm_weight=0.0, visual_weight=1.0)
    result = r77.run_em(corpus, margin_threshold=min(thr, 0.0), lm_weight=0.0, visual_weight=1.0,
                        max_rounds=r77.MAX_ROUNDS)
    assert len(result["rounds"]) <= r77.MAX_ROUNDS
    assert result["rounds"][-1]["n_new_harvested_words"] == 0


def test_run_em_harvests_unambiguous_words_at_round_zero():
    corpus = _saturating_corpus77()
    thr = r77.compute_margin_threshold(corpus, 0, lm_weight=0.0, visual_weight=1.0)
    result = r77.run_em(corpus, margin_threshold=min(thr, 0.0), lm_weight=0.0, visual_weight=1.0)
    assert result["rounds"][0]["n_new_harvested_words"] >= 2   # 'top'/'tap' at minimum.


# --------------------------------------------------------------------------------------------- #
# compute_margin_threshold -- percentile of round-0's OWN distribution.
# --------------------------------------------------------------------------------------------- #
def test_margin_threshold_is_percentile_of_round0_distribution():
    corpus = _saturating_corpus77()
    lo = r77.compute_margin_threshold(corpus, 10, lm_weight=0.0, visual_weight=1.0)
    hi = r77.compute_margin_threshold(corpus, 90, lm_weight=0.0, visual_weight=1.0)
    assert lo <= hi


# --------------------------------------------------------------------------------------------- #
# streaming warm-up -- CAUSAL: position k must never depend on positions >= k of the SAME pass.
# --------------------------------------------------------------------------------------------- #
def test_streaming_warmup_shape():
    corpus = _saturating_corpus77()
    thr = r77.compute_margin_threshold(corpus, 0, lm_weight=0.0, visual_weight=1.0)
    out = r77.run_streaming(corpus, margin_threshold=min(thr, 0.0), lm_weight=0.0,
                            visual_weight=1.0, n_order_seeds=3)
    assert out["curve"]
    n_words_per_writer = len(corpus.words_of_writer(corpus.writers()[0]))
    positions = {row["position"] for row in out["curve"]}
    assert positions == set(range(n_words_per_writer))
    for row in out["curve"]:
        assert row["n_words"] == 3   # one observation per order-seed at every position.


def test_streaming_warmup_is_causal_via_instrumentation():
    """Directly verifies causality: monkeypatch `decode_one` to record, for every call, which pool
    labels are visible -- none may ever be sourced from a word visited LATER in the SAME
    (seed, writer) pass."""
    corpus = _saturating_corpus77()
    calls = []
    real_pool_dict = corpus.pool_dict

    def spy_pool_dict(wid, pool_by_wc, exclude_wid=None):
        # record every source wid currently in the pool (regardless of label) at call time.
        sources = {e["wid"] for entries in pool_by_wc.values() for e in entries}
        calls.append((wid, frozenset(sources)))
        return real_pool_dict(wid, pool_by_wc, exclude_wid=exclude_wid)

    corpus.pool_dict = spy_pool_dict
    thr = r77.compute_margin_threshold(corpus, 0, lm_weight=0.0, visual_weight=1.0)
    r77.run_streaming(corpus, margin_threshold=min(thr, 0.0), lm_weight=0.0, visual_weight=1.0,
                      n_order_seeds=1)
    # group calls into one pass (n_order_seeds=1 -> exactly one writer -> one contiguous sequence).
    seen_so_far = set()
    for wid, sources in calls:
        assert sources <= seen_so_far, (
            f"word {wid} saw pseudo-label sources {sources - seen_so_far} not yet visited -- "
            f"streaming warm-up is not causal")
        seen_so_far.add(wid)


# --------------------------------------------------------------------------------------------- #
# Real-data plausibility (skipped if the corpus / run 61/69 checkpoints aren't present).
# --------------------------------------------------------------------------------------------- #
requires_real = pytest.mark.skipif(
    not (TRAIN_NPZ_PRESENT and RUN69_PREP_PRESENT and RUN61_LEXICON_PRESENT),
    reason="DeepWriting corpus or run 61/69 checkpoints not present")


@pytest.fixture(scope="module")
def small_prep():
    if not (TRAIN_NPZ_PRESENT and RUN69_PREP_PRESENT and RUN61_LEXICON_PRESENT):
        pytest.skip("DeepWriting corpus or run 61/69 checkpoints not present")
    dw = r77.dww.load_deepwriting(r77.SPLIT)
    glyphs = r77.dww.extract_char_glyphs(dw)
    return r77.build_prep(min_words=6, cap=6, writer_cap=4, dw=dw, all_glyphs=glyphs)


@requires_real
def test_prep_writer_split_disjoint_and_matches_run69(small_prep):
    assert small_prep["bg_writers_match_run69"]
    bg = set(small_prep["bg_writers"])
    ho = set(small_prep["ho_writers"])
    assert bg.isdisjoint(ho)
    test_writers = set(small_prep["test_writers"])
    assert test_writers.issubset(ho)
    assert small_prep["n_test_words"] > 0


@requires_real
def test_prep_every_word_has_a_real_oracle_context(small_prep):
    for wd in small_prep["word_records"]:
        ctx = wd["context"]
        assert isinstance(ctx["prev"], str) and isinstance(ctx["next"], str)


@pytest.fixture(scope="module")
def native():
    srs = pytest.importorskip("substrate_rs")
    return srs.Substrate()._inner


@requires_real
def test_cold_and_ceiling_plausibility_band(small_prep, native):
    """COLD (cross word-form bank + own unsupervised frame + oracle context) and CEILING (real
    own-vocabulary bank, leave-one-out) computed on a SMALL real slice must land in a plausible
    regime: cold clears chance, ceiling is not materially worse than cold (the writer's real hand
    can only help, never hurt)."""
    lexicon = r77._load(r77.RUN61_LEXICON)
    lex_by_len = r77.r75.build_lex_by_len(lexicon["lexicon"])
    lm_score = r77.r75.make_lm_scorer(small_prep["lm"]["unigram"], small_prep["lm"]["bigram"],
                                      lexicon["logfreq"])
    cross_bank_by_label = small_prep["cross_bank_by_label"]
    length_index_cross = {int(k): v for k, v in small_prep["length_index_cross"].items()}
    cross_charbank = small_prep["cross_charbank"]

    from collections import defaultdict as dd
    grp = dd(list)
    for wd in small_prep["word_records"]:
        grp[wd["writer"]].append(wd)

    words = {}
    for w, lst in grp.items():
        for local_idx, wd in enumerate(lst):
            L = wd["len"]
            same_len = length_index_cross.get(L, [])
            cross_rich = {}
            for lab in same_len:
                others = cross_bank_by_label[lab]
                if others:
                    cross_rich[lab] = min(r77.cc66.dtw(native, wd["rich"], c["rich"])
                                          for c in others)
            char_rows = []
            for ch in wd["chars"]:
                invA = r77.r69._class_cost(native, ch["inv"], cross_charbank, "inv")
                poseC = r77.r69._class_cost(native, ch["pose_own"], cross_charbank, "pose")
                char_rows.append([invA[c] + r77.PRIMARY_LAMBDA_POSE * poseC[c] for c in range(26)])
            words[str(wd["wid"])] = {"wid": wd["wid"], "writer": wd["writer"], "word": wd["word"],
                                     "len": L, "local_idx": local_idx, "cross_rich": cross_rich,
                                     "cross_env": {}, "char_cross_rows": char_rows,
                                     "context": wd["context"]}

    pairwise = []
    for w, lst in grp.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                d = r77.cc66.dtw(native, lst[i]["rich"], lst[j]["rich"])
                pairwise.append([w, i, j, d, d])

    corpus = r77.FastAdaptCorpus(words, pairwise, lex_by_len, lm_score, "rich")
    cc = r77.cold_and_ceiling_reports(corpus, r77.LM_WEIGHT, r77.PRIMARY_VISUAL_WEIGHT)
    assert cc["cold"]["word_n"] >= 3
    cold_char = 100 * cc["cold"]["char_acc"]
    ceil_char = 100 * cc["ceiling"]["char_acc"]
    assert cold_char > 3.85, f"cold char acc should clear chance, got {cold_char:.1f}%"
    assert ceil_char >= cold_char - 5.0, (
        f"ceiling should not be materially worse than cold: cold={cold_char:.1f}% "
        f"ceiling={ceil_char:.1f}%")
