# PRE-REGISTRATION — DOES IMAGE-ONLY WITHIN-BLOCK AFFINE MATCHING RECOVER 127000's ORACLE?

*Rung 128000. Committed BEFORE any confirmatory number. Only EXPLORATORY pilots on
already-burned seeds 116000–116029 were computed before this file was committed.
Nothing in this file is edited after the first confirmatory number.*

## 0. WHAT THIS RUNG INHERITS AND TESTS

The rotation chain: 125000 FALSIFIED the parallax carve under camera rotation
(break at 0.02 rad); 126000 rescued it to ~0.12 rad via full-field efference as a
search-centre remap (affine GROUPING contributed 0%); 127000 then proved — with a
ground-truth ORACLE flat in rotation to 0.5 rad — that **the information to
separate depth from rotation is ALREADY IN THE TWO-FRAME PAIR** (no ≥3-frame
escape), and named the binding constraint as **the SAD block-match SENSOR's
within-block correspondence bias**: a block under rotation WARPS rather than
rigidly translates, so a single rigid `(dx,dy)` mislocalizes it. 127000's named
fix (its §9 lever 1): **within-block FLOW-MODEL block matching — estimate an
AFFINE/WARP flow model DURING the match, image-only (Lucas-Kanade least squares,
`v(x,y)=A·[dx,dy]+b` over the block), recovering what the oracle proves is
extractable.** Distinct from 126000's affine GROUPING (post-sensor, 0% credit) and
from 127000's sub-pixel refine of a translation minimum (HARMED).

**THIS RUNG BUILDS that sensor and measures whether it recovers the oracle.**

## 1. HYPOTHESIS (two-sided)

**H1 (127000's prediction):** image-only within-block affine matching pushes the
tolerated rotation bound from 0.12 toward the oracle's 0.5 rad, because the affine
fit models the within-block warp the rigid match cannot.

**H0 / the two-sided alternative:** image-only affine matching does NOT push the
bound — either because the affine fit is unidentifiable at the block scale (the
aperture problem RE-APPEARS inside the fit; textureless / 1-D-gradient blocks can't
constrain `A`), OR because the image-match OBJECTIVE ITSELF (brightness constancy /
SAD) has its minimum displaced from the true block-mean flow under rotation, so a
richer per-block motion model inherits the same bias.

## 2. THE STATISTIC (exactly)

- **Primary:** `depth_order_rate` = fraction of the n confirmatory seeds on which
  the per-band mean residual orders near > ref > far (the exact 127000 statistic),
  per arm, per rotation, with a bootstrap 95% CI (1000 resamples, fixed
  `default_rng(0..999)`). **The BOUND** = the last swept rotation at which
  `depth_order_rate ≥ 0.5` (read off the swept curve, no threshold picked).
- **Credit / mechanism diagnostics** (read GROUND TRUTH `t` — validation /
  upper-bound quantities, NEVER inputs to the sensor, exactly as 127000's oracle
  is): (i) `est_err` = mean |estimated block-mean − true block-mean| for rigid vs
  affine; (ii) `drift_from_truth` = initialise the fit AT the true block-mean and
  measure how far `u0` drifts (translation vs affine); (iii) `tt_eigmin` = smallest
  eigenvalue of the per-block translation structure tensor (the identifiability /
  aperture read — image-only).
- **Compute cost** (DATA, not a verdict, §13): per-frame wall time rigid vs
  affine_match and their ratio.

## 3. ARMS (a SENSOR selected by name; DEFAULT unchanged, §0/§9)

- **rigid** — DEFAULT = 127000 `int_int`: integer per-block efference remap +
  integer SAD argmin. **MUST be byte-identical to 127000 int_int and 126000
  full_cf** (Stage A / rot 0).
- **affine_match** — IMAGE-ONLY within-block affine Lucas-Kanade: coarse
  translation from the rigid integer SAD, then LK-refine translation then the full
  6-param affine (both with residual BACKTRACKING — robust, no tuned constant),
  then an MDL guard (inherited τ=√5, in FLOW units — `affine_group`'s exact rule):
  keep the affine block-mean ONLY if the fitted within-block flow SPREAD exceeds τ,
  else keep the translation mean.
- **oracle** — reused from 127000 (true per-block-mean `t` — the credit LOCALIZER /
  single-pair upper bound; NOT a buildable sensor).
- **BLOCK-SIZE ABLATION:** rigid & affine_match at block ∈ {6, 8, 12, 16} (an
  affine fit needs enough pixels → block scale is an identifiability variable; the
  credit split asks whether any push is the affine MODEL or just the block SIZE).

**IMAGE-ONLY AUDIT (the load-bearing discipline):** the SENSOR
(`affine_match_field`) touches ONLY `a`, `b`, `block`, and the KNOWN-POSE efference
`pred_x` (= exactly what the default sensor uses as its search centre). It NEVER
reads `t` / `d_col` / `s_col` / `band_of`. The gate asserts this by source audit.
The oracle and the est-err / drift DIAGNOSTICS DO read `t` — they are upper-bound /
validation quantities, labelled, never the sensor.

## 4. n, FIXED IN ADVANCE (§3 clause 3)

**n = 80** confirmatory seeds `range(128000, 128080)`, matching the arc
(125000/126000/127000 all n=80). Power: the burned pilot (n=30, 116000–116029)
gives `depth_order_rate` patterns tight enough that arms differ from the oracle
(1.00) by > 0.3 and the affine tracks the rigid within ±0.10 at every rotation;
n=80 gives a proportion CI half-width ≤ ~0.11 at p=0.5 and far tighter near 0/1 —
sufficient to establish bound (in)equality and CI-separate every real-sensor arm
from the oracle. **No re-runs, no sweeps beyond the listed arms/rots/blocks.**

## 5. CONFIRMATORY SEEDS NEVER USED FOR ANYTHING (burned-seed ledger)

Confirmatory block **128000–128079** (headline + block ablation + diagnostics, all
on the same 80 seeds). Pilots on BURNED **116000–116029**. Bootstrap CIs use fixed
`default_rng(0..999)` resampling generators, not scene seeds. Compute-cost timing
reuses seed 128000 (already in the confirmatory block).

## 6. DECISION RULE

- **CONFIRM** = affine_match's bound (block 8 or its best block) EXCEEDS the rigid
  bound, CI-separated, measurably toward 0.5; Stage A translation byte-identical; at
  a stated compute cost. Report the push factor and the new bound.
- **DEGRADE** = affine_match pushes the bound but well short of 0.5, OR only at a
  large block size / large compute cost, OR the push is really a block-size effect
  (rigid at that block already pushes) not the affine MODEL — report the split,
  credit assigned.
- **FALSIFY (first-class)** = affine_match's bound ≤ the rigid bound (no push) AND
  it does not recover the oracle. If so, PROVE the mechanism: exhibit whether the
  failure is (a) block-scale identifiability (aperture inside the fit — low
  `tt_eigmin`, exhibit an unconstrained block), or (b) objective misspecification
  (well-conditioned blocks — high `tt_eigmin` — on which the fit initialised AT the
  true mean DRIFTS away, so the intensity-match objective's minimum is off the true
  mean and the affine DOF do not move it there). Name the next lever accordingly. Do
  NOT rescue by using ground truth or by tuning.

**A null (FALSIFY) is a first-class result** — it corrects 127000's own named next
rung, exactly as 127000 corrected 126000's and 126000 corrected 125000's.

## 7. MY PREDICTION, STATED IN ADVANCE (with provisos)

**I predict FALSIFY.** From the burned pilot: affine_match's bound = rigid's bound =
0.12 (no push toward 0.5); `est_err`(affine) > `est_err`(rigid) at every rotation
(the affine model makes the block-mean estimate WORSE, not better); the blocks are
WELL-CONDITIONED at every block size (`tt_eigmin` ≫ 0 on textured BSDS — so it is
NOT the identifiability the H0 clause first guessed); and the fit initialised AT the
true block-mean DRIFTS away from it (translation and, more, affine) — proving the
image-match OBJECTIVE's minimum is displaced from the true block-mean under
rotation. **The binding constraint is therefore the MATCH OBJECTIVE, not the
rigidity of the motion model and not block-scale identifiability; a richer per-block
motion model within the same objective cannot recover the oracle.** The corrected
next lever is NOT a richer per-block model but a different constraint (≥3 frames /
temporal integration as an ESTIMATOR aid even though the info is geometrically in
two; occlusion/disocclusion depth-order cues; or a segment-aware matcher modelling
the depth STEP rather than a smooth affine).

**Provisos that would break the prediction (and what each would teach):** (a) if
some block size DID push the bound CI-separated → DEGRADE, and the credit is
block-size not the affine model unless affine beats rigid AT that block; (b) if
`tt_eigmin` were LOW and an unconstrained block were exhibitable → FALSIFY by
identifiability (the H0 first clause), a DIFFERENT mechanism than I predict; (c) if
the fit initialised at truth did NOT drift → my objective-misspecification
attribution is wrong and I must find another cause. Being wrong on which clause of
H0 holds tells me which layer actually binds.

## 8. SEED CLAIM 128000–128999 (§3 clause 8, verbatim — committed before any confirmatory number)

```
SEED CLAIM 128000-128999: CLEAN -- no collision DETECTED.
  Scope: 835 files with seed sinks; 545 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Confirmatory draws `range(128000, 128080)` (a `range` the static tool does not
resolve to integers — the disclosed CLI blind spot); pilots on BURNED
116000–116029; bootstrap CIs use fixed `default_rng(0..999)`. `unknown_sinks` on
`parallax_affine_match_measure.py` are the `range()` / `default_rng(k)` loop sites,
none outside the block; the char (`parallax_affine_match_char.py`) has NO seed
sinks. Reported in the results doc.

## 9. ENGINE / PROVENANCE (§10)

- Branch `worktree-agent-ad4be9b7f252c19e3`; base HEAD `59a7e1320d`. **NO Rust, NO
  seed** — a host-side measurement extending the parallax carve (sensor
  construction, exactly as 126000/127000). Term enum index 181 remains UNUSED
  (NUM_TERM_VARIANTS=181); if Rust were needed it would allocate index 181 with the
  NUM bump + `variant_table_covers_the_enum` green — it is NOT needed.
- Engine `16fb14133c30`, `source_match` `shared` (source-identical build of
  canonical; a shared build is legitimate §10.1 as this rung adds NO Rust).
  `provenance_line()` printed from INSIDE the measuring process; `source_match ∈
  {own, shared}` asserted start/mid/mid2/end (never a literal build hash);
  re-verified AFTER (`provenance_stable`). Provenance gate its OWN step, before AND
  after. ORACLE `rung7_vision_bench.sh` 222/0 BEFORE and AFTER.
- ≤2 workers (`OMP_NUM_THREADS=2`); `os.getloadavg()` recorded; NO wall-clock
  verdict (compute cost recorded as measured DATA per §13).
