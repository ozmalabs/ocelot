# Mary's Room stage 4: preregistered replication — AMENDMENT A1

This amends `docs/experiments/marys-room-stage4-prereg.md` (committed at
`f25aae47`). It does not edit that file. The amendment, the runner
`scripts/marys_room_stage4_replication.py` and the apparatus addition
(`random_mondrian` / `neutral_mondrian` in `domains/spectral_scene.py`) are
committed together **before** any battery exposure. As with the original,
"look" means the computed `SurfaceLook`, and every claim is about the model.

## 1. Why a replication

**Anomaly in the stage-4 battery** (`docs/experiments/marys-room-stage4-results.md`, "Anomaly"):

- The held-out layouts `standard_mondrian(seed=k)`, k = 1…8, only permute chromatic reflectances among fixed slots. Every non-pair patch is separated from the others by background gutters.
- The pipeline is invariant to where a patch sits: the frame anchor is a max over surfaces, the rung-2 pool is leave-one-out, and every slot touches the background in the same way. So "every per-surface outcome in B1, B2 and B7 is identical across all 9 layouts, the development layout included".
- Example: at 100 td under D65, every layout gives rung 1 = 5/10, non-anchor 4/9 and rung 2 = 7/10.
- The pooled n values (e.g. 72 hue instances, 144 non-exempt patches) are 8 copies of one 9–10-surface scene. The Wilson intervals overstate precision by about √8, so the effective n is one scene.
- B4 picked blue/yellow in every layout. B5 moved patch 10 in every layout.
- The results doc limits the verdicts (P1, P3, P4, P6 supported; P2, P5 partially) to "this one set of 10 surfaces".

**P2 and P5.** B1's hue clause failed. The median E→A hue change was smaller than E→D65 at both td: 4.24° vs 4.47° at 100 td, and 2.41° vs 4.58° at 1000 td. The non-preregistered Euclidean look shift went the other way: 0.027 vs 0.0047 at 100 td, and 0.093 vs 0.023 at 1000 td. P5(a) failed in 0/16 sequences, because `presents_unrecognised` first appears at release. P5(b) held for 64/144 chromatic patches. The results doc calls both P5 failures structural.

**Engine change since the prereg.**

- The prereg engine was `b6a41e3bbba6`. HEAD is now `3460f381` ("fix: run unlabelled rules in the DualProcess cycle plan"), with engine **`ed9237c97f20`**. That fix makes rules with neither a hard_realtime nor a System-2 label settle in the DualProcess default-boot `tick()`.
- The stage-4 pipeline drives the eye's own substrate mechanically. Each `PerceivedSurfaceWorld.expose` runs `submit_photons_2d` → `run_cognitive_tasks(1)` → `run_rules` (to fixpoint) → prune.
- Under `ed9237c97f20`, `tests/test_retina_2d_cones_migrated.py` and `tests/test_stage4_fixes_migrated.py` pass (§10). The second includes the flags-off byte-identity proof against the f25aae47 generators.
- That proof compares seeds on one engine; it does not compare the two engines. So engine equivalence for battery observables is not assumed. It is one more reason to replicate.

**New flagged features** (commit `d0b4f087`, every flag OFF by default):

- re-acquisition of coasting surfaces (`SurfacePersistenceParams.reacquire`);
- recall (`colour_recall`);
- property→concept link (`colour_concept_link`);
- common-fate motion segments (`SurfaceSegmentationParams.motion_segments`).

With these flags at 0, every observable is byte-identical to f25aae47. The prereg's "Not covered" list can now be tested (N1–N4).

## 2. Apparatus and freeze

- **Unchanged files.** The eye, adapter, seeds, generators, `spectral_forward.py`, the broad-study files and the original battery runner are not changed. A1 adds only `random_mondrian`, `neutral_mondrian` and their helpers at the end of `domains/spectral_scene.py`.
  - Every pre-A1 line is unchanged; `tests/test_spectral_scene_random_migrated.py` asserts that `git show 3460f381:domains/spectral_scene.py` is a byte prefix of the file.
  - Existing tests pass (§10).
- **Engine.** `ed9237c97f20` (`runners/dsl/python/substrate_rs/_native.abi3.so`). The runner aborts if `provenance_line()` names any other engine.
- **Freeze.** The runner is committed with this amendment. At start, a confirmatory run aborts unless all of the following hold:
  1. `git ls-files --error-unmatch` and `git diff --quiet HEAD -- <FREEZE_TRACKED>` both exit 0. `FREEZE_TRACKED` covers:
     - the runner, this amendment, the original runner, prereg and results;
     - `photon_eye.py`, `spectral_scene.py`, `perceived_surface_world.py`, `spectral_forward.py`, `engine_provenance.py`;
     - all seven seeds and their seven generators;
     - the broad-study scripts and results, and the stage-4 results;
     - `tests/test_spectral_scene_random_migrated.py`;
     - `runners/dsl/src`, the `.so` and `_native.build.json`.
  2. There are no untracked files under those paths.
  3. `3460f381` is an ancestor of HEAD.
  4. The combined sha256 of `data/colour/**` is `8e567ebe55d33d64ab7efc0c83bdf8c7e016875b26ca97e364567d0fd109355f`. These files are gitignored, so they are frozen by hash; the per-file hashes are written to the output.
- **Output.** The output JSON embeds the runner's own sha256, HEAD, the amendment's sha256, the engine provenance stamp, `RULES` (original) and `RULES_A1`.

## 3. Layouts

`spectral_scene.random_mondrian(seed)` draws a new, independent layout from `numpy.random.default_rng(seed)`:

- **Geometry.**
  - It has 6–12 patches. Each rect has w, h ∈ 3…7 and a uniform position fully on the 24×16 sheet.
  - There are no gutters, so patches may abut or overlap. Later rects overwrite earlier ones, and the label map is the final visible map.
  - Reporting-unit constraint: each patch and the background must be one non-empty 4-connected region. A rect that would break this for any label is redrawn.
- **Reflectances.**
  - The background is drawn from neutrals 19–24.
  - White 9.5 (patch 19) is a patch iff the seed is even, and it is then never the background. In odd seeds the background may be white.
  - The other patch reflectances are drawn without replacement from the remaining ColorChecker patches. A draw equal to the background is redrawn.
- **Mary's room.** `neutral_mondrian(seed)` uses the same geometry. Its background is a neutral, and each patch is one of the five other neutrals, drawn with replacement.

**Layout seeds.** R1, R2, R4, R5, R7 and N1–N4 use seeds **101…116**. R6 and N5 use **101…108**. The stage-4 development layout and the permuted `standard_mondrian(seed=k)` layouts are **not** reused.

### Independence pre-check (no eye, no seeds; `--precheck`)

The table comes from `spectral_scene.expected_catches` only. It touches no outcome of the battery.

- **anchor**: the surface holding the per-channel maximum of expected L, M and S, under E / D65 / A. It is shown once because it is the same under all three illuminants in every layout. `none(L/M/S)` means no single surface holds all three maxima.
- **adj**: the number of 4-adjacent surface pairs.
- **ratio set**: the hash, minimum and median of the adjacent-pair ratio max(Y)/min(Y) under E, where Y is the expected L+M.
- **near-iso**: the number of adjacent pairs with |ΔY| ≤ √(Y_a+Y_b), the segmentation seed's join criterion.

| seed | n | white patch | bg | anchor (E = D65 = A) | adj | ratio set | min r | med r | near-iso E/D65/A @100 td | @1000 td |
|---|---|---|---|---|---|---|---|---|---|---|
| 101 | 8 | no | n5 | none(yellow/n8/n8) | 16 | 1168c3d7 | 1.009 | 1.909 | 1/1/1 | 1/1/0 |
| 102 | 9 | yes | n3.5 | white | 23 | f2e240c0 | 1.103 | 2.359 | 2/2/2 | 0/0/0 |
| 103 | 9 | no | black | none(yellow/yellow/blue flower) | 14 | 3b05315d | 1.537 | 5.002 | 0/0/0 | 0/0/0 |
| 104 | 10 | yes | black | white | 22 | 96d10eb8 | 1.025 | 3.069 | 3/2/3 | 1/1/1 |
| 105 | 7 | no | n6.5 | none(yellow green/yellow green/n6.5) | 13 | bf236934 | 1.010 | 1.899 | 2/2/2 | 1/0/0 |
| 106 | 9 | yes | n5 | white | 19 | 758d04ca | 1.000 | 1.939 | 2/2/3 | 1/1/0 |
| 107 | 6 | no | white | white (background) | 8 | 608878dd | 1.585 | 3.676 | 0/0/0 | 0/0/0 |
| 108 | 6 | yes | n5 | white | 8 | 2ef2025e | 1.009 | 1.912 | 1/1/1 | 1/1/0 |
| 109 | 9 | no | n5 | none(orange yellow/bluish green/blue flower) | 17 | 2be60c56 | 1.009 | 1.558 | 4/3/4 | 1/1/0 |
| 110 | 10 | yes | n3.5 | white | 17 | a61df350 | 1.103 | 2.629 | 2/3/1 | 0/1/0 |
| 111 | 9 | no | n3.5 | n8 | 14 | 47a76704 | 1.178 | 2.085 | 0/0/1 | 0/0/0 |
| 112 | 7 | yes | black | white | 13 | f40fb5fb | 1.078 | 5.921 | 1/0/1 | 0/0/0 |
| 113 | 8 | no | black | n8 | 12 | b52bcc27 | 2.003 | 6.703 | 0/0/0 | 0/0/0 |
| 114 | 7 | yes | n6.5 | white | 11 | fb14540d | 1.172 | 1.705 | 0/0/0 | 0/0/0 |
| 115 | 10 | no | white | white (background) | 20 | ff4231c5 | 1.078 | 3.849 | 1/0/2 | 0/0/1 |
| 116 | 7 | yes | black | white | 8 | f92de8cd | 2.241 | 6.110 | 0/0/0 | 0/0/0 |

Distinct values over seeds 101…116:

| | Count |
|---|---|
| Label maps | 16 |
| Anchor identities | 6 |
| Adjacent-ratio sets | 16 |
| Near-isoluminant profiles | 11 |

The stage-4 held-out layouts `standard_mondrian(seed = 1…8)` give **1 / 1 / 1 / 1** on the same measures. That is the anomaly, reproduced without the eye.

**Consequences known before any exposure** (geometry and expected catches only):

- **No anchor surface.** In layouts 101, 103, 105 and 109, no single surface is the per-channel maximum. Under R7 (kept verbatim), every frame of those layouts counts as "rung 1 not holding on the anchor". The P3 anchor clause therefore cannot be fully supported. The single-anchor-layout restriction is reported as a **secondary** analysis (A18) and never enters a verdict.
- **P5.** P5(a) and (b) carry the same structural failures diagnosed in stage 4. A constant room cannot produce a rung-1 refusal, and continuing surfaces are not re-minted. They are evaluated verbatim regardless.
- **R2 roles.** Layout 109 has no achromatic declared patch, so its R2 "white" role is absent (A4).

## 4. Replication arms R1–R7 (flags OFF)

**Semantics.** Every R world uses `PerceivedSurfaceWorld(24, 16, stage45=True)` with the adapter defaults. The other flags are `reacquire=0` and `motion_segments=0`. The `colour_recall` and `colour_concept_link` seeds are **not loaded**. This is the f25aae47 semantics (`test_flags_off_byte_identical_to_f25aae47`).

**Readback.** Params are read back and asserted: segmentation, persistence, colour, pooled and looking are 1; reacquire and motion_segments are 0; no recall or concept param nodes exist.

**Rules reused verbatim.** The original rules R3–R11, R14 and R16–R18 apply verbatim, through the imported functions `an_b1`, `summarise_b1`, `an_b3`, `an_b4`, `an_b5`, `an_b6`, `an_b7` and `verdicts` of `scripts/marys_room_stage4_battery.py`. That file is not modified. The held-out set is seeds 101…116 (R6: 101…108). For `an_b7`, the deterministic comparison set (`B7_LAYOUTS`) is set to 101…116 at runtime.

**Levels.** scene_td ∈ {100, 1000}, with deterministic quantisation unless stated.

| Arm | Sequence (each a fresh world) | Recorded |
|---|---|---|
| R1 = B1 constancy | E, D65, A, E | per surface: sid continuity; rung-1 status; rung-2 status; look hue-angle change vs exposure 1 |
| R2 = B2 adaptation | scene E; 20 × (scene E + uniform 610 nm overlay, 2000 quanta/cell); scene E | neutral and white surfaces (A4): look rg at exposures 1 and 22; check status at 22 |
| R3 = B3 eyelid | `diffuse(filter='eyelid')` under E/D65/A at 1000 and 10⁴ td | counts of LookingEpisode, FieldLook, SurfaceLook, ColourProperty, PropertyCheck, link edges |
| R4 = B4 swap falsifier | E, then `swap_patches(a,b)` under E for the two declared chromatic patches with the largest L+M difference in that layout | sids at the swapped locations; their check status; others' status |
| R5 = B5 motion | E; translate one declared patch (A6) by +1 column per exposure for 4 exposures; then a jump of 6 columns | sid continuity per step; birth + coast at the jump |
| R6 = B6 Mary room→release | Room: 6 exposures of `neutral_mondrian(seed)` under E, interleaved with 2 eyelid ganzfelds (M M G M M G M M). Release: 3 exposures of `random_mondrian(seed)` (same geometry) under E | node and edge counts by type after the room and after the release; the set of node TYPES instantiated in each phase |
| R7 = B7 Poisson | R1 on all 16 layouts with Poisson quantisation, seeds 7001–7005 | segment count per exposure; sid continuity; rung-1 and rung-2 status |

**Mechanical rules defined on random layouts** (full text in `RULES_A1`):

- **A4, R2 roles.**
  - "neutral" is the background (patch 0, always a neutral).
  - "white" is the declared white 9.5 patch in even seeds. In odd seeds it is the declared achromatic patch with the largest expected L+M under E (ties: lowest id). It is absent if the layout has none (seed 109).
- **A5, R4 pair.** Original R12 verbatim: among chromatic declared patches, the largest |L+M| difference from `patch_report(scene,'E',td)`, ties lexicographic. A layout with fewer than 2 chromatic patches would be skipped; none is.
- **A6, R5 patch.** Original R13 with the unmoved position included: the lowest-id patch whose rect, at offsets 0, +1…+4 and +10 columns, lies on the sheet and overlaps no other declared rect.
  - If there is none, the mirrored schedule [(−1,0)]×4 + [(−6,0)] is tried with the same rule.
  - Only 4 of 101…116 qualify, because the random sheets are crowded: 103 (patch 7, mirrored), 107 (3), 108 (2) and 113 (6).
  - **Supplement:** the first seeds 117, 118, … (ascending) whose layout qualifies are added until R5 has 16 layouts. These are 118, 142, 147, 156, 160, 175, 177, 178, 189, 191, 197 and 199. They are chosen by geometry only, and they enter only R5 and P1-B5.
  - P1-B5 is also reported on the 4 primary layouts alone.
  - The qualifying layouts are less crowded than average, which is a selection effect, reported as such.
- **A7, R6.** The room is `neutral_mondrian(seed)`, G is `diffuse(24,16,'E',td,filter='eyelid')`, and the release is `random_mondrian(seed)` ×3. Every exposure is at the arm's td.

**Predictions P1–P6**, copied verbatim from the prereg. They apply to R1–R7 as they applied to B1–B7.

- **P1. Identity is colour-free.** In B1, every surface keeps its sid across illuminant changes, except surfaces whose luminance boundary with a neighbour falls inside the shot-noise criterion under one of the illuminants. Those split or merge and are refused, never silently re-bound. In B4, sids follow position. In B5, the sid persists through 1-column steps and is reborn at the 6-column jump.
- **P2. Looks change with viewing.** In B1, the median per-surface look hue-angle change E→A is larger than E→D65, and both are larger than 0. In B2, neutral and white looks have rg at exposure 22 below rg at exposure 1.
- **P3. Properties hold only within the stated class.**
  - Rung 1 holds on the anchor surface in every frame.
  - Non-anchor rung-1 holds: the fraction at 100 td ≥ the fraction at 1000 td, and the fraction under A ≤ the fraction under D65.
  - Rung 2 holds on at least as many surfaces as rung 1 in every condition.
  - In B2, checks hold at exposure 22 (catches are linear) while looks have shifted.
  - In B4, swapped surfaces are refused.
- **P4. Episodes without properties.** In B3, every exposure yields one LookingEpisode and one FieldLook, and zero SurfaceLook, ColourProperty, PropertyCheck and link edges.
- **P5. Release adds instances, not kinds.** In B6, every node type and edge type instantiated after release was already instantiated during the room phase. Release adds new ColourProperty instances for chromatic surfaces, new SurfaceLooks and new `presents_property` edges, and no new types.
- **P6. Robustness.** In B7, Poisson quantisation fragments surfaces: the median segment count exceeds the deterministic count. The rung-1 refusal fraction is ≥ the deterministic one. This prediction is about a known limitation; it is not a success criterion.

Verdict rules R9 and R10 apply as before: point estimates decide, and "every" clauses are universal.

## 5. New arms N1–N5 (flags ON as named; stage45=True unless stated)

| Arm | Flags | Sequence | Recorded |
|---|---|---|---|
| N1 re-acquisition | reacquire=1 | **GG:** scene E, U, U, scene E, where U = `diffuse(24,16,'E',td, filter=None)` (open-eye uniform field). **ES:** scene E, eyelid, `swap_patches(scene, a, b)` under E with the A5 pair | per patch: sid set at the last exposure = at exposure 1 (all ≥ 0) → re-acquired; intermediate exposures blank; ES: swapped-sid and other-sid check status, properties unchanged |
| N2 recall | colour_recall loaded, enabled | scene E, eyelid. After the eyelid exposure, one RecallCue per distinct sid ≥ 0 that covered a declared patch at exposure 1, then a control cue for sid 10⁶ | Recollection status per cue; counts of every stage-4.5 type and link edge before and after the cues |
| N3 concept link | colour_concept_link loaded, enabled | one exposure, scene E, at 100 and 1000 td | per patch: truth `truth_for(E·R, 'E')['hue4']`, concept_status, concept, angle, margin. Scored iff truth is chromatic and the patch is a single-patch surface. A non-`categorised` status or a missing property counts as incorrect |
| N4 motion route | motion_segments = 1 vs 0 (two fresh worlds); **stage45=False**, as in the stage-4-fix motion tests | 8 static exposures of scene E, then the declared patch +1 column per exposure × 4 | per exposure: moved-patch sids, whether it is a single-patch surface, motion segments (n_cells, sid, decision, birth_reason), carve polygons (count, coherence); whether flag-on sid grids equal flag-off |
| N5 B6 variant | reacquire=1 | as R6, but the release is `random_mondrian(seed + 1000)`, a different geometry and reflectance set; seeds 101…108 | as R6, plus re-acquired surface counts; P5's clauses computed descriptively |

**N4 patch rule (fixed now, A12).**

1. Candidates are declared patches whose rect at offsets 0 and +1…+4 lies on the sheet and overlaps no other declared rect.
2. Among them, pick the smallest luminance contrast to the background, |Y_p − Y_0|/(Y_p + Y_0), with Y = expected L+M under E. Ties go to the lowest id.
3. If there is no candidate, use the mirrored direction (−1). If there is still none, the layout has no N4 sequence.

Dry-run result: 13 layouts qualify; 101, 104 and 106 do not.

## 6. New predictions

- **Q1 (data-informed, from stage-4 "Not preregistered").** In R1, the median per-surface Euclidean look shift |Δ(rg, by)| against exposure 1 is larger under A than under D65 at both td. Instances follow the R6 hue inclusion rule, and the verdict follows R9 across td.
- **Q2.** N1 re-acquires ≥ 90% of surfaces whose geometry is unchanged. The unit is a declared patch, and geometry is unchanged for every patch in GG and ES. The threshold must hold in each (GG/ES, td) cell (R10).
- **Q3.** In every N2 sequence, every non-control cue is answered with Recollection status `recalled`, and the cues create zero new LookingEpisode and zero new SurfaceLook (R10).
- **Q4.** N3 accuracy exceeds the majority-class rate p0 at each td. p0 is the largest truth-class share among scored patches pooled over layouts. The test is an exact one-sided binomial P(X ≥ k | n, p0) < 0.05 together with accuracy > p0, and the verdict follows R9 across td. Accuracy is reported with Wilson 95% over surfaces and with the layout-cluster bootstrap.
- **Q5 (N4). No prediction.** The stage-4 fixes measured no coherent carve polygon for an isoluminant patch: the onset path is rod-only, and the motion route produced no motion group for isoluminant patch 7. N4 reports motion segments, polygons and identity with the flag on and off, and nothing more. N5 is likewise descriptive.

## 7. Independence requirement and statistics (preregistered)

- **Distinct profiles.** For each R arm, report the number of distinct per-layout outcome profiles over layouts (A15 defines the profile vector per arm). A count of 1 reproduces the stage-4 anomaly.
- **Effective n.** The layout is the unit of independence, so the layout count is the effective n.
- **Intervals.** Every pooled fraction or median is reported with:
  - Wilson 95% over surfaces (fractions only);
  - a layout-cluster percentile bootstrap. Each statistic resamples layouts with replacement B = 10000 times, with `numpy.random.default_rng(20261006)` freshly seeded for that statistic, and recomputes pooled k/n or the pooled median. Resamples with n = 0 are dropped and counted.
- **Verdicts.** Verdicts are still decided on point estimates (R9/R10). Both intervals are reported alongside.
- **Determinism.** After all arms, R1 and R3 are re-run in fresh worlds, and the raw sha256 (timings excluded) must match (A17).

## 8. Planned scale (from `--dry-run`)

| Arm | Sequences | Exposures |
|---|---|---|
| R1 | 32 | 128 |
| R2 | 32 | 704 |
| R3 | 6 | 6 |
| R4 | 32 | 64 |
| R5 | 32 | 192 |
| R6 | 16 | 176 |
| R7 | 160 | 640 |
| N1 | 64 | 224 |
| N2 | 32 | 64 |
| N3 | 32 | 32 |
| N4 | 52 | 624 |
| N5 | 16 | 176 |
| Determinism re-run | 38 | 134 |

- **Totals.** About 3164 exposures and 544 world builds. That is roughly 32 min at 0.60 s per exposure, with an upper bound of about 83 min at the stage-4 maximum of 1.57 s.
- **Dry-run check.** The dry run builds every scene, packet list and world. GraphEye.submit_photons_2d and PerceivedSurfaceWorld.expose are replaced by sentinels that abort the process, and their call counts are printed as 0. The exact figures are in the runner's dry-run output; this table is a copy.

## 9. Deviations from the original battery

1. **Layouts.** The layouts are `random_mondrian` seeds 101…116 (R6/N5: 101…108; R5 supplement A6), not `standard_mondrian(seed=k)`. No development-layout arm is run.
2. **Engine.** `ed9237c97f20` replaces `b6a41e3bbba6`. Seeds are now v1.1.0 / v1.0.0 with the new flags at 0, which is byte-identical to the f25aae47 generators on one engine.
3. **R2 roles** are redefined (A4), because random layouts have a variable background and white is present only in even seeds. Layout 109 has no "white" role.
4. **R5** includes the unmoved position in the overlap test, adds a mirrored-direction fallback, and adds supplement seeds (A6).
5. **R6 room.** The room has random geometry, its neutrals are drawn with replacement, and the background neutral varies by layout. In the original it was always neutral 5. No room slot equals the background.
6. **R7** runs on 16 layouts, not 2.
7. **Statistics.** A layout-cluster bootstrap and distinct-profile counts are added. The secondary single-anchor P3 analysis is added (A18).
8. **Freeze.** The freeze is a `git diff --quiet HEAD` check on a committed runner plus a data hash. The runner's sha256 and HEAD are embedded in the output. This fixes original Deviation 2.
9. **Smoke and dry runs, disclosed.**
   - Before the freeze, the preparer ran `--smoke` once. It ran every arm once at 1000 td on the development layout (`standard_mondrian(seed=None)`, already observed in stage 4; N5's release was `standard_mondrian(seed=1)`), wrote to `/tmp`, and exercised the verdict code on those development data. No battery layout was exposed.
   - The preparer saw those development outputs. Predictions Q1–Q5 were fixed in the brief before the smoke run and were not changed.
   - The development B2 white look reproduced the stage-4 values at 1000 td: rg 0.0332 → −0.0459.
   - `--precheck` and `--dry-run` submit no exposure.
10. **N arms.**
    - N1's ganzfeld is the open-eye uniform field (`filter=None`). The stage-4-fix test used `diffuse()`'s default eyelid filter.
    - N4 uses stage45=False, matching the tested motion configuration.
11. **Recovery.** Analysis-only `--from-raw` re-entry is allowed only for crash recovery, on the same raw records.

## 10. Verification at preparation time (no battery exposure)

All runs used the `ed9237c97f20` engine:

| Suite | Result |
|---|---|
| `tests/test_spectral_scene_random_migrated.py` | 439 passed |
| `tests/test_spectral_scene.py` | 19 passed |
| `tests/test_stage4_fixes_migrated.py` | 26 passed |
| `tests/test_retina_2d_cones_migrated.py` | 15 passed |
| `tests/test_perceived_surfaces_migrated.py` | 14 passed |
| `tests/test_colour_property_episode_migrated.py` | 9 passed |

In total, 522 tests passed in 168 s.

## 11. Running

1. Commit this amendment, the runner, `domains/spectral_scene.py` and the new test, with a clean tree.
2. Run:

   ```
   PYTHONPATH=. /home/matt/ozmadev/ocelot/.venv/bin/python scripts/marys_room_stage4_replication.py
   ```

3. The output is `results/marys_room_stage4_replication.json`, with the raw checkpoint at `/tmp/marys_room_stage4_replication_raw.json`.
4. The results doc must separate R (replication) verdicts, Q verdicts, secondary analyses and anything added after seeing output.
