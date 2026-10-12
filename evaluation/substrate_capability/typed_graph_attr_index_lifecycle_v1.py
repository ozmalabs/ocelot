#!/usr/bin/env python3
"""Source-locked lifecycle measurements for TypedGraph attribute indexes."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRATE = ROOT / "runners/dsl"
NAME = "typed_graph_attr_index_lifecycle_probe_v1"
BIN = CRATE / "target/release" / NAME
SOURCES = (
    "evaluation/substrate_capability/typed_graph_attr_index_lifecycle_v1.py",
    "runners/dsl/src/bin/typed_graph_attr_index_lifecycle_probe_v1.rs",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs",
    "runners/dsl/src/cow_paged_vec.rs",
    "runners/dsl/src/cow_sharded_map.rs",
    "runners/dsl/src/lib.rs",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def output(args: list[str]) -> str:
    return subprocess.run(args, cwd=CRATE, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sizes", nargs="+", type=int, default=[1000, 10000, 50000])
    ap.add_argument("--repeats", type=int, default=7)
    ap.add_argument("--queries", type=int, default=25)
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if args.repeats < 1 or args.queries < 1 or any(n < 1000 for n in args.sizes):
        ap.error("repeats and queries must be positive; sizes must be at least 1000")
    if not args.no_build:
        output(["cargo", "build", "--release", "--bin", NAME])
    if not BIN.is_file():
        raise SystemExit(f"missing probe binary: {BIN}")
    rows = json.loads(output([str(BIN), ",".join(map(str, args.sizes)),
                              str(args.repeats), str(args.queries)]))
    expected = len(args.sizes) * 3
    gates = ("queries_match", "mutation_parity", "restored_graph_matches", "restored_index_matches")
    if len(rows) != expected or any(not all(row[g] for g in gates) for row in rows):
        raise RuntimeError("row count or semantic parity gate failed")
    if any(row["index_build_ns"] <= 0 or row["graph_fork_median_ns"] <= 0
           or row["graph_serialize_ns"] <= 0 or row["graph_restore_ns"] <= 0
           for row in rows):
        raise RuntimeError("unexpected zero-duration lifecycle measurement")
    capture = {
        "schema": "TypedGraphAttrIndexLifecycleV1",
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "toolchain": {"rustc": output(["rustc", "--version"]),
                      "cargo": output(["cargo", "--version"])},
        "runner": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))},
        "binary": {"path": str(BIN.resolve()), "sha256": sha(BIN)},
        "sources": {source: sha(ROOT / source) for source in SOURCES},
        "protocol": {
            "sizes": args.sizes, "cardinalities": [8, 128, 1024],
            "repeats": args.repeats, "queries_per_sample": args.queries,
            "mutation_schedule": "update first min(max(n/100,1),1000) nodes to a fresh value",
            "timed_operations": ["index declaration/backfill", "indexed and scan query batches",
                                 "indexed and unindexed attr mutation batch", "graph shared-page fork",
                                 "serialize", "restore", "restore index declaration/backfill"],
            "controls": "same generated node population; value zero query; exact indexed/scan result parity; restored serialized graph equality",
            "limitations": ["one host; graph-level fork, not full Substrate fork",
                            "no allocator-byte or RSS measurement", "fixed deterministic modulo distribution",
                            "no warm/cold cache control", "timing samples are descriptive and not instrumented with CPU affinity"],
        },
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
