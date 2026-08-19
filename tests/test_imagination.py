"""Tests for `domains/imagination.py` -- TIER 3 of the collapse-modeling
stack: holding/running the graph's own collapse DETACHED from the external
reference frame (imagination / counterfactual), with a RETURN PATH
(`reground`) back to reality, and a gated commit (`commit_imagination`,
routed through `domains/commitment_gate.py`) as the only path that mutates
the live graph with the imagined content.

Mirrors the standalone demonstrator `scripts/jabberwock_imagines.py` in
pytest form, plus a couple of extra edge cases (`focus_nodes` subgraph
snapshot, `has_node`-guard on a discarded/recycled id). See that script's
module docstring for the full section-by-section narrative; this file is
the fast regression the CI-shaped gate runs.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

import substrate_rs as srs

from domains.imagination import DetachedCollapse, commit_imagination, imagine, reground
from domains.shape_tube import goal_manifold, goal_projection

_WHERE_UNGROUNDED_F = {
    "type": "And", "items": [
        {"type": "Eq", "a": {"type": "Count", "source": {
            "type": "Neighbours", "node": {"type": "Var", "name": "f"},
            "edge_type": "grounded_in"}}, "b": {"type": "Lit", "value": 0}},
        {"type": "Eq", "a": {"type": "Count", "source": {
            "type": "Neighbours", "node": {"type": "Var", "name": "h"},
            "edge_type": "yields"}}, "b": {"type": "Lit", "value": 0}},
    ],
}

_WHERE_UNGROUNDED_REVISE = {
    "type": "Eq", "a": {"type": "Count", "source": {
        "type": "Neighbours", "node": {"type": "Var", "name": "f"},
        "edge_type": "grounded_in"}}, "b": {"type": "Lit", "value": 0},
}


def _install_contradiction_rules(s) -> None:
    s.add_node("Rule", {
        "id": "veto_grounded_contradiction",
        "match": [["h", "contradicts", "f"], ["f", "grounded_in", "a"]],
        "effect": [["set_attr", "h", "vetoed", True]],
    })
    s.add_node("Rule", {
        "id": "derive_when_ungrounded",
        "match": [["h", "contradicts", "f"]],
        "where": _WHERE_UNGROUNDED_F,
        "effect": [["add_node", "c", "Conclusion", {"derived_from_hypothesis": True}],
                   ["add_edge", "h", "yields", "c", {}]],
    })


def _install_revise_rule(s) -> None:
    s.add_node("Rule", {
        "id": "revise_when_ungrounded",
        "match": [["h", "revises", "f"]],
        "where": _WHERE_UNGROUNDED_REVISE,
        "effect": [["set_attr", "f", "value",
                    {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "h"}, "key": "new_value"}}]],
    })


def _fact_with_anchor(s, value: str):
    f = s.add_node("Fact", {"value": value})
    a = s.add_node("RealityAnchor", {})
    s.add_edge_unchecked(f, "grounded_in", a)
    return f, a


@pytest.fixture
def scratch():
    return srs.Substrate()


_TEST_PROJECTIONS = {
    "commit": goal_projection("test_writeback_goal", active=True,
                               action_count=1, intervention_magnitude=1.0),
    "wait": goal_projection("test_writeback_goal", active=False,
                             action_count=0, intervention_magnitude=0.0),
    "refine": goal_projection("test_writeback_goal", active=False,
                               action_count=1, intervention_magnitude=0.5),
}
_TEST_MANIFOLD = goal_manifold("test_writeback_goal")


# ---------------------------------------------------------------------------
# 1. imagine produces conclusions
# ---------------------------------------------------------------------------
def test_imagine_produces_conclusions(scratch):
    s = scratch
    _install_contradiction_rules(s)
    f, _a = _fact_with_anchor(s, "blue")
    dc = imagine(s, hypothesis={
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}],
    })
    assert isinstance(dc, DetachedCollapse)
    assert dc.n_conclusions > 0
    added_types = {n.get("type") for n in dc.conclusions["nodes_added"]}
    assert "Conclusion" in added_types
    assert "Hypothesis" in added_types
    # the durable trace exists on the LIVE graph
    assert s.has_node(dc.imagination_node)
    assert s.node(dc.imagination_node)["type"] == "Imagination"
    assert len(dc.conclusion_nodes) == dc.n_conclusions
    for cid in dc.conclusion_nodes:
        assert s.node(cid)["type"] == "ImaginedConclusion"


def test_imagine_with_no_hypothesis_is_a_noop_collapse(scratch):
    """No hypothesis, no rules that fire without one -> zero conclusions,
    still returns a valid DetachedCollapse with a durable trace."""
    s = scratch
    s.add_node("Fact", {"value": "blue"})
    dc = imagine(s)
    assert dc.n_conclusions == 0
    assert dc.hyp_map == {}
    assert s.has_node(dc.imagination_node)


# ---------------------------------------------------------------------------
# 2. frame-independence: cut vs grounded, same hypothesis, different outcome
# ---------------------------------------------------------------------------
def test_frame_independence_cut_vs_grounded(scratch):
    s = scratch
    _install_contradiction_rules(s)
    f, _a = _fact_with_anchor(s, "blue")
    hyp = {"nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
           "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}]}

    dc_cut = imagine(s, hypothesis=hyp, cut_grounding=True)
    assert dc_cut.grounding_cut_count >= 1
    assert "Conclusion" in {n.get("type") for n in dc_cut.conclusions["nodes_added"]}

    dc_grounded = imagine(s, hypothesis=hyp, cut_grounding=False)
    assert dc_grounded.grounding_cut_count == 0
    assert "Conclusion" not in {n.get("type") for n in dc_grounded.conclusions["nodes_added"]}
    h_node = dc_grounded.hyp_map["h"]
    assert dc_grounded.detached.node(h_node)["attrs"].get("vetoed") is True

    # the grounded run never even vetoes when cut -- pin the full contrast
    h_node_cut = dc_cut.hyp_map["h"]
    assert dc_cut.detached.node(h_node_cut)["attrs"].get("vetoed") is not True


# ---------------------------------------------------------------------------
# 3. the return path: reground keeps consistent, discards contradicting
# ---------------------------------------------------------------------------
def test_reground_survives_consistent_discards_contradicting(scratch):
    s = scratch
    _install_contradiction_rules(s)
    _install_revise_rule(s)
    f, _a = _fact_with_anchor(s, "blue")

    dc = imagine(s, hypothesis={
        "nodes": [
            {"key": "h1", "type": "Hypothesis", "attrs": {}},
            {"key": "h2", "type": "Hypothesis", "attrs": {"new_value": "green"}},
        ],
        "edges": [
            {"src": "h1", "type": "contradicts", "tgt": f.value},
            {"src": "h2", "type": "revises", "tgt": f.value},
        ],
    })
    rg = reground(s, dc)
    assert rg["survivors"] and rg["discarded"]
    assert 0.0 < rg["residual"] < 1.0

    survived_kinds = [s.node(cid)["attrs"]["kind"] for cid in rg["survivors"]]
    discarded_kinds = [s.node(cid)["attrs"]["kind"] for cid in rg["discarded"]]
    assert "node_added" in survived_kinds       # the brand-new Conclusion
    assert "node_changed" in discarded_kinds    # the revised (contradicting) Fact

    # reground NEVER writes back -- the live Fact is untouched
    assert s.node(f)["attrs"]["value"] == "blue"

    # the discarded conclusion's own record carries the reason
    discarded_node_changed = next(
        cid for cid in rg["discarded"] if s.node(cid)["attrs"]["kind"] == "node_changed")
    reason = s.node(discarded_node_changed)["attrs"]["reason"]
    assert "contradicts grounded live fact" in reason
    assert s.node(discarded_node_changed)["attrs"]["status"] == "discarded"

    survived_node_added = next(
        cid for cid in rg["survivors"] if s.node(cid)["attrs"]["kind"] == "node_added")
    assert s.node(survived_node_added)["attrs"]["status"] == "survived"

    # the Imagination summary was updated too
    assert s.node(dc.imagination_node)["attrs"]["status"] == "regrounded"
    assert s.node(dc.imagination_node)["attrs"]["n_survived"] == len(rg["survivors"])
    assert s.node(dc.imagination_node)["attrs"]["n_discarded"] == len(rg["discarded"])


def test_reground_ungrounded_live_fact_does_not_veto(scratch):
    """An UNGROUNDED live Fact (no grounded_in edge) that merely differs is
    unconfirmed, not contradicted -- the conclusion survives."""
    s = scratch
    _install_revise_rule(s)
    f = s.add_node("Fact", {"value": "blue"})   # no RealityAnchor -- never grounded
    dc = imagine(s, hypothesis={
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {"new_value": "green"}}],
        "edges": [{"src": "h", "type": "revises", "tgt": f.value}],
    })
    rg = reground(s, dc)
    changed = [cid for cid in dc.conclusion_nodes if s.node(cid)["attrs"]["kind"] == "node_changed"]
    assert changed
    assert all(cid in rg["survivors"] for cid in changed)


# ---------------------------------------------------------------------------
# 4. reversibility: imagine() never mutates pre-existing live state
# ---------------------------------------------------------------------------
def test_reversibility_domain_untouched_by_imagine(scratch):
    s = scratch
    _install_contradiction_rules(s)
    f, a = _fact_with_anchor(s, "blue")
    before = s._inner.graph_to_dict()

    dc = imagine(s, hypothesis={
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}],
    })
    after = s._inner.graph_to_dict()
    diff = srs._native.Substrate.graph_diff(before, after)

    # nothing that existed before was removed or changed
    assert diff["nodes_removed"] == []
    assert diff["nodes_changed"] == []
    assert diff["edges_removed"] == []
    # only the sanctioned trace was appended
    added_types = {n["type"] for n in diff["nodes_added"]}
    assert added_types <= {"Imagination", "ImaginedConclusion"}
    added_edge_types = {e["type"] for e in diff["edges_added"]}
    assert added_edge_types <= {"imagined"}
    # no Commitment record -- imagine() is not a commit
    assert list(s.nodes("Commitment")) == []
    # the original grounding is intact
    assert s.has_edge(f, "grounded_in", a)


def test_reversibility_detached_copy_is_independent(scratch):
    """Mutating the detached copy after imagine() returns must never reach
    the live substrate."""
    s = scratch
    f, a = _fact_with_anchor(s, "blue")
    dc = imagine(s, focus_nodes=[f])
    dc.detached._inner.set_attr(f, "value", "MUTATED")
    dc.detached.add_node("Intruder", {})
    assert s.node(f)["attrs"]["value"] == "blue"
    assert list(s.nodes("Intruder")) == []


# ---------------------------------------------------------------------------
# 4b. gated commit: refused without an approver, allowed with one, mints
#     Commitment either way; imagine()/reground() mint none.
# ---------------------------------------------------------------------------
def test_commit_imagination_gated_and_mints_commitment(scratch):
    s = scratch
    _install_contradiction_rules(s)
    f, _a = _fact_with_anchor(s, "blue")
    dc = imagine(s, hypothesis={
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}],
    })
    rg = reground(s, dc)
    assert list(s.nodes("Commitment")) == []   # imagine + reground: still zero

    refused = commit_imagination(s, dc, rg["survivors"])
    assert refused["gate"]["allowed"] is False
    assert refused["written"] == []
    assert len(list(s.nodes("Commitment"))) == 1   # refusal STILL audited

    allowed = commit_imagination(
        s, dc, rg["survivors"], approver="test-approver",
        projections=_TEST_PROJECTIONS,
        manifold=_TEST_MANIFOLD)
    assert allowed["gate"]["allowed"] is True
    assert allowed["written"]
    assert len(list(s.nodes("Commitment"))) == 2

    committed = next(w for w in allowed["written"]
                     if w["kind"] == "node_added" and s.node(w["node"])["type"] == "Conclusion")
    assert s.has_node(committed["node"])
    assert s.node(dc.imagination_node)["attrs"]["status"] == "committed"


def test_commit_imagination_denylist_refuses_even_with_approver(scratch):
    s = scratch
    _install_contradiction_rules(s)
    f, _a = _fact_with_anchor(s, "blue")
    dc = imagine(s, hypothesis={
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}],
    })
    rg = reground(s, dc)
    res = commit_imagination(
        s, dc, rg["survivors"], approver="anyone",
        policy={"denylist": ["imagination_writeback"]},
        projections=_TEST_PROJECTIONS,
        manifold=_TEST_MANIFOLD)
    assert res["gate"]["allowed"] is False
    assert res["written"] == []


# ---------------------------------------------------------------------------
# 5. planning lookahead: imagine two candidate actions, choose, don't act
# ---------------------------------------------------------------------------
def test_planning_lookahead_chooses_without_acting(scratch):
    s = scratch
    pos = s.add_node("Position", {"x": 0, "y": 0})
    anchor = s.add_node("SensorAnchor", {})
    s.add_edge_unchecked(pos, "grounded_in", anchor)
    s.add_node("Rule", {
        "id": "apply_move",
        "match": [["mv", "targets", "p"]],
        "effect": [["set_attr", "p", "x",
                    {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "mv"}, "key": "dx"}}]],
    })

    outcome_a = imagine(s, hypothesis={
        "nodes": [{"key": "mv", "type": "Move", "attrs": {"dx": 5}}],
        "edges": [{"src": "mv", "type": "targets", "tgt": pos.value}],
    })
    outcome_b = imagine(s, hypothesis={
        "nodes": [{"key": "mv", "type": "Move", "attrs": {"dx": -3}}],
        "edges": [{"src": "mv", "type": "targets", "tgt": pos.value}],
    })
    x_a = outcome_a.detached.node(pos)["attrs"]["x"]
    x_b = outcome_b.detached.node(pos)["attrs"]["x"]
    assert (x_a, x_b) == (5, -3)

    goal = 10
    chosen = outcome_a if abs(goal - x_a) < abs(goal - x_b) else outcome_b
    assert chosen is outcome_a

    # nothing acted on -- the live Position is exactly as before both imaginings
    assert s.node(pos)["attrs"]["x"] == 0


# ---------------------------------------------------------------------------
# focus_nodes: a snapshot restricted to a neighbourhood -- identity for
# EVERY live node is preserved (no id-collision risk for freshly-minted
# hypothesis nodes, see `_snapshot_dict`'s docstring), but only edges
# within the focus closure come along, so out-of-focus nodes are
# structurally isolated (unreachable to the collapse) in the detached copy.
# ---------------------------------------------------------------------------
def test_focus_nodes_restricts_the_snapshot(scratch):
    s = scratch
    _install_contradiction_rules(s)
    f, a = _fact_with_anchor(s, "blue")
    far = s.add_node("Unrelated", {"tag": "far"})   # not in f's 2-hop closure

    dc = imagine(s, focus_nodes=[f], hypothesis={
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}],
    })
    assert dc.detached.has_node(f)
    assert dc.detached.has_node(a)
    # far's identity is reserved (present) but structurally isolated: no
    # edge in the detached copy reaches it, so no Rule can match through it.
    assert dc.detached.has_node(far)
    assert list(dc.detached._inner.neighbours(far, None)) == []
    assert list(dc.detached._inner.in_neighbours(far, None)) == []
    # far lives on, untouched, in the live graph regardless
    assert s.has_node(far)


# ---------------------------------------------------------------------------
# has_node-guard: a conclusion naming a recycled/absent id never crashes
# reground or commit_imagination.
# ---------------------------------------------------------------------------
def test_reground_and_commit_guard_missing_ids(scratch):
    s = scratch
    _install_contradiction_rules(s)
    f, _a = _fact_with_anchor(s, "blue")
    dc = imagine(s, hypothesis={
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}],
    })
    # delete one conclusion record out from under reground/commit
    victim = dc.conclusion_nodes[0]
    s._inner.remove_node(victim)
    rg = reground(s, dc)          # must not raise
    assert victim not in rg["survivors"] and victim not in rg["discarded"]
    res = commit_imagination(
        s, dc, rg["survivors"], approver="x",
        projections=_TEST_PROJECTIONS,
        manifold=_TEST_MANIFOLD)
    assert res["gate"]["allowed"] is True
