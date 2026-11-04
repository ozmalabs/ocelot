# SD LOOP — re-armed transforms get stuck, and rule-side scoring misreads JSON-string signatures — PRE-REGISTRATION (block 371000)

**Status: PRE-REGISTRATION, written 5 November 2026 BEFORE the fix exists.** Both defects
were found during the affect-frame rungs, block 369000
(`docs/research/psychology_affect/AFFECT_FRAME_CODEBOOK_RESULTS.md`) and block 370000
(`…/AFFECT_FRAME_V02_RESULTS.md`). Predictions come from code reading and from the
measured block 370000 outcome. A deviation is reported as found.

## 0. Seed claim (verbatim, run at prereg time)

```
$ .venv/bin/python scripts/seed_claim.py 371000 371999
SEED CLAIM 371000-371999: CLEAN -- no collision DETECTED.
  Scope: 1373 files with seed sinks; 877 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Deterministic; no number is drawn from the block.

## 1. The defects

### D1 — a re-armed transformed observation never returns to a terminal status

`sd_redecode` re-arms `recognized_transformed` observations whenever `codebook_epoch`
grows. This is deliberate, so that a grown codebook can turn them into exact matches. It
resets `transform_checked`, `transform_explained`, `dim_checked` and `dim_explained`. The
re-decode then recomputes `transform_explained` = 1, or `dim_explained` = 1 on the
dimension path. But `sd_recognize_transformed` and `sd_recognize_dim` both require "no
`has_transform` edge yet". That guard exists so the `Transform` node is minted once.
Because the edge already exists, the observation stays `decoded` permanently.

**Measured in block 370000:** 11 of 23 affect frames were stuck. Any codebook that grows
while transformed observations exist is affected.

### D2 — `sd_recognize` and `sd_mint_quantum` misread JSON-string signatures

`load_parts` (`shape_decode.rs`) deliberately accepts a part `signature` either as a native
relation list or as a JSON string. `ShapeDecode`, `TransformDecode` and `DimInfer` handle
both. Four rule sites do not: `sd_recognize.covered_by` and
`sd_mint_quantum.closest_held_shape` in `seeds/shape_decode_loop.json`, and
`pcon_recognize` and `pcon_mark_merge` in `seeds/prog_construction_loop.json`. Each scores
parts with
`Argmax(NodesOfType ShapeSignature, sig, FixedCount(AntiUnify(SetT[X, Attr(sig,"signature")])))`,
and `AntiUnify` treats a JSON string as one opaque value.

**Measured** (probe on `boot_core`): an exact match against a JSON-string part `zz_part_B`
gave `covered_by = "fractal"`; the native-list form gave `zz_part_B`.

A seed-only repair is not possible:
- `FromJsonString` returns its strings as `Surface(Text)`, which never equals the
  observation's `Str` predicates. The probe gave FixedCount 1 against 5 for identical
  content.
- `load_parts` resolves strings against the interner (`json_to_value_scoped`), but no Term
  exposes that parse to a rule.

## 2. Design

### D1 fix (seed data, `seeds/shape_decode_loop.json` v1.17.0 → v1.18.0)

Two new rules are inserted directly after `sd_recognize_dim`.

**`sd_rerecognize_transformed`**
- match `[["ag","observed","obs"],["obs","has_transform","t"]]`
- where: the same `AgnosiaParams` associative guard as `sd_recognize_transformed`;
  `obs.status == "decoded"`; `obs.transform_explained == 1`
- effects:
  - `status := "recognized_transformed"`
  - `covered_by := TransformDecode(...).base`
  - on `t`, set `dims`, `transforms`, `deltas`, `base` (the same TransformDecode fields
    `sd_recognize_transformed` mints) and `source := "transform_decode"`

**`sd_rerecognize_dim`**
- match: same as `sd_rerecognize_transformed`
- where: the agnosia guard; `status == "decoded"`; `dim_explained == 1`;
  `transform_explained != 1`
- effects:
  - `status := "recognized_transformed"`
  - `transform_explained := 1`
  - `covered_by := DimInfer(...).base`
  - on `t`, set every attr `sd_recognize_dim` mints (`dim`, `delta`, `generator`, `k`,
    `dims`, `transforms`, `base`, `generators`, `ks`, `source`)
- The `LatentDimension` node and its edge already exist and are not touched.

No new `Transform` node is minted on re-recognition, and the existing one is updated in
place. Every DimInfer/TransformDecode argument is copied verbatim from the existing rules,
including `grain` and `max_dims`.

### D2 fix (one new Rust Term, `ClosestShape`)

`ClosestShape { goal, codebook_type = "ShapeSignature" }` returns the NODE that the
existing `Argmax` would return, with the one difference that a part's signature is read
the way `load_parts` reads it. For each node of `codebook_type`, in the same order and
with the same comparator and tie rule as `Argmax` over `NodesOfType`:
- if the `signature` attr is `Str` or `Surface(Text)` holding a JSON array, it is parsed
  with `json_to_value_scoped` into a Tuple;
- otherwise the attr `Value` is used unchanged, so native-list parts are byte-identical to
  today.

The score is `fixed_count_value(anti_unify_values(<the SetT of [goal, sig]>, wild))`, with
the same SetT construction and default wild marker as the existing Terms. It returns
`Value::Node`, or `None` when there are no nodes, matching Argmax's `default: null`.

The four rule sites replace only the inner `Argmax{…}` with
`{"type":"ClosestShape","goal":<X>}`. The surrounding `Attr(..., "name")` is unchanged.
`prog_construction_loop` is bumped one minor version.

**Engine housekeeping:**
- The variant is APPENDED at the end of `TermNode`.
- `term_variants.rs` is regenerated with `tools/gen_term_variants.py`.
- JSON parse/emit is added in `jsonio.rs` and `reflect.rs`.
- `copy_subtree` and the children walk handle the new variant.
- The Rust unit tests cover JSON/native parity and Argmax equality on native parts.
- The engine is built with `scripts/engine_build.sh`, and the rebuilt tracked artifact
  `_native.abi3.so` and `_native.build.json` is committed, as the repo already does.

### Consequential test update (declared now)

`tests/test_affect_frame_v02.py::test_G3_growth` pinned D1's stuck state (8/4/11). With D1
fixed, its expectation becomes 8 `recognized` / 15 `recognized_transformed` / 0 `decoded`,
with the same per-frame deltas and still exactly one `has_transform` per transformed frame.
The block 370000 result document stands as the record of the defect; only the live gate
changes, citing this block.

## 3. Predictions and gates

| gate | prediction | fails if |
|---|---|---|
| **G-0** engine | the new Term's Rust unit tests pass; `scale_audit::variant_table_covers_the_enum` passes; the provenance gate reads `own` after `engine_build.sh` | any failure |
| **G-1** covered_by, JSON | the `boot_core` probe of §1 with JSON-string parts gives `covered_by == "zz_part_B"`; the native form still gives `zz_part_B` | any other name |
| **G-2** closest_held_shape, JSON | a partially covered observation `[["probe_c","Z",2],["zznew","Q"]]` against parts A and B (§1 probe) mints an axis whose `closest_held_shape` is `zz_part_B` in BOTH JSON and native forms | the two forms differ, or the name is not `zz_part_B` |
| **G-3** affect codebook as JSON strings | block 369000's 22 events against a copy of `affect_frame_canonical` with every signature stored as `json.dumps(...)`: all 23 frames have `covered_by == affect:<own tag>`, the same statuses and deltas as the native codebook, and 0 mints | any difference (block 369000 run 1 had 8 frames at `fractal`) |
| **G-4** D1, transform path | block 370000 growth arm: 8 recognized / **15** recognized_transformed / **0** decoded; deltas as before; exactly 1 `has_transform` per transformed frame; `Transform` node count unchanged from the pre-fix run (15) | any frame left `decoded`, or a second Transform minted |
| **G-5** D1, dimension path | `test_dimension_inference_migrated.py`'s rotated-tromino observation, after an unrelated `ShapeSignature` is added and `codebook_epoch` bumped, ends `recognized_transformed` (pre-fix: `decoded`) with the same `base`, `generator` and `k`, 1 Transform and 1 LatentDimension | otherwise |
| **G-6** no other behaviour change | the scoped regression set (150 test files mentioning the sd loop, codebook or `covered_by`; list committed as `SD_LOOP_REARM_SCOPE.txt` beside this file) has identical node-id outcomes on the start commit and on the fix, except `tests/test_affect_frame_v02.py::test_G3_growth` (updated as declared) | any other node id changes outcome. Each change is reported and localised; a pass→fail is a failure of this rung |

## 4. Gaps stated in advance

- `sd_redecode` also leaves `gen_checked` and `gen_explained` set. After a re-arm, the
  mint guard can therefore pass without a fresh GenInfer look. This is noted and not fixed
  here, because changing it alters mint behaviour broadly.
- A re-recognised `Transform` that switches from the dimension path to the transform path
  keeps its dimension-only attrs (`dim`, `generator`, `k`, …) alongside the refreshed
  transform fields.
- G-6 is a scoped slice, not the full `-k migrated` sweep. Both runs are in detached
  worktrees, which lack the gitignored `data/` and `results/`. That affects both runs
  equally.

## 5. Files

- `runners/dsl/src/{term.rs, term_variants.rs, jsonio.rs, reflect.rs, shape_decode.rs}`
  and the engine artifact.
- `seeds/shape_decode_loop.json` and `seeds/prog_construction_loop.json` (edited by a new
  generator, `scripts/gen_sd_rearm_and_closest_shape.py`, idempotent).
- `tests/test_sd_rearm_closest_shape_migrated.py` (new), and
  `tests/test_affect_frame_v02.py` (G-3 expectation only).
- Results: `docs/research/engine_substrate/SD_LOOP_REARM_AND_JSON_SIGNATURE_RESULTS.md`.
