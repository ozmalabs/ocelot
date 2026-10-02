#!/usr/bin/env python3
"""Matched release probe for node/edge-only versus adjacency-page sharing."""
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
    "runners/dsl/src/bin/typed_graph_cow_graph_pages_probe.rs",
    "runners/dsl/src/lib.rs", "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
)
TOPOLOGIES = ("path", "star", "grid")


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def output(command: list[str], cwd: Path) -> str:
    return subprocess.run(command, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[771, 1771, 10771, 50771])
    parser.add_argument("--repeats", type=int, default=25)
    parser.add_argument("--no-build", action="store_true", help="use the existing release binary")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 3 or any(n <= 0 for n in args.sizes):
        parser.error("sizes must be positive and repeats must be at least three")
    if not args.no_build:
        output(["cargo", "build", "--release", "--bin", "typed_graph_cow_graph_pages_probe"], CRATE)
    binary = CRATE / "target/release/typed_graph_cow_graph_pages_probe"
    rows = json.loads(output([str(binary), ",".join(map(str, args.sizes)), str(args.repeats)], CRATE))
    expected = {(n, topology) for n in args.sizes for topology in TOPOLOGIES}
    actual = {(r["nodes"], r["topology"]) for r in rows}
    if actual != expected or not all(r["exact_edge_query_and_sibling_isolation"] for r in rows):
        raise RuntimeError("coverage or edge/query/sibling isolation gate failed")
    capture = {
        "schema": "TypedGraphCowGraphPagesProbeV1",
        "implementation_status": "experimental graph route shares CowPagedVec node/edge and top-level adjacency pages plus sharded typed out/in bucket indexes; remaining hash indexes and Substrate fields are eager copies",
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "toolchain": {"rustc": output(["rustc", "--version"], CRATE), "cargo": output(["cargo", "--version"], CRATE)},
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
        "binary": {"path": str(binary.resolve()), "sha256": sha(binary)},
        "sources": {name: sha(ROOT / name) for name in SOURCES},
        "protocol": {
            "sizes": args.sizes, "topologies": list(TOPOLOGIES), "measured_repeats_per_cell": args.repeats,
            "arms": ["eager clone", "shared node/edge record slabs with copied adjacency", "shared node/edge and top-level adjacency pages"],
            "mutations": ["one inserted edge", "ceil(1% of nodes) inserted edges with spaced sources"],
            "timing": "arm order rotates each repetition; fixture construction and semantic checks are outside timed regions; median microseconds",
            "semantic_gate": "new edge queries and counts match across all arms; primary remains unchanged; two shared graph-page siblings add distinct edges independently",
            "scope_limits": ["typed out/in bucket indexes are shard-shared; edge attributes, type buckets, high-degree target maps, declared attribute indexes, and remaining Substrate fields are copied eagerly", "no allocation or RSS/PSS capture", "synthetic topologies only", "does not run full Substrate thoughtexperiments"],
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
