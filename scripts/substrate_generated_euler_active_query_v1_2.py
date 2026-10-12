#!/usr/bin/env python3
"""Source-locked iterative active-query evaluation on generated Euler hypotheses."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
import sys as sys_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]

from domains.engine_provenance import engine_preamble, engine_provenance, rust_source_fingerprint
engine_preamble()
from domains.generator import synthesize
from domains.query_selection import rank_queries_by_disagreement, QueryRankingIndex
from substrate_rs import _native
import jabberwock_closes_the_euler_tie as euler

STEM = "substrate_generated_euler_active_query_v1_2_20260930"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_PREREG_20260930.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_1_AMENDMENT_20260930.md"
AMENDMENT_2 = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_2_AMENDMENT_20260930.md"
SOURCE_PATHS = (
    "domains/generator.py",
    "domains/query_selection.py",
    "domains/engine_provenance.py",
    "scripts/jabberwock_closes_the_euler_tie.py",
    "scripts/substrate_generated_euler_active_query_v1.py",
    "scripts/substrate_generated_euler_active_query_v1_1.py",
    "scripts/analyze_substrate_generated_euler_active_query_v1_1.py",
    "scripts/substrate_generated_euler_active_query_v1_2.py",
    "scripts/analyze_substrate_generated_euler_active_query_v1_2.py",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_PREREG_20260930.md",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_1_AMENDMENT_20260930.md",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_2_AMENDMENT_20260930.md",
)
ANCHORS = euler.KNOWN_COMPLEXES
RANDOM_REPS = 20
SEED = 20260930
OPS = ("Plus", "Times", "Minus", "Div")
CONSTS = (0, 1, 2, -1)
MAX_SIZE = 5
TIMEOUT_S = 15.0
MAX_SOLUTIONS = 10000

HELDOUT = (
    ("pentagon-loop", [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]]),
    ("two-hollow-triangles", [[0, 1], [1, 2], [0, 2], [3, 4], [4, 5], [3, 5]]),
    ("two-filled-triangles", [[0, 1, 2], [3, 4, 5]]),
    ("two-loops-one-vertex", [[0, 1], [1, 2], [2, 3], [3, 0], [0, 4], [4, 5], [5, 6], [6, 0]]),
    ("three-triangle-chain", [[0, 1, 2], [1, 2, 3], [2, 3, 4]]),
    ("two-tetra-boundaries", [list(c) for c in __import__("itertools").combinations(range(4), 3)] +
     [list(c) for c in __import__("itertools").combinations(range(4, 8), 3)]),
)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build_lock() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "schema_version": 1,
        "sources": {name: sha256_file(ROOT / name) for name in SOURCE_PATHS},
        "native_extension": {"path": str(native), "sha256": sha256_file(native)},
        "native_build_manifest_sha256": sha256_file(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "engine_provenance": engine_provenance(),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {
            "anchors": [name for name, _ in ANCHORS],
            "candidate_names": [name for name, _ in euler._family()],
            "heldout_names": [name for name, _ in HELDOUT],
            "policies": ["entropy_uncached", "entropy_cached", "fixed_first", "seeded_random"],
            "random_reps": RANDOM_REPS, "seed": SEED, "max_queries": 12,
            "ops": list(OPS), "consts": list(CONSTS), "max_size": MAX_SIZE,
            "timeout_s": TIMEOUT_S, "max_solutions": MAX_SOLUTIONS,
            "include_output_constants": False,
        },
    }


def equal(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) <= 1e-9
    except (TypeError, ValueError):
        return a == b


def timed_oracle(oracle, value):
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    label = oracle(value)
    return label, time.perf_counter() - wall_start, time.process_time() - cpu_start


def approximate_heap_size(value, seen=None) -> int:
    """Count retained Python container/scalar heap for the prediction matrix."""
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    total = sys_module.getsizeof(value)
    if isinstance(value, dict):
        total += sum(approximate_heap_size(k, seen) + approximate_heap_size(v, seen)
                     for k, v in value.items())
    elif isinstance(value, (list, tuple, set, frozenset)):
        total += sum(approximate_heap_size(item, seen) for item in value)
    return total


def run_anchor(anchor_index: int, anchor_name: str, anchor_faces, substrate) -> dict:
    oracle = euler._make_labeller(substrate)
    candidates = list(euler._family())
    anchor_label, anchor_oracle_wall, anchor_oracle_cpu = timed_oracle(oracle, anchor_faces)
    generation_start = time.perf_counter()
    generation_cpu = time.process_time()
    result = synthesize(
        substrate, [(euler.describe(anchor_faces), anchor_label)],
        ops=OPS, consts=CONSTS, max_size=MAX_SIZE, timeout_s=TIMEOUT_S,
        saturate_k=5, probe_envs=[euler.describe(faces) for _, faces in candidates],
        max_solutions=MAX_SOLUTIONS, include_output_constants=False,
    )
    generation = {
        "pool_size": len(result.get("hypotheses", [])),
        "halt_reason": result["halt_reason"],
        "bounded_pool_complete": result["halt_reason"] == "max_size",
        "explored": result["explored"], "distinct": result["distinct"],
        "reported_elapsed_s": result["elapsed_s"],
        "wall_s": time.perf_counter() - generation_start,
        "cpu_s": time.process_time() - generation_cpu,
        "anchor_oracle_wall_s": anchor_oracle_wall,
        "anchor_oracle_cpu_s": anchor_oracle_cpu,
    }
    hypotheses = result.get("hypotheses", [])
    terms = [item["term"] for item in hypotheses]
    cache_index = None
    cache_build_wall_s = cache_build_cpu_s = 0.0
    cache_retained_heap_bytes = 0
    if terms:
        cache_started = time.perf_counter()
        cache_cpu_started = time.process_time()
        cache_index = QueryRankingIndex(substrate, terms, euler.describe, candidates)
        cache_build_wall_s = time.perf_counter() - cache_started
        cache_build_cpu_s = time.process_time() - cache_cpu_started
        cache_retained_heap_bytes = approximate_heap_size((cache_index._values, cache_index._keys))
    runs = []
    policies = [("entropy_uncached", 0), ("entropy_cached", 0), ("fixed_first", 0)] + [
        ("seeded_random", rep) for rep in range(1, RANDOM_REPS + 1)
    ]
    for policy, replicate in policies:
        alive = list(range(len(terms)))
        remaining = list(candidates)
        random_order = None
        if policy == "seeded_random":
            seed = SEED + anchor_index * 100 + replicate
            random_order = random.Random(seed).sample(remaining, len(remaining))
        responses = []
        prediction_evaluations = 0
        selection_wall_s = 0.0
        selection_cpu_s = 0.0
        decision_compute_wall_s = 0.0
        decision_compute_cpu_s = 0.0
        matrix_cells_read = 0
        while len(alive) > 1 and remaining and terms:
            decision_started = time.perf_counter()
            decision_cpu_started = time.process_time()
            if policy in ("entropy_uncached", "entropy_cached"):
                started = time.perf_counter()
                cpu_started = time.process_time()
                if policy == "entropy_cached":
                    candidate_indices = [i for i, item in enumerate(candidates)
                                         if item in remaining]
                    ranked = cache_index.rank(alive, candidate_indices)
                    matrix_cells_read += len(alive) * len(remaining)
                else:
                    ranked = rank_queries_by_disagreement(
                        substrate, [terms[i] for i in alive], euler.describe, remaining)
                    prediction_evaluations += len(alive) * len(remaining)
                selection_wall_s += time.perf_counter() - started
                selection_cpu_s += time.process_time() - cpu_started
                selected = next(row for row in remaining if row[0] == ranked[0]["name"])
                predicted = ranked[0]["predictions"]
                selected_candidate_index = next(i for i, item in enumerate(candidates)
                                                 if item[0] == selected[0])
            elif policy == "fixed_first":
                selected = remaining[0]
                env = euler.describe(selected[1])
                predicted = [terms[i].evaluate(env, substrate) for i in alive]
                prediction_evaluations += len(alive)
            else:
                # Consume one preregistered random permutation without replacement.
                selected = next(item for item in random_order if item in remaining)
                env = euler.describe(selected[1])
                predicted = [terms[i].evaluate(env, substrate) for i in alive]
                prediction_evaluations += len(alive)
            decision_compute_wall_s += time.perf_counter() - decision_started
            decision_compute_cpu_s += time.process_time() - decision_cpu_started
            label, oracle_wall, oracle_cpu = timed_oracle(oracle, selected[1])
            responses.append({"query": selected[0], "input": selected[1], "label": label,
                              "oracle_wall_s": oracle_wall, "oracle_cpu_s": oracle_cpu})
            if policy == "entropy_cached":
                alive = cache_index.filter(alive, selected_candidate_index, label)
            else:
                alive = [i for i, prediction in zip(alive, predicted) if equal(prediction, label)]
            remaining = [item for item in remaining if item[0] != selected[0]]
        runs.append({
            "policy": policy, "replicate": replicate,
            "random_seed": (SEED + anchor_index * 100 + replicate) if policy == "seeded_random" else None,
            "oracle_responses": responses,
            "final_survivor_ids": alive,
            "oracle_calls": len(responses),
            "prediction_evaluations": prediction_evaluations,
            "selection_wall_s": selection_wall_s,
            "selection_cpu_s": selection_cpu_s,
            "decision_compute_wall_s": decision_compute_wall_s,
            "decision_compute_cpu_s": decision_compute_cpu_s,
            "oracle_wall_s": sum(row["oracle_wall_s"] for row in responses),
            "oracle_cpu_s": sum(row["oracle_cpu_s"] for row in responses),
            "cache_build_wall_s": cache_build_wall_s if policy == "entropy_cached" else None,
            "cache_build_cpu_s": cache_build_cpu_s if policy == "entropy_cached" else None,
            "cache_retained_heap_bytes": cache_retained_heap_bytes if policy == "entropy_cached" else None,
            "matrix_cells_read": matrix_cells_read,
            "decision_plus_oracle_and_cache_wall_s": (
                decision_compute_wall_s + sum(row["oracle_wall_s"] for row in responses) +
                (cache_build_wall_s if policy == "entropy_cached" else 0.0)),
        })

    # Heldout labels are calculated after all policy decisions and are not
    # passed to generation, ranking, filtering, or stopping.
    heldout_oracle = euler._make_labeller(substrate)
    heldout_labels = [{"name": name, "label": heldout_oracle(faces)} for name, faces in HELDOUT]
    for run in runs:
        final_ids = run["final_survivor_ids"]
        accuracies = []
        for i in final_ids:
            accuracies.append(sum(equal(terms[i].evaluate(euler.describe(faces), substrate), row["label"])
                                  for (name, faces), row in zip(HELDOUT, heldout_labels)) / len(HELDOUT))
        run["survivor_heldout_accuracies"] = accuracies
        run["unique_heldout_correct"] = len(final_ids) == 1 and accuracies == [1.0]
    true_behaviors = [
        i for i, term in enumerate(terms)
        if all(equal(term.evaluate(euler.describe(faces), substrate), row["label"])
               for (name, faces), row in zip(HELDOUT, heldout_labels))
    ]
    return {
        "anchor_index": anchor_index, "anchor": anchor_name,
        "generation": generation,
        "hypothesis_ids": [item["term_str"] for item in hypotheses],
        "heldout_labels": heldout_labels,
        "heldout_correct_hypothesis_ids": true_behaviors,
        "pool_contains_heldout_correct": bool(true_behaviors),
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    lock = build_lock()
    if args.lock:
        print(json.dumps(lock, indent=2, sort_keys=True))
        return
    if not LOCK.exists() or json.loads(LOCK.read_text()) != lock:
        raise SystemExit(f"missing or stale source lock: {LOCK}")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite existing raw capture: {RAW}")
    substrate = _native.Substrate()
    started = time.perf_counter()
    anchors = [run_anchor(i, name, faces, substrate)
               for i, (name, faces) in enumerate(ANCHORS)]
    raw = {
        "protocol": STEM, "lock": lock, "anchors": anchors,
        "elapsed_s": time.perf_counter() - started,
        "environment": {"python": sys.version, "platform": platform.platform()},
        "worker_failures": [],
    }
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"raw": str(RAW), "anchors": len(anchors),
                      "elapsed_s": raw["elapsed_s"],
                      "pools": [a["generation"]["pool_size"] for a in anchors],
                      "halt_reasons": [a["generation"]["halt_reason"] for a in anchors]}, sort_keys=True))


if __name__ == "__main__":
    main()
