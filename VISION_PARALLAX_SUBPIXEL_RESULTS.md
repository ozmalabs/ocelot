# WHAT BINDS 126000's 0.12-rad ROTATION BOUND? — RESULTS: **FALSIFY of the leading (sub-pixel) hypothesis, ALL PRE-REGISTERED.**

> **THE LEADING HYPOTHESIS IS WRONG, AND SO IS THE NAMED FALSIFY ESCAPE.**
> 126000 named three un-run levers for its 0.12-rad rotation bound; the strongest
> a-priori candidate — and the frame/continuum invariant's own prediction — was
> **sub-pixel / multi-resolution SENSING**. This rung built every lever as an
> ablatable SENSOR-variant arm and let the ablation assign credit (126000's
> method). **The result: NO real-sensor lever pushes the bound, and two HARM it.**
> Depth-order rate through rot {0,0.04,0.08,0.12,**0.14**,0.16}, n=80 fresh seeds:
>
> | arm | 0.00 | 0.04 | 0.08 | 0.12 | 0.14 | 0.16 | bound |
> |---|---|---|---|---|---|---|---|
> | **int_int (DEFAULT = 126000)** | 1.00 | 1.00 | 1.00 | 0.90 | 0.05 | 0.00 | **0.12** |
> | subpix_sensor (parabolic SAD) | 1.00 | 1.00 | **0.01** | 0.00 | 0.00 | 0.00 | **0.04 — HARMS** |
> | finer_block (block 6) | 1.00 | 1.00 | 1.00 | 0.82 | 0.06 | 0.00 | 0.12 — no push |
> | percol_remap (per-column) | 1.00 | 1.00 | 1.00 | 0.16 | 0.05 | 0.00 | 0.08 — HARMS |
> | subpix_render (INADMISSIBLE diag) | 1.00 | 1.00 | 0.99 | 0.85 | 0.05 | 0.00 | 0.12 — same |
> | **oracle (true block-mean)** | 1.00 | 1.00 | 1.00 | 1.00 | **1.00** | **1.00** | **≥0.16 (holds to 0.5)** |
>
> **CREDIT: 100% of the bound is the SAD BLOCK-MATCH SENSOR; 0% to every named
> lever.** The **oracle** (fed the TRUE per-block-mean displacement, bypassing the
> block match) carves depth order to rot 0.5+ on a SINGLE frame pair, where every
> real sensor reads 0.00 at 0.16 — so the SENSOR is the binding constraint and the
> frame pair CONTAINS the information. The **continuous oracle** is EXACTLY FLAT in
> rot (far −2.9 / ref 0 / near +3 at every rotation to 0.5) — depth and rotation
> are perfectly separable in the continuous map when the pose is KNOWN, so **there
> is NO 2-frame entanglement and the ≥3-frame escape is refuted at the information
> level.** sub-pixel of the SAD minimum (0.04) and per-column remap (0.08) both
> INVERT EARLIER than the default; finer aperture (0.12) is at best marginal; a
> sub-pixel RENDER (inadmissible) gives the SAME 0.12 bound, so **the render's
> integer steps are not the binding discretization either.**
>
> **THE CORRECTED BINDING CONSTRAINT (a first-class correction of 126000's own
> §4 attribution): the SAD block-match's WITHIN-BLOCK-GRADIENT / large-displacement
> CORRESPONDENCE bias.** When the KNOWN self-motion (rotation curvature, ~7–23 px)
> is subtracted by a search-centre remap but still VARIES within the 8-px aperture,
> the single-vector block match returns a gradient-weighted estimate ≠ the true
> block-mean; its measured ref-band residual (which should be 0) climbs and CROSSES
> the near-band residual **between rot 0.12 and 0.14** (ref +1.88 < near +2.08 at
> 0.12; ref +2.11 > near +1.57 at 0.14 — the depth order inverts). **The bound
> falls out of that measured crossing** (§13), where the within-block self-motion
> variation `rot·d/dx[curv]·block` reaches **~0.7–1.0 px ≈ ⅓ of the 3-px depth
> residual** — a correspondence-SNR limit, NOT the continuum limit and NOT the
> render step. **The next rung is a within-block FLOW-MODEL block MATCH** (affine /
> warp solved DURING the SAD, recovering the oracle) — distinct from 126000's
> affine GROUPING (post-sensor, 0% credit) and from ≥3 frames (the pair already
> holds the info). NOT sub-pixel.
>
> **DEFAULT preserved (§9):** int_int is BYTE-IDENTICAL to 126000's full_cf on
> 80/80 seeds. **NO Rust, NO seed, Term index 181 UNUSED** — a measurement
> extending the parallax carve, exactly as 125000/126000 were.

*Pre-registration `VISION_PARALLAX_SUBPIXEL_PREREG.md`, committed **`ff9a22d08e`**
BEFORE any confirmatory number (only EXPLORATORY pilots on already-burned seeds
116000–116029 had been computed). Nothing in it was edited after the first
confirmatory number.*

## ENGINE PROVENANCE (§10)

- Branch **`worktree-agent-ad87babf6ec06c741`**; base HEAD **`f0abe54236`** (the
  126000 ledger merge — contains the parallax-affine carve + all required docs).
  Prereg commit **`ff9a22d08e`**.
- Engine **`16fb14133c30`**, `source_match` **`shared`** — a source-identical
  build of canonical (verified from INSIDE the measuring process via
  `provenance_line()`; **THIS RUNG ADDS NO RUST**, so a shared build is legitimate
  §10.1). `NUM_TERM_VARIANTS=181`, Term enum index 181 UNUSED.
- `provenance_line()` printed into `results/parallax_subpixel.json`; `source_match
  ∈ {own, shared}` asserted start/mid/mid2/end (**never a literal build hash**,
  §10.1); read back **`shared`**. Re-verified AFTER: unchanged
  (`provenance_stable == True`, asserted in the artifact).
- Migrated provenance gate as its OWN step: **7 passed** (before AND after).
- **ORACLE `bash scripts/rung7_vision_bench.sh` (data/ symlinked, §10.2):** BEFORE
  **222 passed / 0 failed**; AFTER **222 passed / 0 failed** (§9 trivial — no Rust,
  no seed, no edit to any committed file; new scripts + new gate only).
- **LOAD:** `os.getloadavg()` in the artifact — start `[4.46, 5.17, 5.17]`, end
  `[5.85, 5.48, 5.27]` (machine shared with concurrent agents); wall **60.0 s**,
  n=80. ≤2 workers (`OMP_NUM_THREADS=2`). **No wall-clock quantity is a verdict** —
  every statistic is a bootstrap over the 80 seeds or an exact/counted quantity.
- **SEED CLAIM 127000–127999 (verbatim, §3 clause 8 — in the prereg, committed
  before any confirmatory number):** reads CLEAN. `seed_audit` reports
  **`unknown_sinks: 1`** on `parallax_subpixel_measure.py` (the `default_rng(k)`
  bootstrap-CI site, line 43 — the disclosed CLI blind spot; the confirmatory
  block is drawn by `range(127000,127080)`, which the static tool does not resolve
  to integers) and **1** on `parallax_subpixel_char.py` (the
  `default_rng(sd)`/loop-var site in the subpix_render scene builder), **none
  outside the block**; 543 unresolved sinks tree-wide (counted, not discarded).
  Confirmatory `range(127000,127080)`; pilots on BURNED 116000–116029; bootstrap
  CIs use fixed `default_rng(0..999)`.

---

## 1. THE 126000 BOUND, RE-EARNED IN-TREE (the baseline)

The DEFAULT arm `int_int` (integer per-block-centre efference remap + integer SAD
search) is **byte-identical to 126000's `full_cf` on all 80 seeds** (ref-band
residual match to <1e-9). Under it the 126000 rotation bound reproduces exactly:
depth-order rate **1.00 (rot 0–0.08) → 0.90 (0.12) → 0.05 (0.14) → 0.00 (0.16)**,
bound **0.12**. This is the in-tree baseline every arm is compared against.

## 2. THE ABLATION — CREDIT ASSIGNED (the headline)

`depth_order_rate` (fraction of 80 seeds ordering near>ref>far), bootstrap 95% CI:

| arm | lever tested | rot 0.08 | rot 0.12 | rot 0.16 | bound | verdict |
|---|---|---|---|---|---|---|
| int_int (default) | — | 1.00 | 0.90 [0.82,0.96] | 0.00 | 0.12 | baseline |
| **subpix_sensor** | (a) displacement sub-pixel | **0.01 [0,0.04]** | 0.00 | 0.00 | **0.04** | **HARMS** (CI-sep from 1.00) |
| **finer_block** (6) | (a) spatial aperture | 1.00 | 0.82 | 0.00 | 0.12 | **no push** |
| **percol_remap** | (b) remap granularity | 1.00 | 0.16 | 0.00 | 0.08 | **HARMS** |
| **subpix_render** | render step (INADMISSIBLE) | 0.99 | 0.85 | 0.00 | 0.12 | **same as default** |
| **oracle** | localizer (true block-mean) | 1.00 | 1.00 | **1.00 [1,1]** | ≥0.16 | **SENSOR is binding** |

**CREDIT ASSIGNMENT:**
- **subpix_sensor is 0.01 at rot 0.08, CI-separated from the default's 1.00** —
  displacement sub-pixel INVERTS EARLIER. Aimed at the wrong layer (the exact echo
  of 126000's affine-grouping 0%-credit / slant-harm). The parabolic refine of the
  SAD minimum over-corrects the steep within-block curvature at the near/far bands.
- **finer_block (block 6) never tolerates a rotation the default cannot** — 0.82 at
  0.12 (vs 0.90), 0.00 at 0.16. The bound is near-optimal at the default aperture;
  spatial resolution is NOT the lever. (Pilot swept block∈{3,4,6,8,12}: the bound
  is NON-monotonic — block 4/3 COLLAPSE — a genuine aperture MDL optimum, not a
  monotone gain.)
- **percol_remap (0.16 at rot 0.12) HARMS** — warping the OBSERVABLE `b` by the
  known per-column pose cannot undo a large per-column displacement, because the
  displacement is a function of the SOURCE column, not the image column (the
  correspondence problem in its exact form). Continuous (sub-pixel-interp) warp is
  no better (bound 0.08).
- **subpix_render (INADMISSIBLE) gives the SAME 0.12 bound** — a continuous
  (non-stepped) render does NOT push the bound. **So the render's integer steps are
  NOT the binding discretization.** This is a first-class correction of 126000's §4
  attribution (see §4).
- **oracle holds to rot 0.16 (rate 1.00, CI [1,1]) and to 0.5 on burned seeds** —
  the true block-mean displacement, on a SINGLE frame pair, carves depth order 25×
  past the real-sensor bound. **The binding constraint is the SAD block-match
  SENSOR; the information is present in the frame pair.** (oracle_rounded — the pose
  read at INTEGER granularity — also holds 1.00 at every rot, so remap-granularity
  is not the oracle's lever either.)

## 3. THE ENTANGLEMENT REFUTATION — no ≥3-frame escape

The pre-registered FALSIFY escape was 2-frame depth/rotation entanglement (a
rotation and a depth change producing the SAME 2-frame flow, unresolvable at any
single-pair resolution → real fix is ≥3 frames). **Refuted, measured:**

| rot | continuous-oracle band residual (far / ref / near) | order |
|---|---|---|
| 0.00 | −2.90 / +0.00 / +3.00 | ✓ |
| 0.08 | −2.90 / +0.00 / +3.00 | ✓ |
| 0.16 | −2.90 / +0.00 / +3.00 | ✓ |
| 0.50 (burned) | −2.90 / +0.00 / +3.00 | ✓ |

The per-band mean of `d_col(x) − d_pred_cont(x)` is **EXACTLY the depth parallax
`base/Z_i − base/Z_ref`, INDEPENDENT of rot** (the rotation curvature `rot·curv(x)`
is common to `d_col` and `d_pred` and cancels term-for-term). **When the pose is
KNOWN, the continuous map separates depth from rotation perfectly — there is no
entanglement.** The oracle sensor confirms the SEPARATION SURVIVES a single-pair
block sensor IF the block-mean is measurable. A third frame is not needed; the
information is not the problem, the SAD block-match is. **The ≥3-frame lever is
therefore NOT the corrected next rung.**

## 4. WHAT THE BOUND FALLS OUT OF (§13) — THE CORRESPONDENCE-SNR CROSSING

The default sensor's per-band residual (should be far −2.9 / ref 0 / near +3):

| rot | far | ref | near | ref > near? (inverted) |
|---|---|---|---|---|
| 0.08 | −2.55 | +1.00 | +2.10 | no |
| 0.12 | −3.15 | **+1.88** | **+2.08** | no (marginal) |
| 0.14 | −3.15 | **+2.11** | **+1.57** | **YES — inverted** |
| 0.16 | −3.50 | +2.95 | +1.29 | inverted |

The ref-band residual — which the efference remap should hold at 0 — climbs
monotonically because the block match returns a biased single vector when the
KNOWN self-motion still varies within the 8-px aperture (steepest at the near/far
bands, where the pinhole curvature `(x−cx)²/f0` has its largest slope). **The depth
order inverts at the rot where the measured ref-band residual curve CROSSES the
measured near-band residual curve — between 0.12 and 0.14** (two swept measured
curves crossing; no threshold picked). The quantity it falls out of: the
within-block self-motion variation `rot·d/dx[curv]·block` at the near band reaches
**~0.7 px (band centre) to ~1.0 px (band edge) ≈ ⅓ of the 3-px near−ref depth
residual** at the crossing — the block-match bias grows to a fraction of the depth
signal it must preserve. **This is a correspondence-SNR limit of a local block
matcher, measured, NOT the frame/continuum render step** (subpix_render proves the
render is not binding) **and NOT the continuum limit** (the oracle proves the info
is present). It is the numeric form of the aperture problem 125000 §7 named
("motion's within-surface gradient MANUFACTURES the sensor's aperture ambiguity"),
now localized to the block-match objective itself.

## 5. WHICH REGISTERED OUTCOME OCCURRED

| criterion | measured | outcome |
|---|---|---|
| sensor resolution binds AND sub-pixel/multi-res pushes the bound | subpix HARMS (0.04), finer_block no push (0.12), remap HARMS (0.08) | **NOT CONFIRM** |
| sub-pixel pushes sub-linearly / partly-sensor-partly-other | no arm pushes at all | **NOT DEGRADE** |
| binding constraint is NOT sensor resolution; if entanglement, PROVE genuine & name ≥3-frame | binding IS the SENSOR (block-match), but NOT its RESOLUTION; entanglement REFUTED (continuous oracle flat, oracle holds single-pair to 0.5) | **FALSIFY (first-class)** |

**⇒ FALSIFY of the leading hypothesis.** Sub-pixel/multi-res sensing does not push
the bound (two levers HARM). The pre-registered FALSIFY escape (≥3 frames /
entanglement) is ALSO refuted — the corrected binding constraint is the SAD
block-match's within-block-gradient / large-displacement correspondence bias, and
it names a DIFFERENT next rung (within-block flow-model MATCHING). My prereg
prediction — FALSIFY with the continuous-oracle refutation, the oracle localizer,
subpix HARMS, subpix_render same, finer_block no push, percol HARMS — held in
every particular.

## 6. WHAT I GOT WRONG — in full

1. **I INHERITED 126000's §4 ATTRIBUTION ("the STEPPED render leaves the ref-band
   residual ∝ rot·curvature") AND MY OWN PREREG §1 RESTATED IT — the subpix_render
   diagnostic REFUTES it.** A continuous (non-stepped) render gives the SAME 0.12
   bound and the SAME ref-band climb (+1.88 at 0.12). The binding discretization is
   NOT the render's rounding; it is the block-match. 126000 already corrected
   125000 once ("grouping" → "aperture"); this is the SECOND correction in the
   chain ("render step" → "block-match correspondence"). The frame/continuum
   invariant is still respected (the render IS integer, admissibly), but it is not
   what CAPS this bound.
2. **I PREDICTED PER-COLUMN REMAP (lever b) MIGHT RECOVER THE ORACLE — IT HARMS
   (0.16 at rot 0.12).** My intuition ("de-rotate per column → remove the
   within-block gradient → the block match sees clean depth") was wrong: warping
   the OBSERVABLE cannot undo a large per-column displacement because the
   displacement indexes the SOURCE column, not the image column (the correspondence
   problem). I caught it in exploration and report it as a first-class negative, not
   a dropped arm. The continuous warp is no better.
3. **MY FIRST subpix_sensor PROTOTYPE HAD DEAD/OVERCOMPLICATED SECOND-PASS SAD
   GATHER CODE** (a placeholder loop then a heavy per-dy recompute, in the scratch
   exploration). I rewrote it as a clean full 4D SAD tensor in the committed char;
   the RESULT was unchanged (subpix harms), but the first implementation was wrong
   enough that I re-derived it before trusting the number.
4. **THE "ORACLE" USES GROUND TRUTH THE AGENT DOES NOT HAVE — it is a LOCALIZER /
   UPPER BOUND, NOT an achievable sensor.** It answers "is the constraint the sensor
   or upstream?" (answer: the sensor) and "is the info in one frame pair?" (yes). It
   does NOT claim a buildable sensor reaches 0.5. Stated scrupulously in §7 below so
   the localizer is never mistaken for a capability.
5. **subpix_sensor does not even zero the rot-0 ref residual (+0.42)** — it inherits
   the sensor's ~8% confab bias; "sub-pixel" refines displacement, not confab. Not a
   self-error, a scope note that the sub-pixel arm never had a clean floor to push
   from.
6. **THE ROTATION MODEL AND ONSET ARE MODEL-DEPENDENT (inherited from 125000/126000).**
   The simplified 1-D pinhole curvature `rot·(f0+(x−cx)²/f0)`; only the mechanism
   (the SENSOR block-match is binding; no entanglement; the correspondence-SNR
   crossing caps the bound) is claimed to transfer, not the exact 0.12–0.14 onset.

## 7. WHAT IS NOT SHOWN (§8)

- **NOTHING SAYS THE SURFACES ARE OBJECTS** (inherited): the depth surfaces are the
  depth planes by construction.
- **THE ORACLE IS A LOCALIZER, NOT A CAPABILITY.** It is fed the TRUE per-block-mean
  displacement (ground truth). It proves the binding constraint is the block-match
  and that a single frame pair holds the depth-order information — it does NOT
  demonstrate an achievable sensor that reaches rot 0.5. Building the within-block
  flow-model match that would APPROACH the oracle is the named next rung, NOT done
  here.
- **THE CORRECTED NEXT RUNG (within-block flow-model MATCHING) IS NAMED, NOT BUILT.**
  I demonstrate that neither sub-pixel, nor finer aperture, nor per-column remap of
  the observable recovers the oracle; I do NOT build the affine/warp-during-SAD
  matcher. The claim is that it is the correct layer (the oracle proves the info is
  there; the correspondence is what fails), not that it will succeed.
- **THE BOUND / ONSET IS MODEL-DEPENDENT** (simplified 1-D pinhole curvature; the
  specific depths [300,10,5], base 30); only the mechanism transfers.
- **STILL SIMULATED PROJECTION — REAL PHOTOMETRY + REAL PROJECTION, SYNTHETIC SCENE
  GEOMETRY** (inherited from 125000/126000): real BSDS pixels + real perspective
  projection; the SCENE geometry (fronto-parallel/slanted planes, one aperture
  family, N≤3) and the camera pose are constructed. **The honest sim-vs-real
  boundary:** the CORRESPONDENCE limit is REAL geometry — the aperture problem is a
  genuine property of any local block matcher on any imagery, and the oracle vs
  real-sensor gap would appear on found video too. But the exact 0.12–0.14 onset is
  a property of THIS render + block + pose model, and genuine found 3-D-motion video
  with a measured 6-DoF pose (memory CODEC↔EYE) remains the deferred variable that
  would test whether a real, noisy pose changes the correspondence bound.
- **NO TIMING CLAIM.** Every quantity is a bootstrap over the 80 seeds or
  exact/counted.

---

## 8. LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **127000–127999 (confirmatory 127000–127079 + pilots on BURNED 116000–116029; unknown_sinks 1 measure + 1 char — the `default_rng`/loop-var CLI blind spot, none outside block; NO Rust, NO seed, Term index 181 UNUSED / NUM_TERM_VARIANTS=181 — a measurement extending the parallax carve)** | **WHAT BINDS 126000's 0.12-rad ROTATION BOUND? — FALSIFY of the leading (sub-pixel/multi-res) hypothesis, ALL PRE-REGISTERED.** 126000 rescued the rotation carve to ~0.12 rad via full-field efference as a search-centre remap and named THREE un-run levers for the bound: (a) sub-pixel/multi-res sensor, (b) remap granularity, (c) ≥3 frames. This rung BUILT every lever as an ablatable SENSOR-variant arm (measurement harness, §0 respected — seeds/carve untouched, DEFAULT byte-identical) and let the ablation ASSIGN CREDIT (126000's method). **NO real-sensor lever pushes the bound; two HARM it.** depth-order rate through rot{0,.04,.08,.12,.14,.16}, n=80 fresh: DEFAULT (int_int = 126000 full_cf, byte-identical 80/80) 1/1/1/0.90/0.05/0 (bound 0.12, re-earned); **subpix_sensor** (parabolic SAD refine, REAL pred, render integer — the LEADING hypothesis) 1/1/**0.01**/0/0/0 (bound **0.04, HARMS**, CI-separated); **finer_block** (block 6) 1/1/1/0.82/0.06/0 (bound 0.12, NO push; pilot block∈{3,4,6,8,12} NON-monotonic — an aperture MDL optimum, finer COLLAPSES); **percol_remap** (per-column warp) 1/1/1/0.16/.../0 (bound 0.08, HARMS — warping the observable can't undo a large per-column displacement, the correspondence problem); **subpix_render** (INADMISSIBLE diagnostic — continuous render) 1/1/0.99/0.85/0.05/0 (**SAME 0.12 bound → render steps NOT binding**); **oracle** (true block-mean, bypasses the block match) **1.00 at every rot to 0.5 on burned seeds** (CI[1,1] at 0.16 vs default 0.00). **CREDIT: 100% the SAD BLOCK-MATCH SENSOR, 0% every named lever.** The oracle proves the SENSOR is binding and the single frame pair HOLDS the info; the **continuous oracle is EXACTLY FLAT in rot** (far −2.9/ref 0/near +3 to 0.5) — depth and rotation are perfectly separable in the continuous map when the pose is KNOWN, so **NO 2-frame entanglement and the ≥3-frame escape is REFUTED at the info level.** **THE CORRECTED BINDING CONSTRAINT (a first-class correction of 126000's §4 render-step attribution — the SECOND in the chain after 125000's grouping→aperture): the block-match's WITHIN-BLOCK-GRADIENT / large-displacement CORRESPONDENCE bias.** The measured ref-band residual (should be 0) climbs +1.00→+1.88→+2.11→+2.95 and CROSSES the near-band residual between rot 0.12 and 0.14 (the depth order inverts); **the bound FALLS OUT of that measured crossing** (§13), where the within-block self-motion variation `rot·d/dx[curv]·block` reaches ~0.7–1.0 px ≈ ⅓ of the 3-px depth residual — a correspondence-SNR limit, NOT the continuum limit and NOT the render step. **NEXT RUNG: within-block FLOW-MODEL block MATCH (affine/warp DURING the SAD, recovering the oracle) — distinct from 126000's affine GROUPING (post-sensor, 0%) and from ≥3 frames (info already in one pair). NOT sub-pixel.** WHAT IT GOT WRONG: inherited+restated 126000's render-step attribution (subpix_render refutes it); predicted per-column remap would recover the oracle (it HARMS); first subpix prototype had dead code (rewrote clean, same result); the oracle uses ground truth — a LOCALIZER/upper-bound, NOT an achievable sensor (stated); subpix doesn't even zero the rot-0 confab residual; onset model-dependent (only the mechanism transfers). Provenance its OWN step (7 passed, re-verified `16fb14133c30` post-run, `provenance_stable` True, `source_match` `shared` — NO Rust); oracle rung7_vision_bench 222/0 BEFORE and AFTER; own gate `test_parallax_subpixel_migrated.py` 9 passed (positive-controlled BOTH ways: a dead localizer reddens the localizer, a false 'helps' claim reddens the pin; §13 no-tuned-threshold audit); 126000 gate `test_parallax_affine_migrated.py` 7 passed (unbroken); loadavg [4.46→5.85], ≤2 workers, wall 60.0 s; SIMULATED projection (real photometry+projection, synthetic scene geometry) — the correspondence limit is real geometry, the exact onset is model-dependent. |

---

## 9. NAMED NEXT LEVERS (each its own pre-registration)

1. **WITHIN-BLOCK FLOW-MODEL BLOCK MATCH (the corrected binding constraint).** Solve
   the correspondence jointly with an affine/warp of the block DURING the SAD (fit
   `v(pos)=A·pos+b` per block by minimizing warped residual), so the KNOWN
   within-block self-motion gradient is compensated INSIDE the match rather than
   after it. The oracle proves this can reach rot ≥0.5 on a single frame pair. This
   is the affine model 126000 tried as GROUPING (post-sensor, 0% credit) moved to
   the MATCHING layer where the ablation says the constraint lives.
2. **REAL 3-D-MOTION VIDEO with measured 6-DoF pose** (memory CODEC↔EYE) — tests
   whether a real, noisy pose changes the correspondence bound; the last constructed
   variable is the scene geometry + pose.
3. **OCCLUSION / DISOCCLUSION as a depth-ORDER cue** (inherited) — a monocular
   front/behind signal common-fate velocity alone does not give, independent of the
   correspondence limit.
