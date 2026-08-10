"""speech_abs_earner — AbS-on-speech: recognize by INVERTING the held acoustic generator (the speech
keystone), the analogue of handwriting AbS (2eb45a1a). graph-native, earn-not-borrow, donkey=0.

THE KEYSTONE (the agent's own pick, speech_analysis_by_synthesis.py): recovering causes from effects
is an INVERSE problem needing a FORWARD model (articulation->acoustics) to invert. The forward model's
key speaker degree-of-freedom is VOCAL-TRACT LENGTH (VTL: the message is in the FILTER/tract). So:
  forward model g(word, alpha) = the word's held cochlear PROTOTYPE warped along the log-freq (band)
                                 axis by VTL factor alpha
  recognize     = argmin_word  min_alpha  dist(observed, g(word, alpha))
The inner min over alpha INVERTS the speaker (recovers the word's gesture under the best-fit tract).

This is the EARNER for the teacher-bootstrap conversion (the conversion_loop is domain-generic): swap
teacher=Whisper, earner=this. Features = the HELD cochlea ops (substrate_rs.speech._audio); the warp +
match is world-adapter MEASUREMENT (reads, doesn't decide). numpy is adapter-only (band-array math).
No learned feature, no borrowed net in the AbS inference. No LLM.
"""
from __future__ import annotations
import numpy as _np                 # ADAPTER: band-trajectory + warp math
from substrate_rs import Substrate as _Substrate
from substrate_rs.speech import _audio as _A

N_BANDS = 24
N_WIN = 12
ALPHAS = _np.linspace(0.80, 1.25, 10)   # candidate vocal-tract factors to invert over

_S = None
_BANK = None


def _ensure():
    """Lazy held-cochlea setup (one substrate + filterbank)."""
    global _S, _BANK
    if _S is None:
        _S = _Substrate()
        _A.seed_audio_grammar(_S)
        _BANK = _A.cochlea(_S, n_bands=N_BANDS, fs=8000)
    return _S, _BANK


def feat(samples, fs=16000):
    """(bands x windows) cochlear trajectory via the HELD cochlea ops. Per-utterance energy-normalized
    (factors out gain/loudness). The held acoustic feature the forward model warps + matches."""
    s, bank = _ensure()
    a = _np.asarray(samples, _np.float32)
    pk = max(float(_np.abs(a).max()), 1e-6)
    a = (a * 0.7 / pk).astype(_np.float32)
    buf = _A.audio_from_array(s, a, sample_rate=fs)
    resps = _A.a1_responses(s, buf, bank)
    out = _np.zeros((N_BANDS, N_WIN), _np.float32)
    for bi, r in enumerate(resps):
        resp = _A.audio_to_array(s, r).astype(_np.float32)
        if resp.ndim > 1:
            resp = resp.mean(axis=1)
        n = len(resp)
        if n == 0:
            continue
        wl = max(1, n // N_WIN)
        for w in range(N_WIN):
            seg = resp[w * wl:(w + 1) * wl]
            if len(seg):
                out[bi, w] = float(_np.sqrt(_np.mean(seg ** 2)))
    nrm = _np.linalg.norm(out)
    return out / nrm if nrm > 1e-8 else out


def warp_bands(proto, alpha):
    """The forward model's speaker DOF: resample the band (log-freq) axis by VTL alpha. alpha>1 =
    longer tract (lower formants) -> shift energy down the bands. The generator's articulation knob."""
    nb = proto.shape[0]
    src = _np.arange(nb)
    tgt = _np.clip(src * alpha, 0, nb - 1)
    out = _np.empty_like(proto)
    for w in range(proto.shape[1]):
        out[:, w] = _np.interp(src, tgt, proto[:, w])
    return out


def abs_score(observed_feat, prototype_feat):
    """The AbS inversion score: min over VTL alpha of dist(observed, g(prototype, alpha)). LOWER =
    the prototype's word, under the best-fit speaker tract, better explains the observed acoustic.
    INVERTS the speaker to recover the word's gesture (the keystone). numpy distance, held feature."""
    best = float("inf")
    for alpha in ALPHAS:
        g = warp_bands(prototype_feat, alpha)
        d = float(_np.linalg.norm(observed_feat - g))
        if d < best:
            best = d
    return best


def classify(observed_feat, prototypes):
    """Classify by inverting the held generator over candidate word PROTOTYPES: argmin over candidates
    of abs_score. Pure inversion (forward-model warp + match) — no learned feature, no Whisper."""
    scores = [abs_score(observed_feat, p) for p in prototypes]
    return int(_np.argmin(scores)), scores


def build_prototype(feats):
    """A held word PROTOTYPE = the mean cochlear trajectory over training examples (the earned
    generator's per-word template). The library stores these; teach/extend read them."""
    return _np.mean(_np.stack(feats, 0), 0) if feats else None
