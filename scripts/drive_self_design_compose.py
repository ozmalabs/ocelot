"""DRIVE THE REAL AGENT — the composer's MULTI-RULE reach (beyond rung-1 analogy). When NO single held template
matches a gap, the agent ASSEMBLES a CHAIN of held templates whose outputs feed the next's input, mints them
ALL, and the composed multi-rule faculty is gated by firing it. No LLM (donkey-spy must stay 0).

Gap: produce `out` from `value`. No single template does value->out. Held templates: halve (value->h), incr
(h->out), neg (value->neg, a distractor). The agent links composable templates (t1.out_attr == t2.in_attr),
finds the chain whose ends match the gap (in=value, out=out), and mints BOTH rules. Gate: value=10 -> h=5,
out=6 (= value/2 + 1).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/drive_self_design_compose.py
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
def Not(x): return {"type":"Not","arg":x}
def And(*xs): return {"type":"And","items":list(xs)}

TEMPLATES=[
 {"produces_id":"designed_halve","in_attr":"value","out_attr":"h",
  "tmpl_match":[["game","has_obs","o"]],"tmpl_where":{"type":"Lit","value":True},
  "tmpl_effect":[["set_attr","o","h",{"__term__":{"type":"Div","a":A("o","value"),"b":L(2.0)}}]]},
 {"produces_id":"designed_incr","in_attr":"h","out_attr":"out",
  "tmpl_match":[["game","has_obs","o"]],"tmpl_where":{"type":"Lit","value":True},
  "tmpl_effect":[["set_attr","o","out",{"__term__":{"type":"Plus","items":[A("o","h"),L(1.0)]}}]]},
 {"produces_id":"designed_neg","in_attr":"value","out_attr":"neg",   # distractor: dead-ends, not on the chain
  "tmpl_match":[["game","has_obs","o"]],"tmpl_where":{"type":"Lit","value":True},
  "tmpl_effect":[["set_attr","o","neg",{"__term__":{"type":"Neg","arg":A("o","value")}}]]},
]

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])

    for t in TEMPLATES:
        n=a.s.add_node("ClauseTemplate",{"produces_id":t["produces_id"],"in_attr":t["in_attr"],
            "out_attr":t["out_attr"],"instantiated":0.0,"tmpl_match":t["tmpl_match"],
            "tmpl_where":t["tmpl_where"],"tmpl_effect":t["tmpl_effect"]})
        a.inner.add_edge_unchecked(a.agent,"holds_template",n)
    # the GAP: produce `out` from `value` — no single template does this
    ax=a.s.add_node("CapabilityAxis",{"is_axis":1.0,"in_attr":"value","out_attr":"out","designed":0.0,
                                      "description":"produce out from value"})
    a.inner.add_edge_unchecked(a.agent,"has_gap",ax)
    single=[t["produces_id"] for t in TEMPLATES if t["in_attr"]=="value" and t["out_attr"]=="out"]
    print(f"  gap: value -> out | single template that covers it directly: {single or 'NONE'}")

    # 1. link composable templates: t1 --composes_with--> t2 iff t1.out_attr == t2.in_attr
    a.inner.add_rule({"name":"__link_composable",
      "match":[["ag","holds_template","t1"],["ag","holds_template","t2"]],
      "where":And(Eq(A("t1","out_attr"),A("t2","in_attr")),Not(Eq(A("t1","produces_id"),A("t2","produces_id")))),
      "effects":[["add_edge","t1","composes_with","t2"]]})
    # 2. design-by-composition: a chain t1->t2 whose ENDS match the gap (in=gap.in, out=gap.out) -> mint BOTH
    a.inner.add_rule({"name":"__design_by_composition",
      "match":[["ag","has_gap","ax"],["ag","holds_template","t1"],["t1","composes_with","t2"]],
      "where":And(Eq(A("t1","in_attr"),A("ax","in_attr")),Eq(A("t2","out_attr"),A("ax","out_attr")),
                  Lt(P0("ax","designed"),L(0.5))),
      "effects":[
        ["add_node","rn1","Rule",{"minted":0.0}],["set_attr","rn1","id",{"__term__":A("t1","produces_id")}],
        ["set_attr","rn1","match",{"__term__":A("t1","tmpl_match")}],["set_attr","rn1","where",{"__term__":A("t1","tmpl_where")}],
        ["set_attr","rn1","effect",{"__term__":A("t1","tmpl_effect")}],["add_edge","ax","wants_mint","rn1"],
        ["add_node","rn2","Rule",{"minted":0.0}],["set_attr","rn2","id",{"__term__":A("t2","produces_id")}],
        ["set_attr","rn2","match",{"__term__":A("t2","tmpl_match")}],["set_attr","rn2","where",{"__term__":A("t2","tmpl_where")}],
        ["set_attr","rn2","effect",{"__term__":A("t2","tmpl_effect")}],["add_edge","ax","wants_mint","rn2"],
        ["set_attr","ax","designed",1.0],["set_attr","ax","chain_a",{"__term__":A("t1","produces_id")}],
        ["set_attr","ax","chain_b",{"__term__":A("t2","produces_id")}]]})
    # 3. mint each assembled rule live
    a.inner.add_rule({"name":"__design_mint","match":[["x","wants_mint","rn"]],
      "where":Lt(P0("rn","minted"),L(0.5)),
      "effects":[["set_rule_clause",{"__term__":A("rn","id")},"__mint__",{"__term__":{"type":"Var","name":"rn"}}],
                 ["set_attr","rn","minted",1.0]]})

    n0=a.inner.rule_count()
    for _ in range(6): a.master_tick(); a.tick()
    n1=a.inner.rule_count()
    chain=(a.s.node(ax)["attrs"].get("chain_a"), a.s.node(ax)["attrs"].get("chain_b"))
    print(f"  assembled chain: {chain[0]} -> {chain[1]}   rule_count {n0}->{n1} (+{n1-n0} minted)")

    # GATE: the composed multi-rule faculty fires correctly
    g=a.s.add_node("WorldInstance",{"world_type":"ComposeTest"})
    o=a.s.add_node("Obs",{"value":10.0}); a.inner.add_edge_unchecked(g,"has_obs",o)
    a.inner.run_rules(60)
    h=a.s.node(o)["attrs"].get("h"); out=a.s.node(o)["attrs"].get("out")
    fired = (h==5.0 and out==6.0)
    print(f"  GATE: value=10 -> h={h} (=5?) out={out} (=6?)  composed faculty works={fired}")

    ok = (not single) and chain==("designed_halve","designed_incr") and (n1-n0)==2 and fired and calls["n"]==0
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — the composer reached a MULTI-RULE gap no single template covered: the "
          f"agent linked composable templates, ASSEMBLED the chain halve->incr, minted BOTH rules, and the "
          f"composed faculty fired correctly (10 -> 5 -> 6). Beyond rung-1, graph-native, calls={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
