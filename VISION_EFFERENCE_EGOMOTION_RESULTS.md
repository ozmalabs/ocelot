# EFFERENCE-COPY EGOMOTION CANCELLATION — RESULTS (block 155000–155999)

**SEED CLAIM 155000-155999: CLEAN** (verbatim `seed_claim.py`, run before the
probe existed; unresolved sinks priced at **573**):

```
$ python3 scripts/seed_claim.py 155000 155999
SEED CLAIM 155000-155999: CLEAN -- no collision DETECTED.
  Scope: 855 files with seed sinks; 573 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**Engine.** `engine 64dbce1e7f47 @ .../runners/dsl/python/substrate_rs/_native.abi3.so`
— `source_match == shared`, source fingerprint `3a66c0636a98…` (identical Rust
source to the canonical tree; **NO Rust added, new files only**). Same
fingerprint as 152000–154000.

**Oracle (`bash scripts/rung7_vision_bench.sh`, `data/` symlinked):**
BEFORE = **222 passed / 0 failed**; AFTER = **222 passed / 0 failed** (both
recorded below). New files only ⇒ the shipped carve/physics path is byte-identical
by construction.

**Branch:** `gamma-substrate/efference-egomotion` (worktree under
`research/.claude/worktrees/efference-egomotion`, NOT merged).

---

## The capability (general, not Doom support)

Active inference / sensory attenuation: an agent predicts the sensory
consequences of its OWN actions via an **efference copy** (a forward model of
its motor command), CANCELS them, and the RESIDUAL is the world / the other.
Applied to vision under **egomotion** (self-turning): predict the optic flow the
turn causes (`E_pred = gain × turn_command`, ~uniform because pure rotation is
depth-independent), cancel it, and the residual isolates INDEPENDENTLY-MOVING
world objects; the view-fixed ≈zero-observed-flow region is the agent's own
**apparatus** (self). ONE self-prediction mechanism → (a) world/object carving
under egomotion, (b) static-background separation, (c) self-apparatus
identification.

The grouping is the EXISTING Rust primitive `segment_motion_and_track`,
byte-for-byte unchanged; the forward model, cancellation, apparatus readout and
gain fit are mechanical sensor transforms (`scripts/efference_egomotion_probe.py`).

---

## H1 — SYNTHETIC mechanism (the ideal oracle): CONFIRM on all three claims

Scene: uniform egomotion `E=(0,6)` + an independent object (own image motion
`(0,-2)`, radius 6) + a view-fixed apparatus band (18 rows). All on ground truth.

| claim | measurement | verdict |
|---|---|---|
| **(i)** residual carve isolates the independent object where RAW fails | RAW object IoU **0.000** → EFFERENCE **1.000** (Δ = 1.00) | **CONFIRM** |
| **(ii)** apparatus identified as self, not a world object | apparatus IoU **1.000**; apparatus carved-as-world-object **0.000**; object mislabeled-apparatus **0.0** | **CONFIRM** |
| **(iii)** static background → residual ≈ 0 | background residual mean **0.0** (exact, integer arithmetic) | **CONFIRM** |

**The RAW carve reports SELF as the world object.** On the same egomotion scene
the uncancelled carve's single "world object" is the APPARATUS (IoU-to-apparatus
**1.000**, IoU-to-object 0.000) — the 152000 weapon-sprite failure, reproduced
on ground truth: a naive relative-motion carve cannot tell the view-fixed self
from an independently-moving world object; both are "figures" relative to the
egomotion background.

**Able-to-fail guard (the assertion is not vacuous).** On the SAME scene with
the apparatus REMOVED, the RAW carve isolates the object fine (IoU **1.000**).
So the raw failure is CAUSED by the apparatus, not a broken carve.

**Calibrated forward model (grounded, §13).** The turn→flow gain, measured as
the robust median flow over a calibration turn, recovered **(0, 6)** = the true
egomotion EXACTLY. No constant was set.

---

## The honest mechanistic decomposition — WHAT ACTUALLY DOES THE WORK

**For UNIFORM (turning) egomotion, the decisive operation is APPARATUS
IDENTIFICATION+FOLDING, not the flow cancellation per se.** Ablation on the
primary scene:

- efference **with** apparatus folding → object IoU **1.000**;
- efference **without** apparatus folding (cancel egomotion only) → object IoU
  **0.000** — no better than raw.

Why: `segment_motion_and_track` already subtracts the *dominant* flow before
deciding figure/ground, so subtracting a **uniform** egomotion vector changes no
relative contrast and is redundant with the built-in subtraction. What the raw
carve CANNOT do is recognise the view-fixed zero-flow region as SELF: that region
inflates the field's Otsu tolerance (its motion boundary to the flowing world is
large) so the small independent object merges into the background, AND it is
carved as the one salient "world object." The efference loop fixes this by
IDENTIFYING the apparatus (zero observed flow **while the forward model says the
world is flowing**) and folding it into the reference — which requires the
egomotion prediction to know the world flows at all. The cancellation's distinct
contributions are then (iii) exact static-background nulling and self-vs-static-
world disambiguation.

**Scope this honestly:** the flow-cancellation-per-se becomes the load-bearing
operation only under **NON-uniform** egomotion (translation/walking, where the
predicted field is depth-dependent and a wrong uniform estimate leaves a
non-uniform residual). That is the NAMED harder extension (below), not built
here; the prediction is that cancellation-accuracy will matter there because the
residual is non-uniform.

---

## The efference-copy-vs-dominant-flow comparison (the self-grounding point)

On the primary scene, all cancellation vectors isolate the object equally
(object IoU 1.000 for efference / mean / median) — because a uniform shift is
invisible to the relative-motion carve. The self-grounding shows in **accuracy**
and in **the decision that the world is flowing**:

| cancellation source | cancel vector | true = (0,6) | background residual |
|---|---|---|---|
| **efference copy** (agent's own turn) | (0, **6.00**) | exact | **0.0** |
| model-free **median** (robust obs.) | (0, 6.00) | exact | 0.0 |
| model-free **mean** (global-motion comp.) | (0, **4.15**) | biased low by the apparatus | 1.85 |

**The self-grounding is decisive when the view is self-dominated.** With the
apparatus filling **60%** of the view, the observed median flow is **(0,0)** —
an observation-based estimate concludes "the world is not moving" and CANNOT
identify the apparatus (apparatus-ID off; object IoU **0.042**). The
**command-based efference copy** knows the agent turned (gain (0,6) from a normal
calibration turn) → apparatus identified, object isolated (IoU **1.000**). The
prediction comes from the agent's action, so it survives the moment the current
observation is corrupted.

---

## Controls (all pass)

- **No egomotion** (`E=0`): predicted flow 0 → world-flowing FALSE → no
  apparatus fold → residual == observed → carve **byte-identical** to the raw
  carve (asserted equal cell-for-cell); object IoU 1.000 both.
- **Static scene + egomotion**: residual ≈ 0 everywhere → **0** world regions
  carved (residual mean-abs 0.0); the apparatus band is folded, not carved.
- **Moving object + no egomotion**: cancellation is a no-op → **byte-identical**
  carve; object IoU 1.000.
- **Apparatus discrimination**: apparatus identified (IoU 1.000), NOT carved as a
  world object (0.000), and a moving object is NOT mislabeled apparatus (0.0
  overlap).

---

## H2 — DOOM `defend_the_center`, TURNING, ground-truth scored: DEGRADE (diagnosed)

Fixed turn action (`turn_right` every tic), seed **155000**, down=2 (grid
160×120), block 8, labels-buffer GT, 60 enemy-present frames. Forward-model gain
calibrated from a separate identical turning capture.

**The diagnosed cause — egomotion is NOT sensor-visible in this arena.**

| diagnostic | value |
|---|---|
| nonzero-flow fraction under turning | **9%** of cells |
| dominant moving-flow (median over moving cells) | **(0, −1)** — no coherent egomotion |
| calibrated gain (all-cell median) | **(0, 0)** |

`defend_the_center` is a dark circular arena: the far walls are untextured, so
block-SAD finds no gradient to track under rotation (verified up to full
resolution: even at down=1/block=16 only 38% of cells flow, coherent egomotion
≈0.5 px). Turning produces **sparse incoherent flow noise** (a few wall edges,
HUD digits, the enemy), NOT the coherent whole-field flow the uniform-cancellation
premise requires. **There is nothing to cancel.**

**Consequence:** gain (0,0) → world-flowing FALSE → the efference carve is a
**measured no-op**, identical to the uncancelled carve:

| carve | enemy IoU mean (n=60) |
|---|---|
| RAW (uncancelled, 153000's turning baseline) | **0.1450** |
| EFFERENCE (cancel + apparatus) | **0.1450** (identical) |

**The honest inversion:** under a non-flowing background, the ENEMY (the one
close, textured mover) has the highest flow — mean magnitude **4.07** — while the
view-fixed weapon apparatus has **0.41**. So the "world flows, self is fixed"
contrast is *reversed*: the self and the background are both ≈still and the
object is the mover. Apparatus-by-zero-flow correctly does NOT fire (weapon IoU
0.0) because the world is not measurably flowing — exactly the honest behaviour.

**Timing:** raw 156 ms/frame, efference 157 ms/frame at down=2 — NOT real-time vs
Doom's 28.6 ms/frame (consistent with 153000's motion-carve cost; the added
cancellation is arithmetic, ~free). Timing loadavg start (0.31) / end (0.74).

**Verdict:** H2 is a DEGRADE with a fully diagnosed cause, and it CONFIRMS a
scope condition: **egomotion cancellation requires a TEXTURED environment where
turning produces sensor-visible coherent flow.** `defend_the_center` does not
provide it. This is distinct from 154000's sub-pixel *enemy* wall — here the
*egomotion itself* is below the sensor's texture/aperture floor.

---

## Architecture audit (CLAUDE.md — the agent is Rust) — CLEAN

- **No Rust, no seed, no default moved — new files only.** The carve is the
  EXISTING `segment_motion_and_track`, byte-for-byte; the efference carve with
  zero egomotion + no apparatus fold IS the raw carve (asserted in the gate).
  Shipped carve/physics path byte-identical by construction; oracle 222/0 both
  sides.
- **The forward model is a mechanical learned sensor.** turn command → predicted
  uniform flow (calibrated gain × command); cancellation is array subtraction;
  the apparatus zero-flow readout and the gain median are array math — the peers
  of `vector_field` / `divergence_field` / `quantize`. No conditional over graph
  state, no agent decision.
- **VizDoom is a world adapter;** the agent's turn command is a known
  world-adapter fact (the action it issued); the labels buffer is the SCORING
  ORACLE, never fed to the eye.
- **Scoring is set arithmetic (IoU) by POSITION,** never by cross-process
  region-id (headline gate stable across 3 fresh processes).
- **§13:** the gain FALLS OUT of the agent's own calibration turn (measured, not
  set); the zero-flow tolerance is the block-matcher's one-pixel floor; the carve
  tolerance is the existing Otsu; grid/downsample/turn-rate/block are declared
  sensor residuals. Raw distributions reported.

---

## WHAT I GOT WRONG

1. **I expected the flow CANCELLATION to be the load-bearing operation; it is
   not, for uniform egomotion.** Because `segment_motion` already subtracts the
   dominant flow, subtracting a uniform egomotion vector is redundant — the
   ablation (cancel-without-apparatus-fold → object IoU 0.000) proves it. The
   NEW capability the efference loop adds under turning is APPARATUS
   IDENTIFICATION (recognising the view-fixed self and folding it), which
   `segment_motion` cannot do. I re-framed H1 around this honest decomposition
   rather than claim the cancellation did work it did not.
2. **The first synthetic used a noisy fragmenting background that made raw and
   efference fail EQUALLY (both 0.33) — a null, not a demonstration.** Removing
   the noise (an ideal-oracle scene is the right H1) exposed the true mechanism.
   The noisy Doom-faithful regime belongs in H2, not the ideal-oracle H1.
3. **I predicted turning would make the whole Doom scene flow (and cancellation
   would recover the enemy). It does not flow at all.** `defend_the_center`'s
   untextured far walls yield ~no trackable egomotion flow (9% nonzero cells, no
   coherent vector), so cancellation is a measured no-op. The premise failed at
   the sensor, one level below where I expected the wall (I expected 154000's
   sub-pixel *enemy* wall; the *egomotion* is itself sub-texture).
4. **My first `calibrate_gain` used the all-cell median, which the apparatus
   biased toward 0** on the synthetic edge case and returned 0 on Doom. I kept
   the all-cell median for the naive model-free estimate (correctly biased) and
   grounded the efference "is the world flowing?" decision on the COMMAND
   magnitude, not the observation — which is what the efference-copy principle
   actually asserts and what makes the self-grounding edge case separate.

---

## Named extension (not built)

**Translation / walking egomotion (parallax, depth-dependent).** There the
predicted flow is NON-uniform (near objects flow faster than far), so a wrong
uniform estimate leaves a NON-uniform residual and the cancellation ACCURACY
becomes load-bearing for object isolation — unlike the uniform turning case where
it is redundant. Prediction: efference cancellation will materially beat a single
global-motion vector there. Requires a depth-parameterised forward model
(flow ∝ egomotion / depth). Also named: sensing FAST egomotion that exceeds the
block aperture needs the motion-compensated (predictive-center) search
(block 148000) seeded with the efference prediction — the efference copy at the
sensor level; it does NOT rescue the *untextured* wall (no gradient to match
regardless of search center), which is the specific `defend_the_center` failure.

---

## Proposed VISION_PROTOCOL.md ledger row (EXACT style)

| **155000–155999 (efference-copy egomotion cancellation; NO Rust, NO seed — new files only; reuses `segment_motion_and_track` byte-identical, fed the residual flow)** | **THE EFFERENCE COPY SEPARATES SELF FROM WORLD UNDER EGOMOTION — one self-prediction mechanism yields object-carving, static-background separation, AND self-apparatus identification; mechanism CONFIRM synthetic, Doom DEGRADE (egomotion not sensor-visible in the untextured arena).** The GENERAL capability (Doom is only the scored eval), grounded in active inference / sensory attenuation: predict the optic flow of the agent's OWN turn (efference copy), cancel it, the residual is the world; the view-fixed ≈zero-observed-flow region is the agent's own apparatus. **H1 SYNTHETIC (ideal oracle) CONFIRM on all three:** under uniform egomotion + a view-fixed apparatus the RAW carve object IoU **0.000** (and reports the APPARATUS as its one world object, IoU **1.000** — the 152000 weapon-sprite failure on ground truth) → EFFERENCE **1.000** (able-to-fail: raw isolates the object at 1.000 with the apparatus REMOVED); apparatus identified IoU **1.000**, not carved as object; static background residual **0.0 EXACT**; calibrated gain **(0,6) = the true egomotion**, measured from the agent's own turn (§13). **THE HONEST DECOMPOSITION:** for UNIFORM turning the decisive op is APPARATUS IDENTIFICATION+FOLDING, NOT the cancellation — `segment_motion` already subtracts the dominant flow, so a uniform-shift cancellation is redundant (ablation: cancel-without-fold → object IoU **0.000**); the new capability is recognising the view-fixed self (possible only because the forward model says the world flows) — flow-cancellation-per-se becomes load-bearing only under NON-uniform (translation/parallax) egomotion, NAMED not built. **SELF-GROUNDING:** with the apparatus at 60% of view the observed median flow is (0,0) ("world not moving") so a model-free estimate fails (object IoU **0.042**, apparatus not identified); the command-based efference copy knows it turned → object **1.000**, apparatus identified — the prediction comes from the agent's action, surviving a corrupted observation. **EFFERENCE vs DOMINANT:** on uniform egomotion all cancellation vectors isolate the object equally (uniform shift invisible to the carve); the efference gain (0,6) matches the robust median and beats the biased global-motion MEAN (0,4.15) on residual accuracy. **H2 DOOM (`defend_the_center`, TURNING, seed 155000, down=2, labels GT) DEGRADE, diagnosed:** turning yields NO sensor-visible egomotion — **9%** nonzero-flow cells, dominant moving-flow **(0,−1)**, gain **(0,0)** (untextured far walls give block-SAD no gradient; verified to full res) — so cancellation is a MEASURED NO-OP: enemy IoU **0.1450** raw == **0.1450** efference. The honest inversion: the ENEMY is the one textured mover (flow mag **4.07**) while the view-fixed weapon is still (**0.41**), so self-and-background are both ≈still and apparatus-by-zero-flow correctly does not fire. CONFIRMS a scope condition: egomotion cancellation needs a TEXTURED world where turning produces coherent flow — distinct from 154000's sub-pixel *enemy* wall (here the *egomotion itself* is sub-texture). **COST:** 156 ms/frame at down=2 (cancellation arithmetic, ~free), NOT real-time vs 28.6 ms. Controls hold (no-egomotion byte-identical no-op; static+egomotion → nothing carved; moving-object+no-egomotion identical). Architecture audit CLEAN: grouping is the unchanged Rust primitive; forward model/cancellation/apparatus readout are mechanical sensor transforms (no agent decision); VizDoom a world adapter; turn command a known adapter fact; labels buffer the oracle; scored by IoU/position. shared engine `3a66c0636a98` (source_match==shared, NO Rust); oracle **222/0 BEFORE and AFTER**; gate `test_efference_egomotion_migrated` **16/16 across 3 fresh processes** (H1 (i)/(ii)/(iii) able-to-fail; controls; self-grounding; efference-vs-dominant; byte-identity-off; H2 confirm-or-diagnosed-degrade, skips if VizDoom absent). §9 byte-identity — new files only. Raw: `results/efference_egomotion.json`, `results/efference_egomotion_imgs/`; `VISION_EFFERENCE_EGOMOTION_RESULTS.md`. NAMED NEXT: translation/parallax egomotion (non-uniform → cancellation becomes load-bearing); efference-seeded motion-compensated search for fast egomotion. `SEED CLAIM 155000-155999 CLEAN`. |
