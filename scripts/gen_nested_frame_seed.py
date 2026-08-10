"""Emit seeds/nested_frame.json — STEP 4 of the N-dim frame-understanding integration
(docs/jabberwock_nd_frame_understanding_design.md). NESTING: a sub-frame is a Locus whose filled_by points at a
child WorldBinding, RECOGNISED when entering it CHANGES the principal-motion basis — the controls now move along
a direction that does NOT project onto any parent axis. The jabberwock's design point 3.

  detect_nested_frame : a locus whose sensed motion is collinear with NO parent axis (the motion opens a new
                        direction the parent frame can't explain) mints a child WorldBinding, links the locus
                        filled_by -> child, and marks it for its own frame discovery. Held Terms only
                        (AngleBetween / Vec / Count / Filter). Single-fire via the locus has_child guard.

Child-frame discovery then runs the authored primitive principal_axes on the child's own controls; value rolls
up to the parent via the existing world_understanding rollup_value rule. This seed adds only the DETECTOR.
"""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PI=3.141592653589793; EPS=0.12
def V(n): return {"type":"Var","name":n}
def A(n,k): return {"type":"Attr","node":V(n),"key":k}
def L(v): return {"type":"Lit","value":v}
def P0(n,k): return {"type":"Plus","items":[A(n,k),L(0.0)]}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def And(*xs): return {"type":"And","items":list(xs)}
def Or(*xs): return {"type":"Or","items":list(xs)}
def Count(src): return {"type":"Count","source":src}
def NodesOf(t): return {"type":"NodesOfType","node_type":t}
def Filter(src,var,pred): return {"type":"Filter","source":src,"var_name":var,"predicate":pred}
def Exists(src,var,pred): return {"type":"Exists","source":src,"var_name":var,"predicate":pred}
def Not(x): return {"type":"Not","arg":x}
def Vec(*items): return {"type":"Vec","items":list(items)}
def Angle(a,b): return {"type":"AngleBetween","a":a,"b":b}

def para(u,v): ang=Angle(u,v); return Or(Lt(ang,L(EPS)), Gt(ang,L(PI-EPS)))
# a parent axis's direction (principal_axes stored it as separate floats dir_x/dir_y/dir_z)
axvec=Vec(P0("ax","dir_x"),P0("ax","dir_y"),P0("ax","dir_z"))
# the motion sensed at the locus (the displacement its controls produced)
mvec=Vec(P0("m","mr"),P0("m","mc"),P0("m","mz"))

# BASIS-CHANGE detector via the authored primitive. A motion that the parent axes can REPRESENT (any linear
# combination, e.g. a diagonal in a 2D plane) is NOT a new frame — it is still the parent. A genuine sub-frame
# is one whose controls reveal a direction OUTSIDE the parent's span — i.e. the discovered dimensionality of the
# sub-context EXCEEDS the parent's (a new axis the parent can't explain). principal_axes (the authored Rust
# primitive) computes both N's deterministically; this rule is a scalar comparison (no DSL aggregation).
detect={"name":"detect_nested_frame",
  "comment":"basis-change detector: a locus whose sub-context discovers MORE axes than the parent frame (a "
            "direction outside the parent's span) is a nested sub-frame -> mint a child WorldBinding (filled_by). "
            "Both N's come from the authored principal_axes; this is a scalar comparison. Single-fire via has_child.",
  "match":[["l","has_subframe","sub"]],
  "where":And(Lt(P0("l","has_child"),L(0.5)),Gt(P0("sub","ndim"),P0("l","parent_ndim"))),
  "effects":[["add_node","cb","WorldBinding",{"kind":"nested","activation":"active"}],
             ["add_edge","l","filled_by","cb"],
             ["add_edge","cb","explores","sub"],
             ["set_attr","l","has_child",1.0],
             ["set_attr","cb","needs_frame",1.0]]}

seed={"id":"nested_frame","version":"1.0.0","depends_on":[],
      "description":"STEP 4: recognise a nested sub-frame by a BASIS CHANGE (locus motion collinear with no "
        "parent axis) and mint a child WorldBinding (filled_by). Child-frame discovery reuses the authored "
        "principal_axes; value rolls up via world_understanding rollup_value. Held Terms only; no new primitive.",
      "microtheory":{"name":"nested_frame","description":"frames nest: a locus whose motion opens a new basis "
        "is a child world; recognised by basis-change, discovered by principal_axes, value rolled up"},
      "nodes":[],"edges":[],"productions":[],"rules":[detect]}
_=para,axvec,mvec,Exists,Not,Count,Filter,And,Or,Eq,Gt  # (kept helpers; detector now uses the authored primitive's N)
out=os.path.join(ROOT,"seeds","nested_frame.json")
tmp=out+".tmp"; json.dump(seed,open(tmp,"w"),indent=1); json.load(open(tmp)); os.replace(tmp,out)
print("wrote",os.path.relpath(out,ROOT),"-",len(seed["rules"]),"rules")
