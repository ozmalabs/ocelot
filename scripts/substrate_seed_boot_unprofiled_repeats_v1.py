#!/usr/bin/env python3
"""Measure unprofiled cold/warm full seed boot on a frozen corpus."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
LOCK = ROOT / "evaluation/substrate_capability/seed_boot_unprofiled_repeats_lock_20260925.json"
CORPUS = ROOT / "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SEED_BOOT_UNPROFILED_REPEATS_PREREG_20260925.md"
OUT = ROOT / "evaluation/reports/substrate_seed_boot_unprofiled_repeats_v1_20260925.json"
PART = ROOT / "evaluation/reports/substrate_seed_boot_unprofiled_repeats_v1_partial_20260925.json"
SOURCES = [
    "scripts/substrate_problem_shape_rule_order_seed_transform_v1_4.py",
    "scripts/substrate_problem_shape_rule_order_preservation_v1_7.py",
    "substrate/boot_all.py", "substrate/world_adapter.py", "substrate/seed_loader.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json",
]
SCHEDULE = ["cold", "warm", "warm", "cold", "cold", "warm"]
CHILD = """
import hashlib,json,sys,time
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from substrate_rs import _native
w0,c0=time.perf_counter_ns(),time.process_time_ns();a=WorldAdapter(seeds=());r=load_all_seeds(a,seed_dir=sys.argv[1]);wall=time.perf_counter_ns()-w0;cpu=time.process_time_ns()-c0
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
rules=sorted((x for x in a.inner.rule_access_sets() if x[2]),key=lambda x:int(x[0]));names=[str(x[1]) for x in rules]
print(json.dumps({'wall_ns':wall,'cpu_ns':cpu,'report':r,'node_count':a.inner.node_count(),'edge_count':a.inner.edge_count(),'graph_sha256':h(a.inner.graph_to_dict()),'grammar_sha256':h(a.inner.grammar_to_json()),'rule_store_sha256':h(a.inner.export_rules()),'rule_access_sha256':h(a.inner.rule_access_sets()),'rule_order':names,'rule_order_sha256':h(names),'process_id':__import__('os').getpid()}))
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    return {path: sha(ROOT / path) for path in SOURCES}


def build_snapshot():
    import importlib.util
    path = ROOT / "scripts/substrate_problem_shape_rule_order_seed_transform_v1_4.py"
    spec = importlib.util.spec_from_file_location("seed_transform_v14", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.build()


def main() -> int:
    lock = json.loads(LOCK.read_text())
    if sha(PREREG) != lock["preregistration_sha256"] or sha(Path(__file__)) != lock["runner_sha256"]:
        raise SystemExit("protocol or runner hash mismatch")
    if source_hashes() != lock["sources"]:
        raise SystemExit("source/build lock mismatch")
    corpus = json.loads(CORPUS.read_text())
    from substrate_problem_shape_rule_order_preservation_v1_7 import seed_corpus_digest
    if corpus["corpus_digest"] != lock["ordered_corpus_digest"] or seed_corpus_digest() != lock["ordered_corpus_digest"]:
        raise SystemExit("ordered seed-corpus digest mismatch")
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    stale = subprocess.check_output([sys.executable, "-c",
        "from domains.engine_provenance import build_is_stale;print('\\n'.join(build_is_stale('.')))"],
        cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale: {stale}")
    snapshot = build_snapshot()
    if snapshot["source_corpus_digest"] != lock["canonical_source_digest"]:
        raise SystemExit("canonical source digest mismatch")
    seed = Path(snapshot["baseline_seed_dir"])
    for item in corpus["manifests"]:
        if sha(seed / item["path"]) != item["sha256"]:
            raise SystemExit(f"snapshot differs from corpus lock: {item['path']}")
    if OUT.exists() or PART.exists():
        raise SystemExit("refusing to overwrite prior startup result/checkpoint")

    from substrate.boot_all import _read_seed_index, _seed_index_cache_path
    cache = Path(_seed_index_cache_path(str(seed)))
    arms = []
    for idx, mode in enumerate(SCHEDULE, 1):
        if mode == "cold":
            cache.unlink(missing_ok=True)
            before = None
        else:
            _read_seed_index(str(seed))
            before = sha(cache)
        worker_env = {**env, "PYTHONHASHSEED": "0"}
        proc = subprocess.run([sys.executable, "-c", CHILD, str(seed)], cwd=ROOT,
                              env=worker_env, text=True, capture_output=True, timeout=900)
        if proc.returncode:
            raise RuntimeError(f"{mode} boot worker {idx} failed: {proc.stderr[-2000:]}")
        row = json.loads(proc.stdout.strip().splitlines()[-1])
        after = sha(cache)
        if before is not None and before != after:
            raise RuntimeError(f"warm cache changed during worker {idx}")
        arm = {"replicate": idx, "cache_mode": mode, "cache_sha256_before": before,
               "cache_sha256_after": after, "worker": row}
        arms.append(arm)
        PART.write_text(json.dumps({"arms": arms, "snapshot": snapshot}, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"replicate": idx, "cache_mode": mode,
                          "wall_ns": row["wall_ns"], "cpu_ns": row["cpu_ns"],
                          "nodes": row["node_count"], "edges": row["edge_count"]}), flush=True)

    state_keys = ("report", "node_count", "edge_count", "graph_sha256", "grammar_sha256",
                  "rule_store_sha256", "rule_access_sha256", "rule_order", "rule_order_sha256")
    fingerprints = [{key: arm["worker"][key] for key in state_keys} for arm in arms]
    hashes_after = source_hashes()
    if hashes_after != lock["sources"] or sha(Path(__file__)) != lock["runner_sha256"]:
        raise RuntimeError("locked sources changed during measurement")
    result = {"schema_version": 1, "probe_id": "seed-boot-unprofiled-repeats-v1-20260925",
              "runner_sha256": sha(Path(__file__)), "preregistration_sha256": sha(PREREG),
              "lock_sha256": sha(LOCK), "source_hashes_after": hashes_after,
              "seed_snapshot": snapshot, "schedule": SCHEDULE, "arms": arms,
              "all_boot_states_equal": all(fp == fingerprints[0] for fp in fingerprints),
              "unique_processes": len({a['worker']['process_id'] for a in arms}) == 6,
              "interpretation": "Unprofiled full seed boot startup envelope on one corpus/host; setup imports are excluded and no task operation is run."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    PART.unlink(missing_ok=True)
    print(json.dumps({"all_boot_states_equal": result["all_boot_states_equal"],
                      "unique_processes": result["unique_processes"], "output": str(OUT)}))
    return 0 if result["all_boot_states_equal"] and result["unique_processes"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
