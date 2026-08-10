"""Does the effector layer learn during a departure, and from what?

`emp_learn_factorized_effector_from_exact_receipt` guards on
`expected_member_count == 1` -- and that guard is the IDENTIFIABILITY
CONDITION, not an oversight: with four commanded members one receipt has four
possible owners. So a compound receipt teaches the PROGRAM and no effector
model, and BV measured that composition variation cannot recover the members
during exactly the window where they are wrong (rank deficit 3.27 deep in the
stall, 348 of 450 actions on one 4-member program).

The targeted-exercise design was selected on that evidence and landed as
`attribution_refresh_actions`. This probe asks the question that decides
whether credit assignment is still the root: with the exercise in, HOW MUCH
does the effector layer actually learn, and where does that learning come from?

  * `experience_count` per effector model, sampled through the episode --
    the layer's total learning;
  * singleton vs compound receipts -- how many actions can teach at all;
  * models never exercised alone -- the ones no receipt can reach.

Purely additive: reads graph state after each settle, decides nothing.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("GAMMA_REGIME_DIAGNOSTICS", "1")
sys.path.insert(0, ".")

import scripts.jabberwock_fixed_wing_jet as J  # noqa: E402

SAMPLES: list = []
WIDTHS: dict = {}
SINGLETONS: list = []
_original = J._settle_graph_request


def _patched(agent, episode, request_seq, *args, **kwargs):
    result = _original(agent, episode, request_seq, *args, **kwargs)
    models = agent.inner.neighbours(episode, "has_embodied_effector_model")
    counts = [
        float(agent.s.node(m)["attrs"].get("experience_count", 0.0))
        for m in models
    ]
    exercised = [
        float(agent.s.node(m)["attrs"].get("last_singleton_exercise_seq", -1.0))
        for m in models
    ]
    programs = agent.inner.neighbours(
        episode, "has_default_embodied_motor_program")
    width = 0
    for program in programs[:1]:
        width = len(agent.inner.neighbours(
            program, "includes_embodied_effector_model"))
    WIDTHS[width] = WIDTHS.get(width, 0) + 1
    SAMPLES.append((int(request_seq), counts, exercised))
    # WHICH member gets the singleton, and when.  BV part 2 found the budget
    # "already being spent, on the wrong members"; this re-measures that with
    # the attribution refresh in.
    if width == 1:
        for program in programs[:1]:
            for member in agent.inner.neighbours(
                program, "includes_embodied_effector_model"
            ):
                token = str(agent.s.node(member)["attrs"].get("token"))
                SINGLETONS.append((int(request_seq), token))
    return result


J._settle_graph_request = _patched

from scripts.jabberwock_jsbsim_f16_paper_replication import (  # noqa: E402
    run_experiment,
)

scenario = sys.argv[1] if len(sys.argv) > 1 else "damaged_wing"
run_experiment(scenario_names=(scenario,), episodes_per_scenario=1,
               base_seed=241102975, include_trace=False)

print(f"\n### {scenario}: {len(SAMPLES)} actions")
print(f"  program width histogram: {dict(sorted(WIDTHS.items()))}")
singleton = WIDTHS.get(1, 0)
total = sum(WIDTHS.values()) or 1
print(f"  actions that CAN teach an effector (width 1): "
      f"{singleton}/{total} ({100.0 * singleton / total:.1f}%)")

print(f"\n  {'action':>8}{'models':>8}{'exp min':>9}{'exp med':>9}"
      f"{'exp max':>9}{'never alone':>13}")
step = max(1, len(SAMPLES) // 12)
for i in list(range(0, len(SAMPLES), step)) + [len(SAMPLES) - 1]:
    seq, counts, exercised = SAMPLES[i]
    if not counts:
        continue
    ordered = sorted(counts)
    never = sum(1 for e in exercised if e < 0.0)
    print(f"  {seq:>8}{len(counts):>8}{ordered[0]:>9.0f}"
          f"{ordered[len(ordered) // 2]:>9.0f}{ordered[-1]:>9.0f}"
          f"{never:>13}")

first, last = SAMPLES[0], SAMPLES[-1]
if first[1] and last[1]:
    gained = sum(last[1]) - sum(first[1])
    print(f"\n  TOTAL effector experience gained over the episode: {gained:.0f}"
          f"  across {len(last[1])} models and {len(SAMPLES)} actions")
    print(f"  per action: {gained / max(1, len(SAMPLES)):.3f} samples")
    never = sum(1 for e in last[2] if e < 0.0)
    print(f"  models NEVER exercised alone at the end: {never}/{len(last[2])}")


# Where the exercise budget actually goes.
import collections  # noqa: E402
SPLIT = 250
early = collections.Counter(t for seq, t in SINGLETONS if seq < SPLIT)
late = collections.Counter(t for seq, t in SINGLETONS if seq >= SPLIT)
print(f"\n  singleton exercises: {len(SINGLETONS)} total "
      f"({sum(early.values())} before action {SPLIT}, "
      f"{sum(late.values())} after)")
print(f"  distinct members exercised alone: {len(early)} before, "
      f"{len(late)} after")
if late:
    top = late.most_common(5)
    share = 100.0 * top[0][1] / sum(late.values())
    print(f"  after {SPLIT}, top members: {top}")
    print(f"  -> the most-exercised member takes {share:.0f}% of the late budget")
