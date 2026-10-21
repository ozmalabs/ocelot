"""Γ type constraints are consumers for nodes matched through their edges."""
import json

from scripts.lint_orphan_signals import _extract_seed_writes_and_reads


def test_matched_declared_edge_consumes_endpoint_node_types(tmp_path):
    seed_dir = tmp_path / "seeds"
    seed_dir.mkdir()
    manifest = {
        "id": "fixture",
        "productions": [{
            "src": {"type": "Agent", "var": "agent"},
            "edge_type": "has_fixture_item",
            "tgt": {"type": "FixtureItem", "var": "item"},
        }],
        "rules": [{
            "name": "consume_fixture_item",
            "match": [["agent", "has_fixture_item", "item"]],
            "where": None,
            "effects": [["add_node", "other", "UnconsumedFixtureType", {}]],
        }],
    }
    (seed_dir / "fixture.json").write_text(json.dumps(manifest))
    writes, reads = _extract_seed_writes_and_reads(seed_dir)
    assert ("node_type", "FixtureItem") in reads
    assert ("node_type", "UnconsumedFixtureType") in writes
    assert ("node_type", "UnconsumedFixtureType") not in reads


def test_unmatched_edge_does_not_consume_endpoint_types(tmp_path):
    seed_dir = tmp_path / "seeds"
    seed_dir.mkdir()
    manifest = {
        "id": "fixture",
        "productions": [{
            "src": {"type": "Agent", "var": "agent"},
            "edge_type": "has_fixture_item",
            "tgt": {"type": "FixtureItem", "var": "item"},
        }],
        "rules": [{"name": "emit_only", "match": [],
                   "effects": [["add_node", "item", "FixtureItem", {}]]}],
    }
    (seed_dir / "fixture.json").write_text(json.dumps(manifest))
    writes, reads = _extract_seed_writes_and_reads(seed_dir)
    assert ("node_type", "FixtureItem") in writes
    assert ("node_type", "FixtureItem") not in reads
