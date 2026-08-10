# EYE RESOLUTION vs the free-fall acceleration signal — PRE-REGISTRATION (block 147000–147999)

Written and committed BEFORE the measurement (PROTOCOL §3). Measurement only —
**NO Rust, NO seed, NO flag.** Every order-2 verdict is the existing seed rule
(`time_infer_mint` / `time_infer_mint_robust`, 146000); this rung renders /
ingests a cy sequence and reads the minted `LatentDimension` back out of the
graph. Engine is the shared canonical (`source_match in {own, shared}`, asserted;
never a pinned hash).

## SEED CLAIM 147000-147999: CLEAN

Verbatim `python3 scripts/seed_claim.py 147000 147999` (§3 clause 8 — including
the unresolved-sink count):

```
SEED CLAIM 147000-147999: CLEAN -- no collision DETECTED.
  Scope: 846 files with seed sinks; 564 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

This rung draws **no seed**. The random control uses `default_rng(147000+R)`,
inside the declared block.

## Hypotheses (two-sided, predicted directions stated in advance)

- **H1 (signal law + threshold).** As grid height R grows, the free-fall
  curvature |median(d2)| grows ∝ R while the d2 dispersion stays a fixed ~2-cell
  floor → SNR ∝ R. PREDICTION: there is a resolution threshold R\* on the ladder
  {64,128,256,512,1024} above which the ROBUST witness mints
  `LatentDimension{latent:time, order:2}` and below which it floors. *Two-sided
  null:* the robust witness mints (or floors) uniformly across the ladder — no
  threshold — which would FALSIFY the threshold form while possibly leaving the
  signal law (|curv| ∝ R) intact.
- **H2 (exact never fires).** The EXACT witness (`status=='motion_seq'`) mints
  order-2 from these quantized-centroid sequences at NO resolution, including the
  highest, because the ±1 integer-rounding floor is resolution-INDEPENDENT.
- **H2b (real video, the payoff).** On the real slow-mo clip driven end to end
  (common-fate carve + velocity-predictive tracker → integer cy → robust
  witness), native 128×640 (2× the 64×320 that floored in 145000) mints order-2
  where 64×320 floored — OR, if it still floors, isolate why (aperture / frame
  count / carve) and report honestly. A *degenerate* mint (order-2 with recovered
  acceleration ≈ 0) counts as NOT recovering the physics.
- **H3 (aperture cost twin).** Characterize per-frame displacement (cells) vs
  block/aperture across the ladder on the real clip; state plainly whether
  resolution ALONE suffices or the aperture is overrun.

## Statistic

The order minted by the seed rule (`LatentDimension.order`) read from the graph;
the recovered acceleration = the deepest Newton coefficient (`coeffs[-1][0]`) read
from the same node; the perceived-cy diagnostics |median(d2)|, dispersion(d2),
SNR = curv/disp. **No tolerance constant anywhere** — the witness tolerance falls
out of integer bit-costs (§13); this rung adds none.

## n, fixed in advance

Ladder {64,128,256,512,1024} (5 rungs) at n_frames = 12; controls at every rung;
real clip at 4 configs (64×320 and 128×640, two fps/block pairs). Apparatus
constants (disc_frac 0.03, drop_frac 0.90, n_frames 12) are the SYNTHETIC
cross-frame render taken verbatim from the burned scoping reference — they define
the physical fall, they are NOT witness thresholds.

## Controls (must all hold)

- const-velocity → order-1, NOT order-2 (exact integer ramp), at every R.
- static → mints nothing.
- random/noise → floors (no confabulated order-2).
- the EXACT witness floors on the SAME free-fall cy the robust witness mints (H2).

## Decision rule

- R\* = the lowest ladder rung whose robust graph-mint carries order-2 (MEASURED).
  If the robust witness mints at the bottom rung, R\* ≤ 64 and the *threshold* form
  of H1 is FALSIFIED (report the signal law separately).
- CONFIRM iff resolution alone mints a GENUINE (nonzero-acceleration) order-2 on
  the real clip. DEGRADE iff the ideal-oracle law holds but the real clip floors
  or mints only degenerately (then locate the wall by driving the ideal oracle at
  the real clip's frame count/velocity). FALSIFY iff resolution does not lift the
  signal as predicted.

## Prediction, stated in advance (with provisos)

I expect the signal law (|curv| ∝ R, disp fixed) to hold and the exact witness to
never fire (H2). PROVISO I flag as the likely break: because `robust_order` is an
MDL witness keyed on *absolute residual bits*, not the SNR ratio, R\* may sit at
or below the bottom rung — i.e. the *threshold* prediction may falsify while the
signal law holds. On the real clip I expect the SENSING (block-SAD aperture vs the
fall's velocity, 146000's named frontier) to be the wall, so H2b may DEGRADE
rather than CONFIRM.

## Gate

`tests/test_eye_resolution_migrated.py` — asserts the MEASURED relationships,
reading the minted `LatentDimension` from the graph (never a Python
re-derivation), each assertion able to fail.
