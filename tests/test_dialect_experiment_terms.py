"""Pins the four Terms added to unblock the EXPERIMENT composer
(`domains/reflective_faculty.py::_compose_experiment_rule` +
`_compose_acting_variant`/`_find_threshold_lits`/`_shift_rule_thresholds`) --
the one composer branch the composer-migration report (commit 5e21b1eb) left
in Python because its compose-time work "exceeds the Term dialect": dynamic
JSON-string construction, recursive Term-tree structural rewrite, and
provenance-Argmax result splicing.

Per-gap verdict (see the task write-up this file accompanies for full
evidence):

  1. Dynamic JSON-string construction -- REAL GAP. `MkDict`/`Append` build a
     graph-native `Value::Dict`/`Tuple`; `domains/experiment_dispatch.py`'s
     `json.loads(delta.add_rules)` needs an actual STRING. `ToJsonString`
     closes it.

  2. Recursive Term-tree structural rewrite -- REAL GAP. Nothing in the
     dialect could walk a Value tree and rewrite matched leaves.
     `FromJsonString` (parse a JSON-string provenance attr back into
     Term-tree land) + `ShiftThresholdLits` (the exact
     `_find_threshold_lits`/`_shift_rule_thresholds` walk, graph-native)
     close it. Closing this gap surfaced a THIRD, narrower one along the
     way: nothing in the dialect could read a field back OUT of a Dict
     VALUE at Term-eval time -- `Attr` reads graph-Node attrs only
     (`Attr(some_dict_value, key)` is always `Value::None`). `DictGet` (the
     Dict-value twin of `Attr`) closes it; without it, `FromJsonString`'s
     own output (and `MkDict`'s) would be a write-only/opaque Value with no
     way to pull `match`/`where`/`effects` back out for reassembly.

  3. Provenance-Argmax result splicing -- ALREADY EXPRESSIBLE, no new Term.
     `domains/reflective_faculty.py::_compose_experiment_rule`'s 'vary'
     branch already embeds `Argmax(Filter(NodesOfType("SeedSummary"), ...),
     ...)` + `Attr(best, "seed_id")` as a HELD Term inside a minted rule's
     own `effects` (the `skip_seeds_expr` -> `{"__term__": skip_seeds_expr}`
     SetAttr arg) -- evaluated at RULE FIRE time, not pre-computed by Python.
     `test_provenance_argmax_splice_already_works` re-proves the mechanism
     directly (Argmax over SeedSummary provenance, filtered + scored by
     StringIndexOf/Sum text overlap, splicing the picked node's own `seed_id`
     attr into a freshly-minted node) using only pre-existing Terms.

This file follows the same test-authoring convention as
tests/test_rule_minting_dialect.py: raw Term-JSON dict lambdas (V/L/Attr/...),
never `domains.reflective_faculty`'s composer functions themselves (this is
capability-envelope pinning, not composer migration -- CLAUDE.md keeps this
file's target reflective_faculty.py's `_compose_experiment_rule` family
untouched). `_shift_rule_thresholds` IS imported directly in the final pilot
test, read-only, purely as the REFERENCE oracle the graph-native
reconstruction is checked against.
"""
from __future__ import annotations

import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

from substrate.world_adapter import WorldAdapter
import substrate_rs as srs

# --- Term-JSON builder helpers (test-authoring DATA, not agent logic) -----

V = lambda n: {"type": "Var", "name": n}
L = lambda v: {"type": "Lit", "value": v}
A = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
MK = lambda *kvs: {"type": "MkDict", "items": list(kvs)}
AP = lambda seq, item: {"type": "Append", "seq": seq, "item": item}
EMPTY_TUPLE = L([])


@pytest.fixture
def agent():
    return WorldAdapter(seeds=())


def _eval(a, term):
    return a.inner.evaluate(term, {})


# ---------------------------------------------------------------------------
# 1) ToJsonString -- MkDict/Append-built structure -> a genuine JSON string.
# ---------------------------------------------------------------------------

def test_to_json_string_serialises_mkdict_append_structure(agent):
    a = agent
    tree = MK(L("name"), L("shifted_rule"),
              L("items"), AP(AP(EMPTY_TUPLE, L(1)), L(2)))
    out = _eval(a, {"type": "ToJsonString", "value": tree})
    assert isinstance(out, str)
    parsed = json.loads(out)
    assert parsed == {"name": "shifted_rule", "items": [1, 2]}


def test_to_json_string_builder_matches_raw_dict(agent):
    """The Python builder (`substrate_rs.ToJsonString`) produces the exact
    same wire dict as the raw Term-JSON -- both evaluate identically."""
    a = agent
    built = srs.ToJsonString(srs.MkDict((srs.Lit("k"), srs.Lit(1))))
    raw = {"type": "ToJsonString", "value": MK(L("k"), L(1))}
    assert built.to_dict() == raw
    assert json.loads(_eval(a, built.to_dict())) == {"k": 1}


# ---------------------------------------------------------------------------
# 2) FromJsonString -- inverse of ToJsonString; round-trips through it.
# ---------------------------------------------------------------------------

def test_from_json_string_parses_nested_structure(agent):
    a = agent
    text = json.dumps({"type": "Lt", "a": {"type": "Var", "name": "x"},
                        "b": {"type": "Lit", "value": 3}})
    parsed = {"type": "FromJsonString", "text": L(text)}
    # Read back a couple of leaves through DictGet (the Dict-VALUE field
    # reader -- `Attr` only reads graph-Node attrs, so `Attr(parsed, ...)`
    # would always be None here) to prove it's genuinely a graph-native
    # Dict, not just an opaque parsed blob.
    ty = _eval(a, {"type": "DictGet", "dict": parsed, "key": L("type")})
    assert ty == "Lt"
    b_value = _eval(a, {"type": "DictGet",
                         "dict": {"type": "DictGet", "dict": parsed, "key": L("b")},
                         "key": L("value")})
    assert b_value == 3


def test_to_json_then_from_json_round_trips(agent):
    a = agent
    tree = MK(L("a"), L(1), L("b"), AP(AP(EMPTY_TUPLE, L("x")), L("y")))
    as_string = {"type": "ToJsonString", "value": tree}
    parsed = {"type": "FromJsonString", "text": as_string}
    a_val = _eval(a, {"type": "DictGet", "dict": parsed, "key": L("a")})
    assert a_val == 1


# ---------------------------------------------------------------------------
# 3) ShiftThresholdLits -- the _find_threshold_lits/_shift_rule_thresholds
#    structural walk, graph-native.
# ---------------------------------------------------------------------------

def test_shift_threshold_lits_shifts_lt_and_gt_only(agent):
    a = agent
    effects_tree = MK(
        L("type"), L("And"),
        L("items"), AP(AP(AP(EMPTY_TUPLE,
            MK(L("type"), L("Lt"), L("a"), MK(L("type"), L("Var"), L("name"), L("x")),
               L("b"), MK(L("type"), L("Lit"), L("value"), L(5)))),
            MK(L("type"), L("Gt"), L("a"), MK(L("type"), L("Var"), L("name"), L("y")),
               L("b"), MK(L("type"), L("Lit"), L("value"), L(-2)))),
            MK(L("type"), L("Eq"), L("a"), MK(L("type"), L("Var"), L("name"), L("z")),
               L("b"), MK(L("type"), L("Lit"), L("value"), L(9)))),
    )
    shifted = _eval(a, {"type": "ShiftThresholdLits", "tree": effects_tree, "shift": L(1.5)})
    items = shifted["items"]
    assert len(items) == 3
    assert items[0]["b"]["value"] == 3.5    # Lt: 5 - 1.5
    assert items[1]["b"]["value"] == -0.5   # Gt: -2 + 1.5
    assert items[2]["b"]["value"] == 9      # Eq: untouched (not Lt/Gt)


# ---------------------------------------------------------------------------
# 4) Provenance-Argmax result splicing -- ALREADY EXPRESSIBLE (no new Term).
#    Re-proves the mechanism `_compose_experiment_rule`'s 'vary' branch
#    already relies on (skip_seeds_expr), embedded in a fired rule's own
#    effects -- not pre-evaluated by Python ahead of the rule firing.
# ---------------------------------------------------------------------------

def test_provenance_argmax_splice_already_works(agent):
    a = agent
    s = a.s
    s.add_node("SeedSummary", {"seed_id": "seed_alpha", "keywords_text": "physics motion gravity",
                                "skippable": 1.0})
    s.add_node("SeedSummary", {"seed_id": "seed_beta", "keywords_text": "language grammar syntax",
                                "skippable": 1.0})
    axis = s.add_node("CapabilityAxis", {"residual_predicates": ["language", "syntax"], "induced": True})
    a.inner.add_edge_unchecked(a.agent, "knows_axis", axis)

    words = A(V("axis"), "residual_predicates")
    overlap = lambda node_t: {"type": "Sum", "source": words, "var_name": "w",
        "value": {"type": "IfThenElse",
                  "cond": {"type": "Gte", "a": {"type": "StringIndexOf",
                                                 "haystack": A(node_t, "keywords_text"), "needle": V("w")},
                           "b": L(0)},
                  "then": L(1), "other": L(0)}}
    candidates = {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "SeedSummary"},
                  "var_name": "s", "predicate": {"type": "Eq", "a": A(V("s"), "skippable"), "b": L(1.0)}}
    best = {"type": "Argmax", "source": candidates, "var_name": "s", "value": overlap(V("s")), "default": None}
    skip_id_expr = {"type": "Let", "name": "best", "value": best,
                     "body": {"type": "IfThenElse",
                              "cond": {"type": "Eq", "a": V("best"), "b": L(None)},
                              "then": L(""),
                              "other": {"type": "IfThenElse",
                                        "cond": {"type": "Gt", "a": overlap(V("best")), "b": L(0.0)},
                                        "then": A(V("best"), "seed_id"), "other": L("")}}}

    rule = {
        "name": "test_provenance_splice",
        "match": [["agent", "knows_axis", "axis"]],
        "where": {"type": "Not", "arg": {"type": "Exists",
                  "source": {"type": "Neighbours", "node": V("axis"), "edge_type": "spliced"},
                  "var_name": "_i", "predicate": L(True)}},
        "effects": [
            ["add_node", "out", "Picked", {"done": 0.0}],
            ["set_attr", "out", "seed_id", {"__term__": skip_id_expr}],
            ["add_edge", "axis", "spliced", "out"],
        ],
    }
    a.inner.add_rule(rule)
    a.inner.run_rules()

    picked = list(s.nodes(type="Picked"))
    assert len(picked) == 1, "gated (fixpoint guard) -- exactly one splice, not an ungated flood"
    assert s.node(picked[0])["attrs"]["seed_id"] == "seed_beta", (
        "seed_beta's keywords ('language grammar syntax') genuinely overlap the axis's "
        "residual_predicates (['language','syntax']); seed_alpha's don't -- Argmax picked "
        "the real winner, not an arbitrary/first node")


# ---------------------------------------------------------------------------
# 5) THE PILOT -- a graph-resident meta-rule mints a SeedDelta whose
#    add_rules JSON string is a genuinely-constructed shifted-threshold
#    variant of a target rule, built ENTIRELY by Terms end to end
#    (FromJsonString + ShiftThresholdLits + ToJsonString), and the result
#    parses to the SAME shape `_shift_rule_thresholds` produces in Python.
#    This is the previously-impossible experiment-composer operation.
# ---------------------------------------------------------------------------

# The target "acting" rule -- shaped like hop_descend_gradient's direction
# gates (Lt(dx,0)/Gt(dx,0)), small enough to keep the pilot self-contained.
_TARGET_RULE = {
    "name": "hop_descend_gradient_demo",
    "match": [["g", "at", "c"]],
    "where": None,
    "effects": [
        ["set_attr", "g", "chosen_action", {"__term__": {
            "type": "IfThenElse",
            "cond": {"type": "Lt", "a": {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "dx"},
                     "b": {"type": "Lit", "value": 0}},
            "then": {"type": "Lit", "value": "left"},
            "other": {"type": "IfThenElse",
                      "cond": {"type": "Gt", "a": {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "dx"},
                               "b": {"type": "Lit", "value": 0}},
                      "then": {"type": "Lit", "value": "right"},
                      "other": {"type": "Lit", "value": "stay"}}}}],
    ],
}


def _make_pilot_scene(a, shift, new_name):
    s = a.s
    rs = s.add_node("RuleSummary", {"name": _TARGET_RULE["name"], "rule_json": json.dumps(_TARGET_RULE)})
    trig = s.add_node("VaryTrigger", {"shift": shift, "new_name": new_name, "composed": 0.0})
    a.inner.add_edge_unchecked(trig, "targets", rs)
    delta = s.add_node("SeedDelta", {"add_rules": "[]", "remove_rules": "[]"})
    a.inner.add_edge_unchecked(trig, "has_delta", delta)
    return trig, rs, delta


def _pilot_meta_rule():
    # `parsed` evaluates to a Dict VALUE (not a graph Node) -- its fields
    # are read with `DictGet`, the Dict-value twin of `Attr` (`Attr` only
    # reads graph-Node attrs; `A(V("rs"), "rule_json")` below is legitimate
    # Attr usage because `rs` IS a real Node).
    DG = lambda d, k: {"type": "DictGet", "dict": d, "key": L(k)}
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    effects_tree = DG(parsed, "effects")
    shifted_effects = {"type": "ShiftThresholdLits", "tree": effects_tree, "shift": A(V("trig"), "shift")}
    shifted_rule_dict = MK(
        L("name"), A(V("trig"), "new_name"),
        L("match"), DG(parsed, "match"),
        L("where"), DG(parsed, "where"),
        L("effects"), shifted_effects,
    )
    add_rules_list = AP(EMPTY_TUPLE, shifted_rule_dict)
    add_rules_json = {"type": "ToJsonString", "value": add_rules_list}
    return {
        "name": "compose_acting_variant_pilot",
        "match": [["trig", "targets", "rs"], ["trig", "has_delta", "delta"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A(V("trig"), "composed"), L(0.0)]}, "b": L(0.5)},
        "effects": [
            ["set_attr", "delta", "add_rules", {"__term__": add_rules_json}],
            ["set_attr", "trig", "composed", 1.0],
        ],
    }


def test_pilot_shifted_variant_matches_python_reference(agent):
    """THE DELIVERABLE: a graph-resident meta-rule performs the exact
    operation `_compose_acting_variant`/`_shift_rule_thresholds` currently
    do in Python -- reading a RuleSummary-shaped JSON-string provenance
    attr, shifting its Lt/Gt thresholds, and landing the result in a
    SeedDelta's `add_rules` JSON-string attr -- using ONLY Terms
    (FromJsonString + ShiftThresholdLits + ToJsonString + MkDict + Append),
    zero Python decision logic at fire time."""
    a = agent
    shift = 3.0
    new_name = _TARGET_RULE["name"] + "_variant_demo"
    trig, rs, delta = _make_pilot_scene(a, shift, new_name)
    a.inner.add_rule(_pilot_meta_rule())
    a.inner.run_rules()

    add_rules_json = a.s.node(delta)["attrs"]["add_rules"]
    assert isinstance(add_rules_json, str), "add_rules must be a genuine JSON STRING, not a graph Dict/Tuple"
    graph_native_variants = json.loads(add_rules_json)
    assert len(graph_native_variants) == 1
    graph_native_variant = graph_native_variants[0]

    # The Python reference oracle -- read-only import, not modified, not
    # invoked as part of the pilot's own rule firing above.
    from domains.reflective_faculty import _shift_rule_thresholds
    python_reference = _shift_rule_thresholds(copy.deepcopy(_TARGET_RULE), shift, new_name)
    # _shift_rule_thresholds pops "active" (not present on our target rule
    # either) -- both sides are directly comparable dicts.
    assert python_reference.pop("active", None) is None

    assert graph_native_variant == python_reference, (
        f"graph-native:\n{json.dumps(graph_native_variant, indent=2)}\n\n"
        f"python reference:\n{json.dumps(python_reference, indent=2)}"
    )

    # Sanity: the shift genuinely happened (not a no-op / accidental identity).
    assert graph_native_variant["name"] == new_name
    inner_cond = graph_native_variant["effects"][0][3]["__term__"]["cond"]
    outer_else_cond = graph_native_variant["effects"][0][3]["__term__"]["other"]["cond"]
    assert inner_cond["b"]["value"] == -3.0        # Lt(dx, 0) -> Lt(dx, 0 - 3)
    assert outer_else_cond["b"]["value"] == 3.0     # Gt(dx, 0) -> Gt(dx, 0 + 3)


def test_pilot_idempotent_no_double_compose(agent):
    a = agent
    trig, rs, delta = _make_pilot_scene(a, 2.0, "demo_variant_idem")
    a.inner.add_rule(_pilot_meta_rule())
    for _ in range(5):
        a.s.tick()
    first = a.s.node(delta)["attrs"]["add_rules"]
    for _ in range(5):
        a.s.tick()
    assert a.s.node(delta)["attrs"]["add_rules"] == first
    assert len(json.loads(first)) == 1
