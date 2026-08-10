"""SHIP THE LINEAR EYE — the block 195000 gate (manifold-gate, NOT byte-identity).

Self-contained: every fact this pins is recomputed here. Prereg:
`EYE_BINDING_PROJECTION_PREREG.md`. Pins, in order:

  * the FIX WIRING — the eye's `binding_projection` context option is DEFAULT ON,
    and the expensive scheduler rule is projectable to `["area"]`;
  * the OBSERVABLE-MANIFOLD gate — OFF ≡ ON on the onset signature, the carve
    polygon set, `area.effort`, and every eye node-type count, across scales AND
    on the landed 160x120 Doom carve crop (this is the gate; NOT graph_to_dict
    byte-identity, which fails on non-observable edge-order scatter);
  * the WORK-COUNT reduction — `term_eval:Attr` exponent OFF ~1.8 -> ON ~1.0;
  * the UNSOUND-PROJECTION falsifier — empty-var projection MUST break an
    observable (non-vacuity);
  * the NON-OBSERVABLE-SCATTER identification — the graph_to_dict OFF/ON diff is
    edge-INSERTION-ORDER only (raw md5 differs; node/edge SETS identical; sorted
    forms identical) — the evidence the manifold-gate is sound, not a loophole;
  * C1 — the OFF path is the committed (pre-fix) oracle.
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)


def _has_flag():
    import substrate_rs as srs
    return hasattr(srs.Substrate()._inner, "set_binding_projection")


needs_engine = pytest.mark.skipif(
    not _has_flag(), reason="engine has no block-188000 binding_projection (rebuild)")

M = pytest.importorskip("scripts.eye_binding_projection_measure")


# ------------------------------------------------------------ fix wiring ------
@needs_engine
def test_eye_defaults_binding_projection_on():
    """The shipped eye turns the flag ON by default; the option opts OUT."""
    from domains.photon_eye import GraphEye
    ctx = {"retina_2d": True, "visual_carve": True}
    assert GraphEye(n_az=10, n_el=8, context=ctx).build()._binding_projection is True
    off = GraphEye(n_az=10, n_el=8,
                   context=dict(ctx, binding_projection=False)).build()
    assert off._binding_projection is False


@needs_engine
def test_expensive_rule_is_projectable_to_area():
    """The rule this rung defeats binds `task` but references it NOWHERE — so it
    projects to `["area"]`. (The same fact 188000's gate pins; re-pinned here.)"""
    from domains.photon_eye import GraphEye
    eye = GraphEye(n_az=10, n_el=8,
                   context={"retina_2d": True, "visual_carve": True}).build()
    rules = dict((r[0], r[2]) for r in eye.substrate._inner.projectable_rules())
    assert "ct_area_effort_tracks_live_salience" in rules
    assert rules["ct_area_effort_tracks_live_salience"] == ["area"]


# --------------------------------------------------- observable-manifold ------
@needs_engine
def test_manifold_identical_off_equals_on_across_scales_and_doom_crop():
    """THE GATE. OFF ≡ ON on onset sig + carve polygons + area.effort + node
    counts, across >=3 bar scales AND the 160x120 Doom carve crop."""
    rep = M.manifold_gate()
    assert len(rep["rows"]) >= 4
    doom = [r for r in rep["rows"] if r["workload"] == "doom_carve_160x120"][0]
    assert doom["n_polys"] >= 1, "Doom carve crop must produce polygons (non-vacuous)"
    assert doom["n_onsets"] > 0
    for row in rep["rows"]:
        assert row["identical"], f"MANIFOLD DIVERGES on {row['workload']}"
    assert rep["all_identical"]


# ------------------------------------------------------------ work-count ------
@needs_engine
def test_work_count_exponent_drops_from_quadratic_to_linear():
    """`term_eval:Attr` (complete work count) exponent OFF ~1.8 -> ON ~1.0, with
    onsets identical at every scale and a wall-clock corroboration."""
    rep = M.work_count()
    assert rep["onsets_identical"], "onsets must match OFF vs ON"
    off_e = rep["off"]["exp_term_eval_Attr"]
    on_e = rep["on"]["exp_term_eval_Attr"]
    assert off_e > 1.5, f"OFF term_eval:Attr exp should be super-linear, got {off_e}"
    assert on_e < 1.2, f"ON term_eval:Attr exp should be ~linear, got {on_e}"
    assert on_e < off_e - 0.4
    # cand_enum (the INCOMPLETE count) is ~linear in BOTH arms — the point.
    assert rep["off"]["exp_cand_enum"] < 1.2
    assert rep["on"]["exp_cand_enum"] < 1.2
    # wall-clock corroboration
    assert rep["on"]["exp_wall"] < rep["off"]["exp_wall"]


# ------------------------------------------------------------- falsifier ------
@needs_engine
def test_unsound_empty_var_projection_breaks_an_observable():
    """F — projecting away `area` (used in the guard AND effect) MUST break an
    observable on a MULTI-HUB workload (the 3-area scheduler running the SAME
    rule the eye's cost is), while the SOUND projection mirrors OFF. The eye is
    structurally one hub, so the mechanism's non-vacuity is witnessed here."""
    rep = M.falsifier()
    assert rep["sound_is_mirror_of_off"], "sound projection must equal OFF"
    assert rep["wrong_breaks_effort_observable"], \
        "unsound projection did NOT break the area.effort observable"
    # 2 of 3 areas left stale under the empty-var projection
    assert rep["sched_effort_wrong"] != rep["sched_effort_sound"]
    # on the single-hub eye, sound and unsound coincide (structural, honest)
    assert rep["eye_single_hub_sound_eq_wrong"]


# --------------------------------------------- non-observable-scatter ---------
@needs_engine
def test_graph_to_dict_scatter_is_wallclock_only_and_non_observable():
    """MEASURED: the ONLY graph_to_dict difference OFF vs ON is the two
    wall-clock timing attributes — they differ even between two identical OFF
    runs (run-to-run nondeterminism, not the flag), and once stripped the full
    graph is BYTE-IDENTICAL OFF ≡ ON ≡ run-to-run. This is the evidence the
    manifold-gate is sound, not a loophole: no attribute VALUE, node, or edge
    the agent perceives differs."""
    rep = M.scatter_identification()
    assert rep["raw_md5_differs_off_vs_on"], "raw dumps must differ (the caveat)"
    assert rep["raw_md5_differs_off_vs_off"], \
        "the scatter is run-to-run nondeterminism, present without the flag"
    assert rep["scatter_is_wallclock_only"], \
        f"scatter is NOT wall-clock-only: {rep['differing_attrs_off_vs_on']}"
    assert rep["node_set_identical"] and rep["edge_set_identical"]
    assert rep["wallclock_stripped_byte_identical_off_on"], \
        "stripping wall-clock must make OFF and ON byte-identical"
    assert rep["wallclock_stripped_deterministic_off_off"]


# ------------------------------------------------------------------ C1 --------
@needs_engine
def test_c1_off_path_is_the_committed_oracle():
    """OFF path is the committed oracle: wall-clock-stripped it is deterministic
    and BYTE-IDENTICAL to the ON path (== committed main), the only raw
    difference being the non-observable wall-clock scatter."""
    rep = M.c1_default_is_committed()
    assert rep["off_stripped_deterministic"]
    assert rep["off_equals_on_stripped"]
    assert rep["off_vs_on_raw_differs_only_by_wallclock"]
    assert rep["manifold_off_equals_on"]
