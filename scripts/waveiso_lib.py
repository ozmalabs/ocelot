"""waveiso_lib — the WAVE-ISOTROPY instrument.

Measures whether the rung-1 wave ensemble carries ORIENTATION, by linear algebra
on the STIMULUS alone. No cortex, no learning rule, no probe.

§10.1 rule 3: `engine_preamble()` MUST run before any `domains.*` import — the
FIRST `substrate_rs` import binds the engine for the process, so a preamble that
runs afterwards is a no-op that LOOKS correct. It is called at module import,
before the `domains.wave_world` import below.

WHAT `x` IS, AND WHY IT IS NOT THE FRAME (§12.2). `oja_learn`'s x term is
    IfThenElse(Lte(Minus(r.step, c.last_burst), WaveParams.window_steps), 1, 0)
i.e. x_i(t) = 1 iff cell i burst within `window_steps` of t. `window_steps` is
2.0 in the committed `WaveParams` default — it is not a constant this instrument
chooses. Measuring the INSTANTANEOUS frame instead would rebuild §12.2's blind
zero-lag measure exactly: a travelling wave reaches a cell and its neighbour at
DIFFERENT times, and refractoriness makes them mutually exclusive at any instant,
so zero-lag reads ~0 for a PERFECT wave. We measure what the rule reads.

THE TRANSLATION-INVARIANCE IDENTITY, which is what makes this cheap and exact.
Oja unit j sees the 7x7 patch x_p at its RF centre p. Its second moment is
    M[a,b] = E_p[ x(p+d_a) x(p+d_b) ] = R(d_a - d_b)
under averaging over RF centres p — and the ensemble IS translation-invariant
(ignition is uniform over the grid, `wave_world.ignite`). So the 49x49 M is the
block-Toeplitz matrix built from the autocorrelation R(d), and R(d) also gives
C(d, theta) directly. ONE object answers all three questions.

THE CONSTANTS, and what each falls out of (§13):
  * `window_steps = 2` — read from the committed WaveParams node, not set here.
  * `rf = 7` — `add_units`' committed default; fixes the displacement range to
    |d| <= 3 (half = rf//2), i.e. exactly the displacements one Oja RF spans.
  * ring radii {1,2,3} — the non-zero |d| a 7x7 RF contains. Not a knob: it is
    the RF's own geometry.
  * ignite_k=1 / ignite_every=6 — `wave_world.record`'s committed defaults.
All other numbers are measured, not chosen.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# §10.1 RULE 3 — BEFORE any domains.* import. Do not move this below.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

import numpy as np  # noqa: E402

from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402


# ---------------------------------------------------------------- the world ---
def make_world(seed: int, h: int, w: int):
    """Boot a substrate with the wave seed and lay out an h x w retina.

    The `boot_core()` + `load_seeds_into` pattern is `scripts/rung4_convergence.py`'s
    verbatim — the rung-1/2/4 measurement precedent.
    """
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    return WaveWorld(s, h=h, w=w, seed=seed)


def record_bursting(world, *, steps: int, ignite_k: int = 1,
                    ignite_every: int = 6, burn_in: int = 0) -> np.ndarray:
    """Run the world and return the BURSTING movie (steps, h, w) as float32.

    `bursting` is what the learning rules read (`_mark_bursts`). Mechanical
    read-back, no decision. `burn_in` steps are run and DISCARDED before
    recording, so the ensemble is not dominated by the empty initial grid.
    """
    out = []
    ids = world._cell_ids
    rc = world._cell_rc
    total = burn_in + steps
    for i in range(total):
        k = ignite_k if (ignite_every and i % ignite_every == 0) else 0
        world.step(ignite_k=k)
        if i < burn_in:
            continue
        b = world.s.get_attr_many(ids, "bursting")
        a = np.zeros((world.h, world.w), np.float32)
        for (r, c), v in zip(rc, b):
            if v == 1.0:
                a[r, c] = 1.0
        out.append(a)
    return np.stack(out)


def read_last_burst(world) -> np.ndarray:
    """The cells' `last_burst` attribute, as an (h, w) array. Pure query —
    used to VERIFY the windowed x against the rule's own term."""
    a = np.zeros((world.h, world.w), np.float32)
    vals = world.s.get_attr_many(world._cell_ids, "last_burst")
    for (r, c), v in zip(world._cell_rc, vals):
        a[r, c] = float(v)
    return a


def window_movie(burst: np.ndarray, window_steps: int) -> np.ndarray:
    """x_i(t) = 1 iff cell i burst within `window_steps` of t.

    Exactly `oja_learn`'s x term: (t - last_burst) <= window_steps is the OR of
    the bursting movie over the last (window_steps + 1) frames. Frames before
    the window is full are dropped, so every returned frame has a full history.
    """
    T = burst.shape[0]
    k = int(window_steps)
    out = np.zeros_like(burst)
    for t in range(T):
        lo = max(0, t - k)
        out[t] = burst[lo:t + 1].max(axis=0)
    return out[k:]


# ------------------------------------------------- the autocorrelation R(d) ---
def frame_autocorr(frame: np.ndarray, half: int) -> np.ndarray:
    """Per-frame UNNORMALISED autocorrelation R_t(d) for |dy|,|dx| <= half.

    Circular (FFT) autocorrelation with the grid's own periodicity. Returns a
    (2*half+1, 2*half+1) array indexed [dy+half, dx+half], each entry the mean
    over positions q of x(q) x(q+d).
    """
    F = np.fft.rfft2(frame)
    ac = np.fft.irfft2(F * np.conj(F), s=frame.shape)
    n = frame.size
    ac = ac / n
    out = np.zeros((2 * half + 1, 2 * half + 1), np.float64)
    for dy in range(-half, half + 1):
        for dx in range(-half, half + 1):
            out[dy + half, dx + half] = ac[dy % frame.shape[0], dx % frame.shape[1]]
    return out


def movie_autocorr(movie: np.ndarray, half: int):
    """Return (R_mean, R_per_frame, mu).

    R_mean = E_t[R_t(d)] is the ensemble second moment E[x(q) x(q+d)].
    mu     = E[x] over the whole movie.
    """
    per = np.stack([frame_autocorr(f, half) for f in movie])
    return per.mean(axis=0), per, float(movie.mean())


def centre_slice(R: np.ndarray, half: int) -> np.ndarray:
    """The |d| <= half centre block of a wider R.

    R must be computed out to rf-1 (= 6 for rf=7), because the second moment
    needs R(d_a - d_b) and the extreme RF offsets differ by 6. The harmonics
    need only |d| <= 3 (the RF's half-width), so they read this centre block.
    """
    Rh = (R.shape[0] - 1) // 2
    return R[Rh - half:Rh + half + 1, Rh - half:Rh + half + 1]


def corr_from_R(R: np.ndarray, mu: float) -> np.ndarray:
    """Pearson correlation rho(d) from the second moment R(d) and mean mu.

    x is BINARY, so Var(x) = mu(1-mu) exactly and
        rho(d) = (R(d) - mu^2) / (mu - mu^2).
    Guarded: a dead (mu=0) or saturated (mu=1) movie has no correlation defined.
    Returns NaN there rather than a fake 0.0 — §1.1's lesson: an absence off a
    guarded division is evidence of a lookup, not a measurement. The caller
    must treat NaN as a FAILED ARM, never as a floor.
    """
    var = mu - mu * mu
    if var <= 1e-12:
        return np.full_like(R, np.nan)
    return (R - mu * mu) / var


# --------------------------------------------------- the anisotropy indices ---
def _ring_mask(half: int, r: int):
    """Integer displacements with |d| in [r-0.5, r+0.5). Returns (dy, dx, theta)."""
    ys, xs = np.mgrid[-half:half + 1, -half:half + 1]
    rad = np.sqrt(ys ** 2 + xs ** 2)
    m = (rad >= r - 0.5) & (rad < r + 0.5)
    return ys[m], xs[m], np.arctan2(ys[m], xs[m])


def _rf_mask(half: int):
    """Every non-zero displacement a 7x7 RF contains: 0 < |d| <= half."""
    ys, xs = np.mgrid[-half:half + 1, -half:half + 1]
    rad = np.sqrt(ys ** 2 + xs ** 2)
    m = (rad > 0) & (rad <= half + 1e-9)
    return ys[m], xs[m], np.arctan2(ys[m], xs[m])


def radial_profile(rho: np.ndarray, half: int) -> dict:
    """rho averaged over each integer ring — C(d) with the angle averaged out.

    This is the Wong/Meister/Shatz correlation index's shape (PRIOR_ART §3.4:
    "if we match one thing, match C(d)"), restricted to the RF's displacements.
    """
    out = {}
    for r in range(1, half + 1):
        ys, xs, _ = _ring_mask(half, r)
        out[r] = float(np.mean(rho[ys + half, xs + half]))
    return out


def corr_length(rho: np.ndarray, half: int) -> float:
    """The waves' OWN half-height correlation length, in cells.

    The smallest r at which the ring-averaged rho has fallen below half its
    r=1 value; if it never does within the RF, the RF's half-width. Used to set
    the disk control's radius FROM THE WAVES' measured statistics rather than
    from a chosen number (§13).
    """
    prof = radial_profile(rho, half)
    base = prof.get(1, 0.0)
    if base <= 0:
        return float(half)
    for r in range(1, half + 1):
        if prof[r] < 0.5 * base:
            return float(r)
    return float(half)


def anisotropy(rho: np.ndarray, half: int, m: int, *, ring: int | None = None) -> float:
    """A_m = |sum_d rho(d) e^{i m theta_d}| / sum_d |rho(d)|, over the RF's
    displacements (or one ring).

    BOUNDED IN [0, 1] BY THE TRIANGLE INEQUALITY, deliberately. The obvious
    alternative (normalising by sum_d rho(d), a modulation depth) is an
    UNBOUNDED ratio that blows up as the mean correlation crosses zero — the
    `peak/base` disease that has already blown up in two independent rungs
    (§1.1's corollary). This one cannot.

    m=2 is the ORIENTATION harmonic (orientation is pi-periodic). m=4 is the
    4-fold harmonic, reported because the retina's `neighbour` edges are a
    4-NEIGHBOURHOOD on a square lattice: a diamond front is 4-fold symmetric,
    and a 4-fold-symmetric rho has A_2 = 0 IDENTICALLY (e^{2i(theta+pi/2)} =
    -e^{2i theta}, so the four lattice-equivalent displacements cancel in
    pairs). So A_2 alone CANNOT see a lattice diamond, and reporting A_4
    alongside it is what keeps that artifact visible instead of hidden (§13.1).
    """
    if ring is None:
        ys, xs, th = _rf_mask(half)
    else:
        ys, xs, th = _ring_mask(half, ring)
    v = rho[ys + half, xs + half]
    if not np.all(np.isfinite(v)):
        return float("nan")
    den = np.abs(v).sum()
    if den <= 1e-12:
        return float("nan")
    return float(np.abs((v * np.exp(1j * m * th)).sum()) / den)


def local_vs_global(per_R: np.ndarray, mu: float, half: int, m: int = 2):
    """(A_global, A_local) — the ensemble-frame vs per-frame anisotropy.

    A_global = |h_m(E_t[R_t])|   — the harmonic of the ENSEMBLE correlation.
    A_local  = E_t[|h_m(R_t)|]   — the mean MAGNITUDE of the per-frame harmonic.

    THE POINT: an ensemble of anisotropic frames with RANDOM orientations
    averages to an ISOTROPIC ensemble. The per-frame harmonic is a COMPLEX
    number whose PHASE is the frame's orientation; averaging the complex values
    cancels (A_global -> 0) while averaging their magnitudes does not
    (A_local > 0). A_local >> A_global therefore means "structure exists
    per-frame, destroyed by ensemble averaging" — which is a statement about
    what the RULE can use, not about what the stimulus contains.

    A_local is a MAGNITUDE and is therefore POSITIVELY BIASED by finite-sample
    noise: it does NOT go to 0 on white noise. Its floor MUST be read off the
    matched white-noise control, never assumed to be zero.
    """
    R_mean = per_R.mean(axis=0)
    A_glob = anisotropy(corr_from_R(centre_slice(R_mean, half), mu), half, m)
    vals = []
    Rh = (per_R.shape[1] - 1) // 2
    for R in per_R:
        # each frame's own mean, from its own R(0)
        mu_t = float(R[Rh, Rh])
        rho_t = corr_from_R(centre_slice(R, half), mu_t)
        a = anisotropy(rho_t, half, m)
        if np.isfinite(a):
            vals.append(a)
    A_loc = float(np.mean(vals)) if vals else float("nan")
    return A_glob, A_loc


# ------------------------------- the LOCAL WAVEFRONT frame (structure tensor) ---
def structure_tensor_coherence(movie: np.ndarray, rf: int = 7):
    """(coh_local, coh_global) — orientation coherence at the RF grain.

    THIS IS THE 'LOCAL WAVEFRONT FRAME' MEASURE, and the frame-level A_2 is NOT
    it. A_2 computed per FRAME is taken over the whole grid, which holds many
    independently-oriented wavefronts at once — so it cancels for exactly the
    same reason the ensemble does, and reads isotropic even if every individual
    front is perfectly oriented. To ask "does an INDIVIDUAL wave carry
    orientation" the window must be the size of the thing that reads it: ONE
    RECEPTIVE FIELD (rf=7, the committed default).

    The structure tensor is the standard instrument for exactly this, and it
    needs no estimate of where a wave's centre is: a front's local orientation
    IS the direction of its intensity gradient, so summing the gradient outer
    product over an rf x rf window aligns to that window's own front normal
    automatically.

        J = sum_window [ gx^2   gx*gy ]
                       [ gx*gy  gy^2  ]

    coherence = |(J_xx - J_yy, 2 J_xy)| / (J_xx + J_yy)
              = the SECOND ANGULAR HARMONIC of the local gradient distribution,
    which is the same currency as `anisotropy`'s A_2, bounded in [0,1] by the
    same triangle inequality. 1 = every gradient in the window shares one
    orientation (a straight front); 0 = gradients uniformly spread (a full ring,
    or scatter).

    coh_local  = E_window[ coherence ]      — per-RF, magnitudes averaged.
    coh_global = coherence of the SUMMED J  — the ensemble's own gradient
                 anisotropy, where opposite orientations cancel as vectors.

    coh_local is a MAGNITUDE and so is positively biased by noise; its floor
    must be read off the matched isotropic control, never assumed to be 0.
    """
    T, h, w = movie.shape
    Jxx = np.zeros((T, h, w))
    Jyy = np.zeros((T, h, w))
    Jxy = np.zeros((T, h, w))
    for t in range(T):
        gy, gx = np.gradient(movie[t].astype(np.float64))
        Jxx[t], Jyy[t], Jxy[t] = gx * gx, gy * gy, gx * gy

    def box(a):
        """Sum over an rf x rf window — the RF's own footprint."""
        c = np.cumsum(np.cumsum(a, axis=1), axis=2)
        c = np.pad(c, ((0, 0), (1, 0), (1, 0)))
        k = rf
        return (c[:, k:, k:] - c[:, :-k, k:] - c[:, k:, :-k] + c[:, :-k, :-k])

    Sxx, Syy, Sxy = box(Jxx), box(Jyy), box(Jxy)
    num = np.sqrt((Sxx - Syy) ** 2 + (2 * Sxy) ** 2)
    den = Sxx + Syy
    ok = den > 1e-9
    coh_local = float((num[ok] / den[ok]).mean()) if ok.any() else float("nan")
    # the ensemble: sum J over ALL windows, ALL frames, THEN take the harmonic
    gxx, gyy, gxy = Jxx.sum(), Jyy.sum(), Jxy.sum()
    coh_global = float(np.sqrt((gxx - gyy) ** 2 + (2 * gxy) ** 2) / (gxx + gyy)) \
        if (gxx + gyy) > 1e-12 else float("nan")
    return coh_local, coh_global


# ------------------------------------------------------- the eigen-analysis ---
def second_moment_matrix(R: np.ndarray, rf: int) -> np.ndarray:
    """The rf^2 x rf^2 second moment M[a,b] = R(d_a - d_b) an Oja unit sees.

    Block-Toeplitz by translation invariance (see module docstring).
    """
    half = rf // 2
    offs = [(dy, dx) for dy in range(-half, half + 1) for dx in range(-half, half + 1)]
    n = len(offs)
    M = np.zeros((n, n), np.float64)
    Rh = (R.shape[0] - 1) // 2
    for a, (ay, ax) in enumerate(offs):
        for b, (by, bx) in enumerate(offs):
            M[a, b] = R[(ay - by) + Rh, (ax - bx) + Rh]
    return M


def orientation_index(v: np.ndarray) -> float:
    """OI of an eigenvector, reshaped to its rf x rf patch: the 2nd angular
    harmonic of its 2D power spectrum, EXCLUDING DC.

        OI = |sum_{k!=0} P(k) e^{2i phi_k}| / sum_{k!=0} P(k)

    A grating at ONE orientation -> ~1. A rotationally symmetric blob -> ~0.
    Bounded in [0,1] by the same triangle inequality as `anisotropy`.
    """
    n = int(round(np.sqrt(v.size)))
    a = v.reshape(n, n)
    P = np.abs(np.fft.fft2(a)) ** 2
    ky = np.fft.fftfreq(n) * n
    kx = np.fft.fftfreq(n) * n
    KY, KX = np.meshgrid(ky, kx, indexing="ij")
    m = ~((KY == 0) & (KX == 0))
    phi = np.arctan2(KY[m], KX[m])
    p = P[m]
    if p.sum() <= 1e-12:
        return float("nan")
    return float(np.abs((p * np.exp(2j * phi)).sum()) / p.sum())


def dc_fraction(v: np.ndarray) -> float:
    """P(k=0) / sum P(k) — how much of the eigenvector is a constant blob."""
    n = int(round(np.sqrt(v.size)))
    P = np.abs(np.fft.fft2(v.reshape(n, n))) ** 2
    if P.sum() <= 1e-12:
        return float("nan")
    return float(P[0, 0] / P.sum())


def eigen_report(R: np.ndarray, mu: float, rf: int, *, centred: bool):
    """Eigen-decomposition of what Oja converges to.

    centred=False -> M = E[xx^T], the SECOND MOMENT. This is what Oja actually
        sees: the rule is `w <- w(1 - eta y^2) + eta y x` on the RAW non-negative
        x, with no mean subtraction anywhere in the seed. Its leading eigenvector
        is what the rule converges to.
    centred=True  -> Sigma = M - mu mu^T, the COVARIANCE. Reported alongside
        because DC dominance and orientation structure are different questions,
        and the arc has already been bitten once by a DC prior (`w0`, 431:1).

    Returns dict with eigenvalues, degeneracy, and the leading vector's OI/DC.
    """
    M = second_moment_matrix(R, rf)
    if centred:
        n = M.shape[0]
        M = M - mu * mu * np.ones((n, n))
    lam, vec = np.linalg.eigh(M)
    idx = np.argsort(lam)[::-1]
    lam = lam[idx]
    vec = vec[:, idx]
    lead = vec[:, 0]
    return {
        "eigenvalues": lam[:10].tolist(),
        # per-mode OI/DC: the leading vector is not the whole story — a
        # SUBDOMINANT oriented pair that is DEGENERATE is a different finding
        # from "no orientation exists", and only the per-mode read shows it.
        "eigvec_OI_top6": [orientation_index(vec[:, k]) for k in range(6)],
        "eigvec_DC_top6": [dc_fraction(vec[:, k]) for k in range(6)],
        "lambda1": float(lam[0]),
        "lambda2": float(lam[1]),
        "degeneracy_l1_over_l2": float(lam[0] / lam[1]) if abs(lam[1]) > 1e-12 else float("inf"),
        "var_explained_1": float(lam[0] / lam.sum()) if lam.sum() > 1e-12 else float("nan"),
        "leading_OI": orientation_index(lead),
        "leading_DC": dc_fraction(lead),
        "leading_vec": lead.tolist(),
    }


# ------------------------------------------------------ synthetic controls ---
def white_noise_movie(rng, T: int, h: int, w: int, p: float) -> np.ndarray:
    """ISOTROPIC control: iid Bernoulli(p). Density MATCHED to the waves, so the
    floor is comparable rather than merely small."""
    return (rng.random((T, h, w)) < p).astype(np.float32)


def disk_movie(rng, T: int, h: int, w: int, p: float, radius: float) -> np.ndarray:
    """ISOTROPIC-AND-CORRELATED control: randomly placed filled disks.

    THIS, NOT WHITE NOISE, IS THE HONEST FLOOR FOR A_m — measured, not assumed.
    White noise has rho(d) ~= 0 at every d != 0, so A_m = |sum rho e^{i m th}| /
    sum |rho| is a ratio of SAMPLING NOISE TO SAMPLING NOISE: undefined, and it
    reads ~0.53 rather than ~0 (measured). That is the `peak/base` disease in a
    third costume — a ratio whose denominator goes to zero — and it means white
    noise is OUTSIDE this statistic's domain, not at its floor. A disk ensemble
    is isotropic like white noise but CARRIES REAL CORRELATION at the same
    length scale as the waves, so the ratio is well posed and the floor is the
    thing it claims to be.

    It is also exactly GCAL's own pre-eye-opening input — "noisy disk-shaped
    patterns" (VISION_PRIOR_ART.md §2.6) — so this arm doubles as a direct read
    on H_B: whatever GCAL gets orientation FROM, it is not this ensemble's
    second-order statistics.

    `radius` is passed by the caller from the waves' OWN measured correlation
    length, never chosen here.
    """
    out = np.zeros((T, h, w), np.float32)
    ys, xs = np.mgrid[0:h, 0:w]
    area = np.pi * radius * radius
    n_disks = max(1, int(round(p * h * w / area)))
    for t in range(T):
        f = np.zeros((h, w), np.float32)
        for _ in range(n_disks):
            cy = float(rng.random() * h)
            cx = float(rng.random() * w)
            dy = np.minimum(np.abs(ys - cy), h - np.abs(ys - cy))
            dx = np.minimum(np.abs(xs - cx), w - np.abs(xs - cx))
            f[(dy ** 2 + dx ** 2) <= radius * radius] = 1.0
        out[t] = f
    return out


def bar_movie(rng, T: int, h: int, w: int, p: float, *,
              theta_fixed: float | None) -> np.ndarray:
    """ANISOTROPIC control: frames of 1-cell-wide straight bars.

    theta_fixed is not None -> every frame's bars share ONE orientation. The
        ensemble is anisotropic; global AND local must read anisotropic.
    theta_fixed is None -> each frame draws its own orientation uniformly. The
        ensemble is ISOTROPIC while every frame is anisotropic. This is the
        control that discriminates the two measurements: it MUST read
        global ~= floor and local >> floor. Without it, "global isotropic,
        local anisotropic" is an untested claim about the instrument.

    Density is matched to `p` by choosing the number of bars per frame.
    """
    out = np.zeros((T, h, w), np.float32)
    ys, xs = np.mgrid[0:h, 0:w]
    n_bars = max(1, int(round(p * h)))
    for t in range(T):
        th = theta_fixed if theta_fixed is not None else float(rng.random() * np.pi)
        # signed distance to a line through the origin at orientation th
        d = xs * np.sin(th) - ys * np.cos(th)
        f = np.zeros((h, w), np.float32)
        for _ in range(n_bars):
            off = float(rng.random() * h)
            f[np.abs(((d - off) % h) - h / 2.0) > (h / 2.0 - 0.5)] = 1.0
        out[t] = f
    return out


# ------------------------------------------------------- front descriptives ---
def front_stats(movie: np.ndarray) -> dict:
    """Is the active set a FRONT, a patch, or scatter?

    `neighbours_mean` — the mean number of 4-neighbours of an active cell that
    are also active. A thin 1-cell-wide CURVE has ~2 (a predecessor and a
    successor along the front); a solid BLOB approaches 4; isolated SCATTER
    approaches 0. The three regimes are separated by the statistic's own
    geometry, not by a chosen threshold.
    """
    T, h, w = movie.shape
    act = movie > 0.5
    n = act.sum(axis=(1, 2)).astype(float)
    nb = np.zeros(T)
    for t in range(T):
        a = act[t]
        cnt = np.zeros((h, w), np.int32)
        cnt[1:, :] += a[:-1, :]
        cnt[:-1, :] += a[1:, :]
        cnt[:, 1:] += a[:, :-1]
        cnt[:, :-1] += a[:, 1:]
        nb[t] = cnt[a].mean() if a.any() else np.nan
    return {
        "density_mean": float(act.mean()),
        "active_per_frame_mean": float(n.mean()),
        "neighbours_mean": float(np.nanmean(nb)),
        "frames_dead": int((n == 0).sum()),
        "n_frames": int(T),
    }


__all__ = [
    "make_world", "record_bursting", "read_last_burst", "window_movie",
    "frame_autocorr", "movie_autocorr", "corr_from_R", "anisotropy",
    "local_vs_global", "second_moment_matrix", "eigen_report",
    "structure_tensor_coherence", "radial_profile", "corr_length",
    "disk_movie", "centre_slice",
    "orientation_index", "dc_fraction", "white_noise_movie", "bar_movie",
    "front_stats", "provenance_line",
]
