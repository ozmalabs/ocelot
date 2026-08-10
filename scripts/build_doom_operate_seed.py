"""build_doom_operate_seed — emit seeds/doom_operate.json (block 210000).

The ACT half of door operation. On recognising an operable feature (209000) the
graph SETS A MOVEMENT GOAL -- a first-class MovementGoal node that MOVES_TOWARD the
recognised region -- and then PURSUES it: the motor action (turn / forward / use)
is DECIDED by rules pursuing that goal and stored on the goal, read + executed by a
mechanical adapter. Arrival (in range + faced + fine-recognised) fires USE ONCE.

The operate DECISION is a rule; the adapter only writes sensors, clears the goal's
motor each tic, and presses the button the graph named (CLAUDE.md). self_load_only
+ default-OFF (OperateParams gate) => byte-identical absent the opt-in.
Integer-native. NO Rust: only existing DSL Terms. Does NOT touch the 211000-owned
geometry channel (region geom_level fixed 0, texture channel only).
"""
from __future__ import annotations
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "doom_operate.json")


# ---- Term-tree helpers (existing DSL Terms only) ----
def V(n): return {"type": "Var", "name": n}
def A(v, k): return {"type": "Attr", "node": V(v), "key": k}
def L(x): return {"type": "Lit", "value": x}
def eq(a, b): return {"type": "Eq", "a": a, "b": b}
def gt(a, b): return {"type": "Gt", "a": a, "b": b}
def gte(a, b): return {"type": "Gte", "a": a, "b": b}
def lt(a, b): return {"type": "Lt", "a": a, "b": b}
def minus(a, b): return {"type": "Minus", "a": a, "b": b}
def absv(a): return {"type": "Abs", "arg": a}
def AND(*xs): return {"type": "And", "items": list(xs)}
def NOT(a): return {"type": "Not", "arg": a}
def ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def T(term): return {"__term__": term}

def col_err(): return absv(minus(A("R", "col"), A("p", "center")))   # |R.col - p.center|
def enabled(): return eq(A("p", "enabled"), L(1.0))


def rule(name, order, match, where, effects):
    return {"name": name, "area": "vision", "order": order,
            "latency_class": "deferred", "match": match, "where": where,
            "effects": effects}


M_PARAMS = ["game", "has_operate_params", "p"]
M_REGION = ["game", "has_perceived_region", "R"]
M_GOAL = ["game", "has_movement_goal", "G"]
M_TOWARD = ["G", "moves_toward", "R"]


def build():
    rules = []

    # 1. op_mint_move: a coarse-recognised operable region -> SET A MOVEMENT GOAL that
    #    MOVES_TOWARD it. This is the movement goal the rest of the loop pursues.
    rules.append(rule(
        "op_mint_move", 7,
        [M_PARAMS, M_REGION],
        AND(enabled(),
            eq(A("R", "recognised_family"), L("operable_feature")),
            NOT(eq(A("R", "mg_minted"), L(1.0)))),
        [["add_node", "G", "MovementGoal",
          {"kind": "approach_operate", "status": "seeking", "used": 0.0, "motor_action": "none"}],
         ["add_edge", "game", "has_movement_goal", "G"],
         ["add_edge", "G", "moves_toward", "R"],
         ["set_attr", "R", "mg_minted", T(L(1.0))]]))

    # 2. op_steer: pursuing a seeking goal, the target is off-centre -> turn toward it.
    rules.append(rule(
        "op_steer", 8,
        [M_PARAMS, M_GOAL, M_TOWARD],
        AND(enabled(),
            eq(A("G", "status"), L("seeking")),
            gte(col_err(), A("p", "face_tol"))),
        [["set_attr", "G", "motor_action",
          T(ite(gt(A("R", "col"), A("p", "center")), L("turn_right"), L("turn_left")))]]))

    # 3. op_advance: pursuing a seeking goal, faced + not yet blocked -> move forward.
    rules.append(rule(
        "op_advance", 8,
        [M_PARAMS, M_GOAL, M_TOWARD],
        AND(enabled(),
            eq(A("G", "status"), L("seeking")),
            lt(col_err(), A("p", "face_tol")),
            gte(A("R", "fwd_progress"), A("p", "block_thresh"))),
        [["set_attr", "G", "motor_action", T(L("forward"))]]))

    # 4. op_use: arrival -- faced, blocked (fwd_progress < block == pressed against the door ==
    #    in USE range), and recognised (recognised==1 LATCHED during approach: texture reads high
    #    at mid-distance and resolves the door/switch; pressed flat against the door the surface
    #    is uniform and texture -> 0, so recognition is object-permanent, not re-derived at
    #    contact) -> USE, ONCE. Sets used + marks the goal operated so no rule sets motor again
    #    (the adapter clears it each tic => no spam).
    rules.append(rule(
        "op_use", 9,
        [M_PARAMS, M_GOAL, M_TOWARD],
        AND(enabled(),
            eq(A("G", "status"), L("seeking")),
            lt(col_err(), A("p", "face_tol")),
            lt(A("R", "fwd_progress"), A("p", "block_thresh")),
            eq(A("R", "recognised"), L(1.0)),
            NOT(eq(A("G", "used"), L(1.0)))),
        [["set_attr", "G", "motor_action", T(L("use"))],
         ["set_attr", "G", "used", T(L(1.0))],
         ["set_attr", "G", "status", T(L("operated"))]]))

    seed = {
        "id": "doom_operate",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": [],
        "area": "vision",
        "description": (
            "The ACT half of door operation (block 210000): recognising an operable "
            "feature (209000) SETS A MOVEMENT GOAL (MovementGoal moves_toward the "
            "region); rules pursue it (steer/advance) and fire USE ONCE on arrival "
            "(in range + faced + fine-recognised). The DECISION is the rules; the "
            "adapter writes sensors + presses the button the graph names. OFF by "
            "default (OperateParams gate); does NOT touch the 211000 geometry channel."),
        "microtheory": "perception",
        "nodes": [],
        "edges": [],
        "productions": [
            {"provenance": "seed:operate:params", "src": {"type": "WorldInstance", "var": "game"},
             "edge_type": "has_operate_params", "tgt": {"type": "OperateParams", "var": "p"}},
            {"provenance": "seed:operate:region", "src": {"type": "WorldInstance", "var": "game"},
             "edge_type": "has_perceived_region", "tgt": {"type": "PerceivedRegion", "var": "R"}},
            {"provenance": "seed:operate:mgoal", "src": {"type": "WorldInstance", "var": "game"},
             "edge_type": "has_movement_goal", "tgt": {"type": "MovementGoal", "var": "G"}},
            {"provenance": "seed:operate:toward", "src": {"type": "MovementGoal", "var": "G"},
             "edge_type": "moves_toward", "tgt": {"type": "PerceivedRegion", "var": "R"}},
        ],
        "rules": rules,
    }
    with open(OUT, "w") as f:
        json.dump(seed, f, indent=2)
    print("wrote", OUT, "with", len(rules), "rules")


if __name__ == "__main__":
    build()
