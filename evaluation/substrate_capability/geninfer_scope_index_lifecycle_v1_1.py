#!/usr/bin/env python3
"""Paired live-Substrate lifecycle scaling for frame-scoped GenInfer."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import build_is_stale, provenance_line
from domains import reflective_faculty as rf
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from substrate_rs import Substrate, _native

RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_SCOPE_INDEX_LIFECYCLE_V1_1_AMENDMENT_20261005.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_geninfer_scope_index_lifecycle_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/geninfer_scope_index_lifecycle_v1_1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/geninfer_scope_index_lifecycle_v1_1_20261005.json"
DECOYS = (0, 1000, 10000)
REPLICATES = (0, 1, 2)
MODES = ("frame_scoped", "frame_scoped_indexed")
POINTS = [(0, 0), (1, 0), (0, 1), (1, 1)]
DIM_TYPES = ["pred", "coord:x", "coord:y", "value"]
MAPS = [[2, 1, 1, 1], [2, -1, 1, 1], [2, 1, 1, 2], [1, 1, 1, 2]]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def seed_closure() -> list[str]:
    pending = [*__import__("substrate.boot_core", fromlist=["CORE_SEEDS"]).CORE_SEEDS,
               "shape_decode_loop"]
    seen: set[str] = set()
    while pending:
        name = str(pending.pop())
        if name in seen:
            continue
        seen.add(name)
        pending.extend(str(dep) for dep in manifest_for(name).get("depends_on", ()))
    return sorted(f"seeds/{name}.json" for name in seen)


def source_paths() -> list[str]:
    base = [
        "domains/engine_provenance.py", "domains/reflective_faculty.py",
        "substrate/boot_core.py", "substrate/seed_loader.py",
        "runners/dsl/src/shape_decode.rs", "runners/dsl/src/term.rs",
        "runners/dsl/src/reflect.rs", "runners/dsl/src/jsonio.rs",
        "runners/dsl/src/graph.rs", "runners/dsl/src/substrate.rs",
        "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
        "runners/dsl/src/persist.rs", "runners/dsl/src/grammar.rs",
        "runners/dsl/src/sym.rs", "runners/dsl/src/access_trace.rs",
        "runners/dsl/src/lib.rs",
        "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
        "runners/dsl/python/substrate_rs/__init__.py",
        "runners/dsl/python/substrate_rs/_native.build.json",
        str(RUNNER.relative_to(ROOT)), str(PROTOCOL.relative_to(ROOT)),
        str(ANALYZER.relative_to(ROOT)),
    ]
    return sorted(set((*base, *seed_closure())))


def frozen() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "source_sha256": {path: sha(ROOT / path) for path in source_paths()},
        "native_path": str(native), "native_sha256": sha(native),
        "engine": provenance_line(),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
    }


def cases() -> list[dict]:
    return [{"id": f"{mode}_d{decoys}_r{rep}_trace{int(trace)}", "mode": mode,
             "decoys": decoys, "replicate": rep, "trace": trace}
            for decoys in DECOYS for mode in MODES for rep in REPLICATES
            for trace in (False, True)]


def transform(matrix: list[int], rows: list[list]) -> list[list]:
    a, b, c, d = matrix
    return [[row[0], a * row[1] + b * row[2], c * row[1] + d * row[2], row[3]]
            for row in rows]


def rows_for(frame: int) -> list[list]:
    return [[f"frame{frame}_p{i}", x, y, "signal"] for i, (x, y) in enumerate(POINTS)]


def receipt_data(sub, obs) -> list[dict]:
    receipts = []
    for node in sub.neighbours(obs, "has_transform"):
        attrs = sub.node(node)["attrs"]
        receipts.append({key: attrs.get(key) for key in
                         ("source", "generator", "generators", "base", "dim", "dims", "k", "ks", "transforms")
                         if key in attrs})
    return receipts


def exact_bucket(sub, scope_id: str) -> tuple[list[int], list[int]]:
    indexed = sorted(int(node.value) for node in sub._inner.nodes_where(
        "ShapeSignature", "scope_id", scope_id))
    scanned = sorted(int(node.value) for node in sub.nodes("ShapeSignature")
                     if sub.node(node)["attrs"].get("scope_id") == scope_id)
    return indexed, scanned


def make_task(sub, agent, case_id: str) -> tuple[list[dict], int]:
    specs = []
    started = time.perf_counter_ns()
    for frame, matrix in enumerate(MAPS[:2]):
        base = rows_for(frame)
        goal = transform(matrix, base)
        scope_id = f"frame_scope_{case_id}_{frame}"
        provenance = hashlib.sha256(canonical({"case": case_id, "frame": frame,
                                                "base": base, "goal": goal}).encode()).hexdigest()
        sub.add_node("FrameScope", {"scope_id": scope_id, "frame": frame,
                                     "case_id": case_id,
                                     "provenance_kind": "locked_synthetic_frame_assignment",
                                     "provenance_sha256": provenance})
        part = sub.add_node("ShapeSignature", {
            "name": f"target_frame_{frame}", "signature": json.dumps(base),
            "kind": "faculty", "faculty": "explicit_scope", "dim_types": DIM_TYPES,
            "frame_id": frame, "scope_id": scope_id,
        })
        obs = sub.add_node("Observation", {
            "signature": goal, "key": ["scope_index_lifecycle", case_id, frame],
            "status": "decoded", "residual": goal, "decoded_epoch": 0.0,
            "dim_types": DIM_TYPES, "frame_id": frame, "scope_id": scope_id,
        })
        sub.add_edge(agent, "observed", obs)
        specs.append({"frame": frame, "matrix": matrix, "base": base, "goal": goal,
                      "part": part, "obs": obs, "scope_id": scope_id,
                      "provenance_sha256": provenance})
    return specs, time.perf_counter_ns() - started


def scan_population(sub, scope_id: str) -> list[int]:
    return sorted(int(node.value) for node in sub.nodes("ShapeSignature")
                  if sub.node(node)["attrs"].get("scope_id") == scope_id)


def execute(case: dict) -> dict:
    if build_is_stale(str(ROOT)):
        raise RuntimeError("native extension is stale")
    source_before = frozen()
    boot_start = time.perf_counter_ns()
    sub, agent = boot_core()
    native = rf._native_eval2(sub)
    rf._ensure_shape_decode_loop(sub, native, agent)
    boot_ns = time.perf_counter_ns() - boot_start
    hwm = {"after_boot_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
    sub.set_attr(agent, "gen_infer_enabled", 1.0)
    sub.set_attr(agent, "gen_infer_scope_required", 1.0)

    decoy_ids = []
    decoy_start = time.perf_counter_ns()
    for i in range(case["decoys"]):
        decoy_ids.append(sub.add_node("ShapeSignature", {
            "name": f"lifecycle_decoy_{i}", "signature": "[]", "kind": "faculty",
            "faculty": "lifecycle_decoy", "dim_types": DIM_TYPES,
            "scope_id": "unrelated_decoy_scope", "frame_id": -1,
        }))
    decoy_insert_ns = time.perf_counter_ns() - decoy_start
    hwm["after_decoys_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    index_build_ns = 0
    indexed = case["mode"] == "frame_scoped_indexed"
    if indexed:
        start = time.perf_counter_ns()
        sub._inner.declare_attr_index("ShapeSignature", "scope_id")
        index_build_ns = time.perf_counter_ns() - start
    hwm["after_index_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    specs, task_insert_ns = make_task(sub, agent, case["id"])
    task_membership = []
    for spec in specs:
        scanned = scan_population(sub, spec["scope_id"])
        got = exact_bucket(sub, spec["scope_id"])[0] if indexed else scanned
        task_membership.append(got == scanned and spec["part"].value in got)
    decoy_index_parity = (not indexed or exact_bucket(sub, "unrelated_decoy_scope")[0]
                          == exact_bucket(sub, "unrelated_decoy_scope")[1])

    # Measure a full native Substrate fork and a fixed branch-local index update.
    fork_start = time.perf_counter_ns()
    branch = sub.fork_shared_graph_pages_experiment()
    fork_ns = time.perf_counter_ns() - fork_start
    hwm["after_fork_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    parent_before = canonical(sub.graph_to_dict())
    fork_matches = canonical(branch.graph_to_dict()) == parent_before
    mutation_ids = decoy_ids[:min(32, len(decoy_ids))]
    mutation_start = time.perf_counter_ns()
    for node in mutation_ids:
        branch.set_attr(node, "scope_id", "mutated_decoy_scope")
    branch_mutation_ns = time.perf_counter_ns() - mutation_start
    if indexed and mutation_ids:
        mutated_index, mutated_scan = exact_bucket(branch, "mutated_decoy_scope")
        original_index, original_scan = exact_bucket(branch, "unrelated_decoy_scope")
        branch_mutation_parity = (mutated_index == mutated_scan and original_index == original_scan
                                  and len(mutated_index) == len(mutation_ids))
    else:
        branch_mutation_parity = all(
            sorted(int(n.value) for n in branch.nodes("ShapeSignature")
                   if branch.node(n)["attrs"].get("scope_id") == value)
            == scan_population(branch, value)
            for value in ("mutated_decoy_scope", "unrelated_decoy_scope"))
    branch_isolated = canonical(sub.graph_to_dict()) == parent_before

    serialize_start = time.perf_counter_ns()
    graph_value = sub.graph_to_dict()
    serialize_ns = time.perf_counter_ns() - serialize_start
    restored = Substrate()
    restore_start = time.perf_counter_ns()
    restored.graph_from_dict(graph_value)
    restore_ns = time.perf_counter_ns() - restore_start
    restore_matches = canonical(restored.graph_to_dict()) == canonical(graph_value)
    hwm["after_restore_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    redeclare_ns = 0
    if indexed:
        redeclare_start = time.perf_counter_ns()
        restored._inner.declare_attr_index("ShapeSignature", "scope_id")
        redeclare_ns = time.perf_counter_ns() - redeclare_start
        restore_index_matches = all(
            exact_bucket(restored, spec["scope_id"])[0]
            == exact_bucket(restored, spec["scope_id"])[1]
            for spec in specs)
    else:
        restore_index_matches = True

    before_nodes = len(list(sub.nodes()))
    before_edges = sub.edge_count()
    hwm_before = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    cpu_start = time.process_time_ns()
    closure_start = time.perf_counter_ns()
    if case["trace"]:
        _native.Substrate.runtime_access_trace_reset()
        _native.Substrate.runtime_work_trace_set_all_scopes_enabled(True)
    try:
        work = int(native.run_rules())
    finally:
        if case["trace"]:
            _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
    closure_wall_ns = time.perf_counter_ns() - closure_start
    closure_cpu_ns = time.process_time_ns() - cpu_start
    if case["trace"]:
        trace_rows, trace_dropped = _native.Substrate.runtime_work_trace_all_scopes_snapshot()
    else:
        trace_rows, trace_dropped = [], 0
    hwm_after = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    hwm["after_closure_kib"] = hwm_after

    outputs = []
    for spec in specs:
        attrs = sub.node(spec["obs"])["attrs"]
        receipts = receipt_data(sub, spec["obs"])
        generators = []
        for node in sub.nodes("DimensionGenerator"):
            gen_attrs = sub.node(node)["attrs"]
            if gen_attrs.get("kind") == "linear":
                generators.append(list(gen_attrs.get("matrix") or []))
        outputs.append({"frame": spec["frame"], "matrix": spec["matrix"],
                        "status": attrs.get("status"), "receipts": receipts,
                        "oracle_exact": spec["goal"] == transform(spec["matrix"], spec["base"]),
                        "target_generator_present": spec["matrix"] in generators})
    source_after = frozen()
    return {
        "pid": os.getpid(), "case": case, "engine": source_before["engine"],
        "source_stable": source_before == source_after,
        "source_before": source_before, "source_after": source_after,
        "decoy_count": len(decoy_ids), "shape_signature_population": len(list(sub.nodes("ShapeSignature"))),
        "node_count_before_closure": before_nodes, "edge_count_before_closure": before_edges,
        "boot_ns": boot_ns, "decoy_insert_ns": decoy_insert_ns,
        "index_build_ns": index_build_ns, "task_insert_ns": task_insert_ns,
        "fork_ns": fork_ns, "branch_mutation_ns": branch_mutation_ns,
        "branch_mutation_count": len(mutation_ids), "fork_matches": fork_matches,
        "branch_isolated": branch_isolated,
        "branch_mutation_parity": branch_mutation_parity,
        "task_membership_parity": all(task_membership),
        "decoy_index_parity": decoy_index_parity,
        "serialize_ns": serialize_ns, "restore_ns": restore_ns,
        "restore_matches": restore_matches, "restore_redeclare_ns": redeclare_ns,
        "restore_index_matches": restore_index_matches,
        "closure_work": work, "closure_wall_ns": closure_wall_ns,
        "closure_cpu_ns": closure_cpu_ns, "hwm_before_kib": hwm_before,
        "hwm_after_kib": hwm_after, "outputs": outputs,
        "hwm_by_phase_kib": hwm,
        "runtime_work_trace": {"rows": [list(row) for row in trace_rows],
                               "dropped": int(trace_dropped)},
        "nodes_after_closure": len(list(sub.nodes())), "edges_after_closure": sub.edge_count(),
    }


def main() -> int:
    args = sys.argv[1:]
    if args == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite lock or capture")
        if build_is_stale(str(ROOT)):
            raise SystemExit("native extension is stale")
        lock = {"schema": "GenInferScopeIndexLifecycleV1_1Lock", "sources": frozen(),
                "cases": cases(), "decoys": DECOYS, "modes": MODES,
                "replicates": REPLICATES, "fixed_mutation_count": 32,
                "matrices": MAPS[:2]}
        LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if len(args) == 3 and args[0] == "--worker":
        lock = json.loads(LOCK.read_text())
        case = next((item for item in lock["cases"] if item["id"] == args[1]), None)
        if case is None:
            raise SystemExit("unknown locked case")
        if frozen() != lock["sources"]:
            raise SystemExit("source/build drift")
        print(json.dumps(execute(case), sort_keys=True))
        return 0
    if args != ["--run"]:
        raise SystemExit("usage: --lock | --worker CASE_ID REPLICATE | --run")
    lock = json.loads(LOCK.read_text())
    if frozen() != lock["sources"]:
        raise SystemExit("source/build drift from lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    results = []
    for case in lock["cases"]:
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", case["id"], str(case["replicate"])],
                              cwd=ROOT, env=env, text=True, capture_output=True, check=True, timeout=300)
        results.append(json.loads(proc.stdout))
    if frozen() != lock["sources"] or not all(row["source_stable"] for row in results):
        raise SystemExit("source/build drift during capture")
    OUT.write_text(json.dumps({"schema": "GenInferScopeIndexLifecycleV1_1Results",
                               "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                               "host": platform.platform(), "lock_sha256": sha(LOCK),
                               "source_manifest": frozen(), "cases": results},
                              indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(),
                      "case_count": len(results), "source_stable": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
