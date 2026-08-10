# ROBUST ORDER-N WITNESS — PRE-REGISTRATION

**Registered BEFORE any measurement number is reported.**
Seed block: `SEED CLAIM 146000-146999: CLEAN -- no collision DETECTED.`
Branch: `gamma-substrate/robust-order-n-witness` (NOT main).

## The wall this fixes (from PHYSICS_FALL_REAL_VIDEO_RESULTS.md)

On a REAL falling ball the generic order-N loop FLOORS to `time_none`: the
perceived second difference is *approximately* constant (a run of exact 3s plus
±1–2 glitch cells) but the witness (`diff_pyramid`/`pyramid_order`) requires it
to be EXACTLY constant. Even an ideal bright-blob perception oracle floors — so
the wall is the WITNESS, not the carve. The synthetic `[1,2,4,7,11,16]` mints
only because integer-Euler physics gives an exactly-constant difference.

## The fix (registered)

Replace the exact-equality DECISION with a DESCRIPTION-LENGTH (MDL) decision on
the SAME finite-difference pyramid (the proposal is unchanged — "bins propose,
continuous decides"). Order-k is witnessed iff modeling difference-level k as a
single robust constant (per-component MEDIAN) + its residual has a STRICTLY
LOWER description length (summed integer bit-cost `ibits`) than the raw stream —
i.e. order-k genuinely COMPRESSES the trajectory given the noise. The tolerance
FALLS OUT of the integer bit-costs; there is NO picked threshold constant.

Two-tier, additive by construction: the UNCHANGED exact witness runs first
(every synthetic/integer case takes it byte-identically); the robust witness
runs ONLY in the branch where the exact witness already floored.

File: `runners/dsl/src/shape_decode.rs` — `ibits`/`vec_ibits`/`median_vec`/
`full_pyramid`/`robust_order`, wired into `order_n_translate_verdict`'s floor
branch; the emit is factored into `emit_order_n` so the exact path is identical.
No new Term, no new variant index. Likely NO seed change.

## The discriminator (fixed here, before numbers)

- **CONFIRM:** the real perceived falling-ball trajectory now mints **order-2**;
  the exact synthetic cases are byte-unchanged (order-1/2/3 as before, gates
  green); random/noise still FLOORS; the tolerance fell out (no magic number);
  oracle `rung7_vision_bench.sh` 222/0 before AND after.
- **DEGRADE:** the witness accepts the real parabola AND keeps noise out, but the
  real GRAPH-CARVE runs are too short / low-curvature (the aperture–velocity
  wall) to mint reliably — quantify, and the wall moves to sensing.
- **FALSIFY (report honestly):** real-structure-with-noise cannot be separated
  from genuine-noise without a hand-set threshold; OR making it tolerant
  over-accepts (random mints); OR it cannot be made additive (the exact/synthetic
  results move). Name exactly what blocks it. NEVER ship a witness that mints on
  noise.

## The two absolute correctness bars (must both hold)

1. **ADDITIVE:** exactly-constant d^k (dispersion 0) still mints the SAME order;
   `test_generic_order_n_migrated` exact cases byte-identical; physics/vision/
   discovery migrated suites GREEN; oracle 222/0 before and after.
2. **SOUND:** a RANDOM stream mints NOTHING; a genuinely non-order-k stream is
   not falsely minted. Proven with multiple random streams + the
   noise-swamps-curvature crossover.

## Verification plan

- Rust unit tests in `order_n_generic_tests` (noisy parabola order-2, glitch
  outliers via median, random floors ×4, tolerance falls out).
- New gate `tests/test_robust_witness_migrated.py` (noisy-parabola mints order-2
  via the Term + run_rules; random floors; exact cases unchanged; tolerance
  falls out).
- `test_generic_order_n_migrated`, `test_time_infer_migrated`,
  `test_dimension_inference_migrated`, `test_transform_decode_migrated`,
  `test_ink_decode_migrated`, `test_fall_from_eye_migrated`,
  `test_object_carve_migrated`, `test_quanta_navigation_migrated`,
  instrument-seam migrated set — per file.
- Re-run the recorded REAL perceived trajectories (`results/
  physics_fall_real_video.json` graph-carve `cy_int`, and the bright-blob oracle
  d2 from the results doc) through the new Term; report order/coeffs read from
  the product (TUPLES) and, where minted, the graph `LatentDimension`.
- Engine: `own` build of this tree's Rust; sha256 recorded; oracle 222/0.
