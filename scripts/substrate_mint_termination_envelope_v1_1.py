#!/usr/bin/env python3
"""Run the paired recursive-mint termination envelope diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_MINT_TERMINATION_ENVELOPE_V1_1_AMENDMENT_20260926.md"
LOCK = ROOT / "evaluation/substrate_capability/mint_termination_envelope_v1_1_lock_20260926.json"
RUN_ID = "substrate-mint-termination-envelope-v1-1-20260926"
INPUT_FILES = ("scripts/substrate_mint_termination_envelope_v1_1.py", "scripts/analyze_substrate_mint_termination_envelope_v1_1.py", "scripts/substrate_run_manifest.py", "docs/research/engine_substrate/SUBSTRATE_MINT_TERMINATION_ENVELOPE_V1_1_AMENDMENT_20260926.md", "docs/research/engine_substrate/SUBSTRATE_MINT_TERMINATION_ENVELOPE_PREREG_20260925.md", "runners/dsl/src/rewrite.rs", "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs", "runners/dsl/python/substrate_rs/_native.build.json")

def locked_inputs():
    return {"sha256": {rel: sha(ROOT / rel) for rel in INPUT_FILES}, "native_extension_sha256": sha(NATIVE), "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_MINT_TERMINATION_ENVELOPE_PREREG_20260925.md"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
BUILD = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "evaluation/reports/substrate_mint_termination_envelope_v1_1_20260926.json")
    ap.add_argument("--lock", action="store_true")
    ap.add_argument("--sizes", type=int, nargs="+", default=[1, 2, 4])
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--max-steps", type=int, default=32)
    args = ap.parse_args()
    if args.lock:
        print(json.dumps({"locked_inputs": locked_inputs()}, indent=2, sort_keys=True)); return 0
    started_utc = datetime.now(timezone.utc).isoformat()
    log_capture = start_console_capture(RUN_ID)
    locked = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale v1.1 lock")
    print("locked recursive mint envelope configuration:", json.dumps({"sizes": args.sizes, "repeats": args.repeats, "max_steps": args.max_steps}, sort_keys=True), flush=True)
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"]
        , cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build is stale:\n{stale}")

    from substrate_rs import _native

    rows = []
    start = time.time_ns()
    for n in args.sizes:
        if n < 1:
            ap.error("sizes must be positive")
        for repeat in range(args.repeats):
            for effect in ("add_node", "add_node_if_absent"):
                s = _native.Substrate()
                nodes = [s.add_node("Seed") for _ in range(n + 1)]
                for a, b in zip(nodes, nodes[1:]):
                    s.add_edge_unchecked(a, "link", b)
                attrs = {"tag": "shared"}
                s.add_rule({"name": "recursive_mint", "match": [["x", "link", "y"]],
                            "effects": [[effect, "w", "Witness", attrs],
                                        ["add_edge", "y", "link", "w", {}]]})
                before_nodes, before_edges = s.node_count(), s.edge_count()
                cpu0, wall0 = time.process_time_ns(), time.perf_counter_ns()
                report = s.run_rules_report(args.max_steps, False)
                wall, cpu = time.perf_counter_ns() - wall0, time.process_time_ns() - cpu0
                after_nodes, after_edges = s.node_count(), s.edge_count()
                bounded = effect == "add_node_if_absent"
                expected_nodes = n + 2
                expected_edges = 2 * n + 1
                exact_bounded = after_nodes == expected_nodes and after_edges == expected_edges
                status_ok = (report["status"] == "fixed_point" and exact_bounded) if bounded else (
                    report["status"] == "progress_budget_reached" and after_nodes > before_nodes)
                rows.append({"size_links": n, "repeat": repeat, "effect": effect,
                             "status": report["status"], "progress_steps": report["progress_steps"],
                             "passes_completed": report["passes_completed"],
                             "budget_overshoot": report["budget_overshoot"],
                             "nodes_before": before_nodes, "nodes_after": after_nodes,
                             "edges_before": before_edges, "edges_after": after_edges,
                             "expected_bounded_nodes": expected_nodes,
                             "expected_bounded_edges": expected_edges,
                             "exact_bounded_state": exact_bounded if bounded else None,
                             "status_and_state_match": status_ok,
                             "wall_time_ns": wall, "cpu_time_ns": cpu})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": 1, "run_id": f"mint-envelope-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
              "preregistration": {"path": str(PREREG.relative_to(ROOT)), "sha256": sha(PREREG)},
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "dirty_tree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
              "native_sha256": sha(NATIVE), "build_record_sha256": sha(BUILD),
              "python": sys.version.split()[0], "platform": platform.platform(),
              "configuration": {"sizes": args.sizes, "repeats": args.repeats, "max_steps": args.max_steps,
                                 "detect_cycles": False, "wall_supervisor_timeout_seconds": 20},
              "started_unix_ns": start, "finished_unix_ns": time.time_ns(), "records": rows,
              "summary": {"record_count": len(rows), "all_checks_pass": all(x["status_and_state_match"] for x in rows),
                          "bounded_fixed_points": sum(x["effect"] == "add_node_if_absent" and x["status"] == "fixed_point" for x in rows),
                          "unrestricted_budget_stops": sum(x["effect"] == "add_node" and x["status"] == "progress_budget_reached" for x in rows)}}
    post = locked_inputs()
    result["locked_inputs"] = locked
    result["post_run_inputs"] = post
    result["lock_sha256"] = sha(LOCK)
    result["exit_status"] = 0 if result["summary"]["all_checks_pass"] and post == locked else 2
    log_ref = finish_console_capture(log_capture)
    result["run_manifest"] = capture_run_manifest(
        run_id=RUN_ID, runner="scripts/substrate_mint_termination_envelope_v1_1.py",
        protocol_files=(str(PREREG.relative_to(ROOT)), str(AMENDMENT.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=("runners/dsl/src/rewrite.rs", "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs", "scripts/substrate_run_manifest.py"),
        analysis_files=("scripts/analyze_substrate_mint_termination_envelope_v1_1.py",),
        started_utc=started_utc, exit_status=result["exit_status"], stdout_stderr_capture=log_ref)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))
    return result["exit_status"]


if __name__ == "__main__":
    raise SystemExit(main())
