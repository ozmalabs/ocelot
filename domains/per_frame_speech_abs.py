"""per_frame_speech_abs — mature the AbS speech generator from COARSE (whole-word mean-prototype +
VTL, 8b54bc3a) to PER-FRAME / SUB-WORD: a word = a TIME sequence of frame trajectories, DTW-aligned,
scored per-frame (predict-to-recover aligned in time) + VTL-warp. The speech analogue of handwriting
per-stroke AbS. graph-native, earn-not-borrow, donkey=0.

THE UPGRADE: coarse g(word,alpha) collapses the cochlear trajectory to a MEAN; per-frame keeps the
full FRAME SEQUENCE (the word's gesture over time) and DTW-ALIGNS query frames to the candidate
word's trajectory (DTW = the held DtwTo Term; the time-alignment is the speech analogue of stroke-
correspondence), under the best VTL warp. Recognize = argmin_word min_alpha DTW(query_frames,
warp(word_frames, alpha)).

HELD pieces: cochlea ops (substrate_rs.speech._audio) for the per-frame band trajectory; DtwTo (held
Rust Term) for time-alignment; VTL warp (numpy adapter). No learned feature / borrowed net in the
recognition. numpy adapter-only (frame extraction + warp). No LLM.
"""
from __future__ import annotations
import numpy as _np                 # ADAPTER: per-frame band trajectory + VTL warp
import substrate_rs as _srs
from substrate_rs import Substrate as _Substrate
from substrate_rs.speech import _audio as _A

N_BANDS = 24
N_WIN = 32                          # finer temporal resolution than coarse (12) — more frames to align
ALPHAS = _np.linspace(0.85, 1.18, 6)

_NS = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}
_S = None
_BANK = None


def _ensure():
    global _S, _BANK
    if _S is None:
        _S = _Substrate()
        _A.seed_audio_grammar(_S)
        _BANK = _A.cochlea(_S, n_bands=N_BANDS, fs=8000)
    return _S, _BANK


def frames(samples, fs=16000, nw=N_WIN):
    """The word's PER-FRAME band trajectory: (nw frames x N_BANDS), the gesture over time (NOT meaned).
    Held cochlea ops; per-utterance energy-normalized. The sub-word sequence DTW aligns + scores."""
    s, bank = _ensure()
    a = _np.asarray(samples, _np.float32)
    pk = max(float(_np.abs(a).max()), 1e-6)
    a = (a * 0.7 / pk).astype(_np.float32)
    buf = _A.audio_from_array(s, a, sample_rate=fs)
    resps = _A.a1_responses(s, buf, bank)
    out = _np.zeros((N_BANDS, nw), _np.float32)
    for bi, r in enumerate(resps):
        resp = _A.audio_to_array(s, r).astype(_np.float32)
        if resp.ndim > 1:
            resp = resp.mean(axis=1)
        n = len(resp)
        if n == 0:
            continue
        wl = max(1, n // nw)
        for w in range(nw):
            seg = resp[w * wl:(w + 1) * wl]
            if len(seg):
                out[bi, w] = float(_np.sqrt(_np.mean(seg ** 2)))
    nrm = _np.linalg.norm(out)
    out = out / nrm if nrm > 1e-8 else out
    return out.T.tolist()           # (frames x bands)


def _dtw(qf, sf):
    """Held DtwTo: time-align two frame sequences, return the alignment distance (the Rust Term)."""
    return float(_NS.evaluate({"type": "DtwTo", "a": _L(qf), "b": _L(sf)}, {}))


def _warp_frames(sf, alpha):
    """VTL warp each frame's band axis (the speaker DOF of the per-frame generator)."""
    a = _np.asarray(sf)
    nb = a.shape[1]; src = _np.arange(nb); tgt = _np.clip(src * alpha, 0, nb - 1)
    return _np.stack([_np.interp(src, tgt, a[i]) for i in range(a.shape[0])]).tolist()


def perframe_score(query_frames, word_frames):
    """The per-frame AbS score: min over VTL alpha of DTW(query, warp(word, alpha)). LOWER = the
    candidate word's per-frame program, time-aligned + under the best tract, better explains the query."""
    best = float("inf")
    for alpha in ALPHAS:
        d = _dtw(query_frames, _warp_frames(word_frames, alpha))
        if d < best:
            best = d
    return best


def classify(query_frames, word_exemplar_sets):
    """Classify by per-frame inversion: argmin over candidate words of the min DTW+warp score across
    that word's exemplar frame-sequences. Pure held inversion (DtwTo + cochlea), no learned feature."""
    scores = [min(perframe_score(query_frames, e) for e in exes) if exes else float("inf")
              for exes in word_exemplar_sets]
    return int(_np.argmin(scores)), scores
