"""The agent GENERATES its AST->Term map as rewrite rules, ports real Python, evaluates it native.

This replaces the rejected Python `emit_term` cascade. `domains/ast_term_rules` holds the only
knowledge — the CORRESPONDENCE (Python `Add` MEANS my `Plus`, `IfExp` MEANS `IfThenElse`, `Compare`
with a `Gt` op MEANS `Gt`, …) — and ONE uniform template that expands every row into a rewrite-rule
dict (no per-node-type branching). The agent installs those rules; the Rust engine applies them
bottom-up over an ingested `AstNode` graph (`run_rules`), folding it into a graph-resident Term-tree
(`Term.<Variant>` nodes + `child.<field>` edges, per reflect::term_from_subgraph); `EvalSubgraph`
then evaluates that graph Term. The compute moved Python -> native WITHOUT a Python emitter: the map
is data the agent owns, the fold is the engine's.

Verified: each ported function evaluates identically to the original Python. The full map is more
correspondence rows of the same shape (BoolOp/Subscript/comprehension as expression rows; Let/Fold
from assignments/loops as statement-level rules) — extension is data, not code.

Run:  python -m scripts.ast_to_term_rules_generate
"""
from __future__ import annotations

import substrate_rs as srs

from domains import ast_term_rules as R
from domains.ast_to_term import ingest_ast, open_ast_productions


def _collapse_runs_ref(xs):
    out = []
    for u in xs:
        if not out or out[-1] != u:
            out.append(u)
    return out


SUITE = [
    ("ema_background", "def f(bg, frame):\n    return 0.95 * bg + 0.05 * frame",
     lambda bg, frame: 0.95 * bg + 0.05 * frame, [{"bg": 2.0, "frame": 10.0}, {"bg": 5.0, "frame": -3.0}]),
    ("diff_of_squares", "def f(a, b):\n    return (a - b) * (a + b)",
     lambda a, b: (a - b) * (a + b), [{"a": 5, "b": 3}, {"a": 2, "b": 7}]),
    ("abs", "def f(x):\n    return x if x > 0 else -x",
     lambda x: x if x > 0 else -x, [{"x": 4}, {"x": -9}, {"x": 0}]),
    ("max3", "def f(a, b, c):\n    return (a if a >= b else b) if (a if a >= b else b) >= c else c",
     lambda a, b, c: (a if a >= b else b) if (a if a >= b else b) >= c else c,
     [{"a": 3, "b": 7, "c": 5}, {"a": 9, "b": 2, "c": 4}, {"a": 1, "b": 1, "c": 8}]),
    # statement-level: Let (straight-line assignments) and Fold (accumulation loops)
    ("let_square", "def f(a, b):\n    t = a + b\n    return t * t",
     lambda a, b: (a + b) * (a + b), [{"a": 2, "b": 3}, {"a": 5, "b": -1}]),
    ("sum_loop", "def f(xs):\n    acc = 0\n    for x in xs:\n        acc = acc + x\n    return acc",
     lambda xs: sum(xs), [{"xs": [1, 2, 3, 4]}, {"xs": [10, -5, 5]}]),
    ("prod_loop", "def f(xs):\n    acc = 1\n    for x in xs:\n        acc = acc * x\n    return acc",
     lambda xs: __import__("math").prod(xs), [{"xs": [1, 2, 3, 4]}, {"xs": [2, 5]}]),
    # non-template expression rules: BoolOp (boolean context), Subscript (>=0), comprehension->Filter
    ("bool_or_value", "def f(a, b):\n    return a or b",      # value context: returns the OPERAND
     lambda a, b: a or b, [{"a": 0, "b": 5}, {"a": 3, "b": 5}, {"a": 0, "b": 0}]),
    ("bool_and_value", "def f(a, b):\n    return a and b",
     lambda a, b: a and b, [{"a": 0, "b": 5}, {"a": 3, "b": 5}]),
    ("bool_or3_bool", "def f(a, b, c):\n    return 1 if (a > 0 or b > 0 or c > 0) else 0",
     lambda a, b, c: 1 if (a > 0 or b > 0 or c > 0) else 0,
     [{"a": -1, "b": -1, "c": -1}, {"a": -1, "b": 5, "c": -1}]),
    ("subscript", "def f(s):\n    return s[0] + s[2]", lambda s: s[0] + s[2],
     [{"s": [3, 9, 4]}, {"s": [1, 1, 1]}]),
    # SET comprehensions (faithful: MapSet/Filter ARE set semantics). List comps are residuals.
    ("set_filter", "def f(xs):\n    return {x for x in xs if x > 0}",
     lambda xs: {x for x in xs if x > 0}, [{"xs": [3, 1, 5, -2, 3]}, {"xs": [-1]}], "set"),
    ("set_map_if", "def f(xs):\n    return {x * x for x in xs if x > 0}",
     lambda xs: {x * x for x in xs if x > 0}, [{"xs": [1, -2, 3]}, {"xs": [2, 2, 3]}], "set"),
    # LIST comprehensions -> ordered MapList/FilterList (added via Layer B): order + dups preserved
    ("list_map", "def f(xs):\n    return [x * x for x in xs]",
     lambda xs: [x * x for x in xs], [{"xs": [3, 1, 3]}, {"xs": [2, -2]}], "list"),
    ("list_map_if", "def f(xs):\n    return [x * x for x in xs if x > 0]",
     lambda xs: [x * x for x in xs if x > 0], [{"xs": [3, -1, 2, 3]}], "list"),
    # conditional-append accumulation loop == a filtered list comprehension (-> MapList/FilterList)
    ("cond_append", "def f(xs):\n    out = []\n    for x in xs:\n        if x > 0:\n            out.append(x * x)\n    return out",
     lambda xs: [x * x for x in xs if x > 0], [{"xs": [3, -1, 2, -4, 3]}, {"xs": [-1]}], "list"),
    # from-end subscript (IndexAt, Layer B) and a stateful acc-dependent loop (collapse_runs)
    ("last_index", "def f(s):\n    return s[-1] + s[0]", lambda s: s[-1] + s[0],
     [{"s": [10, 20, 30]}, {"s": [4, 9]}]),
    ("collapse_runs", "def f(xs):\n    out = []\n    for u in xs:\n        if not out or out[-1] != u:\n            out.append(u)\n    return out",
     _collapse_runs_ref, [{"xs": [1, 1, 2, 2, 3, 1, 1]}, {"xs": [5, 5, 5]}, {"xs": []}], "list"),
]


def _block_head(s, name: str) -> int:
    """The root Term = `emits` of the FunctionDef body's index-0 statement (the block head): the
    Return's value for an expression body, the head Let for a statement body."""
    fd = next(n for n in s.nodes("AstNode")
              if s.node(n)["attrs"].get("ast_type") == "FunctionDef"
              and s.node(n)["attrs"].get("module") == name)
    head = next(c for c in s.neighbours(fd, "child")
                if s.node(c)["attrs"].get("child_field") == "body"
                and s.node(c)["attrs"].get("child_index") == 0)
    em = list(s.neighbours(head, "emits"))
    if len(em) != 1:
        raise AssertionError(f"{name}: block head emits {len(em)} Terms, expected 1")
    return em[0].value


def port_and_eval(s, nat, name, src, ref, cases, kind="num") -> bool:
    ingest_ast(s, src, root_label=name)
    nat.run_rules(3000)
    term = {"type": "EvalSubgraph", "node": {"type": "Lit", "value": {"__nid__": _block_head(s, name)}}}
    ok = True
    for env in cases:
        raw = nat.evaluate(term, env)
        if kind == "set":
            got, want = set(raw), set(ref(**env))
            m = got == want
        elif kind == "list":
            got, want = list(raw), list(ref(**env))
            m = got == want
        else:
            got, want = float(raw), float(ref(**env))
            m = abs(got - want) < 1e-9
        ok &= m
        print(f"    {name:16} {env}  rules={got}  python={want}  {'OK' if m else 'MISMATCH'}")
    return ok


def main() -> None:
    s = srs.Substrate()
    nat = s._inner
    open_ast_productions(s)
    info = R.install(s)
    rules = R.generate_rules()
    print("=" * 80)
    print("AGENT-GENERATED AST->Term RULES — port Python via the engine, evaluate native")
    print("=" * 80)
    print(f"  correspondence rows: {len(R.CORRESPONDENCE)}  ->  generated rules: {info['n_rules']}")
    print(f"  Term variants covered: {info['variants']}")
    print(f"  sample generated rule:\n    {rules[2]['name']}: match={rules[2]['match']}")
    print()
    allok = True
    for entry in SUITE:
        name, src, ref, cases = entry[:4]
        kind = entry[4] if len(entry) > 4 else "num"
        allok &= port_and_eval(s, nat, name, src, ref, cases, kind)
    print("\n" + "=" * 80)
    print(f"  ALL PORTED BY GENERATED RULES, EVAL == PYTHON: {allok}")
    print("  -> no Python emit_term: the map is rule DATA the agent owns; the fold is the Rust engine.")
    print("=" * 80)


if __name__ == "__main__":
    main()
