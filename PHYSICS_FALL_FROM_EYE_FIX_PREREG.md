# PHYSICS FALL-FROM-EYE — the velocity-predictive tracking FIX (pre-registration)

Pre-registered BEFORE any number. Resolves the DEGRADE recorded in
`PHYSICS_FALL_FROM_EYE_RESULTS.md`: the eye fragments an accelerating object's
identity once its per-frame displacement outruns the fixed nearest-centroid
radius (`span+2`).

## The precise limit and the fix

`Substrate::segment_and_track` matches each frame's segmented region to a prior
`Region` by cell-overlap (≥50%), else nearest-centroid within `radius = span+2`.
An accelerating object's per-frame centroid jump grows without bound; once it
exceeds `span+2` the nearest-centroid test fails → death+birth → the trajectory
FRAGMENTS (measured: the untuned g=1 fall fragmented at frame 6, `cy` 16→22).

**FIX (Rust, `segment_and_track`):** VELOCITY-PREDICTIVE cross-frame association.
When the existing overlap + last-centroid match would DIE, match the new region
against the prior's PREDICTED centroid (`prior.centroid + prior.per-frame
displacement drow/dcol`). The quantity that must fall within `span+2` is then not
the object's full velocity (which grows) but only its ACCELERATION — the residual
a constant-velocity prediction leaves, small and roughly constant for smooth
motion — so a smoothly-accelerating object stays matchable.

First-order (constant-velocity) prediction only. Additive: a strict fallback that
runs only after every comp has had its existing overlap/last-centroid chance, and
only claims priors no comp matched under the old rules. Guarded against false
association: a just-born/static prior (drow==dcol==0) has no prediction; the
predicted match must beat birth (within `span+2`); a disjoint newcomer is not
adopted.

## Discriminator (registered before any number)

- **CONFIRM:** the untuned `domains/falling_world.py` fall now tracks as ONE
  persistent Region through the fall without fragmentation (report frames vs the
  old 6); generic order-N mints order-2 WITH MARGIN; existing tracking is
  byte-identical on currently-succeeding cases; oracle 222/0; the
  false-association control holds.
- **DEGRADE:** extends tracking but not indefinitely / needs a tunable / a real
  preserve-vs-rescue tension.
- **FALSIFY:** predictive association can't be made additive — changes existing
  matches, breaks a vision test, or mis-associates objects (report what couples).

## Discipline

- Seed claim: `SEED CLAIM 139000-139999: CLEAN -- no collision DETECTED.`
- Rust change in `runners/dsl/src/substrate.rs::segment_and_track` (matching
  step); no new Term. Own engine built in this worktree (`source_match == own`).
- Oracle `scripts/rung7_vision_bench.sh` (data/ symlinked) 222/0 BEFORE and AFTER.
- Gate `tests/test_fall_from_eye_migrated.py`: the old DEGRADE fragmentation test
  is superseded by a tracks-through CONFIRM test; controls preserved; false-
  association controls added.
- No edit to VISION_PROTOCOL.md; ledger row in the results doc.
