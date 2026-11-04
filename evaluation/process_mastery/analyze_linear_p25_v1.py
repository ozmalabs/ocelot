"""Frozen P25 paired retention analyzer version 1."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.process_mastery.linear_p25_v1 import (
    ARMS, BOOTSTRAP_SEED, BOOTSTRAPS, CONTROL_KINDS, FAMILIES,
    HELDOUT_STREAMS_PER_CELL, MAX_NEW_TASK_LOSS, PHASE, PRIMARY_GAIN,
    RAW_HELDOUT, RESOURCE_LIMITS, _digest, _sha, allocation,
)


def _percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("empty percentile input")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    low = int(math.floor(pos))
    high = int(math.ceil(pos))
    if low == high:
        return ordered[low]
    weight = pos - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def _validate_rows(payload: dict) -> tuple[list[str], dict]:
    failures = []
    plan = payload.get("allocation_plan", {})
    streams = {}
    for cell in plan.get("stream_cells", []):
        for stream_id, seed in zip(cell.get("stream_ids", []), cell.get("seeds", [])):
            streams[stream_id] = {"family": cell.get("family"),
                                  "capacity_ratio": cell.get("capacity_ratio"),
                                  "seed": seed}
    rows = payload.get("streams", [])
    grouped = defaultdict(dict)
    for row in rows:
        stream_id, arm = row.get("stream_id"), row.get("arm")
        if stream_id not in streams or arm not in ARMS or arm in grouped[stream_id]:
            failures.append(f"unexpected_or_duplicate_row:{stream_id}:{arm}")
            continue
        grouped[stream_id][arm] = row
        expected = streams[stream_id]
        if row.get("family") != expected["family"]:
            failures.append(f"family_mismatch:{stream_id}:{arm}")
        if row.get("capacity_ratio") != expected["capacity_ratio"]:
            failures.append(f"capacity_ratio_mismatch:{stream_id}:{arm}")
        if row.get("seed") != expected["seed"]:
            failures.append(f"seed_mismatch:{stream_id}:{arm}")
        if row.get("status") != "complete":
            failures.append(f"incomplete_stream:{stream_id}:{arm}")
        if row.get("target_actions") != 2:
            failures.append(f"target_action_count:{stream_id}:{arm}")
        if row.get("interference_actions") != RESOURCE_LIMITS["interference_actions_per_arm"]:
            failures.append(f"interference_action_count:{stream_id}:{arm}")
        if row.get("graph_bytes", 0) > RESOURCE_LIMITS["graph_bytes_per_learner"]:
            failures.append(f"graph_bytes_ceiling:{stream_id}:{arm}")
        curve = row.get("curve", [])
        try:
            area = _auc(curve)
            if not math.isclose(area, row.get("normalized_auc", float("nan")),
                                rel_tol=0.0, abs_tol=1e-12):
                failures.append(f"auc_mismatch:{stream_id}:{arm}")
        except (TypeError, ValueError, KeyError):
            failures.append(f"curve_invalid:{stream_id}:{arm}")
    if set(grouped) != set(streams):
        failures.append("stream_allocation_incomplete")
    for stream_id, arm_rows in grouped.items():
        if set(arm_rows) != set(ARMS):
            failures.append(f"paired_arm_incomplete:{stream_id}")
            continue
        targets = {tuple(arm_rows[arm].get("target_receipt_ids", ())) for arm in ARMS}
        interference = {tuple(arm_rows[arm].get("interference_receipt_ids", ())) for arm in ARMS}
        capacities = {arm_rows[arm].get("capacity_bytes") for arm in ARMS}
        bases = {arm_rows[arm].get("capacity_basis_bytes") for arm in ARMS}
        if len(targets) != 1 or len(next(iter(targets), ())) != 2:
            failures.append(f"target_receipt_parity:{stream_id}")
        if len(interference) != 1 or len(next(iter(interference), ())) != 6:
            failures.append(f"interference_receipt_parity:{stream_id}")
        if len(capacities) != 1 or len(bases) != 1:
            failures.append(f"capacity_assignment_not_paired:{stream_id}")
    controls = payload.get("structural_controls", [])
    for kind in CONTROL_KINDS:
        matching = [row for row in controls if row.get("kind") == kind]
        expected_count = plan.get("controls_per_kind")
        if len(matching) != expected_count:
            failures.append(f"control_count:{kind}")
        if any(row.get("status") != "PASS" for row in matching):
            failures.append(f"control_failure:{kind}")
    return failures, {"expected_streams": streams, "paired": grouped,
                     "controls": controls}


def _auc(curve: list[dict]) -> float:
    if len(curve) < 2:
        raise ValueError("P25 delayed curve requires at least two checkpoints")
    xs = [float(row["delay_group"]) for row in curve]
    ys = [float(row["success"]) for row in curve]
    width = xs[-1] - xs[0]
    if width <= 0:
        raise ValueError("P25 delayed curve has invalid span")
    area = sum((xs[index] - xs[index - 1]) * (ys[index] + ys[index - 1]) / 2.0
               for index in range(1, len(xs)))
    return area / width


def _bootstrap(values: list[float], *, seed: int, reps: int = BOOTSTRAPS) -> dict:
    if not values:
        return {"mean": None, "ci99": [None, None], "n": 0}
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(reps):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    return {"mean": sum(values) / n,
            "ci99": [_percentile(means, 0.005), _percentile(means, 0.995)],
            "n": n, "bootstrap_replicates": reps, "bootstrap_seed": seed}


def _analysis(payload: dict) -> dict:
    failures, context = _validate_rows(payload)
    plan = payload.get("allocation_plan", {})
    if payload.get("phase") != PHASE:
        failures.append("phase_mismatch")
    if payload.get("split") == "heldout":
        if payload.get("status") != "heldout_pending_analysis":
            failures.append("heldout_status_mismatch")
        if payload.get("heldout_accessed") is not True:
            failures.append("heldout_access_flag_missing")
        if plan.get("streams_per_family_capacity_cell") != HELDOUT_STREAMS_PER_CELL:
            failures.append("heldout_cell_allocation_mismatch")
    else:
        if payload.get("heldout_accessed") is not False:
            failures.append("development_touched_heldout")
        if payload.get("status") != "development_only":
            failures.append("development_status_mismatch")

    paired = context["paired"]
    differences = []
    new_task_differences = []
    cell_summary = {}
    for family in FAMILIES:
        for ratio in plan.get("capacity_ratios", []):
            cell_streams = [sid for sid, values in paired.items()
                            if context["expected_streams"].get(sid, {}).get("family") == family
                            and context["expected_streams"].get(sid, {}).get("capacity_ratio") == ratio
                            and set(values) == set(ARMS)]
            cell_gains = [paired[sid]["sleep_consolidation"]["normalized_auc"]
                          - paired[sid]["replay_only"]["normalized_auc"]
                          for sid in cell_streams]
            cell_new_loss = [paired[sid]["replay_only"]["new_task_accuracy"]
                             - paired[sid]["sleep_consolidation"]["new_task_accuracy"]
                             for sid in cell_streams]
            cell_summary[f"{family}:{ratio}"] = {
                "sleep_minus_replay_auc": _bootstrap(
                    cell_gains, seed=BOOTSTRAP_SEED + int(ratio * 10) + FAMILIES.index(family)),
                "replay_minus_sleep_new_task_accuracy": _bootstrap(
                    cell_new_loss, seed=BOOTSTRAP_SEED + 100 + int(ratio * 10) + FAMILIES.index(family)),
                "stream_ids": cell_streams,
            }
            differences.extend(cell_gains)
            new_task_differences.extend(cell_new_loss)
    primary = _bootstrap(differences, seed=BOOTSTRAP_SEED)
    new_loss = _bootstrap(new_task_differences, seed=BOOTSTRAP_SEED + 1)
    controls = context["controls"]
    controls_pass = (len(controls) == sum(plan.get("controls_per_kind", 0)
                                          for _ in CONTROL_KINDS)
                     and all(row.get("status") == "PASS" for row in controls))
    if payload.get("split") == "heldout":
        success = (not failures and controls_pass and primary["mean"] is not None
                   and primary["mean"] >= PRIMARY_GAIN
                   and new_loss["mean"] is not None
                   and new_loss["mean"] <= MAX_NEW_TASK_LOSS)
        efficacy = {"status": "PASS" if success else "FAIL",
                    "minimum_gain": PRIMARY_GAIN,
                    "maximum_new_task_accuracy_loss": MAX_NEW_TASK_LOSS,
                    "primary_auc_gain": primary,
                    "new_task_accuracy_loss": new_loss,
                    "controls_pass": controls_pass}
    else:
        efficacy = {"status": "development_only", "primary_auc_gain": primary,
                    "new_task_accuracy_loss": new_loss,
                    "controls_pass": controls_pass}
    return {
        "phase": PHASE, "split": payload.get("split"),
        "analysis_status": "INVALID" if failures else "VALID",
        "structural_failures": failures, "stream_count": len(paired),
        "row_count": len(payload.get("streams", [])),
        "expected_row_count": len(context["expected_streams"]) * len(ARMS),
        "control_count": len(controls), "controls_by_kind": {
            kind: {"count": sum(row.get("kind") == kind for row in controls),
                   "passed": sum(row.get("kind") == kind and row.get("status") == "PASS"
                                 for row in controls)}
            for kind in CONTROL_KINDS},
        "primary": efficacy, "capacity_family_cells": cell_summary,
        "arm_means": {arm: (sum(row[arm]["normalized_auc"] for row in paired.values()
                                if arm in row) / max(1, sum(arm in row for row in paired.values())))
                      for arm in ARMS},
        "raw_payload_sha256": _sha(json.dumps(payload, sort_keys=True,
                                               separators=(",", ":"),
                                               ensure_ascii=False, default=str).encode()),
        "allocation_sha256": _digest(plan),
    }


def analyze(payload: dict) -> dict:
    return _analysis(payload)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    payload = json.loads(args.raw.read_text())
    result = analyze(payload)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    if result["analysis_status"] == "INVALID":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
