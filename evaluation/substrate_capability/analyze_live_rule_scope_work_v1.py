#!/usr/bin/env python3
"""Independently summarize reproducible native work rows in live-scope capture."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_3_workers_raw_20261005.json.gz"
SUMMARY = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_3_20261005.json"
OUT = ROOT / "evaluation/reports/live_rule_scope_work_analysis_v1_20261005.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    raw_gz = RAW.read_bytes()
    payload = gzip.decompress(raw_gz)
    raw_sha = sha(payload)
    summary = json.loads(SUMMARY.read_text())
    if raw_sha != summary["raw_uncompressed_sha256"] or not all(summary["checks"].values()):
        raise SystemExit("capture archive failed its summary digest or protocol gates")
    raw = json.loads(payload)
    by_prompt_and_worker = {}
    all_rows: Counter[tuple] = Counter()
    row_shapes = Counter()
    dropped = 0
    prompt_workers: dict[str, set[int]] = defaultdict(set)
    prompt_work: dict[str, dict[int, Counter]] = defaultdict(dict)
    prompt_access: dict[str, dict[int, Counter]] = defaultdict(dict)
    for run in raw["runs"]:
        worker = int(run["replicate"])
        for request in run["capture"]["requests"]:
            prompt = str(request["prompt"])
            rows = request["work_rows"]
            dropped += int(request["work_dropped_events"])
            prompt_workers[prompt].add(worker)
            work_counter = Counter()
            for row in rows:
                if len(row) != 5:
                    raise SystemExit(f"unexpected native work-row shape: {row!r}")
                scope, op_id, kind, subject, units = row
                key = (int(op_id), str(kind), None if subject is None else str(subject))
                work_counter[key] += int(units)
                all_rows[key] += int(units)
                row_shapes[len(row)] += 1
            prompt_work[prompt][worker] = work_counter
            access_counter = Counter()
            for row in request["access_rows"]:
                key = (int(row[0]), str(row[1]), str(row[3]), str(row[4]))
                access_counter[key] += int(row[6])
            prompt_access[prompt][worker] = access_counter
    if dropped:
        raise SystemExit(f"native work trace dropped {dropped} events")
    parity = {}
    for prompt, workers in sorted(prompt_workers.items()):
        ids = sorted(workers)
        same_work = len(ids) == 3 and all(prompt_work[prompt][wid] == prompt_work[prompt][ids[0]] for wid in ids[1:])
        same_access = len(ids) == 3 and all(prompt_access[prompt][wid] == prompt_access[prompt][ids[0]] for wid in ids[1:])
        parity[prompt] = {"worker_ids": ids, "same_work_rows": same_work, "same_access_rows": same_access}
    if not all(row["same_work_rows"] and row["same_access_rows"] for row in parity.values()):
        raise SystemExit(f"per-prompt work/access parity failed: {parity}")

    by_kind = Counter()
    by_op_and_kind = Counter()
    for (op_id, kind, subject), units in all_rows.items():
        by_kind[kind] += units
        by_op_and_kind[(op_id, kind)] += units
    result = {
        "schema": "LiveRuleScopeWorkAnalysisV1",
        "run_id": "live-rule-scope-work-analysis-v1-20261005",
        "raw_path": str(RAW.relative_to(ROOT)),
        "raw_gzip_sha256": sha(raw_gz),
        "raw_uncompressed_sha256": raw_sha,
        "capture_summary_sha256": sha(SUMMARY.read_bytes()),
        "summary": {
            "workers": len(raw["runs"]),
            "prompts": len(parity),
            "raw_work_row_count_across_workers": sum(row_shapes.values()),
            "work_row_shapes": dict(row_shapes),
            "dropped_work_events": dropped,
            "total_work_units_across_workers": sum(all_rows.values()),
            "work_units_by_kind_across_workers": dict(sorted(by_kind.items())),
            "work_units_by_operation_and_kind_across_workers": [
                {"operation_id": op_id, "kind": kind, "units": units}
                for (op_id, kind), units in sorted(by_op_and_kind.items())
            ],
            "prompt_worker_parity": parity,
        },
        "checks": {
            "capture_summary_matches_raw": True,
            "no_work_events_dropped": dropped == 0,
            "all_three_worker_traces_reproduce_per_prompt": all(x["same_work_rows"] for x in parity.values()),
            "all_three_worker_access_traces_reproduce_per_prompt": all(x["same_access_rows"] for x in parity.values()),
        },
        "claim_boundary": "Work rows report the native work counters present in this captured route. They do not directly count dynamic helper invocations or identify all graph nodes visited; syntax and helper scope findings remain static. Units are summed across three replicated workers for storage and must not be interpreted as one-request cost.",
    }
    result["checks"]["all_checks_pass"] = all(result["checks"].values())
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "summary": result["summary"], "checks": result["checks"]}, indent=2))
    if not result["checks"]["all_checks_pass"]:
        raise SystemExit("work-trace analysis gates failed")


if __name__ == "__main__":
    main()
