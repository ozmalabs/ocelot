"""Fail-closed analysis for P27 scheduled cumulative-learning v1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from evaluation.process_mastery.cumulative_checkpoint_panel import world_allocation_digest
from evaluation.process_mastery.linear_p27_v1 import (
    ARMS, BASELINE_DRAWS, BOOTSTRAP_DRAWS, BOOTSTRAP_SEED, CHECKPOINTS, FAMILIES,
    HELDOUT_CONTROLS, MAX_ATTEMPTS_PER_TASK, MAX_GRAPH_BYTES,
    MAX_NATIVE_RULE_STEPS, MAX_SEARCH_ATTEMPTS, PHASE, TESTS_PER_FAMILY,
    SHARED_BUDGET, VALIDATION_PER_FAMILY, allocation, provenance,
)
from evaluation.process_mastery.scheduled_learning_checkpoints import (
    ScheduledLearningCheckpoint, verify_scheduled_checkpoint,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _holm(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values, key=lambda key: (values[key], key))
    running, out = 0.0, {}
    for index, key in enumerate(ordered):
        running = max(running, (len(ordered) - index) * values[key])
        out[key] = min(1.0, running)
    return out


def _quantile(values: list[float], alpha: float = 0.01) -> float:
    values = sorted(values)
    return values[max(0, math.ceil(alpha * len(values)) - 1)]


def _slope(values: list[float]) -> float:
    x = (0.0, 1.0, 2.0, 4.0)
    xbar = sum(x) / len(x)
    ybar = sum(values) / len(values)
    return sum((xi - xbar) * (yi - ybar) for xi, yi in zip(x, values)) / sum(
        (xi - xbar) ** 2 for xi in x)


def _validate_panel_rows(rows: list[dict], *, families: tuple[str, ...],
                         worlds_per_family: int, arms: tuple[str, ...],
                         checkpoints: tuple[str, ...], panel_name: str) -> list[str]:
    failures = []
    expected = worlds_per_family * len(families) * len(arms) * len(checkpoints)
    if len(rows) != expected:
        failures.append(f"{panel_name}_row_count:{len(rows)}!={expected}")
    seen = set()
    for row in rows:
        key = (row.get("family"), row.get("arm"), row.get("checkpoint"), row.get("world_id"))
        if key in seen:
            failures.append(f"{panel_name}_duplicate:{key}")
        seen.add(key)
        if row.get("family") not in families or row.get("arm") not in arms:
            failures.append(f"{panel_name}_unknown_stratum:{key}")
        if row.get("checkpoint") not in checkpoints:
            failures.append(f"{panel_name}_unknown_checkpoint:{key}")
        if row.get("score") not in {0, 1, None}:
            failures.append(f"{panel_name}_invalid_score:{key}")
        if row.get("prediction_missing") != (row.get("score") is None):
            failures.append(f"{panel_name}_missingness_mismatch:{key}")
    for family in families:
        ids = {row["world_id"] for row in rows if row.get("family") == family}
        for arm in arms:
            for checkpoint in checkpoints:
                actual = {row["world_id"] for row in rows
                    if row.get("family") == family and row.get("arm") == arm
                    and row.get("checkpoint") == checkpoint}
                if len(actual) != worlds_per_family or actual != ids:
                    failures.append(f"{panel_name}_unpaired_world_matrix:{family}:{arm}:{checkpoint}")
    return failures


def _paired_rows(rows: list[dict], family: str, candidate: str) -> dict[str, list[float]]:
    grouped: dict[tuple[str, str], dict[str, float]] = {}
    for row in rows:
        if row.get("family") != family or row.get("arm") not in {"frozen_ancestor", candidate}:
            continue
        score = 0.0 if row.get("score") is None else float(row["score"])
        key = (row["world_id"], row["checkpoint"])
        grouped.setdefault(key, {})[row["arm"]] = score
    matrices: dict[str, list[float]] = {}
    worlds = sorted({world for world, _cp in grouped})
    for world in worlds:
        values = []
        for checkpoint in CHECKPOINTS:
            pair = grouped.get((world, checkpoint), {})
            if set(pair) != {"frozen_ancestor", candidate}:
                raise ValueError(f"unpaired result for {family}/{candidate}/{world}/{checkpoint}")
            values.append(pair[candidate] - pair["frozen_ancestor"])
        matrices[world] = values
    return matrices


def _contrast(rows: list[dict], *, family: str, candidate: str,
              seed: int) -> dict:
    matrix = _paired_rows(rows, family, candidate)
    values = list(matrix.values())
    if not values:
        raise ValueError(f"no paired worlds for {family}/{candidate}")
    n = len(values)
    point_final = sum(row[-1] for row in values) / n
    point_slope = sum(_slope(row) for row in values) / n
    rng = random.Random(seed)
    final_draws, slope_draws = [], []
    for _ in range(BOOTSTRAP_DRAWS):
        sampled = [values[rng.randrange(n)] for _ in range(n)]
        final_draws.append(sum(row[-1] for row in sampled) / n)
        slope_draws.append(sum(_slope(row) for row in sampled) / n)
    final_lower = _quantile(final_draws)
    slope_lower = _quantile(slope_draws)
    p_final = (1 + sum(value <= 0 for value in final_draws)) / (BOOTSTRAP_DRAWS + 1)
    p_slope = (1 + sum(value <= 0 for value in slope_draws)) / (BOOTSTRAP_DRAWS + 1)
    return {"family": family, "candidate_arm": candidate,
        "ancestor_arm": "frozen_ancestor", "world_clusters": n,
        "paired_gain_by_checkpoint": [sum(row[index] for row in values) / n
            for index in range(len(CHECKPOINTS))],
        "final_gain": point_final, "checkpoint_slope": point_slope,
        "final_gain_one_sided_99_lower": final_lower,
        "checkpoint_slope_one_sided_99_lower": slope_lower,
        "final_gain_bootstrap_p_le_zero": p_final,
        "checkpoint_slope_bootstrap_p_le_zero": p_slope,
        "bootstrap_draws": BOOTSTRAP_DRAWS, "bootstrap_seed": seed,
        "bootstrap_unit": "paired_world_cluster"}


def analyze(raw_path: Path, *, allow_development: bool = False) -> dict:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    split = raw.get("split")
    if split == "development" and not allow_development:
        raise ValueError("development self-check requires --allow-development")
    failures = []
    if raw.get("phase") != PHASE or split not in {"development", "heldout"}:
        failures.append("wrong_phase_or_split")
    if split == "heldout" and (raw.get("status") != "heldout_pending_analysis"
                                or not raw.get("heldout_accessed")):
        failures.append("heldout_run_not_complete")
    if split == "development" and (raw.get("status") != "development_only"
                                    or raw.get("heldout_accessed")):
        failures.append("development_status_invalid")
    expected_plan = allocation(split)
    test_count = expected_plan["test_worlds_per_family"]
    validation_count = expected_plan["validation_worlds_per_family"]
    control_count = expected_plan["integrity_control_count"]
    if raw.get("allocation_plan") != expected_plan:
        failures.append("allocation_matrix_mismatch")
    if raw.get("allocation_plan", {}).get("allocation_sha256") != expected_plan["allocation_sha256"]:
        failures.append("allocation_digest_mismatch")
    try:
        current_provenance = provenance()
    except Exception as exc:
        current_provenance = None
        failures.append(f"provenance_unavailable:{type(exc).__name__}")
    if current_provenance is not None and raw.get("provenance") != current_provenance:
        failures.append("source_or_runtime_provenance_mismatch")

    training = raw.get("training_lineages", [])
    expected_lineages = len(FAMILIES) * len(ARMS)
    if len(training) != expected_lineages:
        failures.append(f"training_lineage_count:{len(training)}!={expected_lineages}")
    by_lineage = {(row.get("family"), row.get("arm")): row for row in training}
    if len(by_lineage) != len(training):
        failures.append("duplicate_training_lineage")
    checkpoint_maps = {}
    for family in FAMILIES:
        for arm in ARMS:
            lineage = by_lineage.get((family, arm))
            if lineage is None:
                failures.append(f"missing_lineage:{family}:{arm}")
                continue
            if lineage.get("approval_count") != 0 or lineage.get("world_receipt_count") != 0:
                failures.append(f"unauthorized_search_action:{family}:{arm}")
            baseline = lineage.get("baseline_receipts", [])
            baseline_ids = [row.get("event_id") for row in baseline]
            if (len(baseline) != len(BASELINE_DRAWS)
                    or any(not isinstance(event_id, str) or not event_id
                           for event_id in baseline_ids)
                    or len(set(baseline_ids)) != len(baseline_ids)
                    or any(row.get("status") != "observed"
                           or row.get("action_authorized") is not True
                           for row in baseline)):
                failures.append(f"baseline_receipt_integrity:{family}:{arm}")
            selection_rows = lineage.get("selection_rows", [])
            selected_ids = [row.get("receipt_event_id") for row in selection_rows
                            if row.get("receipt_event_id") is not None]
            all_event_ids = baseline_ids + selected_ids
            if (len(set(all_event_ids)) != len(all_event_ids)
                    or lineage.get("target_evidence_count") != len(all_event_ids)):
                failures.append(f"training_receipt_parity:{family}:{arm}")
            if lineage.get("budget_debited", 0) > SHARED_BUDGET:
                failures.append(f"shared_budget_ceiling:{family}:{arm}")
            if lineage.get("candidate_count", 0) > MAX_SEARCH_ATTEMPTS:
                failures.append(f"candidate_limit:{family}:{arm}")
            if lineage.get("native_rule_steps", 0) > MAX_NATIVE_RULE_STEPS:
                failures.append(f"native_rule_ceiling:{family}:{arm}")
            cps = lineage.get("checkpoints", [])
            if len(cps) != len(CHECKPOINTS):
                failures.append(f"checkpoint_count:{family}:{arm}")
                continue
            for index, checkpoint_data in enumerate(cps):
                try:
                    checkpoint = ScheduledLearningCheckpoint(**checkpoint_data)
                    valid = verify_scheduled_checkpoint(checkpoint)
                except Exception:
                    valid = False
                    checkpoint = None
                if not valid:
                    failures.append(f"checkpoint_hash_invalid:{family}:{arm}:{index}")
                    continue
                if checkpoint.arm != arm or checkpoint.checkpoint != CHECKPOINTS[index]:
                    failures.append(f"checkpoint_identity_mismatch:{family}:{arm}:{index}")
                if checkpoint.graph_bytes > MAX_GRAPH_BYTES:
                    failures.append(f"graph_ceiling:{family}:{arm}:{index}")
                if checkpoint.cumulative["native_rule_steps"] > MAX_NATIVE_RULE_STEPS:
                    failures.append(f"checkpoint_rule_ceiling:{family}:{arm}:{index}")
                checkpoint_maps[(family, arm, checkpoint.checkpoint)] = checkpoint
            if len(lineage.get("search_rows", [])) and arm not in {"process_search_only", "combined"}:
                failures.append(f"search_in_control_arm:{family}:{arm}")
            for row in lineage.get("search_rows", []):
                if row.get("attempts_added", 0) > MAX_ATTEMPTS_PER_TASK:
                    failures.append(f"per_task_search_ceiling:{family}:{arm}")
            expected_search_rows = (4 if arm in {"process_search_only", "combined"} else 0)
            if len(lineage.get("search_rows", [])) != expected_search_rows:
                failures.append(f"search_task_count:{family}:{arm}")

    test_rows = [dict(row, family=panel["family"])
        for panel in raw.get("panels", {}).get("test", [])
        for row in panel.get("rows", [])]
    validation_rows = [dict(row, family=panel["family"])
        for panel in raw.get("panels", {}).get("validation", [])
        for row in panel.get("rows", [])]
    failures.extend(_validate_panel_rows(test_rows, families=FAMILIES,
        worlds_per_family=test_count, arms=ARMS,
        checkpoints=CHECKPOINTS, panel_name="test"))
    failures.extend(_validate_panel_rows(validation_rows, families=FAMILIES,
        worlds_per_family=validation_count, arms=ARMS,
        checkpoints=("g3",), panel_name="validation"))
    for family in FAMILIES:
        worlds = raw.get("evaluation_worlds", {}).get(family, {})
        test_ids = {row.get("world_id") for row in worlds.get("test", [])}
        validation_ids = {row.get("world_id") for row in worlds.get("validation", [])}
        if len(test_ids) != test_count or len(validation_ids) != validation_count:
            failures.append(f"world_allocation_count:{family}")
        if test_ids & validation_ids:
            failures.append(f"test_validation_overlap:{family}")
        expected_hash = world_allocation_digest(worlds.get("test", []) +
                                                worlds.get("validation", []))
        if worlds.get("allocation_sha256") != expected_hash:
            failures.append(f"world_allocation_hash:{family}")

    for row in test_rows + validation_rows:
        prediction = row.get("prediction")
        if isinstance(prediction, dict):
            prediction = (prediction.get("expected_after_value")
                if prediction.get("status") == "predicted" else None)
        expected = row.get("expected_outcome")
        scored_prediction = (None if prediction is None else
            int(list(prediction) == list(expected)
                if isinstance(expected, (list, tuple)) else prediction == expected))
        if row.get("score") != scored_prediction:
            failures.append(
                f"prediction_score_mismatch:{row.get('family')}:{row.get('arm')}:"
                f"{row.get('checkpoint')}:{row.get('world_id')}")

    controls = raw.get("integrity_controls", [])
    if len(controls) != control_count:
        failures.append(f"integrity_control_count:{len(controls)}!={control_count}")
    if any(row.get("status") != "PASS" for row in controls):
        failures.append("integrity_control_failure")

    contrast_results = {}
    p_family = {}
    seed_index = 0
    for family in FAMILIES:
        for candidate in ("evidence_selection_only", "process_search_only", "combined"):
            result = _contrast(test_rows, family=family, candidate=candidate,
                               seed=BOOTSTRAP_SEED + seed_index)
            seed_index += 1
            contrast_results[f"{family}:{candidate}"] = result
            p_family[f"{family}:{candidate}:final"] = result["final_gain_bootstrap_p_le_zero"]
            p_family[f"{family}:{candidate}:slope"] = result["checkpoint_slope_bootstrap_p_le_zero"]
    adjusted = _holm(p_family)
    for key, result in contrast_results.items():
        result["holm_adjusted_p"] = {
            "final_gain": adjusted[f"{key}:final"],
            "checkpoint_slope": adjusted[f"{key}:slope"]}
        result["registered_gate_pass"] = bool(
            result["final_gain"] >= 0.10 and result["checkpoint_slope"] >= 0.05
            and result["final_gain_one_sided_99_lower"] > 0
            and result["checkpoint_slope_one_sided_99_lower"] > 0
            and adjusted[f"{key}:final"] < 0.01
            and adjusted[f"{key}:slope"] < 0.01)
    primary = {key: contrast_results[f"{key}:combined"] for key in FAMILIES}
    floor_ceiling = {}
    for arm in ARMS:
        arm_rows = [row for row in test_rows if row.get("arm") == arm and row.get("checkpoint") == "g3"]
        floor_ceiling[arm] = {"n": len(arm_rows),
            "successes": sum(row.get("score") == 1 for row in arm_rows),
            "missing": sum(row.get("prediction_missing") for row in arm_rows),
            "accuracy": (sum(row.get("score") == 1 for row in arm_rows) /
                         len(arm_rows) if arm_rows else None)}
    resource_rows = []
    for lineage in training:
        for checkpoint in lineage.get("checkpoints", []):
            counter = checkpoint.get("cumulative", {})
            resource_rows.append({"family": lineage["family"], "arm": lineage["arm"],
                "checkpoint": checkpoint.get("checkpoint"),
                "primitive_work": counter.get("primitive_work"),
                "source_exposure": counter.get("source_exposure"),
                "native_rule_steps": counter.get("native_rule_steps"),
                "graph_bytes": counter.get("graph_bytes"),
                "budget_debits": counter.get("budget_debits"),
                "task_world_accesses": counter.get("task_world_accesses"),
                "interval_status": checkpoint.get("interval_status")})
    return {"phase": PHASE, "split": split,
        "raw_path": str(raw_path.relative_to(ROOT)), "raw_sha256": _sha(raw_path),
        "structural_status": "VALID" if not failures else "INVALID",
        "structural_failures": failures,
        "runtime_attestation": (current_provenance or {}).get("runtime_attestation"),
        "n_test_rows": len(test_rows), "n_validation_rows": len(validation_rows),
        "missing_test_predictions": sum(row.get("prediction_missing") for row in test_rows),
        "validation_summary": {
            arm: {"n": sum(row.get("arm") == arm for row in validation_rows),
                "successes": sum(row.get("arm") == arm and row.get("score") == 1
                                  for row in validation_rows),
                "missing": sum(row.get("arm") == arm and row.get("prediction_missing")
                                for row in validation_rows)} for arm in ARMS},
        "final_checkpoint_summary": floor_ceiling,
        "primary": {"estimand": "paired combined minus frozen ancestor at g3 and slope over g0-g3",
            "minimum_final_gain": 0.10, "minimum_checkpoint_slope": 0.05,
            "contrasts": primary, "holm_adjusted_p": adjusted,
            "phase_gate_pass": bool(split == "heldout" and all(
                result["registered_gate_pass"] for result in primary.values()) and not failures)},
        "component_contrasts": contrast_results,
        "resource_strata": resource_rows,
        "integrity_controls": {"count": len(controls),
            "status_counts": {status: sum(row.get("status") == status for row in controls)
                for status in ("PASS", "FAIL")},
            "kind_counts": {kind: sum(row.get("kind") == kind for row in controls)
                for kind in ("heldout_selector_guard", "receipt_replay", "approval_boundary")}},
        "claim_limit": "finite simulator evidence only; no broad recursive-improvement or human-equivalence claim"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-development", action="store_true")
    args = parser.parse_args()
    raw_path = args.raw if args.raw.is_absolute() else ROOT / args.raw
    report = analyze(raw_path, allow_development=args.allow_development)
    output = args.output or raw_path.with_name(raw_path.stem + "_analysis.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(json.dumps(report, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, default=str) + "\n")
    tmp.replace(output)
    print(json.dumps({"status": report["structural_status"],
        "structural_failures": len(report["structural_failures"]),
        "analysis_path": str(output), "primary_gate_pass": report["primary"]["phase_gate_pass"]},
        sort_keys=True))
    return 0 if report["structural_status"] == "VALID" else 2


if __name__ == "__main__":
    raise SystemExit(main())
