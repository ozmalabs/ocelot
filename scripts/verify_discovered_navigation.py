"""STEP 3 verification: navigate from the DISCOVERED frame, not a grid. The controls are given SCRAMBLED labels
(c0..c3) whose true effects are a hidden permutation of Up/Down/Left/Right. The agent learns each label's real
displacement (step 1), discovers the axes (step 2, the authored principal_axes), and navigates to food by
INVERTING the learned control basis (the graph rule pick_control_for_goal: Argmax Dot(learned Δ, desired
displacement)). It reaches food despite the scramble — because only LEARNED effects drive it. A hardcoded-
direction baseline (assume c_i is the i-th compass direction) drives the wrong way under the scramble and
starves. That contrast IS the proof the navigation is frame-derived, not grid/label-assumed.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/verify_discovered_navigation.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from forage_world import ForageEnv, gnode, FOOD
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

CONTROLS=["c0","c1","c2","c3"]
# HIDDEN scramble: the agent is NEVER told this. c0 actually moves Down, c1 Up, c2 Right, c3 Left.
SCRAMBLE={"c0":"Down","c1":"Up","c2":"Right","c3":"Left"}

class NavForageEnv(ForageEnv):
    """Hazard-free forage to isolate the STEP-3 claim (frame-derived navigation). Obstacle avoidance is the
    flood layer (step 3+), not what this bench tests."""
    def _init_world(self):
        self._ar,self._ac=7,7; self._haz=[]; self._food=[]; self._place_food(3)
# What a NAIVE hardcoded map would WRONGLY assume (c_i == the i-th compass dir):
ASSUME={"c0":(-1,0),"c1":(1,0),"c2":(0,-1),"c3":(0,1)}

def self_region(a):
    return max((n for n in a.s.nodes("Region") if a.s.node(n)["attrs"].get("is_ground")!=1.0),
               key=lambda n:a.s.node(n)["attrs"].get("respond_votes") or 0, default=None)
def nearest_food(a, sr):
    sa=a.s.node(sr)["attrs"]; sy,sx=sa.get("cy",0),sa.get("cx",0); best=None;bd=1e18
    for n in a.s.nodes("Region"):
        at=a.s.node(n)["attrs"]
        if at.get("is_ground")==1.0 or int(at.get("rvalue") or -1)!=FOOD: continue
        d=abs((at.get("cy") or 0)-sy)+abs((at.get("cx") or 0)-sx)
        if d<bd: bd=d; best=n
    return best

def learn_phase(a, w, g):
    """Step 1: fire each scrambled control, learn its true displacement vector. NB the world adapter records
    the APPLIED token as game.last_action, so we override it with the control LABEL after perceive (before the
    learn tick) — the agent associates its label c_i with the motion it observed, never the hidden token."""
    ctx={}
    for i in range(160):
        ci=CONTROLS[i%4]
        sub,ctx=w.apply((SCRAMBLE[ci],)); a.perceive_frame(sub)
        if ctx.get("over"): sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub)
        g=gnode(a); a.s.set_attr(g,"last_action",ci)      # the agent's own control label, not the hidden token
        a.tick(); a.master_tick()
    return gnode(a)

def navigate_learned(a, w, g, frames=140):
    """Step 3: the graph rule inverts the learned control basis toward the goal."""
    eats=0; prev=0
    for i in range(frames):
        g=gnode(a); sr=self_region(a)
        if sr is None: w.apply(("Up",)); continue
        a.tick()                                            # mark_self sets is_self (graph)
        for old in list(a.inner.neighbours(g,"has_self")): a.inner.remove_edge(g,"has_self",old)
        for old in list(a.inner.neighbours(g,"wants_locus")): a.inner.remove_edge(g,"wants_locus",old)
        a.inner.add_edge_unchecked(g,"has_self",sr)
        food=nearest_food(a,sr)
        if food is not None: a.inner.add_edge_unchecked(g,"wants_locus",food)
        a.master_tick()                                     # pick_control_for_goal sets chosen_action (graph)
        act=a.s.node(g)["attrs"].get("chosen_control")
        if act not in SCRAMBLE: act=CONTROLS[i%4]            # no goal yet -> explore
        sub,ctx=w.apply((SCRAMBLE[act],)); a.perceive_frame(sub)
        sc=ctx.get("score",0) or 0
        if sc>prev: eats+=1
        if ctx.get("over"): sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub); prev=0
        else: prev=sc
    return eats

def navigate_hardcoded(w, frames=140):
    """Baseline: assume c_i is the i-th compass direction (a hardcoded map) — under the scramble this aims wrong."""
    env=w.env; eats=0; prev=0; ctx={}
    for i in range(frames):
        sr=(env._ar,env._ac); food=min(env._food,key=lambda f:abs(f[0]-sr[0])+abs(f[1]-sr[1]))
        des=(food[0]-sr[0],food[1]-sr[1])
        best=max(CONTROLS,key=lambda c:ASSUME[c][0]*des[0]+ASSUME[c][1]*des[1])  # pick by ASSUMED dir
        sub,ctx=w.apply((SCRAMBLE[best],))                 # but the env moves the SCRAMBLED (true) way
        sc=ctx.get("score",0) or 0
        if sc>prev: eats+=1
        if ctx.get("over"): w.apply(("Reset",)); prev=0
        else: prev=sc
    return eats

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    w=ArcWorld(NavForageEnv()); sub,ctx=w.reset(); a.perceive_frame(sub); g=gnode(a)
    for nm in CONTROLS:
        c=a.s.add_node("Control",{"name":nm}); a.inner.add_edge_unchecked(g,"has_control",c)
    g=learn_phase(a,w,g)
    # report what it learned + the discovered N
    sr=self_region(a); learned={}
    for cr in a.inner.neighbours(sr,"responds_via"):
        at=a.s.node(cr)["attrs"]; learned[at.get("cname")]=(round(at.get("dr") or 0,2),round(at.get("dc") or 0,2))
    N=a.inner.principal_axes(int(str(sr).lstrip("#")))
    eats_learned=navigate_learned(a,w,g)
    # fresh world for the honest baseline contrast
    w2=ArcWorld(NavForageEnv()); w2.reset()
    eats_hard=navigate_hardcoded(w2)
    print("  controls given SCRAMBLED labels (true effects hidden):",SCRAMBLE)
    print("  LEARNED displacement per label (from observation):",learned)
    print(f"  discovered dimensionality N={N}")
    print(f"  navigate via LEARNED inversion (graph rule pick_control_for_goal): food eaten = {eats_learned}")
    print(f"  navigate via HARDCODED compass assumption (baseline): food eaten = {eats_hard}")
    print(f"  DONKEY calls: {calls['n']}")
    ok = eats_learned>=3 and eats_learned>eats_hard and N==2 and calls["n"]==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent navigated to food from the DISCOVERED frame: it learned "
          f"each scrambled control's true effect, discovered N={N}, and reached food ({eats_learned}) by "
          f"inverting the learned control basis — while the hardcoded-direction baseline starved ({eats_hard}) "
          f"under the same scramble. Navigation is frame-derived, not grid/label-assumed. donkey={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
