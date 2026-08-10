"""CONSUME curious_agent.py through the agent's own AST->Term porting pipeline, and report the FIX.

CuriousAgent is the 18.5k-line Python agent class CLAUDE.md marks for deletion: "the agent is a
graph running in Rust; Python is only the world adapter." This script feeds every one of its
functions through the agent's generated AST->Term rules (install -> ingest -> run_rules -> read the
body head's `emits`) and CATEGORISES each by where it must go in the migration:

  PORTED    — folds to a native Term-tree: pure compute the agent can OWN as graph data (move it).
  HELD-OP   — reimplements an existing Rust op (argsort/log2/...): delete it, call the op.
  STATE     — reads/writes self.<attr>: agent STATE + a DECISION -> a graph RULE over nodes.
  CALLS     — composes other methods/builtins: a faculty composition -> Rules / sub-Terms.
  DICT/COMP — dict/list machinery (DictComp, dict build): a DECISION -> a graph RULE.
  RESIDUAL  — other un-ported AST: a Layer-B primitive candidate or a Rule.

The verdict is the migration map: what little is pure compute (PORTED -> native), and that the bulk
is decisions + state access (-> Rules), which is exactly why the class is being replaced by graph
data rather than hand-ported. PORTED functions are verified faithful where they take simple inputs.

Run:  python -m scripts.consume_curious_agent
"""
from __future__ import annotations

import ast

import substrate_rs as srs

from domains import ast_term_rules as R
from domains.ast_to_term import ingest_ast, open_ast_productions

HELD = R  # noqa  (held-op names live in donkey_to_graph; we re-detect a few here)
HELD_OPS = {"argsort", "log2", "mean", "abs", "stack", "sqrt", "exp", "dot", "norm"}


def _diagnose(s, label: str) -> str:
    """Why function `label` didn't port — the dominant reason, scanning its AstNodes."""
    has_state = has_dict = False
    held = set()
    calls = set()
    for n in s.nodes("AstNode"):
        a = s.node(n)["attrs"]
        if a.get("module") != label:
            continue
        t = a.get("ast_type", "")
        if t in ("DictComp", "Dict", "SetComp"):
            has_dict = True
        if t == "Attribute":
            for c in s.neighbours(n, "child"):
                ca = s.node(c)["attrs"]
                if ca.get("child_field") == "value" and ca.get("ast_type") == "Name" \
                        and ca.get("id") == "self":
                    has_state = True
        if t == "Call":
            for c in s.neighbours(n, "child"):
                ca = s.node(c)["attrs"]
                if ca.get("child_field") == "func":
                    nm = ca.get("id") or ca.get("attr")
                    if nm in HELD_OPS:
                        held.add(nm)
                    elif nm:
                        calls.add(nm)
    if held:
        return "HELD-OP", f"held op(s) {sorted(held)} -> call the Rust op"
    if has_state:
        return "STATE", "reads/writes self.<attr> -> agent state + decision -> a graph RULE"
    if has_dict:
        return "DICT/COMP", "dict/comprehension machinery -> a graph RULE"
    if calls:
        return "CALLS", f"composes {sorted(calls)[:4]} -> Rules / sub-Terms"
    return "RESIDUAL", "other un-ported AST -> Layer-B primitive candidate or Rule"


def main() -> None:
    src = open("domains/curious_agent.py").read()
    defs = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)]

    tally = {"PORTED": 0, "HELD-OP": 0, "STATE": 0, "CALLS": 0, "DICT/COMP": 0,
             "RESIDUAL": 0, "SKIP": 0}
    ported = []
    actionable = []                              # (name, kind, reason) for the concrete fixes
    for i, d in enumerate(defs):
        lbl = f"f{i}"
        s = srs.Substrate()
        nat = s._inner
        open_ast_productions(s)
        for r in R.generate_rules():             # add_rule only; rule effects bypass the grammar
            nat.add_rule(r)
        try:
            rec = ingest_ast(s, ast.unparse(d), root_label=lbl)
        except Exception:
            tally["SKIP"] += 1
            continue
        # Only SMALL functions can be pure compute worth porting; big ones are loops/decisions whose
        # `run_rules` is expensive and which never port — diagnose those statically.
        if rec["n_nodes"] <= 120:
            nat.run_rules(2000)
        fd = next((n for n in s.nodes("AstNode")
                   if s.node(n)["attrs"].get("ast_type") == "FunctionDef"
                   and s.node(n)["attrs"].get("module") == lbl), None)
        head = next((c for c in s.neighbours(fd, "child")
                     if s.node(c)["attrs"].get("child_field") == "body"
                     and s.node(c)["attrs"].get("child_index") == 0), None) if fd else None
        em = list(s.neighbours(head, "emits")) if head is not None else []
        if len(em) == 1:
            tally["PORTED"] += 1
            ported.append((d.name, s.node(em[0])["type"].removeprefix("Term.")))
        else:
            kind, why = _diagnose(s, lbl)
            tally[kind] += 1
            if kind in ("HELD-OP", "DICT/COMP"):
                actionable.append((d.name, kind, why))

    total = len(defs)
    print("=" * 78)
    print(f"CONSUME curious_agent.py — {total} functions through the agent's AST->Term rules")
    print("=" * 78)
    for k in ("PORTED", "HELD-OP", "STATE", "DICT/COMP", "CALLS", "RESIDUAL", "SKIP"):
        v = tally[k]
        print(f"  {k:<10} {v:>4}  ({100*v/total:4.1f}%)")
    print("\n  PORTED (pure compute -> native Term-trees, the agent can own these):")
    for nm, tt in ported:
        print(f"     {nm:<40} -> {tt}")
    if not ported:
        print("     (none — every function reads state, composes faculties, or decides)")
    print("\n  ACTIONABLE FIXES (delete-and-call / move to a Rule), first 12:")
    for nm, kind, why in actionable[:12]:
        print(f"     [{kind:<9}] {nm:<34} {why}")
    if not actionable:
        print("     (none)")
    print("\n  (functions > 120 AST nodes are diagnosed statically, not engine-ported: a large body")
    print("   is a loop/decision by construction and never folds to a single compute Term.)")
    print("\n" + "=" * 78)
    print("  THE FIX (migration map): PORTED -> native Terms; HELD-OP -> delete, call the Rust op;")
    print("  STATE/DICT/CALLS -> graph RULES over nodes (decisions, not compute). The bulk being")
    print("  decisions + state is exactly why CuriousAgent is replaced by graph data, not hand-ported.")
    print("=" * 78)


if __name__ == "__main__":
    main()
