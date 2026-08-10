"""Compile concise LLVM pass specs into substrate-native RewriteRules.

Phase 3 of the LLVM ingestion arc (see LLVM_LEARNING.md). The concise
spec format is what teachers and humans author; this module compiles it
to the dict shape `substrate_rs.Substrate.add_rule` expects (see py.rs
`add_rule` docstring).

Concise spec:

    {
      "kind": "transformation",
      "name": "constfold_add",
      "match": [["?inst", "uses_op0", "?v1"], ...],
      "where": {"all": [
          {"type_of": "?inst", "is": "LLVMInstruction"},
          {"attr": ["?inst", "opcode"], "eq": "add"},
          ...
      ]},
      "effect": [
          {"add_node": {"var": "?new", "type": "LLVMConstant",
                        "attrs": {"value": {"add": [{"attr": ["?v1", "value"]},
                                                    {"attr": ["?v2", "value"]}]}}}},
          {"replace_value": {"old": "?old_result", "new": "?new"}},
          {"delete": "?inst"},
      ]
    }

Compiled output is a dict whose shape matches:

    {"name": str,
     "match": [[src, et, tgt], ...],
     "where": {<term JSON>} | None,
     "effects": [[<effect array>], ...]}

The substrate's `add_rule` parses this directly into a `RewriteRule`.

The function-of-substrate-spec pattern keeps this module standalone —
it imports the substrate's Term wrappers + `term_to_json` but never
mutates substrate state itself. `install_transformation_rule` is the
one-line bridge.
"""
from __future__ import annotations

from typing import Any

from substrate_rs import (
    And, Attr, Count, Eq, IfThenElse, InNeighbours, Lit, Lt, Lte, Not,
    Or, Plus, Minus, Times, TypeOf, Var, Term as _Term,
)

# Int/bit-op Term wrappers. They live in the substrate_rs Python layer
# (and the Rust TermNode enum) in-tree; an older installed wheel may not
# export the wrappers yet, so construct them generically until the wheel
# is rebuilt — the serialized JSON (`.to_dict()`) is identical either way.
try:
    from substrate_rs import (  # noqa: F401
        Ashr, BitAnd, BitOr, BitXor, IDiv, IRem, Lshr, Shl,
    )
except ImportError:
    def BitAnd(a, b): return _Term("BitAnd", a=a, b=b)
    def BitOr(a, b): return _Term("BitOr", a=a, b=b)
    def BitXor(a, b): return _Term("BitXor", a=a, b=b)
    def Ashr(a, b): return _Term("Ashr", a=a, b=b)
    def Lshr(a, b): return _Term("Lshr", a=a, b=b)
    def Shl(a, b): return _Term("Shl", a=a, b=b)
    def IDiv(a, b): return _Term("IDiv", a=a, b=b)
    def IRem(a, b): return _Term("IRem", a=a, b=b)


def term_to_json(t):
    """Serialize a substrate_rs Term to its JSON dict — byte-identical to
    the legacy ``substrate.term_to_json``; `.to_dict()` is the native form."""
    return t.to_dict()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _strip_q(s: Any) -> Any:
    """Vars in concise form are prefixed with `?`; substrate uses bare
    names. Non-string values pass through unchanged."""
    if isinstance(s, str) and s.startswith("?"):
        return s[1:]
    return s


_COMPUTED_KEYS = ("attr", "type_of", "add", "sub", "mul", "lit",
                  "bit_and", "bit_or", "bit_xor", "shl", "lshr", "ashr",
                  "idiv", "irem",
                  "eq", "lt", "le",
                  "if_then_else",
                  "all", "any", "not")


def _is_computed(v: Any) -> bool:
    """True iff `v` is a dict that names a Term-tree (not a plain literal)."""
    return isinstance(v, dict) and any(k in v for k in _COMPUTED_KEYS)


# ---------------------------------------------------------------------------
# compile where-clauses
# ---------------------------------------------------------------------------

def compile_where(spec: Any):
    """Concise where-spec → substrate Term.

    Supported:
      bool                                  → Lit(bool)
      {"type_of": "?x", "is": "T"}          → Eq(TypeOf(Var(x)), Lit("T"))
      {"attr": ["?x", "k"], "eq": V}        → Eq(Attr(Var(x), "k"), Lit(V))
      {"count_in": ["?x", "et"], "eq": N}   → Eq(Count(InNeighbours(Var(x), et)), Lit(N))
      {"all": [P, Q, …]}                    → And(P, Q, …)
      {"any": [P, Q, …]}                    → Or(P, Q, …)
      {"not": P}                            → Not(P)
    """
    if spec is True or spec is False:
        return Lit(spec)
    if isinstance(spec, dict):
        if "type_of" in spec:
            x = _strip_q(spec["type_of"])
            return Eq(a=TypeOf(node=Var(name=x)), b=Lit(spec["is"]))
        if "attr" in spec:
            x, k = spec["attr"]
            return Eq(a=Attr(node=Var(name=_strip_q(x)), key=k),
                      b=Lit(spec["eq"]))
        if "count_in" in spec:
            x, et = spec["count_in"]
            return Eq(
                a=Count(source=InNeighbours(node=Var(name=_strip_q(x)),
                                            edge_type=et)),
                b=Lit(spec["eq"]),
            )
        if "not_eq_vars" in spec:
            x, y = spec["not_eq_vars"]
            return Not(arg=Eq(a=Var(name=_strip_q(x)),
                              b=Var(name=_strip_q(y))))
        if "all" in spec:
            return And(items=tuple(compile_where(p) for p in spec["all"]))
        if "any" in spec:
            return Or(items=tuple(compile_where(p) for p in spec["any"]))
        if "not" in spec:
            return Not(arg=compile_where(spec["not"]))
    raise ValueError(f"unknown where spec: {spec!r}")


# ---------------------------------------------------------------------------
# compile attr-value Terms (used inside add_node / set_attr effect attrs)
# ---------------------------------------------------------------------------

def compile_attr_term(spec: Any):
    """Concise attr-value spec → substrate Term.

    Supports the where-clause forms plus arithmetic:
      {"attr": ["?x", "k"]}    → Attr(Var(x), "k")
      {"type_of": "?x"}        → TypeOf(Var(x))
      {"add": [a, b, …]}       → Plus(a, b, …)
      {"sub": [a, b]}          → Minus(a, b)
      {"mul": [a, b, …]}       → Times(a, b, …)
      {"lit": V}               → Lit(V) (escape hatch for literal dicts)
      bare scalar              → Lit(scalar)
    """
    if isinstance(spec, bool):
        return Lit(spec)
    if isinstance(spec, (int, float)):
        return Lit(spec)
    if isinstance(spec, dict):
        if "attr" in spec:
            x, k = spec["attr"]
            return Attr(node=Var(name=_strip_q(x)), key=k)
        if "type_of" in spec:
            return TypeOf(node=Var(name=_strip_q(spec["type_of"])))
        if "add" in spec:
            return Plus(items=tuple(compile_attr_term(s) for s in spec["add"]))
        if "sub" in spec:
            a, b = spec["sub"]
            return Minus(a=compile_attr_term(a), b=compile_attr_term(b))
        if "mul" in spec:
            return Times(items=tuple(compile_attr_term(s) for s in spec["mul"]))
        if "bit_and" in spec:
            a, b = spec["bit_and"]
            return BitAnd(a=compile_attr_term(a), b=compile_attr_term(b))
        if "bit_or" in spec:
            a, b = spec["bit_or"]
            return BitOr(a=compile_attr_term(a), b=compile_attr_term(b))
        if "bit_xor" in spec:
            a, b = spec["bit_xor"]
            return BitXor(a=compile_attr_term(a), b=compile_attr_term(b))
        if "shl" in spec:
            a, b = spec["shl"]
            return Shl(a=compile_attr_term(a), b=compile_attr_term(b))
        if "lshr" in spec:
            a, b = spec["lshr"]
            return Lshr(a=compile_attr_term(a), b=compile_attr_term(b))
        if "ashr" in spec:
            a, b = spec["ashr"]
            return Ashr(a=compile_attr_term(a), b=compile_attr_term(b))
        if "idiv" in spec:
            a, b = spec["idiv"]
            return IDiv(a=compile_attr_term(a), b=compile_attr_term(b))
        if "irem" in spec:
            a, b = spec["irem"]
            return IRem(a=compile_attr_term(a), b=compile_attr_term(b))
        if "eq" in spec:
            a, b = spec["eq"]
            return Eq(a=compile_attr_term(a), b=compile_attr_term(b))
        if "lt" in spec:
            a, b = spec["lt"]
            return Lt(a=compile_attr_term(a), b=compile_attr_term(b))
        if "le" in spec:
            a, b = spec["le"]
            return Lte(a=compile_attr_term(a), b=compile_attr_term(b))
        if "if_then_else" in spec:
            d = spec["if_then_else"]
            return IfThenElse(
                cond=compile_attr_term(d["cond"]),
                then=compile_attr_term(d["then"]),
                other=compile_attr_term(d["other"]),
            )
        if "lit" in spec:
            return Lit(spec["lit"])
    if isinstance(spec, str):
        # A bare string is a literal; if the user wanted a variable
        # reference, use {"attr": [...]} or a "?"-prefixed form. Bare
        # strings as literal text are the common case (type names,
        # opcode names, etc.).
        return Lit(spec)
    raise ValueError(f"unknown attr term spec: {spec!r}")


def compile_attrs(attrs_spec: dict) -> dict:
    """Concise attrs dict → effect-attrs dict.

    Each value is either a literal (passes through) or a computed Term
    (wrapped in `{"__term__": …}` per the substrate's effect-arg
    encoding).
    """
    out = {}
    for k, v in attrs_spec.items():
        if _is_computed(v):
            term = compile_attr_term(v)
            out[k] = {"__term__": term_to_json(term)}
        else:
            out[k] = v
    return out


# ---------------------------------------------------------------------------
# compile effects
# ---------------------------------------------------------------------------

def compile_effect(spec: dict) -> list:
    """Concise effect spec → effect-array JSON (per py.rs `add_rule` doc).

    Supported forms (one key per effect dict):
      {"add_edge": [src, et, tgt], "attrs": {...}?}
      {"del_edge": [src, et, tgt]}
      {"add_node": {"var": v, "type": T, "attrs": {...}?}}
      {"delete": "?v"} or {"del_node": "?v"}
      {"set_attr": [var, key, value]}
      {"replace_value": {"old": "?old", "new": "?new"}}
    """
    if not isinstance(spec, dict):
        raise ValueError(f"effect spec must be dict, got {type(spec).__name__}")

    if "add_edge" in spec:
        src, et, tgt = spec["add_edge"]
        attrs = compile_attrs(spec.get("attrs", {}))
        return ["add_edge", _strip_q(src), et, _strip_q(tgt), attrs]

    if "del_edge" in spec:
        src, et, tgt = spec["del_edge"]
        return ["del_edge", _strip_q(src), et, _strip_q(tgt)]

    if "add_node" in spec:
        ent = spec["add_node"]
        attrs = compile_attrs(ent.get("attrs", {}))
        return ["add_node", _strip_q(ent["var"]), ent["type"], attrs]

    if "delete" in spec or "del_node" in spec:
        v = spec.get("delete") or spec.get("del_node")
        return ["del_node", _strip_q(v)]

    if "set_attr" in spec:
        var, key, val = spec["set_attr"]
        if _is_computed(val):
            term = compile_attr_term(val)
            val_json = {"__term__": term_to_json(term)}
        else:
            val_json = val
        return ["set_attr", _strip_q(var), key, val_json]

    if "replace_value" in spec:
        ent = spec["replace_value"]
        return ["replace_value", _strip_q(ent["old"]), _strip_q(ent["new"])]

    raise ValueError(f"unknown effect spec: {spec!r}")


# ---------------------------------------------------------------------------
# compile full rules
# ---------------------------------------------------------------------------

def compile_rule(rule_spec: dict) -> dict:
    """Concise rule spec → dict accepted by `Substrate.add_rule`.

    The returned dict's keys match the wire format py.rs's `add_rule`
    parses: `name`, `match`, `where`, `effects`. `where` is either
    `None` or the substrate's Term JSON.
    """
    kind = rule_spec.get("kind", "transformation")
    if kind != "transformation":
        raise ValueError(
            f"only 'transformation' kind supported here, got {kind!r}"
        )

    name = rule_spec["name"]
    match_edges = [
        [_strip_q(src), et, _strip_q(tgt)]
        for src, et, tgt in rule_spec.get("match", [])
    ]

    where_json = None
    where_spec = rule_spec.get("where")
    if where_spec is not None:
        where_json = term_to_json(compile_where(where_spec))

    effects_json = [compile_effect(e) for e in rule_spec.get("effect", [])]

    return {
        "name": name,
        "match": match_edges,
        "where": where_json,
        "effects": effects_json,
    }


def install_transformation_rule(substrate, rule_spec: dict) -> int:
    """Compile and install a concise transformation rule.

    `substrate` is any object with an `add_rule(dict) -> int` method —
    `substrate_rs.Substrate` is the typical target. Returns the rule's
    integer index.

    Also installs a graph-resident `RewriteRule` mirror node + a
    `member_of` edge to the rule's `RuleFamily` (deduped by structural
    fingerprint). The agent reasons about its own optimization arsenal
    through those nodes — the inference layer is the fingerprint, the
    discovered families are the equivalence classes.
    """
    from .rule_inference import install_rule_node
    rule_idx = substrate.add_rule(compile_rule(rule_spec))
    install_rule_node(substrate, rule_spec, rule_idx=rule_idx)
    return rule_idx


# ---------------------------------------------------------------------------
# JSON-seed loader
# ---------------------------------------------------------------------------

def load_passes_seed(path) -> dict:
    """Read a passes-seed JSON file from disk. Returns the manifest dict
    with `id`, `version`, `depends_on`, `description`, `passes`, …. Does
    NOT install — caller chooses which passes to take from the manifest.

    `path` may be a `str` or `pathlib.Path`.
    """
    import json
    from pathlib import Path
    p = Path(path)
    with p.open("r") as f:
        manifest = json.load(f)
    if "passes" not in manifest:
        raise ValueError(
            f"{p}: missing 'passes' key — not a pass-seed manifest"
        )
    return manifest


def install_passes_seed(substrate, path) -> list[int]:
    """Read the passes-seed JSON at `path` and install every pass into
    `substrate`. Returns the list of rule_idx for the installed passes
    in manifest order.

    Equivalent to::

        manifest = load_passes_seed(path)
        return [install_transformation_rule(substrate, p)
                for p in manifest["passes"]]

    Substrate is any object with `add_rule(dict) -> int`.
    """
    manifest = load_passes_seed(path)
    return [install_transformation_rule(substrate, p)
            for p in manifest["passes"]]


__all__ = [
    "compile_where",
    "compile_attr_term",
    "compile_attrs",
    "compile_effect",
    "compile_rule",
    "install_transformation_rule",
    "load_passes_seed",
    "install_passes_seed",
]
