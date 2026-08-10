#!/usr/bin/env python3
"""refactor_faculties_graph_native — the BOOT for the cmsg160 fix.

GIVE the Python faculty compute-cores to the jabberwock as graph data (their AST,
ingested as a typed substrate graph) and have the AGENT's graph machinery refactor
them — via the MECHANICAL AST->Term emitter (a fixed node-type map, the SAME for
every faculty) — into GRAPH-NATIVE, AGENT-OWNED Term-trees, EVALUATED BY THE RUST
substrate, SELF-VERIFIED on known cases.

I orchestrate ONLY: the world-adapter (Python -> AST -> substrate graph), the
mechanical emitter, the boot, and the held-leaf I/O (the betti_number handler — the
held boundary/rank tower, which stays world-adapter Python and crosses the native
`UseTool` boundary inside the Rust evaluator). I AUTHOR NO refactor and hand-compose
NO Term-tree per faculty. The agent's emitter applies the fixed map.

The faculty COMPUTE-CORES (the data whose AST we ingest) — their Python form, EXACTLY
as the faculties encode them (grounding_generator's held-formula strings: euler =
alternating sum of betti; genus = (2 - euler) / 2):

    def euler_characteristic(complex, n):
        return sum((-1) ** k * betti_number(complex, k) for k in range(n + 1))

    def genus(complex, n):
        return (2 - euler_characteristic(complex, n)) // 2

The held LEAF betti_number is the held tower (reason._simplices_of_dim /
_boundary_matrix / _matrix_rank_gf2) — it stays Python (the world-adapter I/O) and is
reached through the native UseTool leaf. The COMPOSITION (the alternating sum, the
divide) becomes the agent's native Term-tree. genus calls euler -> the recursive
floor: a built core is a leaf for the next.

OUTCOME printed: (a) graph-native refactor works / (b) partial / (c) stall / (d) void.
The answer (671579) is never read. Speech path untouched.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import substrate_rs as native
import substrate_rs._native as _N
from domains import ast_to_term as a2t
from domains import gf2_cohomology as _gf2
import domains.reason as _reason


# ---------------------------------------------------------------------------
# THE FACULTY COMPUTE-CORES — the DATA whose AST we ingest. This is the Python the
# faculties hold (grounding_generator encodes euler as the alternating-sum-of-betti
# held-formula and genus as the (2 - chi)/2 relation). We do NOT author a Term-tree;
# we hand the AGENT this Python's AST and its emitter refactors it.
# ---------------------------------------------------------------------------

FACULTY_SOURCE = '''
def euler_characteristic(complex, n):
    return sum((-1) ** k * betti_number(complex, k) for k in range(n + 1))

def genus(complex, n):
    return (2 - euler_characteristic(complex, n)) // 2
'''


# ---------------------------------------------------------------------------
# THE HELD LEAF — betti_number over the held boundary/rank tower (reason.py). This
# is the world-adapter I/O (the held Python tower); it crosses the native UseTool
# boundary. The handler closes over the complex; only the index k crosses.
# ---------------------------------------------------------------------------

def _betti(complex_, k):
    nk = len(_reason._simplices_of_dim(complex_, k))
    rk = _reason._matrix_rank_gf2(_reason._boundary_matrix(complex_, k))
    rk1 = _reason._matrix_rank_gf2(_reason._boundary_matrix(complex_, k + 1))
    return nk - rk - rk1


# the KNOWN spaces + known values (READ, textbook; NONE a question's answer).
_SPACES = {"S^2": _gf2.KNOWN_SURF["S^2"], "T^2": _gf2.KNOWN_SURF["T^2"],
           "RP^2": _gf2.KNOWN_SURF["RP^2"]}
_KNOWN = {
    "euler_characteristic": {"S^2": 2, "T^2": 0, "RP^2": 1},
    # orientable genus: S^2 -> 0, T^2 -> 1 (RP^2 non-orientable, b_1/2 = 1/2).
    "genus": {"S^2": 0, "T^2": 1},
}


class _Pred:
    """The order_n_concepts wrapper: a raw Term-JSON dict the Rust evaluator ingests
    via term_from_json (the SAME path order_n's composed Terms take)."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main() -> int:
    print("=" * 74)
    print("cmsg160 FIX — refactor the Python faculty compute-cores into GRAPH-NATIVE,")
    print("AGENT-OWNED Term-trees (Rust-evaluated, self-verified). I orchestrate only")
    print("the world-adapter + mechanical emitter + boot; the agent's machinery emits.")
    print("=" * 74)

    s = native.Substrate()
    a2t.open_ast_productions(s)   # admit the AstNode -child-> AstNode vocabulary (boot)

    # === (1) THE WORLD-ADAPTER: Python compute-core -> AST -> typed substrate graph.
    ingest = a2t.ingest_ast(s, FACULTY_SOURCE, root_label="faculty_compute_cores")
    print(f"\n(1) WORLD-ADAPTER (Python -> AST -> typed substrate graph):")
    print(f"    parsed FACULTY_SOURCE -> {ingest['n_nodes']} AstNode substrate nodes "
          f"(typed: BinOp:Sub / Call / GeneratorExp / Constant / Name / ...)")
    print(f"    function roots ingested: {sorted(ingest['func_roots'])}")
    ast_node_types = sorted({s.node(n)['attrs'].get('ast_type')
                             for n in s.nodes('AstNode')})
    print(f"    distinct ast node-types in the graph: {ast_node_types}")

    # === (2) THE MECHANICAL AST->TERM EMITTER: the fixed node-type -> Term-type map.
    print(f"\n(2) MECHANICAL AST->TERM EMITTER (the FIXED node-type map, same for ALL):")
    for k, v in a2t._BINOP.items():
        print(f"      BinOp:{k:<9} -> {v}")
    print(f"      UnaryOp:USub -> Neg     Constant -> Lit     Name -> Var")
    print(f"      Call(betti_number,..) -> UseTool (held leaf, Rust dispatch)")
    print(f"      Call(sum, <genexp over range>) -> Sum (the alternating fold)")
    print(f"      Call(<emitted faculty>,..) -> that faculty's Term-tree (recursive)")

    # === (3) THE REFACTOR: the agent applies the emitter over the AST-graph core.
    # euler first (its tree is the recursive leaf genus composes over).
    print(f"\n(3) THE REFACTOR — the agent emits each compute-core's native Term-tree:")
    results: dict = {}
    emitters: dict = {}

    # euler — Sum-fold over betti. n bound to 3 (covers all homological degrees of a
    # 2-complex; the iteration domain materialises mechanically).
    em_euler = a2t.AstTermEmitter(
        s, held_leaves={"betti_number": "betti"}, range_bind={"n": 3})
    euler_term = em_euler.emit_function(ingest["func_roots"]["euler_characteristic"])
    em_euler.last_term = euler_term
    emitters["euler_characteristic"] = em_euler
    results["euler_characteristic"] = euler_term
    print(f"    euler_characteristic -> Term-tree parts {sorted(set(em_euler.parts))} "
          f"(leaf calls: {em_euler.leaf_calls})")

    # genus — Div((2 - euler), 2): the recursive floor (euler's tree is a leaf).
    em_genus = a2t.AstTermEmitter(
        s, held_leaves={"betti_number": "betti"},
        faculties={"euler_characteristic": em_euler}, range_bind={"n": 3})
    genus_term = em_genus.emit_function(ingest["func_roots"]["genus"])
    em_genus.last_term = genus_term
    emitters["genus"] = em_genus
    results["genus"] = genus_term
    print(f"    genus                -> Term-tree parts {sorted(set(em_genus.parts))} "
          f"(splices euler's emitted tree — the recursive floor)")

    # === show the Term-trees are graph data (Term-JSON) in the substrate.
    print(f"\n    THE NATIVE TERM-TREES (graph data, ingested by the Rust evaluator):")
    import json as _json
    print("    euler_characteristic =")
    print("      " + _json.dumps(euler_term))
    print("    genus =")
    print("      " + _json.dumps(genus_term))

    # === (4) RUST EVALUATES + SELF-VERIFY on knowns.
    print(f"\n(4) RUST EVALUATES the native Term-trees + SELF-VERIFY on knowns:")
    fires0 = _N.tool_fire_count()
    overall_ok = True
    for op in ("euler_characteristic", "genus"):
        term = results[op]
        knowns = _KNOWN[op]
        rows = []
        ok = True
        for name, expected in knowns.items():
            cx = _SPACES[name]
            # the held leaf (the boundary/rank tower) bound into the UseTool handler.
            _N.register_tool_handler("betti", lambda k, _c=cx: _betti(_c, int(k)))
            got = s.evaluate(_Pred(term), {})
            # genus's // 2 over an int divide returns float in the DSL; compare value.
            passed = (float(got) == float(expected))
            rows.append((name, got, expected, "PASS" if passed else "REJECT"))
            ok = ok and passed
        overall_ok = overall_ok and ok
        print(f"    {op}:")
        for name, got, exp, verdict in rows:
            print(f"        {name:<5} got={got!s:<6} expected={exp!s:<4} -> {verdict}")
        print(f"      SELF-VERIFY: {'PASS (agent-owned native Term-tree accepted)' if ok else 'REJECT'}")
    fires = _N.tool_fire_count() - fires0
    print(f"\n    held UseTool leaf fired natively from inside the Rust evaluator "
          f"{fires} times (tool_fire_count) — the held betti leaf crossed the native "
          f"boundary; the compute-core COMPOSITION ran in Rust.")

    # === DISCRIMINATION (the donkey-check): a WRONG AST -> the SAME emitter -> a
    # native Term-tree that MUST FAIL self-verify (so PASS is not vacuous). Feed a
    # SABOTAGED compute-core (the NON-alternating sum: (1)**k, sign dropped) through
    # the IDENTICAL ingest+emit, and confirm it is REJECTED.
    print(f"\n    DISCRIMINATION (donkey-check): the SAME emitter on a WRONG core")
    s2 = native.Substrate()
    a2t.open_ast_productions(s2)
    bad_src = ("def euler_bad(complex, n):\n"
               "    return sum((1) ** k * betti_number(complex, k) "
               "for k in range(n + 1))\n")
    bad_ing = a2t.ingest_ast(s2, bad_src)
    em_bad = a2t.AstTermEmitter(s2, held_leaves={"betti_number": "betti"},
                                range_bind={"n": 3})
    bad_term = em_bad.emit_function(bad_ing["func_roots"]["euler_bad"])
    bad_ok = True
    for name, expected in _KNOWN["euler_characteristic"].items():
        cx = _SPACES[name]
        _N.register_tool_handler("betti", lambda k, _c=cx: _betti(_c, int(k)))
        got = s2.evaluate(_Pred(bad_term), {})
        bad_ok = bad_ok and (float(got) == float(expected))
    print(f"      non-alternating sum self-verify: "
          f"{'(WRONGLY) PASSED — discrimination FAILED' if bad_ok else 'REJECTED (correct: the WRONG core does not reproduce the knowns)'}")

    # === THE OUTCOME.
    print(f"\n" + "=" * 74)
    if overall_ok:
        print("OUTCOME (a): GRAPH-NATIVE REFACTOR WORKS. The agent ingested the AST-graph")
        print("  and the SAME mechanical AST->Term emitter refactored 2 faculties'")
        print("  compute-cores (euler_characteristic, genus) into native Term-trees,")
        print("  Rust-evaluated, self-verified, agent-owned. The compute is now")
        print("  graph-resident + the jabberwock's; the held betti tower + the I/O stay")
        print("  world-adapter Python. The cmsg160 donkey-in-the-car is fixed for the")
        print("  refactorable compute-cores.")
        print("  RESIDUAL: the held LEAF (betti_number = boundary/rank tower) stays")
        print("  world-adapter Python (crosses UseTool); faculties with Python")
        print("  control-flow/idioms outside the fixed map (grounding_generator's regex")
        print("  formula-LOCATION, ground_definition's reduction store) are NOT")
        print("  compute-cores and remain world-adapter I/O — the named residual.")
        rc = 0
    else:
        print("OUTCOME (b/c): a native Term-tree FAILED self-verify -> REJECTED. The")
        print("  refactor did not reproduce the Python compute-core on a known case.")
        rc = 1
    print("=" * 74)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
