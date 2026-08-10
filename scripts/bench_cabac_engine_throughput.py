"""Pure-Rust CABAC engine throughput.

Bypasses the Python bridge entirely — the Rust function constructs
the bin stream, encodes and decodes, then returns the wall time.
This isolates engine cost from the per-bin FFI overhead that
dominated earlier `cabac_round_trip`-based measurements.

Three scenarios:
  all-MPS   — the MPS path stays on, range rarely renorms
  9:1 skew  — typical video distribution
  50/50     — maximum mixing, every bin probably renorms

What the hand-tune produced:
  Before / after the renorm rewrite (single-bit loop vs
  `leading_zeros`-driven bulk shift) are within noise on this
  host — rustc with `-O3 + fat LTO` was already producing
  near-identical code for both forms. The fast-path `if range
  >= 256 return` is the one thing that genuinely matters, and
  the single-bit `while range < 256` already had it for free.

Reproducing the head-to-head:
  cargo build --release                       # tuned
  cargo build --release --features cabac_baseline  # baseline
  cp target/release/libsubstrate_rs.so python/substrate_rs/_native.abi3.so
  python scripts/bench_cabac_engine_throughput.py

Tuned & baseline numbers on this host (12-core, June 2026):
  all-MPS  : ~2.95 ns/bin (both variants)
  9:1 skew : ~2.50 ns/bin (both variants)
  50/50    : ~2.70 ns/bin (both variants)

The headline isn't "we got 2x" — it's "the engine is already
in the 2-3 ns/bin band, comparable to libavcodec's hand-tuned
scalar C." The earlier 59 ns/bin number was Python-overhead-
dominated (one PyTuple constructed per bin in the bridge),
not engine cost.
"""
import sys
import time

from substrate_rs import Substrate


def main(n_bins: int = 5_000_000, runs: int = 5) -> None:
    s = Substrate()
    # (label, p_state_idx, val_mps, skew_one_in)
    scenarios = [
        ("all-MPS ", 30, 1, 10_000_000),  # never hit LPS
        ("9:1 skew", 30, 1, 10),
        ("50/50   ", 30, 1, 2),
    ]
    print(f"CABAC engine throughput — {n_bins:,} bins × encode+decode, "
          f"{runs} runs")
    for label, pstate, vmps, skew in scenarios:
        times = []
        for _ in range(runs):
            elapsed_rs, _ = s._inner.cabac_bench_mixed_bins(
                n_bins, pstate, vmps, skew,
            )
            times.append(elapsed_rs)
        avg = sum(times) / len(times)
        ns_per_bin = (avg * 1e9) / (2 * n_bins)
        mn = (min(times) * 1e9) / (2 * n_bins)
        mx = (max(times) * 1e9) / (2 * n_bins)
        print(f"  {label}: {ns_per_bin:5.2f} ns/bin  "
              f"(min {mn:.2f}, max {mx:.2f})")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5_000_000
    r = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    main(n, r)
