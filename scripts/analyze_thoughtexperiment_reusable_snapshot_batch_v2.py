#!/usr/bin/env python3
"""Independently gate and summarize the reusable-snapshot Thoughtexperiment panel."""
import gzip, hashlib, json, statistics
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from domains.engine_provenance import rust_source_fingerprint
RAW = ROOT / "evaluation/reports/thoughtexperiment_reusable_snapshot_batch_v2.json.gz"
OUT = ROOT / "evaluation/reports/thoughtexperiment_reusable_snapshot_batch_v2_analysis.json"
BACKENDS = ("native_full_copy_scoped", "native_shared_graph_pages_scoped", "native_reusable_snapshot")

def med(xs):
    return statistics.median(xs)

def change_counts(delta):
    names = ("nodes_added", "nodes_removed", "nodes_changed", "edges_added", "edges_removed")
    return {name: len(delta.get(name, [])) for name in names}

def signature(rows):
    return json.dumps(rows, sort_keys=True, separators=(",", ":"))

def main():
    with gzip.open(RAW, "rt", encoding="utf-8") as f:
        capture = json.load(f)
    assert capture["schema"] == "ThoughtexperimentFixedRevisionSixCandidateBatchV1"
    source_drift = [path for path, expected in capture["sources"].items()
                    if "sha256:" + hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected]
    assert not source_drift, f"captured sources changed after run: {source_drift}"
    assert rust_source_fingerprint(str(ROOT)) == capture["rust_source_fingerprint"]
    for artifact in (capture["runner"], capture["binary"]):
        path = Path(artifact["path"])
        assert "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
    assert capture["protocol"]["branch_backends"] == list(BACKENDS)
    assert len(capture["schedule"]) == 72
    indexed = {(c["size"], c["snapshot_backend"]): c for c in capture["comparisons"]}
    assert set(indexed) == {(n, b) for n in (10000, 50000) for b in BACKENDS}
    checks = {"comparisons": 0, "trials": 0, "cross_backend_exact_rows": 0,
              "exact_nested_outcome_gates": 0, "primary_guards": 0,
              "positive_negative_controls": 0}
    cells = []
    paired = []
    residual_by_size = defaultdict(dict)
    for size in (10000, 50000):
        per_backend = {}
        for backend in BACKENDS:
            c = indexed[(size, backend)]
            assert c["repeats"] == 5 and c["warmups"] == 1
            assert len(c["batch_trials"]) == len(c["standalone_trials"]) == 5
            assert c["exact_nested_residual_and_outcome_parity"]
            assert c["cross_backend_exact_output_parity"] and c["primary_graph_and_rules_preserved"]
            assert c["candidate_labels"] == c["batch_trials"][0]["candidate_labels"]
            assert len(c["candidate_labels"]) == 6
            checks["comparisons"] += 1
            checks["trials"] += 5
            checks["exact_nested_outcome_gates"] += 1
            checks["primary_guards"] += 1
            per_backend[backend] = c
            rows_by_candidate = defaultdict(list)
            for block in c["batch_trials"]:
                assert block["primary_graph_and_rules_unchanged"] and block["batch_primary_guard"]
                assert block["one_baseline_shared"] and len(block["rows"]) == 6
                positive = next(r for r in block["rows"] if r["candidate_label"] == "dedup_identity_fix")
                negative = next(r for r in block["rows"] if r["candidate_label"] == "add_match_guard(control)")
                assert positive["converges"] and not negative["converges"]
                checks["positive_negative_controls"] += 1
                for row in block["rows"]:
                    rows_by_candidate[row["candidate_label"]].append({
                        "conclusions": change_counts(row["conclusions"]),
                        "derived_only": change_counts(row["derived_only"]),
                    })
            residual_by_size[(size, backend)] = {
                label: values for label, values in rows_by_candidate.items()
            }
            summary = {
                "size": size, "snapshot_backend": backend,
                "batch_median_ms": med([t["elapsed_ms"] for t in c["batch_trials"]]),
                "standalone_median_ms": med([t["elapsed_ms"] for t in c["standalone_trials"]]),
                "batch_over_standalone_speedup": med([t["elapsed_ms"] for t in c["standalone_trials"]]) /
                                                  med([t["elapsed_ms"] for t in c["batch_trials"]]),
                "baseline_prediction_median_ms": med([t["timing_components_ms"]["baseline_prediction"] for t in c["batch_trials"]]),
                "reusable_snapshot_capture_median_ms": med([t["timing_components_ms"]["reusable_snapshot_capture"] for t in c["batch_trials"]]),
                "candidate_rehearsal_total_median_ms": med([sum(t["timing_components_ms"]["candidate_rehearsals"]) for t in c["batch_trials"]]),
                "candidate_branch_setup_median_ms": med([phase["branch_snapshot_and_setup"] for t in c["batch_trials"] for phase in t["candidate_phase_timings_ms"]]),
                "candidate_rule_patch_median_ms": med([phase["candidate_rule_patch"] for t in c["batch_trials"] for phase in t["candidate_phase_timings_ms"]]),
                "candidate_prediction_median_ms": med([phase["model_after_prediction"] for t in c["batch_trials"] for phase in t["candidate_phase_timings_ms"]]),
                "useful_candidates_per_batch": c["useful_candidates_per_batch"],
            }
            cells.append(summary)
        for block_index in range(5):
            reference = signature(per_backend[BACKENDS[0]]["batch_trials"][block_index]["rows"])
            assert all(signature(per_backend[b]["batch_trials"][block_index]["rows"]) == reference for b in BACKENDS)
            checks["cross_backend_exact_rows"] += 1
        reused = per_backend["native_reusable_snapshot"]
        direct = per_backend["native_shared_graph_pages_scoped"]
        batch_ratios = [d["elapsed_ms"] / r["elapsed_ms"] for d, r in
                        zip(direct["batch_trials"], reused["batch_trials"])]
        standalone_ratios = [d["elapsed_ms"] / r["elapsed_ms"] for d, r in
                             zip(direct["standalone_trials"], reused["standalone_trials"])]
        paired.append({"size": size,
            "batch_reusable_wins": sum(r["elapsed_ms"] < d["elapsed_ms"] for r, d in zip(reused["batch_trials"], direct["batch_trials"])),
            "batch_direct_over_reusable_wall_time_ratio_median": med(batch_ratios),
            "standalone_reusable_wins": sum(r["elapsed_ms"] < d["elapsed_ms"] for r, d in zip(reused["standalone_trials"], direct["standalone_trials"])),
            "standalone_direct_over_reusable_wall_time_ratio_median": med(standalone_ratios),
            "blocks": 5})
    # Summarize the emitted semantic residual sizes; these are changed-object
    # counts, not all attempted writes or page touches.
    residuals = []
    for size in (10000, 50000):
        for candidate in indexed[(size, BACKENDS[0])]["candidate_labels"]:
            count_sets = []
            for backend in BACKENDS:
                for payload in residual_by_size[(size, backend)][candidate]:
                    count_sets.append(payload)
            # All backend/block residual shapes must agree, then report the
            # exact distinct counts by candidate.
            assert all(x == count_sets[0] for x in count_sets)
            first = count_sets[0]
            residuals.append({"size": size, "candidate_label": candidate,
                "conclusions_changed_objects_per_block": first["conclusions"],
                "derived_only_changed_objects_per_block": first["derived_only"],
                "blocks": len(count_sets) // len(BACKENDS)})
    report = {
        "schema": "ThoughtexperimentReusableSnapshotBatchV2Analysis",
        "raw_gzip_sha256": "sha256:" + hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "analyzer_sha256": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "gates": checks,
        "cells": cells,
        "reusable_vs_direct_shared_page_paired": paired,
        "semantic_residual_changed_object_counts": residuals,
        "limits": [
            "One authored correction family, one host, and five measured blocks per size/backend.",
            "The candidate result graph conclusions and derived-only deltas contain zero changed nodes/edges in these rows; this workload does not stress graph-residual writes.",
            "Changed-object residual counts are not a count of every mutation attempt, cloned page, or touched memory location.",
            "The harness evaluates six branches sequentially; no concurrent serving, cancellation, reclamation bound, or vLLM-style KV-block adapter is measured.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"gates": checks, "cells": len(cells), "analysis": str(OUT.relative_to(ROOT))}, indent=2))

if __name__ == "__main__":
    main()
