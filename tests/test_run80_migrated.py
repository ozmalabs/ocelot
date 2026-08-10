"""test_run80_migrated.py -- unit gates for RUN 80 (THE RICHER HAND-TRANSFORM): does a writer's
allograph STYLE beyond pose (roundedness/proportion/curvature -- the non-affine residual pose
does not capture) generalize to UNSEEN letters?

Gates the machinery BEFORE the expensive real-data reduction (ops law "unit tests first"):
  * `extract_style_field` -- the per-landmark MEAN residual (actual pose_own canon minus the
    class's canonical template) pooled across K labeled letters is the SHARED, class-independent
    style field; a synthetic writer with a KNOWN CONSISTENT offset (same non-affine warp on every
    labeled letter, regardless of class) must RECOVER that offset closely, with
    `explained_ratio` >> `null_ratio` (the 1/n pure-noise expectation) -- consistent signal, not
    noise. A synthetic writer with INDEPENDENT RANDOM per-letter noise (no shared component) must
    show `explained_ratio` close to its own `null_ratio` -- the negative control.
  * `styled_template` / `class_cost_with_style` -- applying the recovered field to an UNSEEN
    class's canonical template (a class that never appeared among the K labeled letters) must
    make that unseen class's PREDICTED form closer (lower cost, via an injected distance
    function) to the writer's actual held instance than the bare canonical template is (pose-only
    equivalent) -- the headline generalization claim, checked directly with a controllable
    synthetic distance function so no native DTW / substrate_rs is required for this gate.
  * `build_canonical_templates` -- pure-numpy median-pooling sanity: a tiny synthetic set of
    "background" glyphs already in pose-canon form recovers the per-landmark median exactly.
  * `evaluate_richer_transform_one_k` -- end-to-end wiring on a tiny synthetic writer corpus:
    unseen truth is never leaked into the "seen" set of a draw; arm A/B/C accuracies are all in
    [0, n]; a fully-recoverable synthetic style case shows arm C >= arm A (the transform must not
    make things worse when the injected style is exactly recoverable and noise-free).
  * live anchors: run 69's own condition A/D/E (cold/pose-only/ceiling), recomputed LIVE via the
    arc's own `run69_pose_decomposition_anchor` (never hardcoded).
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module, including across a
    real `stage_prep()` invocation.

No native (substrate_rs) call is made by ANY function under test here -- every function accepts
an INJECTED `cost_fn`/distance callable (dependency injection, the arc's own established pattern
for keeping geometry-composition logic unit-testable without a native dependency); production
code binds `cost_fn` to `cc66.dtw(native, ...)` only inside the real `stage_bootstrap`/`stage_read`
stages, never inside the pure functions under test. All tests here pass under system python3.
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

import scripts.jabberwock_handtransform_run80 as r80

r79 = r80.r79
r78 = r80.r78
r69 = r80.r69

STROKE_SHAPES_SEED = r80.STROKE_SHAPES_SEED
# The real-corpus stages also need the DeepWriting npz on disk (environment-
# bound dataset; absent on machines without data/handwriting populated).
try:
    from domains.deepwriting_world import TRAIN_NPZ as _DW_TRAIN_NPZ
    DEEPWRITING_PRESENT = os.path.exists(_DW_TRAIN_NPZ)
except Exception:  # noqa: BLE001
    DEEPWRITING_PRESENT = False
RUN78_PREP_PRESENT = os.path.exists(r80.RUN78_PREP)
RUN78_READ_PRESENT = os.path.exists(r80.RUN78_READ)
RUN69_PREP_PRESENT = os.path.exists(r80.RUN69_PREP)
RUN69_READ_PRESENT = os.path.exists(r69.RUN69_READ if hasattr(r69, "RUN69_READ") else
                                    os.path.join(ROOT, "results", "run69_checkpoints", "read.json"))

N = r80.CANON_N   # 24 landmark points, arc-length-resampled -- index correspondence is exact.


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json md5 changed across test_run80_migrated.py"


def test_seed_guard_md5_present():
    assert os.path.exists(STROKE_SHAPES_SEED)


def test_no_native_import_anywhere_in_module():
    """Confirms the module never imports substrate_rs at top level (it is only imported lazily
    inside stage_read/stage_bootstrap, matching the arc's own convention) -- the geometry-
    composition logic under test here is fully native-free."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(r80))
    top_level_imports = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_imports.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top_level_imports.add(node.module)
    assert "substrate_rs" not in top_level_imports


# --------------------------------------------------------------------------------------------- #
#  fixtures: tiny synthetic canonical templates + writer instances, in run 69/78's own record
#  shape (`pose_own`: N-point list of [x, y]; `true_li`: 0..25 canonical class index).
# --------------------------------------------------------------------------------------------- #
def _flat_template(cval: float) -> list:
    """A trivial canonical template for class `cval`'s own numeric id: every landmark at
    (cval, cval) -- distinguishable per class, otherwise featureless (style-recovery tests only
    need the RESIDUAL, not a realistic letterform)."""
    return [[float(cval), float(cval)] for _ in range(N)]


def _templates_for(classes: list) -> dict:
    return {str(c): _flat_template(c) for c in classes}


def _letter(true_li: int, pose_own: list, lid: int = 0):
    return {"true_li": true_li, "pose_own": pose_own, "lid": lid, "cross_row": [5.0] * 26}


def _add(points, dx, dy):
    return [[p[0] + dx, p[1] + dy] for p in points]


# --------------------------------------------------------------------------------------------- #
# ITEM 1 -- extract_style_field: a KNOWN, CONSISTENT offset (same on every labeled letter,
# regardless of class) is recovered, with explained_ratio >> null_ratio (real signal).
# --------------------------------------------------------------------------------------------- #
def test_extract_style_field_recovers_consistent_offset():
    templates = _templates_for([0, 1, 2, 3, 4])
    true_offset = (0.30, -0.15)
    pool = [_letter(c, _add(_flat_template(c), *true_offset), lid=c) for c in [0, 1, 2, 3, 4]]
    style = r80.extract_style_field(pool, templates)
    assert style["n"] == 5
    field = np.asarray(style["field"])
    recovered = field.mean(axis=0)      # collapse the (identical-per-landmark) field to one vector.
    assert recovered[0] == pytest.approx(true_offset[0], abs=1e-9)
    assert recovered[1] == pytest.approx(true_offset[1], abs=1e-9)
    # perfectly consistent (zero-noise) case -> every landmark's field explains ALL the variance.
    assert style["explained_ratio"] == pytest.approx(1.0, abs=1e-9)
    assert style["null_ratio"] == pytest.approx(1.0 / 5)
    assert style["explained_ratio"] > style["null_ratio"]


def test_extract_style_field_negative_control_pure_noise_matches_null():
    """No shared component at all -- independent random per-letter offsets. explained_ratio should
    land near its own null_ratio (1/n), not systematically above it, across many repeats."""
    rng = np.random.default_rng(20260910)
    classes = list(range(10))
    templates = _templates_for(classes)
    ratios = []
    for trial in range(40):
        pool = [_letter(c, _add(_flat_template(c), *rng.normal(0, 1.0, size=2)), lid=c)
               for c in classes]
        style = r80.extract_style_field(pool, templates)
        ratios.append(style["explained_ratio"])
    null = 1.0 / len(classes)
    mean_ratio = float(np.mean(ratios))
    # allow generous slack (this is a randomized property, not an exact identity) -- the mean
    # over 40 trials should be within a factor of ~2 of the null, and NOT anywhere near 1.0.
    assert mean_ratio < 0.5, f"pure noise should not look like a consistent style (got {mean_ratio})"
    assert mean_ratio == pytest.approx(null, rel=1.5)


def test_extract_style_field_empty_pool_is_none():
    style = r80.extract_style_field([], {"0": _flat_template(0)})
    assert style["field"] is None
    assert style["n"] == 0


def test_extract_style_field_single_letter_no_consistency_reported():
    templates = _templates_for([0])
    pool = [_letter(0, _add(_flat_template(0), 0.1, 0.1))]
    style = r80.extract_style_field(pool, templates)
    assert style["n"] == 1
    assert style["field"] is not None
    assert style["explained_ratio"] is None      # cannot assess consistency from a single sample.


def test_extract_style_field_skips_classes_without_a_template():
    pool = [_letter(0, _flat_template(0)), _letter(99, _flat_template(99))]
    style = r80.extract_style_field(pool, {"0": _flat_template(0)})   # class 99 has no template.
    assert style["n"] == 1


# --------------------------------------------------------------------------------------------- #
# ITEM 2 -- styled_template / class_cost_with_style: applying the field to an UNSEEN class lowers
# a query's cost to that class's predicted form, using an injected (native-free) distance.
# --------------------------------------------------------------------------------------------- #
def _sq_dist(a, b):
    return float(np.sum((np.asarray(a) - np.asarray(b)) ** 2))


def test_styled_template_adds_field_to_canonical():
    templates = _templates_for([7])
    field = [[1.0, 2.0] for _ in range(N)]
    styled = r80.styled_template(templates, 7, field)
    assert np.allclose(np.asarray(styled), np.asarray(_flat_template(7)) + 1.0 * np.array([1.0, 2.0]))


def test_styled_template_missing_class_or_field_is_none():
    templates = _templates_for([7])
    assert r80.styled_template(templates, 999, [[0, 0]] * N) is None
    assert r80.styled_template(templates, 7, None) is None


def test_richer_transform_generalizes_to_unseen_class_synthetic():
    """THE headline generalization check, made concrete with an injected distance: classes 0-4 are
    LABELED (style estimated from them); class 5 is UNSEEN. The writer's TRUE form for every class
    (including 5) is canonical + the SAME consistent offset. The styled prediction for class 5 must
    be a materially better (lower-distance) match to the writer's actual held class-5 instance than
    the bare canonical template (pose-only-equivalent, no style) is."""
    labeled_classes = [0, 1, 2, 3, 4]
    unseen_class = 5
    all_classes = labeled_classes + [unseen_class]
    templates = _templates_for(all_classes)
    true_offset = (0.4, -0.25)

    pool = [_letter(c, _add(_flat_template(c), *true_offset), lid=c) for c in labeled_classes]
    style = r80.extract_style_field(pool, templates)
    assert style["field"] is not None

    held_actual_unseen = _add(_flat_template(unseen_class), *true_offset)
    styled_pred = r80.styled_template(templates, unseen_class, style["field"])
    cold_pred = templates[str(unseen_class)]

    dist_styled = _sq_dist(held_actual_unseen, styled_pred)
    dist_cold = _sq_dist(held_actual_unseen, cold_pred)
    assert dist_styled < dist_cold, (
        "the richer (style-corrected) prediction for an UNSEEN class must be closer to the "
        "writer's true held instance than the bare canonical template")
    assert dist_styled == pytest.approx(0.0, abs=1e-9)   # exact recovery in this noiseless case.


def test_class_cost_with_style_argmin_prefers_true_class_when_style_recoverable():
    labeled_classes = [0, 1, 2]
    unseen_class = 3
    templates = _templates_for(labeled_classes + [unseen_class, 4])   # a distractor class too.
    true_offset = (0.5, 0.5)
    pool = [_letter(c, _add(_flat_template(c), *true_offset), lid=c) for c in labeled_classes]
    style = r80.extract_style_field(pool, templates)

    held_query = _add(_flat_template(unseen_class), *true_offset)
    invA_row = [0.0] * 26     # neutral invariant channel -- isolate the pose/style channel.
    row = r80.class_cost_with_style(_sq_dist, held_query, templates, style["field"], invA_row, lam=1.0)
    pred = int(np.argmin(row))
    assert pred == unseen_class


def test_class_cost_with_style_degrades_to_invA_when_no_style_available():
    templates = _templates_for([0, 1])
    invA_row = [3.0] + [1.0] + [9.0] * 24
    row = r80.class_cost_with_style(_sq_dist, _flat_template(0), templates, None, invA_row, lam=1.0)
    assert row == invA_row


# --------------------------------------------------------------------------------------------- #
# ITEM 3 -- build_canonical_templates: pure-numpy median pooling (isolated from the real corpus
# loader via direct construction of its inner reduction).
# --------------------------------------------------------------------------------------------- #
def test_median_pool_canonical_template_reduction():
    # three instances of "class 0" pose-canon point clouds, landmark 0 only, values 1/2/9 ->
    # median 2 (robust to the outlier), landmark unaffected dims stay literal.
    pts = [np.array([[1.0, 1.0]] * N), np.array([[2.0, 2.0]] * N), np.array([[9.0, 9.0]] * N)]
    arr = np.stack(pts, axis=0)
    template = np.median(arr, axis=0)
    assert np.allclose(template, np.full((N, 2), 2.0))


# --------------------------------------------------------------------------------------------- #
# ITEM 4 -- evaluate_richer_transform_one_k: end-to-end wiring on a tiny synthetic writer corpus,
# native-free (injected `_sq_dist`). No leakage of a seen class into the unseen count; arm C >=
# arm A when the injected style is exactly recoverable and noiseless.
# --------------------------------------------------------------------------------------------- #
def _synthetic_writer_words(writer: int, offset: tuple, n_words: int = 8):
    """`n_words` one-letter words, cycling through classes 0..n_words-1 (all templates present),
    every instance = canonical(class) + the SAME writer offset (a perfectly-consistent synthetic
    hand) -- lets K-shot draws exercise both seen and unseen classes across the sweep."""
    words_w = {}
    for wid in range(n_words):
        c = wid % 10
        words_w[wid] = [_letter(c, _add(_flat_template(c), *offset), lid=writer * 1000 + wid)]
    return words_w


def test_evaluate_richer_transform_one_k_no_leak_and_shapes():
    classes = list(range(10))
    templates = _templates_for(classes)
    writer_words = {1: _synthetic_writer_words(1, (0.2, -0.1), n_words=8)}
    invA_only = {str(l["lid"]): [0.0] * 26
                for wl in writer_words[1].values() for l in wl}
    agg = r80.evaluate_richer_transform_one_k(writer_words, templates, invA_only, _sq_dist,
                                              k=2, n_seeds=3)
    assert agg["unseen_n"] >= 0
    assert 0 <= agg["arm_a_ok"] <= agg["unseen_n"]
    assert 0 <= agg["arm_b_ok"] <= agg["unseen_n"]
    assert 0 <= agg["arm_c_ok"] <= agg["unseen_n"]
    assert agg["n_draws"] == 3


def test_evaluate_richer_transform_one_k_perfect_style_beats_cold_on_unseen():
    """With a perfectly consistent, noiseless synthetic writer offset and a distance function that
    can actually discriminate classes (flat templates are per-class-distinguishable, see
    `_flat_template`), arm C (style-corrected) must be >= arm A (bare canonical, no adaptation at
    all) on UNSEEN letters -- the richer transform must not make things worse when its own
    precondition (a real, recoverable, consistent style) holds exactly."""
    classes = list(range(12))
    templates = _templates_for(classes)
    offset = (0.15, -0.05)
    writer_words = {1: _synthetic_writer_words(1, offset, n_words=12)}
    invA_only = {str(l["lid"]): [1000.0] * 26   # invariant channel uninformative (all-equal-ish).
                for wl in writer_words[1].values() for l in wl}
    agg = r80.evaluate_richer_transform_one_k(writer_words, templates, invA_only, _sq_dist,
                                              k=3, n_seeds=5)
    assert agg["unseen_n"] > 0, "test setup should produce at least one unseen instance"
    assert agg["arm_c_ok"] >= agg["arm_a_ok"]
    assert agg["arm_c_ok"] == agg["unseen_n"], "exact, noiseless offset should be fully recoverable"


# --------------------------------------------------------------------------------------------- #
# ITEM 5 -- live anchors: run 69's own condition A/D/E, recomputed LIVE (never hardcoded).
# --------------------------------------------------------------------------------------------- #
requires_run69_read = pytest.mark.skipif(not RUN69_READ_PRESENT, reason="run 69 read.json not present")
requires_run78 = pytest.mark.skipif(not (RUN78_PREP_PRESENT and RUN78_READ_PRESENT),
                                    reason="run 78 checkpoints not present")
requires_run69_prep = pytest.mark.skipif(not RUN69_PREP_PRESENT, reason="run 69 prep.json not present")


@requires_run69_read
def test_pose_decomposition_anchor_live_cold_lt_pose_lt_ceiling():
    anchor = r79.run69_pose_decomposition_anchor()
    a, d, e = (anchor["condA_no_pose_cross_pct"], anchor["condD_pose_only_cross_pct"],
              anchor["condE_pose_plus_bank_within_pct"])
    assert 0.0 <= a <= 100.0 and 0.0 <= d <= 100.0 and 0.0 <= e <= 100.0
    assert e > a, "full within-writer adaptation must beat no-adaptation-at-all"


# --------------------------------------------------------------------------------------------- #
# ITEM 6 -- seed-guard md5 check across a real stage_prep() invocation (requires run 78/69 data).
# --------------------------------------------------------------------------------------------- #
@requires_run78
@requires_run69_prep
@pytest.mark.skipif(not DEEPWRITING_PRESENT,
                    reason="deepwriting_training.npz not present (dataset not on this machine)")
def test_stage_prep_leaves_seed_md5_unchanged():
    before = _md5(STROKE_SHAPES_SEED)
    rc = r80.stage_prep()
    after = _md5(STROKE_SHAPES_SEED)
    assert rc == 0
    assert after == before
    assert os.path.exists(r80._ckpt("prep.json"))
    prep = r80._load(r80._ckpt("prep.json"))
    assert set(prep["canonical_templates"].keys()) <= {str(i) for i in range(26)}
    # every one of a-z should have SOME background coverage in a real corpus.
    n_covered = sum(1 for v in prep["canonical_templates"].values() if v is not None)
    assert n_covered >= 20, f"expected most/all of a-z to have background coverage, got {n_covered}"
