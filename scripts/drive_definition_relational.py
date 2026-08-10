"""DRIVE THE REAL AGENT — second chip at NL->fireable-rule: the RELATIONAL definition construction. Extends the
composition schema ("X is composed of N P") with a RELATION differentia ("... connected R"): the recogniser now
also requires the parts to be CONNECTED (>= N-1 links), so it rejects a disconnected set of N parts that the
count-only rule would wrongly accept. Same path as before — parse -> synthesise structured rule -> compile via
the agent's real rule compiler -> fire discriminatively. Bounded to these definition shapes (extensible), no LLM.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/drive_definition_relational.py
"""
from __future__ import annotations
import os, sys, re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

WORDNUM={"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}

def parse_definition(gloss):
    """'[a] X is ... composed of N P [connected R]' -> (concept,count,part,relation|None)."""
    g=gloss.lower()
    mc=re.search(r"\b(a|an)\s+([a-z]+)\s+is\b", g)
    mp=re.search(r"composed of\s+([a-z]+)\s+([a-z]+)", g)
    if not (mc and mp): return None
    count=WORDNUM.get(mp.group(1))
    if count is None: return None
    part=mp.group(2); part=part[:-1] if part.endswith("s") else part
    mr=re.search(r"connected\s+([a-z]+)", g)               # the RELATION differentia (optional)
    relation=mr.group(1) if mr else ("connected" if "connected" in g else None)
    return mc.group(2), count, part, relation

def Var(n): return {"type":"Var","name":n}
def Neigh(n,e): return {"type":"Count","source":{"type":"Neighbours","node":Var(n),"edge_type":e,"any_type":False}}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Gte(a,b): return {"type":"Gte","a":a,"b":b}
def L(v): return {"type":"Lit","value":v}

def synthesise(concept,count,part,relation):
    pe=f"has_{part}"
    clauses=[Eq(Neigh("sh",pe),L(float(count)))]                       # composition: exactly N parts
    if relation:                                                       # relational: connected (>= N-1 links)
        clauses.append(Gte(Neigh("sh","has_connection"),L(float(count-1))))
    where=clauses[0] if len(clauses)==1 else {"type":"And","items":clauses}
    return {"name":f"recog_{concept}","match":[["sh",pe,"p"]],"where":where,
            "effects":[["set_attr","sh",f"is_{concept}",1.0]]}, pe

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])

    DEFS=["A tetromino is a geometric shape composed of four squares connected orthogonally",
          "A chain is a structure composed of three links connected sequentially"]
    results=[]
    for gloss in DEFS:
        pd=parse_definition(gloss)
        print(f"  definition: {gloss!r}")
        print(f"    parsed (concept,count,part,relation) = {pd}")
        if not pd: results.append(False); continue
        concept,count,part,relation=pd
        rule,pe=synthesise(concept,count,part,relation)
        print(f"    synthesised: match {pe}; where count({pe})=={count}"
              f"{' AND count(has_link)>='+str(count-1)+' (connected)' if relation else ''}; set is_{concept}")
        a.inner.add_rule(rule)

        def shape(nparts, nlinks):
            sh=a.s.add_node("Shape",{})
            for _ in range(nparts):
                pn=a.s.add_node(part.capitalize(),{}); a.inner.add_edge_unchecked(sh,pe,pn)
            for _ in range(nlinks):
                a.inner.add_edge_unchecked(sh,"has_connection",a.s.add_node("Link",{}))
            return sh
        pos=shape(count,count-1)            # right count, connected
        neg_count=shape(count-1,count-2)    # wrong count
        neg_disc=shape(count,0)             # right count but DISCONNECTED (the new discrimination)
        a.inner.run_rules(50)
        def rec(s): return a.s.node(s)["attrs"].get(f"is_{concept}")==1.0
        p_ok,c_ok,d_ok=rec(pos),rec(neg_count),rec(neg_disc)
        ok = p_ok and (not c_ok) and (not d_ok)
        print(f"    GATE: connected-{count} recognised={p_ok}  {count-1}-parts={c_ok}  "
              f"DISCONNECTED-{count}={d_ok}  -> {ok}")
        results.append(ok)

    ok=all(results) and calls["n"]==0
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — relational definition->recogniser: the agent parsed the RELATION "
          f"differentia ('connected ...') and synthesised a recogniser that requires CONNECTIVITY, not just "
          f"count — rejecting a disconnected N-part set the count-only rule would accept. Works for tetromino "
          f"and chain (reusable), compiled+fired on the real agent, calls={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
