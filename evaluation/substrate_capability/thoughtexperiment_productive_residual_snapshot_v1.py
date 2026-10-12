#!/usr/bin/env python3
"""Measure nonempty Thoughtexperiment residuals across snapshot backends."""
from __future__ import annotations

import hashlib, json, os, platform, random, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
BACKENDS = ("native_full_copy_scoped", "native_shared_graph_pages_scoped", "native_reusable_snapshot")
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_productive_residual_snapshot_v1.py",
    "scripts/analyze_thoughtexperiment_productive_residual_snapshot_v1.py",
    "domains/imagination.py", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs", "runners/dsl/src/persist.rs",
    "runners/dsl/src/py.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_productive_residual_snapshot_v1.json"

def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def make_fixture(size: int):
    import substrate_rs as srs
    sub = srs.Substrate()
    sub.add_node("Rule", {
        "id": "derive_from_hypothesis",
        "match": [["h", "contradicts", "f"], ["f", "stale", "z"]],
        "effect": [
            ["set_attr", "f", "checked", True],
            ["add_node", "c", "Conclusion", {"derived_from_hypothesis": True}],
            ["add_edge", "h", "yields", "c", {}],
            ["del_node", "z"],
        ],
    })
    fact = sub.add_node("Fact", {"value": "blue"})
    stale = sub.add_node("Stale", {})
    sub.add_edge_unchecked(fact, "stale", stale)
    previous = None
    for i in range(size):
        node = sub.add_node("Unrelated", {"ordinal": i, "payload": "x" * 24})
        if previous is not None:
            sub.add_edge_unchecked(previous, "next", node)
        previous = node
    return sub, fact

def outcome_signature(result):
    return {
        "steps_run": result.steps_run,
        "converged": result.converged,
        "n_conclusions": result.n_conclusions,
        "conclusions": result.conclusions,
        "derived_only": result.derived_only,
    }

def branch_counts(delta):
    return {key: len(delta.get(key, [])) for key in
            ("nodes_added", "nodes_changed", "nodes_removed", "edges_added", "edges_removed")}

def worker(size: int, repeat: int) -> dict:
    from domains.imagination import imagine
    sub, fact = make_fixture(size)
    native = sub._inner
    before_graph = native.graph_to_dict()
    before_rules = json.dumps(native.export_rules(), sort_keys=True, separators=(",", ":"), default=str)
    started = time.perf_counter_ns()
    snapshot = sub.snapshot()
    snapshot_capture_ms = (time.perf_counter_ns() - started) / 1_000_000
    base_revision = list(snapshot.source_revision)
    order = list(BACKENDS if repeat % 2 == 0 else reversed(BACKENDS))
    results = {}
    for backend in order:
        branch_rows = []
        arm_started = time.perf_counter_ns()
        for ordinal in range(5):
            hypothesis = {
                "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {"candidate_ordinal": ordinal}}],
                "edges": [{"src": "h", "type": "contradicts", "tgt": fact.value}],
            }
            started = time.perf_counter_ns()
            result = imagine(
                sub, focus_nodes=[fact], focus_hops=2, hypothesis=hypothesis,
                steps=2, cut_grounding=False, snapshot_backend=backend,
                _snapshot_handle=snapshot if backend == "native_reusable_snapshot" else None,
                _measure_phases=True, record_trace=False,
            )
            wall_ms = (time.perf_counter_ns() - started) / 1_000_000
            terminal_probe_progress = result.detached._inner.tick_graph_then_struct(1)
            branch_rows.append({
                "ordinal": ordinal, "wall_ms": wall_ms,
                "terminal_probe_progress": terminal_probe_progress,
                "phase_timings_ms": result.phase_timings_ms,
                "outcome": outcome_signature(result),
                "conclusions_counts": branch_counts(result.conclusions),
                "derived_only_counts": branch_counts(result.derived_only),
            })
        results[backend] = {"batch_wall_ms": (time.perf_counter_ns() - arm_started) / 1_000_000,
                            "branches": branch_rows}
    after_graph = native.graph_to_dict()
    after_rules = json.dumps(native.export_rules(), sort_keys=True, separators=(",", ":"), default=str)
    later = snapshot.fork()
    later_graph = later.graph_to_dict()
    primary_unchanged = before_graph == after_graph and before_rules == after_rules
    later_isolated = (later_graph == before_graph and
                      all(edge["type"] != "yields" for edge in later_graph["edges"]))
    # Worker-level equality is checked here as an immediate fail-closed gate.
    reference = [results[BACKENDS[0]]["branches"][i]["outcome"] for i in range(5)]
    exact_parity = all([row["branches"][i]["outcome"] for i in range(5)] == reference
                       for row in results.values())
    nonempty = all(
        all(branch["outcome"]["converged"] and branch["outcome"]["steps_run"] == 1
            and branch["terminal_probe_progress"] == 0
            and any(v > 0 for v in branch["derived_only_counts"].values())
            and branch["derived_only_counts"]["nodes_added"] > 0
            and branch["derived_only_counts"]["nodes_changed"] > 0
            and branch["derived_only_counts"]["nodes_removed"] > 0
            and branch["derived_only_counts"]["edges_added"] > 0
            and branch["derived_only_counts"]["edges_removed"] > 0
            for branch in arm["branches"])
        for arm in results.values())
    return {"schema": "ThoughtexperimentProductiveResidualWorkerV1", "size": size,
            "repeat_index": repeat, "worker_pid": os.getpid(),
            "base_revision": base_revision, "snapshot_capture_ms": snapshot_capture_ms,
            "backend_order": order, "backends": results,
            "primary_unchanged": primary_unchanged, "later_snapshot_fork_isolated": later_isolated,
            "exact_backend_residual_parity": exact_parity, "nonempty_derived_residual": nonempty}

def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), int(sys.argv[3])), separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    rows = []
    for size in (0, 10000, 50000):
        for repeat in range(5):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(size), str(repeat)],
                                  cwd=ROOT, text=True, capture_output=True)
            if proc.returncode:
                raise SystemExit(f"worker failed size={size} repeat={repeat}: {proc.stderr[-5000:]}")
            row = json.loads(proc.stdout)
            rows.append(row)
            print(f"[{len(rows)}/15] size={size} repeat={repeat}", flush=True)
    import substrate_rs as srs
    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentProductiveResidualSnapshotCaptureV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
        "binary": {"path": str(binary), "sha256": sha(binary)},
        "source_sha256": {path: sha(ROOT / path) for path in SOURCES},
        "protocol": {"sizes": [0, 10000, 50000], "repeats_per_size": 5, "branches_per_backend": 5,
                     "backends": list(BACKENDS), "backend_order": "alternates by repeat index",
                     "analysis_pythonpath": str(ROOT), "closure_budget_steps": 2,
                     "expected_progress_steps": 1, "terminal_probe_expected_progress": 0},
        "workers": rows,
    }
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    analyzer_env = dict(os.environ)
    analyzer_env["PYTHONPATH"] = str(ROOT) + os.pathsep + analyzer_env.get("PYTHONPATH", "")
    subprocess.run([sys.executable, str(ROOT / "scripts/analyze_thoughtexperiment_productive_residual_snapshot_v1.py")],
                   cwd=ROOT, env=analyzer_env, check=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
