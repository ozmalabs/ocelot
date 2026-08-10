# LS20 FLASH-ONSET-GUIDED MECHANIC DISCOVERY — RESULTS (block 223000)

**Tests the owner's claim:** *"the flash when the avatar goes to the shape is a
salience indicator of what the rules are."* The transient flash on avatar↔shape
contact is ls20's OWN supervision signal — it LOCALISES (where a rule fires) and
TIMES (which step). It routes curiosity/attention; the transform is STILL
discovered by the identical 222000 sd-loop.

Pre-registered in `LS20_FLASH_PREREG.md` (committed ALONE, SHA **`8e1a510b12`**).
Block `223000` claimed CLEAN (`seed_claim.py 223000 223999`, no collision
detected). **Lead with sample-efficiency vs the 222000 blind baseline.**

## THE HEADLINE — SAMPLE-EFFICIENCY vs THE 222000 BLIND BASELINE (G-sample-efficiency, OFFLINE powered)

Observations (world probes) to reach held-out change-set strict-F1 ≥ **0.9**,
flash-onset-guided vs 222000's blind mode-colour control, over a CLUTTER SWEEP,
24 seeds/level, 1000-resample bootstrap 95% CI
(`results/arc_ls20_flash_powered.json`):

| clutter | blind obs-to-converge (conv. rate) | flash obs-to-converge (conv. rate) | flash CI-sep BELOW blind |
|---|---|---|---|
| **n_distractors=0** | **10.0 [10, 10]** (100%) | **10.0 [10, 10]** (100%) | **False (by design)** |
| n_distractors=1 | 187.9 [120, 261] (83%) | **14.6 [11, 18]** (100%) | **True** |
| **n_distractors=2 (headline)** | **393.5 [320, 460]** (29%) | **15.0 [12, 19]** (100%) | **True** |
| n_distractors=3 | 483.3 [450, 500] (8%) | **39.6 [22, 61]** (100%) | **True** |

- **At the headline n_distractors=2, flash-guided converges in ~15 observations;
  blind needs ~26× more and converges in only 29% of the 500-obs budget.** The
  flash arm reaches the mechanic model CI-separated FASTER — the owner's claim,
  MEASURED. (Right-censoring at the budget makes blind's mean a conservative
  LOWER bound on its true cost, so the CI-separation is conservative.)
- **THE ANTI-RIG NULL (n_distractors=0): flash gives ZERO advantage** — both
  converge in exactly 10 observations on a clean 222000-style single-object
  scene, because blind's mode-colour already localises it. The flash advantage
  GROWS monotonically with clutter and vanishes without it. **This is the proof
  the flash is not rigged to hand the mechanic to the flash arm.**

**This gate COULD have failed** (if the cell-diff localised as well as the flash);
it did not, at every clutter level > 0.

## HOW CIRCULARITY WAS AVOIDED (the fatal trap — stated explicitly)

The flash could trivially win if it encoded the answer. It does not:

1. **The flash is a LUMINANCE-ONLY transient, never written into the colour
   grid.** The colour grid (the content both arms decode and score on) is
   IDENTICAL with or without the flash — so the blind arm is NEVER confused by
   the flash; its only problem is the distractor clutter. This is why the
   anti-rig null holds: at n_distractors=0 the colour grid is a clean scene blind
   handles perfectly.
2. **The flash appearance is IDENTICAL for all 10 actions** (a fixed-luminance
   glow at the rule object's contact border). Given only the flash you cannot
   tell move_up from rotate — you must read the object geometry.
3. **Both arms discover the transform via the IDENTICAL 222000 sd-loop**
   (`_recognise_transform` / `TransformDecode` / `DimInfer`). The flash changes
   ONLY which region the sd-loop is pointed at first (attention order), never
   what it computes.
4. **The blind arm ALSO converges** (222000 proved offline F1 1.0; here blind
   converges at n_distractors≤2 given enough budget — e.g. 304 obs on one nd=2
   seed). The comparison is SAMPLE-EFFICIENCY, not can-converge.

## G-flash-detects — THE FLASH IS AN ONSET EVENT (the GENERAL stream, not a bespoke detector)

The REAL `GraphEye` 2-D onset stream (`photon_transduce_onset` Rust kernel +
`retinal_onset_2d` seed — the same async onset machinery that serves Doom / the
photon eye), 30 arenas × 8 steps:

| onset source | mean `magnitude_db` (95% CI) |
|---|---|
| **the FLASH cells** | **20.9 [20.3, 21.4]** (n=240) |
| distractor-motion cells | 13.8 [13.4, 14.1] (n=235) |

- **Flash onset dB CI-separated ABOVE the distractor-motion onsets** (20.3 >
  14.1) — the flash is the most salient transient, so the `fg_pick_flash` rule's
  Argmax(`magnitude_db`) points to it.
- **The Argmax onset localises to a flash cell in 91.2%** of frames (≥ 90%
  pre-registered). The flash is perceivable + localisable by the general
  machinery, no ls20-flash-specific detector.

## G-pointer-vs-content — THE TRANSIENT/PERSISTENT SEPARATION IS LOAD-BEARING

A CONFLATE arm that predicts the transient flash as a PERSISTENT change vs the
SEPARATE arm that uses the flash ONLY as a pointer (16 seeds, 60-obs budget):

| arm | held-out change-set strict-F1 (95% CI) |
|---|---|
| **SEPARATE (flash = pointer only)** | **0.91 [0.85, 0.96]** |
| CONFLATE (flash treated as content) | 0.34 [0.32, 0.35] |

**CI-separated.** Conflating the pointer with the content adds false-positive
changed cells (the flash reverts → the true next frame has no flash there) →
change-set F1 collapses. The flash is a POINTER (where/when), DISTINCT from the
persistent TRANSFORM (what) — proven, not decorative.

## G-graph-native + SOURCE-AUDIT

- **Flash detection = the EXISTING onset stream** (no new detector).
- **Flash-guided attention = a graph RULE** (`fg_pick_flash`,
  `seeds/ls20_flash.json`): Argmax(`magnitude_db`) over the onset cues copied into
  the agent graph → the attended flash location — the DECISION "which onset is the
  flash" is a rule, exactly like 222000's `pc_probe_pick` Argmin curiosity.
- **The transform = the identical 222000 sd-loop.** The adapter is mechanical
  (perceive → onset → attend → sd-loop discover → apply → measure).
- **Source-audit PASS**: the agent's discovery/prediction fns
  (`discover_blind`, `discover_flash_separate`, `_window_region_spec`,
  `_spec_from_objs`, `predict_conflate`) reference the ground-truth `_MOVE`/
  `_XFORM` tables **[] (none)**; only the arena (WORLD PHYSICS) uses them, exactly
  as 222000's `world_next`. The mechanic is minted from observation.

## LIVE HALF (real ARC-AGI-3 ls20 — the HONEST number, reported STRAIGHT)

Auth verified BEFORE measuring (key from `.env`, NEVER printed/committed; `.so`
gitignored, NEVER committed). `arc_ls20_flash_live.py --game ls20-9607627b
--steps 50` (`results/arc_ls20_flash_live.json`):

- **The per-cell model did NOT converge in the budget — the NULL, reported
  STRAIGHT:** flash-guided change-set F1 **0.0** == blind **0.0** == persistence
  **0.0** (46 repeat-obs scored, 4 first-obs). `flash_beats_blind = False`. Same
  null 222000's blind live half reported.
- **WHAT THE FLASH DID LOCALISE (the partial progress, measured):** the GENERAL
  onset stream fired on **50/50 real frames**, its Argmax onset localising to a
  CONSISTENT region (rows ≈ 42–47, cols ≈ 29–34) — the real ls20 flash/interaction
  transients ARE perceivable + localisable by the same machinery that works
  offline. The flash is detected on real content; the rigid single-object
  transform model is still too weak for real ls20's richer dynamics (nested
  fields + multi-colour avatar + move/trail/consume, 52 cells/action — 222000's
  named residual). Perception detail: the reset frame round-trips through the
  216000 pixel eye EXACTLY (values {0,1,3,4,5,8,9,11,12}); over 50 streamed steps
  at least one later frame did not (content-dependent; 222000's shorter 40-step
  run round-tripped throughout).
- **This is an honest measured null with real partial progress**, not a hidden
  failure: the OFFLINE powered sample-efficiency teeth (the deliverable) prove the
  flash-guided mechanism decisively (~26× at nd=2, CI-separated, anti-rig null at
  nd=0); the live half confirms the flash is DETECTED on real ls20 but the
  single-object transform remains the standing frontier.

## DISCIPLINE

- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (no Rust;
  reuses the onset stream + 222000's `TransformDecode`/`DimInfer` + Argmax).
- **`runners/dsl` diff EMPTY** (`term.rs` included) — no tracked file modified;
  the rung is entirely NEW files.
- **Default-OFF byte-identical:** the `fg_pick_flash` rule is guarded on
  `flash_on==1` (`test_flash_rules_are_default_off`); the existing ls20 migrated
  suites (`test_arc_ls20_planning_migrated` + `test_arc_ls20_mapnav_migrated` +
  `test_ls20_percell_migrated`) = **20 passed** (unchanged with the flag off).
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped** == AFTER
  **214 passed, 10 skipped**.
- **34-file `per_area_settlement_regression.sh`:** failing NODE-ID SET IDENTICAL
  before/after (`results/flash_regress_before.txt` == after; 23 failed / 277
  passed / 5 skipped).
- **New gates:** `tests/test_ls20_flash_migrated.py` **8 passed**.
- **Integer-native:** in-frame cell values are the integer lattice; the flash is
  a luminance transient the eye reads; the `Transform` is the cross-frame map.

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The powered sample-efficiency teeth are on ls20-SHAPED offline arenas (real ls20
palette, the general 222000 transform recogniser, a REALISTIC luminance-only
flash, clutter grounded in 222000's measured real-ls20 reality). They prove the
MECHANISM — the flash localises the rule region so the sd-loop converges in far
fewer probes amid clutter — decisively (~26× at nd=2, CI-separated), with the
anti-rig null at nd=0. The LIVE half confirms the flash is DETECTED on real ls20
(onset 50/50) but reports the honest NULL: the real ls20 mechanic is richer than
a rigid single-object transform and does not converge in the 50-step budget. Both
reported.

## FILES

- `LS20_FLASH_PREREG.md` — pre-registration (committed alone, SHA `8e1a510b12`).
- `domains/ls20_flash_seed.py` → `seeds/ls20_flash.json` — the `fg_pick_flash`
  Argmax-onset-magnitude attention rule (depends on `ls20_percell`; default-OFF).
- `worlds/arc_ls20_flash.py` — the mechanical adapter: the clutter arena + the
  luminance-only transient flash, the `OnsetEye` driver (the general 2-D onset
  stream), the three region-selectors (blind / flash-separate / flash-conflate),
  the `FlashAgent` (reuses 222000's Percell + pc_* rules), and the
  sample-efficiency driver. Reuses 222000's discovery/apply/metrics unchanged.
- `scripts/arc_ls20_flash_measure.py` — the powered offline gates + source-audit.
- `scripts/arc_ls20_flash_live.py` — the bounded LIVE half.
- `tests/test_ls20_flash_migrated.py` — 8 gate tests.
- `results/arc_ls20_flash_{powered,live}.json` — the measured numbers.
