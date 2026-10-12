#!/usr/bin/env python3
"""Measure cached-baseline process-CoW candidate batches on fixed revisions."""
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
EVAL = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(EVAL)]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from domains.collapse_model import predict_collapse  # noqa: E402
import thoughtexperiment_process_cow_self_correction_v1 as process  # noqa: E402
import thoughtexperiment_self_correction_copy_comparison_v1 as controls  # noqa: E402

SOURCES = (
    "domains/self_correction.py", "domains/imagination.py",
    "domains/collapse_model.py", "domains/reflective_faculty.py",
    "substrate/boot_core.py", "seeds/shape_decode_loop.json",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "evaluation/substrate_capability/thoughtexperiment_process_cow_self_correction_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def outcome_signature(row: dict) -> str:
    import re
    applied = {
        name: re.sub(r"_(?:scfix|scguard)_[0-9a-f]{8}$", "", value)
        if isinstance(value, str) else value
        for name, value in row["applied"].items()
    }
    return json.dumps({
        "converges": row["converges"], "inert": row["inert"],
        "applied": applied, "residual_before": row["residual_before"],
        "residual_after": row["residual_after"],
        "frontier_growth_before": row["frontier_growth_before"],
        "frontier_growth_after": row["frontier_growth_after"],
        "steps_run": row["steps_run"], "n_conclusions": row["n_conclusions"],
        "residual": row["residual"],
    }, sort_keys=True, separators=(",", ":"))


def baseline(substrate):
    return predict_collapse(substrate, horizon=3, imagine_steps=2,
                            snapshot_backend="native_full_copy")


def run_batch(size: int, *, scoped: bool) -> dict:
    substrate, native, correct, wrong, observations = controls.make_fixture(size)
    candidates = [correct, wrong]
    labels = [candidate["label"] for candidate in candidates]
    if labels != ["dedup_identity_fix", "add_match_guard(control)"]:
        raise RuntimeError(f"locked candidate panel changed: {labels}")
    start = time.perf_counter_ns()
    model_before = baseline(substrate)
    before = process.canonical_digest(native.graph_to_dict())
    rules_before = process.canonical_digest(native.export_rules())
    branch_rows = [process.process_cow_candidate(
        substrate, candidate, model_before,
        horizon=3, frontier_sample=50, focus_hops=1, imagine_steps=2,
        observations=observations, scoped=scoped, persist_receipt=False)
        for candidate in candidates]
    for candidate, row in zip(candidates, branch_rows):
        row["candidate_label"] = candidate["label"]
    branch_revision_unchanged = (
        process.canonical_digest(native.graph_to_dict()) == before
        and process.canonical_digest(native.export_rules()) == rules_before)
    if not branch_revision_unchanged:
        raise RuntimeError("candidate branches or receipts mutated the fixed primary revision")
    for candidate, row in zip(candidates, branch_rows):
        row["receipt_node_id"] = process.persist_process_receipt(
            substrate, candidate, row, probe="self_correction_shape_decode_fixture_v1")
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    return {"elapsed_ms": elapsed_ms, "branch_rows": branch_rows,
            "branch_revision_unchanged_until_receipts": branch_revision_unchanged,
            "receipt_count": len(candidates), "candidate_labels": labels,
            "baseline_converged": model_before.converged}


def run_standalone(size: int, candidate_labels: list[str], *, scoped: bool) -> dict:
    rows = []
    elapsed_total = 0.0
    for label in candidate_labels:
        substrate, native, _correct, _wrong, observations = controls.make_fixture(size)
        candidate = next((c for c in controls._default_candidates(native, "sd_mint_quantum")
                          if c["label"] == label), None)
        if candidate is None:
            raise RuntimeError(f"standalone fixture lacks candidate {label}")
        started = time.perf_counter_ns()
        model_before = baseline(substrate)
        row = process.process_cow_candidate(
            substrate, candidate, model_before,
            horizon=3, frontier_sample=50, focus_hops=1, imagine_steps=2,
            observations=observations, scoped=scoped, persist_receipt=True)
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        elapsed_total += elapsed_ms
        rows.append({"candidate_label": label, **row})
    return {"elapsed_ms": elapsed_total, "branch_rows": rows,
            "branch_revision_unchanged_until_receipts": all(
                row["parent_graph_and_rules_unchanged_before_receipt"] for row in rows),
            "receipt_count": len(rows)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 1000, 10000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--order-seed", type=int, default=20260930)
    parser.add_argument("--unscoped", action="store_true",
                        help="use physical-prune process children instead of sparse scoped reads")
    parser.add_argument("--out", type=Path, default=ROOT /
                        "evaluation/reports/thoughtexperiment_process_batch_amortization_v1.json")
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or min(args.sizes) < 0:
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")
    if not sys.platform.startswith("linux"):
        raise SystemExit("requires Linux process CoW")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine: {stale}")

    scoped = not args.unscoped
    rng = random.Random(args.order_seed)
    comparisons, schedule = [], []
    for size in args.sizes:
        _sub, _panel_native, panel_correct, panel_wrong, _obs = controls.make_fixture(size)
        panel_labels = [panel_correct["label"], panel_wrong["label"]]
        for _ in range(args.warmups):
            warm_batch = run_batch(size, scoped=scoped)
            if warm_batch["candidate_labels"] != panel_labels:
                raise RuntimeError("candidate panel changed during warmup")
            run_standalone(size, warm_batch["candidate_labels"], scoped=scoped)
        rows = {"cached_baseline_batch": [], "baseline_per_candidate": []}
        for repeat in range(args.repeats):
            order = list(rows)
            rng.shuffle(order)
            for mode in order:
                if mode == "cached_baseline_batch":
                    row = run_batch(size, scoped=scoped)
                    if row["candidate_labels"] != panel_labels:
                        raise RuntimeError("candidate panel changed within comparison block")
                else:
                    row = run_standalone(size, panel_labels, scoped=scoped)
                row["repeat"] = repeat
                rows[mode].append(row)
                schedule.append({"size": size, "repeat": repeat, "mode": mode})
        batch, standalone = rows["cached_baseline_batch"], rows["baseline_per_candidate"]
        parity = all(
            len(a["branch_rows"]) == len(b["branch_rows"]) == len(a["candidate_labels"])
            and all(outcome_signature(x) == outcome_signature(y)
                    for x, y in zip(a["branch_rows"], b["branch_rows"]))
            for a, b in zip(batch, standalone))
        isolation = all(a["branch_revision_unchanged_until_receipts"]
                        for a in batch + standalone)
        expected = all(
            batch_row["branch_rows"][0]["converges"] is True
            and standalone_row["branch_rows"][0]["converges"] is True
            and batch_row["branch_rows"][1]["converges"] is False
            and standalone_row["branch_rows"][1]["converges"] is False
            for batch_row, standalone_row in zip(batch, standalone))
        if not (parity and isolation and expected):
            raise SystemExit(f"batch parity/isolation failed at size={size}: "
                             f"parity={parity} isolation={isolation} expected={expected}")
        batch_ms = statistics.median(r["elapsed_ms"] for r in batch)
        standalone_ms = statistics.median(r["elapsed_ms"] for r in standalone)
        comparisons.append({"size": size, "candidate_count": len(batch[0]["branch_rows"]),
                            "candidate_labels": batch[0]["candidate_labels"],
                            "exact_prediction_and_residual_parity": parity,
                            "fixed_primary_until_receipts": isolation,
                            "positive_negative_control_outcomes": expected,
                            "batch_median_ms": batch_ms,
                            "standalone_sum_median_ms": standalone_ms,
                            "speedup": standalone_ms / batch_ms,
                            "batch_trials": batch,
                            "standalone_trials": standalone})

    native_path = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentProcessBatchAmortizationV1",
        "implementation_status": "sequential Linux CoW branches from one fixed primary; baseline reused; receipts deferred until all branches finish",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "runner": {"path": str(Path(__file__).resolve()),
                   "sha256": sha(Path(__file__).resolve())},
        "binary": {"path": str(native_path), "sha256": sha(native_path)},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sources": {name: sha(ROOT / name) for name in SOURCES},
        "protocol": {"candidate_panel": ["dedup_identity_fix", "add_match_guard(control)"],
                    "branch_backend": "process_in_place_scoped" if scoped else "process_in_place",
                    "timed_region": "batch includes one baseline, all fork/digest/residual work, deferred receipts; standalone sums both candidate rehearsals; fixture setup excluded",
                    "fixed_revision": "batch waits to write any ThoughtexperimentReceipt until both branch forks have passed graph/rule digest checks",
                    "order": "seeded randomized paired complete blocks per size"},
        "order_seed": args.order_seed,
        "comparison_order": schedule,
        "comparisons": comparisons,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(capture, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "results": [
        {"size": r["size"], "batch_ms": round(r["batch_median_ms"], 1),
         "standalone_sum_ms": round(r["standalone_sum_median_ms"], 1),
         "speedup": round(r["speedup"], 3)} for r in comparisons]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
