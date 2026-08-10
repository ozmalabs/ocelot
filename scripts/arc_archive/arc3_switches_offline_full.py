"""arc3_switches_offline_full — run the IDENTICAL fully-featured fixed agent
(ARC3_THIN shim + ARC3_FULL seed boot + the live driver's play loop) on the
OFFLINE `switches` env, with NO live API / no key.

This is NOT a new reasoner and NOT a new loop. It reuses, verbatim:

  · the SAME boot      — arc3_live_experiment.run_curious_live with ARC3_THIN=1
                          + ARC3_FULL=1 set, so install_full_seed_set + the
                          arc3_thin_handle install run exactly as the live path.
  · the SAME loop      — run_curious_live's per-action choose/observe/learn loop,
                          curiosity menu, order-N model, consolidation cadence,
                          machinery introspection (EffectObjective / goal_cell /
                          win-rule readouts).
  · the SAME handle    — domains.arc3_thin.arc3_thin_handle (the action-by-target
                          -type fix lives here).

The ONLY thing swapped is the TRANSPORT: instead of Arc3LiveEnv(game) (HTTP), we
pass an OFFLINE SwitchesEnv wrapped so it exposes the two attributes the live
driver reads — `available_actions` (all 5 simple + ACTION6, always offered) and
`close_scorecard()` (a no-op offline). That wrapper is pure world-adapter glue:
it holds no agent state and makes no decision; it only translates the offline
env's protocol surface to the shape the driver expects.

Run under: ulimit -v 8388608 + timeout, capturing to a log.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Boot the agent FULLY FEATURED exactly as the live ARC3_FULL=1 path does:
# the run_curious_live driver branches on these env vars to install the full
# seed set + grounded frame + the thin handle. We set them here so the OFFLINE
# run takes the byte-identical boot.
os.environ["ARC3_THIN"] = "1"
os.environ["ARC3_FULL"] = "1"

from arc3_env import (  # noqa: E402
    SwitchesEnv, ACTION1, ACTION2, ACTION3, ACTION4, ACTION5, ACTION6,
)
from arc3_live_experiment import run_curious_live, evaluate_heldout  # noqa: E402


# server's integer action ids the driver's _live_legal_actions compares against
# env.available_actions. Offline we make every protocol action available so the
# agent sees the full menu (5 simple + the coordinate click) — no game rule, just
# "nothing is masked off" (the offline env has no server gating).
_ALL_ACTIONS = [ACTION1, ACTION2, ACTION3, ACTION4, ACTION5, ACTION6]


class OfflineEnvAdapter:
    """Wrap an offline arc3_env env so it presents the transport surface the live
    driver reads (available_actions, close_scorecard) — pure mechanical glue.

    reset() / step() delegate straight to the wrapped env; the wrapper only adds
    the two attributes the live driver expects from the HTTP env. No agent state,
    no decision."""

    def __init__(self, env):
        self._env = env
        self.game_id = env.game_id
        self.available_actions = list(_ALL_ACTIONS)

    def reset(self):
        return self._env.reset()

    def step(self, action, coord=None):
        return self._env.step(action, coord)

    def close_scorecard(self):
        return None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--actions", type=int, default=300,
                    help="action budget for the offline run")
    ap.add_argument("--coord-stride", type=int, default=1,
                    help="ACTION6 lattice stride; 1 = every cell (the offline "
                         "switches grid is tiny so no subsampling is needed)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-order-n", action="store_true")
    ap.add_argument("--per-tick-budget-ms", type=float, default=50.0)
    ap.add_argument("--verbose", action="store_true", default=True)
    args = ap.parse_args(argv)

    print("=== ARC-3 OFFLINE :: jabberwock (FULLY FEATURED, action-by-target-type "
          "fix) on `switches` ===")
    print(f"  boot: ARC3_THIN={os.environ.get('ARC3_THIN')} "
          f"ARC3_FULL={os.environ.get('ARC3_FULL')}  (no live API, no key)")
    print(f"  actions={args.actions}  seed={args.seed}  "
          f"order_n={not args.no_order_n}")

    env = OfflineEnvAdapter(SwitchesEnv())
    res = run_curious_live(
        game="switches", n_actions=args.actions, seed=args.seed,
        coord_stride=args.coord_stride, order_n=not args.no_order_n,
        verbose=args.verbose, per_tick_budget_ms=args.per_tick_budget_ms,
        env=env,
    )

    eng = res["engaged"]
    print("\n================ RESULT ================")
    print(f"  WIN at action            : {res['won_at']}")
    print(f"  best score reached       : {res['best_score']}")
    print(f"  actions to first progress: {res['actions_to_first_progress']}")
    print(f"  scored steps (idx)       : {res['scored_steps']}")
    print(f"  transitions observed     : {len(res['transitions'])}")
    print(f"  distinct ACTION6 coords  : {res['distinct_coords']}")
    print(f"  actions chosen (by kind) : {res['actions_chosen']}")
    print(f"  gamma productions grown  : {len(res['agent'].gamma_dynamic.productions)}")

    print("\n  -- machinery engaged (read out of the agent itself) --")
    print(f"    goal_cell in concepts    : {eng['goal_cell_in_concepts']} "
          f"(still held? {eng['goal_cell_in_held']})")
    print(f"    goal_cell grounded to    : {eng['goal_cell_grounded_to']} "
          f"@action {eng['grounded_at_action']}")
    print(f"    planner committed route  : len={eng['committed_plan_len']} "
          f"@action {eng['routed_at_action']}")
    print(f"    instance edge types      : {eng['instance_edge_types']}")

    # held-out forward-model check (the same evaluator the live driver ships).
    ho = evaluate_heldout(res["transitions"], cell_transitions=res["cell_transitions"])
    print("\n  -- held-out forward model --")
    for k, v in ho.items():
        print(f"    {k}: {v}")

    return res


if __name__ == "__main__":
    main(sys.argv[1:])
