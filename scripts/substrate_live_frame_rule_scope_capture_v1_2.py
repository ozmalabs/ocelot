#!/usr/bin/env python3
"""Source-locked follow-up resolving live RuleUIDs to native definitions."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_FRAME_RULE_SCOPE_CAPTURE_V1_2_PREREG_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/live_frame_rule_scope_capture_v1_2_lock_20261004.json"
RAW = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_workers_raw_20261004.json.gz"
SUMMARY = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_20261004.json"
V1_RUNNER = ROOT / "scripts/substrate_live_frame_interface_capture_v1.py"
ANALYZER = ROOT / "scripts/analyze_live_frame_rule_scope_capture_v1_2.py"
V1_SUMMARY = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_20261003.json"
V1_ANALYSIS = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_analysis_20261003.json"
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import assert_measuring_engine  # noqa: E402

SPEC = importlib.util.spec_from_file_location("live_frame_capture_v1", V1_RUNNER)
V1 = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(V1)
BASE = V1.BASE


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    # Freeze the complete base worker source closure as it exists now; the
    # historical v1 lock is provenance, not a same-source rerun requirement.
    base = V1.lock_inputs()
    return {
        "base_inputs": base,
        "base_inputs_sha256": hashlib.sha256(json.dumps(base, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__).resolve()),
        "analyzer_sha256": sha(ANALYZER),
        "v1_runner_sha256": sha(V1_RUNNER),
        "v1_analysis_sha256": sha(V1_ANALYSIS),
        "v1_summary_sha256": sha(V1_SUMMARY),
    }


def worker(rep: int) -> dict:
    assert_measuring_engine()
    started = lock_inputs()
    from substrate.world_adapter import WorldAdapter

    original_converse = WorldAdapter.converse
    snapshots = []

    def tracked_converse(agent, *args, **kwargs):
        native = agent.inner
        before = native.export_rules()
        result = original_converse(agent, *args, **kwargs)
        after = native.export_rules()
        snapshots.append({
            "prompt": str(args[0]) if args else None,
            "before_rule_count": len(before), "after_rule_count": len(after),
            "before_rules": before, "after_rules": after,
        })
        return result

    WorldAdapter.converse = tracked_converse
    try:
        captured = V1.instrumented_worker(rep)
    finally:
        WorldAdapter.converse = original_converse
    finished = lock_inputs()
    return {
        "replicate": rep, "pid": os.getpid(),
        "worker_started_inputs": started, "worker_finished_inputs": finished,
        "capture": captured, "request_rule_snapshots": snapshots,
    }


def atomic_json(path: Path, value: dict) -> tuple[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".frame-rule-scope-", suffix=".json.gz", dir=path.parent)
    raw_hash = hashlib.sha256()
    try:
        with os.fdopen(fd, "wb") as target:
            with gzip.GzipFile(filename="", mode="wb", fileobj=target, compresslevel=6, mtime=0) as stream:
                encoder = json.JSONEncoder(indent=2, sort_keys=True, default=str)
                for chunk in encoder.iterencode(value):
                    encoded = chunk.encode("utf-8")
                    raw_hash.update(encoded)
                    stream.write(encoded)
                stream.write(b"\n")
                raw_hash.update(b"\n")
            target.flush()
            os.fsync(target.fileno())
        compressed_hash = sha(Path(temp_name))
        os.replace(temp_name, path)
        return raw_hash.hexdigest(), compressed_hash
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def check_controls() -> tuple[dict, dict]:
    controls = BASE.controls()
    checks = {
        "correct_link_selects_only_owner": controls["correct_link"]["statuses"] == ["selected", "proposed"],
        "omitted_link_selects_no_goal": controls["omitted_link"]["statuses"] == ["proposed", "proposed"],
        "swapped_link_follows_explicit_edge": controls["swapped_link"]["statuses"] == ["proposed", "selected"]
            and controls["swapped_link"]["event_goal_ids"] == [controls["swapped_link"]["goal_ids"][1]]
            and controls["swapped_link"]["declared_target"] == controls["swapped_link"]["goal_ids"][0],
        "duplicate_result_is_idempotent": controls["duplicate_result"]["status"] == "resolved"
            and controls["duplicate_result"]["transition_kinds"] == ["selection", "execution", "action_result"]
            and controls["duplicate_result"]["closed"] and not controls["duplicate_result"]["active"],
        "faculty_failure_blocks_with_identity": controls["faculty_failure"]["goal_status"] == "blocked"
            and controls["faculty_failure"]["goal_transition_kinds"] == ["selection", "execution", "action_failure"]
            and controls["faculty_failure"]["closed"] and not controls["faculty_failure"]["active"],
    }
    return controls, checks


def run() -> dict:
    assert_measuring_engine()
    locked = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale v1.2 source lock; freeze with --lock after final protocol/runner edits")
    env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}
    jobs = [0, 1, 2]
    random.Random(20261004).shuffle(jobs)
    runs, failures = [], []
    for rep in jobs:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True)
        try:
            payload = json.loads(proc.stdout)
        except Exception:
            payload = {"replicate": rep, "worker_error": "invalid_worker_json",
                       "returncode": proc.returncode, "stdout_tail": proc.stdout[-3000:],
                       "stderr_tail": proc.stderr[-3000:]}
        runs.append(payload)
        if proc.returncode:
            failures.append({"replicate": rep, "returncode": proc.returncode,
                             "stderr_tail": proc.stderr[-3000:]})

    captured_runs = [row for row in runs if "capture" in row]
    expected_prompts = list(BASE.PROMPTS)
    schedule_ok = all(
        [snap.get("prompt") for snap in row.get("request_rule_snapshots", [])] == expected_prompts
        and [req.get("prompt") for req in row["capture"].get("requests", [])] == expected_prompts
        for row in captured_runs
    ) and len(captured_runs) == 3
    resolved = True
    resolution_rows = []
    for row in captured_runs:
        for index, snap in enumerate(row["request_rule_snapshots"]):
            post_rules = {int(rule["rule_uid"]): rule for rule in snap["after_rules"]}
            observed = {int(access[0]) for access in row["capture"]["requests"][index]["access_rows"]}
            missing = sorted(observed - post_rules.keys())
            resolved &= not missing
            resolution_rows.append({"replicate": row["replicate"], "turn": index,
                                    "observed_uid_count": len(observed), "mapped_uid_count": len(observed & post_rules.keys()),
                                    "unmapped_uids": missing,
                                    "added_rule_uids": sorted(post_rules.keys() - {int(r["rule_uid"]) for r in snap["before_rules"]})})

    digests = {row["capture"].get("graph_semantic_sha256") for row in captured_runs}
    digest_ok = len(digests) == 1 and None not in digests
    stable_exports = True
    definition_hashes: dict[tuple[int, int], set[str]] = {}
    for row in captured_runs:
        for turn, snap in enumerate(row["request_rule_snapshots"]):
            for rule in snap["after_rules"]:
                uid = int(rule["rule_uid"])
                value = json.dumps(rule, sort_keys=True, separators=(",", ":"), default=str)
                definition_hashes.setdefault((turn, uid), set()).add(hashlib.sha256(value.encode()).hexdigest())
    for hashes in definition_hashes.values():
        stable_exports &= len(hashes) == 1
    lock_stable = lock_inputs() == locked and all(
        row.get("worker_started_inputs") == locked == row.get("worker_finished_inputs")
        for row in captured_runs
    )
    lifecycle = all(
        row["capture"]["task_result"]["turns"][0]["route"] == "self_report"
        and row["capture"]["task_result"]["turns"][0]["goal_count"] == 1
        and row["capture"]["task_result"]["turns"][0]["goal"]["status"] == "resolved"
        and row["capture"]["task_result"]["turns"][0]["goal"]["transition_kinds"] == ["selection", "execution", "action_result"]
        and row["capture"]["task_result"]["turns"][1]["route"] is None
        and row["capture"]["task_result"]["turns"][1]["goal_count"] == 0
        for row in captured_runs
    )
    controls, control_checks = check_controls()
    checks = {
        "three_distinct_fresh_pids": len(captured_runs) == 3 and len({row["pid"] for row in captured_runs}) == 3,
        "source_lock_stable": lock_stable,
        "two_request_export_schedule_reproduces": schedule_ok,
        "runtime_rule_uids_resolve_to_post_request_definitions": resolved,
        "exported_definitions_stable_across_workers": stable_exports,
        "final_graph_digest_reproduces_across_current_workers": digest_ok,
        "task_lifecycle_and_shortfall_reproduce": lifecycle,
        "all_semantic_controls_pass": all(control_checks.values()),
        "no_worker_process_failures": not failures,
    }
    raw = {
        "schema_version": 1, "run_id": "substrate-live-frame-rule-scope-capture-v1.2-20261004",
        "protocol": str(PROTOCOL.relative_to(ROOT)), "locked_inputs": locked,
        "post_run_inputs": lock_inputs(), "worker_order": jobs, "runs": runs,
        "resolution_summary": resolution_rows, "controls": controls,
        "control_checks": control_checks, "process_failures": failures,
        "checks": checks,
        "claim_boundary": "Three fresh workers over the v1 prompt pair. Every access-traced RuleUID is checked against its same-request post-converse native definition snapshot. Exported syntax remains a candidate static scope, not a complete factor or dependency specification.",
    }
    raw_sha, raw_gz_sha = atomic_json(RAW, raw)
    summary = {
        "schema_version": 1, "run_id": raw["run_id"],
        "raw_path": str(RAW.relative_to(ROOT)), "raw_compressed_sha256": raw_gz_sha,
        "raw_uncompressed_sha256": raw_sha,
        "lock_path": str(LOCK.relative_to(ROOT)), "lock_sha256": sha(LOCK),
        "checks": checks, "summary": {
            "workers": len(captured_runs), "exports": sum(len(row.get("request_rule_snapshots", [])) * 2 for row in captured_runs),
            "rule_definition_rows": sum(sum(len(snap["before_rules"]) + len(snap["after_rules"])
                                              for snap in row.get("request_rule_snapshots", []))
                                            for row in captured_runs),
            "runtime_rule_uids_mapped": sum(item["mapped_uid_count"] for item in resolution_rows),
            "runtime_rule_uid_observations": sum(item["observed_uid_count"] for item in resolution_rows),
            "newly_added_rule_uids": sorted({uid for item in resolution_rows for uid in item["added_rule_uids"]}),
        },
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))
    if not all(checks.values()):
        raise SystemExit("one or more v1.2 rule-scope capture gates failed; raw capture retained")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", type=int, choices=(0, 1, 2))
    args = parser.parse_args()
    assert_measuring_engine()
    if args.lock:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"locked_inputs": lock_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
    elif args.worker is not None:
        print(json.dumps(worker(args.worker), sort_keys=True, default=str))
    else:
        run()


if __name__ == "__main__":
    main()
