"""prog_ir_lua — the LUA frame's CST → hub Program-IR reader (P2).

The lua half of PROGRAM_SYNTHESIS_PLAN.md §4-P2, structured exactly like
`domains/prog_ir_rust.py`: tree-sitter CST dump (`domains/ts_ingest`) →
table-driven fold into the hub Program IR, with the correspondence shipped
as seed data (`seeds/lua_correspondence.json`) and this module contributing
only the registered mechanical shape handlers + the read-out. Cross-frame
maps that live in the TABLE (documented there and in
PROGRAM_SYNTHESIS_P2_RUST_LUA.md):

  · 1-based → 0-based: `t[i]` reads/writes as ProgSubscript/SubscriptSet
    with index `i - 1` (array-part reading only; a string-literal key is
    the map-part blocker).
  · numeric for `a, b[, literal step]` → ForEach over the declared `range`
    oracle with the INCLUSIVE stop shifted by the step's sign.
  · generic for `k, v in ipairs(xs)` → a counter + ForEach desugar
    (k is 1-based, exactly lua's).
  · `repeat B until C` → `B; while not C { B }` (body emitted twice; a
    body containing `break` is a blocker — the duplicated first pass
    would strand the break outside the loop).
  · `..` → ProgFString(left, right) — py_str spellings agree with lua
    tostring for ints/strings; ledger records the float-spelling caveat.
  · `#x` → the declared `len` oracle.

Honest residuals: varargs, multiple assignment/return values, keyed table
fields, pairs()/custom iterators, metatables, coroutines, method
definitions … block the read → {ok: False, blockers: [...]}, never a
silent partial emit.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from domains import ts_ingest

_L = lambda v: {"type": "Lit", "value": v}  # noqa: E731

_STMT_TYPES = frozenset({
    "ProgSeq", "ProgAssignVar", "ProgAugAssign", "ProgIfStmt", "ProgForEach",
    "ProgWhile", "ProgLoopCtl", "ProgReturn", "ProgTryOr", "ProgRaise",
    "ProgImportStmt", "ProgSubscriptSet", "ProgAttrSet", "ProgTupleUnpack",
    "ProgDefFnParam",
})


def _expr(w, ir: Dict[str, Any]) -> Dict[str, Any]:
    if ir.get("type") in _STMT_TYPES:
        return w.block(f"statement_in_value_position:{ir.get('type')}")
    return ir


def _stmt_of(stmts: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(stmts) == 1:
        return stmts[0]
    return {"type": "ProgSeq", "stmts": stmts}


def _stmts(w, block) -> List[Dict[str, Any]]:
    """A lua block's statements (no tail-expression concept in lua)."""
    if block is None:
        return []
    out = []
    for c in w.named_children(block):
        if w.kind(c) == "comment":
            continue
        out.append(w.emit(c))
    return out


def _shift_index(w, index_ir: Dict[str, Any]) -> Dict[str, Any]:
    """The 1-based → 0-based cross-frame shift: hub index = lua index - 1."""
    return {"type": "Minus", "a": index_ir, "b": _L(1)}


# ---------------------------------------------------------------------------
# Handlers.
# ---------------------------------------------------------------------------
def lua_unwrap_paren(w, nid, row):
    named = w.named_children(nid)
    if len(named) != 1:
        return w.block("paren_form")
    return w.emit(named[0])


def lua_unary(w, nid, row):
    op_child = w.field_child(nid, "operator")
    operand = w.field_child(nid, "operand")
    if op_child is None or operand is None:
        return w.block("unary_form")
    op = w.text(op_child)
    arg = _expr(w, w.emit(operand))
    if op == "-":
        return {"type": "Neg", "arg": arg}
    if op == "not":
        return {"type": "Not", "arg": arg}
    if op == "#":
        return {"type": "ProgCallExtern", "name": "len", "recv": None,
                "args": [arg]}
    return w.block(f"unary_operator:{op}")


def lua_concat(w, nid, row):
    left = _expr(w, w.emit_field(nid, "left"))
    right = _expr(w, w.emit_field(nid, "right"))
    return {"type": "ProgFString", "parts": [left, right]}


def lua_function(w, nid, row):
    body = w.field_child(nid, "body")
    return _stmt_of(_stmts(w, body) or
                    [{"type": "ProgReturn", "value": None}])


def lua_local(w, nid, row):
    inner = [c for c in w.named_children(nid)
             if w.kind(c) == "assignment_statement"]
    if len(inner) != 1:
        return w.block("local_uninitialized")
    return w.emit(inner[0])


def lua_assign(w, nid, row):
    targets_node = next((c for c in w.named_children(nid)
                         if w.kind(c) == "variable_list"), None)
    values_node = next((c for c in w.named_children(nid)
                        if w.kind(c) == "expression_list"), None)
    if targets_node is None or values_node is None:
        return w.block("assign_form")
    targets = w.named_children(targets_node)
    values = w.named_children(values_node)
    if len(targets) != 1 or len(values) != 1:
        return w.block("multiple_assignment")
    value = _expr(w, w.emit(values[0]))
    tgt = targets[0]
    if w.kind(tgt) == "identifier":
        return {"type": "ProgAssignVar", "name": w.text(tgt), "value": value}
    if w.kind(tgt) == "bracket_index_expression":
        idx = w.field_child(tgt, "field")
        if idx is not None and w.kind(idx) == "string":
            return w.block("table_string_key")
        return {"type": "ProgSubscriptSet",
                "obj": _expr(w, w.emit_field(tgt, "table")),
                "index": _shift_index(w, _expr(w, w.emit_field(tgt, "field"))),
                "value": value}
    return w.block(f"assign_target:{w.kind(tgt)}")


def lua_if(w, nid, row):
    cond = _expr(w, w.emit_field(nid, "condition"))
    then_ir = _stmt_of(_stmts(w, w.field_child(nid, "consequence")) or
                       [{"type": "ProgSeq", "stmts": []}])
    orelse = None
    for alt in reversed(w.field_children(nid, "alternative")):
        k = w.kind(alt)
        if k == "else_statement":
            orelse = _stmt_of(_stmts(w, w.field_child(alt, "body")) or
                              [{"type": "ProgSeq", "stmts": []}])
        elif k == "elseif_statement":
            ec = _expr(w, w.emit_field(alt, "condition"))
            et = _stmt_of(_stmts(w, w.field_child(alt, "consequence")) or
                          [{"type": "ProgSeq", "stmts": []}])
            orelse = {"type": "ProgIfStmt", "cond": ec, "then": et,
                      "orelse": orelse}
        else:
            return w.block(f"if_alternative:{k}")
    return {"type": "ProgIfStmt", "cond": cond, "then": then_ir,
            "orelse": orelse}


def lua_while(w, nid, row):
    return {"type": "ProgWhile",
            "cond": _expr(w, w.emit_field(nid, "condition")),
            "body": _stmt_of(_stmts(w, w.field_child(nid, "body")) or
                             [{"type": "ProgSeq", "stmts": []}]),
            "orelse": None}


def lua_repeat(w, nid, row):
    body = w.field_child(nid, "body")
    if body is not None and w.has_descendant_kind(body, "break_statement"):
        return w.block("repeat_with_break")
    first = _stmts(w, body)
    again = _stmts(w, body)
    cond = _expr(w, w.emit_field(nid, "condition"))
    loop = {"type": "ProgWhile", "cond": {"type": "Not", "arg": cond},
            "body": _stmt_of(again or [{"type": "ProgSeq", "stmts": []}]),
            "orelse": None}
    return {"type": "ProgSeq", "stmts": [*first, loop]}


def _range_args(w, clause) -> Optional[List[Dict[str, Any]]]:
    start = _expr(w, w.emit_field(clause, "start"))
    stop = _expr(w, w.emit_field(clause, "end"))
    step_child = w.field_child(clause, "step")
    if step_child is None:
        return [start, {"type": "Plus", "items": [stop, _L(1)]}]
    # the inclusive→exclusive stop shift needs the step's SIGN, so only a
    # literal (possibly negated) number step is in honest scope.
    sign = 1
    node = step_child
    if w.kind(node) == "unary_expression":
        opc = w.field_child(node, "operator")
        if opc is None or w.text(opc) != "-":
            w.block("for_step_nonliteral")
            return None
        sign = -1
        node = w.field_child(node, "operand")
    if node is None or w.kind(node) != "number":
        w.block("for_step_nonliteral")
        return None
    step_ir = _expr(w, w.emit(node))
    if sign < 0:
        step_ir = {"type": "Neg", "arg": step_ir}
        stop = {"type": "Minus", "a": stop, "b": _L(1)}
    else:
        stop = {"type": "Plus", "items": [stop, _L(1)]}
    return [start, stop, step_ir]


def lua_for(w, nid, row):
    clause = w.field_child(nid, "clause")
    body_stmts = _stmts(w, w.field_child(nid, "body"))
    if clause is None:
        return w.block("for_form")
    if w.kind(clause) == "for_numeric_clause":
        name_child = w.field_child(clause, "name")
        args = _range_args(w, clause)
        if args is None:
            return _L(None)  # blocker already recorded
        return {"type": "ProgForEach", "var": w.text(name_child),
                "iter": {"type": "ProgCallExtern", "name": "range",
                         "recv": None, "args": args},
                "body": _stmt_of(body_stmts or [{"type": "ProgSeq", "stmts": []}]),
                "orelse": None}
    if w.kind(clause) == "for_generic_clause":
        names_node = next((c for c in w.named_children(clause)
                           if w.kind(c) == "variable_list"), None)
        exprs_node = next((c for c in w.named_children(clause)
                           if w.kind(c) == "expression_list"), None)
        names = w.named_children(names_node) if names_node is not None else []
        exprs = w.named_children(exprs_node) if exprs_node is not None else []
        if (len(names) != 2 or len(exprs) != 1
                or any(w.kind(n) != "identifier" for n in names)):
            return w.block("generic_for_shape")
        call = exprs[0]
        fn_name = w.field_child(call, "name") if w.kind(call) == "function_call" else None
        if fn_name is None or w.kind(fn_name) != "identifier" \
                or w.text(fn_name) != "ipairs":
            return w.block("generic_for_non_ipairs")
        args_node = w.field_child(call, "arguments")
        args = w.named_children(args_node) if args_node is not None else []
        if len(args) != 1:
            return w.block("ipairs_arity")
        k_name, v_name = w.text(names[0]), w.text(names[1])
        # counter + ForEach desugar: k counts 1-based exactly as ipairs.
        inner = {"type": "ProgSeq", "stmts": [
            {"type": "ProgAugAssign", "name": k_name, "op": "add",
             "value": _L(1)},
            *body_stmts]}
        return {"type": "ProgSeq", "stmts": [
            {"type": "ProgAssignVar", "name": k_name, "value": _L(0)},
            {"type": "ProgForEach", "var": v_name,
             "iter": _expr(w, w.emit(args[0])), "body": inner,
             "orelse": None}]}
    return w.block(f"for_clause:{w.kind(clause)}")


def lua_return(w, nid, row):
    exp_list = next((c for c in w.named_children(nid)
                     if w.kind(c) == "expression_list"), None)
    if exp_list is None:
        return {"type": "ProgReturn", "value": None}
    values = w.named_children(exp_list)
    if len(values) > 1:
        return w.block("multiple_return_values")
    if not values:
        return {"type": "ProgReturn", "value": None}
    return {"type": "ProgReturn", "value": _expr(w, w.emit(values[0]))}


def lua_break(w, nid, row):
    return {"type": "ProgLoopCtl", "kind": "break"}


def lua_call(w, nid, row):
    fn = w.field_child(nid, "name")
    args_node = w.field_child(nid, "arguments")
    args = [_expr(w, w.emit(c)) for c in w.named_children(args_node)] \
        if args_node is not None else []
    if fn is None:
        return w.block("call_form")
    k = w.kind(fn)
    if k == "identifier":
        return {"type": "ProgCallExtern", "name": w.text(fn), "recv": None,
                "args": args}
    if k == "dot_index_expression":
        # a.b(x) — the dotted lua name verbatim (math.floor, string.rep …).
        return {"type": "ProgCallExtern", "name": w.flat_text(fn),
                "recv": None, "args": args}
    if k == "method_index_expression":
        recv = _expr(w, w.emit_field(fn, "table"))
        method = w.field_child(fn, "method")
        return {"type": "ProgCallExtern", "name": w.text(method),
                "recv": recv, "args": args}
    return w.block(f"call_function:{k}")


def lua_index(w, nid, row):
    idx = w.field_child(nid, "field")
    if idx is not None and w.kind(idx) == "string":
        return w.block("table_string_key")
    return {"type": "ProgSubscript",
            "obj": _expr(w, w.emit_field(nid, "table")),
            "index": _shift_index(w, _expr(w, w.emit_field(nid, "field")))}


def lua_table(w, nid, row):
    items = []
    for f in w.named_children(nid):
        if w.kind(f) != "field":
            continue
        if w.field_child(f, "name") is not None or len(w.named_children(f)) != 1:
            return w.block("table_map_part")
        value = w.field_child(f, "value") or w.named_children(f)[0]
        items.append(_expr(w, w.emit(value)))
    return {"type": "ProgContainerLit", "kind": "list", "items": items}


HANDLERS = {
    "lua_unwrap_paren": lua_unwrap_paren,
    "lua_unary": lua_unary,
    "lua_concat": lua_concat,
    "lua_function": lua_function,
    "lua_local": lua_local,
    "lua_assign": lua_assign,
    "lua_if": lua_if,
    "lua_while": lua_while,
    "lua_repeat": lua_repeat,
    "lua_for": lua_for,
    "lua_return": lua_return,
    "lua_break": lua_break,
    "lua_call": lua_call,
    "lua_index": lua_index,
    "lua_table": lua_table,
}

_ROWS: Optional[List[Dict[str, Any]]] = None


def _rows() -> List[Dict[str, Any]]:
    global _ROWS
    if _ROWS is None:
        _ROWS = ts_ingest.load_correspondence_rows("lua")
    return _ROWS


def _read_params(w, fn_nid) -> List[Dict[str, str]]:
    params: List[Dict[str, str]] = []
    pnode = w.field_child(fn_nid, "parameters")
    if pnode is None:
        return params
    for c in w.named_children(pnode):
        if w.kind(c) != "identifier":
            w.block("varargs" if w.kind(c) == "vararg_expression"
                    else f"param_kind:{w.kind(c)}")
            continue
        params.append({"name": w.text(c), "ty": ""})
    return params


def read_fn_node(substrate, fn_nid) -> Dict[str, Any]:
    """Fold ONE ingested function_declaration CstNode into hub IR."""
    w = ts_ingest.TableWalker(substrate, _rows(), HANDLERS)
    name_child = w.field_child(fn_nid, "name")
    if name_child is not None and w.kind(name_child) == "identifier":
        name = w.text(name_child)
    elif name_child is not None:
        name = w.flat_text(name_child)
        w.block(f"function_name:{w.kind(name_child)}")
    else:
        name = ""
    params = _read_params(w, fn_nid)
    ir = w.emit(fn_nid)
    blockers = sorted(set(w.blockers))
    return {"language": "lua", "name": name, "params": params,
            "ok": not blockers, "ir": ir if not blockers else None,
            "blockers": blockers}


def read_source(substrate, source: str) -> Dict[str, Any]:
    """Parse + ingest a lua source (mechanical) and fold every
    function_declaration into hub IR."""
    rec = ts_ingest.ingest_source(substrate, source, "lua")
    fns = ts_ingest.find_kind(substrate, rec["root"], "function_declaration")
    return {"language": "lua", "root": rec["root"],
            "n_cst_nodes": rec["n_nodes"],
            "functions": [read_fn_node(substrate, f) for f in fns]}


def read_function(substrate, source: str, name: str | None = None) -> Dict[str, Any]:
    out = read_source(substrate, source)
    fns = out["functions"]
    if name is not None:
        fns = [f for f in fns if f["name"] == name]
    if not fns:
        return {"language": "lua", "name": name or "", "params": [],
                "ok": False, "ir": None, "blockers": ["no_function_declaration"]}
    return fns[0]


__all__ = ["read_source", "read_function", "read_fn_node", "HANDLERS"]
