#!/usr/bin/env python3
"""Independent semantic audit for the synthetic shared-prefix probe."""
from __future__ import annotations
import argparse, hashlib, json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = "evaluation/substrate_capability/cow_shared_prefix_adapter_v1.py"
ANALYZER = "scripts/analyze_cow_shared_prefix_adapter_v1.py"
SEMANTIC_FIELDS = (
    "base_revision", "prefix_before_digest", "request_a_digest", "request_b_digest",
    "cancelled_request_block_ids", "stale_revision_refused", "stale_rejection_atomic",
    "sibling_isolation", "sibling_survives_cancel", "later_fork_clean",
    "reusable_after_cancel", "no_active_requests_after_cancel",
    "logical_active_request_blocks_after_cancel",
)
GATES = (
    "stale_revision_refused", "stale_rejection_atomic", "sibling_isolation",
    "sibling_survives_cancel", "later_fork_clean", "reusable_after_cancel",
    "no_active_requests_after_cancel",
)

def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", nargs="?", default="evaluation/reports/cow_shared_prefix_adapter_v1.json")
    args = parser.parse_args()
    path = Path(args.capture)
    if not path.is_absolute():
        path = ROOT / path
    capture = json.loads(path.read_text())
    if capture.get("schema") != "CowSharedPrefixAdapterCaptureV1":
        raise SystemExit("unexpected capture schema")
    if capture["source_sha256"].get(RUNNER) != sha(ROOT / RUNNER):
        raise SystemExit("runner source hash mismatch")
    analyzer_hash = capture["source_sha256"].get(ANALYZER)
    if analyzer_hash != sha(ROOT / ANALYZER):
        raise SystemExit("analyzer source hash mismatch")
    for source, expected_hash in capture["source_sha256"].items():
        if sha(ROOT / source) != expected_hash:
            raise SystemExit(f"captured source changed: {source}")
    binary = Path(capture["binary"]["path"])
    if sha(binary) != capture["binary"]["sha256"]:
        raise SystemExit("native binary hash mismatch")
    sizes = capture["protocol"]["background_sizes"]
    repeats = capture["protocol"]["repeats"]
    expected = len(sizes) * repeats * 2
    rows = capture["rows"]
    if len(rows) != expected:
        raise SystemExit(f"expected {expected} measured workers, found {len(rows)}")
    cells = []
    for size in sizes:
        for backend in capture["protocol"]["backends"]:
            cell = [r for r in rows if r["size_background_nodes"] == size and r["backend"] == backend]
            if len(cell) != repeats or len({r["pid"] for r in cell}) != repeats:
                raise SystemExit(f"worker/repeat count mismatch: {size=} {backend=}")
            if not all(all(r.get(gate) is True for gate in GATES) for r in cell):
                raise SystemExit(f"semantic gate failed: {size=} {backend=}")
            cells.append({"size_background_nodes": size, "backend": backend,
                          "repeats": len(cell), "all_gates_pass": True,
                          "median_timings_ms": {key: statistics.median(r["timings_ms"][key] for r in cell)
                                                for key in cell[0]["timings_ms"]},
                          "median_pss_bytes": {stage: statistics.median(
                              r["memory_samples_bytes"][stage].get("Pss", 0) for r in cell)
                              for stage in cell[0]["memory_samples_bytes"]}})
        eager = [r for r in rows if r["size_background_nodes"] == size and r["backend"] == "full_copy"]
        default = [r for r in rows if r["size_background_nodes"] == size and r["backend"] == "public_default"]
        def signature(row):
            return tuple(row[k] for k in SEMANTIC_FIELDS)
        by_rep_e = {r["repetition"]: signature(r) for r in eager}
        by_rep_d = {r["repetition"]: signature(r) for r in default}
        if by_rep_e != by_rep_d:
            raise SystemExit(f"default/eager semantic parity mismatch: {size=}")
    analysis = {"schema": "CowSharedPrefixAdapterAnalysisV1", "capture": str(path),
                "worker_count": len(rows), "size_count": len(sizes), "gates_per_worker": list(GATES),
                "cells": cells, "default_eager_exact_parity": True,
                "claim_boundary": "synthetic shared-prefix lifecycle compatibility only; no KV-cache, vLLM, scheduler, serving throughput, or serving memory claim"}
    out = ROOT / "evaluation/reports/cow_shared_prefix_adapter_v1_analysis.json"
    out.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(rows), "cells": len(cells), "all_gates_pass": True,
                      "analysis": str(out.relative_to(ROOT))}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
