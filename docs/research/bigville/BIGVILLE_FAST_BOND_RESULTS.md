# RESULTS — Target-sensitive fast path (block 287000)

All five signatures reproduce. **`test_fast_bond_migrated.py` 5/5 + conduct/baseline
18/18 = 23/23 on canonical `fd82dc2978dbb055496dd82390ac2ebe`**. `runners/dsl` diff
EMPTY -- ZERO new Rust.

## Measured
Actor co-present with a Neutral (listed FIRST) and a Friend (affection 3), deciding
SHALLOW-ONLY (deepen disabled -> only the impulse decides):

| fast_gain | help@Neutral impulse | help@Friend impulse | chosen target |
|---|---|---|---|
| 0.1 | 0.70 | **1.00** | **Friend** |
| 0.0 (falsifier) | 0.70 | 0.70 | Neutral (first-tie failure) |

The cheap bond signal (nudge **+0.30** on the friend) makes the fast path prefer the
friend without any deliberation -- resolving the 282000-c finding on the shallow
pass. The nudge is SMALL vs the deep supergraph plan coupling (~1.5): the fast path
approximates, the deep path computes. Resentment repels the fast pull (a resented
target's help-impulse falls below base).

## What this closes
The 282000-c / 286000 residual: weak-bond targeting no longer needs a first
deliberation to internalize. The fast path now has TWO sources of bond-direction --
an INNATE cheap gut-pull (this block) and a LEARNED habit (286000 replay) -- and they
compose: the innate prior handles first encounters, internalization refines over
repetition. Neither substitutes for the other.

## Honest residuals
- The gut-pull is a fixed linear read (affection - resentment); richer fast-affect
  (trust/fear/gratitude) is a later refinement.
- Shallow-only harness isolates the fast path; in the full collapse the deep pass
  still refines/overrides on surprise (as designed).
