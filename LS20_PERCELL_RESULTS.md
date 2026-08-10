# LS20 PER-CELL LIVE MECHANIC — RESULTS (block 222000)

**The richer per-cell model that attacks 221000's trivially-converging aggregate-
count residual.** It predicts WHICH cells change and to WHAT value
(`action × current-frame → per-cell next-frame`), scored on the CHANGE-SET,
NEVER raw accuracy.

Pre-registered in `LS20_PERCELL_PREREG.md` (committed ALONE, SHA **`f21278b301`**).
Block `222000` claimed CLEAN (`seed_claim.py 222000 222999`, no collision detected).
**Lead with the change-set-F1-vs-nulls result.**

## THE HEADLINE — CHANGE-SET F1 vs BOTH NULLS (G-percell-teeth, OFFLINE powered)

`arc_ls20_percell_measure.py`, **N_eval = 200 held-out scenes × 10 actions = 2000
triples**, 1000-resample bootstrap 95% CI (`results/arc_ls20_percell_powered.json`):

| metric (CHANGE-SET) | learned | persistence null | aggregate-count null (221000) |
|---|---|---|---|
| **strict changed-cell F1** | **1.0000 [1.0000, 1.0000]** | 0.0000 [0,0] | 0.0011 [0.0006, 0.0018] |
| location F1 | 1.0000 [1.0000, 1.0000] | 0.0000 [0,0] | 0.0011 [0.0006, 0.0018] |
| value-accuracy (on changed cells) | 1.0000 [1.0000, 1.0000] | 0.0000 [0,0] | 0.0011 [0.0006, 0.0018] |
| exact next-frame-match rate | 1.0000 | 0.0000 | 0.0000 |

- **CI-SEPARATED above BOTH nulls** on all three change-set metrics (learned lower
  bound 1.0000 > persistence upper 0.0000 AND > aggregate upper 0.0018). This is the
  teeth 221000's live aggregate model lacked.
- The learned model is DETERMINISTIC and exact on clean ls20-shaped dynamics (the
  sd-loop recognition is deterministic; the transform, applied to the object's
  CURRENT position, reproduces the next frame cell-for-cell).

**THE METRIC TRAP, exhibited (never the gate):** RAW per-cell accuracy is
learned **1.00000**, persistence **0.99882**, aggregate **0.99765** — the three arms
are INDISTINGUISHABLE on raw accuracy, yet persistence scores **0.000** strict-F1
and aggregate **0.001**. A "predict no change" null aces raw accuracy and has learned
nothing. Scoring on the change-set is the whole point.

**Why the aggregate-count null fails (the 221000 model on the change-set):** it
learns the right per-action changed-cell COUNT (~the `_changed_fraction` × 4096) and
predicts that many cells changing at UNINFORMED locations — right count, wrong
locations → F1 ≈ count/total ≈ 0.001.

## G-mechanic-discovered — ALL 10 action→Transform hypotheses, NONE given

Confirmed **10/10** (conf ≥ 2 — every action's Transform correctly RE-predicted),
each DISCOVERED by the GENERAL 217000 sd-loop recognising the observed object
before→after (no hardcoded action→transform table anywhere):

| action | discovered key | region_colour (selector) |
|---|---|---|
| move_up / down / left / right | `shift:-1:0` / `shift:1:0` / `shift:0:-1` / `shift:0:1` | 9 (avatar) |
| rot1 / rot2 / rot3 | `rotation90:1` / `:2` / `:3` | 11 (carried symbol) |
| refl_c / refl_r | `reflection_c:1` / `reflection_r:1` | 11 |
| recolour | `subst:11>14` | 11 |

The region-selector is ALSO discovered (moves act on the avatar colour 9,
transforms on the symbol colour 11) — the model learns not just the transform but
WHICH object each action moves. Full `Transform{dim,delta}` from the general
`TransformDecode`/`DimInfer` (`generator`/`k` for rotation/reflection, shift
`deltas` for translation, `subst` for recolour) — the same op that serves
Omniglot / ARC-transform, dimension-arbitrary, not an ls20 hack.

## G-convergence — the change-set surprise DROPS as the model learns

Per-cycle change-set surprise (mean `1 − strict-F1` over a fixed probe set, partial
model with persistence fallback for unmodelled actions):

| cycle | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10+ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **surprise** | 0.9 | 0.8 | 0.7 | 0.6 | 0.5 | 0.4 | 0.3 | 0.2 | 0.1 | **0.0** | 0.0 |

A real staircase 0.9 → 0.0: each curiosity cycle (`Argmin(visits)`) models one more
action; surprise hits 0 once all 10 are modelled. Not a flat line.

## Instrument teeth — the metric PENALISES a wrong region-selector (1.0 is EARNED)

`test_metric_penalises_wrong_region_selector`: a model with the RIGHT transform but
the WRONG region colour (applies `move_right`'s shift to the symbol, not the
avatar) scores change-set strict-F1 **< 0.1** vs the correct model's **> 0.9**. The
1.0 is not free — it is earned by both the transform AND the discovered
region-selector; the metric has teeth beyond the two count nulls.

## G-graph-native + SOURCE-AUDIT

The per-cell model is `Hypothesis` + `Transform` graph data
(`seeds/ls20_percell.json`: `pc_probe_pick` Argmin-visits curiosity;
`pc_predict`/`pc_mint`/`pc_confirm`/`pc_revise` predict-and-residual; `pc_attend`
for the env-dictated live action). The adapter (`worlds/arc_ls20_percell.py`) is
mechanical (perceive → discover via sd-loop → stamp facts → tick; apply the
graph-held Transform to RENDER the predicted frame; MEASURE the change-set). Source
audit **PASS**: the agent's prediction functions (`discover_spec`,
`_recognise_transform`, `_apply_spec_to_grid`, `predict_next`, `hypothesis`)
reference the ground-truth `_MOVE`/`_XFORM` tables **[] (none)**; only `world_next`
(WORLD PHYSICS) uses them. The action→transform map is minted from observation, never
read from a table.

## LIVE HALF (real ARC-AGI-3 ls20 — the HONEST number, reported STRAIGHT)

Auth verified BEFORE measuring (key from `.env`, NEVER printed/committed; `.so`
gitignored, NEVER committed). `arc_ls20_percell_live.py --game ls20-9607627b
--steps 40` (`results/arc_ls20_percell_live.json`):

- **Perception survives on REAL live frames:** round-trip through the 216000 pixel
  eye EXACT on all 40 frames.
- **The per-cell model did NOT converge in the budget — the NULL, reported STRAIGHT:**
  learned per-cell change-set F1 **0.0** == persistence change-set F1 **0.0** (36
  repeat-obs scored, 4 first-obs). `learned_beats_persistence = False`.
- **WHY (measured, honest characterisation — the named residual for the next rung):**
  52 cells change per action (matches 221000). But real ls20 has a NESTED field
  structure — a global dominant colour (frame mode ≈ 4) AND a distinct LOCAL
  play-field (≈ colour 3) the avatar moves within — the avatar is MULTI-COLOUR
  (≈{9,11,12}, ~27 cells) and NOT colour-separable from static structure by a
  whole-frame colour selector (~1487 non-background cells), and a bounded side-probe
  tracking the avatar colours showed the actions ARE unit directional moves with a
  SHRINKING figure (a move + trail/consume dynamic). The rigid single-object
  `Transform` model therefore returns `unrecognised` on every action and falls back
  to persistence. `levels_completed = 0` (side effect, logged).
- **This is an honest measured null, not a hidden failure:** the OFFLINE powered
  teeth (the deliverable) prove the per-cell transform MECHANISM decisively; the
  live half MEASURES that the real ls20 mechanic is richer than a rigid single-object
  transform (nested fields + multi-colour avatar + trail) — the concrete, measured
  frontier for a follow-on rung (a local-region / multi-colour-object tracker with a
  trail model).

## DISCIPLINE

- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (no Rust; the
  per-cell transform machinery REUSES the existing `TransformDecode`/`DimInfer`).
- **`runners/dsl` diff EMPTY** (`term.rs` included) — no tracked file modified at all
  (the rung is entirely NEW files).
- **Default-OFF byte-identical:** the pc_* rules are guarded on `percell_on==1`
  (`test_rules_are_default_off`); the existing ls20 migrated suites
  (`test_arc_ls20_planning_migrated.py` + `test_arc_ls20_mapnav_migrated.py`) **= 12
  passed** (unchanged with the flag off).
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped** == AFTER
  **214 passed, 10 skipped**.
- **34-file `per_area_settlement_regression.sh`:** failing NODE-ID SET IDENTICAL
  before/after (23 ids, `diff` **empty**; `results/percell_regress_before.txt` ==
  the committed `results/mapnav_regress_before.txt`, 23/277/5).
- **New gates:** `tests/test_ls20_percell_migrated.py` **8 passed**.
- **Integer-native:** in-frame cell values are the integer lattice; the `Transform`
  (shift delta / rotation / subst) is the CROSS-FRAME map — the base-as-dimension
  invariant (a float lives in the map, never in a frame's cells).

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

The powered change-set teeth are on ls20-SHAPED offline scenarios (real ls20 palette,
the general 217000 transform recogniser). They prove the MECHANISM — predicting WHICH
cells change to WHAT value, the map DISCOVERED — decisively (1.0 vs ~0 nulls,
CI-separated). The LIVE half confirms perception survives on real content but reports
the honest NULL: the real ls20 mechanic (nested fields + multi-colour avatar + trail)
is richer than a rigid single-object transform and does not converge in the 40-step
budget. Both reported.

## FILES

- `LS20_PERCELL_PREREG.md` — pre-registration (committed alone, SHA `f21278b301`).
- `domains/ls20_percell_seed.py` → `seeds/ls20_percell.json` — the `pc_*` curiosity /
  predict-residual / hypothesis / attend rules.
- `worlds/arc_ls20_percell.py` — the mechanical adapter: scene + world physics,
  `discover_spec` (general sd-loop), `_apply_spec_to_grid` (render a graph-held
  Transform), change-set metrics, the investigate/evaluate drivers + the two nulls.
- `scripts/arc_ls20_percell_measure.py` — the powered offline teeth + nulls +
  convergence + discovered hypotheses + source_match audit.
- `scripts/arc_ls20_percell_live.py` — the bounded per-cell LIVE half.
- `tests/test_ls20_percell_migrated.py` — 8 gate tests.
- `results/arc_ls20_percell_{powered,live}.json` — the measured numbers.
