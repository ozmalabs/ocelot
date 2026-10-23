"""Isolated development scoring for restored P22 checkpoint panels."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointExpression, _checkpoint_digest_valid,
    score_restored_checkpoint_task,
)
from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world_v2, generate_loopover_world_v2,
)
from evaluation.process_mastery.p22_resource_accounting import (
    compare_resource_snapshots, resource_snapshot_digest_valid,
)
from substrate.boot_profiles import boot_cognition_on


_GENERATORS = {"d4": generate_d4_world_v2,
               "loopover": generate_loopover_world_v2}
_WORLD_GENERATORS = {
    "pmb_generated_d4_corner_v2": generate_d4_world_v2,
    "pmb_generated_loopover_v2": generate_loopover_world_v2,
}
_EXPECTED_ARMS = {"unchanged", "adaptive_only", "invention_only", "full"}


def _rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _seal_isolated_measurements(outcome: dict, *, wall_seconds: float,
                                peak_rss_bytes: int,
                                parent_runtime: dict) -> dict:
    snapshot = copy.deepcopy(outcome["resource_snapshot"])
    runtime = snapshot["runtime_counters"]
    runtime["wall_time_seconds"] = float(parent_runtime.get(
        "wall_time_seconds", 0.0)) + wall_seconds
    runtime["process_peak_rss_bytes"] = max(int(parent_runtime.get(
        "process_peak_rss_bytes", 0)), peak_rss_bytes)
    coverage = snapshot["resource_measurement_coverage"]
    coverage["wall_time_seconds"] = {"status": "MEASURED",
        "scope": "cumulative prior worker time plus isolated checkpoint worker perf_counter",
        "source": "p22_isolated_worker.perf_counter"}
    coverage["process_peak_rss_bytes"] = {"status": "MEASURED",
        "scope": "maximum of prior isolated checkpoint workers and this worker ru_maxrss",
        "source": "p22_isolated_worker.ru_maxrss"}
    snapshot.pop("snapshot_sha256", None)
    snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(snapshot,
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if not resource_snapshot_digest_valid(snapshot):
        raise RuntimeError("isolated resource snapshot reseal failed")
    outcome["resource_snapshot"] = snapshot
    outcome["isolated_worker_wall_time_seconds"] = wall_seconds
    outcome["isolated_worker_peak_rss_bytes"] = peak_rss_bytes
    return outcome


def _worker(payload: dict) -> dict:
    checkpoint = CheckpointExpression(**payload["checkpoint"])
    if not _checkpoint_digest_valid(checkpoint):
        raise ValueError("worker received an unattested checkpoint")
    started = time.perf_counter()
    agent = None
    try:
        agent = boot_cognition_on()
        outcome = score_restored_checkpoint_task(checkpoint,
            world=payload["world"], agent_factory=lambda: agent,
            cumulative_primitive_ceiling=payload["cumulative_primitive_ceiling"],
            native_rule_progress_ceiling=payload["native_rule_progress_ceiling"],
            allow_heldout_evaluation=payload.get(
                "allow_heldout_evaluation", False))
    except BaseException:
        if agent is not None:
            agent.close()
        raise
    wall_seconds = time.perf_counter() - started
    peak_rss_bytes = _rss_bytes()
    parent_snapshot = json.loads(checkpoint.resource_snapshot_json)
    outcome = _seal_isolated_measurements(outcome,
        wall_seconds=wall_seconds, peak_rss_bytes=peak_rss_bytes,
        parent_runtime=parent_snapshot.get("runtime_counters") or {})
    return outcome


def score_checkpoint_world_isolated(checkpoint: dict, world: dict, *,
                                    cumulative_primitive_ceiling: int,
                                    native_rule_progress_ceiling: int,
                                    allow_heldout_evaluation: bool = False) -> dict:
    """Run one restored checkpoint/world cell in a fresh native learner process."""
    if not isinstance(checkpoint, dict) or not _checkpoint_digest_valid(
            CheckpointExpression(**checkpoint)):
        raise ValueError("isolated worker requires a digest-valid native checkpoint")
    if not isinstance(world, dict):
        raise ValueError("isolated worker requires one registered world view")
    payload = {"checkpoint": checkpoint, "world": world,
        "cumulative_primitive_ceiling": cumulative_primitive_ceiling,
        "native_rule_progress_ceiling": native_rule_progress_ceiling,
        "allow_heldout_evaluation": allow_heldout_evaluation}
    completed = subprocess.run([sys.executable, "-m",
        "evaluation.process_mastery.p22_checkpoint_panel", "--worker"],
        input=json.dumps(payload, sort_keys=True), capture_output=True,
        text=True, check=True, env=os.environ | {
            "OZMA_SEED_PERSIST_DISABLED": "1"})
    return json.loads(completed.stdout)


def run_isolated_checkpoint_panel(checkpoints: dict[str, dict], worlds: list[dict], *,
                                  cumulative_primitive_ceiling: int = 30_000,
                                  native_rule_progress_ceiling: int = 20_000) -> dict:
    """Score each checkpoint/world cell in a separate process."""
    if not isinstance(checkpoints, dict) or set(checkpoints) != _EXPECTED_ARMS:
        raise ValueError("isolated P22 panel requires all four registered arm checkpoints")
    if not isinstance(worlds, list) or not worlds:
        raise ValueError("isolated P22 panel requires registered training worlds")
    if (isinstance(cumulative_primitive_ceiling, bool)
            or not isinstance(cumulative_primitive_ceiling, int)
            or not 1 <= cumulative_primitive_ceiling <= 120_000):
        raise ValueError("cumulative primitive ceiling must be an integer in [1, 120000]")
    if (isinstance(native_rule_progress_ceiling, bool)
            or not isinstance(native_rule_progress_ceiling, int)
            or not 1 <= native_rule_progress_ceiling <= 10_000_000):
        raise ValueError("native rule-progress ceiling must be an integer in [1, 10000000]")
    seen_worlds = set()
    for world in worlds:
        if not isinstance(world, dict):
            raise ValueError("panel world must be a registered training-world view")
        generator = _WORLD_GENERATORS.get(world.get("family"))
        if generator is None:
            raise ValueError("unsupported registered P22 training family")
        draw = world.get("draw")
        if (world.get("split") != "train" or isinstance(draw, bool)
                or not isinstance(draw, int) or not 0 <= draw < 1000
                or world != agent_view(generator(split="train", draw=draw))):
            raise ValueError("panel worlds must exactly match registered training views")
        if world["world_id"] in seen_worlds:
            raise ValueError("panel training-world identities must be unique")
        seen_worlds.add(world["world_id"])
    records = {}
    identities = []
    for arm, record in checkpoints.items():
        checkpoint = CheckpointExpression(**record)
        if not _checkpoint_digest_valid(checkpoint):
            raise ValueError(f"{arm} checkpoint failed digest verification")
        identities.append(checkpoint.checkpoint_id)
        records[arm] = record
    if len(set(identities)) != len(identities):
        raise ValueError("arm checkpoint identities must be unique")

    rows = []
    arm_outcomes = {arm: [] for arm in checkpoints}
    for world in worlds:
        outcomes = {}
        for arm, checkpoint in records.items():
            outcome = score_checkpoint_world_isolated(checkpoint, world,
                cumulative_primitive_ceiling=cumulative_primitive_ceiling,
                native_rule_progress_ceiling=native_rule_progress_ceiling,
                allow_heldout_evaluation=False)
            outcomes[arm] = outcome
            arm_outcomes[arm].append(outcome)
        resources = compare_resource_snapshots({arm: outcome["resource_snapshot"]
            for arm, outcome in outcomes.items()})
        rows.append({"world_id": world["world_id"], "outcomes": outcomes,
            "same_world": all(outcome["world_id"] == world["world_id"]
                              for outcome in outcomes.values()),
            "same_cumulative_primitive_work": len({outcome[
                "cumulative_primitive_work"] for outcome in outcomes.values()}) == 1,
            "primitive_budgets_respected": all(outcome[
                "primitive_budget_respected"] for outcome in outcomes.values()),
            "rule_progress_limits_respected": all(outcome[
                "rule_progress_limit_respected"] for outcome in outcomes.values()),
            "resource_comparison": resources})
    return {"status": "DEVELOPMENT_ONLY", "split": "training",
        "world_ids": [world["world_id"] for world in worlds],
        "cumulative_primitive_ceiling": cumulative_primitive_ceiling,
        "native_rule_progress_ceiling": native_rule_progress_ceiling,
        "same_worlds": all(row["same_world"] for row in rows),
        "same_cumulative_primitive_work": all(row[
            "same_cumulative_primitive_work"] for row in rows),
        "primitive_budgets_respected": all(row["primitive_budgets_respected"]
                                            for row in rows),
        "resource_matched": all(row["resource_comparison"][
            "all_resource_dimensions_match"] for row in rows),
        "all_contract_dimensions_measured": all(row["resource_comparison"][
            "all_contract_dimensions_measured"] for row in rows),
        "efficiency_comparable": all(row["same_cumulative_primitive_work"]
            and row["primitive_budgets_respected"]
            and row["resource_comparison"]["all_resource_dimensions_match"]
            and all(outcome["status"] == "COMPLETED"
                    for outcome in row["outcomes"].values()) for row in rows),
        "arms": {arm: {"outcomes": outcomes,
            "solved_count": sum(outcome["score"] for outcome in outcomes),
            "native_rule_steps": sum(outcome["native_rule_steps"]
                                      for outcome in outcomes),
            "cumulative_primitive_work": [outcome["cumulative_primitive_work"]
                                          for outcome in outcomes],
            "approval_events_added": sum(outcome["approval_events_added"]
                                         for outcome in outcomes),
            "world_receipts_added": sum(outcome["world_receipts_added"]
                                        for outcome in outcomes)}
            for arm, outcomes in arm_outcomes.items()},
        "rows": rows, "efficacy_established": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--roots", type=Path)
    parser.add_argument("--family", choices=tuple(_GENERATORS))
    parser.add_argument("--draws", type=int, nargs="+")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cumulative-primitive-ceiling", type=int, default=30_000)
    parser.add_argument("--native-rule-progress-ceiling", type=int, default=20_000)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(_worker(json.load(sys.stdin)), sort_keys=True))
        return 0
    if args.roots is None or args.family is None or not args.draws or args.output is None:
        parser.error("normal mode requires --roots, --family, --draws, and --output")
    root = json.loads(args.roots.read_text())
    checkpoints = {arm: data["generation_zero_checkpoint"]
                   for arm, data in root["arms"].items()}
    worlds = [agent_view(_GENERATORS[args.family](split="train", draw=draw))
              for draw in args.draws]
    result = run_isolated_checkpoint_panel(checkpoints, worlds,
        cumulative_primitive_ceiling=args.cumulative_primitive_ceiling,
        native_rule_progress_ceiling=args.native_rule_progress_ceiling)
    raw = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if str(args.output).endswith(".gz"):
        args.output.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    else:
        args.output.write_bytes(raw)
    print(json.dumps({"status": result["status"], "family": args.family,
        "world_ids": result["world_ids"],
        "primitive_budgets_respected": result["primitive_budgets_respected"],
        "resource_matched": result["resource_matched"],
        "all_contract_dimensions_measured": result["all_contract_dimensions_measured"],
        "solved": {arm: row["solved_count"] for arm,row in result["arms"].items()},
        "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
