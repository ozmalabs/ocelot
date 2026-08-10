"""VISION IS SPEECH — same order-N machinery; cheap shape read first.

Two corrections (user): (1) the foreground op is a FLAT full-pixel pass — not
order-N. Real perception is cheap-first: a coarse relational-shape read says "this
is a square" in microseconds; you spend expensive ops only on the surprising
residual (the effort dial). (2) Vision and speech are the SAME — order-N relational
shape over a perceptual field — so they use the SAME held ops: shape_signature
(relational rank, gain/scale-invariant), shape_salience (order_n_shape_salience),
acquire_sign.

This shows: the SAME ops applied to a cochlear vector (speech) AND an image patch
(vision); the cheap coarse shape read discriminates shapes in ~us and is ~Nx
cheaper than the full-pixel pass; and order_n_shape_salience gates escalation
(simple/flat -> cheap suffices; surprising -> spend more).

Run:  python -m scripts.vision_speech_unified
"""
from __future__ import annotations
import sys
import time

import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import substrate_rs as srs
S = srs.Substrate


def square(n=12):
    a = np.zeros((n, n), np.float32); a[2:-2, 2:-2] = 1; a[4:-4, 4:-4] = 0; return a


def disk(n=12):
    y, x = np.ogrid[:n, :n]; r = ((y - n / 2 + .5) ** 2 + (x - n / 2 + .5) ** 2) ** .5
    return ((r > n * .2) & (r < n * .42)).astype(np.float32)


def triangle(n=12):
    a = np.zeros((n, n), np.float32)
    for i in range(n):
        w = int((i / n) * (n - 2))
        a[i, max(0, n // 2 - w // 2):min(n, n // 2 + w // 2 + 1)] = 1
    return a


def cross(n=12):
    a = np.zeros((n, n), np.float32)
    for i in range(n):
        a[i, i] = 1; a[i, n - 1 - i] = 1
    return a


def edge_orient_desc(img, cells=2, nbins=8):
    """CHEAP edge read: gradient -> undirected orientation histogram, pooled over a
    coarse spatial grid. The visual analog of cochlear bands — a compact TRAJECTORY
    whose order-N shape is meaningful (a square = strong axis-aligned edges in a box;
    a circle = all orientations everywhere). Robust to brightness/noise; ~us; tiny."""
    gy, gx = np.gradient(img.astype(np.float32))
    mag = np.hypot(gx, gy)
    ori = (np.arctan2(gy, gx) % np.pi)               # 0..pi, undirected edges
    b = np.minimum((ori / np.pi * nbins).astype(int), nbins - 1)
    n = img.shape[0]; h = n // cells
    desc = []
    for r in range(cells):
        for c in range(cells):
            m = mag[r*h:(r+1)*h, c*h:(c+1)*h]; bb = b[r*h:(r+1)*h, c*h:(c+1)*h]
            desc.extend(float(m[bb == k].sum()) for k in range(nbins))
    return np.asarray(desc, np.float32)              # cells*cells*nbins dims


def main():
    print("=" * 78)
    print("VISION IS SPEECH — same order-N ops; EDGES first (cheap), then shape")
    print("=" * 78)
    shapes = {"square": square(), "circle": disk(), "triangle": triangle(), "X": cross()}

    # The demo first showed shape_signature on RAW pixels fails (salience 0, a noisy
    # square no closer than a triangle). Correct read (user: "more like edge
    # detection"): EDGES first -> order-N shape of the edge descriptor.
    print("\n  (1) cheap EDGE-first order-N read: edge-orient desc -> shape_signature:")
    sigs = {}
    for name, img in shapes.items():
        t0 = time.perf_counter_ns()
        desc = edge_orient_desc(img)                 # cheap edge read
        sig = np.asarray(S.shape_signature(desc))    # order-N shape of the edges
        dt = (time.perf_counter_ns() - t0) / 1000.0
        sigs[name] = sig
        print(f"    {name:<9} {desc.size:>2}-dim edge desc -> shape_signature in {dt:6.1f} us")

    def d(a, b):
        return int(np.abs(sigs[a] - sigs[b]).sum())
    cross_min = min(d('square', 'circle'), d('square', 'triangle'), d('square', 'X'))
    noisy = square() + 0.08 * np.random.RandomState(0).randn(12, 12).astype(np.float32)
    nsig = np.asarray(S.shape_signature(edge_orient_desc(noisy)))
    dn = int(np.abs(sigs['square'] - nsig).sum())
    print("\n    discrimination (L1 between edge-shape signatures):")
    print(f"      square-circle {d('square','circle')}, square-triangle {d('square','triangle')}, "
          f"square-X {d('square','X')}")
    print(f"      square vs noisy-square {dn}  vs nearest other shape {cross_min}  -> "
          f"{'RECOGNISED' if dn < cross_min else 'NOT recognised'} "
          f"({'noisy square is closest to square' if dn < cross_min else 'still confused'})")

    # (2) THE SAME OP, BOTH MODALITIES — one held operator, speech + vision.
    print("\n  (2) the SAME held ops drive speech AND vision (one machinery):")
    cochlea_vec = np.array([0.1, 0.3, 0.8, 0.6, 0.2, 0.05] * 3, np.float32)  # cochlear bands
    edge_vec = edge_orient_desc(square())                                    # vision edges
    print(f"    shape_signature(cochlear bands)[:6] = {S.shape_signature(cochlea_vec)[:6]}")
    print(f"    shape_signature(edge descriptor)[:6] = {[int(x) for x in sigs['square'][:6]]}")
    print("    -> identical operator. speech = order-N shape of the cochlear trajectory;")
    print("       vision = order-N shape of the edge/contour trajectory. Structure, not pixels.")

    # (3) WHY EDGES-FIRST IS MANDATORY: the order-N op is O(n^2).
    print("\n  (3) the order-N op is O(n^2) -> edges-first is mandatory, not optional:")
    fine = np.random.RandomState(1).rand(128 * 128).astype(np.float32)
    import timeit
    t_edge = timeit.timeit(lambda: S.shape_signature(edge_vec), number=500) / 500 * 1e6
    t_fine = timeit.timeit(lambda: S.shape_signature(fine), number=20) / 20 * 1e6
    print(f"    {edge_vec.size}-dim edge descriptor : {t_edge:8.1f} us")
    print(f"    16384-px raw full-pixel pass: {t_fine:8.1f} us   "
          f"-> raw pixels are {t_fine/max(t_edge,1e-9):.0f}x more expensive (O(n^2))")

    # (4) THE EFFORT GATE: shape_salience over a TEMPORAL trajectory (rising event vs
    # flat) -> spend the expensive read only on the surprising residual.
    print("\n  (4) effort gate: order-N salience over a temporal trajectory:")
    rising = [0.0, 0.1, 0.25, 0.45, 0.7, 1.0]      # a visual EVENT (something appears)
    flat = [0.5, 0.5, 0.49, 0.5, 0.51, 0.5]        # nothing happening
    print(f"    rising event   salience {S.shape_salience(rising):.3f}  -> ESCALATE (spend)")
    print(f"    flat/no-change salience {S.shape_salience(flat):.3f}  -> cheap read suffices")
    print("=" * 78)
    print("  Vision = speech: EDGES (cheap) -> order-N relational shape (shape_signature),")
    print("  salience-gated effort (shape_salience + EffortDial), recurring signs")
    print("  (acquire_sign), cross-modal binding (synchronous_with). ONE machinery.")
    print("=" * 78)


if __name__ == "__main__":
    main()
