# WHAT BINDS THE 0.12-rad ROTATION BOUND? — PRE-REGISTRATION (block 127000-127999)

*Committed BEFORE any confirmatory number. Only EXPLORATORY pilots on
already-burned seeds 116000-116029 have been computed (the §3-clause-3 power
analysis). The frontier rung named by `VISION_PARALLAX_AFFINE_RESULTS.md` §11
lever 2 ("SUB-PIXEL / MULTI-RESOLUTION SENSOR to push the discretization bound").*

## 0. THE INHERITED BOUND AND THE META-LESSON

126000 rescued the rotation carve from 125000's 0.02 rad to ~0.12 rad via
full-field efference applied as a **search-centre remap of the sensor**, and its
2×2 ablation proved the OTHER named fix (affine grouping) contributed **0%** — a
0%-credit arm is a finding. Its standing meta-lesson, which THIS rung applies:
**WHEN A NAMED FIX DOESN'T HELP, ABLATE — THE FIX MAY BE AIMED AT THE WRONG
LAYER.** 126000 attributed the 0.12-rad break to a STEPPED render leaving a
ref-band residual ∝ rot·curvature that inverts the depth order between rot 0.12
and 0.14, and named THREE un-run candidate levers: (a) sub-pixel / multi-res
sensor; (b) efference-remap granularity; (c) ≥3 frames / temporal integration.

The leading hypothesis (§11 lever 2, and the frame/continuum invariant's own
prediction) is that **sub-pixel sensing is the fix**. This rung does NOT assume
it. It first finds WHICH constraint BINDS the bound, then attacks it, expressing
every candidate as an ablatable arm flag (a different SENSOR selected by the
measure script, exactly as 126000's `carve_single`/`carve_full` and
`efference∈{single,full}×grouping∈{cf,affine}` were — measurement-harness code,
NOT agent seed logic; §0 respected: no agent decision moves to Python, the
existing seeds/carve are untouched, byte-identity preserved).

## 1. THE GOVERNING INVARIANT THIS RUNG TESTS

CLAUDE.md: **"non-integer math is CROSS-FRAME, never IN-frame."** In-frame
(the observable render `b`) is INTEGER by construction — grounding is stepped.
Non-integer math (the pose→flow prediction, the SAD verdict, interpolation) is
CROSS-FRAME and MAY be real. Refinement clause: **"pin a continuous parameter
only to observational resolution — never encode precision the steps cannot
support"**; the INTENSIVE refinement axis's unreachable limit is the continuum.
The leading hypothesis predicts a sub-pixel sensor pins rotation FINER and pushes
the bound PROPORTIONALLY to the resolution gain, up to a principled MDL limit
where the render's own steps stop supporting the precision.

## 2. HYPOTHESIS (two-sided; the prediction is in §7)

**H0:** the sub-pixel / multi-resolution SENSOR is NOT the binding lever — pushing
sensor resolution (displacement sub-pixel OR spatial aperture) does not raise the
tolerated rotation above 126000's ~0.12-0.14 rad break.

**H1 (leading):** sensor resolution IS the binding constraint; a sub-pixel /
multi-res sensor pushes the bound higher, proportionally to the resolution gain,
up to an MDL limit set by the render's own step.

Two-sided because a sub-pixel arm could equally **push**, do **nothing**, or
**HARM** (invert earlier) — and 126000's meta-lesson is that a named fix aimed at
the wrong layer changes nothing or hurts.

## 3. THE ARMS (each a SENSOR variant selected by a flag; default OFF / unchanged)

All arms carve depths `[300,10,5]`, base 30, ref=mid, camera translation + a
y-axis rotation `rot`, τ=√5, on REAL BSDS crops (inherited photometry). The
DEFAULT carve (`full_cf` = 126000: integer per-block-centre efference remap +
integer SAD search) is UNCHANGED and byte-identical. New arms:

| arm | sensor change | admissible? | tests lever |
|---|---|---|---|
| **default** (`int_int`) | 126000 full_cf: integer pred @ block-centre, integer SAD | yes (baseline) | — |
| **subpix_sensor** | REAL pred + PARABOLIC sub-pixel refine of the SAD minimum; render INTEGER | yes (cross-frame verdict) | (a) sub-pixel displacement resolution |
| **subpix_render** | INTEGER search, but `b` rendered by LINEAR interpolation (fractional shift) | **NO — DIAGNOSTIC** (observable no longer stepped) | isolates the RENDER step's contribution |
| **finer_block** | block 6 (nw 24) instead of 8; multi-resolution finer aperture | yes | (a) spatial-aperture resolution |
| **percol_remap** | efference remap at per-COLUMN granularity (warp `b` by the known per-column pose), integer then continuous | yes | (b) remap granularity |
| **oracle** | the TRUE per-block-mean displacement `t` minus pred (bypasses the SAD block match) | N/A — upper bound | localizer: is the SENSOR the binding constraint? |

The **oracle** is the credit localizer: if it holds depth order to high rot on a
SINGLE frame pair while every real sensor breaks at ~0.12-0.14, the binding
constraint is the SAD BLOCK-MATCH SENSOR and the single frame pair CONTAINS the
information (refuting the ≥3-frame / entanglement escape). The **continuous
oracle** (per-band mean of `d_col(x) − d_pred_cont(x)`, no sensor) tests whether
depth and rotation are separable in the CONTINUOUS map at all — if it is flat in
rot, there is NO 2-frame entanglement when the pose is known.

## 4. THE STATISTIC (exactly)

Per arm, per rotation `rot ∈ {0.00, 0.04, 0.08, 0.12, 0.14, 0.16}`:
**`depth_order_rate`** = fraction of seeds whose recovered per-band mean residual
orders the three bands as near > ref > far (the depth order that FALLS OUT of
1/Z). Bootstrap 95% CI over seeds (fixed `default_rng(0..999)`, the parallax
rungs' exact `_ci`). Secondary: per-band mean residual (far/ref/near) per arm per
rot, to show WHERE the order inverts. The **bound** for an arm = the rot at which
`depth_order_rate` crosses 0.5 (read off the swept curve, never picked).

**§13 — the bound falls out, not picked:** the inversion rot is where the
measured ref-band residual curve crosses the measured near-band residual curve
(two swept curves crossing — no threshold chosen), and I additionally report the
within-block self-motion variation `rot·d/dx[curv]·block` at the crossing as the
quantity it falls out of (a correspondence-SNR limit, measured).

## 5. n, FIXED IN ADVANCE

**n = 80** confirmatory seeds **127000-127079** (matching 125000/126000).
Power: the pilot on burned 116000-116019 (n=20) shows the decisive contrasts are
near-deterministic — at rot 0.16 every real-sensor arm reads `depth_order_rate =
0.00` while the oracle reads `1.00` (a 0.00 vs 1.00 separation, > any CI at
n≥20); the subpix_sensor arm INVERTS EARLIER than default (0.08 vs 0.14). n=80
gives proportion CIs ≤ ±0.11, far inside these separations. No arm's verdict
depends on a marginal proportion.

## 6. DECISION RULE (the pre-registered discriminator, verbatim from the task)

- **CONFIRM** = the ablation identifies SENSOR RESOLUTION as the binding
  constraint AND sub-pixel/multi-res pushes the rotation bound (0.12 →
  measurably higher) up to a principled MDL limit that falls out. Report push
  factor vs resolution gain and the limit.
- **DEGRADE** = sub-pixel pushes the bound but sub-linearly / early-saturating,
  OR the binding constraint is PARTLY sensor + partly another lever — report the
  split and which lever is load-bearing.
- **FALSIFY (first-class, name the next rung)** = the binding constraint is NOT
  the sensor resolution. If it is 2-frame rotation/depth entanglement (a rotation
  and a depth change producing the SAME 2-frame flow, unresolvable at any
  single-frame-pair sensor resolution), PROVE the entanglement is genuine and
  name the ≥3-frame rung. Do NOT rescue by tuning sub-pixel.

A null (no arm pushes the bound) is a FALSIFY of the leading hypothesis and must
name the corrected binding constraint and its next rung.

## 7. MY PREDICTION, STATED IN ADVANCE (with provisos)

I predict **FALSIFY of the leading (sub-pixel/multi-res) hypothesis**, with a
first-class CORRECTION that the named FALSIFY escape (≥3 frames / entanglement)
is ALSO wrong (~80% confidence, from the burned-seed pilot):

1. **The continuous oracle is FLAT in rot** (far −2.9 / ref 0 / near +3 at every
   rot to ≥0.5) → depth and rotation are perfectly separable in the continuous
   map when the pose is KNOWN. **There is NO genuine 2-frame entanglement.** So
   the ≥3-frame escape is refuted at the information level.
2. **The oracle sensor holds depth order to rot ≥0.5** on a single frame pair →
   the binding constraint is the SAD BLOCK-MATCH SENSOR, and the single frame
   pair CONTAINS the depth-order information.
3. **subpix_sensor does NOT push the bound — it HARMS it** (inverts at ~0.08 vs
   default ~0.14) → displacement sub-pixel resolution is aimed at the wrong
   layer (echoing 126000's affine-grouping 0%-credit / slant-harm).
4. **subpix_render (inadmissible diagnostic) gives the SAME bound (~0.14)** → the
   render's integer steps are NOT the binding constraint.
5. **finer_block is non-monotonic** (block 6 marginal, finer collapses) →
   spatial-aperture resolution does NOT push the bound; it is near-optimal at the
   default.
6. **percol_remap does NOT push the bound** → remap granularity is not the lever.

**Credit assignment prediction:** 100% of the bound is the SAD block-match's
within-block-gradient / large-displacement CORRESPONDENCE bias; 0% to sub-pixel
displacement resolution (harms), 0% render steps, 0% spatial aperture, 0% remap
granularity, 0% 2-frame entanglement (all measured null/negative). **The MDL
limit ~0.12-0.14 rad falls out of the correspondence-SNR crossing** (the within-
block self-motion variation reaching a non-negligible fraction of the between-
band depth residual), NOT the continuum limit and NOT the render step.

**The corrected next rung** (named, not built): a within-block FLOW-MODEL block
MATCH — solving the correspondence jointly with an affine/warp DURING the SAD
(the sensor's block-match objective), which is what recovers the oracle. This is
DISTINCT from 126000's affine GROUPING (post-sensor, 0% credit) and from ≥3
frames (the information is already in one pair). NOT sub-pixel.

**Provisos that would break the prediction:** if subpix_sensor or finer_block
DOES push `depth_order_rate` measurably above default at rot 0.16 (→ DEGRADE/
CONFIRM); if the continuous oracle is NOT flat in rot (→ genuine entanglement,
the ≥3-frame escape stands, my refutation is wrong); if the oracle sensor itself
inverts at some rot (→ the constraint is not the sensor). Each is a checkable
prediction the confirmatory run can falsify.

## 8. EXACTLY THE LISTED TESTS

The six arms of §3 on the rotation sweep {0,0.04,0.08,0.12,0.14,0.16}, the
continuous-oracle flatness check, and the byte-identity of the DEFAULT carve to
126000's full_cf, on fresh 127000-127079. No sweeps beyond the listed rots (the
pilot's 0.20-0.50 extension was EXPLORATORY on burned seeds, to confirm the
oracle holds — not re-run confirmatorily). No parameter search. A further attempt
needs a NEW pre-registration.

## 9. §3 CLAUSE 8 — check_claim FOR 127000-127999 (verbatim, unknown_sinks priced)

`python scripts/seed_claim.py 127000 127999`:

```
SEED CLAIM 127000-127999: CLEAN -- no collision DETECTED.
  Scope: 833 files with seed sinks; 543 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Reads CLEAN because the confirmatory seeds are drawn by `range(127000, 127080)`,
a `range` the static tool does not resolve to integers (the disclosed CLI blind
spot). `seed_audit` on the confirmatory measure script's `unknown_sinks` is
recorded in the RESULTS doc after the script is written (the loop-var /
`default_rng(sd)` CLI blind spot), none outside the block; 543 unresolved sinks
tree-wide (counted, not discarded). Confirmatory `range(127000,127080)`; pilots
on BURNED 116000-116029; bootstrap CIs use fixed `default_rng(0..999)`.

## 10. ENGINE / PROVENANCE / ORACLE (§10)

Branch `worktree-agent-ad87babf6ec06c741`; base HEAD `f0abe54236`. **NO Rust, NO
seed** — Term index 181 UNUSED, `NUM_TERM_VARIANTS=181`. Engine resolved
`16fb14133c30` `source_match=shared` (a source-identical build of canonical;
legitimate under §10.1 because this rung adds no Rust); `provenance_line()`
printed from INSIDE the measuring process, `source_match ∈ {own,shared}` asserted
start/mid/end, re-verified after (`provenance_stable`). Provenance gate its own
step (7 passed before AND after). ORACLE `bash scripts/rung7_vision_bench.sh`
(data/ symlinked, §10.2) 222/0 BEFORE and AFTER. ≤2 workers, `os.getloadavg()`
recorded, NO wall-clock verdict.
