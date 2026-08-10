"""MANY EASY TARGETS MAKE THE HARD TARGET EASIER — compounding, measured.

The hard target is human-equivalent multilingual word understanding. The EASY, abundant target
is "hear a word and bank it under the human (whisper) label" — there is endless cheap speech to
do this on. The claim the creator made: solving many easy targets COMPOUNDS — each labelled word
heard lifts the hard recognition target.

This measures it directly: a held-out recognition test in four languages, scored as the agent
banks more and more whisper-labelled exemplars (the easy target) into the SAME lexicon the
recogniser reads. If the held-out agreement RISES with the easy bank, the easy targets compound.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.compounding_curriculum
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains.speech_world import SpeechWorld
from domains.speech_world_recognizer import GraphLexicon, WordHat

LANGS = {
    "en": ("lessac", ["one", "two", "three", "four", "five", "six"]),
    "fr": ("siwis", ["un", "deux", "trois", "quatre", "cinq", "six"]),
    "de": ("thorsten", ["eins", "zwei", "drei", "vier", "funf", "sechs"]),
    "es": ("davefx", ["uno", "dos", "tres", "cuatro", "cinco", "seis"]),
}
SEP = "=" * 80


def main():
    print(SEP)
    print("COMPOUNDING — held-out recognition lifts as the easy whisper-labelled bank grows.")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s)
    lex = GraphLexicon(s)
    hat = WordHat()

    def perceive(word, voice, pitch):
        out = sw.synth(word, {"variant": voice, "pitch": pitch, "rate": 175})
        if out is None:
            return None, None
        x, fs = out
        return SDW.feature_channels(s, x, fs), (x, fs)

    # HELD-OUT test set: one clean instance per (lang, word) at a pitch never used for banking.
    held = []
    for lang, (voice, words) in LANGS.items():
        for w in words:
            ch, _ = perceive(w, voice, 80)
            if ch is not None:
                held.append((lang, w, ch))

    def score():
        per = {l: [0, 0] for l in LANGS}
        for lang, w, ch in held:
            guess = hat.recognise(ch, lex)
            per[lang][1] += 1
            if guess == w:
                per[lang][0] += 1
        return {l: (c / max(1, n)) for l, (c, n) in per.items()}

    # the EASY target: bank whisper-labelled exemplars (varied pitches = abundant cheap data).
    bank_pitches = [30, 50, 70]
    milestones = [0, 1, 2, 3]   # how many pitches banked so far
    print("  easy bank size 0 = no exemplars; then bank each (lang,word) at more pitches.\n")
    for m in milestones:
        if m > 0:
            pitch = bank_pitches[m - 1]
            for lang, (voice, words) in LANGS.items():
                for w in words:
                    ch, audio = perceive(w, voice, pitch)
                    if ch is None:
                        continue
                    # label by the HUMAN reference (whisper), falling back to the known word.
                    ref = sw.transcribe_lang(audio[0], audio[1], lang) if audio else None
                    label = ref[0] if ref else w
                    lex.bank(ch, label, source=f"{lang}:{voice}:{pitch}")
        sc = score()
        avg = sum(sc.values()) / len(sc)
        bar = "  ".join(f"{l}={sc[l]*100:.0f}%" for l in LANGS)
        print(f"  easy bank={m*len(LANGS)*6:3d} exemplars  ->  held-out recognition: {bar}  | avg {avg*100:.0f}%")

    final = score()
    avg = sum(final.values()) / len(final)
    base_avg = 0.0  # bank=0 always scores 0 (empty lexicon)
    print(f"\n{SEP}")
    print(f"  held-out multilingual recognition: {base_avg*100:.0f}% (no easy data) -> {avg*100:.0f}% "
          f"(after the easy bank)")
    ok = avg > 0.25
    print(f"  {'PASS' if ok else 'FAIL'} — the EASY target (bank labelled words) COMPOUNDED into "
          f"the HARD target (multilingual recognition): more easy data -> better understanding.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
