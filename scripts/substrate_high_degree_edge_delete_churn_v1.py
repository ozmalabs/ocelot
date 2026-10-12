#!/usr/bin/env python3
"""Measure high-degree edge deletion/reinsertion cost with exact graph oracles."""
from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
from substrate_rs import _native  # noqa: E402
from domains.engine_provenance import build_is_stale  # noqa: E402
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_EDGE_DELETE_CHURN_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/high_degree_edge_delete_churn_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_churn_v1_20260928.json"
RUN_ID = "substrate-high-degree-edge-delete-churn-v1-20260928"
FILES = (
    "scripts/substrate_high_degree_edge_delete_churn_v1.py",
    "scripts/analyze_substrate_high_degree_edge_delete_churn_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_EDGE_DELETE_CHURN_V1_PREREG_20260928.md",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)
SIZES = (5_000, 20_000, 80_000)
REPS = (0, 1, 2)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": {p: sha(ROOT / p) for p in FILES},
        "native_path": str(native), "native_sha256": sha(native),
        "native_build_stale": build_is_stale(str(ROOT)),
    }


def worker(n: int, rep: int) -> dict:
    before = fingerprint()
    s = _native.Substrate()
    t0 = time.perf_counter_ns()
    root = s.add_node("Hub", {"role": "root"})
    targets = [s.add_node("Leaf", {"ordinal": i}) for i in range(n)]
    node_build = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    for target in targets:
        s.add_edge_unchecked(root, "hub_child", target)
    edge_build = time.perf_counter_ns() - t0
    sample_ids = sorted({0, n // 2, n - 1})
    sample_before = [s.has_edge(root, "hub_child", targets[i]) for i in sample_ids]
    t0 = time.perf_counter_ns()
    removed = sum(bool(s.remove_edge(root, "hub_child", target)) for target in targets)
    deletion = time.perf_counter_ns() - t0
    edge_count_after_delete = s.edge_count()
    sample_absent = [not s.has_edge(root, "hub_child", targets[i]) for i in sample_ids]
    t0 = time.perf_counter_ns()
    for target in targets:
        s.add_edge_unchecked(root, "hub_child", target)
    reinsertion = time.perf_counter_ns() - t0
    sample_after = [s.has_edge(root, "hub_child", targets[i]) for i in sample_ids]
    counts = {"nodes": s.node_count(), "edges": s.edge_count()}
    after = fingerprint()
    return {
        "n": n, "replicate": rep, "pid": os.getpid(), "before": before, "after": after,
        "node_build_wall_ns": node_build, "edge_build_wall_ns": edge_build,
        "delete_all_wall_ns": deletion, "reinsert_all_wall_ns": reinsertion,
        "removed_count": removed, "edge_count_after_delete": edge_count_after_delete,
        "sample_ids": sample_ids, "sample_before": sample_before,
        "sample_absent_after_delete": sample_absent, "sample_after_reinsert": sample_after,
        "counts_after_reinsert": counts,
    }


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        fp = fingerprint()
        if fp["native_build_stale"]:
            raise SystemExit("native build is stale")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return 0
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), int(sys.argv[3])), sort_keys=True))
        return 0
    before = fingerprint()
    if before["native_build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text()) != before:
        raise SystemExit("missing/stale source lock or native build")
    jobs = [(n, rep) for n in SIZES for rep in REPS]
    random.Random(20260928).shuffle(jobs)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")))
    started = datetime.now(timezone.utc).isoformat()
    log = start_console_capture(RUN_ID)
    rows = []
    for n, rep in jobs:
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(n), str(rep)],
                            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        row = json.loads(cp.stdout)
        row["worker_stderr"] = cp.stderr
        rows.append(row)
    after = fingerprint()
    checks = {
        "nine_workers": len(rows) == 9,
        "three_replicates_per_size": all(sum(r["n"] == n for r in rows) == 3 for n in SIZES),
        "unique_pids": len({r["pid"] for r in rows}) == 9,
        "stable_parent_source": before == after,
        "stable_worker_source": all(r["before"] == before == r["after"] for r in rows),
        "fresh_native_build": not before["native_build_stale"],
        "exact_delete_and_reinsert_oracle": all(
            r["removed_count"] == r["n"] and r["edge_count_after_delete"] == 0
            and r["sample_before"] == [True] * len(r["sample_ids"])
            and r["sample_absent_after_delete"] == [True] * len(r["sample_ids"])
            and r["sample_after_reinsert"] == [True] * len(r["sample_ids"])
            and r["counts_after_reinsert"] == {"nodes": r["n"] + 1, "edges": r["n"]}
            for r in rows),
        "positive_phase_timings": all(all(r[k] > 0 for k in (
            "node_build_wall_ns", "edge_build_wall_ns", "delete_all_wall_ns", "reinsert_all_wall_ns"))
            for r in rows),
    }
    after = fingerprint()
    log_ref = finish_console_capture(log)
    manifest = capture_run_manifest(
        run_id=RUN_ID, runner="scripts/substrate_high_degree_edge_delete_churn_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")) +
                     ("scripts/substrate_run_manifest.py", "domains/engine_provenance.py"),
        analysis_files=("scripts/analyze_substrate_high_degree_edge_delete_churn_v1.py",),
        started_utc=started, exit_status=0 if all(checks.values()) else 1,
        stdout_stderr_capture=log_ref,
    )
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": before,
           "post_run_inputs": after, "schedule": jobs, "checks": checks,
           "all_checks_pass": all(checks.values()), "runs": rows, "run_manifest": manifest,
           "claim_boundary": "Deletion and reinsertion of one homogeneous high-degree outgoing bucket; timing is descriptive, not an asymptotic proof."}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"worker_count": len(rows), "checks": checks, "all_checks_pass": raw["all_checks_pass"],
                      "raw": str(RAW.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
