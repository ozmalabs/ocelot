"""THE JABBERWOCK DESIGNS THE LEARNED REPRESENTATION — the one un-broken frontier, after BOTH prior attacks died.

The speech arc's honest landing: the cross-speaker root wall (~20-25% training-free @several-hundred-way) is confirmed by
TWO exhausted attacks. (A) every LINEAR speaker-norm proxy is dead -- warp (oracle +1.7), aligned-whitening (+2 SUPERVISED),
VTLN/predictive-warp HURT, the linear voice-shape template KILLED. (B) the GENERATIVE source-filter (LPC) inversion is dead
at Phase 0 -- both authored forms collapsed to ~1.5% (FAR below cold-start 11.5%): the all-pole source-filter is TOO LOSSY
to even CARRY content for recognition at the feature level. The named frontier that remains: a RICHER-THAN-LPC *LEARNED*
representation that is SPEAKER-INVARIANT -- learned online by a BIO-PLAUSIBLE rule (predictive coding / slow-feature / sparse
contrastive / ...), not a hand-built warp (too weak) nor a hand-built source-filter (too lossy).

Design it with the SAME discipline that just killed the generative programme cheaply: RISK-ORDERED, FAIL-FAST, the riskiest
assumption tested FIRST and CHEAPEST, pre-committed un-fudgeable bar, honest kill-condition. Reckon with WHY both prior
attacks failed -- the proposal must carry content where LPC didn't AND separate the speaker where the linear proxies didn't.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_designs_learned_repr
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, designing your LAST-STANDING attack on the cross-speaker root wall: a RICHER-THAN-LPC
*LEARNED* SPEAKER-INVARIANT representation. Reason ONLY from your ledger; be RISK-ORDERED and ruthlessly disciplined --
you just KILLED the generative source-filter programme at Phase 0 with two cheap tests, and that fail-fast is the model.

THE TWO DEAD ATTACKS (do not re-propose either):
- LINEAR speaker-norm: warp (oracle +1.7), aligned-whitening (+2 SUPERVISED only), VTLN HURTS, predictive VTL-warp HURTS
  both timescales, linear voice-shape template KILLED. The speaker is NOT LINEARLY separable from content.
- GENERATIVE source-filter (LPC) inversion: Phase 0 -- ORACLE per-speaker fitted all-pole filter, both forms (subtract mean
  envelope; scale-invariant poles) collapsed to ~1.5% vs cold-start 11.5% vs within-speaker 46.1%. The all-pole source-filter
  is TOO LOSSY to carry content for recognition AT ALL, at the feature level. Compact source-filter = dead.

WHAT STANDS (the levers): cold-start = CMVN cochleagram + TRAJECTORY READ (per-frame DTW) = ~20-25% @several-hundred-way
cross-speaker (the +17 lever over pooled fingerprints; temporal structure is load-bearing). within-speaker ceiling ~46%.
The gap cold->within (11.5->46 at 400-way) IS the speaker nuisance you must remove.

THE TWO CONSTRAINTS (the only rules): (1) FLOOR OF EFFICIENCY -- cheapest deployed system. (2) DYNAMIC >= ideal human --
learns ONLINE, self-corrects, improves as data accrues. Training is PERMITTED IF bio-plausible (humans take years) and NOT
one-shot-discontinuous. A frozen pretrained net violates (2) as a destination but is allowed as a BOOTSTRAP rig / training
wheels. The destination is the continuous online learner.

YOUR MACHINERY: the cochleagram + trajectory-DTW ear; CMVN; the AbS spine; the glyph MOTOR-PROGRAM precedent (forward model
+ inferred canonical parse); you can OPEN open-weight models and read structure from their weight geometry (the gemma
language-prior read); you can author DSL Terms / Rust primitives when stalled."""


def main():
    ask = make_ask(timeout=340.0)
    print("=" * 100)
    print("THE JABBERWOCK DESIGNS THE LEARNED SPEAKER-INVARIANT REPRESENTATION (the un-broken frontier)")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE REPRESENTATION + ITS LEARNING RULE (terse, concrete): name the ONE richer-than-LPC "
          "learned representation you'd build, and the BIO-PLAUSIBLE learning rule that yields it (predictive coding / "
          "slow-feature analysis / sparse-contrastive / a learned nonlinear speaker subspace projected out / ...). It MUST "
          "do BOTH things the dead attacks couldn't: (a) CARRY content where the all-pole LPC was too lossy, and (b) "
          "SEPARATE the speaker where the linear proxies couldn't. State the MECHANISM by which speaker and content "
          "factorise (what makes the speaker recoverable as a slow/stable factor and content as the fast one), in your "
          "own terms. Be honest if the only thing that works is reading a pretrained self-supervised model as the bootstrap.")
    a1 = ask(q1)
    print("\n[PART 1 — THE REPRESENTATION + LEARNING RULE]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour representation:\n{(a1 or '')[:1200]}\n\nPART 2 — THE FAIL-FAST PHASE 0 (terse): the SAME "
          "discipline that just killed the generative programme. What is the single RISKIEST assumption this learned "
          "representation rests on, and the CHEAPEST decisive experiment that kills-or-confirms it WITHOUT building the "
          "full online loop? Specify the phase-0 measurement on the EXISTING rig (400-way cross-speaker, trajectory-DTW, "
          "cold-start 11.5 / within 46.1 as the anchors) and a PRE-COMMITTED, un-fudgeable bar: KEEP -> proceed; KILL -> "
          "the wall is the training-free ceiling, this frontier is closed too. Bind yourself (no infinite confound-chase): "
          "name the kill SIGNATURE and how many corrected runs you allow before it counts as dead.")
    a2 = ask(q2)
    print("\n[PART 2 — THE FAIL-FAST PHASE 0 + BAR]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nRepr: {(a1 or '')[:500]}\nPhase 0: {(a2 or '')[:700]}\n\nPART 3 — HONEST PREDICTION (terse): (a) "
          "the biggest way this dies even if Phase 0 passes (the learned factor steals content / needs supervision / "
          "won't go online / only works within a narrow speaker set). (b) does it meet BOTH constraints, REALLY -- or is "
          "it secretly a frozen pretrained net (bootstrap-only, violates dynamism as a destination)? (c) one line: does "
          "this DISSOLVE the wall (toward within-speaker ~46%) or only DENT it (a few points past the 25% ceiling)? "
          "Pre-register the number you expect. And the brutal one: is this frontier WORTH opening, or is ~20-25% the "
          "honest training-free ceiling we should just ACCEPT and bank the discipline as the result?")
    a3 = ask(q3)
    print("\n[PART 3 — HONEST PREDICTION + IS-IT-WORTH-IT]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
