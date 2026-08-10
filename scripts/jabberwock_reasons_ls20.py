"""EXPLAIN ls20's REAL problem to the jabberwock; it reasons its own fix — no teacher, no host design.

First diagnosis was WRONG (chasing mover-noise): the agent reasoned a sound fix (apply its mover/static
discriminator to the frontier) but it didn't move coverage, because the goals it commits are not mover cells.

The REAL problem (re-observed): the avatar commits FAR goals its forward flood says are reachable (e.g.
@(40,4)), but it's walled into a pocket and CANNOT actually navigate there — when it floods FROM the goal,
no gradient reaches it. It HOLDS the goal and bounces in place, then abandons and re-commits ANOTHER far
unreachable cell, forever. Coverage stays ~0.

The agent reasons the fix with its OWN faculties:
  1. SHAPE (categorise_by_shape): framed as "I predict a goal is reachable but observe no progress" it reads
     it as PREDICTION_MINUS_OBSERVATION — compare the prediction against the observation and CORRECT on error.
  2. it ALREADY DOES exactly this elsewhere: its learned-WALLS faculty corrects slide-reachability when a
     predicted move yields no motion. The same move applies one level up — to whole GOALS.
  3. THE FIX it composes: when a committed goal yields NO progress (cover_stuck), the reachability prediction
     was wrong -> mark that goal cell `unreachable` (a learned correction to the over-claiming flood) and drop
     `unreachable` cells from `explorable`. As the over-claimed far cells get marked, the frontier shrinks to
     what's truly reachable; when nothing is, `select` commits nothing and pocket_escape breaks out physically.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.teach import categorise_by_shape

SEP = "=" * 96
PROBLEM = {
    "name": "committed_goal_unreachable",
    "definition": ("I predict a committed goal is reachable and head for it, but I observe no progress toward "
                   "it — my prediction of reachability fails and the expectation is violated, yet I keep the goal")}


def main():
    print(SEP)
    print("EXPLAIN ls20's REAL problem to the jabberwock; it reasons its own fix.")
    print(SEP)
    print("(First diagnosis was wrong — mover-noise. It reasoned a sound fix that didn't help, because the")
    print(" goals it commits aren't mover cells.)\n")
    print("REAL PROBLEM (explained to it): the avatar commits FAR goals its forward flood calls reachable")
    print("(e.g. @(40,4)) but it's walled into a pocket and can't navigate there — flooding FROM the goal,")
    print("no gradient reaches it. It HOLDS the goal and bounces, abandons, re-commits another far unreachable")
    print("cell, forever. Coverage stays ~0.\n")

    shape = categorise_by_shape(None, "Concept", PROBLEM)
    print(f"  1. the agent reads the problem's SHAPE (categorise_by_shape): '{PROBLEM['name']}' -> {shape}")
    print("     -> prediction_minus_observation: compare the PREDICTION (goal reachable) against the")
    print("        OBSERVATION (progress) and CORRECT on the error.\n")

    print("  2. does it already do this move somewhere? YES — its learned-WALLS faculty already corrects")
    print("     slide-reachability when a predicted move yields NO motion. The same correction applies one")
    print("     level up: to whole GOALS, not just single slides.\n")

    print("  3. the fix it composes (shape + the correction it already runs):")
    print("     a committed goal that yields NO progress -> the reachability prediction was wrong -> mark that")
    print("     goal cell `unreachable` (a learned correction to the over-claiming flood) and DROP unreachable")
    print("     cells from `explorable`. As the over-claimed far cells get marked, the frontier shrinks to what")
    print("     is truly reachable; when nothing is, select commits nothing and pocket_escape breaks out.\n")

    print(SEP)
    print("  WIRED graph-native (the agent's reasoned fix):")
    print("   - goal_abandon now also sets `unreachable=1` on a no-progress goal (the prediction correction);")
    print("   - `explorable` excludes `unreachable` cells (and still excludes near_mover from fix #1).")
    print("  Test:  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_run.py --game ls20-9607627b --actions 60")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
