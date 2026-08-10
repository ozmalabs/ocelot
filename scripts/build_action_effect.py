"""seeds/action_effect.json — the MISSING half of the Doom faculty, rebuilt domain-independent.

In Doom the agent pursued objectives by ACTING and LEARNING WHAT THE ACTION CAUSED (curious_agent.py held it;
the migration rebuilt the active loop only for speech). The resident half survives — select_nav_target drives
the agent to a feature, agency/control_confirm finds what it controls — but the OTHER half, "learn the
transition: my action -> the world changed by X", was never rebuilt as a seed. So the agent navigates and
OBSERVES, yet never discovers what acting CAUSES. That is exactly why it stalls on ls20 where Doom did not.

This seed is the transition learner, keyed ONLY on generic machinery (a `game` WorldInstance, an avatar
`reached` cell, a published `outcome` scalar, the agent's `last_action`, its `Action` repertoire). Nothing
arc- or doom-specific — the adapter publishes `outcome` / `last_action` / the `Action` nodes (mechanical I/O),
and the SAME rules learn the action->effect map in any world. The CapabilityAxis `action_effect` stays
unsatisfied until an effect is found, so the agent's curiosity is NOT complacently spent by merely identifying
what things are — it keeps an open, acted-upon question: what do my actions cause here?

  note_outcome        — once per turn, outcome_delta = outcome - outcome_prev (the effect signal).
  credit_action_effect— attribute the delta to the action that caused it (the per-action learned effect).
  mechanic_discovered — a non-zero effect = the transition found; record which action did it.
  satisfy_action_axis — finding an effect saturates the action_effect axis (the open question answered).
"""
import json, os

def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def ADD(a, b): return {"type": "Plus", "items": [a, b]}
def SUB(a, b): return {"type": "Plus", "items": [a, {"type": "Times", "items": [L(-1.0), b]}]}
def MUL(a, b): return {"type": "Times", "items": [a, b]}
def EQ(a, b): return {"type": "Eq", "a": a, "b": b}
def NEQ(a, b): return {"type": "Not", "arg": EQ(a, b)}
def GTE(a, b): return {"type": "Gte", "a": a, "b": b}
def GT(a, b): return {"type": "Gt", "a": a, "b": b}
def LT(a, b): return {"type": "Lt", "a": a, "b": b}
def AND(*xs): return {"type": "And", "items": list(xs)}
def T(x): return {"__term__": x}
is_av = lambda v: EQ(P0(V(v), "is_avatar_cell"), L(1.0))

ALPHA = 0.3            # forward-model learning rate (EMA of expected perceived change).
SURPRISE_THRESH = 25.0  # cells changed FAR beyond the running baseline = the world did something unusual.

# prediction_minus_observation (the jabberwock's own classification of the fix): the EFFECT of an action is
# the PREDICTION ERROR in perception, not the reward. `world_signal` (adapter-published) = cells that changed
# this turn; `baseline` is the agent's learned forward model of how much usually changes (autonomous drift +
# its own motion). surprise = observation - prediction. An action whose surprise is large did something the
# world does not usually do — that is a discovered effect, whether or not the reward moved.
note_outcome = {
    "name": "note_outcome",
    "match": [["game", "reached", "A"]],
    "where": AND(is_av("A"), NEQ(P0(V("game"), "outcome_stamp"), P0(V("game"), "frame"))),
    "effects": [
        ["set_attr", "game", "outcome_delta",
            T(SUB(P0(V("game"), "world_signal"), P0(V("game"), "baseline")))],          # surprise = obs - prediction
        ["set_attr", "game", "baseline",
            T(ADD(P0(V("game"), "baseline"),
                  MUL(L(ALPHA), SUB(P0(V("game"), "world_signal"), P0(V("game"), "baseline")))))],  # update forward model
        ["set_attr", "game", "score_delta",                                                # the SETPOINT signal
            T(SUB(P0(V("game"), "score"), P0(V("game"), "score_prev")))],                   # (feedback_control)
        ["set_attr", "game", "score_prev", T(P0(V("game"), "score"))],
        ["set_attr", "game", "outcome_stamp", T(P0(V("game"), "frame"))],
        ["set_attr", "game", "action_probes", T(ADD(P0(V("game"), "action_probes"), L(1.0)))]]}

# attribute the change to the action that caused it — the per-action learned effect (the transition map).
credit_action_effect = {
    "name": "credit_action_effect",
    "match": [["game", "has_action", "Act"], ["game", "reached", "A"]],
    "where": AND(is_av("A"), EQ(A(V("Act"), "name"), A(V("game"), "last_action")),
                 NEQ(P0(V("Act"), "effect_stamp"), P0(V("game"), "frame"))),
    "effects": [
        ["set_attr", "Act", "effect", T(P0(V("game"), "outcome_delta"))],
        ["set_attr", "Act", "tried", 1.0],
        ["set_attr", "Act", "effect_stamp", T(P0(V("game"), "frame"))]]}

# A SURPRISE is only a LEAD, not the mechanic (the jabberwock's competitive_inhibition + feedback_control
# correction): the world did something unusual, but I don't yet know if it is PROGRESS or just a transition /
# death. Mark the responsible action as a lead and arm a controlled re-test. One lead at a time.
RETEST = 3.0   # times to re-do the lead action (does it reproduce + move the setpoint?) before judging.
lead_detected = {
    "name": "lead_detected",
    "match": [["game", "reached", "A"]],
    "where": AND(is_av("A"), GT(P0(V("game"), "frame"), L(8.0)),
                 GT(P0(V("game"), "outcome_delta"), L(SURPRISE_THRESH)),
                 NEQ(P0(V("game"), "lead_active"), L(1.0)),
                 NEQ(P0(V("game"), "mechanic_found"), L(1.0))),
    "effects": [["set_attr", "game", "lead_active", 1.0],
                ["set_attr", "game", "lead_action", T(A(V("game"), "last_action"))],
                ["set_attr", "game", "lead_tries", 0.0],
                ["set_attr", "game", "lead_surprise", T(P0(V("game"), "outcome_delta"))]]}

# feedback_control: the SETPOINT is the score. The REAL mechanic is an action that moves it. A score gain
# (whenever it happens — pursuing a lead or not) IS progress found: that is the action worth keeping.
progress_found = {
    "name": "progress_found",
    "match": [["game", "reached", "A"]],
    "where": AND(is_av("A"), GT(P0(V("game"), "score_delta"), L(0.0)),
                 NEQ(P0(V("game"), "mechanic_found"), L(1.0))),
    "effects": [["set_attr", "game", "mechanic_found", 1.0],
                ["set_attr", "game", "mechanic_kind", "progress"],
                ["set_attr", "game", "effective_action", T(A(V("game"), "last_action"))]]}

# competitive_inhibition (controlled re-test): while a lead is active, RE-DO the lead action — does the surprise
# reproduce, and does it move the setpoint? The adapter enacts game.forced_action (same seam as babble).
pursue_lead = {
    "name": "pursue_lead",
    "match": [["game", "reached", "A"]],
    "where": AND(is_av("A"), EQ(P0(V("game"), "lead_active"), L(1.0)),
                 NEQ(P0(V("game"), "mechanic_found"), L(1.0)),
                 NEQ(P0(V("game"), "lead_pursue_stamp"), P0(V("game"), "frame"))),
    "effects": [["set_attr", "game", "forced_action", T(A(V("game"), "lead_action"))],
                ["set_attr", "game", "babble_stamp", T(P0(V("game"), "frame"))],   # reuse the enact seam
                ["set_attr", "game", "lead_tries", T(ADD(P0(V("game"), "lead_tries"), L(1.0)))],
                ["set_attr", "game", "lead_pursue_stamp", T(P0(V("game"), "frame"))]]}

# competitive_inhibition (inhibit the dead lead): re-tested RETEST times with no score gain -> it was a
# transition/death, not progress. Inhibit it and resume the search; count it so the budget knows it is spent.
inhibit_lead = {
    "name": "inhibit_lead",
    "match": [["game", "reached", "A"]],
    "where": AND(is_av("A"), EQ(P0(V("game"), "lead_active"), L(1.0)),
                 GTE(P0(V("game"), "lead_tries"), L(RETEST)),
                 NEQ(P0(V("game"), "mechanic_found"), L(1.0))),
    "effects": [["set_attr", "game", "lead_active", 0.0],
                ["set_attr", "game", "leads_inhibited", T(ADD(P0(V("game"), "leads_inhibited"), L(1.0)))]]}

# BABBLE: while the effect is unknown, try an UNTRIED interaction action (Select / Click) — the moves the
# navigator never emits. This is Doom's goal-babbling: act to discover the transition, don't wait to be told.
# One untried interaction per babble slot (game.babble_idx), frame-stamped so once per turn; the adapter reads
# game.forced_action and enacts it. When all are tried with no effect, the agent has learned they do nothing.
babble_interaction = {
    "name": "babble_interaction",
    "match": [["game", "has_action", "Act"]],
    "where": AND(NEQ(P0(V("game"), "mechanic_found"), L(1.0)),
                 NEQ(P0(V("game"), "lead_active"), L(1.0)),          # pause babbling while re-testing a lead
                 EQ(P0(V("Act"), "interaction"), L(1.0)), NEQ(P0(V("Act"), "tried"), L(1.0)),
                 EQ(P0(V("Act"), "idx"), P0(V("game"), "babble_idx")),
                 NEQ(P0(V("game"), "babble_stamp"), P0(V("game"), "frame"))),
    "effects": [
        ["set_attr", "game", "forced_action", T(A(V("Act"), "name"))],
        ["set_attr", "Act", "tried", 1.0],
        ["set_attr", "game", "babble_idx", T(ADD(P0(V("game"), "babble_idx"), L(1.0)))],
        ["set_attr", "game", "babble_stamp", T(P0(V("game"), "frame"))]]}

# RE-CYCLE: once every interaction has been tried with no effect, advance the click target (click_rank) and
# re-arm the interactions, so the agent probes a DIFFERENT feature next round — a genuine search of the
# interaction space, not a single token try. Bounded by CLICK_CAP so it stops once it has tried them all.
CLICK_CAP = 30.0
recycle_babble = {
    "name": "recycle_babble",
    "match": [["game", "reached", "A"]],
    "where": AND(is_av("A"), NEQ(P0(V("game"), "mechanic_found"), L(1.0)),
                 GTE(P0(V("game"), "babble_idx"), L(2.0)), LT(P0(V("game"), "click_rank"), L(CLICK_CAP)),
                 NEQ(P0(V("game"), "recycle_stamp"), P0(V("game"), "frame"))),
    "effects": [
        ["set_attr", "game", "babble_idx", 0.0],
        ["set_attr", "game", "click_rank", T(ADD(P0(V("game"), "click_rank"), L(1.0)))],
        ["set_attr", "game", "recycle_idx", T(ADD(P0(V("game"), "recycle_idx"), L(1.0)))],
        ["set_attr", "game", "recycle_stamp", T(P0(V("game"), "frame"))]]}

# re-arm the interaction actions when a new recycle round begins (cleared_at lags recycle_idx).
clear_tried = {
    "name": "clear_tried",
    "match": [["game", "has_action", "Act"]],
    "where": AND(EQ(P0(V("Act"), "interaction"), L(1.0)),
                 NEQ(P0(V("Act"), "cleared_at"), P0(V("game"), "recycle_idx"))),
    "effects": [["set_attr", "Act", "tried", 0.0],
                ["set_attr", "Act", "cleared_at", T(P0(V("game"), "recycle_idx"))]]}

# finding an effect answers the open question — saturate the action_effect axis.
satisfy_action_axis = {
    "name": "satisfy_action_axis",
    "match": [["game", "probes_axis", "ax"]],
    "where": AND(EQ(P0(V("game"), "mechanic_found"), L(1.0)), NEQ(P0(V("ax"), "saturation"), L(1.0))),
    "effects": [["set_attr", "ax", "saturation", 1.0], ["set_attr", "ax", "shortfall", 0.0]]}

# the open question itself: a CapabilityAxis the frontier ranks, unsatisfied until an effect is learned.
axis_node = {"local_id": 0, "type": "CapabilityAxis", "attrs": {
    "name": "action_effect", "is_axis": 1.0, "saturation": 0.0, "shortfall": 1.0,
    "capability_keys": ["action_effect"],
    "why": "I do not yet know what my actions CAUSE in this world — and identifying what things ARE does not answer it."}}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
seed = {"id": "action_effect", "version": "1.0.0", "depends_on": [],
        "description": ("The domain-independent action->effect transition learner (the missing Doom half): "
            "note_outcome, credit_action_effect, mechanic_discovered, satisfy_action_axis + the action_effect "
            "CapabilityAxis. The adapter publishes outcome/last_action/Action nodes; these rules learn what "
            "acting causes in ANY world. Plugs into doom or arc identically. Fires in master_tick."),
        "nodes": [axis_node], "edges": [], "productions": [], "concepts": [],
        "rules": [note_outcome, credit_action_effect, lead_detected, progress_found, pursue_lead,
                  inhibit_lead, babble_interaction, recycle_babble, clear_tried, satisfy_action_axis]}
path = os.path.join(ROOT, "seeds", "action_effect.json")
json.dump(seed, open(path, "w"), indent=1); json.load(open(path))
print("wrote seeds/action_effect.json:", [r["name"] for r in seed["rules"]], "+ action_effect axis")
