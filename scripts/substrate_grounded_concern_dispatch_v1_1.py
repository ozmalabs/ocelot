#!/usr/bin/env python3
"""Source-locked direct-dispatch measurement of the concern authoring faculty."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
BASE_PATH = ROOT / "scripts/substrate_live_conversation_capability_panel_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GROUNDED_CONCERN_DISPATCH_V1_1_PREREG_20260928.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/grounded_concern_dispatch_v1_1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/grounded_concern_dispatch_v1_1_20260928.json"
TEXT = "Compare where the two letters differ and judge the trial on that region."
CONDITIONS = {"grounded_compare": "compare", "non_concern_walk": "walk"}
SCHEDULE = [[condition, rep] for rep in (0, 1) for condition in CONDITIONS]
SPEC = importlib.util.spec_from_file_location("live_conversation_panel", BASE_PATH)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BASE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs() -> dict:
    return {
        "base_panel_inputs": BASE.inputs(),
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "conversation_action_sha256": sha(ROOT / "domains/conversation_action.py"),
        "reflective_faculty_sha256": sha(ROOT / "domains/reflective_faculty.py"),
        "schedule": SCHEDULE,
        "text": TEXT,
        "conditions": CONDITIONS,
    }


def worker(condition: str, replicate: int, frozen: dict) -> dict:
    before = inputs()
    if before != frozen:
        raise SystemExit("worker inputs differ from source lock")
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from domains import conversation_action as ca
    import types

    adapter = WorldAdapter(seeds=())
    boot_start_wall, boot_start_cpu = time.perf_counter_ns(), time.process_time_ns()
    boot = load_all_seeds(adapter)
    boot_wall_ns = time.perf_counter_ns() - boot_start_wall
    boot_cpu_ns = time.process_time_ns() - boot_start_cpu
    teacher = {"calls": 0}
    try:
        adapter.set_self_teacher(lambda q: (teacher.__setitem__("calls", teacher["calls"] + 1), "teacher")[1])
    except Exception:
        pass
    comp = types.SimpleNamespace(
        raw=TEXT,
        kind="instruction",
        dispatch={"path": "instruction", "predicate": CONDITIONS[condition], "object": None},
    )
    before_rules = int(adapter.inner.rule_count())
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    error = None
    try:
        result = ca.act_on_instruction(adapter, comp)
    except BaseException as exc:
        result = {}
        error = f"{type(exc).__name__}: {exc}"
    task_wall_ns, task_cpu_ns = time.perf_counter_ns() - start_wall, time.process_time_ns() - start_cpu
    graph_nodes = int(adapter.inner.node_count()) if hasattr(adapter.inner, "node_count") else None
    graph_edges = int(adapter.inner.edge_count()) if hasattr(adapter.inner, "edge_count") else None
    after = inputs()
    return {
        "condition": condition,
        "replicate": replicate,
        "pid": os.getpid(),
        "text": TEXT,
        "predicate": CONDITIONS[condition],
        "error": error,
        "boot_loaded": boot.get("loaded"),
        "boot_failures": len(boot.get("failed", [])),
        "boot_wall_ns": boot_wall_ns,
        "boot_cpu_ns": boot_cpu_ns,
        "task_wall_ns": task_wall_ns,
        "task_cpu_ns": task_cpu_ns,
        "rules_before": before_rules,
        "rules_after": int(adapter.inner.rule_count()),
        "graph_nodes_after": graph_nodes,
        "graph_edges_after": graph_edges,
        "teacher_calls": teacher["calls"],
        "result": result,
        "inputs_before": before,
        "inputs_after": after,
        "inputs_stable": before == after == frozen,
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock or raw output")
        lock = inputs()
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), json.loads(LOCK.read_text())), sort_keys=True, default=lambda obj: int(obj.value) if hasattr(obj, "value") else str(obj)))
        return
    if RAW.exists():
        raise SystemExit("refusing to overwrite raw output")
    lock = inputs()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != lock:
        raise SystemExit("missing or stale source lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs, errors = [], []
    for condition, rep in SCHEDULE:
        cp = subprocess.run([sys.executable, str(RUNNER), "--worker", condition, str(rep)],
                            cwd=ROOT, env=env, text=True, capture_output=True)
        if cp.returncode == 0 and cp.stdout.strip():
            runs.append(json.loads(cp.stdout))
        else:
            errors.append({"condition": condition, "replicate": rep, "returncode": cp.returncode,
                           "stdout": cp.stdout[-2000:], "stderr": cp.stderr[-4000:]})
        print(f"completed={condition}/{rep} rc={cp.returncode}", file=sys.stderr, flush=True)
    report = {
        "schema_version": 1,
        "run_id": "substrate-grounded-concern-dispatch-v1-1-20260928",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "locked_inputs": lock,
        "post_run_inputs": inputs(),
        "schedule": SCHEDULE,
        "errors": errors,
        "runs": runs,
        "capture_status": "complete" if len(runs) == len(SCHEDULE) and not errors else "partial",
        "claim_boundary": "Constructed instruction representation supplied directly to the action dispatcher; natural-language comprehension is bypassed.",
    }
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "status": report["capture_status"], "workers": len(runs), "errors": len(errors)}, indent=2))
    if report["capture_status"] != "complete":
        raise SystemExit("capture incomplete; preserve without pooling")


if __name__ == "__main__":
    main()
