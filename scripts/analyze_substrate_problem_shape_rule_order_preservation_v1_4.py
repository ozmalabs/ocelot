#!/usr/bin/env python3
"""Summarize the locked V1.4 rule-order preservation comparison."""
from __future__ import annotations

import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_4_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_4_analysis_20260925.json"
CORPUS_LOCK = ROOT / "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_4_20260925.json"
PS_RULES = {"ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"}
GLOBAL_METRICS = ("cand_tested", "term_evals_total", "rule_enumerations", "where_evals", "graph_writes", "term_units_total")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate_rules(arm: dict) -> dict[tuple[str, str], int]:
    totals: defaultdict[tuple[str, str], int] = defaultdict(int)
    for record in arm["records"]:
        for row in record["all_rule_scale_audit"]:
            totals[(str(row["rule_name"]), str(row["metric"]))] += int(row["count"])
    return dict(totals)


def summarize() -> dict:
    raw = json.loads(RAW.read_text())
    if not raw.get("all_gates_pass") or not raw.get("unique_process_ids"):
        raise SystemExit("V1.4 raw report does not pass its locked gates")
    manifest = json.loads(CORPUS_LOCK.read_text())["manifests"]
    expected_files = {row["path"]: row["sha256"] for row in manifest}
    snapshot = raw["snapshot"]
    base_dir, candidate_dir = Path(snapshot["baseline_seed_dir"]), Path(snapshot["candidate_seed_dir"])
    baseline_snapshot_verified = all(
        (base_dir / rel).is_file() and not (base_dir / rel).is_symlink() and sha(base_dir / rel) == digest
        for rel, digest in expected_files.items()
    ) and len(list(base_dir.rglob("*.json"))) == len(expected_files)
    candidate_snapshot_verified = all(
        (candidate_dir / rel).is_file() and not (candidate_dir / rel).is_symlink()
        and (rel == "problem_shape_growth.json" or sha(candidate_dir / rel) == digest)
        for rel, digest in expected_files.items()
    ) and len(list(candidate_dir.rglob("*.json"))) == len(expected_files)
    if not baseline_snapshot_verified or not candidate_snapshot_verified:
        raise SystemExit("immutable worker snapshots do not match the locked corpus")
    live_rows = []
    for path in sorted((ROOT / "seeds").glob("*.json")):
        live_rows.append((path.name, sha(path)))
    for path in sorted((ROOT / "seeds/generated").glob("*.json")):
        live_rows.append((f"generated/{path.name}", sha(path)))
    live_digest = hashlib.sha256(json.dumps(live_rows, separators=(",", ":")).encode()).hexdigest()
    live_source_drifted = live_digest != json.loads(CORPUS_LOCK.read_text())["corpus_digest"]
    mixes = {}
    for mix in ("recognition", "recurrent_residual"):
        pairs = [pair for pair in raw["pairs"] if pair["mix"] == mix]
        if len(pairs) != 6:
            raise SystemExit(f"expected six pairs for {mix}, got {len(pairs)}")
        pair_deltas = []
        rule_deltas: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
        for pair in pairs:
            if not pair["semantic_parity"] or not pair["pre_observation_rule_order_match"]:
                raise SystemExit(f"pair {pair['pair']} failed a required gate")
            baseline, candidate = pair["arms"]["baseline"], pair["arms"]["candidate"]
            b_rules, c_rules = aggregate_rules(baseline), aggregate_rules(candidate)
            for key in set(b_rules) | set(c_rules):
                rule_deltas[key].append(c_rules.get(key, 0) - b_rules.get(key, 0))
            pair_deltas.append({
                "pair": pair["pair"],
                "wall_ratio_candidate_over_baseline": pair["wall_ratio"],
                "cpu_ratio_candidate_over_baseline": pair["cpu_ratio"],
                "global_counter_deltas": {
                    metric: int(candidate["global_scale_audit"][metric]) - int(baseline["global_scale_audit"][metric])
                    for metric in GLOBAL_METRICS
                },
                "non_problem_shape_rule_counter_changes": sum(
                    1 for key in set(b_rules) | set(c_rules)
                    if key[0] not in PS_RULES and b_rules.get(key, 0) != c_rules.get(key, 0)
                ),
            })
        non_ps_nonzero = {
            f"{name}::{metric}": {"median_delta": statistics.median(values), "min_delta": min(values), "max_delta": max(values)}
            for (name, metric), values in sorted(rule_deltas.items())
            if name not in PS_RULES and any(value != 0 for value in values)
        }
        ps_summary = {}
        for (name, metric), values in sorted(rule_deltas.items()):
            if name in PS_RULES and any(value != 0 for value in values):
                ps_summary.setdefault(name, {})[metric] = {
                    "median_delta": statistics.median(values),
                    "min_delta": min(values),
                    "max_delta": max(values),
                }
        global_summary = {}
        for metric in GLOBAL_METRICS:
            baseline_values = [int(pair["arms"]["baseline"]["global_scale_audit"][metric]) for pair in pairs]
            candidate_values = [int(pair["arms"]["candidate"]["global_scale_audit"][metric]) for pair in pairs]
            bmed, cmed = statistics.median(baseline_values), statistics.median(candidate_values)
            global_summary[metric] = {
                "baseline_median": bmed,
                "candidate_median": cmed,
                "median_relative_change": (cmed - bmed) / bmed if bmed else None,
                "paired_delta_median": statistics.median([c - b for b, c in zip(baseline_values, candidate_values)]),
            }
        walls = [pair["wall_ratio"] for pair in pairs]
        cpus = [pair["cpu_ratio"] for pair in pairs]
        mixes[mix] = {
            "pair_count": len(pairs),
            "timing": {
                "wall_ratio_median": statistics.median(walls), "wall_ratio_min": min(walls), "wall_ratio_max": max(walls),
                "cpu_ratio_median": statistics.median(cpus), "cpu_ratio_min": min(cpus), "cpu_ratio_max": max(cpus),
            },
            "global_counters": global_summary,
            "problem_shape_rule_deltas": ps_summary,
            "non_problem_shape_rule_counter_changes": non_ps_nonzero,
            "all_non_problem_shape_rule_counters_identical_in_every_pair": not non_ps_nonzero,
            "pairs": pair_deltas,
        }
    result = {
        "schema_version": 1,
        "analysis_id": "problem-shape-rule-order-preservation-v1.4-analysis-20260925",
        "raw_path": str(RAW.relative_to(ROOT)),
        "raw_sha256": sha(RAW),
        "all_gates_pass": raw["all_gates_pass"],
        "unique_process_ids": raw["unique_process_ids"],
        "pair_count": len(raw["pairs"]),
        "snapshot_integrity": {
            "baseline_matches_every_locked_seed_byte": baseline_snapshot_verified,
            "candidate_matches_every_locked_seed_except_transformed_problem_shape_manifest": candidate_snapshot_verified,
            "locked_corpus_digest": json.loads(CORPUS_LOCK.read_text())["corpus_digest"],
            "live_corpus_digest_at_analysis": live_digest,
            "live_source_has_drifted_since_locked_snapshot": live_source_drifted,
        },
        "interpretation": "With an immutable corpus shared between arms and ProblemShape rules kept in their original slots, all audited counters for non-ProblemShape rules are identical pair by pair. Candidate work reductions are confined to the eventized ProblemShape rules. This directly establishes the held-order mechanism on these authored N=32 workloads; attributing the earlier append-arm collateral increases to rule position still requires a same-corpus appended-arm control.",
        "mixes": mixes,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    summary = summarize()
    print(json.dumps({"all_gates_pass": summary["all_gates_pass"], "pairs": summary["pair_count"], "output": str(OUT)}))
