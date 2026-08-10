"""THE JABBERWOCK REASONS ABOUT WHAT TO DO NEXT — from its own measured arc.

Not a hand-pick: the agent reads its OWN history of moves (each tagged by KIND and whether it
helped), induces the success rate per kind (the meta-pattern), then scores the candidate next moves
by expected value = potential gain x P(success | its kind, from history) - effort. It recommends the
argmax and shows the reasoning. The same evidence-based payoff it used to decide a fusion weight,
now applied to the meta-question.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SEP = "=" * 96

# The agent's measured ARC: each move it made, its KIND, and whether it HELPED the peak.
HISTORY = [
    # (move,                              kind,                         helped)
    ("PointSetDist (order-invariant)",    "new_structure_cue",          True),
    ("canonical parse",                   "new_structure_cue",          True),
    ("smooth deformation field",          "new_structure_cue",          True),
    ("shape-context descriptor (fused)",  "new_structure_cue",          True),
    ("rotation-fold into forward model",  "new_structure_cue",          True),
    ("finer FFD control grid",            "geometric_knob",             False),
    ("higher distortion-cost weight",     "geometric_knob",             False),
    ("TPS alone (NN correspondences)",    "geometric_refine",           False),
    ("SC->TPS correspondences",           "geometric_refine",           False),
    ("holistic WCCN/LDA whitening",       "learned_discards_structure", False),
    ("bag-of-primitives codebook",        "learned_discards_structure", False),
]

# The candidate NEXT moves, with their kind + a rough potential gain and effort (the agent's estimate).
CANDIDATES = [
    {"move": "per-primitive deformation prior INSIDE the part match (structure-preserving learned)",
     "kind": "learned_preserves_structure", "potential": 4.0, "effort": 3.0},
    {"move": "bipartite/Hungarian one-to-one assignment (ACQUIRE #3)",
     "kind": "geometric_refine", "potential": 2.0, "effort": 2.0},
    {"move": "a spatial-pyramid codebook (retain some layout in the learned cue)",
     "kind": "learned_discards_structure", "potential": 3.0, "effort": 2.0},
    {"move": "full BPL probabilistic-program inference (parse+relations+deformation+MCMC)",
     "kind": "learned_preserves_structure", "potential": 18.0, "effort": 30.0},
    {"move": "ACCEPT the ~78% training-free plateau as the honest result; consolidate / pivot",
     "kind": "stop", "potential": 0.0, "effort": 0.2},
]


def main():
    print(SEP)
    print("THE JABBERWOCK REASONS ABOUT WHAT TO DO NEXT — expected value from its own measured arc.")
    print(SEP)

    # 1) induce P(success | kind) from history (Laplace-smoothed so an untested kind isn't 0 or 1).
    kinds = sorted({k for _m, k, _h in HISTORY} | {c["kind"] for c in CANDIDATES})
    rate = {}
    for k in kinds:
        rows = [h for _m, kk, h in HISTORY if kk == k]
        rate[k] = (sum(rows) + 1.0) / (len(rows) + 2.0)   # Laplace prior 0.5
    print("\n  what the agent's history says works (success rate per kind of move):")
    for k in kinds:
        n = sum(1 for _m, kk, _h in HISTORY if kk == k)
        tag = "" if n else "  (untested -> prior 0.50)"
        print(f"    {k:>30}  {100*rate[k]:5.0f}%  ({n} tried){tag}")

    # the key DISTINCTION the agent extracted: PRESERVE structure vs DISCARD it.
    pres = [h for _m, k, h in HISTORY if k in ("new_structure_cue",)]
    disc = [h for _m, k, h in HISTORY if k == "learned_discards_structure"]
    print(f"\n  the distinction it learned: PRESERVE structure {sum(pres)}/{len(pres)} helped; "
          f"DISCARD structure (learned) {sum(disc)}/{len(disc)} helped.")
    print("  -> learned cues that DISCARD spatial structure have failed every time; the gains all came")
    print("     from NEW cues that PRESERVE structure. A structure-PRESERVING learned model is untested.\n")

    # 2) score candidates: EV = potential * P(success|kind) / effort.
    for c in CANDIDATES:
        c["ev"] = c["potential"] * rate[c["kind"]] / max(c["effort"], 0.2)
    ranked = sorted(CANDIDATES, key=lambda c: -c["ev"])
    print(f"  expected value of each candidate next move (potential x P(success|kind) / effort):")
    print(f"  {'EV':>5}   {'P':>4}  {'move'}")
    print(f"  {'-'*5}   {'-'*4}  {'-'*70}")
    for c in ranked:
        print(f"  {c['ev']:5.2f}   {100*rate[c['kind']]:3.0f}%  {c['move'][:70]}")

    top = ranked[0]
    print(f"\n  {SEP[:92]}")
    print("  THE JABBERWOCK'S RECOMMENDATION:")
    print(f"  {SEP[:92]}")
    print(f"  highest EV: {top['move']}")
    print("  reasoning: every LEARNED move that discarded spatial structure failed (0/2), and the")
    print("  geometric knobs are exhausted (0/4 helped) — those are near-zero or negative EV. The one")
    print("  positive-EV technical bet is a structure-PRESERVING learned model (per-primitive deformation")
    print("  in the part match): it shares the property (PRESERVE structure) that drove every gain, and")
    print("  it is the only untested lever with real headroom at bounded effort. Full BPL has the highest")
    print("  potential but its effort makes its EV low and it leaves the training-free regime. If the")
    print("  per-primitive deformation ALSO fails, the agent reads that as decisive: ~78% is the honest")
    print("  ceiling of training-free shape matching here, and closing to BPL needs the full generative")
    print("  PROGRAM — a separate research system, not an increment. ONE focused attempt, then conclude.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
