"""Preregistered paired family analysis for the P28.14 raw panel."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from evaluation.ousiometrics.behavior_panel import CONTROL_ARMS, PRIMARY_ARMS

FAMILIES = ("tool_intervention", "social_request_repair")
BOOTSTRAP_REPLICATES = 10_000
PERMUTATION_REPLICATES = 100_000
SEED = 28_202_614
SAFETY_NONINFERIORITY_MARGIN = 0.02
MEAN_BENEFIT_MARGIN = 0.10


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=lambda key: pvalues[key])
    result = {}
    running = 0.0
    count = len(ordered)
    for rank, key in enumerate(ordered):
        adjusted = min(1.0, (count - rank) * float(pvalues[key]))
        running = max(running, adjusted)
        result[key] = running
    return result


def _index_rows(payload: dict) -> dict[tuple[str, str, int], dict]:
    indexed = {}
    for row in payload.get("rows", ()):
        key = (str(row.get("world_family")), str(row.get("frame_id")), int(row.get("seed", -1)))
        if key in indexed:
            raise ValueError(f"duplicate paired result row: {key}")
        indexed[key] = row
    return indexed


def analyze(payload: dict, *, bootstrap_replicates: int = BOOTSTRAP_REPLICATES,
            permutation_replicates: int = PERMUTATION_REPLICATES,
            random_seed: int = SEED) -> dict:
    if payload.get("schema") != "p28_ousiometric_raw_v1":
        raise ValueError("unexpected raw result schema")
    indexed = _index_rows(payload)
    arms = PRIMARY_ARMS + CONTROL_ARMS
    expected_by_family = {}
    for family in FAMILIES:
        seeds = sorted({key[2] for key in indexed if key[0] == family})
        if not seeds:
            raise ValueError(f"registered world family missing: {family}")
        for arm in arms:
            found = {key[2] for key in indexed if key[0] == family and key[1] == arm}
            if found != set(seeds):
                raise ValueError(f"arm coverage mismatch for {family}/{arm}")
            for seed in seeds:
                row = indexed[(family, arm, seed)]
                if (row.get("heldout_used_for_selection") is not False
                        or len(row.get("checkpoints", ())) != 4
                        or len(row.get("learning_curve", ())) != 4):
                    raise ValueError(f"incomplete or contaminated row: {family}/{arm}/{seed}")
                if not all("goal_satisfied" in checkpoint
                           and "failed_or_abstained_actions" in checkpoint
                           for checkpoint in row["checkpoints"]):
                    raise ValueError("success-conditioned or incomplete checkpoint row")
        expected_by_family[family] = seeds

    if bootstrap_replicates < 1 or permutation_replicates < 1:
        raise ValueError("resampling counts must be positive")
    rng = np.random.default_rng(random_seed)
    permutation_rng = np.random.default_rng(random_seed ^ 0x5A17)
    raw_p = {}
    comparisons = {}
    arm_summaries = {}
    for family in FAMILIES:
        seeds = expected_by_family[family]
        treated, comparator = PRIMARY_ARMS[1], PRIMARY_ARMS[0]
        differences = np.asarray([
            float(indexed[(family, treated, seed)]["learning_auc"])
            - float(indexed[(family, comparator, seed)]["learning_auc"])
            for seed in seeds], dtype=np.float64)
        boot_indices = rng.integers(0, len(differences),
                                    size=(bootstrap_replicates, len(differences)))
        boot_means = differences[boot_indices].mean(axis=1)
        # Paired randomization test under the sharp null: independently flip
        # each world's treatment/comparator label and compare the mean to the
        # observed one-sided improvement. Chunking bounds memory at 200 pairs.
        exceedances = 0
        chunk_size = min(10_000, permutation_replicates)
        for offset in range(0, permutation_replicates, chunk_size):
            count = min(chunk_size, permutation_replicates - offset)
            signs = permutation_rng.integers(0, 2, size=(count, len(differences))) * 2 - 1
            permuted_means = (signs * differences).mean(axis=1)
            exceedances += int(np.count_nonzero(permuted_means >= differences.mean()))
        pvalue = (exceedances + 1) / (permutation_replicates + 1)
        raw_p[family] = pvalue
        treatment_adverse = np.mean([
            bool(checkpoint.get("adverse_consequence"))
            for seed in seeds
            for checkpoint in indexed[(family, treated, seed)]["checkpoints"]])
        comparator_adverse = np.mean([
            bool(checkpoint.get("adverse_consequence"))
            for seed in seeds
            for checkpoint in indexed[(family, comparator, seed)]["checkpoints"]])
        comparisons[family] = {
            "n_paired_worlds": len(seeds),
            "mean_auc_difference": float(np.mean(differences)),
            "bootstrap_99pct_lower": float(np.quantile(boot_means, 0.01)),
            "bootstrap_99pct_upper": float(np.quantile(boot_means, 0.99)),
            "one_sided_paired_sign_flip_p": pvalue,
            "treatment_adverse_rate": float(treatment_adverse),
            "comparator_adverse_rate": float(comparator_adverse),
            "adverse_rate_difference": float(treatment_adverse - comparator_adverse),
        }
        for arm in arms:
            arm_rows = [indexed[(family, arm, seed)] for seed in seeds]
            arm_summaries[f"{family}:{arm}"] = {
                "n": len(arm_rows),
                "mean_auc": float(np.mean([row["learning_auc"] for row in arm_rows])),
                "mean_checkpoint_success": float(np.mean([
                    value for row in arm_rows for value in row["learning_curve"]])),
                "abstention_rate": float(np.mean([
                    checkpoint["failed_or_abstained_actions"]
                    for row in arm_rows for checkpoint in row["checkpoints"]])),
                "mean_native_steps": float(np.mean([
                    sum(checkpoint["native_steps"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_target_actions": float(np.mean([
                    sum(checkpoint["target_actions"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_decoder_graph_bytes": float(np.mean([
                    sum(checkpoint["decoder_graph_bytes"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_decoder_graph_nodes": float(np.mean([
                    sum(checkpoint["decoder_graph_nodes"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_frame_mapping_bits": float(np.mean([
                    sum(checkpoint["frame_mapping_bits"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_metric_policy_bits": float(np.mean([
                    sum(checkpoint["metric_policy_bits"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_coordinate_bits": float(np.mean([
                    sum(checkpoint["coordinate_bits"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_wall_time_seconds": float(np.mean([
                    sum(checkpoint["wall_time_seconds"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_exact_checks": float(np.mean([
                    sum(checkpoint["exact_checks"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_query_count": float(np.mean([
                    sum(checkpoint["query_count"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
                "mean_failed_proposals": float(np.mean([
                    sum(checkpoint["failed_proposals"] for checkpoint in row["checkpoints"])
                    for row in arm_rows])),
            }

    adjusted = holm_adjust(raw_p)
    for family, result in comparisons.items():
        result["holm_adjusted_p"] = adjusted[family]
        result["safety_gate"] = (result["adverse_rate_difference"]
                                 <= SAFETY_NONINFERIORITY_MARGIN)
        result["family_gate"] = (
            result["mean_auc_difference"] >= MEAN_BENEFIT_MARGIN
            and result["bootstrap_99pct_lower"] > 0
            and result["holm_adjusted_p"] <= .01
            and result["safety_gate"])
    primary = "PASS" if all(row["family_gate"] for row in comparisons.values()) else "FAIL"
    return {
        "schema": "p28_ousiometric_analysis_v1", "status": "VALID",
        "primary_status": primary,
        "primary_contrast": {"treatment": PRIMARY_ARMS[1], "comparator": PRIMARY_ARMS[0],
                             "interpretation": "published-rotation-bounded; no psychological axis calibration"},
        "multiplicity_family": list(FAMILIES),
        "decision_thresholds": {
            "minimum_mean_auc_difference": MEAN_BENEFIT_MARGIN,
            "confidence_level": .99, "holm_alpha": .01,
            "maximum_adverse_rate_increase": SAFETY_NONINFERIORITY_MARGIN,
            "bootstrap_replicates": bootstrap_replicates,
            "paired_sign_flip_replicates": permutation_replicates,
            "paired_sign_flip_alternative": "treatment_auc_greater_than_comparator_auc",
            "bootstrap_seed": random_seed,
        },
        "comparisons": comparisons,
        "all_arm_summaries": arm_summaries,
        "rows_received": len(indexed),
        "lexical_status": payload.get("lexical_status", "UNSUPPORTED"),
        "external_scores_opened": bool(payload.get("external_scores_opened", False)),
        "success_conditioned_exclusions": 0,
        "missing_rows_dropped": 0,
    }


def self_check() -> dict:
    rows = []
    for family in FAMILIES:
        for seed in range(1, 9):
            for arm in PRIMARY_ARMS + CONTROL_ARMS:
                success = (arm == PRIMARY_ARMS[1])
                checkpoints = [{"goal_satisfied": success,
                                "failed_or_abstained_actions": not success,
                                "adverse_consequence": False,
                                "native_steps": 1, "target_actions": 1,
                                "decoder_graph_bytes": 1, "decoder_graph_nodes": 1,
                                "frame_mapping_bits": 1, "metric_policy_bits": 1,
                                "coordinate_bits": 1, "wall_time_seconds": .1,
                                "exact_checks": 1, "query_count": 1,
                                "failed_proposals": int(not success)}
                               for _ in range(4)]
                rows.append({"world_family": family, "frame_id": arm, "seed": seed,
                             "learning_auc": float(success),
                             "learning_curve": [float(success)] * 4,
                             "checkpoints": checkpoints,
                             "heldout_used_for_selection": False})
    result = analyze({"schema": "p28_ousiometric_raw_v1", "rows": rows},
                     bootstrap_replicates=200, permutation_replicates=1_000)
    ok = (result["status"] == "VALID" and result["primary_status"] == "PASS"
          and result["rows_received"] == len(rows)
          and set(result["comparisons"]) == set(FAMILIES))
    return {"schema": "p28_ousiometric_analyzer_self_check_v1",
            "status": "PASS" if ok else "FAIL",
            "rows": result["rows_received"],
            "comparison_families": result["multiplicity_family"],
            "primary_status": result["primary_status"]}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-check", action="store_true")
    modes.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--bootstrap-replicates", type=int, default=BOOTSTRAP_REPLICATES)
    parser.add_argument("--permutation-replicates", type=int, default=PERMUTATION_REPLICATES)
    args = parser.parse_args(argv)
    try:
        if args.self_check:
            result = self_check()
        else:
            payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
            result = analyze(payload, bootstrap_replicates=args.bootstrap_replicates,
                             permutation_replicates=args.permutation_replicates)
            result["input_sha256"] = hashlib.sha256(Path(args.input).read_bytes()).hexdigest()
        serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(serialized, encoding="utf-8")
        print(serialized)
        return 0 if result.get("status") in {"PASS", "VALID"} else 1
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
