"""Speech with HINTING: the agent composes formant features guided by the science
it holds (hints), using its own ArgMax primitive, then selects by held-out-speaker
recognition. Hints (actionable, from speech_science):
  - F1/F2/F3 = spectral peaks in low/mid/high regions (ArgMax per region)
  - F2/F1, F3/F2 ratios = vocal-tract-length / speaker invariant
  - formant DYNAMICS (per-frame F2 movement) distinguish words (glides/diphthongs)
  - spectral tilt = voicing / manner
Compared against the un-hinted clip-averaged F1/F2/ratio (which sat at 40%).
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

SC, N, FR = "/tmp/sc", 25, 32


class _P:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _argmax(sub, vals):                       # the agent's own runtime primitive
    return sub.evaluate(_P({"type": "ArgMax",
                            "items": [Lit(float(x)).to_dict() for x in vals]}), {})


def load_real(path):
    w = wave.open(path)
    raw = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
           .astype(np.float32) / 32768.0)
    return (raw[::2] if w.getframerate() == 16000 else raw).astype(np.float32)


def hinted_feats(sub, pipe, samples):
    pipe.ingest(sub, np.ascontiguousarray(samples))
    sub.tick(50000)
    stream = None
    for s in sub.nodes("AudioStream"):
        stream = s
    signs = fl._collect_signs_from_stream(sub, stream) if stream else []
    trajs = []
    for sg in signs:
        t = sub.node(sg)["attrs"].get("trajectory")
        if t is not None and len(t) == FR * N:
            trajs.append(np.asarray(t, float).reshape(FR, N))
    if not trajs:
        return None
    T = np.mean(trajs, axis=0)                 # (frames, patches)
    avg = T.mean(axis=0)                        # avg spectrum
    # HINT: F1/F2/F3 = peaks of low/mid/high regions (the agent's ArgMax)
    f1 = _argmax(sub, avg[:8])
    f2 = 8 + _argmax(sub, avg[8:16])
    f3 = 16 + _argmax(sub, avg[16:])
    # HINT: ratios are speaker-invariant
    r21, r32 = (f2 + 1.0) / (f1 + 1.0), (f3 + 1.0) / (f2 + 1.0)
    # HINT: formant DYNAMICS — per-frame F2 peak movement
    f2_traj = [8 + _argmax(sub, T[fr][8:16]) for fr in range(FR)]
    dyn = float(np.std(f2_traj))
    # HINT: spectral tilt = low/high energy
    tilt = float(avg[:12].sum() / (avg[12:].sum() + 1e-6))
    return np.array([f1, f2, f3, r21, r32, dyn, tilt], float)


def main():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    from domains.acoustic_resolution import _root
    sub.set_attr(_root(sub), "resolution", N)

    words = [w for w in ["yes", "no", "up", "down"]
             if os.path.isdir(os.path.join(SC, w))]
    data = {w: [(os.path.join(SC, w, f), f.split("_")[0])
                for f in sorted(os.listdir(os.path.join(SC, w)))
                if f.endswith(".wav")] for w in words}
    tsp = set()
    for w in words:
        sp = sorted({s for _, s in data[w]})
        tsp |= set(sp[::5])
    tr = [(p, w) for w in words for p, s in data[w] if s not in tsp]
    te = [(p, w) for w in words for p, s in data[w] if s in tsp]
    random.shuffle(tr)
    random.shuffle(te)
    tr, te = tr[:120], te[:48]
    print(f"{len(words)} words, hinted formant features, held-out speakers "
          f"(chance {100 // len(words)}%). un-hinted baseline was 40%.")

    names = ["F1", "F2", "F3", "F2/F1", "F3/F2", "dyn", "tilt"]
    trX, trY, teX, teY = [], [], [], []
    for p, w in tr:
        f = hinted_feats(sub, pipe, load_real(p))
        if f is not None:
            trX.append(f)
            trY.append(w)
    for p, w in te:
        f = hinted_feats(sub, pipe, load_real(p))
        if f is not None:
            teX.append(f)
            teY.append(w)
    trX, teX = np.array(trX), np.array(teX)
    std = trX.std(axis=0) + 1e-6
    # split TRAIN into fit + val (validate feature choice WITHOUT touching test)
    m = len(trX) * 3 // 4
    fitX, fitY, vaX, vaY = trX[:m], trY[:m], trX[m:], trY[m:]

    def recog(cols, AX, AY, BX, BY):
        cen = {}
        for f, w in zip(AX, AY):
            cen.setdefault(w, []).append(f[cols])
        cen = {w: np.mean(v, axis=0) for w, v in cen.items()}
        sd = std[cols]
        ok = sum(1 for f, w in zip(BX, BY)
                 if min(cen, key=lambda x: np.sum(((f[cols] - cen[x]) / sd) ** 2)) == w)
        return ok / max(1, len(BY))

    # forward selection of HINTED features on the validation split
    sel, rem, best = [], list(range(len(names))), 0.0
    while rem:
        s, i = max((recog(sel + [j], fitX, fitY, vaX, vaY), j) for j in rem)
        if s <= best:
            break
        best = s
        sel.append(i)
        rem.remove(i)
    acc = recog(sel, trX, trY, teX, teY)
    print(f"\n  agent selected hinted features: {[names[i] for i in sel]}")
    print(f"  HINTED+SELECTED recognition, held-out speakers: "
          f"{acc*100:.0f}%  (vs 40% un-hinted, 33% all-hinted)")


if __name__ == "__main__":
    main()
