"""AGGREGATION-BODY GENERATION — the last rung: the agent generates a Sum whose BODY is itself synthesised,
graph-native, reaching the N-DIMENSIONAL distance.

  body-leaves : px = pos[i] , pt = target[i]   (IndexAt over the bound index i)
  GEN (guided): compose body candidates over them  -> minus(px,pt), absdiff(px,pt), ...   (typed, deduped)
  WRAP rule   : for each body candidate, mint Sum(dims, i, body)  -> a "whole" candidate (the aggregation
                whose body was synthesised) -- the new higher-order generation step.
  SEARCH/GATE : EvalSubgraph each whole on the N-d vector examples (incl pos<target so absdiff is forced);
                gate the one matching all = Sum over dims of |pos[i]-target[i]| = the N-DIMENSIONAL dist.

The SAME gated term verifies on 1-D..4-D vectors. donkey=0; generate + wrap + search are all graph rules.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_aggregation_body_generation.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Ao(k): return {"type": "Attr", "node": V("o"), "key": k}
def IA(seq, idx): return {"type": "IndexAt", "seq": seq, "index": idx}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*x): return {"type": "And", "items": list(x)}
def Not(a): return {"type": "Not", "arg": a}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Ite(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}
def Nb(n, et): return {"type": "Neighbours", "node": V(n), "edge_type": et}
def Pick(src): return {"type": "Pick", "source": src}
def Eval(node): return {"type": "EvalSubgraph", "node": node}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}

DIST_EX = [({"pos": [3, 1], "target": [0, 0], "dims": [0, 1]}, 4),
           ({"pos": [1, 3], "target": [4, 0], "dims": [0, 1]}, 6),          # pos<target -> forces absdiff
           ({"pos": [0, 0, 2], "target": [3, 1, 0], "dims": [0, 1, 2]}, 6),  # 3-D
           ({"pos": [2], "target": [5], "dims": [0]}, 3),                    # 1-D, pos<target
           ({"pos": [1, 1, 1, 1], "target": [0, 0, 0, 0], "dims": [0, 1, 2, 3]}, 4)]  # 4-D
N = float(len(DIST_EX))

def cn(kind, size, role, label):
    return {"kind": kind, "size": float(size), "role": role, "label": label, "ord": -1.0,
            "mc": 0.0, "mframe": -1.0, "dead": 0.0, "wrapped": 0.0, "is_winner": 0.0}

# guided binary GEN over BODY candidates (typed num, node-Eq per-pair dedup, size-bounded)
def gen_binop(op_id, label, build, marker):
    return {"id": op_id, "name": op_id,
        "match": [["lib", "has_cand", "ca"], ["ca", "has_term", "ra"], ["lib", "has_cand", "cb"], ["cb", "has_term", "rb"]],
        "where": And(Eq(A("ca", "role"), L("body")), Eq(A("cb", "role"), L("body")),
                     Eq(A("ca", "kind"), L("num")), Eq(A("cb", "kind"), L("num")),
                     Gt(L(1.0), A("ca", "size")), Gt(L(1.0), A("cb", "size")),
                     Not(Exists(Nb("ca", marker), "v", Eq(V("v"), V("cb"))))),
        "effects": build + [
            ["add_node", "nc", "Candidate", cn("num", 1, "body", label)],
            ["add_edge", "nc", "has_term", "newroot"], ["add_edge", "lib", "has_cand", "nc"],
            ["set_attr", "nc", "ord", {"__term__": A("lib", "next_ord")}],
            ["set_attr", "lib", "next_ord", {"__term__": Plus(A("lib", "next_ord"), L(1.0))}],
            ["add_edge", "ca", marker, "cb"]]}

GEN_MINUS = gen_binop("gen_minus", "minus(px,pt)",
    [["add_node", "newroot", "Term.Minus", {}], ["add_edge", "newroot", "child.a", "ra"], ["add_edge", "newroot", "child.b", "rb"]],
    "did_minus")
GEN_ABSDIFF = gen_binop("gen_absdiff", "absdiff(px,pt)",
    [["add_node", "g", "Term.Gte", {}], ["add_edge", "g", "child.a", "ra"], ["add_edge", "g", "child.b", "rb"],
     ["add_node", "m1", "Term.Minus", {}], ["add_edge", "m1", "child.a", "ra"], ["add_edge", "m1", "child.b", "rb"],
     ["add_node", "m2", "Term.Minus", {}], ["add_edge", "m2", "child.a", "rb"], ["add_edge", "m2", "child.b", "ra"],
     ["add_node", "newroot", "Term.IfThenElse", {}], ["add_edge", "newroot", "child.cond", "g"],
     ["add_edge", "newroot", "child.then", "m1"], ["add_edge", "newroot", "child.other", "m2"]],
    "did_absdiff")

# WRAP: the new aggregation-generation step — wrap a synthesised BODY in Sum(dims, i, body) -> a whole term.
WRAP = {"id": "wrap_sum", "name": "wrap_sum",
    "match": [["lib", "has_cand", "bc"], ["bc", "has_term", "broot"], ["lib", "dims_source", "dsrc"]],
    "where": And(Eq(A("bc", "role"), L("body")), Eq(A("bc", "kind"), L("num")), Eq(A("bc", "wrapped"), L(0.0))),
    "effects": [
        ["add_node", "sm", "Term.Sum", {"var_name": "i"}],
        ["add_edge", "sm", "child.source", "dsrc"], ["add_edge", "sm", "child.value", "broot"],
        ["add_node", "wc", "Candidate", cn("num", 2, "whole", {"__term__": A("bc", "label")})],
        ["add_edge", "wc", "has_term", "sm"], ["add_edge", "lib", "has_cand", "wc"],
        ["add_edge", "wc", "from_body", "bc"],
        ["set_attr", "bc", "wrapped", 1.0]]}

ACTIVE = Eval(Pick(Nb("cand", "has_term")))
MEASURE = {"id": "agg_measure", "name": "agg_measure",
    "match": [["h", "es_pred", "o"], ["lib", "has_cand", "cand"]],
    "where": And(Eq(A("cand", "role"), L("whole")), Gt(A("o", "frame"), A("cand", "mframe"))),
    "effects": [
        ["set_attr", "cand", "mc", {"__term__": Ite(Eq(ACTIVE, A("o", "expected")), Plus(A("cand", "mc"), L(1.0)), L(0.0))}],
        ["set_attr", "cand", "mframe", {"__term__": A("o", "frame")}]]}
GATE = {"id": "agg_gate", "name": "agg_gate",
    "match": [["lib", "has_cand", "cand"]],
    "where": And(Eq(A("cand", "role"), L("whole")), Gte(A("cand", "mc"), L(N)), Eq(A("lib", "solved"), L(0.0))),
    "effects": [["set_attr", "lib", "solved", 1.0], ["set_attr", "cand", "is_winner", 1.0]]}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner
    print("=" * 94)
    print("AGGREGATION-BODY GENERATION — generate a Sum whose BODY is synthesised -> the N-dimensional dist")
    print("=" * 94)

    o = s.add_node("Observable", {"pos": [0.0], "target": [0.0], "dims": [0.0], "expected": 0.0, "frame": 0.0})
    hub = s.add_node("ObsHub", {}); I.add_edge_unchecked(hub, "es_pred", o)
    lib = s.add_node("CandLib", {"next_ord": 2.0, "solved": 0.0})
    # body-leaves: pos[i] and target[i] (IndexAt over the bound index i)
    for i, (label, term) in enumerate([("pos[i]", IA(Ao("pos"), V("i"))), ("target[i]", IA(Ao("target"), V("i")))]):
        root = I.add_term_subgraph(term)
        c = s.add_node("Candidate", {**cn("num", 0, "body", label), "ord": float(i)})
        I.add_edge_unchecked(c, "has_term", root); I.add_edge_unchecked(lib, "has_cand", c)
    # the shared Sum source: dims
    dsrc = I.add_term_subgraph(Ao("dims")); I.add_edge_unchecked(lib, "dims_source", dsrc)
    print("  body-leaves: pos[i], target[i]   (the agent composes the body, then WRAPS it in Sum over dims)")

    for r in (GEN_MINUS, GEN_ABSDIFF, WRAP, MEASURE, GATE):
        I.add_rule(r)

    for step in range(1, 300):
        ex, exp = DIST_EX[(step - 1) % len(DIST_EX)]
        I.set_attr(o, "pos", [float(v) for v in ex["pos"]])
        I.set_attr(o, "target", [float(v) for v in ex["target"]])
        I.set_attr(o, "dims", [float(v) for v in ex["dims"]])
        I.set_attr(o, "expected", float(exp)); I.set_attr(o, "frame", float(step))
        I.run_rules(4000)
        if s.node(lib)["attrs"].get("solved") == 1.0:
            break

    cands = [s.node(c)["attrs"] for c in I.neighbours(lib, "has_cand")]
    bodies = sorted(set(c.get("label") for c in cands if c.get("role") == "body"))
    wholes = [c for c in cands if c.get("role") == "whole"]
    winner = next((c for c in cands if c.get("is_winner") == 1.0), None)
    wlabel = winner.get("label") if winner else None
    print(f"\n  bodies generated (guided): {bodies}")
    print(f"  wrapped into Sum-over-dims wholes: {len(wholes)}")
    print(f"  GATED whole: Sum(dims, i, {wlabel!r})")
    if winner:
        dims_seen = sorted(set(len(ex["dims"]) for ex, _ in DIST_EX))
        print(f"  it was gated by matching ALL {int(N)} examples (consecutive mc={winner.get('mc')}), which span "
              f"{dims_seen}-D vectors (incl pos<target) -> coordinate-count agnostic = N-DIMENSIONAL")
    print("\n" + "=" * 94)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = wlabel == "absdiff(px,pt)"
    print(f"  {'PASS' if ok else 'FAIL'} — the agent synthesised the BODY (absdiff over pos[i],target[i]) AND")
    print("  generated the AGGREGATION (Sum over dims of it) graph-natively = the N-dimensional distance. With")
    print("  this higher-order rung, the deeper N-d Terms (dist_moved, the decision Argmax-over-candidates of")
    print("  Sum-over-candidates) are reachable by the same generate+wrap+search, all in run_rules, donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
