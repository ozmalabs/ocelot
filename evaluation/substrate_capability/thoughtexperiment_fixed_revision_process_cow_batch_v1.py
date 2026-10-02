#!/usr/bin/env python3
"""Compare fixed-revision native-copy batches with process-CoW batches.

Both arms compute one baseline. Each candidate then starts from the same
unchanged primary revision: eager native full copy in the control arm, Linux
fork page-CoW in the treatment. The child returns the same nested residual
and prediction row used by the native batch runner. Whole-graph digests are
checked before and after the timed panel; O(1) semantic revisions guard each
fork return.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import statistics
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(EVAL_DIR)]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from domains.collapse_model import predict_collapse  # noqa: E402
from domains.self_correction import (  # noqa: E402
    _default_candidates,
    imagine_candidate_batch,
    imagine_and_check_convergence,
)
import thoughtexperiment_self_correction_copy_comparison_v1 as controls  # noqa: E402
from thoughtexperiment_fixed_revision_six_candidate_batch_v1 import (  # noqa: E402
    LOCKED_SOURCES as BATCH_LOCKED_SOURCES,
    SCOPED_BACKEND,
    graph_and_rule_digest,
    result_row,
)

LOCKED_SOURCES = tuple(dict.fromkeys((
    *BATCH_LOCKED_SOURCES,
    "evaluation/substrate_capability/thoughtexperiment_fixed_revision_six_candidate_batch_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_fixed_revision_process_cow_batch_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
)))
MAX_PIPE_BYTES = 16 * 1024 * 1024


def send_child_result(fd: int, value: dict) -> None:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()
    if len(data) > MAX_PIPE_BYTES:
        raise ValueError(f"candidate result exceeds {MAX_PIPE_BYTES} bytes")
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        view = view[written:]


def fork_candidate(native, substrate, candidate, baseline, observations,
                   expected_revision: tuple[int, int, int]) -> dict:
    """Run one candidate in a fresh fork child and return its exact result row."""
    if not hasattr(os, "fork") or not sys.platform.startswith("linux"):
        raise RuntimeError("process-CoW arm requires Linux os.fork")
    task_count = len(os.listdir("/proc/self/task"))
    if task_count != 1 or threading.active_count() != 1:
        raise RuntimeError(f"refusing process fork with active threads: proc={task_count}")
    native.assert_experiment_fork_safe()
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            result = imagine_and_check_convergence(
                substrate, candidate, model_before=baseline,
                horizon=3, frontier_sample=50, focus_hops=1, imagine_steps=2,
                experiment_focus_nodes=observations,
                snapshot_backend="process_in_place_scoped",
                _prediction_snapshot_backend=SCOPED_BACKEND,
                _process_forked=True, record_trace=False)
            send_child_result(write_fd, {
                "ok": True,
                "row": result_row(result, candidate["label"]),
            })
            os.close(write_fd)
            os._exit(0)
        except BaseException as exc:
            try:
                send_child_result(write_fd, {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                })
            except BaseException:
                pass
            os.close(write_fd)
            os._exit(1)

    os.close(write_fd)
    chunks, total = [], 0
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
            raise RuntimeError("candidate result exceeded pipe cap")
    os.close(read_fd)
    _, status = os.waitpid(pid, 0)
    if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
        raise RuntimeError(f"candidate child exited abnormally: {status}")
    message = json.loads(b"".join(chunks))
    if not message.get("ok"):
        raise RuntimeError(f"candidate child failed: {message.get('error')}")
    if tuple(native.experiment_graph_rule_revision()) != expected_revision:
        raise RuntimeError("primary graph/rule revision changed across candidate fork")
    return message["row"]


def run_native_batch(size: int) -> dict:
    sub, native, _correct, _wrong, observations = controls.make_fixture(size)
    candidates = _default_candidates(native, "sd_mint_quantum")
    before = graph_and_rule_digest(native)
    started = time.perf_counter_ns()
    batch = imagine_candidate_batch(
        sub, candidates, horizon=3, frontier_sample=50, focus_hops=1,
        imagine_steps=2, snapshot_backend=SCOPED_BACKEND,
        experiment_focus_nodes=observations, record_trace=False)
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    after = graph_and_rule_digest(native)
    rows = [result_row(row, candidate["label"])
            for row, candidate in zip(batch["results"], candidates)]
    return {"elapsed_ms": elapsed_ms, "rows": rows,
            "primary_unchanged": before == after
            and batch["primary_graph_and_rules_unchanged_during_batch"]}


def run_process_batch(size: int) -> dict:
    sub, native, _correct, _wrong, observations = controls.make_fixture(size)
    candidates = _default_candidates(native, "sd_mint_quantum")
    before = graph_and_rule_digest(native)
    started = time.perf_counter_ns()
    baseline = predict_collapse(
        sub, horizon=3, frontier_sample=50, focus_hops=1, imagine_steps=2,
        snapshot_backend=SCOPED_BACKEND, record_trace=False)
    revision = tuple(native.experiment_graph_rule_revision())
    rows = [fork_candidate(native, sub, candidate, baseline, observations, revision)
            for candidate in candidates]
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    after = graph_and_rule_digest(native)
    return {"elapsed_ms": elapsed_ms, "rows": rows,
            "primary_unchanged": before == after,
            "one_baseline_shared": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 1000, 10000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not sys.platform.startswith("linux") or not hasattr(os, "fork"):
        raise SystemExit("this protocol requires Linux fork page-CoW")
    if args.repeats < 1 or args.warmups < 0 or any(n < 0 for n in args.sizes):
        parser.error("repeats must be positive; warmups and sizes nonnegative")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine: {stale}")

    rng = random.Random(args.seed)
    comparisons, schedule = [], []
    for size in args.sizes:
        samples = {"native_full_copy_batch": [], "process_cow_batch": []}
        for iteration in range(args.warmups + args.repeats):
            order = list(samples)
            rng.shuffle(order)
            pair = {}
            for mode in order:
                pair[mode] = run_native_batch(size) if mode == "native_full_copy_batch" \
                    else run_process_batch(size)
                schedule.append({"size": size, "iteration": iteration, "mode": mode})
            if pair["native_full_copy_batch"]["rows"] != pair["process_cow_batch"]["rows"]:
                raise RuntimeError(f"native/process nested residual parity failed at size={size}")
            if not all(trial["primary_unchanged"] for trial in pair.values()):
                raise RuntimeError(f"primary isolation failed at size={size}")
            if iteration >= args.warmups:
                for mode in samples:
                    samples[mode].append(pair[mode])
        native_ms = statistics.median(x["elapsed_ms"] for x in samples["native_full_copy_batch"])
        cow_ms = statistics.median(x["elapsed_ms"] for x in samples["process_cow_batch"])
        rows = samples["process_cow_batch"][0]["rows"]
        useful = sum(r["converges"] and not r["inert"] for r in rows)
        comparisons.append({
            "size": size, "candidate_count": len(rows), "useful_candidates": useful,
            "native_full_copy_batch_median_ms": native_ms,
            "process_cow_batch_median_ms": cow_ms,
            "process_cow_speedup": native_ms / cow_ms,
            "exact_nested_residual_and_outcome_parity": True,
            "primary_graph_and_rules_preserved": True,
            "repeats": args.repeats, "warmups": args.warmups,
            "native_trials": samples["native_full_copy_batch"],
            "process_cow_trials": samples["process_cow_batch"],
        })
    output = {
        "schema": "thoughtexperiment_fixed_revision_process_cow_batch_v1",
        "host": {"platform": platform.platform(), "python": sys.version,
                 "machine": platform.machine()},
        "binary": str(Path(srs._native.__file__).resolve()),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "runner": str(Path(__file__).relative_to(ROOT)),
        "sources": {name: "sha256:" + hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                    for name in LOCKED_SOURCES},
        "implementation_status": "fixed_revision_batch_with_linux_process_page_cow",
        "protocol": {
            "panel": "six deterministic candidates from _default_candidates(sd_mint_quantum)",
            "native_control": "one shared baseline; native_full_copy_scoped branch per candidate",
            "process_treatment": "one shared baseline; fresh Linux fork child per candidate; process_in_place_scoped",
            "revision_guard": "O(1) graph mutation version, rule epoch, and rule-slot count after each child",
            "isolation_gate": "canonical primary graph/rule digests before and after each complete batch",
            "parity_gate": "exact full nested result rows including conclusions, derived_only, and forward-look deltas",
            "timed_region": "baseline prediction plus all six candidates, excluding fixture setup and outer full-state digest checks",
            "order_seed": args.seed,
        },
        "schedule": schedule,
        "comparisons": comparisons,
    }
    encoded = json.dumps(output, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out:
        dest = args.out if args.out.is_absolute() else ROOT / args.out
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(encoded)
        print(dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
