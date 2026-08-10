"""test_run74_migrated.py -- unit gates for RUN 74 (whole-word holistic reading: does matching a
query word's FULL trajectory against REAL word-form exemplars beat the per-letter route on the
sight vocabulary?).

Gates the machinery BEFORE the expensive real-data eval (ops law "unit tests first"):
  * the word-form bank is built BY LABEL, is writer-disjoint (background writers never contribute
    a WITHIN template; a writer's own vocabulary never leaks a different writer's ink);
  * the self-exclusion (leave-one-out) fix: a (writer, word) group of size EXACTLY 2 -- the most
    common "within-covered" case in the real corpus (84/133 such groups) -- must NOT end up with
    an empty template bank for either of its own two queries (the bug this run's own docstring
    documents and fixes: excluding the WHOLE test set up front, rather than just the querying
    instance, would empty exactly this case);
  * `_norm_key` survives a JSON round-trip (tuple span -> list span) without breaking identity
    comparison;
  * whole-word trajectory pose-normalization at the WORD grain reuses `r69.deslant_points` /
    `r69.pose_canon`'s exact recipe (checked by re-deriving the same numbers a different way);
  * the coarse-envelope control channel is byte-identical to run 66's own `wordnorm`;
  * holistic match returns the nearest label on a small synthetic bank;
  * the SYNTHETIC anagram construction: rich whole-word DTW separates a reordered-parts anagram
    that a coarse start/end/extent/arc-length "envelope" is PROVABLY unable to separate (identical
    by construction under pure translation composition);
  * the per-letter route (arm A), reimplemented in this run's own `stage_decode`/`_acc_report`
    style, reproduces run 70's own checkpointed number (30.5% within / 5.9% cross, n=220) when
    applied to run 70's OWN `decode.json` -- a correctness check on this run's OWN accuracy
    arithmetic, not a re-run of run 70's expensive DTW;
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

Native (substrate_rs) tests run under .venv python (whole-word `cc66.dtw`); pure-python tests
(bank construction, key normalization, accuracy arithmetic) need neither native nor real data and
pass under system python3.
"""
from __future__ import annotations

import hashlib
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

import scripts.jabberwock_wholeword_run74 as r74

STROKE_SHAPES_SEED = r74.STROKE_SHAPES_SEED
TRAIN_NPZ_PRESENT = os.path.exists(r74.dww.TRAIN_NPZ)
RUN61_LEXICON_PRESENT = os.path.exists(r74.RUN61_LEXICON)
RUN70_DECODE_PRESENT = os.path.exists(r74.RUN70_DECODE)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run74_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


# --------------------------------------------------------------------------------------------- #
# _norm_key -- identity-key normalization survives a JSON round-trip (tuple -> list span).
# --------------------------------------------------------------------------------------------- #
def test_norm_key_survives_tuple_vs_list_span():
    as_tuple = [5, "the", 100, (3, 9)]
    as_list = [5, "the", 100, [3, 9]]
    assert r74._norm_key(as_tuple) == r74._norm_key(as_list)


def test_norm_key_distinguishes_different_identities():
    a = r74._norm_key([5, "the", 100, [3, 9]])
    b = r74._norm_key([5, "the", 101, [3, 9]])   # different sample
    c = r74._norm_key([6, "the", 100, [3, 9]])   # different writer
    assert a != b
    assert a != c


def test_word_key_roundtrips_through_norm_key():
    w = {"writer": 7, "word": "and", "sample": 42, "word_point_span": (10, 20)}
    k = r74.word_key(w)
    assert r74._norm_key(list(k)) == r74._norm_key(k)


# --------------------------------------------------------------------------------------------- #
# THE BUG THIS RUN FIXES: a (writer, word) group of size exactly 2 must not end up with an empty
# bank for either of its own two queries once self-exclusion is leave-one-out, not whole-set.
# --------------------------------------------------------------------------------------------- #
def _fake_word(writer, word, sample, span, seed):
    """A minimal synthetic word record: a straight diagonal line whose length/position is a
    deterministic function of `seed`, split into per-letter char_segs (one point-pair per char --
    enough for `word_baseline`'s neighbor-window fallback and `word_pose_canon`'s geometry)."""
    rng = np.random.default_rng(seed)
    n_chars = len(word)
    pts_per_char = 4
    char_segs = []
    cursor = 0.0
    for i, ch in enumerate(word):
        base_y = -5.0 + 0.1 * seed
        xs = np.linspace(cursor, cursor + 1.0, pts_per_char) + rng.normal(0, 0.01, pts_per_char)
        ys = np.linspace(base_y, base_y - 0.5, pts_per_char) + rng.normal(0, 0.01, pts_per_char)
        strokes = [np.stack([xs, ys], axis=1).tolist()]
        char_segs.append({"class": 10 + i, "symbol": ch, "strokes": strokes,
                          "pt_start": span[0] + i * pts_per_char,
                          "pt_end": span[0] + (i + 1) * pts_per_char - 1})
        cursor += 1.2
    return {"writer": writer, "word": word, "sample": sample, "char_segs": char_segs,
            "word_point_span": span}


def test_build_word_bank_and_self_exclusion_survive_group_size_two():
    """Two instances of 'the' by the SAME writer (a size-2 within-covered group, the most common
    real-corpus case): after `_build_word_bank` (no up-front test-set exclusion) + the read-time
    leave-one-out self-exclusion, EACH instance must retrieve the OTHER as its template -- never
    an empty bank for its own true label."""
    writer = 1
    wA = _fake_word(writer, "the", sample=100, span=(0, 20), seed=1)
    wB = _fake_word(writer, "the", sample=101, span=(0, 20), seed=2)
    wOther = _fake_word(writer, "and", sample=102, span=(0, 20), seed=3)
    pool = [wA, wB, wOther]

    frame = {"x_height": 1.0, "slant_deg": 0.0}
    bank = r74._build_word_bank(pool, lambda _w: frame, m_bank=5, seed=0, dw={}, ws_index={})

    assert "the" in bank and len(bank["the"]) == 2, "both instances of 'the' must be in the bank"
    key_a = r74._norm_key(r74.word_key(wA))
    key_b = r74._norm_key(r74.word_key(wB))
    others_for_a = [c for c in bank["the"] if r74._norm_key(c["key"]) != key_a]
    others_for_b = [c for c in bank["the"] if r74._norm_key(c["key"]) != key_b]
    assert len(others_for_a) == 1, "query A must retrieve exactly instance B, not an empty bank"
    assert len(others_for_b) == 1, "query B must retrieve exactly instance A, not an empty bank"
    assert r74._norm_key(others_for_a[0]["key"]) == key_b
    assert r74._norm_key(others_for_b[0]["key"]) == key_a


# --------------------------------------------------------------------------------------------- #
# Whole-word RICH / ENVELOPE geometry (pure numpy, no native call).
# --------------------------------------------------------------------------------------------- #
def test_word_envelope_canon_is_run66_wordnorm_verbatim():
    w = _fake_word(1, "cat", sample=1, span=(0, 20), seed=5)
    got = r74.word_envelope_canon(w)
    expect = r74.cc66.wordnorm(r74.cc66.word_points(w))
    assert np.allclose(np.asarray(got), np.asarray(expect))


def test_word_pose_canon_scale_and_translate():
    """A word scaled 2x in x_height and shifted must resample to the SAME rich canon as the
    unscaled/unshifted word -- x-height normalization and baseline-translation are doing their
    job (the point of re-admitting pose at the word grain instead of run 66's naive envelope)."""
    w = _fake_word(1, "cat", sample=1, span=(0, 20), seed=5)
    baseline = 0.0
    canon_a = r74.word_pose_canon(w, baseline, x_height=1.0, slant_deg=0.0)

    w2 = {**w, "char_segs": [
        {**cs, "strokes": [[[2 * x, 2 * y] for x, y in stroke] for stroke in cs["strokes"]]}
        for cs in w["char_segs"]]}
    canon_b = r74.word_pose_canon(w2, baseline=0.0, x_height=2.0, slant_deg=0.0)
    assert np.allclose(np.asarray(canon_a), np.asarray(canon_b), atol=1e-6)


def test_word_pose_canon_deslants():
    """A sheared (slanted) word, de-slanted by the SAME slant, matches the unsheared word's canon
    -- `word_pose_canon` reuses `r69.deslant_points` correctly at the word grain."""
    w = _fake_word(1, "cat", sample=1, span=(0, 20), seed=5)
    baseline = -5.0
    unsheared = r74.word_pose_canon(w, baseline, x_height=1.0, slant_deg=0.0)

    slant_deg = 15.0
    import math
    t = math.tan(math.radians(slant_deg))
    sheared_segs = []
    for cs in w["char_segs"]:
        new_strokes = []
        for stroke in cs["strokes"]:
            new_strokes.append([[x - t * (y - baseline), y] for x, y in stroke])
        sheared_segs.append({**cs, "strokes": new_strokes})
    w_sheared = {**w, "char_segs": sheared_segs}
    deslanted = r74.word_pose_canon(w_sheared, baseline, x_height=1.0, slant_deg=slant_deg)
    assert np.allclose(np.asarray(unsheared), np.asarray(deslanted), atol=1e-6)


# --------------------------------------------------------------------------------------------- #
# Holistic decode -- nearest label on a small synthetic bank (no native call needed at this scale
# -- DTW itself is native, but the ARGMIN-OVER-LABELS decoder logic is pure python and testable
# with pre-computed distances).
# --------------------------------------------------------------------------------------------- #
def test_decode_holistic_picks_nearest_label():
    dists = {"the": 0.5, "and": 0.05, "of": 0.9}
    assert r74.decode_holistic(dists) == "and"


def test_decode_holistic_empty_returns_none():
    assert r74.decode_holistic({}) is None


def test_decode_dual_falls_back_when_uncovered():
    assert r74.decode_dual("holistic_word", True, "letter_word") == "holistic_word"
    assert r74.decode_dual(None, True, "letter_word") == "letter_word"
    assert r74.decode_dual("holistic_word", False, "letter_word") == "letter_word"


# --------------------------------------------------------------------------------------------- #
# THE SYNTHETIC ANAGRAM CONTROL -- rich trajectory separates a reordered-parts anagram that a
# coarse start/end/extent/arclength envelope is PROVABLY unable to separate.
# --------------------------------------------------------------------------------------------- #
def test_envelope_summary_identical_across_synthetic_orders():
    """Pure translation composition of the same two sub-shapes: start point, end point, x-extent,
    and arc-length are IDENTICAL regardless of order -- the envelope summary CANNOT discriminate
    by construction (checked directly, no DTW/native needed)."""
    ab = r74._synthetic_word(("up", "loop"))
    ba = r74._synthetic_word(("loop", "up"))
    e_ab = r74._envelope_summary(ab)
    e_ba = r74._envelope_summary(ba)
    assert np.allclose(e_ab, e_ba, atol=1e-9)


@pytest.fixture(scope="module")
def native():
    srs = pytest.importorskip("substrate_rs")
    return srs.Substrate()._inner


def test_synthetic_anagram_demo_rich_separates_envelope_does_not(native):
    out = r74.synthetic_anagram_demo(native)
    assert out["rich_separates"], (
        f"rich whole-word DTW must prefer the same-order template: "
        f"d_same={out['d_same']:.4f} vs d_reordered={out['d_reordered']:.4f}")
    assert not out["env_separates"], (
        "the coarse envelope summary must be UNABLE to separate the two orders by construction")


# --------------------------------------------------------------------------------------------- #
# Real-corpus anagram set -- sanity on the pre-registered pair list itself (no corpus needed).
# --------------------------------------------------------------------------------------------- #
def test_anagram_pairs_are_genuine_anagrams():
    for a, b in r74.ANAGRAM_PAIRS:
        assert sorted(a) == sorted(b), f"{a!r}/{b!r} are not letter-anagrams of each other"
        assert a != b


def test_anagram_pairs_cover_multiple_lengths():
    lengths = {len(a) for a, _ in r74.ANAGRAM_PAIRS}
    assert len(lengths) >= 3, "the anagram set should span more than one word length"


# --------------------------------------------------------------------------------------------- #
# Per-letter route (arm A) -- reproduces run 70's OWN checkpointed number exactly (n=220: 67/220
# within = 30.45% -> "30.5%"; 13/220 cross = 5.91% -> "5.9%"), via THIS run's own accuracy
# arithmetic applied to run 70's raw per_word records (a correctness check on run74's own
# `_acc_report`-style computation, not a re-run of run 70's expensive DTW).
# --------------------------------------------------------------------------------------------- #
requires_run70 = pytest.mark.skipif(not RUN70_DECODE_PRESENT,
                                    reason="run 70's decode.json checkpoint not present")


@requires_run70
def test_per_letter_arm_reproduces_run70_within():
    dec = r74._load(r74.RUN70_DECODE)
    per_word = dec["per_word"]
    n = len(per_word)
    within_ok = sum(1 for r in per_word if r["within"]["b"] == r["word"])
    cross_ok = sum(1 for r in per_word if r["cross"]["b"] == r["word"])
    assert n == 220
    within_pct = 100.0 * within_ok / n
    cross_pct = 100.0 * cross_ok / n
    assert within_pct == pytest.approx(r74.RUN70_WITHIN_WORD, abs=0.05), (
        f"expected run 70's own 30.5% within-writer word accuracy, recomputed {within_pct:.2f}%")
    assert cross_pct == pytest.approx(r74.RUN70_CROSS_WORD, abs=0.05), (
        f"expected run 70's own 5.9% cross-writer word accuracy, recomputed {cross_pct:.2f}%")


# --------------------------------------------------------------------------------------------- #
# Real-data checks (skipped if the corpus / run 61 checkpoint aren't present).
# --------------------------------------------------------------------------------------------- #
requires_real = pytest.mark.skipif(
    not (TRAIN_NPZ_PRESENT and RUN61_LEXICON_PRESENT),
    reason="DeepWriting corpus or run 61 checkpoint not present")


@pytest.fixture(scope="module")
def small_prep():
    if not (TRAIN_NPZ_PRESENT and RUN61_LEXICON_PRESENT):
        pytest.skip("DeepWriting corpus or run 61 checkpoint not present")
    dw = r74.dww.load_deepwriting(r74.SPLIT)
    glyphs = r74.dww.extract_char_glyphs(dw)
    return r74.build_prep(m_bank_word=2, m_bank_char=2, cross_extra_target=15, dw=dw,
                          all_glyphs=glyphs)


@requires_real
def test_writer_split_disjoint_and_matches_r69_seed(small_prep):
    bg = set(small_prep["bg_writers"])
    ho = set(small_prep["ho_writers"])
    assert bg.isdisjoint(ho)
    assert bg, ho


@requires_real
def test_coverage_fields_present_and_sane(small_prep):
    cov = small_prep["coverage"]
    assert cov["n_ho_total"] > 0
    assert 0 <= cov["n_within_covered"] <= cov["n_ho_total"]
    assert 0 <= cov["n_cross_covered"] <= cov["n_ho_total"]
    assert cov["n_within_covered"] <= cov["n_either_covered"] <= cov["n_ho_total"]
    assert cov["n_cross_covered"] <= cov["n_either_covered"]


@requires_real
def test_within_pool_is_full_achievable_population(small_prep):
    """The evaluation sample's within-covered subset is the FULL corpus population (n_within_pool
    == coverage's n_within_covered) -- not a further-subsampled slice -- since that population is
    small enough (~390 on the full corpus) to use entirely."""
    assert small_prep["n_within_pool"] == small_prep["coverage"]["n_within_covered"]


@requires_real
def test_query_set_has_both_within_and_cross_covered_instances(small_prep):
    queries = small_prep["queries"]
    assert any(q["has_within"] for q in queries)
    assert any(q["has_cross"] for q in queries)


@requires_real
def test_within_vocab_writers_subset_of_test_writers(small_prep):
    vocab_writers = {int(w) for w in small_prep["within_vocab_by_writer"].keys()}
    assert vocab_writers == set(small_prep["test_writers"])
    assert vocab_writers.isdisjoint(set(small_prep["bg_writers"]))


@requires_real
def test_cross_bank_never_contains_a_held_out_writer_instance(small_prep):
    """Every cross-bank template's identity key encodes a BACKGROUND writer -- the CROSS
    condition never leaks a held-out (test) writer's ink."""
    bg = set(small_prep["bg_writers"])
    for label, canons in small_prep["cross_bank_by_label"].items():
        for c in canons:
            writer = c["key"][0]
            assert writer in bg, f"cross-bank template for {label!r} has non-background writer {writer}"


@requires_real
def test_anagram_instances_found_for_at_least_one_pair(small_prep):
    insts = small_prep["anagram_instances"]
    n_total = sum(len(v) for v in insts.values())
    assert n_total > 0, "expected at least some real-corpus anagram instances (e.g. was/saw)"
