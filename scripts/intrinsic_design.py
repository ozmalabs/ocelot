"""INTRINSIC DESIGN — no donkey-in-the-car. The jabberwock designs a faculty for a gap using ONLY its own
graph faculties: it classifies the gap by its OWN shape-classifier (categorise_by_shape), SELECTS the held
faculty of matching shape (analogy — the agent's design DECISION), and composes+mints it from held clause-
trees. The external claude -p channel (make_ask / set_self_teacher) is wired to a SPY that records any call,
to PROVE the donkey is never used.

Strategy dispatch (the agent decides): cheap-first ANALOGY — find a held template whose shape == the gap's
shape and copy+mint it. (Search-over-primitives and HumanImpasse are the next rungs; this proves rung 1 +
the shape-driven decision + the no-donkey guarantee.)

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/intrinsic_design.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.teach import categorise_by_shape

def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}

# Two held faculty TEMPLATES (small valid clause-trees), each with a human-readable description the agent
# will classify ITSELF. The produced rule is toy but VALID (compiles + is distinct) — the point is the
# shape-driven SELECTION + intrinsic mint, not the faculty's depth.
PREDICTOR = {"produces_id":"designed_predict",
  "description":"predict the next value of an observable from its current value (a forward expectation)",
  "tmpl_match":[["game","has_obs","o"]], "tmpl_where":{"type":"Lit","value":True},
  "tmpl_effect":[["set_attr","o","pred",{"__term__":A("o","value")}]]}
SELECTOR = {"produces_id":"designed_select",
  "description":"select the winner among candidate actions by argmax, lateral inhibition, winner-take-all",
  "tmpl_match":[["game","has_choice","c"]], "tmpl_where":{"type":"Lit","value":True},
  "tmpl_effect":[["set_attr","c","picked",{"__term__":{"type":"Lit","value":1.0}}]]}

def main():
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    # --- wire the DONKEY to a spy: any design call to the external channel is recorded (must stay 0) ---
    calls = {"n":0}
    def donkey_spy(q):
        calls["n"] += 1
        return "DONKEY WAS USED"
    agent.set_self_teacher(donkey_spy)

    # --- the agent holds two templates; it classifies EACH by its OWN shape-classifier ---
    holds = []
    for tmpl in (PREDICTOR, SELECTOR):
        shape = categorise_by_shape(agent, "ClauseTemplate", {"description": tmpl["description"]})
        t = agent.s.add_node("ClauseTemplate", {"produces_id":tmpl["produces_id"],"addresses_shape":shape or "",
            "instantiated":0.0,"tmpl_match":tmpl["tmpl_match"],"tmpl_where":tmpl["tmpl_where"],"tmpl_effect":tmpl["tmpl_effect"]})
        agent.inner.add_edge_unchecked(agent.agent, "holds_template", t)
        holds.append((tmpl["produces_id"], shape, t))
        print(f"  held template '{tmpl['produces_id']}' -> agent classified shape = {shape!r}", flush=True)

    # --- a DESIGN GAP: a capability the agent needs; it classifies the gap by the SAME classifier ---
    gap_desc = "predict the next observation so I anticipate what the world does"
    gap_shape = categorise_by_shape(agent, "CapabilityAxis", {"description": gap_desc})
    ax = agent.s.add_node("CapabilityAxis", {"is_axis":1.0,"description":gap_desc,"shape":gap_shape or "","designed":0.0})
    agent.inner.add_edge_unchecked(agent.agent, "has_gap", ax)
    print(f"\n  DESIGN GAP: {gap_desc!r}\n  -> agent classified gap shape = {gap_shape!r}", flush=True)

    # --- DISPATCHER (graph rule): design_by_analogy — match a gap to the held template of the SAME shape
    #     (the agent's own decision, by shape), build the Rule by copying the template's clause-trees, mark
    #     wants_mint. No teacher, no claude -p. ---
    agent.inner.add_rule({"name":"__design_by_analogy",
      "match":[["ag","has_gap","ax"],["ag","holds_template","t"]],
      "where":{"type":"And","items":[
        {"type":"Eq","a":A("ax","shape"),"b":A("t","addresses_shape")},
        {"type":"Lt","a":{"type":"Plus","items":[A("t","instantiated"),{"type":"Lit","value":0.0}]},"b":{"type":"Lit","value":0.5}},
        {"type":"Lt","a":{"type":"Plus","items":[A("ax","designed"),{"type":"Lit","value":0.0}]},"b":{"type":"Lit","value":0.5}}]},
      "effects":[
        ["add_node","rn","Rule",{"minted":0.0}],
        ["set_attr","rn","id",{"__term__":A("t","produces_id")}],
        ["set_attr","rn","match",{"__term__":A("t","tmpl_match")}],
        ["set_attr","rn","where",{"__term__":A("t","tmpl_where")}],
        ["set_attr","rn","effect",{"__term__":A("t","tmpl_effect")}],
        ["add_edge","ax","wants_mint","rn"],
        ["set_attr","t","instantiated",1.0],
        ["set_attr","ax","designed",1.0],
        ["set_attr","ax","designed_from",{"__term__":A("t","produces_id")}]]})
    # the proven mint reflex (set_rule_clause __mint__)
    agent.inner.add_rule({"name":"__design_mint",
      "match":[["x","wants_mint","rn"]],
      "where":{"type":"Lt","a":{"type":"Plus","items":[A("rn","minted"),{"type":"Lit","value":0.0}]},"b":{"type":"Lit","value":0.5}},
      "effects":[["set_rule_clause",{"__term__":A("rn","id")},"__mint__",{"__term__":{"type":"Var","name":"rn"}}],
                 ["set_attr","rn","minted",1.0]]})

    n0 = agent.inner.rule_count()
    for _ in range(4): agent.master_tick(); agent.tick()
    n1 = agent.inner.rule_count()

    designed_from = agent.s.node(ax)["attrs"].get("designed_from")
    # which template was instantiated?
    inst = [pid for (pid,sh,t) in holds if agent.s.node(t)["attrs"].get("instantiated")==1.0]
    print(f"\n  agent DESIGNED from template: {designed_from!r}  (instantiated: {inst})")
    print(f"  rule_count {n0} -> {n1}  (+{n1-n0} minted live)")
    print(f"  DONKEY (make_ask/claude -p) calls: {calls['n']}")
    ok = (designed_from == "designed_predict" and "designed_select" not in inst
          and n1 == n0 + 1 and calls["n"] == 0)
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — the jabberwock DESIGNED a faculty with NO donkey-in-the-car: it "
          f"classified the gap by its OWN shape-classifier ({gap_shape!r}), SELECTED the held faculty of "
          f"matching shape (analogy, not the mismatched selector), composed it from held clause-trees, and "
          f"MINTED it live — the external claude -p channel was NEVER called (calls=0).")
    print("="*96)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
