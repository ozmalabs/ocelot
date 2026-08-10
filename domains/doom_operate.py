"""doom_operate — MECHANICAL adapter for the ACT half of door operation (block 210000).

The operate DECISION lives in seeds/doom_operate.json: recognising an operable
feature SETS A MOVEMENT GOAL (MovementGoal moves_toward the region); rules pursue it
and fire USE on arrival. This module ONLY: (a) creates the opt-in OperateParams gate
+ a persistent target PerceivedRegion; (b) writes SENSOR values onto that region
each tic (screen col, near, fwd_progress) -- pure world/proprioceptive reads;
(c) clears the movement goal's motor each tic, runs the rules, and reads the motor
action the graph chose, mapping it to a VizDoom button vector. Nothing here decides
what to do -- it presses the button the graph names for the goal it set.

It does NOT touch the 211000-owned geometry feature: the region's geom_level is
fixed 0 (texture channel only), so this rung and the geometry rung never collide.
"""
from __future__ import annotations
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "doom_operate.json")

# VizDoom button order used by the run harness: [MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, USE].
MOTOR_TO_BUTTONS = {
    "forward":    [1, 0, 0, 0],
    "turn_left":  [0, 1, 0, 0],
    "turn_right": [0, 0, 1, 0],
    "use":        [0, 0, 0, 1],
    "none":       [0, 0, 0, 0],
    "":           [0, 0, 0, 0],
}


def load_operate_seed(wa):
    """Mechanical: load the doom_operate rule manifest into this substrate."""
    wa.inner.load_seed_manifest(json.load(open(SEED_PATH)), None)


def install(wa, game, *, center=160, face_tol=40, block_thresh=4):
    """Opt-in: create the OperateParams gate (rules are inert absent an enabled one).
    Integer params. Mechanical construction of the opt-in state."""
    S, I = wa.s, wa.inner
    p = S.add_node("OperateParams", {
        "enabled": 1.0, "center": int(center), "face_tol": int(face_tol),
        "block_thresh": int(block_thresh)})
    I.add_edge_unchecked(game, "has_operate_params", p)
    return p


def make_target_region(wa, game):
    """Create the ONE persistent PerceivedRegion the movement goal binds to. Its sensor
    attrs are UPDATED each tic (state lives in the graph, adapter only writes sensors).
    fwd_progress starts high (== 'moving', so approach begins with forward)."""
    S, I = wa.s, wa.inner
    r = S.add_node("PerceivedRegion", {
        "geom_level": 0, "tex_level": 0, "col": 160, "near": 0.0, "fwd_progress": 99.0})
    I.add_edge_unchecked(game, "has_perceived_region", r)
    return r


def update_sensors(wa, region, *, col, tex_level, near, fwd_progress):
    """Write this tic's SENSOR reads onto the persistent region (mechanical, integer)."""
    I = wa.inner
    I.set_attr(region, "col", int(col))
    I.set_attr(region, "tex_level", int(tex_level))
    I.set_attr(region, "geom_level", 0)          # 211000 owns geometry; texture-only here
    I.set_attr(region, "near", 1.0 if near else 0.0)
    I.set_attr(region, "fwd_progress", int(fwd_progress))


def _movement_goals(wa, game):
    return list(wa.inner.neighbours(game, "has_movement_goal"))


def step(wa, game):
    """Clear each movement goal's motor (so a stale action never persists -> no spam), run
    the graph to fixpoint (pattern recognition + operate pursuit), then read the motor
    action the ACTIVE goal chose this tic. Mechanical."""
    S, I = wa.s, wa.inner
    for g in _movement_goals(wa, game):
        I.set_attr(g, "motor_action", "")
    I.run_rules(50000)
    action = "none"
    for g in _movement_goals(wa, game):
        a = S.node(g)["attrs"].get("motor_action") or ""
        if a and a != "none":
            action = a
    return action


def motor_buttons(action):
    return list(MOTOR_TO_BUTTONS.get(action, MOTOR_TO_BUTTONS["none"]))


def read_goal(wa, game):
    """Mechanical read of the movement goal state (for logging / tests)."""
    S, I = wa.s, wa.inner
    for g in _movement_goals(wa, game):
        a = S.node(g)["attrs"]
        return {"kind": a.get("kind"), "status": a.get("status"),
                "used": a.get("used"), "motor_action": a.get("motor_action")}
    return None
