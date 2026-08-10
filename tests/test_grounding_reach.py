"""test_grounding_reach — pins domains/grounding_reach.py, the substrate for a
follow-on agent-authored guard rule (NOT built here; see the module docstring
and CLAUDE.md: the guard decision is a Rule, this only makes groundedness a
queryable graph property).

Covers, on a hand-built graph (no seed boot needed — a bare
`substrate_rs.Substrate()` duck-types as a valid `agent`):

  (a) a node grounded via a CHAIN to a SensorAnchor: reached, hops > 0.
  (b) a self-referential loop with NO anchor: NOT reached.
  (c) confident + low-residual + NO grounding -> flag_ungrounded_confident
      mints a GroundingGap.
  (d) confident + low-residual + WITH an anchor -> NOT flagged (discriminative:
      grounding, not confidence, is what saves it).
  (e) the RECONSTRUCTED residual-salience failure mode (seeds/residual_
      salience.json's history): a SATURATED axis (residual ~ 0) with no live
      grounding -> flagged; a genuinely-solved axis grounded in a
      ConsequenceAnchor (a real judged Experiment outcome) -> NOT flagged.

Plus: grounding_reach's reached/anchors verdict is cross-checked against a
DIRECT call to the same native `ReachableFrom` Term evaluate() — proving the
query is a thin caller of the agent-installed primitive, not a Python re-walk
of the grounded_in graph.
"""
from __future__ import annotations

import substrate_rs as srs

from domains import grounding_reach as gr


def _mk():
    s = srs.Substrate()
    N = {}
    N["agent"] = s.add_node("Agent", {})
    N["percept"] = s.add_node("VisionPercept", {})
    s.add_edge_unchecked(N["agent"], "perceives", N["percept"])

    N["chained"] = s.add_node("Collapse", {"label": "chained"})
    s.add_edge_unchecked(N["chained"], "grounded_in", N["percept"])

    N["loop_a"] = s.add_node("Collapse", {"label": "loop_a"})
    N["loop_b"] = s.add_node("Collapse", {"label": "loop_b"})
    s.add_edge_unchecked(N["loop_a"], "grounded_in", N["loop_b"])
    s.add_edge_unchecked(N["loop_b"], "grounded_in", N["loop_a"])

    N["confident_ungrounded"] = s.add_node("Collapse", {
        "residual": 0.01, "confidence": 0.97})
    N["confident_grounded"] = s.add_node("Collapse", {
        "residual": 0.01, "confidence": 0.97})
    s.add_edge_unchecked(N["confident_grounded"], "grounded_in", N["percept"])

    N["axis_sat_ungrounded"] = s.add_node("CapabilityAxis", {
        "residual": 0.0, "confidence": 0.99, "saturation": 1.0})

    N["run"] = s.add_node("Run", {"status": "done", "score": 12.0, "frames": 12.0})
    N["experiment"] = s.add_node("Experiment", {
        "status": "requested", "outcome": "supported"})
    s.add_edge_unchecked(N["experiment"], "produced", N["run"])
    N["axis_sat_grounded"] = s.add_node("CapabilityAxis", {
        "residual": 0.0, "confidence": 0.99, "saturation": 1.0})
    s.add_edge_unchecked(N["axis_sat_grounded"], "grounded_in", N["experiment"])

    return s, N


def test_ensure_grounding_edges_mints_and_is_idempotent():
    s, N = _mk()
    rep = gr.ensure_grounding_edges(s)
    assert rep["sensor"] >= 1
    assert rep["consequence"] >= 1
    assert s.has_edge(N["percept"], "grounded_in", _anchor(s, "SensorAnchor"))
    assert s.has_edge(N["experiment"], "grounded_in", _anchor(s, "ConsequenceAnchor"))

    rep2 = gr.ensure_grounding_edges(s)
    assert rep2 == {"sensor": 0, "teacher": 0, "consequence": 0, "reality": 0, "total": 0}


def _anchor(s, kind):
    ns = s.nodes(kind)
    assert len(ns) == 1, f"expected exactly one {kind} singleton, got {len(ns)}"
    return ns[0]


def test_scenario_a_chained_reaches_sensor_anchor_with_hops():
    s, N = _mk()
    gr.ensure_grounding_edges(s)
    r = gr.grounding_reach(s, N["chained"])
    assert r["reached"] is True
    assert r["anchors"] == ["SensorAnchor"]
    assert r["hops"] is not None and r["hops"] > 0


def test_scenario_b_self_loop_has_no_anchor():
    s, N = _mk()
    gr.ensure_grounding_edges(s)
    r = gr.grounding_reach(s, N["loop_a"])
    assert r["reached"] is False
    assert r["anchors"] == []
    assert r["hops"] is None


def test_grounding_reach_matches_direct_native_reachable_from():
    """grounding_reach must be a thin caller of the REAL installed
    ReachableFrom Term, not a Python re-walk: cross-check against a direct
    native evaluate() call of the identical term."""
    s, N = _mk()
    gr.ensure_grounding_edges(s)
    term = {"type": "ReachableFrom", "node": {"type": "Var", "name": "n"},
            "edge_type": "grounded_in"}
    direct = set(s._inner.evaluate(term, {"n": N["chained"]}))
    direct_anchor_types = {s.node(x)["type"] for x in direct if s.has_node(x)} & set(gr.ANCHOR_KINDS)
    r = gr.grounding_reach(s, N["chained"])
    assert direct_anchor_types == set(r["anchors"])
    assert "SensorAnchor" in direct_anchor_types


def test_scenario_c_confident_ungrounded_is_flagged():
    s, N = _mk()
    gr.ensure_grounding_edges(s)
    flagged = gr.flag_ungrounded_confident(s, node_types=["Collapse", "CapabilityAxis"])
    assert N["confident_ungrounded"] in flagged
    gaps = list(s.nodes("GroundingGap"))
    assert any(s.node(g)["attrs"].get("node") == N["confident_ungrounded"] for g in gaps)


def test_scenario_d_confident_but_grounded_is_not_flagged():
    """Discriminative: grounding, not confidence, is what saves a node."""
    s, N = _mk()
    gr.ensure_grounding_edges(s)
    flagged = gr.flag_ungrounded_confident(s, node_types=["Collapse", "CapabilityAxis"])
    assert N["confident_grounded"] not in flagged


def test_scenario_e_residual_salience_failure_reconstruction():
    """The 2026-07-02 residual-salience incident, reconstructed: a SATURATED
    axis (residual ~ 0, confidence high) with no live grounding must be
    flagged; a genuinely-solved axis grounded in a real judged Experiment
    (ConsequenceAnchor) must NOT be flagged, even though both look identical
    on residual/confidence alone."""
    s, N = _mk()
    gr.ensure_grounding_edges(s)

    r_ungrounded = gr.grounding_reach(s, N["axis_sat_ungrounded"])
    r_grounded = gr.grounding_reach(s, N["axis_sat_grounded"])
    assert r_ungrounded["reached"] is False
    assert r_grounded["reached"] is True
    assert r_grounded["anchors"] == ["ConsequenceAnchor"]

    flagged = gr.flag_ungrounded_confident(s, node_types=["Collapse", "CapabilityAxis"])
    assert N["axis_sat_ungrounded"] in flagged
    assert N["axis_sat_grounded"] not in flagged


def test_flag_pass_is_idempotent():
    s, N = _mk()
    gr.ensure_grounding_edges(s)
    f1 = gr.flag_ungrounded_confident(s, node_types=["Collapse", "CapabilityAxis"])
    n1 = len(list(s.nodes("GroundingGap")))
    f2 = gr.flag_ungrounded_confident(s, node_types=["Collapse", "CapabilityAxis"])
    n2 = len(list(s.nodes("GroundingGap")))
    assert n1 == n2
    assert set(f1) == set(f2)


def test_missing_attrs_never_false_positive():
    """A node with only ONE of residual/confidence must never be flagged (no
    fabricated verdict from a missing attr)."""
    s, N = _mk()
    only_residual = s.add_node("Collapse", {"residual": 0.0})
    only_conf = s.add_node("Collapse", {"confidence": 0.99})
    gr.ensure_grounding_edges(s)
    flagged = gr.flag_ungrounded_confident(s, node_types=["Collapse"])
    assert only_residual not in flagged
    assert only_conf not in flagged
