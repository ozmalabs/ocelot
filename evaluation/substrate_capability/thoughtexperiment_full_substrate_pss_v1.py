#!/usr/bin/env python3
"""Fresh-process RSS/PSS accounting for complete native Substrate branch forks."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture  # noqa: E402

CRATE = ROOT / "runners/dsl"
BACKENDS = {
    "eager": "fork_full_copy_experiment",
    "shared_records": "fork_shared_slab_experiment",
    "shared_graph_pages": "fork_shared_graph_pages_experiment",
}
LOCKED_SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_full_substrate_pss_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
    "domains/engine_provenance.py", "domains/imagination.py",
    "domains/self_correction.py", "domains/collapse_model.py",
    "domains/reflective_faculty.py", "substrate/boot_core.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/cow_paged_vec.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/src/grammar.rs", "runners/dsl/src/checker.rs",
    "runners/dsl/src/term.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs", "runners/dsl/src/persist.rs",
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def smaps_rollup() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/self/smaps_rollup").read_text(encoding="ascii").splitlines():
        name, sep, tail = line.partition(":")
        if sep and name in {"Rss", "Pss", "Pss_Anon", "Pss_File", "Pss_Shmem",
                            "Private_Clean", "Private_Dirty", "Shared_Clean",
                            "Shared_Dirty", "Swap"}:
            values[name] = int(tail.strip().split()[0]) * 1024
    required = {"Rss", "Pss", "Private_Clean", "Private_Dirty", "Shared_Clean", "Shared_Dirty"}
    missing = required - values.keys()
    if missing:
        raise RuntimeError(f"smaps_rollup missing fields: {sorted(missing)}")
    return values


def worker(size: int, backend: str, iteration: int) -> dict:
    if backend not in BACKENDS:
        raise ValueError(backend)
    substrate, native, _positive, _negative, _observations = make_fixture(size)
    before_revision = native.experiment_graph_rule_revision()
    before_counts = (native.node_count(), native.edge_count())
    gc.collect()
    baseline = smaps_rollup()

    branch = getattr(substrate, BACKENDS[backend])()
    after_fork = smaps_rollup()
    branch_counts_before = (branch.node_count(), branch.edge_count())
    branch.add_node("CoWProbeBranchWrite", {"iteration": iteration, "size": size})
    after_write = smaps_rollup()
    branch_counts_after = (branch.node_count(), branch.edge_count())
    primary_unchanged = native.experiment_graph_rule_revision() == before_revision
    isolated_write = branch_counts_after[0] == branch_counts_before[0] + 1 \
        and branch_counts_after[1:] == branch_counts_before[1:] \
        and (native.node_count(), native.edge_count()) == before_counts
    del branch
    gc.collect()
    after_drop = smaps_rollup()
    return {
        "size_added_nodes": size, "backend": backend, "iteration": iteration,
        "baseline_counts": list(before_counts),
        "branch_counts_before_write": list(branch_counts_before),
        "branch_counts_after_write": list(branch_counts_after),
        "primary_unchanged_after_branch_write": primary_unchanged,
        "branch_write_isolated": isolated_write,
        "baseline_bytes": baseline, "after_fork_bytes": after_fork,
        "after_write_bytes": after_write, "after_drop_bytes": after_drop,
        "fork_delta_bytes": {k: after_fork[k] - baseline[k] for k in baseline.keys() & after_fork.keys()},
        "write_delta_bytes": {k: after_write[k] - after_fork[k] for k in after_fork.keys() & after_write.keys()},
        "post_drop_delta_bytes": {k: after_drop[k] - baseline[k] for k in baseline.keys() & after_drop.keys()},
    }


def median(values: list[float]) -> float:
    return statistics.median(values)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 10000, 50000])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261001)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--worker-size", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--worker-backend", choices=sorted(BACKENDS), help=argparse.SUPPRESS)
    parser.add_argument("--worker-iteration", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if args.worker_size is None or args.worker_backend is None:
            parser.error("worker mode requires worker size and backend")
        print(json.dumps(worker(args.worker_size, args.worker_backend, args.worker_iteration), sort_keys=True))
        return 0
    if args.repeats < 3 or args.warmups < 0 or any(n < 0 for n in args.sizes):
        parser.error("repeats must be at least three; warmups/sizes must be nonnegative")
    if not Path("/proc/self/smaps_rollup").exists():
        raise SystemExit("Linux /proc/self/smaps_rollup is required for this protocol")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine; rebuild before measuring: {stale}")

    rng = random.Random(args.seed)
    rows: list[dict] = []
    schedule: list[dict] = []
    executable = Path(__file__).resolve()
    for size in args.sizes:
        for iteration in range(args.warmups + args.repeats):
            backends = list(BACKENDS)
            rng.shuffle(backends)
            for backend in backends:
                command = [sys.executable, str(executable), "--worker",
                           "--worker-size", str(size), "--worker-backend", backend,
                           "--worker-iteration", str(iteration)]
                completed = subprocess.run(command, cwd=ROOT, text=True,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if completed.returncode:
                    raise RuntimeError(
                        f"worker failed: size={size} backend={backend} iteration={iteration}\n"
                        f"{completed.stderr[-4000:]}"
                    )
                row = json.loads(completed.stdout)
                schedule.append({"size": size, "iteration": iteration, "backend": backend})
                if iteration >= args.warmups:
                    rows.append(row)
                if not row["primary_unchanged_after_branch_write"] or not row["branch_write_isolated"]:
                    raise RuntimeError(f"branch isolation gate failed: size={size} backend={backend} iteration={iteration}")

    summaries = []
    for size in args.sizes:
        for backend in BACKENDS:
            cells = [r for r in rows if r["size_added_nodes"] == size and r["backend"] == backend]
            keys = ("Rss", "Pss", "Private_Clean", "Private_Dirty", "Shared_Clean", "Shared_Dirty", "Swap")
            summaries.append({
                "size_added_nodes": size, "backend": backend, "measured_repeats": args.repeats,
                "median_fork_delta_bytes": {k: median([r["fork_delta_bytes"].get(k, 0) for r in cells]) for k in keys},
                "median_write_delta_bytes": {k: median([r["write_delta_bytes"].get(k, 0) for r in cells]) for k in keys},
                "median_post_drop_delta_bytes": {k: median([r["post_drop_delta_bytes"].get(k, 0) for r in cells]) for k in keys},
                "all_parent_and_branch_isolation_checks_pass": all(
                    r["primary_unchanged_after_branch_write"] and r["branch_write_isolated"] for r in cells),
            })

    capture = {
        "schema": "ThoughtexperimentFullSubstratePssV1",
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "engine_build_record": str(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "runner": {"path": str(executable), "sha256": sha(executable)},
        "sources": {name: sha(ROOT / name) for name in LOCKED_SOURCES},
        "protocol": {
            "sizes_added_nodes": args.sizes, "backends": list(BACKENDS),
            "measured_repeats": args.repeats, "warmups": args.warmups, "seed": args.seed,
            "fixture": "same thoughtexperiment positive/negative fixture; candidate/rule objects retained but not executed",
            "isolation": "one fresh Python/native process per backend × size × iteration; measure smaps_rollup before fork, while branch lives, after one branch-local node insertion, and after branch drop plus GC",
            "memory_metrics": "Linux current RSS/PSS and private/shared clean/dirty pages; these include Python, engine, fixture, branch, and loaded runtime state",
            "semantic_gate": "branch adds one node without changing primary graph/rule revisions/counts; source-compatible fixture across backends",
            "scope_limits": ["smaps_rollup current state, not kernel peak RSS", "single synthetic substrate family", "does not run inference or candidate prediction", "post-drop pages may remain in allocator arenas", "one host"],
        },
        "schedule": schedule, "summaries": summaries, "rows": rows,
    }
    rendered = json.dumps(capture, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
