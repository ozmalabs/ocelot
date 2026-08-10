"""A String attr is read with `A`, never with `P0`.

Written the same day the bug was written three times: the reflex response
signature, the condensation response comparison, and the model fork. `P0` is
`Plus(Attr, 0.0)` -- the first-class-absence idiom for NUMBERS -- so on a
String it yields 0.0 silently. In the fork that produced a model whose token
was `0.0`, and the world adapter raised `unknown X-15 token: '0.0'` mid-block.

A unit gate is cheap and this class of bug has now cost three runs.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = json.loads(
    (ROOT / "seeds" / "embodied_motor_program.json").read_text(encoding="utf-8")
)
RULES = {rule["name"]: rule for rule in SEED["rules"]}

# Attributes that hold Strings anywhere in this seed.
STRING_ATTRS = ("token", "response_shape", "status", "kind", "faculty", "name")


def _plus_zero_reads(term, key_names, found):
    """Collect keys read through a `Plus(Attr, 0.0)` -- i.e. through `P0`."""
    if isinstance(term, dict):
        if term.get("type") == "Plus":
            items = term.get("items", [])
            attrs = [i for i in items if isinstance(i, dict)
                     and i.get("type") == "Attr"]
            zeros = [i for i in items if isinstance(i, dict)
                     and i.get("type") == "Lit" and i.get("value") == 0.0]
            if attrs and zeros:
                for a in attrs:
                    if a.get("key") in key_names:
                        found.add(a["key"])
        for value in term.values():
            _plus_zero_reads(value, key_names, found)
    elif isinstance(term, list):
        for value in term:
            _plus_zero_reads(value, key_names, found)
    return found


def test_no_rule_reads_a_string_attr_through_p0():
    offenders = {}
    for name, rule in RULES.items():
        found = _plus_zero_reads(rule, STRING_ATTRS, set())
        if found:
            offenders[name] = sorted(found)
    assert offenders == {}, (
        "P0 is Plus(Attr, 0.0) and yields 0.0 on a String, silently. "
        f"Use A(...) instead. Offenders: {offenders}"
    )


def test_the_fork_copies_its_token_as_a_string():
    fork = json.dumps(RULES["emp_fork_regime_local_model"])
    assert '"token"' in fork, "the fork must carry its parent's token"
