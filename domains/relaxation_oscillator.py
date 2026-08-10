"""relaxation_oscillator — STAGE 2 of the continuous-speech machine.

THE CLOCK DONE RIGHT (clock-is-relaxation-not-sine, oscillator-is-the-runon-
segmenter). The prior entrain_theta (prosody_syllable) is a gently-DRIVEN sine-ish
phase oscillator: the onset NUDGES a continuously-advancing phase. That is the
wrong dynamics for a SEGMENTER — it free-runs through silence and lags onsets.

A RELAXATION oscillator is the right object: an INTEGRATE-AND-FIRE unit. It
integrates the (Stage-1 sharpened) onset energy toward a THRESHOLD; when the
accumulator crosses threshold it FIRES (emits a syllable boundary) and RESETS to
zero. Crucially the onset RESETS THE PHASE directly — a sharp PULSE-COUPLED phase
reset (Mirollo-Strogatz: a strong incoming pulse advances the unit to threshold /
resets it), NOT a gentle sinusoidal drift. The fire events ARE the syllable
boundaries that segment the run-on stream.

DYNAMICS (forward Euler at the onset frame rate). State = accumulator `a` (the
integrated onset energy) + a refractory timer:
    a_{t+1} = a_t * leak + onset_t                 (leaky integrate the onset)
    if a_{t+1} >= THRESHOLD and not refractory:
        FIRE (emit boundary at t); a <- 0; start refractory
A strong onset PULSE drives `a` across threshold immediately (pulse-coupled reset
to fire), so a boundary lands ON the onset, not a quarter-cycle later. The leak
gives the relaxation character (the accumulator decays between onsets so a long
quiet stretch does NOT eventually fire on accumulated noise — no free-run). A
refractory period enforces the minimum inter-syllable interval (a syllable is
~150-400 ms; two onsets closer than the refractory are one syllable).

OWNED DSP, NO net, NO fit, FROZEN constants (the physics of a syllable's rate +
integrate-and-fire dynamics, not swept on any test set). This is the SENSE /
world-adapter TRANSDUCTION: onset envelope -> fire events = boundaries. No graph
state, no agent decisions.

OUTPUT: segment_boundaries(onset) -> the list of fire-event frame indices = the
syllable/unit boundaries that cut the continuous stream into units for Stage 3.
"""
from __future__ import annotations

import numpy as np

# the onset/cochleagram frame rate the Stage-1 front end produces (~100 fps).
_FPS = 100.0
_HOP_MS = 1000.0 / _FPS

# ---- FROZEN integrate-and-fire constants (a syllable's rate + I&F dynamics) ----

_THRESHOLD = 1.0       # the firing threshold on the (normalised) accumulated onset.
#                        With the onset normalised to peak 1 and a per-syllable onset
#                        burst integrating ~1 unit of drive, threshold 1 fires once
#                        per syllable nucleus. A frozen unit threshold.
_LEAK = 0.86           # per-frame leak of the accumulator (relaxation decay). At
#                        100 fps, 0.86 -> ~65 ms time constant: the accumulator bleeds
#                        off between syllables so quiet stretches never fire (no free-
#                        run), but holds across a syllable's onset burst.
_REFRACTORY_MS = 120.0 # minimum inter-fire interval (a syllable is >=~130 ms; 120 ms
#                        refractory rejects double-firing on one onset's sub-peaks).
_PULSE_FRAC = 0.5      # a SHARP onset pulse this large (frac of peak) forces an
#                        immediate phase reset to fire (Mirollo-Strogatz pulse
#                        coupling): a strong onset advances the unit straight to
#                        threshold rather than waiting to integrate. The CLEAN-
#                        sharpened onsets are near-impulses, so this is what carries
#                        the segmentation on the sharp drive.
_MIN_ONSET_FRAC = 0.04 # ignore onset below this frac of peak (noise floor; silence
#                        must not drive the integrator).


def integrate_and_fire(onset, fps=_FPS, threshold=_THRESHOLD, leak=_LEAK,
                       refractory_ms=_REFRACTORY_MS, pulse_frac=_PULSE_FRAC,
                       min_onset_frac=_MIN_ONSET_FRAC, return_trace=False):
    """Relaxation (leaky integrate-and-fire, pulse-coupled) oscillator on the onset
    envelope. Returns the list of FIRE-event frame indices = syllable boundaries.

    onset : (frames,) the Stage-1 SHARPENED onset envelope (>= 0, peak ~1).
    A boundary is emitted when the leaky accumulator crosses `threshold` OR a sharp
    onset pulse (>= pulse_frac of peak) forces an immediate reset-to-fire (Mirollo-
    Strogatz). After a fire the accumulator resets to 0 and a refractory timer blocks
    re-firing for refractory_ms. Owned DSP, no fit."""
    onset = np.asarray(onset, dtype=np.float64)
    n = onset.size
    if n == 0:
        return ([], {"acc": np.zeros(0), "fires": []}) if return_trace else []
    pk = float(onset.max())
    if pk <= 1e-12:
        return ([], {"acc": np.zeros(0), "fires": []}) if return_trace else []
    o = onset / pk                                  # normalise to peak 1
    o = np.where(o < min_onset_frac, 0.0, o)        # noise floor
    refr = max(1, int(round(refractory_ms / (1000.0 / fps))))

    acc = 0.0
    refractory = 0
    fires = []
    acc_tr = np.empty(n)
    for t in range(n):
        if refractory > 0:
            refractory -= 1
            # during refractory the accumulator still leaks but cannot fire (the
            # syllable's own onset burst is one event, not several).
            acc = acc * leak
            acc_tr[t] = acc
            continue
        # leaky integrate the onset drive
        acc = acc * leak + o[t]
        # PULSE-COUPLED reset: a sharp onset pulse forces an immediate fire (the unit
        # is driven straight to threshold by the incoming pulse, Mirollo-Strogatz).
        pulse = o[t] >= pulse_frac
        if acc >= threshold or pulse:
            fires.append(t)
            acc = 0.0
            refractory = refr
        acc_tr[t] = acc
    if return_trace:
        return fires, {"acc": acc_tr, "fires": fires, "onset": o, "fps": fps}
    return fires


def segment_boundaries(onset, fps=_FPS, **kw):
    """The syllable/unit boundaries (fire-event frame indices) that cut a continuous
    onset stream into units. Thin wrapper over integrate_and_fire. Owned DSP."""
    return integrate_and_fire(onset, fps=fps, **kw)


def count_from_onset(onset, fps=_FPS, **kw):
    """Number of fire events = the self-clocked syllable/unit count of the onset
    stream (the relaxation oscillator's count, the analogue of entrain_theta's
    cycle count). Floor at 1 for any non-silent onset (one nucleus rode). Owned."""
    fires = integrate_and_fire(onset, fps=fps, **kw)
    if fires:
        return len(fires)
    return 1 if (np.asarray(onset).size and float(np.asarray(onset).max()) > 0) else 0


def segments_from_boundaries(fires, n_frames):
    """Turn fire-event indices into (start, end) frame SPANS covering the stream.
    Each unit runs from one boundary to the next; the first unit starts at frame 0,
    the last ends at n_frames. A boundary marks the ONSET of a new unit, so the span
    [fire_i, fire_{i+1}) is the i-th unit. Mechanical. Returns list of (s, e)."""
    if n_frames <= 0:
        return []
    if not fires:
        return [(0, n_frames)]
    bounds = sorted(set(fires))
    if bounds[0] != 0:
        bounds = [0] + bounds
    spans = []
    for i in range(len(bounds)):
        s = bounds[i]
        e = bounds[i + 1] if i + 1 < len(bounds) else n_frames
        if e > s:
            spans.append((s, e))
    return spans


__all__ = [
    "integrate_and_fire", "segment_boundaries", "count_from_onset",
    "segments_from_boundaries",
]
