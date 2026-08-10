"""Run the paired graph-native actuator damage and wear engineering pilot.

The host constructs mechanical conditions and records outcomes. Both arms use
the same graph-authored opaque action schedule. Only the Rust graph's
post-onset plasticity differs.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.pybullet_robot_world import (
    MORPHOLOGIES,
    MechanicalCondition,
)
from scripts.jabberwock_embodied_adaptation import run_episode


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("cannot summarize an empty metric window")
    return sum(values) / len(values)


def _condition(name: str, onset: int) -> MechanicalCondition:
    if name == "damage":
        return MechanicalCondition(
            onset_action=onset,
            abrupt_retention=(0.0, 1.0),
        )
    if name == "wear":
        return MechanicalCondition(
            onset_action=onset,
            wear_per_use=(0.04, 0.0),
            minimum_retention=0.2,
        )
    raise ValueError(f"unknown condition {name!r}")


def _summary(
    condition: str,
    morphology: str,
    adaptive: dict[str, Any],
    frozen: dict[str, Any],
    *,
    onset: int,
    window: int,
) -> dict[str, Any]:
    adaptive_post = adaptive["trace"][onset:]
    frozen_post = frozen["trace"][onset:]
    adaptive_first = _mean(
        [float(row["prediction_error"]) for row in adaptive_post[:window]]
    )
    adaptive_last = _mean(
        [float(row["prediction_error"]) for row in adaptive_post[-window:]]
    )
    frozen_first = _mean(
        [float(row["prediction_error"]) for row in frozen_post[:window]]
    )
    frozen_last = _mean(
        [float(row["prediction_error"]) for row in frozen_post[-window:]]
    )
    return {
        "condition": condition,
        "morphology": morphology,
        "onset_action": onset,
        "window": window,
        "same_graph_action_schedule": (
            [row["selected_token"] for row in adaptive["trace"]]
            == [row["selected_token"] for row in frozen["trace"]]
        ),
        "same_pre_onset_trajectory": (
            adaptive["trace"][onset - 1]["post_base_position"]
            == frozen["trace"][onset - 1]["post_base_position"]
        ),
        "adaptive_first_post_error": adaptive_first,
        "adaptive_last_post_error": adaptive_last,
        "adaptive_fractional_error_recovery": (
            (adaptive_first - adaptive_last) / adaptive_first
        ),
        "frozen_first_post_error": frozen_first,
        "frozen_last_post_error": frozen_last,
        "frozen_fractional_error_recovery": (
            (frozen_first - frozen_last) / frozen_first
        ),
        "late_error_advantage": frozen_last - adaptive_last,
        "adaptive_post_onset_surprises": sum(
            float(row["surprise"]) for row in adaptive_post
        ),
        "frozen_post_onset_surprises": sum(
            float(row["surprise"]) for row in frozen_post
        ),
    }


def run_pilot(
    *,
    steps: int = 108,
    onset: int = 45,
    babble_samples: int = 2,
    seed: int = 0,
    goal: tuple[float, float, float] = (3.0, 0.0, 0.0),
    window: int = 18,
) -> dict[str, Any]:
    if onset < babble_samples * 9:
        raise ValueError("condition onset must follow complete motor babble")
    if steps - onset < window * 2:
        raise ValueError("steps after onset must hold two complete metric windows")

    results = []
    summaries = []
    for condition_name in ("damage", "wear"):
        condition = _condition(condition_name, onset)
        for morphology in MORPHOLOGIES:
            pair = {}
            for mode in ("adaptive_probe", "frozen_probe_control"):
                row = run_episode(
                    morphology,
                    mode,
                    steps=steps,
                    goal=goal,
                    seed=seed,
                    babble_samples=babble_samples,
                    mechanical_condition=condition,
                )
                row["condition_name"] = condition_name
                results.append(row)
                pair[mode] = row
            summaries.append(
                _summary(
                    condition_name,
                    morphology,
                    pair["adaptive_probe"],
                    pair["frozen_probe_control"],
                    onset=onset,
                    window=window,
                )
            )
    return {
        "experiment": "graph_native_damage_wear_adaptation_engineering_pilot",
        "status": "engineering_pilot_not_confirmatory",
        "steps": steps,
        "onset_action": onset,
        "babble_samples": babble_samples,
        "seed": seed,
        "goal": list(goal),
        "metric_window": window,
        "results": results,
        "summaries": summaries,
        "failures": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=108)
    parser.add_argument("--onset", type=int, default=45)
    parser.add_argument("--babble-samples", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--goal", nargs=3, type=float, default=(3.0, 0.0, 0.0))
    parser.add_argument("--window", type=int, default=18)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "results" / "embodied_damage_wear_engineering_pilot.json",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    payload = run_pilot(
        steps=args.steps,
        onset=args.onset,
        babble_samples=args.babble_samples,
        seed=args.seed,
        goal=tuple(args.goal),
        window=args.window,
    )
    rendered = json.dumps(payload, indent=2)
    args.json_out.write_text(rendered + os.linesep, encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
