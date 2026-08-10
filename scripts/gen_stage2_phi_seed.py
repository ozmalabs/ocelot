"""Generator for seeds/stage2_phi_boundary.json — 'the boundary is destruction', understood in phi.

A one-off authoring tool (emits graph DATA). By Stage 2 the agent already holds, from the compensated
discriminator, WHICH Region is the self (axis_kind=="controllable") and its CONTROLLABLE BASIS
(resp_<A>_dr/dc = the per-action displacement of phi). So it does not need to die to learn the walls:

  * roll_self_<A>: roll the self's bounding box forward by resp_<A> (the action's phi-displacement). If the
    rolled box leaves the board ([0,h) x [0,w), read from the game node), that action has NO modelled
    continuation -> would_die_<A> = 1. This is forward-rollout in phi, the termination prior.
  * choose_safe_action: the agent's action. Keep the current heading if its rollout survives; otherwise turn
    to the first action whose rollout stays on the board. The self never chooses an action it predicts ends it.

No death handler, no learned-by-dying, no threshold tuning. The walls are death because the rollout says so.

Run: python3 scripts/gen_stage2_phi_seed.py
"""
from __future__ import annotations

import json
import os

ACTIONS = ["Up", "Down", "Left", "Right"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def V(n): return {"type": "Var", "name": n}
def Lit(v): return {"type": "Lit", "value": v}
def Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def AR(k): return {"type": "Plus", "items": [Attr(V("r"), k), Lit(0.0)]}        # self attr, +0.0 = None-safe
def AG(k): return Attr(V("game"), k)
def Plus(items): return {"type": "Plus", "items": items}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Max(items): return {"type": "Max", "items": items}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def IfThenElse(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def ind(c): return IfThenElse(c, Lit(1.0), Lit(0.0))     # boolean -> 0/1 indicator


def roll_rule(a):
    dr, dc = AR(f"resp_{a}_dr"), AR(f"resp_{a}_dc")
    minr_n, maxr_n = Plus([AR("minr"), dr]), Plus([AR("maxr"), dr])
    minc_n, maxc_n = Plus([AR("minc"), dc]), Plus([AR("maxc"), dc])
    hi_r, hi_c = Minus(AG("h"), Lit(1.0)), Minus(AG("w"), Lit(1.0))
    would_die = Max([
        ind(Lt(minr_n, Lit(0.0))),      # top edge crossed
        ind(Gt(maxr_n, hi_r)),          # bottom edge crossed
        ind(Lt(minc_n, Lit(0.0))),      # left edge crossed
        ind(Gt(maxc_n, hi_c)),          # right edge crossed
    ])
    return {
        "name": f"roll_self_{a.lower()}",
        "comment": f"Roll the self's bbox forward by its learned phi-displacement for {a} (resp_{a}); "
                   f"would_die_{a}=1 if the rolled box leaves the board ([0,h)x[0,w) from the game node). "
                   f"Forward-rollout in phi -> the termination prior, no dying required.",
        "match": [["game", "has_region", "r"]],
        "where": Eq(Attr(V("r"), "axis_kind"), Lit("controllable")),
        "effects": [["set_attr", "r", f"would_die_{a}", {"__term__": would_die}]],
    }


def choose_rule():
    last = AG("last_action")
    wd_last = IfThenElse(Eq(last, Lit("Up")), AR("would_die_Up"),
              IfThenElse(Eq(last, Lit("Down")), AR("would_die_Down"),
              IfThenElse(Eq(last, Lit("Left")), AR("would_die_Left"),
                         AR("would_die_Right"))))
    chosen = IfThenElse(Lt(wd_last, Lit(0.5)), last,
             IfThenElse(Lt(AR("would_die_Up"), Lit(0.5)), Lit("Up"),
             IfThenElse(Lt(AR("would_die_Down"), Lit(0.5)), Lit("Down"),
             IfThenElse(Lt(AR("would_die_Left"), Lit(0.5)), Lit("Left"),
                        Lit("Right")))))
    return {
        "name": "choose_safe_action",
        "comment": "The agent's action: keep the current heading if its rollout survives the boundary; "
                   "otherwise turn to the first action whose rollout stays on the board. The self never "
                   "picks an action it predicts terminates it. Sets game.safe_action (the decision is the "
                   "rule's; the world adapter only transports it).",
        "match": [["game", "has_region", "r"]],
        "where": Eq(Attr(V("r"), "axis_kind"), Lit("controllable")),
        "effects": [["set_attr", "game", "safe_action", {"__term__": chosen}]],
    }


def main():
    seed = {
        "id": "stage2_phi_boundary",
        "version": "1.0.0",
        "depends_on": ["nd_action_correlation"],
        "description": "Stage 2 ('the boundary is destruction') in phi. The agent holds the self's controllable "
                       "basis (resp_<A>) from the compensated discriminator and rolls the self's bbox forward "
                       "by it; an action whose rollout leaves the board ([0,h)x[0,w) from the game node) has no "
                       "modelled continuation = termination (would_die_<A>=1). It then chooses a surviving "
                       "action. The walls are death understood as a forward-rollout prior, not learned by dying "
                       "— no death handler, no threshold tuning. Generated by scripts/gen_stage2_phi_seed.py.",
        "microtheory": {"name": "stage2_phi_boundary",
                        "description": "boundary = destruction: an action whose phi-rollout leaves the board ends the self; avoid it."},
        "nodes": [], "edges": [], "productions": [],
        "rules": [roll_rule(a) for a in ACTIONS] + [choose_rule()],
    }
    out = os.path.join(ROOT, "seeds", "stage2_phi_boundary.json")
    with open(out, "w") as f:
        json.dump(seed, f, indent=1)
    json.load(open(out))
    print(f"wrote + validated {os.path.relpath(out, ROOT)} ({len(seed['rules'])} rules)")


if __name__ == "__main__":
    main()
