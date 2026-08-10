"""Emit seeds/control_dynamic.json — DYNAMIC, graph-native control-type formation. Control kinds are not a fixed
list: the agent RECOGNISES a control from a grounded prior when it can, and MINTS ITS OWN ControlKind from
OBSERVATION when it can't (a novel/alien control with no wiki article), then ADJUSTS that minted kind as it
observes more. No LLM anywhere — wiki is the cheap non-LLM prior, observation is the non-LLM dynamic minter, and
all the recognise/mint/refine logic is graph rules.

  recognise_kind         : a control whose kind was grounded (wiki_grounded) links to the ControlKind whose name
                           matches its kind_name — recognise from the prior, no minting.
  mint_own_kind          : a control NOT grounded (no prior) but with an OBSERVED effect-signature mints a brand-
                           new ControlKind from that observation (effect_family + rep_param), linked is_kind.
                           This is the agent authoring its own control type, dynamically, from what it saw.
  refine_own_kind        : each new observation of a self-minted kind EMAs its rep_param — the type adjusts
                           dynamically as evidence accrues.
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
def Not(x): return {"type":"Not","arg":x}
def And(*xs): return {"type":"And","items":list(xs)}
def Count(src): return {"type":"Count","source":src}
def Neigh(n,e): return {"type":"Neighbours","node":V(n),"edge_type":e,"any_type":False}
def Plus(*xs): return {"type":"Plus","items":list(xs)}
def Times(*xs): return {"type":"Times","items":list(xs)}
def Minus(a,b): return {"type":"Minus","a":a,"b":b}

# recognise from prior: control was grounded -> link to the ControlKind whose name matches (c, ck both bound).
recognise={"name":"recognise_kind",
  "comment":"a control whose kind was grounded from wiki links to the matching ControlKind (recognise from "
            "the prior; no minting). c and ck both match-bound.",
  "match":[["game","has_control","c"],["kreg","has_kind","ck"]],
  "where":And(Gt(P0("c","wiki_grounded"),L(0.5)),
              Lt(Count(Neigh("c","is_kind")),L(0.5)),
              Eq(A("c","kind_name"),A("ck","name"))),
  "effects":[["add_edge","c","is_kind","ck"]]}

# mint its OWN kind from observation: no prior, but an observed effect-signature -> author a new ControlKind.
mint={"name":"mint_own_kind",
  "comment":"a control with NO grounded prior but an OBSERVED effect-signature mints a brand-new ControlKind "
            "from that observation (the agent authoring its own control type, dynamically, no wiki, no LLM).",
  "match":[["game","has_control","c"]],
  "where":And(Lt(P0("c","wiki_grounded"),L(0.5)),
              Gt(P0("c","obs_set"),L(0.5)),
              Lt(Count(Neigh("c","is_kind")),L(0.5))),
  "effects":[["add_node","ck","ControlKind",{"source":"observation","learned":1.0,"family_set":1.0}],
             ["set_attr","ck","effect_family",{"__term__":A("c","obs_family")}],
             ["set_attr","ck","name",{"__term__":A("c","name")}],
             ["set_attr","ck","rep_param",{"__term__":P0("c","obs_param")}],
             ["set_attr","ck","last_seq",{"__term__":P0("c","obs_seq")}],
             ["add_edge","c","is_kind","ck"],
             ["add_edge","kreg","has_kind","ck"]]}

# adjust dynamically: each NEW observation (obs_seq advanced) EMAs the self-minted kind's rep_param.
refine={"name":"refine_own_kind",
  "comment":"a self-minted kind adjusts: each new observation EMAs its rep_param toward what was seen. The type "
            "is not frozen — it tracks evidence.",
  "match":[["c","is_kind","ck"]],
  "where":And(Gt(P0("ck","learned"),L(0.5)),Not(Eq(P0("c","obs_seq"),P0("ck","last_seq")))),
  "effects":[["set_attr","ck","rep_param",{"__term__":Plus(P0("ck","rep_param"),
                Times(L(0.5),Minus(P0("c","obs_param"),P0("ck","rep_param"))))}],
             ["set_attr","ck","last_seq",{"__term__":P0("c","obs_seq")}]]}

# mint/refine need a KindRegistry to hang minted kinds off; recognise needs it to find grounded kinds. The
# grounding routine creates it; seed a fallback so the rules have a kreg even with zero grounded kinds.
nodes=[{"local_id":0,"type":"KindRegistry","attrs":{"name":"control_kinds"}}]
seed={"id":"control_dynamic","version":"1.0.0","depends_on":[],
      "description":"Dynamic, graph-native control-type formation: recognise from a grounded prior when possible, "
        "else MINT a new ControlKind from observation and ADJUST it as evidence accrues. No LLM — wiki prior + "
        "observation, all recognise/mint/refine as graph rules.",
      "microtheory":{"name":"control_dynamic","description":"control types are dynamic: grounded when known, "
        "self-minted from observation when novel, refined as observed — the agent authors its own taxonomy"},
      "nodes":nodes,"edges":[],"productions":[],"rules":[recognise,mint,refine]}
out=os.path.join(ROOT,"seeds","control_dynamic.json")
tmp=out+".tmp"; json.dump(seed,open(tmp,"w"),indent=1); json.load(open(tmp)); os.replace(tmp,out)
print("wrote",os.path.relpath(out,ROOT),"-",len(seed["rules"]),"rules")
