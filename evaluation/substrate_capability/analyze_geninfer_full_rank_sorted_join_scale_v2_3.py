#!/usr/bin/env python3
"""Frozen semantic and scaling gates for the sorted GenInfer identity join."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/geninfer_full_rank_sorted_join_scale_v2_3.py"
ANALYZER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/GENINFER_FULL_RANK_SORTED_JOIN_SCALE_V2_3_PREREG_20261006.md"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_3_20261006.json"
    payload = json.loads(path.read_text())
    errors = []
    for key, source in (("runner_sha256", RUNNER), ("analyzer_sha256", ANALYZER), ("protocol_sha256", PROTOCOL)):
        if payload.get(key) != sha(source):
            errors.append(f"{key} mismatch")
    cases = payload.get("case_spec", [])
    workers = payload.get("workers", [])
    indexed = {}
    binary_hashes = {name: set() for name in ("nested", "sorted")}
    manifests = {}
    for row in workers:
        key = (row["case"]["id"], row["audit"], row["variant"])
        if key in indexed:
            errors.append(f"duplicate worker {key}")
        indexed[key] = row
        binary_hashes[row["variant"]].add(row["native_sha256"])
        if not row.get("source_stable") or row["source_before"] != row["source_after"]:
            errors.append(f"source drift {key}")
        manifests.setdefault(row["variant"], row["source_before"])
        if row.get("process_maxrss_platform_units", 0) <= 0:
            errors.append(f"missing RSS {key}")
        n = row["case"]["relation_count"]
        source_order, target_order = row.get("source_row_order"), row.get("target_row_order")
        if (not isinstance(source_order, list) or not isinstance(target_order, list)
                or sorted(source_order) != list(range(n)) or sorted(target_order) != list(range(n))):
            errors.append(f"invalid row permutation {key}")
        elif source_order == target_order:
            errors.append(f"source/target row orders were not independently permuted {key}")
        for stage, phase in row["phases"].items():
            if not isinstance(phase.get("wall_ns"), int) or phase["wall_ns"] <= 0:
                errors.append(f"invalid timing {key}/{stage}")
            if row["audit"]:
                c = phase.get("full_rank_counters", {})
                required = ("gen_infer_full_rank_bases", "gen_infer_full_rank_refusals",
                    "gen_infer_full_rank_attempts", "gen_infer_full_rank_apply_rejects",
                    "gen_infer_full_rank_candidate_rejects", "gen_infer_full_rank_residual_rejects",
                    "gen_infer_full_rank_survivors", "gen_infer_full_rank_identity_key_comparisons")
                if any(name not in c for name in required):
                    errors.append(f"missing counters {key}/{stage}")
                elif c["gen_infer_full_rank_bases"] > 0 and c["gen_infer_full_rank_identity_key_comparisons"] <= 0:
                    errors.append(f"alignment attempts lack key comparison counts {key}/{stage}")
                elif c["gen_infer_full_rank_bases"] != c["gen_infer_full_rank_refusals"] + c["gen_infer_full_rank_attempts"]:
                    errors.append(f"basis conservation {key}/{stage}")
                elif c["gen_infer_full_rank_attempts"] != sum(c[name] for name in required[3:7]):
                    errors.append(f"attempt conservation {key}/{stage}")
    if len(indexed) != len(cases) * 4:
        errors.append("worker coverage incomplete")
    if any(len(binary_hashes[name]) != 1 for name in binary_hashes) or binary_hashes["nested"] == binary_hashes["sorted"]:
        errors.append("binary hashes inconsistent")
    if manifests.get("nested") != manifests.get("sorted"):
        errors.append("source manifests differ")
    for family in {case["family"] for case in cases}:
        family_reps = {case["replicate"] for case in cases if case["family"] == family}
        if family_reps != {0, 1}:
            errors.append(f"replicates incomplete: {family}")

    def has_matrix(row, matrix):
        return any(g.get("matrix") == matrix for g in row.get("final_generators", []))

    semantic_fields = ("status", "covered_by", "residual", "receipts", "closure_work", "generators")
    for case in cases:
        ident, kind = case["id"], case["kind"]
        for audit in (False, True):
            pair = [indexed.get((ident, audit, arm)) for arm in ("nested", "sorted")]
            if any(row is None for row in pair):
                errors.append(f"missing pair {ident}/audit={audit}")
                continue
            nested, sorted_join = pair
            if nested.get("source_row_order") != sorted_join.get("source_row_order") or nested.get("target_row_order") != sorted_join.get("target_row_order"):
                errors.append(f"paired row ordering differs across arms {ident}/audit={audit}")
            matrix = [v for row in nested["expected_matrix"] for v in row]
            for stage in ("train", "heldout"):
                for field in semantic_fields:
                    if nested["phases"][stage].get(field) != sorted_join["phases"][stage].get(field):
                        errors.append(f"semantic mismatch {ident}/{stage}/{field}/audit={audit}")
            if kind == "positive":
                for row in pair:
                    if not row["training_oracle_exact"] or not has_matrix(row, matrix):
                        errors.append(f"positive matrix not acquired: {ident}/{row['variant']}")
                    if any(row["phases"][s]["status"] != "recognized_transformed" or not row["phases"][s]["receipts"] for s in ("train", "heldout")):
                        errors.append(f"positive recognition missing: {ident}/{row['variant']}")
                    names = [{r.get("generator") for r in row["phases"][s]["receipts"]} for s in ("train", "heldout")]
                    if not names[0] & names[1]:
                        errors.append(f"held-out reuse missing: {ident}/{row['variant']}")
                if audit:
                    nested_work = nested["phases"]["train"]["full_rank_counters"]["gen_infer_full_rank_identity_key_comparisons"]
                    sorted_work = sorted_join["phases"]["train"]["full_rank_counters"]["gen_infer_full_rank_identity_key_comparisons"]
                    if case["relation_count"] >= 32 and not sorted_work < nested_work:
                        errors.append(f"sorted key comparisons did not reduce at N={case['relation_count']}: {ident}")
            else:
                if kind in ("rank_deficient", "ambiguous_id") and not all(row["training_oracle_exact"] for row in pair):
                    errors.append(f"negative fixture mismatch: {ident}")
                if kind == "nonlinear" and any(row["training_oracle_exact"] for row in pair):
                    errors.append(f"nonlinear fixture unexpectedly linear: {ident}")
                for row in pair:
                    for stage in ("train", "heldout"):
                        phase = row["phases"][stage]
                        if phase["status"] != "minted" or phase["receipts"]:
                            errors.append(f"negative control recognized: {ident}/{row['variant']}/{stage}")
                    if row["final_generators"] != row["initial_generators"]:
                        errors.append(f"negative control minted generator: {ident}/{row['variant']}")

    timing = {}
    identity_work = {}
    for n in sorted({case["relation_count"] for case in cases}):
        ids = {case["id"] for case in cases if case["relation_count"] == n and case["kind"] == "positive"}
        timing[str(n)] = {}
        for arm in ("nested", "sorted"):
            rows = [row for row in workers if row["case"]["id"] in ids and row["variant"] == arm and not row["audit"]]
            timing[str(n)][arm] = {
                "train_median_wall_ms": statistics.median(row["phases"]["train"]["wall_ns"] for row in rows) / 1e6,
                "train_median_cpu_ms": statistics.median(row["phases"]["train"]["cpu_ns"] for row in rows) / 1e6,
                "heldout_median_wall_ms": statistics.median(row["phases"]["heldout"]["wall_ns"] for row in rows) / 1e6,
                "heldout_median_cpu_ms": statistics.median(row["phases"]["heldout"]["cpu_ns"] for row in rows) / 1e6,
                "median_process_maxrss_platform_units": statistics.median(row["process_maxrss_platform_units"] for row in rows),
            }
        identity_work[str(n)] = {}
        for arm in ("nested", "sorted"):
            rows = [row for row in workers if row["case"]["relation_count"] == n and row["case"]["kind"] == "positive" and row["variant"] == arm and row["audit"]]
            identity_work[str(n)][arm] = {
                stage: statistics.median(row["phases"][stage]["full_rank_counters"]["gen_infer_full_rank_identity_key_comparisons"] for row in rows)
                for stage in ("train", "heldout")}
    report = {"schema": "GenInferFullRankSortedJoinScaleV2_3Analysis", "capture_sha256": sha(path),
        "errors": errors, "gates_pass": not errors, "worker_count": len(workers),
        "audit_off_positive_summary": timing, "audit_on_identity_key_comparisons": identity_work,
        "interpretation_limit": "Authored 3-D frames on one host. Comparison counters are exact instrumented key-field comparisons; audit-off timing is from instrumented binaries and is diagnostic. RSS is process high-water mark including Python and substrate startup. No result estimates natural-task prevalence or overall capability."}
    out = path.with_name(path.stem.replace("_20261006", "_analysis_20261006") + ".json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(out.relative_to(ROOT)), "errors": errors, "gates_pass": not errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
