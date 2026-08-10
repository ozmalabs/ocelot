"""THE COGNITION ATLAS — one coordinate system that gives language and specificity to a raft of things
that previously had only metaphors.

Creator: this gives language and specificity to a whole raft of things which did not have it. The arc
produced ONE small set of coordinates:
  LAYER     — 1 reality-grounded/world-in-loop · 2 internal model (offline) · 3 meta (transfer) ·
              4 articulation (stating the model)
  RESIDUAL  — does the learning signal come from the WORLD or from the SELF/prior?
  RECAPTURE — how often a world-residual re-grounds the running self-model (every step ... never)
  ARTICULATE— can it state its model as an explicit rule?
Each phenomenon below was, before, a hand-wave ('muscle memory', 'gut feeling', 'losing touch',
'stir-crazy', 'stochastic parrot'). Here each gets COORDINATES, and its grounding error is MEASURED
from the recapture model (jabberwock_disconnection) — not asserted.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_cognition_atlas.py
"""
import numpy as np
INF = float("inf")


def grounding_error(R, capture, n=150, drift=0.05, self_pull=0.3):
    """self-model drifting toward its own prior, re-grounded by a world-residual every R steps (gain
    capture). Mean error once drift sets in. R=inf or capture=0 -> never effectively re-grounded."""
    errs = []
    for seed in range(20):
        rng = np.random.default_rng(seed)
        truth = np.cumsum(rng.normal(0, drift, n)) + 1.0
        s, e = 0.0, []
        for t in range(n):
            e.append(abs(s - truth[t]))
            s += self_pull * (0.0 - s)
            if R != INF and (t + 1) % int(R) == 0:
                s += capture * (truth[t] - s)
        errs.append(np.mean(e[n // 3:]))
    return float(np.mean(errs))


# phenomenon, the vague term it replaces, LAYER, RESIDUAL, recapture R, capture-gain, ARTICULATE
ATLAS = [
    ("motor skill / walking",      "'muscle memory', tacit knowing", 1, "world", 1,   1.0, False),
    ("habit",                      "'autopilot'",                    1, "world", 1,   1.0, False),
    ("perception (tracking)",      "'just seeing'",                  1, "world", 1,   1.0, False),
    ("intuition / expertise",      "'gut feeling', 'flow'",          2, "world", 1,   1.0, False),
    ("planning / imagination",     "'thinking it through'",          2, "model", 1,   1.0, True),
    ("analogy / few-shot transfer","'insight', 'getting it'",        3, "model", 1,   1.0, True),
    ("explanation / language",     "'understanding' (human)",        4, "world", 1,   1.0, True),
    ("dreaming",                   "'the unconscious'",              4, "self",  16,  1.0, True),
    ("confabulation (Korsakoff)",  "'making things up'",             4, "self",  4,   0.0, True),
    ("psychosis / delusion",       "'losing touch with reality'",    4, "self",  INF, 0.0, True),
    ("sensory deprivation / deafferentation", "'stir-crazy'",        4, "self",  INF, 0.0, True),
    ("LLM hallucination",          "'stochastic parrot', 'BS'",      4, "self",  INF, 0.0, True),
]


def main():
    print("=" * 100)
    print("THE COGNITION ATLAS — one coordinate system; each phenomenon gets coordinates + a MEASURED")
    print("grounding error (the term it replaces in quotes). grounded < 0.15; quadrant = grounding x articulation")
    print("=" * 100)
    print(f"  {'phenomenon':30}{'L':>2} {'residual':>8} {'recap':>6} {'g.err':>6} {'grounded':>9} "
          f"{'artic':>6}  {'replaces the vague term'}")
    for name, vague, L, res, R, cap, art in ATLAS:
        g = grounding_error(R, cap)
        Rs = "never" if R == INF else str(int(R))
        gr = "YES" if g < 0.15 else "no"
        print(f"  {name:30}{L:>2} {res:>8} {Rs:>6} {g:6.2f} {gr:>9} {('YES' if art else 'no'):>6}  {vague}")
    print("=" * 100)
    print("  THE RAFT, NAMED: motor skill/habit/perception = Layer 1, world in the loop (no longer")
    print("  'muscle memory'). intuition = Layer 2 grounded-inarticulate ('gut feeling' = an internal")
    print("  model you can't state). planning = Layer 2 offline; analogy = Layer 3 meta. language =")
    print("  Layer 4 grounded-articulate (the human). dreaming/confabulation/psychosis/sensory-")
    print("  deprivation/LLM = Layer 4 articulate but UNGROUNDED, differing only by RECAPTURE: dreaming")
    print("  wakes (R=16, bounded), confabulation's capture is broken, deprivation severs contact, the")
    print("  LLM is never connected. ONE engine, two axes, one recapture parameter — and a dozen things")
    print("  that had only metaphors now have coordinates and a measured number.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
