"""edit_ops — THE STRUCTURAL EDIT-OPERATOR ALGEBRA: mechanical appliers over an
exported rule's JSON (export_rules()/add_rule() dialect). Widens the self-
experiment loop's variant range from THRESHOLD SHIFTS (`_shift_rule_thresholds`
in domains/reflective_faculty.py — changes a decision's MAGNITUDE) to
STRUCTURAL edits (changes a decision's SHAPE): flip a comparison's direction,
drop a match-pattern edge, add an extra match guard, swap which attribute key
a decision reads.

Each `apply_*` function is a PURE, mechanical (op, target) -> new-rule-JSON
transform — the same "structural substitution, no interpretation of what a
threshold/attr MEANS" discipline `_find_threshold_lits` / `_shift_rule_
thresholds` already follow (CLAUDE.md: primitives live in Rust/mechanical
Python, COMPOSITION — which op, where — is the agent's, authored in
domains/reflective_faculty.py's `_compose_structural_variant` via a held
Argmax Term over EditOp x site, never a Python if/else picking the op).

Every applier:
  - deep-copies its input (the original rule dict is never mutated);
  - returns a NEW rule dict (renamed) on success;
  - returns None when the requested edit is INERT for this rule (a real,
    honestly-reported discovery — e.g. dropping a rule's only match edge, or
    flipping a rule with no comparison node at all) — never fabricates a
    edit that isn't actually there to make.

Scope: `apply_flip_comparison` / `apply_swap_term_leaf` are scoped to
`rule['effects']` only (never `match`/`where`) — same reasoning
`_find_threshold_lits` documents: a shift can only change WHAT a rule
DECIDES, never WHETHER it fires. `apply_drop_match_edge` / `apply_add_match_
guard` are the two ops that DO touch firing conditions (match/where) — by
design, the other side of the algebra from the effects-only threshold/swap
family.
"""
from __future__ import annotations

import copy as _copy
from typing import Any, Optional

# Lt<->Gt and Lte<->Gte are the two comparison-direction pairs the Rust term
# evaluator exposes (runners/dsl/src/term.rs: Lt/Lte/Gt/Gte) — flipping type
# while leaving a/b untouched reverses which side of the comparison is
# preferred (a Lt(x, 0) direction gate becomes a Gt(x, 0) gate: "prefer more"
# becomes "prefer less").
_FLIP_PAIRS = {"Lt": "Gt", "Gt": "Lt", "Lte": "Gte", "Gte": "Lte"}


# ---------------------------------------------------------------------------
# structural scans (read-only; find sites an applier could act on)
# ---------------------------------------------------------------------------
def find_comparison_nodes(node: Any) -> list:
    """Recursive scan: every `{"type": "Lt"|"Gt"|"Lte"|"Gte", ...}` node
    reachable inside `node` — the SAME shape `reflective_faculty._find_
    threshold_lits` uses, generalised to all four comparison directions and
    without requiring `b` to be a numeric Lit (a flip doesn't care what's
    compared, only which way). Returns references INTO `node` (callers pass a
    deep-copied tree so mutating them in place is safe)."""
    out: list = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") in _FLIP_PAIRS:
                out.append(n)
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(node)
    return out


def find_attr_keys(node: Any) -> list:
    """Recursive scan: every distinct `key` string of an `{"type": "Attr",
    ...,"key": <str>}` node reachable inside `node`, sorted by (-frequency,
    key) — the candidate SITES `apply_swap_term_leaf` can swap between (only
    keys the rule ALREADY references, never an invented one). Returns
    `[(key, count), ...]`."""
    counts: dict = {}

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "Attr" and isinstance(n.get("key"), str):
                counts[n["key"]] = counts.get(n["key"], 0) + 1
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(node)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


# ---------------------------------------------------------------------------
# appliers — pure (rule, params) -> new-rule-dict | None
# ---------------------------------------------------------------------------
def apply_flip_comparison(rule: dict, new_name: str) -> Optional[dict]:
    """Flip EVERY comparison node in `rule['effects']` (Lt<->Gt, Lte<->Gte) —
    the structural twin of `_shift_rule_thresholds`'s magnitude-shift: instead
    of moving a threshold's VALUE, this reverses its DIRECTION (the gradient
    the rule descends is inverted). Effects-only (never match/where): the
    WHETHER-it-fires condition is untouched, only WHAT it decides. Returns
    None (inert, honest) if `rule['effects']` contains no comparison node at
    all — nothing for this op to flip on this rule."""
    nodes = find_comparison_nodes(rule.get("effects"))
    if not nodes:
        return None
    out = _copy.deepcopy(rule)
    out["name"] = new_name
    for node in find_comparison_nodes(out.get("effects")):
        node["type"] = _FLIP_PAIRS[node["type"]]
    out.pop("active", None)
    return out


def apply_drop_match_edge(rule: dict, index: int, new_name: str) -> Optional[dict]:
    """Drop `rule['match'][index]` — the structural twin that changes WHETHER
    the rule fires (relaxes a constraint: one fewer pattern edge to satisfy).
    Returns None (inert, honest — never produces a degenerate universally-
    matching rule) when `index` is out of range or dropping it would leave
    `match` empty (a rule with zero match edges is a different semantic class,
    not a "relaxed" version of this one)."""
    match = rule.get("match") or []
    if not (0 <= index < len(match)) or len(match) <= 1:
        return None
    out = _copy.deepcopy(rule)
    out["name"] = new_name
    del out["match"][index]
    out.pop("active", None)
    return out


def apply_add_match_guard(rule: dict, node_var: str, attr_key: str, attr_value,
                          new_name: str) -> dict:
    """Add an extra `Eq(Attr(node_var, attr_key), Lit(attr_value))` conjunct
    to `rule['where']` — the structural twin that NARROWS when the rule fires
    (one more condition to satisfy). `node_var` should name a variable the
    rule's own `match` already binds (the caller's job to pick a genuine one —
    see `_compose_structural_variant`); this applier only assembles the JSON,
    it does not validate that `node_var` is bound (an ill-formed guard fails
    at `add_rule`/`evaluate` time, same as any other malformed Term). Always
    succeeds structurally (there is no "inert" case for adding a new, distinct
    conjunct)."""
    guard = {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": node_var},
                                  "key": attr_key},
             "b": {"type": "Lit", "value": attr_value}}
    out = _copy.deepcopy(rule)
    out["name"] = new_name
    old_where = out.get("where")
    out["where"] = {"type": "And", "items": [old_where, guard]} if old_where else guard
    out.pop("active", None)
    return out


def apply_swap_term_leaf(rule: dict, old_key: str, new_key: str, new_name: str) -> Optional[dict]:
    """Replace every `Attr(..., key=old_key)` in `rule['effects']` with
    `Attr(..., key=new_key)` — swapping WHICH attribute a decision reads (e.g.
    a gradient-descent rule that compares `.row` swapped to compare `.col`
    walks the other axis). `new_key` should be a key the rule ALREADY
    references elsewhere (the caller's job — see `find_attr_keys` /
    `_compose_structural_variant`; this applier is pure mechanical
    substitution, it does not itself require `new_key` to pre-exist). Returns
    None (inert, honest) if `old_key` does not occur in `rule['effects']` at
    all — nothing for this op to swap on this rule."""
    def count_key(node, key):
        n = 0
        if isinstance(node, dict):
            if node.get("type") == "Attr" and node.get("key") == key:
                n += 1
            for v in node.values():
                n += count_key(v, key)
        elif isinstance(node, list):
            for v in node:
                n += count_key(v, key)
        return n

    if count_key(rule.get("effects"), old_key) == 0:
        return None
    out = _copy.deepcopy(rule)
    out["name"] = new_name

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "Attr" and node.get("key") == old_key:
                node["key"] = new_key
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(out.get("effects"))
    out.pop("active", None)
    return out


# name-keyed registry — the same dispatch shape reflective_faculty._COMPOSER_
# REGISTRY uses; `_compose_structural_variant` looks up by the agent's own
# EditOp.kind pick, never a Python if/elif over the kind string.
APPLIERS = {
    "flip_comparison": apply_flip_comparison,
    "drop_match_edge": apply_drop_match_edge,
    "add_match_guard": apply_add_match_guard,
    "swap_term_leaf": apply_swap_term_leaf,
}

__all__ = ["find_comparison_nodes", "find_attr_keys", "apply_flip_comparison",
           "apply_drop_match_edge", "apply_add_match_guard", "apply_swap_term_leaf",
           "APPLIERS"]
