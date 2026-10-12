#!/usr/bin/env python3
"""Verify source-specific NodesOfType trace capture hashes and event accounting."""
from __future__ import annotations
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v2_20261003.json"
RAW = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v2_workers_raw_20261003.json.gz"
OUTPUT = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v2_analysis_20261003.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def raw_sha(path: Path) -> str:
    h = hashlib.sha256()
    with gzip.open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    summary = json.loads(CAPTURE.read_text())
    archive_hash = sha(RAW)
    decompressed_hash = raw_sha(RAW)
    with gzip.open(RAW, "rt") as f:
        raw = json.load(f)
    query_rows = candidate_rows = query_count = candidate_count = 0
    empty_rows = empty_count = 0
    event_rows = collections.Counter()
    event_counts = collections.Counter()
    by_request = {}
    for run in raw["runs"]:
        cap = run["base_worker"]["capture"]
        for index, req in enumerate(cap["requests"]):
            counts = collections.Counter()
            rows = collections.Counter()
            for row in req["access_rows"]:
                kind = str(row[1])
                if kind in {"term_typed_population_query", "term_typed_population_candidate",
                            "term_nodes_of_type_query", "term_nodes_of_type_candidate"}:
                    rows[kind] += 1
                    counts[kind] += int(row[6])
            key = f"rep{run['replicate']}_request{index}"
            by_request[key] = {"prompt": req["prompt"], "event_rows": dict(rows),
                               "event_counts": dict(counts)}
            event_rows.update(rows)
            event_counts.update(counts)
    for request in raw["event_summary"].values():
        query_rows += len(request["query_rows"])
        candidate_rows += len(request["candidate_rows"])
        query_count += sum(int(row["count"]) for row in request["query_rows"])
        candidate_count += sum(int(row["count"]) for row in request["candidate_rows"])
        empty_rows += len(request["empty_candidate_query_groups"])
        empty_count += sum(int(row["count"]) for row in request["empty_candidate_query_groups"])
    checks = {
        "compressed_and_decompressed_hashes_match": archive_hash == summary["raw_compressed_sha256"]
            and decompressed_hash == summary["raw_sha256"],
        "all_capture_gates_pass": all(summary["checks"].values()),
        "three_workers_six_requests": len(raw["runs"]) == 3 and len(by_request) == 6,
        "source_specific_rows_match_summary": query_rows == summary["summary"]["new_query_event_rows"]
            and candidate_rows == summary["summary"]["new_candidate_event_rows"],
        "source_specific_counts_positive": query_count > 0 and candidate_count >= query_count,
        "all_four_population_event_kinds_observed": all(event_rows[k] > 0 for k in (
            "term_typed_population_query", "term_typed_population_candidate",
            "term_nodes_of_type_query", "term_nodes_of_type_candidate")),
    }
    result = {
        "schema_version": 1,
        "inputs": {"capture_summary_sha256": sha(CAPTURE),
                    "raw_archive_sha256": archive_hash,
                    "raw_decompressed_sha256": decompressed_hash},
        "checks": checks,
        "capture_checks": summary["checks"],
        "source_specific_nodes_of_type": {"query_rows": query_rows, "query_event_count": query_count,
                                           "candidate_rows": candidate_rows,
                                           "candidate_event_count": candidate_count,
                                           "empty_candidate_query_groups": empty_rows,
                                           "empty_query_event_count": empty_count},
        "typed_population_helper_and_direct_site_events": {
            "rows_by_kind": dict(event_rows), "event_counts_by_kind": dict(event_counts)},
        "by_request": by_request,
        "claim_boundary": (
            "Events 36/37 identify the direct NodesOfType evaluator; 34/35 remain helper population events. "
            "This replay establishes live instrumentation and semantic parity on one authored two-prompt fixture, "
            "not complete dependency recall, locality prevalence, or instrumentation overhead."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise SystemExit("archive or source-specific event accounting gate failed")


if __name__ == "__main__":
    main()
