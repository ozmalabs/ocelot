"""remote_operate_seed — RUNG 230000: PERFORM THE ACTION ON THE CROSS —
exhaust the ACTION space on the reached object, DISCOVER the actuating action.

THE OWNER INSIGHT. Block 229's live run REACHED and "interacted with" the cross
but observed 0 distal change — because "interacted" meant co-located / bumped; the
agent NEVER issued the game's ACTION (use / select) ON the cross. A switch fires
when ACTUATED, not walked into. Owner: "it may need to perform the 'action' on the
cross."

THE FIX EXTENDS THE EXHAUSTION PRINCIPLE FROM THE OBJECT SPACE (226/228 — go to the
only un-visited salient object) TO THE ACTION SPACE: at the reached salient object,
TRY EVERY available game action on it — the movement actions AND the
interact/use/select action (like block 210's `op_use`) — because "I've tried
everything" is not complete until it has tried *acting on* the thing, not just
moving into it. DISCOVER which action actuates it (the one that produces an
observable remote change) — NOT hardcode "ACTION5 = use". The elicited change flows
into 229's `rcg_ground` (`causes(object, effect)`), which grounds it the instant it
appears.

This is a SEED BUILDER (emits graph data — the allowed Python under the
architecture rule). It contains NO agent decision in Python: every decision (which
action to try next; that a remote change was produced → discover the operate
action) is a rule `where`-clause over graph state. The host adapter
(worlds/remote_operate.py) only enumerates the AVAILABLE actions as GameAction
nodes, issues the rule-chosen action AT the object, OBSERVES the real before→after
remote change, and writes an ActionOutcome (+ a 229 Observation).

THE RULES (guarded on game.operate_on==1; default-OFF, byte-identical to any graph
that does not set the flag):

  ro_try_action     — POLICY `exhaust_actions`: exhaust the ACTION space. Match the
    min-ordinal UNTRIED GameAction (a `Not Exists` "no untried action with smaller
    ordinal" guard makes exactly ONE fire per pass), set g.try_action, mark tried.
    Tries the interact/use action too — NOT just movement.
  ro_try_movement   — POLICY `movement_only` (the CONTROL): same, but restricted to
    is_movement==1 actions. It NEVER issues the non-movement interact/use action →
    never actuates → no observable change → nothing to discover / ground / pass.
  ro_discover_operate — HEADLINE: an ActionOutcome with remote_changed==1 (an
    OBSERVED remote change) → mint Operates{action, object, effect} + `operates`
    edge + set g.operate_action = <the action id FROM THE OUTCOME>, g.discovered=1.
    The actuating action is DISCOVERED FROM THE OBSERVED OUTCOME, never a hardcoded
    action id (mint-once guard). The rule reads oc.remote_changed + oc.action_id; it
    names no action id.

COMPOSES WITH 229 UNCHANGED. On one Game node (arm="observe" for 229; op_policy for
230), the Observation the adapter writes when the actuating action fires
(interact=1, remote_changed=1) is consumed by 229's rcg_ground → mints the
persistent causes(object, effect) fact; rcg_knows_and_acts → rcg_pass close the
loop. movement_only never issues the use action → never observes a remote change →
229 grounds nothing → never passes.

Domain-agnostic: the rules name NO ls20/doom/cross/lever/rotation/action-id
constant — the actuating action id + the effect kind are carried through from the
OBSERVED ActionOutcome. `is_movement` is a mechanical property of the ARC-AGI-3
action set the adapter writes (ACTION1-4 moves; ACTION5/6 interact/click); the
discovery reads remote_changed, NOT is_movement. Integer-native. No Rust, no new
Term — reuses the 210 operate seek/use, the 228 reach, the 229 ground, the 220 nav.
"""
from __future__ import annotations

import json
from pathlib import Path


# --- Term-tree builders (same vocabulary as domains/remote_causal_ground_seed.py) --
def V(n):        return {"type": "Var", "name": n}
def A(n, k):     return {"type": "Attr", "node": V(n), "key": k}
def L(v):        return {"type": "Lit", "value": v}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}
def Lt(a, b):    return {"type": "Lt", "a": a, "b": b}
def And(*x):     return {"type": "And", "items": list(x)}
def Or(*x):      return {"type": "Or", "items": list(x)}
def Not(a):      return {"type": "Not", "arg": a}
def T(term):     return {"__term__": term}


def _nb(node_var, edge):
    return {"type": "Neighbours", "node": V(node_var), "edge_type": edge, "any_type": False}


def _exists(node_var, edge, sub_var, predicate):
    return {"type": "Exists", "source": _nb(node_var, edge), "var_name": sub_var,
            "predicate": predicate}


def _at_object(policy):
    """The common guard: this block is ON, we are at the reached object, and we have
    not yet discovered the actuating action (mint-once / stop-exhausting)."""
    return And(Eq(A("g", "operate_on"), L(1.0)),
               Eq(A("g", "op_policy"), L(policy)),
               Eq(A("g", "at_object"), L(1.0)),
               Eq(A("g", "discovered"), L(0.0)))


def _try_effects():
    # The rule SELECTS the next action to try (sets g.try_action) — it does NOT mark
    # `tried`. Marking `tried` is the adapter's MECHANICAL bookkeeping AFTER it issues
    # the rule-chosen action (recording "I issued this", like 210 pressing the button
    # the graph names). This keeps the rule idempotent within a run_rules fixpoint
    # (it re-selects the same min-ordinal untried action and sets the same value), so
    # the adapter drives ONE action per step instead of the fixpoint exhausting all
    # actions internally with no chance to observe each outcome.
    return [["set_attr", "g", "try_action", T(A("a", "action_id"))],
            ["set_attr", "g", "try_is_movement", T(A("a", "is_movement"))],
            ["set_attr", "g", "try_ordinal", T(A("a", "ordinal"))]]


# --------------------------------------------------------------------------
# THE RULES — exhaust the action space, discover the actuating action.
# --------------------------------------------------------------------------
def _rules():
    rules = []

    # ---- EXHAUST THE ACTION SPACE (policy exhaust_actions) ----------------
    # Try EVERY available action ON the object, in ordinal order — the interact/use
    # action too. The min-ordinal-untried guard fires exactly ONE per pass; the
    # `tried` flag self-advances the exhaustion.
    rules.append({
        "name": "ro_try_action",
        "comment": "EXHAUST THE ACTION SPACE (exhaust_actions): pick the min-ordinal UNTRIED "
                   "GameAction and issue it AT the object — the interact/use action too, not "
                   "just movement. Exactly one fires per pass (no smaller untried exists).",
        "match": [["g", "has_action", "a"]],
        "where": And(_at_object("exhaust_actions"),
                     Eq(A("a", "tried"), L(0.0)),
                     Not(_exists("g", "has_action", "a2",
                                 And(Eq(A("a2", "tried"), L(0.0)),
                                     Lt(A("a2", "ordinal"), A("a", "ordinal")))))),
        "effects": _try_effects(),
    })

    # ---- MOVEMENT-ONLY CONTROL (policy movement_only) --------------------
    # The 229-null baseline in ACTION space: try ONLY the movement actions. It never
    # issues the non-movement interact/use action -> never actuates -> no observable
    # change -> nothing to discover / ground / pass. Isolates "did you try ACTING on
    # it, or just moving?".
    rules.append({
        "name": "ro_try_movement",
        "comment": "MOVEMENT-ONLY CONTROL (movement_only): pick the min-ordinal untried "
                   "MOVEMENT action only (is_movement==1). NEVER issues the interact/use "
                   "action -> never actuates the switch.",
        "match": [["g", "has_action", "a"]],
        "where": And(_at_object("movement_only"),
                     Eq(A("a", "tried"), L(0.0)),
                     Eq(A("a", "is_movement"), L(1.0)),
                     Not(_exists("g", "has_action", "a2",
                                 And(Eq(A("a2", "tried"), L(0.0)),
                                     Eq(A("a2", "is_movement"), L(1.0)),
                                     Lt(A("a2", "ordinal"), A("a", "ordinal")))))),
        "effects": _try_effects(),
    })

    # ---- DISCOVER THE OPERATE ACTION (HEADLINE) --------------------------
    # An ActionOutcome that OBSERVED a remote change (remote_changed==1) -> the action
    # that produced it IS the operate action. Mint Operates{action, object, effect}
    # FROM THE OBSERVED OUTCOME (the action id flows from the data — the rule names no
    # action id). Mint-once (g.discovered==0). Works for either policy: movement_only
    # simply never produces such an outcome.
    rules.append({
        "name": "ro_discover_operate",
        "comment": "DISCOVER (headline): an ActionOutcome with an OBSERVED remote change -> the "
                   "action that produced it is the OPERATE action. Mint Operates{action,object,"
                   "effect} from the observed outcome (DISCOVERED, not hardcoded); mint-once.",
        "match": [["g", "has_outcome", "oc"], ["g", "has_action", "a"]],
        "where": And(Eq(A("g", "operate_on"), L(1.0)),
                     Or(Eq(A("g", "op_policy"), L("exhaust_actions")),
                        Eq(A("g", "op_policy"), L("movement_only"))),
                     Eq(A("oc", "remote_changed"), L(1.0)),
                     Eq(A("oc", "action_id"), A("a", "action_id")),
                     Eq(A("g", "discovered"), L(0.0))),
        "effects": [
            ["add_node", "op", "Operates", {
                "action": T(A("oc", "action_id")),
                "object": T(A("g", "object_id")),
                "effect": T(A("oc", "effect_kind")),
            }],
            ["add_edge", "g", "has_operates", "op"],
            ["add_edge", "a", "operates", "op"],
            ["set_attr", "g", "operate_action", T(A("oc", "action_id"))],
            ["set_attr", "g", "discovered", 1.0],
            ["set_attr", "g", "discovered_is_movement", T(A("a", "is_movement"))],
            ["set_attr", "g", "discovered_effect", T(A("oc", "effect_kind"))],
        ],
    })

    return rules


RULES = _rules()


def manifest():
    return {
        "id": "remote_operate",
        "version": "1.0.0",
        "depends_on": [],
        "area": "retina",
        "description": (
            "PERFORM THE ACTION ON THE CROSS (block 230000): exhaust the ACTION space on the "
            "reached object and DISCOVER the actuating action. Extends the 226/228 exhaustion "
            "principle from the OBJECT space to the ACTION space: at the reached object, try "
            "EVERY available action ON it — the movement actions AND the interact/use action "
            "(210 op_use) — because 'tried everything' is not complete until it has tried ACTING "
            "on the thing, not just moving into it. ro_try_action (policy exhaust_actions) picks "
            "the min-ordinal untried GameAction (exactly one per pass) and issues it; "
            "ro_try_movement (policy movement_only, the CONTROL) tries only movements; "
            "ro_discover_operate mints Operates{action,object,effect} from an ActionOutcome that "
            "OBSERVED a remote change — the actuating action DISCOVERED from the observed outcome, "
            "never hardcoded. Composes with 229 UNCHANGED: the Observation the adapter writes when "
            "the actuating action fires is consumed by rcg_ground -> causes(object,effect). "
            "Domain-agnostic (no cross/rotation/action-id constant; the id + effect carried from "
            "the OBSERVED outcome). Guarded on game.operate_on==1 (default-OFF, byte-identical) + "
            "game.op_policy. Integer-native; no Rust; reuses 210 operate + 228 reach + 229 ground "
            "+ 220 nav."),
        "microtheory": {
            "name": "remote_operate",
            "description": "'Tried everything' includes ACTING ON the thing, not just moving into "
                           "it. At the reached object the agent exhausts the ACTION space — every "
                           "available action, the interact/use action too — and DISCOVERS which "
                           "one actuates it by OBSERVING which produces a remote change. The "
                           "actuator is discovered from observation, never hardcoded; the elicited "
                           "change is what 229 grounds. Every decision is a rule; the adapter only "
                           "issues the chosen action and perceives the result.",
        },
        "nodes": [], "edges": [], "productions": [],
        "rules": RULES,
    }


def write_seed(path=None):
    p = Path(path) if path else Path(__file__).resolve().parent.parent / "seeds" / "remote_operate.json"
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())
