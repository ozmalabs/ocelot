# LS20 SEE-THE-MECHANIC — PRE-REGISTRATION (block 231000)

Committed **ALONE**, BEFORE any measurement. This file fixes the diagnostic, the
mechanism, the gates, the controls, and the discipline. Numbers land only in
`LS20_SEE_RESULTS.md`.

## SEED CLAIM (verbatim `check_claim`, recorded here — NOT a permanent pytest)

```
$ python scripts/seed_claim.py 231000 231999
SEED CLAIM 231000-231999: CLEAN -- no collision DETECTED.
  Scope: 949 files with seed sinks; 647 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
EXIT=0
```

Block `231000-231999` claimed CLEAN.

## THE OWNER GROUND TRUTH (this corrects a false null)

Blocks 229/230 reported live **"0 distal change / mechanic triggered some other
way."** That was **WRONG — a PERCEPTION FAILURE, not a game fact.** Owner,
watching the real ls20 frames: **REACHING (moving onto) the cross causes the
INDICATOR to FLASH, the DESTINATION to FLASH, and the EXIT GLYPH to ROTATE.**
These are real, observable pixel effects the agent's change-detection MISSED.
ls20's action set is ONLY the 4 movement actions, so the trigger is MOVEMENT onto
the cross. The whole built pipeline (223 flash-onset → 227 posit-meaning → 228
cross→DESTINATION remote-causation → 229 observe-and-ground → 230 discover-operate)
is CORRECT but was STARVED — the eye never delivered the real signal.

## THE LOCATED CAUSE (two candidates; the live diagnostic disambiguates them per-region)

The live eye used by 229/230 (`worlds/arc_ls20_flash.OnsetEye`) is the shared
retinal-onset stream fed a **luminance** projection of the colour grid
(`luma()` → `_LUMA_LUT`), and the harness computes distal change per-step. TWO
candidate causes; **coverage and an internal classifier are ruled out for this
configuration**, THRESHOLD is confirmed by static analysis, and TIMING/TRANSIENCE
is a co-equal candidate the LIVE diagnostic must settle against ground truth:

- **NOT coverage.** The 2-D onset sheet is built uniformly at full resolution over
  every cell (`photon_eye.py` `_build_2d`; no `retinal_layout` in the OnsetEye
  context → no fovea/periphery downsampling). A remote onset 8-20 cells away is
  processed identically to a central one.
- **NOT an internal distal classifier.** The onset mint rule
  (`seeds/retinal_onset_2d.json`) binds every column with no positional/focus
  predicate; the only distal filter is the live harness's `_distal_onset`, which
  fires WHEN an onset exists.
- **THRESHOLD/LUMINANCE (confirmed by static analysis).** The onset fires only on a
  **luminance INCREASE** past `+6 dB` (`output[3] = 20·log10(caught/adaptation)`,
  `Gt(output[3], 6.0)`). The rod-only 2-D sheet is **colour-blind**, and
  `_LUMA_LUT` collapses most colours to a flat `12.0`. So (a) a DESTINATION flash /
  recolour between two same-luminance colours → `caught ≈ adaptation` → ~0 dB →
  **no onset**; (b) an exit-glyph ROTATION that permutes same-luminance cells → ~0
  dB → **no onset**; (c) any change that dims → negative dB → **no onset**. The
  luminance onset is the wrong instrument for a discrete-colour game — even a
  change PRESENT in the returned frame is lost.
- **TIMING/TRANSIENCE — "FPS is the smuggled premise" (owner).** A "frame" pretends
  the whole field was freshly, uniformly measured at a universal instant. Really,
  perception = new + CHANGED observations against a reconstruction of the settled
  majority from priors. The ls20 flash is a TRANSIENT changed observation — it
  fires on the game's EVENT clock (the rule firing on reach) and reverts. **If a
  before/after diff samples two endpoints that BOTH show the reverted state, it
  aliases to nothing.** The 229/230 harnesses never DELIBERATELY navigated onto the
  cross (they cycled `avail[i%len]`), so they never even produced a reach transition
  — a compounding sampling failure. The live diagnostic settles the sharp empirical
  question: **do the three effects APPEAR in the returned reach-frame (→ threshold
  is the operative cause; the colour-change residual on the reach transition catches
  them) or are they absent from every returned frame (→ a genuine sub-step
  transient the ARC HTTP API — which returns only settled frames — cannot expose,
  reported straight as the honest limit)?** The exit-glyph ROTATION is a PERSISTENT
  change (a held-state delta, detectable even off-timing); the indicator/destination
  FLASHES are TRANSIENT (need the into-frame transition captured). The fix
  distinguishes and handles both.

**G-located-cause** settles this on the real reach transition with PER-REGION
evidence: for each ground-truth changed region (raw cell-diff), whether it is
present in the returned reach-frame at all (timing), whether the luma eye fired and
the luminance-delta it saw vs the `+6 dB` bar (threshold), and whether the change is
transient (reverts on the next frame) or persistent.

## THE FIX (graph-native EVENT-NATIVE perception; the eye/engine/seeds UNTOUCHED)

A **colour-change onset** perception primitive — the discrete-signal analogue of
the retinal onset, framed EVENT-NATIVELY per the owner reframe (NOT "sample the
reach-frame better" — that is still FPS thinking). The previous returned frame is
the **held prior** (the reconstruction of the settled ~98.7% majority); an onset is
the **residual** against it — a cell whose observed **colour INDEX** departs the
held prior — computed at EVERY transition on the game's EVENT cadence (one event
per action/step), NOT as a single before/after endpoint diff (which aliases the
transient away). This is the async onset stream (171000/191000) + held-prediction
residual applied to a discrete colour field:

- an onset fires in **either direction** (a transient flash is a colour that appears
  then reverts; a rotation permutes same-luminance colours);
- each changed cell is classified **TRANSIENT** (reverts to the prior within the
  next frame — the flashes) vs **PERSISTENT** (stays changed in the held surface —
  the exit-glyph rotation), so both are handled and the persistent rotation is
  detectable even off event-time;
- events are `(row, col, magnitude)` like the retinal stream; `magnitude` is the
  size of the changed connected-region, so the UNCHANGED downstream
  (`_salient_centroid` / `_distal_onset`) sorts by region salience exactly as it
  sorts by dB now. No location is hardcoded — the destination/exit regions EMERGE
  from the observed change.

- **New file only.** `ColourChangeEye` lives in a NEW module; the existing
  `OnsetEye`, `photon_eye.py`, and every seed are byte-identical by construction
  (default-OFF: the pre-fix behaviour is the untouched luma path).
- **No Rust.** The colour-diff is a trivial mechanical comparison — squarely
  perception ingest ("the smallest graph token"), like tokenising text into
  Mentions or 229's `observe_change`. Canonical `.so` `fe7c4d33` UNCHANGED. If a
  new Rust Term were truly required, STOP+report — it is not.

## WIRING (the UNCHANGED 227/228/229 pipeline)

- **Destination flash → 229.** The detected DISTAL destination flash is written as
  `add_observation(interact=1, remote_changed=1, cause_id="cross",
  effect_kind="destination_flash")` (preceded by clean natural-timeline no-op
  observations) on an `arm="observe"` `GroundPlanner` with a `has_object` cross →
  229's UNCHANGED `rcg_ground` mints `causes(cross, destination_flash)`.
- **Exit-glyph rotation → 227.** The detected rotation of the exit-glyph
  before→after cells is recognised by 227's UNCHANGED `_recognise_transform` as a
  `Transform{generator:"rotation90", k}` = canonical required key `rot90:k`.

## GATES (pre-registered; measure-first; Wilson 95% CIs; CI-separation = lower>upper)

- **G-detect-the-effects (HEADLINE):** on reaching the cross, the colour-change
  eye DETECTS the indicator flash AND the destination flash AND the exit-glyph
  rotation — measured as precision/recall of detected-vs-GROUND-TRUTH (raw
  cell-diff) regions, **CI-separated above the pre-fix luma eye** (which misses
  them → the 229/230 null reproduced as the baseline). An OFFLINE synthetic
  transient-flash + rotation-on-reach scenario (powered) confirms the mechanism;
  the REAL-frame result is the headline. **Every live-perception claim is gated
  against the ground-truth pixel deltas in the actual frames, never the eye's
  self-report.**
- **G-located-cause:** the diagnostic NAMES the operative failure and disambiguates
  THRESHOLD vs TIMING with PER-REGION evidence (per ground-truth region: present in
  the returned reach-frame at all? luma-eye fired + luminance-delta vs +6 dB?
  colour-change-eye fired? transient-or-persistent?) — not a vague "missed it." If
  the effects are in the returned frame → threshold is operative and the fix
  catches them; if a region is a genuine sub-step transient absent from every
  returned frame → report that straight as the ARC-API observability limit (settled
  frames only), NOT forced into the threshold framing.
- **G-wires-to-pipeline:** the detected destination-flash grounds
  `causes(cross, destination)` via 229's UNCHANGED `rcg_ground`; the exit rotation
  reads as the required transform `rot90:k` (227). End-to-end from a real
  observation.
- **G-live (the real test, HONEST):** on real ARC-AGI-3 ls20, DELIBERATELY
  navigate the avatar ONTO the cross (blob-tracker avatar centroid + onset-located
  cross + greedy Manhattan stepper over ACTION1-4), capture before/reach/after
  frames, compute the ground-truth raw pixel deltas, and report STRAIGHT: does the
  colour-change eye now SEE the flash+rotation on the reach-frame (with the
  detection numbers vs ground truth), or does it still miss some (which, straight)?
  Auth verified BEFORE; `ARC_API_KEY` from the gitignored
  `/home/matt/ozma/internal/.env`, NEVER printed/committed; `.so` never committed;
  STOP+report if API unreachable; NEVER fabricate; state fresh-API. If the API is
  down, the offline synthetic gate + the located-cause diagnostic are the
  deliverable.
- **G-discipline:** integer-native (colour indices; the onset is exact inequality
  on the observed colour); **default-OFF byte-identical** (the existing luma path
  is untouched; the new eye is opt-in — new files only); **canonical `.so` md5
  `fe7c4d33` UNCHANGED** (NO Rust); `term.rs` + whole `runners/dsl` tracked diff
  EMPTY; oracle `rung7_vision_bench` BEFORE==AFTER; 34-file
  `per_area_settlement_regression` BEFORE==AFTER (failing node-id SET identical);
  `source_match` reported for any seed round-trip.

## FALSIFICATION BAR

The fix DETECTS the real effects **measured against ground-truth pixel deltas, not
the eye's self-report** (that self-report is exactly what produced the false null);
the cause is LOCATED (named, per-region); it composes with the UNCHANGED 227/228/229
pipeline; and it is GENERAL — a real perception capability (see transient remote
colour changes + rotations), NOT an ls20-coordinate hack: NO hardcoded
destination/exit-glyph locations (they emerge from the observed change), NO domain
constant in the detector.

## STRUCTURE

Build the colour-change eye + the located-cause diagnostic + the synthetic powered
ablation (luma-eye-misses vs colour-eye-detects) OFFLINE (the guaranteed
deliverable + headline mechanism), wire the detected effects into the UNCHANGED
229/227 pipeline, THEN run the deliberate navigate-onto-the-cross LIVE diagnostic on
real ls20, gating every perception claim against the ground-truth raw pixel deltas.

## FILES (to be created)

- `LS20_SEE_PREREG.md` (this file; committed alone).
- `worlds/arc_ls20_see.py` — the `ColourChangeEye` colour-change onset primitive +
  ground-truth raw-diff/region utilities + the located-cause diagnostic + the
  synthetic reach scenario + the pipeline wiring helpers (mechanical perception;
  no agent decisions).
- `scripts/arc_ls20_see_measure.py` — the powered offline gates (detect-the-effects
  vs the luma baseline; located-cause per-region; wires-to-pipeline) + source-audit.
- `scripts/arc_ls20_see_live.py` — the bounded LIVE navigate-onto-the-cross
  diagnostic, gating detection against the ground-truth pixel deltas.
- `tests/test_arc_ls20_see_migrated.py` — gate tests.
- `results/arc_ls20_see_{powered,live}.json` — the measured numbers.
- `results/see_{oracle,regress}_{before,after}*` — the discipline baselines.
