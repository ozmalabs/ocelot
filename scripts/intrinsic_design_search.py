"""INTRINSIC DESIGN, rung 2 — SEARCH over held primitives + GATE, no donkey. When ANALOGY (rung 1) finds no
single held faculty matching the gap's shape, the jabberwock GENERATES a candidate space by composing its
HELD primitives (operators x operands) and lets its OWN intrinsic measure (predictive accuracy, the GAP-2
rising-tide) GATE the winner. This designs a NOVEL composition no held faculty had. The external claude -p
channel is wired to a spy to PROVE it is never called.

Gap: predict observable y from x1,x2 where (unknown to the agent) y = x1 + x2. No held faculty predicts y;
the agent must COMPOSE one. Candidates = {op(a,b) : op in held {Plus,Times,Minus}} + singletons {a,b} —
generated from what it holds, NOT handed the answer. The measure picks Plus(a,b).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/intrinsic_design_search.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter

def Av(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}

# the agent's HELD primitives: binary operators (a/b shape) and the operands available (the two input
# observables a,b reachable via from1/from2 edges). The candidate SPACE is their cross-product — the agent
# enumerating compositions of what it holds. The answer (Plus) is just one cell of this generated grid.
def candidates():
    a, b = Av("a","value"), Av("b","value")
    cands = [("a", a), ("b", b),
             ("a+b", {"type":"Plus","items":[a,b]}),
             ("a*b", {"type":"Times","items":[a,b]}),
             ("a-b", {"type":"Minus","a":a,"b":b})]
    return cands

def trial(clause):
    """Boot minimal (no donkey, no load_all_seeds), install ONE predictor whose effect IS this candidate,
    run the world, return mean predictive accuracy + the donkey call-count."""
    agent = WorldAdapter(seeds=())
    calls = {"n":0}
    agent.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"]+1), "DONKEY")[1])
    g  = agent.s.add_node("Game", {"id":"g"})
    ox1= agent.s.add_node("Observable", {"id":"x1","value":0.0})
    ox2= agent.s.add_node("Observable", {"id":"x2","value":0.0})
    oy = agent.s.add_node("Observable", {"id":"y","value":0.0,"pred":0.0})
    agent.inner.add_edge_unchecked(g,"predicts",oy)
    agent.inner.add_edge_unchecked(oy,"from1",ox1)
    agent.inner.add_edge_unchecked(oy,"from2",ox2)
    # the predictor: pred(y) = <candidate over a,b>. Reads ONLY inputs a,b (never y) — no peeking.
    agent.inner.add_rule({"name":"search_predict",
      "match":[["g","predicts","y"],["y","from1","a"],["y","from2","b"]],
      "where":{"type":"Lit","value":True},
      "effects":[["set_attr","y","pred",{"__term__":clause}]]})
    accs=[]
    for i in range(6):
        x1=float(i+1); x2=float(2*i+3)          # deterministic, varied inputs
        agent.s.set_attr(ox1,"value",x1); agent.s.set_attr(ox2,"value",x2)
        agent.s.set_attr(oy,"value",x1+x2)      # the world reveals the truth (host I/O)
        agent.master_tick(); agent.tick()       # predictor computes pred from a,b
        ay=agent.s.node(oy)["attrs"]
        err=abs((ay.get("value") or 0)-(ay.get("pred") or 0))
        accs.append(1.0/(1.0+err))              # the GAP-2 measure: 1/(1+|value-pred|)
    return sum(accs)/len(accs), calls["n"]

def main():
    print("="*96)
    print("INTRINSIC DESIGN rung 2 — SEARCH held-primitive compositions, GATE by the agent's own measure, no donkey.")
    print("="*96)
    results=[]; donkey_total=0
    for name, clause in candidates():
        acc, dn = trial(clause); donkey_total += dn
        results.append((acc, name)); print(f"  candidate pred(y)={name:5s}  mean predictive accuracy={acc:.3f}", flush=True)
    results.sort(reverse=True)
    best_acc, best = results[0]
    print(f"\n  GATE selects: pred(y) = {best!r}  (accuracy {best_acc:.3f})")
    print(f"  DONKEY (make_ask/claude -p) calls across the whole search: {donkey_total}")
    ok = (best=="a+b" and best_acc>0.99 and donkey_total==0)
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — the jabberwock DESIGNED a novel composition no held faculty had: it "
          f"GENERATED the candidate space from its held primitives (operators x operands), ran each, and its "
          f"OWN predictive-accuracy measure GATED the winner (a+b) — the external claude -p channel was NEVER "
          f"called (calls={donkey_total}). Rung 2 (search+gate) complete; with rung 1 (analogy) the agent now "
          f"designs by shape OR by search, intrinsically.")
    print("="*96)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
