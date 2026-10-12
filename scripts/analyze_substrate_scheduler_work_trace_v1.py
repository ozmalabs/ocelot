#!/usr/bin/env python3
"""Independent checks for the scheduler/deferred work trace fixture."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_scheduler_work_trace_v1_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_scheduler_work_trace_v1_analysis_20260928.json"
FAMILIES = {"rule_edits": 1, "fb_samples": 3}
SCHEDULER = {
    "scheduler_pass": "scheduler_passes",
    "scheduler_external_poll_slots": "scheduler_external_poll_slots",
    "scheduler_fixedpoint_probe_slots": "scheduler_fixedpoint_probe_slots",
    "scheduler_dirty_vector_slots": "scheduler_dirty_vector_slots",
    "scheduler_selected_rules": "scheduler_selected_rules",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    raw = json.loads(args.input.read_text())
    runs = raw["runs"]
    checks: dict[str, bool] = {
        "three_workers": len(runs) == 3,
        "three_fresh_processes": len({r["pid"] for r in runs}) == 3,
        "replicates_zero_one_two": sorted(r["replicate"] for r in runs) == [0, 1, 2],
        "top_level_source_lock_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "worker_source_lock_stable": all(r["before"] == raw["locked_inputs"] == r["after"] for r in runs),
    }
    profiles = []
    for run in runs:
        scale = run["scale_counters"]
        work_rows = run["work_rows"]
        weighted: Counter[tuple[str, int | None, int]] = Counter()
        operation_ids = set()
        for row in work_rows:
            if len(row) != 5:
                raise SystemExit("unexpected operation-work row schema")
            operation, uid, kind, subject, units = row
            operation_ids.add(int(operation))
            weighted[(str(kind), subject, int(uid))] += int(units)
        work_totals = Counter()
        for (kind, subject, _uid), units in weighted.items():
            work_totals[(kind, subject)] += units

        gates = {
            "fixed_point": run["report"]["status"] == "fixed_point",
            "two_progress_steps": run["report"]["progress_steps"] == 2,
            "three_passes": run["report"]["passes_completed"] == 3,
            "one_seen_edge": run["seen_edges"] == 1,
            "four_grid_cells": run["grid_cells"] == 4,
            "one_operation_id": len(operation_ids) == 1,
            "work_trace_no_drops": run["work_dropped"] == 0,
            "access_trace_no_drops": run["access_trace_dropped"] == 0,
            "scheduler_work_matches_scale_counters": all(
                work_totals[(kind, None)] == int(scale[counter])
                for kind, counter in SCHEDULER.items()
            ),
        }
        for family, subject in FAMILIES.items():
            prefix = f"deferred_queue:{family}:"
            gates[f"{family}_enqueues_match"] = (
                work_totals[("deferred_queue_enqueue_items", subject)]
                == int(scale[prefix + "enqueued_items"])
            )
            gates[f"{family}_drain_batches_match"] = (
                work_totals[("deferred_queue_drain_batches", subject)]
                == int(scale[prefix + "drain_batches"])
            )
            gates[f"{family}_drained_items_match"] = (
                work_totals[("deferred_queue_drained_items", subject)]
                == int(scale[prefix + "drained_items"])
            )
            gates[f"{family}_producer_and_drain_uids"] = (
                all(uid > 0 for (kind, sub, uid), units in weighted.items()
                    if kind == "deferred_queue_enqueue_items" and sub == subject and units > 0)
                and work_totals[("deferred_queue_drain_batches", subject)]
                   == weighted[("deferred_queue_drain_batches", subject, 0)]
                and work_totals[("deferred_queue_drained_items", subject)]
                   == weighted[("deferred_queue_drained_items", subject, 0)]
            )
        allowed_kinds = set(SCHEDULER) | {
            "deferred_queue_enqueue_items", "deferred_queue_drain_batches",
            "deferred_queue_drained_items",
        }
        gates["only_registered_work_kinds"] = all(kind in allowed_kinds for kind, _subject, _uid in weighted)
        profiles.append({
            "replicate": run["replicate"],
            "graph_sha256": run["graph_sha256"],
            "work_operation_ids": sorted(operation_ids),
            "work_totals": {f"{kind}:{subject}": units for (kind, subject), units in sorted(work_totals.items(), key=lambda x: (x[0][0], -1 if x[0][1] is None else x[0][1]))},
            "counter_totals": {k: v for k, v in scale.items()
                               if (k.startswith("scheduler_") or k.startswith("deferred_queue:"))
                               and not k.endswith("_ns")},
            "trace_weighted_events": run["access_trace_weighted_events"],
            "trace_distinct_rows": run["access_trace_distinct_rows"],
            "timing_counters_ns": {k: v for k, v in scale.items()
                                    if k.endswith("_ns") and (k.startswith("scheduler_") or k.startswith("deferred_queue:"))},
            "checks": gates,
        })
    for key in ("graph_sha256", "work_totals", "counter_totals", "trace_weighted_events", "trace_distinct_rows"):
        checks[f"workers_match_{key}"] = all(p[key] == profiles[0][key] for p in profiles[1:])
    checks["per_worker_semantic_and_counter_gates"] = all(all(p["checks"].values()) for p in profiles)
    result = {
        "schema_version": 1,
        "analysis_id": args.output.stem,
        "input_path": str(args.input.relative_to(ROOT) if args.input.is_relative_to(ROOT) else args.input),
        "claim_boundary": "One synthetic rule_edits/fb_samples fixture and one monolithic run_rules operation per worker. Exact work/counter parity does not establish scheduler trace recall or general workload coverage.",
        "worker_profiles": profiles,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": result["all_checks_pass"], "output": str(args.output)}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("scheduler work trace analysis failed")


if __name__ == "__main__":
    main()
