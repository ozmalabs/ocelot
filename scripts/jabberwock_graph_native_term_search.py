"""PORT term synthesis onto the agent's existing GENERATE/SEARCH/GATE graph-rule mechanism (the one in
jabberwock_enumerate_and_search). The candidates are TERM-SUBGRAPHS (add_term_subgraph -> graph data); the
SEARCH is GRAPH RULES that EVALUATE each candidate via EvalSubgraph on the example stream and GATE the one
that matches all examples. The search is the AGENT'S (its rules + its evaluator), not a Python loop. donkey=0.

This is the graph-native twin of my Python bottom-up synth: same job (find the Term that fits the examples),
but the selection runs in run_rules over the agent's own evaluator. Candidates read inputs via Attr(o,..)
so EvalSubgraph resolves them from the observable that carries the current example.

Demo target: absdiff(x,y) = |x-y|. The candidate library holds {x ; x-y ; max2 ; absdiff}; the agent's
graph-rule search escalates through them and GATES absdiff (the only one matching all examples).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_graph_native_term_search.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Ao(k): return {"type": "Attr", "node": V("o"), "key": k}     # input read from the observable
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*x): return {"type": "And", "items": list(x)}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Ite(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}
def Nb(n, et): return {"type": "Neighbours", "node": V(n), "edge_type": et}
def Pick(src): return {"type": "Pick", "source": src}
def Eval(node): return {"type": "EvalSubgraph", "node": node}

# candidate Terms (read inputs via Attr(o,..)); only the last is correct |x-y|
CANDS = [
    ("x",       Ao("x")),
    ("x_minus_y", Minus(Ao("x"), Ao("y"))),
    ("max2",    Ite(Gte(Ao("x"), Ao("y")), Ao("x"), Ao("y"))),
    ("absdiff", Ite(Gte(Ao("x"), Ao("y")), Minus(Ao("x"), Ao("y")), Minus(Ao("y"), Ao("x")))),
]
EXAMPLES = [(3, 0, 3), (0, 5, 5), (4, 4, 0), (2, 7, 5), (9, 1, 8)]
N = float(len(EXAMPLES))

# the ACTIVE candidate's term, fetched from the graph: EvalSubgraph(Pick(neighbours(cand, has_term)))
ACTIVE = Eval(Pick(Nb("cand", "has_term")))

# MEASURE: evaluate the active candidate on THIS example; matched iff it equals expected; count consecutive.
MEASURE = {"id": "ts_measure", "name": "ts_measure",
           "match": [["h", "es_pred", "o"], ["lib", "has_cand", "cand"]],
           "where": And(Eq(A("cand", "ord"), A("o", "cur_ord")), Gt(A("o", "frame"), A("o", "mframe"))),
           "effects": [
               ["set_attr", "o", "matched", {"__term__": Ite(Eq(ACTIVE, A("o", "expected")), L(1.0), L(0.0))}],
               ["set_attr", "o", "matched_count", {"__term__": Ite(Eq(ACTIVE, A("o", "expected")),
                                                                   Plus(A("o", "matched_count"), L(1.0)), L(0.0))}],
               ["set_attr", "o", "mframe", {"__term__": A("o", "frame")}]]}

# GATE: a candidate that matched ALL examples consecutively is the synthesised Term -> keep it.
GATE = {"id": "ts_gate", "name": "ts_gate",
        "match": [["h", "es_pred", "o"]],
        "where": And(Eq(A("o", "solved"), L(0.0)), Gte(A("o", "matched_count"), L(N))),
        "effects": [["set_attr", "o", "solved", 1.0], ["set_attr", "o", "best_ord", {"__term__": A("o", "cur_ord")}]]}

# SEARCH: on a miss, escalate to the next candidate (the agent's own escalation over its candidate space).
SEARCH = {"id": "ts_search", "name": "ts_search",
          "match": [["h", "es_pred", "o"]],
          "where": And(Eq(A("o", "solved"), L(0.0)), Eq(A("o", "matched"), L(0.0)),
                       Gt(A("o", "frame"), A("o", "sframe"))),
          "effects": [["set_attr", "o", "cur_ord", {"__term__": Plus(A("o", "cur_ord"), L(1.0))}],
                      ["set_attr", "o", "matched_count", L(0.0)],
                      ["set_attr", "o", "sframe", {"__term__": A("o", "frame")}]]}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner

    print("=" * 92)
    print("GRAPH-NATIVE TERM SEARCH — candidates are Term-subgraphs; the agent's RULES eval them (EvalSubgraph)")
    print("=" * 92)

    o = s.add_node("Observable", {"x": 0.0, "y": 0.0, "expected": 0.0, "frame": 0.0, "mframe": -1.0,
                                  "matched": 0.0, "matched_count": 0.0, "cur_ord": 0.0, "sframe": -1.0,
                                  "solved": 0.0, "best_ord": -1.0})
    hub = s.add_node("ObsHub", {}); I.add_edge_unchecked(hub, "es_pred", o)
    lib = s.add_node("CandLib", {})
    for i, (nm, term) in enumerate(CANDS):
        root = I.add_term_subgraph(term)                 # the candidate Term becomes GRAPH DATA
        cand = s.add_node("Candidate", {"ord": float(i), "label": nm})
        I.add_edge_unchecked(cand, "has_term", root)
        I.add_edge_unchecked(lib, "has_cand", cand)
    print(f"  candidate library (Term-subgraphs): {[nm for nm, _ in CANDS]}")

    for r in (MEASURE, GATE, SEARCH):
        I.add_rule(r)

    # host feeds the example stream cyclically; the GRAPH RULES do the search.
    order_tried = []
    for step in range(1, 200):
        x, y, exp = EXAMPLES[(step - 1) % len(EXAMPLES)]
        I.set_attr(o, "x", float(x)); I.set_attr(o, "y", float(y))
        I.set_attr(o, "expected", float(exp)); I.set_attr(o, "frame", float(step))
        I.run_rules()
        cur = int(s.node(o)["attrs"].get("cur_ord") or 0)
        if not order_tried or order_tried[-1] != cur:
            order_tried.append(cur)
        if s.node(o)["attrs"].get("solved") == 1.0:
            break

    best = int(s.node(o)["attrs"].get("best_ord") or -1)
    print(f"\n  the agent's graph-rule search escalated through candidate ords {order_tried}")
    print(f"  -> GATED ord {best}" + (f" = '{CANDS[best][0]}'" if 0 <= best < len(CANDS) else " (none)"))
    print("\n" + "=" * 92)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = 0 <= best < len(CANDS) and CANDS[best][0] == "absdiff"
    print(f"  {'PASS' if ok else 'FAIL'} — the SEARCH ran as graph rules over Term-subgraph candidates, evaluating")
    print("  each via the agent's EvalSubgraph on the example stream and gating the one that fit all examples.")
    print("  The search is the AGENT'S (run_rules + its evaluator), not a Python loop. Next rung: a GENERATE")
    print("  rule that COMPOSES the candidate Term-subgraphs (as GENERATE_LADDER mints coeff candidates).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
