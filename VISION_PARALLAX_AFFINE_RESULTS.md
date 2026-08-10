# AFFINE-FLOW GROUPING + FULL-FIELD EFFERENCE vs THE ROTATION FALSIFY — RESULTS: **DEGRADE, ALL PRE-REGISTERED.**

> **THE ROTATION FALSIFY IS RESCUED — BY ONE OF THE TWO NAMED FIXES, AND IT
> FIXES A DIFFERENT LAYER THAN 125000 NAMED.** Full-field efference, applied as a
> **search-centre remap of the sensor** (predictive remapping), recovers the
> depth carve under camera rotation from 125000's **0.02 rad break out to ~0.12
> rad — a 6× extension** (depth-order 1.00→1.00→1.00→0.99→**0.90** through rot
> {0,0.02,0.04,0.08,0.12}, then breaks to 0.00 at 0.16), BOUNDED by the
> frame/continuum discretization (the continuously-cancelled rotation leaves a
> STEPPED residual that lifts the ref-band residual above the near-band and
> inverts the depth order between rot 0.12 and 0.14 — measured, not picked).
>
> **THE 2×2 ASSIGNS ALL CREDIT TO EFFERENCE, NONE TO AFFINE.** `full_affine ==
> full_cf` AND `single_affine == single_cf` EXACTLY at every rotation — affine
> grouping changes NOTHING. Worse, affine actively HARMS the high-tilt slant
> (full_affine eff 1.55 vs full_cf 1.01) and perturbs 9/80 translation scenes.
> **The FALSIFY named "common-fate → affine grouping", but the grouping was never
> the problem: the SENSOR APERTURE is.** Proven three ways: (1) affine (a pure
> grouping change) rescues nothing; (2) full-field efference subtracted POST-HOC
> (V − field, grouping untouched) FAILS (depth-order 0.20/0.00/0.03) because the
> rotation flow SATURATES the sensor before subtraction; (3) the SAME field
> applied as a search-centre remap RESCUES — the fix is where the sensor LOOKS,
> not how the field is grouped.
>
> **STAGE A (translation) — CONFIRM & preserved.** The DEFAULT carve
> `(single-vector, common-fate)` is BYTE-IDENTICAL to 125000 on all 80 seeds (the
> FALSIFY baseline re-earned exactly); all four 2×2 arms carve three surfaces
> (eff ≈ 3.09–3.12, depth-order 1.00). **STAGE B slant — no worse** (full_cf 1.01
> at tilt 0.8, better than single_cf's 1.15; affine harms it). **NO Rust, NO
> seed, Term index 181 UNUSED** — a measurement extending the parallax carve.

*Pre-registration `VISION_PARALLAX_AFFINE_PREREG.md`, committed **`c50f029621`**
BEFORE any confirmatory number (only EXPLORATORY pilots on already-burned seeds
116000–116029 had been computed). Nothing in it was edited after the first
confirmatory number.*

## THE TWO MECHANISMS THIS RUNG BUILT

125000's rotation FALSIFY named two coupled fixes. This rung BUILT both, ablatable
as arm flags (`efference∈{single,full}` × `grouping∈{cf,affine}`), and measured
which is load-bearing.

- **FULL-FIELD EFFERENCE** (`parallax_affine_char.carve_full`): the known pose
  predicts the fixated plane's flow EVERYWHERE, `d_ref(x)=base/Z_ref +
  rot·(f0+(x−cx)²/f0)` — translation const + the depth-INDEPENDENT rotational
  curvature — applied as a **search-centre remap** (`vector_field_eff`). The
  single-vector baseline (`carve_single`, = 125000 EXACT) knows only `base/Z_ref`.
- **AFFINE-FLOW GROUPING** (`affine_group`): group by ONE local affine model
  `v(pos)=A·pos+b`, MDL-guarded so a slope engages only when a within-region
  variation exceeds τ and an affine fit brings it back under τ (translation's
  uniform flow → A=0 → common-fate).

## ENGINE PROVENANCE (§10)

- Branch **`gamma-substrate/vision-affine-flow-efference`**; base HEAD
  **`21801a9b5f`** (contains the 125000 parallax-motion carve + all three required
  results docs). Prereg commit **`c50f029621`**.
- Engine **`16fb14133c30`**, `source_match` **`shared`** — a source-identical
  build of canonical (verified from INSIDE the measuring process via
  `provenance_line()`; **THIS RUNG ADDS NO RUST**, so a shared build is legitimate
  §10.1). Term enum index 181 remains UNUSED (NUM_TERM_VARIANTS=181).
- `provenance_line()` printed into `results/parallax_affine.json`; `source_match ∈
  {own, shared}` asserted start/mid/mid2/end (**never a literal build hash**,
  §10.1); read back **`shared`**. Re-verified AFTER: unchanged
  (`provenance_stable == True`, asserted in the artifact).
- Migrated provenance gate as its OWN step: **7 passed** (before AND after).
- **ORACLE `bash scripts/rung7_vision_bench.sh` (data/ symlinked, §10.2):** BEFORE
  **222 passed / 0 failed**; AFTER **222 passed / 0 failed** (§9 trivial — no Rust,
  no seed, no edit to any committed file; new scripts + new gate only).
- **LOAD:** `os.getloadavg()` in the artifact — start `[5.59, 5.13, 3.85]`, end
  `[5.71, 5.25, 3.99]` (machine shared with concurrent agents); wall **78.6 s**,
  n=80. ≤2 workers (`OMP_NUM_THREADS=2`). **No wall-clock quantity is a verdict** —
  every statistic is a bootstrap over the 80 seeds or an exact/counted quantity.
- **SEED CLAIM 126000–126999 (verbatim, §3 clause 8 — in the prereg, committed
  before any confirmatory number):** reads CLEAN. `seed_audit` reports
  **`unknown_sinks: 1`** on `parallax_affine_measure.py` and **1** on
  `parallax_affine_char.py` — the disclosed `default_rng(sd)`/loop-var CLI blind
  spot (the confirmatory block is drawn by `range(126000,126080)`, which the static
  tool does not resolve to integers), **none outside the block**; 545 unresolved
  sinks tree-wide (counted, not discarded). Confirmatory seeds `range(126000,
  126080)`; pilots on BURNED 116000–116029; bootstrap CIs use fixed
  `default_rng(0..999)`.

---

## 1. THE 125000 ROTATION FALSIFY, RE-EARNED IN-TREE (the baseline)

The default carve `(single-vector efference, common-fate)` is **byte-identical to
125000's carve on all 80 seeds** (eff match to full float precision,
`depth_order_correct` identical). Under it, the rotation FALSIFY reproduces
exactly: depth-order **1.00 (rot 0) → 0.30 (0.02) → 0.00 (0.04) → 0.09 (0.08)**.
This is the exact in-tree comparison the rescued-vs-broken contrast rests on.

## 2. STAGE B ROTATION — THE 2×2 (the headline)

Depths `[300,10,5]`, camera translation AND a y-axis rotation, n=80, τ=√5.
`depth_order_correct` rate per arm:

| rot (rad) | single_cf (=125000) | single_affine | **full_cf** | full_affine | eff (full_cf) |
|---|---|---|---|---|---|
| 0.00 | 1.00 | 1.00 | **1.00** | 1.00 | 3.09 [3.03,3.13] |
| 0.02 | 0.30 | 0.30 | **1.00** | 1.00 | 3.34 [3.28,3.38] |
| 0.04 | 0.00 | 0.00 | **1.00** | 1.00 | 3.40 [3.36,3.43] |
| 0.08 | 0.09 | 0.09 | **0.99** | 0.99 | 3.73 [3.71,3.75] |
| 0.12 | 0.12 | 0.12 | **0.90** | 0.90 | 4.20 [4.17,4.25] |
| 0.16 | 0.15 | 0.15 | **0.00** | 0.00 | 4.61 [4.56,4.65] |

**CREDIT ASSIGNMENT (the point of the 2×2):**
- **full_cf RESCUES** the depth order through rot 0.12 (0.90 at the boundary, 0.99
  at 0.08) where single_cf has collapsed (0.00–0.30). **The tolerated rotation
  extends 0.02 → ~0.12, a 6× improvement.**
- **`full_affine == full_cf` AND `single_affine == single_cf` EXACTLY at every
  rotation.** Affine grouping is **NOT load-bearing** — it changes nothing. After
  full efference the residual field is de-rotated (piecewise-constant), so the
  affine MDL guard never engages (identical to cf); in the single-vector arm the
  sensor is saturated, and affine grouping of a saturated field is still broken.
- **Full-field efference is 100% of the credit; affine grouping is 0%.**

## 3. THE MECHANISM — SEARCH-CENTRE, NOT POST-HOC; SENSOR, NOT GROUPING

125000 named **common-fate → affine grouping**. The measurement REFUTES that
layer:

**DIAGNOSTIC — full-field POST-HOC subtraction FAILS.** Subtracting the SAME full
predicted field AFTER the sensor (`V − field`, grouping untouched) recovers the
depth order on only **0.20 (rot 0.02) / 0.00 (0.04) / 0.03 (0.08)** — i.e. it does
NOT rescue. **Why:** rotation adds up to ~7 px of flow, so the ABSOLUTE
displacement (~12–13 px) exceeds the SAD sensor's aperture (radius = block = 8) —
`V` is already SATURATED before you subtract. The fix is to re-centre the sensor's
SEARCH APERTURE on the predicted self-motion (`vector_field_eff`), so the aperture
is spent on the small DEPTH residual, not the large self-motion. **The same field,
applied as a search prior, rescues; applied post-hoc, fails.** The failure was in
the SENSOR (aperture), not the GROUPING — and affine grouping, a pure grouping
change, therefore cannot help (§2 confirms it does not).

This is a first-class correction of 125000's own diagnosis, and it connects to the
§7 coupling 125000 itself named ("motion's within-surface gradient MANUFACTURES
the sensor's aperture ambiguity"): the aperture is the binding constraint, and the
efference beats it by moving where the sensor looks.

## 4. WHAT THE BOUND FALLS OUT OF (§13) — THE FRAME/CONTINUUM DISCRETIZATION

The rescue is BOUNDED at ~0.12 rad, and the bound is MEASURED (swept 0.02→0.16),
not picked. What it falls out of — the per-band MEAN residual under full_cf
(depth order needs near > ref > far), n=40 fresh seeds:

| rot | far (idx0) | **ref/mid (idx1)** | **near (idx2)** | order |
|---|---|---|---|---|
| 0.04 | −2.65 | +0.52 | +2.09 | near>ref>far ✓ |
| 0.08 | −2.55 | +1.00 | +2.05 | ✓ |
| 0.10 | −2.88 | +1.39 | +1.61 | ✓ |
| 0.12 | −3.17 | +1.87 | +2.11 | ✓ (marginal) |
| 0.14 | −3.15 | **+2.11** | **+1.53** | **INVERTED** |
| 0.16 | −3.50 | +2.96 | +1.32 | INVERTED |

The efference cancels the rotation EXACTLY in the CONTINUOUS map — but the
OBSERVABLE is the STEPPED integer render, and the ref-band residual (which should
be 0) rises monotonically **+0.52 → +2.96** with rot because the per-column rounded
render, matched by the per-block sensor against the block-centre prediction, leaves
a residual ∝ rot·(curvature). The depth order inverts when this stepped residual
lifts the ref band above the near band — **between rot 0.12 and 0.14**. This is the
CLAUDE.md frame/continuum invariant made numeric ("you can apply π, but any given
circle is stepped"): the continuous rotation is applied and cancelled; its
observable residual is stepped and eventually dominates the depth gap. It is the
rotation twin of 125000's slant √5 break (both discretization/aperture limits).
**Honest scope:** the exact boundary (~0.12) is an EMERGENT discretization limit of
this integer render + block sensor, mechanism-attributed and measured — I do NOT
claim a closed-form derivation of 0.12, only that it is not tuned and that its
CAUSE is the stepped observable (the same honesty 125000 applied to its onset).

## 5. STAGE A (TRANSLATION) — CONFIRM, DEFAULT PRESERVED

| arm | eff (τ=√5) | depth_order |
|---|---|---|
| single_cf (DEFAULT = 125000) | 3.106 [3.07,3.14] | 1.00 |
| single_affine | 3.122 [3.10,3.14] | 1.00 |
| full_cf | 3.088 [3.03,3.13] | 1.00 |
| full_affine | 3.121 [3.10,3.14] | 1.00 |

**All four carve three surfaces, depth order 1.00.** `(single,cf)` is byte-
identical to 125000 on **80/80** seeds — §9 default preserved. The full-efference
arm is a DIFFERENT sensor (re-centred aperture) so it is ~equal but NOT byte-
identical (eff 3.088 vs 3.106, differing only on confab cells) — its byte-identity
is NOT claimed; the preserved default is `(single,cf)`. **Affine reduces to cf on
translation on 71/80 seeds** (the 9 differ only on isolated confab specks where a
region's spread exceeds τ) — a MAJORITY reduction, and moot since affine is not
load-bearing.

## 6. STAGE B SLANT — NO WORSE (and affine HARMS it)

Single full-frame plane Z0=7.5, sweep tilt, eff per arm (n=80, τ=√5):

| tilt | per-block step | single_cf | single_affine | full_cf | full_affine |
|---|---|---|---|---|---|
| 0.0 | 0 | 1.01 | 1.02 | 1.01 | 1.01 |
| 0.4 | 1 | 1.01 | 1.01 | 1.01 | 1.01 |
| 0.6 | 2 | 1.01 | 1.04 | 1.01 | 1.04 |
| 0.8 | 5 | 1.15 | **1.84** | **1.01** | **1.55** |

At tilt 0.8 (step 5 > √5, where 125000's common-fate degrades to 1.15) the
load-bearing arm **full_cf is BETTER (1.01)** — the search-centre sensor handles
the mean plane flow more cleanly. **Affine HARMS the slant** (single_affine 1.84,
full_affine 1.55): where the residual has a real ramp the MDL guard engages a slope
that mis-groups the sensor-saturated high-tilt field. So affine is not merely inert
— it is a WORSE grouping on the one regime it was named to help, because at the
tilt where common-fate breaks the SENSOR has already saturated (the within-block
gradient), and no grouping fixes a saturated sensor.

---

## 7. WHICH REGISTERED OUTCOME OCCURRED

| criterion | measured | outcome |
|---|---|---|
| rotation RESCUED ≥0.9, magnitude vs 0.02 | full_cf ≥0.9 through rot 0.12 (6×), breaks 0.16 | rescued, **BOUNDED** |
| the bound FALLS OUT (not picked) | frame/continuum discretization; ref-band residual inverts near 0.12–0.14 (measured, swept) | falls out (mechanism-attributed) |
| WHICH fix is load-bearing (2×2) | full-field efference 100%; affine 0% (identical every arm; harms slant) | **efference alone** |
| Stage A `(single,cf)` byte-identical | 80/80 | **CONFIRM** |
| Stage B slant no worse | full_cf better (1.01 vs 1.15) | **no worse** |

**⇒ DEGRADE.** The rotation carve is rescued up to a larger-but-BOUNDED magnitude
(0.02 → 0.12, 6×) by ONE of the two named fixes — **full-field efference, applied
as a search-centre remap** — while the other named fix (affine grouping) is not
load-bearing and harms the slant. My prereg prediction of DEGRADE, with efference
load-bearing / affine inert / the search-centre proviso / the discretization bound
/ Stage-A byte-identity, held in every particular.

## 8. WHAT I GOT WRONG — in full

1. **MY FIRST DESIGN APPLIED FULL-FIELD EFFERENCE AS A POST-HOC VECTOR SUBTRACTION
   — AND IT FAILED.** I predicted (and first coded) `R = V − full_field` and
   measured depth-order 0.30/0.00/0.03 — the rotation was NOT rescued. The
   diagnosis I missed at first: the un-compensated rotation flow (~7 px) pushes the
   ABSOLUTE displacement past the sensor's aperture (radius=block=8), so V is
   SATURATED before subtraction. The fix — re-centre the SEARCH APERTURE on the
   prediction — moved the efference from a subtraction to a **predictive remapping**
   of the sensor. I kept the failed post-hoc arm as a committed DIAGNOSTIC (§3, it
   proves the search-centre application, not the field value, is the mechanism).
2. **I EXPECTED BOTH NAMED FIXES TO MATTER; ONLY ONE DOES.** I inherited 125000's
   framing that affine grouping + full efference were COUPLED. The 2×2 refutes it:
   `full_affine == full_cf` and `single_affine == single_cf` exactly — affine is
   inert, and worse, it HARMS the slant. I built affine grouping as pre-registered
   and reported it as a first-class NEGATIVE with credit assigned, rather than
   quietly dropping it.
3. **THE FALSIFY NAMED THE WRONG LAYER, AND SO NEARLY DID I.** "common-fate →
   affine grouping" points at the GROUPING. The measurement shows the SENSOR
   aperture is the binding constraint. I nearly reported affine as "buggy, needs
   more work"; the post-hoc diagnostic showed the grouping was never the problem.
4. **AFFINE GROUPING IS NOT BYTE-IDENTICAL ON TRANSLATION (71/80), AND I DO NOT
   HIDE IT.** The MDL guard reduces to common-fate on uniform fields but engages on
   9 confab-speck scenes where a region's spread exceeds τ. The task asked for
   byte-identity; I report the 71/80 as the honest degenerate-reduction number and
   note it is moot (affine is not adopted). The §9-preserving default is
   `(single,cf)`, which IS 80/80.
5. **THE ROTATION-ONSET AND BOUND ARE MODEL-DEPENDENT (inherited from 125000).**
   The rotation model is the simplified 1-D pinhole curvature `u(x)=rot·(f0+(x−cx)²
   /f0)` — a full 3-D rotation has vertical flow and higher-order terms. Only the
   DIRECTION (efference-as-search-prior rescues; the bound is a discretization
   limit) is claimed to transfer, not the exact 0.12 onset.
6. **THE GATE CAUGHT A REAL MARGINAL AT ROT 0.02.** At n=12 burned seeds, single_cf
   at rot 0.02 sits at exactly 0.50 (0.02 IS the FALSIFY onset — 125000 measured
   0.44 at n=80). I moved the gate's "single broken" assertion to rot 0.04/0.08
   where the break is unambiguous, rather than weaken the threshold. (The
   confirmatory n=80 reads 0.30 at rot 0.02 — the collapse is real; 0.02 is just
   the marginal edge.)

## 9. WHAT IS NOT SHOWN (§8)

- **NOTHING SAYS THE SURFACES ARE OBJECTS** (inherited): the depth surfaces are the
  depth planes by construction.
- **THE RESCUE IS BOUNDED at ~0.12 rad** — a strong rotation (>0.14) still inverts
  the depth order via the discretization residual. Beyond it needs finer render /
  a sub-pixel sensor (a distinct, un-run variable) or ≥3 frames.
- **THE ONSET/BOUND IS MODEL-DEPENDENT** (simplified 1-D pinhole curvature); only
  the mechanism (search-centre efference rescues; the bound is a discretization
  limit; affine is inert) is claimed to transfer.
- **STILL SYNTHETIC 3-D STRUCTURE, REAL PHOTOMETRY + REAL PROJECTION** (inherited
  from 125000): real BSDS pixels + perspective projection; the SCENE geometry
  (fronto-parallel/slanted planes, one aperture family, N≤3) is constructed.
  Genuine found 3-D-motion video with measured camera pose remains the deferred
  variable.
- **REAL ROTATIONAL MOTION IS NOW CARVED — under the model.** Camera rotation
  (which 125000 could not carve at all past 0.02 rad) is carved through 0.12 rad
  via full-field efference. But this is rotation in the SIMULATED projection, not
  found video; the deferred lever (real 3-D-motion video) stands.
- **NO TIMING CLAIM.** Every quantity is a bootstrap over the 80 seeds or
  exact/counted.

---

## 10. LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **126000–126999 (confirmatory 126000–126079 + pilots on BURNED 116000–116029; unknown_sinks 1 — the `range()`/loop-var CLI blind spot, none outside block; NO Rust, NO seed, Term index 181 UNUSED / NUM_TERM_VARIANTS=181 — a measurement extending the parallax carve)** | **AFFINE-FLOW GROUPING + FULL-FIELD EFFERENCE vs 125000's ROTATION FALSIFY — DEGRADE, ALL PRE-REGISTERED.** 125000 rescued the parallax carve under camera TRANSLATION but FALSIFIED under ROTATION (0.02 rad), naming TWO coupled fixes: common-fate → AFFINE-FLOW grouping + single-vector → FULL-FIELD efference. This rung BUILT both (ablatable arm flags, no Python fork §0) and ran the 2×2 on Stage A / a rotation sweep / a slant sweep + a post-hoc diagnostic. **RESULT: the rotation carve IS rescued — by ONE fix, applied to a DIFFERENT layer than named.** **FULL-FIELD EFFERENCE, applied as a SEARCH-CENTRE REMAP of the sensor (predictive remapping), extends the tolerated rotation 0.02 → ~0.12 rad (6×): depth-order 1.00→1.00→1.00→0.99→0.90 through rot {0,0.02,0.04,0.08,0.12}, breaks to 0.00 at 0.16.** **THE 2×2 GIVES ALL CREDIT TO EFFERENCE, NONE TO AFFINE: `full_affine==full_cf` AND `single_affine==single_cf` EXACTLY at every rotation — affine grouping changes NOTHING, and HARMS the high-tilt slant (full_affine eff 1.55 vs full_cf 1.01) and perturbs 9/80 translation scenes.** **THE FALSIFY NAMED THE WRONG LAYER: the grouping was never the problem — the SENSOR APERTURE is.** Proven: (1) affine (pure grouping change) rescues nothing; (2) full-field POST-HOC subtraction (V−field, grouping untouched) FAILS (depth-order 0.20/0.00/0.03) because rotation's ~7px flow SATURATES the sensor (radius=block=8) before subtraction; (3) the SAME field applied as a search-centre remap RESCUES — the fix is where the sensor LOOKS. **THE BOUND FALLS OUT of the frame/continuum discretization:** the rotation cancels EXACTLY in the continuous map, but the STEPPED render leaves a ref-band residual ∝ rot·curvature (+0.52→+2.96 measured) that inverts the depth order between rot 0.12 and 0.14 — the rotation twin of 125000's slant √5 break, measured not picked (exact 0.12 is an emergent discretization limit, mechanism-attributed, no closed-form claimed). **STAGE A (translation) — CONFIRM & default preserved: `(single,cf)` byte-identical to 125000 on 80/80; all four arms carve three surfaces (eff 3.09–3.12, depth-order 1.00). STAGE B slant — no worse (full_cf 1.01 at tilt 0.8 vs single_cf 1.15).** WHAT IT GOT WRONG: first applied efference as a POST-HOC subtraction (failed — aperture saturation; kept as the committed diagnostic); expected both named fixes to matter (only efference does; affine inert AND harms slant); nearly reported affine as buggy rather than the wrong layer; affine 71/80 byte-identical on translation (reported, moot — not adopted); onset/bound model-dependent (only the mechanism transfers); the gate caught a real marginal at rot 0.02 (moved to 0.04/0.08). Provenance its OWN step (7 passed, re-verified `16fb14133c30` post-run, `provenance_stable` True, `source_match` `shared` — NO Rust); oracle rung7_vision_bench 222/0 BEFORE and AFTER; own gate `test_parallax_affine_migrated.py` 7 passed (positive-controlled: reproduces the 125000 FALSIFY, proves post-hoc fails, §13 no-tuned-threshold audit); 125000 gate 8 passed (unbroken); loadavg [5.59→5.71], ≤2 workers, wall 78.6 s; engine `16fb14133c30` `shared`. |

---

## 11. NAMED NEXT LEVERS (each its own pre-registration)

1. **REAL 3-D-MOTION VIDEO with measured camera pose** (memory CODEC↔EYE) — the
   last constructed variable is the SCENE geometry; found video over real 3-D
   structure with a real ego-motion sensor retires it, and would test whether the
   efference-as-search-prior mechanism survives a real (noisy, 6-DoF) pose.
2. **SUB-PIXEL / MULTI-RESOLUTION SENSOR to push the discretization bound.** The
   rescue's 0.12-rad ceiling falls out of the STEPPED render (§4). A refinement
   ladder (the memory's INTENSIVE axis — coarse→fine, `space_quantize` depth) on
   the residual would test whether the bound is genuinely the continuum limit or
   just this render's resolution.
3. **≥3 FRAMES / TEMPORAL INTEGRATION** — a single frame pair couples depth and
   the discretization residual; a third frame gives an independent constraint that
   could separate them past 0.12 rad (the FALSIFY branch's named escape, now a
   lever for the DEGRADE's bound).
4. **OCCLUSION / DISOCCLUSION as a depth-ORDER cue** (inherited from 125000) — a
   monocular front/behind signal common-fate velocity alone does not give.
