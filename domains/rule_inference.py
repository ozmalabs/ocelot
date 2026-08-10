"""Structural fingerprints over transformation rules.

A rule's *fingerprint* is a deterministic structural summary of its
match / where / effect skeleton — abstracted from the specific opcode
and from specific constant values. Two rules with the same fingerprint
have the same SHAPE; they're members of the same rule family.

This is the *inference layer* the agent uses to discover what families
exist in its installed LLVM passes. It does not require running the
rule engine — the fingerprint is a function of the rule's spec, and
the family is the equivalence class of rules sharing a fingerprint.

The installer materialises both as graph data: each rule becomes a
`RewriteRule` node with its fingerprint as an attribute, and each
distinct fingerprint becomes a `RuleFamily` node that members link to
via `member_of`. The agent's reasoning over rule families is then a
graph query — no analysis pass needed at runtime.

Compiler-theory concepts (constant_folding, identity_elimination,
strength_reduction, …) get attached on top via Frames whose
`recognises` pattern matches a family's fingerprint. The grounded
meaning of "constant folding" is then exactly the rules in that
family — knowledge built from observed structure, not naming.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# fingerprint helpers
# ---------------------------------------------------------------------------

def _strip(s: Any) -> Any:
    return s[1:] if isinstance(s, str) and s.startswith("?") else s


def _match_edges(rule_spec: dict) -> tuple[str, ...]:
    """Ordered tuple of edge_types from the match patterns."""
    return tuple(t[1] for t in rule_spec.get("match", []))


def _match_has_repeated_var(rule_spec: dict) -> bool:
    """True iff some var (other than the LHS subject, which is the same
    across all triples by convention) appears in >1 triple. Captures
    the `op X, X → X` shape used by identity_*_self rules."""
    triples = rule_spec.get("match", [])
    if not triples:
        return False
    subject = _strip(triples[0][0])
    seen: dict[str, int] = {}
    for _, _, tgt in triples:
        t = _strip(tgt)
        if t == subject:
            continue
        seen[t] = seen.get(t, 0) + 1
    return any(c >= 2 for c in seen.values())


def _walk_where(where_spec: Any, visit) -> None:
    """Visit each leaf constraint dict in a where-spec.

    `not` clauses are intentionally NOT recursed: they are *guards*
    (UB-preservation, divisor-zero, etc.), not part of the rule's
    positive structural pattern. Treating them as structural would
    artificially split families that share an identity — e.g.
    `constfold_sdiv` (which guards `not rhs == 0`) shares the same
    fingerprint as `constfold_add` despite the extra precondition,
    because both POSITIVELY match the constfold shape.
    """
    if where_spec is True or where_spec is False:
        return
    if not isinstance(where_spec, dict):
        return
    if "all" in where_spec:
        for p in where_spec["all"]:
            _walk_where(p, visit)
        return
    if "any" in where_spec:
        for p in where_spec["any"]:
            _walk_where(p, visit)
        return
    if "not" in where_spec:
        # Guard, not structure — skip.
        return
    # leaf — type_of / attr+eq
    visit(where_spec)


def _where_features(rule_spec: dict) -> tuple[int, bool, bool, bool]:
    """Returns (count_typeof_constant, has_value_eq, has_opcode_eq,
    has_use_count_zero).

    Specifically:
      count_typeof_constant — how many operand vars carry `type_of …
          LLVMConstant`. 2 → both operands constants (constfold); 1 →
          one side constant (identity_*_right/left); 0 → neither.
      has_value_eq — True if any `{attr: [?x, value], eq: V}` exists.
          Captures identity_*_zero / identity_mul_one shapes.
      has_opcode_eq — True if any `{attr: [?inst, opcode], eq: OP}`
          exists. (Almost always true; included for completeness.)
      has_use_count_zero — True if any `{count_in: [?x, et], eq: 0}`
          exists. Captures DCE's "no incoming uses" constraint.
    """
    count_typeof_const = 0
    has_value_eq = False
    has_opcode_eq = False
    has_use_count_zero = False

    def visit(leaf: dict):
        nonlocal count_typeof_const, has_value_eq, has_opcode_eq, has_use_count_zero
        if "type_of" in leaf and leaf.get("is") == "LLVMConstant":
            count_typeof_const += 1
        if "attr" in leaf and "eq" in leaf:
            _var, key = leaf["attr"]
            if key == "value":
                has_value_eq = True
            elif key == "opcode":
                has_opcode_eq = True
        if "count_in" in leaf and leaf.get("eq") == 0:
            has_use_count_zero = True

    _walk_where(rule_spec.get("where"), visit)
    return count_typeof_const, has_value_eq, has_opcode_eq, has_use_count_zero


def _effect_kinds(rule_spec: dict) -> tuple[str, ...]:
    """Ordered tuple of effect operation kinds."""
    out = []
    for eff in rule_spec.get("effect", []):
        if not isinstance(eff, dict):
            continue
        # The effect's kind is its single recognised key.
        for k in ("add_edge", "del_edge", "add_node", "delete",
                  "del_node", "set_attr", "replace_value"):
            if k in eff:
                out.append("del_node" if k == "delete" else k)
                break
    return tuple(out)


def _effect_has_computed_value(rule_spec: dict) -> bool:
    """True iff some add_node effect carries a computed (Term) attr —
    distinguishes constfold (which materialises a new constant from a
    Plus/BitAnd/Shl/… computation) from identity rules (which only
    rewire to an existing operand)."""
    from .llvm_pass_compiler import _is_computed
    for eff in rule_spec.get("effect", []):
        if isinstance(eff, dict) and "add_node" in eff:
            for v in eff["add_node"].get("attrs", {}).values():
                if _is_computed(v):
                    return True
    return False


# ---------------------------------------------------------------------------
# rule_fingerprint
# ---------------------------------------------------------------------------

def rule_fingerprint(rule_spec: dict) -> dict:
    """Structural fingerprint of `rule_spec` — same across rules in the
    same family, different between families.

    Returns a dict with:
      match_edges            tuple[str, ...]    ordered edge_type sequence
      match_repeated_var     bool               same var on both operands
      effect_kinds           tuple[str, ...]    ordered effect kind sequence
      effect_computed_value  bool               add_node with computed attr
      typeof_constant_count  int                operands constrained to Const
      has_value_eq           bool               value-equality constraint
      has_opcode_eq          bool               opcode constraint (always T)
      key                    str                canonical signature string
    """
    match_edges = _match_edges(rule_spec)
    repeated_var = _match_has_repeated_var(rule_spec)
    effects = _effect_kinds(rule_spec)
    computed = _effect_has_computed_value(rule_spec)
    n_typeof_const, has_value_eq, has_opcode_eq, has_use_count_zero = \
        _where_features(rule_spec)

    key = (
        f"match=({','.join(match_edges)})"
        f"|rep_var={int(repeated_var)}"
        f"|effects=({','.join(effects)})"
        f"|computed={int(computed)}"
        f"|typeof_const={n_typeof_const}"
        f"|value_eq={int(has_value_eq)}"
        f"|opcode_eq={int(has_opcode_eq)}"
        f"|use_count_zero={int(has_use_count_zero)}"
    )
    return {
        "match_edges": match_edges,
        "match_repeated_var": repeated_var,
        "effect_kinds": effects,
        "effect_computed_value": computed,
        "typeof_constant_count": n_typeof_const,
        "has_value_eq": has_value_eq,
        "has_opcode_eq": has_opcode_eq,
        "has_use_count_zero": has_use_count_zero,
        "key": key,
    }


# ---------------------------------------------------------------------------
# installation — graph-resident RewriteRule + RuleFamily
# ---------------------------------------------------------------------------

def _ensure_inference_grammar(substrate) -> None:
    """Open the productions the inference layer needs — exactly:
    `RewriteRule --member_of--> RuleFamily`. Duplicate productions
    are harmless, so this is called unconditionally per install — no
    cross-substrate state to get wrong."""
    substrate.add_production({
        "src": {"type": "RewriteRule", "var": "src"},
        "edge_type": "member_of",
        "tgt": {"type": "RuleFamily", "var": "tgt"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "rule_inference:member_of",
    })


def install_rule_node(substrate, rule_spec: dict, rule_idx: int | None = None) -> int:
    """Add a `RewriteRule` graph node representing `rule_spec`'s
    structural identity. Find-or-create the `RuleFamily` node for the
    fingerprint and link via `member_of`.

    `rule_idx`, if provided, is the native rule index returned by
    `substrate.add_rule(...)` — it's stored as an attr so a pipeline
    executor can dispatch by walking the graph and calling
    `apply_rule_once(rule_idx)` on each family member.

    Returns the RewriteRule NodeID.

    NOTE: Caller is responsible for `add_rule(compile_rule(rule_spec))`
    — this function only creates the agent-introspectable mirror nodes.
    `install_transformation_rule` does both.
    """
    _ensure_inference_grammar(substrate)
    fp = rule_fingerprint(rule_spec)
    attrs: dict = {
        "name": rule_spec.get("name", ""),
        "doc": rule_spec.get("doc", ""),
        "kind": rule_spec.get("kind", "transformation"),
        "fingerprint": fp["key"],
        "match_edges": list(fp["match_edges"]),
        "effect_kinds": list(fp["effect_kinds"]),
        "match_repeated_var": fp["match_repeated_var"],
        "effect_computed_value": fp["effect_computed_value"],
        "typeof_constant_count": fp["typeof_constant_count"],
        "has_value_eq": fp["has_value_eq"],
        "has_opcode_eq": fp["has_opcode_eq"],
        "has_use_count_zero": fp["has_use_count_zero"],
    }
    if rule_idx is not None:
        attrs["rule_idx"] = rule_idx
    rr = substrate.add_node("RewriteRule", attrs)

    family = _find_or_create_family(substrate, fp["key"])
    substrate.add_edge(rr, "member_of", family, {})
    return rr


def _find_or_create_family(substrate, fingerprint_key: str) -> int:
    """Idempotent: return the RuleFamily node with the given fingerprint,
    creating it if none exists."""
    for n in substrate.nodes("RuleFamily"):
        if substrate.node(n)["attrs"].get("fingerprint") == fingerprint_key:
            return n
    return substrate.add_node("RuleFamily", {
        "fingerprint": fingerprint_key,
    })


__all__ = [
    "rule_fingerprint",
    "install_rule_node",
]
