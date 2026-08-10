"""Generator for seeds/nd_action_correlation.json — the COMPENSATED self/world/board discriminator.

A one-off authoring tool (emits graph DATA). The agent compensates for each object's OWN dynamics rather
than relying on the experiment: a region is CONTROLLABLE only if MY ACTION predicts its motion BETTER THAN
ITS OWN INERTIA does (action-conditioned surprise < passive/constant-velocity surprise, by a margin).
- The avatar: inertia fails when I change action; my action_delta predicts it -> action << passive -> SELF.
- A constant-velocity drifter: its own inertia predicts it perfectly; my action adds nothing -> action ~ passive -> WORLD.
- A jitterer (changes its OWN velocity): predicted by NEITHER my action nor simple inertia -> action not < passive -> WORLD.
- Static: never moves -> BOARD.
This compensates for confounds (a world object changing its own velocity) WITHOUT randomising the actions or
tuning thresholds from outside — the discrimination is the agent's, in its own surprise terms.

Run: python3 scripts/gen_action_corr_seed.py
"""
from __future__ import annotations

import json
import os

ACTIONS = ["Up", "Down", "Left", "Right"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMA = 0.3
MARGIN = 0.3


def V(n): return {"type": "Var", "name": n}
def Lit(v): return {"type": "Lit", "value": v}
def Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def P0(k): return {"type": "Plus", "items": [Attr(V("r"), k), Lit(0.0)]}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Plus(items): return {"type": "Plus", "items": items}
def Times(items): return {"type": "Times", "items": items}
def Max(items): return {"type": "Max", "items": items}
def Neg(a): return {"type": "Neg", "arg": a}
def Abs(x): return Max([x, Neg(x)])
def IfThenElse(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}


def ema(cur, obs_term):
    return Plus([P0(cur), Times([Lit(EMA), Minus(obs_term, P0(cur))])])


def learn_rule(a):
    return {
        "name": f"learn_resp_{a.lower()}",
        "comment": f"Per-region response to action {a}: when I just took {a}, EMA this region's resp_{a}_* "
                   f"toward its observed motion. Per-region so each object learns its OWN response.",
        "match": [["game", "has_region", "r"]],
        "where": Eq(Attr(V("game"), "last_action"), Lit(a)),
        "effects": [
            ["set_attr", "r", "clocked", 1.0],
            ["set_attr", "r", f"next_resp_{a}_dr", {"__term__": ema(f"resp_{a}_dr", P0("drow"))}],
            ["set_attr", "r", f"next_resp_{a}_dc", {"__term__": ema(f"resp_{a}_dc", P0("dcol"))}],
        ],
    }


def _resp_for_last(comp):
    """The response to the action JUST taken (dispatch on game.last_action) — the action-conditioned forecast."""
    la = Attr(V("game"), "last_action")
    return IfThenElse(Eq(la, Lit("Up")), P0(f"resp_Up_{comp}"),
           IfThenElse(Eq(la, Lit("Down")), P0(f"resp_Down_{comp}"),
           IfThenElse(Eq(la, Lit("Left")), P0(f"resp_Left_{comp}"),
                      P0(f"resp_Right_{comp}"))))


def track_rule():
    # passive (inertia) surprise = |velocity now - velocity last frame|; action surprise = |velocity now -
    # my action's learned response|. Both EMA'd; drow_prev/dcol_prev folded at the clock edge.
    passive_inst = Plus([Abs(Minus(P0("drow"), P0("drow_prev"))), Abs(Minus(P0("dcol"), P0("dcol_prev")))])
    action_inst = Plus([Abs(Minus(P0("drow"), _resp_for_last("dr"))), Abs(Minus(P0("dcol"), _resp_for_last("dc")))])
    return {
        "name": "track_surprises",
        "comment": "Compensate for each object's own dynamics: passive_surp = inertia (constant-velocity) "
                   "prediction error; act_surp = my-action prediction error. Both folded EMAs. The agent "
                   "compares them to decide control — my action must beat inertia.",
        "match": [["game", "has_region", "r"]],
        "where": Lit(True),
        "effects": [
            ["set_attr", "r", "clocked", 1.0],
            ["set_attr", "r", "next_drow_prev", {"__term__": P0("drow")}],
            ["set_attr", "r", "next_dcol_prev", {"__term__": P0("dcol")}],
            ["set_attr", "r", "next_passive_surp", {"__term__": ema("passive_surp", passive_inst)}],
            ["set_attr", "r", "next_act_surp", {"__term__": ema("act_surp", action_inst)}],
            ["set_attr", "r", "ever_speed", {"__term__": Max([P0("ever_speed"),
                Plus([Times([P0("drow"), P0("drow")]), Times([P0("dcol"), P0("dcol")])])])}],
        ],
    }


def classify_rule():
    # CONTROLLABLE only if my action predicts BETTER than inertia, by a margin (compensated). Else, if it has
    # ever moved, AUTONOMOUS (its own dynamics / unpredictable by me). Else INVARIANT.
    beats_inertia = Lt(P0("act_surp"), Minus(P0("passive_surp"), Lit(MARGIN)))
    kind = IfThenElse(Lt(P0("ever_speed"), Lit(0.5)), Lit("invariant"),
                      IfThenElse(beats_inertia, Lit("controllable"), Lit("autonomous")))
    # Counterfactual gate: controllability is only TESTED when my action changes. On a constant-action frame
    # (last_action == the action I last classified this region under) HOLD the existing axis_kind, so a long
    # commitment whose constant-velocity body inertia predicts perfectly cannot dissolve an established self.
    held = IfThenElse(Eq(Attr(V("game"), "last_action"), Attr(V("r"), "classified_under")),
                      Attr(V("r"), "axis_kind"), kind)
    return {
        "name": "classify_axis_compensated",
        "comment": "axis_kind: invariant if never moved; controllable if my action's surprise beats inertia's "
                   "by a margin on an action-CHANGE frame; else autonomous. GATED: re-classified only on "
                   "action-change frames (informative counterfactual); HELD on constant-action frames so a "
                   "long commitment cannot dissolve an already-established self (the agent's own fix).",
        "match": [["game", "has_region", "r"]],
        "where": Lit(True),
        "effects": [
            ["set_attr", "r", "axis_kind", {"__term__": held}],
            ["set_attr", "r", "classified_under", {"__term__": Attr(V("game"), "last_action")}],
        ],
    }


def main():
    seed = {
        "id": "nd_action_correlation",
        "self_modification_patchable_rules": ["classify_axis_compensated"],
        "version": "1.0.0",
        "area": "sensorimotor_prediction",
        "latency_class": "hard_realtime",
        "depends_on": ["nd_representation"],
        "description": "The COMPENSATED self/world/board discriminator: a region is controllable only if my "
                       "action predicts its motion better than its own inertia (action-conditioned surprise < "
                       "passive surprise, by a margin). The agent compensates for each object's own dynamics; "
                       "robust to autonomous objects that change their own velocity, with no randomising or "
                       "threshold-tuning from outside. Generated by scripts/gen_action_corr_seed.py.",
        "microtheory": {"name": "nd_action_correlation",
                        "description": "self = my action beats inertia at predicting it; world = inertia/own-dynamics predicts it (or nothing does); board = still."},
        "nodes": [], "edges": [], "productions": [],
        "rules": [learn_rule(a) for a in ACTIONS] + [track_rule(), classify_rule()],
    }
    out = os.path.join(ROOT, "seeds", "nd_action_correlation.json")
    with open(out, "w") as f:
        json.dump(seed, f, indent=1)
    json.load(open(out))
    print(f"wrote + validated {os.path.relpath(out, ROOT)} ({len(seed['rules'])} rules)")


if __name__ == "__main__":
    main()
