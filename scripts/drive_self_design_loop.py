"""DRIVE THE REAL AGENT: the self-design loop END-TO-END, no LLM. One pass, all on the agent's own machinery:
  1. CHOOSE   — the agent's own frontier_pick (the real Argmax in autonomy.json, run via a.inner.evaluate)
                selects the self_design CapabilityAxis: it elects to design.
  2. KNOW-HOW — drive(self_design) reports its design strategy from its own machinery.
  3. RECOGNISE— a DESIGN GAP (a capability it lacks), classified by its OWN categorise_by_shape.
  4. DESIGN   — design_by_analogy: it selects the held template of matching shape and builds a Rule from its
                clause-trees (the agent's decision, by shape), then __design_mint mints it LIVE (set_rule_clause).
  5. GATE     — the minted rule actually FIRES on a test input (the bench): the designed faculty works.
A donkey-spy proves the external LLM channel is never called (calls must stay 0).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/drive_self_design_loop.py
"""
from __future__ import annotations
import os, sys, json
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.teach import categorise_by_shape
from domains import reflective_faculty as rf

def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}
def frontier_pick_term():
    d=json.load(open(os.path.join(ROOT,"seeds","autonomy.json"))); box={}
    def walk(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if k=="frontier_pick_term" and isinstance(v,str): box["t"]=json.loads(v)
                else: walk(v)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d); return box["t"]

# held faculty templates (the agent classifies each by its OWN shape-classifier)
PREDICTOR={"produces_id":"designed_predict",
  "description":"predict the next value of an observable from its current value (a forward expectation)",
  "tmpl_match":[["game","has_obs","o"]],"tmpl_where":{"type":"Lit","value":True},
  "tmpl_effect":[["set_attr","o","pred",{"__term__":A("o","value")}]]}
SELECTOR={"produces_id":"designed_select",
  "description":"select the winner among candidate actions by argmax, lateral inhibition, winner-take-all",
  "tmpl_match":[["game","has_choice","c"]],"tmpl_where":{"type":"Lit","value":True},
  "tmpl_effect":[["set_attr","c","picked",{"__term__":{"type":"Lit","value":1.0}}]]}

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])

    # 0. RECOGNISE a gap first — mint a DesignGap so the gate elects self_design (it is otherwise saturated,
    #    so the agent only designs when it actually has a gap). This is the principled order: gap -> gate -> choose.
    a.s.add_node("DesignGap",{"open":1.0,"description":"a faculty I lack and want to build"})
    for _ in range(3): a.tick()                          # gate_self_design_on_gap fires -> self_design unsaturated

    # 1. CHOOSE — the agent's own selector elects self_design
    fpt=frontier_pick_term()
    sd=next((n for n in a.s.nodes("CapabilityAxis") if a.s.node(n)["attrs"].get("name")=="self_design"),None)
    choice=a.inner.evaluate(fpt)
    chose=str(choice)==str(sd)
    print(f"  1. CHOOSE   frontier_pick selects: {choice} -> self_design = {chose}")

    # 2. KNOW-HOW — it reports its design strategy from its own machinery
    how=rf.reflect("self_design",None,a.s)
    print(f"  2. KNOW-HOW drive(self_design): composable={how.get('composable_machinery')} "
          f"strategy_steps={len(how.get('design_strategy',[]))}")

    # 3. RECOGNISE — hold templates (classified by shape) + a design gap (same classifier)
    holds=[]
    for tmpl in (PREDICTOR,SELECTOR):
        shape=categorise_by_shape(a,"ClauseTemplate",{"description":tmpl["description"]})
        t=a.s.add_node("ClauseTemplate",{"produces_id":tmpl["produces_id"],"addresses_shape":shape or "",
            "instantiated":0.0,"tmpl_match":tmpl["tmpl_match"],"tmpl_where":tmpl["tmpl_where"],"tmpl_effect":tmpl["tmpl_effect"]})
        a.inner.add_edge_unchecked(a.agent,"holds_template",t); holds.append((tmpl["produces_id"],t))
    gap_desc="predict the next observation so I anticipate what the world does"
    gap_shape=categorise_by_shape(a,"CapabilityAxis",{"description":gap_desc})
    ax=a.s.add_node("CapabilityAxis",{"is_axis":1.0,"description":gap_desc,"shape":gap_shape or "","designed":0.0})
    a.inner.add_edge_unchecked(a.agent,"has_gap",ax)
    print(f"  3. RECOGNISE gap {gap_desc!r} -> shape={gap_shape!r}")

    # 4. DESIGN+MINT — the agent's design-by-analogy + mint rules (its own decision, by shape)
    a.inner.add_rule({"name":"__design_by_analogy",
      "match":[["ag","has_gap","ax"],["ag","holds_template","t"]],
      "where":{"type":"And","items":[{"type":"Eq","a":A("ax","shape"),"b":A("t","addresses_shape")},
        {"type":"Lt","a":{"type":"Plus","items":[A("t","instantiated"),{"type":"Lit","value":0.0}]},"b":{"type":"Lit","value":0.5}},
        {"type":"Lt","a":{"type":"Plus","items":[A("ax","designed"),{"type":"Lit","value":0.0}]},"b":{"type":"Lit","value":0.5}}]},
      "effects":[["add_node","rn","Rule",{"minted":0.0}],["set_attr","rn","id",{"__term__":A("t","produces_id")}],
        ["set_attr","rn","match",{"__term__":A("t","tmpl_match")}],["set_attr","rn","where",{"__term__":A("t","tmpl_where")}],
        ["set_attr","rn","effect",{"__term__":A("t","tmpl_effect")}],["add_edge","ax","wants_mint","rn"],
        ["set_attr","t","instantiated",1.0],["set_attr","ax","designed",1.0],
        ["set_attr","ax","designed_from",{"__term__":A("t","produces_id")}]]})
    a.inner.add_rule({"name":"__design_mint","match":[["x","wants_mint","rn"]],
      "where":{"type":"Lt","a":{"type":"Plus","items":[A("rn","minted"),{"type":"Lit","value":0.0}]},"b":{"type":"Lit","value":0.5}},
      "effects":[["set_rule_clause",{"__term__":A("rn","id")},"__mint__",{"__term__":{"type":"Var","name":"rn"}}],
                 ["set_attr","rn","minted",1.0]]})
    n0=a.inner.rule_count()
    for _ in range(4): a.master_tick(); a.tick()
    n1=a.inner.rule_count()
    designed_from=a.s.node(ax)["attrs"].get("designed_from")
    print(f"  4. DESIGN   from template {designed_from!r}; rule_count {n0}->{n1} (+{n1-n0} minted live)")

    # 5. GATE/BENCH — the minted faculty actually FIRES on a fresh input
    g=a.s.add_node("WorldInstance",{"world_type":"DesignTest"})
    o=a.s.add_node("Obs",{"value":42.0}); a.inner.add_edge_unchecked(g,"has_obs",o)
    a.inner.run_rules(50)
    pred=a.s.node(o)["attrs"].get("pred")
    fired = pred==42.0
    print(f"  5. GATE     designed rule fired on a fresh input: obs.value=42 -> obs.pred={pred}  (works={fired})")

    ok = chose and designed_from=="designed_predict" and (n1==n0+1) and fired and calls["n"]==0
    print(f"  DONKEY/LLM calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — the self-design loop ran END-TO-END on the real agent, no LLM: it "
          f"CHOSE self_design (its own frontier_pick), recognised a gap, DESIGNED+MINTED a fireable rule by "
          f"analogy from its held machinery, and the designed faculty FIRED on a fresh input (gate). "
          f"calls={calls['n']}. The agent designed and installed a working faculty for itself.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
