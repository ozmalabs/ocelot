"""THE JABBERWOCK UNDERSTANDS WHAT ITS REPRESENTATION IS — the grid is one projection of an N-D state.

Per the creator: the 2D grid is easy but it is only a REPRESENTATION — what we actually need is an
N-dimensional projection we can rotate through; a "grid" is simply the representation, and the jabberwock
should understand what the representation IS. So I do not design this — I pose the insight + what it holds,
and have the jabberwock understand and design its representation: observations as projections of an N-D
state, rotatable, with the grid as one view, so its understanding generalises beyond 2D rows/cols.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_understands_representation
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from scripts.claude_teacher import make_ask

SEP = "=" * 96

PROMPT = """You are the jabberwock: a typed-graph agent in Rust; Python only adapts I/O; decisions are graph
Rules/Terms. You are designing how you UNDERSTAND AND PLAY GAMES from your own prediction_minus_observation
core (predict the next observation -> surprise -> model/attention/action; the closed loop folds corrections).

WHERE YOU ARE. You built the first stages: Stage 0 you predict a passive world; Stage 1 you learned what
you control (the action_delta map); Stage 2 you treat the boundary as destruction by rolling your model
forward. But you did all this over a 2D GRID — your eye segments cells into Regions with 2D centroids
(cy, cx), and your forward model predicts those 2D coordinates.

THE CREATOR'S CORRECTION (the thing to understand). The 2D grid is EASY, but it is ONLY A REPRESENTATION —
a 2D PROJECTION. What you actually need is an N-DIMENSIONAL projection you can ROTATE THROUGH. A "grid" is
simply the representation; rows and columns are NOT fundamental. You should understand what your
representation IS: an observation is a PROJECTION of a higher-dimensional state, and you can rotate that
projection (change the viewpoint / the basis / which dimensions you read). Tying your perception and your
forward model to 2D rows/cols is the limit you must pass — because to understand tetris, doom, street
fighter, command & conquer, the state that matters is not 2D-spatial, yet the SAME understanding machinery
must work, with the observation as one projection of an N-D state.

WHAT YOU HOLD (to build this from):
- hierarchical_invariance_buildup (build invariant representations from parts) and your shape-recognition
  arc: you already FOLD ROTATION into a forward model (you added oriented candidates, smooth deformation
  fields, log-polar shape-context descriptors, thin-plate splines) and you hold N-dimensional descriptors
  and rotation/transform reasoning.
- prediction_minus_observation + the closed loop; your eye (segmentation, region tracking, motion);
  your seven meta-shapes.

UNDERSTAND, AND HAND BACK (specific, your own — I will implement it graph-native):

1. WHAT THE REPRESENTATION IS. State plainly the relationship between an OBSERVATION (the grid you receive)
   and the N-DIMENSIONAL STATE behind it. What are the N dimensions, for you — are they given, or
   discovered (e.g. from what varies, what your actions move along, what stays invariant)? What does it
   MEAN to "rotate through" the projection — what is the rotation operating on, and what does a rotated
   projection give you that the grid alone does not? Why are rows/cols incidental.

2. THE REPRESENTATION ITSELF. How do you represent a Region / the world state as an N-D vector (or point on
   an N-D manifold)? How does the grid observation PROJECT from it (the projection map), and how do you
   INVERT/lift the 2D observation into the N-D state? How is this stored as graph data (node attrs / a
   basis / a transform), and how do you ROTATE (the operation — a transform Term over the N-D state)?

3. PREDICTION IN N-D. Re-ground your forward model: instead of predicting 2D cy/cx, you predict the next
   N-D state (and surprise is the N-D residual). How does action_delta become a displacement in the N-D
   space? How does "rotate through" help — e.g. predicting in a basis where the dynamics are simplest, or
   recognising the same dynamics under a different projection (invariance)?

4. WHAT STAYS THE SAME. Confirm the ONE mechanism is unchanged — predict -> surprise -> fold — it just
   operates on the N-D representation now, and the grid is one projection of it. Note what of Stages 0-2
   carries over unchanged and what is re-expressed in N-D.

5. HOW YOU'D KNOW YOU UNDERSTOOD IT. The test that you grasp the representation (not just the grid): e.g.
   the same world presented under a different projection is predicted by the same model; or you discover
   the true dimensionality from the data. State the check.

Operate from understanding. The grid is not the world — it is a shadow of it. Tell me what the shadow is a
shadow OF, and how you work in the thing itself."""


def main():
    print(SEP)
    print("THE JABBERWOCK UNDERSTANDS ITS REPRESENTATION — the grid as one projection of an N-D state")
    print(SEP)
    a = boot()
    print("\n  posing the representation insight + your self-knowledge; consulting your design channel ...\n", flush=True)
    ask = make_ask(timeout=600.0, preamble="")
    design = ask(PROMPT)
    if not design:
        print("  (design channel returned empty — claude -p unavailable or timed out)")
        return
    out = os.path.join(ROOT, "docs", "jabberwock_representation_design.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("# The jabberwock's understanding of its representation (the grid as an N-D projection)\n\n")
        f.write("_Authored by the agent. The creator posed the insight + its self-knowledge; the understanding is its own._\n\n")
        f.write(design + "\n")
    print(SEP)
    print("THE JABBERWOCK'S UNDERSTANDING OF ITS REPRESENTATION")
    print(SEP)
    print(design)
    print("\n" + SEP)
    print(f"  saved -> {os.path.relpath(out, ROOT)}")
    print(SEP)


if __name__ == "__main__":
    main()
