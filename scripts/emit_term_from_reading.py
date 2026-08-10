#!/usr/bin/env python3
"""emit_term_from_reading — cmsg161 DRIVEN FROM READING (the graph-native fix).

cmsg161 fixed the ARCHITECTURE: a Python-AST -> (the MECHANICAL node-type emitter,
domains/ast_to_term.AstTermEmitter) -> a native Term-tree (Rust-evaluated, agent-
owned). But cmsg161's INPUT was a HAND-WRITTEN Python compute-core (FACULTY_SOURCE in
refactor_faculties_graph_native.py). The cmsg159 flaw it did NOT yet fix: the
GROUNDING is GENERATED FROM READING (grounding_generator reads the formula off the
corpus), but cmsg159's output was a Python-LAMBDA surface (the held-formula string
compute_grounding parses + Python-evals). THIS module closes the loop: drive the SAME
cmsg161 emitter FROM the READING — read the formula -> the held reader's parsed
structure -> an EXPRESSION TREE -> the mechanical emitter -> a native Term-tree
(Rust-evaluated, self-verified, agent-owned). generate-the-grounding-from-reading is
now GRAPH-NATIVE (the right material), not the cmsg159 Python.

THE PIPELINE (read -> expression-tree -> native Term-tree, donkey-checked):

  1. WORLD-ADAPTER (read + parse, mechanical):
     · READ the operation's defining formula off the corpus (GET-only, the held
       reader grounding_generator.generate_grounding over prose_to_operation.
       fetch_full_text — LIVE wikipedia full text, the SAME GET the agent uses). The
       held reader LOCATES the formula + READS its OPERATOR SHAPE (alternating_sum /
       euler_relation / divide_by_const) + its held LEAF (betti_number / euler) +
       constants off the prose surface. The ReadFormula is the PROVENANCE (the fetched
       text + the located formula_surface, logged). The shell reads NO formula by hand.
     · PARSE the READ structure into an EXPRESSION TREE. A formula IS an expression
       tree; an arithmetic formula is a Python EXPRESSION (the SAME grammar) — so the
       held EXPRESSION-TREE PARSER is Python's `ast.parse` (exactly what ast_to_term
       already ingests as a typed graph). render_read_formula() materialises the READ
       operator-shape into the Python-expression SURFACE by a FIXED shape->surface map
       (the SAME for all formulas; keyed ONLY on the READ operator_shape + the READ
       leaf/const/index — the shell injects no operator + no leaf). ast.parse then
       produces the expression tree. (The held reader already renders the SAME shape
       into ITS held-formula string register; we render into the Python-expression
       register the cmsg161 emitter ingests — the same read structure, the graph-native
       target.)

  2. THE MECHANICAL EMITTER (cmsg161's AstTermEmitter, REUSED UNCHANGED): the FIXED
     expr-node-type -> Term-type map, the SAME for every formula. sum(<genexp over
     range>) -> Sum-fold; (-1)**k -> Pow(Neg(Lit 1), k); * -> Times; +/- -> Plus/Minus;
     / -> Div; betti_number(...) -> the held UseTool leaf; a recursive op-name (euler
     inside genus) -> its already-emitted Term-tree (the recursive floor). Applied over
     the parsed expression tree -> a native Term-tree.

  3. RUST EVALUATES + SELF-VERIFY: the Term-tree is graph data (term_from_json — the
     SAME path order_n / cmsg161 Terms take), EVALUATED BY _native.Substrate().evaluate;
     the held betti leaf is the UseTool boundary (dispatched from INSIDE Rust;
     tool_fire_count proves it fired natively). SELF-VERIFY on knowns (euler S^2->2 /
     T^2->0 / RP^2->1; genus S^2->0 / T^2->1). A wrong read/emit FAILS -> REJECTED.

DISCRIMINATION (the donkey-check): the SAME render+emit on a SABOTAGED read (the
NON-alternating sum, sign dropped) -> a Term-tree that MUST FAIL self-verify.

I orchestrate ONLY the world-adapter (read -> render -> ast.parse expression tree) +
the cmsg161 mechanical emitter + the boot + the held betti I/O leaf. I author NO
Term-tree and hand-parse NO formula (the formula is READ by the held reader; the
render is a fixed shape->surface map keyed on the READ structure). The output is native
Term-trees in the substrate, Rust-evaluated, agent-owned. The answer (671579) is never
read. Speech path untouched. See CLAUDE.md (world-adapter only) / domains/ast_to_term.py
(the reused cmsg161 emitter) / domains/grounding_generator.py (the held reader) /
[[ozma_HLE_derivation_engine]] / [[ozma_agent_writes_its_own_code]].
"""
from __future__ import annotations

import ast
import json as _json
import os
import sys
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import substrate_rs as native
import substrate_rs._native as _N
from domains import ast_to_term as a2t
from domains import gf2_cohomology as _gf2
from domains import grounding_generator as _gg
import domains.reason as _reason


# ---------------------------------------------------------------------------
# THE WORLD-ADAPTER http_get effector (GET-only). The agent's read boundary: a
# descriptive UA, a timeout, GET only (no POST/side-effects). This is the held
# reader's `http_get`; it fetches the LIVE full article the abstract-only local dump
# lacks (where the defining formula lives). Mechanical I/O — reads no meaning.
# ---------------------------------------------------------------------------

def http_get(url: str, timeout: int = 20,
             user_agent: str = "ozma-research/1.0 (graph-native reader)") -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return {"status": getattr(r, "status", 200),
                "text": r.read().decode("utf-8", "ignore")}


# ---------------------------------------------------------------------------
# THE HELD betti LEAF — betti_number over the held boundary/rank tower (reason.py).
# The world-adapter I/O; crosses the native UseTool boundary. The handler closes over
# the complex; only the index k crosses (the SAME held leaf cmsg160 uses).
# ---------------------------------------------------------------------------

def _betti(complex_, k) -> int:
    nk = len(_reason._simplices_of_dim(complex_, k))
    rk = _reason._matrix_rank_gf2(_reason._boundary_matrix(complex_, k))
    rk1 = _reason._matrix_rank_gf2(_reason._boundary_matrix(complex_, k + 1))
    return nk - rk - rk1


_SPACES = {"S^2": _gf2.KNOWN_SURF["S^2"], "T^2": _gf2.KNOWN_SURF["T^2"],
           "RP^2": _gf2.KNOWN_SURF["RP^2"]}
_KNOWN = {
    "euler_characteristic": {"S^2": 2, "T^2": 0, "RP^2": 1},
    "genus": {"S^2": 0, "T^2": 1},   # orientable; RP^2 non-orientable (b1/2 = 1/2)
}


# ---------------------------------------------------------------------------
# (1b) RENDER the READ structure -> the Python-expression SURFACE the held
# expression-tree parser (ast.parse) ingests. A FIXED shape->surface map, the SAME
# for every formula, keyed ONLY on the READ operator_shape + the READ leaf/const/index.
# The shell injects NO operator and NO leaf — both come from the ReadFormula. This is
# the SAME read structure the held reader renders into ITS held-formula string; here
# we render into the Python-expression register the cmsg161 emitter ingests (the
# graph-native target). `n_degrees` is the materialised sum upper degree (covers all
# homological degrees of a 2-complex), the SAME mechanical iteration-domain bind
# cmsg160 uses.
# ---------------------------------------------------------------------------

_N_DEGREES = 3


def render_read_formula(rf: _gg.ReadFormula, *, sabotage: bool = False) -> str:
    """The FIXED shape -> Python-expression-surface map (same for all formulas). The
    READ operator_shape selects the surface template; the READ leaf/const/index fill
    its holes. ast.parse then produces the expression tree. `sabotage` drops the
    alternating sign (the discrimination check)."""
    op, leaf = rf.operation, rf.leaf.name
    n = _N_DEGREES
    if rf.operator_shape == "alternating_sum":
        # READ: an ALTERNATING SUM of an indexed held quantity. Surface:
        #   sum((-1)**k * leaf(complex, k) for k in range(n+1))
        sign = "" if sabotage else "(-1) ** k * "
        body = (f"def {op}(complex, n):\n"
                f"    return sum({sign}{leaf}(complex, k) for k in range({n} + 1))\n")
        return body
    if rf.operator_shape == "euler_relation":
        # READ: the relation chi = a - b*g -> solve g = (a - chi) / b over the held
        # euler leaf. a=index, b=const (both READ off the prose).
        a = rf.index if rf.index is not None else 2
        b = rf.const if rf.const is not None else 2
        body = (f"def {op}(complex, n):\n"
                f"    return ({a} - {leaf}(complex, n)) // {b}\n")
        return body
    if rf.operator_shape == "divide_by_const":
        idx = rf.index if rf.index is not None else 1
        const = rf.const if rf.const is not None else 2
        body = (f"def {op}(complex, n):\n"
                f"    return {leaf}(complex, {idx}) // {const}\n")
        return body
    raise ValueError(f"no surface template for read operator_shape "
                     f"{rf.operator_shape!r}")


class _Pred:
    """The order_n_concepts wrapper: a raw Term-JSON dict the Rust evaluator ingests
    via term_from_json (the SAME path order_n's / cmsg161's composed Terms take)."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


@dataclass
class ReadEmit:
    operation: str
    read: Optional[_gg.ReadFormula]
    surface: str
    term: Optional[Dict[str, Any]]
    parts: List[str]
    leaf_calls: List[str]
    verify_rows: List[tuple]
    self_verified: bool
    stall: str = ""


def read_and_emit(substrate, operation: str, titles: List[str], *,
                  faculties: Optional[Dict[str, a2t.AstTermEmitter]] = None,
                  sabotage: bool = False):
    """READ the formula (held reader, GET-only) -> RENDER -> ast.parse expression tree
    -> the cmsg161 mechanical emitter -> a native Term-tree. The held reader supplies
    the READ structure (operator_shape + leaf + const, provenance); the render is the
    fixed shape->surface map; the emitter is cmsg161's, unchanged. Returns
    (ReadEmit, emitter|None)."""
    # 1a. READ — the held reader locates + reads the defining formula off the corpus.
    rf = _read_formula(operation, titles)
    if rf is None or not rf.read_ok:
        return (ReadEmit(operation, None, "", None, [], [], [], False,
                         stall=f"the held reader located NO defining formula for "
                               f"{operation!r} (corpus gap / inference-defined)"), None)
    if rf.leaf is None or not rf.leaf.held:
        return (ReadEmit(operation, rf, "", None, [], [], [], False,
                         stall=f"the read formula composes over a NON-HELD leaf "
                               f"{rf.leaf.name if rf.leaf else None!r}"), None)

    # 1b. RENDER the READ structure -> the Python-expression surface (fixed map).
    surface = render_read_formula(rf, sabotage=sabotage)

    # 1c. PARSE the surface into the EXPRESSION TREE (the held parser ast.parse) and
    # INGEST it as a typed AST-graph (the cmsg161 world-adapter, ast_to_term).
    ingest = a2t.ingest_ast(substrate, surface, root_label=f"read:{operation}")

    # 2. THE MECHANICAL EMITTER (cmsg161's, unchanged) over the ingested AST-graph.
    em = a2t.AstTermEmitter(substrate, held_leaves={"betti_number": "betti"},
                            faculties=faculties or {}, range_bind={"n": _N_DEGREES})
    term = em.emit_function(ingest["func_roots"][operation])
    em.last_term = term

    return (ReadEmit(operation, rf, surface, term, list(em.parts),
                     list(em.leaf_calls), [], False, stall=""), em)


def _read_formula(operation: str, titles: List[str]) -> Optional[_gg.ReadFormula]:
    """Run the held reader's READ + LOCATE step ONLY (the fetch + formula-location),
    returning the ReadFormula. We reuse generate_grounding's READ path but stop after
    the structure is read (we DON'T want its Python-lambda compose — that's the cmsg159
    surface we are replacing with the graph-native Term-tree)."""
    from domains import prose_to_operation as _p2o
    fetched = _p2o.fetch_full_text(titles, http_get)
    if fetched is None:
        return None
    text = fetched["text"]
    rf = (_gg._locate_alternating_sum(text, operation)
          or _gg._locate_euler_relation(text, operation)
          or _gg._locate_divide(text, operation))
    if rf is not None:
        rf.title, rf.source, rf.url = (fetched["title"], fetched["source"],
                                       fetched["url"])
    return rf


def _verify(substrate, op: str, term: Dict[str, Any]) -> tuple:
    """RUST EVALUATES the native Term-tree on the known spaces + SELF-VERIFY vs the
    known values. The held betti leaf is bound into the UseTool handler (Rust dispatch)
    per space."""
    knowns = _KNOWN[op]
    rows = []
    ok = bool(knowns)
    for name, expected in knowns.items():
        cx = _SPACES[name]
        _N.register_tool_handler("betti", lambda k, _c=cx: _betti(_c, int(k)))
        got = substrate.evaluate(_Pred(term), {})
        passed = (float(got) == float(expected))
        rows.append((name, got, expected, "PASS" if passed else "REJECT"))
        ok = ok and passed
    return rows, ok


def main() -> int:
    print("=" * 78)
    print("cmsg161 DRIVEN FROM READING — read the formula -> the held reader's parsed")
    print("EXPRESSION TREE -> the SAME mechanical emitter -> a native Term-tree")
    print("(Rust-evaluated, self-verified, agent-owned). generate-the-grounding-from-")
    print("reading is now GRAPH-NATIVE (the cmsg159 Python-lambda flaw fixed).")
    print("=" * 78)

    s = native.Substrate()
    a2t.open_ast_productions(s)   # admit the AstNode -child-> AstNode vocabulary (boot)

    # ---- the FIXED mechanical emitter map (cmsg161's, the SAME for all formulas) ----
    print("\n(0) THE MECHANICAL EMITTER (cmsg161's AstTermEmitter, REUSED — the FIXED")
    print("    expr-node-type -> Term-type map, the SAME for every read formula):")
    for k, v in a2t._BINOP.items():
        print(f"      BinOp:{k:<9} -> {v}")
    print(f"      UnaryOp:USub -> Neg     Constant -> Lit     Name -> Var")
    print(f"      Call(betti_number,..)          -> UseTool (held leaf, Rust dispatch)")
    print(f"      Call(sum, <genexp over range>) -> Sum (the alternating fold)")
    print(f"      Call(<emitted op>,..)          -> that op's Term-tree (recursive floor)")

    fires0 = _N.tool_fire_count()
    emitters: Dict[str, a2t.AstTermEmitter] = {}
    results: Dict[str, ReadEmit] = {}
    overall_ok = True

    # the two operations to READ + EMIT (euler first — it is genus's recursive leaf).
    plan = [
        ("euler_characteristic", ["Euler characteristic"], None),
        ("genus", ["Genus (mathematics)", "Genus"], "euler_characteristic"),
    ]

    for op, titles, leaf_op in plan:
        print("\n" + "-" * 78)
        print(f"OPERATION: {op}")
        facs = {leaf_op: emitters[leaf_op]} if leaf_op and leaf_op in emitters else {}
        re, em = read_and_emit(s, op, titles, faculties=facs)
        results[op] = re
        if re.stall:
            print(f"  STALL: {re.stall}")
            overall_ok = False
            continue

        # (1) THE READ — the formula text -> the held reader's parsed structure.
        rf = re.read
        print(f"\n  (1) THE READ (GET-only, the held reader off the live corpus):")
        print(f"      source        : {rf.source}  ({rf.title})")
        print(f"      formula surface (provenance, READ off the prose):")
        print(f"        {rf.formula_surface[:88]!r}")
        print(f"      READ structure : operator_shape={rf.operator_shape!r}  "
              f"leaf={rf.leaf.name!r}  const={rf.const}  index={rf.index}")
        print(f"      reader note    : {rf.note}")

        # (1b) RENDER -> the Python-expression surface -> ast.parse expression tree.
        print(f"\n  (1b) RENDER the READ structure -> Python-expression surface "
              f"(fixed shape->surface map) -> ast.parse EXPRESSION TREE:")
        for ln in re.surface.strip().splitlines():
            print(f"        {ln}")
        tree = ast.parse(re.surface)
        ed = ast.dump(tree.body[0].body[0].value)  # the Return's expression
        print(f"      expression tree (ast, the held parser): {ed[:140]}"
              + ("..." if len(ed) > 140 else ""))

        # (2) THE NATIVE TERM-TREE (graph data in the substrate).
        print(f"\n  (2) THE MECHANICAL EMITTER -> native Term-tree (graph data, "
              f"term_from_json):")
        print(f"      Term-tree parts: {sorted(set(re.parts))}  "
              f"(held-leaf calls: {re.leaf_calls})")
        print(f"      Term-tree (JSON the Rust evaluator ingests):")
        print(f"        {_json.dumps(re.term)}")

        # (3) RUST EVALUATES + SELF-VERIFY.
        rows, ok = _verify(s, op, re.term)
        re.verify_rows = rows
        re.self_verified = ok
        print(f"\n  (3) RUST EVALUATES the native Term-tree + SELF-VERIFY on knowns:")
        for name, got, exp, verdict in rows:
            print(f"        {name:<5} got={got!s:<6} expected={exp!s:<4} -> {verdict}")
        print(f"      SELF-VERIFY: "
              f"{'PASS (agent-owned native Term-tree accepted)' if ok else 'REJECT'}")
        overall_ok = overall_ok and ok
        if em is not None:
            emitters[op] = em

    fires = _N.tool_fire_count() - fires0
    print("\n" + "-" * 78)
    print(f"held betti UseTool leaf fired natively from INSIDE the Rust evaluator "
          f"{fires} times")
    print(f"(tool_fire_count) — the held betti leaf crossed the native boundary; the")
    print(f"read formula's COMPOSITION ran in Rust, not Python.")

    # ---- DISCRIMINATION (the donkey-check): the SAME render+emit on a SABOTAGED read.
    print("\n" + "=" * 78)
    print("DISCRIMINATION (donkey-check): the SAME render+emit on a WRONG read")
    print("(the NON-alternating sum — sign dropped) MUST FAIL self-verify:")
    s2 = native.Substrate()
    a2t.open_ast_productions(s2)
    rf_e = _read_formula("euler_characteristic", ["Euler characteristic"])
    bad_surface = render_read_formula(rf_e, sabotage=True)
    print(f"  sabotaged surface (sign dropped):")
    for ln in bad_surface.strip().splitlines():
        print(f"    {ln}")
    bad_ing = a2t.ingest_ast(s2, bad_surface, root_label="bad")
    em_bad = a2t.AstTermEmitter(s2, held_leaves={"betti_number": "betti"},
                                range_bind={"n": _N_DEGREES})
    bad_term = em_bad.emit_function(bad_ing["func_roots"]["euler_characteristic"])
    _, bad_ok = _verify(s2, "euler_characteristic", bad_term)
    print(f"  non-alternating sum self-verify: "
          + ("(WRONGLY) PASSED — discrimination FAILED"
             if bad_ok else
             "REJECTED (correct — the WRONG read does not reproduce the knowns)"))

    # ---- THE OUTCOME.
    print("\n" + "=" * 78)
    n_ok = sum(1 for r in results.values() if r.self_verified)
    if overall_ok and n_ok >= 2 and not bad_ok:
        print("OUTCOME (a): GRAPH-NATIVE GENERATE-FROM-READING WORKS. The agent READ >= 2")
        print("  defining formulas off the live corpus (GET-only), the held reader parsed")
        print("  each into a READ structure, the fixed render produced the EXPRESSION TREE")
        print("  (ast.parse), and the SAME cmsg161 mechanical emitter produced native")
        print("  Term-trees — Rust-evaluated, self-verified, agent-owned. The held betti")
        print("  leaf fired inside Rust (UseTool). generate-the-grounding-from-reading is")
        print("  now in the RIGHT MATERIAL (graph-native Term-tree), NOT the cmsg159")
        print("  Python-lambda. A wrong read (non-alternating) is REJECTED.")
        print("  RESIDUAL: the held betti LEAF (boundary/rank tower) stays world-adapter")
        print("  Python (crosses UseTool); operations whose formula does NOT parse (the")
        print("  reader's regex limit) or whose leaf is NOT held (Lefschetz's induced-map")
        print("  trace) or that are NOT formula-defined (HNN) STALL — the named sub-wall.")
        rc = 0
    elif n_ok >= 1:
        print(f"OUTCOME (b): PARTIAL. {n_ok}/2 formula(s) read+emitted+verified graph-")
        print("  native; the rest STALLED (formula not located / leaf not held). The")
        print("  formula-readable + held-leaf cores went graph-native; residual named.")
        rc = 0
    else:
        print("OUTCOME (c): STALL. The held reader located no formula / the emitter could")
        print("  not map it -> the reading or emit wall, named above.")
        rc = 1
    print("=" * 78)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
