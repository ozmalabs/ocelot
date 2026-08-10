"""THE JABBERWOCK READS THE ROBUST CHEAP-EARN NEGATIVE — a different angle, or land?

You designed the speech earn-not-borrow investigation. It is COMPLETE and well-controlled, and it is a NEGATIVE on the cheap
side. Read it honestly and decide: is there a fundamentally DIFFERENT cheap angle (a specific inductive bias, NOT brute
distillation/scale), or is the honest truth that this invariance is scale/depth-bound and we LAND?

THE FULL RESULT (400-way cross-speaker rig, trajectory-DTW; anchors cochleagram 11.5 / within-speaker 46 / borrowed
wav2vec2 81; all leak controls pass throughout):
- THE WALL IS NOT FUNDAMENTAL: a learned representation (BORROWED wav2vec2-base, 95M, SSL on LibriSpeech-960h) gives 81%
  cross-speaker (vs the cochleagram's ~11-25 you'd called the training-free ceiling). The ~20-25 ceiling was the FIXED
  cochleagram's limit, not physics.
- BUT YOU CANNOT CHEAPLY EARN IT (every cheap route, robust):
  * ADAPT-ON-TOP of the borrowed latent — a learned per-speaker AFFINE WARP (D diag + rank-2 rotation) trained by self-
    supervised contrastive temporal coherence HURT (-5.6 vs the free CMVN). wav2vec2 is already speaker-robust; no linear
    warp left to earn; the unsupervised objective only damaged word content.
  * DISTIL-INTO-SMALL (~1.3M net) caps ~37% REGARDLESS of front-end (32-band cochleagram 32 / log-mel-80 37 / raw-waveform
    CPU-prohibitive) AND regardless of objective (MSE 37 / RELATIONAL cosine-geometry 37.7). Distil MSE plateaus ~0.53.
- DIAGNOSIS: not the front-end (richer input +5 only), not the objective (geometry = MSE) -> it is CAPACITY/DEPTH. A shallow
  ~1.3M CONV net reaches ~within-speaker (46) but not cross-speaker-81. The invariance is a DEEP/CONTEXTUAL/SCALE property:
  12-layer transformer + LONG-RANGE ATTENTION + SSL over thousands of speakers. Conv nets LACK long context.

THE CONSTRAINTS (unchanged): (1) FLOOR OF EFFICIENCY (club not H100); (2) DYNAMIC >= ideal human, learns online, nothing
frozen. Borrowing is an admissible LIVE MIDPOINT (warm-start, none frozen, improved dynamically), not the destination.
RIG LIMIT: CPU-only torch; raw-waveform training was prohibitive (34 min = epoch 0). Bigger nets are CPU-slow."""
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
    print("THE JABBERWOCK READS THE ROBUST CHEAP-EARN NEGATIVE — different angle or land?")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — WHERE DOES THE INVARIANCE LIVE, AND IS THERE A DIFFERENT CHEAP ANGLE? (terse, honest): the "
          "diagnosis says the speaker-invariance is CONTEXTUAL (long-range attention) + learned-over-many-speakers, which a "
          "shallow conv can't hold. Is there a fundamentally DIFFERENT CHEAP angle that earns it WITHOUT brute scale -- a "
          "specific INDUCTIVE BIAS? Candidates to weigh (pick/reject with reason): (a) a small ATTENTION student (the conv "
          "lacks long context; ~3-5M self-attention might hold what a 1.3M conv can't); (b) a STRUCTURED factorisation that "
          "makes the invariance cheap (separate a slow per-utterance speaker code from fast content, explicitly, so the net "
          "doesn't have to LEARN the invariance over thousands of speakers); (c) the invariance only LOOKS cheap-able but is "
          "irreducibly a property of seeing many speakers (so any cheap net must still be TRAINED on many speakers, and the "
          "'cheap' is the net SIZE not the data) -- which would mean LAND. Which is it, and why?")
    a1 = ask(q1)
    print("\n[PART 1 — WHERE IT LIVES / DIFFERENT ANGLE]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour read:\n{(a1 or '')[:1100]}\n\nPART 2 — DECIDE (terse): either (A) name the ONE cheapest decisive "
          "test of your different angle that fits a CPU rig (what it builds, the measurement on the same 400-way rig, the "
          "pre-committed bar: what number = cheap-earn is alive, what = dead), and bind the runs; OR (B) ratify LANDING -- "
          "state the one-line durable conclusion of the speech earn-not-borrow investigation, and whether the honest status "
          "is 'cheap-earn is impossible' or 'cheap-earn is unproven on a CPU rig but the wall-not-fundamental + methodology "
          "are the wins'. Don't grind: if the different angle is <50/50 to flip it, say LAND.")
    a2 = ask(q2)
    print("\n[PART 2 — DECIDE: TEST OR LAND]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
