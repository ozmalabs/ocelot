#!/usr/bin/env python3
"""Independent integrity and summary analysis for proposal-coverage v1."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1.py"
ANALYZER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_STRUCTURAL_REPAIR_V1_PREREG_20261005.md"
FIXTURE = ROOT / "evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json"
EDIT_OPS = ROOT / "domains/edit_ops.py"
LOCK = ROOT / "evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_lock_20261005.json"
CAPTURE = ROOT / "evaluation/reports/blind_structural_repair_proposal_coverage_v1_20261005.json"
OUT = ROOT / "evaluation/reports/blind_structural_repair_proposal_coverage_v1_analysis_20261005.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen():
    return {str(p.relative_to(ROOT)): sha(p)
            for p in (RUNNER, ANALYZER, PROTOCOL, FIXTURE, EDIT_OPS)}


def main():
    lock = json.loads(LOCK.read_text())
    capture = json.loads(CAPTURE.read_text())
    errors = []
    if frozen() != lock["sources"]:
        errors.append("current source hashes differ from lock")
    if capture.get("lock_sha256") != sha(LOCK):
        errors.append("capture lock hash mismatch")
    workers = capture.get("workers", [])
    if len(workers) != lock["workers"]:
        errors.append("worker count mismatch")
    case_sets = []
    for worker in workers:
        if worker.get("sources_before") != lock["sources"] or worker.get("sources_after") != lock["sources"]:
            errors.append(f"worker {worker.get('worker')} source lock mismatch")
        rows = worker.get("cases", [])
        case_sets.append({r.get("case_id"): r for r in rows})
        if len(rows) != lock["case_count"]:
            errors.append(f"worker {worker.get('worker')} case count mismatch")
        for row in rows:
            if row.get("truncated"):
                errors.append(f"candidate pool truncated: {row.get('case_id')}")
            if row.get("candidate_count") != row.get("unique_count"):
                errors.append(f"candidate count accounting mismatch: {row.get('case_id')}")
            if row.get("candidate_count") != len(set(row.get("candidate_ids", []))):
                errors.append(f"candidate IDs not unique: {row.get('case_id')}")
    if case_sets:
        first = case_sets[0]
        for other in case_sets[1:]:
            if set(first) != set(other):
                errors.append("workers evaluated different case IDs")
                continue
            for case_id in first:
                for key in ("candidate_count", "proposal_count_before_dedup", "valid_count_before_dedup",
                            "unique_count", "truncated", "operator_counts", "target_in_pool",
                            "target_match_count", "candidate_ids"):
                    if first[case_id].get(key) != other[case_id].get(key):
                        errors.append(f"worker semantic mismatch for {case_id}.{key}")
                        break
    rows = list(case_sets[0].values()) if case_sets else []
    hits = sum(bool(row.get("target_in_pool")) for row in rows)
    counts = [row.get("candidate_count", 0) for row in rows]
    timings = [row.get("enumeration_wall_ns", 0) for row in rows]
    summary = {
        "cases": len(rows),
        "target_proposal_hits": hits,
        "target_proposal_misses": len(rows) - hits,
        "proposal_coverage": hits / len(rows) if rows else None,
        "candidate_count_total": sum(counts),
        "candidate_count_median": sorted(counts)[len(counts) // 2] if counts else None,
        "enumeration_wall_ns_median": sorted(timings)[len(timings) // 2] if timings else None,
        "cases_by_candidate_coverage": [
            {"case_id": row["case_id"], "candidate_count": row["candidate_count"],
             "target_in_pool": row["target_in_pool"], "operator_counts": row["operator_counts"]}
            for row in rows
        ],
    }
    result = {"schema": "BlindStructuralRepairProposalCoverageV1Analysis",
              "passed": not errors, "errors": errors, "summary": summary,
              "interpretation": "Proposal-pool coverage only; no task outcomes, graph selection, held-out generalization, or commit were measured."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
