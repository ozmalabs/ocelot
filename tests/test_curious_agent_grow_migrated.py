"""Γ_meta core, slice B — the grow engine, on the seed-booted WorldAdapter.

observe_gamma tallies structural triples + per-type attribute-value sets + the
observation counter; grow_gamma is the two-phase substrate growth: (1) triples
seen >= threshold become unconstrained Productions (meta-gated graph edits);
(2) per-source-type attribute constraints WIDEN — the where-clause is recomputed
from the UNION of all observed values and superseded in (the old production left
as an orphan). Quality is monotone non-decreasing (experiential support of the
discovered triples).

Exercised on synthetic world substrates so the engine is tested in isolation;
slice C wires the real chess world + live self-play for the chess-specific
discoveries (all 12 piece types, the pawn rank invariants, the acts_on gradient).
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate import (ConsistencyChecker, Grammar, In, Substrate, TypedGraph)
from substrate.world_adapter import WorldAdapter

_THRESH = 30


def _world(pawn_ranks):
    """A tiny chess-like position: WhitePawn nodes (carrying a `rank` attr) on a
    Square, via piece_at edges. `rank` is the only piece attribute, so the
    where-clause refinement targets it (the real chess world varies file too;
    here we isolate rank to test the widening mechanism)."""
    g = TypedGraph()
    sq = g._insert_node("Square", {})
    for r in pawn_ranks:
        p = g._insert_node("WhitePawn", {"rank": r})
        g._insert_edge(p, "piece_at", sq)
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def _agent():
    a = WorldAdapter()
    a.boot_gamma_meta()
    return a


def _pawn_where(a):
    for p in a.gamma_dynamic.productions:
        if p.src.type == "WhitePawn" and isinstance(p.where, In):
            return {it.value for it in p.where.container.items}
    return None


def test_grows_gamma_from_observation():
    a = _agent()
    for _ in range(_THRESH + 1):
        a.observe_gamma(_world([1]))
    a.grow_gamma(triple_threshold=_THRESH)
    prods = a.gamma_dynamic.productions
    assert prods, "no productions grown"
    assert a.n_observations > 0
    assert any(p.src.type == "WhitePawn" and p.edge_type == "piece_at"
               and p.tgt.type == "Square" for p in prods)
    assert all(p.provenance.startswith("discovered:") for p in prods)


def test_quality_is_monotone_non_decreasing():
    a = _agent()
    qualities = [a.quality_of_gamma()]
    for _ in range(4):
        for _ in range(_THRESH + 1):
            a.observe_gamma(_world([1, 2]))
        a.grow_gamma(triple_threshold=_THRESH)
        qualities.append(a.quality_of_gamma())
    diffs = [b - a_ for a_, b in zip(qualities, qualities[1:])]
    assert all(d >= 0 for d in diffs), f"quality regressed: {qualities}"
    assert qualities[-1] > qualities[0], "no learning observed"


def test_boundary_models_registered_from_growth():
    a = _agent()
    for _ in range(_THRESH + 1):
        a.observe_gamma(_world([1]))
    a.grow_gamma(triple_threshold=_THRESH)
    assert "WhitePawn" in a.models_set()
    assert "Square" in a.models_set()


def test_where_clauses_widen_with_experience():
    a = _agent()
    for _ in range(_THRESH + 1):
        a.observe_gamma(_world([1]))
    a.grow_gamma(triple_threshold=_THRESH)
    early = _pawn_where(a)
    assert early is not None
    for _ in range(5):
        a.observe_gamma(_world([1, 2, 3]))
    a.grow_gamma(triple_threshold=_THRESH)
    late = _pawn_where(a)
    assert late is not None
    assert early <= late, f"agent forgot values: early={early} late={late}"
    assert len(late) > len(early), "where-set did not widen"


def test_refinement_leaves_orphan_history():
    a = _agent()
    for _ in range(_THRESH + 1):
        a.observe_gamma(_world([1]))
    a.grow_gamma(triple_threshold=_THRESH)
    for _ in range(5):
        a.observe_gamma(_world([1, 2, 3]))
    a.grow_gamma(triple_threshold=_THRESH)          # widening supersedes
    total = len([n for n in a.s.nodes("Production")])
    active = len(list(a.inner.neighbours(a.gamma_root, "production")))
    assert total - active > 0, f"no orphan (total={total}, active={active})"
