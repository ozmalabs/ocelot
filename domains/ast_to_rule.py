"""ast_to_rule — the MECHANICAL statement->Rule migrator: a stateful Python method -> a RewriteRule.

The mechanizability measurement showed ~90% of curious_agent.py statements have a known Rule shape.
This realises that translation. The split that keeps it honest:

  · EXPRESSIONS (conditions, values) are composed BY THE GRAPH RULES (ast_term_rules) — ingested,
    folded by the engine into a Term, then read out to Term-JSON (`term_to_json`, a mechanical
    serialisation of already-composed graph data, like a world-adapter emit — NOT a Python emitter).
  · STATEMENT SHELLS map mechanically to the engine's Effect vocabulary:
        if C: <body>                 -> where = Term(C); effects = <body>
        self.x = e                   -> set_attr(self, "x", Term(e))
        obj.attrs[k] = e             -> set_attr(<obj>, k, Term(e))
        coll.add(t) / coll.append(t) -> add_edge(self, "coll", Term(t))
        return e                     -> the Rule's produced value (a query)

The non-mechanical residue (external calls, try/with/while, the match/trigger) is left as a marked
gap — the ~10% that needs judgment. `method_to_rule` returns the assembled Rule plus what it could
not translate, so the migration is auditable, not silent.
"""
from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional

import substrate_rs as srs

from domains import ast_term_rules as R
from domains.ast_to_term import ingest_ast, open_ast_productions

_LIST_FIELDS = ("items", "args")     # always a list (even with one child), per reconstruct
_SINGLE_FIELDS = ("a", "b", "arg", "cond", "then", "other", "value", "body", "source",
                  "init", "predicate", "seq", "item", "index", "node")


def term_to_json(s, nid) -> Dict[str, Any]:
    """Read an engine-emitted graph-Term (Term.X node + child.* edges + scalar attrs) out to
    Term-JSON. `items`/`args` are always lists; the rest single-child. Mechanical serialisation of
    already-composed graph data, not composition."""
    nd = s.node(nid)
    out: Dict[str, Any] = {"type": nd["type"][len("Term."):]}
    for k, v in nd["attrs"].items():
        out[k] = v
    for f in _LIST_FIELDS:
        ts = list(s.neighbours(nid, "child." + f))
        if ts:
            out[f] = [term_to_json(s, t) for t in ts]
    for f in _SINGLE_FIELDS:
        ts = list(s.neighbours(nid, "child." + f))
        if ts:
            out[f] = term_to_json(s, ts[0])
    return out


class Migrator:
    """Translate methods to Rules over ONE substrate (rules installed once); compose each expression
    by ingesting it and reading the emitted Term."""

    def __init__(self) -> None:
        self.s = srs.Substrate()
        self.nat = self.s._inner
        open_ast_productions(self.s)
        R.install(self.s)
        self._n = 0

    # The substrate's own Term constructors (substrate_rs / substrate.dsl): a call to one of these
    # IS the Term it builds — the agent is hand-writing Term-JSON in Python. Recognising them is
    # transcription of the agent's explicit graph-data construction, not composition. (param -> "s"
    # scalar / "t" sub-term; VARIADIC take an items list.)
    _CTORS = {
        "Var": [("name", "s")], "Lit": [("value", "s")], "TypeOf": [("node", "t")],
        "Attr": [("node", "t"), ("key", "s")],
        "In": [("member", "t"), ("container", "t")],
        "Eq": [("a", "t"), ("b", "t")], "Lt": [("a", "t"), ("b", "t")],
        "Lte": [("a", "t"), ("b", "t")], "Gt": [("a", "t"), ("b", "t")],
        "Gte": [("a", "t"), ("b", "t")], "Div": [("a", "t"), ("b", "t")],
        "Pow": [("a", "t"), ("b", "t")], "Minus": [("a", "t"), ("b", "t")],
        "Dot": [("a", "t"), ("b", "t")], "Union": [("a", "t"), ("b", "t")],
        "Neg": [("arg", "t")], "Not": [("arg", "t")], "Abs": [("arg", "t")],
        "Sqrt": [("arg", "t")], "Log": [("arg", "t")], "Exp": [("arg", "t")],
        "Count": [("source", "t")], "Pick": [("source", "t")],
        "Neighbours": [("node", "t"), ("edge_type", "s")],
        "InNeighbours": [("node", "t"), ("edge_type", "s")],
        "MapNeighbours": [("source", "t"), ("edge_type", "s")],
        "Filter": [("source", "t"), ("var_name", "s"), ("predicate", "t")],
        "Exists": [("source", "t"), ("var_name", "s"), ("predicate", "t")],
        "Sum": [("source", "t"), ("var_name", "s"), ("value", "t")],
        "Prod": [("source", "t"), ("var_name", "s"), ("value", "t")],
        "MinOver": [("source", "t"), ("var_name", "s"), ("value", "t")],
        "MaxOver": [("source", "t"), ("var_name", "s"), ("value", "t")],
        "Tokenize": [("text", "t")], "FinalToken": [("text", "t")],
    }
    _VARIADIC = {"Plus", "Times", "And", "Or", "SetT", "Cat", "Min", "Max", "MkDict", "Vec"}

    def _ctor_name(self, expr: ast.AST):
        if isinstance(expr, ast.Call):
            f = expr.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if nm in self._CTORS or nm in self._VARIADIC:
                return nm
        return None

    def _ctor_term(self, nm: str, call: ast.Call) -> Optional[Dict[str, Any]]:
        """A Term-constructor call -> its Term-JSON (recursing on sub-term args; None if a scalar
        arg isn't a literal or a sub-term doesn't compose)."""
        if nm in self._VARIADIC:
            items = []
            for a in call.args:
                elts = a.elts if isinstance(a, (ast.List, ast.Tuple)) else [a]
                for e in elts:
                    t = self.expr_term(e)
                    if t is None:
                        return None
                    items.append(t)
            return {"type": nm, "items": items}
        plan = self._CTORS[nm]
        provided = {plan[i][0]: a for i, a in enumerate(call.args) if i < len(plan)}
        provided.update({kw.arg: kw.value for kw in call.keywords if kw.arg})
        out: Dict[str, Any] = {"type": nm}
        for pname, kind in plan:
            if pname not in provided:
                continue                                  # optional (edge_type/default)
            av = provided[pname]
            if kind == "s":
                if not isinstance(av, ast.Constant):
                    return None                           # dynamic scalar -> not statically a Term
                out[pname] = av.value
            else:
                t = self.expr_term(av)
                if t is None:
                    return None
                out[pname] = t
        return out

    def _graph_read(self, expr: ast.AST) -> Optional[Dict[str, Any]]:
        """`g.node(X).attrs.get("k")` / `g.node(X).attrs["k"]` -> Attr{node=X, key="k"} — the agent
        reading a node attr, which in a Rule is a graph read off a matched node."""
        if isinstance(expr, ast.Subscript) and isinstance(expr.value, ast.Attribute) \
                and expr.value.attr == "attrs":
            base, key = expr.value.value, expr.slice
        elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) \
                and expr.func.attr == "get" and isinstance(expr.func.value, ast.Attribute) \
                and expr.func.value.attr == "attrs" and expr.args:
            base, key = expr.func.value.value, expr.args[0]
        else:
            return None
        if not (isinstance(base, ast.Call) and isinstance(base.func, ast.Attribute)
                and base.func.attr == "node" and base.args):
            return None
        if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
            return None
        nt = self.expr_term(base.args[0])
        return {"type": "Attr", "node": nt, "key": key.value} if nt is not None else None

    def expr_term(self, expr: ast.AST) -> Optional[Dict[str, Any]]:
        """Compose a Python expression -> Term-JSON. A Term-constructor call / dict / tuple literal is
        recognised directly (the agent's explicit data-building); any other expression is composed BY
        THE RULES."""
        nm = self._ctor_name(expr)
        if nm is not None:
            t = self._ctor_term(nm, expr)
            if t is not None:
                return t
        # nested-module np call: np.<...>.<fn>(args) -> UseTool{tool=<fn>, args} (the held-op boundary;
        # the np-rule only catches np.<fn>, so np.linalg.norm / np.random.x land here).
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute):
            root = expr.func
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name) and root.id == "np" and isinstance(expr.func.value, ast.Attribute):
                args = [self.expr_term(a) for a in expr.args]
                if args and all(a is not None for a in args):
                    return {"type": "UseTool", "tool": expr.func.attr,
                            "args": args}
        # builtin reductions: len(x) -> Count; min/max(...) -> Min/Max (the held reduction Terms)
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            bn = expr.func.id
            if bn == "len" and len(expr.args) == 1:
                s = self.expr_term(expr.args[0])
                if s is not None:
                    return {"type": "Count", "source": s}
            if bn in ("min", "max") and expr.args:
                src = expr.args
                elts = (src[0].elts if len(src) == 1 and isinstance(src[0], (ast.List, ast.Tuple))
                        else src)
                its = [self.expr_term(e) for e in elts]
                if all(x is not None for x in its):
                    return {"type": "Min" if bn == "min" else "Max", "items": its}
        # graph-state read: g.node(X).attrs.get("k") / g.node(X).attrs["k"] -> Attr{node=X, key="k"}
        gr = self._graph_read(expr)
        if gr is not None:
            return gr
        # dict literal {str: v, ...} -> MkDict (alternating [key, value, ...]; string keys only)
        if isinstance(expr, ast.Dict):
            items = []
            for k, v in zip(expr.keys, expr.values):
                if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                    return None
                vt = self.expr_term(v)
                if vt is None:
                    return None
                items += [{"type": "Lit", "value": k.value}, vt]
            return {"type": "MkDict", "items": items}
        # tuple/list literal -> Vec (ordered; preserves order + duplicates, unlike the rules' SetT)
        if isinstance(expr, (ast.Tuple, ast.List)):
            els = []
            for e in expr.elts:
                et = self.expr_term(e)
                if et is None:
                    return None
                els.append(et)
            return {"type": "Vec", "items": els}
        self._n += 1
        lbl = f"e{self._n}"
        try:
            ingest_ast(self.s, "def _():\n    return " + ast.unparse(expr), root_label=lbl)
        except Exception:
            return None
        native_steps = self.nat.run_rules(2500)
        self.s.add_node("NativeASTToRuleReceipt", {
            "schema": "native_ast_to_rule_receipt.v1",
            "cluster": "ast_to_rule.expression_settlement",
            "provenance": "native_rule_readback:ast_to_term",
            "native_rule": "ast_to_term_rules",
            "native_steps": int(native_steps),
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        fd = next((n for n in self.s.nodes("AstNode")
                   if self.s.node(n)["attrs"].get("ast_type") == "FunctionDef"
                   and self.s.node(n)["attrs"].get("module") == lbl), None)
        if fd is None:
            return None
        ret = next((c for c in self.s.neighbours(fd, "child")
                    if self.s.node(c)["attrs"].get("ast_type") == "Return"), None)
        val = next((c for c in self.s.neighbours(ret, "child")
                    if self.s.node(c)["attrs"].get("child_field") == "value"), None) if ret else None
        em = list(self.s.neighbours(val, "emits")) if val is not None else []
        return term_to_json(self.s, em[0]) if len(em) == 1 else None

    def _value(self, expr: ast.AST):
        """A Term-JSON value as a Computed effect arg, or a residual marker."""
        t = self.expr_term(expr)
        return {"__term__": t} if t is not None else None

    def body_term(self, fn: ast.FunctionDef) -> Optional[Dict[str, Any]]:
        """Compose the WHOLE method body via the AST->Term rules' block porter (which threads local
        `x=e` as Let, `for` as Fold, `if` as IfThenElse, the Return as the value). Returns the body's
        Term-JSON, or None if the body isn't a pure value-producer (e.g. it writes self.<attr>, which
        the block porter leaves as a residual — those go through the effects path instead)."""
        self._n += 1
        lbl = f"b{self._n}"
        try:
            ingest_ast(self.s, ast.unparse(fn), root_label=lbl)
        except Exception:
            return None
        native_steps = self.nat.run_rules(4000)
        self.s.add_node("NativeASTToRuleReceipt", {
            "schema": "native_ast_to_rule_receipt.v1",
            "cluster": "ast_to_rule.body_settlement",
            "provenance": "native_rule_readback:ast_to_term",
            "native_rule": "ast_to_term_rules",
            "native_steps": int(native_steps),
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        fd = next((n for n in self.s.nodes("AstNode")
                   if self.s.node(n)["attrs"].get("ast_type") == "FunctionDef"
                   and self.s.node(n)["attrs"].get("module") == lbl), None)
        if fd is None:
            return None
        head = next((c for c in self.s.neighbours(fd, "child")
                     if self.s.node(c)["attrs"].get("child_field") == "body"
                     and self.s.node(c)["attrs"].get("child_index") == 0), None)
        em = list(self.s.neighbours(head, "emits")) if head is not None else []
        return term_to_json(self.s, em[0]) if len(em) == 1 else None

    @staticmethod
    def _is_graph_call(call: ast.Call, op: str) -> bool:
        f = call.func
        return isinstance(f, ast.Attribute) and f.attr == op

    def _mutation(self, stmt: ast.AST) -> Optional[List[Any]]:
        """A state-mutating statement -> one engine Effect, or None if not a recognised mutation."""
        # nid = <g>.add_node(TYPE, {attrs})  -> add_node effect (binds nid for later edges)
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                and isinstance(stmt.targets[0], ast.Name) \
                and isinstance(stmt.value, ast.Call) and self._is_graph_call(stmt.value, "add_node"):
            args = stmt.value.args
            if args and isinstance(args[0], ast.Constant):
                attrs = {}
                if len(args) > 1 and isinstance(args[1], ast.Dict):
                    for k, v in zip(args[1].keys, args[1].values):
                        if isinstance(k, ast.Constant):
                            cv = self._value(v)
                            attrs[str(k.value)] = cv if cv is not None else None
                return ["add_node", stmt.targets[0].id, str(args[0].value), attrs]
        # self.x = e   /   obj.attrs[k] = e   -> set_attr
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            tgt = stmt.targets[0]
            val = self._value(stmt.value)
            if val is None:
                return None
            if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name):
                return ["set_attr", tgt.value.id, tgt.attr, val]              # self.x = e
            if isinstance(tgt, ast.Subscript) and isinstance(tgt.value, ast.Attribute) \
                    and isinstance(tgt.slice, ast.Constant):
                return ["set_attr", tgt.value.attr, str(tgt.slice.value), val]  # obj.attrs['k'] = e
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            f = call.func
            # <g>.add_edge(src, "edge", tgt)  -> add_edge effect (src/tgt are bound node vars)
            if self._is_graph_call(call, "add_edge") and len(call.args) >= 3 \
                    and isinstance(call.args[0], ast.Name) and isinstance(call.args[1], ast.Constant) \
                    and isinstance(call.args[2], ast.Name):
                return ["add_edge", call.args[0].id, str(call.args[1].value), call.args[2].id]
            # coll.add(t) / coll.append(t)  -> add_edge(self, coll, t)
            if isinstance(f, ast.Attribute) and f.attr in ("add", "append") \
                    and isinstance(f.value, ast.Attribute) and isinstance(f.value.value, ast.Name) \
                    and call.args:
                tgt = self._value(call.args[0])
                if tgt is not None:
                    return ["add_edge", f.value.value.id, f.value.attr, tgt]
        return None

    def method_to_rule(self, fn: ast.FunctionDef) -> Dict[str, Any]:
        """Assemble the Rule for a method: where from a guarding `if`, effects from its mutations.
        Returns {name, rule|None, where, effects, residual:[...]} — residual = statements not
        mechanically translatable (the judgment gap)."""
        body = [st for st in fn.body
                if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant))]
        where = None
        effects: List[Any] = []
        residual: List[str] = []

        def take(stmts: List[ast.AST]) -> None:
            for st in stmts:
                mut = self._mutation(st)
                if mut is not None:
                    effects.append(mut)
                elif isinstance(st, (ast.With, ast.AsyncWith)):
                    take(st.body)                         # transaction wrapper -> no-op in the engine
                elif isinstance(st, ast.Return):
                    pass                                  # a query — the Rule's produced value
                else:
                    residual.append(type(st).__name__)

        for st in body:
            if isinstance(st, ast.If) and where is None and not st.orelse:
                where = self._value(st.test)              # the guard
                take(st.body)
            elif isinstance(st, ast.Return):
                pass                                      # the body-as-value is composed below
            else:
                take([st])

        # A pure value-producer (no state effects) migrates as a Term: a clean single-return composes
        # its return expression (fast); a multi-statement body composes WHOLE via the rules' block
        # porter (local bindings -> Let, loops -> Fold, branches -> IfThenElse) which absorbs the
        # statements. State methods (effects present) use the effects path.
        returns = None
        if not effects:
            ret_val = next((s.value for s in body
                            if isinstance(s, ast.Return) and s.value is not None), None)
            if not residual and ret_val is not None:
                returns = self.expr_term(ret_val)         # clean single-return, fast
            else:
                bt = self.body_term(fn)                   # bindings/loops -> Let/Fold; absorbs stmts
                if bt is not None:
                    returns, residual = bt, []

        ok = bool(effects) and not residual
        rule = None
        if ok:
            rule = {"name": f"migrated_{fn.name}",
                    "match": [["self", "is_a", "Agent"]],   # placeholder trigger — the judgment 10%
                    "where": where.get("__term__") if where else None,
                    "effects": effects}
        return {"name": fn.name, "rule": rule, "where": where, "effects": effects,
                "residual": residual, "returns": returns}


__all__ = ["Migrator", "term_to_json"]
