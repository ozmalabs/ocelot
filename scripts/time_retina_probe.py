#!/usr/bin/env python3
"""TIME — the RETINAL step (exploratory, run only after the synthetic passed).

A rigidly-translating pattern through the retina IS a motion orbit: at each
tick the retina's ACTIVE cells (the pattern's footprint) are the same shape,
displaced by the drift velocity. We read the active-cell set per tick as a
frame signature and ask TimeInfer whether the drift's transition generator is
inferred. Honest scope: this is the CHANGE/active-cell level (the pattern's
retinal footprint), not the full center-surround event pipeline — a moving
blob under center-surround + adaptation is NOT an exact integer-rigid
translation, which the exact-equality orbit test would ground at enumeration;
that integration is a separate rung (§11.4).

    PYTHONPATH=runners/dsl/python:. python scripts/time_retina_probe.py
"""
from __future__ import annotations
import json
import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]


def active_cells(grid: np.ndarray, thresh: float) -> list:
    """The retina's active-cell footprint: every above-threshold pixel as a
    ('on', r, c, '1') relation — the pattern's presence on the sheet."""
    out = []
    for r in range(grid.shape[0]):
        for c in range(grid.shape[1]):
            if grid[r, c] > thresh:
                out.append(["on", int(r), int(c), "1"])
    return out


def translating_stimulus(H, W, shape_rc, v, K):
    """K frames of a rigid pattern (`shape_rc` = list of (dr,dc) footprint
    offsets) translating by integer velocity `v=(vr,vc)` across an H×W sheet."""
    frames = []
    for k in range(K):
        g = np.zeros((H, W))
        r0, c0 = 3 + v[0] * k, 3 + v[1] * k
        for (dr, dc) in shape_rc:
            g[r0 + dr, c0 + dc] = 1.0
        frames.append(active_cells(g, 0.5))
    return frames


def time_infer(frames):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    # a held ShapeSignature only supplies dim_types (which slots are coords).
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(frames[0]),
               "kind": "faculty", "faculty": "base", "dim_types": DT})
    def f(field):
        t = {"type": "TimeInfer", "sequence": {"type": "Lit", "value": frames},
             "codebook_type": "ShapeSignature", "max_b": 8, "field": field}
        return native.evaluate(t)
    return f("explained"), f("kind"), f("offset"), f("matrix"), f("window"), f("predicted")


print("ENGINE:", provenance_line())
# an L-tromino footprint drifting DOWN-RIGHT by (1,2) per tick across a 30x30 retina
foot = [(0, 0), (1, 0), (2, 0), (2, 1)]
for name, v in [("drift(1,2)", (1, 2)), ("drift(2,0) horizontal", (2, 0)), ("drift(0,1) vertical", (0, 1))]:
    frames = translating_stimulus(30, 30, foot, v, 7)
    ex, kind, off, mat, win, pred = time_infer(frames)
    # downstream: predict the UNSEEN 8th frame (k=7) and compare to the actual
    withheld = active_cells(_g := (lambda: (lambda gg: (gg, [gg.__setitem__((3 + v[0]*7 + dr, 3 + v[1]*7 + dc), 1.0) for (dr, dc) in foot])[0])(np.zeros((30, 30))))(), 0.5)
    p = sorted([tuple(x) for x in pred]) if pred else None
    w = sorted([tuple(x) for x in withheld])
    print(f"  {name:22} explained={ex} kind={kind} offset={off} window={win} "
          f"downstream_predicts_unseen_frame={p == w}")

print("\n--- CONTROL: a SHUFFLED retinal drift is not an orbit ---")
import random
frames = translating_stimulus(30, 30, foot, (1, 2), 8)
random.seed(26500); sh = frames[:]; random.shuffle(sh)
ex, kind, off, mat, win, pred = time_infer(sh)
print(f"  shuffled drift        explained={ex} (grounds at enumeration)")
