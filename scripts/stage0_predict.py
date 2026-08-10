"""Stage 0 of the jabberwock's curriculum — verify it can PREDICT a passive world.

Run the passive moving-dot world; the agent perceives it, predicts each Region's next centroid (its own
region_predict_next, committed at the clock edge), and measures its surprise (region_surprise). The agent's
own success criterion: per-Region one-step error -> floor on the moving dot. No control, no goals, no death.

Order per frame: advance the world -> master_tick (the clock edge folds LAST frame's prediction into the
standing prediction predicted_cy) -> perceive_frame (the eye ingests observation(t); its internal tick then
computes surprise = |observed(t) - predicted-at-(t-1)| against the just-folded prediction, and predicts the
next). The fold MUST precede perceive: perceive_frame itself ticks, so predicting before the fold would make
the fold capture THIS frame's prediction and surprise would degenerate to speed (|drow|), not prediction
error. So surprise(t) = |observed(t) - predicted-at-(t-1)|.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/stage0_predict.py [steps]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from passive_world import PassiveDotEnv, DOT
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def _dot_region(agent):
    """The moving dot's Region (the non-ground region whose value is the dot's). Pure query."""
    best = None
    for n in agent.s.nodes("Region"):
        a = agent.s.node(n)["attrs"]
        if a.get("is_ground") == 1.0:
            continue
        if int(a.get("rvalue") or 0) == DOT:
            return n
        best = n
    return best


def main() -> int:
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    world = ArcWorld(PassiveDotEnv())
    sub, ctx = world.reset()
    agent.perceive_frame(sub)
    print("STAGE 0 — predict a passive world (a moving dot). success = one-step surprise -> floor.\n")

    surprises = []
    for i in range(steps):
        sub, ctx = world.apply(("Select",))   # the world advances on its own; the agent does not act
        agent.master_tick()                    # clock edge FIRST: fold LAST frame's prediction into predicted_cy
        agent.perceive_frame(sub)              # eye ingests obs(t); its tick surprises vs that prediction, predicts next
        r = _dot_region(agent)
        a = agent.s.node(r)["attrs"] if r else {}
        s = a.get("surprise")
        cy, cx = a.get("cy"), a.get("cx")
        pcy, pcx = a.get("predicted_cy"), a.get("predicted_cx")
        if i >= 2 and s is not None:           # skip the opening frames (drow not yet established / no prior prediction)
            surprises.append(s)
        print(f"  {i+1:3} obs=({cy},{cx}) predicted=({pcy},{pcx}) surprise={s}", flush=True)

    if surprises:
        avg = sum(surprises) / len(surprises)
        floor = min(surprises)
        n_low = sum(1 for s in surprises if s <= 0.5)
        print(f"\n  surprise after warmup: avg={avg:.3f} floor={floor:.3f}  "
              f"({n_low}/{len(surprises)} frames at/near zero)")
        print(f"  => the predictor {'WORKS — surprise at floor between bounces' if floor <= 0.5 else 'is NOT converging'}; "
              f"spikes are the bounces (the one discontinuity its constant-velocity prior is honestly surprised by).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
