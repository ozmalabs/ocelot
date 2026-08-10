"""rule_emitter — a MECHANICAL compiler from a structured rule-spec to a
fireable Rule node. Compiler, not LLM; generic, not hand-fit to any one rule.

The agent decides WHAT (a declarative spec: which predicate dimensions over
which attrs, which effect) — reasoned from its own concepts. This module emits
HOW (the match/where/effect Term-tree, via add_rule). Same division of labour as
domains/runtime_design.py, one level up: there the agent specifies a primitive
and the generator emits Rust; here it specifies a rule and the generator emits a
fireable RewriteRule. No Term-tree is authored by hand per rule.
"""
from __future__ import annotations

from substrate_rs import Var, Attr, Lit, Gt, Lt, Gte, Lte, Eq, And

_OPS = {"lt": Lt, "gt": Gt, "gte": Gte, "lte": Lte, "eq": Eq}


def _operand(spec, vars):
    """A spec operand is either a literal (number/str) or {"attr","node"}."""
    if isinstance(spec, dict) and "attr" in spec:
        return Attr(vars[spec["node"]], spec["attr"])
    return Lit(spec)


def emit_rule_from_spec(nat, spec: dict) -> int:
    """Compile spec -> fireable Rule, install via add_rule, return its index.

    spec = {
      "name":    str,
      "vars":    [var names used in match/trigger],
      "match":   [[src, edge, tgt], ...],          # binds the vars
      "trigger": [ {"lhs": operand, "op": "lt|gt|gte|lte|eq", "rhs": operand}, ...],
      "effects": [[verb, ...], ...],               # set_attr / del_node / ...
    }
    The trigger conjuncts are AND-ed into `where`. Effects pass through verbatim
    (each verb is one the engine already accepts: set_attr/del_node/add_edge/...).
    """
    vars = {v: Var(v) for v in spec["vars"]}
    conjuncts = [
        _OPS[p["op"]](a=_operand(p["lhs"], vars), b=_operand(p["rhs"], vars))
        for p in spec["trigger"]
    ]
    where = And(items=tuple(conjuncts)) if len(conjuncts) > 1 else conjuncts[0]
    rule = {
        "name": spec["name"],
        "match": spec["match"],
        "where": where.to_dict(),
        "effects": spec["effects"],
    }
    return nat.add_rule(rule)
