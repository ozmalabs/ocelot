"""voice_impressionist — recover a speaker's SHORT CODE from a small sample by
INVERTING the owned source-filter forward model, so the agent can re-render its
OWN words in that speaker's voice (an impression).

THE FRAMING (engage from the axioms, not the ML default)
==============================================================================
In (G, Γ) a VOICE is a SHORT CODE — a speaker's configuration over the SHARED
generative grammar (the source-filter forward model every voice runs on):

    voice-code = (filter: VTL + formant bandwidths,
                  source: f0, open-quotient, spectral tilt)

"Do an impression from a small sample" is therefore an INVERSE problem: recover
that low-dimensional code by INVERTING the forward model (analysis-by-synthesis),
then re-render. This BEATS neural voice cloning precisely in the FEW-SHOT regime
— the interpolator (VALL-E / YourTTS) must fit a learned manifold and so needs
lots of data; the structure-RECOVERER needs only a small sample because it
recovers a generative CODE, not a surface (ozma_beat_model_asr_at_the_edge).

THE INVERSION IS PURE OWNED DSP (the donkey line)
==============================================================================
Every step is the agent's owned source-filter DSP run BACKWARDS — NO TTS net,
NO neural vocoder, NO speaker-embedding net, NO .fit / gradient / loss / sweep:

  * VTL              : the speaker's mean LPC-formant LEVEL vs the synth's
                       canonical level -> a multiplicative formant scale (a
                       longer tract lowers formants). `_native.lpc_formants_bw`.
  * formant bw       : the median LPC pole BANDWIDTH (the filter sharpness =
                       breathy/soft -> wide). `_native.lpc_formants_bw`.
  * f0               : the speaker's habitual pitch = the glottal CLOCK rate.
                       `_native.f0_autocorr`.
  * source shape     : the LPC RESIDUAL of a real sample IS that speaker's
                       glottal-source estimate; its open-quotient + spectral
                       tilt are read pitch-synchronously off the residual.
                       `_native.lpc_residual` + `_native.glottal_params_from_residual`.

The recovered code is then handed STRAIGHT through to the OWNED projection
forward model (`domains.projection.build_speech_forward`), which already
takes exactly these knobs (f0_hz, vtl_scale, oq, am, ta_frac, BW). The
impressionist adds NO model — it inverts the existing one and re-runs it
forward. This module is a WORLD ADAPTER: it mechanically translates a real
audio signal into the forward model's speaker knobs. No decisions over graph
state, no agent reasoning in Python.

DONKEY AUDIT (file:line)
==============================================================================
  * inversion primitives = owned native DSP, audio_primitives.rs:
      lpc_residual (~:1622), lpc_formants_bw (~:1670), f0_autocorr (~:1720),
      glottal_params_from_residual (~:1770). PyO3 bindings py.rs (~:6067).
  * forward render = the UNCHANGED owned articulatory synth
      domains/projection.py:120 -> Rust Klatt+LF synthesize_formant_track.
  * NO net, NO .fit, NO gradient, NO embedding, NO sweep-to-fit.
  * CortexLoop / solve_for_n / runners agent-runtime UNTOUCHED (only DSP
    primitives + bindings added — the accretion path).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from substrate_rs import _native


# The synth's CANONICAL formant level at vtl_scale=1.0 — the geometric-mean
# formant frequency the OWNED forward model produces for a neutral tract. Used
# as the reference the recovered speaker level is divided against to get VTL.
# Read directly off the forward model's nomogram (config_to_formants of the
# neutral config), NOT a fitted constant.
def _canonical_synth_level():
    """Geometric-mean F1..F3 (log-Hz mean) the forward model emits across the
    digit gestures at vtl_scale=1.0 — the reference level for VTL recovery."""
    from scripts.articulatory_gamma import (
        GESTURE_SCORES, _admissible_trajectory, synth_formant_trajectory,
        SYNTH_FRAMES,
    )
    logs = []
    for word, score in GESTURE_SCORES.items():
        traj, _src, _g = _admissible_trajectory(score, SYNTH_FRAMES)
        form = synth_formant_trajectory(traj)            # (T x 3) Hz
        logs.append(np.mean(np.log(form + 1e-9)))
    return float(np.mean(logs))


_CANON_LOG_LEVEL = None


def canonical_log_level():
    global _CANON_LOG_LEVEL
    if _CANON_LOG_LEVEL is None:
        _CANON_LOG_LEVEL = _canonical_synth_level()
    return _CANON_LOG_LEVEL


@dataclass
class VoiceCode:
    """The recovered speaker SHORT CODE — the config over the shared grammar."""
    f0_hz: float          # habitual pitch (glottal clock)
    vtl_scale: float      # multiplicative formant scale (tract length)
    oq: float             # open quotient (source pulse width / breathiness)
    ta_frac: float        # return-phase / spectral-tilt proxy (softness)
    bw: tuple             # F1..F3 formant bandwidths (filter sharpness)
    tilt_db: float        # source spectral tilt (diagnostic)
    n_voiced: int         # how many voiced frames the recovery used (confidence)

    def forward_kwargs(self):
        """The recovered code as the projection forward model's speaker knobs —
        handed STRAIGHT through to build_speech_forward.forward()."""
        return dict(f0_hz=self.f0_hz, vtl_scale=self.vtl_scale,
                    oq=self.oq, ta_frac=self.ta_frac)


def recover_voice_code(
    sample: np.ndarray,
    fs: int,
    order: int = 12,
    frame: int = 256,
    hop: int = 128,
    pre_emph: float = 0.97,
) -> Optional[VoiceCode]:
    """Recover a speaker's VoiceCode from a SMALL real sample by INVERTING the
    owned source-filter forward model. Pure owned DSP, NO fit:

      1. frame the sample; keep only VOICED frames (f0_autocorr > 0).
      2. per voiced frame: f0 (clock), LPC formants+bandwidths (filter),
         LPC residual -> open-quotient + spectral tilt (source).
      3. aggregate by MEDIAN (robust central estimate, pure selection — not an
         averaged/fitted template): the speaker's habitual code.
      4. VTL = exp(canonical_synth_level - speaker_formant_level) — the
         multiplicative formant scale that maps the synth's neutral tract onto
         the speaker's (a lower speaker level => longer tract => vtl>1).

    Returns a VoiceCode, or None if the sample has too few voiced frames to
    recover a code (the analysis-by-synthesis honest-abstain)."""
    x = np.asarray(sample, dtype=np.float32)
    if x.size < frame + hop:
        return None
    f0s, oqs, tas, tilts = [], [], [], []
    f_levels, bws = [], []
    for st in range(0, x.size - frame, hop):
        fr = x[st:st + frame].tolist()
        f0 = _native.f0_autocorr(fr, fs, 70.0, 400.0, 0.30)
        if f0 <= 0.0:
            continue                                  # unvoiced — skip
        # FILTER: formants + bandwidths (the speaker's vocal-tract code).
        fbw = _native.lpc_formants_bw(fr, fs, order, pre_emph, 150.0, 3600.0, 600.0)
        if len(fbw) >= 6:                             # need at least F1..F3
            fr_freqs = fbw[0::2][:3]
            fr_bws = fbw[1::2][:3]
            f_levels.append(float(np.mean(np.log(np.asarray(fr_freqs) + 1e-9))))
            bws.append([float(b) for b in fr_bws])
        # SOURCE: residual -> open-quotient + spectral tilt (voice identity).
        res = _native.lpc_residual(fr, order, pre_emph)
        gp = _native.glottal_params_from_residual(res, fs, f0)
        f0s.append(f0)
        oqs.append(gp[0])
        tas.append(gp[1])
        tilts.append(gp[2])
    if len(f0s) < 3 or not f_levels:
        return None
    # robust MEDIAN aggregation (selection, not a fitted template).
    f0_med = float(np.median(f0s))
    oq_med = float(np.clip(np.median(oqs), 0.35, 0.85))
    ta_med = float(np.clip(np.median(tas), 0.004, 0.15))
    tilt_med = float(np.median(tilts))
    spk_level = float(np.median(f_levels))
    bw_arr = np.asarray(bws)
    bw_med = tuple(float(np.median(bw_arr[:, i])) for i in range(min(3, bw_arr.shape[1])))
    while len(bw_med) < 3:
        bw_med = bw_med + (bw_med[-1] if bw_med else 100.0,)
    # VTL: map the synth's neutral tract onto the speaker's formant level. The
    # forward model divides formants by vtl_scale, so a speaker whose formants
    # sit BELOW the synth's neutral level (longer tract) wants vtl_scale > 1.
    vtl = float(np.exp(canonical_log_level() - spk_level))
    vtl = float(np.clip(vtl, 0.7, 1.5))
    return VoiceCode(f0_hz=f0_med, vtl_scale=vtl, oq=oq_med, ta_frac=ta_med,
                     bw=bw_med, tilt_db=tilt_med, n_voiced=len(f0s))


def recover_voice_code_v2(
    sample: np.ndarray,
    fs: int,
    order: int = 12,
    frame: int = 256,
    hop: int = 128,
    pre_emph: float = 0.97,
    f0_ceil: float = 290.0,
) -> Optional[VoiceCode]:
    """recover_voice_code with the GENUINE GLOTTAL INVERSE swapped in for the
    saturating full-frame-residual source read.

    Apples-to-apples with `recover_voice_code`: SAME framing / VTL / median
    aggregation / VoiceCode output — the ONLY changes are the two analysis swaps
    the 48 kHz diagnosis named:
      * SOURCE (oq / ta / tilt): `glottal_inverse_iaif` on the RAW frame (IAIF +
        closed-phase covariance LPC + GCI → recovered glottal FLOW) instead of
        `glottal_params_from_residual` on the over-whitened residual (which pins
        oq at the 0.30 floor for every speaker).
      * F0: `f0_cepstral` (octave-robust cepstrum + autocorr octave-reject) with
        a physiological 290 Hz ceiling instead of plain `f0_autocorr` (which
        octave-doubles low-male voices and collapses the per-speaker spread).
    Everything else is byte-identical to recover_voice_code. Pure owned DSP, NO
    net / .fit / gradient / loss / sweep."""
    x = np.asarray(sample, dtype=np.float32)
    if x.size < frame + hop:
        return None
    f0s, oqs, tas, tilts = [], [], [], []
    f_levels, bws = [], []
    for st in range(0, x.size - frame, hop):
        fr = x[st:st + frame].tolist()
        # SPREAD-PRESERVING f0 (octave-robust).
        f0 = _native.f0_cepstral(fr, fs, 70.0, f0_ceil, 0.40)
        if f0 <= 0.0 or f0 >= f0_ceil * 0.97:
            continue                                  # unvoiced / failed read
        # FILTER: formants + bandwidths (unchanged).
        fbw = _native.lpc_formants_bw(fr, fs, order, pre_emph, 150.0, 3600.0, 600.0)
        if len(fbw) >= 6:
            fr_freqs = fbw[0::2][:3]
            fr_bws = fbw[1::2][:3]
            f_levels.append(float(np.mean(np.log(np.asarray(fr_freqs) + 1e-9))))
            bws.append([float(b) for b in fr_bws])
        # SOURCE: the GENUINE glottal inverse on the RAW frame (not the residual).
        gp = _native.glottal_inverse_iaif(fr, fs, f0)
        f0s.append(f0)
        oqs.append(gp[0])
        tas.append(gp[1])
        tilts.append(gp[2])
    if len(f0s) < 3 or not f_levels:
        return None
    f0_med = float(np.median(f0s))
    # NOTE: oq clamp WIDENED to the genuine LF range (the saturating reader pinned
    # at 0.30 so the old [0.35,0.85] clamp was moot; the inverse spans 0.3..0.95).
    oq_med = float(np.clip(np.median(oqs), 0.30, 0.95))
    ta_med = float(np.clip(np.median(tas), 0.002, 0.20))
    tilt_med = float(np.median(tilts))
    spk_level = float(np.median(f_levels))
    bw_arr = np.asarray(bws)
    bw_med = tuple(float(np.median(bw_arr[:, i])) for i in range(min(3, bw_arr.shape[1])))
    while len(bw_med) < 3:
        bw_med = bw_med + (bw_med[-1] if bw_med else 100.0,)
    vtl = float(np.exp(canonical_log_level() - spk_level))
    vtl = float(np.clip(vtl, 0.7, 1.5))
    return VoiceCode(f0_hz=f0_med, vtl_scale=vtl, oq=oq_med, ta_frac=ta_med,
                     bw=bw_med, tilt_db=tilt_med, n_voiced=len(f0s))


def recover_voice_code_v3(
    sample: np.ndarray,
    fs: int,
    order: int = 12,
    frame: int = 256,
    hop: int = 128,
    pre_emph: float = 0.97,
    f0_ceil: float = 290.0,
) -> Optional[VoiceCode]:
    """recover_voice_code_v2 with the SINGLE named fix: the f0 estimator swapped
    from the integer-binned `f0_cepstral` (which clusters same-register males at
    ~120 Hz) to the high-resolution `f0_yin` (cumulative-mean-normalised
    difference + parabolic interpolation → sub-Hz period, resolves 126/132/153).

    Byte-identical to recover_voice_code_v2 EXCEPT the one line that reads f0 (the
    glottal inverse, framing, VTL, median aggregation, VoiceCode output all
    unchanged — apples-to-apples). Pure owned DSP, NO net / .fit / gradient /
    loss / sweep."""
    x = np.asarray(sample, dtype=np.float32)
    if x.size < frame + hop:
        return None
    f0s, oqs, tas, tilts = [], [], [], []
    f_levels, bws = [], []
    for st in range(0, x.size - frame, hop):
        fr = x[st:st + frame].tolist()
        # HIGH-RESOLUTION f0 (YIN + parabolic interp) — the ONLY swap vs v2.
        f0 = _native.f0_yin(fr, fs, 70.0, f0_ceil, 0.10)
        if f0 <= 0.0 or f0 >= f0_ceil * 0.97:
            continue                                  # unvoiced / failed read
        fbw = _native.lpc_formants_bw(fr, fs, order, pre_emph, 150.0, 3600.0, 600.0)
        if len(fbw) >= 6:
            fr_freqs = fbw[0::2][:3]
            fr_bws = fbw[1::2][:3]
            f_levels.append(float(np.mean(np.log(np.asarray(fr_freqs) + 1e-9))))
            bws.append([float(b) for b in fr_bws])
        gp = _native.glottal_inverse_iaif(fr, fs, f0)
        f0s.append(f0)
        oqs.append(gp[0])
        tas.append(gp[1])
        tilts.append(gp[2])
    if len(f0s) < 3 or not f_levels:
        return None
    f0_med = float(np.median(f0s))
    oq_med = float(np.clip(np.median(oqs), 0.30, 0.95))
    ta_med = float(np.clip(np.median(tas), 0.002, 0.20))
    tilt_med = float(np.median(tilts))
    spk_level = float(np.median(f_levels))
    bw_arr = np.asarray(bws)
    bw_med = tuple(float(np.median(bw_arr[:, i])) for i in range(min(3, bw_arr.shape[1])))
    while len(bw_med) < 3:
        bw_med = bw_med + (bw_med[-1] if bw_med else 100.0,)
    vtl = float(np.exp(canonical_log_level() - spk_level))
    vtl = float(np.clip(vtl, 0.7, 1.5))
    return VoiceCode(f0_hz=f0_med, vtl_scale=vtl, oq=oq_med, ta_frac=ta_med,
                     bw=bw_med, tilt_db=tilt_med, n_voiced=len(f0s))


__all__ = ["VoiceCode", "recover_voice_code", "recover_voice_code_v2",
           "recover_voice_code_v3", "canonical_log_level"]
