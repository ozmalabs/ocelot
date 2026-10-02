#!/usr/bin/env python3
"""Profile eager clone costs of hash-backed TypedGraph query indexes."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRATE = ROOT / "runners/dsl"
BINARY_NAME = "typed_graph_cow_index_clone_profile_probe"
BINARY = CRATE / "target/release" / BINARY_NAME
SOURCES = (
    "evaluation/substrate_capability/typed_graph_cow_index_clone_profile_v1.py",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/bin/typed_graph_cow_index_clone_profile_probe.rs",
    "runners/dsl/src/cow_paged_vec.rs",
    "runners/dsl/src/lib.rs",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def command(args: list[str]) -> str:
    return subprocess.run(args, cwd=CRATE, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[771, 10771, 50771])
    parser.add_argument("--repeats", type=int, default=25)
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or any(size < 128 for size in args.sizes):
        parser.error("repeats must be positive and sizes at least 128")
    if not args.no_build:
        command(["cargo", "build", "--release", "--bin", BINARY_NAME])
    if not BINARY.is_file():
        raise SystemExit(f"missing probe binary: {BINARY}; build first")
    rows = json.loads(command([str(BINARY), ",".join(map(str, args.sizes)), str(args.repeats)]))
    expected = 2 * len(args.sizes)
    if len(rows) != expected or any(not row["exact_index_queries"] for row in rows):
        raise RuntimeError("profile rows or independent index query checks failed")
    for row in rows:
        if len(row["components"]) != 8 or any(
                c["median_shared_fork_ns"] < 0 or c["median_eager_clone_ns"] < 0
                for c in row["components"]):
            raise RuntimeError(f"malformed component profile row: {row}")
        if not row["read_costs"] or not all(c["checksums_match"] for c in row["read_costs"]):
            raise RuntimeError("shared-shard and ordinary-map query results differ")
    capture = {
        "schema": "TypedGraphCowIndexCloneProfileV1",
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "toolchain": {"rustc": command(["rustc", "--version"]),
                      "cargo": command(["cargo", "--version"])},
        "runner": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))},
        "binary": {"path": str(BINARY.resolve()), "sha256": sha(BINARY)},
        "sources": {source: sha(ROOT / source) for source in SOURCES},
        "protocol": {
            "sizes": args.sizes, "repeats": args.repeats,
            "topologies": ["path", "star"],
            "fixture": "typed nodes with 128-value declared attribute index; four edge types; sparse edge attributes; star includes high-degree target index",
            "components": ["edge_attrs", "by_type", "out_by_type", "out_by_type_target_index", "in_by_type", "edges_by_type", "edge_delete_version_by_type", "attr_indices"],
            "timed_scope": "clone or deep-copy one hash-backed field at a time; plus 100k-query 50/50 hit/miss streams against a deep flat FxHashMap control",
            "known_limits": ["microbenchmark of component clone/query work, not end-to-end Substrate fork", "one host and fixed component measurement order", "entry counts are reported but no exact allocator bytes or peak memory", "SmallVec adjacency and CowPagedVec slabs are deliberately not included", "flat query control is built once from the same immutable fixture; branch mutation/query mix is not represented"],
        },
        "implementation_status": "all listed hash-backed query indexes are eagerly cloned by TypedGraph::clone_sharing_graph_pages",
        "rows": rows,
    }
    rendered = json.dumps(capture, sort_keys=True, indent=2) + "\n"
    if args.out:
        dest = args.out if args.out.is_absolute() else ROOT / args.out
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding="utf-8")
        print(dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
