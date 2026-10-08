#!/usr/bin/env python3
"""Measure fan-out cost when typed term-edge dependencies wake stable bindings.

Treatment readers compute a value from the edge type that a writer adds;
control readers compute the same-shaped value from an untouched edge type.
Independent worker processes keep per-instance timing and memory records.
This is an exploratory cost curve, not a speedup or asymptotic claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_term_edge_invalidation_cost_20260924.json"
SIZES = (4, 8, 16, 32, 64)
REPEATS = 5


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value * 1024 if sys.platform.startswith("linux") else value)


def worker(n: int, mode: str, repeat: int) -> dict:
    from substrate_rs import Substrate, _native

    s = Substrate()
    source = s.add_node("InvalidationCostProbe", {})
    anchors = [s.add_node("InvalidationCostProbe", {}) for _ in range(n)]
    seeds = [s.add_node("InvalidationCostProbe", {}) for _ in range(n)]
    for target in anchors:
        s.add_edge_unchecked(source, "anchor", target)
    for target in seeds:
        s.add_edge_unchecked(source, "seed", target)

    counted_type = "changed" if mode == "treatment" else "untouched"
    count_term = {
        "type": "Count",
        "source": {"type": "Edges", "node": {"type": "Var", "name": "x"},
                   "edge_type": counted_type},
    }
    reader_idx = s._inner.add_rule({
        "name": f"invalidation_cost_{mode}_reader",
        "match": [["x", "anchor", "y"]],
        "effects": [["set_attr", "y", "observed_count", {"__term__": count_term}]],
    })
    s._inner.add_rule({
        "name": f"invalidation_cost_{mode}_writer",
        "match": [["x", "seed", "z"]],
        "effects": [["add_edge", "x", "changed", "z"]],
    })
    native_rules = s._inner.rule_access_sets()
    reader_access = next(row for row in native_rules if row[0] == reader_idx)

    rss_after_setup = peak_rss_bytes()
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    progress = s._inner.run_rules(100_000)
    cpu_ns = time.process_time_ns() - cpu_start
    wall_ns = time.perf_counter_ns() - wall_start
    values = [s.node(target)["attrs"].get("observed_count") for target in anchors]
    expected = n if mode == "treatment" else 0
    final_changed = len(s._inner.neighbours(source, "changed"))
    settled = values == [expected] * n and final_changed == n
    return {
        "worker_id": f"{mode}_n{n}_r{repeat}",
        "mode": mode,
        "n_anchor_bindings": n,
        "n_writer_bindings": n,
        "input_edges": 2 * n,
        "progress_firings": progress,
        "final_changed_edges": final_changed,
        "reader_term_edge_reads": reader_access[4],
        "reader_observed_values": values,
        "expected_value_per_anchor": expected,
        "settled_correctly": settled,
        "wall_time_ns": wall_ns,
        "cpu_time_ns": cpu_ns,
        "peak_rss_after_setup_bytes": rss_after_setup,
        "peak_rss_after_run_bytes": peak_rss_bytes(),
        "native_extension_path": str(Path(_native.__file__).resolve()),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "python": sys.version,
        "platform": platform.platform(),
    }


def run_worker(python: str, n: int, mode: str, repeat: int,
               env: dict[str, str]) -> dict:
    proc = subprocess.run(
        [python, str(Path(__file__).resolve()), "--worker", str(n), mode, str(repeat)],
        cwd=ROOT, env=env, text=True, capture_output=True, check=True,
    )
    return json.loads(proc.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=3, metavar=("N", "MODE", "REPEAT"))
    args = parser.parse_args()
    if args.worker:
        n, mode, repeat = args.worker
        print(json.dumps(worker(int(n), mode, int(repeat))))
        return

    records = []
    env = dict(os.environ)
    for n in SIZES:
        for repeat in range(REPEATS):
            for mode in ("control", "treatment"):
                records.append(run_worker(sys.executable, n, mode, repeat, env))
    summaries = []
    for n in SIZES:
        group = [r for r in records if r["n_anchor_bindings"] == n]
        control = [r["wall_time_ns"] for r in group if r["mode"] == "control"]
        treatment = [r["wall_time_ns"] for r in group if r["mode"] == "treatment"]
        control_cpu = [r["cpu_time_ns"] for r in group if r["mode"] == "control"]
        treatment_cpu = [r["cpu_time_ns"] for r in group if r["mode"] == "treatment"]
        treatment_firings = [r["progress_firings"] for r in group if r["mode"] == "treatment"]
        control_firings = [r["progress_firings"] for r in group if r["mode"] == "control"]
        summaries.append({
            "n_anchor_and_writer_bindings": n,
            "control_wall_median_ns": int(statistics.median(control)),
            "treatment_wall_median_ns": int(statistics.median(treatment)),
            "wall_median_ratio_treatment_over_control": statistics.median(treatment) / statistics.median(control),
            "control_cpu_median_ns": int(statistics.median(control_cpu)),
            "treatment_cpu_median_ns": int(statistics.median(treatment_cpu)),
            "cpu_median_ratio_treatment_over_control": statistics.median(treatment_cpu) / statistics.median(control_cpu),
            "control_progress_median": statistics.median(control_firings),
            "treatment_progress_median": statistics.median(treatment_firings),
        })

    source_paths = {
        "rewrite": ROOT / "runners/dsl/src/rewrite.rs",
        "substrate": ROOT / "runners/dsl/src/substrate.rs",
        "binding": ROOT / "runners/dsl/src/py.rs",
        "harness": Path(__file__),
    }
    output = {
        "run_state": "exploratory_cost_pilot",
        "protocol": "term-edge invalidation cost v1",
        "command": "PYTHONPATH=<fresh-native-package>:. python3 scripts/substrate_term_edge_invalidation_cost.py",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip() != "",
        "python": sys.version,
        "platform": platform.platform(),
        "sizes": list(SIZES),
        "repeats_per_condition": REPEATS,
        "source_sha256": {name: sha(path) for name, path in source_paths.items()},
        "summary": summaries,
        "records": records,
        "claim_boundary": [
            "Thirty isolated workers across three sizes and two conditions; exploratory only.",
            "Treatment's reader output depends on each writer edge, so wakeups and recomputation are semantically required by this workload.",
            "The ratio includes required reevaluation and graph writes; it is not pure scheduler overhead.",
            "No asymptotic claim, commodity-scale claim, or general workload estimate follows.",
        ],
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "summary": summaries,
                      "all_settled": all(r["settled_correctly"] for r in records)}, indent=2))
    if not all(r["settled_correctly"] for r in records):
        raise SystemExit("a term-edge invalidation worker did not match its independent oracle")


if __name__ == "__main__":
    main()
