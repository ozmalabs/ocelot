"""Emit seeds/control_kinds.json — the OPEN control-kind taxonomy classifier. The KINDS are grounded on demand
(domains/control_grounding.ground_control_kind mints a ControlKind from any wiki gloss — seeded starter set AND
arbitrarily more). This seed holds the graph-native classifier that reads a grounded kind's NAME and assigns its
effect_family from the MOST-SPECIFIC matching signal-word — itself OPEN (drop in more FamilySignal rows to
recognise more kinds/families).

  FamilySignal data : signal-word -> (effect_family, spec[ificity]). Specific words (rotary, joystick, trackball)
                      have higher spec than generic ones (button, switch), so "rotary switch" classifies as
                      discrete_select (rotary, spec 2) not discrete_act (switch, spec 1).
  classify_kind_family : effect_family = the family of the highest-spec signal whose word is in the kind's name
                         (Argmax over the matching signals by spec). Kind name matched, not the gloss, so generic
                         words that appear incidentally in definitions don't pollute. Single-fire per kind.
"""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def V(n): return {"type":"Var","name":n}
def A(n,k): return {"type":"Attr","node":V(n),"key":k}
def L(v): return {"type":"Lit","value":v}
def P0(n,k): return {"type":"Plus","items":[A(n,k),L(0.0)]}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def And(*xs): return {"type":"And","items":list(xs)}
def Count(src): return {"type":"Count","source":src}
def NodesOf(t): return {"type":"NodesOfType","node_type":t}
def Filter(src,var,pred): return {"type":"Filter","source":src,"var_name":var,"predicate":pred}
def Argmax(src,var,val,default): return {"type":"Argmax","source":src,"var_name":var,"value":val,"default":default}
def Idx(h,n): return {"type":"StringIndexOf","haystack":h,"needle":n}
def AttrOf(node_term,k): return {"type":"Attr","node":node_term,"key":k}

# (word, family, specificity). Specific kind-nouns outrank generic mechanism words.
SIGNALS=[("trackball","relative_pointer",3),("trackpad","relative_pointer",3),("touchpad","relative_pointer",3),
  ("mouse","relative_pointer",3),("pointer","relative_pointer",2),("touch","relative_pointer",2),
  ("joystick","continuous_direction",3),("stick","continuous_direction",2),
  ("rotary","discrete_select",2),("knob","discrete_select",2),("dial","discrete_select",2),
  ("steering","continuous_rotation",3),("wheel","continuous_rotation",2),("paddle","continuous_rotation",2),
  ("slider","range_1dof",3),("throttle","range_1dof",3),("lever","range_1dof",3),("pedal","range_1dof",3),
  ("button","discrete_act",1),("switch","discrete_act",1),("trigger","discrete_act",2),
  ("gamepad","discrete_act",2),("key","discrete_act",1)]

nodes=[{"local_id":0,"type":"SignalRegistry","attrs":{"name":"control_family_signals"}}]
edges=[]
for i,(w,f,s) in enumerate(SIGNALS,1):
    nodes.append({"local_id":i,"type":"FamilySignal","attrs":{"word":w,"family":f,"spec":float(s)}})
    edges.append({"src":{"local":0},"type":"has_signal","tgt":{"local":i},"attrs":{}})

# signals whose word is in this kind's name
matching=Filter(NodesOf("FamilySignal"),"fs",Gt(Idx(A("ck","name_lc"),A("fs","word")),L(-1.0)))
best=Argmax(matching,"fs",P0("fs","spec"),V("ck"))
classify={"name":"classify_kind_family",
  "comment":"effect_family = family of the most-specific signal-word found in the kind's NAME (Argmax by spec). "
            "Name-matched so generic words in definitions don't pollute; specificity breaks multi-word ties "
            "(rotary switch -> discrete_select). Single-fire per kind. OPEN: more signals/kinds extend it, no code.",
  "match":[["kreg","has_kind","ck"]],
  "where":And(Lt(P0("ck","family_set"),L(0.5)),Gt(Count(matching),L(0.5))),
  "effects":[["set_attr","ck","effect_family",{"__term__":AttrOf(best,"family")}],
             ["set_attr","ck","family_set",1.0]]}

seed={"id":"control_kinds","version":"1.0.0","depends_on":[],
      "description":"The OPEN control-kind taxonomy classifier. Kinds are grounded on demand from the on-disk "
        "wiki (a starter set + arbitrarily more); this seed reads a grounded kind's name and assigns its "
        "effect_family from the most-specific matching signal-word. Both kinds and the signal table extend with "
        "no code — reason from grounded knowledge, don't brute-force.",
      "microtheory":{"name":"control_kinds","description":"control kinds are grounded knowledge (open taxonomy); "
        "a kind's effect_family is read from its name/gloss via specificity-weighted signals"},
      "nodes":nodes,"edges":edges,"productions":[],"rules":[classify]}
out=os.path.join(ROOT,"seeds","control_kinds.json")
tmp=out+".tmp"; json.dump(seed,open(tmp,"w"),indent=1); json.load(open(tmp)); os.replace(tmp,out)
print("wrote",os.path.relpath(out,ROOT),"-",len(SIGNALS),"signals,",len(seed["rules"]),"rule")
