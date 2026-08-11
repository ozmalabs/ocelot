#!/usr/bin/env python3
"""Measure decision_making_spike.md §103's two legs: resource-currency sunk
cost (real, not illustrative) and a second declared threat region.

Mechanical measurement tooling only (the `scripts/analyse_f16_*.py`
convention) -- it runs episodes through the existing graph-native seed and
reads the trace back out.  No decisions live here; every number reported is
either read straight off the trace or a plain arithmetic reduction of it
(min/max/mean/first-crossing-index), matching `analyse_f16_energy_ledger.py`'s
own "mechanical reporting only" discipline.

Usage:
    GAMMA_REGIME_DIAGNOSTICS=1 python scripts/measure_risk_ladder_sunk_cost_ticks.py \\
        --leg 1 --output results/risk_ladder_leg1_v1.json
    GAMMA_REGIME_DIAGNOSTICS=1 python scripts/measure_risk_ladder_sunk_cost_ticks.py \\
        --leg 2 --output results/risk_ladder_leg2_v1.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("GAMMA_REGIME_DIAGNOSTICS", "1")

from scripts.jabberwock_jsbsim_f16_paper_replication import (  # noqa: E402
    _run_episode,
)

STEPS = 1000
CONTROL_FREQUENCY_HZ = 10
FAILURE_ONSET_ACTION = 100
REFERENCE_CHANGE_ACTION = 200
BASE_SEED = 24_110_2975

LEG1_SCENARIOS = ("nominal", "jammed_rudder", "damaged_wing")


def _run(scenario_name: str, overrides: dict[str, float] | None) -> dict[str, Any]:
    return _run_episode(
        scenario_name=scenario_name,
        seed=BASE_SEED,
        steps=STEPS,
        control_frequency_hz=CONTROL_FREQUENCY_HZ,
        failure_onset_action=FAILURE_ONSET_ACTION,
        reference_change_action=REFERENCE_CHANGE_ACTION,
        randomized_initial_condition=False,
        gust_standard_deviation_fps=0.0,
        control_quantization_intervals=8,
        include_trace=True,
        extra_episode_overrides=overrides,
    )


def _rung_distribution(trace: list[dict]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for row in trace:
        rung = str(int(row.get("f16_viability_rung", -1)))
        dist[rung] = dist.get(rung, 0) + 1
    return dist


def _first_crossing(trace: list[dict], key: str, threshold: float) -> int | None:
    for row in trace:
        if float(row.get(key, 0.0)) >= threshold:
            return int(row["request_seq"])
    return None


def _summarise_episode(name: str, episode: dict) -> dict[str, Any]:
    trace = episode["trace"]
    metrics = episode["metrics"]
    return {
        "scenario": name,
        # The authoritative crash definition from `_episode_metrics`
        # (`jabberwock_jsbsim_f16_paper_replication.py`) -- ground contact,
        # minimum altitude <= 0, or a plant-failure exception -- read
        # straight off, not reimplemented.
        "crash": bool(metrics["crash"]),
        "paper_like_crash": bool(metrics["paper_like_crash"]),
        "minimum_altitude_ft": float(metrics["minimum_altitude_ft"]),
        "min_altitude_m": min(float(r["altitude_m"]) for r in trace),
        "rung_distribution": _rung_distribution(trace),
        "final_regime_spend_floor": float(trace[-1].get("regime_spend_floor", 0.0)),
        "final_regime_info_spend_floor": float(
            trace[-1].get("regime_info_spend_floor", 0.0)
        ),
        "max_regime_resource_spent_log": max(
            float(r.get("regime_resource_spent_log", 0.0)) for r in trace
        ),
        "max_regime_resource_spent_in_rungs": max(
            float(r.get("regime_resource_spent_in_rungs", 0.0)) for r in trace
        ),
        "final_f16_resource_fraction_remaining": float(
            trace[-1].get("f16_resource_fraction_remaining", 1.0)
        ),
        "info_budget_exhausted_first_action": _first_crossing(
            trace, "regime_info_budget_exhausted", 0.5
        ),
        "budget_exhausted_first_action": _first_crossing(
            trace, "regime_budget_exhausted", 0.5
        ),
        # `f16_probe_stopped_seq`: the action at which the checklist actually
        # stopped (`f16_stop_probe_on_quorum` -- either the response-lag
        # quorum or the info budget, whichever OR-condition fired first).
        # -1.0 (never stopped) reads as None.
        "probe_stopped_at": (
            int(trace[-1]["f16_probe_stopped_seq"])
            if float(trace[-1].get("f16_probe_stopped_seq", -1.0)) >= 0.0
            else None
        ),
        "calibration_action_count": sum(
            1 for r in trace if r.get("program_mode") == "calibration"
        ),
    }


def leg1(output: Path | None) -> dict[str, Any]:
    """Resource-currency sunk cost, real ledger.

    Three arms per scenario:
      baseline            -- no regime_resource_decade declared (byte-identity check)
      parallel (decade=1) -- the operator's natural "same scale as rung_decade"
                              choice; the real, per-action fuel-derived ledger
      positive_control      -- decade=1.0 (a valid whole-number decade -- see
                              the IDiv note below), `regime_resource_spent_log`
                              INITIALISED to 2.0 via `extra_episode_overrides`.
                              The rule's own ratchet (`Max(previous, now)`)
                              only ever raises this floor further over the
                              episode, so a 2.0 initial reading is a clean,
                              honest "what if the ledger already reported two
                              decades of committed resource" positive control
                              -- proving the FLOOR ARITHMETIC and the budget
                              flags respond correctly, independent of whether
                              a 100 s episode's real fuel burn reaches that
                              magnitude (it does not, by a wide margin -- see
                              the calibration table).

    IDiv NOTE (found before this run, via a standalone non-JSBSim probe of
    the rule against a synthetic graph -- checked, not assumed): the engine's
    `IDiv` truncates BOTH operands to i64 BEFORE dividing
    (`runners/dsl/src/term.rs`), not "divide then truncate."  This means
    `regime_resource_decade` (and, inherited unchanged, the pre-existing
    `regime_rung_decade`) must be a POSITIVE WHOLE NUMBER for the documented
    "worth divided by the decade" arithmetic to hold -- a non-integer decade
    silently reads every ratio through it as ZERO rather than erroring
    (verified: decade=0.5 with spent_log=2.0 yields 0 rungs, not 4). This
    means ANY `regime_resource_spent_log` below 1.0 contributes exactly zero
    rungs regardless of which positive integer decade is declared, since the
    NUMERATOR also truncates to 0 first -- a stronger, more deterministic
    mechanism for Prediction 1 than "order of magnitude below the decade"
    alone would suggest, and the reason the original 0.005-decade design for
    this arm (chosen before this probe) was replaced.  Not this rung's bug to
    fix: the pattern is inherited verbatim from the existing worth/info_worth
    terms per this rung's own composition requirement (§98's "must compose
    the same way").
    """
    results: dict[str, Any] = {"leg": 1, "scenarios": {}}
    for name in LEG1_SCENARIOS:
        arms: dict[str, Any] = {}
        baseline_ep = _run(name, None)
        arms["baseline"] = _summarise_episode(name, baseline_ep)
        parallel_ep = _run(name, {"regime_resource_decade": 1.0})
        arms["parallel_decade_1_0"] = _summarise_episode(name, parallel_ep)
        control_ep = _run(name, {
            "regime_resource_decade": 1.0,
            "regime_resource_spent_log": 2.0,
        })
        arms["positive_control_injected_2_0"] = _summarise_episode(
            name, control_ep
        )
        results["scenarios"][name] = arms
        print(
            f"{name}: baseline crash={arms['baseline']['crash']} "
            f"floor(info)={arms['baseline']['final_regime_info_spend_floor']} | "
            f"parallel crash={arms['parallel_decade_1_0']['crash']} "
            f"floor(info)={arms['parallel_decade_1_0']['final_regime_info_spend_floor']} "
            f"resource_rungs={arms['parallel_decade_1_0']['max_regime_resource_spent_in_rungs']} | "
            f"control crash={arms['positive_control_injected_2_0']['crash']} "
            f"floor(info)={arms['positive_control_injected_2_0']['final_regime_info_spend_floor']} "
            f"resource_rungs={arms['positive_control_injected_2_0']['max_regime_resource_spent_in_rungs']}"
        )
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


def leg2(output: Path | None) -> dict[str, Any]:
    """Declared threat region, generalising §86's terrain-only wiring.

    A scripted closing threat (range 4000 m, closing rate 50 m/s -> crosses
    the 80-action/8s evidence horizon around action 720 and fully closes
    around action 800 within the 1000-action episode) declared on nominal
    (clean signal: no other fault) and on damaged_wing (interaction with an
    already-degraded viability ladder).
    """
    threat_overrides = {
        "f16_threat_enabled": 1.0,
        "f16_threat_initial_range_m": 4000.0,
        "f16_threat_closing_rate_m_s": 50.0,
    }
    results: dict[str, Any] = {"leg": 2, "scenarios": {}}
    for name in ("nominal", "damaged_wing"):
        without = _run(name, None)
        with_threat = _run(name, threat_overrides)
        results["scenarios"][name] = {
            "without_threat": _summarise_episode(name, without),
            "with_threat": _summarise_episode(name, with_threat),
        }
        wt = results["scenarios"][name]["with_threat"]
        trace = with_threat["trace"]
        region_actions_min = min(
            float(r.get("f16_threat_region_actions", 1024.0)) for r in trace
        )
        first_capped = _first_crossing(
            trace,
            "f16_threat_region_inside",
            0.5,
        )
        print(
            f"{name}: without rung_dist={results['scenarios'][name]['without_threat']['rung_distribution']} "
            f"| with_threat rung_dist={wt['rung_distribution']} "
            f"min_region_actions={region_actions_min} first_inside_action={first_capped}"
        )
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, choices=(1, 2), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.leg == 1:
        leg1(args.output)
    else:
        leg2(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
