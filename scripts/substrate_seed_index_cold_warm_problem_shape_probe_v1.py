#!/usr/bin/env python3
"""Locked fresh-process cold/warm cache comparison on ProblemShape workloads."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
LOCK = ROOT / "evaluation/substrate_capability/seed_index_cold_warm_problem_shape_lock_20260925.json"
CORPUS_LOCK = ROOT / "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_seed_index_cold_warm_problem_shape_v1_20260925.json"
PART = ROOT / "evaluation/reports/substrate_seed_index_cold_warm_problem_shape_v1_partial_20260925.json"
SOURCES = [
    "scripts/substrate_problem_shape_rule_order_seed_transform_v1_4.py",
    "scripts/substrate_problem_shape_rule_order_preservation_v1_7.py",
    "scripts/substrate_problem_shape_population_scale.py",
    "scripts/substrate_problem_shape_induction_economics.py",
    "substrate/boot_all.py", "substrate/world_adapter.py", "substrate/seed_loader.py",
    "domains/problem_shape.py", "domains/solver_dispatch.py",
    "domains/problem_decomposition.py", "worlds/bigville_can_beliefs.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_sources() -> dict[str, str]:
    return {rel: sha(ROOT / rel) for rel in SOURCES}


def load_snapshot_builder():
    import importlib.util
    path = ROOT / "scripts/substrate_problem_shape_rule_order_seed_transform_v1_4.py"
    spec = importlib.util.spec_from_file_location("seed_transform_v14", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def projection(row: dict) -> dict:
    record_keys = (
        "label", "observation_status_initial", "observation_status_final",
        "covered_by_final", "mint_count_delta", "problem_shape_candidate_pairs",
        "problem_shape_term_evaluations",
    )
    records = []
    for record in row["records"]:
        settle = record.get("post_observe_settle_report", {})
        records.append({
            key: record.get(key) for key in record_keys
            if key in record
        } | {"settle_status": settle.get("status"),
             "settle_progress_count": settle.get("progress_count"),
             "scale_audit": record.get("scale_audit", {})})
    keys = (
        "seed_rule_order_sha256", "seed_rule_names", "seed_problem_shape_rule_positions",
        "pre_observation_rule_order_sha256", "pre_observation_rule_names",
        "pre_observation_problem_shape_rule_positions", "seed_load_order",
        "seed_load_failed_ids", "seed_load_failure_count", "active_problem_shape_rule_positions",
        "active_rule_order_sha256", "final_codebook_shape_count", "total_mints",
        "problem_shape_candidate_pairs_total", "problem_shape_term_evaluations_total",
        "checks", "all_checks_pass",
    )
    return {key: row.get(key) for key in keys} | {"records": records}


def run_worker(mix: str, mode: str, seed_dir: str) -> tuple[dict, str]:
    from substrate.boot_all import _read_seed_index, _seed_index_cache_path
    import importlib.util
    path = ROOT / "scripts/substrate_problem_shape_population_scale.py"
    spec = importlib.util.spec_from_file_location("population_scale_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    cache_path = Path(_seed_index_cache_path(seed_dir))
    if mode == "cold":
        cache_path.unlink(missing_ok=True)
        pre_cache_hash = None
    else:
        _read_seed_index(seed_dir)
        pre_cache_hash = sha(cache_path)
    code = (
        "import json,sys;sys.path[:0]=['.','runners/dsl/python','scripts'];"
        "import substrate_problem_shape_population_scale as m;"
        f"r=m.worker(32,{mix!r},'dynamic',{seed_dir!r});"
        "print(json.dumps(r,sort_keys=True));sys.exit(0 if r['all_checks_pass'] else 2)"
    )
    env = {**os.environ, "PYTHONHASHSEED": "0",
           "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=900)
    if proc.returncode:
        raise RuntimeError(f"{mix}/{mode} worker failed: {proc.stdout[-1500:]} {proc.stderr[-1500:]}")
    row = json.loads(proc.stdout.strip().splitlines()[-1])
    post_cache_hash = sha(cache_path)
    if pre_cache_hash is not None and post_cache_hash != pre_cache_hash:
        raise RuntimeError(f"{mix}/{mode} cache bytes changed during worker")
    if not row.get("all_checks_pass"):
        raise RuntimeError(f"{mix}/{mode} task semantic/fixed-point checks failed")
    return row, {"before": pre_cache_hash, "after": post_cache_hash}


def main() -> int:
    lock = json.loads(LOCK.read_text())
    prereg = ROOT / lock["preregistration"]
    if sha(prereg) != lock["preregistration_sha256"]:
        raise SystemExit("preregistration hash mismatch")
    if current_sources() != lock["sources"]:
        raise SystemExit("source/build lock mismatch")
    corpus_lock = json.loads(CORPUS_LOCK.read_text())
    if corpus_lock["corpus_digest"] != lock["corpus_digest"]:
        raise SystemExit("frozen corpus lock mismatch")
    import substrate_problem_shape_rule_order_preservation_v1_7 as v17
    if v17.seed_corpus_digest() != lock["corpus_digest"]:
        raise SystemExit("current seed manifest hashes differ from frozen corpus lock")
    if OUT.exists() or PART.exists():
        raise SystemExit("refusing to overwrite a prior result/checkpoint")
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    stale = subprocess.check_output([
        sys.executable, "-c",
        "from domains.engine_provenance import build_is_stale;print('\\n'.join(build_is_stale('.')))"],
        cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale: {stale}")

    transform = load_snapshot_builder()
    snapshot = transform.build()
    if snapshot["source_corpus_digest"] != lock["snapshot_source_digest"]:
        raise SystemExit("source seed corpus changed during snapshot creation")
    snapshot_paths = [Path(snapshot[k]) for k in ("baseline_seed_dir", "candidate_seed_dir")]
    if any(p.is_symlink() for d in snapshot_paths for p in d.rglob("*.json")):
        raise SystemExit("snapshot contains symlinked seed files")

    arms = {}
    pids: set[int] = set()
    for mix in lock["configuration"]["mixes"]:
        arms[mix] = {}
        for mode in ("cold", "warm"):
            row, cache_hashes = run_worker(mix, mode, snapshot["baseline_seed_dir"])
            if row["process_id"] in pids:
                raise RuntimeError("worker process IDs are not unique")
            pids.add(row["process_id"])
            arms[mix][mode] = {"cache_sha256": cache_hashes, "worker": row,
                               "projection": projection(row)}
            PART.write_text(json.dumps({"arms": arms, "snapshot": snapshot},
                                       indent=2, sort_keys=True) + "\n")
            print(json.dumps({"mix": mix, "mode": mode,
                              "all_checks_pass": row["all_checks_pass"],
                              "process_id": row["process_id"]}), flush=True)

    comparisons = {}
    for mix, modes in arms.items():
        comparisons[mix] = {
            "full_projection_equal": modes["cold"]["projection"] == modes["warm"]["projection"],
            "seed_load_order_equal": modes["cold"]["worker"]["seed_load_order"] == modes["warm"]["worker"]["seed_load_order"],
            "rule_order_equal": modes["cold"]["worker"]["seed_rule_order_sha256"] == modes["warm"]["worker"]["seed_rule_order_sha256"],
            "semantic_checks_pass": all(modes[x]["worker"]["all_checks_pass"] for x in ("cold", "warm")),
        }
    after_sources = current_sources()
    if after_sources != lock["sources"]:
        raise RuntimeError("locked source/build inputs changed during the run")
    result = {
        "schema_version": 1,
        "probe_id": "seed-index-cold-warm-problem-shape-v1-20260925",
        "locked_inputs": lock,
        "lock_sha256": sha(LOCK),
        "preregistration_sha256": sha(prereg),
        "source_hashes_after": after_sources,
        "seed_snapshot": snapshot,
        "unique_processes": len(pids) == 4,
        "comparisons": comparisons,
        "all_gates_pass": len(pids) == 4 and all(
            c["full_projection_equal"] and c["semantic_checks_pass"]
            for c in comparisons.values()),
        "arms": arms,
        "interpretation": (
            "Cold/warm exact task-and-work parity on two authored N=32 ProblemShape "
            "workloads and one frozen corpus; timing and RSS are excluded from the "
            "parity gate and remain descriptive."),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    PART.unlink(missing_ok=True)
    print(json.dumps({"all_gates_pass": result["all_gates_pass"],
                      "comparisons": comparisons, "output": str(OUT)}))
    return 0 if result["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
