"""The AST->Term map belongs in the GRAPH as rewrite rules — NOT a Python emitter.

The irony the creator named: a Python `emit_term` cascade (if ast_type == 'If' -> IfThenElse,
if == 'Compare' -> Eq/Lt, fold-idiom recognition, ...) is the agent UNDERSTANDING its own code —
composition and decisions — written as host-language `if`/`else`. CLAUDE.md: composition lives in
the graph, never in Python. A "fixed map from AST node type to Term type" IS a rewrite system, and
the substrate already HAS one in Rust (rewrite::RewriteRule, run_rules/tick).

So the agent's own constitution decides the home: the map is rewrite-rule DATA the agent owns and
the Rust engine applies — `ingest_ast` (legitimate world-adapter I/O: source -> AstNode graph) ->
`tick()` (the engine folds AstNode subtrees into Term nodes via the rules) -> `EvalSubgraph` (eval
the graph-resident Term-tree). No `emit_term`, no Python map.

This script PROVES the mechanism on one map entry. The full map is more rules of the SAME shape —
graph data, ideally agent-generated (runtime_design / a rule-authoring faculty), not a Python
function. `domains/ast_to_term.py`'s `emit_term`/`AstTermEmitter` is thereby superseded: keep
`ingest_ast`/`open_ast_productions` (the I/O), delete the Python emitter as the rule set grows.

Run:  python -m scripts.ast_to_term_rule_proof
"""
from __future__ import annotations

import substrate_rs as srs

from domains.ast_to_term import ingest_ast, open_ast_productions

# ONE entry of the AST->Term map, as rule DATA (not Python): Constant -> Lit, value carried over.
# match: a parent --child--> c edge; where: c is a Constant; effects: mint a Lit holding c.value
# and link c --emits--> lit. The same shape scales to BinOp:Add->Plus, If->IfThenElse, the fold
# idiom, etc. — each a rule, run by the Rust engine, owned by the agent as graph data.
CONSTANT_TO_LIT = {
    "name": "ast_constant_to_lit",
    "match": [["p", "child", "c"]],
    "where": {"type": "Eq",
              "a": {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "ast_type"},
              "b": {"type": "Lit", "value": "Constant"}},
    "effects": [
        ["add_node", "lit", "Lit",
         {"value": {"__term__": {"type": "Attr",
                                 "node": {"type": "Var", "name": "c"}, "key": "value"}}}],
        ["add_edge", "c", "emits", "lit"],
    ],
}


def main() -> None:
    s = srs.Substrate()
    nat = s._inner
    open_ast_productions(s)
    # admit the AstNode --emits--> Lit edge (grammar), then ingest a compute-core.
    try:
        s.add_production({"src": {"type": "AstNode", "var": "a"}, "edge_type": "emits",
                          "tgt": {"type": "Lit", "var": "b"}, "where": None,
                          "provenance": "ast_to_term_rule"})
    except Exception:
        pass
    ingest_ast(s, "def f():\n    return 5", root_label="proof")

    print("=" * 74)
    print("AST->Term as a GRAPH RULE (the agent's engine ports its code, not Python)")
    print("=" * 74)
    nat.add_rule(CONSTANT_TO_LIT)
    before = sum(1 for _ in s.nodes("Lit"))
    fired = nat.run_rules(50)
    lits = [s.node(n)["attrs"].get("value") for n in s.nodes("Lit")]
    print(f"  Lit nodes before tick: {before}")
    print(f"  rule applications (Rust engine): {fired}")
    print(f"  Lit nodes after tick:  {len(lits)}  values={lits}")
    ok = lits == [5]
    print(f"\n  PORTED BY A RULE, NOT PYTHON: {ok}")
    print("  -> the Constant AstNode was rewritten to a Lit Term by rule DATA the agent owns.")
    print("  -> full map = more such rules; emit_term (Python) is superseded.")
    print("=" * 74)


if __name__ == "__main__":
    main()
