"""The agent in the persona world: it says its words through different speakers and
hears itself. If it recognizes the same word across personas, it has grounded the
word's speaker-INVARIANT identity by doing — the seed of meaning.
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(2)

from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.persona_speech_world import (install_personas, speak_as,
                                          DEFAULT_PERSONAS)


def main():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    for op in sub.nodes("Operation"):
        if sub.node(op)["attrs"].get("kind") == "lexical_access":
            sub.set_attr(op, "distance_threshold", 0.02)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()

    # teach the agent a handful of words (so it can SAY them)
    af = fl.gather_files(limit=None)
    pool = [f for f in af if f[2] != "jackson"]
    words = ["one", "three", "five", "nine"]
    digits = {w: i for i, w in enumerate(fl._DIGITS)}
    vc = {}
    for w in words:
        clips = [f for f in pool if f[1] == digits[w]][:6]
        for path, digit, sp, idx in clips:
            s, fs = fl.load_wav(path)
            fl.teach_one(sub, pipe, s, w, vc)
            sub.tick(50000)
    print(f"taught: {words}")

    personas = install_personas(sub, DEFAULT_PERSONAS)
    print(f"personas the agent controls: {list(personas)}")
    print(f"  (voices: " + ", ".join(
        f"{n} f0={s[1]:.0f} vtl={s[3]}" for n, s in zip(personas, DEFAULT_PERSONAS)) + ")")

    print("\nThe agent says each word through each persona, and hears itself:")
    print(f"  {'word':>6} | " + " | ".join(f"{n:>8}" for n in personas))
    inv = []
    for w in words:
        row = []
        for name, pid in personas.items():
            audio, _ = speak_as(sub, pipe, pid, w, hear=False)
            heard = fl.predict_one(sub, pipe, audio, vc)
            row.append(heard or "—")
        same = sum(1 for h in row if h == w)
        inv.append(same / len(row))
        print(f"  {w:>6} | " + " | ".join(f"{h:>8}" for h in row)
              + f"   ({same}/{len(row)} heard as itself)")
    print(f"\nspeaker-invariant self-recognition: {100*sum(inv)/len(inv):.0f}% "
          f"— the word heard as the same word across the voices it controls")


if __name__ == "__main__":
    main()
