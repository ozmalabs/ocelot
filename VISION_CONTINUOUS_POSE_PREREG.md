# CONTINUOUS POSE — real-angle rotation as a cross-frame generator, decided by a continuous verdict — pre-registration

*FRONTIER rung T1. The discrete-similarity crossing (`VISION_SIMILARITY_RESULTS.md`)
recognizes identity invariant under the DISCRETE similarity group (integer-lattice
rot90 / reflection / integer uniform scale). Real-angle rotation ALIASES onto that
lattice ("any given circle is stepped"): the similarity path admitted 5/14 rounded
real rotations as lattice coincidences and MINTED the rest as novel — the
identifiability limit the det1 / similarity rungs named and reserved. This rung
extends recognition to CONTINUOUS pose: real-angle rotation is a CROSS-FRAME
generator with a CONTINUOUS parameter θ, applied intensionally (`Rotate`, held) then
RENDERED to the stepped integer lattice (extensional observation), and recognition
decides by a CONTINUOUS VERDICT — the "bins propose, continuous decides" synthesis:
earned discrete quanta propose the identity codebook, a strong continuous geometry
(the held `PointSetDist`) decides. θ lives ONLY in the cross-frame map (the render),
NEVER as an in-frame coordinate — `coord_ints` refusing floats stays correct.*

Committed BEFORE the confirmatory run (§3). Seed block **40000–40999** declared;
**12000–39999 burned** (ledger honoured — the noise floor uses 40000–40099, never
used before; similarity used 39000–39099, det1 38000–38099). Engine provenance
recorded in the RESULTS file (§10). Pinned against base `main` HEAD **d8955f47**
(`git merge-base --is-ancestor d8955f47 HEAD` verified).

## 0. AUDIT — COMPOSE, NO new Rust (§12.4, cited file:line)

**Verdict: COMPOSITION over EXISTING Terms. No `.rs` change.** Continuous-pose
recognition is the held-Term composition the Omniglot AbS path already established
("propose-by-index, RENDER, compare via held PointSetDist / DtwTo, held Argmin"),
transposed from strokes to cell-set point clouds:

- **The render at continuous θ is `Rotate` (already in the engine).**
  `Rotate { vec, angle }` (`runners/dsl/src/term.rs:709`; evaluator `:5858` — `theta =
  angle.as_f64(); (c,s)=(cos,sin); [x·c−y·s, x·s+y·c]`) rotates ONE 2-D point by a
  REAL angle. A point SET is rotated by `MapList`-ing `Rotate` over its points. This
  is the cross-frame map; **θ is a `Float` inside `Rotate`, never a coordinate** — the
  frame invariant, verbatim.
- **The verdict is the held `PointSetDist` (already in the engine).**
  `PointSetDist { a, b }` (`term.rs:545`) — the symmetric Modified Hausdorff distance
  between two point SETS, order-invariant, the exact kernel the Omniglot arc pinned as
  the continuous verdict. Chosen over the affine-absorbing metrics (`DeformDist` /
  `ScTpsDist` / `TpsDeformDist`, `term.rs:572`/`:611`/`:587`) DELIBERATELY: those make
  the whole AFFINE group free (rotation AND shear), which would re-merge the shears the
  similarity rung refused. `PointSetDist` is translation-/order-invariant but NOT
  rotation-invariant, so rotation enters ONLY through the explicit `Rotate` render —
  keeping rotation the sole modelled continuous nuisance (measured superior anyway:
  pilot §3).
- **The decision is composed in the graph** (the DtwTo/PointSetDist precedent: "only
  the distance kernel is Rust; the argmax/argmin DECISION is composed in the graph").
  `covered_by = Attr(Argmin over NodesOfType('ShapeSignature') of MinOver over the
  angle grid of PointSetDist(render, obs.points), 'name')`. `Argmin`/`MinOver`/
  `MapList`/`NodesOfType`/`Attr`/`Sqrt`/`Div` all pre-exist (`term.rs:377`/`:79`/
  `:753`, etc.). **No new Term; no `.rs` edit.**
- **The guard is TWO seed rules in a NEW seed file** (`seeds/continuous_pose.json`,
  gated on a NEW flag `agent.cont_pose`, absent ⇒ OFF ⇒ every committed path
  byte-identical, §9): `cp_recognize` (min-residual ≤ threshold ⇒
  `status=recognized_continuous`, `covered_by=<argmin name>`) and `cp_refuse` (else ⇒
  `cp_refused`). Both require `cont_pose==1` and `status=='cp_decoded'` (a dedicated
  marker the runner sets), so with the flag absent NEITHER fires and the sd loop is
  untouched. **VALIDATED end-to-end via `run_rules` before this commit** (F/T/X at
  37/53/71° each → correct identity; a random blob → `cp_refused`).

Because there is truly **no `.rs` change**, the shared canonical engine is a
legitimate build of this tree's source (§10; `test_engine_provenance_migrated`
green, source `shared`). **No new engine hash: shared-legit.**

The adapter (`scripts/continuous_pose_measure.py`) only: dense-samples the object
codebook, generates rotated-and-rastered observation stimuli (world I/O), sets the
flag + the angle grid, calls `run_rules`, and reads `status`/`covered_by`. **No
Python decision; no covariance; no Hebbian.**

## 1. Objects, resolution, transform, mode

- **Objects** = the SAME 7 full-rank free pentominoes `F,T,U,V,L,N,X` as the wall /
  det1 / similarity rungs. At **resolution s**, each unit cell is dense-sampled as an
  `s×s` block of lattice points (a denser sampling of the SAME shape), centroid-
  centred. `s=1` is the native 5-cell instance resolution of the prior rungs.
- **Observation** = the object dense-sampled at `s`, rotated by a REAL angle θ (about
  the centroid), each point ROUNDED to the nearest integer lattice cell (the
  extensional, in-frame-INTEGER observation), deduplicated, recentred. The rounding IS
  the stepping the frame invariant demands: the in-frame coordinates are integers; the
  real θ lives only in the cross-frame render.
- **Angle grid** `Θ` = `range(0,360,2)` in degrees (radians on the agent as
  `cp_angles`). **Not tuned:** the grid oversamples the raster equivalence classes —
  halving to 1° gives IDENTICAL recognition (pilot: 0/63 mismatches). The step is a
  resolution of the search, not a fitted parameter (§13).
- **Recognition threshold** = `√2/2 ≈ 0.7071` (`Div(Sqrt(2),2)` as graph data). This
  FALLS OUT of the unit lattice: the maximum Euclidean displacement of any point under
  rounding to the nearest integer cell is `√(0.5²+0.5²) = √2/2`, so the Modified-
  Hausdorff residual of a genuine rotation-of-a-known-object against its own rastered
  observation is `≤ √2/2` BY CONSTRUCTION; a shape that is not a rotation of any
  candidate generically exceeds it. **No tuned constant** — the bound is the lattice's
  own half-diagonal (§13).
- **Mode under test** = `cont_pose=1`. Held/discrete generators are irrelevant here
  (the continuous verdict is a distinct rung); the CRUX arm runs the discrete-
  similarity path (`gen_infer=1, gen_similarity=1`) as the baseline.

## 2. Off by default (§9) — ONE new flag, NEW seed file, no Rust

`cont_pose` absent by default ⇒ every committed path byte-identical (`cp_recognize`/
`cp_refuse` require `cont_pose==1`). This rung commits: a NEW seed file
(`seeds/continuous_pose.json`, 2 rules), one `seed_registry.py` registration, a
runner, a gate, this prereg, a results file, a pinned JSON. **No `.rs` edit** ⇒
shared canonical engine legitimate. §9 off-day = the committed bench unmoved; the sd
orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved; siblings green.

## 3. Hypotheses, statistics, decision rule (two-sided; predictions stated)

The geometric arms are DETERMINISTIC (exact counts over object×angle grids). The
**noise floor** is the prospective seeded arm (seeds 40000–40099, never used).

### THE PREDICTION, STATED IN ADVANCE (§3.7)

**I predict continuous-pose recognition COMPOSES and is RESOLUTION-BOUNDED — the frame
/ continuum invariant made operational.** Reasoning: the continuous verdict renders a
candidate at continuous θ and scores the held `PointSetDist`; at ADEQUATE observational
resolution the true candidate's best-θ residual is the rounding floor (`≤√2/2`) and a
wrong candidate cannot align to within it, so recognition is clean; at the NATIVE
5-cell resolution the pentominoes have too few points and real rotation ALIASES —
distinct shapes reach comparable residuals under free θ, so the verdict sits at the
identifiability FLOOR (~chance). The bound is the RESOLUTION, exactly as the invariant
says ("θ pinned only to observational resolution"). **The crux — discrete errs,
continuous correct — holds at adequate resolution**, because the discrete-similarity
path needs an EXACT lattice similarity that a real angle never provides at ANY
resolution (it mints/aliases), whereas the continuous render recovers it.

**What a NULL would mean (and I would report it as a clean negative, §7):** (a) if the
verdict fails even at high resolution, the composition is inadequate / `PointSetDist`
too weak — report + diagnose, do NOT swap to an affine metric to rescue it (§5); (b)
if the verdict succeeds even at `s=1`, there is no identifiability limit — that would
CONTRADICT the frame invariant and be the more interesting finding; (c) if the aliasing
floor cannot be beaten at ANY tested resolution, continuous pose is not expressible at
this instance scale — a clean negative, reported.

### ARMS (exact pass/fail; predictions from pilots on burned construction)

- **A1 — INVARIANCE.** Each object rotated by real angles (5°…85° step 10, ×7) at
  resolution `s`, → recognized (`recognized_continuous`) with `covered_by == self`.
  Statistic: correct / 63 per `s`. **PASS (headline) iff ≥ 60/63 at the adequate
  resolution `s=4`.** *Prediction: `s=4` → 63/63; `s=3` → ~60/63; `s=2` → ~63/63 on
  the 4-angle grid; `s=1` → ~floor (see A4).*
- **A2 — DISCRIMINATION exact-0.** (i) For every object×angle, the argmin picks the
  TRUE identity (no wrong-id merge). (ii) Pairwise: an untransformed `O_j` presented
  against the full codebook is recognized as `O_j`, 0 spurious. **PASS iff wrong-id
  == 0 at `s=4` AND pairwise clean.** *Prediction: 0 wrong-id at `s≥2`; pairwise 0
  spurious (argmin is relative — the true candidate is the per-observation minimum).*
- **A3 — CONTINUOUS-DECIDES CRUX (the whole point).** On the SAME dense real-rotation
  observations, run the DISCRETE-similarity path (`gen_infer=1, gen_similarity=1`) and
  the CONTINUOUS verdict. Statistic: (discrete_correct, continuous_correct) over a
  shared grid. **PASS iff continuous_correct ≫ discrete_correct at `s≥2`.**
  *Prediction: discrete ≈ 0 (mints all — no exact lattice similarity for a real
  angle; pilot 0/6 at `s=2`), continuous ≈ all (pilot 28/28 at `s=2`). The continuous
  verdict resolves exactly what the discrete codebook mints/aliases.*
- **A4 — IDENTIFIABILITY (§8, the honest bound).** The resolution curve `s=1..4`
  (A1's statistic per `s`), plus the step-invariance check (2° vs 1° grid) and the
  θ-precision note. **REPORTED, not gated** as a pass/fail — it IS the bound.
  *Prediction: `s=1` at the aliasing floor (~14/28 ≈ 50%, NOT beating discrete
  meaningfully); recognition RISES with resolution to ~100% by `s≥2`; the 2°→1° grid
  refinement changes 0 verdicts (step not tuned); θ identifiable only to ~`atan(1/R)`
  at the shape's radius `R` (the invariant's "any given circle is stepped").*
- **A5 — FLOOR (refused, not force-merged).**
  - **Noise:** 100 random 5-cell objects, **seeds 40000–40099**, dense-sampled at
    `s=4`, presented against the 7-object codebook. **PASS iff 0/100 recognized**
    (min-residual > `√2/2` ⇒ `cp_refused`). *Prediction: 0/100 — a random blob is a
    rotation of no candidate, so no θ brings any candidate within the rounding floor.*
  - **Different-shape-at-matching-θ:** covered by A2 (argmin picks true) + the
    threshold. *Prediction: a genuinely different shape is NOT force-merged.*

## 4. BOUNDS (§8) — stated in advance, not overclaimed

INSTANCE-level recognition under CONTINUOUS ROTATION pose (plus the discrete-
similarity group already crossed). The win, IF it holds: **real-angle rotation is
recognized as a cross-frame generator with a continuous parameter, rendered to the
stepped lattice and decided by a held continuous verdict — with the identifiability
bound falling OUT of observational resolution, exactly as the frame/continuum
invariant predicts.** This does NOT claim "object recognition solved." NAMED frontier,
UNCHANGED and explicitly NOT this rung: lighting / appearance; non-rigid deformation;
style; **CATEGORY**-level (vs instance); continuous SCALE / translation pose (only
ROTATION here); the full learned axis-codebook at scale; the failure-mode gates
(McCollough, apperceptive/associative, inversion). The object set is 7 hand-chosen
full-rank free pentominoes; the discrimination claim is over those objects × the angle
grid, not over all shapes. The `s>1` resolutions are denser samplings of the SAME 7
shapes — recovering θ, NOT changing the object identities.

## 5. §9 off-day / sibling gates (verified in RESULTS)

`cont_pose` absent by default ⇒ committed bench unmoved. Sibling gates to stay green:
`test_similarity_migrated`, `test_det1_migrated`, `test_gen_infer_migrated`,
`test_dimension_inference_migrated`, `test_sdloop_vision_migrated` (orbit law
`{2:1,3:2,4:2,6:2,12:4}` unmoved), `test_identity_untangling_migrated`,
`test_engine_provenance_migrated`; broad vision bench 200/0.
