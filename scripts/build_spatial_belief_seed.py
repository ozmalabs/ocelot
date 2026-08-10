"""Emit world-agnostic occupancy belief accumulation rules."""
from __future__ import annotations
import json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"seeds","spatial_belief_core.json")
def V(n):return {"type":"Var","name":n}
def L(v):return {"type":"Lit","value":v}
def A(n,k):return {"type":"Attr","node":V(n),"key":k}
def Eq(a,b):return {"type":"Eq","a":a,"b":b}
def And(*x):return {"type":"And","items":list(x)}
def Or(*x):return {"type":"Or","items":list(x)}
def Not(x):return {"type":"Not","arg":x}
def N(n,e):return {"type":"Neighbours","node":n,"edge_type":e,"any_type":False}
def Exists(s,v,p):return {"type":"Exists","source":s,"var_name":v,"predicate":p}
def Idx(s,i):return {"type":"IndexAt","seq":s,"index":L(i)}
POSE=A("obs","pose")
PEQ=lambda a,b:And(Eq(Idx(a,0),Idx(b,0)),Eq(Idx(a,1),Idx(b,1)))
NO_CELL=Not(Exists(N(V("space"),"has_cell"),"cell2",PEQ(A("cell2","pose"),POSE)))
ON=Eq(A("space","spatial_belief"),L(1.0))
RULES=[
 {"name":"spatial_belief_free_new","area":"spatial","order":1,"latency_class":"soft_realtime",
  "match":[["space","observed","obs"]],
  "where":And(ON,Or(Eq(A("obs","src"),L("walk")),Eq(A("obs","src"),L("seen_free"))),NO_CELL),
  "effects":[["add_node","cell","Cell",{"world_type":"Cell","pose":{"__term__":POSE},"value":0.0}],
             ["add_edge","space","has_cell","cell",{}]]},
 {"name":"spatial_belief_wall_new","area":"spatial","order":1,"latency_class":"soft_realtime",
  "match":[["space","observed","obs"]],
  "where":And(ON,Eq(A("obs","src"),L("seen_wall")),NO_CELL),
  "effects":[["add_node","cell","Cell",{"world_type":"Cell","pose":{"__term__":POSE},"value":1.0}],
             ["add_edge","space","has_cell","cell",{}]]},
 {"name":"spatial_belief_walk_corrects_wall","area":"spatial","order":1,"latency_class":"soft_realtime",
  "match":[["space","observed","obs"],["space","has_cell","cell"]],
  "where":And(ON,Eq(A("obs","src"),L("walk")),PEQ(POSE,A("cell","pose")),Eq(A("cell","value"),L(1.0))),
  "effects":[["set_attr_if_different","cell","value",0.0]]}]
MANIFEST={"id":"spatial_belief_core","version":"1.0.0","self_load_only":True,
 "depends_on":["cognitive_areas"],"area":"spatial",
 "description":"World-agnostic persistent occupancy belief from self-location and seen free/wall observations. Unknown is absence; walking is authoritative. Worlds supply only vision, proprioception and affordances.",
 "microtheory":{"name":"spatial_belief_core","description":"observation -> persistent free/wall belief"},
 "nodes":[],"edges":[],
 "productions":[
  {"provenance":"seed:spatial:observation","src":{"type":"WorldInstance","var":"space"},"edge_type":"observed","tgt":{"type":"ObsCell","var":"obs"}},
  {"provenance":"seed:spatial:belief","src":{"type":"WorldInstance","var":"space"},"edge_type":"has_cell","tgt":{"type":"Cell","var":"cell"}}],
 "rules":RULES}
if __name__=="__main__":
 with open(OUT,"w") as f:json.dump(MANIFEST,f,indent=1)
 print(f"wrote {OUT} with {len(RULES)} rules")
