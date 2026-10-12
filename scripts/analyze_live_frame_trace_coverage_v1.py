#!/usr/bin/env python3
"""Join current source trace coverage with the live frame-interface capture."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_workers_raw_20261003.json.gz"
CAPTURE = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_20261003.json"
SOURCE_AUDIT = ROOT / "evaluation/reports/substrate_runtime_access_trace_coverage_v1_2_20261003.json"
SOURCE_AUDIT_RUNNER = ROOT / "scripts/substrate_runtime_access_trace_coverage_audit_v1.py"
OUT = ROOT / "evaluation/reports/live_frame_trace_coverage_v1_20261003.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source_audit = json.loads(SOURCE_AUDIT.read_text())
    capture = json.loads(CAPTURE.read_text())
    if sha(SOURCE_AUDIT_RUNNER) != source_audit["audit_runner_sha256"]:
        raise SystemExit("trace coverage audit runner changed since source inventory capture")
    for relative, expected in source_audit["source_sha256"].items():
        if sha(ROOT / {
            "access_trace": "runners/dsl/src/access_trace.rs",
            "term": "runners/dsl/src/term.rs",
            "shape_decode": "runners/dsl/src/shape_decode.rs",
            "rewrite": "runners/dsl/src/rewrite.rs",
            "jit": "runners/dsl/src/jit.rs",
            "world_adapter": "substrate/world_adapter.py",
        }[relative]) != expected:
            raise SystemExit(f"source changed since trace audit: {relative}")
    if sha(RAW) != capture["raw_compressed_sha256"]:
        raise SystemExit("compressed capture hash differs from capture summary")
    digest = hashlib.sha256()
    with gzip.open(RAW, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != capture["raw_sha256"]:
        raise SystemExit("decompressed capture hash differs from capture summary")
    with gzip.open(RAW, "rt", encoding="utf-8") as stream:
        raw = json.load(stream)

    access_summary = []
    work_summary = []
    access_kind_totals: Counter[str] = Counter()
    work_kind_totals: Counter[str] = Counter()
    work_kind_uid0: Counter[str] = Counter()
    total_access_weight = total_work_units = total_uid0_work = 0
    access_rule_uid_zero_rows = 0
    request_count = 0
    for run in raw["runs"]:
        for index, request in enumerate(run["requests"]):
            request_count += 1
            by_kind: Counter[str] = Counter()
            no_node_by_kind: Counter[str] = Counter()
            rule_uids: set[int] = set()
            access_weight = 0
            for row in request["access_rows"]:
                rule_uid, kind = int(row[0]), str(row[1])
                weight = int(row[6])
                access_weight += weight
                by_kind[kind] += weight
                if row[2] is None:
                    no_node_by_kind[kind] += weight
                rule_uids.add(rule_uid)
                access_rule_uid_zero_rows += int(rule_uid == 0)
            total_access_weight += access_weight
            access_kind_totals.update(by_kind)
            access_summary.append({
                "replicate": run["replicate"], "turn": index,
                "prompt": request["prompt"], "access_weight": access_weight,
                "distinct_access_rows": len(request["access_rows"]),
                "distinct_rule_uids": len(rule_uids),
                "rule_uid_zero_rows": sum(1 for row in request["access_rows"] if int(row[0]) == 0),
                "weight_by_event_kind": dict(sorted(by_kind.items())),
                "weight_without_concrete_node_id_by_event_kind": dict(sorted(no_node_by_kind.items())),
            })

            work_by_kind: Counter[str] = Counter()
            uid0_by_kind: Counter[str] = Counter()
            operations: dict[int, set[str]] = {}
            work_units = uid0_units = 0
            for row in request["work_rows"]:
                operation_id, rule_uid, kind, _subject, units = (
                    int(row[0]), int(row[1]), str(row[2]), row[3], int(row[4])
                )
                work_units += units
                work_by_kind[kind] += units
                operations.setdefault(operation_id, set()).add(kind)
                if rule_uid == 0:
                    uid0_units += units
                    uid0_by_kind[kind] += units
            total_work_units += work_units
            total_uid0_work += uid0_units
            work_kind_totals.update(work_by_kind)
            work_kind_uid0.update(uid0_by_kind)
            work_summary.append({
                "replicate": run["replicate"], "turn": index,
                "prompt": request["prompt"], "distinct_work_rows": len(request["work_rows"]),
                "operation_count": len(operations), "work_units": work_units,
                "rule_uid_zero_work_units": uid0_units,
                "rule_uid_zero_fraction": uid0_units / work_units if work_units else None,
                "work_units_by_event_kind": dict(sorted(work_by_kind.items())),
                "rule_uid_zero_work_units_by_kind": dict(sorted(uid0_by_kind.items())),
            })

    event_names = source_audit["event_kinds"]
    unknown_access = sorted(set(access_kind_totals) - set(event_names.values()))
    unknown_work = sorted(set(work_kind_totals) - set(event_names.values()))
    checks = {
        "source_audit_hashes_match_current_sources": True,
        "capture_archive_and_payload_hashes_match": True,
        "all_observed_access_kinds_have_source_names": not unknown_access,
        "all_observed_work_kinds_have_source_names": not unknown_work,
        "six_workers_two_requests_each": len(raw["runs"]) == 3 and request_count == 6,
        "access_trace_has_no_zero_rule_uid_rows": access_rule_uid_zero_rows == 0,
    }
    result = {
        "schema_version": 1,
        "run_id": "live-frame-trace-coverage-v1-20261003",
        "capture_summary_path": str(CAPTURE.relative_to(ROOT)),
        "capture_summary_sha256": sha(CAPTURE),
        "raw_archive_path": str(RAW.relative_to(ROOT)),
        "raw_archive_sha256": sha(RAW),
        "raw_uncompressed_sha256": digest.hexdigest(),
        "source_audit_path": str(SOURCE_AUDIT.relative_to(ROOT)),
        "source_audit_sha256": sha(SOURCE_AUDIT),
        "analysis_script_sha256": sha(Path(__file__).resolve()),
        "source_sha256": source_audit["source_sha256"],
        "checks": checks,
        "summary": {
            "requests": request_count,
            "total_weighted_access_events": total_access_weight,
            "rule_uid_zero_access_rows_observed": access_rule_uid_zero_rows,
            "total_scheduler_and_work_units": total_work_units,
            "work_units_outside_rule_uid": total_uid0_work,
            "work_units_outside_rule_uid_fraction": total_uid0_work / total_work_units if total_work_units else None,
            "access_weight_by_event_kind": dict(sorted(access_kind_totals.items())),
            "work_units_by_event_kind": dict(sorted(work_kind_totals.items())),
            "work_units_outside_rule_uid_by_kind": dict(sorted(work_kind_uid0.items())),
            "unknown_access_kinds": unknown_access,
            "unknown_work_kinds": unknown_work,
        },
        "per_request_access": access_summary,
        "per_request_work": work_summary,
        "interpretation_boundary": "The source audit documents known instrumentation paths and omissions; the captured trace reports observed event mix only. Access events with UID zero cannot appear because note() discards them. Scheduler/work counters expose some UID-zero work, but do not account for all Python adapter work, callback side effects, failed matcher candidates, uninstrumented Term reads, or every native scan. These counts do not estimate total dependency recall.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "summary": result["summary"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("live frame trace/source crosswalk gate failed")


if __name__ == "__main__":
    main()
