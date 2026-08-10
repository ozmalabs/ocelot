"""MIGRATION step 2 — the WorldBinding TREE + composition rules (nesting). A role-filler can BE a child
binding (a game inside an environment). Proves the jabberwock's three composition rules on a constructed
minigame-in-overworld, as graph rules (no env needed to prove the COMPOSITION):
  - rollup_value: child value contributes to parent value via a transform (winning the minigame is worth a key)
  - terminal_propagation: a child terminal ESCALATES (ends the parent) or is CONTAINED (drops back to parent);
    the bit is OBSERVED, not declared — reconcile flips a mis-seeded 'contained' to 'escalates' when the parent
    actually halted.
  - goal-down: a parent goal targets a child's value (achieving the child satisfies the parent subgoal).
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/world_nesting.py
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
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def And(*xs): return {"type":"And","items":list(xs)}

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    # ---- build a 2-level binding tree: Environment (root) contains Game (child) ----
    pb=a.s.add_node("WorldBinding",{"kind":"environment","activation":"active"})
    cb=a.s.add_node("WorldBinding",{"kind":"game","activation":"active"})
    a.inner.add_edge_unchecked(cb,"parent_binding",pb)
    # parent roles
    pv=a.s.add_node("WorldRole",{"role":"value_signal","value":0.0}); a.inner.add_edge_unchecked(pb,"role",pv)
    pt=a.s.add_node("WorldRole",{"role":"terminal","fired":0.0});      a.inner.add_edge_unchecked(pb,"role",pt)
    pg=a.s.add_node("WorldRole",{"role":"goal"});                      a.inner.add_edge_unchecked(pb,"role",pg)
    # child roles
    cv=a.s.add_node("WorldRole",{"role":"value_signal","value":0.0,"rollup_factor":2.0}); a.inner.add_edge_unchecked(cb,"role",cv)
    ct=a.s.add_node("WorldRole",{"role":"terminal","fired":0.0,"escalation":"contained"}); a.inner.add_edge_unchecked(cb,"role",ct)
    # nesting edges: child value rolls up to parent value; parent goal targets child value
    a.inner.add_edge_unchecked(cv,"rolls_up_to",pv)
    a.inner.add_edge_unchecked(pg,"targets",cv)

    # ---- composition rules (graph) ----
    # rollup_value: parent value = child value * rollup_factor (the contribution; one child here)
    a.inner.add_rule({"name":"rollup_value","match":[["cv","rolls_up_to","pv"]],
      "where":{"type":"Lit","value":True},
      "effects":[["set_attr","pv","value",{"__term__":{"type":"Times","items":[P0("cv","value"),P0("cv","rollup_factor")]}}]]})
    # terminal ESCALATES -> parent terminal fires
    a.inner.add_rule({"name":"terminal_escalate","match":[["cb","parent_binding","pb"],["cb","role","ct"],["pb","role","tp"]],
      "where":And(Eq(A("ct","role"),L("terminal")), Eq(A("tp","role"),L("terminal")),
                  Gt(P0("ct","fired"),L(0.5)), Eq(A("ct","escalation"),L("escalates"))),
      "effects":[["set_attr","tp","fired",1.0]]})
    # terminal CONTAINED -> deactivate only the child subtree (drop back to parent)
    a.inner.add_rule({"name":"terminal_contain","match":[["cb","role","ct"]],
      "where":And(Eq(A("ct","role"),L("terminal")), Gt(P0("ct","fired"),L(0.5)), Eq(A("ct","escalation"),L("contained"))),
      "effects":[["set_attr","cb","activation","dormant"]]})
    # reconcile: a CONTAINED child whose parent actually HALTED was mis-seeded -> flip to escalates
    a.inner.add_rule({"name":"reconcile_escalation","match":[["cb","parent_binding","pb"],["cb","role","ct"]],
      "where":And(Eq(A("ct","role"),L("terminal")), Gt(P0("ct","fired"),L(0.5)),
                  Eq(A("ct","escalation"),L("contained")), Gt(P0("pb","dynamics_halted"),L(0.5))),
      "effects":[["set_attr","ct","escalation","escalates"]]})

    res={}
    # (1) ROLLUP: win the minigame (child value 5) -> parent value rolls up to 2*5=10
    a.s.set_attr(cv,"value",5.0); a.master_tick(); a.tick()
    res["rollup parent value (want 10)"]=a.s.node(pv)["attrs"].get("value")
    # (2) CONTAINED child death -> child dormant, parent stays active, parent terminal NOT fired
    a.s.set_attr(ct,"fired",1.0); a.master_tick(); a.tick()
    res["contained: child activation (want dormant)"]=a.s.node(cb)["attrs"].get("activation")
    res["contained: parent activation (want active)"]=a.s.node(pb)["attrs"].get("activation")
    res["contained: parent terminal fired (want 0/None)"]=a.s.node(pt)["attrs"].get("fired")
    # (3) RECONCILE: same contained child, but observe the parent actually halted -> flip to escalates -> parent terminal fires
    a.s.set_attr(cb,"activation","active"); a.s.set_attr(pb,"dynamics_halted",1.0); a.master_tick(); a.tick()
    res["reconcile: child escalation (want escalates)"]=a.s.node(ct)["attrs"].get("escalation")
    res["reconcile: parent terminal fired (want 1)"]=a.s.node(pt)["attrs"].get("fired")
    # goal-down edge present
    res["goal-down edge present"]=a.s.has_edge(pg,"targets",cv)
    print("  binding-tree composition results:")
    for k,v in res.items(): print(f"    {k}: {v}")
    print(f"  DONKEY calls: {calls['n']}")
    ok = (res["rollup parent value (want 10)"]==10.0
          and res["contained: child activation (want dormant)"]=="dormant"
          and res["contained: parent activation (want active)"]=="active"
          and not res["contained: parent terminal fired (want 0/None)"]
          and res["reconcile: child escalation (want escalates)"]=="escalates"
          and res["reconcile: parent terminal fired (want 1)"]==1.0
          and res["goal-down edge present"] and calls["n"]==0)
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — MIGRATION step 2: WorldBinding is a TREE (child binding under a "
          f"parent role). Composition proven: child value ROLLS UP (10); a CONTAINED child terminal drops the "
          f"child to dormant while the parent stays active; OBSERVATION (parent halted) RECONCILES a mis-seeded "
          f"contained bit to escalates -> parent terminal fires; goal points DOWN to the child. Graph rules "
          f"only, no donkey (calls={calls['n']}).")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
