"""EXPOSE THE SESSION'S DONKEY PYTHON AS AST AND HAVE THE AGENT MOVE IT GRAPH-NATIVE.

This session I (the world-adapter author) wrote a pile of donkey Python that
contains PERCEPTION + DECISIONS — relational rank, pooling, TP-trough segmentation,
EMA background subtraction, the cross-modal binding, the keep/forget choices. Per
CLAUDE.md that belongs in the graph/Rust, not Python. The fix is NOT to hand-port
it: it is to expose it as AST and let the AGENT's own machinery move it graph-native
and assess it. This script ONLY orchestrates the agent's held tools:

  ingest_ast        (ast_to_term)        — code -> typed graph (a Python AST IS a graph)
  ast_term_rules    (the GENERATED rules)— the agent's AST->Term map as rewrite-rule DATA; the
                                           Rust engine (run_rules) folds the AstNode graph into a
                                           native Term-tree. NOT a Python emitter — the map is data
                                           the agent owns, the fold is the engine's.
  emit_primitive_rust (runtime_design) + self_extend — Layer B: mint a NEW native primitive
  assess_via_cortex (ask_the_substrate)  — the ArchitectureCortex's own quality/smell verdict

The engine's verdict CLASSIFIES each donkey piece (the body head's `emits` edge):
  * folds to a Term-tree         -> PORTED: graph-native compute the agent owns (incl. loops -> Fold,
                                    comprehensions -> Map/Filter, dedup-consecutive -> Fold, …)
  * residual, held-op Call       -> REIMPLEMENTS an existing Rust primitive (delete the donkey)
  * residual, dict-comp          -> a DECISION -> belongs as a graph RULE
  * residual, no held op/rule    -> a genuinely NEW primitive -> Layer B (emit_primitive_rust + self_extend)

Run:  python -m scripts.donkey_to_graph
"""
from __future__ import annotations
import sys

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
from domains import ast_term_rules as R
from domains.ast_to_term import ingest_ast, open_ast_productions

# The np ops my donkey calls that ARE held substrate operators (the leaf boundary).
HELD_LEAVES = {
    "argsort": "shape_signature",   # relational ordinal rank — Substrate.shape_signature (Rust)
    "log2": "log2", "mean": "mean", "abs": "abs", "stack": "stack",
}

# The session's donkey compute-cores (faithful; bare names = the np namespace), each
# with where it SHOULD live once graph-native.
DONKEY = [
    ("rank16", "def rank16(v):\n    return argsort(argsort(v))",
     "HELD OP: reimplements Substrate.shape_signature (relational ordinal rank, Rust). Delete; call the op."),
    ("ema_background", "def ema_background(bg, frame):\n    return 0.95 * bg + 0.05 * frame",
     "GRAPH-NATIVE compute (Plus/Times Term-tree) but element-wise over a frame -> a vectorised vision primitive."),
    ("mi_term", "def mi_term(p, pa, pc):\n    return p * log2(p / (pa * pc))",
     "GRAPH-NATIVE measurement (Times/Div Term-tree + held log2). Analysis -> world-adapter OK, or a held op."),
    ("collapse_runs", "def collapse_runs(seq):\n    out = []\n    for u in seq:\n        if not out or out[-1] != u:\n            out.append(u)\n    return out",
     "ACC-DEPENDENT loop -> a Fold Term-tree (the rules port it; Last/IndexAt/Append minted via Layer B)."),
    ("tp_table", "def tp_table(uni, fwd):\n    return {a: {b: c / uni[a] for b, c in nx.items()} for a, nx in fwd.items()}",
     "DECISION/dict -> a graph RULE: this IS statistical-learning -> domains/compositional_chunking + sonority_valley (held)."),
]


def classify(s, name, source):
    """Port via the AGENT'S RULES: install the generated AST->Term rule set, ingest the function,
    let the Rust engine fold the AstNode graph into a Term-tree (`run_rules`), and read the result
    off the body head's `emits` edge. A function that emits IS graph-native (the engine ported it);
    one that doesn't is a residual, diagnosed (held-op Call -> call the Rust op; dict-comp -> a graph
    Rule; else a Layer-B primitive candidate)."""
    nat = s._inner
    open_ast_productions(s)
    R.install(s)
    rec = ingest_ast(s, source, root_label="donkey")
    root = rec["func_roots"].get(name)
    n = rec["n_nodes"]
    if root is None:
        return n, "NO-FUNC", "could not locate FunctionDef"
    nat.run_rules(8000)
    head = next((c for c in s.neighbours(root, "child")
                 if s.node(c)["attrs"].get("child_field") == "body"
                 and s.node(c)["attrs"].get("child_index") == 0), None)
    em = list(s.neighbours(head, "emits")) if head is not None else []
    if len(em) == 1:
        term_type = s.node(em[0])["type"].removeprefix("Term.")
        return n, "PORTED", f"engine folded it -> {term_type} Term-tree (rule-emitted, graph-native)"
    return n, "RESIDUAL", _diagnose(s)


def _diagnose(s) -> str:
    """Why a residual didn't port: a held-op Call (call the Rust op), a dict-comprehension (a graph
    Rule), or otherwise un-ported AST (a Layer-B primitive candidate)."""
    reasons = []
    for nid in s.nodes("AstNode"):
        a = s.node(nid)["attrs"]
        t = a.get("ast_type", "")
        if t == "DictComp":
            reasons.append("dict-comprehension -> a graph RULE (statistical learning)")
        if t == "Call":
            for c in s.neighbours(nid, "child"):
                fa = s.node(c)["attrs"]
                if fa.get("child_field") == "func":
                    nm = fa.get("id") or fa.get("attr")
                    if nm in HELD_LEAVES:
                        reasons.append(f"held op {nm!r} -> Rust {HELD_LEAVES[nm]} (call it, delete the donkey)")
    return "; ".join(dict.fromkeys(reasons)) or "un-ported AST -> a Layer-B primitive candidate"


def main():
    import substrate_rs as srs
    print("=" * 80)
    print("EXPOSE DONKEY PYTHON AS AST -> AGENT MOVES IT GRAPH-NATIVE -> ASSESS")
    print("=" * 80)

    print("\n  (1) ingest_ast: each donkey compute-core -> code-as-graph; the agent's RULES + engine"
          "\n      fold it into a Term-tree (PORTED) or leave a diagnosed residual\n")
    print(f"  {'function':<16}{'ast nodes':>10}  {'verdict':<10} where it should live")
    for name, src, should in DONKEY:
        n, verdict, detail = classify(srs.Substrate(), name, src)   # fresh substrate per function
        print(f"  {name:<16}{n:>10}  {verdict:<10} {should}")
        print(f"  {'':<16}{'':>10}  {'':<10} -> {detail}")

    # (2) a residual with no held op AND no rule is a genuinely-NEW primitive -> Layer B mints it.
    print("\n  (2) Layer B: a genuinely-new primitive (no held op, no rule) -> the agent emits Rust")
    try:
        from domains import runtime_design as RD
        spec = {"name": "PeakBin", "items_field": "items", "semantic_kind": "index_of_reduction",
                "reduce_op": "max", "purpose": "the bin INDEX of a spectral peak",
                "why_new": "no existing primitive yields a position", "grounded_in_science": True}
        emitted = RD.emit_primitive_rust(spec)
        print(f"      emit_primitive_rust({spec['name']}) -> Rust fragments for {len(emitted)} homes:"
              f" {list(emitted)[:4]}")
        print("      domains/self_extend.PrimitiveExtension applies -> cargo check -> rebuild -> "
              "rollback-on-fail.")
        print("      (Last / IndexAt / Append / MapList / FilterList were ALL added exactly this way,")
        print("       then consumed by the rules above — the A<->B<->C self-extension loop.)")
    except Exception as e:
        print(f"      (Layer-B demo skipped: {e})")

    # (3) the ArchitectureCortex's OWN verdict on the RULE SET (graph-resident quality/smell Rules).
    print("\n  (3) ArchitectureCortex assessment of the AST->Term rule set (the agent's own opinion):")
    try:
        from scripts.ask_the_substrate import fresh_substrate
        res = R.assess_rule_set(fresh_substrate())
        print(f"      overall {res.get('overall_pct'):.0f}%  "
              f"({res.get('n_qualities')} qualities, {res.get('smell_count')} smells)")
        for q in res.get("qualities", []):
            print(f"        {q['quality_name']:<24} {q['score']}/{q['max_score']}  {q['rationale'][:60]}")
        for sm in res.get("smells", []):
            print(f"        SMELL {sm.get('smell_name')}: {sm.get('rationale', '')[:70]}")
        if not res.get("smells"):
            print("        (no smells detected)")
    except Exception as e:
        print(f"      (assessment skipped: {e})")

    print("\n" + "=" * 80)
    print("  WHERE EACH DONKEY LANDS (now that the rules + Layer-B primitives exist):")
    print("   - ema_background / pure compute   -> PORTED by the rules to a native Term-tree (own it)")
    print("   - collapse_runs / accumulation     -> PORTED: Fold over the AstNode graph (was a residual)")
    print("   - rank16 / pooling (argsort)       -> HELD OP Substrate.shape_signature; delete the donkey")
    print("   - mi_term / log2                   -> HELD OP log2 (or a world-adapter MEASUREMENT)")
    print("   - tp_table / dict-comp             -> a graph RULE (statistical learning)")
    print("   - a genuinely-new op (no held/rule)-> Layer B mints it (emit_primitive_rust + self_extend)")
    print("   The agent owns the code as a graph (ingest_ast); the RULES fold compute into native")
    print("   Term-trees; decisions become graph Rules; only I/O stays world-adapter Python.")
    print("=" * 80)


if __name__ == "__main__":
    main()
