"""Emit graph-native future-manifold selection policy."""
from __future__ import annotations
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "information_commitment.json")
def V(n): return {"type":"Var","name":n}
def L(v): return {"type":"Lit","value":v}
def A(n,k): return {"type":"Attr","node":V(n),"key":k}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def And(*x): return {"type":"And","items":list(x)}
def Or(*x): return {"type":"Or","items":list(x)}
def Not(x): return {"type":"Not","arg":x}
def Plus(*x): return {"type":"Plus","items":list(x)}
def Minus(a,b): return {"type":"Minus","a":a,"b":b}
def Times(*x): return {"type":"Times","items":list(x)}
def Neigh(n,e): return {"type":"Neighbours","node":n,"edge_type":e,"any_type":False}
def Exists(src,var,pred): return {"type":"Exists","source":src,"var_name":var,"predicate":pred}
def Filter(src,var,pred): return {"type":"Filter","source":src,"var_name":var,"predicate":pred}
def ArgminUnique(src,var,value): return {"type":"ArgminUnique","source":src,"var_name":var,"value":value,"default":None}
def MinOver(src,var,value): return {"type":"MinOver","source":src,"var_name":var,"value":value,"default":L(0.0)}
def MaxOver(src,var,value): return {"type":"MaxOver","source":src,"var_name":var,"value":value,"default":L(0.0)}
def If(c,a,b): return {"type":"IfThenElse","cond":c,"then":a,"other":b}
def set_if(v,k,x,computed=False): return ["set_attr_if_different",v,k,{"__term__":x} if computed else x]

C = Neigh(V("ctx"),"has_candidate")
P = Neigh(V("candidate"),"has_manifold_projection")
INVALID = Not(Eq(A("fp","validated"),L(1.0)))
REASON = If(INVALID,L("future_manifold_evidence_required"),If(Not(Eq(A("fp","manifold_id"),A("ctx","manifold_id"))),L("manifold_identity_mismatch"),If(Lt(A("fp","projection_horizon"),A("ctx","required_horizon")),L("insufficient_temporal_coverage"),If(Gt(A("fp","has_escape_residual"),L(0.0)),L("outside_future_manifold"),If(Lt(A("fp","minimum_retained_width"),A("ctx","minimum_width")),L("insufficient_width"),If(Gt(A("fp","maximum_information_loss"),A("ctx","maximum_information_loss")),L("excess_information_loss"),L("allowed")))))))
FAILED = Not(Eq(REASON,L("allowed")))
# Lexicographic priority: action count, intervention magnitude, descending
# existing objective, then fixed decision ordinal. Each stage filters before
# the next, so no unbounded utility can buy an extra intervention.
S0 = Filter(C,"option",Eq(A("option","hard_veto"),L(0.0)))
S1 = Filter(S0,"option",Eq(A("option","action_count"),MinOver(S0,"x",A("x","action_count"))))
S2 = Filter(S1,"option",Eq(A("option","intervention_magnitude"),MinOver(S1,"x",A("x","intervention_magnitude"))))
S3 = Filter(S2,"option",Eq(A("option","net_value"),MaxOver(S2,"x",A("x","net_value"))))
S4 = Filter(S3,"option",Eq(A("option","decision_ordinal"),MinOver(S3,"x",A("x","decision_ordinal"))))
WIN = ArgminUnique(S4,"option",A("option","decision_ordinal"))
VALUE = {"wait":Minus(A("candidate","expected_information_gain"),Plus(A("candidate","delay_cost"),A("candidate","opportunity_cost"))),"refine":Minus(Times(A("candidate","expected_information_gain"),A("candidate","decision_relevance")),Plus(A("candidate","refinement_cost"),A("candidate","delay_cost"))),"commit":Minus(Plus(A("candidate","expected_goal_work"),A("candidate","expected_information_gain")),A("candidate","resource_cost"))}
RULES=[
 {"name":"ic_missing_manifold_projection_fails_closed","area":"executive","order":3,"latency_class":"soft_realtime","match":[["ctx","has_candidate","candidate"]],"where":And(Not(Exists(P,"fp",L(True))),Eq(A("candidate","hard_veto"),L(0.0))),"effects":[set_if("candidate","hard_veto",1.0),set_if("candidate","veto_reason","future_manifold_evidence_required")]},
 {"name":"ic_gate_manifold_projection","area":"executive","order":3,"latency_class":"soft_realtime","match":[["ctx","has_candidate","candidate"],["candidate","has_manifold_projection","fp"]],"where":Eq(A("candidate","hard_veto"),L(0.0)),"effects":[set_if("candidate","future_manifold_reason",REASON,True),set_if("candidate","future_manifold_allowed",If(FAILED,L(0.0),L(1.0)),True),set_if("candidate","hard_veto",If(FAILED,L(1.0),L(0.0)),True),set_if("candidate","veto_reason",REASON,True)]},
]
for kind in ("wait","refine","commit"):
 RULES.append({"name":"ic_score_"+kind,"area":"executive","order":3,"latency_class":"soft_realtime","match":[["ctx","has_candidate","candidate"]],"where":Eq(A("candidate","decision_kind"),L(kind)),"effects":[set_if("candidate","net_value",VALUE[kind],True)]})
RULES.append({"name":"ic_choose_unique_admissible_option","area":"executive","order":3,"latency_class":"soft_realtime","match":[["ctx","has_candidate","candidate"]],"where":And(Eq(V("candidate"),WIN),Eq(A("ctx","decided"),L(0.0))),"effects":[set_if("candidate","chosen",1.0),set_if("ctx","decided",1.0),set_if("ctx","decision",A("candidate","decision_kind"),True),["add_node","decision","CommitDecision",{"decision_kind":{"__term__":A("candidate","decision_kind")},"candidate_name":{"__term__":A("candidate","name")},"action_count":{"__term__":A("candidate","action_count")},"intervention_magnitude":{"__term__":A("candidate","intervention_magnitude")},"status":"resolved"}],["add_edge","ctx","has_commit_decision","decision",{}],["add_edge","decision","selected","candidate",{}]]})
MANIFEST={"id":"information_commitment","version":"4.0.0","self_load_only":True,"depends_on":["cognitive_areas"],"area":"executive","description":"Shape-residual future-manifold gate and least-action selection.","microtheory":{"name":"information_commitment","description":"least-action selection after hard residual-tube gating"},"nodes":[],"edges":[],"productions":[{"provenance":"seed:information_commitment:candidates","src":{"type":"DecisionContext","var":"ctx"},"edge_type":"has_candidate","tgt":{"type":"CommitOption","var":"candidate"}},{"provenance":"seed:information_commitment:projection","src":{"type":"CommitOption","var":"candidate"},"edge_type":"has_manifold_projection","tgt":{"type":"ManifoldProjection","var":"fp"}},{"provenance":"seed:information_commitment:decision","src":{"type":"DecisionContext","var":"ctx"},"edge_type":"has_commit_decision","tgt":{"type":"CommitDecision","var":"decision"}},{"provenance":"seed:information_commitment:selected","src":{"type":"CommitDecision","var":"decision"},"edge_type":"selected","tgt":{"type":"CommitOption","var":"candidate"}}],"rules":RULES}
if __name__=="__main__":
 with open(OUT,"w") as f: json.dump(MANIFEST,f,indent=1)
 print(f"wrote {OUT} with {len(RULES)} rules")
