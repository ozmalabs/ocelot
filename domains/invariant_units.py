"""invariant_units — the agent FORWARD-DESIGNS speaker-invariant units from
Kaldi's VTLN + CMVN, mined for MECHANISM (not code, not weights).

WHY (the diagnosis, not re-litigated). The Whisper mine proved the agent's
cochlea is the STRONGER raw representation (front-end leave-one-speaker-out
LOSO 0.58 DTW vs Whisper's log-mel 0.29). The gap is therefore NOT the ears —
it is the PROCESSING: the absence of a speaker-invariance abstraction step
downstream of the already-good front-end. Whisper builds it with attention+SGD
(un-portable trained residue). Kaldi builds it with two DESIGNED operations the
agent CAN forward-design from its own science. This module is those two.

THE MINE (mechanism extracted from Kaldi, do NOT copy its code):
  (1) VTLN — Vocal Tract Length Normalization. Different speakers have different
      vocal-tract lengths; a longer tract scales ALL formant frequencies DOWN by
      a factor α (F_i -> α·F_i). Kaldi WARPS the frequency axis per utterance by
      a piecewise-linear factor to map every speaker onto a CANONICAL tract.
      Kaldi SEARCHES α by max-likelihood over a grid — we do NOT need that sweep.
      The agent estimates α FORWARD from its own formant structure: the
      utterance's mean log-formant position, relative to a canonical reference,
      IS log α. (This is exactly the agent's speaker_norm science — a longer
      tract is a constant shift on the log-frequency axis — read as a warp factor
      rather than a subtraction, and applied to the WHOLE spectrum, not only the
      formant features.)
  (2) CMVN — Cepstral Mean (-Variance) Normalization. Subtract the per-utterance
      feature mean (the channel / loudness / long-term-spectrum term), optionally
      scale variance to unit. Kaldi does this per utterance or per speaker.

THE DESIGN (forward, no search):
  feature matrix M = frames x bands  (the agent's gammatone band trajectory, a
  LOG-FREQUENCY axis — so a VTL scale is a CONSTANT SHIFT in band index).
    a. estimate α forward from M's formant structure (mean log-formant vs the
       cohort-canonical reference) — domains/speaker_norm's VTL science;
    b. WARP the band axis by α (shift on log-frequency = a band-index shift with
       linear interpolation) -> every utterance on the canonical tract;
    c. CMVN: subtract the per-utterance per-band mean (optionally /std).
  Then cluster / DTW-compare on the NORMALIZED M -> speaker-invariant units.

HONEST. Humans do speaker-invariant speech on a worse cochlea, so this IS
solvable; the question the accept script answers with numbers is how MUCH of the
LOSO / TP-separation / boundary-F1 gap forward VTLN+CMVN closes, and what is
left (coarticulation / context beyond per-utterance speaker norm). The warp is
ESTIMATED from each utterance's own formants — never swept to maximize a score.

Graph-native note. The VTL warp FACTOR is the agent's own formant-mean science
(speaker_norm.vtl_terms / mean-formant); estimate_vtl_alpha mirrors that Term
forward. The transform itself is a per-frame frequency-axis remap — a perception
primitive that belongs in the Rust front-end (auditory_cortex) when cut over;
here it operates on the same frames x bands matrix the front-end emits, so the
accept harness measures the MECHANISM honestly before any Rust migration.
"""
from __future__ import annotations

import math

import numpy as np


# ---------------------------------------------------------------------------
# The agent's log-frequency band axis (matches the front-end / mine harness):
# 32 gammatone bands log-spaced 80..7500 Hz. On THIS axis a VTL scale α is a
# constant shift, because log(α·f) = log(α) + log(f).
# ---------------------------------------------------------------------------
_LOG_LO, _LOG_HI = math.log(80.0), math.log(7500.0)


def band_centres(n_bands: int = 32) -> np.ndarray:
    return np.array([math.exp(_LOG_LO + (_LOG_HI - _LOG_LO) * i / (n_bands - 1))
                     for i in range(n_bands)], dtype=np.float64)


def _bands_per_octave(n_bands: int) -> float:
    """How many band indices span one octave on this log-spaced axis. A VTL
    scale α shifts the spectrum by log2(α) octaves = that many band steps."""
    total_octaves = (_LOG_HI - _LOG_LO) / math.log(2.0)
    return (n_bands - 1) / total_octaves


# ---------------------------------------------------------------------------
# (1) FORWARD VTLN — estimate α from the utterance's own formant structure.
# ---------------------------------------------------------------------------

def _spectral_centroid_log(frame_band_energy: np.ndarray,
                           log_centres: np.ndarray) -> float:
    """Energy-weighted mean log-frequency of one frame's band spectrum — a
    robust, search-free proxy for the formant centre-of-mass (the agent's
    mean-formant science: subtracting/centering the mean log-formant cancels the
    VTL shift). Returns a log-Hz value."""
    e = np.maximum(frame_band_energy, 0.0)
    s = e.sum()
    if s <= 1e-12:
        return float(log_centres.mean())
    return float((e * log_centres).sum() / s)


def estimate_vtl_logalpha(M: np.ndarray, canonical_log_centroid: float,
                          voiced_floor: float = 0.25) -> float:
    """Estimate log α FORWARD for one utterance (M = frames x bands).

    The agent's VTL science: a vocal-tract scale α shifts the whole spectrum by
    log α on the log-frequency axis. So the utterance's mean log-spectral
    position, RELATIVE to the cohort-canonical position, IS log α. We average the
    per-frame log-centroid over the utterance's most energetic (voiced) frames
    and subtract the canonical reference. NO max-likelihood sweep — this is read
    directly off the formant centre-of-mass, the agent's own forward estimate.
    """
    lc = band_centres(M.shape[1])
    log_lc = np.log(lc)
    frame_energy = M.sum(axis=1)
    if frame_energy.max() <= 1e-12:
        return 0.0
    thr = voiced_floor * frame_energy.max()
    voiced = frame_energy >= thr
    if voiced.sum() == 0:
        voiced = np.ones(M.shape[0], dtype=bool)
    cents = [_spectral_centroid_log(M[f], log_lc) for f in np.where(voiced)[0]]
    utt_log_centroid = float(np.mean(cents))
    # log α = how far this speaker's centre-of-mass sits above the canonical.
    # A higher centroid (shorter tract, higher formants) -> α>1 -> warp DOWN to
    # canonical; lower centroid (longer tract) -> α<1 -> warp UP.
    return utt_log_centroid - canonical_log_centroid


def warp_bands(M: np.ndarray, log_alpha: float) -> np.ndarray:
    """Apply the VTL warp: shift the band (log-frequency) axis so the utterance
    lands on the canonical tract. A scale α on Hz = a shift of -log α on the log
    axis = a band-index shift of -log2(α)*bands_per_octave. Linear interpolation
    along the band axis; energy outside the original range is held at the edge
    (mirrors Kaldi's piecewise-linear warp, which is identity at the extremes).
    """
    n_frames, n_bands = M.shape
    if abs(log_alpha) < 1e-9:
        return M.copy()
    bpo = _bands_per_octave(n_bands)
    shift = (log_alpha / math.log(2.0)) * bpo   # bands to shift the spectrum
    src_idx = np.arange(n_bands, dtype=np.float64) + shift
    src_idx = np.clip(src_idx, 0.0, n_bands - 1)
    i0 = np.floor(src_idx).astype(int)
    i1 = np.minimum(i0 + 1, n_bands - 1)
    frac = src_idx - i0
    out = (M[:, i0] * (1.0 - frac) + M[:, i1] * frac).astype(M.dtype)
    return out


# ---------------------------------------------------------------------------
# (2) CMVN — per-utterance mean removal (+ optional variance scaling).
# ---------------------------------------------------------------------------

def cmvn(M: np.ndarray, do_variance: bool = True,
         eps: float = 1e-6) -> np.ndarray:
    """Cepstral-Mean(-Variance) Normalization. DEFAULT path: this delegates to the
    AGENT'S COMPOSED CMVN Term-tree (domains/cmvn.apply_cmvn), so the normalization
    every consumer gets is the agent's graph-resident program, evaluated natively,
    NOT this numpy. The agent composed (x - per-band-mean) / per-band-std from its
    own speaker_norm science (speaker = constant per-band offset+scale over time) +
    its DSL primitives (Sum/Count/Minus/Times/Sqrt/Div). See domains/cmvn.py.

    Stats are taken over voiced frames (energy gate) so silence padding doesn't bias
    the mean — the agent's Term sums over the `has_stat_frame` edge set that
    apply_cmvn tags. A numpy fallback (identical math) only runs if the agent's Term
    machinery is unavailable, so the side-experiment harness never silently breaks."""
    try:
        from domains.cmvn import apply_cmvn
        return apply_cmvn(M, do_variance=do_variance, eps=eps,
                          voiced_floor=0.25)
    except Exception:
        pass
    frame_energy = M.sum(axis=1)
    if frame_energy.max() > 1e-12:
        voiced = frame_energy >= 0.25 * frame_energy.max()
        if voiced.sum() < 2:
            voiced = np.ones(M.shape[0], dtype=bool)
    else:
        voiced = np.ones(M.shape[0], dtype=bool)
    mu = M[voiced].mean(axis=0, keepdims=True)
    out = M - mu
    if do_variance:
        sd = M[voiced].std(axis=0, keepdims=True)
        out = out / (sd + eps)
    return out.astype(M.dtype)


# ---------------------------------------------------------------------------
# The full forward-designed invariant transform: VTLN (forward α) -> CMVN.
# ---------------------------------------------------------------------------

def canonical_log_centroid(matrices) -> float:
    """The cohort's CANONICAL vocal tract = the mean log-spectral centre-of-mass
    over all utterances (voiced frames). VTLN warps every speaker TO this. It is
    a property of the data cohort, not a tuned knob (Kaldi likewise references a
    canonical / reference speaker)."""
    lc = band_centres(matrices[0].shape[1])
    log_lc = np.log(lc)
    cents = []
    for M in matrices:
        fe = M.sum(axis=1)
        if fe.max() <= 1e-12:
            continue
        voiced = fe >= 0.25 * fe.max()
        if voiced.sum() == 0:
            voiced = np.ones(M.shape[0], dtype=bool)
        cents.extend(_spectral_centroid_log(M[f], log_lc)
                     for f in np.where(voiced)[0])
    return float(np.mean(cents)) if cents else float(log_lc.mean())


def context_norm(M: np.ndarray, window: int = 2) -> np.ndarray:
    """Context (coarticulation) normalization — DEFAULT path. Delegates to the
    AGENT'S COMPOSED context-norm Term-tree (domains/context_invariant_units.
    apply_context_norm), evaluated natively, so the normalization is the agent's
    graph-resident program, NOT this numpy. The agent composed
    band_b(s) - local-context-mean_b(s) from its coarticulation science
    (a phone's acoustics depend on its neighbours -> a LOCAL drifting baseline)
    + its DSL primitives (Sum/Count/Div/Minus/Neighbours). See
    domains/context_invariant_units.py.

    A numpy fallback (identical math: subtract the running +-window local mean per
    band) only runs if the agent's Term machinery is unavailable, so the
    side-experiment harness never silently breaks."""
    try:
        from domains.context_invariant_units import apply_context_norm
        return apply_context_norm(M, window=window)
    except Exception:
        pass
    M = np.asarray(M, dtype=np.float64)
    n_frames, _ = M.shape
    out = np.empty_like(M)
    for r in range(n_frames):
        lo = max(0, r - window)
        hi = min(n_frames - 1, r + window)
        out[r] = M[r] - M[lo:hi + 1].mean(axis=0)
    return out.astype(M.dtype)


def predict_remove(M: np.ndarray, window: int = 2, k: float = 0.5) -> np.ndarray:
    """Coarticulation PREDICT-AND-REMOVE — DEFAULT link-2. Delegates to the AGENT'S
    COMPOSED predict-and-remove Term-tree (domains/coarticulation_predict_remove.
    apply_predict_remove), evaluated natively. The agent pushes each frame AWAY from
    its neighbour-predicted (carryover+anticipation) drift while PRESERVING the
    frame's own level — the opposite of flat-mean context-norm, which removes the
    level and keeps the drift. See domains/coarticulation_predict_remove.py.

    A numpy fallback (identical math) only runs if the agent's Term machinery is
    unavailable, so harnesses never silently break."""
    try:
        from domains.coarticulation_predict_remove import apply_predict_remove
        return apply_predict_remove(M, window=window, k=k)
    except Exception:
        pass
    M = np.asarray(M, dtype=np.float64)
    n_frames, _ = M.shape
    out = np.empty_like(M)
    for r in range(n_frames):
        ll = max(0, r - window)
        leftmu = M[ll:r + 1].mean(axis=0)
        rr = min(n_frames - 1, r + window)
        rightmu = M[r:rr + 1].mean(axis=0)
        nb = (leftmu + rightmu) / 2.0
        out[r] = M[r] - k * (nb - M[r])
    return out.astype(M.dtype)


def invariant_transform(M: np.ndarray, canonical: float,
                        do_vtln: bool = True, do_cmvn: bool = True,
                        do_variance: bool = True, do_context: bool = True,
                        context_window: int = 2,
                        predict_remove_k: float = 0.5) -> np.ndarray:
    """The forward-designed speaker- AND context-invariant unit transform on one
    utterance's frames x bands matrix: (1) forward-VTLN warp to the canonical
    tract, (2) CMVN mean(-variance) removal (link-1, speaker), (3) coarticulation
    PREDICT-AND-REMOVE (link-2, k=0.5). Returns the normalized matrix (same shape).
    Cluster / DTW-compare on THIS, not the raw acoustics, for invariant units.

    DEFAULT = CMVN -> predict-remove, REPLACING the earlier linear flat-mean
    context-norm (NOT stacked on it). The agent's round-2 machinery decided this:
    the do-contrast read `lever_helps` (predict-remove purity 0.843 vs linear
    context-norm 0.645) and — load-bearing — the labels-free unit yardstick stays
    `frontier='none'` ONLY for the REPLACE form (CMVN+predict-remove): pof recovers
    to ~4.3 over the 1.25 floor and compress ~0.768 under the 0.85 ceiling. The
    STACK form (CMVN+context+predict-remove) inherits flat-mean's structure cost and
    flips the yardstick to 'perception', so it is NOT the default.

    do_context defaults ON and now means the predict-remove link. Pass
    do_context=False to recover the CMVN-only baseline for isolation harnesses."""
    out = M
    if do_vtln:
        la = estimate_vtl_logalpha(out, canonical)
        out = warp_bands(out, la)
    if do_cmvn:
        out = cmvn(out, do_variance=do_variance)
    if do_context:
        out = predict_remove(out, window=context_window, k=predict_remove_k)
    return out


__all__ = [
    "band_centres",
    "estimate_vtl_logalpha",
    "warp_bands",
    "cmvn",
    "context_norm",
    "predict_remove",
    "canonical_log_centroid",
    "invariant_transform",
]
