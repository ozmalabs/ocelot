"""Frozen P26 structural analyzer and paired selector efficacy analysis."""
from __future__ import annotations

import argparse
from collections import defaultdict
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.process_mastery.linear_p26_v1 import (
    ARMS, BOOTSTRAPS, BOOTSTRAP_SEED, CHECKPOINTS, CONTROL_KINDS,
    GRAPH_BYTES_LIMIT, HELDOUT_STREAMS_PER_CELL, NATIVE_RULE_STEPS_LIMIT,
    NATIVE_SEARCH_ATTEMPT_LIMIT, PHASE, SHARED_BUDGET, allocation,
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = int(math.floor(position)), int(math.ceil(position))
    if low == high:
        return ordered[low]
    weight = position - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def _auc(curve: list[dict[str, Any]]) -> float:
    if [int(row["cumulative_selection_work"]) for row in curve] != list(CHECKPOINTS):
        raise ValueError("P26 curve must contain every fixed selection-work checkpoint")
    xs = [float(row["cumulative_selection_work"]) for row in curve]
    ys = [float(bool(row["success"])) for row in curve]
    width = xs[-1] - xs[0]
    return sum((xs[i] - xs[i - 1]) * (ys[i] + ys[i - 1]) / 2.0
               for i in range(1, len(xs))) / width


def _bootstrap(values: list[float], *, seed: int, reps: int = BOOTSTRAPS) -> dict:
    if not values:
        return {"mean": None, "ci99": [None, None], "n": 0}
    rng = random.Random(seed)
    n = len(values)
    means = [sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps)]
    return {"mean": sum(values) / n,
        "ci99": [_percentile(means, .005), _percentile(means, .995)],
        "n": n, "bootstrap_replicates": reps, "bootstrap_seed": seed}


def _bootstrap_stronger_control(paired: list[dict[str, float]], *, seed: int,
                                reps: int = BOOTSTRAPS) -> dict:
    """Paired cluster bootstrap with the stronger control reselected per draw."""
    if not paired:
        return {"mean": None, "ci99": [None, None], "n": 0}
    rng = random.Random(seed)
    n = len(paired)
    def gain(indices):
        means = {arm: sum(paired[index][arm] for index in indices) / len(indices)
                 for arm in ARMS}
        return means["residual"] - max(means["fixed"], means["random"])
    values = [gain([rng.randrange(n) for _ in range(n)]) for _ in range(reps)]
    observed = gain(list(range(n)))
    return {"mean": observed,
        "ci99": [_percentile(values, .005), _percentile(values, .995)],
        "n": n, "bootstrap_replicates": reps, "bootstrap_seed": seed,
        "stronger_control_reselected_per_resample": True}


def _randomization_p(differences: list[float], *, seed: int,
                     reps: int = BOOTSTRAPS) -> float:
    observed = sum(differences) / len(differences)
    rng = random.Random(seed)
    extreme = 0
    for _ in range(reps):
        statistic = sum(value if rng.getrandbits(1) else -value
                        for value in differences) / len(differences)
        if statistic >= observed - 1e-15:
            extreme += 1
    return (extreme + 1) / (reps + 1)


def _holm(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda row: row[1])
    adjusted = {}
    running = 0.0
    count = len(ordered)
    for rank, (name, pvalue) in enumerate(ordered):
        running = max(running, min(1.0, (count - rank) * pvalue))
        adjusted[name] = running
    return adjusted


def _validate(payload: dict) -> tuple[list[str], dict]:
    failures = []
    plan = payload.get("allocation_plan", {})
    expected_plan = allocation(payload.get("split", ""),
        streams_per_cell=plan.get("streams_per_family_load_cell"),
        controls_per_kind=plan.get("controls_per_kind"))
    if plan != expected_plan:
        failures.append("allocation_plan_mismatch")
    if payload.get("phase") != PHASE:
        failures.append("phase_mismatch")
    split = payload.get("split")
    expected_status = "heldout_pending_analysis" if split == "heldout" else "development_only"
    if payload.get("status") != expected_status:
        failures.append("payload_status_mismatch")
    if payload.get("heldout_accessed") is not (split == "heldout"):
        failures.append("heldout_access_flag_mismatch")
    attestation = (payload.get("provenance") or {}).get("runtime_attestation") or {}
    if attestation.get("status") != "ATTESTED" or not attestation.get("native_symbols_bound"):
        failures.append("runtime_attestation_not_valid")

    expected_streams = {}
    for cell in plan.get("stream_cells", []):
        for stream_id in cell.get("stream_ids", []):
            expected_streams[stream_id] = {"family": cell["family"],
                "load_stratum": cell["load_stratum"], "pool_size": cell["pool_size"]}
    observed = {}
    for stream in payload.get("streams", []):
        stream_id = stream.get("stream_id")
        if stream_id not in expected_streams or stream_id in observed:
            failures.append(f"unexpected_or_duplicate_stream:{stream_id}")
            continue
        observed[stream_id] = stream
        expected = expected_streams[stream_id]
        for key, value in expected.items():
            if stream.get(key) != value:
                failures.append(f"stream_stratum_mismatch:{stream_id}:{key}")
        arms = {row.get("arm"): row for row in stream.get("arms", [])}
        if set(arms) != set(ARMS) or len(stream.get("arms", [])) != len(ARMS):
            failures.append(f"selector_arm_set_mismatch:{stream_id}")
            continue
        pools = {arms[arm].get("train_pool_sha256") for arm in ARMS}
        pool_ids = {arms[arm].get("train_pool_id") for arm in ARMS}
        available = {tuple(arms[arm].get("available_opportunity_ids", ())) for arm in ARMS}
        if len(pools) != 1 or len(pool_ids) != 1 or len(available) != 1:
            failures.append(f"selector_pool_identity_mismatch:{stream_id}")
        for arm in ARMS:
            row = arms[arm]
            if row.get("status") != "complete":
                failures.append(f"incomplete_selector_row:{stream_id}:{arm}")
            if len(row.get("curve", [])) != len(CHECKPOINTS):
                failures.append(f"curve_checkpoint_count:{stream_id}:{arm}")
            for point in row.get("curve", []):
                if point.get("split") != "heldout" or point.get("status") != "scored":
                    failures.append(f"test_curve_provenance:{stream_id}:{arm}")
                if point.get("prediction_missing") != (point.get("prediction") is None):
                    failures.append(f"prediction_missing_flag:{stream_id}:{arm}")
            try:
                area = _auc(row["curve"])
                if not math.isclose(area, row.get("normalized_auc", area), abs_tol=1e-12):
                    failures.append(f"auc_record_mismatch:{stream_id}:{arm}")
            except (ValueError, KeyError, TypeError):
                failures.append(f"invalid_curve:{stream_id}:{arm}")
            available_ids = set(row.get("available_opportunity_ids", ()))
            selected_ids = row.get("selected_opportunity_ids", ())
            if not set(selected_ids).issubset(available_ids):
                failures.append(f"selected_outside_pool:{stream_id}:{arm}")
            if row.get("source_exposures") != 0:
                failures.append(f"unexpected_source_exposure:{stream_id}:{arm}")
            if row.get("graph_serialized_bytes", GRAPH_BYTES_LIMIT + 1) > GRAPH_BYTES_LIMIT:
                failures.append(f"selector_graph_bytes_ceiling:{stream_id}:{arm}")
            if row.get("native_rule_steps", NATIVE_RULE_STEPS_LIMIT + 1) > NATIVE_RULE_STEPS_LIMIT:
                failures.append(f"selector_rule_step_ceiling:{stream_id}:{arm}")
            if len(row.get("baseline_receipts", ())) != 3:
                failures.append(f"baseline_receipt_count:{stream_id}:{arm}")
            baseline_ids = [receipt.get("event_id") for receipt in row.get("baseline_receipts", ())]
            if any(not event_id for event_id in baseline_ids) or len(set(baseline_ids)) != 3:
                failures.append(f"baseline_receipt_identity:{stream_id}:{arm}")
            if row.get("selection_receipts", 0) > plan.get("selector_selection_limit", -1):
                failures.append(f"selection_receipt_ceiling:{stream_id}:{arm}")
            delivered = [selection for selection in row.get("selection_rows", ())
                         if selection.get("receipt_event_id")]
            if len(delivered) != row.get("selection_receipts"):
                failures.append(f"selection_receipt_conservation:{stream_id}:{arm}")
            if len({selection.get("receipt_event_id") for selection in delivered}) != len(delivered):
                failures.append(f"selection_receipt_duplicate:{stream_id}:{arm}")
            request_cost = sum(float(selection.get("budget_request", {}).get("cost", 0.0))
                for selection in delivered)
            if not math.isclose(request_cost, row.get("selection_budget_debited", -1.0),
                    rel_tol=0.0, abs_tol=1e-9):
                failures.append(f"selector_budget_request_conservation:{stream_id}:{arm}")
            all_approved_cost = sum(float(request.get("cost", 0.0))
                for request in row.get("budget_requests", ())
                if request.get("status") == "approved")
            if not math.isclose(all_approved_cost, row.get("budget_debited", -1.0),
                    rel_tol=0.0, abs_tol=1e-9):
                failures.append(f"selector_total_request_conservation:{stream_id}:{arm}")
            if row.get("budget_remaining", -1) < 0 or row.get("budget_remaining", SHARED_BUDGET + 1) > SHARED_BUDGET:
                failures.append(f"selector_shared_budget:{stream_id}:{arm}")
            required_selector_seeds = {"process_induction", "target_learning",
                "common_target_evidence", "useful_evidence_selection"}
            if not required_selector_seeds.issubset(set(row.get("loaded_seed_ids", ()))):
                failures.append(f"selector_seed_closure:{stream_id}:{arm}")
            if not math.isclose(row.get("budget_debited", -1.0),
                    SHARED_BUDGET - row.get("budget_remaining", SHARED_BUDGET + 1),
                    rel_tol=0.0, abs_tol=1e-9):
                failures.append(f"selector_budget_reconciliation:{stream_id}:{arm}")
        pool_world_ids = set()
        for arm in stream.get("arms", ()):
            pool_world_ids.update(opportunity.split(":act:", 1)[0]
                for opportunity in arm.get("available_opportunity_ids", ()))
        search = stream.get("native_search", {})
        if search.get("status") != "complete":
            failures.append(f"native_search_missing:{stream_id}")
        if (search.get("training_pool_id") != stream.get("train_pool_id")
                or search.get("training_pool_sha256") != stream.get("train_pool_sha256")
                or len(search.get("task_world_ids", ())) != stream.get("pool_size")):
            failures.append(f"native_search_pool_identity_mismatch:{stream_id}")
        if set(search.get("task_world_ids", ())) != pool_world_ids:
            failures.append(f"native_search_task_world_mismatch:{stream_id}")
        if search.get("attempts", NATIVE_SEARCH_ATTEMPT_LIMIT + 1) > NATIVE_SEARCH_ATTEMPT_LIMIT:
            failures.append(f"native_search_attempt_ceiling:{stream_id}")
        if sum((search.get("attempt_statuses") or {}).values()) != search.get("attempts"):
            failures.append(f"native_search_attempt_conservation:{stream_id}")
        attempt_records = search.get("attempt_records", ())
        attempt_statuses = Counter(row.get("status") for row in attempt_records)
        if len(attempt_records) != search.get("attempts") or dict(attempt_statuses) != search.get("attempt_statuses"):
            failures.append(f"native_search_attempt_records_incomplete:{stream_id}")
        per_task_attempts = Counter()
        for attempt in attempt_records:
            worlds = attempt.get("task_world_ids", ())
            if (len(worlds) != 1 or worlds[0] not in pool_world_ids
                    or not attempt.get("node_id") or not attempt.get("expression_key")
                    or attempt.get("params") is None or attempt.get("effect_digest") is None
                    or not attempt.get("operator_kind")):
                failures.append(f"native_search_attempt_provenance_incomplete:{stream_id}")
                continue
            per_task_attempts[worlds[0]] += 1
        if any(count > plan.get("native_search_per_task_limit", -1)
               for count in per_task_attempts.values()):
            failures.append(f"native_search_per_task_ceiling:{stream_id}")
        candidate_records = search.get("candidate_records", ())
        if len(candidate_records) != search.get("candidate_proposals"):
            failures.append(f"native_search_candidate_records_incomplete:{stream_id}")
        for candidate in candidate_records:
            if (not candidate.get("node_id") or not candidate.get("expression_key")
                    or not candidate.get("expression_digest")
                    or candidate.get("expression_tree") is None
                    or candidate.get("params") is None
                    or candidate.get("effect_digest") is None
                    or not candidate.get("derivation_attempt_ids")):
                failures.append(f"native_search_candidate_provenance_incomplete:{stream_id}")
            if any(attempt_id not in {row.get("node_id") for row in attempt_records}
                   for attempt_id in candidate.get("derivation_attempt_ids", ())):
                failures.append(f"native_search_candidate_attempt_link:{stream_id}")
        gate_probe = search.get("candidate_gate_probe", {})
        if candidate_records and (gate_probe.get("status") != "ABSTAIN"
                or gate_probe.get("reason") != "candidate_not_adopted"
                or gate_probe.get("authorize_calls") != 0
                or gate_probe.get("world_transition_calls") != 0):
            failures.append(f"native_search_candidate_approval_guard:{stream_id}")
        if not candidate_records and gate_probe.get("status") != "NO_CANDIDATE":
            failures.append(f"native_search_candidate_probe_malformed:{stream_id}")
        if search.get("adoption_approvals") != 0 or search.get("world_receipts") != 0:
            failures.append(f"native_search_approval_boundary:{stream_id}")
        if search.get("graph_serialized_bytes", GRAPH_BYTES_LIMIT + 1) > GRAPH_BYTES_LIMIT:
            failures.append(f"search_graph_bytes_ceiling:{stream_id}")
        if search.get("native_rule_steps", NATIVE_RULE_STEPS_LIMIT + 1) > NATIVE_RULE_STEPS_LIMIT:
            failures.append(f"search_rule_step_ceiling:{stream_id}")
        required_search_seeds = {"open_process_search", "process_solving", "thinking_budget"}
        if not required_search_seeds.issubset(set(search.get("loaded_seed_ids", ()))):
            failures.append(f"native_search_seed_closure:{stream_id}")
        if not math.isclose(search.get("budget_debited", -1.0),
                SHARED_BUDGET - search.get("budget_remaining", SHARED_BUDGET + 1),
                rel_tol=0.0, abs_tol=1e-9):
            failures.append(f"native_search_budget_reconciliation:{stream_id}")
    if set(observed) != set(expected_streams):
        failures.append("stream_allocation_incomplete")
    controls = payload.get("integrity_controls", [])
    for kind in CONTROL_KINDS:
        rows = [row for row in controls if row.get("kind") == kind]
        if len(rows) != plan.get("controls_per_kind"):
            failures.append(f"control_count:{kind}")
        if any(row.get("status") != "PASS" for row in rows):
            failures.append(f"control_failure:{kind}")
        if kind == "receipt_replay":
            for row in rows:
                if (row.get("replay_added_exposure") is not False
                        or row.get("evidence_count_before") != row.get("evidence_count_after")
                        or row.get("observations_before") != row.get("observations_after")
                        or row.get("replay_disposition") != "deduplicated"):
                    failures.append("receipt_replay_changed_exposure")
        elif kind == "approval_boundary":
            for row in rows:
                probe = row.get("candidate_gate_probe", {})
                if row.get("adoption_approvals") != 0 or row.get("world_receipts") != 0:
                    failures.append("approval_boundary_side_effect")
                if row.get("probe_scope") == "candidate_execution_denied":
                    if (probe.get("status") != "ABSTAIN"
                            or probe.get("reason") != "candidate_not_adopted"
                            or probe.get("authorize_calls") != 0
                            or probe.get("world_transition_calls") != 0):
                        failures.append("approval_boundary_probe_failed")
                elif row.get("probe_scope") == "no_candidate_available":
                    if row.get("candidate_proposals") != 0 or probe.get("status") != "NO_CANDIDATE":
                        failures.append("approval_boundary_candidate_absent_misreported")
                else:
                    failures.append("approval_boundary_scope_missing")
    return failures, {"streams": observed, "expected_streams": expected_streams,
                      "controls": controls}


def _analysis(payload: dict) -> dict:
    failures, context = _validate(payload)
    cells = {}
    grouped = defaultdict(list)
    for stream_id, stream in context["streams"].items():
        grouped[(stream["family"], stream["load_stratum"])].append(stream)
    for cell_index, ((family, load), streams) in enumerate(sorted(grouped.items())):
        arm_aucs = {arm: [] for arm in ARMS}
        paired = []
        missing = {arm: 0 for arm in ARMS}
        for stream in streams:
            rows = {row["arm"]: row for row in stream["arms"]}
            for arm in ARMS:
                auc = _auc(rows[arm]["curve"])
                arm_aucs[arm].append(auc)
                missing[arm] += sum(bool(point.get("prediction_missing"))
                                    for point in rows[arm]["curve"])
            paired.append({arm: _auc(rows[arm]["curve"]) for arm in ARMS})
        cell_name = f"{family}:{load}"
        means = {arm: sum(values) / len(values) if values else None
                 for arm, values in arm_aucs.items()}
        pairwise = {}
        for control_index, control in enumerate(("fixed", "random")):
            diffs = [row["residual"] - row[control] for row in paired]
            p_value = _randomization_p(diffs,
                seed=BOOTSTRAP_SEED + 100_000 + cell_index * 100 + control_index)
            pairwise[control] = {"gain": _bootstrap(diffs,
                seed=BOOTSTRAP_SEED + 200_000 + cell_index * 100 + control_index + 10),
                "one_sided_randomization_p_unadjusted_secondary": p_value}
        stronger_control = max(means["fixed"], means["random"])
        cells[cell_name] = {"n_streams": len(streams), "mean_auc": means,
            "residual_minus_stronger_fixed_or_random": means["residual"] - stronger_control,
            "pairwise_contrasts": pairwise,
            "all_floor_rate": {arm: sum(value == 0 for value in values) / len(values)
                               for arm, values in arm_aucs.items()},
            "all_ceiling_rate": {arm: sum(value == 1 for value in values) / len(values)
                                 for arm, values in arm_aucs.items()},
            "missing_predictions_by_arm": missing,
            "selector_resources": {
                arm: {
                    "mean_selection_receipts": sum(row["selection_receipts"] for row in
                        (next(item for item in stream["arms"] if item["arm"] == arm)
                         for stream in streams)) / len(streams),
                    "total_budget_debited": sum(next(item for item in stream["arms"]
                        if item["arm"] == arm)["budget_debited"] for stream in streams),
                    "max_graph_serialized_bytes": max(next(item for item in stream["arms"]
                        if item["arm"] == arm)["graph_serialized_bytes"] for stream in streams),
                    "max_native_rule_steps": max(next(item for item in stream["arms"]
                        if item["arm"] == arm)["native_rule_steps"] for stream in streams),
                    "total_source_exposures": sum(next(item for item in stream["arms"]
                        if item["arm"] == arm)["source_exposures"] for stream in streams),
                } for arm in ARMS},
            "native_search": {
                "attempts": sum(stream["native_search"]["attempts"] for stream in streams),
                "attempt_status_counts": dict(sum((Counter(stream["native_search"]["attempt_statuses"])
                    for stream in streams), Counter())),
                "unique_verified_effects": sum(stream["native_search"]["unique_verified_effects"]
                    for stream in streams),
                "candidate_proposals": sum(stream["native_search"]["candidate_proposals"]
                    for stream in streams),
                "candidate_status_counts": dict(sum((Counter(candidate.get("status")
                    for candidate in stream["native_search"].get("candidate_records", ()))
                    for stream in streams), Counter())),
                "adoption_approvals": sum(stream["native_search"]["adoption_approvals"]
                    for stream in streams),
                "world_receipts": sum(stream["native_search"]["world_receipts"]
                    for stream in streams),
                "unseen_binding_use": sum(stream["native_search"]["unseen_binding_use"]
                    for stream in streams),
                "unspent_budget": sum(stream["native_search"]["budget_remaining"]
                    for stream in streams),
                "max_graph_serialized_bytes": max(stream["native_search"]["graph_serialized_bytes"]
                    for stream in streams),
                "max_native_rule_steps": max(stream["native_search"]["native_rule_steps"]
                    for stream in streams)}}
    paired_all = []
    for stream in context["streams"].values():
        rows = {row["arm"]: row for row in stream["arms"]}
        paired_all.append({arm: _auc(rows[arm]["curve"]) for arm in ARMS})
    global_means = {arm: sum(row[arm] for row in paired_all) / len(paired_all)
                    for arm in ARMS} if paired_all else {arm: None for arm in ARMS}
    primary_p_values = {}
    primary_pairwise = {}
    for control_index, control in enumerate(("fixed", "random")):
        differences = [row["residual"] - row[control] for row in paired_all]
        name = f"residual_minus_{control}"
        primary_p_values[name] = _randomization_p(differences,
            seed=BOOTSTRAP_SEED + control_index)
        primary_pairwise[control] = {"gain": _bootstrap(differences,
            seed=BOOTSTRAP_SEED + 10 + control_index),
            "one_sided_randomization_p": primary_p_values[name]}
    primary_gain = _bootstrap_stronger_control(paired_all, seed=BOOTSTRAP_SEED + 20)
    holm_adjusted = _holm(primary_p_values)
    for control, contrast in primary_pairwise.items():
        contrast["holm_adjusted_p"] = holm_adjusted[f"residual_minus_{control}"]
    primary_pass = (not failures and primary_gain["mean"] is not None
        and primary_gain["mean"] >= .10
        and primary_gain["ci99"][0] > 0
        and all(value < .01 for value in holm_adjusted.values()))
    return {"phase": PHASE, "split": payload.get("split"),
        "structural_status": "VALID" if not failures else "INVALID",
        "structural_failures": failures, "n_streams": len(context["streams"]),
        "cells": cells,
        "primary": {"estimand": "pooled paired residual AUC minus stronger fixed/random selector",
            "mean_auc": global_means, "gain_reselected_stronger_control": primary_gain,
            "pairwise_residual_minus_control": primary_pairwise,
            "holm_adjusted_one_sided_p": holm_adjusted,
            "minimum_gain": .10, "registered_gate_pass": primary_pass},
        "runtime_attestation": (payload.get("provenance") or {}).get("runtime_attestation"),
        "claim_limit": "finite simulator evidence only; no general process synthesis or human-equivalence claim"}


def analyze_file(path: Path) -> dict:
    raw = path.read_bytes()
    payload = json.loads(raw)
    return {"raw_path": str(path), "raw_sha256": _sha(raw), **_analysis(payload)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze_file(args.raw)
    output = args.output or args.raw.with_name(args.raw.stem + "_analysis.json")
    if output.exists():
        parser.error("refusing to overwrite an existing P26 analysis")
    raw = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    output.write_text(raw, encoding="utf-8")
    print(json.dumps({"output": str(output), "status": result["structural_status"],
                      "failures": result["structural_failures"]}, sort_keys=True))
    return 0 if result["structural_status"] == "VALID" else 2


if __name__ == "__main__":
    raise SystemExit(main())
