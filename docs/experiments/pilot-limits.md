# Pilot limits and the retirement of the 48→28 compression number

Phase 0 of the Mary's Room empirical paper plan. This note records, before any
confirmatory work, exactly what the v2 red/green pilot
(`marys-room-red-green-results.md`, `results/marys_room_red_green.json`) does and
does not establish, and formally **retires** its headline compression number so
it is not carried into the paper as evidence.

## What the pilot legitimately shows (keep)

- **Research-only identification** of the fixed 610/530 nm pair: 2/2, from the
  sign of `L−M` on CIE 2006 fundamentals. A genuine but tiny (2-item) result.
- **Eye identification** after exposure: all 24 columns labelled correctly.
- **Research↔eye direction match**: cosine 0.9988 (610 nm) / 0.9973 (530 nm),
  angular error 2.86° / 4.19°. This is the one quantitatively interesting
  number and it is **earned**, not definitional: the eye reaches it through
  Gaussian capture (centres 564/534/420 nm ≠ CIE) + Naka-Rushton saturation
  before the shared `L−M` opponent formula (see `docs/research/eye-mechanism-table.md`).
  The residual is the footprint of those two documented sources.

## What is retired (do not cite as evidence)

**The `48→28` ("1.714×", "41.7%") compression result is retired.** It is an
artefact of the cost formula applied to duplicated inputs, not an empirical
finding:

1. **It is arithmetic, not measurement.** The declared cost is `raw = N·d` vs
   `coded = k·d + N`, with `N=24`, `d=2`. For `k=2` categories this is
   `48 → 28` by construction. *Any* 24-sample, 2-cluster, 2-D field yields
   exactly this, regardless of the data.
2. **The inputs are duplicates.** `results/marys_room_red_green.json` reports
   `eye_unique_opponent_vectors: 1` for each colour: all 12 columns of a colour
   return an identical vector (the pipeline is deterministic — no RNG in the
   colour path). The "compression" is therefore of 24 copies of two values.
3. **It measures nothing about representation.** `k` is read from the minted
   codebook; with two separable clusters the minter always returns 2. There is
   no held-out set, no distortion axis, and no baseline to beat.

The number is **not upgradable** in place and is not a weaker version of the
real result. It is replaced wholesale by Arm C
(`docs/research/` rate–distortion plan): a train/held-out split, held-out
description length, and matched-code-budget baselines (raw, fixed opponent basis,
PCA, vector quantisation), reported as rate–distortion curves. If the compact
code does not beat raw at matched distortion, that is reported as a negative
result.

## Other pilot limits (scope, not errors)

- **RQ1 is untested by the pilot.** Two stimuli cannot distinguish a decoder
  from a coin flip. RQ1 ("theory-only identification above chance") is evidenced
  only by the Phase 3 broad set (`marys-room-broad-prereg.md`), never by the
  pilot.
- **One illumination/exposure regime, monochromatic only.** No broadband
  colours, no illuminants, no metamers, no pre-receptoral optics. The embodied
  "closed eyelid" condition is absent. All added in Phase 2/3.
- **Determinism ⇒ no trial variance.** The 12 columns per colour are identical
  by construction. Error intervals in the confirmatory study come from the
  stimulus / illuminant / observer-perturbation manifold, not from repeats.
- **The "direction score" (0–100) is demoted.** `100·(1+cos)/2` compresses the
  informative range (cos 0.997–0.999 → 99.87–99.94). Angular error in degrees is
  the primary direction metric going forward; the 0–100 score is dropped.

## Status

- Pilot runs and raw JSON are retained in the repository as feasibility
  evidence and provenance, unchanged.
- No confirmatory claim, title, or abstract may cite the `48→28` number, the
  2-item RQ1 accuracy, or the 0–100 direction score as a primary result.
- The pilot's earned angular-match result may be cited only as pilot-level
  motivation, with the shared-formula / independent-inputs distinction stated.
