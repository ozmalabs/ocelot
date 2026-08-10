"""arc3_steering_test — the LOAD-BEARING test for the owned-but-unwired fix.

The diagnosis (the agent's own): the order-N lift recovered DISCRIMINATION
(1->3 distinct predicted configs) but WINS FELL (6->3) because nothing steered
toward the named objective. The fix wires the planner's intent into the
preview-UNSAFE path: a graph-resident STEERING Term-tree scores each action by
how far its LEARNED modal EffectConfig (predict_effect_config) moves the agent
toward the EffectObjective it has already minted — distance-reduction to the
named goal, folded live into choose_action alongside curiosity.

This harness measures the OUTCOME layer (wins), not discrimination: on the
offline ARC worlds (switches + navigate), does wiring the steering RAISE the
win rate vs the no-steering baseline? Averaged over seeds (wins are stochastic).
It also confirms steering is OFF cleanly when no objective is named (pre-reward)
so exploration does not regress.

  ulimit -v 8388608
  timeout 600 python scripts/arc3_steering_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from arc3_order_n_offline import run_offline  # noqa: E402


def measure(game: str, ticks: int, seeds: list[int], order_n: bool,
            steering: bool, pre_reward: bool = True) -> dict:
    wins = []
    firsts = []
    for s in seeds:
        res = run_offline(game, ticks, s, order_n, verbose=False,
                          steering=steering, pre_reward=pre_reward)
        wins.append(res["wins"])
        firsts.append(res["ticks_to_first_win"])
    total = sum(wins)
    n_solved = sum(1 for w in wins if w > 0)
    firsts_seen = [f for f in firsts if f is not None]
    return {
        "wins_total": total,
        "wins_mean": total / len(seeds),
        "seeds_solved": n_solved,
        "n_seeds": len(seeds),
        "mean_ticks_to_first_win": (
            sum(firsts_seen) / len(firsts_seen) if firsts_seen else None),
    }


def main(argv):
    ticks = 160
    seeds = list(range(8))
    print("=== ARC-3 STEERING test :: wins with vs without the steering term ===")
    print(f"    (order-N lifted menu; {len(seeds)} seeds; {ticks} ticks each)\n")
    # Four conditions: curiosity-only baseline; #1 steering (reward-derived
    # objective only, #2 ablated); #2 pre-reward objective hypothesis (guessed
    # goal lets steering engage BEFORE reward); and both together.
    for game in ("switches", "navigate"):
        print(f"--- {game} ---")
        conds = (
            ("steering OFF (curiosity only)        ", False, False),
            ("steering ON, pre-reward OFF (#1)     ", True, False),
            ("steering ON, pre-reward ON  (#1+#2)  ", True, True),
        )
        for label, steer, pre in conds:
            m = measure(game, ticks, seeds, order_n=True, steering=steer,
                        pre_reward=pre)
            print(f"  {label:36s}  "
                  f"wins_total={m['wins_total']:3d}  "
                  f"wins/seed={m['wins_mean']:.2f}  "
                  f"seeds_solved={m['seeds_solved']}/{m['n_seeds']}  "
                  f"mean_first_win="
                  f"{m['mean_ticks_to_first_win']}")
        print()


if __name__ == "__main__":
    main(sys.argv[1:])
