"""Conway benchmark: Python substrate vs Rust substrate_rs.

Same workload, two backends. The workload exercises the engine hot
paths: many small graph mutations (set_type), heavy admissibility
probing via is_edge_admissible, deep Term evaluation per probe (Filter
+ Neighbours + Count + TypeOf + Eq + In + Not + SetT), and per-step
batch decision-then-apply atomicity.

Usage:
    python3 benchmarks/conway_bench.py [--rows R] [--cols C] [--steps N]
                                       [--pattern glider|r_pentomino|random]

The benchmark reports wall-clock time per step + total per backend
plus the relative speedup factor.
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from typing import Callable

from domains import conway as py_conway
from domains_rs import conway as rs_conway


def random_board(seed: int, rows: int, cols: int, density: float = 0.30) -> list[list[int]]:
    rng = random.Random(seed)
    return [[1 if rng.random() < density else 0 for _ in range(cols)] for _ in range(rows)]


PATTERNS: dict[str, Callable[[int, int], list[list[int]]]] = {
    "glider": lambda r, c: rs_conway.glider_board(r, c),
    "r_pentomino": lambda r, c: rs_conway.r_pentomino_board(r, c),
    "random": lambda r, c: random_board(seed=42, rows=r, cols=c),
}


def bench_python(board: list[list[int]], steps: int) -> tuple[float, float, int]:
    """Returns (encode_ms, step_avg_ms, total_changes)."""
    rows, cols = len(board), len(board[0])
    s = py_conway.make_substrate()

    t0 = time.perf_counter()
    py_conway.encode_board(s, [row[:] for row in board])
    encode_ms = (time.perf_counter() - t0) * 1000.0

    total_changes = 0
    t1 = time.perf_counter()
    for _ in range(steps):
        total_changes += py_conway.step(s)
    step_total = time.perf_counter() - t1
    return encode_ms, (step_total * 1000.0 / steps), total_changes


def bench_rust(board: list[list[int]], steps: int) -> tuple[float, float, int]:
    rows, cols = len(board), len(board[0])
    s = rs_conway.make_substrate()

    t0 = time.perf_counter()
    rs_conway.encode_board(s, [row[:] for row in board])
    encode_ms = (time.perf_counter() - t0) * 1000.0

    total_changes = 0
    t1 = time.perf_counter()
    for _ in range(steps):
        total_changes += rs_conway.step(s)
    step_total = time.perf_counter() - t1
    return encode_ms, (step_total * 1000.0 / steps), total_changes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", type=int, default=30)
    ap.add_argument("--cols", type=int, default=30)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--pattern", choices=PATTERNS.keys(), default="random")
    args = ap.parse_args()

    board = PATTERNS[args.pattern](args.rows, args.cols)
    alive = sum(sum(r) for r in board)
    print(f"\nConway benchmark — {args.rows}×{args.cols} grid, "
          f"pattern={args.pattern} ({alive} alive at t=0), {args.steps} steps\n")
    print(f"{'backend':10s}  {'encode (ms)':>12s}  {'step avg (ms)':>14s}  "
          f"{'total step (ms)':>16s}  {'changes':>10s}")
    print("─" * 70)

    py_enc, py_step, py_chg = bench_python(board, args.steps)
    rs_enc, rs_step, rs_chg = bench_rust(board, args.steps)

    print(f"{'python':10s}  {py_enc:12.2f}  {py_step:14.3f}  "
          f"{py_step * args.steps:16.2f}  {py_chg:10d}")
    print(f"{'rust':10s}  {rs_enc:12.2f}  {rs_step:14.3f}  "
          f"{rs_step * args.steps:16.2f}  {rs_chg:10d}")
    print()

    if py_chg != rs_chg:
        print(f"WARNING: change counts diverged ({py_chg} vs {rs_chg}) — "
              "engines are NOT producing the same evolution")
        return 1

    step_speedup = py_step / max(rs_step, 1e-6)
    encode_speedup = py_enc / max(rs_enc, 1e-6)
    print(f"step speedup:    {step_speedup:.2f}× "
          f"(rust is {step_speedup:.2f}× faster per step)")
    print(f"encode speedup:  {encode_speedup:.2f}×")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
