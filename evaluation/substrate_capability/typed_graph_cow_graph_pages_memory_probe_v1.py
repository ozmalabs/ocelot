#!/usr/bin/env python3
"""Allocator-live-byte comparison of eager, records-only, and graph-page forks."""
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
    "runners/dsl/src/cow_paged_vec.rs", "runners/dsl/src/cow_sharded_map.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/src/bin/typed_graph_cow_graph_pages_memory_probe.rs",
    "runners/dsl/src/lib.rs", "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def output(command: list[str], cwd: Path) -> str:
    return subprocess.run(command, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sizes", nargs="+", type=int, default=[771, 1771, 10771, 50771])
    p.add_argument("--repeats", type=int, default=7)
    p.add_argument("--no-build", action="store_true")
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    if a.repeats < 3 or any(n <= 0 for n in a.sizes):
        p.error("sizes must be positive and repeats must be at least three")
    if not a.no_build:
        output(["cargo", "build", "--release", "--bin", "typed_graph_cow_graph_pages_memory_probe"], CRATE)
    binary = CRATE / "target/release/typed_graph_cow_graph_pages_memory_probe"
    rows = json.loads(output([str(binary), ",".join(map(str, a.sizes)), str(a.repeats)], CRATE))
    expected = {(n, t) for n in a.sizes for t in ("path", "star", "grid")}
    if {(r["nodes"], r["topology"]) for r in rows} != expected:
        raise RuntimeError("capture is missing topology/size cells")
    if not all(r["branches_return_to_live_baseline"] and r["exact_query_and_sibling_isolation"] for r in rows):
        raise RuntimeError("branch reclamation or sibling isolation gate failed")
    capture = {
        "schema": "TypedGraphCowGraphPagesMemoryProbeV1",
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "toolchain": {"rustc": output(["rustc", "--version"], CRATE), "cargo": output(["cargo", "--version"], CRATE)},
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
        "binary": {"path": str(binary.resolve()), "sha256": sha(binary)},
        "sources": {name: sha(ROOT / name) for name in SOURCES},
        "protocol": {
            "sizes": a.sizes, "topologies": ["path", "star", "grid"], "measured_repeats_per_cell": a.repeats,
            "arms": ["eager deep clone", "node/edge sharing with eager adjacency copies", "node/edge plus adjacency-page and typed out/in bucket-index sharing"],
            "mutations": ["clone only", "clone plus one edge insertion", "clone plus ceil(1% of nodes) spaced edge insertions"],
            "metric": "increment in live bytes requested from System allocator while branch is alive; branch drop must return to operation baseline",
            "scope_limits": ["allocator payload bytes, not RSS/PSS or allocator metadata", "remaining hash indexes and wider graph/Substrate fields are still eager copies", "synthetic topologies only"],
        },
        "rows": rows,
    }
    rendered = json.dumps(capture, indent=2, sort_keys=True) + "\n"
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
