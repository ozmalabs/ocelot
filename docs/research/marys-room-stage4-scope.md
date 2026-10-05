# Stage 4 scope: perceived, persistent surfaces from photons

Status: scoping only, nothing built. Companion to
`docs/research/marys-room-looking-vs-red-scope.md`. Findings are VERIFIED (read in
source or run) unless marked INFERRED.

## Goal

Give `ColourProperty` a home that the system perceives rather than one the
adapter declares. That means:

1. a surface segmented from a 2-D colour photon image;
2. the same surface re-identified in later exposures by a cue that does not use
   the colour being tested;
3. its colour property computed with illuminant discounting.

Then "looking at red" (the episode) and "red" (the surface's property) can come
apart under conditions the system did not set up by hand.

## Prerequisite 0: the scheduling bug (root cause found)

- **Root cause.** `dual_process_core` is in `CORE_SEEDS` and is also pulled in
  transitively by other core seeds. It installs an enabled `DualProcessPolicy`.
  Under that policy, `CyclePlan::Default` switches to `DualProcess`
  (`cognitive_cycle.rs:587-592`). System 1 then runs only rules labelled
  `latency_class == hard_realtime` (`:692-698`). System 2 runs only rules in a
  requested string area (`:533`).
- **Effect.** Rules with neither label never run. That covers every
  `vision_lighting*` and `vision_border_ownership` rule.
- **Minimal repro.** `boot_core(seeds=('dual_process_core',))` + `tick` gives
  0 steps. With `run_rules`, or with the policy disabled, the rules fire.
- **Scope.** About 20 test files use default `boot_core()` + `tick` (lighting T3,
  L1, L2, L4; border ownership; several vision suites; INFERRED from grep). The
  lighting and L4 results docs report all passing, so this is a regression.
  Commit history is a single import, so it cannot be dated.
- **For this study.**
  - New seeds declare `latency_class: hard_realtime` at manifest level, since
    they are early vision.
  - Reused lighting/border seeds run under an explicit boot that omits
    `dual_process_core`, declared in the prereg.
  - The core fix should be its own preregistered change, not part of this study:
    either label the vision seeds, or let unlabelled rules run in the DualProcess
    plan.

## What exists (VERIFIED)

| Piece | Mechanism | State for this use |
|---|---|---|
| Colour per cell in 2-D | 2-D sheet is rod-only. The 1-D opponent rule `photon_column_synthesizes_retinal_percept` fires unchanged on 2-D cells once L/M/S receptors, typed edges and a `RetinalPercept` are added (4×4 graft gave rg 0.318, by −0.303) | Needs a flagged build change. No new rule |
| Accelerator | `retina_onset_batch` (Rust) updates rod ids only. With cones present it would leave L/M/S stale and the percept rule would never fire | v1 must refuse `retina_accel` + cones. A cone mirror is a later Rust job |
| Readout | No 2-D percept reader. `processed_count()` never advances in 2-D | Tests drive the sheet synchronously (`submit_photons_2d` → `run_cognitive_tasks(1)` → `run_rules`) |
| Segmentation by ratios | `vision_lighting_l4`: illuminant vs reflectance edges, `l4_flood` components feeding `vision_border_ownership` `ProtoObject` (1 proto, 16 members on 12×12; 205/205 randomised) | Integer cone triples on a 4-neighbour field. Neutral illuminants only: chromatic shadows read as reflectance 6/6 |
| Segmentation by motion | `retinal_carve_2d` `VisionPolygon` from common-fate onset events, on the photon eye | Per wave only, no identity. Needs motion |
| Identity by overlap | `track_comps` (`substrate.rs:5078`): cell overlap `2·ov ≥ min(count)`, then nearest centroid, then velocity. Colour-free when `value` = figure label | Runs on motion/grid comps. Not wired to photon polygons |
| Identity by world position | `allocentric_world_view`: ArgminUnique on world x/y within registration uncertainty; `surface_value` published after association | Colour-free. Needs `OpticRangeEvidence` (optic flow) and scalar values |
| Retinotopic held state | `held_surface`, `staleness_decay`: per-cell EMA of `rod.caught_quanta` | Rod-only. Its surprise gate adopts an illuminant step as new content |
| Circular (must not decide identity) | `feature_identity` (`Eq(F.value, R.rvalue)`), `vision_crossframe_identity` (quantised value), `vision_identity_seam` (appearance NCC) | Excluded |
| Constancy | T3 exact; L1 real gains with a derived ≤1 lattice-step bound; L2 Retinex locales; L3b leave-one-out pooled illuminant (0/1300 leaks); L4 edges | Synthetic integer cones. Model error from non-diagonal sensors is not in any bound |

### Measured: this eye is not a diagonal-illuminant eye

The study's own concern is how far von Kries holds for this eye. I tested
white-patch von Kries on expected catches: 24 ColorChecker patches at 100 td,
mapped from E to the target illuminant.

| Target illuminant | Catch error, median / max | Absolute error, median / max | Hue residual after discounting, median / max |
|---|---|---|---|
| D65 | 1.5% / 8.9% | 0.4 / 4.1 quanta | 0.7° / 3.9° |
| A | 4.7% / 22.2% | 0.4 / 13.5 quanta | 2.2° / 24.1° |

L1's bound allows one lattice step of rounding. The eye's broadband Gaussian
sensors add up to 4 quanta of model error under D65 and 13.5 under A. Expected
outcome: most E↔D65 surfaces fall in class, and many E↔A surfaces are refused.
Under §13 the bound cannot be widened by tuning. Options:

- report the refusals as the result (constancy fails where the sensors are
  broadband);
- use L3b-style corroboration across surfaces, whose spread measures the
  non-diagonality from the scene itself;
- later, spectral sharpening (Finlayson et al. 1994). This needs knowledge of
  the eye's spectra, so it would be a declared, model-level rung.

## Identity criterion (non-circular)

**Primary.** Persistent identity is the component whose cell set overlaps the
previous exposure's component by at least half (`2·ov ≥ min(count)`). Boundaries
come from cues that do not involve the chromatic property under test:

- **(i) Luminance edges** (rod or L+M catch), with grain from photon shot noise
  (`√N`, a physical constant, not tuned). Isoluminant chromatic edges will merge;
  this is reported, not patched.
- **(ii) Common-fate motion** (`retinal_carve_2d`). Fully colour-free. Used as the
  falsification arm.
- **(iii) L4 ratio edges** are weakly circular, because they use cone ratios.
  Allowed only as a reported alternative, within neutral illuminants.

Colour enters only after identity is bound.

**Falsifiers (preregister):**

1. Swap two surfaces' positions with the light held fixed. Identity must follow
   position, so the property attached to "surface 1" changes. Re-binding by
   colour would mean the criterion is circular.
2. Same colour at two locations: never merged.
3. Same geometry, different colour: two identities.
4. Chromatic illuminant step: L4 route expected to misread it (known bound),
   while the luminance/motion routes keep identity.
5. Move a patch: the common-fate route keeps identity; the luminance route must
   either keep it or report a break, never guess.

## Build plan

| Step | Build | Reuse | Effort |
|---|---|---|---|
| 4.0 | Explicit boot without `dual_process_core`; new seeds labelled `hard_realtime` | — | 0.5 d |
| 4.1 | Colour 2-D sheet behind flag `retina_2d_cones`: rod+L+M+S and a `RetinalPercept` per cell; `percepts_2d()` reader; refuse `retina_accel` + cones; default-off byte-identity test; fires-in-2-D test | Percept rule unchanged; graph path | 1 d |
| 4.2 | `domains/spectral_scene.py` (new; `spectral_forward.py` is frozen): Mondrian scenes of ColorChecker patches, per-cell SPD → packets, illuminant schedules, swaps, motion, eyelid, adapting fields | `spectral_forward` API | 0.5–1 d |
| 4.3 | Segmentation seed (`hard_realtime`): luminance-edge components at shot-noise grain, feeding `ProtoObject` via `vision_border_ownership` | border ownership; L4 adapter pattern | 1–2 d |
| 4.4 | Persistence seed `surface_persistence`: `PersistentSurface` node with an overlap match over member cells, birth/coast/die, refusal on ambiguous overlap | `track_comps` criteria (as rules, or via the Rust call) | 1–2 d |
| 4.5 | Property layer: per-surface mean linear catches (saturated cells refused) feed lighting frames (first exposure = reference). L1 in-class/recognise, or L3b pooled with surfaces as locales. Mints `ColourProperty` on `has_colour_property`. Plus stage 1 `LookingEpisode` and stage 3 episode→property edge | lighting T3/L1/L3b | 1.5–2 d |
| 4.6 | Battery + prereg + results doc (dissociations and falsifiers above) | — | 1–2 d |
| Optional | Common-fate route wired to persistence (motion falsifier) | `retinal_carve_2d`, `track_comps` | 1–2 d |
| Optional | Gaze-shift route: chromatic `allocentric_world_view` publish | allocentric seeds | 2–4 d |
| Optional | Cone-aware Rust accelerator mirror with identity + perturb gates (§10) | `retina_onset_batch` | 2–3 d |

Core path (4.0–4.6): about 7–10 working days. With all optional routes: about
13–19.

## Performance (VERIFIED measurements, INFERRED extrapolation)

The rod-only graph path takes 36–45 ms per frame at 32×24 (accelerator about
4 ms). A 4-receptor graph path is estimated at about 0.17–0.2 s per frame at
32×24, using the 1-D strip with 768 columns as a proxy. A battery of a few hundred
exposures is therefore minutes, so no accelerator is needed for the study.

## Dissociation battery (what stage 4 adds over stage 2)

| Test | Episode | Property | Identity cue |
|---|---|---|---|
| Illuminant change on a static Mondrian | RG/BY shift | Same `ColourProperty` (in class), or refused (A) | Luminance-edge overlap |
| Position swap | — | Property follows the new occupant | Overlap |
| Moving patch across a light boundary | Shifts along the path | Same property | Common fate |
| Afterimage after a 610 nm field | Grey surface looks greenish | No green property minted | Overlap |
| Eyelid (diffuse lid-filtered light) | Reddish-leaning episode | No surface, so no property | — |
| Recall without exposure | No episode | Property retrieved, marked recalled | — |
| Mary's release | First chromatic episodes | Properties minted on perceived surfaces, plus link edges | Overlap |

## Risks

- The scheduler regression affects more than this study; it should be raised.
- Non-diagonal sensors make constancy partial by construction (measured above).
  Reporting refusals honestly is the fallback.
- Isoluminant boundaries are invisible to the luminance route.
- `staleness_decay` adopts illuminant steps as content changes. Don't route
  properties through held cells without a per-channel variant.
- 2-D gotchas: `processed_count()` doesn't advance; accelerator × cones;
  per-sensor epoch × cones (don't combine in v1).
- Protocol: committed prereg before each run, OFF-by-default flags with
  byte-identity, engine built only via `scripts/engine_build.sh` if Rust is
  touched. This worktree already carries a modified `.so`.

## Decisions (approved 2026-10-04)

1. **Boot.** Use the explicit-boot workaround for this study. The core scheduler
   fix is raised separately, in `docs/research/engine_substrate/dual-process-starves-unlabelled-rules.md`.
2. **Identity route.** Primary: luminance edges with shot-noise grain. Common-fate
   motion is the falsifier arm. L4 ratio edges appear only as a reported
   alternative.
3. **Constancy under illuminant A.** Refusals are reported as the primary result.
   L3b corroboration across surfaces is added as a declared second rung.
   "All approved" was read as approving both options.
4. **Preregistration.** Committed before each run, as the protocol requires.
