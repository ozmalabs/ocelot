#!/usr/bin/env python3
"""Rule-order and external-state replay probe for stateful UseTool predicates."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_3_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_term_external_dependency_probe_v1_3.py"
LOCK = ROOT / "evaluation/substrate_capability/term_external_dependency_probe_v1_3_lock_20260928.json"
DEFAULT_OUT = ROOT / "evaluation/reports/term_external_dependency_probe_v1_3_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/tools.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_term_external_dependency_probe_v1_3.py",
    "scripts/analyze_term_external_dependency_probe_v1_3.py",
    "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_3_PREREG_20260928.md",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    ext = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_PATHS},
        "native_extension_path": str(ext),
        "native_extension_sha256": sha(ext),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
    }


def run_schedule(order: list[str]) -> dict:
    from substrate_rs import Lit, Substrate, Term, _native

    _native.clear_tool_handlers()
    call_log: list[dict] = []

    def handler(arg):
        result = len(call_log) == 0
        call_log.append({"arg": str(arg), "return": result})
        return result

    _native.register_tool_handler("probe", handler)
    substrate = Substrate()
    inner = substrate._inner
    x = inner.add_node("ReplayProbe", {})
    y = inner.add_node("ReplayProbe", {})
    inner.add_edge_unchecked(x, "trigger", y, {})
    rule_records = []
    where = Term("UseTool", tool="probe", args=[Lit("payload")]).to_dict()
    for name in order:
        idx = inner.add_rule({
            "name": name,
            "match": [["x", "trigger", "y"]],
            "where": where,
            "effects": [["set_attr", "y", name, 1]],
        })
        access = inner.rule_access_sets()[idx]
        rule_records.append({
            "name": name,
            "rule_uid": int(inner.rule_metadata(idx)["rule_uid"]),
            "reads": sorted(map(str, access[3])),
            "reads_any": bool(access[6]),
        })

    first_fire = int(_native.tool_fire_count())
    inner.runtime_access_trace_reset()
    inner.runtime_access_trace_set_enabled(True)
    progress_first = int(inner.run_rules(100))
    inner.runtime_access_trace_set_enabled(False)
    first_trace, first_dropped = inner.runtime_access_trace_snapshot()
    graph_first = inner.graph_to_dict()
    first_calls = list(call_log)
    first_fire_delta = int(_native.tool_fire_count()) - first_fire

    # Change external handler state without mutating the substrate graph.
    call_log.clear()
    second_fire = int(_native.tool_fire_count())
    inner.runtime_access_trace_reset()
    inner.runtime_access_trace_set_enabled(True)
    progress_second = int(inner.run_rules(100))
    inner.runtime_access_trace_set_enabled(False)
    second_trace, second_dropped = inner.runtime_access_trace_snapshot()
    graph_second = inner.graph_to_dict()
    second_calls = list(call_log)
    second_fire_delta = int(_native.tool_fire_count()) - second_fire
    _native.clear_tool_handlers()
    return {
        "insertion_order": order,
        "rules": rule_records,
        "first_settle": {
            "progress": progress_first,
            "callback_log": first_calls,
            "native_fire_delta": first_fire_delta,
            "graph": graph_first,
            "trace_rows": [list(row) for row in first_trace],
            "trace_dropped": int(first_dropped),
        },
        "second_settle_after_external_state_reset": {
            "progress": progress_second,
            "callback_log": second_calls,
            "native_fire_delta": second_fire_delta,
            "graph": graph_second,
            "trace_rows": [list(row) for row in second_trace],
            "trace_dropped": int(second_dropped),
        },
    }


def worker(worker_id: int) -> dict:
    started_inputs = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text())["locked_inputs"] != started_inputs:
        raise RuntimeError("source/native inputs differ from v1.3 lock")
    runs = [run_schedule(["rule_a", "rule_b"]), run_schedule(["rule_b", "rule_a"])]
    return {"worker_id": worker_id, "pid": os.getpid(), "started_inputs": started_inputs,
            "python": sys.version, "platform": platform.platform(), "schedules": runs}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=int)
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.write_lock:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"lock_id": "term_external_dependency_probe_v1_3_20260928", "locked_inputs": lock_inputs()}, indent=2, sort_keys=True) + "\n")
        print(str(LOCK.relative_to(ROOT)))
        return
    if args.worker is not None:
        print(json.dumps(worker(args.worker), sort_keys=True))
        return
    locked = json.loads(LOCK.read_text())
    if lock_inputs() != locked["locked_inputs"]:
        raise SystemExit("source/native inputs differ from v1.3 lock")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing raw capture: {out}")
    runs = []
    for worker_id in range(1, 4):
        argv = [sys.executable, str(Path(__file__).resolve()), "--worker", str(worker_id)]
        proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(f"worker {worker_id} failed ({proc.returncode}): {proc.stderr[-2000:]}")
        run = json.loads(proc.stdout.strip().splitlines()[-1])
        run["child_process"] = {
            "argv": argv, "return_code": proc.returncode,
            "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(proc.stderr.encode()).hexdigest(),
        }
        runs.append(run)
    report = {
        "schema_version": 1,
        "run_id": "term_external_dependency_probe_v1_3_20260928",
        "protocol_sha256": sha(PROTOCOL), "lock_sha256": sha(LOCK),
        "locked_inputs": locked["locked_inputs"],
        "environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(), "cpu_count": os.cpu_count()},
        "runs": runs,
        "claim_boundary": "Three fresh workers × two insertion orders, each with first settle and graph-unchanged callback-state-reset replay. Synthetic local callback only; no general scheduler-order, host-action, or complexity claim.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "schedules_per_worker": len(runs[0]["schedules"]), "output": str(out)}, sort_keys=True))


if __name__ == "__main__":
    main()
