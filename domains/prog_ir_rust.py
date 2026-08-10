"""prog_ir_rust — the RUST frame's CST → hub Program-IR reader (P2).

The rust half of PROGRAM_SYNTHESIS_PLAN.md §4-P2: a `.rs` source is parsed
by the mechanical tree-sitter world adapter (`domains/ts_ingest.ingest_source`
→ CstNode graph), then FOLDED into the hub Program IR (the P1 `Prog*` Term
variants + the expression DSL) by APPLYING the correspondence table shipped
as seed data (`seeds/rust_correspondence.json`). The correspondence — which
cst kind MEANS which Term — is the seed's rows; this module contributes only
the registered SHAPE HANDLERS the rows name (mechanical desugars: block →
ProgSeq, tail expression → ProgReturn, `0..n` → the range oracle, vec![] →
ProgContainerLit, …) and the mechanical read-out (`read_source` /
`read_function`). No per-construct if/elif outside table dispatch; no graph-
state decisions (CLAUDE.md: this whole module is a cross-frame map — plan
§2's frame doctrine — and cross-frame maps are where non-graph machinery is
allowed to live).

Honest residuals: any construct outside the P2 scope (match, closures,
generics, borrows, traits, structs, `&`/`*`, vec![x; n], tuple patterns,
…) blocks the read — the result is {ok: False, blockers: [cst kinds]},
NEVER a silent partial emit.

Semantics ledger (details + fixture verification in
PROGRAM_SYNTHESIS_P2_RUST_LUA.md): integer `/` and `/=` map to IDiv, which
TRUNCATES like rust (exact for i64); `%` maps to Mod, which is floor-style
(diverges from rust on negative operands — fixtures avoid); i64 wrap-around
is NOT modeled (DSL ints are unbounded); param types are recorded as
annotations in the read-out record, not in the (untyped-at-P2) IR.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from domains import ts_ingest

_L = lambda v: {"type": "Lit", "value": v}  # noqa: E731

# IR types that are STATEMENTS: emitting one into a value slot would be a
# category error the fixtures could silently mis-evaluate — refused by name.
_STMT_TYPES = frozenset({
    "ProgSeq", "ProgAssignVar", "ProgAugAssign", "ProgIfStmt", "ProgForEach",
    "ProgWhile", "ProgLoopCtl", "ProgReturn", "ProgTryOr", "ProgRaise",
    "ProgImportStmt", "ProgSubscriptSet", "ProgAttrSet", "ProgTupleUnpack",
    "ProgDefFnParam",
})

# rust statement-position CST kinds inside a block; anything else named is
# an expression (a tail if last — rust's implicit return position).
_RUST_STMT_KINDS = frozenset({
    "let_declaration", "expression_statement", "empty_statement",
})

_AUG_OPS = {"+=": "add", "-=": "sub", "*=": "mult", "/=": "floordiv",
            "%=": "mod"}


def _expr(w, ir: Dict[str, Any]) -> Dict[str, Any]:
    """Guard: a statement emitted into a value position is a blocker."""
    if ir.get("type") in _STMT_TYPES:
        return w.block(f"statement_in_value_position:{ir.get('type')}")
    return ir


def _stmt_of(stmts: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(stmts) == 1:
        return stmts[0]
    return {"type": "ProgSeq", "stmts": stmts}


def _block_parts(w, block) -> tuple:
    """A rust block's (statements, tail-expression-or-None) — the tail is
    the LAST named child when it is a bare expression, OR an
    expression_statement WITHOUT a trailing `;` (tree-sitter wraps
    block-like expressions — if/loop/while — in expression_statement even
    in rust's implicit-value tail position)."""
    stmts: List[Dict[str, Any]] = []
    tail = None
    named = w.named_children(block)
    for i, c in enumerate(named):
        k = w.kind(c)
        if k == "empty_statement":
            continue
        last = i == len(named) - 1
        if k == "expression_statement":
            has_semi = any(w.text(t) == ";" for t in w.children(c))
            if last and not has_semi:
                inner = w.named_children(c)
                tail = w.emit(inner[0]) if inner else None
            else:
                stmts.append(w.emit(c))
        elif k in _RUST_STMT_KINDS:
            stmts.append(w.emit(c))
        elif last:
            tail = w.emit(c)
        else:
            stmts.append(w.block(f"block_inner_expression:{k}"))
    return stmts, tail


def _loop_body(w, block) -> Dict[str, Any]:
    """A loop body: statements; a tail expression is a discarded value in
    rust loop position — emitted as a bare expression statement."""
    stmts, tail = _block_parts(w, block)
    if tail is not None:
        stmts.append(tail)
    return _stmt_of(stmts)


def _range_call(w, rng) -> Dict[str, Any]:
    named = w.named_children(rng)
    if len(named) != 2:
        return w.block("range_form")
    lo = _expr(w, w.emit(named[0]))
    hi = _expr(w, w.emit(named[1]))
    inclusive = any(w.text(c) == "..=" for c in w.children(rng))
    if inclusive:
        hi = {"type": "Plus", "items": [hi, _L(1)]}
    return {"type": "ProgCallExtern", "name": "range", "recv": None,
            "args": [lo, hi]}


# ---------------------------------------------------------------------------
# The registered handlers (row → name → mechanical shape transformer).
# ---------------------------------------------------------------------------
def rs_unwrap_first(w, nid, row):
    named = w.named_children(nid)
    if not named:
        return w.block("empty_expression_statement")
    return w.emit(named[0])


def rs_unwrap_paren(w, nid, row):
    named = w.named_children(nid)
    if len(named) != 1:
        return w.block("paren_form")
    return w.emit(named[0])


def rs_unary(w, nid, row):
    named = w.named_children(nid)
    if not named:
        return w.block("unary_form")
    op = w.text(w.children(nid)[0])
    arg = _expr(w, w.emit(named[0]))
    if op == "-":
        return {"type": "Neg", "arg": arg}
    if op == "!":
        return {"type": "Not", "arg": arg}
    return w.block(f"unary_operator:{op}")


def rs_let(w, nid, row):
    pat = w.field_child(nid, "pattern")
    if pat is None or w.kind(pat) != "identifier":
        return w.block(f"let_pattern:{w.kind(pat) if pat is not None else 'missing'}")
    value = w.field_child(nid, "value")
    if value is None:
        return w.block("let_uninitialized")
    return {"type": "ProgAssignVar", "name": w.text(pat),
            "value": _expr(w, w.emit(value))}


def rs_assign(w, nid, row):
    left = w.field_child(nid, "left")
    right = w.field_child(nid, "right")
    value = _expr(w, w.emit(right))
    if w.kind(left) == "identifier":
        return {"type": "ProgAssignVar", "name": w.text(left), "value": value}
    if w.kind(left) == "index_expression":
        parts = w.named_children(left)
        if len(parts) != 2:
            return w.block("index_form")
        return {"type": "ProgSubscriptSet", "obj": _expr(w, w.emit(parts[0])),
                "index": _expr(w, w.emit(parts[1])), "value": value}
    return w.block(f"assign_target:{w.kind(left)}")


def rs_compound_assign(w, nid, row):
    op_child = w.field_child(nid, "operator")
    op = _AUG_OPS.get(w.text(op_child) if op_child is not None else "")
    if op is None:
        return w.block(f"compound_op:{w.text(op_child)}")
    left = w.field_child(nid, "left")
    if w.kind(left) != "identifier":
        return w.block(f"compound_target:{w.kind(left)}")
    return {"type": "ProgAugAssign", "name": w.text(left), "op": op,
            "value": _expr(w, w.emit_field(nid, "right"))}


def rs_if(w, nid, row):
    """Pure (tail-only) branches → IfThenElse expression; statement
    branches → ProgIfStmt. A branch mixing statements AND a tail value is
    the honest blocker (its value would be silently lost)."""
    cond = _expr(w, w.emit_field(nid, "condition"))
    cs, ct = _block_parts(w, w.field_child(nid, "consequence"))
    if cs and ct is not None:
        return w.block("if_branch_mixed_tail")
    then_pure = ct if not cs else None

    alt = w.field_child(nid, "alternative")  # else_clause
    if alt is None:
        # valueless if statement.
        then_ir = then_pure if then_pure is not None else _stmt_of(cs)
        return {"type": "ProgIfStmt", "cond": cond, "then": then_ir,
                "orelse": None}
    alt_named = w.named_children(alt)
    if len(alt_named) != 1:
        return w.block("else_clause_form")
    alt_node = alt_named[0]
    if w.kind(alt_node) == "if_expression":
        alt_ir = w.emit(alt_node)           # else-if chain, recursively
        alt_pure = alt_ir if alt_ir.get("type") == "IfThenElse" else None
    elif w.kind(alt_node) == "block":
        as_, at = _block_parts(w, alt_node)
        if as_ and at is not None:
            return w.block("if_branch_mixed_tail")
        alt_pure = at if not as_ else None
        alt_ir = alt_pure if alt_pure is not None else _stmt_of(as_)
    else:
        return w.block(f"else_body:{w.kind(alt_node)}")

    if then_pure is not None and alt_pure is not None:
        return {"type": "IfThenElse", "cond": cond, "then": then_pure,
                "other": alt_pure}
    then_ir = then_pure if then_pure is not None else _stmt_of(cs)
    return {"type": "ProgIfStmt", "cond": cond, "then": then_ir,
            "orelse": alt_ir}


def rs_while(w, nid, row):
    return {"type": "ProgWhile",
            "cond": _expr(w, w.emit_field(nid, "condition")),
            "body": _loop_body(w, w.field_child(nid, "body")),
            "orelse": None}


def rs_loop(w, nid, row):
    return {"type": "ProgWhile", "cond": _L(True),
            "body": _loop_body(w, w.field_child(nid, "body")),
            "orelse": None}


def rs_for(w, nid, row):
    pat = w.field_child(nid, "pattern")
    if pat is None or w.kind(pat) != "identifier":
        return w.block(f"for_pattern:{w.kind(pat) if pat is not None else 'missing'}")
    val = w.field_child(nid, "value")
    if w.kind(val) == "range_expression":
        it = _range_call(w, val)
    else:
        it = _expr(w, w.emit(val))
    return {"type": "ProgForEach", "var": w.text(pat), "iter": it,
            "body": _loop_body(w, w.field_child(nid, "body")),
            "orelse": None}


def rs_break(w, nid, row):
    if w.named_children(nid):
        return w.block("break_with_value")
    return {"type": "ProgLoopCtl", "kind": "break"}


def rs_continue(w, nid, row):
    return {"type": "ProgLoopCtl", "kind": "continue"}


def rs_return(w, nid, row):
    named = w.named_children(nid)
    value = _expr(w, w.emit(named[0])) if named else None
    return {"type": "ProgReturn", "value": value}


def rs_call(w, nid, row):
    fn = w.field_child(nid, "function")
    args_node = w.field_child(nid, "arguments")
    args = [_expr(w, w.emit(c)) for c in w.named_children(args_node)] \
        if args_node is not None else []
    k = w.kind(fn)
    if k == "identifier":
        return {"type": "ProgCallExtern", "name": w.text(fn), "recv": None,
                "args": args}
    if k == "scoped_identifier":
        # assoc call — the dotted (path-qualified) name verbatim.
        return {"type": "ProgCallExtern", "name": w.flat_text(fn),
                "recv": None, "args": args}
    if k == "field_expression":
        recv = _expr(w, w.emit_field(fn, "value"))
        name_child = w.field_child(fn, "field")
        return {"type": "ProgCallExtern", "name": w.text(name_child),
                "recv": recv, "args": args}
    return w.block(f"call_function:{k}")


def rs_macro(w, nid, row):
    macro = w.field_child(nid, "macro")
    if macro is None or w.text(macro) != "vec":
        return w.block(f"macro:{w.text(macro) if macro is not None else '?'}")
    tt = next((c for c in w.children(nid) if w.kind(c) == "token_tree"), None)
    if tt is None:
        return w.block("vec_form")
    if any(w.text(c) == ";" for c in w.children(tt)):
        return w.block("vec_repeat")
    items = [_expr(w, w.emit(c)) for c in w.named_children(tt)]
    return {"type": "ProgContainerLit", "kind": "list", "items": items}


def rs_array(w, nid, row):
    items = [_expr(w, w.emit(c)) for c in w.named_children(nid)]
    return {"type": "ProgContainerLit", "kind": "list", "items": items}


def rs_index(w, nid, row):
    parts = w.named_children(nid)
    if len(parts) != 2:
        return w.block("index_form")
    return {"type": "ProgSubscript", "obj": _expr(w, w.emit(parts[0])),
            "index": _expr(w, w.emit(parts[1]))}


def rs_range(w, nid, row):
    return _range_call(w, nid)


def rs_fn_item(w, nid, row):
    body = w.field_child(nid, "body")
    if body is None:
        return w.block("fn_without_body")
    stmts, tail = _block_parts(w, body)
    if tail is not None:
        if tail.get("type") in _STMT_TYPES:
            # a unit-valued tail (a valueless trailing if/loop) — nothing
            # to return; it runs as the last statement.
            stmts.append(tail)
        else:
            stmts.append({"type": "ProgReturn", "value": tail})
    return {"type": "ProgSeq", "stmts": stmts}


HANDLERS = {
    "rs_unwrap_first": rs_unwrap_first,
    "rs_unwrap_paren": rs_unwrap_paren,
    "rs_unary": rs_unary,
    "rs_let": rs_let,
    "rs_assign": rs_assign,
    "rs_compound_assign": rs_compound_assign,
    "rs_if": rs_if,
    "rs_while": rs_while,
    "rs_loop": rs_loop,
    "rs_for": rs_for,
    "rs_break": rs_break,
    "rs_continue": rs_continue,
    "rs_return": rs_return,
    "rs_call": rs_call,
    "rs_macro": rs_macro,
    "rs_array": rs_array,
    "rs_index": rs_index,
    "rs_range": rs_range,
    "rs_fn_item": rs_fn_item,
}

_ROWS: Optional[List[Dict[str, Any]]] = None


def _rows() -> List[Dict[str, Any]]:
    """The correspondence table, loaded once from the seed file (a
    performance cache — the seed is the source of truth)."""
    global _ROWS
    if _ROWS is None:
        _ROWS = ts_ingest.load_correspondence_rows("rust")
    return _ROWS


def _read_params(w, fn_nid) -> List[Dict[str, str]]:
    """Param names + type ANNOTATIONS (recorded in the read-out record —
    the IR itself is untyped at P2, doc §2)."""
    params: List[Dict[str, str]] = []
    pnode = w.field_child(fn_nid, "parameters")
    if pnode is None:
        return params
    for c in w.named_children(pnode):
        k = w.kind(c)
        if k != "parameter":
            w.block(f"param_kind:{k}")
            continue
        pat = w.field_child(c, "pattern")
        if pat is None or w.kind(pat) != "identifier":
            w.block(f"param_pattern:{w.kind(pat) if pat is not None else 'missing'}")
            continue
        ty = w.field_child(c, "type")
        params.append({"name": w.text(pat),
                       "ty": w.flat_text(ty) if ty is not None else ""})
    return params


def read_fn_node(substrate, fn_nid) -> Dict[str, Any]:
    """Fold ONE ingested function_item CstNode into hub IR by applying the
    seed correspondence table. {name, params, ok, ir, blockers}."""
    w = ts_ingest.TableWalker(substrate, _rows(), HANDLERS)
    name_child = w.field_child(fn_nid, "name")
    name = w.text(name_child) if name_child is not None else ""
    params = _read_params(w, fn_nid)
    ir = w.emit(fn_nid)
    blockers = sorted(set(w.blockers))
    return {"language": "rust", "name": name, "params": params,
            "ok": not blockers, "ir": ir if not blockers else None,
            "blockers": blockers}


def read_source(substrate, source: str) -> Dict[str, Any]:
    """Parse + ingest a rust source (mechanical) and fold every
    function_item into hub IR. {language, root, functions: [...]}."""
    rec = ts_ingest.ingest_source(substrate, source, "rust")
    fns = ts_ingest.find_kind(substrate, rec["root"], "function_item")
    return {"language": "rust", "root": rec["root"],
            "n_cst_nodes": rec["n_nodes"],
            "functions": [read_fn_node(substrate, f) for f in fns]}


def read_function(substrate, source: str, name: str | None = None) -> Dict[str, Any]:
    """The single-function convenience read: first (or named) function."""
    out = read_source(substrate, source)
    fns = out["functions"]
    if name is not None:
        fns = [f for f in fns if f["name"] == name]
    if not fns:
        return {"language": "rust", "name": name or "", "params": [],
                "ok": False, "ir": None, "blockers": ["no_function_item"]}
    return fns[0]


__all__ = ["read_source", "read_function", "read_fn_node", "HANDLERS"]
