#!/usr/bin/env python3
"""Independent audit of post-fix episodic checkpoint recovery run v5."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_episodic_checkpoint_recovery_postfix_v5_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/episodic_checkpoint_recovery_postfix_v5_lock_20260925.json"


def main():
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    hashes = {k: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == lock["sha256"][k]
              for k, p in lock["paths"].items()}
    by = {r["variant"]: r for r in raw["readers"]}
    intact, corrupt, missing, malformed = (by[x] for x in
                                            ("intact", "altered_summary", "missing_recorded_edge", "malformed_json"))
    checks = {
        "all_v5_hashes_match_current_inputs": all(hashes.values()),
        "five_distinct_processes": len({raw["writer"]["pid"], *(r["pid"] for r in raw["readers"])}) == 5,
        "intact_restart_retrieves_six_and_restores_relations_rules": (
            raw["writer"]["episode_count"] == 6 and intact["episode_count"] == 6 and
            intact["memory_rule_count"] == 18 and
            all(x == {"bound_event_count": 1, "context_count": 1, "schema_count": 1}
                for x in intact["episode_relation_counts"]) and
            all(q["candidate_count"] == 1 and q["state_summary"] == q["expected_summary"] and
                q["provenance_kind"] == "recalled" and q["observation_status"] == "not_observed"
                for q in intact["queries"])),
        "valid_json_semantic_corruption_remains_undetected": (
            corrupt["queries"][0]["state_summary"] == "CORRUPTION-MARKER" and
            corrupt["queries"][0]["status"] == "recalled" and
            corrupt["queries"][0]["provenance_kind"] == "recalled"),
        "missing_recorded_link_degrades_conservatively": (
            missing["queries"][1]["candidate_count"] == 0 and
            missing["queries"][1]["status"] == "insufficient_information" and
            all(q["state_summary"] == q["expected_summary"] for i, q in enumerate(missing["queries"]) if i != 1)),
        "malformed_json_rejected": malformed["load_status"] == "error" and malformed["exception_type"] == "JSONDecodeError",
        "post_load_close_bug_fixed": all(by[x]["close_status"] == "closed" for x in
                                          ("intact", "altered_summary", "missing_recorded_edge")),
    }
    summary = {name: {"load_status": r["load_status"], "close_status": r.get("close_status"),
                      "close_exception_type": r.get("close_exception_type"),
                      "episode_count": r.get("episode_count"), "memory_rule_count": r.get("memory_rule_count"),
                      "load_ms": r.get("load_ns", 0) / 1e6,
                      "query_candidate_counts": [q["candidate_count"] for q in r.get("queries", [])],
                      "query_summaries": [q.get("state_summary") for q in r.get("queries", [])],
                      "rss_peak_kib": r.get("rss_peak_kib")}
               for name, r in by.items()}
    out = {"run_id": raw["run_id"], "lock_run_id": lock["run_id"], "input_hash_match": hashes,
           "checks": checks, "summary": summary,
           "interpretation": "Post-fix close lifecycle passes; episodic graph checkpoint restores; valid-JSON semantic corruption remains silently trusted.",
           "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    dest = ROOT / "evaluation/reports/substrate_episodic_checkpoint_recovery_postfix_v5_analysis_20260925.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": summary, "output": str(dest)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent post-fix checkpoint audit failed")


if __name__ == "__main__":
    main()
