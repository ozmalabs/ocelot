"""Per-resident CAN belief networks for Bigville (BIGVILLE_CAN_INTEGRATION_
PREREG.md / _RESULTS.md). Gates:

  1. the new `resolution_bins` trait is a real, mixture-drawn, integer,
     range-clamped population param, additive to bigville_cast100.json's
     existing 12-field `params` dict without perturbing them (RNG-stream
     isolation);
  2. the CAN builder (worlds/bigville_can_beliefs.py) produces a real,
     independent, individually-parameterized network per resident using
     only the existing can_ops PyO3 surface;
  3. the measured direction from BIGVILLE_CAN_INTEGRATION_RESULTS.md's live
     two-resident demonstration holds as a regression: the low-resolution
     resident's network shows higher rounding error AND higher frustration
     than the high-resolution resident's, on the identical scenario.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate_rs import _native                                        # noqa: E402
from worlds.bigville_town100_world import (                             # noqa: E402
    build_town_100, generate_cast100, SEED_DEFAULT, _RES_LO, _RES_HI,
    _draw_resolution_bins)
from worlds.bigville_can_beliefs import (                               # noqa: E402
    install_productions, build_resident_can_mt, apply_scenario_evidence,
    effective_resolution_bins, quantize_j, true_edge_j, TOPIC_NAMES,
    STRUCTURAL_EDGES)
from scripts.bigville_can_integration_demo import (                     # noqa: E402
    pick_demo_residents, run_one)

_CAST_PATH = os.path.join(_ROOT, "seeds", "bigville_cast100.json")


def _cast():
    return json.load(open(_CAST_PATH))["residents"]


# -------------------------------------------------------- G-trait-real
def test_resolution_bins_present_integer_and_in_range():
    cast = _cast()
    for r in cast:
        v = r["params"]["resolution_bins"]
        assert isinstance(v, int), "%s: resolution_bins not int: %r" % (r["name"], v)
        assert _RES_LO <= v <= _RES_HI, "%s out of range: %d" % (r["name"], v)


def test_resolution_bins_not_cloned_and_not_unimodal():
    cast = _cast()
    vals = [r["params"]["resolution_bins"] for r in cast]
    assert st.pvariance(vals) > 0.0, "resolution_bins is cloned (zero variance)"
    # mixture design: a real floor cluster AND a real (smaller) ceiling tail,
    # not one bell curve collapsed to its mean.
    floor_ct = sum(1 for v in vals if v <= 4)
    ceil_ct = sum(1 for v in vals if v >= 7)
    assert floor_ct > 30, "floor component too thin: %d" % floor_ct
    assert ceil_ct > 5, "ceiling component too thin: %d" % ceil_ct


# -------------------------------------------------------- G-existing-params-untouched
def test_new_trait_does_not_perturb_existing_12_params():
    """The resolution_bins draw uses its OWN rng stream (rrng, seed+13) --
    changing what it draws (or how many draws it consumes) must not change
    any of the pre-existing 12 _PARAM_SPEC values for ANY resident."""
    import worlds.bigville_town100_world as w

    _, _, layout = build_town_100(SEED_DEFAULT)
    baseline = generate_cast100(layout, SEED_DEFAULT)["residents"]

    orig = w._draw_resolution_bins
    try:
        w._draw_resolution_bins = lambda rng: 999  # deliberately different + out of clamp range pre-clamp
        perturbed = generate_cast100(layout, SEED_DEFAULT)["residents"]
    finally:
        w._draw_resolution_bins = orig

    assert len(baseline) == len(perturbed) == 100
    for b, p in zip(baseline, perturbed):
        bp = dict(b["params"]); bp.pop("resolution_bins", None)
        pp = dict(p["params"]); pp.pop("resolution_bins", None)
        assert bp == pp, "resident %s's existing params perturbed" % b["name"]
        assert b["role_identity"] == p["role_identity"]
        assert b["class"] == p["class"]
        assert b["literacy"] == p["literacy"]


def test_committed_seed_matches_fresh_regeneration():
    """Mirrors test_cast100_migrated.py's own gate, extended to the new
    field -- the committed bigville_cast100.json (with resolution_bins) is
    byte-identical to a fresh regeneration."""
    _, _, layout = build_town_100(SEED_DEFAULT)
    fresh = generate_cast100(layout, SEED_DEFAULT)
    onfile = json.load(open(_CAST_PATH))
    assert onfile == fresh


# -------------------------------------------------------- G-mixture-design-functions
def test_draw_resolution_bins_pure_and_clamped():
    import numpy as np
    rng = np.random.default_rng(1)
    vals = [_draw_resolution_bins(rng) for _ in range(2000)]
    assert min(vals) >= _RES_LO and max(vals) <= _RES_HI
    assert all(isinstance(v, int) for v in vals)


def test_effective_resolution_bins_trait_ceiling_and_state_fraction():
    # zero arousal -> full trait ceiling
    assert effective_resolution_bins(10, 0.0, res_gain=1.0) == 10
    # full arousal (res_gain*arousal>=1) -> floors at 2, never below
    assert effective_resolution_bins(10, 1.0, res_gain=1.0) == 2
    assert effective_resolution_bins(2, 1.0, res_gain=1.0) == 2
    # partial arousal scales down from the trait ceiling
    assert effective_resolution_bins(10, 0.5, res_gain=1.0) == 5


def test_quantize_j_vocabulary_sizes():
    # 2 bins -> only the extremes are representable
    assert quantize_j(0.1, 2) in (-1.0, 1.0)
    assert quantize_j(0.4, 2) == 1.0
    assert quantize_j(-0.4, 2) == -1.0
    # more bins -> finer resolution, small values stay small
    lv = quantize_j(0.1, 9)
    assert abs(lv - 0.1) < 0.15
    assert quantize_j(0.5, 1) == 0.0


def test_true_edge_j_bounded_and_resident_specific():
    p_a = {"mood_bias": 0.30, "w_supergraph": 0.50}    # at population mean
    p_b = {"mood_bias": 0.9, "w_supergraph": 0.9}      # far from mean
    for base_j, key in ((0.5, "mood_bias"), (-0.6, "w_supergraph")):
        ja = true_edge_j(p_a, base_j, key)
        jb = true_edge_j(p_b, base_j, key)
        assert -1.0 <= ja <= 1.0 and -1.0 <= jb <= 1.0
        assert ja == base_j                # at the mean, no nuance shift
        assert jb != base_j                 # deviates -> real per-resident nuance


# -------------------------------------------------------- G-builder-real-network
def test_builder_produces_independent_five_concept_network():
    s = _native.Substrate()
    install_productions(s)
    cast = _cast()
    built = build_resident_can_mt(s, cast[0])
    assert set(built["concepts"]) == set(TOPIC_NAMES)
    assert len(built["edges"]) == len(STRUCTURAL_EDGES)
    audit = s.mt_audit_basin(built["mt_node"])
    assert audit["concept_count"] == 5
    assert audit["coupling_count"] == 5


def test_two_residents_get_genuinely_distinct_concept_nodes():
    """Independence requires DISTINCT Concept nodes per resident (can_ops.rs
    stores state/h/identity as attrs ON the Concept node) -- confirm the
    builder does not accidentally share nodes across two residents."""
    s = _native.Substrate()
    install_productions(s)
    cast = _cast()
    b0 = build_resident_can_mt(s, cast[0])
    b1 = build_resident_can_mt(s, cast[1])
    for t in TOPIC_NAMES:
        assert b0["concepts"][t].value != b1["concepts"][t].value


# -------------------------------------------------------- G-measured-direction-holds
def test_low_resolution_resident_shows_more_rounding_error_and_more_frustration():
    """Regression on BIGVILLE_CAN_INTEGRATION_RESULTS.md's live measured
    direction: on the identical scenario, the coarse (low-resolution-bins)
    resident's network shows a higher mean rounding error (manipulation
    check) AND higher frustration (the registered prediction) than the fine
    (high-resolution-bins) resident's."""
    cast = _cast()
    lo, hi = pick_demo_residents(cast)
    assert lo["params"]["resolution_bins"] < hi["params"]["resolution_bins"]

    s = _native.Substrate()
    install_productions(s)
    r_lo = run_one(s, lo)
    r_hi = run_one(s, hi)

    assert r_lo["mean_abs_rounding_error"] > r_hi["mean_abs_rounding_error"]
    assert r_lo["single_relax_audit"]["frustration"] > r_hi["single_relax_audit"]["frustration"]
    assert r_lo["multi_start_sweep"]["mean_frustration"] > r_hi["multi_start_sweep"]["mean_frustration"]


# -------------------------------------------------------- G-no-python-decision
def test_no_python_rule_engine_in_can_beliefs_builder():
    src = open(os.path.join(_ROOT, "worlds", "bigville_can_beliefs.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "._match", "._apply"):
        assert forbidden not in src, "builder must not run a rule engine: %s" % forbidden
