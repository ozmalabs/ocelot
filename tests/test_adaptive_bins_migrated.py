"""tests/test_adaptive_bins_migrated.py — RUN 32 (OPTION R, "attack the bin grain") unit
gates, run BEFORE the gate script per the ops law. Covers: adaptive edges stored/read as
graph data; the pre-existing UNIFORM-count path stays byte-identical (regression guard on
the old DK); `StrokeQuantize(StrokeRender(sig)) == sig` holds under EXPLICIT adaptive edges
too (a bin-center-safe fixture, mirroring the pre-existing Rust `gate8a_round_trip_seg_and_
pose_exact` / `tests/test_render_geometry_migrated.py::
test_default_render_preserves_stroke_quantize_inverse_single_span` gates); sub-bin residual
emission recovers a KNOWN within-bin offset on a synthetic fixture; the residual-aware
distance (`domains/abs_read.py`) is a held Term (source audit, no Python argmin/argmax/score-
sort); entropy computation is correct on a synthetic bimodal distribution.

Hermetic throughout (`boot_core()` + `_isolate_seed_writes`, mirrors
`tests/test_arrangement_codebook_migrated.py`'s own established fixture) — no unit-test mint
ever lands in the real `seeds/stroke_shapes.json`."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import abs_read as ar
from domains import adaptive_bins as ab
from domains import ink_decode as ink
from domains import stroke_codebook as sc
from domains.teach import teach as _real_teach


@pytest.fixture(autouse=True)
def _isolate_seed_writes(tmp_path, monkeypatch):
    """Redirect teach() persistence to a tmp dir for every test in this file — mirrors
    tests/test_arrangement_codebook_migrated.py's own fixture exactly (same rationale: a
    unit-test mint must never land in the boot seed, seeds/stroke_shapes.json)."""
    monkeypatch.setattr(
        sc, "teach",
        lambda *a, **k: _real_teach(*a, **{**k, "seeds_dir": tmp_path}))


def _boot():
    s, ag = boot_core()
    native = s._inner
    return s, ag, native


# =============================================================================================
# 1. EDGES AS GRAPH DATA — store/read round-trip on the agent root.
# =============================================================================================
def test_edges_stored_and_read_back_as_graph_data():
    s, ag, native = _boot()
    turn_edges = [-180.0, -40.0, 20.0, 180.0]
    len_edges = [0.0, 0.2, 0.6, 1.0]
    ab.store_adaptive_edges(s, turn_edges, len_edges)
    rt_turn, rt_len = ab.read_adaptive_edges(s)
    assert rt_turn == turn_edges
    assert rt_len == len_edges


def test_read_adaptive_edges_absent_is_honest_none():
    s, ag, native = _boot()
    rt_turn, rt_len = ab.read_adaptive_edges(s)
    assert rt_turn is None and rt_len is None


# =============================================================================================
# 2. QUANTILE EDGE COMPUTATION — pure statistics, checkable against numpy directly.
# =============================================================================================
def test_compute_quantile_edges_matches_numpy_quantile_and_clamps_domain():
    values = [0.1, 0.12, 0.15, 0.5, 0.52, 0.9, 0.91, 0.95]
    edges = ab.compute_quantile_edges(values, n_bins=4, domain=(0.0, 1.0))
    assert len(edges) == 5
    assert edges[0] == 0.0 and edges[-1] == 1.0
    assert all(edges[i] < edges[i + 1] for i in range(len(edges) - 1)), "must be strictly ascending"


def test_compute_quantile_edges_degenerate_falls_back_to_uniform():
    edges = ab.compute_quantile_edges([5.0, 5.0, 5.0], n_bins=4, domain=(0.0, 1.0))
    assert edges == [0.0, 0.25, 0.5, 0.75, 1.0]


# =============================================================================================
# 2b. AMENDMENT GATES (2026-07-05, pre-registered before the re-run — the first live
#     gather-edges found a POINT MASS at turn=0.0 (four equal quantiles) and length collapsed
#     onto 1/segments exactly; the nudge-epsilon draft manufactured near-zero-width bins and
#     the first LEARN attempt exploded/hung on them): dedupe merges point-mass quantiles into
#     FEWER effective bins; the guard hard-fails on any non-strictly-increasing edge pair.
# =============================================================================================
def test_dedupe_point_mass_merges_equal_quantiles():
    """A distribution with a point mass (many values exactly equal) must yield DEDUPED edges —
    never several equal/near-equal boundaries, never epsilon-width slivers."""
    values = [0.0] * 500 + [-30.0] * 10 + [45.0] * 10       # heavy point mass at 0.0
    edges = ab.compute_quantile_edges(values, n_bins=12, domain=(-180.0, 180.0))
    assert all(edges[i + 1] > edges[i] for i in range(len(edges) - 1))
    min_width = 360.0 * ab.MIN_BIN_WIDTH_FRAC
    assert all((edges[i + 1] - edges[i]) >= min_width * 0.999 for i in range(len(edges) - 1)), \
        f"every deduped bin must be at least min_width wide, got {edges}"
    assert len(edges) - 1 < 12, "point-mass quantiles must MERGE into fewer effective bins"


def test_dedupe_reproduces_the_live_degenerate_turn_case():
    """The EXACT shape the first live gather-edges produced (four consecutive 0.0 quantiles)
    must come out deduped and strictly increasing."""
    import numpy as np
    rng = np.random.default_rng(1)
    # ~40% of segments locally straight (exactly 0.0), the rest spread over gentle turns.
    values = ([0.0] * 4000
              + list(rng.normal(-12.0, 14.0, 3000))
              + list(rng.normal(10.0, 12.0, 3000)))
    edges = ab.compute_quantile_edges(values, n_bins=12, domain=(-180.0, 180.0))
    assert all(edges[i + 1] > edges[i] for i in range(len(edges) - 1))
    assert edges[0] == -180.0 and edges[-1] == 180.0
    assert edges.count(0.0) <= 1, "the 0.0 point mass must contribute at most ONE edge"


def test_length_dimension_dead_by_construction_yields_few_bins_and_zero_entropy():
    """Equal-arc resampling makes per-segment length == 1/segments BY CONSTRUCTION — the
    amendment keeps the dimension (never silently dropped) with its deduped ~2-3 effective
    bins, and the occupancy report records ~0 bits as the falsifiable evidence."""
    values = [0.125] * 10000 + [0.1249] * 50 + [0.1251] * 50    # 1/8 point mass + jitter
    edges = ab.compute_quantile_edges(values, n_bins=6, domain=(0.0, 1.0))
    assert all(edges[i + 1] > edges[i] for i in range(len(edges) - 1))
    assert len(edges) - 1 <= 3, f"point-mass length must dedupe to <=3 effective bins, got {edges}"
    occ = ab.bin_occupancy(values, edges)
    assert occ["entropy_bits"] < 0.2, (
        f"the dead-by-construction length dimension must REPORT ~0 bits, got {occ}")


def test_assert_strictly_increasing_hard_fails():
    with pytest.raises(ab.DegenerateEdgesError):
        ab._assert_strictly_increasing([0.0, 0.5, 0.5, 1.0])
    with pytest.raises(ab.DegenerateEdgesError):
        ab._assert_strictly_increasing([0.0, 0.7, 0.4, 1.0])
    ab._assert_strictly_increasing([0.0, 0.5, 1.0])            # no raise


def test_bin_occupancy_counts_and_entropy_on_spread_distribution():
    edges = [0.0, 0.25, 0.5, 0.75, 1.0]
    values = [0.1] * 25 + [0.3] * 25 + [0.6] * 25 + [0.9] * 25
    occ = ab.bin_occupancy(values, edges)
    assert occ["counts"] == {"0": 25, "1": 25, "2": 25, "3": 25}
    assert abs(occ["entropy_bits"] - 2.0) < 1e-9


# =============================================================================================
# 3. UNIFORM PATH STAYS BYTE-IDENTICAL — regression guard on the OLD (pre-run-32) DK. Pinned
#    reference values computed directly from the documented uniform formulas
#    (quantize_signed_angle / quantize_bucket) -- turn 90 degrees, len fraction fixed.
# =============================================================================================
def test_uniform_count_path_byte_identical_no_edges_no_residual():
    s, ag, native = _boot()
    pts = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]
    q = sc._quantize(native, pts, segments=2, turn_bins=16, len_bins=8, grid=8, scale_bins=8,
                      canonical_pose=True)
    assert "residuals" not in q, "residuals key must be absent when emit_residual is not requested"
    sig = [list(r) for r in q["signature"]]
    # seg 0: turn_q always 0 by StrokeQuantize's own convention; seg 1: a clean +90 degree
    # turn at turn_bins=16 (22.5 deg/bin) quantizes to bin +4 (4*22.5==90.0 exactly).
    assert sig[0][:4] == ["seg", 0, 0, 4]
    assert sig[1][:4] == ["seg", 1, 4, 4]


def test_dk_default_stroke_codebook_bins_unchanged():
    """The pre-existing DEFAULT_TURN_BINS/DEFAULT_LEN_BINS constants themselves must not have
    moved — RUN 32 is additive (new opt-in params), never a change to the existing defaults."""
    assert sc.DEFAULT_TURN_BINS == 16
    assert sc.DEFAULT_LEN_BINS == 8


# =============================================================================================
# 4. EXACT-INVERSE UNDER ADAPTIVE EDGES — StrokeQuantize(StrokeRender(sig)) == sig, the SAME
#    standing gate (test_render_geometry_migrated.py / strokes.rs's gate8a), now under
#    EXPLICIT turn_edges/len_edges instead of a uniform bin count.
# =============================================================================================
def test_exact_inverse_holds_under_adaptive_edges():
    s, ag, native = _boot()
    turn_edges = [-180.0, -60.0, 60.0, 180.0]
    len_edges = [0.0, 0.3, 0.7, 1.0]
    # A bin-center-safe fixture (mirrors strokes.rs's own gate8a fixture discipline): two
    # segments, turn_q=2 (bin [60,180), center 120) then a length fraction that is EQUAL
    # across segments and sums to 1.0 (the round-trip gate's own documented precondition).
    sig = [["seg", 0, 0, 1], ["seg", 1, 2, 1]]
    rendered = native.evaluate({
        "type": "StrokeRender", "signature": {"type": "Lit", "value": sig},
        "n_points": 3, "apply_pose": False, "turn_bins": 16, "len_bins": 8, "grid": 8,
        "scale_bins": 8,
        "turn_edges": {"type": "Lit", "value": turn_edges},
        "len_edges": {"type": "Lit", "value": len_edges},
    }, {})
    requant = sc._quantize(native, rendered["points"], segments=2, turn_bins=16, len_bins=8,
                            grid=8, scale_bins=8, invariant_only=True,
                            turn_edges=turn_edges, len_edges=len_edges)
    got = [list(r) for r in requant["signature"]]
    assert got == sig, f"StrokeQuantize(StrokeRender(sig)) must recover sig EXACTLY under adaptive edges, got {got}"


def test_adaptive_edges_absent_falls_through_to_uniform_on_render_too():
    """Sanity: StrokeRender with turn_edges/len_edges omitted behaves identically to before
    RUN 32 (no accidental default-path change from adding the new fields)."""
    s, ag, native = _boot()
    sig = [["seg", 0, 0, 4], ["seg", 1, 4, 4]]
    r1 = native.evaluate({"type": "StrokeRender", "signature": {"type": "Lit", "value": sig},
                          "n_points": 3, "apply_pose": False, "turn_bins": 16, "len_bins": 8,
                          "grid": 8, "scale_bins": 8}, {})
    r2 = native.evaluate({"type": "StrokeRender", "signature": {"type": "Lit", "value": sig},
                          "n_points": 3, "apply_pose": False, "turn_bins": 16, "len_bins": 8,
                          "grid": 8, "scale_bins": 8, "turn_edges": None, "len_edges": None}, {})
    assert r1["points"] == r2["points"]


# =============================================================================================
# 5. SUB-BIN RESIDUAL — synthetic KNOWN within-bin offset must be recovered.
# =============================================================================================
def test_residual_recovers_known_offset_uniform_bins():
    s, ag, native = _boot()
    # turn_bins=16 -> bin width 22.5 deg, bin center for q=4 is exactly 90.0. Render a
    # signature at that EXACT center (residual 0 expected), then hand-perturb the resulting
    # points is unnecessary -- instead directly probe a KNOWN raw value via a bins=1 call
    # (adaptive_bins._raw_span_values' own mechanism) against a stroke whose actual turn is
    # deliberately OFFSET from a bin center by a known amount.
    # A right-angle-ish path: first leg along +x, second leg turned by 100 degrees (10 degrees
    # off the nearest 16-bin center at 90/112.5).
    import numpy as np
    theta = math.radians(100.0)
    pts = [[0.0, 0.0], [1.0, 0.0], [1.0 + math.cos(theta), math.sin(theta)]]
    q = sc._quantize(native, pts, segments=2, turn_bins=16, len_bins=8, grid=8, scale_bins=8,
                      invariant_only=True, emit_residual=True)
    residuals = {int(r[0]): (float(r[1]), float(r[2])) for r in q["residuals"]}
    sig = {int(r[1]): (int(r[2]), int(r[3])) for r in [list(x) for x in q["signature"]]}
    turn_q = sig[1][0]
    bin_width = 360.0 / 16
    expected_center = turn_q * bin_width
    expected_residual = 100.0 - expected_center
    got_residual = residuals[1][0]
    assert abs(got_residual - expected_residual) < 1e-6, (got_residual, expected_residual)


def test_raw_span_values_recovers_known_turn_and_length():
    s, ag, native = _boot()
    theta = math.radians(37.0)
    pts = [[0.0, 0.0], [2.0, 0.0], [2.0 + 2 * math.cos(theta), 2 * math.sin(theta)]]
    vals = ab._raw_span_values(native, pts, segments=2)
    # segment 0: turn always 0 by convention; segment 1: turn == 37 degrees, len frac == 0.5
    # (two equal-length legs).
    by_i = {i: (t, l) for (i, t, l) in vals}
    assert abs(by_i[0][1] - 0.5) < 1e-6
    assert abs(by_i[1][0] - 37.0) < 1e-4
    assert abs(by_i[1][1] - 0.5) < 1e-6


# =============================================================================================
# 6. RESIDUAL-AWARE DISTANCE IS A HELD TERM — source audit (no Python min/max/argmin/argmax/
#    score-sort in abs_read.py, the SAME audit test_abs_read_no_python_decisions already runs)
#    plus a correctness check of the Term's own arithmetic.
# =============================================================================================
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)


def test_residual_distance_term_source_is_a_held_term_not_python_math():
    src = Path(ar.__file__).read_text()
    assert "_residual_distance_term" in src
    assert not _BANNED_CALL_RE.search(src)
    # The function itself must build a Sum/Minus/Times Term dict, not compute with raw floats.
    fn_src = src[src.index("def _residual_distance_term"):]
    fn_src = fn_src[:fn_src.index("\ndef ", 1)]
    assert '"type": "Sum"' in fn_src
    assert '"type": "Minus"' in fn_src
    assert '"type": "Times"' in fn_src


def test_residual_aware_distance_computes_sum_of_squared_offsets():
    s, ag, native = _boot()
    query = [[1.0, 2.0], [3.0, -1.0]]
    exemplar = [[1.5, 2.0], [3.0, -2.0]]
    got = ar.residual_aware_distance(native, query, exemplar)
    expected = (1.0 - 1.5) ** 2 + (2.0 - 2.0) ** 2 + (3.0 - 3.0) ** 2 + (-1.0 - -2.0) ** 2
    assert abs(got - expected) < 1e-9


def test_propose_top_k_byte_identical_when_residuals_omitted():
    s, ag, native = _boot()
    query_sig = [["a", 1], ["b", 2]]
    exemplars = [[["a", 1]], [["a", 1], ["b", 2]], [["b", 2]]]
    without = ar.propose_top_k(native, query_sig, exemplars, k=3)
    with_none = ar.propose_top_k(native, query_sig, exemplars, k=3,
                                  query_residuals=None, exemplar_residuals=None)
    assert without == with_none


# =============================================================================================
# 7. ENTROPY — correct on a synthetic bimodal (and degenerate) distribution.
# =============================================================================================
def test_entropy_bits_single_family_collapse_is_zero():
    """The run-28 finding, reproduced synthetically: 10,230/10,231 (effectively ALL) spans in
    ONE family -> H == 0.0 bits."""
    hist = {"only_family": 10231}
    assert ab.shannon_entropy_bits(hist) == 0.0


def test_entropy_bits_bimodal_50_50_is_one_bit():
    hist = {"a": 500, "b": 500}
    got = ab.shannon_entropy_bits(hist)
    assert abs(got - 1.0) < 1e-9


def test_entropy_bits_uniform_four_way_is_two_bits():
    hist = {"a": 25, "b": 25, "c": 25, "d": 25}
    got = ab.shannon_entropy_bits(hist)
    assert abs(got - 2.0) < 1e-9


def test_entropy_report_matches_manual_shannon_formula():
    families = ["x"] * 90 + ["y"] * 9 + ["z"] * 1
    report = ab.entropy_report(families)
    total = 100
    manual = -sum((c / total) * math.log2(c / total) for c in (90, 9, 1))
    assert abs(report["entropy_bits"] - manual) < 1e-9
    assert report["n_families"] == 3
    assert report["n_observations"] == 100
    assert abs(report["top_family_share"] - 0.9) < 1e-9


def test_family_histogram_ignores_none():
    hist = ab.family_histogram(["a", None, "a", "b", None])
    assert hist == {"a": 2, "b": 1}


# =============================================================================================
# 8. GATHER / COMPUTE ADAPTIVE EDGES END-TO-END — a small synthetic LEARN population (no real
#    Omniglot data needed for a unit gate): spread turn/length values so the quantile edges
#    are provably non-uniform.
# =============================================================================================
def test_compute_adaptive_edges_end_to_end_on_synthetic_learn_population():
    s, ag, native = _boot()
    # A population of tiny straight-ish 2-segment strokes clustered around a turn of ~5
    # degrees and a length fraction of ~0.5 -- overwhelmingly NOT spread across the full
    # (-180,180]/[0,1) uniform range, mirroring the real-ink calibration finding.
    import numpy as np
    rng = np.random.default_rng(0)
    strokes = []
    for _ in range(60):
        theta = math.radians(5.0 + rng.normal(0, 1.0))
        strokes.append([[0.0, 0.0], [1.0, 0.0], [1.0 + math.cos(theta), math.sin(theta)]])
    learn_values = ab.gather_learn_span_values(s, strokes, segments=2)
    assert learn_values["n_strokes"] == 60
    assert len(learn_values["turn"]) == 60          # seg 0 excluded, seg 1 included once/stroke
    assert len(learn_values["len"]) == 120           # both segments' lengths included

    report = ab.compute_adaptive_edges(learn_values, turn_bins=4, len_bins=4)
    assert report["turn_edges"][0] == -180.0 and report["turn_edges"][-1] == 180.0
    assert report["len_edges"][0] == 0.0 and report["len_edges"][-1] == 1.0
    # UNIFORM edges would be evenly spaced (90 deg apart over 4 bins); the quantile edges
    # over this tightly-clustered-near-5-degrees population must NOT be evenly spaced --
    # the whole point of the lever.
    uniform_turn = [-180.0, -90.0, 0.0, 90.0, 180.0]
    assert report["turn_edges"] != uniform_turn
