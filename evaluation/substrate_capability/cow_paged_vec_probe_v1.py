#!/usr/bin/env python3
"""Source-locked fanout probe for the experimental Rust CowPagedVec."""
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
    "runners/dsl/src/cow_paged_vec.rs",
    "runners/dsl/src/bin/cow_paged_vec_probe.rs",
    "runners/dsl/src/lib.rs",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def output(command: list[str], *, cwd: Path) -> str:
    return subprocess.run(command, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[771, 1771, 10771, 50771])
    parser.add_argument("--fanouts", nargs="+", type=int, default=[1, 2, 4, 8, 32])
    parser.add_argument("--repeats", type=int, default=25)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 3 or any(x <= 0 for x in args.sizes + args.fanouts):
        parser.error("sizes/fanouts must be positive and repeats must be at least three")

    output(["cargo", "build", "--release", "--bin", "cow_paged_vec_probe"], cwd=CRATE)
    binary = CRATE / "target/release/cow_paged_vec_probe"
    raw = output([
        str(binary), "--sizes", ",".join(map(str, args.sizes)),
        "--fanouts", ",".join(map(str, args.fanouts)),
        "--repeats", str(args.repeats),
    ], cwd=CRATE)
    rows = json.loads(raw)
    expected = {(size, fanout) for size in args.sizes for fanout in args.fanouts}
    actual = {(row["size"], row["fanout"]) for row in rows}
    if actual != expected or not all(row["exact_value_and_primary_isolation"] for row in rows):
        raise RuntimeError("probe coverage or semantic-isolation gate failed")

    capture = {
        "schema": "CowPagedVecProbeV1",
        "implementation_status": "experimental persistent radix-paged vector; not integrated into TypedGraph or Substrate",
        "scope_limits": [
            "base conversion/build is outside branch timings",
            "u64 slots model fixed-size records, not variable-size NodeData/EdgeData payloads",
            "adjacency and graph indexes are not represented",
            "read timings measure indexed lookup only, not rule matching or serialization",
        ],
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "toolchain": {"rustc": output(["rustc", "--version"], cwd=CRATE),
                      "cargo": output(["cargo", "--version"], cwd=CRATE)},
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        "binary": {"path": str(binary.resolve()), "sha256": sha256(binary)},
        "sources": {name: sha256(ROOT / name) for name in SOURCES},
        "protocol": {
            "sizes": args.sizes,
            "branch_fanouts": args.fanouts,
            "measured_repeats": args.repeats,
            "statistics": "median of per-batch timings; all branch arms run in each repetition",
            "cow_fork": "clone shared root once per branch",
            "cow_first_write": "mutate one existing slot in already-forked branches",
            "cow_fork_write": "fork and mutate one slot per branch",
            "vec_control": "Vec<u64>::clone with equivalent read/write values",
            "page_size_slots": 64,
            "semantic_gate": "all CowPagedVec values match the corresponding control; branch writes are isolated from the base and two simultaneously mutated siblings, while untouched leaves remain shared",
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
