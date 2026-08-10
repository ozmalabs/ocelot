"""DRIVE THE REAL AGENT — the BRANCHING / MULTI-INPUT chip. Generalises the linear backward-chaining planner to
a DAG: a template can need MORE THAN ONE input, so when it goes on-path ALL its inputs become needed. The gap
'produce sum from value' is covered by a MULTI-INPUT rule combine(a,b)->sum, where a=halve(value) and
b=double(value): two branches from `value` that MERGE at combine. The planner backward-chains the DAG, mints all
three rules, and the composed faculty fires end-to-end. Dead-end (neg) excluded. No LLM.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/drive_self_design_branch.py
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
def P0(n,k): return {"type":"Plus","items":[A(n,k),L(0.0)]}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def And(*xs): return {"type":"And","items":list(xs)}

# (produces_id, out_attr, [in_attrs], effect)
TEMPLATES=[
 ("designed_halve","a",["value"],[["set_attr","o","a",{"__term__":{"type":"Div","a":A("o","value"),"b":L(2.0)}}]]),
 ("designed_double","b",["value"],[["set_attr","o","b",{"__term__":{"type":"Times","items":[A("o","value"),L(2.0)]}}]]),
 ("designed_combine","sum",["a","b"],                                # MULTI-INPUT: consumes a AND b
  [["set_attr","o","sum",{"__term__":{"type":"Plus","items":[A("o","a"),A("o","b")]}}]]),
 ("designed_neg","neg",["value"],[["set_attr","o","neg",{"__term__":{"type":"Neg","arg":A("o","value")}}]]),  # dead-end
]

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])

    for pid,out,ins,eff in TEMPLATES:
        t=a.s.add_node("ClauseTemplate",{"produces_id":pid,"out_attr":out,"on_path":0.0,
            "tmpl_match":[["game","has_obs","o"]],"tmpl_where":{"type":"Lit","value":True},"tmpl_effect":eff})
        a.inner.add_edge_unchecked(a.agent,"holds_template",t)
        for ia in ins:                                   # inputs as EDGES -> a template can have many
            n=a.s.add_node("InAttr",{"name":ia,"propagated":0.0}); a.inner.add_edge_unchecked(t,"needs_input",n)
    ax=a.s.add_node("CapabilityAxis",{"is_axis":1.0,"out_attr":"sum","need_seeded":0.0,
                                      "description":"produce sum from value (needs a MULTI-INPUT merge)"})
    a.inner.add_edge_unchecked(a.agent,"has_gap",ax)

    # 1. seed: the gap's output is the first needed attr
    a.inner.add_rule({"name":"__seed_gap_need","match":[["ag","has_gap","ax"]],
      "where":Lt(P0("ax","need_seeded"),L(0.5)),
      "effects":[["add_node","na","NeededAttr",{}],["set_attr","na","name",{"__term__":A("ax","out_attr")}],
                 ["add_edge","ag","needs","na"],["set_attr","ax","need_seeded",1.0]]})
    # 2. mark on-path: a template producing a needed attr goes on_path + its rule is queued
    a.inner.add_rule({"name":"__mark_on_path","match":[["ag","needs","na"],["ag","holds_template","t"]],
      "where":And(Eq(A("t","out_attr"),A("na","name")),Lt(P0("t","on_path"),L(0.5))),
      "effects":[["set_attr","t","on_path",1.0],
        ["add_node","rn","Rule",{"minted":0.0}],["set_attr","rn","id",{"__term__":A("t","produces_id")}],
        ["set_attr","rn","match",{"__term__":A("t","tmpl_match")}],["set_attr","rn","where",{"__term__":A("t","tmpl_where")}],
        ["set_attr","rn","effect",{"__term__":A("t","tmpl_effect")}],["add_edge","ag","wants_mint","rn"]]})
    # 3. propagate ALL inputs of an on-path template (the DAG/branching generalisation: each input -> needed)
    a.inner.add_rule({"name":"__propagate_inputs","match":[["ag","holds_template","t"],["t","needs_input","ia"]],
      "where":And(Gt(P0("t","on_path"),L(0.5)),Lt(P0("ia","propagated"),L(0.5))),
      "effects":[["add_node","na","NeededAttr",{}],["set_attr","na","name",{"__term__":A("ia","name")}],
                 ["add_edge","ag","needs","na"],["set_attr","ia","propagated",1.0]]})
    # 4. mint each queued rule live
    a.inner.add_rule({"name":"__design_mint","match":[["x","wants_mint","rn"]],
      "where":Lt(P0("rn","minted"),L(0.5)),
      "effects":[["set_rule_clause",{"__term__":A("rn","id")},"__mint__",{"__term__":{"type":"Var","name":"rn"}}],
                 ["set_attr","rn","minted",1.0]]})

    n0=a.inner.rule_count()
    for _ in range(12): a.master_tick(); a.tick()
    n1=a.inner.rule_count()
    on_path=sorted(a.s.node(t)["attrs"].get("produces_id") for t in a.s.nodes("ClauseTemplate")
                   if a.s.node(t)["attrs"].get("on_path")==1.0)
    print(f"  backward-chained DAG on_path: {on_path}   rule_count {n0}->{n1} (+{n1-n0})")

    g=a.s.add_node("WorldInstance",{"world_type":"BranchTest"})
    o=a.s.add_node("Obs",{"value":10.0}); a.inner.add_edge_unchecked(g,"has_obs",o)
    a.inner.run_rules(80)
    at=a.s.node(o)["attrs"]; av,bv,sv=at.get("a"),at.get("b"),at.get("sum")
    fired=(av==5.0 and bv==20.0 and sv==25.0)
    print(f"  GATE: value=10 -> a={av} b={bv} sum={sv} (expect 5,20,25)  multi-input merge works={fired}")

    ok=(on_path==["designed_combine","designed_double","designed_halve"] and (n1-n0)==3 and fired
        and "designed_neg" not in on_path and calls["n"]==0)
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — BRANCHING/multi-input: the agent backward-chained a DAG — combine(a,b) "
          f"merging two branches halve(value) and double(value) — propagated BOTH inputs, minted all 3 rules, "
          f"excluded the dead-end, and the multi-input faculty fired (10 -> a=5,b=20 -> sum=25). calls={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
