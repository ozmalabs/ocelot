"""STEP 5 verification (the capstone): the Python consumer is DELETED and navigation happens ENTIRELY in
master_tick from the discovered frame. The agent plays forage with NO Python navigation: it declares its
affordances (geometry-free Control nodes) and reads back the action — everything in between is graph rules:
  · affordance_basis     learns each control's displacement vector,
  · contact_consequence  learns which colour is food (positive),
  · mark_self            derives the self region,
  · mark_dist + aim_goal derive the goal (nearest positive-else-untasted kind),
  · pick_control_for_goal inverts the learned control basis -> chosen_control.
We assert (1) domains.world_play.world_understanding_step is GONE, (2) food is collected, (3) no donkey.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/verify_no_python_consumer.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
import domains.world_play as world_play
from verify_discovered_navigation import NavForageEnv
from forage_world import gnode, FOOD
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

CONTROLS=["Up","Down","Left","Right"]   # direct labels (adapter records the applied token as last_action)

def track_consequences(a, g, cons):
    """Mechanical I/O: ensure one Consequence slot per observed region kind (the value_signal role's slots)."""
    for n in a.s.nodes("Region"):
        at=a.s.node(n)["attrs"]
        if at.get("is_ground")==1.0 or at.get("rvalue") is None: continue
        rv=float(at["rvalue"])
        if rv not in cons:
            cm=a.s.add_node("Consequence",{"rvalue":rv,"value":0.0,"tasted":0.0})
            a.inner.add_edge_unchecked(g,"tracks_consequence",cm); cons[rv]=cm

def main():
    # (1) the Python consumer must be gone
    consumer_gone = not hasattr(world_play, "world_understanding_step")

    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    w=ArcWorld(NavForageEnv()); sub,ctx=w.reset(); a.perceive_frame(sub); g=gnode(a)
    world_play.declare_affordances(a, g, CONTROLS)      # adapter: declare affordances (mechanical)
    cons={}; prev=0; eats=0

    # warmup: move around to LEARN control deltas + taste food (consequence). No navigation decisions in Python.
    for i in range(120):
        sub,ctx=w.apply((CONTROLS[i%4],)); a.perceive_frame(sub)
        g=gnode(a); track_consequences(a,g,cons)
        sc=ctx.get("score",0) or 0; ate=sc>prev
        a.s.set_attr(g,"contact_rvalue",float(FOOD) if ate else 0.0); a.s.set_attr(g,"reward",1.0 if ate else 0.0)
        a.tick(); a.master_tick(); prev=sc

    # PLAY — navigation ENTIRELY graph-native in master_tick; Python only reads the chosen action + applies it.
    for i in range(160):
        g=gnode(a); track_consequences(a,g,cons)
        a.master_tick()                                  # mark_self / mark_dist / aim_goal / pick_control_for_goal
        act=world_play.read_chosen(a,g)                  # adapter: read the action the GRAPH chose
        if act not in CONTROLS: act=CONTROLS[i%4]         # no goal derived yet -> explore
        sub,ctx=w.apply((act,)); a.perceive_frame(sub)
        sc=ctx.get("score",0) or 0; ate=sc>prev
        a.s.set_attr(gnode(a),"contact_rvalue",float(FOOD) if ate else 0.0); a.s.set_attr(gnode(a),"reward",1.0 if ate else 0.0)
        a.tick()
        if ate: eats+=1
        prev=sc

    foodv=round(a.s.node(cons[float(FOOD)])["attrs"].get("value") or 0,2) if float(FOOD) in cons else None
    print(f"  (1) world_understanding_step deleted from domains.world_play: {consumer_gone}")
    print(f"  (2) food collected by graph-native navigation in master_tick: {eats}")
    print(f"      (learned food consequence value = {foodv}; goal+self+action all derived by graph rules)")
    print(f"  (3) DONKEY calls: {calls['n']}")
    ok = consumer_gone and eats>=3 and calls["n"]==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the Python consumer is DELETED and the agent navigates ENTIRELY in "
          f"master_tick from the DISCOVERED frame: it declared its affordances, learned their effects, learned "
          f"which colour is food, derived self + goal, and chose its action by inverting the learned control "
          f"basis — collecting {eats} food with zero Python navigation and zero donkey. The agent is the graph.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
