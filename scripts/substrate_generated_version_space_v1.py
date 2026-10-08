#!/usr/bin/env python3
"""Source-locked generated-version-space query selection pilot."""
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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]

from domains.engine_provenance import engine_preamble, engine_provenance, rust_source_fingerprint
engine_preamble()
from domains.generator import synthesize
from domains.query_selection import rank_queries_by_disagreement
from substrate_rs import _native
import cegis_faculty_on_sum_of_n as triangular

STEM = "substrate_generated_version_space_v1_20260930"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_VERSION_SPACE_V1_PREREG_20260930.md"
SOURCE_PATHS = (
    "domains/generator.py",
    "domains/query_selection.py",
    "domains/engine_provenance.py",
    "scripts/cegis_faculty_on_sum_of_n.py",
    "scripts/substrate_generated_version_space_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_VERSION_SPACE_V1_PREREG_20260930.md",
)
ANCHORS = (6, 7, 8, 9, 10)
RANDOM_REPS = 10
SEED = 20260930
HELDOUT = tuple(range(13, 21))


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build_lock() -> dict:
    native_path = Path(_native.__file__).resolve()
    return {
        "schema_version": 1,
        "sources": {name: sha256_file(ROOT / name) for name in SOURCE_PATHS},
        "native_extension": {"path": str(native_path), "sha256": sha256_file(native_path)},
        "native_build_manifest_sha256": sha256_file(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "engine_provenance": engine_provenance(),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {
            "anchors": list(ANCHORS), "heldout": list(HELDOUT),
            "random_reps": RANDOM_REPS, "seed": SEED,
            "candidate_family": "triangular.family() excluding training anchor",
            "ops": ["Plus", "Times", "Minus", "Div"],
            "consts": [0, 1, 2, -1], "max_size": 7, "timeout_s": 10,
            "max_solutions": 10000, "include_output_constants": False,
            "policies": ["fixed_first", "seeded_random", "entropy_ranked", "oracle_best"],
        },
    }


def numeric_equal(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) <= 1e-9
    except (TypeError, ValueError):
        return a == b


def run_anchor(anchor: int, substrate) -> dict:
    describe = triangular.describe
    oracle = triangular.make_oracle(substrate)
    candidates = [(name, value) for name, value in triangular.family() if value != anchor]
    examples = [(describe(anchor), oracle(anchor))]
    started = time.perf_counter()
    cpu_started = time.process_time()
    result = synthesize(
        substrate, examples, ops=("Plus", "Times", "Minus", "Div"),
        consts=(0, 1, 2, -1), max_size=7, timeout_s=10.0, saturate_k=5,
        probe_envs=[describe(value) for _, value in candidates],
        max_solutions=10000, include_output_constants=False,
    )
    generation = {
        "anchor": anchor, "pool_size": len(result.get("hypotheses", [])),
        "halt_reason": result["halt_reason"], "fits": result["fits"],
        "bounded_pool_complete": result["halt_reason"] == "max_size",
        "explored": result["explored"], "distinct": result["distinct"],
        "elapsed_s": result["elapsed_s"],
        "wall_s": time.perf_counter() - started,
        "cpu_s": time.process_time() - cpu_started,
        "candidate_names": [name for name, _ in candidates],
    }
    hypotheses = result.get("hypotheses", [])
    terms = [item["term"] for item in hypotheses]
    ranked = rank_queries_by_disagreement(substrate, terms, describe, candidates) if terms else []
    rank_by_name = {row["name"]: row for row in ranked}

    def eval_pool(value):
        env = describe(value)
        return [term.evaluate(env, substrate) for term in terms]

    holdout_labels = {n: oracle(n) for n in HELDOUT}
    truth_behaviors = [
        i for i in range(len(terms))
        if all(numeric_equal(terms[i].evaluate(describe(n), substrate), label)
               for n, label in holdout_labels.items())
    ]

    policies = []
    for policy in ("fixed_first", "entropy_ranked"):
        if policy == "fixed_first":
            selected = candidates[0][0]
        else:
            selected = ranked[0]["name"] if ranked else candidates[0][0]
        policies.append((policy, 0, selected))
    for rep in range(1, RANDOM_REPS + 1):
        rng = random.Random(SEED + anchor * 100 + rep)
        policies.append(("seeded_random", rep, rng.choice(candidates)[0]))

    oracle_best_rows = []
    oracle_best_labels = {}
    if hypotheses:
        best = None
        for ordinal, (query_name, value) in enumerate(candidates):
            label = oracle(value)
            oracle_best_labels[query_name] = label
            predictions = eval_pool(value)
            survivors = [i for i, prediction in enumerate(predictions) if numeric_equal(prediction, label)]
            oracle_best_rows.append({"query": query_name, "oracle_response": label,
                                     "survivor_count": len(survivors)})
            key = (len(survivors), ordinal)
            if best is None or key < best[0]:
                best = (key, query_name)
        policies.append(("oracle_best", 0, best[1]))

    evaluated = []
    for policy, rep, query_name in policies:
        value = next(value for name, value in candidates if name == query_name)
        label = oracle_best_labels[query_name] if policy == "oracle_best" else oracle(value)
        predictions = eval_pool(value)
        survivors = [i for i, prediction in enumerate(predictions) if numeric_equal(prediction, label)]
        correct_survivors = [i for i in survivors if i in truth_behaviors]
        heldout_accuracy = []
        for i in survivors:
            heldout_accuracy.append(sum(
                numeric_equal(terms[i].evaluate(describe(n), substrate), expected)
                for n, expected in holdout_labels.items()
            ) / len(holdout_labels))
        evaluated.append({
            "policy": policy, "replicate": rep,
            "selected_query": query_name, "oracle_responses": [{"input": value, "label": label}],
            "survivor_count": len(survivors),
            "correct_survivor_count": len(correct_survivors),
            "unique_correct_identification": len(survivors) == 1 and survivors == truth_behaviors,
            "pool_contains_heldout_correct": bool(truth_behaviors),
            "mean_survivor_heldout_accuracy": sum(heldout_accuracy) / len(heldout_accuracy) if heldout_accuracy else None,
            "oracle_calls": len(candidates) if policy == "oracle_best" else 1,
            "entropy_bits": rank_by_name.get(query_name, {}).get("entropy_bits"),
        })
    return {"anchor": anchor, "generation": generation,
            "generated_hypothesis_ids": [h["term_str"] for h in hypotheses],
            "heldout_correct_hypothesis_count": len(truth_behaviors),
            "entropy_ranking": [{"query": r["name"], "entropy_bits": r["entropy_bits"]} for r in ranked],
            "oracle_best_diagnostic": oracle_best_rows, "policies": evaluated}


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
        raise SystemExit(f"refusing to overwrite existing capture: {RAW}")
    substrate = _native.Substrate()
    started = time.perf_counter()
    anchors = [run_anchor(anchor, substrate) for anchor in ANCHORS]
    raw = {
        "protocol": STEM, "lock": lock, "anchors": anchors,
        "worker_failures": [], "elapsed_s": time.perf_counter() - started,
        "environment": {"python": sys.version, "platform": platform.platform()},
    }
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"raw": str(RAW), "anchors": len(anchors),
                      "elapsed_s": raw["elapsed_s"],
                      "pool_sizes": [a["generation"]["pool_size"] for a in anchors],
                      "halt_reasons": [a["generation"]["halt_reason"] for a in anchors]}, sort_keys=True))


if __name__ == "__main__":
    main()
