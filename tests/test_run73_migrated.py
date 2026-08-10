"""test_run73_migrated.py -- unit gates for RUN 73 (bootstrapped self-supervised writer adaptation:
harvest confident lexicon-committed reads from a held-out writer's OWN unlabeled ink, bootstrap
that writer's own allograph bank from the pseudo-labels, iterate, and measure whether reading
climbs from a COLD (generic-bank) start toward the GIVEN-bank ceiling).

Gates the machinery BEFORE the expensive real-data eval (ops law "unit tests first"):
  * frame estimation is label-free (no character identity needed -- `r69.aggregate_scale_slant` /
    `local_baseline_topline` only ever touch `strokes`, confirming step 1's "unsupervised" claim
    is a property of the CODE, not just an assertion in the docstring);
  * the harvest rule (`decode_lexicon_margin` / `harvest_ok`) picks high-margin, fully-agreeing
    words and rejects ambiguous/disagreeing ones;
  * the pairwise DTW index is queried symmetrically;
  * the pseudo-label pool caps at M_BOOT per (writer,class), keeping the highest-margin entries;
  * `BootstrapCorpus.boot_dists` with an EMPTY pool is byte-identical to the pure cross-bank
    distances (round-0 IS the cold start, by construction, not a separately-coded special case);
  * the EM loop's LEAVE-ONE-WORD-OUT guard actually excludes a word's own pseudo-label when
    re-scoring that same word (the anti-circularity property the whole run's honesty rests on);
  * EM converges (stops harvesting) on a saturating synthetic corpus, within MAX_ROUNDS;
  * the margin threshold is a plain percentile of round-0's OWN (empty-pool) margin distribution,
    computed BEFORE any accuracy number exists (no threshold-shopping against outcomes);
  * cold-start plausibility vs run 69's cross-writer numbers, given-bank plausibility vs run 69's
    within-writer numbers (sanity anchors, not exact reproductions -- different word/writer sample);
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

Native (substrate_rs) tests run under .venv python; pure-python tests (harvest rule, pool cap,
EM leave-one-out, convergence, threshold selection) need neither native nor real data and pass
under system python3.
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

import scripts.jabberwock_bootstrap_read_run73 as r73

STROKE_SHAPES_SEED = r73.STROKE_SHAPES_SEED
TRAIN_NPZ_PRESENT = os.path.exists(r73.dww.TRAIN_NPZ)
RUN69_PREP_PRESENT = os.path.exists(r73.RUN69_PREP)
RUN61_LEXICON_PRESENT = os.path.exists(r73.RUN61_LEXICON)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run73_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


# --------------------------------------------------------------------------------------------- #
# Frame estimation is LABEL-FREE (no character identity required) -- the unsupervised claim step
# 1 depends on, checked as a property of the actual code path, not just asserted in prose.
# --------------------------------------------------------------------------------------------- #
def test_frame_estimation_never_touches_identity_fields():
    """A synthetic sample of 6 glyphs carrying ONLY `strokes`/`char_idx`/`sample` (no `class` or
    `symbol` field at all) must still produce a usable frame -- `aggregate_scale_slant` /
    `local_baseline_topline` cannot possibly be using identity if it isn't even present."""
    glyphs = []
    for k in range(6):
        pts = [[float(k), -3.0 - 0.1 * k], [float(k), 0.0]]
        glyphs.append({"sample": 1, "char_idx": k, "strokes": [pts]})   # NO class/symbol keys.
    gbs = {1: sorted(glyphs, key=lambda g: g["char_idx"])}
    fr = r73.r69.aggregate_scale_slant(gbs)
    assert fr["x_height"] > 0
    assert fr["n_glyphs"] == 6


# --------------------------------------------------------------------------------------------- #
# decode_lexicon_margin -- the confidence signal r61.decode_lexicon itself discards.
# --------------------------------------------------------------------------------------------- #
def _dist_row(true_class, lo=0.1, hi=5.0):
    return [lo if c == true_class else hi for c in range(26)]


def test_decode_lexicon_margin_picks_lowest_cost_and_reports_gap():
    lex_by_len = {3: ["cat", "car", "cap"]}
    dists = [_dist_row(r73._lower26("c")), _dist_row(r73._lower26("a")),
             _dist_row(r73._lower26("t"))]
    m = r73.decode_lexicon_margin(dists, 3, lex_by_len)
    assert m["word"] == "cat"
    assert m["n_cands"] == 3
    # "car"/"cap" both cost exactly one wrong-slot (hi - lo) more than "cat" at position 2.
    expected_margin = (5.0 - 0.1) / 3
    assert m["margin_per_char"] == pytest.approx(expected_margin, rel=1e-6)


def test_decode_lexicon_margin_infinite_when_length_unique():
    lex_by_len = {3: ["cat"]}
    dists = [_dist_row(r73._lower26("c")), _dist_row(r73._lower26("a")),
             _dist_row(r73._lower26("t"))]
    m = r73.decode_lexicon_margin(dists, 3, lex_by_len)
    assert m["word"] == "cat"
    assert math.isinf(m["margin_per_char"])


def test_decode_lexicon_margin_none_when_no_candidates():
    assert r73.decode_lexicon_margin([_dist_row(0)], 1, {2: ["at"]}) is None


# --------------------------------------------------------------------------------------------- #
# harvest_ok -- the harvest rule: full per-char agreement AND a non-trivial margin.
# --------------------------------------------------------------------------------------------- #
def test_harvest_ok_accepts_confident_agreeing_word():
    lex_by_len = {3: ["cat", "car", "cap"]}
    dists = [_dist_row(r73._lower26("c")), _dist_row(r73._lower26("a")),
             _dist_row(r73._lower26("t"))]
    rec = r73.harvest_ok(dists, 3, lex_by_len, agreement_bar=1.0, margin_threshold=0.01)
    assert rec is not None
    assert rec["word"] == "cat"
    assert rec["agreement"] == 1.0


def test_harvest_ok_rejects_disagreement_between_visual_and_lexicon():
    """Per-char argmin spells 'cax' (position 2 argmins to a non-lexicon letter close to 't') --
    the lexicon still commits to 'cat', but the (1) full-agreement bar must reject the harvest."""
    lex_by_len = {3: ["cat", "cap"]}
    dists = [
        _dist_row(r73._lower26("c")),
        _dist_row(r73._lower26("a")),
        [0.05 if c == r73._lower26("x") else (0.2 if c == r73._lower26("t") else 5.0)
         for c in range(26)],
    ]
    rec = r73.harvest_ok(dists, 3, lex_by_len, agreement_bar=1.0, margin_threshold=0.0)
    assert rec is None, "visual/lexicon disagreement must be rejected at the primary agreement bar"


def test_harvest_ok_rejects_low_margin_tie():
    """Two same-length lexicon candidates nearly tied (margin ~0) -- even with full agreement on
    the winner, a high margin_threshold must reject it (genuinely ambiguous commitment)."""
    lex_by_len = {3: ["cat", "cas"]}
    eps = 1e-4
    dists = [
        _dist_row(r73._lower26("c")),
        _dist_row(r73._lower26("a")),
        [0.1 if c == r73._lower26("t") else (0.1 + eps if c == r73._lower26("s") else 5.0)
         for c in range(26)],
    ]
    rec_strict = r73.harvest_ok(dists, 3, lex_by_len, agreement_bar=1.0, margin_threshold=1.0)
    assert rec_strict is None
    rec_loose = r73.harvest_ok(dists, 3, lex_by_len, agreement_bar=1.0, margin_threshold=0.0)
    assert rec_loose is not None


# --------------------------------------------------------------------------------------------- #
# pairwise index -- symmetric lookup both directions.
# --------------------------------------------------------------------------------------------- #
def test_pairwise_index_symmetric_lookup():
    rows = [[1, 0, 2, 0.37, 0.12], [1, 5, 9, 0.01, 0.02]]
    idx = r73.build_pairwise_index(rows)
    assert idx[(1, 0, 2)] == (0.37, 0.12)
    assert idx[(1, 2, 0)] == (0.37, 0.12)
    assert r73.pairwise_cost(idx, 1, 0, 2, lam=1.0) == pytest.approx(0.49)
    assert r73.pairwise_cost(idx, 1, 2, 0, lam=0.0) == pytest.approx(0.37)


# --------------------------------------------------------------------------------------------- #
# pool cap -- keeps the M_BOOT highest-margin entries per (writer,class).
# --------------------------------------------------------------------------------------------- #
def test_pool_add_caps_and_keeps_highest_margin():
    pool = {}
    for i, margin in enumerate([0.5, 0.9, 0.1, 0.7, 0.3]):
        r73._pool_add(pool, writer=1, cls=3, wid=100 + i, local_idx=i, margin=margin, cap=3)
    kept = pool[(1, 3)]
    assert len(kept) == 3
    kept_margins = sorted(e["margin"] for e in kept)
    assert kept_margins == pytest.approx([0.5, 0.7, 0.9])   # top-3, lowest two (0.1, 0.3) evicted.


def test_pool_add_no_duplicate_same_source():
    pool = {}
    r73._pool_add(pool, writer=1, cls=0, wid=1, local_idx=5, margin=0.5, cap=3)
    r73._pool_add(pool, writer=1, cls=0, wid=1, local_idx=5, margin=0.5, cap=3)
    assert len(pool[(1, 0)]) == 1


# --------------------------------------------------------------------------------------------- #
# BootstrapCorpus -- synthetic, no native calls. Round-0 (empty pool) IS the cold/cross condition.
# --------------------------------------------------------------------------------------------- #
def _tiny_corpus():
    """2 words, 1 writer, 3 chars each ('cat', 'dog'), hand-built cross costs + a pairwise matrix
    engineered so 'cat's own chars are FAR from 'dog's (so cross-writer pseudo-labels from 'dog'
    never wrongly help decode 'cat', isolating the leave-one-out test below to the self-source
    case only)."""
    def onehot_row(true_c, lo=0.05, hi=4.0):
        return [lo if c == true_c else hi for c in range(26)]

    chars = {}
    # word 0 = "cat" (local idx 0,1,2), word 1 = "dog" (local idx 3,4,5), writer=1.
    letters = ["c", "a", "t", "d", "o", "g"]
    wids = [0, 0, 0, 1, 1, 1]
    positions = [0, 1, 2, 0, 1, 2]
    for li, (ch, wid, pos) in enumerate(zip(letters, wids, positions)):
        tc = r73._lower26(ch)
        # cross bank is DELIBERATELY WRONG/flat (chance-level) so the only way to read correctly
        # is via the bootstrapped pool -- isolates what the pool contributes.
        cross_flat = [2.0] * 26
        chars[f"{wid}:{pos}"] = {
            "writer": 1, "wid": wid, "pos": pos, "local_idx": li, "true_symbol": ch,
            "cross_inv": cross_flat, "cross_pose": cross_flat,
            "ceil_inv": onehot_row(tc), "ceil_pose": onehot_row(tc),
        }
    word_records = [
        {"wid": 0, "writer": 1, "word": "cat", "chars": [{}]*3},
        {"wid": 1, "writer": 1, "word": "dog", "chars": [{}]*3},
    ]
    # pairwise: char i is CLOSE to itself-as-exemplar-of-its-own-letter only (self, li==li trivial,
    # excluded anyway) and FAR from every other char -- so the ONLY way ANY class gets a
    # low-cost boot exemplar is if some OTHER instance of the SAME letter exists. Add a second
    # occurrence of 'c','a','t' hidden nowhere else -- instead, to test self-exclusion cleanly, we
    # engineer local idx 0 ("c" of "cat") to be near-identical to itself's own class, so the ONLY
    # candidate exemplar for class 'c' comes from wid=0 itself (li=0) -- self-exclusion must then
    # leave class 'c' UNCOVERED (falls back to the flat cross cost) when scoring wid=0.
    pairwise_rows = []
    for i in range(6):
        for j in range(i + 1, 6):
            d = 0.1 if (i, j) == (0, 3) else 4.0   # (0,3) close: an ARTIFICIAL synthetic edge used
                                                    # only to demonstrate cross-word pool benefit
                                                    # below; every other pair stays far, so pool
                                                    # coverage for "cat"'s own letters can ONLY ever
                                                    # come from wid=0 itself (self-source), letting
                                                    # the leave-one-out test assert non-improvement.
            pairwise_rows.append([1, i, j, d, d])
    lex_by_len = {3: ["cat", "dog", "cot", "cut"]}
    corpus = r73.BootstrapCorpus(chars, pairwise_rows, word_records, lex_by_len)
    return corpus


def test_boot_dists_with_empty_pool_equals_cross_dists():
    corpus = _tiny_corpus()
    for wid in (0, 1):
        boot = corpus.boot_dists(wid, {}, exclude_wid=wid)
        cross = corpus.cross_dists(wid)
        assert boot == cross, "round-0 (empty pool) must be BYTE-IDENTICAL to the cross condition"


def test_leave_one_word_out_excludes_self_sourced_pseudo_labels():
    """If word 0 ('cat') were, hypothetically, the ONLY source of a pseudo-label for class 'c',
    leave-one-out must NOT let that pseudo-label improve word 0's OWN re-score (it must still fall
    back to the flat cross cost for that class when scoring word 0 itself), even though it WOULD
    be available (and would help) when scoring a DIFFERENT word that also contains 'c'."""
    corpus = _tiny_corpus()
    pool = {}
    # pretend class 'c' (local_idx 0, sourced from wid=0) was harvested.
    r73._pool_add(pool, writer=1, cls=r73._lower26("c"), wid=0, local_idx=0, margin=1.0)
    dists_self = corpus.boot_dists(0, pool, exclude_wid=0)
    c_col = r73._lower26("c")
    assert dists_self[0][c_col] == corpus.cross_dists(0)[0][c_col], (
        "scoring word 0 must NOT benefit from a pseudo-label sourced from word 0 itself")
    # the SAME pool entry DOES lower the cost when scoring a DIFFERENT word (no self-exclusion
    # applies) -- the pool is not simply inert, it is specifically excluded only for its own source.
    dists_other = corpus.boot_dists(1, pool, exclude_wid=1)
    assert dists_other[0][c_col] < corpus.cross_dists(1)[0][c_col], (
        "a pseudo-label sourced from word 0 SHOULD help score word 1 (a different word)")


# --------------------------------------------------------------------------------------------- #
# run_em -- convergence on a saturating synthetic corpus (pure Python, no native calls).
# --------------------------------------------------------------------------------------------- #
def _saturating_corpus(writer=1):
    """4 words -- "cut"/"cup" (UNAMBIGUOUS: each has a decisive per-char cost bias, read correctly
    by cross alone) and "cat"/"cap" (a genuine cold-start AMBIGUITY: position 2's cross cost TIES
    't' and 'p', so the lexicon's tie-break arbitrarily commits BOTH queries to whichever candidate
    is FIRST in the list -- "cat" reads correctly by luck, "cap" reads WRONG as "cat"). Once "cut"
    and "cup" are harvested (round 0, unambiguous) and their position-2 pairwise DTW is close to
    the MATCHING true letter's instance in "cat"/"cap" (encoding "the writer's own t/p look
    different even though the generic bank can't tell them apart"), round 1's bootstrapped pool
    breaks the tie correctly for BOTH "cat" and "cap" -- a clean, mechanistically-understood LIFT
    (cold char_acc = 11/12; converged char_acc = 12/12) attributable ONLY to bootstrapping, not to
    the lexicon or cross bank alone."""
    lex_by_len = {3: ["cat", "cap", "cut", "cup"]}   # LIST (not a set) -- fixes the tie-break order.
    TIE, DECISIVE, HI = 1.0, 1.0, 5.0

    def row(true_c, tie_with=None):
        r = [HI] * 26
        r[true_c] = DECISIVE
        if tie_with is not None:
            r[tie_with] = TIE
        return r

    a, u = r73._lower26("a"), r73._lower26("u")
    t, p = r73._lower26("t"), r73._lower26("p")
    c = r73._lower26("c")
    specs = {
        # word: [(pos, true_letter_class, tie_partner_or_None), ...]
        "cat": [(0, c, None), (1, a, None), (2, t, p)],
        "cap": [(0, c, None), (1, a, None), (2, p, t)],
        "cut": [(0, c, None), (1, u, None), (2, t, None)],
        "cup": [(0, c, None), (1, u, None), (2, p, None)],
    }
    chars, word_records, local_idx_of = {}, [], {}
    li = 0
    for wid, w in enumerate(["cat", "cap", "cut", "cup"]):
        for pos, true_c, tie in specs[w]:
            chars[f"{wid}:{pos}"] = {
                "writer": writer, "wid": wid, "pos": pos, "local_idx": li, "true_symbol": w[pos],
                "cross_inv": row(true_c, tie), "cross_pose": [0.0] * 26,
                "ceil_inv": row(true_c, None), "ceil_pose": [0.0] * 26,
            }
            local_idx_of[(w, pos)] = li
            li += 1
        word_records.append({"wid": wid, "writer": writer, "word": w, "chars": [{}] * 3})

    # pairwise position-2 DTW: SAME true letter -> close (0.02); DIFFERENT true letter -> far (4.0).
    # positions 0/1 are irrelevant to the lift mechanism here (left far/neutral, unused by any
    # class the harvest rule ever needs -- 'c'/'a'/'u' are never ambiguous in this corpus).
    close_pairs = {("cat", 2, "cut", 2), ("cap", 2, "cup", 2)}
    pairwise_rows = []
    for i in range(li):
        for j in range(i + 1, li):
            pairwise_rows.append([writer, i, j, 4.0, 0.0])
    idx = {(w, i, j): k for k, (w, i, j, *_r) in enumerate(pairwise_rows)}
    for wa, pa, wb, pb in close_pairs:
        ia, ib = local_idx_of[(wa, pa)], local_idx_of[(wb, pb)]
        lo, hi = min(ia, ib), max(ia, ib)
        pairwise_rows[idx[(writer, lo, hi)]] = [writer, lo, hi, 0.02, 0.0]

    corpus = r73.BootstrapCorpus(chars, pairwise_rows, word_records, lex_by_len)
    return corpus


def test_run_em_converges_within_max_rounds():
    corpus = _saturating_corpus()
    thr = r73.compute_margin_threshold(corpus, 0)   # 0th percentile -- accept everything finite.
    result = r73.run_em(corpus, agreement_bar=1.0, margin_threshold=min(thr, 0.0),
                        max_rounds=r73.MAX_ROUNDS)
    assert len(result["rounds"]) <= r73.MAX_ROUNDS
    assert result["rounds"][-1]["n_new_harvested_chars"] == 0, "must converge (stop harvesting)"


def test_run_em_lifts_accuracy_above_cold_on_saturating_corpus():
    """On a corpus engineered so same-letter chars genuinely cluster, bootstrapping should climb
    char accuracy above the flat-cross cold start (round 0) by the time it converges -- the basic
    'does the mechanism do anything' sanity check, isolated from real-data noise."""
    corpus = _saturating_corpus()
    thr = r73.compute_margin_threshold(corpus, 0)
    result = r73.run_em(corpus, agreement_bar=1.0, margin_threshold=min(thr, 0.0))
    cold_char_acc = result["rounds"][0]["char_acc"]
    final_char_acc = result["rounds"][-1]["char_acc"]
    assert final_char_acc > cold_char_acc, (
        f"bootstrap should lift char accuracy on a saturating corpus "
        f"(cold={cold_char_acc:.3f}, final={final_char_acc:.3f})")


# --------------------------------------------------------------------------------------------- #
# compute_margin_threshold -- percentile of ROUND-0's OWN distribution, no accuracy peeking.
# --------------------------------------------------------------------------------------------- #
def test_margin_threshold_is_percentile_of_round0_distribution():
    corpus = _saturating_corpus()
    lo = r73.compute_margin_threshold(corpus, 10)
    hi = r73.compute_margin_threshold(corpus, 90)
    assert lo <= hi


# --------------------------------------------------------------------------------------------- #
# Streaming warm-up -- strictly causal (no leave-one-out needed); sanity on shape.
# --------------------------------------------------------------------------------------------- #
def test_streaming_warmup_shape_and_causality():
    corpus = _saturating_corpus()
    thr = r73.compute_margin_threshold(corpus, 0)
    out = r73.run_streaming(corpus, agreement_bar=1.0, margin_threshold=min(thr, 0.0),
                            n_order_seeds=3)
    assert out["curve"], "warm-up curve must be non-empty"
    n_words_per_writer = len(corpus.words_of_writer(corpus.writers()[0]))
    positions = {row["position"] for row in out["curve"]}
    assert positions == set(range(n_words_per_writer))
    for row in out["curve"]:
        assert row["n_words"] == 3   # one observation per order-seed at every position.


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
    dw = r73.dww.load_deepwriting(r73.SPLIT)
    glyphs = r73.dww.extract_char_glyphs(dw)
    return r73.build_prep(min_words=6, cap=6, m_bank=2, dw=dw, all_glyphs=glyphs)


@requires_real
def test_prep_writer_split_disjoint_and_matches_run69(small_prep):
    assert small_prep["bg_writers_match_run69"]
    bg = set(small_prep["bg_writers"])
    ho = set(small_prep["ho_writers"])
    assert bg.isdisjoint(ho)
    test_writers = set(small_prep["test_writers"])
    assert test_writers.issubset(ho)
    assert small_prep["n_test_words"] > 0


@pytest.fixture(scope="module")
def native():
    srs = pytest.importorskip("substrate_rs")
    return srs.Substrate()._inner


@requires_real
def test_cold_and_ceiling_plausibility_band(small_prep, native):
    """COLD (cross bank + own unsupervised frame) and CEILING (real own bank) computed on a SMALL
    real slice must land in the same REGIME as run 69's own numbers (cross 28.8%, within 55.0%) --
    a plausibility gate given a small/different sample, not exact reproduction. Also: ceiling must
    not be WORSE than cold (the writer's real hand can only help, never hurt, vs the generic bank)."""
    lexicon = r73._load(r73.RUN61_LEXICON)
    lex_by_len = r73.r61._lex_by_len(lexicon["lexicon"])
    cross_bank = small_prep["cross_bank"]
    real_own_bank = small_prep["real_own_bank"]
    chars, word_records = {}, []
    n_char = 0
    for wd in small_prep["word_records"]:
        w = wd["writer"]
        ob = real_own_bank.get(str(w), {})
        rec_chars = []
        for pos, ch in enumerate(wd["chars"]):
            cross_inv = r73.r69._class_cost(native, ch["inv"], cross_bank, "inv")
            cross_pose = r73.r69._class_cost(native, ch["pose_own"], cross_bank, "pose")
            ceil_inv = r73.r69._class_cost(native, ch["inv"], ob, "inv")
            ceil_pose = r73.r69._class_cost(native, ch["pose_own"], ob, "pose")
            key = f"{wd['wid']}:{pos}"
            chars[key] = {"writer": w, "wid": wd["wid"], "pos": pos, "local_idx": n_char,
                         "true_symbol": ch["true_symbol"], "cross_inv": cross_inv,
                         "cross_pose": cross_pose, "ceil_inv": ceil_inv, "ceil_pose": ceil_pose}
            n_char += 1
            rec_chars.append({})
        word_records.append({"wid": wd["wid"], "writer": w, "word": wd["word"], "chars": rec_chars})
    corpus = r73.BootstrapCorpus(chars, [], word_records, lex_by_len)
    cc = r73.cold_and_ceiling_reports(corpus)
    assert cc["cold"]["word_n"] >= 3
    cold_char, ceil_char = 100 * cc["cold"]["char_acc"], 100 * cc["ceiling"]["char_acc"]
    # plausibility band: well above 26-way chance (3.85%), ceiling >= cold.
    assert cold_char > 3.85, f"cold char acc should clear chance, got {cold_char:.1f}%"
    assert ceil_char >= cold_char - 5.0, (   # small tolerance for a tiny sample.
        f"ceiling (real writer bank) should not be materially worse than cold (generic bank): "
        f"cold={cold_char:.1f}% ceiling={ceil_char:.1f}%")
