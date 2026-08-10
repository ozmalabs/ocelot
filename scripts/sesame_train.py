"""TRAIN THE JABBERWOCK ON SESAME STREET — real continuous speech, its own ear.

Past WER work was synthetic number-words (piper, silence-gapped). This is REAL speech: the agent
hears the Sesame Street episode 'Can They Be Friends?' off jellyfin, through its OWN 8 kHz cochlear
ear. On natural continuous speech there are no silence gaps, so the agent's silence-based segmenter
can't find word boundaries — whisper (the human-proxy teacher) segments + labels the stream, and the
agent LEARNS RECOGNITION: it banks each heard word as a feature exemplar into its lexicon. Then on a
HELD-OUT later stretch it recognises, through its own ear, the words it has heard before — and we
measure how often it is right (vs whisper's label) and how much of the held-out speech it now covers.

Open vocabulary, Zipf-distributed (many words heard once) — a genuinely harder world than 6 number
words. We report what the agent LEARNED (vocabulary, coverage) and how well its ear recognises it.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.sesame_train [train_min]
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
from domains.speech_world import SpeechWorld, FS
from domains.speech_world_recognizer import GraphLexicon, WordHat
from scripts.source_world import SourceWorld

SEP = "=" * 86


def _audio(sw, src, t0, t1):
    a = sw.play(src, t0, t1)
    if isinstance(a, tuple):
        a = a[0]
    return np.asarray(a, dtype=np.float64)


def main():
    train_min = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
    print(SEP)
    print("TRAIN THE JABBERWOCK ON SESAME STREET — real continuous speech, its own ear.")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s, source_world=SourceWorld(include_jellyfin=True))
    lex = GraphLexicon(s)
    hat = WordHat()
    src = next((x for x in sw.sources() if "sesame" in str(x.get("name", "")).lower()), None)
    if src is None:
        print("  Sesame Street not found on jellyfin."); return 1
    print(f"  source: '{src['name']}'  (the agent hears it through its own 8 kHz ear)\n")

    # TRAIN — stream in 30 s chunks; whisper segments+labels, the agent banks each word it hears.
    print(f"  LEARNING from {train_min:.0f} min of Sesame Street (whisper labels, agent ear):")
    chunk = 30.0
    tok = 0
    t = 0.0
    while t < train_min * 60:
        audio = _audio(sw, src, t, t + chunk)
        if audio.size < FS:
            break
        before = lex.size()
        words = sw.bank_continuous(audio, FS, lex, lang="en")
        tok += len(words)
        if int(t) % 60 == 0:
            print(f"    {t/60:4.1f} min: {tok:4d} tokens heard, {lex.size():4d} exemplars, "
                  f"{len({w for (w, _v) in lex.banked()}):4d} distinct words")
        t += chunk
    vocab = {w for (w, _v) in lex.banked()}
    print(f"\n  LEARNED: {lex.size()} word exemplars, {len(vocab)} distinct words from {tok} tokens.")

    # how many exemplars the agent has per word (Zipf — most words heard once).
    from collections import Counter
    wcount = Counter(w for (w, _v) in lex.banked())

    # HELD-OUT — a later stretch the agent never trained on. Recognise the in-vocab words,
    # bucketed by how many times the word was HEARD in training (does the ear work when sampled?).
    print(f"\n  TEST on HELD-OUT speech ({train_min:.0f}-{train_min+2:.0f} min): the agent's ear vs whisper:")
    buckets = {"1 (singleton)": [0, 0], "2": [0, 0], "3-5": [0, 0], "6+": [0, 0]}

    def bkey(c):
        return "1 (singleton)" if c == 1 else "2" if c == 2 else "3-5" if c <= 5 else "6+"
    correct = total = oov = 0
    th = train_min * 60 + 30
    for _ in range(4):                                  # ~2 min of held-out, 30 s chunks
        audio = _audio(sw, src, th, th + chunk)
        if audio.size < FS:
            break
        for (w, t0, t1) in sw.transcribe_lang_timed(audio, FS, "en"):
            seg = audio[int(t0 * FS):int(t1 * FS)]
            if seg.size < int(0.04 * FS):
                continue
            if w not in vocab:
                oov += 1
                continue
            total += 1
            ok = hat.recognise(SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS), lex) == w
            correct += int(ok)
            b = buckets[bkey(wcount[w])]
            b[1] += 1; b[0] += int(ok)
        th += chunk
    acc = correct / total if total else 0.0
    cover = total / (total + oov) if (total + oov) else 0.0
    print(f"    in-vocab recognition: {correct}/{total} = {acc*100:.0f}% correct (its ear on real speech)")
    print(f"    by training exemplars per word (is it the ear, or data sparsity?):")
    for k in ("1 (singleton)", "2", "3-5", "6+"):
        c, n = buckets[k]
        print(f"        heard {k:>13}x: {c:3d}/{n:3d} = {c/n*100:3.0f}%" if n else
              f"        heard {k:>13}x: (none)")
    print(f"    vocabulary coverage of held-out speech: {cover*100:.0f}% "
          f"({oov} tokens were words it had never heard — the open-vocab frontier)")
    print(f"\n{SEP}")
    print(f"  The jabberwock trained on Sesame Street through its OWN ear: {len(vocab)} words learned, "
          f"{acc*100:.0f}% in-vocab recognition on held-out real speech, {cover*100:.0f}% coverage.")
    print(f"  Frontier: the {oov} never-heard words (open vocabulary) and word SEGMENTATION on gapless")
    print(f"  natural speech (whisper still finds the boundaries — the agent's silence cue needs gaps).")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
