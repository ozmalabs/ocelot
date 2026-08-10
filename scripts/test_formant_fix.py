"""Close the loop: does the agent's SELF-WRITTEN formant representation move
recognition? Trains the base recogniser, has the agent compose its own peak
detectors (Term-trees from primitives), runs them, and do-contrasts recognition
WITH vs WITHOUT the agent's features.
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(42)

from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.phonology import (learn_word_signatures, learn_sequence_signatures,
                               classify_signs)
from domains.acoustic_resolution import enrich_sign_bands, _root
from domains.speech_science import install_speech_science
from domains.formant_features import compose_peak_features, evaluate_peak_features


def main():
    af = fl.gather_files(limit=None)
    jk, tp = {}, []
    for f in af:
        (jk.setdefault(f[1], []).append(f) if f[2] == "jackson" else tp.append(f))
    test = [f for d in range(10) for f in jk.get(d, [])[:4]]      # 40 held-out
    train = random.sample(tp, 250)

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    install_speech_science(sub)
    sub.set_attr(_root(sub), "resolution", 25)        # patch-level = true formants
    vc = {}
    print(f"training base recogniser on {len(train)} samples...")
    for path, d, sp, idx in train:
        s, fs = fl.load_wav(path)
        fl.teach_one(sub, pipe, s, fl._DIGITS[d], vc)
        sub.tick(50000)

    # The agent WRITES its formant detector (Term-trees from primitives) and runs
    # it on every training sign so the word-signatures learn the peak patterns.
    enrich_sign_bands(sub)
    n = compose_peak_features(sub)
    ex = evaluate_peak_features(sub)
    print(f"the agent composed {n} peak-detector predicates from its primitives; "
          f"{ex} formant exhibits added across training signs")
    classify_signs(sub)
    learn_word_signatures(sub, vc)
    learn_sequence_signatures(sub)

    def acc(w):
        c = 0
        for path, d, sp, idx in test:
            s, fs = fl.load_wav(path)
            if fl.predict_one(sub, pipe, s, vc, phonology_weight=w) == fl._DIGITS[d]:
                c += 1
        return c

    base = acc(0.0)
    peaks = acc(1.0)
    print(f"\n  DO-CONTRAST on the agent's self-written representation:")
    print(f"    recognition WITHOUT it (pure NB/DTW)            = {base}/{len(test)}")
    print(f"    recognition WITH the agent's formant features   = {peaks}/{len(test)}")
    if peaks > base:
        print(f"  -> the agent's SELF-WRITTEN representation HELPS (+{peaks-base}). "
              f"The loop pays off: derive -> write-it-itself -> test -> WIN.")
    else:
        print(f"  -> it does not beat baseline ({peaks} vs {base}). Honest result; "
              f"the agent wrote runnable formant features, but they don't yet move "
              f"this recogniser — the next reasoned iteration.")


if __name__ == "__main__":
    main()
