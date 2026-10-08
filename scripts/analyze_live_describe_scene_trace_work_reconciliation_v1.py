#!/usr/bin/env python3
"""Reconcile a locked scene-description trace with independent work counters.

This is a post-hoc analyzer for the v1.1 whole-request capture. It measures
which instrumented effect counts reconcile exactly and records trace fields
that are absent; it does not estimate general trace recall.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "evaluation/reports/live_describe_scene_whole_request_audit_v1_1_workers_raw_20260927.json"
DEFAULT_OUTPUT = ROOT / "evaluation/reports/live_describe_scene_trace_work_reconciliation_v1_20260928.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    raw = json.loads(args.input.read_text())
    runs = raw.get("runs")
    if not isinstance(runs, list):
        raise SystemExit("capture has no runs list")

    audited = [r for r in runs if r.get("arm") == "audited"]
    plain = [r for r in runs if r.get("arm") == "untraced"]
    if len(audited) != 3 or len(plain) != 3:
        raise SystemExit(f"expected 3 audited and 3 untraced runs; got {len(audited)} and {len(plain)}")
    audited.sort(key=lambda r: r["replicate"])
    plain.sort(key=lambda r: r["replicate"])
    if [r["replicate"] for r in audited] != [0, 1, 2] or [r["replicate"] for r in plain] != [0, 1, 2]:
        raise SystemExit("replicate identities are incomplete or duplicated")

    profiles = []
    expected_effect_counters = {
        "effect_edge_upsert": "rule_effect_edge_insert_attempts",
        "effect_edge_delete": "rule_effect_edge_deletes",
        "effect_node_mint": "rule_effect_node_inserts",
        "effect_node_delete": "rule_effect_node_delete_attempts",
        "effect_attr_write": "rule_effect_attr_set_attempts",
    }
    for run in audited:
        rows = run.get("trace_rows")
        scale = run.get("scale")
        if not isinstance(rows, list) or not isinstance(scale, dict):
            raise SystemExit("audited run is missing trace rows or scale counters")
        by_kind: Counter[str] = Counter()
        row_counts: Counter[str] = Counter()
        missing_fields: dict[str, Counter[str]] = defaultdict(Counter)
        by_uid: Counter[str] = Counter()
        for row in rows:
            kind = str(row["kind"])
            count = int(row["count"])
            if count < 0:
                raise SystemExit("negative trace event count")
            by_kind[kind] += count
            row_counts[kind] += 1
            by_uid[str(row.get("rule_uid"))] += count
            for field in ("node", "resource", "peer", "rule_uid"):
                if row.get(field) is None:
                    missing_fields[kind][field] += count
        weighted = sum(by_kind.values())
        if weighted != int(run.get("trace_event_count", -1)):
            raise SystemExit(f"trace event sum mismatch in replicate {run['replicate']}")
        if int(run.get("trace_dropped", -1)) != 0:
            raise SystemExit(f"trace rows dropped in replicate {run['replicate']}")
        per_clause = run.get("per_clause")
        if not isinstance(per_clause, list) or any(not isinstance(row, list) or len(row) < 3 for row in per_clause):
            raise SystemExit("audited run is missing per-clause candidate counters")
        attributed_candidates = sum(int(row[-1]) for row in per_clause)
        if int(scale["cand_tested"]) != attributed_candidates + int(scale["cand_tested_unattributed"]):
            raise SystemExit(f"candidate attribution does not conserve in replicate {run['replicate']}")

        effect_reconciliation = {}
        for event_kind, counter_name in expected_effect_counters.items():
            traced = int(by_kind[event_kind])
            counted = int(scale[counter_name])
            effect_reconciliation[event_kind] = {
                "trace_weighted_events": traced,
                "independent_effect_counter": counter_name,
                "counter_value": counted,
                "exact_match": traced == counted,
            }

        profiles.append({
            "replicate": run["replicate"],
            "arm": run["arm"],
            "trace_weighted_events": weighted,
            "trace_distinct_rows": len(rows),
            "trace_dropped": int(run["trace_dropped"]),
            "trace_by_kind": dict(sorted(by_kind.items())),
            "distinct_rows_by_kind": dict(sorted(row_counts.items())),
            "weighted_fields_absent_by_kind": {
                kind: dict(sorted(fields.items())) for kind, fields in sorted(missing_fields.items())
            },
            "trace_events_by_rule_uid": dict(sorted(by_uid.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0])),
            "counter_totals": {
                key: scale.get(key) for key in (
                "cand_tested", "cand_tested_unattributed", "rule_enumerations",
                    "scheduler_dirty_vector_slots", "scheduler_external_poll_slots",
                    "scheduler_fixedpoint_probe_slots", "scheduler_selected_rules",
                    "scheduler_passes", "term_evals_total", "term_evals_unattributed",
                    "term_units_total", "term_units_unattributed",
                    "deferred_queue:fb_samples:drain_batches",
                )
            },
            "per_clause_attributed_candidate_tests": attributed_candidates,
            "timing_counters": {
                "deferred_queue:fb_samples:drain_ns": scale.get("deferred_queue:fb_samples:drain_ns"),
            },
            "effect_reconciliation": effect_reconciliation,
        })

    signature_fields = ("trace_by_kind", "weighted_fields_absent_by_kind", "counter_totals", "per_clause_attributed_candidate_tests", "effect_reconciliation")
    for field in signature_fields:
        if any(profile[field] != profiles[0][field] for profile in profiles[1:]):
            raise SystemExit(f"audited worker mismatch in {field}")

    plain_summary = []
    for run in plain:
        if run.get("trace_rows") != [] or int(run.get("trace_event_count", -1)) != 0 or int(run.get("trace_dropped", -1)) != 0:
            raise SystemExit(f"untraced control unexpectedly records trace rows in replicate {run['replicate']}")
        plain_summary.append({"replicate": run["replicate"], "trace_rows": 0, "trace_event_count": 0, "trace_dropped": 0})

    result = {
        "schema_version": 1,
        "analysis_id": args.output.stem,
        "analysis_type": "post_hoc_raw_capture_reconciliation",
        "claim_boundary": "One source-locked describe_scene capture only. Exact selected effect-event/counter parity does not establish trace recall, task-independent coverage, or attribution of all host/scheduler/post-rule work.",
        "input_path": str(args.input.relative_to(ROOT) if args.input.is_relative_to(ROOT) else args.input),
        "input_sha256": sha256(args.input),
        "worker_counts": {"audited": len(audited), "untraced": len(plain)},
        "audited_workers": profiles,
        "untraced_controls": plain_summary,
        "aggregate_findings": {
            "trace_weighted_events_per_audited_worker": profiles[0]["trace_weighted_events"],
            "trace_distinct_rows_per_audited_worker": profiles[0]["trace_distinct_rows"],
            "candidate_tests": profiles[0]["counter_totals"]["cand_tested"],
            "candidate_tests_unattributed": profiles[0]["counter_totals"]["cand_tested_unattributed"],
            "term_evaluations": profiles[0]["counter_totals"]["term_evals_total"],
            "term_evaluations_unattributed": profiles[0]["counter_totals"]["term_evals_unattributed"],
            "scheduler_work_has_dedicated_trace_event": False,
            "trace_rule_uid_zero_work_is_observable": False,
            "scope_id_retained_in_raw_trace_rows": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["aggregate_findings"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
