#!/usr/bin/env python3
"""Independently verify notification/requeue attribution and summarize topology work."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evaluation/reports/substrate_scoped_notification_requeue_attribution_v1_20260926.json"
sys.path.insert(0, str(ROOT))
from domains.engine_provenance import rust_source_fingerprint  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def med(values):
    return statistics.median(values)


def phase_counter(phase, name):
    return sum(int(t["counter_delta"].get(name, 0)) for t in phase["turn_records"])


def main():
    data = json.loads(REPORT.read_text())
    paths = {
        "protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_NOTIFICATION_REQUEUE_ATTRIBUTION_PREREG_20260926.md",
        "runner": ROOT / "scripts/substrate_scoped_notification_requeue_attribution_v1.py",
        "graph_rs": ROOT / "runners/dsl/src/graph.rs",
        "substrate_rs": ROOT / "runners/dsl/src/substrate.rs",
        "rewrite_rs": ROOT / "runners/dsl/src/rewrite.rs",
        "py_rs": ROOT / "runners/dsl/src/py.rs",
        "scale_audit_rs": ROOT / "runners/dsl/src/scale_audit.rs",
        "native": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
    }
    integrity = {name: sha(path) == data["inputs"][name] for name, path in paths.items()}
    integrity["rust_source_fingerprint"] = rust_source_fingerprint(str(ROOT)) == data["inputs"]["rust_source_fingerprint"]
    summaries = []
    all_gates = True
    for row in data["rows"]:
        n = int(row["frame_count"])
        reps = row["repetitions"]
        per_rep = []
        metrics = {key: [] for key in ("turns", "no_progress_turns", "notifications", "unique_notifications",
            "duplicate_suppressions", "self_requeues", "enqueues", "max_queue_depth", "candidates",
            "term_evaluations", "wall_ns")}
        per_owner = {}
        for rep in reps:
            event, full = rep["event"], rep["full"]
            checks = dict(rep["gates"])
            for phase in event["phases"]:
                records = phase["turn_records"]
                counters_ok = all(phase_counter(phase, key) == int(phase["audit"].get(key, 0)) for key in
                    ("cand_enum", "term_evals_total", "term_units_total", "scoped_local_rule_matches",
                     "scoped_mt_seeded_rule_matches", "scoped_full_fallback_rule_matches"))
                notifications_ok = all(t["notification_entries"] == len(t["notified_owners"])
                    and sorted(set(t["notified_owners"])) == t["unique_notified_owners"] for t in records)
                per_rep.append(counters_ok and notifications_ok)
                per_owner_phase = {}
                for owner, work in phase["owner_work"].items():
                    slot = per_owner_phase.setdefault(owner, {k: 0 for k in work})
                    for key, value in work.items(): slot[key] += int(value)
                for owner, work in per_owner_phase.items():
                    slot = per_owner.setdefault(owner, {k: [] for k in work})
                    for key, value in work.items(): slot[key].append(value)
            if not all(checks.values()): all_gates = False
            # Aggregate raw records rather than trusting runner summaries.
            event_phases = event["phases"]
            metrics["turns"].append(sum(len(p["turn_records"]) for p in event_phases))
            metrics["no_progress_turns"].append(sum(sum(int(t["progress_steps"] == 0) for t in p["turn_records"]) for p in event_phases))
            metrics["notifications"].append(sum(sum(int(t["notification_entries"]) for t in p["turn_records"]) for p in event_phases))
            metrics["unique_notifications"].append(sum(sum(len(t["unique_notified_owners"]) for t in p["turn_records"]) for p in event_phases))
            metrics["duplicate_suppressions"].append(sum(sum(int(t["duplicate_suppressions"]) for t in p["turn_records"]) for p in event_phases))
            metrics["self_requeues"].append(sum(sum(int(t["self_requeues"]) for t in p["turn_records"]) for p in event_phases))
            metrics["enqueues"].append(sum(sum(int(t["successful_enqueues"]) for t in p["turn_records"]) for p in event_phases))
            metrics["max_queue_depth"].append(max(int(p["max_queue_depth"]) for p in event_phases))
            metrics["candidates"].append(sum(phase_counter(p, "cand_enum") for p in event_phases))
            metrics["term_evaluations"].append(sum(phase_counter(p, "term_evals_total") for p in event_phases))
            metrics["wall_ns"].append(sum(int(p["wall_ns"]) for p in event_phases))
        medians = {key: med(values) for key, values in metrics.items()}
        summaries.append({"topology": row["topology"], "frame_count": n, "repetitions": len(reps),
            "all_source_gates_pass": all(all(rep["gates"].values()) for rep in reps),
            "runner_aggregates_match_raw": all(per_rep),
            **{f"median_{key}": value for key, value in medians.items()},
            "notifications_per_turn": medians["notifications"] / medians["turns"] if medians["turns"] else None,
            "duplicate_suppression_rate": medians["duplicate_suppressions"] / medians["notifications"] if medians["notifications"] else None,
            "owner_work_medians_by_frame": {frame: {key: med(values) for key, values in fields.items()}
                for frame, fields in sorted(per_owner.items(), key=lambda pair: int(pair[0]))}})
        if not all(summary_value for summary_value in (summaries[-1]["all_source_gates_pass"], summaries[-1]["runner_aggregates_match_raw"])):
            all_gates = False
    out = REPORT.with_name("substrate_scoped_notification_requeue_attribution_v1_20260926_analysis.json")
    result = {"protocol_id": data["protocol_id"], "integrity": integrity, "all_gates_pass": all_gates and all(integrity.values()),
        "rows": summaries}
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    compact = [{key: row[key] for key in ("topology", "frame_count", "repetitions", "all_source_gates_pass",
        "runner_aggregates_match_raw", "median_turns", "median_no_progress_turns", "median_notifications",
        "median_duplicate_suppressions", "median_self_requeues", "median_max_queue_depth", "median_candidates",
        "median_term_evaluations", "notifications_per_turn", "duplicate_suppression_rate")} for row in summaries]
    print(json.dumps({"analysis": str(out), "all_gates_pass": result["all_gates_pass"], "integrity": integrity,
        "rows": compact}, indent=2))
    if not result["all_gates_pass"]: raise SystemExit("integrity, attribution conservation, or semantic gate failed")


if __name__ == "__main__": main()
