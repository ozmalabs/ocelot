"""rung7_lib — RUNG 7's measurement harness. Mechanical: build, run, read.

PROTOCOL §10: the engine is pinned by preamble (both ROOT and
`runners/dsl/python`) and every result this library produces is expected to be
reported alongside `provenance_line()`.

THE STATISTICS, and why they are shaped the way they are
--------------------------------------------------------
**THE REAL GATE — the SHAPE departure `SD`.** Rung 6's diagnosis is that
`x_OFF = 1 - x_ON` forces `C_ON,OFF(d) = -C_ON,ON(d)` IDENTICALLY. A naive
"is C_ON,OFF(d) != -C_ON,ON(d)?" test would be passed by ANY non-affine relation
between the channels — including a pure pointwise rectification change with no
spatial structure whatever. That is not what Miller (1994) needs. Miller needs
the two correlation functions to have **DIFFERENT SPATIAL DEPENDENCE**. So the
statistic is deliberately SCALE- and SIGN-INVARIANT:

    rho = Pearson correlation, across d = 1..DMAX, of C_ON,OFF(d) vs C_ON,ON(d)
    SD  = 1 - rho^2

    degenerate (rung 6)         : C_ON,OFF = -C_ON,ON exactly => rho = -1 => SD = 0
    independent spatial structure: SD > 0

`SD` is the fraction of the ON/OFF correlation function's spatial variation that
is NOT explained by ANY affine image of the ON/ON one. A sign flip cannot pass
it. A rescaling cannot pass it. **Its floor is ANALYTIC (exactly 0), not
empirical** — which is the strongest kind of floor this ladder has had, and the
direct answer to PROTOCOL §1's "run the measure on random input".

`d = 0` is EXCLUDED and this is load-bearing: at zero distance the two channels
are the two rectified halves of ONE residual, so `Corr(x_ON(i), x_OFF(i))` is
driven by the rectification nonlinearity alone, carrying no spatial information.
Including it would let a pointwise nonlinearity pass a test about space.

**MILLER'S OWN READING — the space constants.** Reported alongside `SD` because
it is what Miller 1994 actually varies: the distance at which each correlation
function falls to half its d=1 value (`sigma_ON,ON` vs `sigma_ON,OFF`). Equal
space constants = degenerate; different = the precondition holds. Interpretable
where `SD` is only diagnostic.

**CENTRE-SURROUND: `CS`.** A single lit pixel at offset (dr,dc), response read
off the RESIDUAL field (the signed FILTER — rung 6 established that the filter
and the rectified RESPONSE are different objects, and the RF is a property of
the filter). Because `h_k` is a MEAN over the ring, a lit pixel in ring k
contributes `-g_k/n_k`, so summing the whole ring gives exactly `-g_k`:

    CS = -(sum of surround response) / (centre response) = g1 + g2

i.e. the centre-surround index IS the total learned surround gain — pure centre
(`g=0`) scores 0 by construction. The rectified surround SUPPRESSION is reported
too, since that is the observable a downstream cell actually receives.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.seed_registry  # noqa: F401,E402
from domains.lateral_world import (  # noqa: E402
    add_lateral_retina, channels, freeze_lateral, gains, install_gains,
    residuals, set_lat_params, thaw_lateral,
)
from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

H = W = 16
DMAX = 6            # the largest distance with enough cell pairs on a 16x16 grid


# --------------------------------------------------------------------------- #
#  BUILD / RUN
# --------------------------------------------------------------------------- #
def build(*, seed=0, lateral=1.0, learn_gain=1.0, radius2=1.0, eta=2e-3,
          gmax=2.0, g0=0.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)       # keep bh_* gated OFF (oja=0 is NOT a freeze)
    s.set_attr(wp, "oja_eta", 0.0)   # ... and oja_learn an identity
    w = WaveWorld(s, h=H, w=W, seed=seed)
    anat = add_lateral_retina(w)
    set_lat_params(w, lateral=lateral, learn_gain=learn_gain, radius2=radius2,
                   lat_eta=eta, lat_gmax=gmax, lat_g0=g0, frozen=0.0)
    if g0:
        install_gains(w, anat["hcells"], g0, g0)
    return w, anat


def run_waves(world, steps, *, ignite_every=5):
    """Advance the world on its OWN formative input — the agent's waves."""
    for i in range(steps):
        world.step(ignite_k=1 if i % ignite_every == 0 else 0)


def record_channels(world, anat, steps, *, ignite_every=5):
    """Run the world on its own waves; return the (steps, h, w) ON/OFF movies."""
    on_m, off_m = [], []
    for i in range(steps):
        world.step(ignite_k=1 if i % ignite_every == 0 else 0)
        on, off = channels(world, anat["bipolars"])
        on_m.append(on.copy())
        off_m.append(off.copy())
    return np.stack(on_m), np.stack(off_m)


def _corrupt_frame(f, p, kind, rng):
    """Corrupt a binary frame at level `p`. THE SNR AXIS, and ONLY that.

    **`kind="balanced"` (the instrument, DENSITY-PRESERVING).** An ON cell turns
    OFF with probability `p`; an OFF cell turns ON with probability
    `p*m/(1-m)`, where `m` is the frame's own mean. That choice makes
    `E[mean(f')] = mean(f)` exactly, so the corruption degrades the SIGNAL while
    holding the field's DENSITY fixed.

    **`kind="flip"` (the naive version, KEPT because it is a measured negative).**
    A symmetric flip at rate `p`. On a SPARSE binary field this is NOT a pure SNR
    knob: mean activity moves from `m` to `m + p(1-2m)`, i.e. 0.13 -> 0.28 at
    p=0.2. It therefore varies DENSITY and SNR together — two mechanisms on one
    knob, PROTOCOL §4's confound. The rung-7 pilot measured exactly this: it
    reproduced Atick & Redlich's BROADENING monotonically (g2 share
    0.340 -> 0.490) while the predicted WEAKENING inverted (total 0.759 -> 0.797),
    because the denser field raises `Cov(h,c)` faster than the noise raises
    `Var(h)`. The failure was the INSTRUMENT's, not the mechanism's, and it is
    recorded rather than deleted.

    The theory the balanced instrument is meant to test: for independent noise,
    `Cov(h',c')` is attenuated by a factor common to both rings while
    `Var(h'_k)` gains `sigma^2/n_k`, so
        g*_k = (1-a-b)^2 Cov(h,c) / [ (1-a-b)^2 Var(h) + sigma^2/n_k ]
    which WEAKENS with noise (both rings) and shifts share toward the ring with
    the LARGER `n_k` (the far one) — Atick & Redlich's two predictions, from one
    regression.
    """
    if p <= 0.0:
        return f
    if kind == "flip":
        return np.where(rng.random(f.shape) < p, 1.0 - f, f)
    m = float(f.mean())
    if m <= 1e-9 or m >= 1.0 - 1e-9:
        return f
    b = min(1.0, p * m / (1.0 - m))
    on = f > 0.5
    r = rng.random(f.shape)
    out = f.copy()
    out[on & (r < p)] = 0.0
    out[(~on) & (r < b)] = 1.0
    return out


def replay_noisy(world, anat, movie, *, noise=0.0, rng=None, record=False,
                 noise_kind="balanced"):
    """**ATICK & REDLICH'S CONTROL: THE SAME VIDEO AT TWO LUMINANCES.**

    Replay a PRE-RECORDED burst movie, corrupting each cell independently with
    probability `noise` BEFORE the rules see the field, then tick ONCE.

    THE BUG THIS EXISTS TO AVOID, found in the first cut and worth recording:
    corrupting *after* `world.step()` meant the rules had ALREADY run to
    fixpoint on the CLEAN field, and clearing the phase guards to re-run them
    made `lat_learn_gain` fire TWICE per step — once on clean input and once on
    noisy. The "noise level" arm would have differed from control in the number
    of learning events as well as in SNR: two mechanisms, one knob, exactly the
    confound PROTOCOL §4 warns about ("adding a mechanism can silently
    invalidate your control"). Setting the field ONCE, then ticking ONCE,
    guarantees one learning event per step at every noise level.

    Replaying a recorded movie (the `WaveWorld.replay_step` precedent, built for
    the temporal-shuffle control) is also what makes this Atick & Redlich's
    actual experiment rather than an analogue of it: **the stimulus is held
    byte-identical across arms and ONLY the SNR moves.** Two arms driven by two
    independently-generated wave sequences would differ in their stimulus too.

    The noise is UNSTRUCTURED (independent per cell per frame, no spatial or
    temporal correlation) — the adapter's one licensed contribution (PROTOCOL
    §0), the same entropy `WaveWorld.ignite` already supplies. It is the
    photoreceptor-noise / low-light analogue: what the surround DOES about it is
    entirely the rules' business.
    """
    rng = rng or np.random.default_rng(12345)
    on_m, off_m = [], []
    for frame in movie:
        st = float(world.s.node(world.retina)["attrs"]["step"]) + 1.0
        world.s.set_attr(world.retina, "step", st)
        f = _corrupt_frame(frame, noise, noise_kind, rng)
        for (r, c), n in world.cells.items():
            on = float(f[r, c]) > 0.5
            world.s.set_attr(n, "bursting", 1.0 if on else 0.0)
            world.s.set_attr(n, "last_burst", st if on else -999.0)
        world.s.tick(200_000)
        if record:
            o, of = channels(world, anat["bipolars"])
            on_m.append(o.copy())
            off_m.append(of.copy())
    if record:
        return np.stack(on_m), np.stack(off_m)
    return None


# --------------------------------------------------------------------------- #
#  THE CORRELATION FUNCTIONS  (pure numpy over recorded movies)
# --------------------------------------------------------------------------- #
def _zscore(M):
    """(T, h, w) -> (N, T) z-scored per cell. Cells with no variance are
    dropped: a silent channel has no correlation function, and pretending it
    has one (by 0/0 -> nan -> 0) would fabricate structure."""
    T = M.shape[0]
    X = M.reshape(T, -1).T.astype(np.float64)     # (N, T)
    sd = X.std(axis=1)
    live = sd > 1e-9
    Z = np.zeros_like(X)
    Z[live] = (X[live] - X[live].mean(axis=1, keepdims=True)) / sd[live, None]
    return Z, live


def corr_by_distance(A, B, *, dmax=DMAX, h=H, w=W):
    """C_{A,B}(d): mean over cell pairs at Euclidean distance ~d of the
    time-correlation of A at one cell and B at the other.

    Returns `(ds, C)` for d = 1..dmax. Pairs are ORDERED (i != j), so
    C_{ON,OFF} is symmetrised over both directions exactly as C_{ON,ON} is —
    the two are then directly comparable, which the whole gate depends on.
    """
    ZA, liveA = _zscore(A)
    ZB, liveB = _zscore(B)
    T = A.shape[0]
    C = (ZA @ ZB.T) / T                            # (N, N) correlation matrix
    idx = np.arange(h * w)
    rr, cc = idx // w, idx % w
    D = np.sqrt((rr[:, None] - rr[None, :]) ** 2 + (cc[:, None] - cc[None, :]) ** 2)
    Dr = np.rint(D).astype(int)
    ok = liveA[:, None] & liveB[None, :]
    ds, out = [], []
    for d in range(1, dmax + 1):
        m = (Dr == d) & ok
        if m.sum() < 8:
            continue
        ds.append(d)
        out.append(float(C[m].mean()))
    return np.array(ds), np.array(out)


def shape_departure(C_on_on, C_on_off):
    """**THE REAL GATE.** SD = 1 - rho^2, rho = Pearson(C_ON,OFF, C_ON,ON) over d>=1.

    Degenerate (C_ON,OFF = -C_ON,ON exactly) => rho = -1 => SD = 0, ANALYTICALLY.
    Scale- and sign-invariant by construction, so it measures the SHAPE of the
    spatial dependence and cannot be passed by a rectification change.
    """
    a = np.asarray(C_on_on, float)
    b = np.asarray(C_on_off, float)
    # UNDEFINED, NOT ZERO — and the distinction is load-bearing. With `g = 0`
    # the OFF channel is SILENT (resid = c >= 0), so every OFF cell has zero
    # variance, `corr_by_distance` returns an EMPTY array, and `C_ON,OFF(d)`
    # simply DOES NOT EXIST. Reporting `SD = 0` there would be a lie of exactly
    # the kind this ladder keeps retracting: it would read as "maximally
    # degenerate" when the truth is "there is no second channel to be
    # degenerate WITH". `nan` propagates and forces the reader to say which.
    if a.size < 3 or b.size < 3 or a.size != b.size:
        return float("nan")
    if a.std() < 1e-12 or b.std() < 1e-12:
        return float("nan")
    rho = float(np.corrcoef(a, b)[0, 1])
    return 1.0 - rho ** 2


def space_constant(ds, C):
    """MILLER'S OWN READING: the distance at which |C(d)| falls to half its
    |C(d=1)| value, by linear interpolation. `inf` if it never does within the
    measured range (a flat correlation function has no space constant)."""
    a = np.abs(np.asarray(C, float))
    if a.size == 0 or a[0] < 1e-12:
        return float("nan")
    half = a[0] / 2.0
    for i in range(1, len(a)):
        if a[i] <= half:
            x0, x1, y0, y1 = ds[i - 1], ds[i], a[i - 1], a[i]
            if abs(y1 - y0) < 1e-12:
                return float(x1)
            return float(x0 + (y0 - half) * (x1 - x0) / (y0 - y1))
    return float("inf")


# --------------------------------------------------------------------------- #
#  CENTRE-SURROUND: the effective RF, probed one pixel at a time
# --------------------------------------------------------------------------- #
def effective_rf(world, anat, *, centre=(8, 8), radius=2):
    """The effective RF of ONE horizontal cell: response of its RESIDUAL to a
    single lit pixel at each offset. FROZEN throughout (rung 5/6's lesson: a
    probe that lets the layer learn is the instrument training itself).

    Read off the residual — the signed FILTER. Rung 6 established that the
    filter and the rectified RESPONSE are different objects and that the RF is a
    property of the filter (`the split makes the FILTER signed; the THRESHOLD
    makes the RESPONSE signed`). `surround_suppression` reports the response
    side.
    """
    freeze_lateral(world)
    cy, cx = centre
    hc = anat["hcells"][(cy, cx)]
    n = 2 * radius + 1
    rf = np.zeros((n, n), np.float64)
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            tgt = world.cells.get((cy + dr, cx + dc))
            if tgt is None:
                continue
            rf[dr + radius, dc + radius] = _probe_pixel(world, tgt, hc)
    return rf


def _probe_pixel(world, lit_cell, hcell):
    """Present a single lit pixel; return the HCell's residual. Mechanical."""
    st = float(world.s.node(world.retina)["attrs"]["step"]) + 1.0
    world.s.set_attr(world.retina, "step", st)
    for n in world.cells.values():
        world.s.set_attr(n, "state", "rested")
        world.s.set_attr(n, "bursting", 0.0)
        world.s.set_attr(n, "last_burst", -999.0)
    world.s.set_attr(lit_cell, "bursting", 1.0)
    world.s.set_attr(lit_cell, "last_burst", st)
    world.s.tick(200_000)
    return float(world.s.node(hcell)["attrs"]["resid"])


def cs_index(rf, *, radius=2):
    """CS = -(sum of surround) / centre.

    Because each `h_k` is a MEAN over its ring, a lit pixel in ring k
    contributes exactly `-g_k/n_k`, so the ring sums to `-g_k` and
    **CS = g1 + g2**: the centre-surround index IS the total learned surround
    gain. Pure centre (g=0) => 0, by construction, not by measurement luck.
    """
    c = rf[radius, radius]
    if abs(c) < 1e-12:
        return float("nan")
    return float(-(rf.sum() - c) / c)


def surround_suppression(world, anat, *, centre=(8, 8)):
    """THE RESPONSE-SIDE reading: how much a surround annulus suppresses the ON
    channel's response to a lit centre. `1 - (centre+surround)/(centre alone)`.

    Reported alongside `cs_index` because the rectified response is what a
    downstream cell actually receives, and rung 6's whole finding was that the
    filter and the response can disagree completely (OSI 0.0006 vs 0.9115 on
    identical weights).
    """
    freeze_lateral(world)
    cy, cx = centre
    hc = anat["hcells"][(cy, cx)]
    alone = _probe_set(world, [(cy, cx)], hc)
    ring = [(cy + dr, cx + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
    both = _probe_set(world, [(cy, cx)] + ring, hc)
    a = max(alone, 0.0)
    b = max(both, 0.0)
    if a < 1e-12:
        return float("nan")
    return float(1.0 - b / a)


def _probe_set(world, lit, hcell):
    st = float(world.s.node(world.retina)["attrs"]["step"]) + 1.0
    world.s.set_attr(world.retina, "step", st)
    for n in world.cells.values():
        world.s.set_attr(n, "state", "rested")
        world.s.set_attr(n, "bursting", 0.0)
        world.s.set_attr(n, "last_burst", -999.0)
    for rc in lit:
        cell = world.cells.get(rc)
        if cell is not None:
            world.s.set_attr(cell, "bursting", 1.0)
            world.s.set_attr(cell, "last_burst", st)
    world.s.tick(200_000)
    return float(world.s.node(hcell)["attrs"]["resid"])


# --------------------------------------------------------------------------- #
#  THE RUNG-6 REFERENCE: the degenerate complementary split, same frames
# --------------------------------------------------------------------------- #
def complementary_channels(on_movie):
    """Rung 6's split applied to the SAME recorded field: x_OFF = 1 - x_ON.

    The analytic floor of the whole rung, computed rather than assumed — if this
    does not score SD = 0 to numerical precision, the instrument is wrong and no
    other number in the rung means anything.
    """
    return on_movie, 1.0 - on_movie


def raw_burst_movie(world, steps, *, ignite_every=5):
    """The RetinaCell burst field over `steps` — the input BOTH the rung-6
    reference and the rung-7 layer are computed from."""
    out = []
    for i in range(steps):
        world.step(ignite_k=1 if i % ignite_every == 0 else 0)
        a = np.zeros((world.h, world.w), np.float32)
        for (r, c), n in world.cells.items():
            a[r, c] = float(world.s.node(n)["attrs"]["bursting"])
        out.append(a)
    return np.stack(out)


__all__ = [
    "H", "W", "DMAX", "build", "run_waves", "record_channels", "corr_by_distance",
    "shape_departure", "space_constant", "effective_rf", "cs_index",
    "surround_suppression", "complementary_channels", "raw_burst_movie",
    "gains", "residuals", "channels", "freeze_lateral", "thaw_lateral",
    "set_lat_params", "install_gains", "add_lateral_retina",
]
