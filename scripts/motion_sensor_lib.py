"""motion_sensor_lib — CONSTRUCTED-GROUND-TRUTH stimuli for the motion sensor.

THE INSTRUMENT UNDER TEST is `domains.motion_group_world.vector_field` — the
SAD block-matcher that every motion number in this arc rests on. Two rungs
measured it wrong and neither gated it:

  * the motion rung (84000-84999) measured it ~11% WRONG PER BLOCK on a global
    pan whose answer is KNOWN AND UNIFORM, and recorded that it "BOUNDS EVERY
    COUNT in the rung";
  * the phi rung (86000-86999) predicted `(0,0)` for S>4 and measured `(0,4)`
    at S=5-7 -- right direction, wrong magnitude, "confidently wrong and
    INDISTINGUISHABLE DOWNSTREAM FROM A TRUE VECTOR (a sensor defect worth its
    own gate)".

THE GROUND TRUTH HERE IS BY CONSTRUCTION, NEVER SENSED (the recorded rule: a
diagnostic must not be computed by the component it checks). Every stimulus is
built by APPLYING a known displacement field to a synthesised texture, so the
true vector at every block is an input to the construction, not an output of
any estimator.

TOROIDAL BY DEFAULT, AND THAT IS LOAD-BEARING. Textures are synthesised in the
Fourier domain, so they are PERIODIC by construction; an integer `np.roll` is
then an EXACT rigid translation with NO border fabrication anywhere. The true
vector is therefore defined at EVERY block, including the edge blocks, which is
not true of a cropped pan. The bordered case is measured separately and its
border blocks are FLAGGED, never silently pooled.

SIGN CONVENTION, verified against the sensor's own arithmetic. `vector_field`
scores `a[i,j]` against `bp[r+dy+i, r+dx+j] == b[i+dy, j+dx]`, so the offset it
returns is the displacement of content FROM `a` TO `b`. To construct a true
displacement `(Dy, Dx)` we therefore need `b[k+Dy] == a[k]`, i.e.
`b = np.roll(a, (Dy, Dx))`. This is asserted in the gate's I1/I2 invariants
rather than trusted.

No substrate, no seeds drawn by this module -- callers pass their own rng.
"""
from __future__ import annotations

import numpy as np

# The arc's own sensor operating point, quoted not chosen: 72x72 fields with
# BLOCK = 4 are what the motion rung and the phi rung both measured.
GRID = 72
BLOCK = 4

# 8-bit quantisation is the sensor's real input domain (the phi rung's
# "below one 8-bit step" finding is a statement about this lattice).
LEVELS = 256


def texture(rng, size: int = GRID, beta: float = 1.0,
            contrast: float = 32.0, mean: float = 128.0):
    """A PERIODIC texture with a 1/f^beta power spectrum and a given contrast.

    Built in the Fourier domain, so it wraps EXACTLY -- which is what makes an
    integer `np.roll` an exact rigid translation with no border fabrication.

    `contrast` is the pre-quantisation standard deviation in 8-bit units, and
    it is the TEXTURE AXIS this rung sweeps: the motion rung found the flattest
    quartile 4x more error-prone on C1 and NO monotone relationship on C2, and
    that disagreement can only be resolved on a corpus where contrast is an
    INPUT rather than a measured property of found frames.

    `beta` is the spectral slope: 0 is white (all spatial frequencies equal),
    larger is smoother/blobbier. Natural images sit near 1-2.
    """
    w = rng.standard_normal((size, size))
    F = np.fft.fft2(w)
    fy = np.fft.fftfreq(size)[:, None]
    fx = np.fft.fftfreq(size)[None, :]
    f = np.sqrt(fy ** 2 + fx ** 2)
    f[0, 0] = 1.0                      # DC: leave the mean to `mean`
    amp = 1.0 / (f ** beta)
    amp[0, 0] = 0.0
    x = np.real(np.fft.ifft2(F * amp))
    sd = float(x.std())
    if sd > 0:
        x = x / sd
    return quantise(x * float(contrast) + float(mean))


def quantise(x):
    """8-bit lattice. The sensor's input is quantised; so is every stimulus."""
    return np.clip(np.round(np.asarray(x, dtype=np.float64)),
                   0.0, LEVELS - 1.0)


def pan(a, dy: int, dx: int):
    """EXACT rigid translation on the torus: `b[k + dy] == a[k]` everywhere.

    Returns `(b, true_field)` where `true_field[r, c] = (dy, dx)` for every
    block -- the whole point being that this is an INPUT, not an estimate."""
    b = np.roll(np.roll(a, int(dy), axis=0), int(dx), axis=1)
    return b, None                     # true field filled in by `true_uniform`


def true_uniform(shape_hw, block: int, dy: float, dx: float):
    nh, nw = shape_hw[0] // block, shape_hw[1] // block
    t = np.zeros((nh, nw, 2))
    t[..., 0] = float(dy)
    t[..., 1] = float(dx)
    return t


def multi_body(rng, size: int, block: int, vels, beta: float = 1.0,
               contrast: float = 32.0):
    """k rigid bodies, each translated by its OWN velocity.

    Each body owns a contiguous vertical band (a partition of the field), so
    the true vector at a block is the velocity of the band it lies in. Blocks
    that STRADDLE a band boundary have NO single true vector -- they are
    returned in `mixed` and are excluded from the primary rates rather than
    silently pooled, because "this block has two true answers" is a different
    fact from "the sensor was wrong".

    Bands are built by compositing SEPARATELY-ROLLED copies of one periodic
    texture, so within a band the translation is exact and the only
    non-rigidity is at the seams, which is exactly where `mixed` is set.
    """
    a = texture(rng, size, beta=beta, contrast=contrast)
    k = len(vels)
    edges = [round(i * size / k) for i in range(k + 1)]
    b = np.zeros_like(a)
    for i, (dy, dx) in enumerate(vels):
        rolled = np.roll(np.roll(a, int(dy), axis=0), int(dx), axis=1)
        b[:, edges[i]:edges[i + 1]] = rolled[:, edges[i]:edges[i + 1]]

    nh, nw = size // block, size // block
    t = np.zeros((nh, nw, 2))
    mixed = np.zeros((nh, nw), dtype=bool)
    for c in range(nw):
        lo, hi = c * block, (c + 1) * block
        owners = set()
        for x in range(lo, hi):
            for i in range(k):
                if edges[i] <= x < edges[i + 1]:
                    owners.add(i)
        if len(owners) == 1:
            i = owners.pop()
            t[:, c, 0], t[:, c, 1] = float(vels[i][0]), float(vels[i][1])
        else:
            mixed[:, c] = True
            i = min(owners)
            t[:, c, 0], t[:, c, 1] = float(vels[i][0]), float(vels[i][1])
    return a, b, t, mixed


def rotation(rng, size: int, block: int, degrees: float,
             beta: float = 1.0, contrast: float = 32.0):
    """Rotation about the field centre.

    A rotation is NOT a translation, and this module refuses to pretend it is.
    The true vector at a block is defined as the displacement of the block's
    CENTRE under the exact rotation, and `deform` records the maximum deviation
    (in pixels) of any pixel in that block from that single translation. A
    block with `deform > 0.5` is NOT well-approximated by any single vector and
    is reported separately -- the sensor is not wrong there, the model of "one
    vector per block" is.

    `b` is built by INVERSE-mapping with nearest-neighbour sampling, so no
    interpolation smoothing is introduced that would flatter the matcher.
    """
    a = texture(rng, size, beta=beta, contrast=contrast)
    th = np.deg2rad(float(degrees))
    ct, st = np.cos(th), np.sin(th)
    cy = cx = (size - 1) / 2.0
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    # forward map: p -> R(p - c) + c. b(F(p)) = a(p)  =>  b(q) = a(F^-1(q)).
    qy, qx = yy - cy, xx - cx
    sy = ct * qy + st * qx + cy
    sx = -st * qy + ct * qx + cx
    si = np.clip(np.round(sy), 0, size - 1).astype(int)
    sj = np.clip(np.round(sx), 0, size - 1).astype(int)
    b = a[si, sj]

    nh, nw = size // block, size // block
    t = np.zeros((nh, nw, 2))
    deform = np.zeros((nh, nw))
    for r in range(nh):
        for c in range(nw):
            py = r * block + (block - 1) / 2.0
            px = c * block + (block - 1) / 2.0
            fy = ct * (py - cy) - st * (px - cx) + cy
            fx = st * (py - cy) + ct * (px - cx) + cx
            t[r, c] = (fy - py, fx - px)
            d = 0.0
            for iy in range(r * block, (r + 1) * block):
                for ix in range(c * block, (c + 1) * block):
                    gy = ct * (iy - cy) - st * (ix - cx) + cy
                    gx = st * (iy - cy) + ct * (ix - cx) + cx
                    d = max(d, abs((gy - iy) - t[r, c, 0]),
                            abs((gx - ix) - t[r, c, 1]))
            deform[r, c] = d
    return a, b, t, deform


# --- the independent ambiguity oracle ---------------------------------------

def true_offset_is_unique_minimum(a, b, block: int, radius: int, t):
    """Is the TRUE offset the UNIQUE SAD minimiser inside the search window?

    SECONDARY, AND DECLARED AS SUCH. This shares the SAD objective with the
    sensor, so it is NOT independent evidence about the sensor's arithmetic --
    it is a decomposition of the error into

      * STIMULUS AMBIGUITY: the true answer is not recoverable from the data
        under this objective (the aperture problem), versus
      * SENSOR DEFECT: it was recoverable and the sensor missed it.

    What makes it usable at all is that it is GROUND-TRUTH-CONDITIONAL: it asks
    a question about the KNOWN `t`, which the sensor has no access to. The
    PRIMARY ground truth (`t` itself) remains purely constructional.

    Returns a boolean array over blocks.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    H, W = a.shape
    nh, nw = H // block, W // block
    r = int(radius)

    def blocks(x):
        return (x[:nh * block, :nw * block]
                .reshape(nh, block, nw, block).transpose(0, 2, 1, 3))

    A = blocks(a)
    bp = np.pad(b, r, mode="edge")
    keys = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)]
    stack = np.empty((len(keys), nh, nw))
    for i, (dy, dx) in enumerate(keys):
        sh = bp[r + dy:r + dy + H, r + dx:r + dx + W]
        stack[i] = np.abs(A - blocks(sh)).sum(axis=(2, 3))

    best = stack.min(axis=0)
    ties = (stack == best[None, :, :]).sum(axis=0)

    ty = np.rint(t[..., 0]).astype(int)
    tx = np.rint(t[..., 1]).astype(int)
    inside = (np.abs(ty) <= r) & (np.abs(tx) <= r)
    idx = np.clip((ty + r) * (2 * r + 1) + (tx + r), 0, len(keys) - 1)
    here = np.take_along_axis(stack, idx[None, :, :], axis=0)[0]
    # true offset OUTSIDE the aperture is never resolvable, by definition
    return inside & (here == best) & (ties == 1)


# --- classification ----------------------------------------------------------

def classify(v, t, tol: float):
    """The THREE outcomes, partitioned by DOWNSTREAM CONSEQUENCE.

    On blocks where motion EXISTS (`t != 0`) the three are exhaustive and
    mutually exclusive:

      silent_miss       v == (0,0)                 -- reports NO motion where
                                                      motion exists. This is
                                                      the phi rung's
                                                      `n_nonzero = 0`.
      confidently_wrong v != (0,0) and err > tol   -- a WELL-FORMED vector that
                                                      is WRONG, and that is
                                                      INDISTINGUISHABLE
                                                      DOWNSTREAM from a true
                                                      one. This is the phi
                                                      rung's `(0,4)`, and it is
                                                      the class nobody counted.
      correct           v != (0,0) and err <= tol

    SILENT MISS IS TESTED FIRST AND UNCONDITIONALLY, ahead of the tolerance.
    That is deliberate: at a large tolerance a small true motion reported as
    (0,0) would score as "correct", but downstream it is not a slightly-wrong
    vector, it is the ABSENCE of a vector -- a cell that cannot join any
    common-fate group at all. The count of silent misses that would ALSO have
    passed the tolerance is reported separately as a disclosure.

    On blocks where motion does NOT exist (`t == 0`) there is a fourth:

      false_motion      v != (0,0)                 -- motion invented from a
                                                      static scene.
    """
    v = np.asarray(v, dtype=np.float64)
    t = np.asarray(t, dtype=np.float64)
    err = np.linalg.norm(v - t, axis=-1)
    # EXACT zero, no epsilon. Both `v` and `t` are INTEGER displacements stored
    # as float64 -- the sensor emits integer offsets and the construction
    # supplies integer truth -- so exact equality is correct AND strictly
    # stronger than any epsilon. (The in-frame-is-INTEGER invariant: a float
    # tolerance here would be a category error, and an epsilon written in would
    # have been a §13 number with nothing to fall out of.)
    v_zero = (v == 0.0).all(axis=-1)
    t_zero = (t == 0.0).all(axis=-1)
    return {
        "err": err,
        "moving": ~t_zero,
        "static": t_zero,
        "silent_miss": (~t_zero) & v_zero,
        "confidently_wrong": (~t_zero) & (~v_zero) & (err > tol),
        "correct": (~t_zero) & (~v_zero) & (err <= tol),
        "false_motion": t_zero & (~v_zero),
        "silent_miss_within_tol": (~t_zero) & v_zero & (err <= tol),
    }


def otsu_split(values):
    """OTSU'S SPLIT over the OBSERVED values -- §13, and the motion rung's own
    precedent (it derived its grouping tolerance exactly this way, "2.402 on
    C2, 0.0 on C1, both EMERGENT").

    No binning: the observed error magnitudes are a DISCRETE set (norms of
    integer vector differences), so the candidate thresholds are the observed
    values themselves and there is no bin-count to choose. The threshold that
    comes back is fixed by the data's own two-class structure, not by any
    number written here.

    Returns 0.0 on a degenerate (single-valued) distribution -- which is the
    honest answer, and is what the motion rung read on C1.
    """
    v = np.asarray(values, dtype=np.float64).ravel()
    v = v[np.isfinite(v)]
    if v.size == 0:
        return 0.0
    levels, counts = np.unique(v, return_counts=True)
    if levels.size < 2:
        return 0.0
    w = counts.astype(np.float64) / counts.sum()
    cw = np.cumsum(w)
    cm = np.cumsum(w * levels)
    total = cm[-1]
    best_t, best_var = float(levels[0]), -1.0
    for i in range(levels.size - 1):
        w0 = cw[i]
        w1 = 1.0 - w0
        if w0 <= 0 or w1 <= 0:
            continue
        m0 = cm[i] / w0
        m1 = (total - cm[i]) / w1
        between = w0 * w1 * (m0 - m1) ** 2
        if between > best_var:
            best_var, best_t = between, float(levels[i])
    return best_t


def wilson(k: int, n: int, z: float = 1.959963984540054):
    """Wilson score interval. `z` is the 95% normal quantile -- a property of
    the Gaussian, not a tuned parameter."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def mean_ci(xs):
    """Seed-level mean with a normal-approximation 95% CI. THE UNIT IS THE
    SEED (§4): blocks inside one field share input and are not independent."""
    x = np.asarray(xs, dtype=np.float64)
    n = x.size
    if n == 0:
        return (0.0, 0.0, 0.0)
    m = float(x.mean())
    if n < 2:
        return (m, m, m)
    se = float(x.std(ddof=1)) / np.sqrt(n)
    z = 1.959963984540054
    return (m, m - z * se, m + z * se)
