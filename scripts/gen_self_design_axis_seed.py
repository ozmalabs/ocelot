"""Emit seeds/self_design_axis.json — make SELF-DESIGN a capability the agent CHOOSES, but only WHEN IT HAS A
GAP. The autonomy frontier_pick is an Argmax over CapabilityAxis (is_axis==1, eligible iff it has an
investigated_by edge) by the UNDERSTAND-drive value (~ (1-saturation)*1e9). A self_design axis that is always
unsaturated would DOMINATE — the agent would only ever design. So a graph-native GATE ties its saturation to
whether an open DesignGap exists: open gap -> saturation 0 (high value, the agent elects to design); no gap ->
saturation 1 (low value, it pursues its other capabilities). Principled, no LLM.
"""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def V(n): return {"type":"Var","name":n}
def A(n,k): return {"type":"Attr","node":V(n),"key":k}
def L(v): return {"type":"Lit","value":v}
def P0(n,k): return {"type":"Plus","items":[A(n,k),L(0.0)]}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def Gte(a,b): return {"type":"Gte","a":a,"b":b}
def Count(src): return {"type":"Count","source":src}
def NodesOf(t): return {"type":"NodesOfType","node_type":t}
def Filter(src,var,pred): return {"type":"Filter","source":src,"var_name":var,"predicate":pred}
def Ite(c,t,o): return {"type":"IfThenElse","cond":c,"then":t,"other":o}

nodes=[
 {"local_id":0,"type":"CapabilityAxis",
  "attrs":{"name":"self_design","is_axis":1.0,"saturation":1.0,"authoring_exhausted":0.0,"mf_stall":0.0,
           "min_order":0.0,"investigated_count":0.0,
           "description":"design my own faculty for a recognised gap by composing any part of my machinery. "
                         "Chosen only when an open DesignGap exists (gated), so it does not dominate autonomy."}},
 {"local_id":1,"type":"InvestigationOperator",
  "attrs":{"name":"self_design_loop","about":"drives the self_design capability"}},
]
# investigated_by -> eligible for frontier_pick; has_self_design_axis -> the gate rule can find the axis.
edges=[{"src":{"local":0},"type":"investigated_by","tgt":{"local":1},"attrs":{}},
       {"src":{"role":"agent_root"},"type":"has_self_design_axis","tgt":{"local":0},"attrs":{}}]

# GATE: self_design.saturation = 0 iff an open DesignGap exists, else 1. (open gap -> high value -> chosen.)
gate={"name":"gate_self_design_on_gap",
  "comment":"tie self_design's frontier value to whether the agent has a recognised gap: open DesignGap -> "
            "saturation 0 (elect to design); none -> saturation 1 (pursue other capabilities). No domination.",
  "match":[["ag","has_self_design_axis","sd"]],
  "where":{"type":"Lit","value":True},
  "effects":[["set_attr","sd","saturation",{"__term__":
      Ite(Gte(Count(Filter(NodesOf("DesignGap"),"g",Gt(P0("g","open"),L(0.5)))),L(1.0)),L(0.0),L(1.0))}]]}

seed={"id":"self_design_axis","version":"1.0.0","depends_on":[],
      "description":"Adds the self_design CapabilityAxis (frontier-pick eligible) GATED on an open DesignGap, so "
        "the agent chooses to design its own faculties via its own selector ONLY when it has a recognised gap — "
        "no domination of autonomy, no external trigger, no LLM.",
      "microtheory":{"name":"self_design","description":"designing my own faculties is a capability I choose "
        "when I have a gap; the meta-capability over all the others"},
      "nodes":nodes,"edges":edges,"productions":[],"rules":[gate]}
out=os.path.join(ROOT,"seeds","self_design_axis.json")
tmp=out+".tmp"; json.dump(seed,open(tmp,"w"),indent=1); json.load(open(tmp)); os.replace(tmp,out)
print("wrote",os.path.relpath(out,ROOT),"- self_design axis + eligibility + gate-on-gap rule")
