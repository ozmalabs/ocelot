#!/usr/bin/env python3
"""Run source-locked repeated concurrent CoW branch lifecycle measurements."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRATE = ROOT / "evaluation/substrate_capability/fixtures/cow_high_churn_lifecycle/Cargo.toml"
RAW = ROOT / "evaluation/reports/cow_high_churn_lifecycle_v1.json"
ANALYZER = ROOT / "scripts/analyze_cow_high_churn_lifecycle_v1.py"
SOURCES = (
    "docs/research/engine_substrate/COW_HIGH_CHURN_LIFECYCLE_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/cow_high_churn_lifecycle_v1.py",
    "scripts/analyze_cow_high_churn_lifecycle_v1.py",
    "evaluation/substrate_capability/fixtures/cow_high_churn_lifecycle/Cargo.toml",
    "evaluation/substrate_capability/fixtures/cow_high_churn_lifecycle/Cargo.lock",
    "evaluation/substrate_capability/fixtures/cow_high_churn_lifecycle/src/main.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/cow_paged_vec.rs",
    "runners/dsl/src/cow_sharded_map.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint

    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    env = dict(os.environ)
    env["CARGO_TARGET_DIR"] = str(ROOT / "runners/dsl/target")
    command = ["cargo", "run", "--offline", "--release", "--manifest-path", str(CRATE)]
    done = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
    if done.returncode:
        raise SystemExit(done.stderr[-8000:])
    measured = json.loads(done.stdout)
    rows = measured["rows"]
    expected = {(n, f, b) for n in (10_000, 50_000) for f in (4, 16)
                for b in ("shared_snapshot", "eager_copy")}
    if measured.get("schema") != "CowHighChurnLifecycleProbeV1":
        raise SystemExit("unexpected fixture schema")
    if len(rows) != 200:
        raise SystemExit(f"expected 200 measured waves, found {len(rows)}")
    for row in rows:
        if not row["all_semantics_pass"] or not row["primary_unchanged"]:
            raise SystemExit(f"semantic gate failed: {row}")
        if not row["cancel_reduced_live_bytes"]:
            raise SystemExit(f"cancellation reclamation gate failed: {row}")
        if not row["mutation_adjusted_reclamation_pass"] or row["mutation_adjusted_after_drop_bytes"] != 0:
            raise SystemExit(f"adjusted reclamation gate failed: {row}")
    if {(r["size_nodes"], r["fanout"], r["backend"]) for r in rows} != expected:
        raise SystemExit("size/fanout/backend coverage mismatch")
    if {r["wave_index"] for r in rows} != set(range(25)):
        raise SystemExit("repeated wave coverage mismatch")
    paired = {}
    for row in rows:
        key = (row["size_nodes"], row["fanout"], row["wave_index"])
        paired.setdefault(key, {})[row["backend"]] = row["branch_added_ids"]
    if len(paired) != 100 or any(v.get("shared_snapshot") != v.get("eager_copy") for v in paired.values()):
        raise SystemExit("eager/shared branch-ID parity failed")

    rustc = subprocess.run(["rustc", "-Vv"], text=True, capture_output=True, check=True).stdout
    binary = ROOT / "runners/dsl/target/release/cow-high-churn-lifecycle-probe"
    capture = {
        "schema": "CowHighChurnLifecycleCaptureV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "logical_cpu_count": os.cpu_count(), "rustc_verbose": rustc},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "runner_sha256": sha(Path(__file__).resolve()),
        "probe_binary_sha256": sha(binary),
        "source_sha256": {p: sha(ROOT / p) for p in SOURCES},
        "protocol": {"sizes_nodes": [10_000, 50_000], "fanouts": [4, 16],
                     "repeats_per_cell": 25, "backends": ["shared_snapshot", "eager_copy"],
                     "waves": len(rows), "retained_base": True,
                     "allocation_metric": "live requested Rust System-allocator bytes",
                     "reclamation_gate": "each mutation wave returns to the same-backend fork/drop/no-write control",
                     "limits": ["synthetic node-only graphs", "one host", "no commit/adoption or serving adapter"]},
        "cargo_command": command,
        "build_stderr_sha256": "sha256:" + hashlib.sha256(done.stderr.encode()).hexdigest(),
        "measurements": measured,
    }
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    subprocess.run([sys.executable, str(ANALYZER)], cwd=ROOT, env=env, check=True)
    print(json.dumps({"waves": len(rows), "paired_cells": len(paired),
                      "source_fingerprint": capture["engine_fingerprint"],
                      "capture": str(RAW.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
