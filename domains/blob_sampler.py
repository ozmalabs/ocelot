"""BLOB-NATIVE SAMPLING — the world adapter's pixel->sample seam.

`VISION_BLOB_NATIVE_PREREG.md`, committed at `df0156a4` before any headline.

This module is INPUT CONSTRUCTION and nothing else: mechanical pixel->tuple
translation before anything reaches the graph, the same admissible class as
quantizing a frame or building a translation orbit (CLAUDE.md). It reads no
graph state and takes no branch on one.

WHAT IT REPLACES. The incumbent percept is a RASTER partitioned into a square
grid of named regions (`verdict_comparator_world.REGION=6`, `GRID=24`,
`region_origins`) -- a 4x4 lattice of 6x6 squares, the most uniform grid
available. That contradicts two principles already recorded in this project
(*no uniform grid*; *grounding radiates outward and decays with eccentricity*),
and it got built because numpy slices rectangles.

THE DENSITY PROFILE FALLS OUT (PROTOCOL section 13). It is derived from a stated
principle, and the derivation is fixed in the pre-registration BEFORE this code
so it cannot be fitted:

  * PRINCIPLE: grounding decays with eccentricity, and the sampling limit is one
    pixel (in-frame is INTEGER -- stepping IS what grounding is).
  * SELF-SIMILARITY: a blob at eccentricity e has radius r(e) = e/kappa, a
    constant fraction of its own eccentricity. This is the ONLY scale-free
    choice; any other exponent introduces a preferred scale, which the principle
    forbids.
  * ISOTROPY (radial spacing == tangential spacing) then FORCES both laws:
      - radial:     e_{n+1} = e_n + 2 r(e_n) = e_n (1 + 2/kappa)  [geometric]
      - tangential: N_theta = 2 pi e_n / (2 r(e_n)) = pi kappa     [constant]
    Nothing here is chosen. Given self-similarity + isotropy, the geometric ring
    spacing and the constant per-ring count are consequences.
  * BOUNDARY: r(e_1) = 1 pixel (the sampling limit) => e_1 = kappa. The outer
    limit is the field radius R.

That leaves EXACTLY ONE constant, kappa, and it is NOT FREE: it is consumed by
the matched-sample-count constraint the gates already require (the blob arm must
carry the same number of samples as the square arm at the same field size).
`solve_kappa` SOLVES that constraint; it does not tune it. There is no
per-corpus and no per-resolution adjustment, and no cost table entered this
derivation -- the profile would be unchanged had the cost measurements said the
opposite.

NO FIXED-WIDTH NAME EXISTS HERE. A blob is identified by its INTEGER INDEX, and
the signature is `["blob", i, "v<q>"]`. The r143->14 defect class (a 2-digit name
field that silently mis-parsed at >=100 entries, and an answer parse that
required exactly 3 characters so every 3-digit answer read as None) is gone BY
CONSTRUCTION, not patched: there is no name string to overflow.
"""
from __future__ import annotations

import math

import numpy as np

#: The sampling limit, in pixels. NOT a tuning knob: it is the statement that a
#: frame's coordinates are the integer lattice, so nothing finer than one pixel
#: can be grounded. It is the derivation's boundary condition r(e_1) = 1.
PIXEL_LIMIT = 1.0


def ring_eccentricities(kappa: float, R: float) -> list[float]:
    """The geometric ring ladder e_n = kappa * (1 + 2/kappa)^(n-1), truncated at
    the field radius R. A consequence of self-similarity + isotropy, not a
    choice."""
    if kappa <= 0.0:
        return []
    out, e, growth = [], float(kappa), 1.0 + 2.0 / kappa
    while e <= R:
        out.append(e)
        e *= growth
    return out


def blobs_per_ring(kappa: float) -> int:
    """N_theta = pi * kappa, constant across rings. Stepped to the integer
    lattice (you cannot place a fractional blob); at least one."""
    return max(1, int(math.floor(math.pi * kappa + 0.5)))


def layout_count(kappa: float, R: float) -> int:
    """How many blobs the profile yields at this kappa -- one foveal blob at the
    origin plus N_theta per ring."""
    return 1 + blobs_per_ring(kappa) * len(ring_eccentricities(kappa, R))


def solve_kappa(R: float, target: int) -> float:
    """SOLVE the matched-count constraint for kappa. Not a tune: `target` is
    fixed by the comparison (the square arm's sample count at the same field
    size), and kappa is whatever satisfies it.

    Scans a dense grid of kappa and returns the one whose layout count is
    closest to `target`, breaking ties toward the SMALLER kappa (more rings,
    finer foveal sampling) so the rule is deterministic and stated rather than
    incidental."""
    best_k, best_err, best_n = None, None, None
    k = 0.25
    while k <= max(4.0 * R, 64.0):
        n = layout_count(k, R)
        err = abs(n - target)
        if best_err is None or err < best_err:
            best_k, best_err, best_n = k, err, n
        k += 0.25
    return float(best_k)


def blob_layout(R: float, target: int) -> list[tuple[float, float, float]]:
    """The blob field for a circular aperture of radius R carrying ~`target`
    blobs: a list of `(dy, dx, radius)` in FIELD-CENTRED continuous coordinates.

    Positions are IRREGULAR (log-polar, not a lattice), support is CIRCULAR and
    OVERLAPPING (radius r at spacing 2r with a truncated-Gaussian weight, so
    neighbouring supports touch and are not a tiling), and both SIZE and DENSITY
    vary with eccentricity by the derived law.

    Continuous coordinates are correct here: this is the MAP from image to
    percept, and non-integer math is CROSS-FRAME. What the map emits is stepped
    back onto the integer lattice (`sample_blobs`)."""
    kappa = solve_kappa(R, target)
    # The foveal blob sits AT the sampling limit -- that is the boundary
    # condition r(e_1)=1 evaluated at e=0, not a separate choice.
    out: list[tuple[float, float, float]] = [(0.0, 0.0, PIXEL_LIMIT)]
    n_theta = blobs_per_ring(kappa)
    for i, e in enumerate(ring_eccentricities(kappa, R)):
        r = max(PIXEL_LIMIT, e / kappa)
        # Stagger alternate rings by half a step: consecutive rings must not
        # share a spoke, or the layout re-acquires a preferred axis -- exactly
        # the uniformity the principle forbids. A half-step is the only offset
        # that treats both neighbours alike.
        phase = (math.pi / n_theta) * (i % 2)
        for j in range(n_theta):
            th = 2.0 * math.pi * j / n_theta + phase
            out.append((e * math.sin(th), e * math.cos(th), r))
    return out


def sample_blobs(frame, layout, *, k: int, centre=None) -> list[int]:
    """Sample `frame` at every blob, returning ONE INTEGER PER BLOB.

    The weighted mean is computed in the MAP (continuous -- a cross-frame
    quantity, which is where real-valued math belongs) and immediately STEPPED
    onto the integer lattice by the same uniform k-level quantization the square
    arm uses. Continuous in the map, integer in the frame.

    A blob whose support falls entirely outside the frame contributes its
    nearest in-frame pixel rather than a guarded 0.0: an absence produced by a
    guarded division is evidence of a lookup, not a measurement (PROTOCOL 1.1).
    """
    a = np.asarray(frame, float)
    h, w = a.shape
    cy, cx = ((h - 1) / 2.0, (w - 1) / 2.0) if centre is None else centre
    out = []
    for dy, dx, r in layout:
        by, bx = cy + dy, cx + dx
        r0, r1 = int(math.floor(by - r)), int(math.ceil(by + r))
        c0, c1 = int(math.floor(bx - r)), int(math.ceil(bx + r))
        num = den = 0.0
        for rr in range(max(0, r0), min(h, r1 + 1)):
            for cc in range(max(0, c0), min(w, c1 + 1)):
                d2 = (rr - by) ** 2 + (cc - bx) ** 2
                if d2 > r * r:
                    continue
                # Truncated Gaussian at sigma = r/2: support is circular and
                # OVERLAPS its neighbours (weight is non-zero to the rim), so
                # the blobs are not a tiling.
                wgt = math.exp(-2.0 * d2 / (r * r))
                num += wgt * a[rr, cc]
                den += wgt
        if den <= 0.0:
            ry = min(max(int(math.floor(by + 0.5)), 0), h - 1)
            rx = min(max(int(math.floor(bx + 0.5)), 0), w - 1)
            val = float(a[ry, rx])
        else:
            val = num / den
        out.append(int(min(max(int(val / 256.0 * k), 0), k - 1)))
    return out


def sig_of_blobs(vals) -> list[list]:
    """A blob group as its complete relation system.

    The identity is the blob's INTEGER INDEX -- there is no name string, so
    there is no fixed-width field to overflow at >= 100 entries."""
    return [["blob", int(i), f"v{int(v)}"] for i, v in enumerate(vals)]


def group_blobs(layout, n_groups: int, per_group: int) -> list[list[int]]:
    """Partition blob INDICES into `n_groups` contiguous groups of `per_group`.

    Order is ring-major (the layout's own construction order: fovea outward,
    then by angle within a ring), so a group is a spatially contiguous arc. This
    is the blob analogue of a square tile, and it is what the representation
    implies rather than what numpy makes convenient.

    Raises rather than returning a short partition: a short group would be
    scored against a full one and could not win an argmax, which is the same
    silent-selection-bias failure the truncated-aperture guard exists to kill."""
    need = n_groups * per_group
    if len(layout) < need:
        raise ValueError(
            f"blob layout has {len(layout)} blobs, need {need} for "
            f"{n_groups} groups of {per_group}. A short group cannot win an "
            f"argmax against a full one -- this is a SELECTION bias, not only "
            f"a count error.")
    return [list(range(g * per_group, (g + 1) * per_group))
            for g in range(n_groups)]


def eccentricity_profile(layout) -> dict:
    """Descriptive read-out of a layout: what the derived law actually produced.
    Pure query, for the bounds section of the results."""
    if not layout:
        return {"n": 0}
    ecc = [math.hypot(dy, dx) for dy, dx, _r in layout]
    rad = [r for _dy, _dx, r in layout]
    return {"n": len(layout),
            "ecc_min": min(ecc), "ecc_max": max(ecc),
            "r_min": min(rad), "r_max": max(rad),
            "r_mean": sum(rad) / len(rad),
            "n_rings": len({round(e, 6) for e in ecc}) - 1}


__all__ = ["PIXEL_LIMIT", "ring_eccentricities", "blobs_per_ring",
           "layout_count", "solve_kappa", "blob_layout", "sample_blobs",
           "sig_of_blobs", "group_blobs", "eccentricity_profile"]
