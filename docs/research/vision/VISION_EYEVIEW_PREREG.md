# EYE-VIEW SPLAT RENDER — PRE-REGISTRATION (committed before any faithfulness number)

**Seed block 118000–118999. NO Rust, NO Term, NO seed rule.** This is a MECHANICAL
EMIT-ADAPTER: read the eye's held graph/measurement state, translate to an external
image. The architecture rule explicitly permits it ("Emit — read graph state back out
and translate to external output"). No agent logic, no decision over graph state.

## The boundary this render KEEPS (cite `VISION_SPLATTING_SCIENCE.md`)

Splatting is the **DISPLAY**, not the computation. The splatting adjudication REFUTED
"the brain computes with splats": Claim C (persistent dense internal splat cloud) is
refuted by change-blindness / grand-illusion; Claim B (per-scene residual densification =
foveation) is refuted (cortical magnification is a FIXED gradient + active gaze). So:
**the eye's held state is the graph (the parallax carve); splats render what the eye
HOLDS. This render does NOT claim the eye computes with splats.** It is a faithful
read-out only.

## What the eye HOLDS (recovered by re-running the deterministic seeded carve)

The held state is the parallax rung's carve (116000, `parallax_efference`): a known
self-shift Δ (efference copy) → subtraction → common-fate grouping over the SENSED SAD
field. Primary config: `shifts=[0,3,6]`, `block=8`, `grid=144`, `ref_idx=1` (fixated =
middle plane), `τ=√5` (the sensor's own Otsu-within-aperture tolerance, rung 94000). The
carve is pure numpy (`parallax_char.make_scene/vector_field/group_common_fate`), no engine.

Recovered on the confirmatory seeds (setup characterisation, NOT a faithfulness gate):
`eff_surfaces = 1/Σpᵢ²` rounds to **3** on every seed 116000–116009 (mean 3.118); the
K = round(eff_surfaces) = 3 dominant surfaces carry residual velocities **−3 / 0 / +3**
(the middle = the fixated reference at residual 0 — space constancy); confab rate
(sensed ≠ ground-truth cells) 6.8–8.6% (seed 116000: 8.64%, 28/324 cells); the remaining
cells (5–9 per seed, all at the aperture/wrap edge) are confabulation specks the
participation ratio down-weights — the **residual, which renders as HOLES**.

## The render (mechanical emit)

- **carved surface → ONE anisotropic Gaussian.** mean = spatial centroid (image x,y)
  lifted to `z = residual velocity` (the depth the eye MEASURED, relative to the fixated
  reference at z=0 — NOT an invented metric depth); covariance = the surface's 2nd spatial
  moment (anisotropic: bands are tall thin vertical strips ≈3:1 — NOT isotropised);
  colour = mean HELD LUMINANCE of the surface's cells (grayscale — colour is NOT invented,
  memory: luminance is structure, colour is a sparse sign); opacity ∝ confidence,
  covariance inflated by (1−confidence).
- **confidence** = per-surface velocity coherence = `1 − min(1, R_std/τ)` (R_std = the
  surface's residual-velocity spread, τ=√5). A surface whose cells' velocities scatter
  renders MORE DIFFUSE and MORE TRANSPARENT; a tight surface renders sharp. No picked
  number: the softness scale is the sensor's OWN tolerance τ=√5.
- **un-carved / refused cells (not in the top-K surfaces) → NO SPLAT = a VISIBLE HOLE.**
- **forward numpy splat renderer**: project each 3D Gaussian to the image plane (2D
  projected covariance), alpha-composite front-to-back by z. A few dozen lines, no
  training, no heavy dependency.

## THE FOUR FAITHFULNESS GATES (pre-registered; a beautiful render is a confabulating one)

Each threshold FALLS OUT of the sensor resolution or a null (§13); none is picked.

### Gate 1 — HOLE-PRESERVATION
- **Statistic:** fraction of refused cells whose CENTER lies within the 1σ footprint
  (Mahalanobis ≤ 1 — the Gaussian's OWN defining scale, no picked number) of any surface
  splat, in the reference-pose render.
- **Positive control (the load-bearing test):** a scene with a KNOWN un-carved REGION —
  a contiguous rectangular block of cells assigned to NO surface (removed from the held
  surface set). Report the fraction of that region covered by any splat's 1σ footprint.
- **Decision:** PASS iff the KNOWN-no-data region coverage = **0.0 exactly** (a renderer
  that fills a region the eye does not hold FAILS). The natural interior specks' coverage
  is reported separately, not hidden (an interior speck inside a held surface's extent may
  fall within 1σ — that is honest, not a fill).

### Gate 2 — NO OVER-COMPLETION
- **Statistic:** render-complexity / held-complexity, where complexity = number of
  dominant surfaces `round(eff_surfaces)` recovered by RE-CARVING the rendered velocity
  field; held-complexity = K held surfaces.
- **Positive control:** a SPARSE held state — the FLAT scene (held complexity 1) and a
  1-surface DEPTH scene — rendered and re-carved.
- **Decision:** PASS iff render-complexity ≤ held-complexity on every arm (the render
  never ADDS a surface the eye does not hold). Integer count comparison — no tolerance.

### Gate 3 — ROUND-TRIP FAITHFULNESS (analysis-by-synthesis; the StrokeRender/StrokeQuantize precedent, "render is the inverse of the carve")
- **Procedure:** carve → splats → render the splats back into a per-cell VELOCITY field
  V′ (alpha-composited splat velocities, the exact inverse representation of the carve) →
  RE-CARVE V′ with the SAME `group_common_fate(·, √5)` → recover surfaces → bipartite-match
  to the held surfaces.
- **Statistic:** (a) re-carved dominant-surface count; (b) per-surface IoU (held vs
  re-carved cell sets), restricted to the CARVED (non-hole) cells.
- **Derived tolerance:** the carve's OWN velocity tolerance τ=√5 governs "same surface".
  Because the emit writes each surface's exact modal velocity into its footprint and the
  re-carve is deterministic, the target is the STRONGEST §13 outcome — **exact**:
  count == K == 3 AND mean IoU == 1.0 (tolerance 0, no number) on the carved cells. If the
  Gaussian footprints blend boundary velocities across the −3/0/+3 gaps (gap 3 > √5 keeps
  them separable ONLY if boundaries stay sharp), surfaces MERGE and the gate FAILS — so the
  gate genuinely constrains the covariance/opacity (a prettified, over-broad splat fails).
  Reported: actual count and IoU; any deviation from 1.0 is the honest finding, and the
  fallback derived tolerance is IoU ≥ 1 − hole_fraction (holes are never rendered, so they
  cannot round-trip).

### Gate 4 — PARALLAX / SPACE-CONSTANCY MATCH
- **Procedure:** render across an eye-displacement pose sequence in the efference frame
  (reference subtracted): surface i at eye step d sits at `x_i + d·v_i` (v_i = held residual
  velocity). Extract each surface's centroid per pose.
- **Statistic:** (a) reference surface (v=0) centroid displacement across poses; (b) each
  non-reference surface's displacement per unit d.
- **Decision:** PASS iff |reference displacement| = **0.0 exactly** (space constancy — the
  parallax rung measured the reference residual = 0 exactly) AND each non-reference
  surface's displacement per unit d equals its held residual velocity v_i (exact by
  construction, no number). The render's motion reproduces the eye's input motion.

## Prediction (§3 clause 7, stated in advance)

I predict (~85%): Gate 1 positive control = 0.0 exactly (a splat placed only on held
surfaces cannot reach a region with no surface); natural interior-speck coverage small but
nonzero (right-edge specks abut the near surface). Gate 2 = 1.0 on DEPTH (3→3) and FLAT
(1→1), never >1. Gate 3 count = 3 exactly; IoU = 1.0 or very near, because the −3/0/+3 gaps
(3) exceed √5 and front-to-back opacity keeps boundaries winner-take-all — UNLESS
alpha-blend at a boundary bridges a gap, in which case two surfaces merge and I will report
the merge honestly as a covariance-too-broad finding. Gate 4 reference displacement = 0.0
exactly; near/far displace by ∓3 per unit d. Provisos that could break: (i) the right-edge
hole strip abuts surf 2, so its cells may fall within surf 2's 1σ and inflate the natural
(not the positive-control) coverage — reported, not gated; (ii) if I inflate covariance for
"prettiness", Gate 3 will catch it — that is the gate working.

## §13 / discipline

- Every tolerance falls out: 1σ (Gaussian scale), τ=√5 (sensor tolerance), 0-exact
  (deterministic inverse / space constancy), round(eff_surfaces) (participation ratio),
  confab_rate / hole_fraction (measured nulls). No verdict threshold is picked.
- The ONLY manufacturing knobs are STIMULUS/SENSOR configuration (block, shifts, grid) —
  inherited unchanged from the parallax rung, the independent variable, not a verdict knob.
- NO Rust, NO seed, NO Term. §9 trivially satisfied (oracle unchanged before/after).
- Seeds confined to 118000–118999. Confirmatory renders reuse the parallax rung's already-
  burned seeds 116000+ (the held state is theirs); any fresh randomness (positive-control
  scene construction) uses 118000+.
