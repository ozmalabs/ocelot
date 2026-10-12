#!/usr/bin/env python3
"""Analyze scan-based and indexed GenInfer population work."""
from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "evaluation/reports/geninfer_scope_index_trace_v2_1_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/geninfer_scope_index_trace_v2_1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/geninfer_scope_index_trace_v2_1_corrected_analysis_20261005.json"
HELPER_KINDS = {
    "dynamic_helper_invocation", "helper_codebook_population_node",
    "helper_node_attribute_examined", "helper_codebook_part_parsed",
    "helper_relation_cue_population_node", "helper_search_candidate",
    "helper_candidate_part_scored", "helper_graph_term_node_decoded",
    "helper_render_rule_candidate", "helper_auxiliary_population_node",
    "helper_scope_population_index_query", "helper_scope_population_index_member",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(CAP.read_text())
    lock = json.loads(LOCK.read_text())
    groups = defaultdict(list)
    errors = []
    pids = set()
    for row in raw["cases"]:
        mode = row["case"]["mode"]
        groups[mode].append(row)
        pids.add(row["pid"])
        if not row.get("source_stable"):
            errors.append(f"{mode}/{row.get('replicate')}: source drift")
        trace = row.get("runtime_work_trace", {})
        if trace.get("dropped") != 0:
            errors.append(f"{mode}/{row.get('replicate')}: trace drops")
        if len(row.get("outputs", [])) != 2 or not all(
            out.get("oracle_exact") and out.get("target_generator_present")
            for out in row.get("outputs", [])
        ):
            errors.append(f"{mode}/{row.get('replicate')}: exact positive output failed")
        if not all(member.get("members_agree") for member in row.get("scope_membership", [])):
            errors.append(f"{mode}/{row.get('replicate')}: scope membership mismatch")

    summary = {}
    signatures = {}
    for mode, rows in sorted(groups.items()):
        if len(rows) != 3:
            errors.append(f"{mode}: expected three replicates, got {len(rows)}")
        replicate_work = []
        per_replicate = []
        for row in rows:
            counts = Counter()
            attributed_rules = set()
            for event in row["runtime_work_trace"]["rows"]:
                if len(event) != 6:
                    errors.append(f"{mode}/{row.get('replicate')}: malformed work row")
                    continue
                _, _, rule_uid, kind, helper, units = event
                if str(kind) in HELPER_KINDS and int(helper or 0) == 4:
                    counts[str(kind)] += int(units)
                    attributed_rules.add(int(rule_uid))
                    if int(rule_uid) == 0:
                        errors.append(f"{mode}/{row.get('replicate')}: GenInfer work lacks rule UID")
            replicate_work.append(dict(counts))
            per_replicate.append({
                "replicate": row["replicate"],
                "geninfer_rule_uids": sorted(attributed_rules),
                "geninfer_work": dict(sorted(counts.items())),
            })
        signatures[mode] = replicate_work
        kinds = sorted({kind for counts in replicate_work for kind in counts})
        median_work = {
            kind: int(statistics.median(counts.get(kind, 0) for counts in replicate_work))
            for kind in kinds
        }
        summary[mode] = {
            "replicates": len(rows),
            "distinct_worker_pids": len({row["pid"] for row in rows}),
            "median_wall_ns": int(statistics.median(int(row["closure_wall_ns"]) for row in rows)),
            "median_cpu_ns": int(statistics.median(int(row["closure_cpu_ns"]) for row in rows)),
            "median_scope_index_build_ns": int(statistics.median(int(row.get("scope_index_build_ns", 0)) for row in rows)),
            "median_work_by_kind": dict(sorted(median_work.items())),
            "per_replicate": per_replicate,
        }

    work_reproduces = all(
        len({json.dumps(counts, sort_keys=True) for counts in replicates}) == 1
        for replicates in signatures.values()
    )
    scoped = summary.get("frame_scoped", {}).get("median_work_by_kind", {})
    indexed = summary.get("frame_scoped_indexed", {}).get("median_work_by_kind", {})
    explicit_global = summary.get("explicit_global", {}).get("median_work_by_kind", {})
    unscoped_global = summary.get("unscoped_global", {}).get("median_work_by_kind", {})
    comparisons = {}
    for kind in (
        "helper_codebook_population_node", "helper_node_attribute_examined",
        "helper_codebook_part_parsed", "helper_search_candidate",
    ):
        comparisons[kind] = {
            "frame_scoped": scoped.get(kind, 0),
            "frame_scoped_indexed": indexed.get(kind, 0),
            "explicit_global": explicit_global.get(kind, 0),
            "unscoped_global": unscoped_global.get(kind, 0),
        }

    indexed_rows = groups.get("frame_scoped_indexed", [])
    checks = {
        "all_four_conditions_have_three_replicates": len(raw["cases"]) == 12 and len(groups) == 4 and all(len(rows) == 3 for rows in groups.values()),
        "fresh_worker_processes": len(pids) == 12,
        "source_stable_and_no_trace_drops": not any("source drift" in error or "trace drops" in error for error in errors),
        "exact_outputs_and_scope_membership": not any("exact positive" in error or "scope membership" in error for error in errors),
        "work_counts_reproduce_within_condition": work_reproduces,
        "helper_work_rule_attributed": not any("lacks rule UID" in error for error in errors),
        "scoped_codebook_work_is_lower_than_global": scoped.get("helper_codebook_part_parsed", 0) < unscoped_global.get("helper_codebook_part_parsed", 0)
            and scoped.get("helper_search_candidate", 0) < unscoped_global.get("helper_search_candidate", 0),
        "scan_scope_enumerates_full_population": scoped.get("helper_codebook_population_node", 0) == unscoped_global.get("helper_codebook_population_node", -1),
        "indexed_scope_avoids_population_scan": len(indexed_rows) == 3
            and all(row.get("scope_index_declared") and row.get("scope_index_build_ns", 0) > 0 for row in indexed_rows)
            and indexed.get("helper_codebook_population_node", 0) == 0
            and indexed.get("helper_scope_population_index_query", 0) == 4
            and indexed.get("helper_scope_population_index_member", 0) == 4,
        "indexed_scope_preserves_scoped_candidates": indexed.get("helper_codebook_part_parsed", -1) == scoped.get("helper_codebook_part_parsed", -2)
            and indexed.get("helper_search_candidate", -1) == scoped.get("helper_search_candidate", -2),
    }
    result = {
        "schema": "GenInferScopeIndexTraceV2_1CorrectedAnalysis",
        "capture_sha256": sha(CAP),
        "lock_sha256": sha(LOCK),
        "analyzer_sha256": sha(Path(__file__)),
        "correction": "Sparse work rows omit zero-count kinds; the original analyzer used -1 as the missing-key sentinel and incorrectly failed the zero-scan gate. This corrected analyzer treats an absent scan kind as zero and preserves the original preregistered requirement.",
        "checks": checks,
        "summary": summary,
        "scoped_vs_global": comparisons,
        "errors": errors,
        "passed": all(checks.values()),
        "claim_limit": "Authored two-frame GenInfer fixtures only. The attribute-index arm avoids enumerating unrelated ShapeSignature nodes after the index is declared; scope discovery, automatic index admission, mutation/clone cost at scale, and natural-task prevalence are not established.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "checks": checks,
        "scoped_vs_global": comparisons,
        "scope_index_build_ns": {mode: row["median_scope_index_build_ns"] for mode, row in summary.items()},
        "passed": result["passed"], "errors": errors}, indent=2))
    if not result["passed"]:
        raise SystemExit("corrected scope-index v2.1 analysis failed")


if __name__ == "__main__":
    main()
