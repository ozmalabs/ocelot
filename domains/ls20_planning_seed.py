"""ls20_planning_seed — RUNG 218000: the SALIENCE -> INVESTIGATE -> ACT planner
as GRAPH RULES (block 218000, closing the ls20 loop see->understand->DO).

This is a SEED BUILDER (emits graph data — the allowed Python under the
architecture rule, exactly like scripts/move_space_planner.py's rule dicts and
worlds/arc.py's seed builders). It contains NO agent decision in Python: every
planning DECISION is a rule `where`-clause over graph state. The host adapter
(worlds/arc_ls20_scenario.py) only writes PERCEPTION facts (does the carried
symbol match the goal form; which stations exist and are used; the required
transform the graph-native sd-loop recognised) and world PHYSICS (apply a
station's transform; step toward the rule-chosen waypoint; score at the goal).

THE DESIGN PRINCIPLE (owner steer): "It works by SALIENCE and INVESTIGATION.
CURIOSITY FIRST. GOAL BLINDNESS is how you lose." The planner is
INVESTIGATION-driven, not search-driven:

  SALIENCE   — the symbol<->goal MISMATCH is salient (surprise -> ORIENT). The
               perceptual fact `symbol_matches_goal==0` is the surprise; the
               `plan_orient` rule flags it and sets affect=surprise_orient
               (reusing the 208000 surprise->ORIENT emotion vocabulary).
  INVESTIGATE— the agent PROBES the salient: the required transformation is
               RECOGNISED by the general sd-loop (217000 TransformDecode/DimInfer
               — genuine recognition, graph-native), yielding `req_key` on the
               game; the agent then seeks the station whose transform MATCHES the
               recognised key (`plan_seek_station` — investigation, not just any
               detour). That is the 217000 -> 218000 bridge.
  ACT        — route to the rule-chosen waypoint; once the carried symbol matches
               the goal form, deliver (`plan_deliver`).

GOAL BLINDNESS is the control it must beat: the `blind` arm's `plan_blind` rule
tunnels straight to the goal, ignoring the salient mismatch — it delivers the
UN-transformed symbol and LOSES. The `detour` arm proves INVESTIGATION (not mere
detour) is the lever: it detours to the lowest-order station without recognising
WHICH transform is needed, uses the wrong one, and (usually) LOSES too.

Every rule is guarded on `game.plan_on==1` (default-OFF; byte-identical to any
graph that does not set the flag) and on the arm (`game.arm`) so exactly one
policy's rules fire. Integer-native throughout (the shapes are the integer
lattice; the transform key is a categorical token). No Rust, no new Term — the
recognition reuses the EXISTING shape_decode_loop; these are ordinary match+where
+effect rules over the standard evaluator.
"""
from __future__ import annotations

import json
from pathlib import Path


# --- Term-tree builders (same vocabulary as scripts/move_space_planner.py) ----
def V(n):        return {"type": "Var", "name": n}
def A(n, k):     return {"type": "Attr", "node": V(n), "key": k}
def L(v):        return {"type": "Lit", "value": v}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}
def And(*x):     return {"type": "And", "items": list(x)}
def Not(a):      return {"type": "Not", "arg": a}


def _enabled(arm):
    """Common guard: the planner is switched ON for this game AND this arm."""
    return And(Eq(A("g", "plan_on"), L(1.0)), Eq(A("g", "arm"), L(arm)))


# --------------------------------------------------------------------------
# THE RULES — the salience -> investigate -> act loop, graph-native.
# --------------------------------------------------------------------------
def _rules():
    rules = []

    # SALIENCE (surprise -> ORIENT). The symbol<->goal mismatch is salient: flag
    # it and record the affect. Pure orientation (the 208000 vocabulary); it does
    # not itself pick a waypoint — it surfaces the surprise the investigation
    # answers. Fires for the curious arm only (the arm that HEEDS salience).
    rules.append({
        "name": "plan_orient",
        "comment": "SALIENCE: symbol!=goal -> ORIENT (surprise). Reuses 208000 surprise->ORIENT.",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled("curious"), Eq(A("g", "symbol_matches_goal"), L(0.0))),
        "effects": [["set_attr", "g", "salient_mismatch", 1.0],
                    ["set_attr", "g", "affect", "surprise_orient"]],
    })

    # INVESTIGATE + ACT (curious): the carried symbol does NOT yet match the goal
    # form -> seek the station whose transform MATCHES the recognised required key
    # (req_key, from the graph-native 217000 sd-loop). This is the INVESTIGATION
    # decision — route to the station that performs the recognised transform, not
    # just any station. The waypoint is that station's cell.
    rules.append({
        "name": "plan_seek_station",
        "comment": "INVESTIGATE: route to the station matching the recognised required transform.",
        "match": [["g", "has_station", "s"]],
        "where": And(_enabled("curious"),
                     Eq(A("g", "symbol_matches_goal"), L(0.0)),
                     Eq(A("s", "key"), A("g", "req_key")),
                     Eq(A("s", "used"), L(0.0))),
        "effects": [["set_attr", "g", "waypoint", "station"],
                    ["set_attr", "g", "wp_r", {"__term__": A("s", "r")}],
                    ["set_attr", "g", "wp_c", {"__term__": A("s", "c")}]],
    })

    # ACT (curious): the carried symbol matches the goal form -> deliver it (route
    # to the goal). Covers both the identity case (already matches -> straight to
    # goal, NO needless detour) and the post-transform case (station applied ->
    # now matches -> deliver).
    rules.append({
        "name": "plan_deliver",
        "comment": "ACT: carried matches goal -> route to the goal cell and deliver.",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled("curious"), Eq(A("g", "symbol_matches_goal"), L(1.0))),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", {"__term__": A("g", "goal_r")}],
                    ["set_attr", "g", "wp_c", {"__term__": A("g", "goal_c")}]],
    })

    # GOAL BLINDNESS (the control): tunnel straight to the goal, ALWAYS. Ignores
    # the salient mismatch, never investigates, never transforms -> delivers the
    # un-transformed symbol and loses. This IS "goal blindness is how you lose."
    rules.append({
        "name": "plan_blind",
        "comment": "CONTROL: goal-blind -> route straight to the goal, ignoring the mismatch.",
        "match": [["g", "has_ping", "p"]],
        "where": _enabled("blind"),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", {"__term__": A("g", "goal_r")}],
                    ["set_attr", "g", "wp_c", {"__term__": A("g", "goal_c")}]],
    })

    # BLIND DETOUR (the second control): detour to a station, but WITHOUT
    # investigating which transform is needed — take the lowest-order station.
    # Proves INVESTIGATION, not mere detour, is the lever (wrong station -> lose).
    rules.append({
        "name": "plan_detour_seek",
        "comment": "CONTROL: detour to the lowest-order station without investigating which transform.",
        "match": [["g", "has_station", "s"]],
        "where": And(_enabled("detour"),
                     Eq(A("g", "any_station_used"), L(0.0)),
                     Eq(A("s", "order"), L(0.0))),
        "effects": [["set_attr", "g", "waypoint", "station"],
                    ["set_attr", "g", "wp_r", {"__term__": A("s", "r")}],
                    ["set_attr", "g", "wp_c", {"__term__": A("s", "c")}]],
    })
    rules.append({
        "name": "plan_detour_deliver",
        "comment": "CONTROL: after using a station, deliver (whatever the symbol now is).",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled("detour"), Eq(A("g", "any_station_used"), L(1.0))),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", {"__term__": A("g", "goal_r")}],
                    ["set_attr", "g", "wp_c", {"__term__": A("g", "goal_c")}]],
    })

    return rules


RULES = _rules()


def manifest():
    return {
        "id": "ls20_planning",
        "version": "1.0.0",
        "depends_on": ["shape_decode_loop"],
        "area": "retina",
        "description": (
            "ls20 PLANNING/EXECUTION (block 218000): the salience->investigate->act "
            "loop as graph rules. SALIENCE = the symbol<->goal mismatch (surprise->ORIENT); "
            "INVESTIGATE = recognise the required transform (217000 sd-loop) and seek the "
            "matching station; ACT = deliver when the carried symbol matches. Goal-blind "
            "(plan_blind) and blind-detour (plan_detour_*) are the controls it must beat. "
            "Guarded on game.plan_on==1 (default-OFF, byte-identical otherwise) and on "
            "game.arm. Integer-native; no Rust; reuses the existing shape_decode_loop."),
        "microtheory": {
            "name": "ls20_planning",
            "description": "Salience surfaces the mismatch; investigation recognises the "
                           "required transform and the means to perform it; the act follows. "
                           "The goal is an attractor, never a blinder — every where-to-go "
                           "decision is a rule.",
        },
        "nodes": [], "edges": [], "productions": [],
        "rules": RULES,
    }


def write_seed(path=None):
    p = Path(path) if path else Path(__file__).resolve().parent.parent / "seeds" / "ls20_planning.json"
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())
