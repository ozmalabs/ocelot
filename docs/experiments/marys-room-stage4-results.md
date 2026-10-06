# Mary's Room stage 4: looking episodes versus perceived colour properties — RESULTS

This is the confirmatory battery (arms B1–B7, predictions P1–P6) preregistered in
`docs/experiments/marys-room-stage4-prereg.md`, committed at `f25aae47`.

- Runner: `scripts/marys_room_stage4_battery.py`. This is new analysis code. It builds worlds only through `domains/perceived_surface_world.py` and `domains/spectral_scene.py`.
- Outputs:
  - `results/marys_room_stage4_battery.json`, 20 MB. It holds every per-surface, per-exposure record, plus summaries, verdicts, rules, provenance and git checks.
  - `results/marys_room_stage4_battery_summary.csv`.

"Look" means the computed `SurfaceLook` / `FieldLook` (the mean `RetinalPercept`
rg/by of a surface's cells). "Property" means the graph's `ColourProperty`.
Nothing here measures phenomenal experience, and nothing is a claim about human
colour vision.

## Provenance and integrity

- Engine: `b6a41e3bbba6` (`/tmp/ocelot-marys-room/runners/dsl/python/substrate_rs/_native.abi3.so`, 1 other tree build shadowed). Recorded via `provenance_stamp()` in the JSON.
  - `.so` sha256 `b6a41e3b…99ed1`.
  - `_native.build.json` sha256 `fc9c2106…ab31a`.
  - Both files show as modified relative to HEAD. This was already true before the run, and they are the expected engine.
- git HEAD `f25aae476f41…` = the prereg commit. No commits were made.
- **Apparatus check.** Before any exposure, the script ran `git diff --quiet f25aae47 -- <29 paths>` and got exit code 0. The script would have aborted on any difference. The 29 paths are:
  - the prereg;
  - `photon_eye.py`, `spectral_scene.py`, `perceived_surface_world.py`;
  - the five seeds and their five `tools/build_*_seed.py` generators;
  - `spectral_forward.py`, `scripts/marys_room_broad*.py` and `results/marys_room_broad*`;
  - `runners/dsl/src`.

  The same check was clean again after the run.
- Every world loaded all five seeds with `rules_skipped == []`. Its param nodes were read back and asserted: `SurfaceSegmentationParams.enabled`, `SurfacePersistenceParams.enabled`, `ColourPropertyParams.enabled` and `.pooled`, and `LookingEpisodeParams.enabled` were all 1.0. `look_property_link` has no flag; it is gated on the colour and looking flags.
- **Determinism.** After the battery, B1 (all 9 layouts × 2 td) and B3 were re-run in fresh worlds. The raw-record sha256 values, with timings excluded, were identical:
  - B1 `c2d1e2c8…`
  - B3 `87bddfff…`
  - Whole raw payload `9d889676…`
- **Runtime.** The pre-run estimate was 974 exposures at about 14.6 min. The actual run was 896 battery exposures plus 78 rerun exposures:
  - 11.2 min wall in total;
  - mean 0.515 s per exposure, maximum 1.57 s;
  - 140 world builds, about 0.06 s each.
- **Runner script.** sha256 `de2dcad2355a…01303`, taken at launch and unchanged afterwards. It is not embedded in the JSON (see Deviations).

## Declared mechanical choices (fixed in `RULES` before any exposure; printed at start)

Where the prereg left a mechanical choice open, it was fixed by rule. None depends
on an outcome. Full text is in `RULES` in the script and in the JSON.

- **Surface unit (R1).** For reporting, a surface is a declared ground-truth patch: 0 is the background (neutral 5), and 1–10 are the declared patches. Its sid(s) are the graph `cur_sid` values over its cells. The label map is used only for reporting.
- **B2 surfaces (R2).** "Neutral" is the background and "white" is patch 1. Held-out layouts permute only the chromatic reflectances, so the background is the only neutral.
- **P1 exception set (R3).** A patch is exempt if, at some exposure of the sequence, a 4-adjacent cell pair across its border satisfies the seed's own join criterion |ΔY| ≤ √(Y_a+Y_b). Y is the graph's `seg_Y`.
- **Silent re-bind (R4).** A `continue` segment whose sid covers a different set of patches than it did at t−1.
- **Hue (R6).** Hue is degrees(atan2(by, rg)), and the change is the wrapped |Δ| against exposure 1. A patch enters the hue statistics only if, at both exposures, a single sid covers it and that sid covers no other patch. This excludes the merged isoluminant pair.
- **Anchor surface (R7).** The anchor surface is the sid whose lattice catch equals the frame anchor (aL, aM, aS) on all three channels. A frame with no such sid, or a frame whose anchor was minted in that frame, counts as a failure.
- **P3 frames (R8).** P3 uses the B1 exposures D65, A and E_return on held-out layouts. The td comparison pools the D65 and A frames. The A ≤ D65 comparison is made at each td. "Every condition" means every (layout, td, exposure) cell.
- **Verdict rules (R9, R10).**
  - Comparisons use point estimates; Wilson 95% intervals are reported alongside.
  - A comparison clause evaluated at each td is supported if it holds at every td, partially supported if it holds at some, and not supported if it holds at none.
  - A universal clause is supported if all instances hold, partially supported if some do, and not supported if none do.
  - A multi-clause prediction is supported only if every clause is supported, and not supported only if every clause is not supported. Otherwise it is partially supported.
- **B3 (R11).** One fresh world and one exposure for each illuminant (E, D65, A) × td (1000, 10⁴).
- **B4 pair (R12).** Among the chromatic declared patches, the pair with the largest |L+M| difference from `patch_report(scene, 'E', td)`. In every layout this was blue and yellow, at different positions per layout.
- **B5 patch (R13).** The lowest-id patch whose rect stays on the sheet and never overlaps another rect at any offset of the schedule. That is patch 10 (row 11, columns 8–11), in all layouts. Its reflectance varies by layout.
- **B6 room (R15).**
  - Slot i gets ColorChecker neutral 19 + ((i−1) mod 6). So slots 4 and 10 are neutral 5, identical to the background.
  - The order is M M G M M G M M, then R R R. M is the room Mondrian, G is the eyelid ganzfeld under E, and R is the release.
  - Every exposure in B6 is at the arm's td.
- **B6 verdict (R16).** Clause (a) is a subset test on types with count > 0 after the room versus after the release. Clause (b) is evaluated per chromatic patch at release exposure 1. Clause (c) requires the counts of SurfaceLook and `presents_property` to increase.
- **B7 (R17).** `illuminant_change(..., method='poisson', seed=s)`. Clause 1 is checked per (layout, td, exposure) cell, using the median over 5 seeds. Clause 2 is checked per td, over non-minted checks at exposures 2–4.

## Confirmatory results (held-out layouts k = 1…8, both td)

### B1 constancy (E, D65, A, E)

Identity:

- Every non-exempt patch kept one constant sid across all 4 exposures: 144/144 [0.974, 1.000].
- The exempt set was exactly the declared isoluminant pair {6, 7} in all 16 sequences.
- Across all patches, 160/176 were stable.
- At 100 td the pair stayed merged throughout.
- At 1000 td:
  - Under A the pair split into two births, both `refused_ambiguous`. The merged surface coasted as `split`.
  - At E_return it re-merged as a third birth, also `refused_ambiguous`.
  - That gives 24 births in total (3 per sequence × 8), all `refused_ambiguous`.
- There were 0 silent re-binds.

Rung-1 and rung-2 holds (non-minted checks; Wilson 95%):

| td | Exposure | Rung 1, all | Rung 1, non-anchor | Rung 2, all | Rung 2, non-anchor |
|---|---|---|---|---|---|
| 100 | D65 | 40/80 = 0.50 [0.39, 0.61] | 32/72 = 0.44 [0.34, 0.56] | 56/80 = 0.70 [0.59, 0.79] | 48/72 = 0.67 |
| 100 | A | 16/80 = 0.20 [0.13, 0.30] | 8/72 = 0.11 [0.06, 0.20] | 64/80 = 0.80 [0.70, 0.87] | 56/72 = 0.78 |
| 100 | E_return | 80/80 | 72/72 | 80/80 | 72/72 |
| 1000 | D65 | 8/80 = 0.10 [0.05, 0.19] | 0/72 [0, 0.051] | 64/80 = 0.80 [0.70, 0.87] | 56/72 = 0.78 |
| 1000 | A | 8/72 = 0.11 [0.06, 0.20] | 0/64 [0, 0.057] | 40/72 = 0.56 [0.44, 0.67] | 32/64 = 0.50 |
| 1000 | E_return | 72/72 | 64/64 | 72/72 | 64/64 |

- At 1000 td, 16 minted checks under A and 8 at E_return were excluded. These are the newly born pair halves and the re-merged pair.
- **Per-layout counts are identical for every layout.** For example, at 100 td under D65 every layout gives rung 1 = 5/10, non-anchor = 4/9 and rung 2 = 7/10. See the Anomaly section.
- The anchor was patch 1 (white, sid 1) in all 48 frames, and rung 1 held on it in 48/48 [0.926, 1.000].

Median per-surface look hue-angle change against exposure 1 (n = 72 patch instances per cell, 9 per layout):

| td | E→D65 | E→A | E→E_return |
|---|---|---|---|
| 100 | 4.47° | 4.24° | 0.26° |
| 1000 | 4.58° | 2.41° | 1.48° |

Under A, blue and purplish blue reverse hue (170–178°).

### B2 adaptation (E; 20 × (E + 610 nm, 2000 quanta per cell); E)

| td | Surface | rg at exp 1 | rg at exp 22 | by at exp 1 → 22 | Rung 1 at 22 (resid_max) | Rung 2 at 22 | Same sid at 1 and 22 |
|---|---|---|---|---|---|---|---|
| 100 | neutral (bg) | +0.0151 | −0.0206 | −0.0419 → −0.0035 | holds (0) | holds_pooled | yes |
| 100 | white | +0.0441 | −0.0578 | −0.1528 → −0.0233 | holds (0) | holds_pooled | yes |
| 1000 | neutral (bg) | +0.0508 | −0.0713 | −0.1792 → −0.0087 | holds (0) | holds_pooled | yes |
| 1000 | white | +0.0332 | −0.0459 | −0.1830 → −0.0173 | holds (0) | holds_pooled | yes |

These values are identical in all 8 layouts, so the counts are 32/32.

During adaptation (exposures 2–21), the checks were:

- at 100 td: 80 refused / 20 hold;
- at 1000 td: 180 refused / 20 hold.

At 100 td the overlay merged 5 of the 10 surfaces into fewer segments during exposures 2–21 (5 segments instead of 10). Those 5 surfaces (patches 2, 3, 8, 9, 10) were re-born at exposure 22. Neutral and white kept their sids.

### B3 eyelid ganzfeld

All 6 conditions (E, D65 and A, each at 1000 and 10⁴ td) gave the same counts:

- LookingEpisode 1 and FieldLook 1;
- SurfaceLook 0, ColourProperty 0, PropertyCheck 0, FrameStats 0;
- `presents_property` 0 and `presents_unrecognised` 0.

The FieldLook rg was +0.0030 to +0.0067 at 1000 td and +0.027 to +0.059 at 10⁴ td. In every condition rg > 0 and by < 0.

### B4 swap falsifier

| | Result |
|---|---|
| Sequences where every patch's sid followed position | 16/16 |
| Swapped surfaces, rung 1 | 32/32 refused |
| Swapped surfaces, rung 2 | 32/32 refused_pooled |
| Other surfaces, rung 1 | 8/8 hold in every sequence |
| Other surfaces, rung 2 | 8/8 holds_pooled in every sequence |

- The pair was blue and yellow in every layout. Positions were (8,10), (4,5), (4,9), (3,9), (4,5), (2,3), (5,10) and (2,9) for k = 1…8.
- ΔL+M was 239.7 at 100 td and 2396.9 at 1000 td.

### B5 motion (patch 10; +1 column × 4, then +6)

All 16 sequences behaved the same way:

- The moved patch kept its sid (9) through all four 1-column steps.
- At the jump it got a new sid (10), born that epoch. Its segment was a birth with reason `refused_ambiguous`: it claimed the background surface but lost to the background's own segment.
- The old sid had status `coasting`, coast 1.
- Every other patch kept its sid throughout.

### B6 Mary room → release

Node and edge counts by stage-4.5 type are identical in all 16 sequences:

| Phase end | ColourProperty | FrameStats | PropertyCheck | LookingEpisode | SurfaceLook | FieldLook | presents_property | presents_unrecognised |
|---|---|---|---|---|---|---|---|---|
| After room (8 exposures) | 27 | 6 | 54 | 8 | 54 | 2 | 54 | 0 |
| After release (+3) | 30 | 9 | 84 | 11 | 84 | 2 | 69 | 15 |

- **Room.** Each ganzfeld blanks all `cur_sid`, so the 9 room surfaces are re-born after each lid. That gives 3 × 9 = 27 properties, all minted from neutral catches. Every later room check held, so no `presents_unrecognised` edge was ever made in the room.
- **Release, exposure 1.**
  - 7 surfaces continued their room sid by overlap, because the geometry is the same.
  - 2 of those held against their room property: the background and slot 1, which are the same reflectance in room and release.
  - The 5 continuing chromatic surfaces were refused. Their looks link `presents_unrecognised` to the old neutral property.
  - 3 surfaces were born and minted new ColourProperties: slot 4, slot 10 and the merged pair 6+7. Slots 4 and 10 were neutral 5 in the room, so they had been part of the background.
- **Release, exposures 2–3.** 5 hold and 5 refused.
- **Types.** The node types after the release equal those after the room. The release adds one edge type, `presents_unrecognised`.
- **Chromatic patches.** 4 of the 9 chromatic patches per sequence got a ColourProperty minted in the release, giving 64/144.

### B7 Poisson (k = 1, 2; seeds 7001–7005)

- **Segment counts.** In all 16 (layout, td, exposure) cells, the median over 5 seeds was 65–88, against a deterministic count of 10 or 11.
- **Sid continuity.** The fraction of cells keeping their exposure-1 sid fell to 0.31–0.52 by exposure 2 (first seeds shown in the JSON).
- **Rung-1 refusal** over non-minted checks:
  - 100 td: Poisson 646/656 = 0.985 [0.972, 0.992] against deterministic 26/60 = 0.433 [0.316, 0.559];
  - 1000 td: Poisson 719/723 = 0.994 [0.986, 0.998] against deterministic 34/56 = 0.607 [0.476, 0.724].
- **Minted checks** (new fragments) excluded: 1589 at 100 td and 1603 at 1000 td.
- **Rung-2 refusal** (recorded): Poisson 0.226 and 0.213 against deterministic 0.167 and 0.214.

## Predictions — verdicts

| | Verdict | Key numbers |
|---|---|---|
| **P1** identity is colour-free | **supported** | B1: non-exempt patches stable 144/144; exempt set = the declared pair; 0 silent re-binds; all 24 split/merge births `refused_ambiguous`. B4: sids follow position 16/16. B5: steps keep the sid and the jump births a new sid while the old one coasts, 16/16 |
| **P2** looks change with viewing | **partially** | **B1 hue clause NOT SUPPORTED**: the median E→A change is *smaller* than E→D65 at both td (100 td: 4.24° vs 4.47°; 1000 td: 2.41° vs 4.58°), although both are > 0. B2 clause supported: rg(22) < rg(1) for neutral and white, 32/32 |
| **P3** properties hold only within the stated class | **supported** | Rung 1 held on the anchor in 48/48 frames. Non-anchor rung 1: 100 td 40/144 = 0.278 ≥ 1000 td 0/136 = 0; A ≤ D65 at 100 td (0.111 ≤ 0.444) and at 1000 td (0 ≤ 0, trivially). Rung 2 ≥ rung 1 in 48/48 conditions. B2: holds at 22 with looks shifted, 32/32. B4: swapped refused, 32/32 |
| **P4** episodes without properties | **supported** | 6/6 exposures: 1 LookingEpisode, 1 FieldLook, and 0 SurfaceLook, ColourProperty, PropertyCheck and link edges |
| **P5** release adds instances, not kinds | **partially** | **(a) no new types: NOT SUPPORTED**, 0/16; `presents_unrecognised` first appears at release. **(b) new ColourProperty for chromatic surfaces: partially**, 64/144 chromatic patches (4/9 per sequence). (c) new SurfaceLooks and `presents_property` edges: supported, 16/16 (+30 looks, +15 `presents_property`) |
| **P6** Poisson fragments (a limitation, not a success criterion) | **supported** | Median segments > deterministic in 16/16 cells (65–88 vs 10–11). Rung-1 refusal Poisson ≥ deterministic: 0.985 vs 0.433 at 100 td, 0.994 vs 0.607 at 1000 td |

Notes on the verdicts:

- **P3, 1000 td.** The A ≤ D65 comparison passes only because both fractions are 0. At 1000 td no non-anchor surface holds rung 1 under any changed illuminant.
- **P5 (a).** The failure is structural. A room scene that never changes illuminant or content cannot produce a rung-1 refusal, so the `presents_unrecognised` edge type can first appear only at release.
- **P5 (b).** The failure is also structural. The release reuses the room geometry, so 5 of the chromatic surfaces keep their room identity. Their properties are not re-minted, by design: a property is minted once, at first sight. Their looks are linked as unrecognised to the old neutral property instead.

## Development layout (seed = None), reported separately

The development layout gives exactly the same per-surface numbers as every
held-out layout:

- B1: 9 hue instances per cell with the same medians (100 td: 4.47° / 4.24°; 1000 td: 4.58° / 2.41°); rung 1 at D65 = 5/10 at 100 td and 1/10 at 1000 td; anchor 6/6.
- B2: the same rg values; holds at 22.
- B4: pair (4, 5), blue/yellow, both refused.
- B5: ok, with the moved patch being dark skin.
- B6: the same counts.

It is in the JSON under `analysis.B1.development` and under `layout: null` in each arm's per-sequence list.

## Anomaly: held-out layouts are not independent of the development layout

The held-out layouts were meant to be new scenes. They permute reflectances among
fixed slots, and every non-pair patch is separated by background gutters. The
eye, segmentation, identity and both property rungs are all invariant to where a
patch sits:

- the frame anchor is a max over surfaces;
- the rung-2 pool is leave-one-out over the frame;
- adjacency to the background is the same for every slot.

So **every per-surface outcome in B1, B2 and B7 is identical across all 9
layouts, the development layout included.** This was verified: status and hue
change for each (td, exposure, reflectance) do not vary across layouts.

Consequences:

- The "pooled over k = 1…8" n values (for example 72) are 8 copies of 9–10 surfaces. The Wilson intervals therefore overstate precision by about √8. The effective n is the 9–10 surfaces of one scene.
- The "held-out" confirmatory evidence for B1/B2 is distributionally the development scene that the build had already observed. For example, the build reported rung 1 holding 1/10 under D65 at 1000 td, and the battery found the same.
- B4 and B6 vary only in which positions carry which reflectance. In B4 the selected pair is blue/yellow every time.
- The verdicts are reported as computed. They should be read as "holds for this one set of 10 surfaces", not as generalisation over scenes.

## Deviations

1. **Smoke runs before the battery.** Two `--smoke` runs and one analysis-only re-entry were used for crash-testing. Each ran one development-layout sequence per arm at 1000 td, wrote to `/tmp`, and printed no verdicts. The verdict code was exercised on development data with its result discarded. After the first smoke run, the script gained a raw checkpoint (`--from-raw`) and parametrised verdict code. No analysis rule changed. The full run used the final script (sha `de2dcad2…`) unchanged.
2. **Script hash not embedded in the JSON.** The broad study recommends hashing the analysis script into the freeze before eye contact. Here the hash was taken by hand at launch, after the smoke runs, and is recorded only in this document. That the rules were fixed before the confirmatory outputs is supported by the run log, which prints `RULES` first, and by the unchanged hash. It is not certified by a pre-run freeze.
3. **"Five seed flags."** Read as the adapter's enabled flags for segmentation, persistence, colour and looking, plus `pooled`. `look_property_link` has no flag. `pooled` = 1 in every arm, not only for rung-2 reporting, as in the adapter default and the build tests.
4. **Determinism was checked by re-running B1 and B3**, not the whole battery.
5. **B7 refusal pool.** P6 clause 2 pools exposures 2–4, including E_return. P3's td clause pools D65 + A. Both were fixed in `RULES`.
6. **No arm was left unrun.** No API gap was found.

## Not preregistered

These are descriptive extras computed from the same raw records, with no new
exposures. They change no verdict.

- **Euclidean look shift |Δ(rg, by)| against exposure 1** (median, n = 72):

  | td | D65 | A | E_return |
  |---|---|---|---|
  | 100 | 0.0047 | 0.027 | 0.0019 |
  | 1000 | 0.023 | 0.093 | 0.053 |

  By this measure the look moves 4–6× more under A than under D65. The hue-angle metric misses this. Under E the eye's looks already lie in the (+rg, −by) quadrant; for example, white is (+0.044, −0.153) at 100 td. A mainly scales them along that direction, so their angle barely changes. Blue and purplish blue cross the origin and flip by about 175°. So the P2 hue failure reflects the angle metric on this eye, not looks that fail to change.
- **Per-reflectance B1 status**, identical in every layout:
  - Rung 1 under D65 at 100 td holds for white, neutral 5, green, dark skin and the merged pair 6+7.
  - Under A at 100 td it holds only for white and neutral 5.
  - At 1000 td it holds only for white under both D65 and A.
  - Rung 2 refuses red and blue under both illuminants at both td.
- **B2 identity at 100 td.** 5 of 10 surfaces lost identity during the overlay (described under B2).
- **Room re-birth at each lid.** Persistence does not survive a ganzfeld, because there is no re-acquisition of coasting surfaces (a declared non-coverage). The room therefore minted 27 properties for 9 surfaces.

## Interpretation (model-level only)

Within this model and this one set of 10 ColorChecker surfaces:

- **Identity.** Surface identity bound by luminance-edge overlap ignores the chromatic content it carries: swaps, illuminant changes and motion all behave as the criterion requires (P1). Isoluminant splits and merges are refused rather than guessed.
- **Properties versus looks.** Properties are checked against their own rounding bound and are refused when the eye's non-diagonal sensors break von Kries. That happens almost always at 1000 td and often at 100 td. The leave-one-out pooled rung recovers most surfaces (P3). Adaptation moves the looks of neutral surfaces while their catch-based checks hold exactly (P2-B2, P3-B2).
- **The lid.** A closed-eyelid ganzfeld gives an episode and a field look with no surface or property (P4).
- **Mary's release.** In this graph, release does not mostly add new properties. Surfaces whose identity carries over from the room have their old achromatic property refused and their looks linked as `presents_unrecognised`. Only newly segmented surfaces mint a chromatic property. That the release adds a kind of edge not instantiated in the room is a result about this design: a constant room can never trigger a refusal.

These are statements about computed graph states. A `SurfaceLook` is a mean of
computed opponent signals, not an experience, and none of this bears on human
qualia. The layout-invariance anomaly limits generalisation to the single
surface set tested.

## Raw outputs

- `results/marys_room_stage4_battery.json`. Keys:
  - `git`, `engine_provenance`, `rules`, `declared_choices`, `determinism`, `perf`;
  - `analysis` (per-arm per-sequence records and summaries) and `verdicts`;
  - `raw` (every exposure: sid grid, Y grid for B1/B4, segments, surfaces, checks, looks, field looks, frames, properties, counts and patch→sid map).
- `results/marys_room_stage4_battery_summary.csv`. One row per summary quantity, with k, n and the Wilson interval where applicable.
- Run log: `/tmp/marys_room_stage4_run.log`. Raw checkpoint: `/tmp/marys_room_stage4_raw_checkpoint.json`. Both are outside the repo.

## Replication (A1)

A preregistered replication on 16 independent `random_mondrian` layouts (amendment `docs/experiments/marys-room-stage4-amendment-A1.md`, engine `ed9237c97f20`, HEAD `e2311007`) is reported in `docs/experiments/marys-room-stage4-replication-results.md`. Distinct per-layout outcome profiles were 16/16 for R1 and R7, 15/16 for R4 and 8/8 for R6, so the anomaly above does not recur there; R2 (2/16) and R5 (4/16) remain weakly independent. The verdicts were P1 partially (40 silent re-binds from unequal merges continuing the larger parent's sid, a case this battery's symmetric pair never exercised), P2 partially (the hue clause fails again), P3 partially (anchor 0.75, every failure in a layout without a single anchor surface), P4 supported, P5 partially ((a) 0/16, (b) 0/96) and P6 supported. The data-informed Euclidean-shift prediction (Q1) and Q2–Q4 for the new flags were supported.
