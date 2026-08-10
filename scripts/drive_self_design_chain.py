"""DRIVE THE REAL AGENT — richer composition: BACKWARD-CHAINING planner of ARBITRARY DEPTH. From the gap's
output the agent works backward (what produces `out`? what produces ITS input? ...) until it reaches the gap's
available input, assembling a chain of ANY length and EXCLUDING dead-end templates — then mints the whole chain
and gates it by firing. Generalises the single 2-step hop. No LLM (donkey-spy must stay 0).

Gap: produce `out` from `value`. Templates: halve(value->h), incr(h->m), double(m->out), neg(value->neg, a
dead-end). No single template and no 2-step chain covers it; the 3-step chain halve->incr->double does. The
backward planner needs `out` -> picks double -> needs `m` -> incr -> needs `h` -> halve -> needs `value` (have).
neg is never needed, so never minted. Gate: value=10 -> h=5 -> m=6 -> out=12.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/drive_self_design_chain.py
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
def And(*xs): return {"type":"And","items":list(xs)}
def TT(): return {"type":"Lit","value":True}

TEMPLATES=[
 {"produces_id":"designed_halve","in_attr":"value","out_attr":"h",
  "tmpl_effect":[["set_attr","o","h",{"__term__":{"type":"Div","a":A("o","value"),"b":L(2.0)}}]]},
 {"produces_id":"designed_incr","in_attr":"h","out_attr":"m",
  "tmpl_effect":[["set_attr","o","m",{"__term__":{"type":"Plus","items":[A("o","h"),L(1.0)]}}]]},
 {"produces_id":"designed_double","in_attr":"m","out_attr":"out",
  "tmpl_effect":[["set_attr","o","out",{"__term__":{"type":"Times","items":[A("o","m"),L(2.0)]}}]]},
 {"produces_id":"designed_neg","in_attr":"value","out_attr":"neg",  # dead-end distractor
  "tmpl_effect":[["set_attr","o","neg",{"__term__":{"type":"Neg","arg":A("o","value")}}]]},
]

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])

    for t in TEMPLATES:
        n=a.s.add_node("ClauseTemplate",{"produces_id":t["produces_id"],"in_attr":t["in_attr"],
            "out_attr":t["out_attr"],"on_path":0.0,"tmpl_match":[["game","has_obs","o"]],
            "tmpl_where":{"type":"Lit","value":True},"tmpl_effect":t["tmpl_effect"]})
        a.inner.add_edge_unchecked(a.agent,"holds_template",n)
    ax=a.s.add_node("CapabilityAxis",{"is_axis":1.0,"in_attr":"value","out_attr":"out","need_seeded":0.0,
                                      "description":"produce out from value (needs a multi-step chain)"})
    a.inner.add_edge_unchecked(a.agent,"has_gap",ax)

    # 1. seed the backward search: the gap's OUTPUT is the first needed attr
    a.inner.add_rule({"name":"__seed_gap_need","match":[["ag","has_gap","ax"]],
      "where":Lt(P0("ax","need_seeded"),L(0.5)),
      "effects":[["add_node","na","NeededAttr",{}],["set_attr","na","name",{"__term__":A("ax","out_attr")}],
                 ["add_edge","ag","needs","na"],["set_attr","ax","need_seeded",1.0]]})
    # 2. backward chain: a template that PRODUCES a needed attr goes on the path; its INPUT becomes needed; and
    #    the template's rule is queued to mint. Propagates to any depth; dead-ends are never needed -> never minted.
    a.inner.add_rule({"name":"__chain_back","match":[["ag","needs","na"],["ag","holds_template","t"]],
      "where":And(Eq(A("t","out_attr"),A("na","name")),Lt(P0("t","on_path"),L(0.5))),
      "effects":[["set_attr","t","on_path",1.0],
        ["add_node","rn","Rule",{"minted":0.0}],["set_attr","rn","id",{"__term__":A("t","produces_id")}],
        ["set_attr","rn","match",{"__term__":A("t","tmpl_match")}],["set_attr","rn","where",{"__term__":A("t","tmpl_where")}],
        ["set_attr","rn","effect",{"__term__":A("t","tmpl_effect")}],["add_edge","ag","wants_mint","rn"],
        ["add_node","na2","NeededAttr",{}],["set_attr","na2","name",{"__term__":A("t","in_attr")}],
        ["add_edge","ag","needs","na2"]]})
    # 3. mint each queued rule live
    a.inner.add_rule({"name":"__design_mint","match":[["x","wants_mint","rn"]],
      "where":Lt(P0("rn","minted"),L(0.5)),
      "effects":[["set_rule_clause",{"__term__":A("rn","id")},"__mint__",{"__term__":{"type":"Var","name":"rn"}}],
                 ["set_attr","rn","minted",1.0]]})

    n0=a.inner.rule_count()
    for _ in range(10): a.master_tick(); a.tick()
    n1=a.inner.rule_count()
    on_path=sorted(a.s.node(t)["attrs"].get("produces_id") for t in a.s.nodes("ClauseTemplate")
                   if a.s.node(t)["attrs"].get("on_path")==1.0)
    print(f"  backward-chained on_path templates: {on_path}")
    print(f"  rule_count {n0}->{n1} (+{n1-n0} minted)")

    # GATE: the assembled chain of arbitrary depth fires end-to-end
    g=a.s.add_node("WorldInstance",{"world_type":"ChainTest"})
    o=a.s.add_node("Obs",{"value":10.0}); a.inner.add_edge_unchecked(g,"has_obs",o)
    a.inner.run_rules(80)
    at=a.s.node(o)["attrs"]; h,m,out=at.get("h"),at.get("m"),at.get("out")
    fired = (h==5.0 and m==6.0 and out==12.0)
    print(f"  GATE: value=10 -> h={h} m={m} out={out} (expect 5,6,12)  chain works={fired}")

    ok = (on_path==["designed_double","designed_halve","designed_incr"] and (n1-n0)==3 and fired
          and "designed_neg" not in on_path and calls["n"]==0)
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — richer composition: the agent BACKWARD-CHAINED a 3-step pipeline "
          f"(halve->incr->double) of arbitrary depth from the gap's output, EXCLUDED the dead-end (neg), minted "
          f"all 3 rules, and the assembled chain fired end-to-end (10->5->6->12). Graph-native, calls={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
