"""ast_term_rules — the agent GENERATES its AST->Term map as rewrite-rule DATA.

The map is NOT a Python emitter (that was the rejected `emit_term` cascade — composition/decisions
in the host language). The map is rewrite RULES the agent owns and the Rust engine runs. This module
holds the ONE thing that is genuine knowledge — the CORRESPONDENCE between a Python AST node type and
the agent's own Term variant (Python `Add` MEANS my `Plus`; `IfExp` MEANS my `IfThenElse`) — and a
SINGLE uniform template that expands every correspondence into a rule. There is no per-node-type
branching here: the expander is the same fold for every row, parameterised only by the row's data.
That is the categorical line vs `emit_term`, which made open-ended per-node decisions at translate
time. Here the composition (the actual AST->Term fold) happens in the Rust engine, bottom-up, when
`tick()`/`run_rules()` applies these rules to an ingested `AstNode` graph.

Encoding (per src/reflect.rs `term_from_subgraph`, what `EvalSubgraph` reconstructs):
  · a Term node has type `Term.<Variant>`
  · its children are out-edges `child.<field>`; a LIST field (items/args) carries an `index` attr
  · scalar fields (value, name, …) are node attrs
A rule fires bottom-up: it matches a parent AstNode whose needed children have ALREADY emitted their
Term (`child` then `emits`), mints the `Term.<Variant>` node, wires it to those emitted child Terms,
and marks the parent emitted. Leaves (Constant->Lit, Name->Var) fire first; parents follow at
fixpoint. The full map is just more CORRESPONDENCE rows — same template, ideally agent-extended.
"""
from __future__ import annotations

from typing import Any, Dict, List

# THE CORRESPONDENCE — the only knowledge. Each row pairs a Python AST node type with the agent's
# Term variant and how the AST children map to the Term's fields. Field plans:
#   ("leaf",)                              no children (a Lit/Var); scalars carry the data
#   ("items", [ast_field, ...])            a LIST Term field `items`, children in this order
#   ("fields", [(ast_field, term_field)])  single-child Term fields (a/b/cond/then/…)
# scalars: [(ast_attr, term_attr)] copied verbatim from the AstNode onto the Term node.
CORRESPONDENCE: List[Dict[str, Any]] = [
    {"ast": "Constant",      "term": "Lit",        "children": ("leaf",),
     "scalars": [("value", "value")]},
    {"ast": "Name",          "term": "Var",        "children": ("leaf",),
     "scalars": [("id", "name")]},
    {"ast": "BinOp:Add",     "term": "Plus",       "children": ("items", ["left", "right"])},
    {"ast": "BinOp:Mult",    "term": "Times",      "children": ("items", ["left", "right"])},
    {"ast": "BinOp:Sub",     "term": "Minus",      "children": ("fields", [("left", "a"), ("right", "b")])},
    {"ast": "BinOp:Div",     "term": "Div",        "children": ("fields", [("left", "a"), ("right", "b")])},
    {"ast": "BinOp:FloorDiv","term": "Div",        "children": ("fields", [("left", "a"), ("right", "b")])},
    {"ast": "BinOp:Pow",     "term": "Pow",        "children": ("fields", [("left", "a"), ("right", "b")])},
    {"ast": "UnaryOp:USub",  "term": "Neg",        "children": ("fields", [("operand", "arg")])},
    {"ast": "UnaryOp:Not",   "term": "Not",        "children": ("fields", [("operand", "arg")])},
    {"ast": "IfExp",         "term": "IfThenElse", "children": ("fields", [("test", "cond"),
                                                                           ("body", "then"),
                                                                           ("orelse", "other")])},
    # Comparisons: Python wraps the operator in a child cmpop node (field "ops"); the row's `guard`
    # matches+constrains that child by ast_type WITHOUT wiring it, so one Compare AST disambiguates
    # to the right Term by which op child it carries. (Single, non-chained comparisons.)
    {"ast": "Compare", "term": "Eq",  "guard": [("ops", "Eq")],
     "children": ("fields", [("left", "a"), ("comparators", "b")])},
    {"ast": "Compare", "term": "Lt",  "guard": [("ops", "Lt")],
     "children": ("fields", [("left", "a"), ("comparators", "b")])},
    {"ast": "Compare", "term": "Lte", "guard": [("ops", "LtE")],
     "children": ("fields", [("left", "a"), ("comparators", "b")])},
    {"ast": "Compare", "term": "Gt",  "guard": [("ops", "Gt")],
     "children": ("fields", [("left", "a"), ("comparators", "b")])},
    {"ast": "Compare", "term": "Gte", "guard": [("ops", "GtE")],
     "children": ("fields", [("left", "a"), ("comparators", "b")])},
]


def _attr(var: str, key: str) -> Dict[str, Any]:
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def _eq(a: Dict[str, Any], lit: Any) -> Dict[str, Any]:
    return {"type": "Eq", "a": a, "b": {"type": "Lit", "value": lit}}


def _not_emitted_yet(var: str = "p") -> Dict[str, Any]:
    """Fire-once guard: the node hasn't emitted a Term yet (no `emits` out-edge). Without it a
    plain AddNode rule re-fires every fixpoint pass."""
    return {"type": "Eq",
            "a": {"type": "Count", "source": {"type": "Neighbours",
                  "node": {"type": "Var", "name": var}, "edge_type": "emits"}},
            "b": {"type": "Lit", "value": 0}}


def rule_for(row: Dict[str, Any]) -> Dict[str, Any]:
    """The ONE uniform expansion: a correspondence row -> a rewrite-rule dict. Same shape for every
    row; no `if ast_type == …`. The child wiring is read off the row's field plan. `p` is always the
    AstNode being ported (bound via its parent `child` edge for a leaf, via its own child edges
    otherwise)."""
    ast_t, term_t, plan = row["ast"], row["term"], row["children"]
    # bind `p` = the node we port. A leaf has no child edges to match it by, so match its parent edge.
    match: List[List[str]] = [["par", "child", "p"]] if plan[0] == "leaf" else []
    where: List[Dict[str, Any]] = [_eq(_attr("p", "ast_type"), ast_t), _not_emitted_yet("p")]
    effects: List[List[Any]] = []

    # guard children: matched + constrained by ast_type, NOT wired (e.g. a Compare's op cmpop node).
    for gi, (gfield, gtype) in enumerate(row.get("guard", [])):
        gv = f"g{gi}"
        match.append(["p", "child", gv])
        where += [_eq(_attr(gv, "child_field"), gfield), _eq(_attr(gv, "ast_type"), gtype)]

    # scalar attrs copied from the AstNode (Computed: the bound parent's attr value)
    attrs: Dict[str, Any] = {}
    for ast_attr, term_attr in row.get("scalars", []):
        attrs[term_attr] = {"__term__": _attr("p", ast_attr)}
    effects.append(["add_node", "t", f"Term.{term_t}", attrs])

    if plan[0] == "leaf":
        pass  # no children; the parent itself is matched via the [p,child,c] edge
    else:
        # gather (ast_field, child_var, term_var) — each needed child must be EMITTED already
        if plan[0] == "items":
            spec = [(f, f"c{i}", f"t{i}", i) for i, f in enumerate(plan[1])]
        else:  # "fields"
            spec = [(af, f"c{i}", f"t{i}", tf) for i, (af, tf) in enumerate(plan[1])]
        for af, cv, tv, slot in spec:
            match += [["p", "child", cv], [cv, "emits", tv]]
            where.append(_eq(_attr(cv, "child_field"), af))
        for af, cv, tv, slot in spec:
            if plan[0] == "items":
                effects.append(["add_edge", "t", "child.items", tv, {"index": slot}])
            else:
                effects.append(["add_edge", "t", f"child.{slot}", tv])

    effects.append(["add_edge", "p", "emits", "t"])
    where_term = where[0] if len(where) == 1 else {"type": "And", "items": where}
    return {"name": f"ast_{term_t.lower()}_from_{ast_t.replace(':', '_').lower()}",
            "match": match, "where": where_term, "effects": effects}


# --- statement-level rules (Let from assignments, Fold from accumulation loops) -----------
# These are NOT the uniform per-node template: a statement construct is a PATTERN over a statement
# SEQUENCE (a block), so each is its own explicit rule — still rule DATA the engine runs, not a
# Python emitter. The block model: a statement `emits` the Term for "the value of the block from
# this statement onward". Return is the base case (emits its value's Term); an Assign followed by a
# successor that emits becomes a Let binding the rest; the `acc=INIT; for v in src: acc=expr;
# <rest>` idiom becomes Let{acc = Fold(...) in <rest>}. Consecutiveness in a block is read off the
# child_index attrs (s2.index == s1.index + 1, same parent, same "body" field) — pure structure.

def _idx(var: str) -> Dict[str, Any]:
    return _attr(var, "child_index")


def _consecutive(s1: str, s2: str) -> Dict[str, Any]:
    return {"type": "Eq",
            "a": {"type": "Plus", "items": [_idx(s1), {"type": "Lit", "value": 1}]},
            "b": _idx(s2)}


def _and(*conds: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "And", "items": list(conds)}


def statement_rules() -> List[Dict[str, Any]]:
    sym = lambda var: {"__term__": _attr(var, "id")}        # a Name node's id -> a Sym scalar
    return [
        # base case: Return emits its value's Term (the block tail).
        {"name": "stmt_return_tail",
         "match": [["r", "child", "v"], ["v", "emits", "tv"]],
         "where": _and(_eq(_attr("r", "ast_type"), "Return"),
                       _eq(_attr("v", "child_field"), "value"), _not_emitted_yet("r")),
         "effects": [["add_edge", "r", "emits", "tv"]]},

        # x = expr ; <rest>  ->  Let{name=x, value=expr, body=<rest>}. Fires only when the successor
        # already emits (a Return/Assign/expr stmt) — NOT when it's an accumulating For (no emit),
        # which the Fold rule claims instead.
        {"name": "stmt_assign_to_let",
         "match": [["p", "child", "s1"], ["s1", "child", "tgt"],
                   ["s1", "child", "ve"], ["ve", "emits", "tval"],
                   ["p", "child", "s2"], ["s2", "emits", "tbody"]],
         "where": _and(_eq(_attr("s1", "ast_type"), "Assign"),
                       _eq(_attr("tgt", "child_field"), "targets"),
                       _eq(_attr("tgt", "ast_type"), "Name"),
                       _eq(_attr("ve", "child_field"), "value"),
                       _eq(_attr("s1", "child_field"), "body"),
                       _eq(_attr("s2", "child_field"), "body"),
                       _consecutive("s1", "s2"), _not_emitted_yet("s1")),
         "effects": [["add_node", "let", "Term.Let", {"name": sym("tgt")}],
                     ["add_edge", "let", "child.value", "tval"],
                     ["add_edge", "let", "child.body", "tbody"],
                     ["add_edge", "s1", "emits", "let"]]},

        # acc = INIT ; for v in SRC: acc = EXPR ; <rest>  ->  Let{acc = Fold(SRC,v,acc,INIT,EXPR) in <rest>}
        {"name": "stmt_accumulator_to_fold",
         "match": [["p", "child", "ia"], ["ia", "child", "itgt"],
                   ["ia", "child", "ie"], ["ie", "emits", "tinit"],
                   ["p", "child", "fo"],
                   ["fo", "child", "src"], ["src", "emits", "tsrc"],
                   ["fo", "child", "ftgt"],
                   ["fo", "child", "fb"], ["fb", "child", "be"], ["be", "emits", "tbody"],
                   ["p", "child", "s2"], ["s2", "emits", "tcont"]],
         "where": _and(_eq(_attr("ia", "ast_type"), "Assign"),
                       _eq(_attr("itgt", "child_field"), "targets"),
                       _eq(_attr("itgt", "ast_type"), "Name"),
                       _eq(_attr("ie", "child_field"), "value"),
                       _eq(_attr("fo", "ast_type"), "For"),
                       _eq(_attr("src", "child_field"), "iter"),
                       _eq(_attr("ftgt", "child_field"), "target"),
                       _eq(_attr("ftgt", "ast_type"), "Name"),
                       _eq(_attr("fb", "child_field"), "body"),
                       _eq(_attr("fb", "ast_type"), "Assign"),
                       _eq(_attr("be", "child_field"), "value"),
                       _eq(_attr("ia", "child_field"), "body"),
                       _eq(_attr("fo", "child_field"), "body"),
                       _eq(_attr("s2", "child_field"), "body"),
                       _consecutive("ia", "fo"), _consecutive("fo", "s2"),
                       _not_emitted_yet("ia")),
         "effects": [["add_node", "fold", "Term.Fold",
                      {"var_name": sym("ftgt"), "acc_name": sym("itgt")}],
                     ["add_edge", "fold", "child.source", "tsrc"],
                     ["add_edge", "fold", "child.init", "tinit"],
                     ["add_edge", "fold", "child.body", "tbody"],
                     ["add_node", "let", "Term.Let", {"name": sym("itgt")}],
                     ["add_edge", "let", "child.value", "fold"],
                     ["add_edge", "let", "child.body", "tcont"],
                     ["add_edge", "ia", "emits", "let"]]},

        # out = [] ; for u in SRC: if C: out.append(EXPR) ; return out  ->  Let{out = Fold(...)}
        #   Fold{source:SRC, var_name:u, acc_name:out, init:{}(empty),
        #        body: IfThenElse{cond:C, then:Append(out, EXPR), other:out}}
        # The Fold form exposes the ACCUMULATOR (acc_name=out) to C and EXPR, so it handles BOTH the
        # loop-var case AND the acc-dependent stateful scan (collapse_runs: `not out or out[-1]!=u`)
        # — using the Layer-B Append (ordered concat) + Last/IndexAt (via subscript). Universally
        # faithful + ordered, so it subsumes the earlier MapList/FilterList conditional-append rule.
        {"name": "stmt_conditional_append_to_fold",
         "match": [["p", "child", "ia"], ["ia", "child", "itgt"], ["ia", "child", "ival"],
                   ["p", "child", "fo"], ["fo", "child", "ftgt"],
                   ["fo", "child", "src"], ["src", "emits", "tsrc"],
                   ["fo", "child", "fb"], ["fb", "child", "ctest"], ["ctest", "emits", "tC"],
                   ["fb", "child", "appstmt"], ["appstmt", "child", "appcall"],
                   ["appcall", "child", "appfunc"], ["appfunc", "child", "appobj"],
                   ["appcall", "child", "argexpr"], ["argexpr", "emits", "tEXPR"],
                   ["p", "child", "s2"], ["s2", "emits", "tcont"]],
         "where": _and(
             _eq(_attr("ia", "ast_type"), "Assign"),
             _eq(_attr("itgt", "child_field"), "targets"), _eq(_attr("itgt", "ast_type"), "Name"),
             _eq(_attr("ival", "child_field"), "value"), _eq(_attr("ival", "ast_type"), "List"),
             _eq(_attr("fo", "ast_type"), "For"),
             _eq(_attr("ftgt", "child_field"), "target"), _eq(_attr("ftgt", "ast_type"), "Name"),
             _eq(_attr("src", "child_field"), "iter"),
             _eq(_attr("fb", "child_field"), "body"), _eq(_attr("fb", "ast_type"), "If"),
             _eq(_count_children("fb"), 2),                       # test + one body stmt, no else
             _eq(_attr("ctest", "child_field"), "test"),
             _eq(_attr("appstmt", "child_field"), "body"), _eq(_attr("appstmt", "ast_type"), "Expr"),
             _eq(_attr("appcall", "child_field"), "value"), _eq(_attr("appcall", "ast_type"), "Call"),
             _eq(_attr("appfunc", "child_field"), "func"),
             _eq(_attr("appfunc", "ast_type"), "Attribute"), _eq(_attr("appfunc", "attr"), "append"),
             _eq(_attr("appobj", "child_field"), "value"), _eq(_attr("appobj", "ast_type"), "Name"),
             {"type": "Eq", "a": _attr("appobj", "id"), "b": _attr("itgt", "id")},  # append to acc
             _eq(_attr("argexpr", "child_field"), "args"),
             _eq(_attr("ia", "child_field"), "body"), _eq(_attr("fo", "child_field"), "body"),
             _eq(_attr("s2", "child_field"), "body"),
             _consecutive("ia", "fo"), _consecutive("fo", "s2"), _not_emitted_yet("ia")),
         "effects": [
             ["add_node", "initset", "Term.SetT", {}],                 # empty init; Append -> Tuple
             ["add_node", "accv1", "Term.Var", {"name": {"__term__": _attr("itgt", "id")}}],
             ["add_node", "accv2", "Term.Var", {"name": {"__term__": _attr("itgt", "id")}}],
             ["add_node", "app", "Term.Append", {}],
             ["add_edge", "app", "child.seq", "accv1"],
             ["add_edge", "app", "child.item", "tEXPR"],
             ["add_node", "ite", "Term.IfThenElse", {}],
             ["add_edge", "ite", "child.cond", "tC"],
             ["add_edge", "ite", "child.then", "app"],
             ["add_edge", "ite", "child.other", "accv2"],
             ["add_node", "fold", "Term.Fold", {"var_name": {"__term__": _attr("ftgt", "id")},
                                                "acc_name": {"__term__": _attr("itgt", "id")}}],
             ["add_edge", "fold", "child.source", "tsrc"],
             ["add_edge", "fold", "child.init", "initset"],
             ["add_edge", "fold", "child.body", "ite"],
             ["add_node", "let", "Term.Let", {"name": {"__term__": _attr("itgt", "id")}}],
             ["add_edge", "let", "child.value", "fold"],
             ["add_edge", "let", "child.body", "tcont"],
             ["add_edge", "ia", "emits", "let"]]},
    ]


# --- extra expression rules that don't fit the per-node template -----------------------------
# BoolOp is variadic (Python flattens `a and b and c` to one node with N values); Subscript carries
# its index as a slice child (constant or unary-minus); a comprehension is a filtered iteration.
# Each is rule DATA; only their shape differs from the uniform per-node rows.

def _count_children(var: str) -> Dict[str, Any]:
    return {"type": "Count", "source": {"type": "Neighbours",
            "node": {"type": "Var", "name": var}, "edge_type": "child"}}


def boolop_rules(max_arity: int = 4) -> List[Dict[str, Any]]:
    """`a and b…` / `a or b…` -> the OPERAND semantics Python actually has (and/or return an OPERAND,
    not a bool): `a or b` == `a if a else b`, `a and b` == `b if a else a`, right-nested for N. This
    is faithful in BOTH value context (`x = a or default`) AND boolean context (a condition then
    truthy-tests the operand — same result), so it replaces the boolean And/Or shortcut and its
    caveat. Python flattens to one node with N values, so one fixed-arity rule per (op, N) with an
    EXACT-arity guard `Count(children)==N+1` (op child + N values) so a lower-arity rule can't fire
    on a higher-arity node and drop values. (Pure Terms, so re-using a value Term for cond+branch is
    a harmless double-eval, not a side effect; a Let-desugar would avoid it if effects ever mattered.)
    """
    out: List[Dict[str, Any]] = []
    for ast_t, op in (("BoolOp:And", "and"), ("BoolOp:Or", "or")):
        for n in range(2, max_arity + 1):
            match: List[List[str]] = []
            where = [_eq(_attr("p", "ast_type"), ast_t),
                     _eq(_count_children("p"), n + 1), _not_emitted_yet("p")]
            for i in range(n):
                cv, tv = f"c{i}", f"t{i}"
                match += [["p", "child", cv], [cv, "emits", tv]]
                where += [_eq(_attr(cv, "child_field"), "values"), _eq(_idx(cv), i)]
            # right-nested IfThenElse: level i tests value t{i}; the tail is t{n-1}.
            effects: List[List[Any]] = [["add_node", f"ite{i}", "Term.IfThenElse", {}]
                                        for i in range(n - 1)]
            for i in range(n - 1):
                ite, ti = f"ite{i}", f"t{i}"
                nxt = f"ite{i + 1}" if i < n - 2 else f"t{n - 1}"
                if op == "or":      # a if a else <rest>
                    effects += [["add_edge", ite, "child.cond", ti],
                                ["add_edge", ite, "child.then", ti],
                                ["add_edge", ite, "child.other", nxt]]
                else:               # and: <rest> if a else a
                    effects += [["add_edge", ite, "child.cond", ti],
                                ["add_edge", ite, "child.then", nxt],
                                ["add_edge", ite, "child.other", ti]]
            effects.append(["add_edge", "p", "emits", "ite0"])
            out.append({"name": f"expr_{op}_{n}ary_operand",
                        "match": match, "where": {"type": "And", "items": where},
                        "effects": effects})
    return out


def subscript_rules() -> List[Dict[str, Any]]:
    """`seq[idx]` -> IndexAt{seq, index} for ANY index whose slice emits a Term — a constant, a
    negative/from-end literal (`seq[-1]`, the slice is `Neg(Lit 1)`), or a dynamic expression
    (`seq[i]`, `seq[i-1]`). IndexAt (a Layer-B primitive) evaluates its index dynamically with
    Python-style from-end semantics, so this one rule subsumes the old non-negative-only `Nth` rule
    and closes the from-end-indexing residual."""
    return [
        {"name": "expr_subscript_indexat",
         "match": [["p", "child", "val"], ["val", "emits", "tv"],
                   ["p", "child", "sl"], ["sl", "emits", "tidx"]],
         "where": {"type": "And", "items": [
             _eq(_attr("p", "ast_type"), "Subscript"),
             _eq(_attr("val", "child_field"), "value"),
             _eq(_attr("sl", "child_field"), "slice"), _not_emitted_yet("p")]},
         "effects": [["add_node", "t", "Term.IndexAt", {}],
                     ["add_edge", "t", "child.seq", "tv"],
                     ["add_edge", "t", "child.index", "tidx"],
                     ["add_edge", "p", "emits", "t"]]},
    ]


def _comprehension_family(ast_t: str, filter_term: str, map_term: str) -> List[Dict[str, Any]]:
    """The three comprehension rules for one collection kind, parameterised by its iteration Terms:
      · `{/[ x for x in src if pred ]}`     (identity elt) -> <filter_term>{source, var_name, predicate}
      · `{/[ f(x) for x in src ]}`          (transforming) -> <map_term>{source, var_name, value}
      · `{/[ f(x) for x in src if pred ]}`  -> <map_term> over <filter_term>
    SetComp uses the SET-valued Filter/MapSet (reorder+dedup = set semantics); ListComp uses the
    ORDERED FilterList/MapList (added via Layer B) — order + duplicates preserved = list semantics.
    Identity-vs-transforming is a `Not(Eq(elt.id,tgt.id))` guard; no-if vs if is
    `Count(comprehension children) == 2 or 3` (target, iter, [ifs])."""
    kind = "list" if ast_t == "ListComp" else "set"
    gen_match = [["p", "child", "gen"], ["gen", "child", "tgt"],
                 ["gen", "child", "itr"], ["itr", "emits", "tsrc"]]
    gen_where = [_eq(_attr("p", "ast_type"), ast_t),
                 _eq(_attr("gen", "child_field"), "generators"),
                 _eq(_attr("gen", "ast_type"), "comprehension"),
                 _eq(_attr("tgt", "child_field"), "target"), _eq(_attr("tgt", "ast_type"), "Name"),
                 _eq(_attr("itr", "child_field"), "iter")]
    identity = {"type": "Eq", "a": _attr("elt", "id"), "b": _attr("tgt", "id")}
    transforming = {"type": "Not", "arg": identity}
    sym_var = {"var_name": {"__term__": _attr("tgt", "id")}}
    return [
        # {x for x in src if pred}  -> Filter / FilterList
        {"name": f"expr_{kind}filter_identity_if",
         "match": [["p", "child", "elt"]] + gen_match
                  + [["gen", "child", "pred"], ["pred", "emits", "tpred"]],
         "where": {"type": "And", "items": gen_where + [
             _eq(_attr("elt", "child_field"), "elt"), _eq(_attr("elt", "ast_type"), "Name"),
             identity, _eq(_attr("pred", "child_field"), "ifs"),
             _eq(_count_children("gen"), 3), _not_emitted_yet("p")]},
         "effects": [["add_node", "t", f"Term.{filter_term}", sym_var],
                     ["add_edge", "t", "child.source", "tsrc"],
                     ["add_edge", "t", "child.predicate", "tpred"],
                     ["add_edge", "p", "emits", "t"]]},
        # {f(x) for x in src}  -> MapSet / MapList
        {"name": f"expr_{kind}map_noif",
         "match": [["p", "child", "elt"], ["elt", "emits", "telt"]] + gen_match,
         "where": {"type": "And", "items": gen_where + [
             _eq(_attr("elt", "child_field"), "elt"), transforming,
             _eq(_count_children("gen"), 2), _not_emitted_yet("p")]},
         "effects": [["add_node", "t", f"Term.{map_term}", sym_var],
                     ["add_edge", "t", "child.source", "tsrc"],
                     ["add_edge", "t", "child.value", "telt"],
                     ["add_edge", "p", "emits", "t"]]},
        # {f(x) for x in src if pred}  -> Map over Filter
        {"name": f"expr_{kind}map_if",
         "match": [["p", "child", "elt"], ["elt", "emits", "telt"]] + gen_match
                  + [["gen", "child", "pred"], ["pred", "emits", "tpred"]],
         "where": {"type": "And", "items": gen_where + [
             _eq(_attr("elt", "child_field"), "elt"), transforming,
             _eq(_attr("pred", "child_field"), "ifs"),
             _eq(_count_children("gen"), 3), _not_emitted_yet("p")]},
         "effects": [["add_node", "flt", f"Term.{filter_term}", sym_var],
                     ["add_edge", "flt", "child.source", "tsrc"],
                     ["add_edge", "flt", "child.predicate", "tpred"],
                     ["add_node", "t", f"Term.{map_term}", sym_var],
                     ["add_edge", "t", "child.source", "flt"],
                     ["add_edge", "t", "child.value", "telt"],
                     ["add_edge", "p", "emits", "t"]]},
    ]


def noteq_rule() -> List[Dict[str, Any]]:
    """`a != b` -> Not{Eq{a, b}}. NotEq has no single Term (unlike Eq/Lt/Lte/Gt/Gte), so it needs the
    two-node form — separate from the uniform comparison rows. (Common: collapse_runs' `out[-1] != u`.)"""
    return [{
        "name": "expr_compare_noteq",
        "match": [["p", "child", "cl"], ["cl", "emits", "ta"],
                  ["p", "child", "cr"], ["cr", "emits", "tb"], ["p", "child", "op"]],
        "where": {"type": "And", "items": [
            _eq(_attr("p", "ast_type"), "Compare"),
            _eq(_attr("cl", "child_field"), "left"),
            _eq(_attr("cr", "child_field"), "comparators"),
            _eq(_attr("op", "child_field"), "ops"), _eq(_attr("op", "ast_type"), "NotEq"),
            _not_emitted_yet("p")]},
        "effects": [["add_node", "eq", "Term.Eq", {}],
                    ["add_edge", "eq", "child.a", "ta"], ["add_edge", "eq", "child.b", "tb"],
                    ["add_node", "t", "Term.Not", {}], ["add_edge", "t", "child.arg", "eq"],
                    ["add_edge", "p", "emits", "t"]]}]


def mathcall_rules() -> List[Dict[str, Any]]:
    """numpy / math calls are MECHANICAL, not faculty composition. A 1-arg call to a math op (bare
    `abs(x)` or `np.abs(x)`) -> the unary Term (`Abs`/`Sqrt`/`Log`/`Exp`); any other `np.<op>(...)`
    call -> `UseTool{tool=<op>, args=[...]}` (the np namespace IS the held-leaf boundary — UseTool
    dispatches to a registered Rust/Python handler from inside the evaluator). The func is matched +
    constrained by name but not wired; arity-guarded by `Count(children)`."""
    out: List[Dict[str, Any]] = []

    def fname_is(op: str) -> Dict[str, Any]:     # the call's func is named `op` (bare Name or np.<op>)
        return {"type": "Or", "items": [_eq(_attr("fn", "id"), op), _eq(_attr("fn", "attr"), op)]}

    # 1-arg unary math ops -> their Term (arg field).
    for op, term in (("abs", "Abs"), ("sqrt", "Sqrt"), ("log", "Log"), ("exp", "Exp")):
        out.append({
            "name": f"expr_{op}_call",
            "match": [["p", "child", "fn"], ["p", "child", "a0"], ["a0", "emits", "ta"]],
            "where": _and(_eq(_attr("p", "ast_type"), "Call"),
                          _eq(_attr("fn", "child_field"), "func"), fname_is(op),
                          _eq(_attr("a0", "child_field"), "args"),
                          _eq(_count_children("p"), 2), _not_emitted_yet("p")),
            "effects": [["add_node", "t", f"Term.{term}", {}],
                        ["add_edge", "t", "child.arg", "ta"], ["add_edge", "p", "emits", "t"]]})

    # generic np.<op>(x) / np.<op>(x, y) -> UseTool{tool=<op>, args=[...]}. Restricted to the `np`
    # namespace (func is Attribute whose value is Name "np") so it never absorbs self.method() calls.
    for n in (1, 2):
        match = [["p", "child", "fn"], ["fn", "child", "ns"]]
        where = [_eq(_attr("p", "ast_type"), "Call"),
                 _eq(_attr("fn", "child_field"), "func"), _eq(_attr("fn", "ast_type"), "Attribute"),
                 _eq(_attr("ns", "child_field"), "value"), _eq(_attr("ns", "id"), "np"),
                 _eq(_count_children("p"), n + 1), _not_emitted_yet("p")]
        effects: List[Any] = [["add_node", "t", "Term.UseTool",
                               {"tool": {"__term__": _attr("fn", "attr")}}]]
        for i in range(n):
            match += [["p", "child", f"a{i}"], [f"a{i}", "emits", f"t{i}"]]
            where += [_eq(_attr(f"a{i}", "child_field"), "args"), _eq(_idx(f"a{i}"), i)]
            effects.append(["add_edge", "t", "child.args", f"t{i}", {"index": i}])
        effects.append(["add_edge", "p", "emits", "t"])
        out.append({"name": f"expr_np_usetool_{n}", "match": match,
                    "where": {"type": "And", "items": where}, "effects": effects})
    return out


def attribute_rule() -> List[Dict[str, Any]]:
    """`obj.attr` (an Attribute READ, e.g. `self.threshold`) -> Attr{node=obj, key=attr}. The state
    read a STATE method's condition/value needs, so its where/value expression can be composed by the
    rules + read out to Term-JSON (the AST->Rule migrator). (A method-call's `obj.method` Attribute
    also matches but only matters where it's used as a value — method calls are residual anyway.)"""
    return [{
        "name": "expr_attr_from_attribute",
        "match": [["p", "child", "obj"], ["obj", "emits", "tobj"]],
        "where": {"type": "And", "items": [
            _eq(_attr("p", "ast_type"), "Attribute"),
            _eq(_attr("obj", "child_field"), "value"), _not_emitted_yet("p")]},
        "effects": [["add_node", "t", "Term.Attr", {"key": {"__term__": _attr("p", "attr")}}],
                    ["add_edge", "t", "child.node", "tobj"],
                    ["add_edge", "p", "emits", "t"]]}]


def comprehension_rules() -> List[Dict[str, Any]]:
    """SET comprehensions -> set-valued Filter/MapSet; LIST comprehensions -> the ordered FilterList/
    MapList (Layer-B primitives) — both now faithful (set: dedup+unordered; list: order+duplicates)."""
    return (_comprehension_family("SetComp", "Filter", "MapSet")
            + _comprehension_family("ListComp", "FilterList", "MapList"))


def generate_rules() -> List[Dict[str, Any]]:
    """The agent's rule set: every correspondence row through the one template, the statement-level
    patterns (Let, Fold), and the non-template expression rules (BoolOp, Subscript, comprehension)."""
    return ([rule_for(row) for row in CORRESPONDENCE] + statement_rules()
            + boolop_rules() + subscript_rules() + comprehension_rules() + noteq_rule()
            + attribute_rule() + mathcall_rules())


def install(substrate) -> Dict[str, Any]:
    """Open the Term-graph grammar (Term.* nodes; child.*/emits edges) and install the generated
    rules into the native engine. Returns {n_rules, variants}."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    variants = sorted({r["term"] for r in CORRESPONDENCE}
                      | {"Let", "Fold", "Nth", "Filter", "MapSet", "IfThenElse",
                         "FilterList", "MapList", "Last", "IndexAt", "Append", "SetT", "Attr",
                         "Abs", "Sqrt", "Log", "Exp", "UseTool"})
    # admit AstNode --emits--> Term.X and Term.X --child.*--> Term.Y (idempotent).
    fields = ["items", "a", "b", "arg", "cond", "then", "other", "value", "body",
              "source", "init", "predicate", "seq", "item", "index", "node", "args"]
    for v in variants:
        for et, tgtset in (("emits", variants),):
            for tv in tgtset:
                _try_prod(substrate, "AstNode", et, f"Term.{tv}")
        for f in fields:
            for tv in variants:
                _try_prod(substrate, f"Term.{v}", f"child.{f}", f"Term.{tv}")
    rules = generate_rules()
    for r in rules:
        nat.add_rule(r)
    return {"n_rules": len(rules), "variants": variants}


def _try_prod(substrate, src_t: str, edge: str, tgt_t: str) -> None:
    try:
        substrate.add_production({"src": {"type": src_t, "var": "a"}, "edge_type": edge,
                                  "tgt": {"type": tgt_t, "var": "b"}, "where": None,
                                  "provenance": "ast_term_rules"})
    except Exception:
        pass


def _rule_family(name: str) -> str:
    """The architectural family of a rule, from its name — the `category` the cortex scores for
    separation-of-concerns and data-drivenness."""
    if "compare" in name or any(name.startswith(f"ast_{c}_") for c in ("eq", "lt", "lte", "gt", "gte")):
        return "comparison"
    if "_and_" in name or "_or_" in name or "operand" in name:
        return "boolean"
    if "ifthenelse" in name or "ifexp" in name:
        return "conditional"
    if "subscript" in name or "indexat" in name:
        return "indexing"
    if "filter" in name or "map" in name or "comprehension" in name:
        return "comprehension"
    if name.startswith("stmt_") and ("fold" in name or "accumulator" in name or "append" in name):
        return "iteration"
    if name.startswith("stmt_"):
        return "binding"
    if "not_from" in name:
        return "boolean"
    return "arithmetic"


def assess_rule_set(substrate) -> dict:
    """Have the agent's ArchitectureCortex assess the generated AST->Term rule set — its OWN verdict,
    not the author's. The rules live in the engine's rule store (not graph nodes), so represent the
    set as graph data the cortex can query: a Microtheory whose Concepts ARE the rules (each carrying
    its family `category` + the Term it emits), then run the cortex's graph-resident quality scorers +
    smell detectors over it. `substrate` must have the cortex vocabulary productions open
    (e.g. scripts.ask_the_substrate.fresh_substrate()). Returns {..., qualities:[...], smells:[...]}."""
    from domains.architecture_cortex import ArchitectureCortex
    cortex = ArchitectureCortex(substrate).install()
    mt = substrate.add_node("Microtheory", {
        "name": "ast_term_port_map",
        "definition": "the agent's Python-AST -> native-Term rewrite-rule map"})
    for r in generate_rules():
        emitted = next((e[2] for e in r["effects"] if e[0] == "add_node"), "")
        c = substrate.add_node("Concept", {
            "name": r["name"], "category": _rule_family(r["name"]),
            "definition": f"rewrite rule emitting {emitted.removeprefix('Term.') or '?'}",
            "origin": "ast_term_rules"})
        substrate.add_edge(mt, "has_concept", c)
    aid = cortex.assess(mt)
    out = dict(substrate.node(aid)["attrs"])
    out["qualities"] = [{
        "quality_name": str(substrate.node(qs)["attrs"].get("quality_name", "")),
        "score": int(substrate.node(qs)["attrs"].get("score", 0)),
        "max_score": int(substrate.node(qs)["attrs"].get("max_score", 0)),
        "rationale": str(substrate.node(qs)["attrs"].get("rationale", ""))[:160],
    } for qs in substrate.neighbours(aid, "scored_on")]
    out["smells"] = [{
        "smell_name": str(substrate.node(si)["attrs"].get("smell_name", "")),
        "rationale": str(substrate.node(si)["attrs"].get("rationale", ""))[:160],
    } for si in substrate.neighbours(aid, "detected_smell")]
    return out


__all__ = ["CORRESPONDENCE", "rule_for", "generate_rules", "install", "assess_rule_set"]
