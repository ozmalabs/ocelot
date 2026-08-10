"""Ask Jabberwock to propose a performance test.

Jabberwock's hardware-aware design (commit bc4fe5f, scripts/jabberwock_
optimal_runner_for_this_system.py) made specific quantitative
predictions for the Ryzen 9600X target. With the implementation now
substantially built out (l1_hot_paths.rs + l2_dispatch.rs + l2_adaptive.rs
+ l3_drives.rs + l3_lqr.rs + l3_mpc.rs + code_cache.rs + l6_*), some of
those predictions are testable.

Method: walk the design's quantitative claims + identify ones that
match implemented components + propose a specific microbenchmark.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")


def main():
    print("=" * 72)
    print("JABBERWOCK PROPOSES A PERFORMANCE TEST")
    print("=" * 72)
    print()

    # ---------------------------------------------------------------
    # 1. What predictions did Jabberwock make (from commit bc4fe5f)?
    # ---------------------------------------------------------------
    print("Quantitative predictions from the hardware-aware design")
    print("(commit bc4fe5f, Ryzen 9600X + AVX-512 + 32 MiB L3):")
    print()
    predictions = [
        ("Graph mutations",
         "~30M node mutations/sec sustained (arena + AVX-512 packing)"),
        ("Rule firings",
         "~10K reflexes per 100µs tick = ~100M reflex-firings/sec across "
         "6 workers"),
        ("Kalman updates",
         "~250K state-vector updates/sec for dim ≤ 64 single-core; "
         "~1.5M/sec at 6 cores"),
        ("Working set",
         "up to 32 MiB resides in L3 — DRAM bandwidth-bound only above"),
        ("Speedup vs generic",
         "30-50× wall-clock for representative substrate workloads "
         "(rule-heavy + numeric)"),
    ]
    for name, claim in predictions:
        print(f"  · {name}")
        print(f"      {claim}")
    print()

    # ---------------------------------------------------------------
    # 2. What's implemented + testable?
    # ---------------------------------------------------------------
    print("=" * 72)
    print("Match against implemented components:")
    print("=" * 72)
    print()
    matches = [
        ("Graph mutations",
         "substrate.add_node + graph.rs arena slabs",
         "TESTABLE — measure raw add_node throughput"),
        ("Rule firings",
         "l2_dispatch::Scheduler + l2_adaptive::AdaptiveDispatcher::submit",
         "TESTABLE — measure submit throughput across 6 workers"),
        ("Kalman updates",
         "l3_drives::KalmanFilter1D::update",
         "TESTABLE — 1D Kalman is the simplest case; "
         "multi-dim is deferred"),
        ("Working set",
         "implicit in L1 layout choices",
         "PARTIAL — hard to measure directly without perf counters"),
        ("Speedup vs generic",
         "would need a 'generic' baseline runner",
         "DEFERRED — no baseline to compare against"),
    ]
    for pred_name, impl_ref, verdict in matches:
        print(f"  · {pred_name}")
        print(f"      impl: {impl_ref}")
        print(f"      → {verdict}")
        print()

    # ---------------------------------------------------------------
    # 3. The proposal
    # ---------------------------------------------------------------
    print("=" * 72)
    print("JABBERWOCK'S PROPOSED PERFORMANCE TEST")
    print("=" * 72)
    print()
    print("  Three microbenchmarks, each pitting a specific")
    print("  Jabberwock-prediction against measured reality:")
    print()
    print("  Benchmark 1: Graph mutation throughput")
    print("    Prediction:  ~30M node mutations/sec sustained")
    print("    Method:      add N=10⁶ nodes via TypedGraph::insert_node")
    print("                  to a single-type arena. Measure wall clock.")
    print("    Report:      nodes/sec.")
    print()
    print("  Benchmark 2: L2 dispatcher submit throughput")
    print("    Prediction:  ~10K reflexes per 100µs tick =")
    print("                  ~100M reflex-firings/sec across 6 workers")
    print("    Method:      Submit N=10⁵ no-op tasks to a 6-worker")
    print("                  Scheduler. Time submit() + drain.")
    print("    Report:      submits/sec.")
    print()
    print("  Benchmark 3: 1D Kalman update throughput")
    print("    Prediction:  ~250K state updates/sec single-core")
    print("    Method:      KalmanFilter1D::update(measurement)")
    print("                  loop N=10⁶ times. Measure wall clock.")
    print("    Report:      updates/sec.")
    print()
    print("  Honesty caveats Jabberwock notes:")
    print("    · Prediction was 'sustained' rate — short-burst")
    print("      benchmarks may exceed it because L1/L2 caches are")
    print("      cold for a real substrate's mixed-workload pattern.")
    print("    · KalmanFilter1D is 1-dimensional; predictions were for")
    print("      ≤64-dim. 1D is the simplest case + should beat the")
    print("      multi-dim prediction.")
    print("    · The 100M reflex-firings/sec includes work inside the")
    print("      reflex (rule evaluation); no-op submit measures just")
    print("      the dispatcher overhead, which should be much faster.")
    print()
    print("  Each measurement gets compared against the prediction.")
    print("  Beat the prediction = the implementation matches the")
    print("  design Jabberwock surfaced from its vocabulary.")
    print("  Miss the prediction = a real gap to investigate.")


if __name__ == "__main__":
    main()
