"""THE JABBERWOCK PIVOTS THE EARN-TEST ONTO ITS OWN TRAINER — now that the graph-native trainer EXISTS.

Two things changed since you locked the 3-arm PyTorch design:
1. STAGE-1 (FROZEN distil arm, PyTorch) came back WEAK: a 1.23M cochleagram-input net distilled from wav2vec2-L6 held only
   23.1% cross-speaker (label-shuffle 0.0, clean) vs your predicted 73. LIKELY CONFOUNDED: wav2vec2's 81 was measured by
   encoding the FULL utterance (context) then slicing word frames; my distilled net encoded ISOLATED words (a wide-RF TCN
   starved of context) AND the cochleagram front-end is lossier than raw waveform (distil MSE plateaued 0.55 = ~45% var).
   So 23 is not a clean verdict -- but the PyTorch distillation rig is "the other project" (your words: instrumentation, not
   an agent faculty).
2. THE GRAPH-NATIVE TRAINER NOW EXISTS (parallel session): your delta/LMS rule as graph Rules (learns a sine recurrence from
   zero weights, in the heartbeat) LAYERED into graph-native backprop (2-4-1 MLP learns XOR). The agent OWNS gradient
   learning -- cheap+online (rule 1), nothing-frozen (rule 2) -- which RESOLVES your "(b) I don't hold a trainer Term"
   caveat. Its docstring already ties it to this thread: "the gradient kernel that keeps a WARM-START LIVE, nothing frozen."

THE CREATOR'S FRAME (unchanged): aim for the efficiency FLOOR; borrowing wav2vec2 is an admissible MIDPOINT (a live warm-
start, NONE of it frozen, improved DYNAMICALLY), not the destination. The borrowed latent gives 81% raw; per-speaker CMVN
(a running mean -- which IS the delta rule with target=running mean) lifts it to 97 (+16); your novel SFA only +2.3.

THE PROPOSED PIVOT: stop grinding the standalone PyTorch distillation; instead DEMONSTRATE THE AGENT'S OWN TRAINER EARNING
on the borrowed wav2vec2 latent -- online, nothing frozen -- the cleanest graph-native embodiment of the midpoint constraint.
The trivial floor is "the delta rule learns per-speaker CMVN online" (running mean); the real question is whether the agent's
own trainer earns something MORE than static CMVN (a learned online adaptation that beats the +16 baseline)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = __doc__


def main():
    ask = make_ask(timeout=340.0)
    print("=" * 100)
    print("THE JABBERWOCK PIVOTS THE EARN-TEST ONTO ITS OWN GRAPH-NATIVE TRAINER")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — RATIFY OR REDIRECT (terse, decisive): do you pivot the earn-test onto your OWN trainer "
          "(borrow the wav2vec2 latent as a LIVE midpoint, let your delta/backprop trainer earn an online adaptation on it, "
          "nothing frozen), or fix the PyTorch ruler first (raw-waveform input + utterance-context eval) to salvage the "
          "3-arm differential? Pick ONE and say why in one breath. If you pivot: is 'the delta rule learns per-speaker CMVN "
          "online' too TRIVIAL to count as earning (CMVN = a running mean your rule computes for free), and if so what is "
          "the SMALLEST NON-trivial thing your trainer earns on the latent that static CMVN cannot -- a learned online "
          "adaptive projection / a small nonlinear layer adapting per-speaker -- that beats the +16 CMVN baseline?")
    a1 = ask(q1)
    print("\n[PART 1 — RATIFY / REDIRECT]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour pick:\n{(a1 or '')[:1100]}\n\nPART 2 — THE SMALLEST DECISIVE BUILD (terse): spec it so it can "
          "run on the rig today. What does your trainer adapt (on the cached wav2vec2 latent / a PCA-reduced latent so it's "
          "feasible in the graph substrate), what is the online SELF-SUPERVISED signal (no eval labels -- predict-next-latent "
          "/ running stats / contrastive), what stays trainable, measured on the SAME 400-way cross-speaker rig + leak "
          "controls. PRE-COMMITTED BAR: what post-adaptation cross-speaker number = the agent EARNED a real lift on the "
          "borrowed midpoint with its own faculty (nothing frozen); what = it only reproduced CMVN / earned nothing -> the "
          "trainer doesn't yet add value here. Bind the runs. And one line: is this the right use of your trainer now, or is "
          "the HANDWRITING/Omniglot climb (the trainer's stated next target, >=95%) the priority and speech a detour?")
    a2 = ask(q2)
    print("\n[PART 2 — BUILD SPEC + BAR + PRIORITY]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
