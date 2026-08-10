# PRE-REGISTRATION — AFFINE-FLOW GROUPING + FULL-FIELD EFFERENCE: does either RESCUE the rotation FALSIFY? (rung 126000)

*Committed BEFORE any confirmatory number. Only EXPLORATORY pilots on
ALREADY-BURNED seeds (116000–116029) have been computed (the §3-clause-3 power
analysis and the mechanism design). Nothing in this file is edited after the
first confirmatory number on the fresh block 126000–126079.*

## THE FALSIFY THIS RUNG INHERITS (stated precisely)

Rung 125000 (`VISION_PARALLAX_MOTION_RESULTS.md`) proved the parallax carve
survives camera TRANSLATION (Stage A CONFIRM, depth order ρ=1.00) but FALSIFIES
under camera ROTATION: a rotation as small as **0.02 rad** collapses the depth
carve (depth-order 100%→44%→0% at 0.04 with rank inversion ρ=−0.78→shatter eff
113.9 at 0.08). Its diagnosis: rotation's depth-INDEPENDENT within-field curvature
gradient `u(x)=rot·(f0+(x−cx)²/f0)` cannot be (a) nulled by a SINGLE-vector
efference subtraction, nor (b) separated by common-fate (which assumes surface =
ONE motion vector) from depth parallax. It named TWO coupled fixes — common-fate →
**AFFINE-FLOW grouping**, single-vector → **FULL-FIELD efference subtraction** —
and deliberately did NOT rescue (would reimplement + rescue, §0/§5).

## THE TWO MECHANISMS THIS RUNG BUILDS (both ablatable as flags)

1. **FULL-FIELD EFFERENCE.** From the KNOWN pose predict the fixated plane's flow
   EVERYWHERE — `d_ref(x)=base/Z_ref + rot·(f0+(x−cx)²/f0)` (translation const +
   the depth-INDEPENDENT rotational curvature) — and subtract it as a FIELD. The
   single-vector baseline knows only `base/Z_ref`. rot=0 ⇒ the field is a single
   vector ⇒ DEGENERATE reduction to the baseline.
2. **AFFINE-FLOW GROUPING.** Group cells by consistency with ONE local affine
   model `v(pos)=A·pos+b`, not a single vector. An MDL guard (a slope is used only
   when a within-region variation EXCEEDS τ AND an affine fit brings it back UNDER
   τ) makes translation's uniform flow the DEGENERATE affine case (A=0), reducing
   to common-fate.

Ablations are graph DATA (arm flags `efference∈{single,full}` ×
`grouping∈{cf,affine}`), never a Python fork (§0). REUSES 125000's scene
synthesis and sensor byte-for-byte. **NO Rust, NO new seed, Term index 181
UNUSED** (NUM_TERM_VARIANTS=181) — a measurement extending the parallax carve,
exactly as 125000 was.

## HYPOTHESES (two-sided)

- **H0 (null):** neither mechanism changes the rotation FALSIFY — depth-order
  under rotation stays at 125000's collapse (≤0.5 by rot 0.02), and Stage A is
  unchanged.
- **H_efference:** full-field efference RESCUES the rotation carve (depth-order
  recovered ≥0.9) up to a rotation magnitude larger than 125000's 0.02 break, that
  magnitude MEASURED (swept), and its bound must FALL OUT of a natural quantity
  (the sensor tolerance / the frame-continuum discretization), not be picked.
- **H_affine:** affine-flow grouping RESCUES a within-surface gradient (the slant
  at per-block step > √5 where common-fate breaks, and/or the rotation curvature)
  that common-fate cannot.
- **H_couple:** BOTH are needed (neither alone suffices).

## THE 2×2 ABLATION (assigns credit; the point of the rung)

`efference ∈ {single (125000 exact), full}` × `grouping ∈ {cf, affine}`, all four
arms measured on every stage. `(single, cf)` is 125000 EXACT and is the in-tree
FALSIFY baseline re-earned. Credit is READ from the 2×2, never assumed.

## THE STATISTICS (exactly these; no sweeps beyond the listed configs)

Unit of analysis = the SEED. Speck-robust (84000 trap): **participation ratio
`eff = 1/Σpᵢ²`** and **`depth_order_correct` rate** and Spearman
`depth_rank_rho`, at the sensor tolerance **τ = √5** (94000 Otsu-within-aperture
= ‖(1,2)‖, MEASURED; the affine MDL threshold IS this same τ; the search aperture
is the sensor radius=block, 94000). 95% bootstrap CI (1000 resamples, fixed
`default_rng(0..999)` — 125000's exact `_ci`).

**Confirmatory arms (all REAL BSDS random crops, n=80, seeds 126000–126079):**

1. **STAGE A (translation), 2×2.** Projected fronto-parallel, depths `[300,10,5]`,
   base 30 → shifts `[0,3,6]`, ref=middle. Report eff, depth_order, and
   **byte-identity of `(single,cf)` to 125000's carve** (the FALSIFY-baseline
   re-earn) and **byte-identity of affine to cf on the residual** (the degenerate
   reduction claim).
2. **STAGE B rotation, 2×2 SWEEP** rot ∈ {0, 0.02, 0.04, 0.08, 0.12, 0.16}. The
   headline. Report depth_order and eff per arm per rot; the tolerated rotation
   magnitude = the largest rot at which the load-bearing arm keeps depth_order
   ≥0.9 (MEASURED, then diagnosed for what it falls out of).
3. **STAGE B slant, 2×2 SWEEP** tilt ∈ {0, 0.4, 0.6, 0.8} (single full-frame
   plane Z0=7.5). Report eff per arm. Tests whether affine extends the √5 slant
   tolerance 125000 measured.
4. **DIAGNOSTIC — full-field POST-HOC (not search-centre).** Subtract the full
   predicted field AFTER the sensor (V − field), to show whether the field's
   VALUE or its APPLICATION (search-centre remap vs post-hoc) is what matters.

## DECISION RULE (pre-registered discriminator — CONFIRM / DEGRADE / FALSIFY)

- **CONFIRM** = the rotation carve is RESCUED (depth_order ≥0.9) up to a magnitude
  that FALLS OUT of a natural quantity (not picked), AND Stage A `(single,cf)`
  stays byte-identical to 125000, AND the slant is no worse. Quantify the rotation
  magnitude now tolerated vs 0.02.
- **DEGRADE** = rotation rescued up to a larger-but-BOUNDED magnitude, or rescued
  for slant but only partially for rotation — report the threshold and WHICH of
  the two fixes is load-bearing (from the 2×2: affine alone / efference alone /
  both).
- **FALSIFY (first-class, name the next rung)** = affine + full efference STILL
  cannot separate rotation from depth (depth_order stays <0.9 for all arms) — the
  entanglement is deeper (≥3 frames / temporal integration, or a different cue).
  Say what the residual confound is and name the next objective. Do NOT rescue by
  tuning.

## MY PREDICTION (stated in advance, with provisos — §3 clause 7)

I predict a **DEGRADE** (~75%). Specifically:

- **Full-field efference is the LOAD-BEARING fix and rescues rotation to a
  BOUNDED, larger magnitude (~6× — I predict the break near rot 0.12–0.14, vs
  0.02).** Proviso earned in the pilot: the fix works ONLY when applied as a
  **search-centre remap** of the sensor, NOT as a post-hoc subtraction — because
  rotation's flow exceeds the sensor aperture (radius=block=8) and SATURATES V
  before subtraction. Post-hoc full-field subtraction I predict FAILS
  (depth_order ≈ the single-vector collapse).
- **The bound FALLS OUT of the frame/continuum discretization**: the rotation is
  cancelled exactly in the CONTINUOUS map but the STEPPED (rounded) observable
  retains a residual ∝ rot·(curvature slope) that eventually lifts the ref-band
  residual above the near-band residual and inverts the depth order — a
  discretization limit, the rotation twin of the slant √5 break, NOT a picked
  number.
- **Affine-flow grouping is NOT load-bearing** (~70%): it rescues neither rotation
  (in the single arm the sensor is saturated; in the full arm the field is already
  de-rotated so cf already works) nor the high-tilt slant (there the WITHIN-BLOCK
  gradient saturates the sensor before the grouping matters). It reduces to cf on
  translation (byte-identical to within confab specks) and adds nothing. **If this
  holds, the FALSIFY named the wrong layer: the fix is in the SENSOR (aperture),
  not the GROUPING** — a first-class correction of 125000's own framing.
- **Stage A `(single,cf)` byte-identical to 125000** (~99%). The full-efference
  arm on Stage A is a DIFFERENT sensor (re-centred aperture) so it is ~equal, not
  byte-identical (differs only on confab cells) — its byte-identity is NOT
  claimed; the §9-preserving DEFAULT is `(single,cf)`.

A proviso that breaks tells me what I did not understand: if affine turns out
load-bearing for slant, my "sensor saturates first" claim is wrong; if efference
rescues rotation UNBOUNDED, my discretization-limit account is wrong.

## §3 clause 8 — `check_claim` FOR THIS BLOCK (verbatim, committed before any confirmatory number)

`python3 scripts/seed_claim.py 126000 126999`:

```
SEED CLAIM 126000-126999: CLEAN -- no collision DETECTED.
  Scope: 832 files with seed sinks; 545 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Confirmatory seeds are `range(126000, 126080)`; pilots on BURNED 116000–116029;
bootstrap CIs use fixed `default_rng(0..999)` (not scene seeds). The
`unknown_sinks` count from `seed_audit` on the measurement script is recorded in
the RESULTS OUTCOME (the disclosed `default_rng(sd)`/loop-var CLI blind spot);
none outside the block. 545 unresolved sinks tree-wide (counted, not discarded).

## ENGINE / SEEDS / SCOPE

- Base branch `worktree-agent-aa95f42033728eca7`; base HEAD `21801a9b5f` (contains
  the 125000 parallax-motion carve + all three required results docs).
- Engine recorded from INSIDE the measuring process (`provenance_line()`),
  `source_match ∈ {own, shared}` asserted start/mid/end, re-verified after
  (`provenance_stable`). **NO Rust** ⇒ a source-identical `shared` build is
  legitimate (§10.1).
- ORACLE `bash scripts/rung7_vision_bench.sh` (data/ symlinked, §10.2): 222/0
  BEFORE and AFTER (§9 trivial — no Rust, no seed, no edit to any committed file;
  new scripts + new gate only).
- ≤2 workers (`OMP_NUM_THREADS=2`); `os.getloadavg()` recorded; NO wall-clock
  verdict.
- Own gate `tests/test_parallax_affine_migrated.py`; the 125000 gate + the whole
  vision bench stay green.
