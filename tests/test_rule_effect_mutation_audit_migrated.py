"""Native rule-effect mutation audit covers the instrumented mutation arms."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")


def test_native_rule_effect_mutation_counters_cover_effect_families():
    from substrate_rs import _native

    def run_case(effects, *, two_inputs=False):
        s = _native.Substrate()
        a = s.add_node("AuditVertex")
        b = s.add_node("AuditVertex")
        c = s.add_node("AuditVertex")
        s.add_edge_unchecked(a, "audit_trigger", b)
        match = [["a", "audit_trigger", "b"]]
        if two_inputs:
            s.add_edge_unchecked(c, "audit_incoming", b)
            match.append(["c", "audit_incoming", "b"])
        s.add_rule({"name": "audit_effect", "match": match, "effects": effects})
        _native.Substrate.scale_audit_reset()
        _native.Substrate.scale_audit_set_enabled(True)
        try:
            s.run_rules(10)
            return dict(_native.Substrate.scale_audit_snapshot())
        finally:
            _native.Substrate.scale_audit_set_enabled(False)

    samples = [
        run_case([["add_edge", "a", "audit_out", "b", {}]]),
        run_case([["del_edge", "a", "audit_trigger", "b"]]),
        run_case([["add_node", "fresh", "Minted", {}]],),
        run_case([["add_node_if_absent", "fresh", "Witness", {"tag": "one"}]]),
        run_case([["del_node", "b"]]),
        run_case([["set_attr", "a", "tag", "value"]]),
        run_case([["set_attr_if_different", "a", "tag", "value"]]),
        run_case([["replace_value", "b", "a"]], two_inputs=True),
    ]

    assert samples[0]["rule_effect_edge_insert_attempts"] >= 1
    assert samples[1]["rule_effect_edge_deletes"] >= 1
    assert samples[2]["rule_effect_node_inserts"] >= 1
    assert samples[3]["rule_effect_node_inserts"] == 1
    assert samples[4]["rule_effect_node_delete_attempts"] >= 1
    assert samples[5]["rule_effect_attr_set_attempts"] >= 1
    assert samples[6]["rule_effect_attr_set_attempts"] == 1
    assert samples[7]["rule_effect_replace_edge_deletes"] >= 1
    assert samples[7]["rule_effect_replace_edge_insert_attempts"] >= 1

