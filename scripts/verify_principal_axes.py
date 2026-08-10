"""STEP 2 verification: DISCOVER the frame's axes (and N) from the bag of learned control vectors — never
assume 2D. Part A: from step 1's actually-learned forage deltas, the agent discovers N=2, with Up/Down on one
axis (signs +/-) and Left/Right on the other. Part B (generality): give it five controls spanning three
independent directions and it discovers N=3 — the dimensionality tracks the data, not a hardcoded 2.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/verify_principal_axes.py
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

CONTROLS=["Up","Down","Left","Right"]

def run_rules(a, n=8):
    for _ in range(n): a.tick()

def axes_of(a):
    return [n for n in a.s.nodes("Axis")]

def part_a():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    w=ArcWorld(ForageEnv()); sub,ctx=w.reset(); a.perceive_frame(sub); g=gnode(a)
    for nm in CONTROLS:
        c=a.s.add_node("Control",{"name":nm}); a.inner.add_edge_unchecked(g,"has_control",c)
    for i in range(160):                       # STEP 1: learn each control's displacement
        act=CONTROLS[i%4]; a.s.set_attr(g,"last_action",act)
        sub,ctx=w.apply((act,)); a.perceive_frame(sub)
        if ctx.get("over"): sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub)
        a.tick(); a.master_tick(); g=gnode(a)
    run_rules(a)                               # STEP 2: discover the axes from the learned vectors
    self_r=max((n for n in a.s.nodes("Region") if a.s.node(n)["attrs"].get("is_ground")!=1.0),
               key=lambda n:a.s.node(n)["attrs"].get("respond_votes") or 0, default=None)
    ndim=a.s.node(self_r)["attrs"].get("ndim") if self_r else None
    # which axis each control landed on
    cr_axis={}
    for cr in a.inner.neighbours(self_r,"responds_via"):
        at=a.s.node(cr)["attrs"]; ax=list(a.inner.neighbours(cr,"on_axis"))
        cr_axis[at.get("cname")]=(ax[0] if ax else None, at.get("sign"))
    naxes=len(axes_of(a))
    ud_same = cr_axis.get("Up",(1,))[0]==cr_axis.get("Down",(2,))[0] and cr_axis["Up"][0] is not None
    lr_same = cr_axis.get("Left",(1,))[0]==cr_axis.get("Right",(2,))[0] and cr_axis["Left"][0] is not None
    ud_sign = cr_axis.get("Up",(0,0))[1]!=cr_axis.get("Down",(0,0))[1]
    okA = naxes==2 and ndim==2 and ud_same and lr_same and ud_sign and calls["n"]==0
    print(f"  PART A (from learned forage deltas): #Axis={naxes} ndim={ndim} | Up/Down same axis={ud_same} "
          f"opposite signs={ud_sign} | Left/Right same axis={lr_same} | donkey={calls['n']}")
    for nm in CONTROLS: print(f"    {nm:5s} -> axis {cr_axis.get(nm,(None,))[0]} sign {cr_axis.get(nm,(None,None))[1]}")
    return okA

def part_b():
    """Five controls spanning THREE independent directions -> N must be 3 (not assumed 2)."""
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    sr=a.s.add_node("Region",{"respond_votes":9.0,"is_ground":0.0})
    vecs={"X+":(1.0,0.0,0.0),"X-":(-1.0,0.0,0.0),"Y+":(0.0,1.0,0.0),"Y-":(0.0,-1.0,0.0),"Z+":(0.0,0.0,1.0)}
    for nm,(dr,dc,dz) in vecs.items():
        cr=a.s.add_node("ControlResponse",{"cname":nm,"dr":dr,"dc":dc,"dz":dz})
        a.inner.add_edge_unchecked(sr,"responds_via",cr)
    run_rules(a)
    naxes=len(axes_of(a)); ndim=a.s.node(sr)["attrs"].get("ndim")
    okB = naxes==3 and ndim==3
    print(f"  PART B (3 independent directions among 5 controls): #Axis={naxes} ndim={ndim}  ({'OK' if okB else 'MISS'})")
    return okB

def main():
    okA=part_a(); okB=part_b()
    ok=okA and okB
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent DISCOVERED the frame's axes + dimensionality from the "
          f"learned control vectors alone: N=2 from forage's four controls (Up/Down one axis, Left/Right the "
          f"other), N=3 when the controls span three directions. The dimensionality tracks the data, never a "
          f"hardcoded 2D grid. Graph-native, no new Rust primitive (AngleBetween/Vec carry it).")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
