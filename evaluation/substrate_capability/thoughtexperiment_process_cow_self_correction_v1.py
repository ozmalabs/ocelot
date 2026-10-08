#!/usr/bin/env python3
"""Measure Linux process-CoW rehearsal against serialized/native-copy controls.

The parent computes the ordinary pre-intervention prediction, then forks a
single-threaded child. The Rust-backed substrate is inherited by Linux using
page-level copy-on-write; the child runs the candidate rehearsal in place and
returns a compact residual over a pipe. The parent verifies graph/rule state
did not change, then persists the namespaced residual receipt.

This is a Linux-specific prototype. It refuses unsafe process/native state and
does not claim that fork is portable or that the fixture covers every effect.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import resource
import statistics
import sys
import threading
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(EVAL_DIR)]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from domains.collapse_model import predict_collapse  # noqa: E402
from domains.self_correction import imagine_and_check_convergence  # noqa: E402
import thoughtexperiment_self_correction_copy_comparison_v1 as controls  # noqa: E402

LOCKED_SOURCES = (
    "domains/self_correction.py",
    "domains/collapse_model.py",
    "domains/imagination.py",
    "domains/reflective_faculty.py",
    "substrate/boot_core.py",
    "seeds/shape_decode_loop.json",
    "tests/test_self_correction.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/checker.rs",
    "runners/dsl/src/cognitive_cycle.rs",
    "runners/dsl/src/grammar.rs",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/graph_rules.rs",
    "runners/dsl/src/l2_adaptive.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/sym.rs",
    "runners/dsl/src/term.rs",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
)
MAX_PIPE_BYTES = 16 * 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256_bytes(payload)


def private_dirty_kb() -> int | None:
    try:
        for line in Path("/proc/self/smaps_rollup").read_text().splitlines():
            if line.startswith("Private_Dirty:"):
                return int(line.split()[1])
    except (OSError, ValueError):
        return None
    return None


def send_child_result(write_fd: int, payload: dict) -> None:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if len(data) > MAX_PIPE_BYTES:
        raise ValueError(f"fork residual exceeds {MAX_PIPE_BYTES} bytes")
    view = memoryview(data)
    while view:
        written = os.write(write_fd, view)
        view = view[written:]


def process_cow_candidate(substrate, candidate: dict, model_before, *,
                          horizon: int, frontier_sample: int,
                          focus_hops: int, imagine_steps: int,
                          observations: list, scoped: bool,
                          persist_receipt: bool = True) -> dict:
    """Fork one isolated child, return its branch residual, persist receipt."""
    if not hasattr(os, "fork") or not sys.platform.startswith("linux"):
        raise RuntimeError("process-CoW thoughtexperiments require Linux os.fork")
    task_count = len(os.listdir("/proc/self/task"))
    if task_count != 1 or threading.active_count() != 1:
        raise RuntimeError(f"refusing process fork with active threads: proc={task_count}")
    native = substrate._inner
    native.assert_experiment_fork_safe()

    before_graph = native.graph_to_dict()
    before_rules = native.export_rules()
    before_graph_digest = canonical_digest(before_graph)
    before_rules_digest = canonical_digest(before_rules)
    branch_id = uuid.uuid4().hex
    read_fd, write_fd = os.pipe()
    started_ns = time.perf_counter_ns()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        private_before = private_dirty_kb()
        child_started_ns = time.perf_counter_ns()
        try:
            result = imagine_and_check_convergence(
                substrate, candidate, model_before=model_before,
                horizon=horizon, frontier_sample=frontier_sample,
                focus_hops=focus_hops, imagine_steps=imagine_steps,
                experiment_focus_nodes=observations,
                snapshot_backend=("process_in_place_scoped" if scoped else "process_in_place"),
                _process_forked=True,
            )
            imagined = result["imagined"]
            residual = {
                "conclusions": imagined.conclusions,
                "derived_only": imagined.derived_only,
            }
            report = {
                "ok": True,
                "branch_id": branch_id,
                "converges": bool(result["converges"]),
                "inert": bool(result["inert"]),
                "applied": result["applied"],
                "residual_before": float(result["model_before"].residual),
                "residual_after": float(result["model_after"].residual),
                "frontier_growth_before": float(result["model_before"].frontier_growth_rate),
                "frontier_growth_after": float(result["model_after"].frontier_growth_rate),
                "steps_run": int(result["model_after"].imagine_steps_run),
                "n_conclusions": int(imagined.n_conclusions),
                "residual": residual,
                "child_wall_ms": (time.perf_counter_ns() - child_started_ns) / 1_000_000,
                "child_private_dirty_before_kb": private_before,
                "child_private_dirty_after_kb": private_dirty_kb(),
                "child_peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            }
            send_child_result(write_fd, report)
            os.close(write_fd)
            os._exit(0)
        except BaseException as exc:
            error = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            try:
                send_child_result(write_fd, error)
            except BaseException:
                pass
            os.close(write_fd)
            os._exit(1)

    os.close(write_fd)
    chunks = []
    total = 0
    while True:
        block = os.read(read_fd, 65_536)
        if not block:
            break
        chunks.append(block)
        total += len(block)
        if total > MAX_PIPE_BYTES:
            os.kill(pid, 9)
            os.close(read_fd)
            os.waitpid(pid, 0)
            raise RuntimeError("fork residual exceeded parent read limit")
    os.close(read_fd)
    _, status = os.waitpid(pid, 0)
    elapsed_ms = (time.perf_counter_ns() - started_ns) / 1_000_000
    if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
        raise RuntimeError(f"fork child exited abnormally: wait_status={status}")
    report = json.loads(b"".join(chunks))
    if not report.get("ok"):
        raise RuntimeError(f"fork child failed: {report.get('error')}")

    after_graph = native.graph_to_dict()
    after_rules = native.export_rules()
    parent_unchanged = (
        canonical_digest(after_graph) == before_graph_digest
        and canonical_digest(after_rules) == before_rules_digest
    )
    if not parent_unchanged:
        raise RuntimeError("OS-CoW child changed primary graph or native rewrite rules")

    residual_json = json.dumps(report["residual"], sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
    residual_digest = sha256_bytes(residual_json.encode())
    result = {
        **{key: report[key] for key in (
            "converges", "inert", "applied", "residual_before", "residual_after",
            "frontier_growth_before", "frontier_growth_after", "steps_run", "n_conclusions",
        )},
        "branch_id": branch_id,
        "candidate_digest": canonical_digest(candidate),
        "residual": report["residual"],
        "residual_digest": residual_digest,
        "parent_graph_and_rules_unchanged_before_receipt": parent_unchanged,
        "fork_child_pipe_wall_ms": elapsed_ms,
        "child_wall_ms": report["child_wall_ms"],
        "receipt_persist_ms": 0.0,
        "child_private_dirty_before_kb": report["child_private_dirty_before_kb"],
        "child_private_dirty_after_kb": report["child_private_dirty_after_kb"],
        "child_peak_rss_kb": report["child_peak_rss_kb"],
    }
    if persist_receipt:
        result["receipt_node_id"] = persist_process_receipt(
            substrate, candidate, result, probe="self_correction_shape_decode_fixture_v1")
    else:
        result["receipt_node_id"] = None
    return result


def persist_process_receipt(substrate, candidate: dict, result: dict, *, probe: str) -> int:
    """Persist one already-validated branch residual into the primary graph."""
    residual_json = json.dumps(result["residual"], sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
    receipt_start = time.perf_counter_ns()
    receipt = substrate.add_node("ThoughtexperimentReceipt", {
        "branch_id": result["branch_id"],
        "candidate_label": str(candidate.get("label") or ""),
        "candidate_digest": result["candidate_digest"],
        "probe": probe,
        "converges": result["converges"],
        "inert": result["inert"],
        "residual_before": result["residual_before"],
        "residual_after": result["residual_after"],
        "frontier_growth_before": result["frontier_growth_before"],
        "frontier_growth_after": result["frontier_growth_after"],
        "steps_run": result["steps_run"],
        "n_conclusions": result["n_conclusions"],
        "residual_digest": result["residual_digest"],
        "residual_json": residual_json,
        "parent_unchanged_before_receipt": result["parent_graph_and_rules_unchanged_before_receipt"],
        "status": "received",
    })
    result["receipt_persist_ms"] = (time.perf_counter_ns() - receipt_start) / 1_000_000
    return receipt.value


def run_process_cell(size: int, arm: str, repeats: int, warmups: int,
                     backend: str = "linux_process_cow") -> dict:
    rows = []
    for iteration in range(warmups + repeats):
        substrate, native, correct, wrong, observations = controls.make_fixture(size)
        candidate = correct if arm == "correct" else wrong
        model_started = time.perf_counter_ns()
        model_before = predict_collapse(
            substrate, horizon=3, imagine_steps=2,
            snapshot_backend="native_full_copy",
        )
        model_before_ms = (time.perf_counter_ns() - model_started) / 1_000_000
        result = process_cow_candidate(
            substrate, candidate, model_before,
            horizon=3, frontier_sample=50, focus_hops=1, imagine_steps=2,
            observations=observations, scoped=backend.endswith("_scoped"),
        )
        result["model_before_converged"] = bool(model_before.converged)
        result["model_before_residual"] = float(model_before.residual)
        result["model_before_frontier_growth"] = float(model_before.frontier_growth_rate)
        result["model_before_wall_ms"] = model_before_ms
        result["total_wall_ms"] = model_before_ms + result["fork_child_pipe_wall_ms"] + result["receipt_persist_ms"]
        result["unrelated_nodes_requested"] = size
        result["candidate_arm"] = arm
        if iteration >= warmups:
            rows.append(result)
    return {
        "unrelated_nodes_requested": size,
        "candidate_arm": arm,
        "snapshot_backend": backend,
        "repeats": repeats,
        "warmups": warmups,
        "median_total_wall_ms": statistics.median(r["total_wall_ms"] for r in rows),
        "median_model_before_wall_ms": statistics.median(r["model_before_wall_ms"] for r in rows),
        "median_fork_child_pipe_wall_ms": statistics.median(r["fork_child_pipe_wall_ms"] for r in rows),
        "median_child_wall_ms": statistics.median(r["child_wall_ms"] for r in rows),
        "median_receipt_persist_ms": statistics.median(r["receipt_persist_ms"] for r in rows),
        "median_child_private_dirty_delta_kb": statistics.median(
            (r["child_private_dirty_after_kb"] or 0) - (r["child_private_dirty_before_kb"] or 0)
            for r in rows
        ),
        "outcomes": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 1000, 10000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--order-seed", type=int, default=20260930,
                        help="seed for reproducible randomized order of candidate/backend cells")
    parser.add_argument("--out", type=Path, default=ROOT / "evaluation/reports/thoughtexperiment_process_cow_self_correction_v1.json")
    args = parser.parse_args()
    if not sys.platform.startswith("linux") or not hasattr(os, "fork"):
        raise SystemExit("this protocol requires Linux process CoW via os.fork")
    if args.repeats < 1 or args.warmups < 0 or any(n < 0 for n in args.sizes):
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine; rebuild before measuring: {stale}")

    results = []
    control_results = []
    semantic_comparisons = []
    backends = ("linux_process_cow", "linux_process_cow_scoped", *controls.BACKENDS)
    cells = [(arm, backend) for arm in ("correct", "wrong") for backend in backends]
    rng = random.Random(args.order_seed)
    schedule = []
    warmup_order = []

    # Warm every path once per size/candidate, then execute each repeat as a
    # randomized complete block containing all candidate/backend combinations.
    for size in args.sizes:
        for arm, backend in cells:
            warmup_order.append({"size": size, "arm": arm, "backend": backend})
            if backend.startswith("linux_process_cow"):
                run_process_cell(size, arm, repeats=1, warmups=0, backend=backend)
            else:
                controls.run_cell(size, arm, backend, repeats=1, warmups=0)

        process_trials = {(arm, backend): [] for arm, backend in cells
                          if backend.startswith("linux_process_cow")}
        control_trials = {(arm, backend): [] for arm, backend in cells
                          if not backend.startswith("linux_process_cow")}
        for iteration in range(args.repeats):
            block = list(cells)
            rng.shuffle(block)
            for arm, backend in block:
                schedule.append({"iteration": iteration, "size": size,
                                 "arm": arm, "backend": backend})
                if backend.startswith("linux_process_cow"):
                    trial = run_process_cell(size, arm, repeats=1, warmups=0, backend=backend)
                    process_trials[(arm, backend)].extend(trial["outcomes"])
                else:
                    trial = controls.run_cell(size, arm, backend, repeats=1, warmups=0)
                    control_trials[(arm, backend)].extend(trial["outcomes"])

        for arm, backend in cells:
            if backend.startswith("linux_process_cow"):
                rows = process_trials[(arm, backend)]
                results.append({
                    "unrelated_nodes_requested": size,
                    "candidate_arm": arm,
                    "snapshot_backend": backend,
                    "repeats": len(rows),
                    "warmups": 1,
                    "median_total_wall_ms": statistics.median(r["total_wall_ms"] for r in rows),
                    "median_model_before_wall_ms": statistics.median(r["model_before_wall_ms"] for r in rows),
                    "median_fork_child_pipe_wall_ms": statistics.median(r["fork_child_pipe_wall_ms"] for r in rows),
                    "median_child_wall_ms": statistics.median(r["child_wall_ms"] for r in rows),
                    "median_receipt_persist_ms": statistics.median(r["receipt_persist_ms"] for r in rows),
                    "median_child_private_dirty_delta_kb": statistics.median(
                        (r["child_private_dirty_after_kb"] or 0) -
                        (r["child_private_dirty_before_kb"] or 0) for r in rows),
                    "outcomes": rows,
                })
            else:
                rows = control_trials[(arm, backend)]
                elapsed = [r["trial_wall_ms"] for r in rows]
                control_results.append({
                    "unrelated_nodes_requested": size,
                    "candidate_arm": arm,
                    "snapshot_backend": backend,
                    "repeats": len(rows),
                    "warmups": 1,
                    "median_ms": statistics.median(elapsed),
                    "min_ms": min(elapsed),
                    "max_ms": max(elapsed),
                    "outcomes": rows,
                })

    def semantic_signature(row: dict) -> tuple:
        applied = row["applied"]
        normalized_applied = {
            name: value.rsplit("_", 1)[0] if isinstance(value, str) and
            value.rsplit("_", 1)[-1].isalnum() and len(value.rsplit("_", 1)[-1]) == 8
            else value
            for name, value in applied.items()
        }
        residual = row.get("residual")
        if residual is None:
            residual = {"conclusions": row.get("conclusions"),
                        "derived_only": row.get("derived_only")}
        return (
            row["converges"], row["inert"], json.dumps(normalized_applied, sort_keys=True),
            row["residual_before"], row["residual_after"],
            row["frontier_growth_before"], row["frontier_growth_after"],
            row["steps_run"], row["n_conclusions"],
            json.dumps(residual, sort_keys=True, separators=(",", ":")),
        )

    control_by = {(r["unrelated_nodes_requested"], r["candidate_arm"], r["snapshot_backend"]): r
                  for r in control_results}
    process_by = {(r["unrelated_nodes_requested"], r["candidate_arm"], r["snapshot_backend"]): r for r in results}
    for size in args.sizes:
        for arm in ("correct", "wrong"):
            process_rows = process_by[(size, arm, "linux_process_cow")]["outcomes"]
            scoped_rows = process_by[(size, arm, "linux_process_cow_scoped")]["outcomes"]
            control_rows = [
                control_by[(size, arm, backend)]["outcomes"]
                for backend in controls.BACKENDS
            ]
            signatures = [semantic_signature(row) for row in process_rows]
            matched = all(
                all(signatures[idx] == semantic_signature(rows[idx]) for rows in control_rows)
                for idx in range(len(signatures))
            ) and all(len(rows) == len(signatures) for rows in control_rows) and all(
                len(scoped_rows) == len(signatures) and
                semantic_signature(process_rows[idx]) == semantic_signature(scoped_rows[idx])
                for idx in range(len(signatures)))
            expected = arm == "correct"
            expected_control = all(row["converges"] is expected
                                   for row in process_rows + scoped_rows + [row for rows in control_rows for row in rows])
            parent_isolated = all(row["parent_graph_and_rules_unchanged_before_receipt"]
                                  for row in process_rows + scoped_rows)
            if not (matched and expected_control and parent_isolated):
                raise SystemExit(f"process-CoW parity/isolation failed size={size} arm={arm}")
            semantic_comparisons.append({
                "size": size, "arm": arm, "matched_repeats_per_backend": args.repeats,
                "exact_prediction_and_residual_parity": True,
                "parent_graph_and_rule_isolation": True,
                "expected_control_outcome": "converges" if expected else "diverges",
                "control_outcome_gate_passed": expected_control,
            })
    native_path = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentProcessCowSelfCorrectionV1",
        "implementation_status": "Linux_process_fork_page_CoW_child_in_place; residual_pipe_return; deep-copy_and_serialization_controls_available",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0], "process_threads": len(os.listdir("/proc/self/task"))},
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__).resolve())},
        "binary": {"path": str(native_path), "sha256": sha256_file(native_path)},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sources": {name: sha256_file(ROOT / name) for name in LOCKED_SOURCES},
        "protocol": {
            "fork_eligibility": "Linux only; one process thread; no Python hooks, agent thread, initialized memory faculty, pending graph effects/attribute-write observations, framebuffer handles, or native reads_external rules",
            "parent_invariant": "exact canonical graph and native rewrite-rule digests before fork equal digests after child exit and before receipt persistence",
            "residual_return": "child sends full graph-diff conclusions and derived-only residual over a pipe; parent stores JSON and digest in ThoughtexperimentReceipt without merging branch state",
            "limits": ["one synthetic self-correction fixture family", "single host", "no concurrent branches", "no external OS sandbox; eligibility is a source/runtime effect guard, not security isolation"],
        },
        "comparison_order": [
            *schedule
        ],
        "comparison_order_seed": args.order_seed,
        "comparison_order_design": "one seeded randomized complete block per repeat and graph size; each block contains both candidate arms on process-CoW, serialization, and native-full-copy backends",
        "warmup_order": warmup_order,
        "timing_components": {
            "process_cow_model_before_ms": "separately reported native full-copy baseline prediction cost",
            "process_cow_fork_child_pipe_ms": "fork through child completion and residual transfer; includes branch execution/readout",
            "process_cow_child_wall_ms": "child candidate rehearsal through residual assembly, excludes pipe transfer",
            "process_cow_receipt_persist_ms": "primary receipt write, reported separately",
            "process_cow_total_wall_ms": "sum of model-before, fork-child-pipe, and receipt persistence; fixture construction excluded",
            "copy_control_median_ms": "full model-before plus branch rehearsal/readout; fixture construction excluded",
        },
        "semantic_comparisons": semantic_comparisons,
        "results": results,
        "copy_controls": control_results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(capture, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "cells": len(results),
                      "medians_ms": [{"size": r["unrelated_nodes_requested"], "arm": r["candidate_arm"],
                                      "total": r["median_total_wall_ms"], "fork_child_pipe": r["median_fork_child_pipe_wall_ms"],
                                      "private_dirty_delta_kb": r["median_child_private_dirty_delta_kb"]}
                                     for r in results]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
