# LS20 ISOLATE-THE-CLEAN-TRIPLE — RESULTS (block 232000)

Pre-registered in `LS20_TRIPLE_PREREG.md` (committed **ALONE**, SHA `8e743c6478`),
BEFORE any number here. Block `232000-232999` claimed CLEAN (`seed_claim.py 232000
232999`; verbatim `check_claim` in the prereg — NOT a permanent pytest).

## THE MECHANISM — RESIDUAL-AFTER-EXPLAINING-THE-AVATAR (no no-op frame needed)

231 fixed the EYE but could not isolate the owner's clean TRIPLE (indicator flash +
DESTINATION flash + exit-glyph ROTATION): real ls20 has NO no-op action, so every
step the avatar MOVES and the reach-frame raw diff (~52 cells) MIXES the avatar's own
movement with the effects. 232 removes the confound by PREDICTION, the held-prediction
principle at whole-frame grain:

```
predicted = tracker.predict(before, action)         # 224 tracker: translate avatar
avatar_cells = raw_changed_cells(before, predicted) # what the avatar move explains
residual = raw_changed_cells(predicted, reach)       # the SURPRISE = the effects
```

Cells the avatar move correctly accounts for (its new cell, its vacated cell, the
covered cross) MATCH between `predicted` and `reach` and drop out; the effects were
never touched by the avatar-translate, so they ARE the residual. The avatar is
**ADJACENT IN QUANTA** to the cross (231 measured the per-action jump as `(5,0)`/
`(0,5)` — a 5-pixel jump is ONE quantum step), so `before` sits one quantum hop from
the cross: the footprint never pixel-merges with it, and the reach is a single clean
quantum-grain translate.

## THE HEADLINE — G-isolate-triple (OFFLINE powered, ground-truth-gated)

`results/arc_ls20_triple_powered.json`, N=64, Wilson 95% CIs. On a synthetic
ls20-shaped reach (avatar approach + on-cell reach + the three effects), the residual
isolates all three effects (each a subset of the ground-truth effect cells) AND
excludes every avatar cell:

| arm | clean-isolate all-three (excl. avatar) |
|---|---|
| **residual-after-explaining-the-avatar (the fix)** | **1.000 [0.943, 1.000]** |
| raw before→reach diff (NO-EXPLANATION control) | 0.000 [0.000, 0.057] |

- **G-isolate-triple: PASS**, CI-separated (residual CI-lower **0.943 > 0.057**
  control CI-upper). The residual contains all three effect regions and EXCLUDES the
  avatar; the raw diff (231's approach) ALWAYS contains the avatar (the confound).
  Measured against the GROUND-TRUTH raw cell-diff, never the eye's self-report.

## G-residual-explains-avatar (N=64)

| metric | value |
|---|---|
| residual EXCLUDES avatar, NON-trivially (avatar footprint == ground truth, non-empty) | **1.000 [0.943, 1.000]** |
| raw diff excludes avatar (control, want 0) | 0.000 [0.000, 0.057] |
| mean `residual ∩ avatar_cells` | **0.0** |

- **PASS**, CI-separated. "Non-trivial" is load-bearing: the tracker's translate
  ACTUALLY predicted the avatar (the predicted footprint equals the ground-truth
  avatar cells, non-empty), so `residual ∩ avatar == 0` is real confound-removal, not
  a vacuous empty-prediction pass. **The confound is removed by PREDICTION, not a
  no-op frame.**

## G-rotation-recognised (N=64)

- The ISOLATED exit-glyph rotation (the residual's distal PERSISTENT region) reads as
  `rot90:k` via 227's UNCHANGED `_recognise_transform` (through 231's
  `recognise_rotation`), **matching the ground-truth k: 1.000 [0.943, 1.000]**; the
  NO-DETECTION control (a near-miss where the effect does not fire) reads a rotation
  **0.000 [0.000, 0.057]**. CI-separated. This is the transform 231 could not
  recognise because it was not isolated.

## G-reach-certified (N=64)

- On-cell reach certifies the triple **1.000 [0.943, 1.000]**; a NEAR-MISS (avatar
  one quantum hop short, effects absent) certifies it **0.000 [0.000, 0.057]**.
  CI-separated. **The triple firing is a sufficient on-cell reach certificate** (vs
  231's locus-only reach).

## G-live (REAL ls20-9607627b) — THE CONFOUND REMOVED BY PREDICTION, honest partial

`scripts/arc_ls20_triple_live.py --game ls20-9607627b --nav 60`
(`results/arc_ls20_triple_live.json`, frames in `..._frames.json` /
`..._allframes.json`). **FRESH-API** (not replay). Auth verified BEFORE (`ARC_API_KEY`
from the gitignored `/home/matt/ozma/internal/.env`, NEVER printed/committed; RESET
`state=NOT_FINISHED`, grid 64×64, `available=[ACTION1..4]`). The tracker LEARNED the
per-action avatar shift as graph data (`ACTION1` up=(0,0) blocked, `ACTION2`
down=(5,0), `ACTION3` left=(0,−5), `ACTION4` right=(0,+5) — matching 231) and PRECISE
nav walked the avatar ONTO the cross cell (`min avatar→cross dist = 2.0`, on-cell
arrival transition, vs 231's locus-only radius-6).

On the on-cell reach transition, the GROUND-TRUTH raw cell-diff = **52 changed cells
in 2 regions**:

| quantity | value |
|---|---|
| raw ground-truth changed cells (before→reach) | 52 (2 regions) |
| **avatar cells EXPLAINED by the tracker (translate)** | **50** |
| **residual after explaining the avatar** | **2** |
| `residual ∩ avatar_cells` (overlap) | **0** |
| residual EXCLUDES the avatar | **True** |
| raw diff CONTAINS the avatar (the 231 confound) | **True** |
| surviving residual region | 1 region — 2 cells, distal (dist 23.1), persistent |

- **THE CONFOUND IS REMOVED LIVE BY PREDICTION.** The residual-after-explaining-the-
  avatar collapses the 52-cell mixed diff to a **2-cell residual**, EXPLAINING the
  50-cell avatar movement and EXCLUDING it (overlap **0**), where the raw diff
  (231's method) still CONTAINS the avatar. The surviving residual is exactly the
  genuine DISTAL remote effect 231 identified (the 2-cell persistent recolour at
  ~row 61) — now cleanly SEPARATED from the avatar's move, gated against the
  ground-truth pixel deltas, never the eye's self-report.
- **THE FULL CLEAN TRIPLE DOES NOT ISOLATE LIVE — reported STRAIGHT.** Only ONE
  remote region is present in the returned reach frames on this game/budget (a 2-cell
  persistent recolour): NO separable indicator+destination flash PAIR, and a 2-cell
  region cannot establish a rotation (`recognise_rotation` returns nothing). So
  `all_three_isolated=False`. This is the **honest ARC-API / budget limit**, the same
  one 231 hit: the ARC HTTP API returns only settled frames, and ls20's no-no-op
  action set means the transient flashes are sub-step events the returned frames do
  not expose as separable regions. The full three-effect isolation is proven OFFLINE
  (powered, CI-separated); the LIVE half lands the CORE advance — **the avatar
  confound that blocked 231 is removed by prediction, leaving the genuine remote
  effect isolated.**

## G-graph-native / SOURCE-AUDIT

`source_audit` (`results/arc_ls20_triple_powered.json`):
`{'isolation_reads_no_scenario_ground_truth_in_decision': True,
'regions_emerge_from_residual': True, 'isolation_is_predict_and_residual': True,
'no_hardcoded_effect_location_literal': True,
'banned_domain_tokens_in_decision_logic': [],
'reuses_224_tracker_and_231_recogniser': True, 'clean': True}`.

- The isolation is **predict-and-residual**: it names NO effect LOCATION, reads NO
  ground-truth action→effect table, and reads NO scenario ground truth in its decision
  functions — the regions EMERGE from the residual (`_cluster` over
  `raw_changed_cells(predicted, reach)`). It REUSES 224's `LiveObjectTracker` (the
  shift is graph data on a Percell agent), 231's `ColourChangeEye` /
  `raw_changed_cells` / `recognise_rotation` and 229's grounder — all UNCHANGED. The
  new code is a mechanical world adapter (no agent decisions, no Python rule engine).

## DISCIPLINE

- **Canonical `.so` md5 `6829143c…` UNCHANGED** (NO Rust — the residual is integer
  cell arithmetic on the colour diff). `term.rs` NOT modified; whole `runners/dsl`
  tracked+untracked diff EMPTY (verified).
- **Default-OFF byte-identical:** the fix is entirely NEW files
  (`worlds/arc_ls20_triple.py`, `scripts/arc_ls20_triple_{measure,live}.py`,
  `tests/test_arc_ls20_triple_migrated.py`); 231's `arc_ls20_see.py`, the 224
  tracker, the luma eye, `photon_eye.py`, and every seed are UNTOUCHED — the pre-fix
  path is byte-identical BY CONSTRUCTION.
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped** == AFTER **214
  passed, 10 skipped** (`results/see_oracle_{before,after}_232.txt`).
- **34-file `per_area_settlement_regression`:** failing NODE-ID SET **IDENTICAL**
  BEFORE == AFTER — **23 failed, 278 passed, 5 skipped** both runs; `diff` of the
  sorted node-id lists EMPTY (`results/see_regress_{before,after}_232_ids.txt`). (The
  23 are the pre-existing reds this environment carries; 232 touches none.)
- **New gates:** `tests/test_arc_ls20_triple_migrated.py` **10 passed**
  (ground-truth-is-a-real-raw-diff; residual-is-observed-minus-predicted-avatar;
  residual-isolates-all-three-excludes-avatar; residual-explains-avatar-nontrivially;
  rotation-recognised-rot90-k; near-miss-does-not-certify; no-explanation-control-
  contains-avatar; powered-isolation-ci-separated; source-audit-predict-and-residual;
  fix-is-new-code-reusing-shared-unchanged).
- **Integer-native:** colour indices; exact cell inequalities; the residual is a set
  difference of raw integer cell-diffs; the verdict is gated on the ground-truth raw
  diff.

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The OFFLINE powered ablation proves the MECHANISM decisively: the residual-after-
explaining-the-avatar isolates all three effects (indicator + destination + rotation),
CI-separated above the no-explanation control which reproduces the confound; the
avatar is explained NON-trivially (residual ∩ avatar == 0); the rotation reads as
`rot90:k` via the UNCHANGED 227; the triple certifies the on-cell reach against a
near-miss. The LIVE half lands the CORE advance on REAL ls20: the residual collapses
the 52-cell mixed diff to a 2-cell residual, EXPLAINING and EXCLUDING the 50-cell
avatar (overlap 0), where 231's raw diff still contained it — the confound removed by
PREDICTION, the genuine remote effect cleanly separated. The honest residual: the full
clean triple does NOT isolate live (only ONE remote region — a 2-cell persistent
recolour — is exposed in the returned frames; no separable flash pair, no
rotation-capable region), the same ARC-API / no-no-op / budget limit 231 hit. Both
reported.

## FILES

- `LS20_TRIPLE_PREREG.md` — pre-registration (committed alone, SHA `8e743c6478`).
- `worlds/arc_ls20_triple.py` — the residual-after-explaining-the-avatar isolation +
  the synthetic TripleReachScenario (mechanical perception; reuses 224/231/229;
  no agent decisions).
- `scripts/arc_ls20_triple_measure.py` — the powered offline gates + controls +
  source-audit.
- `scripts/arc_ls20_triple_live.py` — the LIVE precise-nav-onto-the-cross + isolate.
- `tests/test_arc_ls20_triple_migrated.py` — 10 gate tests.
- `results/arc_ls20_triple_powered.json` — the powered numbers + source-audit.
- `results/arc_ls20_triple_live.json`, `..._frames.json`, `..._allframes.json` — the
  real captured frames + the live isolation.
- `results/see_{oracle,regress}_{before,after}_232*` — the discipline baselines.
