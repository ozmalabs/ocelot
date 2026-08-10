#!/usr/bin/env python3
"""DEPTH — the RETINAL step (exploratory, run only after the synthetic passed).

Two distinguishable patterns drifting across the retina at DIFFERENT integer
velocities ARE a depth-from-motion scene (motion parallax): the near pattern
sweeps faster than the far one. We read each tick's ACTIVE cells (both patterns'
footprints, each carrying its own label in the val slot) as a frame signature
and ask DepthInfer whether latent:depth is minted, ordered by velocity, and
whether it predicts an unseen view. Controls: a FLAT retinal scene (both
patterns at ONE velocity) must mint NOTHING; a shuffled scene grounds.

Honest scope (PROTOCOL §11.4, and prereg P1): the two patterns are DISTINGUISHABLE
(a two-channel active-cell read — "two patterns"). Recovering the surfaces from
motion ALONE when appearance is uniform (unlabelled common-fate segmentation) is a
SEPARATE rung, exactly as the full center-surround event pipeline was for time.
This is the CHANGE/active-cell level; a moving blob under center-surround +
adaptation is not exact-integer-rigid and would ground at the exact-equality floor.

    PYTHONPATH=runners/dsl/python:. python scripts/depth_retina_probe.py
"""
from __future__ import annotations
import json, random
import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
FOOT = [(0, 0), (1, 0), (2, 0), (2, 1)]            # an L-tromino footprint


def render(H, W, patterns, k):
    """Active cells at tick k: each pattern = (label, origin, velocity)."""
    out = []
    for (label, (r0, c0), v) in patterns:
        rr, cc = r0 + v[0] * k, c0 + v[1] * k
        for (dr, dc) in FOOT:
            out.append(["on", int(rr + dr), int(cc + dc), label])
    return out


def scene(H, W, patterns, K):
    return [render(H, W, patterns, k) for k in range(K)]


def depth_infer(frames):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(frames[0]),
               "kind": "faculty", "faculty": "base", "dim_types": DT})

    def f(field):
        t = {"type": "DepthInfer", "sequence": {"type": "Lit", "value": frames},
             "codebook_type": "ShapeSignature", "max_b": 8, "field": field}
        return native.evaluate(t)
    return dict(explained=f("explained"), n_layers=f("n_layers"),
                velocities=f("velocities"), ordering=f("ordering"),
                window=f("window"), predicted=f("predicted"), reason=f("reason"))


print("ENGINE:", provenance_line())

# Two patterns, SAME coord region entry, DIFFERENT parallax velocities.
# Pattern 'a' (nearer) drifts faster than 'b' (farther).
print("\n--- MULTI-DEPTH retina: 'a' drift (3,0) [near], 'b' drift (1,0) [far] ---")
for vname, va, vb in [("a(3,0) b(1,0)", (3, 0), (1, 0)),
                      ("a(2,1) b(1,0)", (2, 1), (1, 0)),
                      ("a(0,3) b(0,1)", (0, 3), (0, 1))]:
    K = 6
    pats = [("a", (3, 3), va), ("b", (3, 10), vb)]
    frames = scene(30, 30, pats, K)
    r = depth_infer(frames)
    # downstream: predict the unseen view at tick K, compare
    withheld = sorted(tuple(x) for x in render(30, 30, pats, K))
    pred = sorted(tuple(x) for x in r["predicted"]) if r["predicted"] else None
    faster = "a" if sum(abs(x) for x in va) > sum(abs(x) for x in vb) else "b"
    near = r["ordering"][0][-1] if r["ordering"] else None
    print(f"  {vname:14} explained={r['explained']} n_layers={r['n_layers']} "
          f"near={near}(expect {faster}) predicts_unseen_view={pred == withheld}")

print("\n--- FLAT control: both patterns at ONE velocity (2,0) -> NO depth ---")
pats = [("a", (3, 3), (2, 0)), ("b", (3, 10), (2, 0))]
r = depth_infer(scene(30, 30, pats, 6))
print(f"  explained={r['explained']} status_reason={r['reason']} n_layers={r['n_layers']} "
      f"(a flat retinal scene must mint NOTHING)")

print("\n--- SHUFFLE control: multi-depth frames shuffled -> grounds (no depth) ---")
pats = [("a", (3, 3), (3, 0)), ("b", (3, 10), (1, 0))]
frames = scene(30, 30, pats, 8)
random.seed(27500); sh = [list(f) for f in frames]; random.shuffle(sh)
r = depth_infer(sh)
print(f"  explained={r['explained']} reason={r['reason']} (shuffled -> per-surface velocity not constant)")
