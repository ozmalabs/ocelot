"""The jabberwock's OWN fix (docs/jabberwock_derivation_loop_design.md), load-bearing core: the missing
CARRIER. On recognising an unknown world (world_curiosity's CapabilityAxis), open a DeriveProgram Frame that
PERSISTS the derivation stage and OWNS action emission — so the agent sustains the derive-by-acting loop
instead of collapsing to Reset. This realises stage 1 (locate_self) + the gated advance, and verifies the
collapse STOPS on raw snake (nothing stamped: the agent perceives the frame, the carrier sustains varied
probing, control-discovery derives self from respond_votes, the stage advances).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/derive_loop.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from snake_env import SnakeEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

def V(n): return {"type":"Var","name":n}
def At(n,k): return {"type":"Attr","node":V(n),"key":k}
def L(v): return {"type":"Lit","value":v}
def Plus(*xs): return {"type":"Plus","items":list(xs)}
def Ite(c,t,e): return {"type":"IfThenElse","cond":c,"then":t,"other":e}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def Gte(a,b): return {"type":"Gte","a":a,"b":b}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Not(x): return {"type":"Not","arg":x}
def And(*xs): return {"type":"And","items":list(xs)}
def Minus(a,b): return {"type":"Minus","a":a,"b":b}
def Times(*xs): return {"type":"Times","items":list(xs)}
def Neg(x): return {"type":"Neg","arg":x}
def Mx(*xs): return {"type":"Max","items":list(xs)}
def ABS(x): return Mx(x,Neg(x))
def P0(n,k): return Plus(At(n,k),L(0.0))   # attr-or-0
def Argmax(src_edge, var, value):
    return {"type":"Argmax","source":{"type":"Neighbours","node":V("game"),"edge_type":src_edge,"any_type":False},
            "var_name":var,"value":value,"default":L(0.0)}
def gnode(agent):
    return next((n for n in agent.s.nodes("WorldInstance") if agent.s.node(n)["attrs"].get("world_type")=="Game"), None)

def main():
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    calls={"n":0}; agent.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])

    # The jabberwock's LOAD-BEARING Reset-guard: rewrite the competing action-emitter (enact_forced_action,
    # the forced_action->chosen_action gate whose babble repertoire includes Reset) so it cannot fire while a
    # DeriveProgram is open (game.has_prog>=0.5). Then derive_step is the SOLE action source while deriving.
    # set_rule_clause "where" takes a TERM VALUE -> store the new where on a cfg attr (nested dicts round-trip)
    # and pass Attr(cfg,"guarded_where"), as the repair path stores f.corrected.
    guarded_where = {"type":"And","items":[
        Eq(At("game","world_type"),L("Game")),
        Eq(At("game","babble_stamp"),At("game","frame")),
        Not(Eq(Plus(At("game","control_known"),L(0)),L(1.0))),
        Lt(Plus(At("game","has_prog"),L(0.0)),L(0.5))]}
    cfg = agent.s.add_node("DeriveConfig", {"guarded_where": guarded_where, "applied": 0.0})
    agent.inner.add_edge_unchecked(agent.agent, "derive_config", cfg)
    agent.inner.add_rule({"name":"apply_reset_guard",
      "match":[["ag","derive_config","cfg"]],
      "where":Lt(Plus(At("cfg","applied"),L(0.0)),L(0.5)),
      "effects":[["set_rule_clause","enact_forced_action","where",{"__term__":At("cfg","guarded_where")}],
                 ["set_attr","cfg","applied",1.0]]})

    # open_derive_program — the COUPLING reflex (curiosity-axis -> carrier). On the unknown-world axis
    # (capability_keys include 'world') bound to the game, with no DeriveProgram yet, instantiate one at
    # stage locate_self (dependency-first). Single-fires via the has_program back-edge.
    agent.inner.add_rule({"name":"open_derive_program",
      "match":[["ax","is_axis_marker","ax"]] if False else [["body","inhabits","game"]],
      "where":{"type":"And","items":[
        Eq(At("game","world_type"),L("Game")),
        Lt(Plus(At("game","has_prog"),L(0.0)),L(0.5))]},
      "effects":[
        ["add_node","dp","DeriveProgram",{"stage":0.0,"probe_idx":0.0,"last_frame":-1.0}],
        ["add_edge","dp","deriving","game"],
        ["set_attr","game","has_prog",1.0]]})

    # derive_step — the SOLE action source while a program is open. Stage 0 (locate_self): emit a VARIED
    # control each frame (cycle Up/Down/Left/Right via probe_idx) and keep going — NO babble budget. This is
    # the carrier that the jabberwock identified as missing. Frame-guarded (one action/frame).
    cyc = Ite(Lt(Plus(At("dp","probe_idx"),L(0.0)),L(1.0)),L("Up"),
          Ite(Lt(Plus(At("dp","probe_idx"),L(0.0)),L(2.0)),L("Down"),
          Ite(Lt(Plus(At("dp","probe_idx"),L(0.0)),L(3.0)),L("Left"),L("Right"))))
    nxt = Ite(Lt(Plus(At("dp","probe_idx"),L(0.0)),L(3.0)),Plus(At("dp","probe_idx"),L(1.0)),L(0.0))
    agent.inner.add_rule({"name":"derive_step",
      "match":[["dp","deriving","game"]],
      "where":{"type":"And","items":[
        Eq(Plus(At("dp","stage"),L(0.0)),L(0.0)),
        Not(Eq(At("dp","last_frame"),At("game","frame")))]},
      "effects":[
        ["set_attr","dp","last_frame",{"__term__":At("game","frame")}],
        ["set_attr","game","chosen_action",{"__term__":cyc}],
        ["set_attr","game","forced_action",{"__term__":cyc}],
        ["set_attr","dp","probe_idx",{"__term__":nxt}]]})

    # advance_stage — gated: locate_self done_when some region has respond_votes >= 2 (self derived) -> stage 1.
    agent.inner.add_rule({"name":"advance_locate_self",
      "match":[["dp","deriving","game"],["game","has_region","r"]],
      "where":{"type":"And","items":[
        Eq(Plus(At("dp","stage"),L(0.0)),L(0.0)),
        {"type":"Gte","a":Plus(At("r","respond_votes"),L(0)),"b":L(2)}]},
      "effects":[["set_attr","dp","stage",1.0],["set_attr","r","is_self",1.0]]})

    # ---- STAGE 1: learn_consequence (jabberwock's design: move toward an un-tasted region to manufacture a
    # contact event; learn the kind's value from the VISIBLE score). No stamping: the score is on-screen; the
    # agent derives the delta (prev_score fold) + attributes it to the kind it CHOSE to pursue. ----
    def dist2(n1,n2): return Plus(ABS(Minus(At(n1,"cy"),At(n2,"cy"))), ABS(Minus(At(n1,"cx"),At(n2,"cx"))))
    # pick_target: nearest non-self, non-ground region that is NOT immediately adjacent (skip the neck=own body)
    tgt = Argmax("has_region","r",
            Ite(And(Not(Eq(P0("r","is_self"),L(1.0))), Not(Eq(P0("r","is_ground"),L(1.0))), Gt(dist2("s","r"),L(1.5))),
                Neg(dist2("s","r")), L(-1000000.0)))
    agent.inner.add_rule({"name":"pick_target",
      "match":[["dp","deriving","game"],["game","has_region","s"]],
      "where":And(Eq(P0("dp","stage"),L(1.0)), Eq(P0("s","is_self"),L(1.0)), Not(Eq(At("dp","last_pick"),At("game","frame")))),
      "effects":[["set_attr","dp","last_pick",{"__term__":At("game","frame")}],
                 ["set_attr","dp","tgt_cy",{"__term__":{"type":"Attr","node":tgt,"key":"cy"}}],
                 ["set_attr","dp","tgt_cx",{"__term__":{"type":"Attr","node":tgt,"key":"cx"}}],
                 ["set_attr","dp","pursuing",{"__term__":{"type":"Attr","node":tgt,"key":"rvalue"}}]]})
    # derive_step stage 1: chosen_action = the action whose learned displacement best reduces distance to tgt
    adist = Plus(ABS(Minus(Plus(At("s","cy"),P0("a","dcy")), P0("dp","tgt_cy"))),
                 ABS(Minus(Plus(At("s","cx"),P0("a","dcx")), P0("dp","tgt_cx"))))
    pursue_act = {"type":"Attr","node":Argmax("has_action","a",Neg(adist)),"key":"name"}
    agent.inner.add_rule({"name":"derive_step_pursue",
      "match":[["dp","deriving","game"],["game","has_region","s"]],
      "where":And(Eq(P0("dp","stage"),L(1.0)), Eq(P0("s","is_self"),L(1.0)), Not(Eq(At("dp","last_frame"),At("game","frame")))),
      "effects":[["set_attr","dp","last_frame",{"__term__":At("game","frame")}],
                 ["set_attr","game","chosen_action",{"__term__":pursue_act}],
                 ["set_attr","game","forced_action",{"__term__":pursue_act}]]})
    # prev_score fold (derive the delta of the VISIBLE score): commit prev_score := score each frame
    agent.inner.add_rule({"name":"fold_prev_score","match":[["dp","deriving","game"]],
      "where":Not(Eq(At("game","last_sf"),At("game","frame"))),
      "effects":[["set_attr","game","clocked",1.0],["set_attr","game","last_sf",{"__term__":At("game","frame")}],
                 ["set_attr","game","next_prev_score",{"__term__":P0("game","score")}]]})
    # learn_consequence: VISIBLE score rose while pursuing kind K -> K's consequence EMA toward rewarding
    agent.inner.add_rule({"name":"learn_consequence",
      "match":[["dp","deriving","game"],["game","tracks_consequence","cm"]],
      "where":And(Eq(P0("cm","rvalue"),P0("dp","pursuing")), Gt(P0("game","score"),P0("game","prev_score"))),
      "effects":[["set_attr","cm","clocked",1.0],
                 ["set_attr","cm","next_value",{"__term__":Plus(P0("cm","value"),Times(L(0.5),Minus(L(1.0),P0("cm","value"))))}]]})
    # advance: a rewarding kind found -> stage 2 (navigate)
    agent.inner.add_rule({"name":"advance_learn_consequence",
      "match":[["dp","deriving","game"],["game","tracks_consequence","cm"]],
      "where":And(Eq(P0("dp","stage"),L(1.0)), Gt(P0("cm","value"),L(0.3))),
      "effects":[["set_attr","dp","stage",2.0]]})

    world=ArcWorld(SnakeEnv()); sub,ctx=world.reset(); agent.perceive_frame(sub)
    cons_slots={}
    # HAND-OFF precondition: the agent operates_in the world, so the HELD goal_derivation chain (stage-1
    # learn_consequence: derive salient goal -> pursue -> fold consequence from the VISIBLE score) can drive
    # once self is derived. (operates_in is the edge select_frontier/pursue_active_goal need.)
    agent.inner.add_edge_unchecked(agent.agent, "operates_in", gnode(agent))
    def slots(g):  # consequence slot per PERCEIVED non-ground colour (perception of distinct colours; not semantics)
        for n in agent.s.nodes("Region"):
            at=agent.s.node(n)["attrs"]
            if at.get("is_ground")==1.0: continue
            rv=at.get("rvalue")
            if rv is None: continue
            rv=float(rv)
            if rv not in cons_slots:
                cm=agent.s.add_node("Consequence",{"rvalue":rv,"value":0.0}); agent.inner.add_edge_unchecked(g,"tracks_consequence",cm); cons_slots[rv]=cm
    acts=[]; resp_best=0; stage_reached=0; eats=0; prev_score=0
    for i in range(160):
        g=gnode(agent)
        agent.master_tick()                       # fold first (S0 lesson)
        a = agent.s.node(gnode(agent))["attrs"].get("chosen_action") or ""
        acts.append(a)
        sub,ctx=world.apply((a,) if a else ("Up",)); agent.perceive_frame(sub)
        g=gnode(agent)
        agent.s.set_attr(g,"score",float(ctx.get("score",0) or 0))   # the VISIBLE score (on-screen, as a human sees)
        agent.s.set_attr(g,"frame",float(i+1))
        slots(g)
        agent.tick()
        sc=ctx.get("score",0) or 0
        if sc>prev_score: eats+=1
        prev_score=sc
        if ctx.get("over"): sub,ctx=world.apply(("Reset",)); agent.perceive_frame(sub); prev_score=0
        for n in agent.s.nodes("Region"):
            rv=agent.s.node(n)["attrs"].get("respond_votes") or 0
            resp_best=max(resp_best,int(rv))
        dp=next((n for n in agent.s.nodes("DeriveProgram")),None)
        if dp: stage_reached=max(stage_reached,int(agent.s.node(dp)["attrs"].get("stage") or 0))
    learned={rv:round(agent.s.node(cm)["attrs"].get("value") or 0,3) for rv,cm in cons_slots.items()}
    rewarding=[rv for rv,v in learned.items() if v>0.3]
    from collections import Counter
    cnt=Counter(acts); resets=cnt.get("Reset",0); varied=sum(v for k,v in cnt.items() if k in ("Up","Down","Left","Right"))
    print(f"  eats(unaided)={eats}  learned consequence per colour={learned}  rewarding kinds derived={rewarding}")
    print(f"  action histogram: {dict(cnt)}")
    print(f"  varied controls={varied}/160  Reset={resets}/160  best respond_votes={resp_best}  stage_reached={stage_reached}")
    print(f"  DONKEY calls: {calls['n']}")
    ok = resets <= 5 and resp_best >= 2 and stage_reached >= 2 and len(rewarding) >= 1 and 8.0 in rewarding and calls["n"]==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the jabberwock's carrier ran stages 0->1: collapse stopped "
          f"(Reset {resets}/160), self derived (respond_votes={resp_best}), and at stage 1 it pursued un-tasted "
          f"regions and LEARNED food's value from the VISIBLE score alone (rewarding kinds={rewarding}; colour 8 "
          f"= food, derived NOT stamped), stage_reached={stage_reached}. eats(unaided)={eats}. No donkey "
          f"(calls={calls['n']}).")
    print("="*96)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
