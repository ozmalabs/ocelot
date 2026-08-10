"""Tests for the CAN migration shim — backwards-compat for binary
refers_to → causal_influence + state/field/β attribute seeding.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native

from domains.can_migration import (
    full_migration,
    migrate_refers_to_to_causal_influence,
    seed_concept_state_attrs,
    seed_mt_temperature,
)


_NODE_TYPES = ("Microtheory", "Concept", "Rule")
_EDGE_TYPES = ("genlMt", "has_concept", "has_rule", "refers_to",
               "causal_influence")


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


def test_migrate_refers_to_creates_causal_influence():
    s = _fresh_substrate()
    a = s.add_node("Concept", {"name": "A"})
    b = s.add_node("Concept", {"name": "B"})
    s.add_edge(a, "refers_to", b, {})
    created = migrate_refers_to_to_causal_influence(s)
    assert created == 1
    targets = s.neighbours(a, "causal_influence")
    assert b in targets


def test_migration_idempotent():
    s = _fresh_substrate()
    a = s.add_node("Concept", {})
    b = s.add_node("Concept", {})
    s.add_edge(a, "refers_to", b, {})
    first = migrate_refers_to_to_causal_influence(s)
    second = migrate_refers_to_to_causal_influence(s)
    assert first == 1
    assert second == 0  # no double-creation


def test_seed_concept_state_attrs_initialises_zero():
    s = _fresh_substrate()
    n = s.add_node("Concept", {"name": "X"})
    touched = seed_concept_state_attrs(s)
    assert touched == 1
    attrs = s.node(n)["attrs"]
    assert attrs["state"] == 0.0
    assert attrs["external_field"] == 0.0


def test_seed_concept_state_does_not_overwrite_existing():
    s = _fresh_substrate()
    n = s.add_node("Concept", {"state": 0.7, "external_field": 1.2})
    touched = seed_concept_state_attrs(s)
    assert touched == 0  # nothing to do
    attrs = s.node(n)["attrs"]
    assert attrs["state"] == 0.7
    assert attrs["external_field"] == 1.2


def test_seed_mt_temperature_default_beta_one():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "m"})
    touched = seed_mt_temperature(s)
    assert touched == 1
    assert s.node(mt)["attrs"]["temperature"] == 1.0


def test_seed_mt_temperature_respects_custom_beta():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    seed_mt_temperature(s, default_beta=2.5)
    assert s.node(mt)["attrs"]["temperature"] == 2.5


def test_full_migration_end_to_end():
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    a = s.add_node("Concept", {})
    b = s.add_node("Concept", {})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "refers_to", b, {})
    result = full_migration(s)
    assert result["edges_created"] == 1
    assert result["concepts_seeded"] == 2
    assert result["mts_seeded"] == 1
    # Migrated network is queryable by mean-field operations.
    marg = s.mt_mean_field_marginal(mt)
    assert len(marg) == 2


def test_can_ops_consume_migrated_graph():
    """End-to-end: migrate a legacy graph + run all four can_ops on it.

    After migration, mean-field at the all-zero state is the symmetric
    saddle. A small evidence h on one node breaks the symmetry and the
    coupling pulls the other node to the same sign.
    """
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {})
    a = s.add_node("Concept", {})
    b = s.add_node("Concept", {})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "refers_to", b, {})  # legacy edge
    full_migration(s, default_weight=0.8, default_beta=2.0)

    # Inject a small positive evidence on A — breaks symmetry.
    s.set_attr(a, "external_field", 0.3)

    marg = s.mt_mean_field_marginal(mt)
    energy = s.mt_energy(mt, marg)
    target = s.mt_target(mt)
    dist = s.mt_distance_to_target(mt)
    report = s.mt_audit_basin(mt)

    # All nodes target +1 by default after migration.
    assert target[a.value] == 1.0
    assert target[b.value] == 1.0
    # Coupling + evidence pulls both nodes positive.
    assert marg[a.value] > 0 and marg[b.value] > 0
    assert report["coupling_count"] == 1
    assert isinstance(dist["magnitude"], float)
    assert isinstance(energy, float)
