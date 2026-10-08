#!/usr/bin/env python3
"""Isolate branch creation cost for eager native copy and Linux page-CoW.

Both arms start from the same live fixture and install the same focus edge
scope. The native arm deep-copies the Substrate; the process arm forks, sets
the scope in the child, returns a compact shape summary, and waits. Inference,
candidate edits, graph diffing, and fixture construction are excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import statistics
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(EVAL_DIR)]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
import thoughtexperiment_self_correction_copy_comparison_v1 as controls  # noqa: E402

LOCKED_SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_branch_creation_cost_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
)


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                  default=str).encode()).hexdigest()


def native_branch(sub, observations: list) -> tuple[int, int]:
    branch = sub.fork_full_copy_experiment()
    branch.set_experiment_edge_scope([int(getattr(n, "value", n)) for n in observations], 1)
    return branch._inner.node_count(), branch._inner.edge_count()


def process_branch(sub, native, observations: list) -> tuple[int, int]:
    if len(os.listdir("/proc/self/task")) != 1 or threading.active_count() != 1:
        raise RuntimeError("process-CoW probe requires a single-threaded parent")
    native.assert_experiment_fork_safe()
    revision = tuple(native.experiment_graph_rule_revision())
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            sub.set_experiment_edge_scope([int(getattr(n, "value", n)) for n in observations], 1)
            payload = json.dumps({"ok": True, "nodes": sub._inner.node_count(),
                                  "edges": sub._inner.edge_count()},
                                 separators=(",", ":")).encode()
            os.write(write_fd, payload)
            os.close(write_fd)
            os._exit(0)
        except BaseException as exc:
            payload = json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}).encode()
            try:
                os.write(write_fd, payload)
            except OSError:
                pass
            os.close(write_fd)
            os._exit(1)
    os.close(write_fd)
    chunks = []
    while True:
        data = os.read(read_fd, 4096)
        if not data:
            break
        chunks.append(data)
    os.close(read_fd)
    _, status = os.waitpid(pid, 0)
    if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
        raise RuntimeError(f"CoW setup child failed: {status}")
    result = json.loads(b"".join(chunks))
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "unknown child error"))
    if tuple(native.experiment_graph_rule_revision()) != revision:
        raise RuntimeError("CoW child changed parent semantic revision")
    return int(result["nodes"]), int(result["edges"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 1000, 10000, 50000])
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux") or not hasattr(os, "fork"):
        raise SystemExit("this protocol requires Linux fork page-CoW")
    if args.repeats < 1 or args.warmups < 0 or any(n < 0 for n in args.sizes):
        parser.error("repeats must be positive; warmups and sizes nonnegative")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine: {stale}")
    rng = random.Random(args.seed)
    comparisons, schedule = [], []
    for size in args.sizes:
        sub, native, _correct, _wrong, observations = controls.make_fixture(size)
        before = (digest(native.graph_to_dict()), digest(native.export_rules()))
        samples = {"native_deep_copy_plus_scope": [], "process_fork_plus_scope_pipe": []}
        expected_shape = None
        for iteration in range(args.warmups + args.repeats):
            order = list(samples)
            rng.shuffle(order)
            for mode in order:
                start = time.perf_counter_ns()
                shape = native_branch(sub, observations) if mode == "native_deep_copy_plus_scope" \
                    else process_branch(sub, native, observations)
                elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
                if expected_shape is None:
                    expected_shape = shape
                if shape != expected_shape:
                    raise RuntimeError(f"branch visible shape mismatch at size={size}: {shape} != {expected_shape}")
                schedule.append({"size": size, "iteration": iteration, "mode": mode})
                if iteration >= args.warmups:
                    samples[mode].append(elapsed_ms)
        after = (digest(native.graph_to_dict()), digest(native.export_rules()))
        if before != after:
            raise RuntimeError(f"primary state changed at size={size}")
        native_med = statistics.median(samples["native_deep_copy_plus_scope"])
        cow_med = statistics.median(samples["process_fork_plus_scope_pipe"])
        comparisons.append({
            "size": size, "node_count": expected_shape[0], "visible_edge_count": expected_shape[1],
            "native_copy_plus_scope_median_ms": native_med,
            "process_fork_scope_pipe_median_ms": cow_med,
            "process_to_native_cost_ratio": cow_med / native_med,
            "native_samples_ms": samples["native_deep_copy_plus_scope"],
            "process_samples_ms": samples["process_fork_plus_scope_pipe"],
            "exact_visible_shape_parity": True, "primary_graph_and_rules_preserved": True,
        })
    output = {
        "schema": "thoughtexperiment_branch_creation_cost_v1",
        "host": {"platform": platform.platform(), "python": sys.version,
                 "machine": platform.machine()},
        "binary": str(Path(srs._native.__file__).resolve()),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "runner": str(Path(__file__).relative_to(ROOT)),
        "sources": {name: "sha256:" + hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                    for name in LOCKED_SOURCES},
        "implementation_status": "branch_creation_only_native_copy_vs_linux_page_cow",
        "protocol": {
            "native_arm": "fork_full_copy_experiment plus identical one-hop focus edge scope",
            "process_arm": "Linux os.fork, same focus scope in child, compact shape pipe, waitpid",
            "timed_scope": "branch creation, focus scope, and for process arm pipe/wait; no prediction or candidate edits",
            "fixture_setup_excluded": True,
            "order_seed": args.seed,
            "repeats": args.repeats, "warmups": args.warmups,
        },
        "schedule": schedule,
        "comparisons": comparisons,
    }
    encoded = json.dumps(output, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out:
        dest = args.out if args.out.is_absolute() else ROOT / args.out
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(encoded)
        print(dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
