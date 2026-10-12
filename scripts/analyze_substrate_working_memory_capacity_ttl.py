#!/usr/bin/env python3
"""Independent audit of the frozen working-memory capacity and TTL run."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_working_memory_capacity_ttl_amended_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/working_memory_capacity_ttl_amended_lock_20260925.json"


def main():
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    hashes = {k: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == lock["sha256"][k]
              for k, path in lock["paths"].items()}
    runs = {r["scenario"]: r for r in raw["runs"]}
    cap, rep = runs["capacity"], runs["replacement"]
    un, ma = runs["ttl_unmaintained"]["expiry"], runs["ttl_maintained"]["expiry"]
    checks = {
        "all_locked_hashes_match": all(hashes.values()),
        "four_expected_scenarios": set(runs) == {"capacity", "replacement", "ttl_unmaintained", "ttl_maintained"},
        "capacity_two_accept_then_refuse": cap["active_slot_count"] == 2 and
            [g["result_status"] for g in cap["gates"]] == ["accepted", "accepted", "refused"] and
            cap["gates"][2]["reason"] == "capacity_limit",
        "replacement_targets_low_priority_foreign_task": rep["active_slot_count"] == 2 and
            rep["gates"][2]["result_status"] == "accepted_with_interference" and
            any(s["held_content"] == ["project"] and s["priority"] == 0.8 and
                s["interference_count"] == 1 and s["last_replacement_reason"] == "cross_task_interference"
                for s in rep["slots"]) and
            any(s["held_content"] == ["high-chat"] and s["priority"] == 0.9 for s in rep["slots"]) and
            not any("low-chat" in s["held_content"] for s in rep["slots"]),
        "unmaintained_expires_on_boundary_and_releases_content": un["initial_expiry"] == 9.0 and
            un["at_epoch_8"]["status"] == "active" and un["final"]["status"] == "expired" and
            un["final"]["terminal_reason"] == "maintenance_lapsed" and
            un["final"]["terminal_epoch"] == 9.0 and un["final"]["held_content_count"] == 0,
        "maintenance_extends_expiry_then_releases_content": ma["initial_expiry"] == 9.0 and
            ma["at_epoch_8"]["expires_epoch"] == 16.0 and ma["at_epoch_9"]["status"] == "active" and
            ma["final"]["status"] == "expired" and ma["final"]["terminal_epoch"] == 16.0 and
            ma["final"]["held_content_count"] == 0,
    }
    out = {"run_id": raw["run_id"], "lock_run_id": lock["run_id"],
           "input_hash_match": hashes, "checks": checks,
           "summary": {name: {"active_slots": r["active_slot_count"], "slot_count": r["slot_count"],
                              "gate_results": [g["result_status"] for g in r["gates"]],
                              "boot_ms": r["boot_ns"] / 1e6,
                              "tick_ms": {t["label"]: t["tick_ns"] / 1e6 for t in r["ticks"]},
                              "rss_peak_kib": r["rss_peak_kib"]}
                       for name, r in runs.items()},
           "interpretation": "The authored two-slot capacity/replacement and epoch expiry/maintenance behaviors matched this synthetic protocol.",
           "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    dest = ROOT / "evaluation/reports/substrate_working_memory_capacity_ttl_analysis_20260925.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": out["summary"], "output": str(dest)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent working-memory audit failed")


if __name__ == "__main__":
    main()
