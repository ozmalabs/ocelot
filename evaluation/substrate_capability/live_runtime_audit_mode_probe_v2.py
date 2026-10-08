#!/usr/bin/env python3
"""Source-locked diagnostic of audit gates around live request execution."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_RUNTIME_AUDIT_MODE_PROBE_V2_PREREG_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/live_runtime_audit_mode_probe_v2_lock_20261004.json"
RAW = ROOT / "evaluation/reports/live_runtime_audit_mode_probe_v2_20261004.json"
BASE_RUNNER = ROOT / "scripts/substrate_live_frame_interface_capture_v1.py"
BASE_ANALYZER = ROOT / "scripts/analyze_live_frame_rule_scope_capture_v1_2.py"
BASE_RAW = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_workers_raw_20261004.json.gz"
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import assert_measuring_engine  # noqa: E402

SPEC = importlib.util.spec_from_file_location("live_frame_capture_for_audit_mode_probe", BASE_RUNNER)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BASE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs() -> dict:
    from substrate_rs import _native
    return {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__).resolve()),
        "base_runner_sha256": sha(BASE_RUNNER),
        "base_analyzer_sha256": sha(BASE_ANALYZER),
        "base_raw_sha256": sha(BASE_RAW),
        "base_worker_inputs": BASE.lock_inputs(),
        "native_sha256": sha(Path(_native.__file__).resolve()),
        "cargo_lock_sha256": sha(ROOT / "runners/dsl/Cargo.lock"),
    }


def worker(rep: int = 0) -> dict:
    assert_measuring_engine()
    from substrate_rs import _native
    from substrate.world_adapter import WorldAdapter

    native = _native.Substrate
    original = WorldAdapter.converse
    observations = []

    def counted(agent, *args, **kwargs):
        inner = agent.inner
        entry = list(native.scale_audit_mode_snapshot())
        native.scale_audit_set_enabled(False)
        native.scale_audit_set_per_rule_enabled(False)
        native.scale_audit_reset()
        native.scale_audit_per_rule_reset()
        after_disable = list(native.scale_audit_mode_snapshot())
        native.scale_audit_mode_trace_reset()
        native.scale_audit_mode_trace_set_enabled(True)
        result = original(agent, *args, **kwargs)
        after_call = list(native.scale_audit_mode_snapshot())
        transitions = native.scale_audit_mode_trace_snapshot()
        native.scale_audit_mode_trace_set_enabled(False)
        counters = {
            "global": [list(row) for row in native.scale_audit_snapshot()],
            "per_rule": [list(row) for row in native.scale_audit_per_rule_snapshot()],
            "metadata": [list(row) for row in native.scale_audit_rule_metadata_snapshot()],
            "identities": [list(row) for row in native.scale_audit_rule_identity_snapshot()],
            "edge_candidates": [list(row) for row in inner.scale_audit_match_edge_snapshot()],
        }
        observations.append({
            "prompt": str(args[0]) if args else None,
            "mode_at_wrapper_entry": entry,
            "mode_after_disable_and_reset": after_disable,
            "mode_after_converse": after_call,
            "mode_transitions_during_converse": transitions,
            "counters": counters,
        })
        return result

    WorldAdapter.converse = counted
    try:
        payload = BASE.instrumented_worker(rep)
    finally:
        WorldAdapter.converse = original
    payload["audit_mode_observations"] = observations
    return payload


def main() -> int:
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(), sort_keys=True, default=str))
        return 0
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite an existing probe artifact")
        LOCK.write_text(json.dumps({"schema": "LiveRuntimeAuditModeProbeV2Lock", "locked_inputs": locked_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    assert_measuring_engine()
    locked = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock")
    env = {
        **os.environ,
        "OZMA_NO_LLM": "1",
        "OZMA_SEED_PERSIST_DISABLED": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONPATH": os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), os.environ.get("PYTHONPATH", ""))),
    }
    cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"], cwd=ROOT, env=env, text=True, capture_output=True)
    if cp.returncode:
        raise SystemExit(f"worker failed rc={cp.returncode}: {cp.stderr[-2000:]}")
    payload = json.loads(cp.stdout)
    post = locked_inputs()
    result = {
        "schema": "LiveRuntimeAuditModeProbeV2",
        "locked_inputs": locked,
        "post_run_inputs": post,
        "source_stable": locked == post,
        "worker_returncode": cp.returncode,
        "worker": payload,
    }
    def has_audit_work(observation: dict) -> bool:
        counters = observation.get("counters", {})
        return (
            any(int(value) != 0 for _, value in counters.get("global", []))
            or bool(counters.get("per_rule"))
            or bool(counters.get("metadata"))
            or bool(counters.get("identities"))
            or bool(counters.get("edge_candidates"))
        )

    result["all_checks_pass"] = (
        result["source_stable"]
        and len(payload.get("requests", [])) == 2
        and len(payload.get("audit_mode_observations", [])) == 2
        and all(x.get("mode_after_disable_and_reset") == [False, False, False] for x in payload["audit_mode_observations"])
        and not any(has_audit_work(x) for x in payload["audit_mode_observations"])
        and all(len(x.get("counters", {}).get("global", [])) > 0 for x in payload["audit_mode_observations"])
    )
    RAW.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    summary = [{
        "prompt": x.get("prompt"),
        "mode_at_wrapper_entry": x.get("mode_at_wrapper_entry"),
        "mode_after_disable_and_reset": x.get("mode_after_disable_and_reset"),
        "mode_after_converse": x.get("mode_after_converse"),
        "mode_transitions_during_converse": x.get("mode_transitions_during_converse"),
        "nonzero_global_counters": {k: v for k, v in x["counters"]["global"] if int(v)},
        "per_rule_row_count": len(x["counters"]["per_rule"]),
        "metadata_row_count": len(x["counters"]["metadata"]),
    } for x in payload.get("audit_mode_observations", [])]
    print(json.dumps({"source_stable": result["source_stable"], "all_checks_pass": result["all_checks_pass"], "observations": summary, "capture": RAW.relative_to(ROOT).as_posix()}, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
