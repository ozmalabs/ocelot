"""The rule IR compares executable meaning, not authoring-format accidents."""
from __future__ import annotations

from copy import deepcopy

from substrate.rule_ir import canonical_rule_body, rules_semantically_equal


def _rule() -> dict:
    return {
        "name": "canonical_probe",
        "match": [["a", "sees", "b"], ["a", "knows", "c"]],
        "where": {
            "type": "Gt",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "b"}, "key": "score"},
            "b": {"type": "Lit", "value": 0.0},
        },
        "effects": [
            ["add_node", "d", "SeedDelta", {
                "add_rules": '[{"name":"child","match":[],"where":{"type":"Lit","value":true},"effects":[]}]',
                "remove_rules": '["old"]',
            }],
            ["add_edge", "b", "changed_by", "d"],
        ],
    }


def test_rule_ir_normalises_runtime_equivalent_encodings():
    left = _rule()
    right = deepcopy(left)
    right["match"].reverse()
    right["where"]["b"]["value"] = 0
    right["effects"][0][3]["add_rules"] = (
        '[{"effects":[],"where":{"value":true,"type":"Lit"},'
        '"match":[],"name":"child","content_hash":42,"revision":3,'
        '"rule_uid":9,"active":true}]')
    right["effects"][1].append({})

    assert rules_semantically_equal(left, right)
    assert canonical_rule_body(left) == canonical_rule_body(right)


def test_rule_ir_does_not_normalise_away_a_real_guard():
    guarded = _rule()
    unguarded = deepcopy(guarded)
    unguarded["where"] = {"type": "Lit", "value": True}

    assert not rules_semantically_equal(guarded, unguarded)


def test_invalid_rule_has_no_canonical_body():
    assert canonical_rule_body({"name": "broken"}) == ""
