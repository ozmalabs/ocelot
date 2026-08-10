# DOES IMAGE-ONLY WITHIN-BLOCK AFFINE MATCHING RECOVER 127000's ORACLE? — RESULTS: **FALSIFY of 127000's own named next rung, ALL PRE-REGISTERED.**

> **THE AFFINE-DURING-MATCH FIX 127000 NAMED DOES NOT RECOVER THE ORACLE — AND
> THE REASON IS NOT THE ONE THE FALSIFY BRANCH GUESSED.** 127000 proved, with a
> ground-truth ORACLE flat in rotation to 0.5 rad, that the depth/rotation
> information is ALREADY in the two-frame pair, blamed the SAD block-match's
> within-block correspondence bias, and named the fix: estimate an AFFINE/WARP
> flow model DURING the match (image-only Lucas-Kanade least squares), instead of
> a rigid `(dx,dy)`. This rung BUILT that sensor and measured it. **The result:
> image-only affine matching does NOT push the rotation bound (stays at rigid's
> 0.12, vs the oracle's 0.5), MAKES the block-mean estimate WORSE than rigid, and
> costs 18.7×.** depth-order rate through rot {0,.08,.12,.16,.20}, n=80 fresh
> seeds 128000–128079:
>
> | arm | 0.00 | 0.08 | 0.12 | 0.16 | 0.20 | bound |
> |---|---|---|---|---|---|---|
> | **rigid (DEFAULT = 127000 int_int)** | 1.00 | 0.99 | 0.89 | 0.00 | 0.00 | **0.12** |
> | **affine_match** (image-only LK) | 0.99 | 0.99 | 0.78 | 0.25 | 0.15 | **0.12 — NO push** |
> | **oracle** (true block-mean) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **≥0.20 (holds to 0.5)** |
>
> **CREDIT: the affine MODEL does NOT recover the oracle; the binding constraint
> is the image-MATCH OBJECTIVE, not the rigidity of the motion model and NOT
> block-scale identifiability.** Proven three ways: (1) the affine's block-mean
> error EXCEEDS the rigid's at EVERY rotation (est_err aff 0.38→4.31 vs rig
> 0.30→3.40) — the extra DOF add bias, not accuracy; (2) the blocks are
> WELL-CONDITIONED at every block size (tt_eigmin 789–1454 at block 8; > 250 even
> at block 6) — the aperture problem does NOT re-appear inside the fit, so the
> H0 identifiability clause is REFUTED; (3) initialised AT the true block-mean the
> fit DRIFTS AWAY from it (affine drift 0.23→2.28 px, > the translation drift on
> the same blocks) — **the intensity-match objective's MINIMUM is displaced from
> the true block-mean under rotation, and a richer per-block motion model within
> the same objective inherits and amplifies the bias.** The affine's ONLY
> measurable effect is a sub-bound, CI-separated graceful-degradation edge past the
> rigid break (rot 0.16: 0.25 [0.16,0.35] vs rigid 0.00) — real, but **below 0.5
> (no bound push), and it appears at LARGE blocks too, at 18.7× the rigid compute.**
>
> **DEFAULT preserved (§9):** rigid is BYTE-IDENTICAL to 127000 int_int AND 126000
> full_cf on 80/80 seeds. **NO Rust, NO seed, Term index 181 UNUSED** — a
> measurement extending the parallax carve, exactly as 125000/126000/127000 were.

*Pre-registration `VISION_PARALLAX_AFFINE_MATCH_PREREG.md`, committed **`4c3263d47e`**
BEFORE any confirmatory number (only EXPLORATORY pilots on already-burned seeds
116000–116029 had been computed). Nothing in it was edited after the first
confirmatory number.*

## ENGINE PROVENANCE (§10)

- Branch **`worktree-agent-ad4be9b7f252c19e3`**; base HEAD **`59a7e1320d`**. Prereg
  commit **`4c3263d47e`**.
- Engine **`16fb14133c30`**, `source_match` **`shared`** — a source-identical build
  of canonical (verified from INSIDE the measuring process via `provenance_line()`;
  **THIS RUNG ADDS NO RUST**, so a shared build is legitimate §10.1).
  `NUM_TERM_VARIANTS=181`, Term enum index 181 UNUSED.
- `provenance_line()` printed into `results/parallax_affine_match.json`;
  `source_match ∈ {own, shared}` asserted start/mid/mid2/end (**never a literal
  build hash**, §10.1); read back **`shared`**. Re-verified AFTER: unchanged
  (`provenance_stable == True`, asserted in the artifact).
- Migrated provenance gate as its OWN step: **7 passed** (before AND after).
- **ORACLE `bash scripts/rung7_vision_bench.sh` (data/ symlinked, §10.2):** BEFORE
  **222 passed / 0 failed**; AFTER **222 passed / 0 failed** (§9 trivial — no Rust,
  no seed, no edit to any committed file; new scripts + new gate only).
- **LOAD:** `os.getloadavg()` in the artifact — start `[6.05, 6.37, 5.69]`, end
  `[7.30, 7.19, 6.88]` (machine shared with concurrent agents); wall **1192.2 s**,
  n=80 (the drift-from-truth diagnostic runs an LK per block twice per seed×rot —
  the expensive part; the SENSOR itself is 0.37 s/frame). ≤2 workers
  (`OMP_NUM_THREADS=2`). **No wall-clock quantity is a verdict** — every statistic
  is a bootstrap over the 80 seeds or an exact/counted quantity; the compute cost
  below is a MEASURED quantity (data), not a verdict.
- **SEED CLAIM 128000–128999 (verbatim, §3 clause 8 — in the prereg, committed
  before any confirmatory number):** reads CLEAN. `seed_audit` reports
  **`unknown_sinks: 1`** on `parallax_affine_match_measure.py` (the `default_rng(k)`
  bootstrap / `range(128000,128080)` site the static tool does not resolve to
  integers — the disclosed CLI blind spot) and **0 sinks** on
  `parallax_affine_match_char.py` (the char draws no seeds; scene seeding lives in
  `parallax_affine_char.scene`), **none outside the block**; 546 unresolved sinks
  tree-wide (counted, not discarded). Confirmatory `range(128000,128080)`; pilots on
  BURNED 116000–116029; bootstrap CIs use fixed `default_rng(0..999)`.
  `seed_audit --check 128000 128999` on both scripts: `ok: true, outside: []`.

---

## 1. THE 127000 BOUND AND THE ORACLE'S 0.5, RE-EARNED IN-TREE (the bracket)

The DEFAULT arm `rigid` (integer per-block-centre efference remap + integer SAD) is
**byte-identical to 127000's `int_int` AND to 126000's `full_cf` on all 80 seeds**
(ref-band residual match < 1e-12 / < 1e-9). Under it the 127000 rotation bound
reproduces exactly: depth-order rate **1.00 (rot 0) → 0.99 (0.08) → 0.89 (0.12) →
0.00 (0.16)**, **bound 0.12** (the broken end of the bracket). The **oracle** (true
per-block-mean, bypassing the block match) holds **1.00 at every swept rot to 0.20**
and **1.00 at rot 0.30 and 0.50** on burned seeds (the achievable-if-you-knew end).
**Bracket: broken 0.12 ↔ achievable 0.5** — exactly 127000's, re-earned.

## 2. THE ABLATION — CREDIT ASSIGNED (the headline)

`depth_order_rate` (fraction of 80 seeds ordering near>ref>far), bootstrap 95% CI:

| arm | lever tested | rot 0.12 | rot 0.16 | rot 0.20 | bound | verdict |
|---|---|---|---|---|---|---|
| rigid (default) | — | 0.89 [0.81,0.95] | 0.00 [0,0] | 0.00 | 0.12 | baseline |
| **affine_match** | affine flow DURING match | 0.78 [0.69,0.86] | **0.25 [0.16,0.35]** | 0.15 [0.07,0.23] | **0.12** | **NO push** |
| **oracle** | true block-mean (localizer) | 1.00 | **1.00** | 1.00 | ≥0.20 | binding is the SENSOR/objective |

**CREDIT ASSIGNMENT:**
- **affine_match's bound = rigid's bound = 0.12** — image-only affine matching does
  NOT tolerate a rotation the rigid cannot. **Push factor 1.0×** toward the oracle's
  0.5. The leading hypothesis (H1) is FALSIFIED.
- **affine_match's ONLY effect is a sub-bound, CI-separated graceful-degradation
  edge:** at rot 0.16 it reads 0.25 [0.16,0.35] where rigid reads 0.00 [0,0] (CIs
  disjoint — a REAL effect), and 0.15 [0.07,0.23] at 0.20. It is not inert. But
  **0.25 < 0.5**, so it is not a bound push and is nowhere near the oracle's 1.00.
  It also mildly HARMS at rot 0.12 (0.78 vs 0.89 — CIs touch, ~equal).
- **oracle holds to 0.20 (and 0.5 on burned) where every real sensor reads 0.00** —
  the binding constraint is the SENSOR, and (§4) specifically its match OBJECTIVE.

## 3. THE BLOCK-SIZE ABLATION — the push is NOT a block-size effect either

`depth_order_rate` at rot 0.12 / 0.16, per block size (n=80):

| block | rigid 0.12 | affine 0.12 | rigid 0.16 | affine 0.16 | affine bound |
|---|---|---|---|---|---|
| 6 | 0.82 | 0.81 | 0.00 | 0.31 | 0.12 |
| 8 (default) | 0.89 | 0.78 | 0.00 | 0.25 | 0.12 |
| 12 | 0.25 | **0.45** | 0.00 | **0.41** | 0.08 |
| 16 | 0.12 | 0.24 | 0.00 | 0.23 | 0.00 |

- **No block size lets affine reach a bound past 0.12.** At the block sizes where
  the carve works best (6/8), affine ≈ rigid (bound 0.12 both). At large blocks
  (12/16) affine degrades more gracefully than rigid (0.45 vs 0.25 at rot 0.12; 0.41
  vs 0.00 at rot 0.16) — but the ABSOLUTE rate there is well below the block-8 bound,
  so it is a graceful-degradation edge, not a rescue. **The affine's edge is real at
  large blocks but never pushes the bound — the credit is neither the affine model
  (bound unchanged) nor a block size (best block = smallest, where affine=rigid).**
- **The blocks are WELL-CONDITIONED at every size** (tt_eigmin median > 250 at block
  6, 789–1454 at block 8) — an affine fit is not identifiability-starved at any of
  these scales on textured BSDS. **The FALSIFY is NOT the aperture-inside-the-fit
  the H0 clause guessed.**

## 4. WHAT THE FALSIFY FALLS OUT OF (§13) — THE MATCH OBJECTIVE, PROVEN BY DRIFT-FROM-TRUTH

The mechanism is neither the motion model's rigidity nor identifiability. It is that
the **image-match objective's minimum is displaced from the true block-mean flow.**
Two ground-truth-validation diagnostics (labelled `_diag`, NEVER inputs to the
sensor), n=80:

| rot | est_err rigid | est_err affine | drift(trans) init@truth | drift(affine) init@truth | tt_eigmin | used_aff |
|---|---|---|---|---|---|---|
| 0.00 | 0.30 | 0.38 | 0.05 | 0.23 | 1454 | 0.02 |
| 0.08 | 1.72 | 1.95 | 0.90 | 0.94 | 1224 | 0.03 |
| 0.12 | 2.32 | 2.74 | 1.21 | 1.25 | 1059 | 0.05 |
| 0.16 | 2.98 | 4.09 | 1.29 | 1.74 | 943 | 0.07 |
| 0.20 | 3.40 | 4.31 | 1.59 | 2.28 | 789 | 0.07 |

- **est_err(affine) > est_err(rigid) at EVERY rotation** — recovering the true
  block-mean (an AREA mean, what the oracle uses and what separates depth) is HARDER
  with the affine model, not easier. The extra 4 linear DOF add variance/bias.
- **DRIFT-FROM-TRUTH is the clincher.** Initialise the LK AT the true block-mean and
  it walks AWAY: 0.05→1.59 px (translation) and 0.23→2.28 px (affine, always ≥). The
  optimizer STARTS at the answer and leaves it — so this is NOT a basin/convergence
  failure (my optimizer is sound; at rot 0 the translation drift is 0.05, ~0). **The
  OBJECTIVE's minimum is genuinely off the true mean.** Under rotation `b`'s block is
  a WARPED, partially-decorrelated version of `a`'s — the brightness-constancy /
  SAD minimum lands where the surviving correspondence is, not at the area-mean flow.
- **The affine MDL guard trusts the WRONG signal.** It engages the affine u0 only
  when the affine lowers the WARP (intensity) residual by a real within-block flow
  spread > τ=√5 (used 2–7% of blocks) — but a better intensity fit does NOT mean a
  better block-mean (est_err(affine) is worse WHERE it engages). Fitting the pixels
  better and estimating the mean flow better are decoupled under this objective.

**This is a correspondence-OBJECTIVE limit, measured — NOT the continuum limit
(the oracle proves the info is present) and NOT identifiability (the fit is
well-conditioned).** It is the aperture problem 125000 §7 named, now localized one
level deeper than 127000 placed it: not the RIGIDITY of the block match, but the
brightness-constancy match OBJECTIVE itself, which a richer motion model shares.

## 5. THE IMAGE-ONLY AUDIT (the load-bearing discipline)

The SENSOR (`affine_match_field` and its helpers `_affine_block` / `_lk_refine` /
`_warp_resid` / `_bilinear`) takes ONLY the two frames `a`, `b`, the block size, and
the KNOWN-POSE efference `pred_x` (= `round(efference_field(sc, True))`, EXACTLY what
127000's default sensor uses as its integer search centre). The gate
(`test_sensor_is_image_only`) asserts by `inspect.getsource` that these functions
contain **no** `d_col` / `s_col` / `band_of` / `t` reference and **no** `sc[` scene
indexing. **The `pred_x` is pose, not pixels of `b`; it is not ground-truth image
displacement.** The oracle (`t`) and the est_err / drift diagnostics DO read `t` —
they are labelled upper-bound / validation quantities, never fed to the sensor,
exactly as 127000's oracle is. **If the sensor touched `t` this rung would have
measured nothing;** it does not.

## 6. COMPUTE COST (measured DATA, §13 — a rescue that costs 18.7× would be a degrade worth stating; here there is no rescue)

Per-frame wall time (mean of 20 reps on seed 128000, rot 0.12, block 8):

| sensor | s / frame | ratio to rigid |
|---|---|---|
| rigid (integer SAD) | 0.0197 | 1.0× |
| affine_match (iterative LK per block) | 0.369 | **18.7×** |

The affine match is **18.7× more expensive** than the rigid SAD (an iterative
Gauss-Newton LK with residual backtracking per block, vs one vectorised SAD tensor).
**It buys no bound push and a worse block-mean estimate — 18.7× for a sub-bound
graceful-degradation edge.** (Not a verdict — a measured quantity the next rung must
weigh.)

## 7. WHICH REGISTERED OUTCOME OCCURRED

| criterion | measured | outcome |
|---|---|---|
| affine bound > rigid, CI-sep, toward 0.5 | bound 0.12 = 0.12; push 1.0× | **NOT CONFIRM** |
| pushes short of 0.5 / block-size / compute | bound NOT pushed at any block; sub-bound edge only | **NOT DEGRADE (bound unmoved)** |
| bound ≤ rigid AND no oracle recovery; prove mechanism | bound = rigid; est_err worse; well-conditioned + drifts from truth → OBJECTIVE, not identifiability | **FALSIFY (first-class)** |

**⇒ FALSIFY of 127000's own named next rung.** Image-only within-block affine
matching does not recover the oracle: it does not push the bound (0.12→0.12), makes
the block-mean estimate worse, and the binding constraint is the match OBJECTIVE
(its minimum is off the true block-mean under rotation — proven by drift-from-truth
on well-conditioned blocks), NOT the rigidity of the motion model and NOT the
block-scale identifiability the FALSIFY branch first guessed. My prereg prediction —
FALSIFY, bound unmoved, est_err(affine) > rigid, well-conditioned, drift-from-truth
> 0 — held in every particular, including the correct H0 clause (objective, not
identifiability).

## 8. WHAT I GOT WRONG — in full

1. **I FIRST HYPOTHESISED THE BIAS WAS SIMPLE CONTRAST-WEIGHTING — AND A PROBE
   REFUTED IT.** I nearly wrote a decisive mechanism claim ("the match returns a
   contrast-weighted mean of the true flow, not the area mean"). I built the probe
   (`|rigid − contrast-weighted-mean|` vs `|rigid − unweighted-mean|`): the rigid
   estimate is EQUIDISTANT from both (marginally closer to UNWEIGHTED). The clean
   story was false; the bias is not simple gradient-weighting. I dropped the claim
   and report only what drift-from-truth proves (the objective's minimum is off the
   true mean, mechanism-attributed, no closed form).
2. **MY FIRST AFFINE LK DIVERGED on depth-boundary blocks** — initialised AT the true
   mean at rot 0 it drifted **51.8 px** (a few boundary blocks where no affine flow
   matches the depth STEP, and the linear terms overshoot). The init-at-truth
   diagnostic CAUGHT it. I added residual BACKTRACKING (accept a step only if it
   lowers the warp residual — robust, no tuned constant); the drift fell to 0.86 and
   the SENSOR result was unchanged, but the raw LK was genuinely unstable.
3. **HYBRID INIT ALONE (rigid coarse → affine) HARMED at low rot before I added the
   MDL guard** — the affine linear DOF overfit noise where no gradient justifies them
   (the exact pattern 126000's affine GROUPING showed on the slant). I added the
   flow-spread MDL guard (`affine_group`'s rule, inherited τ=√5) so affine reduces to
   translation when no ramp is present. I explored efference-init / hybrid-init /
   guard / no-guard as first-class variants, not a single lucky configuration.
4. **THE INHERITED CORRECTION — 127000's NAMED NEXT RUNG WAS WRONG.** 127000 named
   "within-block flow-model match recovers the oracle" as its corrected next rung
   (its own §9 lever 1). This rung REFUTES it: the affine-during-match does NOT
   recover the oracle. This is the FOURTH correction in the chain (125000 grouping →
   126000 aperture → 127000 render-step→correspondence → 128000
   correspondence→OBJECTIVE-misspecification). "The info is in the frame pair"
   (127000, geometric/oracle) does NOT imply "the info is recoverable by minimising
   an image-match objective on the pair" — that gap is the real binding constraint,
   and I inherited 127000's optimism about it in H1.
5. **THE MDL GUARD'S CRITERION IS DECOUPLED FROM THE GOAL.** The guard engages affine
   when it improves the intensity fit — but a better intensity fit does not mean a
   better block-mean (est_err is worse where it engages). I report this as a
   first-class limitation of the guard, not a tuning knob to fix.
6. **THE ONSET / BOUND IS MODEL-DEPENDENT (inherited from 125000–127000).** The
   simplified 1-D pinhole curvature; only the mechanism (the match OBJECTIVE binds;
   affine does not recover the oracle; well-conditioned not identifiability) is
   claimed to transfer, not the exact 0.12 onset.

## 9. WHAT IS NOT SHOWN (§8)

- **NOTHING SAYS THE SURFACES ARE OBJECTS** (inherited): the depth surfaces are the
  depth planes by construction.
- **THE FALSIFY IS SCOPED TO AFFINE FLOW-MODEL MATCHING VIA LK LEAST SQUARES** —
  exactly what 127000 named. A FUNDAMENTALLY DIFFERENT estimator (not
  brightness-constancy least squares — e.g. a robust/segment-aware matcher modelling
  the depth STEP, phase correlation, or a mutual-information objective) is NOT tested
  and is not ruled out by this rung; only the named per-block affine model is.
- **THE ORACLE IS A LOCALIZER, NOT A CAPABILITY** (inherited): it is fed the TRUE
  per-block-mean. It proves the binding constraint is the sensor/objective and the
  frame pair holds the info — it does NOT demonstrate an achievable sensor at 0.5.
- **THE BOUND / ONSET IS MODEL-DEPENDENT** (simplified 1-D pinhole curvature; depths
  [300,10,5], base 30); only the mechanism transfers.
- **STILL SIMULATED PROJECTION — REAL PHOTOMETRY + REAL PROJECTION, SYNTHETIC SCENE
  GEOMETRY** (inherited from 125000–127000): real BSDS pixels + real perspective
  projection; the SCENE geometry (fronto-parallel planes, one aperture family, N≤3)
  and the camera pose are constructed. **The honest sim-vs-real boundary:** the
  correspondence-objective limit is REAL geometry — a brightness-constancy match on a
  rotation-warped block lands off the area-mean on ANY imagery, and the oracle vs
  affine gap would appear on found video too. But the exact 0.12 onset and the
  specific drift magnitudes are properties of THIS render + block + pose model, and
  genuine found 3-D-motion video with a measured 6-DoF pose remains the deferred
  variable.
- **NO TIMING CLAIM.** The compute cost (§6) is measured DATA, not a verdict; every
  depth-order statistic is a bootstrap over the 80 seeds or exact/counted.

---

## 10. LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **128000–128999 (confirmatory 128000–128079 + pilots on BURNED 116000–116029; unknown_sinks 1 measure + 0 char — the `range()`/`default_rng(k)` CLI blind spot, none outside block; NO Rust, NO seed, Term index 181 UNUSED / NUM_TERM_VARIANTS=181 — a measurement extending the parallax carve)** | **DOES IMAGE-ONLY WITHIN-BLOCK AFFINE MATCHING RECOVER 127000's ORACLE? — FALSIFY of 127000's own named next rung, ALL PRE-REGISTERED.** 127000 proved (ground-truth oracle flat in rot to 0.5) the depth/rotation info is IN the two-frame pair, blamed the SAD block-match's within-block correspondence bias, and named the fix: estimate an AFFINE/WARP flow model DURING the match (image-only Lucas-Kanade least squares), not a rigid (dx,dy). This rung BUILT that sensor (host-side measurement harness, §0 respected — seeds/carve untouched, DEFAULT byte-identical; sensor IMAGE-ONLY — audited, touches only a,b,known-pose pred) and ran the ablation (rigid vs affine_match × block∈{6,8,12,16}) with ground-truth-validation diagnostics. **NO push: rigid bound 0.12 = affine_match bound 0.12** (depth-order rate through rot{0,.08,.12,.16,.20}, n=80: rigid 1.00/0.99/0.89/0.00/0.00; affine 0.99/0.99/0.78/**0.25**/0.15; oracle 1.00 at every rot to 0.20 and to 0.5 burned). **CREDIT: the affine MODEL does NOT recover the oracle; the binding constraint is the image-MATCH OBJECTIVE, NOT the rigidity of the motion model and NOT block-scale identifiability.** Proven: (1) est_err(affine) > est_err(rigid) at EVERY rot (0.38→4.31 vs 0.30→3.40) — the extra DOF add bias not accuracy; (2) WELL-CONDITIONED at every block size (tt_eigmin 789–1454 @block8, >250 @block6) — the aperture does NOT re-appear inside the fit, H0's identifiability clause REFUTED; (3) initialised AT the true block-mean the fit DRIFTS AWAY (affine 0.23→2.28 px, ≥ translation) — the intensity-match objective's MINIMUM is off the true block-mean under rotation. affine_match's ONLY effect is a sub-bound CI-separated graceful-degradation edge (rot 0.16: 0.25[0.16,0.35] vs rigid 0.00) — real but <0.5 (no bound push), present at large blocks too, at **18.7× the rigid compute** (0.369 vs 0.0197 s/frame). Block ablation: no block size reaches a bound past 0.12 (best block 6/8, affine=rigid; large blocks 12/16 affine degrades more gracefully but sub-0.5). **THE FOURTH CHAIN CORRECTION (125000 grouping→126000 aperture→127000 render-step→correspondence→128000 correspondence→OBJECTIVE-misspecification): "the info is in the pair" does NOT imply "recoverable by an image-match objective on the pair".** NEXT RUNG: NOT a richer per-block motion model — a DIFFERENT constraint (≥3 frames / temporal integration as an ESTIMATOR aid though the info is geometrically in two; occlusion/disocclusion depth-ORDER cues; or a segment-aware / non-brightness-constancy matcher modelling the depth STEP). WHAT IT GOT WRONG: first hypothesised simple contrast-weighting (a probe REFUTED it — rigid equidistant from weighted/unweighted); first affine LK DIVERGED on depth-boundary blocks (51.8px init@truth — added residual backtracking); hybrid-init alone harmed low-rot before the MDL guard; inherited 127000's optimism that affine-during-match recovers the oracle (H1, refuted); the MDL guard's intensity-fit criterion is decoupled from block-mean accuracy; onset model-dependent (only the mechanism transfers). Provenance its OWN step (7 passed, re-verified `16fb14133c30` post-run, `provenance_stable` True, `source_match` `shared` — NO Rust); oracle rung7_vision_bench 222/0 BEFORE and AFTER; own gate `test_parallax_affine_match_migrated.py` 10 passed (positive-controlled BOTH ways: tt_eigmin reads ~0 on a degenerate 1-D-gradient block so its large BSDS value is live; a false 'recovers the oracle' claim reddens the pin; image-only source audit; §13 no-tuned-threshold audit); 127000 gate `test_parallax_subpixel_migrated.py` 9 passed + 126000 gate 7 passed (unbroken); loadavg [6.05→7.30], ≤2 workers, wall 1192.2 s (drift diagnostic dominates; sensor 0.37 s/frame); SIMULATED projection (real photometry+projection, synthetic scene geometry) — the correspondence-objective limit is real geometry, the exact onset is model-dependent. |

---

## 11. NAMED NEXT LEVERS (each its own pre-registration)

1. **≥3 FRAMES / TEMPORAL INTEGRATION AS AN ESTIMATOR AID.** 127000 refuted the
   ≥3-frame escape at the INFO level (a single pair holds the depth/rotation
   separation geometrically). But this rung shows the single pair does NOT yield it
   to an image-match OBJECTIVE. A third frame gives an independent correspondence
   constraint that could pin the block-mean the two-frame objective cannot — an
   ESTIMATOR lever, distinct from the (refuted) INFO lever.
2. **A NON-BRIGHTNESS-CONSTANCY / SEGMENT-AWARE MATCHER.** The FALSIFY is scoped to
   the affine LK objective. A matcher that models the depth STEP explicitly (segment
   the block by flow, robust M-estimator, phase correlation, or a mutual-information
   objective) attacks the objective misspecification directly, not the motion model.
3. **OCCLUSION / DISOCCLUSION as a depth-ORDER cue** (inherited) — a monocular
   front/behind signal that does not go through displacement matching at all, so it
   is immune to the correspondence-objective limit this rung localized.
4. **REAL 3-D-MOTION VIDEO with measured 6-DoF pose** (memory CODEC↔EYE) — the last
   constructed variable is the scene geometry + pose; tests whether a real, noisy
   pose changes the correspondence-objective bound.
