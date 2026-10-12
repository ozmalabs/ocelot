#!/usr/bin/env python3
"""Source-locked replay of a generated experiment-judge rule against oracle cases."""
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
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_EXPERIMENT_JUDGE_SEMANTICS_V1_PREREG_20260928.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/generated_experiment_judge_semantics_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/generated_experiment_judge_semantics_v1_20260928.json"
TEXT = "Compare where the two letters differ and judge the trial on that region."
CASES = [
    {"case": "positive", "run_status": "done", "score": 3.0, "frames": 3.0, "expected": "supported"},
    {"case": "negative", "run_status": "done", "score": -2.0, "frames": 2.0, "expected": "refuted"},
    {"case": "zero", "run_status": "done", "score": 0.0, "frames": 3.0, "expected": "inconclusive"},
    {"case": "nonterminal_control", "run_status": "running", "score": 3.0, "frames": 3.0, "expected": None},
]
SCHEDULE = [["judge_suite", rep] for rep in (0, 1)]
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
        "cases": CASES,
        "text": TEXT,
        "schedule": SCHEDULE,
    }


def node_num(value) -> int:
    return int(value.value if hasattr(value, "value") else value)


def worker(replicate: int, frozen: dict) -> dict:
    before = inputs()
    if before != frozen:
        raise SystemExit("worker inputs differ from source lock")
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from domains import conversation_action as ca
    import types

    adapter = WorldAdapter(seeds=())
    boot_wall0, boot_cpu0 = time.perf_counter_ns(), time.process_time_ns()
    boot = load_all_seeds(adapter)
    boot_wall_ns = time.perf_counter_ns() - boot_wall0
    boot_cpu_ns = time.process_time_ns() - boot_cpu0
    teacher = {"calls": 0}
    try:
        adapter.set_self_teacher(lambda q: (teacher.__setitem__("calls", teacher["calls"] + 1), "teacher")[1])
    except Exception:
        pass

    active_before = sorted(r.get("name", "") for r in adapter.inner.export_rules() if r.get("active"))
    comp = types.SimpleNamespace(
        raw=TEXT, kind="instruction",
        dispatch={"path": "instruction", "predicate": "compare", "object": None},
    )
    action_start_wall, action_start_cpu = time.perf_counter_ns(), time.process_time_ns()
    try:
        action = ca.act_on_instruction(adapter, comp)
        action_error = None
    except BaseException as exc:
        action, action_error = {}, f"{type(exc).__name__}: {exc}"
    action_wall_ns = time.perf_counter_ns() - action_start_wall
    action_cpu_ns = time.process_time_ns() - action_start_cpu
    active_after = sorted(r.get("name", "") for r in adapter.inner.export_rules() if r.get("active"))
    generated_judge_names = [n for n in active_after if n.startswith("judge_experiment_outcome_")]
    case_records = []
    for case in CASES:
        exp = adapter.s.add_node("Experiment", {
            "hypothesis": f"diagnostic:{case['case']}", "game": "synthetic_oracle",
            "status": "running", "run_dir": "", "diagnostic_case": case["case"],
        })
        run = adapter.s.add_node("Run", {
            "status": case["run_status"], "score": case["score"], "frames": case["frames"],
        })
        adapter.inner.add_edge_unchecked(exp, "produced", run)
        start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
        error = None
        try:
            progress = int(adapter.inner.run_rules())
        except BaseException as exc:
            progress, error = -1, f"{type(exc).__name__}: {exc}"
        elapsed_wall, elapsed_cpu = time.perf_counter_ns() - start_wall, time.process_time_ns() - start_cpu
        exp_attrs = dict(adapter.s.node(exp)["attrs"])
        analysed = [node_num(x) for x in adapter.inner.neighbours(exp, "analysed")]
        case_records.append({
            **case,
            "experiment_id": node_num(exp),
            "run_id": node_num(run),
            "observed_outcome": exp_attrs.get("outcome"),
            "conclusion_ready": exp_attrs.get("conclusion_ready"),
            "analysed_run_ids": analysed,
            "progress_steps": progress,
            "run_rules_error": error,
            "settle_wall_ns": elapsed_wall,
            "settle_cpu_ns": elapsed_cpu,
        })
    after = inputs()
    return {
        "replicate": replicate,
        "pid": os.getpid(),
        "text": TEXT,
        "action_error": action_error,
        "action": action,
        "teacher_calls": teacher["calls"],
        "boot_loaded": boot.get("loaded"),
        "boot_failures": len(boot.get("failed", [])),
        "boot_wall_ns": boot_wall_ns,
        "boot_cpu_ns": boot_cpu_ns,
        "action_wall_ns": action_wall_ns,
        "action_cpu_ns": action_cpu_ns,
        "active_rules_before": active_before,
        "active_rules_after": active_after,
        "generated_judge_rule_names": generated_judge_names,
        "cases": case_records,
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
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), json.loads(LOCK.read_text())), sort_keys=True,
                           default=lambda obj: int(obj.value) if hasattr(obj, "value") else str(obj)))
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
    for _, rep in SCHEDULE:
        cp = subprocess.run([sys.executable, str(RUNNER), "--worker", str(rep)],
                            cwd=ROOT, env=env, text=True, capture_output=True)
        if cp.returncode == 0 and cp.stdout.strip():
            runs.append(json.loads(cp.stdout))
        else:
            errors.append({"replicate": rep, "returncode": cp.returncode,
                           "stdout": cp.stdout[-2000:], "stderr": cp.stderr[-4000:]})
        print(f"completed=judge_suite/{rep} rc={cp.returncode}", file=sys.stderr, flush=True)
    report = {
        "schema_version": 1,
        "run_id": "substrate-generated-experiment-judge-semantics-v1-20260928",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "locked_inputs": lock,
        "post_run_inputs": inputs(),
        "schedule": SCHEDULE,
        "errors": errors,
        "runs": runs,
        "capture_status": "complete" if len(runs) == len(SCHEDULE) and not errors else "partial",
    }
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "status": report["capture_status"],
                      "workers": len(runs), "errors": len(errors)}, indent=2))
    if report["capture_status"] != "complete":
        raise SystemExit("capture incomplete; preserve without pooling")


if __name__ == "__main__":
    main()
