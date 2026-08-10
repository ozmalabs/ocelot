"""Put the agent on ACTUAL speech — Google Speech Commands (real words, thousands
of real speakers), not the FSDD digit toy. Train on real clips, test on HELD-OUT
SPEAKERS (the real lack-of-invariance test).
"""
import os
import sys
import wave
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(1)

from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.phonology import learn_word_signatures, learn_sequence_signatures

SC = "/tmp/sc"


def load_real(path):
    w = wave.open(path)
    raw = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
           .astype(np.float32) / 32768.0)
    if w.getframerate() == 16000:                       # -> 8 kHz for the cochlea
        try:
            from scipy.signal import decimate
            raw = decimate(raw, 2)
        except Exception:
            raw = raw[::2]
    return np.ascontiguousarray(raw.astype(np.float32)), 8000


def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    n_train = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    n_test = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    avail = [w for w in sorted(os.listdir(SC))
             if os.path.isdir(os.path.join(SC, w)) and not w.startswith("_")
             and len([f for f in os.listdir(os.path.join(SC, w))
                      if f.endswith(".wav")]) > 200]
    words = avail[:n_words]
    print(f"ACTUAL-SPEECH: {len(words)} words {words}")
    data = {}
    for w in words:
        for fn in sorted(os.listdir(os.path.join(SC, w))):
            if fn.endswith(".wav"):
                data.setdefault(w, []).append((os.path.join(SC, w, fn),
                                               fn.split("_")[0]))
    # hold out whole SPEAKERS for test — speaker-independent recognition
    test_spk = set()
    for w in words:
        spks = sorted({s for _, s in data[w]})
        test_spk |= set(spks[::6])                       # ~1/6 of speakers
    train = [(p, w) for w in words for p, s in data[w] if s not in test_spk]
    test = [(p, w) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(train)
    random.shuffle(test)
    train, test = train[:n_train], test[:n_test]

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    vc = {}
    print(f"training on {len(train)} real clips; testing on {len(test)} from "
          f"HELD-OUT speakers ({len(words)}-way, chance {100 // len(words)}%)...")
    import time
    _t0 = time.time()
    for _i, (path, w) in enumerate(train):
        s, _ = load_real(path)
        fl.teach_one(sub, pipe, s, w, vc)
        sub.tick(50000)
        if (_i + 1) % 200 == 0:
            print(f"  trained {_i + 1}/{len(train)} "
                  f"({time.time() - _t0:.0f}s)", flush=True)
    learn_word_signatures(sub, vc)
    learn_sequence_signatures(sub)

    c = 0
    for path, w in test:
        s, _ = load_real(path)
        if fl.predict_one(sub, pipe, s, vc) == w:
            c += 1
    print(f"\n  recognition on ACTUAL SPEECH, held-out speakers: "
          f"{c}/{len(test)} = {100 * c / len(test):.0f}%")


if __name__ == "__main__":
    main()
