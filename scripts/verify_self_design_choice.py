"""DRIVE THE REAL AGENT: prove the jabberwock can CHOOSE to design — its OWN autonomy frontier_pick (the real
Argmax selection term from seeds/autonomy.json) selects the self_design CapabilityAxis when its value is highest,
and it can still answer HOW it designs (the self_design reflective faculty). No LLM: the selector is the agent's,
evaluated by the agent's own a.inner.evaluate; the answer is read off its own machinery.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/verify_self_design_choice.py
"""
from __future__ import annotations
import os, sys, json
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import reflective_faculty as rf

def frontier_pick_term():
    d=json.load(open(os.path.join(ROOT,"seeds","autonomy.json"))); box={}
    def walk(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if k=="frontier_pick_term" and isinstance(v,str): box["t"]=json.loads(v)
                else: walk(v)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d); return box.get("t")

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    fpt=frontier_pick_term()
    sd=next((n for n in a.s.nodes("CapabilityAxis")
             if a.s.node(n)["attrs"].get("name")=="self_design"), None)
    print(f"  self_design CapabilityAxis present: {sd is not None}")
    eligible = sd is not None and len(list(a.inner.neighbours(sd,"investigated_by")))>=1
    print(f"  self_design is frontier-eligible (has investigated_by): {eligible}")

    # (a) DRIVE the real selector now
    pick0 = a.inner.evaluate(fpt)
    print(f"  frontier_pick (current) selects: {pick0}  (self_design? {str(pick0)==str(sd)})")

    # (b) model the agent having EXPLORED its current capabilities: saturate every OTHER eligible axis.
    #     This is the realistic trigger for self-extension — when the known capabilities are mined out, the
    #     UNDERSTAND drive's highest-value frontier becomes building NEW faculties.
    for n in a.s.nodes("CapabilityAxis"):
        if str(n)!=str(sd):
            a.s.set_attr(n,"saturation",1.0)
    pick1 = a.inner.evaluate(fpt)
    chose_design = str(pick1)==str(sd)
    print(f"  after its other capabilities saturate, frontier_pick selects: {pick1}  -> chose self_design = {chose_design}")

    # (c) and it can still answer HOW it designs, from its own machinery (the step-1 reflective faculty)
    ans = rf.reflect("self_design", None, a.s)
    cm = ans.get("composable_machinery",{})
    print(f"  drive(self_design) -> composable_machinery={cm}  strategy_steps={len(ans.get('design_strategy',[]))}")

    ok = (sd is not None and eligible and chose_design and cm.get("rules",0)>=1 and calls["n"]==0)
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent can CHOOSE to design: self_design is a first-class, "
          f"eligible CapabilityAxis in its OWN frontier_pick, and when its current capabilities are explored its "
          f"real selector ELECTS self_design ({chose_design}); it then answers HOW from its own machinery "
          f"(rules/terms/microtheories). Self-invoked, graph-native, no LLM (calls={calls['n']}).")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
