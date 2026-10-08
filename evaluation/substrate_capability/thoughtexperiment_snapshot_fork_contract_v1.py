#!/usr/bin/env python3
"""Measure reusable Substrate snapshot/fork lifecycle across native backends.

This is a capability contract probe, not an end-to-end thoughtexperiment
speed benchmark. It checks that independent consumers and the source substrate
remain isolated, then times snapshot capture and repeated branch creation on
the same fixed base.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402

LOCKED_SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_snapshot_fork_contract_v1.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
)
BACKENDS = ("full_copy", "shared_slabs", "shared_graph_pages")


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def fixture(size: int) -> tuple[srs.Substrate, object]:
    sub = srs.Substrate()
    previous = None
    for index in range(size):
        node = sub.add_node("FrameItem", {"ordinal": index, "value": 0})
        if previous is not None:
            sub.add_edge_unchecked(previous, "next", node, {})
        previous = node
    if size == 0:
        raise ValueError("size must be positive")
    return sub, sub.nodes("FrameItem")[size // 2]


def exercise(sub: srs.Substrate, target, backend: str, fanout: int) -> dict:
    before_revision = tuple(sub.experiment_graph_rule_revision())
    before_nodes = len(sub.nodes("FrameItem"))
    started = time.perf_counter_ns()
    snapshot = sub._snapshot_with_backend(backend)
    capture_ns = time.perf_counter_ns() - started
    if snapshot._measurement_backend != backend or tuple(snapshot.source_revision) != before_revision:
        raise RuntimeError("snapshot identity/backend/revision contract failed")

    fork_samples, branches = [], []
    for _ in range(fanout):
        t0 = time.perf_counter_ns()
        branches.append(snapshot.fork())
        fork_samples.append(time.perf_counter_ns() - t0)
    for index, branch in enumerate(branches):
        branch.set_attr(target, "value", index + 1)
        branch.add_node("BranchOnly", {"consumer": index})
    sub.set_attr(target, "value", -1)
    sub.add_node("PrimaryOnly", {})

    # A later fork must still start from the immutable captured revision.
    read_only = snapshot.fork()
    checks = (
        len(sub.nodes("FrameItem")) == before_nodes
        and sub.node(target)["attrs"]["value"] == -1
        and len(sub.nodes("PrimaryOnly")) == 1
        and len(sub.nodes("BranchOnly")) == 0
        and len(read_only.nodes("FrameItem")) == before_nodes
        and read_only.node(target)["attrs"]["value"] == 0
        and len(read_only.nodes("PrimaryOnly")) == 0
        and len(read_only.nodes("BranchOnly")) == 0
        and all(branch.node(target)["attrs"]["value"] == i + 1
                and len(branch.nodes("BranchOnly")) == 1
                and len(branch.nodes("PrimaryOnly")) == 0
                for i, branch in enumerate(branches))
        and tuple(snapshot.source_revision) == before_revision
    )
    if not checks:
        raise RuntimeError(f"branch isolation/parity failed for {backend=} {fanout=}")
    return {
        "backend": backend,
        "snapshot_id": snapshot.id,
        "source_revision": list(snapshot.source_revision),
        "fanout": fanout,
        "snapshot_capture_ms": capture_ns / 1e6,
        "branch_fork_median_ms": median([x / 1e6 for x in fork_samples]),
        "branch_fork_samples_ms": [x / 1e6 for x in fork_samples],
        "all_branch_and_primary_isolation_gates_pass": True,
        "read_only_consumer_sees_captured_revision": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=5000)
    parser.add_argument("--fanouts", nargs="+", type=int, default=[1, 4, 16])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.size < 1 or args.repeats < 1 or any(n < 1 for n in args.fanouts):
        parser.error("size, repeats, and fanouts must be positive")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine: {stale}")

    rows = []
    for backend in BACKENDS:
        for fanout in args.fanouts:
            samples = []
            for _ in range(args.repeats):
                sub, target = fixture(args.size)
                samples.append(exercise(sub, target, backend, fanout))
            rows.append({
                "backend": backend,
                "fanout": fanout,
                "repeats": args.repeats,
                "snapshot_capture_median_ms": median([r["snapshot_capture_ms"] for r in samples]),
                "branch_fork_median_ms": median([r["branch_fork_median_ms"] for r in samples]),
                "all_repeats_pass": all(r["all_branch_and_primary_isolation_gates_pass"] for r in samples),
                "read_only_revision_checks_pass": all(r["read_only_consumer_sees_captured_revision"] for r in samples),
                "samples": samples,
            })
    if not all(r["all_repeats_pass"] and r["read_only_revision_checks_pass"] for r in rows):
        raise RuntimeError("snapshot contract gate failed")
    capture = {
        "schema": "ThoughtexperimentSnapshotForkContractV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version},
        "engine": {"binary": str(Path(srs._native.__file__).resolve()),
                   "rust_source_fingerprint": rust_source_fingerprint(str(ROOT))},
        "runner": str(Path(__file__).relative_to(ROOT)),
        "sources": {name: sha(ROOT / name) for name in LOCKED_SOURCES},
        "protocol": {
            "fixture": "path of FrameItem nodes with ordinal/value attributes",
            "snapshot_backends": list(BACKENDS), "fanouts": args.fanouts,
            "repeats": args.repeats, "fixture_size": args.size,
            "consumers": ["independent mutable branch 0..N", "mutated primary", "read-only post-mutation fork"],
            "gates": ["backend and source revision preserved", "siblings isolated", "primary isolated", "read-only consumer sees captured base"],
            "timed_scope": "snapshot capture and repeated branch fork only; fixture construction and mutations excluded",
            "limitations": ["graph/substrate contract smoke on one synthetic path fixture", "no concurrent writes, cancellation/reclamation, adoption or conflict handling", "not an end-to-end Thoughtexperiment result", "non-graph substrate fields are still eagerly copied", "does not establish vLLM/KV-cache compatibility"],
        },
        "rows": rows,
    }
    encoded = json.dumps(capture, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out:
        dest = args.out if args.out.is_absolute() else ROOT / args.out
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(encoded, encoding="utf-8")
        print(dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
