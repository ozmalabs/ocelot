#!/usr/bin/env python3
"""Validate productive residual parity and summarize native snapshot costs."""
import hashlib, json, statistics, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/thoughtexperiment_productive_residual_snapshot_v1.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_productive_residual_snapshot_v1_analysis.json"
BACKENDS = ("native_full_copy_scoped", "native_shared_graph_pages_scoped", "native_reusable_snapshot")
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_productive_residual_snapshot_v1.py",
    "scripts/analyze_thoughtexperiment_productive_residual_snapshot_v1.py",
    "domains/imagination.py", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs", "runners/dsl/src/persist.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/_native.build.json",
)

def med(values):
    return statistics.median(values)

def main():
    from domains.engine_provenance import rust_source_fingerprint
    capture = json.loads(RAW.read_text())
    assert capture["schema"] == "ThoughtexperimentProductiveResidualSnapshotCaptureV1"
    assert capture["protocol"]["backends"] == list(BACKENDS)
    assert len(capture["workers"]) == 15
    assert len({w["worker_pid"] for w in capture["workers"]}) == 15
    drift = [path for path, expected in capture["source_sha256"].items()
             if "sha256:" + hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected]
    assert not drift, f"source drift since capture: {drift}"
    assert rust_source_fingerprint(str(ROOT)) == capture["engine_fingerprint"]
    for artifact in (capture["runner"], capture["binary"]):
        assert "sha256:" + hashlib.sha256(Path(artifact["path"]).read_bytes()).hexdigest() == artifact["sha256"]
    grouped = defaultdict(list)
    for worker in capture["workers"]:
        assert worker["size"] in (0, 10000, 50000)
        assert worker["primary_unchanged"] and worker["later_snapshot_fork_isolated"]
        assert worker["exact_backend_residual_parity"] and worker["nonempty_derived_residual"]
        assert worker["backend_order"] == (list(BACKENDS) if worker["repeat_index"] % 2 == 0 else list(reversed(BACKENDS)))
        assert set(worker["backends"]) == set(BACKENDS)
        per_backend_outcomes = []
        for backend in BACKENDS:
            arm = worker["backends"][backend]
            assert len(arm["branches"]) == 5
            outcomes = []
            for ordinal, branch in enumerate(arm["branches"]):
                assert branch["ordinal"] == ordinal
                outcome = branch["outcome"]
                counts = branch["derived_only_counts"]
                assert outcome["n_conclusions"] > 0
                assert outcome["steps_run"] == 1 and outcome["converged"]
                assert branch["terminal_probe_progress"] == 0
                assert all(counts[key] > 0 for key in
                           ("nodes_added", "nodes_changed", "nodes_removed", "edges_added", "edges_removed"))
                outcomes.append(outcome)
            per_backend_outcomes.append(outcomes)
        assert all(outcomes == per_backend_outcomes[0] for outcomes in per_backend_outcomes[1:])
        grouped[worker["size"]].append(worker)
    summaries = []
    pairwise = []
    residuals = []
    for size in (0, 10000, 50000):
        workers = sorted(grouped[size], key=lambda w: w["repeat_index"])
        assert len(workers) == 5
        for backend in BACKENDS:
            arms = [w["backends"][backend] for w in workers]
            branches = [b for arm in arms for b in arm["branches"]]
            capture_ms = med([w["snapshot_capture_ms"] for w in workers])
            summaries.append({
                "size": size, "backend": backend, "workers": len(workers), "branches": len(branches),
                "batch_wall_median_ms": med([arm["batch_wall_ms"] for arm in arms]),
                "reusable_snapshot_capture_median_ms": capture_ms if backend == "native_reusable_snapshot" else 0.0,
                "batch_plus_capture_median_ms": med([arm["batch_wall_ms"] for arm in arms]) +
                                                (capture_ms if backend == "native_reusable_snapshot" else 0.0),
                "branch_wall_median_ms": med([b["wall_ms"] for b in branches]),
                "branch_snapshot_and_rule_setup_median_ms": med([b["phase_timings_ms"]["branch_snapshot_and_rule_setup"] for b in branches]),
                "hypothesis_preparation_median_ms": med([b["phase_timings_ms"]["grounding_and_hypothesis_preparation"] for b in branches]),
                "collapse_tick_median_ms": med([b["phase_timings_ms"]["collapse_tick"] for b in branches]),
                "residual_readout_median_ms": med([b["phase_timings_ms"]["residual_readout"] for b in branches]),
            })
            first = workers[0]["backends"][backend]["branches"][0]
            residuals.append({"size": size, "backend": backend,
                "conclusions_changed_objects": first["conclusions_counts"],
                "derived_only_changed_objects": first["derived_only_counts"],
                "every_branch_same_counts": all(b["derived_only_counts"] == first["derived_only_counts"] and
                    b["conclusions_counts"] == first["conclusions_counts"] for w in workers
                    for b in w["backends"][backend]["branches"])})
        for other in ("native_full_copy_scoped", "native_shared_graph_pages_scoped"):
            ratios = [w["backends"][other]["batch_wall_ms"] /
                      w["backends"]["native_reusable_snapshot"]["batch_wall_ms"] for w in workers]
            pairwise.append({"size": size, "comparison": other + "_over_reusable_wall_ratio",
                "median": med(ratios),
                "reusable_wins": sum(w["backends"]["native_reusable_snapshot"]["batch_wall_ms"] <
                                     w["backends"][other]["batch_wall_ms"] for w in workers),
                "blocks": len(workers)})
    report = {
        "schema": "ThoughtexperimentProductiveResidualSnapshotAnalysisV1",
        "raw_sha256": "sha256:" + hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "analyzer_sha256": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "gates": {"workers": 15, "fresh_worker_pids": 15, "size_cells": 3,
                  "repeats_per_size": 5, "branches_per_backend": 5,
                  "exact_nonempty_residual_parity": True, "primary_unchanged": True,
                  "later_snapshot_fork_isolated": True, "current_sources_and_engine": True},
        "cells": summaries,
        "paired_backend_comparisons": pairwise,
        "residual_shapes": residuals,
        "limits": [
            "One authored hypothesis-driven rule fixture, one focus topology, and one host.",
            "Five sequential alternatives per worker; concurrent branch execution is not measured.",
            "No residual adoption/merge into the primary is performed; return and adoption are separate lifecycle operations.",
            "Changed-object counts are semantic residual size, not every mutation attempt, cloned page, or touched byte.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"gates": report["gates"], "analysis": str(OUT.relative_to(ROOT))}, indent=2))

if __name__ == "__main__":
    main()
