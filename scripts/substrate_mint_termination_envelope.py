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

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_MINT_TERMINATION_ENVELOPE_PREREG_20260925.md"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
BUILD = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--sizes", type=int, nargs="+", default=[1, 2, 4])
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--max-steps", type=int, default=32)
    args = ap.parse_args()
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
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))
    return 0 if result["summary"]["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
