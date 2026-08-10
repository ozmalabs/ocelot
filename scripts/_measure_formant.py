"""Measure formant-feature speech recognition using whatever index-primitives the
runtime currently has (ArgMax, ArgMin, ...). Run as a fresh process so it loads the
latest rebuilt substrate. Prints one line: ACC <pct> PRIMS <list>.
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
N = 25


class _P:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _has(sub, ttype):
    try:
        sub.evaluate(_P({"type": ttype, "items": [Lit(1.0).to_dict(),
                                                  Lit(2.0).to_dict()]}), {})
        return True
    except Exception:
        return False


def load_real(path):
    w = wave.open(path)
    raw = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
           .astype(np.float32) / 32768.0)
    if w.getframerate() == 16000:
        raw = raw[::2]
    return np.ascontiguousarray(raw.astype(np.float32))


def main():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    sub.set_attr(_root(sub), "resolution", N)
    prims = [t for t in ("ArgMax", "ArgMin") if _has(sub, t)]

    def feats(samples):
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
        lo = [Lit(float(x)).to_dict() for x in spec[:half]]
        hi = [Lit(float(x)).to_dict() for x in spec[half:]]
        vec = []
        for t in prims:                       # one feature pair per available prim
            a = sub.evaluate(_P({"type": t, "items": lo}), {})
            b = half + sub.evaluate(_P({"type": t, "items": hi}), {})
            vec += [a, b, (b + 1.0) / (a + 1.0)]
        return np.array(vec, float)

    words = [w for w in ["yes", "no", "up", "down"]
             if os.path.isdir(os.path.join(SC, w))]
    data = {w: [(os.path.join(SC, w, f), f.split("_")[0])
                for f in sorted(os.listdir(os.path.join(SC, w)))
                if f.endswith(".wav")] for w in words}
    test_spk = set()
    for w in words:
        sp = sorted({s for _, s in data[w]})
        test_spk |= set(sp[::5])
    tr = [(p, w) for w in words for p, s in data[w] if s not in test_spk]
    te = [(p, w) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(tr)
    random.shuffle(te)
    tr, te = tr[:120], te[:48]

    cent = {}
    allf = []
    for p, w in tr:
        f = feats(load_real(p))
        if f is not None:
            cent.setdefault(w, []).append(f)
            allf.append(f)
    centroids = {w: np.mean(v, axis=0) for w, v in cent.items() if v}
    std = np.std(allf, axis=0) + 1e-6
    c = n = 0
    for p, w in te:
        f = feats(load_real(p))
        if f is None:
            continue
        n += 1
        if min(centroids, key=lambda x: np.sum(((f - centroids[x]) / std) ** 2)) == w:
            c += 1
    print(f"ACC {100 * c / max(1, n):.0f} PRIMS {prims}")


if __name__ == "__main__":
    main()
