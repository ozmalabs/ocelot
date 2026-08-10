# DOES THE PARALLAX CARVE SURVIVE REAL *MOTION*? — RESULTS: **A SPLIT VERDICT, ALL PRE-REGISTERED.**

> **STAGE A — CONFIRM.** Parallax DERIVED from depth + camera translation by
> perspective projection (not a hand-set shift) carves a real-BSDS depth scene
> into THREE surfaces (eff 3.09 [3.02,3.15]), the DEPTH ORDER falls out of the
> residual (nearer = larger, 80/80 seeds), CI-separated from a static-camera
> control (eff 1.00 exactly). Byte-identical to the windowed slide on all 80
> seeds — the ONLY change from 124000 is that the shift is DERIVED.
>
> **STAGE B slant — DEGRADE at √5, FALSIFY at exact τ=0.** A slanted surface's
> within-surface flow gradient SHATTERS the carve under exact-equality grouping
> (single-plane eff climbs 1.04 → 6.34 with tilt), but at the sensor's own
> tolerance √5 common-fate TOLERATES it — a single plane stays one surface, a
> 3-plane scene keeps count 3 and depth order 100% — until the adjacent-block
> displacement STEP exceeds √5 (a threshold that FALLS OUT of the sensor
> tolerance). Common-fate is MORE robust than its single-vector assumption
> because it is a TRANSITIVE flood.
>
> **STAGE B rotation — FALSIFY (a first-class result).** A camera ROTATION as
> small as 0.02 rad corrupts the depth carve — depth-order 100% → 44% (0.02) →
> 0% (0.04, the rank INVERTS, ρ=−0.78) → total shatter (eff 113.9 at 0.08) —
> because rotation's within-field (curvature) flow gradient cannot be nulled by a
> SINGLE-vector efference subtraction nor separated by common-fate from depth
> parallax. **THE NAMED NEXT RUNG: common-fate → AFFINE-FLOW grouping + full-field
> efference subtraction.** The carve is NOT rescued.
>
> Real photometry (124000) AND real fronto-parallel motion hold; a camera
> ROTATION is the thing that breaks common-fate. NO Rust, NO seed, Term index 180
> UNUSED — a measurement reusing the parallax carve.

*Pre-registration `VISION_PARALLAX_MOTION_PREREG.md`, committed **`f8ccfa45cd`**
BEFORE any confirmatory number (only pilots on already-burned seeds 116000–116039
had been computed — the §3-clause-3 power analysis). Nothing in it was edited
after the first confirmatory number.*

## THE ONE VARIABLE

116000 (synthetic) and 124000 (real photometry) both CONFIRMED the parallax
carve — but each imposed the parallax BY HAND, one uniform hand-set shift per
depth plane (a "windowed slide"). **This rung changes exactly that one variable:
the displacement FALLS OUT of depth + camera motion via perspective projection,
`d = f·T / Z` (nearer sweeps faster), rendered per-column from a REAL BSDS crop.**
Real BSDS photometry is kept throughout (do NOT reintroduce that variable). The
carve is REUSED byte-for-byte (`parallax_char.group_common_fate` /
`domains.motion_group_world.vector_field` — the mechanism the load-bearing
`parallax_efference` seed encodes). **NO Rust, NO new seed.**

## ENGINE PROVENANCE (§10)

- Branch **`worktree-agent-a451ac59c8fc26d6e`**; base SHA **`489bc41110`**
  (contains the parallax carve machinery + the three required results docs — read
  before starting). Prereg commit **`f8ccfa45cd`**.
- Engine **`67add13387fa`**, built IN THIS TREE by `scripts/engine_build.sh`.
  Rust source verified byte-identical to canonical *before* the build (a shared
  build would also be legitimate under §10.1); built in-tree anyway. **THIS RUNG
  ADDS NO RUST**; Term enum index 180 remains UNUSED.
- `provenance_line()` printed from INSIDE the measuring process into
  `results/parallax_motion.json`; `source_match` asserted `∈ {own, shared}` at
  start / mid / end (**never a literal build hash**, §10.1); read back **`own`**.
  Re-verified AFTER the measurement: `engine 67add13387fa @ <this worktree>/…`
  — unchanged (`provenance_stable == True`, asserted in the artifact).
- Migrated provenance gate as its OWN step, FIRST: **7 passed**; re-run AFTER:
  **7 passed**.
- **ORACLE `bash scripts/rung7_vision_bench.sh` (data/ symlinked, §10.2):**
  BEFORE **222 passed / 0 failed**; AFTER **222 passed / 0 failed** (§9 trivial —
  no Rust, no seed, no edit to any committed file; new scripts + new gate only).
- **LOAD:** `os.getloadavg()` in the artifact — start `[0.28, 0.28, 0.34]`, end
  `[0.63, 0.37, 0.37]`; wall **38.3 s** (all seven arms, n=80). ≤2 workers
  (`OMP_NUM_THREADS=2`). **No wall-clock quantity is a verdict** — every statistic
  is a bootstrap over the 80 seeds or an exact/counted quantity.
- **SEED CLAIM 125000–125999 (verbatim, §3 clause 8, post-run):**
  ```
  SEED CLAIM 125000-125999: CLEAN -- no collision DETECTED.
    Scope: 831 files with seed sinks; 541 UNRESOLVED sink sites tree-wide (counted, not discarded).
  ```
  Reads CLEAN because the confirmatory seeds are `range(125000, 125080)` — a
  `range` the static tool does not resolve to integers (the disclosed CLI blind
  spot; `seed_audit scripts/parallax_motion_measure.py` reports **10 unknown
  sinks**, the `default_rng(sd)`/`default_rng(k)` loop sites). The block IS
  genuinely drawn by THIS rung's confirmatory arm (125000–125079); pilots on
  burned 116000–116039; bootstrap CIs use fixed `default_rng(0..999)` resampling
  generators (the parallax rungs' exact `_ci`), not scene seeds. **`unknown_sinks:
  10` (the CLI blind spot), none outside the block; 541 unresolved sinks tree-wide
  (counted, not discarded).**

---

## 1. STAGE A — CONFIRM. MOTION-DERIVED PARALLAX CARVES THREE SURFACES, DEPTH ORDER FALLS OUT

Projected scene: depths `Z = [300, 10, 5]` (far background, middle=ref, near),
base `f·T = 30` → displacement `d = base/Z = [0.1, 3, 6]` → integer render shifts
`[0, 3, 6]`. The far background (Z=300) has SUB-PIXEL parallax that rounds to 0 —
the honest frame/continuum statement (the map is continuous, the observable is
stepped). n=80 fresh seeds 125000–125079, unit=SEED, both τ.

| statistic | Stage A motion (A1) | static control (A2) | windowed slide (baseline) | verdict |
|---|---|---|---|---|
| **eff_surfaces** (τ=√5) | **3.09 [3.02, 3.15]** | **1.00 [1.00,1.00]** | 3.09 (identical) | CI-separated ✓ |
| **eff_surfaces** (τ=0) | 3.17 [3.15, 3.20] | 1.00 | 3.17 (identical) | CI-separated ✓ |
| **largest_frac** (τ=√5) | **0.368 [0.354, 0.386]** | 1.000 | 0.368 | < 0.5 ✓ |
| **depth_order_correct** (both τ) | **80/80 = 1.00** (ρ=1.00) | — | — | falls out ✓ |
| **byte-identity to windowed slide** | **True on all 80 seeds** | — | — | only the shift is DERIVED ✓ |

**All five pre-registered Stage-A CONFIRM criteria met at BOTH τ.** The eye
carves a real-textured, motion-derived depth scene into three surfaces of ≈⅓ the
frame each (exactly the number of depth planes), the DEPTH ORDER (nearer plane =
larger residual velocity) falls out of the residual on every seed, and a
static-camera control (base=0 → b==a → no flow) gives one blob (eff 1.00
exactly). **⇒ STAGE A: CONFIRM.**

**Byte-identity is the exact in-tree comparison.** A fronto-parallel plane under
lateral translation IS a per-band uniform shift, so the projected frames are
byte-identical to the windowed slide `[0,3,6]` — proven on all 80 seeds
(`eff` values match to full float precision). The honest scope: **Stage A tests
nothing NEW at the pixel level** (the carve is inherited from 124000); its new
content is (a) the shift is DERIVED from 1/Z not hand-set, (b) the depth order is
now a checkable prediction that falls out, (c) the static-camera null. The real
test of real motion is Stage B.

---

## 2. STAGE B(i) — A SLANTED PLANE: DEGRADE AT √5, FALSIFY AT EXACT τ=0

One full-frame plane (Z0=7.5, central flow d0=4 px) given a fractional depth
tilt across its half-width, tilt ∈ {0…0.8}. True surface count = 1; the flow is a
gradient. n=80.

| tilt | per-block step | **eff (τ=0)** | **eff (τ=√5)** | reading |
|---|---|---|---|---|
| 0.0 | 0 | 1.04 [1.01,1.07] | 1.01 [1.01,1.02] | one surface ✓ |
| 0.2 | 1 | 2.11 [2.07,2.17] | 1.02 [1.00,1.04] | τ=0 splits; √5 holds |
| 0.4 | 1 | 3.62 [3.55,3.75] | 1.01 [1.00,1.03] | τ=0 shatters; √5 holds |
| 0.6 | 2 | 4.18 [4.09,4.34] | 1.01 [1.00,1.03] | τ=0 shatters; √5 holds (step ≤ √5) |
| 0.8 | 5 | 6.34 [6.23,6.52] | **1.14 [1.13,1.15]** | √5 breaks (step > √5) |

**At exact τ=0 the slant is a clean FALSIFY:** any non-zero gradient shatters the
surface into constant-integer-displacement strips (eff climbs monotonically
1.04 → 6.34). Exact common-fate cannot survive a within-surface gradient at all.

**At the sensor's own tolerance τ=√5 the slant is a DEGRADE, and common-fate is
MORE robust than its single-vector assumption:** it TOLERATES the within-surface
gradient (eff ≈ 1.01 through tilt 0.6) because it is a TRANSITIVE flood — adjacent
blocks whose displacement differs by ≤ √5 merge, and a gentle ramp stays ONE
connected group no matter how large its TOTAL range. It breaks only when the
ADJACENT-block step exceeds √5: tilt 0.6 (max step 2 ≤ √5) holds; tilt 0.8 (max
step 5 > √5) breaks (eff 1.14). **The threshold FALLS OUT of the sensor tolerance
√5 — a step of 2 still merges (‖(0,2)‖=2 ≤ √5), a step of 3 shatters — it is not
picked.**

## 3. STAGE B(ii) — 3 PLANES, MIDDLE SLANTED: CONFIRM (no merge-wrongly at √5)

| tilt (middle band) | eff (τ=√5) | depth_order_correct |
|---|---|---|
| 0.0 | 3.09 [3.02,3.15] | 1.00 |
| 0.2 | 3.11 [3.05,3.15] | 1.00 |
| 0.4 | 3.13 [3.07,3.18] | 1.00 |
| 0.6 | 3.12 [3.06,3.17] | 1.00 |

**CONFIRM.** At √5 the middle plane's gradient is absorbed, the count stays 3, and
the depth order stays correct on every seed through tilt 0.6 — the residual gaps
of 3 (> √5) between planes prevent the tolerated within-surface gradient from
bridging to a neighbour. No merge-wrongly at the swept tilts.

## 4. STAGE B(iii) — A CAMERA ROTATION: FALSIFY (names common-fate → affine-flow)

Depths `[300,10,5]`, camera translation AND a y-axis rotation rot ∈ {0…0.08} rad.
The efference copy is the SAME single-vector subtraction the parallax seed uses
(the fixated plane's flow). n=80, τ=√5.

| rot (rad) | eff (τ=√5) | depth_order_correct | depth_rank ρ |
|---|---|---|---|
| 0.00 | 3.09 [3.02, 3.15] | 1.00 | +1.00 |
| **0.02** | **2.48 [2.35, 2.63]** | **0.44** | +0.63 |
| **0.04** | 3.31 [3.04, 3.62] | **0.00** | **−0.78** |
| **0.08** | **113.92 [101.35, 127.28]** | 0.10 | −0.30 |

**FALSIFY, and it is a first-class result.** A camera rotation as small as
**0.02 rad (~1.1°)** corrupts the depth carve: the depth-order rate collapses
100% → 44% → **0%** (at 0.04 the rank INVERTS, ρ=−0.78 — the symmetric curvature
term flips which band reads nearest), and by 0.08 the field SHATTERS (eff 113.9).
**Why:** a y-axis rotation induces a horizontal flow `u(x)=rot·(f + (x−cx)²/f)`
that is (a) DEPTH-INDEPENDENT and (b) a spatially-varying GRADIENT across the
whole field. A SINGLE-vector efference subtraction (the parallax seed's
mechanism) nulls it at only one point, leaving the curvature gradient; common-fate
then mis-groups that gradient AND cannot separate it from the depth parallax. **THE
NAMED NEXT RUNG: common-fate → AFFINE-FLOW grouping (group by a consistent local
flow AFFINE model) + full-field efference subtraction of the KNOWN rotational flow
(depth-independent, so the agent CAN compute it — the single-vector mechanism is
what falls short, not the information).** The carve is NOT rescued.

## 5. STAGE B(iv) — PURE ROTATION (no depth): the null is exposed

| rot (rad) | eff (τ=0) | eff (τ=√5) |
|---|---|---|
| 0.00 | 1.00 | 1.00 |
| 0.02 | 1.15 [1.13,1.19] | 1.01 [1.01,1.01] |
| 0.04 | 1.86 [1.82,1.90] | 1.10 [1.08,1.13] |
| 0.08 | 243.97 [226.66,260.74] | 97.11 [84.68,111.50] |

With NO depth (base=0), a GENTLE rotation correctly mints ≈ **one** group at √5
(rot ≤ 0.04) — rotation carries no depth, so it does not invent spurious surfaces
at the sensor tolerance — but a STRONG rotation (0.08) shatters even without depth.
This exposes the B(iii) FALSIFY as a genuine rotation effect, not a depth
artefact: rotation's within-field gradient is the culprit at both.

---

## 6. WHICH REGISTERED OUTCOME OCCURRED

| criterion | measured | outcome |
|---|---|---|
| **Stage A** eff ⊂ [2.5,3.5], largest<0.5, depth_order ≥0.9, CI-sep from static, byte-identical | 3.09, 0.368, 1.00, sep from 1.00, all 80 | **CONFIRM** |
| **Stage B slant** CONFIRM/DEGRADE/FALSIFY | √5 tolerates to per-block step √5 (DEGRADE, threshold falls out); τ=0 shatters (FALSIFY); 3-plane count+order held (CONFIRM) | **DEGRADE (√5) + FALSIFY (τ=0)** |
| **Stage B rotation** CONFIRM/FALSIFY | 0.02 rad → depth_order 0.44; 0.04 → 0.00; 0.08 → eff 113.9 | **FALSIFY** |

My predictions (prereg §Predictions) held in every particular: Stage A CONFIRM
(~95%); slant DEGRADE-at-√5 / FALSIFY-at-0 (~85%); rotation FALSIFY (~80%), with
the pure-rotation control minting no spurious surfaces at gentle rot. The one
proviso quantified rather than broken: the slant √5 break lands between per-block
step 2 (tilt 0.6, holds) and 5 (tilt 0.8, breaks), bracketing √5≈2.24.

---

## 7. THE SENSOR BOUND THE TRUE-MOTION CARVE INHERITS (§8), AND HOW MOTION INTERACTS WITH IT

- **Inherited from 94000/124000:** the SAD sensor confabulates where a block
  carries < 0.4 block-std (unreachable in BSDS at this band width, 124000) and
  silent-misses 50–75% on a straight edge (the aperture problem). Measured here:
  Stage A confab **8.2%** (≈ the 124000 natural rate 7.3%), and the reference-band
  SENSED residual reaches **8 px** on a confab cell while the efference copy is
  EXACT (ground-truth residual 0) — the same space-constancy DEGRADE 124000
  named, carried into true motion unchanged.
- **How true motion's within-surface gradient INTERACTS with it (the new
  coupling):** a slant or rotation makes the displacement vary WITHIN a block
  (`within_block_step` up to 5 at tilt 0.8), so a single block spans multiple true
  displacements — the block match becomes ambiguous exactly as an edge does. This
  is why the √5 slant break and the rotation shatter co-occur with large
  within-block steps: the within-surface gradient drives the sensor toward its own
  aperture failure. The two bounds are not independent — motion's gradient
  MANUFACTURES the sensor's ambiguity.

---

## 8. WHAT I GOT WRONG — in full

1. **MY FIRST SLANT PARAMETRIZATION WAS UNPHYSICAL AND CRASHED.** I first tilted
   the plane as `Z += slant·(x−center)` on the ABSOLUTE depth scale, which let Z
   pass through 0 (the plane through the camera), exploding the displacement to
   ~50 px and overflowing the source crop (a real RuntimeError in the pilot). Fixed
   to a BOUNDED fractional tilt `Z = Z_i·(1 + tilt·u)`, |tilt|<1, so Z stays
   positive. Caught in the pilot, before the prereg.
2. **STAGE A TESTS NOTHING NEW AT THE PIXEL LEVEL — and I say so.** A
   fronto-parallel plane under lateral translation IS a per-band uniform shift, so
   the projected frames are byte-identical to the windowed slide. Stage A's new
   content is depth-order + static control + motion-derivation, not a new carve. I
   report the byte-identity as the finding it is (the ONLY change is the shift is
   derived), not as an independent confirmation.
3. **THE [0,3,6] REALIZATION USES AN EXTREME FAR DEPTH (Z=300).** To reproduce the
   124000 floor exactly I chose depths whose far band rounds to 0 parallax. That is
   an honest distant background (sub-pixel parallax, the frame/continuum
   invariant), but it is a DEPTH CHOSEN to realize a specific shift set — disclosed,
   the same standing as 116000 choosing shifts [0,3,6].
4. **THE ROTATION MODEL IS A SIMPLIFIED 1-D PINHOLE CURVATURE.** `u(x)=rot·(f +
   (x−cx)²/f)` is the horizontal-flow term of a small y-axis rotation; a full 3-D
   rotation also has vertical flow and higher-order terms. The FALSIFY DIRECTION is
   robust to the approximation (ANY within-field gradient breaks single-vector
   common-fate), but the exact rot onset (0.02–0.04) is model-dependent — I do not
   claim the onset value transfers to a real camera, only that a small rotation
   breaks the mechanism.
5. **THE EFFERENCE COPY IS A SINGLE VECTOR — and I did NOT "fix" it for rotation.**
   A KNOWN rotation's flow is depth-independent, so the agent COULD subtract the
   full field and remove it. Subtracting the full field would be REIMPLEMENTING the
   carve (forbidden §0) and RESCUING a failed gate (forbidden §5). I kept the
   parallax seed's single-vector mechanism, so the FALSIFY stands as a property of
   THAT mechanism, and names the fix as the next rung rather than smuggling it in.
6. **THE SENSED SPACE-CONSTANCY (8 px) IS THE SENSOR'S, NOT THE EFFERENCE COPY'S**
   — inherited from 124000, restated so it is not oversold as broken.

---

## 9. WHAT IS NOT SHOWN (§8)

- **NOTHING SAYS THE SURFACES ARE OBJECTS** (inherited): the depth surfaces are the
  depth planes by construction, not inspected for content.
- **NO OCCLUSION / DISOCCLUSION.** Bands/planes are fixed image regions with
  per-region depth; a real parallax boundary reveals/hides texture (a distinct,
  un-run depth-ORDER cue).
- **THE ROTATION FALSIFY'S ONSET IS MODEL-DEPENDENT** (simplified pinhole
  curvature); only its DIRECTION (a small rotation breaks single-vector
  common-fate) is claimed to transfer.
- **STILL SYNTHETIC 3-D STRUCTURE, REAL PHOTOMETRY + REAL PROJECTION.** The pixels
  and the displacement are real (BSDS crop + perspective projection); the SCENE
  geometry (fronto-parallel/slanted planes, one aperture family, horizontal
  parallax, N≤3) is constructed. Genuine found 3-D-motion video with measured
  camera pose is the remaining deferred variable.
- **NO TIMING CLAIM.** Every quantity is a bootstrap over the 80 seeds or
  exact/counted.

---

## 10. LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **125000–125999 (confirmatory 125000–125079 + pilots on BURNED 116000–116039; unknown_sinks 10 — the `range()`/loop-var CLI blind spot, none outside block; NO Rust, NO seed, Term index 180 UNUSED — a measurement reusing the parallax carve)** | **DOES THE PARALLAX CARVE SURVIVE REAL MOTION? A SPLIT VERDICT, ALL PRE-REGISTERED.** The last unmet parallax variable (124000 named it): the displacement now FALLS OUT of depth + camera motion via PERSPECTIVE PROJECTION (`d=f·T/Z`, nearer sweeps faster), NOT a hand-set uniform shift, rendered per-column from a REAL BSDS crop (photometry kept from 124000). Carve REUSED byte-for-byte (`group_common_fate`/`vector_field`). **STAGE A (fronto-parallel translation) — CONFIRM: motion-derived parallax carves THREE surfaces (eff 3.09 [3.02,3.15] τ=√5, 3.17 τ=0), largest 0.368, the DEPTH ORDER falls out of the residual (nearer=larger, 80/80 seeds, ρ=1.00), CI-separated from a static-camera control (base=0 → b==a → eff 1.00 EXACTLY); BYTE-IDENTICAL to the windowed slide on all 80 seeds — the only change is the shift is DERIVED (honest scope: Stage A tests nothing NEW at the pixel level; the new content is depth-order + static null + motion-derivation).** **STAGE B slant (single plane) — DEGRADE at √5, FALSIFY at exact τ=0: a within-surface gradient SHATTERS the carve at exact equality (eff 1.04→6.34 with tilt) but at √5 common-fate TOLERATES it (eff≈1.01 through tilt 0.6) because it is a TRANSITIVE flood — MORE robust than its single-vector assumption — until the ADJACENT-BLOCK step exceeds √5 (tilt 0.8, step 5, eff 1.14); THE THRESHOLD FALLS OUT of the sensor tolerance √5 (step 2 merges, step 3 shatters), not picked. 3-plane middle-slanted CONFIRM (count 3, depth order 100% through tilt 0.6 — no merge-wrongly).** **STAGE B rotation — FALSIFY (first-class): a camera rotation as small as 0.02 rad corrupts the carve — depth-order 100%→44% (0.02)→0% (0.04, rank INVERTS ρ=−0.78)→shatter (eff 113.9 at 0.08) — because rotation's depth-INDEPENDENT within-field curvature gradient cannot be nulled by a SINGLE-vector efference subtraction nor separated by common-fate from depth parallax. NAMES THE NEXT RUNG: common-fate → AFFINE-FLOW grouping + full-field efference. Pure-rotation control (no depth) mints ≈1 surface at gentle rot (null exposed).** THE SENSOR BOUND INHERITED (94000/124000): confab 8.2% (≈124000's 7.3%), sensed space-constancy 8 px while the efference copy is EXACT (GT residual 0); AND a NEW coupling — motion's within-surface gradient (within-block step up to 5) MANUFACTURES the sensor's aperture ambiguity, so the √5 slant break and rotation shatter co-occur with large within-block steps. WHAT IT GOT WRONG: first slant parametrization let Z→0 (unphysical, crashed — fixed to bounded fractional tilt); Stage A is byte-identical to the windowed slide so tests nothing NEW at the pixel level (said so); the [0,3,6] realization uses an extreme far depth Z=300 (honest distant background, disclosed); the rotation model is a simplified 1-D pinhole curvature (only the FALSIFY direction transfers, not the onset value); the single-vector efference was NOT "fixed" for rotation (would reimplement + rescue — kept, so the FALSIFY names the next rung). Provenance its OWN step (7 passed, re-verified 67add13387fa post-run, provenance_stable True, source_match `own`); oracle rung7_vision_bench 222/0 BEFORE and AFTER; own gate `test_parallax_motion_migrated.py` 8 passed (positive-controlled: a gradient render is NOT byte-identical; the §13 no-tuned-threshold audit); loadavg [0.28→0.63], ≤2 workers, wall 38.3 s; engine `67add13387fa` `own` — NO RUST, NO SEED, index 180 UNUSED. |

---

## 11. NAMED NEXT LEVERS (each its own pre-registration)

1. **COMMON-FATE → AFFINE-FLOW GROUPING (the FALSIFY names it).** Group cells by a
   consistent local flow AFFINE model (translation + linear gradient), not a single
   vector, so a slanted surface's ramp and a rotation's curvature are ONE affine
   surface, not many strips. Paired with a FULL-FIELD efference subtraction of the
   KNOWN rotational flow (depth-independent — computable from the pose alone). This
   is the mechanism the rotation FALSIFY demands.
2. **REAL 3-D-MOTION VIDEO with measured camera pose** (or the codec motion-vector
   field, memory CODEC↔EYE) — the last constructed variable is the SCENE geometry;
   found video over real 3-D structure retires it.
3. **OCCLUSION / DISOCCLUSION as a depth-ORDER cue** — a real parallax boundary
   reveals/hides texture; a monocular front/behind signal common-fate velocity
   alone does not give.
