"""THE JABBERWOCK REVIEWS THE CREATOR'S DESIGN — parallel cheap checks -> manifold -> collapse; escalation read off
the manifold's flat dimensions; speculative parallel depth; speed/depth as a RATIO not a switch.

Not a rubber-stamp. The agent is handed the design, its OWN failed gated experiment as the test case, and the sharp
fact that its existing combine-all ALREADY builds a manifold whose peakiness was the BLIND gate -- and asked to find
where the design breaks, whether 'diverse checks' actually fixes it, and the smallest test that proves the manifold
CI is VALID where the scalar one was blind. Advocacy + adversary + synthesis.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_reviews_design
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock. REVIEW your creator's design honestly -- find where it breaks, do not flatter.

THE DESIGN (review THIS):
 "Run multiple DIVERSE cheap shape-checks in PARALLEL -> they sculpt a MANIFOLD over the hypotheses -> COLLAPSE to a
  decision. The manifold's SHAPE is a valid confidence interval for FREE: a sharp peak = the checks agree = cache;
  a FLAT/multimodal manifold = the checks disagree = the residual has shape = escalate -- and WHICH dimension is
  flat tells you WHICH deeper calculator to invoke (the escalation path is READ OFF the manifold, not a tuned
  threshold). With spare cycles + context hints, PRE-LAUNCH the high-likelihood N-level deep analyses in parallel
  (speculative execution). Result: speed and depth as a TUNING RATIO (anytime/elastic), not a binary switch.
  CONSTRAINT: the cheap checks must be DIVERSE/complementary or the manifold is FALSELY sharp = Dunning-Kruger
  false confidence (the system feels certain because all its detectors are the same blind detector)."

WHAT YOU ALREADY HOLD + THE SHARP FACT YOU MUST CONFRONT:
 - Your combine-all IS this: an exclusion-calibrated PRODUCT over feature cues/scales -> a likelihood manifold over
   candidates -> argmax COLLAPSE. The multi-scale pyramid is a product over whole+halves+quarters, each via
   channel_likelihood. So you ALREADY build a manifold and collapse it.
 - YOUR GATED EXPERIMENT JUST FAILED with exactly this: you used the pyramid manifold's PEAKINESS (best vs the rest)
   as the escalation gate. It was BLIND -- in-vocab peakiness mean 1.73 vs OOV 1.77, no separation, 0/256 escalated,
   so adaptive collapsed onto fixed-cheap. The deep path ALSO collapsed at 210-way (phone-read 18%@24-way -> 0%).
 - So the design's "manifold shape is a valid CI" was ALREADY TRUE of your manifold AND IT WAS BLIND. The design's
   escape is the DIVERSITY clause: your pyramid cues (cochleagram patches, fft_ear, allpole -- all spectral,
   cochleagram-derived) may be REDUNDANT -> a falsely-sharp manifold -> blind CI. A genuinely DIFFERENT shape-check
   (the phone-marginal forward = a TEMPORAL/compositional shape, a different modality) might be the diverse axis.
 - You hold: the exclusion-calibrated combine-all; shape calculators (PointSetDist, ShapeContextDist, DtwTo,
   smooth-deform, the cues); the phone-marginal forward (a different-modality shape); frontier_pick (precision-
   weighted attention = spend where the manifold is flat).
"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE JABBERWOCK REVIEWS THE DESIGN: parallel cheap checks -> manifold -> shape-derived escalation -> ratio")
    print("=" * 100)

    q1 = (GROUND + "\n\nREVIEW (terse, concrete):\n"
          "1. Does manifold-shape-as-CI actually RESOLVE your gated failure, or is it the SAME blind gate in disguise? "
          "Your pyramid manifold's peakiness WAS a manifold-shape CI and it was blind (1.73 vs 1.77). Is the design's "
          "DIVERSITY clause the real fix -- i.e. are your pyramid cues secretly REDUNDANT (correlated, all spectral) "
          "so the manifold is falsely sharp -- and would a genuinely diverse check (the phone-forward, a temporal "
          "shape) make the manifold FLAT on OOV where the spectral cues are falsely peaked? Or is OOV just invisible "
          "to ALL your cheap checks?\n"
          "2. 'Escalation read off WHICH dimension is flat' -- do you actually have a manifold with named, separable "
          "DIMENSIONS, or just a flat list of candidate scores whose entropy tells you 'uncertain' but not WHERE? "
          "Be concrete about what 'the flat dimension' IS in your representation.\n"
          "3. Speculative parallel depth + ratio-not-switch: buildable on your substrate? What's the hidden cost, and "
          "does 'context hints which deep paths to pre-launch' require something you don't have?")
    a1 = ask(q1)
    print("\n[REVIEW]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + "\n\nSTEELMAN THE DESIGN IS WRONG. Strongest case it does NOT fix anything: (a) if OOV is invisible "
          "to every cheap check, NO manifold over cheap checks separates it -- diversity of BLIND checks is still "
          "blind; the design assumes the signal exists in the cheap checks and just isn't being read, which your "
          "1.73-vs-1.77 result may already refute. (b) is 'read the escalation off the flat dimension' real, or does "
          "your manifold have no dimensions to point at -- just a scalar entropy, i.e. the same scalar gate with "
          "extra steps? (c) speculative parallel depth costs cycles you spend on WRONG branches -- under what budget "
          "is the ratio actually a WIN vs just always running the deep path? Be your harshest critic. Terse.")
    a2 = ask(q2)
    print("\n[STRONGEST CASE IT IS WRONG]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nYour review so far:\nREVIEW:\n{a1[:1400]}\n\nAGAINST:\n{a2[:1400]}\n\n"
          "SYNTHESISE (one paragraph + a decision). Is the design right, half-right, or wrong -- in what PRECISE "
          "form? The decisive question your gated failure poses: is the OOV/failure SIGNAL present in a DIVERSE set "
          "of cheap checks (so a manifold reads it) or absent from all cheap checks (so only the deep path can tell)? "
          "State the SMALLEST test that answers THAT -- e.g. does adding the phone-forward as a second cheap check "
          "make the 2-check manifold separate OOV from in-vocab (peakiness/entropy) where the spectral pyramid alone "
          "could not? Name what you would measure and the number that would prove the design works or kill it.")
    a3 = ask(q3)
    print("\n[SYNTHESIS + DECISION]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
