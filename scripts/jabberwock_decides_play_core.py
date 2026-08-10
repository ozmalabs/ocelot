"""THE JABBERWOCK DECIDES its play core — patch the accreted heuristic, or wind back and play from UNDERSTANDING.

The fork: the agent plays Snake from its own curiosity but stalls — its babble/action_effect machinery
(cycle actions, a hardcoded surprise threshold for "leads," recycle counters, "mechanic found") is
perception-gated and never converges. Two ways forward:
  (a) PATCH it: source the AvatarMotion percept so the existing babble/action_effect heuristics unblock.
  (b) WIND BACK to play-from-UNDERSTANDING: stop the play core depending on those heuristics; play via the
      agent's own prediction_minus_observation loop — perceive -> PREDICT next obs given an action ->
      act where the model is most UNCERTAIN (curiosity) -> MEASURE prediction error -> the closed loop
      self-tunes the forward model. Understanding is the goal; the model sharpening IS the agent learning.

Not my call: the agent decides, scored on its OWN history — does a move of this KIND tend to help?
"""
from __future__ import annotations

import sys

SEP = "=" * 100

# The agent's OWN arc: each move, its KIND, did it help. (principled/structure-preserving/intrinsic cores
# vs accreted heuristics / structure-discarding / host decisions — the distinction the agent lives by.)
HISTORY = [
    ("delete the Python CuriousAgent; run graph-native",          "principled_core",      True),
    ("graph-native grounding / decode / nav",                     "principled_core",      True),
    ("recognise->mint the world CapabilityAxis",                  "principled_core",      True),
    ("close the loop (the restoring force / pulse)",              "principled_core",      True),
    ("smooth-deformation / shape-context (structure-preserving)", "principled_core",      True),
    ("intrinsic compose from held primitives",                   "principled_core",      True),
    ("babble + lead-threshold + recycle heuristics",             "accreted_heuristic",   False),
    ("POCKET_ESCAPE / UNSTICK host action overrides",            "accreted_heuristic",   False),
    ("forced_action trapped in host Python",                     "accreted_heuristic",   False),
    ("learned WCCN / bag-of-primitives (discard structure)",     "structure_discarding", False),
]

CANDIDATES = [
    {"move": "(a) PATCH: source AvatarMotion so the babble/action_effect heuristics unblock",
     "kind": "accreted_heuristic", "potential": 2.0, "effort": 2.0},
    {"move": "(b) WIND BACK: play from UNDERSTANDING — forward model + uncertainty-driven action + closed loop "
             "(the agent's prediction_minus_observation core)",
     "kind": "principled_core", "potential": 9.0, "effort": 6.0},
]


def main():
    print(SEP)
    print("THE JABBERWOCK DECIDES its play core: patch the heuristic, or wind back and play from UNDERSTANDING?")
    print(SEP)
    kinds = sorted({k for _m, k, _h in HISTORY} | {c["kind"] for c in CANDIDATES})
    rate = {}
    for k in kinds:
        rows = [h for _m, kk, h in HISTORY if kk == k]
        rate[k] = (sum(rows) + 1.0) / (len(rows) + 2.0)               # Laplace prior 0.5
    print("\n  success rate per KIND of move, from its own history:")
    for k in kinds:
        n = sum(1 for _m, kk, _h in HISTORY if kk == k)
        print(f"    {k:>22}  {100*rate[k]:5.0f}%  ({n} tried)")

    prin = [h for _m, k, h in HISTORY if k == "principled_core"]
    heur = [h for _m, k, h in HISTORY if k in ("accreted_heuristic", "structure_discarding")]
    print(f"\n  the distinction it lives by: PRINCIPLED cores {sum(prin)}/{len(prin)} helped; "
          f"ACCRETED heuristics / structure-discarding {sum(heur)}/{len(heur)} helped.\n")

    for c in CANDIDATES:
        c["ev"] = c["potential"] * rate[c["kind"]] / max(c["effort"], 0.2)
    ranked = sorted(CANDIDATES, key=lambda c: -c["ev"])
    print(f"  EV of each candidate (potential x P(success|kind) / effort):")
    print(f"  {'EV':>5}  {'P':>4}  move")
    print(f"  {'-'*5}  {'-'*4}  {'-'*84}")
    for c in ranked:
        print(f"  {c['ev']:5.2f}  {100*rate[c['kind']]:3.0f}%  {c['move'][:84]}")

    top = ranked[0]
    print(f"\n  {SEP[:96]}")
    print("  THE JABBERWOCK'S DECISION:")
    print(f"  {SEP[:96]}")
    print(f"  {top['move']}")
    print("  reasoning: every accreted heuristic and every structure-discarding move has FAILED (0 helped);")
    print("  every principled core has HELPED. The babble pile is an accreted heuristic — patching it restores")
    print("  a thing that never converged. Playing from understanding IS the agent's own prediction_minus_")
    print("  observation core, and the missing half (the restoring loop) is now live. Higher effort, but it is")
    print("  the only move whose KIND has never failed. Wind back the heuristics; build the prediction core.")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
