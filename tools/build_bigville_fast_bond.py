"""Emit seeds/bigville_fast_bond.json (block 287000) -- the TARGET-SENSITIVE FAST
PATH. The 282000-c finding: the shallow collapse ties on impulse (every `help`=0.7)
and settles the first co-present target before the deep pass reads the Bond, so a
friend loses to a neutral. Fix: a CHEAP bond signal in the impulse itself -- the
gut-pull toward someone you like -- so the fast path is already roughly
bond-directed, no first deliberation needed. Composes with (does not replace)
learned internalization (286000): innate gut-pull + learned habit.

  fb_fast_bond: impulse := base_weight + fast_gain * (affect_affection - affect_resentment)
    for a directed option whose target is co-present (sees) and held-in-Bond.

The nudge is SMALL (fast_gain << the deep supergraph coupling): the fast path is a
cheap approximation; the deep plan_value stays the full model. FALSIFIER:
fast_gain=0 -> impulse = base_weight -> the 282000-c targeting failure returns.
ZERO new Rust; self_load_only.
"""
import json, os
def V(n): return {"type":"Var","name":n}
def A(nd,k): return {"type":"Attr","node":nd,"key":k}
def Plus(*it): return {"type":"Plus","items":list(it)}
def Minus(a,b): return {"type":"Minus","a":a,"b":b}
def Times(*it): return {"type":"Times","items":list(it)}
def T(t): return {"__term__":t}

RULE={
 "name":"fb_fast_bond","batch":False,
 "comment":("TARGET-SENSITIVE FAST PATH: a cheap bond signal nudges a directed "
  "option's impulse (the shallow/gut pull) so help@friend outpulls help@neutral "
  "WITHOUT deliberation -- resolving the 282000-c weak-bond targeting finding. "
  "impulse = base_weight + fast_gain*(affection - resentment), only for a "
  "co-present, held-in-Bond target. SMALL vs the deep supergraph plan_value "
  "coupling -- the fast path approximates, the deep path computes. FALSIFIER: "
  "fast_gain=0 -> impulse=base_weight -> targeting fails again."),
 "match":[["m","in_scene","d"],["d","aims_at","o"],["m","sees","o"],
          ["m","holds_bond","bond"],["bond","toward","o"]],
 "effects":[["set_attr","d","impulse",
   T(Plus(A(V("d"),"base_weight"),
          Times(A(V("m"),"fast_gain"),
                Minus(A(V("bond"),"affect_affection"),
                      A(V("bond"),"affect_resentment")))))]],
}
def build():
    return {"id":"bigville_fast_bond","version":"1.0.0","depends_on":[],
     "self_load_only":True,
     "description":("TARGET-SENSITIVE FAST PATH (block 287000). A cheap bond signal "
      "nudges a directed option's shallow impulse so the fast collapse is roughly "
      "bond-directed (help@friend > help@neutral) without a first deliberation -- "
      "the innate gut-pull resolving the 282000-c weak-bond targeting finding; "
      "composes with learned internalization (286000). impulse = base_weight + "
      "fast_gain*(affection - resentment), co-present held-in-Bond targets only; "
      "SMALL vs the deep supergraph plan_value. FALSIFIER: fast_gain=0. ZERO new "
      "Rust; self_load_only."),
     "nodes":[],"edges":[],"productions":[],"concepts":[],"rules":[RULE]}
if __name__=="__main__":
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out=os.path.join(root,"seeds","bigville_fast_bond.json")
    json.dump(build(),open(out,"w"),indent=1); print("wrote",out)
