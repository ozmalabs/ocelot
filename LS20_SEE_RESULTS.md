# LS20 SEE-THE-MECHANIC — RESULTS (block 231000)

Pre-registered in `LS20_SEE_PREREG.md` (committed **ALONE**, SHA `b75a8621a5`),
BEFORE any number here. Block `231000-231999` claimed CLEAN (`seed_claim.py 231000
231999`; verbatim `check_claim` in the prereg — NOT a permanent pytest).

## THE OWNER GROUND TRUTH (corrects a false null)

Blocks 229/230 reported live **"0 distal change / mechanic triggered some other
way."** That was **WRONG — a PERCEPTION FAILURE, not a game fact.** Owner, watching
real ls20 frames: **REACHING the cross causes the INDICATOR to FLASH, the
DESTINATION to FLASH, and the EXIT GLYPH to ROTATE.** The whole built pipeline
(223→227→228→229→230) was CORRECT but STARVED — the eye never delivered the signal.

## THE HEADLINE — G-detect-the-effects: THE EYE NOW SEES WHAT THE LUMA EYE WAS BLIND TO

The 229/230 live eye (`arc_ls20_flash.OnsetEye`) is the shared retinal-onset stream
fed a **luminance** projection of the colour grid. It is **colour-blind** and
**increase-only**. The fix is an **event-native colour-change onset**
(`worlds/arc_ls20_see.ColourChangeEye`): the previous returned frame is the HELD
PRIOR; an onset is the RESIDUAL against it — a cell whose observed **colour INDEX**
departs the prior, in EITHER direction — computed per-transition on the game's EVENT
cadence, classified TRANSIENT (reverts — the flashes) vs PERSISTENT (stays — the
rotation).

**OFFLINE (powered, ground-truth-gated), the synthetic reach event** where the
flash + rotation are colour-only (same-luminance under the luma LUT) and the avatar
move is luminance-visible — the 229/230 null reproduced as the baseline
(`results/arc_ls20_see_powered.json`, N=48, Wilson 95% CIs):

| eye | indicator flash | destination flash | exit-glyph rotation | **all three** |
|---|---|---|---|---|
| **colour-change (the fix)** | 1.000 [0.926,1.0] | 1.000 [0.926,1.0] | 1.000 [0.926,1.0] | **1.000 [0.926, 1.000]** |
| luma (pre-fix, the null) | 0.000 [0,0.074] | 0.000 [0,0.074] | 0.000 [0,0.074] | **0.000 [0.000, 0.074]** |

- **G-detect-the-effects: PASS**, CI-separated (colour all-three CI-lower **0.926 >
  0.074** luma CI-upper). The colour eye detects the indicator flash AND the
  destination flash AND the exit-glyph rotation (read as `rot90:k` by 227's
  UNCHANGED `_recognise_transform` — keys `rot90:1/2/3` all observed); the luma eye
  detects NONE (the 229/230 null exactly). Measured against the GROUND-TRUTH raw
  cell-diff, never the eye's self-report. Detected onsets are a strict SUBSET of the
  ground-truth changed cells (no confabulation,
  `test_detection_is_gated_against_ground_truth_not_self_report`).

## G-located-cause — THRESHOLD, per-region, disambiguated from timing

`results/arc_ls20_see_powered.json` `G_located_cause` (N=48): the operative cause is
**THRESHOLD** — every region the luma eye misses is a **colour-only change PRESENT in
the returned reach-frame** (so NOT a sub-step timing transient) that the increase-only
luminance onset drops (sub-+6 dB). **175/223** ground-truth regions were missed by
luma; the colour eye covers **all** (`colour_eye_covers_all_rate` 1.000 [0.926,1.0]
vs `luma_eye_covers_all_rate` 0.000 [0,0.074]). Per-region evidence records, for each
region: present-in-returned-frame, luma-fired + luminance-delta vs +6 dB,
colour-fired, transient/persistent — not a vague "missed it." Coverage and an
internal distal classifier were ruled out by static analysis (uniform full-resolution
onset sheet; no positional predicate in the mint rule).

## G-wires-to-pipeline — the detected effects flow into the UNCHANGED 227/229

`results/arc_ls20_see_powered.json` `G_wires_to_pipeline` (N=24):

- **destination flash → 229:** the detected distal destination flash drives 229's
  UNCHANGED `rcg_ground` → mints `causes(cross, destination_flash)`
  (`destination_flash_grounds_causes_rate` **1.000 [0.862,1.0]**); a no-detection
  control grounds nothing (**0.000 [0,0.138]**).
- **exit rotation → 227:** the detected rotation reads as `rot90:k`
  (`rotation_read_as_227_key_rate` **1.000 [0.862,1.0]**; keys rot90:1/2/3).

## G-live (REAL ls20) — THE FALSE NULL CORRECTED, MEASURED STRAIGHT AGAINST GROUND TRUTH

`scripts/arc_ls20_see_live.py --game ls20-9607627b --nav 40`
(`results/arc_ls20_see_live.json`, frames in `results/arc_ls20_see_live_frames.json`).
**FRESH-API** (not replay). Auth verified BEFORE (`ARC_API_KEY` from the gitignored
`/home/matt/ozma/internal/.env`, NEVER printed/committed; RESET `state=NOT_FINISHED`,
grid 64×64, `available=[ACTION1..4]`). Navigation LEARNED each move's avatar
displacement by probing (ACTION1 up=(0,0) blocked, ACTION2 down=(5,0), ACTION3
left=(0,−5), ACTION4 right=(0,+5)) and localised the cross via the onset stream to
**(47,34)** — the SAME locus as 223/225/227/228/229. Reproducible across 3 episodes.

On the reach transition at the cross, the GROUND-TRUTH raw cell-diff = **52 changed
cells in 2 regions**, one of them DISTAL:

| region | kind | luma Δdb | **luma eye** | **colour eye** |
|---|---|---|---|---|
| local (50 cells, ~(44,36), dist 2.5) | avatar + local change (colours 3,9,12) | +13.2 | fired | fired |
| **DISTAL (2 cells, (61,17), dist 27)** | **remote change colour 11→3 (a DIMMING)** | **−13.2** | **MISSED** | **FIRED** |

- **THE FALSE NULL IS CORRECTED.** There WAS an observable remote change on reaching
  the cross — the pre-fix luma eye simply could not see it. The colour eye achieves
  **full ground-truth recall (52/52 events)**; the luma eye reports **15/52** (it
  drops 37 colour-only cells, INCLUDING the entire distal region — a symbol at row 61
  recolouring 11→3, a luminance DIMMING of −13 dB that increase-only luminance cannot
  register). Gated against the ground-truth raw pixel deltas, NOT the eye's
  self-report (which is exactly what produced 229/230's null).
- **Located cause confirmed LIVE, per-region:** `operative_cause=threshold`; the
  missed distal region is `present_in_returned_reach_frame=True` (NOT a sub-step
  timing transient), `luma_above_6db=False` (Δ −13 dB), `colour_eye_fired=True`.
- **Wires to the pipeline from a REAL observation:** the colour-eye-detected distal
  remote change grounds `causes(cross, …)` via 229's UNCHANGED `rcg_ground`
  (verified on the saved frames — grounded=True, edge `('cross','destination_flash')`).

**HONEST RESIDUALS (reported straight, NOT patched):**
1. The distal remote effect captured on this game/budget was a **2-cell persistent
   recolour (11→3)**, not the clean separable indicator+destination-flash+rotation
   triple the owner described; **no rotation was recognisable in any live region**
   this budget (a 2-cell region cannot establish a rotation). The full three-effect
   detection is proven OFFLINE (powered, CI-separated); the LIVE half confirms the
   CORE fix (the colour eye sees a remote change the luma eye is blind to) + the
   located cause + end-to-end 229 grounding.
2. **Real ls20 has NO no-op action** (available=[ACTION1..4]); every frame requires a
   move, so the reach→after frame ALSO changed 52 cells — the transient/persistent
   classification is CONFOUNDED live (a genuine ARC-API observability limit, not a
   fix defect).
3. The greedy nav reached the cross LOCUS (onset-localised (47,34)); I cannot certify
   the avatar body was precisely ON the cross cell vs its immediate vicinity.
4. The local 50-cell region merges the avatar move with any local flash; the
   distal-vs-local kind-attribution is a scoring convenience — the DETECTOR itself
   hardcodes no location (source-audit clean).

## G-graph-native / SOURCE-AUDIT

`source_audit` (`results/arc_ls20_see_powered.json`): `{'no_hardcoded_ls20_
destination_or_exit_location_in_detector': True, 'regions_emerge_from_observed_change':
True, 'detector_reads_ground_truth_raw_diff': True, 'no_ground_truth_action_effect_
table': True, 'banned_domain_tokens_in_detector_logic': [], 'clean': True}`.

- The detector names **NO** destination/exit-glyph LOCATION and **NO** domain
  constant — the destination/exit regions EMERGE from the observed change
  (`changed_regions` over `raw_changed_cells`). Perception is mechanical (a real
  array diff, the honest twin of 229's `observe_change`); the DECISIONS (grounding,
  transform) stay in the UNCHANGED 229/227 rules.

## DISCIPLINE

- **Canonical `.so` md5 `fe7c4d33…` UNCHANGED** (the improved real-time foveated
  photon eye — NO Rust; the colour-diff is perception ingest, not an engine change).
  `runners/dsl` tracked diff EMPTY (`term.rs` included) — verified.
- **Default-OFF byte-identical:** the fix is entirely NEW files
  (`worlds/arc_ls20_see.py`, `scripts/arc_ls20_see_{measure,live}.py`,
  `tests/test_arc_ls20_see_migrated.py`); the existing luma `OnsetEye`,
  `photon_eye.py`, and every seed are UNTOUCHED — the pre-fix path is byte-identical
  BY CONSTRUCTION (`test_fix_touches_no_shared_perception_path`).
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped** == AFTER **214
  passed, 10 skipped** (`results/see_oracle_{before,after}.txt`).
- **34-file `per_area_settlement_regression`:** failing NODE-ID SET **IDENTICAL**
  BEFORE == AFTER — **23 failed, 278 passed, 5 skipped** both runs; `diff` of the
  sorted node-id lists EMPTY (`results/see_regress_{before,after}_ids.txt`). (The 23
  are the pre-existing reds this environment carries; 231 touches none.)
- **New gates:** `tests/test_arc_ls20_see_migrated.py` **12 passed**
  (ground-truth-is-a-real-raw-diff; reach-produces-the-three-regions;
  colour-detects-all-three-luma-misses; detection-gated-against-ground-truth;
  located-cause-threshold-per-region; destination→229-grounds;
  no-detection-control; rotation→227-rot90-key; transient-vs-persistent;
  fix-touches-no-shared-path; source-audit-no-hardcoded-location;
  event-native-residual-against-held-prior).
- **Integer-native:** colour indices; the onset is exact inequality on the observed
  colour; the verdict is gated on the ground-truth raw diff.

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The OFFLINE powered ablation proves the MECHANISM decisively: the event-native
colour-change eye detects all three effects (indicator + destination + rotation),
CI-separated above the pre-fix luma eye which reproduces the 229/230 null; the
located cause is THRESHOLD, named per-region; the effects wire into the UNCHANGED
227/229 pipeline (destination→grounds, rotation→rot90:k). The LIVE half corrects the
false null on REAL ls20: the colour eye SEES a remote change (colour 11→3 at row 61,
a −13 dB dimming) the luma eye is BLIND to, full ground-truth recall 52/52 vs 15/52,
which grounds `causes(cross,…)` via 229 end-to-end — the located cause confirmed live
per-region. The honest residual: the clean three-effect triple was not isolated in
the live budget (the captured remote effect was a 2-cell recolour, not a
rotation), and real ls20's no-no-op action confounds transient/persistent
classification. Both reported.

## FILES

- `LS20_SEE_PREREG.md` — pre-registration (committed alone, SHA `b75a8621a5`).
- `worlds/arc_ls20_see.py` — the ColourChangeEye + ground-truth utilities + located-
  cause diagnostic + synthetic reach scenario + 227/229 wiring (mechanical
  perception; no agent decisions).
- `scripts/arc_ls20_see_measure.py` — the powered offline gates + source-audit.
- `scripts/arc_ls20_see_live.py` — the LIVE navigate-onto-the-cross diagnostic.
- `tests/test_arc_ls20_see_migrated.py` — 12 gate tests.
- `results/arc_ls20_see_{powered,live}.json`, `results/arc_ls20_see_live_frames.json`
  — the measured numbers + the real captured frames.
- `results/see_{oracle,regress}_{before,after}*` — the discipline baselines.
