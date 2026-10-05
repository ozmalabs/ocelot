# Scope: separating "looking at red" from "red" in the Mary's Room study

Status: scoping only. Nothing is built yet.

## The distinction

- **LookingEpisode ("what looking at red feels like").** The state of this eye in
  this exposure: `red_green`, `blue_yellow`, intensity, adaptation and onset or
  salience. It is token-level and observer-bound.
- **ColourProperty ("what red feels like").** A colour attributed to a surface,
  held constant across illuminant, intensity and adaptation. It is type-level and
  shareable.
- **A link edge**, from an episode to the property it presents.

The confirmatory study used one vector for both roles. The readings it gives
(illuminant A collapse, adaptation "errors", the eyelid result) are in
`docs/experiments/marys-room-*-exploratory.md` and in the conversation record.
On the 24 reflectances under three illuminants, 71% of the eye's hue-direction
variance comes from the surface and 29% from the viewing conditions (4% main
effect, 25% interaction). Normalising each cone's catch by the in-scene white
(von Kries) lifts hue accuracy under illuminant A from 6/18 to 10/18.

## What already exists

Verified in source unless marked otherwise.

| Need | Existing mechanism | Gap |
|---|---|---|
| Constancy | `seeds/vision_lighting.json`: T3 exact von Kries `SurfaceIdentity` with in-class/out-of-class refusal; L1 real gains; L2 Retinex locales; L3/L3b pooled illuminant; L4 shadow vs reflectance edges. Flag-gated, OFF. | Runs on synthetic integer `ObjSurface` cones, not on GraphEye output |
| Surfaces in one exposure | GraphEye 1-D strip: L/M/S per column; several surfaces plus a white reference fit in one `submit_photons` (as in `scripts/marys_room_red_green.py`) | No neighbour edges; the 2-D sheet is rod-only |
| Episode vocabulary | `PhotonExposure` (deleted on each new exposure); `Agent perceives VisionPercept`; `observer_aperture`; `episodic_working_memory_core` (observed vs recalled provenance) | No durable per-exposure episode node |
| Percept → category link | `ci_assign` (attrs only); `shape_recognition` `geometric_shape` edge; `li_recognize` (attr `lit_id`) | No episode → property edge. `presents_as` is already used by `deformation_beneficiary` with a different meaning |
| Persistent object identity | `feature_identity` (games; position + value matching); `vision_crossframe_identity`; `retinal_carve` (`VisionPolygon` from common-fate motion, photon eye) | Nothing gives static photon surfaces an identity across exposures |
| Symbolic colour concepts | `seeds/colour_meaning.json` (19 text concepts, e.g. red ≈ 620–700 nm) | Not linked to anything perceptual |

The "objecthood wall" cited by `vision_colour_identity` is a cortex
orientation-selectivity null (`VISION_RUNG8E_RESULTS.md`). Constancy itself was
crossed later by the lighting ladder. What remains walled is a perceived,
persistent object from photons.

## Blocker found and diagnosed

`tests/test_lighting_migrated.py` and `tests/test_border_ownership_migrated.py`
fail in this worktree (18 failed). They fail in the same way in the canonical tree
(14 failed in lighting).

- **Cause:** under the default `boot_core()` seed set, `Substrate.tick()` runs the
  cognitive-cycle default plan, and the `vision_lighting` rules never fire
  (0 steps). The rules themselves work. With `boot_core(seeds=())`, `tick()` fires
  them, and all 11 non-parametrised lighting tests pass.
- **Not caused by an engine mismatch:** the tests call `engine_preamble()`, and the
  failure reproduces on the worktree engine `b6a41e3bbba6`.
- **Separate hazard:** without `engine_preamble()`, a plain import from this
  worktree loads the canonical tree's engine (`e59004a6b6d3`), and that engine's
  provenance check reports it was built from different Rust source.
- **Options:**
  - (a) Fix the default-plan scheduling in core. This is outside this study and
    should be its own change.
  - (b) Boot the property layer minimally (`boot_core(seeds=())` plus the needed
    seeds), declared in the prereg.

  (b) unblocks this work. (a) is needed before the lighting tests can serve as a
  gate.

## Build path

| Stage | Build | Effort | Honest scope |
|---|---|---|---|
| 0 | Resolve the tick/boot issue (option b for now) and confirm the lighting suite passes under it | 0.5 day | — |
| 1 | `LookingEpisode` seed: one durable node per exposure, minted from `Retina has_exposure PhotonExposure` before the exposure is replaced. Carries per-surface state (RG, BY, intensity, adaptation, salience), an observer edge, and `status: observed` via the episodic seed. Flag-gated, OFF | 0.5–1 day | Full |
| 2 | `ColourProperty` seed. An adapter groups declared column spans into surfaces and feeds each one's linear `caught_quanta` (not activation) into lighting frames, with an in-scene white reference. The L1 real-gain comparison then mints or recognises a property on a `has_colour_property` edge. Stimuli come from `domains/spectral_forward.py` (surfaces + white under E/D65/A) | 1–2 days | Surface identity is declared by retinal location, not perceived. Constancy will be approximate, because Gaussian cones on broadband spectra are not exactly diagonal; the size of that error is a result in its own right |
| 3 | Link edge from an episode's per-surface percept to the recognised property (new name, not `presents_as`). Optionally a further edge from the property to the `colour_meaning` concept | 0.5 day | Full |
| 4 | Perceived persistent surface: port `retinal_carve` + `feature_identity` to photon `VisionPolygon`s, or put cones on the 2-D sheet | 1–2 weeks, risky | This is the remaining wall |

## Dissociations each stage makes testable (to preregister)

| Test | Episode prediction | Property prediction | Stage |
|---|---|---|---|
| Constancy: same surface + white under E/D65/A | RG/BY differ | Same property (or refusal if outside class) | 2 |
| Reference ablation: remove the white | — | Property refused, not guessed | 2 |
| Adaptation / afterimage: 610 nm field, then white | White episode turns greenish (measured flip already exists) | No green property minted; white surface unchanged | 1–2 |
| Eyelid: lid-filtered ambient, no surface | Episode exists, reddish-leaning | No surface, no property, no link | 1–3 |
| Memory / imagery: recall red without exposure | No new episode | Property retrieved, marked recalled | 3 |
| Mary before release (research concepts, room episodes, eyelid episodes) | Episodes exist | Concept exists | 3 |
| Mary's first release exposure | New episode | Prediction: release adds an episode node and a link edge, and adds no new property kind | 3 |

The last row turns "does Mary learn something new" into a count: which node and
edge types appear in the graph on release. Episodes without properties (eyelid,
afterimage) and properties without episodes (recall) are the controls that show
the two concepts really are separate.

## Risks

- The tick/boot scheduling issue above.
- Saturating adaptation makes activations non-linear in illuminant gain. Use
  `caught_quanta`.
- Using reflectance matching to decide "same surface" would be circular for a
  constancy test. Identity must be declared by location until stage 4.
- Only the 1-D strip has colour, so there is no spatial surround and no Retinex
  (L2) without stage 4.
- The repo protocol requires a committed preregistration before each run, and an
  OFF-by-default flag with byte-identity. This study has so far frozen by hash
  without commits.

## Decisions needed

1. Option (b), minimal boot, for now, with the core scheduling fix raised
   separately?
2. Is declared-location surface identity acceptable for stages 1–3, with stage 4
   deferred?
3. Commit the preregistration this time, as the protocol requires?
