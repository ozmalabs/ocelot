"""projection — a GENERIC, REUSABLE projection function: config <-> signal.

THE ABSTRACTION (modality-agnostic; this is NOT a speech trick)
==============================================================================
A perceiving/acting agent has an INTERNAL representation (a configuration: a
point/trajectory/structure in some low-dimensional config space the agent
reasons over) and an EXTERNAL signal (the raw thing in the world — audio
samples, pixels, motor torques, bytes). A PROJECTION is the single map that
ties the two together, and it is BIDIRECTIONAL:

    project(config) -> signal      FORWARD   (generate / render / speak / act)
    invert(signal)  -> config      INVERSE   (perceive / parse / recognise)

These are the SAME function read in two directions. Perception is inverting the
forward model; generation is running it forward. The agent that owns one owns
the other — they MUST be the same map, or what it says is not what it hears
(ozma_order_n_analysis_by_synthesis: "perceive by inverting the forward model;
say it to yourself"). A forward/inverse pair built from two DIFFERENT maps is a
bug — the renderer and the sensor would disagree, and a closed sensorimotor
loop (act -> sense -> recognise) could never ground.

WHY GENERIC / REUSABLE (not a speech-specific synthesis trick)
==============================================================================
Nothing in the interface mentions speech, formants, or audio. The contract is
purely: a `forward` map config->signal, an `invert` map signal->config (via the
agent's native recognition Terms), and a `decode` that names a config from a
finite vocabulary. ANY modality with a renderer/sensor pair instantiates it:

  * SPEECH   : config = articulatory gesture trajectory; signal = audio.
               forward = source-filter synthesis; invert = formant-DTW + d_A.
  * VISION   : config = shape/pose/scene graph; signal = pixels.
               forward = a renderer; invert = recognition over the same model.
  * MOTOR    : config = joint trajectory; signal = sensed motion/contact.
               forward = the body's dynamics; invert = proprioceptive parse.
  * CODEC    : config = a structured description; signal = a byte stream.
               forward = encode; invert = decode.

The renderer/sensor pair "for any modality" — the articulatory gesture->formant
model is just the SPEECH INSTANCE plugged into this interface. The agent's
recognition is ALWAYS the inverse of the SAME forward model it generates with.

DONKEY AUDIT
==============================================================================
  * The Projection holds two callables the CALLER supplies: a `forward`
    (config -> signal) and an `invert` (signal -> config-name, via the agent's
    native recognition Terms). This module owns NO model — it is the interface +
    the loop plumbing (a world-adapter contract). No net, no .fit, no gradient.
  * The SPEECH instance's forward is the agent's OWNED articulatory source-filter
    forward model (scripts.articulatory_gamma config_to_formants + the Rust
    Klatt voicebox synthesize_formant_track). Its invert is the native cutover
    recognition (the d_A Argmin / formant-DTW Terms) — the SAME forward model run
    backwards. No TTS net.
  * CortexLoop / solve_for_n are untouched; this is adapter glue, not agent
    decisions (the decisions are the native Terms invert() calls).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

import numpy as np


# ==============================================================================
#  The GENERIC interface.
# ==============================================================================

@dataclass
class Projection:
    """A bidirectional config <-> signal map (modality-agnostic).

    forward : config -> signal   (the renderer / actuator; the agent's owned
              forward model run FORWARD — generation).
    inverse : signal -> config   (the sensor / recogniser; the SAME forward
              model run BACKWARDS — perception). Returns the agent's internal
              config (e.g. a recognised vocabulary name), via native Terms.

    The contract is the whole point: forward and inverse are two directions of
    ONE map. A loop project()->invert() should return the config you started
    from when the projection is faithful — that round-trip IS the grounding
    test, in any modality.
    """
    name: str
    forward: Callable[..., np.ndarray]
    inverse: Callable[[np.ndarray], Any]
    # optional knobs a renderer accepts (e.g. speaker params) — opaque to the
    # interface, passed straight through to forward().
    forward_kwargs: Optional[dict] = None

    def project(self, config: Any, **kwargs) -> np.ndarray:
        """FORWARD: config -> signal. Generation / render / speak / act."""
        kw = dict(self.forward_kwargs or {})
        kw.update(kwargs)
        return self.forward(config, **kw)

    def invert(self, signal: np.ndarray) -> Any:
        """INVERSE: signal -> config. Perception / parse / recognise."""
        return self.inverse(signal)

    def round_trip(self, config: Any, **kwargs) -> Any:
        """project then invert — the grounding round-trip. Returns the config the
        inverse recovers from the agent's own generated signal. config==round_trip
        is the loop closing, in ANY modality."""
        return self.invert(self.project(config, **kwargs))


# ==============================================================================
#  The SPEECH instance of the generic projection.
# ==============================================================================
#  config = a digit word-name -> its articulatory gesture trajectory (the agent's
#           owned phonetics, GESTURE_SCORES). project() runs the OWNED articulatory
#           source-filter forward model FORWARD to audio. invert() runs the SAME
#           forward model BACKWARDS (the native cutover recognition: formant-DTW +
#           d_A Argmin Terms) to recover the word-name. ONE model, two directions.

def _rust(sub):
    return sub._inner if hasattr(sub, "_inner") else sub


# the native (Rust) classical-DSP primitives — module-level functions, NOT Substrate
# methods. The A-by-S correction is built entirely from these owned primitives.
import substrate_rs._native as _N


# ==============================================================================
#  W5 — the ANALYSIS-BY-SYNTHESIS formant correction, wired into the DIGIT path.
# ==============================================================================
#  The proven W5 result (scripts/synth_formant_fix.py, VCTK voice-identity): the
#  RENDERED formants do NOT re-analyse to the INTENDED formant print — the
#  source-filter forward model drifts (worst at low f0). The fix is a deterministic
#  A-by-S correction: render -> RE-ANALYSE the rendered formants (lpc_formants_bw,
#  the SAME analyser the inverse uses) -> measure the DRIFT from the intended
#  targets -> SET the synthesised poles to the values that make the rendered
#  formants LAND on the intended targets (the owned native primitive
#  lpc_formant_set_track), iterated as a damped, best-tracked fixed point.
#
#  In the digit path the INTENDED targets are the agent's OWN articulatory formant
#  trajectory `scaled` (config_to_formants, post VTL + babble offset), NOT a real
#  speaker's print: the loop drives "what it speaks" to re-analyse to "what it
#  intended". MEASURED RESULT (docs/w5_digit_consolidation.md): it DOES make the
#  digit formants re-analyse to target (F1F2 drift 621->243 Hz, 40/40 tokens) BUT
#  REGRESSED the Stage-4 closure (OLD word-discriminative ear 62.5%->20.0%; the
#  invariant ear was UNMOVED at 17.5%). Hence axs_correct DEFAULTS OFF — opt-in only.
#
#  DONKEY: owned classical DSP only — lpc_coeff_track / lpc_bw_expand_track /
#  lpc_residual_track / lpc_formant_set_track / lpc_cross_resynth / lpc_formants_bw,
#  all native Rust primitives. Python is world-adapter glue: marshal arrays, call
#  the native primitives, run the deterministic fixed point. NO net, NO .fit, NO
#  gradient, NO loss, NO sweep-to-fit, NO decision over graph state.

# native A-by-S knobs — fixed owned constants (NOT tuned to any score; the loop's
# only objective is the rendered formants converging to the INTENDED targets).
_AXS_ORDER = 18           # LPC order for the re-analysis / set-track at fs<=8k
_AXS_FRAME = 200          # analysis frame (samples) — ~25 ms at 8 kHz
_AXS_HOP = 80             # hop (samples) — ~10 ms at 8 kHz
_AXS_PE = 0.97            # pre-emphasis
_AXS_BW_FLOOR = 60.0      # bandwidth floor (Hz) for the recovered poles
_AXS_NFORMANT = 3         # F1..F3 — the digit cue dims
_AXS_BW_ALPHA = 0.6       # bandwidth blend toward target
_AXS_WARP_LO = 150.0      # in-band frequency window for the pole set
_AXS_WARP_HI = 3800.0
_AXS_ITERS = 5            # damped fixed-point passes
_AXS_LAM = 0.7            # damped inverse step (best-tracked)


def _resample_targets(form, n_frames):
    """Resample an intended (T x 3) Hz formant trajectory onto an `n_frames`-long
    per-LPC-frame grid (monotone linear). Mechanical array reshape."""
    T = form.shape[0]
    if n_frames <= 0:
        return form
    if T == n_frames:
        return form
    src = np.linspace(0.0, 1.0, T)
    dst = np.linspace(0.0, 1.0, n_frames)
    out = np.zeros((n_frames, form.shape[1]), dtype=np.float64)
    for k in range(form.shape[1]):
        out[:, k] = np.interp(dst, src, form[:, k])
    return out


def _measure_rendered_formants(rust, audio, fs, n_frames):
    """Re-analyse the rendered audio's per-frame F1..F3 (Hz) on the LPC frame grid,
    using the SAME native analyser the inverse uses (lpc_formants_bw). Returns an
    (n_frames x 3) Hz array (NaN where a frame has < 3 in-band formants). `rust` is
    accepted for signature symmetry; the LPC primitives are module-level natives."""
    out = np.full((n_frames, _AXS_NFORMANT), np.nan, dtype=np.float64)
    a = np.asarray(audio, dtype=np.float32)
    half = _AXS_FRAME // 2
    for fi in range(n_frames):
        pos = fi * _AXS_HOP
        lo = max(0, pos - half)
        hi = min(len(a), lo + _AXS_FRAME)
        if hi - lo < _AXS_ORDER + 2:
            continue
        fbw = _N.lpc_formants_bw(
            a[lo:hi].tolist(), int(fs), _AXS_ORDER, _AXS_PE,
            _AXS_WARP_LO, _AXS_WARP_HI, 700.0)
        ff = list(fbw[0::2])
        if len(ff) >= _AXS_NFORMANT:
            out[fi, :] = ff[:_AXS_NFORMANT]
    return out


def _axs_render(rust, audio0, fs, intended, bw_hz):
    """The native A-by-S formant correction for the digit path. `audio0` is the raw
    Klatt-synth output; `intended` is the (T x 3) Hz formant trajectory the synth
    aimed at; `bw_hz` is the per-formant target bandwidth (Hz). Drives the rendered
    formants to re-analyse to `intended` by setting the synthesised poles to the
    drift-compensated absolute targets (lpc_formant_set_track), re-synthesising with
    the rendered residual (lpc_cross_resynth), and iterating a damped best-tracked
    fixed point. Returns (corrected_audio, final_drift_hz)."""
    audio0 = np.asarray(audio0, dtype=np.float32)
    n = len(audio0)
    if n < _AXS_FRAME + _AXS_HOP:
        return audio0, float("nan")
    # the rendered residual (excitation) is fixed — only the filter poles are warped.
    res = _N.lpc_residual_track(audio0.tolist(), _AXS_ORDER, _AXS_FRAME, _AXS_HOP, _AXS_PE)
    a0 = _N.lpc_coeff_track(audio0.tolist(), _AXS_ORDER, _AXS_FRAME, _AXS_HOP, _AXS_PE)
    a0 = _N.lpc_bw_expand_track(a0, _AXS_ORDER, int(fs), _AXS_BW_FLOOR)
    stride = _AXS_ORDER + 1
    n_frames = len(a0) // stride
    if n_frames < 1:
        return audio0, float("nan")
    tgt = _resample_targets(np.asarray(intended, dtype=np.float64), n_frames)  # (n_frames x 3)
    bw = np.asarray(bw_hz, dtype=np.float64).reshape(-1)[:_AXS_NFORMANT]
    bw_flat = [float(bw[k]) for _ in range(n_frames) for k in range(_AXS_NFORMANT)]
    # current per-frame absolute frequency targets we feed the pole-set primitive;
    # start AT the intended formants, then pre-distort to compensate the measured drift.
    cur = tgt.copy()
    best_drift = float("inf")
    best_audio = audio0
    for _ in range(_AXS_ITERS):
        tf_flat = [float(cur[fi, k]) if cur[fi, k] > 0 else 0.0
                   for fi in range(n_frames) for k in range(_AXS_NFORMANT)]
        a_warp = _N.lpc_formant_set_track(
            a0, _AXS_ORDER, int(fs), tf_flat, bw_flat,
            _AXS_NFORMANT, _AXS_BW_ALPHA, _AXS_WARP_LO, _AXS_WARP_HI)
        y = np.array(_N.lpc_cross_resynth(a_warp, list(res), _AXS_ORDER, _AXS_HOP, _AXS_PE),
                     dtype=np.float32)
        if len(y) >= n:
            y = y[:n]
        else:
            y = np.concatenate([y, np.zeros(n - len(y), dtype=np.float32)])
        peak = float(np.max(np.abs(y))) if y.size else 0.0
        if peak > 1.0:
            y = y / peak
        # RE-ANALYSE the corrected render and measure the drift from the INTENDED targets.
        meas = _measure_rendered_formants(rust, y, fs, n_frames)
        err = tgt - meas                                   # (n_frames x 3) Hz
        valid = np.isfinite(err)
        drift = float(np.sqrt(np.nanmean((err[:, :2]) ** 2))) if valid[:, :2].any() else float("nan")
        if np.isfinite(drift) and drift < best_drift:
            best_drift, best_audio = drift, y
        # damped inverse step: pre-distort the synth target by the measured drift so
        # the NEXT render lands on the intended formant (deterministic fixed point).
        step = np.where(valid, _AXS_LAM * err, 0.0)
        cur = cur + step
    return best_audio, best_drift


def build_speech_forward(AG):
    """Build the SPEECH forward map config(word) -> audio signal, from the agent's
    OWNED articulatory forward model. For a word, synthesise its admissible gesture
    trajectory (Γ-feasible config path), project config -> formant-Hz trajectory +
    voicing via the owned source-filter nomogram, and render to audio with the Rust
    Klatt voicebox (synthesize_formant_track). NO TTS net, NO .fit. Returns a
    closure forward(word, sub, fs, dur_s, f0_hz, ...) -> np.float32 audio."""
    from scripts.articulatory_gamma import (
        GESTURE_SCORES, _admissible_trajectory, synth_formant_trajectory,
        synth_voicing, SYNTH_FRAMES,
    )

    # natural formant bandwidths (Hz), F1..F3 — fixed phonetic constants, not fitted.
    BW = (80.0, 100.0, 130.0)

    def forward(word, sub, fs=8000, dur_s=0.4, f0_hz=120.0, vtl_scale=1.0,
                oq=0.6, am=0.0, ta_frac=0.01, formant_offset=None, bw=None,
                axs_correct=False):
        score = GESTURE_SCORES.get(word.lower())
        n_out = max(int(dur_s * fs), 1)
        if score is None:
            return np.zeros(n_out, dtype=np.float32)
        # config trajectory (Γ-admissible) -> formant-Hz trajectory + voicing.
        traj, src_seq, _gamma = _admissible_trajectory(score, SYNTH_FRAMES)
        form = synth_formant_trajectory(traj)            # (T x 3) Hz
        voi = synth_voicing(src_seq)                     # (T,)
        T = form.shape[0]
        # the per-formant BANDWIDTHS (filter sharpness): the speaker's recovered
        # formant bandwidths when the impressionist supplies them (a breathy/soft
        # voice has WIDE formant bandwidths), else the natural phonetic constants.
        bw_use = tuple(bw) if bw is not None else BW
        # babble-refine knob: a per-formant log-Hz offset on the synthesised target
        # (the owned articulatory adjustment the babble loop accepts iff the hear-self
        # mismatch drops). Multiplicative in Hz == additive in log-Hz. Default = none.
        if formant_offset is not None:
            fo = np.asarray(formant_offset, dtype=np.float64).reshape(1, -1)
            form = form * np.exp(fo)
        # VTL is a multiplicative formant scale (the speaker knob): a longer tract
        # (vtl>1) lowers formants. Apply it to the Hz the renderer receives.
        scaled = form / max(vtl_scale, 1e-3)
        formants_flat = [float(v) for row in scaled for v in row]
        bw_flat = [float(bw_use[i % len(bw_use)]) for _ in range(T) for i in range(3)]
        # amplitude envelope: full during voiced/fricative, dip in pure silence.
        amp = [1.0] * T
        voiced = [float(v) for v in voi]
        rust = _rust(sub)
        audio_bytes = rust.synthesize_formant_track(
            formants_flat, bw_flat, voiced, amp, 3, n_out, int(fs),
            float(f0_hz), float(oq), float(am), float(ta_frac))
        audio = np.frombuffer(audio_bytes, dtype=np.float32).copy()
        # W5 — the A-by-S formant correction (owned native DSP): drive the rendered
        # formants to RE-ANALYSE to the INTENDED targets `scaled`. It DOES make the
        # digit formants re-analyse to target (F1F2 drift 621->243 Hz, all 40 tokens;
        # docs/w5_digit_consolidation.md), BUT it is DEFAULT-OFF: measured on the
        # Stage-4 loop it REGRESSED the closure (OLD word-discriminative ear
        # 62.5%->20.0%, the LPC pole-set + cross-resynth strips the spectral detail
        # that ear reads; the invariant ear was UNMOVED at 17.5%, the hoped-for rise
        # did not occur). The loop closes via FUSION, so this is opt-in only.
        if axs_correct:
            try:
                corrected, _drift = _axs_render(rust, audio, fs, scaled, bw_use)
                if corrected is not None and len(corrected) == len(audio):
                    audio = np.asarray(corrected, dtype=np.float32)
            except Exception:
                pass
        return audio

    return forward


def build_speech_invert(recogniser, prong="fused"):
    """Build the SPEECH inverse map signal(audio) -> config(word-name), from the
    agent's NATIVE cutover recognition (the d_A Argmin / formant-DTW / fusion
    Terms). This is the SAME articulatory forward model run BACKWARDS: the native
    cognition scores each word by how well its admissible synthesised trajectory
    (the forward model) matches the observed shadow, and Argmins. `recogniser` is
    a NativeRecogniser (its .recognise(sig) returns the per-prong predictions).
    Returns invert(audio) -> word-name or None."""
    def invert(audio):
        out = recogniser.recognise(np.asarray(audio, dtype=np.float64))
        if out is None:
            return None
        return out.get(prong)

    return invert


def speech_projection(AG, recogniser, prong="fused"):
    """The SPEECH instance of the generic Projection: forward = owned articulatory
    source-filter synthesis; invert = the native cutover recognition (the inverse
    of the SAME forward model). Returns a Projection."""
    fwd = build_speech_forward(AG)
    inv = build_speech_invert(recogniser, prong=prong)
    return Projection(name="speech", forward=fwd, inverse=inv)


__all__ = [
    "Projection", "build_speech_forward", "build_speech_invert",
    "speech_projection",
]
