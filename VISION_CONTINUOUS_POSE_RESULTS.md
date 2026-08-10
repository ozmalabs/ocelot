# CONTINUOUS POSE — real-angle rotation, cross-frame generator, continuous verdict — RESULTS

*Pre-registered in `VISION_CONTINUOUS_POSE_PREREG.md` (committed BEFORE this run, §3).
Runner `scripts/continuous_pose_measure.py`, gate `tests/test_continuous_pose_migrated.py`,
pinned `results/continuous_pose.json`. Noise floor seeds 40000–40099 (never previously
used; similarity used 39000–39099, det1 38000–38099). Base `main` HEAD **d8955f47**
(`git merge-base --is-ancestor d8955f47 HEAD` verified).*

**Provenance (§10):**
`engine 7d5f50c18673 @ …/runners/dsl/python/substrate_rs/_native.abi3.so
[shared build from …/gamma-substrate — Rust source identical]`. This rung adds **NO
Rust** — continuous-pose recognition is a COMPOSITION over existing Terms (`Rotate` +
`PointSetDist` + `MapList`/`MinOver`/`Argmin`/`NodesOfType`/`Attr`) driven by two new
SEED rules (`seeds/continuous_pose.json`, gated on `agent.cont_pose`, OFF by default).
The shared canonical engine is a legitimate build of this tree's source
(`test_engine_provenance_migrated` green, source `shared` — byte-identical `.rs`).
**No new engine hash: shared-legit, because there is truly no `.rs` change.**

## HEADLINE — the composition CROSSES, and the identifiability bound FALLS OUT of resolution

**Continuous-pose recognition COMPOSES graph-natively — real-angle rotation is
recognized as a CROSS-FRAME generator (`Rotate`, continuous θ) rendered to the stepped
integer lattice, DECIDED by the held continuous verdict `PointSetDist` over a
discrete-codebook proposal ("bins propose, continuous decides") — and its behaviour is
governed EXACTLY by the frame/continuum invariant: θ is pinned to observational
resolution.** At the native 5-cell instance resolution real rotation ALIASES (the
verdict wrong-merges 22/63 — the identifiability floor the det1/similarity rungs
named); at adequate resolution (≥2× denser sampling of the SAME shapes) the verdict
recovers identity cleanly (63/63), the wrong-merges vanish, and the discrete-similarity
path — which needs an EXACT lattice similarity a real angle never provides — cannot
follow (0/14). Every pre-registered prediction held.

- **AUDIT verdict: COMPOSE, no new Rust.** `Rotate { vec, angle }`
  (`runners/dsl/src/term.rs:709`, evaluator `:5858`) applies the real θ; a point set is
  rotated by `MapList`-ing it. `PointSetDist { a, b }` (`term.rs:545`, Modified
  Hausdorff) is the verdict — chosen over the affine-absorbing `DeformDist`/`ScTpsDist`/
  `TpsDeformDist` DELIBERATELY (those free the whole affine group incl. shears; measured
  inferior anyway, §"metric pilot"). `covered_by = Attr(Argmin over
  NodesOfType('ShapeSignature') of MinOver over `cp_angles` of PointSetDist(render,
  obs.points), 'name')`; recognized iff min-residual ≤ `√2/2`. **No `.rs` edit** — the
  vision bench's own no-Python-thresholds scan finds nothing (every knob is graph data).

## RESULTS (mode: `cont_pose=1`, all arms)

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A1 INVARIANCE (s=4)** | correct/63 over 7 obj × angles 5..85 | **63/63**, 0 wrong, 0 refused | ≥60/63 ✓ (63/63) |
| **A2 DISCRIMINATION exact-0** | wrong_id + untransformed | **wrong_id=0, untransformed 7/7 → exact0=TRUE** | exact-0 ✓ |
| **A3 CRUX (s=2)** | discrete vs continuous correct/14 | **discrete 0/14 (all minted), continuous 14/14** | continuous ≫ discrete ✓ |
| **A4 identifiability curve** | correct/63 per scale | **s=1: 41/63 (22 wrong-id); s=2: 63/63; s=3: 60/63; s=4: 63/63** | floor at s=1, recovers ✓ |
| **A4 step 2°==1°** | verdict mismatches | **0/63** | 0 (not tuned) ✓ |
| **A5 NOISE floor** (seeds 40000–40099) | force-maps/100 | **0/100** | 0/100 ✓ |

## The three questions the task demanded, ANSWERED by measurement

**1. Does the continuous verdict resolve what the discrete codebook aliases/mints (the
CRUX)?** YES, cleanly. On the SAME dense rounded real-rotation observations (s=2), the
discrete-similarity path (`gen_infer=1, gen_similarity=1`) recognizes **0/14** — it
MINTS every one as novel (`status=minted, covered_by=None`), because a real angle
(37°/53°) is not an exact integer-linear similarity of any pentomino at ANY resolution.
The continuous verdict recognizes **14/14** correctly (e.g. F@37° → `minted/None`
discrete, `recognized_continuous/F` continuous). The continuous θ, living in the
cross-frame `Rotate` render, recovers exactly the identity the lattice-exact discrete
search cannot express.

**2. Is invariance preserved and discrimination exact-0 at adequate resolution?** YES.
At s=4, every object rotated by real angles 5°…85° is recognized as its own identity
(**63/63**, 0 wrong, 0 refused); the argmin never merges a different shape (`wrong_id=0`),
and every untransformed object is recognized as itself (7/7) → **exact-0 = TRUE**. Noise
(100 random 5-cell blobs, fresh seeds 40000–40099) is REFUSED **0/100** — no candidate,
at any θ, renders to within the lattice half-diagonal of a random blob.

**3. Is θ pinned only to observational resolution (the IDENTIFIABILITY bound, §8)?** YES
— measured directly as the resolution curve:

| resolution `s` | correct/63 | wrong-id merges | reading |
|---|---|---|---|
| **s=1 (native 5-cell)** | 41/63 | **22** | real rotation ALIASES — the identifiability FLOOR |
| **s=2** | 63/63 | 0 | recovered |
| **s=3** | 60/63 | 3 (F@35→T, F@75→X, F@85→X) | near-recovered (F/X residual alias) |
| **s=4** | 63/63 | 0 | clean |

At the native 5-cell instance resolution the pentominoes carry too few points, so
distinct shapes come within the rounding floor (`√2/2`) under free θ and the verdict
wrong-merges 22/63 — **this is the honest negative on the native-resolution arm, the
aliasing limit ("any given circle is stepped") the prior rungs reserved.** Giving the
observation adequate resolution (a denser sampling of the SAME 7 shapes — recovering θ,
NOT changing the identities) recovers identity to 63/63. **The bound is the RESOLUTION,
exactly as the frame/continuum invariant predicts** — θ pinned to what the steps can
support (MDL), no precision beyond the lattice. The angle-grid step is likewise NOT
tuned: refining 2°→1° changes **0/63** verdicts (it oversamples the raster equivalence
classes). The recognition threshold `√2/2` FALLS OUT of the unit lattice (the maximum
rounding displacement), not a fitted constant (§13).

## The metric pilot (WHY `PointSetDist`, not an affine metric) — reported

Under a FREE rotation search at the native 5-cell resolution, every candidate metric is
at the aliasing floor (measured, angles 37°/53°, argmin over all 7 candidates): 
`PointSetDist` 7/14, `ShapeContextDist` 8/14, `DeformDist` 7/14, `ScTpsDist` 8/14,
`TpsDeformDist` 5/14 — margins ≤0.03, i.e. NO metric beats aliasing at s=1 (this is a
RESOLUTION limit, not a metric limit). The affine-absorbing metrics (`DeformDist`/
`ScTpsDist`/`TpsDeformDist`) were rejected on principle regardless: they free the whole
affine group (rotation AND shear), which would re-merge the shears the similarity rung
refused. `PointSetDist` keeps rotation the SOLE modelled continuous nuisance (it enters
only through the explicit `Rotate` render) and, once resolution is adequate, is
sufficient AND cheapest (s=2 → 28/28 in the pilot; s=4 → clean separation, true residual
≤0.42 vs noise ≥0.86). This is NOT metric surgery (§5): the metric was chosen on the
frame-invariant argument + a pre-run pilot, then FIXED; no measure was changed to rescue
a failure.

## BOUNDS (§8) — what is NOT shown

INSTANCE-level recognition under CONTINUOUS ROTATION pose (plus the discrete-similarity
group already crossed). The win, precisely stated: **real-angle rotation is recognized
as a cross-frame generator with a continuous parameter, rendered to the stepped lattice
and decided by a held continuous verdict — graph-natively, no new Rust — with the
identifiability bound falling OUT of observational resolution, the frame/continuum
invariant made operational.** This does **NOT** claim "object recognition solved." NAMED
frontier, UNCHANGED and explicitly NOT this rung: continuous SCALE / translation pose
(only ROTATION here); lighting / appearance; non-rigid deformation; style;
**CATEGORY**-level (vs instance); the full learned axis-codebook at scale; the
failure-mode gates (McCollough, apperceptive/associative, inversion). The object set is
7 hand-chosen full-rank free pentominoes; the discrimination claim is over those objects
× the angle grid, not over all shapes. The `s>1` resolutions are denser samplings of the
SAME 7 shapes. The verdict is a POST-HOC argmin over the discrete codebook, not a joint
proposal-refinement search; at native resolution it wrong-merges (the reported floor).

## §9 off-day / sibling gates

`cont_pose` absent by default ⇒ committed bench unmoved. At engine `7d5f50c18673`:
- new gate `tests/test_continuous_pose_migrated.py` **6/6** (incl. off-by-default: with
  the flag absent NEITHER cp rule fires, the observation keeps its `cp_decoded` marker;
  and the crux: discrete mints a real rotation, continuous recognizes it);
- sibling gates **62 passed / 0 failed together** (`test_similarity_migrated`,
  `test_det1_migrated`, `test_gen_infer_migrated`, `test_dimension_inference_migrated`,
  `test_sdloop_vision_migrated` — orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved,
  `test_identity_untangling_migrated`, `test_engine_provenance_migrated` source `shared`);
- broad vision bench `scripts/rung7_vision_bench.sh` (`data/` symlinked, §10.2):
  **200 passed / 0 failed** — the committed vision bench is unmoved, and its
  no-Python-thresholds scan reports *"(none — every knob is graph data)"* (the
  `cont_pose` knob is graph data).
