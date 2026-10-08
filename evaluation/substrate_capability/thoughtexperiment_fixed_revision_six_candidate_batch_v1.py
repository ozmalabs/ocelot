#!/usr/bin/env python3
"""Compare one-baseline six-candidate batches with standalone rehearsals."""
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
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from domains.self_correction import (  # noqa: E402
    _default_candidates,
    imagine_candidate_batch,
    imagine_and_check_convergence,
)
from evaluation.substrate_capability import thoughtexperiment_self_correction_copy_comparison_v1 as controls  # noqa: E402

LOCKED_SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_fixed_revision_six_candidate_batch_v1.py",
    "domains/self_correction.py",
    "domains/edit_ops.py",
    "domains/collapse_model.py",
    "domains/imagination.py",
    "domains/reflective_faculty.py",
    "substrate/boot_core.py",
    "seeds/shape_decode_loop.json",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/cow_paged_vec.rs",
    "runners/dsl/src/cow_sharded_map.rs",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
)
SCOPED_BACKEND = "native_full_copy_scoped"


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def graph_and_rule_digest(native) -> tuple[str, str]:
    graph = json.dumps(native.graph_to_dict(), sort_keys=True,
                       separators=(",", ":"), default=str)
    rules = json.dumps(native.export_rules(), sort_keys=True,
                       separators=(",", ":"), default=str)
    return (hashlib.sha256(graph.encode()).hexdigest(),
            hashlib.sha256(rules.encode()).hexdigest())


def result_row(result: dict, label: str) -> dict:
    before = result["model_before"]
    after = result["model_after"]
    return {
        "candidate_label": label,
        "converges": bool(result["converges"]),
        "inert": bool(result["inert"]),
        "applied_target_rules": sorted(result["applied"]),
        "residual_before": float(before.residual),
        "residual_after": float(after.residual),
        "frontier_growth_before": float(before.frontier_growth_rate),
        "frontier_growth_after": float(after.frontier_growth_rate),
        "steps_run": after.imagine_steps_run,
        "conclusions": result["imagined"].conclusions,
        "derived_only": result["imagined"].derived_only,
        "forward_look_deltas_before": before.forward_look_deltas,
        "forward_look_deltas_after": after.forward_look_deltas,
    }


def make_trial(size: int):
    sub, native, _correct, _wrong, observations = controls.make_fixture(size)
    candidates = _default_candidates(native, "sd_mint_quantum")
    return sub, native, observations, candidates


def run_batch(size: int, snapshot_backend: str = SCOPED_BACKEND) -> dict:
    sub, native, observations, candidates = make_trial(size)
    labels = [candidate["label"] for candidate in candidates]
    before = graph_and_rule_digest(native)
    started = time.perf_counter_ns()
    batch = imagine_candidate_batch(
        sub, candidates, horizon=3, frontier_sample=50, focus_hops=1,
        imagine_steps=2, snapshot_backend=snapshot_backend,
        experiment_focus_nodes=observations, _measure_phases=True, record_trace=False)
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    after = graph_and_rule_digest(native)
    rows = [result_row(result, label)
            for result, label in zip(batch["results"], labels)]
    return {
        "elapsed_ms": elapsed_ms,
        "candidate_labels": labels,
        "candidate_count": len(labels),
        "rows": rows,
        "one_baseline_shared": True,
        "timing_components_ms": batch["timing_components_ms"],
        "candidate_phase_timings_ms": [result["phase_timings_ms"] for result in batch["results"]],
        "baseline_prediction_phases_ms": batch["model_before"].phase_timings_ms,
        "candidate_prediction_phases_ms": [result["model_after"].phase_timings_ms
                                            for result in batch["results"]],
        "primary_graph_and_rules_unchanged": before == after,
        "batch_primary_guard": batch["primary_graph_and_rules_unchanged_during_batch"],
    }


def run_standalone(size: int, snapshot_backend: str = SCOPED_BACKEND) -> dict:
    sub, native, observations, candidates = make_trial(size)
    labels = [candidate["label"] for candidate in candidates]
    before = graph_and_rule_digest(native)
    started = time.perf_counter_ns()
    rows = []
    phase_timings = []
    prediction_phase_timings = []
    baseline_prediction_phases = []
    for candidate in candidates:
        result = imagine_and_check_convergence(
            sub, candidate, horizon=3, frontier_sample=50, focus_hops=1,
            imagine_steps=2, experiment_focus_nodes=observations,
            snapshot_backend=snapshot_backend, _measure_phases=True, record_trace=False)
        rows.append(result_row(result, candidate["label"]))
        phase_timings.append(result["phase_timings_ms"])
        prediction_phase_timings.append(result["model_after"].phase_timings_ms)
        baseline_prediction_phases.append(result["model_before"].phase_timings_ms)
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    after = graph_and_rule_digest(native)
    return {
        "elapsed_ms": elapsed_ms,
        "candidate_labels": labels,
        "candidate_count": len(labels),
        "rows": rows,
        "candidate_phase_timings_ms": phase_timings,
        "candidate_prediction_phases_ms": prediction_phase_timings,
        "baseline_prediction_phases_ms": baseline_prediction_phases,
        "one_baseline_shared": False,
        "primary_graph_and_rules_unchanged": before == after,
    }


def signature(rows: list[dict]) -> str:
    return json.dumps(rows, sort_keys=True, separators=(",", ":"))


def validate_trial(batch: dict, standalone: dict) -> None:
    if batch["candidate_labels"] != standalone["candidate_labels"]:
        raise RuntimeError("candidate order changed between batch and standalone arms")
    if signature(batch["rows"]) != signature(standalone["rows"]):
        raise RuntimeError("batch and standalone nested residuals/outcomes diverged")
    if not (batch["primary_graph_and_rules_unchanged"]
            and batch["batch_primary_guard"]
            and standalone["primary_graph_and_rules_unchanged"]):
        raise RuntimeError("primary graph or rules changed during fixed-revision experiment")
    if batch["candidate_count"] != 6:
        raise RuntimeError(f"expected six candidates, found {batch['candidate_count']}")
    if not next(r for r in batch["rows"] if r["candidate_label"] == "dedup_identity_fix")["converges"]:
        raise RuntimeError("positive candidate did not converge")
    if next(r for r in batch["rows"] if r["candidate_label"] == "add_match_guard(control)")["converges"]:
        raise RuntimeError("negative guard control converged")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 1000, 10000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--snapshot-backends", nargs="+",
                        choices=["native_full_copy_scoped", "native_shared_slab_scoped",
                                 "native_shared_graph_pages_scoped",
                                 "native_reusable_snapshot"],
                        default=[SCOPED_BACKEND])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or any(size < 0 for size in args.sizes):
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine; rebuild before measuring: {stale}")

    rng = random.Random(args.seed)
    comparisons, schedule = [], []
    cross_backend_checked = len(args.snapshot_backends) > 1
    for size in args.sizes:
        trials = {backend: {"one_baseline_six_candidate_batch": [],
                            "baseline_recomputed_per_candidate": []}
                  for backend in args.snapshot_backends}
        for iteration in range(args.warmups + args.repeats):
            jobs = [(backend, mode) for backend in args.snapshot_backends
                    for mode in ("one_baseline_six_candidate_batch",
                                 "baseline_recomputed_per_candidate")]
            rng.shuffle(jobs)
            pair = {backend: {} for backend in args.snapshot_backends}
            for backend, mode in jobs:
                pair[backend][mode] = (
                    run_batch(size, backend) if mode == "one_baseline_six_candidate_batch"
                    else run_standalone(size, backend))
                schedule.append({"size": size, "iteration": iteration,
                                 "snapshot_backend": backend, "mode": mode})
            for backend in args.snapshot_backends:
                validate_trial(pair[backend]["one_baseline_six_candidate_batch"],
                               pair[backend]["baseline_recomputed_per_candidate"])
            if len(args.snapshot_backends) > 1:
                reference_backend = args.snapshot_backends[0]
                reference_rows = pair[reference_backend]["one_baseline_six_candidate_batch"]["rows"]
                for backend in args.snapshot_backends[1:]:
                    candidate_rows = pair[backend]["one_baseline_six_candidate_batch"]["rows"]
                    if signature(reference_rows) != signature(candidate_rows):
                        raise RuntimeError(
                            f"backend result parity failed: {reference_backend} vs {backend}")
            if iteration >= args.warmups:
                for backend in args.snapshot_backends:
                    for mode in trials[backend]:
                        trials[backend][mode].append(pair[backend][mode])
        for backend in args.snapshot_backends:
            backend_trials = trials[backend]
            batch_rows = backend_trials["one_baseline_six_candidate_batch"]
            standalone_rows = backend_trials["baseline_recomputed_per_candidate"]
            batch_ms = statistics.median(row["elapsed_ms"] for row in batch_rows)
            standalone_ms = statistics.median(row["elapsed_ms"] for row in standalone_rows)
            useful_counts = [sum(row["converges"] and not row["inert"] for row in trial["rows"])
                             for trial in batch_rows]
            baseline_prediction_median = statistics.median(
                trial["timing_components_ms"]["baseline_prediction"] for trial in batch_rows)
            candidate_rehearsal_medians = [statistics.median(
                trial["timing_components_ms"]["candidate_rehearsals"][index]
                for trial in batch_rows) for index in range(batch_rows[0]["candidate_count"])]
            comparisons.append({
                "size": size,
                "snapshot_backend": backend,
                "candidate_count": batch_rows[0]["candidate_count"],
                "candidate_labels": batch_rows[0]["candidate_labels"],
                "repeats": args.repeats,
                "warmups": args.warmups,
                "exact_nested_residual_and_outcome_parity": True,
                "cross_backend_exact_output_parity": cross_backend_checked,
                "primary_graph_and_rules_preserved": True,
                "useful_candidates_per_batch": useful_counts,
                "batch_baseline_prediction_median_ms": baseline_prediction_median,
                "batch_candidate_rehearsal_medians_ms": candidate_rehearsal_medians,
                "batch_median_ms": batch_ms,
                "standalone_median_ms": standalone_ms,
                "speedup": standalone_ms / batch_ms,
                "batch_trials": batch_rows,
                "standalone_trials": standalone_rows,
            })

    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentFixedRevisionSixCandidateBatchV1",
        "implementation_status": "one shared baseline; six isolated scoped native branches; mutation-journal readout; primary traces disabled during measured batch",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "runner": {"path": str(Path(__file__).resolve()),
                   "sha256": sha256(Path(__file__).resolve())},
        "binary": {"path": str(binary), "sha256": sha256(binary)},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sources": {name: sha256(ROOT / name) for name in LOCKED_SOURCES},
        "protocol": {
            "candidate_generation": "all variants from _default_candidates(sd_mint_quantum), expected six",
            "branch_backends": args.snapshot_backends,
            "residual_readout": "Rust sparse mutation journal",
            "batch_primary_revision": "record_trace=False; all six branches start from unchanged primary; before/after graph and rule digests checked",
            "standalone_control": "same candidate list and backend, independently recomputes baseline for each candidate, trace writes disabled",
            "timed_region": "batch includes baseline once and all candidate branch/prediction/residual work; standalone includes baseline per candidate; fixture setup excluded",
            "semantic_gate": "exact candidate order, applied rule, outputs, conclusions, derived_only, nested forward-look residuals, convergence and primary-state parity",
            "cross_backend_gate": "when multiple backends are selected, canonical batch result rows are compared exactly after each matched randomized block; disagreement aborts capture",
            "order_seed": args.seed,
        },
        "comparisons": comparisons,
        "schedule": schedule,
    }
    rendered = json.dumps(capture, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
