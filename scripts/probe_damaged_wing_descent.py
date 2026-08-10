"""WHY does damaged_wing reach the ground?

Three episodes, one ground contact, and the crashing one is a sharp outlier on
exactly one axis: maximum structural utilization 16.20 against 0.64 for the
other two, with control saturation of 0.001. Enormous loads while the
controller was barely commanding. That combination is the thing to explain --
it rules out "commanded hard and could not" and points at either a departure
the controller never fought, or a controller that stopped commanding.

This walks the trace and reports, per phase of the episode, the quantities that
separate those readings: attitude and rates (is it departed?), angle of attack
and airspeed (is it stalled?), the commanded targets (is it asking for
anything?), and the regime/viability state (does it know?).

Purely additive: it reads the trace the runner already produces.
"""
from __future__ import annotations

import math
import os
import sys

os.environ.setdefault("GAMMA_REGIME_DIAGNOSTICS", "1")
sys.path.insert(0, ".")

from scripts.jabberwock_jsbsim_f16_paper_replication import (  # noqa: E402
    run_experiment,
)

FEET = 1.0 / 0.3048
scenario = sys.argv[1] if len(sys.argv) > 1 else "damaged_wing"
episodes = int(sys.argv[2] if len(sys.argv) > 2 else 1)

report = run_experiment(scenario_names=(scenario,),
                        episodes_per_scenario=episodes,
                        base_seed=241102975, include_trace=True)

for index, episode in enumerate(report["scenarios"][scenario]["episodes"]):
    trace = episode.get("trace") or []
    metrics = episode["metrics"]
    if not trace:
        print(f"episode {index}: no trace")
        continue
    print(f"\n### {scenario} episode {index} "
          f"(ground_contact={metrics.get('ground_contact')}, "
          f"min_alt={metrics.get('minimum_altitude_ft'):.0f} ft, "
          f"struct={metrics.get('maximum_structural_utilization'):.2f})")
    print(f"  {'act':>5}{'alt_ft':>9}{'ias':>7}{'aoa':>7}"
          f"{'t_fwd':>8}{'t_vert':>8}{'t_pitch':>9}{'t_turn':>8}"
          f"{'margin':>8}{'rung':>6}{'recal':>7}{'pred_err':>11}{'mode':>12}")
    step = max(1, len(trace) // 24)
    rows = list(range(0, len(trace), step)) + [len(trace) - 1]
    for i in sorted(set(rows)):
        row = trace[i]
        roll, pitch, _yaw = row["attitude_angles"]
        p, q, r = row["body_rates"]
        target = row["target_consequence_delta"]
        print(f"  {row['request_seq']:>5}"
              f"{float(row['altitude_m']) * FEET:>9.0f}"
              f"{float(row['airspeed_m_s']):>7.1f}"
              f"{math.degrees(float(row['angle_of_attack_radians'])):>7.1f}"
              f"{float(target['forward']):>8.3f}"
              f"{float(target['vertical']):>8.3f}"
              f"{float(row['target_body_rate_delta'][1]):>9.3f}"
              f"{float(row['target_body_rate_delta'][2]):>8.3f}"
              f"{float(row.get('margin_actions', -1.0)):>8.0f}"
              f"{float(row.get('f16_viability_rung', -1.0)):>6.0f}"
              f"{float(row['recalibration_count']):>7.0f}"
              f"{float(row['prediction_error_energy']):>11.2f}"
              f"  {str(row['program_mode'])[:10]:<10}")

    # The phase the episode ends in is what has to be explained.
    tail = trace[-40:]
    aoa = [math.degrees(float(r["angle_of_attack_radians"])) for r in tail]
    beta = [math.degrees(float(r["sideslip_radians"])) for r in tail]
    yaw_rate = [math.degrees(float(r["body_rates"][2])) for r in tail]
    nz = [float(r["normal_load_factor"]) for r in tail]
    print(f"\n  last 40 actions: aoa {min(aoa):.1f}..{max(aoa):.1f} deg   "
          f"beta {min(beta):.1f}..{max(beta):.1f} deg   "
          f"yaw rate {min(yaw_rate):.1f}..{max(yaw_rate):.1f} deg/s   "
          f"nz {min(nz):.2f}..{max(nz):.2f}")
    modes = {}
    for row in trace:
        modes[str(row["program_mode"])] = modes.get(
            str(row["program_mode"]), 0) + 1
    print(f"  program_mode over the episode: {modes}")


    # IS THE TRIGGER SCALED AT ALL?  `compound_surprise_threshold` is a fixed
    # absolute 2.0.  If the signal it judges spans orders of magnitude, that
    # constant is not a threshold, it is a coin flip weighted by units -- and
    # the recalibration BUDGET exists only to stop the resulting chatter.  A
    # budget is hysteresis, and hysteresis is a sign of a scaling error.
    energies = sorted(float(r["prediction_error_energy"]) for r in trace)
    live = [e for e in energies if e > 0.0]
    THRESHOLD = 2.0
    over = sum(1 for e in energies if e > THRESHOLD)
    print(f"\n  prediction_error_energy vs a FIXED threshold of {THRESHOLD}:")
    if live:
        # Percentiles, not min/max: the minimum is denormal and a raw span
        # ratio off it prints a meaningless number with forty digits.
        p05 = live[len(live) // 20]
        p95 = live[(len(live) * 19) // 20]
        print(f"    p05 {p05:.3f}  median {live[len(live) // 2]:.2f}  "
              f"p95 {p95:.1f}  max {live[-1]:.1f}")
    print(f"    actions over threshold: {over}/{len(energies)} "
          f"({100.0 * over / len(energies):.1f}%)")
    print(f"    -> the trigger is satisfied on {100.0 * over / len(energies):.0f}% "
          "of actions; the budget is the only thing stopping it")
