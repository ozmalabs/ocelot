"""Fail-closed analysis for the frozen P24 common-target transfer panel."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import subprocess
from collections import defaultdict
from pathlib import Path

ARMS = ("fresh", "compatible_source", "wrong_source", "same_target_map_work")
FAMILIES = ("heat_to_thermal", "lever_to_latch")
CONTROL_KINDS = ("duplicate_receipt", "stale_map", "wrong_source_map")
BOOTSTRAPS = 10_000
BOOTSTRAP_SEED = 24_2026
PRIMARY_GAIN = 0.10
ACCURACY_TOLERANCE = 0.02


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _auc(curve: list[dict]) -> float:
    if len(curve) != 3 or [x.get("target_interactions") for x in curve] != [0, 1, 2]:
        raise ValueError("curve must contain checkpoints 0, 1, 2")
    values = [x.get("success") for x in curve]
    if any(v not in (0, 1) or isinstance(v, bool) for v in values):
        raise ValueError("success values must be integer 0/1")
    return sum((values[i] + values[i + 1]) / 2 for i in range(2)) / 2


def _holm(pvalues: dict[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=pvalues.get)
    adjusted, running = {}, 0.0
    count = len(ordered)
    for rank, key in enumerate(ordered):
        running = max(running, min(1.0, (count - rank) * pvalues[key]))
        adjusted[key] = running
    return adjusted


def _primary_bootstrap(rows: list[dict], *, replicates=BOOTSTRAPS,
                       seed=BOOTSTRAP_SEED) -> dict:
    by_stream = defaultdict(dict)
    for row in rows:
        by_stream[row["stream_id"]][row["arm"]] = {
            "auc": row["normalized_auc"], "final": row["curve"][-1]["success"]}
    streams = sorted(by_stream)
    if not streams or any(set(by_stream[key]) != set(ARMS) for key in streams):
        raise ValueError("primary requires complete paired four-arm streams")

    def effect(sample: list[str], metric: str) -> float:
        means = {arm: sum(by_stream[s][arm][metric] for s in sample) / len(sample)
                 for arm in ARMS}
        return means["compatible_source"] - max(means["fresh"],
                                                 means["same_target_map_work"])

    observed = effect(streams, "auc")
    final_observed = effect(streams, "final")
    rng = random.Random(seed)
    samples = [[streams[rng.randrange(len(streams))] for _ in streams]
               for _ in range(replicates)]
    draws = [effect(sample, "auc") for sample in samples]
    final_draws = [effect(sample, "final") for sample in samples]
    ordered = sorted(draws)
    lower, upper = ordered[int(.005 * (replicates - 1))], ordered[int(.995 * (replicates - 1))]
    # One-sided cluster-bootstrap tail probability for positive gain.
    # Center the paired bootstrap distribution at the null before evaluating
    # a one-sided superiority tail; flat effects therefore yield p=1.
    p = (1 + sum(value - observed >= observed for value in draws)) / (replicates + 1)
    final_ordered = sorted(final_draws)
    final_lower = final_ordered[int(.005 * (replicates - 1))]
    final_upper = final_ordered[int(.995 * (replicates - 1))]
    return {"observed_gain": observed, "ci_99": [lower, upper],
            "final_accuracy_gain": final_observed,
            "final_accuracy_gain_ci_99": [final_lower, final_upper],
            "bootstrap_p_one_sided": p, "replicates": replicates,
            "seed": seed, "paired_world_clusters": len(streams)}


def analyze(payload: dict, *, preregistration: str | Path | None = None,
            bootstrap_replicates=BOOTSTRAPS) -> dict:
    failures = []
    heldout = payload.get("split") == "heldout"
    if payload.get("phase") != "linear-p24-v1":
        failures.append("phase_mismatch")
    if heldout:
        if payload.get("status") != "heldout_pending_analysis":
            failures.append("heldout_status_mismatch")
        if not preregistration:
            failures.append("heldout_preregistration_missing")
        else:
            path = Path(preregistration)
            try:
                freeze = json.loads(next(line[len("P24_FREEZE_JSON: "):]
                                         for line in path.read_text().splitlines()
                                         if line.startswith("P24_FREEZE_JSON: ")))
                if _sha(path.read_bytes()) != payload.get("preregistration_sha256"):
                    failures.append("preregistration_hash_mismatch")
                changed = subprocess.check_output(
                    ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
                    cwd=Path.cwd(), text=True).splitlines()
                relative = str(path.resolve().relative_to(Path.cwd().resolve()))
                if changed != [relative]:
                    failures.append("preregistration_not_standalone_head_commit")
                for key in ("runner_sha256", "analyzer_sha256", "source_bundle_sha256",
                            "loaded_extension_sha256", "build_receipt_sha256",
                            "profile_sha256", "profile_seed_bundle_sha256"):
                    if payload.get("provenance", {}).get(key) != freeze.get(key):
                        failures.append("frozen_provenance_mismatch:" + key)
                if payload.get("allocation_sha256") != freeze.get("heldout_allocation_sha256"):
                    failures.append("heldout_allocation_digest_mismatch")
                if freeze.get("primary") != {"metric": "normalized_learning_curve_auc",
                        "comparison": "compatible_minus_stronger_source_free",
                        "minimum_gain": PRIMARY_GAIN}:
                    failures.append("frozen_primary_mismatch")
                expected_acceptance = {
                    "maximum_final_accuracy_loss": ACCURACY_TOLERANCE,
                    "zero_receipt_loss_or_double_credit": True,
                    "confidence_level": 0.99,
                    "bootstrap_replicates": BOOTSTRAPS,
                    "bootstrap_seed_by_family": {"heat_to_thermal": BOOTSTRAP_SEED,
                                                  "lever_to_latch": BOOTSTRAP_SEED + 1},
                    "holm_alpha": 0.01, "controls_per_kind": 100,
                    "streams_per_family": 200}
                if freeze.get("acceptance") != expected_acceptance:
                    failures.append("frozen_acceptance_mismatch")
                if freeze.get("resource_limits") != allocation.get("resource_limits"):
                    failures.append("frozen_resource_limits_mismatch")
            except (OSError, StopIteration, ValueError, subprocess.SubprocessError):
                failures.append("preregistration_invalid")
    elif payload.get("heldout_accessed") is not False or payload.get("status") != "development_only":
        failures.append("development_access_status_invalid")

    allocation = payload.get("allocation", {})
    if allocation.get("arms") != list(ARMS) or allocation.get("families") != list(FAMILIES):
        failures.append("allocation_arm_or_family_mismatch")
    expected_streams = {x.get("stream_id"): x for x in allocation.get("streams", [])}
    if len(expected_streams) != len(allocation.get("streams", [])):
        failures.append("duplicate_allocated_stream")
    records = payload.get("streams", [])
    grouped = defaultdict(dict)
    for row in records:
        stream, arm = row.get("stream_id"), row.get("arm")
        if stream not in expected_streams or arm not in ARMS or arm in grouped[stream]:
            failures.append("unexpected_or_duplicate_stream_arm")
            continue
        grouped[stream][arm] = row
        try:
            recomputed = _auc(row.get("curve", []))
            if not math.isclose(recomputed, row.get("normalized_auc"), abs_tol=1e-12):
                failures.append("auc_mismatch:" + str(stream) + ":" + str(arm))
        except (TypeError, ValueError):
            failures.append("invalid_curve:" + str(stream) + ":" + str(arm))
        if row.get("status") != "complete":
            failures.append("incomplete_row:" + str(stream) + ":" + str(arm))
        if row.get("family") != expected_streams[stream].get("family"):
            failures.append("family_mismatch:" + str(stream))
        if row.get("target_actions") != 2:
            failures.append("target_action_count_mismatch:" + str(stream) + ":" + str(arm))
    if set(grouped) != set(expected_streams):
        failures.append("stream_allocation_incomplete")
    for stream, arms in grouped.items():
        if set(arms) != set(ARMS):
            failures.append("paired_arm_incomplete:" + str(stream))
            continue
        receipt_sets = {tuple(arms[arm].get("target_receipt_ids", [])) for arm in ARMS}
        target_ids = next(iter(receipt_sets), ())
        if len(receipt_sets) != 1 or len(target_ids) != 2 or len(set(target_ids)) != 2:
            failures.append("receipt_parity_failure:" + str(stream))
        signatures = {json.dumps(arms[arm].get("ordinary_evidence_signature", []),
                                sort_keys=True) for arm in ARMS}
        if len(signatures) != 1:
            failures.append("ordinary_evidence_parity_failure:" + str(stream))
        for arm in ARMS:
            row = arms[arm]
            evidence = row.get("ordinary_evidence_signature", [])
            if len(evidence) != 2 or {item.get("event_id") for item in evidence} != set(target_ids):
                failures.append("ordinary_support_credit_mismatch:" + str(stream) + ":" + arm)
            expected_source = 2 if arm in {"compatible_source", "wrong_source"} else 0
            expected_source_units = float(expected_source)
            expected_maps = 0 if arm == "fresh" else 2
            expected_verifications = 5 if arm in {"compatible_source", "wrong_source"} else 0
            expected_map_debits = 0 if arm == "fresh" else 2
            expected_budget_debits = 2 if arm == "fresh" else 4
            if (row.get("source_action_count") != expected_source
                    or row.get("source_information_units") != expected_source_units
                    or row.get("map_pair_count") != expected_maps
                    or row.get("map_verification_queries") != expected_verifications
                    or row.get("map_work_budget_debits") != expected_map_debits
                    or row.get("shared_budget_debits") != expected_budget_debits):
                failures.append("arm_exposure_or_work_mismatch:" + str(stream) + ":" + arm)
            transfer = row.get("transfer", {})
            if arm == "compatible_source" and (
                    transfer.get("map_status") != "verified"
                    or transfer.get("target_effect_status") != "verified"):
                failures.append("compatible_source_not_verified:" + str(stream))
            if arm == "wrong_source" and transfer.get("map_status") != "rejected":
                failures.append("wrong_source_not_rejected:" + str(stream))
            if arm in {"fresh", "same_target_map_work"} and (
                    transfer.get("map_status") != "not_attempted"
                    or row.get("source_information_units") != 0):
                failures.append("source_free_arm_leakage:" + str(stream) + ":" + arm)
            limits = allocation.get("resource_limits", {})
            if row.get("external_model_queries") != limits.get("external_model_queries"):
                failures.append("external_model_query_count_mismatch:" + str(stream) + ":" + arm)
            budget = row.get("shared_budget", {})
            if (budget.get("capacity") != limits.get("native_budget_capacity")
                    or budget.get("capacity_ceiling") != limits.get("native_budget_capacity_ceiling")
                    or budget.get("enabled") != 1.0
                    or not isinstance(budget.get("remaining"), (int, float))
                    or budget["remaining"] < 0):
                failures.append("shared_budget_record_mismatch:" + str(stream) + ":" + arm)
            if (row.get("native_rule_work", limits.get("native_rule_steps_per_learner", 0) + 1)
                    > limits.get("native_rule_steps_per_learner", 0)
                    or row.get("source_native_rule_work", limits.get("native_rule_steps_per_learner", 0) + 1)
                    > limits.get("native_rule_steps_per_learner", 0)
                    or row.get("graph", {}).get("bytes", limits.get("graph_bytes_per_target_learner", 0) + 1)
                    > limits.get("graph_bytes_per_target_learner", 0)):
                failures.append("resource_ceiling_exceeded:" + str(stream) + ":" + arm)
            if not isinstance(row.get("shared_stream_elapsed_seconds"), (int, float)):
                failures.append("elapsed_time_missing:" + str(stream) + ":" + arm)

    controls = payload.get("controls", [])
    expected_controls = {(x.get("kind"), x.get("control_id"))
                         for x in allocation.get("controls", [])}
    observed_controls = {(x.get("kind"), x.get("control_id")) for x in controls}
    if observed_controls != expected_controls or len(observed_controls) != len(controls):
        failures.append("control_allocation_mismatch")
    control_counts = {kind: sum(row.get("kind") == kind for row in controls)
                      for kind in CONTROL_KINDS}
    if any(row.get("status") != "PASS" for row in controls):
        failures.append("structural_control_failure")
    required_controls = allocation.get("controls_per_kind")
    if required_controls is not None and any(control_counts[kind] != required_controls
                                             for kind in CONTROL_KINDS):
        failures.append("control_count_mismatch")
    for row in records:
        if row.get("source_action_count", 0) < 0 or row.get("source_information_units", 0) < 0:
            failures.append("invalid_exposure_count")
        if row.get("shared_budget_debits", 0) < row.get("map_work_budget_debits", 0):
            failures.append("map_debits_exceed_shared_budget")

    primary = {}
    pvalues = {}
    for family in FAMILIES:
        family_rows = [row for row in records if row.get("family") == family]
        if not family_rows:
            failures.append("family_missing:" + family)
            continue
        try:
            result = _primary_bootstrap(family_rows, replicates=bootstrap_replicates,
                                        seed=BOOTSTRAP_SEED + FAMILIES.index(family))
            pvalues[family] = result["bootstrap_p_one_sided"]
            means = {arm: sum(r["normalized_auc"] for r in family_rows
                              if r["arm"] == arm) /
                     sum(r["arm"] == arm for r in family_rows) for arm in ARMS}
            final = {arm: sum(r["curve"][-1]["success"] for r in family_rows
                              if r["arm"] == arm) /
                     sum(r["arm"] == arm for r in family_rows) for arm in ARMS}
            result.update({"arm_mean_auc": means, "final_accuracy": final,
                           "stronger_source_free_arm": max(("fresh", "same_target_map_work"),
                               key=lambda arm: means[arm]),
                           "accuracy_loss_vs_stronger_source_free":
                               max(final["fresh"], final["same_target_map_work"])
                               - final["compatible_source"]})
            primary[family] = result
        except (ValueError, ZeroDivisionError, KeyError, TypeError):
            failures.append("primary_unavailable:" + family)
    adjusted = _holm(pvalues)
    for family, p_adj in adjusted.items():
        primary[family]["holm_p_adjusted"] = p_adj
        gain = primary[family]["observed_gain"]
        loss = primary[family]["accuracy_loss_vs_stronger_source_free"]
        primary[family]["efficacy_gate"] = (
            "PASS" if gain >= PRIMARY_GAIN and loss <= ACCURACY_TOLERANCE and p_adj < .01
            else "FAIL")

    valid = not failures
    return {"phase": "linear-p24-v1", "status": "PASS" if valid else "FAIL",
            "evidence_class": ("DEVELOPMENT_ONLY" if not heldout else
                               "HELDOUT" if valid else "HELDOUT_INVALID"),
            "primary_status": ("NOT_ESTIMATED" if not heldout else
                               "NOT_ESTABLISHED" if not valid else
                               "PASS" if all(x["efficacy_gate"] == "PASS"
                                             for x in primary.values()) else "FAIL"),
            "counts": {"streams": len(expected_streams), "arm_rows": len(records),
                       "controls": len(controls), "control_by_kind": control_counts},
            "primary_by_family": primary,
            "secondary_contrasts": _secondary(records), "failures": failures}


def _secondary(records: list[dict]) -> dict:
    output = {}
    for family in FAMILIES:
        rows = [x for x in records if x.get("family") == family]
        means = {arm: (sum(x["normalized_auc"] for x in rows if x["arm"] == arm) /
                       max(1, sum(x["arm"] == arm for x in rows))) for arm in ARMS}
        output[family] = {
            "wrong_source_minus_fresh_auc": means["wrong_source"] - means["fresh"],
            "same_target_map_work_minus_fresh_auc":
                means["same_target_map_work"] - means["fresh"],
            "compatible_source_minus_fresh_auc":
                means["compatible_source"] - means["fresh"],
            "all_rows_retained": True}
    return output


def self_check() -> dict:
    streams, records = [], []
    for family_index, family in enumerate(FAMILIES):
        for index in range(2):
            stream = f"p24-analyzer-selfcheck:{family}:{index}"
            streams.append({"family": family, "stream_id": stream})
            ids = [f"{stream}:target:{i}" for i in range(2)]
            signature = [{"event_id": event} for event in ids]
            for arm in ARMS:
                curve = [{"target_interactions": i, "success": int(i > 0)}
                         for i in range(3)]
                source_count = 2 if arm in {"compatible_source", "wrong_source"} else 0
                map_count = 0 if arm == "fresh" else 2
                verification_count = 5 if source_count else 0
                map_debits = 0 if arm == "fresh" else 2
                budget_debits = 2 if arm == "fresh" else 4
                records.append({"stream_id": stream, "family": family, "arm": arm,
                    "curve": curve, "normalized_auc": .75,
                    "target_receipt_ids": ids, "target_actions": 2,
                    "ordinary_evidence_signature": signature, "status": "complete",
                    "source_action_count": source_count,
                    "source_information_units": float(source_count),
                    "map_pair_count": map_count,
                    "map_verification_queries": verification_count,
                    "native_rule_work": 12, "source_native_rule_work": 12 if source_count else 0,
                    "external_model_queries": 0,
                    "graph": {"bytes": 60_000},
                    "shared_budget": {"enabled": 1.0, "remaining": 100 - budget_debits,
                                      "capacity": 16.0, "capacity_ceiling": 64.0},
                    "shared_stream_elapsed_seconds": .01,
                    "shared_budget_debits": budget_debits,
                    "map_work_budget_debits": map_debits,
                    "transfer": ({"map_status": "verified", "target_effect_status": "verified"}
                                 if arm == "compatible_source" else
                                 {"map_status": "rejected", "target_effect_status":
                                  "not_attempted_no_source_model"}
                                 if arm == "wrong_source" else
                                 {"map_status": "not_attempted"})})
    payload = {"phase": "linear-p24-v1", "split": "development",
        "status": "development_only", "heldout_accessed": False,
        "allocation": {"arms": list(ARMS), "families": list(FAMILIES),
            "streams": streams, "controls": [], "resource_limits": {
                    "external_model_queries": 0,
                "native_rule_steps_per_learner": 80_000,
                "graph_bytes_per_target_learner": 100_000,
                "native_budget_capacity": 16.0,
                "native_budget_capacity_ceiling": 64.0},
            "controls_per_kind": 0}, "streams": records, "controls": []}
    result = analyze(payload, bootstrap_replicates=100)
    if result["status"] != "PASS" or any(
            item["observed_gain"] != 0 for item in result["primary_by_family"].values()):
        raise AssertionError("flat P24 self-check must pass structure and report zero gain")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        if args.input:
            parser.error("--self-check cannot be combined with an input file")
        result = self_check()
    elif args.input:
        result = analyze(json.loads(args.input.read_text(encoding="utf-8")),
                         preregistration=args.preregistration)
    else:
        parser.error("input is required unless --self-check is supplied")
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded)
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
