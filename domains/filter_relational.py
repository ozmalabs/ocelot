"""filter_relational — the agent's PURIFIED FILTER relational representation.

THE INSIGHT (ozma_whisper_message_is_the_filter, GOAL 1): the linguistic message
lives in the FILTER (the vocal-tract resonances / LPC poles), NOT the source.  The
band-energy relational shape (domains/relational_shape) reads the filter MOSTLY but
not PURELY, because gammatone band ENERGY also reflects the EXCITATION spectrum
(harmonic pulse train vs noise) — so it dropped 15.6 pts voiced->whisper even with
the LPC filter held identical.

THE PURIFICATION: read the SAME relational composition (ordinal RANK + whole-unit
SELF-SIMILARITY, verbatim from domains/relational_shape) over the LPC POLE / FORMANT
trajectory (F1/F2/F3 + bandwidths = the vocal-tract resonances) INSTEAD of the 32
band energies.  The pole/formant set is the PURE filter: it is recovered from the LPC
analysis BEFORE the excitation is re-imposed, so it is EXCITATION-INDEPENDENT by
construction.  Discarding the band energy discards the excitation the band rep still
carries.  PREDICTION: the pole/formant relational rep CLOSES the whisper drop
(smaller v->v minus v->whisper gap) because there is no source left in it to lose.

OWNED OPS AT THE I/O BOUNDARY (the filter trajectory):
  * lpc_formants_bw  — per LPC frame, the in-band pole frequencies AND bandwidths
    (F1/F2/F3 + bw1/bw2/bw3) from the LPC pole angles/radii.  This is the speaker's
    vocal-tract filter, the half of the impression the whisper synth already used.
The per-frame formant/bw vector is laid out as a frames x 6 trajectory — the SAME
shape the relational composition consumes (it was written for frames x bands and is
dimension-agnostic).

RELATIONAL COMPOSITION (the agent's owned ops, native eval — UNCHANGED):
  domains.relational_shape.relational_shape over the formant/bw trajectory:
    (1) per-frame ORDINAL RANK of the 6 filter dimensions (which resonance/bandwidth
        is higher than which) — invariant to any order-preserving talker transform of
        the filter coordinates;
    (2) WHOLE-UNIT SELF-SIMILARITY: each frame's rank-agreement with the unit's own
        phase anchors — a relation internal to the unit.
NO new agent code: the composition is reused verbatim; only the SUBSTRATE it reads
(filter poles, not band energy) changes.  numpy appears only at the I/O boundary
(LPC frame -> formant vector), exactly as the band path does.

DISCIPLINE: LPC formant extraction = owned ops at the I/O boundary; the relational
composition + recognition distance stay native (substrate.evaluate / DtwTo).
"""
from __future__ import annotations

import numpy as np

import substrate_rs._native as N
from domains.relational_shape import relational_shape


# LPC framing — IDENTICAL to scripts/voiced_whisper_probe.py (8 kHz FSDD), so the
# filter trajectory is read off the SAME poles the whisper synth held fixed.
LPC_ORDER = 14
LPC_FRAME = 200          # 25 ms @ 8 kHz
LPC_HOP = 80             # 10 ms
LPC_PE = 0.97
N_FORMANT = 3            # F1/F2/F3 (+ their bandwidths) = the in-band vocal-tract poles
F_LO = 150.0
F_HI = 3800.0
BW_MAX = 600.0
# Near-silent frames carry no reliable poles.  The gate is RELATIVE to each clip's
# own energy (a fraction of its median frame RMS), NOT an absolute level: voiced and
# synth-whisper have the SAME overall RMS but different per-frame energy
# distributions (a pulse train concentrates energy where noise spreads it), so an
# ABSOLUTE gate truncates the whisper trajectory far harder than the voiced one — a
# serialization-dependent artifact that would unfairly shorten the whisper unit.  A
# per-clip relative gate keeps the same proportion of each unit's frames regardless
# of source.  This is I/O-boundary level normalization, not a fitted parameter.
RMS_GATE_FRAC = 0.15     # keep frames above 15% of the clip's median frame RMS


def formant_trajectory(x, fs):
    """frames x 6 PURE-FILTER trajectory: per LPC frame, [F1,F2,F3, bw1,bw2,bw3] from
    the LPC pole frequencies/bandwidths (lpc_formants_bw).  Excitation-independent by
    construction.  Owned-op I/O-boundary translation only — no decision logic."""
    x = np.asarray(x, dtype=np.float32)
    starts = list(range(0, len(x) - LPC_FRAME, LPC_HOP))
    if len(starts) < 2:
        return None
    frame_rms = np.array([float(np.sqrt((x[i:i + LPC_FRAME] ** 2).mean()))
                          for i in starts], dtype=np.float32)
    med = float(np.median(frame_rms[frame_rms > 0])) if np.any(frame_rms > 0) else 0.0
    gate = RMS_GATE_FRAC * med
    rows = []
    for i, rms in zip(starts, frame_rms):
        if rms < gate:
            continue
        fr = x[i:i + LPC_FRAME]
        fb = N.lpc_formants_bw(fr.tolist(), int(fs), LPC_ORDER, LPC_PE,
                               F_LO, F_HI, BW_MAX)
        # lpc_formants_bw returns flat [f0,bw0, f1,bw1, ...] ascending by freq.
        freqs = [fb[2 * k] for k in range(len(fb) // 2)]
        bws = [fb[2 * k + 1] for k in range(len(fb) // 2)]
        freqs = (list(freqs) + [0.0, 0.0, 0.0])[:N_FORMANT]
        bws = (list(bws) + [0.0, 0.0, 0.0])[:N_FORMANT]
        rows.append(list(freqs) + list(bws))
    if len(rows) < 2:
        return None
    return np.array(rows, dtype=np.float32)


# ---------------------------------------------------------------------------
# CEPSTRAL-ENVELOPE FORMANT TRAJECTORY — the BETTER, source-robust estimator.
#
# Homomorphic deconvolution (the agent's named gap: cepstral liftering / cepstrum /
# homomorphic deconvolution): a speech frame is SOURCE * FILTER (convolution); in the
# log-spectral domain that is an ADDITION the cepstrum separates by quefrency.  The
# LOW-quefrency cepstrum is the smooth FILTER ENVELOPE, the HIGH-quefrency is the
# SOURCE comb (voiced) / noise (whisper).  Liftering to the envelope and peak-picking
# THAT reads formants with the excitation divided out — robust whether the source was
# a harmonic pulse train or noise.  Native op cepstral_formants (authored in Rust,
# audio_primitives::cepstral_formants), same flat [f,bw,...] layout as lpc_formants_bw
# so it is a DROP-IN replacement on the filter path.  Owned-op I/O boundary only.
# ---------------------------------------------------------------------------
CEP_LIFTER = 24          # cepstral cutoff quefrency: keep the envelope, drop the comb
CEP_F_LO = 250.0         # formants do not sit below ~250 Hz; avoids the DC/tilt bump


def cepstral_formant_trajectory(x, fs):
    """frames x 6 PURE-FILTER trajectory via CEPSTRAL ENVELOPE peaks:
    [F1,F2,F3, bw1,bw2,bw3] read off the liftered (source-removed) log-spectral
    envelope per frame.  Same framing/gating as the LPC trajectory so the only change
    is the ESTIMATOR (envelope peaks vs all-pole roots).  Owned-op boundary only."""
    x = np.asarray(x, dtype=np.float32)
    starts = list(range(0, len(x) - LPC_FRAME, LPC_HOP))
    if len(starts) < 2:
        return None
    frame_rms = np.array([float(np.sqrt((x[i:i + LPC_FRAME] ** 2).mean()))
                          for i in starts], dtype=np.float32)
    med = float(np.median(frame_rms[frame_rms > 0])) if np.any(frame_rms > 0) else 0.0
    gate = RMS_GATE_FRAC * med
    rows = []
    for i, rms in zip(starts, frame_rms):
        if rms < gate:
            continue
        fr = x[i:i + LPC_FRAME]
        fb = N.cepstral_formants(fr.tolist(), int(fs), CEP_F_LO, F_HI,
                                 N_FORMANT, CEP_LIFTER)
        freqs = [fb[2 * k] for k in range(len(fb) // 2)]
        bws = [fb[2 * k + 1] for k in range(len(fb) // 2)]
        freqs = (list(freqs) + [0.0, 0.0, 0.0])[:N_FORMANT]
        bws = (list(bws) + [0.0, 0.0, 0.0])[:N_FORMANT]
        rows.append(list(freqs) + list(bws))
    if len(rows) < 2:
        return None
    return np.array(rows, dtype=np.float32)


def cepstral_filter_relational(x, fs, n_anchors=6):
    """(C) RELATIONAL FILTER/CEPSTRAL — the whole-unit relational shape over the
    cepstral-envelope formant trajectory (source-removed).  Same relational machinery,
    a cleaner/more-source-robust filter substrate than the LPC poles."""
    M = cepstral_formant_trajectory(x, fs)
    if M is None or len(M) < 2:
        return None
    return relational_shape(M, n_anchors=n_anchors)


def filter_relational(x, fs, n_anchors=6):
    """(C) RELATIONAL FILTER/POLE — the agent's whole-unit relational shape composed
    over the PURE FILTER (formant/pole) trajectory, evaluated natively.  Same
    relational machinery as the band-energy rep, different (excitation-free)
    substrate."""
    M = formant_trajectory(x, fs)
    if M is None or len(M) < 2:
        return None
    return relational_shape(M, n_anchors=n_anchors)


__all__ = ["formant_trajectory", "filter_relational",
           "cepstral_formant_trajectory", "cepstral_filter_relational"]
