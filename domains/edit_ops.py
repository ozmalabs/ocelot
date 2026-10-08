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
import hashlib as _hashlib
import json as _json
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


def find_edge_identity_sites(rule: dict) -> list[dict]:
    """Return generic absence-guard sites for emitted edges at bound endpoints.

    A fresh opposite endpoint also exposes bounded attribute-signature sites
    when a corresponding add_node effect gives those fields from bound Attrs.
    Site generation is linear plus pairwise combinations, not a power set.
    """
    bound = set()
    for edge in rule.get("match") or []:
        if isinstance(edge, list) and len(edge) >= 3:
            if isinstance(edge[0], str):
                bound.add(edge[0])
            if isinstance(edge[2], str):
                bound.add(edge[2])
    sites = []
    seen = set()

    def add_site(site):
        key = (site["direction"], site["var"], site["edge_type"], site["other"],
               site.get("scope", "edge"), site.get("node_var"), site.get("node_type"),
               tuple(site.get("identity_keys") or ()))
        if key in seen:
            return
        seen.add(key)
        sites.append(site)
    for effect in rule.get("effects") or []:
        if not (isinstance(effect, list) and len(effect) >= 4 and effect[0] == "add_edge"):
            continue
        src, edge_type, tgt = effect[1], effect[2], effect[3]
        options = []
        if isinstance(src, str) and src in bound:
            options.append(("out", src, tgt if isinstance(tgt, str) and tgt in bound else None))
        if isinstance(tgt, str) and tgt in bound:
            options.append(("in", tgt, src if isinstance(src, str) and src in bound else None))
        for direction, var, other in options:
            row = {"direction": direction, "var": var, "edge_type": edge_type,
                   "other": other, "scope": "edge", "node_var": None,
                   "node_type": None, "identity_keys": []}
            add_site(row)
            if other is not None:
                continue
            fresh_var = tgt if direction == "out" else src
            for node_effect in rule.get("effects") or []:
                if not (isinstance(node_effect, list) and len(node_effect) >= 4
                        and node_effect[0] == "add_node" and node_effect[1] == fresh_var
                        and isinstance(node_effect[3], dict)):
                    continue
                node_var, node_type, attrs = node_effect[1], node_effect[2], node_effect[3]
                identity_keys = []
                for key, value in attrs.items():
                    term = value.get("__term__") if isinstance(value, dict) else None
                    if (isinstance(term, dict) and term.get("type") == "Attr"
                            and isinstance(term.get("node"), dict)
                            and term["node"].get("type") == "Var"
                            and term["node"].get("name") in bound):
                        identity_keys.append(key)
                identity_keys.sort()
                key_sets = [[k] for k in identity_keys]
                key_sets.extend([[identity_keys[i], identity_keys[j]]
                    for i in range(len(identity_keys)) for j in range(i + 1, len(identity_keys))])
                if len(identity_keys) > 2:
                    key_sets.append(identity_keys)
                for keys in key_sets:
                    candidate = {"direction": direction, "var": var, "edge_type": edge_type,
                        "other": None, "scope": "node_attrs", "node_var": node_var,
                        "node_type": node_type, "identity_keys": keys}
                    add_site(candidate)
    return sites


def apply_add_edge_identity_guard(rule: dict, site: dict, new_name: str) -> Optional[dict]:
    """Add a Not-Exists guard for one structural edge-identity site."""
    if site not in find_edge_identity_sites(rule):
        return None
    existing = "existing_edge_identity"
    if site.get("scope") == "node_attrs":
        node_effect = next((e for e in rule.get("effects") or [] if isinstance(e, list)
            and len(e) >= 4 and e[0] == "add_node" and e[1] == site["node_var"]
            and e[2] == site["node_type"]), None)
        if node_effect is None:
            return None
        attrs = node_effect[3]
        predicates = []
        for key in site["identity_keys"]:
            value = attrs.get(key)
            term = value.get("__term__") if isinstance(value, dict) else None
            if not isinstance(term, dict):
                return None
            predicates.append({"type": "Eq", "a": {"type": "Attr",
                "node": {"type": "Var", "name": existing}, "key": key}, "b": _copy.deepcopy(term)})
        source = {"type": "NodesOfType", "node_type": site["node_type"]}
        predicate = predicates[0] if len(predicates) == 1 else {"type": "And", "items": predicates}
    else:
        source_type = "Neighbours" if site["direction"] == "out" else "InNeighbours"
        anchor = {"type": "Var", "name": site["var"]}
        source = {"type": source_type, "node": anchor, "edge_type": site["edge_type"]}
        predicate = ({"type": "Eq", "a": {"type": "Var", "name": existing},
                      "b": {"type": "Var", "name": site["other"]}}
                     if site.get("other") is not None else {"type": "Lit", "value": True})
    guard = {"type": "Not", "arg": {"type": "Exists", "source": source,
             "var_name": existing, "predicate": predicate}}
    out = _copy.deepcopy(rule)
    out["name"] = new_name
    old_where = out.get("where")
    out["where"] = {"type": "And", "items": [old_where, guard]} if old_where else guard
    out.pop("active", None)
    return out


def observed_relation_signatures(rule: dict, bindings: dict, graph_edges: list) -> list[dict]:
    """Project local training-graph edges to relation signatures at rule vars.

    `bindings` maps variables bound by the current rule match to graph node
    IDs; `graph_edges` is a sequence of `(src_id, edge_type, tgt_id)` triples.
    Edges from/to a matched node to an as-yet-unbound node become extension
    proposals. The function reports available relations only; it does not
    claim they are useful or causal.
    """
    bound_vars = {edge[i] for edge in (rule.get("match") or [])
                  if isinstance(edge, list) for i in (0, 2)
                  if len(edge) > i and isinstance(edge[i], str)}
    node_to_var = {}
    for var, node_id in (bindings or {}).items():
        if var in bound_vars:
            node_to_var.setdefault(node_id, []).append(var)
    known_nodes = set((bindings or {}).values())
    signatures = set()
    for edge in graph_edges or []:
        if not isinstance(edge, (list, tuple)) or len(edge) < 3:
            continue
        src_id, edge_type, tgt_id = edge[:3]
        if not isinstance(edge_type, str):
            continue
        if src_id in node_to_var and tgt_id not in known_nodes:
            for anchor in node_to_var[src_id]:
                signatures.add((anchor, "out", edge_type))
        if tgt_id in node_to_var and src_id not in known_nodes:
            for anchor in node_to_var[tgt_id]:
                signatures.add((anchor, "in", edge_type))
    return [{"anchor_var": anchor, "direction": direction, "edge_type": edge_type}
            for anchor, direction, edge_type in sorted(signatures)]


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


def enumerate_single_edit_candidates(rule: dict, *, max_candidates: int = 256,
                                    observed_relations: Optional[list[dict]] = None) -> list[dict]:
    """Enumerate a bounded, deterministic pool of one-edit rule variants.

    The pool is derived from the supplied rule's syntax and, optionally,
    observed relation signatures tied to variables already bound by its match:
    comparison
    flips, unit numeric-literal shifts, removal of one existing `where`
    conjunction, boolean effect-literal toggles, match-edge deletion, swaps
    between attribute keys already present in effects, guards over already
    referenced keys and literals, and edge-identity guards. It does not
    inspect task examples or an oracle. Each observed relation signature has
    `anchor_var`, `direction` (`in` or `out`), and `edge_type`; it proposes a
    match edge between that bound variable and one fresh variable. Such
    signatures are intended to come from training graph neighborhoods.
    Each row contains a stable canonical ID, operator/site description, and
    the candidate rule JSON. Duplicate semantic variants are collapsed after
    ignoring the display name and `active` metadata. The cap is strict and
    truncation is reported so callers cannot mistake a prefix for exhaustive
    search.

    This is a proposal enumerator, not a repair diagnosis or a claim that the
    bounded language contains a correct edit. Numeric shifts use a registered
    ±1 neighborhood; this can miss arbitrary thresholds. Its syntax-derived
    guard basis deliberately cannot invent new attributes or constants.
    """
    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")

    base_name = str(rule.get("name") or "rule")
    proposals: list[tuple[str, str, Optional[dict]]] = []

    def propose(operator: str, site: str, variant: Optional[dict]) -> None:
        proposals.append((operator, site, variant))

    comparisons = find_comparison_nodes(rule.get("effects"))
    if comparisons:
        propose("flip_comparison", "all_effect_comparisons",
                apply_flip_comparison(rule, base_name + "_candidate_flip"))

    def replace_at_path(root: Any, path: tuple, replacement: Any) -> Any:
        out = _copy.deepcopy(root)
        parent = out
        for part in path[:-1]:
            parent = parent[part]
        parent[path[-1]] = _copy.deepcopy(replacement)
        return out

    def walk_type(node: Any, wanted: str, path: tuple = ()):
        if isinstance(node, dict):
            if node.get("type") == wanted:
                yield path, node
            for key, value in node.items():
                yield from walk_type(value, wanted, path + (key,))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                yield from walk_type(value, wanted, path + (index,))

    # The registered unit neighborhood supplies a bounded numeric proposal
    # grammar without claiming to infer arbitrary constants. Each literal is
    # edited independently, preserving all other syntax.
    for section in ("where", "effects"):
        for path, literal in walk_type(rule.get(section), "Lit"):
            value = literal.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            for delta in (-1, 1):
                replacement = dict(literal)
                replacement["value"] = value + delta
                variant = replace_at_path(rule, (section,) + path, replacement)
                variant["name"] = base_name + "_candidate_numeric"
                variant.pop("active", None)
                propose("shift_numeric_literal", f"{section}{path}:{value}{delta:+}", variant)

    # Guard removal is offered only for an explicit conjunction with at least
    # two children. A singleton is collapsed to its child to avoid a degenerate
    # one-item And wrapper.
    for path, conjunction in walk_type(rule.get("where"), "And"):
        items = conjunction.get("items")
        if not isinstance(items, list) or len(items) < 2:
            continue
        for index in range(len(items)):
            remaining = _copy.deepcopy(items[:index] + items[index + 1:])
            replacement = {"type": "And", "items": remaining} if len(remaining) > 1 else remaining[0]
            variant = replace_at_path(rule, ("where",) + path, replacement)
            variant["name"] = base_name + "_candidate_drop_guard"
            variant.pop("active", None)
            propose("drop_where_conjunct", f"where{path}.items[{index}]", variant)

    for path, literal in walk_type(rule.get("effects"), "Lit"):
        value = literal.get("value")
        if not isinstance(value, bool):
            continue
        replacement = dict(literal)
        replacement["value"] = not value
        variant = replace_at_path(rule, ("effects",) + path, replacement)
        variant["name"] = base_name + "_candidate_toggle_effect"
        variant.pop("active", None)
        propose("toggle_boolean_effect", f"effects{path}:{value}->{not value}", variant)

    for index, edge in enumerate(rule.get("match") or []):
        propose("drop_match_edge", f"match[{index}]",
                apply_drop_match_edge(rule, index, base_name + f"_candidate_drop_{index}"))

    bound_vars = sorted({edge[i] for edge in (rule.get("match") or [])
                         if isinstance(edge, list) for i in (0, 2)
                         if len(edge) > i and isinstance(edge[i], str)})
    used_vars = set(bound_vars)
    next_var_index = 0
    relation_rows = [row for row in (observed_relations or []) if isinstance(row, dict)]
    for relation in sorted(relation_rows, key=lambda row: (
            str(row.get("anchor_var")), str(row.get("direction")), str(row.get("edge_type")))):
        anchor = relation.get("anchor_var")
        direction = relation.get("direction")
        edge_type = relation.get("edge_type")
        if anchor not in bound_vars or direction not in ("in", "out") or not isinstance(edge_type, str):
            continue
        while f"__candidate_node_{next_var_index}" in used_vars:
            next_var_index += 1
        fresh = f"__candidate_node_{next_var_index}"
        next_var_index += 1
        used_vars.add(fresh)
        edge = [anchor, edge_type, fresh] if direction == "out" else [fresh, edge_type, anchor]
        variant = _copy.deepcopy(rule)
        variant["name"] = base_name + "_candidate_add_match_edge"
        variant.setdefault("match", []).append(edge)
        variant.pop("active", None)
        propose("add_match_edge", f"match:+{edge!r}", variant)

    effect_keys = [key for key, _ in find_attr_keys(rule.get("effects"))]
    for old_key in effect_keys:
        for new_key in effect_keys:
            if old_key == new_key:
                continue
            propose("swap_term_leaf", f"effects:{old_key}->{new_key}",
                    apply_swap_term_leaf(rule, old_key, new_key,
                                         base_name + "_candidate_swap"))

    def collect(node: Any, *, typ: str, field: str) -> set:
        found = set()
        if isinstance(node, dict):
            if node.get("type") == typ and field in node:
                value = node[field]
                if isinstance(value, (str, int, float, bool)) or value is None:
                    found.add(value)
            for value in node.values():
                found.update(collect(value, typ=typ, field=field))
        elif isinstance(node, list):
            for value in node:
                found.update(collect(value, typ=typ, field=field))
        return found

    syntax = [rule.get("where"), rule.get("effects")]
    keys = set()
    literals = set()
    for part in syntax:
        keys.update(collect(part, typ="Attr", field="key"))
        literals.update(collect(part, typ="Lit", field="value"))
    # Stable primitive ordering; complex literal values are outside this
    # bounded candidate grammar and therefore omitted explicitly.
    literals = {v for v in literals if isinstance(v, (str, int, float, bool)) or v is None}
    keys = sorted(k for k in keys if isinstance(k, str))
    literals = sorted(literals, key=lambda v: (type(v).__name__, repr(v)))
    for node_var in bound_vars:
        for attr_key in keys:
            for value in literals:
                site = f"where:{node_var}.{attr_key}=={value!r}"
                variant = apply_add_match_guard(
                    rule, node_var, attr_key, value, base_name + "_candidate_guard")
                propose("add_match_guard", site, variant)

    for site in find_edge_identity_sites(rule):
        variant = apply_add_edge_identity_guard(
            rule, site, base_name + "_candidate_identity")
        propose("add_edge_identity_guard", _json.dumps(site, sort_keys=True), variant)

    unique: dict[str, dict] = {}
    total_valid = 0
    for operator, site, variant in proposals:
        if variant is None:
            continue
        semantic = _copy.deepcopy(variant)
        semantic.pop("name", None)
        semantic.pop("active", None)
        canonical = _json.dumps(semantic, sort_keys=True, separators=(",", ":"))
        candidate_id = _hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        total_valid += 1
        if candidate_id in unique:
            unique[candidate_id]["duplicate_sites"].append({"operator": operator, "site": site})
            continue
        unique[candidate_id] = {
            "candidate_id": candidate_id,
            "operator": operator,
            "site": site,
            "rule": variant,
            "duplicate_sites": [],
        }

    rows = list(unique.values())
    truncated = len(rows) > max_candidates
    selected = rows[:max_candidates]
    return [{**row, "proposal_count_before_dedup": len(proposals),
             "valid_count_before_dedup": total_valid,
             "unique_count": len(rows), "truncated": truncated}
            for row in selected]


# name-keyed registry — the same dispatch shape reflective_faculty._COMPOSER_
# REGISTRY uses; `_compose_structural_variant` looks up by the agent's own
# EditOp.kind pick, never a Python if/elif over the kind string.
APPLIERS = {
    "flip_comparison": apply_flip_comparison,
    "drop_match_edge": apply_drop_match_edge,
    "add_match_guard": apply_add_match_guard,
    "swap_term_leaf": apply_swap_term_leaf,
    "add_edge_identity_guard": apply_add_edge_identity_guard,
}

__all__ = ["find_comparison_nodes", "find_attr_keys", "find_edge_identity_sites", "observed_relation_signatures", "apply_flip_comparison",
           "apply_drop_match_edge", "apply_add_match_guard", "apply_swap_term_leaf", "apply_add_edge_identity_guard",
           "enumerate_single_edit_candidates", "APPLIERS"]
