#!/usr/bin/env python3
"""Compare ordinary, mutation-log, and full-snapshot closure reporting costs."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners/dsl/python"))
sys.path.insert(0, str(ROOT))

from domains.engine_provenance import rust_source_fingerprint  # noqa: E402
from substrate_rs import Substrate  # noqa: E402
from substrate_rs.ext import add_rule  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def empty_graph(size: int) -> Substrate:
    substrate = Substrate()
    for _ in range(size):
        substrate.add_node("DeltaAuditBenchNode", {})
    substrate._inner.run_rules(10)  # warm the empty-closure path
    return substrate


def measure(size: int, repeats: int) -> dict:
    substrate = empty_graph(size)
    pairs = []
    for replicate in range(repeats):
        order = ["plain", "observer", "snapshot"]
        if replicate % 3:
            order = order[replicate % 3 :] + order[: replicate % 3]
        times = {}
        for mode in order:
            start = time.perf_counter_ns()
            if mode == "plain":
                outcome = substrate._inner.run_rules(10)
                if outcome != 0:
                    raise RuntimeError(f"unexpected empty-closure progress: {outcome}")
            elif mode == "observer":
                outcome = substrate._inner.run_rules_delta_report(10, False)
                if outcome["affected_nodes"] or outcome["affected_edges"]:
                    raise RuntimeError(f"no-op mutation observer emitted targets: {outcome}")
            else:
                outcome = substrate._inner.run_rules_snapshot_delta_report(10, False)
                if outcome["affected_nodes"] or outcome["affected_edges"]:
                    raise RuntimeError(f"no-op snapshot emitted targets: {outcome}")
            elapsed = time.perf_counter_ns() - start
            times[f"{mode}_ns"] = elapsed
        pairs.append(times)
    plain = [p["plain_ns"] for p in pairs]
    observer = [p["observer_ns"] for p in pairs]
    snapshot = [p["snapshot_ns"] for p in pairs]
    return {
        "node_count": size,
        "edge_count": 0,
        "repeats": repeats,
        "pairs": pairs,
        "median_plain_ns": statistics.median(plain),
        "median_observer_ns": statistics.median(observer),
        "median_snapshot_ns": statistics.median(snapshot),
        "observer_ratio_to_plain": statistics.median(observer) / statistics.median(plain),
        "snapshot_ratio_to_plain": statistics.median(snapshot) / statistics.median(plain),
    }


def active_edge_call(size: int, mode: str) -> tuple[int, dict | None]:
    substrate = Substrate()
    for _ in range(size):
        src = substrate.add_node("DeltaAuditBenchSource", {})
        tgt = substrate.add_node("DeltaAuditBenchTarget", {})
        substrate.add_edge_unchecked(src, "delta_input", tgt)
    add_rule(
        substrate._inner,
        "delta_report_active_edge_rule",
        [("src", "delta_input", "tgt")],
        [["add_edge", "src", "delta_derived", "tgt", {}]],
    )
    start = time.perf_counter_ns()
    if mode == "plain":
        outcome = substrate._inner.run_rules(100_000)
        report = None
    elif mode == "observer":
        report = substrate._inner.run_rules_delta_report(100_000, False)
        outcome = report["progress_steps"]
    else:
        report = substrate._inner.run_rules_snapshot_delta_report(100_000, False)
        outcome = report["progress_steps"]
    elapsed = time.perf_counter_ns() - start
    if outcome <= 0:
        raise RuntimeError(f"active fixture made no progress on {size} matches")
    if report is not None:
        if report["status"] != "fixed_point":
            raise RuntimeError(f"active fixture did not settle: {report}")
        if substrate._inner.node_count() != 2 * size:
            raise RuntimeError("active fixture changed node count unexpectedly")
        if report["progress_steps"] != 1:
            raise RuntimeError(f"expected one progressing settlement pass: {report}")
        if mode == "observer" and (
            len(report["affected_nodes"]) != 2 * size
            or len(report["affected_edges"]) != size
        ):
            raise RuntimeError(f"unexpected observer target counts: {report}")
        if mode == "snapshot" and (
            len(report["affected_nodes"]) != 2 * size
            or len(report["affected_edges"]) != size
        ):
            raise RuntimeError(f"unexpected exact delta counts: {report}")
    return elapsed, report


def measure_active(size: int, repeats: int) -> dict:
    pairs = []
    for replicate in range(repeats):
        order = ["plain", "observer", "snapshot"]
        if replicate % 3:
            order = order[replicate % 3 :] + order[: replicate % 3]
        pair = {}
        targets = {}
        for mode in order:
            elapsed, report = active_edge_call(size, mode)
            pair[f"{mode}_ns"] = elapsed
            if report is not None:
                targets[mode] = (
                    set(report["affected_nodes"]),
                    {tuple(edge) for edge in report["affected_edges"]},
                )
                pair[f"{mode}_targets"] = {
                    "nodes": len(report["affected_nodes"]),
                    "edges": len(report["affected_edges"]),
                }
        if not targets["snapshot"][0] <= targets["observer"][0]:
            raise RuntimeError(f"observer missed exact node targets at size={size}")
        if not targets["snapshot"][1] <= targets["observer"][1]:
            raise RuntimeError(f"observer missed exact edge targets at size={size}")
        pairs.append(pair)
    medians = {
        f"median_{mode}_ns": statistics.median(pair[f"{mode}_ns"] for pair in pairs)
        for mode in ("plain", "observer", "snapshot")
    }
    return {
        "matched_input_edges": size,
        "expected_derived_edges": size,
        "repeats": repeats,
        "pairs": pairs,
        **medians,
        "observer_ratio_to_plain": medians["median_observer_ns"] / medians["median_plain_ns"],
        "snapshot_ratio_to_plain": medians["median_snapshot_ns"] / medians["median_plain_ns"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[1000, 10000, 50000])
    parser.add_argument("--active-sizes", type=int, nargs="+", default=[64, 512, 2048])
    parser.add_argument("--repeats", type=int, default=9)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evaluation/reports/substrate_rule_graph_delta_report_overhead_20260925.json",
    )
    args = parser.parse_args()
    native = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    report = {
        "study": "substrate_rule_graph_delta_report_overhead",
        "date": "2026-09-25",
        "scope": "empty fixed-point plus sparse add-edge closure; compares normal, mutation-log and full-snapshot costs",
        "runner_sha256": sha256(Path(__file__)),
        "native_sha256": sha256(native),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sizes": [measure(size, args.repeats) for size in args.sizes],
        "active_edge_closure": [measure_active(size, min(args.repeats, 5)) for size in args.active_sizes],
        "limits": [
            "one host and process; timings are diagnostic microbenchmarks",
            "empty-closure arm has no active rules or graph writes",
            "active edge closure is a sparse synthetic rule, not a natural workload",
            "does not include frame mapping, deferred effects, or external notification routing",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
if __name__ == "__main__":
    main()
