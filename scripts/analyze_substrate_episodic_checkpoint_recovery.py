#!/usr/bin/env python3
"""Independent audit of episodic save/load and corruption probe."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_episodic_checkpoint_recovery_amended_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/episodic_checkpoint_recovery_amended_v3_lock_20260925.json"


def main():
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    hashes = {k: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == lock["sha256"][k]
              for k, p in lock["paths"].items()}
    readers = {r["variant"]: r for r in raw["readers"]}
    intact, corrupt, missing, malformed = (readers[x] for x in
                                            ("intact", "altered_summary", "missing_recorded_edge", "malformed_json"))
    intact_q = intact["queries"]
    corrupted_q = corrupt["queries"]
    missing_q = missing["queries"]
    checks = {
        "all_v3_locked_hashes_match": all(hashes.values()),
        "five_distinct_processes": len({raw["writer"]["pid"], *(r["pid"] for r in raw["readers"])}) == 5,
        "intact_checkpoint_roundtrips_six_events_and_rules": (
            raw["writer"]["episode_count"] == 6 and intact["load_status"] == "loaded" and
            intact["episode_count"] == 6 and intact["memory_rule_count"] == 18 and
            len(intact["episode_relation_counts"]) == 6 and
            all(x == {"bound_event_count": 1, "context_count": 1, "schema_count": 1}
                for x in intact["episode_relation_counts"]) and
            len(intact_q) == 6 and all(q["candidate_count"] == 1 and
                q["state_summary"] == q["expected_summary"] and q["status"] == "recalled" and
                q["provenance_kind"] == "recalled" and q["observation_status"] == "not_observed"
                for q in intact_q)),
        "altered_summary_is_silently_returned_as_recalled": (
            corrupted_q[0]["state_summary"] == "CORRUPTION-MARKER" and
            corrupted_q[0]["status"] == "recalled" and
            corrupted_q[0]["provenance_kind"] == "recalled" and
            corrupted_q[0]["observation_status"] == "not_observed" and
            all(q["state_summary"] == q["expected_summary"] for q in corrupted_q[1:])),
        "missing_record_link_returns_explicit_insufficient_information": (
            missing_q[1]["candidate_count"] == 0 and missing_q[1]["status"] == "insufficient_information" and
            all(q["state_summary"] == q["expected_summary"] for i, q in enumerate(missing_q) if i != 1)),
        "malformed_checkpoint_returns_json_decode_error": (
            malformed["load_status"] == "error" and malformed["exception_type"] == "JSONDecodeError"),
        "restored_adapter_close_exposes_vision_field_error": all(
            readers[x]["close_status"] == "error" and
            readers[x]["close_exception_type"] == "AttributeError"
            for x in ("intact", "altered_summary", "missing_recorded_edge")),
    }
    summary = {
        "checkpoint_bytes": raw["checkpoint_bytes"],
        "writer_pid": raw["writer"]["pid"],
        "writer_episode_count": raw["writer"]["episode_count"],
        "readers": {name: {
            "pid": r["pid"], "load_status": r["load_status"],
            "load_ms": r.get("load_ns", 0) / 1e6,
            "close_status": r.get("close_status"),
            "close_exception_type": r.get("close_exception_type"),
            "candidate_counts": [q["candidate_count"] for q in r.get("queries", [])],
            "summaries": [q.get("state_summary") for q in r.get("queries", [])],
            "median_query_tick_ms": statistics.median(q["tick_ns"] / 1e6 for q in r.get("queries", [])) if r.get("queries") else None,
            "rss_peak_kib": r.get("rss_peak_kib"),
        } for name, r in readers.items()},
    }
    out = {"run_id": raw["run_id"], "lock_run_id": lock["run_id"],
           "input_hash_match": hashes, "checks": checks, "summary": summary,
           "interpretation": "Graph checkpoints preserve episodic state and rule execution here, but do not detect valid-JSON semantic corruption; loaded adapter cleanup raises AttributeError.",
           "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    dest = ROOT / "evaluation/reports/substrate_episodic_checkpoint_recovery_analysis_20260925.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": summary, "output": str(dest)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent episodic checkpoint audit failed")


if __name__ == "__main__":
    main()
