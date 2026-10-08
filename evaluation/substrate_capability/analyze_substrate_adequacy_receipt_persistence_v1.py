#!/usr/bin/env python3
"""Independent checks and cost summary for receipt persistence/replay."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/substrate_adequacy_receipt_persistence_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_receipt_persistence_v1_analysis_20261002.json"


def analyze() -> dict:
    capture = json.loads(RAW.read_text())
    checks = []
    for pair in capture["workers"]:
        rep, writer, reader = pair["writer"]["repetition"], pair["writer"], pair["reader"]
        checks.extend([
            {"rep": rep, "case": "writer_saved", "pass": writer["pass"] and writer["saved"] and writer["persisted"]},
            {"rep": rep, "case": "export_probe_matches_lazy_gate_state", "pass": writer["export_probe"]["full"]["gate_rule_found"] == writer["export_probe"]["prefix"]["gate_rule_found"] and writer["gate_loaded_after_teach"]},
            {"rep": rep, "case": "fresh_process_restore", "pass": reader["attrs_match"] and reader["loaded_shape_count"] == 1 and reader["loaded_seed_count"] > 0},
            {"rep": rep, "case": "same_receipt_replay_idempotent", "pass": reader["replay_ok"] and reader["replay_saved"] is False and reader["replay_persisted"] is True and len(reader["after_replay"]["shapes"]) == 1 and reader["after_replay"]["epoch"] == reader["epoch_before"]},
            {"rep": rep, "case": "stale_source_and_request_refused", "pass": reader["stale_source_refused"] and reader["stale_request_refused"] and reader["final_state"] == reader["after_replay"]},
            {"rep": rep, "case": "manifest_and_receipt_hash_stable", "pass": reader["manifest_sha256"] == writer["manifest_sha256"] and reader["receipt_sha256"] == writer["receipt_sha256"]},
            {"rep": rep, "case": "source_lock_stable", "pass": reader["active_after"] == capture["lock"]["active"] and writer["active_after"] == capture["lock"]["active"]},
        ])
    writer_boot = sorted(p["writer"]["boot_ns"] / 1e6 for p in capture["workers"])
    writer_teach = sorted(p["writer"]["teach_ns"] / 1e6 for p in capture["workers"])
    reader_boot = sorted(p["reader"]["boot_ns"] / 1e6 for p in capture["workers"])
    replay = sorted(p["reader"]["replay_ns"] / 1e6 for p in capture["workers"])
    full_export = sorted(p["writer"]["export_probe"]["full"]["wall_ns"] / 1e6
                         for p in capture["workers"])
    prefix_export = sorted(p["writer"]["export_probe"]["prefix"]["wall_ns"] / 1e6
                           for p in capture["workers"])
    median = lambda values: values[len(values)//2]
    result = {"schema": "SubstrateAdequacyReceiptPersistenceV1Analysis",
              "capture_pass": capture["passed"], "checks": checks,
              "passed": capture["passed"] and all(row["pass"] for row in checks),
              "repetitions": len(capture["workers"]),
              "median_writer_full_seed_boot_ms": median(writer_boot),
              "median_reader_full_seed_boot_ms": median(reader_boot),
              "median_accepted_teach_and_persist_ms": median(writer_teach),
              "median_fresh_process_replay_ms": median(replay),
              "median_full_rule_export_ms": median(full_export),
              "median_prefix_rule_export_ms": median(prefix_export),
              "median_full_to_prefix_export_ratio": median(full_export) / median(prefix_export)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    result = analyze()
    print(json.dumps({"passed": result["passed"], "checks": len(result["checks"]),
                      "analysis": str(OUT)}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
