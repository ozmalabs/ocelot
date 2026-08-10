"""learned_voice_shape — a LEARNED per-voice template library (the forward model),
and predict-subtract recognition on the residual.

THE MOVE (ozma_bootstrap_forward_model_from_generation, the CLEAN path). The
seeded neutral-tube prototype was OFF-MANIFOLD and peeled the word
(docs/seeded_prototype_loso.md — KILL). The diagnosis: the speaker template must be
LEARNED from real-speech-like audio, not guessed. Here a trained TTS is the WORLD
(it generates on-manifold diverse "speakers"); the agent LEARNS its own voice-shape
library from that world, and recognises a test utterance by SUBTRACTING the nearest
learned shape's predicted contribution and aligning the residual with its UNCHANGED
DtwTo recognizer.

WHAT A LEARNED VOICE-SHAPE IS. For one voice (a generated speaker, or a real train
speaker in the control), pool the per-band frames of ALL that voice's utterances into
one (frames x bands) matrix on the SOURCE-NORMALISED cochleagram (per-band unit
variance — the SAME normalisation CMVN applies). The voice-shape is then:
  · the MEAN frame over the pool (the rank-0 constant the voice imposes on every
    frame of every word it says = the speaker's persistent spectral signature), AND
  · the top-k PRINCIPAL band-space directions of the centred pool (the remaining
    structure CONSISTENT across the voice's words = the voice's formant-space basis).
This is the SAME mean+SVD operation that — applied WITHIN one utterance — reduced to
CMVN (synthesize_gaps), but learned ACROSS a voice's MANY utterances over MANY words.
Because it is pooled across DIFFERENT words, the word-specific articulation averages
out and what survives IS the per-voice constant — a genuine template the per-utterance
mean cannot be (the per-utterance mean still carries that utterance's single word).

PREDICT-SUBTRACT. For a test utterance: source-normalise its cochleagram, PICK the
nearest learned voice-shape (argmin over the library of the distance from the
utterance mean frame to each shape's mean frame), then for EACH frame SUBTRACT the
picked shape's predicted contribution = its mean frame PLUS the frame's projection
onto the shape's principal band-space directions. The residual per-frame trajectory
is the WORD with the voice's persistent + consistent structure removed; the agent's
unchanged DtwTo aligns it.

DONKEY BOUNDARY (audited). TTS = the WORLD (data the agent hears) — only used to
generate the band frames the shapes are learned FROM; it is NEVER inverted, NEVER
used for recognition. The voice-shape library = LEARNED by OWNED LINEAR ALGEBRA ONLY
(np.mean + np.linalg.svd + projection); NO net, NO gradient, NO trained weight, NO
fit-to-labels (the SVD is the closed-form principal subspace of each voice's OWN pooled
frames). Recognition = the agent's graph-resident DtwTo (unchanged). This module is
world-adapter feature derivation: it turns audio into the residual trajectory the
agent's recognizer reads; it makes NO decision over graph state.
"""
from __future__ import annotations

import numpy as np

from domains.filter_settings import cochleagram, COCHLEAR_SETTINGS

_MIDDLE = next(s for s in COCHLEAR_SETTINGS if s[0] == "middle")


def _coch(x, fs):
    """The middle-setting cochleagram (frames x bands) — the SAME front-end the CMVN
    baseline reads. Pure boundary DSP."""
    _, env_cut, dur_cut, nf = _MIDDLE
    return cochleagram(np.asarray(x, dtype=np.float64), fs, env_cut, dur_cut, nf)


def _source_normalise(M):
    """Per-band unit-variance normalise the cochleagram — the SAME source
    normalisation CMVN applies, so the residual is read on the source-normalised
    cochleagram (the speaker's per-band gain cancels before the shape is removed)."""
    sd = M.std(axis=0, keepdims=True)
    return M / (sd + 1e-6)


def learn_voice_shape(clips, fs, k=1):
    """LEARN one voice's shape from its utterances. `clips`: a list of waveforms ALL
    spoken by the SAME voice (one generated speaker / one real train speaker), over
    possibly different words. k: number of consistent components kept (k>=1 includes
    the mean direction; k-1 principal directions on top of the mean).

    Returns a shape dict {mean (bands,), basis (bands x (k-1)), k} or None if there
    were no usable frames. OWNED LINEAR ALGEBRA ONLY — np.mean + np.linalg.svd; NO
    net, NO gradient, NO fit-to-labels. The SVD is the closed-form principal subspace
    of THIS voice's OWN pooled, source-normalised frames."""
    rows = []
    for x in clips:
        M = _coch(x, fs)
        if M.size == 0:
            continue
        rows.append(_source_normalise(M))
    if not rows:
        return None
    P = np.concatenate(rows, axis=0)            # (total_frames x bands), this voice
    mean = P.mean(axis=0)                        # the voice's persistent signature
    basis = np.zeros((P.shape[1], 0), dtype=np.float64)
    n_pc = max(0, k - 1)
    if n_pc > 0 and P.shape[0] > 1 and P.shape[1] > 1:
        C = P - mean[None, :]
        try:
            _U, _S, Vt = np.linalg.svd(C, full_matrices=False)
            basis = Vt[:n_pc].T                  # bands x n_pc consistent directions
        except np.linalg.LinAlgError:
            basis = np.zeros((P.shape[1], 0), dtype=np.float64)
    return {"mean": mean, "basis": basis, "k": int(k)}


def learn_library(voice_clips, fs, k=1):
    """LEARN the full voice-shape library: one learned shape per voice. `voice_clips`:
    {voice_id: [waveform, ...]}. Returns a list of shape dicts (the library the
    predict-subtract picks the nearest from). Owned linear algebra per voice; no net."""
    lib = []
    for _vid, clips in voice_clips.items():
        sh = learn_voice_shape(clips, fs, k=k)
        if sh is not None:
            lib.append(sh)
    return lib


def _pick_shape(mean_frame, library):
    """PICK the nearest learned voice-shape: argmin over the library of the L2 distance
    from this utterance's mean frame to each shape's mean frame. Mechanical nearest-
    neighbour over the learned templates (the forward model's 'which speaker is this')."""
    best = None
    best_d = None
    for sh in library:
        d = float(np.linalg.norm(mean_frame - sh["mean"]))
        if best_d is None or d < best_d:
            best_d, best = d, sh
    return best


def residual_track(x, fs, library, attrs=None):
    """PREDICT-SUBTRACT then read the residual as an ORDERED per-frame trajectory
    (frames x bands) — the SAME shape `cmvn_track` returns, so the agent's unchanged
    DtwTo recognizer aligns it.

    Source-normalise the test cochleagram; PICK the nearest learned voice-shape; for
    each frame SUBTRACT the picked shape's predicted contribution (its mean frame PLUS
    the frame's projection onto the shape's principal band-space directions); read the
    residual. If the library is empty this reduces to CMVN (mean-subtract within the
    utterance), so the residual recognizer degrades gracefully. Pure boundary DSP +
    owned projection; NO net, NO decision over graph state."""
    M = _coch(x, fs)
    if M.size == 0:
        return []
    Mz = _source_normalise(M)
    if not library:
        # no learned library -> fall back to the per-utterance mean (= CMVN).
        mean = Mz.mean(axis=0, keepdims=True)
        R = Mz - mean
    else:
        mean_frame = Mz.mean(axis=0)
        sh = _pick_shape(mean_frame, library)
        # predict each frame's voice contribution = shape mean + projection on basis.
        C = Mz - sh["mean"][None, :]            # remove the persistent voice signature
        B = sh["basis"]
        if B.shape[1] > 0:
            proj = (C @ B) @ B.T                 # the consistent-direction component
            R = C - proj                         # SUBTRACT the learned voice subspace
        else:
            R = C
    # per-frame L2 so the DTW frame-distance is on the residual SHAPE (the same
    # readout cmvn_track / speaker_residual_track use).
    out = []
    for r in range(R.shape[0]):
        v = R[r]
        nrm = np.linalg.norm(v)
        out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
    return out


__all__ = ["learn_voice_shape", "learn_library", "residual_track"]
