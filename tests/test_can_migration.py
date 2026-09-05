"""Tests for the CAN migration shim — backwards-compat for binary
refers_to → causal_influence + state/field/β attribute seeding.
"""
from __future__ import annotations

import json

import pytest
from substrate_rs import _native
from substrate.seed_loader import engine_rules_only

from domains.can_migration import (
    full_migration,
    migrate_refers_to_to_causal_influence,
    seed_concept_state_attrs,
    seed_mt_temperature,
)
from domains.can_native_orchestration import (
    native_audit_basin,
    native_marginal_from_state,
    scoped_settle,
)

_CAN_SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
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


def _native_substrate():
    s = _fresh_substrate()
    for path in _CAN_SEED_PATHS:
        s.load_seed_manifest(engine_rules_only(json.load(open(path))))
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
    # PHASE A: migrated network is queryable — mt_target (survivor) sees
    # both concepts. (Was: mt_mean_field_marginal len==2, engine removed.)
    assert len(s.mt_target(mt)) == 2


def test_can_ops_consume_migrated_graph():
    """End-to-end: migrate a legacy graph + run the surviving CAN reads on
    it via the native path.

    PHASE A (native-backend cutover): the continuous mean-field query was
    removed. After migration we make the Mt native (discrete_mode='3state',
    seeds loaded), inject evidence, settle, then read the SURVIVING reads
    (mt_target/mt_distance_to_target/mt_energy) + native_audit_basin. The
    `coupling_count` assertion is dropped (native_audit_basin omits it).
    """
    s = _native_substrate()
    mt = s.add_node("Microtheory", {})
    a = s.add_node("Concept", {})
    b = s.add_node("Concept", {})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    s.add_edge(a, "refers_to", b, {})  # legacy edge
    full_migration(s, default_weight=0.8, default_beta=2.0)
    # Make the migrated Mt native + add the reverse coupling so the native
    # out-edges-only local field sees the a↔b coupling both ways.
    s.set_attr(mt, "discrete_mode", "3state")
    s.set_attr(mt, "can_tick", 0)
    s.add_edge(b, "causal_influence", a, {"weight": 0.8})

    # Inject a small positive evidence on A — breaks symmetry.
    s.set_attr(a, "external_field", 0.3)
    scoped_settle(s, mt)

    marg = native_marginal_from_state(s, mt)
    energy = s.mt_energy(mt, marg)
    target = s.mt_target(mt)
    dist = s.mt_distance_to_target(mt)
    report = native_audit_basin(s, mt)

    # All nodes target +1 by default after migration.
    assert target[a.value] == 1.0
    assert target[b.value] == 1.0
    # Coupling + evidence pulls both nodes non-negative.
    assert marg[a.value] >= 0 and marg[b.value] >= 0
    # PHASE A: coupling_count assertion dropped (native audit omits it).
    assert isinstance(dist["magnitude"], float)
    assert isinstance(energy, float)
