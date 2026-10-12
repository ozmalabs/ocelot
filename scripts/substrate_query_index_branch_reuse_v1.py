#!/usr/bin/env python3
"""Measure immutable query-index reuse across synthetic hypothesis branches."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import engine_preamble, engine_provenance, rust_source_fingerprint
engine_preamble()
from domains.generator import synthesize
from domains.query_selection import QueryRankingIndex, rank_queries_by_disagreement
from substrate_rs import _native
import jabberwock_closes_the_euler_tie as euler

STEM = "substrate_query_index_branch_reuse_v1_20260930"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_QUERY_INDEX_BRANCH_REUSE_V1_PREREG_20260930.md"
SOURCES = (
    "domains/generator.py", "domains/query_selection.py", "domains/engine_provenance.py",
    "scripts/jabberwock_closes_the_euler_tie.py",
    "scripts/substrate_query_index_branch_reuse_v1.py",
    "scripts/analyze_substrate_query_index_branch_reuse_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_QUERY_INDEX_BRANCH_REUSE_V1_PREREG_20260930.md",
)
BRANCH_BATCHES = (1, 5, 20)
REPS = 5
SEED = 20260930
OPS = ("Plus", "Times", "Minus", "Div")
CONSTS = (0, 1, 2, -1)


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def lock_payload() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "schema_version": 1,
        "sources": {name: digest(ROOT / name) for name in SOURCES},
        "native_extension": {"path": str(native), "sha256": digest(native)},
        "native_manifest_sha256": digest(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "engine_provenance": engine_provenance(),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"anchors": [name for name, _ in euler.KNOWN_COMPLEXES],
                   "batch_sizes": list(BRANCH_BATCHES), "repetitions": REPS,
                   "seed": SEED, "candidate_names": [n for n, _ in euler._family()],
                   "target_sampling": "uniform without replacement over returned fitting hypotheses",
                   "absolute_numeric_tolerance": 1e-9, "arms": ["uncached", "cached"]},
    }


def approx_heap(value, seen=None):
    if seen is None:
        seen = set()
    oid = id(value)
    if oid in seen:
        return 0
    seen.add(oid)
    total = sys.getsizeof(value)
    if isinstance(value, dict):
        total += sum(approx_heap(k, seen) + approx_heap(v, seen) for k, v in value.items())
    elif isinstance(value, (list, tuple, set, frozenset)):
        total += sum(approx_heap(v, seen) for v in value)
    return total


def numeric_equal(a, b):
    try:
        return abs(float(a) - float(b)) <= 1e-9
    except (TypeError, ValueError):
        return a == b


def make_pool(substrate, anchor_faces, candidates):
    oracle = euler._make_labeller(substrate)
    started, cpu = time.perf_counter(), time.process_time()
    result = synthesize(
        substrate, [(euler.describe(anchor_faces), oracle(anchor_faces))],
        ops=OPS, consts=CONSTS, max_size=5, timeout_s=15.0, saturate_k=5,
        probe_envs=[euler.describe(faces) for _, faces in candidates],
        max_solutions=10000, include_output_constants=False,
    )
    return result, time.perf_counter() - started, time.process_time() - cpu


def run_batch(mode, target_ids, terms, candidates, substrate, index=None):
    started, cpu = time.perf_counter(), time.process_time()
    index_build_wall = 0.0
    index_build_cpu = 0.0
    index_heap = 0
    native_selector_evals = 0
    if mode == "cached" and index is None:
        t, c = time.perf_counter(), time.process_time()
        index = QueryRankingIndex(substrate, terms, euler.describe, candidates)
        index_build_wall, index_build_cpu = time.perf_counter() - t, time.process_time() - c
        index_heap = approx_heap((index._values, index._keys))
        native_selector_evals = index.prediction_evaluations
    branch_rows = []
    target_eval_count = 0
    for target_id in target_ids:
        alive = list(range(len(terms)))
        remaining = list(range(len(candidates)))
        query_path = []
        while len(alive) > 1 and remaining:
            if mode == "cached":
                ranked = index.rank(alive, remaining)
                chosen = ranked[0]
                candidate_index = chosen["candidate_index"]
                predictions = chosen["predictions"]
                target_label = terms[target_id].evaluate(
                    euler.describe(candidates[candidate_index][1]), substrate)
                target_eval_count += 1
                alive = index.filter(alive, candidate_index, target_label)
            else:
                ranked = rank_queries_by_disagreement(
                    substrate, [terms[i] for i in alive], euler.describe,
                    [candidates[i] for i in remaining])
                native_selector_evals += len(alive) * len(remaining)
                chosen = ranked[0]
                candidate_index = next(i for i in remaining
                                       if candidates[i][0] == chosen["name"])
                predictions = chosen["predictions"]
                target_label = terms[target_id].evaluate(
                    euler.describe(candidates[candidate_index][1]), substrate)
                target_eval_count += 1
                alive = [h for h, pred in zip(alive, predictions)
                         if numeric_equal(pred, target_label)]
            query_path.append(candidates[candidate_index][0])
            remaining.remove(candidate_index)
        branch_rows.append({"target_id": target_id, "query_path": query_path,
                            "final_survivors": alive, "target_recovered": alive == [target_id]})
    return {
        "mode": mode, "branch_count": len(target_ids), "branches": branch_rows,
        "all_targets_recovered": all(row["target_recovered"] for row in branch_rows),
        "total_queries": sum(len(row["query_path"]) for row in branch_rows),
        "native_selector_prediction_evaluations": native_selector_evals,
        "target_response_evaluations": target_eval_count,
        "index_build_wall_s": index_build_wall, "index_build_cpu_s": index_build_cpu,
        "index_retained_heap_bytes": index_heap,
        "batch_wall_s": time.perf_counter() - started,
        "batch_cpu_s": time.process_time() - cpu,
        "total_wall_including_index_build_s": time.perf_counter() - started,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    lock = lock_payload()
    if args.lock:
        print(json.dumps(lock, indent=2, sort_keys=True))
        return
    if not LOCK.exists() or json.loads(LOCK.read_text()) != lock:
        raise SystemExit(f"missing or stale source lock: {LOCK}")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite existing capture: {RAW}")
    substrate = _native.Substrate()
    candidates = list(euler._family())
    anchor_rows = []
    global_start = time.perf_counter()
    for anchor_index, (anchor_name, anchor_faces) in enumerate(euler.KNOWN_COMPLEXES):
        result, generation_wall, generation_cpu = make_pool(substrate, anchor_faces, candidates)
        hypotheses = result.get("hypotheses", [])
        terms = [hyp["term"] for hyp in hypotheses]
        if result["halt_reason"] != "max_size":
            pool_complete = False
        else:
            pool_complete = True
        if len(terms) < 1:
            raise RuntimeError(f"empty generated pool at anchor {anchor_name}")
        reps = []
        for rep in range(1, REPS + 1):
            target_ids = random.Random(SEED + anchor_index * 1000 + rep).sample(
                range(len(terms)), min(20, len(terms)))
            blocks = []
            for batch_size in BRANCH_BATCHES:
                chosen_targets = target_ids[:batch_size]
                order = ["cached", "uncached"] if (anchor_index + rep) % 2 else ["uncached", "cached"]
                pair = {}
                for mode in order:
                    pair[mode] = run_batch(mode, chosen_targets, terms, candidates,
                                           substrate)
                uncached = {row["target_id"]: row for row in pair["uncached"]["branches"]}
                cached = {row["target_id"]: row for row in pair["cached"]["branches"]}
                parity = all(uncached[k] == cached[k] for k in uncached)
                blocks.append({"branch_count": batch_size, "target_ids": chosen_targets,
                               "arm_order": order, "arms": pair,
                               "exact_branch_parity": parity})
            reps.append({"replicate": rep, "batches": blocks})
        anchor_rows.append({
            "anchor_index": anchor_index, "anchor": anchor_name,
            "pool": {"size": len(terms), "halt_reason": result["halt_reason"],
                     "complete": pool_complete, "explored": result["explored"],
                     "distinct": result["distinct"],
                     "generation_wall_s": generation_wall, "generation_cpu_s": generation_cpu},
            "repetitions": reps,
        })
    raw = {"protocol": STEM, "lock": lock, "anchors": anchor_rows,
           "elapsed_s": time.perf_counter() - global_start,
           "environment": {"python": sys.version, "platform": platform.platform()},
           "worker_failures": []}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"raw": str(RAW), "elapsed_s": raw["elapsed_s"],
                      "pools": [row["pool"]["size"] for row in anchor_rows]}, sort_keys=True))


if __name__ == "__main__":
    main()
