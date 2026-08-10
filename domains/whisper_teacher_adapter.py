"""whisper_teacher_adapter — the BORROWED Whisper (the "help-button" external ear) as a FeatureTeacher
proposal for the speech teacher-bootstrap conversion. The speech analogue of the Gemma vision teacher
(8e29d42a). graph-native earned side; Whisper = read-only PROPOSAL only.

ARCHITECTURE: Whisper is the borrowed SCAFFOLD (a fast recognition PROPOSAL via its ENCODER features —
cosine top-K over word prototypes). The earned structure (the held AbS-on-speech earner + the grown
word library) makes the DECISION and stands alone. This adapter produces a Whisper encoder feature per
audio segment (mean-pooled), used ONLY for the top-K proposal — NO Whisper weights enter the earned
structure, and Whisper is NOT in the teach/extend path.

NOTE (honest survey finding): Whisper cannot free-transcribe these isolated ~0.1-0.2s word segments
(too short/decontextualized -> empty). So the teacher proposal uses Whisper's ENCODER FEATURES
(cosine top-K), exactly as the Gemma vision teacher used vision-tower features — a borrowed-net
proposal, not free transcription.

torch/ctranslate2/faster-whisper are used here ONLY (the teacher). The earned structure (AbS-on-speech
+ library) uses none of them. numpy adapter-only for the feature math. No LLM.
"""
from __future__ import annotations
from collections import OrderedDict
import hashlib
import numpy as _np                 # ADAPTER: feature pooling/cosine

_MODEL = None
_CACHE_MAX = 512
_CACHE = OrderedDict()


def available() -> bool:
    try:
        from faster_whisper import WhisperModel  # noqa
        return True
    except Exception:
        return False


def _load():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _MODEL


def embed(audio):
    """The BORROWED Whisper ENCODER feature of one audio segment (mean-pooled, L2-normalized) — the
    teacher's PROPOSAL signal. Content-addressed and bounded so Python object-id reuse cannot give a
    new clip an old clip's embedding. Returns a numpy vector or None."""
    a = _np.ascontiguousarray(_np.asarray(audio, _np.float32))
    h = hashlib.blake2b(digest_size=20)
    h.update(str(a.shape).encode("ascii"))
    h.update(a.dtype.str.encode("ascii"))
    h.update(memoryview(a).cast("B"))
    key = h.digest()
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return _CACHE[key]
    m = _load()
    feats = m.feature_extractor(a)            # log-mel
    enc = m.encode(feats)                      # encoder output (ctranslate2 StorageView)
    arr = _np.asarray(enc)                     # (1, T, D)
    v = arr.reshape(-1, arr.shape[-1]).mean(0)
    v = v / (_np.linalg.norm(v) + 1e-9)
    _CACHE[key] = v
    _CACHE.move_to_end(key)
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return v


def clear_embedding_cache():
    """Clear the borrowed-sensor cache (measurement/test lifecycle only)."""
    _CACHE.clear()


def make_teacher():
    """A FeatureTeacher backed by the borrowed Whisper encoder (proposal only). Works on (audio)
    items: the conversion_loop's support/query are audio arrays; the teacher embeds + cosines them."""
    import domains.conversion_loop as cl
    return cl.FeatureTeacher(embed, name="whisper-borrowed")


class InvalidForcedDecodeScoring(RuntimeError):
    """The retired API was scoring generated continuations, not candidate tokens."""


_INVALID_FORCED_DECODE = (
    "retired invalid Whisper forced-decode scorer: CTranslate2 `generate` "
    "treats candidate prompt tokens as unscored initial tokens, so its returned "
    "score is for the generated continuation, not P(candidate|audio). Use the "
    "encoder-grounded graph guard instead."
)


def _seq_score(enc, word):
    """Fail loudly: the historical implementation did not score `word`."""
    del enc, word
    raise InvalidForcedDecodeScoring(_INVALID_FORCED_DECODE)


def _encode(audio):
    m = _load()
    return m.encode(m.feature_extractor(_np.asarray(audio, _np.float32)))


def _word_prior(word):
    del word
    raise InvalidForcedDecodeScoring(_INVALID_FORCED_DECODE)


def forced_decode_topk(audio, candidates, k=3):
    """Retired: CTranslate2 cannot score the supplied prompt tokens."""
    del audio, candidates, k
    raise InvalidForcedDecodeScoring(_INVALID_FORCED_DECODE)


class ForcedDecodeTeacher:
    """Compatibility tombstone for the invalid historical experiment."""

    def __init__(self, vocab):
        del vocab
        raise InvalidForcedDecodeScoring(_INVALID_FORCED_DECODE)

    def propose(self, audio, support=None, k=3):
        del audio, support, k
        raise InvalidForcedDecodeScoring(_INVALID_FORCED_DECODE)

    def full_rank(self, audio):
        del audio
        raise InvalidForcedDecodeScoring(_INVALID_FORCED_DECODE)
