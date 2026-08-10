"""tests/test_novelty_threshold_migrated.py — RUN 28 LEVER 1 gates: calibrated novelty (CFAR)
on `domains/ink_decode.py`'s DTW near-miss fallback tier (`domains/novelty_calibration.py`).
Hermetic, synthetic ink only (`glyph_motor_world._sample_stroke`), the SAME live-geometry
precedent `tests/test_ink_decode_migrated.py`/`tests/test_homework_characters_migrated.py` use
— no dataset.

FIXTURE NOTE (found empirically while building this suite, worth recording): with the default
`homework_loop._default_dk()` span settings (`min_span=2`), a single stroke's own greedy
Viterbi lattice search shreds it into many tiny 2-knot sub-spans that trivially exact-match
ANY straight-line family (2 raw points are geometrically straight by construction, regardless
of the stroke's true overall curvature) — a real, PRE-EXISTING property of the segmentation
lattice, not something this lever changes, but one that makes the DTW-fallback tier
unreachable in a naive single-family test fixture. Every test below forces `min_span ==
max_span == max_knots` (mirrors `test_homework_characters_migrated.py::_corner_char_fixture`'s
own established technique for controlling segmentation) so a whole synthetic stroke is decoded
as ONE span, genuinely exercising the fine -> mid -> coarse -> dtw ladder on its own overall
shape.

THE WALL (runs 26/27): `_dtw_fallback`'s accept/reject threshold was a single hard-coded
constant (`stroke_codebook.DEFAULT_DTW_THRESHOLD = 0.15`), calibrated once against synthetic
jitter, never against the REAL distribution of in-family continuous distances — so reading
real held-out Omniglot ink never minted once across 6 full cycles. This suite proves the fix
(`domains/novelty_calibration.calibrate_dtw_thresholds`) makes the threshold GRAPH DATA (gate
3), derived from a real measured population, WITHOUT ever rejecting the mastered material it
was calibrated from (gate 1 — the false-novelty regression, a FORMAL guarantee by construction:
threshold = max(observed) + margin >= every observed distance), while a genuinely novel shape
still mints (gate 2)."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import glyph_motor_world as gmw
from domains import homework_loop as hl
from domains import ink_decode as ink
from domains import novelty_calibration as nc
from domains import reflective_faculty as rf
from domains import stroke_codebook as sc
from domains.teach import teach as _real_teach

N_KNOTS = 24


@pytest.fixture(autouse=True)
def _isolate_seed_writes(tmp_path, monkeypatch):
    """Redirect teach() persistence to a tmp dir — this suite's mints must never land in
    the boot seed (seeds/stroke_shapes.json); the live graph install is unaffected. Belt-
    and-suspenders alongside the session-wide conftest.py guard (mirrors
    test_arrangement_codebook_migrated.py's own established fixture)."""
    monkeypatch.setattr(
        sc, "teach",
        lambda *a, **k: _real_teach(*a, **{**k, "seeds_dir": tmp_path}))


def _boot():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _dk() -> dict:
    """Forces WHOLE-STROKE single-span decoding (see module docstring's fixture note) --
    `min_span == max_span == max_knots` so the lattice cannot shred a stroke into trivially-
    matching micro-spans, genuinely exercising fine/mid/coarse/dtw on the stroke's own shape."""
    dk = hl._default_dk()
    dk.update(min_span=N_KNOTS, max_span=N_KNOTS, max_knots=N_KNOTS)
    return dk


def _build_line_codebook(s):
    sc.build_stroke_codebook(
        s, sources=[("I_0", gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], N_KNOTS).tolist())],
        include_pickle=False)


def _line_family(n: int, *, seed: int, std: float = 0.01) -> list:
    """`n` jittered near-duplicates of ONE canonical horizontal line -- the synthetic
    "in-family" population LEVER 1 calibrates against."""
    rng = np.random.default_rng(seed)
    base = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], N_KNOTS)
    return [(base + rng.normal(0.0, std, size=base.shape)).tolist() for _ in range(n)]


def _zigzag_stroke() -> list:
    """A single pen-stroke, four alternating steep lines (a W shape) -- the gate-2 "genuinely
    novel" fixture, chosen by MEASURED geometry (recorded here so the choice is reproducible,
    not folklore): its invariant-prototype DtwTo distance to the straight-line prototype is
    ~0.36, ABOVE every calibrated in-family threshold this suite's populations produce
    (~0.15-0.26), and its sharp direction reversals fail the COARSE grain too (large
    per-segment turn bins), so it genuinely reaches the DTW-fallback tier and rejects. Two
    fixtures that do NOT work, measured en route (kept as the honest record): a 90-degree
    CORNER sits at DtwTo ~0.19 to a line -- INSIDE the honestly-calibrated in-family band
    (~0.25 at jitter std 0.01), a true near-miss, not novelty; a smooth 300-degree ARC never
    reaches the DTW tier at all (per-segment turn ~27 deg quantizes to 0 at the 6-bin coarse
    grain -- the pre-existing "tolerance = coarseness" ladder absorbs it, a separate,
    out-of-scope generosity lever 1 deliberately does not touch)."""
    segs = [gmw._sample_stroke("line", [0.0, 0.0, 0.25, 1.0], N_KNOTS // 4),
            gmw._sample_stroke("line", [0.25, 1.0, 0.5, 0.0], N_KNOTS // 4),
            gmw._sample_stroke("line", [0.5, 0.0, 0.75, 1.0], N_KNOTS // 4),
            gmw._sample_stroke("line", [0.75, 1.0, 1.0, 0.0], N_KNOTS // 4)]
    return np.concatenate(segs, axis=0).tolist()


def _decode_and_count_mints(s, points_list: list, dk: dict) -> int:
    """Mechanical: decode every stroke, sum the OOV mint count `decode_ink` itself already
    reports (`len(res['minted'])`) -- the SAME field `homework_loop.MarkedItem.n_mints_reading`
    is built from, so this test measures exactly what the run-28 gate script measures."""
    total = 0
    for points in points_list:
        ink_node = ink.ingest_ink(s, points, max_knots=dk["max_knots"])
        res = ink.decode_ink(s, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                              segments=dk["segments"], turn_bins=dk["turn_bins"],
                              len_bins=dk["len_bins"], grid=dk["grid"],
                              scale_bins=dk["scale_bins"])
        total += len(res.get("minted", []))
    return total


# ===========================================================================
# Gate 3: the threshold LIVES IN THE GRAPH, not a Python constant.
# ===========================================================================
def test_calibration_writes_a_per_family_threshold_as_graph_data():
    s, ag, native = _boot()
    dk = _dk()
    _build_line_codebook(s)

    # CORRECTED SCOPE (the run-28 coordinator's own anomaly fix, see the module docstring's
    # SCOPE section): EVERY accepted span at ANY tier is measured against its matched family's
    # prototype -- 300 whole-stroke decodes therefore yield ~300 in-family observations,
    # comfortably clearing min_family_samples=5.
    report = nc.calibrate_dtw_thresholds(s, _line_family(300, seed=1), dk, min_family_samples=5)

    assert report["calibrated_families"], (
        f"expected at least one per-family calibration; per_family={report['per_family']!r}")
    family = report["calibrated_families"][0]
    node = sc._find_stroke_node(s, family)
    assert node is not None
    stored = s.node(node)["attrs"].get("dtw_reject_threshold")
    assert stored is not None, "the calibrated threshold must be READABLE graph data"
    assert stored == pytest.approx(report["per_family"][family]["threshold"])

    # It is GRAPH DATA, not a Python constant: mutating the attr changes what the decode
    # pipeline's own threshold-resolution helper reads back.
    ag_node = rf._agent_root_node(s)
    s.set_attr(node, "dtw_reject_threshold", 0.777)
    assert ink._resolve_dtw_threshold(s, ag_node, family) == pytest.approx(0.777)


def test_data_starved_family_pools_into_global_threshold():
    s, ag, native = _boot()
    dk = _dk()
    _build_line_codebook(s)

    # A small population (n=50 -> ~50 accepted-span observations) below a deliberately
    # generous min_family_samples=100 -- forces pooling.
    report = nc.calibrate_dtw_thresholds(s, _line_family(50, seed=2), dk,
                                          min_family_samples=100)

    assert not report["calibrated_families"], "must NOT support a per-family threshold here"
    assert report["pooled_families"], "the data-starved family must be reported as pooled"
    assert report["global"] is not None
    ag_node = rf._agent_root_node(s)
    at = s.node(ag_node)["attrs"]
    assert at.get("dtw_near_threshold_calibrated") == pytest.approx(report["global"]["threshold"])


def test_calibration_formula_reports_p95_but_never_applies_it():
    s, ag, native = _boot()
    dk = _dk()
    _build_line_codebook(s)
    report = nc.calibrate_dtw_thresholds(s, _line_family(300, seed=3), dk, min_family_samples=5)
    assert report["calibrated_families"]
    family = report["calibrated_families"][0]
    stats = report["per_family"][family]
    assert stats["p95"] <= stats["max"] + 1e-9
    applied = stats["threshold"]
    assert applied == pytest.approx(stats["max"] + report["margin"])
    assert applied != pytest.approx(stats["p95"]), (
        "the APPLIED threshold must be the pre-registered max+margin formula, not p95+margin "
        "(p95 is reported for transparency only)")


# ===========================================================================
# Gate 1 — FALSE-NOVELTY REGRESSION: mastered material stays recognized, zero new mints.
# ===========================================================================
def test_calibration_does_not_regress_mastered_material():
    s, ag, native = _boot()
    dk = _dk()
    _build_line_codebook(s)

    calibration_pool = _line_family(300, seed=10)
    report = nc.calibrate_dtw_thresholds(s, calibration_pool, dk, min_family_samples=5)
    assert report["calibrated_families"], "sanity: this family must have calibrated"

    # A FRESH draw from the SAME in-family distribution (never seen by calibration itself) --
    # the mastered-material replay this gate's own contract is about.
    fresh_in_family = _line_family(60, seed=11)
    n_mints = _decode_and_count_mints(s, fresh_in_family, dk)
    assert n_mints == 0, (
        "calibrating the DTW threshold from real in-family data must NEVER cause the SAME "
        "family's own already-mastered material to be rejected as novel — the max+margin "
        "formula is chosen precisely so every future in-distribution observation stays "
        "under threshold")

    # Round-trip self-consistency (render -> re-decode) also stays saturated -- the SAME
    # ~99%-style check run 26/27's own marking-set contract used, replayed here hermetically.
    marked = hl.mark(s, [{"id": i, "class_id": "I", "points": pts}
                         for i, pts in enumerate(fresh_in_family)], dk=dk)
    mean_score = float(np.mean([m.round_trip_score for m in marked]))
    assert mean_score > 0.9, f"mastered-material round trip regressed to {mean_score:.4f}"


# ===========================================================================
# Gate 2 — a synthetic genuinely-novel stroke, outside the family's threshold, MINTS.
# ===========================================================================
def test_genuinely_novel_shape_mints_after_calibration():
    s, ag, native = _boot()
    dk = _dk()
    _build_line_codebook(s)
    report = nc.calibrate_dtw_thresholds(s, _line_family(300, seed=20), dk, min_family_samples=5)
    assert report["calibrated_families"], "sanity: calibration must have applied"

    n_mints = _decode_and_count_mints(s, [_zigzag_stroke()], dk)
    assert n_mints >= 1, (
        "a zigzag (fails every grain AND sits beyond the calibrated in-family DTW band) must "
        "mint after calibration -- calibration must never make novelty detection WORSE")


# ===========================================================================
# Gate 3b — the calibrated value (not the hardcoded constant) is what the held Lt Term reads,
# verified at its own decision boundary (robust regardless of whether the calibrated value
# happens to land above or below the legacy constant for a given synthetic population).
# ===========================================================================
def test_calibrated_threshold_governs_the_held_lt_boundary():
    s, ag, native = _boot()
    dk = _dk()
    _build_line_codebook(s)
    report = nc.calibrate_dtw_thresholds(s, _line_family(300, seed=30), dk, min_family_samples=5)
    family = report["calibrated_families"][0]
    threshold = report["per_family"][family]["threshold"]

    ag_node = rf._agent_root_node(s)
    resolved = ink._resolve_dtw_threshold(s, ag_node, family)
    assert resolved == pytest.approx(threshold)

    eps = 1e-6
    accept = bool(native.evaluate(
        {"type": "Lt", "a": {"type": "Lit", "value": threshold - eps},
         "b": {"type": "Lit", "value": resolved}}, {}))
    reject = bool(native.evaluate(
        {"type": "Lt", "a": {"type": "Lit", "value": threshold + eps},
         "b": {"type": "Lit", "value": resolved}}, {}))
    assert accept is True, "a distance just BELOW the calibrated threshold must be accepted"
    assert reject is False, "a distance just ABOVE the calibrated threshold must be rejected"


# ===========================================================================
# Gate — EMPTY CALIBRATION IS A HARD FAILURE (the run-28 anomaly-found-and-fixed: the first
# live calibrate invocation measured n_spans=0 under a since-corrected dtw-tier-only scope and
# SILENTLY passed, leaving both arms running with the lever inert — structurally impossible
# to repeat unnoticed now).
# ===========================================================================
def test_empty_calibration_raises_never_silently_passes():
    s, ag, native = _boot()
    dk = _dk()
    _build_line_codebook(s)
    with pytest.raises(nc.EmptyCalibrationError):
        nc.calibrate_dtw_thresholds(s, [], dk)          # zero sources -> zero observations.

    # The deliberate escape hatch for tests of the failure mode itself stays available and
    # reports the emptiness honestly.
    report = nc.calibrate_dtw_thresholds(s, [], dk, fail_on_empty=False)
    assert report["n_spans_measured"] == 0 and report["n_families"] == 0
    assert report["global"] is None and not report["calibrated_families"]


# ===========================================================================
# Gate — no-Python-decision source audit (mirrors test_homework_loop_migrated.py's own
# test_homework_loop_no_python_decisions exactly, applied to the new module).
# ===========================================================================
def test_novelty_calibration_no_python_decisions():
    src = Path(nc.__file__).read_text()
    banned = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
    minmax_key = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
    assert not banned.search(src), (
        "novelty_calibration.py must not call argmin/argmax in Python -- the threshold is a "
        "fixed formula (max+margin) over an already-collected list, never a ranking decision")
    assert not minmax_key.search(src)
    bare_list_isinstance = re.compile(r"isinstance\([^,]+,\s*list\s*\)")
    assert not bare_list_isinstance.search(src), (
        f"bare isinstance(..., list) found (must accept tuples too): "
        f"{bare_list_isinstance.search(src).group(0)!r}")
