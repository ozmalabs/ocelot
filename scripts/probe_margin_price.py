"""Is the margin term LIVE, and what did it TRADE?

Two quantities, reported as a pair and ranked by nothing.  Tracking error and
margin are incomparable objectives -- `cognitive_pareto` refuses to scalarize
exactly this, and a probe that called one of them "worse" would be doing by
hand what the faculty declines to do.  Whether the trade is worth making is a
decision against a declared objective basis, not something a measurement
settles.  The probe's job is to say what moved and by how much.

`margin_actions` is a MinOver with a 1024.0 fallback, so an episode that never
approaches a region reports a budget so long that urgency (reference/margin)
rounds to nothing and the new term is inert in practice.  A cost term that
cannot change a decision is not a feature, it is a comment.  This reads the
distribution the composer actually saw.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("GAMMA_REGIME_DIAGNOSTICS", "1")
sys.path.insert(0, ".")

import scripts.jabberwock_fixed_wing_jet as J  # noqa: E402

REFERENCE = 50.0
ROWS: list = []
_original = J._settle_graph_request


def _patched(agent, episode, request_seq, *args, **kwargs):
    result = _original(agent, episode, request_seq, *args, **kwargs)
    attrs = agent.s.node(episode)["attrs"]
    ROWS.append((
        int(request_seq),
        float(attrs.get("margin_actions", -1.0)),
        float(attrs.get("f16_viability_rung", -1.0)),
    ))
    return result


J._settle_graph_request = _patched

from scripts.jabberwock_jsbsim_f16_paper_replication import (  # noqa: E402
    run_experiment,
)

scenario = sys.argv[1] if len(sys.argv) > 1 else "nominal"
run_experiment(scenario_names=(scenario,), episodes_per_scenario=1,
               base_seed=241102975, include_trace=False)

margins = [row[1] for row in ROWS if row[1] >= 0.0]
print(f"\n### {scenario}: {len(ROWS)} actions, {len(margins)} with a margin")
if not margins:
    print("  margin_actions NEVER published -- the term is dead")
    raise SystemExit(0)
# There is no margin of zero -- if the margin is zero it is too late, and
# those actions belong to the escape path, not to the price of time.
too_late = sum(1 for m in margins if m <= 0.0)
print(f"  too late (margin 0)  : {too_late}/{len(margins)} "
      f"({100.0 * too_late / len(margins):.1f}%) -- escape, not priced")
capped = sum(1 for m in margins if m >= 1024.0)
print(f"  at the 1024 fallback : {capped}/{len(margins)} "
      f"({100.0 * capped / len(margins):.1f}%)")
live = [m for m in margins if 0.0 < m < 1024.0]
if live:
    live.sort()
    print(f"  finite margin        : min {live[0]:.0f}  "
          f"median {live[len(live) // 2]:.0f}  max {live[-1]:.0f}")
    urgent = [REFERENCE / m for m in live]
    urgent.sort()
    print(f"  urgency (50/margin)  : min {urgent[0]:.3f}  "
          f"median {urgent[len(urgent) // 2]:.3f}  max {urgent[-1]:.3f}")
    print(f"  actions with urgency > 1 (inside the horizon): "
          f"{sum(1 for u in urgent if u > 1.0)}/{len(urgent)}")
else:
    print("  every action sat at the fallback -- the term never bit")
