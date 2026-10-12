#!/usr/bin/env python3
"""Independently validate native matcher counters for the locked join matrix."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) != 4:
    raise SystemExit("usage: analyze... COUNTERS_A COUNTERS_B UNINSTRUMENTED_TOPOLOGY_RAW")
paths = [Path(x) for x in sys.argv[1:]]
raw_a, raw_b, base = [json.loads(p.read_text()) for p in paths]


def semantics(raw):
    keys = ("topology", "n_initial_nodes", "n_initial_edges", "match_arity",
            "enumerated_match_bindings", "distinct_terminal_nodes", "progress_bound",
            "actual_node_count", "actual_edge_count", "actual_graph_projection_sha256",
            "native_report", "checks", "all_checks_pass", "scale_audit", "per_rule_audit")
    return {x["case_id"]: {k: x[k] for k in keys} for x in raw["cases"]}


def group_key(row):
    return (row["topology"], row["n_initial_nodes"], row["match_arity"])


base_by_group = {}
for row in base["cases"]:
    base_by_group.setdefault(group_key(row), row)
base_by_group = {k: v for k, v in base_by_group.items()}
checks = {
    "fresh_process_counter_replication": semantics(raw_a) == semantics(raw_b),
    "both_captures_pass": raw_a["all_checks_pass"] and raw_b["all_checks_pass"],
    "same_capture_design": raw_a["design"] == raw_b["design"],
    "expected_rep_count": all(len(r["cases"]) == 126 for r in (raw_a, raw_b)),
    "counter_arm_input_groups_match": set(base_by_group) == {group_key(x) for x in raw_a["cases"]},
    "native_artifact_matches_uninstrumented": all(
        r["provenance"]["native_sha256"] == base["provenance"]["native_sha256"] for r in (raw_a, raw_b)),
    "captured_sources_match_checkout": all(
        hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value
        for r in (raw_a, raw_b) for name, value in r["provenance"]["source_sha256"].items()),
    "native_artifact_matches_checkout": all(
        hashlib.sha256(Path(r["provenance"]["native_path"]).read_bytes()).hexdigest()
        == r["provenance"]["native_sha256"] for r in (raw_a, raw_b)),
}
for raw in (raw_a, raw_b):
    for case in raw["cases"]:
        label = case["case_id"]
        group = base_by_group[group_key(case)]
        local = {
            "same_binding_count_as_wall_capture": case["enumerated_match_bindings"] == group["enumerated_match_bindings"],
            "same_terminal_count_as_wall_capture": case["distinct_terminal_nodes"] == group["distinct_terminal_nodes"],
            "same_graph_hash_as_wall_capture": case["actual_graph_projection_sha256"] == group["actual_graph_projection_sha256"],
            "candidate_path_conservation": case["scale_audit"]["cand_enum"] == sum(
                case["scale_audit"][k] for k in ("cand_enum_scan", "cand_enum_local", "cand_enum_hinted")),
            "candidate_epoch_conservation": case["scale_audit"]["cand_enum"] == sum(
                case["scale_audit"][k] for k in ("cand_enum_first", "cand_enum_repeat")),
            "all_enumerated_candidates_tested": case["scale_audit"]["cand_enum"] == case["scale_audit"]["cand_tested"],
            "term_eval_variants_conserved": case["scale_audit"]["term_evals_total"] == sum(
                v for k, v in case["scale_audit"].items() if k.startswith("term_eval:")),
            "term_units_variants_conserved": case["scale_audit"]["term_units_total"] == sum(
                v for k, v in case["scale_audit"].items() if k.startswith("term_unit:")),
        }
        metrics = {
            "candidate_pairs": "cand_enum", "candidate_tests": "cand_tested",
            "term_evaluations": "term_evals_total", "term_units": "term_units_total",
            "binding_leaves": "leaf_visits", "rule_enumerations": "rule_enumerations",
            "effect_edge_insert_attempts": "rule_effect_edge_insert_attempts",
            "effect_node_inserts": "rule_effect_node_inserts",
        }
        per_rule = defaultdict(int)
        for row in case["per_rule_audit"]:
            per_rule[row["metric"]] += row["count"]
        for per_metric, global_metric in metrics.items():
            local[f"per_rule_conserved:{per_metric}"] = case["scale_audit"][global_metric] == per_rule[per_metric]
        checks.update({f"{raw['run_id']}:{label}:{key}": value for key, value in local.items()})

groups = defaultdict(list)
for row in raw_a["cases"]:
    groups[group_key(row)].append(row)
summary = []
for (topology, n, q), rows in sorted(groups.items()):
    counters = [x["scale_audit"] for x in rows]
    summary.append({"topology": topology, "n": n, "q": q, "replicates": len(rows),
                    "input_edges": rows[0]["n_initial_edges"],
                    "match_bindings": rows[0]["enumerated_match_bindings"],
                    "candidate_pairs": statistics.median(x["cand_enum"] for x in counters),
                    "candidate_tests": statistics.median(x["cand_tested"] for x in counters),
                    "scan_candidates": statistics.median(x["cand_enum_scan"] for x in counters),
                    "local_candidates": statistics.median(x["cand_enum_local"] for x in counters),
                    "leaf_visits": statistics.median(x["leaf_visits"] for x in counters),
                    "rule_enumerations": statistics.median(x["rule_enumerations"] for x in counters),
                    "term_evaluations": statistics.median(x["term_evals_total"] for x in counters),
                    "graph_writes": statistics.median(x["graph_writes"] for x in counters)})

result = {
    "schema": "substrate_finite_key_join_work_attribution_analysis_v1_2",
    "raw_sha256": {f"input_{i+1}:{p.name}": hashlib.sha256(p.read_bytes()).hexdigest()
                   for i, p in enumerate(paths)},
    "check_count": len(checks), "checks": checks, "all_checks_pass": all(checks.values()),
    "summary": summary,
    "claim_boundary": "Native scale-audit counts for one locked positive finite-key rule schema; audit-on wall times intentionally excluded.",
}
print(json.dumps(result, sort_keys=True, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
