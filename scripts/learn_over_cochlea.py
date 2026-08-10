"""Teach the agent to LEARN OVER THE COCHLEA IT HAS.

The arc concluded: the gammatone cochlea is biologically correct, the blur IS the
ear, and the lever is LEARNING over it (as a child does) — not sharper perception.
This run tests that directly: the agent learns word categories over its OWN realistic
(blurry) cochlear representation, and we ask the honest questions —
  (1) does LEARNING get held-out-speaker recognition off chance?
  (2) does the agent's SPEAKER NORMALIZATION (VTL) help the learning generalise?
  (3) do its DYNAMICS (formant transition) add over static?
  (4) the LEARNING CURVE: does more exposure help, and where does it plateau (the
      cochlea's ceiling)?
All features are the agent's own (ArgMax formant freqs, VTL mean-subtraction, the
order-1-time transition). Learning = category prototypes from data. Honest numbers.
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
from domains.acoustic_resolution import enrich_sign_bands, enrich_sign_windows, _root

SC, N = "/tmp/sc", 25


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
    return np.ascontiguousarray((r[::2] if w.getframerate() == 16000 else r)
                                .astype(np.float32))


def main():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    sub.set_attr(_root(sub), "resolution", N)
    t = N // 3

    def features(x):
        pipe.ingest(sub, x)
        sub.tick(50000)
        st = None
        for s in sub.nodes("AudioStream"):
            st = s
        sg = fl._collect_signs_from_stream(sub, st) if st else []
        enrich_sign_bands(sub, signs=sg)
        enrich_sign_windows(sub, resolution=N, signs=sg)
        spec, early, late = [], [], []
        for s in sg:
            a = sub.node(s)["attrs"]
            v = [a.get(f"band{N}_{i}") for i in range(N)]
            e = [a.get(f"band{N}_{i}_e") for i in range(N)]
            l = [a.get(f"band{N}_{i}_l") for i in range(N)]
            if all(z is not None for z in v):
                spec.append(np.array(v, float))
            if all(z is not None for z in e):
                early.append(np.array(e, float))
                late.append(np.array(l, float))
        if not spec:
            return None
        a = np.mean(spec, 0)
        F = np.array([_amax(sub, a[:t]), t + _amax(sub, a[t:2*t]),
                      2*t + _amax(sub, a[2*t:])], float)
        vtl = F - F.mean()                              # speaker normalization
        if early:
            e = np.mean(early, 0); l = np.mean(late, 0)
            f2e = t + _amax(sub, e[t:2*t]); f2l = t + _amax(sub, l[t:2*t])
            trans = float(f2l - f2e)                    # order-1-time transition
        else:
            trans = 0.0
        return {"raw": F, "vtl": vtl, "vtl+dyn": np.append(vtl, trans)}

    words = [w for w in ["yes", "no", "up", "down"] if os.path.isdir(f"{SC}/{w}")]
    data = {w: [(f"{SC}/{w}/{f}", f.split("_")[0])
                for f in sorted(os.listdir(f"{SC}/{w}")) if f.endswith(".wav")]
            for w in words}
    tsp = set()
    for w in words:
        s = sorted({x for _, x in data[w]})
        tsp |= set(s[::5])
    tr = {w: [p for p, s in data[w] if s not in tsp] for w in words}
    te = {w: [p for p, s in data[w] if s in tsp][:10] for w in words}

    print(f"{len(words)} words, held-out speakers (chance {100//len(words)}%). "
          f"Caching the agent's cochlear features...")
    trf = {w: [features(load(p)) for p in tr[w][:80]] for w in words}
    tef = {w: [features(load(p)) for p in te[w]] for w in words}
    trf = {w: [f for f in v if f] for w, v in trf.items()}
    tef = {w: [f for f in v if f] for w, v in tef.items()}

    def learn_and_test(rep, k):
        cen, allf = {}, []
        for w in words:
            xs = [f[rep] for f in trf[w][:k]]
            if xs:
                cen[w] = np.mean(xs, 0)
                allf += xs
        sd = np.std(allf, 0) + 1e-6
        c = n = 0
        for w in words:
            for f in tef[w]:
                n += 1
                if min(cen, key=lambda x: np.sum(((f[rep]-cen[x])/sd)**2)) == w:
                    c += 1
        return 100 * c / max(1, n)

    print("\nLEARNING CURVE — held-out-speaker accuracy by training clips/word:")
    print(f"  {'clips/word':>10} | {'raw':>6} | {'vtl(norm)':>9} | {'vtl+dyn':>7}")
    for k in (8, 16, 32, 64, 80):
        print(f"  {k:>10} | {learn_and_test('raw',k):5.0f}% | "
              f"{learn_and_test('vtl',k):8.0f}% | {learn_and_test('vtl+dyn',k):6.0f}%")


if __name__ == "__main__":
    main()
