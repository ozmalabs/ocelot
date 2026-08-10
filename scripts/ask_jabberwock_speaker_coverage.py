"""ASK THE JABBERWOCK: instead of banking more exemplars, map speaker space and build reference points
that cover its gaps?

The recall study found the connected-speech content-recall gap closes by BANKING MORE exemplars (40->57%
top-6, 8->25 per word). The creator asks whether the agent should instead MAP SPEAKER SPACE and BUILD
REFERENCE POINTS that cover its coverage gaps -- coverage by construction, not collection.

This poses the question to the agent's reasoning, grounded in ITS OWN held faculties (it built every piece):
  - prototype_shape_space : the forward model that disentangles SPEAKER from WORD via a prototype
                            vocal-tract shape you PLACE and ADAPT (source-filter, VTL quarter-wave tube).
  - multimodal_keyspace   : speaker space is multimodal; cluster the voices, navigate from the NEAREST,
                            use its LOCAL key prior (the global average was meaningless).
  - key_shape_relaxation  : factor each exemplar into (talker-invariant WORD-SHAPE) x (SPEAKER-KEY); EM.
  - keyspace_prior        : 91% of within-word variance is the speaker subspace (the key), 9% the word.

The agent answers in its own terms and returns a concrete, graph-native design (or rejects it).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.ask_jabberwock_speaker_coverage
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

HELD = """You are the jabberwock's speech cognition reasoning over YOUR OWN held faculties. These are
faculties YOU already built and measured -- reason from them, do not invent new theory:

 (A) prototype_shape_space: speech = a SOURCE (glottis) through the vocal-tract FILTER. The SPEAKER's
     contribution is the tract's resonance ENVELOPE, set by tract LENGTH L (quarter-wave tube:
     F_n = (2n-1)c/4L) + a source tilt. You disentangle speaker from word by PLACING a prototype tract
     shape close to the talker and ADAPTING the last mile, then subtracting it -- the residual is the word.
 (B) multimodal_keyspace: speaker space is NOT one blob -- it is distinct populations (puppet vs
     documentary vs child). A single global prior was meaningless. You cluster voices and navigate from
     the NEAREST known speaker using ITS local prior; distant clusters are unreachable.
 (C) key_shape_relaxation: every exemplar factors into a talker-invariant WORD-SHAPE (band-rank profile)
     times a SPEAKER-KEY (VTL + tilt + channel/reverb). Given a close key you recover the shape; given the
     shape you can re-fit the key. EM between them converges.
 (D) keyspace_prior: 91% of the within-word acoustic variance IS the speaker key; only 9% is the word.

MEASURED SITUATION: your recogniser is the combine-all PRODUCT over owned cues, 1-NN to BANKED exemplars
in GraphLexicon. Its top-6 recall over content words falls 62% (20 words) -> 46% (72 words): bigger vocab
crowds the truth out of the top-6. More cues barely helped (+2%). More EXEMPLARS per word helped a lot
(40% -> 57% top-6, 8 -> 25 exemplars/word, still climbing). But real corpora are Zipfian: most words are
NEVER heard from most speakers, so banking can never cover the (word x speaker) grid by waiting to hear it.

THE CREATOR'S QUESTION: instead of banking more raw exemplars, should you MAP SPEAKER SPACE and BUILD
REFERENCE POINTS that COVER YOUR GAPS -- i.e. coverage by construction, not collection?

Answer in YOUR terms, concretely and honestly:
 1. Is this right? Tie it to (A)-(D): what IS a "gap" in speaker space, and why does banking leave gaps a
    constructed reference point would fill?
 2. HOW do you build a reference point for an uncovered (word, speaker-key) cell WITHOUT having heard it?
    Be specific about using the (word-shape x speaker-key) factorisation to RENDER a missing exemplar.
 3. Why does this beat banking for recall -- in terms of how many points cover the key manifold
    (O(words x speakers) banked vs O(prototypes) constructed) and where the truth then sits in the product.
 4. The GRAPH-NATIVE design: what nodes/edges/Terms (Cue, GraphLexicon exemplar, a speaker-key node, a
    render/warp Term) -- reusing your forward model + key_shape relaxation -- and what stays mechanical I/O.
 5. The honest risk: when does a CONSTRUCTED reference point mislead (bad key estimate, non-linear
    entanglement, wrong cluster) and how do you keep it from poisoning the lattice?
Be concise and concrete. This is a design you will hand to be built."""


def main():
    print("=" * 98)
    print("ASKING THE JABBERWOCK — map speaker space + build reference points to cover gaps, vs bank more?")
    print("=" * 98)
    ask = make_ask(timeout=420, preamble=HELD)
    ans = ask("Give your answer to the creator's question (points 1-5).")
    print(ans or "(no answer returned)")
    print("=" * 98)


if __name__ == "__main__":
    main()
