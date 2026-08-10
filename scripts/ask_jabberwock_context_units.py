"""Ask the jabberwock how to build context-dependent sub-word units -- its evidence-located next lever.

Grounded in the falsified aligner result: the OOV read from phones is real (24% top-3, 6x chance) but CAPPED,
and iterating the aligner HURT -- so the limit is the UNIT (phones are context-blind: /t/ in 'stop' != /t/ in
'water'). The agent decides how to make units context-aware WITHOUT re-creating the sparsity it just escaped.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock. Your real-speech ladder, each rung proven on a one-variable test:

  rep (DTW over cochleagram frames)  ->  +10pt recall (pooling discarded the time course)
  phone units read a NEVER-BANKED word from parts  ->  24% top-3 = 6x chance (open vocab, CMUdict + DtwTo)
  iterate the aligner (EM forced-align)  ->  REFUTED, it HURT (24->14%): the boundary aligner is NOT the limit.

So your OWN fork now points here: the limit is the UNIT. A context-free phone is too coarse -- a banked /t/ from
"stop" is acoustically not the /t/ in "water" (aspiration, flap, the neighbour's coarticulation). A single phone
model averages those into mush, and no re-alignment fixes it. You need CONTEXT-DEPENDENT units. Sharpen the read.

THE TRAP YOU MUST SOLVE (this is the crux, not a footnote). Context-dependence re-creates the very sparsity you
just ESCAPED with phones. 40 phones -> 40^3 = 64k triphones; on a real bank MOST are unseen, so a held-out
word's triphones are themselves OOV -- you would be back to "can't read a unit you never banked", one level
down. Any answer that ignores this fails. The classic fix is TYING: cluster acoustically-similar contexts so
each cluster has enough exemplars AND an unseen context maps to its nearest cluster. You must say how a context
a word needs, that you never banked, still gets a model.

WHAT YOU HOLD (compose; do not assume you must invent):
 - the phone bank + DtwTo matcher (works), CMUdict (word->phones, hence the left/right neighbours of each phone).
 - TRANSITION / dynamic cues (formant motion over time) and the order-N-over-time operator -- coarticulation IS
   a transition phenomenon; a phone modelled WITH its dynamics may capture context without exploding the inventory.
 - clustering faculties (cross_speaker_clustering; your competitive_inhibition / shape machinery) -- the tying tool.
 - your holdout diagnostic + EM aligner machinery (jabberwock_reads_oov_from_phones / iterate_aligner).

DECIDE, concretely and in your own terms:
 1. WHAT is the context-dependent unit, weighed against the sparsity trap:
    (a) TRIPHONE with state TYING / context CLUSTERING (capture full context, back off unseen contexts to the
        nearest cluster) -- powerful but you must specify the clustering + the unseen-context map;
    (b) BIPHONE / DIPHONE (one-side context / the boundary transition) -- far fewer units, coarticulation lives
        at boundaries; cheaper, less sparse;
    (c) the same MONOPHONE but modelled WITH its DYNAMICS (transition cue / order-N over its frames) -- context
        via the within-phone trajectory, NO inventory growth at all;
    (d) position-in-syllable / left-XOR-right context only.
    Pick one (or a principled combination) and JUSTIFY it AGAINST the sparsity trap specifically.
 2. THE UNSEEN-CONTEXT MAP: a held-out word needs a unit-context you never banked. How does it still get a
    model (cluster back-off? the dynamics carrying it so context is implicit? a similarity tie)? Be concrete.
 3. The first RUNNABLE step on your existing holdout (jabberwock_reads_oov_from_phones): one new unit definition,
    SAME bank/targets/forced boundaries, measured against the 24% top-3 monophone baseline. The clean read: does
    a context-aware unit lift the OOV read WITHOUT the unseen-context sparsity killing it?
 4. What you MEASURE (OOV-word top-1/top-3 from parts, vs 24%) and the honest risk (sparsity wins / the dynamics
    cue too weak / clustering ties the wrong contexts).

Be concise and concrete -- the next move you'd hand to yourself."""


def main():
    ask = make_ask(timeout=420, preamble=PREAMBLE)
    print(ask("How do you build context-dependent units that sharpen the OOV read without re-creating sparsity? "
              "Decide and give the step."))


if __name__ == "__main__":
    main()
