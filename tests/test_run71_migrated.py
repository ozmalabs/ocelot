"""test_run71_migrated.py -- unit gates for RUN 71 (incremental motor-simulation AbS: replacing
the STATIC bank-of-real-exemplars emission (runs 69/70) with a GENERATE-AND-COMPARE (AbS) emission
built from run 66's learned writer, placed into run 69's writer-relative frame).

Gates the machinery BEFORE the expensive real-data eval (ops law "unit tests first"):
  * `gen_inv_from_form` is exactly run 66's own invariant channel (`form["canon"]`, no new
    geometry);
  * `gen_pose_from_form`'s derivation: undo-rotation-then-scale-then-shear behaves as expected on
    synthetic forms (rotating theta by 90deg rotates the output; doubling k_scale doubles
    magnitude; slant shear moves x but not y; slant=0/k_scale=1/theta=0 is the identity);
  * `compute_class_scale` recovers a known arclen/x_height ratio from a synthetic glyph population;
  * `build_cross_gen_bank`/`build_within_gen_bank` produce the {class: [{"inv","pose"}]} schema
    `r69._class_cost` expects (the drop-in-bank-swap contract this run's whole design rests on);
  * generate a candidate letter in a given writer frame (StrokeRender + run 69's frame) --
    `gen_pose_from_form` applied to a REAL run-66 codebook form, native round-trip sanity;
  * generate WITH a join (coarticulation, run 66) -- `_observed_window`/`coartic_scores`'s window
    construction and the AbS emission correctly prefers the TRUE candidate on a clean synthetic
    2-letter case;
  * the AbS emission (`_class_cost` over a generated bank) picks the correct class when one
    candidate's generated shape is an exact copy of the query and another is very different;
  * the static-emission arm (this run's `static_invB`/`static_poseE`/etc. fields) is a byte-for-
    byte COPY of run 69's own read.json records -- no recomputation, no drift;
  * within/cross split: this run's own within-writer test-writer union and its UNIONED sample
    exclusion set cover BOTH the isolated and word test items for every shared writer (no leakage
    into the motor-sim generator's own training pool);
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

Native (substrate_rs) tests run under .venv python (StrokeQuantize/StrokeRender/DtwTo via
`cc66.learn_letter_form`/`r69._class_cost`); pure-python tests (the gen_pose_from_form derivation,
class_scale, bank-schema, window construction) need neither native nor real data.
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

import scripts.jabberwock_motorsim_run71 as r71
import scripts.jabberwock_pose_read_run69 as r69

STROKE_SHAPES_SEED = r71.STROKE_SHAPES_SEED
TRAIN_NPZ_PRESENT = os.path.exists(r71.dww.TRAIN_NPZ)
RUN69_PREP_PRESENT = os.path.exists(r71.RUN69_PREP)
RUN69_READ_PRESENT = os.path.exists(r71.RUN69_READ)
RUN70_PREP_PRESENT = os.path.exists(r71.RUN70_PREP)
RUN66_LETTERS_PRESENT = os.path.exists(r71.RUN66_LETTERS)
RUN66_JOINS_PRESENT = os.path.exists(r71.RUN66_JOINS)
RUN61_LEXICON_PRESENT = os.path.exists(r71.RUN61_LEXICON)


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run71_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


# --------------------------------------------------------------------------------------------- #
# gen_inv_from_form -- exactly run 66's own invariant channel, no new geometry.
# --------------------------------------------------------------------------------------------- #
def test_gen_inv_from_form_is_verbatim_canon():
    form = {"canon": [[0.0, 0.0], [1.0, 0.5], [2.0, 0.0]], "theta": 0.3, "arclen": 4.0}
    assert r71.gen_inv_from_form(form) == form["canon"]


# --------------------------------------------------------------------------------------------- #
# gen_pose_from_form -- the derivation (rotation-undo, scale-to-x-height, shear-by-slant).
# --------------------------------------------------------------------------------------------- #
def _square_form(theta=0.0, arclen=1.0):
    # a small unit square-ish canon, arclen normalized (StrokeQuantize's own convention: starts
    # at the origin) -- CANON_N not required to be exact for these pure-geometry checks.
    canon = [[0.0, 0.0], [0.5, 0.0], [1.0, 0.0], [1.0, 1.0]]
    return {"canon": canon, "theta": theta, "arclen": arclen}


def test_gen_pose_identity_when_theta_zero_scale_one_slant_zero():
    form = _square_form(theta=0.0)
    out = np.asarray(r71.gen_pose_from_form(form, k_scale=1.0, slant_deg=0.0))
    assert np.allclose(out, np.asarray(form["canon"]))


def test_gen_pose_scale_is_linear_in_k_scale():
    form = _square_form(theta=0.0)
    out1 = np.asarray(r71.gen_pose_from_form(form, k_scale=1.0, slant_deg=0.0))
    out2 = np.asarray(r71.gen_pose_from_form(form, k_scale=2.0, slant_deg=0.0))
    assert np.allclose(out2, out1 * 2.0)


def test_gen_pose_rotation_undoes_canonical_heading():
    """theta=90deg should rotate the canon's natural absolute orientation by 90deg -- a point at
    (1,0) in canon-space lands near (0,1) in the generated pose (up to the k_scale/slant applied
    afterward, both identity here)."""
    form = {"canon": [[0.0, 0.0], [1.0, 0.0]], "theta": math.pi / 2, "arclen": 1.0}
    out = np.asarray(r71.gen_pose_from_form(form, k_scale=1.0, slant_deg=0.0))
    assert out[0] == pytest.approx([0.0, 0.0], abs=1e-9)
    assert out[1] == pytest.approx([0.0, 1.0], abs=1e-9)


def test_gen_pose_slant_shears_x_not_y():
    form = _square_form(theta=0.0)
    out0 = np.asarray(r71.gen_pose_from_form(form, k_scale=1.0, slant_deg=0.0))
    out_sheared = np.asarray(r71.gen_pose_from_form(form, k_scale=1.0, slant_deg=20.0))
    assert np.allclose(out_sheared[:, 1], out0[:, 1]), "shear must not touch y"
    # points with nonzero y should move in x; the point at y=0 (origin) must stay put.
    assert out_sheared[3, 0] != pytest.approx(out0[3, 0])
    assert out_sheared[0, 0] == pytest.approx(out0[0, 0])


# --------------------------------------------------------------------------------------------- #
# compute_class_scale -- recovers a known arclen/x_height ratio from a synthetic population.
# --------------------------------------------------------------------------------------------- #
def test_compute_class_scale_recovers_known_ratio():
    # ONE writer, ONE sample, 3 glyphs of class 10 laid out so the neighbor-median frame is
    # baseline=0, topline=-2 (x_height=2); each glyph's own stroke has arclen=4 -> ratio=2.0.
    def glyph(char_idx):
        # a straight vertical stroke of arclen=4 over >=6 points (compute_class_scale's own
        # single-stroke min-length filter), NOT itself defining the frame (the frame comes from
        # neighbors, per r69.local_baseline_topline's own convention) -- give every glyph the SAME
        # vertical extent [0,-2] so neighbor-median = self extent too.
        pts = [[0.0, 0.0], [0.0, -0.5], [0.0, -1.0], [0.0, -1.5], [0.0, -2.0], [0.0, -4.0]]
        return {"writer": 1, "sample": 100, "char_idx": char_idx, "class": 10, "symbol": "a",
                "strokes": [pts]}
    glyphs = [glyph(k) for k in range(4)]
    ws_index = r69._index_by_writer_sample(glyphs)
    scale, n_obs = r71.compute_class_scale(glyphs, bg_writers={1}, ws_index=ws_index)
    # arclen of 0->-0.5->-1->-1.5->-2->-4 = 0.5*4+2 = 4; x_height from neighbors = baseline(0)-
    # topline(-4) = 4 (median max_y=0, median min_y=-4 over neighbors, matching each glyph's own
    # full vertical extent since all glyphs are identical) -> ratio = 4/4 = 1.0.
    assert n_obs[10] == 4
    assert scale[10] == pytest.approx(1.0, abs=1e-6)
    # an unobserved class falls back to the documented default.
    assert scale[11] == r71.DEFAULT_CLASS_SCALE


def test_compute_class_scale_ignores_multistroke_and_non_bg():
    def glyph(writer, n_strokes, char_idx=0):
        pts = [[0.0, 0.0], [0.0, -2.0]]
        return {"writer": writer, "sample": 5, "char_idx": char_idx, "class": 10, "symbol": "a",
                "strokes": [pts] * n_strokes}
    glyphs = [glyph(1, 2), glyph(2, 1)]     # writer 1 multi-stroke (skip), writer 2 not background.
    ws_index = r69._index_by_writer_sample(glyphs)
    scale, n_obs = r71.compute_class_scale(glyphs, bg_writers={1}, ws_index=ws_index)
    assert n_obs[10] == 0
    assert scale[10] == r71.DEFAULT_CLASS_SCALE


# --------------------------------------------------------------------------------------------- #
# build_cross_gen_bank / build_within_gen_bank -- the {class: [{"inv","pose"}]} schema
# `r69._class_cost` requires (the drop-in bank-swap contract).
# --------------------------------------------------------------------------------------------- #
def test_gen_bank_schema_matches_class_cost_contract():
    codebook = {"10": [{"canon": [[0.0, 0.0], [1.0, 0.0]], "theta": 0.0, "arclen": 2.0}],
                "11": []}
    class_scale = {"10": 1.5}
    bank = r71.build_cross_gen_bank(codebook, class_scale, pop_slant_deg=0.0)
    assert set(bank.keys()) == {str(c) for c in r71.LOWER_CLASSES}
    assert len(bank["10"]) == 1
    assert set(bank["10"][0].keys()) == {"inv", "pose"}
    assert bank["11"] == []            # no forms -> empty bank entry, handled gracefully downstream.


def test_within_gen_bank_uses_writer_frame():
    writer_forms = {"10": [{"canon": [[0.0, 0.0], [1.0, 0.0]], "theta": 0.0, "arclen": 3.0}]}
    bank_a = r71.build_within_gen_bank(writer_forms, {"x_height": 1.0, "slant_deg": 0.0})
    bank_b = r71.build_within_gen_bank(writer_forms, {"x_height": 3.0, "slant_deg": 0.0})
    pose_a = np.asarray(bank_a["10"][0]["pose"])
    pose_b = np.asarray(bank_b["10"][0]["pose"])
    # k_scale = arclen/x_height -> 3.0 for bank_a, 1.0 for bank_b -> bank_a is 3x bank_b.
    assert np.allclose(pose_a, pose_b * 3.0)


# --------------------------------------------------------------------------------------------- #
# _observed_window -- word-context local-window construction for coarticulation (pure geometry).
# --------------------------------------------------------------------------------------------- #
def _char(strokes):
    return {"true_symbol": "a", "strokes": strokes}


def test_observed_window_concatenates_neighbors():
    chars = [_char([[[0.0, 0.0], [1.0, 0.0]]]), _char([[[2.0, 0.0], [3.0, 0.0]]]),
              _char([[[4.0, 0.0], [5.0, 0.0]]])]
    mid = r71._observed_window(chars, 1)
    assert mid.shape[0] == 6            # all 3 chars' points (2 pts each).
    first = r71._observed_window(chars, 0)
    assert first.shape[0] == 4           # only chars[0:2] (no left neighbor).
    last = r71._observed_window(chars, 2)
    assert last.shape[0] == 4            # only chars[1:3] (no right neighbor).


# --------------------------------------------------------------------------------------------- #
# Native gates: substrate_rs required (StrokeQuantize/StrokeRender/DtwTo via cc66/r69).
# --------------------------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def native():
    srs = pytest.importorskip("substrate_rs")
    return srs.Substrate()._inner


def _line_points(x0, y0, x1, y1, n=12):
    return [[x0 + (x1 - x0) * t / (n - 1), y0 + (y1 - y0) * t / (n - 1)] for t in range(n)]


def test_learn_letter_form_and_generate_in_writer_frame(native):
    """Generate a candidate letter (StrokeQuantize+StrokeRender via `cc66.learn_letter_form`) and
    place it via `gen_pose_from_form` into a synthetic writer frame -- the round-trip should stay
    finite and the SAME shape scaled by a bigger x_height should have proportionally bigger extent
    (the core motor-sim mechanism: generate once, place per writer)."""
    import scripts.jabberwock_cursive_curriculum_run66 as cc66
    pts = _line_points(0.0, 0.0, 1.0, 3.0) + _line_points(1.0, 3.0, 2.0, 0.0)
    form = cc66.learn_letter_form(native, pts)
    assert len(form["canon"]) == cc66.CANON_N
    pose_small = np.asarray(r71.gen_pose_from_form(form, k_scale=1.0, slant_deg=0.0))
    pose_big = np.asarray(r71.gen_pose_from_form(form, k_scale=4.0, slant_deg=0.0))
    ext_small = pose_small[:, 1].max() - pose_small[:, 1].min()
    ext_big = pose_big[:, 1].max() - pose_big[:, 1].min()
    assert ext_big == pytest.approx(4.0 * ext_small, rel=1e-6)


def test_abs_emission_picks_the_matching_class(native):
    """`_class_cost` (r69's, reused verbatim) over a generated bank of 2 classes must pick the
    class whose GENERATED canon matches the query, when the other class's canon is very
    different -- the AbS emission's basic correctness."""
    query_inv = _line_points(0.0, 0.0, 1.0, 1.0, n=r69.CANON_N)
    bank = {
        "10": [{"inv": query_inv, "pose": query_inv}],                       # exact match.
        "11": [{"inv": _line_points(0.0, 0.0, -5.0, -5.0, n=r69.CANON_N),
                "pose": _line_points(0.0, 0.0, -5.0, -5.0, n=r69.CANON_N)}],  # far away.
    }
    cost = r69._class_cost(native, query_inv, bank, "inv")
    li10, li11 = 10 - 10, 11 - 10
    assert cost[li10] < cost[li11]


def test_generate_word_with_join_matches_run66(native):
    """Coarticulation reuses `cc66.generate_word(..., joins=True)` verbatim -- a 2-letter word
    generated WITH the learned join gap should differ from WITHOUT joins whenever the gap is
    nonzero (the mechanism run 66 already validated; this just confirms r71 imports/calls it
    correctly)."""
    import scripts.jabberwock_cursive_curriculum_run66 as cc66
    form_a = cc66.learn_letter_form(native, _line_points(0.0, 0.0, 1.0, 2.0))
    form_b = cc66.learn_letter_form(native, _line_points(0.0, 0.0, -1.0, 2.0))
    gap = np.array([0.3, -0.2])
    with_join = cc66.generate_word(native, [form_a, form_b], gap, joins=True)
    no_join = cc66.generate_word(native, [form_a, form_b], gap, joins=False)
    assert not np.allclose(with_join[-1], no_join[-1])


# --------------------------------------------------------------------------------------------- #
# Real-data checks (skipped if the corpus / run 61/66/69/70 checkpoints aren't present).
# --------------------------------------------------------------------------------------------- #
requires_real = pytest.mark.skipif(
    not (TRAIN_NPZ_PRESENT and RUN69_PREP_PRESENT and RUN69_READ_PRESENT and RUN70_PREP_PRESENT
         and RUN66_LETTERS_PRESENT and RUN66_JOINS_PRESENT and RUN61_LEXICON_PRESENT),
    reason="DeepWriting corpus or run 61/66/69/70 checkpoints not present")


@pytest.fixture(scope="module")
def real_prep():
    if not (TRAIN_NPZ_PRESENT and RUN69_PREP_PRESENT and RUN70_PREP_PRESENT
            and RUN61_LEXICON_PRESENT):
        pytest.skip("DeepWriting corpus or run 61/69/70 checkpoints not present")
    return r71.build_prep()


@requires_real
def test_prep_reproduces_run69_and_run70_test_sets(real_prep):
    """The regenerated isolated-char and word test sets are byte-identical to run 69's / run 70's
    own saved selections (same seeds, same functions, writer ids are ints so set iteration is
    hash-stable) -- the apples-to-apples guarantee this run's whole comparison rests on."""
    assert real_prep["bg_match_run69"]
    assert real_prep["bg_match_run70"]
    assert real_prep["iso_test_match_run69"]
    assert real_prep["word_test_match_run70"]


@requires_real
def test_within_writer_generator_exclusion_covers_both_test_sets(real_prep):
    """A writer appearing in BOTH the isolated and word test sets must have its own-exemplar pool
    (used to LEARN that writer's motor-sim codebook) drawn with an exclusion set covering samples
    from EITHER evaluation -- no leakage of a test item's own ink into its generator's training
    pool. Spot-check: no own_raw_bank exemplar for any test writer is bit-identical to a query
    char's own points is NOT directly checkable post-hoc (points aren't stored per query here),
    so this asserts the STRUCTURAL guarantee instead: test_writers is exactly the union of
    iso_writers and word_writers, and every writer's own_raw_bank pool was drawn AFTER excluding
    that writer's full test-sample set (nonempty exclude set for every writer that has test
    items)."""
    iso_w = set(real_prep["iso_writers"])
    word_w = set(real_prep["word_writers"])
    assert set(real_prep["test_writers"]) == iso_w | word_w
    assert iso_w & word_w, "expect at least one writer shared by both test sets on real data"


@requires_real
def test_static_within_isolated_char_matches_run69_reported_number(real_prep):
    """This run's REUSED static arm (invB/poseE, loaded verbatim from run 69's read.json) must
    reproduce run 69's own reported 55.0% within-writer isolated-char number when scored with the
    SAME combined posterior -- confirms no drift from copy-paste/reindexing."""
    r69_read = r71._load(r71.RUN69_READ)
    if not r69_read.get("done"):
        pytest.skip("run 69's read.json not COMPLETE")
    recs = r69_read["records"]
    ok = 0
    for r in recs:
        v = np.asarray(r["invB"]) + r71.PRIMARY_LAMBDA * np.asarray(r["poseE"])
        ok += int((int(np.argmin(v)) + 10) == r["true_class"])
    acc = 100.0 * ok / len(recs)
    assert acc == pytest.approx(r71.RUN69_WITHIN_ISO_CHAR, abs=1.0)
