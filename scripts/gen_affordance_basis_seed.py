"""Emit seeds/affordance_basis.json — STEP 1 of the N-dim frame-understanding integration
(docs/jabberwock_nd_frame_understanding_design.md). The world declares each control as a Control node carrying
NO GEOMETRY (just a name); the agent LEARNS each control's displacement vector by observing how its self-region
moves after firing that control. This replaces the four hardcoded resp_Up/Down/Left/Right rules in
nd_action_correlation with ONE affordance-generic learner over Control nodes — an affordance becomes a learned
basis-displacement, not a handed (drow,dcol).

  mint_control_response : one ControlResponse per (region, control), minted once (control_confirm idiom).
  learn_control_delta   : EMA cr.(dr,dc) toward the region's observed (drow,dcol) on frames where that control
                          was the last action. Clocked EMA folded at the clock edge.

Graph rules only; Control nodes + has_control edges are the world's affordance declaration (admissible adapter
I/O). Verified by scripts/verify_affordance_basis.py.
"""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def V(n): return {"type":"Var","name":n}
def A(n,k): return {"type":"Attr","node":V(n),"key":k}
def L(v): return {"type":"Lit","value":v}
def P0(n,k): return {"type":"Plus","items":[A(n,k),L(0.0)]}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def Times(*xs): return {"type":"Times","items":list(xs)}
def Minus(a,b): return {"type":"Minus","a":a,"b":b}
def Plus(*xs): return {"type":"Plus","items":list(xs)}
def Count(src): return {"type":"Count","source":src}
def Neigh(n,e): return {"type":"Neighbours","node":V(n),"edge_type":e,"any_type":False}
def Filter(src,var,pred): return {"type":"Filter","source":src,"var_name":var,"predicate":pred}

# EMA toward target with rate 0.3: cur + 0.3*(target - cur)
def ema(cur_n,cur_k, tgt_n,tgt_k):
    cur=P0(cur_n,cur_k); tgt=P0(tgt_n,tgt_k)
    return Plus(cur, Times(L(0.3), Minus(tgt, cur)))

# mint one ControlResponse per (region, control): guard = no existing responds_via cr whose cname == c.name
mint={"name":"mint_control_response",
      "comment":"one ControlResponse per (region,control), minted once (control_confirm idiom). The control "
                "carries no geometry; this slot will hold the LEARNED displacement vector for that control on "
                "that region.",
      "match":[["game","has_region","r"],["game","has_control","c"]],
      "where":Lt(Count(Filter(Neigh("r","responds_via"),"cr",Eq(A("cr","cname"),A("c","name")))),L(0.5)),
      "effects":[["add_node","cr","ControlResponse",{"dr":0.0,"dc":0.0,"n":0.0}],
                 ["add_edge","r","responds_via","cr"],
                 ["add_edge","cr","to_control","c"],
                 ["set_attr","cr","cname",{"__term__":A("c","name")}]]}

# learn the control's displacement: on frames where this control was the last action, EMA the slot toward the
# region's OBSERVED (drow,dcol). drow/dcol are perceptual observations (admissible); the control's effect is learned.
learn={"name":"learn_control_delta",
       "comment":"EMA each (region,control) response toward the region's observed (drow,dcol) on frames where "
                 "that control was fired. An affordance's effect is LEARNED, never given.",
       "match":[["game","has_region","r"],["r","responds_via","cr"],["cr","to_control","c"]],
       "where":Eq(A("game","last_action"),A("c","name")),
       "effects":[["set_attr","cr","clocked",1.0],
                  ["set_attr","cr","next_dr",{"__term__":ema("cr","dr","r","drow")}],
                  ["set_attr","cr","next_dc",{"__term__":ema("cr","dc","r","dcol")}],
                  ["set_attr","cr","next_n",{"__term__":Plus(P0("cr","n"),L(1.0))}]]}

seed={"id":"affordance_basis","version":"1.0.0","depends_on":[],
      "description":"STEP 1 of N-dim frame understanding: learn each control's displacement vector from "
        "observation (the world declares controls as geometry-free Control nodes; the agent learns their "
        "effect). One affordance-generic learner replaces the four hardcoded resp_<dir> rules. The learned "
        "ControlResponse.(dr,dc) per (self-region,control) are the control basis-vectors nd_basis_discovery "
        "(step 2: principal_axes) will turn into the discovered frame's axes.",
      "microtheory":{"name":"affordance_basis","description":"learn control displacement vectors from "
        "observation; affordances are learned basis-displacements, not handed geometry"},
      "nodes":[],"edges":[],"productions":[],"rules":[mint,learn]}
out=os.path.join(ROOT,"seeds","affordance_basis.json")
tmp=out+".tmp"; json.dump(seed,open(tmp,"w"),indent=1); json.load(open(tmp)); os.replace(tmp,out)
print("wrote",os.path.relpath(out,ROOT),"-",len(seed["rules"]),"rules")
