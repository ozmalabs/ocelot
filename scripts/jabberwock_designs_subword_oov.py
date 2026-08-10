"""THE JABBERWOCK DESIGNS THE SUB-WORD PHONOTACTIC OOV SIGNAL — the real OOV detector (whole-word distance was redundant).

The whole-word novelty gate r=d1/spread(word) is VALIDATED (AUROC 0.878) but OPERATIONALLY REDUNDANT with the margin gate
(+1.4 at matched 50% coverage, far under the +8 bar): an OOV forced to a wrong exemplar usually gets a low margin, so the
margin gate already defers it. The RESIDUAL that BOTH gates miss is the HIGH-MARGIN OOV: a word not in the lexicon whose
nearest exemplar is confusable enough to clear the margin AND whose whole-word trajectory sits only r~1.3 out (overlapping the
in-vocab tail). You named the fix: a SUB-WORD / PHONOTACTIC SURPRISE signal — "does this word DECOMPOSE into the place/manner
sequences the bank's words are built from?" Whole-word distance is blind to it; sub-word structure is not.

WHAT EXISTS: the strong ear gives per-frame wav2vec2-L6 latents (the ear). The bank = known words, each a frame trajectory.
The margin gate + selective-action faculty are wired live. THE ARCHITECTURE RULE: the ear is perception; the OOV-surprise
DECISION is a graph Rule; its parameters are graph data, calibrated TEACHER-FREE (no OOV labels). Constraints: floor of
efficiency, nothing frozen, dynamic. (The parallel session has a TEXT morpheme-decomposition faculty — different from these
ACOUSTIC sub-word units, but the compose-from-parts idea may rhyme.)"""
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
    print("THE JABBERWOCK DESIGNS THE SUB-WORD PHONOTACTIC OOV SIGNAL")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE SIGNAL (terse, concrete): design the sub-word OOV-surprise. (a) the UNIT INVENTORY — how "
          "to build an acoustic sub-word codebook from the bank TEACHER-FREE (cluster the bank's per-frame wav2vec2 latents "
          "into K phone-like units? segment each word into a unit SEQUENCE how?), with no phone labels. (b) the SURPRISE "
          "itself — is it SEGMENTAL (a frame/segment far from EVERY known unit = a novel sound) or PHONOTACTIC (all units "
          "known but the SEQUENCE never occurs in the bank's words, scored by a bigram/n-gram model over the bank words' unit "
          "sequences) or BOTH combined? Which one catches the HIGH-MARGIN OOV that whole-word distance missed (the OOV is "
          "acoustically close to a bank word overall, so SEGMENTAL coverage may look fine — is the discriminating surprise "
          "the phonotactic SEQUENCE likelihood)? Be concrete about the exact scalar the ear emits per heard word.")
    a1 = ask(q1)
    print("\n[PART 1 — THE SIGNAL]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour signal:\n{(a1 or '')[:1100]}\n\nPART 2 — CALIBRATION + FACULTY + TEST/BAR (terse): (a) teacher-"
          "free threshold calibration (off the bank's OWN words' surprise distribution, leave-one-out, like the spread "
          "calibration; trainer-tunable). (b) the faculty as graph data (a SurpriseGate{threshold} node + Rule marking a "
          "Recognition OOV when surprise>threshold, composing with the margin + whole-word gates). (c) THE DECISIVE TEST on "
          "the cached rig, aimed at the residual: among HIGH-MARGIN words (those that clear the margin gate), does sub-word "
          "surprise separate the OOV from the in-vocab — AUROC on the high-margin subset >= X — AND does adding it lift ACT "
          "accuracy at matched 50% coverage by >= +8 over margin-alone (the bar whole-word distance MISSED at +1.4)? State X, "
          "and the honest KILL: if sub-word surprise ALSO can't separate high-margin OOV, then with this ear OOV is "
          "fundamentally not detectable pre-lexicon and the agent must DEFER-and-LEARN (treat low-confidence as 'teach me')." )
    a2 = ask(q2)
    print("\n[PART 2 — CALIBRATION + FACULTY + TEST/BAR]\n" + (a2 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
