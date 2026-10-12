"""Improvement integrity for whole SeedDeltas (plan P3, 2026-10-10).

seeds/improvement_integrity.json holds `protected_node_types`: the node types
whose records and policies ARE the self-improvement loop. Until P3 only RULES
were checked against it (a rule naming a protected type is loop machinery).
A delta's node-level parts were not: `set_node_attrs` could rewrite a
VariationPolicy and `add_concepts` could mint any node type, both in the child
replay and at adoption.

This module is the one structural read both sides use:
  * `delta_violations(sub, delta)` -- every part of a delta that touches the
    loop: an added rule naming a protected type, a node-attr edit or a node
    addition whose type is protected. The adoption gate denies on any.
  * `filter_protected(sub, delta)` -- the child's twin: the same parts are
    dropped from the delta before it is applied, and reported.

PROVENANCE_TYPES are refused for node-level edits too. They are not loop
machinery (rules may read them freely) but they ARE the adoption gate's own
evidence: `RuleSummary.skippable` / `SeedSummary.skippable` decide what the
denylist lets through, so a delta that edited them could open the gate it is
judged by. Mechanical reads only; nothing here decides what to try.
"""
from __future__ import annotations

import json

PROVENANCE_TYPES = ("RuleSummary", "SeedSummary")


def protected_types(sub) -> tuple:
    """The held protected_node_types (empty when the seed is not loaded)."""
    out: set = set()
    try:
        for n in sub.nodes("ImprovementIntegrity"):
            for t in sub.node(n)["attrs"].get("protected_node_types") or []:
                out.add(str(t))
    except Exception:  # noqa: BLE001 -- type absent on a bare graph
        return ()
    return tuple(sorted(out))


def rule_names_protected_type(rule, types) -> bool:
    """Does this rule's JSON name a protected node type as a string token?
    Conservative by construction; an unreadable rule fails closed."""
    if not types:
        return False
    try:
        s = rule if isinstance(rule, str) else json.dumps(rule)
    except Exception:  # noqa: BLE001
        return True
    return any(('"%s"' % t) in s for t in types)


def _node_edit_types(types) -> set:
    # node-level edits are refused on loop types AND on the gate's own
    # provenance evidence; only when the integrity seed is loaded at all
    return set(types) | set(PROVENANCE_TYPES) if types else set()


def delta_violations(sub, delta: dict) -> list:
    """Every part of `delta` (the plain-dict form: add_rules, set_node_attrs,
    add_concepts / add_nodes) that touches the self-improvement loop, as
    human-readable reasons. Empty = the delta may be applied."""
    types = protected_types(sub)
    if not types:
        return []
    refused = _node_edit_types(types)
    out = []
    for r in delta.get("add_rules") or []:
        if rule_names_protected_type(r, types):
            name = r.get("name", "?") if isinstance(r, dict) else "?"
            out.append(f"added rule {name!r} names a self-improvement-loop node type")
    for item in delta.get("set_node_attrs") or []:
        t = str((item or {}).get("type") or "") if isinstance(item, dict) else ""
        if t in refused:
            out.append(f"node-attr edit on {t} (self-improvement integrity)")
    for key in ("add_concepts", "add_nodes"):
        for item in delta.get(key) or []:
            t = str((item or {}).get("type") or "Concept") if isinstance(item, dict) else ""
            if t in refused:
                out.append(f"node addition of type {t} (self-improvement integrity)")
    return out


def filter_protected(sub, delta: dict) -> tuple:
    """(delta', refused): `delta` with every node-level part that touches the
    loop removed (set_node_attrs / add_concepts items of a refused type),
    and the reasons. Rules are left to the adoption gate (unchanged
    behaviour: a child may trial them, the parent never installs them)."""
    types = protected_types(sub)
    if not types:
        return delta, []
    refused_types = _node_edit_types(types)
    out = dict(delta)
    refused = []
    for key, default in (("set_node_attrs", ""), ("add_concepts", "Concept")):
        kept = []
        for item in delta.get(key) or []:
            t = str((item or {}).get("type") or default) if isinstance(item, dict) else ""
            if t in refused_types:
                refused.append(f"{key}: {t}")
            else:
                kept.append(item)
        out[key] = kept
    return out, refused
