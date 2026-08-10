"""Emit generic compositional control-basis bridge for existing cognition."""
from __future__ import annotations
import json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"seeds","control_bundle.json")
def V(n):return {"type":"Var","name":n}
def L(v):return {"type":"Lit","value":v}
def A(n,k):return {"type":"Attr","node":V(n),"key":k}
def Eq(a,b):return {"type":"Eq","a":a,"b":b}
def Lt(a,b):return {"type":"Lt","a":a,"b":b}
def Gt(a,b):return {"type":"Gt","a":a,"b":b}
def And(*x):return {"type":"And","items":list(x)}
def Or(*x):return {"type":"Or","items":list(x)}
def Not(x):return {"type":"Not","arg":x}
def Neg(x):return {"type":"Neg","arg":x}
def Plus(*x):return {"type":"Plus","items":list(x)}
def Times(*x):return {"type":"Times","items":list(x)}
def Count(x):return {"type":"Count","source":x}
def N(n,e):return {"type":"Neighbours","node":n,"edge_type":e,"any_type":False}
def Filter(s,v,p):return {"type":"Filter","source":s,"var_name":v,"predicate":p}
def Exists(s,v,p):return {"type":"Exists","source":s,"var_name":v,"predicate":p}
def Argmin(s,v,val):return {"type":"Argmin","source":s,"var_name":v,"value":val,"default":None}
def ArgminUnique(s,v,val):return {"type":"ArgminUnique","source":s,"var_name":v,"value":val,"default":None}
def MinOver(s,v,val):return {"type":"MinOver","source":s,"var_name":v,"value":val,"default":None}
def Eval(node):return {"type":"EvalSubgraph","node":node}
def Pick(s):return {"type":"Pick","source":s}
CONTROLS=N(V("game"),"has_control")
ATTENTION_VALUE=Eval(Pick(N(V("agent"),"attention_value_term")))
ATTENTION_WINNER=ArgminUnique(
    CONTROLS,"control",Neg(ATTENTION_VALUE))
ATTENTION_ACTIVE=And(
    Eq(A("agent","attention_refused"),L(0.0)),
    Gt(A("agent","attention_salience"),L(2.0)))
# Controls already selected by another faculty, and controls on the same
# exclusive apparatus axis, are not curiosity candidates. Attention can
# therefore orient the body while curiosity independently explores movement,
# weapon, and interaction axes without ever producing an inadmissible bundle.
# The direct attention-winner exclusion makes this independent of scheduler
# area order: curiosity may settle before or after the attention edge exists.
COMPATIBLE_CONTROLS=Filter(
    CONTROLS,"option",
    And(
        Not(Exists(
            N(V("game"),"selected_control"),"selected",
            Eq(V("selected"),V("option")))),
        Not(Exists(
            N(V("option"),"exclusive_with"),"blocked",
            Exists(
                N(V("game"),"selected_control"),"selected",
                Eq(V("selected"),V("blocked"))))),
        Not(And(
            ATTENTION_ACTIVE,
            Or(
                Eq(V("option"),ATTENTION_WINNER),
                Exists(
                    N(V("option"),"exclusive_with"),"blocked",
                    Eq(V("blocked"),ATTENTION_WINNER)))))))
LEAST_TRIALS=MinOver(
    COMPATIBLE_CONTROLS,"option",A("option","n_trials"))
# Strict total exploration rank from graph data. One additional trial must
# outweigh every apparatus ordinal, so this cycles through the least-tried
# controls without allowing match iteration order to break a tie.
EXPLORATION_RANK=Plus(
    Times(A("option","n_trials"),Plus(Count(CONTROLS),L(1))),
    A("option","control_ordinal"))
LEAST_TRIED_UNIQUE=ArgminUnique(
    COMPATIBLE_CONTROLS,"option",EXPLORATION_RANK)
OPERATE=Eval(Pick(N(V("agent"),"operate_control_term")))
RULES=[
 {"name":"control_attention_orients_unique_best","area":"motor","order":0,
  "latency_class":"hard_realtime",
  "match":[["game","has_control","control"],["game","for_agent","agent"]],
  "where":And(ATTENTION_ACTIVE,
              Eq(V("control"),ATTENTION_WINNER)),
  "effects":[["add_edge","game","selected_control","control",{}],
             ["set_attr_if_different","game","chosen_source","retinal_attention"],
             ["set_attr_if_different","game","attention_control_epoch",
              {"__term__":A("agent","attention_sensor_epoch")}]]},
 {"name":"control_curiosity_explores_least_tried","area":"executive","order":2,"latency_class":"best_effort",
  "match":[["game","has_control","control"],["game","for_agent","agent"]],
  "where":And(Eq(V("control"),LEAST_TRIED_UNIQUE),
              Eq(A("game","chosen_control"),L(""))),
  "effects":[["set_attr_if_different","game","chosen_control",{"__term__":A("control","name")}],
             ["set_attr_if_different","game","chosen_source","curiosity"],
             ["set_attr_if_different","game","curiosity_min_trials",{"__term__":LEAST_TRIALS}]]},
 {"name":"control_chosen_to_independent_selection","area":"motor","order":1,"latency_class":"hard_realtime",
  "match":[["game","has_control","control"]],
  "where":And(Eq(A("control","name"),A("game","chosen_control")),
              Not(Exists(N(V("game"),"selected_control"),"x",Eq(V("x"),V("control"))))),
  "effects":[["add_edge","game","selected_control","control",{}]]},
 {"name":"control_operate_term_selects_operation_axes","area":"motor","order":0,"latency_class":"hard_realtime",
  "match":[["game","has_control_axis","axis"],["axis","has_control","control"],
           ["game","for_agent","agent"]],
  "where":And(Eq(A("axis","role"),L("operate")),Gt(OPERATE,L(0.0)),
              Not(Exists(N(V("game"),"selected_control"),"x",Eq(V("x"),V("control"))))),
  "effects":[["add_edge","game","selected_control","control",{}]]},
 {"name":"control_bundle_from_selected_primitives","area":"motor","order":1,"latency_class":"hard_realtime",
  "match":[["game","selected_control","control"]],
  "where":Eq(A("game","bundle_open"),L(1.0)),
  "effects":[["add_node_if_absent","bundle","ControlBundle",{
                "world_tick":{"__term__":A("game","world_tick")}}],
             ["add_edge","game","has_control_bundle","bundle",{}],
             ["add_edge","bundle","includes_control","control",{}]]},
 {"name":"control_bundle_initial_status","area":"motor","order":1,"latency_class":"hard_realtime",
  "match":[["game","has_control_bundle","bundle"]],
  "where":Eq(A("bundle","status"),L(None)),
  "effects":[["set_attr","bundle","status","proposed"]]},
 {"name":"control_bundle_rejects_same_axis_pair","area":"motor","order":1,"latency_class":"hard_realtime",
  "match":[["bundle","includes_control","a"],["a","exclusive_with","b"]],
  "where":Exists(N(V("bundle"),"includes_control"),"x",Eq(V("x"),V("b"))),
  "effects":[["set_attr_if_different","bundle","status","inadmissible"]]},
 {"name":"control_bundle_mints_one_tick_intent","area":"motor","order":1,"latency_class":"hard_realtime",
  "match":[["game","has_control_bundle","bundle"]],
  "where":And(Eq(A("bundle","status"),L("proposed")),
              Not(Exists(N(V("bundle"),"has_intent"),"i",L(True)))),
  "effects":[["add_node","intent","ActionIntent",{
                "created_tick":{"__term__":A("game","world_tick")},
                "expires_tick":{"__term__":Plus(
                    A("game","world_tick"),
                    A("game","intent_horizon_ticks"))},
                "status":"proposed"}],
             ["add_edge","bundle","has_intent","intent",{}],
             ["add_edge","intent","enacts_bundle","bundle",{}]]},
 {"name":"control_trial_count_enacted_bundle_once","area":"learning","order":1,
  "latency_class":"soft_realtime",
  "match":[["intent","enacts_bundle","bundle"],
           ["bundle","includes_control","control"]],
  "where":And(Eq(A("intent","status"),L("enacted")),
              Lt(A("control","last_trial_epoch"),A("intent","enacted_tick"))),
  "effects":[["set_attr_if_different","control","n_trials",
               {"__term__":Plus(A("control","n_trials"),L(1))}],
             ["set_attr_if_different","control","last_trial_epoch",
               {"__term__":A("intent","enacted_tick")}]]}]
MANIFEST={"id":"control_bundle","version":"1.0.0","self_load_only":True,
 "depends_on":["affordance_basis","discovered_navigation","motor_core","information_commitment"],
 "area":"motor",
 "description":"Bridge existing cognition to simultaneous physical control. Worlds publish independent ControlAxis/Control nodes. Graph-resolved retinal attention selects an orienting primitive while curiosity independently explores the least-tried compatible apparatus axis; navigation and held operate terms may compose with both. Enacted bundle membership, not a scalar host action label, advances every primitive's trial memory. No Python action scorer and no world-authored combinations.",
 "microtheory":{"name":"control_bundle","description":"independent cognitive control intents -> compatible simultaneous bundle"},
 "nodes":[],"edges":[],
 "productions":[
  {"provenance":"seed:control_bundle:axis","src":{"type":"WorldInstance","var":"g"},"edge_type":"has_control_axis","tgt":{"type":"ControlAxis","var":"a"}},
  {"provenance":"seed:control_bundle:axis-control","src":{"type":"ControlAxis","var":"a"},"edge_type":"has_control","tgt":{"type":"Control","var":"c"}},
  {"provenance":"seed:control_bundle:exclusive","src":{"type":"Control","var":"a"},"edge_type":"exclusive_with","tgt":{"type":"Control","var":"b"}},
  {"provenance":"seed:control_bundle:game-control","src":{"type":"WorldInstance","var":"g"},"edge_type":"has_control","tgt":{"type":"Control","var":"c"}},
  {"provenance":"seed:control_bundle:selected","src":{"type":"WorldInstance","var":"g"},"edge_type":"selected_control","tgt":{"type":"Control","var":"c"}},
  {"provenance":"seed:control_bundle:bundle","src":{"type":"WorldInstance","var":"g"},"edge_type":"has_control_bundle","tgt":{"type":"ControlBundle","var":"b"}},
  {"provenance":"seed:control_bundle:includes","src":{"type":"ControlBundle","var":"b"},"edge_type":"includes_control","tgt":{"type":"Control","var":"c"}},
  {"provenance":"seed:control_bundle:intent","src":{"type":"ControlBundle","var":"b"},"edge_type":"has_intent","tgt":{"type":"ActionIntent","var":"i"}},
  {"provenance":"seed:control_bundle:enacts","src":{"type":"ActionIntent","var":"i"},"edge_type":"enacts_bundle","tgt":{"type":"ControlBundle","var":"b"}},
  {"provenance":"seed:control_bundle:agent","src":{"type":"WorldInstance","var":"g"},"edge_type":"for_agent","tgt":{"type":"Agent","var":"a"}}],
 "rules":RULES}
if __name__=="__main__":
 with open(OUT,"w") as f:json.dump(MANIFEST,f,indent=1)
 print(f"wrote {OUT} with {len(RULES)} rules")
