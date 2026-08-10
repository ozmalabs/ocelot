"""audio_basis_select — the PRINCIPLED, LABEL-FREE SELECTOR over candidate bases.

THE SELECTOR IS NOT ACCURACY.  It is compression / coherence, computed WITHOUT the
recognition decision and WITHOUT held-out accuracy.  Two native, label-free
criteria, each reported per candidate basis; the agent PICKS the winner by the
selector value.

PRIMARY = COMPRESSION (description length, MDL — the substrate's core selector): the
basis that describes the data most COMPACTLY captures the most structure.  SHIFT-
COHERENCE is the SECONDARY (VTL-stability) tie-break.  CORRECTED 2026-06-16 (see
select(); commit 076d8b54): shift-coherence-primary mis-picked the cochlear ENERGY
envelope — most VTL-stable because least informative — capping cross-speaker
clustering ~0.30, while the spectral-SHAPE (formant) basis compresses better and
lifts it to ~0.68.  Invariance without discriminability is the wrong objective;
compression is the right one.

(1) SHIFT-COHERENCE  (the VTL=shift criterion, the directive's primary lever)
----------------------------------------------------------------------------
VTL is multiplicative on frequency = an additive SHIFT in log-frequency.  In the
RIGHT basis, the SAME word spoken by DIFFERENT speakers should differ by ~a pure
TRANSLATION of the spectral pattern along the band axis; in the WRONG basis it is a
tangled per-band warp.  We measure this directly:

  For each same-word cross-speaker PAIR of band-trajectory matrices (A, B), both
  z-normalised per band, find the SINGLE integer band-shift s that best aligns B to
  A (max cross-correlation over the band axis), and report:

     resid(shift) / resid(0)   — how much of the cross-speaker mismatch a SINGLE
                                  shift removes.  << 1 means the variation IS a
                                  translation (coherent basis); ~1 means a shift
                                  doesn't help (tangled basis).

  Word identity is used ONLY to GROUP same-word pairs (it is the natural unit of
  "same content, different speaker"); it is NOT a label fed to a classifier and the
  measure is the GEOMETRY of the variation, not recognition accuracy.  The shift is
  chosen to MINIMISE a residual, per pair, with no held-out set — it is the
  coherence of the representation, not a tuned hyper-parameter.

(2) MDL / COMPRESSION  (effective spectral dimensionality)
----------------------------------------------------------
The more coherent basis DESCRIBES the band trajectories more compactly.  Label-free
proxy: the SPECTRAL ENTROPY of the singular-value spectrum of the stacked frame
matrix (the rep's effective dimensionality), averaged over clips, plus a simple
quantised description-length of the per-frame band-DIFFERENCE pattern.  Both are
intrinsic properties of the representation — no task, no labels, no fit.  Lower
effective dimension / shorter description length = the basis captures the same
signal with fewer coordinates = it compresses better.

REPORTED: per basis, (a) median shift-coherence residual ratio (lower = better),
(b) mean effective dimensionality / DL (lower = better).  The agent CHOOSES the
basis that is most coherent under the PRIMARY criterion (shift-coherence), with
compression as the corroborating second criterion.  All without recognition labels.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np


# ---------------------------------------------------------------------------
# (1) SHIFT-COHERENCE
# ---------------------------------------------------------------------------
def _z_per_band(M):
    """z-normalise each band (column) over time so the residual measures SHAPE,
    not level (level is the trivially-removable part of the talker transform)."""
    M = np.asarray(M, dtype=np.float64)
    mu = M.mean(axis=0, keepdims=True)
    sd = M.std(axis=0, keepdims=True) + 1e-9
    return (M - mu) / sd


def _word_pattern(M):
    """Collapse a frames x bands trajectory to a single SPECTRAL pattern over the
    band axis (mean over time of the z-per-band matrix), the object a VTL shift
    translates.  Returns a length-bands vector, then z-scored over bands."""
    Z = _z_per_band(M)
    v = Z.mean(axis=0)
    v = (v - v.mean()) / (v.std() + 1e-9)
    return v


def _best_shift_resid_ratio(va, vb, max_shift=None):
    """Best single integer band-shift of vb onto va.  Returns resid(best_shift) /
    resid(0): how much a SINGLE translation reduces the mismatch.  << 1 => the
    cross-speaker difference is (mostly) a shift in this basis (coherent)."""
    n = len(va)
    if max_shift is None:
        max_shift = max(2, n // 3)
    base = float(np.sum((va - vb) ** 2)) + 1e-12
    best = base
    for s in range(-max_shift, max_shift + 1):
        if s == 0:
            shifted = vb
        elif s > 0:
            shifted = np.concatenate([np.full(s, vb[0]), vb[:-s]])
        else:
            shifted = np.concatenate([vb[-s:], np.full(-s, vb[-1])])
        r = float(np.sum((va - shifted) ** 2))
        if r < best:
            best = r
    return best / base


def shift_coherence(mats_by_word, max_pairs_per_word=60, rng=None):
    """mats_by_word: {word -> [frames x bands matrices]}.  Returns the MEDIAN
    over same-word cross-... (here within-word, mixed speaker) pairs of the
    best-single-shift residual ratio.  LOWER = the same word differs by ~a pure
    shift in this basis = MORE COHERENT.  Label used only to group same-word pairs.

    (The caller is responsible for passing matrices drawn across speakers so the
    within-word pairs are genuinely cross-speaker.)"""
    rng = rng or np.random.default_rng(0)
    ratios = []
    for word, mats in mats_by_word.items():
        if len(mats) < 2:
            continue
        pats = [_word_pattern(M) for M in mats if M is not None and M.shape[0] >= 2]
        k = len(pats)
        if k < 2:
            continue
        pairs = [(i, j) for i in range(k) for j in range(i + 1, k)]
        if len(pairs) > max_pairs_per_word:
            idx = rng.choice(len(pairs), size=max_pairs_per_word, replace=False)
            pairs = [pairs[t] for t in idx]
        for i, j in pairs:
            ratios.append(_best_shift_resid_ratio(pats[i], pats[j]))
    if not ratios:
        return float("nan"), 0
    return float(np.median(ratios)), len(ratios)


# ---------------------------------------------------------------------------
# (2) MDL / COMPRESSION — effective spectral dimensionality (label-free).
# ---------------------------------------------------------------------------
def _effective_dim(M):
    """Spectral-entropy effective dimensionality of a z-per-band frames x bands
    matrix: exp(H) of the normalised singular-value^2 distribution.  Lower = the
    trajectory lives in fewer coordinates = more compressible in this basis."""
    Z = _z_per_band(M)
    if Z.shape[0] < 2 or Z.shape[1] < 2:
        return float(min(Z.shape))
    try:
        s = np.linalg.svd(Z, compute_uv=False)
    except np.linalg.LinAlgError:
        return float(min(Z.shape))
    p = (s ** 2)
    p = p / (p.sum() + 1e-12)
    p = p[p > 0]
    H = -float(np.sum(p * np.log(p)))
    return float(np.exp(H))


def _quant_dl(M, levels=8):
    """A crude per-clip description length: bits to code the quantised per-frame
    band-DIFFERENCE pattern (delta-spectrum) at `levels` levels via its empirical
    entropy.  Lower bits = more redundancy captured = more compressible."""
    Z = _z_per_band(M)
    d = np.diff(Z, axis=0)
    if d.size == 0:
        return 0.0
    lo, hi = d.min(), d.max()
    if hi - lo < 1e-9:
        return 0.0
    q = np.clip(((d - lo) / (hi - lo) * (levels - 1)).round().astype(int),
                0, levels - 1)
    counts = np.bincount(q.ravel(), minlength=levels).astype(np.float64)
    p = counts / counts.sum()
    p = p[p > 0]
    H = -float(np.sum(p * np.log2(p)))      # bits/symbol
    return H * d.size                        # total bits for the clip


def compression(mats):
    """mats: [frames x bands matrices].  Returns (mean effective dim, mean DL bits
    PER BAND).  Lower on both = more compressible / coherent.  DL is normalised by
    band count so bases with different band counts are comparable (here all share
    n_bands, but we normalise anyway for cleanliness)."""
    dims, dls = [], []
    for M in mats:
        if M is None or M.shape[0] < 2 or M.shape[1] < 2:
            continue
        dims.append(_effective_dim(M))
        dls.append(_quant_dl(M) / M.shape[1])
    if not dims:
        return float("nan"), float("nan"), 0
    return float(np.mean(dims)), float(np.mean(dls)), len(dims)


# ---------------------------------------------------------------------------
# SELECT — combine the two label-free criteria into a ranking.  Primary =
# CORRECTED OBJECTIVE (2026-06-16): rank by COMPRESSION (description length = MDL),
# the substrate's CORE selector — NOT shift-coherence. shift-coherence is a secondary
# (VTL-stability) tie-break. NO accuracy anywhere.
# ---------------------------------------------------------------------------
def select(per_basis):
    """per_basis: {name -> {"shift_ratio":..,"shift_n":..,"eff_dim":..,
    "dl_bits":..,"comp_n":..}}.  Returns (chosen_name, ranked_list).

    Ranking key = DESCRIPTION LENGTH (dl_bits) ASCENDING — the substrate's compression /
    MDL selector: the front-end that lets the agent describe the data most COMPACTLY
    captures the most structure. Shift-coherence (VTL stability) is the SECONDARY
    tie-break, not the primary criterion.

    WHY CHANGED (commit 076d8b54 / fix-the-fixer): shift-coherence-PRIMARY mis-picked the
    cochlear ENERGY envelope — it is the MOST shift-coherent (most VTL-stable) precisely
    because it is the LEAST informative (it discards the formant pattern), capping
    cross-speaker clustering at ~0.30. The spectral-SHAPE (formant) front-end is LESS
    shift-coherent but compresses far better (dl ~18 vs ~26 bits, effective-dim ~2.7 vs
    ~1.9) and lifts clustering to ~0.68. Shift-coherence alone optimises INVARIANCE
    without DISCRIMINABILITY and chooses the uninformative-but-stable basis; compression
    rewards structure captured, which is the property a front-end must have. The choice
    is by the PRINCIPLED selector (MDL), never by accuracy.

    The returned `rows` keep their (name, shift_ratio, eff_dim, dl_bits) layout for
    callers; only the ranking and `chosen` follow the corrected (compression) objective."""
    rows = []
    for name, d in per_basis.items():
        rows.append((name, d.get("shift_ratio", float("nan")),
                     d.get("eff_dim", float("nan")),
                     d.get("dl_bits", float("nan"))))
    # ascending DESCRIPTION LENGTH (rows[*][3], lower = more compressive = more structure
    # captured = the MDL selector); shift-coherence residual (rows[*][1]) as tie-break.
    rows.sort(key=lambda r: (np.isnan(r[3]), r[3], np.isnan(r[1]), r[1]))
    chosen = rows[0][0] if rows else None
    return chosen, rows


__all__ = ["shift_coherence", "compression", "select",
           "_word_pattern", "_best_shift_resid_ratio", "_effective_dim"]
