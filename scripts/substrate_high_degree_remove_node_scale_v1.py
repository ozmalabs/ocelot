#!/usr/bin/env python3
"""Measure public remove_node after stable-order batched incident-edge cleanup."""
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

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_REMOVE_NODE_SCALE_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_REMOVE_NODE_SCALE_V1_1_AMENDMENT_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/high_degree_remove_node_scale_v1_1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_high_degree_remove_node_scale_v1_1_20260928.json"
RUN_ID = "substrate-high-degree-remove-node-scale-v1-1-20260928"
FILES = (
    "scripts/substrate_high_degree_remove_node_scale_v1.py",
    "scripts/analyze_substrate_high_degree_remove_node_scale_v1.py",
    "scripts/substrate_high_degree_edge_delete_batch_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_REMOVE_NODE_SCALE_V1_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_REMOVE_NODE_SCALE_V1_1_AMENDMENT_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_EDGE_DELETE_BATCH_V1_PREREG_20260928.md",
    "evaluation/reports/substrate_high_degree_edge_delete_batch_v1_20260928.json",
    "evaluation/reports/substrate_high_degree_edge_delete_batch_v1_analysis_20260928.json",
    "evaluation/substrate_capability/high_degree_edge_delete_batch_v1_lock_20260928.json",
    "evaluation/reports/substrate_high_degree_edge_delete_churn_v1_20260928.json",
    "evaluation/reports/substrate_high_degree_edge_delete_churn_v1_analysis_20260928.json",
    "evaluation/substrate_capability/high_degree_edge_delete_churn_v1_lock_20260928.json",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)
SIZES = (5_000, 20_000, 80_000)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "files": {p: sha(ROOT / p) for p in FILES}, "native_path": str(native),
            "native_sha256": sha(native), "native_build_stale": build_is_stale(str(ROOT))}


def worker(n: int, rep: int) -> dict:
    before = fingerprint()
    s = _native.Substrate()
    events = []
    s.register_hook("node_deleted", lambda nid, type_name: events.append((nid.value, type_name)))
    t0 = time.perf_counter_ns()
    root = s.add_node("Hub", {"role": "root"})
    leaves = [s.add_node("Leaf", {"ordinal": i}) for i in range(n)]
    for leaf in leaves:
        s.add_edge_unchecked(root, "hub_child", leaf)
    setup = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    removed = s.remove_node(root)
    deletion = time.perf_counter_ns() - t0
    graph = s.graph_to_dict()
    nodes = graph["nodes"]
    node_rows = {row["id"]: row for row in nodes}
    ordinal_values = sorted(row.get("attrs", {}).get("ordinal") for row in nodes)
    samples = []
    for i in sorted({0, n // 2, n - 1}):
        samples.append({"id": i + 1, "attrs": node_rows.get(i + 1, {}).get("attrs")})
    after = fingerprint()
    return {"n": n, "replicate": rep, "pid": os.getpid(), "before": before, "after": after,
            "setup_wall_ns": setup, "remove_node_wall_ns": deletion,
            "removed": removed, "node_count": s.node_count(), "edge_count": s.edge_count(),
            "root_id": root.value, "root_absent": root.value not in node_rows,
            "node_rows": len(nodes), "all_nodes_are_leaves": all(row.get("type") == "Leaf" for row in nodes),
            "ordinal_values": ordinal_values, "expected_ordinals": list(range(n)),
            "samples": samples, "expected_sample_ordinals": [i for i in sorted({0, n // 2, n - 1})],
            "hook_events": events}


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
    jobs = [(n, rep) for n in SIZES for rep in range(3)]
    random.Random(20260930).shuffle(jobs)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")))
    started = datetime.now(timezone.utc).isoformat()
    log = start_console_capture(RUN_ID)
    rows = []
    for n, rep in jobs:
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(n), str(rep)],
                            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        rows.append(json.loads(cp.stdout))
    after = fingerprint()
    checks = {
        "nine_workers": len(rows) == 9,
        "three_workers_per_size": all(sum(r["n"] == n for r in rows) == 3 for n in SIZES),
        "unique_pids": len({r["pid"] for r in rows}) == 9,
        "stable_parent_and_worker_source": before == after and all(r["before"] == before == r["after"] for r in rows),
        "fresh_native_build": not before["native_build_stale"],
        "exact_public_remove_node_oracles": all(
            r["removed"] is True and r["root_absent"] is True
            and r["node_count"] == r["node_rows"] == r["n"] and r["edge_count"] == 0
            and r["all_nodes_are_leaves"] is True
            and r["ordinal_values"] == r["expected_ordinals"]
            and [sample["attrs"].get("ordinal") for sample in r["samples"]] == r["expected_sample_ordinals"]
            and r["hook_events"] == [[0, "Hub"]]
            for r in rows),
        "positive_timings": all(r["setup_wall_ns"] > 0 and r["remove_node_wall_ns"] > 0 for r in rows),
    }
    log_ref = finish_console_capture(log)
    manifest = capture_run_manifest(
        run_id=RUN_ID, runner="scripts/substrate_high_degree_remove_node_scale_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(AMENDMENT.relative_to(ROOT)),
                        str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")) +
                     ("scripts/substrate_run_manifest.py", "domains/engine_provenance.py"),
        analysis_files=("scripts/analyze_substrate_high_degree_remove_node_scale_v1.py",),
        started_utc=started, exit_status=0 if all(checks.values()) else 1,
        stdout_stderr_capture=log_ref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": before,
           "post_run_inputs": after, "schedule": jobs, "checks": checks,
           "all_checks_pass": all(checks.values()), "runs": rows, "run_manifest": manifest,
           "claim_boundary": "Public root-node deletion with outgoing hub edges, three sizes and processes per size; no rule-heavy or mixed-topology claim."}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"worker_count": len(rows), "checks": checks,
                      "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))},
                     indent=2, sort_keys=True))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
