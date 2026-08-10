"""DRIVE THE REAL AGENT — third chip at NL->fireable-rule: the CONDITION definition construction. For a
genus-differentia-by-CONDITION definition "X is a Y that has ATTR COMP N" the agent parses (concept, genus,
attribute, comparator, value) and synthesises a recogniser:
    match a node that is an instance of the genus; where node.ATTR COMP N; effect set is_X=1
compiled via the agent's real rule compiler and fired discriminatively (right genus + condition -> recognised;
wrong value or wrong genus -> rejected). New vs count/connectivity: a NUMERIC ATTRIBUTE CONDITION on a typed
genus. Bounded to this shape (extensible), no LLM.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/drive_definition_condition.py
"""
from __future__ import annotations
import os, sys, re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

WORDNUM={"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,
         "twenty":20,"thirty":30,"forty":40,"fifty":50,"hundred":100}
COMP={"above":"Gt","over":"Gt","exceeding":"Gt","below":"Lt","under":"Lt"}

def parse_condition(gloss):
    """'[a] X is a Y that has ATTR COMP N' -> (concept,genus,attr,comp,value)."""
    g=gloss.lower()
    mc=re.search(r"\b(a|an)\s+([a-z]+)\s+is\s+(a|an)\s+([a-z]+)", g)
    mh=re.search(r"has\s+([a-z]+)\s+(above|over|exceeding|below|under)\s+([a-z]+)", g)
    if not (mc and mh): return None
    val=WORDNUM.get(mh.group(3))
    if val is None: return None
    return mc.group(2), mc.group(4), mh.group(1), COMP[mh.group(2)], val

def Var(n): return {"type":"Var","name":n}
def A(n,k): return {"type":"Attr","node":Var(n),"key":k}
def P0(n,k): return {"type":"Plus","items":[A(n,k),{"type":"Lit","value":0.0}]}
def L(v): return {"type":"Lit","value":v}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}

def synthesise(concept,genus,attr,comp,value):
    cond={"type":comp,"a":P0("d",attr),"b":L(float(value))}
    where={"type":"And","items":[Eq(A("g","name"),L(genus)),cond]}
    return {"name":f"recog_{concept}","match":[["d","instance_of","g"]],"where":where,
            "effects":[["set_attr","d",f"is_{concept}",1.0]]}

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])

    DEFS=["A heatwave is a day that has temperature above thirty",
          "A bargain is a product that has price below ten"]
    results=[]
    for gloss in DEFS:
        pd=parse_condition(gloss)
        print(f"  definition: {gloss!r}")
        print(f"    parsed (concept,genus,attr,comp,value) = {pd}")
        if not pd: results.append(False); continue
        concept,genus,attr,comp,value=pd
        a.inner.add_rule(synthesise(concept,genus,attr,comp,value))
        print(f"    synthesised: match instance_of g(name={genus!r}); where d.{attr} {comp} {value}; set is_{concept}")

        gc=a.s.add_node("Concept",{"name":genus})
        other=a.s.add_node("Concept",{"name":"other_"+genus})
        def inst(genus_node, **attrs):
            d=a.s.add_node("Entity",attrs); a.inner.add_edge_unchecked(d,"instance_of",genus_node); return d
        sat = value+5 if comp=="Gt" else value-5      # satisfies the condition
        vio = value-5 if comp=="Gt" else value+5      # violates it
        pos=inst(gc, **{attr:float(sat)})             # right genus + condition met
        neg_cond=inst(gc, **{attr:float(vio)})        # right genus, condition NOT met
        neg_genus=inst(other, **{attr:float(sat)})    # wrong genus, condition met
        a.inner.run_rules(40)
        def rec(s): return a.s.node(s)["attrs"].get(f"is_{concept}")==1.0
        p_ok,c_ok,gx=rec(pos),rec(neg_cond),rec(neg_genus)
        ok=p_ok and (not c_ok) and (not gx)
        print(f"    GATE: {genus}({attr}={sat}) recognised={p_ok}  {genus}({attr}={vio})={c_ok}  "
              f"wrong-genus({attr}={sat})={gx}  -> {ok}")
        results.append(ok)

    ok=all(results) and calls["n"]==0
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — condition definition->recogniser: the agent parsed a genus + a "
          f"numeric attribute CONDITION ('has ATTR above/below N') and synthesised a recogniser that fires only "
          f"on the right genus meeting the condition — rejecting condition-violators and wrong-genus. Works for "
          f"heatwave and bargain (reusable), compiled+fired on the real agent, calls={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
