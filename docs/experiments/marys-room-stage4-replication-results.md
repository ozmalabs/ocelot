# Mary's Room stage 4: preregistered replication (amendment A1) — RESULTS

This is the confirmatory replication run under
`docs/experiments/marys-room-stage4-amendment-A1.md` (committed with the runner at
`e2311007`). It covers the replication arms R1–R7 (predictions P1–P6, verbatim from
`docs/experiments/marys-room-stage4-prereg.md`) and the new arms N1–N5 (predictions Q1–Q5).

- Runner: `scripts/marys_room_stage4_replication.py`. It reuses the original analysis functions (`an_b1` … `verdicts`) of `scripts/marys_room_stage4_battery.py` without modifying them.
- Outputs:
  - `results/marys_room_stage4_replication.json` (81 MB). It holds freeze, provenance, `RULES` and `RULES_A1`, declared choices, per-arm analyses, cluster statistics, profiles, verdicts and every raw record. In git it is stored gzip-compressed as `results/marys_room_stage4_replication.json.gz` (7.5 MB). Decompress with `gunzip -k`; the decompressed sha256 is `e019f91f40594bc21b30655eec6c3ffb7871da2d10ec2b38e96dcf630bf83af4`.
  - Raw checkpoint: `/tmp/marys_room_stage4_replication_raw.json`. Run log: `/tmp/a1_run.log`. Both are outside the repo.

As in stage 4, "look" means the computed `SurfaceLook` / `FieldLook` and "property" means the graph's `ColourProperty`. Nothing here measures experience or human colour vision.

## 1. Provenance and integrity

- **git HEAD** `e2311007a490…` ("research: preregister Mary's Room stage 4 replication (amendment A1)"). The base commit `3460f381` is an ancestor. No commits were made during or after the run.
- **Freeze check** (`freeze` in the JSON; all passed before any exposure):
  - `git ls-files --error-unmatch` over the 43 `FREEZE_TRACKED` paths exited 0;
  - `git diff --quiet HEAD -- <paths>` exited 0 with no changed names;
  - no untracked files under those paths;
  - the combined `data/colour/**` sha256 was `8e567ebe…5f`, equal to the expected value. The 19 per-file hashes are embedded.
- **Engine** `ed9237c97f20` (`runners/dsl/python/substrate_rs/_native.abi3.so`, sha256 `ed9237c9…d436`; `_native.build.json` sha256 `ad298af7…a77dc7`). Source fingerprint match `own`, no stale Rust, 1 other tree build shadowed (as in stage 4).
- **Runner script** sha256 `29613b77bb8f3c236b6b6f407c1b19672fab801b0b9dc31c05798726657dcacd`, embedded in the JSON and printed at launch. Amendment sha256 `f39659fd…e7`. This addresses original Deviation 2.
- **Runtime.** 45.7 min wall (2741.9 s).
  - 3030 battery exposures, the arm total of the §8 dry-run plan. The perf count (`perf.exposures`) is taken over the arms' raw records, so the determinism re-run (planned at 134 exposures) is not part of it.
  - Mean 0.673 s per exposure, maximum 1.63 s.
  - 544 world builds (mean 0.067 s). This equals the plan including the determinism re-run.
  - The runtime is inside the preregistered estimate of 32–83 min.
- **Determinism (A17).** After all arms, R1 and R3 were re-run in fresh worlds. The raw sha256 values (timings excluded) were identical: R1 `a53fef2c…7907`, R3 `99d14526…45be`. Whole raw payload `7d90cc67…bb`.

## 2. Independence of layouts

The A15 distinct per-layout outcome profiles were:

| Arm | Distinct profiles | Stage 4 |
|---|---|---|
| R1 constancy | 16/16 | 1 |
| R2 adaptation | 2/16 | 1 |
| R4 swap | 15/16 | 1 |
| R5 motion | 4/16 | 1 |
| R6 room→release | 8/8 | 1 |
| R7 Poisson | 16/16 | 1 |

- **R1, R6, R7 (16/16, 8/8, 16/16).** Every layout gives a different outcome profile. The stage-4 anomaly (one scene copied eight times) is not reproduced. The layout is the effective unit, and the layout-cluster bootstrap below is the honest interval for these arms.
- **R4 (15/16).** Only layouts 114 and 116 share a profile (all sids follow, both swapped refused, 6/6 others hold at both td). R4 is effectively independent.
- **R2 (2/16): limited independence.**
  - The A15 profile is binary: status at 22, pooled status at 22, rg(22) < rg(1) and same sid. It saturates. Every role in every layout holds, holds_pooled, drops in rg and keeps its sid. The only second profile is layout 109, which has no "white" role.
  - The continuous values carry little more information. The white-role look depends on the reflectance alone: 5 distinct (rg1, rg22) values for 5 reflectances over 15 layouts.
  - The 8 even-seed white 9.5 patches all reproduce the stage-4 white values exactly: +0.0441 → −0.0578 at 100 td and +0.0332 → −0.0459 at 1000 td.
  - The neutral role (the background) has 10 (100 td) and 8 (1000 td) distinct value pairs over 5 background neutrals.
  - R2's 62/62 is therefore closer to "5 neutrals × a few contexts" than to 62 independent surfaces.
- **R5 (4/16): limited independence.**
  - The A6 rule selects a patch whose rect overlaps no other declared rect at any offset. In practice that is a patch surrounded by background, which recreates the stage-4 gutter configuration.
  - In that configuration the outcome does not depend on the layout: 12 of 16 layouts give the same "all ok" profile at both td.
  - The other profiles come only from moved patches that the background segment had absorbed from exposure 1 (sid 0 throughout): 147 (bluish green, both td), 178 (dark skin, 100 td only) and 189 (blue sky, both td).
  - R5 therefore tests one geometric situation (an isolated patch on background) plus one failure mode (the patch is merged into the background).
- **R3** has no layout (it is a ganzfeld). It is a re-execution on the new engine, not a test on new scenes.

## 3. Verdicts

Verdict rules R9 and R10 apply, as in stage 4. The decision is made on point estimates. "Boot" is the layout-cluster percentile bootstrap (B = 10000, `default_rng(20261006)`, no resamples dropped).

### Replication (P1–P6, verbatim prereg predictions on R1–R7)

| | Replication verdict | Key numbers (replication) | Stage-4 battery |
|---|---|---|---|
| **P1** identity is colour-free | **partially** | **R1: not supported.** Non-exempt patches stable 233/233 = 1.00 (Wilson [0.984, 1.000], boot [1, 1]); all patches 274/294 = 0.932 [0.897, 0.956]; 20 births, all `refused_ambiguous`; but **40 silent re-binds** (§4). **R4: partially**, sids follow position in 19/32 = 0.594 [0.423, 0.745], boot [0.406, 0.781]. **R5: partially**, 27/32 = 0.844 [0.682, 0.931], boot [0.656, 1.0]; steps keep the sid 32/32, jump born 27/32, old sid coasts 29/32; primary layouts alone 8/8 (supported) | supported. 144/144 non-exempt stable; 0 silent re-binds; 24 births `refused_ambiguous`; B4 16/16; B5 16/16 |
| **P2** looks change with viewing | **partially** | **Hue clause not supported**: median E→A < E→D65 at both td. 100 td: 4.25° (n 104, boot [3.99, 4.98]) vs 4.47° (n 113, boot [3.52, 4.95]). 1000 td: 3.08° (n 131, boot [2.41, 3.27]) vs 4.35° (n 133, boot [4.33, 4.61]). Both > 0. **R2 clause supported**: rg(22) < rg(1) for 62/62 [0.942, 1.000], boot [1, 1] | partially. Hue 4.24° vs 4.47° and 2.41° vs 4.58°; B2 32/32 |
| **P3** properties hold only within the stated class | **partially** | **Anchor clause partially**: 72/96 = 0.75 [0.655, 0.826], boot [0.50, 0.94]. A18 secondary: 72/72 on the 12 single-anchor layouts. **Non-anchor fractions supported**: 100 td 74/228 = 0.325 [0.267, 0.388] ≥ 1000 td 9/255 = 0.035 [0.019, 0.066]; A ≤ D65 at 100 td (26/112 = 0.232 ≤ 48/116 = 0.414) and at 1000 td (1/127 = 0.008 ≤ 8/128 = 0.063). **Rung 2 ≥ rung 1 partially**: 95/96 conditions. **R2 holds at 22 supported**: 62/62. **R4 swapped refused partially**: 52/64 = 0.813 [0.700, 0.889], boot [0.656, 0.953] | supported. Anchor 48/48; non-anchor 0.278 ≥ 0; A ≤ D65 0.111 ≤ 0.444 and 0 ≤ 0; 48/48; 32/32; 32/32 |
| **P4** episodes without properties | **supported** | 6/6 exposures: 1 LookingEpisode, 1 FieldLook, and 0 SurfaceLook, ColourProperty, PropertyCheck, FrameStats and link edges. FieldLook rg +0.0030 to +0.0067 (1000 td) and +0.027 to +0.059 (10⁴ td), with by < 0 | supported, with identical values |
| **P5** release adds instances, not kinds | **partially** | **(a) no new types: not supported**, 0/16; `presents_unrecognised` is new at release. **(b) new ColourProperty for chromatic surfaces: not supported**, 0/96 [0, 0.038], boot [0, 0]. **(c) new SurfaceLooks and `presents_property`: partially**, 8/16 | partially. (a) 0/16; (b) 64/144; (c) 16/16 |
| **P6** Poisson fragments (a limitation, not a success criterion) | **supported** | Median segments > deterministic in 128/128 cells (medians 48–77 vs 6–11). Rung-1 refusal, Poisson vs deterministic: 100 td 3343/3546 = 0.943 (boot [0.922, 0.963]) vs 154/375 = 0.411 (boot [0.365, 0.458]); 1000 td 3953/3975 = 0.994 (boot [0.991, 0.997]) vs 247/418 = 0.591 (boot [0.570, 0.612]). Minted checks excluded: 10968 and 11136 | supported. 16/16 cells (65–88 vs 10–11); 0.985 vs 0.433; 0.994 vs 0.607 |

Checked against the A1 wording:

- **P1.** By R5 (stage-4 `RULES`, applied verbatim), the B1 clause requires both that non-exempt patches are stable *and* that there is no silent re-bind. The 40 re-binds alone make it "not supported". Combined with B4 and B5 (both partial) under R10, P1 is "partially".
- **P3.** A1 §3 predicted before exposure that the anchor clause "cannot be fully supported". All 24 failing frames are the 6 frames each of layouts 101, 103, 105 and 109, where no sid holds the frame anchor. The A18 restriction is reported only as secondary.
- **P5.** A1 §3 stated that (a) and (b) carry the structural failures diagnosed in stage 4 and would be evaluated verbatim. They were.
- **P6.** Supported, but per the prereg this is a limitation, not a success.

### New predictions (Q1–Q5, A1 §6)

| | Verdict | Key numbers | Stage-4 comparison |
|---|---|---|---|
| **Q1** Euclidean look shift A > D65 (data-informed) | **supported** | Median \|Δ(rg, by)\| vs exposure 1. 100 td: A 0.0278 (n 104, boot [0.0269, 0.0353]) > D65 0.0074 (n 113, boot [0.0067, 0.0078]). 1000 td: A 0.147 (n 131, boot [0.097, 0.149]) > D65 0.0253 (n 133, boot [0.0227, 0.0284]) | Not preregistered there: 0.027 vs 0.0047 and 0.093 vs 0.023 (one scene) |
| **Q2** N1 re-acquires ≥ 90% per cell | **supported** | GG 100 td 147/147 and GG 1000 td 147/147 (Wilson [0.975, 1], boot [1, 1]). ES 100 td 135/147 = **0.918** [0.863, 0.953], boot [0.878, 0.957]. ES 1000 td 140/147 = 0.952 [0.905, 0.977], boot [0.906, 0.987]. Intermediate exposures blank in 64/64 sequences | No re-acquisition existed; the stage-4 room re-minted 27 properties for 9 surfaces |
| **Q3** N2 recall answers every cue, with no new looks | **supported** | 32/32 sequences. 269/269 non-control cues `recalled`. Cues created 0 nodes or edges of every stage-4.5 type, including 0 LookingEpisode and 0 SurfaceLook. Control cue (sid 10⁶): `no_property` / `no_surface` in 32/32 | n/a |
| **Q4** N3 concept accuracy > majority rate | **supported** | 100 td: 61/79 = **0.772** [0.668, 0.851], boot [0.697, 0.852], vs p0 = **0.430**; binomial p = 6.5e-10. 1000 td: 75/97 = **0.773** [0.680, 0.845], boot [0.696, 0.849], vs p0 = 0.423; p = 2.2e-12. All scored patches `categorised` | n/a |
| **Q5** N4 motion route (no prediction) | report only | 52 sequences (26 flag-on/flag-off pairs). 8/52 sequences, all flag-on, contain a motion segment and a carve polygon. 18/26 pairs have identical sid grids with the flag on and off. Details in §8 | Stage-4 fix: no motion group for the isoluminant patch |

## 4. P1: the 40 silent re-binds

### Definition used (verbatim from the original battery)

`RULES.R4_silent_rebind` in `scripts/marys_room_stage4_battery.py`:

> A silent re-bind = a SurfaceSegment with decision 'continue' at exposure t whose sid covers a different SET of ground-truth patches at t than at t-1. A refused split/merge = the affected cells' segment is a 'birth' (birth_reason recorded).

The code (`an_b1`) works as follows:

- `composition(snap)` maps each sid to the set of declared patches that have **at least one cell** carrying that sid, using `patch_sids`.
- For every exposure t ≥ 1 and every segment with `decision == "continue"`, it compares `comps[t-1][sid]` with `comps[t][sid]`. Any difference is a re-bind: growth, shrinkage or exchange.
- `RULES.R5_P1_B1` makes P1-B1 supported only if there are no non-exempt unstable patches **and** no silent re-binds. Exempt patches may change sid, but even an exempt patch's change counts if it happens through a `continue` segment.

### What the 40 are

The investigation used the stored raw R1 records only, with no new exposures. Patch identity of cells came from `spectral_scene.random_mondrian(seed).label_map()`, which is geometry only and does not touch the eye.

- **Scope.** The 40 events occur in 16 of 32 R1 sequences across 11 layouts: 101, 102, 104, 105, 106, 108, 109, 110, 111, 112 and 115.
- **Timing.** By transition: E→D65 6, D65→A 18, A→E_return 16.
- **Exempt patches.** Every patch involved is in that sequence's R3 exempt set: it has a border pair within the shot-noise join criterion. Non-exempt identity is perfect (233/233).
- **Whole patches.** In every event, whole patches move. Each patch's cells carry a single sid before and after, so no event involves a partial patch.
- **Pairs.** Every event is one half of a pair. The same (sid, patch) leaves and rejoins, or joins and leaves, within the sequence.

The events fall into two mechanisms, 20 each:

- **M, merge-continuation (20; 12 "M-re", 8 "M-first").** At t, one segment's member cells come wholly from two previous sids. Each parent's overlap is 100% of that parent.
  - The segment continues the **larger** parent's sid. The smaller parent is not accepted: it coasts with `claims = 1` and `coast = 1`, and is never marked `split` or refused.
  - So the absorbed patch's cells now carry a sid that, at t−1, denoted a different patch, and nothing in the graph records a refusal.
  - In 12 cases the absorbed sid had been born from an earlier split in the same sequence (re-merge, M-re). In 8 cases the two surfaces had been separate since exposure 1 (first merge, M-first).
  - The continuing sid's own property check then ran against the larger parent's property. Rung 1 held in 10/20 and rung 2 in 13/20.
- **S, split with majority continuation (20).** At t, the cells of one previous sid are divided between two current segments.
  - The part holding the majority keeps the sid. Its share of the parent ranges from 40/75 (53%) to 271/286 (95%).
  - The shed patch is **born `refused_ambiguous`**. These are exactly the 20 recorded births.
  - No patch's cells acquire another patch's sid. The event counts under R4 only because the continuing sid now covers fewer patches.

**No case is "a patch whose segment changed to include a different patch" without a merge.** Every growth event is a full two-parent merge (type M).

Why stage 4 had 0 re-binds:

- Its only criterion-boundary pair, patches 6 and 7 of `standard_mondrian`, has two equal rects of 16 cells each.
- At 100 td the pair stayed merged throughout, so there was no change.
- At 1000 td the A-split was an exact tie, so both halves were born and the merged sid coasted as `split`. The E_return re-merge combined two equal parents, also a tie, so it too was born.
- The unequal case was never exercised.

### Classification of all 40

In the table, "(k/n)" is a parent's overlap with the segment over that parent's size at t−1. Check = the continuing sid's rung-1 / rung-2 status at t.

| # | Layout | td | Transition | sid | Patches t−1 → t | Type | What the segmentation did | Check |
|---|---|---|---|---|---|---|---|---|
| 1 | 101 | 1000 | D65→A | 0 | [0, 1] → [0] | S | split: sid 0 keeps 212/224 cells; patch 1 blue sky (12 cells) born sid 8, refused_ambiguous | refused / holds_pooled |
| 2 | 101 | 1000 | A→E_return | 0 | [0] → [0, 1] | M-re | merge: sid 0 (212/212) + sid 8 (12/12) → continues sid 0; sid 8 coasting, no refusal; absorbed patch 1 blue sky | holds / holds_pooled |
| 3 | 102 | 100 | D65→A | 0 | [0, 6] → [0, 6, 7] | M-first | merge: sid 0 (196/196) + sid 7 (36/36) → continues sid 0; sid 7 coasting, no refusal; absorbed patch 7 purplish blue | refused / holds_pooled |
| 4 | 102 | 100 | D65→A | 4 | [4, 8] → [4] | S | split: sid 4 keeps 40/75 cells; patch 8 green (35 cells) born sid 8, refused_ambiguous | refused / refused_pooled |
| 5 | 102 | 100 | A→E_return | 0 | [0, 6, 7] → [0, 6] | S | split: sid 0 keeps 196/232 cells; patch 7 purplish blue (36 cells) born sid 9, refused_ambiguous | holds / holds_pooled |
| 6 | 102 | 100 | A→E_return | 4 | [4] → [4, 8] | M-re | merge: sid 4 (40/40) + sid 8 (35/35) → continues sid 4; sid 8 coasting, no refusal; absorbed patch 8 green | holds / holds_pooled |
| 7 | 104 | 100 | E→D65 | 1 | [7, 9] → [9] | S | split: sid 1 keeps 35/63 cells; patch 7 red (28 cells) born sid 8, refused_ambiguous | refused / refused_pooled |
| 8 | 104 | 100 | D65→A | 1 | [9] → [7, 9] | M-re | merge: sid 1 (35/35) + sid 8 (28/28) → continues sid 1; sid 8 coasting, no refusal; absorbed patch 7 red | refused / refused_pooled |
| 9 | 104 | 1000 | D65→A | 2 | [1, 3] → [3] | S | split: sid 2 keeps 12/20 cells; patch 1 purple (8 cells) born sid 10, refused_ambiguous | refused / refused_pooled |
| 10 | 104 | 1000 | D65→A | 9 | [4] → [4, 5] | M-first | merge: sid 9 (20/20) + sid 6 (12/12) → continues sid 9; sid 6 coasting, no refusal; absorbed patch 5 neutral 6.5 | refused / refused_pooled |
| 11 | 104 | 1000 | A→E_return | 2 | [3] → [1, 3] | M-re | merge: sid 2 (12/12) + sid 10 (8/8) → continues sid 2; sid 10 coasting, no refusal; absorbed patch 1 purple | holds / holds_pooled |
| 12 | 104 | 1000 | A→E_return | 9 | [4, 5] → [4] | S | split: sid 9 keeps 20/32 cells; patch 5 neutral 6.5 (12 cells) born sid 11, refused_ambiguous | holds / holds_pooled |
| 13 | 105 | 1000 | E→D65 | 1 | [2, 5] → [5] | S | split: sid 1 keeps 35/50 cells; patch 2 neutral 5 (15 cells) born sid 7, refused_ambiguous | refused / refused_pooled |
| 14 | 105 | 1000 | A→E_return | 1 | [5] → [2, 5] | M-re | merge: sid 1 (35/35) + sid 7 (15/15) → continues sid 1; sid 7 coasting, no refusal; absorbed patch 2 neutral 5 | holds / holds_pooled |
| 15 | 106 | 100 | D65→A | 3 | [6] → [1, 6] | M-first | merge: sid 3 (9/9) + sid 2 (6/6) → continues sid 3; sid 2 coasting, no refusal; absorbed patch 1 orange | refused / refused_pooled |
| 16 | 106 | 100 | A→E_return | 3 | [1, 6] → [6] | S | split: sid 3 keeps 9/15 cells; patch 1 orange (6 cells) born sid 8, refused_ambiguous | holds / holds_pooled |
| 17 | 106 | 1000 | D65→A | 2 | [2, 9] → [9] | S | split: sid 2 keeps 24/33 cells; patch 2 bluish green (9 cells) born sid 9, refused_ambiguous | refused / refused_pooled |
| 18 | 106 | 1000 | A→E_return | 2 | [9] → [2, 9] | M-re | merge: sid 2 (24/24) + sid 9 (9/9) → continues sid 2; sid 9 coasting, no refusal; absorbed patch 2 bluish green | holds / holds_pooled |
| 19 | 108 | 1000 | D65→A | 0 | [0, 4] → [0] | S | split: sid 0 keeps 271/286 cells; patch 4 blue sky (15 cells) born sid 6, refused_ambiguous | refused / refused_pooled |
| 20 | 108 | 1000 | A→E_return | 0 | [0] → [0, 4] | M-re | merge: sid 0 (271/271) + sid 6 (15/15) → continues sid 0; sid 6 coasting, no refusal; absorbed patch 4 blue sky | holds / holds_pooled |
| 21 | 109 | 100 | E→D65 | 1 | [2, 6] → [2] | S | split: sid 1 keeps 22/36 cells; patch 6 red (14 cells) born sid 6, refused_ambiguous | refused / refused_pooled |
| 22 | 109 | 100 | D65→A | 5 | [7] → [5, 7] | M-first | merge: sid 5 (42/42) + sid 2 (27/27) → continues sid 5; sid 2 coasting, no refusal; absorbed patch 5 bluish green | refused / refused_pooled |
| 23 | 109 | 100 | A→E_return | 1 | [2] → [2, 6] | M-re | merge: sid 1 (22/22) + sid 6 (14/14) → continues sid 1; sid 6 coasting, no refusal; absorbed patch 6 red | holds / holds_pooled |
| 24 | 109 | 100 | A→E_return | 5 | [5, 7] → [7] | S | split: sid 5 keeps 42/69 cells; patch 5 bluish green (27 cells) born sid 7, refused_ambiguous | holds / holds_pooled |
| 25 | 109 | 1000 | D65→A | 0 | [0, 9] → [0] | S | split: sid 0 keeps 196/211 cells; patch 9 blue sky (15 cells) born sid 9, refused_ambiguous | refused / refused_pooled |
| 26 | 109 | 1000 | A→E_return | 0 | [0] → [0, 9] | M-re | merge: sid 0 (196/196) + sid 9 (15/15) → continues sid 0; sid 9 coasting, no refusal; absorbed patch 9 blue sky | holds / holds_pooled |
| 27 | 110 | 100 | D65→A | 0 | [0, 5, 9] → [0, 9] | S | split: sid 0 keeps 240/259 cells; patch 5 red (19 cells) born sid 9, refused_ambiguous | holds / refused_pooled |
| 28 | 110 | 100 | A→E_return | 0 | [0, 9] → [0, 5, 9] | M-re | merge: sid 0 (240/240) + sid 9 (19/19) → continues sid 0; sid 9 coasting, no refusal; absorbed patch 5 red | holds / holds_pooled |
| 29 | 110 | 1000 | E→D65 | 6 | [9] → [5, 9] | M-first | merge: sid 6 (49/49) + sid 5 (19/19) → continues sid 6; sid 5 coasting, no refusal; absorbed patch 5 red | refused / refused_pooled |
| 30 | 110 | 1000 | D65→A | 6 | [5, 9] → [9] | S | split: sid 6 keeps 49/68 cells; patch 5 red (19 cells) born sid 11, refused_ambiguous | refused / holds_pooled |
| 31 | 111 | 100 | D65→A | 0 | [0] → [0, 5] | M-first | merge: sid 0 (214/214) + sid 5 (20/20) → continues sid 0; sid 5 coasting, no refusal; absorbed patch 5 purplish blue | holds / holds_pooled |
| 32 | 111 | 100 | A→E_return | 0 | [0, 5] → [0] | S | split: sid 0 keeps 214/234 cells; patch 5 purplish blue (20 cells) born sid 10, refused_ambiguous | holds / holds_pooled |
| 33 | 112 | 100 | E→D65 | 5 | [1, 7] → [7] | S | split: sid 5 keeps 18/23 cells; patch 1 orange yellow (5 cells) born sid 7, refused_ambiguous | refused / refused_pooled |
| 34 | 112 | 100 | D65→A | 5 | [7] → [1, 7] | M-re | merge: sid 5 (18/18) + sid 7 (5/5) → continues sid 5; sid 7 coasting, no refusal; absorbed patch 1 orange yellow | refused / holds_pooled |
| 35 | 115 | 100 | E→D65 | 4 | [1, 5] → [5] | S | split: sid 4 keeps 18/24 cells; patch 1 orange yellow (6 cells) born sid 10, refused_ambiguous | refused / holds_pooled |
| 36 | 115 | 100 | D65→A | 4 | [5] → [1, 5] | M-re | merge: sid 4 (18/18) + sid 10 (6/6) → continues sid 4; sid 10 coasting, no refusal; absorbed patch 1 orange yellow | refused / holds_pooled |
| 37 | 115 | 100 | D65→A | 8 | [6] → [3, 6] | M-first | merge: sid 8 (15/15) + sid 7 (9/9) → continues sid 8; sid 7 coasting, no refusal; absorbed patch 3 green | refused / refused_pooled |
| 38 | 115 | 100 | A→E_return | 8 | [3, 6] → [6] | S | split: sid 8 keeps 15/24 cells; patch 3 green (9 cells) born sid 11, refused_ambiguous | holds / holds_pooled |
| 39 | 115 | 1000 | D65→A | 9 | [6] → [3, 6] | M-first | merge: sid 9 (15/15) + sid 8 (9/9) → continues sid 9; sid 8 coasting, no refusal; absorbed patch 3 green | refused / refused_pooled |
| 40 | 115 | 1000 | A→E_return | 9 | [3, 6] → [6] | S | split: sid 9 keeps 15/24 cells; patch 3 green (9 cells) born sid 11, refused_ambiguous | holds / holds_pooled |

### Is this a defect of the identity criterion?

**Yes, for the 20 merges.**

- The persistence rule (`tools/build_surface_persistence_seed.py`) defines the claim test as: S claims P iff ov(S,P) > 0 and 2·ov(S,P) ≥ min(S.n_cells, P.n_cells).
- S accepts P iff P is S's *unique* overlap argmax and no rival segment claims P with ≥ overlap.
- So a merge is refused only when the two parents tie. When a merged segment has a strict-majority parent, it continues that parent's sid, and the minority parent simply coasts.
- The seed's own description promises that an ambiguous "merge (one segment tied between two Ps)" is refused. The implementation matches that text, but not the prereg's P1 wording ("split or merge and are refused, never silently re-bound"). A merge of two whole surfaces is not refused unless they are the same size.

**For the 20 splits, partly.**

- The shed part is refused, as P1 requires.
- The majority part keeps the sid. That is an overlap-continuation choice, not a re-binding of any patch's cells.
- R4 counts these events because it compares patch sets in both directions.

**A preregistered fix**, described only, not implemented and not run:

1. **Merge refusal.** A current segment S is not accepted for any P if its member cells come from more than one previous sid P₁, P₂, … with each such parent's overlap ≥ half of that parent (2·ov(S,Pᵢ) ≥ Pᵢ.n_cells). Equivalently, S claims ≥ 2 previous surfaces under the existing claim test, since S.n ≥ Pᵢ.n for a merge. S is then born with a new reason (for example `refused_merge`), and every claimed parent coasts with a marked status (for example `merged`).
2. **Optional split symmetry.** If a previous P is claimed by ≥ 2 current segments, no claimant continues P. All of them are born `refused_ambiguous`, and P is marked `split`, as already happens for ties.

   With (1) alone, R4 as defined would still count the 20 S events. A prereg should either adopt (2) or redefine R4 as "a continue segment whose sid gains a patch whose cells carried a different sid at t−1".

The fix's footprint was measured descriptively on the stored raw records. It counts `continue` segments whose cells come from ≥ 2 previous sids, each with overlap ≥ half its parent:

| Arm | Segments meeting the condition |
|---|---|
| R1 | 20 of 793; exactly the 20 M events |
| R2 | 25 of 4536, all at the first overlay exposure |
| R4 | 11 of 258, all at the swap |
| R5 | 29 of 1358, all at the 6-column jump |
| R6 | 11 of 780, all at release exposure 1 |
| N5 | 16 of 1034, all at release exposure 1 |
| R7 (Poisson) | 3827 of 7521 |
| N1 | 0 of 527 |

The fix would therefore change other arms' outcomes too. Their downstream effects (sid numbering, later exposures, checks) cannot be computed without new exposures. It must be a new preregistration with a full re-run, not a re-analysis.

The same mechanism also explains most R4 failures (§9, Not preregistered). It does not catch merges in which the absorbed parent contributes less than half its cells: 2 such R4 cases.

## 5. P2: the hue clause fails again; Q1 confirmed

- **Hue clause.** The prereg hue clause fails at both td, as in stage 4. The median E→A hue change is smaller than E→D65: 4.25° vs 4.47° at 100 td and 3.08° vs 4.35° at 1000 td. The 100-td medians are within 0.02° of stage 4's single-scene values (4.24° / 4.47°).
- **Q1.** The Euclidean shift goes the predicted way at both td: A/D65 = 3.7× at 100 td and 5.8× at 1000 td. The layout-cluster bootstrap intervals for A and D65 do not overlap in either cell.
  - Q1 is **data-informed**: it was formulated from the stage-4 "Not preregistered" Euclidean measure, after the stage-4 hue failure had been seen.
  - Its confirmation here is on 16 independent layouts (R1 has 16/16 distinct profiles) that were not observed before the freeze.
  - So the stage-4 diagnosis is now a confirmed prediction on new scenes: looks change more under A than under D65, but mostly along their existing (+rg, −by) direction, so the angle metric misses it.
- **R2 clause.** Supported, 62/62. The limited independence of R2 (§2) applies.

## 6. P3: anchor clause and the other clauses

- **Anchor (0.75).** The clause fails in exactly the 24 frames of layouts 101, 103, 105 and 109. There, by expected catches, no single surface holds the per-channel maximum (A1 §3 pre-check: `none(L/M/S)`), so no sid's catch equals the frame anchor on all three channels. R7 counts these frames as failures.
  - **A18 secondary**, reported, not a verdict input: on the 12 single-anchor layouts (102, 104, 106, 107, 108, 110–116), rung 1 held on the anchor in 72/72 frames. That includes 107 and 115, where the anchor is the white background.
- **Non-anchor rung 1:**

  | | 100 td | 1000 td |
  |---|---|---|
  | D65 | 48/116 = 0.414 | 8/128 = 0.063 |
  | A | 26/112 = 0.232 | 1/127 = 0.008 |
  | D65 + A pooled | 74/228 = 0.325 | 9/255 = 0.035 |

  Both comparisons hold at both td. Unlike stage 4, the 1000-td A ≤ D65 comparison is not trivially 0 ≤ 0.
- **Rung 2 ≥ rung 1.** 95/96 conditions. The single failure is layout 108, 100 td, D65: rung 1 holds on 5/6 and rung 2 on 4/6.
- **Rung 2 overall** (D65 + A): 0.722 at 100 td and 0.692 at 1000 td, against rung 1 at 0.389 and 0.118.
- **R2 holds at 22.** 62/62: rung 1 `holds` with resid_max 0 and rung 2 `holds_pooled`, while rg moved from > 0 to < 0.
- **R4 swapped refused.** 52/64. 11 swapped-surface sids had no check at the swap: the exposure-1 sid was not continued, because the swapped patch merged into a neighbour's continuing segment or was born. 1 held: layout 108 at 100 td, sid 0, the background sid that also covered swapped patch 4.

## 7. P5: why it fails, and the N5 contrast

**R6 (same-geometry release, reacquire off):**

- **Room.** Every check during the room phase was `minted` (402) or `holds` (402), and no `presents_unrecognised` edge existed after the room (0 in 16/16).
- **Lids.** Each ganzfeld blanks `cur_sid`, so room surfaces are re-born after each lid. Every chromatic patch's property at release was minted at epoch 7, the first room exposure after the second lid, from neutral catches.
- **Release exposure 1.**
  - 122 of 128 segments `continue` a room sid, because the geometry is identical. 6 are births, one per sequence in layouts 101, 104 and 107: each is a patch that had shared a room surface with a neighbour and separated at release, born `refused_ambiguous`. None of them is a chromatic patch.
  - Checks: 116 refused, 6 minted, 6 hold. Every continuing chromatic surface is refused, and its look is linked `presents_unrecognised` to the old neutral property.
- **Clause (a)** fails because that edge type first appears at release.
- **Clause (b)** fails completely (0/96): every chromatic patch keeps its grey-room identity, so no property is re-minted.
  - This is stricter than stage 4 (64/144). There, room slots 4 and 10 equalled the background and were therefore born at release.
  - A1 Deviation 5 removed that coincidence: no room slot equals the background.
- **Clause (c)** fails in the 8 sequences of layouts 102, 103, 105 and 108. Every release surface is refused there, so `presents_property` does not increase (+0). In the other 8 sequences it increases by 3 or 6.

**N5 (different-geometry release `random_mondrian(seed+1000)`, reacquire on; descriptive):**

- **Room.** Re-acquisition carries room surfaces across the lids: 134 minted vs 670 holds in the room, against 402 / 402 in R6. 6–10 surfaces were re-acquired by the end of the room.
- **Release exposure 1.** 113 births vs 46 continuations. The 46 continuing surfaces (overlap with the old geometry) were refused.
- **P5 clauses (descriptive):**

  | Clause | N5 result |
  |---|---|
  | (a) no new types | 0/16. `presents_unrecognised` is still new at release; it is the only new type |
  | (b) chromatic patches with a release-minted property | 101/130 = 0.777 (100 td 50/65, 1000 td 51/65) |
  | (c) SurfaceLook and `presents_property` increase | 16/16 (+9 to +33 `presents_property`) |

So (b) depends on the release presenting new segments rather than on colour content. (a) fails structurally in both designs: a constant grey room never produces a rung-1 refusal, so the refusal edge type can only appear at release.

## 8. New arms N1–N5

### N1 re-acquisition (Q2)

| Cell | Re-acquired | Notes |
|---|---|---|
| GG 100 td | 147/147 | |
| GG 1000 td | 147/147 | |
| ES 100 td | 135/147 = 0.918 | 12 misses in 9 layouts |
| ES 1000 td | 140/147 = 0.952 | 7 misses in 4 layouts |

- Intermediate exposures were blank (no sid) in 64/64 sequences.
- **ES misses.** The 19 missed patch instances are the same patches that fail to follow position in R4 (layouts 101, 102, 103, 104, 108, 109, 112, 113 and 115). After the swap, the new reflectance arrangement changes which neighbours join under the luminance criterion. The patch then either continues another surface's sid (a merge, as in §4) or is born `refused_ambiguous`.
- ES properties were unchanged in 26/32 sequences. The other 6 contain a birth that minted a property.
- Q2 passes the 0.90 threshold in every cell. ES at 100 td is the closest, with 0.918 (bootstrap lower bound 0.878).

### N2 recall (Q3)

- In all 32 sequences, every one of the 269 non-control cues returned `recalled`.
- The cues added 0 nodes and edges of every counted type (ColourProperty, FrameStats, PropertyCheck, LookingEpisode, SurfaceLook, FieldLook, `presents_property`, `presents_unrecognised`).
- The control cue for sid 10⁶ returned `no_property` / `no_surface` in 32/32.

### N3 concept link (Q4)

The majority rate p0 was 0.430 at 100 td and 0.423 at 1000 td (yellow).

Truth classes (scored patches):

| td | yellow | red/purple | blue | green |
|---|---|---|---|---|
| 100 | 34 | 21 | 17 | 7 |
| 1000 | 41 | 27 | 22 | 7 |

Confusion, truth → concept:

| Truth | 100 td | 1000 td |
|---|---|---|
| yellow | 26 yellow, 8 green | 32 yellow, 9 green |
| red/purple | 11 red/purple, 7 blue, 3 yellow | 14 red/purple, 7 blue, 6 yellow |
| blue | 17 blue | 22 blue |
| green | 7 green | 7 green |

- Blue and green are always correct. The errors are yellow→green and red/purple→blue/yellow.
- Accuracy is 0.772 at 100 td and 0.773 at 1000 td. Both are above p0 with binomial p < 1e-9.
- Per-layout accuracy ranges from 1/2 to 8/8.

### N4 motion route (Q5, descriptive)

- **Setup.** 13 layouts × 2 td × flag on/off = 52 sequences. Layouts 101, 104 and 106 have no N4 patch.
- **Where motion segments appear.** Only in flag-on sequences of layouts 108, 109, 114 and 115 (both td). Each time they first appear at the 3rd one-column step.
  - Every motion segment has 3–9 cells.
  - Every one is born `refused_ambiguous`, except one: in layout 108 at the 4th step, a motion segment continued its own previous motion sid.
  - Each produced one carve polygon, with coherence 0.866 or 1.0.
- **Effect on identity:**
  - **108** (neutral 3.5) and **115** (blue flower): the moved patch kept its sid at every step with the flag on and off. The motion segment covered a separate small set of cells.
  - **109** (cyan) and **114** (neutral 8): with the flag on, the motion segment carved 6 cells of the moving patch into a new sid. The patch was split across two sids at steps 3–4 (`sid_kept_through_moves` = T, T, F, F). With the flag off it kept one sid throughout (at 109, 100 td, that sid was the background's).
- **Flag on vs off.** In the other 18 pairs, the flag-on sid grids are identical to flag-off.
- **Summary.** On these layouts the motion route rarely fires. When it does, it either leaves identity unchanged or fragments the moving surface. For the one background-merged moving patch (109, 100 td), it carved 6 cells into a new refusal-born sid at steps 3–4. It did not give that patch a surface of its own.

### N5

See §7.

## 9. Deviations

**From A1 §9, as preregistered:**

1. The layouts are `random_mondrian` seeds 101…116. R6 and N5 use 101…108, and R5 adds 12 supplement seeds (A6). There is no development-layout arm.
2. The engine is `ed9237c97f20`, not `b6a41e3bbba6`.
3. The R2 roles were redefined (A4). Layout 109 has no "white" role.
4. R5 includes the unmoved position, a mirrored fallback and supplement seeds. The primary set of 4 layouts (8 sequences) was 8/8. The 5 failures are all in supplement layouts (147, 178 and 189), whose selection depends on geometry only.
5. The R6 room uses random geometry, neutrals drawn with replacement, and a varying background. No slot equals the background. This is the direct cause of the P5(b) difference from stage 4 (§7).
6. R7 ran on 16 layouts.
7. The layout-cluster bootstrap and distinct-profile counts were added, and so was the A18 secondary analysis.
8. The freeze is a committed runner plus `git diff --quiet` plus a data hash, with the script sha embedded.
9. A smoke run and a dry run happened before the freeze on the development layout, as disclosed in A1.
10. N1 uses an open-eye uniform field (`filter=None`). N4 uses stage45=False.
11. No `--from-raw` recovery was needed or used.

**At run time:**

- None in the runner: no abort, no crash, no re-entry, no change of script (sha unchanged).
- The exposure count equals the plan.
- **After the run**, this write-up appended a pointer paragraph to `docs/experiments/marys-room-stage4-results.md`. That file is in A1's `FREEZE_TRACKED` set, so a future confirmatory launch of the same runner at this tree would fail the freeze check until the change is committed. The run itself was unaffected. The freeze was clean at launch, and the results were produced before the edit.

## 10. Not preregistered

These are descriptive analyses on the stored raw records, with no new exposures. They change no verdict.

- **§4 silent-rebind classification and fix footprint.** This includes the cell-level parent overlaps and the use of `random_mondrian(seed).label_map()` for cell→patch identity (geometry only).
- **R4 failure mechanism.** 13 of 32 sequences fail "sids follow position", with 19 non-following patch instances.
  - 13 instances took another surface's *continuing* sid. In 11 of them the continuing segment met the §4 merge condition (≥ 2 parents, each ≥ half covered). In 2 (layout 109 and layout 115, both at 100 td) the absorbed parent was covered by less than half.
  - 6 instances were born `refused_ambiguous`.
  - This is the merge-continuation defect showing up in the swap arm. In stage 4, gutters prevented any new adjacency.
- **R5 failure mechanism.** In all 5 failing sequences, the moved patch was covered by the background sid 0 from exposure 1: 147 (bluish green), 178 at 100 td (dark skin), and 189 (blue sky).
  - In 178/100 and 189 the jump produced no new sid.
  - In 147 the jump continued another surface's sid (2) rather than being born.
  - So steps "keep the sid" only because the background keeps its sid.
- **Rung 2 overall and per-condition values** (§6), and the N1 ES properties-unchanged count.
- **R2 value-level independence** (§2): number of distinct (rg1, rg22) pairs per role.
- **N5 room statistics** (minted vs holds) and release segment decisions (§7).

## 11. Interpretation boundary (model level)

All statements concern computed graph states of this model on these 16 synthetic ColorChecker layouts:

- **Layouts.** The replication removes the stage-4 single-scene limitation for R1, R4, R6 and R7. R2 and R5 remain weakly independent, for the reasons in §2.
- **Identity.**
  - Identity bound by cell overlap remains colour-free. Non-exempt patches were stable 233/233, and 1-column steps kept the moved patch's sid in 32/32 sequences (5 of them only through the background sid).
  - But the criterion is not refusal-complete. Unequal merges of whole surfaces continue the larger surface's identity, and nothing records it.
  - Stage 4 could not show this, because its only boundary pair was symmetric.
- **Looks and properties.**
  - Looks move with illuminant more under A than under D65 (Q1, now confirmed on new scenes). The hue-angle metric still fails to show it.
  - Properties are refused outside their class: rung 1 holds rarely at 1000 td, and rung 2 recovers about 70%. They also hold exactly under adaptation while looks shift.
- **Mary's release.** In this graph, release mostly refuses old grey-room properties when identity carries over. It mints chromatic properties only for newly segmented surfaces. The only "new kind" at release is the refusal edge, which a constant room cannot produce.
- **New flags.**
  - Re-acquisition, recall and the concept link do what A1 predicted.
  - The motion route does not separate merged surfaces and can fragment a moving one.

A `SurfaceLook` is a mean of computed opponent signals and a `ColourProperty` is a stored catch triple. Neither is an experience, and nothing here bears on human qualia or human colour vision.

## Raw outputs

- `results/marys_room_stage4_replication.json`. Keys:
  - `freeze`, `script_sha256`, `git_head`, `engine_provenance`;
  - `rules_original`, `rules_A1`, `declared_choices`, `determinism`, `perf`, `raw_payload_sha256`;
  - `analysis_R` (B1–B7 per-sequence records via the original analysis functions);
  - `analysis_N` (N1–N5, N3 summary, `cluster` bootstrap statistics, `profiles`);
  - `verdicts_P`, `verdicts_Q`, `raw`.
- Raw checkpoint `/tmp/marys_room_stage4_replication_raw.json` (sha `7d90cc67…bb`) and run log `/tmp/a1_run.log`, both outside the repo.
