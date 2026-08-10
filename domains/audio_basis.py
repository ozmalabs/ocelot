"""audio_basis — the AGENT CHOOSES ITS OWN BASIS FOR AUDIO.

THE INSIGHT (orchestrator directive, internalised)
--------------------------------------------------
The gammatone-ENERGY front end is the "base 10 of audio": the human cochlea's
ANATOMICAL-ACCIDENT filter layout (the particular spacing our embodiment happens
to provide), NOT the basis in which speech STRUCTURE is COHERENT.  The agent is
not built from a human cochlea — it can CHOOSE the basis where speech CLOSES, the
way a rational creature counts in base 12 (divisors 2,3,4,6 all terminate) rather
than base 10 (only 2,5).  The right basis is the one aligned with speech's
multiplicative / dyadic physics:

  * VTL (vocal-tract length) is MULTIPLICATIVE on frequency = an ADDITIVE SHIFT in
    LOG-frequency.  So in a LOG / constant-Q / octave basis, speaker change becomes
    a near-pure TRANSLATION of the spectral pattern along the band axis — the
    invariance is a SIMPLE operation (a shift), not a tangled warp.
  * Sound is octave / harmonic (dyadic).  A constant-Q / octave layout aligns the
    band axis with that physics.

WHAT THIS MODULE PROVIDES — a CANDIDATE BASIS FAMILY (composed, NOT fitted)
--------------------------------------------------------------------------
A basis here = a parametrized GAMMATONE FILTERBANK whose only freedom is the
LAYOUT of band centre frequencies on the frequency axis (the warp), plus band
COUNT and band Q (filter sharpness via the gammatone order).  Every band is the
SAME owned gammatone+envelope primitive (`gammatone_env` from the mine harness);
the candidate bases differ ONLY in WHERE the centres sit:

    LINEAR     centres equally spaced in Hz            (most anatomy-agnostic / naive)
    MEL        centres equally spaced on the mel scale (perceptual, sub-octave)
    ERB        centres equally spaced on the ERB scale (the cochlea's own ~gammatone)
    LOG        centres equally spaced in log-Hz        (VTL = pure shift here)
    OCTAVE     constant-Q, integer fractions of an octave (dyadic / harmonic basis)

LINEAR/ERB sit at the ANATOMICAL end; LOG/OCTAVE sit at the STRUCTURAL end.  ERB
with 32 bands is the EXISTING gammatone front end (the default / baseline).

These are all composed transforms over the agent's owned FFT/filterbank ops at the
I/O boundary — NOT learned, NOT fitted.  The agent does not train a basis; it
COMPOSES several and SELECTS among them by a principled, LABEL-FREE criterion.

DISCIPLINE: nothing here selects by accuracy.  The selector (audio_basis_select)
is compression / shift-coherence, computed WITHOUT recognition labels.
"""
from __future__ import annotations

import math

import numpy as np

from scripts.mine_whisper import gammatone_env


def gammatone_env_q(x, fs, fc, q, env_cut=50.0):
    """Constant-Q gammatone band envelope: bandwidth = fc / q (proportional to the
    centre frequency) instead of the ERB-proportional bandwidth `gammatone_env`
    uses.  This is the DYADIC / harmonic basis's filter: each band spans the same
    FRACTION of an octave, so the filterbank tiles frequency on a multiplicative
    (octave) grid — aligned with speech's octave/harmonic physics.  Owned FIR
    gammatone construction, I/O boundary only (no fit)."""
    dur = 0.025
    L = int(dur * fs)
    t = np.arange(L) / fs
    b = 2.0 * math.pi * (fc / max(q, 1e-6))     # constant-Q bandwidth
    g = t ** 3 * np.exp(-b * t) * np.cos(2 * math.pi * fc * t)
    e = math.sqrt(float(np.sum(g * g)))
    if e > 0:
        g = g / e
    y = np.convolve(x, g, mode="same")
    y = np.maximum(y, 0.0)
    tau = 1.0 / (2 * math.pi * env_cut)
    a = math.exp(-1.0 / (tau * fs))
    out = np.empty_like(y)
    acc = 0.0
    for i in range(len(y)):
        acc = a * acc + (1 - a) * y[i]
        out[i] = acc
    return out


# ---------------------------------------------------------------------------
# Frequency-axis WARPS — Hz <-> warped-unit, so we can lay out band centres
# equally-spaced in the WARPED unit.  Each warp is a different BASIS.
# ---------------------------------------------------------------------------
def _hz_to_mel(f):
    return 2595.0 * math.log10(1.0 + f / 700.0)


def _mel_to_hz(m):
    return 700.0 * (10.0 ** (m / 2595.0) - 1.0)


def _hz_to_erb(f):
    # Glasberg & Moore ERB-rate scale.
    return 21.4 * math.log10(1.0 + 0.00437 * f)


def _erb_to_hz(e):
    return (10.0 ** (e / 21.4) - 1.0) / 0.00437


# ---------------------------------------------------------------------------
# CANDIDATE BASES — centre-frequency layouts.  f_lo/f_hi the analysis band.
# Returned as a plain list of centre frequencies (Hz), ascending.
# ---------------------------------------------------------------------------
F_LO, F_HI = 80.0, 3800.0          # 8 kHz FSDD -> Nyquist 4 kHz; keep margin


def centres_linear(n, f_lo=F_LO, f_hi=F_HI):
    return [f_lo + (f_hi - f_lo) * i / (n - 1) for i in range(n)]


def centres_mel(n, f_lo=F_LO, f_hi=F_HI):
    m_lo, m_hi = _hz_to_mel(f_lo), _hz_to_mel(f_hi)
    return [_mel_to_hz(m_lo + (m_hi - m_lo) * i / (n - 1)) for i in range(n)]


def centres_erb(n, f_lo=F_LO, f_hi=F_HI):
    e_lo, e_hi = _hz_to_erb(f_lo), _hz_to_erb(f_hi)
    return [_erb_to_hz(e_lo + (e_hi - e_lo) * i / (n - 1)) for i in range(n)]


def centres_log(n, f_lo=F_LO, f_hi=F_HI):
    l_lo, l_hi = math.log(f_lo), math.log(f_hi)
    return [math.exp(l_lo + (l_hi - l_lo) * i / (n - 1)) for i in range(n)]


def centres_octave(n, f_lo=F_LO, f_hi=F_HI):
    # Constant-Q / dyadic: centres are equal fractions of an octave apart.
    # log2-equally-spaced is identical in placement to LOG, but we name and treat
    # it as the OCTAVE/constant-Q basis (the dyadic, harmonic-aligned basis).  We
    # keep it distinct so the family spans naming/physics intent even where two
    # layouts coincide numerically; its Q can be set per-band constant downstream.
    l_lo, l_hi = math.log2(f_lo), math.log2(f_hi)
    return [2.0 ** (l_lo + (l_hi - l_lo) * i / (n - 1)) for i in range(n)]


_WARP_FNS = {
    "LINEAR": centres_linear,
    "MEL": centres_mel,
    "ERB": centres_erb,
    "LOG": centres_log,
    "OCTAVE": centres_octave,
}


# Constant-Q factor for the OCTAVE basis: bandwidth = fc / Q.  Q chosen so each
# band spans ~1/3 octave (Q≈4.3) — the standard constant-Q / dyadic tiling, a fixed
# geometric property of the basis, NOT a tuned-for-accuracy parameter.
_OCTAVE_Q = 4.3


def candidate_family(n_bands=32):
    """The candidate basis family the agent composes.  Returns an ordered list of
    (name, centres_hz, bw_mode) where bw_mode is None (ERB-proportional gammatone
    bandwidth, the standard cochlear filter) or a float Q (constant-Q bandwidth =
    fc/Q, the dyadic / octave-tiling filter).  ERB@n_bands with bw_mode=None is the
    existing gammatone front end (baseline).

    The family spans ANATOMICAL (LINEAR, ERB) -> STRUCTURAL (LOG, OCTAVE), MEL
    between.  LINEAR/MEL/ERB/LOG share the standard gammatone bandwidth and differ
    ONLY in centre LAYOUT (the warp); OCTAVE additionally uses constant-Q bandwidth
    so it is a genuinely distinct dyadic basis (not just a relabelled LOG).  All are
    composed owned gammatone+envelope transforms — not fitted."""
    fam = []
    for name in ("LINEAR", "MEL", "ERB", "LOG"):
        fam.append((name, _WARP_FNS[name](n_bands), None))
    fam.append(("OCTAVE", _WARP_FNS["OCTAVE"](n_bands), _OCTAVE_Q))
    return fam


# ---------------------------------------------------------------------------
# BAND TRAJECTORY in a CHOSEN basis — the same machinery as
# scripts.invariant_units_accept.band_trajectory_matrix, but with the basis's
# OWN centre frequencies (and gammatone order = Q control).  I/O boundary only:
# owned gammatone_env per band, duration-LPF, resample to n_frames.
# ---------------------------------------------------------------------------
def band_trajectory_basis(x, fs, centres, n_frames=32, env_cut=50.0, bw_mode=None):
    """frames x bands trajectory in the basis defined by `centres` (Hz) and
    `bw_mode` (None = standard ERB-proportional gammatone bandwidth; a float Q =
    constant-Q bandwidth fc/Q).  Same owned gammatone+envelope front end as the
    default path; only the band centres (and, for OCTAVE, the bandwidth) differ.
    Pure composed transform — no fit, no learned basis."""
    if bw_mode is None:
        envs = [gammatone_env(x, fs, fc, env_cut=env_cut) for fc in centres]
    else:
        envs = [gammatone_env_q(x, fs, fc, bw_mode, env_cut=env_cut)
                for fc in centres]
    # duration LPF per band (same ~80 ms sustained smoothing as the patch path)
    cut = 1000.0 / (2 * math.pi * 80.0)
    tau = 1.0 / (2 * math.pi * cut)
    a = math.exp(-1.0 / (tau * fs))
    smoothed = []
    for env in envs:
        sm = np.empty_like(env)
        acc = 0.0
        for i in range(len(env)):
            acc = a * acc + (1 - a) * env[i]
            sm[i] = acc
        smoothed.append(sm)
    n_src = len(smoothed[0])
    rows = []
    for tf in range(n_frames):
        sp = tf * n_src / n_frames
        i0 = int(sp)
        i1 = min(i0 + 1, n_src - 1)
        frac = sp - i0
        rows.append([buf[i0] * (1 - frac) + buf[i1] * frac for buf in smoothed])
    return np.array(rows, dtype=np.float32)


__all__ = [
    "candidate_family", "band_trajectory_basis",
    "centres_linear", "centres_mel", "centres_erb", "centres_log",
    "centres_octave", "F_LO", "F_HI",
]
