#!/usr/bin/env python3
"""TWO-EYE SUB-RECEPTOR OFFSET REGISTRATION SENSOR (block 176000-176999).

A mechanical numpy sensor — the 1-D PERIODIC analog of block 149000's
`subcell_register.register_residual_offset`, REUSING its PROVEN
`bilinear_upsample` sub-cell interpolation primitive. It READS ONLY the two
eyes' activation arrays (their overlapping views of ONE flat textured wall) and
EMITS the sub-receptor offset between them as a FINER-UNIT INTEGER (offset × S).

This closes Rung 5's largest caveat: Rung 5 handed the fusion a KNOWN offset;
here the offset is ESTIMATED from the eyes' own data, then fed into the same
`multilook_superres` kernel. It is the exact reuse the Rung-5 residual named
("the tree's proven `subcell_register`, block 149000").

NO agent decision, NO graph state, no `if` over graph state — the offset is a
pure signal read, exactly like `motion_group_world.vector_field` /
`subcell_register.register_residual_offset`. Every downstream order-N / fusion
decision remains the Rust kernel + seed rule.

THE FRAME/CONTINUUM INVARIANT — WHERE PRECISION IS ALLOWED TO LIVE
-----------------------------------------------------------------
The emitted `bt` is an INTEGER (finer units of 1/S receptor) — the STEPPED
observable. delta_est = bt / S is a CROSS-FRAME quantity: the map
`Hom(frame_A, frame_B)` between the two eyes' frames, so it MAY be non-integer.
A per-eye displacement IS such a map (like 149000's per-frame velocity). No
float is ever returned as, or written into, an in-frame coordinate. `S` is a
DECLARED resolution residual (§13), like `block` / `k` — the registration's
sub-cell step (1/S receptor); it is NOT a tuned tolerance.
"""
from __future__ import annotations

import numpy as np

from domains.subcell_register import bilinear_upsample


def estimate_offset_fine(act_a, act_b, *, S, max_shift_receptors=1):
    """Estimate eye B's sub-receptor offset relative to eye A, as a FINER-UNIT
    INTEGER, from the two eyes' activation samples of ONE periodic wall.

    Both eyes sample the SAME flat textured wall (period P = N receptors) over
    the same extent — eye A at integer receptor positions i, eye B at i + delta.
    So eye B's sequence is eye A's sequence CIRCULARLY shifted by the continuous
    sub-receptor `delta`. We REUSE subcell's proven `bilinear_upsample` to render
    both sequences on an S-times-finer grid and find the integer fine-shift `bt`
    that best aligns B onto A (SAD argmin, Occam ascending-|shift| tie-break —
    the same conditioning as subcell). The wall is PERIODIC (no boundary), so the
    sequences are CIRCULARLY padded before upsampling — no edge clamping enters
    the interior.

    Args:
        act_a, act_b : the two eyes' per-receptor activations (length N each).
        S            : the finer unit (1/S receptor) — declared §13 residual.
        max_shift_receptors : residual search half-window in receptors (the
                       offset is sub-receptor, so ±1 receptor is ample).

    Returns (bt, diag): `bt` = the offset in finer units (INTEGER);
        delta_est = bt / S. Because b_i = f(i + delta) aligns to a when shifted
        LEFT by delta, `bt ≈ delta * S` (positive for a positive offset). A
        constant fine-grid pad offset cancels between the two upsamples, so the
        estimate is independent of the absolute interior anchor.
    """
    a = np.asarray(act_a, dtype=np.float64)
    b = np.asarray(act_b, dtype=np.float64)
    n = int(a.shape[0])
    if b.shape[0] != n:
        raise ValueError("two eyes must have the same receptor count")
    S = int(S)
    pad = int(max_shift_receptors) + 1                   # wrap margin (receptors)
    ap = np.concatenate([a[-pad:], a, a[:pad]])          # circular pad (periodic wall)
    bp = np.concatenate([b[-pad:], b, b[:pad]])
    # REUSE subcell's proven bilinear sub-cell interpolation (as 1-row images).
    aU = bilinear_upsample(ap[None, :], S)[0]
    bU = bilinear_upsample(bp[None, :], S)[0]
    lo = pad * S                                         # interior start (fine units)
    span = n * S                                         # interior length (fine units)
    aint = aU[lo:lo + span]
    R = int(max_shift_receptors) * S
    # candidate fine shifts, ascending magnitude — Occam tie-break: the smallest
    # correction wins an exact tie (identical to subcell's offset ordering).
    offs = sorted(range(-R, R + 1), key=lambda t: (abs(int(t)), int(t)))
    best = np.inf
    bt = 0
    sad0 = None
    for t in offs:
        bint = bU[lo - t:lo - t + span]                  # shift B by t finer units
        sad = float(np.abs(aint - bint).sum())
        if t == 0:
            sad0 = sad
        if sad < best:
            best = sad
            bt = int(t)
    diag = {
        "best_sad": best / span,
        "centre_sad": (sad0 / span) if sad0 is not None else None,
        "S": S, "R": R, "n": n,
    }
    return int(bt), diag


def estimate_offset(act_a, act_b, *, S, max_shift_receptors=1):
    """Convenience wrapper: return (delta_est, bt, diag) where delta_est = bt/S
    is the CROSS-FRAME offset in receptor units (a map, allowed non-integer) and
    `bt` is the invariant-clean INTEGER finer-unit observable.

    NOTE: this amplitude-SAD estimator is corrupted by an ALIASED supra-Nyquist
    target (block-176000 v1 result — the target energy is indistinguishable from
    real in-band energy to a shift metric). For a wall carrying a supra-Nyquist
    harmonic, use `estimate_offset_phase` instead."""
    bt, diag = estimate_offset_fine(
        act_a, act_b, S=S, max_shift_receptors=max_shift_receptors)
    return bt / float(S), bt, diag


def clean_bins(N, k0):
    """The DFT bins a supra-Nyquist harmonic k0 does NOT contaminate, for a
    length-N sample sequence. k0 aliases onto bin `|k0 mod N|` folded into
    [0, N/2]; the clean, phase-bearing bins are the well-sampled harmonics
    STRICTLY below the Nyquist bin N/2 (DC has no shift phase; the Nyquist bin
    is real-valued and carries no shift phase either), MINUS the aliased bin.
    Pure arithmetic from the KNOWN band structure — not fit to data."""
    alias = k0 % N
    if alias > N // 2:
        alias = N - alias                       # fold into [0, N/2]
    return [k for k in range(1, (N + 1) // 2) if k != alias]


def estimate_offset_phase(act_a, act_b, *, S, N=None, k0=None, bins=None):
    """Estimate eye B's sub-receptor offset as the CROSS-FRAME PHASE between the
    two eyes' DFT bins — the invariant's named map ("Fourier lives in the MAP
    between frames"). EXACT for well-sampled bins, and IMMUNE to an aliased
    supra-Nyquist target because the bin it folds onto is EXCLUDED.

    For each clean bin k: `B_k / A_k = exp(+i·2π·k·δ/N)` (shift theorem), so
    `δ = angle(B_k/A_k)·N/(2π·k)`. δ is amplitude-weighted-averaged over the
    clean bins (`bins`, or `clean_bins(N, k0)` if not given), then emitted as a
    FINER-UNIT INTEGER `bt = round(δ·S)` — the stepped observable; δ_est = bt/S.

    Returns (delta_est, bt, diag). Assumes a sub-receptor offset (|δ| < N/(2·max
    bin)); no phase unwrapping is applied (the wall's offset is sub-receptor)."""
    a = np.asarray(act_a, dtype=np.float64)
    b = np.asarray(act_b, dtype=np.float64)
    n = int(a.shape[0])
    if b.shape[0] != n:
        raise ValueError("two eyes must have the same receptor count")
    N = n if N is None else int(N)
    if bins is None:
        if k0 is None:
            raise ValueError("give either explicit `bins` or `k0`")
        bins = clean_bins(N, int(k0))
    A = np.fft.rfft(a)
    B = np.fft.rfft(b)
    num = 0.0
    den = 0.0
    per_bin = {}
    for k in bins:
        w = float(abs(A[k]))
        if w < 1e-9:                             # dead bin — no phase to read
            continue
        ph = float(np.angle(B[k] / A[k]))        # = 2π·k·δ/N
        d = ph * N / (2.0 * np.pi * k)
        per_bin[k] = d
        num += w * d
        den += w
    if den <= 0:
        return 0.0, 0, {"bins": list(bins), "per_bin": per_bin, "S": int(S)}
    delta = num / den
    bt = int(round(delta * int(S)))              # stepped invariant-clean observable
    diag = {"bins": list(bins), "per_bin": per_bin, "delta_raw": delta,
            "S": int(S), "N": N}
    return bt / float(S), bt, diag
