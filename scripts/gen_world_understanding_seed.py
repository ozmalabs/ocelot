"""Emit seeds/world_understanding.json — fold the verified world-understanding interface into a BOOT seed so
it comes up live by default. Contains: the BIND rule (recognise a world -> mint a WorldBinding + the six
universal WorldRole slots), the nesting composition rules (rollup_value / terminal_escalate / terminal_contain
/ reconcile_escalation), the attention interrupt rules (terminal_watch / preempt_for_terminal), and the frame
library (Game + Conversation WorldFrame nodes, with per-role found_by priors). Graph rules only; the consumers
(navigate_alive) + the parallel allocator stay as adapter methods over the held WorkerPool. Seed-manifest
format (effects plural). Verified pieces: world_roles.py, world_nesting.py, world_interrupt.py, world_conversation.py.
"""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def V(n): return {"type":"Var","name":n}
def A(n,k): return {"type":"Attr","node":V(n),"key":k}
def L(v): return {"type":"Lit","value":v}
def P0(n,k): return {"type":"Plus","items":[A(n,k),L(0.0)]}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def Not(x): return {"type":"Not","arg":x}
def And(*xs): return {"type":"And","items":list(xs)}

ROLES=["controllable_locus","affordance_effect","value_signal","dynamics","terminal","goal"]

# BIND: on a world the agent inhabits with no binding yet, mint a WorldBinding + the six universal role slots.
# Single-fires via the world.has_binding guard (set in the effect destroys the precondition).
bind_effects=[["add_node","bnd","WorldBinding",{"kind":"unknown","activation":"active"}],
              ["add_edge","bnd","binds","w"],["set_attr","w","has_binding",1.0]]
for i,r in enumerate(ROLES):
    bind_effects.append(["add_node",f"s{i}","WorldRole",{"role":r,"status":"unbound","confidence":0.0}])
    bind_effects.append(["add_edge","bnd","role",f"s{i}"])
bind_rule={"name":"bind_world","comment":"recognise a world -> mint a WorldBinding + the six universal role "
           "slots (controllable_locus/affordance_effect/value_signal/dynamics/terminal/goal). Game is data; "
           "this names no game-noun. Single-fire via world.has_binding.",
           "match":[["body","inhabits","w"]],
           "where":And(Not(Eq(A("w","world_type"),L(""))), Lt(P0("w","has_binding"),L(0.5))),
           "effects":bind_effects}

rollup={"name":"rollup_value","comment":"child value contributes to parent value via rollup_factor (winning a "
        "sub-world is value in the parent). Applied where the child value role rolls_up_to the parent value role.",
        "match":[["cv","rolls_up_to","pv"]],"where":L(True),
        "effects":[["set_attr","pv","value",{"__term__":{"type":"Times","items":[P0("cv","value"),P0("cv","rollup_factor")]}}]]}
escalate={"name":"terminal_escalate","comment":"a child terminal marked escalates fires the parent terminal "
          "(dying in the environment ends everything).",
          "match":[["cb","parent_binding","pb"],["cb","role","ct"],["pb","role","tp"]],
          "where":And(Eq(A("ct","role"),L("terminal")),Eq(A("tp","role"),L("terminal")),Gt(P0("ct","fired"),L(0.5)),Eq(A("ct","escalation"),L("escalates"))),
          "effects":[["set_attr","tp","fired",1.0]]}
contain={"name":"terminal_contain","comment":"a child terminal marked contained deactivates only the child "
         "subtree (losing a minigame drops back to the overworld).",
         "match":[["cb","role","ct"]],
         "where":And(Eq(A("ct","role"),L("terminal")),Gt(P0("ct","fired"),L(0.5)),Eq(A("ct","escalation"),L("contained"))),
         "effects":[["set_attr","cb","activation","dormant"]]}
reconcile={"name":"reconcile_escalation","comment":"OBSERVED, not declared: a contained child whose parent "
           "actually halted was mis-seeded -> flip to escalates (evidence overwrites the bit).",
           "match":[["cb","parent_binding","pb"],["cb","role","ct"]],
           "where":And(Eq(A("ct","role"),L("terminal")),Gt(P0("ct","fired"),L(0.5)),Eq(A("ct","escalation"),L("contained")),Gt(P0("pb","dynamics_halted"),L(0.5))),
           "effects":[["set_attr","ct","escalation","escalates"]]}
watch={"name":"terminal_watch","comment":"O(1) DEDUCE on a SUSPENDED (backgrounded) binding: roll its stored "
       "terminal forward by its own postulate (hazard_dist -= hazard_vel) each clock tick, no worker, no "
       "perception. Frame-guarded on the binding clock.",
       "match":[["b","role","tr"]],
       "where":And(Eq(A("b","activation"),L("suspended")),Eq(A("tr","role"),L("terminal")),Not(Eq(P0("tr","last_watch"),P0("b","clk")))),
       "effects":[["set_attr","tr","last_watch",{"__term__":P0("b","clk")}],
                  ["set_attr","tr","hazard_dist",{"__term__":{"type":"Minus","a":P0("tr","hazard_dist"),"b":P0("tr","hazard_vel")}}]]}
preempt={"name":"preempt_for_terminal","comment":"extrapolated imminence crossed threshold -> reactivate the "
         "backgrounded binding (pull a worker back) BEFORE the terminal fires.",
         "match":[["b","role","tr"]],
         "where":And(Eq(A("b","activation"),L("suspended")),Eq(A("tr","role"),L("terminal")),Lt(P0("tr","hazard_dist"),{"type":"Plus","items":[P0("tr","preempt_threshold"),L(0.001)]})),
         "effects":[["set_attr","b","activation","active"],["set_attr","b","urgency",1.0],["set_attr","b","preempted",1.0]]}

# frame library (data): Game + Conversation, each a WorldFrame node carrying per-role found_by priors.
def frame_node(lid, kind, shape, fills):
    return {"local_id":lid,"type":"WorldFrame","attrs":{"kind":kind,"shape":shape,
            **{f"fills_{r}":fills[r] for r in fills}}}
frames=[frame_node(0,"Game","prediction_minus_observation",
          {"controllable_locus":"respond_votes","value_signal":"score","terminal":"death","goal":"positive_kind",
           "affordance_effect":"action_delta","dynamics":"region_postulates"}),
        frame_node(1,"Conversation","dialogic_exchange",
          {"controllable_locus":"write_head","value_signal":"uptake_minus_repair","terminal":"breakdown","goal":"intent_satisfied",
           "affordance_effect":"speech_acts","dynamics":"turn_taking_laws"})]

seed={"id":"world_understanding","version":"1.0.0","depends_on":[],
      "description":"The world-understanding interface (the creator's reframe: not a game-player, a world-"
        "understander pointed at a world). Hardcodes only the six universal ROLES; game is data. BIND mints a "
        "WorldBinding + six WorldRole slots on any recognised world; held faculties fill them; worlds nest "
        "(rollup_value/terminal_escalate/contain/reconcile); a backgrounded terminal is deduce-extrapolated "
        "(terminal_watch) and preempts a worker back (preempt_for_terminal). Frames (Game/Conversation) are "
        "priors over how a world-KIND fills the roles. Consumers (navigate_alive) + the parallel allocator are "
        "adapter methods over the held WorkerPool. Built+verified: world_roles/nesting/interrupt/conversation.",
      "microtheory":{"name":"world_understanding","description":"six universal world-roles + frame library; "
        "bind any world, nest worlds, attend per-binding up to system backpressure"},
      "nodes":frames,"edges":[],"productions":[],
      "rules":[bind_rule,rollup,escalate,contain,reconcile,watch,preempt,
               # contact_consequence: the value_signal/terminal FILLER learner — EMA each contacted kind's
               # consequence toward the visible reward (score up / death). Fills the goal (positive) and
               # terminal (negative) roles from outcome; nothing stamped beyond the visible reward.
               {"name":"contact_consequence","comment":"learn a kind's consequence from the visible reward",
                "match":[["g","tracks_consequence","cm"]],
                "where":And(Eq(A("cm","rvalue"),A("g","contact_rvalue")),
                            Not(Eq(A("g","contact_rvalue"),L(0.0)))),
                "effects":[["set_attr","cm","clocked",1.0],["set_attr","cm","tasted",1.0],
                  ["set_attr","cm","next_value",{"__term__":{"type":"Plus","items":[P0("cm","value"),
                    {"type":"Times","items":[L(0.5),{"type":"Minus","a":P0("g","reward"),"b":P0("cm","value")}]}]}}]]}]}
out=os.path.join(ROOT,"seeds","world_understanding.json")
tmp=out+".tmp"; json.dump(seed,open(tmp,"w"),indent=1); json.load(open(tmp)); os.replace(tmp,out)
print("wrote",os.path.relpath(out,ROOT),"-",len(seed["rules"]),"rules,",len(seed["nodes"]),"frame nodes")
