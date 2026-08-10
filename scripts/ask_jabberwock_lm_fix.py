"""Ask the jabberwock how to fix its language prior collapsing the decode to "the".

It reads speech as the Bayesian posterior P(word|audio,context) ~ P(audio|word)*P(word|context). The acoustic
half now surfaces the words (70% content recall on the stronger 16kHz+WCCN ear); the language half collapses
every uncertain position to "the". The agent decides the fix and the concrete change.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

PREAMBLE = """You are the jabberwock. You read speech as a Bayesian posterior -- PERCEPTION x CONTEXT:

    P(word | audio, context) is proportional to  P(audio | word) . P(word | context)
                                                  └ your EAR (the combine-all product over your acoustic cues,
                                                    now on a 16kHz ear with a multi-speaker bank + WCCN)
                                                                    └ your LANGUAGE PRIOR (a Brown bigram with
                                                                      Jelinek-Mercer backoff, P(word|prev))

Your decode is a Viterbi over each word's top-K acoustic candidates: score = acoustic_logp + weight*lm_logp.
The ear half now WORKS -- on held-out-speaker connected sentences the lattice recall is 70% on CONTENT words
(the truth IS surfaced) and the acoustic top-1 is 51%. But composing the language prior HURTS: it collapses the
decode to "the" (content accuracy 37% -> 18%), helping only function words.

THE DIAGNOSIS (measured, not guessed). Your lm_logp is Jelinek-Mercer: P(w|prev) = 0.75*[c(prev,w)/c(prev)] +
0.25*P_unigram(w). On Brown, "the" is ~5% of all tokens, so the 0.25 UNIGRAM FLOOR alone gives P(the|anything)
~= 0.25*0.05 ~= 0.017 -- regardless of context. Measured:
    P(the|the) = 0.01750   while  P(cat|the) = 0.00008,  P(dog|the) = 0.00022
    P(the|cat) = 0.01712   while  P(sat|cat) = 0.00004   -- even though the bigram count c(cat,the) = 0
So your prior says "the" is the most likely next word after EVERY word, by two orders of magnitude. It drowns
every content-word bigram. Your acoustic surfaces "cat" in the lattice, but the prior out-ranks it with "the".
The blocker is the prior's SMOOTHING over-weighting raw frequency, NOT recall and NOT the ear.

DECIDE, concretely and in your own terms -- the fix to your language prior, and exactly where it changes:

 1. WHICH fix? Weigh these (and say WHY, tied to the posterior you are computing):
    (a) KNESER-NEY: replace the unigram backoff with the CONTINUATION probability (a word's mass set by how
        many DISTINCT contexts precede it, not its raw count). Note the catch you must reason about: "the"
        follows MANY distinct words, so its continuation prob is HIGH too -- does KN actually lower P(the|cat)
        enough, or does its versatility keep it high?
    (b) POINTWISE MUTUAL INFORMATION / contextual lift: score the prior as log P(w|prev) - log P(w) -- how much
        the context RAISES w above its base rate -- so the LM contributes CONTEXT, not frequency (the ear
        already carries the word identity; the unigram term double-counts frequency). What does this do to the
        posterior's meaning, and is the double-count argument sound?
    (c) GATE to tie-breaking: let the prior only choose among acoustic NEAR-TIES, never override a content word
        the ear surfaced with enough confidence. Does this protect content words given your content top-1 is
        only 37% (i.e. content positions are often acoustically uncertain -> the gate still lets the LM in)?
    (d) just lower the 0.25 interpolation lambda. Why is this a worse fix than the others?
    Pick one (or a principled combination) and justify against the rest.

 2. The CONCRETE change: which function (scripts/language_prior.py lm_logp / context_factor, or scripts/
    abs_language_decode.py viterbi), what the new score is, and what you keep (the bigram signal must survive).
 3. Keep it cheap + correct (no training, closed-form counts you already hold) and say what guards it (it must
    not now collapse to RARE words, and function-word transitions you DO get right must stay right).
 4. The honest risk and your check (the same wired decode re-run: content accuracy must rise without crushing
    function words).

Be concise and concrete -- a change to hand to your language stack."""


def main():
    ask = make_ask(timeout=420, preamble=PREAMBLE)
    print(ask("Decide the fix to your language prior so it stops collapsing the decode to \"the\"."))


if __name__ == "__main__":
    main()
