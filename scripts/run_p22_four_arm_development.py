#!/usr/bin/env python3
"""Run a training-only P22 four-arm native wiring diagnostic."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.process_mastery.p22_four_arm_development import (
    run_p22_four_arm_development,
)
from evaluation.process_mastery.p22_arms import _ARM_SWITCHES
from evaluation.process_mastery.p22_resource_accounting import compare_resource_snapshots


def _run_isolated_arm(family: str, draws: list[int], validation_draws: list[int],
                     arm: str, search_attempt_ceiling: int,
                     measure_native_rule_work: bool,
                     capture_checkpoints: bool) -> dict:
    command = [sys.executable, str(Path(__file__).resolve()), "--family", family,
        "--training-draws", *[str(draw) for draw in draws],
        "--validation-draws", *[str(draw) for draw in validation_draws],
        "--search-attempt-ceiling", str(search_attempt_ceiling),
        "--worker-arm", arm]
    if measure_native_rule_work:
        command.append("--measure-native-rule-work")
    if capture_checkpoints:
        command.append("--capture-checkpoints")
    environment = os.environ.copy()
    environment.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    completed = subprocess.run(command, check=True, capture_output=True,
        text=True, env=environment)
    return json.loads(completed.stdout)


def _run_isolated_arms(family: str, draws: list[int],
                       validation_draws: list[int],
                       search_attempt_ceiling: int,
                       measure_native_rule_work: bool,
                       capture_checkpoints: bool) -> dict:
    runs = {arm: _run_isolated_arm(family, draws, validation_draws, arm,
                                   search_attempt_ceiling,
                                   measure_native_rule_work,
                                   capture_checkpoints)
            for arm in _ARM_SWITCHES}
    arms = {arm: result["arms"][arm] for arm, result in runs.items()}
    snapshots = {arm: data["resource_snapshot"] for arm, data in arms.items()}
    return {"status": "DEVELOPMENT_ONLY", "family": family, "split": "training",
        "training_world_ids": runs["unchanged"]["training_world_ids"],
        "validation_world_ids": runs["unchanged"]["validation_world_ids"],
        "search_attempt_ceiling": search_attempt_ceiling,
        "common_worlds": all(data["training_tasks"] and
            [row["world_id"] for row in data["training_tasks"]] ==
            runs["unchanged"]["training_world_ids"] for data in arms.values()),
        "all_arms_terminal": all(data["all_tasks_terminal"] for data in arms.values()),
        "arms": arms, "resource_comparison": compare_resource_snapshots(snapshots),
        "approvals_created": sum(data["approval_count"] for data in arms.values()),
        "world_receipts_created": sum(data["world_receipt_count"]
                                       for data in arms.values()),
        "efficacy_established": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=("d4", "loopover"), required=True)
    parser.add_argument("--training-draws", type=int, nargs="+", required=True)
    parser.add_argument("--validation-draws", type=int, nargs="*", default=[])
    parser.add_argument("--search-attempt-ceiling", type=int, default=64)
    parser.add_argument("--measure-native-rule-work", action="store_true",
        help="capture isolated per-rule native counters for each arm")
    parser.add_argument("--capture-checkpoints", action="store_true",
        help="capture each isolated arm's complete measured generation-zero native checkpoint")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker-arm", choices=tuple(_ARM_SWITCHES))
    args = parser.parse_args()
    if args.worker_arm:
        result = run_p22_four_arm_development(family=args.family,
            training_draws=tuple(args.training_draws),
            validation_draws=tuple(args.validation_draws),
            search_attempt_ceiling=args.search_attempt_ceiling,
            selected_arms=(args.worker_arm,),
            measure_process_peak_rss=True,
            measure_native_rule_work=args.measure_native_rule_work,
            capture_checkpoints=args.capture_checkpoints)
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.output is None:
        parser.error("--output is required for the four-arm runner")
    result = _run_isolated_arms(args.family, args.training_draws,
                                 args.validation_draws,
                                 args.search_attempt_ceiling,
                                 args.measure_native_rule_work,
                                 args.capture_checkpoints)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "family": result["family"],
        "search_attempt_ceiling": result["search_attempt_ceiling"],
        "common_worlds": result["common_worlds"],
        "resources_match": result["resource_comparison"]["all_resource_dimensions_match"],
        "solved": {arm: data["solved_count"] for arm, data in result["arms"].items()},
        "proposals": {arm: data["proposal_count"] for arm, data in result["arms"].items()},
        "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
