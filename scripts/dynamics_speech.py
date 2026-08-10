"""Learn over DYNAMICS-OVER-TIME, not static snapshots. The blurry cochlea can't
give sharp formants, but it gives their MOVEMENT — and the shape of the formant
trajectory (how F2 glides) is far more speaker-invariant than absolute values, the
way humans actually hear. Per-frame formants via the agent's ArgMax; classify by
DTW over the trajectory shape (which absorbs rate + speaker differences).
Compared with the static clip-average (40%).
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

SC = "/tmp/sc"


class _P:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _amax(sub, v):
    return 0 if len(v) == 0 else sub.evaluate(
        _P({"type": "ArgMax", "items": [Lit(float(x)).to_dict() for x in v]}), {})


def load(p):
    w = wave.open(p)
    r = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
         .astype(np.float32) / 32768.0)
    return (r[::2] if w.getframerate() == 16000 else r)


def dtw(a, b):
    n, m = len(a), len(b)
    D = np.full((n + 1, m + 1), 1e18)
    D[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = abs(a[i - 1] - b[j - 1])
            D[i, j] = c + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    return D[n, m]


def main():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    from domains.speech_cortex import SpeechCortex
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    NP = len(list(sub.nodes("A1Patch")))
    hi = NP // 2

    def f2_trajectory(x):
        pipe.ingest(sub, np.ascontiguousarray(x))
        sub.tick(50000)
        st = None
        for s in sub.nodes("AudioStream"):
            st = s
        sg = fl._collect_signs_from_stream(sub, st) if st else []
        trs = [np.asarray(t, float).reshape(-1, NP)
               for t in (sub.node(g)["attrs"].get("trajectory") for g in sg)
               if t is not None and len(t) % NP == 0]
        if not trs:
            return None
        T = np.mean(trs, axis=0)                    # (frames, channels)
        # per-frame spectral CENTROID over the formant band — a SMOOTH tracker of
        # formant movement (no per-frame peak jitter). Its trajectory shape is the
        # speaker-invariant dynamic cue.
        idx = np.arange(hi, NP, dtype=float)
        e_all = T.sum(axis=1)
        cen = np.array([np.sum(idx * T[fr][hi:]) / (T[fr][hi:].sum() + 1e-9)
                        for fr in range(T.shape[0])], float)
        cen = cen[e_all > e_all.max() * 0.15]        # voiced frames only
        if len(cen) < 4:
            return None
        return (cen - cen.mean()) / (cen.std() + 1e-6)   # speaker-invariant shape

    words = [w for w in ["yes", "no", "up", "down"]
             if os.path.isdir(os.path.join(SC, w))]
    data = {w: [(os.path.join(SC, w, f), f.split("_")[0])
                for f in sorted(os.listdir(os.path.join(SC, w)))
                if f.endswith(".wav")] for w in words}
    tsp = set()
    for w in words:
        s = sorted({x for _, x in data[w]})
        tsp |= set(s[::5])
    tr = [(p, w) for w in words for p, s in data[w] if s not in tsp]
    te = [(p, w) for w in words for p, s in data[w] if s in tsp]
    random.shuffle(tr)
    random.shuffle(te)
    tr, te = tr[:100], te[:48]
    print(f"learning over DYNAMICS (F2 trajectory shape, DTW), {len(words)} words, "
          f"held-out speakers (chance {100 // len(words)}%); patches={NP}")

    bank = []
    for p, w in tr:
        f = f2_trajectory(load(p))
        if f is not None:
            bank.append((f, w))
    c = n = 0
    for p, w in te:
        f = f2_trajectory(load(p))
        if f is None:
            continue
        n += 1
        pred = min(bank, key=lambda bw: dtw(f, bw[0]))[1]
        if pred == w:
            c += 1
    print(f"\n  DYNAMICS recognition (DTW over formant trajectory), held-out "
          f"speakers: {c}/{n} = {100 * c / max(1, n):.0f}%  (static was 40%)")


if __name__ == "__main__":
    main()
