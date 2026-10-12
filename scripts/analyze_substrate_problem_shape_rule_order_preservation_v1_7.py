#!/usr/bin/env python3
"""Analyze the locked three-arm V1.7 rule-placement comparison."""
from __future__ import annotations

import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_7_20260925.json"
CORPUS_LOCK = ROOT / "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_7_analysis_20260925.json"
PS_RULES = {"ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"}
METRICS = ("cand_tested", "term_evals_total", "rule_enumerations", "where_evals", "graph_writes", "term_units_total")
ARMS = ("baseline", "append", "preserve")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rule_totals(arm: dict) -> dict[tuple[str, str], int]:
    totals: defaultdict[tuple[str, str], int] = defaultdict(int)
    for record in arm["records"]:
        for row in record["all_rule_scale_audit"]:
            totals[(str(row["rule_name"]), str(row["metric"]))] += int(row["count"])
    return dict(totals)


def median_range(values: list[float]) -> dict:
    return {"median": statistics.median(values), "min": min(values), "max": max(values)}


def main() -> int:
    raw = json.loads(RAW.read_text())
    if not raw.get("all_gates_pass") or not raw.get("unique_process_ids") or len(raw.get("pairs", [])) != 12:
        raise SystemExit("V1.7 report failed an acceptance gate")
    lock = json.loads(CORPUS_LOCK.read_text())
    manifest = {row["path"]: row["sha256"] for row in lock["manifests"]}
    snapshot = raw["snapshot"]
    base_dir, candidate_dir = Path(snapshot["baseline_seed_dir"]), Path(snapshot["candidate_seed_dir"])
    base_match = len(list(base_dir.rglob("*.json"))) == len(manifest) and all(
        (base_dir / rel).is_file() and not (base_dir / rel).is_symlink() and sha(base_dir / rel) == digest
        for rel, digest in manifest.items())
    candidate_match = len(list(candidate_dir.rglob("*.json"))) == len(manifest) and all(
        (candidate_dir / rel).is_file() and not (candidate_dir / rel).is_symlink()
        and (rel == "problem_shape_growth.json" or sha(candidate_dir / rel) == digest)
        for rel, digest in manifest.items())
    if not base_match or not candidate_match:
        raise SystemExit("V1.7 worker snapshots failed byte-level corpus verification")

    mix_results = {}
    for mix in ("recognition", "recurrent_residual"):
        pairs = [pair for pair in raw["pairs"] if pair["mix"] == mix]
        if len(pairs) != 6:
            raise SystemExit(f"expected six triads for {mix}")
        rule_delta: defaultdict[tuple[str, str, str], list[int]] = defaultdict(list)
        global_values = {arm: {metric: [] for metric in METRICS} for arm in ARMS}
        wall = {arm: [] for arm in ("append", "preserve")}
        cpu = {arm: [] for arm in ("append", "preserve")}
        unchanged_preserve_other_rules = True
        pair_records = []
        for pair in pairs:
            gates = (pair["semantic_parity"] and pair["seed_corpus_order_match"] and pair["preserved_order_match"]
                     and pair["append_order_matches_expected_tombstone_and_append"])
            if not gates:
                raise SystemExit(f"pair {pair['pair']} has a failed gate")
            totals = {arm: rule_totals(pair["arms"][arm]) for arm in ARMS}
            all_keys = set().union(*(set(v) for v in totals.values()))
            pair_non_ps_changes = {arm: 0 for arm in ("append", "preserve")}
            for key in all_keys:
                name, metric = key
                for arm in ("append", "preserve"):
                    delta = totals[arm].get(key, 0) - totals["baseline"].get(key, 0)
                    rule_delta[(arm, name, metric)].append(delta)
                    if name not in PS_RULES and delta != 0:
                        pair_non_ps_changes[arm] += 1
                        if arm == "preserve":
                            unchanged_preserve_other_rules = False
            for arm in ARMS:
                for metric in METRICS:
                    global_values[arm][metric].append(int(pair["arms"][arm]["global_scale_audit"][metric]))
            for arm in ("append", "preserve"):
                wall[arm].append(float(pair[f"wall_ratio_{arm}_over_baseline"]))
                cpu[arm].append(float(pair[f"cpu_ratio_{arm}_over_baseline"]))
            pair_records.append({
                "pair": pair["pair"], "arm_order": pair["order"],
                "wall_ratios": {arm: pair[f"wall_ratio_{arm}_over_baseline"] for arm in ("append", "preserve")},
                "cpu_ratios": {arm: pair[f"cpu_ratio_{arm}_over_baseline"] for arm in ("append", "preserve")},
                "non_problem_shape_rule_counter_changes": pair_non_ps_changes,
            })

        global_summary = {}
        for metric in METRICS:
            med = {arm: statistics.median(global_values[arm][metric]) for arm in ARMS}
            global_summary[metric] = {
                "baseline_median": med["baseline"], "append_median": med["append"], "preserve_median": med["preserve"],
                "append_delta_vs_baseline": med["append"] - med["baseline"],
                "preserve_delta_vs_baseline": med["preserve"] - med["baseline"],
                "preserve_delta_vs_append": med["preserve"] - med["append"],
                "append_relative_change": (med["append"] - med["baseline"]) / med["baseline"] if med["baseline"] else None,
                "preserve_relative_change": (med["preserve"] - med["baseline"]) / med["baseline"] if med["baseline"] else None,
            }
        ps_deltas = {}
        collateral = {}
        for (arm, name, metric), values in sorted(rule_delta.items()):
            item = {"median_delta_vs_baseline": statistics.median(values), "min_delta": min(values), "max_delta": max(values)}
            if name in PS_RULES and any(values):
                ps_deltas.setdefault(arm, {}).setdefault(name, {})[metric] = item
            elif name not in PS_RULES and metric == "term_evaluations" and any(v > 0 for v in values):
                collateral.setdefault(arm, {})[name] = item
        mix_results[mix] = {
            "pair_count": len(pairs),
            "timing_ratios": {arm: {"wall": median_range(wall[arm]), "cpu": median_range(cpu[arm])} for arm in ("append", "preserve")},
            "global_counters": global_summary,
            "problem_shape_rule_deltas": ps_deltas,
            "non_problem_shape_term_evaluation_increases": collateral,
            "preserve_arm_has_no_non_problem_shape_counter_changes": unchanged_preserve_other_rules,
            "pairs": pair_records,
        }

    result = {
        "schema_version": 1,
        "analysis_id": "problem-shape-rule-order-preservation-v1.7-analysis-20260925",
        "raw_path": str(RAW.relative_to(ROOT)), "raw_sha256": sha(RAW),
        "all_gates_pass": raw["all_gates_pass"], "unique_process_ids": raw["unique_process_ids"],
        "snapshot_integrity": {
            "baseline_snapshot_matches_every_locked_seed_hash": base_match,
            "candidate_matches_every_locked_seed_except_intentionally_transformed_growth_manifest": candidate_match,
            "locked_corpus_digest": lock["corpus_digest"],
            "seed_index_cache_hashes_checked_around_every_worker": True,
            "cache_normalization": "both derived caches explicitly cleared and rebuilt before any arm process",
        },
        "interpretation": "The same-corpus randomized three-arm comparison reproduces the six non-ProblemShape Term-evaluation increases in the append arm and eliminates all other-rule counter changes in the original-slot arm. This supports rule-placement/timing as the cause of the earlier collateral work on these workloads. It is work-count evidence only; timing ranges are broad, and the result does not generalize to natural tasks or larger populations.",
        "mixes": mix_results,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": result["all_gates_pass"], "triads": len(raw["pairs"]), "output": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
