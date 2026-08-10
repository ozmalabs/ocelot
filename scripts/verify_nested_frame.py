"""STEP 4 verification: frames NEST. (A) A sub-context whose controls reveal a direction OUTSIDE the parent's
span — i.e. MORE discovered axes than the parent (the authored principal_axes computes both N's) — is recognised
as a nested sub-frame and a child WorldBinding is minted (filled_by); a sub-context that stays within the
parent's dimensionality is NOT (it's the same frame, e.g. a mere diagonal is still row+col). (B) The child's OWN
frame is the one principal_axes discovered (it includes the new axis the parent lacked). (C) The child's value
rolls UP to the parent via the existing world_understanding rollup_value rule. Recognise a sub-world by basis-
change, discover its frame, compose its value upward — the binding tree recurses, all from the authored
primitive + held rules.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/verify_nested_frame.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

def run(a,n=6):
    for _ in range(n): a.tick()

def region_with_controls(a, vecs):
    r=a.s.add_node("Region",{"respond_votes":9.0})
    for nm,(dr,dc,dz) in vecs.items():
        cr=a.s.add_node("ControlResponse",{"cname":nm,"dr":float(dr),"dc":float(dc),"dz":float(dz)})
        a.inner.add_edge_unchecked(r,"responds_via",cr)
    n=a.inner.principal_axes(int(str(r).lstrip("#")))           # discover this context's frame
    return r,n

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])

    # PARENT frame: 2D controls -> N=2 (row, col)
    rp,Np=region_with_controls(a,{"r+":(1,0,0),"r-":(-1,0,0),"c+":(0,1,0),"c-":(0,-1,0)})
    # SUB-context that opens a NEW dimension (depth) -> N=3 : a genuine nested frame
    rs3,N3=region_with_controls(a,{"r+":(1,0,0),"r-":(-1,0,0),"c+":(0,1,0),"c-":(0,-1,0),"d+":(0,0,1),"d-":(0,0,-1)})
    # SUB-context that stays within the parent's plane (a diagonal basis) -> still N=2 : NOT a new frame
    rs2,N2=region_with_controls(a,{"a":(1,1,0),"b":(-1,-1,0),"e":(1,-1,0),"f":(-1,1,0)})

    # --- A. basis-change (N-increase) detector ---
    l_nest=a.s.add_node("Locus",{"name":"portal","parent_ndim":float(Np)})
    a.inner.add_edge_unchecked(l_nest,"has_subframe",rs3)
    l_flat=a.s.add_node("Locus",{"name":"open_room","parent_ndim":float(Np)})
    a.inner.add_edge_unchecked(l_flat,"has_subframe",rs2)
    run(a)
    nest_child=list(a.inner.neighbours(l_nest,"filled_by"))
    flat_child=list(a.inner.neighbours(l_flat,"filled_by"))
    A_ok = len(nest_child)==1 and len(flat_child)==0
    print(f"  parent N={Np}; sub-with-new-dimension N={N3}; sub-within-plane N={N2}")
    print(f"  A. detect-by-basis-change: new-dimension locus -> child binding={len(nest_child)} (expect 1); "
          f"same-dimensionality locus -> child={len(flat_child)} (expect 0)  {'OK' if A_ok else 'MISS'}")

    # --- B. the child's OWN frame includes the axis the parent lacked (a depth axis: |dir_z|>0.5) ---
    has_depth = any(abs(a.s.node(ax)["attrs"].get("dir_z",0))>0.5 for ax in a.s.nodes("Axis"))
    B_ok = N3==3 and has_depth
    print(f"  B. child frame discovered: N={N3} (expect 3); includes a depth axis the parent lacked={has_depth}  {'OK' if B_ok else 'MISS'}")

    # --- C. roll the child's value UP to the parent (existing world_understanding rollup_value) ---
    pv=a.s.add_node("ValueRole",{"value":0.0})
    cv=a.s.add_node("ValueRole",{"value":10.0,"rollup_factor":1.0})
    a.inner.add_edge_unchecked(cv,"rolls_up_to",pv)
    run(a)
    parent_val=a.s.node(pv)["attrs"].get("value")
    C_ok = parent_val==10.0
    print(f"  C. value rollup child->parent: parent value={parent_val} (expect 10.0)  {'OK' if C_ok else 'MISS'}")

    ok = A_ok and B_ok and C_ok and calls["n"]==0
    print(f"  DONKEY calls: {calls['n']}")
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — frames NEST: a sub-frame is recognised by a BASIS CHANGE (a "
          f"sub-context that reveals a dimension outside the parent's span -> child WorldBinding, while a "
          f"same-dimensionality sub-context stays in the parent), the child's OWN frame is what the authored "
          f"principal_axes discovered (it has the depth axis the parent lacked), and its value rolls UP to the "
          f"parent. The binding tree recurses; authored primitive + held rules; donkey={calls['n']}.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
