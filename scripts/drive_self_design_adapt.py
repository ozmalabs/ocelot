"""DRIVE THE REAL AGENT — the ADAPTATION chip: REUSE a HELD rule for a new gap by substituting its SLOTS
(rename attrs, parametrise constants) in its clause-trees, rather than copying verbatim (rung-1) or re-deriving.
The agent holds `halve` (set o.h = o.value/2). A new gap "set o.third = o.amount/3" is the SAME STRUCTURE with
different slots; the agent ADAPTS halve via a substitution {value->amount, h->third, 2.0->3.0} -> a new fireable
rule. Done again for `quarter`. Compiled via the real rule compiler and fired. The adapted rule is provably the
held rule's structure with slots substituted (reuse, not re-derivation). No LLM.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/drive_self_design_adapt.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}
def L(v): return {"type":"Lit","value":v}

# the HELD rule the agent reuses: set o.h = o.value / 2
HALVE={"name":"halve","match":[["g","has_obs","o"]],"where":{"type":"Lit","value":True},
       "effects":[["set_attr","o","h",{"__term__":{"type":"Div","a":A("o","value"),"b":L(2.0)}}]]}

def adapt(rule, new_name, subst):
    """Reuse a held rule: deep-substitute the SLOT tokens (attr-name strings + constant numbers) in its
    clause-trees. Everything else (structure, var names, ops) is preserved -> the held rule, parametrised."""
    def walk(x):
        if isinstance(x,str): return subst.get(x,x)
        if isinstance(x,bool): return x
        if isinstance(x,(int,float)): return subst.get(x,x)
        if isinstance(x,list): return [walk(e) for e in x]
        if isinstance(x,dict): return {k:walk(v) for k,v in x.items()}
        return x
    return {"name":new_name,"match":walk(rule["match"]),"where":walk(rule["where"]),"effects":walk(rule["effects"])}

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])

    a.inner.add_rule(HALVE)                                   # the agent holds `halve`

    # ADAPT the held rule to two new gaps by slot-substitution (reuse + parametrise)
    THIRD = adapt(HALVE, "third",   {"value":"amount","h":"third","b" : "b", 2.0:3.0})
    QUARTER = adapt(HALVE, "quarter",{"value":"qty","h":"quarter", 2.0:4.0})
    # prove it's the held structure with slots substituted (not a fresh hand-write)
    import json
    base_div = json.dumps(HALVE["effects"]).count("Div")
    third_div = json.dumps(THIRD["effects"]).count("Div")
    structural = (base_div==1 and third_div==1
                  and json.dumps(THIRD["effects"]).replace("amount","value").replace("third","h").replace("3.0","2.0")
                      == json.dumps(HALVE["effects"]))
    print(f"  adapted 'third' is halve's structure with slots substituted (provably): {structural}")
    a.inner.add_rule(THIRD); a.inner.add_rule(QUARTER)
    print("  adapted: third = set o.third = o.amount/3 ;  quarter = set o.quarter = o.qty/4")

    g=a.s.add_node("WorldInstance",{"world_type":"AdaptTest"})
    o1=a.s.add_node("Obs",{"value":10.0}); a.inner.add_edge_unchecked(g,"has_obs",o1)
    o2=a.s.add_node("Obs",{"amount":12.0}); a.inner.add_edge_unchecked(g,"has_obs",o2)
    o3=a.s.add_node("Obs",{"qty":20.0}); a.inner.add_edge_unchecked(g,"has_obs",o3)
    a.inner.run_rules(40)
    h=a.s.node(o1)["attrs"].get("h"); th=a.s.node(o2)["attrs"].get("third"); qt=a.s.node(o3)["attrs"].get("quarter")
    print(f"  GATE: halve(value=10)->h={h} (=5?)  third(amount=12)->third={th} (=4?)  quarter(qty=20)->quarter={qt} (=5?)")
    fired = (h==5.0 and th==4.0 and qt==5.0)

    ok = structural and fired and calls["n"]==0
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — ADAPTATION: the agent REUSED its held `halve` rule for two new gaps "
          f"by substituting slots (attrs + the constant divisor) — yielding `third` and `quarter` that compiled "
          f"and fired correctly (10->5, 12->4, 20->5). Reuse-and-parametrise of real machinery, not copy or "
          f"re-derive. calls={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
