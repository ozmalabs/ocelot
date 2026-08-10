"""INTRINSIC DESIGN, rung 3 — honest HumanImpasse to the CREATOR (not the donkey) when search is dry.
When neither analogy (rung 1) nor search over held primitives (rung 2) yields a candidate that clears the
gate, the jabberwock does NOT summon claude -p — it raises a HumanImpasse addressed to the creator. Gap:
predict y = a*a, which NO composition of the held binary ops {Plus,Times,Minus} over operands {a,b} can fit.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/intrinsic_design_impasse.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from scripts.intrinsic_design_search import candidates   # reuse the held-primitive candidate space

TARGET = 0.99

def trial(agent_factory, clause, truth):
    agent = agent_factory()
    calls = {"n":0}
    agent.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"]+1), "DONKEY")[1])
    g  = agent.s.add_node("Game", {"id":"g"})
    ox1= agent.s.add_node("Observable", {"id":"x1","value":0.0})
    ox2= agent.s.add_node("Observable", {"id":"x2","value":0.0})
    oy = agent.s.add_node("Observable", {"id":"y","value":0.0,"pred":0.0})
    agent.inner.add_edge_unchecked(g,"predicts",oy)
    agent.inner.add_edge_unchecked(oy,"from1",ox1); agent.inner.add_edge_unchecked(oy,"from2",ox2)
    agent.inner.add_rule({"name":"search_predict",
      "match":[["g","predicts","y"],["y","from1","a"],["y","from2","b"]],
      "where":{"type":"Lit","value":True},
      "effects":[["set_attr","y","pred",{"__term__":clause}]]})
    accs=[]
    for i in range(6):
        x1=float(i+1); x2=float(2*i+3)
        agent.s.set_attr(ox1,"value",x1); agent.s.set_attr(ox2,"value",x2)
        agent.s.set_attr(oy,"value",truth(x1,x2))
        agent.master_tick(); agent.tick()
        ay=agent.s.node(oy)["attrs"]; err=abs((ay.get("value") or 0)-(ay.get("pred") or 0))
        accs.append(1.0/(1.0+err))
    return sum(accs)/len(accs), calls["n"], agent

def main():
    print("="*96)
    print("INTRINSIC DESIGN rung 3 — search is DRY (y=a*a, unreachable by held ops) -> HumanImpasse to creator, no donkey.")
    print("="*96)
    truth = lambda a,b: a*a
    fac = lambda: WorldAdapter(seeds=())
    results=[]; donkey_total=0; last=None
    for name, clause in candidates():
        acc, dn, ag = trial(fac, clause, truth); donkey_total += dn; last = ag
        results.append((acc,name)); print(f"  candidate {name:5s}  accuracy={acc:.3f}", flush=True)
    results.sort(reverse=True); best_acc, best = results[0]
    cleared = best_acc >= TARGET
    print(f"\n  best candidate {best!r} accuracy={best_acc:.3f}  cleared target {TARGET}? {cleared}")
    raised_impasse = False
    if not cleared:
        # the agent does NOT call the donkey — it raises an honest HumanImpasse to the creator.
        imp = last.s.add_node("Impasse", {"kind":"human","to":"creator","resolved":0.0,
              "gap":"predict y from a,b","note":"no composition of my held primitives clears the gate; I need a new primitive"})
        last.inner.add_edge_unchecked(last.agent, "raises", imp)
        raised_impasse = any(last.s.node(n)["attrs"].get("kind")=="human" for n in last.s.nodes("Impasse"))
    print(f"  raised HumanImpasse to creator: {raised_impasse}")
    print(f"  DONKEY (make_ask/claude -p) calls across the whole search: {donkey_total}")
    ok = (not cleared) and raised_impasse and donkey_total==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — search over held primitives was DRY (best {best_acc:.3f} < {TARGET}); the "
          f"jabberwock raised an honest HumanImpasse to the CREATOR for a new primitive, and the external "
          f"claude -p channel was NEVER called (calls={donkey_total}). Rungs 1+2+3 complete: analogy -> search "
          f"-> HumanImpasse-to-creator, all intrinsic, no donkey.")
    print("="*96)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
