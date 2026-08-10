#!/usr/bin/env python3
"""STEREO — the RETINAL step (exploratory, run only after the synthetic passed).

The stereo twin of `depth_retina_probe.py`: two distinguishable patterns at
DIFFERENT disparities across a 30x30 retina, viewed by N EYE hubs at baselines
0..N-1 AT ONE INSTANT. Each eye's view = each pattern shifted by baseline*disparity
(near = large disparity, shifts more per eye). We read each eye's ACTIVE cells as a
frame signature and ask the UNCHANGED DepthInfer whether latent:depth is minted,
ordered by disparity (near first), and whether it predicts an UNSEEN EYE's view.
Controls: a scene at ONE depth (uniform disparity) must mint NOTHING; an eye-order
shuffle grounds. The eye count is Count(Eye hubs) — demonstrated at N=2 and N=3.

Honest scope (PROTOCOL §11.4): the two patterns are DISTINGUISHABLE (a two-channel
active-cell read). Recovering surfaces from disparity ALONE when appearance is
uniform (unlabelled correspondence) is a SEPARATE rung, exactly as it was for the
motion-depth retina. This is the labelled active-cell level.

    PYTHONPATH=runners/dsl/python:. python scripts/stereo_retina_probe.py
"""
from __future__ import annotations
import json, random

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
FOOT = [(0, 0), (1, 0), (2, 0), (2, 1)]            # an L-tromino footprint


def eye_view(patterns, baseline):
    """One eye's retinal image: each pattern = (label, origin, disparity),
    shifted by baseline*disparity along the column (disparity) axis."""
    out = []
    for (label, (r0, c0), disp) in patterns:
        cc = c0 - disp * baseline
        for (dr, dc) in FOOT:
            out.append(["on", int(r0 + dr), int(cc + dc), label])
    return out


def eye_hubs(s, n):
    for b in range(n):
        s.add_node("Eye", {"baseline": float(b)})


def views_from_graph(s, patterns):
    """One frame per Eye hub in the graph, ordered by baseline. Count from graph."""
    eyes = sorted(int(s.node(e)["attrs"]["baseline"]) for e in s.nodes("Eye"))
    return [eye_view(patterns, b) for b in eyes], len(eyes)


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


def build(n_eyes, patterns):
    s, ag = boot_core()
    eye_hubs(s, n_eyes)
    frames, count = views_from_graph(s, patterns)
    return frames, count


print("ENGINE:", provenance_line())

# Two patterns at DIFFERENT disparities. 'a' (nearer) larger disparity than 'b'.
print("\n--- MULTI-DEPTH retina, N EYES at one instant: 'a' disp 3 [near], 'b' disp 1 [far] ---")
for N in (2, 3):
    pats = [("a", (3, 3), 3), ("b", (3, 12), 1)]
    frames, count = build(N, pats)
    r = depth_infer(frames)
    # downstream: predict the UNSEEN eye at baseline N (one beyond the last)
    withheld = sorted(tuple(x) for x in eye_view(pats, N))
    pred = sorted(tuple(x) for x in r["predicted"]) if r["predicted"] else None
    near = r["ordering"][0][-1] if r["ordering"] else None
    print(f"  N={N} eyes_from_graph={count} explained={r['explained']} n_layers={r['n_layers']} "
          f"near={near}(expect a) predicts_unseen_eye={pred == withheld}")

print("\n--- SINGLE-DEPTH control: both patterns at ONE disparity (2) -> NO depth ---")
pats = [("a", (3, 3), 2), ("b", (3, 12), 2)]
frames, count = build(3, pats)
r = depth_infer(frames)
print(f"  eyes_from_graph={count} explained={r['explained']} reason={r['reason']} "
      f"n_layers={r['n_layers']} (a single-depth retinal scene must mint NOTHING)")

print("\n--- EYE-ORDER SHUFFLE control: multi-depth eye-frames shuffled -> grounds ---")
pats = [("a", (3, 3), 3), ("b", (3, 12), 1)]
frames, count = build(8, pats)
random.seed(28500); sh = [list(f) for f in frames]; random.shuffle(sh)
r = depth_infer(sh)
print(f"  explained={r['explained']} reason={r['reason']} "
      f"(shuffled eye order -> per-surface disparity not constant)")
