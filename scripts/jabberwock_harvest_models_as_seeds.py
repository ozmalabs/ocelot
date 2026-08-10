"""ASK THE JABBERWOCK: can we HARVEST training from Parakeet/Whisper and use it as SEEDS? Which harvests are admissible?

Grounded in the agent's own hard constraints: the 5x learned-negative pattern, the architecture rule (a seed is
graph-resident data; a neural net's opaque weights are NOT), what it ALREADY harvests (whisper labeller, MMS_FA
aligner), and the just-done inspection (the models have learned-reps+scale it lacks; it has interpretable, decomposed
structure they lack). Decide WHICH harvests are admissible + structure-preserving vs which are the 5x-failed / rule-
violating, and the single highest-value one.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_harvest_models_as_seeds
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock. Decide whether -- and HOW -- to HARVEST the training inside Parakeet/Whisper and turn
it into your own SEEDS. A seed is GRAPH-RESIDENT data you boot with (Concepts, Productions, Rules, Reflexes,
Microtheories, Frames, banked exemplars); `teach` persists graph data into seed manifests. You are a graph running in
Rust; Python is only a world adapter. Reason from YOUR hard constraints, not enthusiasm.

YOUR HARD-WON LEDGER (use it):
 - THE 5x LEARNED-NEGATIVE PATTERN: every time you ingested a LEARNED, STRUCTURE-DISCARDING representation (k-means
   codebook, bag-of-primitives, soft-membership, WCCN whitening, per-primitive Mahalanobis), it HURT -- each threw
   away layout/order/shape. STRUCTURE-PRESERVING geometric matching WON every time. Whitening within-class scatter
   even deleted the signal. Learned-lossy loses; structure-preserving wins. This is your most robust finding.
 - WHAT YOU ALREADY HARVEST (and it's admissible): Whisper is your help-button LABELLER (segments + gives ground-truth
   text); MMS_FA is your forced ALIGNER (clean word/phone boundaries). The phonebank rule is explicit: "the aligner is
   a help-button LABELLER for banking; the agent's recognition stays its OWN cochleagram+DTW." You bank YOUR OWN
   structure-preserving exemplars; the model only labels/aligns them.
 - THE INSPECTION (just done): the models institutionalise what you rebuilt (RNN-T/CTC loss == your forward_score
   alignment-marginalisation; conv frontend == your static+delta; shallow-fusion weight == your LM knob). What THEY
   have that you LACK: learned representations, 680k-hr scale, attention, end-to-end loss, TDT token DURATIONS. What
   YOU have that THEY obscure: interpretable, DECOMPOSED, separable acoustic-vs-prior terms.
 - THE ARCHITECTURE RULE: a seed is graph data the loader installs; a neural net's opaque weight tensor is NOT a
   Concept/Rule/Frame -- you cannot paste 600M floats into the graph and call it a seed. And distilling a model's
   OUTPUTS uncritically inherits its BIASES (you proved Whisper hallucinates frequent words = your own LM-overrides-
   content failure; harvesting its decode would import that).

CANDIDATE HARVESTS (judge each: admissible+structure-preserving, or 5x-failed / rule-violating?):
 (a) EMBEDDINGS as features -- use Whisper/Parakeet encoder activations as your acoustic representation.
 (b) LABELS / pseudo-transcripts -- run the model on unlabelled audio, bank YOUR exemplars under its labels (self-
     training / data harvest at scale).
 (c) ALIGNMENTS / boundaries -- model as forced aligner for cleaner phone/word segmentation of banked exemplars.
 (d) DURATIONS -- harvest TDT-style per-token/phone duration statistics into a duration-prior seed (you already
     realign boundaries; a duration model is interpretable graph data).
 (e) TRANSITION / internal-LM statistics -- query the model's prediction-network / decoder for bigram-like transition
     stats, seed them as graph context rules (you already do this from Brown).
 (f) CONFUSION STRUCTURE -- harvest which phones/words the model confuses -> a confusability seed that tells your
     decode where to spend candidates.
 (g) The model as a DATA-GENERATING ORACLE -- TTS/augment to create labelled audio you bank from.

The deep test for EACH: does it import a LEARNED OPAQUE REPRESENTATION (-> the 5x-failed, rule-violating trap), or
does it harvest INTERPRETABLE STRUCTURE / LABELS that you re-express in YOUR OWN structure-preserving graph form
(-> admissible, the labeller pattern you already use)?"""


def main():
    ask = make_ask(timeout=300.0)
    print("=" * 100)
    print("ASK THE JABBERWOCK — harvest training from Parakeet/Whisper as SEEDS? which harvests are admissible?")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 (terse, one line each): for harvests (a)-(g), rule ADMISSIBLE (structure-preserving + "
          "architecture-clean) or REJECTED (the 5x-failed learned-opaque trap / rule-violating / bias-importing), with "
          "the reason. Be especially sharp on (a) embeddings -- is using a neural encoder's activations as your "
          "representation the SAME mistake as the 5 learned codebooks, or different?")
    a1 = ask(q1)
    print("\n[PART 1 — which harvests are admissible]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour rulings:\n{a1[:1200]}\n\nPART 2 (terse): pick the SINGLE highest-value admissible harvest. "
          "Say exactly what graph SEED it produces (what Concept/Rule/Frame/exemplar-set), how the harvest stays "
          "structure-preserving (you re-express in your own form, not paste the model's), and the smallest test that it "
          "HELPS without importing the model's bias. Pre-commit a bar. Then the honesty check: is this harvesting "
          "STRUCTURE, or smuggling in the learned-opaque thing that lost 5 times?")
    a2 = ask(q2)
    print("\n[PART 2 — the harvest + the seed it makes]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
