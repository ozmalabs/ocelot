#!/usr/bin/env python3
"""Join typed-population trace rows to live rule syntax, retaining attribution limits."""
from __future__ import annotations
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v1_20261003.json"
RAW = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v1_workers_raw_20261003.json.gz"
MANIFEST = ROOT / "evaluation/reports/live_operation_scope_manifest_v1_20261003.json"
OUTPUT = ROOT / "evaluation/reports/nodes_of_type_trace_capture_v1_analysis_20261003.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def decompressed_sha(path: Path) -> str:
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
    manifest = json.loads(MANIFEST.read_text())
    raw_archive_sha = sha(RAW)
    raw_json_sha = decompressed_sha(RAW)
    with gzip.open(RAW, "rt") as f:
        raw = json.load(f)
    scope = {int(row["rule_uid"]): row for row in manifest["per_rule_operation_scopes"]}
    stats = {"query_rows": collections.Counter(), "candidate_rows": collections.Counter(),
             "query_count": collections.Counter(), "candidate_count": collections.Counter(),
             "empty_query_rows": collections.Counter(), "empty_query_count": collections.Counter()}
    empty_keys = collections.defaultdict(set)
    observed_uids = set()
    for request_id, request in raw["event_summary"].items():
        for row in request["query_rows"]:
            uid = int(row["rule_uid"]); observed_uids.add(uid)
            class_name = ("rule_definition_contains_NodesOfType"
                          if scope.get(uid, {}).get("term_variant_counts", {}).get("NodesOfType", 0)
                          else "rule_definition_lacks_NodesOfType_syntax")
            stats["query_rows"][class_name] += 1
            stats["query_count"][class_name] += int(row["count"])
            key = (uid, str(row.get("node_type")))
            has_candidate = any(int(c["rule_uid"]) == uid and str(c.get("node_type")) == key[1]
                                for c in request["candidate_rows"])
            if not has_candidate:
                stats["empty_query_rows"][class_name] += 1
                stats["empty_query_count"][class_name] += int(row["count"])
                empty_keys[class_name].add(key)
        for row in request["candidate_rows"]:
            uid = int(row["rule_uid"]); observed_uids.add(uid)
            class_name = ("rule_definition_contains_NodesOfType"
                          if scope.get(uid, {}).get("term_variant_counts", {}).get("NodesOfType", 0)
                          else "rule_definition_lacks_NodesOfType_syntax")
            stats["candidate_rows"][class_name] += 1
            stats["candidate_count"][class_name] += int(row["count"])
    result = {
        "schema_version": 1,
        "inputs": {"capture_summary_sha256": sha(CAPTURE), "raw_archive_sha256": raw_archive_sha,
                    "raw_decompressed_sha256": raw_json_sha, "operation_manifest_sha256": sha(MANIFEST)},
        "checks": {
            "raw_hashes_match_capture_summary": raw_archive_sha == summary["raw_compressed_sha256"]
                and raw_json_sha == summary["raw_sha256"],
            "captured_worker_gates_pass": all(summary["checks"].values()),
            "all_event_rule_uids_resolve_in_operation_manifest": observed_uids <= set(scope),
            "six_request_summaries_present": len(raw["event_summary"]) == 6,
        },
        "capture_checks": summary["checks"],
        "aggregate": summary["summary"],
        "rule_syntax_join": {
            "classification": "whether the exported definition syntax contains NodesOfType; not attribution of a shared event to a specific evaluator site",
            "query_event_rows_by_rule_class": dict(stats["query_rows"]),
            "query_event_count_by_rule_class": dict(stats["query_count"]),
            "candidate_event_rows_by_rule_class": dict(stats["candidate_rows"]),
            "candidate_event_count_by_rule_class": dict(stats["candidate_count"]),
            "empty_query_rows_by_rule_class": dict(stats["empty_query_rows"]),
            "empty_query_count_by_rule_class": dict(stats["empty_query_count"]),
            "unique_empty_rule_type_groups_by_rule_class": {k: len(v) for k, v in empty_keys.items()},
        },
        "claim_boundary": (
            "Kinds 34/35 are shared with other typed-population helpers. The capture establishes live emission, "
            "empty-result visibility, and candidate cardinality for typed-population paths. Syntax joining is "
            "correlational; it does not attribute every row to a NodesOfType AST evaluation or establish complete dependencies."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if not all(result["checks"].values()):
        raise SystemExit("one or more archive or join checks failed")


if __name__ == "__main__":
    main()
