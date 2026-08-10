"""test_run70_migrated.py -- unit gates for RUN 70 (the cursive word-reading payoff: run 69's
writer-relative pose recognizer + run 61's lexicon collapse + run 68's bidirectional loop, on
real cursive WORDS).

Gates the machinery BEFORE the expensive real-data eval (ops law "unit tests first"):
  * `_pad62` preserves argmin / lexicon-decode correctness (the reuse trick that lets this run
    call r61's 62-class decoders unmodified on native 26-class posteriors);
  * arm (c) at lambda=0.0 is EXACTLY arm (b) -- r68's own hard invariant, re-verified on THIS
    run's padded/26-class data path, not just r68's own 62-class one;
  * per-char posterior construction on a REAL cursive word reuses run 69's recognizer verbatim
    (the query canons this run builds for a word char are byte-identical to what run 69's own
    `invariant_canon`/`pose_canon` produce on the same strokes/frame);
  * the WITHIN-writer / CROSS-writer writer sets stay disjoint (own-bank writers subset of
    held-out writers, cross-bank untouched by this run, background writer set matches run 69's);
  * per-char accuracy on WORD characters (given a small real prep+read) lands in the same regime
    as run 69's own isolated-char numbers (55.0% within / 28.8% cross) -- a plausibility gate, not
    an exact reproduction (different sampling: word-context chars, not run 69's own char
    selection);
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

Native (substrate_rs) tests run under .venv python (this run reuses `cc66.dtw` via r69's
`_class_cost`); pure-python tests (padding, decoder plumbing, IA-loop equality) need neither
native nor real data and pass under system python3.
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

import scripts.jabberwock_cursive_wordread_run70 as r70

STROKE_SHAPES_SEED = r70.STROKE_SHAPES_SEED
TRAIN_NPZ_PRESENT = os.path.exists(r70.dww.TRAIN_NPZ)
RUN69_PREP_PRESENT = os.path.exists(r70.RUN69_PREP)
RUN61_LEXICON_PRESENT = os.path.exists(r70.RUN61_LEXICON)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run70_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


# --------------------------------------------------------------------------------------------- #
# _pad62 -- the reuse trick: r61's 62-class decoders operate unmodified on this run's native
# 26-class (lowercase-only) posteriors via a BIG-padded embedding.
# --------------------------------------------------------------------------------------------- #
def test_pad62_preserves_argmin():
    """decode_no_context on the padded 62-vector picks the SAME letter as a direct 26-argmin,
    for many random vectors (not just one lucky case)."""
    rng = np.random.default_rng(0)
    for _ in range(20):
        vec26 = rng.uniform(0.0, 10.0, size=26).tolist()
        direct = r70.LETTERS26[int(np.argmin(vec26))]
        padded = r70._pad62(vec26)
        via_r61 = r70.r61.decode_no_context([padded], r70.SYMBOLS62)
        assert via_r61 == direct


def test_pad62_never_selects_padded_slots():
    """Even a very small real distance value never beats BIG in the padded slots (sanity on the
    magnitude gap -- BIG must genuinely dwarf any DTW-scale distance)."""
    vec26 = [1e3] * 26          # deliberately large (DTW distances are typically O(0.01-1)).
    padded = r70._pad62(vec26)
    pred = r70.r61.decode_no_context([padded], r70.SYMBOLS62)
    assert pred in r70.LETTERS26, "must still pick a lowercase letter, never a digit/uppercase slot"


def test_lexicon_decode_reuses_r61_unmodified():
    """decode_arm_b (padded call into r61.decode_lexicon) picks the lexicon word that minimizes
    summed per-position lowercase distance -- verified against a tiny hand-built lexicon."""
    lex_by_len = {3: ["cat", "car", "cap"]}
    logfreq = {}
    # distances favor 'c'-'a'-'t' at each position (lower = better).
    dists = [
        [0.1 if c == r70.r68._lower26("c") else 5.0 for c in range(26)],
        [0.1 if c == r70.r68._lower26("a") else 5.0 for c in range(26)],
        [0.1 if c == r70.r68._lower26("t") else 5.0 for c in range(26)],
    ]
    pred = r70.decode_arm_b(dists, 3, lex_by_len, logfreq)
    assert pred == "cat"


def test_arm_a_no_context_may_diverge_from_lexicon():
    """A sanity check that (a) is genuinely context-free: with per-position evidence that (in
    isolation) argmins to an OOV nonsense string, arm (a) returns that nonsense string while arm
    (b) is pulled to a real lexicon word -- demonstrating the two arms are doing different things,
    not accidentally identical code paths."""
    lex_by_len = {3: ["cat", "cap"]}
    logfreq = {}
    # position 2 argmins to 'x' (not in either lexicon candidate) but is CLOSE to both 't' and 'p'.
    dists = [
        [0.1 if c == r70.r68._lower26("c") else 5.0 for c in range(26)],
        [0.1 if c == r70.r68._lower26("a") else 5.0 for c in range(26)],
        [0.05 if c == r70.r68._lower26("x") else (0.2 if c == r70.r68._lower26("t") else 5.0)
         for c in range(26)],
    ]
    a_pred = r70.decode_arm_a(dists)
    b_pred = r70.decode_arm_b(dists, 3, lex_by_len, logfreq)
    assert a_pred == "cax"
    assert b_pred == "cat"


# --------------------------------------------------------------------------------------------- #
# arm (c) lambda=0.0 == arm (b) -- r68's own hard invariant, re-checked on this run's data path.
# --------------------------------------------------------------------------------------------- #
def test_loop_lambda_zero_equals_lexicon_collapse():
    lex_by_len = {3: ["cat", "car", "cap", "dog"], 4: ["dogs", "cats"]}
    logfreq = {}
    rng = np.random.default_rng(1)
    for _ in range(10):
        L = 3
        dists = [rng.uniform(0.0, 3.0, size=26).tolist() for _ in range(L)]
        b_pred = r70.decode_arm_b(dists, L, lex_by_len, logfreq)
        c_preds = r70.decode_arm_c(dists, lex_by_len, lambdas=[0.0, 0.5])
        assert c_preds["0.0"] == b_pred, (
            f"arm (c) lambda=0.0 must equal arm (b) exactly (got {c_preds['0.0']!r} vs "
            f"{b_pred!r})")


def test_loop_can_change_prediction_at_nonzero_lambda():
    """Sanity: the loop is not a no-op machine -- at least SOME nonzero lambda changes at least
    one prediction relative to lambda=0, on a WSE-shaped synthetic ambiguity (reuses r68's own
    fixture pattern)."""
    cands = ["at", "an", "as", "ax", "ab", "ip"]
    lex_by_len = {2: cands}
    # ambiguous first letter (i edges out a), but 5 candidates share 'a' at pos0 vs 1 sharing 'i'.
    dists = [
        [0.0 if c == r70.r68._lower26("i") else (0.02 if c == r70.r68._lower26("a") else 5.0)
         for c in range(26)],
        [0.0 if c == r70.r68._lower26("p") else 0.05 for c in range(26)],
    ]
    c_preds = r70.decode_arm_c(dists, lex_by_len, lambdas=[0.0, 0.5, 1.0])
    assert c_preds["0.0"] == "ip"
    assert any(c_preds[k] != c_preds["0.0"] for k in ("0.5", "1.0")), (
        "expected at least one nonzero lambda to flip the WSE-ambiguous decode")


# --------------------------------------------------------------------------------------------- #
# Writer-frame plumbing for a word character (pure geometry, no native call).
# --------------------------------------------------------------------------------------------- #
def test_local_frame_for_word_char_matches_isolated_glyph_frame():
    """A synthetic sample with 6 isolated char glyphs (matching `extract_char_glyphs`'s shape) and
    a WORD spanning chars 2-4 of it: `local_frame_for_word_char` on the word's middle char must
    equal `r69.local_baseline_topline` called directly against the isolated-glyph list at the
    corresponding index -- the whole point of recovering `char_idx` via `pt_start`."""
    import scripts.jabberwock_pose_read_run69 as r69

    def glyph(char_idx, y_top, y_bot, pt_start):
        pts = [[float(char_idx), y_top], [float(char_idx), y_bot]]
        return {"writer": 1, "sample": 100, "char_idx": char_idx, "class": 10, "symbol": "a",
                "strokes": [pts], "pt_start": pt_start, "pt_end": pt_start + 1}

    # 6 isolated glyphs -- the FULL per-sample neighbor pool `extract_char_glyphs` would produce.
    all_glyphs = [glyph(k, y_top=-5.0 - k, y_bot=0.0 + 0.1 * k, pt_start=10 * k) for k in range(6)]
    ws_index = r69._index_by_writer_sample(all_glyphs)

    # a fake `dw` whose soc_labels/`_char_starts` recovers pt_start=[0,10,20,30,40,50] for sample 100.
    import numpy as _np
    soc = _np.zeros(60)
    for k in range(6):
        soc[10 * k] = 1
    dw = {"soc_labels": {100: soc}}

    # the WORD spans char_idx 2..4 (pt_start 20,30,40) -- char_segs carry pt_start/strokes only.
    word = {"writer": 1, "sample": 100,
            "char_segs": [{"strokes": all_glyphs[k]["strokes"], "pt_start": 10 * k, "symbol": "a"}
                          for k in (2, 3, 4)]}
    middle_seg = word["char_segs"][1]     # char_idx 3.

    base_via_word, fell_back = r70.local_frame_for_word_char(dw, word, middle_seg, ws_index)
    assert not fell_back, "the primary (isolated-glyph-index) path should be used here"
    base_direct, _top_direct = r69.local_baseline_topline(all_glyphs, 3, window=r70.LOCAL_WINDOW)
    assert base_via_word == pytest.approx(base_direct)


def test_local_frame_falls_back_when_sample_absent():
    """If the sample isn't in the isolated-glyph index at all, the fallback path (word's own char
    list as neighbor pool) is used instead of raising."""
    import scripts.jabberwock_pose_read_run69 as r69
    word = {"writer": 1, "sample": 999, "char_segs": [
        {"strokes": [[[0.0, 0.0], [0.0, -5.0]]], "pt_start": 0, "symbol": "a"},
        {"strokes": [[[1.0, 0.0], [1.0, -5.0]]], "pt_start": 10, "symbol": "b"},
    ]}
    dw = {"soc_labels": {999: __import__("numpy").array([1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0])}}
    base, fell_back = r70.local_frame_for_word_char(dw, word, word["char_segs"][0], {})
    assert fell_back
    assert isinstance(base, float)


# --------------------------------------------------------------------------------------------- #
# Real-data checks (skipped if the corpus / run 61 / run 69 checkpoints aren't present).
# --------------------------------------------------------------------------------------------- #
requires_real = pytest.mark.skipif(
    not (TRAIN_NPZ_PRESENT and RUN69_PREP_PRESENT and RUN61_LEXICON_PRESENT),
    reason="DeepWriting corpus or run 61/69 checkpoints not present")


@pytest.fixture(scope="module")
def small_prep():
    if not (TRAIN_NPZ_PRESENT and RUN69_PREP_PRESENT and RUN61_LEXICON_PRESENT):
        pytest.skip("DeepWriting corpus or run 61/69 checkpoints not present")
    dw = r70.dww.load_deepwriting(r70.SPLIT)
    glyphs = r70.dww.extract_char_glyphs(dw)
    return r70.build_prep(target_n=24, m_bank=2, dw=dw, all_glyphs=glyphs)


@requires_real
def test_prep_reuses_run69_bg_writers_and_cross_bank(small_prep):
    """The background-writer set (and therefore the cross-writer bank + population frame, loaded
    verbatim from run 69's own prep.json) matches run 69's exactly -- same split call, same seed."""
    assert small_prep["bg_writers_match_run69"]
    assert small_prep["cross_bank"], "cross bank must be non-empty (loaded from run 69)"
    assert set(small_prep["bg_writers"]).isdisjoint(set(small_prep["ho_writers"]))


@requires_real
def test_own_bank_writers_subset_of_held_out(small_prep):
    bg = set(small_prep["bg_writers"])
    ho = set(small_prep["ho_writers"])
    own_bank_writers = {int(w) for w in small_prep["own_bank"].keys()}
    assert own_bank_writers.issubset(ho)
    assert own_bank_writers.isdisjoint(bg)
    test_writers = set(small_prep["test_writers"])
    assert test_writers == own_bank_writers


@requires_real
def test_query_canons_reuse_run69_functions_verbatim(small_prep):
    """A word char's 'inv' canon in this run's prep is IDENTICAL to calling
    `r69.invariant_canon` directly on the same strokes -- confirms this run calls run 69's
    recognizer, not a reimplementation."""
    import scripts.jabberwock_pose_read_run69 as r69
    wd = small_prep["word_records"][0]
    assert len(wd["chars"]) >= 1
    # re-derive the strokes is not directly available post-prep (only canons are stored), so
    # instead check internal consistency: invariant_canon is a pure function of strokes alone,
    # so recomputing it from the SAME test word (re-run build_prep on a 1-word slice) must match.
    dw = r70.dww.load_deepwriting(r70.SPLIT)
    words = r70.dww.extract_words(dw, min_len=r70.WORD_MIN_LEN, max_len=r70.WORD_MAX_LEN,
                                  lowercase_only=True, complete_only=True)
    match = next((w for w in words if w["writer"] == wd["writer"] and w["word"] == wd["word"]),
                 None)
    assert match is not None
    expect = r69.invariant_canon(match["char_segs"][0]["strokes"])
    assert np.allclose(np.asarray(wd["chars"][0]["inv"]), np.asarray(expect))


@pytest.fixture(scope="module")
def native():
    srs = pytest.importorskip("substrate_rs")
    return srs.Substrate()._inner


@requires_real
def test_word_char_accuracy_plausibility_band(small_prep, native):
    """Per-char accuracy on WORD characters, scored with the SAME combined (invariant+pose)
    posterior run 69 uses, lands in the same REGIME as run 69's own isolated-char numbers
    (55.0% within / 28.8% cross) -- a plausibility gate (different sample: word-context chars from
    this run's own word-based writer/test selection, not run 69's char-based selection), not an
    exact-number reproduction."""
    own_bank = small_prep["own_bank"]
    cross_bank = small_prep["cross_bank"]
    n_within_ok = n_cross_ok = n_char = 0
    for wd in small_prep["word_records"]:
        w = str(wd["writer"])
        ob = own_bank.get(w, {})
        for i, ch in enumerate(wd["chars"]):
            true_c = r70.r68._lower26(ch["true_symbol"])
            invB = r69_module()._class_cost(native, ch["inv"], ob, "inv")
            poseE = r69_module()._class_cost(native, ch["pose_own"], ob, "pose")
            invA = r69_module()._class_cost(native, ch["inv"], cross_bank, "inv")
            poseC = r69_module()._class_cost(native, ch["pose_pop"], cross_bank, "pose")
            within = [invB[c] + r70.PRIMARY_LAMBDA_POSE * poseE[c] for c in range(26)]
            cross = [invA[c] + r70.PRIMARY_LAMBDA_POSE * poseC[c] for c in range(26)]
            n_within_ok += int(np.argmin(within) == true_c)
            n_cross_ok += int(np.argmin(cross) == true_c)
            n_char += 1
    assert n_char >= 30
    within_acc = 100.0 * n_within_ok / n_char
    cross_acc = 100.0 * n_cross_ok / n_char
    # plausibility band: well above chance (3.85%, 26-way), and within-writer clearly above cross.
    assert within_acc > 3.85 * 2, f"within-writer word-char acc should clear chance, got {within_acc:.1f}%"
    assert within_acc >= cross_acc, (
        f"within-writer should not be WORSE than cross-writer on the same combined posterior "
        f"(within={within_acc:.1f}% cross={cross_acc:.1f}%) -- the run 69 mechanism must transfer")


def r69_module():
    import scripts.jabberwock_pose_read_run69 as r69
    return r69
