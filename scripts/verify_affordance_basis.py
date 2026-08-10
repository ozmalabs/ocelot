"""STEP 1 verification: the agent LEARNS each control's displacement vector with NO geometry given. The world
declares four Control nodes (Up/Down/Left/Right) carrying only a name — no (drow,dcol). The agent fires them
and, by observing how its self-region moves, learns each control's effect into a ControlResponse slot. We then
read the self-region's learned slots and check they recovered the true control basis-vectors. Nothing about the
directions is told to the agent; it is discovered from observation.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/verify_affordance_basis.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from forage_world import ForageEnv, gnode
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

CONTROLS=["Up","Down","Left","Right"]  # NAMES only; the agent is told NO geometry for any of them
TRUE={"Up":(-1,0),"Down":(1,0),"Left":(0,-1),"Right":(0,1)}  # ground truth, for scoring ONLY

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    w=ArcWorld(ForageEnv()); sub,ctx=w.reset(); a.perceive_frame(sub)
    g=gnode(a)
    # WORLD declares affordances: a Control node per control, NO geometry, has_control edge from the game.
    for nm in CONTROLS:
        c=a.s.add_node("Control",{"name":nm}); a.inner.add_edge_unchecked(g,"has_control",c)
    # fire each control many times in a fixed rotation; the agent observes its self-region's motion and learns.
    for i in range(160):
        act=CONTROLS[i%4]
        a.s.set_attr(g,"last_action",act)            # the world reports which affordance was just fired
        sub,ctx=w.apply((act,)); a.perceive_frame(sub)
        if ctx.get("over"): sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub)
        a.tick()                                     # mint_control_response + learn_control_delta (clocked)
        a.master_tick()                              # fold next_dr/dc -> dr/dc
        g=gnode(a)
    # read the SELF region (highest respond_votes) and its learned ControlResponse per control
    self_r=max((n for n in a.s.nodes("Region") if a.s.node(n)["attrs"].get("is_ground")!=1.0),
               key=lambda n:a.s.node(n)["attrs"].get("respond_votes") or 0, default=None)
    learned={}
    if self_r is not None:
        for cr in a.inner.neighbours(self_r,"responds_via"):
            at=a.s.node(cr)["attrs"]; learned[at.get("cname")]=(round(at.get("dr") or 0,2),round(at.get("dc") or 0,2))
    print("  controls declared with NO geometry:",CONTROLS)
    print("  LEARNED control basis-vectors (self region, from observation):")
    ok=True
    for nm in CONTROLS:
        got=learned.get(nm); want=TRUE[nm]
        hit = got is not None and abs(got[0]-want[0])<0.34 and abs(got[1]-want[1])<0.34
        ok = ok and hit
        print(f"    {nm:5s} learned={got}  true={want}  {'OK' if hit else 'MISS'}")
    print(f"  DONKEY calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok and calls['n']==0 else 'PARTIAL'} — the agent DISCOVERED each control's "
          f"displacement vector from OBSERVATION alone (controls carried no geometry), recovering the basis "
          f"the world never gave it. One affordance-generic rule, graph-native, donkey={calls['n']}. "
          f"This is the basis nd_basis_discovery (step 2: principal_axes) turns into the discovered frame's axes.")
    print("="*96)
    return 0 if (ok and calls["n"]==0) else 1

if __name__=="__main__":
    raise SystemExit(main())
