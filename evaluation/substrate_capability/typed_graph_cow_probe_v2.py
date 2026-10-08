#!/usr/bin/env python3
"""Source-locked topology and sparse-write comparison on actual TypedGraph values."""
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
    "runners/dsl/src/bin/typed_graph_cow_probe_v2.rs", "runners/dsl/src/lib.rs",
    "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
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
        output(["cargo", "build", "--release", "--bin", "typed_graph_cow_probe_v2"], CRATE)
    binary = CRATE / "target/release/typed_graph_cow_probe_v2"
    rows = json.loads(output([str(binary), ",".join(map(str, args.sizes)), str(args.repeats)], CRATE))
    expected = {(n, topology) for n in args.sizes for topology in TOPOLOGIES}
    actual = {(r["nodes"], r["topology"]) for r in rows}
    if actual != expected or not all(r["exact_query_and_sibling_isolation"] for r in rows):
        raise RuntimeError("coverage or graph query/sibling-isolation gate failed")
    capture = {
        "schema": "TypedGraphCowProbeV2",
        "implementation_status": "actual TypedGraph node/edge slabs use CowPagedVec; adjacency, indexes, and other substrate state remain eager copies",
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "toolchain": {"rustc": output(["rustc", "--version"], CRATE), "cargo": output(["cargo", "--version"], CRATE)},
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
        "binary": {"path": str(binary.resolve()), "sha256": sha(binary)},
        "sources": {name: sha(ROOT / name) for name in SOURCES},
        "protocol": {
            "sizes": args.sizes, "topologies": list(TOPOLOGIES), "measured_repeats_per_cell": args.repeats,
            "fixtures": "one node type, empty node/edge attrs; directed path, center-out star, and rectangular grid",
            "write_patterns": ["one node-attribute write", "ceil(1% of nodes) spaced node-attribute writes"],
            "timing": "eager/shared arm order alternates per repetition; median operation microseconds; fixture construction excluded",
            "semantic_gate": "counts and node-type queries match; branch neighbours match base; two siblings take divergent values; eager/shared results agree; base value remains unchanged",
            "scope_limits": ["only three synthetic topologies", "query indexes and other Substrate fields still clone eagerly", "no allocation or RSS/PSS accounting", "no deletion or append mutation workload"],
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
