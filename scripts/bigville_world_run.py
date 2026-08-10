#!/usr/bin/env python3
"""bigville R11 (block 259000) -- the SCOPE-GATING cost harness (HEADLINE).

Measures per-tick COST (wall-clock µs/tick AND the engine's `rule_costs`
cost-units for `bw_run_in_scope`) as the OUT-OF-SCOPE world grows for a FIXED
in-scope population, under two arms:

  * ON  (scope-gating) -- out-of-scope agents are bare PERSISTED nodes with NO
    activity wiring, so the matcher never scans them (DORMANT, ~0 compute). Cost
    should be FLAT in the total world.
  * OFF (ablated)      -- the whole world is wired active, so every agent RUNS.
    Cost should grow ~linearly with the TOTAL world -- the cost we must NOT pay.

Writes results/bigville_world/summary.json. This is the rung's headline
measurement, NOT one of the ~43-min oracles.

No agent decision here -- the harness only builds populations, ticks, and times.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.bigville_world_world import BigvilleWorldWorld          # noqa: E402


def measure(n_in, n_out, *, gated, ticks=20):
    """Build n_in in-scope + n_out out-of-scope agents and time `ticks` ticks.

    gated=True  -> out-of-scope agents are unwired (DORMANT).
    gated=False -> ablation: EVERY agent is wired (the whole world runs).
    """
    w = BigvilleWorldWorld()
    for i in range(n_in):
        w.materialize_agent("in%d" % i, in_scope=True)
    for i in range(n_out):
        # ablation removes the gate: an "out of scope" agent is wired anyway.
        w.materialize_agent("out%d" % i, in_scope=(not gated) or False)
        if not gated:
            # scope-gating OFF: wire the whole world (materialize already wired it
            # because in_scope=True); nothing more to do.
            pass
    # warm one tick, then reset the cost counter and time a clean window.
    w.tick()
    w.reset_costs()
    us = w.timed_tick(reps=ticks)
    cost = w.run_cost_of_rule("bw_run_in_scope")
    return dict(n_in=n_in, n_out=n_out, total=n_in + n_out,
                us_per_tick=round(us, 2), rule_cost_units=cost)


def main():
    n_in = 10
    n_outs = [0, 90, 490, 990, 2990]
    on = [measure(n_in, no, gated=True) for no in n_outs]
    off = [measure(n_in, no, gated=False) for no in n_outs]

    def cost_growth(rows):
        base = rows[0]["us_per_tick"]
        return round(rows[-1]["us_per_tick"] / base, 2) if base else None

    on_ratio = cost_growth(on)
    off_ratio = cost_growth(off)
    on_vs_off_at_max = round(off[-1]["us_per_tick"] / on[-1]["us_per_tick"], 1)

    summary = dict(
        block=259000,
        headline="scope-gating: per-tick cost FLAT in the out-of-scope world (ON) "
                 "vs ~linear in the TOTAL world (OFF, ablated)",
        n_in=n_in,
        scope_gating_on=on,
        scope_gating_off=off,
        on_cost_growth_factor=on_ratio,     # ~1.0 (flat) is the claim
        off_cost_growth_factor=off_ratio,   # grows with the total world
        off_over_on_at_max_total=on_vs_off_at_max,
        pass_flat_on=(on_ratio is not None and on_ratio < 1.5),
        pass_off_grows=(off_ratio is not None and off_ratio > 3.0),
        pass_on_cheaper_at_max=(off[-1]["us_per_tick"] > on[-1]["us_per_tick"]),
    )
    out_dir = os.path.join(_ROOT, "results", "bigville_world")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
