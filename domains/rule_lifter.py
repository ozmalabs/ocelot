"""rule_lifter — mechanically LIFT a recognizable class of agent-logic Python
(decision-over-graph-state functions) into graph-resident RULES (Term-trees
the Rust engine runs), NOT Rust code.

Per CLAUDE.md: "any if/else that reads graph state and decides what to do is a
Rule, not Python." A lifted Rule is graph DATA, so it goes LIVE with NO maturin
rebuild — the engine already runs Rules (`add_rule` / `apply_rule_once`). This
is the architecturally-correct destination for the decision-logic subset of the
`requires_replacement` units the impl-substrate self-model flags.

NO LLM anywhere. Pure `ast` recognition + mechanical `substrate_rs` Term
emission, mirroring `rust_rewrite_world.install_requires_replacement_rule` /
`meta_monitor.install_meta_issue_rule`.

## The recognized subset (RESTRICTED, well-defined)

A single function of exactly this shape:

    def f(substrate, ...):
        for <var> in substrate.nodes("<TYPE>"):
            if <CONDITION over substrate.node(<var>)["attrs"].get("<key>")>:
                substrate.set_attr(<var>, "<key>", <literal>)   # set_attr effect
                # and/or substrate.add_edge(<var>, "<etype>", <var>)  # self-edge

  * One top-level `for` over `substrate.nodes("<TYPE>")` (a string literal type).
  * One `if` whose test is a CONDITION tree over `substrate.node(<var>)["attrs"]
    .get("<key>")` reads, compared (>,<,>=,<=,==,!=) to LITERALS, combined by
    `and` / `or` / `not`.
  * A body of one-or-more EFFECTS, each either
      - `substrate.set_attr(<var>, "<key-literal>", <literal>)`, or
      - `substrate.add_edge(<var>, "<etype-literal>", <var>)`  (self-edge only).
  * NOTHING ELSE. Nested loops, function calls in the body other than the two
    effects, non-attr tests, dynamic (non-literal) keys/types, `else` branches,
    assignments, comprehensions, or any other statement -> recognize returns
    None. CONSERVATIVE: a near-miss is None, never a wrong Rule.

## The lift

The emitter mirrors the working template: it builds the where-CONDITION as a
`substrate_rs` Term (Attr(var,key) under Gt/Lt/Gte/Lte/Eq + And/Or/Not), opens a
`has_<TYPE>` production + wires every node of `<TYPE>` under a `RuleLiftRoot` so
the matched node is reachable by an edge (the engine's `match` is always an
edge triple `[src,edge,tgt]`, exactly like `has_unit`), then installs the Rule
with set_attr / self-add_edge effects. Firing `apply_rule_once` over the matched
edges reproduces the Python function's graph mutations — LIVE, no rebuild.
"""
from __future__ import annotations

import ast
from typing import Any

from substrate_rs import (Attr, Var, Lit, Gt, Lt, Gte, Lte, Eq, And, Or, Not)


# Comparator AST node -> Term constructor (==, != handled specially: != = Not(Eq)).
_CMP_TERM = {
    ast.Gt: Gt,
    ast.Lt: Lt,
    ast.GtE: Gte,
    ast.LtE: Lte,
    ast.Eq: Eq,
}
_CMP_SYM = {
    ast.Gt: ">", ast.Lt: "<", ast.GtE: ">=", ast.LtE: "<=",
    ast.Eq: "==", ast.NotEq: "!=",
}


def _native(substrate):
    return substrate._inner if hasattr(substrate, "_inner") else substrate


# --------------------------------------------------------------------------- recognizer

# The receiver attrs that, on a method, count as "the substrate handle" — i.e.
# `self.<attr>` where <attr> in this set is treated exactly like a bare
# `substrate` name in the function form. A method must use ONE of these
# consistently; a mixed handle or `self.<other>` state in test/effect -> reject.
_SELF_HANDLE_ATTRS = frozenset({"s", "substrate", "graph", "g"})


class _NotInSubset(Exception):
    """Raised the instant anything outside the recognized subset appears.
    Carries the reason. Recognition catches it and returns None — never a Rule."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _handle_matches(node: ast.AST, handle: str | None) -> bool:
    """True if `node` is the substrate handle expression. `handle` is either
    None (the bare `substrate` Name — function form) or a `self.<attr>` accessor
    name in `_SELF_HANDLE_ATTRS` (method form). Conservative: ONLY the exact
    declared handle matches; any other Name / `self.<other>` -> False."""
    if handle is None:
        return isinstance(node, ast.Name) and node.id == "substrate"
    # method form: node must be `self.<handle>`
    return (isinstance(node, ast.Attribute)
            and node.attr == handle
            and isinstance(node.value, ast.Name)
            and node.value.id == "self")


def _const_value(node: ast.AST) -> Any:
    """A literal Python constant (str / number / bool / None), else reject."""
    if isinstance(node, ast.Constant):
        return node.value
    # `-0.3` etc. parse as UnaryOp(USub, Constant) — accept numeric negation.
    if (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)
            and isinstance(node.operand, ast.Constant)
            and isinstance(node.operand.value, (int, float))
            and not isinstance(node.operand.value, bool)):
        return -node.operand.value
    raise _NotInSubset("effect/comparison value is not a literal constant")


def _is_attr_get(node: ast.AST, loop_var: str, handle: str | None) -> str | None:
    """Recognize exactly `<HANDLE>.node(<loop_var>)["attrs"].get("<key>")` and
    return the literal key, else None. `<HANDLE>` is `substrate` (function form)
    or `self.<attr>` (method form, per `handle`). Conservative: any deviation
    -> None."""
    # Outer: <...>.get("key")  (zero-or-one positional default ignored only if
    # it is a literal; a non-literal default is rejected as outside-subset).
    if not (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"):
        return None
    if node.keywords:
        return None
    if not node.args or not isinstance(node.args[0], ast.Constant) \
            or not isinstance(node.args[0].value, str):
        return None
    key = node.args[0].value
    if len(node.args) >= 2:
        # default arg present — only a literal default is in-subset (it is not
        # represented in the Term, but a non-literal would smuggle in logic).
        _const_value(node.args[1])
    # Middle: <...>["attrs"]
    sub = node.func.value
    if not (isinstance(sub, ast.Subscript)
            and isinstance(sub.slice, ast.Constant)
            and sub.slice.value == "attrs"):
        return None
    # Inner: <HANDLE>.node(<loop_var>)
    call = sub.value
    if not (isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "node"
            and _handle_matches(call.func.value, handle)):
        return None
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Name) \
            or call.args[0].id != loop_var:
        return None
    return key


def _build_condition(test: ast.AST, loop_var: str,
                     handle: str | None) -> tuple[Any, dict]:
    """Recurse the if-test into a (Term, structured-dict) pair. Only attr-get
    comparisons against literals, combined by and/or/not, are admitted. Anything
    else raises _NotInSubset."""
    if isinstance(test, ast.BoolOp):
        ctor = And if isinstance(test.op, ast.And) else Or
        terms, structs = [], []
        for v in test.values:
            t, st = _build_condition(v, loop_var, handle)
            terms.append(t)
            structs.append(st)
        op = "and" if isinstance(test.op, ast.And) else "or"
        return ctor(items=tuple(terms)), {"op": op, "args": structs}

    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        t, st = _build_condition(test.operand, loop_var, handle)
        return Not(t), {"op": "not", "args": [st]}

    if isinstance(test, ast.Compare):
        if len(test.ops) != 1 or len(test.comparators) != 1:
            raise _NotInSubset("chained comparison (a < b < c) not in subset")
        op = type(test.ops[0])
        key = _is_attr_get(test.left, loop_var, handle)
        if key is None:
            raise _NotInSubset(
                "comparison left side is not substrate.node(var)['attrs'].get('k')")
        val = _const_value(test.comparators[0])
        struct = {"op": "cmp", "key": key, "cmp": _CMP_SYM[op], "value": val}
        if op is ast.NotEq:
            return Not(Eq(a=Attr(Var("N"), key), b=Lit(val))), struct
        if op not in _CMP_TERM:
            raise _NotInSubset(f"comparator {op.__name__} not in subset")
        term = _CMP_TERM[op](a=Attr(Var("N"), key), b=Lit(val))
        return term, struct

    raise _NotInSubset("condition is not a comparison / and / or / not over attrs")


def _recognize_effect(stmt: ast.AST, loop_var: str, handle: str | None) -> dict:
    """One body statement -> a structured effect dict (set_attr or self add_edge),
    else raise. Bodies are restricted to these two substrate mutations, invoked
    on the declared HANDLE (`substrate` or `self.<attr>`)."""
    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)):
        raise _NotInSubset("body statement is not a substrate mutation call")
    call = stmt.value
    func = call.func
    if not (isinstance(func, ast.Attribute)
            and _handle_matches(func.value, handle)):
        raise _NotInSubset("body call is not on the substrate handle")

    if func.attr == "set_attr":
        if call.keywords or len(call.args) != 3:
            raise _NotInSubset("set_attr arity not (var, key, value)")
        if not (isinstance(call.args[0], ast.Name)
                and call.args[0].id == loop_var):
            raise _NotInSubset("set_attr target is not the loop variable")
        if not (isinstance(call.args[1], ast.Constant)
                and isinstance(call.args[1].value, str)):
            raise _NotInSubset("set_attr key is not a string literal")
        value = _const_value(call.args[2])
        return {"kind": "set_attr", "key": call.args[1].value, "value": value}

    if func.attr == "add_edge":
        # Self-edge only: add_edge(var, "etype", var). The engine's AddEdge
        # binds src_var + tgt_var from the match; a free target would not be
        # bound, so we conservatively admit only the matched node as target.
        if call.keywords or len(call.args) not in (3, 4):
            raise _NotInSubset("add_edge arity not (src, etype, tgt[, attrs])")
        if not (isinstance(call.args[0], ast.Name)
                and call.args[0].id == loop_var):
            raise _NotInSubset("add_edge source is not the loop variable")
        if not (isinstance(call.args[1], ast.Constant)
                and isinstance(call.args[1].value, str)):
            raise _NotInSubset("add_edge type is not a string literal")
        if not (isinstance(call.args[2], ast.Name)
                and call.args[2].id == loop_var):
            raise _NotInSubset(
                "add_edge target is not the loop variable (only self-edges in subset)")
        if len(call.args) == 4:
            raise _NotInSubset("add_edge with attrs dict not in subset")
        return {"kind": "add_edge", "edge_type": call.args[1].value}

    raise _NotInSubset(f"substrate.{func.attr}(...) not a liftable effect")


def _is_trivial_noop(stmt: ast.AST) -> bool:
    """A top-level statement that carries no graph effect and no logic, so it
    may sit between recognizable blocks without disqualifying the function:
    a docstring / bare string / number / Ellipsis Expr, or a bare `pass`.
    ANYTHING with a payload (a call, return-with-logic, assignment, mutation)
    is NOT trivial — those route to the all-or-nothing reject."""
    if isinstance(stmt, ast.Pass):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
        return True
    return False


def _detect_handle(func: ast.FunctionDef) -> tuple[str | None, bool]:
    """Determine the substrate handle from the signature.

    Returns (handle, is_method):
      * function form  `def f(substrate, ...)` -> (None, False)
        — the handle is the bare `substrate` Name.
      * method form    `def m(self, ...)`      -> ('<attr>', True)
        — the handle is `self.<attr>`, with <attr> DISCOVERED below from the
        graph calls (it must be one consistent attr in _SELF_HANDLE_ATTRS).
        Here we return ('', True) as a sentinel; the caller resolves the
        concrete attr while recognizing blocks (and rejects on a mismatch).
    Raises _NotInSubset if the signature is neither form."""
    args = func.args
    if not args.args:
        raise _NotInSubset("function takes no parameters")
    first = args.args[0].arg
    if first == "substrate":
        return None, False
    if first == "self":
        return "", True          # concrete attr resolved during block walk
    raise _NotInSubset("first parameter is not `substrate` or `self`")


def _resolve_self_handle(func: ast.FunctionDef) -> str:
    """For a method (first param `self`), find the ONE `self.<attr>` accessor
    (attr in _SELF_HANDLE_ATTRS) used as the substrate handle across all graph
    calls (`self.<attr>.nodes/.node/.set_attr/.add_edge`). A method using more
    than one such handle, or none, is rejected. (Other `self.<x>` references in
    the test/effect are caught later by `_handle_matches` returning False.)"""
    found: set[str] = set()
    for sub in ast.walk(func):
        if (isinstance(sub, ast.Attribute)
                and isinstance(sub.value, ast.Attribute)
                and isinstance(sub.value.value, ast.Name)
                and sub.value.value.id == "self"
                and sub.value.attr in _SELF_HANDLE_ATTRS
                and sub.attr in ("nodes", "node", "set_attr", "add_edge")):
            found.add(sub.value.attr)
    if not found:
        raise _NotInSubset(
            "method has no self.<s|substrate|graph|g> substrate handle")
    if len(found) > 1:
        raise _NotInSubset(
            f"method mixes substrate handles {sorted(found)} (not in subset)")
    return next(iter(found))


def _recognize_block(loop: ast.For, handle: str | None) -> dict:
    """Recognize ONE guarded-for block:
        for <var> in <HANDLE>.nodes("<TYPE>"):
            if <CONDITION>:
                <EFFECTS>
    Returns the structured block dict, or raises _NotInSubset. <HANDLE> is the
    bare `substrate` Name (handle=None) or `self.<handle>` (method form)."""
    if loop.orelse:
        raise _NotInSubset("for/else not in subset")
    if not isinstance(loop.target, ast.Name):
        raise _NotInSubset("loop target is not a single name")
    loop_var = loop.target.id

    it = loop.iter
    if not (isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute)
            and it.func.attr == "nodes"
            and _handle_matches(it.func.value, handle)):
        raise _NotInSubset("loop iterable is not <handle>.nodes(...)")
    if len(it.args) != 1 or not isinstance(it.args[0], ast.Constant) \
            or not isinstance(it.args[0].value, str):
        raise _NotInSubset("nodes() type is not a string literal")
    node_type = it.args[0].value

    if len(loop.body) != 1 or not isinstance(loop.body[0], ast.If):
        raise _NotInSubset("loop body is not a single `if`")
    iff = loop.body[0]
    if iff.orelse:
        raise _NotInSubset("`if` has an else branch (not in subset)")

    cond_term, cond_struct = _build_condition(iff.test, loop_var, handle)
    if not iff.body:
        raise _NotInSubset("`if` body is empty")
    effects = [_recognize_effect(s, loop_var, handle) for s in iff.body]

    return {
        "node_type": node_type,
        "var": loop_var,
        "condition": cond_struct,
        "_condition_term": cond_term,   # prebuilt Term (Var('N') basis)
        "effects": effects,
    }


def recognize_rule_shape(py_source: str, func_name: str) -> dict | None:
    """Recognize the RESTRICTED decision-over-graph-state pattern in the function
    `func_name` within `py_source`. Returns a structured dict
    {node_type, var, condition, effects, blocks, ...} on a match, or None for
    anything outside the subset.

    CONSERVATIVE by construction: any deviation -> None, never a wrong Rule."""
    ok, recognized, _reason = recognize_with_reason(py_source, func_name)
    return recognized if ok else None


def recognize_with_reason(py_source: str, func_name: str) -> tuple[bool, dict | None, str]:
    """Recognize `func_name` as one-or-more rule-shape blocks. Returns
    (ok, recognized, reason); reason is "" on success.

    Accepts BOTH forms:
      * `def f(substrate, ...)`  — function, handle is the `substrate` Name.
      * `def m(self, ...)`       — method, handle is `self.<attr>` for ONE attr
        in {s, substrate, graph, g}, used consistently.

    The body is a SEQUENCE of independent guarded-for blocks (each a
    `for ... in <handle>.nodes("T"): if <cond>: <effects>`), interleaved only
    with trivial no-ops (docstring / pass). ALL-OR-NOTHING: if ANY top-level
    statement is not a recognizable block or a trivial no-op (a call, a return
    with logic, a non-guarded mutation, an assignment to state), the WHOLE
    function is rejected — never partially lifted.

    On success `recognized` carries `blocks` (one structured dict per for-block,
    in source order) PLUS top-level mirror keys (node_type/var/condition/effects)
    from the FIRST block, for back-compat with single-block callers."""
    try:
        tree = ast.parse(py_source)
    except SyntaxError as e:
        return False, None, f"source does not parse: {e}"

    func = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name == func_name:
            func = node
            break
    if func is None:
        return False, None, f"function {func_name!r} not found"
    if isinstance(func, ast.AsyncFunctionDef):
        return False, None, "async function not in subset"

    try:
        handle, is_method = _detect_handle(func)
        if is_method:
            # Resolve the ONE concrete self.<attr> handle (rejects mixed/none).
            handle = _resolve_self_handle(func)

        blocks: list[dict] = []
        for stmt in func.body:
            if _is_trivial_noop(stmt):
                continue
            if isinstance(stmt, ast.For):
                blocks.append(_recognize_block(stmt, handle))
                continue
            # Anything else at top level -> reject the WHOLE function.
            raise _NotInSubset(
                "body has a top-level statement that is not a guarded `for` "
                "block (multi-statement all-or-nothing: function rejected)")
        if not blocks:
            raise _NotInSubset("body has no recognizable for-block")
    except _NotInSubset as e:
        return False, None, e.reason

    first = blocks[0]
    return True, {
        "func_name": func_name,
        "handle": handle,            # None (function form) or self.<attr>
        "blocks": blocks,
        # back-compat mirror of the first block:
        "node_type": first["node_type"],
        "var": first["var"],
        "condition": first["condition"],
        "_condition_term": first["_condition_term"],
        "effects": first["effects"],
    }, ""


# --------------------------------------------------------------------------- emitter


def _root(substrate) -> int:
    for n in substrate.nodes("RuleLiftRoot"):
        return n
    return substrate.add_node("RuleLiftRoot", {"origin": "rule_lifter"})


def _wire_type_under_root(substrate, node_type: str) -> str:
    """Open a `has_<TYPE>` production + wire every node of `node_type` under the
    RuleLiftRoot via that edge, so the lifted Rule can match the node through an
    edge triple (the engine's only match form). Idempotent. Returns the edge
    type. This is mechanical graph translation (the `has_unit` pattern), no
    decision."""
    edge_type = f"has_{node_type}"
    try:
        substrate.add_production({
            "src": {"type": "RuleLiftRoot", "var": "a"},
            "edge_type": edge_type,
            "tgt": {"type": node_type, "var": "b"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": f"rule_lifter:{edge_type}",
        })
    except Exception:
        pass
    root = _root(substrate)
    existing = set(substrate.neighbours(root, edge_type))
    for n in substrate.nodes(node_type):
        if n not in existing:
            try:
                substrate.add_edge(root, edge_type, n)
            except Exception:
                pass
    return edge_type


def _condition_term_for_var(cond_struct: dict, var_name: str):
    """Rebuild a condition Term with the match variable name (the engine binds
    the matched node to the match's target var). Recognition built it on
    Var('N'); rebuild on `var_name` so the where references the bound node."""
    def build(struct):
        op = struct["op"]
        if op == "cmp":
            key, val = struct["key"], struct["value"]
            cmp = struct["cmp"]
            base = Attr(Var(var_name), key)
            if cmp == "!=":
                return Not(Eq(a=base, b=Lit(val)))
            ctor = {">": Gt, "<": Lt, ">=": Gte, "<=": Lte, "==": Eq}[cmp]
            return ctor(a=base, b=Lit(val))
        if op == "not":
            return Not(build(struct["args"][0]))
        ctor = And if op == "and" else Or
        return ctor(items=tuple(build(a) for a in struct["args"]))
    return build(cond_struct)


def emit_block_rule(block: dict, substrate, rule_name: str,
                    match_var: str = "N", root_var: str = "R") -> int:
    """Build + install ONE graph Rule for a single recognized block, mirroring
    `install_requires_replacement_rule`. Returns the Rule index.

    The Rule:
      match:   [[root_var, "has_<TYPE>", match_var]]   (edge to each node of TYPE)
      where:   the block's CONDITION as a Term over Attr(match_var, key)
      effects: set_attr / self add_edge, exactly the Python block's mutations.

    NO LLM — pure Term emission."""
    nat = _native(substrate)
    node_type = block["node_type"]
    edge_type = _wire_type_under_root(substrate, node_type)

    where = _condition_term_for_var(block["condition"], match_var).to_dict()

    effects = []
    for eff in block["effects"]:
        if eff["kind"] == "set_attr":
            effects.append(["set_attr", match_var, eff["key"],
                            {"__term__": Lit(eff["value"]).to_dict()}])
        elif eff["kind"] == "add_edge":
            # Self-edge: src and tgt both the matched node.
            effects.append(["add_edge", match_var, eff["edge_type"], match_var])

    rule = {
        "name": rule_name,
        "match": [[root_var, edge_type, match_var]],
        "where": where,
        "effects": effects,
    }
    return nat.add_rule(rule)


def emit_rule(recognized: dict, substrate, match_var: str = "N",
              root_var: str = "R") -> int:
    """Back-compat single-Rule emitter — emits the FIRST block. Returns its Rule
    index. Multi-block functions should use `emit_rules` (one Rule per block)."""
    blocks = recognized.get("blocks") or [recognized]
    return emit_block_rule(blocks[0], substrate,
                           f"lifted_{recognized['func_name']}",
                           match_var, root_var)


def emit_rules(recognized: dict, substrate, match_var: str = "N",
               root_var: str = "R") -> list[int]:
    """Emit one graph Rule PER recognized block, in source order. Returns the
    list of Rule indices. A single-block function yields one Rule; a
    multi-statement function yields several — each block independently lifted."""
    blocks = recognized.get("blocks") or [recognized]
    fname = recognized["func_name"]
    nids = []
    for i, block in enumerate(blocks):
        name = f"lifted_{fname}" if len(blocks) == 1 else f"lifted_{fname}_{i}"
        nids.append(emit_block_rule(block, substrate, name, match_var, root_var))
    return nids


def fire_lifted_rule(substrate, rule_index: int, node_type: str,
                     max_iters: int | None = None) -> int:
    """Drive the lifted Rule to fixpoint via the engine's `run_rules`.

    `apply_rule_once` returns the FIRST match and stops — for an idempotent
    decision rule (set_attr to a constant) the first qualifying node would
    re-fire forever, never advancing. `run_rules` is the engine's canonical
    fix: it walks PAST no-op bindings (a set_attr / add_edge that doesn't
    change the graph records no progress and is undone) until every match has
    been progressed, reaching a true fixpoint — exactly once per node. Returns
    the number of progressing applications.

    `rule_index` / `node_type` are accepted for symmetry with the per-rule API;
    `run_rules` fires every installed Rule in the substrate (the lifter installs
    its Rule(s) into a focused substrate, so this is the right driver).
    `node_type` may be a single type string or a list of types (multi-block):
    the cap is sized over the union of nodes of those types."""
    nat = _native(substrate)
    types = [node_type] if isinstance(node_type, str) else list(node_type)
    count = sum(len(list(substrate.nodes(t))) for t in types)
    cap = max_iters if max_iters is not None else count * 4 + 16
    substrate.add_node("NativeRuleLifterReceipt", {
        "schema": "native_rule_lifter_receipt_v1",
        "cluster": "rule_lifter.fixpoint_execution",
        "provenance": "native_rule_readback:lifted_rule",
        "native_rule": "lifted_rule_native_fixpoint",
        "native_steps": ["install_lifted_rule", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    return nat.run_rules(cap)


def lift_function(substrate, py_source: str, func_name: str) -> dict:
    """Recognize then emit. Returns {ok, rule_nids, rule_nid, reason,
    recognized}. `rule_nids` is the list of one-Rule-per-block indices;
    `rule_nid` is the first (back-compat). ok=False with a reason when the
    function is outside the liftable subset (the recognizer is conservative —
    a near-miss is rejected, never lifted to a wrong Rule, and a multi-statement
    function with ANY unrecognizable top-level statement is rejected WHOLE)."""
    ok, recognized, reason = recognize_with_reason(py_source, func_name)
    if not ok:
        return {"ok": False, "rule_nids": [], "rule_nid": None,
                "reason": reason, "recognized": None}
    rule_nids = emit_rules(recognized, substrate)
    clean = {k: v for k, v in recognized.items() if k != "_condition_term"}
    clean["blocks"] = [{k: v for k, v in b.items() if k != "_condition_term"}
                       for b in recognized["blocks"]]
    return {"ok": True, "rule_nids": rule_nids, "rule_nid": rule_nids[0],
            "reason": "", "recognized": clean}


__all__ = [
    "recognize_rule_shape",
    "recognize_with_reason",
    "emit_block_rule",
    "emit_rule",
    "emit_rules",
    "fire_lifted_rule",
    "lift_function",
]
