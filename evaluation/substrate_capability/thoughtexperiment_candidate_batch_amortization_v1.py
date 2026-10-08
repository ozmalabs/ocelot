#!/usr/bin/env python3
"""Measure fixed-revision candidate batching with one cached baseline.

Compares the new batch API (one baseline prediction reused across candidates,
no primary experiment traces) with repeated standalone rehearsals (each does
its own baseline). Fixture construction is excluded; the batch API's primary
state digest checks are included in its elapsed time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(EVAL_DIR)]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from domains.self_correction import (  # noqa: E402
    _default_candidates,
    imagine_candidate_batch,
    imagine_and_check_convergence,
)
import thoughtexperiment_self_correction_copy_comparison_v1 as controls  # noqa: E402

LOCKED_SOURCES = (
    "domains/self_correction.py",
    "domains/collapse_model.py",
    "domains/imagination.py",
    "domains/reflective_faculty.py",
    "substrate/boot_core.py",
    "seeds/shape_decode_loop.json",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_applied(applied: dict) -> dict:
    import re
    return {k: re.sub(r"_(?:scfix|scguard)_[0-9a-f]{8}$", "", v)
            if isinstance(v, str) else v for k, v in applied.items()}


def result_signature(result: dict) -> tuple:
    before, after = result["model_before"], result["model_after"]
    return (
        bool(result["converges"]), bool(result["inert"]),
        json.dumps(normalize_applied(result["applied"]), sort_keys=True),
        before.converged, before.residual, before.frontier_growth_rate,
        after.converged, after.residual, after.frontier_growth_rate,
        after.imagine_steps_run, result["imagined"].n_conclusions,
    )


def one_trial(size: int, mode: str) -> dict:
    substrate, native, _correct, _wrong = controls.make_fixture(size)
    candidates = _default_candidates(native, "sd_mint_quantum")
    if len(candidates) != 2 or [c["label"] for c in candidates] != [
            "dedup_identity_fix", "add_match_guard(control)"]:
        raise RuntimeError(f"locked fixture candidate panel changed: {[c['label'] for c in candidates]}")

    naive_inputs = []
    if mode == "baseline_per_candidate":
        # Each ordinary rehearsal mutates its primary with durable traces.
        # Give each candidate an independent fresh revision, matching the
        # fixed-primary semantics of the batch arm.
        for candidate in candidates:
            trial_sub, trial_native, _c, _w = controls.make_fixture(size)
            trial_candidates = _default_candidates(trial_native, "sd_mint_quantum")
            match = next(c for c in trial_candidates if c["label"] == candidate["label"])
            naive_inputs.append((trial_sub, match))

    started = time.perf_counter_ns()
    if mode == "cached_baseline_batch":
        batch = imagine_candidate_batch(
            substrate, candidates, snapshot_backend="native_full_copy")
        rows = batch["results"]
        primary_unchanged = batch["primary_graph_and_rules_unchanged_during_batch"]
    elif mode == "baseline_per_candidate":
        rows = [imagine_and_check_convergence(
            trial_sub, candidate, snapshot_backend="native_full_copy")
            for trial_sub, candidate in naive_inputs]
        primary_unchanged = None
    else:
        raise ValueError(mode)
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    return {
        "elapsed_ms": elapsed_ms,
        "candidate_labels": [c["label"] for c in candidates],
        "signatures": [result_signature(row) for row in rows],
        "outcomes": [{
            "label": row["candidate"]["label"],
            "converges": bool(row["converges"]),
            "inert": bool(row["inert"]),
            "applied": normalize_applied(row["applied"]),
            "model_before": {
                "converged": row["model_before"].converged,
                "residual": row["model_before"].residual,
                "frontier_growth_rate": row["model_before"].frontier_growth_rate,
            },
            "model_after": {
                "converged": row["model_after"].converged,
                "residual": row["model_after"].residual,
                "frontier_growth_rate": row["model_after"].frontier_growth_rate,
            },
        } for row in rows],
        "primary_graph_and_rules_unchanged": primary_unchanged,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 1000, 10000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--order-seed", type=int, default=20260930)
    parser.add_argument("--out", type=Path, default=ROOT /
                        "evaluation/reports/thoughtexperiment_candidate_batch_amortization_v1.json")
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or any(n < 0 for n in args.sizes):
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine; rebuild before measuring: {stale}")

    rng = random.Random(args.order_seed)
    raw: dict[tuple[int, str], list[dict]] = {}
    order = []
    for size in args.sizes:
        for mode in ("cached_baseline_batch", "baseline_per_candidate"):
            for _ in range(args.warmups):
                one_trial(size, mode)
        raw[(size, "cached_baseline_batch")] = []
        raw[(size, "baseline_per_candidate")] = []
        for repeat in range(args.repeats):
            block = ["cached_baseline_batch", "baseline_per_candidate"]
            rng.shuffle(block)
            for mode in block:
                row = one_trial(size, mode)
                row["repeat"] = repeat
                raw[(size, mode)].append(row)
                order.append({"size": size, "repeat": repeat, "mode": mode})

    comparisons = []
    for size in args.sizes:
        batch_rows = raw[(size, "cached_baseline_batch")]
        naive_rows = raw[(size, "baseline_per_candidate")]
        parity = all(row["signatures"] == base["signatures"]
                     for row, base in zip(batch_rows, naive_rows))
        unchanged = all(row["primary_graph_and_rules_unchanged"] is True
                        for row in batch_rows)
        expected = all(
            [row["outcomes"][0]["converges"] is True and
             row["outcomes"][1]["converges"] is False for row in batch_rows + naive_rows])
        if not (parity and unchanged and expected):
            raise SystemExit(f"batch parity/isolation gate failed at size={size}")
        batch_ms = [r["elapsed_ms"] for r in batch_rows]
        naive_ms = [r["elapsed_ms"] for r in naive_rows]
        batch_median = statistics.median(batch_ms)
        naive_median = statistics.median(naive_ms)
        comparisons.append({
            "size": size,
            "candidate_count": 2,
            "repeats": args.repeats,
            "exact_prediction_and_residual_parity": parity,
            "primary_graph_and_rule_isolation": unchanged,
            "expected_positive_negative_controls": expected,
            "batch_median_ms": batch_median,
            "baseline_per_candidate_median_ms": naive_median,
            "speedup": naive_median / batch_median,
            "raw_batch_trials": batch_rows,
            "raw_baseline_per_candidate_trials": naive_rows,
        })

    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentCandidateBatchAmortizationV1",
        "implementation_status": "baseline_reused_across_fixed_revision_batch; native_full_copy branch backend",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "runner": {"path": str(Path(__file__).resolve()),
                   "sha256": sha256_file(Path(__file__).resolve())},
        "binary": {"path": str(binary), "sha256": sha256_file(binary)},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sources": {name: sha256_file(ROOT / name) for name in LOCKED_SOURCES},
        "protocol": {
            "candidate_panel": ["dedup_identity_fix", "add_match_guard(control)"],
            "branch_backend": "native_full_copy",
            "fixture_construction": "excluded from timers; each mode/repeat receives a fresh fixture",
            "cached_baseline": "computed once per batch and passed to both candidate rehearsals",
            "primary_isolation": "batch mode records one baseline, suppresses per-candidate traces, then hashes graph plus native rules before/after candidate branches",
            "order": "seeded randomized complete block per repeat and graph size",
            "cost_boundary": "includes baseline and branch execution, residual extraction, batch isolation digests; excludes fixture construction",
            "limits": ["two candidates only", "one synthetic self-correction family", "one host",
                       "native deep-copy branch remains O(state)",
                       "does not establish CoW or open-ended candidate-search throughput"],
        },
        "order_seed": args.order_seed,
        "comparison_order": order,
        "comparisons": comparisons,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(capture, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "results": [
        {"size": r["size"], "batch_ms": r["batch_median_ms"],
         "per_candidate_baseline_ms": r["baseline_per_candidate_median_ms"],
         "speedup": r["speedup"]} for r in comparisons]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
