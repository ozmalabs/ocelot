# VISION — RUNG 5 PREREG: TWO EYES → SPATIAL (and TEMPORAL) SUPER-RESOLUTION by MULTI-LOOK DE-ALIASING

**Committed BEFORE any confirmatory number is read.** This file is committed
ALONE; the build, the kernel, the eyes, the measurement, and the gate follow in
later commits.

## Seed block — DRAWN AND VERIFIED CLEAN

Block **175000–175999** (measurement seeds `numpy.default_rng(175000 + arm)`).

```
$ python3 scripts/seed_claim.py 175000 175999
SEED CLAIM 175000-175999: CLEAN -- no collision DETECTED.
  Scope: 870 files with seed sinks; 589 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

`check_claim(175000, 175999)` returns `ok=True` with empty `declared_overlap`
(not 135000/136000/163000/164000/166000/170000; above the highest ledger block).

## The claim (falsifiable)

Two low-resolution photoreceptor eyes (`domains.photon_eye.GraphEye`), offset by
a KNOWN sub-receptor amount, viewing ONE flat TEXTURED surface (a periodic
luminance texture carrying a spatial harmonic ABOVE a single eye's
receptor-Nyquist), recover detail that NEITHER eye can represent alone. NOT
stereo/disparity (the surface is flat — no depth edges): **MULTI-LOOK
DE-ALIASING** (Tsai–Huang microscanning super-resolution). The two eyes' offset
samples interleave at sub-receptor lattice positions, carrying the PHASE that
de-aliases frequencies above either eye's Nyquist.

The FUSION is graph-native: a Rust `multilook_superres` CognitiveTask kernel
(band-limited least-squares reconstruction from samples at known nonuniform
positions; a small ridge damps directions the samples do not constrain — no new
DSL Term enum variant) + a `retinal_mint_superres` graph rule. Python is
mechanical I/O only: build TWO `GraphEye`s, feed each its offset view, tick, read
each eye's per-receptor activation, pack the fusion task, read the minted
`SuperResolvedField` back out.

### Reconstruction-error definitions (measured against the dense true field)

Let `err_single` = MSE of the single-eye reconstruction, `err_fused(δ)` = MSE of
the fused two-eye reconstruction at sub-receptor offset δ, `err_naive2x` = MSE of
a naive 2× reconstruction (single eye upsampled to 2× by linear interpolation —
double the samples, NO second real look), all against the densely-transduced
ground-truth field, all through the SAME fixed reconstruction operator (the only
independent variable is the SAMPLES / the offset).

### PRE-REGISTERED PASS CRITERIA (ALL must hold) — SPATIAL headline

1. **Fusion beats a single eye:** `err_single / err_fused(0.5) > 4`.
2. **Fusion beats naive 2× stacking:** `err_naive2x / err_fused(0.5) > 2`.
3. **THE FALSIFIER — zero-offset shows NO gain:**
   `err_single / err_fused(0.0) ∈ [0.8, 1.25]` (gain ≈ 0). Two IDENTICAL eyes
   (δ=0) → redundant samples → the offset, not the sensor count, is the cause.
4. **A target only the fused pair resolves:** the high harmonic k0 (with
   single-eye-Nyquist < k0 < fused-Nyquist) is reconstructed by the fused pair
   (offset 0.5) with per-fine-point RMS error below 20% of its amplitude, and by
   the single eye above 60% of its amplitude (aliased).

### PRE-REGISTERED PASS CRITERIA — TEMPORAL headline (space-offset ≡ time-offset)

The IDENTICAL Rust kernel, positions reinterpreted as TIMES. Two eyes on
INDEPENDENT async clocks (different tick phase — NO shared clock) sample a
time-varying stimulus at the UNION of their event times. With `t_err_*` the
temporal-reconstruction MSEs:

5. **Async union beats one clock:** `t_err_single / t_err_fused(0.5) > 4`.
6. **Zero temporal-offset (clocks in phase) → NO gain:**
   `t_err_single / t_err_fused(0.0) ∈ [0.8, 1.25]`.

## Controls / able-to-fail

- **Zero-offset (δ=0)** is the primary falsifier: if super-resolution were merely
  "more sensors", δ=0 would also gain. Criterion 3 forbids it.
- **Naive 2× stacking**: more pixels without a second real look; criterion 2
  forbids fusion winning trivially by pixel count.
- **Single-eye baseline** + the aliased high harmonic (criterion 4): a target the
  single eye provably cannot resolve.

## Discipline

- **Default OFF / byte-identity (§9):** the fusion kernel + `retinal_superres`
  seed + adapter are ADDITIVE and engaged only when a `SuperresParams` node is
  present (the world opts in). `GraphEye`'s rungs 1–4 / 166000 / 170000 paths are
  BYTE-UNCHANGED (no edit to any existing kernel, seed, or `GraphEye` build path).
- **Oracle:** `bash scripts/rung7_vision_bench.sh` → 0 failed, BEFORE == AFTER.
- **Provenance (§10):** the gate asserts `source_match in ("own","shared")`.
- **NO TIMING CLAIM.**
- **Gate:** `tests/test_two_eyes_migrated.py`.

## Honest scope (declared before measuring)

- The sub-receptor offset is KNOWN (a controlled displacement), not estimated
  from the images. Registration-from-data (the physics arc's proven
  `subcell_register`) is a separate, additional problem; here the offset is a
  given, isolating the de-aliasing win.
- The SPATIAL headline runs on the photon eye's native 1-D azimuth strip (the
  eye's documented foundation). The 2-D flat-wall case is the SAME kernel applied
  per elevation row (separable, azimuth-only offset) and is noted as a follow-on.
- The gain SATURATES and is bounded by photon quantization + the ridge floor; the
  claim is a large, sign-definite, control-separated gain, not infinite
  resolution.
