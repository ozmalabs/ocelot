#!/usr/bin/env python3
"""Source-locked high-cardinality TypedGraph attribute-index COW profile."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRATE = ROOT / "runners/dsl"
BIN_NAME = "typed_graph_cow_attr_index_profile_v2"
BIN = CRATE / "target/release" / BIN_NAME
PROTOCOL = ROOT / "docs/research/engine_substrate/TYPED_GRAPH_COW_ATTR_INDEX_PROFILE_V2_PREREG_20261006.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/typed_graph_cow_attr_index_profile_v2_lock_20261006.json"
OUT = ROOT / "evaluation/reports/typed_graph_cow_attr_index_profile_v2_20261006.json"
SOURCES = (
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/cow_sharded_map.rs",
    "runners/dsl/src/bin/typed_graph_cow_attr_index_profile_v2.rs",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def command(args: list[str]) -> str:
    return subprocess.run(args, cwd=CRATE, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def inputs() -> dict:
    if not BIN.is_file():
        raise SystemExit("profile binary is missing")
    return {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "source_sha256": {source: sha(ROOT / source) for source in SOURCES},
        "binary_sha256": sha(BIN),
        "rustc": command(["rustc", "--version"]),
        "cargo": command(["cargo", "--version"]),
    }


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] not in ("--lock",):
        raise SystemExit("usage: typed_graph_cow_attr_index_profile_v2.py [--lock]")
    subprocess.run(["cargo", "build", "--release", "--bin", BIN_NAME], cwd=CRATE, check=True)
    current = inputs()
    if sys.argv[1:] == ["--lock"]:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"schema": "TypedGraphCowAttrIndexProfileV2Lock",
                                    "locked_inputs": current}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs") != current:
        raise SystemExit("missing or stale source lock; build and run with --lock first")
    rows = json.loads(command([str(BIN), "7164,16384,50771", "51"]))
    after = inputs()
    if current != after or len(rows) != 3 or not all(row["queries_exact"] for row in rows):
        raise SystemExit("source stability, row count, or exact-query gate failed")
    payload = {
        "schema": "TypedGraphCowAttrIndexProfileV2",
        "locked_inputs": current,
        "post_run_inputs": after,
        "source_stable": current == after,
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "fixture": "one distinct integer value per node, one declared attribute index",
        "protocol": {"nodes": [7164, 16384, 50771], "repeats": 51,
                     "comparison": "shallow COW clone versus deep clone of all attribute-index/value shards",
                     "limitations": ["index component only", "no branch first-write cost",
                                     "no whole-Substrate fork", "no allocator memory measure"]},
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
