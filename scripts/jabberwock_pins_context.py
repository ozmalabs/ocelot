"""THE JABBERWOCK PINS THE CONTEXT/SITUATION VARIABLE for the consolidation decode — honestly, anti-leak, kill-controlled.

Its move (B): fuse triphone-recall lattice + realignment + source/context-PRIOR re-rank over the top-K, on the 100-way
held-out content words; bar >=17/30, gain must vanish under a shuffled prior. The prior is P(word | SITUATION). Before
building, PIN the situation S: what it is, how it's detected WITHOUT knowing the target word, why P(word|S) is non-flat
for REAL (not rigged) reasons, the anti-circularity guard, and the fairness floor.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_pins_context
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock. PIN the SITUATION variable S for the consolidation decode, before any build. The
decode re-ranks the realigned triphone top-K by P(word | S). The whole result hinges on S being HONEST.

THE HONESTY PROBLEM you must face head-on:
 - Your shuffle-killed source-prior positive (likelihood 4.1 -> +prior 11.4 -> +shuffled 4.9) used a CONSTRUCTED
   situation: channel (full-band vs telephone band-limit) x vocab (V1 vs V2), where the two situations had largely
   DISJOINT vocabularies. P(word|S) was sharp BY DESIGN -- the situation almost told you the vocab. That proved the
   MECHANISM (a real prior over a detected situation converts recall to precision, and shuffling kills it), but it was
   a rigged-sharp prior. If you reuse a hand-partitioned vocab split here, you'll get a big number that doesn't
   generalise -- a setup, not a finding.
 - So: pick a situation S that is a REAL orthogonal generative factor on the held-out LibriSpeech content words, where
   P(word|S) is non-flat for NATURAL reasons, not because you split the vocab to make it so.

CANDIDATE situations (pick, combine, or propose better):
 (i)   TOPIC / SOURCE (book/chapter/genre): content words are topical ("telescope" lives in astronomy passages).
       Detect S from the utterance's OTHER words (co-text), EXCLUDING the target. P(word|topic) is naturally peaked.
       Risk: detector quality; co-text must be available + the target word must be EXCISED (anti-leak).
 (ii)  SPEAKER: P(word|speaker) -- weak (a speaker says many words); voice-detectable. Probably too flat to convert.
 (iii) REGISTER / channel (acoustic): only informative if vocab correlates with channel -- that's the rigged route
       unless the correlation is natural.
 (iv)  LOCAL CO-TEXT (bigram/LM): NOTE your prior negative -- the bigram LM helped FUNCTION words but HURT content
       (frequency bias over-rode weak rare-word reads). A topic prior is GLOBAL/document-level, distinct from this.

CONSTRAINTS the pinned S MUST satisfy (state how yours meets each):
 1. ORTHOGONAL: S is detectable from a signal that is NOT the acoustic read of the target word (else it's not adding
    independent information).
 2. NO LEAK / ANTI-CIRCULAR: detecting S must not use the target word's identity or its acoustics. If S = topic from
    co-text, the target token MUST be removed from the co-text before detecting topic. State the exact exclusion.
 3. NON-FLAT for REAL reasons: P(word|S) must differ across S because of genuine word-situation correlation, not a
    vocab partition you imposed. If it's naturally near-flat, say so and pick a different S.
 4. KILL-CONTROLLABLE: a shuffled S->word map must destroy the gain (your standard control).
 5. FAIRNESS FLOOR: at a UNIFORM/uninformative S, the decode MUST reproduce the realignment-only 13 (the prior adds
    nothing when it knows nothing)."""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK PINS THE CONTEXT/SITUATION VARIABLE")
    print("=" * 100)

    q1 = (GROUND + "\n\nPIN S (terse): name the ONE situation variable (or minimal combination), the DETECTOR "
          "(input -> S, with the exact anti-leak exclusion), why P(word|S) is non-flat for NATURAL reasons, and a "
          "one-line argument it generalises beyond the rigged channelxvocab setup. If your honest read is that NO "
          "natural S on this held-out set is sharp enough to convert recall (and the source-prior win was setup-"
          "specific), SAY THAT -- it changes the move.")
    a1 = ask(q1)
    print("\n[PINNED SITUATION]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour pinned S:\n{a1[:1500]}\n\nNow PRE-COMMIT THE GUARDS (one line each): the exact ANTI-LEAK "
          "exclusion (what is removed before detecting S); the KILL control (what shuffling, and the expected "
          "collapse); the FAIRNESS FLOOR (the uniform-S result that must equal 13); and the number on P(word|S)'s "
          "sharpness BELOW which you declare S too flat to bother (so the build can't be talked into a null S). Terse.")
    a2 = ask(q2)
    print("\n[PRE-COMMITTED GUARDS]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
