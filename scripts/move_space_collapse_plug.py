"""MOVE-SPACE as a DomainPlug into the agent's EXISTING collapse engine — NOT a new layer.

Creator: "why is there a new layer - this is manifold collapse and residual." Correct. The predict ->
surprise -> learn loop I had bolted on is exactly scripts/collapse_engine.run_collapse, which is DOMAIN-
GENERAL (DomainPlug): per revealed prefix it COLLAPSES the candidate manifold, and where the model cannot
explain the true next symbol it records a GAP (the residual) and calls on_gap (the learning step = grow Γ).
Sentences, letters, llvm, voice already plug in. The move-space is just another plug:

  symbols   : cells "r,c" and actions "U/D/L/R"; a transition is the length-3 sequence (s, a, s').
  next_dist : the agent's transition model. For an UNLEARNED (s,a) it returns its GENERALISATION prior
              ("the action moves me one cell", ignoring walls) — which is WRONG at a wall. A wall is then a
              RESIDUAL the manifold cannot collapse: true_next (= stay) has no mass -> run_collapse records a
              GAP and calls on_gap.
  on_gap    : LEARN the real transition (count it into the model = grow Γ). The mistake becomes knowledge.

So "it can't get stuck unless it made a mistake, then it learns" = the collapse engine's gap-localisation +
on_gap, pointed at the transition manifold. No score, no new mechanism. Run it twice: gaps before learning =
the wall transitions the prior mispredicts (the only places it could be surprised/stuck); gaps after = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/move_space_collapse_plug.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from collapse_engine import DomainPlug, run_collapse        # the agent's domain-general collapse loop

DIRS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
GRID, WALLS = 5, {(1, 1), (1, 3), (2, 2), (3, 1)}            # the world's hidden obstacles
def cs(rc): return f"{rc[0]},{rc[1]}"
def ingrid(rc): return 0 <= rc[0] < GRID and 0 <= rc[1] < GRID
def naive(s, a):                                            # the GENERALISATION prior: a step moves one cell
    r, c = map(int, s.split(",")); dr, dc = DIRS[a]; nb = (r + dr, c + dc)
    return cs(nb) if ingrid(nb) else s
def truth(s, a):                                            # the WORLD: a wall (or edge) stops the move
    r, c = map(int, s.split(",")); dr, dc = DIRS[a]; nb = (r + dr, c + dc)
    return cs(nb) if (ingrid(nb) and nb not in WALLS) else s


def make_plug(model):
    open_cells = [(r, c) for r in range(GRID) for c in range(GRID) if (r, c) not in WALLS]
    seqs = []
    for rc in open_cells:
        for a in DIRS:
            r, c = rc; dr, dc = DIRS[a]
            if ingrid((r + dr, c + dc)):                    # a move is attempted into the grid
                s = cs(rc); seqs.append((s, a, truth(s, a)))

    def next_dist(ctx):
        # predict the NEXT config only after a (config, action) context; else no prediction.
        if len(ctx) < 2 or ctx[-1] not in DIRS:
            return {}
        s, a = ctx[-2], ctx[-1]
        if (s, a) in model:                                 # LEARNED transition (counts)
            tot = sum(model[(s, a)].values())
            return {o: n / tot for o, n in model[(s, a)].items()}
        return {naive(s, a): 1.0}                           # GENERALISATION prior (wrong at walls)

    def on_gap(ctx, missing):                               # LEARN: count the real transition (grow Γ)
        s, a = ctx[-2], ctx[-1]
        model.setdefault((s, a), {}).setdefault(missing, 0)
        model[(s, a)][missing] += 1

    return DomainPlug(name="move_space", pool=seqs, train=seqs, targets=seqs,
                      seq_logprob=lambda seq: 0.0, next_dist=next_dist, on_gap=on_gap)


def main():
    print("=" * 92)
    print("MOVE-SPACE plugged into the EXISTING collapse engine (run_collapse) — no new layer")
    print("=" * 92)
    model = {}                                              # the agent's transition model — starts empty
    plug = make_plug(model)
    seq_lp = {s: 0.0 for s in plug.pool}

    r1 = run_collapse(plug, seq_lp)
    gaps1 = len(r1.gaps)                                    # residuals the generalisation can't collapse...
    wall_trans = sum(1 for (s, a, o) in plug.pool if o == s)  # ...= the wall transitions (stay-in-place)
    learned = len(model)
    print(f"\n  PASS 1: collapse found {gaps1} GAPS — transitions the generalisation mispredicts (a wall =")
    print(f"    a residual it cannot collapse). on_gap LEARNED each one. model now holds {learned} transitions.")
    print(f"    (independently, the world has {wall_trans} wall/stay transitions — the only surprisable spots.)")

    r2 = run_collapse(plug, seq_lp)                         # same engine, now with the learned model
    gaps2 = len(r2.gaps)
    print(f"  PASS 2: collapse found {gaps2} gaps — the model explains every transition, so it CANNOT be")
    print("    surprised/stuck. Knowledge is complete; the score was never involved.")

    print("\n" + "=" * 92)
    ok = gaps1 == wall_trans and gaps1 > 0 and gaps2 == 0
    print(f"  {'PASS' if ok else 'FAIL'} — the move-space is a DomainPlug into the agent's collapse engine:")
    print("  PREDICT = manifold collapse, SURPRISE/STUCK = the residual gap it cannot collapse, LEARN = on_gap")
    print("  growing Γ. 'Can't get stuck unless a mistake -> learn' is this loop, not a new layer; score-free.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
