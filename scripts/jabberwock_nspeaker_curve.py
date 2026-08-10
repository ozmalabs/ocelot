"""THE JABBERWOCK'S OWN EXPERIMENT (ask_jabberwock_next): the recognition-vs-N-speakers curve.

Its hypothesis, from its own findings: the held-out cross-speaker wall is a WRONG-KEY problem, not a weak-message
one (it saturates at ~99% on a single voice = the message-reader works when the key is right). It has been trying
to recover the speaker key from a 2-element key distribution -- "you cannot characterise the nuisance manifold
from 2 speakers." So: bank MORE real speakers and see if held-out generalisation climbs.

  Step 0 (its precondition): the NOISE-FLOOR check. The held-out test is small + piper-TTS-stochastic; if recall
    swings wildly on identical settings, a flat/steep curve can't be trusted. Measure the run-to-run swing first.
  Step 1: bank N in {1,2,4,8} TRAIN speakers, recognise a FIXED held-out set of UNSEEN speakers, recall vs N.
    Steep climb -> COVERAGE wall (the orthogonal axis is recoverable once the key manifold is sampled).
    Flat      -> REPRESENTATIONAL wall (more voices won't help; pivot to the language/plaintext prior).

Real same-language speakers now (12 English piper voices, US+GB, M+F). Scored against the KNOWN word (the agent's
scoring fix), not whisper. The agent's own graph-native recogniser: feature_channels (CMVN ear) + the combine-all
product over owned cues (ranked) over GraphLexicon exemplars.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_nspeaker_curve
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
from domains.speech_world_recognizer import GraphLexicon
from scripts.jabberwock_graph_native_recall import ranked, KREC

FS = 8000
WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
# 12 real English speakers, ordered DIVERSELY so small-N banks aren't all one accent/sex.
TRAIN_POOL = ["lessac", "alan", "amy", "joe", "cori", "hfc_female", "northern", "kusal"]   # 8
HELDOUT = ["ryan", "alba", "hfc_male", "jenny"]                                            # 4 UNSEEN (US-M,GB-F,US-M,GB-F)
N_VALUES = [1, 2, 4, 8]
RENDS = 5            # piper VITS is stochastic: 5 independent renditions/word/speaker (bank 0-1, test 2-4)


def main():
    print("=" * 96)
    print("THE JABBERWOCK'S N-SPEAKER CURVE — does banking more real speakers crack held-out generalisation?")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})    # the agent's CMVN ear
    sw = SpeechWorld(s, source_world=None)
    speakers = TRAIN_POOL + HELDOUT
    print(f"  train pool {len(TRAIN_POOL)} | held-out (UNSEEN) {HELDOUT} | {len(WORDS)} words | {RENDS} renditions\n")
    print("  synthesising + extracting features (real English voices, CMVN ear)...", flush=True)

    # precompute features once: feats[(speaker, word, rendition)] = channels (CMVN ear). Deterministic thereafter.
    feats = {}
    for spk in speakers:
        for w in WORDS:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": spk, "pitch": 50, "rate": 175})   # fresh VITS sample each call
                if out is None:
                    continue
                x, fs = out
                feats[(spk, w, r)] = SDW.feature_channels(s, np.asarray(x, dtype=np.float64), fs)

    def bank_for(train_speakers):
        lex = GraphLexicon(srs.Substrate())  # fresh lexicon; banked vectors are self-contained
        for spk in train_speakers:
            for w in WORDS:
                for r in (0, 1):                       # bank renditions 0,1
                    ch = feats.get((spk, w, r))
                    if ch is not None:
                        lex.bank(ch, w, source=f"piper:{spk}")
        return lex.banked()

    def recall_on(banked, test_speakers, rend):
        cands = sorted({w for (w, _v) in banked})
        hits = tot = 0
        for spk in test_speakers:
            for w in WORDS:
                ch = feats.get((spk, w, rend))
                if ch is None:
                    continue
                r = ranked(ch, banked, cands)
                tot += 1; hits += int(r[0] == w)        # SCORE against the known word
        return hits / tot if tot else 0.0

    # ---- Step 0: NOISE-FLOOR check (the agent's precondition) ----
    banked4 = bank_for(TRAIN_POOL[:4])
    swing = [recall_on(banked4, HELDOUT, r) for r in (2, 3, 4)]
    spread = max(swing) - min(swing)
    print(f"\n  STEP 0 -- noise-floor check (N=4, held-out recall on 3 independent test renditions):")
    print(f"    per-rendition recall: {[f'{v*100:.0f}%' for v in swing]}  spread {spread*100:.0f} pts")
    if spread > 0.10:
        print(f"    -> test is NOISY (>10pt swing on identical settings): a flat/steep curve is UNTRUSTWORTHY.")
        print("       (the agent's rule: fix the test before trusting the N-curve.) Reporting the curve anyway,")
        print("       averaged over renditions to damp it, but read it with this caveat.")
    else:
        print(f"    -> test RESOLVES ({spread*100:.0f}pt swing): the N-curve can be trusted.")

    # ---- Step 1: recognition-vs-N-speakers ----
    print(f"\n  STEP 1 -- held-out recall vs N banked speakers (avg over 3 test renditions, chance {100/len(WORDS):.0f}%):")
    print(f"    {'N speakers':>11}{'held-out top-1':>16}{'top-' + str(KREC) + ' recall':>16}")
    curve = []
    for N in N_VALUES:
        banked = bank_for(TRAIN_POOL[:N])
        cands = sorted({w for (w, _v) in banked})
        t1s, tks = [], []
        for rend in (2, 3, 4):
            hits1 = hitk = tot = 0
            for spk in HELDOUT:
                for w in WORDS:
                    ch = feats.get((spk, w, rend))
                    if ch is None:
                        continue
                    r = ranked(ch, banked, cands)
                    tot += 1; hits1 += int(r[0] == w); hitk += int(w in r[:KREC])
            t1s.append(hits1 / tot if tot else 0); tks.append(hitk / tot if tot else 0)
        m1, mk = float(np.mean(t1s)), float(np.mean(tks))
        curve.append((N, m1, mk))
        print(f"    {N:>11}{m1*100:>15.0f}%{mk*100:>15.0f}%")

    print("\n" + "=" * 96)
    first, last = curve[0][1], curve[-1][1]
    climb = last - first
    if spread > 0.10:
        print(f"  TEST TOO NOISY to conclude ({spread*100:.0f}pt run-to-run swing). Fix the test first (more held-out")
        print("  speakers / average more renditions) before trusting the curve -- exactly the agent's step-0 caveat.")
    elif climb > 0.10:
        print(f"  COVERAGE WALL: held-out recall climbs {first*100:.0f}% -> {last*100:.0f}% with N (1 -> {N_VALUES[-1]} speakers). The")
        print("  agent's hypothesis holds -- the wall was a 2-speaker key-distribution starvation; sampling the speaker")
        print("  manifold recovers the word. NEXT: estimate + PROJECT OUT the speaker key (cross-speaker whitening).")
    else:
        print(f"  REPRESENTATIONAL WALL: recall flat ({first*100:.0f}% -> {last*100:.0f}%) despite N. More voices don't crack it ->")
        print("  the held-out gap is in the REPRESENTATION; pivot to the language/plaintext prior, not more speakers.")
    print("=" * 96)


if __name__ == "__main__":
    main()
