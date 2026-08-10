"""arc3_order_n_offline — HONEST OFFLINE VALIDATION of the order-N world-model lift.

The live ARC-3 games require an ARC_API_KEY (read ONLY from os.environ, never a
file) that is not present in this environment. This harness validates the order-N
lift's MECHANICS against the faithful offline re-implementation (arc3_env.py),
which contains a game with the SAME structure that defeats the order-1 model on the
dense live games: ``switches`` has a HIDDEN OBJECTIVE that is a CONFIGURATION over
the effect-set (all three switch-cells ON), and per-coordinate ACTION6 clicks that
each toggle a distinct cell — the dense-game structure in miniature.

It drives the REAL CuriousAgent through the offline env with the SAME loop the live
driver uses, then reports, side by side:
  · order-1 (per-type marginal)  vs  order-N (joint-config) held-out discrimination;
  · the inferred latent objective from the order-N lift;
  · order-N curiosity-biased menu vs unbiased.

This is a mechanics + discrimination proof — NOT a live result. The live re-run
command (identical wiring) is printed at the end for the user to run with their key.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.curious_agent import CuriousAgent, canonical_action_kind  # noqa: E402
from domains.arc3_world import arc3_world_handle  # noqa: E402
from domains.order_n_world_model import (  # noqa: E402
    order2_signature, order_n_objective, order_n_curiosity_weights,
    predict_order2,
)
from arc3_env import ENVS  # noqa: E402
from arc3_live_experiment import (  # noqa: E402
    _changed_celltypes, _changed_cells, _order_n_biased_menu, evaluate_heldout,
)


def run_offline(game: str, n_ticks: int, seed: int, order_n: bool,
                verbose: bool = False, steering: bool = True,
                pre_reward: bool = True, coord_salience: bool = True):
    random.seed(seed)
    env = ENVS[game]()
    agent = CuriousAgent()
    # Steering contrast: set the graph-resident steering_weight policy to 0 to
    # ABLATE the learned-model-toward-objective pull (curiosity only), or leave
    # it at its default to wire it in. Graph data — read live in choose_action.
    if not steering:
        agent._set_named_lit_policy("steering_weight", 0.0)
    # #2 PRE-REWARD objective contrast: set the graph-resident
    # pre_reward_objective_weight policy to 0 to ABLATE the pre-reward objective
    # hypothesis (no guessed goal — steering only engages after a real reward),
    # or leave it at its default to wire it in. Graph data, round-trips.
    if not pre_reward:
        agent._set_named_lit_policy("pre_reward_objective_weight", 0.0)
    # #3 COORDINATE SALIENCE contrast: set the graph-resident
    # coord_salience_weight policy to 0 to ABLATE the pull toward salient
    # coordinates (the event-salience faculty lifted to WHICH coordinate to act
    # at), or leave it at its default to wire it in. Graph data, round-trips.
    if not coord_salience:
        agent._set_named_lit_policy("coord_salience_weight", 0.0)
    handle = arc3_world_handle(env, agent)
    substrate, ctx = handle["reset"]()
    agent.observe(substrate)

    transitions: list = []
    cell_transitions: list = []
    scored_steps: list = []
    curiosity_w: dict = {}
    best_score = ctx["score"]
    wins = 0
    ticks_to_first_win = None

    for i in range(n_ticks):
        actions = handle["legal_actions"](substrate, ctx)
        if not actions:
            break
        if order_n:
            actions = _order_n_biased_menu(actions, curiosity_w, 8, random)
        action = agent.choose_action(substrate, ctx, actions, handle)
        chosen = canonical_action_kind(action)

        touched = handle["interpret_acts_on"](substrate, ctx, action)
        for t in touched:
            agent._register_relation(t, "acts_on")
        agent._record_activity("act", touched)

        q_before = agent.quality_of_position(substrate)
        pre = substrate
        substrate, ctx = handle["apply_action"](substrate, ctx, action)
        changed = _changed_celltypes(pre, substrate)
        transitions.append((chosen, changed))
        cell_transitions.append((chosen, _changed_cells(pre, substrate)))

        agent.observe(substrate)
        q_after = agent.quality_of_position(substrate)
        agent.record_action_outcome(
            chosen, agent.last_world_novelty, max(0.0, q_before - q_after),
            agent.boredom_count(substrate), ctx.get("tick", 0),
            terminal_delta=1.0 if ctx["won"] else 0.0,
            frontier_after=agent.last_freshening_count,
        )

        if ctx["score"] > best_score:
            best_score = ctx["score"]
            scored_steps.append(len(transitions) - 1)

        if order_n and (i + 1) % 4 == 0:
            curiosity_w = order_n_curiosity_weights(cell_transitions)

        if (i + 1) % 8 == 0:
            agent.grow_gamma()
        if (i + 1) % 16 == 0:
            agent.discover_relations()
            agent.discover_theorems()

        if ctx["won"]:
            wins += 1
            if ticks_to_first_win is None:
                ticks_to_first_win = i + 1
                if verbose:
                    print(f"    [{game}] WIN at tick {i+1}")
            substrate, ctx = handle["reset"]()
            agent.observe(substrate)

    return {
        "agent": agent, "transitions": transitions,
        "cell_transitions": cell_transitions, "scored_steps": scored_steps,
        "wins": wins, "ticks_to_first_win": ticks_to_first_win,
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="switches", choices=list(ENVS))
    ap.add_argument("--ticks", type=int, default=160)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    print(f"=== ARC-3 OFFLINE order-N validation :: '{args.game}' ===\n")
    out = {}
    for label, on in (("order-1 baseline", False), ("order-N lifted", True)):
        res = run_offline(args.game, args.ticks, args.seed, on, args.verbose)
        ev = evaluate_heldout(res["transitions"],
                              cell_transitions=res["cell_transitions"])
        obj = order_n_objective(res["cell_transitions"], res["scored_steps"])
        out[label] = {
            "wins": res["wins"],
            "ticks_to_first_win": res["ticks_to_first_win"],
            "heldout": ev,
            "objective": (sorted(obj["objective_config"])
                          if obj["objective_config"] else None),
            "objective_support": obj["support"],
        }
        print(f"--- {label} ---")
        print(f"  wins={res['wins']}  ticks_to_first_win={res['ticks_to_first_win']}")
        print(f"  held-out: {json.dumps(ev)}")
        print(f"  inferred objective: {out[label]['objective']} "
              f"(support {obj['support']})\n")

    # honest read of the discrimination delta.
    b, n = out["order-1 baseline"]["heldout"], out["order-N lifted"]["heldout"]
    print("--- order-1 vs order-N discrimination ---")
    print(f"  order-1 distinct predicted configs : {b.get('order1_distinct_configs')}")
    print(f"  order-N distinct predicted configs : {n.get('order2_distinct_configs')}")
    print(f"  order-1 action-cond jaccard        : {b.get('order1_action_conditioned_jaccard')}")
    print(f"  order-N joint-config jaccard       : {n.get('order2_jointconfig_jaccard')}")

    print("\n--- LIVE re-run command (export key at runtime; never in a file) ---")
    print("  export ARC_API_KEY=...   # from your account; NOT committed")
    print("  ulimit -v 8388608")
    print("  timeout 600 python scripts/arc3_live_experiment.py "
          "--game vc33-5430563c --actions 120 --coord-stride 8 --verbose")
    print("  # baseline contrast: add --no-order-n")


if __name__ == "__main__":
    main(sys.argv[1:])
