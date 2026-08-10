"""Pins the Terms needed to migrate the last EXPERIMENT-composer branches off
Python: the four mechanical (op, target) -> new-rule-JSON appliers in
`domains/edit_ops.py` (`apply_flip_comparison` / `apply_drop_match_edge` /
`apply_add_match_guard` / `apply_swap_term_leaf`), the "structural" twin of
the threshold-shift machinery `tests/test_dialect_experiment_terms.py`
already pinned. This is the documented next step after commit f23a4d21.

Per-applier verdict (empirically checked -- see each section below):

  1. `apply_add_match_guard` -- ALREADY EXPRESSIBLE, no new Term. Wrapping
     `where` in `Eq(Attr(Var(node_var), attr_key), Lit(attr_value))`, and (if
     an old `where` exists) an outer `And([old_where, guard])`, is exactly
     `MkDict` + `IfThenElse` + `Eq` + `Append` -- all pre-existing. Verified
     byte-identical against the Python oracle BEFORE any Rust change in this
     commit (`test_add_match_guard_already_expressible`).

  2. `apply_flip_comparison` / `apply_swap_term_leaf` -- REAL GAP, closed by
     ONE new Term: `RewriteTreeNodes(tree, field, value_map, type_filter)`.
     Both appliers are "walk a Value tree, where a node matches a predicate,
     rewrite ONE field" with a different predicate/field pair --
     `ShiftThresholdLits` (the closest existing sibling) only rewrites a
     NUMERIC value by an arithmetic shift depending on which of two node
     TYPES it is, not a same-shaped string-to-string field remap, so it
     doesn't cover either. `RewriteTreeNodes` generalises that walk:
       - flip: `field="type"`, `type_filter=None` (the field being checked
         IS the field being rewritten), `value_map` holding all four
         Lt/Gt/Lte/Gte pairs -- ONE pass, not four sequential
         re-applications (which would double-flip a node the first pass
         already touched).
       - swap: `type_filter="Attr"`, `field="key"`,
         `value_map={old_key: new_key}`.

  3. `apply_drop_match_edge` -- REAL GAP, closed by ONE new Term:
     `ListDrop(list, index)`. Nothing in the dialect could drop a list
     element by POSITION -- `FilterList` (the closest sibling) only sees the
     element itself in its predicate, never its index, so it can express
     content-based removal but not `rule["match"][index]`. No
     Enumerate/Zip/Range Term exists to fake an index either.

     HONEST RESIDUAL for the next (composer-migration) agent: `ListDrop` is
     a pure MECHANICAL primitive -- it drops whatever index you give it,
     unconditionally (out-of-range is a no-op, but "would leave `match`
     empty" is NOT checked, because that's a SEMANTIC/business-rule
     decision, not a structural one; see CLAUDE.md's primitive-vs-decision
     split). `apply_drop_match_edge`'s full inertness condition is `not (0
     <= index < len(match)) or len(match) <= 1` -- the SECOND half
     ("would leave <1 edge") has to live in the COMPOSER's own `where`-guard,
     not in the Term. This file proves that guard is ALSO already
     expressible with pre-existing Terms (`Count` + `Gte` + `Lt` + `Gt` +
     `And`) -- see `_drop_guard` below -- so the full applier (mechanical
     drop AND business-rule inertness) is graph-native end to end, just
     split across the primitive (mechanical) and the meta-rule's `where`
     (decision), exactly the CLAUDE.md shape.

  4. GENERAL INERTNESS PATTERN (applies to flip/swap, discovered while
     proving the honest-None cases): `RewriteTreeNodes` is a TOTAL function
     -- it always returns a tree, identical to the input when nothing
     matched. So the graph-native "did this genuinely change anything"
     check -- the thing `apply_flip_comparison`/`apply_swap_term_leaf` use
     Python `if not nodes: return None` for -- is simply
     `Not(Eq(rewritten, original))`, using the pre-existing `Eq`/`Not`
     Terms. No bespoke "does a matching node exist anywhere in this tree"
     walker Term is needed; equality-of-result-to-input IS that check,
     for free, for ANY `RewriteTreeNodes` call.

  5. `apply_swap_term_leaf`'s SITE (the top-2 MOST-REFERENCED Attr keys in a
     rule's effects, by frequency) -- a SEPARATE gap from #2 above (#2 only
     proves the REWRITE-given-a-value-map half; this is the COLLECT-and-RANK
     half, which `RewriteTreeNodes` genuinely cannot do -- it only rewrites
     matching nodes in place, it never accumulates a frequency table across a
     tree walk). Closed by ONE new Term: `AttrKeyRanking(tree)` -- walks the
     SAME Dict/Tuple tree `RewriteTreeNodes` walks, tallies every
     `{"type":"Attr"}` node's `key` field occurrence, and returns a
     `(-count, key)`-sorted ranked Tuple, IDENTICAL to
     `domains/edit_ops.py`'s `find_attr_keys`. See section 8 below for the
     FULL site-to-value_map chain (`AttrKeyRanking` -> `Count`-guard ->
     `IndexAt(ranking, 0/1, 0)` -> `MkDict` -> `RewriteTreeNodes`), proven
     byte-identical to `apply_swap_term_leaf` called with `find_attr_keys`'s
     OWN top-2 pick (not a hardcoded key pair, unlike section 5's pilots
     below, which pin the REWRITE mechanism in isolation with an
     already-known key pair).

This file follows the same test-authoring convention as
tests/test_dialect_experiment_terms.py: raw Term-JSON dict lambdas
(V/L/A/MK/AP/DG), never `domains.reflective_faculty`'s composer functions
(capability-envelope pinning, not composer migration -- CLAUDE.md keeps
`_compose_structural_variant` untouched). `domains.edit_ops`'s four `apply_*`
functions ARE imported directly in the pilot tests, read-only, purely as the
REFERENCE ORACLE the graph-native reconstruction is checked against.

The pilots run against REAL rules from the `grid_navigation` seed, read back
via `native.export_rules()` (the exact dialect `_ensure_acting_rule_
provenance` mirrors into `RuleSummary.rule_json`):
  - `hop_descend_gradient` -- the acting rule named throughout the task spec
    (has Lt/Gt comparison nodes in its effects, `row`/`col` Attr keys, a
    non-null `where`, and exactly ONE match edge -- the natural "inert drop"
    case, since dropping its only edge would leave `match` empty).
  - `mark_visited_footprint` -- same seed, TWO match edges (the natural
    "successful drop" case) and no comparison node in its effects at all
    (the natural "inert flip" case).
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
from domains.edit_ops import (
    apply_add_match_guard,
    apply_drop_match_edge,
    apply_flip_comparison,
    apply_swap_term_leaf,
)

# --- Term-JSON builder helpers (test-authoring DATA, not agent logic) -----

V = lambda n: {"type": "Var", "name": n}
L = lambda v: {"type": "Lit", "value": v}
A = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
MK = lambda *kvs: {"type": "MkDict", "items": list(kvs)}
AP = lambda seq, item: {"type": "Append", "seq": seq, "item": item}
DG = lambda d, k: {"type": "DictGet", "dict": d, "key": L(k)}
EMPTY_TUPLE = L([])

_FLIP_VALUE_MAP = MK(L("Lt"), L("Gt"), L("Gt"), L("Lt"), L("Lte"), L("Gte"), L("Gte"), L("Lte"))


@pytest.fixture
def agent():
    """A `grid_navigation`-booted agent -- carries the two real acting rules
    the pilots below target."""
    return WorldAdapter(seeds=("grid_navigation",))


def _eval(a, term):
    return a.inner.evaluate(term, {})


def _exported(a, name):
    rules = a.inner.export_rules()
    hit = next(r for r in rules if isinstance(r, dict) and r.get("name") == name)
    return hit


# ---------------------------------------------------------------------------
# 1) RewriteTreeNodes -- the new general conditional-tree-rewrite Term.
#    Direct-eval unit pins (no rule firing needed).
# ---------------------------------------------------------------------------

def test_rewrite_tree_nodes_flips_comparison_type(agent):
    a = agent
    tree = {"type": "Lt", "a": {"type": "Var", "name": "x"}, "b": {"type": "Lit", "value": 5}}
    out = _eval(a, {"type": "RewriteTreeNodes", "tree": L(tree), "field": L("type"),
                     "value_map": _FLIP_VALUE_MAP, "type_filter": None})
    assert out["type"] == "Gt"
    assert out["a"] == {"type": "Var", "name": "x"}
    assert out["b"] == {"type": "Lit", "value": 5}


def test_rewrite_tree_nodes_recurses_into_nested_structure(agent):
    a = agent
    tree = {"type": "And", "items": [
        {"type": "Lt", "a": {"type": "Var", "name": "x"}, "b": {"type": "Lit", "value": 1}},
        {"type": "Eq", "a": {"type": "Var", "name": "y"}, "b": {"type": "Lit", "value": 2}},
        {"type": "Gt", "a": {"type": "Var", "name": "z"}, "b": {"type": "Lit", "value": 3}},
    ]}
    out = _eval(a, {"type": "RewriteTreeNodes", "tree": L(tree), "field": L("type"),
                     "value_map": _FLIP_VALUE_MAP, "type_filter": None})
    kinds = [item["type"] for item in out["items"]]
    assert kinds == ["Gt", "Eq", "Lt"], "only Lt/Gt flipped; Eq untouched, nesting preserved"


def test_rewrite_tree_nodes_swaps_attr_key_only_when_type_matches(agent):
    a = agent
    vm = MK(L("row"), L("col"))
    attr_node = {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "row"}
    out = _eval(a, {"type": "RewriteTreeNodes", "tree": L(attr_node), "field": L("key"),
                     "value_map": vm, "type_filter": L("Attr")})
    assert out == {"type": "Attr", "node": {"name": "c", "type": "Var"}, "key": "col"}

    # A DIFFERENT node type that happens to have a "key" field matching
    # old_key must NOT be touched -- the type_filter guard is load-bearing
    # (this is exactly what distinguishes swap from a blind field-rename).
    other_node = {"type": "NotAttr", "key": "row"}
    out2 = _eval(a, {"type": "RewriteTreeNodes", "tree": L(other_node), "field": L("key"),
                      "value_map": vm, "type_filter": L("Attr")})
    assert out2 == other_node


def test_rewrite_tree_nodes_is_total_identity_when_nothing_matches(agent):
    """The general inertness pattern: RewriteTreeNodes always returns a
    tree -- unchanged when nothing matches. `Not(Eq(rewritten, original))`
    is the graph-native twin of the Python appliers' `if not nodes: return
    None`, for free, with pre-existing Terms."""
    a = agent
    tree = {"type": "SetAttr", "key": "unrelated", "value": {"type": "Lit", "value": 1}}
    rewritten = {"type": "RewriteTreeNodes", "tree": L(tree), "field": L("type"),
                 "value_map": _FLIP_VALUE_MAP, "type_filter": None}
    assert _eval(a, rewritten) == tree
    changed = _eval(a, {"type": "Not", "arg": {"type": "Eq", "a": rewritten, "b": L(tree)}})
    assert changed is False


# ---------------------------------------------------------------------------
# 2) ListDrop -- the new index-based list-element-removal Term.
# ---------------------------------------------------------------------------

def test_list_drop_removes_the_element_at_index(agent):
    a = agent
    # REPOINTED by prereg A8 (2026-08-04). This assertion used to read
    # `== (("a","b","c"),)` and justify it as "Tuple-valued (Value::Tuple),
    # nested lists decode as nested tuples too" -- but that was the LOSSY
    # `Lit` WIRE, not `ListDrop`'s semantics: `py.rs::pyobj_to_json` put a
    # Python list on the wire as a bare JSON array, which
    # `persist::decode_value` reads as `Value::Tuple`. A Python list now
    # arrives as `Value::List`, so a list in gives a list out.
    out = _eval(a, {"type": "ListDrop", "list": L([["a", "b", "c"], ["d", "e", "f"]]), "index": L(1)})
    assert out == [["a", "b", "c"]], out
    assert type(out) is list and type(out[0]) is list
    # ...and the REFUTING direction, so the collapse cannot come back
    # silently: a TUPLE in still gives a tuple out.
    out_t = _eval(a, {"type": "ListDrop", "list": L((("a", "b", "c"), ("d", "e", "f"))), "index": L(1)})
    assert out_t == (("a", "b", "c"),), out_t
    assert type(out_t) is tuple and type(out_t[0]) is tuple


def test_list_drop_negative_index_counts_from_end(agent):
    a = agent
    out = _eval(a, {"type": "ListDrop", "list": L([10, 20, 30]), "index": L(-1)})
    assert out == [10, 20] and type(out) is list, out       # list  in -> list  out
    out_t = _eval(a, {"type": "ListDrop", "list": L((10, 20, 30)), "index": L(-1)})
    assert out_t == (10, 20) and type(out_t) is tuple, out_t  # tuple in -> tuple out


def test_list_drop_out_of_range_is_a_mechanical_noop(agent):
    """ListDrop is a pure structural primitive: out-of-range is a no-op
    (unchanged elements back), NOT the fuller "would this leave the rule
    with <1 match edge" business-rule inertness -- that belongs in the
    composer's own `where`-guard (see `_drop_guard` / the drop pilots
    below), matching CLAUDE.md's primitive-vs-decision split."""
    a = agent
    out = _eval(a, {"type": "ListDrop", "list": L([1, 2, 3]), "index": L(99)})
    assert out == [1, 2, 3] and type(out) is list, out
    out_t = _eval(a, {"type": "ListDrop", "list": L((1, 2, 3)), "index": L(99)})
    assert out_t == (1, 2, 3) and type(out_t) is tuple, out_t
    # In particular: dropping the ONLY element of a 1-element list DOES
    # remove it mechanically (index 0 is in-range) -- the Term has no
    # opinion about whether that's a semantically valid rule any more.
    out_empty = _eval(a, {"type": "ListDrop", "list": L([["g", "reached", "A"]]), "index": L(0)})
    assert out_empty == [] and type(out_empty) is list, out_empty


# ---------------------------------------------------------------------------
# Shared pilot machinery -- mirrors tests/test_dialect_experiment_terms.py's
# `_make_pilot_scene` / `_pilot_meta_rule` shape exactly: a `VaryTrigger`
# targets a `RuleSummary`'s `rule_json` provenance, a meta-rule reads it back
# via `FromJsonString`, rewrites ONE field, and lands the result as a JSON
# string in a `SeedDelta.add_rules` attr -- gated (fixpoint-idempotent) so it
# composes exactly once.
# ---------------------------------------------------------------------------

def _make_pilot_scene(a, rule_dict, trig_attrs, new_name):
    s = a.s
    rs = s.add_node("RuleSummary", {"name": rule_dict["name"], "rule_json": json.dumps(rule_dict)})
    attrs = dict(trig_attrs)
    attrs["new_name"] = new_name
    attrs["composed"] = 0.0
    trig = s.add_node("VaryTrigger", attrs)
    a.inner.add_edge_unchecked(trig, "targets", rs)
    delta = s.add_node("SeedDelta", {"add_rules": "[]", "remove_rules": "[]"})
    a.inner.add_edge_unchecked(trig, "has_delta", delta)
    return trig, rs, delta


def _passthrough_rule(parsed, override_field, override_expr):
    """Rebuild the FULL exported-rule dict (name/match/where/effects/batch/
    match_type -- every field `native.export_rules()` emits besides
    `active`, which the Python appliers pop) via DictGet passthroughs,
    substituting ONE field. Proven byte-identical round-trip shape (see
    tests/test_dialect_experiment_terms.py's own pilot)."""
    kvs = [L("name"), A(V("trig"), "new_name")]
    for f in ("match", "where", "effects", "batch", "match_type"):
        kvs += [L(f), (override_expr if f == override_field else DG(parsed, f))]
    return MK(*kvs)


def _gated_meta_rule(name, parsed, override_field, override_expr, extra_where=None):
    new_rule = _passthrough_rule(parsed, override_field, override_expr)
    add_rules_json = {"type": "ToJsonString", "value": AP(EMPTY_TUPLE, new_rule)}
    not_yet_composed = {"type": "Lt", "a": {"type": "Plus", "items": [A(V("trig"), "composed"), L(0.0)]}, "b": L(0.5)}
    where_items = [not_yet_composed] if extra_where is None else [not_yet_composed, extra_where]
    return {
        "name": name,
        "match": [["trig", "targets", "rs"], ["trig", "has_delta", "delta"]],
        "where": {"type": "And", "items": where_items},
        "effects": [
            ["set_attr", "delta", "add_rules", {"__term__": add_rules_json}],
            ["set_attr", "trig", "composed", 1.0],
        ],
    }


def _fire(a, meta_rule):
    a.inner.add_rule(meta_rule)
    a.inner.run_rules()


def _minted_variants(a, delta):
    return json.loads(a.s.node(delta)["attrs"]["add_rules"])


# ---------------------------------------------------------------------------
# 3) apply_add_match_guard -- ALREADY EXPRESSIBLE, no new Term (MkDict +
#    IfThenElse + Eq + Append). Byte-identical pilot on hop_descend_gradient.
# ---------------------------------------------------------------------------

def test_add_match_guard_already_expressible(agent):
    a = agent
    hop = _exported(a, "hop_descend_gradient")
    new_name = "hop_descend_gradient_guarded_demo"
    trig, rs, delta = _make_pilot_scene(a, hop, {}, new_name)

    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    old_where = DG(parsed, "where")
    guard = MK(L("type"), L("Eq"),
               L("a"), MK(L("type"), L("Attr"),
                          L("node"), MK(L("type"), L("Var"), L("name"), L("game")),
                          L("key"), L("nav_mode")),
               L("b"), MK(L("type"), L("Lit"), L("value"), L("guarded_demo")))
    new_where = {"type": "IfThenElse",
                 "cond": {"type": "Eq", "a": old_where, "b": L(None)},
                 "then": guard,
                 "other": MK(L("type"), L("And"), L("items"), AP(AP(EMPTY_TUPLE, old_where), guard))}

    _fire(a, _gated_meta_rule("compose_guard_pilot", parsed, "where", new_where))
    variants = _minted_variants(a, delta)
    assert len(variants) == 1

    oracle = apply_add_match_guard(copy.deepcopy(hop), "game", "nav_mode", "guarded_demo", new_name)
    assert variants[0] == oracle, (
        f"graph-native:\n{json.dumps(variants[0], indent=2)}\n\npython reference:\n{json.dumps(oracle, indent=2)}"
    )


def test_add_match_guard_wraps_existing_where_with_and(agent):
    """Direct-eval pin of the OTHER branch (old_where is None) -- the
    'always succeeds structurally' applier has no inert case, so this is a
    synthetic minimal rule rather than a real-seed pilot."""
    a = agent
    rule = {"name": "synthetic_no_where", "match": [["g", "at", "c"]], "where": None,
            "effects": [["set_attr", "g", "x", 1.0]]}
    rs = a.s.add_node("RuleSummary", {"name": rule["name"], "rule_json": json.dumps(rule)})
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    old_where = DG(parsed, "where")
    guard = MK(L("type"), L("Eq"), L("a"), L("dummy"), L("b"), L("dummy"))
    new_where = {"type": "IfThenElse", "cond": {"type": "Eq", "a": old_where, "b": L(None)},
                 "then": guard, "other": MK(L("type"), L("And"), L("items"), AP(AP(EMPTY_TUPLE, old_where), guard))}
    out = a.inner.evaluate(new_where, {"rs": rs})
    assert out == {"type": "Eq", "a": "dummy", "b": "dummy"}, "old_where is None -> just the guard, no And wrapper"


# ---------------------------------------------------------------------------
# 4) apply_flip_comparison -- REAL GAP, closed by RewriteTreeNodes.
#    Success pilot: hop_descend_gradient (has Lt/Gt in effects).
#    Inert pilot:   mark_visited_footprint (no comparison node at all).
# ---------------------------------------------------------------------------

def _flip_pilot_pieces(parsed):
    effects = DG(parsed, "effects")
    flipped = {"type": "RewriteTreeNodes", "tree": effects, "field": L("type"),
               "value_map": _FLIP_VALUE_MAP, "type_filter": None}
    changed = {"type": "Not", "arg": {"type": "Eq", "a": flipped, "b": effects}}
    return flipped, changed


def test_flip_comparison_pilot_matches_python_reference(agent):
    a = agent
    hop = _exported(a, "hop_descend_gradient")
    new_name = "hop_descend_gradient_flipped_demo"
    trig, rs, delta = _make_pilot_scene(a, hop, {}, new_name)
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    flipped, changed = _flip_pilot_pieces(parsed)

    _fire(a, _gated_meta_rule("compose_flip_pilot", parsed, "effects", flipped, extra_where=changed))
    variants = _minted_variants(a, delta)
    assert len(variants) == 1

    oracle = apply_flip_comparison(copy.deepcopy(hop), new_name)
    assert variants[0] == oracle, (
        f"graph-native:\n{json.dumps(variants[0], indent=2)}\n\npython reference:\n{json.dumps(oracle, indent=2)}"
    )
    # Sanity: the flip genuinely happened.
    inner_cond = variants[0]["effects"][0][3]["__term__"]["cond"]
    assert inner_cond["type"] == "Gt", "Lt(row-adjacent gate) flipped to Gt"


def test_flip_comparison_pilot_is_honestly_inert_when_no_comparison(agent):
    """mark_visited_footprint's effects contain no Lt/Gt/Lte/Gte at all --
    the meta-rule's `changed` guard never fires, matching the Python
    oracle's `None` exactly (no SeedDelta gets populated)."""
    a = agent
    mvf = _exported(a, "mark_visited_footprint")
    new_name = "mvf_flip_demo"
    trig, rs, delta = _make_pilot_scene(a, mvf, {}, new_name)
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    flipped, changed = _flip_pilot_pieces(parsed)

    _fire(a, _gated_meta_rule("compose_flip_pilot", parsed, "effects", flipped, extra_where=changed))
    assert _minted_variants(a, delta) == []
    assert a.s.node(trig)["attrs"]["composed"] == 0.0, "never fired -- honestly inert"

    oracle = apply_flip_comparison(copy.deepcopy(mvf), new_name)
    assert oracle is None


# ---------------------------------------------------------------------------
# 5) apply_swap_term_leaf -- REAL GAP, closed by the SAME RewriteTreeNodes.
#    Success pilot: hop_descend_gradient, row -> col (both real Attr keys).
#    Inert pilot:   a key that doesn't occur in hop's effects at all.
# ---------------------------------------------------------------------------

def _swap_pilot_pieces(parsed, old_key, new_key):
    effects = DG(parsed, "effects")
    vm = MK(L(old_key), L(new_key))
    swapped = {"type": "RewriteTreeNodes", "tree": effects, "field": L("key"),
               "value_map": vm, "type_filter": L("Attr")}
    changed = {"type": "Not", "arg": {"type": "Eq", "a": swapped, "b": effects}}
    return swapped, changed


def test_swap_term_leaf_pilot_matches_python_reference(agent):
    a = agent
    hop = _exported(a, "hop_descend_gradient")
    new_name = "hop_descend_gradient_swapped_demo"
    trig, rs, delta = _make_pilot_scene(a, hop, {}, new_name)
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    swapped, changed = _swap_pilot_pieces(parsed, "row", "col")

    _fire(a, _gated_meta_rule("compose_swap_pilot", parsed, "effects", swapped, extra_where=changed))
    variants = _minted_variants(a, delta)
    assert len(variants) == 1

    oracle = apply_swap_term_leaf(copy.deepcopy(hop), "row", "col", new_name)
    assert variants[0] == oracle, (
        f"graph-native:\n{json.dumps(variants[0], indent=2)}\n\npython reference:\n{json.dumps(oracle, indent=2)}"
    )
    assert '"key": "col"' in json.dumps(variants[0]) and '"key": "row"' not in json.dumps(variants[0])


def test_swap_term_leaf_pilot_is_honestly_inert_when_key_absent(agent):
    a = agent
    hop = _exported(a, "hop_descend_gradient")
    new_name = "hop_swap_absent_demo"
    trig, rs, delta = _make_pilot_scene(a, hop, {}, new_name)
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    swapped, changed = _swap_pilot_pieces(parsed, "nonexistent_key_xyz", "col")

    _fire(a, _gated_meta_rule("compose_swap_pilot", parsed, "effects", swapped, extra_where=changed))
    assert _minted_variants(a, delta) == []

    oracle = apply_swap_term_leaf(copy.deepcopy(hop), "nonexistent_key_xyz", "col", new_name)
    assert oracle is None


# ---------------------------------------------------------------------------
# 6) apply_drop_match_edge -- REAL GAP, closed by ListDrop for the mechanical
#    half; the "would leave <1 edge" business-rule half is a `where`-guard
#    built from PRE-EXISTING Terms (Count/Gte/Lt/Gt/And) -- `_drop_guard`.
#    Success pilot: mark_visited_footprint, drop index 1 (2 match edges).
#    Inert pilot:   hop_descend_gradient, drop index 0 (only 1 match edge).
# ---------------------------------------------------------------------------

def _drop_pilot_pieces(parsed, index_expr):
    match = DG(parsed, "match")
    dropped = {"type": "ListDrop", "list": match, "index": index_expr}
    count = {"type": "Count", "source": match}
    # Mirrors apply_drop_match_edge's guard EXACTLY:
    #   0 <= index < len(match) and len(match) > 1
    guard = {"type": "And", "items": [
        {"type": "Gte", "a": index_expr, "b": L(0)},
        {"type": "Lt", "a": index_expr, "b": count},
        {"type": "Gt", "a": count, "b": L(1)},
    ]}
    return dropped, guard


def test_drop_match_edge_pilot_matches_python_reference(agent):
    a = agent
    mvf = _exported(a, "mark_visited_footprint")
    assert len(mvf["match"]) == 2, "the real 2-edge rule this pilot targets"
    new_name = "mvf_drop_demo"
    trig, rs, delta = _make_pilot_scene(a, mvf, {"index": 1}, new_name)
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    idx = A(V("trig"), "index")
    dropped, guard = _drop_pilot_pieces(parsed, idx)

    _fire(a, _gated_meta_rule("compose_drop_pilot", parsed, "match", dropped, extra_where=guard))
    variants = _minted_variants(a, delta)
    assert len(variants) == 1

    oracle = apply_drop_match_edge(copy.deepcopy(mvf), 1, new_name)
    assert variants[0] == oracle, (
        f"graph-native:\n{json.dumps(variants[0], indent=2)}\n\npython reference:\n{json.dumps(oracle, indent=2)}"
    )
    assert variants[0]["match"] == [["game", "reached", "A"]]


def test_drop_match_edge_pilot_is_honestly_inert_when_it_would_empty_match(agent):
    """hop_descend_gradient has exactly ONE match edge -- dropping it would
    leave `match` empty, so both the Python oracle AND the graph-native
    guard refuse (the guard's `Gt(count, 1)` conjunct is False)."""
    a = agent
    hop = _exported(a, "hop_descend_gradient")
    assert len(hop["match"]) == 1, "the real 1-edge rule this inert pilot targets"
    new_name = "hop_drop_demo"
    trig, rs, delta = _make_pilot_scene(a, hop, {"index": 0}, new_name)
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    idx = A(V("trig"), "index")
    dropped, guard = _drop_pilot_pieces(parsed, idx)

    _fire(a, _gated_meta_rule("compose_drop_pilot", parsed, "match", dropped, extra_where=guard))
    assert _minted_variants(a, delta) == []
    assert a.s.node(trig)["attrs"]["composed"] == 0.0

    oracle = apply_drop_match_edge(copy.deepcopy(hop), 0, new_name)
    assert oracle is None

    # And the RAW mechanical ListDrop (no guard) WOULD have dropped it --
    # proving the inertness lives in the guard, not the primitive (the
    # residual documented at the top of this file).
    rs2 = a.s.add_node("RuleSummary2", {"rule_json": json.dumps(hop)})
    match_only = {"type": "DictGet",
                  "dict": {"type": "FromJsonString", "text": A(V("rs2"), "rule_json")},
                  "key": L("match")}
    mechanical = a.inner.evaluate({"type": "ListDrop", "list": match_only, "index": L(0)}, {"rs2": rs2})
    assert mechanical == (), "the Term itself has no opinion -- it just drops"


# ---------------------------------------------------------------------------
# 7) Idempotence -- the same fixpoint-guard discipline
#    test_dialect_experiment_terms.py's pilot pins, re-proven for one of the
#    new Terms' meta-rules (flip).
# ---------------------------------------------------------------------------

def test_flip_pilot_idempotent_no_double_compose(agent):
    a = agent
    hop = _exported(a, "hop_descend_gradient")
    new_name = "hop_flip_idem_demo"
    trig, rs, delta = _make_pilot_scene(a, hop, {}, new_name)
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    flipped, changed = _flip_pilot_pieces(parsed)
    a.inner.add_rule(_gated_meta_rule("compose_flip_pilot", parsed, "effects", flipped, extra_where=changed))
    for _ in range(5):
        a.s.tick()
    first = a.s.node(delta)["attrs"]["add_rules"]
    for _ in range(5):
        a.s.tick()
    assert a.s.node(delta)["attrs"]["add_rules"] == first
    assert len(json.loads(first)) == 1


# ---------------------------------------------------------------------------
# 8) AttrKeyRanking -- the swap-SITE finder that closes the LAST
#    experiment-composer residual (apply_swap_term_leaf's site pick, see
#    module docstring point 5). Direct-eval pin against find_attr_keys,
#    then the FULL site-to-value_map chain (AttrKeyRanking -> Count-guard ->
#    IndexAt(ranking, 0/1, 0) -> MkDict -> RewriteTreeNodes) proven
#    byte-identical to apply_swap_term_leaf called with find_attr_keys' OWN
#    top-2 pick -- the exact chain seeds/composer_experiment_graph.json's
#    compose_experiment_structure_graph swap branch uses.
# ---------------------------------------------------------------------------
from domains.edit_ops import find_attr_keys  # noqa: E402  (import after module setup, matches file's own style)


def test_attr_key_ranking_matches_find_attr_keys_on_a_real_rule(agent):
    a = agent
    hop = _exported(a, "hop_descend_gradient")
    ranking = _eval(a, {"type": "AttrKeyRanking", "tree": L(hop.get("effects"))})
    oracle = find_attr_keys(hop.get("effects"))
    assert list(ranking) == oracle, (ranking, oracle)
    # Sanity: hop_descend_gradient genuinely has >=2 distinct Attr keys (the
    # non-degenerate case the swap SITE chain below depends on).
    assert len(oracle) >= 2


def _swap_site_pieces(parsed):
    """The FULL site-to-value_map chain: AttrKeyRanking(effects) -> guard
    on >=2 distinct keys -> top-1/top-2 via IndexAt(ranking, i, 0) ->
    {old_key: new_key} via MkDict -> RewriteTreeNodes(effects, type_filter=
    "Attr", field="key", value_map). Mirrors seeds/composer_experiment_
    graph.json's compose_experiment_structure_graph swap branch verbatim
    (same Let-nesting shape, different var names -- this file's own
    convention keeps raw dict literals, no Let/LetT helper needed since
    each piece is only referenced once here)."""
    effects = DG(parsed, "effects")
    ranking = {"type": "AttrKeyRanking", "tree": effects}
    has_two_keys = {"type": "Gt", "a": {"type": "Count", "source": ranking}, "b": L(1)}
    old_key = {"type": "IndexAt", "seq": {"type": "IndexAt", "seq": ranking, "index": L(0)}, "index": L(0)}
    new_key = {"type": "IndexAt", "seq": {"type": "IndexAt", "seq": ranking, "index": L(1)}, "index": L(0)}
    vm = MK(old_key, new_key)
    swapped = {"type": "RewriteTreeNodes", "tree": effects, "field": L("key"),
               "value_map": vm, "type_filter": L("Attr")}
    return has_two_keys, swapped


def test_swap_site_chain_matches_python_reference_on_hop_descend_gradient(agent):
    """THE CRUX: the graph-native SITE-COMPUTATION chain (AttrKeyRanking ->
    IndexAt -> MkDict -> RewriteTreeNodes), fed hop_descend_gradient's REAL
    effects tree, picks the SAME top-2 keys find_attr_keys picks and
    produces a rule byte-identical to apply_swap_term_leaf called with that
    OWN pick -- not a hardcoded key pair (unlike section 5's isolated
    REWRITE-mechanism pilot above)."""
    a = agent
    hop = _exported(a, "hop_descend_gradient")
    new_name = "hop_descend_gradient_swap_site_demo"
    trig, rs, delta = _make_pilot_scene(a, hop, {}, new_name)
    parsed = {"type": "FromJsonString", "text": A(V("rs"), "rule_json")}
    has_two_keys, swapped = _swap_site_pieces(parsed)

    _fire(a, _gated_meta_rule("compose_swap_site_pilot", parsed, "effects", swapped, extra_where=has_two_keys))
    variants = _minted_variants(a, delta)
    assert len(variants) == 1

    keys_found = find_attr_keys(hop.get("effects"))
    old_key, new_key = keys_found[0][0], keys_found[1][0]
    oracle = apply_swap_term_leaf(copy.deepcopy(hop), old_key, new_key, new_name)
    assert variants[0] == oracle, (
        f"graph-native:\n{json.dumps(variants[0], indent=2)}\n\npython reference:\n{json.dumps(oracle, indent=2)}"
    )
    assert f'"key": "{new_key}"' in json.dumps(variants[0])
