# LS20 ISOLATE-THE-CLEAN-TRIPLE — PRE-REGISTRATION (block 232000)

Committed **ALONE**, BEFORE any measurement. This file fixes the diagnostic, the
mechanism, the gates, the controls, and the discipline. Numbers land only in
`LS20_TRIPLE_RESULTS.md`.

## SEED CLAIM (verbatim `check_claim`, recorded here — NOT a permanent pytest)

```
$ python scripts/seed_claim.py 232000 232999
SEED CLAIM 232000-232999: CLEAN -- no collision DETECTED.
  Scope: 951 files with seed sinks; 650 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Block `232000-232999` claimed CLEAN (verbatim `check_claim` above returns
`OK: True`).

## WHERE THIS PICKS UP (231's honest residual)

231 fixed the EYE: an event-native COLOUR-CHANGE onset
(`worlds/arc_ls20_see.ColourChangeEye`) now SEES the colour-only changes the
increase-only luminance eye was blind to (proven offline CI-separated; the false
null corrected live — the colour eye achieved full ground-truth recall 52/52 vs
the luma eye's 15/52 on a real reach transition). But 231 did **NOT** isolate the
clean TRIPLE the owner described (indicator flash + destination flash + exit-glyph
rotation). The captured live effect was a **2-cell recolour, no recognisable
rotation**, for two reasons stated straight in `LS20_SEE_RESULTS.md`:

1. **Real ls20 has NO no-op action** (`available=[ACTION1..4]`): every step the
   avatar MOVES, so the reach-frame raw diff (~52 cells) **MIXES the avatar's own
   movement with the effects**. The transient/persistent classification is
   confounded because before→reach AND reach→after both move the avatar.
2. **Greedy nav reached the cross LOCUS but could not certify the avatar was
   exactly ON the cross cell** — so the triple may not have fully fired.

## THE MECHANISM — RESIDUAL-AFTER-EXPLAINING-THE-AVATAR

You do **NOT** need a no-op frame. The held-prediction principle (the FPS reframe
at whole-frame grain) removes the confound by PREDICTION, not by a special frame:

- **PREDICT the avatar (224's tracker).** `worlds/arc_ls20_percell_track`'s
  `LiveObjectTracker` learns each action's avatar displacement from clean approach
  transitions (a translate), holds the avatar footprint, and PREDICTS the reach
  frame by translating that footprint by the learned shift:
  `predicted = tracker.predict(before, action)`.
- **The RESIDUAL is the surprise.** `residual = raw_changed_cells(predicted,
  reach)` — the cells the actual reach frame differs from the AVATAR-EXPLAINED
  prediction. Cells the avatar move correctly accounts for (its new position, its
  vacated old position, the covered cross) match between `predicted` and `reach`
  and so are **NOT** in the residual. The remaining changed cells — the indicator
  flash, the destination flash, the exit-glyph rotation — ARE in the residual
  because the avatar-translate prediction never touched them. **That is the
  isolation.** The avatar is **ADJACENT IN QUANTA** to the cross: 231 measured the
  per-action avatar jump as `(5,0)`/`(0,5)` — a single 5-pixel jump is ONE quantum
  step (the 218/220 quanta-navigation grain), so `before` sits ONE QUANTUM HOP from
  the cross. In pixels that is several cells, so the avatar footprint never
  pixel-merges with the cross; and the reach is a SINGLE QUANTUM STEP, the natural
  grain for the avatar-translate prediction — the cleanest possible prediction
  unit. (The held-prediction/translate is per-quantum; the residual is what the
  one-hop avatar prediction did NOT account for.)
- **Recognise the isolated rotation.** The residual's DISTAL PERSISTENT region is
  the exit-glyph rotation; it is read as `rot90:k` by 227's UNCHANGED
  `_recognise_transform` (via 231's `recognise_rotation`, unchanged). The residual's
  DISTAL TRANSIENT region is the destination flash; it grounds `causes(cross, …)`
  via 229's UNCHANGED `rcg_ground`. The residual's LOCAL TRANSIENT region is the
  indicator flash.
- **Reach certified by the triple.** The triple firing (all three effects in the
  residual) CERTIFIES the avatar reached the cross CELL — the effects ARE the
  on-cell reach signal (vs 231's locus-only reach).

This is general (the held-prediction principle: observed change minus predicted
change = surprise), NOT an ls20 pixel hack: the detector hardcodes NO effect
location and reads NO ground-truth action→effect table.

## GATES (measure-first; pre-registered here)

- **G-isolate-triple (HEADLINE, GROUND-TRUTH-gated).** On the reach, the three
  effects are ISOLATED from the avatar movement: the residual-after-explaining-the-
  avatar (a) EXCLUDES the avatar's cells and (b) CONTAINS all three effect regions,
  measured against the raw cell-diff GROUND TRUTH. Offline on a synthetic reach
  scenario (avatar translate + the three effects) this must isolate all three
  cleanly, POWERED (N≥48, Wilson 95% CIs), CI-separated above a NO-EXPLANATION
  control (the raw before→reach diff, which mixes the avatar in). The REAL-frame
  result is the headline. If live the avatar cannot be gotten on-cell or only a
  partial effect fires, that is reported STRAIGHT with what DID isolate.
- **G-residual-explains-avatar.** The avatar's local change is EXPLAINED by 224's
  tracker (a translate); the residual EXCLUDES the avatar's cells (measured:
  `|residual ∩ avatar_explained_cells| ≈ 0`, powered, CI-separated above the raw
  diff which fully contains the avatar). The confound is removed by PREDICTION, not
  a no-op frame.
- **G-rotation-recognised.** The ISOLATED exit-glyph rotation (the residual's
  distal persistent region) reads as `rot90:k` via 227's UNCHANGED
  `_recognise_transform` — the transform 231 could not recognise because it was not
  isolated. Powered rate → 1.0; a no-detection control reads nothing.
- **G-reach-certified.** The triple firing certifies the avatar reached the cross
  CELL (vs 231's locus): when the avatar is on-cell the residual carries all three
  effects; a NEAR-MISS scenario (avatar stops one cell short, effects do NOT fire)
  yields NO triple — the triple is a sufficient on-cell certificate. Powered,
  CI-separated (on-cell all-three vs near-miss all-three).
- **G-live (REAL ls20-9607627b, FRESH-API, honest).** Does the clean triple
  isolate on the real game (all three, separated + rotation recognised), or only
  partially? Reported STRAIGHT, gated against GROUND-TRUTH pixel deltas, NEVER the
  eye's self-report. Auth verified BEFORE (`ARC_API_KEY` from the gitignored
  `/home/matt/ozma/internal/.env`, NEVER printed/committed). The `.so` is never
  committed. API unreachable → STOP and report, NEVER fabricate. State fresh-API vs
  replay. Precise nav: greedily step the avatar until its centroid is ON the cross
  cell (not merely near the locus), capture before/reach/after, run the residual
  isolation.
- **G-discipline.** Integer-native (colour indices; exact cell inequalities).
  Graph-native (reuse 231 colour eye + 224 tracker + 220 nav + 227/229; the new
  code is a mechanical world adapter — no agent decisions, no Python rule engine).
  Default-OFF byte-identical (all-new files; 231's `arc_ls20_see.py`, the tracker,
  the luma eye, `photon_eye.py`, and every seed UNTOUCHED). Canonical `.so` md5
  `6829143c` UNCHANGED (NO Rust — the residual is perception arithmetic on the
  colour diff; if a new Rust Term were truly needed I STOP and report). `term.rs`
  and the whole `runners/dsl` tracked diff EMPTY. Oracle `rung7_vision_bench`
  BEFORE == AFTER. 34-file `per_area_settlement_regression` failing-node-id SET
  BEFORE == AFTER. `source_match` reported.

## CONTROLS

- **NO-EXPLANATION control** — use the raw `before→reach` diff instead of the
  avatar-explained residual. It ALWAYS contains the avatar cells (the confound),
  so "excludes the avatar" is FALSE by construction; CI-separated below the
  residual arm. This is the confound 231 hit.
- **NEAR-MISS control** — the avatar stops one cell short of the cross and the
  three effects do NOT fire; the triple must NOT be certified (no false on-cell).
- **NO-DETECTION control (rotation)** — with no isolated distal-persistent region,
  the rotation recogniser reads nothing.

## FALSIFICATION BAR

The isolation is by PREDICTION-AND-RESIDUAL (explain the avatar, the rest is the
effects — general, the held-prediction principle, not an ls20 pixel hack); gated
against GROUND-TRUTH deltas, not self-report; the rotation recognised by the
UNCHANGED 227; whether the clean triple isolates LIVE is measured and reported
straight either way (it may only partially isolate — that is an honest result).

## FILES (all NEW; default-OFF)

- `LS20_TRIPLE_PREREG.md` — this pre-registration (committed ALONE).
- `worlds/arc_ls20_triple.py` — the residual-after-explaining-the-avatar isolation
  (mechanical perception + ground-truth measurement + the synthetic reach
  scenario) reusing 224's tracker, 231's colour eye + `recognise_rotation`, 229's
  grounder.
- `scripts/arc_ls20_triple_measure.py` — the powered offline gates + controls +
  source-audit.
- `scripts/arc_ls20_triple_live.py` — the LIVE precise-nav-onto-the-cross + isolate.
- `tests/test_arc_ls20_triple_migrated.py` — the gate tests.
- `LS20_TRIPLE_RESULTS.md` — the measured numbers (lands AFTER this prereg).
