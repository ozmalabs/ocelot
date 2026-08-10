"""ARC-AGI generate-and-select solver under the EXPLAINS-ALL-TRAIN-PAIRS certificate.

ARC-AGI-3 is INTERACTIVE/agentic (turn-based game environments, learn-by-playing,
no offline certificate) — NOT the jabberwock's home court. ARC-AGI-1/2 ARE the
static grid puzzles whose scoring IS an admissibility certificate: a candidate
grid->grid program is admissible IFF it reproduces EVERY train (input->output)
pair EXACTLY. That is the same generate-and-select-under-a-certificate engine as
the scalar `synthesize` (domains/generator.py): bottom-up, size-ordered
enumeration over a DSL grammar, keep the smallest program that fits ALL knowns,
commit on test ONLY when a program fits — else ABSTAIN (MISS). Zero false
positives where the certificate guarantees it: the only WRONG mode is a program
that fits all train pairs yet the held-out test differs (under-determined train).

This is the WORLD ADAPTER (mechanical I/O + enumeration). The "agent reasoning"
is the admissibility certificate, not Python conditionals over task content:
NO per-task hard-coding, NO peeking at the test output to fit. The recolor maps
are DERIVED from train pairs (a bijection that must be consistent across all
pairs), not hand-set per task.

Run (vmem-capped, timeout-guarded):
  ulimit -v 8388608
  PYTHONPATH=runners/dsl/python:. timeout 600 python3 scripts/arc_solver.py
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time
from itertools import product as iproduct
from typing import Callable

Grid = tuple[tuple[int, ...], ...]


# ===========================================================================
# Grid representation (immutable, hashable -> usable as observational-equiv key)
# ===========================================================================

def to_grid(rows) -> Grid:
    return tuple(tuple(int(c) for c in row) for row in rows)


def dims(g: Grid) -> tuple[int, int]:
    return (len(g), len(g[0]) if g else 0)


def colors(g: Grid) -> set[int]:
    return {c for row in g for c in row}


# ===========================================================================
# THE GRID DSL — grid->grid primitives. Each is a pure function Grid->Grid.
# The candidate PROGRAM space = these primitives + their compositions (size-N).
# ===========================================================================

def t_identity(g: Grid) -> Grid:
    return g


def t_rot90(g: Grid) -> Grid:
    return tuple(zip(*g[::-1]))


def t_rot180(g: Grid) -> Grid:
    return tuple(tuple(row[::-1]) for row in g[::-1])


def t_rot270(g: Grid) -> Grid:
    return tuple(zip(*g))[::-1]


def t_flip_h(g: Grid) -> Grid:        # mirror left-right
    return tuple(tuple(row[::-1]) for row in g)


def t_flip_v(g: Grid) -> Grid:        # mirror top-bottom
    return g[::-1]


def t_transpose(g: Grid) -> Grid:
    return tuple(zip(*g))


def t_anti_transpose(g: Grid) -> Grid:
    # transpose across the anti-diagonal = rot90 then flip_h
    flipped = tuple(tuple(row[::-1]) for row in g[::-1])  # rot180
    return tuple(zip(*flipped))


# --- geometric base ops (shape-preserving up to transpose) ---
GEOMETRIC: dict[str, Callable[[Grid], Grid]] = {
    "identity": t_identity,
    "rot90": t_rot90,
    "rot180": t_rot180,
    "rot270": t_rot270,
    "flip_h": t_flip_h,
    "flip_v": t_flip_v,
    "transpose": t_transpose,
    "anti_transpose": t_anti_transpose,
}


# --- gravity (move all non-background cells down/up/left/right, per column/row) ---
def _gravity(g: Grid, bg: int, axis: str) -> Grid:
    h, w = dims(g)
    out = [[bg] * w for _ in range(h)]
    if axis in ("down", "up"):
        for c in range(w):
            col = [g[r][c] for r in range(h) if g[r][c] != bg]
            if axis == "down":
                for i, v in enumerate(reversed(col)):
                    out[h - 1 - i][c] = v
            else:
                for i, v in enumerate(col):
                    out[i][c] = v
    else:
        for r in range(h):
            row = [v for v in g[r] if v != bg]
            if axis == "right":
                for i, v in enumerate(reversed(row)):
                    out[r][w - 1 - i] = v
            else:
                for i, v in enumerate(row):
                    out[r][i] = v
    return to_grid(out)


# ===========================================================================
# DERIVED (train-fitted) primitives — NOT hard-coded per task. Each is INDUCED
# from the train pairs under a consistency requirement; if the induction is
# inconsistent across pairs it yields NO primitive (returns None). This is the
# admissibility certificate applied to the primitive itself.
# ===========================================================================

def induce_recolor(train: list[tuple[Grid, Grid]]) -> Callable | None:
    """A per-cell color bijection consistent across ALL train pairs and shape-
    preserving. Returns a Grid->Grid that applies the learned color map, or None
    if no single consistent cellwise map explains every pair."""
    mapping: dict[int, int] = {}
    for gi, go in train:
        if dims(gi) != dims(go):
            return None
        for ri in range(len(gi)):
            for ci in range(len(gi[0])):
                a, b = gi[ri][ci], go[ri][ci]
                if a in mapping:
                    if mapping[a] != b:
                        return None  # inconsistent -> not a cellwise recolor
                else:
                    mapping[a] = b
    def apply(g: Grid) -> Grid:
        return to_grid([[mapping.get(c, c) for c in row] for row in g])
    return apply


def induce_bg(train: list[tuple[Grid, Grid]]) -> int:
    """Most common color across train inputs = background (for gravity etc.)."""
    cnt: dict[int, int] = {}
    for gi, _ in train:
        for row in gi:
            for c in row:
                cnt[c] = cnt.get(c, 0) + 1
    return max(cnt, key=cnt.get) if cnt else 0


# ===========================================================================
# THE PROGRAM SPACE. A program is a tuple of named ops applied left-to-right.
# Size = number of ops. Bottom-up by size; observational-equivalence pruning
# on the (tuple of per-train-input outputs) signature collapses equivalent
# programs (the same trick `synthesize` uses on scalar signatures).
# ===========================================================================

def build_op_pool(train: list[tuple[Grid, Grid]]):
    """The admissible op set for this task: geometric ops always; derived ops
    only when their induction succeeds (consistent across train)."""
    pool: dict[str, Callable[[Grid], Grid]] = dict(GEOMETRIC)
    rec = induce_recolor(train)
    if rec is not None:
        pool["recolor*"] = rec
    bg = induce_bg(train)
    for axis in ("down", "up", "left", "right"):
        pool[f"gravity_{axis}"] = (lambda axis: lambda g: _gravity(g, bg, axis))(axis)
    return pool


def apply_program(prog: tuple[str, ...], pool, g: Grid) -> Grid | None:
    cur = g
    for name in prog:
        try:
            cur = to_grid(pool[name](cur))
        except Exception:
            return None
    return cur


def program_signature(prog, pool, inputs) -> tuple | None:
    sig = []
    for g in inputs:
        out = apply_program(prog, pool, g)
        if out is None:
            return None
        sig.append(out)
    return tuple(sig)


def solve_task(task: dict, max_size: int = 3, timeout_s: float = 8.0):
    """Generate-and-select. Returns dict with the certified program (or None),
    the test predictions, and stats. ABSTAINS (program=None) when no program of
    size<=max_size reproduces ALL train outputs."""
    t0 = time.time()
    train = [(to_grid(p["input"]), to_grid(p["output"])) for p in task["train"]]
    train_in = [gi for gi, _ in train]
    train_out = tuple(go for _, go in train)

    pool = build_op_pool(train)
    op_names = list(pool.keys())

    # Bottom-up enumeration by size with observational-equivalence pruning.
    by_size: dict[int, list[tuple]] = {0: [()]}     # size 0 = identity program
    seen: set = set()                                # signatures already realised
    # size-0 signature
    s0 = program_signature((), pool, train_in)
    if s0 is not None:
        seen.add(s0)
        if s0 == train_out:
            return _result((), pool, task, t0, "solved")

    explored = 1
    for size in range(1, max_size + 1):
        if time.time() - t0 > timeout_s:
            return _result(None, pool, task, t0, "timeout", explored)
        cur: list[tuple] = []
        for base in by_size[size - 1]:
            for name in op_names:
                if time.time() - t0 > timeout_s:
                    return _result(None, pool, task, t0, "timeout", explored)
                prog = base + (name,)
                sig = program_signature(prog, pool, train_in)
                explored += 1
                if sig is None:
                    continue
                if sig in seen:
                    continue          # observationally equivalent -> prune
                # CERTIFICATE: reproduces every train output exactly?
                if sig == train_out:
                    return _result(prog, pool, task, t0, "solved", explored)
                seen.add(sig)
                cur.append(prog)
        by_size[size] = cur
        if not cur:                   # saturated: no new behaviours reachable
            break
    return _result(None, pool, task, t0, "abstain", explored)


def _result(prog, pool, task, t0, status, explored=0):
    preds = None
    if prog is not None:
        preds = []
        for p in task["test"]:
            preds.append(apply_program(prog, pool, to_grid(p["input"])))
    return {
        "program": prog,
        "status": "solved" if prog is not None else status,
        "preds": preds,
        "explored": explored,
        "elapsed_s": round(time.time() - t0, 3),
    }


# ===========================================================================
# Harness — run over a batch, score honestly: SOLVED / ABSTAINED / WRONG.
# WRONG := certificate satisfied on train but test prediction differs (the only
# possible WRONG mode; under-determined train). report it loudly.
# ===========================================================================

def run_batch(files, max_size=3, timeout_s=8.0, verbose=False):
    n = solved = abstained = wrong = certified = 0
    wrong_tasks = []
    solved_tasks = []
    t0 = time.time()
    for f in files:
        task = json.load(open(f))
        if not task.get("test") or task["test"][0].get("output") is None:
            continue                  # eval set may hide test outputs; skip score
        n += 1
        r = solve_task(task, max_size=max_size, timeout_s=timeout_s)
        if r["program"] is None:
            abstained += 1
            if verbose:
                print(f"  ABSTAIN  {os.path.basename(f)} ({r['status']}, "
                      f"explored={r['explored']}, {r['elapsed_s']}s)")
            continue
        certified += 1               # program fit ALL train pairs
        # check test predictions against held-out truth (NOT used to fit)
        ok = True
        for p, pred in zip(task["test"], r["preds"]):
            if pred != to_grid(p["output"]):
                ok = False
                break
        if ok:
            solved += 1
            solved_tasks.append((os.path.basename(f), r["program"]))
            if verbose:
                print(f"  SOLVED   {os.path.basename(f)}  prog={r['program']}")
        else:
            wrong += 1
            wrong_tasks.append((os.path.basename(f), r["program"]))
            print(f"  WRONG*   {os.path.basename(f)}  prog={r['program']} "
                  f"(fit all train, test differs)")
    return {
        "n": n, "solved": solved, "abstained": abstained, "wrong": wrong,
        "certified": certified, "elapsed_s": round(time.time() - t0, 1),
        "wrong_tasks": wrong_tasks, "solved_tasks": solved_tasks,
    }


def main():
    base = "/tmp/arc_data/ARC-AGI/data"
    which = sys.argv[1] if len(sys.argv) > 1 else "training"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    max_size = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    files = sorted(glob.glob(os.path.join(base, which, "*.json")))[:limit]

    print(f"ARC-AGI {which}: {len(files)} tasks, max_program_size={max_size}")
    print("DSL ops: geometric(8) + induced recolor* + gravity(4)")
    print("certificate: program reproduces ALL train pairs exactly\n")

    res = run_batch(files, max_size=max_size, timeout_s=8.0, verbose=False)
    print("\n" + "=" * 62)
    print(f"  scored tasks : {res['n']}")
    print(f"  CERTIFIED    : {res['certified']}  (program fit all train pairs)")
    print(f"  SOLVED       : {res['solved']}   (test output exactly correct)")
    print(f"  ABSTAINED    : {res['abstained']} (no program fit all train -> MISS)")
    print(f"  WRONG        : {res['wrong']}   (fit all train, test differs)")
    if res["n"]:
        print(f"  solve rate   : {100*res['solved']/res['n']:.1f}% of scored")
        if res["certified"]:
            print(f"  precision    : {100*res['solved']/res['certified']:.1f}% "
                  f"of certified (1 - false-positive rate)")
    print(f"  wall time    : {res['elapsed_s']}s")
    if res["solved_tasks"]:
        print("\n  sample solved programs:")
        for name, prog in res["solved_tasks"][:12]:
            print(f"    {name}: {prog}")


if __name__ == "__main__":
    main()
