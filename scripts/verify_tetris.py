"""Point the booted, graph-native world-understanding agent at TETRIS and report honestly what it does. This is
a stress test of the frame-understanding stack we built (steps 1-5): it was designed for navigate-a-locus-to-a-
goal-LOCATION worlds (forage/snake). Tetris is different in three ways the stack does NOT (yet) model:
  · ROTATE is a non-translation affordance (transforms the piece's shape, not a point's position);
  · the value signal is LINES CLEARED (a configuration objective), not a colour you contact / a place you reach;
  · gravity moves the locus autonomously every tick.
So we expect it to BIND the world, find the piece as self, and LEARN the translation controls — but to have no
goal to navigate to (no food/locus), hence no Tetris strategy. We measure that honestly against random play.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/verify_tetris.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
import domains.world_play as world_play
from tetris_world import TetrisEnv, PIECE
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

CONTROLS=["Up","Down","Left","Right"]   # Up=rotate, Down=drop, Left/Right=move (agent learns the effects)

def gnode(a): return next((n for n in a.s.nodes("WorldInstance") if a.s.node(n)["attrs"].get("world_type")=="Game"),None)
def self_region(a):
    return max((n for n in a.s.nodes("Region") if a.s.node(n)["attrs"].get("is_ground")!=1.0),
               key=lambda n:a.s.node(n)["attrs"].get("respond_votes") or 0, default=None)

def play_random(frames=400):
    import random as _r; rng=_r.Random(0)
    w=ArcWorld(TetrisEnv()); sub,ctx=w.reset(); lines=0
    for i in range(frames):
        sub,ctx=w.apply((rng.choice(CONTROLS),))
        lines=ctx.get("score",0) or 0
        if ctx.get("over"): sub,ctx=w.apply(("Reset",))
    return lines

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    w=ArcWorld(TetrisEnv()); sub,ctx=w.reset(); a.perceive_frame(sub); g=gnode(a)
    body=a.s.add_node("Body",{}); a.inner.add_edge_unchecked(body,"inhabits",g)
    world_play.declare_affordances(a, g, CONTROLS)

    # warmup: cycle controls, learn each affordance's effect from observation
    for i in range(160):
        sub,ctx=w.apply((CONTROLS[i%4],)); a.perceive_frame(sub)
        if ctx.get("over"): sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub)
        g=gnode(a); a.inner.add_edge_unchecked(body,"inhabits",g)
        a.tick(); a.master_tick()

    sr=self_region(a); learned={}
    if sr is not None:
        for cr in a.inner.neighbours(sr,"responds_via"):
            at=a.s.node(cr)["attrs"]; learned[at.get("cname")]=(round(at.get("dr") or 0,2),round(at.get("dc") or 0,2))
        N=a.inner.principal_axes(int(str(sr).lstrip("#")))
        self_rv=int(a.s.node(sr)["attrs"].get("rvalue") or -1)
    else: N=0; self_rv=None
    nb=len(a.s.nodes("WorldBinding"))

    # PLAY graph-native: navigation runs in master_tick (but there is no goal-LOCUS in Tetris -> it explores)
    prev=0; lines=0
    for i in range(400):
        g=gnode(a); a.inner.add_edge_unchecked(body,"inhabits",g)
        a.master_tick()
        act=world_play.read_chosen(a,g)
        if act not in CONTROLS: act=CONTROLS[i%4]
        sub,ctx=w.apply((act,)); a.perceive_frame(sub)
        sc=ctx.get("score",0) or 0; lines=sc
        if ctx.get("over"): sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub); prev=0
        else: prev=sc
        a.tick()
    rand_lines=play_random(400)

    print(f"  binds the world (WorldBinding minted): {nb>=1}")
    print(f"  found the piece as self: rvalue={self_rv} (piece colour={PIECE})  -> {'yes' if self_rv==PIECE else 'no'}")
    print(f"  learned affordance effects (Up=rotate, Down=drop, Left, Right): {learned}")
    print(f"  discovered dimensionality N={N}")
    print(f"  goal derived (a navigable goal-kind region exists): "
          f"{bool([n for n in a.s.nodes('Region') if (a.s.node(n)['attrs'].get('is_goal_kind') or 0)>0.5])}")
    print(f"  lines cleared — graph-native play: {lines}   random baseline: {rand_lines}")
    print(f"  DONKEY calls: {calls['n']}")
    print("\n"+"="*96)
    plays = lines>rand_lines
    binds_learns = nb>=1 and self_rv==PIECE and len(learned)>=3
    print(f"  VERDICT — {'PLAYS TETRIS' if plays else 'DOES NOT (yet) PLAY TETRIS'}. The framework "
          f"{'binds the world, finds the falling piece as self, and learns its translation controls' if binds_learns else 'partially binds/learns'} "
          f"(N={N}), but Tetris is NOT a navigate-to-a-LOCUS world: there is no goal location, ROTATE is a shape "
          f"transform (not a displacement the inversion can use), and the reward is LINES CLEARED (not a colour "
          f"contacted). So with no goal it explores -> {lines} lines vs {rand_lines} random. The honest edge of "
          f"the current stack; donkey={calls['n']}.")
    print("="*96)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
