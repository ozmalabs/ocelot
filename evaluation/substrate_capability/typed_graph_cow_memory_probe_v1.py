#!/usr/bin/env python3
"""Source-locked allocation accounting for eager and shared-slab TypedGraph branches."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRATE = ROOT / "runners/dsl"
SOURCES = (
    "runners/dsl/src/cow_paged_vec.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/src/bin/typed_graph_cow_memory_probe.rs", "runners/dsl/src/lib.rs",
    "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def output(command: list[str], cwd: Path) -> str:
    return subprocess.run(command, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[771, 1771, 10771, 50771])
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--no-build", action="store_true", help="use the existing release binary")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 3 or any(n <= 0 for n in args.sizes):
        parser.error("sizes must be positive and repeats must be at least three")
    if not args.no_build:
        output(["cargo", "build", "--release", "--bin", "typed_graph_cow_memory_probe"], CRATE)
    binary = CRATE / "target/release/typed_graph_cow_memory_probe"
    rows = json.loads(output([str(binary), ",".join(map(str, args.sizes)), str(args.repeats)], CRATE))
    expected = {(n, topology) for n in args.sizes for topology in ("path", "star", "grid")}
    actual = {(r["nodes"], r["topology"]) for r in rows}
    if actual != expected or not all(r["returned_to_baseline_after_drop"] and r["exact_sibling_isolation"] for r in rows):
        raise RuntimeError("coverage, allocator reclamation, or branch-isolation gate failed")
    capture = {
        "schema": "TypedGraphCowMemoryProbeV1",
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "toolchain": {"rustc": output(["rustc", "--version"], CRATE), "cargo": output(["cargo", "--version"], CRATE)},
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
        "binary": {"path": str(binary.resolve()), "sha256": sha(binary)},
        "sources": {name: sha(ROOT / name) for name in SOURCES},
        "protocol": {
            "sizes": args.sizes, "topologies": ["path", "star", "grid"], "measured_repeats_per_cell": args.repeats,
            "accounting": "custom System GlobalAlloc tracks requested payload bytes, live retained bytes, peak live delta, and allocation count during a single branch operation; allocator metadata and process RSS/PSS are excluded",
            "arms": ["eager clone", "shared-slab clone", "clone plus one node attribute write", "clone plus ceil(1% of nodes) spaced writes"],
            "statistics": "median across repetitions; arm order alternates per block; base graph and fixture construction are outside measurements",
            "semantic_gate": "branch drops return live requested bytes to pre-operation baseline; divergent shared siblings agree on graph queries and preserve primary state",
            "scope_limits": ["graph storage only; not full Substrate state", "indexes are still eagerly cloned", "payload byte counts exclude allocator metadata, fragmentation, page residency, and other processes", "synthetic topologies only"],
        },
        "rows": rows,
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
