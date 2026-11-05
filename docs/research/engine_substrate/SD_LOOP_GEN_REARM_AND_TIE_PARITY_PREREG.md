# SD LOOP — reset GenInfer flags on re-arm, and tie-instrument parity for ClosestShape — PRE-REGISTRATION (block 372000)

**Status: PRE-REGISTRATION, written 5 November 2026 before the change exists.** This closes
the gaps stated in advance in block 371000
([results](SD_LOOP_REARM_AND_JSON_SIGNATURE_RESULTS.md) §5).

## 0. Seed claim (verbatim, run at prereg time)

```
$ .venv/bin/python scripts/seed_claim.py 372000 372999
SEED CLAIM 372000-372999: CLEAN -- no collision DETECTED.
  Scope: 1373 files with seed sinks; 877 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## 1. The gaps

### G1 — `sd_redecode` leaves GenInfer flags stale

`sd_redecode` (shape_decode_loop v1.18.0) resets `transform_checked`,
`transform_explained`, `dim_checked` and `dim_explained`. It does **not** reset
`gen_checked` or `gen_explained`. Eight rules read those flags as "the GenInfer look has
been taken for this residual": `sd_gen_check*`, `sd_mint_generator`,
`sd_mint_quadratic_generator`, `sd_mint_quantum`, `sd_dedup_existing`,
`sd_recognize_at_grain` and `sd_mdl_outliers`.

After a re-arm, the stale flags have two effects:
- With `gen_checked == 1, gen_explained != 1`, the observation reaches the mint and dedup
  guards without a fresh GenInfer look against the grown codebook.
- With `gen_explained == 1`, `sd_recognize_at_grain` can recognise from a verdict made
  against the old codebook.

### G2 — `ClosestShape` is not seen by the tie instruments

`ClosestShape` replaced `Argmax` at the two sd-loop sites. It reports to the selector audit
(block 371000), but not to the `argmin_tie` census or its refusal coercion
(`argmin_tie::coerces_refusal`). So the tie census can no longer see ties at those sites,
and the coercion mode can no longer refuse them.

## 2. Design

### G1 (seed data)

`sd_redecode` additionally sets `gen_checked := 0` and `gen_explained := 0`. This is the
same idiom it already uses for the transform and dimension flags, where 0 is falsy for
every `== 1` guard and distinct from 1. The change is made by extending
`scripts/gen_sd_rearm_and_closest_shape.py`, which stays idempotent. Version 1.18.0 →
1.19.0.

### G2 (Rust, `eval_closest_shape`)

When `argmin_tie::enabled()`, do exactly what `argmin_or_argmax_over` does for `Argmax`
(`want_min = false`):
- track the count of candidates tied at the maximum (exact `cmp_value_lex == Equal`);
- call `note_firing`, plus `note_empty` or `note_tie`;
- on a tie, call `note_site("ClosestShape", <goal term JSON>, true)`;
- call `note_nulls(n_seen, 0, false)`, since a score is never None.

When `argmin_tie::coerces_refusal(false)` and there is a tie, return `None` (Argmax with
`default: null`) and call `note_refusal`. All of this sits behind the instruments'
default-off atomic loads, so with the instruments off behaviour is byte-identical.

## 3. Gates and predictions

| gate | prediction | fails if |
|---|---|---|
| **H-0** engine | Rust tests: a tie fixture (two identical parts) records 1 tie and 1 site under `argmin_tie` and is refused under coercion; a non-tie records 0 ties; with instruments off the output is unchanged; `closest_shape` tests 4/4 still pass; provenance `own` | any failure |
| **H-1** re-arm ≡ fresh decode | For every observation in three streams, the end state after a re-arm (`status`, `covered_by`, `gen_explained`, and a count of 1 `has_transform` where present) equals the state of a FRESH observation with the same signature decoded once against the final codebook. The streams are: (a) the block 370000 affect growth stream (23 frames); (b) the det1 view grid (`scripts/det1_measure.py` A2 shear and rotation views, gen_infer on, uni on), followed by an epoch bump from an unrelated part; (c) the block 371000 tromino scenario. Predicted 100% agreement after the fix. Before the fix, the measured disagreement count is recorded, not predicted | any disagreement after the fix |
| **H-2** flags re-checked | in stream (b), every re-armed residual observation has `gen_checked == 1` after the run, set by a fresh `sd_gen_check*` firing | any stale flag |
| **H-3** regression | the block 371000 scoped set (2022 ids, `SD_LOOP_REARM_SCOPE.txt` minus humanoid walking) has identical node-id outcomes on the start commit and on the fix. The 32 `test_humanoid_walking_migrated.py` ids run separately on both trees with a 3-hour cap each, and are reported | any pass→fail, unless localised and shown to be a stale-flag artefact. Each change is reported |

## 4. Measurement of committed records (separate from the gates)

The block 371000 results listed consumers whose codebooks store JSON-string signatures.
`scripts/agnosia_measure.py`, `scripts/identity_untangling_measure.py` and
`scripts/identity_seam_measure.py` are run on the pre-371000 tree (`1281a482`) and on the
current tree, in separate worktrees, and their outputs are diffed. Any changed committed
number gets a dated correction note appended to its RESULTS document. Those documents are
not otherwise edited. The det1 correction found in block 371000 gets its note in
`VISION_DET1_RESULTS.md`.

## 5. Gaps

- `ClosestShape`'s tie site key is the goal Term's JSON, not the old Argmax value Term's.
  Census rows from before and after this change therefore name the site differently.
- The `/home/matt/ocelot-atsm-baseline` engine, which lacks `Round`, is a frozen baseline
  checkout. It is out of scope and not touched.
