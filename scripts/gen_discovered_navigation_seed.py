"""Emit seeds/discovered_navigation.json — STEPS 3 + 5 of the N-dim frame-understanding integration. Navigate
ENTIRELY in master_tick from the DISCOVERED frame — no Python consumer, no grid, no hardcoded directions.

  mark_dist             : for the self region (is_self, from mark_self) and each region whose colour has a
                          POSITIVE learned consequence (a goal kind), stamp that region's manhattan distance to
                          self. Both regions match-bound (no predicate closure); the consequence join picks
                          goal kinds from what was LEARNED, nothing hardcoded.
  aim_goal              : the goal centroid (g.goal_cy/goal_cx) = the nearest goal-kind region (Argmin over the
                          marked distances). Derives the goal role graph-natively.
  pick_control_for_goal : chosen_control = the control whose LEARNED displacement vector dots most with the
                          desired displacement (goal centroid - self centroid). The inversion of the discovered
                          control basis — frame-derived, label-agnostic.

Everything fires in master_tick. The adapter only ingests observations (regions + consequences) + affordances
(Control nodes) and reads chosen_control back. The Python consumer world_understanding_step is DELETED.
"""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def V(n): return {"type":"Var","name":n}
def A(n,k): return {"type":"Attr","node":V(n),"key":k}
def L(v): return {"type":"Lit","value":v}
def P0(n,k): return {"type":"Plus","items":[A(n,k),L(0.0)]}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def And(*xs): return {"type":"And","items":list(xs)}
def Or(*xs): return {"type":"Or","items":list(xs)}
def Abs(x): return {"type":"Abs","arg":x}
def Minus(a,b): return {"type":"Minus","a":a,"b":b}
def Plus(*xs): return {"type":"Plus","items":list(xs)}
def Vec(*items): return {"type":"Vec","items":list(items)}
def Dot(a,b): return {"type":"Dot","a":a,"b":b}
def Neigh(n,e): return {"type":"Neighbours","node":V(n),"edge_type":e,"any_type":False}
def NodesOf(t): return {"type":"NodesOfType","node_type":t}
def Filter(src,var,pred): return {"type":"Filter","source":src,"var_name":var,"predicate":pred}
def Argmax(src,var,val,default): return {"type":"Argmax","source":src,"var_name":var,"value":val,"default":default}
def Argmin(src,var,val,default): return {"type":"Argmin","source":src,"var_name":var,"value":val,"default":default}
def AttrOf(node_term,k): return {"type":"Attr","node":node_term,"key":k}

# 1. stamp each goal-kind region's manhattan distance to the self region (both match-bound; consequence join
#    selects goal kinds = colours with a positive learned consequence). Mark it a goal candidate.
mark_dist={"name":"mark_dist",
  "comment":"stamp distance-to-self on regions whose colour has a positive learned consequence (goal kinds). "
            "self + region both match-bound (no closure); goal kinds come from learning, nothing hardcoded.",
  "match":[["g","has_region","sr"],["g","has_region","rr"],["g","tracks_consequence","cm"]],
  "where":And(Gt(P0("sr","is_self"),L(0.5)),
              Lt(P0("rr","is_self"),L(0.5)),
              Eq(A("cm","rvalue"),A("rr","rvalue")),
              Or(Gt(P0("cm","value"),L(0.3)),Lt(P0("cm","tasted"),L(0.5)))),  # positive kind, else (bootstrap) untasted
  "effects":[["set_attr","rr","is_goal_kind",1.0],
             ["set_attr","rr","dist_to_self",{"__term__":Plus(Abs(Minus(P0("rr","cy"),P0("sr","cy"))),
                                                              Abs(Minus(P0("rr","cx"),P0("sr","cx"))))}]]}

# 2. the goal centroid = the nearest goal-kind region (Argmin over the marked distances; value reads only the
#    region's own dist_to_self, no closure). Derives the goal role graph-natively.
goal_src=Filter(NodesOf("Region"),"rr",Gt(P0("rr","is_goal_kind"),L(0.5)))
nearest=Argmin(goal_src,"rr",P0("rr","dist_to_self"),V("sr"))
aim_goal={"name":"aim_goal",
  "comment":"goal centroid = nearest goal-kind region's centroid. The goal role, derived graph-natively.",
  "match":[["g","has_region","sr"]],
  "where":Gt(P0("sr","is_self"),L(0.5)),
  "effects":[["set_attr","g","goal_cy",{"__term__":AttrOf(nearest,"cy")}],
             ["set_attr","g","goal_cx",{"__term__":AttrOf(nearest,"cx")}]]}

# 3. invert the learned control basis toward the goal: chosen_control = Argmax control of Dot(learned Δ, desired)
desired=Vec(Minus(P0("g","goal_cy"),P0("sr","cy")),Minus(P0("g","goal_cx"),P0("sr","cx")),L(0.0))
desired_extent=Plus(Abs(Minus(P0("g","goal_cy"),P0("sr","cy"))),
                    Abs(Minus(P0("g","goal_cx"),P0("sr","cx"))))
cdvec=Vec(P0("cr","dr"),P0("cr","dc"),P0("cr","dz"))
best_control=Argmax(Neigh("sr","responds_via"),"cr",Dot(cdvec,desired),V("sr"))
pick={"name":"pick_control_for_goal",
  "comment":"chosen_control = the control whose LEARNED Δ dots most with the desired displacement to the goal. "
            "Frame-derived (no grid, no hardcoded directions); self found via is_self, goal via g.goal_cy/cx.",
  "match":[["g","has_region","sr"]],
  "where":And(Gt(P0("sr","is_self"),L(0.5)),Gt(desired_extent,L(0.5))),
  "effects":[["set_attr","g","chosen_control",{"__term__":AttrOf(best_control,"cname")}]]}

seed={"id":"discovered_navigation","version":"1.0.0","depends_on":[],
      "description":"STEPS 3+5: navigate ENTIRELY in master_tick from the discovered frame. mark_dist + aim_goal "
        "derive the goal role from learned consequences (graph-native); pick_control_for_goal inverts the "
        "learned control basis toward it. No Python consumer, no grid, no hardcoded directions.",
      "microtheory":{"name":"discovered_navigation","description":"derive self+goal and choose the action by "
        "inverting the learned control basis, all in master_tick; navigation is frame-derived, not grid-assumed"},
      "nodes":[],"edges":[],"productions":[],"rules":[mark_dist,aim_goal,pick]}
out=os.path.join(ROOT,"seeds","discovered_navigation.json")
tmp=out+".tmp"; json.dump(seed,open(tmp,"w"),indent=1); json.load(open(tmp)); os.replace(tmp,out)
print("wrote",os.path.relpath(out,ROOT),"-",len(seed["rules"]),"rules")
