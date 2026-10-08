"""Recursive same-type edge writes must remain visible to the rule fixpoint."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")


def test_multi_edge_rule_consumes_edges_it_mints_until_transitive_closure():
    from substrate_rs import _native

    substrate = _native.Substrate()
    nodes = [substrate.add_node("ClosureVertex") for _ in range(6)]
    for src, tgt in zip(nodes, nodes[1:]):
        substrate.add_edge_unchecked(src, "closure_link", tgt)

    substrate.add_rule({
        "name": "closure_two_links",
        "match": [["x", "closure_link", "y"], ["y", "closure_link", "z"]],
        "effects": [["add_edge", "x", "closure_reach", "z", {}]],
    })
    substrate.add_rule({
        "name": "closure_extend_reach",
        "match": [["x", "closure_reach", "y"], ["y", "closure_link", "z"]],
        "effects": [["add_edge", "x", "closure_reach", "z", {}]],
    })

    _native.Substrate.scale_audit_reset()
    _native.Substrate.scale_audit_set_enabled(True)
    steps = substrate.run_rules(10_000)
    scale = dict(_native.Substrate.scale_audit_snapshot())
    _native.Substrate.scale_audit_set_enabled(False)

    # A six-vertex directed path has 5 direct edges and 10 transitive reach
    # edges. The recursive rule must revisit its own newly-created reach edges.
    assert steps > 0
    assert substrate.edge_count() == 15
    assert scale["rule_effect_edge_insert_attempts"] >= 10
    assert substrate.run_rules(1) == 0
