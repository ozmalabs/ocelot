#!/usr/bin/env python3
"""Paired sequential-vs-batch high-degree edge deletion measurement."""
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

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_EDGE_DELETE_BATCH_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/high_degree_edge_delete_batch_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_high_degree_edge_delete_batch_v1_20260928.json"
RUN_ID = "substrate-high-degree-edge-delete-batch-v1-20260928"
FILES = (
    "scripts/substrate_high_degree_edge_delete_batch_v1.py",
    "scripts/analyze_substrate_high_degree_edge_delete_batch_v1.py",
    "scripts/substrate_high_degree_edge_delete_churn_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_EDGE_DELETE_BATCH_V1_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_HIGH_DEGREE_EDGE_DELETE_CHURN_V1_PREREG_20260928.md",
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
REPS = (0, 1, 2)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "files": {p: sha(ROOT / p) for p in FILES}, "native_path": str(native),
            "native_sha256": sha(native), "native_build_stale": build_is_stale(str(ROOT))}


def digest_graph(s) -> str:
    data = json.dumps(s.graph_to_dict(), sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(data).hexdigest()


def build_graph(n: int):
    s = _native.Substrate()
    root = s.add_node("Hub", {"role": "root"})
    targets = [s.add_node("Leaf", {"ordinal": i}) for i in range(n)]
    t0 = time.perf_counter_ns()
    for target in targets:
        s.add_edge_unchecked(root, "hub_child", target)
    edge_build = time.perf_counter_ns() - t0
    return s, root, targets, edge_build


def arm(n: int, mode: str) -> dict:
    t0 = time.perf_counter_ns()
    s, root, targets, edge_build = build_graph(n)
    total_build = time.perf_counter_ns() - t0
    ids = sorted({0, n // 2, n - 1})
    before_digest = digest_graph(s)
    sample_before = [s.has_edge(root, "hub_child", targets[i]) for i in ids]
    t0 = time.perf_counter_ns()
    if mode == "sequential":
        outcomes = [s.remove_edge(root, "hub_child", target) for target in targets]
    else:
        outcomes = s.remove_edges_batch([(root.value, "hub_child", target.value) for target in targets])
    delete_wall = time.perf_counter_ns() - t0
    deleted_digest = digest_graph(s)
    sample_after = [not s.has_edge(root, "hub_child", targets[i]) for i in ids]
    return {"mode": mode, "node_count": s.node_count(), "edge_count": s.edge_count(),
            "build_total_wall_ns": total_build, "edge_build_wall_ns": edge_build,
            "delete_wall_ns": delete_wall, "before_digest": before_digest,
            "deleted_digest": deleted_digest, "outcome_true_count": sum(bool(x) for x in outcomes),
            "outcome_count": len(outcomes), "sample_before": sample_before,
            "sample_absent_after": sample_after}


def mixed_semantic_probe() -> dict:
    def make():
        s = _native.Substrate()
        events = []
        s.register_hook("edge_deleted", lambda src, et, tgt: events.append((src.value, et, tgt.value)))
        root = s.add_node("Hub")
        a, b, c, d, e, f, g = [s.add_node("Leaf") for _ in range(7)]
        s.add_edge_unchecked(root, "alpha", a, {"v": 1})
        s.add_edge_unchecked(root, "beta", b, {"v": 2})
        s.add_edge_unchecked(root, "alpha", c, {"v": 3})
        s.add_edge_unchecked(root, "beta", d, {"v": 4})
        s.add_edge_unchecked(root, "alpha", e, {"v": 5})
        s.add_edge_unchecked(root, "gamma", f, {"v": 6})
        s.add_edge_unchecked(root, "alpha", g, {"v": 7})
        return s, root, (a, b, c, d, e, f, g), events
    seq, rs, ts, seq_events = make()
    bat, rb, tb, bat_events = make()
    ops = [("alpha", 0), ("beta", 1), ("alpha", 0), ("gamma", 3), ("alpha", 4)]
    seq_out = [seq.remove_edge(rs, et, ts[target]) for et, target in ops]
    batch_keys = [(rb.value, et, tb[target].value) for et, target in ops]
    batch_out = bat.remove_edges_batch(batch_keys)
    return {"sequential_outcomes": seq_out, "batch_outcomes": batch_out,
            "sequential_events": seq_events, "batch_events": bat_events,
            "sequential_neighbors": [x.value for x in seq.neighbours(rs)],
            "batch_neighbors": [x.value for x in bat.neighbours(rb)],
            "sequential_alpha_neighbors": [x.value for x in seq.neighbours(rs, "alpha")],
            "batch_alpha_neighbors": [x.value for x in bat.neighbours(rb, "alpha")],
            "sequential_graph": seq.graph_to_dict(), "batch_graph": bat.graph_to_dict(),
            "sequential_digest": digest_graph(seq), "batch_digest": digest_graph(bat),
            "sequential_nodes": seq.node_count(), "batch_nodes": bat.node_count(),
            "sequential_edges": seq.edge_count(), "batch_edges": bat.edge_count()}


def worker(n: int, rep: int) -> dict:
    before = fingerprint()
    order = ["sequential", "batch"] if rep % 2 == 0 else ["batch", "sequential"]
    arms = {mode: arm(n, mode) for mode in order}
    after = fingerprint()
    return {"n": n, "replicate": rep, "pid": os.getpid(), "order": order,
            "arms": arms, "before": before, "after": after}


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
    semantic = mixed_semantic_probe()
    jobs = [(n, rep) for n in SIZES for rep in REPS]
    random.Random(20260929).shuffle(jobs)
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
        "nine_fresh_workers": len(rows) == 9 and len({r["pid"] for r in rows}) == 9,
        "three_pairs_per_size": all(sum(r["n"] == n for r in rows) == 3 for n in SIZES),
        "parent_lock_stable": before == after,
        "worker_lock_stable": all(r["before"] == before == r["after"] for r in rows),
        "native_build_fresh": not before["native_build_stale"],
        "mixed_semantic_outcomes_match": semantic["sequential_outcomes"] == semantic["batch_outcomes"]
            == [True, True, False, False, True],
        "mixed_hook_events_match": semantic["sequential_events"] == semantic["batch_events"],
        "stable_remaining_adjacency_order": semantic["sequential_neighbors"] == semantic["batch_neighbors"]
            and semantic["sequential_alpha_neighbors"] == semantic["batch_alpha_neighbors"]
            and len(semantic["sequential_neighbors"]) == 4
            and len(semantic["sequential_alpha_neighbors"]) == 2,
        "mixed_graph_state_matches": semantic["sequential_digest"] == semantic["batch_digest"]
            and semantic["sequential_graph"] == semantic["batch_graph"]
            and semantic["sequential_nodes"] == semantic["batch_nodes"]
            and semantic["sequential_edges"] == semantic["batch_edges"],
        "all_scale_mutation_oracles": all(all(
            arm_row["node_count"] == row["n"] + 1 and arm_row["edge_count"] == 0
            and arm_row["outcome_true_count"] == row["n"] and arm_row["outcome_count"] == row["n"]
            and arm_row["sample_before"] == [True] * len(arm_row["sample_before"])
            and arm_row["sample_absent_after"] == [True] * len(arm_row["sample_absent_after"])
            and len(arm_row["deleted_digest"]) == 64
            for arm_row in row["arms"].values()) for row in rows),
        "paired_final_graph_digests_equal": all(
            row["arms"]["sequential"]["deleted_digest"] == row["arms"]["batch"]["deleted_digest"]
            for row in rows),
        "paired_initial_graph_digests_equal": all(
            row["arms"]["sequential"]["before_digest"] == row["arms"]["batch"]["before_digest"]
            for row in rows),
    }
    log_ref = finish_console_capture(log)
    manifest = capture_run_manifest(
        run_id=RUN_ID, runner="scripts/substrate_high_degree_edge_delete_batch_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")) +
                     ("scripts/substrate_run_manifest.py", "domains/engine_provenance.py"),
        analysis_files=("scripts/analyze_substrate_high_degree_edge_delete_batch_v1.py",),
        started_utc=started, exit_status=0 if all(checks.values()) else 1,
        stdout_stderr_capture=log_ref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": before,
           "post_run_inputs": after, "schedule": jobs, "semantic_probe": semantic,
           "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows,
           "run_manifest": manifest,
           "claim_boundary": "Paired sequential and stable-order batch deletion on one homogeneous high-degree outgoing bucket, with mixed-edge semantic controls; timing is fixture-scoped."}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"worker_count": len(rows), "checks": checks,
                      "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))},
                     indent=2, sort_keys=True))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
