"""Γ_meta core, slice A — the self-growing grammar as graph data, gated by a
meta-grammar, on the seed-booted WorldAdapter's OWN Rust substrate (self.s).

This is the structural foundation of test_curious_agent: Γ_dynamic is a VIEW over
Production nodes hanging off a Grammar root; every Γ-edit goes through the CHECKED
add_edge, so the meta-grammar refuses ill-formed edits (the agent grows its own
grammar under the same admissibility machinery that gates the world it observes);
supersede leaves the old production as an orphan (the substrate keeps its history).

Covers the structural/meta-grammar subset of test_curious_agent (the Γ-growth
mechanism exercised directly via _append_production/_supersede). The chess-
observation growth loop — discovering piece types + pawn invariants from live
self-play, quality monotonicity, where-clause widening — is slices B (the grow
engine) and C (the chess world); test_curious_agent burns only after all three.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate import NodePattern, Production
from substrate_rs._native import InadmissibleEdge
from substrate.world_adapter import WorldAdapter


def _agent():
    a = WorldAdapter()
    a.boot_gamma_meta()
    return a


def _prod(src, edge, tgt, prov="discovered:x"):
    return Production(src=NodePattern(src, "s"), edge_type=edge,
                      tgt=NodePattern(tgt, "t"), where=None, provenance=prov)


def test_starts_with_empty_gamma():
    a = _agent()
    assert len(a.gamma_dynamic.productions) == 0
    assert a.quality_of_gamma() == 0.0
    assert a.n_observations == 0


def test_mind_graph_starts_with_grammar_root():
    a = _agent()
    grammar_nodes = [n for n in a.s.nodes("Grammar")]
    assert len(grammar_nodes) == 1
    assert a.gamma_root == grammar_nodes[0]
    assert len([n for n in a.s.nodes("Production")]) == 0


def test_mind_substrate_has_meta_grammar():
    a = _agent()
    provs = [p.get("provenance", "") for p in a.s.grammar_to_json()["productions"]]
    assert any(pr.startswith("meta:") for pr in provs)


def test_gamma_edits_visible_in_mind_graph():
    a = _agent()
    a._append_production(_prod("WhitePawn", "piece_at", "Square"))
    a._append_production(_prod("BlackKing", "piece_at", "Square"))
    production_edges = list(a.inner.neighbours(a.gamma_root, "production"))
    assert len(production_edges) == len(a.gamma_dynamic.productions) == 2
    for pid in production_edges:
        src = list(a.inner.neighbours(pid, "pattern.src"))
        tgt = list(a.inner.neighbours(pid, "pattern.tgt"))
        assert len(src) == 1 and len(tgt) == 1
        assert a.s.node(src[0])["type"] == "NodePattern"
        assert a.s.node(tgt[0])["type"] == "NodePattern"


def test_gamma_dynamic_is_a_view_not_storage():
    a = _agent()
    a._append_production(_prod("WhitePawn", "piece_at", "Square"))
    n1 = len(a.gamma_dynamic.productions)
    a._append_production(_prod("InjectedType", "injected_edge", "Square",
                               prov="external:injected"))
    g2 = a.gamma_dynamic
    assert len(g2.productions) == n1 + 1
    assert any(p.provenance == "external:injected" for p in g2.productions)


def test_inadmissible_edit_rejected_by_meta_gamma():
    a = _agent()
    np_id = a.s.add_node("NodePattern", {"type": "Foo", "var": "x"})
    # Γ_meta admits only Production targets on a `production` edge from gamma_root.
    with pytest.raises(InadmissibleEdge):
        a.inner.add_edge(a.gamma_root, "production", np_id)


def test_inadmissible_boundary_relation_rejected():
    a = _agent()
    bt = a._ensure_body_type("WhitePawn")
    # Γ_meta admits only {senses, models, acts_on} from Agent -> BodyType.
    with pytest.raises(InadmissibleEdge):
        a.inner.add_edge(a.agent, "secret_relation", bt)


def test_supersede_leaves_orphan_history():
    a = _agent()
    a._append_production(_prod("WhitePawn", "piece_at", "Square"))
    a._supersede_production(
        0, _prod("WhitePawn", "piece_at", "Square", prov="discovered:x|refined"))
    total = len([n for n in a.s.nodes("Production")])
    active = len(list(a.inner.neighbours(a.gamma_root, "production")))
    assert total - active > 0, f"no orphan (total={total}, active={active})"
