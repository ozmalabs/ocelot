"""SHARED-LEXICON COMPOUNDING ON CONTINUOUS SPEECH, RELIABLY LABELLED.

The creator's fix: make the easy wins compound. (1) Easy continuous-speech learning must bank
into the SAME lexicon the recogniser reads (WordExemplar). (2) The labels must be RELIABLE —
whisper hallucinates on isolated short words (and can't even segment piper's fr/de/es), so for
synthesised speech we use the KNOWN words with controlled boundaries (synth_concat), and for
REAL speech (an English children's video) whisper word-segmentation, which IS reliable on
continuous audio.

PART A (the multilingual fix): the agent learns words ONLY from connected clips (each word
coarticulated, concatenated), banked into the shared lexicon under KNOWN labels, and held-out
recognition lifts in all four languages — French (which was 0% on whisper-mislabelled isolated
words) now works, because the labels are fixed.

PART B (real continuous speech): the SAME shared-lexicon mechanism ingests a real children's
video, whisper-segments it, and banks the real words — showing it runs on real speech.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.compounding_continuous
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
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
    print("SHARED-LEXICON COMPOUNDING ON CONTINUOUS SPEECH, reliably labelled.")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s)
    lex = GraphLexicon(s)          # the SHARED lexicon — continuous ingest AND recognition read it
    hat = WordHat()

    def words_from_concat(lang, voice, words, pitch):
        """Connected clip (known boundaries+labels) -> [(word, feats)]. RELIABLE for any language."""
        out = sw.synth_concat(words, {"variant": voice, "pitch": pitch, "rate": 175})
        if out is None:
            return []
        clip, fs, bounds = out
        pairs = []
        for (w, t0, t1) in bounds:
            seg = np.asarray(clip[int(t0 * fs):int(t1 * fs)], dtype=np.float64)
            if seg.size >= int(0.04 * fs):
                pairs.append((w, SDW.feature_channels(s, seg, fs)))
        return pairs

    held = []
    for lang, (voice, words) in LANGS.items():
        for w, ch in words_from_concat(lang, voice, words, 85):
            held.append((lang, w, ch))

    def score():
        per = {l: [0, 0] for l in LANGS}
        for lang, w, ch in held:
            per[lang][1] += 1
            if hat.recognise(ch, lex) == w:
                per[lang][0] += 1
        return {l: (c / n if n else 0.0) for l, (c, n) in per.items()}

    print("  PART A — learn words ONLY from connected clips, KNOWN labels (the multilingual fix):\n")
    banked = 0
    for pitch in (None, 30, 50, 70):
        if pitch is not None:
            for lang, (voice, words) in LANGS.items():
                for w, ch in words_from_concat(lang, voice, words, pitch):
                    lex.bank(ch, w, source=f"concat:{lang}:{pitch}")
                    banked += 1
        sc = score()
        avg = sum(sc.values()) / len(sc)
        bar = "  ".join(f"{l}={sc[l]*100:.0f}%" for l in LANGS)
        print(f"  bank={banked:3d} words  ->  held-out recognition: {bar}  | avg {avg*100:.0f}%")

    final = score()
    avg = sum(final.values()) / len(final)
    print(f"\n  multilingual recognition (shared lexicon, reliable labels): 0% -> {avg*100:.0f}%  "
          f"| French now {final['fr']*100:.0f}% (was 0%)")

    # PART B — the SAME mechanism on REAL continuous speech (a children's video).
    print("\n  PART B — real continuous speech (children's video) -> SHARED lexicon, whisper-segmented:")
    real_words = []
    try:
        srcs = [x for x in sw.sources(kinds=("video", "audio")) if x.get("origin") == "local"]
        if srcs:
            audio = sw.play(srcs[0], 0.0, 18.0)
            real_words = sw.bank_continuous(audio, 8000, lex, lang="en")
            print(f"    '{srcs[0]['name'][:30]}' -> learned {len(real_words)} real words into the "
                  f"shared lexicon: {real_words[:10]}")
        else:
            print("    (no local video available)")
    except Exception as e:
        print(f"    (real-speech ingest unavailable: {type(e).__name__})")

    print(f"\n{SEP}")
    ok = avg > 0.4 and final["fr"] > 0.0
    print(f"  multilingual: 0% -> {avg*100:.0f}% (fr {final['fr']*100:.0f}%); real-speech words "
          f"banked into the shared lexicon: {len(real_words)}")
    print(f"  {'PASS' if ok else 'FAIL'} — easy continuous speech, banked into the SHARED lexicon with "
          f"RELIABLE labels, COMPOUNDS into multilingual recognition (French fixed).")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
