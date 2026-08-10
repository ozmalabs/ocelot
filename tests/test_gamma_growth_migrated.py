"""meta-Γ growth, migrated — the mechanical half of grow_representation runs on
the WorldAdapter (no CuriousAgent): a discovered (salient) relation is reified
into a new Γ production admitting it + a Pattern node asserted by the agent.
The DECISION (salience) is the seeded predicate; only the reification is here.

(grow_gamma's compositional Γ_dynamic structure-growth — genuine representation
reasoning beyond relation-promotion — stays in the bench.)
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def _discover():
    wa = WorldAdapter()
    for _ in range(10):
        wa.record_activity("act", ["Body"])
        wa.record_activity("observe", ["Item"])
    promoted = wa.discover_relations(min_count=8)
    return wa, promoted


def test_discovered_relation_grows_a_production():
    wa, promoted = _discover()
    assert len(promoted) > 0
    for rid in promoted:
        assert rid in wa.meta_productions()


def test_production_lands_in_the_grammar():
    wa, promoted = _discover()
    g = wa.inner.grammar_to_json()
    prod_edges = {p.get("edge_type") for p in g.get("productions", [])}
    for rid in promoted:
        assert rid in prod_edges


def test_discovery_asserts_a_pattern_node():
    wa, promoted = _discover()
    patterns = wa.patterns()
    assert len(patterns) == len(promoted)
    assert all(p["shape"] == "temporal_lag" for p in patterns)
    assert any(p["from_type"] == "Body" and p["to_type"] == "Item" for p in patterns)


def test_growth_is_idempotent_on_rediscovery():
    wa, promoted = _discover()
    n_prod = len(wa.meta_productions())
    n_pat = len(wa.patterns())
    for _ in range(5):
        wa.record_activity("act", ["Body"])
        wa.record_activity("observe", ["Item"])
    wa.discover_relations(min_count=8)
    assert len(wa.meta_productions()) == n_prod      # no new production for the same relation
    assert len(wa.patterns()) == n_pat
