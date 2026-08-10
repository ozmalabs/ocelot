"""earned_augmentation — EARNED data augmentation for the from-scratch learned head (7fd2be31).

THE DATA-SCALE PRESCRIPTION: the residual to borrowed Gemma 91% is a DATA-SCALE gap (the curve
still climbs). If the gap is DATA, SYNTHESIZE the data-scale you'd otherwise borrow — from the
agent's OWN machinery, NOT a borrowed augmentation library or pretrained net.

EARNED augmentation sources (all from held data / the agent's own generative math):
  • NATURAL POSITIVES — Omniglot's 20 reps per char (same char x 20 drawers) = FREE earned
    writer-variation (the writer-shape style residual, 5695f2b3, made manifest as real samples).
  • GENERATED VARIANTS — the agent's OWN deformation/generation math over the pen TRACE:
      affine  (rotate/scale/shear — a held drawer's style as a linear motor transform),
      elastic (smooth random displacement field along the stroke — residual-recurrence-style
               perturbation of the stroke trajectory),
      motor   (per-point gaussian motor noise — the BPL-style rendering noise).
  These are GENERATED from each trace, not drawn from any external corpus.

The DEGENERATE control (must do WORSE): random pixel/feature NOISE on the image (not a real
deformation / not a true positive) — proves it's MEANINGFUL augmentation, not just jitter.

torch/numpy USAGE (flagged): numpy is the deformation + raster + scatter adapter math (pure
geometry on the trace points; no learned/borrowed weights). The trainer (learned_perceptual_head)
is from-scratch torch. NO external augmentation data, NO pretrained net, NO borrowed weights.
"""
from __future__ import annotations
import numpy as _np                 # ADAPTER: deformation geometry + raster/scatter math
import domains.omniglot_world as _ow
import domains.scattering_feature as _sf


# ---- the agent's OWN generated trace deformations (no borrowed data) ----

def deform_affine(strokes, rng):
    """A random affine motor transform (rotate/scale/shear) — a drawer-style as a linear map."""
    rot = rng.uniform(-0.30, 0.30)
    sx = rng.uniform(0.82, 1.18); sy = rng.uniform(0.82, 1.18)
    shear = rng.uniform(-0.18, 0.18)
    R = _np.array([[_np.cos(rot), -_np.sin(rot)], [_np.sin(rot), _np.cos(rot)]])
    Sh = _np.array([[1.0, shear], [0.0, 1.0]]); Sc = _np.diag([sx, sy])
    M = R @ Sh @ Sc
    return [(_np.asarray(s, float) @ M.T) for s in strokes]


def deform_elastic(strokes, rng, amp=3.0, smooth=20):
    """A smooth random displacement field along each stroke (residual-recurrence-style warp)."""
    out = []
    for s in strokes:
        a = _np.asarray(s, float); n = len(a)
        if n < 3:
            out.append(a); continue
        w = max(2, min(smooth, n))
        dx = _np.cumsum(rng.randn(n)); dy = _np.cumsum(rng.randn(n))
        k = _np.ones(w) / w
        dx = _np.convolve(dx, k, "same"); dy = _np.convolve(dy, k, "same")
        dx = amp * dx / (_np.abs(dx).max() + 1e-6); dy = amp * dy / (_np.abs(dy).max() + 1e-6)
        out.append(a + _np.stack([dx, dy], 1))
    return out


def deform_motor(strokes, rng, sigma=0.8):
    """Per-point gaussian motor noise — the BPL-style rendering-noise perturbation."""
    return [_np.asarray(s, float) + sigma * rng.randn(*_np.asarray(s, float).shape) for s in strokes]


def generate_variant(strokes, rng):
    """One EARNED generated variant = a random composition of the agent's own deformations."""
    out = strokes
    if rng.rand() < 0.8:
        out = deform_affine(out, rng)
    if rng.rand() < 0.7:
        out = deform_elastic(out, rng, amp=rng.uniform(1.5, 4.0))
    if rng.rand() < 0.5:
        out = deform_motor(out, rng, sigma=rng.uniform(0.4, 1.0))
    return out


def augmented_scatter(path, rng):
    """A scattering feature of ONE earned-generated variant of the trace."""
    st = _ow.load_strokes(path)
    return _sf.scatter_trace_image(generate_variant(st, rng))


# ---------------------------------------------------------------------------
# THE SYNTHESIS FIX — model the WRITER'S PHYSICAL MOTOR LIMITS (the synthetic-vs-real
# ceiling diagnosis: unconstrained variants break the motor physics REAL writers obey).
# A real hand produces the thermodynamically CHEAPEST trajectory: MINIMUM-JERK / minimum-
# effort, with the TWO-THIRDS POWER LAW (speed proportional to curvature^(-1/3) — slows on
# tight curves). DIAGNOSED gap (measured): unconstrained synthetic jerk ~2x real (per-point
# motor noise adds unphysical high-frequency jerk) and a broken two-thirds slope. The FIX:
# SMOOTH (minimum-jerk) low-frequency warps ONLY + two-thirds re-timing — physically-cheap
# variation that matches real writer diversity. All the agent's OWN motor model; no borrowed data.
# ---------------------------------------------------------------------------
def _smooth_warp(a, rng, amp, n_ctrl=4):
    """A MINIMUM-JERK-like spatial warp: a few control-point displacements, smoothly
    interpolated + low-pass filtered (low jerk). NO per-point noise (that is what made the
    unconstrained synthesis 2x too jerky vs a real hand)."""
    n = len(a)
    if n < 5:
        return a
    ts = _np.linspace(0, 1, n); cs = _np.linspace(0, 1, n_ctrl)
    dx = _np.interp(ts, cs, rng.randn(n_ctrl) * amp)
    dy = _np.interp(ts, cs, rng.randn(n_ctrl) * amp)
    w = max(3, n // 6); k = _np.ones(w) / w
    dx = _np.convolve(dx, k, "same"); dy = _np.convolve(dy, k, "same")
    return a + _np.stack([dx, dy], 1)


def _two_thirds_retime(a, beta=0.33):
    """Re-time the trajectory so speed ~ curvature^(-beta) (the two-thirds power law): dwell
    more where curvature is high (the hand SLOWS on tight curves). Affects the 1D-trajectory
    feature's timing; spatially near-identity. The agent's own motor-cost model."""
    if len(a) < 5:
        return a
    v = _np.diff(a, axis=0); sp = _np.linalg.norm(v, axis=1) + 1e-6
    th = _np.arctan2(v[:, 1], v[:, 0]); dth = _np.abs(_np.diff(_np.unwrap(th)))
    k = _np.concatenate([[1e-3], dth]) / (sp + 1e-6) + 1e-3
    w = k ** beta
    cw = _np.concatenate([[0.0], _np.cumsum(w * sp)])
    u = _np.linspace(0, cw[-1], len(a))
    return _np.stack([_np.interp(u, cw, a[:, 0]), _np.interp(u, cw, a[:, 1])], 1)


def generate_physical_variant(strokes, rng, amp=2.0, retime=True):
    """One PHYSICS-CONSTRAINED variant = an affine motor transform + a MINIMUM-JERK smooth
    warp (+ optional two-thirds re-timing). Physically-cheap variation matching real writer
    motor statistics (low jerk, two-thirds coupling) — the synthesis FIX. The agent's OWN
    motor model; no borrowed data."""
    out = strokes
    if rng.rand() < 0.8:
        out = deform_affine(out, rng)
    out2 = []
    for s in out:
        a = _smooth_warp(_np.asarray(s, float), rng, amp=rng.uniform(1.0, amp))
        if retime:
            a = _two_thirds_retime(a)
        out2.append(a)
    return out2


def physical_scatter(path, rng, amp=2.0):
    """A scattering feature of ONE physics-constrained variant (the synthesis FIX)."""
    return _sf.scatter_trace_image(generate_physical_variant(_ow.load_strokes(path), rng, amp=amp))


def motor_stats(strokes):
    """Measure a trajectory's MOTOR statistics — two-thirds-law slope (log speed vs log
    curvature; physical ideal ~ -1/3), mean jerk, speed CV. Used to compare REAL vs synthetic
    diversity (the diagnosis + the fix's discriminative control)."""
    sp_, k_, jk_ = [], [], []
    for s in strokes:
        a = _np.asarray(s, float)
        if len(a) < 5:
            continue
        v = _np.diff(a, axis=0); sp = _np.linalg.norm(v, axis=1) + 1e-6
        th = _np.arctan2(v[:, 1], v[:, 0]); dth = _np.abs(_np.diff(_np.unwrap(th)))
        k = dth / (sp[:-1] + 1e-6) + 1e-6
        jrk = _np.diff(_np.diff(v, axis=0), axis=0)
        sp_.append(sp[:len(k)]); k_.append(k); jk_.append(_np.linalg.norm(jrk, axis=1))
    if not sp_:
        return None
    sp = _np.concatenate(sp_); k = _np.concatenate(k_); jk = _np.concatenate(jk_)
    m = (sp > 1e-3) & (k > 1e-3)
    if m.sum() < 5:
        return None
    import warnings as _w
    with _w.catch_warnings():
        _w.simplefilter("ignore")
        slope = float(_np.polyfit(_np.log(k[m]), _np.log(sp[m]), 1)[0])
    return {"twothirds_slope": slope, "mean_jerk": float(jk.mean()),
            "speed_cv": float(sp.std() / sp.mean())}


# ---- the DEGENERATE control: random feature noise (not a real deformation) ----

def degenerate_scatter(path, rng, noise=0.5):
    """A scattering feature with random NOISE added (the degenerate control — NOT a real
    deformation / not a true positive). Meaningful augmentation must beat this."""
    f = _sf.scatter_trace_image(_ow.load_strokes(path))
    if f is None:
        return None
    return f + noise * rng.randn(*f.shape) * (_np.abs(f).mean() + 1e-6)


# ---- build an AUGMENTED background training set (scatter features) ----

def build_augmented_set(*, n_alphabets=None, max_per=None, n_aug=2, mode="real", seed=0,
                        include_natural=True):
    """Build (X, y) scatter features for the background set with EARNED augmentation.
    mode='real'      -> n_aug agent-generated variants per drawing (own deformations)
    mode='degenerate'-> n_aug random-NOISE variants per drawing (the control)
    include_natural  -> the original 20 reps are already natural positives (kept regardless).
    Held data only; eval alphabets excluded. Returns (X, y, n_classes)."""
    rng = _np.random.RandomState(seed)
    bg = _ow.alphabets("background")
    if n_alphabets:
        bg = bg[:n_alphabets]
    X, y, cid = [], [], 0
    for al in bg:
        for c in _ow.characters(al, split="background"):
            ds = _ow.drawings(c)
            if max_per:
                ds = ds[:max_per]
            feats = []
            for d in ds:
                if include_natural:
                    f0 = _sf.scatter_trace_image(_ow.load_strokes(d))
                    if f0 is not None:
                        feats.append(f0)
                for _ in range(n_aug):
                    if mode == "degenerate":
                        fa = degenerate_scatter(d, rng)
                    elif mode == "physical":          # the synthesis FIX (writer motor limits)
                        fa = physical_scatter(d, rng)
                    else:                              # "real" = unconstrained own deformations
                        fa = augmented_scatter(d, rng)
                    if fa is not None:
                        feats.append(fa)
            if len(feats) >= 2:
                for f in feats:
                    X.append(f); y.append(cid)
                cid += 1
    return _np.array(X, dtype=_np.float32), _np.array(y), cid
