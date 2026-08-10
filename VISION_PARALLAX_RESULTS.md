# PARALLAX FROM KNOWN SELF-MOTION — RESULTS: **CONFIRM. A KNOWN SELF-SHIFT CARVES A DEPTH-STRUCTURED SCENE INTO ITS SURFACES (FEW + LARGE) WHERE A BYTE-IDENTICAL STATIC FRAME CANNOT; A FLAT CONTROL YIELDS ONE BLOB. SPACE CONSTANCY IS EXACT (ZERO RESIDUAL ON THE FIXATED PLANE). GRAPH-RESIDENT AS A SEED (`parallax_efference`, default OFF); NO RUST, INDEX 180 UNUSED.**

*Pre-registration `VISION_PARALLAX_PREREG.md`, committed **`b2cc1ccaca`** BEFORE
any confirmatory number (only the pilot on burned seeds 116900+ had been
computed). Nothing in it was edited after the first confirmatory number. This
rung reports its pre-registered **CONFIRM** and builds the graph-resident
realization as a **SEED** — the DSL expresses the mechanism (vector subtraction
is `VecSub`, already native), so **Term enum index 180 is UNUSED**; `git diff`
adds one seed + its registration + one migrated test, no Rust.*

**ENGINE PROVENANCE (§10).** Printed from **inside** the measuring process into
`results/parallax.json`, asserted `== EXPECT_ENGINE` at start / pre-graph / end,
and re-verified after the measurement:

```
engine e039d2eec2dd @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so  [1 other tree build(s) shadowed]
```

`provenance_stable` (provenance == provenance_after): **True** (asserted in the
artifact). Branch **`worktree-agent-a9bf6e3235f3eefd3`** — the name I actually
see. Base SHA **`d0445352a0`** (contains index 179 `MotionEnergy` and the three
required results docs — verified before starting). Engine built in-tree by
`scripts/engine_build.sh` (**`own`**, hash `e039d2eec2dd`, byte-identical to the
motion-energy / phasefield / closure rungs — same Rust source); **THIS RUNG ADDS
NO RUST.** Migrated provenance gate run as **its own step, first: 7 passed**, and
re-verified after the measurement: **7 passed**.

> **THE §11 HAZARD THE CLOSURE RUNG HIT, CAUGHT EARLY (recorded first):** my
> first orienting `cd` landed in the SHARED checkout
> (`/home/matt/ozma/internal/research/experiments/gamma-substrate`), not my
> isolated worktree (`.claude/worktrees/agent-a9bf6e3235f3eefd3/...`). I caught
> it from `git rev-parse --show-toplevel` on the FIRST command, moved ALL work
> into the worktree, symlinked `data/` (§10.2, not a copy), and built + measured
> only there. Nothing was written to the shared tree.

**LOAD (recorded with every measurement).** `os.getloadavg()` in the artifact:
start `[0.34, 0.50, 0.59]`, end `[1.00, 1.05, 1.07]`; wall **1629.8 s**
(dominated by the graph-runtime arm's 120 boot+settle cycles, which ran
concurrently with the migrated test). **At most 2 workers; no wall-clock
quantity is a verdict — every statistic is a bootstrap over the 80 seeds or an
exact/counted quantity.**

**FLOORS asserted in-run:** the efference-copy subtraction is **exact to the
pixel** — the fixated plane's ground-truth residual `max|R| = 0.0` EXACTLY
(space constancy); the depth bands are **INVISIBLE in the byte-identical static
frame** (column gradient at band boundaries **15.35** ≈ within-band **16.36**),
so only the motion can carve them.

---

## 1. THE HEADLINE

**Does a KNOWN self-generated shift Δ (efference copy), subtracted and grouped by
common fate, carve a depth-structured scene into surfaces (FEW + LARGE) where a
BYTE-IDENTICAL static frame cannot — while a FLAT control does not carve? YES.
CONFIRM.**

Primary arm (GRID=144, block=8, N=3 depth planes, parallax shifts `[0,3,6]`,
fixation = middle plane; 324-cell field, 3 bands of 108 cells; n=80 fresh
confirmatory seeds 116000–116079, unit = SEED, 95% bootstrap CI), grouping the
**sensed** residual field (real SAD `vector_field`) by common fate:

| statistic | DEPTH | FLAT | discriminator |
|---|---|---|---|
| **eff_surfaces** `1/Σpᵢ²` (τ=0) | **3.12 [3.11, 3.13]** | **1.00 [1.00, 1.00]** | CI-separated ✓ |
| **eff_surfaces** (τ=√5) | **3.11 [3.10, 3.12]** | **1.00 [1.00, 1.00]** | CI-separated ✓ |
| **largest_frac** (τ=0) | **0.358 [0.357, 0.360]** | **1.000 [1.000, 1.000]** | CI-separated ✓ |
| **largest_frac** (τ=√5) | **0.361 [0.359, 0.362]** | **1.000** | CI-separated ✓ |
| **top-5 size fractions** (τ=0) | **[0.359, 0.333, 0.284, 0.003, 0.003]** | **[1.0, 0, 0, 0, 0]** | 3 surfaces vs 1 blob |
| field discontinuity (ground truth) | **3.0** (a real boundary to segment on) | **0.00** (null EXPOSED) | — |
| space constancy: ref residual (GT) | **0.0 EXACTLY** | (whole frame is the reference) | — |

**Three measured facts, each pre-registered, put this in CONFIRM (all at BOTH
τ):**

1. **DEPTH carves into ≈ N=3 surfaces.** `eff_surfaces` (the participation
   ratio, robust to the sensor's confabulation-speck tail) is **3.12** — three
   large surfaces of ≈ 1/3 the frame each (top-5 fractions 0.359 / 0.333 /
   0.284), plus a negligible tail (≤ 0.003). Few-but-plural, exactly the number
   of depth planes.
2. **DEPTH's largest surface is NOT most of the frame** (0.358), while **FLAT is
   ONE blob** (`eff_surfaces` 1.00, `largest_frac` 1.000). The giant ground the
   closure rung could never break on a static frame is broken here by parallax.
3. **The FLAT null is EXPOSED, not vacuous:** the FLAT residual field's
   discontinuity is **0.00** (a uniform shift carries no boundary), while the
   DEPTH residual field carries a **3.0-pixel** discontinuity at each depth
   boundary. FLAT stays one blob because there is genuinely nothing to segment —
   not because the operator failed.

**⇒ PRE-REGISTERED VERDICT: CONFIRM.** DEPTH and FLAT are CI-separated on both
statistics at both τ; the DEPTH knee (few + large) co-holds with the FLAT null.
**And this is the closure rung's terminus made active:** a single static frame
cannot carve itself into few-and-large (seven per-frame relations failed) — but
a KNOWN self-shift over a scene with depth carves it into its surfaces, because
**objecthood lives in temporal coherence and the eye supplies the coherence by
moving itself.**

---

## 2. THE BYTE-IDENTICAL STATIC FRAME IS THE WHOLE RIGOR — and it holds

The DEPTH and FLAT conditions share ONE periodic texture `a` (one array). Because
all N bands are the SAME texture, **the depth planes leave NO trace in the static
frame**: the column gradient AT the band boundaries (**15.35**) is
indistinguishable from the within-band gradient (**16.36**). A static carver
(value flood, phase congruency, MDL closure — the seven the closure rung ran) has
literally nothing to key on at a depth boundary, and whatever it carves it carves
**identically** in DEPTH and FLAT. **Only the post-shift frame differs** (DEPTH:
each band by its own parallax shift; FLAT: the whole frame by one shift — verified
to differ in exactly the 96/144 non-reference columns). So the entire DEPTH-vs-FLAT
difference is **parallax vs uniform motion**, nothing else. This is the control
that makes it a test and not "motion helps".

---

## 3. THE EFFERENCE COPY IS THE KNOWN Δ — space constancy is EXACT

The subtracted reference field is built from the shift I **chose** (`Δ_ref`), never
estimated from pixels. `R = V − Δ_ref` is exact integer arithmetic (the SAD sensor
emits integer offsets; `Δ_ref` is an integer shift). Two pre-registered
consequences, both measured:

- **Space constancy / "the shift is not perceived":** the fixated (reference)
  plane's residual is **0.0 EXACTLY** on the ground-truth field, and on the
  **FLAT** world armed on its own uniform motion the graph mints **0 objects on
  all 20 seeds** — the whole world reads STATIONARY despite the retinal shift.
  This is the ungrounded fixed point: the tracked plane is the reference (zero
  residual), everything else is grounded relative to it by its parallax.
- **The residual field IS depth-relative-to-reference:** segmenting the residual
  segments by depth (the DEPTH residual's 3.0-pixel discontinuities sit exactly
  at the depth boundaries).

**Honesty (§8, declared in the prereg):** the efference-copy subtraction is
TRANSLATION-INVARIANT for the PARTITION — subtracting a constant does not change
which cells are equal — so it does **not** "cause" the carve (common fate on the
raw field already carves DEPTH and not FLAT). Its load-bearing roles are (a) space
constancy (zero residual on the fixated plane) and (b) choosing WHICH plane is the
reference. Both are real and measured; neither is the segmentation itself.

---

## 4. THE GRAPH-RESIDENT REALIZATION — a SEED, not a Rust Term (§0)

The mechanism is graph-native already: `vision_motion_group`'s common-fate flood
(the 84000 rung) carves by neighbour velocity DIFFERENCE. The genuinely-new,
load-bearing piece is the **reference frame**: `mo_dominant` ESTIMATES it as the
largest group's velocity; the efference copy is the eye's KNOWN self-motion,
supplied, never estimated. The DSL expresses this (`VecSub` is native), so
**index 180 is UNUSED** and the build is one seed:

**`seeds/parallax_efference.json`** (v1.0.0, depends on `vision_motion_group`),
ONE rule `pe_efference_ref`: when armed (`MotionParams.mo_efference > 0.5`) it
writes `field.dom_v = field.efference_v` and `dom_done = 1` EARLY, which
**suppresses `mo_dominant` via its OWN `dom_done < 0.5` guard** (no edit to the
84000 seed) so the UNCHANGED `mo_mint` refuses the CHOSEN fixation plane. Pre-
registered checks, all measured on the confirmatory seeds:

| check | result | reads |
|---|---|---|
| **default OFF byte-identical** (loaded+disarmed == not loaded) | **True on all 20 seeds** | §9 — committed behaviour unchanged |
| **armed is LOAD-BEARING** (`D = armed ≠ disarmed`) | **1 on all 20 seeds** | §13.2 / §1's fifth clause — it MOVES the minted set |
| the reference becomes the CHOSEN Δ | `armed_dom = (0,3)` vs estimated `baseline_dom = (0,6)` | the eye fixates the plane it chose, not the largest |
| the fixated plane is REFUSED | `(0,3)` never among minted surfaces; near `(0,6)` + far `(0,0)` minted | space constancy in the graph |
| **FLAT armed mints 0 objects** | **{0} on all 20 seeds** | the flat world reads stationary |
| `assert_settled` unsettled pairs | **0** everywhere | genuine fixpoint, not a partial flood |

`test_parallax_efference_migrated.py` — **7 passed**, positive-controlled BOTH
ways: `test_armed_is_load_bearing_and_refuses_the_chosen_fixation` (the mechanism
moves the set) is guarded by `test_dead_control_arming_on_the_estimated_dominant_does_NOT_move`
(arming on the SAME vector the field would estimate reproduces the baseline — so
the load-bearing test bites on the CHOICE of reference, not merely on the seed
being loaded), and `test_default_off_is_byte_identical` (a seed that changed
disarmed behaviour would fail).

---

## 5. THE SIZE DISTRIBUTION IN BOTH CONDITIONS, ALL ARMS (the headline of every arm)

| arm (τ) | DEPTH eff_surfaces | DEPTH largest_frac | DEPTH top-5 fractions | FLAT eff / largest | verdict |
|---|---|---|---|---|---|
| **primary N=3 block8** (τ=0) | 3.12 [3.11,3.13] | 0.358 [0.357,0.360] | [.359,.333,.284,.003,.003] | 1.00 / 1.000 | **CONFIRM** |
| **primary N=3 block8** (τ=√5) | 3.11 [3.10,3.12] | 0.361 [0.359,0.362] | [.361,.333,.284,.004,.003] | 1.00 / 1.000 | **CONFIRM** |
| secondary N=2 block8 (both τ) | 2.00 [2.00,2.00] | 0.500 | [.500,.500,.0002,0,0] | 1.00 / 1.000 | **CONFIRM** (2 surfaces) |
| **inherited-bound N=3 block4** (τ=0) | 3.34 [3.34,3.34] | 0.333 | [.333,.333,.278,.004,.003] | 1.01 / 0.994 | carves, but… |
| **inherited-bound N=3 block4** (τ=√5) | **1.08 [1.07,1.08]** | **0.963 [0.962,0.965]** | [.963,.007,.005,.004,.003] | 1.01 / 0.995 | **FALSIFY — bands MERGE** |

**The inherited-bound arm FALSIFIES as predicted, and the falsification IS the
finding.** Block 4's aperture (= 4) cannot hold three depths separated enough to
survive the sensor's accuracy tolerance: at τ=√5 the three bands (residual gaps
of only 2 < √5) MERGE into one blob (`largest_frac` 0.963), and at τ=0 the sensor's
confabulation inflates the count. The verdict FLIPS between the two derived τ ⇒ no
§13-clean operating point at block 4 for N=3. **The bound that falls out: the
number of resolvable depth planes ≤ aperture / tolerance ≈ block / √5** (block 4 →
1.8 → 2 planes; block 8 → 3.6 → 3 planes). This is derived entirely from the
sensor's own measured aperture (= `block`, `vector_field`) and accuracy tolerance
(√5, rung 94000) — not chosen. **N=2 is robustly confirmable across apertures;
N=3 needs aperture ≥ ~6.** Reported in full, not cherry-picked: block 8 CONFIRMS,
block 4 FALSIFIES, and the bound explains both.

---

## 6. THE INHERITED BOUNDS, STATED (this line has two named traps)

- **The grouping is only as good as the motion field (84000 over-grouped 23× on a
  bad signal).** Measured here: even at block 8 the sensor confabulates up to
  **14 px** on a seam/aperture-corner cell (`sensor_err_max = 14`), and the raw
  count is confab-inflated (10–11 groups where 3 are real). **The participation
  ratio absorbs this exactly** — the confab specks have `pᵢ² → 0` weight, so
  `eff_surfaces` reads the 3 real surfaces (3.12), NOT the 11 raw groups. The raw
  median is therefore NOT reported as the discriminator (it is 1 at τ=0, corrupted
  by the speck tail — the same statistic that burned 84000). This is why the
  pre-registered statistics are the participation ratio and `largest_frac`, both
  speck-robust.
- **The sensor CONFABULATES rather than abstains past its aperture.** The reference
  band's SENSED residual reaches 3 px (a confabulated cell), while the GROUND-TRUTH
  residual is exactly 0 — so space constancy is EXACT in principle and bounded by
  the sensor's confabulation in practice. This is the correct, honest reading of
  the sensor-gate rung's bound applied to this rung.
- **A null needs exposure.** The FLAT one-blob result is NOT vacuous: the FLAT
  residual field's discontinuity is measured at **0.00** (no boundary exists to
  segment on), while the DEPTH field carries a real **3.0-px** discontinuity. The
  null is a genuine absence of structure, proven.

---

## 7. §13 — WHERE THE NUMBERS CAME FROM (and the manufacturing knob, named)

- **The tolerance τ FALLS OUT, two readings, both enumerated, verdict holds at
  BOTH:** exact τ=0 (integer vector equality, NO NUMBER AT ALL) and τ=√5 ≈ 2.2361
  (the motion-sensor-gate rung's MEASURED Otsu-within-aperture accuracy tolerance,
  the norm of the integer (1,2)). The primary CONFIRM and the FLAT null are
  identical at both.
- **THE MANUFACTURING KNOB, NAMED (the closure rung's §13 trap was a compute cap;
  mine is different):** it is NOT τ — it is the sensor's **APERTURE (`block`) and
  the depth SHIFTS `s_i`**, which are STIMULUS/SENSOR CONFIGURATION (the same
  standing as motion-energy's `DOT`/`FIELD_W` and the closure rung's ring radius),
  NOT verdict thresholds. The shifts are the INDEPENDENT VARIABLE (the depth
  structure imposed) and are reported across the block-4/block-8 comparison so the
  aperture bound is exhibited, not tuned around. **No measured quantity is compared
  against a chosen number to decide the verdict** — the discriminators are a
  participation ratio and a fraction, and the boundary threshold is the derived τ.
- **The seed introduces NO new constant** (`test_seed_has_no_tuned_threshold`
  passes): its only literals are flag guards (`> 0.5`, the same standing as
  `vision_motion_group`'s own flag guards) and the −1/0/1 sentinels; the agreement
  tolerance is reused from `vision_motion_group`'s field-derived value.
- **Seed audit:** `check_claim(116000,116999)` post-run (verbatim, §3 clause 8):

  ```
  SEED CLAIM 116000-116999: REFUSED.
    OCCUPIED: 81 seed integer(s) in this range are measurably drawn by 3 file(s).
      116000: scripts/parallax_measure.py, tests/test_parallax_efference_migrated.py
      116001: scripts/parallax_measure.py, tests/test_parallax_efference_migrated.py
      116002: scripts/parallax_measure.py, tests/test_parallax_efference_migrated.py
      116003: scripts/parallax_measure.py
      ... and 61 more
    Scope: 822 files with seed sinks; 511 UNRESOLVED sink sites tree-wide (counted, not discarded).
  ```

  (The REFUSAL is my OWN in-block seeds — confirmatory 116000–116079 + pilot
  116900 — the expected post-run state; none outside the block. The prereg-time
  check was CLEAN save the pilot 116900, verbatim in the prereg. `unknown_sinks`
  for my scripts: the confirmatory seeds are `default_rng(116000+i)`, all
  in-block.) **`unknown_sinks: 0` for the confirmatory arm; 511 unresolved sinks
  tree-wide (counted, not discarded).**

---

## 8. WHICH REGISTERED OUTCOME OCCURRED

| criterion (§5 of prereg — CONFIRM, all co-holding at BOTH τ) | measured | met? |
|---|---|---|
| DEPTH eff_surfaces ∈ [2.5, 3.5] (≈N) | 3.11–3.12 | ✓ |
| DEPTH largest_frac < 0.5 | 0.358–0.361 | ✓ |
| FLAT eff_surfaces ∈ [0.9,1.2] AND largest_frac > 0.9 | 1.00 / 1.000 | ✓ |
| DEPTH-vs-FLAT CI-separated on both | yes, at both τ | ✓ |
| FLAT field discontinuity = 0 (null exposed) | 0.00 | ✓ |
| space constancy: reference residual = 0 (GT) | 0.0 exactly | ✓ |
| default-OFF byte-identical; armed load-bearing; FLAT armed 0 | all True | ✓ |

Clean **CONFIRM** on the primary and secondary arms; the block-4 N=3 arm is the
pre-registered aperture-bound **FALSIFY**. My prediction (§6 of prereg, ~85%
CONFIRM primary, block-4 FALSIFY, space constancy exact, seed load-bearing) held
in every particular.

---

## 9. WHAT I GOT WRONG — in full

1. **THE RAW MEDIAN AND COUNT ARE CONFAB-CORRUPTED — I nearly used them.** My
   first pilot read the raw median (1.0) and raw count (11) and would have
   reported a mess (median-1 looks like a FALSIFY; count-11 looks like
   over-segmentation). The 84000 rung's own trap ("median 2, a random pair beats
   a real one") is the sensor's confabulation-speck tail, and it corrupts any raw
   size statistic here. I switched — in the pilot, before the prereg — to the
   participation ratio (`1/Σpᵢ²`) and `largest_frac`, which are speck-robust, and
   pre-registered THOSE. The raw median/count are reported (§5, `results/parallax.json`)
   but explicitly NOT the discriminator. Had I pre-registered raw median I would
   have mis-read a clean CONFIRM.
2. **I ORIENTED IN THE SHARED CHECKOUT ON MY FIRST COMMAND** (the exact closure-rung
   §11 hazard). Caught immediately by `git rev-parse --show-toplevel` returning the
   shared root; moved all work into the isolated worktree before building or
   measuring. Nothing touched the shared tree. Disclosed, not elided.
3. **THE SENSED SPACE-CONSTANCY IS NOT EXACT (only the ground-truth is).** I
   registered "reference residual EXACTLY 0" — true on the constructed field, but
   the SENSED reference band reaches 3 px on a confabulated cell. I state both:
   exact in principle (the efference copy is known), bounded by the sensor's
   confabulation in practice. Not a failure — the honest reading of the inherited
   sensor bound.
4. **THE EFFERENCE-COPY SUBTRACTION DOES NOT CAUSE THE CARVE, and I had to be
   careful not to imply it does.** The partition is translation-invariant; common
   fate on the raw field already separates DEPTH and not FLAT. The subtraction's
   work is space constancy and reference-choice. Declared in the prereg (§7) and
   restated here (§3) so the mechanism is not oversold.
5. **THE GRAPH ARM IS SLOW (120 boot+settle) and I ran it concurrently with the
   migrated test**, so wall was 1630 s (both contending). No verdict rides on wall;
   loadavg recorded; the 2-worker cap held (peak loadavg ~2.1). A sequencing note,
   not a result.

---

## 10. WHAT IS NOT SHOWN (§8)

- **NOTHING HERE SAYS THE SURFACES ARE OBJECTS.** No surface is inspected for
  content; the 3 DEPTH surfaces are shown to be the 3 depth planes by
  construction, not to be "objects".
- **OCCLUSION/DISOCCLUSION IS NOT MODELLED.** Bands are FIXED image regions with
  per-region velocity (the small-baseline, ignore-boundary-motion idealization of
  a fronto-parallel plane). The finding is about the piecewise-constant flow field,
  not about occlusion cues (a real parallax boundary reveals/hides texture; that is
  a distinct, un-run mechanism).
- **SYNTHETIC FOURIER TEXTURES, NOT FOUND FRAMES** (the motion-sensor-gate rung's
  load-bearing assumption, inherited). One sensor (SAD `vector_field`), one aperture
  family, fronto-parallel planes, horizontal parallax only, N ≤ 3.
- **THE APERTURE BOUND IS DERIVED FROM ~2 DATA POINTS** (block 4 vs 8). `block/√5`
  predicts the direction and the N=2-vs-N=3 split; it is not swept across apertures.
- **NO TIMING CLAIM.** Every quantity is a bootstrap over the 80 seeds or exact/counted.

---

## 11. LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **116000–116999 (confirmatory seeds 116000–116079 + pilot 116900; unknown_sinks 0 for the confirmatory arm, none outside block; Term enum index 180 ALLOCATED and UNUSED — the DSL expresses the mechanism, so the build is a SEED not Rust)** | **PARALLAX FROM KNOWN SELF-MOTION — CONFIRM. A KNOWN SELF-SHIFT CARVES A DEPTH SCENE INTO ITS SURFACES WHERE A BYTE-IDENTICAL STATIC FRAME CANNOT; A FLAT CONTROL YIELDS ONE BLOB.** The closure rung's terminus (a single static frame cannot be carved few-and-large by ANY per-frame relation; objecthood lives in temporal coherence) made ACTIVE: the eye MOVES ITSELF by a known shift Δ (efference copy), subtracts the reference-plane field, and groups the residual by common fate. Stimulus (`scripts/parallax_char.py`, reusing `motion_sensor_lib` toroidal textures): ONE periodic texture, N vertical bands; DEPTH rolls each band by its own integer parallax shift `[0,3,6]`, FLAT rolls the whole frame uniformly — **the static frame `a` is BYTE-IDENTICAL (bands INVISIBLE: boundary gradient 15.35 ≈ within 16.36), only the post-shift frame differs, so the whole DEPTH-vs-FLAT difference is parallax vs uniform motion.** Grouped by common fate (SENSED SAD field), n=80 fresh seeds, unit=SEED, statistics SPECK-ROBUST (participation ratio `1/Σpᵢ²` + `largest_frac`, because the raw median/count are corrupted by the sensor's confabulation tail — the 84000 trap). **PRIMARY (N=3, block 8): DEPTH eff_surfaces 3.12 [3.11,3.13], largest_frac 0.358 [0.357,0.360], top-5 [.359,.333,.284,.003,.003] — three surfaces of ≈1/3 each; FLAT eff 1.00, largest 1.000, field discontinuity 0.00 (NULL EXPOSED) — CI-SEPARATED on both, at BOTH derived τ (exact 0 AND sensor √5). CONFIRM.** Secondary N=2 block8: 2 surfaces (eff 2.00, largest 0.500) vs FLAT one blob. **SPACE CONSTANCY: the fixated plane's ground-truth residual is 0.0 EXACTLY (efference subtraction exact-to-pixel), and a FLAT world armed on its own uniform motion mints 0 objects — the world reads stationary despite the retinal shift.** **INHERITED-BOUND arm (block 4, N=3): FALSIFY as predicted — the bands MERGE at τ=√5 (largest 0.963) and the count inflates at τ=0, verdict FLIPS ⇒ no §13-clean operating point; THE BOUND THAT FALLS OUT: resolvable depth planes ≤ aperture/tolerance ≈ block/√5 (block 4→2, block 8→3), derived from the sensor's own measured aperture and √5 tolerance.** **GRAPH-RESIDENT as a SEED `parallax_efference` (v1.0.0, depends vision_motion_group, ONE rule pe_efference_ref, default OFF): replaces mo_dominant's ESTIMATED reference (largest group's velocity) with the SUPPLIED efference copy (field.efference_v), suppressing mo_dominant via its OWN dom_done guard (no edit to the 84000 seed) so mo_mint refuses the CHOSEN fixation plane. DEFAULT-OFF byte-identical on all 20 seeds (§9); ARMED load-bearing on all 20 (§13.2 — refuses (0,3) fixation not (0,6) estimated dominant); FLAT armed mints 0 (space constancy); assert_settled clean. NO RUST, index 180 UNUSED.** §13: τ falls out (exact 0 / sensor √5, verdict holds at both); the manufacturing knob NAMED is the sensor APERTURE + depth SHIFTS (stimulus/sensor CONFIGURATION, the independent variable, reported across block 4 vs 8), NOT τ; seed has NO new constant (only flag guards + sentinels). Gate `test_parallax_efference_migrated.py` 7 passed, positive-controlled BOTH ways (a dead-control arming on the estimated dominant reproduces the baseline; a disarmed seed that changed behaviour fails). WHAT IT GOT WRONG: nearly used the confab-corrupted raw median/count (switched to speck-robust stats in the pilot, pre-registered THOSE); oriented in the SHARED checkout on the first command (the closure-rung §11 hazard, caught by `show-toplevel`, moved all work to the worktree); sensed space-constancy is bounded by the sensor's confabulation (3px), only the ground-truth is exactly 0; the efference-copy subtraction does NOT cause the carve (translation-invariant partition) — its work is space constancy + reference-choice. FLOORS asserted in-run (efference subtraction exact-to-pixel 0.0; bands invisible 15.35≈16.36); provenance its OWN step (7 passed) + printed from inside the process, re-verified `e039d2eec2dd` post-measurement (`provenance_stable` True); oracle `scripts/rung7_vision_bench.sh` **222 passed / 0 failed** (with `data/`) BEFORE and AFTER; seed_record written; loadavg [0.34→1.00]; engine `e039d2eec2dd` **`own` — NO RUST, index 180 UNUSED.** |

---

## 12. NAMED NEXT LEVERS, each needing its own pre-registration

1. **THE EYE GETS A MOTOR (the follow-on the brief names).** Here Δ is a rendering
   parameter and its efference copy is that same chosen Δ. The next rung closes the
   loop: the agent EMITS a saccade/translation (`seeds/motor_intent_core.json`
   exists), the world renders the parallax, and the SAME efference copy the motor
   command carries is subtracted. The mechanism is identical; only the source of Δ
   changes from a parameter to a motor act.
2. **OCCLUSION/DISOCCLUSION as a depth-ORDER cue.** This rung's bands are fixed
   image regions (no boundary motion). A real parallax boundary reveals/hides
   texture on the near/far side — a monocular depth-ORDER signal (which surface is
   in front) that common-fate velocity alone does not give.
3. **PARALLAX + BORDER OWNERSHIP.** The DEPTH residual's discontinuities sit at
   depth boundaries; `vision_border_ownership` produces edges WITH A SIDE. A cycle
   constrained to keep the near side consistent is the stronger closure the closure
   rung's §10 named — now with a temporal (parallax) boundary to anchor it.
4. **FINER DEPTH via a LARGER APERTURE, or a MULTI-SCALE sensor.** The block/√5
   bound says N=3 needs aperture ≥ 6. A coarse-to-fine motion sensor (large
   aperture proposes, small aperture refines) would resolve more depth planes than
   any single aperture — the "bins propose, continuous decides" idiom in the motion
   domain.
