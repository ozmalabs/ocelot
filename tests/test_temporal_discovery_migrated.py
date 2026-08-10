"""temporal-pattern discovery, migrated — body-type temporal_lag pairs mined
from the activity log via the SEEDED salience_predicate, in the WorldAdapter (no
CuriousAgent). Covers tests/test_temporal_discovery: no/single event -> nothing;
a repeated (act,Body)->(observe,Item) pair promoted as shape='temporal_lag' with
count + lag; shared rel_ id space; count updates on rediscovery (no dup ids).
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def _temporal(wa):
    return [m for m in wa._discovered_relations.values() if m.get("shape") == "temporal_lag"]


def test_no_events_no_temporal_patterns():
    wa = WorldAdapter()
    wa.discover_relations()
    assert _temporal(wa) == []


def test_single_event_no_temporal_patterns():
    wa = WorldAdapter()
    wa.record_activity("act", ["Body"])
    wa.discover_relations()
    assert _temporal(wa) == []


def test_repeated_pair_discovered_as_temporal_lag():
    wa = WorldAdapter()
    for _ in range(10):
        wa.record_activity("act", ["Body"])
        wa.record_activity("observe", ["Item"])
    wa.discover_relations()
    target = next((m for m in _temporal(wa)
                   if m["from_kind"] == "act" and m["from_type"] == "Body"
                   and m["to_kind"] == "observe" and m["to_type"] == "Item"), None)
    assert target is not None
    assert target["count"] >= 10
    assert target["lag"] == 1


def test_temporal_patterns_share_rel_id_space():
    wa = WorldAdapter()
    for _ in range(10):
        wa.record_activity("act", ["Body"])
        wa.record_activity("observe", ["Item"])
    wa.discover_relations()
    assert all(rid.startswith("rel_") for rid in wa._discovered_relations)


def test_count_updates_on_rediscovery_no_dup_ids():
    wa = WorldAdapter()
    for _ in range(10):
        wa.record_activity("act", ["Body"])
        wa.record_activity("observe", ["Item"])
    wa.discover_relations()
    n_first = len(wa._discovered_relations)
    for _ in range(5):
        wa.record_activity("act", ["Body"])
        wa.record_activity("observe", ["Item"])
    wa.discover_relations()
    assert len(wa._discovered_relations) == n_first
    target = next(m for m in _temporal(wa)
                  if m["from_type"] == "Body" and m["to_type"] == "Item")
    assert target["count"] >= 15
