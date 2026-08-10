"""Emit seeds/principal_axes.json — STEP 2 of the N-dim frame-understanding integration
(docs/jabberwock_nd_frame_understanding_design.md). DISCOVER the natural frame's axes (and N) from the BAG of
learned control displacement vectors (step 1's ControlResponse.(dr,dc[,dz])), generalising nd_basis_discovery
from a single velocity vector to a minimal independent basis over the set. Collinear controls collapse to ONE
axis (Up/Down -> the vertical axis, signs +1/-1); N = Count(Axis) = the DISCOVERED dimensionality, never
assumed. NO new Rust primitive — AngleBetween / Vec / Nth (all held) carry it.

  mark_self      : the self region = the one with max respond_votes (game-independent); gates the rest.
  cr_make_dvec   : build each control's displacement as a uniform 3D vector dvec = Vec(dr,dc,dz).
  mint_axis      : mint ONE Axis per collinear class — ONLY the lexicographic-MAX control of the class mints
                   (race-free under batched fixpoint application); the rest attach.
  attach_to_axis : file every other collinear control onto that Axis (via a sibling already on it) with a sign.
  write_ndim     : N = Count(Axis) on the self region = the discovered dimensionality.

para(u,v) = AngleBetween(u,v) ~0 (parallel) OR ~pi (antiparallel): collinearity from the held angle Term alone.
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
def Gte(a,b): return {"type":"Gte","a":a,"b":b}
def Not(x): return {"type":"Not","arg":x}
def And(*xs): return {"type":"And","items":list(xs)}
def Or(*xs): return {"type":"Or","items":list(xs)}
def Count(src): return {"type":"Count","source":src}
def Neigh(n,e): return {"type":"Neighbours","node":V(n),"edge_type":e,"any_type":False}
def NodesOf(t): return {"type":"NodesOfType","node_type":t}
def Filter(src,var,pred): return {"type":"Filter","source":src,"var_name":var,"predicate":pred}
def Exists(src,var,pred): return {"type":"Exists","source":src,"var_name":var,"predicate":pred}
def MaxOver(src,var,val): return {"type":"MaxOver","source":src,"var_name":var,"value":val}
def Vec(*items): return {"type":"Vec","items":list(items)}
def Nth(seq,i): return {"type":"Nth","items":seq,"index":i}
def Angle(a,b): return {"type":"AngleBetween","a":a,"b":b}
def Mag(v): return {"type":"Magnitude","arg":v}
def Ite(c,t,o): return {"type":"IfThenElse","cond":c,"then":t,"other":o}

def para(u,v): ang=Angle(u,v); return Or(Lt(ang,L(EPS)), Gt(ang,L(PI-EPS)))
def dv(n): return A(n,"dvec")
# lexicographic >: cr2.dvec > cr.dvec by first differing of (x,y,z)
def gt_lex(big,small):
    def c(i): return Nth(dv(big),i), Nth(dv(small),i)
    (x2,x1),(y2,y1),(z2,z1)=c(0),c(1),c(2)
    return Or(Gt(x2,x1),
              And(Eq(x2,x1),Gt(y2,y1)),
              And(Eq(x2,x1),Eq(y2,y1),Gt(z2,z1)))

# the self region = max respond_votes among all Regions (game-independent); gates the axis discovery.
mark_self={"name":"mark_self","comment":"the self region = the one with max respond_votes; gates axis discovery",
  "match":[["sr","responds_via","cr"]],
  "where":{"type":"Lit","value":True},
  "effects":[["set_attr","sr","is_self",{"__term__":Ite(
      Eq(P0("sr","respond_votes"),MaxOver(NodesOf("Region"),"rr",P0("rr","respond_votes"))),L(1.0),L(0.0))}]]}

# build each control's displacement as a uniform 3D vector (dz defaults 0 for 2D worlds; carries lift in 3D)
make_dvec={"name":"cr_make_dvec","comment":"build each control's learned displacement as a 3D vector on the cr",
  "match":[["sr","responds_via","cr"]],
  "where":Lt(P0("cr","has_dvec"),L(0.5)),
  "effects":[["set_attr","cr","dvec",{"__term__":Vec(P0("cr","dr"),P0("cr","dc"),P0("cr","dz"))}],
             ["set_attr","cr","has_dvec",1.0]]}

# mint ONE Axis per collinear class: only the lexicographic-MAX control of the class mints (race-free).
mint_axis={"name":"mint_axis","comment":"mint one Axis per collinear class; only the lexicographic-max control "
  "of the class mints (race-free under batched application), the rest attach.",
  "match":[["sr","responds_via","cr"]],
  "where":And(Gt(P0("sr","is_self"),L(0.5)),
              Gte(P0("cr","has_dvec"),L(0.5)),
              Lt(Count(Neigh("cr","on_axis")),L(0.5)),
              Not(Exists(Neigh("sr","responds_via"),"cr2",
                   And(Gte(P0("cr2","has_dvec"),L(0.5)),
                       Not(Eq(A("cr","cname"),A("cr2","cname"))),
                       para(dv("cr"),dv("cr2")),
                       gt_lex("cr2","cr"))))),
  "effects":[["add_node","ax","Axis",{}],
             ["add_edge","cr","on_axis","ax"],
             ["set_attr","ax","dir",{"__term__":dv("cr")}],
             ["set_attr","cr","sign",1.0]]}

# file every other collinear control onto the existing Axis (found via a sibling already on it) with a sign.
attach={"name":"attach_to_axis","comment":"file a collinear control onto the existing Axis (found via a sibling "
  "already on it) with sign +1 (parallel) / -1 (antiparallel).",
  "match":[["sr","responds_via","cr"],["sr","responds_via","cr2"],["cr2","on_axis","ax"]],
  "where":And(Gt(P0("sr","is_self"),L(0.5)),
              Gte(P0("cr","has_dvec"),L(0.5)),
              Lt(Count(Neigh("cr","on_axis")),L(0.5)),
              Gt(Mag(A("ax","dir")),L(0.5)),     # axis dir committed (avoids reading an unset zero -> angle 0 -> false-collinear)
              Not(Eq(A("cr","cname"),A("cr2","cname"))),
              para(A("ax","dir"),dv("cr"))),
  "effects":[["add_edge","cr","on_axis","ax"],
             ["set_attr","cr","sign",{"__term__":Ite(Lt(Angle(A("ax","dir"),dv("cr")),L(PI/2)),L(1.0),L(-1.0))}]]}

# N = number of Axis nodes = the DISCOVERED dimensionality, written on the self region.
write_ndim={"name":"write_ndim","comment":"N (dimensionality) = Count(Axis); tracks the data, never assumed 2D.",
  "match":[["sr","responds_via","cr"]],
  "where":And(Gt(P0("sr","is_self"),L(0.5)),Not(Eq(P0("sr","ndim"),Count(NodesOf("Axis"))))),
  "effects":[["set_attr","sr","ndim",{"__term__":Count(NodesOf("Axis"))}]]}

# NOTE: the deterministic axis-clustering (mint one Axis per collinear class, signs, ndim) is the JABBERWOCK-
# AUTHORED Rust primitive `principal_axes(region)` (scripts/jabberwock_authors_principal_axes.py) — a batched
# fixpoint rule-engine cannot express it without mint races (proven: it gave 32 axes / 1 axis). The primitive is
# invoked mechanically on the self region (like predict_wall_set / slide_flood). This seed keeps only the
# graph-native SELF derivation (mark_self); cr_make_dvec/mint_axis/attach/write_ndim are SUPERSEDED by the
# primitive and intentionally dropped.
seed={"id":"principal_axes","version":"1.0.0","depends_on":[],
      "description":"STEP 2: discover the natural frame's AXES + dimensionality from the learned control "
        "displacement vectors. The clustering is the jabberwock-AUTHORED Rust primitive principal_axes(region) "
        "(deterministic, no fixpoint race); this seed keeps only the graph-native self-region derivation that "
        "tells the primitive which region is the controllable locus.",
      "microtheory":{"name":"principal_axes","description":"discover the minimal independent basis (axes + N) "
        "over the control displacement vectors via the authored primitive; the frame is inferred, not given"},
      "nodes":[],"edges":[],"productions":[],"rules":[mark_self]}
out=os.path.join(ROOT,"seeds","principal_axes.json")
tmp=out+".tmp"; json.dump(seed,open(tmp,"w"),indent=1); json.load(open(tmp)); os.replace(tmp,out)
print("wrote",os.path.relpath(out,ROOT),"-",len(seed["rules"]),"rules")
