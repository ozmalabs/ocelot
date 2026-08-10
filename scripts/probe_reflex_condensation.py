"""Read the surprise-shape index the condensation rules build.

Purely additive: it captures the agent handle on the way past and reads the
library out at the end.  It changes nothing and decides nothing -- the
condensation and release decisions are `emp_condense_surprise_reflex` and
`emp_release_condensed_reflex`, which run in the graph's own fixpoint.

What it answers, in the order the answers matter:

  1. Does the residual quantise into a USABLE number of shapes?  One shape
     means the quantum is too coarse to say anything; one shape per encounter
     means it is too fine for any shape to accumulate a history.
  2. Do runs actually LENGTHEN?  A run of 1 everywhere means the response
     varies every encounter and there is nothing to condense.
  3. Does anything condense, and does anything RELEASE?  Condensation without
     release is the failure mode the whole design is against.
"""
from __future__ import annotations

import math
import os
import sys

os.environ.setdefault("GAMMA_REGIME_DIAGNOSTICS", "1")
sys.path.insert(0, ".")

import scripts.jabberwock_fixed_wing_jet as J  # noqa: E402

HANDLE: list = []
_original = J._settle_graph_request


TRACE: list = []


def _patched(agent, episode, request_seq, *args, **kwargs):
    if not HANDLE:
        HANDLE.append(agent)
    result = _original(agent, episode, request_seq, *args, **kwargs)
    # Mechanical read-back of the two quantities the rules join on, so a
    # non-firing rule can be told apart from a rule with nothing to fire on.
    programs = agent.inner.neighbours(episode, "has_default_embodied_motor_program")
    for program in programs[:1]:
        a = agent.s.node(program)["attrs"]
        TRACE.append((
            request_seq,
            float(a.get("relative_normal_load_error", -1.0)),
            float(a.get("prediction_error_energy", -1.0)),
            len(agent.inner.neighbours(
                program, "includes_embodied_effector_model")),
            len(agent.inner.neighbours(
                agent.agent, "has_embodied_surprise_shape_library")),
        ))
    return result


J._settle_graph_request = _patched

from scripts.jabberwock_jsbsim_f16_paper_replication import (  # noqa: E402
    run_experiment,
)

scenario = sys.argv[1] if len(sys.argv) > 1 else "nominal"
episodes = int(sys.argv[2]) if len(sys.argv) > 2 else 1
run_experiment(scenario_names=(scenario,), episodes_per_scenario=episodes,
               base_seed=241102975, include_trace=False)

if not HANDLE:
    print("no agent handle captured")
    raise SystemExit(1)

agent = HANDLE[0]
root = agent.agent
shapes = agent.inner.neighbours(root, "has_embodied_surprise_shape_library")
print(f"\n### {scenario}: {len(shapes)} surprise shapes")
print(f"  {'ordinal':>8}{'run':>6}{'order':>7}{'status':>11}{'seen@':>8}  response")
rows = []
for node in shapes:
    a = agent.s.node(node)["attrs"]
    rows.append((
        float(a.get("ordinal", 0.0)),
        float(a.get("stable_run", 0.0)),
        float(a.get("order", 1.0)),
        str(a.get("status", "?")),
        str(a.get("response_shape", ""))[:40],
        float(a.get("last_seen_seq", -1.0)),
    ))
for ordinal, run, order, status, response, seen in sorted(rows):
    print(f"  {ordinal:>8.0f}{run:>6.0f}{order:>7.0f}{status:>11}"
          f"{seen:>8.0f}  {response}")

condensed = [r for r in rows if r[2] < 0.5]
epoch = float(agent.s.node(root)["attrs"].get("motor_reflex_epoch", 0.0))
runs = [r[1] for r in rows]
print(f"\n  condensed now : {len(condensed)}/{len(rows)}")
print(f"  reflex epoch  : {epoch:.0f}"
      "   (condensations + releases over the whole run)")
if runs:
    print(f"  run length    : max {max(runs):.0f}  "
          f"mean {sum(runs) / len(runs):.1f}  "
          f"singletons {sum(1 for r in runs if r < 1.5)}/{len(runs)}")

# The firing side: did order 0 actually fire, and how often?
root_attrs = agent.s.node(root)["attrs"]
enactments = float(root_attrs.get("motor_reflex_enactments", 0.0))
fires = 0.0
for node in agent.inner.neighbours(root, "has_reflex"):
    at = agent.s.node(node)["attrs"]
    if at.get("name") == "motor_reflex_buy_time":
        fires = float(at.get("fire_count", 0.0))
        print(f"\n  reflex        : autonomous={at.get('autonomous')} "
              f"fire_count={fires:.0f}")
print(f"  enactments    : {enactments:.0f}"
      "   (the graph-resident response rule)")

print(f"\n  trace: {len(TRACE)} actions with a default program")
if TRACE:
    errs = [t[1] for t in TRACE]
    print(f"  relative_normal_load_error: min {min(errs):.4f} "
          f"max {max(errs):.4f} unset(-1) {sum(1 for e in errs if e < 0)}")
    import collections
    # The LOG ordinal, matching `surprise_shape_ordinal`.  This read was
    # linear until the seed's ordinal was, and a stale copy here would
    # report buckets the index does not use.
    q = collections.Counter(
        int(math.log(abs(e) + 1.0)) for e in errs if e >= 0)
    print(f"  ordinal histogram: {dict(sorted(q.items())[:12])}")
    print(f"  members per program: "
          f"{collections.Counter(t[3] for t in TRACE).most_common(5)}")
    lib = [t[4] for t in TRACE]
    print(f"  library size: first {lib[0]} .. last {lib[-1]}; "
          f"grew at {sum(1 for i in range(1, len(lib)) if lib[i] > lib[i-1])} actions")
