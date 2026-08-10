"""prototype_shape_space — the SEEDED prototype vocal-tract shape-space + the
per-utterance prototype FORWARD MODEL (pick / adapt / subtract / read the residual).

THE IDEA (memory ozma_forward_model_is_a_prototype_shape): the forward model that
disentangles SPEAKER from WORD is a CLOSE-ENOUGH SHAPE (a prototype), not the exact
speaker. The within-utterance linear subtract (synthesize_gaps_on_audio) reduced to
CMVN 0.570 because it had NO MODEL of the speaker beyond the per-band mean — the
speaker's resonances stay tangled into the word's. A prototype shape PREDICTS the
speaker's contribution to the tangled part and subtracts THAT, leaving the word. We
SEED the shape-space (the innate prior = the settled acoustics of vocal tracts) and
ADAPT on the fly (the learned last mile to THIS talker).

==========================================================================
WHERE EVERY SHAPE PARAMETER COMES FROM — the agent's OWN speech-science (sourced;
NOT hand-authored). Read off seeds/expansions/speech_*_decomposition.json:

 • source_filter_theory (production_principle): "speech = a SOURCE (glottal pulse or
   noise) passed through the vocal tract acting as a linear FILTER. The source sets
   pitch/voicing; the FILTER (tract shape) imposes the resonances (formants) =
   SPECTRAL ENVELOPE. Source and filter are largely independent."
   => the SPEAKER's contribution to the tangled spectrum IS the FILTER ENVELOPE (the
      tract's resonance pattern). That is the thing the prototype predicts + subtracts;
      what is left (the residual) is the source + the word's articulation.

 • vocal_tract_resonance_formants (production_mechanism): "the vocal tract is an
   ACOUSTIC TUBE that resonates at frequencies (F1,F2,F3...) set by its LENGTH +
   constriction pattern; these resonances appear as spectral peaks (formants)."
   => a NEUTRAL (un-constricted, schwa) tube of length L is a quarter-wave resonator
      closed at the glottis, open at the lips: its resonances are
          F_n = (2n-1) * c / (4 L),  n = 1,2,3,...   (c = speed of sound ~ 35000 cm/s)
      This is the SETTLED ACOUSTICS the seed encodes — the prototype shape of "what a
      vocal tract of length L does", before any word-specific constriction.

 • glottal_source (production_mechanism): "its spectrum is broadband, falling
   ~ -12 dB/octave for voicing."
   => the source contributes a SMOOTH SPECTRAL TILT, not resonances. So the seeded
      prototype envelope is (tube resonances) + (a source tilt term) — and the tilt is
      exactly the part adaptation fits per talker (pitch/voice-quality vary the slope).

 • speaker_normalization (perception_mechanism): "factoring out talker differences —
   SCALING for VOCAL-TRACT LENGTH (formant frequencies SHIFT)..."  +  speaker_norm.py
   (the agent's own composed VTL invariant): VTL scales ALL formants by a factor =>
   on a LOG-frequency axis a CONSTANT SHIFT of the whole envelope.
   => the SPAN of prototype shapes is a grid over L (the tube length), because L is the
      agent's named dominant talker factor. The human VTL range is ~13 cm (small
      child / short female tract) to ~18 cm (large adult male tract); the grid spans
      that range. L is the ONE speaker axis; everything else (the word's constriction)
      is what survives the subtract.

 • lack_of_invariance / perception_needs_normalization (the design constraint): "a
   template-per-phoneme recogniser cannot work; invariance must be RECOVERED, not
   assumed" — recovered HERE by predicting + removing the talker's filter envelope.

So the shape-space = a small grid of NEUTRAL-TUBE filter envelopes over L (VTL), each
the quarter-wave resonance set of a tube of that length rendered as a smooth all-pole
envelope on the agent's 32 cochlear bands, plus a source spectral tilt. NOTHING in the
grid is invented — L, the quarter-wave law, the source tilt, and the "subtract the
filter envelope" move are each a named concept the agent holds.

==========================================================================
DONKEY AUDIT:
 • the shapes are DESIGNED FROM the agent's speech-science concepts (each parameter
   sourced above); the GRID is emitted MECHANICALLY (a numpy loop over L), the
   I/O-boundary category — the same as the gammatone front end. No reasoning here.
 • pick = nearest seeded shape to the utterance mean spectrum (an argmin over a fixed
   distance). adapt = a few least-squares steps refining (L, gain, tilt) to minimise
   the residual = OWNED linear algebra (closed-form normal-equations projection),
   NO fit over a dataset, NO trained net, NO learned weight, per-utterance only.
 • subtract = remove the adapted envelope from each frame; read the residual.
 • per-utterance, UNSUPERVISED, NO speaker labels, NO cross-utterance leakage.
 • recognition is the agent's graph-resident DtwTo (in the experiment script).
"""
from __future__ import annotations

import numpy as np

from scripts.mine_whisper import BANDS

# the agent's 32 cochlear band centres (Hz), log-spaced 80..7500 (filter_settings).
_BAND_HZ = np.asarray(BANDS, dtype=np.float64)
_LOG_BAND = np.log(_BAND_HZ)

# c = speed of sound in the vocal tract, cm/s. The standard production constant
# (vocal_tract_resonance_formants: the tube acoustics). 35000 cm/s.
_C_CMPS = 35000.0

# the human VOCAL-TRACT-LENGTH span (cm), the agent's named dominant talker axis
# (speaker_normalization: "scaling for VOCAL-TRACT LENGTH"). ~13 cm (short tract:
# child / small female) .. ~18 cm (long tract: large adult male). A small grid spans
# the human speaker space — the SEED PRIOR that lands in the right region.
_VTL_MIN_CM = 13.0
_VTL_MAX_CM = 18.0
_N_SHAPES = 9                     # grid resolution over L (mechanical; ~0.6 cm steps)

# how many tube resonances to render into the envelope. The neutral tube's first
# ~4 quarter-wave resonances fall within the 80..7500 Hz band range at these lengths
# (F4 of an 18 cm tube ~ 5440 Hz; within range). vocal_tract_resonance_formants names
# F1,F2,F3...; 4 covers the band span.
_N_RESONANCES = 4
# resonance bandwidth as a fraction of centre frequency — the all-pole pole radius.
# A formant's bandwidth is ~5-10% of its centre (a moderately sharp resonance); this
# renders each quarter-wave resonance as a smooth peak, not a delta. 0.08 = 8%.
_BW_FRAC = 0.08


def _tube_resonances(L_cm: float) -> np.ndarray:
    """The quarter-wave resonance frequencies (Hz) of a neutral tube of length L_cm —
    F_n = (2n-1) c / (4 L), the agent's vocal_tract_resonance_formants acoustics.
    Sourced, NOT invented."""
    n = np.arange(1, _N_RESONANCES + 1, dtype=np.float64)
    return (2.0 * n - 1.0) * _C_CMPS / (4.0 * L_cm)


def _allpole_envelope_db(resonances_hz: np.ndarray) -> np.ndarray:
    """Render a set of resonances as a SMOOTH all-pole spectral ENVELOPE on the agent's
    32 cochlear bands (log-magnitude / dB). Each resonance is a 2nd-order all-pole peak
    1/|1 - 2r cos(w-w0) z^-1 + r^2 z^-2| approximated on the log-Hz band axis by a
    Lorentzian in log-frequency (bandwidth = _BW_FRAC of centre). The product of the
    per-resonance peaks IS the tract filter's smooth envelope (source_filter_theory:
    the filter imposes the spectral envelope). Owned DSP — closed-form, no fit."""
    env = np.zeros_like(_LOG_BAND)
    for f0 in resonances_hz:
        if f0 <= 0:
            continue
        lf0 = np.log(f0)
        # half-width in log-Hz: log(f0+bw) - log(f0) ~ bw/f0 = _BW_FRAC (small-x).
        hw = _BW_FRAC
        # Lorentzian peak in log-frequency = the all-pole resonance magnitude (dB).
        env += 1.0 / (1.0 + ((_LOG_BAND - lf0) / hw) ** 2)
    # to a log-magnitude envelope (the domain the cochleagram trajectory uses): the
    # all-pole magnitude is the resonance sum in power; take log for the dB envelope.
    return np.log(env + 1e-3)


def seed_shape_space() -> list[tuple[float, np.ndarray]]:
    """The SEEDED prototype shape-space: a grid over VTL (L) of neutral-tube filter
    envelopes. Returns [(L_cm, envelope_db[32])]. Each envelope is the SPEAKER's
    predicted spectral contribution at that vocal-tract length — the prior shape the
    per-utterance forward model picks from. Emitted MECHANICALLY (the I/O boundary)
    from the sourced acoustics above."""
    Ls = np.linspace(_VTL_MIN_CM, _VTL_MAX_CM, _N_SHAPES)
    space = []
    for L in Ls:
        env = _allpole_envelope_db(_tube_resonances(float(L)))
        space.append((float(L), env.astype(np.float64)))
    return space


# the seeded space, computed once (it is a fixed prior, not per-utterance state).
_SHAPE_SPACE = seed_shape_space()
_SHAPE_ENVS = np.stack([e for _, e in _SHAPE_SPACE], axis=0)   # n_shapes x bands
_SHAPE_LS = np.asarray([L for L, _ in _SHAPE_SPACE])


def _basis(env: np.ndarray) -> np.ndarray:
    """The adaptation BASIS: columns the per-utterance least-squares may scale to bend
    the picked prototype toward THIS talker, WITHOUT letting it absorb the word.
      • the prototype envelope itself (a GAIN on the tract resonance pattern),
      • a constant (DC level — overall loudness/channel),
      • a linear log-frequency TILT (the glottal_source spectral slope ~ -12 dB/oct,
        which varies per talker by voice quality/pitch — the agent's named source term).
    Three columns ONLY — a deliberately LOW-capacity model so adaptation closes the last
    mile to the speaker's smooth envelope but CANNOT fit the word's sharp constriction
    pattern (that survives as the residual). Sourced: gain on the FILTER + the SOURCE
    tilt are exactly the two things source-filter theory says the talker varies."""
    n = env.size
    dc = np.ones(n)
    tilt = (_LOG_BAND - _LOG_BAND.mean())
    tilt = tilt / (np.linalg.norm(tilt) + 1e-9)
    return np.stack([env, dc, tilt], axis=1)            # bands x 3


def _fit_envelope(mean_spec: np.ndarray, env: np.ndarray):
    """ADAPT: least-squares fit of (gain*prototype + dc + tilt) to the utterance MEAN
    spectrum. Closed-form normal equations (owned linear algebra) — NO iteration needed
    for a linear basis, NO fit over data, per-utterance. Returns the adapted predicted
    speaker envelope on the bands + the residual norm of the fit."""
    A = _basis(env)                                     # bands x 3
    # closed-form least-squares coefficients c = (A^T A)^-1 A^T y.
    try:
        coef, *_ = np.linalg.lstsq(A, mean_spec, rcond=None)
    except np.linalg.LinAlgError:
        return env.copy(), float(np.linalg.norm(mean_spec - env))
    pred = A @ coef
    res = float(np.linalg.norm(mean_spec - pred))
    return pred, res


def prototype_forward_model(M: np.ndarray, refine: bool = True,
                            post_cmvn: bool = True):
    """The per-utterance PROTOTYPE FORWARD MODEL on a (frames x bands) cochleagram:

      1. PICK the close-enough seeded shape: the prototype envelope nearest the
         utterance's MEAN log-spectrum (after centring, so the pick is on envelope
         SHAPE not level). Argmin over the seeded VTL grid.
      2. ADAPT it toward THIS talker: least-squares (gain, dc, tilt) fit of the picked
         prototype to the mean spectrum — the last mile (owned linear algebra).
      3. (refine) re-PICK against the adapted fit residual across all shapes, keep the
         best-fitting L — a few steps, still per-utterance least-squares only.
      4. SUBTRACT the adapted predicted speaker envelope from EVERY frame.

    Returns (residual_M[frames x bands], picked_L_cm, fit_residual). The residual is
    the per-frame deviation from the predicted speaker envelope = the WORD's
    constriction trajectory. Owned linear algebra ONLY; per-utterance; no labels."""
    M = np.asarray(M, dtype=np.float64)
    if M.size == 0:
        return M, float("nan"), float("nan")
    # work in the log domain (the cochleagram is magnitude; the envelope is dB) so the
    # multiplicative source x filter becomes an ADDITIVE envelope subtract, exactly the
    # source_filter_theory factoring.
    Mlog = np.log(np.clip(M, 1e-6, None))
    mean_spec = Mlog.mean(axis=0)                       # the utterance's mean spectrum
    mc = mean_spec - mean_spec.mean()                   # centre for the SHAPE pick
    # 1. PICK: nearest seeded envelope shape (centre each seed too -> compare SHAPES).
    seeds_c = _SHAPE_ENVS - _SHAPE_ENVS.mean(axis=1, keepdims=True)
    d = np.linalg.norm(seeds_c - mc[None, :], axis=1)
    best = int(np.argmin(d))
    # 2/3. ADAPT: fit each candidate's (gain,dc,tilt) to the mean spectrum; if refine,
    # keep the L whose adapted fit has the smallest residual (the best-explaining tract
    # length AFTER adaptation — the last mile may reorder the raw pick).
    if refine:
        best_res = np.inf
        pred = None
        for i in range(_SHAPE_ENVS.shape[0]):
            p, r = _fit_envelope(mean_spec, _SHAPE_ENVS[i])
            if r < best_res:
                best_res, pred, best = r, p, i
    else:
        pred, best_res = _fit_envelope(mean_spec, _SHAPE_ENVS[best])
    # 4. SUBTRACT the adapted predicted SPEAKER envelope from every frame -> residual.
    R = Mlog - pred[None, :]
    # post_cmvn: per-band variance-normalise the residual. This makes PROTOTYPE a STRICT
    # SUPERSET of CMVN — CMVN's per-band mean (the pred DC column already removes the
    # mean spectrum) AND variance normalisation, PLUS the removal of the seeded tract
    # RESONANCE SHAPE (the part CMVN's flat mean-subtract leaves tangled in). So any lift
    # over CMVN is credited to the resonance disentanglement, not to a different baseline.
    if post_cmvn:
        sd = R.std(axis=0, keepdims=True)
        R = R / (sd + 1e-6)
    return R, float(_SHAPE_LS[best]), float(best_res)


def prototype_residual_track(x, fs, attrs=None):
    """The agent's residual TRAJECTORY after the prototype forward model — the same
    output shape as agent_frontend.cmvn_track / speaker_residual_track (frames x bands,
    per-frame L2), so the graph-resident DtwTo recognizer aligns it UNCHANGED.

    The cochleagram -> prototype_forward_model (pick the seeded tract shape, adapt it,
    subtract the predicted speaker envelope) -> per-frame L2 of the residual. World-
    adapter feature derivation (mechanical I/O around the owned forward model)."""
    from domains.filter_settings import cochleagram, COCHLEAR_SETTINGS
    attrs = attrs or {}
    _, env_cut, dur_cut, nf = next(s for s in COCHLEAR_SETTINGS if s[0] == "middle")
    env_cut = float(attrs.get("env_cut", env_cut))
    dur_cut = float(attrs.get("dur_cut", dur_cut))
    n_frames = int(attrs.get("n_frames", nf))
    refine = bool(attrs.get("refine", True))
    x = np.asarray(x, dtype=np.float64)
    M = cochleagram(x, fs, env_cut, dur_cut, n_frames)
    if M.size == 0:
        return []
    R, _L, _r = prototype_forward_model(M, refine=refine)
    out = []
    for r in range(R.shape[0]):
        v = R[r]
        nrm = np.linalg.norm(v)
        out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
    return out


__all__ = ["seed_shape_space", "prototype_forward_model",
           "prototype_residual_track", "_tube_resonances", "_allpole_envelope_db"]
