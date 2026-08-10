# ROBUST ORDER-N WITNESS — RESULTS: **CONFIRM on the witness (the FALSIFY is fixed); DEGRADE on the graph carve (the wall moved to sensing).**

The real-video FALSIFY (`PHYSICS_FALL_REAL_VIDEO_RESULTS.md`) was located precisely
at the WITNESS: order-N floored on the real falling ball because the perceived
second difference is *approximately* — never *exactly* — constant, and even an
ideal bright-blob perception oracle floored. This rung replaces the exact-equality
DECISION with a DESCRIPTION-LENGTH (MDL) one on the SAME finite-difference pyramid
("bins propose, continuous decides"). The result:

- **CONFIRM (the witness / the FALSIFY):** the cleanest real perceived free-fall
  trajectory — the bright-blob oracle whose second difference is the FALSIFY doc's
  own `[5,4,3,3,3,3,3,-13,9,6,3,-4]` — **now mints ORDER-2**, read from the graph
  (`LatentDimension{name:'latent:time', order:2, coeffs:((v0,0),(3,0))}`). The
  exact witness's floor is carried by the robust verdict. Physics from real
  perceived video, at the witness.
- **DEGRADE (the graph carve):** the block-SAD **graph-carve** windows (the
  trajectories actually read from the carve graph in the FALSIFY doc) STILL floor
  under the robust witness — SOUNDLY, because they are short / near-linear: their
  `d2` is jitter around ~0 with no curvature above the noise. **The wall moved from
  the WITNESS to SENSING** — the aperture–velocity tension (§133 of the FALSIFY
  doc) now dominates.
- **SOUND:** random / genuine-noise streams mint NOTHING under the robust witness
  (differencing amplifies their spread; no order compresses below raw). Proven on
  the graph-carve windows themselves and on multiple random streams.
- **ADDITIVE:** the exact witness runs FIRST and unchanged; the robust witness is
  OPT-IN (`TimeInfer.robust`) and runs only where the exact one already floored, so
  every synthetic/exact case is BYTE-IDENTICAL and every physics gate stays green.

Pre-registration `ROBUST_ORDER_N_WITNESS_PREREG.md`, committed **`c0120e7a69`**
BEFORE any number. Seed block **`SEED CLAIM 146000-146999: CLEAN -- no collision
DETECTED.`**

## Why OPT-IN — the frame/continuum invariant forced it (what I got wrong first)

My first implementation made the robust witness the DEFAULT (fire wherever the exact
one floored). It broke **4 physics gates** (`test_galileo_migrated` ×3,
`test_mass_by_action_migrated` ×1). The reason is the deepest finding of this rung,
and it is exactly CLAUDE.md's frame/continuum invariant:

- The mass-recovery / galileo pipeline reads the order-2 acceleration coefficient
  and inverts it to mass (`m = J/a`). It DEPENDS on a FRACTIONAL acceleration
  (`a = J/m` non-integer) FLOORING — because a non-integer generator is **not
  expressible in-frame** (in-frame is INTEGER; the continuum is CROSS-FRAME). The
  exact witness is RIGHT to refuse it.
- **A fractional acceleration and a real fall are the SAME signature** — a real
  fall's acceleration in grid units is ALSO fractional (that is *why* its `d2`
  jitters). Measured: `recover_mass(3, 5, ticks=7)` gives perceived cx
  `[2,4,7,12,19,27,37,49]` (`a = 5/3`); a default-tolerant witness minted order-2
  with the rounded integer `a=2` → wrong mass `2` (true `3`). A wrong in-frame
  generator, exactly what the exact witness must refuse.

So the exact and robust witnesses answer **two different questions**, and conflating
them is the bug:

- **EXACT (default)** — the IN-FRAME question: *"is there an INTEGER order-N
  generator carrying every pair by exact equality?"* Floors a fractional/continuous
  acceleration, correctly. What mass-recovery NEEDS. **Byte-identical.**
- **ROBUST (opt-in)** — the CROSS-FRAME question: *"is this the STEPPED observation
  of a continuous order-N parabola (constant to within its own dispersion)?"* For
  real perception. Mints order-2 with the robust (median) acceleration.

Opt-in is therefore not a dodge — it is the correct modeling of the invariant. A
continuous acceleration is carried intensionally (the robust mint is a cross-frame
detection), never mistaken for an in-frame integer generator.

## The witness — MDL on the same pyramid, tolerance falls out (`shape_decode.rs`)

Two-tier, additive by construction (`order_n_translate_verdict`):

1. The UNCHANGED exact witness (`diff_pyramid`/`pyramid_order`) runs first. Every
   exactly-constant `d^k` (synthetic, integer-Euler) mints the same order it always
   did (`emit_order_n`, factored out so the exact path is identical).
2. ONLY in the branch where the exact witness floored, and ONLY if the caller set
   `robust`, `robust_order` runs the MDL verdict:
   - Build the FULL pyramid (`full_pyramid`, no exact early-stop).
   - For each depth `m`, description length `DL(m)` = summed integer bit-cost
     (`ibits`) of {the `m` leading coefficients} + {the per-component MEDIAN
     constant of level `m`} + {the residuals of level `m` about that constant}. This
     is a lossless re-encoding (integrate `m` times to reconstruct), so the shortest
     is the best explanation — MDL.
   - Mint order `= argmin_m DL(m) + 1` iff it is `≥ 2`, STRICTLY beats the raw
     stream's `DL_null`, and the winning level has `≥ 3` samples of evidence.

**The tolerance FALLS OUT of the integer bit-costs — there is no threshold constant
in the code** (grep-clean; §13). A level constant to within small residuals encodes
cheaply and wins; a level whose spread rivals its magnitude (random, or differencing
that amplifies noise) encodes no cheaper than raw and LOSES → floor. Zero dispersion
⇒ zero residual cost ⇒ the MDL verdict agrees with exact equality (but the exact path
is taken first). The constant is the per-component **MEDIAN** — the outlier-robust
centre that ignores the ±glitch outliers real perception produces (a MEAN would be
dragged by them and break the witness).

Files: `runners/dsl/src/shape_decode.rs` (`ibits`/`vec_ibits`/`median_vec`/
`full_pyramid`/`robust_order`/`emit_order_n`, wired into
`order_n_translate_verdict`'s floor branch); the opt-in `robust: bool` field added to
the `TimeInfer` Term (`term.rs`/`jsonio.rs`/`reflect.rs`; serialized only when true,
so existing terms are byte-identical; NO new Term, NO new variant index).
`seeds/time_axis.json` v1.1.0: two ADDED rules `time_infer_mint_robust` /
`time_infer_floor_robust` gated on a distinct observation status
`motion_seq_robust` (the existing `motion_seq` rules are untouched → byte-identical);
they carry `robust:true` on every `TimeInfer`.

## The two absolute bars — PROVEN

### Bar 1 — ADDITIVE (exact/synthetic byte-identical)

- `test_generic_order_n_migrated` (8) + `test_time_infer_migrated` (6): const_vel →
  order-1 (exact tuple `('translate',(2,0),(),7,1)`), const_accel `[1,2,3,4,5,6]` →
  order-2, order-3 stream → order-3, random → floor — **all unchanged, 14 passed.**
- The default (exact) witness FLOORS the noisy parabola and the fractional-accel
  synthetic byte-identically (`explained=False, order=0`), so `recover_mass(3,5)`
  still returns `[]` — **the 4 physics gates I first broke are green again**
  (`galileo` + `mass_by_action` + `fall_from_eye` + `physics_derivation`: 44 passed
  with `generic_order_n`/`time_infer`).
- Full disturbed-surface swept per file, all green: dimension_inference,
  transform_decode, ink_decode, object_carve, quanta_navigation, engine_provenance,
  failure_baseline, rust_engine_parity (101 passed).

### Bar 2 — SOUND (random / noise mints NOTHING)

- Rust unit tests `order_n_generic_tests` (9): `robust_random_still_floors` (×4
  streams), `robust_noisy_parabola_is_order_2`, `robust_glitch_outlier_parabola_is_order_2`
  (median through glitches), `robust_tolerance_falls_out_no_magic_number`.
- The migrated gate `test_robust_witness_migrated` (7): random floors under BOTH
  witnesses (Term + run_rules `time_none`); several random streams all floor.
- **The graph-carve windows themselves floor** (below) — the strongest soundness
  evidence: real near-linear jitter is refused.

## The measured discriminator (products — TUPLES — and the graph mint)

### The real perceived trajectories (read from the graph, `results/physics_fall_real_video.json`)

| perceived `cy` (from the graph) | `d2` | exact | **robust order** |
|---|---|---|---|
| graph-carve `whole_fall` `[60,56,53,64]` (n=4) | `[1,14]` | floor | **floor** (too short) |
| graph-carve `mid_1fps` `[60,61,67,72,74,78,84,88,84]` | `[5,-1,-3,2,2,-2,-8]` | floor | **floor** (bounce-contaminated, high variance) |
| graph-carve `fast_2fps` `[173,175,178,180,184,186,190]` | `[1,-1,2,-2,2]` | floor | **floor** (near-linear; `d2` mean 0.4, no curvature above noise) |
| graph-carve `fast_2fps 48×240` `[134,135,136,140,143]` | `[0,3,-1]` | floor | **floor** (n=5, near-linear) |
| graph-carve `fastest_3fps` `[202,205,206,210,210,214]` | `[-2,3,-4,4]` | floor | **floor** (near-linear) |
| **bright-blob oracle N=14** (recon from `d2=[5,4,3,3,3,3,3,-13,9,6,3,-4]`) | five exact-3s + glitches | floor | **ORDER-2** ✅ |
| **bright-blob oracle N=16** (`d2=[3,3,4,1,3,1,4,1,-9,1,10,1,1,-1]`) | ~constant 1 + glitches | floor | **ORDER-2** ✅ |
| **bright-blob oracle N=18** (`d2=[1,5,1,1,3,1,3,0,3,-1,-12,11,2,-4,9,2]`) | ~constant 2 + glitches | floor | **ORDER-2** ✅ |

- **The graph carve (the real "read from the graph" trajectories) still floor** —
  this is the **DEGRADE**: the block-SAD windows are short/near-linear (aperture–
  velocity tension), and their `d2` genuinely has no curvature above the jitter. The
  robust witness SOUNDLY refuses them (it is not a "mint anything noisy" witness).
- **The bright-blob oracle — the cleanest real perception of the SAME fall — mints
  order-2**, read from the graph via `run_rules`:
  `('translate', 2, ((10,0),(3,0)), 14)` (order 2; velocity base `(10,0)`;
  acceleration `(3,0)` — the median through the ±13/±9 glitch outliers; window 14).
  The default `motion_seq` rule floors the same trajectory to `time_none`
  byte-identically. **This is the FALSIFY resolved at the witness: the uniform
  acceleration that was perceptibly present but not exactly constant is now
  witnessed.**

### The verdict on the two questions

The FALSIFY was "the exact witness floors the real (approximately-constant) parabola."
That is FIXED: given a perception clean enough to carry an above-noise curvature (the
oracle), the robust witness mints order-2. The remaining wall on the block-SAD graph
carve is NOT the witness — it is that the trackable windows are too short/low-curvature
(sensing / aperture), which the FALSIFY doc already named as the compounding second
wall and which now dominates.

## §13 — the tolerance falls out (no magic number)

`test_tolerance_falls_out_no_magic_number` + the Rust
`robust_tolerance_falls_out_no_magic_number`: with the SAME fixed noise pattern,
curvature ABOVE the noise (accel 4) → order-2; the SAME noise with NO curvature
(constant velocity) → floors. The crossover is set entirely by the data's own
description length. There is no numeric tolerance in `robust_order` to point at —
only the integer bit-cost `ibits` (a fixed universal code) and the median. Verified
by inspection of the source: no float, no threshold literal.

## Provenance / discipline

- Worktree branch **`gamma-substrate/robust-order-n-witness`** (NOT main); prereg
  **`c0120e7a69`** BEFORE any number.
- Engine sha256 **`eb36c8bf4e7b75ffe52bd324514fd6fa628d56255f47bc490bbcedf491281798`**,
  **`source_match = own`** (this tree's Rust; asserted from inside the process via
  `engine_preamble` / `provenance_stamp`). Rust unit tests linked libpython via
  `RUSTFLAGS="-L /usr/lib -C link-arg=-lpython3.14"`; the INSTALLED engine is the
  clean `cargo build --release` cdylib (hash above), rebuilt and re-hashed after the
  test run.
- **SEED CLAIM 146000-146999:** `CLEAN -- no collision DETECTED.` (no seed drawn by
  the witness — deterministic finite differences + median + integer bit-costs).
- **ORACLE** `scripts/rung7_vision_bench.sh` (data/ symlinked): **BEFORE 222 passed / 0 failed (174.59 s, baseline engine 1792a9ce)**;
  **AFTER 222 passed / 0 failed (180.63 s)**.
- Instrument seams (`test_engine_provenance_migrated` + `test_failure_baseline_migrated`)
  green; the 3 pre-existing reds are not mine.

## What I got WRONG (in full)

1. **I first made the robust witness the DEFAULT and broke 4 physics gates.** I had
   asserted (in the prereg's own additivity reasoning) that firing only in the floor
   branch was "purely additive." It is additive for streams that TRULY floored — but
   the mass-recovery gates deliberately feed FRACTIONAL-acceleration streams and rely
   on the floor to avoid emitting a wrong integer mass. The fix (opt-in) came from the
   frame/continuum invariant, and it is the stronger finding: exact and robust are two
   different questions (in-frame integer vs cross-frame stepped-continuous), and the
   real fall shares its signature with the fractional synthetic — so they CANNOT be
   the same default.
2. **My first "tolerance falls out" test was wrong.** I built a "high noise floors"
   case that actually still had a coherent +3 drift, so minting order-2 there was
   CORRECT, not over-acceptance. The real demonstration is curvature-present-vs-absent
   under the SAME noise. Corrected.
3. **I initially measured the oracle without the dim-typed ShapeSignature**, so
   `coord_dims` was empty and every trajectory floored for a trivial (wrong) reason. A
   read-back that isn't set up like the real path lies — I re-ran with the codebook the
   Term reads, matching the gate's boot.
4. **The graph carve does NOT mint — I must say so plainly.** The headline "physics
   from real video, end to end" holds only for the bright-blob oracle perception, not
   for the block-SAD carve trajectory that the pipeline actually reads from the graph.
   The witness is fixed; the sensing (aperture–velocity) wall is what now blocks the
   graph-carve path, and that is a DEGRADE, not a CONFIRM, on that specific path.

## Ledger row (this doc, not VISION_PROTOCOL.md)

| rung | claim | engine (own) | oracle before/after | verdict |
|---|---|---|---|---|
| robust-order-N-witness (block 146000-146999) | Replace the EXACT-equality order-N witness with an MDL/description-length verdict on the same finite-difference pyramid (tolerance falls out of integer bit-costs, robust MEDIAN constant), OPT-IN via `TimeInfer.robust` (frame/continuum invariant: exact = in-frame integer generator for mass recovery, byte-identical; robust = cross-frame stepped-continuous parabola for real perception). The cleanest real perceived free-fall (bright-blob oracle, the FALSIFY's own `d2`) now **mints ORDER-2** read from the graph (`latent:time`, coeffs `((v0,0),(3,0))`); RANDOM and the near-linear block-SAD graph-carve windows still FLOOR (sound); all exact/synthetic + physics/vision/discovery gates byte-identical. NO new Term, NO new variant. | `eb36c8bf…` (own) | 222 passed / 0 failed (174.59 s, baseline engine 1792a9ce) → 222 passed / 0 failed (180.63 s) | **CONFIRM (witness/FALSIFY fixed) + DEGRADE (graph carve → aperture/sensing wall)** |
