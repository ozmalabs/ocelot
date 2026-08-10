"""Small actual-speech run USING the agent's newly-designed ArgMax primitive.

Computes formant features (F1, F2 = spectral peak bins via ArgMax; F2/F1 ratio =
vocal-tract-length / speaker-invariant) over its own cochlear spectrum, and asks:
on HELD-OUT SPEAKERS, does the formant-ratio cue generalise better than the
band-means (which sat at chance)? The formants are computed by EVALUATING ArgMax
terms — the primitive the agent just added to its runtime.
"""
import os
import sys
import wave
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(2)

from substrate_rs import Substrate, Lit
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.acoustic_resolution import enrich_sign_bands, _root

SC = "/tmp/sc"
N = 25  # cochlear patches


class _P:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def load_real(path):
    w = wave.open(path)
    raw = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
           .astype(np.float32) / 32768.0)
    if w.getframerate() == 16000:
        raw = raw[::2]
    return np.ascontiguousarray(raw.astype(np.float32)), 8000


def clip_formants(sub, pipe, samples):
    """Average spectrum over the clip's signs, then F1/F2 via the agent's ArgMax."""
    pipe.ingest(sub, samples)
    sub.tick(50000)
    stream = None
    for s in sub.nodes("AudioStream"):
        stream = s
    signs = fl._collect_signs_from_stream(sub, stream) if stream else []
    if not signs:
        return None
    enrich_sign_bands(sub, signs=signs)
    spec = np.zeros(N)
    k = 0
    for sg in signs:
        a = sub.node(sg)["attrs"]
        v = [a.get(f"band{N}_{i}") for i in range(N)]
        if all(x is not None for x in v):
            spec += np.array(v, float)
            k += 1
    if k == 0:
        return None
    spec /= k
    half = N // 2
    f1 = sub.evaluate(_P({"type": "ArgMax",
                          "items": [Lit(float(x)).to_dict() for x in spec[:half]]}), {})
    f2 = half + sub.evaluate(_P({"type": "ArgMax",
                          "items": [Lit(float(x)).to_dict() for x in spec[half:]]}), {})
    ratio = (f2 + 1.0) / (f1 + 1.0)
    return np.array([f1, f2, ratio], float)


def main():
    words = ["yes", "no", "up", "down"]
    words = [w for w in words if os.path.isdir(os.path.join(SC, w))]
    data = {w: [(os.path.join(SC, w, f), f.split("_")[0])
                for f in sorted(os.listdir(os.path.join(SC, w)))
                if f.endswith(".wav")] for w in words}
    test_spk = set()
    for w in words:
        spks = sorted({s for _, s in data[w]})
        test_spk |= set(spks[::5])
    train = [(p, w) for w in words for p, s in data[w] if s not in test_spk]
    test = [(p, w) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(train)
    random.shuffle(test)
    train, test = train[:120], test[:48]

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    sub.set_attr(_root(sub), "resolution", N)
    print(f"{len(words)} words; {len(train)} train, {len(test)} held-out-speaker "
          f"test (chance {100 // len(words)}%). Computing formants via ArgMax...")

    feats = {}
    for path, w in train:
        s, _ = load_real(path)
        f = clip_formants(sub, pipe, s)
        if f is not None:
            feats.setdefault(w, []).append(f)
    centroids = {w: np.mean(v, axis=0) for w, v in feats.items() if v}
    stds = np.std([f for v in feats.values() for f in v], axis=0) + 1e-6

    def classify(f):
        return min(centroids, key=lambda w: np.sum(((f - centroids[w]) / stds) ** 2))

    c = 0
    n = 0
    for path, w in test:
        s, _ = load_real(path)
        f = clip_formants(sub, pipe, s)
        if f is None:
            continue
        n += 1
        if classify(f) == w:
            c += 1
    print(f"\n  formant-feature recognition (ArgMax F1/F2/ratio), held-out "
          f"speakers: {c}/{n} = {100 * c / max(1, n):.0f}%")
    print("  (band-mean NB/DTW baseline on real speaker-independent speech was at "
          "chance; this tests whether the speaker-invariant ratio generalises)")


if __name__ == "__main__":
    main()
