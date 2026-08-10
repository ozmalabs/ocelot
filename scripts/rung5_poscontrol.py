"""RUNG 5 — CONVERGENCE CHECK (PROTOCOL 2) + POSITIVE CONTROL (PROTOCOL 1).

The model's own simple Units have no orientation-selective RESPONSE (measured:
OSI ~0.002 vs an ideal Gabor's 0.758 through the identical probe), so no arm run
on them could mean anything. Before concluding, this asks the separable
question rung 3's positive control asked of its own null instrument:

    CAN the pooling rule produce a phase-invariant, orientation-tuned cell AT
    ALL, from inputs that ARE phase-sensitive?

The simple layer is replaced by a HAND-INSTALLED Gabor bank (4 orientations x 4
phases at one retinal centre) — a perfect stimulus for the rule. This is a
positive control, NOT an arm: the bank is hand-built and is exactly the kind of
structure the paradigm rule forbids handing the agent. It answers "is the rule a
null instrument?" and nothing else.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.complex_cells import (add_complex_layer, pool_weights, grating,
                                   binarize, present, cell_stats, gabor,
                                   install_weights, f1f0, osi, THETAS)

H = W = 16
RF = 7
PERIOD = 4.0          # the CALIBRATED probe: all 4 reference orientations tuned
                      # (OSI 0.80-1.00, F1/F0 1.28-1.49). period 3 ALIASES with the
                      # integer lattice at 0 deg (OSI 0.07); 6-7 exceed the RF envelope.
ORIS = [0.0, 45.0, 90.0, 135.0]
PHASES = [0.0, np.pi / 2, np.pi, 3 * np.pi / 2]


def build(seed: int, *, trace_delta: float, cx_eta: float):
    """A hand-installed Gabor bank + one CUnit pooling all of it."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_complex"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 0.0)          # the bank is FIXED: no simple-layer learning
    cp = s.nodes("ComplexParams")[0]
    s.set_attr(cp, "complex", 1.0)
    s.set_attr(cp, "trace_delta", float(trace_delta))
    s.set_attr(cp, "cx_eta", float(cx_eta))

    w = WaveWorld(s, h=H, w=W, seed=seed)
    centres = [(H // 2, W // 2)] * (len(ORIS) * len(PHASES))
    units = w.add_units(len(centres), rf=RF, centres=centres)
    labels = []
    for i, th in enumerate(ORIS):
        for j, ph in enumerate(PHASES):
            k = i * len(PHASES) + j
            install_weights(w, units[k], gabor(RF, th, ph, PERIOD))
            labels.append((th, ph))
    cus = add_complex_layer(w, [units], seed=seed)
    return w, units, cus[0], labels


class Trainer:
    """Drifting gratings: ORIENTATION is held for `dwell` steps while PHASE
    advances every step. That is the slowness structure the trace exploits —
    phase varies fast, orientation slowly. The orientation SEQUENCE is uniform
    random adapter entropy (no preferred orientation is handed to the agent).

    STATEFUL on purpose: the convergence check advances the SAME trainer in
    increments, so the input sequence CONTINUES rather than restarting. (A
    fresh rng per call replays the identical sequence, which makes every drift
    reading a measurement of a repeat, not of settling — found and fixed before
    the numbers were read.)"""

    def __init__(self, w, seed: int, dwell: int = 8):
        self.w, self.dwell = w, dwell
        self.rng = np.random.default_rng(seed + 4242)
        self.i = 0
        self.th = float(self.rng.choice(ORIS))

    def run(self, steps: int):
        for _ in range(steps):
            if self.i % self.dwell == 0:
                self.th = float(self.rng.choice(ORIS))
            ph = 2 * np.pi * (self.i % self.dwell) / self.dwell
            present(self.w, binarize(grating((H, W), self.th, ph, PERIOD)))
            self.i += 1


def structure(pw):
    """How CONCENTRATED the pooling is: 1 - normalised entropy of the weight
    distribution. 0 = uniform over all 16 inputs (no selection), 1 = one input."""
    p = np.abs(pw)
    if p.sum() <= 0:
        return 0.0
    p = p / p.sum()
    ent = -(p * np.log(p + 1e-12)).sum()
    return float(1.0 - ent / np.log(len(p)))


if __name__ == "__main__":
    print("=" * 74)
    print("PART 1 — CONVERGENCE (PROTOCOL 2): does cx_learn settle? Which eta?")
    print("=" * 74)
    for eta in (5e-4, 1e-4, 2e-5, 5e-6):
        w, units, cu, labels = build(0, trace_delta=0.2, cx_eta=eta)
        tr = Trainer(w, 0)
        prev = pool_weights(w, cu, units).copy()
        row = []
        for target in (400, 800, 1600, 3200, 6400):
            tr.run(target - (row[-1][0] if row else 0))
            pw = pool_weights(w, cu, units)
            drift = (np.linalg.norm(pw - prev) /
                     max(np.linalg.norm(pw), 1e-9))
            row.append((target, structure(pw), drift, int(np.isnan(pw).sum())))
            prev = pw.copy()
        print(f"\n  cx_eta={eta:g}")
        for t, st, dr, nan in row:
            print(f"    step {t:5d}: structure={st:.4f}  drift={dr:.4f}  NaN={nan}")

    print("\n  PART 2 (the positive control itself) lives in scripts/rung5_measure.py,")
    print("  which probes through a FROZEN world. It is NOT run here: `oja=0` is not a")
    print("  freeze (bh_* are gated on oja==0.0), so any probe run from this file before")
    print("  complex_cells.freeze() existed was training the thing it measured.")
