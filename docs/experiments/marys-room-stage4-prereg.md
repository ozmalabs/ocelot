# Mary's Room stage 4: looking episodes versus perceived colour properties (PREREGISTRATION)

Committed before the battery runs. The code under test is fixed by the same
commit. Scope and approved decisions are in
`docs/research/marys-room-stage4-scope.md`.

## Question

When the eye's per-exposure state (a *look*) and a perceived surface's colour
property are represented separately and linked by an edge, do they dissociate
the way the two concepts should?

- Looks should change with illuminant, adaptation and viewing.
- Properties should hold, or be explicitly refused, on a surface whose identity
  is fixed without using its colour.
- What does a Mary-style room→release sequence add to the graph?

All claims are about the model. "Look" is the computed `SurfaceLook`, not
phenomenal experience.

## Apparatus (frozen by this commit)

- **Eye:** `domains/photon_eye.py` with flag `retina_2d_cones`. This is a 2-D
  sheet of rod+L+M+S cells and per-cell `RetinalPercept`, built with
  `retinal_layout='uniform'` and driven synchronously. Engine `b6a41e3bbba6`.
- **Scenes:** `domains/spectral_scene.py`. Mondrians are 24×16 cells of
  ColorChecker patches, quantised with `spectral_forward.quantize` (cumulative
  rounding unless stated).
- **Seeds**, all `hard_realtime` and flag-gated OFF by default, written by the
  generators in `tools/`:
  - `surface_segmentation`: luminance Y = L+M linear catch. Neighbours are the
    same surface iff |ΔY| ≤ √(Y_a+Y_b). Min-label flood.
  - `surface_persistence`: identity by cell-set overlap, 2·ov ≥ min(count).
    Ambiguous claims are refused; unmatched surfaces coast.
  - `colour_property`: per-surface mean linear catch on the integer lattice, and
    a frame anchor = per-channel max.
    - Rung 1: von Kries cross-multiplication with the derived rounding-only
      bound.
    - Rung 2: L3b leave-one-out pooled gain, tolerance = the pool's spread.
  - `looking_episode`: `LookingEpisode` per exposure, `SurfaceLook` per matched
    surface, `FieldLook` for a boundaryless field.
  - `look_property_link`: `presents_property` / `presents_unrecognised`.
- **Adapter:** `domains/perceived_surface_world.py`, mechanical only.
- **Boot:** the eye's own substrate, plus the seeds; fixpoint by `run_rules`
  (see `docs/research/engine_substrate/dual-process-starves-unlabelled-rules.md`).

## Already observed during the build (development scene; NOT confirmatory)

The build tests used `standard_mondrian(seed=None)` at 1000 td under E/D65/A,
an adaptation overlay, the eyelid ganzfeld, `swap_patches(2,3)`, translations by
1 and 5 cells, and a 12×6 duplicate-reflectance scene. They observed:

- Identity kept under E→D65 for all patches. Under D65→A the isoluminant pair
  (ids 6, 7) split.
- Rung 1 holds only the anchor surface under D65 and A (1/10, 1/9). Rung 2 holds
  8/10 under D65 and 5/9 under A.
- Neutral looks shift negative after 610 nm adaptation while the checks hold.
- Eyelid: an episode and a field look, with no surface, property or link.
- Swapped surfaces are refused.
- Poisson quantisation fragments the scene (74 segments on one seed).

These are reported as development observations only. The battery below uses
held-out layouts and conditions not run during the build.

## Battery (confirmatory)

**Scenes:**
- held-out layouts `standard_mondrian(seed=k)` for k = 1…8;
- the development layout (seed=None), reported separately and never pooled.

**Levels:** scene_td ∈ {100, 1000}. Quantisation is deterministic unless stated.

| Arm | Sequence (each a fresh world) | Recorded |
|---|---|---|
| B1 constancy | E, D65, A, E | per surface: sid continuity; rung-1 status; rung-2 status; look hue-angle change vs exposure 1 |
| B2 adaptation | scene E; 20 × (scene E + uniform 610 nm overlay, 2000 quanta/cell); scene E | neutral and white surfaces: look rg at exposures 1 and 22; check status at 22 |
| B3 eyelid | `diffuse(filter='eyelid')` under E/D65/A at 1000 and 10⁴ td | counts of LookingEpisode, FieldLook, SurfaceLook, ColourProperty, PropertyCheck, link edges |
| B4 swap falsifier | E, then `swap_patches(a,b)` under E for the two declared chromatic patches with the largest L+M difference in that layout | sids at the swapped locations; their check status; others' status |
| B5 motion | E; translate one declared patch by +1 column per exposure for 4 exposures; then a jump of 6 columns | sid continuity per step; birth + coast at the jump |
| B6 Mary room→release | Room: 6 exposures of an achromatic Mondrian (ColorChecker neutrals 19–24 in the standard geometry; background neutral 5) under E, interleaved with 2 eyelid ganzfelds. Release: 3 exposures of `standard_mondrian(seed=k)` under E | node and edge counts by type after the room and after the release; the set of node TYPES instantiated in each phase |
| B7 Poisson | B1 on layouts k = 1, 2 with Poisson quantisation, seeds 7001–7005 | segment count per exposure; sid continuity; rung-1 and rung-2 status |

## Predictions

- **P1. Identity is colour-free.** In B1, every surface keeps its sid across
  illuminant changes, except surfaces whose luminance boundary with a neighbour
  falls inside the shot-noise criterion under one of the illuminants. Those
  split or merge and are refused, never silently re-bound. In B4, sids follow
  position. In B5, the sid persists through 1-column steps and is reborn at the
  6-column jump.
- **P2. Looks change with viewing.** In B1, the median per-surface look
  hue-angle change E→A is larger than E→D65, and both are larger than 0. In B2,
  neutral and white looks have rg at exposure 22 below rg at exposure 1.
- **P3. Properties hold only within the stated class.**
  - Rung 1 holds on the anchor surface in every frame.
  - Non-anchor rung-1 holds: the fraction at 100 td ≥ the fraction at 1000 td,
    and the fraction under A ≤ the fraction under D65.
  - Rung 2 holds on at least as many surfaces as rung 1 in every condition.
  - In B2, checks hold at exposure 22 (catches are linear) while looks have
    shifted.
  - In B4, swapped surfaces are refused.
- **P4. Episodes without properties.** In B3, every exposure yields one
  LookingEpisode and one FieldLook, and zero SurfaceLook, ColourProperty,
  PropertyCheck and link edges.
- **P5. Release adds instances, not kinds.** In B6, every node type and edge type
  instantiated after release was already instantiated during the room phase.
  Release adds new ColourProperty instances for chromatic surfaces, new
  SurfaceLooks and new `presents_property` edges, and no new types.
- **P6. Robustness.** In B7, Poisson quantisation fragments surfaces: the median
  segment count exceeds the deterministic count. The rung-1 refusal fraction is
  ≥ the deterministic one. This prediction is about a known limitation; it is
  not a success criterion.

A failed prediction is reported as failed. Nothing listed under "Apparatus" may
change after the battery output is seen. A bug fix would require a new commit,
a new prereg amendment, and rerunning the whole battery.

## Not covered (declared deviations from the scope)

- **Common-fate motion identity route.** Not built. B5 tests motion through the
  overlap criterion only.
- **Recall/imagery arm** (a property without a look). The episodic retrieval
  link is not built.
- **Link from ColourProperty to symbolic colour concepts** (`colour_meaning`).
  Not built.
- **Refusal of saturated cells** and **re-acquisition of coasting surfaces**.
  Not built.

## Analysis

- Fractions with Wilson 95% intervals over surfaces, pooled across held-out
  layouts.
- Per-layout counts are also reported.
- Hue angle is atan2(by, rg) of the SurfaceLook, in degrees.
- The development layout is reported separately.
- The results doc must separate confirmatory arms from anything added after
  seeing output.
