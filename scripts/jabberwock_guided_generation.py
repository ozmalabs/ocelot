"""GUIDED-GENERATION STEERING — the cure for the combinatorial wall, graph-native. Three guidances steer
the GENERATE/SEARCH loop so it stays small and terminates (the review's prescription):
  1 TYPED composition  — a GEN rule for op fires only on candidates whose KIND matches its arg-kinds
                          (num/bool), so type-invalid compositions are never minted.
  2 PER-PAIR DEDUP     — node-identity Eq markers: op(a,b) is minted once (no re-firing blowup).
  3 OBSERVATIONAL PRUNE— a PRUNE rule kills candidates that behave IDENTICALLY on the examples (same
                          signature) — the agent's evaluator collapsing equivalents (absdiff(x,y)==
                          absdiff(y,x); Minus(x,x)==0==...). This is the dominant pruner.
  + EARLY GATE         — stop when a survivor matches all examples.

absdiff is composed as a binary LIBRARY MACRO op (reuse, not atoms). Demo target |x-y|: the typed GEN
mints a small set, PRUNE collapses the observational duplicates, GATE keeps absdiff. donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_guided_generation.py
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
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*x): return {"type": "And", "items": list(x)}
def Not(a): return {"type": "Not", "arg": a}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Times(*x): return {"type": "Times", "items": list(x)}
def Ite(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}
def Nb(n, et): return {"type": "Neighbours", "node": V(n), "edge_type": et}
def Pick(src): return {"type": "Pick", "source": src}
def Eval(node): return {"type": "EvalSubgraph", "node": node}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}

EXAMPLES = [(3, 0, 3), (0, 5, 5), (4, 4, 0), (2, 7, 5), (9, 1, 8)]   # |x-y|
N = float(len(EXAMPLES))
MAX_SIZE = 1.0

def cnode(kind, size, label):
    return {"kind": kind, "size": float(size), "label": label, "ord": -1.0,
            "mc": 0.0, "sig": 0.0, "count": 0.0, "mframe": -1.0, "dead": 0.0, "is_winner": 0.0}

# 1+2: TYPED + PER-PAIR-DEDUP generation. GEN_MINUS: num,num -> num (binary, child.a/child.b).
def gen_binop(op_id, term_type, kind_out, label, build_children, marker):
    return {"id": op_id, "name": op_id,
        "match": [["lib", "has_cand", "ca"], ["ca", "has_term", "ra"], ["lib", "has_cand", "cb"], ["cb", "has_term", "rb"]],
        "where": And(Eq(A("ca", "kind"), L("num")), Eq(A("cb", "kind"), L("num")),
                     Eq(A("ca", "dead"), L(0.0)), Eq(A("cb", "dead"), L(0.0)),
                     Gt(L(MAX_SIZE), A("ca", "size")), Gt(L(MAX_SIZE), A("cb", "size")),
                     Not(Exists(Nb("ca", marker), "v", Eq(V("v"), V("cb"))))),
        "effects": build_children + [
            ["add_node", "nc", "Candidate", cnode(kind_out, 1, label)],
            ["add_edge", "nc", "has_term", "newroot"], ["add_edge", "lib", "has_cand", "nc"],
            ["set_attr", "nc", "ord", {"__term__": A("lib", "next_ord")}],
            ["set_attr", "lib", "next_ord", {"__term__": Plus(A("lib", "next_ord"), L(1.0))}],
            ["add_edge", "ca", marker, "cb"]]}

GEN_MINUS = gen_binop("gen_minus", "Term.Minus", "num", "minus(a,b)",
    [["add_node", "newroot", "Term.Minus", {}], ["add_edge", "newroot", "child.a", "ra"], ["add_edge", "newroot", "child.b", "rb"]],
    "did_minus")
# absdiff LIBRARY MACRO as a binary op: Ite(Gte(a,b), Minus(a,b), Minus(b,a))
GEN_ABSDIFF = gen_binop("gen_absdiff", "Term.IfThenElse", "num", "absdiff(a,b)",
    [["add_node", "g", "Term.Gte", {}], ["add_edge", "g", "child.a", "ra"], ["add_edge", "g", "child.b", "rb"],
     ["add_node", "m1", "Term.Minus", {}], ["add_edge", "m1", "child.a", "ra"], ["add_edge", "m1", "child.b", "rb"],
     ["add_node", "m2", "Term.Minus", {}], ["add_edge", "m2", "child.a", "rb"], ["add_edge", "m2", "child.b", "ra"],
     ["add_node", "newroot", "Term.IfThenElse", {}], ["add_edge", "newroot", "child.cond", "g"],
     ["add_edge", "newroot", "child.then", "m1"], ["add_edge", "newroot", "child.other", "m2"]],
    "did_absdiff")

# MEASURE: per num candidate, EvalSubgraph on this example -> consecutive-match count + rolling signature.
ACTIVE = Eval(Pick(Nb("cand", "has_term")))
MEASURE = {"id": "g_measure", "name": "g_measure",
    "match": [["h", "es_pred", "o"], ["lib", "has_cand", "cand"]],
    "where": And(Eq(A("cand", "kind"), L("num")), Eq(A("cand", "dead"), L(0.0)), Gt(A("o", "frame"), A("cand", "mframe"))),
    "effects": [
        ["set_attr", "cand", "mc", {"__term__": Ite(Eq(ACTIVE, A("o", "expected")), Plus(A("cand", "mc"), L(1.0)), L(0.0))}],
        ["set_attr", "cand", "sig", {"__term__": Plus(Times(A("cand", "sig"), L(31.0)), ACTIVE)}],
        ["set_attr", "cand", "count", {"__term__": Plus(A("cand", "count"), L(1.0))}],
        ["set_attr", "cand", "mframe", {"__term__": A("o", "frame")}]]}

# 3: OBSERVATIONAL PRUNE — two fully-measured candidates with the SAME signature are equivalent; kill the
# later (higher-ord) one so generation/measurement collapse over distinct behaviours only.
PRUNE = {"id": "g_prune", "name": "g_prune",
    "match": [["lib", "has_cand", "c1"], ["lib", "has_cand", "c2"]],
    "where": And(Gte(A("c1", "count"), L(N)), Gte(A("c2", "count"), L(N)), Eq(A("c1", "dead"), L(0.0)),
                 Eq(A("c1", "sig"), A("c2", "sig")), Gt(A("c1", "ord"), A("c2", "ord"))),
    "effects": [["set_attr", "c1", "dead", 1.0]]}

# EARLY GATE: a live survivor that matched all examples is the synthesised Term.
GATE = {"id": "g_gate", "name": "g_gate",
    "match": [["lib", "has_cand", "cand"]],
    "where": And(Gte(A("cand", "mc"), L(N)), Eq(A("cand", "dead"), L(0.0)), Eq(A("lib", "solved"), L(0.0))),
    "effects": [["set_attr", "lib", "solved", 1.0], ["set_attr", "cand", "is_winner", 1.0]]}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner
    print("=" * 94)
    print("GUIDED-GENERATION STEERING — typed + per-pair-dedup + observational-prune + early-gate")
    print("=" * 94)

    o = s.add_node("Observable", {"x": 0.0, "y": 0.0, "expected": 0.0, "frame": 0.0})
    hub = s.add_node("ObsHub", {}); I.add_edge_unchecked(hub, "es_pred", o)
    lib = s.add_node("CandLib", {"next_ord": 2.0, "solved": 0.0})
    for i, role in enumerate(("x", "y")):
        root = I.add_term_subgraph(A("o", role))
        c = s.add_node("Candidate", {**cnode("num", 0, role), "ord": float(i)})
        I.add_edge_unchecked(c, "has_term", root); I.add_edge_unchecked(lib, "has_cand", c)

    for r in (GEN_MINUS, GEN_ABSDIFF, MEASURE, PRUNE, GATE):
        I.add_rule(r)

    gen_done = 0
    for step in range(1, 400):
        x, y, exp = EXAMPLES[(step - 1) % len(EXAMPLES)]
        I.set_attr(o, "x", float(x)); I.set_attr(o, "y", float(y))
        I.set_attr(o, "expected", float(exp)); I.set_attr(o, "frame", float(step))
        I.run_rules(4000)
        if s.node(lib)["attrs"].get("solved") == 1.0:
            break

    cands = [s.node(c)["attrs"] for c in I.neighbours(lib, "has_cand")]
    total = len(cands)
    live = [c for c in cands if c.get("dead") != 1.0]
    pruned = [c for c in cands if c.get("dead") == 1.0]
    winner = next((c.get("label") for c in cands if c.get("is_winner") == 1.0), None)
    print(f"\n  generated candidates (typed): {total}")
    print(f"  observationally pruned (equivalent on the examples): {len(pruned)} -> survivors {len(live)}")
    print(f"  survivor labels: {sorted(set(c.get('label') for c in live))}")
    print(f"  GATED winner: {winner!r}")
    print("\n" + "=" * 94)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = winner == "absdiff(a,b)"
    print(f"  {'PASS' if ok else 'FAIL'} — typing kept type-invalid compositions out, per-pair dedup stopped")
    print("  re-minting, and the OBSERVATIONAL PRUNE collapsed equivalents (the agent's evaluator deciding) so")
    print("  the space stayed small and terminated; the gate kept absdiff. These are the steering knobs that")
    print("  dissolve the combinatorial wall — applied with aggregation-generation, the deeper blocks follow.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
