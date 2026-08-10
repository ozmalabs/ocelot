#!/usr/bin/env python3
"""jabberwock_imagines -- standalone, discriminative demonstrator for TIER 3
of the collapse-modeling stack (`domains/imagination.py`): holding/running
the graph's OWN collapse DETACHED from the external reference frame, with a
RETURN PATH back to reality.

This is the mechanical MACHINERY only (snapshot / cut-grounding / inject /
run / reground / gated writeback) -- a follow-on task has the agent AUTHOR
the rules that decide WHEN to imagine and WHAT to do with the result. This
script proves the machinery works standalone, on a small hand-built scratch
substrate (no full seed boot needed -- the mechanism is domain-general).

Sections, each PASS/FAIL, exit 0 iff every section passes:

  1. IMAGINE PRODUCES CONCLUSIONS -- injecting a hypothesis and running the
     detached collapse yields new nodes/edges the grounded graph didn't have.
  2. FRAME-INDEPENDENCE -- the SAME hypothesis, cut vs not-cut, reaches a
     DIFFERENT conclusion: cut derives a consequence the grounded collapse
     vetoes instead.
  3. THE RETURN PATH -- reground() keeps a conclusion consistent with a
     grounded live fact, and discards one that contradicts a grounded live
     fact (both directions, on the same imagination).
  4. REVERSIBILITY -- every node/edge that existed before imagine() is
     byte-identical after; only the sanctioned Imagination/ImaginedConclusion
     trace was appended; no Commitment record. A subsequent writeback DOES
     mint a Commitment (gated: refused with no approver, allowed with one).
  5. PLANNING LOOKAHEAD -- two candidate actions are imagined; the better one
     is chosen by reading the imagined outcomes, never touching the live
     graph, before anything is committed.

Rerun this after any change to domains/imagination.py.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs                                          # noqa: E402

from domains.imagination import (                                   # noqa: E402
    commit_imagination, imagine, reground,
)

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


def _install_contradiction_rules(s) -> None:
    """Two graph-resident Rule nodes over a `Hypothesis -contradicts-> Fact`
    edge: one derives a Conclusion ONLY when the Fact is currently
    UNGROUNDED (Count of its `grounded_in` neighbours is 0); the other vetoes
    the hypothesis whenever the Fact IS grounded. `graph_to_dict`/
    `graph_from_dict` carry these as ordinary nodes -- no separate
    installation step needed on the detached copy."""
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


_WHERE_UNGROUNDED_REVISE = {
    "type": "Eq", "a": {"type": "Count", "source": {
        "type": "Neighbours", "node": {"type": "Var", "name": "f"},
        "edge_type": "grounded_in"}}, "b": {"type": "Lit", "value": 0},
}


def _install_revise_rule(s) -> None:
    """A `Hypothesis -revises-> Fact` edge overwrites the Fact's `value`
    attr with the hypothesis's `new_value` -- but ONLY when the Fact is
    currently ungrounded (same guard shape as `derive_when_ungrounded`).
    This is the rule that produces a `node_changed` conclusion by IDENTITY
    (same NodeID as the live Fact), which is what `reground` can catch as a
    contradiction if the live Fact stays grounded."""
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


def _hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def section_1_conclusions() -> bool:
    _hr("1. IMAGINE PRODUCES CONCLUSIONS")
    s = srs.Substrate()
    _install_contradiction_rules(s)
    f, _a = _fact_with_anchor(s, "blue")
    dc = imagine(s, hypothesis={
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}],
    })
    added_types = sorted(n.get("type") for n in dc.conclusions["nodes_added"])
    ok = dc.n_conclusions > 0 and "Conclusion" in added_types and "Hypothesis" in added_types
    print(f"  n_conclusions={dc.n_conclusions} nodes_added_types={added_types} "
          f"converged={dc.converged} residual={dc.residual}")
    print("  PASS" if ok else "  FAIL")
    return ok


def section_2_frame_independence() -> bool:
    _hr("2. FRAME-INDEPENDENCE (cut vs grounded, same hypothesis)")
    s = srs.Substrate()
    _install_contradiction_rules(s)
    f, _a = _fact_with_anchor(s, "blue")
    hyp = {"nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
           "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}]}

    dc_cut = imagine(s, hypothesis=hyp, cut_grounding=True)
    dc_grounded = imagine(s, hypothesis=hyp, cut_grounding=False)

    cut_has_conclusion = "Conclusion" in {n.get("type") for n in dc_cut.conclusions["nodes_added"]}
    grounded_has_conclusion = "Conclusion" in {n.get("type") for n in dc_grounded.conclusions["nodes_added"]}
    h_grounded_node = dc_grounded.hyp_map["h"]
    vetoed = dc_grounded.detached.node(h_grounded_node)["attrs"].get("vetoed") is True

    ok = cut_has_conclusion and (not grounded_has_conclusion) and vetoed
    print(f"  cut_grounding=True  -> Conclusion derived: {cut_has_conclusion}")
    print(f"  cut_grounding=False -> Conclusion derived: {grounded_has_conclusion}, hypothesis vetoed: {vetoed}")
    print("  PASS" if ok else "  FAIL")
    return ok


def section_3_return_path() -> bool:
    _hr("3. THE RETURN PATH (reground: survive vs discard)")
    s = srs.Substrate()
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
    survived_kinds = [s.node(cid)["attrs"]["kind"] for cid in rg["survivors"]]
    discarded_kinds = [s.node(cid)["attrs"]["kind"] for cid in rg["discarded"]]
    live_value_untouched = s.node(f)["attrs"]["value"] == "blue"

    ok = ("node_added" in survived_kinds and "node_changed" in discarded_kinds
          and 0.0 < rg["residual"] < 1.0 and live_value_untouched)
    print(f"  survivors kinds={survived_kinds} discarded kinds={discarded_kinds} residual={rg['residual']}")
    print(f"  live Fact.value still 'blue' (reground never writes back): {live_value_untouched}")
    for d in rg["detail"]:
        print(f"    {d['kind']:14s} survived={d['survived']!s:5s} {d['reason']}")
    print("  PASS" if ok else "  FAIL")
    return ok


def section_4_reversibility_and_commit() -> bool:
    _hr("4. REVERSIBILITY + GATED COMMIT")
    s = srs.Substrate()
    _install_contradiction_rules(s)
    f, a = _fact_with_anchor(s, "blue")
    before = s._inner.graph_to_dict()

    dc = imagine(s, hypothesis={
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": f.value}],
    })
    after_imagine = s._inner.graph_to_dict()
    diff = srs._native.Substrate.graph_diff(before, after_imagine)
    domain_untouched = not diff["nodes_removed"] and not diff["nodes_changed"] and not diff["edges_removed"]
    added_types = {n["type"] for n in diff["nodes_added"]}
    added_edge_types = {e["type"] for e in diff["edges_added"]}
    trace_only = added_types <= {"Imagination", "ImaginedConclusion"} and added_edge_types <= {"imagined"}
    no_commitment_from_imagine = len(list(s.nodes("Commitment"))) == 0
    still_grounded = s.has_edge(f, "grounded_in", a)

    rg = reground(s, dc)
    refused = commit_imagination(s, dc, rg["survivors"])
    n_commit_after_refusal = len(list(s.nodes("Commitment")))
    ok_ = commit_imagination(s, dc, rg["survivors"], approver="jabberwock-imagines-demo")
    n_commit_after_allow = len(list(s.nodes("Commitment")))

    committed_conclusion = next((w for w in ok_["written"] if w["kind"] == "node_added"), None)
    committed_live = committed_conclusion is not None and s.has_node(committed_conclusion["node"])

    ok = (domain_untouched and trace_only and no_commitment_from_imagine and still_grounded
          and refused["gate"]["allowed"] is False and n_commit_after_refusal == 1
          and ok_["gate"]["allowed"] is True and n_commit_after_allow == 2
          and committed_live)

    print(f"  domain (pre-existing nodes/edges) untouched by imagine(): {domain_untouched}")
    print(f"  only Imagination/ImaginedConclusion/imagined added by imagine(): {trace_only}")
    print(f"  Commitment records after imagine(): 0 -> {no_commitment_from_imagine}")
    print(f"  writeback w/o approver: allowed={refused['gate']['allowed']} "
          f"(Commitment count -> {n_commit_after_refusal})")
    print(f"  writeback w/ approver:  allowed={ok_['gate']['allowed']} "
          f"(Commitment count -> {n_commit_after_allow}), committed node live: {committed_live}")
    print("  PASS" if ok else "  FAIL")
    return ok


def section_5_planning_lookahead() -> bool:
    _hr("5. PLANNING LOOKAHEAD (imagine two moves, choose, without acting)")
    s = srs.Substrate()
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
    goal = 10
    chosen = "A" if abs(goal - x_a) < abs(goal - x_b) else "B"
    live_untouched = s.node(pos)["attrs"]["x"] == 0

    ok = x_a == 5 and x_b == -3 and chosen == "A" and live_untouched
    print(f"  imagined outcome A: x={x_a}   imagined outcome B: x={x_b}   goal={goal}")
    print(f"  chosen by reading the imagined outcomes: {chosen}")
    print(f"  live Position.x still 0 (nothing acted on): {live_untouched}")
    print("  PASS" if ok else "  FAIL")
    return ok


def main() -> int:
    results = [
        section_1_conclusions(),
        section_2_frame_independence(),
        section_3_return_path(),
        section_4_reversibility_and_commit(),
        section_5_planning_lookahead(),
    ]
    _hr("SUMMARY")
    ok = all(results)
    print(f"  {sum(results)}/{len(results)} sections passed")
    print("OVERALL: PASS" if ok else "OVERALL: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
