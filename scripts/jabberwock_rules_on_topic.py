"""THE JABBERWOCK RULES ON ITS TOPIC-PRIOR ABORT GATE — abort move (B) as scoped? open rare/big-corpus, or land+pivot?"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

G = """You are the jabberwock, ruling on your topic-prior ABORT GATE for the consolidation decode (move B: re-rank the
realigned top-K by P(word|topic)). You pinned S = chapter topic, anti-leak, and pre-committed: median log2 P(w|S) -
log2 P(w) >= 0.5 BITS or ABORT.

THE PILOT RESULT (dev-clean, 97 chapters, 28736 content tokens; per-occurrence boost, leave-one-utterance-out):
  TARGETS (the 24 frequent content words = actual candidate set): ORACLE & DETECTED median -1.47 bits, 9% >= 0.5.
  RARE contrast (corpus count 3-12):                              ORACLE & DETECTED median -0.61 bits, 26% >= 0.5.
  => both < 0.5 => ABORT by the letter.

TWO things are true and you must separate them:
 1) INSTRUMENT CAVEAT (absolute bits under-read): the docs are tiny (~296 tokens) so add-alpha smoothing (alpha*V~803)
    swamps real counts, and leave-one-out zeroes single-occurrence rare words -> even the ORACLE (knowing the true
    document) reads NEGATIVE, a logical impossibility for a sound estimator. So the exact bits are too crude to trust
    as a positive; a proper test needs a TOPIC MODEL estimated on a LARGE corpus (train-clean-100/500), not this tiny
    held-out set.
 2) ROBUST STRUCTURAL SIGNAL (survives the noise): rare > frequent (26% vs 9%; -0.61 > -1.47). The held-out TARGETS
    are FREQUENT content words = intrinsically the LEAST topical; topic cannot convert them regardless of instrument.
    The candidate set is the problem, exactly as your pin anticipated.

RULE NOW (terse, decisive), and HONESTLY weigh that this is the 4th harness-caveated negative in a row -- the
discipline is to not let "the instrument under-read" become an infinite rescue:
 (1) Does the gate ABORT move (B) AS SCOPED (topic re-rank over these frequent targets)? Given structural signal #2,
     is that abort SOUND independent of the instrument caveat?
 (2) Is the rare-word + big-corpus-topic-model regime worth OPENING as a NEW, separately pre-registered experiment
     (your pin's own branch) -- or is that the same over-reach you've warned against, and the honest move is to LAND
     speech at the confirmed realignment win (6->13) and the kill-controlled source-prior, and pivot?
 (3) One-line honesty check: is "rare words on a big corpus would clear it" a real next experiment or motivated
     reasoning dressed as a branch?"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK RULES ON ITS TOPIC-PRIOR ABORT GATE")
    print("=" * 100)
    a = ask(G + "\n\nRule: (1) abort-B-as-scoped? (2) open rare/big-corpus as a NEW experiment, or LAND+pivot? "
            "(3) the one-line honesty check.")
    print("\n[RULING]\n" + (a or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
