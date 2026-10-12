#!/usr/bin/env python3
"""Independent scale, state-parity, and artifact-integrity analysis."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evaluation/reports/substrate_scoped_notification_fanout_scale_v1_20260926.json"
BASELINE = ROOT / "evaluation/substrate_capability/frame_topology_cost_attribution_baseline_20260926"
sys.path.insert(0, str(ROOT))
from domains.engine_provenance import rust_source_fingerprint  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data = json.loads(REPORT.read_text())
    paths = {
        "protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_NOTIFICATION_FANOUT_SCALE_PREREG_20260926.md",
        "runner": ROOT / "scripts/substrate_scoped_notification_fanout_scale_v1.py",
        "graph_rs": BASELINE / "graph.rs",
        "substrate_rs": BASELINE / "substrate.rs",
        "rewrite_rs": BASELINE / "rewrite.rs",
        "py_rs": BASELINE / "py.rs",
        "native": BASELINE / "_native.abi3.so",
    }
    integrity = {key: sha(path) == data["inputs"][key] for key, path in paths.items()}
    integrity["rust_source_fingerprint"] = rust_source_fingerprint(str(BASELINE / "source_tree")) == data["inputs"]["rust_source_fingerprint"]
    sizes = [int(x) for x in data["sizes"]]
    result_rows, all_checks = [], []
    for row in data["rows"]:
        n = int(row["frame_count"])
        rep_checks, event_times, full_times, event_steps, full_steps, event_turns = [], [], [], [], [], []
        for rep in row["repetitions"]:
            event, full, omitted = rep["event"], rep["full"], rep["omitted"]
            expected_ids = event["born"]["owner_ids"]
            checks = {
                "exact_all_owners_on_birth": event["birth"]["notified_owners"] == expected_ids,
                "exact_all_owners_on_deletion": event["deletion"]["notified_owners"] == expected_ids,
                "birth_and_deletion_queue_complete": event["birth"]["complete"] and event["deletion"]["complete"],
                "birth_state_matches_full": event["born"] == full["born"],
                "deletion_state_matches_full": event["ended"] == full["ended"],
                "full_reference_fixed_points": full["birth"]["status"] == "fixed_point" and full["deletion"]["status"] == "fixed_point",
                "omitted_leaf_is_stale": omitted["born"]["states"][-1] == 0 and omitted["born"] != full["born"],
                "no_event_cap_or_deferred_effects": not event["birth"]["cap_hit"] and not event["deletion"]["cap_hit"] and not event["birth"]["deferred_pending"] and not event["deletion"]["deferred_pending"],
                "fanout_is_n_minus_one": sum(event["born"]["dependency_edges"]) == n - 1,
                "deletion_removes_all_dependencies": not any(event["ended"]["dependency_edges"]),
            }
            rep_checks.append(checks); all_checks.extend(checks.values())
            event_times.append(event["elapsed_ns"] / 1e6); full_times.append(full["elapsed_ns"] / 1e6)
            event_steps.append(event["birth"]["progress_steps"] + event["deletion"]["progress_steps"])
            full_steps.append(int(full["birth"]["progress_steps"]) + int(full["deletion"]["progress_steps"]))
            event_turns.append(event["birth"]["reports"] + event["deletion"]["reports"])
        result_rows.append({
            "frame_count": n, "repetitions": len(rep_checks), "all_repeat_gates_pass": all(all(c.values()) for c in rep_checks),
            "median_event_ms": statistics.median(event_times), "median_full_ms": statistics.median(full_times),
            "median_event_to_full_time_ratio": statistics.median(event_times) / statistics.median(full_times),
            "median_event_progress_steps": statistics.median(event_steps),
            "median_full_progress_steps": statistics.median(full_steps),
            "median_event_scoped_report_turns": statistics.median(event_turns),
            "event_turns_per_frame": statistics.median(event_turns) / n,
            "repeat_gates": rep_checks,
        })
    result = {
        "protocol_id": data["protocol_id"], "integrity": integrity,
        "sizes_match_preregistration": sizes == [2, 4, 8, 16, 32, 64],
        "repeats_per_size_match_preregistration": all(len(r["repetitions"]) == 5 for r in data["rows"]),
        "rows": result_rows, "all_gates_pass": all(integrity.values()) and sizes == [2, 4, 8, 16, 32, 64] and all(all_checks),
    }
    out = REPORT.with_name("substrate_scoped_notification_fanout_scale_v1_20260926_analysis.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    compact = [{k: row[k] for k in ("frame_count", "repetitions", "all_repeat_gates_pass", "median_event_ms", "median_full_ms", "median_event_progress_steps", "median_full_progress_steps", "median_event_scoped_report_turns")} for row in result_rows]
    print(json.dumps({"analysis": str(out), "all_gates_pass": result["all_gates_pass"], "integrity": integrity, "rows": compact}, indent=2))
    if not result["all_gates_pass"]:
        raise SystemExit("integrity or scale gate failed")


if __name__ == "__main__":
    main()
