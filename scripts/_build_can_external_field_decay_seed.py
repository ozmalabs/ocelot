"""One-off authoring script: appends `can_native_external_field_decay` to
seeds/can_decay_identity.json programmatically, to avoid a hand-typo in a
nested Term-tree -- the same `tools/*`-class precedent
`scripts/_build_can_decay_identity_seed.py` already used (CLAUDE.md names
this class explicitly: "one-off authoring/capture scripts that EMIT seed
manifests"; not agent runtime).

See docs/research/engine_substrate/CAN_EXTERNAL_FIELD_DECAY_PREREG.md for
the registered design this encodes.

Idempotent: if a rule of this name already exists in the seed, it is
REPLACED (not duplicated) so this script can be re-run safely.
"""
from __future__ import annotations

import json

SEED_PATH = "seeds/can_decay_identity.json"


def _attr(node_var: str, key: str) -> dict:
    return {"type": "Attr", "node": {"type": "Var", "name": node_var}, "key": key}


def _lit(value) -> dict:
    return {"type": "Lit", "value": value}


def _policy_or() -> dict:
    """Byte-identical subtree to the Or(...) policy gate the other two
    rules in this seed already use -- re-expressing
    mt_allows(mt, "allow_h_drift") as a Term."""
    return {
        "type": "Or",
        "items": [
            {"type": "Eq", "a": _attr("mt", "update_policy"), "b": _lit("adaptive")},
            {
                "type": "And",
                "items": [
                    {"type": "Eq", "a": _attr("mt", "update_policy"), "b": _lit("hybrid")},
                    {
                        "type": "Not",
                        "arg": {
                            "type": "Eq",
                            "a": _attr("mt", "allow_h_drift"),
                            "b": _lit(0),
                        },
                    },
                ],
            },
        ],
    }


def _clamp_toward_zero_term(node_var: str, key: str) -> dict:
    """max(x-1, 0) when x>0; min(x+1, 0) when x<0; unchanged at x==0.
    The symmetric generalisation of the other two rules' one-sided
    Gt(x,0)-then-x-1 body, required because external_field is a SIGNED
    float with no native accumulation rule (PREREG Sec1b)."""
    x = _attr(node_var, key)
    return {
        "type": "IfThenElse",
        "cond": {"type": "Gt", "a": x, "b": _lit(0)},
        "then": {
            "type": "Max",
            "items": [
                {"type": "Minus", "a": x, "b": _lit(1)},
                _lit(0),
            ],
        },
        "other": {
            "type": "IfThenElse",
            "cond": {"type": "Lt", "a": x, "b": _lit(0)},
            "then": {
                "type": "Min",
                "items": [
                    {"type": "Plus", "items": [x, _lit(1)]},
                    _lit(0),
                ],
            },
            "other": x,
        },
    }


def build_rule() -> dict:
    return {
        "name": "can_native_external_field_decay",
        "comment": (
            "v1.1.0. Native analog of maybe_decay_h/can_ops.rs::decay_h for "
            "external_field (h) -- the ONE quantity that mechanism targets "
            "and this arc had not given a native writer (CAN_MT_SCOPED_"
            "RULES_RESULTS.md Sec4c). Symmetric clamp toward zero (max(h-1,"
            "0) when positive, min(h+1,0) when negative) via pre-existing "
            "Max/Min Terms -- the required generalisation of "
            "can_native_evidence_decay's one-sided integer-floor body, "
            "since external_field is a signed float with no native "
            "accumulation rule (PREREG Sec1b). No same-tick-race guard: "
            "confirmed by direct grep (PREREG Sec0/Sec2) that no native "
            "rule and no Python module (including can_counterfactual.py) "
            "ever writes external_field -- decay is the only writer this "
            "attr ever gets, so there is no reinforcement event to race "
            "against, unlike can_native_evidence_decay's own fix. "
            "Policy-gated: mt_allows(mt, 'allow_h_drift'), the SAME axis "
            "maybe_decay_h/can_native_evidence_decay/can_native_identity_"
            "evidence_decay all use. See CAN_EXTERNAL_FIELD_DECAY_PREREG.md "
            "/ _RESULTS.md."
        ),
        "match_type": "Concept",
        "match": [["mt", "has_concept", "c"]],
        "where": {
            "type": "And",
            "items": [
                {
                    "type": "Gt",
                    "a": _attr("mt", "can_tick"),
                    "b": _attr("c", "external_field_decay_tick"),
                },
                _policy_or(),
            ],
        },
        "effects": [
            [
                "set_attr",
                "c",
                "external_field",
                {"__term__": _clamp_toward_zero_term("c", "external_field")},
            ],
            [
                "set_attr",
                "c",
                "external_field_decay_tick",
                {"__term__": _attr("mt", "can_tick")},
            ],
        ],
    }


def main() -> None:
    with open(SEED_PATH) as f:
        seed = json.load(f)
    rules = seed["rules"]
    new_rule = build_rule()
    replaced = False
    for i, r in enumerate(rules):
        if r.get("name") == new_rule["name"]:
            rules[i] = new_rule
            replaced = True
            break
    if not replaced:
        rules.append(new_rule)
    with open(SEED_PATH, "w") as f:
        json.dump(seed, f, indent=1)
        f.write("\n")
    print("replaced" if replaced else "appended", new_rule["name"], "in", SEED_PATH)


if __name__ == "__main__":
    main()
