#!/usr/bin/env python3
"""THIS RUNG'S OWN SEED CONSUMPTION — the self-audit fixture (prereg §2, V1).

The audit tool is a static analyser and therefore draws NO seeds of its own.
That is exactly the vacuous case VISION_PROTOCOL.md §1.1 warns about: a tool
reporting zero everywhere and a clean tree LOOK IDENTICAL. So this rung spends
part of its own block deliberately, using the SAME three constructs that made
the resolution rung's consumption invisible to a substring scan, and then
audits ITSELF before auditing anyone else.

Declared block for this rung: 82000-82999.
Consumed here: 82000-82049 and 82300-82349 (see `draw_all`).

Nothing below contains the literal string "82049" or "82300"; recovering them
is the same problem the ledger audit has to solve.
"""
from __future__ import annotations

import random

import numpy as np

SEED_BLOCK = 82000
N_TRIALS = 50


def _inner(seed, t):
    """Interprocedural leg: `seed` arrives as an argument, never as a literal."""
    return np.random.RandomState(seed + 300 + t)


def draw_all():
    """Two scattered sub-ranges inside one declared block."""
    acc = []
    for t in range(N_TRIALS):
        rng = random.Random(SEED_BLOCK + t)          # 82000..82049
        acc.append(rng.random())
        r2 = _inner(SEED_BLOCK, t)                   # 82300..82349
        acc.append(float(r2.random_sample()))
    return acc


if __name__ == "__main__":
    vals = draw_all()
    print(f"{len(vals)} draws, mean={sum(vals) / len(vals):.6f}")
